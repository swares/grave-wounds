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
  return { severity: final, lethal: fx[0], infection: fx[1], bleed: fx[2], pain: fx[3], shock: fx[4], impair: fx[5] || [], graze: isGraze(margin, critical), loc, mech };
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
  const shot = volleyShots(att, men, hexes, rng, opts);
  return shot ? blows(att, dfd, shot[0], shot[1], 0, rng, { exposed: opts.exposed || [], shift: -1000 }) : null;
}
function volleyShots(att, men, hexes, rng, opts = {}){   // [aimed shots, attack %] of a volley, or null out of range
  const penalty = opts.penalty || 0, factor = opts.factor ?? 1;
  const band = fieldRange(att.weapon, hexes, opts.reach || 0);
  if (!band) return null;
  const S = UD.missile, tempo = isMg(att.weapon) ? UD.machine_guns.tempo : S.tempo;   // a machine gun's served guns, at its own tempo
  const shots = men * (S.rate[att.weapon] ?? S.default_rate) * tempo * factor;
  return [countBlows(shots, rng), attackOf(att) - band.penalty - penalty];
}

// ---------- heroes (as gravewounds/units.py) ----------
function aimedAt(exposed, rng){                    // the hero a blow falls on, or null
  for (const [hero, p] of exposed) if (hero.state === "up" && rng.random() < p) return hero;
  return null;
}
function heroBlow(att, hero, roll, rng, t){   // roll: {r, atk, critAt, shift}; his own parry (none if stunned; less for his wounds), the full wound roll on his kit, the roller's stop check
  const { r, atk, critAt, shift } = roll;
  if (r > atk) return;
  const critical = r <= critAt, dfn = held(hero) === "stunned" ? 0 : hero.defence + shift - heroPenalties(hero)[1];
  if (!critical && dfn > 0 && rng.randint(1, 100) <= dfn) return;
  const h = rollWound(att.table, att.weapon, hero.kit, atk - r, critical, rng);
  if (h.severity === "stopped") return;
  const [bleed, pain, shock] = h.graze ? [Math.max(0, h.bleed - 1), Math.max(0, h.pain - 1), false] : [h.bleed, h.pain, !!h.shock];
  hero.wounds.push({ loc: h.loc, mech: h.mech, sev: h.severity, graze: h.graze, bleed, pain, impair: (h.impair || []).slice() });
  if (UD.dead_if.includes(h.lethal)) hero.state = "dead";
  else if (heroPenalties(hero)[2].some(f => f === "down" || f === "incapacitated")) hero.state = "down";   // a wound that fells him or knocks him out
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
function heroPenalties(hero){                     // [% off attack, % off defence, flags]: pain, Blood lost, impairments (old and new), sickness, as the roller
  const C = FD.combat, T = FD.tracking, [blood, pool] = heroBlood(hero);
  const ws = [...(hero.old?.length ? hero.old : [{ loc: null, pain: hero.old_pain || 0, impair: [] }]), ...(hero.wounds || [])];
  const pain = Math.min(ws.reduce((a, w) => a + (w.pain || 0), 0), T.pain_cap) * C.pain_step;
  let attack = pain, defence = pain;
  const flags = new Set(), th = bloodThreshold(blood / pool);
  if (th){ attack += th.penalty || 0; defence += th.penalty || 0; for (const f of ["down", "incapacitated"]) if (th[f]) flags.add(f) }
  const [a, df, f] = impairments(ws, hero.hand || "R"), rule = FD.in_fight?.[hero.sick || ""] || {};
  f.forEach(x => flags.add(x));
  for (const k of ["defend_only", "out"]) if (rule[k]) flags.add(k);
  attack += a + (rule.penalty || 0); defence += df + (rule.penalty || 0);
  return [Math.min(attack, C.cap), Math.min(defence, C.cap), [...flags].sort((x, y) => (x < y ? -1 : 1))];
}
function impairments(ws, hand){                     // [% off attack, % off defence, flags] from wounds' impairments, each counted once (an arm's by which arm)
  let attack = 0, defence = 0;
  const seen = new Set(), flags = new Set();
  for (const [key, eff] of ws.flatMap(w => (w.impair || []).map(imp => impairEffect(w, imp, hand)))){
    if (seen.has(key)) continue;
    seen.add(key);
    attack += eff.attack || 0; defence += eff.defence || 0;
    for (const x of ["down", "off_hand", "no_shield", "incapacitated"]) if (eff[x]) flags.add(x);
  }
  if ([...seen].some(k => (FD.combat.one_arm || []).includes(k.split("|")[0]))) flags.add("one_arm");   // an arm hurt: no two-handed weapon
  return [attack, defence, flags];
}
function impairEffect(w, imp, hand){              // [key, effect] of impairment imp on wound w: an arm's by which arm it is
  const rule = FD.combat.impair[imp] || {};
  if (!("weapon_arm" in rule) && !("shield_arm" in rule)) return [imp + "|", rule];
  const loc = FD.locations[w.loc] || {}, arm = loc.zone === "arms" && (loc.side === "L" || loc.side === "R") && loc.side !== hand ? "shield_arm" : "weapon_arm";
  return [imp + "|" + arm, rule[arm] || {}];
}
function heroesAfter(us, rng, quiet = null, cautery = false, closed = new Set()){   // closed: the sides whose aid post is moving this exchange (no first aid there)
   // end of an exchange: holds wear off, first aid (quiet exchange, or at the aid post), heroes bleed (with the unit, lying out, going back or at the post), Blood thresholds, pain checks; bearers back
  const log = [];
  us.forEach((u, i) => {
    for (const hero of u.heroes || []){
      if (hero.state === "dead" || hero.state === "prisoner" || (hero.carried && !hero.post)) continue;   // off the map: out of the battle
      const aid = hero.post && closed.has(u.side) ? null : aidFor(u, hero, rng, !!quiet?.[i], cautery);
      if (aid) log.push({ kind: "heroaid", unit: i, ...aid });
      const line = heroAfter(hero, rng);
      if (line) log.push({ kind: "herobled", unit: i, ...line });
    }
  });
  return [...log, ...bearersBack(us)];
}
function aidFor(u, hero, rng, quiet, cautery){    // first aid this exchange: at the aid post always (heroes.aid_post.first_aid); with his unit in a quiet exchange
  if (hero.post) return firstAid(hero, rng, [UD.heroes.aid_post.first_aid, "the aid post"], cautery);
  if (quiet && !offField(hero)) return firstAid(hero, rng, healerOf(u), cautery);
  return null;
}
const offField = h => !!(h.left || h.carried || h.going);   // left behind, on his way back, or carried to the rear or the aid post: out of his unit's fight
const quarterOf = table => UD.heroes.quarter[FD.tables[table]?.battle] ?? UD.heroes.quarter.default;   // % a man the enemy finds lying out is taken prisoner, else killed
const postsMoving = field => new Set((field?.posts || []).filter(p => p.moving).map(p => p.side));   // the sides whose aid post is moving this exchange (as units.posts_moving)
function postsSettle(field){                       // after the exchange a moving aid post counts down; at 0 it is open again (as units._posts_settle)
  for (const p of field?.posts || []) if (p.moving){ p.moving -= 1; if (p.moving <= 0) delete p.moving }
}
const aidPost = (field, side) => (field?.posts || []).find(p => p.side === side && !p.overrun) || null;   // side's aid post, if not overrun
const party = (u, bearers) => ({ pos: [...u.pos], bearers, dir: mod6(u.facing + 3), ex: 0 });   // a party setting off back: where, its bearers, the way back, exchanges going
function partiesAfter(us, field){                 // each party goes on along the cheapest way toward its post (or the map edge the way back); arriving, he is carried and the bearers head back (as units._parties_after)
  const log = [];
  us.forEach((u, i) => {
    for (const hero of u.heroes || []){
      if (!hero.going) continue;
      const stop = partyStops(u, hero);
      for (const line of stop ? [stop] : partyMoves(us, field, i, hero)) log.push({ kind: "party", unit: i, hero: hero.id, name: hero.name, ...line });
    }
  });
  return log;
}
function partyStops(u, hero){                      // its hero killed or taken (bearers go back), or unable to walk with no bearers (he lies there)
  const g = hero.going;
  if (hero.state === "dead" || hero.state === "prisoner"){ delete hero.going; bearersOff(u, g); return { what: "stopped", at: g.pos } }
  if (g.bearers <= 0 && lame(hero)){ delete hero.going; hero.left = true; hero.at = g.pos; return { what: "lies", at: g.pos } }
  return null;
}
function partyMoves(us, field, i, hero){          // [its log line] or []: on along the cheapest way toward the post or the edge; arriving, the hero is carried (as units._party_moves)
  const u = us[i], g = hero.going, post = aidPost(field, u.side);
  g.ex += 1;
  const [way, note] = partyWay(us, field, i, [g, post]), noted = note ? [note] : [];
  if (way === null) return noted;
  g.pos = way[0];
  if (!way[1]) return noted;
  delete hero.going;
  hero.carried = true;
  if (post && !g.no_way) hero.post = true;
  bearersOff(u, g);
  return [{ what: g.no_way || !post ? "edge" : "post", at: [...g.pos] }];
}
function partyWay(us, field, i, [g, post]){       // [[where it gets this exchange, arrived?] or null, a log line or null]: to the post if a way leads there, else the edge the way back, else any edge (as units.party_way)
  const u = us[i], size = fieldSize(field), pos = [...g.pos], walker = { side: u.side, mounted: false };
  const blocked = new Set(us.filter(e => e.side !== u.side && e.men > 0).flatMap(e => footprint(e).flat().map(hk)));
  blocked.delete(hk(pos));
  let note = null, ways = post && !g.no_way ? waysTo(field, walker, [post.at], blocked, size) : new Map(), aim = ways.has(hk(pos)) ? post.at : null;
  if (post && !ways.has(hk(pos)) && !g.no_way){ g.no_way = true; note = { what: "no_way", at: [...post.at] } }
  if (!ways.has(hk(pos))){ aim = mapEdge(field, pos, g.dir); ways = waysTo(field, walker, [aim], blocked, size) }
  if (!ways.has(hk(pos))) ways = waysTo(field, walker, borderHexes(size), blocked, size);
  if (!ways.has(hk(pos))) return [null, note];
  return [goAlong(field, walker, [pos, aim], ways, blocked), note];
}
function borderHexes([cols, rows]){              // every hex on the map's edge, in column then row order (as units._border)
  const out = [];
  for (let c = 0; c < cols; c++) for (let r = 0; r < rows; r++) if (c === 0 || c === cols - 1 || r === 0 || r === rows - 1) out.push([c, r]);
  return out;
}
function waysTo(field, walker, aims, blocked, size){   // Map hex -> least movement from it to the nearest aim, not through blocked hexes (as units._ways_to)
  const best = new Map(), todo = new Map([[0, []]]);
  for (const a of aims) if (!blocked.has(hk(a))){ best.set(hk(a), 0); todo.get(0).push(a) }
  let k = 0;
  while (todo.size){
    const now = todo.get(k) || [];
    todo.delete(k);
    for (const y of now) if (best.get(hk(y)) === k) relaxInto(field, walker, y, k, [best, todo, blocked, size]);
    k += 1;
  }
  return best;
}
function relaxInto(field, walker, y, k, [best, todo, blocked, size]){   // each neighbour stepping into y more cheaply gets its new least movement and waits in todo (as units._relax_into)
  for (let dn = 0; dn < 6; dn++){
    const x = step(y, dn);
    if (!onMap(x, size) || blocked.has(hk(x))) continue;
    const c = unitStepCost(field, walker, x, y);
    if (c === null || k + c >= (best.get(hk(x)) ?? 1e9)) continue;
    best.set(hk(x), k + c);
    if (!todo.has(k + c)) todo.set(k + c, []);
    todo.get(k + c).push(x);
  }
}
function goAlong(field, walker, [start, aim], ways, blocked){   // [where it gets, arrived?]: down the ways, nearest the straight line toward aim, while the pace lasts, at least a step (as units._go_along)
  const line = ray([...start], aim, hdist(start, aim));
  let pos = start, left = UD.heroes.aid_post.pace, moved = false;
  while (ways.get(hk(pos)) > 0){
    const nxt = nextDown(field, walker, pos, ways, blocked, line);
    if (!nxt || (moved && nxt[1] > left)) break;
    [pos, left, moved] = [nxt[0], left - nxt[1], true];
  }
  return [[...pos], ways.get(hk(pos)) === 0];
}
function nextDown(field, walker, pos, ways, blocked, line){   // [hex, cost] of the step down the ways nearest the line, the first by direction of equals (as units._next_down)
  let best = null;
  for (let dn = 0; dn < 6; dn++){
    const x = step(pos, dn);
    if (!ways.has(hk(x)) || blocked.has(hk(x))) continue;
    const c = unitStepCost(field, walker, pos, x);
    if (c === null || c + ways.get(hk(x)) !== ways.get(hk(pos))) continue;
    const off = Math.min(...line.map(y => hdist(x, y)));
    if (best === null || off < best[0]) best = [off, x, c];
  }
  return best?.slice(1) ?? null;
}
function bearersOff(u, g){                         // a party's bearers set off back to their unit, due after as many exchanges as it went
  if (g.bearers > 0) u.away = [...(u.away || []), { men: g.bearers, left: Math.max(1, g.ex) }];
}
function mapEdge(field, h, dirn){                  // the last hex on the map going from h in direction dirn
  const [cols, rows] = fieldSize(field);
  for (;;){
    const x = step(h, dirn);
    if (x[0] < 0 || x[0] >= cols || x[1] < 0 || x[1] >= rows) return [...h];
    h = x;
  }
}
function lyingAfter(us, table, rng){              // heroes lying out on a hex: picked up by a unit of their side standing there, or taken or killed by an enemy one (as units._lying_after)
  const log = [], occ = occupancy(us);
  us.forEach((u, i) => {
    for (const hero of (u.heroes || []).filter(h => h.left && h.at && h.state !== "dead" && h.state !== "prisoner")){
      const j = occ[hk(hero.at)];
      if (hero.left_by !== undefined && (j === undefined || us[j].id !== hero.left_by)) delete hero.left_by;   // the unit that left him has moved off: it may come back for him
      if (j === undefined || out_(us[j]) || us[j].vehicle || hero.left_by !== undefined) continue;
      if (us[j].side === u.side){
        u.heroes.splice(u.heroes.indexOf(hero), 1);
        delete hero.left; delete hero.at;
        us[j].heroes = [...(us[j].heroes || []), { ...hero, role: "behind" }];
        log.push({ kind: "fetched", unit: j, from: i, hero: hero.id, name: hero.name });
      }
      else log.push({ kind: "found", unit: i, by: j, ...taken(hero, table, rng) });
    }
  });
  return log;
}
function taken(hero, table, rng){                 // found by the enemy: prisoner at the war's quarter %, else killed
  const roll = rng.randint(1, 100), chance = quarterOf(table), fate = roll <= chance ? "prisoner" : "killed";
  hero.state = roll <= chance ? "prisoner" : "dead";
  delete hero.post;
  return { hero: hero.id, name: hero.name, fate, roll, chance };
}
function postsAfter(us, field, table, rng){       // an aid post with an enemy unit (not out) within heroes.aid_post.overrun hexes is overrun: its heroes taken or killed
  const log = [], reach = UD.heroes.aid_post.overrun;
  for (const p of field?.posts || []){
    if (p.overrun || !us.some(u => u.side !== p.side && !out_(u) && footprint(u).flat().some(x => hdist(x, p.at) <= reach))) continue;
    p.overrun = true;
    log.push({ kind: "overrun_post", side: p.side, at: p.at });
    us.forEach((u, i) => {
      for (const h of u.heroes || []) if (h.post && u.side === p.side && h.state !== "dead" && h.state !== "prisoner") log.push({ kind: "found", unit: i, at_post: true, ...taken(h, table, rng) });
    });
  }
  return log;
}
function shellParties(ctx, bursts, kind, att){    // shell bursts near parties going back: the hero and each bearer struck as men in the open (as units._shell_parties)
  const { us, field, rng, log } = ctx;
  us.forEach((u, i) => {
    for (const hero of u.heroes || []){
      if (!hero.going || hero.state === "dead" || hero.state === "prisoner") continue;
      const line = shellParty(field, u, hero, [bursts, kind, att], rng);
      if (line) log.push({ kind: "partyhit", unit: i, ...line });
    }
  });
}
function shellParty(field, u, hero, [bursts, kind, att], rng){
  const g = hero.going, cut = shellCut(field, g.pos, false);
  let hits = 0, struck = 0;
  for (const at of bursts){
    const dist = hdist(g.pos, at);
    if (dist > kind.radius) continue;
    const p = kind.struck[dist] * cut;
    if (rng.randint(1, 100) <= p) hits++;
    for (let b = 0; b < g.bearers; b++) if (rng.randint(1, 100) <= p) struck++;
  }
  if (!hits && !struck) return null;
  const atk = UD.indirect.attack, t = blows(att, sideOfUnit(u, att.table), struck, atk, 0, rng, { exposed: [], shift: -1000 });
  const th = newTally(), critAt = Math.floor(atk * FD.combat.critical_fraction);
  for (let k = 0; k < hits; k++) if (hero.state !== "dead") heroBlow(att, hero, { r: rng.randint(1, 100), atk, critAt, shift: -1000 }, rng, th);
  g.bearers -= t.down;
  Object.assign(u, { down: (u.down || 0) + t.down, dead: (u.dead || 0) + t.dead });
  takeHurt(u, t);
  return { hero: hero.id, name: hero.name, at: g.pos, struck, down: t.down, dead: t.dead, hits: th.heroes || [], state: hero.state };
}
const cauterises = table => UD.heroes.cautery.battles.includes(FD.tables[table]?.battle);   // the battle's era cauterises where a tourniquet cannot go
function bearersBack(us){                         // each party of bearers counts down; due back, it rejoins a unit still standing, else stays at the rear
  const log = [];
  us.forEach((u, i) => {
    if (!u.away?.length) return;
    const due = u.away.map(a => ({ ...a, left: a.left - 1 }));
    const stands = (u.state === "steady" || u.state === "shaken") && u.men > 0;
    const back = stands ? due.filter(a => a.left <= 0).reduce((n, a) => n + a.men, 0) : 0;
    u.away = due.filter(a => a.left > 0 || !back);
    if (back){ u.men += back; log.push({ kind: "bearers", unit: i, men: back }) }
  });
  return log;
}
function carryBack(units, i, heroId, field = null){   // unit i sends bearers to carry the hero back: to its side's aid post as a party, else off the map at once: null, or why not (as units.carry_back)
  const H = UD.heroes, u = units[i], hero = (u.heroes || []).find(h => h.id === heroId);
  if (!hero || !lamed(hero)) return "he can walk, or is not with the unit";
  if (u.state !== "steady" && u.state !== "shaken") return "the unit is running";
  if (u.men <= H.bearers) return `the unit has not ${H.bearers} men to spare`;
  u.men -= H.bearers;
  if (aidPost(field, u.side)){ hero.going = party(u, H.bearers); return null }
  hero.carried = true;
  u.away = [...(u.away || []), { men: H.bearers, left: H.back_after }];
  return null;
}
function walkBack(units, i, heroId){              // a wounded hero who can walk leaves his unit and goes back alone (as units.walk_back): null, or why not
  const u = units[i], hero = (u.heroes || []).find(h => h.id === heroId);
  if (hero?.state !== "up" || offField(hero)) return "he is not up with the unit";
  if (lamed(hero)) return "he cannot walk: carry him back";
  if (!hero.wounds?.length && !hero.old?.length) return "he is not wounded";
  hero.going = party(u, 0);
  return null;
}
function leaveBehind(units, i, heroId){           // a lamed or down hero left on his unit's hex, to be fetched or found (as units.leave): null, or why not
  const u = units[i], hero = (u.heroes || []).find(h => h.id === heroId);
  if (!hero || !lamed(hero)) return "he can walk, or is not with the unit";
  Object.assign(hero, { left: true, at: [...u.pos], left_by: u.id });
  return null;
}
function heroFates(units, table, rng){            // after the battle: heroes left on the field found, taken prisoner or killed (as units.hero_fates)
  const out = [];
  const stands = u => u.men > 0 && (u.state === "steady" || u.state === "shaken");
  const up = new Set(units.filter(stands).map(u => u.side)), chance = quarterOf(table);
  units.forEach((u, i) => {
    const gone = !stands(u);
    for (const h of u.heroes || []){
      if (h.state === "dead" || h.state === "prisoner" || h.carried || !(h.left || h.going || (gone && h.state === "down"))) continue;
      if (up.has(u.side) || !up.size){ out.push({ unit: i, hero: h.id, name: h.name, fate: "found" }); continue }
      const roll = rng.randint(1, 100);
      out.push({ unit: i, hero: h.id, name: h.name, fate: roll <= chance ? "prisoner" : "killed", roll, chance });
    }
  });
  return out;
}
function healerOf(u){                             // [Leechcraft, name] of u's best healer: heroes up with Leechcraft, and its medics while it has men; or null
  const up = (u.heroes || []).filter(h => h.state === "up" && !offField(h) && Number.isFinite(h.leech)).map(h => [h.leech, h.name]);
  if (u.medics && u.men > 0) up.push([UD.heroes.medic[u.medic_quality || u.quality], "the medics"]);
  if (!up.length) return null;
  return up.reduce((a, b) => (b[0] > a[0] ? b : a), up[0]);
}
function firstAid(hero, rng, healer = null, cautery = false){   // his worst-bleeding wound (this battle's or one he came with): Leechcraft % or heroes.first_aid %; tourniquet a limb, cauterise the body (older eras), or bind
  const ws = [...hero.wounds, ...(hero.old || [])].filter(w => (w.bleed || 0) > 0);
  if (!ws.length) return null;
  const w = ws.reduce((a, b) => (b.bleed > a.bleed ? b : a), ws[0]), H = UD.heroes;
  const line = { hero: hero.id, name: hero.name, loc: w.loc, ...(healer ? { by: healer[1] } : {}) };
  if (rng.randint(1, 100) > (healer ? healer[0] : H.first_aid)) return { ...line, stopped: false, bleed: w.bleed };
  const limb = ["arms", "legs"].includes(FD.locations[w.loc]?.zone);
  let how = "bind";
  if (limb && w.bleed >= H.tourniquet_from){ w.bleed = 0; how = "tourniquet" }
  else if (cautery && !limb && w.bleed >= H.cautery.from_bleed){
    w.bleed = 0; how = "cauterise";
    if (!healer){ w.pain = Math.min(FD.tracking.pain_cap, (w.pain || 0) + H.cautery.pain); sumOldPain(hero, w) }
  }
  else w.bleed = Math.max(0, w.bleed - (healer ? FD.combat.first_aid.bind : 1));
  w.aid = how;                                      // the roller marks it treated (on the field) when he goes back
  if ((hero.old || []).includes(w)) hero.old_bleed = hero.old.reduce((a, o) => a + Math.round(FD.tracking.bleed_per_round[o.bleed || 0] * UD.exchange_rounds), 0);
  return { ...line, stopped: true, bleed: w.bleed, how };
}
function sumOldPain(hero, w){                     // an old wound's pain changed: his old pain is theirs again
  if ((hero.old || []).includes(w)) hero.old_pain = hero.old.reduce((a, o) => a + (o.pain || 0), 0);
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
const heroesOf = (u, roles) => (u.heroes || []).filter(h => h.state === "up" && !offField(h) && roles.includes(h.role));
const actingOf = (u, roles) => heroesOf(u, roles).filter(heroStrikes);   // up, and able to strike or shoot this exchange
function heroStrikes(hero){                           // not held by a stop check, not too sick to do more than defend, not hurt in an arm (one_arm) with a two-handed weapon
  if (held(hero) || hero.defend_only) return false;
  return !(FD.weapons[hero.weapon]?.two_handed && heroPenalties(hero)[2].includes("one_arm"));
}
function lamed(hero){                             // a hero who slows his unit: not dead or off the field, and cannot walk (lame)
  if (hero.state === "dead" || offField(hero)) return false;
  return lame(hero);
}
function lame(hero){                              // down, or lamed by a wound (heroes.lamed): he cannot walk
  const L = UD.heroes.lamed;
  return hero.state !== "up" || [...(hero.old || []), ...(hero.wounds || [])].some(w => (w.impair || []).some(i => L.includes(i)));
}
function exposure(u, rout, missile = false){        // [[hero, chance]] for the heroes of u a blow on it may fall on
  if (rout || missile){
    const roles = rout ? ["front", "ranged", "behind"] : ["front", "ranged"];
    return heroesOf(u, roles).map(h => [h, 1 / Math.max(1, u.men)]);
  }
  return heroesOf(u, ["front", "ranged"]).map(h => [h, Math.min(1, UD.heroes.exposure / Math.max(1, frontMen(u)))]);
}
const heroSide = (u, hero, table) => ({ table, weapon: hero.weapon, kit: hero.kit, quality: u.quality, skill: hero.attack - heroPenalties(hero)[0] });
function leaderState(u){
  const ls = (u.heroes || []).filter(h => h.leader);
  if (!ls.length) return u.leader;
  return ls.some(h => h.state === "up" && !offField(h)) ? "up" : "down";
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
  if (u.dug) m += mods.dug_in || 0;
  if (u.no_ammo) m += mods.no_ammo || 0;
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
function form(u){                                 // a unit's formation; a vehicle unit's is one vehicle a hex at its kind's move
  const F = UD.formations[u.formation], K = vehicleKind(u);
  return K ? { ...F, per_hex: K.crew, move: K.move } : F;
}
const vehicleKind = u => (u.vehicle ? UD.vehicles.kinds[u.vehicle] : null);   // a vehicle unit's kind, or null
const vehiclesLeft = (u, lost = 0) => { const K = vehicleKind(u); return K ? Math.ceil(Math.max(0, u.men - lost) / K.crew) : 0 };
const armourOf = u => { const K = vehicleKind(u); return K ? UD.vehicles.armour[u.armour || K.armour] : null };   // its own (a battlefield's armour), else its kind's
const hurtsArmour = weapon => weapon in (UD.vehicles?.anti_armour || {});
const soft = u => { const K = vehicleKind(u); return !!K && "small" in UD.vehicles.armour[K.armour] };   // a soft-skinned vehicle unit: small arms can hurt it
function shotAtVehicle(weapon){                    // a weapon's line at vehicles: anti_armour, else small arms on the armour's small row (as units._shot_at_vehicle)
  const V = UD.vehicles;
  if (weapon in (V.anti_armour || {})) return V.anti_armour[weapon];
  return { rate: UD.machine_guns.weapons.includes(weapon) ? V.small_arms.mg : V.small_arms.rate, row: "small" };
}
function bearing(t, h){                            // the direction (0-5) from hex t that points most nearly at hex h (the first of equals)
  const a = cube(t), b = cube(h), v = [b[0] - a[0], b[1] - a[1], b[2] - a[2]];
  const dots = AX.map(([q, r]) => v[0] * q + v[1] * r + v[2] * (-q - r));
  return dots.indexOf(Math.max(...dots));
}
function killChance(u, row, h, t){                 // % a hit from h on vehicle unit u (at t) knocks one out: its armour's row %, x aspect for a flank or rear shot, to 100
  const A = armourOf(u), side = h && t && (h[0] !== t[0] || h[1] !== t[1]) ? arc(u.facing, bearing(t, h)) : "front";
  if (side === "front" && A.front?.[row] !== undefined) return A.front[row];   // composite armour: proof from the front
  return Math.min(100, Math.trunc(A[row] * (UD.vehicles.aspect?.[side] ?? 1)));
}
function harm(u, n, lost, rng){                    // hits that did not knock a vehicle out: on the turret (damage.turret %) or the hull, each may immobilise one or put its gun out -> {immobilised, gun, turret}
  const D = UD.vehicles.damage, left = vehiclesLeft(u, lost), out = { immobilised: 0, gun: 0, turret: 0 };
  for (let s = 0; s < n; s++){
    const turret = rng.randint(1, 100) <= D.turret, P = turret ? D.turret_hit : D.hull_hit;
    if (turret) out.turret++;
    const r = rng.randint(1, 100);
    if (r <= P.immobilised) out.immobilised++;
    else if (r <= P.immobilised + P.gun) out.gun++;
  }
  u.immobile = Math.min(left, (u.immobile || 0) + out.immobilised);
  u.gunless = Math.min(left, (u.gunless || 0) + out.gun);
  return out;
}
function harmLine(h){
  const o = {};
  if (h.immobilised) o.immobilised = h.immobilised;
  if (h.gun) o.gun_out = h.gun;
  if (h.turret) o.turret = h.turret;
  return o;
}
function ridersLine(k){
  const o = {};
  if (k.riders_struck) o.rstruck = k.riders_struck;
  if (k.riders_down) o.rdown = k.riders_down;
  if (k.riders_dead) o.rdead = k.riders_dead;
  return o;
}
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
    const [blocked, pen0, stk] = across(field, u, h, step(h, dn), reach);
    const climbing = blocked && reach < 2 && hasLadders(u), pen = pen0 + (climbing ? UD.escalade.penalty : 0);
    const defends = blocked && reach < 2 && !climbing && hasLadders(units[j]);   // the defenders on the wall strike at the men on the ladders, a rank of them
    let n = Math.min(defends ? abreast : per, men[k]);
    if (blocked && !defends) n = reach >= 2 ? Math.min(abreast, men[k]) : climbers(men[k], abreast, climbing);
    if (busy.has(k)) n = Math.max(0, n - Math.min(abreast, men[k]));   // the front rank is hacking at the works
    if (n <= 0) return;
    const key = [i, j, arc(units[j].facing, dn + 3), pen, stk ? 1 : 0].join("|");
    groups.set(key, (groups.get(key) || 0) + n);
  });
}
function climbers(men, abreast, climbing){       // across a wall with ladders: escalade.share of the front rank, at least one (as units._hex_strikers)
  return climbing && men > 0 ? Math.max(1, Math.floor(Math.min(abreast, men) * UD.escalade.share)) : 0;
}
function strikeGroups(units, occ, field){
  const groups = new Map();
  units.forEach((u, i) => { if (!out_(u)) unitGroups(units, occ, i, groups, field) });
  return groups;
}
const cmpKey = (a, b) => { const x = a.split("|"), y = b.split("|"); return (+x[0] - +y[0]) || (+x[1] - +y[1]) || x[2].localeCompare(y[2]) || (+x[3] - +y[3]) || (+x[4] - +y[4]) };
function strikes(units, field = null){            // [{att, dfd, men, situation, rout, penalty, stakes}]
  const occ = occupancy(units), groups = strikeGroups(units, occ, field);
  const out = [...groups.keys()].sort(cmpKey).map(k => { const [i, j, sit, pen, stk] = k.split("|"); return { att: +i, dfd: +j, men: groups.get(k), situation: sit, rout: false, penalty: +pen, stakes: stk === "1" } })
    .filter(s => !units[s.att].vehicle && !units[s.dfd].vehicle);   // no one fights a vehicle hand to hand
  units.forEach((b, j) => {
    if (b.state !== "broken" || b.men <= 0 || b.vehicle) return;
    for (const i of adjacentUnits(units, occ, j)) if (units[i].side !== b.side && units[i].state !== "broken" && units[i].state !== "fled" && !units[i].vehicle) out.push({ att: i, dfd: j, men: units[i].men, situation: "rear", rout: true });
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
    if (e.side === u.side || e.men <= 0 || e.state === "fled" || (e.vehicle && !hurtsArmour(u.weapon) && !soft(e) && !exposed(e))) return;   // small arms do not shoot at armoured vehicles
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
  const [h, t, dist] = path, u = units[i], high = heightAt(field, h), arc = UD.line_of_fire.arcing.includes(u.weapon);
  let over = true, pen = 0;
  if (isGun(u.weapon)){
    over = dist > UD.artillery.canister_to;
    if (over && gunKind(u) === "howitzer") return 0;
  }
  for (const x of ray(h, t, dist).slice(1, -1)){
    const k = occ[hk(x)];
    if (k === undefined || k === i || k === j || (over && high > heightAt(field, x))) continue;
    if (!arc) return null;
    pen = UD.line_of_fire.arc_penalty;
  }
  return pen;
}
const beyondReach = (weapon, dist) => !isGun(weapon) && !FD.weapons[weapon].off_map && fieldRange(weapon, dist, 100) === null;   // out of range even with its bands doubled (the wind and height add at most half): a shortcut that changes nothing (as units._beyond_reach)
function canShoot(u, field, [h, t, dist], clear){  // u's weapon reaches from h to t, in sight, with a line of fire (as units._can_shoot)
  if (beyondReach(u.weapon, dist)) return false;   // out of range however the wind and height help: no need to look
  const wx = shotWeather(field, u.weapon, dist, h, t, seerOf(u)), reach = (wx.reach || 0) + heightEdge(field, u.weapon, h, t)[1];
  return !wx.blocked && reaches(u, dist, reach) && (!clear || clear(h, t, dist));
}
function nearestAhead(u, front, fv, hexes, field, clear = null){  // [distance, front hex, target hex]: the shortest in range of u's weapon and in sight ahead of the line, with a line of fire
  let best = null;
  for (const t of hexes){
    const c = cube(t);
    for (const h of front){
      const s = cube(h);
      if ((c[0] - s[0]) * fv[0] + (c[1] - s[1]) * fv[1] + (c[2] - s[2]) * fv[2] <= 0) continue;
      const dist = hdist(h, t);
      if ((best === null || dist < best[0]) && canShoot(u, field, [h, t, dist], clear)) best = [dist, h, t];
    }
  }
  return best;
}
function volleys(units, field = null){            // [{att, dfd, men, dist, cover, penalty, misfire, reach, from, to, over}]; riders shooting from vehicles too (riders: true)
  const occ = occupancy(units), out = [];
  units.forEach((u, i) => {
    if (out_(u) || busyDigging(u) || (inContact(units, occ, i) && !inBunker(field, u))) return;   // a bunker's men shoot out even in contact
    if ("range" in FD.weapons[u.weapon] && ammoState(u) !== "out" && !(u.resupplying && ammoFull(u))) out.push(...volleyOf(units, occ, field, i));
    out.push(...riderVolley(units, occ, field, i));
  });
  return out;
}
function volleyOf(units, occ, field, i, men = null){   // unit i's volley at its target ([v] or []); men: the shooters (default its front ranks) (as units._volley_of)
  const u = units[i];
  let best = target(units, i, field, occ), blind = false;
  if (!best && men === null){ best = fixedTarget(units, i, field, occ); blind = !!best }
  if (!best) return [];
  const wx = shotWeather(field, u.weapon, best[0], best[2], best[3], seerOf(u, { blind })), [up, longer] = heightEdge(field, u.weapon, best[2], best[3]);
  if (wx.blocked) return [];
  const shots = men === null ? shooters(u, field) : men;
  const v = { att: i, dfd: best[1], men: men === null && ammoState(u) === "low" ? shots / 2 : shots, dist: best[0], cover: shareCover(field, best[2], units[best[1]]) + groundCover(units[best[1]]) + shieldCover(units[best[1]], best[3], best[2]), penalty: wx.penalty - up, misfire: wx.misfire, reach: (wx.reach || 0) + longer, from: best[2], to: best[3],
    height: up, over: lineFire(units, occ, field, i, best[1], [best[2], best[3], best[0]]), seen: seenShare(field, units[best[1]], best[3], u.weapon) };
  for (const k of ["blind", "flash", "beam"]) if (wx[k]) v[k] = true;
  if (men === null && isMg(u.weapon)) Object.assign(v, beaten(units, occ, field, i, best));
  return [v];
}
function riderShooters(u){                         // riders who can shoot: through an IFV's ports or from a tank's hull, rider_fire share (as units.rider_shooters)
  const K = vehicleKind(u), R = u.riders;
  if (!K || !R || R.men <= 0 || ROUTED.has(R.state) || !("range" in FD.weapons[R.weapon])) return 0;
  const F = UD.vehicles.rider_fire;
  let share = 0;
  if (K.ports) share = F.ports;
  else if (K.rides) share = F.hull;
  return Math.floor(R.men * share);
}
function riderVolley(units, occ, field, i){         // the riders' volley from vehicle unit i, with their own weapon (as units._rider_volley)
  const R = units[i].riders, all = riderShooters(units[i]);
  if (all <= 0 || ammoState(R) === "out") return [];
  const n = ammoState(R) === "low" ? all / 2 : all, pseudo = units.map((x, k) => (k === i ? { ...x, weapon: R.weapon, kit: R.kit, quality: R.quality, nv: R.nv } : x));
  return volleyOf(pseudo, occ, field, i, n).map(v => ({ ...v, riders: true }));
}
const shooterOf = (us, v) => (v.riders ? us[v.att].riders : us[v.att]);   // the unit a volley is fired by
function fixedTarget(units, i, field, occ){         // [distance, index, shooter hex, target hex]: a machine gun on a fixed line firing blind in the dark at the nearest enemy near the line
  const u = units[i];
  if (!u.fixed || !isMg(u.weapon) || !lightOf(field)) return null;
  const front = footprint(u)[0], h = front[Math.floor(front.length / 2)], n = hdist(h, u.fixed);
  if (n === 0) return null;
  const line = ray(h, u.fixed, n).slice(1), width = FD.weather.light.fixed_line.width;
  let best = null;
  units.forEach((e, j) => {
    if (e.side === u.side || out_(e) || e.vehicle) return;
    for (const t of footprint(e).flat()){
      const dist = hdist(h, t);
      if ((best !== null && dist >= best[0]) || Math.min(...line.map(x => hdist(t, x))) > width || !reaches(u, dist)) continue;
      if (lineFire(units, occ, field, i, j, [h, t, dist]) !== null) best = [dist, j, h, t];
    }
  });
  return best;
}
// ----- machine guns and going to ground (as gravewounds/units.py) -----
const isMg = w => (UD.machine_guns?.weapons || []).includes(w);
const mgGuns = u => Math.ceil(Math.max(0, u.men) / UD.machine_guns.crew);   // one a crew, while a man of it is up
const dugHere = u => !!u.dug && u.dug[0] === u.pos[0] && u.dug[1] === u.pos[1];   // it stands where it dug in (it leaves its holes when it moves)
const low = u => !!(u.prone || ((u.emplaced || dugHere(u)) && u.state !== "broken" && u.state !== "fled"));   // gone to ground, or emplaced or dug in where it stands, and not running
const busyDigging = u => !!(u.digging || u.mining || u.clearing);   // digging in, or sappers laying or lifting mines: it does not shoot (as units.busy_digging)
const canDig = u => UD.commander.ground_with.includes(u.weapon) && !u.vehicle && !u.mounted && !isBattery(u) && !isAtGun(u) && !u.emplaced;   // a foot unit with a modern weapon (as units.can_dig)
function digAll(us){                               // end of the exchange: digging units still where they began, standing and out of contact dig on; after dig_in.exchanges they are dug in (as units._dig_all)
  const occ = occupancy(us), out = [];
  us.forEach((u, i) => {
    const g = u.digging;
    if (!g) return;
    if (g.at[0] !== u.pos[0] || g.at[1] !== u.pos[1] || ROUTED.has(u.state) || u.men <= 0 || inContact(us, occ, i)){ delete u.digging; return }
    const n = g.n + 1;
    if (n < UD.dig_in.exchanges){ u.digging = { at: [...g.at], n }; return }
    delete u.digging;
    u.dug = [...u.pos];
    out.push({ kind: "dug", unit: i });
  });
  return out;
}
const canSap = u => !!u.sappers && !u.vehicle && !u.mounted && !isBattery(u) && !isAtGun(u);   // sappers can lay or lift mines (as units.can_sap)
function aheadRow(field, u){                       // the row of hexes just ahead of its front row, on the map (as units.ahead_row)
  const rows = footprint(u), [cols, nrows] = fieldSize(field);
  return (rows[0] || []).map(h => step(h, u.facing)).filter(x => x[0] >= 0 && x[0] < cols && x[1] >= 0 && x[1] < nrows);
}
const knownMine = (m, side = null) => !m.hidden || !!m.found || (side !== null && m.side === side);   // a minefield hex a side knows of: marked, found, or laid by its sappers (as units.known_mine)
function sapperDone(field, u, task, w, occ){       // its mining or clearing finished: [log kind, hexes] laid (where no unit stands) or lifted in the row ahead (as units._sapper_done)
  const M = field.mines || (field.mines = {}), row = aheadRow(field, u);
  if (task === "mining"){
    const hexes = row.filter(x => !(hk(x) in M) && !(hk(x) in occ));
    for (const x of hexes) M[hk(x)] = { kind: w.kind, hidden: true, side: u.side };
    return ["laid", hexes];
  }
  const hexes = row.filter(x => hk(x) in M && knownMine(M[hk(x)], u.side));
  for (const x of hexes) delete M[hk(x)];
  return ["lifted", hexes];
}
const sapperTask = u => (u.mining && "mining") || (u.clearing && "clearing") || null;
function sappersAll(us, field){                    // end of the exchange: sappers still where and as they began, standing and out of contact work on (as units._sappers_all)
  if (!field){ for (const u of us){ delete u.mining; delete u.clearing } return [] }
  const occ = occupancy(us), out = [], S = UD.mines.sappers;
  us.forEach((u, i) => {
    const task = sapperTask(u);
    if (!task) return;
    const w = u[task];
    if (!canSap(u) || w.at[0] !== u.pos[0] || w.at[1] !== u.pos[1] || w.facing !== u.facing || ROUTED.has(u.state) || u.men <= 0 || inContact(us, occ, i)){ delete u[task]; return }
    const n = w.n + 1;
    if (n < S[task === "mining" ? "lay" : "clear"]){ u[task] = { ...w, at: [...w.at], n }; return }
    delete u[task];
    const [kind, hexes] = sapperDone(field, u, task, w, occ);
    out.push({ kind, unit: i, hexes: hexes.length, ...(task === "mining" ? { mine: w.kind } : {}) });
  });
  return out;
}
const groundCover = u => (low(u) ? UD.to_ground.cover : 0);                 // % off shots at a unit gone to ground (or emplaced)
function hasShields(u){                           // its guns have shields: always (gun_shields.weapons), or optional ones the GM marked shielded (as units.has_shields)
  const S = UD.gun_shields || {};
  return (S.weapons || []).includes(u.weapon) || (!!u.shielded && (S.optional || []).includes(u.weapon));
}
function shieldCover(u, t, h){                    // % off small-arms fire from h at unit u (its hex t): its guns' shields, from its front only
  const S = UD.gun_shields || {};
  if (!hasShields(u) || (h[0] === t[0] && h[1] === t[1])) return 0;
  return arc(u.facing, bearing(t, h)) === "front" ? S.cover : 0;
}
function hidesAt(field, h){                       // men in hex h hidden by its ground or a hex work that hides (a trench)
  if (groundAt(field, h).hides) return true;
  const it = field?.works?.hexes?.[`${h[0]},${h[1]}`];
  return !!it && !!FD.works?.hex_works?.[it.type]?.hides;
}
function seenShare(field, u, at, weapon = null){  // share of aimed shots at u that find a man: hidden.seen % (mg_seen % for a machine gun) if gone to ground, in a bunker or in hiding ground
  const H = UD.hidden;
  if (!H) return 1;
  if (!(low(u) || inBunker(field, u) || (at && hidesAt(field, at)))) return 1;
  return weapon && isMg(weapon) ? (H.mg_seen ?? H.seen) / 100 : H.seen / 100;
}
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
  if (!under || !isMg(shooterOf(us, v).weapon)) return;
  under[v.dfd] = true;
  if (v.behind !== undefined && v.behind !== null) under[v.behind] = true;
}
// a unit of `side` can see hex h to call fire on it: in sight in the weather, no woods between
const spotted = (units, field, side, h) => units.some(u => u.side === side && u.men > 0 && u.state !== "broken" && u.state !== "fled" && sees(field, u, h, sightHexes(field, h, seerOf(u))));
function sightHexes(field, h = null, seer = null){  // how far the weather and the light let a man (seer: his kit and night device) see hex h, in field hexes (null: as far as the map); a lit hex as by day, one that fired out to light.flash
  const cond = field?.weather?.cond, L = lightOf(field);
  let vis = cond && FD.weather ? thermalSight(FD.weather.conditions[cond], FD.weather.conditions[cond].visibility, seer) : null;
  if (vis === undefined) vis = null;
  let dark = L && !lit(field, h) ? darkSight(L, nightDevice(seer, field))[0] : null;
  if (dark !== null && flashing(field, h)) dark = Math.max(dark, FD.weather.light.flash);
  if (dark !== null && beaming(field, h) && seesBeam(seer, field)) dark = Math.max(dark, NV().beam);
  if (dark !== null) vis = vis === null ? dark : Math.min(vis, dark);
  return vis === null ? null : Math.floor(vis / UD.range_scale);
}
function sees(field, u, h, sight){                // any hex of u sees h: within sight, a clear sight past woods and buildings (clearSight), no smoke on the line
  return footprint(u).flat().some(x => {
    const dist = hdist(x, h);
    if (sight !== null && dist > sight) return false;
    return clearSight(field, x, h, dist) && (!smokedLine(field, x, h, dist) || seesSmoke(seerOf(u)));
  });
}
function within(h, radius){                       // hex h and every hex within radius of it
  const out = [[h[0], h[1]]];
  for (let n = 1; n <= radius; n++) for (let a = 0; a < 6; a++){ const corner = step(h, a, n); for (let j = 0; j < n; j++) out.push(step(corner, a + 2, j)) }
  return out;
}
function indirectAll(us, table, rng, acc, log, field, under){   // every fire mission due this exchange, in the support list's order
  const weapon = shellWeapon(table);
  if (!field || !weapon) return;
  (field.support || []).forEach((b, k) => { if (due(field, b)) fireMission({ us, table, weapon, rng, acc, log, field, under }, k, b) });
}
function due(field, b){                           // called, its wait over, rounds and tubes left, not moving, (aircraft) able to fly, its aim in reach of its place
  const m = b.mission;
  if (!m || (m.wait || 0) > 0 || (b.rounds || 0) <= 0 || servedTubes(b) <= 0 || b.displacing) return false;
  return grounded(field, b) === null && aimInReach(field, b);
}
function reachOf(b){                              // how far a placed battery reaches (its kind's range, field hexes), or null: no place, or a kind without a range
  const r = UD.indirect.kinds[b.kind].range;
  return r !== undefined && r !== null && b.place !== undefined && b.place !== null ? r : null;
}
const inReach = (b, h) => { const r = reachOf(b); return r === null || !h || hdist(b.place, h) <= r };   // can fire on hex h from where it stands
function aimInReach(field, b){                     // a mission's hex, or the enemy battery's place, in reach
  const m = b.mission;
  if (m.battery !== undefined && m.battery !== null){
    const sup = field.support || [], tg = m.battery >= 0 && m.battery < sup.length ? sup[m.battery] : null;
    const at = tg?.place;
    return at === undefined || at === null || inReach(b, at);
  }
  return inReach(b, m.hex);
}
function overrunAll(us, field){                    // a placed battery with an enemy unit within a hex of its place is overrun: tubes lost, mission over
  const log = [];
  (field?.support || []).forEach((b, k) => {
    if (b.place === undefined || b.place === null || (b.tubes || 0) <= 0) return;
    if (us.some(u => u.side !== b.side && !out_(u) && footprint(u).flat().some(h => hdist(h, b.place) <= 1))){
      Object.assign(b, { tubes: 0, mission: null, overrun: true });
      log.push({ kind: "overrun", sup: k, name: b.name, side: b.side });
    }
  });
  return log;
}
function grounded(field, b){                      // why aircraft cannot fly (a condition or a light), or null
  const K = UD.indirect.kinds[b.kind], A = UD.indirect.air || {};
  if (!K.air) return null;
  const wx = field?.weather || {};
  if ((A.grounded || []).includes(wx.cond)) return wx.cond;
  if (!K.by_night && (A.night || []).includes(wx.light || "day")) return wx.light;
  return null;
}
const crewOf = b => ("crew" in b ? b.crew : (b.tubes || 0) * (UD.indirect.kinds[b.kind].crew || 0));   // crewmen still serving
function servedTubes(b){                          // tubes it can fire: not knocked out, with `serve` men each
  const K = UD.indirect.kinds[b.kind];
  return K.serve === undefined ? b.tubes || 0 : Math.min(b.tubes || 0, Math.floor(crewOf(b) / K.serve));
}
function fireMission(ctx, k, b){                  // on an enemy battery or a hex: smoke laid or men struck; located; a creeping mission moves on (ctx: us, table, weapon, rng, acc, log, field, under)
  const { rng, log, field, us } = ctx;
  const K = UD.indirect.kinds[b.kind], m = b.mission;
  const air = !!K.air && m.hex !== undefined && m.hex !== null && !m.illum, fac = air && facSees(us, field, b, m.hex);
  if (air && !fac && friendsNear(us, b, m.hex)){ log.push({ kind: "airhold", sup: k, name: b.name, side: b.side, at: m.hex }); return }
  const shells = Math.min(servedTubes(b) * (m.illum ? 1 : K.rate), b.rounds);
  b.rounds -= shells;
  if (!K.direct && !K.air) b.located = true;       // tanks close behind the line and aircraft are never located
  if (m.illum){
    lightUp(field, m.hex, K.illum || 0, 1);
    log.push({ kind: "barrage", sup: k, name: b.name, side: b.side, shells, at: m.hex, bursts: [], smoke: false, illum: true });
  } else if (m.battery !== undefined && m.battery !== null) log.push(...counterFire(field, [k, b, shells, K], [ctx.table, ctx.weapon], rng));
  else onHex(ctx, [k, b, shells], [air, fac]);
  missionOn(b, m, field.size);
}
function onHex(ctx, fire, flight){                 // shells or an air attack on a hex (less scatter with a controller), then ground fire at the aircraft
  const { us, rng, log, field } = ctx, [k, b, shells] = fire, [air, fac] = flight, K = UD.indirect.kinds[b.kind], at = log.length;
  const marked = air && !fac && hk(b.mission.hex) in (field?.smoke || {}), scatter = fac || marked ? Math.floor(K.scatter / UD.indirect.air.fac.scatter) : K.scatter;
  const run = air ? b.mission.attack : null;
  if (run && run in (UD.indirect.air.runs || {})) runs(ctx, k, b, shells, scatter);
  else bombard(ctx, k, b, shells, scatter);
  if (fac) log[at].fac = true;
  if (marked) log[at].marked = true;
  if (air) log.push(...groundFire(us, [k, b], Math.ceil(shells / K.rate), rng));
}
function facSees(us, field, b, h){                 // a forward air controller (fac) of the aircraft's side, on its feet, sees hex h
  return us.some(u => u.fac && u.side === b.side && !out_(u) && sees(field, u, h, sightHexes(field, h, seerOf(u))));
}
function friendsNear(us, b, h){                    // a unit of the aircraft's side within indirect.air.fac.danger hexes of h
  const r = UD.indirect.air.fac.danger;
  return us.some(u => u.side === b.side && u.men > 0 && footprint(u).flat().some(x => hdist(x, h) <= r));
}
function runLine(at, dirn, mode){                 // an attack run's hexes: length hexes through at, along dirn
  const n = UD.indirect.air.runs[mode].length, out = [];
  for (let o = -Math.floor((n - 1) / 2); o <= Math.floor(n / 2); o++) out.push(step(at, dirn, o));
  return out;
}
function runs(ctx, k, b, passes, scatter){        // strafing runs or napalm strips: each pass's line scatters, then the men and vehicles on every line are struck (as units._runs)
  const { us, table, rng, acc, log } = ctx, m = b.mission, R = UD.indirect.air.runs[m.attack], lines = [];
  for (let p = 0; p < passes; p++){ const dirn = rng.randint(0, 5), far = rng.randint(0, scatter); lines.push(runLine(step(m.hex, dirn, far), m.dir ?? 0, m.attack)) }
  const hexes = lines.flat();
  log.push({ kind: "barrage", sup: k, name: b.name, side: b.side, shells: passes, at: m.hex, bursts: hexes, smoke: false, run: m.attack });
  const K = { ...UD.indirect.kinds[b.kind], knock: R.knock };
  us.forEach((u, i) => {
    if (u.vehicle){ shellVehicle(us, i, hexes, K, { table, rng, acc, log, src: [k, b] }); return }
    runStruck(ctx, i, [k, b, m.attack, hexes]);
  });
}
function runStruck(ctx, i, [k, b, mode, hexes]){  // unit i's men on the run's hexes: struck at the run's %, strafing cut as shellfire; napalm burns
  const { us, table, weapon, rng, acc, log, field, under } = ctx, u = us[i], R = UD.indirect.air.runs[mode];
  if (u.men <= 0 || u.state === "fled") return;
  const keys = hexes.map(hk), men = menByHex(u);
  let struck = 0, near = false;
  footprint(u).flat().forEach((h, n) => {
    const times = keys.filter(x => x === hk(h)).length;
    if (!times) return;
    near = true;
    const p = R.struck * (mode === "strafe" ? shellCut(field, h, low(u)) : 1);
    for (let s = 0; s < times * men[n]; s++) if (rng.randint(1, 100) <= p) struck++;
  });
  if (!near) return;
  under[i] = true;
  if (!struck) return;
  let t;
  if (mode === "napalm") t = burns(struck, R.dead, rng);
  else {
    const gun = (FD.tables[table]?.weapons || []).includes("machine_gun") ? "machine_gun" : weapon;
    t = blows({ table, weapon: gun, kit: null, quality: "regular" }, sideOfUnit(u, table), struck, UD.indirect.attack, 0, rng, { exposed: exposure(u, false, true), shift: -1000 });
  }
  t = takeHurt(u, t);
  acc.lost[i] += t.down; acc.dead[i] += t.dead;
  log.push(...logged({ kind: "shelled", sup: k, name: b.name, dfd: i, struck, run: mode }, t));
}
function flak(us, b, h){                           // % an aircraft attacking h is shot down: enemy machine guns, rockets and rifles within reach, times exposed, at most cap
  const G = UD.indirect.air.ground_fire, K = UD.indirect.kinds[b.kind];
  let chance = 0, aaFire = 0;
  for (const u of us){
    const w = u.weapon, aa = (G.aa_weapons || []).includes(w), reach = aa ? G.aa_reach : G.reach;
    if (u.side === b.side || out_(u) || u.vehicle || !footprint(u).flat().some(x => hdist(x, h) <= reach)) continue;
    if (aa) aaFire += G.aa * mgGuns(u);
    else if (isMg(w)) chance += G.mg * mgGuns(u);
    else if (G.rockets.includes(w)) chance += G.rocket;
    else if ("range" in FD.weapons[w] && !isGun(w) && !UD.line_of_fire.arcing.includes(w)) chance += G.rifles * u.men / 100;
  }
  return Math.min(G.aa_cap, Math.min(G.cap, chance * (K.exposed ?? 1)) + aaFire * (K.exposed ?? 1));
}
function groundFire(us, flight, attacking, rng){   // ground fire at the aircraft that attacked: each lost at flak %, taking its share of the attacks left
  const [k, b] = flight, chance = flak(us, b, b.mission.hex);
  if (chance <= 0 || b.tubes <= 0) return [];
  let hit = 0, downed = 0;
  for (let a = 0; a < attacking; a++) if (rng.randint(1, 100) <= chance) hit++;
  hit = Math.min(b.tubes, hit);
  if (!hit) return [];
  for (let a = 0; a < hit; a++) if (rng.randint(1, 100) <= UD.indirect.air.ground_fire.downed) downed++;
  const share = Math.floor(b.rounds / b.tubes);
  b.tubes -= hit;
  b.rounds = Math.max(0, b.rounds - share * hit);
  return [{ kind: "airloss", sup: k, name: b.name, side: b.side, lost: downed, damaged: hit - downed, left: b.tubes }];
}
function bombard(ctx, k, b, shells, scatter = null){   // shells on a hex: where each lands (0 to scatter hexes off), then smoke laid, or men struck and bunkers knocked
  const { rng, log, field } = ctx, K = UD.indirect.kinds[b.kind], m = b.mission, bursts = [], sc = scatter ?? K.scatter;
  for (let s = 0; s < shells; s++){ const dirn = rng.randint(0, 5), far = rng.randint(0, sc); bursts.push(step(m.hex, dirn, far)) }
  log.push({ kind: "barrage", sup: k, name: b.name, side: b.side, shells, at: m.hex, bursts, smoke: !!m.smoke });
  if (m.smoke) laySmoke(field, bursts);
  else { shellUnits(ctx, k, b, bursts); shellParties(ctx, bursts, K, { table: ctx.table, weapon: ctx.weapon, kit: null, quality: "regular" }); knockBunkers(field, k, b, bursts, rng, log) }
}
function lightUp(field, at, radius, late = 0){      // a flare or illumination lights the hexes within radius of at for light.lasts exchanges (+ late: fired after the shooting)
  if (radius > 0) (field.lit || (field.lit = [])).push({ at: [...at], radius, left: FD.weather.light.lasts + late });
}
function missionOn(b, m, size){                   // a single mission ends; a creeping one keeps its fire plan: `every` exchanges a line, `lines` lines, or off the map
  if (!m.repeat){ b.mission = null; return }
  const cr = m.creep;
  if (!cr) return;
  cr.on = (cr.on || 0) + 1;
  if (cr.on < (cr.every || 1)) return;
  cr.on = 0;
  if (cr.lines && (cr.line ?? 1) >= cr.lines){
    if (!cr.legs?.length){ b.mission = null; return }
    const [nxt, ...rest] = cr.legs;                // the fire plan's next leg: its own lift, direction and lines
    cr.legs = rest;
    Object.assign(cr, { step: nxt.step, dir: nxt.dir, lines: nxt.lines || 0, line: 0, done: 0 });
  }
  cr.line = (cr.line ?? 1) + 1;
  for (let s = 0; s < cr.step; s++){ m.hex = step(m.hex, cr.dir + (cr.done || 0) % 2); cr.done = (cr.done || 0) + 1 }
  if (size && !(m.hex[0] >= 0 && m.hex[0] < size[0] && m.hex[1] >= 0 && m.hex[1] < size[1])) b.mission = null;
}
function counterFire(field, fire, tw, rng){        // fire [k, battery, shells, kind]: shells among the guns knock out tubes and strike crewmen; near bursts strike crewmen
  const [k, b, shells, K] = fire, [table, weapon] = tw, CB = UD.indirect.counter_battery;
  const j = b.mission.battery, sup = field.support, tg = j >= 0 && j < sup.length ? sup[j] : null;
  if (!tg || tg.side === b.side){ b.mission = null; return [] }
  let hits = 0, struck = 0;
  for (let s = 0; s < shells; s++){
    const r = rng.randint(1, 100);
    if (r <= K.counter){ hits++; struck += CB.among }
    else if (r <= K.counter * CB.near) struck += CB.near_struck;
  }
  const knocked = Math.min(tg.tubes, hits), crew = crewOf(tg);
  struck = Math.min(struck, crew);
  const t = blows({ table, weapon, kit: null, quality: "regular" }, { table, weapon, kit: "none", quality: "regular" }, struck, UD.indirect.attack, 0, rng, { exposed: [], shift: -1000 });
  tg.tubes -= knocked;
  tg.crew = crew - t.down;
  tg.crew_down = (tg.crew_down || 0) + t.down;
  tg.crew_dead = (tg.crew_dead || 0) + t.dead;
  tg.hurt ??= {};
  takeHurt(tg, t);                                   // the crews' wounds, kept by kind for the after-battle reckoning (as units._counter_fire)
  if (servedTubes(tg) <= 0) tg.mission = null;
  return [{ kind: "counter", sup: k, name: b.name, side: b.side, shells, target: j, tname: tg.name, knocked, left: tg.tubes, struck, down: t.down, dead: t.dead, crew: tg.crew, served: servedTubes(tg) }];
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
function burns(struck, dead, rng){                 // men reached by flame: down with critical burns, dead % killed outright
  const t = newTally();
  Object.assign(t, { blows: struck, hits: struck, critical: struck, down: struck });
  for (let m = 0; m < struck; m++){
    if (rng.randint(1, 100) <= dead) t.dead++;
    else noteHurt(t, "critical", { lethal: "days", infection: "high" }, true);
  }
  return t;
}
function bunkerStruck(us, j, x, M, ctx){          // the men in a bunker's hex when it falls: struck by blast or by flame
  const b = us[j], { table, weapon, rng, acc } = ctx, hexes = footprint(b).flat();
  const k = hexes.findIndex(h => h[0] === x[0] && h[1] === x[1]), there = k >= 0 ? menByHex(b)[k] : 0;
  let struck = 0, t;
  for (let m = 0; m < there; m++) if (rng.randint(1, 100) <= M.struck) struck++;
  if (M.flame) t = burns(struck, UD.assault.flame_dead, rng);   // burns: out of the fight, no location roll; some killed outright
  else t = blows({ table, weapon, kit: null, quality: "regular" }, sideOfUnit(b, table), struck, UD.assault.attack, 0, rng, { exposed: exposure(b, false, true), shift: -1000 });
  t = takeHurt(b, t);
  acc.lost[j] += t.down; acc.dead[j] += t.dead;
  return { ...t, struck };
}
function shellUnits(ctx, k, b, bursts){           // the men struck in every unit by a battery's bursts, and their wounds
  const { us, table, weapon, rng, acc, log, field, under } = ctx;
  const I = UD.indirect, K = I.kinds[b.kind], att = { table, weapon, kit: null, quality: "regular" };
  us.forEach((u, i) => {
    if (u.vehicle){ shellVehicle(us, i, bursts, K, { table, rng, acc, log, src: [k, b] }); return }
    const struck = shellStruckUnit(field, u, bursts, K, rng);
    if (struck === null) return;
    under[i] = true;
    if (!struck) return;
    const t = takeHurt(u, blows(att, sideOfUnit(u, table), struck, I.attack, 0, rng, { exposed: exposure(u, false, true), shift: -1000 }));
    acc.lost[i] += t.down; acc.dead[i] += t.dead;
    log.push(...logged({ kind: "shelled", sup: k, name: b.name, dfd: i, struck }, t));
  });
}
function shellVehicle(us, i, bursts, kind, ctx){   // shells or bombs bursting in a vehicle's own hex knock it out at the kind's knock % x its armour's shell (ctx: table, rng, acc, log, src)
  const u = us[i], { table, rng, acc, log, src } = ctx;
  if (u.men <= 0 || u.state === "fled") return;
  const hexes = new Set(footprint(u).flat().map(hk)), direct = bursts.filter(at => hexes.has(hk(at))).length, p = (kind.knock || 0) * armourOf(u).shell;
  if (direct && p > 0){
    let kills = 0;
    for (let s = 0; s < direct; s++) if (rng.randint(1, 100) <= p) kills++;
    const k = knockOut(us, i, kills, table, rng, acc);
    if (k.knocked) log.push(...logged({ kind: "knocked_out", sup: src[0], name: src[1].name, dfd: i, knocked: k.knocked, crew: k.crew, struck: k.struck, ...ridersLine(k) }, k.tally));
  }
  log.push(...hullShelled(us, i, bursts, kind, table, rng, src));
}
function hullShelled(us, i, bursts, kind, table, rng, src){   // men riding on the hulls struck by the bursts as men in the open, wounded as by shellfire (as units._hull_shelled)
  const u = us[i];
  if (!exposed(u)) return [];
  const R = u.riders, hexes = footprint(u).flat(), base = Math.floor(R.men / hexes.length), extra = R.men % hexes.length;
  const men = hexes.map((h, j) => base + (j < extra ? 1 : 0));
  let struck = 0, near = false;
  for (const at of bursts) hexes.forEach((h, j) => {
    const dist = hdist(h, at);
    if (dist > kind.radius) return;
    near = true;
    for (let s = 0; s < men[j]; s++) if (rng.randint(1, 100) <= kind.struck[dist]) struck++;
  });
  struck = Math.min(struck, R.men);
  const weapon = shellWeapon(table);
  if (!near || !struck || !weapon) return [];
  const t = takeHurt(R, blows({ table, weapon, kit: null, quality: "regular" }, sideOfUnit(R, table), struck, UD.indirect.attack, 0, rng, { exposed: [], shift: -1000 }));
  const down = Math.min(t.down, R.men);
  Object.assign(R, { men: R.men - down, down: (R.down || 0) + down, dead: (R.dead || 0) + Math.min(t.dead, down) });
  return [{ kind: "hullshelled", sup: src[0], name: src[1].name, dfd: i, struck, down, dead: Math.min(t.dead, down) }];
}
function shellStruckUnit(field, u, bursts, kind, rng){   // men of u struck by these bursts, or null if none came near
  if (u.men <= 0 || u.state === "fled") return null;
  const hexes = footprint(u).flat(), men = menByHex(u), cuts = hexes.map(h => shellCut(field, h, low(u)));
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
    const target = quality(u.quality).nerve + (low(u) ? S.prone : 0), roll = rng.randint(1, 100);
    if (roll > target){ u.pinned = 2; log.push({ kind: "pinned", unit: i, roll, target }) }
  });
  return log;
}
function beaten(units, occ, field, i, best){      // {behind, beyond, bcover}: the first other unit in the beaten zone past the target
  const [dist, j, h, t] = best, line = ray(h, t, dist + UD.machine_guns.beaten.beyond).slice(dist);
  for (let k = 0; k < line.length; k++){
    if (groundAt(field, line[k]).stops_shot) break;
    const b = occ[hk(line[k])];
    if (k > 0 && b !== undefined && b !== i && b !== j && !units[b].vehicle) return { behind: b, beyond: k, bcover: (groundAt(field, line[k]).cover || 0) + groundCover(units[b]), bseen: seenShare(field, units[b], line[k], units[i].weapon) };
  }
  return { behind: null, beyond: 0, bcover: 0, bseen: 1 };
}
function beatenFire(us, table, rng, acc, log, v){ // the cone falling on into the unit behind the target
  const bh = us[v.behind], r = { ...v, dfd: v.behind, dist: v.dist + v.beyond, men: v.men * UD.machine_guns.beaten.share / 100 };
  const opts = { factor: form(bh).missile_factor * (100 - v.misfire) / 100 * (v.bseen ?? 1), exposed: exposure(bh, false, true), penalty: v.bcover + v.penalty, reach: v.reach };
  const hits = volley(sideOfUnit(us[v.att], table), sideOfUnit(bh, table), r.men, r.dist, rng, opts);
  if (!hits) return;
  const t = takeHurt(bh, hits);
  tallyLoss(acc, r, t);
  log.push(...logged({ kind: "beaten", ...r }, t));
}

// ---------- the field: ground, works and weather (as gravewounds/units.py) ----------
// field: {ground: {hex key: kind}, works: {edges, hexes}, weather: {cond, wind, ground} or null, size: [cols, rows]}
const fieldSize = field => field?.size || [UD.map.cols, UD.map.rows];
// The ground never changes during a battle (only the GM's painting in setup, which calls forgetGround), so what stands on
// each hex and what a sight line between two hexes crosses are worked out once and remembered, keyed by the field's ground
const GROUND_MEMO = new WeakMap();                // field ground -> {at: [column][row] ground spec, lines: Map sightKey -> packed sight line}
const NO_GROUND = {};
function groundMemo(field){
  const g = field?.ground || NO_GROUND;
  let m = GROUND_MEMO.get(g);
  if (!m){ m = { at: [], lines: new Map() }; GROUND_MEMO.set(g, m) }
  return m;
}
const forgetGround = field => { GROUND_MEMO.delete(field?.ground || NO_GROUND) };   // the GM painted the ground: work it out afresh
function groundAt(field, h){                      // the ground kind's spec at hex h (open if unpainted)
  const col = groundMemo(field).at, c = col[h[0]] || (col[h[0]] = []);
  let g = c[h[1]];
  if (g === undefined){ g = UD.ground[field?.ground?.[hk(h)] || "open"]; c[h[1]] = g }
  return g;
}
const sightKey = (h, t) => ((h[0] + 1024) * 4096 + h[1] + 1024) * 16777216 + (t[0] + 1024) * 4096 + t[1] + 1024;   // one number for a pair of hexes (columns and rows -1024 to 3071)
function sightLine(field, h, t, dist){            // the ground's part of a sight line from h to t (dist apart), worked out once, packed in a number: dead ground between (crestOn) 1, a clear sight to aim (sightOn) 2, the hexes of light cover between (thinOn) times 4 (as units._sight_line)
  const lines = groundMemo(field).lines, key = sightKey(h, t);
  let s = lines.get(key);
  if (s === undefined){
    const line = ray(h, t, dist);
    s = (crestOn(field, h, t, line) ? 1 : 0) + (sightOn(field, h, t, line) ? 2 : 0) + 4 * thinOn(field, h, line);
    lines.set(key, s);
  }
  return s;
}
const groundKey = (field, h) => field?.ground?.[hk(h)] || "open";   // the ground kind painted on hex h
function across(field, u, h, x, reach){           // [blocked: only reach 2 over it, penalty %, stakes: no charge for horses]
  if (!field) return [false, 0, false];
  const [cols, rows] = fieldSize(field), m = meleeAcross(field.works, h, x, reach, cols, rows);
  let pen = m.penalty;
  pen += Math.max(0, heightAt(field, x) - heightAt(field, h));
  const it = hexItem(field.works, x), stk = !!(u.mounted && it && specOf("hex", it).no_horse);
  return [m.blocked, pen, stk];
}
const upOf = field => field?.up || "N";          // the compass point at the top of the field map
const SMOKED = { blocked: "Smoke: no one can see to shoot through it.", penalty: 0, misfire: 0, reach: 0 };
const SCREENED = { blocked: "Woods, buildings or thick scrub between: no one can see to aim through them.", penalty: 0, misfire: 0, reach: 0 };
const CRESTED = { blocked: "Higher ground between: dead ground, no one can see over it to shoot.", penalty: 0, misfire: 0, reach: 0 };
const clearSight = (field, h, t, dist) => !field?.ground || (sightLine(field, h, t, dist) & 2) > 0;   // a man at h sees t to aim (sightOn)
const overCrest = (field, h, t, dist) => !!field?.ground && (sightLine(field, h, t, dist) & 1) > 0;   // dead ground between (crestOn)
const thinned = (field, h, t, dist) => (field?.ground ? sightLine(field, h, t, dist) >> 2 : 0);   // hexes of light cover between (thinOn)
function smokedLine(field, h, t, dist){            // smoke over any hex of the line from h to t (ends too): a smoke hex i hexes from h is on it only as its step i (as units.smoked_line)
  for (const k in field?.smoke || {}){
    const x = k.split(",").map(Number), i = hdist(h, x);
    if (i > dist || hdist(x, t) !== dist - i) continue;
    const y = rayAt(h, t, i);
    if (y[0] === x[0] && y[1] === x[1]) return true;
  }
  return false;
}
function sightOn(field, h, t, line){              // a man at h sees t to aim: no ground higher than both ends between (crestOn: dead ground), nothing that screens (woods, buildings) between past see_into hexes at either end, and no more than thin.blind_past hexes of light cover
  if (!field?.ground) return true;
  const k = UD.line_of_fire.see_into ?? 1, up = heightAt(field, h);
  if (crestOn(field, h, t, line)) return false;
  if (line.slice(1 + k, line.length - 1 - k).some(y => groundAt(field, y).screen && heightAt(field, y) >= up)) return false;
  return thinOn(field, h, line) <= UD.line_of_fire.thin.blind_past;
}
function crestOn(field, h, t, line){              // dead ground: open ground (a slope or high ground; tall buildings screen as buildings) higher than both h and t on the line between, not within line_of_fire.crest_clear hexes of either end (a man just behind a crest sees over it)
  if (!field?.ground) return false;
  const k = UD.line_of_fire.crest_clear ?? 1, rise = y => (groundAt(field, y).screen ? 0 : heightAt(field, y));
  const top = Math.max(heightAt(field, h), heightAt(field, t));
  return line.slice(1 + k, line.length - 1 - k).some(y => rise(y) > top);
}
function thinOn(field, h, line){                  // hexes of light cover (scrub, orchards) on the line, not the ends, as high as the man at h stands
  if (!field?.ground) return 0;
  const up = heightAt(field, h);
  return line.slice(1, -1).filter(y => groundAt(field, y).light && heightAt(field, y) >= up).length;
}
function shotWeather(field, weapon, dist, h = null, t = null, seer = null){   // the weather on a shot from h to t; smoke on the line blocks it; seer: {kit, blind} in the dark
  if (h && t && smokedLine(field, h, t, dist) && !seesSmoke(seer)) return { ...SMOKED };
  if (h && t && !seer?.blind && overCrest(field, h, t, dist)) return { ...CRESTED };
  if (h && t && !seer?.blind && !clearSight(field, h, t, dist)) return { ...SCREENED };
  if (isGun(weapon)) return gunWeather(field, dist, h, t, seer);
  const cond = field?.weather ? FD.weather?.conditions?.[field.weather.cond] : null, far = dist * UD.range_scale;
  const seen = seer?.blind || (cond?.thermal && seesSmoke(seer) && far <= cond.thermal) ? 0 : far;   // blind down a fixed line, or a thermal sight within its reach in a sandstorm: the weather's sight does not count
  const out = inTheCold(field, weapon, inTheDark(field, dist, t, weatherAttack(field?.weather || null, weapon, seen, h, t, upOf(field)), seer));
  const n = h && t && !out.blocked ? thinned(field, h, t, dist) : 0;   // light cover between: aimed fire thinned
  return n ? { ...out, penalty: out.penalty + n * UD.line_of_fire.thin.per } : out;
}
const coldOf = field => FD.weather?.cold?.levels?.[field?.weather?.cold || ""] || null;   // the field's cold level, or null
function inTheCold(field, weapon, out){            // automatic weapons jam more in hard cold
  const L = coldOf(field);
  if (L && !out.blocked && FD.weather.cold.jams.includes(weapon)) out.misfire = Math.min(100, out.misfire + L.jam);
  return out;
}
function lightOf(field){                          // the field's light (weather.light), or null by day
  const L = FD.weather?.light?.levels?.[field?.weather?.light || "day"];
  return L && ((L.sight !== null && L.sight !== undefined) || L.aim) ? L : null;
}
const lit = (field, h) => !!h && (field?.lit || []).some(x => hdist(h, x.at) <= x.radius);   // a flare or illumination lights hex h
function inTheDark(field, dist, t, out, seer = null){   // no aiming beyond the light's sight at an unlit hex (night vision further, flashes seen further), its aim % off; blind down a fixed line
  const L = lightOf(field);
  if (out.blocked || !L || lit(field, t)) return out;
  if (seer?.blind){ out.penalty += FD.weather.light.fixed_line.aim; out.blind = true; return out }
  const [sight, aim] = darkSight(L, nightDevice(seer, field)), far = dist * UD.range_scale;
  if (sight !== null && far > sight){
    if (flashing(field, t) && far <= FD.weather.light.flash) out.flash = true;
    else if (beaming(field, t) && seesBeam(seer, field) && far <= NV().beam) out.beam = true;
    else { out.blocked = `${L.name}: no one can be seen to aim at beyond ${Math.floor(sight / UD.range_scale)} hexes.`; return out }
  }
  out.penalty += aim;
  return out;
}
const NV = () => FD.weather?.light?.night_vision || {};
const fireControlOf = (o, table) => (UD.vehicles.kinds[o.vehicle]?.fc ? o.fc || UD.vehicles.fire_control.by_war[FD.tables[table]?.battle] || null : null);   // a tank's fire control: the battlefield's, else its war's (as units.fire_control_of)
const vehicleDevice = table => NV().vehicles?.[FD.tables[table]?.battle] ?? null;   // the night device a vehicle unit carries by default in this table's war (as units.vehicle_device)
function nightDevice(seer, field = null){          // the night-vision device a shooter or watcher ({kit, nv, at}) carries: the unit's own ("none": none), else his kit's, else null; null if it washes out where he stands in a flare's light (with field)
  let dev = null;
  if (seer?.nv) dev = seer.nv === "none" ? null : seer.nv;
  else if ((NV().kits || []).includes(seer?.kit)) dev = NV().kit_device;
  return dev && field && NV().devices?.[dev]?.washes && lit(field, seer?.at) ? null : dev;
}
const seerOf = (u, k = {}) => ({ kit: u.kit, nv: u.nv, at: u.pos, ...k });   // a unit as a shooter or watcher in the dark (at: where it stands, for a flare's washout)
const beaming = (field, t) => !!t && (field?.beams || []).some(x => x[0] === t[0] && x[1] === t[1]);   // a hex a unit fired from by its infrared beam last exchange
const seesBeam = (seer, field) => !!NV().devices?.[nightDevice(seer, field) || ""]?.sees_beam;   // the watcher's device picks up an infrared beam
function darkSight(L, device){                      // [sight in battle hexes or null, aim % off] in light L for a man with this device (null: his eyes)
  const dev = NV().devices?.[device || ""], sight = L.sight ?? null;
  if (!dev) return [sight, L.aim];
  return [sight === null ? null : Math.max(sight, dev.sight), Math.min(L.aim, dev.aim)];
}
const seesSmoke = seer => !!NV().devices?.[nightDevice(seer) || ""]?.smoke;   // a thermal sight sees through smoke
const flashing = (field, t) => !!t && (field?.flashes || []).some(x => x[0] === t[0] && x[1] === t[1]);   // a hex a unit fired from in the dark last exchange
const FLASHING = new Set(["volley", "hero", "antiarmour", "tankfire", "cannon"]);
function beams(us, log, field){                    // after the shooting, in any dark: the hexes of every unit that fired by its infrared searchlight (not washed out), seen by enemy infrared and intensifier devices through the next exchange (as units._beams)
  if (!field) return;
  const sight = lightOf(field)?.sight ?? null;
  if (sight === null){ delete field.beams; return }
  const fired = [...new Set(log.filter(x => FLASHING.has(x.kind) && x.att !== undefined && x.att !== null).map(x => x.att))]
    .filter(i => NV().devices?.[nightDevice(seerOf(us[i]), field) || ""]?.beam);
  const keys = new Set(), hexes = [];
  for (const i of fired) for (const h of footprint(us[i]).flat()){ const k = hk(h); if (!keys.has(k)){ keys.add(k); hexes.push([h[0], h[1]]) } }
  hexes.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (hexes.length) field.beams = hexes; else delete field.beams;
}
function flashes(us, log, field){                  // after the shooting, in poor light: the hexes of every unit that fired, seen by their flashes through the next exchange
  if (!field) return;
  const sight = lightOf(field)?.sight ?? null;
  if (sight === null || sight >= FD.weather.light.flash){ delete field.flashes; return }
  const fired = [...new Set(log.filter(x => FLASHING.has(x.kind) && x.att !== undefined && x.att !== null).map(x => x.att))];
  const keys = new Set(), hexes = [];
  for (const i of fired) for (const h of footprint(us[i]).flat()){ const k = hk(h); if (!keys.has(k)){ keys.add(k); hexes.push([h[0], h[1]]) } }
  hexes.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (hexes.length) field.flashes = hexes; else delete field.flashes;
}
function nightDrift(units, i, size, field, rng){   // a unit that moved in the dark may lose its direction, turning a point off and straying a hex along it: {lost, unit, strayed} (as units.night_drift)
  const u = units[i], L = lightOf(field);
  if (!L?.lost) return { lost: false, unit: u, strayed: false };
  const chance = Math.max(0, Math.min(100, L.lost + Math.floor((60 - quality(u.quality).nerve) / 2)));
  if (rng.randint(1, 100) > chance) return { lost: false, unit: u, strayed: false };
  const left = rng.randint(1, 100) % 2 === 0;
  const turned = { ...u, facing: mod6(u.facing + (left ? 1 : -1)), lost: FD.weather.light.lost_for };
  if (!fits(units, i, turned, size, field)) return { lost: true, unit: { ...turned, facing: u.facing }, strayed: false };
  const gone = stray(units, i, turned, [left, size, field]);
  return { lost: true, unit: gone || turned, strayed: !!gone };
}
function stray(units, i, u, [left, size, field]){  // a lost unit goes on a hex along its wrong facing (the front hexside it turned toward), unless that is off the map, on other units or ground it cannot stand on, or touching the enemy: the unit there, or null (as units._stray)
  const moved = { ...u, pos: step(u.pos, u.facing + (left ? 1 : 0)) };
  if (!fits(units, i, moved, size, field)) return null;
  const after = units.map((x, k) => (k === i ? moved : x));
  return inContact(after, occupancy(after), i) ? null : moved;
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
function heightEdge(field, weapon, h, t){         // [% to hit, % longer range bands]: down from higher ground +, up at it -, by each 10 of height between; none for guns
  if (!field || isGun(weapon)) return [0, 0];
  const diff = heightAt(field, h) - heightAt(field, t), H = UD.high_ground;
  if (diff > 0) return [Math.floor(H.shoot * diff / 10), Math.floor(H.reach * diff / 10)];
  return diff < 0 ? [-Math.floor(H.shoot * -diff / 10), 0] : [0, 0];
}
const heightAt = (field, h) => (field ? groundAt(field, h).height || 0 : 0);   // how high the ground at h stands (a slope 5, high ground or tall buildings 10)
function sweepCost(field, before, after){          // the ground a turning unit's ends sweep over: the worst extra going of hexes it comes to stand on
  if (!field) return 0;
  const old = new Set(footprint(before).flat().map(hk));
  const going = x => (after.vehicle ? UD.vehicles.ground[groundKey(field, x)] ?? 1 : groundAt(field, x).move);
  return Math.max(0, ...footprint(after).flat().filter(x => !old.has(hk(x))).map(x => going(x) - 1));
}
function holdsWorks(field, h, t){                 // unit t holds works against an attack from h: dug in or emplaced, cover from the works toward h in any of its hexes, or in ground that hides men (as units.holds_works)
  if (dugHere(t) || t.emplaced) return true;
  if (!field) return false;
  const [cols, rows] = fieldSize(field);
  return footprint(t).some(row => row.some(x => groundAt(field, x).hides || missileCover(field.works, h, x, cols, rows).cover > 0));
}
function coverAt(field, h, t){                    // % off shots from h at t: the best of the works' and the ground's
  if (!field) return 0;
  const [cols, rows] = fieldSize(field);
  return Math.max(missileCover(field.works, h, t, cols, rows).cover, groundAt(field, t).cover || 0);
}
const fatiguePenalty = u => (u.fatigue ? WXD.fatigue.levels[u.fatigue].penalty : 0);
const sideOfUnit = (u, table) => { const f = fatiguePenalty(u); return { table, weapon: u.weapon, kit: u.kit, quality: u.quality, ...(f ? { attack: -f, defence: -f } : {}) } };
function toilGoing(us, field){                    // in deep mud or snow, every hex a unit (not a vehicle) went since the last exchange is a toil (as units._toil_going)
  if (deepGoing(field?.weather?.ground) <= 0) return;
  for (const u of us) if (u.toil_from && !u.vehicle) tire(u, hdist(u.toil_from, u.pos));
}
function toilFought(us, fought){                  // a toil for each unit that fought hand to hand; its next going counted from here (as units._toil_fought)
  for (const k of fought) tire(us[k], 1);
  for (const u of us) u.toil_from = [...u.pos];
}
function tire(u, n){                              // (as units.tire) n more toil: a fatigue step worse each time its kit's load is reached, to worst at most
  const T = FD.toil, need = T.blows[T.load[u.kit] || "light"];
  let toil = (u.toil || 0) + n, f = u.fatigue || 0;
  while (toil >= need){ toil -= need; if (f < T.worst) f++ }
  u.toil = toil; if (f) u.fatigue = f;
}
const meleeSide = (u, table) => ({ ...sideOfUnit(u, table), weapon: meleeWeapon(u) });   // hand to hand: a battery's crews fight with their own weapon
function takeHurt(u, t){                         // the wounded go onto the unit struck; the tally (for the log) keeps the rest
  const { hurt, ...rest } = t;
  for (const [k, n] of Object.entries(hurt)) u.hurt[k] = (u.hurt[k] || 0) + n;
  return rest;
}
function tallyLoss(acc, s, t){ acc.lost[s.dfd] += t.down; acc.dead[s.dfd] += t.dead; acc.dealt[s.att] += t.down }
const copyUnit = u => ({ ...u, hurt: { ...u.hurt }, heroes: (u.heroes || []).map(h => ({ ...h, wounds: [...(h.wounds || [])], ...(h.held ? { held: { ...h.held } } : {}), ...(h.going ? { going: { ...h.going } } : {}) })) });
function logged(line, t){                         // a log line for a tally, then one for each blow that fell on a hero
  const { heroes, ...rest } = t;
  return [{ ...line, ...rest }, ...(heroes || []).map(h => ({ kind: "herohit", unit: line.dfd, ...h }))];
}
function pikeFront(u){                            // steady, in a pike formation, with a pike: a front horse cannot charge home on
  const P = UD.melee.pikes;
  return u.state === "steady" && P.formations.includes(u.formation) && P.weapons.includes(meleeWeapon(u)) && !u.mounted;
}
function strikeAll(us, table, rng, acc, log, field, thinned = null){   // thinned: men each unit lost to canister as it came in; its striking men cut in that share
  const struck = new Set(), dueled = new Set();
  for (let s of strikes(us, field)){
    const cut = (thinned || [])[s.att] || 0;
    if (cut && !s.rout){ const men = us[s.att].men, kept = Math.floor(s.men * Math.max(0, men - cut) / Math.max(1, men)); s = { ...s, men: kept, thinned: s.men - kept } }
    const a = us[s.att], b = us[s.dfd];
    const charge = !!a.charged && !!a.mounted && !s.stakes && !(s.situation === "front" && pikeFront(b));   // no charge home onto a front of pikes
    const vsHorse = b.mounted && pikeFront(a) ? UD.melee.pikes.attack : 0;
    const opts = { situation: s.situation, charge, shaken: a.state === "shaken", rout: s.rout, exposed: exposure(b, s.rout), penalty: (s.penalty || 0) - vsHorse };
    const t = takeHurt(b, melee(meleeSide(a, table), meleeSide(b, table), s.men, rng, opts));
    tallyLoss(acc, s, t);
    acc.flanked[s.dfd] = acc.flanked[s.dfd] || s.situation === "flank" || s.situation === "rear";
    log.push(...logged({ kind: s.rout ? "rout" : "melee", ...s }, t));
    if (!s.rout && acc.fought){ acc.fought.add(s.att); acc.fought.add(s.dfd) }
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
    if (x.state !== "up" || !heroStrikes(x) || y.state !== "up") continue;
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
function heroShots(us, v, { table, rng, acc, log, field, exposed, mf }){   // the shooting unit's heroes with missile weapons fire with it
  const b = us[v.dfd];
  for (const hero of actingOf(us[v.att], ["ranged"])){
    const wx = shotWeather(field, hero.weapon, v.dist, v.from, v.to, { kit: hero.kit, blind: !!v.blind });
    if (wx.blocked) continue;
    const [up, longer] = heightEdge(field, hero.weapon, v.from, v.to);
    if (!fieldRange(hero.weapon, v.dist, wx.reach + longer)) continue;
    const hopts = { factor: mf * (100 - wx.misfire) / 100 * v.seen, exposed, penalty: v.cover + wx.penalty - up + v.over, reach: wx.reach + longer };
    const t = takeHurt(b, volley(heroSide(us[v.att], hero, table), sideOfUnit(b, table), UD.heroes.tempo, v.dist, rng, hopts));
    tallyLoss(acc, v, t);
    log.push(...logged({ kind: "hero", hero: hero.id, name: hero.name, att: v.att, dfd: v.dfd, dist: v.dist }, t));
  }
}
// ---------- ammunition (as gravewounds/units.py) ----------
function ammoFull(u){                              // a full load in exchanges of fire (ammunition.loads / (missile.rate * burn), rounded, at least 1); null if it does not count: no load, a vehicle, a battery or anti-tank guns
  const A = UD.ammunition || {}, load = (A.loads || {})[u.weapon];
  if (!load || u.vehicle || !("range" in FD.weapons[u.weapon]) || isBattery(u) || isAtGun(u)) return null;
  const S = UD.missile;
  return Math.max(1, Math.floor(load / ((S.rate[u.weapon] ?? S.default_rate) * A.burn) + 0.5));
}
function fireLeft(u){                            // exchanges of fire left (u.ammo, else a full load), or null
  const full = ammoFull(u);
  return full === null ? null : Math.min(full, u.ammo ?? full);
}
function ammoState(u){                             // full, low (at or under ammunition.low of a full load) or out; null if it does not count
  const full = ammoFull(u), left = fireLeft(u);
  if (full === null) return null;
  if (left <= 0) return "out";
  return left <= full * UD.ammunition.low ? "low" : "full";
}
function spend(us, v){                             // a volley fired: its shooters (the riders for a riders' volley) use an exchange of fire
  const u = us[v.att], who = v.riders ? u.riders : u, left = fireLeft(who);
  if (left !== null) who.ammo = Math.max(0, left - 1);
}
const EDGE_BEHIND_OF = ["W", "S", "E", "E", "N", "W"];   // the map edge behind units facing 0-5
function supplyEdge(us, side){                     // the map edge its supplies come from: behind the way most of the side's standing men face, or null
  const n = [0, 0, 0, 0, 0, 0];
  for (const u of us) if (u.side === side && u.men > 0 && u.state !== "fled") n[mod6(u.facing)] += u.men;
  const top = Math.max(...n);
  return top === 0 ? null : EDGE_BEHIND_OF[n.indexOf(top)];
}
function edgeGap(edge, h, [cols, rows]){           // hexes between h and map edge N, S, E or W
  return { N: h[1], S: rows - 1 - h[1], W: h[0], E: cols - 1 - h[0] }[edge];
}
function supplyNear(us, i, field){                 // what it can draw ammunition from within ammunition.reach: edge, vehicle or dump; null
  const A = UD.ammunition, u = us[i], reach = A.reach, hexes = footprint(u).flat(), edge = supplyEdge(us, u.side);
  if (edge !== null && Math.min(...hexes.map(h => edgeGap(edge, h, fieldSize(field)))) < reach) return "edge";
  for (let j = 0; j < us.length; j++){
    const e = us[j];
    if (j !== i && e.side === u.side && e.state === "steady" && e.men > 0 && A.vehicles.includes(e.vehicle)
        && Math.min(...hexes.flatMap(h => footprint(e).flat().map(x => hdist(h, x)))) <= reach) return "vehicle";
  }
  if ((field?.dumps || []).some(m => m.side === u.side && Math.min(...hexes.map(h => hdist(h, m.at))) <= reach)) return "dump";
  return null;
}
function airDrops(field, rng){                     // end of the exchange: each supply drop called lands as a dump, a d6 direction and 0 to air_drop.scatter hexes off (kept on the map)
  const drops = field?.drops || [], out = [], [cols, rows] = fieldSize(field);
  if (field) delete field.drops;
  for (const m of drops){
    const dirn = rng.randint(1, 6) - 1, n = rng.randint(0, UD.ammunition.air_drop.scatter), h = step(m.at, dirn, n);
    const at = [Math.min(Math.max(h[0], 0), cols - 1), Math.min(Math.max(h[1], 0), rows - 1)];
    (field.dumps || (field.dumps = [])).push({ at, side: m.side });
    out.push({ kind: "drop", side: m.side, aim: [...m.at], at });
  }
  return out;
}
function shootAll(us, table, rng, acc, log, field, under = null){
  for (const v of volleys(us, field)){
    markMg(us, v, under);
    spend(us, v);
    const b = us[v.dfd], exposed = exposure(b, false, true), mf = form(b).missile_factor;
    if (b.vehicle){ armourVolley(us, table, rng, acc, log, v, { factor: mf * (100 - v.misfire) / 100 * v.seen, penalty: v.cover + v.penalty + v.over, reach: v.reach }); continue }
    const t = takeHurt(b, volley(sideOfUnit(shooterOf(us, v), table), sideOfUnit(b, table), v.men, v.dist, rng, { factor: mf * (100 - v.misfire) / 100 * v.seen, exposed, penalty: v.cover + v.penalty + v.over, reach: v.reach }));
    tallyLoss(acc, v, t);
    log.push(...logged({ kind: "volley", ...v }, t));
    if (v.behind !== undefined && v.behind !== null) beatenFire(us, table, rng, acc, log, v);
    if (!v.riders) heroShots(us, v, { table, rng, acc, log, field, exposed, mf });
  }
  for (const c of cannonades(us, field)) fireBattery(us, table, rng, acc, log, c);
  vehicleGuns(us, table, rng, acc, log, field, under);
}
function armourVolley(us, table, rng, acc, log, v, opts){   // anti-armour shots that hit knock a vehicle out at its armour's rpg %
  const att = sideOfUnit(shooterOf(us, v), table), band = fieldRange(att.weapon, v.dist, opts.reach || 0);
  if (!band) return;
  const A = shotAtVehicle(att.weapon);
  const n = countBlows(v.men * A.rate * opts.factor, rng), atk = attackOf(att) - band.penalty - opts.penalty;
  let hits = 0, kills = 0;
  for (let s = 0; s < n; s++) if (rng.randint(1, 100) <= atk) hits++;
  const p = A.row in UD.vehicles.armour[vehicleKind(us[v.dfd]).armour] ? killChance(us[v.dfd], A.row, v.from, v.to) : 0;
  for (let s = 0; s < hits; s++) if (p && rng.randint(1, 100) <= p) kills++;
  const k = knockOut(us, v.dfd, kills, table, rng, acc), hm = harm(us[v.dfd], A.row === "small" ? 0 : hits - k.knocked, acc.lost[v.dfd], rng);
  const shot = A.row === "small" ? ridersShot(us[v.dfd], hits - k.knocked, att, table, rng) : {};
  acc.dealt[v.att] += k.crew;
  log.push(...logged({ kind: "antiarmour", ...v, shots: n, hit: hits, knocked: k.knocked, crew: k.crew, struck: k.struck, kill: p, ...harmLine(hm), ...ridersLine(k), ...shot }, k.tally));
}
function knockOut(us, i, n, table, rng, acc){      // up to n vehicles out: their crews out of the fight, each struck at crew_struck % -> {knocked, crew, struck, tally}
  const u = us[i], K = vehicleKind(u), V = UD.vehicles;
  n = Math.min(n, vehiclesLeft(u, acc.lost[i]));
  if (n <= 0) return { knocked: 0, crew: 0, struck: 0, tally: newTally() };
  const crew = Math.min(n * K.crew, u.men - acc.lost[i]);
  let struck = 0;
  for (let s = 0; s < crew; s++) if (rng.randint(1, 100) <= V.crew_struck) struck++;
  const weapon = shellWeapon(table);
  let t = struck && weapon ? blows({ table, weapon, kit: null, quality: "regular" }, sideOfUnit(u, table), struck, UD.indirect.attack, 0, rng, { exposed: [], shift: -1000 }) : newTally();
  t = takeHurt(u, t);
  const left = vehiclesLeft(u, acc.lost[i]);
  acc.lost[i] += crew;
  acc.dead[i] += Math.min(t.dead, crew);
  return { knocked: n, crew, struck, tally: t, ...ridersHit(u, n, left, table, rng) };
}
function ridersShot(u, n, att, table, rng){         // small-arms hits on a soft carrier that knocked none out: each strikes a rider, wounded by the shooter's weapon (as units._riders_shot)
  const R = u.riders;
  if (!R || R.men <= 0 || n <= 0) return {};
  const struck = Math.min(n, R.men);
  const t = takeHurt(R, blows({ table, weapon: att.weapon, kit: null, quality: "regular" }, sideOfUnit(R, table), struck, UD.indirect.attack, 0, rng, { exposed: [], shift: -1000 }));
  const down = Math.min(t.down, R.men);
  Object.assign(R, { men: R.men - down, down: (R.down || 0) + down, dead: (R.dead || 0) + Math.min(t.dead, down) });
  return { rshot: struck, rshotdown: down, rshotdead: Math.min(t.dead, down) };
}
function ridersHit(u, n, left, table, rng){        // the riders in n of a carrier unit's `left` vehicles, knocked out: each struck at riders_struck %, wounded as by shellfire
  const R = u.riders;
  if (!R || R.men <= 0 || left <= 0) return {};
  const share = Math.min(R.men, Math.ceil(R.men * n / left));
  let struck = 0;
  for (let s = 0; s < share; s++) if (rng.randint(1, 100) <= UD.vehicles.riders_struck) struck++;
  const weapon = shellWeapon(table);
  if (!struck || !weapon) return { riders_struck: struck };
  const t = takeHurt(R, blows({ table, weapon, kit: null, quality: "regular" }, sideOfUnit(R, table), struck, UD.indirect.attack, 0, rng, { exposed: [], shift: -1000 }));
  const down = Math.min(t.down, R.men);
  Object.assign(R, { men: R.men - down, down: (R.down || 0) + down, dead: (R.dead || 0) + Math.min(t.dead, down) });
  return { riders_struck: struck, riders_down: down, riders_dead: Math.min(t.dead, down) };
}
function vehicleGuns(us, table, rng, acc, log, field, under){   // each vehicle unit's main gun: at vehicles, hits by range and knocks by armour; at men, bursts as the indirect kind `he`
  us.forEach((u, i) => {
    const G = gunOf(u);
    if (!G || out_(u)) return;
    const best = gunTarget(us, i, field, G);
    if (!best) return;
    const [dist, j, h, t] = best;
    let rounds = gunsFiring(u) * G.rate;
    if (isAtGun(u)){ rounds = Math.min(rounds, atRounds(u)); u.spent = (u.spent || 0) + rounds }
    if (rounds <= 0) return;
    if (us[j].vehicle){ gunAtVehicle(us, [i, j, dist, rounds, h, t], G, { table, rng, acc, log }); return }
    log.push({ kind: "tankfire", att: i, dfd: j, dist, rounds, at: t });
    const weapon = shellWeapon(table);
    if (weapon && field) shellUnits({ us, table, weapon, rng, acc, log, field, under: under || us.map(() => false) }, null, { kind: G.he, name: u.name ?? null }, Array.from({ length: rounds }, () => [...t]));
  });
}
function gunOf(u){                                // a unit's main gun: a vehicle kind's, or an anti-tank gun unit's (none while it resupplies)
  if (isAtGun(u)) return u.resupplying || u.unhooked ? null : UD.anti_tank_guns.gun;
  const K = vehicleKind(u), F = u.fc ? UD.vehicles.fire_control[u.fc] : null;
  if (!K?.gun) return null;
  return F ? { ...K.gun, range: F.range, hit: F.hit } : K.gun;   // a tank's gun hits and reaches by its fire control
}
const atRounds = u => Math.max(0, Math.ceil((u.start ?? u.men) / UD.anti_tank_guns.crew) * UD.anti_tank_guns.rounds - (u.spent || 0));   // an anti-tank gun unit's rounds left
const gunsFiring = u => (isAtGun(u) ? atGuns(u) : Math.max(0, vehiclesLeft(u) - (u.gunless || 0)));   // its vehicles whose guns work, or its anti-tank guns served
function gunAtVehicle(us, shot, G, ctx){          // a main gun's rounds at a vehicle unit: hits by range, knocks by armour (shot: [gun unit, target, dist, rounds])
  const [i, j, dist, rounds, h, t] = shot, { table, rng, acc, log } = ctx;
  let hits = 0, kills = 0;
  for (let s = 0; s < rounds; s++) if (rng.randint(1, 100) <= chanceAt(G.hit, dist)) hits++;
  const p = killChance(us[j], "gun", h, t);
  for (let s = 0; s < hits; s++) if (rng.randint(1, 100) <= p) kills++;
  const k = knockOut(us, j, kills, table, rng, acc), hm = harm(us[j], hits - k.knocked, acc.lost[j], rng);
  acc.dealt[i] += k.crew;
  log.push(...logged({ kind: "tankfire", att: i, dfd: j, dist, rounds, hit: hits, knocked: k.knocked, crew: k.crew, struck: k.struck, kill: p, ...harmLine(hm), ...ridersLine(k) }, k.tally));
}
const keyBefore = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);   // a gun target's [vehicle first, distance] ranks before another's
function gunTarget(us, i, field, G){              // [dist, index, gun hex, target hex]: the nearest enemy vehicle in range, sight and front with a line of fire, else the nearest such unit
  const u = us[i], occ = occupancy(us), front = footprint(u)[0], fv = fvec(u.facing);
  let best = null;
  us.forEach((e, j) => {
    if (e.side === u.side || e.men <= 0 || e.state === "fled") return;
    const clear = clearFn(us, occ, field, i, j);
    for (const t of footprint(e).flat()) for (const h of front){
      const dist = hdist(h, t), key = [e.vehicle ? 0 : 1, dist];
      if (dist <= G.range && (!best || keyBefore(key, best[0])) && canLay(field, clear, fv, [h, t, dist], seerOf(u))) best = [key, [dist, j, h, t]];
    }
  });
  return best ? best[1] : null;
}
function canLay(field, clear, fv, line, seer = null){   // a gun at h can be laid on t: ahead, in sight (seer: the crew's night device), with a clear line of fire
  const [h, t, dist] = line;
  return ahead(fv, h, t) && clearSight(field, h, t, dist) && !gunWeather(field, dist, h, t, seer).blocked && (!clear || clear(h, t, dist));
}
function ahead(fv, h, t){ const c = cube(t), s = cube(h); return (c[0] - s[0]) * fv[0] + (c[1] - s[1]) * fv[1] + (c[2] - s[2]) * fv[2] > 0 }
function fireBattery(us, table, rng, acc, log, c){   // at the target, guns knocked out there, then balls bounding on into the unit behind
  const a = us[c.att], b = us[c.dfd], gun = sideOfUnit(a, table);
  let t = takeHurt(b, cannonade(gun, b, c, rng, exposure(b, false, true)));
  a.spent = (a.spent || 0) + c.rounds;
  if (b.id !== undefined && b.id !== null) a.fired = { ...a.fired, [String(b.id)]: c.dist };
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
const offObjective = (u, obj) => Math.min(1e6, ...footprint(u).flat().map(h => hdist(h, obj)));   // hexes from its nearest hex to the objective (1e6 with no hexes)
function objectiveRadii(field){                    // [radius, hold, guard] of the field's objective: commander.objective's, widened by its own objective_radius (as units.objective_radii)
  const R = UD.commander.objective, r = field?.objective_radius || R.radius;
  return [r, R.hold + r - R.radius, R.guard + r - R.radius];
}
const secondView = field => ({ ...field, objective: [...field.objective2], objective_radius: null });   // the field as the commander sees it for the second objective, at its own radius (as units.second_view; read only)
function objectiveHeld(us, field){                 // with an objective marked: [{kind objective, hex, sides there (units' order), held (the one side there, else null)}], and a second line (second: true) for a second objective
  if (!field?.objective) return [];
  return field.objective2 ? [heldAt(us, field), { ...heldAt(us, secondView(field)), second: true }] : [heldAt(us, field)];
}
function heldAt(us, field){                        // {kind objective, hex, sides, held} for the field's objective (as units._held_at)
  const obj = field.objective, r = objectiveRadii(field)[0];
  const sides = [...new Set(us.filter(u => !ROUTED.has(u.state) && u.men > 0 && offObjective(u, obj) <= r).map(u => u.side))];
  return { kind: "objective", hex: [...obj], sides, held: sides.length === 1 ? sides[0] : null };
}
function exchange(units, table, rng, field = null){   // -> {units, log}; works being breached are updated in field
  const us = units.map(copyUnit), n = us.length, log = [];
  const acc = { lost: new Array(n).fill(0), dead: new Array(n).fill(0), dealt: new Array(n).fill(0), flanked: new Array(n).fill(false), fought: new Set() };
  toilGoing(us, field);
  const under = new Array(n).fill(false);          // under shellfire or machine-gun fire this exchange (suppression)
  minesAll(us, table, rng, acc, log, field);
  for (const c of closingFire(us, field)) fireBattery(us, table, rng, acc, log, c);
  strikeAll(us, table, rng, acc, log, field, [...acc.lost]);
  shootAll(us, table, rng, acc, log, field, under);
  indirectAll(us, table, rng, acc, log, field, under);
  assaultAll(us, table, rng, acc, log, field);
  breachAll(us, field, log);
  const occ = occupancy(us), before = us.map(u => u.men);
  us.forEach((u, i) => {
    const cut = Math.min(acc.lost[i], u.men);
    Object.assign(u, { men: u.men - cut, down: (u.down || 0) + cut, dead: (u.dead || 0) + Math.min(acc.dead[i], cut) });
    if (cut > 0) u.hit = true; else delete u.hit;   // it lost men this exchange: under fire, for the next moves
  });
  log.push(...moraleAll(us, occ, before, acc, rng, table, field), ...suppressAll(us, under, rng), ...heroesAfter(us, rng, us.map((_, i) => !acc.lost[i] && !under[i] && !inContact(us, occ, i)), cauterises(table), postsMoving(field)),
    ...partiesAfter(us, field), ...lyingAfter(us, table, rng), ...postsAfter(us, field, table, rng), ...digAll(us), ...sappersAll(us, field));
  postsSettle(field);
  toilFought(us, acc.fought);
  for (const u of us) delete u.unhooked;             // guns unhooked this move are in action (as units._unhooked_after)
  afterExchange(us, field, log);
  log.push(...landings(us, table, rng, field), ...airDrops(field, rng), ...vehiclesAfter(us, field), ...objectiveHeld(us, field));
  if (field?.mines && Object.keys(field.mines).length) for (const u of us) u.was = [[...u.pos], u.facing];   // where its next moves begin: the ground it crosses
  return { units: us, log };
}
// ---------- minefields (as gravewounds/units.py) ----------
function crossed(u, field = null){                 // the hexes u went into since was: its footprint at each step of the way it went (went), less where it began, in order (as units.crossed)
  const was = u.was;
  if (!was || (was[0][0] === u.pos[0] && was[0][1] === u.pos[1] && was[1] === u.facing)) return [];
  const seen = new Set(footprint({ ...u, pos: [...was[0]], facing: was[1] }).flat().map(hk)), out = [];
  for (const p of went(field, u, was[0])) for (const x of footprint({ ...u, pos: [...p] }).flat()){
    if (seen.has(hk(x))) continue;
    seen.add(hk(x));
    out.push(x);
  }
  return out;
}
function went(field, u, start){                   // the middle hex's way from start to u.pos, start left out ([pos] if it only turned): mine_path, else a straight line (as units.went)
  if (start[0] === u.pos[0] && start[1] === u.pos[1]) return [[...u.pos]];
  return (field ? minePath(field, u, start) : null) || ray([...start], u.pos, hdist(start, u.pos)).slice(1);
}
function minePath(field, u, start){               // within its allowance (times charge_move if it charged), the way crossing the fewest known enemy minefield hexes, then the cheapest; null if none (as units.mine_path)
  const limit = allowance(u) * (u.charged ? UD.charge_move : 1), size = fieldSize(field), goal = u.pos;
  if (limit <= 0 || hdist(start, goal) > limit) return null;
  const mines = field.mines || {}, steps = new Map(), levels = mineLevels(field, u, [start, limit, size], [mines, steps]);
  let end = null;
  for (let c = 0; c <= limit; c++){
    const m = levels[c].get(hk(goal));
    if (m !== undefined && (end === null || m < end[0])) end = [m, c];
  }
  return end ? mineWayBack(field, u, [goal, end[1], end[0]], [levels, steps, mines, size, start]) : null;
}
function mineLevels(field, u, [start, limit, size], [mines, steps]){   // for each movement spent, Map hex -> the fewest known enemy minefield hexes crossed to reach it for exactly that (as units._mine_levels)
  const levels = Array.from({ length: limit + 1 }, () => new Map());
  levels[0].set(hk(start), 0);
  for (let c = 0; c <= limit; c++){
    for (const [k, m0] of levels[c]){
      for (const [x, sc] of stepsCached(field, u, k.split(",").map(Number), size, steps)){
        const m = c + sc <= limit ? m0 + knownMinesAt(u, x, mines) : null;
        if (m !== null && m < (levels[c + sc].get(hk(x)) ?? 1e9)) levels[c + sc].set(hk(x), m);
      }
    }
  }
  return levels;
}
function stepsCached(field, u, h, size, steps){   // stepsFrom for hex h, other units left out, worked out once
  const k = hk(h);
  if (!steps.has(k)) steps.set(k, stepsFrom(field, u, h, {}, size));
  return steps.get(k);
}
const knownMinesAt = (u, x, mines) => footprint({ ...u, pos: [...x] }).flat().filter(y => { const m = mines[hk(y)]; return m && m.side !== u.side && knownMine(m, u.side) }).length;   // hexes of u's footprint at x in enemy minefields its side knows of (as units._known_mines_at)
function stepInto(field, u, p, h, size, steps){   // what it costs to step from p into h (null if it cannot, or p is off the map)
  if (!onMap(p, size)) return null;
  const e = stepsCached(field, u, p, size, steps).find(([x]) => x[0] === h[0] && x[1] === h[1]);
  return e ? e[1] : null;
}
function mineWayBack(field, u, [h0, c0, m0], [levels, steps, mines, size, start]){   // back to the start: at each hex the fitting neighbour nearest the straight line from the start, the first by direction of equals (as units._way_back)
  const line = ray([...start], h0, hdist(start, h0)), out = [[...h0]];
  let h = h0, c = c0, m = m0;
  while (c > 0){
    const here = knownMinesAt(u, h, mines), best = stepBack(field, u, [h, c, m - here], [levels, steps, size, line]);
    if (best === null) return null;
    [h, c, m] = [best[1], c - best[2], m - here];
    if (c > 0) out.push([...h]);
  }
  return out.reverse();
}
function stepBack(field, u, [h, c, want], [levels, steps, size, line]){   // [off the line, hex, cost] of the neighbour stepping into h from the level below with want mines (as units._step_back)
  let best = null;
  for (let dn = 0; dn < 6; dn++){
    const p = step(h, dn), sc = stepInto(field, u, p, h, size, steps);
    if (sc === null || sc > c || levels[c - sc].get(hk(p)) !== want) continue;
    const off = Math.min(...line.map(x => hdist(p, x)));
    if (best === null || off < best[0]) best = [off, p, sc];
  }
  return best;
}
function minesAll(us, table, rng, acc, log, field){   // units that went into minefield hexes set them off, before the shooting; each field set off is found
  const mines = field?.mines;
  if (!mines || !Object.keys(mines).length) return;
  us.forEach((u, i) => {
    if (u.men <= 0 || u.state === "fled") return;
    const hit = crossed(u, field).filter(x => hk(x) in mines && mines[hk(x)].side !== u.side);   // its own sappers' mines do not strike it
    if (!hit.length) return;
    for (const x of hit) mines[hk(x)].found = true;
    log.push(...setOff(us, i, hit.map(x => mines[hk(x)].kind), table, rng, acc));
  });
}
function minesVehicles(us, i, kinds, line, [table, rng, acc]){   // vehicles struck at the kind's vehicles %, knocked out at their armour's mine %, else immobilised
  const M = UD.mines, u = us[i];
  let struck = 0, kills = 0;
  for (const k of kinds) if (rng.randint(1, 100) <= M.kinds[k].vehicles) struck++;
  for (let s = 0; s < struck; s++) if (rng.randint(1, 100) <= armourOf(u).mine) kills++;
  const k = knockOut(us, i, kills, table, rng, acc), left = vehiclesLeft(u, acc.lost[i]), immobile = Math.min(left, struck - k.knocked);
  u.immobile = Math.min(left, (u.immobile || 0) + immobile);
  return logged({ ...line, struck, knocked: k.knocked, crew: k.crew, immobilised: immobile, ...ridersLine(k) }, k.tally);
}
function setOff(us, i, kinds, table, rng, acc){   // unit i in minefield hexes of these kinds: men struck at men % (a hex's worth a hex), vehicles at vehicles % then knocked at armour mine %, else immobilised
  const M = UD.mines, u = us[i], line = { kind: "mines", unit: i, hexes: kinds.length };
  if (u.vehicle) return minesVehicles(us, i, kinds, line, [table, rng, acc]);
  const per = form(u).per_hex;
  let struck = 0;
  for (const k of kinds) for (let s = 0; s < Math.min(per, u.men); s++) if (rng.randint(1, 100) <= M.kinds[k].men) struck++;
  const weapon = (FD.tables[table]?.weapons || []).includes(M.weapon) ? M.weapon : null;
  if (!struck || !weapon) return [{ ...line, struck, down: 0, dead: 0 }];
  const t = takeHurt(u, blows({ table, weapon, kit: null, quality: "regular" }, sideOfUnit(u, table), struck, M.attack, 0, rng, { exposed: exposure(u, false, true), shift: -1000 }));
  acc.lost[i] += t.down; acc.dead[i] += t.dead;
  return logged({ ...line, struck }, t);
}
function lzState(units, field, side, lz){         // blocked (an enemy within heliborne.blocked hexes), hot (an enemy could shoot at it) or cold
  const H = UD.heliborne;
  let hot = false;
  for (const u of units){
    if (u.side === side || u.men <= 0 || u.state === "fled") continue;
    const hexes = footprint(u).flat();
    if (hexes.some(x => hdist(x, lz) <= H.blocked)) return "blocked";
    hot = hot || (!out_(u) && couldShoot(field, u, hexes, lz));
  }
  return hot ? "hot" : "cold";
}
function couldShoot(field, u, hexes, t){          // u has a weapon that reaches hex t and sees it to aim
  if (!("range" in FD.weapons[u.weapon])) return false;
  return hexes.some(x => { const dist = hdist(x, t), wx = shotWeather(field, u.weapon, dist, x, t, seerOf(u)); return !wx.blocked && reaches(u, dist, wx.reach || 0) });
}
function landings(us, table, rng, field){         // helicopters back from their turnaround, then the lifts in order: men in, supply dumps, units lifted out (as units.landings)
  if (!UD.heliborne || !field) return [];
  for (const H of field.helos || []) H.away = (H.away || []).filter(t => t > 1).map(t => t - 1);
  const lifts = field.lifts || [], log = [], used = {};
  for (const lf of lifts) if (lf.left > 0) log.push(...fly(us, [table, rng, field], lf, used));
  field.lifts = lifts.filter(lf => lf.left > 0);
  return log;
}
function helos(field, side){                      // a side's helicopters (field.helos, made from heliborne's defaults the first time) (as units.helos)
  const list = field.helos || (field.helos = []), D = UD.heliborne;
  let H = list.find(x => x.side === side);
  if (!H){ H = { side, aircraft: D.aircraft, carry: D.carry, turnaround: D.turnaround, away: [], damaged: 0, downed: 0 }; list.push(H) }
  return H;
}
const helosFree = H => Math.max(0, H.aircraft - (H.away || []).length - (H.damaged || 0) - (H.downed || 0));   // ready to fly
function fly(us, [table, rng, field], lf, used){  // one lift this exchange, if its side has helicopters free and its zone room (as units._fly)
  const side = lf.unit.side, key = `${lf.lz[0]},${lf.lz[1]}`, H = helos(field, side), kind = lf.kind || "in";
  const can = Math.min(UD.heliborne.at_once - (used[key] || 0), helosFree(H));
  if (can <= 0) return [];
  const state = lzState(us, field, side, lf.lz);
  if (state === "blocked") return [{ kind: "waveoff", name: lf.unit.name, side, lz: lf.lz, why: "blocked" }];
  let n, log;
  if (kind === "supply"){ n = 1; log = supplyLift(field, lf) }
  else if (kind === "out") [n, log] = liftOut(us, [field, H, can], lf);
  else { [n, log] = land(us, [table, rng, field], lf, Math.min(lf.left, can * H.carry)); n = Math.ceil(n / H.carry) }
  if (n <= 0) return log;
  used[key] = (used[key] || 0) + n;
  return [...log, ...heloHits([rng, field], H, [n, state === "hot", lf])];
}
function supplyLift(field, lf){                    // a helicopter sets down a supply dump on its zone
  (field.dumps || (field.dumps = [])).push({ at: [...lf.lz], side: lf.unit.side });
  lf.left = 0;
  return [{ kind: "helisupply", side: lf.unit.side, lz: [...lf.lz] }];
}
function liftOut(us, [field, H, can], lf){        // a unit lifted away, as many men as the free helicopters carry, if within zone hexes and out of contact: [helicopters used, log] (as units._lift_out)
  const i = us.findIndex(u => u.id !== undefined && u.id !== null && u.id === lf.unit.id), u = i < 0 ? null : us[i];
  if (!u || u.men <= 0 || ROUTED.has(u.state)){ lf.left = 0; return [0, []] }
  const near = Math.min(...footprint(u).flat().map(h => hdist(h, lf.lz))) <= UD.heliborne.zone;
  if (!near || inContact(us, occupancy(us), i)) return [0, [{ kind: "waveoff", name: lf.unit.name, side: u.side, lz: lf.lz, why: near ? "contact" : "far" }]];
  const n = Math.min(u.men, can * H.carry);
  Object.assign(u, { men: u.men - n, flown: (u.flown || 0) + n });
  lf.left = u.men;
  if (!u.men) delete u.boarding;
  return [Math.ceil(n / H.carry), [{ kind: "flownout", unit: i, name: lf.unit.name, side: u.side, lz: lf.lz, men: n, all: !u.men }]];
}
function heloHits([rng, field], H, [n, hot, lf]){  // at a hot zone each helicopter hit at heliborne.hit %, downed at .downed % (a wreck) else damaged; the rest away for their turnaround (as units._helo_hits)
  const D = UD.heliborne;
  let hit = 0, downed = 0;
  for (let k = 0; k < n; k++) if (hot && rng.randint(1, 100) <= D.hit) hit++;
  for (let k = 0; k < hit; k++) if (rng.randint(1, 100) <= D.downed) downed++;
  H.damaged = (H.damaged || 0) + hit - downed;
  H.downed = (H.downed || 0) + downed;
  (H.away || (H.away = [])).push(...new Array(n - hit).fill(H.turnaround));
  for (let k = 0; k < downed; k++) wreckNear(field, lf.lz);
  return hit ? [{ kind: "helohit", side: H.side, lz: [...lf.lz], hit, downed }] : [];
}
function wreckNear(field, lz){                     // a downed helicopter's wreck on the nearest hex to the zone with no work on it
  if (!field.works) field.works = { edges: {}, hexes: {} };
  const hexes = field.works.hexes || (field.works.hexes = {});
  const h = within(lz, UD.heliborne.zone).find(x => !(`${x[0]},${x[1]}` in hexes));
  if (h) hexes[`${h[0]},${h[1]}`] = { type: "wreck", progress: 0 };
}
function land(us, [table, rng, field], lf, n){    // n of a lift's men landing at its zone, if they fit: [men landed, log] (as units._land)
  const side = lf.unit.side, name = lf.unit.name, state = lzState(us, field, side, lf.lz);
  let i = us.findIndex(u => u.id !== undefined && u.id !== null && u.id === lf.unit.id);
  if (i < 0) i = us.length;
  const u = i < us.length ? { ...us[i] } : { ...lf.unit, pos: [...lf.lz], men: 0, start: 0, down: 0, dead: 0, hurt: {}, heroes: [], state: "steady" };
  Object.assign(u, { men: u.men + n, start: u.start + n });
  const spots = i < us.length ? [u.pos] : within(lf.lz, UD.heliborne.zone);
  u.pos = spots.find(h => fits(us, i, { ...u, pos: [...h] }, fieldSize(field), field)) || null;
  if (!u.pos) return [0, [{ kind: "waveoff", name, side, lz: lf.lz, why: "room" }]];
  u.pos = [...u.pos];
  if (i < us.length) Object.assign(us[i], { men: u.men, start: u.start });
  else us.push(u);
  lf.left -= n;
  const line = { kind: "landed", unit: i, dfd: i, name, side, lz: lf.lz, men: n, hot: state === "hot", first: u.start === n };
  return [n, state === "hot" ? hotLanding(us[i], table, rng, n, line) : [line]];
}
function hotLanding(u, table, rng, n, line){      // each man landing struck at heliborne.hot %, wounds as shellfire
  const weapon = shellWeapon(table);
  let struck = 0;
  for (let k = 0; k < n; k++) if (rng.randint(1, 100) <= UD.heliborne.hot) struck++;
  if (!weapon || !struck) return [{ ...line, struck }];
  const t = takeHurt(u, blows({ table, weapon, kit: null, quality: "regular" }, sideOfUnit(u, table), struck, UD.indirect.attack, 0, rng, { exposed: exposure(u, false, true), shift: -1000 }));
  const cut = Math.min(t.down, u.men);
  Object.assign(u, { men: u.men - cut, down: (u.down || 0) + cut, dead: (u.dead || 0) + Math.min(t.dead, cut) });
  return logged({ ...line, struck }, t);
}
function afterExchange(us, field, log = []){        // charges spent, batteries changed over, pins wear off, missions come due, batteries displace, smoke thins and drifts
  us.forEach((u, i) => {
    u.charged = false;
    delete u.jostled;
    if (u.resupplying && ammoFull(u)) log.push({ kind: "resupplied", unit: i });
    batteryAfter(u);
    if (u.pinned) u.pinned -= 1;
    if (u.lost) u.lost -= 1;
  });
  flashes(us, log, field);
  beams(us, log, field);
  for (const b of field?.support || []) if (b.mission && (b.mission.wait || 0) > 0) b.mission.wait -= 1;
  log.push(...displaceAll(field), ...overrunAll(us, field));
  if (field?.smoke) field.smoke = Object.fromEntries(Object.entries(field.smoke).filter(([, n]) => n > 1).map(([h, n]) => [h, n - 1]));   // smoke thins
  smokeDrifts(field);
  if (field?.lit?.length) field.lit = field.lit.filter(x => x.left > 1).map(x => ({ ...x, left: x.left - 1 }));   // flares burn down
}
function displaceAll(field){                      // displacing batteries count down; one that has moved is no longer located, missions on it end
  const sup = field?.support || [], log = [];
  sup.forEach((b, k) => {
    if (!b.displacing) return;
    b.displacing -= 1;
    if (b.displacing) return;
    b.located = false;
    if (b.to !== undefined && b.to !== null){ b.place = b.to; delete b.to }   // its new position, plotted when it was ordered to move
    for (const x of sup) if (x.mission && x.mission.battery === k) x.mission = null;
    log.push({ kind: "displaced", sup: k, name: b.name, side: b.side, ...(b.place !== undefined && b.place !== null ? { place: b.place } : {}) });
  });
  return log;
}
function downwind(field){                         // the hex side (0-5) the wind blows smoke through, or null
  const w = field?.weather || {}, pts = WXD?.wind_points || [];
  if (!pts.includes(w.dir) || (w.wind || "calm") === "calm") return null;
  const [wx, wy] = WIND_VECTORS[(pts.indexOf(w.dir) - pts.indexOf(upOf(field)) + 12) % 8];
  let best = null, side = null;
  for (let dn = 0; dn < 6; dn++){
    const [dq, dr] = AX[dn], dot = Math.sqrt(3) * (dq + dr / 2) * wx + 1.5 * dr * wy;
    if (best === null || dot > best + 1e-9){ best = dot; side = dn }
  }
  return side;
}
function smokeDrifts(field){                      // smoke moves `drift` hexes downwind; off the map it is gone
  const sm = field?.smoke, side = sm ? downwind(field) : null, n = UD.indirect.smoke.drift?.[field?.weather?.wind || "calm"] || 0;
  if (side === null || !n) return;
  const size = field.size, out = {};
  for (const [key, left] of Object.entries(sm)){
    const h = step(key.split(",").map(Number), side, n);
    if (size && !(h[0] >= 0 && h[0] < size[0] && h[1] >= 0 && h[1] < size[1])) continue;
    const k2 = `${h[0]},${h[1]}`;
    out[k2] = Math.max(out[k2] || 0, left);
  }
  field.smoke = out;
}
function vehicleLosses(u, before, lost){          // [down, lost this exchange] for its morale: a vehicle unit's in whole vehicles gone (their crews), not crewmen hit in vehicles still fighting (as units._vehicle_losses)
  const K = vehicleKind(u);
  if (!K) return [u.down, lost];
  const startV = Math.ceil(u.start / K.crew), wasV = Math.ceil(before / K.crew), nowV = vehiclesLeft(u);
  return [(startV - nowV) * K.crew, Math.max(0, wasV - nowV) * K.crew];
}
function moraleAll(us, occ, before, acc, rng, table, field = null){
  const log = [], broke = [];
  us.forEach((u, i) => {
    if (out_(u)) return;
    const near = adjacentUnits(us, occ, i);
    const [down, lost] = vehicleLosses(u, before[i], acc.lost[i]);
    const unit = { quality: u.quality, start: u.start, down, lost, dealt: acc.dealt[i], men: before[i], state: u.state,
      leader: leaderState(u), flanked: acc.flanked[i], contact: near.some(j => us[j].side !== u.side), friends: near.some(j => us[j].side === u.side && us[j].state === "steady"), dug: low(u) || inBunker(field, u), no_ammo: ammoState(u) === "out" };
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
  if ((u.boarding || (u.resupplying && (isAtGun(u) || ammoFull(u)))) && u.state !== "broken" && u.state !== "fled") return 0;
  if (isBattery(u) && !u.abandoned && u.state !== "broken"){   // crews running from their guns run on foot
    if (u.limbering || u.resupplying) return 0;
    if (!u.limbered) return jostledMove(u, carrying(u, UD.artillery.pushed));
  }
  return jostledMove(u, carrying(u, u.mounted ? UD.mounted_move : form(u).move));
}
function jostledMove(u, move){                    // a move cut by rout.jostle for a unit a broken friend ran through this exchange (as units._jostled)
  return u.jostled && u.state !== "broken" && u.state !== "fled" ? Math.floor(move * (1 - UD.rout.jostle)) : move;
}
function carrying(u, move){                       // a unit's move, slowed (heroes.carried, at least 1 hex) if a lamed hero is with it
  return move && (u.heroes || []).some(lamed) ? Math.max(1, Math.floor(move * UD.heroes.carried)) : move;
}
function turnCost(u){ const n = Math.ceil(Math.max(1, u.men) / form(u).per_hex); return Math.max(1, Math.ceil(Math.min(u.width, n) / UD.turn_per)) }
const onMap = (h, size) => h[0] >= 0 && h[0] < size[0] && h[1] >= 0 && h[1] < size[1];
function canEnter(field, u, h){                  // no wagons or water; for horses, no marsh, stakes or felled trees; vehicles only on the ground they cross
  if (groundAt(field, h).impassable) return false;
  if (u.vehicle && !(groundKey(field, h) in UD.vehicles.ground)) return false;
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
function abandonImmobile(u){                       // a vehicle unit leaves its immobilised vehicles: their crews leave the fight unhurt (bailed)
  const K = vehicleKind(u), n = u.immobile || 0;
  if (!K || n <= 0) return u;
  const off = Math.min(u.men, n * K.crew), v = { ...u, men: u.men - off, bailed: (u.bailed || 0) + off, immobile: 0 };
  v.gunless = Math.min(v.gunless || 0, vehiclesLeft(v));
  return v;
}
const carries = u => { const K = vehicleKind(u); return K ? vehiclesLeft(u) * (K.carry || K.rides || 0) : 0 };   // men a vehicle unit can carry (inside, or on the hull)
const exposed = u => { const K = vehicleKind(u); return !!(K?.rides && (u.riders?.men || 0) > 0) };   // men riding on the outside of a vehicle unit
const tows = u => { const K = vehicleKind(u); return K ? vehiclesLeft(u) * (K.tows || 0) : 0 };   // anti-tank guns a vehicle unit can tow
function rideWhy(u, c){                             // why u cannot ride with c (anti-tank guns: be towed), before contact and distance; or null (as units._cannot_mount)
  if (isAtGun(u)){
    if (u.emplaced) return "the guns are emplaced";
    if (!c.vehicle || c.side !== u.side || tows(c) <= 0) return "those are not its side's gun tractors";
    if (c.riders) return "they tow guns already";
    return atGuns(u) > tows(c) ? `they can tow ${tows(c)}` : null;
  }
  if (u.vehicle || isGun(u.weapon) || u.mounted) return "only men on foot can ride";
  if (!c.vehicle || c.side !== u.side || carries(c) <= 0) return "those are not its side's carriers";
  if (c.riders) return "they carry men already";
  return u.men > carries(c) ? `they have room for ${carries(c)}` : null;
}
function placeWhy(units, occ, i, j){               // in contact, broken, or not beside the carriers; or null
  if (out_(units[i]) || out_(units[j]) || inContact(units, occ, i) || inContact(units, occ, j)) return "one of them is in contact or broken";
  const cs = footprint(units[j]).flat();
  return Math.min(...footprint(units[i]).flat().flatMap(a => cs.map(b => hdist(a, b)))) > 1 ? "they are not beside the carriers" : null;
}
function mountUnit(units, i, j){                    // foot unit i gets aboard vehicle unit j (anti-tank guns: hook up to its tractors) -> {ok, why, units}
  const u = units[i], c = units[j], occ = occupancy(units);
  const why = rideWhy(u, c) || placeWhy(units, occ, i, j);
  if (why) return { ok: false, why, units };
  const { pos, facing, ...rider } = u;
  return { ok: true, why: null, units: units.filter((_, k) => k !== i).map(x => (x === c ? { ...x, riders: rider } : x)) };
}
function dismountUnit(units, j, size, field = null){   // vehicle unit j's riders get down beside it (behind if they fit), added as the last unit -> {ok, why, units}
  const c = units[j], R = c.riders;
  if (!R) return { ok: false, why: "no one is aboard", units };
  const back = mod6(c.facing + 3), f = c.facing;
  for (const [dn, n] of [[back, 1], [back, 2], [mod6(f + 2), 1], [mod6(f + 5), 1], [mod6(f + 2), 2], [mod6(f + 5), 2], [f, 1], [back, 3], [back, 4]]){
    const spot = { ...R, pos: step(c.pos, dn, n), facing: f }, trial = [...units, spot];
    if (fits(trial, units.length, spot, size, field)){
      const out = units.map((x, k) => {
        if (k !== j) return x;
        const { riders, ...rest } = x;
        return rest;
      });
      return { ok: true, why: null, units: [...out, spot] };
    }
  }
  return { ok: false, why: "no room to get down beside them", units };
}
function vehiclesAfter(us, field){                  // immobilised and gunless no more than the vehicles left; riders of a unit with none left get down where it stood
  const log = [];
  [...us].forEach((u, j) => {
    if (!u.vehicle) return;
    const left = vehiclesLeft(u);
    for (const k of ["immobile", "gunless"]) if (k in u) u[k] = Math.min(u[k], left);
    if (left === 0 && u.riders && u.riders.men > 0){
      const r = dismountUnit(us, j, field?.size || [UD.map.cols, UD.map.rows], field);
      if (r.ok){ us.splice(0, us.length, ...r.units); log.push({ kind: "bailout", unit: j, riders: us.length - 1, men: us[us.length - 1].men }) }
    }
  });
  return log;
}
function fits(units, i, u, size, field = null){
  const occ = occupancy(units.filter((_, k) => k !== i)), hexes = footprint(u).flat();
  if (!hexes.every(h => onMap(h, size) && occ[hk(h)] === undefined)) return false;
  return !field || stands(field, u, hexes);
}
const hasLadders = u => !!u.ladders && !u.mounted && !u.vehicle;   // a unit on foot marked with ladders (as units.has_ladders)
const STEPS = [];                                  // while a commander orders its side (command): Map field -> Map "mover a>b" -> movement; nothing it orders changes the works, ground or weather (as units._STEPS)
function moverOf(u){                               // what a step's movement depends on in the unit: vehicle, horse, ladders or foot (as units._mover)
  if (u.vehicle) return "v";
  if (u.mounted) return "m";
  return hasLadders(u) ? "l" : "f";
}
function unitStepCost(field, u, a, b){            // movement for the middle hex from a to b: works, ground, deep going; null if it cannot; remembered while a commander orders its side (as units.step_cost)
  if (!field) return 1;
  if (!STEPS.length) return stepOf(field, u, a, b);
  const top = STEPS.at(-1), memo = top.get(field) || top.set(field, new Map()).get(field), key = moverOf(u) + hk(a) + ">" + hk(b);
  let c = memo.get(key);
  if (c === undefined){ c = stepOf(field, u, a, b); memo.set(key, c) }
  return c;
}
function stepOf(field, u, a, b){                  // unitStepCost, worked out (as units._step_cost)
  if (!canEnter(field, u, b)) return null;
  const c = stepCost(field.works, a, b, hasLadders(u) ? UD.escalade.cross : null);
  if (c === null) return null;
  const going = u.vehicle ? UD.vehicles.ground[groundKey(field, b)] : groundAt(field, b).move;
  return c + going - 1 + deepGoing(field.weather?.ground) + (coldOf(field)?.move || 0) + (lightOf(field)?.move || 0);
}
const mates = (units, i, through) => units.filter((x, k) => k !== i && !(through && x.side === units[i].side));   // the units whose hexes unit i's middle hex may not pass: all, or (through, for a charge) the enemy's (as units.mates)
function passedThrough(units, i, pos){             // the friendly units (not running) on the straight line of a charge from where unit i stands to pos (as units.passed_through)
  const u = units[i], line = new Set(ray(u.pos, pos, hdist(u.pos, pos)).map(hk));
  return units.flatMap((x, k) => (k !== i && x.side === u.side && x.state !== "broken" && x.state !== "fled" && footprint(x).flat().some(h => line.has(hk(h))) ? [k] : []));
}
function pathLen(units, i, goal, size, limit, field = null, through = false){   // least movement for the middle hex to goal (through: passing its own side's units); null if more than limit
  const occ = occupancy(mates(units, i, through)), u = units[i];
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
function stepsFrom(field, u, h, occ, size){       // [hex, cost] for each step the middle hex can take from h: the worst any of its hexes pays
  const out = [], front = field ? footprint({ ...u, pos: h }).flat() : [h];
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
function rootedWhy(u){                             // why a unit cannot leave its hex (though it may turn), or ""
  if (u.lost) return "it has lost its way in the dark (it may turn)";
  if (u.immobile) return `${u.immobile} of its vehicles cannot move (abandon them to move on; it may turn)`;
  return u.emplaced ? "it is emplaced, dug in for the battle (it may turn)" : "";
}
function moveUnit(units, i, pos, facing, size, field = null){   // {ok, cost, charge, why}
  const u = units[i];
  if (u.state === "broken" || u.state === "fled") return { ok: false, why: "it is running" };
  const same = pos[0] === u.pos[0] && pos[1] === u.pos[1] && facing === u.facing;
  if (inContact(units, occupancy(units), i) && !same) return { ok: false, why: "it is in contact" };
  const rooted = (pos[0] !== u.pos[0] || pos[1] !== u.pos[1]) && rootedWhy(u);
  if (rooted) return { ok: false, why: rooted };
  const turns = Math.min(mod6(facing - u.facing), mod6(u.facing - facing)), most = allowance(u) * UD.charge_move;
  const [steps, through] = chargePath(units, i, pos, size, most, field);
  if (steps === null) return { ok: false, why: "too far, or no way through" };
  const moved = { ...u, pos: pos.slice(), facing: mod6(facing) };
  if (!fits(units, i, moved, size, field)) return { ok: false, why: "no room there" };
  const cost = steps + turns * turnCost(u) + (turns ? sweepCost(field, { ...u, pos: pos.slice() }, moved) : 0), after = units.map((x, k) => (k === i ? moved : x));
  return moveVerdict(units, i, pos, { cost, steps, most, through, contact: inContact(after, occupancy(after), i) });
}
function moveVerdict(units, i, pos, { cost, steps, most, through, contact }){   // {ok, cost, charge, through?, why} for a move whose path, cost and contact are known (as the end of units.move)
  const u = units[i];
  if (through && !contact) return { ok: false, why: "it can pass through its own men only to charge" };
  const passed = through ? { through: passedThrough(units, i, pos) } : {};
  if (cost <= allowance(u)) return { ok: true, cost, charge: contact && steps > 0, ...passed };
  if (contact && u.state === "steady" && cost <= most) return { ok: true, cost, charge: true, ...passed };
  return { ok: false, why: "too far" };
}
function chargePath(units, i, pos, size, most, field){   // [least movement, passing through friends]: round them, else (a steady unit, for a charge) through them (as units._charge_path)
  const steps = pathLen(units, i, pos, size, most, field);
  if (steps !== null || units[i].state !== "steady") return [steps, false];
  return [pathLen(units, i, pos, size, most, field, true), true];
}
function flee(units, i, size, field = null){      // a broken unit runs straight back; off the map it has fled; through its own side's units to the first free ground beyond (as units.flee)
  let u = { ...units[i] };
  if (!footprint(u).some(row => row.length)) return { ...u, state: "fled" };   // no men left standing in it: it is gone
  const back = mod6(u.facing + 3), allow = allowance(u);
  const others = units.filter((x, k) => k === i || x.side !== u.side), j = others.indexOf(units[i]);
  let clear = u;
  for (let n = 0; n < allow * UD.rout.through; n++){
    const nxt = { ...u, pos: step(u.pos, back) };
    if (!footprint(nxt).every(row => row.every(h => onMap(h, size)))) return { ...u, state: "fled" };
    if (unitStepCost(field, u, u.pos, nxt.pos) === null || !fits(others, j, nxt, size, field)) break;
    u = nxt;
    if (fits(units, i, u, size, field)){
      clear = u;
      if (n + 1 >= allow) break;
    }
  }
  return clear;
}
function ranThrough(units, i, after){             // indices of the friendly units unit i passed through running straight back to after (as units.ran_through)
  let u = { ...units[i] };
  const back = mod6(u.facing + 3), out = [];
  while ((u.pos[0] !== after.pos[0] || u.pos[1] !== after.pos[1]) && after.state !== "fled"){
    u = { ...u, pos: step(u.pos, back) };
    const hexes = new Set(footprint(u).flat().map(hk));
    units.forEach((x, k) => {
      if (k !== i && !out.includes(k) && x.side === u.side && x.state !== "broken" && x.state !== "fled" && footprint(x).flat().some(h => hexes.has(hk(h)))) out.push(k);
    });
  }
  return out;
}
function runAway(units, i, size, field = null){   // units after broken unit i runs, the friends it ran through jostled (as units.run_away)
  const after = flee(units, i, size, field), hit = new Set(ranThrough(units, i, after));
  return units.map((x, k) => {
    if (k === i) return after;
    return hit.has(k) ? { ...x, jostled: true } : x;
  });
}

// ---------- the enemy commander (as gravewounds.commander) ----------
const ROUTED = new Set(["broken", "fled"]);
const AI_MOVES = new Set(["move", "charge", "advance", "fall_back", "close_up", "spot", "search"]);   // orders that take a unit somewhere new (as commander.MOVES)
function command(units, side, size, field, rng, exchange = null, { stance = "attack", memory = null, table = null } = {}){   // {units, orders}: each unit of side ordered in turn, by its quality (units.yaml commander); stance attack or hold; memory: where it last saw each enemy (updated in place); each step's movement worked out once while it orders
  STEPS.push(new Map());
  try { return orderSide(units, side, [size, field, rng, exchange], { stance, memory, table }) }
  finally { STEPS.pop() }
}
function orderSide(units, side, [size, field, rng, exchange], { stance, memory, table }){   // command, worked out (as commander._command)
  let us = units.map(u => ({ ...u }));
  const orders = [], mem = memory ?? {};
  const known = sightings(us, side, field, exchange, mem), aim = aims(us, side, field, stance, mem);
  const goal = aim[1];                              // the field with the objective most of its units go for (with a second one marked)
  { const h = hookUp(us, side, [goal, known, exchange, stance]); us = h.units; orders.push(...h.orders) }
  { const r = ridersAi(us, side, [goal, known, exchange, stance], orders); us = r.units; orders.splice(0, orders.length, ...r.orders) }
  holdBack(us, side, known);
  orders.push(...commitReserve(us, side, known, mem));
  if (stance === "hold") orders.push(...fixLines(us, side, [field, known, exchange]));
  for (let i = 0; i < us.length; i++){
    if (us[i].side !== side || !commandable(us, i, exchange)) continue;
    const roll = rng.randint(1, 100), o1 = unitOrder(us, i, [size, plugging(aimOf(us, i, aim), us[i]), stance, known, exchange], roll);
    const o0 = spotter(us, i, o1, [size, field, stance, known]) || o1;
    const o = o0 && us[i].plug && (o0.act === "advance" || o0.act === "fall_back") ? { ...o0, gap: true } : o0;   // going to plug the gap, not the side's objective
    if (o){
      orders.push({ unit: i, ...o });
      applyOrder(us, i, o);
      if (AI_MOVES.has(o.act)) sightings(us, side, field, exchange, mem);   // what it sees from where it went, the units after it know (as commander.command)
    }
  }
  orders.push(...moveGuns(us, side, [size, goal, stance, known, exchange]), ...layGuns(us, side, [size, goal, known, exchange]), ...callFireAi(us, side, goal, known, [stance, exchange, orders, table]));
  return { units: us, orders };
}
function aims(us, side, field, stance, mem){       // [the field as its garrison of the first objective sees it, as the rest see it, the garrison's indices] (as commander.aims)
  if (!field?.objective || !field.objective2) return [field, field, []];
  const held = objectiveHeld(us, field)[0].held, second = secondView(field), plan = mem.plan ?? (mem.plan = {});
  if (stance !== "attack") return held !== null && held !== side ? [second, second, []] : [field, field, []];
  if (held !== side){ delete plan.garrison; return [field, field, []] }
  const at = [[...field.objective], [...field.objective2]];
  if (!plan.garrison || JSON.stringify(plan.garrison.at) !== JSON.stringify(at)){
    const r = objectiveRadii(field)[0];
    plan.garrison = { at, units: us.map((u, k) => k).filter(k => us[k].side === side && us[k].men > 0 && !ROUTED.has(us[k].state) && offObjective(us[k], field.objective) <= r).map(k => us[k].id ?? k) };
  }
  return [field, second, plan.garrison.units];
}
const aimOf = (us, i, aim) => (aim[2].includes(us[i].id ?? i) ? aim[0] : aim[1]);   // the field (objective) unit i goes for: the first's if it is in the garrison, by id (as commander._aim)
const knownFoes = known => Object.entries(known).filter(([k]) => /^\d+$/.test(k));   // [index, {pos, facing, ex}] of the enemies it knows of
function holdBack(us, side, known){                // at its first move (unless the GM marked reserves), its rearmost units up to commander.reserve % of its men are held back, not one on a route (as commander._hold_back)
  const mine = us.map((u, i) => i).filter(i => us[i].side === side && us[i].men > 0 && !ROUTED.has(us[i].state));
  if (!mine.length || mine.some(i => "reserve" in us[i])) return;
  const byQ = {};
  let men = 0;
  for (const i of mine){ men += us[i].men; byQ[us[i].quality] = (byQ[us[i].quality] || 0) + us[i].men }
  const keys = Object.keys(byQ).sort((a, b) => a.localeCompare(b)), q = keys.reduce((a, k) => (byQ[k] > byQ[a] ? k : a), keys[0]);
  let room = Math.floor(men * (UD.commander.reserve[q] ?? 0) / 100);
  const known0 = !knownFoes(known).length;
  const foes = us.map((e, j) => j).filter(j => us[j].side !== side && us[j].men > 0 && !ROUTED.has(us[j].state) && (known0 || String(j) in known));
  const away = i => (foes.length ? Math.min(...foes.map(j => hdist(us[i].pos, knownAt(us, j, known).pos))) : 0);
  const far = [...mine].sort((a, b) => away(b) - away(a) || a - b);
  for (const i of mine) us[i].reserve = false;
  for (const i of far){
    if (isBattery(us[i]) || isAtGun(us[i]) || tractor(us[i]) || us[i].via || us[i].men > room) continue;
    us[i].reserve = true;
    room -= us[i].men;
  }
}
function commitReserve(us, side, known, memory){   // one reserve unit committed when one of its units broke, an enemy is within gap of a reserve unit, or (veterans) an enemy broke (as commander._commit)
  const plan = memory.plan ?? (memory.plan = {});
  const own = us.filter(u => u.side === side && ROUTED.has(u.state)).length, foe = us.filter(u => u.side !== side && ROUTED.has(u.state)).length;
  const broke = own > (plan.own ?? own), foeBroke = foe > (plan.foe ?? foe);
  Object.assign(plan, { own, foe });
  const hole = gapLeft(us, side, plan);
  const held = us.map((u, i) => i).filter(i => us[i].side === side && us[i].reserve && us[i].men > 0 && !ROUTED.has(us[i].state));
  if (!held.length) return [];
  if (broke && hole !== null){
    const pick = held.reduce((a, i) => (hdist(us[i].pos, hole) < hdist(us[a].pos, hole) ? i : a), held[0]);
    Object.assign(us[pick], { reserve: false, plug: [...hole] });
    return [{ unit: pick, act: "commit", why: "broke", at: [...hole] }];
  }
  const kf = knownFoes(known), near = {};
  for (const i of held) near[i] = kf.length ? Math.min(...kf.map(([, m]) => hdist(us[i].pos, m.pos))) : 10 ** 6;
  const nearest = list => list.reduce((a, i) => (near[i] < near[a] ? i : a), list[0]);
  const gap = held.some(i => near[i] <= UD.commander.gap), vets = held.filter(i => us[i].quality === "veteran");
  let pick, why;
  if (broke || gap){ pick = nearest(held); why = broke ? "broke" : "gap" }
  else if (foeBroke && vets.length){ pick = nearest(vets); why = "exploit" }
  else return [];
  us[pick].reserve = false;
  return [{ unit: pick, act: "commit", why }];
}
function fixLines(us, side, [field, known, exchange]){   // holding, by day or at dusk, its machine guns: with no fixed line, laid on the nearest known enemy in reach, else ahead toward the nearest known enemy (or along its facing); a line laid ahead is shifted once onto an enemy in reach off it (as commander._fix_lines)
  if (lightOf(field) && field?.weather?.light !== "dusk") return [];
  const out = [];
  us.forEach((u, i) => {
    if (u.side !== side || u.vehicle || !isMg(u.weapon) || u.state !== "steady" || u.men <= 0) return;
    if ((exchange !== null && u.arrived === exchange) || (u.fixed && !u.fix_ahead)) return;
    const o = fixOrder(us, i, field, known);
    if (!o) return;
    const rest = { ...u };
    delete rest.fix_ahead;
    us[i] = { ...rest, fixed: o.hex, ...(o.ahead ? { fix_ahead: true } : {}) };
    out.push({ unit: i, ...o });
  });
  return out;
}
function fixOrder(us, i, field, known){           // machine gun i's fixed line: on the nearest known enemy in reach; with none and no line yet, ahead (lineAhead); a line laid ahead shifted onto such an enemy off it (relay); null: no change (as commander._fix_order)
  const u = us[i];
  const foes = knownFoes(known).map(([k, m]) => [hdist(u.pos, m.pos), Number(k)]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const near = foes.filter(([dist]) => dist > 0 && fieldRange(u.weapon, dist) !== null);
  if (near.length){
    const j = near[0][1], at = [...known[String(j)].pos];
    if (u.fixed && onLine(u, at)) return null;
    return { act: "fix", target: j, hex: at, ...(u.fixed ? { relay: true } : {}) };
  }
  if (u.fixed) return null;
  const at = lineAhead(u, field, foes.length ? known[String(foes[0][1])].pos : null);
  return at === null ? null : { act: "fix", target: foes.length ? foes[0][1] : null, hex: at, ahead: true };
}
function onLine(u, h){                            // hex h within light.fixed_line.width of machine gun u's fixed line (as commander._on_line)
  const front = footprint(u)[0], g = front[Math.floor(front.length / 2)], n = hdist(g, u.fixed), w = FD.weather.light.fixed_line.width;
  return n > 0 && ray(g, u.fixed, n).slice(1).some(x => hdist(x, h) <= w);
}
function lineAhead(u, field, toward){             // the hex a machine gun lays a line ahead on: along the line from its front's middle toward a known enemy out of reach, else along its facing, the furthest hex before the first it cannot reach or see, or the map's edge; null if none (as commander._line_ahead)
  const front = footprint(u)[0], g = front[Math.floor(front.length / 2)];
  let reach = 0;
  for (let n = 1; n < 400; n++) if (fieldRange(u.weapon, n) !== null) reach = n;
  let far = toward !== null ? [...toward] : g;
  for (let k = 0; k < (toward !== null ? 0 : 2 * reach); k++) far = step(far, u.facing + (k % 2));
  const size = field?.size || [1e6, 1e6];
  let best = null;
  for (const x of ray(g, far, hdist(g, far)).slice(1)){
    const on = x[0] >= 0 && x[0] < size[0] && x[1] >= 0 && x[1] < size[1];
    if (!on || fieldRange(u.weapon, hdist(u.pos, x)) === null || !sees(field, u, x, sightHexes(field, x, seerOf(u)))) break;
    best = [...x];
  }
  return best;
}
function gapLeft(us, side, plan){                 // where the first of its units newly broken stood at its last move, or null; then where its standing units are now (as commander._gap_left)
  const was = plan.stood || {};
  const k = us.findIndex((u, j) => u.side === side && ROUTED.has(u.state) && String(u.id ?? j) in was);
  const hole = k < 0 ? null : was[String(us[k].id ?? k)];
  plan.stood = Object.fromEntries(us.map((u, j) => [u, j]).filter(([u]) => u.side === side && !ROUTED.has(u.state) && u.men > 0).map(([u, j]) => [String(u.id ?? j), [...u.pos]]));
  return hole;
}
const plugging = (field, u) => (u.plug ? { ...field, objective: [...u.plug], objective_radius: null } : field);   // a reserve unit sent to plug a gap sees that hex as its objective (as commander._plugging)
function layGuns(us, side, [size, field, known, exchange]){   // its batteries and anti-tank guns on the map turn to face the nearest enemy it knows of (as commander._lay_guns)
  const out = [], occ = occupancy(us), kf = knownFoes(known);
  us.forEach((u, i) => {
    if (u.side !== side || !(isBattery(u) || isAtGun(u)) || u.state !== "steady" || u.men <= 0 || u.limbered || u.limbering) return;
    if ((exchange !== null && u.arrived === exchange) || inContact(us, occ, i) || !kf.length) return;
    const j = kf.map(([k, m]) => [hdist(u.pos, m.pos), Number(k)]).reduce((a, b) => (b[0] < a[0] || (b[0] === a[0] && b[1] < a[1]) ? b : a), [Infinity, Infinity])[1];
    const f = bearing(u.pos, knownAt(us, j, known).pos);
    if (f !== u.facing && moveUnit(us, i, u.pos, f, size, field).ok){ us[i] = { ...u, facing: f }; out.push({ unit: i, act: "turn", target: j, facing: f }) }
  });
  return out;
}
const TOW_SLACK = 4;                               // hexes from its tractor the guns may land when unhooked (dismountUnit: up to 4 behind)
function gunReach(u){                              // how far a gun unit's guns reach, or null; a tractor towing guns counts TOW_SLACK less, so its guns land in reach (as commander.gun_reach)
  if (isBattery(u)) return gunRange(u);
  if (isAtGun(u)) return UD.anti_tank_guns.gun.range;
  return u.riders && isAtGun(u.riders) ? UD.anti_tank_guns.gun.range - TOW_SLACK : null;
}
function gunGoal(us, u, field, known){              // [target or null, hex to go for, in reach]: the nearest enemy it knows of, else the objective while beyond its radius (as commander._gun_goal)
  const kf = knownFoes(known).map(([k, m]) => [hdist(u.pos, m.pos), Number(k)]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (kf.length){ const [dist, j] = kf[0]; return [j, [...knownAt(us, j, known).pos], dist <= gunReach(u)] }
  const obj = objectiveOf(field);
  if (obj === null || offObjective(u, obj) <= objectiveRadii(field)[0]) return [null, null, true];
  return [null, obj, false];
}
function gunReady(us, i, side, exchange){           // a gun unit of the side it may order: steady, with men, not just come on, out of contact, not abandoned, changing over or resupplying (as commander._gun_ready)
  const u = us[i];
  if (u.side !== side || u.state !== "steady" || u.men <= 0 || u.abandoned) return false;
  if ((exchange !== null && u.arrived === exchange) || u.limbering || u.resupplying) return false;
  return !inContact(us, occupancy(us), i);
}
function ridersAi(units, side, ctx, orders0){     // {units, orders}: its carriers' riders get down; then, attacking, its foot units get aboard empty carriers beside them (as commander._riders)
  let us = units, orders = orders0;
  for (let j = 0; j < us.length; j++){
    const r = getDown(us, j, side, ctx);
    if (r){ us = r.units; orders.push(r.order) }
  }
  if (ctx[3] !== "attack") return { units: us, orders };
  let i = 0;
  while (i < us.length){
    const j = carrierFor(us, i, side, ctx);
    if (j === null){ i++; continue }
    const name = us[i].name ?? null;
    us = mountUnit(us, i, j).units;
    dropIndex(ctx[1], i);
    orders = orders.map(o => (Number.isInteger(o.unit) ? { ...o, unit: o.unit - (o.unit > i ? 1 : 0) } : o));
    orders.push({ unit: j - (j > i ? 1 : 0), act: "mount", riders: name });
  }
  return { units: us, orders };
}
const weaponsReach = (weapons, dist) => weapons.some(w => "range" in FD.weapons[w] && fieldRange(w, dist) !== null);   // any of these weapons that shoot reaches dist (as commander._in_reach)
const enemyInReach = (at, weapons, known) => knownFoes(known).some(([, m]) => weaponsReach(weapons, hdist(at, m.pos)));   // a known enemy within reach of any of them from at (as commander._enemy_in_reach)
function getDown(us, j, side, [field, known, exchange]){   // {units, order} when carrier j's riders get down: an enemy it knows of in reach of theirs or its weapon, or at the objective (as commander._get_down)
  const c = us[j], R = c.riders;
  if (c.side !== side || !c.vehicle || !R || (R.men ?? 0) <= 0 || isAtGun(R) || ROUTED.has(c.state)) return null;
  const obj = objectiveOf(field), atObj = obj !== null && offObjective(c, obj) <= objectiveRadii(field)[0];
  if (!atObj && !enemyInReach(c.pos, [R.weapon, c.weapon], known)) return null;
  const r = dismountUnit(us, j, fieldSize(field), field);
  if (!r.ok) return null;
  return { units: [...r.units.slice(0, -1), { ...r.units.at(-1), arrived: exchange }], order: { unit: j, act: "dismount", riders: R.name ?? null } };
}
function carrierFor(us, i, side, [field, known, exchange]){   // the first empty carrier beside attacking foot unit i it can board, with no known enemy in reach of its weapon or the carrier's; else null (as commander._carrier_for)
  const u = us[i];
  if (u.side !== side || u.vehicle || u.reserve || !commandable(us, i, exchange) || u.state !== "steady") return null;
  if (u.digging || u.mining || u.clearing || u.prone) return null;
  const obj = objectiveOf(field);
  if (obj !== null && offObjective(u, obj) <= objectiveRadii(field)[0]) return null;
  for (let j = 0; j < us.length; j++){
    const c = us[j];
    if (j === i || !c.vehicle || tractor(c) || (c.immobile || 0) >= vehiclesLeft(c) || !mountUnit(us, i, j).ok) continue;
    if (![u.pos, c.pos].some(at => enemyInReach(at, [u.weapon, c.weapon], known))) return j;
  }
  return null;
}
function dropIndex(known, i){                       // unit i has left the list: the enemy indices remembered above it move down one (as commander._drop_index)
  const moved = Object.entries(known).map(([k, v]) => [/^\d+$/.test(k) && +k > i ? String(+k - 1) : k, v]);
  for (const k of Object.keys(known)) delete known[k];
  for (const [k, v] of moved) known[k] = v;
}
function hookUp(units, side, [field, known, exchange, stance]){   // anti-tank guns hook up to an empty tractor beside them: attacking, with no known enemy in reach and somewhere to go; either stance, under threat (as commander._hook_up)
  let us = units, out = [], i = 0;
  while (i < us.length){
    const u = us[i];
    if (!isAtGun(u) || u.emplaced || !gunReady(us, i, side, exchange)){ i++; continue }
    const [, goal, inr] = gunGoal(us, u, field, known);
    const wants = (stance === "attack" && !inr && goal !== null) || gunThreat(us, i, known) !== null;
    const j = wants ? us.findIndex((c, k) => k !== i && mountUnit(us, i, k).ok) : -1;
    if (j < 0){ i++; continue }
    us = mountUnit(us, i, j).units;
    dropIndex(known, i);
    out = out.map(o => ({ ...o, unit: o.unit - (o.unit > i ? 1 : 0) }));
    out.push({ unit: j - (j > i ? 1 : 0), act: "hook", guns: u.name ?? null });
  }
  return { units: us, orders: out };
}
function moveGuns(us, side, ctx){                   // its batteries and tractors towing anti-tank guns limber, move, unlimber or unhook; attacking, empty tractors fetch guns (as commander._move_guns)
  const [size, field, stance, , exchange] = ctx, out = [], n = us.length, claimed = new Set();
  for (let i = 0; i < n; i++){
    const u = us[i];
    let o;
    if (stance === "attack" && tractor(u) && !u.riders && gunReady(us, i, side, exchange)) o = fetchGuns(us, i, ctx, claimed);
    else if (!(isBattery(u) || (tractor(u) && gunReach(u))) || !gunReady(us, i, side, exchange)) continue;
    else {
      const j = gunThreat(us, i, ctx[3]);
      o = j === null ? gunOrder(us, i, ctx) : pullBack(us, i, j, ctx);
    }
    if (o && gunApply(us, i, o, [size, field, exchange])) out.push({ unit: i, ...o });
  }
  return out;
}
function wantsTow(us, g, [, field, , known, exchange]){   // anti-tank guns that would hook up: on the map, not emplaced, ready, nothing in reach and somewhere to go (as commander._wants_tow)
  const e = us[g];
  if (!isAtGun(e) || e.emplaced || !gunReady(us, g, e.side, exchange)) return false;
  const [, goal, inr] = gunGoal(us, e, field, known);
  return goal !== null && !inr;
}
function fetchGuns(us, i, ctx, claimed){            // an empty tractor goes beside the nearest guns that want a tow and that it can tow, facing where they will go (as commander._fetch)
  const [size, field, , known] = ctx, u = us[i];
  const guns = us.map((e, g) => [e, g]).filter(([e, g]) => e.side === u.side && !claimed.has(g) && wantsTow(us, g, ctx) && rideWhy(e, u) === null)
    .map(([e, g]) => [hdist(u.pos, e.pos), g]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  if (!guns.length) return null;
  const g = guns[0][1];
  claimed.add(g);
  const goal = gunGoal(us, us[g], field, known)[1], near = footprint(us[g]).flat(), occ = occupancy(us);
  const foes = new Set(Object.keys(occ).filter(k => us[occ[k]].side !== u.side));
  const cands = [...reachable(us, i, size, allowance(u), field).values()].map(([h, c]) => {
    const f = bearing(h, goal), gap = Math.min(...footprint({ ...u, pos: h, facing: f }).flat().flatMap(a => near.map(b => hdist(a, b))));
    return [gap <= 1 ? 0 : gap, c, h[1], h[0], f];
  }).sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3] || a[4] - b[4]);
  let tries = UD.commander.tries;
  for (const [, c, row, col, f] of cands){
    const h = [col, row];
    if (h[0] === u.pos[0] && h[1] === u.pos[1]) return null;
    if (touches({ ...u, pos: h, facing: f }, foes)) continue;
    if (tries === 0) return null;
    tries -= 1;
    const m = legalMove(us, i, [h, f, c, false], [size, field]);
    if (m.ok) return { act: "fetch", target: null, guns: g, pos: h, facing: f, cost: m.cost };
  }
  return null;
}
function gunThreat(us, i, known){                  // the enemy it knows of that could charge gun unit i this move with no steady friend between, or null (as commander.threat)
  const u = us[i];
  const foes = knownFoes(known).map(([k, m]) => [hdist(u.pos, m.pos), Number(k)]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  for (const [dist, j] of foes){
    const e = us[j];
    if (e.state === "broken" || e.state === "fled" || e.men <= 0 || dist > allowance(e) * UD.charge_move) continue;
    if (!screened(us, i, knownAt(us, j, known).pos)) return j;
  }
  return null;
}
function screened(us, i, a){                        // a steady friendly unit (not guns or vehicles) has a hex on the straight line between hex a and gun unit i (as commander._screened)
  const u = us[i], line = new Set(ray(a, u.pos, hdist(a, u.pos)).slice(1, -1).map(hk));
  return us.some((x, k) => k !== i && x.side === u.side && x.state === "steady" && !isBattery(x) && !isAtGun(x) && !x.vehicle && footprint(x).flat().some(h => line.has(hk(h))));
}
function pullBack(us, i, j, [size, field, , known]){   // under threat from enemy j: a battery in action limbers; one limbered (or a tractor) goes to the hex in its allowance furthest from the enemy, keeping its facing (as commander._pull_back)
  const u = us[i];
  if (isBattery(u) && !u.limbered) return { act: "limber", target: j, back: true };
  const foe = knownAt(us, j, known).pos, occ = occupancy(us), here = hdist(u.pos, foe);
  const foes = new Set(Object.keys(occ).filter(k => us[occ[k]].side !== u.side));
  const cands = [...reachable(us, i, size, allowance(u), field).values()].map(([h, c]) => [-hdist(h, foe), c, h[1], h[0]])
    .sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3]);
  let tries = UD.commander.tries;
  for (const [far, c, row, col] of cands){
    const h = [col, row];
    if (-far <= here) return null;
    if (touches({ ...u, pos: h }, foes)) continue;
    if (tries === 0) return null;
    tries -= 1;
    const m = legalMove(us, i, [h, u.facing, c, false], [size, field]);
    if (m.ok) return { act: "pull_back", target: j, pos: h, facing: u.facing, cost: m.cost };
  }
  return null;
}
function gunOrder(us, i, [size, field, stance, known]){   // holding, or with an enemy in reach, it unlimbers (unhooks); else a battery in action limbers, and one limbered or a tractor moves (as commander._gun_order)
  const u = us[i], battery = isBattery(u), [t, goal, inr] = gunGoal(us, u, field, known);
  if (stance === "hold" || inr){
    if (battery) return u.limbered ? { act: "unlimber", target: t } : null;
    return { act: "unhook", target: t };
  }
  if (battery && !u.limbered) return { act: "limber", target: t };
  return gunMove(us, i, [t, goal], [size, field]);
}
function gunMove(us, i, [t, goal], [size, field]){   // the best hex within its allowance, not touching the enemy, facing its goal (as commander._gun_move)
  const u = us[i], K = UD.commander, reach = gunReach(u), allow = allowance(u), occ = occupancy(us);
  const foes = new Set(Object.keys(occ).filter(k => us[occ[k]].side !== u.side));
  const cands = [...reachable(us, i, size, allow, field).values()].map(([h, c]) => {
    const dist = hdist(h, goal);
    let s = -c - (K.mines[u.quality] ?? 0) * mined(field, u.pos, h, u.side);
    if (t === null) s -= K.closing * dist;
    else s += (dist >= K.keep_off && dist <= reach ? K.in_range : -K.closing * dist) - (dist < K.keep_off ? K.too_close : 0);
    return [-s, c, aside(h, goal), h[1], h[0]];
  }).sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3] || a[4] - b[4]);
  let tries = K.tries;
  for (const [, c, , row, col] of cands){
    const h = [col, row];
    if (h[0] === u.pos[0] && h[1] === u.pos[1]) return null;
    const f = bearing(h, goal);
    if (touches({ ...u, pos: h, facing: f }, foes)) continue;
    if (tries === 0) return null;
    tries -= 1;
    const m = legalMove(us, i, [h, f, c, false], [size, field]);
    if (m.ok) return { act: t === null ? "advance" : "move", target: t, pos: h, facing: f, cost: m.cost };
  }
  return null;
}
function gunApply(us, i, o, [size, field, exchange]){   // limber or unlimber (changing over), move, or unhook the towed guns beside the tractor; false with no room (as commander._gun_apply)
  if (o.act === "unhook"){
    const r = dismountUnit(us, i, size, field);
    if (!r.ok) return false;
    us.splice(0, us.length, ...r.units.slice(0, -1), { ...r.units.at(-1), arrived: exchange, unhooked: true });
  } else if (o.act === "limber" || o.act === "unlimber") us[i] = { ...us[i], limbering: true };
  else us[i] = { ...us[i], pos: o.pos, facing: o.facing };
  return true;
}
function callFireAi(us, side, field, known, [stance, exchange, orders, table] = ["attack", null, [], null]){   // its batteries under counter-battery fire displace; in the dark, one battery lights an enemy it lost sight of; attacking, one battery lays smoke where its units are under fire; its other free batteries are called on the enemy it sees that scores best as a target (as commander._call_fire)
  const out = displaceAi(field, side);
  const free = (field?.support || []).map((b, k) => k).filter(k => freeBattery(field.support[k], side));
  out.push(...callIllum(us, side, field, [known, exchange], free));
  if (stance === "attack") out.push(...callSmoke(us, side, field, known, free));
  out.push(...aiCounter(field, side, free));
  if (stance === "attack") out.push(...callCreep(us, side, field, [known, orders || []], free));
  const air = (field?.support || []).map((b, k) => k).filter(k => freeAir(field, field.support[k], side));
  [...free, ...air].sort((a, b) => a - b).forEach(k => {
    const b = field.support[k], K = UD.indirect.kinds[b.kind];
    if (b.mission) return;
    const aim = fireAim(us, side, field, known, b, K);
    if (!aim) return;
    const run = K.air ? airRun(us, side, b, K, aim, [table, field]) : null;
    b.mission = { hex: aim[1], wait: K.delay, repeat: false, ...run };
    out.push({ unit: null, act: "fire", battery: k, target: aim[0], hex: aim[1], ...(run ? { attack: run.attack } : {}), ...(K.air && facSees(us, field, b, aim[1]) ? { fac: true } : {}) });
  });
  return out;
}
function callCreep(us, side, field, [known, orders], free){   // attacking: a creeping barrage on the enemy nearest a unit moving or charging on it, lifting along that unit's facing (as commander._call_creep)
  const sup = field?.support || [], CR = UD.commander.creep;
  if (sup.some(b => b.side === side && b.mission?.creep)) return [];
  const ours = us.filter(u => u.side === side && u.men > 0 && u.state !== "fled"), KI = k => UD.indirect.kinds[sup[k].kind];
  const pairs = orders.filter(o => (o.act === "move" || o.act === "charge") && o.target !== null && o.target !== undefined && String(o.target) in known)
    .map(o => [hdist(us[o.unit].pos, knownAt(us, o.target, known).pos), o.unit, o.target]).sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2]);
  for (const [dist, i, t] of pairs){
    const h = dist <= CR.near ? marksOf(us[t]).find(x => spotted(us, field, side, x)) : undefined;
    if (!h) continue;
    const guns = free.filter(k => !sup[k].mission && inReach(sup[k], h) && !tooNear(ours, h, KI(k).radius + KI(k).scatter))
      .map(k => [KI(k).delay, k]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    if (guns.length){
      const k = guns[0][1];
      sup[k].mission = { hex: [...h], wait: guns[0][0], repeat: true, creep: { step: CR.step, dir: us[i].facing, every: CR.every, lines: CR.lines } };
      return [{ unit: null, act: "creep", battery: k, target: t, hex: [...h], for: i }];
    }
  }
  return [];
}
function airRun(us, side, b, K, [j, h], [table, field]){   // a strafing run or napalm strip along a wide enemy front, its line clear of its own men by the scatter (cut where a controller sees the aim); or null (as commander._air_run)
  const R = UD.indirect.air.runs || {}, rows = footprint(us[j]), front = rows.length ? rows[0].length : 0;
  const war = table ? FD.tables[table]?.battle ?? null : null, dirn = (us[j].facing + 5) % 6;
  const ours = us.filter(u => u.side === side && u.men > 0 && u.state !== "fled");
  for (const mode of ["napalm", "strafe"]){
    const r = R[mode];
    if (!r?.kinds.includes(b.kind) || front < r.length || (r.wars && !r.wars.includes(war))) continue;
    if (!runLine(h, dirn, mode).some(x => tooNear(ours, x, airScatter(us, field, b, K, h)))) return { attack: mode, dir: dirn };
  }
  return null;
}
function callIllum(us, side, field, [known, exchange], free){   // in the dark: illumination over the lost enemy nearest its units, by the free battery with illumination that lands soonest (as commander._call_illum)
  const L = lightOf(field), ours = us.filter(u => u.side === side && u.men > 0 && u.state !== "fled");
  if ((L?.sight ?? null) === null || !ours.length) return [];
  const lost = knownFoes(known).filter(([, m]) => m.ex !== (exchange ?? 0) && !lit(field, m.pos))
    .map(([k, m]) => [Math.min(...ours.map(o => hdist(o.pos, m.pos))), Number(k)]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
  const sup = field?.support || [];
  const coming = sup.filter(b => b.side === side && b.mission?.illum).map(b => [b.mission.hex, UD.indirect.kinds[b.kind].illum || 0]);
  for (const [, j] of lost){
    const h = [...known[String(j)].pos];
    if (coming.some(([c, r]) => hdist(h, c) <= r)) continue;
    const guns = free.filter(k => !sup[k].mission && UD.indirect.kinds[sup[k].kind].illum && inReach(sup[k], h))
      .map(k => [UD.indirect.kinds[sup[k].kind].delay, k]).sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    if (guns.length){
      const k = guns[0][1];
      sup[k].mission = { hex: h, wait: UD.indirect.kinds[sup[k].kind].delay, repeat: false, illum: true };
      return [{ unit: null, act: "illum", battery: k, target: j, hex: h }];
    }
  }
  return [];
}
function aiCounter(field, side, free){            // one free battery with the best counter % fires on the reachable located enemy battery with most tubes served (as commander._call_counter)
  const sup = field?.support || [];
  const marks = sup.map((x, j) => j).filter(j => sup[j].side !== side && sup[j].located && (sup[j].tubes || 0) > 0);
  let best = null;
  for (const k of free){
    const b = sup[k], K = UD.indirect.kinds[b.kind];
    if (b.mission || !K.counter) continue;
    const aims = marks.filter(j => sup[j].place === undefined || sup[j].place === null || inReach(b, sup[j].place));
    if (!aims.length || (best && K.counter <= best[0])) continue;
    best = [K.counter, k, aims.reduce((a, j) => (servedTubes(sup[j]) > servedTubes(sup[a]) ? j : a), aims[0])];
  }
  if (!best) return [];
  const [, k, j] = best;
  sup[k].mission = { battery: j, wait: UD.indirect.kinds[sup[k].kind].delay, repeat: false };
  return [{ unit: null, act: "counter", battery: k, on: j }];
}
function shiftedPlace(field, place, away){           // displace_shift hexes along the map edge nearest a placed battery, away from the battery firing on it, else toward more room (as commander.shifted)
  const [cols, rows] = fieldSize(field), gaps = [place[0], cols - 1 - place[0], place[1], rows - 1 - place[1]];
  const axis = gaps.indexOf(Math.min(...gaps)) < 2 ? 1 : 0, n = axis ? rows : cols, at = place[axis], step = UD.indirect.displace_shift;
  let way;
  if (away !== null && away[axis] !== at) way = away[axis] > at ? -1 : 1;
  else way = at <= (n - 1) / 2 ? 1 : -1;
  let to = Math.min(n - 1, Math.max(0, at + way * step));
  if (to === at) to = Math.min(n - 1, Math.max(0, at - way * step));
  const out = [...place];
  out[axis] = to;
  return out;
}
function displaceAi(field, side){                  // its located batteries an enemy counter-battery mission is aimed at displace (as commander._displace)
  const sup = field?.support || [], out = [];
  sup.forEach((b, k) => {
    const n = UD.indirect.kinds[b.kind].displace || 0;
    if (b.side !== side || !b.located || b.displacing || (b.tubes || 0) <= 0 || !n) return;
    const by = sup.findIndex(x => x.side !== side && x.mission?.battery === k);
    if (by < 0) return;
    Object.assign(b, { displacing: n, mission: null });
    if (b.place !== undefined && b.place !== null) b.to = shiftedPlace(field, b.place, sup[by].place ?? null);
    out.push({ unit: null, act: "displace", battery: k, by, ...(b.to ? { to: b.to } : {}) });
  });
  return out;
}
const freeAir = (field, b, side) => !!UD.indirect.kinds[b.kind].air && b.side === side && !b.mission && (b.rounds || 0) > 0 && (b.tubes || 0) > 0 && !grounded(field, b);   // its aircraft it can send: not grounded (as commander._free_air)
function freeBattery(b, side){                     // one of its off-map batteries it can call: not tanks or aircraft, no mission, rounds and tubes, not displacing
  const K = UD.indirect.kinds[b.kind];
  return !(b.side !== side || b.mission || K.direct || K.air || b.displacing || (b.rounds || 0) <= 0 || servedTubes(b) <= 0);
}
function callSmoke(us, side, field, known, free){   // smoke on the nearest known enemy shooting at a unit that cannot shoot back, by the free battery that lands soonest (as commander._call_smoke)
  const S = UD.indirect.smoke, wind = field?.weather?.wind || "calm", sight = lightOf(field)?.sight ?? null;
  if (!free.length || (S.lasts[wind] ?? 0) <= 1 || (sight !== null && sight < FD.weather.light.flash)) return [];
  const sm = field?.smoke || {};
  for (const [, j] of shootingAt(us, side, known)){
    const h = marksOf(knownAt(us, j, known)).find(x => spotted(us, field, side, x) && !(hk(x) in sm));
    if (!h) continue;
    const reach = free.filter(k => inReach(field.support[k], h)).map(k => [UD.indirect.kinds[field.support[k].kind].delay, k]);
    if (!reach.length) continue;
    reach.sort((a, b) => a[0] - b[0] || a[1] - b[1]);
    const k = reach[0][1], b = field.support[k];
    b.mission = { hex: [...h], wait: UD.indirect.kinds[b.kind].delay, repeat: false, smoke: true };
    return [{ unit: null, act: "smoke", battery: k, target: j, hex: [...h] }];
  }
  return [];
}
function shootingAt(us, side, known){              // [[distance, enemy index]], nearest first: known enemies whose missiles reach a standing unit of the side that cannot shoot back
  const seen = new Map();
  for (const u of us){
    if (u.side !== side || ROUTED.has(u.state) || u.men <= 0) continue;
    for (const [k, m] of knownFoes(known)){
      const e = us[Number(k)], dist = hdist(m.pos, u.pos);
      const hits = "range" in FD.weapons[e.weapon] && fieldRange(e.weapon, dist) !== null;
      const back = "range" in FD.weapons[u.weapon] && fieldRange(u.weapon, dist) !== null;
      if (hits && !back) seen.set(`${dist},${k}`, [dist, Number(k)]);
    }
  }
  return [...seen.values()].sort((a, b) => a[0] - b[0] || a[1] - b[1]);
}
function fireAim(us, side, field, known, b, K){    // [enemy index, hex] to fire on, or null: none of its men within burst and scatter (airScatter); aircraft prefer an aim a controller sees (as commander._fire_aim)
  const ours = us.filter(u => u.side === side && u.men > 0 && u.state !== "fled");
  let best = null;
  us.forEach((e, j) => {
    if (e.side === side || !(String(j) in known) || !ours.length) return;
    const h = marksOf(e).find(x => spotted(us, field, side, x));
    if (!h || !inReach(b, h) || tooNear(ours, h, K.radius + airScatter(us, field, b, K, h))) return;
    const u = ours.reduce((a, o) => (hdist(o.pos, e.pos) < hdist(a.pos, e.pos) ? o : a), ours[0]);
    const talked = !!K.air && facSees(us, field, b, h), sc = threatScore(u, e, e);
    if (!best || (talked && !best[0]) || (talked === best[0] && sc > best[1])) best = [talked, sc, [j, [...h]]];
  });
  return best ? best[2] : null;
}
const airScatter = (us, field, b, K, h) => (K.air && field && facSees(us, field, b, h) ? Math.floor(K.scatter / UD.indirect.air.fac.scatter) : K.scatter);   // aircraft scatter at h: cut where a controller of their side sees it (as commander._air_scatter)
const marksOf = e => { const rows = footprint(e); return [e.pos, ...(rows.length ? [rows[0][0], rows[0].at(-1)] : [])] };   // its middle hex, then either end of its front row
const tooNear = (ours, h, r) => ours.some(u => footprint(u).flat().some(x => hdist(x, h) <= r));   // any of the side's hexes within r of h
function sightings(us, side, field, exchange, memory){   // {index: {pos, facing, ex}}: enemies seen now where they stand; others where last seen, for remember exchanges
  const ex = exchange ?? 0;
  us.forEach((e, j) => {
    const k = String(j);
    if (e.side === side) return;
    if (ROUTED.has(e.state) || e.men <= 0) delete memory[k];
    else if (seenBy(us, side, field, e)) memory[k] = { pos: [...e.pos], facing: e.facing, ex };
    else if (k in memory && ex - memory[k].ex > UD.commander.remember) delete memory[k];
  });
  return memory;
}
const seenBy = (us, side, field, e) => marksOf(e).some(h => spotted(us, field, side, h));   // a unit of side sees enemy e: its middle hex or either end of its front row
const tractor = u => !!vehicleKind(u)?.tows;      // gun tractors: not ordered as other units (towing: moveGuns)
function commandable(us, i, exchange){            // standing, not a battery, anti-tank guns or gun tractors, not in contact, not just come on
  const u = us[i];
  if (ROUTED.has(u.state) || u.men <= 0 || isBattery(u) || isAtGun(u) || tractor(u)) return false;
  if (exchange !== null && u.arrived === exchange) return false;
  return !inContact(us, occupancy(us), i);
}
function spotter(us, i, o, [size, field, stance, known]){   // attacking, an air controller that would stand or turn moves up to see a target for its side's aircraft, when they can fly and no controller sees a known enemy (as commander._spotter)
  const u = us[i];
  if (stance !== "attack" || !u.fac || (o && o.act !== "turn")) return null;
  if (u.prone || u.reserve || busyDigging(u)) return null;
  if (!(field?.support || []).some(b => freeAir(field, b, u.side))) return null;
  if (ownFight(us, i, field)) return null;
  const ranked = rankedFoes(us, i, known, field);
  if (!ranked.length || ranked.some(([, p]) => facSees(us, field, u, p))) return null;
  return toSee(us, i, ranked, [size, field]);
}
function rankedFoes(us, i, known, field){         // the enemies its side knows of, best target first, with where each was last seen: [[index, hex]] (as commander._ranked_foes)
  const u = us[i], out = [];
  us.forEach((e, j) => {
    if (e.side === u.side || ROUTED.has(e.state) || e.men <= 0 || !(String(j) in (known || {}))) return;
    const seen = knownAt(us, j, known);
    out.push([-(threatScore(u, e, seen) + guards(seen, field)), j, [...seen.pos]]);
  });
  return out.sort((a, b) => a[0] - b[0] || a[1] - b[1]).map(([, j, p]) => [j, p]);
}
function ownFight(us, i, field){                  // the controller has a fight of its own: an enemy touching it, one it sees within its weapon's reach, or under fire (pinned, or it lost men last exchange) (as commander._own_fight)
  const u = us[i];
  if (u.pinned || u.hit || inContact(us, occupancy(us), i)) return true;
  if (!("range" in FD.weapons[u.weapon])) return false;
  return us.some(e => e.side !== u.side && !ROUTED.has(e.state) && e.men > 0 && fieldRange(u.weapon, hdist(u.pos, e.pos)) !== null
    && sees(field, u, e.pos, sightHexes(field, e.pos, seerOf(u))));
}
function toSee(us, i, ranked, [size, field]){     // the controller's spot within commander.spot.moves moves (not its own hex, no known mines on the way) from which, facing it, it sees a known enemy, touching none; a spot out of known enemies' reach preferred within spot.safe moves more; of equals the best target, then lowest row and column; beyond this move, a move toward it (as commander._to_see)
  const u = us[i], C = UD.commander, allow = allowance(u), occ = occupancy(us), foes = new Set(Object.keys(occ).filter(k => us[occ[k]].side !== u.side));
  let tries = C.tries;
  const cands = spotCands(us, i, ranked, [size, field, foes]);
  if (!cands.length) return null;
  const safe = cands.filter(x => x[0] <= cands[0][0] + C.spot.safe * allow && safeSpot(us, [x[3], x[2]], ranked));
  for (const [c, , row, col, j, f] of safe.length ? safe : cands){
    if (tries <= 0) return null;
    if (c <= allow){
      tries -= 1;
      const m = moveUnit(us, i, [col, row], f, size, field);
      if (m.ok && !m.charge) return { act: "spot", target: j, pos: [col, row], facing: f, cost: m.cost };
      continue;
    }
    const r = stepTo(us, i, [[col, row], j, ranked], [size, field, foes, tries]);
    tries = r[1];
    if (r[0]) return r[0];
  }
  return null;
}
function spotCands(us, i, ranked, [size, field, foes]){   // [movement, rank, row, col, enemy, facing], cheapest first, for each hex within spot.moves moves (not its own, no known mines on the way) from which it sees a known enemy (as commander._spot_cands)
  const u = us[i], out = [];
  for (const [h, c] of reachable(us, i, size, allowance(u) * UD.commander.spot.moves, field).values()){
    if ((h[0] === u.pos[0] && h[1] === u.pos[1]) || mined(field, u.pos, h, u.side)) continue;
    const seen = seesFrom(field, { ...u, pos: [...h] }, ranked, foes);
    if (seen) out.push([c, seen[0], h[1], h[0], seen[1], seen[2]]);
  }
  return out.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3] || a[4] - b[4] || a[5] - b[5]);
}
const safeSpot = (us, h, ranked) => !ranked.some(([j, p]) => "range" in FD.weapons[us[j].weapon] && fieldRange(us[j].weapon, hdist(p, h)) !== null);   // no known enemy, where last seen, reaches h with its missile weapon (as commander._safe_spot)
function stepTo(us, i, [spot, j, ranked], [size, field, foes, tries]){   // a move toward a spot beyond this move: the hex in its allowance nearest the spot, then cheapest, lowest row and column, nearer than it stands, touching no enemy, facing the enemy it goes to see: [order or null, tries left] (as commander._step_to)
  const u = us[i], p = ranked.find(([k]) => k === j)[1], now = hdist(u.pos, spot);
  const steps = [...reachable(us, i, size, allowance(u), field).values()].filter(([h]) => hdist(h, spot) < now && !mined(field, u.pos, h, u.side))
    .map(([h, c]) => [hdist(h, spot), c, h[1], h[0]]).sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3]);
  for (const [, , row, col] of steps){
    const f = bearing([col, row], p);
    if (touches({ ...u, pos: [col, row], facing: f }, foes)) continue;
    if (tries <= 0) break;
    tries -= 1;
    const m = moveUnit(us, i, [col, row], f, size, field);
    if (m.ok && !m.charge) return [{ act: "spot", target: j, pos: [col, row], facing: f, cost: m.cost, toward: [...spot] }, tries];
  }
  return [null, tries];
}
function seesFrom(field, u, ranked, foes){        // [rank, enemy, facing] of the best-ranked enemy u, placed so, would see facing it without touching the enemy, or null (as commander._sees_from)
  for (let r = 0; r < ranked.length; r++){
    const [j, p] = ranked[r], there = { ...u, facing: bearing(u.pos, p) };
    if (!touches(there, foes) && sees(field, there, p, sightHexes(field, p, seerOf(there)))) return [r, j, there.facing];
  }
  return null;
}
const unsteady = (us, i, t) => (!us[i].prone && !us[i].vehicle && underFire(us, i) ? { act: "ground", target: t } : null);   // a shaken unit holds, going to ground under missile fire (not vehicles) (as commander._unsteady)
function unitOrder(us, i, ctx, roll){            // one unit's order, or null (it holds); ctx [size, field, stance, known, exchange]
  const u = us[i], C = UD.commander, obj = objectiveOf(ctx[1]), t = aiTarget(us, i, ctx[3], ctx[1]);
  if (u.state !== "steady") return unsteady(us, i, t);
  if (busyDigging(u) || u.resupplying) return null;
  const ammo = ammoOrder(us, i, t, ctx);
  if (ammo) return ammo;
  if (u.reserve) return reserveOrder(us, i, t, ctx);
  const sap = sapperOrder(us, i, t, ctx);
  if (sap) return sap;
  const route = routeOrder(us, i, ctx);
  if (route) return route;
  if ((obj !== null || ctx[2] === "hold") && digs(us, i, ctx)) return { act: "dig", target: t };
  if (t === null && obj === null) return search(us, i, ctx);
  if (roll <= (C.hesitate[u.quality] ?? 0)) return { act: "hesitate", target: t, roll };
  const o = obj === null ? bestOrder(us, i, t, ctx) : forObjective(us, i, t, ctx);
  return t === null ? o : lastSeen(o, ctx[3], t, ctx[4]);
}
function routeOrder(us, i, ctx){                   // a unit on its route (via: waypoints from the battlefield's account) goes on to the next, dropping each it reaches (within commander.route.reach hexes); it turns aside only for an enemy in contact or right across its way; with none left, or no way on, null: it is ordered as any other (as commander._route_order)
  const u = us[i];
  if (!u.via) return null;
  const via = u.via.slice();
  while (via.length && hdist(u.pos, via[0]) <= UD.commander.route.reach) via.shift();
  if (via.length) u.via = via;
  else delete u.via;
  if (!via.length || routeBlocked(us, i, via[0], ctx[3])) return null;
  const [size, field, stance, known, exchange] = ctx;
  return toward(us, i, null, [size, { ...field, objective: via[0], objective_radius: null }, stance, known, exchange], "advance");
}
function routeBlocked(us, i, w, known){            // in contact, or an enemy it knows of within its move of the straight way to waypoint w (within a hex of it) (as commander._route_blocked)
  const u = us[i];
  if (inContact(us, occupancy(us), i)) return true;
  const way = ray(u.pos, w, hdist(u.pos, w)).slice(1, allowance(u) + 1);
  return Object.entries(known || {}).some(([k, m]) => /^\d+$/.test(k) && way.some(h => hdist(h, m.pos) <= 1));
}
function search(us, i, [size, field, stance, known, exchange]){   // attacking, with no objective and no enemy it knows of: a move toward the last hex on the map straight ahead along its facing; holding, null (as commander._search)
  if (stance !== "attack") return null;
  const u = us[i], fs = fieldSize(field);
  let ahead = [...u.pos];
  for (let n = 1; ; n++){
    const h = step(u.pos, u.facing, n);
    if (!onMap(h, fs)) break;
    ahead = [...h];
  }
  if (ahead[0] === u.pos[0] && ahead[1] === u.pos[1]) return null;
  return toward(us, i, null, [size, { ...field, objective: ahead, objective_radius: null }, stance, known, exchange], "search");
}
function ammoOrder(us, i, t, [size, field, stance, known, exchange]){   // low or out with a supply source in reach: resupply (out at once; low with no known enemy in its range); out with none, attacking: fall back toward its supply edge (as commander._ammo_order)
  const u = us[i], state = ammoState(u);
  if (state !== "low" && state !== "out") return null;
  if (supplyNear(us, i, field) !== null){
    const near = knownFoes(known || {}).some(([, m]) => fieldRange(u.weapon, hdist(u.pos, m.pos)) !== null);
    return state === "out" || !near ? { act: "resupply", target: t } : null;
  }
  const edge = supplyEdge(us, u.side);
  if (state !== "out" || stance !== "attack" || edge === null) return null;
  const [cols, rows] = fieldSize(field), goal = { N: [u.pos[0], 0], S: [u.pos[0], rows - 1], W: [0, u.pos[1]], E: [cols - 1, u.pos[1]] }[edge];
  return toward(us, i, t, [size, { ...(field || {}), objective: goal, objective_radius: null }, stance, known, exchange], "fall_back");
}
function reserveOrder(us, i, t, ctx){             // a reserve held back digs in where it waits when safe, else stays facing its target (as commander._reserve_order)
  const u = us[i];
  if (canDig(u) && !dugHere(u) && safeToDig(us, i, ctx[3])) return { act: "dig", target: t };
  return t === null ? null : stayOrder(us, i, t, u.facing, "range" in FD.weapons[u.weapon]);
}
function digs(us, i, [, field, , known]){          // a unit digs in where it stands: at the objective (within its radius) or holding with none; it can, is not dug in there, and is safe (as commander._digs)
  const u = us[i];
  if (!canDig(u) || dugHere(u)) return false;
  const obj = objectiveOf(field);
  if (obj !== null && offObjective(u, obj) > objectiveRadii(field)[0]) return false;
  return safeToDig(us, i, known);
}
function safeToDig(us, i, known){                 // not under fire, and no enemy it knows of within its weapon's range (as commander._safe_to_dig)
  if (underFire(us, i)) return false;
  const u = us[i];
  return !knownFoes(known || {}).some(([, m]) => fieldRange(u.weapon, hdist(u.pos, m.pos)) !== null);
}
const foesMine = (m, side) => !!m && knownMine(m) && m.side !== side;   // a minefield hex it knows of that its own sappers did not lay (as commander._foes_mine)
function sapperOrder(us, i, t, ctx){              // sappers set to work: attacking, lift known mines ahead in their way (closing up to the belt first); holding or at the objective, lay (as commander._sapper_order)
  const u = us[i], field = ctx[1];
  if (!canSap(u)) return null;
  const row = aheadRow(field, u), mines = field?.mines || {};
  let goal = null;
  if (ctx[2] === "attack") goal = t === null ? objectiveOf(field) : knownAt(us, t, ctx[3]).pos;
  if (goal !== null && row.some(x => foesMine(mines[hk(x)], u.side)) && mined(field, u.pos, goal, u.side)) return { act: "lift", target: t };
  const close = goal !== null && foesOnWay(field, u.pos, goal, u.side) ? closeUp(us, i, [t, goal], ctx) : null;
  if (close) return close;
  return lays(us, i, ctx, row) ? { act: "lay", target: t, kind: mineKind(us, ctx[3]) } : null;
}
function foesOnWay(field, a, h, side){            // known enemy minefield hexes on the straight way from a to h (as commander._foes_on_way)
  const mines = field?.mines || {};
  return !(a[0] === h[0] && a[1] === h[1]) && ray([...a], [...h], hdist(a, h)).slice(1).some(x => foesMine(mines[hk(x)], side));
}
function closeUp(us, i, [t, goal], [size, field]){   // sappers close up along the straight way to the known belt, as far as they legally can without a hex in enemy mines, stopping once the row ahead is mined (as commander._close_up)
  const u = us[i], mines = field?.mines || {}, f = bearing(u.pos, goal), inMines = xs => xs.some(x => foesMine(mines[hk(x)], u.side));
  let best = null;
  for (const p of ray([...u.pos], [...goal], hdist(u.pos, goal)).slice(1)){
    const there = { ...u, pos: [...p], facing: f };
    if (inMines(footprint(there).flat())) break;
    const m = moveUnit(us, i, [...p], f, size, field);
    if (!m.ok || m.charge) break;
    best = [[...p], m.cost];
    if (inMines(aheadRow(field, there))) break;
  }
  return best === null ? null : { act: "close_up", target: t, pos: best[0], facing: f, cost: best[1] };
}
function lays(us, i, [, field, stance, known], row){   // holding (or at the objective), no known enemy within commander.sappers.clear_of, a free hex ahead (as commander._lays)
  const u = us[i], obj = objectiveOf(field);
  if (stance !== "hold" && (obj === null || offObjective(u, obj) > objectiveRadii(field)[0])) return false;
  const near = UD.commander.sappers.clear_of;
  if (knownFoes(known || {}).some(([, m]) => hdist(u.pos, m.pos) <= near)) return false;
  const mines = field?.mines || {}, occ = occupancy(us);
  return row.some(x => !(hk(x) in mines) && !(hk(x) in occ));
}
const mineKind = (us, known) => (knownFoes(known || {}).some(([k]) => us[+k].vehicle) ? "mixed" : "ap");   // mixed if an enemy it knows of has vehicles (as commander._mine_kind)
const objectiveOf = field => (field?.objective ? [...field.objective] : null);   // the hex the GM marked as the commander's objective, or null
function forObjective(us, i, t, ctx){              // attacking: at the objective it holds, with no enemy or nothing better it advances; holding: too far out it falls back unless it can charge
  const off = offObjective(us[i], objectiveOf(ctx[1]));
  if (t === null) return noTarget(us, i, ctx, off);
  if (ctx[2] === "attack") return attackObjective(us, i, t, ctx, off);
  const o = bestOrder(us, i, t, ctx);
  if (off > objectiveRadii(ctx[1])[1] && o?.act !== "charge") return toward(us, i, t, ctx, "fall_back") || o;
  return o;
}
function noTarget(us, i, ctx, off){                // no enemy to go for: attacking, it advances unless at the objective; holding, it falls back if too far out
  const [radius, hold] = objectiveRadii(ctx[1]), attack = ctx[2] === "attack";
  if (off <= (attack ? radius : hold)) return null;
  return toward(us, i, null, ctx, attack ? "advance" : "fall_back");
}
function attackObjective(us, i, t, ctx, off){      // attacking with a target: at the objective it holds; else its best order, or an advance when that is only to stand or turn and the target is not guarding the objective
  if (off <= objectiveRadii(ctx[1])[0]) return bestOrder(us, i, t, [ctx[0], ctx[1], "hold", ctx[3], ctx[4]]);
  const o = bestOrder(us, i, t, ctx);
  if ((o !== null && o.act !== "turn") || guards(knownAt(us, t, ctx[3]), ctx[1])) return o;
  return toward(us, i, t, ctx, "advance") || o;
}
function toward(us, i, t, [size, field, , known], act){   // a move toward the objective within its allowance (its turn included), touching no enemy, to the hex it likes best; or null
  const u = us[i];
  if (u.lost || u.immobile || u.emplaced) return null;
  const obj = objectiveOf(field), tu = t === null ? null : knownAt(us, t, known);
  const free = u.prone ? { ...u, prone: false } : u, base = us.map((x, k) => (k === i ? free : x));
  const occ = occupancy(base), foes = new Set(Object.keys(occ).filter(k => base[occ[k]].side !== u.side)), allow = allowance(free);
  let tries = UD.commander.tries;
  for (const [c, h] of towardHexes(base, i, tu, [size, field])){
    const f = facingFrom(h, tu, obj, u.facing);
    const fs = facingsFor(f, u.facing).filter(g => c + Math.min(mod6(g - u.facing), mod6(u.facing - g)) * turnCost(free) <= allow && !touches({ ...u, pos: h, facing: g }, foes));
    if (!fs.length) continue;
    if (tries === 0) return null;
    tries -= 1;
    const [m, g] = legalFacing(base, i, [h, fs[0], c, false], [size, field, foes]);
    if (m.ok) return { act, target: t, pos: h, facing: g, cost: m.cost, ...(u.prone ? { up: true } : {}) };
  }
  return null;
}
function towardHexes(base, i, tu, [size, field]){   // [[movement, hex]] it can reach nearer the objective, best first (as commander._toward_hexes)
  const u = base[i], C = UD.commander, obj = objectiveOf(field), q = u.quality, now = hdist(u.pos, obj);
  const cands = [...reachable(base, i, size, allowance(u), field).values()].filter(([h]) => hdist(h, obj) < now).map(([h, c]) => {
    const cover = tu === null ? 0 : (C.cover[q] ?? 0) * coverAt(field, tu.pos, h);
    return [C.closing * hdist(h, obj) + c + (C.mines[q] ?? 0) * mined(field, u.pos, h, u.side) - cover, c, aside(h, obj), h[1], h[0]];
  });
  cands.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3] || a[4] - b[4]);
  return cands.map(([, c, , row, col]) => [c, [col, row]]);
}
function facingFrom(h, tu, obj, facing){           // toward the target if any, else the objective (as it was, at the objective)
  if (tu !== null && (tu.pos[0] !== h[0] || tu.pos[1] !== h[1])) return bearing(h, tu.pos);
  return h[0] === obj[0] && h[1] === obj[1] ? facing : bearing(h, obj);
}
function lastSeen(o, known, t, exchange){        // the order, with the exchange its target was last seen in (last) if not this one
  const last = known?.[String(t)]?.ex;
  return o && last !== undefined && last !== (exchange ?? 0) ? { ...o, last } : o;
}
function aiTarget(us, i, known = null, field = null){   // the enemy unit it goes for among those its side knows of (null: every one standing), by threatScore (the first of equals), or null; with an objective, more for one guarding it
  const u = us[i];
  let best = null;
  us.forEach((e, j) => {
    if (e.side === u.side || ROUTED.has(e.state) || e.men <= 0 || (known !== null && !(String(j) in known))) return;
    const seen = knownAt(us, j, known), sc = threatScore(u, e, seen) + guards(seen, field);
    if (best === null || sc > best[0]) best = [sc, j];
  });
  return best ? best[1] : null;
}
function guards(seen, field){                      // commander.objective.bonus for an enemy within the objective's guard of it, else 0
  const obj = objectiveOf(field);
  if (obj === null || hdist(seen.pos, obj) > objectiveRadii(field)[2]) return 0;
  return UD.commander.objective.bonus;
}
function knownAt(us, j, known){                   // enemy unit j where its side last saw it (as it is if seen now)
  const m = known?.[String(j)];
  return m ? { ...us[j], pos: m.pos, facing: m.facing } : us[j];
}
function threatScore(u, e, seen){                 // how much u wants enemy e: closing off a hex away; by its quality's sense, % of e down, e shaken, e a danger to it
  const C = UD.commander, dist = hdist(u.pos, seen.pos), sense = C.sense[u.quality] ?? 0;
  if (!sense) return -C.closing * dist;
  const down = Math.floor((e.down || 0) * 100 / Math.max(1, e.start || e.men));
  const shooter = "range" in FD.weapons[u.weapon], theirs = "range" in FD.weapons[e.weapon];
  const danger = (!shooter && theirs) || (shooter && !theirs && dist <= allowance(e) * UD.charge_move);
  const weak = C.hurt * down + (e.state === "shaken" ? C.shaken : 0) + (danger ? C.threat : 0);
  return sense * weak - C.closing * dist;
}
function underFire(us, i){                         // an enemy unit's missile weapon reaches unit i
  const u = us[i];
  return us.some(e => e.side !== u.side && !ROUTED.has(e.state) && e.men > 0 && "range" in FD.weapons[e.weapon] && fieldRange(e.weapon, hdist(e.pos, u.pos)) !== null);
}
function storming(u, t, field, stance){           // attacking, armed for storming (black powder with the bayonet), its target holding works: it closes and charges (as commander.storming)
  return stance === "attack" && UD.commander.storm.includes(u.weapon) && holdsWorks(field, u.pos, t);
}
function support(us, i){                          // men times attack % of the steady friendly units (not guns or vehicles) touching unit i: they go in with it (as commander.support)
  const u = us[i], near = new Set(footprint(u).flat().flatMap(h => [0, 1, 2, 3, 4, 5].map(n => hk(step(h, n)))));
  return us.reduce((a, x, k) => (k !== i && x.side === u.side && x.state === "steady" && !isBattery(x) && !x.vehicle && footprint(x).flat().some(h => near.has(hk(h))) ? a + x.men * quality(x.quality).attack : a), 0);
}
function mayCharge(u, t, stance = "attack", storm = false, backing = 0){   // men without missiles (or storming works), steady, with the odds its quality wants in its stance, counting the friends touching it
  if (("range" in FD.weapons[u.weapon] && !storm) || u.state !== "steady") return false;
  const mine = u.men * quality(u.quality).attack + backing, theirs = t.men * quality(t.quality).attack;
  return 100 * mine >= (UD.commander.charge_odds[stance][u.quality] ?? 100) * theirs;
}
function turnToward(base, i, f, [size, field]){    // the facing nearest f, turning the shorter way, it can reach where it stands this move, or null (as commander._turn_toward)
  const u = base[i], right = mod6(f - u.facing), sign = right <= 3 ? 1 : -1;
  for (let n = Math.min(right, 6 - right); n > 0; n--){
    const g = mod6(u.facing + sign * n);
    if (moveUnit(base, i, u.pos, g, size, field).ok) return g;
  }
  return right === 0 && moveUnit(base, i, u.pos, f, size, field).ok ? f : null;
}
function bestOrder(us, i, t, [size, field, stance, known]){   // the best-scoring hex it can legally reach, facing the target (where last seen); holding, it only charges, else stays
  const u = us[i], tu = knownAt(us, t, known), hold = stance === "hold";
  const free = u.prone ? { ...u, prone: false } : u, base = us.map((x, k) => (k === i ? free : x));
  const storm = storming(u, tu, field, stance);
  const shooter = "range" in FD.weapons[u.weapon] && !storm, charge = mayCharge(u, tu, stance, storm, support(us, i));
  const best = firstMove(base, i, tu, [size, field], [charge, hold, shooter, storm]);
  if (best === null){
    const f = keepFront(u, bearing(u.pos, tu.pos));
    const g = turnToward(base, i, f, [size, field]);   // no hex it likes is in reach: it turns where it stands, as far toward the target as it can
    return g === null ? null : stayOrder(us, i, t, g, shooter);
  }
  const [h, f, m] = best;
  if (h[0] === u.pos[0] && h[1] === u.pos[1]) return stayOrder(us, i, t, f, shooter);
  return { act: m.charge ? "charge" : "move", target: t, pos: h, facing: f, cost: m.cost, ...(u.prone ? { up: true } : {}), ...(m.through?.length ? { through: m.through } : {}) };
}
function firstMove(base, i, tu, [size, field], [charge, hold, shooter, storm]){   // [hex, facing, move] for the best-scoring hex it will move to, or null
  const u = base[i];
  if (hold && !charge) return null;
  const allow = allowance(u), occ = occupancy(base), stuck = !!(u.lost || u.immobile || u.emplaced);
  let tries = UD.commander.tries;
  const foes = new Set(Object.keys(occ).filter(k => base[occ[k]].side !== u.side));
  const reach = aiReach(base, i, [size, allow * (charge ? UD.charge_move : 1), field], charge && u.state === "steady");
  const cands = [...reach.values()].map(([h, c, via]) => [-aiScore(field, u, tu, h, c, shooter, storm), c, aside(h, tu.pos), h[1], h[0], via]);
  cands.sort((a, b) => a[0] - b[0] || a[1] - b[1] || a[2] - b[2] || a[3] - b[3] || a[4] - b[4]);
  for (const [, c, , row, col, via] of cands){
    const h = [col, row], f = keepFront(u, bearing(h, tu.pos)), touch = touches({ ...u, pos: h, facing: f }, foes);
    if (skipsHex(touch, [charge, hold, via], c > allow, stuck && (h[0] !== u.pos[0] || h[1] !== u.pos[1]))) continue;
    if (tries === 0) return null;
    tries -= 1;
    const [m, g] = legalFacing(base, i, [h, f, c, touch], [size, field, foes]);
    if (!rejects(m, charge, hold)) return [h, g, passing(base, i, h, m, via)];
  }
  return null;
}
const passing = (base, i, h, m, via) => (via ? { ...m, through: passedThrough(base, i, h) } : m);   // the legal move, with the friends it passes through if it came through them (as commander._passing)
function skipsHex(touch, [charge, hold, via], far, stuck){   // a hex it will not try (as commander._skips)
  if (stuck || (via && !touch)) return true;
  return touch ? !charge : hold || far;
}
function aiReach(base, i, [size, limit, field], through){   // Map hk -> [hex, least movement, through friends]: round its own side's units, and (a steady unit that may charge) only through them (as commander._reach)
  const out = new Map([...reachable(base, i, size, limit, field).entries()].map(([k, [h, c]]) => [k, [h, c, false]]));
  if (through) for (const [k, [h, c]] of reachable(base, i, size, limit, field, true)) if (!out.has(k)) out.set(k, [h, c, true]);
  return out;
}
const keepFront = (u, b) => (arc(u.facing, b) === "front" ? u.facing : b);   // the facing to take toward direction b: its own if b is already in its front arc, else b (as commander.keep_front)
function facingsFor(f, now){                       // f, then a point either side, then two, then the facing it has now (each once) (as commander._facings)
  const out = [];
  for (const g of [f, f + 1, f - 1, f + 2, f - 2, now]) if (!out.includes(mod6(g))) out.push(mod6(g));
  return out;
}
function legalFacing(base, i, [h, f, c, touch], [size, field, foes]){   // [move, facing]: legalMove facing f; if it may not move there so (no room, or the turn too dear), the nearest facing that it may, touching (or not) as before (as commander._legal_facing)
  const m = legalMove(base, i, [h, f, c, touch], [size, field]);
  if (m.ok) return [m, f];
  const u = base[i];
  for (const g of facingsFor(f, u.facing).slice(1)){
    if (touches({ ...u, pos: h, facing: g }, foes) !== touch) continue;
    const m2 = legalMove(base, i, [h, g, c, touch], [size, field]);
    if (m2.ok) return [m2, g];
  }
  return [m, f];
}
function legalMove(base, i, [h, f, c, touch], [size, field]){   // moveUnit for a hex whose least movement and contact are known, without finding the path again
  const u = base[i], moved = { ...u, pos: h, facing: mod6(f) };
  if (!fits(base, i, moved, size, field)) return { ok: false };
  const turns = Math.min(mod6(f - u.facing), mod6(u.facing - f));
  const cost = c + turns * turnCost(u) + (turns ? sweepCost(field, { ...u, pos: h }, moved) : 0), allow = allowance(u);
  if (cost <= allow) return { ok: true, cost, charge: touch && c > 0 };
  if (touch && u.state === "steady" && cost <= allow * UD.charge_move) return { ok: true, cost, charge: true };
  return { ok: false };
}
const touches = (u, foes) => footprint(u).some(row => row.some(h => [0, 1, 2, 3, 4, 5].some(dn => foes.has(hk(step(h, dn))))));   // placed so, it touches a hex the enemy stands on
function rejects(m, charge, hold){                // a move it will not make: illegal, a charge without the odds, or (holding) anything but a charge
  if (!m.ok) return true;
  return m.charge ? !charge : hold;
}
function stayOrder(us, i, t, f, shooter){         // on the ground it stays down; else turn to the target, or go to ground under fire with a modern weapon
  const u = us[i], C = UD.commander;
  if (u.prone) return null;
  if (f !== u.facing) return { act: "turn", target: t, facing: f };
  const dig = shooter && !u.vehicle && C.ground_with.includes(u.weapon) && (C.cover[u.quality] ?? 0) > 0 && underFire(us, i);   // vehicles do not go to ground
  return dig ? { act: "ground", target: t } : null;
}
const aside = (h, to) => { const x = 2 * h[0] + (h[1] & 1), tx = 2 * to[0] + (to[1] & 1); return (x - tx) ** 2 + 3 * (h[1] - to[1]) ** 2 };   // squared straight-line distance: ties go to the move nearer the straight line (as commander.aside)
function aiScore(field, u, tu, h, cost, shooter, storm = false){   // how much the commander likes unit u ending at h (higher is better); storming works, it takes no account of cover on the way
  const C = UD.commander, q = u.quality, dist = hdist(h, tu.pos);
  const s = (storm ? 0 : (C.cover[q] ?? 0)) * coverAt(field, tu.pos, h) - cost - (C.mines[q] ?? 0) * mined(field, u.pos, h, u.side);
  if (shooter){
    const inr = dist >= 1 && (fieldRange(u.weapon, dist) !== null || gunInRange(field, u, [h, tu.pos, dist]));
    const stand = inr && u.vehicle && gunOf(u) && !answers(field, tu, [tu.pos, [...h], dist]) ? C.stand_off : 0;
    return s + stand + (inr ? C.in_range : -C.closing * dist) - (dist < C.keep_off ? C.too_close : 0);
  }
  const flank = arc(tu.facing, bearing(tu.pos, h)) === "front" ? 0 : (C.flank[q] ?? 0);
  return s - C.closing * dist + flank;
}
function gunInRange(field, u, [h, t, dist]){      // u's main gun (a vehicle's, or anti-tank guns) reaches from h to t and the weather and light let it see t from there (as commander._gun_in_range)
  const G = gunOf(u);
  if (!G || dist > G.range) return false;
  const sight = sightHexes(field, [...t], seerOf({ ...u, pos: [...h] }));
  return sight === null || dist <= sight;
}
function answers(field, e, [a, h, dist]){          // enemy unit e at a could shoot back at hex h: its weapon or main gun reaches and the weather and light let it see h (as commander._answers)
  const sight = sightHexes(field, h, seerOf({ ...e, pos: [...a] }));
  if (sight !== null && dist > sight) return false;
  if ("range" in FD.weapons[e.weapon] && fieldRange(e.weapon, dist) !== null) return true;
  const G = gunOf(e);
  return !!G && dist <= G.range;
}
function mined(field, a, h, side = null){         // hexes of minefields its side knows of (marked, found, or laid by its sappers) on the straight way from a to h
  const mines = field?.mines || {};
  if (!Object.keys(mines).length || (a[0] === h[0] && a[1] === h[1])) return 0;
  return ray([...a], [...h], hdist(a, h)).slice(1).filter(x => { const m = mines[hk(x)]; return m && knownMine(m, side) }).length;
}
function reachable(units, i, size, limit, field = null, through = false){   // Map hk -> [hex, least movement] for every hex the middle hex can reach within limit (through: passing its own side's units)
  const occ = occupancy(mates(units, i, through)), u = units[i];
  const best = new Map([[hk(u.pos), 0]]), done = new Map(), open = [[0, u.pos]];
  while (open.length){
    const [cost, h] = popCheapest(open);
    if (done.has(hk(h))) continue;
    done.set(hk(h), [h, cost]);
    for (const [x, c] of stepsFrom(field, u, h, occ, size)){
      if (cost + c > limit || cost + c >= (best.get(hk(x)) ?? limit + 1)) continue;
      best.set(hk(x), cost + c);
      open.push([cost + c, x]);
    }
  }
  return done;
}
function applyOrder(us, i, o){                    // carry out an order (as the page's own move: charged when it charges)
  const u = us[i];
  if (o.act === "ground") us[i] = { ...u, prone: true };
  else if (o.act === "dig") us[i] = { ...u, digging: { at: [...u.pos], n: 0 } };
  else if (o.act === "resupply") us[i] = { ...u, resupplying: true };
  else if (o.act === "lay") us[i] = { ...u, mining: { at: [...u.pos], facing: u.facing, n: 0, kind: o.kind } };
  else if (o.act === "lift") us[i] = { ...u, clearing: { at: [...u.pos], facing: u.facing, n: 0 } };
  else if (o.act === "turn") us[i] = { ...u, facing: o.facing };
  else if (AI_MOVES.has(o.act)){
    us[i] = { ...u, pos: o.pos, facing: o.facing, charged: o.act === "charge", ...(o.up ? { prone: false } : {}) };
    for (const k of o.through || []) us[k] = { ...us[k], jostled: true };   // the friends it charged through are jostled
  }
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
function diesOfWound(lethal, [care, ev], d100){   // a wound that kills in minutes or hours: does it, before help comes? the medevac's figures where better (as units._dies)
  const A = UD.aftermath, K = A.medevac?.kinds?.[ev] || {};
  if (lethal === "minutes") return d100() > Math.max(A.saved.minutes, K.minutes || 0);
  if (lethal === "hours") return d100() > Math.max(A.saved.hours[care], K.hours || 0);
  return false;
}
function medevacKind(table, hasLz, helosLeft){    // a side's medevac in this war, helicopters falling back without a landing zone or a helicopter left; null if none (as units.medevac_kind)
  const M = UD.aftermath.medevac || {};
  let kind = M.battles?.[FD.tables[table]?.battle] ?? null;
  if (M.kinds?.[kind]?.fallback && !(hasLz && helosLeft)) kind = M.kinds[kind].fallback;
  return kind;
}
function aftermath(units, care, rng, medevac = null){   // per unit {left, died, cases}; care: each unit's camp care; medevac: each unit's side's medevac kind or null
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
        if (diesOfWound(lethal, [care[i], medevac ? medevac[i] : null], d100)) r.died++;
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
const isAtGun = u => (UD.anti_tank_guns?.weapons || []).includes(u.weapon);   // an anti-tank gun unit
const atGuns = u => Math.ceil(Math.max(0, u.men) / UD.anti_tank_guns.crew);    // its guns served: one a crew, while a man of it is up
function meleeWeapon(u){                           // hand to hand, a battery's or an anti-tank gun's crews have their own weapon
  if (isBattery(u)) return UD.artillery.crew_weapon;
  return isAtGun(u) ? UD.anti_tank_guns.crew_weapon : u.weapon;
}
const gunsOf = u => Math.ceil((u.start ?? u.men) / UD.artillery.crew);   // the guns it brought into action
const gunsServed = u => Math.max(0, Math.min(gunsOf(u) - (u.guns_lost || 0), Math.ceil(Math.max(0, u.men) / UD.artillery.crew)));
const ammoLeft = u => Math.max(0, gunsOf(u) * UD.artillery.ammo - (u.spent || 0));
const thermalSight = (cond, vis, seer) => (vis !== null && vis !== undefined && cond?.thermal && seesSmoke(seer) ? Math.max(vis, cond.thermal) : vis);   // a thermal sight sees further through a sandstorm (weather.yaml thermal) (as units._thermal_sight)
function gunWeather(field, dist, h = null, t = null, seer = null){   // no laying guns on what cannot be seen (less with rain or snow in the gunners' faces); the wind as on firearms
  const out = { blocked: null, penalty: 0, misfire: 0, reach: 0 }, w = field?.weather;
  if (!w) return out;
  const cond = WXD.conditions[w.cond];
  let vis = cond.visibility;
  if (vis !== null && vis !== undefined && cond.precip !== "none" && windLie(w, h, t, upOf(field)) === "against") vis = Math.floor(vis * WXD.driven_sight / 100);
  vis = thermalSight(cond, vis, seer);
  if (vis !== null && vis !== undefined && dist * UD.range_scale > vis){ out.blocked = `${cond.name}: the guns cannot be laid on what cannot be seen.`; return out }
  out.penalty = WXD.winds.find(x => x.id === w.wind).firearm;
  return inTheDark(field, dist, t, out, seer);
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
function sectionsOf(u){                           // the sections a battery has split off, in order
  if (u.sections?.length) return [...u.sections];
  return u.section ? [u.section] : [];
}
function batteryFires(units, occ, field, i, best){   // the battery's fire at best, then each section's at its own target (guns from those left, one stays); each carries its share of the rounds left, by its guns (as units._battery_fires)
  const u = units[i], guns = gunsServed(u), ammo = ammoLeft(u), firing = [];
  let spare = guns - 1;
  for (const sec of sectionsOf(u)){
    const n = Math.min(sec.guns || 0, spare), at = n > 0 ? namedTarget(units, i, field, occ, sec.target) : null;
    if (at){ firing.push([sec, n, at, Math.floor(ammo * n / guns)]); spare -= n }
  }
  const mainGuns = guns - firing.reduce((a, f) => a + f[1], 0), mainAmmo = ammo - firing.reduce((a, f) => a + f[3], 0);
  const out = [batteryFire(units, [occ, field], i, best, { guns: mainGuns, ammo: mainAmmo, shot: u.shot })];
  for (const [sec, n, at, share] of firing) if (share > 0) out.push(batteryFire(units, [occ, field], i, at, { guns: n, ammo: share, shot: sec.shot, section: true }));
  return out;
}
function batteryFire(units, ground, i, best, order){   // guns of battery i at best; order {guns, ammo, shot, per, section}
  const [occ, field] = ground, A = UD.artillery, u = units[i];
  const wx = gunWeather(field, best[0], best[2], best[3], seerOf(u)), shot = shotKind(u, best[0], order.shot);
  const behind = shot === "round" ? ricochetAt(occ, field, i, best) : null, tgt = units[best[1]], tid = tgt.id;
  const graze = shot === "canister" && best[0] > A.canister.strike[0][0] && firmLine(field, best) ? A.canister.graze : 0;
  return { att: i, dfd: best[1], guns: order.guns, rounds: Math.min(order.guns * (order.per ?? A.rounds), order.ammo), dist: best[0], shot, cover: coverAt(field, best[2], best[3]) + groundCover(tgt), penalty: wx.penalty,
    named: !!order.section || (tid !== undefined && tid !== null && tid === u.target), graze, bore: gunKind(u), behind: behind ? behind[0] : null, beyond: behind ? behind[1] : 0,
    fuse: shot === "shell" ? fuseSetting(u, tid, best[0]) : 0, section: !!order.section };
}
function fuseSetting(u, tid, dist){               // how far the gunners' cut fuses widen the air band: crew quality, and more on a target ranged last exchange
  const F = UD.artillery.set_fuse;
  if (!F) return 0;
  const was = tid === undefined || tid === null ? undefined : u.laid?.[String(tid)];
  return (F.quality[u.quality] || 0) + (was !== undefined && Math.abs(was - dist) <= F.within ? F.ranged : 0);
}
function closingFire(units, field = null){        // batteries charged in front: canister at the first charger as it comes in (closing: true)
  const A = UD.artillery, out = [];
  if (A?.closing === undefined) return out;
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
  if (isAtGun(u) && u.resupplying){ u.spent = 0; u.resupplying = false }
  if (u.resupplying && ammoFull(u)){ delete u.ammo; u.resupplying = false }
  if (!isBattery(u)) return;
  u.laid = u.fired || {};
  delete u.fired;
  if (u.resupplying){ u.spent = 0; u.resupplying = false }
  if (u.limbering){ u.limbered = !u.limbered; u.limbering = false }
  if (u.state === "broken" || u.state === "fled") u.abandoned = true;
}

/* ---------- the turn: a battle's moves and exchanges, shared by the page and self-play (as battle.py) ----------
   B: a battle's state, {sides, table, units, field, size, exchange, phase ("setup", 0, 1 or "over"), stages,
   stageNo, waiting, start, entry, seq}; the page's S is one. */
const EDGE_FACING = { S: 1, N: 4, W: 0, E: 3 }, OPPOSITE = { S: "N", N: "S", W: "E", E: "W" };
const EDGE_BEHIND = ["W", "S", "E", "E", "N", "W"];   // the map edge behind units facing 0-5 (as entrySpots)
const sideIndex = (B, u) => (u.side === B.sides[0] ? 0 : 1);
const fieldSupport = B => B.field.support || (B.field.support = []);
function makeUnit(o, id, table){                   // a new unit as the GM or a battlefield draws it (as battle.make_unit)
  const nv = o.nv || (o.vehicle ? vehicleDevice(table) : null), fc = fireControlOf(o, table);
  return { id, name: o.name, side: o.side, banner: o.banner || null, force: o.force ?? null, men: o.men, start: o.men, down: 0, dead: 0, hurt: {}, heroes: [], quality: o.quality, weapon: o.weapon,
    kit: o.kit, formation: o.formation, mounted: !!o.mounted, ...(isGun(o.weapon) ? { guns: gunKind(o) } : {}), width: o.width || Math.ceil(o.men / form(o).per_hex),
    pos: o.pos, facing: o.facing, state: "steady", charged: false, ...(o.prone ? { prone: true } : {}), ...(o.emplaced ? { emplaced: true } : {}), ...(o.vehicle ? { vehicle: o.vehicle } : {}), ...(o.fixed ? { fixed: o.fixed.slice() } : {}), ...(o.armour ? { armour: o.armour } : {}), ...(o.via?.length ? { via: o.via.map(h => [...h]) } : {}), ...(nv ? { nv } : {}), ...(fc ? { fc } : {}), ...(o.fac ? { fac: true } : {}), ...(o.ladders ? { ladders: true } : {}), ...(o.type ? { type: o.type } : {}), ...(o.size ? { size: o.size } : {}), ...(o.medics ? { medics: o.medics, medic_quality: o.medic_quality || o.quality } : {}) };
}
function ensureTags(B){                            // each unit's number on its side, kept for the battle (B3 stays B3) (as battle.ensure_tags)
  for (const u of [...B.units].sort((a, b) => a.id - b.id)) if (!u.n){
    const k = sideIndex(B, u);
    u.n = 1 + Math.max(0, ...B.units.filter(v => v.n && sideIndex(B, v) === k).map(v => v.n));
  }
}
function standOrFly(B, unit, lands){               // a battlefield's unit: on the field, or (lands: a landing zone's index) waiting to come in by air (as battle.stand_or_fly)
  const lz = lands === undefined || lands === null ? null : (B.field.lz || [])[lands];
  if (!lz){ B.units.push(unit); return }
  const { men, start, down, dead, hurt, heroes, state, ...tmpl } = unit;
  (B.field.lifts || (B.field.lifts = [])).push({ unit: { ...tmpl, pos: [...lz] }, lz: [...lz], left: men });
}
function holdForStages(B, phases){                 // the battlefield's phases; the units they bring on wait off the map (numbered first, so B5 is still B5) (as battle.hold_for_stages)
  if (!phases?.length) return;
  ensureTags(B);
  B.stages = structuredClone(phases);
  B.stageNo = -1;
  B.waiting = [];
  const lifts = B.field.lifts || [], sup = fieldSupport(B);
  B.stages.forEach((st, i) => (st.arrive || []).forEach(name => {
    const u = B.units.find(v => v.name === name), lf = lifts.find(l => l.unit.name === name), b = sup.find(x => x.name === name);
    if (u){ B.waiting.push({ stage: i, unit: u }); B.units = B.units.filter(v => v !== u) }
    else if (lf){ B.waiting.push({ stage: i, unit: lf.unit, lift: lf }); B.field.lifts = B.field.lifts.filter(l => l !== lf) }   // coming in by air: it takes off when its phase begins
    else if (b){ B.waiting.push({ stage: i, unit: { name: b.name }, support: b }); B.field.support = fieldSupport(B).filter(x => x !== b) }   // a battery or aircraft: on call from its phase
  }));
}
function setUpBattle(fid){                         // a battlefield with its armies as drawn up, before the battle starts (as battle.set_up)
  const F = FD.fields[fid];
  const B = { sides: F.sides.slice(), table: F.table, units: [], field: structuredClone(F.field), exchange: 0, phase: "setup", stages: null, stageNo: -1, waiting: [], start: null, entry: F.entry || null, seq: 1 };
  B.size = B.field.size.slice();
  B.field.lifts = [];
  F.units.forEach(u => standOrFly(B, makeUnit({ ...u, side: F.sides[u.side] }, B.seq++, B.table), u.lands));
  holdForStages(B, F.phases);
  return B;
}
const fielded = (B, k) => B.units.some(u => sideIndex(B, u) === k && u.men > 0 && u.state !== "fled");
function sideFacing(B, k){                         // the way most of a side's men face (its starting edge's way if it has none left) (as battle.side_facing)
  const n = [0, 0, 0, 0, 0, 0];
  B.units.filter(u => sideIndex(B, u) === k && u.men > 0 && u.state !== "fled").forEach(u => { n[mod6(u.facing)] += u.men });
  if (Math.max(...n) > 0) return n.indexOf(Math.max(...n));
  return k ? 3 : 0;
}
function entryEdge(B, k){                          // where side k's new units come in: the battlefield's entry, else the edge behind the way most of its men face; the other side's opposite edge if they would share one (as battle.entry_edge)
  if (B.entry) return B.entry[k];
  const own = s => (fielded(B, s) ? EDGE_BEHIND[mod6(sideFacing(B, s))] : null);
  const mine = own(k), theirs = own(1 - k);
  if (mine && !(k === 1 && mine === theirs)) return mine;
  if (theirs) return OPPOSITE[theirs];
  return k ? "E" : "W";                           // no units on either side: west and east
}
function entrySpots(size, facing, ranks){          // front hexes for a unit `ranks` deep with its rear at the map edge behind a side facing this way, middle outwards (as battle.entry_spots)
  const [W, H] = size, mid = m => Array.from({ length: m }, (_, i) => Math.floor(m / 2) + (i % 2 ? -1 : 1) * Math.ceil(i / 2)).filter(x => x >= 0 && x < m);
  const out = [];
  for (let d = ranks; d < ranks + 12; d++){
    if (facing === 1) mid(W).forEach(c => out.push([c, H - 1 - d]));        // facing the top: come on at the bottom
    else if (facing === 4) mid(W).forEach(c => out.push([c, d]));           // facing the bottom: at the top
    else if (facing === 0 || facing === 5) mid(H).forEach(r => out.push([d, r]));   // facing right: at the left
    else mid(H).forEach(r => out.push([W - 1 - d, r]));                     // facing left: at the right
  }
  return out;
}
function entryWidths(size, w){                     // the widths to try: as asked (at most the map's width), then a quarter narrower each time, to 1 (as battle.entry_widths)
  const out = [];
  for (let x = Math.min(w, size[0] - 4); x >= 1; x = x > 1 ? Math.min(x - 1, Math.floor(x * 0.75)) : 0) out.push(x);
  return out;
}
function placeArrival(B, u, k){                    // where an arriving unit comes on: where the battlefield draws it if there is room, else at its side's entry edge; null if no room (as battle.place_arrival)
  if (fits([...B.units, u], B.units.length, u, B.size, B.field)) return u;
  const facing = EDGE_FACING[entryEdge(B, k)];
  for (const width of entryWidths(B.size, u.width)){
    const ranks = footprint({ ...u, width, pos: [0, 0], facing }).length;
    const pos = entrySpots(B.size, facing, ranks).find(h => fits([...B.units, { ...u, width, pos: h, facing }], B.units.length, { ...u, width, pos: h, facing }, B.size, B.field));
    if (pos) return { ...u, width, pos, facing };
  }
  return null;
}
function lightOfPhase(B, st, out){                 // a phase that sets the light (light: a weather.yaml light level) changes the field's from then on (sunset, dawn); out.light: {phase index: the level's name} (as battle._light_of_phase)
  if (!st.light) return;
  B.field.weather = { ...B.field.weather, light: st.light };
  (out.light || (out.light = {}))[B.stageNo] = FD.weather.light.levels[st.light].name;
}
function advanceStages(B){                         // at the start of an exchange: begin each phase whose exchange has come, and bring on its units (any with no room wait for the next exchange): {begun: [phase index], came: [unit index], flying: [{name, left}], onCall: [name]} (as battle.advance_stages)
  const out = { begun: [], came: [], flying: [], onCall: [] };
  if (!B.stages) return out;
  while (B.stageNo + 1 < B.stages.length && B.stages[B.stageNo + 1].at <= B.exchange){
    B.stageNo += 1;
    out.begun.push(B.stageNo);
    lightOfPhase(B, B.stages[B.stageNo], out);
  }
  B.waiting = B.waiting.filter(w => {
    if (w.stage > B.stageNo) return true;
    if (w.support){ fieldSupport(B).push(w.support); out.onCall.push(w.support.name); return false }
    if (w.lift){ (B.field.lifts || (B.field.lifts = [])).push(w.lift); out.flying.push({ name: w.unit.name, left: w.lift.left }); return false }   // lands by the heliborne rules, a lift at a time
    const at = placeArrival(B, w.unit, sideIndex(B, w.unit));
    if (!at) return true;
    B.units.push({ ...at, arrived: B.exchange });
    out.came.push(B.units.length - 1);
    return false;
  });
  return out;
}
function markStarts(B){                            // with minefields down, where each unit's first moves begin (the ground it crosses) (as battle.mark_starts)
  if (Object.keys(B.field.mines || {}).length) for (const u of B.units) u.was = [[...u.pos], u.facing];
}
function startPhase(B, k){                         // side k's move; at the start of an exchange every broken unit runs first: [{unit, through}] (as battle.start_phase)
  B.phase = k;
  const ran = [];
  for (let i = 0; i < B.units.length; i++){
    if (k !== 0 || B.units[i].state !== "broken") continue;
    const through = ranThrough(B.units, i, flee(B.units, i, B.size, B.field));
    B.units = runAway(B.units, i, B.size, B.field);
    ran.push({ unit: i, through, fled: B.units[i].state === "fled" });
  }
  B.start = B.units.map(u => ({ ...u }));
  return ran;
}
function drifts(B, k, rng){                        // in the dark, each unit of side k that moved this phase may lose its direction: [{unit, strayed, turned}] (as battle.drifts)
  if (!lightOf(B.field)) return [];
  const out = [];
  B.units.forEach((u, i) => {
    const was = B.start?.[i];
    if (u.side !== B.sides[k] || !was || (was.pos[0] === u.pos[0] && was.pos[1] === u.pos[1])) return;
    const r = nightDrift(B.units, i, B.size, B.field, rng);
    if (!r.lost) return;
    B.units[i] = r.unit;
    out.push({ unit: i, strayed: !!r.strayed, turned: r.unit.facing !== u.facing });
  });
  return out;
}
function realignStarts(B){                         // B.start by unit id, after units joined or left the list (a unit whose riders changed starts as it is) (as battle.realign_starts)
  const was = B.start || [];
  B.start = B.units.map(u => { const s = was.find(x => x.id === u.id); return s && s.riders?.id === u.riders?.id ? s : { ...u } });
}
function beginBattle(B){                           // set-up done: the first exchange begins, side 0 to move: {stages, ran} (as battle.begin)
  B.exchange = 1;
  const stages = advanceStages(B);
  markStarts(B);
  return { stages, ran: startPhase(B, 0) };
}
function endMove(B, rng){                          // the moving side's move is done: after side 0, side 1 moves; after side 1, the exchange is fought and the next begins: {lost, log, stages, ran} (as battle.end_move)
  if (B.phase === 0){
    const lost = drifts(B, 0, rng);
    return { lost, log: null, stages: null, ran: startPhase(B, 1) };
  }
  const lost = drifts(B, 1, rng), r = exchange(B.units, B.table, rng, B.field);
  B.units = r.units;
  B.exchange += 1;
  const stages = advanceStages(B);
  return { lost, log: r.log, stages, ran: startPhase(B, 0) };
}
function commanderMemory(B, M){                   // M {n, mem}: where a side's commander last saw each enemy unit (by index), forgotten when units joined or left the list since (as battle.commander_memory)
  if (M.n !== B.units.length){ M.mem = {}; M.n = B.units.length }
  return M.mem;
}
function commandMove(B, stance, M, rng){           // the commander orders the moving side (M: its memory, see commanderMemory): its orders (as battle.command_move)
  const n = B.units.length, r = command(B.units, B.sides[B.phase], B.size, B.field, rng, B.exchange, { stance, memory: commanderMemory(B, M), table: B.table });
  B.units = r.units;
  if (B.units.length !== n) realignStarts(B);     // guns hooked up or unhooked: each unit's move this phase starts where it stood
  M.n = B.units.length;
  return r.orders;
}
const standingSide = (B, k) => B.units.some(u => u.side === B.sides[k] && u.men > 0 && (u.state === "steady" || u.state === "shaken"));
const toCome = (B, k) => (B.waiting || []).some(w => !w.support && sideIndex(B, w.unit) === k) || (B.field.lifts || []).some(l => l.unit.side === B.sides[k] && l.left > 0);   // side k has units still to come on: a later phase's, or by air (as battle.to_come)
function secured(B, side){                        // no standing enemy of side within commander.self_play.secure hexes of the (first) objective, and none still to come (as battle.secured)
  const R = UD.commander.self_play.secure, at = B.field.objective;
  if (toCome(B, 1 - B.sides.indexOf(side))) return false;
  return !B.units.some(u => u.side !== side && u.men > 0 && STANDING.has(u.state) && hdist(u.pos, at) <= R);
}
function playStop(B, held, stances){               // after an exchange of a self-played battle: why it stops, or null; held {side, n}: which attacking side held the (first) objective and for how many exchanges running, updated; stances: each side's; a side with none standing but units still to come is not gone (as battle.stop_reason)
  const P = UD.commander.self_play, gone = [0, 1].filter(k => !standingSide(B, k) && !toCome(B, k));
  const h = objectiveHeld(B.units, B.field)[0]?.held ?? null;
  if (!held.seen){ held.seen = true; held.start = h }   // who held it after the first exchange: holding it from the start is not taking it
  else if (h !== held.start) held.start = null;   // once it has changed hands, taking it counts
  const o = h !== null && h !== held.start && stances[B.sides.indexOf(h)] === "attack" && secured(B, h) ? h : null;   // a holding side on its ground has not taken it; nor has one with the enemy still close round it
  if (o === null) held.n = 0;
  else held.n = o === held.side ? held.n + 1 : 1;
  held.side = o;
  if (gone.length) return { why: "gone", sides: gone };
  if (held.n >= P.held) return { why: "held", side: o };
  if (B.exchange - 1 >= playLimit(B)) return { why: "limit" };
  return null;
}
function playLimit(B){                            // the exchanges a self-played battle runs at most: the limit, or after_phases past its last phase's start (as battle.play_limit)
  const P = UD.commander.self_play, last = Math.max(0, ...(B.stages || []).map(s => s.at));
  return Math.max(P.limit, Math.min(P.most, last ? last + P.after_phases : 0));
}
function playStances(fid){                         // a self-played battle's stances: the side the battlefield's objective names attacks and the other holds; else its stances as fought; else both attack (as battle.stances)
  const F = fid ? FD.fields[fid] : null, o = F?.objective;
  if (o) return [0, 1].map(k => (k === o.side ? "attack" : "hold"));
  return F?.stances ? [...F.stances] : ["attack", "attack"];
}
function crewsOf(B){                               // each fire-support battery with crews (not aircraft), as a unit for the after-battle reckoning (as battle.crews)
  return fieldSupport(B).map((b, k) => [b, k]).filter(([b]) => !UD.indirect.kinds[b.kind]?.air && typeof b.crew === "number")
    .map(([b, k]) => ({ id: `sup${k}`, name: b.name, side: b.side, men: b.crew, start: b.crew + (b.crew_down || 0), down: b.crew_down || 0, dead: b.crew_dead || 0, hurt: b.hurt || {}, state: "steady", heroes: [] }));
}
const afterAll = B => [...B.units, ...B.units.filter(u => u.riders).map(u => u.riders), ...crewsOf(B)];   // every unit, the men still aboard carriers too, and the batteries' crews
function sideEvac(B, k){                           // side k's medevac kind (its war's, helicopters falling back without a zone or a helicopter left), or null if none (as battle.side_medevac)
  const H = UD.heliborne ? helos(B.field, B.sides[k]) : null, left = !!H && H.aircraft - (H.damaged || 0) - (H.downed || 0) > 0;
  return medevacKind(B.table, (B.field.lz || []).length > 0, left);
}
function afterBattle(B, care, evac, rng){          // the battle over: each unit's aftermath (care, evac: per unit) and the heroes' fates, applied: {all, after, fates} (as battle.after_battle)
  const all = afterAll(B), am = aftermath(all, care, rng, evac);
  const after = all.map((u, i) => ({ id: u.id, killed: u.dead || 0, ...am[i] }));
  const fates = heroFates(B.units, B.table, rng);  // heroes left on the field: found, taken prisoner or killed
  for (const f of fates){
    const h = B.units[f.unit].heroes.find(x => x.id === f.hero);
    if (f.fate === "killed") h.state = "dead";
    else if (f.fate === "prisoner") h.state = "prisoner";
    h.fate = f.fate;
  }
  B.phase = "over";
  return { all, after, fates };
}
/* Turning points, for the narrative: what changed in an exchange that a reader would want told (as battle.py) */
const STANDING = new Set(["steady", "shaken"]);
function pointsBase(B){                            // the state turning points are measured from: each unit's state by id, and who held each objective (as battle.points_base)
  return { states: Object.fromEntries(B.units.map(u => [u.id, u.state])), held: objectiveHeld(B.units, B.field).map(o => o.held) };
}
function commitsOf(B, orders){                     // the reserve units a commander's orders committed, by id (as battle.commits_of)
  return orders.filter(o => o.act === "commit").map(o => B.units[o.unit]?.id).filter(x => x !== undefined);
}
function turningPoints(B, base, stages, commits){  // since base: phases begun (and who came on), units broken or fled by side, objectives taken or lost, reserves committed (ids by side): [point] (as battle.turning_points)
  const out = [];
  for (const i of stages?.begun || []) out.push({ kind: "phase", stage: i, came: (stages.came || []).map(k => B.units[k]?.id), ...(stages.light?.[i] ? { light: stages.light[i] } : {}) });
  for (const [k, side] of B.sides.entries()){
    const mine = B.units.filter(u => u.side === side && u.id in base.states);
    const broke = mine.filter(u => STANDING.has(base.states[u.id]) && !STANDING.has(u.state)).map(u => u.id);
    const fled = mine.filter(u => base.states[u.id] !== "fled" && u.state === "fled").map(u => u.id);
    if (broke.length || fled.length) out.push({ kind: "broke", side: k, units: broke, fled });
    const c = commits.filter(id => B.units.some(u => u.id === id && u.side === side));
    if (c.length) out.push({ kind: "commit", side: k, units: c });
  }
  objectiveHeld(B.units, B.field).forEach((o, i) => {
    const was = base.held[i] ?? null;
    if (o.held !== was) out.push({ kind: "objective", second: !!o.second, held: o.held, was });
  });
  return out;
}
function endPoint(B, stop, all, after){            // the battle's end, as a turning point: why it stopped (null: the GM ended it), each side's men killed, left on the field, died of wounds, carried to camp, and units still standing (as battle.end_point)
  const sides = B.sides.map(side => {
    const rows = all.map((u, i) => [u, after[i]]).filter(([u]) => u.side === side);
    return { start: rows.reduce((n, [u]) => n + (u.start || 0), 0), killed: rows.reduce((n, [, a]) => n + a.killed, 0), left: rows.reduce((n, [, a]) => n + a.left, 0),
      died: rows.reduce((n, [, a]) => n + a.died, 0), carried: rows.reduce((n, [, a]) => n + a.cases.length, 0),
      standing: B.units.filter(u => u.side === side && u.men > 0 && STANDING.has(u.state)).length };
  });
  return { kind: "end", exchanges: B.exchange - 1, stop, sides, held: objectiveHeld(B.units, B.field).map(o => o.held) };
}
function selfPlay(fid, rng, stances = null){       // a battlefield played to its end by the commander on both sides (as battle.self_play): {battle, stop, orders, after, fates, points}
  const B = setUpBattle(fid), st = stances || playStances(fid), mem = [{ n: -1, mem: {} }, { n: -1, mem: {} }], held = { side: null, n: 0 };
  const opening = beginBattle(B), points = [];
  let stop = null, orders = 0, base = pointsBase(B);
  const first = turningPoints(B, base, opening.stages, []);
  if (first.length) points.push({ exchange: 0, points: first });
  while (!stop){
    const ex = B.exchange, commits = [];
    let stages = null;
    for (const k of [0, 1]){
      const o = commandMove(B, st[k], mem[k], rng);
      orders += o.length;
      commits.push(...commitsOf(B, o));
      stages = endMove(B, rng).stages || stages;
    }
    const pts = turningPoints(B, base, stages, commits);
    if (pts.length) points.push({ exchange: ex, points: pts });
    base = pointsBase(B);
    stop = playStop(B, held, st);
  }
  const all = afterAll(B), evac = [sideEvac(B, 0), sideEvac(B, 1)];
  const r = afterBattle(B, all.map(() => "field"), all.map(u => evac[sideIndex(B, u)]), rng);
  points.push({ exchange: B.exchange - 1, points: [endPoint(B, stop, all, r.after)] });
  return { battle: B, stop, orders, after: r.after, fates: r.fates, points };
}
