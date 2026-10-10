// Builds data/maps/lutzen-1632.yaml: the Lützen campaign of November 1632 on the travel map, at
// 1 km a hex, from Naumburg on the Saale to Leipzig. Run from this folder after editing:
// npm ci && node make_lutzen.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - towns and villages are placed at their modern coordinates (facts);
// - rivers, brooks, woods and roads are drawn by hand through those places, after the line of
//   the modern rivers and the old high road from Naumburg by Weißenfels and Lützen to Leipzig,
//   with the course of the campaign told in our own words. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  naumburg: [51.153, 11.810], weissenfels: [51.200, 11.969], rippach: [51.226, 12.074], lutzen: [51.257, 12.140],
  markranstadt: [51.302, 12.220], leipzig: [51.340, 12.375], halle: [51.483, 11.970], merseburg: [51.355, 11.993],
  durrenberg: [51.296, 12.066], korbetha: [51.262, 12.023], schkeuditz: [51.396, 12.222], pegau: [51.168, 12.252],
  zwenkau: [51.218, 12.326], poserna: [51.215, 12.090], kotzschau: [51.312, 12.117], hohenmolsen: [51.159, 12.098],
};

// ---------- rivers (impassable but at a bridge, a ford or a town) and brooks ----------
const RIVERS = {
  saale: [[51.115, 11.760], "naumburg", [51.180, 11.880], "weissenfels", [51.235, 11.995], "korbetha", "durrenberg", [51.330, 12.030],
          "merseburg", [51.420, 11.975], "halle", [51.505, 11.950]],
  elster: [[51.115, 12.220], "pegau", "zwenkau", [51.300, 12.350], "leipzig", [51.370, 12.300], "schkeuditz", [51.405, 12.100], [51.430, 11.990]],
  pleisse: [[51.115, 12.430], [51.250, 12.400], "leipzig"],
};
const STREAMS = [
  [[51.165, 12.130], "poserna", "rippach", [51.245, 12.040], "korbetha"],                       // the Rippach
  ["zwenkau", [51.240, 12.230], [51.250, 12.160], [51.268, 12.090], "durrenberg"],             // the Floßgraben, a timber canal
];

// ---------- woods and marsh (centre, radius km) ----------
const WOODS = [[[51.360, 12.330], 3], [[51.300, 12.360], 2], [[51.500, 11.900], 2.5], [[51.180, 11.900], 2], [[51.130, 12.000], 2.5]];
const MARSH = [[[51.385, 12.160], 2.5], [[51.420, 12.040], 1.5]];

// ---------- roads (through places, in order) ----------
const ROADS = [
  ["naumburg", "weissenfels", "rippach", "lutzen", "markranstadt", "leipzig"],   // the high road to Leipzig
  ["weissenfels", "durrenberg", "merseburg", "halle"], ["halle", "schkeuditz", "leipzig"], ["merseburg", "kotzschau", "lutzen"],
  ["leipzig", "zwenkau", "pegau"], ["pegau", "hohenmolsen", "weissenfels"], ["lutzen", "poserna", "hohenmolsen"],
];

const TOWNS = ["naumburg", "weissenfels", "lutzen", "leipzig", "halle", "merseburg", "pegau", "schkeuditz"];
const VILLAGES = ["markranstadt", "durrenberg", "korbetha", "zwenkau", "poserna", "kotzschau", "hohenmolsen", "rippach"];

const NAMES = { naumburg: "Naumburg", weissenfels: "Weißenfels", rippach: "Rippach", lutzen: "Lützen", markranstadt: "Markranstädt",
  leipzig: "Leipzig", halle: "Halle", merseburg: "Merseburg", durrenberg: "Dürrenberg", korbetha: "Großkorbetha", schkeuditz: "Schkeuditz",
  pegau: "Pegau", zwenkau: "Zwenkau", poserna: "Poserna", kotzschau: "Kötzschau", hohenmolsen: "Hohenmölsen" };
const notes = {
  naumburg: "The Swedish army's camp; it marched out on 15 November",
  rippach: "An Imperial rearguard held the crossing of the Rippach brook on 15 November, until dark",
  lutzen: "Wallenstein stood north of the high road here on 16 November; the battle, in fog, where Gustavus Adolphus fell",
  halle: "Where Pappenheim had gone; called back in the night, his horse reached the field about midday",
  leipzig: "Where the Imperial army fell back after the battle",
};

const map = buildCampaign({
  id: "lutzen-1632", script: "make_lutzen.mjs", title: "The Lützen campaign of November 1632, from Naumburg to Leipzig",
  name: "Lützen campaign, 1632 (Naumburg to Leipzig)",
  start_date: "1632-11-15", calendar: "gregorian", latitude: 51, climate: "continental", climate_shift: -0.5,
  bounds: [11.75, 51.51, 12.45, 51.11], midLat: 51.31, hexKm: 1,
  header: [
    "Towns and villages are at their modern places; rivers, brooks, woods and roads are drawn by",
    "hand through them and are approximate.",
    "",
    "What happened, briefly (dates Gregorian; the Swedes' own calendar was ten days behind): in",
    "November 1632 Wallenstein, thinking the campaigning season over, spread his army into winter",
    "quarters and sent Pappenheim with a strong corps to Halle. Gustavus Adolphus, camped at",
    "Naumburg, marched out on 15 November to catch the Imperial army apart, but was held at the",
    "Rippach crossing until dark. Wallenstein drew up north of the high road at Lützen, lined its",
    "ditches with musketeers, set guns on the windmill hill by the town, and called Pappenheim",
    "back. The battle on 16 November was fought in fog that came and went. Gustavus Adolphus was",
    "killed in a cavalry fight; Pappenheim arrived at midday and was mortally wounded; by evening",
    "the Swedes had taken the windmill battery, and the Imperial army fell back to Leipzig in the",
    "night. Numbers are disputed; those below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["saale", "elster"], streams: STREAMS,
  woods: WOODS, marsh: MARSH, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { naumburg: "camp", lutzen: "objective" },
  forces: [
    { name: "Swedish foot", type: "foot", side: "Sweden", men: 12000, tools: true, at: "naumburg" },
    { name: "Swedish horse", type: "mounted", side: "Sweden", men: 6000, tools: false, at: "naumburg" },
    { name: "Wallenstein's army", type: "foot", side: "Empire", men: 12000, tools: true, at: "lutzen" },
    { name: "Imperial horse", type: "mounted", side: "Empire", men: 4000, tools: false, at: "lutzen" },
    { name: "Imperial rearguard at the Rippach", type: "mounted", side: "Empire", men: 500, tools: false, at: "rippach" },
    { name: "Pappenheim's horse", type: "mounted", side: "Empire", men: 3000, tools: false, at: "halle" },
    { name: "Pappenheim's foot", type: "foot", side: "Empire", men: 3000, tools: true, at: "halle" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
