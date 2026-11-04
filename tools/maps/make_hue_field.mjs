// Builds data/fields/hue-1968.yaml: the Marines taking the provincial headquarters in the new city
// of Hue, south of the Perfume River, on 6 February 1968, on the field map at 10 m a hex. Run from this folder after
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
// the morning of 6 February, the last day of the three (the Treasury fell on the 4th, the hospital
// was entered on the 5th), in our own words, with round numbers for play. Played from the 4th, the
// fight ran 55 hours and every run was cut off after 20 (self_play.most), long before the
// headquarters fell.
import { N, patch, speckle, groundGrid, unit, led, writeField, at } from "./field_lib.mjs";

const COLS = 150, ROWS = 110;                 // 1500 m east to west, about 950 m north to south
const RIVER = 8, LE_LOI = 11, CANAL = 100;    // the river along the north, Le Loi street on its bank, the Phu Cam canal along the south
const HIGHWAY = 40, BRIDGE = 30;              // Highway 1 (four hexes wide from here) north from the An Cuu bridge; the river bridge into the Citadel
const onHighway = c => c >= HIGHWAY - 1 && c <= HIGHWAY + 2;
// The hospital is drawn by the river and the provincial headquarters to the south-east beyond the
// Treasury, so that the Marines come to them in the order they did (the hospital entered on the 5th,
// the headquarters taken on the 6th); neither place is traced from a map.
const MACV = [44, 22], UNIVERSITY = [62, 18], HOSPITAL = [86, 24], TREASURY = [98, 42], PROVINCE = [112, 52], PRISON = [102, 74];
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
const MARINE = { quality: "regular", weapon: "rifle_assault", kit: "vietnam_usmc", formation: "extended", mounted: false, masks: true };   // every man of 2/5 carried a gas mask (2/5's chronology)
const MG = { quality: "regular", weapon: "machine_gun", kit: "vietnam_usmc", formation: "mg", mounted: false };
const TANK = { quality: "regular", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank" };
const ONTOS = { ...TANK, vehicle: "ontos" };
const PAVN = { quality: "veteran", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, prone: true };
// Leaders from the accounts (heroes.field_leaders), commissioned officers with the unit they led,
//   ranks as the sources give them. Sources: https://historynet.com/?p=13737864
//   https://miltours.com/image/data/brochures/lneckhuepart1.pdf
// The morning of 6 February (2/5's February command chronology, through the project's hue-supports
//   notes): H Company halted by heavy fire before the provincial headquarters at 09:50; tanks, 106 mm
//   recoilless rifles and Ontos called up; an 81 mm mission with E-8 gas silenced the North Vietnamese
//   weapons and let the Marines into the compound (4 Marines killed, 9 wounded, 6 North Vietnamese
//   killed). One tank took two B-40s and fought on; an Ontos sent to blast the wall was knocked out by
//   a B-40, and a 106 on a Mule made the breach (Nolan; Wikipedia after Bowden). G Company was at the
//   hospital. The company strengths are ours (no figure for the 6th: the companies came in at 140 and
//   had lost men every day), as are the North Vietnamese numbers (Nolan: six dead or dying pulled
//   from the spider holes round the headquarters and one taken, many escaped) and every position.
const units = [
  at("H Company, 2/5 Marines (before the headquarters)", US, 100, MARINE, 10, [PROVINCE[0] - 12, PROVINCE[1]], 0),
  at("G Company, 2/5 Marines (at the hospital)", US, 100, MARINE, 10, [HOSPITAL[0] - 10, HOSPITAL[1]], 0),
  at("Marine M48 tanks", US, 8, TANK, 2, [88, 46], N),                              // the 2 gun tanks the accounts name in the assaults
  at("Marine Ontos", US, 6, ONTOS, 2, [88, 60], N),                                  // the 2 that came in with H/2/5 on 2 February
  at("106 mm recoilless rifle on a Mule", US, 4, { ...MARINE, weapon: "recoilless" }, 1, [PROVINCE[0] - 17, PROVINCE[1] + 5], 0),   // one gun, its crew ours
  at("North Vietnamese in the provincial headquarters", NV, 40, PAVN, 6, [PROVINCE[0], PROVINCE[1]], 3),
  at("North Vietnamese in the hospital", NV, 40, PAVN, 6, [HOSPITAL[0], HOSPITAL[1]], 3),
  at("North Vietnamese RPG teams", NV, 10, { ...PAVN, weapon: "rpg" }, 2, [PROVINCE[0] - 4, PROVINCE[1] + 5], 3),
  at("North Vietnamese machine guns", NV, 10, { ...MG, kit: "none", quality: "veteran", prone: true }, 2, [PROVINCE[0] + 3, PROVINCE[1] - 2], 3),
];
led(units, {
  "H Company, 2/5 Marines (before the headquarters)": [["Ron Christmas", "Captain"], ["Leo Myers", "Lieutenant"]],
  "G Company, 2/5 Marines (at the hospital)": [["Chuck Meadows", "Captain"], ["Michael McNeil", "Second Lieutenant"]],
});

// A strongpoint (a bunker) under the middle of the North Vietnamese in the headquarters (its spider
// holes) and in the hospital (its bunkers: 2/5's chronology has the hospital ringed by them).
const STRONGPOINTS = units.filter(u => /in the (provincial headquarters|hospital)/.test(u.name)).map(u => [...u.pos]);

writeField({
  phases: [   // an exchange is about a minute, from 09:50
    { name: "Halted before the headquarters", at: 1, note: "09:50 on 6 February: H Company, 2/5 Marines is halted by heavy fire before the provincial headquarters; G Company is at the hospital (2/5's chronology)." },
    { name: "Tanks, 106s and Ontos called up", at: 31, note: "Tanks, 106 mm recoilless rifles and Ontos are called up (2/5's chronology; when is ours). About 10:20 the North Vietnamese retake the hospital's TB building (Gurske).", arrive: ["Marine M48 tanks", "Marine Ontos", "106 mm recoilless rifle on a Mule"] },
  ],
  objective: { at: PROVINCE, side: 0, name: "the provincial headquarters", radius: 3 },
  ends: { at: 256, why: "the flag over the provincial headquarters a little past 14:00 (Nolan), the hospital secured by 14:05 (Gurske): from 09:50" },
  id: "hue-1968", name: "Hue: the provincial headquarters, 6 February 1968", sides: ["United States and ARVN", "North Vietnamese"], table: "vietnam-1965-70-hospitalized",
  travel: { map: "hue-1968", place: "Hue, the new city (south bank)", within: 1, sides: ["United States and ARVN", "North Vietnamese"] },
  weather: "{cond: rain, wind: breeze, dir: NE, ground: {mud: 1, snow: 0}}",
  grid, units,
  hexWorks: { bunker: STRONGPOINTS },
  support: [
    { name: "Marine 81 mm mortars", side: 0, kind: "mortar", tubes: 8 },
    { name: "E-8 tear gas launcher", side: 0, kind: "e8", tubes: 1 },      // 2/5's chronology: the E-8 used at the Treasury, the provincial headquarters and the hospital; one launcher is ours
    { name: "Marine 105 mm howitzers (observed missions only)", side: 0, kind: "field", tubes: 6 },
    { name: "North Vietnamese mortars", side: 1, kind: "mortar", tubes: 8 },
    { name: "North Vietnamese rockets and guns", side: 1, kind: "field", tubes: 4 },
  ],
  header: [
    `The new city of Hue, south of the Perfume River, on 6 February 1968, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1500 m`,
    "east to west and 950 m north to south, north at the top: the river along the top with its bridge",
    "into the Citadel, Le Loi street and the park along the bank, Highway 1 coming up from the An",
    "Cuu bridge on the Phu Cam canal along the bottom, and between them blocks of houses and the",
    "stone public buildings: the MACV compound, the university, the provincial headquarters, the",
    "Treasury, the hospital and the prison.",
    "Generated by tools/maps/make_hue_field.mjs: edit that file and re-run it rather than this one.",
    "The streets, blocks and buildings are drawn by hand to that pattern, not traced from any map or",
    "photograph; the deployment is the morning of 6 February, H Company halted before the provincial",
    "headquarters and G Company at the hospital, in our own words, with round numbers for play.",
    "The public buildings are tall buildings (tall buildings) and the houses buildings,",
    "with rubble where the shells fell; tanks keep to the streets. Cold drizzle and low cloud.",
    "",
    "What happened, briefly: from 4 February the 2nd Battalion, 5th Marines, with the 1st Battalion,",
    "1st Marines, fought east from the MACV compound and the university, taking the Treasury, the",
    "public health building and the hospital building by building with tanks, Ontos, recoilless",
    "rifles and tear gas; the provincial headquarters fell on the 6th, its flag pulled down a little",
    "after 14:00. By 10 February the south bank was clear, and the fighting moved into the Citadel.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
