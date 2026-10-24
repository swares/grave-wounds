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
check("the console's fights: offered where enemies are within reach, sent as Fight here sends them, a battle's result taken in once", () => {
  const D = fresh(31).D;
  setUp(D, "towton-1461");
  D.save();
  let n = 0;
  while (!makeTravelDay(DATA, RULES).fightsOnOffer().length && n++ < 20) makeTravelDay(DATA, RULES, { roll100: parkMiller(40 + n) }).marchStep();
  const fights = makeTravelDay(DATA, RULES).fightsOnOffer(), x = fights[0];
  assert.ok(x, "no fight on offer after the forces met");
  assert.ok(x.title.includes(" against ") && x.options[0].when && /Surprise: \d+%/.test(x.options[0].note), JSON.stringify(x).slice(0, 300));
  assert.equal(x.maps[0][0], "roller");
  const keys = new Set(fights.map(f => f.title));
  assert.equal(keys.size, fights.length, "the same fight offered twice");
  const page = makeTravelDay(DATA, RULES, { roll100: parkMiller(77) }).sendFightFor(x.id, 0, "roller");
  assert.equal(page, "roller.html");
  const h = JSON.parse(store.getItem("gravewounds-handoff"));
  assert.ok(h.from === "travel" && h.foes.length && h.surprise && typeof h.surprise.roll === "number" && h.place, JSON.stringify(h).slice(0, 200));
  assert.equal(makeTravelDay(DATA, RULES).sendFightFor(x.id, 0, "field"), "field.html");
  const fh = JSON.parse(store.getItem("gravewounds-field-handoff"));
  assert.ok(fh.forces.some(f => f.role === "defender") && fh.forces.some(f => f.role === "attacker") && fh.start, JSON.stringify(fh).slice(0, 200));
  const t = JSON.parse(store.getItem("gravewounds-travel")), f = t.forces["towton-1461"][0];
  store.setItem("gravewounds-field-result", JSON.stringify({ battle: fh.battle, mapId: "towton-1461", place: fh.place, minutes: 90, start: fh.start,
    forces: { [f.id]: { lost: 100, killed: 80, left: 10, died: 10, cases: [{ d: "wound", inc: 0, step: 3, peak: 0, shown: 0, chronic: false, inf: "low", fever: 2 }] } } }));
  const said = makeTravelDay(DATA, RULES).takeBattle();
  assert.match(said, /battle at .* is over/);
  const after = JSON.parse(store.getItem("gravewounds-travel")), g = after.forces["towton-1461"][0];
  assert.equal(g.men, f.men - 100);
  assert.ok(after.fought.includes(fh.battle) && store.getItem("gravewounds-field-result") === null);
  assert.equal(makeTravelDay(DATA, RULES).takeBattle(), null, "taken twice");
});
check("the console's orders: routes, march and halt, camp and rest, given from the saved day and saved", () => {
  const D = fresh(51).D;
  D.S.mapId = "towton-1461";
  D.forcesHere();
  D.save();
  const day = () => makeTravelDay(DATA, RULES, { roll100: parkMiller(9) });
  const saved = () => JSON.parse(store.getItem("gravewounds-travel")).forces["towton-1461"];
  const o = day().orderChoices(saved()[0].id), id = o.id;
  assert.ok(o.places.length > 3 && o.foes.length && o.camps.length && !o.led && !o.routed, JSON.stringify(o).slice(0, 200));
  let said = day().giveOrder(id, "to", o.places[0][0]);
  let f = saved().find(x => x.id === id);
  assert.match(said, /will march to/);
  assert.equal(f.order, "march");
  assert.deepEqual(f.waypoints, [o.places[0][0].split(",").map(Number)]);
  said = day().giveOrder(id, "via", o.foes[0][0]);
  assert.equal(saved().find(x => x.id === id).waypoints.length, 2, said);
  const before = JSON.stringify(saved().find(x => x.id === id).waypoints);
  const m = DATA.maps["towton-1461"], keyOf = Object.values(DATA.terrain.terrain).find(t => t.cost === null || t.cost === undefined)?.key;
  const r = m.rows.findIndex(row => keyOf && row.includes(keyOf)), bad = r >= 0 ? `${m.rows[r].indexOf(keyOf)},${r}` : null;
  if (bad){
    said = day().giveOrder(id, "to", bad);
    assert.match(said, /cannot/);
    assert.equal(JSON.stringify(saved().find(x => x.id === id).waypoints), before, "a refused route changed the route");
  }
  assert.match(day().giveOrder(id, "halt"), /halts/);
  assert.equal(saved().find(x => x.id === id).order, "halt");
  assert.match(day().giveOrder(id, "march"), /will march/);
  assert.match(day().giveOrder(id, "clear"), /cleared/);
  f = saved().find(x => x.id === id);
  assert.ok(!f.path && f.order === "halt" && !f.waypoints.length);
  const camp = o.camps.find(c => c[3])[0];
  day().giveOrder(id, "camp", camp);
  assert.equal(saved().find(x => x.id === id).camp.kind, camp);
  const other = saved()[1].id;
  assert.match(day().giveOrder(other, "rest"), /rests/);
  assert.ok(saved().find(x => x.id === other).day >= 2);
  assert.match(day().giveOrder(999, "halt"), /not on the map/);
});
check("the console's march with nothing saved: it says to choose a map", () => {
  store.clear();
  const D = makeTravelDay(DATA, RULES);
  assert.equal(D.marchSummary(), null);
});
const CLEAR = new Set(["open", "farmland", "heath", "road"]);   // ground where a force is in plain sight
check("fog of war: a side sees the enemy within its sight, not beyond it, nor in woods unless next to it", () => {
  const { D } = fresh(3);
  D.S.mapId = "towton-1461";
  const fs = D.forcesHere(), a = fs[0], e = fs.find(o => o.side !== a.side), m = D.curMap();
  const open = []; for (let r = 0; r < m.rows.length; r++) for (let c = 0; c < m.rows[0].length; c++) if (CLEAR.has(RULES.terrainAt(m, [c, r]).id)) open.push([c, r]);
  const forest = []; for (let r = 0; r < m.rows.length; r++) for (let c = 0; c < m.rows[0].length; c++) if (RULES.terrainAt(m, [c, r]).id === "forest") forest.push([c, r]);
  for (const f of fs) f.pos = [0, 0];                         // the others out of the way
  for (const f of fs.filter(o => o !== a && o !== e)) f.pos = null;
  a.type = "foot"; a.pos = open[0];
  const reach = D.sightOf(a);
  assert.ok(reach >= 1);
  const at = d => open.find(h => RULES.hexDistance(h, a.pos) === d);
  e.pos = at(reach);
  assert.deepEqual(D.sightings(a.side).map(x => x.id), [e.id], `seen at ${reach} hexes`);
  e.pos = at(reach + 1);
  assert.deepEqual(D.sightings(a.side), [], "not seen beyond its sight");
  a.type = "mounted";
  if (D.sightOf(a) > reach){ assert.deepEqual(D.sightings(a.side).map(x => x.id), [e.id], "horse sees further") }
  a.type = "foot";
  const wood = forest.find(h => RULES.hexDistance(h, a.pos) === 2) || forest.find(h => RULES.hexDistance(h, a.pos) > 1);
  if (wood){
    e.pos = wood;
    assert.deepEqual(D.sightings(a.side), [], "not seen in woods, two hexes off");
    const next = RULES.neighbours(a.pos, m.rows[0].length, m.rows.length)[0];
    e.pos = next;
    assert.deepEqual(D.sightings(a.side).map(x => x.id), [e.id], "next to it: always seen");
  }
});
check("fog of war: the weather and the dark cut how far a force sees", () => {
  const { D } = fresh(4);
  D.S.mapId = "towton-1461";
  const a = D.forcesHere()[0], H = DATA.terrain.sight.hexes;
  a.type = "mounted";
  const X = D.wxState(); D.dayWeather(1);
  const day = { ...X.days[1].w };
  X.days[1].w = { ...day, cond: "fog" };
  assert.equal(D.sightOf(a), 1, "fog: one hex");
  X.days[1].w = { ...day, cond: "rain" };
  assert.equal(D.sightOf(a, { cond: "rain", light: "day" }), Math.max(1, Math.floor(H.mounted / 2)), "rain: halved");
  assert.equal(D.sightOf(a, { cond: "fair", light: "night" }), 1, "a dark night: one hex");
  assert.equal(D.sightOf(a, { cond: "fair", light: "day" }), H.mounted, "a clear day: its full sight");
});
check("fog of war: a player's view holds his side's forces and only the enemy it sees, or saw", () => {
  const { D } = fresh(5);
  D.S.mapId = "towton-1461";
  const fs = D.forcesHere(), a = fs[0], e = fs.find(o => o.side !== a.side), m = D.curMap();
  for (const f of fs.filter(o => o.side !== a.side && o !== e)) f.pos = null;
  const open = []; for (let r = 0; r < m.rows.length; r++) for (let c = 0; c < m.rows[0].length; c++) if (CLEAR.has(RULES.terrainAt(m, [c, r]).id)) open.push([c, r]);
  a.pos = open[0]; a.type = "foot";
  e.pos = open.find(h => RULES.hexDistance(h, a.pos) === 1);
  D.save();
  D.noteSightings(); D.save();
  let v = makeTravelDay(DATA, RULES).fogView(a.side);
  assert.deepEqual(v.seen.map(x => x.name), [e.name], "seen next to him");
  assert.match(v.seen[0].size, /^about |^fewer than/, "a rough size, not his count");
  assert.ok(!("men" in v.seen[0]) && !("route" in v.seen[0]) && !("health" in v.seen[0]), "nothing else of the enemy's");
  assert.ok(v.ours.every(f => f.side === a.side) && v.ours.some(f => f.name === a.name));
  e.pos = open.find(h => RULES.hexDistance(h, a.pos) > 10);
  D.save();
  v = makeTravelDay(DATA, RULES).fogView(a.side);
  assert.deepEqual(v.seen, [], "gone out of sight");
  assert.equal(v.last.length, 1, "remembered where it was last seen");
  assert.ok(RULES.hexDistance(v.last[0].pos, a.pos) === 1 && v.last[0].when.includes(","), JSON.stringify(v.last[0]));
  assert.ok(!JSON.stringify(v).includes(JSON.stringify(e.pos)), "and not where it is now");
  const theirs = makeTravelDay(DATA, RULES).fogView(e.side);
  assert.ok(theirs.ours.every(f => f.side === e.side), "the other side's view is its own");
});
check("the day runs with no page: no document or window", () => assert.equal(typeof document + typeof window, "undefinedundefined"));

const tally = failed ? `${failed} failed, ${passed} passed` : `all ${passed} passed`;
console.log(`travel day on ${MAPS.length} maps: ${tally}`);
process.exit(failed ? 1 : 0);
