// Builds data/maps/keating-2009.yaml: the Kamdesh valley in Nuristan and Combat Outpost Keating,
// October 2009, on the travel map at 0.5 km a hex. Run from this folder after editing:
// npm ci && node make_keating.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the US Army's investigation and award citations give them
//   and as they are summarised publicly: Combat Outpost Keating lay at the bottom of a steep
//   valley where the Darreh-ye Kushtoz stream meets the Landay-Sin river, by the village of Urmul,
//   below Kamdesh village; Observation Post Fritsche stood on the ridge above it; on 3 October
//   2009 some 300 insurgents attacked both from the mountainsides at dawn and broke into the
//   outpost; B Troop, 3rd Squadron, 61st Cavalry, with Afghan soldiers and two Latvian advisers,
//   about 70 men, took it back by the afternoon with air support; eight Americans were killed; the
//   outpost was given up three days later as planned;
// - the outpost, the observation post and the villages placed after the accounts and approximate;
//   the mountains, the river, the stream, the terraces and the track drawn by hand. They are
//   approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  keating: [35.384, 71.330], fritsche: [35.373, 71.338], urmul: [35.387, 71.320], kamdesh: [35.412, 71.345], mandigal: [35.360, 71.300],
  north: [35.440, 71.330], east: [35.390, 71.390], south: [35.335, 71.300], west: [35.400, 71.270],
};
const RIVERS = {
  landaysin: [[35.455, 71.315], [35.420, 71.322], [35.395, 71.325], [35.384, 71.324], [35.365, 71.312], [35.345, 71.300], [35.325, 71.290]],
};
const BRIDGES = [[35.385, 71.3245]].map((p, i) => { P["bridge" + i] = p; return "bridge" + i });
const STREAMS = [[[35.395, 71.400], [35.390, 71.370], [35.386, 71.345], [35.384, 71.328]]];   // the Darreh-ye Kushtoz, down from the east to the outpost
const FARMS = [[P.keating, 0.4], [P.urmul, 0.4], [P.kamdesh, 0.8], [[35.400, 71.326], 0.5], [P.mandigal, 0.5], [[35.430, 71.322], 0.5]];
const WOODS = [[[35.395, 71.290], 1.4], [[35.370, 71.360], 1.6], [[35.420, 71.370], 1.4], [[35.350, 71.335], 1.2], [[35.440, 71.290], 1.2]];
const HILLS = [[P.fritsche, 0.4]];
const ROADS = [["north", [35.420, 71.326], [35.400, 71.327], "keating", [35.365, 71.315], "south"], ["keating", [35.398, 71.335], "kamdesh"]];
const NAMES = { keating: "Combat Outpost Keating", fritsche: "Observation Post Fritsche", urmul: "Urmul", kamdesh: "Kamdesh", mandigal: "Mandigal" };
const notes = {
  keating: "B Troop, 3-61 Cavalry's outpost at the bottom of the valley, attacked at dawn on 3 October 2009 (approximate)",
  fritsche: "The observation post on the ridge above, with the outpost's mortars; attacked at the same time (approximate)",
  kamdesh: "The district's main village, on the mountainside above the outpost (approximate)",
};
const map = buildCampaign({
  id: "keating-2009", script: "make_keating.mjs", title: "The Kamdesh valley and COP Keating, October 2009",
  name: "COP Keating, 2009 (the Kamdesh valley)",
  start_date: "2009-10-03", calendar: "gregorian", latitude: 35, climate: "hindu_kush", climate_shift: 0, base: "M",
  bounds: [71.260, 35.460, 71.410, 35.320], midLat: 35.39, hexKm: 0.5,
  header: [
    "The outpost, the observation post and the villages are placed after the accounts and",
    "approximate; the mountains, the Landay-Sin and its side stream, the terraces, the woods and the",
    "track are drawn by hand. Nearly all of it is steep mountainside under deodar and scrub; the",
    "valley floor and the villages' terraces are the only level ground.",
    "",
    "What happened, briefly: Combat Outpost Keating sat at the bottom of the Kamdesh valley, overlooked",
    "on every side, with Observation Post Fritsche on the ridge above. At dawn on 3 October 2009",
    "some 300 insurgents attacked both from the mountainsides, set much of the outpost alight and",
    "broke into it. B Troop, 3rd Squadron, 61st Cavalry, with Afghan soldiers and two Latvian",
    "advisers, about 70 men, fought them back out by the afternoon with Apaches and jets; eight",
    "Americans were killed. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["landaysin"], streams: STREAMS, bridges: BRIDGES, fords: [],
  farms: FARMS, woods: WOODS, hills: HILLS, mountains: [], roads: ROADS, towns: [], villages: ["urmul", "kamdesh", "mandigal"],
  kinds: { keating: "objective", fritsche: "objective" },
  depots: { keating: ["Coalition"] },   // where each side resupplies (project doc "depots-research")
  tongues: { kamdesh: ["nuristani", "pashto"], urmul: ["nuristani", "pashto"] },   // the people's own tongues where they differ from the map's (project doc "tongues-research")
  forces: [
    { name: "B Troop, 3-61 Cavalry, with Afghan soldiers and Latvian advisers (COP Keating)", type: "foot", side: "Coalition", men: 70, tools: true, at: "keating" },
    { name: "Observation Post Fritsche", type: "foot", side: "Coalition", men: 20, tools: true, at: "fritsche" },
    { name: "Insurgents on the northern slopes", type: "foot", side: "Insurgents", men: 120, tools: false, at: "north" },
    { name: "Insurgents on the eastern slopes", type: "foot", side: "Insurgents", men: 100, tools: false, at: "east" },
    { name: "Insurgents on the western slopes", type: "foot", side: "Insurgents", men: 80, tools: false, at: "west" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
