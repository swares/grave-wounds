// Builds data/maps/albuera-1811.yaml: the Albuera campaign of May 1811 on the travel map, at 1 km
// a hex, from Badajoz and Elvas to Santa Marta and Fuente del Maestre. Run from this folder after
// editing: npm ci && node make_albuera.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - towns and villages are placed at their modern coordinates (facts); a few force starts
//   (the siege lines, Blake's march) are only approximate;
// - rivers, brooks, woods and roads are drawn by hand through those places, after the line of
//   the modern rivers and roads, with the course of the campaign told in our own words. They
//   are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

import { P, RIVERS, STREAMS, FORDS, WOODS, HILLS, ROADS, TOWNS, VILLAGES } from "./albuera_base.mjs";   // the ground, shared with make_badajoz.mjs

const NAMES = { badajoz: "Badajoz", siege: "Siege lines", elvas: "Elvas", olivenza: "Olivenza", valverde: "Valverde de Leganés",
  albuera: "La Albuera", almendral: "Almendral", nogales: "Nogales", talavera: "Talavera la Real ford", lobon: "Lobón",
  solana: "Solana de los Barros", santamarta: "Santa Marta", villalba: "Villalba de los Barros", almendralejo: "Almendralejo",
  fuente: "Fuente del Maestre", torre: "Torre de Miguel Sesmero" };
const notes = {
  badajoz: "Held by a French garrison and besieged by Beresford in May 1811: the prize",
  siege: "Beresford's siege works; the siege was raised on 13 to 15 May as Soult came on",
  elvas: "The Portuguese fortress across the border: the allies' base",
  albuera: "Where Beresford and Blake joined and stood on 16 May; the battle, south of the village",
  santamarta: "The allied cavalry fell back from here before Soult's advance",
  almendral: "Blake's Spanish army came up by this road, joining late on 15 May (approximate)",
  fuente: "Soult's army on the road from Seville",
};

const map = buildCampaign({
  id: "albuera-1811", script: "make_albuera.mjs", title: "The Albuera campaign of May 1811, from Badajoz to Santa Marta",
  name: "Albuera campaign, 1811 (Badajoz to Santa Marta)",
  start_date: "1811-05-13", calendar: "gregorian", latitude: 39, climate: "mediterranean", climate_shift: -1,
  bounds: [-7.20, 38.95, -6.38, 38.48], midLat: 38.72, hexKm: 1,
  header: [
    "Towns and villages are at their modern places; the siege lines and Blake's start are only",
    "approximate; rivers, brooks, woods and roads are drawn by hand and approximate.",
    "",
    "What happened, briefly (dates Gregorian): in spring 1811 Marshal Beresford's British and",
    "Portuguese besieged French-held Badajoz. Marshal Soult marched up from Seville to relieve it.",
    "Beresford raised the siege and joined General Blake's Spanish army at La Albuera, across",
    "the road from the south. On 16 May Soult made a show against the village while his main",
    "force marched round through the olive woods onto the heights south of the allied line. The",
    "Spanish there held; a British brigade that came up beside them was ridden down by Polish",
    "lancers in a hailstorm; the British line that followed stood and traded volleys at close",
    "range until both sides were shot to pieces, and a late counter-attack drove the French off.",
    "Both armies lost about a third of their men engaged. Numbers below are round figures for play.",
  ],
  places: P, names: NAMES, notes, rivers: RIVERS, majorRivers: ["guadiana"], streams: STREAMS, fords: FORDS,
  woods: WOODS, hills: HILLS, roads: ROADS, towns: TOWNS, villages: VILLAGES,
  kinds: { siege: "camp", badajoz: "objective" },
  depots: { elvas: ["Allies"], badajoz: ["France"] },   // where each side resupplies (project doc "depots-research")
  tongues: { olivenza: ["portuguese", "spanish"], elvas: ["portuguese"] },   // the people's own tongues where they differ from the map's (project doc "tongues-research")
  forces: [
    { name: "Beresford's British", type: "foot", side: "Allies", men: 10000, tools: true, at: "siege" },
    { name: "Beresford's Portuguese", type: "foot", side: "Allies", men: 10000, tools: true, at: "siege" },
    { name: "Allied cavalry", type: "mounted", side: "Allies", men: 3000, tools: false, at: "santamarta" },
    { name: "Blake's Spanish army", type: "foot", side: "Allies", men: 14000, tools: true, at: "almendral" },
    { name: "Soult's army", type: "foot", side: "France", men: 19000, tools: true, at: "fuente" },
    { name: "French cavalry (Latour-Maubourg)", type: "mounted", side: "France", men: 4000, tools: false, at: "fuente" },
    { name: "Badajoz garrison", type: "foot", side: "France", men: 3000, tools: true, at: "badajoz" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
console.log(map.grid.map(r => r.join("")).join("\n"));
