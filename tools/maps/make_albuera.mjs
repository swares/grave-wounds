// Builds data/maps/albuera-1811.yaml: the Albuera campaign of May 1811 on the travel map, at 1 km
// a hex, from Badajoz and Elvas to Santa Marta and Fuente del Maestre. Run from this folder after
// editing: npm ci && node make_albuera.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - towns and villages are placed at their modern coordinates (facts); a few force starts
//   (the siege lines, Blake's march) are only approximate;
// - rivers, brooks, woods and roads are drawn by hand through those places, after the line of
//   the modern rivers and roads, with the course of the campaign told in our own words. They
//   are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  badajoz: [38.879, -6.970], siege: [38.860, -6.950], elvas: [38.881, -7.163], olivenza: [38.686, -7.101],
  valverde: [38.674, -6.983], albuera: [38.716, -6.822], almendral: [38.611, -6.818], nogales: [38.583, -6.738],
  talavera: [38.880, -6.770], lobon: [38.851, -6.623], solana: [38.722, -6.538], santamarta: [38.513, -6.623],
  villalba: [38.611, -6.511], almendralejo: [38.683, -6.407], fuente: [38.528, -6.448], torre: [38.611, -6.795],
};

// ---------- rivers (impassable but at a bridge, a ford or a town) and brooks ----------
const RIVERS = {
  guadiana: [[38.870, -6.300], [38.860, -6.520], "lobon", [38.875, -6.700], "talavera", [38.880, -6.880], "badajoz", [38.840, -7.040],
             [38.790, -7.100], [38.740, -7.170], [38.700, -7.230]],
};
const STREAMS = [
  ["nogales", [38.650, -6.780], "albuera", [38.790, -6.860], [38.870, -6.900]],      // the Albuera, from the Nogales brook to the Guadiana
  [[38.600, -6.700], [38.680, -6.790], "albuera"],                                  // the Chicapierna
];
const FORDS = ["talavera"];

// ---------- woods (olive groves and holm-oak), hills (centre, radius km) ----------
const WOODS = [[[38.700, -6.760], 2.5], [[38.640, -6.700], 3], [[38.560, -6.560], 3], [[38.760, -7.000], 2.5], [[38.620, -6.900], 2.5]];
const HILLS = [[[38.560, -6.900], 4], [[38.520, -6.740], 3]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["badajoz", "siege", "albuera", "torre", "santamarta", "fuente"],           // the Seville road
  ["badajoz", "elvas"], ["badajoz", "talavera", "lobon", [38.870, -6.380]],    // to Mérida
  ["olivenza", "valverde", "albuera"], ["albuera", "almendral", "nogales", "santamarta"], ["albuera", "solana", "almendralejo"],
  ["santamarta", "villalba", "almendralejo"], ["badajoz", "olivenza"],
];

const TOWNS = ["badajoz", "elvas", "olivenza", "almendralejo"];
const VILLAGES = ["valverde", "albuera", "almendral", "nogales", "lobon", "solana", "santamarta", "villalba", "fuente", "torre"];

const NAMES = { badajoz: "Badajoz", siege: "Siege lines", elvas: "Elvas", olivenza: "Olivenza", valverde: "Valverde de Leganés",
  albuera: "La Albuera", almendral: "Almendral", nogales: "Nogales", talavera: "Talavera la Real ford", lobon: "Lobón",
  solana: "Solana de los Barros", santamarta: "Santa Marta", villalba: "Villalba de los Barros", almendralejo: "Almendralejo",
  fuente: "Fuente del Maestre", torre: "Torre de Miguel Sesmero" };
const notes = {
  badajoz: "Held by a French garrison and besieged by Beresford in May 1811: the prize",
  siege: "Beresford's siege works; the siege was raised on 13 to 15 May as Soult came on",
  elvas: "The Portuguese fortress across the border: the allies' base",
  albuera: "Where Beresford and Blake joined and stood on 16 May; the battle, south of the village",
  santamarta: "The allied cavalry fell back from here before Soult's advance",
  almendral: "Blake's Spanish army came up by this road, joining late on 15 May (approximate)",
  fuente: "Soult's army on the road from Seville",
};

const map = buildCampaign({
  id: "albuera-1811", script: "make_albuera.mjs", title: "The Albuera campaign of May 1811, from Badajoz to Santa Marta",
  name: "Albuera campaign, 1811 (Badajoz to Santa Marta)",
  start_date: "1811-05-13", calendar: "gregorian", latitude: 39, climate: "mediterranean", climate_shift: -1,
  bounds: [-7.20, 38.95, -6.38, 38.48], midLat: 38.72, hexKm: 1,
  header: [
    "Towns and villages are at their modern places; the siege lines and Blake's start are only",
    "approximate; rivers, brooks, woods and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly (dates Gregorian): in spring 1811 Marshal Beresford's British and",
    "Portuguese besieged French-held Badajoz. Marshal Soult marched up from Seville to relieve it.",
    "Beresford raised the siege and joined General Blake's Spanish army at La Albuera, across",
    "the road from the south. On 16 May Soult made a show against the village while his main",
    "force marched round through the olive woods onto the heights south of the allied line. The",
    "Spanish there held; a British brigade that came up beside them was ridden down by Polish",
    "lancers in a hailstorm; the British line that followed stood and traded volleys at close",
    "range until both sides were shot to pieces, and a late counter-attack drove the French off.",
    "Both armies lost about a third of their men engaged. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["guadiana"], streams: STREAMS, fords: FORDS,
  woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { siege: "camp", badajoz: "objective" },
  forces: [
    { name: "Beresford's British", type: "foot", side: "Allies", men: 10000, tools: true, at: "siege" },
    { name: "Beresford's Portuguese", type: "foot", side: "Allies", men: 10000, tools: true, at: "siege" },
    { name: "Allied cavalry", type: "mounted", side: "Allies", men: 3000, tools: false, at: "santamarta" },
    { name: "Blake's Spanish army", type: "foot", side: "Allies", men: 14000, tools: true, at: "almendral" },
    { name: "Soult's army", type: "foot", side: "France", men: 19000, tools: true, at: "fuente" },
    { name: "French cavalry (Latour-Maubourg)", type: "mounted", side: "France", men: 4000, tools: false, at: "fuente" },
    { name: "Badajoz garrison", type: "foot", side: "France", men: 3000, tools: true, at: "badajoz" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
