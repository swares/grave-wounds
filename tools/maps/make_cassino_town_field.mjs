// Builds data/fields/cassino-town-1944.yaml: the New Zealand attack into the bombed town of
// Cassino and on Castle Hill, 15 March 1944, on the field map at 10 m a hex. Run from this folder
// after editing: node make_cassino_town_field.mjs (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the plain facts of the
// battle as the official histories give them and as they are summarised publicly. On the
// morning of 15 March about 435 bombers and some 750 guns (Blumenson) reduced the town to rubble and craters; the 25th
// New Zealand Battalion went in from the north down the road from Caira, with tanks of the 19th
// Armoured Regiment that the rubble and craters stopped, and took Castle Hill; German paratroops
// of the 1st Parachute Division came up out of the cellars and held the south of the town, the
// Continental Hotel and the slopes below the abbey; heavy rain that evening filled the craters.
// The ruins, the craters, the castle and the roads are drawn by hand, not traced from any map or
// photograph, and are approximate; the deployment is the attack going in, in our own words, with
// round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 140, ROWS = 120;                 // 1400 m east to west, about 1040 m north to south
const NORTH_ROAD = 84;                          // the road from Caira, straight down into the town from the north
const ROUTE6 = 96;                                                       // Route 6, along the south of the town
const RAPIDO = r => 132 + Math.round(wobble(r / 8, 1.3, 0.4) * 0.7);     // the Rapido along the east
const CASTLE = [28, 30], HOTEL = [50, 76], STATION = [104, 106];
function slopes(c, r){                        // Castle Hill and the massif's foot to the west, or null
  if (patch(c, r, { cx: CASTLE[0], cy: CASTLE[1], rx: 4, ry: 3 })) return "x";                      // the castle's ruins
  if (patch(c, r, { cx: CASTLE[0], cy: CASTLE[1], rx: 10, ry: 9, a: 0.4, b: 1.6 })) return speckle(c, r, 3) ? "r" : "h";   // Castle Hill
  if (c < 36 + wobble(r / 9, 0.3, 1.0) * 2) return speckle(c, r, 4) ? "F" : "h";                    // the massif's foot: terraces and scrub, rising to the abbey
  return null;
}
function lines(c, r){                         // the roads and the river, or null
  if (Math.abs(c - RAPIDO(r)) <= 1) return r === ROUTE6 || r === ROUTE6 + 1 ? "." : "w";            // the Rapido, bridged on Route 6
  if (r === ROUTE6 || r === ROUTE6 + 1) return ".";                                                  // Route 6
  if (r < 50 && c === NORTH_ROAD) return ".";                                        // the road from the north, still open outside the town
  return null;
}
function town(c, r){                          // the town: rubble and flooded craters; the hotel; the station
  if (patch(c, r, { cx: HOTEL[0], cy: HOTEL[1], rx: 3, ry: 2 })) return "B";                         // the Continental Hotel's shell
  if (patch(c, r, { cx: STATION[0], cy: STATION[1], rx: 8, ry: 5, a: 1.2, b: 0.3 })) return speckle(c, r, 4) ? "." : "T";   // the station and its yards
  if (patch(c, r, { cx: 78, cy: 70, rx: 46, ry: 32, a: 0.6, b: 2.0 })) return speckle(c, r, 9) ? "m" : "x";                 // the town: rubble, craters full of water
  return r > 40 && speckle(c, r, 5) ? "m" : ".";                                                      // the flat ground round it: fields, cratered and muddy nearer the town
}
const kind = (c, r) => slopes(c, r) ?? lines(c, r) ?? town(c, r);
const grid = groundGrid(COLS, ROWS, kind);

const NZ = { side: 0, facing: S }, DE = { side: 1, facing: N };
const KIWI = { quality: "veteran", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false };
const PARA = { quality: "veteran", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false, prone: true };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("25th New Zealand Battalion (into the town from the north)", NZ, 500, KIWI, 30, [70, 40], S),
  at("D Company, 25th Battalion (for Castle Hill)", NZ, 100, KIWI, 10, [CASTLE[0] + 6, 18], S),
  at("26th New Zealand Battalion (following up)", NZ, 400, KIWI, 30, [70, 20], S),
  at("19th Armoured Regiment (Shermans north of the town)", NZ, 32, { quality: "regular", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank" }, 4, [104, 30], S),
  at("German paratroops in the cellars (the north of the town)", DE, 80, PARA, 10, [72, 54], N),
  at("German paratroops in the ruins (the middle of the town)", DE, 100, PARA, 12, [80, 72], N),
  at("German paratroops at the Continental Hotel", DE, 60, PARA, 6, [HOTEL[0], HOTEL[1] - 3], 1),
  at("German paratroops by the station", DE, 60, PARA, 8, [STATION[0], STATION[1] - 7], N),
  at("German machine guns (the town)", DE, 15, MG, 3, [60, 60], N),
  at("German machine guns (below the abbey)", DE, 10, MG, 2, [38, 70], 0),
];

// The cellars the paratroops came up out of: a bunker under the middle of each paratroop unit's
// front row (they were drawn a few hexes off the units before, so no unit stood in one).
const CELLARS = units.filter(u => u.name.startsWith("German paratroops")).map(u => [...u.pos]);

writeField({
  phases: [   // an exchange is about a minute; times and sources in the project's battle-phases research (round 2), rounded; (est.) marks an estimate
    { name: "Into the rubble", at: 1, note: "Noon on 15 March: the bombing stops, the guns open and the 25th Battalion goes in from the north." },
    { name: "Castle Hill taken", at: 241, note: "About 16:00, four hours later: D Company of the 25th takes Castle Hill (Point 193)." },
    { name: "The 26th Battalion committed", at: 301, note: "Late afternoon (est.): the 26th Battalion is committed and takes three hours in the dark to reach Route 6.", arrive: ["26th New Zealand Battalion (following up)"] },
  ],
  ends: { at: 10801, why: "called off on 23 March: midnight from noon on the 15th" },
  objective: { at: CASTLE, side: 0, name: "Castle Hill", radius: 3 },
  id: "cassino-town-1944", name: "Cassino town and Castle Hill, 15 March 1944", sides: ["Allies", "Germans"], table: "owens-wwii",
  travel: { map: "cassino-1944", place: "Cassino", within: 1, sides: ["Allies", "Germans"] },
  weather: "{cond: overcast, wind: breeze, dir: S, ground: {mud: 2, snow: 0}}",
  grid, units,
  hexWorks: { bunker: CELLARS },
  support: [
    { name: "New Zealand and British field guns", side: 0, kind: "field", tubes: 36 },
    { name: "Medium and heavy guns", side: 0, kind: "howitzer", tubes: 12 },
    { name: "Fighter-bombers", side: 0, kind: "fighter_bomber", tubes: 12 },
    { name: "German mortars and Nebelwerfers", side: 1, kind: "mortar", tubes: 12 },
    { name: "German guns", side: 1, kind: "field", tubes: 8 },
  ],
  header: [
    `The town of Cassino and Castle Hill on 15 March 1944, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1400 m east to west and`,
    "1040 m north to south, north at the top: the bombed town in the middle, Castle Hill and its",
    "ruined castle at the upper left, the massif's foot rising to the abbey along the left edge,",
    "the road from Caira coming in from the north, Route 6 and the station to the south, the",
    "Rapido along the right.",
    "Generated by tools/maps/make_cassino_town_field.mjs: edit that file and re-run it rather than this one.",
    "The ruins, craters, castle and roads are drawn by hand, not traced from any map or photograph;",
    "the deployment is the attack going in, in our own words, with round numbers for play. The town",
    "is rubble (rubble) with flooded craters (marsh): tanks can keep only to the open road and the",
    "fields, and the paratroops' cellars are bunkers. Overcast, the ground already wet; that evening",
    "the rain came down.",
    "",
    "What happened, briefly: on the morning of 15 March 1944 about 435 bombers and some 750 guns reduced",
    "the town to rubble. The 25th New Zealand Battalion went in from the north with tanks of the",
    "19th Armoured Regiment, which the rubble and craters stopped short; D Company took Castle Hill.",
    "German paratroops came up out of the cellars and held the south of the town and the Continental",
    "Hotel. The fighting went on in the ruins for eight days, Gurkhas holding Hangman's Hill below",
    "the abbey, until the attack was called off on 23 March.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
