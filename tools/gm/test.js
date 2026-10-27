// The scripted fighter (templates/fighter.js), run with no page: a small hex board stands in for the
// roller's map (same odd-row offset hexes), and each test checks one choice the brain makes.
//   node tools/gm/test.js
"use strict";
const assert = require("node:assert/strict");
const F = require("../../templates/fighter.js");

let failed = 0, passed = 0;
function check(name, fn){
  try { fn(); passed++ } catch (e){ failed++; console.error(`FAIL ${name}\n  ${e.message.split("\n").slice(0, 6).join("\n  ")}`) }
}

/* ----- a board like the roller's: hexes "col,row", odd rows shifted ----- */
const cube = ([c, r]) => { const q = c - (r - (r & 1)) / 2; return [q, r, -q - r] };
const P = k => k.split(",").map(Number);
const dist = (a, b) => { const x = cube(P(a)), y = cube(P(b)); return Math.max(Math.abs(x[0] - y[0]), Math.abs(x[1] - y[1]), Math.abs(x[2] - y[2])) };
function board(o){                                  // a view for the brain: me at `here`, enemies, how far he can go
  const { here, enemies, advance = 3, run = 6, reach = 1, range = 0, cover = {}, me = {} } = o;
  const hexes = [];
  for (let c = 0; c < 16; c++) for (let r = 0; r < 12; r++){
    const k = `${c},${r}`, d = dist(here, k);
    if (d === 0 || d > run || enemies.some(e => e.hex === k)) continue;
    hexes.push({ hex: k, cost: d, run: d > advance });
  }
  const strikeRange = range || reach;
  return {
    me: { id: 1, ranged: range > 0, frac: 1, named: false, blows: [], attack: 60, able: true, ...me },
    here, reach: hexes, enemies, stance: o.stance || "steady", losing: !!o.losing,
    targetsFrom: h => enemies.map(e => ({ id: e.id, dist: dist(h, e.hex), penalty: range && dist(h, e.hex) > range / 2 ? 20 : 0 }))
      .filter(t => t.dist <= strikeRange),
    dist, coverAt: h => cover[h] || 0,
  };
}
const foe = (id, hex, more = {}) => ({ id, hex, frac: 1, armoured: false, plated: false, ...more });

check("a man in reach strikes where he stands", () => {
  const t = F.chooseTurn(board({ here: "5,5", enemies: [foe(2, "6,5")] }));
  assert.equal(t.move, null);
  assert.equal(t.target, 2);
});
check("a man who can get there advances and strikes", () => {
  const t = F.chooseTurn(board({ here: "2,5", enemies: [foe(2, "5,5")] }));
  assert.ok(t.move, "he moves");
  assert.equal(dist(t.move, "5,5"), 1);
  assert.equal(t.target, 2);
  assert.ok(dist("2,5", t.move) <= 3, "advancing, not running, so he can still strike");
});
check("too far to strike: he closes as near as he can and does not strike", () => {
  const t = F.chooseTurn(board({ here: "0,0", enemies: [foe(2, "12,9")] }));
  assert.equal(t.target, null);
  assert.ok(dist(t.move, "12,9") < dist("0,0", "12,9"));
});
check("a cautious man does not run to close", () => {
  const v = board({ here: "0,0", enemies: [foe(2, "12,9")], stance: "cautious" });
  const t = F.chooseTurn(v);
  assert.ok(dist("0,0", t.move) <= 3);
});
check("the most hurt enemy in reach is struck first", () => {
  const t = F.chooseTurn(board({ here: "5,5", enemies: [foe(2, "6,5"), foe(3, "4,5", { frac: 0.3 })] }));
  assert.equal(t.target, 3);
});
check("badly hurt, a steady man falls back; a reckless one fights on", () => {
  const o = { here: "5,5", enemies: [foe(2, "6,5")], me: { frac: 0.2 } };
  const s = F.chooseTurn(board({ ...o, stance: "steady" }));
  assert.ok(s.move && dist(s.move, "6,5") > 1, "falls back");
  const r = F.chooseTurn(board({ ...o, stance: "reckless" }));
  assert.equal(r.move, null);
  assert.equal(r.target, 2);
});
check("on a side near breaking, a cautious man falls back even unhurt", () => {
  const t = F.chooseTurn(board({ here: "5,5", enemies: [foe(2, "6,5")], stance: "cautious", losing: true }));
  assert.ok(t.move && dist(t.move, "6,5") > 1);
});
check("he aims for a gap only in part-covered armour and with attack to spare", () => {
  const armoured = [foe(2, "6,5", { armoured: true })];
  assert.equal(F.chooseTurn(board({ here: "5,5", enemies: armoured, me: { attack: 75 } })).gap, true);
  assert.equal(F.chooseTurn(board({ here: "5,5", enemies: armoured, me: { attack: 45 } })).gap, false);
  assert.equal(F.chooseTurn(board({ here: "5,5", enemies: [foe(2, "6,5")], me: { attack: 90 } })).gap, false);
});
check("a named man declares thrust at plate and cut at the unarmoured; others declare nothing", () => {
  const named = { named: true, blows: ["cut", "thrust"] };
  assert.equal(F.chooseTurn(board({ here: "5,5", enemies: [foe(2, "6,5", { plated: true })], me: named })).blow, "thrust");
  assert.equal(F.chooseTurn(board({ here: "5,5", enemies: [foe(2, "6,5")], me: named })).blow, "cut");
  assert.equal(F.chooseTurn(board({ here: "5,5", enemies: [foe(2, "6,5")], me: { blows: ["cut", "thrust"] } })).blow, "");
});
check("a shooter shoots from where he is, and does not walk into the enemy's arms", () => {
  const t = F.chooseTurn(board({ here: "2,5", enemies: [foe(2, "8,5")], range: 12 }));
  assert.equal(t.move, null);
  assert.equal(t.target, 2);
  const far = F.chooseTurn(board({ here: "0,0", enemies: [foe(2, "15,11")], range: 4, advance: 6, run: 10 }));
  assert.ok(dist(far.move, "15,11") >= 2);
});
check("a badly hurt shooter with nowhere to go takes cover", () => {
  const v = board({ here: "5,5", enemies: [foe(2, "8,5")], range: 12, me: { frac: 0.2 } });
  v.reach = [];
  const t = F.chooseTurn(v);
  assert.equal(t.cover, true);
  assert.equal(t.target, null);
});
check("a man who cannot attack moves but does not strike", () => {
  const t = F.chooseTurn(board({ here: "5,5", enemies: [foe(2, "6,5")], me: { able: false } }));
  assert.equal(t.target, null);
});
check("no enemy left: he does nothing", () => {
  const t = F.chooseTurn(board({ here: "5,5", enemies: [] }));
  assert.deepEqual([t.move, t.target, t.cover], [null, null, false]);
});
check("the same view gives the same choice", () => {
  const v = board({ here: "0,0", enemies: [foe(2, "9,7"), foe(3, "9,9")] });
  assert.deepEqual(F.chooseTurn(v), F.chooseTurn(v));
});

/* ----- first aid (out of an enemy's reach) ----- */
const pal = (id, hex, more = {}) => ({ id, hex, down: false, bleed: 0, ...more });
check("a man bleeding badly and out of reach binds his own wound", () => {
  const t = F.chooseTurn({ ...board({ here: "2,2", enemies: [foe(2, "9,9")], me: { bleed: 0.08 } }), friends: [] });
  assert.equal(t.aid, 1); assert.equal(t.target, null); assert.equal(t.move, null);
});
check("next to an enemy he fights on rather than bind himself", () => {
  const t = F.chooseTurn({ ...board({ here: "5,5", enemies: [foe(2, "6,5")], me: { bleed: 0.08 } }), friends: [] });
  assert.equal(t.aid, undefined); assert.equal(t.target, 2);
});
check("a cautious man goes to the worst-bleeding comrade", () => {
  const v = { ...board({ here: "2,2", enemies: [foe(2, "12,10")], stance: "cautious" }), friends: [pal(3, "4,2", { bleed: 0.02 }), pal(4, "2,4", { bleed: 0.06 })] };
  const t = F.chooseTurn(v);
  assert.equal(t.aid, 4); assert.equal(dist(t.move, "2,4"), 1); assert.equal(t.target, null);
});
check("a steady man treats only a comrade who is down", () => {
  const up = { ...board({ here: "2,2", enemies: [foe(2, "12,10")] }), friends: [pal(3, "3,2", { bleed: 0.06 })] };
  assert.equal(F.chooseTurn(up).aid, undefined);
  const down = { ...board({ here: "2,2", enemies: [foe(2, "12,10")] }), friends: [pal(3, "3,2", { bleed: 0.06, down: true })] };
  assert.equal(F.chooseTurn(down).aid, 3);
});
check("a reckless man leaves the wounded to the others", () => {
  const v = { ...board({ here: "2,2", enemies: [foe(2, "12,10")], stance: "reckless" }), friends: [pal(3, "3,2", { bleed: 0.06, down: true })] };
  assert.equal(F.chooseTurn(v).aid, undefined);
});
check("no one gives first aid within an enemy's reach", () => {
  const v = { ...board({ here: "5,5", enemies: [foe(2, "6,5")], stance: "cautious" }), friends: [pal(3, "4,5", { bleed: 0.06, down: true })] };
  assert.equal(F.chooseTurn(v).aid, undefined);
});

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
