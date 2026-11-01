// Builds data/fields/burgos-1812.yaml: the storm of the hornwork of San Miguel at Burgos, on the
// night of 19-20 September 1812, on the field map at 10 m a hex. Run from this folder after
// editing: node make_burgos_field.mjs (no packages needed).
//
// Sources (project doc "burgos-research"): Oman, A History of the Peninsular War, vol. 6 (1922),
// ch. II. The hornwork stood on a hill about 300 yards from the castle, across a ravine, and the
// castle's guns commanded it. Its front was an earthwork 25 feet high, "covered by a counterscarp
// of 10 feet deep", steep and slippery, with a demi-bastion either side; the flanks were weaker,
// and the rear (the gorge) "was only closed by a row of palisades, erected within the last two
// days", 7 feet high. In it were seven field-pieces, 4- and 6-pounders, and a battalion of the
// 34th, 500 strong. The plan: a firing party of 300 of the 1/42nd to keep down the garrison's
// fire, two columns of Pack's Portuguese with Highland ladder parties at the two demi-bastions,
// and the flank companies of Stirling's brigade (1/42nd, 1/24th, 1/79th) in a false attack on the
// gorge, to be made real if it was weakly held. It was bright moonlight: the firing party was seen
// as it came over the crest, fired from about 150 yards and lost half its men. The ladders at the
// demi-bastions "were found somewhat short", and Pack's men fell back. Major Somers Cocks's 140
// light-company men ran up the back slope under the castle's fire, broke through the palisade
// "partly by using axes, partly by main force and climbing", and the 34th ran for the postern
// and got away to the castle, leaving its guns. Losses: the assailants 421 killed and wounded
// (204 of the 1/42nd, 113 Portuguese), the garrison 198 with 60 prisoners.
// The drawing is schematic and ours: the hornwork as a front with a demi-bastion at each end, two
// flanks and a gorge, on a hill, the castle's corner across the ravine; no plan was traced. The
// escarp is drawn as wall edges (no axe opens it: men go up it with ladders or not at all), with
// a ditch in front of it (not deep: 10 feet); the gorge is a palisade with the postern (a gate) in
// it. The Portuguese columns' strengths are ours (no source reached gives them), with round numbers.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 80, ROWS = 66;                    // 800 m east to west, about 570 m north to south
const FRONT = 24, GORGE = 37, W = 34, E = 56;  // the hornwork's front row, its gorge row and its flanks' columns
const bastion = (c, r) => r >= FRONT - 4 && r < FRONT && ((c >= W - 3 && c <= W + 4) || (c >= E - 4 && c <= E + 3));   // the demi-bastions, out from the front's two ends
const inside = (c, r) => (c >= W && c <= E && r >= FRONT && r <= GORGE) || bastion(c, r);
const castle = (c, r) => r >= 56 && c <= 24 - (ROWS - 1 - r);                // the corner of the castle's outer works, south-west, about 300 yards from the gorge
const ravine = (c, r) => c >= 8 && c <= 46 && Math.abs((r - 49) - (c - 28) * 0.75 + wobble(c / 5, 0.6, 1.3) * 0.5) <= 1.5 && !castle(c, r);   // the ravine between the hill and the castle
const hill = (c, r) => patch(c, r, { cx: 45, cy: 31, rx: 22, ry: 17, a: 0.8, b: 2.1 });

function kind(c, r){
  if (castle(c, r)) return "h";                  // the castle hill, the higher of the two
  if (inside(c, r)) return "h";                  // the hornwork's terreplein, on the hilltop
  if (ravine(c, r)) return "r";
  if (hill(c, r)) return "s";                     // the hill's slopes, open
  return speckle(c, r, 11) ? "r" : ".";
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- works ----------
// The escarp (wall edges) on every side between the hornwork and the ground outside but the gorge,
// with the ditch outside it; the palisade across the gorge, the postern in its middle.
const neighbours = (c, r) => {                   // odd rows shifted half a hex east
  const o = r & 1;
  return [[c - 1, r], [c + 1, r], [c - 1 + o, r - 1], [c + o, r - 1], [c - 1 + o, r + 1], [c + o, r + 1]]
    .filter(([q, s]) => q >= 0 && q < COLS && s >= 0 && s < ROWS);
};
const wall = [], ditch = [], palisade = [], gate = [];
const POSTERN = [45, 46];                        // the postern's columns on the gorge row
for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++){
  if (!inside(c, r)) continue;
  for (const o of neighbours(c, r)){
    if (inside(...o)) continue;
    const side = [[c, r], o];
    if (r === GORGE && o[1] > r){
      (POSTERN.includes(c) ? gate : palisade).push(side);
      continue;
    }
    wall.push(side);
    ditch.push(side);
  }
}

// ---------- the armies (pos is the middle of the front row) ----------
const AL = { side: 0, facing: S }, FR = { side: 1, facing: N };
const LINE = { quality: "regular", weapon: "musket_smoothbore", kit: "none", formation: "close", mounted: false };
const GUNS = { quality: "regular", weapon: "artillery_smoothbore", kit: "none", formation: "battery", mounted: false };   // ten crew to a gun
const WEST = [[36, 18]], EAST = [[54, 18]];      // the two Portuguese columns, to the foot of each demi-bastion
const GORGE_ROUTE = [[66, 22], [66, 42], [50, 42], [46, 33]];   // the light companies: round the east flank, up the back slope, over the palisade and in
const units = [
  unit("Guns in San Miguel (seven 4- and 6-pounders)", FR, 70, { ...GUNS, emplaced: true }, [4, 43, FRONT]),   // emplaced: in their embrasures, they stay put
  // the battalion on the parapet either side of the guns
  unit("1st battalion, 34th Line (west half)", FR, 250, LINE, [6, 36, FRONT]),
  unit("1st battalion, 34th Line (east half)", FR, 250, LINE, [6, 49, FRONT]),
  unit("Guns on the castle", FR, 60, { ...GUNS, emplaced: true }, [3, 10, 58]),
  unit("1/42nd, the firing party", AL, 300, LINE, [8, 41, 7]),
  unit("Pack's Portuguese, west column (short ladders)", AL, 400, { ...LINE, ladders: "short", via: WEST }, [5, 33, 6]),
  unit("Pack's Portuguese, east column (short ladders)", AL, 400, { ...LINE, ladders: "short", via: EAST }, [5, 53, 6]),
  unit("Light companies of the 1/42nd, 1/24th and 1/79th (Cocks)", AL, 140, { ...LINE, quality: "veteran", formation: "open", ladders: true, via: GORGE_ROUTE }, [4, 66, 10]),
];

writeField({
  phases: [   // an exchange is about a minute; the times are ours
    { name: "The storm", at: 1, note: "Night, in bright moonlight: the firing party comes over the crest and is seen at once; the Portuguese columns go for the demi-bastions, the light companies round to the gorge." },
  ],
  ends: { at: 60, why: "about an hour: the firing party stood about a quarter of an hour, and the hornwork was carried the same night (our reading)" },
  objective: { at: [45, 31], side: 0, name: "the hornwork of San Miguel", radius: 6 },
  id: "burgos-1812", name: "Burgos, 19-20 September 1812 (the hornwork of San Miguel)", sides: ["Allies", "French"], table: "peninsular-1808-14-all-hits",
  weather: "{cond: fair, wind: calm, light: moonlit, ground: {mud: 0, snow: 0}}",
  grid, units,
  edgeWorks: { wall, ditch, palisade, gate },
  header: [
    `The storm of the hornwork of San Miguel, Burgos, on the night of 19-20 September 1812, at 10 m a hex: ${COLS} x ${ROWS}`,
    "hexes, 800 m east to west and about 570 m north to south, north at the top: the hornwork on its hill,",
    "its front and demi-bastions to the north, its gorge to the south; the ravine and the corner of the",
    "castle's works to the south-west.",
    "Generated by tools/maps/make_burgos_field.mjs: edit that file and re-run it rather than this one.",
    "Schematic, drawn by hand to Oman's account (project doc burgos-research), not traced from a plan.",
    "The escarp, 25 feet of earth, is drawn as wall edges with a ditch (10 feet, not deep) before it;",
    "the gorge is a palisade with the postern in it. The Portuguese ladders are short (ladders: short):",
    "they do not reach the top of the escarp. The Portuguese columns' strengths are ours.",
    "",
    "What happened, briefly: on the first night of the siege Wellington had the outlying hornwork",
    "stormed without a bombardment. In bright moonlight the firing party of the 42nd was seen as it",
    "came over the crest, stood firing from about 150 yards and lost half its men; Pack's Portuguese",
    "reached the demi-bastions, found their ladders short, and fell back. Meanwhile Major Somers",
    "Cocks took the light companies round to the gorge, under the castle's guns, and broke through the",
    "palisade; the battalion of the 34th ran for the postern and got away to the castle, leaving its",
    "seven guns. The Allies lost 421 killed and wounded, the French 198 with 60 prisoners. The castle",
    "itself held out, and after five weeks Wellington gave up the siege.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
