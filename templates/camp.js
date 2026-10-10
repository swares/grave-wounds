/* Camp layout and works labour, shared by the roller's battle map and the travel map.
   Same rules as gravewounds/combat.py (party_of, camp_radius, camp_map_size, camp_works, works_labour).
   A force type may be a column's party: [[type, men], ...].
   build.py puts this file into both pages at their CAMP_JS marker. Each page provides
   WK (works.yaml), CAMP_HEX_M (the battle map's hex, metres), NEIGHBOURS, hexDistance,
   hkey and edgeKey. */
function partyOf(men, ftype){                 // a force type as a party [[type, men]]; a column's party is given as one
  return typeof ftype === "string" ? [[ftype, men]] : ftype.map(p => p.slice());
}
function campRadius(men, ftype){
  const need = partyOf(men, ftype).reduce((t, [ft, n]) => t + n * WK.camp_area[ft], 0);
  const area = Math.max(WK.camp_area_min, need), n = area / (Math.sqrt(3) / 2 * 4);
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
const around = ([c, r]) => NEIGHBOURS[r & 1].map(([dc, dr]) => [c + dc, r + dr]);   // all six, on the map or not
function stakePieces(centre, r){
  const gateOut = [centre[0] + r + 1, centre[1]];
  return { stakes: ringWalk(centre, r + 1).filter(h => !sameH(h, gateOut)).map(h => ["hex", [h], { type: "stakes", progress: 0 }]) };
}
function wallPieces(out, centre, r){          // bank and palisade round the ring, and the gate
  const gateIn = [centre[0] + r, centre[1]], gateOut = [centre[0] + r + 1, centre[1]];
  for (const h of ringWalk(centre, r)){
    for (const n of around(h).filter(x => hexDistance(centre, x) === r + 1)){
      if (sameH(h, gateIn) && sameH(n, gateOut)){
        out.gate.push(["edge", [h, n], { type: "gate", progress: 0, open: false, inside: hkey(h) }]);
        continue;
      }
      out.bank.push(["edge", [h, n], { type: "bank", progress: 0, high: hkey(h) }]);
      out.palisade.push(["edge", [h, n], { type: "palisade", progress: 0 }]);
    }
  }
}
function ditchPieces(out, centre, r){         // the ditch one ring out, leaving the way to the gate
  const gateOut = [centre[0] + r + 1, centre[1]];
  for (const h of ringWalk(centre, r + 1).filter(x => !sameH(x, gateOut))){
    for (const n of around(h).filter(x => hexDistance(centre, x) === r + 2)){
      out.ditch.push(["edge", [h, n], { type: "ditch", progress: 0, high: hkey(h) }]);
    }
  }
}
function campPieces(layout, centre, r){       // every piece by type, in building order round the ring, on the map or not
  if (layout === "stakes") return stakePieces(centre, r);
  const out = { ditch: [], bank: [], palisade: [], gate: [] };
  wallPieces(out, centre, r);
  ditchPieces(out, centre, r);
  return out;
}
function pieceLabour(where, item, hauled){
  if (where === "edge") return edgeLabour(WK.edge_works[item.type], hauled, edgeMetres());
  const sp = WK.hex_works[item.type];
  return (sp.each || 0) + (hauled ? sp.haul || 0 : 0);
}
const CAMP_ROOM = 6;                          // hexes between a camp too big for the map and the attackers' edge
// Battle-map layout for a camp. One that fits sits in the middle; one that does not is laid out at
// its true size with its centre moved west, so the stretch with the gate (east) is on the map and
// the rest runs off it (fits false). done: man-hours of work done so far (null: finished); the
// works go up in the order the camp lists them, each kind all round the ring from the gate before
// the next starts. Pieces off the map count towards the labour but are not shown.
function campWorks(kind, men, ftype, cols, rows, done = null, hauled = false){
  const c = WK.camps[kind], layout = c.layout, r = campRadius(men, ftype), extra = layout === "fortified" ? 2 : 1;
  let centre = [Math.floor(cols / 2), Math.floor(rows / 2)];
  const fits = campFits(centre, r + extra, cols, rows);
  if (!fits) centre = [cols - 1 - CAMP_ROOM - (r + extra), Math.floor(rows / 2)];
  const works = { edges: {}, hexes: {} }, result = { centre, radius: r, fits, works };
  if (layout) layPieces(c, campPieces(layout, centre, r), works, { done, hauled, cols, rows });
  return result;
}
function layPieces(c, pieces, works, o){
  const on = h => h[0] >= 0 && h[0] < o.cols && h[1] >= 0 && h[1] < o.rows;
  let spent = 0;
  for (const [where, hexes, item] of c.works.flatMap(k => pieces[k])){
    spent += pieceLabour(where, item, o.hauled);
    if (o.done !== null && spent > o.done + 1e-9) return;
    if (!hexes.every(on)) continue;
    if (where === "hex"){
      works.hexes[hkey(hexes[0])] = item;
      continue;
    }
    const k = edgeKey(...hexes);
    if (!works.edges[k]) works.edges[k] = [];
    works.edges[k].push(item);
  }
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
