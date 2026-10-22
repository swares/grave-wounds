// Builds data/maps/chipyong-1951.yaml: the 23rd Infantry's stand at Chipyong-ni, 13-15 February
// 1951, on the travel map at 1 km a hex, from Yangpyong in the west to Wonju in the east and
// Yoju in the south. Run from this folder after editing: npm ci && node make_chipyong.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the US Army's histories give them and as they are
//   summarised publicly: the 23rd Infantry Regimental Combat Team, with the French Battalion,
//   the 1st Ranger Company, the 37th Field Artillery Battalion, a battery of the 503rd and a
//   battery of the 82nd AAA, about 4,500 men, held a tight perimeter round the road and rail
//   junction; the Chinese 39th, 40th and 42nd Armies closed round it; Task Force Crombez (the
//   5th Cavalry, with about twenty tanks) broke through from the south on the afternoon of the
//   15th;
// - the coast is not on this map; the Han and the towns are Natural Earth's and at their modern
//   centres, rounded (Chipyong-ni is Jipyeong-ri today, Yoju is Yeoju, Yangpyong Yangpyeong);
//   the Twin Tunnels, Koksu-ri and Hill 397 are placed after the accounts' distances and are
//   approximate;
// - the hills, the roads and the railroad are drawn by hand through those places. They are
//   approximate; most of the low ground is rice paddy, frozen in February.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  chipyong: [37.475, 127.637], twintunnels: [37.445, 127.690], hill397: [37.462, 127.652], kokso: [37.395, 127.612],
  yoju: [37.298, 127.637], yangpyong: [37.491, 127.488], wonju: [37.342, 127.920], hoengsong: [37.492, 127.985],
  munmang: [37.380, 127.780], sokpul: [37.520, 127.560],
  north: [37.555, 127.700], northwest: [37.550, 127.560], southwest: [37.420, 127.560],   // where the Chinese armies come in (not places)
};

// ---------- the Han (crossed only at its bridges) and the streams ----------
const RIVERS = {
  han: [[37.255, 127.760], [37.290, 127.665], [37.310, 127.620], [37.355, 127.575], [37.420, 127.525], [37.475, 127.500], [37.505, 127.470], [37.545, 127.425]],
};
const STREAMS = [
  [[37.540, 127.640], "chipyong", [37.430, 127.625], "kokso", [37.330, 127.640]],   // the stream south past Chipyong-ni to the Han
  [[37.480, 127.760], "twintunnels", [37.420, 127.700]],
];
const BRIDGES = [[37.307, 127.630], [37.485, 127.496]].map((p, i) => { P["bridge" + i] = p; return "bridge" + i });
const FORDS = [];

// ---------- hills and mountains everywhere, the valleys farmed ----------
const FARMS = [[P.chipyong, 2.0], [P.kokso, 1.5], [P.yoju, 3.0], [P.yangpyong, 2.5], [P.wonju, 3.5], [P.hoengsong, 2.0], [[37.440, 127.630], 1.5], [[37.360, 127.630], 1.5],
  [P.twintunnels, 1.0], [P.munmang, 1.5], [[37.330, 127.840], 2.0]];
const MOUNTAINS = [[[37.530, 127.800], 4.0], [[37.420, 127.820], 3.5], [[37.545, 127.520], 2.5], [[37.360, 127.730], 2.5], [[37.440, 127.560], 2.0], [[37.540, 127.900], 3.0]];
const HILLS = [];

// ---------- roads and the railroad (through places, in order) ----------
const ROADS = [
  ["north", "chipyong", "kokso", "yoju"],                                          // the road south to Yoju: Task Force Crombez's way in
  ["yangpyong", "sokpul", "chipyong"],                                             // west to Yangpyong
  ["chipyong", "twintunnels", "munmang", "wonju"],                                 // south-east to Wonju
  ["yangpyong", [37.520, 127.580], "chipyong", "twintunnels", [37.400, 127.800], "wonju"],   // the Seoul-Wonju railroad
  ["yoju", [37.320, 127.780], "wonju", "hoengsong"], ["northwest", "sokpul"], ["southwest", "kokso"],
];

const TOWNS = ["yoju", "wonju", "yangpyong"];
const VILLAGES = ["chipyong", "kokso", "hoengsong", "munmang", "sokpul"];

const NAMES = { chipyong: "Chipyong-ni", twintunnels: "The Twin Tunnels", hill397: "Hill 397", kokso: "Koksu-ri", yoju: "Yoju", yangpyong: "Yangpyong",
  wonju: "Wonju", hoengsong: "Hoengsong", munmang: "Munmang-ni", sokpul: "Sokpul" };
const notes = {
  chipyong: "The 23rd Infantry and the French Battalion held a perimeter about a mile across round the road and rail junction, 13-15 February 1951",
  twintunnels: "The 23rd fought the Chinese here at the start of February, two weeks before the siege (approximate)",
  hill397: "The high ground south-east of the perimeter from which the Chinese came at E and G Companies (approximate)",
  kokso: "Where Task Force Crombez's tanks ran the gauntlet of Chinese fire on the road north (approximate)",
  yoju: "Where Task Force Crombez set out on the afternoon of 15 February",
};

const map = buildCampaign({
  id: "chipyong-1951", script: "make_chipyong.mjs", title: "The siege of Chipyong-ni, February 1951",
  name: "Chipyong-ni, 1951 (Yangpyong to Wonju)",
  start_date: "1951-02-13", calendar: "gregorian", latitude: 37, climate: "korea", climate_shift: 0, base: "h",
  bounds: [127.420, 37.560, 128.010, 37.250], midLat: 37.40, hexKm: 1,
  header: [
    "The Han is crossed only at its bridges; the towns are at their modern centres, rounded; the",
    "Twin Tunnels, Koksu-ri and Hill 397 are placed after the accounts and approximate; the hills,",
    "roads and railroad are drawn by hand. Most of the low ground is rice paddy (farmland), frozen",
    "in February; the rest is steep wooded hills.",
    "",
    "What happened, briefly: in February 1951 the Chinese struck the UN line in the central",
    "mountains. The 23rd Infantry Regimental Combat Team (Colonel Paul Freeman), with the French",
    "Battalion, Rangers, artillery and anti-aircraft guns, about 4,500 men, was left at the road",
    "and rail junction of Chipyong-ni and dug a tight perimeter on the low hills round it. On the",
    "nights of 13 and 14 February Chinese regiments of three armies attacked all round it; aircraft",
    "dropped flares and ammunition, and by day fighter-bombers kept them off. Early on the 15th they",
    "broke into the southern perimeter at G Company's hill. That afternoon Task Force Crombez, the",
    "5th Cavalry with about twenty tanks, fought its way up the road from Yoju and the Chinese drew",
    "off. Numbers below are round figures for play: US accounts put the Chinese at up to 25,000,",
    "Chinese accounts at three regiments committed.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["han"], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  farms: FARMS, woods: [], hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { chipyong: "objective", yoju: "camp" },
  depots: { yoju: ["United Nations"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "23rd Infantry Regimental Combat Team (with the French Battalion)", type: "foot", side: "United Nations", men: 4500, tools: true, at: "chipyong" },
    { name: "Task Force Crombez (5th Cavalry, with tanks)", type: "foot", side: "United Nations", men: 1500, tools: true, at: "yoju" },
    { name: "Chinese 40th Army (119th and 120th Divisions)", type: "foot", side: "Chinese", men: 6000, tools: true, at: "north" },
    { name: "Chinese 39th Army (115th Division)", type: "foot", side: "Chinese", men: 4000, tools: true, at: "northwest" },
    { name: "Chinese 42nd Army (125th and 126th Divisions)", type: "foot", side: "Chinese", men: 5000, tools: true, at: "southwest" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
