// Builds data/maps/osan-1950.yaml: Task Force Smith and the battle of Osan, 5 July 1950, the
// first fight of the US Army in the Korean War, on the travel map at 1 km a hex, from Suwon in
// the north to P'yongt'aek in the south and Ansong in the east. Run from this folder after
// editing: npm ci && node make_osan.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the US Army's account of the battle (Appleman, South to the Naktong, and the Army's
//   extract of it, both works of the US government): the force held a saddle in a line of hills
//   that crosses the Suwon-Osan highway at right angles about 2 miles north of Osan, the
//   railroad crossing the same hill line about a mile east of the highway; Suwon about 8 miles
//   north, P'yongt'aek about 12 miles south, Ansong to the east;
// - the saddle (Jukmiryeong) is placed at the memorial there (37.184 N, 127.050 E), the towns at
//   their modern centres, rounded;
// - the hills, streams and the roads and railroad between the towns are drawn by hand through
//   those places. They are approximate; most of the low ground is rice paddy and fields.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  suwon: [37.268, 127.015], saddle: [37.184, 127.050], osan: [37.150, 127.070], pyeongtaek: [36.992, 127.088],
  ansong: [37.008, 127.270], railcross: [37.182, 127.066], guns: [37.168, 127.046], byeongjeom: [37.205, 127.033],
  songtan: [37.072, 127.060], jinwi: [37.110, 127.085], yangseong: [37.110, 127.190], hwaseong: [37.205, 127.000],
  north: [37.290, 127.010], northeast: [37.285, 127.060],   // where the North Korean columns come in (not places)
};

// ---------- streams (brooks: wet, slow ground, crossed anywhere) ----------
const STREAMS = [
  [[37.275, 127.050], [37.235, 127.055], [37.200, 127.040], [37.160, 127.020], [37.110, 126.990]],   // Hwangguji stream, west of the highway
  [[37.190, 127.090], [37.160, 127.080], "jinwi", [37.070, 127.090], [37.000, 127.100]],              // Osan stream and the Jinwi
  [[37.120, 127.230], [37.060, 127.200], [37.020, 127.150], [36.995, 127.120]],                       // a stream down from Ansong way
];
const RIVERS = {}, BRIDGES = [], FORDS = [];

// ---------- hills and woods: the hill line north of Osan, the ridges to the east ----------
const HILLS = [[[37.186, 127.025], 1.3], [[37.184, 127.040], 1.3], [[37.185, 127.058], 1.3], [[37.181, 127.074], 1.2], [[37.183, 127.088], 1.2], [[37.170, 127.035], 1.2],   // the hill line at the saddle; Doksan
  [[37.230, 127.090], 2.2], [[37.150, 127.150], 2.6], [[37.090, 127.150], 2.4], [[37.230, 126.990], 1.8], [[37.060, 127.240], 2.0],
  [[37.130, 127.010], 1.4], [[37.270, 127.110], 2.0]];
const MOUNTAINS = [[[37.180, 127.200], 2.4], [[37.250, 127.180], 2.2]];
const WOODS = [[[37.170, 127.035], 0.8], [[37.150, 127.150], 1.4], [[37.250, 127.180], 1.2]];

// ---------- roads and the railroad (through places, in order) ----------
const ROADS = [
  ["north", "suwon", "byeongjeom", "saddle", "osan", "jinwi", "songtan", "pyeongtaek"],                                  // the main highway, Suwon to P'yongt'aek
  ["northeast", [37.240, 127.060], [37.210, 127.064], "railcross", [37.165, 127.074], "osan", [37.080, 127.072], "pyeongtaek"],   // the railroad from Seoul
  ["osan", [37.120, 127.130], "yangseong", [37.050, 127.240], "ansong"],                                               // the road east to Ansong
  ["suwon", "hwaseong"], ["pyeongtaek", [37.000, 127.180], "ansong"],
];

const TOWNS = ["suwon", "osan", "pyeongtaek"];
const VILLAGES = ["ansong", "byeongjeom", "songtan", "jinwi", "yangseong", "hwaseong"];

const NAMES = { suwon: "Suwon", saddle: "The saddle north of Osan (Jukmiryeong)", osan: "Osan", pyeongtaek: "P'yongt'aek",
  ansong: "Ansong", railcross: "The railroad over the hill line", guns: "The howitzer position", byeongjeom: "Pyongjom",
  songtan: "Songt'an", jinwi: "Chinwi", yangseong: "Yangsong", hwaseong: "Hwasong" };
const notes = {
  saddle: "Task Force Smith dug in astride the highway here before dawn on 5 July 1950; a memorial stands there now",
  railcross: "C Company's right flank was bent back along a finger ridge beside the railroad (approximate)",
  guns: "A battery of the 52nd Field Artillery, about 2,000 yards behind the ridge and just west of the highway (approximate)",
  suwon: "Where the North Korean column came from: the tanks first, then the infantry in trucks and on foot",
  ansong: "Where the survivors gathered that evening and the next day",
};

const map = buildCampaign({
  id: "osan-1950", script: "make_osan.mjs", title: "Task Force Smith and the battle of Osan, July 1950",
  name: "Osan, 1950 (Suwon to P'yongt'aek)",
  start_date: "1950-07-05", calendar: "gregorian", latitude: 37, climate: "korea", climate_shift: 0, base: "f",
  bounds: [126.96, 37.300, 127.300, 36.975], midLat: 37.14, hexKm: 1,
  header: [
    "The saddle north of Osan is at its memorial; the towns are at their modern centres, rounded;",
    "the hills, streams, roads and railroad are drawn by hand and approximate. Most of the low",
    "ground is rice paddy and fields (farmland).",
    "",
    "What happened, briefly: the North Korean army crossed into the South on 25 June 1950 and took",
    "Seoul three days later. The first American ground force to reach the fighting, Task Force",
    "Smith (two short rifle companies of the 1st Battalion, 21st Infantry, with recoilless rifles",
    "and mortars, about 400 men, and a battery of 105 mm howitzers), dug in across the highway north",
    "of Osan before dawn on 5 July. At about 8 that morning the tanks of the 107th Tank Regiment",
    "came down the road from Suwon: the howitzers and bazookas stopped a few, but more than thirty",
    "drove through and on south. Near noon the infantry of the 4th Division followed, some 5,000",
    "men; they worked round both flanks, and in the afternoon the force fell back across the",
    "paddies under fire, losing most heavily on the way. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: [], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  woods: WOODS, hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { saddle: "objective", osan: "objective", pyeongtaek: "camp" },
  depots: { pyeongtaek: ["United Nations"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "Task Force Smith (1st Battalion, 21st Infantry, B and C Companies)", type: "foot", side: "United Nations", men: 415, tools: true, at: "saddle" },
    { name: "Battery of the 52nd Field Artillery (105 mm howitzers)", type: "foot", side: "United Nations", men: 125, tools: true, at: "guns" },
    { name: "34th Infantry (forward battalion)", type: "foot", side: "United Nations", men: 700, tools: true, at: "pyeongtaek" },
    { name: "107th Tank Regiment (T-34s: fire support on the field map)", type: "wagons", side: "North Koreans", men: 150, tools: false, at: "north" },
    { name: "16th Regiment, 4th Division", type: "foot", side: "North Koreans", men: 3000, tools: true, at: "north" },
    { name: "18th Regiment, 4th Division", type: "foot", side: "North Koreans", men: 3000, tools: true, at: "northeast" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
