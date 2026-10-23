// Builds data/fields/dornach-1499.yaml: the battle of Dornach, on the fields below Dorneck castle,
// on the afternoon and evening of 22 July 1499, on the field map at 10 m a hex. Run from this folder
// after editing: node make_dornach_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours (project doc "dornach-research"): Leutenegger
// and Winkler after the chronicles (Anshelm, Brennwald, Schilling, Tatarinoff's documents). The
// imperial army camped on the fields between Dornach and Arlesheim, on the castle side of the Birs,
// with its guns before Dorneck and "im Ramstel" and the Welsche Garde across the river at Reinach;
// the Confederates came down through the wood on the scarp below the Gempen about 16:00, took the
// guns (Fürstenberg was killed in the fight for them), were driven back towards the wood and the
// castle by the Welsche Garde and the Landsknechte, held through hours of fighting as the Bernese
// main body came out of the trees, and about 19:00 Lucerne and Zug came up from the Arlesheim side
// and the imperial army broke over the Birs. The map is turned with east at the top, so the Swiss
// come down it as they came down the scarp: north (Arlesheim) is on the left, the Birs at the
// bottom. The scarp, the castle's spur, the village, the river and the camp are drawn by hand to
// that shape, not traced from any map; the contingents' strengths are the chronicles' (Leutenegger)
// and the imperial army's split among its parts is ours, with round numbers.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 120, ROWS = 140;                 // 1200 m north (left) to south (right), about 1210 m east (top) to west (bottom)
const scarpFoot = c => 32 + Math.round(wobble(c / 9, 0.4, 1.7) * 2);   // where the wooded scarp meets the plain
const BIRS = c => 131 + Math.round(wobble(c / 8, 1.3, 0.2) * 1.2);      // the river, near the bottom
const BRIDGE = 40;                            // Dornachbrugg's bridge, north-west of the village
const CASTLE = [95, 14], GUNS = [66, 60];

function river(c, r){                         // the Birs and the far bank (null: east of it)
  const b = BIRS(c);
  if (r >= b - 1 && r <= b + 1) return Math.abs(c - BRIDGE) <= 1 ? "." : "m";   // shallow, fordable; the bridge
  if (r > b + 1) return speckle(c, r, 3) ? "o" : ".";                          // the meadows towards Reinach
  return null;
}
function scarp(c, r){                         // the wood on the scarp, Dorneck on its spur (null: below it)
  if (patch(c, r, { cx: CASTLE[0], cy: CASTLE[1], rx: 4, ry: 3 })) return "T";                        // the castle
  if (patch(c, r, { cx: CASTLE[0], cy: CASTLE[1] + 2, rx: 9, ry: 7, a: 0.8, b: 1.6 })) return "h";     // its spur
  const f = scarpFoot(c);
  if (r < f - 6) return speckle(c, r, 6) ? "s" : "F";                                                 // the wood, dense undergrowth
  if (r < f) return speckle(c, r, 3) ? "o" : "s";                                                     // the lower slope, scrub
  return null;
}
function plain(c, r){                         // the fields, the village and the camp
  if (patch(c, r, { cx: 88, cy: 46, rx: 9, ry: 6, a: 1.2, b: 0.5 })) return speckle(c, r, 3) ? "." : "T";   // Oberdornach and its church
  if (patch(c, r, { cx: BRIDGE, cy: 122, rx: 6, ry: 4, a: 0.3, b: 2.1 })) return speckle(c, r, 3) ? "." : "T";   // Dornachbrugg
  if (c < 9 && r > 38 && r < 62) return speckle(c, r, 3) ? "." : "T";                                 // the edge of Arlesheim
  if (patch(c, r, { cx: 45, cy: 72, rx: 7, ry: 4, a: 2.0, b: 0.9 })) return "h";                     // a rise (later "Blood Hill")
  return speckle(c, r, 8) ? "o" : ".";                                                                // harvest fields
}
const kind = (c, r) => river(c, r) ?? scarp(c, r) ?? plain(c, r);
const grid = groundGrid(COLS, ROWS, kind);

const wagons = [];                            // the camp's carts and tents, towards the river
for (let c = 22; c <= 82; c += 6) wagons.push([c, 108], [c + 3, 112]);

// ---------- the armies (pos is the middle of the front row; "south" here is west, down the slope) ----------
const CH = { side: 0, facing: S }, IM = { side: 1, facing: N };
const PIKES = { quality: "veteran", weapon: "pike", kit: "brigandine_sallet", formation: "close", mounted: false };
const HALBERDS = { quality: "veteran", weapon: "halberd", kit: "jack_sallet", formation: "close", mounted: false };
const GUNS_HAND = { quality: "regular", weapon: "handgun", kit: "none", formation: "open", mounted: false };
const LANDSKNECHTE = { quality: "regular", weapon: "pike", kit: "jack_sallet", formation: "close", mounted: false };
const LEVIES = { quality: "green", weapon: "spear", kit: "gambeson", formation: "close", mounted: false };
const HORSE = { quality: "veteran", weapon: "spear", kit: "full_plate", formation: "close", mounted: true };
const BATTERY = { quality: "regular", weapon: "artillery_smoothbore", kit: "none", formation: "battery", mounted: false, guns: "smoothbore" };
const units = [
  unit("Solothurn's vanguard (Niklaus Conrad)", CH, 1000, PIKES, [20, 62, 30]),
  unit("Solothurn's halberdiers", CH, 500, HALBERDS, [12, 84, 32]),
  unit("Bernese under Kaspar von Stein", CH, 500, HALBERDS, [12, 46, 30]),
  unit("Zürich (Kaspar Göldli)", CH, 400, PIKES, [12, 30, 30]),
  unit("Bern's main banner (Rudolf von Erlach)", CH, 3000, PIKES, [36, 40, 18]),
  unit("Lucerne and Zug", CH, 1000, PIKES, [16, 2, 36]),
  unit("Dorneck garrison (Benedikt Hugi)", CH, 20, { ...GUNS_HAND, quality: "veteran" }, [2, CASTLE[0] - 1, CASTLE[1] + 2]),
  unit("Imperial guns before Dorneck and in the Ramstel", IM, 100, BATTERY, [5, GUNS[0], GUNS[1]]),
  unit("Fürstenberg and the knights", IM, 300, HORSE, [10, 52, 64]),
  unit("Imperial handgunners", IM, 300, GUNS_HAND, [10, 74, 62]),
  unit("Landsknechte in the camp", IM, 3000, LANDSKNECHTE, [36, 36, 80]),
  unit("Geldern Landsknechte", IM, 2000, { ...LANDSKNECHTE, quality: "veteran" }, [26, 78, 84]),
  unit("Swabian and Alsatian levies", IM, 3000, LEVIES, [40, 22, 100]),
  unit("The Welsche Garde (Louis de Vaudrey)", IM, 1000, HORSE, [24, 28, 138]),
];

writeField({
  phases: [   // an exchange is about a minute; the attack about 16:00 (local solar time), sunset 19:36 (project doc "dornach-research")
    { name: "Out of the wood", at: 1, note: "About 16:00: the vanguard comes down through the undergrowth on the camp in the afternoon heat and goes for the guns; Fürstenberg rides towards the noise and is killed." },
    { name: "The Welsche Garde comes over the Birs", at: 31, note: "The horse from Reinach and the Landsknechte counter-attack; the vanguard falls back towards the wood and the castle (when the horse came is our reading).", arrive: ["The Welsche Garde (Louis de Vaudrey)"] },
    { name: "Bern's main banner comes out of the trees", at: 46, note: "The Bernese main body, slowed by the undergrowth, comes down to the fight (when is our reading).", arrive: ["Bern's main banner (Rudolf von Erlach)"] },
    { name: "Lucerne and Zug", at: 181, note: "About 19:00: some 1,000 men of Lucerne and Zug come up from the Arlesheim side with horns and shouting.", arrive: ["Lucerne and Zug"] },
    { name: "Sunset", at: 217, note: "19:36: the sun goes down behind the Birs; the rout goes over the river.", light: "dusk" },
    { name: "Moonlight", at: 253, note: "20:12: dark, under a full moon rising in the east-south-east.", light: "moonlit" },
  ],
  ends: { at: 241, why: "four to five hours of fighting (Leutenegger): 20:00 from 16:00" },
  objective: { at: GUNS, side: 0, name: "the imperial guns and camp", radius: 6 },
  id: "dornach-1499", name: "Dornach, 22 July 1499 (the fields below Dorneck)", sides: ["Swiss Confederates", "Imperials"], table: "dornach-1499-all-hits",
  travel: { map: "dornach-1499", place: "The fields below Dorneck (the battlefield)", within: 1, sides: ["Swiss Confederates", "Swabian League and the Empire"] },
  up: "E",
  weather: "{cond: fair, wind: calm, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { wagon: wagons },
  header: [
    `The battle of Dornach, 22 July 1499, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1200 m north to south and 1210 m east to west,`,
    "EAST at the top: the wooded scarp below the Gempen across the top, Dorneck castle on its spur at",
    "top right, Oberdornach below it, the fields and the imperial camp in the middle, Arlesheim's",
    "edge on the left, the Birs and Dornachbrugg's bridge at the bottom, the Welsche Garde beyond.",
    "Generated by tools/maps/make_dornach_field.mjs: edit that file and re-run it rather than this one.",
    "The scarp, the castle, the villages, the river and the camp are drawn by hand to the shape the",
    "accounts give, not traced from any map; the Confederate contingents are the chronicles'",
    "strengths, the imperial army's split among its parts is ours, with round numbers for play. The",
    "river is shallow and fordable (marsh); the Swiss have none of their guns, left behind on the",
    "Gempen. Fourteen of the imperial army's 21 captured guns are not on the field.",
    "",
    "What happened, briefly: the Confederates watched the camp from the heights through the morning,",
    "came down through the wood about four in the afternoon and fell on it while many were resting",
    "in the heat, taking the guns; the imperial commander Heinrich von Fürstenberg was killed. The",
    "Welsche Garde and the Landsknechte drove the vanguard back towards the wood and the castle,",
    "and for hours the fight swayed over the fields as the Bernese came down. About seven in the",
    "evening Lucerne and Zug came up from the Arlesheim side, and the imperial army broke and fled",
    "over the Birs, leaving its guns, its camp and some 3,000 dead; the Swiss had sworn to take no",
    "prisoners.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
