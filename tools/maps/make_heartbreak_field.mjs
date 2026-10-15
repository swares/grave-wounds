// Builds data/fields/heartbreak-1951.yaml: Hill 931 on Heartbreak Ridge, October 1951, on the field
// map at 10 m a hex. Run from this folder after editing: node make_heartbreak_field.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours: the US Army's account
// (Hermes, Truce Tent and Fighting Front) as summarised publicly. Hill 931 is the highest peak of
// a narrow ridge running north from Hill 894, about 1,300 yards to its south; the North Koreans
// held it in log-and-earth bunkers dug into the crest and the spurs; the 23rd Infantry attacked
// along the crest from 894 and the French Battalion up the spurs, under its machine guns and
// mortars, while tanks drove up the Mundung-ni valley to the west. The ridge, the spurs, the
// valley and the bunkers are drawn by hand to that shape, not traced from any map, and are
// approximate; the deployment is the October attack, in our own words, with round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 170, ROWS = 260;                 // 1700 m east to west, about 2250 m north to south
const CREST = r => 96 + Math.round(wobble(r / 12, 0.4, 1.7) * 2);       // the ridge's crest, north to south
const H931 = [CREST(70), 70], H894 = [CREST(228), 228];
const VALLEY = 22;                                                      // the Mundung-ni valley along the west edge
function valley(c, r){                            // the Mundung-ni valley: its stream, the track and the paddies
  if (Math.abs(c - VALLEY) <= 1) return "m";                                                            // the valley's stream
  if (c > VALLEY + 1 && c <= VALLEY + 9) return ".";                                                    // the track and the dry fields beside it
  return speckle(c, r, 3) ? "m" : ".";                                                                  // paddies
}
function onRidge(c, r){                           // the crest, the peaks and the spurs running down off the ridge
  const d = Math.abs(c - CREST(r));
  const peak = patch(c, r, { cx: H931[0], cy: H931[1], rx: 10, ry: 8 }) || patch(c, r, { cx: H894[0], cy: H894[1], rx: 9, ry: 7 });
  return peak || (r % 40 < 4 && d < 50);
}
function kind(c, r){
  if (Math.abs(c - VALLEY) <= 10) return valley(c, r);
  if (Math.abs(c - CREST(r)) <= 3) return speckle(c, r, 4) ? "r" : "h";                                 // the crest: narrow, rocky
  if (onRidge(c, r)) return speckle(c, r, 3) ? "r" : "h";
  return speckle(c, r, 3) ? "F" : "r";                                                                   // steep wooded slopes, shattered by shellfire
}
const grid = groundGrid(COLS, ROWS, kind);
const BUNKERS = [[H931[0] - 2, H931[1]], [H931[0] + 2, H931[1] + 2], [H931[0], H931[1] + 6], [CREST(90), 90], [CREST(110), 110], [CREST(50), 50], [CREST(84) + 6, 84]];

const UN = { side: 0, facing: N }, KP = { side: 1, facing: S };
const GI = { quality: "regular", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false };
const KPA = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false, prone: true };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "mg", mounted: false, prone: true };
const TANK = { quality: "regular", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank" };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("2nd Battalion, 23rd Infantry (along the crest from 894)", UN, 600, GI, 12, [CREST(180), 180], N),
  at("French Battalion (up the east spur)", UN, 600, { ...GI, quality: "veteran" }, 20, [150, 126], 2),
  at("1st Battalion, 23rd Infantry (up the west spur)", UN, 500, GI, 20, [50, 124], 0),
  at("72nd Tank Battalion company (the Mundung-ni valley)", UN, 40, TANK, 4, [VALLEY + 5, 200], N),
  at("North Koreans on Hill 931", KP, 300, KPA, 14, [H931[0], H931[1] + 2], S),
  at("North Koreans on the crest south of 931", KP, 200, KPA, 6, [CREST(100), 100], S),
  at("North Koreans on the crest north of 931", KP, 200, KPA, 8, [CREST(40), 40], S),
  at("North Korean machine guns (931)", KP, 15, MG, 3, [H931[0] + 4, H931[1] + 8], S),
  at("North Korean machine guns (the west spur)", KP, 10, MG, 2, [CREST(84) - 12, 84], 2),
];

writeField({
  objective: { at: H931, side: 0, name: "Hill 931", radius: 3 },
  id: "heartbreak-1951", name: "Hill 931 on Heartbreak Ridge, October 1951", sides: ["United Nations", "North Koreans"], table: "korea-1950-53-hospitalized",
  travel: { map: "heartbreak-1951", place: "Hill 931", within: 1, sides: ["United Nations", "North Koreans"] },
  weather: "{cond: fair, wind: breeze, dir: NW, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { bunker: BUNKERS },
  support: [
    { name: "105 mm and 155 mm howitzers (2nd Division artillery)", side: 0, kind: "field", tubes: 36 },
    { name: "8-inch and 155 mm guns (corps artillery)", side: 0, kind: "howitzer", tubes: 12 },
    { name: "4.2-inch mortars", side: 0, kind: "mortar", tubes: 8 },
    { name: "Fighter-bombers", side: 0, kind: "fighter_bomber", tubes: 8 },
    { name: "North Korean mortars", side: 1, kind: "mortar", tubes: 12 },
    { name: "North Korean and Chinese guns", side: 1, kind: "field", tubes: 8 },
  ],
  header: [
    `Hill 931 on Heartbreak Ridge, October 1951, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1700 m east to west and 2250 m north to`,
    "south, north at the top: the narrow crest running north and south up the middle, Hill 931 in",
    "the upper part, Hill 894 at the bottom, spurs off both sides, the Mundung-ni valley along the",
    "west edge.",
    "Generated by tools/maps/make_heartbreak_field.mjs: edit that file and re-run it rather than this one.",
    "The ridge, spurs, valley and bunkers are drawn by hand to the shape the accounts give, not",
    "traced from any map; the deployment is the October attack, in our own words, with round",
    "numbers for play. Steep slopes of shattered trees and rock; the North Koreans' bunkers on the",
    "crest; tanks in the valley (vehicles). A fair autumn day.",
    "",
    "What happened, briefly: the 23rd Infantry and the French Battalion attacked up the ridge from",
    "13 September 1951 and took and lost Hill 931 several times against North Koreans in bunkers,",
    "with heavy losses on both sides. In October the 2nd Division attacked along the whole front:",
    "the 23rd went in on the night of 5 October and before noon the next day Hill 931 was finally",
    "taken. From 10 October tanks went up the Mundung-ni valley behind the ridge, and the French",
    "took the last peak, Hill 851, at daybreak on 13 October. The tank company on this map came up",
    "the valley four days after 931 fell: the GM can leave it off.",
  ],
});
