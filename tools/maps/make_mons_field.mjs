// Builds data/fields/mons-1914.yaml: the canal salient at Nimy, north of Mons, on 23 August 1914,
// on the field map at 10 m a hex. Run from this folder after editing: node make_mons_field.mjs
// (no packages needed).
//
// Sources, all plain fact, and the drawing is ours: the Mons-Condé canal bends north in a loop
// at Nimy, with a road bridge and a railway bridge near its tip; the 4th Royal Fusiliers held
// the bridges and the houses of Nimy on the south bank, the 4th Middlesex the canal to the east;
// German infantry of IX Corps (Infantry Regiments 84 and 86 among them) came at them over the
// fields and through the woods to the north, many in close order. Each British battalion had
// two machine guns. The canal, the village, the woods and the bridges are drawn by hand to that
// shape, not traced from any map, and are approximate. The deployment is mid-morning, in our
// own words; numbers are round figures for play.
import { N, S, wobble, patch, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 150, ROWS = 120;                 // 1500 m east to west, about 1040 m north to south
// The canal: about 20 m wide, its loop's tip at the top of the salient near the middle.
const canal = c => 34 + ((c - 72) / 46) ** 2 * 26 + wobble(c / 4, 0.4, 1.3) * 0.4;
const roadBridge = 80, railBridge = 64;       // columns of the two bridges at the tip of the loop
function inCanal(c, r){                       // about 20 m wide, unbroken
  const lo = Math.min(canal(c - 0.5), canal(c + 0.5)), hi = Math.max(canal(c - 0.5), canal(c + 0.5));
  return r >= lo - 0.5 && r <= hi + 1.5;
}
function kind(c, r){
  const k = canal(c);
  if (inCanal(c, r)) return c === roadBridge || c === railBridge ? "." : "w";
  if (r > k + 2 && patch(c, r, { cx: 74, cy: 62, rx: 22, ry: 14, a: 0.5, b: 1.7 })) return "T";     // Nimy, on the south bank
  if (r > k + 2 && patch(c, r, { cx: 30, cy: 104, rx: 20, ry: 14, a: 1.1, b: 0.2 })) return "T";    // the edge of Mons
  if (r < k - 6 && patch(c, r, { cx: 128, cy: 14, rx: 26, ry: 16, a: 2.0, b: 0.9 })) return "F";    // woods north-east, towards Obourg
  if (r < k - 6 && patch(c, r, { cx: 18, cy: 12, rx: 16, ry: 10, a: 0.3, b: 2.4 })) return "F";     // a wood to the north-west
  if (r > k + 2 && patch(c, r, { cx: 118, cy: 90, rx: 10, ry: 8, a: 1.6, b: 0.1 })) return "h";     // a slag heap behind the line
  if (r < k && r > k - 4 && (c % 9 === 0)) return "r";                                             // the towpath's spoil and hedges
  return ".";
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const BR = { side: 0, facing: N }, GE = { side: 1, facing: S };
const RIFLES = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "mg", mounted: false };
const COLUMN = { quality: "regular", weapon: "rifle_service", kit: "none", formation: "close", mounted: false };
const row = c => Math.ceil(Math.max(canal(c - 0.5), canal(c + 0.5))) + 3;    // the first row clear of the canal on the south bank
const rowFor = (c0, w) => Math.max(...Array.from({ length: w }, (_, i) => row(c0 + i)));   // clear of the canal all along a front
const units = [
  unit("4th Royal Fusiliers (C Coy, the railway bridge)", BR, 180, RIFLES, [18, 50, rowFor(50, 18)]),
  unit("Royal Fusiliers machine guns (railway bridge)", BR, 10, MG, [2, 68, rowFor(68, 2)]),
  unit("4th Royal Fusiliers (B Coy, the road bridge)", BR, 180, RIFLES, [18, 72, rowFor(72, 18)]),
  unit("4th Royal Fusiliers (A and D Coys, Nimy)", BR, 400, RIFLES, [34, 58, 76]),
  unit("4th Middlesex (canal east)", BR, 400, RIFLES, [20, 98, rowFor(98, 20)]),
  unit("Middlesex machine guns", BR, 10, MG, [2, 118, rowFor(118, 2)]),
  unit("IR 84, I Battalion", GE, 900, COLUMN, [6, 62, 18]),
  unit("IR 84, II Battalion", GE, 900, COLUMN, [6, 84, 16]),
  unit("IR 86, I Battalion (from the woods)", GE, 900, COLUMN, [6, 116, 36]),
  unit("IR 84 machine-gun company", GE, 30, { ...MG, quality: "regular" }, [6, 73, 26]),
  unit("IR 84, III Battalion (in support)", GE, 900, { ...COLUMN, formation: "extended" }, [60, 72, 9]),
];

writeField({
  phases: [   // an exchange is about a minute; times from docs and sources in the project's battle-phases research, rounded
    { name: "The first assault", at: 1, note: "09:00: IR 84 comes at the bridges of the salient in close order." },
    { name: "A renewed attack", at: 31, note: "Half an hour after the first is beaten off, a wider attack comes in through the woods (which battalion is our reading).", arrive: ["IR 86, I Battalion (from the woods)"] },
    { name: "The attack in force", at: 121, note: "11:00: the Germans attack in force (that the supporting battalion went in then is our reading).", arrive: ["IR 84, III Battalion (in support)"] },
    { name: "Withdrawal", at: 251, note: "13:10: the Fusiliers are ordered back; they go at 13:40." },
  ],
  objective: { at: [railBridge, rowFor(railBridge, 1)], side: 1, name: "the railway bridge at Nimy", radius: 3 },
  id: "mons-1914", name: "Mons, 23 August 1914 (the Nimy salient)", sides: ["British", "Germans"], table: "wwi-1914-18-wounds",
  travel: { map: "mons-1914", place: "Nimy bridges", within: 2, sides: ["British", "Germans"] },
  weather: "{cond: overcast, wind: calm, dir: SW, ground: {mud: 0, snow: 0}}",
  grid, units,
  support: [
    { name: "British field guns (18-pounders)", side: 0, kind: "field", tubes: 6 },
    { name: "German field guns (77 mm)", side: 1, kind: "field", tubes: 12 },
    { name: "German field howitzers", side: 1, kind: "howitzer", tubes: 6 },
  ],
  header: [
    `The canal salient at Nimy, north of Mons, 23 August 1914, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1500 m`,
    "east to west and 1040 m north to south, north at the top: the canal loop across the middle,",
    "its two bridges near the tip, Nimy on the south bank, open fields and woods to the north.",
    "Generated by tools/maps/make_mons_field.mjs: edit that file and re-run it rather than this one.",
    "The canal, the village, the woods and the bridges are drawn by hand to the shape the accounts",
    "give, not traced from any map; the deployment is mid-morning, in our own words, with round",
    "numbers for play. Water (the canal) can be crossed only at the bridges.",
    "",
    "What happened, briefly: the Royal Fusiliers held the bridges at the tip of the salient, with",
    "their two machine guns at the railway bridge. German infantry came over the open ground in",
    "close order and through the woods, and the British rifle and machine-gun fire cut them down",
    "in numbers; the Fusiliers' machine-gun officer and one of his gunners kept the guns firing",
    "after the rest of the crews were hit. German guns pounded the salient, the attackers worked",
    "round its flanks, and by afternoon the battalion fell back through Nimy. The Germans crossed,",
    "and that night the BEF began its long retreat.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
