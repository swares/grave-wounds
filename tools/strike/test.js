// The strike's rules (templates/strike.js) and the event log (templates/gamelog.js), run with no page.
//   node tools/strike/test.js                (the unit tests, on dist/gravewounds-data.json)
//   python3 tools/strike/parity.py [n] [seed] (writes .cache/ and runs this with STRIKE_PARITY=1)
// With STRIKE_PARITY=1 it reads parity.py's bundle and cases from .cache/: strikes played through
// gravewounds.engine.roll_hit, each played here on the same dice, which must give the same wound.
// Then the unit tests: the attack phase, the player's own dice, determinism with seeded dice, and
// who sees what in the log.
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");

const ROOT = path.resolve(__dirname, "..", "..");
const { makeStrike } = require("../../templates/strike.js");
const G = require("../../templates/gamelog.js");

// The files are fixed: parity.py's bundle and cases when it has written them, else the built bundle (no cases).
const CACHE = path.join(__dirname, ".cache");
const readJson = p => JSON.parse(fs.readFileSync(p, "utf8"));
const parityRun = fs.existsSync(path.join(CACHE, "cases.json")) && process.env.STRIKE_PARITY === "1";
const DATA = readJson(parityRun ? path.join(CACHE, "data.json") : path.join(ROOT, "dist", "gravewounds-data.json"));
const S = makeStrike(DATA);

let failed = 0, passed = 0;
function check(name, fn){
  try { fn(); passed++ } catch (e){ failed++; console.error(`FAIL ${name}\n  ${e.message.split("\n").slice(0, 8).join("\n  ")}`) }
}
const scripted = numbers => {                      // dice that give these numbers in order, and fail if asked for more
  const left = numbers.slice();
  return { randint(a, b){ assert.ok(left.length, `dice asked for more than the ${numbers.length} given`); const v = left.shift(); assert.ok(v >= a && v <= b, `${v} outside ${a}-${b}`); return v }, left };
};
const seeded = seed => {                            // Park-Miller, as units.js SeededDice
  let st = Math.max(1, seed % 2147483647);
  return { randint(a, b){ st = (st * 16807) % 2147483647; return a + (st % (b - a + 1)) } };
};
const ctxOf = c => ({ table: c.table, ltable: c.ltable, weapon: c.weapon, mods: [], ranges: c.ranges, aimRanges: c.aimRanges,
  armor: c.kit, evidence: c.evidence, rc: { range: null }, freeHit: false, attacker: null, defender: null });

/* ----- the wound, against Python's roll_hit ----- */
if (parityRun){
  const cases = readJson(path.join(CACHE, "cases.json"));
  let same = 0;
  cases.forEach((c, i) => check(`parity case ${i} (${c.table}, ${c.weapon}, ${c.kit})`, () => {
    const dice = scripted(c.dice);
    const cmd = { atk: c.atk, def: null, aim: c.aim, gap: c.gap, blow: c.blow, sev: c.sev, rolls: c.atkRoll ? { atk: c.atkRoll } : {} };
    const { hit: h } = S.resolveStrike(ctxOf(c), cmd, dice);
    assert.equal(dice.left.length, 0, "the JavaScript took fewer dice than Python");
    const p = c.py;
    assert.deepEqual([h.loc, h.mech, h.sev, h.graze], [p.loc, p.mech, p.sev, p.graze], "location, blow, severity, graze");
    assert.deepEqual([h.rolls.loc, h.rolls.mech, h.rolls.sev], [p.rolls.location, p.rolls.mechanism, p.rolls.severity], "rolls");
    assert.deepEqual([h.aim.zonePaid, h.aim.gapPaid, h.aim.left], [p.aim.zone_paid, p.aim.gap_paid, p.aim.left], "aim paid");
    assert.deepEqual(h.fx, p.fx, "wound effects");
    if (p.armor){
      const a = h.armor;
      assert.ok(a, "armour on the JavaScript side");
      assert.deepEqual([a.mat, a.rc, a.covered, a.gapped, a.steps, a.from, a.to],
        [p.armor.material, p.armor.cover_roll, p.armor.covered, p.armor.gap_aimed, p.armor.steps, p.armor.from, p.armor.to], "armour");
    } else assert.equal(h.armor, null, "no armour");
    same++;
  }));
  console.log(`parity: ${same} strikes give the same wound as gravewounds.engine.roll_hit`);
}

/* ----- the attack phase ----- */
const tid = Object.keys(DATA.tables).find(t => DATA.tables[t].weapons.includes("sword") && DATA.tables[t].resolve.sword === undefined) || Object.keys(DATA.tables)[0];
const base = { table: tid, ltable: tid, weapon: "sword", mods: [], ranges: [{ id: DATA.locations[0].id, pct: 100, lo: 1, hi: 100 }], aimRanges: null,
  armor: "none", evidence: true, rc: { range: null }, freeHit: false, attacker: null, defender: null };

check("a miss ends the strike, with no wound dice", () => {
  const d = scripted([]);
  const r = S.resolveStrike(base, { atk: 40, def: null, rolls: { atk: 90 } }, d);
  assert.equal(r.hit.miss, true);
  assert.equal(r.hit.fx, null);
  assert.deepEqual(r.dice, [{ name: "atk", v: 90, sides: 100, by: "player" }]);
  assert.equal(r.effects.closeIn, true);
  assert.equal(r.effects.xp, null);
});
check("a parry ends the strike and marks the defender's skill", () => {
  const r = S.resolveStrike(base, { atk: 60, def: 50, rolls: { atk: 45, def: 10 } }, scripted([]));
  assert.equal(r.hit.defended, true);
  assert.equal(r.effects.xp, "defended");
  assert.equal(r.hit.combat.def.defended, true);
});
check("a critical cannot be parried", () => {
  const crit = Math.floor(60 * DATA.combat.critical_fraction);
  const r = S.resolveStrike(base, { atk: 60, def: 99, rolls: { atk: crit, def: 1 } }, scripted([5, 5]));
  assert.equal(r.hit.combat.def, null);
  assert.equal(r.hit.sev !== undefined && !r.hit.defended, true);
  assert.equal(r.hit.combat.atk.critical, true);
});
check("the attacker's penalties and the range lower the attack", () => {
  const ctx = { ...base, rc: { range: { penalty: 10 } }, attacker: { name: "Will", pen: { attack: 15, defence: 0, flags: [] }, state: null } };
  const r = S.resolveStrike(ctx, { atk: 50, rolls: { atk: 30 } }, scripted([1, 1]));
  assert.equal(r.hit.combat.atk.effective, 25);
  assert.equal(r.hit.miss, true);
});
check("an incapacitated attacker is blocked before any die", () => {
  const ctx = { ...base, attacker: { name: "Will", pen: { attack: 0, defence: 0, flags: ["incapacitated"] }, state: null } };
  const r = S.resolveStrike(ctx, { atk: 50, rolls: {} }, scripted([]));
  assert.match(r.hit.blocked, /Will is incapacitated/);
  assert.equal(r.dice.length, 0);
  assert.equal(r.effects.closeIn, false);
});
check("the range check blocks before anything", () => {
  const r = S.resolveStrike({ ...base, rc: { blocked: "out of reach" } }, { atk: 50 }, scripted([]));
  assert.equal(r.hit.blocked, "out of reach");
});
check("wet priming: a misfire loses the shot and closes a free attack", () => {
  const r = S.resolveStrike({ ...base, freeHit: true, rc: { range: { misfire: 30, penalty: 0 } } }, { atk: 50, rolls: {} }, scripted([12]));
  assert.match(r.hit.blocked, /^Misfire: d100 12 against 30%/);
  assert.equal(r.effects.free, "misfire");
});
check("a miss with a man in the way rolls the stray shot", () => {
  const rc = { range: { penalty: 0, stray: 25, way: [7] } };
  const r = S.resolveStrike({ ...base, rc }, { atk: 30, rolls: { atk: 80 } }, scripted([20]));
  assert.deepEqual(r.hit.stray, { id: 7, roll: 20, chance: 25, hit: true });
});
check("the player's own dice are used and marked; the rest are rolled", () => {
  const r = S.resolveStrike(base, { atk: 70, rolls: { atk: 33, loc: 50 } }, scripted([40]));
  const by = Object.fromEntries(r.dice.map(x => [x.name, x.by]));
  assert.equal(by.atk, "player");
  assert.equal(by.loc, "player");
  assert.equal(by.mech, "dice");
});
check("a die out of range is not taken as the player's", () => {
  const r = S.resolveStrike(base, { atk: null, sev: "light", rolls: { loc: 0, mech: 101 } }, scripted([5, 6]));
  assert.ok(r.dice.every(x => x.by === "dice"));
});
check("the same seed gives the same strike", () => {
  const cmd = { atk: 55, def: 30, aim: "", gap: false, sev: "roll", rolls: {} };
  const a = S.resolveStrike(base, cmd, seeded(42)), b = S.resolveStrike(base, cmd, seeded(42));
  assert.deepEqual(a, b);
});
check("the strike changes neither its situation nor its command", () => {
  const ctx = structuredClone(base), cmd = { atk: 55, def: 30, rolls: { atk: 20 } };
  const before = JSON.stringify([ctx, cmd]);
  S.resolveStrike(ctx, cmd, seeded(3));
  assert.equal(JSON.stringify([ctx, cmd]), before);
});

/* ----- the event log ----- */
check("events are numbered in order and kept to LOG_KEEP", () => {
  const log = [];
  for (let i = 0; i < G.LOG_KEEP + 5; i++) G.logEvent(log, { type: "strike", data: { i } });
  assert.equal(log.length, G.LOG_KEEP);
  assert.equal(log[0].n, 6);
  assert.equal(log.at(-1).n, G.LOG_KEEP + 5);
});
check("the GM sees everything; a side sees its own in full and the rest's public part", () => {
  const log = [], y = G.sideSeat("Yorkists"), l = G.sideSeat("Lancastrians");
  G.logEvent(log, { type: "strike", vis: [l], data: { sev: "critical" }, pub: { outcome: "hit" } });
  G.logEvent(log, { type: "wound", vis: [y], data: { sev: "light" }, pub: null });
  G.logEvent(log, { type: "note", vis: "public", data: { text: "rain" } });
  assert.equal(G.viewFor(log, G.GM_SEAT).length, 3);
  assert.ok(G.viewFor(log, G.GM_SEAT).every(v => v.full));
  const ly = G.viewFor(log, y);
  assert.deepEqual(ly.map(v => [v.n, v.full, v.data]), [[1, false, { outcome: "hit" }], [2, true, { sev: "light" }], [3, true, { text: "rain" }]]);
  const ll = G.viewFor(log, l);
  assert.deepEqual(ll.map(v => v.n), [1, 3]);       // the Yorkist wound has no public part: the Lancastrians see nothing of it
  assert.ok(!JSON.stringify(ll).includes("light"));
});
check("seats: the GM first, then each side once", () => {
  assert.deepEqual(G.seatsIn(["A", "B", "A"]), ["gm", "side:A", "side:B"]);
});

check("an arrow beats bare mail and cloth, not plate, a coat of plates or mail over padding", () => {
  for (const w of ["longbow", "crossbow"]){
    assert.equal(S.armorSteps("mail", "pierce", w), 0); assert.equal(S.armorSteps("jack", "pierce", w), 0);
    assert.equal(S.armorSteps("plate", "pierce", w), 2); assert.equal(S.armorSteps("plates", "pierce", w), 2); assert.equal(S.armorSteps("mail_padded", "pierce", w), 1);
  }
  assert.equal(S.armorSteps("plate", "pierce", "halberd"), 1);   // a halberd's spike still beats plate a step
  assert.equal(S.armorSteps("plate", "pierce", "bill"), 1);      // and the bill's top spike, as the halberd's
  assert.equal(S.armorSteps("plate", "cut", "bill"), 3);        // its blade does not
});

/* ----- quick-play strikes: one d1000 on the strike's exact chart ----- */
const quickBase = (() => {                          // a sword on a man in a padded jack, his whole body's spread of places, with a parry
  const ids = DATA.locations.map(l => l.id), per = Math.floor(100 / ids.length);
  const ranges = ids.map((id, i) => ({ id, pct: per, lo: i * per + 1, hi: i === ids.length - 1 ? 100 : (i + 1) * per }));
  const kit = (DATA.armor.kits.find(k => k.id === "gambeson") || DATA.armor.kits[0]).id;
  return { ...base, ranges, armor: kit, evidence: false };
})();
const quickKey = h => (h.blocked ? "blocked" : h.miss ? "miss" : h.defended ? "defended" : JSON.stringify([h.loc, h.mech, h.sev, !!h.graze]));
check("quick-play: the chart's chances add up to 1, and each line's dice give that line", () => {
  const cmd = { atk: 55, def: 30, aim: "", gap: false, blow: "", sev: "roll", rolls: {} };
  const chart = S.quickChart(quickBase, cmd);
  assert.ok(Math.abs(chart.reduce((t, l) => t + l.p, 0) - 1) < 1e-9, "the chances add up to 1");
  assert.ok(chart.length > 20, `${chart.length} lines`);
  for (const l of chart){
    const r = S.resolveStrike(quickBase, { ...cmd, rolls: l.rolls }, scripted([]));
    assert.equal(JSON.stringify([r.hit.blocked ? "blocked" : r.hit.miss ? `miss|${r.hit.stray ? r.hit.stray.hit : ""}` : r.hit.defended ? "defended"
      : JSON.stringify([r.hit.loc, r.hit.mech, r.hit.sev, !!r.hit.graze, r.hit.armor ? r.hit.armor.mat : null, r.hit.armor ? r.hit.armor.covered : null])]), JSON.stringify([l.key]));
  }
});
check("quick-play: the chart matches 40,000 strikes rolled die by die", () => {
  const cmd = { atk: 55, def: 30, aim: "", gap: false, blow: "", sev: "roll", rolls: {} };
  const chart = S.quickChart(quickBase, cmd), n = 40000, got = {}, dice = seeded(4242);
  for (let i = 0; i < n; i++){ const k = quickKey(S.resolveStrike(quickBase, cmd, dice).hit); got[k] = (got[k] || 0) + 1 }
  const want = {};
  for (const l of chart){ const h = S.resolveStrike(quickBase, { ...cmd, rolls: l.rolls }, scripted([])).hit; const k = quickKey(h); want[k] = (want[k] || 0) + l.p }
  for (const k of ["miss", "defended"]) assert.ok(Math.abs(want[k] - got[k] / n) < 4 * Math.sqrt(want[k] * (1 - want[k]) / n), `${k}: chart ${want[k].toFixed(4)}, rolled ${(got[k] / n).toFixed(4)}`);
  for (const sev of ["stopped", "light", "serious", "critical"]){
    const w = Object.entries(want).filter(([k]) => k.includes(`"${sev}"`)).reduce((t, [, p]) => t + p, 0);
    const g = Object.entries(got).filter(([k]) => k.includes(`"${sev}"`)).reduce((t, [, c]) => t + c, 0) / n;
    assert.ok(Math.abs(w - g) < 4 * Math.sqrt(Math.max(w, 1e-4) * (1 - w) / n), `${sev}: chart ${w.toFixed(4)}, rolled ${g.toFixed(4)}`);
  }
});
check("quick-play: one d1000, then the strike on the line's dice", () => {
  const cmd = { atk: 55, def: 30, aim: "", gap: false, blow: "", sev: "roll", rolls: {} };
  const r = S.quickStrike(quickBase, cmd, scripted([1000]));
  assert.deepEqual(r.dice, [{ name: "quick", v: 1000, sides: 1000, by: "dice" }]);
  assert.equal(r.hit.quick.roll, 1000);
  const chart = S.quickChart(quickBase, cmd);
  let sum = 0, line = chart[chart.length - 1];
  for (const l of chart){ sum += l.p; if (0.9995 < sum){ line = l; break } }
  assert.equal(quickKey(r.hit), quickKey(S.resolveStrike(quickBase, { ...cmd, rolls: line.rolls }, scripted([])).hit));
});
check("quick-play: each kind of wound comes out on the d1000 within 1 in 1,000 of its chance", () => {
  const cmd = { atk: 55, def: 30, aim: "", gap: false, blow: "", sev: "roll", rolls: {} };
  const chart = S.quickChart(quickBase, cmd), LOCS = Object.fromEntries(DATA.locations.map(l => [l.id, l]));
  const kind = l => (l.key.startsWith("[") ? (([loc, mech, sev, g]) => [LOCS[loc].class, mech, sev, g].join("|"))(JSON.parse(l.key)) : l.key);
  const want = {}, got = {};
  for (const l of chart) want[kind(l)] = (want[kind(l)] || 0) + l.p;
  const chartKey = h => (h.blocked ? "blocked" : h.miss ? `miss|${h.stray ? h.stray.hit : ""}` : h.defended ? "defended" : [LOCS[h.loc].class, h.mech, h.sev, !!h.graze].join("|"));
  for (let v = 1; v <= 1000; v++){ const k = chartKey(S.quickStrike(quickBase, cmd, scripted([v]), chart).hit); got[k] = (got[k] || 0) + 0.001 }
  for (const k of Object.keys(want)) assert.ok(Math.abs(want[k] - (got[k] || 0)) <= 0.001 + 1e-9, `${k}: chance ${want[k].toFixed(4)}, on the d1000 ${(got[k] || 0).toFixed(3)}`);
});
check("quick-play: a strike with one outcome takes no die", () => {
  const ctx = { ...base, attacker: { name: "Will", pen: { attack: 0, defence: 0, flags: ["incapacitated"] }, state: null } };
  const r = S.quickStrike(ctx, { atk: 50, rolls: {} }, scripted([]));
  assert.match(r.hit.blocked, /incapacitated/);
  assert.deepEqual(r.dice, []);
});
console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
