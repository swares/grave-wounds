// Builds data/fields/wanat-2008.yaml: Vehicle Patrol Base Kahler and Observation Post Topside at
// Wanat, at dawn on 13 July 2008, on the field map at 10 m a hex. Run from this folder after
// editing: node make_wanat_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's accounts (the
// Combat Studies Institute's study of the battle, and the Army's account for the Medal of Honor
// to Staff Sergeant Ryan Pitts, works of the US government). The patrol base was an open field
// about 300 m long and 100 m wide at the edge of the village, buildings on two sides, its
// barriers built only chest-high and in places only loose wire, with the 120 mm mortar's pit and
// a TOW Humvee; the observation post, nine men among rocks under a tree on a ridge 50-70 m east
// of it, overlooked the valley, with a brush-filled draw just beyond its north side and a
// two-storey building north of it; the village stood on higher ground, with the bazaar, a hotel
// and the mosque overlooking the perimeter; the fighters were first seen on the high ground to
// the west, and came from the draw, the buildings north of the post and in the village, and the
// high ground and farmland. The fields, terraces, houses and slopes are drawn by hand to that
// shape, not traced from any map or photograph, and are approximate; the deployment is about
// 04:20, in our own words, with round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 90, ROWS = 70;                   // 900 m east to west, about 600 m north to south
const VPB = { c0: 34, c1: 44, r0: 26, r1: 60 };   // the patrol base: an open field about 100 m by 300 m, north to south
const OP = [52, 30];                          // Observation Post Topside, on the ridge 50-70 m east of the base
const RIVER = r => 14 + Math.round(wobble(r / 7, 0.8, 1.6) * 0.8);       // the Waygal river, west of the village
const DRAW = c => 22 - Math.round((c - 46) * 0.45 + wobble(c / 4, 0.2, 1.1) * 0.6);   // the brush-filled draw, down from the north-east past the post's north side
function works(c, r){                        // the base, the post and the draw, or null
  if (c >= VPB.c0 && c <= VPB.c1 && r >= VPB.r0 && r <= VPB.r1) return speckle(c, r, 9) ? "r" : ".";   // the base: open, with vehicles and HESCO here and there
  if (patch(c, r, { cx: OP[0], cy: OP[1], rx: 4, ry: 3, a: 0.3, b: 1.1 })) return speckle(c, r, 2) ? "r" : "h";   // the post: rocks on the ridge
  if (c >= 44 && c <= 70 && Math.abs(r - DRAW(c)) <= 1) return "o";      // the draw: brush (scrub), cover that thins sight
  return null;
}
function built(c, r){                         // the buildings north of the post, the bazaar and hotel, the mosque and the village, or null
  if (patch(c, r, { cx: 54, cy: 16, rx: 2, ry: 2 })) return "B";         // the two-storey building north of the post
  if (patch(c, r, { cx: 38, cy: 15, rx: 9, ry: 7, a: 1.4, b: 0.5 })) return speckle(c, r, 5) ? "." : "T";   // the bazaar and the hotel
  if (patch(c, r, { cx: 27, cy: 30, rx: 2, ry: 2 })) return "B";         // the mosque, over the base's west side
  if (c > 17 && c < 33 && r < 50) return speckle(c, r, 3) ? "r" : "T";    // the village on its terraces, above the base
  return null;
}
function land(c, r){                          // the high ground on both sides, and the terraced fields
  if (c <= 11) return speckle(c, r, 4) ? "F" : "h";                       // the high ground west of the river
  if (c >= 58) return speckle(c, r, 3) ? "F" : "h";                       // the ridge and slopes east
  return speckle(c, r, 4) ? "." : "r";                                     // terraced fields
}
const kind = (c, r) => (Math.abs(c - RIVER(r)) <= 1 ? "w" : null) ?? works(c, r) ?? built(c, r) ?? land(c, r);   // the river: crossed at the bridge
const grid = groundGrid(COLS, ROWS, kind);
for (let r = 44; r <= 46; r++) for (let c = 11; c <= 17; c++) grid[r][c] = ".";   // the bridge over the river and the track up to the base

// ---------- the armies (pos is the middle of the front row) ----------
const US = { side: 0, facing: N }, INS = { side: 1, facing: S };
const PARA = { quality: "veteran", weapon: "rifle_assault", kit: "interceptor", formation: "extended", mounted: false, prone: true };
const M240 = { quality: "veteran", weapon: "machine_gun", kit: "interceptor", formation: "mg", mounted: false, prone: true };
const ANA = { quality: "green", weapon: "rifle_assault", kit: "pasgt", formation: "extended", mounted: false, prone: true };
const FIGHTER = { quality: "regular", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, prone: true };   // in cover, firing from hiding
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("Observation Post Topside (paratroopers)", US, 6, PARA, 2, [OP[0], OP[1] - 1], N),
  at("Observation Post Topside (the M240 and its crew)", US, 3, M240, 1, [OP[0] + 2, OP[1]], 0),
  at("2nd Platoon at the base's north end", US, 15, PARA, 5, [39, VPB.r0 + 1], N),
  at("2nd Platoon on the base's east side, facing the post", US, 12, PARA, 4, [VPB.c1 - 1, 40], 0),
  at("Humvee guns (.50 cal, Mk 19) and the TOW", US, 6, { ...M240, prone: false }, 2, [37, 44], 3),
  at("Engineers and the mortar section", US, 10, { ...PARA, quality: "regular" }, 4, [39, 54], S),
  at("Afghan National Army platoon (the base's west side)", US, 24, ANA, 6, [VPB.c0 + 1, 40], 3),
  at("Fighters in the bazaar and the hotel", INS, 50, FIGHTER, 10, [38, 18], S),
  at("Fighters in the village and the mosque", INS, 40, FIGHTER, 8, [26, 34], 5),
  at("Fighters on the high ground west of the river", INS, 30, FIGHTER, 6, [6, 30], 0),
  at("Fighters in the draw north of the post", INS, 40, FIGHTER, 10, [56, DRAW(56) - 2], S),
  at("Fighters from the farmland and slopes east", INS, 60, FIGHTER, 10, [72, 36], 3),
  at("RPG teams", INS, 15, { ...FIGHTER, weapon: "rpg" }, 3, [46, 14], 4),
  at("PKM machine guns", INS, 10, { ...M240, kit: "none", quality: "regular" }, 2, [64, 18], 3),
];

writeField({
  objective: { at: OP, side: 1, name: "Observation Post Topside" },
  id: "wanat-2008", name: "Wanat: the patrol base and the observation post, 13 July 2008", sides: ["United States", "Insurgents"], table: "oif-oef-2001-wounds",
  travel: { map: "wanat-2008", place: "Wanat (Vehicle Patrol Base Kahler)", within: 1, sides: ["United States", "Insurgents"] },
  weather: "{cond: fair, wind: calm, light: dusk, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { wire: [[VPB.c0, VPB.r0 - 1], [VPB.c0 + 1, VPB.r0 - 1], [VPB.c1, VPB.r0 - 1], [VPB.c1 + 1, 34], [VPB.c1 + 1, 35], [VPB.c1 + 1, 48], [VPB.c1 + 1, 49]] },
  support: [
    { name: "120 mm mortar (the base's own)", side: 0, kind: "mortar", tubes: 1 },
    { name: "155 mm guns at Blessing", side: 0, kind: "howitzer", tubes: 2 },
    { name: "Apaches (AH-64)", side: 0, kind: "gunship", tubes: 2 },
    { name: "A-10, B-1B and F-15E (later in the morning)", side: 0, kind: "fighter_bomber", tubes: 3 },
  ],
  header: [
    `The patrol base and the observation post at Wanat at dawn on 13 July 2008, at 10 m a hex: ${COLS} x ${ROWS} hexes, about`,
    "900 m east to west and 600 m north to south, north at the top: the base (an open field about",
    "100 m by 300 m) right of the middle, Observation Post Topside on the ridge east of it, the",
    "brush-filled draw past the post's north side, the bazaar and hotel to the north, the village",
    "and its mosque on the terraces to the west, the Waygal river and the high ground beyond.",
    "Generated by tools/maps/make_wanat_field.mjs: edit that file and re-run it rather than this one.",
    "Light cover (scrub, key o): the brush in the draw, seen and shot through at a cost.",
    "The fields, terraces, houses and slopes are drawn by hand to the shape the accounts give, not",
    "traced from any map or photograph; the deployment is about 04:20, in our own words, with round",
    "numbers for play. First light (dusk or dawn). The base's barriers were chest-high at best and",
    "in places only loose wire: the paratroopers are dug in (gone to ground), the fighters firing",
    "from cover. The 120 mm mortar and the TOW were hit in the first minutes; the Apaches came",
    "about half an hour in, the jets later.",
    "",
    "What happened, briefly: at about 04:20 some 200 fighters opened fire from the village, the",
    "bazaar, the hotel, the mosque, the draw and the high ground, with RPGs and machine guns, on the",
    "base and above all on the post, where every man was wounded in the first volley. Men ran from",
    "the base up the terraces to hold it; nine Americans were killed, all but one of them at or",
    "going to the post, and 27 wounded. Guns from Blessing, Apaches and then jets drove the",
    "fighters off after about four hours. The base was given up a few days later.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
