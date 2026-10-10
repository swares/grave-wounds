/* Unit combat on the field map: same rules as gravewounds/units.py (and the wound roll of
   gravewounds/engine.roll_hit, from ranges precomputed by build.py). build.py puts this file
   into the field page at its UNITS_JS marker. The page provides FD (the field bundle).
   rng: {randint(a, b), random()}; SeededDice gives repeatable dice for tests. */
const UD = FD.units;
const mod6 = n => ((n % 6) + 6) % 6;
class SeededDice {
  constructor(seed){ this.state = Math.max(1, seed % 2147483647) }
  next(){ this.state = this.state * 16807 % 2147483647; return this.state }
  randint(a, b){ return a + this.next() % (b - a + 1) }
  random(){ return this.next() / 2147483647 }
}
const quality = q => UD.quality[q];

// ---------- the wound roll (as engine.roll_hit, with a margin) ----------
const SEV_LADDER = ["stopped", "light", "serious", "critical"];
function lookupRange(ranges, roll){
  const r = ranges.find(x => x[1] <= roll && roll <= x[2]);
  if (!r) throw new Error("roll " + roll + " not on table");
  return r[0];
}
function marginSeverity(margin, critical, wid, zone){
  if (critical) return "critical";
  const bands = FD.combat.margin_bands, w = FD.weapons[wid] || {};
  let b = bands.default;
  if (w.threat && bands.ballistic) b = bands.ballistic.find(x => x.zones.includes(zone));
  if (margin >= b.critical) return "critical";
  return margin >= b.serious ? "serious" : "light";
}
function armorSteps(material, mech, wid){
  const mat = FD.materials[material], w = FD.weapons[wid] || {};
  const steps = mech === "ballistic" && w.threat && mat.threats?.[w.threat] !== undefined ? mat.threats[w.threat] : mat[mech];
  return Math.max(0, steps - (w.armor_defeat?.[mech] || 0));
}
const reduceSeverity = (sev, steps) => SEV_LADDER[Math.max(0, SEV_LADDER.indexOf(sev) - steps)];
const isGraze = (margin, critical) => !critical && margin <= FD.combat.graze_margin;
function rollWound(table, wid, kit, margin, critical, rng){   // {severity, lethal, graze}
  const loc = lookupRange(FD.tables[table].ranges[wid], rng.randint(1, 100));
  const mech = lookupRange(FD.mechanisms[wid], rng.randint(1, 100));
  const sev = marginSeverity(margin, critical, wid, FD.locations[loc].zone);
  let final = sev;
  const layers = kit ? FD.kits[kit].layers[loc] : [];
  if (layers.length){
    const whole = layers.length === 1 && layers[0][1] === 1 && layers[0][2] === 100;
    const cov = whole ? null : rng.randint(1, 100);
    const hit = whole ? layers[0] : layers.find(l => l[1] <= cov && cov <= l[2]);
    final = reduceSeverity(sev, hit ? armorSteps(hit[0], mech, wid) : 0);
  }
  if (final === "stopped") return { severity: final, lethal: null, graze: false };
  return { severity: final, lethal: FD.lethal[loc][mech][final], graze: isGraze(margin, critical) };
}

// ---------- blows ----------
function weaponReach(wid, dist){                   // as gravewounds.combat.weapon_reach
  const w = FD.weapons[wid];
  if (w.off_map) return { band: "any", penalty: 0 };
  if (dist < 1) return null;
  if ("reach" in w) return dist <= w.reach ? { band: "reach", penalty: 0 } : null;
  for (let i = 0; i < w.range.length; i++) if (dist <= w.range[i]) return { band: FD.combat.range[i].band, penalty: FD.combat.range[i].penalty };
  return null;
}
const fieldRange = (wid, hexes) => weaponReach(wid, hexes * UD.range_scale);
function countBlows(n, rng){ const whole = Math.floor(n); return whole + (rng.random() < n - whole ? 1 : 0) }
const newTally = () => ({ blows: 0, missed: 0, parried: 0, stopped: 0, hits: 0, light: 0, serious: 0, critical: 0, down: 0, dead: 0 });
function landWound(att, dfd, margin, critical, rng, t){
  const h = rollWound(att.table, att.weapon, dfd.kit, margin, critical, rng);
  if (h.severity === "stopped"){ t.stopped++; return }
  t.hits++;
  t[h.severity]++;
  if (UD.dead_if.includes(h.lethal)){ t.dead++; t.down++; return }
  if (h.severity === "light" || h.graze) return;
  const nerve = quality(dfd.quality).nerve - (h.severity === "critical" ? 10 : 0);
  if (rng.randint(1, 100) > nerve) t.down++;
}
function blows(att, dfd, n, atk, dfn, rng){
  const t = newTally();
  t.blows = n;
  atk = Math.max(0, atk);
  const critAt = Math.floor(atk * FD.combat.critical_fraction);
  for (let i = 0; i < n; i++){
    const r = rng.randint(1, 100);
    if (r > atk){ t.missed++; continue }
    const critical = r <= critAt;
    if (!critical && dfn > 0 && rng.randint(1, 100) <= dfn){ t.parried++; continue }
    landWound(att, dfd, atk - r, critical, rng, t);
  }
  return t;
}
// opts: {situation, charge, shaken, rout}
function melee(att, dfd, men, rng, opts = {}){
  const M = UD.melee, situation = opts.situation || "front";
  let tempo = M.tempo, atk = quality(att.quality).attack + (att.attack || 0), dfn = quality(dfd.quality).defence + (dfd.defence || 0);
  if (situation === "flank" || situation === "rear"){ atk += M[situation].attack; dfn += M[situation].defence }
  if (opts.charge){ atk += M.charge.attack; tempo *= M.charge.tempo }
  if (opts.shaken) atk += M.shaken.attack;
  if (opts.rout){ atk += UD.rout.attack; tempo *= UD.rout.tempo; dfn = 0 }
  return blows(att, dfd, countBlows(men * tempo, rng), atk, dfn, rng);
}
function volley(att, dfd, men, hexes, rng, penalty = 0, factor = 1){
  const band = fieldRange(att.weapon, hexes);
  if (!band) return null;
  const S = UD.missile, shots = men * (S.rate[att.weapon] ?? S.default_rate) * S.tempo * factor;
  const atk = quality(att.quality).attack + (att.attack || 0) - band.penalty - penalty;
  return blows(att, dfd, countBlows(shots, rng), atk, 0, rng);
}

// ---------- morale ----------
function moraleMods(mods, u){
  let m = 0;
  if (u.leader === "up") m += mods.leader;
  else if (u.leader === "down") m += mods.leader_down;
  if (u.down >= u.start / 2) m += mods.heavy;
  if (u.flanked) m += mods.flank;
  if (u.friends) m += mods.veteran_friends;
  if (u.state === "steady") m += mods.in_order;
  m -= Math.min(mods.losing_cap, mods.losing_per_man * Math.max(0, (u.lost || 0) - (u.dealt || 0)));
  return m;
}
function failedState(mo, u, by){
  if (u.state === "shaken") return "broken";
  const hard = u.flanked || u.down >= u.start / 2;
  return hard && by > mo.shaken_by ? "broken" : "shaken";
}
function morale(u, roll){                       // {check, target, state}
  const M = UD.morale;
  if (u.state === "broken") return { check: false, target: null, state: "broken" };
  const losing = (u.lost || 0) > (u.dealt || 0) && u.contact;
  const struck = u.down >= M.trigger * u.start || u.lost >= M.shock * Math.max(1, u.men) || u.flanked || losing;
  const rally = u.state === "shaken" && !u.contact;
  if (!struck && !rally) return { check: false, target: null, state: u.state };
  const target = quality(u.quality).nerve + moraleMods(M.mods, u);
  if (roll <= target) return { check: true, target, state: rally && !struck ? "steady" : u.state };
  return { check: true, target, state: failedState(M, u, roll - target) };
}

// ---------- the field map ----------
const AX = [[1, 0], [1, -1], [0, -1], [-1, 0], [-1, 1], [0, 1]];   // E, NE, NW, W, SW, SE (axial)
function step(h, dirn, n = 1){
  let q = h[0] - (h[1] - (h[1] & 1)) / 2, r = h[1];
  const [dq, dr] = AX[mod6(dirn)];
  q += dq * n; r += dr * n;
  return [q + (r - (r & 1)) / 2, r];
}
function cube(h){ const q = h[0] - (h[1] - (h[1] & 1)) / 2; return [q, h[1], -q - h[1]] }
function hdist(a, b){ const x = cube(a), y = cube(b); return Math.max(Math.abs(x[0] - y[0]), Math.abs(x[1] - y[1]), Math.abs(x[2] - y[2])) }
function arc(facing, dirn){
  const k = mod6(dirn - facing);
  if (k <= 1) return "front";
  return k === 2 || k === 5 ? "flank" : "rear";
}
const form = u => UD.formations[u.formation];
const hk = h => h[0] + "," + h[1];
function footprint(u){                          // rows of hexes, front row first
  if (u.men <= 0 || u.state === "fled") return [];
  const n = Math.ceil(u.men / form(u).per_hex), w = Math.max(1, Math.min(u.width, n)), v = u.facing;
  const start = step(u.pos, v + 2, Math.floor((w - 1) / 2)), rows = [];
  let k = 0;
  while (k < n){
    const base = step(start, v + 3, rows.length), row = [];
    for (let i = 0; i < Math.min(w, n - k); i++) row.push(step(base, v + 5, i));
    k += row.length;
    rows.push(row);
  }
  return rows;
}
function menByHex(u){
  const per = form(u).per_hex, out = [];
  let left = u.men;
  for (const row of footprint(u)) row.forEach(() => { const n = Math.min(per, left); out.push(n); left -= n });
  return out;
}
function occupancy(units){
  const occ = {};
  units.forEach((u, i) => { for (const row of footprint(u)) for (const h of row) occ[hk(h)] = i });
  return occ;
}
function adjacentUnits(units, occ, i){
  const out = new Set();
  for (const row of footprint(units[i])) for (const h of row) for (let dn = 0; dn < 6; dn++){
    const j = occ[hk(step(h, dn))];
    if (j !== undefined && j !== i) out.add(j);
  }
  return [...out].sort((a, b) => a - b);
}
const inContact = (units, occ, i) => adjacentUnits(units, occ, i).some(j => units[j].side !== units[i].side);
const out_ = u => u.state === "broken" || u.state === "fled" || u.men <= 0;
function strikeGroups(units, occ){               // melee across the front: {"i|j|situation": men}
  const groups = new Map();
  units.forEach((u, i) => {
    if (out_(u)) return;
    const rows = footprint(u), men = menByHex(u), reach = FD.weapons[u.weapon].reach || 1;
    const ranks = reach >= UD.melee.second_rank_reach ? 2 : 1;
    (rows[0] || []).forEach((h, k) => {
      for (const dn of [u.facing, u.facing + 1]){
        const j = occ[hk(step(h, dn))];
        if (j === undefined || units[j].side === u.side || units[j].state === "broken") continue;
        const key = [i, j, arc(units[j].facing, dn + 3)].join("|");
        groups.set(key, (groups.get(key) || 0) + Math.min(form(u).abreast * ranks, men[k]));
        break;
      }
    });
  });
  return groups;
}
const cmpKey = (a, b) => { const x = a.split("|"), y = b.split("|"); return (+x[0] - +y[0]) || (+x[1] - +y[1]) || x[2].localeCompare(y[2]) };
function strikes(units){                         // [{att, dfd, men, situation, rout}]
  const occ = occupancy(units), groups = strikeGroups(units, occ);
  const out = [...groups.keys()].sort(cmpKey).map(k => { const [i, j, sit] = k.split("|"); return { att: +i, dfd: +j, men: groups.get(k), situation: sit, rout: false } });
  units.forEach((b, j) => {
    if (b.state !== "broken" || b.men <= 0) return;
    for (const i of adjacentUnits(units, occ, j)) if (units[i].side !== b.side && units[i].state !== "broken" && units[i].state !== "fled") out.push({ att: i, dfd: j, men: units[i].men, situation: "rear", rout: true });
  });
  return out;
}
function fvec(facing){ const a = AX[mod6(facing)], b = AX[mod6(facing + 1)], q = a[0] + b[0], r = a[1] + b[1]; return [q, r, -q - r] }
function target(units, i){                       // [distance, index] of the nearest enemy in range in front, or null
  const u = units[i], fv = fvec(u.facing), front = footprint(u)[0];
  let best = null;
  units.forEach((e, j) => {
    if (e.side === u.side || e.men <= 0 || e.state === "fled") return;
    const dist = nearestAhead(u.weapon, front, fv, footprint(e).flat());
    if (dist !== null && (best === null || dist < best[0])) best = [dist, j];
  });
  return best;
}
function nearestAhead(weapon, front, fv, hexes){  // shortest distance in range from the front to a hex ahead of the line
  let best = null;
  for (const t of hexes){
    const c = cube(t);
    for (const h of front){
      const s = cube(h);
      if ((c[0] - s[0]) * fv[0] + (c[1] - s[1]) * fv[1] + (c[2] - s[2]) * fv[2] <= 0) continue;
      const dist = hdist(h, t);
      if (fieldRange(weapon, dist) && (best === null || dist < best)) best = dist;
    }
  }
  return best;
}
function volleys(units){                         // [{att, dfd, men, dist}]
  const occ = occupancy(units), out = [];
  units.forEach((u, i) => {
    if (out_(u) || !("range" in FD.weapons[u.weapon]) || inContact(units, occ, i)) return;
    const best = target(units, i);
    if (!best) return;
    const rows = footprint(u), men = menByHex(u), per = form(u).abreast * Math.min(UD.shoot_ranks, form(u).ranks);
    let shooters = 0;
    for (let k = 0; k < rows[0].length; k++) shooters += Math.min(per, men[k]);
    out.push({ att: i, dfd: best[1], men: shooters, dist: best[0] });
  });
  return out;
}
const sideOfUnit = (u, table) => ({ table, weapon: u.weapon, kit: u.kit, quality: u.quality });
function tallyLoss(acc, s, t){ acc.lost[s.dfd] += t.down; acc.dead[s.dfd] += t.dead; acc.dealt[s.att] += t.down }
function exchange(units, table, rng){            // -> {units, log}
  const us = units.map(u => ({ ...u })), n = us.length, log = [];
  const acc = { lost: new Array(n).fill(0), dead: new Array(n).fill(0), dealt: new Array(n).fill(0), flanked: new Array(n).fill(false) };
  for (const s of strikes(us)){
    const a = us[s.att], b = us[s.dfd];
    const t = melee(sideOfUnit(a, table), sideOfUnit(b, table), s.men, rng, { situation: s.situation, charge: !!a.charged && !!a.mounted, shaken: a.state === "shaken", rout: s.rout });
    tallyLoss(acc, s, t);
    acc.flanked[s.dfd] = acc.flanked[s.dfd] || s.situation === "flank" || s.situation === "rear";
    log.push({ kind: s.rout ? "rout" : "melee", ...s, ...t });
  }
  for (const v of volleys(us)){
    const t = volley(sideOfUnit(us[v.att], table), sideOfUnit(us[v.dfd], table), v.men, v.dist, rng, 0, form(us[v.dfd]).missile_factor);
    tallyLoss(acc, v, t);
    log.push({ kind: "volley", ...v, ...t });
  }
  const occ = occupancy(us), before = us.map(u => u.men);
  us.forEach((u, i) => {
    const cut = Math.min(acc.lost[i], u.men);
    Object.assign(u, { men: u.men - cut, down: (u.down || 0) + cut, dead: (u.dead || 0) + Math.min(acc.dead[i], cut) });
  });
  log.push(...moraleAll(us, occ, before, acc, rng, table));
  for (const u of us) u.charged = false;
  return { units: us, log };
}
function moraleAll(us, occ, before, acc, rng, table){
  const log = [], broke = [];
  us.forEach((u, i) => {
    if (out_(u)) return;
    const near = adjacentUnits(us, occ, i);
    const unit = { quality: u.quality, start: u.start, down: u.down, lost: acc.lost[i], dealt: acc.dealt[i], men: before[i], state: u.state,
      leader: u.leader, flanked: acc.flanked[i], contact: near.some(j => us[j].side !== u.side), friends: near.some(j => us[j].side === u.side && us[j].state === "steady") };
    const m = morale(unit, rng.randint(1, 100));
    if (m.check) log.push({ kind: "morale", unit: i, target: m.target, from: u.state, state: m.state });
    if (m.state === "broken") broke.push(i);
    u.state = m.state;
  });
  for (const j of broke) log.push(...routStrike(us, occ, j, table, rng));
  return log;
}
function routStrike(us, occ, j, table, rng){     // a unit that has just broken is struck by every man touching it
  const log = [];
  for (const i of adjacentUnits(us, occ, j)){
    const a = us[i], b = us[j];
    if (a.side === b.side || out_(a) || b.men <= 0) continue;
    const t = melee(sideOfUnit(a, table), sideOfUnit(b, table), a.men, rng, { rout: true });
    const cut = Math.min(t.down, b.men);
    Object.assign(b, { men: b.men - cut, down: b.down + cut, dead: b.dead + Math.min(t.dead, cut) });
    log.push({ kind: "rout", att: i, dfd: j, men: a.men, situation: "rear", rout: true, ...t });
  }
  return log;
}

// ---------- movement ----------
const allowance = u => (u.mounted ? UD.mounted_move : form(u).move);
function turnCost(u){ const n = Math.ceil(Math.max(1, u.men) / form(u).per_hex); return Math.max(1, Math.ceil(Math.min(u.width, n) / UD.turn_per)) }
const onMap = (h, size) => h[0] >= 0 && h[0] < size[0] && h[1] >= 0 && h[1] < size[1];
function fits(units, i, u, size){
  const occ = occupancy(units.filter((_, k) => k !== i));
  return footprint(u).every(row => row.every(h => onMap(h, size) && occ[hk(h)] === undefined));
}
function pathLen(units, i, goal, size, limit){
  const occ = occupancy(units.filter((_, k) => k !== i)), start = units[i].pos, seen = new Set([hk(start)]);
  let frontier = [start];
  for (let n = 0; n <= limit; n++){
    if (frontier.some(h => h[0] === goal[0] && h[1] === goal[1])) return n;
    const next = [];
    for (const h of frontier) for (let dn = 0; dn < 6; dn++){
      const x = step(h, dn);
      if (seen.has(hk(x)) || !onMap(x, size) || occ[hk(x)] !== undefined) continue;
      seen.add(hk(x));
      next.push(x);
    }
    frontier = next;
  }
  return goal[0] === start[0] && goal[1] === start[1] ? 0 : null;
}
function moveUnit(units, i, pos, facing, size){   // {ok, cost, charge, why}
  const u = units[i];
  if (u.state === "broken" || u.state === "fled") return { ok: false, why: "it is running" };
  const same = pos[0] === u.pos[0] && pos[1] === u.pos[1] && facing === u.facing;
  if (inContact(units, occupancy(units), i) && !same) return { ok: false, why: "it is in contact" };
  const turns = Math.min(mod6(facing - u.facing), mod6(u.facing - facing)), most = allowance(u) * UD.charge_move;
  const steps = pathLen(units, i, pos, size, most);
  if (steps === null) return { ok: false, why: "too far, or no way through" };
  const moved = { ...u, pos: pos.slice(), facing: mod6(facing) };
  if (!fits(units, i, moved, size)) return { ok: false, why: "no room there" };
  const cost = steps + turns * turnCost(u), after = units.map((x, k) => (k === i ? moved : x));
  const contact = inContact(after, occupancy(after), i);
  if (cost <= allowance(u)) return { ok: true, cost, charge: contact && steps > 0 };
  if (contact && u.state === "steady" && cost <= most) return { ok: true, cost, charge: true };
  return { ok: false, why: "too far" };
}
function flee(units, i, size){                   // a broken unit runs straight back; off the map it has fled
  let u = { ...units[i] };
  const back = mod6(u.facing + 3);
  for (let n = 0; n < allowance(u); n++){
    const nxt = { ...u, pos: step(u.pos, back) };
    if (!footprint(nxt).every(row => row.every(h => onMap(h, size)))) return { ...u, state: "fled" };
    if (!fits(units, i, nxt, size)) break;
    u = nxt;
  }
  return u;
}
