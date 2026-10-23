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

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
