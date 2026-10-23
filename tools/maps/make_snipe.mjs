// Builds data/maps/snipe-1942.yaml: the northern sector of the Second Battle of El Alamein on 26
// October 1942, on the travel map at 1 km a hex, from the coast at Sidi Abd el Rahman to El Alamein
// and south past Miteiriya Ridge. Run from this folder after editing: npm ci && node make_snipe.mjs
//
// Sources, all plain fact, and the drawing is ours (project doc "snipe-research"): El Alamein and
// Tell el Aqqaqir at the US NGA's points, Sidi Abd el Rahman at Wikipedia's, Tel el Eisa at the
// German war cemetery on it; Kidney, Snipe and Woodcock derived from Wikipedia's distances to
// Aqqaqir (no source gives a grid reference for them) and only approximate, as are Miteiriya Ridge
// and the Rahman track. The coastline is Natural Earth's (public domain); the railway, the coast
// road, the tracks and the ridges are drawn by hand after the modern ones and are approximate.
// The minefields are not drawn (the travel map has no mines). The divisions stand where
// historyofwar's order of battle and Wikipedia put them; their strengths are round figures.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  snipe: [30.820, 28.758], woodcock: [30.852, 28.764], kidney: [30.842, 28.776], aqqaqir: [30.8728, 28.7400],
  rahman: [30.967, 28.733], teleisa: [30.889, 28.875], elalamein: [30.8301, 28.9550], miteiriya: [30.805, 28.820],
  leaguer: [30.829, 28.757], littorio: [30.816, 28.738],   // the 15th Panzer and Littorio leaguers by Snipe (not places)
  highland: [30.838, 28.830], nzdiv: [30.800, 28.860], aussies: [30.880, 28.900], armour1: [30.848, 28.805],
  south21: [30.728, 28.752], light164: [30.880, 28.800],
};

// ---------- ridges (centre, radius km) ----------
const HILLS = [[[30.808, 28.800], 1.4], [[30.803, 28.830], 1.4], [[30.798, 28.860], 1.2],   // Miteiriya Ridge, running east-south-east (approximate)
  [[30.889, 28.875], 0.8], [[30.8728, 28.7400], 0.6]];                                       // Tel el Eisa; Tell el Aqqaqir

// ---------- roads, tracks and the railway (through places, in order) ----------
const ROADS = [
  [[31.000, 28.600], [30.985, 28.680], "rahman", [30.930, 28.800], [30.900, 28.870], [30.860, 28.930], [30.845, 28.980]],   // the coast road
  [[30.950, 28.600], [30.930, 28.700], [30.905, 28.800], "teleisa", [30.860, 28.920], "elalamein", [30.825, 28.980]],     // the railway, through Tel el Eisa and El Alamein stations
  ["rahman", "aqqaqir", "snipe", [30.760, 28.752], "south21"],                                                           // the Rahman track (its line not sourced)
  ["elalamein", [30.835, 28.900], "highland", "armour1", "kidney", "woodcock"],                                          // the northern corridor, through the minefields (our line)
  ["highland", "miteiriya", "nzdiv"], ["aqqaqir", "light164", "teleisa"],
];

const TOWNS = [];
const VILLAGES = ["rahman", "elalamein"];

const NAMES = { snipe: "Snipe (the battlefield)", woodcock: "Woodcock (approximate)", kidney: "The Kidney feature (approximate)",
  aqqaqir: "Tell el Aqqaqir", rahman: "Sidi Abd el Rahman", teleisa: "Tel el Eisa", elalamein: "El Alamein station",
  miteiriya: "Miteiriya Ridge (approximate)", highland: "51st Division's ground (approximate)", nzdiv: "The New Zealanders' ground (approximate)",
  aussies: "The Australians' ground (approximate)", armour1: "1st Armoured Division's ground (approximate)", light164: "164th Light Division's ground (approximate)" };
const notes = {
  snipe: "A shallow oval depression with camelthorn, about 900 by 450 m: 2nd Rifle Brigade's position from the night of 26/27 October, dug in some 800 yards short of the intended spot",
  woodcock: "The other objective of 26/27 October, a mile north-west of Kidney, for the 2nd King's Royal Rifle Corps",
  kidney: "A kidney-shaped contour on the map ('Hill 28' to the Axis), often called a ridge though a depression",
  aqqaqir: "The Axis defence base on the Rahman track, 3 miles north-west of Kidney",
  rahman: "The coastal mosque at the north end of the Rahman track; 90th Light and Trieste in reserve near it",
  elalamein: "A minor railway station on the coast, inside the Alamein box of the summer's fighting",
  teleisa: "Taken by the Australians in July; the German war cemetery now stands on it",
  miteiriya: "The ridge the New Zealanders took on 23/24 October",
};

const map = buildCampaign({
  id: "snipe-1942", script: "make_snipe.mjs", title: "El Alamein, the northern sector, 26 October 1942",
  name: "Snipe, 1942 (the coast to Miteiriya)",
  start_date: "1942-10-26", calendar: "gregorian", latitude: 31, climate: "egypt_coast", climate_shift: 0, base: ".",
  bounds: [28.60, 31.00, 28.98, 30.72], midLat: 30.86, hexKm: 1,
  header: [
    "El Alamein and Tell el Aqqaqir are at the NGA's points; Kidney, Snipe, Woodcock, Miteiriya Ridge,",
    "the Rahman track and the divisions' ground are only approximate (no grid reference was found for",
    "them). The coastline is Natural Earth's; the railway, roads, tracks and ridges are drawn by hand.",
    "The minefields of the Devil's Gardens are not drawn.",
    "",
    "What happened, briefly: Montgomery's Eighth Army attacked at 21:40 on 23 October 1942 under a",
    "full moon, clearing corridors through the Axis minefields. By the 26th the northern attack had",
    "stalled round the Kidney feature. That night the 2nd Rifle Brigade, with 239 Battery's",
    "six-pounders, went out to seize Snipe, a pivot for the 24th Armoured Brigade, and on the 27th",
    "beat off the German and Italian armour from dawn to dark before coming out on foot. Numbers below",
    "are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: {}, majorRivers: [], streams: [], bridges: [], fords: [],
  hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { snipe: "objective", elalamein: "camp", rahman: "camp" },
  depots: { elalamein: ["Eighth Army"], rahman: ["Axis"] },   // the railway behind each side (our reading: the forward depots were not found)
  forces: [
    { name: "2nd Rifle Brigade and 239 Battery (Turner)", type: "foot", side: "Eighth Army", men: 300, tools: true, at: "kidney" },
    { name: "24th Armoured Brigade", type: "foot", side: "Eighth Army", men: 600, tools: true, at: "armour1" },
    { name: "1st Armoured Division (the rest)", type: "foot", side: "Eighth Army", men: 9000, tools: true, at: "armour1" },
    { name: "51st (Highland) Division", type: "foot", side: "Eighth Army", men: 12000, tools: true, at: "highland" },
    { name: "9th Australian Division", type: "foot", side: "Eighth Army", men: 12000, tools: true, at: "aussies" },
    { name: "2nd New Zealand Division", type: "foot", side: "Eighth Army", men: 9000, tools: true, at: "nzdiv" },
    { name: "Eighth Army supply columns", type: "wagons", side: "Eighth Army", men: 2000, tools: true, at: "elalamein" },
    { name: "15th Panzer Division (the leaguer north of Snipe)", type: "foot", side: "Axis", men: 3000, tools: true, at: "leaguer" },
    { name: "Littorio Armoured Division and Kampfgruppe Stiffelmayer", type: "foot", side: "Axis", men: 3000, tools: true, at: "littorio" },
    { name: "21st Panzer Division (coming north)", type: "foot", side: "Axis", men: 3000, tools: true, at: "south21" },
    { name: "164th Light Division and Trento", type: "foot", side: "Axis", men: 8000, tools: true, at: "light164" },
    { name: "90th Light Division and Trieste", type: "foot", side: "Axis", men: 6000, tools: true, at: "rahman" },
    { name: "Panzerarmee supply columns", type: "wagons", side: "Axis", men: 1500, tools: true, at: "aqqaqir" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
