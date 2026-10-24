// The campaign's reading of the pages (templates/campaign.js), with no browser: a stand-in for the
// browser's storage holding what the pages write, and each test checks what the campaign makes of it.
//   node tools/campaign/test.js
"use strict";
const assert = require("node:assert/strict");
const C = require("../../templates/campaign.js");

let failed = 0, passed = 0;
function check(name, fn){
  try { fn(); passed++ } catch (e){ failed++; console.error(`FAIL ${name}\n  ${e.message.split("\n").slice(0, 6).join("\n  ")}`) }
}
function store(entries){                           // a stand-in for localStorage
  const ks = Object.keys(entries);
  return { length: ks.length, key: i => ks[i], getItem: k => entries[k] };
}
const CD = { maps: { "towton-1461": { name: "Towton, 1461", start_date: "1461-03-27" } }, eras: { medieval: "Medieval (c.1250-1500)" } };
const J = o => JSON.stringify(o);
const pages = {
  "gravewounds-team-builder": J({ era: "medieval", team: [{ name: "Will" }, { name: "Hal" }], losses: [] }),
  "gravewounds-named": J({ a: { name: "Will", map: "towton-1461", force: 3, health: { cases: [] } }, b: { name: "Hal", dead: true } }),
  "gravewounds-travel": J({ mapId: "towton-1461", forces: { "towton-1461": [{ side: "York" }, { side: "Lancaster" }] }, clock: { "towton-1461": { day: 4, used: 6 } }, fought: [] }),
  "gravewounds-lethality": "heroic",
  "gravewounds-narrator": J({ provider: "anthropic", key: "sk-secret" }),
  "other-site-entry": "not ours",
};

check("it reads only Grave Wounds entries, as stored, and never the narrator's", () => {
  const raw = C.read(store(pages));
  assert.ok(raw["gravewounds-team-builder"].startsWith("{"));
  assert.equal(raw["gravewounds-lethality"], "heroic");
  assert.ok(!("gravewounds-narrator" in raw) && !("other-site-entry" in raw));
});
check("the status: the team, the named men, the map and its day", () => {
  const st = C.status(C.read(store(pages)), CD);
  assert.deepEqual(st.team.men, ["Will", "Hal"]);
  assert.equal(st.team.eraName, "Medieval (c.1250-1500)");
  assert.deepEqual([st.named.men, st.named.withForce, st.named.dead], [2, 1, 1]);
  assert.deepEqual([st.travel.mapName, st.travel.day, st.travel.forces], ["Towton, 1461", 4, 2]);
  assert.equal(st.fight.sent, null);
});
check("nothing stored yet: an empty status, no error", () => {
  const st = C.status({}, CD);
  assert.deepEqual([st.team.men, st.named.men, st.travel, st.fight.sent, st.fight.roller], [[], 0, null, null, null]);
});
check("a fight sent from the travel map moves the campaign to the fight, once", () => {
  const raw = { ...C.read(store(pages)), "gravewounds-handoff": J({ from: "travel", force: { name: "Will's lances" }, place: "Ferrybridge", foes: [{ name: "Clifford's flankers" }] }) };
  const s = C.suggest("march", C.status(raw, CD), {});
  assert.equal(s.phase, "fight");
  assert.equal(s.page, "roller.html");
  assert.match(s.why, /Ferrybridge against Clifford's flankers/);
  assert.equal(C.suggest("march", C.status(raw, CD), { [s.mark]: true }), null);
});
check("a battle sent to the field map, then its result, then the aftermath", () => {
  const sent = { ...C.read(store(pages)), "gravewounds-field-handoff": J({ battle: "towton-1461:4:6:3", place: "Towton", forces: [{ name: "York" }] }) };
  assert.equal(C.suggest("march", C.status(sent, CD), {}).page, "field.html");
  const done = { ...C.read(store(pages)), "gravewounds-field-result": J({ battle: "towton-1461:4:6:3", place: "Towton", minutes: 42, forces: { 3: { lost: 7 }, 5: { lost: 12 } } }) };
  const s = C.suggest("fight", C.status(done, CD), {});
  assert.equal(s.phase, "aftermath");
  assert.match(s.why, /19 men lost in 42 minutes/);
});
check("a fight noticed but not yet set up does not hide the win that follows", () => {
  const sent = J({ from: "travel", force: { name: "Will's lances" }, place: "Ferrybridge", foes: [] });
  const raw = { ...C.read(store(pages)), "gravewounds-handoff": sent, "gravewounds-chars": J({ chars: [{ side: "York" }, { side: "Lancaster" }], wonBy: "York", events: [] }) };
  const first = C.suggest("march", C.status(raw, CD), {});
  assert.equal(first.phase, "fight");
  assert.equal(C.suggest("fight", C.status(raw, CD), { [first.mark]: true }).phase, "aftermath");
});
check("a fight won on the roller moves the campaign on only from the fight", () => {
  const raw = { ...C.read(store(pages)), "gravewounds-chars": J({ chars: [{ side: "York" }, { side: "Lancaster" }], wonBy: "York", events: [{ type: "strike" }] }) };
  assert.equal(C.suggest("fight", C.status(raw, CD), {}).phase, "aftermath");
  assert.equal(C.suggest("march", C.status(raw, CD), {}), null);
});
check("a save file holds every entry as stored, but never the narrator's", () => {
  const raw = C.read(store(pages)), f = C.saveFile({ ...raw, "gravewounds-narrator": "{}" }, "Towton");
  assert.equal(f.format, "grave-wounds-save");
  assert.ok(!("gravewounds-narrator" in f.keys));
  const text = JSON.stringify(f);                  // as the file is written, then read back
  const back = C.checkFile(JSON.parse(text));
  assert.deepEqual(back, raw);
});
check("a file that is not a save, or a damaged one, is refused", () => {
  assert.throws(() => C.checkFile({ hello: 1 }), /not a Grave Wounds save/);
  assert.throws(() => C.checkFile({ format: "grave-wounds-save", version: 2, keys: {} }), /version 2/);
  assert.throws(() => C.checkFile({ format: "grave-wounds-save", version: 1, keys: { "gravewounds-x": { a: 1 } } }), /damaged/);
  const keys = C.checkFile({ format: "grave-wounds-save", version: 1, keys: { "gravewounds-x": "1", "evil-key": "x", "gravewounds-narrator": "{}" } });
  assert.deepEqual(keys, { "gravewounds-x": "1" });
});

/* ----- what happens by itself: noticed once each ----- */
const CDN = { ...CD, weather: { rain: "Rain" }, diseases: { typhus: "Camp fever", fever: "Wound fever" } };
function apply(seen, r){                          // the news taken, as the console takes it
  for (const n of r.news) seen[n.mark] = n.value;
  for (const k of r.forget) delete seen[k];
  return seen;
}
const travelWith = (forces, day, wx = {}) => J({ mapId: "towton-1461", forces: { "towton-1461": forces }, clock: { "towton-1461": { day, used: 0 } }, wx: { "towton-1461": { days: wx } }, fought: [] });
const sickCase = d => ({ d, inc: 0, step: 3 }), incubating = d => ({ d, inc: 2, step: 0 });
check("a named man's death is news once, with what he died of and his force", () => {
  const raw = { ...C.read(store(pages)),
    "gravewounds-named": J({ a: { name: "Will", map: "towton-1461", force: 3, dead: true, died: "typhus", pid: "p1" }, b: { name: "Hal", dead: true, pid: "p2" } }),
    "gravewounds-purses": J({ p2: { lost: { why: "killed" } } }),
    "gravewounds-travel": travelWith([{ id: 3, name: "Edward's army", side: "York", men: 900 }], 2) };
  const r = C.notices(C.status(raw, CDN), { "day:towton-1461": 2 }, CDN);
  const whys = r.news.map(n => n.why);
  assert.ok(whys.includes("Will has died of camp fever, with Edward's army."), whys.join(" | "));
  assert.ok(whys.includes("Hal has died (killed)."), whys.join(" | "));
  assert.equal(C.notices(C.status(raw, CDN), apply({ "day:towton-1461": 2 }, r), CDN).news.length, 0);
});
check("sickness breaking out in a force is news once; over and back, news again; wounds are not sickness", () => {
  const ill = travelWith([{ id: 3, name: "Edward's army", side: "York", men: 900, health: { cases: [sickCase("typhus"), sickCase("typhus"), incubating("typhus"), sickCase("wound"), sickCase("fever")] } }], 2);
  const well = travelWith([{ id: 3, name: "Edward's army", side: "York", men: 900, health: { cases: [] } }], 2);
  const seen = { "day:towton-1461": 2 };
  let r = C.notices(C.status({ "gravewounds-travel": ill }, CDN), seen, CDN);
  assert.deepEqual(r.news.map(n => n.why).sort((a, b) => a.localeCompare(b)), ["Camp fever has broken out in Edward's army: 2 sick.", "Wound fever has broken out in Edward's army: 1 sick."]);
  apply(seen, r);
  assert.equal(C.notices(C.status({ "gravewounds-travel": ill }, CDN), seen, CDN).news.length, 0);
  r = C.notices(C.status({ "gravewounds-travel": well }, CDN), seen, CDN);
  assert.equal(r.forget.length, 2);
  apply(seen, r);
  assert.equal(C.notices(C.status({ "gravewounds-travel": ill }, CDN), seen, CDN).news.length, 2);
});
check("the end of a day: a map first seen is only marked; then one line for the days that ended, with the weather and each side", () => {
  const forces = [{ id: 1, name: "A", side: "York", men: 1500, health: { cases: [sickCase("typhus")] } }, { id: 2, name: "B", side: "Lancaster", men: 25000 }];
  const seen = {};
  let r = C.notices(C.status({ "gravewounds-travel": travelWith(forces, 1) }, CDN), seen, CDN);
  assert.deepEqual(r.news.filter(n => n.mark.startsWith("day:")).map(n => [n.value, n.why]), [[1, null]]);
  apply(seen, r);
  r = C.notices(C.status({ "gravewounds-travel": travelWith(forces, 2, { 1: { w: { cond: "rain", low: 3, high: 9 } } }) }, CDN), seen, CDN, c => c + " C");
  const day = r.news.find(n => n.mark === "day:towton-1461");
  assert.equal(day.why, "Day 1 has ended on the map of Towton, 1461: rain, 3 C to 9 C. York 1 force, 1,500 men, 1 sick; Lancaster 1 force, 25,000 men.");
  apply(seen, r);
  r = C.notices(C.status({ "gravewounds-travel": travelWith(forces, 5) }, CDN), seen, CDN);
  assert.match(r.news.find(n => n.mark === "day:towton-1461").why, /^Days 2 to 4 have ended on the map of Towton, 1461\. York/);
});
check("the end of a season in the team builder is news once, and moves the campaign to downtime", () => {
  const raw = { "gravewounds-xp": J({ p1: { stamp: 1700 }, p2: { stamp: 1700 }, p3: { stamp: 900 } }) };
  const r = C.notices(C.status(raw, CDN), {}, CDN), n = r.news.find(x => x.mark.startsWith("season:"));
  assert.equal(n.phase, "downtime");
  assert.match(n.why, /rolled for 2 men/);
  assert.equal(C.notices(C.status(raw, CDN), { [n.mark]: true }, CDN).news.length, 0);
});

check("a man taken prisoner is news once", () => {
  const raw = { "gravewounds-team-builder": J({ era: "medieval", team: [{ name: "Will", pid: "p1" }], prisoners: [{ name: "Hal", pid: "p2" }] }) };
  const r = C.notices(C.status(raw, CDN), {}, CDN);
  assert.deepEqual(r.news.filter(n => n.why).map(n => n.why), ["Hal has been taken prisoner."]);
  assert.equal(C.notices(C.status(raw, CDN), apply({}, r), CDN).news.length, 0);
});
check("a new rank is news; a rank first seen is only marked", () => {
  const CDR = { ...CDN, ranks: { medieval: { soldier: "Soldier", vintenar: "Vintenar" } } };
  const team = rank => ({ "gravewounds-team-builder": J({ era: "medieval", team: [{ name: "Will", pid: "p1", rank }] }) });
  const seen = apply({}, C.notices(C.status(team("soldier"), CDR), {}, CDR));
  assert.equal(seen["rank:p1"], "soldier");
  const r = C.notices(C.status(team("vintenar"), CDR), seen, CDR);
  assert.deepEqual(r.news.map(n => n.why), ["Will is now vintenar."]);
  assert.equal(C.notices(C.status(team("vintenar"), CDR), apply(seen, r), CDR).news.length, 0);
});
check("a force out of rations, water, medical stores or ammunition is news once; refilled and out again, news again", () => {
  const f = sup => travelWith([{ id: 3, name: "Edward's army", side: "York", men: 900, ...sup }], 2);
  const seen = { "day:towton-1461": 2 };
  let r = C.notices(C.status({ "gravewounds-travel": f({ sup: { rations: 0, med: 0, ammo: 1 }, supHungry: true }) }, CDN), seen, CDN);
  assert.deepEqual(r.news.map(n => n.why), ["Edward's army is out of rations.", "Edward's army is out of medical stores."]);
  apply(seen, r);
  assert.equal(C.notices(C.status({ "gravewounds-travel": f({ sup: { rations: 0, med: 0, ammo: 1 }, supHungry: true }) }, CDN), seen, CDN).news.length, 0);
  r = C.notices(C.status({ "gravewounds-travel": f({ sup: { rations: 3, med: 0, ammo: 1 }, supHungry: false }) }, CDN), seen, CDN);
  assert.deepEqual(r.forget, ["out:towton-1461:3:rations"]);
  apply(seen, r);
  r = C.notices(C.status({ "gravewounds-travel": f({ sup: { rations: 0, med: 0, ammo: 0 }, supHungry: true, thirsty: true }) }, CDN), seen, CDN);
  assert.deepEqual(r.news.map(n => n.why), ["Edward's army is out of rations.", "Edward's army is out of water.", "Edward's army is out of ammunition."]);
});

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
