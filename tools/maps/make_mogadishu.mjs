// Builds data/maps/mogadishu-1993.yaml: Mogadishu on 3-4 October 1993, on the travel map at
// 0.25 km a hex, from the airport in the south-west to the stadium in the north-east. Run from
// this folder after editing: npm ci && node make_mogadishu.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the US Army's account (The United States Army in Somalia, 1992-1994, a work of the US
//   government) for the facts: Task Force Ranger flew from its compound at the western end of
//   the airport at about 15:30 to a target near the Olympic Hotel, by the Bakara Market; the
//   first helicopter down came down about three blocks from the target, the second less than a
//   mile south; the 10th Mountain Division's quick reaction company was pinned near the K-4
//   traffic circle; the relief column formed at the airport and the New Port and went in by
//   National Street and Shalalawi Street; the force came out to the Pakistani stadium in the
//   north-east of the city by 06:30;
// - the target, the crash sites and the city's centre at their published positions, rounded;
//   the airport compound, K-4, the New Port, the market and the stadium are placed after the
//   account and approximate; the coast is drawn by hand past the airport, the old port and Lido beach;
// - the streets are drawn by hand through those places. They are approximate. All of the
//   land is built up (village) but the airport and the beaches.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  target: [2.0511, 45.3247], crash1: [2.0526, 45.3263], crash2: [2.0471, 45.3264], olympic: [2.0505, 45.3245], bakara: [2.0470, 45.3175],
  compound: [2.0140, 45.2990], k4: [2.0330, 45.3130], newport: [2.0330, 45.3390], stadium: [2.0590, 45.3360],
  north: [2.0720, 45.3220], west: [2.0500, 45.2900],   // where the militia come in from (not places)
};

// ---------- the streets (through places, in order) ----------
const ROADS = [
  ["compound", [2.0230, 45.3060], "k4", [2.0420, 45.3200], "olympic", "target", "north"],   // the airport road to K-4, and on north past the Olympic Hotel (Shalalawi Street)
  ["k4", [2.0350, 45.3250], "newport"],                                                     // to the New Port
  ["newport", [2.0420, 45.3320], "crash2", "crash1", [2.0560, 45.3310], "stadium"],         // National Street and on north-east to the stadium
  ["west", "bakara", "olympic"], ["k4", "bakara"],
];
// The sea: the coast drawn by hand past the airport's seaward edge, the old port and Lido beach
// (Natural Earth's coast is a few kilometres out at this scale).
const SEA = [[2.004, 45.284], [2.011, 45.297], [2.019, 45.313], [2.027, 45.331], [2.034, 45.344], [2.044, 45.357], [2.055, 45.369], [2.060, 45.376], [2.068, 45.392], [1.990, 45.392], [1.990, 45.280], [2.002, 45.280]];
const CLEARINGS = [[[2.0150, 45.3040], 0.6], [[2.0100, 45.2960], 0.4]];   // the airport's runway and apron

const NAMES = { target: "The target building", crash1: "Crash site 1 (Super 61)", crash2: "Crash site 2 (Super 64)", olympic: "The Olympic Hotel",
  bakara: "The Bakara Market", compound: "Task Force Ranger's compound (the airport)", k4: "The K-4 traffic circle", newport: "The New Port",
  stadium: "The Pakistani stadium" };
const notes = {
  target: "Task Force Ranger's assault force landed here at about 15:42 on 3 October 1993 and took 24 prisoners",
  crash1: "Super 61, a Black Hawk, came down here about three blocks from the target; some 90 Rangers and Delta held round it through the night",
  crash2: "Super 64 came down here, less than a mile south of the first; it was overrun and its pilot taken",
  k4: "The 10th Mountain Division's quick reaction company was pinned near here and fell back (approximate)",
  stadium: "Where the force came out to at about 06:30 on 4 October, after the run out on foot (approximate)",
  newport: "Where the relief column of Pakistani tanks, Malaysian armoured carriers and American infantry formed up (approximate)",
};

const map = buildCampaign({
  id: "mogadishu-1993", script: "make_mogadishu.mjs", title: "Mogadishu, 3-4 October 1993",
  name: "Mogadishu, 1993 (the airport to the stadium)",
  start_date: "1993-10-03", calendar: "gregorian", latitude: 2, climate: "horn_coast", climate_shift: 0, base: "v", coast: "drawn", water: [SEA],
  bounds: [45.285, 2.075, 45.375, 2.000], midLat: 2.04, hexKm: 0.25,
  header: [
    "The target, the crash sites and the Olympic Hotel are at their published positions, rounded;",
    "the airport compound, K-4, the New Port, the market and the stadium are placed after the US",
    "Army's account and approximate; the coast is drawn by hand past the airport, the old port and",
    "Lido beach, and the streets by hand. The city is built up throughout (village), streets and houses",
    "behind walls; the airport is open ground.",
    "",
    "What happened, briefly: on the afternoon of 3 October 1993 Task Force Ranger (Rangers and",
    "Delta Force, about 160 men, in helicopters and a convoy of trucks and Humvees) raided a",
    "building near the Olympic Hotel to seize two of Mohamed Farrah Aideed's lieutenants. As they",
    "left, militia of Aideed's Somali National Alliance brought down two Black Hawks with RPGs. Some",
    "90 Americans fought their way to the first crash and held round it through the night, with",
    "Little Bird gunships firing for them; the second crash site was overrun. After midnight a",
    "relief column of Pakistani tanks, Malaysian armoured carriers and the 10th Mountain Division's",
    "infantry fought through to the first crash, and at dawn they came out to the Pakistani",
    "stadium. Eighteen Americans were killed and some 80 wounded; Malaysian and Pakistani soldiers",
    "were killed and wounded too; Somali losses are put at 500 to 1,500. Numbers below are round",
    "figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: {}, majorRivers: [], streams: [], bridges: [], fords: [],
  clearings: CLEARINGS, woods: [], hills: [], mountains: [], roads: ROADS, towns: ["target", "bakara", "olympic"], villages: [],
  kinds: { target: "objective", crash1: "objective", compound: "camp" },
  depots: { compound: ["United States"], newport: ["United States"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "Task Force Ranger (Rangers and Delta)", type: "foot", side: "United States", men: 160, tools: false, at: "target" },
    { name: "Relief column (10th Mountain, with Malaysian and Pakistani armour)", type: "foot", side: "United States", men: 400, tools: false, at: "newport" },
    { name: "Somali National Alliance militia (the market)", type: "foot", side: "Somali National Alliance", men: 1000, tools: false, at: "bakara" },
    { name: "Somali National Alliance militia (the north)", type: "foot", side: "Somali National Alliance", men: 500, tools: false, at: "north" },
    { name: "Somali National Alliance militia (K-4 and the south)", type: "foot", side: "Somali National Alliance", men: 500, tools: false, at: "k4" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
