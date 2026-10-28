// Shared drawing for the battlefields (make_agincourt_field.mjs, make_towton_field.mjs): a field
// map of 10 m pointy-top hexes, ground painted as rows of letters (units.yaml ground keys), works
// and the armies as drawn up, written to data/fields/<id>.yaml.
import { UNIT_SIZES } from "./unit_sizes.mjs";
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
// A unit placed by hand: its front's middle at pos, facing that way.
export const at = (name, army, men, kind, width, pos, facing) => ({ ...unit(name, army, men, kind, [width, 0, 0]), pos, facing });
// Hexes as the rules count them (units.js step: odd rows shifted half a hex east): a hex n steps
// from h in direction d (0 east, then anticlockwise: NE, NW, W, SW, SE).
const AX = [[1, 0], [1, -1], [0, -1], [-1, 0], [-1, 1], [0, 1]];
export function stepHex(h, d, n = 1){
  let q = h[0] - (h[1] - (h[1] & 1)) / 2, r = h[1];
  const [dq, dr] = AX[((d % 6) + 6) % 6];
  q += dq * n; r += dr * n;
  return [q + (r - (r & 1)) / 2, r];
}
// The hexes of a unit's front row, as the rules lay it out (units.js footprint), for a unit with
// at least as many hexes of men as its width: the works its account puts it in go under these.
export function frontRow(u){
  const start = stepHex(u.pos, u.facing + 2, Math.floor((u.width - 1) / 2));
  return Array.from({ length: u.width }, (_, i) => stepHex(start, u.facing + 5, i));
}
// The first column of a unit's front row (facing north).
export const firstCol = u => u.pos[0] - Math.floor((u.width - 1) / 2);

const yq = s => JSON.stringify(s);
const unitLine = u => `  - {name: ${yq(u.name)}, side: ${u.side}, men: ${u.men}, quality: ${u.quality}, weapon: ${u.weapon}, kit: ${u.kit}, formation: ${u.formation}, width: ${u.width}, pos: [${u.pos.join(", ")}], facing: ${u.facing}${u.mounted ? ", mounted: true" : ""}${u.guns ? ", guns: " + u.guns : ""}${u.prone ? ", prone: true" : ""}${u.lands === undefined ? "" : ", lands: " + u.lands}${u.vehicle ? ", vehicle: " + u.vehicle : ""}${u.fixed ? ", fixed: [" + u.fixed.join(", ") + "]" : ""}${u.via ? ", via: [" + u.via.map(h => "[" + h.join(", ") + "]").join(", ") + "]" : ""}${u.nv ? ", nv: " + u.nv : ""}${u.fc ? ", fc: " + u.fc : ""}${u.armour ? ", armour: " + u.armour : ""}${u.fac ? ", fac: true" : ""}${u.ladders ? ", ladders: true" : ""}${u.type ? ", type: " + u.type : ""}${u.size ? ", size: " + u.size : ""}}`;
function dumpsLine(ds){                          // the supply dumps' line (and its comment), or ""
  if (!ds?.length) return "";
  const one = m => "{at: [" + m.at.join(", ") + "], side: " + m.side + "}";
  return `\n# Supply dumps placed before the battle (side 0 or 1): its units within ammunition.reach of one can resupply there.\ndumps: [${ds.map(one).join(", ")}]`;
}
function objLine(o){                              // the objective's line (and its comment), or ""
  if (!o) return "";
  const radius = o.radius ? ", radius: " + o.radius : "";
  return `\n# The place the battle was fought for (side: the army that attacked it; radius: the hexes round it that count): the enemy commander's objective.\nobjective: {at: [${o.at.map(Math.round).join(", ")}], side: ${o.side}, name: ${yq(o.name)}${radius}}`;
}
function phasesText(ps){                          // the phases (and their comment), or ""
  if (!ps?.length) return "";
  const flow = o => "{" + Object.entries(o).map(([k, v]) => `${k}: ${typeof v === "string" ? yq(v) : v}`).join(", ") + "}";   // a phase's when or weather, inline
  const line = p => `  - {name: ${yq(p.name)}, at: ${p.at}${p.when ? ", when: " + flow(p.when) : ""}${p.note ? ", note: " + yq(p.note) : ""}${p.light ? ", light: " + p.light : ""}${p.weather ? ", weather: " + flow(p.weather) : ""}${p.arrive?.length ? ", arrive: [" + p.arrive.map(yq).join(", ") + "]" : ""}}`;
  return `\n# Phases: each begins at an exchange (about a minute each, the first 1); the units it lists wait off the map until then,\n# then come on where they are drawn, or at their side's entry edge if that is taken.\nphases:\n${ps.map(line).join("\n")}`;
}
function endsLine(e){                              // the account's length of the fight (and its comment), or ""
  if (!e) return "";
  return `\n# How long the fight went on, in exchanges from the first, by the account (${e.why}): self-play runs at least this long (never past commander.self_play.most).\nends: ${e.at}`;
}
function stancesLine(st){                        // the stances' line (and its comment), or "": a field with no objective
  if (!st) return "";
  return `\n# How each army fought (attack or hold), for the enemy commander on both sides; a field with an objective takes it from the objective.\nstances: [${st.join(", ")}]`;
}
function markersLine(m){                         // the markers settings' line (and its comment), or ""
  if (!m) return "";
  const parts = Object.entries(m).map(([k, v]) => `${k}: ${v}`).join(", ");
  return `\n# Unit markers on the field map (labels: names, ids or both; strength; size marks): units.yaml markers otherwise.\nmarkers: {${parts}}`;
}
// Each unit's size mark from unit_sizes.mjs, unless its generator set one. A field listed there must
// list every unit it has without a size, and only units it has.
function sized(id, units){
  const table = UNIT_SIZES[id];
  if (!table) return units;
  const names = new Set(units.map(u => u.name));
  const stray = Object.keys(table).filter(n => !names.has(n));
  const missing = units.filter(u => !u.size && !table[u.name]).map(u => u.name);
  if (stray.length || missing.length)
    throw new Error(`unit_sizes.mjs, ${id}: ${stray.length ? "no such unit: " + stray.join("; ") : ""}${stray.length && missing.length ? " / " : ""}${missing.length ? "no size for: " + missing.join("; ") : ""}`);
  return units.map(u => (u.size ? u : { ...u, size: table[u.name] }));
}
const hexList = hs => hs.map(h => `[${h.join(", ")}]`).join(", ");

// Foot in extended order, machine-gun teams, and a front row laid along a line: the presets the
// First World War battlefields share. line(w) is the row of the line at a column; the front row is the
// lowest of the w columns from c0, less `ahead` rows (nearer the enemy to the north).
export const extended = (quality, more = {}) => ({ quality, weapon: "rifle_service", kit: "none", formation: "extended", mounted: false, ...more });
export const mgTeam = (quality, more = {}) => ({ quality, weapon: "machine_gun", kit: "none", formation: "mg", mounted: false, ...more });
export const alongLine = (line, ahead) => (w, c0) => [w, c0, Math.min(...Array.from({ length: w }, (_, i) => line(c0 + i))) - ahead];

// Writes the battlefield file. spec: {id, script, header (comment lines), name, sides, table,
// travel {map, place, within, sides}, weather (YAML flow text), grid, hexWorks {type: [hexes]},
// edgeWorks {type: [[hex, hex], ...]} (the first hex of each pair the high or inner side), units,
// up (the compass point at the top of the map, if not north), support (each side's batteries on
// call: [{name, side (0 or 1), kind (units.yaml indirect.kinds), tubes}]), lz (landing zones,
// hexes; a unit with `lands: k` comes in by air at the k-th), dumps (supply dumps placed before the battle:
// [{at: hex, side: 0 or 1}], where its side's units can draw ammunition), objective (the place the battle
// was fought for: {at: hex, side: the army that attacked it (0 or 1), name, radius: hexes round it
// that count as on it}), markers (the unit markers' settings: {labels, strength, size}, all
// optional), stances (with no objective: how each army fought, [attack|hold, attack|hold]), ends ({at: the
// exchange the account's fight ends, why: the words it rests on}), phases (the battle's stages: [{name, at (the exchange it begins, the first 1), note,
// arrive (names of units held off the map until then)}]). A unit may also set type and size
// (units.yaml markers).
export function writeField(spec){
  spec = { ...spec, units: sized(spec.id, spec.units) };
  const { grid } = spec, works = Object.entries(spec.hexWorks || {});
  const edges = Object.entries(spec.edgeWorks || {});
  const workLine = ([type, hs]) => `    - {type: ${type}, at: [${hexList(hs)}]}`;
  const edgeLine = ([type, pairs]) => `    - {type: ${type}, at: [${pairs.map(pr => "[" + hexList(pr) + "]").join(", ")}]}`;
  const hexText = works.length ? "  hexes:\n" + works.map(workLine).join("\n") + "\n" : "";
  const edgeText = edges.length ? "  edges:\n" + edges.map(edgeLine).join("\n") + "\n" : "";
  const worksText = hexText || edgeText ? "works:\n" + hexText + edgeText : "";
  const supText = (spec.support || []).length ? "# Batteries on call (off the map): loading the field fills the Fire support panel.\nsupport:\n"
    + spec.support.map(s => `  - {name: ${yq(s.name)}, side: ${s.side}, kind: ${s.kind}, tubes: ${s.tubes}${s.place ? ", place: [" + s.place.join(", ") + "]" : ""}${s.df ? ", df: true" : ""}}`).join("\n") + "\n" : "";
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
${upLine}weather: ${spec.weather}${spec.lz ? "\n" : ""}${spec.lz ? "lz: [" + hexList(spec.lz) + "]               # landing zones (units with `lands` come in by air at that one)" : ""}${dumpsLine(spec.dumps)}${objLine(spec.objective)}${stancesLine(spec.stances)}${endsLine(spec.ends)}${markersLine(spec.markers)}${phasesText(spec.phases)}
ground: |
${grid.map(row => "  " + row.join("")).join("\n")}
${worksText}${supText}units:
${spec.units.map(unitLine).join("\n")}
`;
  fs.mkdirSync(path.join(ROOT, "data/fields"), { recursive: true });
  fs.writeFileSync(path.join(ROOT, `data/fields/${spec.id}.yaml`), out);
}
