// Builds data/fields/topolcani-1915.yaml: a Serbian rearguard in the snow by Topolčani, on the road
// from Prilep to Bitola, in late November 1915, on the field map at 10 m a hex. Run from this folder
// after editing: node make_topolcani_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours (project doc "mojkovac-topolcani-research"):
// Flora Sandes, An English Woman-Sergeant in the Serbian Army (1916), chapter III, who was with the
// 2nd Regiment's ambulance: "little shallow trenches dotted about on the hillside, with about a
// dozen men in each"; two regiments on "an enormous front", "outnumbered by the Bulgarians by more
// than four to one"; a company of reinforcements floundering up through the drifts; a small
// deserted hahn (inn) of two rooms by the roadside close to Topolčani, a river behind it that the
// road crossed by a bridge with ten mines in it, which failed to blow up; snow all night, a blizzard
// from daybreak that stopped for a while about midday, the Bulgarians' "Hourrah" as they took the
// trenches about midday, big guns in the late afternoon, the ambulance sent back at twilight and the
// staff gone about nine; most of the wounded hit in the right arm or wrist. She gives no date: it
// falls after Prilep was occupied on 17 November and before Bitola fell (about 21 November); we take
// about 19 November. The hillside, the river, the bridge and the hahn are drawn by hand to her
// account, not traced from any map; the companies, the Bulgarian battalions and the hours are ours,
// with round numbers for play at her odds of four to one.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 130, ROWS = 110;                 // 1300 m east to west, about 950 m north to south
const ROAD_C = 66;                            // the road from Prilep (north) to Bitola (south)
const road = r => (r < 76 ? ROAD_C + Math.round(wobble(r / 6, 0.7, 2.2) * 1.2) : ROAD_C);   // straight down to the bridge
// The hillside: a long low rise across the north of the map, its crest a wavy line, the trenches
// dotted along its forward slope.
const crest = c => Math.round(30 + 4 * Math.sin((c - 20) / 22) + wobble(c / 8, 1.3, 0.2) * 0.6);
const riverRow = c => Math.round(86 + 3 * Math.sin(c / 17) + wobble(c / 5, 0.2, 1.1) * 0.5);   // the river, west to east, behind the hahn
const HAHN = [ROAD_C + 4, 68];                // the hahn by the roadside, close to the village
const onRoad = (c, r) => Math.abs(c - road(r)) <= 0;

function kind(c, r){
  const k = crest(c), w = riverRow(c);
  if (r >= w && r <= w + 1) return c === ROAD_C ? "." : "w";                                    // the river and its bridge
  if (onRoad(c, r)) return ".";
  if (Math.abs(c - HAHN[0]) <= 1 && Math.abs(r - HAHN[1]) <= 0) return "T";                     // the hahn: two small rooms
  if (r > w + 1) return speckle(c, r, 5) ? "o" : ".";                                           // beyond the river, towards Bitola
  if (Math.abs(r - k) <= 1) return speckle(c, r, 5) ? "r" : "h";                                // the crest of the hillside
  if (r < k - 1 && r >= k - 12) return speckle(c, r, 7) ? "r" : "s";                            // its forward slope, towards Prilep
  if (r < k - 12) return patch(c, r, { cx: 112, cy: 6, rx: 18, ry: 8, a: 0.8, b: 1.6 }) ? "F" : (speckle(c, r, 9) ? "o" : ".");
  if (r > k + 1 && r <= k + 10) return speckle(c, r, 6) ? "o" : "s";                            // the reverse slope
  if (patch(c, r, { cx: 104, cy: 74, rx: 14, ry: 6, a: 1.1, b: 0.5 })) return "h";               // a little hill by the road
  if (patch(c, r, { cx: 26, cy: 66, rx: 16, ry: 8, a: 0.4, b: 2.3 })) return "T";                // Topolčani village
  return speckle(c, r, 6) ? "o" : ".";
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const SR = { side: 0, facing: N }, BG = { side: 1, facing: S };
const SERB = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false, prone: true };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "mg", mounted: false, prone: true };
const BULGAR = { quality: "regular", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false };
const forward = (w, c0) => [w, c0, Math.min(...Array.from({ length: w }, (_, i) => crest(c0 + i))) - 3];   // on the forward slope
const units = [
  unit("2nd Regiment, a company west of the road", SR, 200, SERB, forward(24, 30)),
  unit("2nd Regiment, a company astride the road", SR, 200, SERB, forward(24, 56)),
  unit("2nd Regiment machine guns", SR, 10, MG, forward(2, 84)),
  unit("2nd Regiment, the company of reinforcements", SR, 200, { ...SERB, prone: false }, [24, 54, 50]),
  unit("Bulgarian battalion down the road", BG, 850, BULGAR, [30, 52, 16]),
  unit("Bulgarian battalion on the west", BG, 850, BULGAR, [30, 12, 16]),
  unit("Bulgarian machine guns", BG, 20, { ...MG, quality: "regular", prone: false }, [4, 88, 20]),
  unit("Bulgarian battalion on the east", BG, 850, BULGAR, [30, 92, 16]),
];
// The little shallow trenches dotted about on the hillside: a short stretch in every few hexes.
const trench = [];
for (let c = 20; c <= 96; c++) if (Math.floor(c / 3) % 3 !== 2) trench.push([c, crest(c) - 3]);

writeField({
  phases: [   // an exchange is about a minute; the hours are our reading of Sandes (project doc "mojkovac-topolcani-research")
    { name: "Daybreak in the blizzard", at: 1, note: "About 07:00: in a blizzard after a night of snow, the Bulgarians come on down the road from Prilep at the trenches on the hillside (the hour is ours; 'daybreak')." },
    { name: "The reinforcements", at: 121, note: "About 09:00: a company of reinforcements flounders up through the deep drifts (Sandes; the hour is ours).", arrive: ["2nd Regiment, the company of reinforcements"] },
    { name: "The blizzard stops", at: 271, note: "About 11:30: the blizzard stops for a while (Sandes: 'about midday').", weather: { cond: "heavy_snow", wind: "strong" } },
    { name: "The trenches taken", at: 301, note: "About midday: the Bulgarians' 'Hourrah' as they take the trenches (Sandes)." },
    { name: "The big guns", at: 481, note: "Late afternoon: the big guns open again; the bridge, with ten mines in it, fails to blow up, and the Bulgarian guns cross (Sandes; the hour is ours).", weather: { cond: "snow", wind: "strong" } },
    { name: "Twilight", at: 541, note: "About 16:00, the grey November twilight: the ambulance is sent back and the Serbs go (Sandes).", light: "dusk" },
  ],
  ends: { at: 571, why: "the trenches taken about midday, the Serbs gone at dusk (Sandes): 07:00 to about 16:30" },
  objective: { at: [road(crest(ROAD_C) - 3), crest(ROAD_C) - 3], side: 1, name: "the trenches across the road to Bitola", radius: 10 },
  id: "topolcani-1915", name: "Topolčani, November 1915", sides: ["Serbians", "Bulgarians"], table: "wwi-1914-18-wounds",
  travel: { map: "serbia-1915", place: "Topolčani", within: 1, sides: ["Serbia and Montenegro", "Central Powers"] },
  weather: "{cond: blizzard, wind: gale, dir: N, ground: {mud: 0, snow: 2}}",
  grid, units,
  hexWorks: { trench },
  support: [
    { name: "Serbian mountain guns (a few, old)", side: 0, kind: "field", tubes: 2 },
    { name: "Bulgarian field guns", side: 1, kind: "field", tubes: 8 },
    { name: "Bulgarian big guns", side: 1, kind: "howitzer", tubes: 2 },
  ],
  header: [
    `By Topolčani on the road from Prilep to Bitola, late November 1915, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1300 m`,
    "east to west and 950 m north to south, north at the top: the road comes down from Prilep over",
    "a long low hillside with the Serbian trenches dotted along its forward slope, past the hahn",
    "by the roadside and the village to the west, and crosses the river at the bottom by a bridge.",
    "Generated by tools/maps/make_topolcani_field.mjs: edit that file and re-run it rather than this one.",
    "The hillside, the river, the bridge and the hahn are drawn by hand to Flora Sandes's account,",
    "not traced from any map. She gives no date (after Prilep fell on 17 November, before Bitola",
    "fell about the 21st: we take about the 19th) and no strengths beyond the odds, more than four",
    "to one; the companies, the Bulgarian battalions and the hours are our reading, with round",
    "numbers for play. The bridge's mines failed, so the bridge stands.",
    "",
    "What happened, briefly: after the Babuna pass was given up, the 2nd and 14th Regiments fell",
    "back down the road towards Bitola, holding the Bulgarians off as they went. By Topolčani, in a",
    "blizzard after a night of snow, they held little shallow trenches dotted about on a hillside,",
    "a dozen men in each, outnumbered more than four to one. A company of reinforcements came up",
    "through the drifts; about midday the Bulgarians took the trenches. The bridge behind, with ten",
    "mines in it, failed to blow up, and the Bulgarian guns came across in the late afternoon. At",
    "twilight the ambulance was sent back, and the Serbs went on towards Bitola and Albania. Most of",
    "the wounded Sandes dressed were hit in the right arm or wrist.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
