// Builds data/fields/aljubarrota-1385.yaml: the battle of Aljubarrota on the plateau of São Jorge,
// on the evening of 14 August 1385, on the field map at 10 m a hex. Run from this folder after
// editing: node make_aljubarrota_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours (project doc "aljubarrota-research"): Monteiro,
// Aljubarrota Revisitada (2001) and his 2006 and 2009 papers; Fernão Lopes's chronicle of João I
// through them; Juan I's own letter of 29 August 1385; the excavations of 1958-60 and 1999. The
// plateau runs north-south between two stream valleys 15-30 m deep (Vale de Madeiros to the west),
// leaving a front of about 300-400 m ("340 to 400 lances", Juan I); the Portuguese stood facing
// south with the chapel of São Jorge (built from 1393) about where their vanguard stood; a ditch
// of about 182 m wrapped the east side of the chapel's ground, a shallow ditch of about 330 m ran
// across the front, and some 830 pits (wolf-pits, 90 x 50 cm) lay in rows on the vanguard's right,
// in a zone 100-150 m deep. The valleys, the ditches and the pit field are drawn to those figures,
// not traced from any plan; the pits play as stakes (they stop horses and slow men). The strengths
// are Lopes's (his lances as men-at-arms), split among the bodies he names, with round numbers.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 100, ROWS = 130;                 // 1000 m east to west, about 1130 m north to south
const CHAPEL = [50, 44];
const FRONT_PT = 50, FRONT_CA = 78;           // the Portuguese front row (facing south); the Castilian vanguard's (facing north)
// The valleys' lines: they close in towards the Portuguese line and open out to the south.
const westValley = r => 24 - (r - FRONT_PT) * 0.08 + wobble(r / 7, 0.6, 1.8) * 0.7;
const eastValley = r => 77 + (r - FRONT_PT) * 0.08 + wobble(r / 6, 2.1, 0.4) * 0.7;

function valley(c, r, centre){                // the stream, its floor and its sides (null: not in this valley)
  const d = Math.abs(c - centre);
  if (d <= 1) return "m";                     // the stream: wet, slow
  if (d <= 3) return speckle(c, r, 3) ? "F" : "o";   // the valley floor: trees and brush
  if (d <= 8) return speckle(c, r, 5) ? "o" : "s";   // the valley sides, 12-25%
  return null;
}
function plateau(c, r){                       // the plateau: open, low vegetation and a few trees and orchards
  if (patch(c, r, { cx: 50, cy: 118, rx: 14, ry: 6, a: 0.7, b: 1.9 })) return speckle(c, r, 2) ? "o" : ".";   // orchards by Chão da Feira
  if (patch(c, r, { cx: 50, cy: 12, rx: 10, ry: 5, a: 1.4, b: 0.3 })) return ".";                         // the baggage park, behind
  return speckle(c, r, 7) ? "o" : ".";
}
const kind = (c, r) => valley(c, r, westValley(r)) ?? valley(c, r, eastValley(r)) ?? plateau(c, r);
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the field works ----------
const line = (a, b) => {                      // the hexes from a to b
  const n = Math.max(Math.abs(b[0] - a[0]), Math.abs(b[1] - a[1]));
  return Array.from({ length: n + 1 }, (_, i) => [Math.round(a[0] + (b[0] - a[0]) * i / n), Math.round(a[1] + (b[1] - a[1]) * i / n)]);
};
const bigDitch = [[47, 38], [53, 39], [56, 43], [56, 49], [59, 53]];   // about 182 m: north of the chapel, round its east side, ending SE
const frontDitch = [[33, FRONT_PT + 3], [67, FRONT_PT + 3]];          // about 330 m, shallow, across the front
const ditchPairs = pts => {                   // edge pairs along a line: [the defenders' side, the far side]
  const out = [];
  for (let i = 0; i + 1 < pts.length; i++) for (const h of line(pts[i], pts[i + 1])) out.push([h, [h[0] + 1, h[1]]]);
  return out;
};
const frontPairs = line(...frontDitch).map(h => [[h[0], h[1] - 1], h]);
const pits = [];                              // the pit field on the vanguard's right (west), about 1 ha
for (let r = FRONT_PT + 1; r <= FRONT_PT + 13; r++) for (let c = 27; c <= 38; c++) if ((r + c) % 2 === 0 || r % 3 === 0) pits.push([c, r]);
const wagons = [];                            // the baggage, behind the rearguard
for (let c = 42; c <= 58; c += 2) { wagons.push([c, 8]); wagons.push([c, 16]) }

// ---------- the armies (pos is the middle of the front row) ----------
const PT = { side: 0, facing: S }, CA = { side: 1, facing: N };
const MAA = { quality: "veteran", weapon: "spear", kit: "transitional", formation: "close", mounted: false };
const FOOT = { quality: "regular", weapon: "spear", kit: "gambeson", formation: "close", mounted: false };
const ARCHERS = { quality: "veteran", weapon: "longbow", kit: "gambeson", formation: "open", mounted: false };
const CROSSBOWS = { quality: "regular", weapon: "crossbow", kit: "gambeson", formation: "open", mounted: false };
const LANCES = { quality: "veteran", weapon: "spear", kit: "transitional", formation: "close", mounted: true };
const GINETES = { quality: "veteran", weapon: "spear", kit: "hauberk", formation: "open", mounted: true };
const units = [
  unit("Vanguard: the Constable's men-at-arms", PT, 600, MAA, [20, 39, FRONT_PT]),
  unit("Vanguard foot", PT, 1200, FOOT, [20, 39, FRONT_PT - 6]),
  unit("Right wing: the Ala dos Namorados", PT, 200, MAA, [6, 33, FRONT_PT]),
  unit("Left wing: Antão Vasques and the foreigners", PT, 200, MAA, [6, 59, FRONT_PT]),
  unit("Crossbowmen, right wing", PT, 400, CROSSBOWS, [6, 27, FRONT_PT]),
  unit("English archers, left wing", PT, 300, ARCHERS, [6, 65, FRONT_PT]),
  unit("Crossbowmen, left wing", PT, 400, CROSSBOWS, [4, 71, FRONT_PT]),
  unit("Rearguard: João I's men-at-arms", PT, 700, MAA, [22, 39, 32]),
  unit("Rearguard foot", PT, 1500, FOOT, [24, 38, 25]),
  unit("Baggage guard", PT, 300, CROSSBOWS, [14, 43, 13]),
  unit("French vanguard (on foot)", CA, 1200, MAA, [30, 30, FRONT_CA]),
  unit("Portuguese loyalists in the vanguard (João Afonso Telo)", CA, 400, MAA, [12, 60, FRONT_CA]),
  { ...unit("Left wing: the Master of Alcántara's ginetes", CA, 700, GINETES, [14, 6, FRONT_CA + 6]), via: [[8, 40], [20, 10], [40, 5]] },   // round the west of the field to the baggage (Lopes; the way is our reading)
  unit("Right wing: the Master of Calatrava (Pedro Álvares Pereira)", CA, 700, LANCES, [14, 84, FRONT_CA + 6]),
  unit("Juan I's main battle (three mounted bodies)", CA, 3000, { ...LANCES, quality: "regular" }, [40, 30, 104]),
];

writeField({
  phases: [   // an exchange is about a minute; the attack about 18:00 (local solar time), sunset 18:50 (project doc "aljubarrota-research")
    { name: "The bombards and the advance", at: 1, note: "About 18:00: the Castilian trons fire (one shot kills two squires, brothers) and the French and loyalist vanguard comes on into the pits and the shot from the wings." },
    { name: "The vanguards meet", at: 16, note: "In the gap between the valleys; the Castilian wings cannot come up level with their vanguard. Prisoners taken in the first clash are killed." },
    { name: "The main battle comes up", at: 31, note: "About 18:30: Juan I's three mounted bodies are funnelled onto the vanguard; the Master of Alcántara's ginetes ride round to the baggage (which way is our reading).", arrive: ["Juan I's main battle (three mounted bodies)"] },
    { name: "Sunset", at: 51, note: "18:50: the sun goes down; the royal standard has fallen and the rout begins.", light: "dusk" },
    { name: "Moonlight", at: 76, note: "19:15: dark, with a moon a little over half full in the south.", light: "moonlit" },
  ],
  ends: { at: 61, why: "less than an hour (Monteiro): 19:00 from 18:00" },
  objective: { at: CHAPEL, side: 1, name: "the Portuguese position at São Jorge", radius: 8 },
  id: "aljubarrota-1385", name: "Aljubarrota, 14 August 1385 (the plateau of São Jorge)", sides: ["Portuguese", "Castilians"], table: "towton-1461-all-hits",
  period: "Hundred Years' War",
  travel: { map: "aljubarrota-1385", place: "São Jorge (the battlefield)", within: 1, sides: ["Portugal", "Castile"] },
  weather: "{cond: fair, wind: breeze, dir: NW, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { stakes: pits, wagon: wagons },
  edgeWorks: { ditch: [...ditchPairs(bigDitch), ...frontPairs] },
  header: [
    `The battle of Aljubarrota on the plateau of São Jorge, 14 August 1385, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1000 m`,
    "east to west and 1130 m north to south, north at the top: the Portuguese facing south about the",
    "chapel's ground, with the ditches in front and the pit field on their right; a stream valley on",
    "each side; the Castilians coming up from Chão da Feira at the bottom.",
    "Generated by tools/maps/make_aljubarrota_field.mjs: edit that file and re-run it rather than this one.",
    "The valleys, the ditches and the pit field are drawn to the excavated and chronicle figures, not",
    "traced from any plan; the pits play as stakes. The strengths are Fernão Lopes's, split among the",
    "bodies he names, with round numbers for play; the Castilian crossbowmen and foot, left behind",
    "by the King, are not on the field, nor the bombards, which fired once to little effect. The",
    "wounds roll on Towton's table; the ossuary's bone evidence is its own table.",
    "",
    "What happened, briefly: the Portuguese, about a third as many, turned about in the afternoon",
    "to face the Castilians who had gone round them, and dug in between the valleys. Near sunset",
    "the French and the Portuguese who held for Castile came on, many on foot, into the pits and",
    "the shot of the English archers and the crossbowmen on the wings; the vanguards met in the",
    "narrow front, the Portuguese killed their first prisoners, and when Juan I's main battle came",
    "up it was funnelled in and broken. The royal standard fell and the Castilians fled in the dusk;",
    "the Master of Alcántara's riders, who had gone round to the baggage, were beaten off. Thousands",
    "more were killed in the rout that night and the next day.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
