// Builds data/fields/redan-1855-june.yaml: the first British assault on the Great Redan at
// Sevastopol, at dawn on 18 June 1855, on the field map at 10 m a hex. Run from this folder after
// editing: node make_redan_june_field.mjs (no packages needed).
//
// Sources, all plain fact, and the drawing is ours: Lord Raglan's despatch of 19 June (in the
// Household Narrative of Current Events, 1855) and the published histories. Columns of
// detachments from the Light, 2nd and 4th Divisions were drawn up in the trenches: the right
// (Colonel Yea's) against the Redan's left face, a centre column against the salient, the left
// (Sir John Campbell's) against the re-entering angle formed by the right face and flank of the
// work, to the west (the faces are named from inside the work: the left face is the east one). When
// the French attack on the Malakhov ran into heavy fire at daybreak the two flank columns went
// out; the centre column never left the trenches (Engels, writing in 1855; and the losses fell
// almost all in the two flank columns' brigades), so it is not on the map. Riflemen covered them; sailors carried the
// ladders and soldiers the wool-bags. The open ground was about 400 m wide, the abatis was still
// whole, and the works were fully manned: grape and musketry from the Redan and the batteries on
// either side stopped the columns short of it, and their leaders fell. The work and the ground
// are drawn by redan_lib.mjs (here with the trench further out, the abatis whole and fewer shell
// holes); the deployment is our own reading, in our own words, with round numbers for play.
// The ditch is drawn deep (works.yaml `deep`): without ladders it costs most of a move to get
// down into and out of; the ladder parties marked as carrying ladders put them down into
// it where they reach it, and from then on everyone crosses it there as an ordinary ditch (Delhi
// 1857, the nearest well-recorded case: the time went on letting the ladders down; Simpson's
// ladder party of 320 placed theirs and the men "immediately stormed the parapet").
import { unit, writeField } from "./field_lib.mjs";
import { COLS, redan, BRITISH, RUSSIANS, RIFLE, MUSKET, GUNS, COMMON } from "./redan_lib.mjs";

const ROWS = 105;                            // about 910 m north to south
const { grid, hexWorks, edgeWorks } = redan({ rows: ROWS, trenchRow: 92, holes: 25, abatis: "whole" });   // the trench about 400 m from the salient

// ---------- the armies (pos is the middle of the front row) ----------
// A column: covering riflemen, the ladder and wool-bag party, the storming party and its supports.
const column = (label, col0) => [
  unit(`${label}: covering riflemen (Rifle Brigade)`, BRITISH, 100, { ...RIFLE, formation: "open", size: "company" }, [10, col0, 89]),
  unit(`${label}: ladders and wool-bags (sailors and soldiers)`, BRITISH, 170, { ...RIFLE, ladders: true, size: "company" }, [6, col0 + 2, 91]),
  unit(`${label}: storming party`, BRITISH, 400, { ...RIFLE, size: "battalion" }, [10, col0, 94]),
  unit(`${label}: supports`, BRITISH, 800, { ...RIFLE, quality: "green", size: "battalion" }, [12, col0 - 1, 98]),
];
const units = [
  ...column("Right column (Yea)", 65),        // Raglan: the right column against the left face (the east one: faces are named from inside the work)
  ...column("Left column (Campbell)", 25),     // the left against the re-entering angle by the right face (the west one)
  unit("Russian infantry at the salient", RUSSIANS, 600, { ...MUSKET, size: "battalion" }, [12, 44, 45]),
  unit("Guns on the right face", RUSSIANS, 40, { ...GUNS, size: "battery" }, [3, 35, 35]),
  unit("Guns on the left face", RUSSIANS, 40, { ...GUNS, size: "battery" }, [3, 62, 35]),
  unit("Battery on the line to the west", RUSSIANS, 60, { ...GUNS, size: "battery" }, [4, 15, 34]),
  unit("Battery on the line to the east", RUSSIANS, 60, { ...GUNS, size: "battery" }, [4, 70, 33]),
  unit("Russian infantry behind the breastwork", RUSSIANS, 1600, { ...MUSKET, size: "regiment" }, [26, 37, 24]),
  unit("Riflemen on the line to the west", RUSSIANS, 200, { ...MUSKET, weapon: "rifle_musket", formation: "open", size: "company" }, [10, 2, 34]),
  unit("Riflemen on the line to the east", RUSSIANS, 200, { ...MUSKET, weapon: "rifle_musket", formation: "open", size: "company" }, [10, 82, 33]),
  unit("Russian reserve in the Karabelnaya", RUSSIANS, 2000, { ...MUSKET, size: "brigade" }, [40, 30, 12]),
];

writeField({
  phases: [   // an exchange is about a minute; the times are our reading of the accounts, rounded
    { name: "The columns go out", at: 1, note: "At daybreak the riflemen, the ladder and wool-bag parties and the storming parties leave the trenches under grape and musketry." },
    { name: "The supports follow", at: 4, note: "The supports come out behind the storming parties.", arrive: ["Right column (Yea): supports", "Left column (Campbell): supports"] },
    { name: "The Russian reserve comes up", at: 15, note: "The reserve in the Karabelnaya comes up to the line; by now the attack is failing and is soon called off.", arrive: ["Russian reserve in the Karabelnaya"] },
  ],
  ...COMMON,
  id: "redan-1855-june", name: "The Great Redan, 18 June 1855",
  weather: "{cond: fair, wind: calm, ground: {mud: 0, snow: 0}}",   // daybreak, but light enough: the columns were under fire as soon as they left the trenches
  grid, units, hexWorks, edgeWorks, deep: ["ditch"],
  header: `The first British assault on the Great Redan, Sevastopol, 18 June 1855, at dawn, at 10 m a hex: ${COLS} x ${ROWS}
hexes, about 1000 m east to west and 910 m north to south, north at the top: the Redan's point
toward the British trench at the bottom, about 400 m away, the Karabelnaya suburb behind it.
Generated by tools/maps/make_redan_june_field.mjs: edit that file and re-run it rather than this one.
The work and the ground are drawn by hand to the shape the accounts give, not traced from any
map (the point is cut off square, 120 m across, so that units in line can reach it); the
deployment is our own reading, in our own words, with round numbers for play.
The ditch is deep: without ladders it costs most of a move to cross; the ladder parties are
marked as carrying ladders, and where they reach the ditch the ladders go down and it is crossed as an ordinary ditch.

What happened, briefly: the French and British were to storm the Malakhov and the Redan together
after a bombardment, but the Russians had repaired their works in the night and saw the French
forming. The French went in early and piecemeal and were thrown back. At daybreak Lord Raglan
sent the two flank columns out of the trenches (the centre column, meant to follow, never left
them, and is not on the map): riflemen in front, sailors with the ladders,
soldiers with wool-bags, then the storming parties. Grape and musketry from the Redan and the
batteries either side swept the open ground, and the abatis in front of the work was still
whole. The leading men fell within yards of the trenches; Colonel Yea and Sir John Campbell
were killed, and the attack was called off. Some 1,400 British were killed, wounded or
missing.`.split("\n"),
});
console.log(grid.map(r => r.join("")).join("\n"));
