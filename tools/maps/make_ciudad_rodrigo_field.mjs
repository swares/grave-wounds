// Builds data/fields/ciudad-rodrigo-1812.yaml: the storm of Ciudad Rodrigo on the night of 19 January 1812,
// the great and lesser breaches, on the field map at 10 m a hex. Run from this folder after editing:
// node make_ciudad_rodrigo_field.mjs (no packages needed).
//
// Sources (project doc "ciudad-rodrigo-research"):
// - The walls (napoleon-series, The Siege of Ciudad Rodrigo): a main wall about 10 m high with a dry ditch
//   about 7 m wide at its foot; before it a fausse-braie about 6 m high with a ditch "7 meters wide and 3
//   meters high on the glacis side". The 94th found that ditch "not so great but that men with arms might
//   leap into it" (Waterloo Association, the 94th's narrative): no ditch here is deep.
// - The breaches (napoleon-series): the great breach about 30 m wide at the town's northernmost angle, the
//   lesser about 10 m wide and about 200 m east of it, both made by the guns on the Little Teson. Behind
//   the great breach: chevaux-de-frise on top, mines on the slopes, cuts 5 m deep and 3 m wide on both sides
//   of the terreplein, and a 24-pounder on each side firing onto it (the 94th's narrative: two light brass
//   guns en barbette on the fausse-braie, enfilading it). Behind the lesser: no cuts, only a disabled gun
//   across its top, and at least one gun able to hit its slope from the flank.
// - The storm (historyofwar; napoleon-series; Wikipedia; britishbattles): at 7 pm the 3rd Division went at the
//   great breach, Mackinnon's brigade behind a party with hay bags, while Campbell's brigade (the 5th, 77th
//   and 94th) came from the convent of Santa Cruz on the west to clear the fausse-braie and the ditch and
//   reached the breach first; a mine or a train of powder fired under the stormers killed Mackinnon. The
//   Light Division (Vandeleur's brigade, from behind the convent of San Francisco) went at the lesser breach;
//   its forlorn hope first took the fausse-braie for the main wall; it got in, almost unopposed, and took the
//   great breach's defenders from behind. "An hour had nearly elapsed before all resistance ceased" (the 94th's
//   narrative). Both divisions met in the cathedral square. The moon "threw the shadow of the wall" on the
//   ditch (the 94th's narrative): a waxing crescent about a third lit, high in the south-west at seven
//   (worked out for the place and day).
// - The garrison: about 1,800 to 1,900 under Barrié (the 34th Light, the 113th Line, two artillery companies).
// The drawing is schematic and ours: the north face straight, the west face running south from the angle;
// no plan was traced. No source reached gives the columns' strengths or the garrison's split: those are
// ours, with round numbers. The diversions (Pack at the San Pelayo gate, O'Toole over the Águeda) are off
// the map.
import { N, S, speckle, groundGrid, unit, at, stepHex, writeField } from "./field_lib.mjs";

const COLS = 60, ROWS = 62;                    // 600 m east to west, about 540 m north to south
const FB = 35, MW = 38, WF = 9, WM = 12;        // the fausse-braie's first row and the main wall's; their first columns on the west face
const inTown = (c, r) => c >= WM && r >= MW;
const inFausse = (c, r) => !inTown(c, r) && c >= WF && r >= FB;   // the fausse-braie, an L round the angle
const outside = (c, r) => !inTown(c, r) && !inFausse(c, r);
// The breaches, through the fausse-braie and the main wall: the sources give the great about 30 m (3 hexes)
// and the lesser about 10 m (1 hex); drawn 6 and 4 hexes wide (ours). The rules lay a column's ranks out
// behind it on a diagonal (units.js footprint), so a gap cut straight through the two walls admits a column
// only some hexes narrower than itself: at the sources' widths no column deeper than it is wide got in, and
// self-play stalled on the fausse-braie (2 November 2026). Wellington's columns went in narrower and deeper.
const GREAT = new Set([13, 14, 15, 16, 17, 18]), LESSER = new Set([34, 35, 36, 37]);   // the breaches' columns
const breach = (c, r) => (GREAT.has(c) || LESSER.has(c)) && r >= FB && r <= MW;
const greatTop = (c, r) => GREAT.has(c) && r === MW;

function kind(c, r){
  if (breach(c, r)) return "s";                                       // the breach: a bare slope of rubble, the stormers in full view
  if (inFausse(c, r)) return ".";                                     // the fausse-braie's terreplein
  if (inTown(c, r)){
    if (r <= MW + 2 || c <= WM + 1) return ".";                       // the rampart and the ground behind it
    if (r >= 50 && r <= 55 && c >= 16 && c <= 24) return ".";         // the cathedral square
    return c % 6 === 0 || r % 5 === 0 ? "." : "T";                    // streets and houses
  }
  return speckle(c, r, 8) ? "r" : ".";                                // the glacis, broken by the siege works
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- works ----------
// Walls round the fausse-braie (its outer face) and the main wall (between it and the town), none across a
// breach; a ditch (not deep) at the foot of each; at the top of the great breach the cuts on both sides (deep:
// 5 m) and chevaux-de-frise across it into the town; the trench the columns go in from.
const wall = [], ditch = [], cut = [], chevaux = [], trench = [];
const on = ([c, r]) => c >= 0 && c < COLS && r >= 0 && r < ROWS;
for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++){
  for (let d = 0; d < 6; d++){
    const o = stepHex([c, r], d);
    if (!on(o)) continue;
    if (inFausse(c, r) && outside(...o)){
      if (!breach(c, r)) wall.push([[c, r], o]);
      ditch.push([[c, r], o]);
    }
    if (inTown(c, r) && inFausse(...o)){
      if (!(breach(c, r) && breach(...o))) wall.push([[c, r], o]);
      if (!breach(c, r) || !breach(...o)) ditch.push([[c, r], o]);
    }
    if (greatTop(c, r) && inTown(...o) && !breach(...o)){
      if (o[1] <= MW + 1 && !GREAT.has(o[0])) cut.push([[c, r], o]);   // the cuts either side of the breach's top
      else chevaux.push([o, [c, r]]);                                       // the chevaux-de-frise across it
    }
  }
}
for (let c = 4; c <= 42; c++) if (!speckle(c, 12, 5)) trench.push([c, 12]);   // the trench on the Little Teson, about 200 m out

// The French fired a train of powder and shells on the great breach as the stormers reached its top (the 94th's
// narrative; napoleon-series: a mine; others: a magazine): hidden, on the breach's slope through the fausse-braie.
const MINES = [...GREAT].map(c => ({ at: [c, MW - 1], kind: "sprung", hidden: true }));

// ---------- the armies (pos is the middle of the front row) ----------
const AL = { side: 0, facing: S }, FR = { side: 1, facing: N };
const LINE = { quality: "regular", weapon: "musket_smoothbore", kit: "none", formation: "close", mounted: false };
const LIGHT = { ...LINE, quality: "veteran" };
const LADDERS = { ...LINE, ladders: true };
const GUNS = { quality: "regular", weapon: "artillery_smoothbore", kit: "none", formation: "battery", mounted: false, emplaced: true };   // ten crew to a gun
const through = c => [[c, FB - 4], [c, MW + 4]];   // straight down to the foot of a breach, then over its top and into the town
const TO_GREAT = through(16), TO_LESSER = through(36);
const FROM_WEST = [[6, FB - 3], ...TO_GREAT];                       // north along the west face, round the angle, along the ditch to the great breach
const units = [
  // the garrison on this front (ours: Barrié's 1,800 to 1,900 held the whole circuit and the castle; no reserve
  // here: none is recorded, and a reserve on or near the breach kept it from ever being secured in self-play)
  unit("French at the great breach", FR, 500, LINE, [5, 13, MW + 3]),
  at("French on the fausse-braie", FR, 200, LINE, 5, [24, FB + 1], N),
  unit("French at the lesser breach", FR, 150, LINE, [3, 34, MW + 3]),
  at("Gun east of the great breach", FR, 10, GUNS, 1, [19, MW + 1], 2),     // facing west, along the rampart onto the breach
  at("Gun west of the great breach", FR, 10, GUNS, 1, [12, MW + 1], 0),     // on the rampart at the angle, facing east onto the breach
  at("Gun on the lesser breach's flank", FR, 10, GUNS, 1, [40, MW + 1], 2),
  // the 3rd Division (ours: the strengths): its storming party with the hay bags and ladders, then
  // Mackinnon's brigade in two halves 3 hexes wide; Campbell's brigade (the 5th, 77th, 94th)
  // from the convent of Santa Cruz on the west, along the ditch to the breach
  unit("3rd Division storming party (with ladders)", AL, 500, { ...LADDERS, quality: "veteran", formation: "open", via: TO_GREAT }, [3, 15, 22]),
  unit("Mackinnon's brigade (first half)", AL, 700, { ...LINE, via: TO_GREAT }, [3, 14, 12]),
  unit("Mackinnon's brigade (second half)", AL, 700, { ...LINE, via: TO_GREAT }, [3, 19, 12]),
  at("Campbell's brigade (5th, 77th, 94th, with ladders)", AL, 1200, { ...LADDERS, via: FROM_WEST }, 3, [6, 44], N),
  // the Light Division: its stormers, then Vandeleur's brigade in columns of 300, 2 hexes wide (the strengths
  // and the columns ours)
  unit("Light Division stormers (with ladders)", AL, 300, { ...LADDERS, quality: "veteran", via: TO_LESSER }, [2, 35, 26]),
  unit("Vandeleur's brigade (first column)", AL, 300, { ...LIGHT, via: TO_LESSER }, [2, 39, 26]),
  unit("Vandeleur's brigade (second column)", AL, 300, { ...LIGHT, via: TO_LESSER }, [2, 36, 17]),
  unit("Vandeleur's brigade (third column)", AL, 300, { ...LIGHT, via: TO_LESSER }, [2, 39, 17]),
  unit("Vandeleur's brigade (fourth column)", AL, 300, { ...LIGHT, via: TO_LESSER }, [2, 42, 17]),
];

writeField({
  phases: [   // an exchange is about a minute; the storm went in at seven
    { name: "The storm", at: 1, note: "Seven at night, a crescent moon high in the south-west: the 3rd Division goes for the great breach, Campbell's brigade along the ditch from Santa Cruz, the Light Division for the lesser breach." },
  ],
  ends: { at: 55, why: "\"an hour had nearly elapsed before all resistance ceased\" (the 94th's narrative)" },
  // The great breach is the objective: the main attack's, which its defenders held until the Light Division took
  // them from behind; then both divisions went on to the cathedral square, where the garrison gave up (the
  // square and the castle beyond it: no fight for them is recorded). The French at the great breach hold there
  // (orders.yaml).
  objective: { at: [16, MW + 2], side: 0, name: "the great breach", radius: 6 },
  id: "ciudad-rodrigo-1812", name: "Ciudad Rodrigo, 19 January 1812 (the breaches)", sides: ["Allies", "French"], table: "peninsular-1808-14-all-hits",
  travel: { map: "ciudad-rodrigo-1812", place: "Ciudad Rodrigo", within: 1, sides: ["Allies", "France"] },
  weather: "{cond: fair, wind: calm, light: moonlit, ground: {mud: 0, snow: 0}}",
  grid, units, deep: ["cut"], edgeTypes: { cut: "ditch" }, mines: MINES,
  // The 3rd Division rallied under the guns and took the great breach (napoleon-series): broken units
  // re-form out of the enemy's reach (units.yaml morale.reform), as at Badajoz.
  reform: true,
  hexWorks: { trench },
  edgeWorks: { wall, ditch, cut, chevaux },
  header: [
    `The storm of Ciudad Rodrigo, 19 January 1812, the great and lesser breaches, at 10 m a hex: ${COLS} x ${ROWS} hexes, 600 m`,
    "east to west and about 540 m north to south, north at the top: the town's north face and the angle at its",
    "north-west corner, with the fausse-braie before the main wall; the great breach near the angle, the lesser",
    "200 m east; the glacis and the trench on the Little Teson above.",
    "Generated by tools/maps/make_ciudad_rodrigo_field.mjs: edit that file and re-run it rather than this one.",
    "Schematic, drawn by hand to the accounts (project doc ciudad-rodrigo-research), not traced from a plan.",
    "The fausse-braie and the main wall are stone-wall edges, each with a ditch at its foot (not deep: men",
    "leapt into it); each breach is a bare slope through both, the great 6 hexes and the lesser 4 (ours: the",
    "sources give 30 m and 10 m, too narrow for a column as the rules lay one out). Behind the great breach:",
    "deep cuts on both sides of its top, chevaux-de-frise across it, a gun on each side and a hidden mine on",
    "its slope. The columns' strengths and the garrison's split are ours: no source reached gives them. The",
    "Light Division's plan (plans.yaml) takes it through the lesser breach onto the great breach's defenders",
    "from behind; the great breach is the objective.",
    "",
    "What happened, briefly: after eleven days of siege the guns had made two breaches. At seven on the",
    "night of 19 January the 3rd Division stormed the great breach, where a mine or a train of powder went",
    "up under the stormers and killed Mackinnon, and the guns either side swept the top until their crews",
    "were overwhelmed; the Light Division got in at the lesser breach, where Craufurd was mortally wounded,",
    "and took the great breach's defenders from behind. In under an hour the garrison gave up, and the",
    "town was sacked that night.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
