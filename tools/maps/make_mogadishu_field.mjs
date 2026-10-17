// Builds data/fields/mogadishu-1993.yaml: the streets round the target and the two crash sites
// in Mogadishu on the evening of 3 October 1993, on the field map at 10 m a hex. Run from this
// folder after editing: node make_mogadishu_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's account (The
// United States Army in Somalia, 1992-1994, a work of the US government) and the published
// positions of the target, the Olympic Hotel and the two crash sites. The target building was
// down the street from the Olympic Hotel, by the Bakara Market; the first Black Hawk came down
// about three blocks to the north-east, and some 90 Rangers and Delta fought their way to it and
// held the houses round it through the night; the second came down less than a mile to the south
// and was overrun. The street plan, the houses, the walled yards and the taller buildings are
// drawn by hand, not traced from any map or photograph, and are approximate: a grid of narrow
// streets and one-storey stone houses behind walls, the hotel and a few blocks of several
// storeys, the market's crowded stalls. The deployment is nightfall, in our own words, with
// round numbers for play.
import { N, S, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 110, ROWS = 110;                 // 1100 m east to west, about 950 m north to south
const TARGET = [45, 40], HOTEL = [44, 48], CRASH1 = [63, 21], CRASH2 = [64, 91];
const SHALALAWI = 48;                         // the street north past the Olympic Hotel (two hexes wide)
const NATIONAL = 100;                         // the wide street along the south
function street(c, r){
  if (c === SHALALAWI || c === SHALALAWI + 1) return true;
  if (r === NATIONAL || r === NATIONAL + 1) return true;
  if ((c + Math.floor(r / 23) * 3) % 9 === 0) return true;               // north-south streets, a block of eight houses between, jogging every few blocks
  return (r + Math.floor(c / 31) * 2) % 8 === 0;                          // east-west streets and alleys
}
function kind(c, r){
  if (street(c, r)) return speckle(c, r, 13) ? "r" : ".";                  // sand streets, the odd wreck or barricade
  if (patch(c, r, { cx: HOTEL[0] - 3, cy: HOTEL[1], rx: 3, ry: 3, a: 0.2, b: 0.9 })) return "B";   // the Olympic Hotel, five storeys
  if (patch(c, r, { cx: 18, cy: 66, rx: 16, ry: 18, a: 1.3, b: 0.4 })) return speckle(c, r, 3) ? "r" : "T";   // the Bakara Market: stalls, sheds, alleys
  if (speckle(c, r, 37) || patch(c, r, { cx: 84, cy: 34, rx: 4, ry: 3 }) || patch(c, r, { cx: 30, cy: 22, rx: 3, ry: 3 })) return "B";   // a few blocks of several storeys
  return speckle(c, r, 6) ? "." : "T";                                     // one-storey stone houses behind walls, and their yards
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const US = { side: 0, facing: N }, SNA = { side: 1, facing: S };
// The assault force went in by day and left its night-vision goggles behind: nv none.
const RANGER = { quality: "veteran", weapon: "rifle_assault", kit: "ranger_1993", formation: "extended", mounted: false, nv: "none" };
const SAW = { quality: "veteran", weapon: "machine_gun", kit: "ranger_1993", formation: "mg", mounted: false, nv: "none" };
const MILITIA = { quality: "green", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("Rangers and Delta in the houses north of the crash", US, 30, { ...RANGER, fac: true }, 6, [CRASH1[0] - 2, CRASH1[1] - 3], N),
  at("Rangers and Delta in the houses south of the crash", US, 30, RANGER, 6, [CRASH1[0] + 1, CRASH1[1] + 4], S),
  at("Rangers and Delta at the corner west of the crash", US, 25, RANGER, 4, [CRASH1[0] - 6, CRASH1[1] + 1], 3),
  at("Machine guns (SAWs and M60s) at the crash", US, 10, SAW, 2, [CRASH1[0] + 4, CRASH1[1] - 1], 0),
  at("Crash site 2: the crew, Gordon and Shughart", US, 6, RANGER, 2, [CRASH2[0] - 2, CRASH2[1]], S),
  at("Relief column (10th Mountain infantry)", US, 150, { ...RANGER, quality: "regular" }, 15, [44, 100], N),
  at("Relief column (Malaysian APCs and Pakistani tanks)", US, 36, { quality: "regular", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "apc" }, 4, [60, 100], N),
  at("Militia from the Bakara Market", SNA, 300, MILITIA, 30, [30, 34], 0),
  at("Militia coming in from the north", SNA, 200, MILITIA, 30, [62, 5], S),
  at("Militia from the east", SNA, 150, MILITIA, 20, [90, 22], 3),
  at("Militia and the crowd at crash site 2", SNA, 200, MILITIA, 30, [64, 84], S),
  at("RPG teams", SNA, 20, { ...MILITIA, weapon: "rpg", quality: "regular" }, 4, [48, 12], 5),
  at("Militia machine guns", SNA, 10, { ...SAW, kit: "none", quality: "regular" }, 2, [78, 40], 2),
];

writeField({
  phases: [   // an exchange is about a minute; times and sources in the project's battle-phases research (round 2), rounded; (est.) marks an estimate
    { name: "Two crash sites", at: 1, note: "About 16:42: the Rangers and Delta hold the houses round Super 61; Gordon and Shughart are inserted at Super 64." },
    { name: "Crash site 2 falls", at: 59, note: "About 17:40: the snipers run out of ammunition and are killed as the crowd overruns Durant's crash site." },
    { name: "The relief column", at: 553, note: "01:55: the relief column of 10th Mountain troops in Malaysian APCs, with Pakistani tanks, reaches the trapped force.", arrive: ["Relief column (10th Mountain infantry)", "Relief column (Malaysian APCs and Pakistani tanks)"] },
  ],
  ends: { at: 783, why: "out at dawn: sunrise 05:44, worked out for the place and day, from 16:42" },
  objective: { at: CRASH1, side: 1, name: "Super 61's crash site", radius: 4 },
  id: "mogadishu-1993", name: "Mogadishu: the crash sites, 3 October 1993", sides: ["United States", "Somali National Alliance"], table: "somalia-1993-wounds",
  travel: { map: "mogadishu-1993", place: "Crash site 1 (Super 61)", within: 2, sides: ["United States", "Somali National Alliance"] },
  weather: "{cond: fair, wind: breeze, dir: SW, light: night, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { wreck: [CRASH1, CRASH2] },
  support: [
    { name: "Little Bird gunships (AH-6)", side: 0, kind: "gunship", tubes: 4 },
  ],
  header: [
    `The streets round the target and the two crash sites in Mogadishu on the evening of 3 October 1993, at 10 m a hex: ${COLS} x`,
    `${ROWS} hexes, about 1100 m east to west and 950 m north to south, north at the top: the target building`,
    "left of the middle, the Olympic Hotel down the street from it on Shalalawi Street, the Bakara",
    "Market to the south-west, the first crash site to the north-east and the second to the south.",
    "Generated by tools/maps/make_mogadishu_field.mjs: edit that file and re-run it rather than this one.",
    "The street plan, the houses, the walled yards and the taller buildings are drawn by hand, not",
    "traced from any map or photograph: narrow sand streets (open ground), one-storey stone houses",
    "behind walls (buildings), the hotel and a few blocks of several storeys (tall buildings), the",
    "market's stalls and sheds. The deployment is nightfall, in our own words, with round numbers",
    "for play. It is dark (the moon rose late that night); the Little Birds fly at night. The two",
    "downed Black Hawks are on the map (downed helicopters). There are no vehicle rules: the relief",
    "column can be brought on as infantry from the south with Add a unit.",
    "",
    "What happened, briefly: Task Force Ranger landed at the target at about 15:42 and took 24",
    "prisoners. As the force was leaving, Super 61 was shot down by an RPG about three blocks away;",
    "the Rangers and Delta fought their way to it on foot and held the houses round it, while",
    "Super 64 came down to the south, where two Delta snipers who had asked to go in died",
    "defending the crew and the site was overrun. Through the night Little Birds fired for the",
    "men at the first crash. At 01:55 the relief column reached them, and at dawn they came out,",
    "some of them on foot, to the Pakistani stadium. Eighteen Americans were killed and some 80",
    "wounded; Somali losses are put at 500 to 1,500.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
