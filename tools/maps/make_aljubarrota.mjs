// Builds data/maps/aljubarrota-1385.yaml: the Aljubarrota campaign of August 1385, on the travel
// map at 1 km a hex, from Leiria and Ourém to Porto de Mós and Alcobaça. Run from this folder
// after editing: npm ci && node make_aljubarrota.mjs
//
// Sources, all plain fact, and the drawing is ours (project doc "aljubarrota-research", after
// Monteiro, Aljubarrota Revisitada, 2001):
// - towns and villages are placed at their modern sites (facts); the Castilians' halt at Jardoeira,
//   the Portuguese first position and Chão da Feira are only approximate (no coordinates found);
// - the rivers, the hills of the Serras de Aire e Candeeiros, the pine woods and the roads are
//   drawn by hand through those places, after the modern ones, and are approximate. The monastery
//   of Batalha was vowed for the victory and begun in 1386, so it is not on the map.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  leiria: [39.7475, -8.8078], portomos: [39.6017, -8.8175], aljubarrota: [39.566, -8.930], alcobaca: [39.5483, -8.9798],
  ourem: [39.642, -8.590], calvaria: [39.6400, -8.8669], saojorge: [39.6396, -8.8452],
  firstpos: [39.657, -8.840], jardoeira: [39.675, -8.828], chaodafeira: [39.630, -8.856],
  castilians: [39.726, -8.818], portuguese: [39.605, -8.815],   // where the armies stand on the 13th (not places)
};

// ---------- rivers (crossed where a road bridges them) and brooks ----------
const RIVERS = {
  lis: [[39.690, -8.765], [39.715, -8.790], [39.744, -8.803], [39.765, -8.840], [39.790, -8.880]],
  lena: [[39.612, -8.818], [39.640, -8.825], [39.665, -8.822], [39.700, -8.810], [39.738, -8.804]],
  alcoa: [[39.590, -8.905], [39.565, -8.950], [39.550, -8.977], [39.555, -8.990]],
};
const STREAMS = [
  [[39.615, -8.885], [39.632, -8.868], [39.648, -8.848], [39.660, -8.828]],   // the ribeira da Calvaria
  [[39.625, -8.860], [39.640, -8.856]],                                     // Vale de Madeiros, west of the field
  [[39.628, -8.832], [39.642, -8.836]],                                     // Vale da Mata, east of it (which side is our reading)
];
const BRIDGES = [];
const FORDS = [];

// ---------- hills (the karst serras), woods ----------
const HILLS = [
  [[39.570, -8.860], 4], [[39.540, -8.880], 4], [[39.580, -8.800], 4],     // the Serra dos Candeeiros, south of Porto de Mós
  [[39.590, -8.720], 6], [[39.620, -8.680], 5], [[39.555, -8.660], 6],     // the Serra de Aire, towards Ourém
  [[39.645, -8.590], 1.2],                                                  // Ourém's castle hill
];
const WOODS = [[[39.770, -8.960], 4], [[39.735, -8.930], 3], [[39.700, -8.700], 3], [[39.560, -8.760], 3]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["leiria", [39.715, -8.812], "jardoeira", "firstpos", "saojorge", "chaodafeira", [39.600, -8.890], "aljubarrota", "alcobaca"],   // the Leiria-Alcobaça-Lisbon road
  ["jardoeira", [39.660, -8.860], "calvaria", "chaodafeira"],                // the Castilians' way round by Calvaria
  ["portomos", [39.620, -8.832], "saojorge"], ["leiria", [39.690, -8.830], [39.640, -8.822], "portomos"],
  ["portomos", [39.620, -8.720], [39.640, -8.640], "ourem"], ["leiria", [39.700, -8.700], "ourem"],
  ["portomos", [39.570, -8.880], "aljubarrota"],
];

const TOWNS = ["leiria", "alcobaca", "ourem", "portomos"];
const VILLAGES = ["aljubarrota", "calvaria"];

const NAMES = { leiria: "Leiria", portomos: "Porto de Mós", aljubarrota: "Aljubarrota", alcobaca: "Alcobaça", ourem: "Ourém",
  calvaria: "Calvaria de Cima", saojorge: "São Jorge (the battlefield)", firstpos: "The first position (approximate)",
  jardoeira: "Jardoeira (approximate)", chaodafeira: "Chão da Feira (approximate)" };
const notes = {
  saojorge: "The plateau between two valleys where the Portuguese dug pits and ditches and fought on 14 August; the chapel of São Jorge (from 1393) and the ossuary stand there",
  firstpos: "Where the Portuguese first drew up on the morning of the 14th, facing Leiria (about 2 km north of the field)",
  jardoeira: "Where the head of the Castilian column came up about noon, saw the Portuguese across the road and turned west",
  chaodafeira: "The open ground south of the field where the Castilians halted after going round by Calvaria",
  leiria: "The Castilian base on 12-14 August, with their carts and some 8,000 head of seized cattle",
  portomos: "The Portuguese camped here on 12-13 August; men of the abbot of Alcobaça joined them",
  alcobaca: "The Cistercian monastery whose abbot sent men to the Portuguese; the army went there on 17 August",
  ourem: "Taken for the Master of Avis in 1384; the Portuguese marched through on 11 August",
  aljubarrota: "The village the battle is named for, 11 km from the field",
};

const map = buildCampaign({
  id: "aljubarrota-1385", script: "make_aljubarrota.mjs", title: "The Aljubarrota campaign, August 1385, from Leiria to Alcobaça",
  name: "Aljubarrota, 1385 (Leiria to Alcobaça)", period: "Hundred Years' War",
  start_date: "1385-08-13", calendar: "julian", latitude: 40, climate: "atlantic_iberia", climate_shift: -0.5,
  bounds: [-8.99, 39.79, -8.55, 39.53], midLat: 39.66, hexKm: 1,
  header: [
    "Towns and villages are at their modern places; Jardoeira, the first position and Chão da Feira",
    "are only approximate; the rivers, hills, woods and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly: in July 1385 Juan I of Castile invaded Portugal to take its crown for",
    "his wife Beatriz, with French lances and the Portuguese who held for her, and came down by",
    "Coimbra to Leiria. João of Avis, made king by the Cortes that April, and his Constable Nuno",
    "Álvares Pereira gathered at Tomar and came by Ourém to Porto de Mós to bar the road to Lisbon.",
    "On 14 August they drew up across the road on the plateau of São Jorge; the Castilians went round",
    "them to the west, and the Portuguese turned about to face south between two valleys and dug",
    "pits and ditches. Near sunset the Castilians attacked and were broken in under an hour; Juan",
    "fled through the night to Santarém. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: [], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { saojorge: "objective", portomos: "camp", leiria: "camp" },
  depots: { portomos: ["Portugal"], alcobaca: ["Portugal"], ourem: ["Portugal"], leiria: ["Castile"] },   // where each side resupplies (project doc "aljubarrota-research")
  forces: [
    { name: "Portuguese vanguard and wings (Nuno Álvares)", type: "foot", side: "Portugal", men: 3800, tools: true, at: "portuguese" },
    { name: "Portuguese rearguard (João I)", type: "foot", side: "Portugal", men: 2500, tools: true, at: "portomos" },
    { name: "English and Gascons", type: "foot", side: "Portugal", men: 700, tools: true, at: "portomos" },
    { name: "Portuguese baggage", type: "wagons", side: "Portugal", men: 600, tools: false, at: "portomos" },
    { name: "Castilian vanguard (French lances and Portuguese loyalists)", type: "mounted", side: "Castile", men: 3200, tools: false, at: "castilians" },
    { name: "Juan I's main battle and wings", type: "mounted", side: "Castile", men: 5000, tools: false, at: "leiria" },
    { name: "Castilian crossbowmen and foot", type: "foot", side: "Castile", men: 10000, tools: true, at: "leiria" },
    { name: "Castilian baggage (700 carts)", type: "wagons", side: "Castile", men: 2000, tools: false, at: "leiria" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
