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
function campWorks(kind, men, ftype, cols, rows){
  const layout = WK.camps[kind].layout, centre = [Math.floor(cols / 2), Math.floor(rows / 2)];
  let r = campRadius(men, ftype), fits = true;
  const extra = layout === "fortified" ? 2 : 1;
  while (r > 1 && !campFits(centre, r + extra, cols, rows)){
    r--;
    fits = false;
  }
  const works = { edges: {}, hexes: {} };
  if (layout === "stakes") layStakes(works, centre, r, cols, rows);
  else if (layout === "fortified") layFortified(works, centre, r, cols, rows);
  return { centre, radius: r, fits, works };
}
function hexesAt(centre, dist, cols, rows){   // the hexes exactly `dist` from the centre
  const out = [];
  for (let y = 0; y < rows; y++){
    for (let x = 0; x < cols; x++){
      if (hexDistance(centre, [x, y]) === dist) out.push([x, y]);
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
function layStakes(works, centre, r, cols, rows){
  const gateOut = [centre[0] + r + 1, centre[1]];
  for (const h of hexesAt(centre, r + 1, cols, rows)){
    if (!sameH(h, gateOut)) works.hexes[hkey(h)] = { type: "stakes", progress: 0 };
  }
}
function layFortified(works, centre, r, cols, rows){
  layWall(works, centre, r, cols, rows);
  layDitch(works, centre, r, cols, rows);
}
function layWall(works, centre, r, cols, rows){   // bank and palisade round the ring, with the gate
  const gateIn = [centre[0] + r, centre[1]], gateOut = [centre[0] + r + 1, centre[1]];
  for (const h of hexesAt(centre, r, cols, rows)){
    for (const n of neighbours(h, cols, rows).filter(x => hexDistance(centre, x) === r + 1)){
      const gate = sameH(h, gateIn) && sameH(n, gateOut);
      works.edges[edgeKey(h, n)] = gate ? [{ type: "gate", progress: 0, open: false, inside: hkey(h) }]
        : [{ type: "bank", progress: 0, high: hkey(h) }, { type: "palisade", progress: 0 }];
    }
  }
}
function layDitch(works, centre, r, cols, rows){  // the ditch one ring out, leaving the way to the gate
  const gateOut = [centre[0] + r + 1, centre[1]];
  for (const h of hexesAt(centre, r + 1, cols, rows)){
    if (sameH(h, gateOut)) continue;
    for (const n of neighbours(h, cols, rows).filter(x => hexDistance(centre, x) === r + 2)){
      works.edges[edgeKey(h, n)] = [{ type: "ditch", progress: 0, high: hkey(h) }];
    }
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
