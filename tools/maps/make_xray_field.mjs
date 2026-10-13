// Builds data/fields/xray-1965.yaml: landing zone X-Ray on the afternoon of 14 November 1965, on
// the field map at 10 m a hex. Run from this folder after editing: node make_xray_field.mjs
// (no packages needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the plain facts of the
// battle as the US Army's accounts give them and as they are summarised publicly. X-Ray was a
// flat clearing about 100 m across, ringed by low trees and big termite hills, at the eastern
// foot of the Chu Pong massif, with a dry creek bed along its west side; only about eight
// helicopters could land at once. B Company landed first and pushed west across the creek bed
// and up towards the massif; its 2nd Platoon chased the enemy onto a knoll and was cut off
// there; A Company came in on B's left along the creek bed, C Company to the south. The North
// Vietnamese 9th and 7th Battalions of the 66th Regiment came down off the massif from the west
// and south-west. The clearing, the creek bed, the knoll and the slopes are drawn by hand to that
// shape, not traced from any map, and are approximate; the deployment is mid-afternoon of the
// 14th, as D Company was coming in, in our own words, with round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 160, ROWS = 130;                 // 1600 m east to west, about 1130 m north to south
const LZ = [104, 66];                         // the middle of the clearing
const creek = r => 86 + Math.round(wobble(r / 6, 0.9, 2.1) * 1.2);       // the dry creek bed, north to south west of the clearing
const foot = r => 58 + wobble(r / 8, 1.7, 0.3) * 3;                       // the foot of the massif's slopes
const KNOLL = { cx: 62, cy: 34, rx: 6, ry: 5, a: 0.5, b: 1.4 };            // the cut-off platoon's knoll
function kind(c, r){
  if (patch(c, r, { cx: LZ[0], cy: LZ[1], rx: 9, ry: 6, a: 2.1, b: 0.6 })) return speckle(c, r, 9) ? "r" : ".";   // the clearing: elephant grass, a termite hill or two
  if (Math.abs(c - creek(r)) <= 2) return "r";                             // the dry creek bed: steep little banks, cover
  if (patch(c, r, KNOLL)) return "h";
  if (c < foot(r)) return speckle(c, r, 4) ? "h" : "F";                   // the massif's lower slopes: forest on rising ground
  if (speckle(c, r, 11)) return "r";                                       // termite hills
  return speckle(c, r, 3) ? "o" : "F";                                     // scrub trees and tall grass (scrub)
}
const grid = groundGrid(COLS, ROWS, kind);

// ---------- the armies (pos is the middle of the front row) ----------
const US = { side: 0, facing: N }, VN = { side: 1, facing: S };
const CAV = { quality: "regular", weapon: "rifle_assault", kit: "ww2_rifleman", formation: "extended", mounted: false };
const MG = { quality: "regular", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false };
const PAVN = { quality: "veteran", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const flying = u => ({ ...u, lands: 0 });     // comes in by air at the landing zone
const units = [
  at("B Company, 1st Battalion, 7th Cavalry (across the creek bed)", US, 90, { ...CAV, prone: true }, 20, [creek(50) - 4, 50], 3),
  at("2nd Platoon, B Company (cut off on the knoll)", US, 27, { ...CAV, prone: true }, 5, [KNOLL.cx, KNOLL.cy], 2),
  at("A Company (along the creek bed, B's left)", US, 110, { ...CAV, prone: true }, 22, [creek(80) - 1, 80], 3),
  at("C Company (south of the clearing)", US, 105, CAV, 26, [LZ[0] - 2, 92], S),
  at("Battalion machine guns and mortars (the command post's termite hill)", US, 20, MG, 4, [LZ[0], LZ[1] + 2], 3),
  flying(at("D Company (landing)", US, 110, CAV, 12, [LZ[0], LZ[1]], 3)),
  flying(at("B Company, 2nd Battalion, 7th Cavalry (flown in at dusk)", US, 120, CAV, 12, [LZ[0], LZ[1]], 3)),
  at("9th Battalion, 66th Regiment (down off the massif)", VN, 450, PAVN, 40, [40, 46], 0),
  at("7th Battalion, 66th Regiment (from the south-west)", VN, 450, PAVN, 40, [64, 108], 5),
  at("North Vietnamese company round the knoll", VN, 120, PAVN, 14, [48, 30], 0),
  at("66th Regiment machine guns", VN, 15, { ...MG, kit: "none", quality: "veteran" }, 3, [50, 70], 0),
];

writeField({
  id: "xray-1965", name: "Landing zone X-Ray, 14 November 1965", sides: ["United States", "North Vietnamese"], table: "vietnam-1965-70-hospitalized",
  travel: { map: "iadrang-1965", place: "Landing zone X-Ray", within: 2, sides: ["United States", "North Vietnamese"] },
  weather: "{cond: fair, wind: calm, ground: {mud: 0, snow: 0}}",
  lz: [LZ],
  grid, units,
  support: [
    { name: "105 mm howitzers (1st Battalion, 21st Artillery, at Falcon)", side: 0, kind: "field", tubes: 12 },
    { name: "81 mm mortars", side: 0, kind: "mortar", tubes: 4 },
    { name: "Aerial rocket artillery (helicopter gunships)", side: 0, kind: "gunship", tubes: 4 },
    { name: "Skyraiders and jets (bombs, napalm)", side: 0, kind: "fighter_bomber", tubes: 6 },
    { name: "North Vietnamese mortars", side: 1, kind: "mortar", tubes: 6 },
  ],
  header: [
    `Landing zone X-Ray on the afternoon of 14 November 1965, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1600 m east to`,
    "west and 1130 m north to south, north at the top: the clearing right of middle (the landing",
    "zone, H), the dry creek bed west of it, the lower slopes of the Chu Pong massif on the left,",
    "the knoll where B Company's 2nd Platoon was cut off up to the north-west.",
    "Generated by tools/maps/make_xray_field.mjs: edit that file and re-run it rather than this one.",
    "Light cover (scrub, key o): the tall elephant grass among the scrub trees (woods) round the clearing.",
    "The clearing, the creek bed, the knoll and the slopes are drawn by hand to the shape the",
    "accounts give, not traced from any map; the deployment is mid-afternoon of the 14th, as D",
    "Company was coming in, in our own words, with round numbers for play. Scrub trees, tall",
    "elephant grass and termite hills all round (woods, scrub, rough). D Company, and B",
    "Company of the 2nd Battalion at dusk, come in by air at the landing zone, 80 men an exchange,",
    "while the North Vietnamese are not on top of it; a hot landing zone costs men.",
    "",
    "What happened, briefly: B Company landed at 10:48 and within the hour was fighting on the",
    "slopes west of the creek bed; its 2nd Platoon was cut off on a knoll and surrounded. A Company",
    "came in on its left, C Company to the south, and the North Vietnamese came down off the",
    "massif at all three. Artillery from Falcon, rocket helicopters and air strikes with napalm",
    "held them off while the rest of the battalion landed under fire; D Company came in during the",
    "afternoon and a company of the 2nd Battalion at dusk. The cut-off platoon held through the",
    "night and was reached the next afternoon. At X-Ray the Americans lost 79 killed and 121",
    "wounded over three days; they counted 634 North Vietnamese dead.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
