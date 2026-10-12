// Builds data/maps/heartbreak-1951.yaml: Heartbreak Ridge and its valleys, September-October 1951,
// on the travel map at 0.5 km a hex. Run from this folder after editing: npm ci && node make_heartbreak.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the US Army's account (Hermes, Truce Tent and Fighting Front, a work of the US government)
//   as summarised publicly, for the facts: the ridge runs north from Hill 894 to Hill 931, its
//   highest peak, about 1,300 yards on, and Hill 851 about 2,100 yards beyond, between the
//   Mundung-ni valley to the west and the Sat'ae-ri valley to the east; the US 2nd Infantry
//   Division, with the French and Netherlands battalions, attacked it from 13 September 1951
//   against the North Korean III Corps, later reinforced by a Chinese division, and took it on
//   15 October, after tanks drove up the Mundung-ni valley behind it (Operation Touchdown);
// - the peaks at their published spacing, the ridge at the published position, rounded; the
//   villages, valleys and roads placed after the accounts and approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  h894: [38.289, 128.017], h931: [38.300, 128.017], h851: [38.317, 128.015], mundung: [38.335, 127.985], satae: [38.300, 128.050],
  bloody: [38.255, 128.000], south: [38.225, 128.010], north: [38.375, 128.000], northeast: [38.370, 128.060], tankpark: [38.250, 127.975],
};
const STREAMS = [[[38.375, 127.985], "mundung", [38.300, 127.982], [38.250, 127.975], [38.222, 127.970]], [[38.360, 128.055], "satae", [38.250, 128.045], [38.222, 128.040]]];
const FARMS = [[P.mundung, 0.7], [P.satae, 0.6], [[38.270, 127.978], 0.6], [[38.265, 128.045], 0.5]];
const MOUNTAINS = [[P.h931, 1.0], [P.h851, 0.9], [P.h894, 0.8], [[38.330, 127.940], 2.2], [[38.270, 128.090], 2.0], [[38.350, 128.090], 1.8], [P.bloody, 1.0]];
const ROADS = [["south", "tankpark", [38.300, 127.981], "mundung", "north"], ["south", [38.250, 128.044], "satae", "northeast"]];
const NAMES = { h894: "Hill 894", h931: "Hill 931", h851: "Hill 851", mundung: "Mundung-ni", satae: "Sat'ae-ri", bloody: "Bloody Ridge (south)", tankpark: "The 72nd Tank Battalion's start" };
const notes = {
  h931: "The ridge's highest peak, fought over for a month and taken by the 23rd Infantry and the French Battalion on 13 October 1951",
  h894: "The ridge's southern end, taken at the start of the battle",
  h851: "Taken by the French Battalion on 13 October (approximate)",
  mundung: "Tanks of the 72nd Tank Battalion drove up the valley to here on 10 October, behind the ridge (approximate)",
};
const map = buildCampaign({
  id: "heartbreak-1951", script: "make_heartbreak.mjs", title: "Heartbreak Ridge, September-October 1951",
  name: "Heartbreak Ridge, 1951 (the Mundung-ni and Sat'ae-ri valleys)",
  start_date: "1951-09-13", calendar: "gregorian", latitude: 38, climate: "korea", climate_shift: -2, base: "h",
  bounds: [127.920, 38.380, 128.100, 38.220], midLat: 38.30, hexKm: 0.5,
  header: [
    "The peaks are at their published spacing along the ridge, rounded; the villages, valleys and",
    "roads are placed after the accounts and approximate; the mountains are drawn by hand. Steep,",
    "wooded mountains (hills, mountains); farmed valley floors; streams down each valley.",
    "",
    "What happened, briefly: after Bloody Ridge, in September 1951 the US 2nd Infantry Division",
    "attacked the next ridge north, held by the North Korean 6th and 12th Divisions in log-and-",
    "earth bunkers. The 23rd Infantry and the French Battalion went up its narrow spurs again and",
    "again for a month, taking and losing Hill 931. In October the division widened the attack,",
    "and tanks drove up the Mundung-ni valley west of the ridge into the enemy's rear (Operation",
    "Touchdown); the ridge fell on 13-15 October. The division lost some 3,700 men; the North",
    "Koreans and Chinese, by its count, about 25,000. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: {}, majorRivers: [], streams: STREAMS, bridges: [], fords: [],
  farms: FARMS, woods: [], hills: [], mountains: MOUNTAINS, roads: ROADS, towns: [], villages: ["mundung", "satae"],
  kinds: { h931: "objective", h851: "objective" },
  forces: [
    { name: "23rd Infantry and the French Battalion", type: "foot", side: "United Nations", men: 3500, tools: true, at: "h894" },
    { name: "9th Infantry", type: "foot", side: "United Nations", men: 3000, tools: true, at: "bloody" },
    { name: "38th Infantry and the Netherlands Battalion", type: "foot", side: "United Nations", men: 3500, tools: true, at: "south" },
    { name: "72nd Tank Battalion", type: "wagons", side: "United Nations", men: 300, tools: false, at: "tankpark" },
    { name: "North Korean 6th Division", type: "foot", side: "North Koreans", men: 3000, tools: true, at: "h931" },
    { name: "North Korean 12th Division", type: "foot", side: "North Koreans", men: 3000, tools: true, at: "h851" },
    { name: "Chinese 204th Division", type: "foot", side: "North Koreans", men: 6000, tools: true, at: "north" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
