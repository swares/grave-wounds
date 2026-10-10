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
// A unit: army {side, facing}, kind {quality, weapon, kit, formation, mounted}, at [width, first col, front row].
export function unit(name, army, men, kind, at){
  const [width, col0, row] = at;
  return { name, ...army, men, ...kind, width, pos: [middle(col0, width, army.facing), row] };
}
// The first column of a unit's front row (facing north).
export const firstCol = u => u.pos[0] - Math.floor((u.width - 1) / 2);

const yq = s => JSON.stringify(s);
const unitLine = u => `  - {name: ${yq(u.name)}, side: ${u.side}, men: ${u.men}, quality: ${u.quality}, weapon: ${u.weapon}, kit: ${u.kit}, formation: ${u.formation}, width: ${u.width}, pos: [${u.pos.join(", ")}], facing: ${u.facing}${u.mounted ? ", mounted: true" : ""}}`;
const hexList = hs => hs.map(h => `[${h.join(", ")}]`).join(", ");

// Writes the battlefield file. spec: {id, script, header (comment lines), name, sides, table,
// travel {map, place, within, sides}, weather (YAML flow text), grid, hexWorks {type: [hexes]}, units}.
export function writeField(spec){
  const { grid } = spec, works = Object.entries(spec.hexWorks || {});
  const worksText = works.length ? `works:\n  hexes:\n${works.map(([type, hs]) => `    - {type: ${type}, at: [${hexList(hs)}]}`).join("\n")}\n` : "";
  const t = spec.travel;
  const out = `${spec.header.map(l => ("# " + l).trimEnd()).join("\n")}
id: ${spec.id}
name: ${yq(spec.name)}
sides: [${spec.sides.map(yq).join(", ")}]
table: ${spec.table}
# On the travel map: a fight within \`within\` hexes of this place offers this field. \`sides\` are
# the travel-map sides that stand where each army stands here (${spec.sides[0]} first).
travel: {map: ${t.map}, place: ${yq(t.place)}, within: ${t.within}, sides: [${t.sides.map(yq).join(", ")}]}
size: [${grid[0].length}, ${grid.length}]
weather: ${spec.weather}
ground: |
${grid.map(row => "  " + row.join("")).join("\n")}
${worksText}units:
${spec.units.map(unitLine).join("\n")}
`;
  fs.mkdirSync(path.join(ROOT, "data/fields"), { recursive: true });
  fs.writeFileSync(path.join(ROOT, `data/fields/${spec.id}.yaml`), out);
}
