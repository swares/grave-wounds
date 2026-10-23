// Builds data/maps/beaumont-hamel-1916.yaml: the northern half of the British front on the Somme on
// the eve of 1 July 1916, on the travel map at 1 km a hex, from Doullens to Bapaume and from
// Gommecourt to Albert. Run from this folder after editing: npm ci && node make_beaumont.mjs
//
// Sources, all plain fact, and the drawing is ours (project doc "beaumont-research"): towns and
// villages at their modern town halls (geo.api.gouv.fr), the Newfoundland Memorial at Wikipedia's
// point, Serre, Hamel, Gézaincourt and the woods only approximate; the Ancre, its marshes, the
// ridges, the woods, the roads and the metre-gauge and standard-gauge railways are drawn by hand
// through those places, after the modern ones, and are approximate. The divisions and regiments
// stand where Wikipedia's First Day on the Somme puts them; their strengths are round figures.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  park: [50.0736, 2.6481], beaumont: [50.0839, 2.6564], auchonvillers: [50.0805, 2.6311], mailly: [50.0768, 2.6050],
  englebelmer: [50.0597, 2.6090], mesnil: [50.0538, 2.6473], acheux: [50.0725, 2.5332], louvencourt: [50.0937, 2.4991],
  bertrancourt: [50.0921, 2.5592], forceville: [50.0611, 2.5562], varennes: [50.0491, 2.5342], hedauville: [50.0456, 2.5687],
  bouzincourt: [50.0267, 2.6099], senlis: [50.0263, 2.5780], albert: [50.0012, 2.6518], aveluy: [50.0236, 2.6596],
  authuille: [50.0421, 2.6681], hamel: [50.062, 2.670], marieux: [50.1068, 2.4436], puchevillers: [50.0531, 2.4086],
  beauquesne: [50.0832, 2.3920], doullens: [50.1574, 2.3412], gezaincourt: [50.145, 2.360], toutencourt: [50.0358, 2.4585],
  contay: [50.0040, 2.4800], raincheval: [50.0743, 2.4389], arqueves: [50.0725, 2.4694], lealvillers: [50.0644, 2.5100],
  warloy: [50.0096, 2.5246], authie: [50.1215, 2.4883], bus: [50.1036, 2.5433], colincamps: [50.1001, 2.6026],
  courcelles: [50.1035, 2.5836], sailly: [50.1198, 2.5955], bayencourt: [50.1313, 2.5703], coigneux: [50.1308, 2.5506],
  couin: [50.1345, 2.5313], souastre: [50.1528, 2.5641], pas: [50.1541, 2.4906], hebuterne: [50.1253, 2.6363],
  foncquevillers: [50.1487, 2.6318], gommecourt: [50.1400, 2.6440], serre: [50.100, 2.660], puisieux: [50.1167, 2.6939],
  bucquoy: [50.1404, 2.7089], achietp: [50.1228, 2.7513], achietg: [50.1321, 2.7844], beaucourt: [50.0802, 2.6860],
  grandcourt: [50.0809, 2.7088], miraumont: [50.0920, 2.7299], pys: [50.0879, 2.7555], irles: [50.1003, 2.7531],
  grevillers: [50.1037, 2.8114], biefvillers: [50.1155, 2.8228], ligny: [50.0844, 2.8280], bapaume: [50.1040, 2.8496],
  lesars: [50.0704, 2.7812], courcelette: [50.0579, 2.7444], pozieres: [50.0404, 2.7253], thiepval: [50.0544, 2.6895],
  redan: [50.095, 2.652],   // Redan Ridge and the Heidenkopf, where RIR 121 stood (not a place)
};

// ---------- rivers (crossed where a road bridges them), marsh ----------
const RIVERS = {
  ancre: ["miraumont", [50.084, 2.712], [50.078, 2.690], [50.068, 2.676], "hamel", [50.050, 2.670], [50.035, 2.665], [50.020, 2.660],
    [50.005, 2.652], [49.985, 2.640], [49.965, 2.625]],
};
const MARSH = [[[50.076, 2.690], 0.8], [[50.064, 2.673], 0.8], [[50.048, 2.670], 0.8], [[50.030, 2.663], 0.7]];   // the Ancre's wet valley floor (its 1916 extent is not known)
const BRIDGES = [];

// ---------- woods and ridges (centre, radius km) ----------
const WOODS = [[[50.036, 2.652], 1.2], [[50.055, 2.676], 0.7], [[50.137, 2.652], 0.6], [[50.082, 2.610], 0.5], [[50.118, 2.680], 0.6]];   // Aveluy, Thiepval, Gommecourt, Mailly and Rossignol woods (all approximate)
const HILLS = [[[50.056, 2.700], 1.6], [[50.095, 2.655], 0.9], [[50.083, 2.645], 0.6], [[50.085, 2.690], 0.8], [[50.080, 2.570], 1.2]];   // Thiepval Ridge, Redan Ridge, Hawthorn Ridge, Beaucourt Ridge, the summit between Acheux and Mailly

// ---------- roads and railways (through places, in order) ----------
const ROADS = [
  ["albert", [50.025, 2.598], "hedauville", "varennes", "acheux", "louvencourt", [50.120, 2.420], "doullens"],   // the Albert-Doullens road (D938)
  ["albert", "pozieres", [50.055, 2.760], "lesars", "ligny", "bapaume"],                                     // the Albert-Bapaume road
  ["acheux", "bertrancourt", "mailly", "auchonvillers", "beaumont", "beaucourt", "grandcourt", "miraumont", "irles", "achietp", "achietg"],
  ["mailly", "colincamps", "hebuterne", "foncquevillers", "souastre", "pas"], ["colincamps", "courcelles", "bus", "louvencourt"],
  ["mailly", "englebelmer", "mesnil", "hamel"], ["englebelmer", "hedauville"], ["bouzincourt", "aveluy", "authuille", "thiepval", "grandcourt"],
  ["albert", "bouzincourt", "senlis", "warloy", "contay"], ["varennes", "toutencourt", "puchevillers"], ["beauquesne", "raincheval", "arqueves", "lealvillers", "acheux"],
  ["marieux", "louvencourt"], ["marieux", "authie", "bus"], ["sailly", "bayencourt", "coigneux", "couin", "authie"],
  ["auchonvillers", "serre", "puisieux", "bucquoy"], ["puisieux", "miraumont"], ["bapaume", "biefvillers", "achietg"], ["bapaume", "grevillers", "irles"],
  ["pys", "courcelette", "pozieres"], ["miraumont", "pys", "lesars"], ["doullens", "gezaincourt", "beauquesne", "puchevillers", "toutencourt", "contay"],
  ["gezaincourt", [50.110, 2.430], "acheux", "forceville", "hedauville", "albert"],   // the Albert-Doullens metre-gauge railway, cut back to Gézaincourt (Réseau d'Albert)
  ["albert", "aveluy", "hamel", "beaucourt", "miraumont", "achietp", "achietg"],     // the Amiens-Arras standard gauge, German beyond the front
];

const TOWNS = ["albert", "doullens", "bapaume"];
const VILLAGES = ["beaumont", "auchonvillers", "mailly", "englebelmer", "mesnil", "acheux", "louvencourt", "bertrancourt", "forceville", "varennes",
  "hedauville", "bouzincourt", "senlis", "aveluy", "authuille", "marieux", "puchevillers", "beauquesne", "toutencourt", "contay", "raincheval",
  "arqueves", "lealvillers", "warloy", "authie", "bus", "colincamps", "courcelles", "sailly", "bayencourt", "coigneux", "couin", "souastre", "pas",
  "hebuterne", "foncquevillers", "gommecourt", "serre", "puisieux", "bucquoy", "achietp", "achietg", "beaucourt", "grandcourt", "miraumont", "pys",
  "irles", "grevillers", "biefvillers", "ligny", "lesars", "courcelette", "pozieres", "thiepval", "gezaincourt"];

const NAMES = { park: "Newfoundland Park (the battlefield)", beaumont: "Beaumont-Hamel", auchonvillers: "Auchonvillers", mailly: "Mailly-Maillet",
  englebelmer: "Englebelmer", mesnil: "Mesnil-Martinsart", acheux: "Acheux-en-Amiénois", louvencourt: "Louvencourt", bertrancourt: "Bertrancourt",
  forceville: "Forceville", varennes: "Varennes", hedauville: "Hédauville", bouzincourt: "Bouzincourt", senlis: "Senlis-le-Sec", albert: "Albert",
  aveluy: "Aveluy", authuille: "Authuille", hamel: "Hamel (approximate)", marieux: "Marieux", puchevillers: "Puchevillers", beauquesne: "Beauquesne",
  doullens: "Doullens", gezaincourt: "Gézaincourt (approximate)", toutencourt: "Toutencourt", contay: "Contay", raincheval: "Raincheval",
  arqueves: "Arquèves", lealvillers: "Léalvillers", warloy: "Warloy-Baillon", authie: "Authie", bus: "Bus-lès-Artois", colincamps: "Colincamps",
  courcelles: "Courcelles-au-Bois", sailly: "Sailly-au-Bois", bayencourt: "Bayencourt", coigneux: "Coigneux", couin: "Couin", souastre: "Souastre",
  pas: "Pas-en-Artois", hebuterne: "Hébuterne", foncquevillers: "Foncquevillers", gommecourt: "Gommecourt", serre: "Serre (approximate)",
  puisieux: "Puisieux", bucquoy: "Bucquoy", achietp: "Achiet-le-Petit", achietg: "Achiet-le-Grand", beaucourt: "Beaucourt-sur-l'Ancre",
  grandcourt: "Grandcourt", miraumont: "Miraumont", pys: "Pys", irles: "Irles", grevillers: "Grévillers", biefvillers: "Biefvillers-lès-Bapaume",
  ligny: "Ligny-Thilloy", bapaume: "Bapaume", lesars: "Le Sars", courcelette: "Courcelette", pozieres: "Pozières", thiepval: "Thiepval" };
const notes = {
  park: "The British line between Hawthorn Ridge and the Mary Redan, no man's land and the German line at Y Ravine: the 29th Division's attack and the Newfoundlanders' at 09:15 on 1 July",
  beaumont: "German since 1914: RIR 119 sheltered in deep dugouts under the village and in Y Ravine",
  louvencourt: "The Newfoundlanders' billets until 21:00 on 30 June, a three-hour march from St John's Road",
  acheux: "The VIII Corps collecting station and the metre-gauge railhead for the wounded",
  marieux: "VIII Corps headquarters (Hunter-Weston)",
  puchevillers: "The 3rd and 44th Casualty Clearing Stations; ambulance trains from 2 July",
  miraumont: "The 26th Reserve Division's main dressing station and its railway from Achiet",
  englebelmer: "Where the 1st Inniskillings left their ten per cent out of battle",
  mailly: "The 87th Field Ambulance's advanced dressing station",
  gommecourt: "The German salient attacked by the Third Army's 46th and 56th Divisions as a diversion",
  serre: "The village the 31st Division's Pals battalions attacked",
  thiepval: "The German fortress village south of the Ancre (RIR 99), facing the 36th and 32nd Divisions",
  albert: "The basilica's leaning Virgin; the railway and the metre-gauge hub behind the front",
  bapaume: "The first day's distant objective, on the Albert-Bapaume road",
  gezaincourt: "Where the Albert-Doullens metre gauge met the standard gauge to Frévent",
};

const map = buildCampaign({
  id: "beaumont-hamel-1916", script: "make_beaumont.mjs", title: "The Somme, 30 June 1916, from Doullens to Bapaume",
  name: "Beaumont-Hamel, 1916 (Doullens to Bapaume)",
  start_date: "1916-06-30", calendar: "gregorian", latitude: 50, climate: "maritime", climate_shift: 0,
  bounds: [2.33, 50.17, 2.87, 49.98], midLat: 50.08, hexKm: 1,
  header: [
    "Towns and villages are at their modern town halls; Serre, Hamel, Gézaincourt and the woods are only",
    "approximate; the Ancre, its marshes, the ridges, the woods, the roads and the railways are drawn by",
    "hand and approximate. The front line is not drawn: the forces stand where the divisions held it.",
    "",
    "What happened, briefly: after a week's bombardment from 24 June, the Fourth Army attacked on a",
    "front of 25 km at 07:30 on 1 July 1916, the Third Army at Gommecourt to its north as a diversion.",
    "North of the Ancre the VIII Corps' 31st, 4th and 29th Divisions went at Serre, Redan Ridge and",
    "Beaumont-Hamel against the Württemberg regiments of the 26th Reserve Division, who had held the",
    "line for twenty months and came up from deep dugouts when the barrage lifted. The Hawthorn Ridge",
    "mine went up ten minutes early, and the attack failed all along the corps front; the British",
    "lost 57,470 men that day. On 30 June the Newfoundland Regiment marched up from Louvencourt to",
    "the support trenches. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: [], streams: [], bridges: BRIDGES, fords: [],
  marsh: MARSH, woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { park: "objective", louvencourt: "camp", acheux: "camp", miraumont: "camp" },
  depots: { acheux: ["British"], doullens: ["British"], miraumont: ["Germans"] },   // railheads: Acheux, Doullens; Miraumont's station from Achiet (project doc "beaumont-research")
  forces: [
    { name: "1st Newfoundland Regiment", type: "foot", side: "British", men: 800, tools: true, at: "louvencourt" },
    { name: "29th Division (the rest)", type: "foot", side: "British", men: 11000, tools: true, at: "auchonvillers" },
    { name: "4th Division", type: "foot", side: "British", men: 12000, tools: true, at: "mailly" },
    { name: "31st Division", type: "foot", side: "British", men: 12000, tools: true, at: "colincamps" },
    { name: "36th (Ulster) Division", type: "foot", side: "British", men: 12000, tools: true, at: "aveluy" },
    { name: "VIII Corps supply columns", type: "wagons", side: "British", men: 1000, tools: true, at: "acheux" },
    { name: "RIR 119 (Beaumont-Hamel)", type: "foot", side: "Germans", men: 3000, tools: true, at: "beaumont" },
    { name: "RIR 121 (Redan Ridge)", type: "foot", side: "Germans", men: 3000, tools: true, at: "redan" },
    { name: "IR 169 (Serre)", type: "foot", side: "Germans", men: 3000, tools: true, at: "serre" },
    { name: "RIR 99 (Thiepval)", type: "foot", side: "Germans", men: 3000, tools: true, at: "thiepval" },
    { name: "26th Reserve Division trains", type: "wagons", side: "Germans", men: 1500, tools: true, at: "miraumont" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
