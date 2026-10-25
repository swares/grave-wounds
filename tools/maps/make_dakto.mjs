// Builds data/maps/dakto-1967.yaml: Dak To, November 1967, on the travel map at 0.5 km a hex, from
// the Dak To base and Tan Canh on Highway 14 west along Route 512 to Ben Het and the hills towards
// the border, Hill 875 among them. Run from this folder after editing: npm ci && node make_dakto.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the US Army's histories give them and as they are summarised
//   publicly: in November 1967 the 4th Infantry Division's 1st Brigade, the 173rd Airborne
//   Brigade and ARVN airborne and infantry battalions fought the North Vietnamese 1st Division and
//   24th Regiment through the jungle hills south and west of Dak To; the fighting climbed Hills
//   724, 823 and 1338 and ended on Hill 875, south-west of the Ben Het camp, where the 2nd and 4th
//   Battalions of the 503rd Infantry fought from 19 to 23 November; the North Vietnamese shelled
//   the Dak To base and blew up its ammunition dump on 15 November;
// - Dak To, Tan Canh, Ben Het and the hills placed after the accounts and approximate; the river,
//   the roads and the high ground drawn by hand. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  base: [14.650, 107.805], tancanh: [14.665, 107.793], benhet: [14.695, 107.665], h875: [14.580, 107.608], h823: [14.640, 107.700],
  h1338: [14.610, 107.770], h724: [14.605, 107.650], southwest: [14.555, 107.600], northwest: [14.725, 107.700],
  north: [14.735, 107.812], south: [14.548, 107.838], west: [14.700, 107.580],
};
const RIVERS = {
  poko: [[14.738, 107.770], [14.700, 107.783], [14.668, 107.787], [14.640, 107.785], [14.600, 107.778], [14.548, 107.762]],
};
const STREAMS = [[[14.700, 107.640], [14.670, 107.700], [14.655, 107.760], [14.650, 107.786]], [[14.620, 107.610], [14.600, 107.700], [14.590, 107.775]]];
const FARMS = [[P.tancanh, 0.9], [P.base, 0.8], [[14.690, 107.800], 0.7], [P.benhet, 0.5]];
const CLEARINGS = [[[14.630, 107.810], 0.8], [[14.675, 107.740], 0.6]];
const HILLS = [[P.h823, 0.8], [P.h724, 0.9], [P.h875, 0.8], [[14.700, 107.740], 1.2], [[14.680, 107.630], 1.0]];
const MOUNTAINS = [[P.h1338, 1.6], [[14.580, 107.700], 2.4], [[14.570, 107.800], 1.8], [[14.725, 107.620], 2.0], [[14.560, 107.630], 1.4]];
const ROADS = [["north", "tancanh", "base", [14.620, 107.830], "south"], ["tancanh", [14.672, 107.740], [14.685, 107.700], "benhet", "west"]];
const NAMES = {
  base: "Dak To base and airstrip", tancanh: "Tan Canh", benhet: "Ben Het Special Forces camp", h875: "Hill 875", h823: "Hill 823",
  h1338: "Hill 1338", h724: "Hill 724",
};
const notes = {
  base: "The brigades' base and airstrip; its ammunition dump blew up under shellfire on 15 November 1967",
  h875: "The 2nd and 4th Battalions, 503rd Infantry fought up it from 19 to 23 November 1967 (approximate)",
  h1338: "Taken by the 4th Infantry Division's 3rd Battalion, 12th Infantry in early November (approximate)",
  benhet: "A Special Forces and CIDG camp near the border, and a fire base for the guns (approximate)",
};
const map = buildCampaign({
  id: "dakto-1967", script: "make_dakto.mjs", title: "Dak To, November 1967",
  name: "Dak To, 1967 (the base to Hill 875)",
  start_date: "1967-11-03", calendar: "gregorian", latitude: 15, climate: "central_highlands", climate_shift: 0, base: "F",
  bounds: [107.570, 14.740, 107.845, 14.545], midLat: 14.64, hexKm: 0.5,
  header: [
    "Dak To, Tan Canh, Ben Het and the hills are placed after the accounts and approximate; the",
    "Poko river, Highway 14, Route 512 and the high ground are drawn by hand. Steep ridges under",
    "triple-canopy jungle and bamboo, rising to 1,300 m south of Dak To; the valley floor round the",
    "base and Tan Canh is cleared. The Poko is a river, crossed where the roads cross it.",
    "",
    "What happened, briefly: in November 1967 the North Vietnamese 1st Division and 24th Regiment",
    "fought the 4th Infantry Division, the 173rd Airborne Brigade and ARVN battalions through the",
    "hills round Dak To. The Americans climbed Hills 724, 823 and 1338; the North Vietnamese blew up",
    "the base's ammunition dump on 15 November; and the battle ended on Hill 875, taken on 23",
    "November after five days. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: [], streams: STREAMS, bridges: [], fords: [],
  farms: FARMS, clearings: CLEARINGS, woods: [], hills: HILLS, mountains: MOUNTAINS, roads: ROADS,
  towns: [], villages: ["tancanh", "benhet"],
  kinds: { base: "camp", h875: "objective", h1338: "objective" },
  depots: { base: ["United States and ARVN"], benhet: ["United States and ARVN"] },   // where each side resupplies (project doc "depots-research")
  tongues: { tancanh: ["vietnamese", "montagnard"] },   // the people's own tongues where they differ from the map's (project doc "tongues-research")
  forces: [
    { name: "173rd Airborne Brigade (2/503 and 4/503)", type: "foot", side: "United States and ARVN", men: 1000, tools: true, at: "base" },
    { name: "1st Brigade, 4th Infantry Division", type: "foot", side: "United States and ARVN", men: 2000, tools: true, at: "base" },
    { name: "ARVN airborne and 42nd Regiment", type: "foot", side: "United States and ARVN", men: 1200, tools: true, at: "tancanh" },
    { name: "Ben Het: Special Forces and CIDG", type: "foot", side: "United States and ARVN", men: 400, tools: true, at: "benhet" },
    { name: "North Vietnamese 1st Division (32nd, 66th and 174th Regiments)", type: "foot", side: "North Vietnamese", men: 6000, tools: true, at: "southwest" },
    { name: "North Vietnamese 24th Regiment", type: "foot", side: "North Vietnamese", men: 2000, tools: true, at: "northwest" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
