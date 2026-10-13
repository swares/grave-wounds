// Builds data/fields/chipyong-1951.yaml: the perimeter at Chipyong-ni on the night of 14-15
// February 1951, on the field map at 10 m a hex. Run from this folder after editing:
// node make_chipyong_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the plain facts of the
// battle as the US Army's histories give them and as they are summarised publicly. The 23rd
// Infantry held a perimeter about a mile across on the low hills round the village: the 1st
// Battalion on the north, the 3rd on the east, the 2nd on the south (G Company on the southern
// hill, the Chinese coming at it from Hill 397), the French Battalion on the west, with B
// Company and the 1st Ranger Company in reserve and the artillery, the tanks and the AAA's
// quad .50s inside. Aircraft dropped flares through the nights. The hills, the village, the
// railroad and the paddies are drawn by hand to that shape, not traced from any map, and are
// approximate; the deployment is the second night's attack, in our own words, with round numbers
// for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 200, ROWS = 170;                 // 2000 m east to west, about 1470 m north to south
const CX = 100, CY = 86, RX = 72, RY = 58;    // the perimeter: an uneven ring of low hills round the village
const ring = (c, r) => Math.hypot((c - CX) / RX, (r - CY) / RY) * (1 + 0.05 * wobble(Math.atan2(r - CY, c - CX) * 8, 0.7, 1.9));
const RAIL = r => 96 + Math.round(wobble(r / 9, 1.1, 0.2) * 0.4);        // the railroad, east to west through the south of the village
const ROAD = r => 102 + Math.round(wobble(r / 6, 0.4, 1.3) * 0.6);       // the road north and south (Route 24 and the road to Yoju)
function kind(c, r){
  if (Math.abs(c - ROAD(r)) <= 1) return ".";                             // the road
  if (Math.abs(r - RAIL(c)) <= 1) return ".";                             // the railroad embankment
  if (patch(c, r, { cx: CX, cy: CY, rx: 20, ry: 13, a: 0.4, b: 2.2 })) return speckle(c, r, 4) ? "." : "T";   // the village
  const k = ring(c, r);
  if (k > 0.86 && k < 1.08) return speckle(c, r, 7) ? "F" : "h";          // the perimeter hills, with scrub
  if (k >= 1.25 && speckle(c, r, 2)) return speckle(c, r, 3) ? "F" : "h";  // the hills beyond, wooded
  return speckle(c, r, 23) ? "r" : ".";                                    // paddies, frozen, and dikes
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const UN = { side: 0, facing: N }, CH = { side: 1, facing: S };
const DUG = { quality: "regular", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };   // in their foxholes
const MG = { quality: "regular", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false, prone: true };
const PVA = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false };
const edge = (angle, out = 0) => {                                        // the hex on the perimeter crest (out: hexes outside it) at an angle (0 east, 90 south)
  const a = angle * Math.PI / 180;
  return [Math.round(CX + (RX + out) * 0.97 * Math.cos(a)), Math.round(CY + (RY + out) * 0.97 * Math.sin(a))];
};
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  // the 1st Battalion on the north
  at("A Company, 23rd Infantry", UN, 150, DUG, 30, edge(-115), N),
  at("C Company, 23rd Infantry (astride the road north)", UN, 150, DUG, 30, edge(-80), N),
  // the 3rd Battalion on the east
  at("I Company, 23rd Infantry", UN, 150, DUG, 25, edge(-40), 0),
  at("K Company, 23rd Infantry", UN, 150, DUG, 25, edge(0), 0),
  at("L Company, 23rd Infantry", UN, 150, DUG, 25, edge(38), 5),
  // the 2nd Battalion on the south
  at("E Company, 23rd Infantry", UN, 150, DUG, 30, edge(65), S),
  at("G Company, 23rd Infantry (the southern hill)", UN, 140, DUG, 30, edge(95), S),
  at("F Company, 23rd Infantry", UN, 150, DUG, 30, edge(125), S),
  // the French Battalion on the west
  at("French Battalion, 3rd Company", UN, 200, { ...DUG, quality: "veteran" }, 25, edge(158), 3),
  at("French Battalion, 2nd Company", UN, 200, { ...DUG, quality: "veteran" }, 25, edge(190), 3),
  at("French Battalion, 1st Company", UN, 200, { ...DUG, quality: "veteran" }, 25, edge(222), 2),
  // machine guns and the AAA's quad .50s on the line
  at("Quad .50s (82nd AAA), south", UN, 20, MG, 4, edge(80, -6), S),
  at("Quad .50s (82nd AAA), north", UN, 20, MG, 4, edge(-95, -6), N),
  at("2nd Battalion machine guns", UN, 15, MG, 3, edge(110, -6), S),
  // the reserve inside
  at("B Company, 23rd Infantry (reserve)", UN, 150, { ...DUG, prone: false }, 25, [CX - 30, CY + 12], S),
  at("1st Ranger Company (reserve)", UN, 100, { ...DUG, prone: false, quality: "veteran" }, 20, [CX + 30, CY + 12], S),
  // the Chinese, closing in the dark
  at("Chinese regiment from Hill 397 (against G Company)", CH, 1200, PVA, 60, [edge(92)[0], 150], N),
  at("Chinese battalion (against E Company)", CH, 500, PVA, 30, edge(50, 22), 2),
  at("Chinese battalion (against C Company)", CH, 600, PVA, 40, [edge(-80, 26)[0], 6], S),
  at("Chinese battalion (against K Company)", CH, 500, PVA, 30, [edge(0, 18)[0], edge(0)[1]], 3),
  at("Chinese battalion (against the French)", CH, 500, PVA, 30, [16, edge(190)[1]], 0),
  at("Chinese machine guns (south)", CH, 15, { ...MG, kit: "none", quality: "veteran", prone: false }, 3, [edge(110)[0], 160], N),
];

writeField({
  objective: { at: edge(95), side: 1, name: "G Company's hill on the southern perimeter" },
  id: "chipyong-1951", name: "The perimeter at Chipyong-ni, 14-15 February 1951", sides: ["United Nations", "Chinese"], table: "korea-1950-53-hospitalized",
  travel: { map: "chipyong-1951", place: "Chipyong-ni", within: 2, sides: ["United Nations", "Chinese"] },
  weather: "{cond: fair, wind: breeze, dir: NW, light: night, ground: {mud: 0, snow: 1}}",
  grid, units,
  support: [
    { name: "105 mm howitzers (37th Field Artillery)", side: 0, kind: "field", tubes: 18 },
    { name: "155 mm howitzers (B Battery, 503rd Field Artillery)", side: 0, kind: "howitzer", tubes: 6 },
    { name: "4.2-inch mortars", side: 0, kind: "mortar", tubes: 6 },
    { name: "Tanks (the regimental tank company)", side: 0, kind: "tank", tubes: 6 },
    { name: "Fighter-bombers (by day)", side: 0, kind: "fighter_bomber", tubes: 8 },
    { name: "Chinese mortars", side: 1, kind: "mortar", tubes: 12 },
  ],
  header: [
    `The perimeter at Chipyong-ni on the night of 14-15 February 1951, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 2000 m`,
    "east to west and 1470 m north to south, north at the top: the village in the middle, the",
    "railroad through its south, the road north and south, and the ring of low hills the 23rd",
    "Infantry dug in on, about a mile across.",
    "Generated by tools/maps/make_chipyong_field.mjs: edit that file and re-run it rather than this one.",
    "The hills, the village, the railroad and the paddies are drawn by hand to the shape the",
    "accounts give, not traced from any map; the deployment is the second night's attack, in our",
    "own words, with round numbers for play. A clear, bitter night with snow on the ground and the",
    "paddies frozen hard (open ground). It is dark: fire the illumination (the transports' flares)",
    "or flares from the line to see what is coming. The fighter-bombers fly only by day.",
    "",
    "What happened, briefly: the Chinese came at the perimeter on the night of 13 February, from",
    "the north-west, north and south-east, and again all round after dark on the 14th, after a",
    "day in which fighter-bombers and an airdrop of ammunition kept them off. In the early hours",
    "of the 15th they broke into the southern perimeter at G Company's hill; counterattacks by the",
    "reserve, the Rangers and B Company could not retake all of it. That afternoon Task Force",
    "Crombez's tanks arrived from Yoju and the Chinese drew off. The 23rd lost about 50 killed,",
    "250 wounded and 40 missing; the Chinese, by US estimates, some 2,000 killed.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
