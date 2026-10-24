// The travel map's day (templates/travelday.js), run with no page.
//   python3 tools/travel/parity.py [n] [seed]   (writes .cache/ and runs this after test.js)
// On real maps, with named men in the forces and seeded dice: forces march on their routes to
// meet the enemy, make camp, rest, and the clock moves on, night after night, as the travel map's
// clock buttons move it. Checked: the same seed plays the same game; the state saved part way and
// restored into a fresh day plays on exactly as if it had never stopped; and after every move the
// state holds together (fatigue in range, forces on the map, the clock never going back, the weather
// rolled day by day from the first, with no gaps).
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");

const makeTravelRules = require("../../templates/travelrules.js");
const makeTravelDay = require("../../templates/travelday.js");

const CACHE = path.join(__dirname, ".cache");
if (process.env.TRAVEL_PARITY !== "1" || !fs.existsSync(path.join(CACHE, "shared.js"))){
  console.error("Run it through python3 tools/travel/parity.py: it writes the data and the shared files.");
  process.exit(1);
}
const DATA = JSON.parse(fs.readFileSync(path.join(CACHE, "data.json"), "utf8"));

// The browser the travel page runs in, as much as the day needs: storage, crypto's dice, and the
// shared rule files with the page's own names they read (as travel.html sets them).
const mem = new Map();
const store = {
  getItem: k => (mem.has(k) ? mem.get(k) : null), setItem: (k, v) => { mem.set(k, String(v)) }, removeItem: k => { mem.delete(k) },
  key: i => [...mem.keys()][i] ?? null, get length(){ return mem.size }, clear: () => mem.clear(),
};
Object.defineProperty(globalThis, "localStorage", { value: store, configurable: true });
let cryptoState = 1;
globalThis.crypto.getRandomValues = a => { for (let i = 0; i < a.length; i++){ cryptoState = (cryptoState * 48271) % 2147483647; a[i] = cryptoState } return a };
globalThis.TD = { checks: DATA.checks, training: DATA.training, loads: DATA.loads, weights: DATA.weights, supplies: DATA.supplies, kit: DATA.kit,
  stress: DATA.stress, hazards: DATA.hazards, languages: DATA.languages, era: { id: null, skills: [] } };
Object.assign(globalThis, require(path.join(CACHE, "shared.js")));
Object.assign(COINS, DATA.coins || {});
const RULES = makeTravelRules(DATA, { partyOf, hzCurrentBand, hzFordWater, spMedicalShort });
Object.assign(globalThis, { WK: DATA.works, CAMP_HEX_M: DATA.battle_hex_m, CG: DATA.ground,
  NEIGHBOURS: RULES.NEIGHBOURS, hexDistance: RULES.hexDistance, hkey: RULES.hkey, edgeKey: RULES.edgeKey });

let failed = 0, passed = 0;
function check(name, fn){
  try { fn(); passed++ } catch (e){ failed++; console.error(`FAIL ${name}\n  ${String(e.stack || e).split("\n").slice(0, 8).join("\n  ")}`) }
}
const parkMiller = seed => { let s = Math.max(1, seed % 2147483647); return () => { s = (s * 16807) % 2147483647; return 1 + (s % 100) } };

function fresh(seed){                               // an empty browser and a new day on these dice
  store.clear();
  cryptoState = seed * 7919 + 1;
  return { D: makeTravelDay(DATA, RULES, { roll100: parkMiller(seed) }), seed };
}
function setUp(D, mapId){                           // its forces as on the map, named men in two, each force's route to an enemy
  const S = D.S;
  S.mapId = mapId;
  const forces = D.forcesHere(), named = {}, purses = {};
  forces.slice(0, 2).forEach((f, k) => {
    for (let i = 0; i < 3; i++){
      const pid = `p${k}${i}`;
      named[`u${k}${i}`] = { name: `Man ${k}${i}`, endurance: 40 + 10 * i, map: mapId, force: f.id, pid, str: 35 + 15 * i, sex: "m", fieldcraft: 30 + 20 * i, leechcraft: 20 * i, log: [] };
      purses[pid] = { name: `Man ${k}${i}`, coins: { d: 150 } };
    }
  });
  store.setItem("gravewounds-named", JSON.stringify(named));
  store.setItem("gravewounds-purses", JSON.stringify(purses));
  forces.forEach((f, i) => { if (i % 2) f.loadOrder = "heavy" });
  for (const f of forces){
    const foe = forces.find(o => o.side !== f.side);
    if (foe) D.addWaypoint(f, foe.pos);
  }
}
const KINDS = ["event", "event", "hour", "nightfall", "event"];
function move(D, i){                                // one press of a clock button; now and then a camp or a rest
  const forces = D.forcesHere();
  if (i === 7 && forces[0]) D.makeCamp(forces[0], Object.keys(DATA.works.camps)[1]);
  if (i === 11 && forces[1]) D.restColumn(forces[1]);
  D.moveClock(KINDS[i % KINDS.length]);
  return D.S.msg;
}
function snapshot(D){                               // all a game is: the travel state and what the day keeps beside it
  D.save();
  return JSON.stringify(Object.fromEntries([...mem.entries()].sort(([a], [b]) => (a < b ? -1 : 1))));
}
function holds(D, before){                          // the state holds together after a move
  const S = D.S, m = D.curMap(), c = S.clock[S.mapId], L = DATA.weather.fatigue.levels.length;
  assert.ok(c && (c.day > before.day || (c.day === before.day && c.used >= before.used - 1e-9)), `the clock went back: ${JSON.stringify(before)} -> ${JSON.stringify(c)}`);
  const rolled = Object.keys(S.wx[S.mapId]?.days || {}).map(Number).sort((x, y) => x - y);
  assert.ok(rolled.every((d, i) => d === i + 1), `the weather is rolled day by day from the first: ${rolled}`);
  for (const f of D.forcesHere()){
    assert.ok(Number.isInteger(f.fatigue) && f.fatigue >= 0 && f.fatigue < L, `${f.name}: fatigue ${f.fatigue}`);
    assert.ok(f.pos[0] >= 0 && f.pos[1] >= 0 && f.pos[1] < m.rows.length && f.pos[0] < m.rows[0].length, `${f.name} off the map at ${f.pos}`);
    assert.ok(Number.isInteger(f.men) && f.men >= 0, `${f.name}: ${f.men} men`);
    assert.ok(f.day <= c.day + 1, `${f.name} is on day ${f.day}, the clock on ${c.day}`);
    const n = RULES.healthCounts(D.healthOf(f), f.men);
    assert.ok(n.unfit <= Math.max(f.men, n.unfit) && n.fit >= 0, `${f.name}: health ${JSON.stringify(n)}`);
  }
  return { day: c.day, used: c.used };
}
function play(mapId, seed, moves, stopAt = null){   // -> the snapshot after `moves` presses; stopAt saves and restores into a new day there
  let D = fresh(seed).D;
  setUp(D, mapId);
  let at = D.clockNow() && { ...D.S.clock[mapId] }, msgs = [];
  for (let i = 0; i < moves; i++){
    if (i === stopAt){                                // the page closed and opened again: only what was saved goes on
      D.save();
      D = makeTravelDay(DATA, RULES, { roll100: D.roll100 });   // the same dice, going on
      D.restore();
      assert.equal(D.S.mapId, mapId);
    }
    msgs.push(move(D, i));
    at = holds(D, at);
  }
  return { snap: snapshot(D), msgs, day: D.S.clock[mapId].day };
}

const MAPS = ["towton-1461", "agincourt-1415", "bull-run-1861", "generic-valley", "chosin-1950"].filter(id => DATA.maps[id]);
const MOVES = 24;
for (const id of MAPS){
  let a = null;
  check(`${id}: plays ${MOVES} moves of the clock, the state holding together`, () => { a = play(id, 5, MOVES) });
  if (!a) continue;
  check(`${id}: the same dice play the same game`, () => assert.equal(play(id, 5, MOVES).snap, a.snap));
  check(`${id}: other dice play another`, () => assert.notEqual(play(id, 6, MOVES).snap, a.snap));
  check(`${id}: saved part way and restored into a new day, it plays on as if it had not stopped`, () => {
    const b = play(id, 5, MOVES, 9);
    assert.equal(b.snap, a.snap);
  });
  check(`${id}: the clock moved on and something happened`, () => {
    assert.ok(a.day >= 2, `still day ${a.day}`);
    assert.ok(a.msgs.some(m => /meet|arrives|Night passes|marching is done/.test(m)), a.msgs.slice(0, 4).join(" | "));
  });
}
// The campaign console's way in: it never holds the day, it starts from what is saved each time.
check("the console's march: a summary looks without changing anything, a step moves on and saves", () => {
  const D = fresh(21).D;
  setUp(D, "towton-1461");
  D.save();
  const before = snapshot(D), sum = makeTravelDay(DATA, RULES).marchSummary();
  assert.equal(snapshot(D), before, "the summary changed the saved state");
  assert.ok(sum.forces.length >= 2 && sum.day === 1 && sum.working, JSON.stringify(sum).slice(0, 200));
  assert.ok(sum.forces.some(f => f.order.startsWith("marching to")), sum.forces.map(f => f.order).join(", "));
  let r = null, n = 0;
  do { r = makeTravelDay(DATA, RULES, { roll100: parkMiller(99 + n) }).marchStep(); n++ } while (!r.met.length && n < 20);
  assert.ok(r.met.length && r.met[0].length === 2, `no meeting after ${n} steps: ${r.text}`);
  assert.match(r.text, /meet/);
  const saved = JSON.parse(store.getItem("gravewounds-travel"));
  assert.deepEqual(saved.clock["towton-1461"], { day: r.day, used: r.used }, "the step was not saved");
  const orders = makeTravelDay(DATA, RULES).marchSummary().forces.map(f => f.order);
  assert.ok(orders.some(o => o.startsWith("halted")) && !orders.some(o => o.startsWith("busy")), `after the meeting: ${orders.join(", ")}`);
});
check("the console's march with nothing saved: it says to choose a map", () => {
  store.clear();
  const D = makeTravelDay(DATA, RULES);
  assert.equal(D.marchSummary(), null);
});
check("the day runs with no page: no document or window", () => assert.equal(typeof document + typeof window, "undefinedundefined"));

const tally = failed ? `${failed} failed, ${passed} passed` : `all ${passed} passed`;
console.log(`travel day on ${MAPS.length} maps: ${tally}`);
process.exit(failed ? 1 : 0);
