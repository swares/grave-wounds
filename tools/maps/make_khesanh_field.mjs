// Builds data/fields/khesanh-1968.yaml: Hill 861A above Khe Sanh before dawn on 5 February 1968,
// on the field map at 10 m a hex. Run from this folder after editing: node make_khesanh_field.mjs
// (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Marine Corps' history
// of the siege as summarised publicly. E Company, 2nd Battalion, 26th Marines, about 200 men, had
// dug in on Hill 861A, a knoll on the ridge north-east of Hill 861, inside trenches, bunkers and
// wire, the jungle cleared back for fields of fire; at about 04:00 on 5 February, in the fog and
// dark, after a heavy barrage, a North Vietnamese battalion of the 101D Regiment came through the
// wire on the north and got into the trenches; the Marines' reserve platoon counterattacked and
// threw them out hand to hand by dawn, while the guns at the base and on 881 South fired round the
// hill. The hill, the ridge, the trenches, bunkers and wire are drawn by hand to that shape, not
// traced from any map, and are approximate; the deployment is the attack, in our own words, with
// round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 140, ROWS = 120;                 // 1400 m east to west, about 1040 m north to south
const TOP = [72, 62];
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
const RIDGE = c => 62 + Math.round((TOP[0] - c) * 0.35 + wobble(c / 7, 0.4, 1.1));   // the ridge, running down to the south-west towards 861
function kind(c, r){
  if (patch(c, r, { cx: TOP[0], cy: TOP[1], rx: 14, ry: 11, a: 0.6, b: 1.3 })) return speckle(c, r, 3) ? "r" : "h";   // the knoll: bare, cratered
  if (Math.abs(r - RIDGE(c)) <= 4 && c < TOP[0]) return speckle(c, r, 4) ? "r" : "h";                   // the ridge towards 861
  if (hdist([c, r], TOP) <= 26) return speckle(c, r, 6) ? "o" : "r";                                     // the cleared slopes: elephant grass (scrub), stumps, craters
  return speckle(c, r, 5) ? "r" : "F";                                                                    // jungle
}
const grid = groundGrid(COLS, ROWS, kind);
const BUNKERS = [[TOP[0] - 8, TOP[1]], [TOP[0] + 8, TOP[1]], [TOP[0] - 4, TOP[1] - 7], [TOP[0] + 4, TOP[1] - 7], [TOP[0], TOP[1] + 8]];
const trenchHexes = ring(TOP, 8).filter(h => !BUNKERS.some(b => b[0] === h[0] && b[1] === h[1]));

const US = { side: 0, facing: N }, NV = { side: 1, facing: S };
// The Marines had a few Starlight scopes on the hill (nv: starlight); the North Vietnamese had none.
const MARINE = { quality: "regular", weapon: "rifle_assault", kit: "vietnam_usmc", formation: "extended", mounted: false, prone: true, nv: "starlight" };
const MG = { quality: "regular", weapon: "machine_gun", kit: "vietnam_usmc", formation: "mg", mounted: false, prone: true, nv: "starlight" };
const PAVN = { quality: "veteran", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, nv: "none" };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("E Company, 2/26 Marines (the north trenches)", US, 60, MARINE, 10, [TOP[0], TOP[1] - 8], N),
  at("E Company, 2/26 Marines (the west and east trenches)", US, 60, MARINE, 8, [TOP[0] - 8, TOP[1] + 2], 3),
  at("E Company's reserve platoon", US, 50, { ...MARINE, prone: false }, 8, [TOP[0] + 2, TOP[1] + 4], N),
  { ...at("E Company's machine guns", US, 10, MG, 2, [TOP[0] + 5, TOP[1] - 6], N), fixed: [TOP[0], 16] },   // laid by day through the north wire
  at("North Vietnamese battalion (through the north wire)", NV, 400, PAVN, 30, [TOP[0], 16], S),
  at("North Vietnamese company (from the north-west)", NV, 120, PAVN, 12, [24, 30], 5),
  at("North Vietnamese machine guns", NV, 10, { ...MG, kit: "none", quality: "veteran", nv: "none" }, 2, [TOP[0] + 20, 22], 4),
];

writeField({
  objective: { at: TOP, side: 1, name: "the top of Hill 861A", radius: 8 },
  id: "khesanh-1968", name: "Hill 861A, Khe Sanh, 5 February 1968", sides: ["United States and ARVN", "North Vietnamese"], table: "vietnam-1965-70-hospitalized",
  travel: { map: "khesanh-1968", place: "Hill 861A", within: 1, sides: ["United States and ARVN", "North Vietnamese"] },
  weather: "{cond: fog, wind: calm, light: night, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { trench: trenchHexes, bunker: BUNKERS, wire: ring(TOP, 13).filter((_, i) => i % 4 !== 0) },
  support: [
    { name: "Marine 105 mm and 155 mm howitzers (the base)", side: 0, kind: "howitzer", tubes: 18 },
    { name: "4.2-inch mortars (the base)", side: 0, kind: "mortar", tubes: 6 },
    { name: "Marine 105 mm howitzers on 881 South", side: 0, kind: "field", tubes: 3 },
    { name: "North Vietnamese 82 mm mortars", side: 1, kind: "mortar", tubes: 12 },
    { name: "North Vietnamese rockets and guns", side: 1, kind: "field", tubes: 8 },
  ],
  header: [
    `Hill 861A before dawn on 5 February 1968, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1400 m east to west and 1040 m`,
    "north to south, north at the top: the knoll in the middle, ringed with trenches, bunkers and",
    "wire, the ridge running down to the south-west towards Hill 861, the slopes cleared to elephant",
    "grass and craters, jungle beyond.",
    "Generated by tools/maps/make_khesanh_field.mjs: edit that file and re-run it rather than this one.",
    "Light cover (scrub, key o): the elephant grass on the cleared slopes, seen and shot through at a cost.",
    "The hill, the ridge, the trenches, bunkers and wire are drawn by hand to the shape the accounts",
    "give, not traced from any map; the deployment is the North Vietnamese attack, in our own words,",
    "with round numbers for play. Fog and a dark night: fire illumination and flares.",
    "",
    "What happened, briefly: at about 04:00 on 5 February 1968, after a heavy barrage, a North",
    "Vietnamese battalion came through the wire on the north of Hill 861A and into E Company's",
    "trenches. The reserve platoon counterattacked and the Marines threw them out hand to hand",
    "before dawn, with the base's guns firing round the hill; seven Marines were killed, and more",
    "than a hundred North Vietnamese dead were counted.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
