// Builds data/fields/mojkovac-1916.yaml: the Montenegrin stand on the Bojna njiva above Mojkovac,
// on the upper Tara, on 6 January 1916, on the field map at 10 m a hex. Run from this folder after
// editing: node make_mojkovac_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours (project doc "mojkovac-topolcani-research"):
// the Montenegrin Sandžak army under Serdar Janko Vukotić, 6,500 men with 25 guns and 8 machine
// guns, against about 20,000 Austro-Hungarians with 45 guns (English Wikipedia, after the Vojna
// enciklopedija and Vukčević and Kovačević); the upper Tara valley, the Bojna njiva the "gate" of
// Mojkovac, the 205th Landsturm Brigade the bulk of Generalmajor Reinöhl's group, the Drobnjak
// battalion the only Montenegrin reserve, heavy snow and fog, Reinöhl killed leading his last
// reserves, and the Austro-Hungarian loss of 700 men, 224 of them dead (German Wikipedia, after the
// Austrian official history, vol. 4, p. 43); the attack after a heavy bombardment early on 6
// January, beaten off by noon, the Montenegrins holding and retaking Mojkovac by the day's end,
// knee-deep snow, hand-to-hand fighting with bayonets and knives (English Wikipedia). The sources
// disagree on who attacked: the English article has the Austro-Hungarians attack, the German one
// Vukotić's general attack on their position on the Bojna njiva; we take both, in turn. The ground
// is drawn by hand to that shape, not traced from any map; the slice of the line, the companies,
// the battalions and the times are ours, with round numbers for play, at the sourced odds of about
// three to one.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField, extended, mgTeam, alongLine } from "./field_lib.mjs";

const COLS = 130, ROWS = 110;                 // 1300 m east to west, about 950 m north to south
// The Bojna njiva: a long rise across the map, highest in the middle, falling to the Tara on the
// west; the Montenegrin trenches along its northern brow.
const brow = c => Math.round(52 + 6 * Math.cos((c - 70) / 26) + wobble(c / 7, 0.4, 1.9) * 0.7);
const river = r => 5 + Math.round(wobble(r / 4, 1.1, 0.3) * 0.6);   // the Tara, down the west edge
const BRIDGE = 96;                                                  // the road bridge into Mojkovac

function kind(c, r){
  const k = brow(c), w = river(r);
  if (c <= w) return r === BRIDGE ? "." : "w";
  if (c === w + 1 || c === w + 2) return speckle(c, r, 4) ? "r" : ".";                              // the riverbank
  if (r > k + 22 && c < 44 && patch(c, r, { cx: 24, cy: 98, rx: 18, ry: 10, a: 0.6, b: 1.4 })) return "T";   // Mojkovac's edge
  if (Math.abs(r - k) <= 2) return speckle(c, r, 6) ? "r" : "h";                                   // the brow: snow on short turf
  if (r > k + 2 && r <= k + 12) return speckle(c, r, 5) ? "o" : "h";                               // the top of the Bojna njiva
  if (r < k - 2 && r >= k - 16) {                                                                 // the slope up from the north
    if (patch(c, r, { cx: 108, cy: k - 9, rx: 12, ry: 7, a: 1.2, b: 0.4 })) return "F";
    return speckle(c, r, 7) ? "r" : "s";
  }
  if (r < k - 16) {                                                                               // the snowfields and the woods below
    if (patch(c, r, { cx: 30, cy: 10, rx: 20, ry: 9, a: 0.3, b: 2.0 })) return "F";
    if (patch(c, r, { cx: 98, cy: 14, rx: 24, ry: 10, a: 1.5, b: 0.8 })) return "F";
    return speckle(c, r, 8) ? "o" : ".";
  }
  return speckle(c, r, 4) ? "o" : ".";                                                            // the far side, down to the town
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies ----------
const MN = { side: 0, facing: N }, AH = { side: 1, facing: S };
const MONTE = extended("veteran", { prone: true }), MG = mgTeam("veteran", { prone: true }), LANDSTURM = extended("regular");
const onBrow = alongLine(brow, 1);                                     // just forward of the brow
const units = [
  unit("Sandžak army, a company above the Tara", MN, 200, MONTE, onBrow(18, 12)),
  unit("Sandžak army, a company on the Bojna njiva", MN, 200, MONTE, onBrow(20, 52)),
  unit("Sandžak army machine guns", MN, 10, MG, onBrow(2, 75)),
  unit("Sandžak army, a company on the east of the rise", MN, 200, MONTE, onBrow(20, 92)),
  unit("Drobnjak battalion (the reserve)", MN, 500, { ...MONTE, prone: false }, [30, 50, 62]),
  unit("205th Landsturm Brigade, a battalion by the river", AH, 800, LANDSTURM, [26, 12, 22]),
  unit("205th Landsturm Brigade, a battalion in the centre", AH, 800, LANDSTURM, [28, 50, 24]),
  unit("Austro-Hungarian machine guns", AH, 20, { ...MG, quality: "regular", prone: false }, [4, 64, 30]),
  unit("205th Landsturm Brigade, a battalion on the east", AH, 800, LANDSTURM, [26, 92, 22]),
  unit("Reinöhl's last reserves", AH, 800, LANDSTURM, [28, 50, 12]),
];
const trench = [12, 52, 92].flatMap((c0, i) => Array.from({ length: [18, 20, 20][i] }, (_, j) => [c0 + j, brow(c0 + j) - 1]))
  .concat([[74, brow(74) - 1], [75, brow(75) - 1]]);

writeField({
  phases: [   // an exchange is about a minute; the times are our reading of the accounts (project doc "mojkovac-topolcani-research")
    { name: "The bombardment and the attack", at: 1, note: "About 07:30: after a heavy bombardment of Mojkovac and the lines, the Landsturm come up out of the snowfields at the Bojna njiva (the hour is ours; 'early that morning')." },
    { name: "Beaten off", at: 271, note: "About noon: the attack has been beaten off (English Wikipedia), and heavy snow sets in (German Wikipedia: heavy snowfall and fog in the fighting on the Bojna njiva; the hour is ours).", weather: { cond: "heavy_snow", wind: "breeze" } },
    { name: "The Drobnjak battalion", at: 301, note: "About 12:30: Vukotić throws in his only reserve, the Drobnjak battalion, which breaks into the enemy's first line but not the second (German Wikipedia; the hour is ours).", arrive: ["Drobnjak battalion (the reserve)"] },
    { name: "Reinöhl's last reserves", at: 421, note: "About 14:30: Reinöhl leads his last reserves forward and is killed (German Wikipedia; the hour is ours). Bayonets and knives in the snow and fog.", arrive: ["Reinöhl's last reserves"], weather: { cond: "fog", wind: "calm" } },
    { name: "Dusk", at: 541, note: "About 16:30: the light goes; Mojkovac and the ground round it are in Montenegrin hands.", light: "dusk" },
  ],
  ends: { at: 571, why: "beaten off by noon, Mojkovac retaken by the day's end (English Wikipedia): 07:30 to about 17:00" },
  objective: { at: [72, brow(72)], side: 1, name: "the Bojna njiva, the gate of Mojkovac", radius: 8 },
  id: "mojkovac-1916", name: "Mojkovac, 6 January 1916", sides: ["Montenegrins", "Austro-Hungarians"], table: "wwi-1914-18-wounds",
  travel: { map: "serbia-1915", place: "Mojkovac", within: 1, sides: ["Serbia and Montenegro", "Central Powers"] },
  weather: "{cond: snow, wind: breeze, dir: N, ground: {mud: 0, snow: 2}}",
  grid, units,
  hexWorks: { trench },
  support: [
    { name: "Montenegrin mountain guns (a few)", side: 0, kind: "field", tubes: 2 },
    { name: "Austro-Hungarian field and mountain guns", side: 1, kind: "field", tubes: 8 },
    { name: "Austro-Hungarian heavy guns", side: 1, kind: "howitzer", tubes: 2 },
  ],
  header: [
    `The Bojna njiva above Mojkovac on the upper Tara, 6 January 1916, at 10 m a hex: ${COLS} x ${ROWS} hexes, about`,
    "1300 m east to west and 950 m north to south, north at the top: snowfields and woods below,",
    "the long rise of the Bojna njiva across the middle with the Montenegrin trenches along its",
    "brow, the Tara down the west edge with a bridge, and the edge of Mojkovac at the bottom left.",
    "Generated by tools/maps/make_mojkovac_field.mjs: edit that file and re-run it rather than this one.",
    "The rise, the river and the woods are drawn by hand to the shape the accounts give, not traced",
    "from any map; the slice of the line, the companies, the battalions and the hours are our",
    "reading, with round numbers for play at the sourced odds of about three to one (6,500",
    "Montenegrins with 25 guns and 8 machine guns against about 20,000 Austro-Hungarians with 45",
    "guns). The sources disagree on who attacked: we have the Austro-Hungarians attack first, then",
    "the Montenegrin reserve counter-attack.",
    "",
    "What happened, briefly: while the Serbian army crossed the mountains to the Adriatic, the",
    "Montenegrin Sandžak army under Serdar Janko Vukotić was ordered to hold the Austro-Hungarians",
    "off its flank. On 6 January 1916, Orthodox Christmas Eve, the Austro-Hungarians attacked",
    "after a heavy bombardment, in knee-deep snow; they were beaten off by noon, and in fighting",
    "with bayonets and knives on the Bojna njiva, in snow and fog, the Drobnjak battalion broke into",
    "their line and Generalmajor Reinöhl was killed leading his last reserves. A second attack on",
    "7 January failed too, and the Austro-Hungarians drew off. They lost 700 men, 224 of them dead",
    "(the Austrian official history); the Montenegrins 205 (English Wikipedia). Montenegro laid",
    "down its arms within three weeks.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
