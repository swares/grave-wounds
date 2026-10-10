// Builds data/maps/towton-1461.yaml: the Towton campaign of March 1461 on the travel map, at
// 1 km a hex, from Pontefract and the Aire crossings to York. Run from this folder after
// editing: npm ci && node make_towton.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - towns, villages, bridges and fords are placed at their modern coordinates (facts);
// - rivers, brooks, woods and roads are drawn by hand through those places, after the line of
//   the modern rivers and the old road north (Ferrybridge, Sherburn, Towton, Tadcaster, York),
//   with the course of the campaign told in our own words. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  york: [53.959, -1.081], bishopthorpe: [53.921, -1.096], tadcaster: [53.884, -1.262], towton: [53.851, -1.268],
  saxton: [53.828, -1.284], lead: [53.836, -1.301], cockbeck: [53.846, -1.290], stutton: [53.873, -1.290],
  dintingdale: [53.815, -1.272], sherburn: [53.797, -1.250], fairburn: [53.744, -1.287], brotherton: [53.722, -1.274],
  ferrybridge: [53.711, -1.270], knottingley: [53.705, -1.248], pontefract: [53.691, -1.312], darrington: [53.675, -1.265],
  wentbridge: [53.650, -1.258], castleford: [53.725, -1.362], wakefield: [53.683, -1.499], leeds: [53.797, -1.548],
  garforth: [53.792, -1.389], aberford: [53.826, -1.344], barwick: [53.832, -1.395], bramham: [53.879, -1.355],
  bostonspa: [53.904, -1.345], wetherby: [53.928, -1.386], ulleskelf: [53.853, -1.215], cawood: [53.832, -1.130],
  selby: [53.784, -1.067], hambleton: [53.775, -1.170],
};

// ---------- rivers (impassable but at a bridge, a ford or a town) and brooks ----------
const RIVERS = {
  aire: [[53.795, -1.60], "leeds", [53.765, -1.47], [53.735, -1.40], "castleford", [53.722, -1.31], "ferrybridge",
         [53.712, -1.24], [53.710, -1.15], [53.700, -1.05], [53.690, -0.95]],
  calder: [[53.680, -1.60], "wakefield", [53.705, -1.42], "castleford"],
  wharfe: [[53.920, -1.60], [53.925, -1.45], "wetherby", "bostonspa", "tadcaster", "ulleskelf", [53.840, -1.16], "cawood"],
  ouse: [[53.995, -1.12], "york", "bishopthorpe", [53.880, -1.10], "cawood", [53.805, -1.08], "selby", [53.745, -1.03], [53.725, -0.95]],
};
const STREAMS = [["barwick", "aberford", [53.836, -1.322], "cockbeck", "stutton", [53.879, -1.284]]];   // Cock Beck, into the Wharfe
const BRIDGES = ["ferrybridge"], FORDS = ["castleford"];

// ---------- woods (centre, radius km) and marsh ----------
const WOODS = [[[53.845, -1.287], 0.6], [[53.875, -1.375], 1.5], [[53.862, -1.330], 1.2], [[53.640, -1.300], 2.5], [[53.765, -1.330], 1.0]];
const MARSH = [[[53.700, -1.110], 2.5], [[53.860, -1.075], 1.2], [[53.735, -1.215], 1.0]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["wentbridge", "darrington", "ferrybridge", "brotherton", "fairburn", "sherburn", "dintingdale", "saxton", "towton", "tadcaster", [53.925, -1.170], "york"],
  ["pontefract", "ferrybridge"], ["wakefield", "pontefract", "darrington"], ["pontefract", "castleford", [53.765, -1.45], "leeds"],
  ["castleford", "aberford", [53.865, -1.310], "tadcaster"], ["leeds", "garforth", "aberford"], ["leeds", [53.830, -1.45], "bramham", "tadcaster"],
  ["leeds", [53.870, -1.470], "wetherby", [53.935, -1.250], "york"], ["sherburn", "hambleton", "selby"], ["sherburn", [53.815, -1.190], "cawood"],
  ["york", "bishopthorpe", "cawood"], ["ferrybridge", "knottingley"],
];

const TOWNS = ["york", "tadcaster", "pontefract", "leeds", "wakefield", "selby", "wetherby"];
const VILLAGES = ["towton", "saxton", "sherburn", "brotherton", "fairburn", "knottingley", "darrington", "wentbridge", "aberford", "barwick",
  "bramham", "bostonspa", "garforth", "stutton", "ulleskelf", "cawood", "hambleton", "bishopthorpe"];

const NAMES = { york: "York", bishopthorpe: "Bishopthorpe", tadcaster: "Tadcaster", towton: "Towton", saxton: "Saxton", lead: "Lead",
  cockbeck: "Cock Beck", stutton: "Stutton", dintingdale: "Dintingdale", sherburn: "Sherburn-in-Elmet", fairburn: "Fairburn",
  brotherton: "Brotherton", ferrybridge: "Ferrybridge", knottingley: "Knottingley", pontefract: "Pontefract", darrington: "Darrington",
  wentbridge: "Wentbridge", castleford: "Castleford ford", wakefield: "Wakefield", leeds: "Leeds", garforth: "Garforth", aberford: "Aberford",
  barwick: "Barwick-in-Elmet", bramham: "Bramham", bostonspa: "Boston Spa", wetherby: "Wetherby", ulleskelf: "Ulleskelf", cawood: "Cawood",
  selby: "Selby", hambleton: "Hambleton" };
const notes = {
  pontefract: "Where the Yorkist army gathered, 27 and 28 March",
  ferrybridge: "The Aire crossing: Lord Clifford's dawn attack on the Yorkists holding it, 28 March",
  castleford: "Lord Fauconberg crossed the Aire here on 28 March to get round Clifford",
  dintingdale: "Where Clifford's men were caught and Clifford killed, 28 March",
  towton: "The battle, Palm Sunday, 29 March 1461, on the plateau between here and Saxton",
  saxton: "The Yorkists drew up just north of the village",
  cockbeck: "In flood on the day of the battle; many fleeing Lancastrians died crossing it",
  tadcaster: "The Wharfe crossing on the road to York, where the rout made for",
  york: "Henry VI and Queen Margaret waited here: the Yorkists' goal",
  wakefield: "Richard, Duke of York, was killed near here on 30 December 1460",
  wentbridge: "The Duke of Norfolk's men came up the road from the south, late",
};

const map = buildCampaign({
  id: "towton-1461", script: "make_towton.mjs", title: "The Towton campaign of March 1461, from Pontefract to York",
  name: "Towton campaign, 1461 (Pontefract to York)",
  start_date: "1461-03-27", calendar: "julian", latitude: 54, climate: "maritime", climate_shift: -1,
  bounds: [-1.6, 53.99, -0.99, 53.63], midLat: 53.81, hexKm: 1,
  header: [
    "Towns, villages, the bridge and the ford are at their modern places; rivers, brooks, woods",
    "and roads are drawn by hand through them and are approximate.",
    "",
    "What happened, briefly (dates Julian): Edward, Earl of March, was proclaimed king in London",
    "on 4 March 1461 and marched north after the Lancastrian army, with Henry VI and Queen",
    "Margaret at York. The Yorkists gathered around Pontefract. At dawn on 28 March Lord Clifford's",
    "horsemen surprised the Yorkists holding the Aire crossing at Ferrybridge; Lord Fauconberg",
    "crossed upstream at Castleford, and Clifford was caught and killed at Dintingdale as he fell",
    "back. On Palm Sunday, 29 March, the armies met on the plateau between Saxton and Towton, in a",
    "snowstorm blowing into the Lancastrians' faces. The Yorkist archers shot first and stepped",
    "back out of reach; the Lancastrians came on, and the lines fought for hours until the Duke of",
    "Norfolk's men came up on the Yorkist right and the Lancastrian line broke. Many died in the",
    "rout across Cock Beck and on the road to Tadcaster. Henry VI and Margaret fled from York to",
    "Scotland. Numbers on both sides are disputed; those below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["aire", "wharfe", "ouse"], streams: STREAMS,
  bridges: BRIDGES, fords: FORDS, woods: WOODS, marsh: MARSH, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { pontefract: "camp", york: "objective" },
  forces: [
    { name: "Edward's army", type: "foot", side: "York", men: 15000, tools: true, at: "pontefract" },
    { name: "Fauconberg's vanward", type: "mounted", side: "York", men: 2000, tools: false, at: "pontefract" },
    { name: "Fitzwalter's men at the crossing", type: "foot", side: "York", men: 500, tools: false, at: "brotherton" },
    { name: "Norfolk's men", type: "foot", side: "York", men: 5000, tools: true, at: "wentbridge" },
    { name: "Lancastrian army (Somerset)", type: "foot", side: "Lancaster", men: 25000, tools: true, at: "towton" },
    { name: "Clifford's horse", type: "mounted", side: "Lancaster", men: 500, tools: false, at: "sherburn" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
