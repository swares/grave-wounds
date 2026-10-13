// Builds data/fields/goosegreen-1982.yaml: Darwin Hill at dawn on 28 May 1982, on the field map at
// 10 m a hex. Run from this folder after editing: node make_goosegreen_field.mjs (no packages
// needed).
//
// Sources, all public domain or plain fact, and the drawing is ours: the official history of the
// campaign as summarised publicly. After fighting down the isthmus through the night, 2 Para's A
// Company came up to Darwin Hill at first light and was stopped below the Argentine trenches
// along the ridge, pinned in a gorse-filled gully; B Company was held on the open slope further
// west towards Boca House; the commanding officer went forward with his small headquarters and
// was killed charging a trench; the paratroopers broke in with rockets, grenades and machine guns
// later that morning. The ridge, the gully, the gorse, the shore and Darwin settlement are drawn by
// hand to that shape, not traced from any map, and are approximate; the deployment is the fight
// at dawn, in our own words, with round numbers for play.
import { N, S, wobble, patch, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

const COLS = 140, ROWS = 110;                 // 1400 m east to west, about 950 m north to south
const RIDGE = c => 56 + Math.round(wobble(c / 8, 0.6, 1.4));             // the crest of Darwin ridge, west to east
const SHORE = r => 126 + Math.round(wobble(r / 7, 1.1, 0.3) * 1.5);       // Darwin's inlet of Choiseul Sound along the east
const DARWIN = [114, 74], GULLY = [100, 44];
function shoreAndSettlement(c, r){            // the sea, the loch, Darwin's houses and paddocks (null: neither)
  if (c >= SHORE(r) || c < 4) return "w";                                                              // Choiseul Sound east, Brenton Loch west
  if (patch(c, r, { cx: DARWIN[0], cy: DARWIN[1], rx: 6, ry: 5 })) return speckle(c, r, 3) ? "." : "T";   // Darwin settlement
  return null;
}
function slopes(c, r){                        // the gorse in the gully and along the hedges, the ridge and the open grass
  if (patch(c, r, { cx: GULLY[0], cy: GULLY[1], rx: 5, ry: 10, a: 0.4, b: 1.1 })) return speckle(c, r, 4) ? "r" : "o";   // the gorse gully below Darwin Hill: scrub, seen and shot through
  if (r === 34 && c > 30 && c < 90 && !speckle(c, r, 5)) return "o";                                  // a gorse hedge across the slope
  if (Math.abs(r - RIDGE(c)) <= 3 && c > 50) return speckle(c, r, 3) ? "r" : "h";                      // Darwin ridge
  return speckle(c, r, 7) ? "m" : ".";                                                                 // open grass and peat, boggy hollows
}
const kind = (c, r) => shoreAndSettlement(c, r) ?? slopes(c, r);
const grid = groundGrid(COLS, ROWS, kind);
const TRENCH = [];
for (let c = 54; c <= 112; c++){
  if (c % 7 !== 0) TRENCH.push([c, RIDGE(c) - 2]);
}
const BUNKERS = [[64, RIDGE(64) - 2], [84, RIDGE(84) - 2], [98, RIDGE(98) - 2], [108, RIDGE(108) - 2]];

const UK = { side: 0, facing: S }, AR = { side: 1, facing: N };
const PARA = { quality: "veteran", weapon: "rifle_assault", kit: "ww2_rifleman", formation: "extended", mounted: false };
const GPMG = { quality: "veteran", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false };
const CONSCRIPT = { quality: "green", weapon: "rifle_assault", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };
const MAG = { quality: "regular", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false, prone: true };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
const units = [
  at("A Company, 2 Para (in the gorse gully)", UK, 90, PARA, 10, [GULLY[0], GULLY[1] - 6], S),
  at("B Company, 2 Para (on the open slope)", UK, 90, PARA, 14, [44, 30], S),
  at("2 Para's headquarters (H. Jones)", UK, 20, PARA, 4, [GULLY[0] - 6, 26], S),
  at("D Company, 2 Para (coming up)", UK, 90, PARA, 14, [70, 12], S),
  at("2 Para's machine guns", UK, 10, GPMG, 2, [GULLY[0] + 8, 30], S),
  at("Argentine platoons in the ridge trenches (west)", AR, 70, CONSCRIPT, 14, [70, RIDGE(70) - 1], N),
  at("Argentine platoons in the ridge trenches (Darwin Hill)", AR, 70, CONSCRIPT, 14, [98, RIDGE(98) - 1], N),
  at("Argentine machine guns", AR, 10, MAG, 2, [86, RIDGE(86)], N),
  at("Argentine reserve (Darwin)", AR, 40, { ...CONSCRIPT, prone: false }, 6, [DARWIN[0] - 8, DARWIN[1] - 8], N),
];

writeField({
  id: "goosegreen-1982", name: "Darwin Hill, Goose Green, 28 May 1982", sides: ["British", "Argentines"], table: "falklands-1982-wounds",
  travel: { map: "goosegreen-1982", place: "Darwin Hill", within: 1, sides: ["British", "Argentines"] },
  weather: "{cond: overcast, wind: breeze, dir: W, light: dusk, ground: {mud: 1, snow: 0}}",
  grid, units,
  hexWorks: { trench: TRENCH.filter(h => !BUNKERS.some(b => b[0] === h[0] && b[1] === h[1])), bunker: BUNKERS },
  support: [
    { name: "8 Battery's 105 mm light guns", side: 0, kind: "field", tubes: 3 },
    { name: "2 Para's 81 mm mortars", side: 0, kind: "mortar", tubes: 2 },
    { name: "Argentine 105 mm pack howitzers", side: 1, kind: "field", tubes: 3 },
    { name: "Argentine 120 mm mortars", side: 1, kind: "mortar", tubes: 2 },
  ],
  header: [
    `Darwin Hill at dawn on 28 May 1982, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1400 m east to west and 950 m north to`,
    "south, north at the top: Darwin ridge across the middle with the Argentine trenches along its",
    "crest, the gorse gully below Darwin Hill on the right, a gorse hedge across the open slope,",
    "Darwin settlement by its inlet of Choiseul Sound in the lower right, Brenton Loch along the left.",
    "Generated by tools/maps/make_goosegreen_field.mjs: edit that file and re-run it rather than this one.",
    "Light cover (scrub, key o): the gorse in the gully and the gorse hedge, seen and shot through at a cost.",
    "The ridge, the gully, the gorse, the shore and the settlement are drawn by hand to the shape",
    "the accounts give, not traced from any map; the deployment is the fight at dawn, in our own",
    "words, with round numbers for play. Grey first light, a cold westerly, the peat wet underfoot.",
    "",
    "What happened, briefly: at first light on 28 May 1982 2 Para's A Company was stopped below the",
    "Argentine trenches on Darwin Hill and pinned in the gorse gully, B Company on the bare slope to",
    "the west. Lieutenant-Colonel H. Jones was killed leading his headquarters against a trench.",
    "Later that morning the paratroopers broke into the line with rockets, grenades and machine",
    "guns, and by the afternoon they had closed round Goose Green.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
