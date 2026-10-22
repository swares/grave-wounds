// Builds data/maps/lundys-lane-1814.yaml: the Niagara campaign of July 1814 on the travel map,
// at 1 km a hex, from Lake Erie to Lake Ontario along the Niagara River. Run from this folder
// after editing: npm ci && node make_lundys_lane.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - forts, villages and the battlefield are placed at their modern sites (facts), Chippawa,
//   Queenston and the forts at the river's mouth nudged a little off the river to their own bank
//   at this 1 km scale;
// - the lake shores (which the land data counts as land) and the river are drawn by hand, after
//   the line of the modern shores; the creeks, the escarpment, woods and roads too. All are
//   approximate. The river is crossed only by boat: the crossings are marked as fords.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  chippawa: [43.058, -79.064], lundys: [43.091, -79.094], falls: [43.079, -79.076], queenston: [43.162, -79.062],
  lewiston: [43.172, -79.030], fortgeorge: [43.248, -79.075], fortniagara: [43.262, -79.050], forterie: [42.903, -78.927],
  blackrock: [42.935, -78.888], stdavids: [43.157, -79.110], schlosser: [43.077, -79.005], decou: [43.115, -79.205],
  streets: [43.036, -79.045], newark: [43.256, -79.088], crossing_q: [43.165, -79.047], crossing_g: [43.250, -79.062],
};

// ---------- the lakes (hand-drawn shores; the map runs past them to its edges) ----------
const WATER = [
  [[43.32, -79.32], [43.200, -79.320], [43.205, -79.250], [43.225, -79.150], [43.250, -79.085], [43.262, -79.068],
   [43.268, -79.040], [43.272, -78.960], [43.282, -78.870], [43.32, -78.86]],          // Lake Ontario
  [[42.84, -79.32], [42.882, -79.320], [42.870, -79.200], [42.875, -79.060], [42.893, -78.955], [42.898, -78.930],
   [42.890, -78.900], [42.880, -78.870], [42.84, -78.86]],                              // Lake Erie
];

// ---------- the river (impassable but by boat) and creeks ----------
const RIVERS = {
  niagara: [[42.898, -78.922], [42.940, -78.925], [42.980, -78.968], [43.030, -79.010], [43.055, -79.048], [43.075, -79.066],
            [43.100, -79.062], [43.130, -79.046], "crossing_q", [43.200, -79.052], "crossing_g", [43.266, -79.062]],
  niagara_east: [[42.925, -78.905], [43.000, -78.885], [43.040, -78.930], [43.062, -78.990], [43.072, -79.040]],   // the channel east of Grand Island
  chippawa_creek: [[43.030, -79.320], [43.045, -79.200], [43.050, -79.100], [43.054, -79.055]],
};
const STREAMS = [
  [[43.190, -79.260], [43.160, -79.230], "decou", [43.140, -79.180]],                     // Twelve Mile Creek country, approximate
  [[43.200, -79.130], [43.230, -79.100], "newark"],                                       // Four Mile Creek, approximate
];
const FORDS = ["crossing_q", "crossing_g", "forterie"];   // the crossings by boat

// ---------- the Niagara escarpment (hills) and woods (centre, radius km) ----------
const HILLS = [[[43.150, -79.060], 1.2], [[43.152, -79.100], 1.5], [[43.145, -79.150], 1.8], [[43.140, -79.200], 1.8], [[43.135, -79.260], 1.8],
  [[43.150, -79.020], 1.0]];
const WOODS = [[[43.100, -79.150], 2.5], [[43.010, -79.120], 3], [[42.960, -79.050], 2.5], [[43.050, -79.250], 2.5], [[43.110, -79.000], 2],
  [[42.990, -78.980], 2]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["forterie", [42.960, -78.950], [43.010, -79.005], "streets", "chippawa", "falls", "lundys", [43.120, -79.070], "queenston", [43.210, -79.072], "fortgeorge", "newark"],  // the Portage road
  ["lundys", [43.100, -79.150], "decou"], ["queenston", "stdavids", "decou"], ["stdavids", [43.200, -79.110], "newark"],
  ["chippawa", [43.066, -79.150], [43.062, -79.300]], ["blackrock", [42.990, -78.900], [43.050, -78.950], "schlosser", [43.110, -79.020], "lewiston", [43.230, -79.040], "fortniagara"], ["queenston", "crossing_q", "lewiston"], ["fortgeorge", "crossing_g", "fortniagara"],
];

const TOWNS = [];
const VILLAGES = ["chippawa", "queenston", "lewiston", "stdavids", "newark", "blackrock"];

const NAMES = { chippawa: "Chippawa", lundys: "Lundy's Lane", falls: "Niagara Falls", queenston: "Queenston", lewiston: "Lewiston",
  fortgeorge: "Fort George", fortniagara: "Fort Niagara", forterie: "Fort Erie", blackrock: "Black Rock", stdavids: "St. Davids",
  schlosser: "Fort Schlosser", decou: "DeCou's (approximate)", streets: "Street's Creek", newark: "Newark (burned)",
  crossing_q: "Queenston crossing", crossing_g: "Fort George crossing" };
const notes = {
  chippawa: "The American camp from 24 July, behind the creek where they had won on 5 July",
  lundys: "The lane over a low hill above the falls, with its churchyard: the British line and guns on 25 July",
  forterie: "Taken by the Americans on 3 July; their way home over the river",
  crossing_q: "Boats over the river below the gorge, Queenston to Lewiston",
  crossing_g: "Boats over the river's mouth, Fort George to Fort Niagara",
  fortgeorge: "The British fort at the river's mouth, where Drummond landed from York",
  fortniagara: "Held by the British since December 1813",
  newark: "The town the Americans burned in December 1813",
  streets: "Where the Americans beat Riall at Chippawa on 5 July",
};

const map = buildCampaign({
  id: "lundys-lane-1814", script: "make_lundys_lane.mjs", title: "The Niagara campaign of July 1814, from Lake Erie to Lake Ontario",
  name: "Niagara campaign, 1814 (Fort Erie to Fort George)",
  start_date: "1814-07-24", calendar: "gregorian", latitude: 43, climate: "great_lakes", climate_shift: -1,
  bounds: [-79.32, 43.30, -78.86, 42.86], midLat: 43.08, hexKm: 1, water: WATER,
  header: [
    "Forts, villages and the battlefield are at their modern places; the lake shores, the river,",
    "the creeks, the escarpment, woods and roads are drawn by hand and approximate. The river can",
    "be crossed only by boat, at the crossings marked as fords.",
    "",
    "What happened, briefly: in July 1814 Major General Jacob Brown's American army crossed the",
    "Niagara, took Fort Erie and beat General Riall's British at Chippawa. It pushed north to",
    "Queenston, then fell back to Chippawa. On 25 July Riall's advance guard took post on the hill",
    "at Lundy's Lane above the falls, and Lieutenant General Drummond came up from Fort George with",
    "more men. Winfield Scott's brigade attacked late in the day and was cut up in front of the",
    "British guns; in the dark the 21st Infantry rushed and took them, and the British counter-",
    "attacked again and again until near midnight. Both armies were worn out; the Americans fell",
    "back, leaving the guns, and later to Fort Erie. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["niagara", "niagara_east"], streams: STREAMS, fords: FORDS,
  woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { chippawa: "camp", fortgeorge: "objective", forterie: "objective", fortniagara: "objective" },
  depots: { fortgeorge: ["Britain"], fortniagara: ["Britain"], chippawa: ["United States"], forterie: ["United States"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "Scott's brigade", type: "foot", side: "United States", men: 1100, tools: true, at: "chippawa" },
    { name: "Ripley's brigade", type: "foot", side: "United States", men: 1200, tools: true, at: "chippawa" },
    { name: "Porter's volunteers", type: "foot", side: "United States", men: 500, tools: false, at: "chippawa" },
    { name: "American dragoons", type: "mounted", side: "United States", men: 100, tools: false, at: "chippawa" },
    { name: "Riall's advance guard", type: "foot", side: "Britain", men: 1000, tools: true, at: "queenston" },
    { name: "British light dragoons", type: "mounted", side: "Britain", men: 200, tools: false, at: "queenston" },
    { name: "Drummond's column", type: "foot", side: "Britain", men: 1500, tools: true, at: "fortgeorge" },
    { name: "Fort Niagara garrison", type: "foot", side: "Britain", men: 600, tools: true, at: "fortniagara" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
