// node play.js <field id> <seeds> <out.json> [page] [first seed]: self-play a battlefield with the stances as fought
// (PLANNER=1 in the environment: the commander plans for itself on a side with no written plan),
// one run a seed (seed k is dice k x 101, k from first, default 1), and write what each run came to.
"use strict";
const fs = require("node:fs");
const { load } = require("./page.js");

const [fid, nSeeds, outFile, htmlPath, firstArg] = process.argv.slice(2);
const first = Number(firstArg || 1);
const { FD, api } = load(htmlPath, ["secured"]);
const F = FD.fields[fid], runs = [];
const securedAtEnd = (B, end) => (F.objective && end.held[0] ? api.secured(B, end.held[0]) : null);   // whoever holds the objective at the end has no enemy standing round it
for (let s = first; s < first + Number(nSeeds); s++){
  const t0 = Date.now(), r = api.selfPlay(fid, new api.SeededDice(s * 101), null, !!process.env.PLANNER);
  const B = r.battle, end = r.points.at(-1).points[0];
  const units = B.units.map(u => ({ name: u.name, side: u.side, start: u.start, men: u.men, state: u.state, dead: u.dead || 0, down: u.down || 0, pos: u.pos }));
  runs.push({ seed: s * 101, ms: Date.now() - t0, stop: r.stop, exchanges: B.exchange - 1, orders: r.orders, sides: end.sides, held: end.held, secured: securedAtEnd(B, end), units });
}
fs.writeFileSync(outFile, JSON.stringify({ fid, name: F.name, sides: F.sides, stances: api.playStances(fid), objective: F.objective || null, phases: (F.phases || []).length, runs }, null, 1));
console.log(fid, runs.map(r => `${r.stop.why}@${r.exchanges}`).join(" "), runs.reduce((a, r) => a + r.ms, 0) + "ms");
