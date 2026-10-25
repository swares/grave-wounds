// Builds data/fields/tumbledown-1982.yaml: Mount Tumbledown on the night of 13-14 June 1982, on the
// field map at 10 m a hex. Run from this folder after editing: node make_tumbledown_field.mjs (no
// packages needed).
//
// Sources (the project's tumbledown-research.md): the 2nd Battalion, Scots Guards attacked the long
// rocky ridge from the west. G Company took the empty western end by 22:30; Left Flank passed
// through and was held for hours by machine guns and snipers with night sights in the summit crags,
// until its bayonet assault after 02:30; Right Flank went round and cleared the eastern end after
// first light. N Company of the Argentine 5th Marine Infantry Battalion held the ridge: the 4th
// Platoon (Vázquez) near the summit covering the west, the engineers' platoon behind it facing
// north, the 3rd Platoon on the northern slopes over Moody Brook, and army platoons of RI 4 and RI 12
// beside them. The ridge, its crags and the slopes are drawn by hand to that shape, not traced from
// any map, and are approximate; the deployment is Left Flank's contact at 22:30, in our own words,
// with round numbers for play (no source gives the Scots Guards' company strengths).
import { frontRow, wobble, speckle, patch, groundGrid, writeField, at } from "./field_lib.mjs";

const COLS = 220, ROWS = 120;                 // 2.2 km west to east, about 1,040 m north to south (rows 8.66 m apart)
const E = 0, W = 3;                           // facings: east (a little north) and west (a little south)
const CREST = c => 58 + Math.round(wobble(c / 9, 0.4, 1.2) * 1.5);       // the crest of the ridge, west to east
const WEST = [12, CREST(12)], SUMMIT = [124, CREST(124)], EAST = [206, CREST(206)];
function kind(c, r){
  const d = r - CREST(c);
  if (patch(c, r, { cx: SUMMIT[0], cy: SUMMIT[1], rx: 26, ry: 9, a: 0.7, b: 1.9 })) return speckle(c, r, 2) ? "r" : "h";   // the summit crags
  if (Math.abs(d) <= 3) return speckle(c, r, 3) ? "r" : "h";                                  // the rocky crest
  if (Math.abs(d) <= 12) return speckle(c, r, 6) ? "r" : "s";                                  // the steep upper slopes, rock among them
  if (d < -12) return speckle(c, r, 5) ? "m" : ".";                                            // the northern slopes down to Moody Brook, boggy
  return speckle(c, r, 4) ? "m" : ".";                                                         // the southern slopes, peat and bog
}
const grid = groundGrid(COLS, ROWS, kind);

const UK = { side: 0, facing: E }, AR = { side: 1, facing: W };
const GUARDS = { quality: "regular", weapon: "rifle_assault", kit: "ww2_rifleman", formation: "extended", mounted: false };
const GPMG = { quality: "regular", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false };
const MARINES = { quality: "regular", weapon: "rifle_assault", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };
const MARINE_MG = { quality: "regular", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false, prone: true, nv: "starlight" };
const ARMY = { quality: "green", weapon: "rifle_assault", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };
const units = [
  at("G Company, 2nd Scots Guards (on the western end)", UK, 90, GUARDS, 12, [WEST[0] + 6, WEST[1]], E),
  at("Left Flank, 2nd Scots Guards (13 and 15 Platoons in front, 14 behind)", UK, 100, { ...GUARDS, prone: true }, 14, [70, CREST(70) + 2], E),
  at("Scots Guards' machine guns", UK, 10, GPMG, 2, [62, CREST(62) - 1], E),
  at("Right Flank, 2nd Scots Guards (round the south)", UK, 90, GUARDS, 12, [48, CREST(48) + 22], E),
  at("4th Platoon, N Company, BIM 5 (Vázquez, the summit)", AR, 40, MARINES, 8, [SUMMIT[0] - 16, SUMMIT[1]], W),
  at("Marine heavy machine guns and snipers (the summit crags)", AR, 10, MARINE_MG, 2, [SUMMIT[0] - 10, SUMMIT[1] - 3], W),
  at("RI 4 platoon (Silva, beside the 4th Platoon)", AR, 30, ARMY, 6, [SUMMIT[0] - 14, SUMMIT[1] + 7], W),
  at("5th (engineers) Platoon (Miño, behind, facing north)", AR, 30, MARINES, 6, [SUMMIT[0] + 6, SUMMIT[1] - 4], 2),
  at("3rd Platoon, N Company (Lucero, the northern slopes)", AR, 40, MARINES, 8, [SUMMIT[0] + 4, SUMMIT[1] - 18], 2),
  at("RI 12 platoons (Mosteirín and Dorigón, the eastern end)", AR, 60, ARMY, 10, [EAST[0] - 8, EAST[1]], W),
  at("La Madrid's platoon, RI 6 (the counter-attack)", AR, 30, { ...ARMY, prone: false }, 6, [EAST[0], EAST[1] + 10], W),
];

// The Argentine works along the crest: bunkers in the summit crags under the 4th Platoon, its
// machine guns and the RI 4 platoon, trenches and sangars under the front rows of the platoons
// that held the ridge, and on along the crest where no unit stands.
const HELD = units.filter(u => u.side === AR.side && !u.name.includes("counter-attack"));
const BUNKERS = HELD.filter(u => /4th Platoon|machine guns|RI 4/.test(u.name)).map(u => [...u.pos]);
const isBunker = h => BUNKERS.some(b => b[0] === h[0] && b[1] === h[1]);
const heldCols = new Set(HELD.flatMap(u => frontRow(u).map(h => h[0])));
const TRENCH = [];
for (let c = 100; c <= 214; c++) if (c % 6 !== 0 && !heldCols.has(c)) TRENCH.push([c, CREST(c) - 1]);
for (const u of HELD) TRENCH.push(...frontRow(u));

writeField({
  phases: [   // an exchange is about a minute, from Left Flank's contact at 22:30 local (UTC-4); times and sources in the project's tumbledown-research.md, rounded; (est.) marks an estimate
    { name: "Left Flank in the crags", at: 1, note: "22:30 (local): G Company holds the empty western end; Left Flank passes through and is stopped by machine guns and snipers in the summit crags." },
    { name: "The counter-attack", at: 211, note: "About 02:00: under snow, La Madrid's platoon of RI 6 and Miño's engineers counter-attack and are driven back (the Argentine 03:00, an hour ahead).", arrive: ["La Madrid's platoon, RI 6 (the counter-attack)"] },
    { name: "Bayonets", at: 241, note: "02:30: the guns can at last fire ahead of 15 Platoon, and Major Kiszely leads Left Flank in with the bayonet; Right Flank moves up to go round it (when, no source gives).", arrive: ["Right Flank, 2nd Scots Guards (round the south)"] },
    { name: "The east end falls", at: 436, note: "05:45: Right Flank, gone round Left Flank, clears the eastern end (the Argentine 6:45)." },
    { name: "Withdraw to Sapper Hill", at: 526, note: "07:15: BIM 5 is ordered back to Sapper Hill (the Argentine 8:15); the 4th Platoon's last trench falls about then." },
    { name: "Tumbledown taken", at: 571, note: "About 08:00-08:15: the mountain is in the Scots Guards' hands, well after dawn." },
  ],
  objective: { at: [SUMMIT[0] - 8, SUMMIT[1]], side: 0, name: "the summit crags of Mount Tumbledown", radius: 10 },
  id: "tumbledown-1982", name: "Mount Tumbledown, 13-14 June 1982", sides: ["British", "Argentines"], table: "falklands-1982-wounds",
  travel: { map: "tumbledown-1982", place: "Mount Tumbledown", within: 1, sides: ["British", "Argentines"] },
  weather: "{cond: snow, wind: breeze, dir: W, light: night, ground: {mud: 1, snow: 1}}",
  grid, units,
  hexWorks: { trench: TRENCH.filter(h => !isBunker(h)), bunker: BUNKERS },
  support: [
    { name: "The 105 mm light guns (up to five batteries)", side: 0, kind: "field", tubes: 18 },
    { name: "Naval gunfire (a frigate's 4.5-inch gun)", side: 0, kind: "field", tubes: 1 },
    { name: "Scots Guards' 81 mm mortars", side: 0, kind: "mortar", tubes: 4 },
    { name: "N Company's 60 mm mortars (two sections near the summit)", side: 1, kind: "mortar", tubes: 2 },
    { name: "BIM 5's 81 mm mortars (Mount William)", side: 1, kind: "mortar", tubes: 6 },
    { name: "Marine 105 mm pack howitzers (B Battery)", side: 1, kind: "field", tubes: 6 },
  ],
  header: [
    `Mount Tumbledown on the night of 13-14 June 1982, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 2.2 km west to east and`,
    "1,040 m north to south, north at the top: the long rocky ridge across the middle, from its western",
    "end (left) to the summit crags in the middle and the eastern end (right), the northern slopes",
    "falling to Moody Brook along the top, the southern slopes of peat and bog along the bottom.",
    "Generated by tools/maps/make_tumbledown_field.mjs: edit that file and re-run it rather than this one.",
    "The ridge, its crags and the slopes are drawn by hand to the shape the accounts give, not traced",
    "from any map; the deployment is Left Flank's contact at 22:30, in our own words, with round",
    "numbers for play (no source gives the Scots Guards' company strengths). Night and falling snow;",
    "the moon rose at 22:45, about half lit, behind cloud. The marines' machine guns and snipers",
    "had night sights (starlight scopes here; the kind is not recorded).",
    "",
    "What happened, briefly: on the night of 13-14 June 1982 the 2nd Battalion, Scots Guards attacked",
    "Tumbledown from the west after a diversion on the south. G Company took the empty western end;",
    "Left Flank was held for four hours among the crags by the marines of N Company, BIM 5, until its",
    "bayonet assault at 02:30; Right Flank went round and cleared the eastern end at first light. The",
    "Argentines were ordered back to Sapper Hill, and the mountain was taken by about 08:00. The",
    "Argentine surrender followed that day.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
