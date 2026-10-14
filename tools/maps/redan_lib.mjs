// Shared drawing for the two Great Redan battlefields (make_redan_field.mjs, 8 September 1855;
// make_redan_june_field.mjs, 18 June 1855): the Redan, the Russian line either side, the
// breastwork across its gorge, the abatis, the British advanced trench and the ground between,
// at 10 m a hex. All drawn by hand to the shape the accounts give, not traced from any map, and
// approximate. The point of the salient is cut off square, a front of 12 hexes (120 m): a
// simplification for the field map, whose units stand in straight lines and could not otherwise
// reach the men in a sharp point.
import { N, S, wobble, speckle, patch, groundGrid } from "./field_lib.mjs";

export const COLS = 100;                      // 1000 m east to west
const ROW_M = Math.sqrt(3) / 2;              // a row is this many hexes deep (pointy-top hexes)
const TIP = [50, 46];                        // the salient (col, row)
const BLUNT = 5;                             // the salient's point is cut off square, this many hexes either side
const SPAN = 12;                             // the faces run this many hexes beyond it ...
const SLOPE = 1.15;                          // ... rising one row-height for every this many hexes across
const tipX = TIP[0] + (TIP[1] & 1) / 2, tipY = TIP[1] * ROW_M;
const curtainY = c => tipY - SPAN / SLOPE + 0.25 * wobble(c / 4, 0.7, 1.9);
// The Russian line's front: the Redan's two faces, and the line either side of it.
function lineY(x){
  const dx = Math.abs(x - tipX);
  if (dx <= BLUNT) return tipY;
  return dx <= BLUNT + SPAN ? tipY - (dx - BLUNT) / SLOPE : curtainY(x);
}
const centre = (c, r) => [c + (r & 1) / 2, r * ROW_M];
const behind = (c, r) => { const [x, y] = centre(c, r); return y < lineY(x) };   // inside the Russian line

// The armies' common kinds, and what both fields share in their files.
export const BRITISH = { side: 0, facing: N }, RUSSIANS = { side: 1, facing: S };
export const RIFLE = { quality: "regular", weapon: "rifle_musket", kit: "none", formation: "close", mounted: false };
export const MUSKET = { quality: "regular", weapon: "musket_smoothbore", kit: "none", formation: "close", mounted: false };
export const GUNS = { quality: "regular", weapon: "artillery_smoothbore", kit: "none", formation: "battery", mounted: false };
export const COMMON = {
  objective: { at: [50, 42], side: 0, name: "the Redan's salient", radius: 3 },
  sides: ["British", "Russians"], table: "crimea-1854-56-all-hits",
  travel: { map: "sevastopol-1855", place: "The Great Redan", within: 1, sides: ["Allies", "Russia"] },
};

const neighbours = (c, r, rows) => {          // odd rows shifted half a hex east
  const o = r & 1;
  return [[c - 1, r], [c + 1, r], [c - 1 + o, r - 1], [c + o, r - 1], [c - 1 + o, r + 1], [c + o, r + 1]]
    .filter(([q, s]) => q >= 0 && q < COLS && s >= 0 && s < rows);
};
// The ground: the ruined suburb, the ravines either side, and shell holes in front of the works.
const groundKind = (trenchRow, holes) => (c, r) => {
  if (r < 15 && patch(c, r, { cx: 50, cy: 2, rx: 46, ry: 14, a: 0.9, b: 2.3 })) return speckle(c, r, 3) ? "T" : "x";   // the Karabelnaya, shelled to ruins
  if (r > 34 && c < 7 + wobble(r / 3, 1.3, 0.4)) return "r";                // the ravine on the west
  if (r > 34 && c > 92 + wobble(r / 3, 0.2, 1.6)) return "r";               // the ravine on the east
  if (!behind(c, r) && r < trenchRow && speckle(c, r, holes)) return "r";  // shell holes in front of the works
  return ".";
};
// The ditch and parapet (every side between a hex behind the line and one in front of it, the
// inner hex first), and the breastwork across the Redan's back (the Russians north of it).
function parapet(rows){
  const ditch = [], bank = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < COLS; c++){
    if (!behind(c, r)) continue;
    for (const n of neighbours(c, r, rows)) if (!behind(...n)){ ditch.push([[c, r], n]); bank.push([[c, r], n]) }
  }
  const BREAST = 24;
  for (let c = 36; c <= 64; c++){
    for (const n of neighbours(c, BREAST, rows)) if (n[1] === BREAST + 1) bank.push([[c, BREAST], n]);
  }
  return { ditch, bank };
}
// The abatis in front of the Redan's faces: "scatter" (a hex in three, two or three rows out) or
// "whole" (a belt two rows deep).
function abatisBelt(rows, belt){
  const out = [];
  const lies = (c, r) => (belt === "whole" ? behind(c, r - 2) || behind(c, r - 3) : behind(c, r - 3) && speckle(c, r, 3));
  for (let r = 0; r < rows; r++) for (let c = 0; c < COLS; c++){
    const [x] = centre(c, r);
    if (!behind(c, r) && Math.abs(x - tipX) <= BLUNT + SPAN + 2 && !behind(c, r - 1) && lies(c, r)) out.push([c, r]);
  }
  return out;
}
// The British advanced trench, and the zig-zag back from it.
function trenchLine(rows, trenchRow){
  const out = [];
  for (let c = 26; c <= 78; c++) out.push([c, trenchRow + Math.round(0.4 * wobble(c / 5, 2.2, 0.5))]);
  for (let r = trenchRow + 2; r < rows; r++){ const k = (r - trenchRow) % 6; out.push([52 + (k < 3 ? k : 6 - k), r]) }
  return out;
}

// The field: rows (north to south), the British advanced trench's row, shell holes (about one hex
// in `holes` in front of the works) and the abatis ("scatter": what the bombardment left; "whole").
export function redan({ rows, trenchRow, holes, abatis: belt }){
  return {
    grid: groundGrid(COLS, rows, groundKind(trenchRow, holes)),
    hexWorks: { abatis: abatisBelt(rows, belt), trench: trenchLine(rows, trenchRow) },
    edgeWorks: parapet(rows),
  };
}
