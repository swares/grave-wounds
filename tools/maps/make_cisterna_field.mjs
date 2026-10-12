// Builds data/fields/cisterna-1944.yaml: the Rangers at dawn short of Cisterna, 30 January 1944,
// on the field map at 10 m a hex. Run from this folder after editing: node make_cisterna_field.mjs
// (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's account (Anzio
// Beachhead, American Forces in Action series). The 1st and 3rd Ranger Battalions came up the
// Pantano ditch in the dark and at dawn were at the road crossing, within 800 yards of Cisterna,
// in open, treeless fields. The Germans had brought in fresh troops the night before; as light
// came up, a force with three self-propelled guns opened fire, and machine guns, mortars and
// snipers in houses, haystacks and dugouts pinned the Rangers in the open; by noon tanks drove
// through them. A few Rangers reached the buildings near the railroad station. The fields, the
// ditch, the road, the farmhouses and the town's edge are drawn by hand to that shape, not
// traced from any map, and are approximate; the deployment is first light, in our own words,
// with round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 150, ROWS = 120;                 // 1500 m east to west, about 1040 m north to south
const townEdge = c => 9 + wobble(c / 4, 0.3, 1.1) * 0.8;
const road = r => Math.round(30 + (ROWS - 1 - r) * 0.28 + (r < 12 ? (12 - r) * 0.6 : 0));      // the Conca-Cisterna road, from the bottom left up to the town
const ditch = r => Math.round(140 - (ROWS - 1 - r) * 0.62 + wobble(r / 3, 1.7, 0.4) * 0.6);    // the Pantano ditch, from the bottom right north-west
const FARMS = [[52, 46], [96, 40], [118, 58], [24, 62], [70, 66], [132, 30]];                  // farmhouses and their yards
const STACKS = [[40, 74], [84, 54], [108, 78], [16, 84], [60, 30], [140, 70], [76, 88]];         // haystacks
function kind(c, r){
  if (r < townEdge(c) && c > 20 && c < 142) return speckle(c, r, 5) ? "." : "T";            // Cisterna's southern edge
  if (r < 14 && c >= 6 && c <= 20) return speckle(c, r, 3) ? "." : "T";                      // the railroad station and its sheds
  if (Math.abs(c - road(r)) <= 1 && r >= 8) return ".";                                      // the road
  if (r >= 30 && Math.abs(c - ditch(r)) <= 1) return "m";                                    // the ditch: wet, steep-sided
  if (r === 20 || r === 21) return c % 37 < 2 ? "." : "m";                                   // a cross ditch below the town, bridged here and there
  for (const [fc, fr] of FARMS) if (patch(c, r, { cx: fc, cy: fr, rx: 3, ry: 2, a: fc, b: fr })) return "T";
  for (const [sc, sr] of STACKS) if (Math.abs(c - sc) <= 1 && Math.abs(r - sr) <= 1) return "r";
  return speckle(c, r, 41) ? "r" : ".";                                                      // open, treeless fields
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const US = { side: 0, facing: N }, DE = { side: 1, facing: S };
const RANGERS = { quality: "veteran", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false };
const GREN = { quality: "veteran", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };   // dug in, in houses and haystacks
const MG = { quality: "veteran", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false, prone: true };
const units = [
  unit("1st Ranger Battalion (at the road crossing)", US, 380, RANGERS, [40, 44, 82]),
  unit("3rd Ranger Battalion (along the ditch)", US, 380, RANGERS, [36, 92, 96]),
  unit("3rd Reconnaissance Troop platoon (following up the road)", US, 43, RANGERS, [8, 38, 112]),
  unit("Hermann Göring Division infantry (the town's edge)", DE, 400, GREN, [80, 40, Math.round(townEdge(80)) + 1]),
  unit("Machine guns in the farmhouses (west)", DE, 10, MG, [2, 51, 49]),
  unit("Machine guns in the farmhouses (east)", DE, 10, MG, [2, 95, 43]),
  unit("Machine guns in the farmhouses (far east)", DE, 10, MG, [2, 117, 61]),
  unit("Riflemen in haystacks and dugouts (west)", DE, 150, GREN, [30, 4, 70]),
  unit("Riflemen in haystacks and dugouts (east)", DE, 150, GREN, [30, 116, 84]),
  unit("Paratroops by the station", DE, 120, { ...GREN, prone: false }, [24, 2, 18]),
];

writeField({
  id: "cisterna-1944", name: "The Rangers at Cisterna, 30 January 1944", sides: ["Americans", "Germans"], table: "owens-wwii",
  travel: { map: "anzio-1944", place: "Cisterna", within: 2, sides: ["Americans", "Germans"] },
  weather: "{cond: fair, wind: calm, dir: N, ground: {mud: 1, snow: 0}}",
  grid, units,
  support: [
    { name: "3rd Division field artillery (105 mm)", side: 0, kind: "field", tubes: 12 },
    { name: "Ranger 4.2-inch mortars", side: 0, kind: "mortar", tubes: 4 },
    { name: "Self-propelled guns (direct fire)", side: 1, kind: "tank", tubes: 3 },
    { name: "Tanks (later in the morning)", side: 1, kind: "tank", tubes: 6 },
    { name: "German mortars", side: 1, kind: "mortar", tubes: 8 },
  ],
  header: [
    `The Rangers short of Cisterna at first light, 30 January 1944, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1500 m`,
    "east to west and 1040 m north to south, north at the top: the southern edge of Cisterna along",
    "the top, the railroad station top left, the Conca road coming up from the bottom left, the",
    "Pantano ditch from the bottom right, and open, treeless fields with farmhouses and haystacks.",
    "Generated by tools/maps/make_cisterna_field.mjs: edit that file and re-run it rather than this one.",
    "The fields, the ditch, the road, the farmhouses and the town's edge are drawn by hand to the",
    "shape the account gives, not traced from any map; the deployment is first light, in our own",
    "words, with round numbers for play. A cold, still January dawn; the reclaimed ground soft.",
    "There are no vehicle rules: the self-propelled guns and tanks are on call as direct fire (Fire",
    "support), and the Rangers' bazookas and sticky grenades are left to the GM. The Germans in",
    "houses, haystacks and dugouts start gone to ground; houses are buildings (cover).",
    "",
    "What happened, briefly: the Rangers had come four miles up the ditch in the dark, past German",
    "posts, and were short of the town at dawn. Three self-propelled guns opened on them; the",
    "Rangers knocked them out, but machine guns, mortars and snipers pinned them in the open, and",
    "the Germans closed in from all sides. A few reached the buildings by the station. Around noon",
    "tanks drove through them and split them into small groups; the last radio message came at",
    "12:30. Of 767 Rangers six got back; most of the rest were taken prisoner.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
