// Builds data/fields/babuna-1915.yaml: the Serbian defence of the Babuna pass, on the road from
// Veles to Prilep, in mid-November 1915, on the field map at 10 m a hex. Run from this folder
// after editing: node make_babuna_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours (project doc "serbia1915-research"): about
// 5,000 men of the Serbian 2nd and 14th Infantry Regiments held the heights of the pass, which
// command the northern approach from Izvor, on "an enormous front" with "absolutely no reserves"
// and a few "little old cannon" (Flora Sandes, who was with the 2nd Regiment's ambulance); a
// Bulgarian division attacked in the first days of November and was driven back to Izvor, and
// with reinforcements from the Veles front the Bulgarians pressed the Serbs back to the crest,
// which they held "for a week and more" (the Nelson history); the retreat was ordered "at ten
// o'clock that night", and Prilep was occupied on 17 November. The day is our reading: a
// Bulgarian attack from dawn on one battalion's stretch of the crest, about 12-15 November, the
// pass given up at 22:00. The saddle, the spurs, the hairpins and the woods are drawn by hand to
// the accounts' shape, not traced from any map, and are approximate; the companies, the machine
// guns and the Bulgarian battalions are ours, with round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, frontRow, writeField } from "./field_lib.mjs";

const COLS = 130, ROWS = 110;                 // 1300 m east to west, about 950 m north to south
// The crest's row: lowest (furthest south) at the saddle in the middle, the two spurs pushing
// north towards Izvor on either side of the road.
const spur = (c, cx) => 14 * Math.exp(-(((c - cx) / 15) ** 2));
const ridge = c => Math.round(54 - spur(c, 28) - spur(c, 104) + wobble(c / 6, 0.8, 2.1) * 0.8);
const SADDLE = [64, ridge(64)];

// The road: up from Izvor in hairpins to the saddle, then down towards Prilep.
const ROUTE = [[56, 0], [56, 12], [74, 18], [56, 26], [74, 34], [60, 42], [64, SADDLE[1]], [66, 64], [72, 84], [72, ROWS - 1]];
const road = new Set();
for (let i = 0; i + 1 < ROUTE.length; i++){
  const [a, b] = [ROUTE[i], ROUTE[i + 1]], n = Math.max(Math.abs(b[0] - a[0]), Math.abs(b[1] - a[1]));
  for (let j = 0; j <= n; j++) road.add(`${Math.round(a[0] + (b[0] - a[0]) * j / n)},${Math.round(a[1] + (b[1] - a[1]) * j / n)}`);
}

function kind(c, r){
  if (road.has(`${c},${r}`)) return ".";
  const k = ridge(c);
  if (Math.abs(r - k) <= 2) return speckle(c, r, 5) ? "r" : "h";                                   // the crest: rock and short turf
  if (r < k && r >= k - 20){                                                                        // the north face, up from Izvor
    if (patch(c, r, { cx: 44, cy: k - 10, rx: 9, ry: 6, a: 0.4, b: 1.3 })) return "F";               // beech in the gully west of the road
    if (patch(c, r, { cx: 88, cy: k - 12, rx: 8, ry: 6, a: 1.7, b: 0.2 })) return "F";               // and east of it
    if (speckle(c, r, 6)) return "r";
    return speckle(c, r, 3) ? "o" : "s";                                                            // scrub oak on the slope
  }
  if (r > k && r <= k + 12) return speckle(c, r, 4) ? "o" : "s";                                    // the reverse slope
  if (r > k){                                                                                      // down towards Prilep
    if (patch(c, r, { cx: 30, cy: 92, rx: 22, ry: 12, a: 0.9, b: 2.2 })) return "F";
    if (patch(c, r, { cx: 108, cy: 96, rx: 18, ry: 10, a: 2.1, b: 0.6 })) return "F";
    return speckle(c, r, 3) ? "o" : ".";
  }
  if (patch(c, r, { cx: 18, cy: 10, rx: 16, ry: 9, a: 0.2, b: 1.9 })) return "F";                   // the foot of the pass, Izvor way
  if (patch(c, r, { cx: 112, cy: 8, rx: 16, ry: 8, a: 1.4, b: 0.7 })) return "F";
  return speckle(c, r, 4) ? "o" : ".";
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const SR = { side: 0, facing: N }, BG = { side: 1, facing: S };
const SERB = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false, prone: true };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "mg", mounted: false, prone: true };
const BULGAR = { quality: "regular", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false };
const onCrest = (w, c0) => [w, c0, Math.min(...Array.from({ length: w }, (_, i) => ridge(c0 + i))) - 1];   // the front row just forward of the crest
const units = [
  unit("2nd Regiment, a company on the west spur", SR, 220, SERB, onCrest(20, 18)),
  unit("2nd Regiment, a company astride the road", SR, 220, SERB, onCrest(22, 53)),
  unit("2nd Regiment, a company on the east spur", SR, 220, SERB, onCrest(20, 94)),
  unit("2nd Regiment machine guns (the saddle)", SR, 10, MG, onCrest(2, 76)),
  unit("2nd Regiment, a company behind the saddle", SR, 220, { ...SERB, prone: false }, [20, 54, SADDLE[1] + 10]),
  unit("Bulgarian battalion up the road", BG, 900, BULGAR, [30, 46, 12]),
  unit("Bulgarian battalion onto the west spur", BG, 900, BULGAR, [30, 8, 12]),
  unit("Bulgarian machine guns", BG, 20, { ...MG, quality: "regular", prone: false }, [4, 64, 14]),
  unit("Bulgarian battalion onto the east spur", BG, 900, BULGAR, [26, 98, 16]),
  unit("Bulgarian battalion from the Veles front", BG, 900, BULGAR, [30, 46, 27]),
];
const trench = units.filter(u => u.side === 0 && u.prone).flatMap(frontRow);

writeField({
  phases: [   // an exchange is about a minute; the day is our reading of the accounts (project doc "serbia1915-research")
    { name: "The bombardment and the first attack", at: 1, note: "Dawn, about 06:30: the Bulgarian guns open on the crest and a battalion comes up the road from Izvor." },
    { name: "Up the spurs", at: 61, note: "About 07:30: a second battalion climbs the west spur into the fire from the trenches." },
    { name: "The flank pressed", at: 391, note: "About 13:00: the Bulgarians press the east spur (which flank is our reading).", arrive: ["Bulgarian battalion onto the east spur"] },
    { name: "Reinforcements from Veles", at: 571, note: "About 16:00: a fresh battalion comes up from the Veles front.", arrive: ["Bulgarian battalion from the Veles front"] },
    { name: "Dusk", at: 631, note: "About 17:00: the light goes; the Serbs hang on along the crest.", light: "dusk" },
    { name: "Night", at: 661, note: "Dark: the fight dies down to sniping along the crest.", light: "night" },
    { name: "The retreat", at: 931, note: "22:00: the order comes to retreat, and the regiments go down the road to Prilep.", light: "night" },
  ],
  ends: { at: 931, why: "retreat ordered at ten o'clock that night (Sandes): 22:00 from 06:30" },
  objective: { at: SADDLE, side: 1, name: "the saddle of the Babuna pass", radius: 6 },
  id: "babuna-1915", name: "The Babuna pass, November 1915", sides: ["Serbians", "Bulgarians"], table: "wwi-1914-18-wounds",
  travel: { map: "serbia-1915", place: "Babuna pass", within: 1, sides: ["Serbia and Montenegro", "Central Powers"] },
  weather: "{cond: overcast, wind: breeze, dir: N, ground: {mud: 1, snow: 0}}",
  grid, units,
  hexWorks: { trench },
  support: [
    { name: "Serbian mountain guns (a few, old)", side: 0, kind: "field", tubes: 2 },
    { name: "Bulgarian field guns", side: 1, kind: "field", tubes: 12 },
    { name: "Bulgarian heavy guns", side: 1, kind: "howitzer", tubes: 4 },
  ],
  header: [
    `The Babuna pass on the road from Veles to Prilep, mid-November 1915, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1300 m`,
    "east to west and 950 m north to south, north at the top: the road climbs in hairpins from",
    "Izvor to the saddle in the middle, between two spurs that push north; the Serbian trenches",
    "run along the crest; the road goes on down towards Prilep at the bottom.",
    "Generated by tools/maps/make_babuna_field.mjs: edit that file and re-run it rather than this one.",
    "The saddle, the spurs, the hairpins and the woods are drawn by hand to the shape the accounts",
    "give, not traced from any map; the day, the companies and the Bulgarian battalions are our",
    "reading, with round numbers for play. Machine guns and the Bulgarian divisions engaged are",
    "not in the sources found.",
    "",
    "What happened, briefly: with Skopje and Veles lost, two Serbian regiments, about 5,000 men",
    "with a few old guns and no reserves, held the Babuna heights across the road to Prilep. They",
    "drove the first Bulgarian division back to Izvor in the first days of November; reinforced",
    "from the Veles front, the Bulgarians pushed them back to the crest, which they held for a",
    "week and more. Flora Sandes, with the 2nd Regiment's ambulance, saw the wounded walk down",
    "from the position. At ten one night the retreat was ordered; Prilep fell on 17 November, and",
    "the regiments went back by Bitola into Albania.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
