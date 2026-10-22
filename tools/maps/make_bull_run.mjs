// Builds data/maps/bull-run-1861.yaml: the First Bull Run (Manassas) campaign of July 1861 on the
// travel map, at 1 km a hex, from Fairfax Court House to Gainesville. Run from this folder after
// editing: npm ci && node make_bull_run.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - villages, the junction, the Stone Bridge and Henry Hill are placed at their modern sites
//   (facts); the fords on Bull Run are only approximate;
// - Bull Run, its creeks, woods, roads and the railways (drawn as roads) are drawn by hand
//   through those places, after the line of the modern streams and roads. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  centreville: [38.840, -77.429], fairfax: [38.846, -77.306], fxstation: [38.802, -77.326], manassas: [38.751, -77.475],
  stonebridge: [38.826, -77.534], sudley: [38.856, -77.553], ballsford: [38.817, -77.508], mitchell: [38.808, -77.460],
  blackburn: [38.802, -77.449], mclean: [38.796, -77.438], unionmills: [38.786, -77.424], henryhill: [38.813, -77.521],
  groveton: [38.817, -77.572], gainesville: [38.796, -77.614], cubrun: [38.837, -77.470], farmford: [38.836, -77.541],
};

// ---------- Bull Run (crossed only at its fords and the Stone Bridge), Cub Run, creeks ----------
const RIVERS = {
  bullrun: [[38.910, -77.650], [38.880, -77.590], [38.862, -77.562], "sudley", [38.845, -77.545], "farmford", "stonebridge",
            [38.822, -77.520], "ballsford", [38.812, -77.480], "mitchell", "blackburn", "mclean", "unionmills", [38.760, -77.410], [38.700, -77.385]],
  cubrun: [[38.930, -77.475], [38.880, -77.472], "cubrun", [38.815, -77.468], [38.810, -77.466]],
};
const STREAMS = [
  [[38.800, -77.630], [38.830, -77.585], [38.850, -77.560]],         // Catharpin Run
  [[38.830, -77.570], [38.825, -77.545], [38.823, -77.530]],         // Young's Branch, under Henry Hill
  [[38.760, -77.560], [38.780, -77.520], [38.800, -77.505]],         // a branch from the south-west, approximate
];
const BRIDGES = ["stonebridge"];
const FORDS = ["sudley", "farmford", "ballsford", "mitchell", "blackburn", "mclean", "unionmills"];

// ---------- woods (centre, radius km) and the low hills ----------
const WOODS = [[[38.850, -77.510], 2.2], [[38.870, -77.560], 2], [[38.800, -77.540], 1.8], [[38.780, -77.450], 2.2], [[38.820, -77.400], 2],
  [[38.880, -77.420], 2.5], [[38.780, -77.580], 2.2], [[38.890, -77.330], 2], [[38.760, -77.350], 2.2], [[38.840, -77.600], 1.5]];
const HILLS = [[[38.813, -77.521], 0.8], [[38.840, -77.429], 0.8], [[38.815, -77.540], 0.7]];

// ---------- roads and railways (through places, in order) ----------
const ROADS = [
  ["fairfax", [38.842, -77.370], "centreville", "cubrun", [38.830, -77.505], "stonebridge", [38.823, -77.528], "groveton", "gainesville"],   // the Warrenton Turnpike
  ["sudley", [38.835, -77.548], "henryhill", [38.780, -77.500], "manassas"],                                       // the Sudley road
  ["centreville", "mitchell", [38.775, -77.468], "manassas"], ["centreville", "blackburn"], ["centreville", "unionmills"],
  ["cubrun", [38.852, -77.497], [38.862, -77.530], "sudley"],                                                     // the Union flank march
  ["manassas", "unionmills", "fxstation", [38.790, -77.270]], ["manassas", [38.775, -77.550], "gainesville"],   // the railways
  ["fairfax", "fxstation"], ["henryhill", "ballsford", [38.830, -77.470]],
];

const TOWNS = [];
const VILLAGES = ["centreville", "fairfax", "manassas", "groveton", "gainesville"];

const NAMES = { centreville: "Centreville", fairfax: "Fairfax Court House", fxstation: "Fairfax Station", manassas: "Manassas Junction",
  stonebridge: "Stone Bridge", sudley: "Sudley Springs Ford", ballsford: "Ball's Ford", mitchell: "Mitchell's Ford",
  blackburn: "Blackburn's Ford", mclean: "McLean's Ford", unionmills: "Union Mills Ford", henryhill: "Henry Hill",
  groveton: "Groveton", gainesville: "Gainesville", cubrun: "Cub Run bridge", farmford: "Farm Ford" };
const notes = {
  centreville: "McDowell's army gathered here from 18 July",
  manassas: "The railway junction both armies wanted; Johnston's army came in here by train from 19 July",
  blackburn: "Where Tyler's probe was thrown back on 18 July (approximate)",
  stonebridge: "Evans's small brigade held the turnpike crossing on the morning of 21 July",
  sudley: "Where the Union flank march crossed Bull Run on 21 July (approximate)",
  henryhill: "Where Jackson's brigade stood 'like a stone wall' and the battle turned",
  farmford: "Sherman's brigade waded over here in the afternoon (approximate)",
};

const map = buildCampaign({
  id: "bull-run-1861", script: "make_bull_run.mjs", title: "The First Bull Run campaign of July 1861, from Fairfax Court House to Gainesville",
  name: "First Bull Run campaign, 1861 (Fairfax to Gainesville)",
  start_date: "1861-07-18", calendar: "gregorian", latitude: 39, climate: "virginia", climate_shift: -0.5,
  bounds: [-77.66, 38.93, -77.27, 38.70], midLat: 38.81, hexKm: 1,
  header: [
    "Villages, the junction, the Stone Bridge and Henry Hill are at their modern places; the fords",
    "on Bull Run are only approximate; the streams, woods, roads and railways (drawn as roads) are",
    "drawn by hand and approximate.",
    "",
    "What happened, briefly: in July 1861 Brigadier General Irvin McDowell's Union army marched",
    "out of Washington toward the railway junction at Manassas, held by General P. G. T.",
    "Beauregard's Confederates behind Bull Run. A probe at Blackburn's Ford on 18 July was thrown",
    "back. While McDowell planned, General Joseph E. Johnston brought most of his army from the",
    "Shenandoah Valley by train. On 21 July the Union made a show at the Stone Bridge and marched",
    "round by Sudley Springs onto the Confederate left. They drove it back onto Henry Hill, where",
    "Jackson's brigade held; the Union batteries pushed onto the hill were taken, fresh Confederate",
    "brigades came up on the right, and the Union army fell back in a rout to Centreville and",
    "Washington. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["bullrun"], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { centreville: "camp", manassas: "objective" },
  depots: { manassas: ["Confederacy"], centreville: ["Union"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "Tyler's division", type: "foot", side: "Union", men: 9000, tools: true, at: "centreville" },
    { name: "Hunter's division", type: "foot", side: "Union", men: 2500, tools: true, at: "centreville" },
    { name: "Heintzelman's division", type: "foot", side: "Union", men: 9500, tools: true, at: "fairfax" },
    { name: "Miles's reserve", type: "foot", side: "Union", men: 6000, tools: true, at: "centreville" },
    { name: "Union cavalry", type: "mounted", side: "Union", men: 300, tools: false, at: "centreville" },
    { name: "Bonham's and Longstreet's brigades", type: "foot", side: "Confederacy", men: 8000, tools: true, at: "mitchell" },
    { name: "Ewell's and Jones's brigades", type: "foot", side: "Confederacy", men: 5000, tools: true, at: "unionmills" },
    { name: "Evans's and Cocke's brigades", type: "foot", side: "Confederacy", men: 4000, tools: true, at: "ballsford" },
    { name: "Beauregard's reserve", type: "foot", side: "Confederacy", men: 4000, tools: true, at: "manassas" },
    { name: "Johnston's army (coming by train)", type: "foot", side: "Confederacy", men: 9000, tools: true, at: "manassas" },
    { name: "Stuart's cavalry", type: "mounted", side: "Confederacy", men: 300, tools: false, at: "manassas" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
