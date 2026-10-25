// Builds data/fields/debecka-2003.yaml: the Debecka crossroads in northern Iraq on the morning of
// 6 April 2003, on the field map at 10 m a hex. Run from this folder after editing: node
// make_debecka_field.mjs (no packages needed).
//
// Sources (the project's debecka-research.md): two Special Forces A-teams, ODAs 391 and 392 of
// Company C, 3rd Battalion, 3rd SFG, with about 80 KDP Peshmerga, drove south to the crossroads
// where the Erbil-Qayyarah road meets Highway 2 and held it about 45 minutes. An Iraqi
// counter-attack of MT-LBs and T-55s came up out of the haze from the south; the teams fell back
// about 900 m to a low ridge they called "the Alamo" and fought it off with Javelins and heavy
// machine guns, 19 missiles for 17 hits, every shot over 2,200 m. A Navy F-14 then bombed by
// mistake the Kurdish and American vehicles gathered at "Press Hill" to the rear. The Iraqi
// counter-attack is the official history's (Veritas): at least five tanks, four armoured carriers,
// two troop trucks and several command vehicles, with infantry. The ridges, the crossroads and the
// town are drawn by hand to the distances the accounts give, not traced from any map, and are
// approximate; the deployment is the counter-attack coming out of the haze, in our own words, with
// round numbers for play.
import { speckle, patch, wobble, groundGrid, writeField, at } from "./field_lib.mjs";

const COLS = 150, ROWS = 290;                 // 1.5 km east to west, about 2,500 m north to south (rows 8.66 m apart)
const ROAD = 75;                              // the hardball road from the ridge, north to south
const ALAMO = c => 46 + Math.round(wobble(c / 8, 0.5, 1.3));           // the low ridge the teams fell back to
const CROSS = [ROAD, 150], PRESS = [ROAD, 10], DEBECKA = [132, 186];   // the crossroads 900 m south of the Alamo
function kind(c, r){
  if (patch(c, r, { cx: DEBECKA[0], cy: DEBECKA[1], rx: 16, ry: 18, a: 0.6, b: 1.4 })) return speckle(c, r, 4) ? "." : "T";   // the edge of Debecka
  if (patch(c, r, { cx: PRESS[0], cy: PRESS[1], rx: 30, ry: 8, a: 1.1, b: 0.3 })) return speckle(c, r, 5) ? "r" : "h";       // Press Hill, the second ridge
  const d = r - ALAMO(c);
  if (Math.abs(d) <= 2) return speckle(c, r, 6) ? "r" : "h";                                // the crest of the Alamo
  if (d > 2 && d <= 7) return "s";                                                          // its forward (south) slope
  if (Math.abs(r - CROSS[1]) <= 1 && c > 4 && c < COLS - 4) return speckle(c, r, 9) ? "r" : ".";   // the berm along Highway 2
  return speckle(c, r, 20) ? "r" : ".";                                                    // the open plain
}
const grid = groundGrid(COLS, ROWS, kind);

const US = { side: 0, facing: 4 }, IQ = { side: 1, facing: 1 };
const GMV = { quality: "veteran", weapon: "machine_gun", kit: "interceptor", formation: "armour", mounted: false, vehicle: "lorry" };   // gun trucks: .50s and Mk 19s
const JAVELIN = { quality: "veteran", weapon: "atgm", kit: "interceptor", formation: "extended", mounted: false, prone: true, nv: "thermal" };   // the launchers' thermal sights
const SF = { quality: "veteran", weapon: "rifle_assault", kit: "interceptor", formation: "extended", mounted: false, prone: true };
const PESH = { quality: "regular", weapon: "rifle_assault", kit: "none", formation: "extended", mounted: false, prone: true };
const T55 = { quality: "regular", weapon: "machine_gun", kit: "none", formation: "armour", mounted: false, vehicle: "tank", nv: "none" };
const MTLB = { ...T55, vehicle: "apc" };
const TRUCK = { ...T55, vehicle: "lorry" };
const IRAQI = { quality: "green", weapon: "rifle_assault", kit: "ww2_rifleman", formation: "extended", mounted: false };
// 31 Americans (Antenori): 26 of the two teams, four gun trucks each with two men aboard, the rest
// dismounted with the Javelins, and 3 combat controllers and 2 intelligence soldiers.
const units = [
  at("ODA 391's gun trucks (the Alamo, west of the road)", US, 8, GMV, 4, [ROAD - 12, ALAMO(ROAD - 12) - 3], 4),
  at("ODA 391's Javelin teams", US, 5, JAVELIN, 2, [ROAD - 8, ALAMO(ROAD - 8)], 4),
  at("ODA 392's gun trucks (the Alamo, east of the road)", US, 8, GMV, 4, [ROAD + 12, ALAMO(ROAD + 12) - 3], 4),
  at("ODA 392's Javelin teams", US, 5, JAVELIN, 2, [ROAD + 8, ALAMO(ROAD + 8)], 4),
  at("The combat controllers and the intelligence men", US, 5, { ...SF, fac: true }, 2, [ROAD, ALAMO(ROAD) - 1], 4),
  at("Peshmerga with the teams", US, 80, PESH, 14, [ROAD + 30, ALAMO(ROAD + 30)], 4),
  at("Peshmerga and the command vehicles at Press Hill", US, 60, { ...PESH, prone: false }, 10, [PRESS[0], PRESS[1] + 2], 4),
  at("Iraqi MT-LBs (ahead, under smoke)", IQ, 12, MTLB, 4, [ROAD, 282], 1),
  at("Iraqi T-55s", IQ, 20, T55, 5, [ROAD + 4, 288], 1),
  at("Iraqi motorised infantry", IQ, 100, IRAQI, 14, [ROAD - 20, 280], 1),
  at("Iraqi troop trucks and command vehicles", IQ, 8, TRUCK, 4, [ROAD - 4, 288], 1),
];

writeField({
  phases: [   // an exchange is about a minute; times are Gresham's ("local", UTC+4), which run about two hours ahead of the CENTCOM release for the bomb; sources in the project's debecka-research.md, rounded; (est.) marks an estimate
    { name: "Out of the haze", at: 1, note: "About 09:40 (Gresham's clock): MT-LBs and T-55s come up out of the haze from the south; the teams have fallen back from the crossroads to the Alamo." },
    { name: "The bomb on Press Hill", at: 21, note: "Just before 10:00 by Gresham (about 12:15 by the CENTCOM release): the lead F-14's bomb falls on the Peshmerga and the command vehicles at Press Hill, not the Iraqi tanks. The GM takes their losses from the account: 18 dead and about 45 wounded." },
    { name: "The Iraqis break", at: 96, note: "11:15 (Gresham): the Iraqis begin to break; a dozen try to surrender." },
  ],
  objective: { at: [ROAD, ALAMO(ROAD)], side: 1, name: "the Alamo, the low ridge north of the crossroads", radius: 12 },
  id: "debecka-2003", name: "The Debecka crossroads, 6 April 2003", sides: ["Americans and Kurds", "Iraqis"], table: "oif-oef-2001-wounds",
  travel: { map: "debecka-2003", place: "The Debecka crossroads", within: 1, sides: ["Americans and Kurds", "Iraqis"] },
  weather: "{cond: overcast, wind: breeze, dir: NW, ground: {mud: 0, snow: 0}}",
  grid, units,
  dumps: [{ at: [PRESS[0] + 14, PRESS[1] + 4], side: 0 }],   // ODB 390's "War Pigs", the cut-down 5-ton trucks that brought ammunition forward
  support: [
    { name: "The teams' 60 mm mortars", side: 0, kind: "mortar", tubes: 2 },
    { name: "Navy F/A-18s (close air support)", side: 0, kind: "fighter_bomber", tubes: 2 },
    { name: "Iraqi 120 mm mortars", side: 1, kind: "mortar", tubes: 2 },
  ],
  header: [
    `The Debecka crossroads on the morning of 6 April 2003, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 1.5 km east to west and`,
    "2,500 m north to south, north at the top: Press Hill, the second ridge, at the top; the low ridge the",
    "teams called the Alamo just below it; the crossroads and the berm along Highway 2 900 m south of the",
    "Alamo, the hardball road running north to south through the middle; the edge of Debecka to the",
    "south-east of the crossroads; open plain south to the board's edge.",
    "Generated by tools/maps/make_debecka_field.mjs: edit that file and re-run it rather than this one.",
    "The ridges, the crossroads and the town are drawn by hand to the distances the accounts give, not",
    "traced from any map; the deployment is the Iraqi counter-attack coming out of the haze, in our own",
    "words, with round numbers for play. Iraqi fire support is the two 120 mm mortars the official",
    "history saw (Gresham speaks of artillery too, a single account). Hazy, with low cloud. The",
    "Javelins were all fired at 2,200 m or more, the Iraqis first seen 2 km off: they come on at the",
    "board's south edge, about 2 km from the Alamo. How far Press Hill lay behind the Alamo no source",
    "gives: here about 300 m.",
    "",
    "What happened, briefly: on 6 April 2003 two Special Forces teams and about 80 Peshmerga broke",
    "through the Iraqi line on the ridge north of Debecka and held the crossroads for about 45 minutes.",
    "An Iraqi counter-attack of tanks and armoured carriers drove them back to a low ridge, where their",
    "Javelins knocked out the carriers and stopped the tanks. A Navy F-14 then bombed the Kurdish and",
    "American vehicles behind them by mistake, killing 18 and wounding about 45. By late morning the",
    "Iraqis had broken.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
