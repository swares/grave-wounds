// Builds data/fields/foxhill-1950.yaml: Fox Company, 7th Marines on its hill over Toktong Pass,
// the night of 27-28 November 1950, on the field map at 10 m a hex. Run from this folder after
// editing: node make_foxhill_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Marine Corps' and
// Army's accounts (works of the US government) and public summaries for the facts. Fox Company
// (Captain William Barber), about 240 men with attached machine guns and mortars, dug in on a
// hill north of the road at Toktong Pass, half way between Yudam-ni and Hagaru-ri, in snow and
// -20 F cold; from the first night a regiment of the Chinese 59th Division attacked it from the
// heights to the north and across the road; the company held for five days, supplied by air and
// covered by howitzers at Hagaru-ri and Corsairs by day, until the 1st Battalion, 7th Marines
// reached it over the mountains on 2 December. The hill, the road, the rocks and the slopes are
// drawn by hand to that shape, not traced from any map, and approximate; the deployment is the
// first night's attack, in our own words, with round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 150, ROWS = 120;                 // 1500 m east to west, about 1040 m north to south
const HILL = [75, 54];                        // the crest Fox Company held
const ROAD = c => 92 + Math.round(wobble(c / 9, 0.6, 1.4) * 1.2);       // the road through the pass, west to east, south of the hill
function kind(c, r){
  if (Math.abs(r - ROAD(c)) <= 1) return ".";                                                        // the road: ice and packed snow
  if (patch(c, r, { cx: HILL[0], cy: HILL[1], rx: 14, ry: 10, a: 0.9, b: 0.3 })) return speckle(c, r, 4) ? "r" : "h";   // the crest: rocks
  if (patch(c, r, { cx: HILL[0], cy: HILL[1] + 6, rx: 26, ry: 22, a: 1.6, b: 1.1 })) return speckle(c, r, 3) ? "F" : "r";   // its slopes: scrub pine, boulders
  if (r < 30) return speckle(c, r, 3) ? "F" : "h";                                                   // the heights to the north (Toktong-san's spurs)
  if (r > ROAD(c) + 3) return speckle(c, r, 4) ? "F" : "h";                                          // the ridge across the road
  return speckle(c, r, 5) ? "F" : "r";                                                               // broken slopes
}
const grid = groundGrid(COLS, ROWS, kind);

const US = { side: 0, facing: N }, CH = { side: 1, facing: S };
const MARINE = { quality: "regular", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };   // in holes hacked in the frozen ground
const MG = { quality: "regular", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false, prone: true };
const PVA = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("Fox Company, 3rd Platoon (the crest, facing north)", US, 60, MARINE, 14, [HILL[0] - 2, HILL[1] - 8], N),
  at("Fox Company, 1st Platoon (the east shoulder)", US, 55, MARINE, 10, [HILL[0] + 13, HILL[1] - 2], 0),
  at("Fox Company, 2nd Platoon (the west shoulder)", US, 55, MARINE, 10, [HILL[0] - 14, HILL[1] - 1], 3),
  { ...at("Heavy machine guns", US, 15, MG, 3, [HILL[0] + 4, HILL[1] - 6], N), fixed: [HILL[0], 26] },   // laid by day up the slope to the heights
  at("Company headquarters, mortars and the road block", US, 40, MARINE, 10, [HILL[0], HILL[1] + 14], S),
  at("Chinese battalion from the heights (north)", CH, 500, PVA, 40, [HILL[0], 24], S),
  at("Chinese battalion from the north-east", CH, 400, PVA, 30, [HILL[0] + 40, 34], 2),
  at("Chinese battalion across the road (south)", CH, 400, PVA, 40, [HILL[0], ROAD(HILL[0]) + 10], N),
  at("Chinese machine guns", CH, 10, { ...MG, kit: "none", quality: "veteran", prone: false }, 2, [HILL[0] - 30, 30], 5),
];

writeField({
  objective: { at: HILL, side: 1, name: "the crest Fox Company held", radius: 7 },
  id: "foxhill-1950", name: "Fox Hill at Toktong Pass, 27-28 November 1950", sides: ["United Nations", "Chinese"], table: "korea-1950-53-hospitalized",
  travel: { map: "chosin-1950", place: "Toktong Pass (Fox Hill)", within: 1, sides: ["United Nations", "Chinese"] },
  weather: "{cond: fair, wind: strong, dir: NW, light: night, cold: bitter, ground: {mud: 0, snow: 2}}",
  grid, units,
  support: [
    { name: "105 mm howitzers at Hagaru-ri", side: 0, kind: "field", tubes: 6 },
    { name: "Fox Company's 60 mm mortars", side: 0, kind: "mortar", tubes: 3 },
    { name: "Corsairs (by day)", side: 0, kind: "fighter_bomber", tubes: 4 },
    { name: "Chinese mortars", side: 1, kind: "mortar", tubes: 4 },
  ],
  header: [
    `Fox Hill over Toktong Pass on the night of 27-28 November 1950, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1500 m east to`,
    "west and 1040 m north to south, north at the top: the hill Fox Company held in the middle,",
    "the road through the pass below it to the south, the heights to the north, a ridge across",
    "the road.",
    "Generated by tools/maps/make_foxhill_field.mjs: edit that file and re-run it rather than this one.",
    "The hill, road, rocks and slopes are drawn by hand to the shape the accounts give, not traced",
    "from any map; the deployment is the first night's attack, in our own words, with round",
    "numbers for play. Bitter cold (-20 F): automatic weapons jam, men move slowly; deep snow; a",
    "dark night with a strong wind from the north-west. Corsairs fly only by day.",
    "",
    "What happened, briefly: Fox Company was posted on the hill on 27 November to hold the pass for",
    "the regiments at Yudam-ni. That night a Chinese regiment attacked it from three sides. The",
    "Marines held the crest, lost and retook part of it, and held on for five days and nights,",
    "supplied by air drops and covered by the howitzers at Hagaru-ri and by Corsairs, until the",
    "1st Battalion, 7th Marines reached them across the mountains on 2 December. Of about 240 men,",
    "26 were killed, 89 wounded and 3 missing; many more suffered frostbite.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
