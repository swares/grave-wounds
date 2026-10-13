// Builds data/fields/osan-1950.yaml: Task Force Smith's position north of Osan, 5 July 1950, on
// the field map at 10 m a hex. Run from this folder after editing: node make_osan_field.mjs
// (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's account of
// the battle (Appleman, South to the Naktong, and the Army's extract of it). Two short rifle
// companies of the 1st Battalion, 21st Infantry held a line of hills crossing the highway at
// right angles, B Company at the saddle where the road goes over, one of its platoons on a
// hillock west of the road, C Company along the ridge to the east with its right bent back
// along a finger ridge beside the railroad, about a mile east of the road. Recoilless rifles and
// bazookas were by the road; the 4.2-inch and 60 mm mortars behind the crest; five 105 mm
// howitzers about 2,000 yards back and one 1,000 yards back, off this map. After the tanks had
// gone through, the infantry of the North Korean 4th Division came down the road from Suwon, in
// trucks and on foot, deployed across the paddies and worked round both flanks. The ridge, the
// saddle, the paddies and the line are drawn by hand to that shape, not traced from any map,
// and are approximate; the deployment is the infantry attack near noon, in our own words, with
// round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 220, ROWS = 110;                 // 2200 m east to west, about 950 m north to south
const ROAD = 40, RAIL = 190;                  // the highway and the railroad, running north to south
const road = r => ROAD + Math.round(wobble(r / 4, 0.4, 1.6) * 0.6), rail = r => RAIL + Math.round(wobble(r / 5, 2.2, 0.3) * 0.5);
const crest = c => 46 + wobble(c / 6, 1.3, 0.7) * 1.1;                 // the hill line's crest, west to east
const saddle = c => Math.abs(c - ROAD) <= 7;
function ridge(c, r){
  const k = crest(c), off = r - k;
  if (saddle(c)) return Math.abs(off) <= 3 ? "." : null;                 // the road's way over: lower and open
  if (patch(c, r, { cx: 18, cy: 49, rx: 7, ry: 5, a: 0.6, b: 1.9 })) return "h";   // the hillock west of the road
  if (c >= RAIL - 14 && c <= RAIL - 6 && r > k && r < k + 28) return "h";  // the finger ridge by the railroad, running south
  if (off >= -5 && off <= 4) return speckle(c, r, 9) ? "F" : "h";          // the crest: bare, with scrub pine
  if (off > -10 && off < -5) return "r";                                  // the steep forward slope
  return null;
}
function kind(c, r){
  if (Math.abs(c - road(r)) <= 1) return ".";                             // the highway
  if (Math.abs(c - rail(r)) <= 1) return ".";                             // the railroad embankment
  const top = ridge(c, r);
  if (top) return top;
  if (r < crest(c) - 10) return speckle(c, r, 5) ? "." : "m";             // rice paddies to the north, with their dikes
  if (r > crest(c) + 4 && r < crest(c) + 16) return speckle(c, r, 13) ? "F" : ".";   // the back slope
  return speckle(c, r, 5) ? "." : "m";                                    // paddies behind the hills
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const UN = { side: 0, facing: N }, NK = { side: 1, facing: S };
const RIFLES = { quality: "green", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };   // in their foxholes
const MG = { quality: "regular", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false, prone: true };
const KPA = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false };
const row = c => Math.round(crest(c)) - 3;
const units = [
  unit("B Company, 21st Infantry (the saddle and east of it)", UN, 140, RIFLES, [47, ROAD + 3, row(ROAD + 26)]),
  unit("B Company platoon (the hillock west of the road)", UN, 35, RIFLES, [12, 12, 45]),
  unit("Recoilless rifle and bazooka teams (by the road)", UN, 25, { ...RIFLES, quality: "regular" }, [9, ROAD - 4, row(ROAD) + 4]),
  unit("Battalion machine guns", UN, 10, MG, [2, ROAD + 20, row(ROAD + 20) + 2]),
  unit("C Company, 21st Infantry (the ridge east)", UN, 120, RIFLES, [40, 110, row(130)]),
  unit("C Company's right (bent back by the railroad)", UN, 30, RIFLES, [10, RAIL - 15, row(RAIL - 10) + 10]),
  unit("16th Regiment, leading battalion (across the paddies)", NK, 1000, KPA, [90, 20, 18]),
  unit("16th Regiment, battalion working round the west", NK, 600, KPA, [40, 0, 30]),
  unit("18th Regiment, column on the highway", NK, 1500, { ...KPA, formation: "close" }, [6, ROAD - 3, 10]),
  unit("18th Regiment, battalion moving down the railroad", NK, 600, KPA, [44, 160, 20]),
  unit("4th Division machine guns", NK, 15, { ...MG, kit: "none", quality: "veteran", prone: false }, [3, 60, 22]),
];

writeField({
  objective: { at: [ROAD, Math.round(crest(ROAD))], side: 1, name: "the saddle where the road crosses the ridge", radius: 6 },
  id: "osan-1950", name: "Task Force Smith at Osan, 5 July 1950", sides: ["United Nations", "North Koreans"], table: "korea-1950-53-hospitalized",
  travel: { map: "osan-1950", place: "The saddle north of Osan (Jukmiryeong)", within: 2, sides: ["United Nations", "North Koreans"] },
  weather: "{cond: overcast, wind: calm, dir: S, ground: {mud: 1, snow: 0}}",
  grid, units,
  support: [
    { name: "105 mm howitzers (52nd Field Artillery)", side: 0, kind: "field", tubes: 6 },
    { name: "4.2-inch mortars", side: 0, kind: "mortar", tubes: 2 },
    { name: "60 mm mortars", side: 0, kind: "mortar", tubes: 4 },
    { name: "T-34 tanks (107th Tank Regiment)", side: 1, kind: "tank", tubes: 8 },
    { name: "North Korean mortars", side: 1, kind: "mortar", tubes: 6 },
  ],
  header: [
    `Task Force Smith's position north of Osan, 5 July 1950, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 2200 m east to`,
    "west and 950 m north to south, north at the top: the hill line across the middle, the",
    "highway over it at the saddle on the left, the railroad on the right, rice paddies before",
    "and behind.",
    "Generated by tools/maps/make_osan_field.mjs: edit that file and re-run it rather than this one.",
    "The hills, the saddle, the paddies and the line are drawn by hand to the shape the accounts",
    "give, not traced from any map; the deployment is the infantry attack near noon, in our own",
    "words, with round numbers for play. A wet morning after rain; the paddies are deep in water.",
    "There are no vehicle rules: the T-34s are on call as tanks firing over open sights (Fire",
    "support), and the Americans' recoilless rifles and bazookas fight as riflemen. Their foxholes",
    "are men gone to ground: they start that way. Most of the force were young soldiers new to",
    "battle (green).",
    "",
    "What happened, briefly: the North Korean tanks came down the road from Suwon at about eight",
    "in the morning and drove through the saddle under fire; a few were stopped, the rest went on",
    "south, cutting the telephone wire to the guns. Near noon the infantry followed, about 5,000",
    "men, came on across the paddies under the mortars and howitzers, and worked round both",
    "flanks. At half past two Smith ordered the withdrawal; most of the losses came as the",
    "companies fell back across the open ground. About 150 of the infantry and 31 of the gunners",
    "were killed, wounded or missing. The North Koreans' losses are put at about 130.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
