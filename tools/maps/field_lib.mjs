// Shared drawing for the battlefields (make_agincourt_field.mjs, make_towton_field.mjs): a field
// map of 10 m pointy-top hexes, ground painted as rows of letters (units.yaml ground keys), works
// and the armies as drawn up, written to data/fields/<id>.yaml.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");

// Facing 1 is north, 4 is south (the corner between two hexsides; see docs/units.md).
export const N = 1, S = 4;

// A smooth wobble for drawn edges: a sum of sines, fixed so the file is the same each run.
export const wobble = (r, a, b) => 1.4 * Math.sin(r / 5.3 + a) + 0.8 * Math.sin(r / 2.1 + b);
export const lerp = (a, b, t) => a + (b - a) * t;
// A fixed scatter: true for about one hex in n, with no pattern to the eye (a hash of the hex).
export function speckle(c, r, n){
  let h = Math.imul(c, 374761393) + Math.imul(r, 668265263);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  return ((h ^ (h >>> 16)) >>> 0) % n === 0;
}
// Whether hex (c, r) is inside a rounded, uneven patch: an ellipse {cx, cy, rx, ry} whose edge
// wobbles by the phases {a, b}.
export function patch(c, r, { cx, cy, rx, ry, a = 0, b = 0 }){
  return ((c - cx) / rx) ** 2 + ((r - cy) / ry) ** 2 <= 1 + 0.12 * wobble(Math.atan2(r - cy, c - cx) * 6, a, b);
}

// A ground grid, each hex's letter from kind(col, row); paint() fills a rectangle.
export function groundGrid(cols, rows, kind){
  const grid = Array.from({ length: rows }, (_, r) => Array.from({ length: cols }, (_, c) => kind(c, r)));
  grid.paint = (c0, c1, r0, r1, k) => { for (let r = r0; r <= r1; r++) for (let c = c0; c <= c1; c++) grid[r][c] = k };
  return grid;
}

// The middle of a front row that starts at col0: facing north the row runs east from its
// middle's west side, facing south the other way, so an even width puts the middle one further east.
function middle(col0, width, facing){
  const half = Math.floor((width - 1) / 2);
  return facing === S && width % 2 === 0 ? col0 + half + 1 : col0 + half;
}
// A unit: army {side, facing}, kind {quality, weapon, kit, formation, mounted, guns (a battery's: rifled
// or howitzer; smoothbore if left out), prone (gone to ground: dug in)}, at [width, first col, front row].
export function unit(name, army, men, kind, at){
  const [width, col0, row] = at;
  return { name, ...army, men, ...kind, width, pos: [middle(col0, width, army.facing), row] };
}
// The first column of a unit's front row (facing north).
export const firstCol = u => u.pos[0] - Math.floor((u.width - 1) / 2);

const yq = s => JSON.stringify(s);
const unitLine = u => `  - {name: ${yq(u.name)}, side: ${u.side}, men: ${u.men}, quality: ${u.quality}, weapon: ${u.weapon}, kit: ${u.kit}, formation: ${u.formation}, width: ${u.width}, pos: [${u.pos.join(", ")}], facing: ${u.facing}${u.mounted ? ", mounted: true" : ""}${u.guns ? ", guns: " + u.guns : ""}${u.prone ? ", prone: true" : ""}${u.lands === undefined ? "" : ", lands: " + u.lands}${u.vehicle ? ", vehicle: " + u.vehicle : ""}${u.fixed ? ", fixed: [" + u.fixed.join(", ") + "]" : ""}}`;
const hexList = hs => hs.map(h => `[${h.join(", ")}]`).join(", ");

// Writes the battlefield file. spec: {id, script, header (comment lines), name, sides, table,
// travel {map, place, within, sides}, weather (YAML flow text), grid, hexWorks {type: [hexes]},
// edgeWorks {type: [[hex, hex], ...]} (the first hex of each pair the high or inner side), units,
// up (the compass point at the top of the map, if not north), support (each side's batteries on
// call: [{name, side (0 or 1), kind (units.yaml indirect.kinds), tubes}]), lz (landing zones,
// hexes; a unit with `lands: k` comes in by air at the k-th)}.
export function writeField(spec){
  const { grid } = spec, works = Object.entries(spec.hexWorks || {});
  const edges = Object.entries(spec.edgeWorks || {});
  const workLine = ([type, hs]) => `    - {type: ${type}, at: [${hexList(hs)}]}`;
  const edgeLine = ([type, pairs]) => `    - {type: ${type}, at: [${pairs.map(pr => "[" + hexList(pr) + "]").join(", ")}]}`;
  const hexText = works.length ? "  hexes:\n" + works.map(workLine).join("\n") + "\n" : "";
  const edgeText = edges.length ? "  edges:\n" + edges.map(edgeLine).join("\n") + "\n" : "";
  const worksText = hexText || edgeText ? "works:\n" + hexText + edgeText : "";
  const supText = (spec.support || []).length ? "# Batteries on call (off the map): loading the field fills the Fire support panel.\nsupport:\n"
    + spec.support.map(s => `  - {name: ${yq(s.name)}, side: ${s.side}, kind: ${s.kind}, tubes: ${s.tubes}}`).join("\n") + "\n" : "";
  const t = spec.travel, upLine = spec.up ? "up: " + spec.up + "                       # the compass point at the top of the map\n" : "";
  const out = `${spec.header.map(l => ("# " + l).trimEnd()).join("\n")}
id: ${spec.id}
name: ${yq(spec.name)}
${spec.period ? "period: " + yq(spec.period) + "                # the period its pickers list it under (else its wound table's conflict)\n" : ""}sides: [${spec.sides.map(yq).join(", ")}]
table: ${spec.table}
# On the travel map: a fight within \`within\` hexes of this place offers this field. \`sides\` are
# the travel-map sides that stand where each army stands here (${spec.sides[0]} first).
travel: {map: ${t.map}, place: ${yq(t.place)}, within: ${t.within}, sides: [${t.sides.map(yq).join(", ")}]}
size: [${grid[0].length}, ${grid.length}]
${upLine}weather: ${spec.weather}${spec.lz ? "\n" : ""}${spec.lz ? "lz: [" + hexList(spec.lz) + "]               # landing zones (units with `lands` come in by air at that one)" : ""}
ground: |
${grid.map(row => "  " + row.join("")).join("\n")}
${worksText}${supText}units:
${spec.units.map(unitLine).join("\n")}
`;
  fs.mkdirSync(path.join(ROOT, "data/fields"), { recursive: true });
  fs.writeFileSync(path.join(ROOT, `data/fields/${spec.id}.yaml`), out);
}
