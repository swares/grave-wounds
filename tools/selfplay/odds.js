// node odds.js [page] [seeds]: the procedural planner on open ground at set odds, away from the
// battlefields (docs/units.md, The procedural planner): does an attacker's own plan help it? A holding
// side of four regular companies against an attacking side of 1, 2, 3 or 4 times as many (as many units
// again in rows behind), medieval (bills and longbows, Towton's tables) and Second World War (riflemen
// and a machine gun, Owens), in fair weather on open ground. Each case is played with the attacker
// planning for itself and without; for each, the attacker's share of runs won: the holders gone, or at
// the run's end the holders having lost the larger share. One line a case, JSON.
"use strict";
const { load } = require("./page.js");
const [pageArg, seedsArg] = process.argv.slice(2);
const seeds = Number(seedsArg || 12);
const { FD, api } = load(pageArg || null, []);
const ERAS = {
  medieval: { table: "towton-1461-all-hits", kit: "jack_sallet", front: [["bill", "close", 5], ["longbow", "open", 10]] },
  ww2: { table: "owens-wwii", kit: "ww2_rifleman", front: [["rifle_service", "extended", 20], ["machine_gun", "mg", 2]] },
};
function field(era, odds){                          // a battlefield of open ground, 100 x 90 hexes, north at the top
  const E = ERAS[era], units = [], xs = [20, 38, 56, 74];
  const company = (side, n, k, y, facing) => {
    const [weapon, formation, width] = E.front[k % 4 === 3 ? 1 : 0];   // one in four a shooter (or machine gun)
    const men = weapon === "machine_gun" ? 10 : 200;
    units.push({ name: `${side ? "Attackers" : "Holders"} ${n}`, side, men, quality: "regular", weapon, kit: E.kit, formation, width, pos: [xs[k % 4], y], facing });
  };
  for (let k = 0; k < 4; k++) company(0, k + 1, k, 25, 4);
  for (let w = 0; w < odds; w++) for (let k = 0; k < 4; k++) company(1, w * 4 + k + 1, k, 52 + 7 * w, 1);
  return { name: `Open ground, ${era}, ${odds} to 1`, sides: ["Holders", "Attackers"], table: E.table, units, stances: ["hold", "attack"],
    field: { ground: {}, works: { edges: {}, hexes: {} }, weather: { cond: "fair", wind: "calm", ground: { mud: 0, snow: 0 } }, size: [100, 90] } };
}
function share(B, side){ const us = B.units.filter(u => u.side === side), a = us.reduce((x, u) => x + u.start, 0); return a ? us.reduce((x, u) => x + u.start - u.men, 0) / a : 0 }
for (const era of Object.keys(ERAS)) for (const odds of [1, 2, 3, 4]){
  const fid = `odds-${era}-${odds}`;
  FD.fields[fid] = field(era, odds);
  const out = { era, odds };
  for (const [label, planner] of [["no_plan", false], ["plan", 1]]){
    let won = 0;
    for (let s = 1; s <= seeds; s++){
      const r = api.selfPlay(fid, new api.SeededDice(s * 101), null, planner), B = r.battle;
      const gone = r.stop.why === "gone" && (r.stop.sides || []).includes(0);   // stop.sides: the indices of the sides gone
      if (gone || (r.stop.why !== "gone" && share(B, "Holders") > share(B, "Attackers"))) won++;
    }
    out[label] = Math.round(1000 * won / seeds) / 1000;
  }
  console.log(JSON.stringify(out));
}
