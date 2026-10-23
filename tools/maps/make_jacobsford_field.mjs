// Builds data/fields/jacobsford-1179.yaml: the storm of the Templar castle at Jacob's Ford at dawn on
// Thursday 30 August 1179, on the field map at 10 m a hex. Run from this folder after editing:
// node make_jacobsford_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours (project doc "jacobsford-research"): the castle
// as the excavators give it (Ellenblum et al. 1998; Raphael 2023): about 150 by 50 m, its long side
// north-south on the north part of a low tell, walls about 4 m thick and some 10 m high, a south
// gate, an east postern and one square tower at the south-west corner; the Jordan along the east
// foot of the tell, curving round its south to the ford about 200 m below the castle. Saladin's
// men mined the north-east corner, and the second mine's fire brought it down at sunrise; a timber
// wall the Franks had built behind it caught fire in the wind, and the castle was stormed. The
// garrison is al-Qadi al-Fadil's (80 knights with their squires, 15 chiefs with 50 men each,
// craftsmen, who are not on the field); no source gives Saladin's numbers, so the attackers are ours, with round numbers.
// The tell, the river, the breach and the camp are drawn to those figures, not traced from a plan.
import { N, S, wobble, patch, speckle, groundGrid, unit, stepHex, writeField } from "./field_lib.mjs";

const COLS = 40, ROWS = 70;                   // 400 m east to west, about 600 m north to south
const C0 = 14, C1 = 18, R0 = 22, R1 = 38;     // the castle's hexes: 50 m by about 150 m
const RIVER = r => 30 + Math.round(wobble(r / 5, 0.6, 1.4) * 0.8);     // the Jordan, east of the tell
const FORD_ROW = 62;
const inCastle = (c, r) => c >= C0 && c <= C1 && r >= R0 && r <= R1;
const inBreach = (c, r) => c >= C1 - 2 && r <= R0 + 2;                 // the north-east corner the mine brought down

function water(c, r){                         // the Jordan: down the east side, then west round the south of the tell
  if (r < FORD_ROW - 3) return Math.abs(c - RIVER(r)) <= 1 ? "w" : null;
  const bend = FORD_ROW + Math.round((c - 20) * 0.15 + wobble(c / 4, 1.1, 0.3) * 0.6);
  if (c > RIVER(r) + 1 || Math.abs(r - bend) > 1) return null;
  return Math.abs(c - 20) <= 2 ? "m" : "w";                            // the ford: shallow water
}
function tell(c, r){                          // the castle, the tell and its slopes
  if (inCastle(c, r)){
    if (inBreach(c, r)) return "x";                                     // the fallen wall
    if (c === C0 && r === R1) return "B";                               // the south-west tower
    if (patch(c, r, { cx: 15, cy: 30, rx: 1.2, ry: 2 })) return "T";    // the vaulted kitchen and stores
    return ".";
  }
  if (patch(c, r, { cx: 16, cy: 32, rx: 9, ry: 22, a: 0.9, b: 2.0 })) return "h";   // the tell
  if (patch(c, r, { cx: 16, cy: 32, rx: 12, ry: 25, a: 0.4, b: 1.3 })) return "s";
  return null;
}
function ground(c, r){                        // the faubourg's tents and lime heaps, fields, brush by the river
  if (patch(c, r, { cx: 10, cy: 46, rx: 6, ry: 6, a: 1.7, b: 0.4 })) return speckle(c, r, 2) ? "o" : ".";
  if (c > RIVER(r) - 4) return speckle(c, r, 2) ? "o" : ".";
  return speckle(c, r, 6) ? "o" : ".";
}
const kind = (c, r) => water(c, r) ?? tell(c, r) ?? ground(c, r);
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the walls (edges between a castle hex and the hex outside it), the gates ----------
const wall = [], gate = [];
const SOUTH_GATE = [16, R1], POSTERN = [C1, 30];
for (let r = R0; r <= R1; r++) for (let c = C0; c <= C1; c++){
  if (inBreach(c, r)) continue;
  for (let d = 0; d < 6; d++){
    const o = stepHex([c, r], d);
    if (inCastle(o[0], o[1]) || inBreach(o[0], o[1])) continue;
    const isGate = (c === SOUTH_GATE[0] && r === SOUTH_GATE[1] && o[1] > r) || (c === POSTERN[0] && r === POSTERN[1] && d === 0);
    (isGate ? gate : wall).push([[c, r], o]);
  }
}

// ---------- the armies (pos is the middle of the front row) ----------
const TP = { side: 0, facing: N }, AY = { side: 1, facing: S };
const KNIGHTS = { quality: "veteran", weapon: "sword", kit: "hauberk", formation: "close", mounted: false };
const SERGEANTS = { quality: "regular", weapon: "spear", kit: "hauberk", formation: "close", mounted: false };
const CROSSBOWS = { quality: "regular", weapon: "crossbow", kit: "gambeson", formation: "open", mounted: false };
const STORMERS = { quality: "veteran", weapon: "sword", kit: "hauberk", formation: "close", mounted: false };
const ARCHERS = { quality: "veteran", weapon: "bow", kit: "gambeson", formation: "open", mounted: false };
const VOLUNTEERS = { quality: "green", weapon: "spear", kit: "gambeson", formation: "close", mounted: false };
const units = [
  unit("Templar knights and their squires", TP, 160, KNIGHTS, [3, 15, 26]),
  unit("Sergeants (the fifteen companies)", TP, 450, SERGEANTS, [4, C0 + 1, 29]),
  unit("Crossbowmen and archers", TP, 300, CROSSBOWS, [3, C0 + 2, 33]),
  unit("The storming column (Farrukh-Shah)", AY, 1000, STORMERS, [3, 16, 20]),
  unit("Archers north of the castle", AY, 600, ARCHERS, [10, 2, 20]),
  unit("Archers across the river", AY, 400, ARCHERS, [5, 33, 36]),
  unit("Volunteers and foot (the second wave)", AY, 1500, VOLUNTEERS, [6, 15, 8]),
];

writeField({
  phases: [   // an exchange is about a minute; sunrise 05:35 local solar time on 30 August 1179 (project doc "jacobsford-research")
    { name: "The wall falls", at: 1, note: "Sunrise: the second mine's fire brings down the north-east corner; the timber wall behind it catches fire in the wind, and the storming column goes in." },
    { name: "Full light", at: 25, note: "The sun is up over the Golan.", light: "day" },
    { name: "The second wave", at: 31, note: "The volunteers and the rest of the foot come up to the breach (when is our reading).", arrive: ["Volunteers and foot (the second wave)"] },
  ],
  ends: { at: 121, why: "the storm and the killing after it, a morning's work: two hours from sunrise (our reading; no source gives its length)" },
  objective: { at: [16, 30], side: 1, name: "the castle at Jacob's Ford", radius: 4 },
  id: "jacobsford-1179", name: "Jacob's Ford, 30 August 1179 (the storm of the castle)", sides: ["Templars", "Ayyubids"], table: "sidon-1253-all-hits",
  travel: { map: "jacobsford-1179", place: "Chastellet (the castle at Jacob's Ford)", within: 1, sides: ["Kingdom of Jerusalem", "Ayyubids"] },
  weather: "{cond: fair, wind: breeze, dir: W, light: dusk, ground: {mud: 0, snow: 0}}",
  grid, units,
  edgeWorks: { wall, gate },
  header: [
    `The storm of the castle at Jacob's Ford, 30 August 1179, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 400 m east to west and 600 m`,
    "north to south, north at the top: the castle on the tell in the middle, its north-east corner",
    "fallen (rubble), the gate in the south wall, the postern on the east and the tower at the",
    "south-west; the Jordan down the east side and round the south, with the ford below the castle.",
    "Generated by tools/maps/make_jacobsford_field.mjs: edit that file and re-run it rather than this one.",
    "The castle is drawn to the excavated figures, the tell, river and camp by hand; the walls are",
    "stone-wall edges (no crossing but the breach and the gates), the breach rubble. The garrison is",
    "al-Qadi al-Fadil's; Saladin's numbers are not known and the attackers are ours, with round numbers",
    "for play. The wounds roll on Sidon's table (the castle's own five skeletons are too few for one).",
    "",
    "What happened, briefly: Saladin came to the ford on Saturday 25 August, took the outer works that",
    "evening, set up mangonels and mined the north-east corner. The first mine's fire failed and the",
    "wall stood; he paid a dinar for every skin of water carried to put the fire out so his sappers",
    "could dig deeper, fired it again, and at sunrise on Thursday the wall fell. The timber wall behind",
    "it burned in the wind, the commander threw himself into the fire, and the castle was stormed. Some",
    "700 were taken, many killed on the road; Saladin had the apostates and the bowmen put to death.",
    "Baldwin IV's army, gathering at Tiberias, came too late.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
