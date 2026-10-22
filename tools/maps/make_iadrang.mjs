// Builds data/maps/iadrang-1965.yaml: the Ia Drang valley and the Chu Pong massif, 14-17
// November 1965, on the travel map at 0.5 km a hex. Run from this folder after editing:
// npm ci && node make_iadrang.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the US Army's accounts give them and as they are summarised
//   publicly: landing zone X-Ray in a clearing about 100 m across at the eastern foot of the
//   Chu Pong massif, a dry creek bed on its west side, the Ia Drang about 2 km to the
//   north-west; landing zone Albany about 2.5 km north-east of X-Ray; the artillery's landing
//   zone Falcon about 8 km to the north-east; the 1st Battalion, 7th Cavalry landed by
//   helicopter from 10:48 on 14 November and was attacked by the 7th and 9th Battalions of
//   the North Vietnamese 66th Regiment coming down off the massif;
// - X-Ray, Albany and Falcon are at their published positions, rounded; Columbus and Victor are
//   placed after the accounts and approximate; the border with Cambodia runs just off the
//   west edge;
// - the massif, the hills, the river and its streams and the scrub forest are drawn by hand
//   through those places. They are approximate. There are no roads.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  xray: [13.568, 107.714], albany: [13.595, 107.715], falcon: [13.623, 107.764], columbus: [13.585, 107.748], victor: [13.553, 107.738],
  chupong: [13.545, 107.672], knoll: [13.572, 107.706], border: [13.600, 107.585],
  west: [13.560, 107.600], northwest: [13.640, 107.640],   // where the North Vietnamese battalions come in (not places)
};

// ---------- the Ia Drang (crossed at its fords) and the streams ----------
const RIVERS = {
  iadrang: [[13.655, 107.815], [13.630, 107.780], [13.605, 107.745], [13.590, 107.712], [13.583, 107.680], [13.585, 107.640], [13.595, 107.590]],
};
const STREAMS = [
  [[13.545, 107.760], [13.570, 107.750], [13.600, 107.735]],
];
const FORDS = [[13.596, 107.728], [13.585, 107.690], [13.618, 107.767]].map((p, i) => { P["ford" + i] = p; return "ford" + i });
const BRIDGES = [];

// ---------- scrub forest everywhere, the massif, the clearings ----------
const MOUNTAINS = [[P.chupong, 3.2], [[13.520, 107.640], 3.0], [[13.525, 107.700], 1.8]];
const HILLS = [[[13.560, 107.690], 1.4], [[13.580, 107.650], 1.5], [[13.535, 107.740], 1.2], [[13.650, 107.700], 1.5]];
const CLEARINGS = [[P.xray, 0.3], [P.albany, 0.3], [P.falcon, 0.4], [P.columbus, 0.3], [P.victor, 0.3], [[13.615, 107.700], 0.8], [[13.630, 107.740], 0.9]];
const ROADS = [];

const NAMES = { xray: "Landing zone X-Ray", albany: "Landing zone Albany", falcon: "Landing zone Falcon (the guns)", columbus: "Landing zone Columbus",
  victor: "Landing zone Victor", chupong: "The Chu Pong massif", knoll: "The knoll of the cut-off platoon", border: "The Cambodian border (just to the west)" };
const notes = {
  xray: "A clearing about 100 m across at the foot of the Chu Pong; the 1st Battalion, 7th Cavalry landed here from 10:48 on 14 November 1965",
  knoll: "2nd Platoon, B Company was cut off here on the afternoon of the 14th and held until relieved the next afternoon (approximate)",
  falcon: "Two batteries of 105 mm howitzers fired for X-Ray from here, about 8 km away",
  albany: "The 2nd Battalion, 7th Cavalry was ambushed in the tall grass short of here on 17 November",
  victor: "The 2nd Battalion, 5th Cavalry landed here on the 15th and marched to X-Ray (approximate)",
  columbus: "Where the 2nd Battalion, 5th Cavalry marched on the 17th (approximate)",
};

const map = buildCampaign({
  id: "iadrang-1965", script: "make_iadrang.mjs", title: "The Ia Drang valley and the Chu Pong massif, November 1965",
  name: "Ia Drang, 1965 (X-Ray and Albany)",
  start_date: "1965-11-14", calendar: "gregorian", latitude: 14, climate: "central_highlands", climate_shift: 0, base: "F",
  bounds: [107.585, 13.665, 107.825, 13.505], midLat: 13.58, hexKm: 0.5,
  header: [
    "X-Ray, Albany and Falcon are at their published positions, rounded; Columbus, Victor and the",
    "cut-off platoon's knoll are placed after the accounts and approximate; the massif, hills,",
    "river and streams are drawn by hand. Nearly all of it is scrub forest and tall elephant grass",
    "(forest), with a few clearings; there are no roads. Cambodia is just off the west edge.",
    "",
    "What happened, briefly: on 14 November 1965 the 1st Battalion, 7th Cavalry (Lieutenant Colonel",
    "Harold Moore), about 450 men, was flown by sixteen helicopters, a lift every half hour or so,",
    "into landing zone X-Ray at the foot of the Chu Pong, where two battalions of the North",
    "Vietnamese 66th Regiment were waiting above. The fighting began within the hour and went on",
    "for three days, held by artillery from Falcon, air strikes and more battalions flown in. On",
    "17 November the 2nd Battalion, 7th Cavalry, marching to Albany, was ambushed in the tall grass",
    "by the 66th's 8th Battalion and the 33rd Regiment. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["iadrang"], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  clearings: CLEARINGS, woods: [], hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: [], villages: [],
  kinds: { xray: "objective", falcon: "camp" },
  depots: { falcon: ["United States"], chupong: ["North Vietnamese"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "1st Battalion, 7th Cavalry (Moore)", type: "foot", side: "United States", men: 450, tools: true, at: "xray" },
    { name: "2nd Battalion, 7th Cavalry", type: "foot", side: "United States", men: 500, tools: true, at: "falcon" },
    { name: "2nd Battalion, 5th Cavalry (Tully)", type: "foot", side: "United States", men: 450, tools: true, at: "victor" },
    { name: "1st Battalion, 21st Artillery (two batteries at Falcon)", type: "foot", side: "United States", men: 200, tools: true, at: "falcon" },
    { name: "66th Regiment, 7th and 9th Battalions", type: "foot", side: "North Vietnamese", men: 1100, tools: true, at: "chupong" },
    { name: "66th Regiment, 8th Battalion", type: "foot", side: "North Vietnamese", men: 550, tools: true, at: "northwest" },
    { name: "33rd Regiment, 1st and 3rd Battalions", type: "foot", side: "North Vietnamese", men: 800, tools: true, at: "west" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
