// Builds data/maps/grozny-1995.yaml: Grozny and its approaches, 31 December 1994 to January 1995,
// on the travel map at 0.5 km a hex, from the Severny airport in the north to Khankala in the east.
// Run from this folder after editing: npm ci && node make_grozny.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as they are summarised publicly from the Russian and Western
//   accounts: on 31 December 1994 Russian columns drove into Grozny from the north, the west and
//   the east to take the Presidential Palace and the railway station; the northern group's 131st
//   (Maikop) Motor Rifle Brigade reached the station and the 81st Motor Rifle Regiment the palace
//   district, where Chechen fighters with rocket launchers in the buildings destroyed much of
//   their armour that night; the western and eastern groups stopped short; the palace fell on 19
//   January 1995 and the city by March;
// - the palace, the station, Minutka square, the airports and the suburbs placed after the
//   accounts and approximate; the Sunzha, the roads, the railway and the hills drawn by hand.
//   They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  palace: [43.318, 45.692], station: [43.307, 45.708], minutka: [43.297, 45.716], severny: [43.388, 45.698], khankala: [43.297, 45.772],
  north: [43.398, 45.700], northwest: [43.375, 45.615], west: [43.315, 45.585], east: [43.292, 45.815], south: [43.255, 45.700],
};
const RIVERS = {
  sunzha: [[43.255, 45.630], [43.280, 45.660], [43.300, 45.685], [43.315, 45.700], [43.335, 45.715], [43.360, 45.745], [43.380, 45.790], [43.395, 45.815]],
};
// The rest of the city (unnamed): every hex of an uneven oval of blocks round the centre, from
// Staropromyslovsky in the north-west to the south-east, but not on the Sunzha itself.
const nearRiver = ([lat, lon]) => RIVERS.sunzha.some(([a, o], i) => {
  const [b, q] = RIVERS.sunzha[i + 1] || [a, o], t = Math.max(0, Math.min(1, ((lat - a) * (b - a) + (lon - o) * (q - o) * 0.53) / (((b - a) ** 2 + (q - o) ** 2 * 0.53) || 1)));
  return Math.hypot(lat - (a + (b - a) * t), (lon - (o + (q - o) * t)) * 0.73) < 0.003;
});
const CITY = {};
for (let lat = 43.280; lat <= 43.352; lat += 0.0035){
  for (let lon = 45.625; lon <= 45.745; lon += 0.005){
    const inOval = ((lat - 43.316) / 0.036) ** 2 + ((lon - 45.685) / (0.062 - (lat - 43.316) * 0.5)) ** 2 <= 1;
    if (inOval && !nearRiver([lat, lon])) CITY["city" + Object.keys(CITY).length] = [lat, lon];
  }
}
Object.assign(P, CITY);
const HILLS = [[[43.265, 45.610], 1.5], [[43.255, 45.760], 1.5], [[43.385, 45.640], 1.2]];
const FARMS = [[[43.375, 45.740], 1.5], [[43.270, 45.700], 1.5], [[43.330, 45.600], 1.2]];
const ROADS = [
  ["north", "severny", [43.350, 45.695], "palace", "station", "minutka", "south"],
  ["northwest", [43.350, 45.640], "palace"], ["west", [43.315, 45.640], "palace"], ["station", "khankala", "east"],
];
const NAMES = {
  palace: "The Presidential Palace", station: "Grozny railway station", minutka: "Minutka square", severny: "Severny airport", khankala: "Khankala airbase",
};
const notes = {
  palace: "Dudayev's headquarters; the 81st Motor Rifle Regiment's objective on 31 December 1994; taken on 19 January 1995 (approximate)",
  station: "The 131st Brigade reached it on 31 December 1994 and was cut off and largely destroyed there (approximate)",
  minutka: "A Chechen stronghold in the south-east of the city, held into February (approximate)",
};
const map = buildCampaign({
  id: "grozny-1995", script: "make_grozny.mjs", title: "Grozny, December 1994 to January 1995",
  name: "Grozny, 1995 (the New Year's assault)",
  start_date: "1994-12-31", calendar: "gregorian", latitude: 43, climate: "continental", climate_shift: 0, base: ".",
  bounds: [45.580, 43.400, 45.820, 43.250], midLat: 43.32, hexKm: 0.5,
  header: [
    "The palace, the station, Minutka square, the airports and the suburbs are placed after the",
    "accounts and approximate; the Sunzha, the roads and the hills are drawn by hand. A city of",
    "apartment blocks and houses on the Sunzha, with oil works and open steppe and fields round it,",
    "low hills to the south; the Sunzha is crossed on the city's bridges.",
    "",
    "What happened, briefly: on 31 December 1994 Russian armoured columns drove into Grozny from",
    "three sides. The 131st Brigade reached the railway station and the 81st Regiment the palace",
    "district, but Chechen fighters in the buildings knocked out much of their armour with rocket",
    "launchers that night and the next day; the columns from the west and east stopped short. The",
    "Russians fought on block by block, took the palace on 19 January 1995 and the city by March.",
    "Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: [], streams: [], bridges: [], fords: [],
  farms: FARMS, woods: [], hills: HILLS, mountains: [], roads: ROADS,
  towns: ["palace", "station", "minutka", ...Object.keys(CITY)], villages: [],
  kinds: { palace: "objective", station: "objective", severny: "camp" },
  forces: [
    { name: "131st (Maikop) Motor Rifle Brigade", type: "foot", side: "Russians", men: 1500, tools: true, at: "northwest" },
    { name: "81st Motor Rifle Regiment", type: "foot", side: "Russians", men: 1300, tools: true, at: "north" },
    { name: "Western group (19th Motor Rifle Division)", type: "foot", side: "Russians", men: 2000, tools: true, at: "west" },
    { name: "Eastern group (129th Motor Rifle Regiment)", type: "foot", side: "Russians", men: 2000, tools: true, at: "east" },
    { name: "Chechen fighters at the palace", type: "foot", side: "Chechens", men: 1000, tools: true, at: "palace" },
    { name: "Chechen fighters round the station", type: "foot", side: "Chechens", men: 500, tools: true, at: "station" },
    { name: "Chechen fighters at Minutka square", type: "foot", side: "Chechens", men: 500, tools: true, at: "minutka" },
    { name: "Chechen reserves (the south)", type: "foot", side: "Chechens", men: 1000, tools: true, at: "south" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
