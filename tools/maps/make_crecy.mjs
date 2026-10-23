// Builds data/maps/crecy-1346.yaml: the last days of the Crécy campaign, 24-26 August 1346, on the
// travel map at 1 km a hex, from the Somme at Blanchetaque and Abbeville to the Forest of Crécy, Crécy
// and the Authie. Run from this folder after editing: npm ci && node make_crecy.mjs
//
// Sources, all plain fact, and the drawing is ours (project doc "crecy-research"): the towns and
// villages at their modern town halls (the French government's geo.api.gouv.fr), Wadicourt, the
// windmill, the Croix de Bohême, Valloires and the ford only approximate; the coast, the Somme
// estuary (in 1346 a tidal marsh up to Abbeville), the Maye, the Authie, the Forest of Crécy (at its
// modern extent: its limits in 1346 are not known) and the roads are drawn by hand through those
// places and are approximate (no road map of 1346 was found). The coast is drawn ("coast: drawn"):
// the Natural Earth line is too coarse for the bay at this scale.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  crecy: [50.2526, 1.8828], wadicourt: [50.270, 1.905], field: [50.260, 1.902], estrees: [50.2541, 1.9286],
  fontaine: [50.2378, 1.9296], croix: [50.248, 1.905], domvast: [50.1994, 1.9221], canchy: [50.1866, 1.8761],
  forestlabbaye: [50.2042, 1.8224], labroye: [50.2787, 1.9905], noyellesch: [50.2060, 1.9809], striquier: [50.1314, 1.9497],
  abbeville: [50.1058, 1.8341], portlegrand: [50.1520, 1.7474], saigneville: [50.1360, 1.7127], blanchetaque: [50.145, 1.728],
  noyelles: [50.1837, 1.7091], crotoy: [50.2148, 1.6260], stvalery: [50.1885, 1.6298], rue: [50.2726, 1.6675],
  acheux: [50.0650, 1.6764], dompierre: [50.3033, 1.9180], argoules: [50.3410, 1.8364], valloires: [50.351, 1.818],
  pontremy: [50.0549, 1.9035], livingston: [50.210, 1.890],
  amiens_road: [50.050, 1.990],   // where the French foot and the late levies come up from Amiens and the south (not a place)
};

// ---------- rivers (the Somme crossed only at Abbeville, Pont-Remy and the ford), the Maye, the sea ----------
const RIVERS = {
  somme: [[50.052, 1.960], "pontremy", [50.075, 1.870], "abbeville", [50.118, 1.808], [50.133, 1.775], [50.143, 1.748],
    "blanchetaque", [50.160, 1.708], [50.176, 1.680], [50.190, 1.660]],
  authie: [[50.262, 2.030], "labroye", [50.295, 1.950], "dompierre", [50.325, 1.870], "argoules", [50.355, 1.790], [50.362, 1.720]],
};
const WATER = [   // the sea and the Bay of the Somme (the shore of 1346 is not known; this is the modern bay, a little wider)
  [[50.370, 1.540], [50.370, 1.570], [50.300, 1.568], [50.250, 1.575], [50.236, 1.585], [50.226, 1.610], [50.221, 1.632],
    [50.206, 1.658], [50.196, 1.684], [50.183, 1.694], [50.176, 1.676], [50.183, 1.652], [50.191, 1.636], [50.201, 1.602],
    [50.207, 1.572], [50.200, 1.540]],
];
const STREAMS = [[[50.262, 1.975], [50.255, 1.930], "crecy", [50.250, 1.840], [50.245, 1.780], [50.238, 1.720], [50.228, 1.660]]];   // the Maye: small, wet, crossed anywhere
const BRIDGES = ["pontremy"], FORDS = ["blanchetaque"];

// ---------- marsh, woods, hills (centre, radius km) ----------
const MARSH = [
  [[50.168, 1.700], 1.8], [[50.150, 1.735], 1.4], [[50.135, 1.768], 1.2], [[50.120, 1.800], 1],   // the tidal estuary below Abbeville
  [[50.245, 1.660], 2.2], [[50.280, 1.620], 2.5], [[50.330, 1.640], 2.5],                       // the Marquenterre, the Maye and the Authie's bas-champs
  [[50.243, 1.800], 1],                                                                       // the wet north fringe of the forest
];
const WOODS = [[[50.228, 1.825], 4], [[50.212, 1.852], 2.8], [[50.222, 1.768], 2.5], [[50.343, 1.805], 1.5], [[50.180, 1.960], 1.5]];
const HILLS = [[[50.262, 1.900], 0.8], [[50.250, 1.940], 1.2]];                               // the ridge by the windmill; the Estrées plateau

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["abbeville", "canchy", "crecy", "wadicourt", "labroye"],                                  // Abbeville to Hesdin by Crécy
  ["abbeville", "striquier", "noyellesch", "fontaine", "estrees", "wadicourt"],               // the French way round by Saint-Riquier (Gumm), on the Roman road
  ["abbeville", [50.150, 1.880], "domvast", "fontaine"], ["domvast", "canchy"],
  ["abbeville", [50.130, 1.800], "portlegrand", "noyelles", "rue", [50.362, 1.700]],          // the coast road towards Montreuil
  ["noyelles", "crotoy"], ["noyelles", [50.192, 1.770], "forestlabbaye", "canchy"],
  ["rue", [50.262, 1.760], "crecy"],
  ["acheux", "saigneville", "blanchetaque"], ["saigneville", "stvalery"], ["saigneville", [50.110, 1.770], "abbeville"],
  ["abbeville", "pontremy"], ["pontremy", "amiens_road"], ["striquier", "amiens_road"],
  ["wadicourt", "dompierre", "argoules", "valloires"],
];

const TOWNS = ["abbeville", "rue", "crotoy", "stvalery", "striquier", "crecy"];
const VILLAGES = ["wadicourt", "estrees", "fontaine", "domvast", "canchy", "forestlabbaye", "labroye", "noyellesch", "portlegrand",
  "saigneville", "noyelles", "acheux", "dompierre", "argoules"];

const NAMES = { crecy: "Crécy", wadicourt: "Wadicourt (approximate)", field: "The Vallée des Clercs (the battlefield)",
  estrees: "Estrées-lès-Crécy", fontaine: "Fontaine-sur-Maye", croix: "Croix de Bohême (approximate)", domvast: "Domvast",
  canchy: "Canchy", forestlabbaye: "Forest-l'Abbaye", labroye: "Labroye (La Broye castle)", noyellesch: "Noyelles-en-Chaussée",
  striquier: "Saint-Riquier", abbeville: "Abbeville", portlegrand: "Port-le-Grand", saigneville: "Saigneville",
  blanchetaque: "Blanchetaque ford (approximate)", noyelles: "Noyelles-sur-Mer", crotoy: "Le Crotoy", stvalery: "Saint-Valery-sur-Somme",
  rue: "Rue", acheux: "Acheux-en-Vimeu", dompierre: "Dompierre-sur-Authie", argoules: "Argoules", valloires: "Valloires abbey (approximate)",
  pontremy: "Pont-Remy bridge", livingston: "Livingston's site (approximate)" };
const notes = {
  field: "The traditional field (Cassini, 1757): the English on the slope between Crécy and Wadicourt above the Vallée des Clercs, its east side a steep bank 2-6 m high; the battle of 26 August",
  blanchetaque: "The tidal ford, passable a few hours twice a day; forced on the morning of 24 August against Godemar du Fay. Where it ran moved from year to year",
  saigneville: "The south end of the ford; the English waited here for the tide on the morning of 24 August",
  portlegrand: "The north bank of the ford, where Godemar du Fay drew up 500 men-at-arms and 3,000 foot",
  abbeville: "Philip VI's base from 23 August, with the bridge over the Somme; he left it early on the 26th",
  noyelles: "Sacked by Despenser on 24 August; Edward lodged here with Catherine d'Artois",
  crotoy: "Burned on the evening of 24 August; where the fleet was to have met the army",
  rue: "Plundered and burned by the English",
  labroye: "Philip reached its castle after dark on the 26th ('this is the fortune of France') and rode on at midnight for Amiens",
  croix: "Where, by tradition, the blind King John of Bohemia fell",
  valloires: "Where the French princes were buried on 28-29 August",
  livingston: "Where Michael Livingston (2015) would put the battle instead: unconfirmed",
  acheux: "The English camp on the night of 23-24 August",
  crecy: "On the Maye; the English right rested on it. The forest begins about 2 km south-west",
  striquier: "An abbey town on the French road north (Gumm)",
};

const map = buildCampaign({
  id: "crecy-1346", script: "make_crecy.mjs", title: "The Crécy campaign, 24-26 August 1346, from the Somme to Crécy",
  period: "Hundred Years' War", name: "Crécy, 1346 (the Somme to Crécy)",
  start_date: "1346-08-24", calendar: "julian", latitude: 50, climate: "maritime", climate_shift: -0.5,
  bounds: [1.55, 50.37, 2.03, 50.045], midLat: 50.2, hexKm: 1, coast: "drawn",
  header: [
    "Towns and villages are at their modern town halls; Wadicourt, the windmill, the Croix de Bohême,",
    "Valloires and the ford are only approximate; the coast, the estuary, the rivers, the forest and the",
    "roads are drawn by hand and approximate (no road map of 1346 was found, and the bay has silted).",
    "",
    "What happened, briefly (dates Julian): Edward III landed in Normandy on 12 July, sacked Caen and",
    "marched up the Seine and north to the Somme, whose bridges Philip VI held. On 23 August he camped",
    "at Acheux; shortly after midnight he marched for the tidal ford of Blanchetaque, and when the tide",
    "fell, about eight in the morning of the 24th, forced it against Godemar du Fay. Philip came up from",
    "Abbeville too late, faced the ford and went back to the bridge. The English sacked Noyelles and Le",
    "Crotoy, went round the Forest of Crécy on the 25th and drew up on the slope above the Vallée des",
    "Clercs, where Philip attacked them on the evening of the 26th. Numbers below are round figures for",
    "play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["somme"], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  water: WATER, marsh: MARSH, woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { field: "objective", noyelles: "camp", abbeville: "camp" },
  depots: { noyelles: ["England"], abbeville: ["France"] },   // where each side resupplies: Noyelles sacked, Abbeville Philip's base (our reading)
  forces: [
    { name: "Edward III's army", type: "foot", side: "England", men: 11000, tools: true, at: "saigneville" },
    { name: "English horse (hobelars and mounted archers)", type: "mounted", side: "England", men: 3000, tools: false, at: "saigneville" },
    { name: "English carts", type: "wagons", side: "England", men: 500, tools: true, at: "acheux" },
    { name: "Godemar du Fay at the ford", type: "foot", side: "France", men: 3500, tools: false, at: "portlegrand" },
    { name: "Philip VI's men-at-arms", type: "mounted", side: "France", men: 12000, tools: false, at: "abbeville" },
    { name: "The Genoese crossbowmen (Doria and Grimaldi)", type: "foot", side: "France", men: 6000, tools: true, at: "abbeville" },
    { name: "French foot and the levies", type: "foot", side: "France", men: 7000, tools: true, at: "amiens_road" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
