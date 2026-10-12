// Builds data/maps/cassino-1944.yaml: Cassino and the Monte Cassino massif, February to May 1944,
// on the travel map at 0.5 km a hex, from Monte Cairo to the Liri valley and from Piedimonte to
// Cervaro. Run from this folder after editing: npm ci && node make_cassino.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battles as the official histories give them and as they are
//   summarised publicly: the abbey on Monte Cassino above the town, bombed on 15 February
//   1944; the 4th Indian Division's attacks along Snakeshead Ridge on Point 593 in February;
//   the New Zealand Corps' attack on the bombed town and Castle Hill in March; the 2nd Polish
//   Corps' attack on Point 593 and the ridges beyond in May; the Rapido east of the town, Route 6
//   through it and on into the Liri valley;
// - the abbey, the town, Cervaro, Piedimonte San Germano, Caira and Sant'Angelo in Theodice
//   at their modern centres, rounded; Castle Hill, Hangman's Hill, Point 593, Snakeshead Ridge
//   and Phantom Ridge placed after the accounts and approximate;
// - the mountains, the river, the roads and the railroad drawn by hand through those places.
//   They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  abbey: [41.4903, 13.8139], town: [41.4881, 13.8297], castle: [41.4917, 13.8237], hangman: [41.4902, 13.8180], p593: [41.5005, 13.8085],
  snakeshead: [41.5055, 13.8020], phantom: [41.5075, 13.7950], station: [41.4825, 13.8270], piedimonte: [41.4994, 13.7490],
  cairo: [41.5437, 13.7608], caira: [41.5090, 13.8180], santangelo: [41.4560, 13.8020], cervaro: [41.4833, 13.9014],
  east: [41.4850, 13.8700], north: [41.5300, 13.8250],   // where the Allied divisions come in (not places)
};

// ---------- the Rapido (crossed at its bridges) and the streams ----------
const RIVERS = {
  rapido: [[41.5500, 13.8420], [41.5200, 13.8380], [41.4990, 13.8350], [41.4880, 13.8345], [41.4720, 13.8230], [41.4560, 13.8100], [41.4380, 13.8150]],
};
const STREAMS = [[[41.5000, 13.8800], [41.4900, 13.8600], [41.4870, 13.8400]]];
const BRIDGES = [[41.4885, 13.8346], [41.4560, 13.8100], [41.5200, 13.8381]].map((p, i) => { P["bridge" + i] = p; return "bridge" + i });

// ---------- the massif and the hills; farmland in the valleys ----------
const MOUNTAINS = [[P.cairo, 3.0], [[41.5050, 13.7900], 1.6], [[41.5150, 13.7800], 1.6], [[41.4950, 13.8050], 0.9]];
const HILLS = [[P.abbey, 0.6], [P.p593, 0.6], [P.castle, 0.25], [[41.5200, 13.8150], 0.9], [[41.4950, 13.8800], 1.2], [[41.4750, 13.9000], 1.4], [[41.5250, 13.8650], 1.4]];
const WOODS = [[[41.5300, 13.8000], 1.0], [[41.4650, 13.8800], 0.8]];

// ---------- roads and the railroad (through places, in order) ----------
const ROADS = [
  ["cervaro", "east", [41.4870, 13.8460], "bridge0", "town", [41.4820, 13.8150], [41.4700, 13.7850], [41.4550, 13.7500], [41.4450, 13.7250]],   // Route 6, the Via Casilina, into the Liri valley
  ["town", [41.4950, 13.8300], "caira", "north"],                                                     // the road north up the valley to Caira
  ["town", "castle", [41.4930, 13.8180], "abbey"],                                                    // the winding road up to the abbey
  ["east", "station", [41.4700, 13.8100], [41.4500, 13.7800]],                                       // the railroad from the station into the Liri valley
  ["santangelo", "bridge1", [41.4600, 13.8300]], ["piedimonte", [41.4800, 13.7600], [41.4700, 13.7850]],
];

const NAMES = { abbey: "The abbey of Monte Cassino", town: "Cassino", castle: "Castle Hill (Point 193)", hangman: "Hangman's Hill (Point 435)", p593: "Point 593 (Monte Calvario)",
  snakeshead: "Snakeshead Ridge", phantom: "Phantom Ridge", station: "Cassino station", piedimonte: "Piedimonte San Germano", cairo: "Monte Cairo",
  caira: "Caira", santangelo: "Sant'Angelo in Theodice", cervaro: "Cervaro" };
const notes = {
  abbey: "Bombed to ruins on 15 February 1944; the Germans then held the rubble. Polish troops raised their flag over it on 18 May",
  p593: "The key to the massif: the 4th Indian Division failed to take it in February, the Poles took it in May (approximate)",
  snakeshead: "The narrow ridge from Point 593 towards the abbey along which the Indians attacked (approximate)",
  castle: "The castle above the town, taken by the New Zealanders on 15 March and held through the third battle (approximate)",
  hangman: "Gurkhas reached the hill below the abbey in March and held it for nine days (approximate)",
  town: "Bombed and shelled to rubble on 15 March 1944; German paratroops held its cellars and ruins",
  phantom: "Attacked by the Polish 5th Kresowa Division on 12 May (approximate)",
};

const map = buildCampaign({
  id: "cassino-1944", script: "make_cassino.mjs", title: "Cassino and Monte Cassino, February to May 1944",
  name: "Cassino, 1944 (Monte Cairo to the Liri valley)",
  start_date: "1944-02-15", calendar: "gregorian", latitude: 41, climate: "mediterranean", climate_shift: -1, base: "f",
  bounds: [13.720, 41.560, 13.930, 41.430], midLat: 41.49, hexKm: 0.5,
  header: [
    "The abbey, the town and the villages are at their modern centres, rounded; Castle Hill,",
    "Hangman's Hill, Point 593 and the ridges are placed after the accounts and approximate; the",
    "massif, hills, river, roads and railroad are drawn by hand. The valleys are farmland and",
    "olive terraces; the massif is bare rock and scrub.",
    "",
    "What happened, briefly: the abbey on Monte Cassino overlooked the Liri valley, the road to",
    "Rome, and the Germans' Gustav Line ran through the town and over the massif. The Americans",
    "failed to cross the Rapido and take the heights in January 1944. On 15 February bombers",
    "destroyed the abbey, and the 4th Indian Division attacked along Snakeshead Ridge for Point",
    "593 and failed. On 15 March the town was bombed and shelled to rubble and the New Zealand",
    "Corps attacked into it; German paratroops held the ruins for eight days. In May, in the fourth",
    "battle, the 2nd Polish Corps attacked Point 593 and the ridges beyond; the Germans, outflanked",
    "in the Liri valley, gave up the massif, and the Poles raised their flag over the abbey on 18",
    "May. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["rapido"], streams: STREAMS, bridges: BRIDGES, fords: [],
  woods: WOODS, hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: ["town"], villages: ["caira", "piedimonte", "santangelo", "cervaro"],
  kinds: { abbey: "objective", p593: "objective", town: "objective" },
  forces: [
    { name: "4th Indian Division", type: "foot", side: "Allies", men: 6000, tools: true, at: "north" },
    { name: "2nd New Zealand Division", type: "foot", side: "Allies", men: 6000, tools: true, at: "east" },
    { name: "German paratroops and panzergrenadiers (the abbey and the massif)", type: "foot", side: "Germans", men: 3000, tools: true, at: "abbey" },
    { name: "German paratroops (the town)", type: "foot", side: "Germans", men: 1500, tools: true, at: "town" },
    { name: "German reserves (Piedimonte)", type: "foot", side: "Germans", men: 2000, tools: true, at: "piedimonte" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
