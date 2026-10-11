// Builds data/maps/bougainville-1944.yaml: the American perimeter at Empress Augusta Bay on
// Bougainville, March 1944, on the travel map at 1 km a hex. Run from this folder after editing:
// npm ci && node make_bougainville.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the coast is Natural Earth's (public domain), coarse at this scale;
// - Cape Torokina, the rivers' mouths, the airfields, Hill 700, Hill 260 and Mount Bagana are
//   placed after their published positions, rounded; the hills and the trails inland are only
//   approximate;
// - the rivers, swamps, jungle, ridges and trails are drawn by hand through those places. They
//   are approximate. The land is jungle (forest) unless drawn otherwise.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  torokina: [-6.235, 155.045], piva: [-6.205, 155.075], hill700: [-6.168, 155.093], hill260: [-6.190, 155.135],
  torokinamouth: [-6.247, 155.065], pivamouth: [-6.228, 155.055], larumamouth: [-6.175, 154.975], bagana: [-6.140, 155.195],
  numa: [-6.120, 155.140], eastwest: [-6.225, 155.110], fighter: [-6.240, 155.050], koromokina: [-6.200, 155.010],
  north6: [-6.090, 155.100], east23: [-6.150, 155.170], west45: [-6.120, 155.020],
};

// ---------- rivers (crossed only at the fords and bridges named), creeks ----------
const RIVERS = {
  torokina: [[-6.080, 155.170], [-6.140, 155.150], [-6.190, 155.120], [-6.220, 155.090], "torokinamouth", [-6.262, 155.060]],
  piva: [[-6.110, 155.090], [-6.160, 155.080], [-6.190, 155.070], "pivamouth", [-6.235, 155.050]],
  laruma: [[-6.090, 154.990], [-6.140, 154.980], "larumamouth", [-6.185, 154.965]],
};
const STREAMS = [
  [[-6.150, 155.010], [-6.185, 155.015], "koromokina", [-6.215, 155.010]],          // the Koromokina, through swamp
  [[-6.140, 155.120], [-6.180, 155.110], [-6.205, 155.100]],                         // a creek under Hill 700
];
const BRIDGES = [];
const FORDS = [[-6.200, 155.069], [-6.215, 155.095], [-6.170, 155.140]];

// ---------- the coast swamps, the cleared perimeter, the ridges ----------
const MARSH = [[[-6.205, 155.000], 2.6], [[-6.230, 154.990], 1.8], [[-6.245, 155.100], 1.6], [[-6.255, 155.130], 2.0]];
const CLEARINGS = [[[-6.230, 155.050], 1.4], [[-6.205, 155.080], 1.4], [[-6.220, 155.065], 1.0]];   // the beachhead, airfields and roads
const HILLS = [[[-6.168, 155.093], 1.0], [[-6.190, 155.135], 0.9], [[-6.150, 155.060], 1.5], [[-6.130, 155.120], 1.5]];
const MOUNTAINS = [[[-6.140, 155.195], 3.5], [[-6.090, 155.150], 3.0], [[-6.080, 155.060], 3.0]];

// ---------- roads and trails (through places, in order) ----------
const ROADS = [
  ["torokina", "fighter", "pivamouth", "piva", "hill700", "numa"],         // the perimeter road, out along the Numa Numa trail
  ["piva", "eastwest", "hill260"], ["torokina", "koromokina", "larumamouth"], ["piva", [-6.200, 155.040], "koromokina"],
];

const TOWNS = [];
const VILLAGES = [];

const NAMES = { torokina: "Cape Torokina", piva: "Piva airfields", hill700: "Hill 700", hill260: "Hill 260",
  torokinamouth: "Torokina River mouth", pivamouth: "Piva River mouth", larumamouth: "Laruma River mouth", bagana: "Mount Bagana",
  numa: "Numa Numa trail", eastwest: "East-West trail", fighter: "Torokina airstrip", koromokina: "Koromokina lagoon" };
const notes = {
  torokina: "Where the 3rd Marine Division landed on 1 November 1943",
  hill700: "Held by the 145th Infantry; Japanese troops broke into its line on 8-9 March 1944 and were driven out in days of close fighting (approximate)",
  hill260: "An outpost of the Americal Division on a knoll east of the Torokina, fought over for weeks in March 1944 (approximate)",
  piva: "The bomber and fighter strips the perimeter was built to hold",
  bagana: "The active volcano that looms over the perimeter",
};

const map = buildCampaign({
  id: "bougainville-1944", script: "make_bougainville.mjs", title: "The Empress Augusta Bay perimeter on Bougainville, March 1944",
  name: "Bougainville, 1944 (the Torokina perimeter)",
  start_date: "1944-03-07", calendar: "gregorian", latitude: -6, climate: "tropical", climate_shift: 0, base: "F",
  bounds: [154.93, -6.06, 155.25, -6.29], midLat: -6.18, hexKm: 1,
  header: [
    "The coast is Natural Earth's and coarse; the cape, the river mouths, the airfields, the hills",
    "and the volcano are placed after their published positions, rounded; the rivers, swamps,",
    "ridges and trails are drawn by hand and approximate. The land is jungle unless drawn otherwise.",
    "",
    "What happened, briefly: on 1 November 1943 American Marines landed at Cape Torokina in Empress",
    "Augusta Bay and built a perimeter around airfields in the jungle; by early 1944 the Army's",
    "XIV Corps held it, the 37th Infantry Division on the left and the Americal Division on the",
    "right. In March 1944 the Japanese 17th Army counterattacked it from the hills. On Hill 700",
    "the Japanese broke into the 145th Infantry's pillbox line on the night of 8-9 March and were",
    "thrown out in days of close fighting; at Hill 260 the fight went on for weeks. American",
    "artillery and mortars, firing on call all round the perimeter, did much of the killing. The",
    "attacks failed with heavy Japanese losses. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["torokina", "piva", "laruma"], streams: STREAMS, bridges: BRIDGES,
  fords: FORDS.map((p, i) => { P["ford" + i] = p; return "ford" + i }),
  marsh: MARSH, clearings: CLEARINGS, hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { torokina: "camp", piva: "objective", hill700: "objective", hill260: "objective" },
  forces: [
    { name: "37th Infantry Division (Beightler)", type: "foot", side: "Americans", men: 14000, tools: true, at: "piva" },
    { name: "145th Infantry, on Hill 700", type: "foot", side: "Americans", men: 2500, tools: true, at: "hill700" },
    { name: "Americal Division (Hodge)", type: "foot", side: "Americans", men: 14000, tools: true, at: "eastwest" },
    { name: "Iwasa unit (23rd Infantry)", type: "foot", side: "Japanese", men: 4500, tools: true, at: "north6" },
    { name: "Magata unit (45th Infantry)", type: "foot", side: "Japanese", men: 5000, tools: true, at: "west45" },
    { name: "Muda unit (13th Infantry)", type: "foot", side: "Japanese", men: 4000, tools: true, at: "east23" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
