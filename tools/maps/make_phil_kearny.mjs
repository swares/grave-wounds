// Builds data/maps/phil-kearny-1866.yaml: Fort Phil Kearny on the Bozeman Trail, under the Big
// Horn Mountains, in Red Cloud's War (1866-68), on the travel map at 1 km a hex. Run from this
// folder after editing: npm ci && node make_phil_kearny.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the fort, the Fetterman Fight's ground and the Wagon Box Fight's site are placed after
//   their published positions, rounded (the fort 44.532 N 106.826 W; the Fetterman fight
//   44.571 N 106.839 W; the Wagon Box site on the plateau between the Pineys, 44.558 N
//   106.898 W); the corral's exact place was never agreed;
// - Pilot Hill south of the fort, the Sullivant Hills along the wood road, Lodge Trail Ridge to
//   the north, Peno Creek beyond it, the pinery about six miles north-west, Lake De Smet and the
//   Big Horns are placed after the descriptions of the fort's ground, approximate;
// - the Big and Little Piney creeks, the pine woods, the hills and the Bozeman Trail and the wood
//   road are drawn by hand through those places. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  fort: [44.532, -106.826], pilot: [44.523, -106.821], sullivant: [44.548, -106.858], lodge: [44.556, -106.833],
  fetterman: [44.571, -106.839], peno: [44.588, -106.828], wagonbox: [44.558, -106.898], pinery: [44.575, -106.925],
  desmet: [44.466, -106.745], crossing: [44.539, -106.826],
  lakota: [44.650, -106.800], cheyenne: [44.650, -106.880], south: [44.448, -106.760],   // where forces come in (not places)
};

// ---------- the creeks (brooks: wet, slow ground, crossed anywhere) ----------
const STREAMS = [
  [[44.567, -106.975], [44.567, -106.950], [44.563, -106.895], [44.552, -106.860], "crossing", [44.541, -106.800], [44.553, -106.760], [44.565, -106.690]],   // Big Piney
  [[44.540, -106.975], [44.545, -106.950], [44.551, -106.905], [44.540, -106.862], [44.528, -106.836], [44.538, -106.812]],                                // Little Piney
  [[44.560, -106.812], [44.578, -106.826], "peno", [44.620, -106.832], [44.660, -106.838]],                                                            // Peno Creek
];
const RIVERS = {}, BRIDGES = [], FORDS = [];

// ---------- woods, hills, the mountains, the lake ----------
const WOODS = [[[44.578, -106.948], 2.6], [[44.545, -106.972], 2.8], [[44.610, -106.962], 2.4], [[44.505, -106.968], 2.2]];   // pine on the foothills: the pinery
const HILLS = [[[44.548, -106.858], 1.2], [[44.552, -106.831], 0.8], [[44.562, -106.836], 0.8], [[44.571, -106.840], 0.7],   // Sullivant Hills; Lodge Trail Ridge
  [[44.523, -106.821], 0.5], [[44.600, -106.880], 1.5], [[44.500, -106.880], 1.5]];
const MOUNTAINS = [[[44.570, -107.045], 4], [[44.505, -107.040], 4], [[44.630, -107.040], 4]];
const WATER = [[[44.482, -106.752], [44.478, -106.736], [44.462, -106.732], [44.452, -106.744], [44.458, -106.756], [44.472, -106.758]]];   // Lake De Smet

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["south", [44.470, -106.770], [44.500, -106.800], "fort", "crossing", "lodge", "fetterman", "peno", [44.660, -106.840]],   // the Bozeman Trail
  ["fort", [44.540, -106.845], "sullivant", [44.556, -106.885], "wagonbox", "pinery"],                                    // the wood road
];

const TOWNS = ["fort"];
const VILLAGES = [];

const NAMES = { fort: "Fort Phil Kearny", pilot: "Pilot Hill", sullivant: "Sullivant Hills", lodge: "Lodge Trail Ridge",
  fetterman: "Fetterman battlefield", peno: "Peno Creek", wagonbox: "Wagon Box corral", pinery: "The pinery", desmet: "Lake De Smet" };
const notes = {
  fort: "The stockade of the Mountain District, built from July 1866 between the Piney creeks; burned by the Cheyenne after the Army left in 1868",
  pilot: "The lookout hill: its pickets signalled attacks on the wood trains",
  lodge: "Carrington ordered that no one pursue over this ridge",
  fetterman: "Where Fetterman's 81 men were killed on 21 December 1866 (approximate)",
  wagonbox: "Powell's corral of wagon boxes, 2 August 1867; its exact place was never agreed (approximate)",
  pinery: "The woodcutters' camps, about six miles north-west of the fort, where the logs for the fort were cut",
};

const map = buildCampaign({
  id: "phil-kearny-1866", script: "make_phil_kearny.mjs", title: "Fort Phil Kearny and the Bozeman Trail, 1866-1867",
  name: "Fort Phil Kearny, 1866 (Red Cloud's War)",
  start_date: "1866-12-20", calendar: "gregorian", latitude: 44, climate: "high_plains", climate_shift: -0.5, base: ".",
  bounds: [-107.06, 44.665, -106.68, 44.440], midLat: 44.55, hexKm: 1,
  header: [
    "The fort, the Fetterman battlefield and the Wagon Box site are at their published positions,",
    "rounded; the hills, creeks, woods and trails are drawn by hand and approximate. Open grass",
    "unless drawn otherwise.",
    "",
    "What happened, briefly: in 1866 the Army built three forts along the Bozeman Trail, the road",
    "to the Montana goldfields, through the hunting grounds of the Lakota, Cheyenne and Arapaho,",
    "against the will of their leaders. Red Cloud of the Oglala led the war against them. Through",
    "the summer and autumn war parties struck the wood trains and the trail. On 21 December 1866",
    "decoys drew Captain Fetterman's 81 men over Lodge Trail Ridge, where about a thousand",
    "warriors killed them all. On 2 August 1867 Captain Powell's 32 men, behind a corral of wagon",
    "boxes near the pinery, held off a much larger attack with new breech-loading rifles. In 1868",
    "the Army gave up the forts by the Treaty of Fort Laramie. Numbers below are round figures",
    "for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: [], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  woods: WOODS, hills: HILLS, mountains: MOUNTAINS, water: WATER, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { fort: "camp", fetterman: "objective", wagonbox: "objective", pinery: "objective" },
  depots: { fort: ["US Army"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "Fort Phil Kearny garrison (Carrington)", type: "foot", side: "US Army", men: 350, tools: true, at: "fort" },
    { name: "2nd Cavalry, Company C", type: "mounted", side: "US Army", men: 60, tools: false, at: "fort" },
    { name: "Wood train and its guard", type: "wagons", side: "US Army", men: 90, tools: true, at: "pinery" },
    { name: "Lakota war parties (Oglala, Minneconjou, Brulé)", type: "mounted", side: "Lakota, Cheyenne and Arapaho", men: 700, tools: false, at: "lakota" },
    { name: "Cheyenne and Arapaho warriors", type: "mounted", side: "Lakota, Cheyenne and Arapaho", men: 300, tools: false, at: "cheyenne" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
