// Builds data/maps/sevastopol-1855.yaml: the siege of Sevastopol in its last days, September 1855,
// on the travel map at 1 km a hex, from Kamiesh Bay to the Chernaya and from the North Side to
// Balaklava. Run from this folder after editing: npm ci && node make_sevastopol.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the coast, the harbour and the South Bay are drawn by hand (the land data is too coarse for
//   the Chersonese peninsula at this scale), after the line of the modern shore;
// - the town, Balaklava, Kadikoi, the Malakhov, the Redan, Inkerman, the Traktir bridge and the
//   heights are placed at their modern sites (facts), the works and camps only approximately;
// - the Chernaya, the ridges, the scrub, the roads and the Balaklava railway (drawn as a road)
//   are drawn by hand through those places. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  sevastopol: [44.613, 33.522], karabelnaya: [44.611, 33.549], redan: [44.603, 33.541], malakhov: [44.6087, 33.5544],
  flagstaff: [44.600, 33.512], northside: [44.632, 33.548], inkerman: [44.612, 33.612],
  inkbridge: [44.6125, 33.603], homeridge: [44.594, 33.588], camp: [44.578, 33.556], kamiesh: [44.583, 33.408],
  frenchleft: [44.588, 33.500], frenchright: [44.590, 33.572], balaklava: [44.500, 33.600], kadikoi: [44.512, 33.592], col: [44.535, 33.585],
  causeway: [44.526, 33.640], traktir: [44.531, 33.672], fedyukhin: [44.545, 33.664], chorgun: [44.503, 33.712],
  mackenzie: [44.630, 33.660], sapun: [44.560, 33.600], chorgunford: [44.508, 33.700],
};

// ---------- the sea, the harbour (the Roadstead) and the South Bay, by hand ----------
const WATER = [
  [[44.700, 33.300], [44.700, 33.520], [44.665, 33.525], [44.645, 33.505], [44.627, 33.485], [44.618, 33.485],
   [44.614, 33.470], [44.606, 33.455], [44.596, 33.430], [44.585, 33.405], [44.578, 33.385], [44.585, 33.370],
   [44.560, 33.370], [44.530, 33.400], [44.505, 33.460], [44.495, 33.500], [44.493, 33.560], [44.497, 33.598],
   [44.490, 33.620], [44.484, 33.700], [44.470, 33.800], [44.400, 33.800], [44.400, 33.300]],
  [[44.627, 33.480], [44.626, 33.540], [44.623, 33.580], [44.620, 33.603], [44.615, 33.603], [44.614, 33.580],
   [44.616, 33.540], [44.617, 33.500], [44.617, 33.480]],
  [[44.616, 33.528], [44.616, 33.540], [44.598, 33.539], [44.598, 33.533]],      // the South Bay, between the town and the Karabelnaya
];

// ---------- the Chernaya (crossed at its bridges and the ford by Chorgun) ----------
const RIVERS = {
  chernaya: [[44.485, 33.770], [44.497, 33.735], "chorgun", "chorgunford", [44.518, 33.690], "traktir", [44.548, 33.652],
             [44.575, 33.636], [44.598, 33.622], "inkbridge", [44.617, 33.598]],
};
const BRIDGES = ["traktir", "inkbridge"];
const FORDS = ["chorgunford"];

// ---------- scrub and woods, ridges and heights (centre, radius km) ----------
const WOODS = [[[44.598, 33.600], 1.3], [[44.640, 33.690], 2.5], [[44.610, 33.660], 1.5], [[44.490, 33.660], 1.5]];
const HILLS = [[[44.560, 33.600], 1.2], [[44.548, 33.596], 1], [[44.575, 33.605], 1], [[44.545, 33.664], 1.2],
  [[44.526, 33.635], 1], [[44.630, 33.660], 1.5], [[44.594, 33.590], 0.8], [[44.6087, 33.5544], 0.4]];
const MOUNTAINS = [[[44.490, 33.630], 1.5], [[44.488, 33.700], 2]];

// ---------- roads, and the railway from Balaklava (through places, in order) ----------
const ROADS = [
  ["balaklava", "kadikoi", "col", [44.560, 33.572], "camp", [44.596, 33.548], "karabelnaya"],              // Balaklava road, and the railway beside it
  [[44.505, 33.770], [44.518, 33.700], "causeway", "col"],                                                    // the Woronzov road, along the Causeway Heights
  ["kadikoi", "traktir", [44.580, 33.665], "mackenzie"],                                                       // over the Traktir bridge to the Mackenzie heights
  ["camp", "homeridge", "inkbridge", "inkerman"],                                                              // the Inkerman road
  ["kamiesh", [44.588, 33.450], "frenchleft", "flagstaff", "sevastopol"],                                      // from the French base to the town
  ["northside", [44.638, 33.600], "mackenzie"],                                                                // the North Side's road out
  ["frenchleft", [44.580, 33.530], "camp"],
];

const TOWNS = ["sevastopol", "karabelnaya"];
const VILLAGES = ["balaklava", "kadikoi", "chorgun", "inkerman"];

const NAMES = { sevastopol: "Sevastopol", redan: "The Great Redan",
  malakhov: "The Malakhov", northside: "The North Side",
  inkerman: "Inkerman", homeridge: "Home Ridge", camp: "The British camp (Cathcart's Hill)",
  kamiesh: "Kamiesh", frenchleft: "The French left attack", balaklava: "Balaklava", kadikoi: "Kadikoi",
  col: "The Col", causeway: "The Causeway Heights", traktir: "Traktir bridge", fedyukhin: "The Fedyukhin heights",
  chorgun: "Chorgun", mackenzie: "The Mackenzie heights", sapun: "The Sapun ridge", chorgunford: "Ford by Chorgun" };
const notes = {
  redan: "The British stormed its salient on 8 September 1855 and were driven out after about an hour and a half (approximate)",
  malakhov: "Taken by the French at noon on 8 September 1855, from the Mamelon just south of it (theirs since June); the Russians gave up the south side that night",
  camp: "The British army's camps on the upland",
  kamiesh: "The French army's base and harbour",
  balaklava: "The British army's harbour and base",
  traktir: "Where the Russian field army's last attempt to relieve the town was beaten on 16 August 1855",
  homeridge: "The heart of the Battle of Inkerman, 5 November 1854 (approximate)",
  causeway: "The Battle of Balaklava, 25 October 1854, was fought across these heights and the valleys either side",
};

const map = buildCampaign({
  id: "sevastopol-1855", script: "make_sevastopol.mjs", title: "The siege of Sevastopol in September 1855, from Kamiesh Bay to the Chernaya",
  name: "Siege of Sevastopol, 1855 (Kamiesh to the Chernaya)",
  start_date: "1855-09-07", calendar: "gregorian", latitude: 45, climate: "crimea", climate_shift: -0.5,
  bounds: [33.385, 44.665, 33.765, 44.480], midLat: 44.57, hexKm: 1,
  header: [
    "The coast, the harbour and the South Bay are drawn by hand after the modern shore. The town, the",
    "harbour of Balaklava, the Malakhov, the Redan and the heights are at their modern places, the",
    "works and camps only approximately; the Chernaya, the scrub, the roads and the Balaklava",
    "railway (drawn as a road) are drawn by hand and approximate.",
    "",
    "What happened, briefly: the British, French and Turkish armies landed in the Crimea in",
    "September 1854, beat the Russians on the Alma and laid siege to Sevastopol from the south,",
    "supplied through Balaklava and Kamiesh. The Russians' attacks on the siege lines at Balaklava",
    "(October 1854) and Inkerman (November 1854) failed, and the armies wintered in the trenches.",
    "Through 1855 the trenches crept forward; the French took the Mamelon in June, and a joint",
    "assault on the Malakhov and the Redan on 18 June failed. The Russian field army's last",
    "attempt at relief was beaten on the Chernaya on 16 August. After a three-day bombardment,",
    "on 8 September the French stormed and held the Malakhov; the British got into the Redan's",
    "salient but were driven out. That night the Russians blew up their works and crossed to the",
    "North Side. Numbers below are round figures for play.",
  ],
  coast: "drawn", places: P, names: NAMES, notes, water: WATER, rivers: RIVERS, majorRivers: ["chernaya"], bridges: BRIDGES, fords: FORDS,
  base: ".", woods: WOODS, hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { redan: "objective", malakhov: "objective", camp: "camp", kamiesh: "camp", balaklava: "camp" },
  depots: { balaklava: ["Allies"], kamiesh: ["Allies"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "Light Division", type: "foot", side: "Allies", men: 3500, tools: true, at: "camp" },
    { name: "2nd Division", type: "foot", side: "Allies", men: 3500, tools: true, at: "camp" },
    { name: "Highland and 4th Divisions (reserve)", type: "foot", side: "Allies", men: 7000, tools: true, at: "camp" },
    { name: "British cavalry", type: "mounted", side: "Allies", men: 1500, tools: false, at: "kadikoi" },
    { name: "Bosquet's corps (French right attack)", type: "foot", side: "Allies", men: 25000, tools: true, at: "frenchright" },
    { name: "French 1st Corps (left attack)", type: "foot", side: "Allies", men: 15000, tools: true, at: "frenchleft" },
    { name: "French and Sardinians on the Chernaya", type: "foot", side: "Allies", men: 25000, tools: true, at: "fedyukhin" },
    { name: "Garrison of the Karabelnaya (Malakhov and Redan)", type: "foot", side: "Russia", men: 20000, tools: true, at: "malakhov" },
    { name: "Garrison of the town side", type: "foot", side: "Russia", men: 20000, tools: true, at: "sevastopol" },
    { name: "Reserve on the North Side", type: "foot", side: "Russia", men: 10000, tools: true, at: "northside" },
    { name: "Field army on the Mackenzie heights", type: "foot", side: "Russia", men: 30000, tools: true, at: "mackenzie" },
    { name: "Russian cavalry", type: "mounted", side: "Russia", men: 3000, tools: false, at: "mackenzie" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
