// Builds data/fields/hamburger-1969.yaml: the summit of Dong Ap Bia (Hill 937), "Hamburger Hill",
// on 20 May 1969, on the field map at 10 m a hex. Run from this folder after editing:
// node make_hamburger_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's accounts of the
// battle as summarised publicly. After ten days of air strikes, napalm and shellfire had stripped
// the summit of its jungle, the 3rd Battalion, 187th Infantry went up from the north-west, the 1st
// Battalion, 506th Infantry from the south and the ARVN 2nd Battalion, 3rd Regiment from the
// east, on the morning of 20 May; the North Vietnamese 29th Regiment's survivors held tiers of
// bunkers on the slopes and the summit, and many slipped away west towards Laos; the summit was
// taken about noon. The hill, its spurs and the bunkers are drawn by hand to that shape, not traced
// from any map, and are approximate; the deployment is the last assault, in our own words, with
// round numbers for play.
import { N, S, wobble, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 140, ROWS = 140;                 // 1400 m east to west, about 1210 m north to south
const TOP = [70, 66];
const cube = ([c, r]) => { const q = c - (r - (r & 1)) / 2; return [q, r, -q - r] };
const hdist = (a, b) => { const x = cube(a), y = cube(b); return Math.max(Math.abs(x[0] - y[0]), Math.abs(x[1] - y[1]), Math.abs(x[2] - y[2])) };
function ring(h, d){                          // the hexes exactly d from h
  const out = [];
  for (let r = h[1] - d; r <= h[1] + d; r++){
    for (let c = h[0] - d - 1; c <= h[0] + d + 1; c++){
      if (hdist([c, r], h) === d) out.push([c, r]);
    }
  }
  return out;
}
function onSpur(c, r){                        // the spurs down to the north-west and the south
  if (r < TOP[1]) return Math.abs((c - TOP[0]) - (r - TOP[1]) * 0.6) <= 3 + wobble(r / 6, 0.5, 1.2);
  return Math.abs(c - TOP[0] - 2) <= 3;
}
function kind(c, r){
  const d = hdist([c, r], TOP);
  if (d <= 10) return speckle(c, r, 3) ? "r" : "h";                                                       // the summit: stripped to stumps and craters
  if (d <= 34 && onSpur(c, r)) return speckle(c, r, 3) ? "h" : "r";                                       // the spurs the attacks came up
  if (d <= 34) return speckle(c, r, 3) ? "F" : "r";                                                       // the slopes: blasted jungle and bamboo
  return speckle(c, r, 6) ? "r" : "F";                                                                     // jungle
}
const grid = groundGrid(COLS, ROWS, kind);
const BUNKERS = [6, 14, 22].flatMap(d => ring(TOP, d).filter((_, i) => i % (d / 2) === 0));

const US = { side: 0, facing: S }, NV = { side: 1, facing: N };
const SKY = { quality: "veteran", weapon: "rifle_assault", kit: "vietnam_army", formation: "extended", mounted: false };
const ARVN = { ...SKY, quality: "regular", kit: "none" };
const PAVN = { quality: "veteran", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, prone: true };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "mg", mounted: false, prone: true };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("3/187 Infantry (up the north-west spur)", US, 200, SKY, 14, [TOP[0] - 22, TOP[1] - 22], 5),
  at("1/506 Infantry (up the south spur)", US, 200, SKY, 14, [TOP[0] + 2, TOP[1] + 30], N),
  at("ARVN 2nd Battalion, 3rd Regiment (from the east)", US, 200, ARVN, 14, [TOP[0] + 32, TOP[1]], 3),
  at("29th Regiment on the summit", NV, 120, PAVN, 10, [TOP[0], TOP[1] - 2], 2),
  at("29th Regiment in the north-west bunkers", NV, 60, PAVN, 8, [TOP[0] - 10, TOP[1] - 10], 2),
  at("29th Regiment in the south bunkers", NV, 60, PAVN, 8, [TOP[0] + 2, TOP[1] + 14], 4),
  at("North Vietnamese machine guns", NV, 10, MG, 2, [TOP[0] + 8, TOP[1] - 6], 0),
];

writeField({
  objective: { at: TOP, side: 0, name: "the summit of Hill 937 (Hamburger Hill)" },
  id: "hamburger-1969", name: "Hamburger Hill (Dong Ap Bia), 20 May 1969", sides: ["United States and ARVN", "North Vietnamese"], table: "vietnam-1965-70-hospitalized",
  travel: { map: "hamburger-1969", place: "Dong Ap Bia (Hill 937)", within: 1, sides: ["United States and ARVN", "North Vietnamese"] },
  weather: "{cond: overcast, wind: calm, ground: {mud: 2, snow: 0}}",
  grid, units,
  hexWorks: { bunker: BUNKERS },
  support: [
    { name: "105 mm and 155 mm howitzers (the fire bases)", side: 0, kind: "howitzer", tubes: 18 },
    { name: "Fighter-bombers", side: 0, kind: "fighter_bomber", tubes: 12 },
    { name: "Battalion 81 mm mortars", side: 0, kind: "mortar", tubes: 8 },
    { name: "North Vietnamese mortars", side: 1, kind: "mortar", tubes: 6 },
  ],
  header: [
    `The summit of Dong Ap Bia (Hill 937) on 20 May 1969, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1400 m east to west and 1210 m`,
    "north to south, north at the top: the summit in the middle, stripped to stumps and craters,",
    "with tiers of bunkers down its slopes, the spurs running down to the north-west and the south,",
    "blasted jungle and bamboo below.",
    "Generated by tools/maps/make_hamburger_field.mjs: edit that file and re-run it rather than this one.",
    "The hill, its spurs and the bunkers are drawn by hand to the shape the accounts give, not traced",
    "from any map; the deployment is the last assault, in our own words, with round numbers for",
    "play. Overcast, the slopes mud after days of rain.",
    "",
    "What happened, briefly: on the morning of 20 May 1969, after ten days of attacks, the 3rd",
    "Battalion, 187th Infantry went up from the north-west, the 1st Battalion, 506th Infantry from",
    "the south and an ARVN battalion from the east. The North Vietnamese held their bunkers to the",
    "last or slipped away towards Laos, and the summit was taken about noon.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
