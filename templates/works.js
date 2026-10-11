/* Works and weather on a battle map, shared by the wound roller's battle map and the field
   map. Same rules as gravewounds/combat.py (step_cost, missile_cover, melee_across,
   deep_going, weather_attack, ray). build.py puts this file into both pages at their WORKS_JS
   marker. Each page provides WK (works.yaml), WXD (weather.yaml), WD_WEAPONS (weapons),
   hkey, edgeKey, neighbours(h, cols, rows) and hexDistance.
   works = {edges: {edgeKey: [item]}, hexes: {hexKey: item}}. */
const specOf = (kind, item) => (kind === "edge" ? WK.edge_works : WK.hex_works)[item.type];
function intact(kind, item){ const b = specOf(kind, item).breach; return !(b && (item.progress || 0) >= b) }
function edgeItems(works, a, b){
  if (!works) return [];
  return (works.edges?.[edgeKey(a, b)] || []).filter(it => intact("edge", it) && !(specOf("edge", it).gate && it.open));
}
function hexItem(works, h){
  const it = works?.hexes?.[hkey(h)];
  return it && intact("hex", it) ? it : null;
}
function stepCost(works, a, b){
  let cost = 1;
  for (const it of edgeItems(works, a, b)){
    const s = specOf("edge", it), c = s.gate ? null : s.cross;
    if (c === null || c === undefined) return null;
    cost += c;
  }
  const it = hexItem(works, b);
  if (!it) return cost;
  const e = specOf("hex", it).enter;
  return e === null || e === undefined ? null : cost + e;
}
function heapPushW(hp, x){
  hp.push(x);
  let i = hp.length - 1;
  while (i > 0){
    const p = (i - 1) >> 1;
    if (lessW(hp[p], hp[i])) break;
    [hp[p], hp[i]] = [hp[i], hp[p]];
    i = p;
  }
}
function heapPopW(hp){
  const top = hp[0], last = hp.pop();
  if (!hp.length) return top;
  hp[0] = last;
  let i = 0;
  for (;;){
    const l = 2 * i + 1, r = l + 1;
    let m = i;
    if (l < hp.length && lessW(hp[l], hp[m])) m = l;
    if (r < hp.length && lessW(hp[r], hp[m])) m = r;
    if (m === i) break;
    [hp[m], hp[i]] = [hp[i], hp[m]];
    i = m;
  }
  return top;
}
const lessW = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);
// Hexes within `steps` movement, paying stepCost() plus `extra` a hex, plus stepExtra(a, b)
// (the battle map's ground and climbing). opts: {cols, rows, enemies, friends, works, extra,
// stepExtra} (see gravewounds/combat.py reachable_works).
function reachableWorks(start, steps, opts){
  const { cols, rows, enemies, friends, works, extra = 0, stepExtra = null } = opts;
  const key = h => h[0] + "," + h[1], blocked = new Set(enemies.map(key)), friendly = new Set(friends.map(key));
  const best = new Map([[key(start), 0]]), done = new Set(), hp = [[0, 0, start]];
  let seq = 1;
  const relax = (h, cost, n) => {
    const nk = key(n);
    if (blocked.has(nk)) return;
    const sc = stepCost(works, h, n);
    if (sc === null) return;
    const nc = cost + sc + extra + (stepExtra ? stepExtra(h, n) : 0);
    if (nc > steps || nc >= (best.has(nk) ? best.get(nk) : steps + 1)) return;
    best.set(nk, nc); heapPushW(hp, [nc, seq++, n]);
  };
  while (hp.length){
    const [cost, , h] = heapPopW(hp), k = key(h);
    if (done.has(k)) continue;
    done.add(k);
    for (const n of neighbours(h, cols, rows)) relax(h, cost, n);
  }
  for (const k of friendly) if (best.get(k)) best.delete(k);
  return best;
}
// ---------- lines of fire (as gravewounds.combat) ----------
function cubeRound(x, y, z){                    // the offset hex nearest a point in cube coordinates
  let rx = Math.floor(x + 0.5), ry = Math.floor(y + 0.5);
  const rz = Math.floor(z + 0.5), dx = Math.abs(rx - x), dy = Math.abs(ry - y), dz = Math.abs(rz - z);
  if (dx > dy && dx > dz) rx = -ry - rz;
  else if (dy > dz) ry = -rx - rz;
  return [rx + (ry - (ry & 1)) / 2, ry];
}
function hexRay(a, b, n){                        // the hexes on the line from a through b, n steps (b is step distance(a, b))
  const cu = h => { const q = h[0] - (h[1] - (h[1] & 1)) / 2; return [q, h[1], -q - h[1]] };
  const s = cu(a), c = cu(b), k = Math.max(Math.abs(s[0] - c[0]), Math.abs(s[1] - c[1]), Math.abs(s[2] - c[2]));
  if (k === 0) return [[...a]];
  const out = [];
  for (let i = 0; i <= n; i++) out.push(cubeRound(s[0] + (c[0] - s[0]) * i / k + 1e-6, s[1] + (c[1] - s[1]) * i / k + 2e-6, s[2] + (c[2] - s[2]) * i / k - 3e-6));
  return out;
}
function facing(target, attacker, cols, rows){
  const ns = neighbours(target, cols, rows);
  if (!ns.length) return [];
  const best = Math.min(...ns.map(n => hexDistance(n, attacker)));
  return ns.filter(n => hexDistance(n, attacker) === best);
}
function edgeCover(works, target, n){              // [cover, type]: the best cover the works on this side give the target
  let best = 0, what = null;
  for (const e of edgeItems(works, target, n)){
    const s = specOf("edge", e);
    if ((s.cover_side || "both") === "high" && e.high !== hkey(target)) continue;
    if ((s.cover || 0) > best){ best = s.cover; what = e.type }
  }
  return [best, what];
}
function missileCover(works, attacker, target, cols, rows){
  let best = 0, what = null;
  const take = (c, t) => { if (c > best){ best = c; what = t } };
  const it = hexItem(works, target);
  if (it) take(specOf("hex", it).cover_here || 0, it.type);
  for (const n of facing(target, attacker, cols, rows)){
    take(...edgeCover(works, target, n));
    const h = n[0] === attacker[0] && n[1] === attacker[1] ? null : hexItem(works, n);
    if (h) take(specOf("hex", h).cover_behind || 0, h.type);
  }
  return { cover: best, work: what };
}
function meleeAcross(works, attacker, target, reach, cols, rows){
  const d1 = hexDistance(attacker, target) === 1;
  const cands = d1 ? [attacker.slice()] : facing(target, attacker, cols, rows);
  let blocked = false, penalty = 0, what = null;
  for (const n of cands){
    let pen = 0;
    for (const e of edgeItems(works, target, n)){
      const s = specOf("edge", e);
      if (s.blocks_melee && reach < 2 && d1){ blocked = true; what = e.type }
      if (s.height && e.high === hkey(target)){ pen += s.height; what = what || e.type }
    }
    penalty = Math.max(penalty, pen);
  }
  return { blocked, penalty, work: what };
}
function deepGoing(ground){
  if (!ground || !WXD) return 0;
  const deep = WXD.ground.deep;
  return (ground.mud || 0) >= deep || (ground.snow || 0) >= deep ? WXD.battle.deep_step : 0;
}
// The wind's direction (as gravewounds/combat.py wind_lie): how a shot from hex frm to hex to lies
// to the wind: "with" (the wind behind it, within 45 degrees), "against", "across", or null (calm,
// no direction, no hexes). up: the compass point at the top of the map.
const WIND_NAMES = { N: "north", NE: "north-east", E: "east", SE: "south-east", S: "south", SW: "south-west", W: "west", NW: "north-west" };
function windDirOptions(cur){                     // the options for a "Wind from" select
  return `<option value="">(no direction)</option>` + (WXD?.wind_points || []).map(p => `<option value="${p}" ${cur === p ? "selected" : ""}>from the ${WIND_NAMES[p]}</option>`).join("");
}
function windDirNote(weather){                    // what the wind's direction does, for a weather note
  const wind = WXD?.winds.find(x => x.id === weather?.wind);
  if (!weather?.dir || !wind?.reach) return "";
  const into = wind.into_wind ? ` and −${wind.into_wind}%` : "", cond = WXD.conditions[weather.cond];
  const driven = cond.precip === "none" ? "" : `; ${cond.precip} driven into the faces of those shooting into it halves their sight`;
  return `wind from the ${WIND_NAMES[weather.dir]}: bows, crossbows and slings reach ${wind.reach}% further with it, ${wind.reach}% less into it${into}${driven}`;
}
const S45 = Math.sqrt(0.5);
const WIND_VECTORS = [[0, -1], [S45, -S45], [1, 0], [S45, S45], [0, 1], [-S45, S45], [-1, 0], [-S45, -S45]];
function windLie(weather, frm, to, up = "N"){
  const pts = WXD?.wind_points || [];
  if (!weather || !frm || !to || !pts.includes(weather.dir) || weather.wind === "calm") return null;
  const k = (pts.indexOf(weather.dir) - pts.indexOf(up) + 12) % 8, [wx, wy] = WIND_VECTORS[k];   // where it blows to, on the page
  const q1 = frm[0] - (frm[1] - (frm[1] & 1)) / 2, q2 = to[0] - (to[1] - (to[1] & 1)) / 2, dr = to[1] - frm[1];
  const dx = Math.sqrt(3) * ((q2 - q1) + dr / 2), dy = 1.5 * dr, n = Math.hypot(dx, dy);
  if (n === 0) return null;
  const dot = dx * wx + dy * wy;
  if (dot >= S45 * n - 1e-9) return "with";
  if (dot <= -S45 * n + 1e-9) return "against";
  return "across";
}
function sightFor(cond, lie, out){                // how far a shooter can see to aim: less with rain or snow in his face
  let vis = cond.visibility;
  if (vis !== null && vis !== undefined && lie === "against" && cond.precip !== "none"){
    vis = Math.floor(vis * WXD.driven_sight / 100);
    out.notes.push(`${cond.precip} in their faces`);
  }
  return vis;
}
function windReach(w, wind, lie, out){            // with the wind a bow, crossbow or sling reaches further; into it, less and harder
  if ((lie !== "with" && lie !== "against") || w.ignition || !wind.reach) return;
  out.reach = lie === "with" ? wind.reach : -wind.reach;
  const sign = out.reach > 0 ? "+" : "", way = lie === "with" ? "with" : "into";
  out.notes.push(`${way} the wind, reach ${sign}${out.reach}%`);
  if (lie === "against" && wind.into_wind){ out.penalty += wind.into_wind; out.notes.push(`into the wind -${wind.into_wind}%`) }
}
function weatherAttack(weather, wid, dist, frm = null, to = null, up = "N"){   // -> {blocked, penalty, misfire, reach (% on the range bands), notes}
  const out = { blocked: null, penalty: 0, misfire: 0, reach: 0, notes: [] }, w = WD_WEAPONS[wid];
  if (!weather || !WXD || !("range" in w)) return out;
  const cond = WXD.conditions[weather.cond], lie = windLie(weather, frm, to, up), vis = sightFor(cond, lie, out);
  if (vis !== null && vis !== undefined && dist > vis){
    out.blocked = `${cond.name}: no one can be seen to aim at beyond ${vis} hexes (${fmtM(vis * 2)}).`;
    return out;
  }
  const wind = WXD.winds.find(x => x.id === weather.wind);
  windReach(w, wind, lie, out);
  if (w.string){
    const p = WXD.battle.string_wet[cond.wet];
    if (p){ out.penalty += p; out.notes.push(`wet string -${p}%`) }
  }
  const firearm = !!w.ignition, wp = firearm ? wind.firearm : wind.missile;
  if (wp){ out.penalty += wp; out.notes.push(`${wind.name.toLowerCase()} -${wp}%`) }
  if (firearm) out.misfire = WXD.battle.misfire[w.ignition][cond.wet];
  return out;
}
