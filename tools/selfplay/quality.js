// node quality.js <field id> <seed> [page]: how the commander used each side's units over one self-played run.
// A unit is engaged in an exchange when it fired, struck, or was struck hand to hand. For each side:
// idleMen: % of its men in units never engaged; peakEngaged: the most % engaged in one exchange;
// firstEngaged, lastFirst: the exchanges its first and last units first engaged (piecemeal when far apart);
// lostIdle: % of its losses (not in the rout) taken by units that could not hit back that exchange;
// broke: [unit, exchange, exchanges engaged]; idleWhy: each idle unit, whether it moved, was held in reserve
// (and to when), its state and how near the nearest enemy it ended.
"use strict";
const { load } = require("./page.js");

const [fid, seed, htmlPath] = process.argv.slice(2);
const T = [];
const cube = h => { const q = h[0] - (h[1] - (h[1] & 1)) / 2; return [q, h[1], -q - h[1]] };
const hd = (a, b) => { const x = cube(a), y = cube(b); return Math.max(Math.abs(x[0] - y[0]), Math.abs(x[1] - y[1]), Math.abs(x[2] - y[2])) };

function seenThisMove(r){                         // {engaged: Set of unit indices, lost: {index: men down, not in the rout}}
  const engaged = new Set(), lost = {};
  for (const l of r.log || []){
    if (l.att !== undefined && (l.down !== undefined || l.blows !== undefined)) engaged.add(l.att);
    if (l.kind === "melee" && l.dfd !== undefined) engaged.add(l.dfd);
    const d = l.down ?? 0, j = l.dfd ?? l.unit;
    if (typeof d === "number" && d && j !== undefined && l.kind !== "rout") lost[j] = (lost[j] || 0) + d;
  }
  return { engaged, lost };
}
function track(B, u, i, seen){
  const t = T[i] ||= { side: u.side, name: u.name, start: u.start, engaged: [], moved: 0, lostIdle: 0, lost: 0, broke: null, reserveAt: [] };
  const ex = B.exchange, on = seen.engaged.has(i);
  if (u.reserve) t.reserveAt.push(ex);
  if (on) t.engaged.push(ex);
  if (t.last && (t.last[0] !== u.pos[0] || t.last[1] !== u.pos[1])) t.moved++;
  t.last = [...u.pos];
  t.state = u.state;
  const foes = B.units.filter(e => e.side !== u.side && e.pos && e.men > 0 && e.state !== "fled");
  t.near = foes.length ? Math.min(...foes.map(e => hd(u.pos, e.pos))) : null;
  t.lost += seen.lost[i] || 0;
  if (!on && u.state !== "broken") t.lostIdle += seen.lost[i] || 0;
  if (u.state === "broken" && t.broke === null) t.broke = ex;
}
const hook = (B, r) => {
  const seen = seenThisMove(r);
  B.units.forEach((u, i) => { if (u.pos && u.state !== "fled") track(B, u, i, seen) });
};
function sideReport(s, stance){
  const us = T.filter(t => t && t.side === s), men = us.reduce((a, t) => a + t.start, 0) || 1;
  const firsts = us.filter(t => t.engaged.length).map(t => t.engaged[0]).sort((a, b) => a - b);
  const idle = us.filter(t => !t.engaged.length), perEx = {};
  for (const t of us) for (const e of t.engaged) perEx[e] = (perEx[e] || 0) + t.start;
  const lost = us.reduce((a, t) => a + t.lost, 0);
  return { side: s, stance, units: us.length,
    idleMen: Math.round(100 * idle.reduce((a, t) => a + t.start, 0) / men),
    peakEngaged: Math.round(100 * Math.max(0, ...Object.values(perEx)) / men),
    firstEngaged: firsts[0] ?? null, lastFirst: firsts.at(-1) ?? null,
    lostIdle: Math.round(100 * us.reduce((a, t) => a + t.lostIdle, 0) / Math.max(1, lost)),
    broke: us.filter(t => t.broke !== null).map(t => [t.name, t.broke, t.engaged.length]),
    idleWhy: idle.map(t => ({ name: t.name, men: t.start, moved: t.moved, reserve: t.reserveAt.length > 0, reserveTo: t.reserveAt.at(-1) ?? null, state: t.state, near: t.near })) };
}
const { FD, api } = load(htmlPath, [], hook);
const r = api.selfPlay(fid, new api.SeededDice(Number(seed) * 101));
const st = api.playStances(fid);
console.log(JSON.stringify({ fid, seed: Number(seed) * 101, stop: r.stop, exchanges: r.battle.exchange - 1,
  sides: FD.fields[fid].sides.map((s, k) => sideReport(s, st[k])) }));
