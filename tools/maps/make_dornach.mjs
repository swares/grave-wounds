// Builds data/maps/dornach-1499.yaml: the Dornach campaign of July 1499, on the travel map at 1 km
// a hex, from Basel to Liestal and from the Rhine to the Jura at Seewen. Run from this folder after
// editing: npm ci && node make_dornach.mjs
//
// Sources, all plain fact, and the drawing is ours (project doc "dornach-research"): the monuments'
// positions from the Swiss Army's inventory of war memorials (Solothurn, 2025); the other towns,
// villages and castles at their modern sites, several only approximate; the Rhine, the Birs, the
// Ergolz, the Gempen plateau and its wooded scarp, the Blauen, the Bruderholz and the roads are
// drawn by hand through those places, after the modern ones (no road map of 1499 was found), and
// are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  basel: [47.5566, 7.5929], reinach: [47.4935, 7.5911], arlesheim: [47.4940, 7.6198], dornach: [47.4786, 7.6167],
  dorneck: [47.4800, 7.6280], gempen: [47.4757, 7.6608], stollen: [47.487, 7.656], liestal: [47.4846, 7.7346],
  muttenz: [47.5229, 7.6452], munchenstein: [47.518, 7.618], aesch: [47.471, 7.596], pfeffingen: [47.459, 7.588],
  angenstein: [47.452, 7.604], grellingen: [47.442, 7.589], hochwald: [47.456, 7.642], seewen: [47.436, 7.659],
  buren: [47.446, 7.673], stjakob: [47.540, 7.617], augst: [47.537, 7.718], birseck: [47.488, 7.630],
  field: [47.486, 7.619],
  confederates: [47.500, 7.775],   // where Lucerne and Zug are coming from (not a place)
};

// ---------- rivers (crossed where a road bridges them) ----------
const RIVERS = {
  rhine: [[47.537, 7.785], [47.535, 7.718], [47.545, 7.660], [47.555, 7.615], [47.560, 7.592], [47.575, 7.585], [47.585, 7.580]],
  birs: [[47.400, 7.540], [47.425, 7.556], [47.442, 7.585], [47.452, 7.600], [47.470, 7.606], [47.487, 7.612], [47.505, 7.615],
    [47.518, 7.620], [47.540, 7.622], [47.553, 7.625]],
  ergolz: [[47.440, 7.785], [47.470, 7.750], [47.486, 7.737], [47.510, 7.730], [47.535, 7.720]],
};
const STREAMS = [];
const BRIDGES = [];
const FORDS = [];

// ---------- hills and woods (centre, radius km) ----------
const HILLS = [
  [[47.470, 7.675], 3.5], [[47.455, 7.700], 3],                            // the Gempen plateau (Dorneckberg)
  [[47.450, 7.530], 3],                                                     // the Blauen
  [[47.530, 7.585], 1.8],                                                   // the Bruderholz
  [[47.415, 7.640], 3.5], [[47.415, 7.720], 3],                             // the Jura towards Seewen and the Hauenstein
];
const WOODS = [[[47.484, 7.643], 1.6], [[47.470, 7.648], 1.5], [[47.455, 7.715], 2.5], [[47.425, 7.600], 2.5], [[47.545, 7.675], 1.8], [[47.445, 7.540], 2]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["basel", "stjakob", "muttenz", [47.505, 7.700], "liestal"],                // the road up the Rhine valley to Liestal and the Hauenstein
  ["basel", "stjakob", "munchenstein", [47.500, 7.613], "dornach", "aesch", "grellingen"],   // up the Birs
  ["arlesheim", [47.487, 7.614], "dornach"], ["arlesheim", "munchenstein"],
  ["basel", [47.525, 7.592], "reinach", "aesch", "pfeffingen"],               // over the Bruderholz
  ["dornach", [47.478, 7.640], "gempen", [47.480, 7.700], "liestal"],         // the road over the Gempen the Swiss kept off
  ["gempen", "hochwald", "seewen", "buren"], ["augst", [47.510, 7.735], "liestal"],
];

const TOWNS = ["basel", "liestal"];
const VILLAGES = ["reinach", "arlesheim", "dornach", "gempen", "muttenz", "munchenstein", "aesch", "grellingen", "hochwald", "seewen", "buren", "augst"];

const NAMES = { basel: "Basel", reinach: "Reinach", arlesheim: "Arlesheim", dornach: "Dornach", dorneck: "Dorneck castle",
  gempen: "Gempen", stollen: "Gempenstollen (approximate)", liestal: "Liestal", muttenz: "Muttenz", munchenstein: "Münchenstein",
  aesch: "Aesch", pfeffingen: "Pfeffingen castle (approximate)", angenstein: "Angenstein castle (approximate)",
  grellingen: "Grellingen", hochwald: "Hochwald", seewen: "Seewen", buren: "Büren", stjakob: "St. Jakob an der Birs",
  augst: "Augst", birseck: "Birseck castle (approximate)", field: "The fields below Dorneck (the battlefield)" };
const notes = {
  field: "The fields between Dornach and Arlesheim where the imperial army camped and was broken on 22 July",
  dorneck: "Solothurn's castle on its spur, held by some twenty men under Benedikt Hugi and besieged from 21 July",
  stollen: "Where the Bernese and Solothurners watched the imperial camp on the 22nd before coming down through the woods",
  liestal: "Where the Confederates gathered, and Hugi's messenger ran on the night of 21-22 July",
  reinach: "The Welsche Garde camped here, across the Birs from the main camp",
  basel: "Neutral in 1499: it forbade its people to take part, though men of the upper Basel country joined the Swiss",
  pfeffingen: "An imperial castle; the Swiss besieged it for a day on 25 July",
  stjakob: "Where the Swiss were destroyed by the Armagnacs in 1444",
  dornach: "Mostly burned in March; Fürstenberg and two other imperial lords lie in its church",
  arlesheim: "The imperial camp spread north from Dornach towards here",
};

const map = buildCampaign({
  id: "dornach-1499", script: "make_dornach.mjs", title: "The Dornach campaign, July 1499, from Basel to Liestal",
  name: "Dornach, 1499 (Basel to Liestal)",
  start_date: "1499-07-21", calendar: "julian", latitude: 47, climate: "continental", climate_shift: -0.5,
  bounds: [7.52, 47.58, 7.79, 47.40], midLat: 47.49, hexKm: 1,
  header: [
    "Towns and villages are at their modern places, the monuments by the Swiss Army's coordinates;",
    "the Gempenstollen and some castles are only approximate; the rivers, hills, woods and roads",
    "are drawn by hand and approximate (no road map of 1499 was found).",
    "",
    "What happened, briefly: in the Swabian War of 1499 Count Heinrich von Fürstenberg brought the",
    "imperial army of the west up the Birs from the Sundgau to take Solothurn's castle of Dorneck,",
    "the key to the road over the Hauenstein. On 21 July it camped below the castle at Dornach and",
    "Arlesheim, with the Welsche Garde across the river at Reinach. That night the castle's warden",
    "sent a messenger over the wall to the Confederates gathering at Liestal; they came over the",
    "Gempen through the woods, watched the camp from the heights, and on the afternoon of the 22nd",
    "fell on it. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["rhine"], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { field: "objective", liestal: "camp", arlesheim: "camp", dorneck: "camp" },
  depots: { liestal: ["Swiss Confederates"], dorneck: ["Swiss Confederates"], arlesheim: ["Swabian League and the Empire"] },   // where each side resupplies (project doc "dornach-research")
  forces: [
    { name: "Solothurn, Bern and Zürich (the vanguard)", type: "foot", side: "Swiss Confederates", men: 2000, tools: true, at: "gempen" },
    { name: "Bern's main banner (Rudolf von Erlach)", type: "foot", side: "Swiss Confederates", men: 3000, tools: true, at: "liestal" },
    { name: "Lucerne and Zug", type: "foot", side: "Swiss Confederates", men: 1000, tools: true, at: "confederates" },
    { name: "Dorneck garrison (Benedikt Hugi)", type: "foot", side: "Swiss Confederates", men: 20, tools: true, at: "dorneck" },
    { name: "Fürstenberg's Landsknechte and levies", type: "foot", side: "Swabian League and the Empire", men: 8000, tools: true, at: "arlesheim" },
    { name: "Geldern Landsknechte", type: "foot", side: "Swabian League and the Empire", men: 2000, tools: true, at: "dornach" },
    { name: "The Welsche Garde (Louis de Vaudrey)", type: "mounted", side: "Swabian League and the Empire", men: 1000, tools: false, at: "reinach" },
    { name: "Knights and lords", type: "mounted", side: "Swabian League and the Empire", men: 300, tools: false, at: "arlesheim" },
    { name: "Imperial guns and baggage", type: "wagons", side: "Swabian League and the Empire", men: 1000, tools: false, at: "field" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
