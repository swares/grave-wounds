// Builds data/maps/jacobsford-1179.yaml: the siege of Jacob's Ford, August 1179, on the travel map
// at 1 km a hex, from Tiberias and the Sea of Galilee to Banias, the Hula and the Golan edge. Run
// from this folder after editing: npm ci && node make_jacobsford.mjs
//
// Sources, all plain fact, and the drawing is ours (project doc "jacobsford-research", after
// Barber 1998, Raphael 2023 and Ellenblum et al. 1998): the castle by its excavated site (33.0047 N,
// 35.6269 E, 200 m north of the ford: drawn a hex west of the ford so the two stay apart), the
// towns and castles at their modern sites (Tell al-Qadi and Quneitra only approximate); the
// Jordan, the Hula lake and marsh, the Sea of Galilee, the hills of Galilee and the Golan, and
// the roads are drawn by hand after the modern ones and are approximate. The Mamluk bridge north
// of the ford, Nimrod's castle and Capernaum's village are later or abandoned, and are left off.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  castle: [33.0047, 35.6180], ford: [33.0030, 35.6290], tiberias: [32.7944, 35.5333], safed: [32.9658, 35.4983],
  capernaum: [32.8811, 35.5750], banias: [33.2486, 35.6944], telqadi: [33.249, 35.652], hunin: [33.2189, 35.5453],
  quneitra: [33.117, 35.817],
  saladin: [33.020, 35.660], baldwin: [32.800, 35.540],   // where the armies stand on the 25th (not places)
};

// ---------- the Jordan (crossed only at the ford; drawn from where its headwaters meet, so the
// way round the head of the Hula by Tell al-Qadi stays open), lakes the land data counts as land ----------
const RIVERS = {
  jordan: [[33.190, 35.636], [33.150, 35.620], [33.105, 35.610], [33.055, 35.616], [33.030, 35.625],
    [33.012, 35.629], [32.990, 35.630], [32.960, 35.632], [32.930, 35.626], [32.900, 35.612], [32.885, 35.600]],
};
const WATER = [
  [[32.887, 35.585], [32.870, 35.640], [32.820, 35.655], [32.770, 35.645], [32.770, 35.530], [32.810, 35.528], [32.850, 35.535], [32.875, 35.560]],   // the Sea of Galilee
  [[33.106, 35.596], [33.100, 35.626], [33.076, 35.633], [33.056, 35.616], [33.062, 35.592], [33.086, 35.585]],                                      // Lake Hula
];
const FORDS = ["ford"];

// ---------- marsh, hills, woods (centre, radius km) ----------
const MARSH = [[[33.125, 35.605], 3.5], [[33.160, 35.615], 3], [[33.200, 35.630], 2]];          // the Hula swamps
const HILLS = [
  [[32.960, 35.500], 5], [[32.930, 35.555], 4], [[33.150, 35.545], 5], [[33.220, 35.540], 3],    // Upper Galilee, Safed and the Korazim plateau; the Naftali ridge
  [[33.000, 35.700], 5], [[32.900, 35.700], 5], [[33.080, 35.720], 5], [[33.150, 35.780], 6], [[32.980, 35.800], 6],   // the Golan escarpment and plateau
  [[33.250, 35.780], 4],                                                                       // towards Hermon
];
const MOUNTAINS = [[[32.990, 35.470], 3]];                                                     // Mount Meron's flank
const WOODS = [[[33.200, 35.700], 3], [[33.050, 35.770], 3]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  [[32.930, 35.470], "safed", [32.990, 35.580], "castle", "ford", [33.040, 35.700], "quneitra", [33.150, 35.850]],   // Acre to Damascus by the ford
  ["tiberias", [32.850, 35.540], "capernaum", [32.950, 35.605], "castle"],
  ["banias", "telqadi", [33.150, 35.575], [33.060, 35.580], "castle"], ["banias", "hunin"], ["banias", [33.200, 35.760], [33.150, 35.840]],
  ["tiberias", [32.900, 35.500], "safed"],
];

const TOWNS = ["tiberias", "safed", "banias"];
const VILLAGES = [];

const NAMES = { castle: "Chastellet (the castle at Jacob's Ford)", ford: "Jacob's Ford", tiberias: "Tiberias", safed: "Safed",
  capernaum: "Capernaum (ruins)", banias: "Banias", telqadi: "Tell al-Qadi (approximate)", hunin: "Hunin (Chastel Neuf)",
  quneitra: "Quneitra (approximate)" };
const notes = {
  castle: "The Templar castle begun in October 1178 on a low tell by the ford: walls 4 m thick and about 10 m high, unfinished; stormed on 30 August",
  ford: "The only crossing of the Jordan between the Hula swamps and the gorge to the south, on the road from Acre to Damascus",
  tiberias: "Where Baldwin IV gathered the relief, slowly; 25 km from the castle",
  safed: "A Templar castle since 1168; Saladin's men cut timber for their palisades in its country",
  banias: "Ayyubid since 1164: Saladin's base for his raids across the Hula",
  hunin: "Rebuilt in 1178 by Humphrey of Toron, who died here of his wounds in April 1179",
  quneitra: "On the Golan, on the way to Damascus, a day's ride from the ford (whether there was a stage here in 1179 is not known)",
  telqadi: "Part of the screen Saladin set across the Hula in 1179",
};

const map = buildCampaign({
  id: "jacobsford-1179", script: "make_jacobsford.mjs", title: "The siege of Jacob's Ford, August 1179, from Tiberias to Banias",
  name: "Jacob's Ford, 1179 (Tiberias to Banias)",
  start_date: "1179-08-25", calendar: "julian", latitude: 33, climate: "jordan_valley", climate_shift: 0,
  bounds: [35.47, 33.27, 35.86, 32.77], midLat: 33.02, hexKm: 1, coast: "drawn",
  header: [
    "The castle stands 200 m north of the ford, drawn a hex west of it at this scale; the towns and",
    "castles are at their modern places, Tell al-Qadi and Quneitra only approximate; the Jordan, the",
    "lakes, the Hula marsh, the hills and the roads are drawn by hand and approximate. The Jordan can",
    "be crossed only at the ford.",
    "",
    "What happened, briefly: in the autumn of 1178 Baldwin IV and the Templars began a great castle at",
    "Jacob's Ford, a day's ride from Damascus, against Saladin's protests and his offer of 100,000",
    "dinars to pull it down. In 1179 Saladin's forces beat the Franks near Banias and at Marj Ayyun.",
    "On Saturday 25 August he came to the ford with his army, took the outer works that evening, set",
    "up mangonels and mined the north-east corner; the first mine's fire failed, the second brought",
    "the wall down at dawn on Thursday 30 August, and the castle was stormed. Baldwin, gathering an",
    "army at Tiberias, came too late. Saladin razed the castle, and a plague from the heat and the dead",
    "killed ten of his emirs. Numbers below are round figures for play; no source gives Saladin's.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["jordan"], streams: [], bridges: [], fords: FORDS,
  water: WATER, marsh: MARSH, woods: WOODS, hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { castle: "objective", tiberias: "camp", banias: "camp" },
  depots: { tiberias: ["Kingdom of Jerusalem"], safed: ["Kingdom of Jerusalem"], banias: ["Ayyubids"] },   // where each side resupplies (project doc "jacobsford-research")
  forces: [
    { name: "The Templar garrison", type: "foot", side: "Kingdom of Jerusalem", men: 1100, tools: true, at: "castle" },
    { name: "Baldwin IV's relief (gathering)", type: "foot", side: "Kingdom of Jerusalem", men: 4000, tools: true, at: "baldwin" },
    { name: "The king's knights", type: "mounted", side: "Kingdom of Jerusalem", men: 600, tools: false, at: "tiberias" },
    { name: "Saladin's horse (askari and mamluks)", type: "mounted", side: "Ayyubids", men: 6000, tools: false, at: "saladin" },
    { name: "Saladin's foot, archers and sappers", type: "foot", side: "Ayyubids", men: 3000, tools: true, at: "saladin" },
    { name: "Farrukh-Shah's horse", type: "mounted", side: "Ayyubids", men: 1000, tools: false, at: "banias" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
