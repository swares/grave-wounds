// Builds data/maps/visby-1361.yaml: Valdemar IV's invasion of Gotland in July 1361 on the travel
// map, at 1 km a hex, from the west-coast landing to Visby. Run from this folder after
// editing: npm ci && node make_visby.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the coastline is Natural Earth's 1:50m land (public domain, via the world-atlas package);
// - villages and landmarks are placed at their modern coordinates, some (the landing places,
//   Ajmunds bridge, Fjäle mire) only to within a mile or so;
// - woods and roads are drawn by hand and are approximate; the course of the campaign is told
//   in our own words.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  visby: [57.639, 18.294], korsbetningen: [57.632, 18.302], vasterhejde: [57.598, 18.205], stenkumla: [57.555, 18.270],
  vall: [57.553, 18.365], roma: [57.512, 18.448], tofta: [57.500, 18.140], masterby: [57.470, 18.304],
  ajmunds: [57.466, 18.296], fjale: [57.476, 18.315], vastergarn: [57.440, 18.150], sanda: [57.430, 18.218],
  hejde: [57.430, 18.390], klintehamn: [57.387, 18.203], vivesholm: [57.380, 18.180], frojel: [57.335, 18.190],
  eksta: [57.290, 18.170], kronvald: [57.300, 18.140],
};

// ---------- woods and marsh (centre, radius km) ----------
const WOODS = [[[57.450, 18.230], 3], [[57.580, 18.320], 2.5], [[57.360, 18.300], 3], [[57.530, 18.200], 2], [[57.420, 18.330], 2],
  [[57.600, 18.420], 3], [[57.320, 18.260], 2.5]];
const MARSH = [[[57.478, 18.322], 1.5]];                     // Fjäle mire (dry that summer)

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["eksta", "frojel", "klintehamn", "sanda", "vastergarn", "tofta", "vasterhejde", "visby"],
  ["klintehamn", [57.430, 18.270], "masterby", "stenkumla", "visby"], ["hejde", "masterby"], ["roma", "vall", "visby"],
  ["roma", [57.490, 18.380], "masterby"], ["vivesholm", "klintehamn"],
];

const TOWNS = ["visby"];
const VILLAGES = ["vasterhejde", "stenkumla", "vall", "roma", "tofta", "masterby", "vastergarn", "sanda", "hejde", "klintehamn", "frojel", "eksta"];

const NAMES = { visby: "Visby", korsbetningen: "Korsbetningen", vasterhejde: "Västerhejde", stenkumla: "Stenkumla", vall: "Vall",
  roma: "Roma", tofta: "Tofta", masterby: "Mästerby", ajmunds: "Ajmunds bridge", fjale: "Fjäle mire", vastergarn: "Västergarn",
  sanda: "Sanda", hejde: "Hejde", klintehamn: "Klintehamn", vivesholm: "Vivesholm", frojel: "Fröjel", eksta: "Eksta", kronvald: "Kronvald" };
const notes = {
  vivesholm: "One likely landing place of the Danish fleet, 22 July 1361",
  kronvald: "The other likely landing place, on the Eksta coast",
  ajmunds: "The Gotlanders broke the bridge here to hold the Danes",
  fjale: "The Danes crossed the mire, dry that summer, and beat the Gotland levy, 24 or 25 July",
  masterby: "The battle of Mästerby, 24 or 25 July",
  roma: "Where the island's assembly met: the Gotland levies gathered from their districts",
  visby: "The walled Hanseatic town; its gates stayed shut during the battle outside, and it opened them two days later",
  korsbetningen: "Outside the ring wall by the south gate: the battle of 27 July and the mass graves",
};

const map = buildCampaign({
  id: "visby-1361", script: "make_visby.mjs", title: "Valdemar IV's invasion of Gotland, July 1361, from the west coast to Visby",
  name: "Gotland, 1361 (the landing to Visby)",
  start_date: "1361-07-22", calendar: "julian", latitude: 57, climate: "maritime", climate_shift: 0,
  bounds: [18.0, 57.68, 18.55, 57.26], midLat: 57.47, hexKm: 1,
  header: [
    "The coastline is Natural Earth's (public domain); villages and landmarks are at their modern",
    "places, some only to within a mile or so; woods and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly (dates Julian): Valdemar IV of Denmark took Öland, then landed on",
    "Gotland's west coast on 22 July 1361 with an army of perhaps 2,000 to 2,500, many of them",
    "hired Germans. The Gotland farmers gathered their district levies. They broke the bridge at",
    "Ajmunds, but the Danes crossed the mire beside it, dry in the hot summer, and beat them at",
    "Mästerby. The Danes reached Visby first; on 27 July the levies fought them outside the ring",
    "wall by the south gate, while the town kept its gates shut, and were cut down in their",
    "hundreds. Two days later Visby opened its gates and paid. The dead were buried in mass",
    "graves outside the wall, the source of the Visby wound tables. Numbers are disputed; those",
    "below are round figures for play.",
  ],
  places: P, names: NAMES, notes, woods: WOODS, marsh: MARSH, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { vivesholm: "camp", visby: "objective" },
  forces: [
    { name: "Valdemar's army", type: "foot", side: "Denmark", men: 2500, tools: true, at: "vivesholm" },
    { name: "Gotland levy, southern districts", type: "foot", side: "Gotland", men: 2000, tools: false, at: "hejde" },
    { name: "Gotland levy, northern districts", type: "foot", side: "Gotland", men: 3000, tools: false, at: "roma" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
