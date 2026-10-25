// Builds data/maps/debecka-2003.yaml: the country south of Erbil in northern Iraq, April 2003, on
// the travel map at 0.5 km a hex, from Pir Da'ud south over the ridge to the Debecka crossroads and
// west to Makhmur. Run from this folder after editing: npm ci && node make_debecka.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours (the project's
// debecka-research.md):
// - the plain facts of the battle as the accounts give them: on 6 April 2003 Special Forces teams of
//   Task Force Viking with KDP Peshmerga attacked south from the Pir Da'ud area across the ridge
//   (Zurqah Ziraw Dagh, about 5 km north of the crossroads) and held the crossroads where the
//   Erbil-Qayyarah road meets Highway 2, about 40 km south-south-west of Erbil (Veritas); the Iraqi
//   line along the ridge was the Green Line, held by the Iraqi army;
// - only the crossroads has a published coordinate (35.884 N, 43.784 E); the ridge, Press Hill,
//   the Alamo and Pir Da'ud are placed from the distances the accounts give, the roads' lines
//   beyond the crossroads by inference (Highway 2 north-west towards Mosul and south-east towards
//   Kirkuk). They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  crossroads: [35.884, 43.784], debecka: [35.870, 43.800], alamo: [35.892, 43.784], presshill: [35.905, 43.784],
  ridge: [35.930, 43.784], pirdaud: [36.000, 43.780], makhmur: [35.776, 43.579],
  north: [36.020, 43.780], nw: [36.000, 43.560], se: [35.770, 43.900], west: [35.860, 43.550],
};
const HILLS = [[P.presshill, 0.3], [P.alamo, 0.2]];
const MOUNTAINS = [[[35.932, 43.600], 1.0], [[35.931, 43.680], 1.0], [P.ridge, 1.0], [[35.929, 43.860], 1.0]];   // Zurqah Ziraw Dagh, the long ridge facing south
const ROADS = [["north", "pirdaud", "ridge", "presshill", "alamo", "crossroads", "west"], ["nw", "crossroads", "debecka", "se"], ["makhmur", "west"]];
const NAMES = {
  crossroads: "The Debecka crossroads", debecka: "Debecka (Dibagah)", alamo: "The Alamo", presshill: "Press Hill",
  ridge: "The ridge (Zurqah Ziraw Dagh)", pirdaud: "Pir Da'ud", makhmur: "Makhmur",
};
const notes = {
  crossroads: "Where the Erbil-Qayyarah road meets Highway 2, held by ODAs 391 and 392 on 6 April 2003",
  alamo: "The low ridge about 900 m north of the crossroads where the teams stopped the Iraqi counter-attack (approximate)",
  presshill: "The second ridge, where the F-14's bomb fell on the Kurdish and American vehicles (approximate)",
  ridge: "The Iraqi line, breached on the morning of 6 April (approximate)",
  pirdaud: "The Kurdish town north of the ridge (approximate)",
};
const map = buildCampaign({
  id: "debecka-2003", script: "make_debecka.mjs", title: "Debecka, April 2003",
  name: "Debecka, 2003 (south of Erbil)",
  start_date: "2003-04-06", calendar: "gregorian", latitude: 36, climate: "mediterranean", climate_shift: 0, base: ".",
  bounds: [43.540, 36.030, 43.910, 35.760], midLat: 35.89, hexKm: 0.5,
  header: [
    "Only the crossroads has a published coordinate; the ridge, Press Hill, the Alamo and Pir Da'ud are",
    "placed from the distances the accounts give, the roads beyond the crossroads by inference. Open",
    "rolling plain, green in April, rising north to the long ridge of Zurqah Ziraw Dagh.",
    "",
    "What happened, briefly: on 6 April 2003 Special Forces teams of Task Force Viking and KDP Peshmerga",
    "broke through the Iraqi line on the ridge and drove south to the Debecka crossroads. An Iraqi",
    "counter-attack with tanks drove them back to a low ridge, where their Javelin missiles stopped it.",
    "A Navy F-14 then bombed the Kurdish and American vehicles behind them by mistake. Numbers below are",
    "round figures for play.",
  ],
  places: P, names: NAMES, notes, water: [], rivers: {}, majorRivers: [], streams: [], bridges: [], fords: [],
  farms: [], woods: [], marsh: [], hills: HILLS, mountains: MOUNTAINS, roads: ROADS,
  towns: ["makhmur"], villages: ["debecka", "pirdaud"],
  kinds: { pirdaud: "camp", crossroads: "objective", ridge: "objective" },
  depots: { pirdaud: ["Americans and Kurds"], makhmur: ["Iraqis"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "ODAs 391 and 392 (Special Forces, with gun trucks)", type: "foot", side: "Americans and Kurds", men: 30, tools: true, at: "pirdaud" },
    { name: "KDP Peshmerga with the teams", type: "foot", side: "Americans and Kurds", men: 80, tools: true, at: "pirdaud" },
    { name: "Iraqi infantry on the ridge", type: "foot", side: "Iraqis", men: 300, tools: true, at: "ridge" },
    { name: "Iraqi mechanised company (tanks and carriers)", type: "foot", side: "Iraqis", men: 140, tools: true, at: "debecka" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
