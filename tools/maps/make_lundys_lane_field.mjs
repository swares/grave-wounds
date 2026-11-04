// Builds data/fields/lundys-lane-1814.yaml: the field of Lundy's Lane, 25 July 1814, on the field
// map at 10 m a hex. Run from this folder after editing: node make_lundys_lane_field.mjs (no
// packages needed).
//
// Sources, all plain fact, and the drawing is ours: the British held a low hill west of the
// Portage road, a mile or so from the falls, with Lundy's Lane running along its crest past a
// churchyard and their guns on the top; the Americans came up the Portage road from the south,
// through fields and woods. The hill, the woods and the fields are drawn by hand to that shape,
// not traced from any map, and are approximate. The deployment is the evening's opening, when
// Scott's brigade came up against the hill and Jesup's 25th worked round the British left by
// the Portage road, in our own words; numbers are round figures for play, the guns among them.
import { N, S, wobble, patch, groundGrid, unit, led, writeField } from "./field_lib.mjs";

const COLS = 130, ROWS = 110;                 // 1300 m east to west, about 950 m north to south
const crest = c => 30 + wobble(c / 3, 0.7, 1.6);                     // Lundy's Lane along the crest
function kind(c, r){
  const k = crest(c);
  if (patch(c, r, { cx: 62, cy: k, rx: 40, ry: 13, a: 0.7, b: 1.6 })) return "h";                 // the hill
  if (c >= 46 && c <= 52 && r >= k - 4 && r <= k - 1) return "r";   // the churchyard and its wall, behind the guns
  if (r > 60 && c < 45 + wobble(r / 2, 1.3, 0.2)) return "F";        // woods south-west, where Scott's men formed
  if (c > 112 && r > 40) return "F";                                 // woods along the river side
  if (r < 8 && c < 30) return "F";
  return ".";
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const US = { side: 0, facing: N }, GB = { side: 1, facing: S };
const LINE = { quality: "regular", weapon: "musket_smoothbore", kit: "none", formation: "close", mounted: false };
const HORSE = { quality: "regular", weapon: "saber", kit: "dragoon_helmet", formation: "close", mounted: true };
const GUNS = { quality: "regular", weapon: "artillery_smoothbore", kit: "none", formation: "battery", mounted: false };   // ten crew to a gun
// Leaders from the accounts (heroes.field_leaders), ranks as Wikipedia's "Battle of Lundy's Lane" gives
//   them; Riall with the 8th and 41st on the lane is ours. Brown and Drummond, who led no one unit,
//   are not on the map.
const units = [
  unit("Scott's brigade (9th, 11th, 22nd)", US, 800, { ...LINE, quality: "veteran" }, [24, 52, 72]),
  { ...unit("25th Infantry (Jesup)", US, 300, { ...LINE, quality: "veteran" }, [8, 104, 60]), via: [[110, 40], [100, 18]] },   // round the British left (the east end of the hill) to behind their line (our reading)
  unit("Towson's battery", US, 60, GUNS, [3, 72, 80]),
  unit("Ripley's brigade (21st, 23rd, coming up)", US, 900, LINE, [24, 52, 100]),
  unit("Porter's volunteers (coming up)", US, 500, { ...LINE, quality: "green", formation: "open" }, [25, 10, 100]),
  unit("British guns on the crest", GB, 50, GUNS, [3, 49, 33]),
  unit("89th Foot", GB, 400, { ...LINE, quality: "veteran" }, [10, 36, 35]),
  unit("Incorporated Militia", GB, 300, { ...LINE, quality: "green" }, [8, 56, 35]),
  unit("Glengarry Light Infantry", GB, 300, { ...LINE, formation: "open" }, [15, 14, 40]),
  unit("8th and 41st Foot (on the lane)", GB, 400, LINE, [10, 66, 35]),
  unit("19th Light Dragoons", GB, 150, HORSE, [6, 86, 30]),
  unit("Hercules Scott's column (coming up)", GB, 1000, LINE, [25, 40, 10]),
  // Hindman's guns brought up among the captured British guns (Wikipedia: "While the Americans tried to deploy their
  // own artillery among the captured British guns, Drummond ... mounted a determined attempt to retake his own
  // cannon"; HistoryNet: they "consolidated the high ground and brought up their own artillery"): Biddle's three
  // 12-pounders and Ritchie's two 6-pounders and howitzer (Wikipedia's order of battle), ten crew to a gun; where
  // on the crest, just behind the British guns' ground, is ours.
  unit("Hindman's guns brought up (Biddle's and Ritchie's companies)", US, 60, GUNS, [6, 49, 37]),
];
led(units, {
  "Scott's brigade (9th, 11th, 22nd)": [["Winfield Scott", "Brigadier-General"]],
  "25th Infantry (Jesup)": [["Thomas Jesup", "Major"]],
  "Towson's battery": [["Nathan Towson", "Captain"]],
  "Ripley's brigade (21st, 23rd, coming up)": [["Eleazer Ripley", "Brigadier-General"]],
  "Porter's volunteers (coming up)": [["Peter B. Porter", "Brigadier-General"]],
  "89th Foot": [["Joseph Morrison", "Lieutenant-Colonel"]],
  "Incorporated Militia": [["William Robinson", "Lieutenant-Colonel"]],
  "Glengarry Light Infantry": [["Francis Battersby", "Lieutenant-Colonel"]],
  "8th and 41st Foot (on the lane)": [["Phineas Riall", "Major-General"]],
  "19th Light Dragoons": [["Robert Lisle", "Major"]],
  "Hercules Scott's column (coming up)": [["Hercules Scott", "Colonel"]],
});

writeField({
  phases: [   // an exchange is about a minute; the times are our reading of the accounts, rounded
    { name: "Scott attacks the hill", at: 1, note: "About seven in the evening: Scott's brigade attacks the guns on the hill rather than wait, while Jesup's 25th works round the British left." },
    { name: "Sunset", at: 31, note: "About half past seven the sun sets (worked out for the place and day): dusk.", light: "dusk" },
    { name: "Dark, by moonlight", at: 61, note: "By about eight it is dark; a moon some eight days old, more than half lit, is up until after midnight.", light: "moonlit" },
    { name: "Ripley and Hercules Scott come up", at: 120, note: "About nine, in the dark: Brown brings up Ripley's brigade and Porter's volunteers, and Hercules Scott's column, sent towards Queenston and recalled, reaches the British line.", arrive: ["Ripley's brigade (21st, 23rd, coming up)", "Porter's volunteers (coming up)", "Hercules Scott's column (coming up)"] },
    { name: "Drummond's counter-attacks", at: 150, note: "Drummond's reinforced line counter-attacks three times to win back the guns, until near midnight." },
    { name: "The American guns come up", at: 271, when: { broken: "British guns on the crest" }, note: "Once the British guns are taken, Hindman brings Biddle's and Ritchie's guns up among them on the crest (Wikipedia; HistoryNet); Drummond's men come on to retake their cannon, \"the muzzles of the Enemy's Guns ... advanced within a few Yards of ours\" (Drummond). Never, if the guns are not taken.", arrive: ["Hindman's guns brought up (Biddle's and Ritchie's companies)"] },
  ],
  ends: { at: 271, why: "counter-attacks until near midnight: 23:30 from 19:00" },
  objective: { at: [49, 33], side: 0, name: "the British guns on the crest by the churchyard", radius: 3 },
  id: "lundys-lane-1814", name: "Lundy's Lane, 25 July 1814", sides: ["Americans", "British"], table: "war-1812-all-hits",
  travel: { map: "lundys-lane-1814", place: "Lundy's Lane", within: 2, sides: ["United States", "Britain"] },
  weather: "{cond: fair, wind: calm, dir: SW, ground: {mud: 0, snow: 0}}",
  grid, units,
  header: [
    `The field of Lundy's Lane, 25 July 1814, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1300 m east to`,
    "west and 950 m north to south, north at the top; the Portage road and the Niagara are off the",
    "map to the east.",
    "Generated by tools/maps/make_lundys_lane_field.mjs: edit that file and re-run it rather than this one.",
    "The hill, the churchyard, the woods and the fields are drawn by hand to the shape the accounts",
    "give, not traced from any map; the deployment is the evening's opening, in our own words, with",
    "round numbers for play.",
    "",
    "What happened, briefly: Scott's brigade came up the Portage road at about seven in the evening",
    "and found Riall's men on the hill with their guns at the churchyard. Scott attacked rather than",
    "wait, and his brigade was shot to pieces in front of the guns over the next two hours, though",
    "Jesup's 25th worked round the British left in the dusk and took Riall prisoner. Brown brought up",
    "Ripley's brigade; in the dark Colonel Miller's 21st Infantry rushed the guns and took them, and",
    "the Americans held the crest. Drummond's reinforced line counter-attacked three times until",
    "near midnight. Both sides were exhausted; the Americans fell back to Chippawa, taking one British 6-pounder but leaving the rest.",
    "Most of it was fought at night: the phases bring dusk at sunset (about 19:30) and a moonlit night",
    "from about 20:00 (a moon about eight days old, more than half lit: sunset and moon are worked out",
    "for the place and the day, not from the accounts, which speak of darkness and thick smoke).",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
