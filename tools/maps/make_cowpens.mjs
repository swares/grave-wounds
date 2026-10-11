// Builds data/maps/cowpens-1781.yaml: the Cowpens campaign of January 1781 on the travel map, at
// 1 km a hex, in the South Carolina upcountry between the Pacolet and the Broad. Run from this
// folder after editing: npm ci && node make_cowpens.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the places are placed at their modern sites where they are known (the Cowpens battlefield)
//   and only approximately where they are not (the shoals, the iron works, Thicketty fort);
// - the Broad and Pacolet rivers, the creeks, the woods and the roads are drawn by hand through
//   those places, after the line of the modern rivers and roads. They are approximate.
// The country was mostly open forest then, with scattered farms and cattle pastures (the
// "cowpens"), so the map is forest with clearings.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  cowpens: [35.142, -81.817], thicketty: [35.050, -81.700], easterwood: [34.928, -81.780], grindal: [34.962, -81.640],
  ironworks: [34.935, -81.860], cherokee: [35.105, -81.545], broadfork: [35.250, -81.700], goudelock: [35.010, -81.745],
  mountain: [35.280, -81.900], union: [34.875, -81.620], fairforest: [34.880, -81.930], camp: [34.975, -81.655],
};

// ---------- rivers (impassable but at a bridge, a ford or a town) and creeks ----------
const RIVERS = {
  broad: [[35.330, -81.770], "broadfork", [35.180, -81.600], "cherokee", [35.000, -81.510], [34.900, -81.480], [34.820, -81.470]],
  pacolet: [[35.030, -82.010], [34.980, -81.900], "easterwood", [34.945, -81.700], "grindal", [34.920, -81.560], [34.900, -81.490]],
};
const STREAMS = [
  [[35.180, -81.760], [35.100, -81.720], "thicketty", [35.000, -81.620], [34.950, -81.560]],    // Thicketty Creek
  [[35.200, -81.860], [35.130, -81.780], [35.080, -81.640], [35.040, -81.560]],              // Cherokee Creek, approximate
  [[34.990, -81.960], "fairforest", [34.860, -81.880]],                                       // Fair Forest Creek
];
const FORDS = ["easterwood", "grindal", "cherokee", "broadfork"];

// ---------- the country: forest, with clearings and farms; low ridges (centre, radius km) ----------
const CLEARINGS = [[[35.142, -81.817], 1.6], [[35.050, -81.700], 1.2], [[34.962, -81.640], 1.2], [[35.010, -81.745], 1.2]];
const FARMS = [[[34.935, -81.860], 2], [[34.875, -81.620], 2], [[34.880, -81.930], 1.8], [[35.105, -81.545], 1.2], [[35.200, -81.880], 1.5]];
const HILLS = [[[35.280, -81.900], 3.5], [[35.230, -81.980], 3]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["easterwood", "goudelock", "thicketty", "cowpens", [35.230, -81.840], "mountain"],      // the road Tarleton came up, and on toward the mountains
  ["grindal", "camp", "thicketty"], ["grindal", "union"], ["cowpens", [35.150, -81.700], "cherokee"],  // the Green River road east to the Broad
  ["ironworks", "easterwood"], ["ironworks", "fairforest"], ["cowpens", [35.200, -81.760], "broadfork"],
  ["union", [34.900, -81.760], "ironworks"],
];

const TOWNS = [];
const VILLAGES = ["ironworks", "union", "fairforest"];

const NAMES = { cowpens: "Hannah's Cowpens", thicketty: "Thicketty Fort", easterwood: "Easterwood Shoals", grindal: "Grindal Shoals",
  ironworks: "Wofford's Iron Works", cherokee: "Cherokee Ford", broadfork: "Island Ford (approximate)", goudelock: "Goudelock's farm",
  mountain: "Toward Gilbert Town", union: "Union Court House", fairforest: "Fair Forest", camp: "Morgan's camp" };
const notes = {
  cowpens: "A cattle pasture by the Green River road, where Morgan turned to fight on 17 January",
  grindal: "The ford by Morgan's camp on the Pacolet (approximate)",
  camp: "Morgan's camp above Grindal Shoals until 15 January (approximate)",
  easterwood: "Where Tarleton crossed the Pacolet on 15 to 16 January (approximate)",
  goudelock: "Tarleton's men rested here before their night march (approximate)",
  broadfork: "Morgan's way north over the Broad after the battle (approximate)",
};

const map = buildCampaign({
  id: "cowpens-1781", script: "make_cowpens.mjs", title: "The Cowpens campaign of January 1781, between the Pacolet and the Broad",
  name: "Cowpens campaign, 1781 (the Pacolet to the Broad)",
  start_date: "1781-01-14", calendar: "gregorian", latitude: 35, climate: "carolina", climate_shift: -1,
  bounds: [-82.02, 35.33, -81.46, 34.84], midLat: 35.08, hexKm: 1, base: "F",
  header: [
    "Hannah's Cowpens is at its modern site; the shoals, the fort, the iron works and the camps are",
    "only approximate; rivers, creeks, woods and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly: in January 1781 General Daniel Morgan's small American force raided in",
    "the South Carolina upcountry, west of Lord Cornwallis's army. Cornwallis sent Lieutenant",
    "Colonel Banastre Tarleton after him with his Legion, light infantry and regulars. Morgan fell",
    "back from the Pacolet, and with the Broad River behind him chose to fight at the Cowpens, a",
    "pasture on the road north. Tarleton marched through the night and attacked at dawn on 17",
    "January. Morgan's riflemen and militia fired and fell back as planned; when the British",
    "pressed on against his Continentals, the Americans turned and closed on both flanks while",
    "their cavalry came in behind. Most of Tarleton's force was killed, wounded or taken in under",
    "an hour. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["broad", "pacolet"], streams: STREAMS, fords: FORDS,
  clearings: CLEARINGS, farms: FARMS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { camp: "camp" },
  forces: [
    { name: "Morgan's Continentals", type: "foot", side: "Americans", men: 600, tools: true, at: "camp" },
    { name: "Militia and riflemen (Pickens)", type: "foot", side: "Americans", men: 1000, tools: false, at: "camp" },
    { name: "Washington's cavalry", type: "mounted", side: "Americans", men: 120, tools: false, at: "camp" },
    { name: "Tarleton's foot", type: "foot", side: "British", men: 800, tools: true, at: "ironworks" },
    { name: "Tarleton's Legion horse", type: "mounted", side: "British", men: 300, tools: false, at: "ironworks" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
