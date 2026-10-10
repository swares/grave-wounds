/* Works and weather on a battle map, shared by the wound roller's battle map and the field
   map. Same rules as gravewounds/combat.py (step_cost, missile_cover, melee_across,
   deep_going, weather_attack). build.py puts this file into both pages at their WORKS_JS
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
// Hexes within `steps` movement, paying stepCost() plus `extra` a hex. opts: {cols, rows,
// enemies, friends, works, extra} (see gravewounds/combat.py reachable_works).
function reachableWorks(start, steps, opts){
  const { cols, rows, enemies, friends, works, extra = 0 } = opts;
  const key = h => h[0] + "," + h[1], blocked = new Set(enemies.map(key)), friendly = new Set(friends.map(key));
  const best = new Map([[key(start), 0]]), done = new Set(), hp = [[0, 0, start]];
  let seq = 1;
  const relax = (h, cost, n) => {
    const nk = key(n);
    if (blocked.has(nk)) return;
    const sc = stepCost(works, h, n);
    if (sc === null) return;
    const nc = cost + sc + extra;
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
function weatherAttack(weather, wid, dist){
  const out = { blocked: null, penalty: 0, misfire: 0, notes: [] }, w = WD_WEAPONS[wid];
  if (!weather || !WXD || !("range" in w)) return out;
  const cond = WXD.conditions[weather.cond], vis = cond.visibility;
  if (vis !== null && vis !== undefined && dist > vis){
    out.blocked = `${cond.name}: no one can be seen to aim at beyond ${vis} hexes (${vis * 2} m).`;
    return out;
  }
  const wind = WXD.winds.find(x => x.id === weather.wind);
  if (w.string){
    const p = WXD.battle.string_wet[cond.wet];
    if (p){ out.penalty += p; out.notes.push(`wet string -${p}%`) }
  }
  const firearm = !!w.ignition, wp = firearm ? wind.firearm : wind.missile;
  if (wp){ out.penalty += wp; out.notes.push(`${wind.name.toLowerCase()} -${wp}%`) }
  if (firearm) out.misfire = WXD.battle.misfire[w.ignition][cond.wet];
  return out;
}
