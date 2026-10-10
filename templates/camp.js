/* Camp layout and works labour, shared by the roller's battle map and the travel map.
   Same rules as gravewounds/combat.py (camp_radius, camp_map_size, camp_works, works_labour).
   build.py puts this file into both pages at their CAMP_JS marker. Each page provides
   WK (works.yaml), CAMP_HEX_M (the battle map's hex, metres), neighbours, hexDistance,
   hkey and edgeKey. */
function campRadius(men, ftype){
  const area = Math.max(WK.camp_area_min, men * WK.camp_area[ftype]), n = area / (Math.sqrt(3) / 2 * 4);
  let r = 0; while (3 * r * (r + 1) + 1 < n) r++;
  return Math.max(r, 1);
}
const AXIAL_DIRS = [[1, 0], [1, -1], [0, -1], [-1, 0], [-1, 1], [0, 1]];   // E, NE, NW, W, SW, SE
function ringWalk(centre, k){                 // the hexes k from the centre, round the ring from the east (the gate side)
  if (k === 0) return [centre.slice()];
  let q = centre[0] - (centre[1] - (centre[1] & 1)) / 2 + k, r = centre[1];
  const out = [];
  for (let i = 0; i < 6; i++){
    const [dq, dr] = AXIAL_DIRS[(i + 2) % 6];
    for (let j = 0; j < k; j++){
      out.push([q + (r - (r & 1)) / 2, r]);
      q += dq;
      r += dr;
    }
  }
  return out;
}
function campFits(centre, rr, cols, rows){    // every hex within rr of the centre is on the map
  let cnt = 0;
  for (let y = 0; y < rows; y++){
    for (let x = 0; x < cols; x++){
      if (hexDistance(centre, [x, y]) <= rr) cnt++;
    }
  }
  return cnt === 3 * rr * (rr + 1) + 1;
}
const sameH = (a, b) => a[0] === b[0] && a[1] === b[1];
function stakePieces(centre, r, on){
  const gateOut = [centre[0] + r + 1, centre[1]];
  return { stakes: ringWalk(centre, r + 1).filter(h => on(h) && !sameH(h, gateOut)).map(h => ["hex", hkey(h), { type: "stakes", progress: 0 }]) };
}
function wallPieces(out, centre, r, cols, rows, on){   // bank and palisade round the ring, and the gate
  const gateIn = [centre[0] + r, centre[1]], gateOut = [centre[0] + r + 1, centre[1]];
  for (const h of ringWalk(centre, r).filter(on)){
    for (const n of neighbours(h, cols, rows).filter(x => hexDistance(centre, x) === r + 1)){
      const k = edgeKey(h, n);
      if (sameH(h, gateIn) && sameH(n, gateOut)){
        out.gate.push(["edge", k, { type: "gate", progress: 0, open: false, inside: hkey(h) }]);
        continue;
      }
      out.bank.push(["edge", k, { type: "bank", progress: 0, high: hkey(h) }]);
      out.palisade.push(["edge", k, { type: "palisade", progress: 0 }]);
    }
  }
}
function ditchPieces(out, centre, r, cols, rows, on){  // the ditch one ring out, leaving the way to the gate
  const gateOut = [centre[0] + r + 1, centre[1]];
  for (const h of ringWalk(centre, r + 1).filter(x => on(x) && !sameH(x, gateOut))){
    for (const n of neighbours(h, cols, rows).filter(x => hexDistance(centre, x) === r + 2)){
      out.ditch.push(["edge", edgeKey(h, n), { type: "ditch", progress: 0, high: hkey(h) }]);
    }
  }
}
function campPieces(layout, centre, r, cols, rows){   // every piece by type, in building order round the ring
  const on = h => h[0] >= 0 && h[0] < cols && h[1] >= 0 && h[1] < rows;
  if (layout === "stakes") return stakePieces(centre, r, on);
  const out = { ditch: [], bank: [], palisade: [], gate: [] };
  wallPieces(out, centre, r, cols, rows, on);
  ditchPieces(out, centre, r, cols, rows, on);
  return out;
}
function pieceLabour(where, item, hauled){
  if (where === "edge") return edgeLabour(WK.edge_works[item.type], hauled, edgeMetres());
  const sp = WK.hex_works[item.type];
  return (sp.each || 0) + (hauled ? sp.haul || 0 : 0);
}
// Battle-map layout for a camp in the middle of the map, cut down to fit if it must. done: man-hours
// of work done so far (null: finished); the works go up in the order the camp lists them, each kind
// all round the ring from the gate before the next starts.
function campWorks(kind, men, ftype, cols, rows, done = null, hauled = false){
  const c = WK.camps[kind], layout = c.layout, centre = [Math.floor(cols / 2), Math.floor(rows / 2)];
  let r = campRadius(men, ftype), fits = true;
  const extra = layout === "fortified" ? 2 : 1;
  while (r > 1 && !campFits(centre, r + extra, cols, rows)){
    r--;
    fits = false;
  }
  const works = { edges: {}, hexes: {} }, result = { centre, radius: r, fits, works };
  if (!layout) return result;
  const pieces = campPieces(layout, centre, r, cols, rows);
  let spent = 0;
  for (const [where, key, item] of c.works.flatMap(k => pieces[k])){
    spent += pieceLabour(where, item, hauled);
    if (done !== null && spent > done + 1e-9) return result;
    if (where === "hex") works.hexes[key] = item;
    else (works.edges[key] = works.edges[key] || []).push(item);
  }
  return result;
}
const campMapSize = (kind, men, ftype) => 2 * (campRadius(men, ftype) + (WK.camps[kind].layout === "fortified" ? 2 : 1)) + 3;
const edgeMetres = () => CAMP_HEX_M / Math.sqrt(3);
function edgeLabour(sp, hauled, em){        // one hex side of a work, or one gate
  if ("each" in sp) return sp.each;
  const haul = hauled ? sp.haul || 0 : 0;
  return ((sp.per_metre || 0) + haul) * em;
}
function worksLabour(works, hauled = false){  // man-hours to build these works
  const em = edgeMetres();
  let t = 0;
  for (const items of Object.values(works?.edges || {})){
    for (const it of items) t += edgeLabour(WK.edge_works[it.type], hauled, em);
  }
  for (const it of Object.values(works?.hexes || {})){
    const sp = WK.hex_works[it.type];
    t += (sp.each || 0) + (hauled ? sp.haul || 0 : 0);
  }
  return t;
}
