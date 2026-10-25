// The Monte Cassino massif at 10 m a hex, shared by the February and May battlefields
// (make_cassino_monastery_field.mjs, make_cassino_poles_field.mjs): Point 593 at the north-west,
// Snakeshead Ridge running south-east from it to Point 444 and the ruined abbey, Phantom Ridge to
// the west, the gullies between. Drawn by hand to the shape the accounts give (narrow rocky
// ridges, steep scrubby slopes, boulders and gullies), not traced from any map, and approximate.
import { wobble, patch, speckle, groundGrid } from "./field_lib.mjs";

export const COLS = 200, ROWS = 150;          // 2000 m east to west, about 1300 m north to south
export const P593 = [60, 34], P444 = [112, 72], ABBEY = [150, 112], PHANTOM = [22, 60];
const lerp = (a, b, t) => a + (b - a) * t;
function nearRidge(c, r, a, b, w){            // within w hexes of the ridge line from a to b
  const dx = b[0] - a[0], dy = b[1] - a[1], t = Math.max(0, Math.min(1, ((c - a[0]) * dx + (r - a[1]) * dy) / (dx * dx + dy * dy)));
  return Math.hypot(c - lerp(a[0], b[0], t), r - lerp(a[1], b[1], t)) <= w + wobble((c + r) / 6, 0.4, 1.2) * 0.6;
}
function kind(c, r){
  if (patch(c, r, { cx: ABBEY[0], cy: ABBEY[1], rx: 11, ry: 8, a: 0.3, b: 1.7 })) return speckle(c, r, 6) ? "r" : "x";   // the abbey's ruins
  if (patch(c, r, { cx: P593[0], cy: P593[1], rx: 7, ry: 6, a: 1.1, b: 0.2 })) return speckle(c, r, 3) ? "r" : "h";    // Point 593's rocky top
  if (patch(c, r, { cx: P444[0], cy: P444[1], rx: 6, ry: 5, a: 0.8, b: 2.0 })) return speckle(c, r, 3) ? "r" : "h";    // Point 444
  if (nearRidge(c, r, P593, ABBEY, 4) || nearRidge(c, r, PHANTOM, P593, 3)) return speckle(c, r, 4) ? "r" : "h";       // Snakeshead and Phantom Ridges: narrow and rocky
  if (Math.abs(r - (96 + wobble(c / 7, 0.9, 0.2) * 1.5) + c * 0.15) <= 1 && c < 120) return "r";                       // a gully, boulders
  return speckle(c, r, 3) ? "o" : "r";                                                                                 // steep slopes: scrub, broken rock
}
export const massif = () => groundGrid(COLS, ROWS, kind);
// The header lines the massif's battlefields share: the scrub, and how the ground and the deployment are drawn.
export const MASSIF_NOTES = [
  "Light cover (scrub, key o): the thorn scrub on the steep slopes among the broken rock.",
  "The ground is drawn by hand to the shape the accounts give, not traced from any map; the",
  "deployment is the attack going in, in our own words, with round numbers for play.",
];
