// Builds data/fields/fallujah-2004.yaml: the northern Jolan in Fallujah on 9 November 2004, on the
// field map at 10 m a hex. Run from this folder after editing: node make_fallujah_field.mjs (no
// packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Marine Corps' and
// Army's histories as summarised publicly. RCT-1's Marines came south out of the apartment blocks
// and across the railway into the Jolan, the old quarter of narrow lanes and walled, flat-roofed
// houses by the Euphrates; Army tanks and Bradleys of the 2nd Battalion, 7th Cavalry led down the
// wider streets, firing into the houses, and the Marines cleared them room by room behind; the
// insurgents fought from the houses and the mosques, with rocket launchers, machine guns and
// snipers, and fell back south. The streets, the houses, the park, the mosques and the railway are
// drawn by hand to that pattern, not traced from any map or photograph, and are approximate; the
// deployment is the attack south, in our own words, with round numbers for play.
import { N, S, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 140, ROWS = 120;                 // 1400 m east to west, about 1040 m north to south
const RAIL = 10, RIVER = 6;                   // the railway embankment across the north; the Euphrates along the west
const MAIN = 72;                              // the wide street south from the railway, the armour's way in
const PARK = [96, 64];
const MOSQUES = [[40, 40], [86, 92], [116, 34], [58, 78]];
function edges(c, r){                         // the river and its bank, the railway, the main street, the park, the mosques (null: none)
  if (c < RIVER) return "w";
  if (c < RIVER + 4) return speckle(c, r, 3) ? "." : "F";                                              // palms along the bank
  if (Math.abs(c - MAIN) <= 1 || r === RAIL || r === RAIL + 1) return ".";                              // the main street, and the railway across it
  if (r < RAIL) return speckle(c, r, 3) ? "." : "B";                                                   // the apartment blocks north of the railway
  if (patch(c, r, { cx: PARK[0], cy: PARK[1], rx: 8, ry: 6 })) return speckle(c, r, 4) ? "F" : ".";     // the Jolan park
  if (MOSQUES.some(([cx, cy]) => patch(c, r, { cx, cy, rx: 2, ry: 2 }))) return "B";
  return null;
}
function lanes(c, r){                         // the lanes and the walled houses
  if (c % 9 === 0 || r % 8 === 4) return speckle(c, r, 16) ? "x" : ".";                                // lanes, with wrecks and rubble
  return speckle(c, r, 13) ? "x" : "T";                                                                 // walled, flat-roofed houses
}
const kind = (c, r) => edges(c, r) ?? lanes(c, r);
const grid = groundGrid(COLS, ROWS, kind);

const US = { side: 0, facing: S }, IN = { side: 1, facing: N };
const MARINE = { quality: "veteran", weapon: "rifle_assault", kit: "interceptor", formation: "extended", mounted: false };
const SAW = { quality: "veteran", weapon: "machine_gun", kit: "interceptor", formation: "mg", mounted: false };
const TANK = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank" };
const BRADLEY = { ...TANK, vehicle: "ifv" };
const FIGHTER = { quality: "regular", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, prone: true };
const RPG = { ...FIGHTER, weapon: "rpg" };
const PKM = { quality: "regular", weapon: "machine_gun", kit: "none", formation: "mg", mounted: false, prone: true };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("2-7 Cavalry's M1A1 tanks (the main street)", US, 16, TANK, 2, [MAIN, 14], S),
  at("2-7 Cavalry's Bradleys (behind the tanks)", US, 12, BRADLEY, 2, [MAIN, 4], S),
  at("Marine company (west of the main street)", US, 150, MARINE, 16, [44, 14], S),
  at("Marine company (east of the main street)", US, 150, MARINE, 16, [104, 14], S),
  at("Marine machine guns", US, 12, SAW, 2, [60, 6], S),
  at("Insurgents in the houses (north-west)", IN, 80, FIGHTER, 10, [40, 32], N),
  at("Insurgents in the houses (north-east)", IN, 80, FIGHTER, 10, [110, 30], N),
  at("Insurgent RPG teams (by the main street)", IN, 20, RPG, 3, [MAIN - 2, 34], N),
  at("Insurgent RPG teams (the park)", IN, 20, RPG, 3, [PARK[0] - 10, PARK[1] - 8], N),
  at("Insurgents in the mosque and the houses south", IN, 120, FIGHTER, 12, [58, 72], N),
  at("Insurgent machine guns", IN, 10, PKM, 2, [99, 46], N),
];

writeField({
  id: "fallujah-2004", name: "Fallujah: into the Jolan, 9 November 2004", sides: ["Coalition", "Insurgents"], table: "oif-oef-2001-wounds",
  travel: { map: "fallujah-2004", place: "The Jolan", within: 1, sides: ["Coalition", "Insurgents"] },
  weather: "{cond: overcast, wind: breeze, dir: NW, ground: {mud: 1, snow: 0}}",
  grid, units,
  support: [
    { name: "Marine and Army 155 mm howitzers", side: 0, kind: "howitzer", tubes: 12 },
    { name: "81 mm and 120 mm mortars", side: 0, kind: "mortar", tubes: 8 },
    { name: "Close air support", side: 0, kind: "fighter_bomber", tubes: 6 },
    { name: "Insurgent mortars", side: 1, kind: "mortar", tubes: 4 },
  ],
  header: [
    `The northern Jolan in Fallujah on 9 November 2004, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1400 m east to west and 1040 m`,
    "north to south, north at the top: the apartment blocks and the railway across the top, the",
    "Euphrates and its palms down the left, the main street south from the railway, the Jolan's",
    "lanes and walled houses everywhere else, the park and four mosques among them.",
    "Generated by tools/maps/make_fallujah_field.mjs: edit that file and re-run it rather than this one.",
    "The streets, houses, park, mosques and railway are drawn by hand to that pattern, not traced from",
    "any map or photograph; the deployment is the attack south, in our own words, with round numbers",
    "for play. The houses are buildings, the blocks and mosques tall buildings; armour keeps to the",
    "lanes and the main street. Overcast after the night's rain.",
    "",
    "What happened, briefly: on 9 November 2004 RCT-1's Marines came south across the railway into",
    "the Jolan behind the tanks and Bradleys of the 2nd Battalion, 7th Cavalry, which fired into the",
    "houses as they went. The Marines cleared the houses room by room; the insurgents fought from the",
    "houses and mosques with rockets, machine guns and snipers and fell back south. By 13 November",
    "the Jolan was taken, though the clearing went on for weeks.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
