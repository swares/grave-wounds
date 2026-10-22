// Builds data/maps/hue-1968.yaml: Hue and its approaches, 31 January to early March 1968, on the
// travel map at 0.5 km a hex, from the Phu Bai combat base north-west up Highway 1 to the city on
// the Perfume River, the Citadel on its north bank. Run from this folder after editing:
// npm ci && node make_hue.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the US Marine Corps and US Army histories give them and as
//   they are summarised publicly: on 31 January 1968, at the Tet offensive, two North Vietnamese
//   regiments and Viet Cong battalions took most of Hue in a night; the 6th Regiment the Citadel
//   north of the river, except the ARVN 1st Division's headquarters at Mang Ca in its north-east
//   corner, and the 4th Regiment the new city south of it, except the MACV advisers' compound;
//   Marines came up Highway 1 from Phu Bai over the An Cuu bridge on the Phu Cam canal, cleared
//   the south bank street by street in the first half of February and the Citadel by early March;
//   the 1st Cavalry Division's 3rd Brigade closed in from the north-west, at La Chu, where the
//   North Vietnamese headquarters was;
// - the Citadel, the bridges, Phu Bai and the villages placed after the accounts and
//   approximate; the river, the canal, the road and the hills drawn by hand. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  citadel: [16.470, 107.578], mangca: [16.481, 107.586], tayloc: [16.476, 107.567], macv: [16.4645, 107.5935],
  newcity: [16.461, 107.598], giahoi: [16.476, 107.600], thienmu: [16.4535, 107.5445], lachu: [16.505, 107.545],
  phubai: [16.401, 107.700], ancuu: [16.452, 107.603], pk17: [16.535, 107.505], tombs: [16.425, 107.575],
  north: [16.540, 107.530], west: [16.470, 107.505],
};
// The rest of the city's hexes (unnamed): the Citadel's corners, the new city's blocks, Gia Hoi's streets.
const CITY = { cit1: [16.467, 107.569], cit2: [16.478, 107.570], cit3: [16.478, 107.586], cit4: [16.468, 107.583], new1: [16.458, 107.590], new2: [16.457, 107.600], new3: [16.463, 107.603], gia1: [16.480, 107.596] };
Object.assign(P, CITY);
const RIVERS = {
  huong: [[16.375, 107.570], [16.410, 107.565], [16.435, 107.552], [16.450, 107.546], [16.457, 107.562], [16.463, 107.578],
    [16.469, 107.592], [16.476, 107.604], [16.488, 107.614], [16.505, 107.622], [16.525, 107.632], [16.545, 107.640]],
  phucam: [[16.456, 107.565], [16.452, 107.585], [16.452, 107.603], [16.458, 107.615], [16.466, 107.614], [16.474, 107.607]],
};
const BRIDGES = [[16.4685, 107.5880], "ancuu"].map((p, i) => {
  if (typeof p === "string") return p;
  P["bridge" + i] = p; return "bridge" + i;
});
const MARSH = [[[16.500, 107.580], 2.2], [[16.515, 107.600], 1.8], [[16.430, 107.640], 1.6], [[16.495, 107.660], 2.0], [[16.410, 107.620], 1.4]];
const WOODS = [[[16.440, 107.520], 1.0], [[16.395, 107.545], 1.2]];
const HILLS = [[P.tombs, 1.3], [[16.405, 107.590], 1.4], [[16.440, 107.530], 1.2], [[16.385, 107.640], 1.2]];
const MOUNTAINS = [[[16.385, 107.505], 2.0], [[16.420, 107.500], 1.4]];
const ROADS = [
  ["phubai", [16.415, 107.670], [16.435, 107.630], "ancuu", "macv", "bridge0", "citadel", [16.500, 107.560], "north"],
  ["citadel", "west"], ["citadel", "giahoi"],
];
const NAMES = {
  citadel: "The Citadel (Hue)", mangca: "Mang Ca (ARVN 1st Division headquarters)", tayloc: "Tay Loc airfield", macv: "The MACV compound",
  newcity: "Hue, the new city (south bank)", giahoi: "Gia Hoi", thienmu: "Thien Mu pagoda", lachu: "La Chu", phubai: "Phu Bai combat base",
  ancuu: "An Cuu bridge", pk17: "PK-17", tombs: "The imperial tombs",
};
const notes = {
  citadel: "Taken by the North Vietnamese 6th Regiment on the night of 30-31 January 1968, retaken by early March (approximate)",
  mangca: "Held all through by the ARVN 1st Division's headquarters (approximate)",
  macv: "The American advisers held it on the first night; the Marines came up to it from Phu Bai (approximate)",
  ancuu: "Highway 1 crosses the Phu Cam canal here into the new city (approximate)",
  lachu: "The North Vietnamese command post, attacked by the 1st Cavalry Division's 3rd Brigade (approximate)",
};
const map = buildCampaign({
  id: "hue-1968", script: "make_hue.mjs", title: "Hue, January to March 1968",
  name: "Hue, 1968 (the city and Phu Bai)",
  start_date: "1968-01-31", calendar: "gregorian", latitude: 16, climate: "central_coast", climate_shift: 0, base: "f",
  bounds: [107.500, 16.545, 107.730, 16.370], midLat: 16.46, hexKm: 0.5,
  header: [
    "The Citadel, the bridges, Phu Bai and the villages are placed after the accounts and",
    "approximate; the Perfume River, the Phu Cam canal, Highway 1 and the hills are drawn by hand.",
    "Rice paddies and villages on the coastal plain, low hills with the imperial tombs to the",
    "south-west; the Perfume River is crossed at its bridge in the city, the canal at An Cuu.",
    "",
    "What happened, briefly: early on 31 January 1968, at the Tet offensive, North Vietnamese and",
    "Viet Cong troops took most of Hue. The ARVN 1st Division held its headquarters at Mang Ca and",
    "the American advisers their compound south of the river. Marines came up Highway 1 from Phu",
    "Bai and cleared the new city in the first half of February, then fought along the Citadel's",
    "walls; the ARVN took back the palace on 24 February, while the 1st Cavalry Division closed in",
    "from the north-west. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["huong"], streams: [], bridges: BRIDGES, fords: [],
  farms: [], woods: WOODS, marsh: MARSH, hills: HILLS, mountains: MOUNTAINS, roads: ROADS,
  towns: ["citadel", "newcity", "giahoi", ...Object.keys(CITY)], villages: ["lachu", "thienmu", "pk17"],
  kinds: { citadel: "objective", macv: "objective", phubai: "camp" },
  depots: { phubai: ["United States and ARVN"], lachu: ["North Vietnamese"] },   // where each side resupplies (project doc "depots-research")
  tongues: { giahoi: ["vietnamese", "chinese"] },   // the people's own tongues where they differ from the map's (project doc "tongues-research")
  forces: [
    { name: "ARVN 1st Division headquarters and the Black Panther company", type: "foot", side: "United States and ARVN", men: 400, tools: true, at: "mangca" },
    { name: "MACV advisers' compound", type: "foot", side: "United States and ARVN", men: 200, tools: true, at: "macv" },
    { name: "1st Battalion, 1st Marines, and 2nd Battalion, 5th Marines", type: "foot", side: "United States and ARVN", men: 1000, tools: true, at: "phubai" },
    { name: "Marine tanks and Ontos", type: "wagons", side: "United States and ARVN", men: 60, tools: false, at: "phubai" },
    { name: "3rd Brigade, 1st Cavalry Division", type: "foot", side: "United States and ARVN", men: 1200, tools: true, at: "pk17" },
    { name: "North Vietnamese 6th Regiment (the Citadel)", type: "foot", side: "North Vietnamese", men: 2500, tools: true, at: "citadel" },
    { name: "North Vietnamese 4th Regiment (the new city)", type: "foot", side: "North Vietnamese", men: 2000, tools: true, at: "newcity" },
    { name: "North Vietnamese command post and reserves", type: "foot", side: "North Vietnamese", men: 1500, tools: true, at: "lachu" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
