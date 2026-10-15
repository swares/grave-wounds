// Builds data/maps/easting73-1991.yaml: the 2nd Armored Cavalry Regiment's last day before the
// Tawakalna Division, 26 February 1991, in the desert of southern Iraq, on the travel map at 0.5 km
// a hex, from about 60 Easting (on the military grid) east to Objective Norfolk. Run from this
// folder after editing: npm ci && node make_easting73.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours:
// - the plain facts of the battle as the US Army's own accounts give them (public domain) and as
//   they are summarised publicly: on 26 February 1991 the 2nd Armored Cavalry Regiment, screening
//   ahead of VII Corps, attacked east in a sandstorm; its limit of advance, first 60 Easting, was
//   moved up to 70 Easting once it made contact; Eagle Troop fought through Iraqi positions in
//   buildings near the 00 Northing at about 68 Easting, crested a low rise and destroyed a
//   Tawakalna tank company dug in behind it, then went on to the high ground about 74 Easting;
//   Iron Troop, halted near 67 Easting to the south, came north under fire and destroyed tanks
//   on the 70 Easting position, with Killer Troop firing in support; Ghost Troop, the
//   northernmost, held a ridge above a wadi north of Eagle against counter-attacks for some six
//   hours into the night; the Iraqi brigades were the Tawakalna Division's 18th Mechanized and
//   the 37th Armored (the accounts disagree whether the 37th was the Tawakalna's or the 12th
//   Armored Division's) and the 12th Armored Division's 9th Armored; the 1st Infantry Division
//   passed through the cavalry in the small hours of the 27th and took Objective Norfolk, a
//   supply depot round the crossing of the IPSA pipeline road and desert tracks, by dawn;
// - the grid lines placed from the military grid (zone 38: about 96.6 km of grid to a degree of
//   longitude at this latitude), the positions after the accounts and approximate; the ground,
//   the rises and the pipeline road drawn by hand (the wadi below Ghost Troop's ridge is named, not
//   drawn: we have no course for it). They are approximate.
import { buildCampaign } from "./campaign_lib.mjs";

const NORTHING_00 = 29.845;                   // the latitude of Eagle Troop's fight, about the 00 Northing
const easting = e => 45 + (600 + e - 500) / 96.6;   // grid easting (the last two figures, in km, of the 6xx km band) to longitude
const P = {
  e60: [NORTHING_00, easting(60)], e67: [29.800, easting(67)], e70: [NORTHING_00, easting(70)], village: [29.854, easting(68)],
  rise: [NORTHING_00, easting(73)], beyond: [NORTHING_00, easting(74.2)], ghost: [29.890, easting(73)], killer: [29.790, easting(65)],
  norfolk: [29.860, 46.915], depot: [29.875, 46.930], ghostback: [29.890, easting(61)], eagleback: [NORTHING_00, easting(61)],
  ironback: [29.800, easting(62)], tawakalna37: [29.900, easting(76)], ninth: [29.790, easting(74)],
};
const HILLS = [[P.rise, 0.6], [P.beyond, 0.8], [P.ghost, 0.6]];
const ROADS = [
  [[29.960, 46.940], "depot", "norfolk", [29.740, 46.895]],                       // the IPSA pipeline road, north to south (approximate)
  [[29.845, 46.620], "e60", "village", "rise", "norfolk"],                         // a desert track east
];
const NAMES = {
  e60: "60 Easting (the first limit of advance)", e67: "Iron Troop's halt near 67 Easting", e70: "70 Easting (the limit of advance moved up)",
  village: "The buildings near 68 Easting", rise: "The rise at 73 Easting", beyond: "The high ground about 74 Easting",
  ghost: "Ghost Troop's ridge above the wadi", killer: "Killer Troop's position", norfolk: "Objective Norfolk", depot: "The Iraqi supply depot",
};
const notes = {
  e60: "The 2nd Armored Cavalry Regiment's first limit of advance on 26 February 1991, moved up to 70 Easting after contact (approximate)",
  village: "Where Eagle Troop first took fire, from infantry in a cluster of buildings, a dug-in anti-aircraft gun and a village (approximate)",
  rise: "Eagle Troop crested this low rise at about 16:20 in a sandstorm and destroyed a Tawakalna tank company dug in behind it (approximate)",
  beyond: "Eagle Troop went on past its limit of advance to this high ground and destroyed more T-72s (approximate)",
  ghost: "The northernmost troop held a ridge above a wadi here against counter-attacks for about six hours into the night (approximate)",
  e67: "Iron Troop halted here, then moved north under fire and destroyed tanks on the 70 Easting position (approximate)",
  norfolk: "Round the crossing of the IPSA pipeline road and desert tracks; taken by the 1st Infantry Division by dawn on 27 February (approximate)",
};
const map = buildCampaign({
  id: "easting73-1991", script: "make_easting73.mjs", title: "73 Easting, February 1991",
  name: "73 Easting, 1991 (the 2nd Armored Cavalry's last day)",
  start_date: "1991-02-26", calendar: "gregorian", latitude: 30, climate: "arid", climate_shift: 0, base: ".",
  bounds: [46.620, 29.950, 46.960, 29.740], midLat: 29.85, hexKm: 0.5,
  header: [
    "The grid lines (60 to 74 Easting) are placed from the military grid; the troops, the buildings,",
    "the rises, the depot and the pipeline road are placed after the accounts and are",
    "approximate, drawn by hand. Flat, hard, open desert, with low rises a few metres high that hide",
    "what is behind them. Ghost Troop's wadi is not drawn: we have no course for it.",
    "",
    "What happened, briefly: on 26 February 1991 the 2nd Armored Cavalry Regiment attacked east in",
    "a sandstorm into the Iraqi Republican Guard's Tawakalna Division. Eagle Troop fought through the",
    "buildings near 68 Easting and, at about 16:20, crested the rise at 73 Easting onto a dug-in tank",
    "company, destroying it in some 23 minutes; Ghost Troop to the north held its ridge into the night,",
    "Iron and Killer Troops fought to the south. In the small hours of the 27th the 1st Infantry",
    "Division passed through and took Objective Norfolk by dawn. Numbers below are round figures for",
    "play: a cavalry troop was about 120 men with nine tanks and a dozen or so Bradleys; the Iraqi",
    "brigades' strengths that day are not known, so theirs are estimates.",
  ],
  places: P, names: NAMES, notes, water: [], rivers: {}, majorRivers: [], streams: [], bridges: [], fords: [],
  farms: [], woods: [], marsh: [], hills: HILLS, mountains: [], roads: ROADS,
  towns: [], villages: ["village"],
  kinds: { e60: "camp", rise: "objective", norfolk: "objective", depot: "objective" },
  forces: [
    { name: "Eagle Troop, 2nd Squadron", type: "foot", side: "Coalition", men: 120, tools: true, at: "eagleback" },
    { name: "Ghost Troop, 2nd Squadron", type: "foot", side: "Coalition", men: 120, tools: true, at: "ghostback" },
    { name: "Iron Troop, 3rd Squadron", type: "foot", side: "Coalition", men: 120, tools: true, at: "ironback" },
    { name: "Killer Troop, 3rd Squadron", type: "foot", side: "Coalition", men: 120, tools: true, at: "killer" },
    { name: "Iraqi infantry in the buildings", type: "foot", side: "Iraqis", men: 100, tools: true, at: "village" },
    { name: "Tawakalna Division, 18th Mechanized Brigade", type: "foot", side: "Iraqis", men: 2000, tools: true, at: "rise" },
    { name: "37th Armored Brigade", type: "foot", side: "Iraqis", men: 1500, tools: true, at: "tawakalna37" },
    { name: "12th Armored Division, 9th Armored Brigade", type: "foot", side: "Iraqis", men: 1500, tools: true, at: "ninth" },
    { name: "Depot troops at Norfolk", type: "foot", side: "Iraqis", men: 300, tools: true, at: "depot" },
  ],
});
console.log(`${map.cols} x ${map.rows} hexes`);
