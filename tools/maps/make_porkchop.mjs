// Builds data/maps/porkchop-1953.yaml: the 7th Infantry Division's outpost line north of Yeoncheon,
// April-July 1953, on the travel map at 0.5 km a hex. Run from this folder after editing:
// npm ci && node make_porkchop.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the US Army's accounts (Hermes, Truce Tent and Fighting Front; Marshall's study of the
//   battle) as summarised publicly, for the facts: Pork Chop Hill, a hill of about 300 m, was an
//   outpost in front of the 7th Infantry Division's main line, Hill 200 beside it; Old Baldy to
//   its west fell to the Chinese in March 1953, leaving Pork Chop open on three sides; a company
//   of the 31st Infantry held it in bunkers and trenches when the Chinese 141st Division attacked
//   on the night of 16 April 1953; the 17th Infantry's companies retook it; in July the Chinese
//   took it after five days and the hill was given up;
// - Pork Chop at its published position, rounded; Old Baldy, Hill 200, T-Bone and the main line
//   placed after the accounts and approximate; the hills, streams and roads drawn by hand.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  porkchop: [38.2414, 127.0194], h200: [38.2370, 127.0250], oldbaldy: [38.2420, 126.9990], tbone: [38.2570, 127.0420], mlr: [38.2300, 127.0200],
  yeoncheon: [38.1960, 127.0700], rear: [38.2050, 127.0300], north: [38.2900, 127.0100], northeast: [38.2850, 127.0700],
};
const STREAMS = [[[38.290, 126.990], [38.250, 127.010], [38.235, 127.012], [38.210, 127.030], [38.190, 127.060]], [[38.280, 127.080], [38.240, 127.060], [38.200, 127.070]]];
const FARMS = [[P.yeoncheon, 1.5], [[38.240, 127.012], 0.6], [[38.215, 127.040], 1.2]];
const HILLS = [[P.porkchop, 0.4], [P.h200, 0.3], [P.oldbaldy, 0.5], [P.tbone, 0.7], [[38.270, 127.020], 1.5], [[38.275, 126.970], 1.5], [[38.210, 126.980], 1.5], [[38.225, 127.080], 1.3]];
const ROADS = [["yeoncheon", "rear", "mlr", "h200"], ["yeoncheon", [38.230, 127.090], "northeast"], ["rear", [38.215, 126.980], [38.215, 126.950]]];
const NAMES = { porkchop: "Pork Chop Hill", h200: "Hill 200", oldbaldy: "Old Baldy (Hill 266)", tbone: "T-Bone Hill", mlr: "The main line of resistance", yeoncheon: "Yeoncheon", rear: "The 17th Infantry's reserve" };
const notes = {
  porkchop: "An outpost in front of the 7th Division's line, held by a company in bunkers and trenches; retaken in April 1953 and given up in July",
  oldbaldy: "Taken by the Chinese on 23 March 1953, which left Pork Chop open on three sides (approximate)",
  h200: "The outpost beside Pork Chop (approximate)",
  tbone: "Chinese-held hill across the valley (approximate)",
};
const map = buildCampaign({
  id: "porkchop-1953", script: "make_porkchop.mjs", title: "Pork Chop Hill and the outpost line, 1953",
  name: "Pork Chop Hill, 1953 (the outpost line north of Yeoncheon)",
  start_date: "1953-04-16", calendar: "gregorian", latitude: 38, climate: "korea", climate_shift: 0, base: "f",
  bounds: [126.950, 38.295, 127.100, 38.185], midLat: 38.24, hexKm: 0.5,
  header: [
    "Pork Chop Hill is at its published position, rounded; Old Baldy, Hill 200, T-Bone and the",
    "main line are placed after the accounts and approximate; the hills, streams and roads are",
    "drawn by hand. Low, bare hills (hills) over paddy valleys (farmland), cratered by two years",
    "of shelling.",
    "",
    "What happened, briefly: by 1953 the front had stood still for two years, and the armies fought",
    "over outposts while the truce was talked out. On the night of 16 April the Chinese 141st",
    "Division took most of Pork Chop from E Company, 31st Infantry; K and L Companies and then",
    "companies of the 17th Infantry fought back up it and held it, with some 77,000 shells fired",
    "on the outposts. In July the Chinese attacked again for five days, and on 11 July the 7th",
    "Division gave the hill up. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: {}, majorRivers: [], streams: STREAMS, bridges: [], fords: [],
  farms: FARMS, woods: [], hills: HILLS, mountains: [], roads: ROADS, towns: ["yeoncheon"], villages: [],
  kinds: { porkchop: "objective", rear: "camp" },
  depots: { mlr: ["United Nations"], rear: ["United Nations"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "E Company, 31st Infantry (Pork Chop)", type: "foot", side: "United Nations", men: 100, tools: true, at: "porkchop" },
    { name: "31st Infantry (the main line)", type: "foot", side: "United Nations", men: 2500, tools: true, at: "mlr" },
    { name: "17th Infantry", type: "foot", side: "United Nations", men: 3000, tools: true, at: "rear" },
    { name: "Chinese 141st Division", type: "foot", side: "Chinese", men: 7000, tools: true, at: "north" },
    { name: "Chinese 67th Division", type: "foot", side: "Chinese", men: 6800, tools: true, at: "northeast" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
