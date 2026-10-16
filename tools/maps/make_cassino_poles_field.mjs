// Builds data/fields/cassino-poles-1944.yaml: the 2nd Polish Corps' night attack on Point 593 and
// Phantom Ridge, 12 May 1944, on the field map at 10 m a hex. Run from this folder after editing:
// node make_cassino_poles_field.mjs
//
// Sources, all public domain or plain fact, and the drawing is ours: the plain facts of the
// battle as the official histories give them and as they are summarised publicly. At 01:00 on
// 12 May, after a great bombardment, the 3rd Carpathian Rifle Division attacked Point 593 and the
// 5th Kresowa Division the ridges to the west, against the German 1st Parachute Division; they
// took and lost Point 593 that day, and held on until the Germans gave up the massif on the 17th;
// on the 18th a Polish patrol raised the flag over the abbey. The ground (cassino_massif.mjs) is
// drawn by hand, not traced from any map, and approximate; the deployment is the attack going in,
// in our own words, with round numbers for play.
import { N, S, unit, writeField } from "./field_lib.mjs";
import { COLS, ROWS, P593, P444, ABBEY, PHANTOM, massif } from "./cassino_massif.mjs";

const grid = massif();
const PL = { side: 0, facing: S }, DE = { side: 1, facing: N };
const POLE = { quality: "veteran", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false };
const PARA = { quality: "veteran", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false, prone: true };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "ww2_rifleman", formation: "mg", mounted: false, prone: true };
const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
// A battalion as companies (company 1, 2, ...) side by side across its front, a hex apart, centred on col at row: men each, the
// battalion's men per hex of front kept (width: the companies' width)
const companies = (name, where, army, kind, [men, width], [col, row], facing) => men.map((m, k) => ({ ...at(`${name}, company ${k + 1} (${where})`, army, m, kind, width, [Math.round(col + (k - (men.length - 1) / 2) * (width + 1)), row], facing), size: "company" }));
const units = [
  ...companies("1st Carpathian Rifle Brigade, 2nd Battalion", "for Point 593", PL, POLE, [[225, 225, 225, 225], 8], [P593[0] + 4, 12], S),
  ...companies("1st Carpathian Rifle Brigade, 1st Battalion", "along Snakeshead, for Albaneta", PL, POLE, [[175, 175, 175, 175], 6], [P444[0] - 10, 30], S),
  ...companies("5th Kresowa Division", "for Phantom Ridge", PL, POLE, [[225, 225, 225, 225], 8], [PHANTOM[0] + 4, 30], S).map(u => ({ ...u, via: [[PHANTOM[0], PHANTOM[1] - 4]] })),   // for Phantom Ridge first, then 593
  at("German paratroops on Point 593", DE, 150, PARA, 10, [P593[0], P593[1] + 2], N),
  at("German paratroops on Phantom Ridge", DE, 150, PARA, 12, [PHANTOM[0] + 2, PHANTOM[1] + 2], N),
  at("German paratroops on Point 444", DE, 100, PARA, 10, [P444[0], P444[1] + 1], N),
  at("Germans in the abbey's ruins", DE, 200, PARA, 18, [ABBEY[0], ABBEY[1] - 4], N),
  at("German machine guns (Point 593)", DE, 15, MG, 3, [P593[0] + 8, P593[1] + 4], N),
  at("German machine guns (Phantom Ridge)", DE, 10, MG, 2, [PHANTOM[0] + 12, PHANTOM[1] + 6], N),
];

writeField({
  phases: [   // an exchange is about a minute; times and sources in the project's battle-phases research (round 2), rounded; (est.) marks an estimate
    { name: "The advance", at: 1, note: "01:00 on 12 May, after the bombardment: the 1st Battalion goes for Albaneta and the Kresowa for Phantom Ridge." },
    { name: "For Point 593", at: 31, note: "01:30: the 2nd Battalion sets off for Point 593.", arrive: [1, 2, 3, 4].map(k => `1st Carpathian Rifle Brigade, 2nd Battalion, company ${k} (for Point 593)`) },
    { name: "Point 593 taken", at: 61, note: "About 02:00 to 02:30: Point 593 is taken, then held against counter-attack after counter-attack." },
    { name: "Forced off 593", at: 461, note: "About 08:40 the Poles are forced off 593 by the fifth German attack (one source)." },
    { name: "Abandon 593", at: 721, note: "After 13:00 the decision is taken to abandon 593; at 15:00 the 1st Battalion is ordered back." },
    { name: "The last men leave", at: 1111, note: "19:30: the last men of 4th Company leave 593." },
  ],
  objective: { at: P593, side: 0, name: "Point 593", radius: 4 },
  id: "cassino-poles-1944", name: "The Poles at Point 593 and Phantom Ridge, 12 May 1944", sides: ["Allies", "Germans"], table: "owens-wwii",
  travel: { map: "cassino-1944", place: "Phantom Ridge", within: 1, sides: ["Allies", "Germans"] },
  weather: "{cond: fair, wind: calm, light: night, ground: {mud: 0, snow: 0}}",
  grid, units,
  support: [
    { name: "Polish and British field guns", side: 0, kind: "field", tubes: 36 },
    { name: "Medium and heavy guns", side: 0, kind: "howitzer", tubes: 12 },
    { name: "Mortars", side: 0, kind: "mortar", tubes: 12 },
    { name: "German mortars and Nebelwerfers", side: 1, kind: "mortar", tubes: 12 },
    { name: "German guns", side: 1, kind: "field", tubes: 8 },
  ],
  header: [
    `Point 593, Phantom Ridge and the abbey of Monte Cassino on the night of 11-12 May 1944, at 10 m a hex: ${COLS} x ${ROWS}`,
    "hexes, about 2000 m east to west and 1300 m north to south, north at the top: Point 593 at the",
    "upper left, Phantom Ridge to the west, Snakeshead Ridge running down past Point 444 to the",
    "abbey's ruins at the lower right.",
    "Generated by tools/maps/make_cassino_poles_field.mjs (the ground is cassino_massif.mjs): edit",
    "Light cover (scrub, key o): the thorn scrub on the steep slopes among the broken rock.",
    "them and re-run it rather than this file.",
    "The ground is drawn by hand to the shape the accounts give, not traced from any map; the",
    "deployment is the attack going in, in our own words, with round numbers for play. Dark: the",
    "attack went in at 01:00.",
    "",
    "What happened, briefly: in the fourth battle the 2nd Polish Corps (General Wladyslaw Anders)",
    "attacked the massif from the north at 01:00 on 12 May after an enormous bombardment. The",
    "1st Carpathian Rifle Brigade made the attack: its 2nd Battalion took Point 593 about 02:00 and",
    "was thrown off it in the morning, its 1st went for Albaneta; the last men left 593 at 19:30.",
    "The Kresowa Division fought on Phantom Ridge.",
    "Losses were very heavy on both sides. With the French and British through the Gustav Line in",
    "the valleys, the paratroops gave up the massif on the 17th, and a Polish patrol raised the flag",
    "over the abbey on the morning of the 18th.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
