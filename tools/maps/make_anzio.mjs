// Builds data/maps/anzio-1944.yaml: the Anzio beachhead and the attack on Cisterna, 30 January
// 1944, on the travel map at 1 km a hex, from the coast at Anzio to Velletri and Littoria. Run
// from this folder after editing: npm ci && node make_anzio.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the US Army's account of the battle (Anzio Beachhead, American Forces in Action series, a
//   work of the US government): the Rangers crossed the west branch of the Mussolini Canal at
//   01:30 and went up the narrow Pantano ditch, which runs north-west across the fields to the
//   right of the Conca-Cisterna road, about four miles of open fields; by dawn they were at the
//   road crossing, within 800 yards of Cisterna; the 4th Rangers came up the Conca-Cisterna road
//   towards Isola Bella and were stopped short of it;
// - the coast is Natural Earth's; Anzio, Nettuno, Aprilia, Campoleone, Velletri, Cisterna and
//   Littoria (Latina) are at their modern centres, rounded; Conca (now Borgo Montello) and Isola
//   Bella are placed after the account's distances and approximate;
// - the canals, the roads, the railroad, the woods and the hills are drawn by hand through those
//   places. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  anzio: [41.448, 12.627], nettuno: [41.458, 12.661], aprilia: [41.594, 12.654], campoleone: [41.651, 12.660],
  velletri: [41.687, 12.778], cisterna: [41.599, 12.831], latina: [41.467, 12.904], conca: [41.513, 12.757],
  isola: [41.578, 12.806], crossing: [41.548, 12.770], station: [41.592, 12.820], padiglione: [41.515, 12.680],
  carroceto: [41.578, 12.650], flyover: [41.555, 12.650], ferriere: [41.535, 12.790],
  cisternaNE: [41.640, 12.870], hgtanks: [41.620, 12.815], aprilianorth: [41.690, 12.690], eastroad: [41.580, 12.900],   // where the German forces come in (not places)
};

// ---------- the canals (crossed only at their bridges) and the brooks ----------
const RIVERS = {
  canal: [[41.640, 12.880], [41.600, 12.850], [41.565, 12.815], "ferriere", [41.500, 12.795], [41.455, 12.790], [41.410, 12.790]],   // the Mussolini Canal
  westcanal: [[41.590, 12.735], [41.565, 12.755], "crossing", [41.520, 12.775], [41.500, 12.795]],                                    // its west branch
};
const STREAMS = [
  ["crossing", [41.565, 12.785], [41.585, 12.808]],                            // the Pantano ditch, north-west across the fields
  [[41.640, 12.700], [41.600, 12.690], [41.560, 12.690], [41.500, 12.700], [41.450, 12.700]],   // the Moletta and the wadis west of the Albano road
];
const BRIDGES = [[41.548, 12.772], [41.505, 12.792], [41.470, 12.790]].map((p, i) => { P["bridge" + i] = p; return "bridge" + i });
const FORDS = [];

// ---------- woods, hills ----------
const WOODS = [[[41.520, 12.640], 2.4], [[41.490, 12.700], 2.2], [[41.470, 12.740], 2.0]];   // the Padiglione woods and the macchia
const HILLS = [[[41.700, 12.760], 2.2], [[41.680, 12.830], 2.0], [[41.660, 12.900], 2.0]];   // the Alban Hills' foot and the Lepini
const MOUNTAINS = [[[41.680, 12.950], 1.8]];

// ---------- roads and railroads (through places, in order) ----------
const ROADS = [
  ["anzio", "flyover", "carroceto", "aprilia", "campoleone", "aprilianorth"],             // the Albano road north from Anzio
  ["velletri", [41.640, 12.800], "cisterna", [41.540, 12.870], "latina"],                   // the Appian Way (Highway 7)
  ["nettuno", "padiglione", "conca", [41.545, 12.782], "isola", "cisterna"],               // Nettuno to Conca and the Conca-Cisterna road
  ["anzio", "nettuno", [41.455, 12.760], [41.465, 12.850], "latina"],                       // the coast road
  [[41.700, 12.700], "campoleone", [41.640, 12.760], "station", "cisterna", "cisternaNE"],  // the Rome-Naples railroad through Cisterna
  ["eastroad", "latina"], ["aprilia", [41.600, 12.740], "isola"],
];

const TOWNS = ["anzio", "cisterna", "latina", "velletri"];
const VILLAGES = ["nettuno", "aprilia", "campoleone", "conca", "isola", "carroceto", "padiglione"];

const NAMES = { anzio: "Anzio", nettuno: "Nettuno", aprilia: "Aprilia (the Factory)", campoleone: "Campoleone", velletri: "Velletri",
  cisterna: "Cisterna", latina: "Littoria (Latina)", conca: "Conca", isola: "Isola Bella", crossing: "Where the Rangers crossed the canal",
  station: "Cisterna station", padiglione: "Padiglione", carroceto: "Carroceto", flyover: "The flyover", ferriere: "Le Ferriere" };
const notes = {
  crossing: "The 1st and 3rd Ranger Battalions crossed the west branch of the Mussolini Canal here at 01:30 on 30 January 1944 and went up the Pantano ditch (approximate)",
  cisterna: "The Rangers' objective: by dawn they were in the open fields within 800 yards of the town",
  isola: "German machine guns in the farmhouses below it stopped the 4th Rangers on the road (approximate)",
  conca: "Where the 4th Rangers and the 3rd Battalion, 15th Infantry set off up the road to Cisterna (approximate)",
  aprilia: "The British attacked north from here towards Campoleone the same night",
};

const map = buildCampaign({
  id: "anzio-1944", script: "make_anzio.mjs", title: "The Anzio beachhead and the attack on Cisterna, January 1944",
  name: "Anzio, 1944 (the beachhead to Cisterna)",
  start_date: "1944-01-29", calendar: "gregorian", latitude: 41, climate: "mediterranean", climate_shift: -1,
  bounds: [12.600, 41.705, 12.960, 41.400], midLat: 41.55, hexKm: 1,
  header: [
    "The coast is Natural Earth's; the towns are at their modern centres, rounded; Conca and Isola",
    "Bella are placed after the US Army's account and approximate; the canals, roads, railroad,",
    "woods and hills are drawn by hand and approximate. Most of the plain is farmland, reclaimed",
    "from the Pontine marshes and cut by drainage ditches.",
    "",
    "What happened, briefly: Allied VI Corps landed at Anzio on 22 January 1944, behind the German",
    "line at Cassino, and built up its beachhead for a week. On the night of 29-30 January it",
    "attacked out: the British north towards Campoleone, the US 3rd Division towards Cisterna and",
    "the Appian Way. Two Ranger battalions, 767 men, went ahead in the dark up the Pantano ditch to",
    "take Cisterna by surprise; at dawn they were caught in the open fields short of the town by",
    "Germans brought in the night before, in houses, haystacks and dugouts, with self-propelled",
    "guns and later tanks. By noon it was over: only six of them got back. The 4th Rangers and the",
    "3rd Division were stopped short of Isola Bella and of Cisterna. Numbers below are round",
    "figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["canal", "westcanal"], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  woods: WOODS, hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { cisterna: "objective", isola: "objective", anzio: "camp" },
  depots: { anzio: ["Americans"], nettuno: ["Americans"], cisterna: ["Germans"], velletri: ["Germans"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "Ranger Force, 1st and 3rd Ranger Battalions (Darby)", type: "foot", side: "Americans", men: 767, tools: false, at: "crossing" },
    { name: "4th Ranger Battalion", type: "foot", side: "Americans", men: 400, tools: false, at: "conca" },
    { name: "15th Infantry, 3rd Battalion", type: "foot", side: "Americans", men: 800, tools: true, at: "conca" },
    { name: "7th Infantry", type: "foot", side: "Americans", men: 2500, tools: true, at: "padiglione" },
    { name: "504th Parachute Infantry", type: "foot", side: "Americans", men: 1500, tools: true, at: "bridge2" },
    { name: "Hermann Göring Division (battle groups)", type: "foot", side: "Germans", men: 3000, tools: true, at: "cisterna" },
    { name: "Assault guns and tanks (Hermann Göring Division)", type: "wagons", side: "Germans", men: 200, tools: false, at: "hgtanks" },
    { name: "356th Reconnaissance and 7th Luftwaffe Jäger Battalions", type: "foot", side: "Germans", men: 800, tools: true, at: "eastroad" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
