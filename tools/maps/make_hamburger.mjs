// Builds data/maps/hamburger-1969.yaml: the A Shau valley, May 1969, on the travel map at 0.5 km a
// hex, from the Laotian border and Dong Ap Bia (Hill 937) east across the valley floor to A Luoi
// and Ta Bat. Run from this folder after editing: npm ci && node make_hamburger.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the US Army's accounts give them and as they are summarised
//   publicly: in Operation Apache Snow the 101st Airborne Division's 3rd Brigade landed in the A
//   Shau valley on 10 May 1969; the 3rd Battalion, 187th Infantry found the North Vietnamese 29th
//   Regiment dug in on Dong Ap Bia, Hill 937, a mountain on the valley's west side a mile or two
//   from the border with Laos; it attacked up the hill again and again over ten days, joined by
//   the 1st Battalion, 506th Infantry from the south, the 2nd Battalion, 501st, and the ARVN 2nd
//   Battalion, 3rd Regiment, until the summit was taken on 20 May; the American press called it
//   "Hamburger Hill";
// - Ap Bia, A Luoi, Ta Bat and the valley placed after the accounts and approximate; the rivers,
//   the valley road and the mountains drawn by hand. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  apbia: [16.215, 107.140], h900: [16.208, 107.152], aluoi: [16.218, 107.225], tabat: [16.170, 107.268], lz: [16.232, 107.178],
  south: [16.172, 107.190], east: [16.215, 107.250], laos: [16.230, 107.090], northwest: [16.295, 107.130],
  north: [16.305, 107.170], southeast: [16.125, 107.315],
};
const RIVERS = {
  asap: [[16.305, 107.160], [16.265, 107.180], [16.225, 107.205], [16.190, 107.240], [16.150, 107.280], [16.125, 107.310]],
};
const STREAMS = [[[16.222, 107.140], [16.205, 107.170], [16.198, 107.200], [16.205, 107.212]], [[16.250, 107.140], [16.240, 107.175], [16.235, 107.190]]];
const CLEARINGS = [[P.aluoi, 1.0], [[16.250, 107.200], 1.2], [[16.190, 107.245], 1.0], [P.tabat, 0.9], [[16.150, 107.285], 0.8]];
const HILLS = [[P.h900, 0.7], [[16.180, 107.160], 1.2], [[16.260, 107.150], 1.2]];
const MOUNTAINS = [[P.apbia, 1.0], [[16.280, 107.110], 2.2], [[16.150, 107.120], 2.4], [[16.200, 107.100], 1.6], [[16.270, 107.270], 2.4], [[16.200, 107.300], 2.2], [[16.140, 107.220], 1.6]];
const ROADS = [["north", [16.265, 107.188], "aluoi", [16.190, 107.248], "tabat", "southeast"]];
const NAMES = {
  apbia: "Dong Ap Bia (Hill 937)", h900: "Hill 900", aluoi: "A Luoi", tabat: "Ta Bat", lz: "3/187's landing zone",
};
const notes = {
  apbia: "The 29th Regiment held it in bunkers from 10 to 20 May 1969; 'Hamburger Hill' (approximate)",
  aluoi: "An old airstrip on the valley floor (approximate)",
  lz: "Where the 3rd Battalion, 187th Infantry landed on 10 May 1969 (approximate)",
};
const map = buildCampaign({
  id: "hamburger-1969", script: "make_hamburger.mjs", title: "The A Shau valley, May 1969",
  name: "Hamburger Hill, 1969 (the A Shau valley)",
  start_date: "1969-05-10", calendar: "gregorian", latitude: 16, climate: "annamite", climate_shift: 0, base: "F",
  bounds: [107.080, 16.310, 107.320, 16.120], midLat: 16.21, hexKm: 0.5,
  header: [
    "Ap Bia, A Luoi, Ta Bat and the valley are placed after the accounts and approximate; the A Sap",
    "and its streams, the valley road and the mountains are drawn by hand. Mountains under thick",
    "jungle on both sides, the valley floor between them open elephant grass, the border with Laos",
    "a mile or two west of Ap Bia.",
    "",
    "What happened, briefly: on 10 May 1969 the 101st Airborne Division's 3rd Brigade landed in the",
    "A Shau. The 3rd Battalion, 187th Infantry found the North Vietnamese 29th Regiment on Dong Ap",
    "Bia and attacked it eleven times in ten days, through rain and shellfire; the 1st Battalion,",
    "506th Infantry came up from the south, and with the 2nd Battalion, 501st and an ARVN battalion",
    "they took the summit on 20 May. The hill was given up soon after. Numbers below are round",
    "figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: [], streams: STREAMS, bridges: [], fords: [],
  farms: [], clearings: CLEARINGS, woods: [], hills: HILLS, mountains: MOUNTAINS, roads: ROADS,
  towns: [], villages: [],
  kinds: { apbia: "objective", lz: "camp" },
  forces: [
    { name: "3rd Battalion, 187th Infantry", type: "foot", side: "United States and ARVN", men: 450, tools: true, at: "lz" },
    { name: "1st Battalion, 506th Infantry", type: "foot", side: "United States and ARVN", men: 450, tools: true, at: "south" },
    { name: "2nd Battalion, 501st Infantry", type: "foot", side: "United States and ARVN", men: 450, tools: true, at: "aluoi" },
    { name: "ARVN 2nd Battalion, 3rd Regiment", type: "foot", side: "United States and ARVN", men: 400, tools: true, at: "east" },
    { name: "North Vietnamese 29th Regiment", type: "foot", side: "North Vietnamese", men: 1200, tools: true, at: "apbia" },
    { name: "North Vietnamese reserves in Laos", type: "foot", side: "North Vietnamese", men: 1500, tools: true, at: "laos" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
