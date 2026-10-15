// Builds data/fields/easting73-1991.yaml: Eagle Troop cresting the rise at 73 Easting on the
// afternoon of 26 February 1991, on the field map at 10 m a hex. Run from this folder after
// editing: node make_easting73_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's own accounts
// of the battle (public domain) and the plain facts as they are summarised publicly. In a
// sandstorm that cut sight to a few hundred metres, Eagle Troop of the 2nd Armored Cavalry
// Regiment (nine M1A1 tanks and its Bradleys) fought through Iraqi positions in a cluster of
// buildings to the west, then at about 16:20 crested a low, almost unseen rise and came on a
// Tawakalna Division tank company dug in on its reverse slope, with BMPs in prepared positions
// and infantry in trenches; in some 23 minutes it destroyed the position (the accounts give 28
// tanks, 16 carriers and some 30 lorries) with no loss, then pushed on past its limit of
// advance to the high ground about a kilometre further east, where it destroyed a second group
// of T-72s. Ghost Troop fought to the north and Iron Troop to the south, off this map. The
// rise, the trenches and the high ground beyond are drawn by hand to that shape, not traced
// from any map, and are approximate; the deployment is the moment of cresting, in our own words,
// with round numbers for play. No minefields are drawn: the accounts we used name none here.
import { wobble, speckle, patch, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 200, ROWS = 120;                 // 2 km east to west (about 72.2 to 74.2 Easting), 1.2 km north to south
const E = 0, W = 3;                           // facings: east (a little north) and west (a little south)
const CREST = r => 80 + Math.round(wobble(r / 9, 0.3, 1.7));            // the low rise at 73 Easting, north to south
const BEYOND = [180, 58];                                                // the high ground about 74 Easting
function kind(c, r){
  if (Math.abs(c - CREST(r)) <= 2) return "h";                                                           // the rise: a fold of a few metres, dead ground behind it
  if (patch(c, r, { cx: BEYOND[0], cy: BEYOND[1], rx: 12, ry: 40, a: 0.8, b: 2.1 })) return "h";   // the high ground beyond
  return speckle(c, r, 25) ? "r" : ".";                                                                  // flat, hard desert, stony in places
}
const grid = groundGrid(COLS, ROWS, kind);
const TRENCH = [];
for (let r = 24; r <= 96; r++){
  if (r % 9 !== 0) TRENCH.push([CREST(r) + 8, r]);
}
const BUNKERS = [[CREST(36) + 8, 36], [CREST(60) + 8, 60], [CREST(84) + 8, 84]];
const isBunker = h => BUNKERS.some(b => b[0] === h[0] && b[1] === h[1]);

const US = { side: 0, facing: E }, IQ = { side: 1, facing: W };
const M1A1 = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank", nv: "thermal" };
const M3 = { ...M1A1, vehicle: "ifv" };                                   // the cavalry's M3 Bradleys (their TOW missiles not drawn apart from the gun)
const T72 = { quality: "regular", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank", nv: "none" };
const BMP = { ...T72, vehicle: "ifv" };
const LORRY = { ...T72, vehicle: "lorry" };
const GUARD = { quality: "regular", weapon: "rifle_assault", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("Eagle Troop's tanks (the troop commander and the north platoon)", US, 20, M1A1, 5, [38, 50], E),
  at("Eagle Troop's tanks (the south platoon)", US, 16, M1A1, 4, [36, 72], E),
  at("Eagle Troop's Bradleys (the north scout platoon)", US, 18, M3, 6, [24, 30], E),
  at("Eagle Troop's Bradleys (the south scout platoon)", US, 18, M3, 6, [22, 92], E),
  at("Tawakalna T-72s dug in behind the rise (north)", IQ, 40, T72, 10, [CREST(44) + 5, 44], W),
  at("Tawakalna T-72s dug in behind the rise (south)", IQ, 40, T72, 10, [CREST(76) + 5, 76], W),
  at("BMP-1s in their positions behind the rise", IQ, 24, BMP, 8, [CREST(60) + 14, 60], W),
  at("Iraqi infantry in the trenches", IQ, 120, GUARD, 14, [CREST(60) + 9, 60], W),
  at("Iraqi RPG teams", IQ, 20, { ...GUARD, weapon: "rpg" }, 3, [CREST(30) + 9, 30], W),
  at("Iraqi lorries behind the position", IQ, 16, LORRY, 8, [CREST(60) + 40, 60], W),
  at("T-72s on the high ground beyond (about 74 Easting)", IQ, 72, T72, 18, [BEYOND[0] - 4, BEYOND[1]], W),
];

writeField({
  phases: [   // an exchange is about a minute; times from docs and sources in the project's battle-phases research, rounded
    { name: "Over the rise", at: 1, note: "16:18: the troop commander's gunner kills the first T-72." },
    { name: "Through the trenches", at: 5, note: "16:22: eight more T-72s are destroyed; the troop fights through the trenches and BMPs." },
    { name: "The high ground beyond", at: 19, note: "About 16:36 the troop attacks into the main position; at 16:40 it halts at 73 Easting, the next line of tanks just out of range.", arrive: ["T-72s on the high ground beyond (about 74 Easting)"] },
  ],
  objective: { at: [CREST(60) + 6, 60], side: 0, name: "the Iraqi position behind the rise at 73 Easting", radius: 9 },
  id: "easting73-1991", name: "73 Easting: Eagle Troop crests the rise, 26 February 1991", sides: ["Coalition", "Iraqis"], table: "gulf-1991-us-wounds",
  travel: { map: "easting73-1991", place: "The rise at 73 Easting", within: 1, sides: ["Coalition", "Iraqis"] },
  weather: "{cond: sandstorm, wind: strong, dir: NW, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { trench: TRENCH.filter(h => !isBunker(h)), bunker: BUNKERS },
  support: [
    { name: "Eagle Troop's mortars", side: 0, kind: "mortar", tubes: 2 },
    { name: "2nd Squadron's howitzer battery", side: 0, kind: "howitzer", tubes: 8 },
    { name: "Tawakalna guns", side: 1, kind: "field", tubes: 4 },
  ],
  header: [
    `The rise at 73 Easting on the afternoon of 26 February 1991, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 2 km east to west`,
    "(from about 72.2 to 74.2 Easting on the military grid) and 1.2 km north to south, north at the top:",
    "flat, hard desert, a low rise running north to south across the left middle with the Iraqi trenches",
    "and dug-in tanks on its reverse (east) slope, hidden by it (dead ground), and the high ground about",
    "74 Easting on the right.",
    "Generated by tools/maps/make_easting73_field.mjs: edit that file and re-run it rather than this one.",
    "The rise, the trenches and the high ground are drawn by hand to the shape the accounts give, not",
    "traced from any map; the deployment is the moment before Eagle Troop crested the rise, just out",
    "of the dug-in tanks' sight, in our own words, with round numbers for play. A sandstorm: sight cut",
    "to 400 m, thermal sights included (a design choice; in the event the M1A1s' thermal sights saw",
    "further than the Iraqis' could), a strong wind. No aircraft fly in it. No minefields are drawn:",
    "the accounts we used name none on this ground.",
    "",
    "What happened, briefly: at about 16:20 on 26 February 1991 Eagle Troop, 2nd Armored Cavalry",
    "Regiment, came over a low rise in a sandstorm onto a Tawakalna Division tank company dug in on its",
    "far side. In about 23 minutes its nine M1A1s and its Bradleys destroyed the position without loss",
    "(the accounts give 28 tanks, 16 carriers and about 30 lorries; other tallies differ), then went on",
    "to the high ground about 74 Easting and destroyed more T-72s there.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
