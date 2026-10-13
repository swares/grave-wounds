// Builds data/fields/dakto-1967.yaml: Hill 875 near Dak To on 19 November 1967, on the field map at
// 10 m a hex. Run from this folder after editing: node make_dakto_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's accounts of the
// battle as summarised publicly. On the morning of 19 November the 2nd Battalion, 503rd Infantry,
// about 300 men, went up the north slope of Hill 875 through bamboo and jungle; the North
// Vietnamese 174th Regiment, dug in on the crest in bunkers and trenches joined by tunnels, stopped
// them below the top and closed in behind them, so that the battalion was ringed on the slope;
// air strikes and artillery hit the hill all day, and that evening a stray bomb fell among the
// paratroopers; the 4th Battalion came up the next day, and the crest was taken on 23 November.
// The hill, the slopes, the bunkers and the trenches are drawn by hand to that shape, not traced
// from any map, and are approximate; the deployment is the attack going up, in our own words, with
// round numbers for play.
import { N, S, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 120, ROWS = 140;                 // 1200 m east to west, about 1210 m north to south
const TOP = [60, 74];
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
function kind(c, r){
  const d = hdist([c, r], TOP);
  if (d <= 8) return speckle(c, r, 3) ? "r" : "h";                                                      // the crest: blasted bare
  if (patch(c, r, { cx: TOP[0], cy: TOP[1] - 8, rx: 22, ry: 16, a: 0.7, b: 1.6 })) return speckle(c, r, 3) ? "r" : "F";   // the north slope: shattered bamboo and fallen trees
  if (d <= 30) return speckle(c, r, 4) ? "h" : "F";                                                      // the hill's flanks under jungle
  return speckle(c, r, 6) ? "r" : "F";                                                                   // jungle and bamboo
}
const grid = groundGrid(COLS, ROWS, kind);
const BUNKERS = [...ring(TOP, 4).filter((_, i) => i % 3 === 0), ...ring(TOP, 10).filter((_, i) => i % 6 === 0)];
const trenchHexes = [...ring(TOP, 7), ...ring(TOP, 12)].filter(h => !BUNKERS.some(b => b[0] === h[0] && b[1] === h[1]));

const US = { side: 0, facing: S }, NV = { side: 1, facing: N };
const SKY = { quality: "veteran", weapon: "rifle_assault", kit: "vietnam_army", formation: "extended", mounted: false };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "vietnam_army", formation: "mg", mounted: false };
const PAVN = { quality: "veteran", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, prone: true };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("C Company, 2/503 Infantry (up the slope)", US, 100, SKY, 12, [TOP[0] - 6, TOP[1] - 26], S),
  at("D Company, 2/503 Infantry (up the slope)", US, 100, SKY, 12, [TOP[0] + 8, TOP[1] - 26], S),
  at("A Company, 2/503 Infantry (cutting the landing zone behind)", US, 90, SKY, 12, [TOP[0], TOP[1] - 46], S),
  at("2/503's machine guns", US, 10, MG, 2, [TOP[0], TOP[1] - 30], S),
  at("174th Regiment on the crest", NV, 250, PAVN, 14, [TOP[0], TOP[1] - 6], N),
  at("174th Regiment in the lower trenches", NV, 150, PAVN, 14, [TOP[0] + 2, TOP[1] - 12], N),
  at("North Vietnamese company behind them (from the west)", NV, 120, { ...PAVN, prone: false }, 12, [16, TOP[1] - 46], 0),
  at("North Vietnamese machine guns", NV, 10, { ...MG, kit: "none", prone: true }, 2, [TOP[0] - 14, TOP[1] - 4], N),
];

writeField({
  objective: { at: TOP, side: 0, name: "the crest of Hill 875", radius: 4 },
  id: "dakto-1967", name: "Hill 875, Dak To, 19 November 1967", sides: ["United States and ARVN", "North Vietnamese"], table: "vietnam-1965-70-hospitalized",
  travel: { map: "dakto-1967", place: "Hill 875", within: 1, sides: ["United States and ARVN", "North Vietnamese"] },
  weather: "{cond: fair, wind: calm, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { trench: trenchHexes, bunker: BUNKERS },
  support: [
    { name: "105 mm and 155 mm howitzers (the fire bases)", side: 0, kind: "howitzer", tubes: 12 },
    { name: "Fighter-bombers", side: 0, kind: "fighter_bomber", tubes: 8 },
    { name: "2/503's 81 mm mortars", side: 0, kind: "mortar", tubes: 4 },
    { name: "North Vietnamese 82 mm mortars", side: 1, kind: "mortar", tubes: 8 },
  ],
  header: [
    `Hill 875 near Dak To on 19 November 1967, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1200 m east to west and 1210 m north`,
    "to south, north at the top: the crest below the middle, ringed with bunkers and trenches, the",
    "north slope above it shattered bamboo and fallen trees, jungle all round.",
    "Generated by tools/maps/make_dakto_field.mjs: edit that file and re-run it rather than this one.",
    "The hill, the slopes, the bunkers and the trenches are drawn by hand to the shape the accounts",
    "give, not traced from any map; the deployment is the attack going up, in our own words, with",
    "round numbers for play. Fair and dry: the dry season had begun.",
    "",
    "What happened, briefly: on 19 November 1967 the 2nd Battalion, 503rd Infantry went up the north",
    "slope of Hill 875 and was stopped below the crest by the 174th Regiment's bunkers, while North",
    "Vietnamese came in behind it and overran the landing zone; that evening a stray bomb fell among",
    "the paratroopers. The 4th Battalion reached them the next night, and on 23 November, after days",
    "of air strikes, the two battalions took the crest.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
