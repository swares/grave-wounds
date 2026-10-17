// Builds data/fields/lutzen-1632.yaml: the field of Lützen, 16 November 1632, on the field map at
// 10 m a hex. Run from this folder after editing: node make_lutzen_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours: the Imperial army stood north of the high
// road from Lützen to Leipzig, with the road's ditches dug out and lined with musketeers, the
// town on its right and guns on the windmill hill by the town; the Swedes came up from the south
// after crossing the Floßgraben, a timber canal. The town, the hill, the road and its ditches,
// and the canal are drawn by hand to that shape, not traced from any map, and are approximate.
// The deployment is the outline most modern accounts share, in our own words: both armies in
// lines of foot with horse on the wings, and Pappenheim's horse coming in late on the Imperial
// left. Numbers are disputed; those here are round figures for play, the guns among them.
import { N, S, wobble, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 220, ROWS = 120;                 // 2200 m east to west, about 1040 m north to south
const ROAD = 75;                              // the high road runs east and west along this row
function kind(c, r){
  if (c < 22 + wobble(r, 0.8, 1.9) && r > 38 && r < ROAD) return "r";            // Lützen: the burning town, its gardens and walls
  if (c >= 24 && c < 54 + wobble(r, 2.1, 0.6) && r > 48 && r < ROAD) return "h"; // the windmill hill
  if (Math.abs(r - (115 + wobble(c / 3, 1.3, 0.4))) < 1) return "m";              // the Floßgraben, behind the Swedes
  return ".";
}
const grid = groundGrid(COLS, ROWS, kind);

// The road's ditches, dug out and lined with musketeers: a bank on its north side (the earth
// thrown up, high side north) and a ditch on its south side (high side the road). On an odd row
// a hex's southern neighbours are (c, r+1) and (c+1, r+1).
const bank = [], ditch = [];
for (let c = 0; c < COLS; c++){
  for (const dc of [-1, 0]) if (c + dc >= 0) bank.push([[c, ROAD - 1], [c + dc, ROAD]]);      // row 74 is even: its southern neighbours are c-1 and c
  for (const dc of [0, 1]) if (c + dc < COLS) ditch.push([[c, ROAD], [c + dc, ROAD + 1]]);   // row 75 is odd: its southern neighbours are c and c+1
}

// ---------- the armies (pos is the middle of the front row) ----------
const SWE = { side: 0, facing: N }, IMP = { side: 1, facing: S };
const SHOT = { quality: "regular", weapon: "matchlock_musket", kit: "none", formation: "open", mounted: false };
const PIKE = { quality: "regular", weapon: "pike", kit: "pikeman_1630", formation: "close", mounted: false };
const HORSE = { quality: "veteran", weapon: "sword", kit: "harquebusier_1630", formation: "close", mounted: true };
const CUIRASS = { ...HORSE, kit: "cuirassier_1630" };
const GUNS = { quality: "regular", weapon: "artillery_smoothbore", kit: "none", formation: "battery", mounted: false };   // ten crew to a gun
const units = [
  unit("Swedish musketeers, first line", SWE, 3000, { ...SHOT, quality: "veteran" }, [80, 70, 100]),
  unit("Swedish pike, first line", SWE, 3000, { ...PIKE, quality: "veteran" }, [50, 85, 103]),
  unit("Swedish second line", SWE, 4000, PIKE, [60, 80, 108]),
  unit("Swedish horse, right (the King)", SWE, 3000, HORSE, [30, 160, 100]),
  unit("Swedish horse, left (Bernhard)", SWE, 2500, HORSE, [25, 38, 100]),
  unit("Musketeers in the road ditch", IMP, 1600, SHOT, [80, 70, ROAD - 1]),
  unit("Imperial musketeers, centre", IMP, 4000, SHOT, [70, 75, 69]),
  unit("Imperial pike, centre", IMP, 4000, PIKE, [50, 85, 64]),
  unit("Musketeers at the windmill battery", IMP, 800, SHOT, [20, 30, 70]),
  unit("Windmill battery", IMP, 70, GUNS, [4, 38, 67]),
  unit("Imperial centre battery", IMP, 140, GUNS, [7, 105, 72]),
  unit("Swedish heavy guns", SWE, 200, GUNS, [10, 105, 97]),
  unit("Imperial horse, right", IMP, 1500, HORSE, [20, 30, 58]),
  unit("Imperial cuirassiers, left", IMP, 2000, CUIRASS, [25, 155, 68]),
  unit("Pappenheim's horse (coming up)", IMP, 2500, CUIRASS, [30, 185, 10]),
  unit("Pappenheim's foot (coming up, too late)", IMP, 3000, PIKE, [40, 120, 6]),
];

writeField({
  phases: [   // an exchange is about a minute; times from docs and sources in the project's battle-phases research, rounded
    { name: "The Swedes advance on the ditches", at: 1, note: "About 11:00 the King's lines begin their final advance across the road ditches." },
    { name: "Pappenheim strikes the Swedish right", at: 76, note: "Between 12:00 and 12:30 Pappenheim's horse arrive on the Imperial left and check the Swedish right.", arrive: ["Pappenheim's horse (coming up)"] },
    { name: "The King is killed; the second line goes in", at: 151, note: "After 13:00, in the fog: Gustavus Adolphus is killed and Knyphausen holds the line with the second line (the time is our estimate).", arrive: ["Swedish second line"] },
    { name: "Lull", at: 241, note: "By 15:00 Bernhard's attack has failed; a lull of about half an hour." },
    { name: "The final assault on the windmill hill", at: 271, note: "15:30 to 17:00: as the light fades Bernhard's men take the windmill battery." },
    { name: "Pappenheim's foot arrive", at: 421, note: "18:00: Pappenheim's foot come up, too late; at 20:00 Wallenstein withdraws.", arrive: ["Pappenheim's foot (coming up, too late)"] },
  ],
  ends: { at: 541, why: "Wallenstein withdraws at 20:00, from 11:00" },
  objective: { at: [38, 67], side: 0, name: "the windmill battery", radius: 4 },
  id: "lutzen-1632", name: "Lützen, 16 November 1632", sides: ["Swedes", "Imperialists"], table: "thirty-years-war-all-hits",
  travel: { map: "lutzen-1632", place: "Lützen", within: 2, sides: ["Sweden", "Empire"] },
  weather: "{cond: fog, wind: calm, ground: {mud: 0, snow: 0}}",
  grid, units, edgeWorks: { bank, ditch },
  header: [
    `The field of Lützen, 16 November 1632 (Gregorian), at 10 m a hex: ${COLS} x ${ROWS} hexes, about`,
    "2200 m east to west and 1040 m north to south, north at the top.",
    "Generated by tools/maps/make_lutzen_field.mjs: edit that file and re-run it rather than this one.",
    "The town, the windmill hill, the road and its ditches and the Floßgraben are drawn by hand to",
    "the shape the accounts give, not traced from any map; the deployment is the outline most",
    "modern accounts share, in our own words, with round numbers for play.",
    "",
    "What happened, briefly: the Swedes crossed the Floßgraben in the early morning and drew up",
    "facing the Imperial line behind the high road. Fog delayed the attack until late morning",
    "and came and went all day. The Swedish right drove the Imperial left back across the road;",
    "in the centre the Swedish foot took the ditches and lost them again. Gustavus Adolphus,",
    "riding to help his foot, was killed in the fog. Pappenheim's horse came up on the Imperial",
    "left at midday and checked the Swedish right; Pappenheim was mortally wounded. Late in the",
    "day Bernhard of Saxe-Weimar's men stormed the windmill hill and its battery, and in the",
    "night Wallenstein withdrew. The guns: 7 on the windmill hill and 14 in the Imperial centre,",
    "20 heavy Swedish guns in front of their foot (round figures; the regimental guns are left out).",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
