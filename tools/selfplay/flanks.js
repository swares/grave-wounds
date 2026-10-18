// node flanks.js <field id> <seed> [page]: one self-played run, measured for flanking (docs/selfplay-review.md, Flanking):
// after each exchange, for each side, its spare units (steady, on foot or horse, not guns or vehicles, not in contact
// with an enemy) and whether each could reach an open hex on the flank or rear of an enemy unit that is fighting one
// of its own, within one move or three, and strike from it with a facing it can turn to on a charge; and the flank and rear strikes each side made, and how many came from a
// unit that had such a chance in the exchanges before; and the share of each side's volleys fired from off the target's front.
"use strict";
const { load } = require("./page.js");

const [fid, seed, htmlPath] = process.argv.slice(2);
const WINDOW = 5;                                    // exchanges after a chance in which a flank strike counts as taking it
const S = {};                                        // by side: the tallies
let api = null;
function noteVolley(us, l){                          // a volley, and whether it came from off its target's front (the rules give fire from a flank no edge, but for vehicles)
  const a = us[l.att], b = us[l.dfd];
  if (!a || !b || !l.from || !l.to) return;
  const T = side(a.side), off = (l.from[0] !== l.to[0] || l.from[1] !== l.to[1]) && api.arc(b.facing, api.bearing(l.to, l.from)) !== "front";
  T.volleys++;
  if (off) T.volleyFlank++;
}
const side = s => (S[s] ||= { exchanges: 0, engaged: 0, spare: 0, reserve: 0, chance1: 0, chance3: 0, exWith3: 0, strikes: 0, front: 0, taken: 0, rout: 0, onRoute: 0, volleys: 0, volleyFlank: 0 });
const lastChance = {};                               // unit id -> last exchange it had a chance (3 moves)

function flankHexes(units, occ, j, out){             // open hexes beside enemy unit j off its front, each with the facings a unit there strikes it from (into out: hk -> facings)
  const t = units[j];
  for (const x of api.footprint(t).flat()) for (let d = 0; d < 6; d++){
    if (api.arc(t.facing, d) === "front") continue;
    const h = api.step(x, d);
    if (occ[api.hk(h)] === undefined) out.set(api.hk(h), [...(out.get(api.hk(h)) || []), (d + 3) % 6, (d + 2) % 6]);
  }
  return out;
}
const standing = u => u.men > 0 && (u.state === "steady" || u.state === "shaken");
const fights = u => !u.vehicle && !api.isBattery(u) && !api.isAtGun(u);

function measure(B){                                 // the board after an exchange, as each commander sees it next
  const us = B.units, occ = api.occupancy(us);
  for (const s of B.sides){
    const T = side(s);
    T.exchanges++;
    const engaged = us.map((t, j) => j).filter(j => us[j].side !== s && standing(us[j]) && api.adjacentUnits(us, occ, j).some(k => us[k].side === s && standing(us[k])));
    if (!engaged.length) continue;
    T.engaged++;
    const open = new Map();
    for (const j of engaged) flankHexes(us, occ, j, open);
    let any = false;
    us.forEach((u, i) => {
      if (u.side !== s || u.state !== "steady" || !u.pos || !fights(u) || api.inContact(us, occ, i)) return;
      T.spare++;
      if (u.reserve) T.reserve++;
      if (u.via) T.onRoute++;
      const a = api.allowance(u);
      if (a <= 0) return;
      const r = api.reachable(us, i, B.size, 3 * a, B.field);
      const turnable = g => Math.min((g - u.facing + 12) % 6, (u.facing - g + 12) % 6) * api.turnCost(u) <= a * api.CHARGE;   // a facing it can still take on a charge
      let best = Infinity;
      for (const [k, [, c]] of r) if ((open.get(k) || []).some(turnable)) best = Math.min(best, c);
      if (best <= a) T.chance1++;
      if (best <= 3 * a){ T.chance3++; any = true; lastChance[u.id] = B.exchange }
    });
    if (any) T.exWith3++;
  }
}
function noteStrikes(B, log, before){                // flank and rear strikes in this exchange's log
  for (const l of log || []){
    if (l.kind === "volley"){ noteVolley(before, l); continue }
    if (l.kind !== "melee" && l.kind !== "rout") continue;
    const a = before[l.att];
    if (!a) continue;
    const T = side(a.side);
    if (l.kind === "rout"){ T.rout++; continue }
    if (l.situation !== "flank" && l.situation !== "rear"){ T.front++; continue }
    T.strikes++;
    const c = lastChance[a.id];
    if (c !== undefined && B.exchange - 1 - c <= WINDOW) T.taken++;
  }
}
const hook = (B, r) => {                             // after each side's move; after side 1's the exchange has been fought (its units keep their places in the list)
  if (B.phase !== 0) return;
  noteStrikes(B, r.log, B.units);
  measure(B);
};
const loaded = load(htmlPath, ["reachable", "footprint", "occupancy", "adjacentUnits", "inContact", "step", "arc", "bearing", "hk", "allowance", "turnCost", "UD", "isBattery", "isAtGun"], hook);
api = loaded.api;
api.CHARGE = api.UD.charge_move;
const r = api.selfPlay(fid, new api.SeededDice(Number(seed) * 101));
const F = loaded.FD.fields[fid], B = r.battle;
const winner = r.stop?.why === "held" ? r.stop.side : null;
console.log(JSON.stringify({ fid, name: F.name, seed: Number(seed), stances: api.playStances(fid), sides: F.sides, exchanges: B.exchange - 1, stop: r.stop, winner, by: S }));
