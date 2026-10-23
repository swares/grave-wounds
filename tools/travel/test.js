// The travel map's rules (templates/travelrules.js), run with no page, against the Python.
//   python3 tools/travel/parity.py [n] [seed]   (writes .cache/ and runs this with TRAVEL_PARITY=1)
// It reads parity.py's data bundle and cases from .cache/: weather and ground, routes and marches,
// camp work, who fights, and camp disease, each played through gravewounds/*.py, and plays each here
// on the same inputs and dice. Every result must be the same (numbers to within 1e-9).
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");

const makeTravelRules = require("../../templates/travelrules.js");
const ranks = require("../../templates/ranks.js");

const CACHE = path.join(__dirname, ".cache");
const readJson = p => JSON.parse(fs.readFileSync(p, "utf8"));
if (process.env.TRAVEL_PARITY !== "1" || !fs.existsSync(path.join(CACHE, "cases.json"))){
  console.error("Run it through python3 tools/travel/parity.py: the cases come from the Python.");
  process.exit(1);
}
const DATA = readJson(path.join(CACHE, "data.json"));
globalThis.TD = { hazards: DATA.hazards };          // ranks.js reads its data from TD, as on the page
const R = makeTravelRules(DATA, ranks);

let failed = 0, passed = 0;
function check(name, fn){
  try { fn(); passed++ } catch (e){ failed++; if (failed <= 20) console.error(`FAIL ${name}\n  ${e.message.split("\n").slice(0, 12).join("\n  ")}`) }
}
function same(a, b, where = ""){                      // deep equality, numbers to within 1e-9 (sines and roots may differ in the last bit)
  if (typeof a === "number" && typeof b === "number"){
    if (Math.abs(a - b) > 1e-9 * Math.max(1, Math.abs(b))) throw new Error(`${where}: ${a} != ${b}`);
    return;
  }
  if (a === undefined) a = null;
  if (b === undefined) b = null;
  if (a === null || b === null || typeof a !== "object" || typeof b !== "object"){
    if (a !== b) throw new Error(`${where}: ${JSON.stringify(a)} != ${JSON.stringify(b)}`);
    return;
  }
  if (Array.isArray(a) !== Array.isArray(b)) throw new Error(`${where}: array against object`);
  const keys = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const k of keys) same(a[k], b[k], `${where}.${k}`);
}
const orNone = v => (v === null ? undefined : v);    // Python's None for "the usual": the JavaScript's default
const scripted = rolls => { let i = 0; const f = () => { assert.ok(i < rolls.length, "asked for more dice than the Python used"); return rolls[i++] }; f.used = () => i; return f };

function weather(c){
  const m = DATA.maps[c.map];
  let prev = null, ground = null;
  for (const x of c.days){
    const w = R.rollWeather(m, x.day, prev, x.rolls);
    ground = R.nextGround(ground, w);
    const rest = R.nightRest(x.camp, w), o = x.out, at = `day ${x.day}`;
    same(w, o.w, at + " weather"); same(ground, o.ground, at + " ground");
    same(R.mapDate(m, x.day), o.date, at + " date");
    same(R.marchWindow(m, x.day), o.window, at + " marching hours");
    same(R.lightAt(m, x.day, x.hour, w.cond), o.light, at + " light");
    same(R.coldLevel(w.low), o.cold, at + " cold");
    same(rest, o.rest, at + " rest");
    same(R.fatigueAfter(x.fatigue, x.marched, w, ground, rest), o.fatigue, at + " fatigue");
    same(Object.fromEntries(Object.keys(DATA.terrain.terrain).map(t => [t, R.terrainPct(t, ground)])), o.pct, at + " terrain %");
    same(Object.keys(DATA.terrain.terrain).filter(t => R.flooded(t, ground)), o.flooded, at + " flooded");
    prev = w;
  }
}
function route(c){
  const m = DATA.maps[c.map], o = c.out, path = R.route(m, c.start, c.goal, c.ftype, c.ground);
  same(path, o.path, "route");
  for (const [k, v] of Object.entries(o.passable)) same(R.passable(m, k.split(",").map(Number), c.ftype, c.ground), v, "passable " + k);
  for (const [k, v] of Object.entries(o.fords)){
    const h = k.split(",").map(Number);
    same([R.fordHere(m, h, c.ground), R.tooDeep(m, h, c.ftype, c.ground)], v, "ford " + k);
  }
  if (!c.march) return;
  const a = c.march;
  same(R.schedule(m, path, c.ftype, a.day, a.used, { hpdList: a.hpd, ground: a.sground, speed: a.speed }), o.schedule, "schedule");
  same(R.advance(m, path, a.index, a.at, a.hours, { hpd: a.today, ftype: c.ftype, ground: c.ground, speed: a.speed, carried: a.carried }), o.advance, "advance");
  same(path.slice(1).map((h, i) => R.stepHours(m, path[i], h, c.ftype, c.ground, a.speed)), o.hours, "step hours");
  same(R.plan(m, c.start, [path[Math.floor(path.length / 2)], c.goal], c.ftype, c.ground), o.plan, "plan");
}
function camp(c){
  const start = { day: c.day, used: c.used };
  same(R.campDone(c.day, c.used, c.hours, c.hpd), c.out.done, "camp done");
  same(R.campWorked(start, c.later.day, c.later.used, c.hpd), c.out.worked, "camp worked");
  same(R.campLabourDone(c.camp, c.later.day, c.later.used, c.hpd), c.out.labour, "camp labour");
}
function fight(c){
  same(c.forces.map(a => c.forces.map(b => R.hexDistance(a.pos, b.pos))), c.dist, "distances");
  same(R.fightPlan(c.forces, c.sel, c.wait), c.out, "who fights");
}
function health(c){
  const rng = scripted(c.rolls);
  let h = c.init;
  for (const [i, s] of c.steps.entries()){
    const o = s.out, at = `step ${i} (${s.op})`, end = orNone(s.end);
    if (s.op === "week"){
      const factors = R.weekFactors(s.o), nurse = R.nursingOf(h, c.men, s.clean), extra = R.contagionOf(h, c.men);
      same(factors, o.factors, at + " factors"); same(nurse, o.nurse, at + " nursing"); same(extra, o.extra, at + " contagion");
      const ch = Object.fromEntries(Object.keys(DATA.disease.diseases).map(did => [did, [R.outbreakChance(did, factors, extra), R.catchChance(did, factors, end, extra),
        DATA.disease.nursing.spread[did] ? R.nurseChance(did, nurse, end) : 0]]));
      same(ch, o.chances, at + " chances"); same(R.scurvyChance(s.noFresh, end), o.scurvy, at + " scurvy chance");
      const r = R.healthWeek(h, c.men, factors, rng, end, { extra, nurse, noFresh: s.noFresh });
      same(r.events, o.events, at + " events"); h = r.health;
    } else {
      same(R.frostbiteChance(s.ctx.low, s.ctx.shelter, end), o.frost, at + " frostbite chance");
      const r = R.healthDay(h, s.ctx, rng, end);
      same(r.events, o.events, at + " events"); h = r.health;
    }
    same(h, o.health, at + " health"); same(rng.used(), o.used, at + " dice used");
    const n = R.healthCounts(h, c.men);
    same(n, o.counts, at + " counts"); same(R.sickMarchPct(n.fit, n.carried), o.pct, at + " march %");
  }
  const f = c.fresh;
  same([R.freshToday(f.forage, f.camped, f.issued, f.found), R.fieldcraftNeeded(f.forage, f.camped), R.leechBonus(f.leech)], f.out, "fresh food");
}
const KINDS = { weather, route, camp, fight, health };

const cases = readJson(path.join(CACHE, "cases.json"));
const count = {};
for (const [n, c] of cases.entries()){
  count[c.kind] = (count[c.kind] || 0) + 1;
  check(`${c.kind} case ${n}`, () => KINDS[c.kind](c));
}

console.log(`travel rules against the Python: ${Object.entries(count).map(([k, v]) => `${v} ${k}`).join(", ")}`);
console.log(failed ? `${failed} failed, ${passed} passed` : `all ${passed} passed`);
process.exit(failed ? 1 : 0);
