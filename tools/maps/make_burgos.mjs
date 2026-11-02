// Builds data/maps/burgos-1812.yaml: Wellington's siege of the castle of Burgos, 19 September to 21 October
// 1812, on the travel map at 1 km a hex, from Celada del Camino on the Valladolid road to Briviesca on the
// road to France. Run from this folder after editing: node make_burgos.mjs
//
// Sources (project docs "siege-phase-research" and "burgos-research"; historyofwar, Siege of Burgos;
// Wikipedia, Siege of Burgos; britishbattles.com, Retreat from Burgos): the 1st Division and Pack's
// Portuguese invested the castle on 19 September and stormed the hornwork of San Miguel that night; the
// outer wall was escaladed and failed on 22/23 September; the first mine was fired at midnight 29/30
// September and fell short; the second, on 4 October, brought down 100 feet of the rampart and the outer
// walls were taken; Dubreton's sorties on 5 and 8 October undid much of the work; the third mine, under San
// Roman, went off on 18 October and the storm failed. Wellington had about 24,000 Anglo-Portuguese and
// Santocildes' 11,000 Spaniards (Wikipedia); his covering divisions held a ridge at Rubena, about 8 km out
// on the Briviesca road, with pickets at Monasterio (Rodilla), where the French forced the stream on 18
// October. Souham's Army of Portugal had concentrated at Briviesca and, with part of Caffarelli's Army of
// the North, came to about 50,000 (historyofwar; britishbattles gives 45,000 and 9,000). It stood before
// Rubena on 21 October; that night Wellington gave up the siege and slipped away over the Arlanzón bridges.
// The garrison: about 2,000 under Dubreton (two battalions of the 34th Line, one of the 130th, gunners and
// sappers).
// The fortress (Sieges, docs/travel.md): broken by a mine. breach_days 10 (from the investment on 19
// September to the first mine on the night of 29 September) and redig 5 (to the second, on 4 October) are
// our reading of the dates: no source gives the galleries' digging days. 2,000 workers and 90 days' stores
// are ours (no source reached gives the working parties or the garrison's provisions; hunger played no part
// in 1812). Forces are round figures for play: the 35,000 allied total, the 2,000 garrison and the 50,000
// French are sourced; the splits between them are ours.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  burgos: [42.342, -3.704], siege: [42.350, -3.704], villafria: [42.364, -3.623], rubena: [42.382, -3.582],
  quintanapalla: [42.410, -3.551], monasterio: [42.457, -3.468], quintanavides: [42.487, -3.420], briviesca: [42.549, -3.322],
  atapuerca: [42.377, -3.507], villafranca: [42.389, -3.307], ibeas: [42.330, -3.552], castanares: [42.339, -3.633],
  villalbilla: [42.338, -3.773], buniel: [42.312, -3.822], celada: [42.262, -3.938], sotopalacios: [42.448, -3.682],
  cardenadijo: [42.304, -3.666], sarracin: [42.264, -3.700],
};
const NAMES = { burgos: "Burgos", siege: "Siege lines", villafria: "Villafría", rubena: "Rubena", quintanapalla: "Quintanapalla",
  monasterio: "Monasterio de Rodilla", quintanavides: "Quintanavides", briviesca: "Briviesca", atapuerca: "Atapuerca",
  villafranca: "Villafranca Montes de Oca", ibeas: "Ibeas de Juarros", castanares: "Castañares", villalbilla: "Villalbilla",
  buniel: "Villa de Buniel", celada: "Celada del Camino", sotopalacios: "Sotopalacios", cardenadijo: "Cardeñadijo", sarracin: "Sarracín" };
const notes = {
  burgos: "The castle on its hill above the town, held by Dubreton's 2,000; besieged from 19 September 1812 and never taken",
  siege: "The siege lines before the castle, from the hornwork of San Miguel (taken on the first night)",
  rubena: "Wellington's covering position, on a ridge about 8 km out on the Briviesca road; Souham stood before it at sunset on 21 October",
  monasterio: "The allied pickets' stream, forced by the French on 18 October (a piquet of Brunswickers taken)",
  briviesca: "Where Souham concentrated the Army of Portugal, with Caffarelli's men from the Army of the North",
  buniel: "Where the retreating columns met again on the night of 21-22 October",
  celada: "On the road back to Valladolid, the way the army retreated",
};

// ---------- rivers, brooks, hills, woods, roads ----------
const RIVERS = {
  arlanzon: [[42.300, -3.430], [42.318, -3.552], [42.326, -3.633], "burgos", [42.330, -3.725], [42.320, -3.773], [42.298, -3.822], [42.268, -3.895], [42.232, -3.960]],   // south of the villages on its north bank
};
const STREAMS = [
  ["quintanapalla", "rubena", "villafria", [42.348, -3.680]],      // the Vena, down to Burgos
];
const HILLS = [[[42.370, -3.515], 3], [[42.300, -3.610], 3], [[42.480, -3.760], 5], [[42.440, -3.560], 3]];   // the Sierra de Atapuerca, the heights south of the Arlanzón, the páramos north
const WOODS = [[[42.375, -3.335], 5], [[42.320, -3.470], 3]];   // the Montes de Oca; the woods toward the Sierra de la Demanda
const ROADS = [
  ["burgos", "villafria", "rubena", "quintanapalla", "monasterio", "quintanavides", "briviesca"],   // the camino real, the high road to France
  ["villafria", "atapuerca", "villafranca"],                                                    // the pilgrims' road east
  ["burgos", "villalbilla", "buniel", "celada"],                                                // to Valladolid
  ["burgos", "sotopalacios", [42.570, -3.690]],                                                 // north, toward Santander
  ["burgos", "cardenadijo", "sarracin", [42.250, -3.705]],                                      // south, toward Lerma and Madrid
];

const map = buildCampaign({
  id: "burgos-1812", script: "make_burgos.mjs", title: "The siege of Burgos, September and October 1812, from Celada to Briviesca",
  name: "Burgos, 1812 (the siege)",
  start_date: "1812-09-19", calendar: "gregorian", latitude: 42, climate: "continental", climate_shift: 2,   // Burgos, high on the meseta: about continental Europe's autumn, a little warmer by day (ours)
  bounds: [-3.96, 42.57, -3.30, 42.25], midLat: 42.41, hexKm: 1,
  header: [
    "Towns and villages are at their modern places; the siege lines are only approximate; rivers, brooks, woods,",
    "hills and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly (dates Gregorian): after Salamanca Wellington followed Clausel's beaten Army of",
    "Portugal north and came to Burgos on 19 September with about 35,000 men and only three 18-pounders. The",
    "town fell without a fight; Dubreton's 2,000 held the castle. The hornwork of San Miguel was stormed the",
    "first night, an escalade of the outer wall failed on the 22nd, the first mine fell short on the 29th, the",
    "second opened the outer wall on 4 October, and Dubreton's sorties undid much of the work. Souham gathered",
    "the Army of Portugal and part of the Army of the North at Briviesca, drove in the pickets at Monasterio on",
    "18 October, and stood before Rubena on the 21st. That night Wellington gave up the siege and slipped away",
    "over the Arlanzón bridges toward Valladolid. Burgos is a fortress here (docs/travel.md, Sieges), broken",
    "by a mine. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes,
  rivers: RIVERS, streams: STREAMS, hills: HILLS, woods: WOODS, roads: ROADS,
  towns: ["burgos", "briviesca"],
  villages: ["villafria", "rubena", "quintanapalla", "monasterio", "quintanavides", "atapuerca", "villafranca", "ibeas", "castanares",
    "villalbilla", "buniel", "celada", "sotopalacios", "cardenadijo", "sarracin"],
  kinds: { siege: "camp", burgos: "objective" },
  depots: { celada: ["Allies"], briviesca: ["France"] },   // where each side resupplies: ours (the allied road back to Valladolid; the French road from Vitoria)
  fortresses: { burgos: { side: "France", by: "mine", breach_days: 10, redig: 5, workers: 2000, stores: 90 } },   // see the header
  forces: [
    { name: "The siege corps (1st Division and Pack's Portuguese)", type: "foot", side: "Allies", men: 8000, tools: true, at: "siege" },
    { name: "The covering divisions (5th, 6th and 7th, Bradford's Portuguese)", type: "foot", side: "Allies", men: 14000, tools: true, at: "rubena" },
    { name: "Santocildes' Spaniards", type: "foot", side: "Allies", men: 11000, tools: true, at: "rubena" },
    { name: "Allied cavalry (Anson and Bock)", type: "mounted", side: "Allies", men: 2000, tools: false, at: "monasterio" },
    { name: "Burgos garrison (Dubreton)", type: "foot", side: "France", men: 2000, tools: true, at: "burgos" },
    { name: "Army of Portugal (Souham)", type: "foot", side: "France", men: 37000, tools: true, at: "briviesca" },
    { name: "Caffarelli's detachment (Army of the North)", type: "foot", side: "France", men: 8000, tools: true, at: "briviesca" },
    { name: "French cavalry", type: "mounted", side: "France", men: 5000, tools: false, at: "briviesca" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
