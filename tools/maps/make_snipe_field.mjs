// Builds data/fields/snipe-1942.yaml: the 2nd Rifle Brigade's fight at Outpost Snipe, west of the
// Kidney feature at El Alamein, from first light to dark on Tuesday 27 October 1942, on the field
// map at 10 m a hex. Run from this folder after editing: node make_snipe_field.mjs (no packages
// needed).
//
// Sources, all plain fact, and the drawing is ours (project doc "snipe-research"): Wikipedia after
// Pitt and Latimer, the New Zealand official history, the US Intelligence Bulletin and the
// accounts after Lucas Phillips's Alamein (the committee that counted the wrecks). Snipe was a
// shallow oval depression about 1,000 by 500 yards, its long axis north-east to south-west, with
// camelthorn and soft sand: the only cover in thousands of yards of flat desert, a low ridge to the
// west (the Italian tanks came over it at 13:00) and one to the east (24th Armoured Brigade crested
// it at 07:30). The 19 six-pounders stood by company sectors: B Company's five to the south-east, C
// Company's four to the south-west, A Company's four to the north-west and north, 239 Battery's six
// to the north and north-east; 76 riflemen and 22 carriers with them, and 16 sappers. No source
// places the guns one by one, and the ridges, the hollow's depth and the strength and line of each
// Axis attack but those the accounts number are ours, with round numbers. The clock is Egyptian
// summer time (GMT+3), which the sources' first light at 06:15 and last round at 19:40 fit; whether
// the armies moved their clocks back at midnight on 26/27 October is not known.
import { N, S, wobble, groundGrid, unit, writeField, allRows } from "./field_lib.mjs";

const COLS = 200, ROWS = 160;                 // 2000 m west to east, about 1390 m north to south
const C = [100, 80];                          // the middle of the hollow
const NE = 0, NW = 2, SW = 3, SE = 5;         // facings (corners; see docs/units.md)
function kind(c, r){                          // flat desert with the two low ridges; the hollow and its camelthorn play as open ground (its depth is not known, and the rules' scrub would keep tanks out)
  const west = 30 + Math.round(wobble(r / 11, 0.9, 2.2) * 1.5), east = 178 + Math.round(wobble(r / 13, 2.1, 0.4) * 1.5);
  if (Math.abs(c - west) <= 1) return "h";                                          // the low ridge to the west, its crest
  if (Math.abs(c - west) <= 4) return "s";
  if (Math.abs(c - east) <= 1) return "h";                                          // and the one to the east
  if (Math.abs(c - east) <= 4) return "s";
  return ".";
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const RB = { side: 0, facing: N }, AX = { side: 1, facing: S };
const SIX_PDR = { quality: "veteran", weapon: "at_gun", kit: "ww2_rifleman", formation: "at_gun", mounted: false, prone: true, he: false };   // dug in by 03:45; armour-piercing only (no HE round for the 6-pounder until 1943: project doc "snipe-research", F2)
const RIFLES = { quality: "veteran", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };
const CARRIERS = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "apc" };   // Universal Carriers with their Brens
const SHERMANS = { quality: "regular", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank" };
const PANZERS = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank" };        // Panzer III and IV: heavy armour (50 mm fronts)
const M14 = { ...PANZERS, quality: "regular", armour: "light" };                                                                        // M13/40, M14/41, Semovente 75/18: 30 mm fronts
const BERSAGLIERI = { quality: "regular", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false };
const at = (u, facing) => ({ ...u, facing });
const units = [
  at(unit("239 Battery's six-pounders (north and north-east)", RB, 30, SIX_PDR, [6, 124, 49]), NE),
  at(unit("A Company's six-pounders (north-west and north)", RB, 20, SIX_PDR, [4, 84, 60]), NW),
  at(unit("C Company's six-pounders (south-west)", RB, 20, SIX_PDR, [4, 74, 108]), SW),
  at(unit("B Company's six-pounders (south-east)", RB, 25, SIX_PDR, [5, 116, 100]), SE),
  at(unit("A Company's riflemen", RB, 30, RIFLES, [10, 88, 66]), NW),
  at(unit("C Company's riflemen", RB, 30, RIFLES, [10, 78, 102]), SW),
  at(unit("B Company's riflemen", RB, 30, RIFLES, [10, 110, 94]), SE),
  unit("The carriers (scout and carrier platoons)", RB, 66, CARRIERS, [11, 95, 78]),
  unit("7th Field Squadron's sappers", RB, 16, { ...RIFLES, weapon: "rifle_service" }, [4, 100, 86]),
  at(unit("47th RTR (Shermans and Crusaders)", RB, 96, SHERMANS, [12, 182, 52]), NW),
  at(unit("41st RTR", RB, 96, SHERMANS, [12, 182, 104]), SW),
  at(unit("15th Panzer's tanks, passing north at dawn", AX, 60, PANZERS, [15, 128, 10]), SW),
  at(unit("Littorio's tanks and Semoventi, passing south at dawn (Stiffelmayer)", AX, 68, M14, [17, 120, 150]), NW),
  at(unit("Long-gunned Panzers from the south", AX, 100, PANZERS, [25, 40, 154]), N),
  unit("Bersaglieri of the Littorio", AX, 200, BERSAGLIERI, [24, 4, 92]),
  at(unit("A dozen Italian tanks from the west", AX, 48, M14, [12, 6, 70]), NE),
  at(unit("German tanks on the Italians' right", AX, 32, PANZERS, [8, 6, 120]), NE),
  at(unit("Italian tanks over the western ridge (Capitano Preve)", AX, 36, M14, [9, 14, 106]), NE),
  at(unit("Panzer IIIs against the north-west", AX, 60, PANZERS, [15, 20, 10]), SE),
  at(unit("German tanks of the evening attack, from the south-west", AX, 120, PANZERS, [30, 60, 152]), N),
  at(unit("Italian tanks of the evening attack", AX, 40, M14, [10, 140, 154]), N),
];
const waves = { 76: ["47th RTR (Shermans and Crusaders)", "41st RTR", "Long-gunned Panzers from the south"],
  226: ["Bersaglieri of the Littorio"], 256: ["A dozen Italian tanks from the west", "German tanks on the Italians' right"],
  406: ["Italian tanks over the western ridge (Capitano Preve)"],
  646: ["Panzer IIIs against the north-west", "German tanks of the evening attack, from the south-west", "Italian tanks of the evening attack", "Stukas (the attack before Rommel's counter-stroke)"] };

// The gun pits and slit trenches dug between 00:15 and 03:45 (project doc "snipe-research": the guns
// "dug in" by 03:45, the pits dug in the dark in soft sand, one gun "sunk into the sand"): a
// trench under every gun and rifle section of the battalion. Drawn to the units, not to any plan.
const pits = units.filter(u => u.side === 0 && u.prone).flatMap(u => allRows(u, 6));

writeField({
  phases: [   // an exchange is about a minute; Egyptian summer time (GMT+3): first light 06:15, sunrise 07:15, sunset 18:21 (project doc "snipe-research")
    { name: "First light", at: 1, note: "06:15: the German and Italian tank groups leave their leaguers and pass across the front; the guns engage them broadside at about 800 yards." },
    { name: "Civil dawn", at: 36, note: "06:50: light enough to lay a gun at 800 yards (the rules' dusk allows no aimed fire beyond 20 hexes; the guns were firing at the passing columns by then).", light: "day" },
    { name: "Sunrise", at: 61, note: "07:15." },
    { name: "24th Armoured Brigade", at: 76, note: "07:30: 47th and 41st RTR come over the ridge to the east (and fire on Snipe by mistake); long-gunned Panzers come up from the south to meet them.", arrive: waves[76] },
    { name: "The brigade pulls back", at: 166, note: "09:00: 47th RTR, down to five Shermans and six Crusaders, and 41st RTR go back behind the ridge." },
    { name: "Italian infantry", at: 226, note: "About 10:00: Bersaglieri mass to the west; the carriers go out at them.", arrive: waves[226] },
    { name: "A dozen Italian tanks", at: 256, note: "About 10:30: Italian tanks from the west, with Germans on their right.", arrive: waves[256] },
    { name: "Over the western ridge", at: 406, note: "About 13:00: eight Italian tanks and a Semovente come over the ridge at the south-west sector; Turner loads Sergeant Calistan's gun.", arrive: waves[406] },
    { name: "Rommel's counter-stroke", at: 646, note: "About 17:00: after Stukas and a five-minute bombardment, German and Italian tanks come on; fifteen Panzer IIIs turn on the north-west, where two guns are left working.", arrive: waves[646] },
    { name: "Sunset", at: 727, note: "18:21: the attackers fall back to 800 yards and fire until dark.", light: "dusk" },
    { name: "Dark", at: 780, note: "19:14: the moon does not rise until about 20:55.", light: "night" },
  ],
  ends: { at: 806, why: "the last anti-tank round fired at 19:40 as the light faded (Wikipedia); the attacks ended at 19:00 (Turner's citation)" },
  objective: { at: C, side: 1, name: "Snipe", radius: 22 },
  id: "snipe-1942", name: "Snipe, 27 October 1942 (El Alamein)", sides: ["British", "Germans and Italians"], table: "owens-wwii",
  travel: { map: "snipe-1942", place: "Snipe (the battlefield)", within: 1, sides: ["Eighth Army", "Axis"] },
  weather: "{cond: fair, wind: calm, dir: NW, light: dusk, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { trench: pits },
  support: [
    { name: "German guns and 88s", side: 1, kind: "field", tubes: 8 },
    { name: "Stukas (the attack before Rommel's counter-stroke)", side: 1, kind: "fighter_bomber", tubes: 20 },
  ],
  header: [
    `Snipe, 27 October 1942, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 2000 m west to east and 1390 m north to south, north at the`,
    "top: the oval hollow of Snipe in the middle (open ground, ringed by the objective), the low ridges",
    "to the west and east, flat desert with camelthorn all round.",
    "Generated by tools/maps/make_snipe_field.mjs: edit that file and re-run it rather than this one.",
    "The hollow is drawn to the accounts' size; its depth, the ridges and the guns' places inside their",
    "company sectors are ours. The Axis attacks the accounts number are drawn at those numbers; the",
    "rest, and where each came from, are ours, with round numbers. A tank unit is four men to a tank.",
    "Panzers play as heavy armour, the Italian M13s, M14s and Semoventi as light. The British artillery",
    "is not on call (the observer was lost at 04:00), and the friendly fire is not played. Clock: GMT+3.",
    "The camelthorn is not drawn: the rules' scrub would keep tanks out of it, and it stopped none here.",
  "The guns and riflemen are in the gun pits and slit trenches dug before dawn (a trench under each",
  "section, drawn to the units, not to any plan). The six-pounders fire armour-piercing only: there",
  "was no high-explosive round for them in October 1942.",
    "",
    "What happened, briefly: the 2nd Rifle Brigade went out from the Kidney feature on the night of",
    "26/27 October with 239 Battery's six-pounders and dug in at Snipe, short of the intended spot,",
    "between the leaguers of 15th Panzer and the Littorio. From first light the Axis tanks crossed in",
    "front of them and were shot up; 24th Armoured Brigade came up and went back; Italian and German",
    "attacks came in through the day, and Rommel's counter-stroke in the evening was stopped short.",
    "About 32 tanks and 5 self-propelled guns were left burnt out round the hollow (the committee's",
    "count, a month later), for 72 men killed and wounded of under 300. The battalion came out on",
    "foot that night with one gun.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
