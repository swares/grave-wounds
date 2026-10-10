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
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { feature } from "topojson-client";
import { geoContains } from "d3-geo";

const here = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(here, "../..");
const HEX_KM = 5, ROW_KM = HEX_KM * Math.sqrt(3) / 2;
const LON0 = -0.05, LAT0 = 51.1, LON1 = 3.3, LAT1 = 49.35;     // west, north, east, south
const KX = 111.32 * Math.cos(50.2 * Math.PI / 180), KY = 111.2;  // km a degree at the map's middle
const COLS = Math.ceil((LON1 - LON0) * KX / HEX_KM) + 1, ROWS = Math.ceil((LAT0 - LAT1) * KY / ROW_KM) + 1;

const xy = ([lat, lon]) => [(lon - LON0) * KX, (LAT0 - lat) * KY];
const centre = (c, r) => [c * HEX_KM + (r & 1) * HEX_KM / 2, r * ROW_KM];
const toLatLon = ([x, y]) => [LAT0 - y / KY, LON0 + x / KX];
function hexAt(p){                                // the hex whose centre is nearest a point (km)
  const [x, y] = p, r0 = Math.round(y / ROW_KM);
  let best = null, bd = Infinity;
  for (let r = r0 - 1; r <= r0 + 1; r++){
    const c0 = Math.round((x - (r & 1) * HEX_KM / 2) / HEX_KM);
    for (let c = c0 - 1; c <= c0 + 1; c++){
      const [cx, cy] = centre(c, r), dd = (cx - x) ** 2 + (cy - y) ** 2;
      if (dd < bd){ bd = dd; best = [c, r] }
    }
  }
  return best;
}
const on = ([c, r]) => c >= 0 && c < COLS && r >= 0 && r < ROWS;

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

const TOWNS = new Set(["harfleur", "fecamp", "dieppe", "eu", "stvalery", "abbeville", "amiens", "corbie", "peronne", "nesle", "ham",
  "doullens", "stpol", "hesdin", "montreuil", "boulogne", "calais", "rouen", "arras", "stomer", "albert", "gravelines"]);
const VILLAGES = new Set(["montivilliers", "stvaleryc", "arques", "treport", "crotoy", "hangest", "boves", "athies", "forceville", "frevent",
  "blangy", "azincourt", "etaples", "guines", "ardres", "fruges", "caudebec", "neufchatel", "aumale", "bapaume", "lucheux", "tancarville"]);

// ---------- painting ----------
const land = (() => { const t = JSON.parse(fs.readFileSync(path.join(here, "node_modules/world-atlas/land-50m.json"), "utf8")); return feature(t, t.objects.land) })();
const grid = Array.from({ length: ROWS }, (_, r) => Array.from({ length: COLS }, (_, c) => {
  const [lat, lon] = toLatLon(centre(c, r));
  return geoContains(land, [lon, lat]) ? "f" : "w";
}));
const pt = p => (typeof p === "string" ? P[p] : p);
const set = (h, k, onLandOnly = true) => { if (on(h) && (!onLandOnly || grid[h[1]][h[0]] !== "w")) grid[h[1]][h[0]] = k };
function line(points, k, step = 0.4){             // every hex a polyline runs through
  const out = [];
  for (let i = 0; i + 1 < points.length; i++){
    const a = xy(pt(points[i])), b = xy(pt(points[i + 1])), n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / step));
    for (let j = 0; j <= n; j++) out.push(hexAt([a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n]));
  }
  for (const h of out) set(h, k);
  return out;
}
function blob([c, rad], k){                       // every land hex within rad km of a point (and the one at it)
  const p = xy(c);
  for (let r = 0; r < ROWS; r++) for (let q = 0; q < COLS; q++){
    const [x, y] = centre(q, r);
    if (Math.hypot(x - p[0], y - p[1]) <= rad && grid[r][q] !== "w") grid[r][q] = k;
  }
  set(hexAt(p), k);
}
WOODS.forEach(w => blob(w, "F"));
MARSH.forEach(w => blob(w, "m"));
HILLS.forEach(w => blob(w, "h"));
const roadHexes = ROADS.flatMap(rd => line(rd, "="));
for (const [name, rv] of Object.entries(RIVERS)){
  const hexes = line(rv, "~");
  // Where a road crosses a lesser river, a bridge; the Somme and the Seine only at the crossings named
  if (name === "somme" || name === "seine") continue;
  const onRiver = new Set(hexes.map(h => h.join(",")));
  for (const h of roadHexes) if (onRiver.has(h.join(","))) set(h, "b");
}
for (const b of BRIDGES) set(hexAt(xy(P[b])), "b");
for (const f of FORDS) set(hexAt(xy(P[f])), "d");
// A place whose hex came out as sea (the coast is coarse at this scale) moves to the nearest land hex.
function placeHex(k){
  const h = hexAt(xy(P[k]));
  if (!on(h) || grid[h[1]][h[0]] !== "w") return h;
  const p = xy(P[k]);
  let best = h, bd = Infinity;
  for (let r = h[1] - 2; r <= h[1] + 2; r++) for (let c = h[0] - 2; c <= h[0] + 2; c++){
    if (!on([c, r]) || grid[r][c] === "w") continue;
    const [x, y] = centre(c, r), dd = (x - p[0]) ** 2 + (y - p[1]) ** 2;
    if (dd < bd){ bd = dd; best = [c, r] }
  }
  return best;
}
const rivered = h => on(h) && grid[h[1]][h[0]] === "~";
for (const v of VILLAGES) if (!rivered(placeHex(v))) set(placeHex(v), "v");   // a village on a river is not a crossing
for (const t of TOWNS) set(placeHex(t), "T");

// ---------- the file ----------
const hx = placeHex;
const NAMES = { harfleur: "Harfleur", montivilliers: "Montivilliers", fecamp: "Fécamp", stvaleryc: "Saint-Valery-en-Caux",
  dieppe: "Dieppe", arques: "Arques", eu: "Eu", treport: "Le Tréport", stvalery: "Saint-Valery-sur-Somme", crotoy: "Le Crotoy",
  blanchetaque: "Blanchetaque ford", abbeville: "Abbeville", pontremy: "Pont-Remy bridge", hangest: "Hangest", picquigny: "Picquigny bridge",
  amiens: "Amiens", boves: "Boves", corbie: "Corbie", bray: "Bray bridge", peronne: "Péronne", athies: "Athies", bethencourt: "Béthencourt ford",
  voyennes: "Voyennes ford", nesle: "Nesle", ham: "Ham", albert: "Albert", forceville: "Forceville", doullens: "Doullens", frevent: "Frévent",
  stpol: "Saint-Pol", blangy: "Blangy", azincourt: "Azincourt", hesdin: "Hesdin", montreuil: "Montreuil", etaples: "Étaples",
  boulogne: "Boulogne", guines: "Guînes", calais: "Calais", ardres: "Ardres", fruges: "Fruges", rouen: "Rouen", caudebec: "Caudebec",
  tancarville: "Tancarville", aumale: "Aumale", neufchatel: "Neufchâtel", gravelines: "Gravelines", stomer: "Saint-Omer", arras: "Arras",
  bapaume: "Bapaume", lucheux: "Lucheux", kent: "England (Kent)" };
const SPECIAL = { harfleur: "camp", calais: "objective" };
function kindOf(k){
  if (SPECIAL[k]) return SPECIAL[k];
  if (TOWNS.has(k)) return "town";
  return VILLAGES.has(k) ? "village" : "landmark";
}
const notes = { harfleur: "The English landed nearby in mid-August and took the town on 22 September, after a five-week siege", calais: "English since 1347: the army's goal",
  blanchetaque: "Edward III's crossing in 1346; held against the English on 13 October 1415", azincourt: "The battle, 25 October",
  bethencourt: "Crossed on 19 October", voyennes: "Crossed on 19 October", rouen: "Where the French main army mustered; the King and the Dauphin stayed here",
  kent: "Across the Channel: off the march, shown for the coast" };
const yq = s => JSON.stringify(s);
const noteOf = k => (notes[k] ? ", note: " + yq(notes[k]) : "");
const places = Object.keys(NAMES).filter(k => on(hx(k))).map(k =>
  `  - {name: ${yq(NAMES[k])}, kind: ${kindOf(k)}, hex: [${hx(k).join(", ")}]${noteOf(k)}}`);
const out = `# The Agincourt campaign of 1415, from Harfleur to Calais, at ${HEX_KM} km a hex (about ${Math.round(COLS * HEX_KM)} by ${Math.round(ROWS * ROW_KM)} km).
# Generated by tools/maps/make_agincourt.mjs: edit that file and re-run it rather than this one.
# The coastline is Natural Earth's (public domain); towns, fords and bridges are at their modern
# places; rivers, woods and roads are drawn by hand through them and are approximate.
#
# What happened, briefly (dates Julian, as the chroniclers kept them): Henry V landed by the
# Seine mouth in mid-August and took Harfleur on 22 September, after a siege in which dysentery
# killed or sent home thousands. He left on 8 October to march to Calais, on the coast road by
# Fécamp, Arques and Eu. On 13 October he found the Blanchetaque ford held, and turned up the
# Somme looking for a crossing while the French vanguard shadowed him on the far bank: by Pont-Remy,
# Hangest and Boves, past Amiens, until he crossed at Béthencourt and Voyennes on 19 October.
# Meanwhile the French main army, mustered at Rouen, marched north-east and joined the
# vanguard around Péronne; the King and the Dauphin stayed behind at Rouen. Henry marched
# north by Athies, Albert and Forceville, crossed the Ternoise at Blangy on 24 October, and
# found the combined French army across his road at Azincourt, where they fought on the
# 25th. Numbers on both sides are disputed; those below are round figures for play.
id: agincourt-1415
name: "Agincourt campaign, 1415 (Harfleur to Calais)"
hex_km: ${HEX_KM}
start_date: "1415-10-08"
calendar: julian
latitude: 50
climate: maritime
climate_shift: -0.5
terrain: |
${grid.map(row => "    " + row.join("")).join("\n")}
places:
${places.join("\n")}
forces:
  - {name: "Henry V's army", type: mounted, side: "England", men: 8500, tools: true, hex: [${hx("harfleur").join(", ")}]}
  - {name: "English baggage", type: wagons, side: "England", men: 300, tools: true, hex: [${hx("montivilliers").join(", ")}]}
  - {name: "French vanguard (Boucicaut, d'Albret)", type: mounted, side: "France", men: 6000, tools: false, hex: [${hx("abbeville").join(", ")}]}
  - {name: "French main army (from Rouen)", type: foot, side: "France", men: 15000, tools: true, hex: [${hx("rouen").join(", ")}]}
`;
fs.writeFileSync(path.join(root, "data/maps/agincourt-1415.yaml"), out);
console.log(`${COLS} x ${ROWS} hexes`);
console.log(grid.map(r => r.join("")).join("\n"));
