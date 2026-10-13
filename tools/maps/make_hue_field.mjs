// Builds data/fields/hue-1968.yaml: the Marines clearing the new city of Hue, south of the
// Perfume River, 4-6 February 1968, on the field map at 10 m a hex. Run from this folder after
// editing: node make_hue_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Marine Corps'
// history of 1968 as summarised publicly. The 2nd Battalion, 5th Marines, with the 1st
// Battalion, 1st Marines, fought east along the south bank from the MACV compound and the
// university, building by building, through the Treasury, the public health building, the
// hospital and the prison, with tanks and Ontos firing into the buildings and 81 mm mortars and
// recoilless rifles; artillery was held back at first to spare the city; the North Vietnamese
// 4th Regiment held the stone public buildings with rifles, machine guns and RPGs; the weather
// was cold, with drizzle and low cloud. The streets, blocks and buildings are drawn by hand to
// that pattern, not traced from any map or photograph, and are approximate; the deployment is
// the attack east, in our own words, with round numbers for play.
import { N, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 150, ROWS = 110;                 // 1500 m east to west, about 950 m north to south
const RIVER = 8, LE_LOI = 11, CANAL = 100;    // the river along the north, Le Loi street on its bank, the Phu Cam canal along the south
const HIGHWAY = 40, BRIDGE = 30;              // Highway 1 (four hexes wide from here) north from the An Cuu bridge; the river bridge into the Citadel
const onHighway = c => c >= HIGHWAY - 1 && c <= HIGHWAY + 2;
const MACV = [44, 22], UNIVERSITY = [62, 18], PROVINCE = [86, 24], TREASURY = [98, 42], HOSPITAL = [122, 30], PRISON = [102, 74];
const BIG = [MACV, UNIVERSITY, PROVINCE, TREASURY, HOSPITAL, PRISON];
function water(c, r){                         // the river and the canal, crossed by their bridges; Le Loi street
  if (r <= RIVER) return Math.abs(c - BRIDGE) <= 1 ? "." : "w";
  if (r <= LE_LOI) return ".";
  if (r >= CANAL && r <= CANAL + 3) return onHighway(c) ? "." : "w";
  return null;
}
function streets(c, r){                       // Highway 1 and the grid of streets between the blocks
  if (onHighway(c)) return ".";
  if (r > CANAL) return speckle(c, r, 3) ? "m" : ".";                                               // paddies and gardens south of the canal
  return c % 16 === 8 || r % 14 === 4 ? "." : null;
}
function blocks(c, r){                        // the public buildings, the park along the river, the blocks of houses and shops
  if (BIG.some(([cx, cy]) => patch(c, r, { cx, cy, rx: 5, ry: 3 }))) return "B";
  if (r < 16 && c > 66 && c < 112) return speckle(c, r, 3) ? "F" : ".";                             // the park along the river bank
  if (speckle(c, r, 11)) return "x";                                                                 // shell-holed and fallen
  return speckle(c, r, 5) ? "." : "T";                                                              // houses, shops and courtyards
}
const kind = (c, r) => water(c, r) ?? streets(c, r) ?? blocks(c, r);
const grid = groundGrid(COLS, ROWS, kind);

const US = { side: 0, facing: 0 }, NV = { side: 1, facing: 3 };
const MARINE = { quality: "regular", weapon: "rifle_assault", kit: "vietnam_usmc", formation: "extended", mounted: false };
const MG = { quality: "regular", weapon: "machine_gun", kit: "vietnam_usmc", formation: "mg", mounted: false };
const TANK = { quality: "regular", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank" };
const PAVN = { quality: "veteran", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, prone: true };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("F Company, 2/5 Marines (by the university)", US, 140, MARINE, 12, [UNIVERSITY[0] + 7, 24], 0),
  at("H Company, 2/5 Marines (for the Treasury)", US, 140, MARINE, 12, [74, 36], 0),
  at("G Company, 2/5 Marines (the south blocks)", US, 120, MARINE, 12, [70, 62], 0),
  at("A Company, 1/1 Marines and the MACV compound", US, 160, MARINE, 10, [MACV[0], MACV[1] + 5], 0),
  at("Marine machine guns", US, 12, MG, 2, [UNIVERSITY[0], UNIVERSITY[1] + 3], 0),
  at("Marine M48 tanks (Highway 1)", US, 16, TANK, 2, [HIGHWAY, 46], N),
  at("North Vietnamese in the provincial headquarters", NV, 120, PAVN, 10, [PROVINCE[0], PROVINCE[1] + 4], 3),
  at("North Vietnamese in the Treasury", NV, 150, PAVN, 10, [TREASURY[0], TREASURY[1] + 4], 3),
  at("North Vietnamese in the hospital", NV, 150, PAVN, 10, [HOSPITAL[0], HOSPITAL[1] + 4], 3),
  at("North Vietnamese in the prison", NV, 120, PAVN, 10, [PRISON[0], PRISON[1] + 4], 3),
  at("North Vietnamese RPG teams", NV, 30, { ...PAVN, weapon: "rpg" }, 4, [82, 44], 3),
  at("North Vietnamese machine guns", NV, 10, { ...MG, kit: "none", quality: "veteran", prone: true }, 2, [92, 32], 3),
];

writeField({
  objective: { at: PROVINCE, side: 0, name: "the provincial headquarters", radius: 3 },
  id: "hue-1968", name: "Hue: the new city, 4-6 February 1968", sides: ["United States and ARVN", "North Vietnamese"], table: "vietnam-1965-70-hospitalized",
  travel: { map: "hue-1968", place: "Hue, the new city (south bank)", within: 1, sides: ["United States and ARVN", "North Vietnamese"] },
  weather: "{cond: rain, wind: breeze, dir: NE, ground: {mud: 1, snow: 0}}",
  grid, units,
  hexWorks: { bunker: [[TREASURY[0] - 5, TREASURY[1]], [HOSPITAL[0] - 5, HOSPITAL[1]], [PRISON[0] - 5, PRISON[1]]] },
  support: [
    { name: "Marine 81 mm mortars", side: 0, kind: "mortar", tubes: 8 },
    { name: "Marine 105 mm howitzers (held back at first)", side: 0, kind: "field", tubes: 6 },
    { name: "North Vietnamese mortars", side: 1, kind: "mortar", tubes: 8 },
    { name: "North Vietnamese rockets and guns", side: 1, kind: "field", tubes: 4 },
  ],
  header: [
    `The new city of Hue, south of the Perfume River, on 4-6 February 1968, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1500 m`,
    "east to west and 950 m north to south, north at the top: the river along the top with its bridge",
    "into the Citadel, Le Loi street and the park along the bank, Highway 1 coming up from the An",
    "Cuu bridge on the Phu Cam canal along the bottom, and between them blocks of houses and the",
    "stone public buildings: the MACV compound, the university, the provincial headquarters, the",
    "Treasury, the hospital and the prison.",
    "Generated by tools/maps/make_hue_field.mjs: edit that file and re-run it rather than this one.",
    "The streets, blocks and buildings are drawn by hand to that pattern, not traced from any map or",
    "photograph; the deployment is the Marines attacking east, in our own words, with round numbers",
    "for play. The public buildings are tall buildings (tall buildings) and the houses buildings,",
    "with rubble where the shells fell; tanks keep to the streets. Cold drizzle and low cloud.",
    "",
    "What happened, briefly: from 4 February the 2nd Battalion, 5th Marines, with the 1st Battalion,",
    "1st Marines, fought east from the MACV compound and the university, taking the Treasury, the",
    "public health building and the hospital building by building with tanks, Ontos, recoilless",
    "rifles and tear gas; the provincial headquarters fell on the 6th. By 10 February the south bank",
    "was clear, and the fighting moved into the Citadel.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
