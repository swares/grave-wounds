// Builds data/fields/beaumont-hamel-1916.yaml: the 29th Division's attack at Beaumont-Hamel on
// 1 July 1916, the first day of the Somme, over the ground of the Newfoundland Memorial Park, on
// the field map at 10 m a hex. Run from this folder after editing: node make_beaumont_field.mjs (no
// packages needed).
//
// Sources, all plain fact, and the drawing is ours (project doc "beaumont-research"): Veterans
// Affairs Canada, The Rooms and the Newfoundland Regiment Museum after Nicholson, the regiment's
// and the 1st Inniskillings' war diaries, Wikipedia after Middlebrook and the RIR 119 history.
// St John's Road (the support trench the Newfoundlanders went over from) about 230 m behind the
// British front line, which stood on the crest; no man's land about 400 m wide opposite Y Ravine,
// falling to the German line in a shallow valley, the Danger Tree about halfway; the British wire
// with too few lanes cut, the German wire thick and intact; the German front system three trenches
// deep, with deep dugouts every 46 m; Y Ravine, 6 m deep and 9 m wide, forking at its west end by
// the German front line and running east, its dugouts housing a battalion. The 87th Brigade went at
// 07:30 (2nd SWB and 1st Inniskillings, then 1st KOSB and 1st Border at 07:35); the Newfoundlanders
// left St John's Road at 09:15, alone, A and B Companies in front and C and D 100 yards behind; the
// 1st Essex came up on their right at 10:50 (the Essex war diary and Veterans Affairs; 09:55 by the
// Museum). No source gives
// RIR 119's companies or its machine guns here: those, the British battalions' strengths but the
// Inniskillings' and the Newfoundlanders', and where each stood are ours, with round numbers. The
// lines, the slope and the ravine are drawn to those distances, not traced from a trench map.
import { N, S, wobble, speckle, groundGrid, unit, writeField } from "./field_lib.mjs";

// EAST is at the top: the columns run from north (left, towards Hawthorn Ridge) to south (right,
// towards the Mary Redan), the rows from east (the German rear, top) to west (St John's Road, bottom).
const COLS = 80, ROWS = 116;                  // 800 m north to south, about 1000 m east to west
const ST_JOHNS = 112, BRIT = 85;              // St John's Road; the British front line (on the crest)
const GER = 39;                               // the German front line: about 400 m from the British
const TRENCH = (base, c, a) => base + Math.round(wobble(c / 6, a, a + 1.1) * 0.6);
const RAVINE = r => 20 + Math.round(wobble(r / 6, 0.8, 2.0) * 1.2);   // Y Ravine's line, running east (up)
const DANGER_TREE = [36, 62];

function inRavine(c, r){                      // the ravine and the two arms at its west end
  if (r <= GER - 4) return Math.abs(c - RAVINE(r)) <= 1;
  if (r <= GER) return Math.abs(c - (RAVINE(r) - (r - GER + 4))) <= 1 || Math.abs(c - (RAVINE(r) + (r - GER + 4))) <= 1;
  return false;
}
function ground(c, r){
  if (inRavine(c, r)) return "r";                                         // Y Ravine: deep, out of sight
  if (c === DANGER_TREE[0] && r === DANGER_TREE[1]) return "o";            // the Danger Tree, stripped
  if (r >= BRIT - 6 && r <= BRIT + 4) return "h";                          // the crest the British line stood on: men crossing it are on the skyline
  if (r > BRIT + 4) return speckle(c, r, 9) ? "o" : "s";                   // the slight incline down to St John's Road
  if (r > GER + 2) return speckle(c, r, 12) ? "o" : ".";                   // no man's land: grass and shell holes, falling gently to the German wire
  return speckle(c, r, 10) ? "o" : ".";                                    // the German side
}
const grid = groundGrid(COLS, ROWS, ground);

// ---------- the trenches, the wire, the dugouts ----------
const line = (base, a, skip) => Array.from({ length: COLS }, (_, c) => [c, TRENCH(base, c, a)]).filter(h => !inRavine(h[0], h[1]) && !skip?.(h));
const stJohns = line(ST_JOHNS, 0.3), britFront = line(BRIT, 1.7);
const assembly = line(BRIT + 11, 2.5);                                    // the assembly and support trenches between (our drawing)
const gerFront = line(GER, 0.9), gerSecond = line(GER - 9, 2.2), gerThird = line(GER - 18, 0.4);
const dugouts = [...gerFront.filter(h => h[0] % 5 === 2), ...gerSecond.filter(h => h[0] % 7 === 3),        // every 46 m along the front trench
  [RAVINE(GER - 8) - 2, GER - 8], [RAVINE(GER - 8) + 2, GER - 8], [RAVINE(GER - 20) - 2, GER - 20], [RAVINE(GER - 20) + 2, GER - 20]];   // and in the ravine's sides
const stores = dugouts.filter((h, i) => i % 2 === 0).map(at => ({ at, side: 1 }));   // ammunition in the dugouts: the machine guns fired all morning (our placing)
const isDugout = h => dugouts.some(d => d[0] === h[0] && d[1] === h[1]);
const trench = [...stJohns, ...britFront, ...assembly, ...gerFront, ...gerSecond, ...gerThird].filter(h => !isDugout(h));
const britWire = [], gerWire = [];
for (let c = 0; c < COLS; c++){
  if (c % 8 >= 2) britWire.push([c, TRENCH(BRIT, c, 1.7) - 3]);           // lanes cut every 80 m, two hexes wide: too few
  for (const k of [3, 4, 5]) if (!speckle(c, k, 14) && !inRavine(c, TRENCH(GER, c, 0.9) + k)) gerWire.push([c, TRENCH(GER, c, 0.9) + k]);   // thick, a few shell gaps
}

// ---------- the armies (pos is the middle of the front row; "north" here is east, towards the Germans) ----------
const BR = { side: 0, facing: N }, GE = { side: 1, facing: S };
const WAVE = { quality: "veteran", weapon: "rifle_service", kit: "ww2_rifleman", formation: "extended", mounted: false };   // Brodie helmets, 170 rounds, two Mills bombs
const NFLD = { ...WAVE, quality: "regular" };                                                                            // Gallipoli, but no set-piece attack before
const HOLD = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "extended", mounted: false, prone: true };
const MG = { quality: "veteran", weapon: "machine_gun", kit: "none", formation: "mg", mounted: false, prone: true };
const RESERVE = { quality: "veteran", weapon: "rifle_service", kit: "none", formation: "close", mounted: false, prone: true };
const units = [
  unit("2nd South Wales Borderers (first wave, on Y Ravine)", BR, 700, WAVE, [36, 4, BRIT - 1]),
  unit("1st Royal Inniskilling Fusiliers (first wave, the right)", BR, 950, WAVE, [38, 41, BRIT - 1]),
  unit("1st Border (second wave)", BR, 832, WAVE, [36, 4, BRIT + 10]),
  unit("1st King's Own Scottish Borderers (second wave)", BR, 700, WAVE, [38, 41, BRIT + 10]),
  unit("1st Newfoundland Regiment, A and B Companies", BR, 390, NFLD, [44, 6, 104]),
  unit("1st Newfoundland Regiment, C and D Companies", BR, 390, NFLD, [44, 6, 111]),
  unit("1st Essex, two leading companies", BR, 360, WAVE, [24, 54, 108]),
  unit("RIR 119, front-line company (Y Ravine)", GE, 150, HOLD, [25, 2, GER]),
  unit("RIR 119 machine guns at the head of Y Ravine", GE, 10, MG, [2, 27, GER]),
  unit("RIR 119, front-line company (the south)", GE, 150, HOLD, [25, 31, GER]),
  unit("RIR 119 machine guns in the front trench", GE, 10, MG, [2, 56, GER]),
  unit("RIR 119 machine guns behind, on the right", GE, 10, MG, [2, 62, GER - 9]),
  unit("RIR 119 machine guns on the right (enfilade)", GE, 10, MG, [2, 70, GER]),
  unit("RIR 119, the company in Y Ravine", GE, 200, RESERVE, [3, 21, GER - 6]),
  unit("RIR 119, the support company (third trench)", GE, 150, HOLD, [30, 42, GER - 19]),
];

writeField({
  phases: [   // an exchange is about a minute; BEF time (GMT+1); sunrise 04:43 (project doc "beaumont-research")
    { name: "Zero", at: 1, note: "07:30: the barrage lifts off the German front line and walks back 100 yards every two minutes; the 2nd SWB and 1st Inniskillings go over. Ten minutes ago the Hawthorn Ridge mine went up to the north, and the Germans are up from their dugouts." },
    { name: "The second wave", at: 6, note: "07:35: the 1st KOSB and 1st Border leave the assembly trenches into the machine-gun fire.", arrive: ["1st Border (second wave)", "1st King's Own Scottish Borderers (second wave)"] },
    { name: "White rockets", at: 31, note: "About 08:00: German white signal rockets are taken for British success flares; the 88th Brigade is told to go forward." },
    { name: "The order", at: 76, note: "08:45: 'the 1st Essex and 1st Newfoundland Regiment will advance as soon as possible', to take the German first trench and clear to Station Road." },
    { name: "The Newfoundlanders go over", at: 106, note: "09:15: from St John's Road, over the open, alone and without the Essex or artillery, the sun 40 degrees up ahead of them; men fall in heaps at the gaps in their own wire.", arrive: ["1st Newfoundland Regiment, A and B Companies", "1st Newfoundland Regiment, C and D Companies"] },
    { name: "Hadow reports", at: 136, note: "09:45: the commanding officer reports that the attack has failed." },
    { name: "The Essex", at: 201, note: "10:50, by the Essex war diary and Veterans Affairs (09:55 by the Museum): the Essex's two leading companies go forward on the right, after a halt order that never reached them.", arrive: ["1st Essex, two leading companies"] },
  ],
  ends: { at: 221, why: "from zero at 07:30 to the Essex's attack at 10:50 and its halt by about 11:10 (our cut: the line was quiet by afternoon, the 88th Brigade taking it over at 14:00)" },
  objective: { at: [30, GER], side: 0, name: "the German front line at Y Ravine", radius: 10 },
  id: "beaumont-hamel-1916", name: "Beaumont-Hamel, 1 July 1916 (the Newfoundland Park)", sides: ["British", "Germans"], table: "wwi-1914-18-wounds",
  travel: { map: "beaumont-hamel-1916", place: "Newfoundland Park (the battlefield)", within: 1, sides: ["British", "Germans"] },
  up: "E",
  weather: "{cond: fair, wind: calm, dir: W, ground: {mud: 0, snow: 0}}",
  grid, units,
  hexWorks: { trench, bunker: dugouts, wire: [...britWire, ...gerWire] },
  dumps: stores,
  support: [
    { name: "German field guns (the Sperrfeuer on the British trenches)", side: 1, kind: "field", tubes: 12 },
    { name: "German howitzers", side: 1, kind: "howitzer", tubes: 4 },
  ],
  header: [
    `Beaumont-Hamel, 1 July 1916, at 10 m a hex: ${COLS} x ${ROWS} hexes, about 800 m north to south and 1000 m east to west, EAST at`,
    "the top: St John's Road across the bottom, the British front line on the crest, the British wire",
    "and its few lanes, no man's land falling to the German wire and the German front system across",
    "the middle, Y Ravine running up from it on the left (north), the Danger Tree halfway across.",
    "Generated by tools/maps/make_beaumont_field.mjs: edit that file and re-run it rather than this one.",
    "The lines, the slope and the ravine are drawn to the distances the sources give, not traced from",
    "a trench map; the narrowing of no man's land to the north-west is off this board. RIR 119's",
    "companies and machine guns here are not known: those, and the British battalions' strengths (but",
    "the Inniskillings' 952 and the Newfoundlanders' 780), are ours, with round numbers. The British",
    "barrage lifted at zero and is not on call; the German field guns are. The Germans wear no steel",
    "helmets (whether RIR 119 had them on 1 July is not known); the British wear the Brodie. The",
    "German ammunition is in the dugouts (supply dumps); no man's land plays as open ground, falling",
    "only in the account (a slope hex would hide the forward slope from the German line).",
    "",
    "What happened, briefly: after a week's bombardment the 29th Division attacked at 07:30 against",
    "RIR 119, who had come up from their dugouts when the Hawthorn Ridge mine went up ten minutes",
    "early. The 87th Brigade's waves were cut down in no man's land and at the German wire; only",
    "parts of the Inniskillings got in. German white rockets were taken for British success signals,",
    "and at 09:15 the 1st Newfoundland Regiment went over from St John's Road, alone and in full view.",
    "Within twenty minutes most were down, few beyond the Danger Tree. Of 780, 684 to 710 were killed",
    "or wounded, and 68 answered the roll call the next day; RIR 119 lost 292 men all day.",
  ],
});
console.log(grid.map(r => r.join("")).join("\n"));
