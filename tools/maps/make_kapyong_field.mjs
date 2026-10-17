// Builds data/fields/kapyong-1951.yaml: Hill 504 and the valley at Kapyong on the night of 23-24
// April 1951, on the field map at 10 m a hex. Run from this folder after editing:
// node make_kapyong_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the plain facts of the
// battle as the official histories give them and as they are summarised publicly. 3 RAR held
// Hill 504 east of the Kapyong river, its companies on the hill's spurs and summit and one on a
// knoll by the road in the valley, battalion headquarters at Chuktun-ni with a platoon of
// American Shermans forward in the valley; from 21:30 on the 23rd the Chinese came down the
// valley and up the spurs in the dark, overrunning the tanks' outpost and part of B Company's
// knoll and attacking A and D Companies on the hill until dawn. The hill, the spurs, the river,
// the road and the hamlet are drawn by hand to that shape, not traced from any map, and are
// approximate; the deployment is the night attack, in our own words, with round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 220, ROWS = 160;                 // 2200 m east to west, about 1390 m north to south
const RIVER = r => 92 + Math.round(wobble(r / 10, 0.7, 1.9) * 2);        // the Kapyong river, north to south
const ROAD = r => RIVER(r) - 8 + Math.round(wobble(r / 7, 1.2, 0.4));    // the road up the valley, west of the river
const SUMMIT = [176, 64], KNOLL = [106, 70], HAMLET = [100, 132], TANKS = [ROAD(56) + 4, 56];
function valley(c, r){                            // the river, the road and what stands by it (null: none of these)
  if (Math.abs(c - RIVER(r)) <= 1) return "m";                                                          // the river: shallow, stony, fordable
  if (c === ROAD(r)) return ".";                                                                        // the road
  if (patch(c, r, { cx: TANKS[0], cy: TANKS[1], rx: 6, ry: 3 })) return ".";                           // dry ground by the road where the tanks stood
  if (patch(c, r, { cx: HAMLET[0], cy: HAMLET[1], rx: 6, ry: 4 })) return speckle(c, r, 3) ? "." : "T";  // Chuktun-ni
  return null;
}
function hills(c, r){                             // the knoll, Hill 504 and the hills west of the valley (null: the valley floor)
  if (patch(c, r, { cx: KNOLL[0], cy: KNOLL[1], rx: 6, ry: 5, a: 0.3, b: 1.2 })) return "h";            // B Company's knoll by the road
  if (patch(c, r, { cx: SUMMIT[0], cy: SUMMIT[1], rx: 18, ry: 12, a: 1.1, b: 0.5 })) return speckle(c, r, 4) ? "r" : "h";   // Hill 504's summit
  const wooded = c > 120 + wobble(r / 9, 0.2, 1.4) * 3                                                   // Hill 504's slopes and spurs
    || c < 40 + wobble(r / 8, 1.5, 0.6) * 3;                                                             // the hills west of the valley, towards 677
  if (wooded) return speckle(c, r, 3) ? "F" : "h";
  return null;
}
function kind(c, r){
  return valley(c, r) ?? hills(c, r) ?? (speckle(c, r, 4) ? "." : "m");                                 // else paddies in the valley
}
const grid = groundGrid(COLS, ROWS, kind);

const UN = { side: 0, facing: N }, CH = { side: 1, facing: S };
const DIGGER = { quality: "veteran", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false, prone: true };
const PVA = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false };
const TANK = { quality: "regular", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank" };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("A Company, 3 RAR (the north spur)", UN, 120, DIGGER, 14, [150, 40], N),
  at("D Company, 3 RAR (the summit)", UN, 120, DIGGER, 14, [SUMMIT[0], SUMMIT[1] - 8], N),
  at("B Company, 3 RAR (the knoll by the road)", UN, 120, DIGGER, 12, [KNOLL[0], KNOLL[1] - 3], N),
  at("C Company, 3 RAR (in reserve on the hill)", UN, 120, { ...DIGGER, prone: false }, 14, [160, 96], N),
  at("Battalion machine guns", UN, 10, MG, 2, [150, 48], N),
  at("3 RAR headquarters (Chuktun-ni)", UN, 60, { ...DIGGER, quality: "regular" }, 10, [HAMLET[0], HAMLET[1] - 6], N),
  at("Platoon of Shermans (72nd Heavy Tank Battalion)", UN, 20, TANK, 5, TANKS, N),
  at("Chinese battalion down the valley", CH, 600, PVA, 30, [ROAD(10), 10], S),
  at("Chinese battalion onto the north spur", CH, 500, PVA, 30, [150, 12], S),
  { ...at("Chinese battalion round the east of the hill", CH, 500, PVA, 30, [200, 30], 3), via: [[214, 96], [150, 128], [100, 126]] },   // down the east of the hill and round its south to battalion headquarters (the phase note; the way is our reading)
  at("Chinese machine guns", CH, 10, { ...MG, kit: "none", prone: false }, 2, [110, 20], 4),
];

writeField({
  phases: [   // an exchange is about a minute; times from docs and sources in the project's battle-phases research, rounded
    { name: "The valley outpost is hit", at: 1, note: "21:30: the Chinese strike the forward tank platoon and probe A Company." },
    { name: "Round the flank", at: 31, note: "About 22:00, mixed in with retreating South Koreans, the Chinese reach battalion headquarters at Chuktun-ni.", arrive: ["Chinese battalion round the east of the hill"] },
    { name: "The main assaults", at: 201, note: "00:50: the main assault on B Company's 4 Platoon; A Company's 1 Platoon is pulled back at 01:00." },
    { name: "Headquarters pulls out", at: 451, note: "05:00 to 06:00: battalion headquarters withdraws down the valley, the Shermans escorting it." },
    { name: "B Company called up the hill", at: 586, note: "07:15: after the last assault on it at 04:45, B Company is ordered up onto the hill." },
  ],
  ends: { at: 871, why: "fell back the next afternoon: 12:00 from 21:30" },
  objective: { at: SUMMIT, side: 1, name: "Hill 504's summit", radius: 8 },
  id: "kapyong-1951", name: "Hill 504 and the valley at Kapyong, 23-24 April 1951", sides: ["United Nations", "Chinese"], table: "korea-1950-53-hospitalized",
  travel: { map: "kapyong-1951", place: "Hill 504", within: 1, sides: ["United Nations", "Chinese"] },
  weather: "{cond: fair, wind: calm, light: night, ground: {mud: 0, snow: 0}}",
  grid, units,
  support: [
    { name: "16th Field Regiment, RNZA (25-pounders)", side: 0, kind: "field", tubes: 24 },
    { name: "3 RAR's mortars", side: 0, kind: "mortar", tubes: 6 },
    { name: "Chinese mortars", side: 1, kind: "mortar", tubes: 8 },
  ],
  header: [
    `Hill 504 and the Kapyong valley on the night of 23-24 April 1951, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 2200 m east to`,
    "west and 1390 m north to south, north at the top: the valley with its paddies, road and river",
    "in the middle, B Company's knoll by the road, Hill 504's summit and spurs on the right, the hills",
    "towards 677 on the left, Chuktun-ni at the bottom.",
    "Generated by tools/maps/make_kapyong_field.mjs: edit that file and re-run it rather than this one.",
    "The hill, spurs, river, road and hamlet are drawn by hand to the shape the accounts give, not",
    "traced from any map; the deployment is the night attack, in our own words, with round numbers",
    "for play. A dark night; the river is shallow and fordable (marsh).",
    "",
    "What happened, briefly: the ROK 6th Division broke on 22 April and streamed back down the",
    "valley. That night and the next the Chinese came after it. From 21:30 on the 23rd they struck",
    "the tanks' outpost and B Company in the valley and climbed the spurs at A and D Companies on",
    "the hill, attacking all night; the Australians held, and the next afternoon fell back through",
    "the Middlesex, the tanks covering them. 3 RAR lost 32 killed and 59 wounded; the Chinese far",
    "more.",
  ],
});
