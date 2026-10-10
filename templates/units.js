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
  if (final === "stopped") return { severity: final, lethal: null, infection: null, graze: false, loc, mech };
  const fx = FD.effects[loc][mech][final];
  return { severity: final, lethal: fx[0], infection: fx[1], graze: isGraze(margin, critical), loc, mech };
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
const newTally = () => ({ blows: 0, missed: 0, parried: 0, stopped: 0, hits: 0, light: 0, serious: 0, critical: 0, down: 0, dead: 0, hurt: {} });
function noteHurt(t, sev, h, down){             // a wounded man: severity, death clock, infection risk, down or not
  const k = [sev, h.lethal, h.infection, down ? 1 : 0].join("|");
  t.hurt[k] = (t.hurt[k] || 0) + 1;
}
function landWound(att, dfd, margin, critical, rng, t){
  const h = rollWound(att.table, att.weapon, dfd.kit, margin, critical, rng);
  if (h.severity === "stopped"){ t.stopped++; return }
  t.hits++;
  t[h.severity]++;
  if (UD.dead_if.includes(h.lethal)){ t.dead++; t.down++; return }
  if (h.severity === "light" || h.graze){ noteHurt(t, h.graze ? "light" : h.severity, h, false); return }
  const nerve = quality(dfd.quality).nerve - (h.severity === "critical" ? 10 : 0);
  const down = rng.randint(1, 100) > nerve;
  if (down) t.down++;
  noteHurt(t, h.severity, h, down);
}
function blows(att, dfd, n, atk, dfn, rng, aim){   // aim: the heroes a blow may fall on, and how their defence shifts
  const t = newTally();
  t.blows = n;
  atk = Math.max(0, atk);
  const critAt = Math.floor(atk * FD.combat.critical_fraction);
  for (let i = 0; i < n; i++){
    const hero = aimedAt(aim.exposed, rng), r = rng.randint(1, 100);
    if (hero){ heroBlow(att, hero, { r, atk, critAt, shift: aim.shift }, rng, t); continue }
    if (r > atk){ t.missed++; continue }
    const critical = r <= critAt;
    if (!critical && dfn > 0 && rng.randint(1, 100) <= dfn){ t.parried++; continue }
    landWound(att, dfd, atk - r, critical, rng, t);
  }
  return t;
}
const attackOf = side => (side.skill ?? quality(side.quality).attack) + (side.attack || 0);   // a hero's own skill, else his unit's
// opts: {situation, charge, shaken, rout, exposed: [[hero, chance]]}
function melee(att, dfd, men, rng, opts = {}){
  const M = UD.melee, situation = opts.situation || "front";
  let tempo = M.tempo, atk = attackOf(att) - (opts.penalty || 0), dfn = quality(dfd.quality).defence + (dfd.defence || 0);
  const base = dfn;
  if (situation === "flank" || situation === "rear"){ atk += M[situation].attack; dfn += M[situation].defence }
  if (opts.charge){ atk += M.charge.attack; tempo *= M.charge.tempo }
  if (opts.shaken) atk += M.shaken.attack;
  if (opts.rout){ atk += UD.rout.attack; tempo *= UD.rout.tempo; dfn = 0 }
  const shift = dfn > 0 ? dfn - base : -1000;      // a hero's defence moves with his unit's; none if it has none
  return blows(att, dfd, countBlows(men * tempo, rng), atk, dfn, rng, { exposed: opts.exposed || [], shift });
}
function volley(att, dfd, men, hexes, rng, opts = {}){   // opts: {penalty, factor, exposed}
  const penalty = opts.penalty || 0, factor = opts.factor ?? 1;
  const band = fieldRange(att.weapon, hexes);
  if (!band) return null;
  const S = UD.missile, shots = men * (S.rate[att.weapon] ?? S.default_rate) * S.tempo * factor;
  const atk = attackOf(att) - band.penalty - penalty;
  return blows(att, dfd, countBlows(shots, rng), atk, 0, rng, { exposed: opts.exposed || [], shift: -1000 });
}

// ---------- heroes (as gravewounds/units.py) ----------
function aimedAt(exposed, rng){                    // the hero a blow falls on, or null
  for (const [hero, p] of exposed) if (hero.state === "up" && rng.random() < p) return hero;
  return null;
}
function heroBlow(att, hero, roll, rng, t){   // roll: {r, atk, critAt, shift}; his own parry, then the full wound roll on his kit
  const { r, atk, critAt, shift } = roll;
  if (r > atk) return;
  const critical = r <= critAt, dfn = hero.defence + shift;
  if (!critical && dfn > 0 && rng.randint(1, 100) <= dfn) return;
  const h = rollWound(att.table, att.weapon, hero.kit, atk - r, critical, rng);
  if (h.severity === "stopped") return;
  hero.wounds.push({ loc: h.loc, mech: h.mech, sev: h.severity, graze: h.graze });
  if (UD.dead_if.includes(h.lethal)) hero.state = "dead";
  else if (h.severity !== "light" && !h.graze && rng.randint(1, 100) > hero.nerve - (h.severity === "critical" ? 10 : 0)) hero.state = "down";
  t.heroes ??= [];
  t.heroes.push({ hero: hero.id, name: hero.name, sev: h.severity, loc: h.loc, graze: h.graze, state: hero.state });
}
const heroesOf = (u, roles) => (u.heroes || []).filter(h => h.state === "up" && roles.includes(h.role));
function exposure(u, rout, missile = false){        // [[hero, chance]] for the heroes of u a blow on it may fall on
  if (rout || missile){
    const roles = rout ? ["front", "ranged", "behind"] : ["front", "ranged"];
    return heroesOf(u, roles).map(h => [h, 1 / Math.max(1, u.men)]);
  }
  return heroesOf(u, ["front", "ranged"]).map(h => [h, Math.min(1, UD.heroes.exposure / Math.max(1, frontMen(u)))]);
}
const heroSide = (u, hero, table) => ({ table, weapon: hero.weapon, kit: hero.kit, quality: u.quality, skill: hero.attack });
function leaderState(u){
  const ls = (u.heroes || []).filter(h => h.leader);
  if (!ls.length) return u.leader;
  return ls.some(h => h.state === "up") ? "up" : "down";
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
function frontMen(u){                             // men in the front rank: the ones a blow on its front falls among
  const rows = footprint(u), men = menByHex(u);
  if (!rows.length) return 0;
  let n = 0;
  for (let k = 0; k < rows[0].length; k++) n += Math.min(form(u).abreast, men[k]);
  return n;
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
function struckHex(units, occ, u, h){            // [enemy index, direction] across the first of h's front sides with a standing enemy
  for (const dn of [u.facing, u.facing + 1]){
    const j = occ[hk(step(h, dn))];
    if (j !== undefined && units[j].side !== u.side && units[j].state !== "broken") return [j, dn];
  }
  return null;
}
function unitGroups(units, occ, i, groups, field){   // unit i's front hexes' strikes: "i|j|situation|penalty|stakes" -> men
  const u = units[i], rows = footprint(u), men = menByHex(u), reach = FD.weapons[u.weapon].reach || 1, abreast = form(u).abreast;
  const per = abreast * (reach >= UD.melee.second_rank_reach ? 2 : 1);
  (rows[0] || []).forEach((h, k) => {
    const hit = struckHex(units, occ, u, h);
    if (!hit) return;
    const [j, dn] = hit, [blocked, pen, stk] = across(field, u, h, step(h, dn), reach);
    const n = blocked ? Math.min(reach >= 2 ? abreast : 0, men[k]) : Math.min(per, men[k]);
    if (n <= 0) return;
    const key = [i, j, arc(units[j].facing, dn + 3), pen, stk ? 1 : 0].join("|");
    groups.set(key, (groups.get(key) || 0) + n);
  });
}
function strikeGroups(units, occ, field){
  const groups = new Map();
  units.forEach((u, i) => { if (!out_(u)) unitGroups(units, occ, i, groups, field) });
  return groups;
}
const cmpKey = (a, b) => { const x = a.split("|"), y = b.split("|"); return (+x[0] - +y[0]) || (+x[1] - +y[1]) || x[2].localeCompare(y[2]) || (+x[3] - +y[3]) || (+x[4] - +y[4]) };
function strikes(units, field = null){            // [{att, dfd, men, situation, rout, penalty, stakes}]
  const occ = occupancy(units), groups = strikeGroups(units, occ, field);
  const out = [...groups.keys()].sort(cmpKey).map(k => { const [i, j, sit, pen, stk] = k.split("|"); return { att: +i, dfd: +j, men: groups.get(k), situation: sit, rout: false, penalty: +pen, stakes: stk === "1" } });
  units.forEach((b, j) => {
    if (b.state !== "broken" || b.men <= 0) return;
    for (const i of adjacentUnits(units, occ, j)) if (units[i].side !== b.side && units[i].state !== "broken" && units[i].state !== "fled") out.push({ att: i, dfd: j, men: units[i].men, situation: "rear", rout: true });
  });
  return out;
}
function fvec(facing){ const a = AX[mod6(facing)], b = AX[mod6(facing + 1)], q = a[0] + b[0], r = a[1] + b[1]; return [q, r, -q - r] }
function target(units, i, field){                // [distance, index, shooter hex, target hex] of the nearest enemy in range, in sight, in front; or null
  const u = units[i], fv = fvec(u.facing), front = footprint(u)[0];
  let best = null;
  units.forEach((e, j) => {
    if (e.side === u.side || e.men <= 0 || e.state === "fled") return;
    const near = nearestAhead(u.weapon, front, fv, footprint(e).flat(), field);
    if (near && (best === null || near[0] < best[0])) best = [near[0], j, near[1], near[2]];
  });
  return best;
}
function nearestAhead(weapon, front, fv, hexes, field){  // [distance, front hex, target hex]: the shortest in range and in sight ahead of the line
  let best = null;
  for (const t of hexes){
    const c = cube(t);
    for (const h of front){
      const s = cube(h);
      if ((c[0] - s[0]) * fv[0] + (c[1] - s[1]) * fv[1] + (c[2] - s[2]) * fv[2] <= 0) continue;
      const dist = hdist(h, t);
      if ((best === null || dist < best[0]) && fieldRange(weapon, dist) && !shotWeather(field, weapon, dist).blocked) best = [dist, h, t];
    }
  }
  return best;
}
function volleys(units, field = null){            // [{att, dfd, men, dist, cover, penalty, misfire}]
  const occ = occupancy(units), out = [];
  units.forEach((u, i) => {
    if (out_(u) || !("range" in FD.weapons[u.weapon]) || inContact(units, occ, i)) return;
    const best = target(units, i, field);
    if (!best) return;
    const rows = footprint(u), men = menByHex(u), per = form(u).abreast * Math.min(UD.shoot_ranks, form(u).ranks);
    let shooters = 0;
    for (let k = 0; k < rows[0].length; k++) shooters += Math.min(per, men[k]);
    const wx = shotWeather(field, u.weapon, best[0]);
    out.push({ att: i, dfd: best[1], men: shooters, dist: best[0], cover: coverAt(field, best[2], best[3]), penalty: wx.penalty, misfire: wx.misfire });
  });
  return out;
}

// ---------- the field: ground, works and weather (as gravewounds/units.py) ----------
// field: {ground: {hex key: kind}, works: {edges, hexes}, weather: {cond, wind, ground} or null, size: [cols, rows]}
const fieldSize = field => field?.size || [UD.map.cols, UD.map.rows];
const groundAt = (field, h) => UD.ground[field?.ground?.[hk(h)] || "open"];
function across(field, u, h, x, reach){           // [blocked: only reach 2 over it, penalty %, stakes: no charge for horses]
  if (!field) return [false, 0, false];
  const [cols, rows] = fieldSize(field), m = meleeAcross(field.works, h, x, reach, cols, rows);
  let pen = m.penalty;
  if (groundAt(field, x).height && !groundAt(field, h).height) pen += groundAt(field, x).height;
  const it = hexItem(field.works, x), stk = !!(u.mounted && it && specOf("hex", it).no_horse);
  return [m.blocked, pen, stk];
}
const shotWeather = (field, weapon, dist) => weatherAttack(field?.weather || null, weapon, dist * UD.range_scale);
function coverAt(field, h, t){                    // % off shots from h at t: the best of the works' and the ground's
  if (!field) return 0;
  const [cols, rows] = fieldSize(field);
  return Math.max(missileCover(field.works, h, t, cols, rows).cover, groundAt(field, t).cover || 0);
}
const sideOfUnit = (u, table) => ({ table, weapon: u.weapon, kit: u.kit, quality: u.quality });
function takeHurt(u, t){                         // the wounded go onto the unit struck; the tally (for the log) keeps the rest
  const { hurt, ...rest } = t;
  for (const [k, n] of Object.entries(hurt)) u.hurt[k] = (u.hurt[k] || 0) + n;
  return rest;
}
function tallyLoss(acc, s, t){ acc.lost[s.dfd] += t.down; acc.dead[s.dfd] += t.dead; acc.dealt[s.att] += t.down }
const copyUnit = u => ({ ...u, hurt: { ...u.hurt }, heroes: (u.heroes || []).map(h => ({ ...h, wounds: [...(h.wounds || [])] })) });
function logged(line, t){                         // a log line for a tally, then one for each blow that fell on a hero
  const { heroes, ...rest } = t;
  return [{ ...line, ...rest }, ...(heroes || []).map(h => ({ kind: "herohit", unit: line.dfd, ...h }))];
}
function strikeAll(us, table, rng, acc, log, field){
  const struck = new Set();
  for (const s of strikes(us, field)){
    const a = us[s.att], b = us[s.dfd];
    const opts = { situation: s.situation, charge: !!a.charged && !!a.mounted && !s.stakes, shaken: a.state === "shaken", rout: s.rout, exposed: exposure(b, s.rout), penalty: s.penalty || 0 };
    let t = takeHurt(b, melee(sideOfUnit(a, table), sideOfUnit(b, table), s.men, rng, opts));
    tallyLoss(acc, s, t);
    acc.flanked[s.dfd] = acc.flanked[s.dfd] || s.situation === "flank" || s.situation === "rear";
    log.push(...logged({ kind: s.rout ? "rout" : "melee", ...s }, t));
    if (struck.has(s.att)) continue;
    struck.add(s.att);
    for (const hero of heroesOf(a, ["front"])){
      t = takeHurt(b, melee(heroSide(a, hero, table), sideOfUnit(b, table), UD.heroes.tempo, rng, opts));
      tallyLoss(acc, s, t);
      log.push(...logged({ kind: "hero", hero: hero.id, name: hero.name, att: s.att, dfd: s.dfd, situation: s.situation }, t));
    }
  }
}
function shootAll(us, table, rng, acc, log, field){
  for (const v of volleys(us, field)){
    const b = us[v.dfd], exposed = exposure(b, false, true), mf = form(b).missile_factor;
    let t = takeHurt(b, volley(sideOfUnit(us[v.att], table), sideOfUnit(b, table), v.men, v.dist, rng, { factor: mf * (100 - v.misfire) / 100, exposed, penalty: v.cover + v.penalty }));
    tallyLoss(acc, v, t);
    log.push(...logged({ kind: "volley", ...v }, t));
    for (const hero of heroesOf(us[v.att], ["ranged"])){
      const wx = shotWeather(field, hero.weapon, v.dist);
      if (!fieldRange(hero.weapon, v.dist) || wx.blocked) continue;
      const hopts = { factor: mf * (100 - wx.misfire) / 100, exposed, penalty: v.cover + wx.penalty };
      t = takeHurt(b, volley(heroSide(us[v.att], hero, table), sideOfUnit(b, table), UD.heroes.tempo, v.dist, rng, hopts));
      tallyLoss(acc, v, t);
      log.push(...logged({ kind: "hero", hero: hero.id, name: hero.name, att: v.att, dfd: v.dfd, dist: v.dist }, t));
    }
  }
}
function breachable(field, u, h){                // [kind, key, item]: the first work h's front rank can hack at
  for (const dn of [u.facing, u.facing + 1]){
    const x = step(h, dn);
    const e = edgeItems(field.works, h, x).find(it => specOf("edge", it).breach);
    if (e) return ["edge", edgeKey(h, x), e];
    const it = hexItem(field.works, x);
    if (it && specOf("hex", it).breach) return ["hex", hk(x), it];
  }
  return null;
}
function breachAll(us, field, log){               // units ordered to breach hack at the works on their front (works updated in place)
  if (!field?.works) return;
  const scale = UD.hex_m / FD.battle_hex_m, per = UD.exchange_rounds * UD.breach_share / scale;
  us.forEach((u, i) => {
    if (!u.breach || out_(u)) return;
    const rows = footprint(u), men = menByHex(u);
    (rows[0] || []).forEach((h, k) => {
      const hit = breachable(field, u, h);
      if (!hit) return;
      const [kind, where, it] = hit;
      it.progress = (it.progress || 0) + Math.min(form(u).abreast, men[k]) * per;
      if (!intact(kind, it)) log.push({ kind: "breach", unit: i, work: it.type, at: where });
    });
  });
}
function exchange(units, table, rng, field = null){   // -> {units, log}; works being breached are updated in field
  const us = units.map(copyUnit), n = us.length, log = [];
  const acc = { lost: new Array(n).fill(0), dead: new Array(n).fill(0), dealt: new Array(n).fill(0), flanked: new Array(n).fill(false) };
  strikeAll(us, table, rng, acc, log, field);
  shootAll(us, table, rng, acc, log, field);
  breachAll(us, field, log);
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
      leader: leaderState(u), flanked: acc.flanked[i], contact: near.some(j => us[j].side !== u.side), friends: near.some(j => us[j].side === u.side && us[j].state === "steady") };
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
    const t = takeHurt(b, melee(sideOfUnit(a, table), sideOfUnit(b, table), a.men, rng, { rout: true, exposed: exposure(b, true) }));
    const cut = Math.min(t.down, b.men);
    Object.assign(b, { men: b.men - cut, down: b.down + cut, dead: b.dead + Math.min(t.dead, cut) });
    log.push(...logged({ kind: "rout", att: i, dfd: j, men: a.men, situation: "rear", rout: true }, t));
  }
  return log;
}

// ---------- movement ----------
const allowance = u => (u.mounted ? UD.mounted_move : form(u).move);
function turnCost(u){ const n = Math.ceil(Math.max(1, u.men) / form(u).per_hex); return Math.max(1, Math.ceil(Math.min(u.width, n) / UD.turn_per)) }
const onMap = (h, size) => h[0] >= 0 && h[0] < size[0] && h[1] >= 0 && h[1] < size[1];
function canEnter(field, u, h){                  // no wagons; for horses, no marsh, stakes or felled trees
  const it = hexItem(field.works, h);
  if (it && (specOf("hex", it).enter === null || specOf("hex", it).enter === undefined)) return false;
  if (!u.mounted) return true;
  return !groundAt(field, h).no_horse && !(it && specOf("hex", it).no_horse);
}
const wallBetween = (field, a, b) => edgeItems(field.works, a, b).some(it => { const s = specOf("edge", it); return s.cross === null || s.cross === undefined || !!s.gate });
function stands(field, u, hexes){                 // ground it can stand on, and no palisade or wall running through it
  const keys = new Set(hexes.map(hk));
  return hexes.every(h => canEnter(field, u, h) && [0, 1, 2, 3, 4, 5].every(dn => { const x = step(h, dn); return !keys.has(hk(x)) || !wallBetween(field, h, x) }));
}
function fits(units, i, u, size, field = null){
  const occ = occupancy(units.filter((_, k) => k !== i)), hexes = footprint(u).flat();
  if (!hexes.every(h => onMap(h, size) && occ[hk(h)] === undefined)) return false;
  return !field || stands(field, u, hexes);
}
function unitStepCost(field, u, a, b){            // movement for the middle hex from a to b: works, ground, deep going; null if it cannot
  if (!field) return 1;
  if (!canEnter(field, u, b)) return null;
  const c = stepCost(field.works, a, b);
  if (c === null) return null;
  return c + groundAt(field, b).move - 1 + deepGoing(field.weather?.ground);
}
function pathLen(units, i, goal, size, limit, field = null){   // least movement for the middle hex to goal; null if more than limit
  const occ = occupancy(units.filter((_, k) => k !== i)), u = units[i];
  const best = new Map([[hk(u.pos), 0]]), done = new Set();
  let open = [[0, u.pos]];
  while (open.length){
    let m = 0;
    for (let q = 1; q < open.length; q++) if (open[q][0] < open[m][0]) m = q;
    const [cost, h] = open[m];
    open.splice(m, 1);
    if (done.has(hk(h))) continue;
    if (h[0] === goal[0] && h[1] === goal[1]) return cost;
    done.add(hk(h));
    for (let dn = 0; dn < 6; dn++){
      const x = step(h, dn);
      if (!onMap(x, size) || occ[hk(x)] !== undefined) continue;
      const sc = unitStepCost(field, u, h, x);
      if (sc === null || cost + sc > limit || cost + sc >= (best.get(hk(x)) ?? limit + 1)) continue;
      best.set(hk(x), cost + sc);
      open.push([cost + sc, x]);
    }
  }
  return null;
}
function moveUnit(units, i, pos, facing, size, field = null){   // {ok, cost, charge, why}
  const u = units[i];
  if (u.state === "broken" || u.state === "fled") return { ok: false, why: "it is running" };
  const same = pos[0] === u.pos[0] && pos[1] === u.pos[1] && facing === u.facing;
  if (inContact(units, occupancy(units), i) && !same) return { ok: false, why: "it is in contact" };
  const turns = Math.min(mod6(facing - u.facing), mod6(u.facing - facing)), most = allowance(u) * UD.charge_move;
  const steps = pathLen(units, i, pos, size, most, field);
  if (steps === null) return { ok: false, why: "too far, or no way through" };
  const moved = { ...u, pos: pos.slice(), facing: mod6(facing) };
  if (!fits(units, i, moved, size, field)) return { ok: false, why: "no room there" };
  const cost = steps + turns * turnCost(u), after = units.map((x, k) => (k === i ? moved : x));
  const contact = inContact(after, occupancy(after), i);
  if (cost <= allowance(u)) return { ok: true, cost, charge: contact && steps > 0 };
  if (contact && u.state === "steady" && cost <= most) return { ok: true, cost, charge: true };
  return { ok: false, why: "too far" };
}
function flee(units, i, size, field = null){      // a broken unit runs straight back; off the map it has fled
  let u = { ...units[i] };
  const back = mod6(u.facing + 3);
  for (let n = 0; n < allowance(u); n++){
    const nxt = { ...u, pos: step(u.pos, back) };
    if (!footprint(nxt).every(row => row.every(h => onMap(h, size)))) return { ...u, state: "fled" };
    if (unitStepCost(field, u, u.pos, nxt.pos) === null || !fits(units, i, nxt, size, field)) break;
    u = nxt;
  }
  return u;
}

// ---------- after the battle (as units.aftermath and disease.wound_case) ----------
const TR = FD.track;
const standingUnit = u => u.men > 0 && (u.state === "steady" || u.state === "shaken");
const trStep = name => TR.steps.indexOf(name);
function woundCase(sev, lethal, inf, d100){     // a man carried from the field: his case on the wound track
  const W = TR.wounds, lo = W.fever_after[0], hi = W.fever_after[1];
  const step = Math.max(trStep(W.start[sev]), trStep(W.clock_step[lethal] || "healed"));
  return { d: "wound", inc: 0, step, peak: 0, shown: 0, chronic: false, inf, fever: lo + (d100() - 1) % (hi - lo + 1) };
}
function diesOfWound(lethal, care, d100){
  const A = UD.aftermath;
  if (lethal === "minutes") return d100() > A.saved.minutes;
  if (lethal === "hours") return d100() > A.saved.hours[care];
  return false;
}
function aftermath(units, care, rng){            // per unit {left, died, cases}; care: each unit's camp care
  const A = UD.aftermath, d100 = () => rng.randint(1, 100);
  const up = new Set(units.filter(standingUnit).map(u => u.side));
  return units.map((u, i) => {
    const r = { left: 0, died: 0, cases: [] }, room = { 1: Math.max(0, (u.down || 0) - (u.dead || 0)), 0: Math.max(0, u.men) };
    const abandon = A.left_behind && !up.has(u.side);
    for (const k of Object.keys(u.hurt || {}).sort((a, b) => (a < b ? -1 : 1))){
      const [sev, lethal, inf, down] = k.split("|"), n = Math.min(u.hurt[k], room[down]);
      room[down] -= n;
      if (down === "1" && abandon){ r.left += n; continue }
      for (let m = 0; m < n; m++){
        if (diesOfWound(lethal, care[i], d100)) r.died++;
        else r.cases.push(woundCase(sev, lethal, inf, d100));
      }
    }
    return r;
  });
}
