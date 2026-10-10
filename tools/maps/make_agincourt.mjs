// Builds data/maps/agincourt-1415.yaml: the Agincourt campaign of 1415 on the travel map, at
// 5 km a hex, from Harfleur and the Seine to Calais. Run from this folder after editing:
//   npm ci && node make_agincourt.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the coastline is Natural Earth's 1:50m land (public domain, via the world-atlas package);
// - towns, fords and bridges are placed at their modern coordinates (facts);
// - rivers, woods and roads are drawn by hand through those places, after the line of the
//   modern rivers and the chroniclers' accounts of the march, in our own words. They are
//   approximate: a 5 km hex shows a river or a wood, not its banks.
// The coast and the Somme estuary have moved since 1415 (the bay has silted, Harfleur's
// harbour has gone); at this scale that changes little.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  harfleur: [49.507, 0.198], montivilliers: [49.546, 0.188], fecamp: [49.757, 0.374],
  stvaleryc: [49.870, 0.710], dieppe: [49.925, 1.078], arques: [49.880, 1.130], eu: [50.047, 1.418], treport: [50.060, 1.373],
  stvalery: [50.183, 1.633], crotoy: [50.217, 1.617], blanchetaque: [50.120, 1.750], abbeville: [50.105, 1.833],
  pontremy: [50.053, 1.910], hangest: [49.980, 2.063], picquigny: [49.944, 2.143], amiens: [49.894, 2.302], boves: [49.846, 2.389],
  corbie: [49.909, 2.509], bray: [49.940, 2.718], peronne: [49.932, 2.932], athies: [49.854, 2.980], bethencourt: [49.790, 2.960],
  voyennes: [49.774, 3.020], nesle: [49.758, 2.913], ham: [49.747, 3.073], albert: [50.002, 2.652], forceville: [50.064, 2.557],
  doullens: [50.157, 2.340], frevent: [50.276, 2.290], stpol: [50.381, 2.334], blangy: [50.420, 2.170], azincourt: [50.463, 2.129],
  hesdin: [50.373, 2.038], montreuil: [50.464, 1.764], etaples: [50.513, 1.640], boulogne: [50.726, 1.614], guines: [50.869, 1.870],
  calais: [50.951, 1.858], ardres: [50.854, 1.978], fruges: [50.515, 2.133], rouen: [49.443, 1.099], caudebec: [49.526, 0.725],
  tancarville: [49.472, 0.465], aumale: [49.770, 1.753], neufchatel: [49.733, 1.440], gravelines: [50.986, 2.128],
  kent: [51.06, 0.95], stomer: [50.750, 2.252], arras: [50.291, 2.777], bapaume: [50.103, 2.849], lucheux: [50.197, 2.413],
};

// ---------- rivers (impassable but at a bridge, a ford or a town) ----------
const RIVERS = {
  seine: ["tancarville", "caudebec", [49.48, 0.88], "rouen", [49.36, 1.15]],
  somme: [[50.215, 1.590], "stvalery", "blanchetaque", "abbeville", "pontremy", "hangest", "picquigny", "amiens", [49.90, 2.42],
          "corbie", "bray", [49.94, 2.83], "peronne", [49.88, 2.95], "athies", "bethencourt", "voyennes", "ham", [49.80, 3.24], [49.85, 3.29], [49.90, 3.40]],
  bresle: ["treport", "eu", [49.92, 1.60], "aumale"],
  bethune: ["dieppe", "arques", "neufchatel"],
  authie: [[50.370, 1.590], [50.30, 1.85], [50.23, 2.10], "doullens", [50.12, 2.52]],
  canche: ["etaples", "montreuil", "hesdin", "frevent", [50.33, 2.45]],
  ternoise: ["hesdin", "blangy", "stpol"],
};
// Where a river can be crossed: towns on it, and these bridges and fords.
const BRIDGES = ["pontremy", "picquigny", "bray"], FORDS = ["blanchetaque", "bethencourt", "voyennes"];

// ---------- woods (centre, radius km) and marsh ----------
const WOODS = [[[49.96, 1.52], 9], [[50.25, 1.88], 7], [[50.35, 2.07], 5], [[49.85, 1.22], 5], [[50.20, 2.44], 4],
               [[50.70, 1.72], 5], [[50.83, 1.94], 4], [[49.62, 0.55], 4], [[50.47, 2.14], 2.5]];
const MARSH = [[[50.20, 1.62], 4], [[50.06, 1.32], 0], [[49.80, 2.96], 3], [[49.92, 2.86], 3], [[50.98, 2.02], 5]];
const HILLS = [[[50.42, 1.95], 5], [[50.62, 1.80], 6]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["harfleur", "montivilliers", "fecamp", "stvaleryc", "dieppe"],
  ["harfleur", "caudebec", "rouen"],
  ["dieppe", "arques", "eu", "abbeville"],
  ["rouen", "neufchatel", "aumale", "abbeville"],
  ["abbeville", "pontremy", "picquigny", "amiens", "corbie", "bray", "peronne", "ham"],
  ["amiens", "boves"], ["peronne", "athies", "nesle"], ["peronne", "bapaume", "arras"],
  ["amiens", "doullens", "frevent", "stpol"], ["albert", "forceville", "doullens"], ["peronne", "albert"],
  ["abbeville", "montreuil", "boulogne", "calais"], ["frevent", "blangy", "azincourt", "fruges", "stomer"],
  ["hesdin", "blangy"], ["hesdin", "montreuil"], ["fruges", "guines", "calais"], ["stomer", "ardres", "calais"],
  ["calais", "gravelines"],
];

const TOWNS = ["harfleur", "fecamp", "dieppe", "eu", "stvalery", "abbeville", "amiens", "corbie", "peronne", "nesle", "ham",
  "doullens", "stpol", "hesdin", "montreuil", "boulogne", "calais", "rouen", "arras", "stomer", "albert", "gravelines"];
const VILLAGES = ["montivilliers", "stvaleryc", "arques", "treport", "crotoy", "hangest", "boves", "athies", "forceville", "frevent",
  "blangy", "azincourt", "etaples", "guines", "ardres", "fruges", "caudebec", "neufchatel", "aumale", "bapaume", "lucheux", "tancarville"];

const NAMES = { harfleur: "Harfleur", montivilliers: "Montivilliers", fecamp: "Fécamp", stvaleryc: "Saint-Valery-en-Caux",
  dieppe: "Dieppe", arques: "Arques", eu: "Eu", treport: "Le Tréport", stvalery: "Saint-Valery-sur-Somme", crotoy: "Le Crotoy",
  blanchetaque: "Blanchetaque ford", abbeville: "Abbeville", pontremy: "Pont-Remy bridge", hangest: "Hangest", picquigny: "Picquigny bridge",
  amiens: "Amiens", boves: "Boves", corbie: "Corbie", bray: "Bray bridge", peronne: "Péronne", athies: "Athies", bethencourt: "Béthencourt ford",
  voyennes: "Voyennes ford", nesle: "Nesle", ham: "Ham", albert: "Albert", forceville: "Forceville", doullens: "Doullens", frevent: "Frévent",
  stpol: "Saint-Pol", blangy: "Blangy", azincourt: "Azincourt", hesdin: "Hesdin", montreuil: "Montreuil", etaples: "Étaples",
  boulogne: "Boulogne", guines: "Guînes", calais: "Calais", ardres: "Ardres", fruges: "Fruges", rouen: "Rouen", caudebec: "Caudebec",
  tancarville: "Tancarville", aumale: "Aumale", neufchatel: "Neufchâtel", gravelines: "Gravelines", stomer: "Saint-Omer", arras: "Arras",
  bapaume: "Bapaume", lucheux: "Lucheux", kent: "England (Kent)" };
const notes = { harfleur: "The English landed nearby in mid-August and took the town on 22 September, after a five-week siege", calais: "English since 1347: the army's goal",
  blanchetaque: "Edward III's crossing in 1346; held against the English on 13 October 1415", azincourt: "The battle, 25 October",
  bethencourt: "Crossed on 19 October", voyennes: "Crossed on 19 October", rouen: "Where the French main army mustered; the King and the Dauphin stayed here",
  kent: "Across the Channel: off the march, shown for the coast" };

const map = buildCampaign({
  id: "agincourt-1415", script: "make_agincourt.mjs", title: "The Agincourt campaign of 1415, from Harfleur to Calais",
  name: "Agincourt campaign, 1415 (Harfleur to Calais)",
  start_date: "1415-10-08", calendar: "julian", latitude: 50, climate: "maritime", climate_shift: -0.5,
  bounds: [-0.05, 51.1, 3.3, 49.35], midLat: 50.2, hexKm: 5,
  header: [
    "The coastline is Natural Earth's (public domain); towns, fords and bridges are at their modern",
    "places; rivers, woods and roads are drawn by hand through them and are approximate.",
    "",
    "What happened, briefly (dates Julian, as the chroniclers kept them): Henry V landed by the",
    "Seine mouth in mid-August and took Harfleur on 22 September, after a siege in which dysentery",
    "killed or sent home thousands. He left on 8 October to march to Calais, on the coast road by",
    "Fécamp, Arques and Eu. On 13 October he found the Blanchetaque ford held, and turned up the",
    "Somme looking for a crossing while the French vanguard shadowed him on the far bank: by Pont-Remy,",
    "Hangest and Boves, past Amiens, until he crossed at Béthencourt and Voyennes on 19 October.",
    "Meanwhile the French main army, mustered at Rouen, marched north-east and joined the",
    "vanguard around Péronne; the King and the Dauphin stayed behind at Rouen. Henry marched",
    "north by Athies, Albert and Forceville, crossed the Ternoise at Blangy on 24 October, and",
    "found the combined French army across his road at Azincourt, where they fought on the",
    "25th. Numbers on both sides are disputed; those below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["somme", "seine"], bridges: BRIDGES, fords: FORDS,
  woods: WOODS, marsh: MARSH, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { harfleur: "camp", calais: "objective" },
  forces: [
    { name: "Henry V's army", type: "mounted", side: "England", men: 8500, tools: true, at: "harfleur" },
    { name: "English baggage", type: "wagons", side: "England", men: 300, tools: true, at: "montivilliers" },
    { name: "French vanguard (Boucicaut, d'Albret)", type: "mounted", side: "France", men: 6000, tools: false, at: "abbeville" },
    { name: "French main army (from Rouen)", type: "foot", side: "France", men: 15000, tools: true, at: "rouen" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
