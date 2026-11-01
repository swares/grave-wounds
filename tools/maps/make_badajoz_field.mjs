// Builds data/fields/badajoz-1812.yaml: the storm of Badajoz on the night of 6-7 April 1812, the
// breaches and the castle, on the field map at 10 m a hex. Run from this folder after editing:
// node make_badajoz_field.mjs (no packages needed).
//
// Sources (project doc "badajoz-research"): three breaches made by the guns, in the Trinidad
// bastion, the Santa Maria bastion and the curtain between them, stormed at 22:00 by the 4th
// Division (Trinidad) and the Light Division (Santa Maria), which lost their way against a ravelin
// and mixed; across the top of each breach a fringe of sword blades chained in the rubble, with
// spiked planks on the slope and musketeers behind; the ditch in front of the Trinidad flooded
// from the dammed Rivillas, which cut that breach off; the castle on its hill north of the
// breaches, above the Rivillas, taken by escalade by Picton's 3rd Division while every attack on
// the breaches failed. Each storming party went in 500 strong with 12 ladders. The garrison was
// about 5,000 under Philippon, most of them elsewhere on the walls. Dark: the moon rose after
// two in the morning (worked out for the place and day). The 5th Division's escalade of San
// Vicente, about a kilometre west, is off the map.
// The drawing is schematic and ours: the enclosure as a south face and an east face with the two
// bastions, the castle as a walled block on high ground; no plan was traced. No source reached
// gives the wall heights, the ditch's depth, the breaches' widths, the divisions' strengths in
// the storm or the garrison's split, so those are ours, with round numbers.
import { N, S, wobble, patch, speckle, groundGrid, unit, at, stepHex, writeField } from "./field_lib.mjs";

const COLS = 90, ROWS = 80;                    // 900 m east to west, about 690 m north to south
const EF = 70, SF = 50;                        // the east face's column and the south face's row
const inCastle = (c, r) => c >= 50 && c <= EF && r >= 2 && r <= 20;   // the castle walls are the enclosure's on the east
const inTrinidad = (c, r) => c >= 63 && c <= 74 && r >= 44 && r <= 56 && Math.abs(c - 68.5) + Math.abs(r - 50) * 0.8 <= 7.5;
const inSantaMaria = (c, r) => c >= 33 && c <= 45 && r >= 46 && r <= 58 && Math.abs(c - 39) + Math.abs(r - 52) * 0.8 <= 7.5;
const inside = (c, r) => (c <= EF && r <= SF) || inTrinidad(c, r) || inSantaMaria(c, r);
const inTown = (c, r) => inside(c, r) && !inCastle(c, r);
// the breaches: a slope of rubble 8 hexes (80 m) wide in each, on its outer face (ours: no source
// reached gives their widths; units move as blocks, and a column wider than its breach cannot get in)
const breach = (c, r) => (inTrinidad(c, r) && r >= 54 && c >= 64 && c <= 72)
  || (c >= 51 && c <= 58 && r === SF)
  || (inSantaMaria(c, r) && c >= 43 && r >= 48 && r <= 56);
const RIVILLAS = r => 79 + Math.round(wobble(r / 4, 0.4, 1.9) * 0.7);
const lake = (c, r) => r >= 28 && r <= 62 && patch(c, r, { cx: 82, cy: 46, rx: 9, ry: 17, a: 1.1, b: 0.3 });
const flooded = (c, r) => !inside(c, r) && ((c >= 71 && c <= 75 && r >= 30 && r <= 58) || (r >= 57 && r <= 58 && c >= 66 && c <= 75));
const ravelin = (c, r) => r >= 54 && r <= 60 && Math.abs(c - 54.5) <= (60 - r) * 0.8;

function kind(c, r){
  if (breach(c, r)) return "x";
  if (inCastle(c, r)) return speckle(c, r, 4) ? "T" : "h";        // the Alcazaba on the Cerro de la Muela
  if (inTown(c, r)){
    if (r >= SF - 4 || inTrinidad(c, r) || inSantaMaria(c, r)) return ".";   // the ramparts and the ground behind them
    return c % 7 === 0 || r % 6 === 0 ? "." : "T";                 // streets and houses
  }
  if (flooded(c, r)) return c >= 71 ? "w" : "m";                     // the ditch flooded from the dammed Rivillas: deep along the east face, waist-deep before the Trinidad breach (where men drowned or stuck)
  if (lake(c, r)) return speckle(c, r, 3) ? "m" : "w";               // the inundation
  if (r < 28 && Math.abs(c - RIVILLAS(r)) <= 1) return r >= 20 && r <= 27 ? "m" : "w";   // the Rivillas; the dyke the 3rd Division crossed, under two feet of water (drawn wide enough for a column)
  if (r <= 22 && c > EF && c < RIVILLAS(r) - 1) return "s";          // the castle hill's slope down to the stream
  if (ravelin(c, r)) return "h";                                       // the unfinished ravelin before the curtain
  return speckle(c, r, 9) ? "r" : ".";                                 // the glacis, broken by the siege works
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- works ----------
// The walls on every side between the place and the ground outside it (none on a breach), the
// castle walled all round but for its gate into the town (blown, so left open); the deep ditch outside the town's
// walls and in front of the breaches; the sword blades (chevaux de frise: no ladders get over them) across the top of each
// breach, the spiked planks (stakes) on its slope; the trenches the columns go in from.
const wall = [], ditch = [], chevaux = [], stakes = [], trench = [];
const CASTLE_GATE = [[59, 20], [60, 20]];   // the gate into the town, which Wellington had blown: left open (the rules have no blowing of a gate)
for (let r = 0; r < ROWS; r++) for (let c = 0; c < COLS; c++){
  if (!inside(c, r)) continue;
  for (let d = 0; d < 6; d++){
    const o = stepHex([c, r], d);
    if (o[0] < 0 || o[0] >= COLS || o[1] < 0 || o[1] >= ROWS) continue;
    const outer = !inside(o[0], o[1]);
    if (inCastle(c, r) && !inCastle(o[0], o[1])){
      if (outer || !inTown(o[0], o[1]) || !CASTLE_GATE.some(g => g[0] === c && g[1] === r) || o[1] <= r) wall.push([[c, r], o]);
      continue;
    }
    if (!outer || inCastle(c, r)) continue;
    if (!breach(c, r)) wall.push([[c, r], o]);
    ditch.push([[c, r], o]);
  }
  if (breach(c, r)){
    stakes.push([c, r]);
    for (let d = 0; d < 6; d++){
      const o = stepHex([c, r], d);
      if (inTown(o[0], o[1]) && !breach(o[0], o[1])) chevaux.push([o, [c, r]]);
    }
  }
}
for (let c = 30; c <= 74; c++) if (!speckle(c, 71, 5)) trench.push([c, 71]);

// Fireballs and burning hay thrown into the ditch lit it and the breaches as the storm went in: each
// breach and the ditch before it lit all battle (lit: the radii are ours).
const FIRES = [{ at: [68, 56], radius: 7 }, { at: [55, 52], radius: 6 }, { at: [44, 53], radius: 7 }];

// ---------- the armies (pos is the middle of the front row) ----------
const AL = { side: 0, facing: N }, FR = { side: 1, facing: S };
const LINE = { quality: "regular", weapon: "musket_smoothbore", kit: "none", formation: "close", mounted: false };
const LIGHT = { ...LINE, quality: "veteran" };
const LADDERS = { ...LINE, ladders: true };
const GUNS = { quality: "regular", weapon: "artillery_smoothbore", kit: "none", formation: "battery", mounted: false };   // ten crew to a gun
const TRINIDAD = [[68, 60], [68, 52]], CURTAIN = [[55, 56], [55, 48]], SANTA_MARIA = [[50, 53], [45, 52]];   // to the foot of each breach, then over its top
const CASTLE = [[79, 24], [72, 14], [62, 12], [60, 22]];   // over the Rivillas by the dyke, up the hill, over the east wall, out by the gate
const units = [
  // the garrison on this front (ours: Philippon's 5,000 held the whole circuit and San Cristobal)
  unit("French at the Trinidad breach", FR, 600, LINE, [6, 65, 53]),
  unit("French at the curtain breach", FR, 400, LINE, [5, 52, 48]),
  at("French at the Santa Maria breach", FR, 600, LINE, 5, [41, 51], 0),
  at("Guns on the Santa Maria bastion", FR, 60, GUNS, 3, [37, 55], 5),
  at("The castle's garrison (French and Hesse-Darmstadt)", FR, 450, LINE, 6, [68, 10], 5),
  unit("Philippon's reserve in the town", FR, 500, LINE, [6, 52, 38]),
  // the storm: each division's storming party (500 with 12 ladders), then its two brigades (ours)
  // in columns a breach wide or less (8 hexes): a wider block cannot get through the gap
  // Each goes by its route (via) to its breach or wall, as the plan of attack sent it: walls stand
  // between every column and the town, and with no route a column halts at the first wall in its way.
  unit("4th Division storming party (with ladders)", AL, 500, { ...LADDERS, formation: "open", via: TRINIDAD }, [7, 62, 64]),
  unit("4th Division, first brigade", AL, 1500, { ...LINE, via: TRINIDAD }, [8, 61, 69]),
  unit("4th Division, second brigade", AL, 1500, { ...LINE, via: CURTAIN }, [8, 61, 75]),
  unit("Light Division storming party (with ladders)", AL, 500, { ...LADDERS, quality: "veteran", formation: "open", via: SANTA_MARIA }, [7, 46, 64]),
  unit("Light Division, first brigade", AL, 1000, { ...LIGHT, via: SANTA_MARIA }, [8, 45, 69]),
  unit("Light Division, second brigade", AL, 1000, { ...LIGHT, via: CURTAIN }, [8, 45, 75]),
  // the 3rd Division escaladed the castle as a division: every unit of it carries ladders
  at("3rd Division storming party (with ladders)", AL, 500, { ...LADDERS, via: CASTLE }, 5, [84, 18], 2),
  at("3rd Division, first brigade", AL, 1250, { ...LADDERS, via: CASTLE }, 5, [87, 9], N),
  at("3rd Division, second brigade", AL, 1250, { ...LADDERS, via: CASTLE }, 5, [87, 0], N),
];

writeField({
  phases: [   // an exchange is about a minute; the storm went in at ten
    { name: "The storm", at: 1, note: "Ten at night: the forlorn hopes go in; a French sentry gives the alarm, fireballs and burning hay light the ditch." },
    { name: "The breaches given up", at: 120, note: "About midnight: some forty attacks on the breaches have failed (historyofwar; another account says eleven); the castle is carried. Wellington's order to fall back from the breaches came about two." },
  ],
  ends: { at: 150, why: "about two and a half hours: the breaches assaulted for about two hours (Wikipedia), the castle carried in that time (our reading)" },
  // The castle is the objective: the breaches held all night, and the town fell because the 3rd
  // Division took the castle and held it until morning, when Philippon gave up (the 5th Division's
  // entry at San Vicente is off the map). The French at the breaches hold there (orders.yaml).
  objective: { at: [60, 11], side: 0, name: "the castle of Badajoz", radius: 6 },
  id: "badajoz-1812", name: "Badajoz, 6-7 April 1812 (the breaches and the castle)", sides: ["Allies", "French"], table: "peninsular-1808-14-all-hits",
  travel: { map: "albuera-1811", place: "Badajoz", within: 1, sides: ["Allies", "France"] },
  weather: "{cond: fair, wind: calm, light: night, ground: {mud: 0, snow: 0}}",
  grid, units, deep: ["ditch"],
  hexWorks: { stakes, trench },
  edgeWorks: { wall, ditch, chevaux },
  lit: FIRES,
  header: [
    `The storm of Badajoz, 6-7 April 1812, the breaches and the castle, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 900 m east to`,
    "west and 690 m north to south, north at the top: the town behind its south face, the Santa Maria",
    "bastion (left) and the Trinidad (right) with the three breaches, the castle on its hill at the top",
    "right, the Rivillas and its inundation down the east side, the glacis and the trenches below.",
    "Generated by tools/maps/make_badajoz_field.mjs: edit that file and re-run it rather than this one.",
    "Schematic, drawn by hand to the accounts (project doc badajoz-research), not traced from a plan.",
    "The walls are stone-wall edges with a deep ditch outside them (ladders go down into it); each",
    "breach is rubble with spiked planks (stakes) on its slope and the sword blades (chevaux de frise)",
    "across its top; the ditch before the Trinidad is flooded. Wall heights, the ditch's depth, the",
    "breaches' widths, the divisions' strengths and the garrison's split are ours: no source reached",
    "gives them. Each storming party is 500 with ladders, as the plan of attack gave it.",
    "",
    "What happened, briefly: after three weeks of siege the guns made two breaches, and a third in a",
    "day more. At ten at night on 6 April the 4th and Light Divisions went at the breaches. The ditch",
    "before the Trinidad had been flooded, the Light Division lost its way against a ravelin, and on",
    "the breaches sword blades, spiked planks, mines and the fire of men with three muskets each held",
    "them: some forty attacks failed, about two thousand fell in under two hours. Meanwhile Picton's",
    "3rd Division crossed the Rivillas and took the castle by escalade, and the 5th Division got over",
    "the walls at San Vicente, off this map, and came along the ramparts; the French left the",
    "breaches, and Philippon surrendered at seven in the morning. The sack lasted until the next day.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
