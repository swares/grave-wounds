// Builds data/fields/keating-2009.yaml: Combat Outpost Keating at dawn on 3 October 2009, on the
// field map at 10 m a hex. Run from this folder after editing: node make_keating_field.mjs (no
// packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's investigation
// and the award citations as summarised publicly. The outpost lay on a small flat by the
// Landay-Sin river where the Kushtoz stream comes in, with steep slopes rising on every side and
// Urmul village across the river; its buildings, the Afghan soldiers' quarters, the mortar pit, the
// trucks at the guard posts and the wire were all overlooked; at about 06:00 some 300 insurgents
// opened fire from the slopes with rocket launchers, machine guns, mortars and recoilless rifles,
// pinned the mortar pit, drove the Afghan soldiers back, broke in through the east and set the
// buildings alight; the Americans fell back to a defensive line round the barracks and the
// command post, then counterattacked to take back the outpost, while Apaches and jets struck the
// slopes. The flat, the buildings, the river, the stream, the village and the slopes are drawn by
// hand to that shape, not traced from any map or photograph, and are approximate; the deployment
// is the attack at dawn, in our own words, with round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField, at } from "./field_lib.mjs";

const COLS = 120, ROWS = 110;                 // 1200 m east to west, about 950 m north to south
const RIVER = r => 24 + Math.round(wobble(r / 7, 0.9, 1.4) * 0.8);       // the Landay-Sin, north to south down the west
const STREAM = c => 70 + Math.round(wobble(c / 6, 0.3, 1.2) * 0.6);      // the Kushtoz, in from the east to the river
const COP = [50, 56], URMUL = [12, 52];
function water(c, r){                         // the river, the stream and the bridge to Urmul (null: neither)
  if (Math.abs(c - RIVER(r)) <= 2) return r === COP[1] - 6 ? "." : "w";
  if (c > RIVER(r) && Math.abs(r - STREAM(c)) <= 1) return "w";
  return null;
}
function flat(c, r){                          // the outpost and its flat, Urmul's houses and terraces (null: the slopes)
  if (patch(c, r, { cx: COP[0], cy: COP[1], rx: 14, ry: 10, a: 0.5, b: 1.2 })) return speckle(c, r, 4) ? "T" : ".";   // the outpost's buildings, trucks and yards
  if (patch(c, r, { cx: URMUL[0], cy: URMUL[1], rx: 8, ry: 10 })) return speckle(c, r, 3) ? "r" : "T";               // Urmul
  if (patch(c, r, { cx: COP[0] - 6, cy: COP[1] + 2, rx: 24, ry: 15, a: 1.1, b: 0.4 })) return speckle(c, r, 4) ? "r" : ".";   // the valley floor
  return null;
}
function slopes(c, r){                        // steep mountainside on every side: rock, scrub and deodar
  const up = Math.min(Math.abs(r - COP[1]), Math.abs(c - COP[0]) * 1.4);
  if (up < 30) return speckle(c, r, 3) ? "o" : "r";                       // the lower slopes: rock and scrub
  return speckle(c, r, 3) ? "h" : "F";
}
const kind = (c, r) => water(c, r) ?? flat(c, r) ?? slopes(c, r);
const grid = groundGrid(COLS, ROWS, kind);
const cube = ([c, r]) => { const q = c - (r - (r & 1)) / 2; return [q, r, -q - r] };
const hdist = (a, b) => { const x = cube(a), y = cube(b); return Math.max(Math.abs(x[0] - y[0]), Math.abs(x[1] - y[1]), Math.abs(x[2] - y[2])) };
const WIRE = [];
for (let r = COP[1] - 13; r <= COP[1] + 13; r++){
  for (let c = COP[0] - 18; c <= COP[0] + 18; c++){
    if (hdist([c, r], COP) === 15 && c > RIVER(r) + 2 && (c + r) % 3 !== 0) WIRE.push([c, r]);
  }
}

const US = { side: 0, facing: N }, IN = { side: 1, facing: S };
const TROOPER = { quality: "veteran", weapon: "rifle_assault", kit: "interceptor", formation: "extended", mounted: false, prone: true };
const GUNS = { quality: "veteran", weapon: "machine_gun", kit: "interceptor", formation: "mg", mounted: false, prone: true };
const ANA = { quality: "green", weapon: "rifle_assault", kit: "pasgt", formation: "extended", mounted: false, prone: true };
const FIGHTER = { quality: "regular", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, prone: true };
const RPG = { ...FIGHTER, weapon: "rpg" };
const PKM = { quality: "regular", weapon: "machine_gun", kit: "none", formation: "mg", mounted: false, prone: true };
const units = [
  at("B Troop, 3-61 Cavalry (the barracks and command post)", US, 30, { ...TROOPER, fac: true }, 6, [COP[0] - 3, COP[1] - 4], N),
  at("B Troop (the guard posts and trucks)", US, 15, TROOPER, 4, [COP[0] + 7, COP[1] - 2], 0),
  at("B Troop's machine guns (the trucks)", US, 8, GUNS, 2, [COP[0] - 8, COP[1] + 5], 4),
  at("Afghan soldiers (the east side)", US, 20, ANA, 4, [COP[0] + 10, COP[1] + 4], 0),
  at("Insurgents on the north slope", IN, 100, FIGHTER, 16, [COP[0], COP[1] - 19], S),
  at("Insurgents on the east slope", IN, 80, FIGHTER, 12, [COP[0] + 28, COP[1] + 2], 3),
  at("Insurgents in Urmul and across the river", IN, 50, FIGHTER, 8, [URMUL[0] + 3, URMUL[1] - 11], 0),
  at("Insurgents on the south slope", IN, 50, FIGHTER, 10, [COP[0] + 4, COP[1] + 24], N),
  at("Insurgent RPG teams (north)", IN, 20, RPG, 3, [COP[0] - 13, COP[1] - 16], S),
  at("Insurgent machine guns (east)", IN, 10, PKM, 2, [COP[0] + 23, COP[1] - 4], 3),
];

writeField({
  ends: { at: 361, why: "the outpost retaken by the afternoon: 12:00 from 06:00" },
  objective: { at: COP, side: 1, name: "the outpost", radius: 8 },
  id: "keating-2009", name: "Combat Outpost Keating, 3 October 2009", sides: ["Coalition", "Insurgents"], table: "oif-oef-2001-wounds",
  travel: { map: "keating-2009", place: "Combat Outpost Keating", within: 1, sides: ["Coalition", "Insurgents"] },
  weather: "{cond: fair, wind: calm, light: dusk, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { wire: WIRE },
  support: [
    { name: "The outpost's 120 mm and 60 mm mortars", side: 0, kind: "mortar", tubes: 2 },
    { name: "Apaches (AH-64)", side: 0, kind: "gunship", tubes: 2 },
    { name: "A-10s, F-15Es and a B-1B (later in the morning)", side: 0, kind: "fighter_bomber", tubes: 3 },
    { name: "Insurgent mortars and recoilless rifles", side: 1, kind: "mortar", tubes: 4 },
  ],
  header: [
    `Combat Outpost Keating at dawn on 3 October 2009, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1200 m east to west and 950 m`,
    "north to south, north at the top: the outpost on its flat in the middle, ringed with wire, the",
    "Landay-Sin down the left with the bridge to Urmul, the Kushtoz coming in from the east below the",
    "outpost, and steep slopes of rock, scrub and deodar rising on every side.",
    "Generated by tools/maps/make_keating_field.mjs: edit that file and re-run it rather than this one.",
    "Light cover (scrub, key o): the scrub on the lower slopes among the rock; the deodar above is woods.",
    "The flat, the buildings, the river, the stream, the village and the slopes are drawn by hand to",
    "the shape the accounts give, not traced from any map or photograph; the deployment is the",
    "attack at dawn, in our own words, with round numbers for play. Observation Post Fritsche, on",
    "the ridge to the south-east, is off this field.",
    "",
    "What happened, briefly: at about 06:00 on 3 October 2009 some 300 insurgents opened fire on the",
    "outpost from the slopes, pinned the mortar pit, drove the Afghan soldiers back and broke in from",
    "the east, setting the buildings alight. The Americans held a line round the barracks and the",
    "command post, then counterattacked and took the outpost back by the afternoon, with Apaches and",
    "jets striking the slopes. Eight Americans were killed and more than twenty wounded.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
