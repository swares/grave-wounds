// Builds data/maps/chosin-1950.yaml: the Chosin Reservoir campaign, 27 November to 11 December
// 1950, on the travel map at 1 km a hex, from Yudam-ni and the reservoir down the one road to
// Hamhung and the port of Hungnam. Run from this folder after editing: npm ci && node make_chosin.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the US Navy's and the US Army's and Marine Corps' accounts (works of the US government) and
//   public summaries for the facts: the 1st Marine Division at Yudam-ni west of the reservoir and
//   Hagaru-ri at its south end, with an Army regimental combat team east of it, was attacked by
//   the Chinese 9th Army Group from the night of 27 November in record cold; Fox Company, 7th
//   Marines held Toktong Pass between Yudam-ni and Hagaru-ri for five days; the division fought
//   its way down the road through Koto-ri, Funchilin Pass and Chinhung-ni to Hamhung and Hungnam,
//   from where X Corps was taken off by sea;
// - the towns and villages at their modern positions, rounded; Toktong Pass, Funchilin Pass and
//   the treadway bridge placed after the accounts and approximate; the reservoir's shore, the
//   mountains and the road drawn by hand. They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

// ---------- places (lat, lon) ----------
const P = {
  yudam: [40.483, 127.117], hagaru: [40.383, 127.250], toktong: [40.430, 127.185], kotori: [40.283, 127.300], funchilin: [40.235, 127.335],
  bridge: [40.225, 127.345], chinhung: [40.183, 127.367], hamhung: [39.920, 127.540], hungnam: [39.835, 127.620], sinhung: [40.470, 127.310],
  northwest: [40.560, 127.080], toktongpeak: [40.455, 127.200], east: [40.430, 127.420], west: [40.320, 127.150],   // where the Chinese armies come in (not places)
};

// ---------- the reservoir (hand-drawn shore) and the rivers ----------
const RESERVOIR = [[40.395, 127.245], [40.430, 127.230], [40.480, 127.215], [40.540, 127.205], [40.600, 127.225], [40.620, 127.260], [40.580, 127.285],
  [40.520, 127.275], [40.470, 127.300], [40.440, 127.300], [40.410, 127.280], [40.392, 127.262]];
const RIVERS = {};
const STREAMS = [[[40.290, 127.305], [40.240, 127.335], [40.190, 127.365], [40.080, 127.430], [39.960, 127.520], [39.880, 127.590]]];   // the Changjin's gorge down to the plain
const BRIDGES = ["bridge"];

// ---------- mountains everywhere above the plain; farmland in the valleys and on the plain ----------
const FARMS = [[P.yudam, 1.5], [P.hagaru, 2.0], [P.kotori, 1.5], [P.chinhung, 1.2], [[39.950, 127.520], 8.0], [P.hungnam, 4.0], [P.sinhung, 1.2]];
const HILLS = [[[40.050, 127.460], 5.0], [[40.120, 127.400], 4.0]];
const MOUNTAINS = [];

// ---------- the one road (and the narrow-gauge railroad beside it below Koto-ri) ----------
const ROADS = [
  ["northwest", "yudam", "toktong", "hagaru", "kotori", "funchilin", "bridge", "chinhung", [40.080, 127.430], "hamhung", "hungnam"],
  ["hagaru", [40.420, 127.290], "sinhung", "east"], ["west", "kotori"],
];

const NAMES = { yudam: "Yudam-ni", hagaru: "Hagaru-ri", toktong: "Toktong Pass (Fox Hill)", kotori: "Koto-ri", funchilin: "Funchilin Pass", bridge: "The treadway bridge",
  chinhung: "Chinhung-ni", hamhung: "Hamhung", hungnam: "Hungnam", sinhung: "Sinhung-ni (east of the reservoir)" };
const notes = {
  toktong: "Fox Company, 7th Marines held the hill over the pass from 27 November to 2 December 1950 (approximate)",
  hagaru: "The division's base at the south end of the reservoir, with its airstrip: the wounded were flown out from here",
  bridge: "The Chinese blew the bridge over the gorge; a treadway bridge was dropped by air on 7 December and the division crossed (approximate)",
  sinhung: "The Army's regimental combat team (Task Force Faith) was cut off and destroyed east of the reservoir (approximate)",
  hungnam: "X Corps was taken off by sea from here, 11-24 December",
};

const map = buildCampaign({
  id: "chosin-1950", script: "make_chosin.mjs", title: "The Chosin Reservoir, November-December 1950",
  name: "Chosin Reservoir, 1950 (Yudam-ni to Hungnam)",
  start_date: "1950-11-27", calendar: "gregorian", latitude: 40, climate: "changjin", climate_shift: -2, base: "M",
  water: [RESERVOIR],
  bounds: [127.050, 40.640, 127.680, 39.800], midLat: 40.22, hexKm: 1,
  header: [
    "The towns and villages are at their modern positions, rounded; Toktong Pass, Funchilin Pass",
    "and the bridge are placed after the accounts and approximate; the reservoir's shore, the",
    "mountains and the road are drawn by hand. Above the coastal plain it is all steep mountains,",
    "with farmland in the valleys; one road leads down to the sea. The winter of 1950 was among",
    "the coldest on record (a colder climate than central Korea's, and colder still that year).",
    "",
    "What happened, briefly: in late November 1950 the 1st Marine Division was strung out along the",
    "road to the Chosin Reservoir, two regiments at Yudam-ni, the base at Hagaru-ri, an Army",
    "regimental combat team east of the reservoir. On the night of 27 November the Chinese 9th",
    "Army Group, some 120,000 men, attacked all of them at once, in temperatures of -20 F and",
    "lower. The Marines fought back from Yudam-ni through Toktong Pass, where Fox Company held its",
    "hill for five days, to Hagaru-ri, and then down the road through Koto-ri and over the gorge at",
    "Funchilin Pass on a bridge dropped from the air, to Hamhung and the sea. The Army's force east",
    "of the reservoir was destroyed. Frostbite took as many men as the Chinese. Numbers below are",
    "round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: [], streams: STREAMS, bridges: BRIDGES, fords: [],
  farms: FARMS, woods: [], hills: HILLS, mountains: MOUNTAINS, roads: ROADS, towns: ["hamhung", "hungnam"], villages: ["yudam", "hagaru", "kotori", "chinhung", "sinhung"],
  kinds: { hagaru: "camp", toktong: "objective", hungnam: "objective" },
  forces: [
    { name: "5th and 7th Marines (Yudam-ni)", type: "foot", side: "United Nations", men: 8000, tools: true, at: "yudam" },
    { name: "Fox Company, 7th Marines", type: "foot", side: "United Nations", men: 240, tools: true, at: "toktong" },
    { name: "Hagaru-ri garrison (3rd Battalion, 1st Marines and others)", type: "foot", side: "United Nations", men: 3000, tools: true, at: "hagaru" },
    { name: "1st Marines and 41 Commando (Koto-ri)", type: "foot", side: "United Nations", men: 4000, tools: true, at: "kotori" },
    { name: "Regimental Combat Team 31 (east of the reservoir)", type: "foot", side: "United Nations", men: 2500, tools: true, at: "sinhung" },
    { name: "Chinese 79th and 89th Divisions (Yudam-ni)", type: "foot", side: "Chinese", men: 18000, tools: true, at: "northwest" },
    { name: "Chinese 59th Division (Toktong Pass)", type: "foot", side: "Chinese", men: 8000, tools: true, at: "toktongpeak" },
    { name: "Chinese 80th Division (east of the reservoir)", type: "foot", side: "Chinese", men: 9000, tools: true, at: "east" },
    { name: "Chinese 58th and 60th Divisions (Hagaru-ri and the road south)", type: "foot", side: "Chinese", men: 15000, tools: true, at: "west" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
