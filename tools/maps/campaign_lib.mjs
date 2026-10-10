// Shared drawing for the campaign maps (make_agincourt.mjs, make_towton.mjs): a travel map of
// pointy-top hexes (odd rows shifted half a hex east) over a stretch of real country, painted
// from a spec of places (latitude, longitude), rivers, woods, marsh, hills and roads drawn
// through them, bridges and fords, towns and villages, and the forces at the start.
//
// The land and sea come from Natural Earth's 1:50m land (public domain, via the world-atlas
// package); everything else is the spec's, drawn by hand from plain facts.
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { feature } from "topojson-client";
import { geoContains } from "d3-geo";

const here = path.dirname(fileURLToPath(import.meta.url));
export const ROOT = path.resolve(here, "../..");

// The hex grid over the spec's bounds: positions in km from the north-west corner.
function makeGrid(spec){
  const { hexKm } = spec, rowKm = hexKm * Math.sqrt(3) / 2;
  const [lon0, lat0, lon1, lat1] = spec.bounds;                 // west, north, east, south
  const kx = 111.32 * Math.cos(spec.midLat * Math.PI / 180), ky = 111.2;   // km a degree at the map's middle
  const cols = Math.ceil((lon1 - lon0) * kx / hexKm) + 1, rows = Math.ceil((lat0 - lat1) * ky / rowKm) + 1;
  const g = {
    hexKm, rowKm, cols, rows,
    xy: ([lat, lon]) => [(lon - lon0) * kx, (lat0 - lat) * ky],
    centre: (c, r) => [c * hexKm + (r & 1) * hexKm / 2, r * rowKm],
    toLatLon: ([x, y]) => [lat0 - y / ky, lon0 + x / kx],
    on: ([c, r]) => c >= 0 && c < cols && r >= 0 && r < rows,
  };
  g.hexAt = ([x, y]) => {                         // the hex whose centre is nearest a point (km)
    const r0 = Math.round(y / rowKm);
    let best = null, bd = Infinity;
    for (let r = r0 - 1; r <= r0 + 1; r++){
      const c0 = Math.round((x - (r & 1) * hexKm / 2) / hexKm);
      for (let c = c0 - 1; c <= c0 + 1; c++){
        const [cx, cy] = g.centre(c, r), dd = (cx - x) ** 2 + (cy - y) ** 2;
        if (dd < bd){ bd = dd; best = [c, r] }
      }
    }
    return best;
  };
  return g;
}

function landShape(){
  const t = JSON.parse(fs.readFileSync(path.join(here, "node_modules/world-atlas/land-50m.json"), "utf8"));
  return feature(t, t.objects.land);
}

// Paints the terrain: land or sea, then woods, marsh, hills, brooks (as marsh), roads, rivers (with a bridge where
// a road crosses a lesser river), the named bridges and fords, villages and towns.
function paint(spec, g){
  const land = landShape(), P = spec.places;
  const grid = Array.from({ length: g.rows }, (_, r) => Array.from({ length: g.cols }, (_, c) => {
    const [lat, lon] = g.toLatLon(g.centre(c, r));
    return geoContains(land, [lon, lat]) ? spec.base || "f" : "w";
  }));
  const pt = p => (typeof p === "string" ? P[p] : p);
  const set = (h, k) => { if (g.on(h) && grid[h[1]][h[0]] !== "w") grid[h[1]][h[0]] = k };
  const line = (points, k, step = g.hexKm * 0.08) => {          // every hex a polyline runs through
    const out = [];
    for (let i = 0; i + 1 < points.length; i++){
      const a = g.xy(pt(points[i])), b = g.xy(pt(points[i + 1])), n = Math.max(1, Math.ceil(Math.hypot(b[0] - a[0], b[1] - a[1]) / step));
      for (let j = 0; j <= n; j++) out.push(g.hexAt([a[0] + (b[0] - a[0]) * j / n, a[1] + (b[1] - a[1]) * j / n]));
    }
    for (const h of out) set(h, k);
    return out;
  };
  const blob = ([c, rad], k) => {                 // every land hex within rad km of a point (and the one at it)
    const p = g.xy(c);
    for (let r = 0; r < g.rows; r++) for (let q = 0; q < g.cols; q++){
      const [x, y] = g.centre(q, r);
      if (Math.hypot(x - p[0], y - p[1]) <= rad && grid[r][q] !== "w") grid[r][q] = k;
    }
    set(g.hexAt(p), k);
  };
  (spec.woods || []).forEach(w => blob(w, "F"));
  (spec.marsh || []).forEach(w => blob(w, "m"));
  (spec.hills || []).forEach(w => blob(w, "h"));
  (spec.streams || []).forEach(st => line(st, "m"));        // a brook: wet, slow ground, not a river
  const roadHexes = (spec.roads || []).flatMap(rd => line(rd, "="));
  // A major river is crossed only where the spec says; where a road crosses a lesser one, a
  // bridge (but not on a hex the two share, where they meet).
  const major = new Set(spec.majorRivers || []), lesser = [], majorHexes = new Set();
  for (const [name, rv] of Object.entries(spec.rivers || {})){
    const hexes = line(rv, "~").map(h => h.join(","));
    if (major.has(name)) hexes.forEach(k => majorHexes.add(k));
    else lesser.push(...hexes);
  }
  const onLesser = new Set(lesser.filter(k => !majorHexes.has(k)));
  for (const h of roadHexes) if (onLesser.has(h.join(","))) set(h, "b");
  for (const b of spec.bridges || []) set(g.hexAt(g.xy(P[b])), "b");
  for (const f of spec.fords || []) set(g.hexAt(g.xy(P[f])), "d");
  // A place whose hex came out as sea (the coast is coarse at this scale) moves to the nearest land hex.
  const placeHex = k => {
    const h = g.hexAt(g.xy(P[k]));
    if (!g.on(h) || grid[h[1]][h[0]] !== "w") return h;
    const p = g.xy(P[k]);
    let best = h, bd = Infinity;
    for (let r = h[1] - 2; r <= h[1] + 2; r++) for (let c = h[0] - 2; c <= h[0] + 2; c++){
      if (!g.on([c, r]) || grid[r][c] === "w") continue;
      const [x, y] = g.centre(c, r), dd = (x - p[0]) ** 2 + (y - p[1]) ** 2;
      if (dd < bd){ bd = dd; best = [c, r] }
    }
    return best;
  };
  const rivered = h => g.on(h) && grid[h[1]][h[0]] === "~";
  for (const v of spec.villages) if (!rivered(placeHex(v))) set(placeHex(v), "v");   // a village on a river is not a crossing
  for (const t of spec.towns) set(placeHex(t), "T");
  return { grid, placeHex };
}

// The map file: header comment, settings, terrain rows, places and forces.
export function buildCampaign(spec){
  const g = makeGrid(spec), { grid, placeHex } = paint(spec, g), yq = s => JSON.stringify(s);
  const towns = new Set(spec.towns), villages = new Set(spec.villages);
  const kindOf = k => {
    if (spec.kinds?.[k]) return spec.kinds[k];
    if (towns.has(k)) return "town";
    return villages.has(k) ? "village" : "landmark";
  };
  const noteOf = k => (spec.notes[k] ? ", note: " + yq(spec.notes[k]) : "");
  const places = Object.keys(spec.names).filter(k => g.on(placeHex(k))).map(k =>
    `  - {name: ${yq(spec.names[k])}, kind: ${kindOf(k)}, hex: [${placeHex(k).join(", ")}]${noteOf(k)}}`);
  const forces = spec.forces.map(f =>
    `  - {name: ${yq(f.name)}, type: ${f.type}, side: ${yq(f.side)}, men: ${f.men}, tools: ${f.tools}, hex: [${placeHex(f.at).join(", ")}]}`);
  const size = `about ${Math.round(g.cols * g.hexKm)} by ${Math.round(g.rows * g.rowKm)} km`;
  const out = `# ${spec.title}, at ${g.hexKm} km a hex (${size}).
# Generated by tools/maps/${spec.script}: edit that file and re-run it rather than this one.
${spec.header.map(l => ("# " + l).trimEnd()).join("\n")}
id: ${spec.id}
name: ${yq(spec.name)}
hex_km: ${g.hexKm}
start_date: ${yq(spec.start_date)}
calendar: ${spec.calendar}
latitude: ${spec.latitude}
climate: ${spec.climate}
climate_shift: ${spec.climate_shift}
terrain: |
${grid.map(row => "    " + row.join("")).join("\n")}
places:
${places.join("\n")}
forces:
${forces.join("\n")}
`;
  fs.writeFileSync(path.join(ROOT, `data/maps/${spec.id}.yaml`), out);
  return { cols: g.cols, rows: g.rows, grid, placeHex };
}
