// Builds data/fields/redan-1855.yaml: the British assault on the Great Redan at Sevastopol,
// 8 September 1855, on the field map at 10 m a hex. Run from this folder after editing:
// node make_redan_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours: the Redan was a V-shaped earthwork with its
// point (the salient) toward the British trenches, a deep ditch (15 to 20 feet) and a parapet
// along its two faces, joined to the Russian line on either side and open at the back (the
// gorge), with breastworks and traverses inside. The British advanced trench was about 200
// yards from the salient; the abatis in front had been mostly smashed by the bombardment. The
// work, its ditch, the line either side, the trench, the ravines and the shell holes are drawn
// by hand to that, not traced from any map, and are approximate. The deployment is just after
// noon, when the stormers went over, in our own words; numbers are round figures for play.
// The Russian infantry are on smoothbore muskets (most of them still were), their riflemen on
// rifles; the British on the rifle-musket. The siege guns on both sides are not on the map.
import { N, S, wobble, speckle, patch, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 100, ROWS = 80;                 // 1000 m east to west, about 690 m north to south
const ROW_M = Math.sqrt(3) / 2;              // a row is this many hexes deep (pointy-top hexes)
const TIP = [50, 46];                        // the salient (col, row)
const SPAN = 12;                             // the faces run this many hexes either side of the salient ...
const SLOPE = 1.15;                          // ... rising one row-height for every this many hexes across
const tipX = TIP[0] + (TIP[1] & 1) / 2, tipY = TIP[1] * ROW_M;
const curtainY = c => tipY - SPAN / SLOPE + 0.25 * wobble(c / 4, 0.7, 1.9);
// The Russian line's front: the Redan's two faces, and the line either side of it.
function lineY(x){
  const dx = Math.abs(x - tipX);
  return dx <= SPAN ? tipY - dx / SLOPE : curtainY(x);
}
const centre = (c, r) => [c + (r & 1) / 2, r * ROW_M];
const behind = (c, r) => { const [x, y] = centre(c, r); return y < lineY(x) };   // inside the Russian line

const TRENCH_ROW = 67;                       // the British advanced trench, about 200 yards from the salient
function kind(c, r){
  if (r < 15 && patch(c, r, { cx: 50, cy: 2, rx: 46, ry: 14, a: 0.9, b: 2.3 })) return speckle(c, r, 3) ? "T" : "x";   // the Karabelnaya, shelled to ruins
  if (r > 34 && c < 7 + wobble(r / 3, 1.3, 0.4)) return "r";                // the ravine on the west
  if (r > 34 && c > 92 + wobble(r / 3, 0.2, 1.6)) return "r";               // the ravine on the east
  if (!behind(c, r) && r < TRENCH_ROW && speckle(c, r, 14)) return "r";    // shell holes in front of the works
  return ".";
}
const grid = groundGrid(COLS, ROWS, kind);

// Neighbours of a hex (odd rows shifted half a hex east).
function neighbours(c, r){
  const o = r & 1;
  return [[c - 1, r], [c + 1, r], [c - 1 + o, r - 1], [c + o, r - 1], [c - 1 + o, r + 1], [c + o, r + 1]]
    .filter(([q, s]) => q >= 0 && q < COLS && s >= 0 && s < ROWS);
}

// The ditch and parapet: every side between a hex behind the line and one in front of it, the
// inner hex first.
const ditch = [], bank = [];
for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++){
  if (!behind(c, r)) continue;
  for (const n of neighbours(c, r)) if (!behind(...n)){ ditch.push([[c, r], n]); bank.push([[c, r], n]) }
}
// The breastwork across the Redan's back, the Russians behind it (north) on its inner side.
const BREAST = 24;
for (let c = 36; c <= 64; c++){
  for (const n of neighbours(c, BREAST)) if (n[1] === BREAST + 1) bank.push([[c, BREAST], n]);
}
// What is left of the abatis: a scatter two or three rows out from the Redan's faces.
const abatis = [];
for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++){
  const [x] = centre(c, r);
  if (behind(c, r) || Math.abs(x - tipX) > SPAN + 2) continue;
  if (behind(c, r - 3) && !behind(c, r - 1) && speckle(c, r, 3)) abatis.push([c, r]);
}
// The British advanced trench, and the zig-zag back from it.
const trench = [];
for (let c = 26; c <= 78; c++) trench.push([c, TRENCH_ROW + Math.round(0.4 * wobble(c / 5, 2.2, 0.5))]);
for (let r = TRENCH_ROW + 2; r < ROWS; r++){ const k = (r - TRENCH_ROW) % 6; trench.push([52 + (k < 3 ? k : 6 - k), r]) }

// ---------- the armies (pos is the middle of the front row) ----------
const BRITISH = { side: 0, facing: N }, RUSSIANS = { side: 1, facing: S };
const RIFLE = { quality: "regular", weapon: "rifle_musket", kit: "none", formation: "close", mounted: false };
const MUSKET = { quality: "regular", weapon: "musket_smoothbore", kit: "none", formation: "close", mounted: false };
const GUNS = { quality: "regular", weapon: "artillery_smoothbore", kit: "none", formation: "battery", mounted: false };
const units = [
  unit("Covering party (2nd Rifle Brigade and the Buffs)", BRITISH, 200, { ...RIFLE, formation: "open" }, [20, 40, 63]),
  unit("Ladder party (the Buffs and the 97th)", BRITISH, 320, RIFLE, [10, 45, 65]),
  unit("Light Division stormers (90th and 97th)", BRITISH, 1000, RIFLE, [20, 28, 68]),
  unit("2nd Division stormers (the Buffs, 41st and 62nd)", BRITISH, 760, { ...RIFLE, quality: "green" }, [16, 56, 68]),
  unit("Supports (7th, 23rd, 33rd, 34th and 77th)", BRITISH, 1500, { ...RIFLE, quality: "green" }, [30, 35, 74]),
  unit("Vladimirski Regiment, at the salient", RUSSIANS, 500, MUSKET, [12, 44, 38]),
  unit("Guns on the left face", RUSSIANS, 40, GUNS, [3, 40, 33]),
  unit("Guns on the right face", RUSSIANS, 40, GUNS, [3, 58, 33]),
  unit("Vladimirski Regiment, behind the breastwork", RUSSIANS, 1300, MUSKET, [26, 37, 23]),
  unit("Riflemen on the line to the west", RUSSIANS, 300, { ...MUSKET, weapon: "rifle_musket", formation: "open" }, [20, 12, 33]),
  unit("Kamchatski and Iakutski regiments (reserve)", RUSSIANS, 2000, MUSKET, [40, 30, 12]),
];

writeField({
  objective: { at: [50, 40], side: 0, name: "the Redan's salient", radius: 6 },
  id: "redan-1855", name: "The Great Redan, 8 September 1855", sides: ["British", "Russians"], table: "crimea-1854-56-all-hits",
  travel: { map: "sevastopol-1855", place: "The Great Redan", within: 1, sides: ["Allies", "Russia"] },
  weather: "{cond: fair, wind: strong, dir: N, ground: {mud: 0, snow: 0}}",
  grid, units, hexWorks: { abatis, trench }, edgeWorks: { ditch, bank },
  header: [
    `The British assault on the Great Redan, Sevastopol, 8 September 1855, at 10 m a hex: ${COLS} x ${ROWS}`,
    "hexes, about 1000 m east to west and 690 m north to south, north at the top: the Redan's point",
    "toward the British trench at the bottom, the Karabelnaya suburb behind it at the top.",
    "Generated by tools/maps/make_redan_field.mjs: edit that file and re-run it rather than this one.",
    "The work, its ditch, the line either side, the breastwork, the trench, the ravines and the",
    "shell holes are drawn by hand to the shape the accounts give, not traced from any map; the",
    "deployment is just after noon, in our own words, with round numbers for play.",
    "",
    "What happened, briefly: after three days' bombardment the French stormed the Malakhov, east",
    "of the Redan, at noon and held it. On their signal the British went over from the advanced",
    "trench, about 200 yards out: a covering party of riflemen, the ladder party, then the",
    "stormers of the Light and 2nd Divisions. Many fell crossing the open ground; the ladders were",
    "too few and some too short, but men got down into the ditch and up onto the salient. There",
    "they stopped and fired from the parapet instead of pressing on, while the Russians fired back",
    "from behind their breastwork and traverses and their reserves came up. The supports came",
    "forward piecemeal and crowded into the salient. After about an hour and a half a Russian",
    "counter-attack drove them back over the parapet and the ditch. That night the Russians blew",
    "up their works and left the south side of the town. It was a cold day, with a strong wind",
    "and dust.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
