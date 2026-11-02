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
const CLEAR_DAY = { cond: "fair", light: "day" };
function lone(D){                                   // one force of each side on the map's clear ground, the rest off it
  const fs = D.forcesHere(), a = fs[0], e = fs.find(o => o.side !== a.side), m = D.curMap();
  for (const f of fs) if (f !== a && f !== e) f.pos = null;
  const hexes = id => { const out = []; for (let r = 0; r < m.rows.length; r++) for (let c = 0; c < m.rows[0].length; c++) if (id(RULES.terrainAt(m, [c, r]).id)) out.push([c, r]); return out };
  const open = hexes(t => CLEAR.has(t));
  a.pos = open[Math.floor(open.length / 2)];
  const at = (km, where = open) => where.find(h => Math.abs(RULES.hexDistance(h, a.pos) * m.hex_km - km) < 1e-9);
  return { a, e, m, at, forest: hexes(t => t === "forest") };
}
check("fog of war: a side sees the enemy within its sight in km, not beyond, nor in woods unless its outposts are on it", () => {
  const { D } = fresh(3);
  D.S.mapId = "towton-1461";                        // 1 km hexes
  const { a, e, at, forest } = lone(D), K = DATA.terrain.sight;
  a.type = "foot";
  assert.equal(D.sightOf(a, CLEAR_DAY), K.km.foot);
  e.pos = at(K.km.foot);
  assert.deepEqual(D.sightings(a.side).map(x => x.id), [e.id], `seen at ${K.km.foot} km`);
  e.pos = at(K.km.foot + 1);
  assert.deepEqual(D.sightings(a.side), [], "not seen beyond its sight");
  a.type = "mounted";
  assert.deepEqual(D.sightings(a.side).map(x => x.id), [e.id], "a mounted force, its patrols out, sees further");
  a.type = "foot";
  const wood = at(2, forest);
  if (wood){
    e.pos = wood;
    assert.deepEqual(D.sightings(a.side), [], "not seen in woods, 2 km off");
    e.pos = at(K.contact_km, forest) || at(K.contact_km);
    assert.deepEqual(D.sightings(a.side).map(x => x.id), [e.id], "within its outposts' reach: always found");
  }
});
check("fog of war: in km, so a map's hex size does not change how far a force sees", () => {
  for (const id of ["towton-1461", "agincourt-1415", "mogadishu-1993"].filter(x => DATA.maps[x])){
    const { D } = fresh(6), keep = DATA.maps[id].sight;
    delete DATA.maps[id].sight;                       // naked-eye sight alone: no aircraft up
    D.S.mapId = id;
    const { a, e, m, at } = lone(D), K = DATA.terrain.sight;
    a.type = "foot";
    const near = at(Math.floor(K.km.foot / m.hex_km) * m.hex_km), far = at((Math.floor(K.km.foot / m.hex_km) + 1) * m.hex_km);
    if (near){ e.pos = near; assert.equal(D.sightings(a.side).length, 1, `${id}: seen within ${K.km.foot} km`) }
    if (far && (Math.floor(K.km.foot / m.hex_km) + 1) * m.hex_km > Math.max(K.km.foot, K.contact_km)){ e.pos = far; assert.equal(D.sightings(a.side).length, 0, `${id}: not beyond`) }
    if (keep) DATA.maps[id].sight = keep;
  }
});
check("fog of war: the weather and the dark cut how far a force sees", () => {
  const { D } = fresh(4);
  D.S.mapId = "towton-1461";
  const a = D.forcesHere()[0], K = DATA.terrain.sight, vis = c => DATA.weather.conditions[c].visibility * DATA.battle_hex_m * K.weather_mass / 1000;
  a.type = "mounted";
  assert.equal(D.sightOf(a, CLEAR_DAY), K.km.mounted, "a clear day: its full sight");
  assert.equal(D.sightOf(a, { cond: "fog", light: "day" }), vis("fog"), "fog");
  assert.equal(D.sightOf(a, { cond: "rain", light: "day" }), vis("rain"), "rain");
  assert.ok(vis("fog") < vis("rain") && vis("rain") < K.km.foot, "fog cuts more than rain, and both less than a clear day");
  assert.equal(D.sightOf(a, { cond: "fair", light: "dusk" }), K.km.mounted * K.dusk, "dusk");
  assert.equal(D.sightOf(a, { cond: "fair", light: "moonlit" }), K.moonlit_km, "by moonlight");
  assert.equal(D.sightOf(a, { cond: "fair", light: "night" }), K.night_km, "a dark night");
});
check("fog of war: by day in flying weather a side with aircraft up sees every enemy force in the open on the map, not in cover, nor at night", () => {
  const { D } = fresh(7);
  D.S.mapId = "chosin-1950";                         // the UN had the air (data/maps sight.air)
  const { a, e, m, at, forest } = lone(D), K = DATA.terrain.sight, air = DATA.maps["chosin-1950"].sight.air;
  const ours = air.includes(a.side) ? a : e, theirs = ours === a ? e : a;
  assert.ok(D.airUp(ours.side, CLEAR_DAY), "its aircraft are up on a clear day");
  assert.ok(!D.airUp(theirs.side, CLEAR_DAY), "the other side has none up");
  assert.ok(!D.airUp(ours.side, { cond: "fog", light: "day" }) && !D.airUp(ours.side, { cond: "fair", light: "night" }) && !D.airUp(ours.side, { cond: "fair", light: "dusk" }), "grounded in fog, at dusk and in the dark");
  const v = D.fogView(ours.side), flying = v.light === "day" && K.air_weather.includes(Object.keys(DATA.weather.conditions).find(c => DATA.weather.conditions[c].name === v.weather) || "fair");
  assert.equal(v.air, flying, "the player's view says whether its aircraft are up");
  const opens = []; for (let r = 0; r < m.rows.length; r++) for (let c = 0; c < m.rows[0].length; c++) if (CLEAR.has(RULES.terrainAt(m, [c, r]).id) && RULES.hexDistance([c, r], ours.pos) * m.hex_km > K.km.mounted + 1) opens.push([c, r]);
  theirs.pos = opens[0];
  assert.ok(theirs.pos, "an open hex far off");
  assert.equal(D.sightings(ours.side).length, flying ? 1 : 0, "seen from the air, far beyond its forces' sight, only while its aircraft are up");
  const wood = forest.find(h => RULES.hexDistance(h, ours.pos) * m.hex_km > K.contact_km + 1);
  if (wood){ theirs.pos = wood; assert.equal(D.sightings(ours.side).length, 0, "woods hide a force from the air") }
});
check("fog of war: a side's night sights see further in the dark, never beyond the day's sight", () => {
  const { D } = fresh(8);
  D.S.mapId = "easting73-1991";                      // thermal sights for the Coalition (data/maps sight.night)
  const fs = D.forcesHere(), K = DATA.terrain.sight, night = DATA.maps["easting73-1991"].sight.night;
  const ours = fs.find(f => night[f.side]), theirs = fs.find(f => !night[f.side]);
  const dev = DATA.weather.light.night_vision.devices[night[ours.side]], km = dev.sight * DATA.battle_hex_m * K.weather_mass / 1000;
  ours.type = theirs.type = "foot";
  assert.equal(D.deviceKm(ours.side), km, "its device's sight, as for a body of troops");
  assert.equal(D.sightOf(ours, { cond: "fair", light: "night" }), Math.min(K.km.foot, km), "a dark night: its device's sight");
  assert.equal(D.sightOf(ours, { cond: "fair", light: "moonlit" }), Math.min(K.km.foot, km), "by moonlight too");
  assert.equal(D.sightOf(ours, CLEAR_DAY), K.km.foot, "by day no further than without");
  assert.equal(D.sightOf(theirs, { cond: "fair", light: "night" }), K.night_km, "the side without: naked eye");
  assert.ok(D.sightOf(ours, { cond: "fog", light: "night" }) <= DATA.weather.conditions.fog.visibility * DATA.battle_hex_m * K.weather_mass / 1000 + 1e-9, "never beyond the weather's sight");
});
check("sieges: a garrison shut in its fortress is not fought until the breach is practicable; each day of siege work counts towards it", () => {
  const { D } = fresh(9);
  D.S.mapId = "jacobsford-1179";
  const fs = D.forcesHere(), pl = D.fortresses()[0], F = pl.fortress, c = { day: 1, used: 0 };
  assert.ok(pl && F.breach_days > 0, "the castle is a fortress");
  const g = fs.find(f => f.side === F.side && D.sameHex(f.pos, pl.hex)), foot = fs.find(f => f.side !== F.side && f.tools);
  foot.pos = [pl.hex[0] + 1, pl.hex[1]]; foot.marched = 0; foot.day = 1;
  assert.deepEqual(D.fightOptions(g)[0].attackers, [], "no storm before the breach");
  assert.ok(D.siegeState(pl).invested, "invested");
  foot.men = F.workers / 2;
  D.siegeNight(c);
  assert.equal(D.siegeState(pl).days, 0.5, "half the workers wanted: half a day");
  foot.men = F.workers * 3;
  foot.marched = 2;
  D.siegeNight(c);
  assert.equal(D.siegeState(pl).days, 0.5, "a day it marched: no work");
  foot.marched = 0;
  for (let n = 0; n < F.breach_days; n++) D.siegeNight(c);
  assert.equal(F.by, "mine", "Jacob's Ford's castle is broken by a mine");
  assert.ok(D.siegeState(pl).ready && !D.siegeState(pl).practicable, "the mine dug: ready to fire, the wall still stands");
  assert.deepEqual(D.fightOptions(g)[0].attackers, [], "no storm before the mine brings the wall down");
  let fired = 0;
  for (let n = 0; n < 40 && !D.siegeState(pl).practicable; n++){
    if (D.siegeState(pl).ready){ D.save(); D.fireMine(pl.name); D.restore(); fired++ }
    else { for (const f of D.forcesHere()) f.marched = 0; D.siegeNight(c) }
  }
  assert.ok(D.siegeState(pl).practicable && fired >= 1, "fired until it brings the wall down (a miss: dug again)");
  assert.deepEqual(D.fightOptions(g)[0].attackers, [foot.id], "the storm is offered once the breach is practicable");
  const v = D.fogView(g.side);
  assert.deepEqual(v.sieges, [{ name: pl.name, practicable: true, ours: true }], "the garrison's players see the siege");
});
check("sieges: an invested garrison eats its fortress's stores; summoned, it accepts or refuses terms", () => {
  const { D } = fresh(10);
  D.S.mapId = "jacobsford-1179";
  const fs = D.forcesHere(), pl = D.fortresses()[0], F = pl.fortress, c = { day: 1, used: 0 };
  const g = fs.find(f => f.side === F.side && D.sameHex(f.pos, pl.hex)), foot = fs.find(f => f.side !== F.side && f.tools);
  foot.pos = [pl.hex[0] + 1, pl.hex[1]]; foot.marched = 0; foot.day = 1;
  g.fed = false;
  assert.ok(D.fedByArmy(g), "invested, fed from the fortress's stores");
  D.siegeNight(c);
  assert.equal(D.siegeState(pl).stores, F.stores - 1, "a day of stores eaten");
  D.S.sieges[D.S.mapId][pl.name].stores = 0;
  assert.ok(!D.fedByArmy(g), "stores gone: not fed");
  D.save();
  const T = DATA.terrain.siege.terms;
  assert.equal(D.termsChance(pl).chance, T.before, "before the breach");
  let msg = D.summon(pl.name, "refuse");
  assert.match(msg, /refuses terms/);
  D.restore();
  assert.deepEqual(D.noQuarterIn([g.id]), [], "refused before the breach: quarter as usual");
  D.S.sieges[D.S.mapId][pl.name].days = F.breach_days; D.S.sieges[D.S.mapId][pl.name].blown = true;
  D.save();
  assert.equal(D.termsChance(pl).chance, T.breach, "the breach practicable");
  msg = D.summon(pl.name, "refuse");
  assert.match(msg, /no quarter/);
  D.restore();
  assert.deepEqual(D.noQuarterIn([g.id, foot.id]), [g.id], "refused after the breach: the garrison gets no quarter");
  msg = D.summon(pl.name, "accept");
  D.restore();
  const g2 = D.forcesHere().find(f => f.id === g.id);
  assert.match(msg, /honours of war/);
  assert.equal(D.siegeState(pl).side, foot.side, "the place passes to the besiegers");
  assert.equal(g2.order, "march", "the garrison marches out");
});
check("sieges: a sortie can be fought from behind the walls and, if it succeeds, costs a day of work; unbesieged, the garrison repairs", () => {
  const { D } = fresh(11);
  D.S.mapId = "jacobsford-1179";
  const fs = D.forcesHere(), pl = D.fortresses()[0], F = pl.fortress, c = { day: 1, used: 0 };
  const g = fs.find(f => f.side === F.side && D.sameHex(f.pos, pl.hex)), foot = fs.find(f => f.side !== F.side && f.tools);
  foot.pos = [pl.hex[0] + 1, pl.hex[1]]; foot.marched = 0; foot.day = 1;
  D.S.sieges[D.S.mapId] = { [pl.name]: { days: 2.5 } };
  D.save();
  assert.deepEqual(D.fightOptions(foot)[0].attackers.filter(id => id === g.id), [], "no sortie ordered: the walls keep them apart");
  D.sortie(pl.name, "order");
  D.restore();
  assert.ok(D.fightOptions(foot)[0].attackers.includes(g.id), "a sortie: the garrison can fight the besiegers");
  assert.ok(!D.nearFields(foot).some(([, b]) => b.place === pl.name), "the storm battlefield is not offered for a sortie");
  assert.deepEqual(D.fightOptions(g)[0].attackers, [], "but no storm of the garrison before the breach");
  D.sortie(pl.name, "success");
  D.restore();
  assert.equal(D.siegeState(pl).days, 2.5 - DATA.terrain.siege.sortie_cost, "a day of work lost");
  assert.ok(!D.siegeState(pl).sortie, "the sortie is over");
  const far = D.forcesHere().find(f => f.id === foot.id);
  far.pos = [pl.hex[0] + 6, pl.hex[1]];
  D.siegeNight(c);
  assert.equal(D.siegeState(pl).days, 1.5 - DATA.terrain.siege.repair, "not invested: the garrison repairs");
});
check("sieges: the besiegers' lines count as a filthy camp from the investment; the unburied dead bring sickness until buried", () => {
  const { D } = fresh(12);
  D.S.mapId = "jacobsford-1179";
  const fs = D.forcesHere(), pl = D.fortresses()[0], F = pl.fortress, c = { day: 1, used: 0 };
  const g = fs.find(f => f.side === F.side && D.sameHex(f.pos, pl.hex)), foot = fs.find(f => f.side !== F.side && f.tools);
  foot.pos = [pl.hex[0] + 1, pl.hex[1]]; foot.marched = 0; foot.day = 1;
  D.siegeNight(c);
  assert.deepEqual([foot.siegeFrom?.role, g.siegeFrom?.role], ["besieger", "garrison"], "both sides count from the investment");
  assert.equal(D.hygieneOf(foot, null), DATA.terrain.siege.lines_hygiene, "siege lines with no camp: filthy");
  assert.equal(D.hygieneOf(g, null), "fair", "the garrison: as its camp");
  foot.day = 1 + DATA.disease.staying_days;
  const fac = D.weekFactorsFor(foot, null, "poor");
  assert.ok(fac.includes("staying") && fac.includes("crowded"), "a month in filthy siege lines: staying and crowded");
  assert.ok(!fac.includes("dead"), "no dead yet");
  D.S.dead[D.S.mapId] = [{ hex: pl.hex.slice(), day: foot.day - 2, place: pl.name }];
  assert.ok(D.weekFactorsFor(foot, null, "poor").includes("dead"), "a battle's dead within a hex");
  D.S.dead[D.S.mapId][0].buried = true;
  assert.ok(!D.weekFactorsFor(foot, null, "poor").includes("dead"), "buried: gone");
  D.S.dead[D.S.mapId][0].buried = false; D.S.dead[D.S.mapId][0].day = foot.day - DATA.disease.dead_days;
  assert.ok(!D.weekFactorsFor(foot, null, "poor").includes("dead"), "after dead_days: gone");
  foot.pos = [pl.hex[0] + 6, pl.hex[1]];
  D.siegeNight({ day: foot.day, used: 0 });
  assert.equal(foot.siegeFrom, undefined, "no longer investing");
});
check("sieges: Badajoz 1812 is invested from the start, and its breach is practicable after 21 days of the siege corps' work", () => {
  const { D } = fresh(13);
  D.S.mapId = "badajoz-1812";
  const pl = D.fortresses()[0], F = pl.fortress;
  assert.equal(pl.name, "Badajoz");
  assert.ok(D.siegeState(pl).invested, "the siege corps starts within a hex of the town");
  const c = { day: 1, used: 0 };
  for (let n = 1; n <= F.breach_days; n++){ for (const f of D.forcesHere()) f.day = n; c.day = n; D.siegeNight(c) }
  assert.ok(D.siegeState(pl).practicable, "practicable after the night of day 21 (5 April), stormed on the 22nd (6 April)");
  assert.ok(D.nearFields(D.forcesHere().find(f => f.side === F.side && D.sameHex(f.pos, pl.hex))).some(([id]) => id === "badajoz-1812"), "the storm on the Badajoz battlefield");
});
check("sieges: Burgos 1812 is invested from the start, and its mine is dug after 10 days of the siege corps' work", () => {
  const { D } = fresh(17);
  D.S.mapId = "burgos-1812";
  const pl = D.fortresses()[0], F = pl.fortress;
  assert.equal(pl.name, "Burgos"); assert.equal(F.by, "mine");
  assert.ok(D.siegeState(pl).invested, "the siege corps starts within a hex of the castle");
  const c = { day: 1, used: 0 };
  for (let n = 1; n <= F.breach_days; n++){ for (const f of D.forcesHere()) f.day = n; c.day = n; D.siegeNight(c) }
  const st = D.siegeState(pl);
  assert.ok(st.ready && !st.practicable, "dug after the night of day 10 (28 September), fired on the 29th: not practicable until it is");
  assert.ok(D.nearFields(D.forcesHere().find(f => f.side === F.side && D.sameHex(f.pos, pl.hex))).some(([id]) => id === "burgos-1812"), "the hornwork battlefield");
});
check("sieges: a mine fired falls short (dug again) or brings the wall down; a countermine may find it", () => {
  const { D } = fresh(14);
  D.S.mapId = "jacobsford-1179";
  const fs = D.forcesHere(), pl = D.fortresses()[0], F = pl.fortress, M = DATA.terrain.siege.mine;
  const g = fs.find(f => f.side === F.side && D.sameHex(f.pos, pl.hex)), foot = fs.find(f => f.side !== F.side && f.tools);
  foot.pos = [pl.hex[0] + 1, pl.hex[1]]; foot.marched = 0; foot.day = 1;
  D.S.sieges[D.S.mapId] = { [pl.name]: { days: F.breach_days } };
  D.save();
  let short = 0, down = 0;
  for (let n = 0; n < 60; n++){
    D.S.sieges[D.S.mapId][pl.name] = { days: F.breach_days }; D.save();
    const msg = D.fireMine(pl.name); D.restore();
    if (/falls short/.test(msg)){ short++; assert.equal(D.siegeState(pl).days, F.breach_days - F.redig, "fell short: redig days to dig again") }
    else { down++; assert.ok(D.siegeState(pl).practicable, "the wall comes down") }
  }
  assert.ok(short > 10 && down > 10, `both happen at ${M.success}% (${short} short, ${down} down)`);
  D.S.sieges[D.S.mapId][pl.name] = { days: 0 }; D.save();
  assert.match(D.countermine(pl.name), /countermines/);
  D.restore();
  assert.ok(D.siegeState(pl).countermine, "the garrison countermines");
  let found = 0;
  for (let n = 0; n < 200; n++){
    D.S.sieges[D.S.mapId][pl.name].days = 0.5;
    for (const f of D.forcesHere()){ f.marched = 0; f.day = 1 }
    const out = D.siegeNight({ day: 1, used: 0 }).join(" ");
    if (/countermine breaks into the gallery/.test(out)) found++;
  }
  assert.ok(found > 10 && found < 60, `found about ${M.countermine}% of the days (${found} of 200)`);
});
check("sieges: a storm won takes the place; refused terms after the breach, the stormers sack it for days where the era allows", () => {
  const { D } = fresh(15);
  D.S.mapId = "badajoz-1812";
  const pl = D.fortresses()[0], F = pl.fortress, fs = D.forcesHere();
  const g = fs.find(f => f.side === F.side && D.sameHex(f.pos, pl.hex)), siege = fs.filter(f => f.side !== F.side && D.siegeState(pl).by.includes(f.name));
  assert.ok(siege.length, "the siege corps invests Badajoz");
  D.S.sieges[D.S.mapId] = { [pl.name]: { days: F.breach_days, terms: "refused after the breach" } };
  D.save();
  const msg = D.stormWon(pl.name);
  D.restore();
  assert.match(msg, /stormed and taken/); assert.match(msg, /sacked/);
  assert.equal(D.siegeState(pl).side, siege[0].side, "the place passes to the stormers");
  assert.equal(D.forcesHere().find(f => f.id === g.id).pos, null, "the garrison is taken");
  const s1 = D.forcesHere().find(f => f.id === siege[0].id);
  assert.ok(D.sacking(s1), "the stormers are sacking");
  assert.ok(D.conditionsOf(s1).includes("sacking"), "desertion and straggling doubled");
  for (let n = 0; n < DATA.terrain.siege.sack_days; n++){ const c = D.clockNow(); D.siegeNight(c); c.day += 1 }
  assert.ok(!D.sacking(s1), `over after ${DATA.terrain.siege.sack_days} days`);
});
check("sieges: no sack where the era forbids it, nor when the GM spares the place", () => {
  const { D } = fresh(16);
  D.S.mapId = "badajoz-1812";
  const pl = D.fortresses()[0], F = pl.fortress;
  D.S.sieges[D.S.mapId] = { [pl.name]: { days: F.breach_days, terms: "refused after the breach" } };
  D.save();
  assert.doesNotMatch(D.stormWon(pl.name, false), /sacked/, "spared by the GM");
  D.restore();
  assert.ok(!DATA.sack_eras.includes("wwii") && DATA.sack_eras.includes("horse_musket"), "the eras that allow a sack");
});
check("fog of war: a player's view holds his side's forces and only the enemy it sees, or saw", () => {
  const { D } = fresh(5);
  D.S.mapId = "towton-1461";
  const fs = D.forcesHere(), a = fs[0], e = fs.find(o => o.side !== a.side), m = D.curMap();
  for (const f of fs.filter(o => o.side !== a.side && o !== e)) f.pos = null;
  const open = []; for (let r = 0; r < m.rows.length; r++) for (let c = 0; c < m.rows[0].length; c++) if (CLEAR.has(RULES.terrainAt(m, [c, r]).id)) open.push([c, r]);
  a.pos = open[0]; a.type = "foot";
  e.pos = open.find(h => RULES.hexDistance(h, a.pos) === 1);   // 1 km: within its outposts' reach
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
