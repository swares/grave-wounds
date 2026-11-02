// Builds data/maps/ciudad-rodrigo-1812.yaml: Wellington's siege of Ciudad Rodrigo, 8 to 19 January 1812, on the
// travel map at 1 km a hex, from the allied quarters west of the Águeda to Salamanca. Run from this folder after
// editing: node make_ciudad_rodrigo.mjs
//
// Sources (project doc "siege-phase-research"; historyofwar, Siege of Ciudad Rodrigo; Wikipedia, Siege of
// Ciudad Rodrigo (1812)): the siege began on 8 January, when the Light Division stormed the Renaud redoubt
// on the Greater Teson that night; the first parallel was opened on the 9th, four divisions (the 1st, 3rd,
// 4th and Light) taking the trenches in turn for 24 hours each; the convent of Santa Cruz was stormed on the
// 13th; Barrié's sortie on the 14th was beaten off, the batteries opened that afternoon, and San Francisco
// was taken that night; by the end of the 18th the guns had made two breaches, and the town was stormed at
// 7 pm on the 19th and sacked that night. The garrison: about 2,000 under Barrié, from Dorsenne's Army of the
// North, with "food and ammunition ... not in short supply" (historyofwar). The besiegers: 26,000 (Wikipedia),
// of an army of up to 40,000. Marmont and Dorsenne heard of the siege at Valladolid on the 14th and meant to
// gather 32,000 at Salamanca by the 26th, thinking the town would hold three weeks; Marmont was a day's march
// from Salamanca when he heard on the 21st that it had fallen.
// The fortress (Sieges, docs/travel.md): broken by the guns, 11 days of siege work to a practicable breach
// (8 to 18 January: sourced), so the siege corps, working from the first day, has it practicable after the
// night of the 18th and the storm on the 19th, as in 1812. The rotation of the four divisions is left out:
// they are one siege corps in the lines. 2,000 workers and 90 days' stores are ours. Marmont's army is not on
// the map (the GM may bring it on); the Salamanca garrison, the split of the allied army beyond the 26,000
// besiegers and where the rest stood are ours.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  rodrigo: [40.600, -6.533], siege: [40.609, -6.533], bridge: [40.588, -6.560], gallegos: [40.633, -6.700], espeja: [40.565, -6.712],
  guinaldo: [40.427, -6.680], bodon: [40.480, -6.600], caridad: [40.640, -6.625], santi: [40.710, -6.390],
  martin: [40.775, -6.290], fuente: [40.800, -6.250], aldehuela: [40.870, -6.070], calzada: [40.890, -5.920],
  tamames: [40.656, -6.110], salamanca: [40.965, -5.664], matilla: [40.830, -5.940], robleda: [40.410, -6.630],
};
const NAMES = { rodrigo: "Ciudad Rodrigo", siege: "Siege lines", gallegos: "Gallegos de Argañán", espeja: "Espeja",
  guinaldo: "Fuenteguinaldo", bodon: "El Bodón", caridad: "La Caridad ford", santi: "Sancti-Spíritus", martin: "Martín de Yeltes",
  fuente: "La Fuente de San Esteban", aldehuela: "Aldehuela de la Bóveda", calzada: "Calzada de Don Diego", tamames: "Tamames",
  salamanca: "Salamanca", matilla: "Matilla de los Caños", robleda: "Robleda" };
const notes = {
  rodrigo: "Held by Barrié's 2,000 of the Army of the North; besieged from 8 January 1812 and stormed on the night of the 19th",
  siege: "The siege lines on the Greater Teson, where the Light Division stormed the Renaud redoubt on the first night",
  gallegos: "West of the Águeda, toward Almeida, the allies' siege park (off the map): the allied depot here is ours",
  caridad: "A ford over the Águeda below the town (ours: the divisions crossed daily from their quarters)",
  salamanca: "Where Marmont meant to gather 32,000 by 26 January; he was a day's march off when he heard on the 21st that Ciudad Rodrigo had fallen",
};

// ---------- rivers, fords, hills, woods, roads ----------
const RIVERS = {
  agueda: [[40.400, -6.470], [40.500, -6.490], [40.570, -6.510], "rodrigo", [40.615, -6.580], "caridad", [40.700, -6.700], [40.800, -6.760], [41.000, -6.780]],
  tormes: [[40.800, -5.620], [40.900, -5.640], [40.958, -5.664], [40.990, -5.760], [41.000, -5.800]],
};
const FORDS = ["caridad"];
const STREAMS = [
  [[40.560, -6.350], "santi", [40.800, -6.330], [40.990, -6.420]],      // the Yeltes
  [[40.620, -6.100], [40.760, -6.140], [40.900, -6.250], [40.990, -6.300]],   // the Huebra
];
const HILLS = [[[40.470, -6.300], 8], [[40.450, -5.950], 6]];   // the foothills of the Sierra de Francia and the Sierra de Gata
const MOUNTAINS = [[[40.430, -6.150], 4]];                       // toward the Peña de Francia
const WOODS = [[[40.540, -6.640], 4], [[40.700, -6.050], 5], [[40.760, -6.500], 4]];   // the holm-oak dehesas, at their thickest
const ROADS = [
  ["rodrigo", "santi", "martin", "fuente", "aldehuela", "calzada", "salamanca"],   // the high road to Salamanca
  ["rodrigo", "bridge", "gallegos", [40.640, -6.780]],                           // over the bridge and west, toward Almeida
  ["bridge", "bodon", "guinaldo"], ["guinaldo", "robleda"], ["espeja", "guinaldo"], ["espeja", "caridad", "siege"],
  ["fuente", "tamames"], ["tamames", "matilla", "salamanca"],
];

const map = buildCampaign({
  id: "ciudad-rodrigo-1812", script: "make_ciudad_rodrigo.mjs", title: "The siege of Ciudad Rodrigo, January 1812, from the Águeda to Salamanca",
  name: "Ciudad Rodrigo, 1812 (the siege)",
  start_date: "1812-01-08", calendar: "gregorian", latitude: 41, climate: "continental", climate_shift: 5,   // the Salamanca plain: milder winters than central Europe's (ours)
  bounds: [-6.78, 41.00, -5.62, 40.40], midLat: 40.70, hexKm: 1,
  header: [
    "Towns and villages are at their modern places; the siege lines are only approximate; rivers, brooks, woods,",
    "hills and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly (dates Gregorian): Wellington surprised Ciudad Rodrigo in midwinter, before Marmont",
    "and Dorsenne could gather to relieve it. On 8 January the Light Division stormed the Renaud redoubt; four",
    "divisions took the trenches in turn, crossing the Águeda each day from their quarters; the batteries opened",
    "on the 14th, and by the 18th there were two breaches. On the night of the 19th the 3rd Division stormed the",
    "great breach and the Light Division the lesser (Craufurd and Mackinnon were killed), and the town was",
    "sacked that night. Marmont, gathering at Salamanca, heard on the 21st. Ciudad Rodrigo is a fortress here",
    "(docs/travel.md, Sieges). Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes,
  rivers: RIVERS, majorRivers: ["agueda", "tormes"], fords: FORDS, streams: STREAMS, hills: HILLS, mountains: MOUNTAINS, woods: WOODS, roads: ROADS,
  towns: ["rodrigo", "salamanca"],
  villages: ["gallegos", "espeja", "guinaldo", "bodon", "santi", "martin", "fuente", "aldehuela", "calzada", "tamames", "matilla", "robleda"],
  kinds: { siege: "camp", rodrigo: "objective", caridad: "landmark" },
  depots: { gallegos: ["Allies"], salamanca: ["France"] },   // where each side resupplies: ours
  fortresses: { rodrigo: { side: "France", breach_days: 11, workers: 2000, stores: 90 } },   // see the header
  forces: [
    { name: "The siege corps (1st, 3rd, 4th and Light Divisions, Pack's Portuguese)", type: "foot", side: "Allies", men: 26000, tools: true, at: "siege" },
    { name: "The rest of the allied foot", type: "foot", side: "Allies", men: 11000, tools: true, at: "guinaldo" },
    { name: "Allied cavalry", type: "mounted", side: "Allies", men: 3000, tools: false, at: "santi" },
    { name: "Ciudad Rodrigo garrison (Barrié)", type: "foot", side: "France", men: 2000, tools: true, at: "rodrigo" },
    { name: "Salamanca garrison", type: "foot", side: "France", men: 3000, tools: true, at: "salamanca" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
