// Builds data/maps/serbia-1915.yaml: the Serbian retreat of 1915, from the West Morava to the
// Adriatic, on the travel map at 5 km a hex: Kraljevo and Niš in the north, Durrës on the coast,
// Bitola and Lake Ohrid in the south. Run from this folder after editing: npm ci && node make_serbia1915.mjs
//
// Sources, all plain fact, and the drawing is ours (project doc "serbia1915-research"):
// - towns and villages are placed at their modern sites (facts); the passes, Vizier's Bridge,
//   Ljum Kula and Topolčani are only approximate;
// - the rivers, mountains, woods, marsh, lakes and roads are drawn by hand through those places,
//   after the line of the modern rivers and roads, and are approximate;
// - the forces' places and strengths on 5 November are our reading of the research: the
//   campaign-wide figures are sourced, how they split between armies mostly is not.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  kraljevo: [43.724, 20.688], krusevac: [43.581, 21.331], nis: [43.321, 21.896], prokuplje: [43.236, 21.590],
  kursumlija: [43.150, 21.267], raska: [43.292, 20.616], novipazar: [43.138, 20.516], leskovac: [42.998, 21.946],
  mitrovica: [42.883, 20.867], vucitrn: [42.822, 20.969], podujevo: [42.911, 21.193], pristina: [42.667, 21.167],
  gazimestan: [42.691, 21.124], lipljan: [42.522, 21.123], gnjilane: [42.465, 21.467], ferizaj: [42.367, 21.167],
  kacanik: [42.232, 21.259], vranje: [42.551, 21.900], kumanovo: [42.132, 21.714], skopje: [41.996, 21.432],
  prizren: [42.213, 20.739], djakovica: [42.383, 20.433], pec: [42.660, 20.292], patriarchate: [42.664, 20.266],
  decani: [42.547, 20.266], rozaje: [42.840, 20.160], cakor: [42.685, 20.054], plav: [42.600, 19.940],
  andrijevica: [42.730, 19.790], berane: [42.843, 19.873], podgorica: [42.441, 19.263], shkoder: [42.068, 19.512],
  kukes: [42.083, 20.417], kukesford: [42.17, 20.25], strugabridge: [41.21, 20.66], spas: [42.18, 20.27], viziers: [42.14, 20.47], puke: [42.050, 19.900],
  lezhe: [41.782, 19.644], shengjin: [41.814, 19.594], durres: [41.313, 19.446], debar: [41.517, 20.533],
  struga: [41.167, 20.667], ohrid: [41.117, 20.802], resen: [41.089, 21.012], elbasan: [41.111, 20.081],
  tetovo: [42.010, 20.971], gostivar: [41.796, 20.908], kicevo: [41.512, 20.959], veles: [41.716, 21.775],
  izvor: [41.555, 21.697], babuna: [41.45, 21.60], prilep: [41.344, 21.553], topolcani: [41.23, 21.43],
  bitola: [41.032, 21.335], mojkovac: [42.960, 19.580], bijelopolje: [43.038, 19.747], kolasin: [42.823, 19.520],
  // where forces stand that are not at a named place
  austrians: [43.78, 20.28], germans: [43.79, 21.05], sandzak: [43.15, 19.85], mountainbde: [43.60, 19.75],
  timok: [43.28, 21.72], bulgars1: [43.52, 21.82],
};

// ---------- rivers (crossed where a road bridges them, or at the named bridges), brooks ----------
const RIVERS = {
  westMorava: [[43.80, 20.42], [43.74, 20.58], "kraljevo", [43.65, 20.95], [43.61, 21.20], [43.67, 21.42], [43.80, 21.45]],
  southMorava: [[42.40, 21.95], [42.70, 21.93], [43.05, 21.90], [43.37, 21.80], [43.50, 21.66], [43.67, 21.42]],
  ibar: [[42.80, 20.15], [42.88, 20.45], [42.90, 20.72], [42.893, 20.85], [43.05, 20.78], [43.20, 20.66], [43.29, 20.63], [43.50, 20.63], [43.71, 20.68]],
  sitnica: [[42.52, 21.08], [42.70, 21.05], [42.82, 20.94], [42.89, 20.86]],
  whiteDrin: [[42.75, 20.30], [42.62, 20.40], [42.40, 20.55], [42.25, 20.66], [42.15, 20.50], [42.13, 20.34]],
  blackDrin: [[41.18, 20.69], [41.35, 20.55], [41.52, 20.44], [41.75, 20.43], [41.95, 20.36], [42.13, 20.34]],
  drin: [[42.13, 20.34], [42.20, 20.15], [42.25, 20.03], [42.15, 19.90], [42.10, 19.83], [42.01, 19.63]],
  buna: [[42.01, 19.63], [42.04, 19.53], [41.95, 19.45], [41.87, 19.37]],   // the lower Drin and the Buna, by Shkodër
  vardar: [[41.80, 20.88], [41.95, 21.20], [42.00, 21.40], [41.85, 21.60], [41.72, 21.79], [41.55, 21.95]],
  lepenac: [[42.33, 21.17], [42.22, 21.24], [42.10, 21.33], [42.00, 21.42]],
  crna: [[41.00, 21.40], [41.10, 21.44], [41.25, 21.68], [41.40, 21.95]],
  shkumbin: [[41.00, 20.47], [41.08, 20.30], [41.10, 20.10], [41.08, 19.85], [41.03, 19.60], [41.00, 19.48]],
  tara: [[42.78, 19.48], [42.823, 19.520], [42.90, 19.56], [42.96, 19.575], [43.03, 19.50], [43.12, 19.38], [43.20, 19.25]],   // the upper Tara, past Kolašin and Mojkovac
  lim: [[42.60, 19.93], [42.73, 19.80], [42.84, 19.86], [43.04, 19.75], [43.30, 19.60], [43.50, 19.45]],
};
const STREAMS = [
  [[42.66, 20.29], [42.60, 20.35], [42.50, 20.45]],     // the Pećka Bistrica
  [[43.15, 21.27], [43.24, 21.45], [43.30, 21.65]],     // the Toplica, Kuršumlija to Prokuplje
];
const BRIDGES = ["viziers", "strugabridge"];
const FORDS = ["kukesford"];

// ---------- lakes the land data counts as land: Skadar (its east end), Ohrid (its north), Prespa (its tip) ----------
const WATER = [
  [[42.37, 19.10], [42.30, 19.30], [42.20, 19.42], [42.10, 19.48], [42.13, 19.36], [42.20, 19.22], [42.30, 19.05]],
  [[41.17, 20.71], [41.14, 20.79], [41.05, 20.80], [40.95, 20.76], [40.92, 20.70], [41.00, 20.64], [41.10, 20.66]],
  [[41.06, 21.02], [41.00, 21.08], [40.98, 20.96]],
];

// ---------- mountains, hills, woods and marsh (centre, radius km) ----------
const MOUNTAINS = [
  [[42.50, 19.92], 16], [[42.42, 20.10], 14], [[42.66, 20.12], 10], [[42.35, 19.75], 14],   // the Prokletije, Plav to Đakovica
  [[42.05, 20.85], 14], [[42.12, 21.00], 9],                                                 // the Šar
  [[43.27, 20.82], 12],                                                                      // Kopaonik
  [[42.86, 20.35], 10],                                                                      // Mokra Gora, between Peć and Rožaje
  [[41.80, 20.57], 11],                                                                      // Korab, above Debar
  [[42.00, 20.05], 14], [[41.80, 20.12], 14], [[41.55, 20.20], 12],                          // the north Albanian highlands
  [[42.76, 20.00], 11], [[42.70, 19.72], 10], [[42.55, 19.55], 12], [[42.86, 20.15], 7],   // Hajla, the Komovi and the Kuči mountains
  [[42.30, 20.00], 10], [[42.20, 19.85], 10], [[42.14, 20.18], 7], [[41.95, 20.25], 8],     // over the Drin to the Prokletije: no way for wheels
  [[41.35, 20.33], 12], [[41.15, 20.42], 10], [[41.03, 20.55], 7],                            // Jablanica, between the Black Drin and the Shkumbin
  [[42.85, 19.50], 16], [[43.10, 19.40], 14],                                                // the Montenegrin mountains
  [[41.55, 21.40], 10],                                                                      // Jakupica, west of the Babuna
  [[41.40, 20.88], 10],                                                                      // between Kičevo and Ohrid
  [[41.00, 21.20], 7],                                                                       // Pelister, above Bitola
];
// The country is hill and mountain (the base); the farmed plains and valleys are cleared from it.
const FARMS = [
  [[42.65, 21.10], 20], [[42.80, 20.95], 10], [[42.45, 20.45], 16], [[42.30, 20.60], 8],             // the Kosovo plain and Metohija
  [[43.64, 21.05], 10], [[43.60, 21.35], 9], [[43.40, 21.70], 10], [[43.25, 21.55], 7], [[43.70, 20.75], 6],   // the Morava valleys
  [[42.80, 21.90], 8], [[42.20, 21.75], 10], [[42.00, 21.45], 10], [[41.90, 20.95], 9], [[41.80, 21.92], 8],   // Vranje, Kumanovo, Skopje, Polog, Ovče Pole
  [[41.22, 21.45], 13], [[41.05, 21.35], 9],                                                          // Pelagonia, Prilep to Bitola
  [[41.45, 19.60], 14], [[41.20, 19.62], 11], [[41.95, 19.55], 8], [[41.75, 19.65], 6], [[42.40, 19.30], 9], [[41.15, 19.90], 7],   // the coastal plains, Zeta and Elbasan
];
const HILLS = [[[42.80, 21.40], 10], [[43.05, 21.05], 8]];
const WOODS = [[[43.42, 20.40], 14], [[42.97, 20.20], 9], [[41.62, 20.30], 10], [[43.52, 21.10], 9], [[42.95, 21.55], 9], [[41.95, 19.75], 8]];
const MARSH = [[[42.17, 19.33], 7], [[41.88, 19.45], 5], [[41.42, 19.55], 6]];

// ---------- roads and railways (through places, in order). The tracks over the Albanian and
// Montenegrin mountains were for mules and men on foot: they are left off, so wagons and guns
// cannot cross, as the Serbs found. ----------
const ROADS = [
  ["kraljevo", [43.65, 20.95], "krusevac", [43.45, 21.58], "nis"],                         // the West Morava valley
  ["kraljevo", [43.50, 20.63], "raska", "novipazar"], ["raska", [43.10, 20.72], "mitrovica"],   // the Ibar valley
  ["krusevac", [43.32, 21.28], "kursumlija", "podujevo", "pristina"],                       // over the Kopaonik's eastern end
  ["nis", "prokuplje", "kursumlija"], ["nis", "leskovac", "vranje"],
  ["mitrovica", "vucitrn", "gazimestan", "pristina", "lipljan", "ferizaj", "kacanik", "skopje"],   // the road and railway down the Kosovo plain
  ["vranje", [42.35, 21.80], "kumanovo", "skopje"], ["pristina", "gnjilane", [42.30, 21.62], "kumanovo"],
  ["lipljan", [42.38, 20.88], "prizren"], ["ferizaj", [42.28, 20.95], "prizren"],
  ["mitrovica", [42.75, 20.60], "pec"], ["pec", "decani", "djakovica", "prizren"], ["novipazar", "rozaje"],
  ["prizren", "tetovo"], ["skopje", "tetovo", "gostivar", "kicevo", "ohrid", "struga"],
  ["skopje", [41.85, 21.60], "veles", "izvor", "babuna", "prilep", "topolcani", "bitola"],   // the road over the Babuna
  ["bitola", "resen", "ohrid"], ["elbasan", [41.20, 19.80], "durres"],
  ["podgorica", [42.25, 19.40], "shkoder"], ["shkoder", [41.95, 19.56], "lezhe", [41.55, 19.55], "durres"], ["lezhe", "shengjin"],
  ["berane", "andrijevica"], ["berane", "bijelopolje", [43.00, 19.68], "mojkovac", "kolasin"],   // up the Lim and over to the Tara
];

const TOWNS = ["kraljevo", "krusevac", "nis", "leskovac", "mitrovica", "pristina", "skopje", "prizren", "pec", "podgorica", "shkoder",
  "durres", "bitola", "prilep", "elbasan", "veles", "ohrid"];
const VILLAGES = ["prokuplje", "kursumlija", "raska", "novipazar", "vucitrn", "podujevo", "lipljan", "gnjilane", "ferizaj", "kacanik",
  "vranje", "kumanovo", "djakovica", "rozaje", "plav", "andrijevica", "berane", "kukes", "spas", "puke", "lezhe", "shengjin", "debar",
  "struga", "resen", "tetovo", "gostivar", "kicevo", "izvor", "topolcani", "mojkovac", "bijelopolje", "kolasin"];

const NAMES = { kraljevo: "Kraljevo", krusevac: "Kruševac", nis: "Niš", prokuplje: "Prokuplje", kursumlija: "Kuršumlija",
  raska: "Raška", novipazar: "Novi Pazar", leskovac: "Leskovac", mitrovica: "Mitrovica", vucitrn: "Vučitrn", podujevo: "Podujevo",
  pristina: "Priština", gazimestan: "Gazimestan (the field of Kosovo)", lipljan: "Lipljan", gnjilane: "Gnjilane", ferizaj: "Ferizaj",
  kacanik: "Kačanik gorge", vranje: "Vranje", kumanovo: "Kumanovo", skopje: "Skopje", prizren: "Prizren", djakovica: "Đakovica",
  pec: "Peć", patriarchate: "Patriarchate of Peć", decani: "Visoki Dečani", rozaje: "Rožaje", cakor: "Čakor pass", plav: "Plav",
  andrijevica: "Andrijevica", berane: "Berane", podgorica: "Podgorica", shkoder: "Shkodër (Scutari)", kukes: "Kukës",
  spas: "Spas", viziers: "Vizier's Bridge", kukesford: "Drin crossing below Kukës", strugabridge: "Struga bridge", puke: "Pukë", lezhe: "Lezhë (Alessio)", shengjin: "Shëngjin (San Giovanni di Medua)",
  durres: "Durrës (Durazzo)", debar: "Debar", struga: "Struga", ohrid: "Ohrid", resen: "Resen", elbasan: "Elbasan", tetovo: "Tetovo",
  gostivar: "Gostivar", kicevo: "Kičevo", veles: "Veles", izvor: "Izvor", babuna: "Babuna pass", prilep: "Prilep",
  topolcani: "Topolčani", bitola: "Bitola (Monastir)", mojkovac: "Mojkovac", bijelopolje: "Bijelo Polje", kolasin: "Kolašin" };
const notes = {
  kraljevo: "The Supreme Command's seat until early November; the West Morava valley road runs east from here",
  nis: "Taken by the Bulgarian 1st Army on 5 November",
  mitrovica: "Fell on 23 November, with Priština",
  pristina: "Fell on 23 November; the Serbian armies gathered on the Kosovo plain around it, with refugees",
  gazimestan: "The field of the battle of 1389, where the Serbian armies made their last stand in Kosovo",
  kacanik: "The gorge from Kosovo down to Skopje, taken by the Bulgarians on 26 October; Serbian attacks towards it failed in November",
  skopje: "Fell to the Bulgarians on 22 October, cutting the railway to Salonika",
  prizren: "The King, the government and the Supreme Command left from here on 24-26 November; taken on 29 November",
  pec: "Where the commanders met in council (29 November to 2 December); the northern column set out from here; taken on 7 December",
  cakor: "The pass on the northern column's road into Montenegro, 1,844 m",
  rozaje: "On the way north-west into Montenegro",
  kukes: "Where the White and Black Drin meet; the central and southern columns split near here (Ljum Kula)",
  kukesford: "Where the central column crossed the Drin, on foot and with pack animals (approximate)",
  strugabridge: "The bridge over the Black Drin where it leaves Lake Ohrid, on the southern column's way west (approximate)",
  viziers: "An old stone bridge on the central column's way from Prizren into Albania (approximate)",
  shkoder: "Where the northern and central columns came out; about 89,000 soldiers reached it",
  shengjin: "The little port where some of the army and the refugees were taken off by ship",
  durres: "The main port of the evacuation: about 95,000 soldiers were taken off here",
  elbasan: "The southern column passed here on its way to Durrës; the Bulgarians took it on 29 January",
  babuna: "The pass where about 5,000 men of the 2nd and 14th Regiments held the road to Prilep for a week and more (approximate)",
  izvor: "Where the Bulgarian attack was driven back to, in the first days of November",
  prilep: "Occupied by the Bulgarians on 17 November",
  topolcani: "Where Flora Sandes's company fought a rearguard in the snow, by a river and a mined bridge (approximate)",
  mojkovac: "Where the Montenegrin Sandžak army beat off the Austro-Hungarians on 6-7 January 1916, covering the Serbian retreat",
  bijelopolje: "Reached by the Austro-Hungarian 62nd Division on 16 December",
  debar: "Taken by the Bulgarians about 8-9 December",
  ohrid: "Taken by the Bulgarians about 8-9 December",
};

// Serbian where the Serbs are: the Morava valleys (Muslims left after 1878) and highland Montenegro.
// Macedonian Slavic counts as the game's Bulgarian (period sources count them so); Ladino as Spanish.
const SR = ["serbian"];
const map = buildCampaign({
  id: "serbia-1915", script: "make_serbia1915.mjs", title: "The Serbian retreat, November 1915 to January 1916, from Kraljevo to the Adriatic",
  name: "Serbia, 1915 (the great retreat)",
  start_date: "1915-11-05", calendar: "gregorian", latitude: 42, climate: "balkan_highland", climate_shift: 0,
  bounds: [19.20, 43.80, 21.95, 41.00], midLat: 42.4, hexKm: 5,
  header: [
    "Towns and villages are at their modern places; the passes, Vizier's Bridge and Topolčani are",
    "only approximate; the rivers, mountains, woods, lakes and roads are drawn by hand and approximate.",
    "The tracks over the Albanian and Montenegrin mountains are not roads: men and pack animals",
    "cross the mountains on foot, wagons and guns cannot.",
    "",
    "What happened, briefly: in October 1915 the Austro-Hungarian 3rd Army and the German 11th",
    "Army crossed the Danube and the Sava and took Belgrade, and Bulgaria came in from the east,",
    "cutting the railway to Salonika at Skopje. By early November the Serbian armies were falling",
    "back up the West Morava and the Ibar towards Kosovo, while in Macedonia two regiments held the",
    "Babuna pass against the Bulgarians for a week and more. Attacks to break through to the Allies",
    "at Salonika failed, and on 23 November Mitrovica and Priština fell. On 25 November the retreat",
    "was ordered over the mountains to the Adriatic, by three columns: from Peć through Montenegro",
    "to Shkodër, from Prizren through Albania to Shkodër, and from Prizren by Debar and Elbasan to",
    "Durrës. In snow, with little food and Albanian bands about, the army and its refugees and",
    "prisoners crossed in December; perhaps 140,000 to 155,000 soldiers came out, and Allied ships",
    "took them to Corfu. Numbers below are round figures for play; the positions on 5 November are",
    "our reading of the research, which has few sourced figures for single armies.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["drin", "vardar"], streams: STREAMS, bridges: BRIDGES, fords: FORDS,
  base: "h", farms: FARMS, water: WATER, woods: WOODS, marsh: MARSH, hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { pristina: "objective", babuna: "objective", mojkovac: "objective", durres: "camp", shkoder: "camp" },
  // where each side resupplies (project docs "depots-research" and "serbia1915-research"): the
  // Serbs from their stores in Kosovo and the Montenegrins at Podgorica, with a little brought in
  // by sea at the coast; the Bulgarians from Niš and Skopje.
  depots: { pristina: ["Serbia and Montenegro"], prizren: ["Serbia and Montenegro"], podgorica: ["Serbia and Montenegro"],
    shkoder: ["Serbia and Montenegro"], durres: ["Serbia and Montenegro"], nis: ["Central Powers"], skopje: ["Central Powers"] },
  tongues: {
    kraljevo: SR, krusevac: SR, nis: SR, prokuplje: SR, kursumlija: SR, raska: SR, leskovac: SR, vranje: SR, andrijevica: SR, berane: SR,
    novipazar: ["serbian", "albanian"], rozaje: ["serbian", "albanian"], mitrovica: ["serbian", "albanian"], podgorica: ["serbian", "albanian"],
    pristina: ["albanian", "serbian", "turkish"], prizren: ["albanian", "serbian", "turkish"], pec: ["albanian", "serbian"],
    vucitrn: ["albanian", "serbian"], ferizaj: ["albanian", "serbian"], gnjilane: ["albanian", "serbian"], plav: ["albanian", "serbian"],
    shkoder: ["albanian", "serbian"], djakovica: ["albanian"],
    skopje: ["bulgarian", "turkish", "albanian"], kumanovo: ["bulgarian", "turkish", "albanian"], veles: ["bulgarian", "turkish"],
    prilep: ["bulgarian", "turkish"], bitola: ["turkish", "bulgarian", "aromanian", "spanish", "albanian"],
    ohrid: ["bulgarian", "turkish", "albanian"], struga: ["bulgarian", "turkish", "albanian"], debar: ["albanian", "bulgarian"],
    tetovo: ["albanian", "bulgarian", "turkish"], gostivar: ["albanian", "bulgarian", "turkish"], kicevo: ["bulgarian", "albanian"],
    resen: ["bulgarian", "turkish"], izvor: ["bulgarian"], babuna: ["bulgarian"], topolcani: ["bulgarian"],
    mojkovac: SR, bijelopolje: SR, kolasin: SR,
  },   // the people's own tongues where they differ from the map's (project doc "tongues-research")
  forces: [
    { name: "Serbian 1st Army (Mišić)", type: "foot", side: "Serbia and Montenegro", men: 40000, tools: true, at: "kraljevo" },
    { name: "Serbian 3rd Army (Šturm)", type: "foot", side: "Serbia and Montenegro", men: 35000, tools: true, at: "krusevac" },
    { name: "Serbian 2nd Army (Stepanović)", type: "foot", side: "Serbia and Montenegro", men: 50000, tools: true, at: "prokuplje" },
    { name: "Timok group", type: "foot", side: "Serbia and Montenegro", men: 20000, tools: true, at: "timok" },
    { name: "Užice group", type: "foot", side: "Serbia and Montenegro", men: 15000, tools: true, at: "novipazar" },
    { name: "Supreme Command, the King and the government", type: "wagons", side: "Serbia and Montenegro", men: 2000, tools: false, at: "raska" },
    { name: "Serbian troops at the Kačanik gorge", type: "foot", side: "Serbia and Montenegro", men: 15000, tools: true, at: "ferizaj" },
    { name: "Macedonian group (Vasić): 2nd and 14th Regiments", type: "foot", side: "Serbia and Montenegro", men: 5000, tools: true, at: "babuna" },
    { name: "Montenegrin Sandžak army (Vukotić)", type: "foot", side: "Serbia and Montenegro", men: 20000, tools: true, at: "sandzak" },
    { name: "Montenegrin troops at Andrijevica", type: "foot", side: "Serbia and Montenegro", men: 8000, tools: true, at: "andrijevica" },
    { name: "Austro-Hungarian 3rd Army (Kövess)", type: "foot", side: "Central Powers", men: 40000, tools: true, at: "austrians" },
    { name: "Austro-Hungarian mountain brigades", type: "foot", side: "Central Powers", men: 10000, tools: true, at: "mountainbde" },
    { name: "German 11th Army (Gallwitz)", type: "foot", side: "Central Powers", men: 40000, tools: true, at: "germans" },
    { name: "Bulgarian 1st Army (Boyadzhiev): 9th Division", type: "foot", side: "Central Powers", men: 18000, tools: true, at: "nis" },
    { name: "Bulgarian 1st Army: 1st and 6th Divisions", type: "foot", side: "Central Powers", men: 36000, tools: true, at: "bulgars1" },
    { name: "Bulgarian 2nd Army (Todorov): 3rd Division", type: "foot", side: "Central Powers", men: 18000, tools: true, at: "kacanik" },
    { name: "Bulgarian 2nd Army: 7th Division", type: "foot", side: "Central Powers", men: 18000, tools: true, at: "vranje" },
    { name: "Bulgarian Cavalry Division", type: "mounted", side: "Central Powers", men: 4000, tools: false, at: "skopje" },
    { name: "Bulgarian division at Izvor", type: "foot", side: "Central Powers", men: 18000, tools: true, at: "izvor" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
