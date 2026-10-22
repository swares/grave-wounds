// Builds data/maps/mons-1914.yaml: the battle of Mons, August 1914, on the travel map at 1 km a
// hex, from Condé to Binche and from Soignies to Maubeuge. Run from this folder after editing:
// npm ci && node make_mons.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - towns and villages are placed at their modern sites (facts); the canal bridges are only
//   approximate;
// - the Mons-Condé canal, the Canal du Centre, the Haine, the Sambre, the woods, the slag-heap
//   hills of the Borinage and the roads are drawn by hand through those places, after the line
//   of the modern canals, rivers and roads. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  mons: [50.454, 3.952], nimy: [50.474, 3.955], obourg: [50.466, 4.010], jemappes: [50.449, 3.888], ghislain: [50.448, 3.818],
  conde: [50.452, 3.588], binche: [50.411, 4.165], maubeuge: [50.278, 3.973], frameries: [50.408, 3.897], soignies: [50.578, 4.070],
  casteau: [50.513, 4.008], bavay: [50.298, 3.794], ghlin: [50.488, 3.906], baudour: [50.484, 3.835], havre: [50.468, 4.054],
  symphorien: [50.437, 4.004], thulin: [50.425, 3.737], boussu: [50.433, 3.795], harmignies: [50.405, 4.016], quievrain: [50.405, 3.684],
  nimybridge: [50.468, 3.958], obourgbridge: [50.464, 4.012], jemappesbridge: [50.455, 3.885], ghislainbridge: [50.454, 3.818],
  mariette: [50.458, 3.760], pommeroeul: [50.459, 3.708],
  north3: [50.560, 3.800], north4: [50.600, 3.640], northcav: [50.585, 3.590],   // where the German corps come in (not places)
};

// ---------- the canals (crossed only at their bridges), rivers and brooks ----------
const RIVERS = {
  canal: ["conde", [50.457, 3.650], "pommeroeul", "mariette", "ghislainbridge", [50.455, 3.850], "jemappesbridge", [50.462, 3.920],
          [50.470, 3.940], "nimybridge", [50.470, 3.985], "obourgbridge", [50.467, 4.035], [50.465, 4.090], [50.470, 4.150], [50.478, 4.250]],
  sambre: [[50.230, 3.880], [50.262, 3.930], "maubeuge", [50.300, 4.050], [50.330, 4.150], [50.360, 4.250]],
};
const STREAMS = [
  [[50.440, 3.600], [50.442, 3.700], [50.444, 3.800], [50.446, 3.870], [50.452, 3.930], [50.445, 4.000], [50.440, 4.100]],   // the Haine, south of the canal
  [[50.540, 3.700], [50.500, 3.760], [50.470, 3.790]],                                                                       // a brook from the north
  [[50.330, 3.800], [50.360, 3.860], [50.400, 3.940]],                                                                       // a brook to the south
];
const BRIDGES = ["nimybridge", "obourgbridge", "jemappesbridge", "ghislainbridge", "mariette", "pommeroeul"];
const FORDS = [];

// ---------- woods (centre, radius km), the slag heaps and rises ----------
const WOODS = [[[50.500, 3.830], 2.6], [[50.395, 3.840], 2.8], [[50.490, 4.040], 1.8], [[50.540, 3.960], 2.0], [[50.330, 3.900], 2.2],
  [[50.350, 4.080], 2.0], [[50.560, 3.850], 2.2], [[50.270, 3.820], 2.4]];
const HILLS = [[[50.420, 3.860], 1.2], [[50.430, 3.930], 0.8], [[50.415, 3.800], 1.0], [[50.440, 3.975], 0.7], [[50.400, 4.000], 1.0]];

// ---------- roads and railways (through places, in order) ----------
const ROADS = [
  ["soignies", "casteau", "nimy", "mons", [50.380, 3.960], [50.330, 3.970], "maubeuge"],               // Brussels road, on to Maubeuge
  ["conde", "quievrain", "thulin", "boussu", "ghislain", "jemappes", "mons"],                         // the road west to Condé
  ["mons", "symphorien", [50.425, 4.080], "binche"],                                                   // the road east to Binche
  ["mons", "frameries", [50.350, 3.840], "bavay"],                                                     // the old road to Bavay
  ["mons", "ghlin", "baudour", [50.520, 3.760]], ["mons", "obourg", "havre"], ["casteau", "havre"],
  ["ghislain", "baudour"], ["bavay", "maubeuge"], ["harmignies", "symphorien"], ["harmignies", [50.350, 4.000], "maubeuge"],
];

const TOWNS = ["mons", "maubeuge"];
const VILLAGES = ["nimy", "obourg", "jemappes", "ghislain", "conde", "binche", "frameries", "soignies", "casteau", "bavay", "ghlin",
  "baudour", "havre", "symphorien", "thulin", "boussu", "harmignies", "quievrain"];

const NAMES = { mons: "Mons", nimy: "Nimy", obourg: "Obourg", jemappes: "Jemappes", ghislain: "Saint-Ghislain", conde: "Condé",
  binche: "Binche", maubeuge: "Maubeuge", frameries: "Frameries", soignies: "Soignies", casteau: "Casteau", bavay: "Bavay",
  ghlin: "Ghlin", baudour: "Baudour", havre: "Havré", symphorien: "Saint-Symphorien", thulin: "Thulin", boussu: "Boussu",
  harmignies: "Harmignies", quievrain: "Quiévrain", nimybridge: "Nimy bridges", obourgbridge: "Obourg bridge",
  jemappesbridge: "Jemappes bridge", ghislainbridge: "Saint-Ghislain bridge", mariette: "Mariette bridge", pommeroeul: "Pommerœul bridge" };
const notes = {
  nimybridge: "The road and railway bridges at the tip of the canal salient, held by the Royal Fusiliers on 23 August (approximate)",
  obourgbridge: "The Middlesex held the canal and the station here (approximate)",
  casteau: "Where British cavalry met German horsemen on 22 August, the BEF's first shots of the war",
  maubeuge: "The fortress the BEF marched up from",
  mons: "The BEF's line ran along the canal north of the town",
  symphorien: "The military cemetery here holds the first and last British soldiers killed in the war",
};

// The map's people speak Picard and French (data/languages.yaml); Binche, in the Centre, Walloon
// (our reading: the line between the two runs about La Louvière).
const map = buildCampaign({
  id: "mons-1914", script: "make_mons.mjs", title: "The battle of Mons, August 1914, from Condé to Binche",
  name: "Mons, 1914 (Condé to Binche)",
  start_date: "1914-08-22", calendar: "gregorian", latitude: 50, climate: "maritime", climate_shift: 1,
  bounds: [3.55, 50.62, 4.27, 50.24], midLat: 50.43, hexKm: 1,
  header: [
    "Towns and villages are at their modern places; the canal bridges are only approximate; the",
    "canals, rivers, woods, slag-heap hills and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly: the British Expeditionary Force, four infantry divisions and a",
    "cavalry division of regulars, marched up from Maubeuge to the Mons-Condé canal on 21 and 22",
    "August 1914, on the left of the French Fifth Army. The German First Army, marching south",
    "through Belgium, ran into it on 23 August. The Germans attacked across the open ground north",
    "of the canal, many of them in close order, and the British rifle fire, aimed and fast, cost",
    "them dearly; the British lost most heavily in the salient the canal makes at Nimy, where",
    "the Royal Fusiliers held the bridges. By the afternoon the Germans were across at Nimy and",
    "Obourg, and that night the BEF began its retreat. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["canal", "sambre"], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { mons: "objective", maubeuge: "camp" },
  depots: { maubeuge: ["British"] },   // where each side resupplies (project doc "depots-research")
  tongues: { binche: ["walloon", "french"] },   // the people's own tongues where they differ from the map's (project doc "tongues-research")
  forces: [
    { name: "3rd Division (Hamilton)", type: "foot", side: "British", men: 15000, tools: true, at: "mons" },
    { name: "5th Division (Fergusson)", type: "foot", side: "British", men: 15000, tools: true, at: "boussu" },
    { name: "I Corps (Haig)", type: "foot", side: "British", men: 30000, tools: true, at: "harmignies" },
    { name: "Cavalry Division (Allenby)", type: "mounted", side: "British", men: 9000, tools: false, at: "binche" },
    { name: "IX Corps (von Quast)", type: "foot", side: "Germans", men: 40000, tools: true, at: "soignies" },
    { name: "III Corps (von Lochow)", type: "foot", side: "Germans", men: 40000, tools: true, at: "north3" },
    { name: "IV Corps (Sixt von Armin)", type: "foot", side: "Germans", men: 40000, tools: true, at: "north4" },
    { name: "German cavalry (Marwitz)", type: "mounted", side: "Germans", men: 6000, tools: false, at: "northcav" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
