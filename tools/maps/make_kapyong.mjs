// Builds data/maps/kapyong-1951.yaml: the Kapyong valley, 22-25 April 1951, on the travel map at
// 0.5 km a hex, from Kapyong on the Pukhan north up the valley past Hills 504 and 677. Run from
// this folder after editing: npm ci && node make_kapyong.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the official histories give them and as they are
//   summarised publicly: the 27th British Commonwealth Brigade blocked the Kapyong valley north
//   of the village as the Chinese spring offensive broke the ROK 6th Division, the 3rd Battalion,
//   Royal Australian Regiment on Hill 504 east of the river, the 2nd Battalion, Princess
//   Patricia's Canadian Light Infantry on Hill 677 west of it, the 1st Middlesex behind, with New
//   Zealand guns and a company of American tanks; Hill 794 to the north-west was left undefended;
//   3 RAR's headquarters was at the hamlet of Chuktun-ni in the valley;
// - Kapyong at its modern centre, rounded; the hills and Chuktun-ni placed after the accounts
//   and approximate; the rivers, the road and the hills drawn by hand. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  kapyong: [37.8315, 127.5105], h504: [37.882, 127.546], h677: [37.884, 127.503], h794: [37.905, 127.496], chuktun: [37.872, 127.528],
  naechon: [37.930, 127.540], north: [37.985, 127.530], northwest: [37.975, 127.460], blocking: [37.850, 127.515],
};
const RIVERS = {
  pukhan: [[37.790, 127.630], [37.805, 127.580], [37.812, 127.540], [37.808, 127.500], [37.800, 127.460], [37.790, 127.420]],
};
const STREAMS = [[[37.985, 127.535], "naechon", [37.900, 127.532], "chuktun", [37.850, 127.522], [37.818, 127.518]]];   // the Kapyong river, shallow and fordable, down the valley
const BRIDGES = [[37.812, 127.540]].map((p, i) => { P["bridge" + i] = p; return "bridge" + i });
const FARMS = [[P.kapyong, 1.2], [[37.870, 127.528], 0.8], [[37.900, 127.534], 0.7], [P.naechon, 0.6], [[37.850, 127.522], 0.6]];
const HILLS = [[P.h504, 1.0], [P.h677, 1.0], [[37.860, 127.560], 1.2], [[37.860, 127.490], 1.0]];
const MOUNTAINS = [[P.h794, 1.3], [[37.950, 127.480], 2.5], [[37.950, 127.590], 2.5], [[37.880, 127.610], 1.8], [[37.890, 127.440], 2.0]];
const ROADS = [["north", "naechon", [37.900, 127.528], "chuktun", "blocking", "kapyong", "bridge0", [37.790, 127.545]], ["kapyong", [37.820, 127.450], [37.815, 127.420]]];
const NAMES = { kapyong: "Kapyong", h504: "Hill 504", h677: "Hill 677", h794: "Hill 794 (Sudok San)", chuktun: "Chuktun-ni", naechon: "Naech'on", blocking: "The brigade's blocking position" };
const notes = {
  h504: "3rd Battalion, Royal Australian Regiment held it on the night of 23-24 April 1951 and withdrew the next afternoon (approximate)",
  h677: "2nd Battalion, PPCLI held it on the night of 24-25 April, surrounded and supplied by air (approximate)",
  chuktun: "3 RAR's headquarters and the American tanks were here in the valley (approximate)",
  h794: "Left undefended: the brigade had too few men to hold it (approximate)",
};
const map = buildCampaign({
  id: "kapyong-1951", script: "make_kapyong.mjs", title: "The Kapyong valley, April 1951",
  name: "Kapyong, 1951 (the Kapyong valley)",
  start_date: "1951-04-22", calendar: "gregorian", latitude: 38, climate: "korea", climate_shift: 0, base: "h",
  bounds: [127.420, 37.990, 127.630, 37.780], midLat: 37.88, hexKm: 0.5,
  header: [
    "Kapyong is at its modern centre, rounded; the hills, Chuktun-ni and Naech'on are placed after",
    "the accounts and approximate; the rivers, road and hills are drawn by hand. Steep wooded hills",
    "either side of a narrow valley of paddies; the Kapyong river is shallow and fordable (a",
    "brook); the Pukhan is crossed at its bridge.",
    "",
    "What happened, briefly: on 22 April 1951 the Chinese spring offensive broke the ROK 6th",
    "Division north of Kapyong. The 27th British Commonwealth Brigade, about 2,000 men, blocked the",
    "valley: the Australians on Hill 504, the Canadians on Hill 677, with New Zealand guns and",
    "American tanks. On the nights of 23-24 and 24-25 April the Chinese 118th Division attacked",
    "both hills; the Australians fell back on the 24th, and the Canadians, surrounded and supplied",
    "by air, held. The road to Seoul stayed shut. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["pukhan"], streams: STREAMS, bridges: BRIDGES, fords: [],
  farms: FARMS, woods: [], hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: ["kapyong"], villages: ["chuktun", "naechon"],
  kinds: { h504: "objective", h677: "objective", kapyong: "camp" },
  forces: [
    { name: "3rd Battalion, Royal Australian Regiment", type: "foot", side: "United Nations", men: 700, tools: true, at: "h504" },
    { name: "2nd Battalion, Princess Patricia's Canadian Light Infantry", type: "foot", side: "United Nations", men: 700, tools: true, at: "h677" },
    { name: "1st Battalion, Middlesex Regiment, and the brigade's guns", type: "foot", side: "United Nations", men: 1000, tools: true, at: "blocking" },
    { name: "A Company, 72nd Heavy Tank Battalion", type: "wagons", side: "United Nations", men: 75, tools: false, at: "chuktun" },
    { name: "ROK 6th Division (falling back)", type: "foot", side: "United Nations", men: 3000, tools: false, at: "naechon" },
    { name: "Chinese 118th Division", type: "foot", side: "Chinese", men: 9000, tools: true, at: "north" },
    { name: "Chinese 60th Division", type: "foot", side: "Chinese", men: 6000, tools: true, at: "northwest" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
