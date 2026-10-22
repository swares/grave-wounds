// Builds data/maps/goosegreen-1982.yaml: the Darwin isthmus on East Falkland, May 1982, on the
// travel map at 0.5 km a hex, from Camilla Creek House south down the isthmus to Darwin and Goose
// Green. Run from this folder after editing: npm ci && node make_goosegreen.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the official history gives them and as they are summarised
//   publicly: the 2nd Battalion, the Parachute Regiment, about 500 men, marched south from San
//   Carlos to Camilla Creek House and on the night of 27-28 May 1982 attacked down the narrow
//   isthmus, past Burntside House and Coronation Point, to the Argentine line across it from
//   Darwin Hill to Boca House; the battalion's commanding officer was killed on Darwin Hill; the
//   Argentine garrison of Goose Green and its airstrip, about 1,000 of the 12th Infantry Regiment
//   and air force men, surrendered on 29 May;
// - the settlements and the positions placed after the accounts and approximate; the shores of
//   Brenton Loch and Choiseul Sound, the tracks and the ground drawn by hand (the land data is
//   too coarse for an isthmus a mile wide). They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  camilla: [-51.752, -58.975], burntside: [-51.785, -58.990], coronation: [-51.793, -58.950], darwin: [-51.800, -58.955],
  darwinhill: [-51.806, -58.963], boca: [-51.830, -59.015], goosegreen: [-51.823, -58.972], airstrip: [-51.829, -58.962],
  north: [-51.722, -58.980], lafonia: [-51.860, -59.000],
};
const WATER = [
  [[-51.715, -59.150], [-51.715, -59.060], [-51.760, -59.030], [-51.790, -59.008], [-51.805, -58.990], [-51.815, -59.002], [-51.830, -59.035],
    [-51.875, -59.070], [-51.875, -59.150]],                                                                              // Brenton Loch and Falkland Sound, to the west
  [[-51.782, -58.800], [-51.788, -58.915], [-51.796, -58.940], [-51.808, -58.946], [-51.818, -58.955], [-51.832, -58.957], [-51.848, -58.952],
    [-51.875, -58.935], [-51.875, -58.800]],                                                                              // Choiseul Sound, to the east
];
const MARSH = [[[-51.770, -58.960], 0.8], [[-51.740, -58.950], 1.0], [[-51.850, -58.990], 1.0]];
const HILLS = [[P.darwinhill, 0.5], [[-51.735, -59.010], 1.0]];
const ROADS = [["north", "camilla", "burntside", [-51.795, -58.975], "darwin"], [[-51.795, -58.975], "goosegreen", "airstrip"], ["goosegreen", "lafonia"]];
const NAMES = {
  camilla: "Camilla Creek House", burntside: "Burntside House", coronation: "Coronation Point", darwin: "Darwin", darwinhill: "Darwin Hill",
  boca: "Boca House", goosegreen: "Goose Green", airstrip: "Goose Green airstrip",
};
const notes = {
  camilla: "2 Para's start line for the night march south, 27 May 1982 (approximate)",
  darwinhill: "The Argentine line's eastern end, where Lieutenant-Colonel H. Jones was killed on 28 May (approximate)",
  boca: "The Argentine line's western end (approximate)",
  goosegreen: "The settlement and the Argentine garrison, which surrendered on 29 May 1982 (approximate)",
};
const map = buildCampaign({
  id: "goosegreen-1982", script: "make_goosegreen.mjs", title: "Goose Green, May 1982",
  name: "Goose Green, 1982 (the Darwin isthmus)",
  start_date: "1982-05-27", calendar: "gregorian", latitude: -52, climate: "falklands", climate_shift: 0, base: ".", coast: "drawn",
  bounds: [-59.100, -51.720, -58.850, -51.870], midLat: -51.80, hexKm: 0.5,
  header: [
    "The settlements and the Argentine positions are placed after the accounts and approximate;",
    "the shores of Brenton Loch and Choiseul Sound, the tracks and the ground are drawn by hand,",
    "the land data being too coarse for the isthmus. Open, treeless grass and peat with gorse",
    "hedges, boggy in the hollows; no trees and no cover but the folds of the ground.",
    "",
    "What happened, briefly: on the night of 27-28 May 1982 the 2nd Battalion, the Parachute",
    "Regiment attacked south from Camilla Creek House down the Darwin isthmus. At dawn it was held",
    "by the Argentine line from Darwin Hill to Boca House, where its commanding officer was killed;",
    "by the afternoon the line had broken and the paratroopers closed round Goose Green. The",
    "Argentine garrison, outnumbering them two to one, surrendered on the 29th. Numbers below are",
    "round figures for play.",
  ],
  places: P, names: NAMES, notes, water: WATER, rivers: {}, majorRivers: [], streams: [], bridges: [], fords: [],
  farms: [], woods: [], marsh: MARSH, hills: HILLS, mountains: [], roads: ROADS,
  towns: [], villages: ["darwin", "goosegreen", "camilla", "burntside", "boca"],
  kinds: { camilla: "camp", darwinhill: "objective", goosegreen: "objective" },
  depots: { camilla: ["British"], goosegreen: ["Argentines"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "2nd Battalion, the Parachute Regiment", type: "foot", side: "British", men: 500, tools: true, at: "camilla" },
    { name: "Argentine company on Darwin Hill", type: "foot", side: "Argentines", men: 120, tools: true, at: "darwinhill" },
    { name: "Argentine company at Boca House", type: "foot", side: "Argentines", men: 100, tools: true, at: "boca" },
    { name: "12th Infantry Regiment (Task Force Mercedes)", type: "foot", side: "Argentines", men: 600, tools: true, at: "goosegreen" },
    { name: "Argentine air force men and anti-aircraft guns", type: "foot", side: "Argentines", men: 200, tools: true, at: "airstrip" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
