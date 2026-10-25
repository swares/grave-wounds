// Builds data/fields/bougainville-1944.yaml: Hill 700 on the Torokina perimeter, Bougainville,
// 8-12 March 1944, on the field map at 10 m a hex. Run from this folder after editing:
// node make_bougainville_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours: Hill 700 is a steep ridge on the north of
// the perimeter, held by the 145th Infantry (37th Infantry Division) in a line of log-and-earth
// pillboxes with wire in front and a belt of jungle cleared below it for fields of fire. The
// Japanese 23rd Infantry Regiment came up its northern slopes through the jungle and broke into
// the line at a saddle on the night of 8-9 March; the Americans drove them out over the next
// days, with artillery and mortars firing on call close in front of the line. The ridge, the
// saddle, the cleared belt and the line are drawn by hand to that shape, not traced from any
// map, and are approximate. The deployment is the start of the attack, in our own words;
// numbers are round figures for play.
import { frontRow, N, S, wobble, patch, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 120, ROWS = 100;                 // 1200 m east to west, about 870 m north to south
const crest = c => 48 + wobble(c / 3, 0.7, 2.2) * 0.8;               // the ridge's crest line, west to east
const saddle = c => c >= 54 && c <= 66;                               // where the line dips between two knobs
function ridgeTop(c, off){
  if (!saddle(c)) return "h";
  return Math.abs(off) <= 2 ? "." : "r";
}
function kind(c, r){
  const k = crest(c);
  if (Math.abs(r - k) <= 6) return ridgeTop(c, r - k);                       // the ridge top; the saddle lower, its sides broken
  if (r > k - 18 && r < k - 6) return (c * 7 + r * 3) % 11 === 0 ? "r" : ".";  // the cleared belt: stumps and shell holes
  if (r >= k - 22 && r <= k - 18) return "r";                                // the jungle's torn edge
  if (r > k + 6 && r < k + 12 && patch(c, r, { cx: 60, cy: k + 9, rx: 70, ry: 4, a: 0.2, b: 1.1 })) return "r";   // the steep back slope
  return "F";                                                                // jungle
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- works: wire below the crest (the pillboxes are under the line that held them, below) ----------
const wire = [];
for (let c = 2; c < COLS - 2; c++) if (c % 13 !== 6) wire.push([c, Math.round(crest(c)) - 12]);   // a belt with lanes through it

// ---------- the armies (pos is the middle of the front row) ----------
const US = { side: 0, facing: N }, JP = { side: 1, facing: S };
const RIFLES = { quality: "regular", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false };
const MG = { quality: "regular", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false };
const JRIFLES = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false };
const units = [
  unit("145th Infantry, 2nd Battalion (west knob)", US, 330, RIFLES, [44, 4, Math.round(crest(26)) - 2]),
  unit("145th Infantry, 2nd Battalion (east knob)", US, 330, RIFLES, [44, 72, Math.round(crest(94)) - 2]),
  unit("Machine guns covering the saddle (west)", US, 12, MG, [3, 50, Math.round(crest(51)) - 1]),
  unit("Machine guns covering the saddle (east)", US, 12, MG, [3, 67, Math.round(crest(68)) - 1]),
  unit("145th Infantry, 1st Battalion (reserve)", US, 700, RIFLES, [60, 30, 82]),
  unit("148th Infantry, 2nd Battalion (11-12 March)", US, 600, RIFLES, [50, 35, 86]),
  unit("23rd Infantry, II Battalion (on the saddle)", JP, 800, JRIFLES, [36, 30, 20]),
  unit("23rd Infantry, III Battalion (east slope)", JP, 800, JRIFLES, [36, 76, 14]),
  unit("23rd Infantry machine-gun company", JP, 30, { ...MG, kit: "none", quality: "veteran" }, [6, 60, 26]),
];

// The pillbox line on the crest, held by the 145th Infantry: a pillbox every seventh hex along the
// front rows of its battalions on the crest and under each machine-gun section (drawn a few hexes
// ahead of them before, so no unit stood in one, and the Japanese could take them empty).
const bunkers = units.filter(u => u.side === US.side && !u.name.includes("reserve"))
  .flatMap(u => (u.weapon === "machine_gun" ? [[...u.pos]] : frontRow(u).filter((_, i) => i % 7 === 3)));

writeField({
  phases: [   // an exchange is about a minute; times and sources in the project's battle-phases research (round 2), rounded; (est.) marks an estimate
    { name: "The saddle is seized", at: 1, note: "About 02:30 on 9 March the 23rd Infantry's 2nd Battalion blows the wire and takes the saddle." },
    { name: "The 3rd Battalion follows", at: 6, note: "The 3rd Battalion follows in the same column and is caught by American artillery (est. minutes).", arrive: ["23rd Infantry, III Battalion (east slope)"] },
    { name: "The reserve counter-attacks", at: 571, note: "About noon on 9 March, C Company of the 1st Battalion, 145th, starts up Hill 700 against the saddle.", arrive: ["145th Infantry, 1st Battalion (reserve)"] },
    { name: "The 148th Infantry", at: 3531, note: "13:20 on 11 March: the 2nd Battalion, 148th Infantry, attacks the saddle; on 12 March its E and F Companies take the last pillboxes with flamethrowers (Miller, CARTWHEEL).", arrive: ["148th Infantry, 2nd Battalion (11-12 March)"] },
  ],
  ends: { at: 4171, why: "the line whole again by 12 March: midnight from 02:30 on the 9th" },
  objective: { at: [60, Math.round(crest(60))], side: 1, name: "the saddle in the line", radius: 7 },
  id: "bougainville-1944", name: "Hill 700, Bougainville, 8-12 March 1944", sides: ["Americans", "Japanese"], table: "bougainville-1944-all-hits",
  travel: { map: "bougainville-1944", place: "Hill 700", within: 2, sides: ["Americans", "Japanese"] },
  weather: "{cond: rain, wind: calm, dir: SE, ground: {mud: 1, snow: 0}}",
  grid, units, hexWorks: { bunker: bunkers, wire },
  support: [
    { name: "105 mm howitzers (field artillery)", side: 0, kind: "field", tubes: 12 },
    { name: "155 mm howitzers", side: 0, kind: "howitzer", tubes: 12 },
    { name: "81 mm mortars", side: 0, kind: "mortar", tubes: 6 },
    { name: "Japanese mountain guns", side: 1, kind: "field", tubes: 8 },
    { name: "Japanese mortars", side: 1, kind: "mortar", tubes: 6 },
  ],
  header: [
    `Hill 700 on the Torokina perimeter, Bougainville, March 1944, at 10 m a hex: ${COLS} x ${ROWS} hexes, about`,
    "1200 m east to west and 870 m north to south, north at the top: the ridge across the middle",
    "with a saddle between two knobs, the American pillbox line on its forward crest, wire and a",
    "cleared belt below it, and jungle beyond.",
    "Generated by tools/maps/make_bougainville_field.mjs: edit that file and re-run it rather than this one.",
    "The ridge, the saddle, the clearing and the line are drawn by hand to the shape the accounts",
    "give, not traced from any map; the deployment is the start of the attack, in our own words,",
    "with round numbers for play. Pillboxes are bunkers (cover 50%); the wire is slow to cross.",
    "",
    "What happened, briefly: on 8 March the Japanese 23rd Infantry came up through the jungle under",
    "its own guns and mortars. Shortly after midnight two companies probed the line at the saddle;",
    "at about 02:30 on 9 March the regiment came again in column of battalions, the 2nd leading,",
    "and seized several pillboxes. American artillery and mortars fired close in front of the line",
    "all night, and the 1st Battalion, 145th, was released from division reserve that day. Over",
    "the next days the 145th Infantry, with engineers, cleared the pillboxes one by one (two light",
    "tanks tried to help on the 9th but could not climb the hill); on 12 March E and F Companies of",
    "the 2nd Battalion, 148th Infantry, took the last of them with flamethrowers, and the line was",
    "whole again (Miller, CARTWHEEL). The Japanese dead lay",
    "thick on the slopes. The weather was hot and wet.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
