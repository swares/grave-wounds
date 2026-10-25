// Builds data/maps/tumbledown-1982.yaml: the hills west of Stanley on East Falkland, June 1982, on
// the travel map at 0.5 km a hex, from Two Sisters and Goat Ridge east to Sapper Hill and Stanley.
// Run from this folder after editing: npm ci && node make_tumbledown.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours (the project's
// tumbledown-research.md):
// - the plain facts of the battle as the accounts give them: the 2nd Battalion, Scots Guards, about
//   640 men, flown to Goat Ridge on 13 June 1982, attacked Mount Tumbledown from the west that
//   night, with the 1st/7th Gurkha Rifles following on to Mount William; the Argentine 5th Marine
//   Infantry Battalion (BIM 5), about 700 marines and 200 soldiers, held Tumbledown, Mount William
//   and Sapper Hill, and was ordered back to Sapper Hill on the morning of the 14th;
// - the hills, Moody Brook and the positions placed after the accounts' relative positions, not
//   printed coordinates; Stanley Harbour, the Fitzroy-Stanley track and the ground drawn by hand.
//   They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const P = {
  stanley: [-51.695, -57.851], moodybrook: [-51.686, -57.924], sapper: [-51.707, -57.870], tumbledown: [-51.692, -57.962],
  tumbledownwest: [-51.693, -57.980], william: [-51.703, -57.935], goatridge: [-51.694, -58.000], harriet: [-51.698, -58.025],
  twosisters: [-51.683, -58.045], wireless: [-51.672, -57.920], ponyspass: [-51.712, -57.950],
  west: [-51.715, -58.080], east: [-51.700, -57.820],
};
const WATER = [
  [[-51.684, -57.930], [-51.683, -57.900], [-51.687, -57.875], [-51.690, -57.850], [-51.688, -57.825], [-51.684, -57.800],
    [-51.672, -57.800], [-51.676, -57.830], [-51.679, -57.870], [-51.679, -57.905], [-51.681, -57.930]],                  // Stanley Harbour, from Moody Brook east
];
const MARSH = [[[-51.715, -58.000], 1.0], [[-51.675, -57.970], 0.8], [[-51.720, -57.900], 0.8]];
const HILLS = [[P.tumbledown, 0.6], [P.tumbledownwest, 0.4], [P.william, 0.5], [P.sapper, 0.4], [P.goatridge, 0.4], [P.harriet, 0.5],
  [P.twosisters, 0.6], [P.wireless, 0.5]];
const ROADS = [["west", [-51.712, -58.000], "ponyspass", [-51.710, -57.900], "sapper", "stanley", "east"], ["moodybrook", "stanley"]];
const NAMES = {
  stanley: "Stanley (Puerto Argentino)", moodybrook: "Moody Brook", sapper: "Sapper Hill", tumbledown: "Mount Tumbledown",
  tumbledownwest: "Tumbledown, the western end", william: "Mount William", goatridge: "Goat Ridge", harriet: "Mount Harriet",
  twosisters: "Two Sisters", wireless: "Wireless Ridge", ponyspass: "Pony's Pass",
};
const notes = {
  goatridge: "The Scots Guards' assembly area, flown in on 13 June 1982 (approximate)",
  tumbledown: "The summit crags, held by N Company, BIM 5, and taken by the Scots Guards on the morning of 14 June (approximate)",
  william: "Taken by the 1st/7th Gurkha Rifles on 14 June (approximate)",
  sapper: "BIM 5 fell back here on the morning of 14 June (approximate)",
  stanley: "The Argentine garrison surrendered on 14 June 1982",
};
const map = buildCampaign({
  id: "tumbledown-1982", script: "make_tumbledown.mjs", title: "Tumbledown, June 1982",
  name: "Tumbledown, 1982 (the hills west of Stanley)",
  start_date: "1982-06-13", calendar: "gregorian", latitude: -52, climate: "falklands", climate_shift: 0, base: ".", coast: "drawn",
  bounds: [-58.080, -51.660, -57.800, -51.730], midLat: -51.695, hexKm: 0.5,
  header: [
    "The hills and the positions are placed after the accounts and approximate; Stanley Harbour,",
    "the Fitzroy-Stanley track and the ground are drawn by hand, the land data being too coarse.",
    "Open, treeless grass and peat, boggy in the hollows, with long rocky ridges and crags on the",
    "hills; no trees and no cover but the folds of the ground and the rocks.",
    "",
    "What happened, briefly: on the night of 13-14 June 1982 the 2nd Battalion, Scots Guards attacked",
    "Mount Tumbledown from Goat Ridge, after a diversion along the track to the south. The marines of",
    "BIM 5 held the summit crags until the bayonet assault after 02:30 and were ordered back to",
    "Sapper Hill at first light; the Gurkhas went on to Mount William. The Argentine garrison of",
    "Stanley surrendered that day. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, water: WATER, rivers: {}, majorRivers: [], streams: [], bridges: [], fords: [],
  farms: [], woods: [], marsh: MARSH, hills: HILLS, mountains: [], roads: ROADS,
  towns: ["stanley"], villages: ["moodybrook"],
  kinds: { goatridge: "camp", tumbledown: "objective", william: "objective", sapper: "objective" },
  depots: { goatridge: ["British"], stanley: ["Argentines"] },   // where each side resupplies (project doc "depots-research")
  forces: [
    { name: "2nd Battalion, Scots Guards", type: "foot", side: "British", men: 640, tools: true, at: "goatridge" },
    { name: "1st Battalion, 7th Gurkha Rifles", type: "foot", side: "British", men: 600, tools: true, at: "goatridge" },
    { name: "N Company, BIM 5, with army platoons", type: "foot", side: "Argentines", men: 250, tools: true, at: "tumbledown" },
    { name: "BIM 5 on Mount William", type: "foot", side: "Argentines", men: 150, tools: true, at: "william" },
    { name: "BIM 5's headquarters and reserve (Sapper Hill)", type: "foot", side: "Argentines", men: 400, tools: true, at: "sapper" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
