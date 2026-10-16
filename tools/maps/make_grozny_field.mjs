// Builds data/fields/grozny-1995.yaml: the railway station in Grozny at dusk on 31 December
// 1994, on the field map at 10 m a hex. Run from this folder after editing:
// node make_grozny_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the battle as it is
// summarised publicly from the Russian and Western accounts. On the afternoon of 31 December the
// 1st Battalion of the 131st (Maikop) Motor Rifle Brigade drove its tanks and infantry carriers
// into the station square and occupied the station and the freight yard; Chechen fighters in the
// apartment blocks and houses round the square cut the column off, and through the night teams
// with RPG rocket launchers fired down from the upper floors into the carriers and tanks parked in
// the streets; the survivors tried to break out on 1 January. The square, the station, the yards,
// the tracks and the blocks round them are drawn by hand to that pattern, not traced from any map
// or photograph, and are approximate; the deployment is the fight for the square at dusk, in our own
// words, with round numbers for play.
import { N, S, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 140, ROWS = 110;                 // 1400 m east to west, about 950 m north to south
const STATION = [70, 58], SQUARE = [70, 44], YARD = 76;  // the station building, its square to the north, the freight yard's tracks from row 76 south
function rail(c, r){                          // the station, its square and the tracks and yards south of it (null: neither)
  if (patch(c, r, { cx: STATION[0], cy: STATION[1], rx: 12, ry: 3 })) return "B";                       // the station building
  if (patch(c, r, { cx: SQUARE[0], cy: SQUARE[1], rx: 16, ry: 9 })) return speckle(c, r, 15) ? "x" : ".";  // the station square
  if (r >= YARD - 12 && r < YARD) return speckle(c, r, 12) ? "x" : ".";                                  // the platforms and tracks
  if (r >= YARD && r < YARD + 14) return speckle(c, r, 6) ? "T" : ".";                                    // the freight yard and its sheds
  return null;
}
function town(c, r){                          // the streets, the apartment blocks and the houses
  if (c % 20 === 10 || r % 16 === 8) return speckle(c, r, 14) ? "x" : ".";                               // streets, wrecks and rubble in them
  if (r < 40 || r >= YARD + 14) return speckle(c, r, 4) ? "." : "B";                                     // five- and nine-storey apartment blocks
  return speckle(c, r, 4) ? "." : "T";                                                                    // older houses and shops by the station
}
const kind = (c, r) => rail(c, r) ?? town(c, r);
const grid = groundGrid(COLS, ROWS, kind);

const RU = { side: 0, facing: N }, CH = { side: 1, facing: S };
const SOLDIER = { quality: "green", weapon: "rifle_assault", kit: "ww2_rifleman", formation: "extended", mounted: false };
const BMP = { quality: "green", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "ifv" };
const TANK = { ...BMP, vehicle: "tank" };
const FIGHTER = { quality: "veteran", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, prone: true };
const RPG = { ...FIGHTER, weapon: "rpg" };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "mg", mounted: false, prone: true };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("1st Battalion, 131st Brigade (in the station)", RU, 150, SOLDIER, 16, [STATION[0], STATION[1] + 1], N),
  at("131st Brigade's infantry carriers (the square)", RU, 36, BMP, 3, [SQUARE[0] - 6, SQUARE[1]], N),
  at("131st Brigade's tanks (the square)", RU, 24, TANK, 2, [SQUARE[0] + 8, SQUARE[1]], N),
  at("131st Brigade's men in the freight yard", RU, 80, SOLDIER, 12, [STATION[0] + 30, YARD + 4], N),
  at("Chechen RPG teams (the blocks north of the square)", CH, 40, RPG, 6, [SQUARE[0], SQUARE[1] - 12], S),
  at("Chechen RPG teams (the houses to the west)", CH, 30, RPG, 4, [SQUARE[0] - 20, SQUARE[1]], 0),
  at("Chechen RPG teams (the houses to the east)", CH, 30, RPG, 4, [SQUARE[0] + 20, SQUARE[1] + 4], 3),
  at("Chechen fighters (north)", CH, 150, FIGHTER, 16, [SQUARE[0] + 2, 12], S),
  at("Chechen fighters (south of the yards)", CH, 120, FIGHTER, 14, [60, YARD + 22], N),
  at("Chechen machine guns", CH, 10, MG, 2, [SQUARE[0] + 24, 30], 4),
];

writeField({
  phases: [   // an exchange is about a minute; sunset and the moon worked out for the place and day
    { name: "Dusk in the square", at: 1, note: "About 16:30, as the sun sets: the column is cut off in the square and the station, and the Chechens close in." },
    { name: "Dark", at: 31, note: "By about 17:05 it is dark; overcast, and the moon a day from new.", light: "night" },
  ],
  // The night's fight: the Chechens close in on the station the battalion holds (the afternoon's drive into it is over).
  objective: { at: STATION, side: 1, name: "the railway station", radius: 5 },
  id: "grozny-1995", name: "Grozny: the railway station, 31 December 1994", sides: ["Russians", "Chechens"], table: "chechnya-wounds",
  travel: { map: "grozny-1995", place: "Grozny railway station", within: 1, sides: ["Russians", "Chechens"] },
  weather: "{cond: overcast, wind: calm, light: dusk, ground: {mud: 1, snow: 0}}",
  grid, units,
  support: [
    { name: "Russian artillery", side: 0, kind: "field", tubes: 18 },
    { name: "Russian mortars", side: 0, kind: "mortar", tubes: 6 },
    { name: "Chechen mortars", side: 1, kind: "mortar", tubes: 4 },
  ],
  header: [
    `The railway station in Grozny at dusk on 31 December 1994, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1400 m east to west and`,
    "950 m north to south, north at the top: the station building in the middle with its square to",
    "the north, the platforms, tracks and freight yard to the south, older houses round the",
    "station, and apartment blocks of five and nine storeys beyond, with streets between.",
    "Generated by tools/maps/make_grozny_field.mjs: edit that file and re-run it rather than this one.",
    "The square, station, yards, tracks and blocks are drawn by hand to that pattern, not traced from",
    "any map or photograph; the deployment is the fight for the square at dusk, in our own words, with",
    "round numbers for play. The apartment blocks are tall buildings (tall buildings), the houses",
    "buildings; vehicles keep to the square, the streets and the tracks. Winter dusk, the dark coming on:",
    "the phases bring a dark night at about 17:05 (sunset about 16:30, the moon a day from new, worked",
    "out for the place and day). The objective is the Chechens': the night was their attack on the station.",
    "",
    "What happened, briefly: on the afternoon of 31 December 1994 the 131st Brigade's 1st Battalion",
    "drove into the station square and took the station and the freight yard. Chechen fighters in",
    "the buildings round it cut the column off and, through the night, fired rockets down into the",
    "tanks and carriers in the streets. Most of the brigade's armour was destroyed, and about 18:00",
    "on 1 January its survivors broke out of the station; Colonel Savin was killed in the breakout",
    "(his death is marked on 2 January).",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
