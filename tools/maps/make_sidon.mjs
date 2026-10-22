// Builds data/maps/sidon-1253.yaml: the raid on Sidon in 1253 on the travel map, at 1 km a hex,
// from Tyre and Sidon on the coast up to Beaufort and Banias. Run from this folder after
// editing: npm ci && node make_sidon.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the coastline is Natural Earth's 1:50m land (public domain, via the world-atlas package);
// - towns, castles and villages are placed at their modern coordinates (facts);
// - rivers, hills, mountains, woods and roads are drawn by hand and are approximate; the
//   course of events is told in our own words. The written record of the raid is thin: the
//   date and the numbers here are guesses for play.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  sidon: [33.5615, 35.3715], seacastle: [33.5672, 35.3690], tyre: [33.2705, 35.1960], sarepta: [33.4550, 35.2960],
  litanimouth: [33.3380, 35.2500], khardali: [33.3350, 35.5550], beaufort: [33.3255, 35.5295], nabatieh: [33.3780, 35.4840],
  marjayoun: [33.3600, 35.5900], banias: [33.2483, 35.6939], subeibe: [33.2528, 35.7136], hasbaya: [33.3980, 35.6850],
  jezzine: [33.5450, 35.5840], awali: [33.5960, 35.3870], zahrani: [33.4800, 35.3200],
};

// ---------- rivers (impassable but at a bridge, a ford or a town) ----------
const RIVERS = {
  litani: [[33.640, 35.700], [33.550, 35.680], [33.450, 35.620], [33.370, 35.580], "khardali", [33.306, 35.548], [33.298, 35.500], [33.312, 35.420],
           [33.330, 35.350], "litanimouth"],
  hasbani: [[33.450, 35.700], "hasbaya", [33.300, 35.650], [33.200, 35.630]],
  awali: [[33.620, 35.580], [33.615, 35.480], "awali"],
  zahrani: [[33.510, 35.500], [33.490, 35.400], "zahrani", [33.482, 35.290]],
};
const BRIDGES = ["khardali", "litanimouth"];

// ---------- hills, mountains and woods (centre, radius km) ----------
const HILLS = [];
for (let lat = 33.20; lat <= 33.66; lat += 0.06) for (let lon = 35.36; lon <= 35.76; lon += 0.07) HILLS.push([[lat, lon], 4.5]);
const MOUNTAINS = [[[33.560, 35.640], 5], [[33.620, 35.700], 5], [[33.450, 35.740], 3]];   // the Lebanon range's southern end, and Hermon's flank
const WOODS = [[[33.545, 35.560], 3], [[33.450, 35.520], 2.5], [[33.300, 35.420], 2]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  [[33.200, 35.170], "tyre", "litanimouth", "sarepta", "zahrani", "sidon", "awali", [33.660, 35.420]],          // the coast road
  ["sidon", [33.500, 35.440], "nabatieh", "beaufort", "khardali", "marjayoun", "banias", "subeibe"],
  ["marjayoun", "hasbaya", [33.480, 35.760]], ["banias", [33.280, 35.760]],                                       // towards Damascus
  ["sidon", [33.560, 35.480], "jezzine"],
];

const TOWNS = ["sidon", "tyre", "banias"];
const VILLAGES = ["sarepta", "nabatieh", "marjayoun", "hasbaya", "jezzine"];

const NAMES = { sidon: "Sidon", seacastle: "Sea Castle", tyre: "Tyre", sarepta: "Sarepta", litanimouth: "Litani bridge", khardali: "Khardali bridge",
  beaufort: "Beaufort", nabatieh: "Nabatieh", marjayoun: "Marj Ayyun", banias: "Banias", subeibe: "Subeibe", hasbaya: "Hasbaya",
  jezzine: "Jezzine", awali: "Awali mouth", zahrani: "Zahrani" };
const notes = {
  sidon: "Its walls were being rebuilt in 1253 when the raiders broke in; Louis IX later helped bury the dead here",
  seacastle: "The castle on its islet off the harbour, where some of the garrison held out",
  beaufort: "The lords of Sidon's castle above the Litani gorge",
  banias: "The Damascene frontier town the raid came from",
  subeibe: "The great castle above Banias",
  tyre: "Stands in for Louis IX's army, which was further south when Sidon fell and came afterwards",
  hasbaya: "The road on to Damascus, off the map to the east",
};

const map = buildCampaign({
  id: "sidon-1253", script: "make_sidon.mjs", title: "The raid on Sidon, 1253, from Banias to the coast",
  name: "Sidon, 1253 (Banias to the coast)",
  start_date: "1253-06-15", calendar: "julian", latitude: 33, climate: "mediterranean", climate_shift: 0,
  bounds: [35.15, 33.66, 35.77, 33.19], midLat: 33.42, hexKm: 1,
  header: [
    "The coastline is Natural Earth's (public domain); towns, castles and villages are at their",
    "modern places; rivers, hills, woods and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly: Louis IX of France stayed on in the Holy Land after his defeat in",
    "Egypt, rebuilding the crusader towns' walls. In 1253, while masons were at work on Sidon's,",
    "an army from Damascus came down from the hills and broke into the unfinished town. Hundreds",
    "were killed and many carried off; some of the garrison held out in the sea castle. Louis came",
    "afterwards, helped bury the dead with his own hands, and finished the walls. In 1260 a Mongol",
    "force sacked Sidon again. Two mass graves of young men, dug into the town ditch by the land",
    "castle, date from one of these attacks: the source of the Sidon wound tables. The date and",
    "the numbers here are guesses for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["litani"], bridges: BRIDGES,
  hills: HILLS, mountains: MOUNTAINS, woods: WOODS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { banias: "camp", sidon: "objective" },
  depots: { sidon: ["Franks"], banias: ["Damascus"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "Army of Damascus, horse", type: "mounted", side: "Damascus", men: 3000, tools: false, at: "banias" },
    { name: "Army of Damascus, foot", type: "foot", side: "Damascus", men: 1500, tools: true, at: "banias" },
    { name: "Sidon's garrison and builders", type: "foot", side: "Franks", men: 1500, tools: true, at: "sidon" },
    { name: "Beaufort's garrison", type: "foot", side: "Franks", men: 200, tools: true, at: "beaufort" },
    { name: "Louis IX's army", type: "mounted", side: "Franks", men: 2500, tools: true, at: "tyre" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
