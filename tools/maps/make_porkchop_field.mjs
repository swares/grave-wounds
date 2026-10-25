// Builds data/fields/porkchop-1953.yaml: Pork Chop Hill on the night of 16-17 April 1953, on the
// field map at 10 m a hex. Run from this folder after editing: node make_porkchop_field.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's accounts
// (Hermes, Truce Tent and Fighting Front; Marshall's study) as summarised publicly. Pork Chop
// was a hill of about 300 m, its crest ringed with sandbagged bunkers joined by trenches, held by
// E Company, 31st Infantry, with Hill 200 to the south-east and the main line behind; at about
// 23:00 on 16 April a Chinese battalion came up it from the north and west in the dark and took
// most of it; K Company, 135 strong, and L Company counterattacked from the south before dawn,
// L Company's men pinned in the trenches of Hill 200 for a time; the artillery fired "flash" fire
// round the outposts all night. The hill, the trenches, the bunkers, the valley and Hill 200 are
// drawn by hand to that shape, not traced from any map, and approximate; the deployment is the
// Chinese attack, in our own words, with round numbers for play.
import { N, S, patch, speckle, groundGrid, unit, writeField, at } from "./field_lib.mjs";

const COLS = 160, ROWS = 130;                 // 1600 m east to west, about 1130 m north to south
const TOP = [76, 56], H200 = [124, 96];
const cube = ([c, r]) => { const q = c - (r - (r & 1)) / 2; return [q, r, -q - r] };
const hdist = (a, b) => { const x = cube(a), y = cube(b); return Math.max(Math.abs(x[0] - y[0]), Math.abs(x[1] - y[1]), Math.abs(x[2] - y[2])) };
function kind(c, r){
  if (patch(c, r, { cx: TOP[0], cy: TOP[1], rx: 22, ry: 16, a: 0.5, b: 1.2 })) return speckle(c, r, 3) ? "r" : "h";   // Pork Chop: bare, cratered
  if (patch(c, r, { cx: H200[0], cy: H200[1], rx: 12, ry: 9, a: 1.3, b: 0.2 })) return speckle(c, r, 3) ? "r" : "h";   // Hill 200
  if (r > 116) return speckle(c, r, 4) ? "r" : "h";                                                                     // the main line's hills
  if (speckle(c, r, 3)) return "r";                                                                                    // the valleys: craters and wire,
  return speckle(c, r, 5) ? "m" : ".";                                                                                 // and old paddies
}
const grid = groundGrid(COLS, ROWS, kind);
function ring(h, d){                              // the hexes exactly d from h
  const out = [];
  for (let r = h[1] - d; r <= h[1] + d; r++){
    for (let c = h[0] - d - 1; c <= h[0] + d + 1; c++){
      if (hdist([c, r], h) === d) out.push([c, r]);
    }
  }
  return out;
}
const TRENCH = [...ring(TOP, 9), ...ring(TOP, 3), ...ring(H200, 5)];
const BUNKERS = [[TOP[0] - 9, TOP[1]], [TOP[0] + 9, TOP[1]], [TOP[0] - 4, TOP[1] - 8], [TOP[0] + 5, TOP[1] - 8], [TOP[0], TOP[1] + 9], [TOP[0], TOP[1]]];
const trenchHexes = TRENCH.filter(h => !BUNKERS.some(b => b[0] === h[0] && b[1] === h[1]));

const UN = { side: 0, facing: N }, CH = { side: 1, facing: S };
const GI = { quality: "regular", weapon: "rifle_service", kit: "vietnam_army", formation: "extended", mounted: false };
const MG = { quality: "regular", weapon: "machine_gun", kit: "vietnam_army", formation: "mg", mounted: false };
const PVA = { quality: "veteran", weapon: "pistol_smg", kit: "none", formation: "extended", mounted: false };
const units = [
  at("E Company, 31st Infantry (the north trenches)", UN, 50, GI, 10, [TOP[0], TOP[1] - 9], N),
  at("E Company, 31st Infantry (the west trenches)", UN, 30, GI, 6, [TOP[0] - 9, TOP[1] + 2], 3),
  { ...at("E Company's machine guns", UN, 10, MG, 2, [TOP[0] + 6, TOP[1] - 7], N), fixed: [TOP[0], 18] },   // laid by day down the north slope
  at("L Company, 31st Infantry (Hill 200)", UN, 120, GI, 12, [H200[0], H200[1] - 5], 2),
  at("K Company, 31st Infantry (from the main line)", UN, 135, GI, 20, [80, 122], N),
  at("G Company, 17th Infantry (from the main line)", UN, 130, GI, 13, [56, 124], N),
  at("Chinese battalion up the north slope", CH, 400, PVA, 30, [TOP[0], 18], S),
  at("Chinese company from Old Baldy (the west)", CH, 150, PVA, 12, [16, 60], 0),
  at("Chinese machine guns", CH, 10, { ...MG, kit: "none", quality: "veteran" }, 2, [50, 14], 5),
];

writeField({
  phases: [   // an exchange is about a minute; times from docs and sources in the project's battle-phases research, rounded
    { name: "E Company overrun", at: 1, note: "23:05: the lights come on all over the hill and the Chinese battalion comes up the north slope." },
    { name: "The first relief", at: 176, note: "Shortly after 02:00 L Company's platoons are sent up to reinforce E Company; most of the hill is in Chinese hands.", arrive: ["L Company, 31st Infantry (Hill 200)"] },
    { name: "K Company counter-attacks", at: 326, note: "04:30: the barrage lifts and K Company steps off; L Company attacks again at about the same time.", arrive: ["K Company, 31st Infantry (from the main line)"] },
    { name: "A fresh Chinese company", at: 550, note: "08:14: G Company of the 17th Infantry arrives as a fresh Chinese company appears (which company it was is our reading).", arrive: ["Chinese company from Old Baldy (the west)", "G Company, 17th Infantry (from the main line)"] },
  ],
  ends: { at: 1496, why: "the hill back in American hands by the 18th: midnight from 23:05 on the 16th" },
  objective: { at: TOP, side: 1, name: "the top of Pork Chop Hill", radius: 9 },
  id: "porkchop-1953", name: "Pork Chop Hill, 16-17 April 1953", sides: ["United Nations", "Chinese"], table: "korea-1950-53-hospitalized",
  travel: { map: "porkchop-1953", place: "Pork Chop Hill", within: 1, sides: ["United Nations", "Chinese"] },
  weather: "{cond: fair, wind: calm, light: night, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { trench: trenchHexes, bunker: BUNKERS, wire: ring(TOP, 14).filter((_, i) => i % 3 !== 0) },
  support: [
    { name: "7th Division artillery (105 mm, flash fire)", side: 0, kind: "field", tubes: 36 },
    { name: "155 mm and 8-inch howitzers", side: 0, kind: "howitzer", tubes: 12 },
    { name: "4.2-inch mortars", side: 0, kind: "mortar", tubes: 8 },
    { name: "Chinese mortars", side: 1, kind: "mortar", tubes: 16 },
    { name: "Chinese artillery", side: 1, kind: "field", tubes: 12 },
  ],
  header: [
    `Pork Chop Hill on the night of 16-17 April 1953, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1600 m east to west and 1130 m`,
    "north to south, north at the top: Pork Chop in the middle, ringed with trenches and bunkers and",
    "wire, Hill 200 to the south-east, the main line's hills along the bottom, the valleys between",
    "cratered and wired.",
    "Generated by tools/maps/make_porkchop_field.mjs: edit that file and re-run it rather than this one.",
    "The hill, trenches, bunkers, valley and Hill 200 are drawn by hand to the shape the accounts",
    "give, not traced from any map; the deployment is the Chinese attack, in our own words, with",
    "round numbers for play. A dark night: fire illumination and flares. The defenders wear the",
    "M1952 flak vest; the Chinese attack with burp guns (submachine guns) and grenades.",
    "",
    "What happened, briefly: at about 23:00 on 16 April 1953 a Chinese battalion came up Pork Chop",
    "out of the dark and overran most of E Company's trenches. K Company counterattacked up the hill",
    "before dawn and L Company from Hill 200; companies of the 17th Infantry followed, and by the",
    "18th the hill was back in American hands, after some 77,000 shells had been fired on the",
    "outposts. In April the Americans lost 104 killed and 373 wounded.",
  ],
});
