// node targets.js <field id> <seed> [page]: one self-played run, as play.js writes it (report.py reads it),
// with what it shows against the morale targets (docs/morale-redesign.md): each unit's share of men down
// when it broke and why it checked, and each side's men down in all and after breaking (in the rout).
"use strict";
const { load } = require("./page.js");

const [fid, seed, htmlPath] = process.argv.slice(2);
const breaks = [], down = {}, routDown = {}, why = {};
function noteLine(B, l){                           // one log line: men down by side (and in the rout), a unit's break and why it checked
  const j = l.dfd ?? l.unit, u = B.units[j];
  if (!u) return;
  const d = typeof l.down === "number" ? l.down : 0;
  if (d && l.dfd !== undefined){
    down[u.side] = (down[u.side] || 0) + d;
    if (l.kind === "rout") routDown[u.side] = (routDown[u.side] || 0) + d;
  }
  if (l.kind !== "morale") return;
  if (l.state === "broken" && l.from !== "broken") breaks.push({ side: u.side, unit: u.name, start: u.start, down: u.down || 0, share: Math.round(1000 * (u.down || 0) / Math.max(1, u.start)) / 10, at: B.exchange, why: l.why || null });
  for (const w of l.why || []) why[w] = (why[w] || 0) + 1;
}
function noteRan(B, x){                           // a cornered unit that surrendered at the start of the exchange: its men lost after breaking (taken and killed)
  if (!x.surrendered) return;
  const u = B.units[x.unit], n = x.taken + x.killed;
  down[u.side] = (down[u.side] || 0) + n;
  routDown[u.side] = (routDown[u.side] || 0) + n;
}
const hook = (B, r) => {
  for (const l of r.log || []) noteLine(B, l);
  for (const x of r.ran || []) noteRan(B, x);
};
const { FD, api } = load(htmlPath, ["secured"], hook);
const t0 = Date.now(), r = api.selfPlay(fid, new api.SeededDice(Number(seed) * 101)), F = FD.fields[fid];
const B = r.battle, end = r.points.at(-1).points[0];
const run = { seed: Number(seed) * 101, ms: Date.now() - t0, stop: r.stop, exchanges: B.exchange - 1, orders: r.orders, sides: end.sides, held: end.held, secured: F.objective && end.held[0] ? api.secured(B, end.held[0]) : null,
  units: B.units.map(u => ({ name: u.name, side: u.side, start: u.start, men: u.men, state: u.state, dead: u.dead || 0, down: u.down || 0, pos: u.pos })),
  targets: { start: Object.fromEntries(F.sides.map(s => [s, B.units.filter(u => u.side === s).reduce((a, u) => a + u.start, 0)])), down, routDown, breaks, why } };
console.log(JSON.stringify({ fid, name: F.name, sides: F.sides, stances: api.playStances(fid), objective: F.objective || null, phases: (F.phases || []).length, runs: [run] }));
