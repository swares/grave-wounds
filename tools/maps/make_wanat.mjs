// Builds data/maps/wanat-2008.yaml: the Waygal valley from the Pech to Wanat, July 2008, on the
// travel map at 0.5 km a hex. Run from this folder after editing: npm ci && node make_wanat.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the US Army's accounts (the Combat Studies Institute's study of the battle, and the Army's
//   account for the Medal of Honor to Staff Sergeant Ryan Pitts, works of the US government) for
//   the facts: 2nd Platoon, Chosen Company, 2nd Battalion, 503rd Infantry, with engineers,
//   Marine trainers and a platoon of the Afghan National Army, began a vehicle patrol base at the
//   edge of Wanat in the Waygal valley on 8-9 July 2008, about 5 miles from Camp (Forward
//   Operating Base) Blessing on the Pech, which fired 155 mm guns in its support; about 200
//   fighters attacked it at about 04:20 on 13 July;
// - Wanat at its published position, rounded; Blessing, the Pech and the upper valley's
//   villages placed after the accounts and approximate;
// - the mountains, the river, the terraced fields, the woods and the track up the valley are
//   drawn by hand. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  wanat: [35.0525, 70.9075], blessing: [34.993, 70.868], nangalam: [34.986, 70.850], waygal: [35.110, 70.930], aranas: [35.085, 70.985],
  bella: [35.070, 70.870],
  northeast: [35.110, 70.990], north: [35.120, 70.920],   // where the fighters come in from (not places)
};

// ---------- the rivers ----------
const RIVERS = {
  waygal: [[35.125, 70.930], "waygal", [35.080, 70.915], [35.055, 70.905], [35.030, 70.890], [35.005, 70.870], [34.988, 70.856]],
  pech: [[34.995, 70.800], [34.988, 70.840], [34.984, 70.865], [34.975, 70.900], [34.968, 70.940], [34.960, 71.000]],
};
const BRIDGES = [[35.050, 70.903], [34.986, 70.852], [35.025, 70.887]].map((p, i) => { P["bridge" + i] = p; return "bridge" + i });
const STREAMS = [[[35.065, 70.960], [35.058, 70.930], [35.054, 70.912]]];   // a side stream down to Wanat from the east

// ---------- mountains everywhere; the valley floor terraced and farmed, woods on the slopes ----------
const FARMS = [[P.wanat, 0.9], [[35.080, 70.917], 0.7], [P.waygal, 0.8], [[35.030, 70.888], 0.6], [[35.005, 70.868], 0.6], [P.nangalam, 1.0], [[34.975, 70.920], 0.8], [P.aranas, 0.5], [P.bella, 0.4]];
const WOODS = [[[35.060, 70.880], 1.4], [[35.040, 70.935], 1.6], [[35.095, 70.960], 1.5], [[35.015, 70.910], 1.2], [[35.090, 70.895], 1.2]];
const HILLS = [[[35.050, 70.922], 0.6], [[35.068, 70.900], 0.5]];   // the ridges right over Wanat

// ---------- the track up the valley ----------
const ROADS = [["blessing", [35.000, 70.873], [35.012, 70.884], [35.030, 70.898], [35.045, 70.910], "wanat", [35.065, 70.920], [35.080, 70.925], [35.100, 70.935], "waygal"], ["blessing", [34.982, 70.905], [34.972, 71.000]]];   // and the Pech road east, on the north bank

const NAMES = { wanat: "Wanat (Vehicle Patrol Base Kahler)", blessing: "Camp Blessing (the guns)", nangalam: "Nangalam", waygal: "Waygal", aranas: "Aranas", bella: "Bella" };
const notes = {
  wanat: "2nd Platoon, Chosen Company dug in here from 9 July 2008; about 200 fighters attacked at about 04:20 on the 13th",
  blessing: "Forward Operating Base Blessing on the Pech, about 5 miles away: its 155 mm guns fired for Wanat (approximate)",
  aranas: "A smaller outpost up the side valley (approximate)",
  bella: "A smaller outpost, closed shortly before (approximate)",
};

const map = buildCampaign({
  id: "wanat-2008", script: "make_wanat.mjs", title: "The Waygal valley and Wanat, July 2008",
  name: "Wanat, 2008 (the Waygal valley)",
  start_date: "2008-07-13", calendar: "gregorian", latitude: 35, climate: "hindu_kush", climate_shift: 0, base: "M",
  bounds: [70.800, 35.130, 71.000, 34.955], midLat: 35.04, hexKm: 0.5,
  header: [
    "Wanat is at its published position, rounded; Blessing, Nangalam, Waygal and the side outposts",
    "are placed after the accounts and approximate; the mountains, rivers, terraced fields, woods",
    "and the track up the valley are drawn by hand. Nearly all of it is steep mountainside; the",
    "valley floors are terraced fields (farmland) and villages.",
    "",
    "What happened, briefly: in July 2008 the 173rd Airborne was pulling its outposts back to the",
    "Pech, and 2nd Platoon, Chosen Company, 2nd Battalion, 503rd Infantry, with engineers, Marine",
    "trainers and a platoon of the Afghan National Army, about 70 men, was sent to build a new",
    "patrol base at Wanat, beside the district centre. Before dawn on 13 July, five days in, about",
    "200 fighters attacked it from the village, the bazaar, the mosque and the high ground, hitting",
    "the observation post on the ridge above hardest. Guns at Blessing, Apaches within the half",
    "hour, and then jets held them off; a quick reaction force came up the valley. Nine Americans",
    "were killed and 27 wounded; the base was given up a few days later. Numbers below are round",
    "figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["waygal", "pech"], streams: STREAMS, bridges: BRIDGES, fords: [],
  farms: FARMS, woods: WOODS, hills: HILLS, mountains: [], roads: ROADS, towns: [], villages: ["wanat", "nangalam", "waygal", "aranas"],
  kinds: { wanat: "objective", blessing: "camp" },
  depots: { blessing: ["United States"], wanat: ["Insurgents"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "2nd Platoon, Chosen Company, 2-503rd Infantry (with engineers, Marines and ANA)", type: "foot", side: "United States", men: 72, tools: true, at: "wanat" },
    { name: "Chosen Company quick reaction force (Camp Blessing)", type: "foot", side: "United States", men: 60, tools: false, at: "blessing" },
    { name: "Fighters from the village and the high ground", type: "foot", side: "Insurgents", men: 200, tools: false, at: "north" },
    { name: "Fighters from the east (against the observation post)", type: "foot", side: "Insurgents", men: 100, tools: false, at: "northeast" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
