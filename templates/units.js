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
  return { severity: final, lethal: fx[0], infection: fx[1], bleed: fx[2], pain: fx[3], shock: fx[4], graze: isGraze(margin, critical), loc, mech };
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
const fieldRange = (wid, hexes, reach = 0) => weaponReach(wid, hexes * UD.range_scale * 100 / (100 + reach));   // reach: the wind's % on the range bands
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
  const modern = UD.modern_fire.weapons.includes(att.weapon);     // breech-loaders and shell: more men stopped
  if (h.graze || (h.severity === "light" && !modern)){ noteHurt(t, "light", h, false); return }
  const down = (modern && h.severity !== "light") || rng.randint(1, 100) > quality(dfd.quality).nerve - (h.severity === "critical" ? 10 : 0);
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
function volley(att, dfd, men, hexes, rng, opts = {}){   // opts: {penalty, factor, exposed, reach (the wind's % on the range bands)}
  const penalty = opts.penalty || 0, factor = opts.factor ?? 1;
  const band = fieldRange(att.weapon, hexes, opts.reach || 0);
  if (!band) return null;
  const S = UD.missile, tempo = isMg(att.weapon) ? UD.machine_guns.tempo : S.tempo;   // a machine gun's served guns, at its own tempo
  const shots = men * (S.rate[att.weapon] ?? S.default_rate) * tempo * factor;
  const atk = attackOf(att) - band.penalty - penalty;
  return blows(att, dfd, countBlows(shots, rng), atk, 0, rng, { exposed: opts.exposed || [], shift: -1000 });
}

// ---------- heroes (as gravewounds/units.py) ----------
function aimedAt(exposed, rng){                    // the hero a blow falls on, or null
  for (const [hero, p] of exposed) if (hero.state === "up" && rng.random() < p) return hero;
  return null;
}
function heroBlow(att, hero, roll, rng, t){   // roll: {r, atk, critAt, shift}; his own parry (none if stunned; less for his wounds), the full wound roll on his kit, the roller's stop check
  const { r, atk, critAt, shift } = roll;
  if (r > atk) return;
  const critical = r <= critAt, dfn = held(hero) === "stunned" ? 0 : hero.defence + shift - heroPenalty(hero);
  if (!critical && dfn > 0 && rng.randint(1, 100) <= dfn) return;
  const h = rollWound(att.table, att.weapon, hero.kit, atk - r, critical, rng);
  if (h.severity === "stopped") return;
  const [bleed, pain, shock] = h.graze ? [Math.max(0, h.bleed - 1), Math.max(0, h.pain - 1), false] : [h.bleed, h.pain, !!h.shock];
  hero.wounds.push({ loc: h.loc, mech: h.mech, sev: h.severity, graze: h.graze, bleed, pain });
  if (UD.dead_if.includes(h.lethal)) hero.state = "dead";
  else {
    const [blood, pool] = heroBlood(hero), roll2 = checks(h.severity, shock) ? rng.randint(1, 100) : 0;
    heroCheck(hero, stopCheck(hero.nerve, h.severity, heroPain(hero), roll2, blood / pool, shock));
  }
  t.heroes ??= [];
  t.heroes.push({ hero: hero.id, name: hero.name, sev: h.severity, loc: h.loc, graze: h.graze, state: hero.state });
}
// ----- a hero's wounds, as the roller (gravewounds/combat.py stop_check, pain_check) -----
const checks = (sev, shock) => shock && FD.combat.stop_check.severities.includes(sev);
function stopTarget(nerve, sev, pain, frac){
  let target = nerve - Math.min(pain, FD.tracking.pain_cap) * FD.combat.pain_step;
  const th = bloodThreshold(frac);
  if (th) target -= th.penalty || 0;
  if (sev === "critical") target -= FD.combat.stop_check.critical_penalty;
  return target;
}
function stopCheck(nerve, sev, pain, roll, frac, shock = true){   // null if the wound calls for none; else {passed, state}
  const SC = FD.combat.stop_check;
  if (!SC.severities.includes(sev) || !shock) return null;
  const target = stopTarget(nerve, sev, pain, frac);
  if (roll <= target) return { passed: true, state: null };
  const failBy = roll - target, res = SC.results.find(x => !("upto" in x) || failBy <= x.upto);
  return { passed: false, state: res.state };
}
const painCheck = (nerve, pain, roll, frac) => (pain <= FD.tracking.pain_cap ? null : stopCheck(nerve, FD.combat.stop_check.pain_round_as, pain, roll, frac));
function heroCheck(hero, res){                    // out: down; defend only or stunned: held for his next exchange (a worse hold replaces a milder)
  if (!res || res.passed) return;
  if (res.state === "out"){ hero.state = "down"; return }
  const order = Object.keys(FD.combat.states);
  if (!hero.held || order.indexOf(res.state) >= order.indexOf(hero.held.state)) hero.held = { state: res.state, left: 2 };
}
const held = hero => (hero.held && hero.held.left > 0 ? hero.held.state : null);
const heroPain = hero => (hero.old_pain || 0) + (hero.wounds || []).reduce((a, w) => a + (w.pain || 0), 0);
function heroBlood(hero){ const pool = hero.pool || FD.tracking.blood_pool; return [hero.blood ?? pool, pool] }
const bloodThreshold = frac => [...FD.tracking.thresholds].sort((a, b) => a.at - b.at).find(x => frac <= x.at) || null;
function heroPenalty(hero){                       // % off his attack and defence: pain (to the cap) and Blood lost
  const [blood, pool] = heroBlood(hero), th = bloodThreshold(blood / pool);
  return Math.min(heroPain(hero), FD.tracking.pain_cap) * FD.combat.pain_step + (th?.penalty || 0);
}
function heroesAfter(us, rng){                    // end of an exchange: holds wear off, heroes bleed, Blood thresholds, pain checks
  const log = [];
  us.forEach((u, i) => {
    for (const hero of u.heroes || []){
      const line = hero.state === "dead" ? null : heroAfter(hero, rng);
      if (line) log.push({ kind: "herobled", unit: i, ...line });
    }
  });
  return log;
}
function heroAfter(hero, rng){                    // one hero's end of an exchange; a log line if he crossed a Blood threshold or went down
  const T = FD.tracking;
  if (hero.held) hero.held.left -= 1;
  const [blood, pool] = heroBlood(hero), wasUp = hero.state === "up";
  const lost = (hero.old_bleed || 0) + hero.wounds.reduce((a, w) => a + Math.round(T.bleed_per_round[w.bleed || 0] * UD.exchange_rounds), 0);
  if (!lost && !(wasUp && heroPain(hero) > T.pain_cap)) return null;
  const before = bloodThreshold(blood / pool);
  hero.blood = Math.max(0, blood - lost);
  const after = bloodThreshold(hero.blood / pool);
  if (wasUp && after && (after.down || after.incapacitated)) hero.state = "down";
  if (hero.blood <= 0) hero.dying = true;
  if (hero.state === "up" && heroPain(hero) > T.pain_cap) heroCheck(hero, painCheck(hero.nerve, heroPain(hero), rng.randint(1, 100), hero.blood / pool));
  if (after === before && !(wasUp && hero.state !== "up")) return null;
  return { hero: hero.id, name: hero.name, lost, blood: hero.blood, pool, state: hero.state };
}
const heroesOf = (u, roles) => (u.heroes || []).filter(h => h.state === "up" && roles.includes(h.role));
const actingOf = (u, roles) => heroesOf(u, roles).filter(h => !held(h));   // up and not held by a stop check: they strike or shoot
function exposure(u, rout, missile = false){        // [[hero, chance]] for the heroes of u a blow on it may fall on
  if (rout || missile){
    const roles = rout ? ["front", "ranged", "behind"] : ["front", "ranged"];
    return heroesOf(u, roles).map(h => [h, 1 / Math.max(1, u.men)]);
  }
  return heroesOf(u, ["front", "ranged"]).map(h => [h, Math.min(1, UD.heroes.exposure / Math.max(1, frontMen(u)))]);
}
const heroSide = (u, hero, table) => ({ table, weapon: hero.weapon, kit: hero.kit, quality: u.quality, skill: hero.attack - heroPenalty(hero) });
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
const ray = hexRay;                              // the hexes on a line (works.js)
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
function bunkerAt(field, h){                      // the intact bunker in hex h, or null
  const it = field?.works?.hexes?.[`${h[0]},${h[1]}`];
  return it && UD.assault.works.includes(it.type) && intact("hex", it) ? it : null;
}
const inBunker = (field, u) => !!field && footprint(u).flat().some(h => bunkerAt(field, h));
function unitGroups(units, occ, i, groups, field){   // unit i's front hexes' strikes: "i|j|situation|penalty|stakes" -> men
  const u = units[i], rows = footprint(u), men = menByHex(u), reach = FD.weapons[meleeWeapon(u)].reach || 1, abreast = form(u).abreast;
  const per = abreast * Math.min(reach, form(u).ranks), busy = breaching(field, u);   // a rank for each hex of reach
  (rows[0] || []).forEach((h, k) => {
    const hit = struckHex(units, occ, u, h);
    if (!hit) return;
    const [j, dn] = hit;
    if (bunkerAt(field, h) || bunkerAt(field, step(h, dn))) return;   // no blows into or out of an intact bunker: it must be stormed
    const [blocked, pen, stk] = across(field, u, h, step(h, dn), reach);
    let n = Math.min(per, men[k]);
    if (blocked) n = reach >= 2 ? Math.min(abreast, men[k]) : 0;
    if (busy.has(k)) n = Math.max(0, n - Math.min(abreast, men[k]));   // the front rank is hacking at the works
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
function target(units, i, field, occ = null){    // [distance, index, shooter hex, target hex] of the nearest enemy in range, in sight, in front; or null (a battery: its named target first, a clear line of fire)
  const u = units[i], fv = fvec(u.facing), front = footprint(u)[0];
  const named = namedTarget(units, i, field, occ, u.target);
  if (named) return named;
  let best = null;
  units.forEach((e, j) => {
    if (e.side === u.side || e.men <= 0 || e.state === "fled") return;
    const near = nearestAhead(u, front, fv, footprint(e).flat(), field, clearFn(units, occ, field, i, j));
    if (near && (best === null || near[0] < best[0])) best = [near[0], j, near[1], near[2]];
  });
  return best;
}
function namedTarget(units, i, field, occ, tid){  // a target the GM named for a battery (tid, a unit's id), if it can be fired on
  const u = units[i];
  if (!occ || tid === undefined || tid === null) return null;
  const j = units.findIndex(e => e.id !== undefined && e.id === tid);
  if (j < 0 || units[j].side === u.side || out_(units[j])) return null;
  const near = nearestAhead(u, footprint(u)[0], fvec(u.facing), footprint(units[j]).flat(), field, clearFn(units, occ, field, i, j));
  return near ? [near[0], j, near[1], near[2]] : null;
}
const clearFn = (units, occ, field, i, j) => (occ ? (h, t, dist) => lineFire(units, occ, field, i, j, [h, t, dist]) !== null : null);
function lineFire(units, occ, field, i, j, path){   // path [from hex, to hex, distance]: null if a unit between blocks the shot, else % off (bows loosing high over them)
  const [h, t, dist] = path, u = units[i], high = groundAt(field, h).height, arc = UD.line_of_fire.arcing.includes(u.weapon);
  let over = true, pen = 0;
  if (isGun(u.weapon)){
    over = dist > UD.artillery.canister_to;
    if (over && gunKind(u) === "howitzer") return 0;
  }
  for (const x of ray(h, t, dist).slice(1, -1)){
    const k = occ[hk(x)];
    if (k === undefined || k === i || k === j || (over && high && !groundAt(field, x).height)) continue;
    if (!arc) return null;
    pen = UD.line_of_fire.arc_penalty;
  }
  return pen;
}
function nearestAhead(u, front, fv, hexes, field, clear = null){  // [distance, front hex, target hex]: the shortest in range of u's weapon and in sight ahead of the line, with a line of fire
  const weapon = u.weapon;
  let best = null;
  for (const t of hexes){
    const c = cube(t);
    for (const h of front){
      const s = cube(h);
      if ((c[0] - s[0]) * fv[0] + (c[1] - s[1]) * fv[1] + (c[2] - s[2]) * fv[2] <= 0) continue;
      const dist = hdist(h, t);
      if (best !== null && dist >= best[0]) continue;
      const wx = shotWeather(field, weapon, dist, h, t), reach = (wx.reach || 0) + heightEdge(field, weapon, h, t)[1];
      if (!wx.blocked && reaches(u, dist, reach) && (!clear || clear(h, t, dist))) best = [dist, h, t];
    }
  }
  return best;
}
function volleys(units, field = null){            // [{att, dfd, men, dist, cover, penalty, misfire, reach, from, to, over}]
  const occ = occupancy(units), out = [];
  units.forEach((u, i) => {
    if (out_(u) || !("range" in FD.weapons[u.weapon]) || (inContact(units, occ, i) && !inBunker(field, u))) return;   // a bunker's men shoot out even in contact
    const best = target(units, i, field, occ);
    if (!best) return;
    const wx = shotWeather(field, u.weapon, best[0], best[2], best[3]), [up, longer] = heightEdge(field, u.weapon, best[2], best[3]);
    const v = { att: i, dfd: best[1], men: shooters(u, field), dist: best[0], cover: shareCover(field, best[2], units[best[1]]) + groundCover(units[best[1]]), penalty: wx.penalty - up, misfire: wx.misfire, reach: (wx.reach || 0) + longer, from: best[2], to: best[3],
      height: up, over: lineFire(units, occ, field, i, best[1], [best[2], best[3], best[0]]) };
    if (isMg(u.weapon)) Object.assign(v, beaten(units, occ, field, i, best));
    out.push(v);
  });
  return out;
}
// ----- machine guns and going to ground (as gravewounds/units.py) -----
const isMg = w => (UD.machine_guns?.weapons || []).includes(w);
const mgGuns = u => Math.ceil(Math.max(0, u.men) / UD.machine_guns.crew);   // one a crew, while a man of it is up
const groundCover = u => (u.prone ? UD.to_ground.cover : 0);                 // % off shots at a unit gone to ground
function shooters(u, field = null){               // a machine-gun team's served guns; any other unit's front hexes' first shoot_ranks ranks, less breaching front ranks; pinned, fewer
  let n = 0;
  if (isMg(u.weapon)) n = mgGuns(u);
  else {
    const rows = footprint(u), men = menByHex(u), ab = form(u).abreast, per = ab * Math.min(UD.shoot_ranks, form(u).ranks), busy = breaching(field, u);
    for (let k = 0; k < rows[0].length; k++) n += Math.max(0, Math.min(per, men[k]) - (busy.has(k) ? Math.min(ab, men[k]) : 0));
  }
  return u.pinned ? n * UD.suppression.fire : n;
}
// ----- indirect fire and suppression (as gravewounds/units.py) -----
function shellWeapon(table){                      // the weapon shell fragments wound as on this table, or null (no indirect fire)
  const I = UD.indirect, have = FD.tables[table]?.weapons || [];
  return [I.weapon, I.fallback].find(w => have.includes(w)) || null;
}
function markMg(us, v, under){                    // a machine gun's target, and any unit in its beaten zone, check for suppression
  if (!under || !isMg(us[v.att].weapon)) return;
  under[v.dfd] = true;
  if (v.behind !== undefined && v.behind !== null) under[v.behind] = true;
}
// a unit of `side` can see hex h to call fire on it: in sight in the weather, no woods between
const spotted = (units, field, side, h) => units.some(u => u.side === side && u.men > 0 && u.state !== "broken" && u.state !== "fled" && sees(field, u, h, sightHexes(field)));
function sightHexes(field){                       // how far the weather lets a man see, in field hexes (null: as far as the map)
  const cond = field?.weather?.cond, vis = cond && FD.weather ? FD.weather.conditions[cond].visibility : null;
  return vis === null || vis === undefined ? null : Math.floor(vis / UD.range_scale);
}
function sees(field, u, h, sight){                // any hex of u sees h: within sight, no woods between, no smoke on the line
  return footprint(u).flat().some(x => {
    const dist = hdist(x, h);
    if (sight !== null && dist > sight) return false;
    const line = ray(x, h, dist);
    return !line.slice(1, -1).some(y => groundAt(field, y).cover) && !smoked(field, line);
  });
}
function smoked(field, hexes){                    // smoke over any of these hexes
  const sm = field?.smoke;
  return !!sm && hexes.some(h => `${h[0]},${h[1]}` in sm);
}
function within(h, radius){                       // hex h and every hex within radius of it
  const out = [[h[0], h[1]]];
  for (let n = 1; n <= radius; n++) for (let a = 0; a < 6; a++){ const corner = step(h, a, n); for (let j = 0; j < n; j++) out.push(step(corner, a + 2, j)) }
  return out;
}
function indirectAll(us, table, rng, acc, log, field, under){   // every fire mission due this exchange, in the support list's order
  const weapon = shellWeapon(table);
  if (!field || !weapon) return;
  (field.support || []).forEach((b, k) => {
    const m = b.mission;
    if (!m || (m.wait || 0) > 0 || (b.rounds || 0) <= 0 || (b.tubes || 0) <= 0) return;
    fireMission({ us, table, weapon, rng, acc, log, field, under }, k, b);
  });
}
function fireMission(ctx, k, b){                  // on an enemy battery or a hex: smoke laid or men struck; located; a creeping mission moves on (ctx: us, table, weapon, rng, acc, log, field, under)
  const { rng, log, field } = ctx;
  const K = UD.indirect.kinds[b.kind], m = b.mission, shells = Math.min(b.tubes * K.rate, b.rounds);
  b.rounds -= shells;
  if (!K.direct) b.located = true;                 // tanks close behind the line are never located
  if (m.battery !== undefined && m.battery !== null) log.push(...counterFire(field, k, b, shells, K, rng));
  else {
    const bursts = [];
    for (let s = 0; s < shells; s++){ const dirn = rng.randint(0, 5), far = rng.randint(0, K.scatter); bursts.push(step(m.hex, dirn, far)) }
    log.push({ kind: "barrage", sup: k, name: b.name, side: b.side, shells, at: m.hex, bursts, smoke: !!m.smoke });
    if (m.smoke) laySmoke(field, bursts);
    else { shellUnits(ctx, k, b, bursts); knockBunkers(field, k, b, bursts, rng, log) }
  }
  missionOn(b, m, field.size);
}
function missionOn(b, m, size){                   // a single mission ends; a creeping one moves its aim on, and ends when it leaves the map
  if (!m.repeat){ b.mission = null; return }
  const cr = m.creep;
  if (!cr) return;
  for (let s = 0; s < cr.step; s++){ m.hex = step(m.hex, cr.dir + (cr.done || 0) % 2); cr.done = (cr.done || 0) + 1 }
  if (size && !(m.hex[0] >= 0 && m.hex[0] < size[0] && m.hex[1] >= 0 && m.hex[1] < size[1])) b.mission = null;
}
function counterFire(field, k, b, shells, K, rng){   // each shell knocks out one of the target battery's tubes at K's counter %
  const j = b.mission.battery, sup = field.support, tg = j >= 0 && j < sup.length ? sup[j] : null;
  if (!tg || tg.side === b.side){ b.mission = null; return [] }
  let hits = 0;
  for (let s = 0; s < shells; s++) if (rng.randint(1, 100) <= K.counter) hits++;
  const knocked = Math.min(tg.tubes, hits);
  tg.tubes -= knocked;
  if (tg.tubes <= 0) tg.mission = null;
  return [{ kind: "counter", sup: k, name: b.name, side: b.side, shells, target: j, tname: tg.name, knocked, left: tg.tubes }];
}
function laySmoke(field, bursts){                 // smoke over each burst and the hexes round it, as long as the wind lets it hang
  const S = UD.indirect.smoke, lasts = S.lasts[field.weather?.wind || "calm"], sm = field.smoke || (field.smoke = {});
  for (const at of bursts) for (const h of within(at, S.radius)){ const key = `${h[0]},${h[1]}`; sm[key] = Math.max(sm[key] || 0, lasts) }
}
function knockBunkers(field, k, b, bursts, rng, log){   // a shell bursting on a bunker's hex knocks it out at the kind's knock %
  const knock = UD.indirect.kinds[b.kind].knock || 0;
  if (!knock) return;
  for (const at of bursts){
    const it = bunkerAt(field, at);
    if (it && rng.randint(1, 100) <= knock){ it.out = true; log.push({ kind: "knocked", sup: k, name: b.name, side: b.side, at }) }
  }
}
function blastWeapon(table){                      // the weapon a storming party's grenades and charges wound as, or null
  const A = UD.assault, have = FD.tables[table]?.weapons || [];
  return [A.weapon, A.fallback].find(w => have.includes(w)) || null;
}
function assaultAll(us, table, rng, acc, log, field){   // every unit ordered to storm the bunkers across its front
  const weapon = blastWeapon(table);
  if (!field || !weapon) return;
  const occ = occupancy(us);
  us.forEach((u, i) => { if (UD.assault.means[u.assault] && !out_(u)) storm(us, occ, i, { table, weapon, rng, acc, log, field }) });
}
function storm(us, occ, i, ctx){                  // unit i storms each intact, held bunker next to its front hexes once
  const u = us[i], A = UD.assault, M = A.means[u.assault], done = new Set(), { rng, acc, log, field } = ctx;
  for (const h of footprint(u)[0] || []){
    const hit = struckHex(us, occ, u, h);
    if (!hit) continue;
    const [j, dn] = hit, x = step(h, dn), it = bunkerAt(field, x), key = `${x[0]},${x[1]}`;
    if (!it || done.has(key)) continue;
    done.add(key);
    const need = M.knock + (us[j].pinned ? A.pinned : 0), roll = rng.randint(1, 100);
    const line = { kind: "assault", unit: i, dfd: j, means: u.assault, at: x, roll, need, out: roll <= need };
    if (roll > need){ log.push(line); continue }
    it.out = true;
    const t = bunkerStruck(us, j, x, M, ctx);
    acc.dealt[i] += t.down;
    log.push(...logged(line, t));
  }
}
function bunkerStruck(us, j, x, M, ctx){          // the men in a bunker's hex when it falls: struck by blast or by flame
  const b = us[j], { table, weapon, rng, acc } = ctx, hexes = footprint(b).flat();
  const k = hexes.findIndex(h => h[0] === x[0] && h[1] === x[1]), there = k >= 0 ? menByHex(b)[k] : 0;
  let struck = 0, t;
  for (let m = 0; m < there; m++) if (rng.randint(1, 100) <= M.struck) struck++;
  if (M.flame){                                   // burns: out of the fight, no location roll; some killed outright
    t = newTally();
    Object.assign(t, { blows: struck, hits: struck, critical: struck, down: struck });
    for (let m = 0; m < struck; m++){
      if (rng.randint(1, 100) <= UD.assault.flame_dead) t.dead++;
      else noteHurt(t, "critical", { lethal: "days", infection: "high" }, true);
    }
  } else t = blows({ table, weapon, kit: null, quality: "regular" }, sideOfUnit(b, table), struck, UD.assault.attack, 0, rng, { exposed: exposure(b, false, true), shift: -1000 });
  t = takeHurt(b, t);
  acc.lost[j] += t.down; acc.dead[j] += t.dead;
  return { ...t, struck };
}
function shellUnits(ctx, k, b, bursts){           // the men struck in every unit by a battery's bursts, and their wounds
  const { us, table, weapon, rng, acc, log, field, under } = ctx;
  const I = UD.indirect, K = I.kinds[b.kind], att = { table, weapon, kit: null, quality: "regular" };
  us.forEach((u, i) => {
    const struck = shellStruckUnit(field, u, bursts, K, rng);
    if (struck === null) return;
    under[i] = true;
    if (!struck) return;
    const t = takeHurt(u, blows(att, sideOfUnit(u, table), struck, I.attack, 0, rng, { exposed: exposure(u, false, true), shift: -1000 }));
    acc.lost[i] += t.down; acc.dead[i] += t.dead;
    log.push(...logged({ kind: "shelled", sup: k, name: b.name, dfd: i, struck }, t));
  });
}
function shellStruckUnit(field, u, bursts, kind, rng){   // men of u struck by these bursts, or null if none came near
  if (u.men <= 0 || u.state === "fled") return null;
  const hexes = footprint(u).flat(), men = menByHex(u), cuts = hexes.map(h => shellCut(field, h, u.prone));
  let near = false, struck = 0;
  for (const at of bursts){
    hexes.forEach((h, j) => {
      const dist = hdist(h, at);
      if (dist > kind.radius) return;
      near = true;
      const p = kind.struck[dist] * cuts[j];
      for (let x = 0; x < men[j]; x++) if (rng.randint(1, 100) <= p) struck++;
    });
  }
  return near ? struck : null;
}
function shellCut(field, h, prone){               // shellfire's struck % times this: tree bursts in woods; else going to ground and the ground's cover
  const I = UD.indirect, TB = I.tree_burst, bk = bunkerAt(field, h);
  const shelter = bk ? (100 - (WK.hex_works[bk.type].cover_here || 0)) / 100 : 1;   // a bunker's men get its cover against shell too
  if (TB.ground.includes(field?.ground?.[`${h[0]},${h[1]}`] || "open")) return TB.factor * (prone ? TB.prone : 1) * shelter;
  return (prone ? I.prone : 1) * (100 - (groundAt(field, h).cover || 0)) / 100 * shelter;
}
function suppressAll(us, under, rng){             // under fire: Nerve or pinned for the next exchange
  const S = UD.suppression, log = [];
  us.forEach((u, i) => {
    if (!under[i] || u.men <= 0 || u.state === "broken" || u.state === "fled") return;
    const target = quality(u.quality).nerve + (u.prone ? S.prone : 0), roll = rng.randint(1, 100);
    if (roll > target){ u.pinned = 2; log.push({ kind: "pinned", unit: i, roll, target }) }
  });
  return log;
}
function beaten(units, occ, field, i, best){      // {behind, beyond, bcover}: the first other unit in the beaten zone past the target
  const [dist, j, h, t] = best, line = ray(h, t, dist + UD.machine_guns.beaten.beyond).slice(dist);
  for (let k = 0; k < line.length; k++){
    if (groundAt(field, line[k]).stops_shot) break;
    const b = occ[hk(line[k])];
    if (k > 0 && b !== undefined && b !== i && b !== j) return { behind: b, beyond: k, bcover: (groundAt(field, line[k]).cover || 0) + groundCover(units[b]) };
  }
  return { behind: null, beyond: 0, bcover: 0 };
}
function beatenFire(us, table, rng, acc, log, v){ // the cone falling on into the unit behind the target
  const bh = us[v.behind], r = { ...v, dfd: v.behind, dist: v.dist + v.beyond, men: v.men * UD.machine_guns.beaten.share / 100 };
  const opts = { factor: form(bh).missile_factor * (100 - v.misfire) / 100, exposed: exposure(bh, false, true), penalty: v.bcover + v.penalty, reach: v.reach };
  const hits = volley(sideOfUnit(us[v.att], table), sideOfUnit(bh, table), r.men, r.dist, rng, opts);
  if (!hits) return;
  const t = takeHurt(bh, hits);
  tallyLoss(acc, r, t);
  log.push(...logged({ kind: "beaten", ...r }, t));
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
const upOf = field => field?.up || "N";          // the compass point at the top of the field map
const SMOKED = { blocked: "Smoke: no one can see to shoot through it.", penalty: 0, misfire: 0, reach: 0 };
function shotWeather(field, weapon, dist, h = null, t = null){   // the weather on a shot from h to t; smoke on the line blocks it
  if (h && t && smoked(field, ray(h, t, dist))) return { ...SMOKED };
  return isGun(weapon) ? gunWeather(field, dist, h, t) : weatherAttack(field?.weather || null, weapon, dist * UD.range_scale, h, t, upOf(field));
}
const reaches = (u, dist, reach = 0) => (isGun(u.weapon) ? dist <= gunRange(u) : !!fieldRange(u.weapon, dist, reach));   // a battery's guns to their range
function shareCover(field, h, target){            // % off a volley from h at a unit: the average cover of its row nearest h, rounded down
  if (!field) return 0;
  const rows = footprint(target);
  if (!rows.length) return 0;
  let row = rows[0], near = Infinity;
  for (const r of rows){ const m = Math.min(...r.map(t => hdist(h, t))); if (m < near){ near = m; row = r } }
  return Math.floor(row.reduce((a, t) => a + coverAt(field, h, t), 0) / row.length);
}
function heightEdge(field, weapon, h, t){         // [% to hit, % longer range bands]: down from high ground +, up at it -; none for guns
  if (!field || isGun(weapon)) return [0, 0];
  const a = !!groundAt(field, h).height, b = !!groundAt(field, t).height, H = UD.high_ground;
  if (a && !b) return [H.shoot, H.reach];
  return b && !a ? [-H.shoot, 0] : [0, 0];
}
function coverAt(field, h, t){                    // % off shots from h at t: the best of the works' and the ground's
  if (!field) return 0;
  const [cols, rows] = fieldSize(field);
  return Math.max(missileCover(field.works, h, t, cols, rows).cover, groundAt(field, t).cover || 0);
}
const sideOfUnit = (u, table) => ({ table, weapon: u.weapon, kit: u.kit, quality: u.quality });
const meleeSide = (u, table) => ({ ...sideOfUnit(u, table), weapon: meleeWeapon(u) });   // hand to hand: a battery's crews fight with their own weapon
function takeHurt(u, t){                         // the wounded go onto the unit struck; the tally (for the log) keeps the rest
  const { hurt, ...rest } = t;
  for (const [k, n] of Object.entries(hurt)) u.hurt[k] = (u.hurt[k] || 0) + n;
  return rest;
}
function tallyLoss(acc, s, t){ acc.lost[s.dfd] += t.down; acc.dead[s.dfd] += t.dead; acc.dealt[s.att] += t.down }
const copyUnit = u => ({ ...u, hurt: { ...u.hurt }, heroes: (u.heroes || []).map(h => ({ ...h, wounds: [...(h.wounds || [])], ...(h.held ? { held: { ...h.held } } : {}) })) });
function logged(line, t){                         // a log line for a tally, then one for each blow that fell on a hero
  const { heroes, ...rest } = t;
  return [{ ...line, ...rest }, ...(heroes || []).map(h => ({ kind: "herohit", unit: line.dfd, ...h }))];
}
function pikeFront(u){                            // steady, in a pike formation, with a pike: a front horse cannot charge home on
  const P = UD.melee.pikes;
  return u.state === "steady" && P.formations.includes(u.formation) && P.weapons.includes(meleeWeapon(u)) && !u.mounted;
}
function strikeAll(us, table, rng, acc, log, field){
  const struck = new Set(), dueled = new Set();
  for (const s of strikes(us, field)){
    const a = us[s.att], b = us[s.dfd];
    const charge = !!a.charged && !!a.mounted && !s.stakes && !(s.situation === "front" && pikeFront(b));   // no charge home onto a front of pikes
    const vsHorse = b.mounted && pikeFront(a) ? UD.melee.pikes.attack : 0;
    const opts = { situation: s.situation, charge, shaken: a.state === "shaken", rout: s.rout, exposed: exposure(b, s.rout), penalty: (s.penalty || 0) - vsHorse };
    const t = takeHurt(b, melee(meleeSide(a, table), meleeSide(b, table), s.men, rng, opts));
    tallyLoss(acc, s, t);
    acc.flanked[s.dfd] = acc.flanked[s.dfd] || s.situation === "flank" || s.situation === "rear";
    log.push(...logged({ kind: s.rout ? "rout" : "melee", ...s }, t));
    if (struck.has(s.att)) continue;
    struck.add(s.att);
    frontHeroes([a, b], s, { table, rng, acc, log }, opts, dueled);
  }
}
function frontHeroes(units, s, ctx, opts, dueled){   // a striking unit's front heroes: each duels the enemy's first free front hero, or strikes its rankers
  const [a, b] = units, { table, rng, acc, log } = ctx;
  for (const hero of actingOf(a, ["front"])){
    if (dueled.has(hero.id)) continue;
    const foe = s.rout ? null : heroesOf(b, ["front"]).find(h => !dueled.has(h.id)) || null;
    if (foe){ log.push(...duel([a, b], [hero, foe], table, rng, s, dueled)); continue }
    const t = takeHurt(b, melee(heroSide(a, hero, table), meleeSide(b, table), UD.heroes.tempo, rng, opts));
    tallyLoss(acc, s, t);
    log.push(...logged({ kind: "hero", hero: hero.id, name: hero.name, att: s.att, dfd: s.dfd, situation: s.situation }, t));
  }
}
function duel(units, pair, table, rng, s, dueled){   // two front heroes fight each other: heroes.duel attempts each, the first unit's hero first
  const [a, b] = units, [hero, foe] = pair, log = [];
  dueled.add(hero.id); dueled.add(foe.id);
  for (const [x, y, ux, k] of [[hero, foe, a, s.att], [foe, hero, b, s.dfd]]){
    if (x.state !== "up" || held(x) || y.state !== "up") continue;
    const side = heroSide(ux, x, table), atk = Math.max(0, side.skill), critAt = Math.floor(atk * FD.combat.critical_fraction), t = newTally();
    t.blows = countBlows(UD.heroes.duel, rng);
    for (let n = 0; n < t.blows; n++){
      if (y.state !== "up") break;
      heroBlow(side, y, { r: rng.randint(1, 100), atk, critAt, shift: 0 }, rng, t);
    }
    log.push({ kind: "duel", unit: k, hero: x.id, name: x.name, foe: y.id, fname: y.name, blows: t.blows },
      ...(t.heroes || []).map(h => ({ kind: "herohit", unit: k === s.att ? s.dfd : s.att, ...h })));
  }
  return log;
}
function shootAll(us, table, rng, acc, log, field, under = null){
  for (const v of volleys(us, field)){
    markMg(us, v, under);
    const b = us[v.dfd], exposed = exposure(b, false, true), mf = form(b).missile_factor;
    let t = takeHurt(b, volley(sideOfUnit(us[v.att], table), sideOfUnit(b, table), v.men, v.dist, rng, { factor: mf * (100 - v.misfire) / 100, exposed, penalty: v.cover + v.penalty + v.over, reach: v.reach }));
    tallyLoss(acc, v, t);
    log.push(...logged({ kind: "volley", ...v }, t));
    if (v.behind !== undefined && v.behind !== null) beatenFire(us, table, rng, acc, log, v);
    for (const hero of actingOf(us[v.att], ["ranged"])){
      const wx = shotWeather(field, hero.weapon, v.dist, v.from, v.to);
      if (wx.blocked) continue;
      const [up, longer] = heightEdge(field, hero.weapon, v.from, v.to);
      if (!fieldRange(hero.weapon, v.dist, wx.reach + longer)) continue;
      const hopts = { factor: mf * (100 - wx.misfire) / 100, exposed, penalty: v.cover + wx.penalty - up + v.over, reach: wx.reach + longer };
      t = takeHurt(b, volley(heroSide(us[v.att], hero, table), sideOfUnit(b, table), UD.heroes.tempo, v.dist, rng, hopts));
      tallyLoss(acc, v, t);
      log.push(...logged({ kind: "hero", hero: hero.id, name: hero.name, att: v.att, dfd: v.dfd, dist: v.dist }, t));
    }
  }
  for (const c of cannonades(us, field)) fireBattery(us, table, rng, acc, log, c);
}
function fireBattery(us, table, rng, acc, log, c){   // at the target, guns knocked out there, then balls bounding on into the unit behind
  const a = us[c.att], b = us[c.dfd], gun = sideOfUnit(a, table);
  let t = takeHurt(b, cannonade(gun, b, c, rng, exposure(b, false, true)));
  a.spent = (a.spent || 0) + c.rounds;
  if (b.id !== undefined && b.id !== null) a.fired = { ...(a.fired || {}), [String(b.id)]: c.dist };
  if (t.dismounted) b.guns_lost = (b.guns_lost || 0) + t.dismounted;
  tallyLoss(acc, c, t);
  log.push(...logged({ kind: "cannon", ...c }, t));
  if (c.behind === null) return;
  const r = { ...c, dfd: c.behind }, bh = us[r.dfd];
  t = takeHurt(bh, ricochet(gun, bh, c, rng, exposure(bh, false, true)));
  tallyLoss(acc, r, t);
  log.push(...logged({ kind: "ricochet", ...r }, t));
}
function breaching(field, u){                     // indexes of the front hexes whose front rank is breaching the works
  if (!field?.works || !u.breach) return new Set();
  return new Set((footprint(u)[0] || []).map((h, k) => (breachable(field, u, h) ? k : -1)).filter(k => k >= 0));
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
  const under = new Array(n).fill(false);          // under shellfire or machine-gun fire this exchange (suppression)
  for (const c of closingFire(us, field)) fireBattery(us, table, rng, acc, log, c);
  strikeAll(us, table, rng, acc, log, field);
  shootAll(us, table, rng, acc, log, field, under);
  indirectAll(us, table, rng, acc, log, field, under);
  assaultAll(us, table, rng, acc, log, field);
  breachAll(us, field, log);
  const occ = occupancy(us), before = us.map(u => u.men);
  us.forEach((u, i) => {
    const cut = Math.min(acc.lost[i], u.men);
    Object.assign(u, { men: u.men - cut, down: (u.down || 0) + cut, dead: (u.dead || 0) + Math.min(acc.dead[i], cut) });
  });
  log.push(...moraleAll(us, occ, before, acc, rng, table), ...suppressAll(us, under, rng), ...heroesAfter(us, rng));
  afterExchange(us, field);
  return { units: us, log };
}
function afterExchange(us, field){                // charges spent, batteries changed over, pins wear off, missions come due
  for (const u of us){
    u.charged = false;
    batteryAfter(u);
    if (u.pinned) u.pinned -= 1;
  }
  for (const b of field?.support || []) if (b.mission && (b.mission.wait || 0) > 0) b.mission.wait -= 1;
  if (field?.smoke) field.smoke = Object.fromEntries(Object.entries(field.smoke).filter(([, n]) => n > 1).map(([h, n]) => [h, n - 1]));   // smoke thins
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
    const t = takeHurt(b, melee(meleeSide(a, table), meleeSide(b, table), a.men, rng, { rout: true, exposed: exposure(b, true) }));
    const cut = Math.min(t.down, b.men);
    Object.assign(b, { men: b.men - cut, down: b.down + cut, dead: b.dead + Math.min(t.dead, cut) });
    log.push(...logged({ kind: "rout", att: i, dfd: j, men: a.men, situation: "rear", rout: true }, t));
  }
  return log;
}

// ---------- movement ----------
function allowance(u){                            // hexes a unit may move (twice for a charge); a battery changing over or resupplying not at all, unlimbered a hex or so
  if ((u.prone || u.pinned) && u.state !== "broken" && u.state !== "fled") return 0;   // gone to ground or pinned: no move
  if (isBattery(u) && !u.abandoned && u.state !== "broken"){   // crews running from their guns run on foot
    if (u.limbering || u.resupplying) return 0;
    if (!u.limbered) return UD.artillery.pushed;
  }
  return u.mounted ? UD.mounted_move : form(u).move;
}
function turnCost(u){ const n = Math.ceil(Math.max(1, u.men) / form(u).per_hex); return Math.max(1, Math.ceil(Math.min(u.width, n) / UD.turn_per)) }
const onMap = (h, size) => h[0] >= 0 && h[0] < size[0] && h[1] >= 0 && h[1] < size[1];
function canEnter(field, u, h){                  // no wagons or water; for horses, no marsh, stakes or felled trees
  if (groundAt(field, h).impassable) return false;
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
  const best = new Map([[hk(u.pos), 0]]), done = new Set(), open = [[0, u.pos]];
  while (open.length){
    const [cost, h] = popCheapest(open);
    if (done.has(hk(h))) continue;
    if (h[0] === goal[0] && h[1] === goal[1]) return cost;
    done.add(hk(h));
    for (const [x, c] of stepsFrom(field, u, h, occ, size)){
      if (cost + c > limit || cost + c >= (best.get(hk(x)) ?? limit + 1)) continue;
      best.set(hk(x), cost + c);
      open.push([cost + c, x]);
    }
  }
  return null;
}
function popCheapest(open){                      // take the [cost, hex] with the least cost (the first of equals)
  let m = 0;
  for (let q = 1; q < open.length; q++) if (open[q][0] < open[m][0]) m = q;
  return open.splice(m, 1)[0];
}
function stepsFrom(field, u, h, occ, size){       // [hex, cost] for each step the middle hex can take from h: the worst its front row pays
  const out = [], front = field ? footprint({ ...u, pos: h })[0] || [] : [h];
  for (let dn = 0; dn < 6; dn++){
    const x = step(h, dn);
    if (!onMap(x, size) || occ[hk(x)] !== undefined) continue;
    const sc = frontCost(field, u, front, dn, size);
    if (sc !== null) out.push([x, sc]);
  }
  return out;
}
function frontCost(field, u, front, dn, size){    // the worst step cost of a front row's hexes stepping in direction dn (off the map: not counted)
  let worst = 0;
  for (const f of front){
    const y = step(f, dn);
    if (!onMap(y, size)) continue;
    const c = unitStepCost(field, u, f, y);
    if (c === null) return null;
    worst = Math.max(worst, c);
  }
  return worst || 1;
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

// ---------- guns (as gravewounds/units.py) ----------
// A battery: a unit whose weapon is a gun (units.yaml artillery), its men the crews. u.limbered:
// moves, cannot fire; u.limbering: changing over this exchange; u.abandoned: broke and left its guns.
const isGun = w => (UD.artillery?.guns || []).includes(w);
const isBattery = u => isGun(u.weapon);
const meleeWeapon = u => (isBattery(u) ? UD.artillery.crew_weapon : u.weapon);
const gunsOf = u => Math.ceil((u.start ?? u.men) / UD.artillery.crew);   // the guns it brought into action
const gunsServed = u => Math.max(0, Math.min(gunsOf(u) - (u.guns_lost || 0), Math.ceil(Math.max(0, u.men) / UD.artillery.crew)));
const ammoLeft = u => Math.max(0, gunsOf(u) * UD.artillery.ammo - (u.spent || 0));
function gunWeather(field, dist, h = null, t = null){   // no laying guns on what cannot be seen (less with rain or snow in the gunners' faces); the wind as on firearms
  const out = { blocked: null, penalty: 0, misfire: 0, reach: 0 }, w = field?.weather;
  if (!w) return out;
  const cond = WXD.conditions[w.cond];
  let vis = cond.visibility;
  if (vis !== null && vis !== undefined && cond.precip !== "none" && windLie(w, h, t, upOf(field)) === "against") vis = Math.floor(vis * WXD.driven_sight / 100);
  if (vis !== null && vis !== undefined && dist * UD.range_scale > vis){ out.blocked = `${cond.name}: the guns cannot be laid on what cannot be seen.`; return out }
  out.penalty = WXD.winds.find(x => x.id === w.wind).firearm;
  return out;
}
const chanceAt = (bands, dist) => (bands.find(([to]) => dist <= to) || [0, 0])[1];
const canFire = u => isBattery(u) && !out_(u) && !u.abandoned && !u.limbered && !u.limbering && !u.resupplying && gunsServed(u) > 0 && ammoLeft(u) > 0;
function cannonades(units, field = null){         // [{att, dfd, guns, rounds, dist, shot, cover, penalty, named, graze, behind, beyond, fuse, section}]: a battery's fire, and its section's
  const occ = occupancy(units), out = [], A = UD.artillery;
  units.forEach((u, i) => {
    if (!A || !canFire(u) || inContact(units, occ, i)) return;
    const best = target(units, i, field, occ);
    if (best) out.push(...batteryFires(units, occ, field, i, best));
  });
  return out;
}
function batteryFires(units, occ, field, i, best){   // the battery's fire at best, and its section's at the section's target if it split one off
  const u = units[i], guns = gunsServed(u), ammo = ammoLeft(u), sec = u.section || {};
  const n = Math.min(sec.guns || 0, guns - 1), at = n > 0 ? namedTarget(units, i, field, occ, sec.target) : null;
  const main = batteryFire(units, [occ, field], i, best, { guns: at ? guns - n : guns, ammo, shot: u.shot });
  if (!at || ammo <= main.rounds) return [main];
  return [main, batteryFire(units, [occ, field], i, at, { guns: n, ammo: ammo - main.rounds, shot: sec.shot, section: true })];
}
function batteryFire(units, ground, i, best, order){   // guns of battery i at best; order {guns, ammo, shot, per, section}
  const [occ, field] = ground, A = UD.artillery, u = units[i];
  const wx = gunWeather(field, best[0], best[2], best[3]), shot = shotKind(u, best[0], order.shot);
  const behind = shot === "round" ? ricochetAt(occ, field, i, best) : null, tgt = units[best[1]], tid = tgt.id;
  const graze = shot === "canister" && best[0] > A.canister.strike[0][0] && firmLine(field, best) ? A.canister.graze : 0;
  return { att: i, dfd: best[1], guns: order.guns, rounds: Math.min(order.guns * (order.per ?? A.rounds), order.ammo), dist: best[0], shot, cover: coverAt(field, best[2], best[3]) + groundCover(tgt), penalty: wx.penalty,
    named: !!order.section || (tid !== undefined && tid !== null && tid === u.target), graze, bore: gunKind(u), behind: behind ? behind[0] : null, beyond: behind ? behind[1] : 0,
    fuse: shot === "shell" ? fuseSetting(u, tid, best[0]) : 0, section: !!order.section };
}
function fuseSetting(u, tid, dist){               // how far the gunners' cut fuses widen the air band: crew quality, and more on a target ranged last exchange
  const F = UD.artillery.set_fuse;
  if (!F) return 0;
  const was = tid === undefined || tid === null ? undefined : (u.laid || {})[String(tid)];
  return (F.quality[u.quality] || 0) + (was !== undefined && Math.abs(was - dist) <= F.within ? F.ranged : 0);
}
function closingFire(units, field = null){        // batteries charged in front: canister at the first charger as it comes in (closing: true)
  const A = UD.artillery, out = [];
  if (!A || A.closing === undefined) return out;
  const occ = occupancy(units);
  units.forEach((u, i) => {
    const best = canFire(u) ? charger(units, occ, field, i) : null;
    if (best) out.push({ ...batteryFire(units, [occ, field], i, best, { guns: gunsServed(u), ammo: ammoLeft(u), shot: "canister", per: A.closing }), named: false, closing: true });
  });
  return out;
}
function charger(units, occ, field, i){           // [distance, index, gun hex, its hex] of the first enemy that charged battery i in front, or null
  const u = units[i], front = footprint(u)[0], fv = fvec(u.facing);
  for (const j of adjacentUnits(units, occ, i)){
    const e = units[j];
    if (e.side === u.side || !e.charged || out_(e)) continue;
    const near = nearestAhead(u, front, fv, footprint(e).flat(), field);
    if (near) return [near[0], j, near[1], near[2]];
  }
  return null;
}
const gunKind = u => u.guns || (u.howitzer ? "howitzer" : "smoothbore");   // smoothbore, rifled or howitzer (howitzer: true, saved before)
const gunRange = u => (gunKind(u) === "rifled" ? UD.artillery.rifled.range : UD.artillery.range);
function shotKind(u, dist, want = null){          // the shot ordered if the guns fire it and it reaches; else canister within canister range, beyond it shell from howitzers and rifles, round shot from smoothbores
  const A = UD.artillery;
  if ((A.shots?.[gunKind(u)] || []).includes(want) && (want !== "canister" || dist <= A.canister_to)) return want;
  if (dist <= A.canister_to) return "canister";
  return gunKind(u) === "smoothbore" ? "round" : "shell";
}
function firmLine(field, best){                   // firm ground from the gun to the target hex
  const [dist, , h, t] = best;
  return !softGround(field) && !ray(h, t, dist).slice(1).some(x => groundAt(field, x).stops_shot);
}
function softGround(field){                       // mud or snow deep enough to stop a ball bounding
  const g = field?.weather?.ground || {}, soft = UD.artillery.ricochet.soft;
  return (g.mud || 0) >= soft || (g.snow || 0) >= soft;
}
function ricochetAt(occ, field, i, best){          // [unit index, hexes past the target] a bounding ball can strike, or null
  if (softGround(field)) return null;
  const [dist, j, h, t] = best, line = ray(h, t, dist + UD.artillery.ricochet.beyond).slice(dist);
  for (let k = 0; k < line.length; k++){
    if (groundAt(field, line[k]).stops_shot) return null;
    const u = occ[hk(line[k])];
    if (k > 0 && u !== undefined && u !== i && u !== j) return [u, k];
  }
  return null;
}
function canisterStruck(A, c, cut, rounds, rng){   // men hit by canister: each ball a chance (more on firm ground)
  const p = (chanceAt(A.canister.strike, c.dist) + (c.graze || 0)) * cut, balls = c.bore === "rifled" ? A.rifled.canister_balls : A.canister.balls;
  let struck = 0;
  for (let k = 0; k < rounds * balls; k++) if (rng.randint(1, 100) <= p) struck++;
  return struck;
}
function shellStruck(A, c, factor, rounds, rng){  // [men hit, shells that burst on the unit, of them in the air]: the fuse decides early, air, ground or blind
  const H = A.howitzer, R = c.bore === "rifled" ? A.rifled : H, p = chanceAt(R.strike, c.dist) * factor, fuses = setFuse(R.fuse, c.fuse || 0);   // rifled shell: its own strike and percussion fuse
  const hitAt = { air: H.air_hit * (100 - c.cover / 2) / 100, ground: H.fragment_hit * (100 - c.cover) / 100 };
  let struck = 0, bursts = 0, air = 0;
  for (let k = 0; k < rounds; k++){
    if (rng.randint(1, 100) > p) continue;
    const fuse = chanceAt(fuses, rng.randint(1, 100));
    if (!(fuse in hitAt)) continue;
    bursts++;
    if (fuse === "air") air++;
    for (let m = 0; m < H.fragments; m++) if (rng.randint(1, 100) <= hitAt[fuse]) struck++;
  }
  return [struck, bursts, air];
}
function setFuse(bands, by){                     // the fuse table with its air band widened by `by` (narrowed if negative), never past its neighbours
  return bands.map(([to, what], k) => {
    if (what !== "air" || !by) return [to, what];
    const lo = k ? bands[k - 1][0] : 0, hi = k + 1 < bands.length ? bands[k + 1][0] : 100;
    return [Math.max(lo, Math.min(hi, to + by)), what];
  });
}
function roundShotStruck(A, p, rounds, target, rng){   // [men hit, balls that struck]: each ball that strikes (p %) goes through the ranks
  const rs = A.round_shot, path = Math.min(rs.path_max, form(target).ranks * footprint(target).length);
  let struck = 0, hits = 0;
  for (let k = 0; k < rounds; k++){
    if (rng.randint(1, 100) > p) continue;
    hits++;
    for (let m = 0; m < path; m++) if (rng.randint(1, 100) <= rs.file) struck++;
  }
  return [struck, hits];
}
function cannonade(att, target, c, rng, exposed = []){   // a battery's fire at the target unit: the men struck, then a wound roll each; guns knocked out
  const A = UD.artillery, rounds = c.rounds, cut = form(target).missile_factor * (100 - c.cover - c.penalty) / 100;
  let struck, hits = 0, air = 0;
  if (c.shot === "canister") struck = canisterStruck(A, c, cut, rounds, rng);
  else if (c.shot === "shell") [struck, hits, air] = shellStruck(A, c, form(target).missile_factor * (100 - c.penalty) / 100, rounds, rng);
  else [struck, hits] = roundShotStruck(A, chanceAt(A.round_shot.strike, c.dist) * cut, rounds, target, rng);
  const t = blows(att, sideOfUnit(target, att.table), struck, A.attack, 0, rng, { exposed, shift: -1000 });
  if (c.shot === "shell"){ t.bursts = hits; t.air = air }
  if (isBattery(target)){
    let n = 0;
    for (let k = 0; k < hits; k++) if (rng.randint(1, 100) <= A.dismount) n++;
    t.dismounted = Math.min(n, gunsServed(target));
  }
  return t;
}
function ricochet(att, target, c, rng, exposed = []){   // balls bounding on into the unit behind the target
  const A = UD.artillery, p = chanceAt(A.ricochet.strike, c.beyond) * form(target).missile_factor;
  const [struck] = roundShotStruck(A, p, c.rounds, target, rng);
  return blows(att, sideOfUnit(target, att.table), struck, A.attack, 0, rng, { exposed, shift: -1000 });
}
function batteryAfter(u){                          // end of an exchange: changing over is done, resupply is in; a broken battery has left its guns
  if (!isBattery(u)) return;
  u.laid = u.fired || {};
  delete u.fired;
  if (u.resupplying){ u.spent = 0; u.resupplying = false }
  if (u.limbering){ u.limbered = !u.limbered; u.limbering = false }
  if (u.state === "broken" || u.state === "fled") u.abandoned = true;
}
