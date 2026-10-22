// Builds data/maps/fallujah-2004.yaml: Fallujah and its approaches, November 2004, on the travel map
// at 0.5 km a hex, from the Euphrates and the Jolan in the west to Camp Fallujah in the east.
// Run from this folder after editing: npm ci && node make_fallujah.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the US Marine Corps' and Army's histories give them and as
//   they are summarised publicly: in Operation Phantom Fury (al-Fajr), from 7 November 2004, two
//   Marine regimental combat teams with Army armoured battalions and Iraqi battalions attacked
//   south into the city from the railway on its northern edge, RCT-1 on the west through the
//   Jolan and RCT-7 on the east, while an Army brigade held the cordon round it; the hospital
//   peninsula and the bridges over the Euphrates were taken first; the insurgents fought from the
//   houses, with rocket launchers, machine guns and bombs; the city was declared secure by late
//   November, though clearing went on into December;
// - the districts, the railway station, the bridges, the hospital and Camp Fallujah placed after
//   the accounts and approximate; the river, the roads and the city's extent drawn by hand. They
//   are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  jolan: [33.360, 43.766], queens: [33.340, 43.800], shuhada: [33.326, 43.776], centre: [33.348, 43.784], station: [33.368, 43.790],
  hospital: [33.350, 43.750], cloverleaf: [33.346, 43.812], camp: [33.322, 43.858], northwest: [33.385, 43.765], northeast: [33.385, 43.805],
  south: [33.300, 43.785],
};
const RIVERS = {
  euphrates: [[33.400, 43.725], [33.380, 43.745], [33.362, 43.757], [33.350, 43.760], [33.340, 43.756], [33.330, 43.748], [33.315, 43.738], [33.295, 43.720]],
};
// The rest of the city (unnamed): every point of an uneven square of blocks east of the river, from the railway in the north
// to the industrial south.
const CITY = {};
for (let lat = 33.322; lat <= 33.366; lat += 0.003){
  for (let lon = 43.764; lon <= 43.812; lon += 0.004){
    if (lon - 43.764 > (33.366 - lat) * 0.3 || lat > 33.335) CITY["city" + Object.keys(CITY).length] = [lat, lon];
  }
}
Object.assign(P, CITY);
const FARMS = [[[33.380, 43.730], 1.4], [[33.300, 43.740], 1.4], [[33.390, 43.840], 1.2], [[33.305, 43.830], 1.2]];
const MARSH = [[[33.355, 43.735], 0.6]];
const ROADS = [
  [[33.346, 43.700], [33.348, 43.745], "hospital", [33.349, 43.759], "centre", "cloverleaf", [33.336, 43.840], "camp", [33.320, 43.880]],
  ["station", "centre", "shuhada", "south"], [[33.400, 43.800], "station"],
];
const BRIDGES = [[33.349, 43.759], [33.338, 43.754]].map((p, i) => { P["bridge" + i] = p; return "bridge" + i });
const NAMES = {
  jolan: "The Jolan", queens: "The Queens (al-Askari)", shuhada: "Shuhada", centre: "Fallujah, the city centre", station: "The railway station",
  hospital: "Fallujah hospital", cloverleaf: "The cloverleaf", camp: "Camp Fallujah",
};
const notes = {
  jolan: "The old north-western quarter, an insurgent stronghold; RCT-1 attacked south through it from 8 November 2004 (approximate)",
  station: "The railway on the city's northern edge, the start line for the assault (approximate)",
  hospital: "Taken on the night of 7 November 2004 with the bridges, by Iraqi commandos and Marines (approximate)",
};
const map = buildCampaign({
  id: "fallujah-2004", script: "make_fallujah.mjs", title: "Fallujah, November 2004",
  name: "Fallujah, 2004 (Operation Phantom Fury)",
  start_date: "2004-11-07", calendar: "gregorian", latitude: 33, climate: "arid", climate_shift: 0, base: ".",
  bounds: [43.700, 33.400, 43.880, 33.295], midLat: 33.35, hexKm: 0.5,
  header: [
    "The districts, the railway station, the bridges, the hospital and Camp Fallujah are placed",
    "after the accounts and approximate; the Euphrates, the roads and the city's extent are drawn by",
    "hand. A city of walled, flat-roofed concrete houses on the east bank of the Euphrates, with",
    "palm groves and fields by the river and open desert round it; the river is crossed on its two",
    "bridges.",
    "",
    "What happened, briefly: on the night of 7 November 2004 Iraqi commandos and Marines took the",
    "hospital and the bridges west of Fallujah. The next night two Marine regimental combat teams,",
    "with Army armour and Iraqi battalions, attacked south across the railway into the city, RCT-1",
    "through the Jolan and RCT-7 to the east, while an Army brigade held the cordon. They fought",
    "house by house to the south of the city in about ten days, and cleared it into December.",
    "Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["euphrates"], streams: [], bridges: BRIDGES, fords: [],
  farms: FARMS, woods: [], marsh: MARSH, hills: [], mountains: [], roads: ROADS,
  towns: ["jolan", "queens", "shuhada", "centre", ...Object.keys(CITY)], villages: [],
  kinds: { jolan: "objective", camp: "camp", station: "objective" },
  depots: { camp: ["Coalition"], jolan: ["Insurgents"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "Regimental Combat Team 1 (3/1 and 3/5 Marines, 2-7 Cavalry)", type: "foot", side: "Coalition", men: 3000, tools: true, at: "northwest" },
    { name: "Regimental Combat Team 7 (1/8 and 1/3 Marines, 2-2 Infantry)", type: "foot", side: "Coalition", men: 3000, tools: true, at: "northeast" },
    { name: "Iraqi army and commando battalions", type: "foot", side: "Coalition", men: 2000, tools: true, at: "hospital" },
    { name: "2nd Brigade, 1st Cavalry Division (the cordon)", type: "foot", side: "Coalition", men: 1500, tools: true, at: "south" },
    { name: "Insurgents in the Jolan", type: "foot", side: "Insurgents", men: 1000, tools: true, at: "jolan" },
    { name: "Insurgents in the city centre and the Queens", type: "foot", side: "Insurgents", men: 1000, tools: true, at: "queens" },
    { name: "Insurgents in Shuhada and the south", type: "foot", side: "Insurgents", men: 1000, tools: true, at: "shuhada" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
