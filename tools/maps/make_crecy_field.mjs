// Builds data/fields/crecy-1346.yaml: the battle of Crécy on the traditional field, the slope between
// Crécy and Wadicourt above the Vallée des Clercs, on the evening of Saturday 26 August 1346, on the
// field map at 10 m a hex. Run from this folder after editing: node make_crecy_field.mjs (no
// packages needed).
//
// Sources, all plain fact, and the drawing is ours (project doc "crecy-research"): the site as
// Cassini fixed it (1757) and as Preston reads it (Ayton and Preston, The Battle of Crécy, 2005):
// the English on the ridge facing east-south-east across the Vallée des Clercs, their right on
// Crécy and the Maye, their left towards Wadicourt, a line about 2,000 yards long; the valley's
// east side a steep bank, over 45 degrees and 2-6 m high, for about 2 km, open only at its ends,
// so that the French came up the valley from its south end by the Fontaine-sur-Maye road rather
// than straight over from the Estrées plateau (the way in is our reading of Preston, whose chapter
// we could not read). The wagon park by the wood behind the host with one entry (Froissart), the
// shallow pits in front (Baker, after DeVries), the Prince's battle some 300 yards ahead of the
// King's and Northampton's to its left and a little back (Gumm), the King's by the windmill. The
// strengths are Froissart's battles (800, 800 and 700 men-at-arms; 2,000, 1,200 and 2,000 archers;
// 1,000 Welsh), with the King's spearmen ours; the French are Sumption's (about 12,000 men-at-arms
// and 6,000 Genoese), split among the bodies the chroniclers name, with round numbers. The ridge,
// the valley, the bank and the terraces are drawn to those words, not traced from any survey.
import { N, S, wobble, patch, speckle, groundGrid, unit, stepHex, writeField } from "./field_lib.mjs";

// WEST is at the top: the columns run from south (left, Crécy) to north (right, Wadicourt), the rows
// from west (the English rear) to east (the Estrées plateau).
const COLS = 200, ROWS = 160;                 // about 2000 m south to north, 1390 m west to east
const SLOPE = c => 46 + Math.round(wobble(c / 9, 0.7, 1.9) * 1.5);     // where the ridge top falls away
const FLOOR = c => 80 + Math.round(wobble(c / 11, 2.2, 0.5) * 1.5);    // the valley floor
const BANK = c => 104 + Math.round(wobble(c / 13, 1.1, 2.6) * 1.5);    // the foot of the bank: its face is this row
const BANK_C0 = 46, BANK_C1 = 188;           // the bank's ends: open south (the way in) and marshy north
const MAYE = r => 4 + Math.round(wobble(r / 8, 0.3, 1.2) * 0.8);       // the Maye, down the south edge
const WINDMILL = [106, 33];
const hasBank = c => c >= BANK_C0 && c <= BANK_C1;

function town(c, r){                          // Crécy's edge, the Maye, Wadicourt (null: none)
  if (Math.abs(c - MAYE(r)) <= 1) return "m";                          // the Maye: small, wet, slow
  if (c < MAYE(r)) return speckle(c, r, 3) ? "o" : ".";               // its far bank
  if (patch(c, r, { cx: 16, cy: 4, rx: 12, ry: 12, a: 0.4, b: 1.7 })) return speckle(c, r, 3) ? "." : "T";   // the edge of Crécy
  if (patch(c, r, { cx: 198, cy: 2, rx: 9, ry: 9, a: 1.9, b: 0.2 })) return speckle(c, r, 3) ? "." : "T";    // the edge of Wadicourt
  return null;
}
function ridge(c, r){                         // the English side: the wood and the park behind, the ridge, the slope
  if (c === WINDMILL[0] && r === WINDMILL[1]) return "B";                                       // the windmill
  if (patch(c, r, { cx: 136, cy: 4, rx: 22, ry: 7, a: 2.3, b: 0.9 })) return speckle(c, r, 7) ? "o" : "F";   // the wood behind the host
  if (r < SLOPE(c)) return speckle(c, r, 11) ? "o" : "h";
  if (r < FLOOR(c)) return speckle(c, r, 6) ? "o" : "s";                                      // the slope: ripe wheat, scrub
  return null;
}
function beyond(c, r){                        // the valley floor, the bank and the plateau
  if (c > BANK_C1 && r >= FLOOR(c) - 6 && r <= BANK(c) + 6 && speckle(c, r, 2)) return "m";   // the valley's wet north end
  if (!hasBank(c) || r < BANK(c)) return speckle(c, r, 9) ? "o" : ".";
  if (r === BANK(c)) return "r";                                                              // the face of the bank
  return speckle(c, r, 8) ? "o" : "h";                                                        // the Estrées plateau
}
const kind = (c, r) => town(c, r) ?? ridge(c, r) ?? beyond(c, r);
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the bank, the terraces, the pits, the wagon park ----------
const bank = [];                              // [the high side (the plateau), the low side (the face)], every edge between them
for (let c = BANK_C0; c <= BANK_C1; c++){
  const top = [c, BANK(c) + 1];
  for (const d of [1, 2]){                    // NE, NW: the hexes above it
    const o = stepHex(top, d);
    if (o[0] >= BANK_C0 && o[0] <= BANK_C1 && o[1] <= BANK(o[0])) bank.push([top, o]);
  }
}
const terraces = [];                          // lynchets on the slope towards Crécy (an unsourced guide's; our drawing): [upper, lower]
for (const [row, c0, c1] of [[58, 12, 70], [68, 10, 56]]){
  for (let c = c0; c <= c1; c++){
    const lower = [c, row + Math.round(wobble(c / 7, 0.9, 0.1) * 0.6)];
    for (const d of [1, 2]) terraces.push([stepHex(lower, d), lower]);
  }
}
const pits = [];                              // the shallow pits, scattered before the line
for (let r = 54; r <= 60; r++) for (let c = 12; c <= 168; c++) if (speckle(c, r, 5)) pits.push([c, r]);
const wagons = [];                            // the carts round the horse park, by the wood, with one way in (on the east)
for (let a = 0; a < 360; a += 6){
  if (a > 60 && a < 120) continue;            // the entry
  const t = a * Math.PI / 180, h = [Math.round(95 + 16 * Math.cos(t)), Math.round(11 + 7 * Math.sin(t))];
  if (!wagons.some(w => w[0] === h[0] && w[1] === h[1])) wagons.push(h);
}

// ---------- the armies (pos is the middle of the front row; "south" here is east, down the slope) ----------
const EN = { side: 0, facing: S }, FR = { side: 1, facing: N };
const MAA = { quality: "veteran", weapon: "spear", kit: "transitional", formation: "close", mounted: false };
const ARCHERS = { quality: "veteran", weapon: "longbow", kit: "gambeson", formation: "open", mounted: false };
const WELSH = { quality: "regular", weapon: "spear", kit: "gambeson", formation: "close", mounted: false };
const GENOESE = { quality: "veteran", weapon: "crossbow", kit: "gambeson", formation: "open", mounted: false };   // their pavises left with the baggage
const LANCES = { quality: "veteran", weapon: "spear", kit: "transitional", formation: "close", mounted: true };
const LEVY = { quality: "green", weapon: "spear", kit: "gambeson", formation: "close", mounted: false };
const units = [
  unit("The Prince's archers, right", EN, 1000, ARCHERS, [30, 12, 52]),
  unit("The Prince of Wales's men-at-arms (with Warwick)", EN, 800, MAA, [20, 43, 52]),
  unit("Welsh spearmen with the Prince", EN, 1000, WELSH, [20, 43, 50]),
  unit("The Prince's archers, left", EN, 1000, ARCHERS, [30, 64, 52]),
  unit("Arundel's archers, right", EN, 600, ARCHERS, [20, 104, 48]),
  unit("Arundel's men-at-arms (the second battle)", EN, 800, MAA, [20, 125, 48]),
  unit("Arundel's archers, left", EN, 600, ARCHERS, [20, 146, 48]),
  unit("Edward III's men-at-arms (by the windmill)", EN, 700, MAA, [18, 86, 32]),
  unit("Edward III's archers", EN, 2000, ARCHERS, [40, 70, 28]),
  unit("The King's spearmen", EN, 1500, WELSH, [19, 118, 32]),
  unit("The Genoese crossbowmen (Doria and Grimaldi)", FR, 6000, GENOESE, [56, 10, 100]),
  unit("Alençon's men-at-arms", FR, 3000, LANCES, [30, 8, 122]),
  unit("John of Bohemia and his knights", FR, 500, LANCES, [13, 42, 122]),
  unit("Lorraine, Blois and Flanders", FR, 3000, LANCES, [30, 70, 130]),
  unit("Philip VI's battle", FR, 4000, { ...LANCES, quality: "regular" }, [40, 10, 140]),
  unit("French foot on the road", FR, 2000, LEVY, [25, 60, 150]),
];

writeField({
  phases: [   // an exchange is about a minute; the Genoese about 17:00 (local solar time, Sumption), sunset 18:40 (project doc "crecy-research")
    { name: "The Genoese come on", at: 1, note: "About 17:00, as the shower passes: the crossbowmen, tired, without their pavises and their strings wet, come up the valley with three shouts; the archers step forward and shoot 'so thick that it seemed snow'." },
    { name: "Alençon rides through them", at: 16, note: "The Genoese break; the Count of Alençon's men ride them down and on at the Prince's battle (when is our reading).", arrive: ["Alençon's men-at-arms"] },
    { name: "The King of Bohemia", at: 31, note: "The blind king is led in, his knights' reins tied to his; all are killed.", arrive: ["John of Bohemia and his knights"] },
    { name: "The charges go on", at: 61, note: "Lorraine, Blois and Flanders come up, contingent by contingent (Knighton counts sixteen charges in all; Blois dismounted his men for the last).", arrive: ["Lorraine, Blois and Flanders"] },
    { name: "Sunset", at: 101, note: "18:40: the sun goes down behind the English.", light: "dusk" },
    { name: "Philip's battle", at: 121, note: "The King's own battle and what foot had come up go in; two horses are killed under Philip and an arrow strikes his face (when is our reading).", arrive: ["Philip VI's battle", "French foot on the road"] },
    { name: "Moonlight", at: 135, note: "19:14: dark, under a moon about three-quarters full, low in the south; it sets about midnight.", light: "moonlit" },
  ],
  ends: { at: 241, why: "four hours from 17:00, into the moonlight (our cut: Knighton has the charges go on to about midnight, Froissart has the battle end about evensong)" },
  objective: { at: [95, 46], side: 1, name: "the English position between Crécy and Wadicourt", radius: 12 },
  id: "crecy-1346", name: "Crécy, 26 August 1346 (the Vallée des Clercs)", sides: ["English", "French"], table: "towton-1461-all-hits",
  period: "Hundred Years' War",
  travel: { map: "crecy-1346", place: "The Vallée des Clercs (the battlefield)", within: 1, sides: ["England", "France"] },
  up: "W",
  weather: "{cond: overcast, wind: breeze, dir: W, ground: {mud: 1, snow: 0}}",
  grid, units,
  hexWorks: { stakes: pits, wagon: wagons },
  edgeWorks: { bank: [...bank, ...terraces] },
  header: [
    `The battle of Crécy, 26 August 1346, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 2000 m south to north and 1390 m west to east,`,
    "WEST at the top: the wood and the wagon park behind, the English on the ridge and its slope from",
    "Crécy and the Maye (left) towards Wadicourt (right), the windmill behind the middle; the Vallée",
    "des Clercs across the middle, its far side a steep bank open only at its ends; the Estrées plateau",
    "below it, and the way in from the Fontaine-sur-Maye road at bottom left.",
    "Generated by tools/maps/make_crecy_field.mjs: edit that file and re-run it rather than this one.",
    "The ridge, the valley, the bank and the terraces are drawn to the accounts' words (Preston's bank;",
    "the terraces from an unsourced guide), not traced from any survey. The bank plays as an earth bank",
    "(slow to cross, high side the plateau's): the rules have no edge horses cannot cross, so it only",
    "slows them. The pits play as stakes. The English guns (ribalds under the carts) are not on the",
    "field. The strengths are Froissart's battles for the English and Sumption's figures for the",
    "French, split among the bodies the chroniclers name, with round numbers for play; most of the",
    "French foot never came up. Men-at-arms on both sides wear the coat of plates and mail of the 1340s.",
    "",
    "What happened, briefly: the English drew up on foot in the morning, their horses in the park,",
    "and waited without food. Philip VI came up from Abbeville through the day and, against advice,",
    "attacked in the evening, just after a thunder shower, the first rain in six weeks. The Genoese",
    "crossbowmen, sent in first without their pavises, were shot down and ridden down by Alençon's",
    "men; the French cavalry charged again and again, contingent by contingent, into the dark, and",
    "were broken on the archers and the Prince's battle. The King of Bohemia, Alençon, Lorraine, Blois",
    "and Flanders were killed, and the heralds counted 1,542 knights and squires dead before the",
    "Prince's line; the English lost perhaps forty men-at-arms. Philip left the field about midnight.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
