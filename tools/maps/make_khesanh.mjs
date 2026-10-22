// Builds data/maps/khesanh-1968.yaml: Khe Sanh, January to April 1968, on the travel map at
// 0.5 km a hex, from the Laotian border and Lang Vei east along Route 9 past the combat base and
// its hill outposts. Run from this folder after editing: npm ci && node make_khesanh.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the siege as the US Marine Corps' history gives them and as they are
//   summarised publicly: the 26th Marines, with the 1st Battalion, 9th Marines and the 37th ARVN
//   Ranger Battalion, held the combat base on its plateau and the hills to the north-west (881
//   South, 861, 861A, 558) from 21 January 1968; the North Vietnamese 325C Division was to the
//   north-west and the 304th to the south-west, with guns on Co Roc across the border in Laos;
//   Khe Sanh village fell on 21 January and the Lang Vei Special Forces camp on Route 9 to tanks on
//   the night of 6-7 February; the base was supplied by air through the fog of the dry season
//   until Operation Pegasus came up Route 9 in April;
// - the base, the hills, the village and Lang Vei placed after the accounts and approximate;
//   the rivers, the road and the high ground drawn by hand. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  base: [16.655, 106.728], h881s: [16.680, 106.680], h881n: [16.700, 106.684], h861: [16.684, 106.706], h861a: [16.690, 106.716],
  h558: [16.676, 106.726], h950: [16.706, 106.714], village: [16.627, 106.735], langvei: [16.613, 106.668], coroc: [16.592, 106.590],
  northwest: [16.730, 106.650], southwest: [16.600, 106.625], east: [16.655, 106.815],
};
const RIVERS = {
  raoquan: [[16.745, 106.738], [16.705, 106.740], [16.672, 106.746], [16.648, 106.760], [16.640, 106.790], [16.646, 106.820]],
  xepon: [[16.745, 106.600], [16.700, 106.605], [16.650, 106.598], [16.610, 106.610], [16.580, 106.612]],
};
const STREAMS = [[[16.700, 106.690], [16.672, 106.700], [16.650, 106.712], [16.640, 106.740]]];
const FARMS = [[P.village, 1.0], [[16.640, 106.715], 0.8], [P.base, 0.9]];
const CLEARINGS = [[[16.668, 106.750], 0.8], [[16.620, 106.690], 0.7]];
const HILLS = [[P.h861, 0.8], [P.h861a, 0.6], [P.h558, 0.6], [[16.640, 106.680], 1.2], [[16.615, 106.770], 1.4]];
const MOUNTAINS = [[P.h881s, 1.0], [P.h881n, 1.2], [P.h950, 1.2], [P.coroc, 1.6], [[16.730, 106.700], 2.0], [[16.725, 106.780], 2.2], [[16.600, 106.730], 1.6]];
const ROADS = [
  [[16.618, 106.598], "langvei", [16.620, 106.700], "village", [16.640, 106.760], [16.648, 106.790], "east"],
  ["village", [16.640, 106.730], "base"],
];
const BRIDGES = [[16.618, 106.604]].map((p, i) => { P["bridge" + i] = p; return "bridge" + i });
const NAMES = {
  base: "Khe Sanh combat base", h881s: "Hill 881 South", h881n: "Hill 881 North", h861: "Hill 861", h861a: "Hill 861A", h558: "Hill 558",
  h950: "Hill 950", village: "Khe Sanh village", langvei: "Lang Vei Special Forces camp", coroc: "Co Roc (Laos)",
};
const notes = {
  base: "The 26th Marines' base on its plateau, with the airstrip; besieged from 21 January to early April 1968 (approximate)",
  h861a: "E Company, 2nd Battalion, 26th Marines held it against a night attack on 5 February 1968 (approximate)",
  h881s: "India and Mike Companies, 3rd Battalion, 26th Marines held it all through the siege (approximate)",
  langvei: "Overrun by North Vietnamese infantry with PT-76 tanks on the night of 6-7 February 1968 (approximate)",
  coroc: "North Vietnamese guns fired on the base from these cliffs across the border (approximate)",
};
const map = buildCampaign({
  id: "khesanh-1968", script: "make_khesanh.mjs", title: "Khe Sanh, January to April 1968",
  name: "Khe Sanh, 1968 (the base and its hills)",
  start_date: "1968-01-20", calendar: "gregorian", latitude: 17, climate: "annamite", climate_shift: 0, base: "F",
  bounds: [106.580, 16.745, 106.820, 16.580], midLat: 16.66, hexKm: 0.5,
  header: [
    "The base, the hills, the village and Lang Vei are placed after the accounts and approximate;",
    "the rivers, Route 9 and the high ground are drawn by hand. Steep hills under jungle and",
    "elephant grass, the base and the village's coffee plantations on the plateau; the Rao Quan",
    "runs south past the base, the Xe Pon along the border with Laos.",
    "",
    "What happened, briefly: on 21 January 1968 the North Vietnamese attacked Hill 861 and began",
    "shelling the Khe Sanh combat base, held by the 26th Marines and an ARVN Ranger battalion. The",
    "village fell that day, Hill 861A was attacked on 5 February, and Lang Vei was overrun by tanks",
    "on the 7th. For eleven weeks the base and its hills were supplied by air through the fog while",
    "B-52s and artillery hammered the hills around them; Operation Pegasus relieved it in April.",
    "Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: [], streams: STREAMS, bridges: BRIDGES, fords: [],
  farms: FARMS, clearings: CLEARINGS, woods: [], hills: HILLS, mountains: MOUNTAINS, roads: ROADS,
  towns: [], villages: ["village", "langvei"],
  kinds: { base: "camp", h861a: "objective", h881s: "objective" },
  depots: { base: ["United States and ARVN"], coroc: ["North Vietnamese"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "26th Marines, 1/9 Marines and the 37th ARVN Rangers", type: "foot", side: "United States and ARVN", men: 6000, tools: true, at: "base" },
    { name: "Marines on the hill outposts (881 South, 861, 861A, 558)", type: "foot", side: "United States and ARVN", men: 1200, tools: true, at: "h861a" },
    { name: "Lang Vei: Special Forces and CIDG", type: "foot", side: "United States and ARVN", men: 500, tools: true, at: "langvei" },
    { name: "North Vietnamese 325C Division", type: "foot", side: "North Vietnamese", men: 8000, tools: true, at: "northwest" },
    { name: "North Vietnamese 304th Division", type: "foot", side: "North Vietnamese", men: 8000, tools: true, at: "southwest" },
    { name: "North Vietnamese guns on Co Roc", type: "wagons", side: "North Vietnamese", men: 400, tools: true, at: "coroc" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
