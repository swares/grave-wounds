// Builds data/fields/redan-1855.yaml: the British assault on the Great Redan at Sevastopol,
// 8 September 1855, on the field map at 10 m a hex. Run from this folder after editing:
// node make_redan_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours: the Redan was a V-shaped earthwork with its
// point (the salient) toward the British trenches, a deep ditch (15 to 20 feet) and a parapet
// along its two faces, joined to the Russian line on either side and open at the back (the
// gorge), with breastworks and traverses inside. The British advanced trench was about 200
// yards from the salient; the abatis in front had been mostly smashed by the bombardment. The
// work and the ground are drawn by redan_lib.mjs. The deployment is just after
// noon, when the stormers went over, in our own words; numbers are round figures for play.
// The point of the salient is drawn cut off square, a front of 12 hexes (120 m): a simplification
// for the field map, whose units stand in straight lines and could not otherwise reach the men
// in a sharp point. The Russian infantry are on smoothbore muskets (most of them still were), their riflemen on
// rifles; the British on the rifle-musket. The Barrack Battery, on the line to the west, is on the
// map (Russell: it swept the stormers with grape). The British siege batteries are not: they ceased
// firing at noon, when the French went in, and the Redan's own heavy guns are the guns on its faces.
// The ditch is drawn deep (works.yaml `deep`): without ladders it costs most of a move to get
// down into and out of; the ladder party marked as carrying ladders put them down into
// it where they reach it, and from then on everyone crosses it there as an ordinary ditch (Delhi
// 1857, the nearest well-recorded case: the time went on letting the ladders down; Simpson's
// ladder party of 320 placed theirs and the men "immediately stormed the parapet").
import { unit, writeField } from "./field_lib.mjs";
import { COLS, redan, BRITISH, RUSSIANS, RIFLE, MUSKET, GUNS, COMMON } from "./redan_lib.mjs";

const ROWS = 80;                             // about 690 m north to south
const { grid, hexWorks, edgeWorks } = redan({ rows: ROWS, trenchRow: 67, holes: 14, abatis: "scatter" });   // the trench about 200 yards from the salient; the abatis mostly smashed

// ---------- the armies (pos is the middle of the front row) ----------
const units = [
  unit("Covering party (2nd Rifle Brigade and the Buffs)", BRITISH, 200, { ...RIFLE, formation: "open", size: "company" }, [20, 40, 63]),
  unit("Ladder party (the Buffs and the 97th)", BRITISH, 320, { ...RIFLE, ladders: true, size: "company" }, [10, 45, 65]),
  // Simpson's about 1,000 stormers, half from each division (the Household Narrative: 760 from the 2nd alone)
  unit("Light Division stormers (90th and 97th)", BRITISH, 500, { ...RIFLE, size: "regiment" }, [20, 28, 68]),
  unit("2nd Division stormers (the Buffs, 41st and 62nd)", BRITISH, 500, { ...RIFLE, quality: "green", size: "regiment" }, [16, 50, 68]),
  unit("Supports (7th, 23rd, 33rd, 34th and 77th)", BRITISH, 1500, { ...RIFLE, quality: "green", size: "brigade" }, [30, 35, 74]),
  unit("Vladimirski Regiment, at the salient", RUSSIANS, 400, { ...MUSKET, size: "battalion" }, [12, 44, 45]),
  unit("Guns on the right face", RUSSIANS, 40, { ...GUNS, size: "battery" }, [3, 35, 35]),   // the faces named from inside the work: the right face is the west one
  unit("Guns on the left face", RUSSIANS, 40, { ...GUNS, size: "battery" }, [3, 62, 35]),
  unit("Vladimirski Regiment, behind the breastwork", RUSSIANS, 1400, { ...MUSKET, size: "regiment" }, [26, 37, 24]),
  unit("Riflemen on the line to the west", RUSSIANS, 300, { ...MUSKET, weapon: "rifle_musket", formation: "open", size: "company" }, [10, 6, 34]),
  // Russell: the stormers "were swept by the guns of the Barrack Battery and by several pieces on the
  // proper right of the Redan, loaded heavily with grape"; the Barrack Battery stood on the line west of the Redan
  unit("Barrack Battery, on the line to the west", RUSSIANS, 60, { ...GUNS, size: "battery" }, [4, 16, 34]),
  unit("Iakutski and Selenginski regiments (reserve)", RUSSIANS, 2000, { ...MUSKET, size: "brigade" }, [40, 30, 12]),
];

writeField({
  ...COMMON,
  id: "redan-1855", name: "The Great Redan, 8 September 1855",
  phases: [   // an exchange is about a minute; the times are our reading of the accounts, rounded
    { name: "The stormers go over", at: 1, note: "On the French signal from the Malakhov, the covering party, the ladders and the stormers leave the advanced trench." },
    { name: "The supports come forward", at: 10, note: "The supports follow up piecemeal and crowd into the salient behind the stormers.", arrive: ["Supports (7th, 23rd, 33rd, 34th and 77th)"] },
    { name: "The Russian counter-attack", at: 50, note: "After nearly an hour (Simpson's despatch) the Russian reserves come up from the Karabelnaya and drive the British back over the parapet.", arrive: ["Iakutski and Selenginski regiments (reserve)"] },
  ],
  weather: "{cond: fair, wind: strong, dir: N, ground: {mud: 0, snow: 0}}",
  grid, units, hexWorks, edgeWorks, deep: ["ditch"],
  header: `The British assault on the Great Redan, Sevastopol, 8 September 1855, at 10 m a hex: ${COLS} x ${ROWS}
hexes, about 1000 m east to west and 690 m north to south, north at the top: the Redan's point
toward the British trench at the bottom, the Karabelnaya suburb behind it at the top.
Generated by tools/maps/make_redan_field.mjs: edit that file and re-run it rather than this one.
The work, its ditch, the line either side, the breastwork, the trench, the ravines and the
shell holes are drawn by hand to the shape the accounts give, not traced from any map (the
point is cut off square, 120 m across, so that units in line can reach it); the
deployment is just after noon, in our own words, with round numbers for play.
The ditch is deep: without ladders it costs most of a move to cross; the ladder party is
marked as carrying ladders, and where it reaches the ditch the ladders go down and it is crossed as an ordinary ditch.

What happened, briefly: after three days' bombardment the French stormed the Malakhov, east
of the Redan, at noon and held it. On their signal the British went over from the advanced
trench, about 200 yards out: a covering party of riflemen, the ladder party, then the
stormers of the Light and 2nd Divisions. Many fell crossing the open ground, swept with grape
from the guns on the Redan's flank and from the Barrack Battery to the west; the ladders were
too few and some too short, but men got down into the ditch and up onto the salient. There
they stopped and fired from the parapet instead of pressing on, while the Russians fired back
from behind their breastwork and traverses and their reserves came up. The supports came
forward piecemeal and crowded into the salient. After nearly an hour, Simpson says, a Russian
counter-attack drove them back over the parapet and the ditch. That night the Russians blew
up their works and left the south side of the town. It was a cold day, with a strong wind
and dust.`.split("\n"),
});
console.log(grid.map(r => r.join("")).join("\n"));
