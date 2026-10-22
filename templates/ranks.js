/* Skill checks, rank, pay, promotion and loot: the rules of gravewounds/checks.py and
   gravewounds/ranks.py, shared by the team builder and the wound roller (build.py puts this file
   beside purse.js in each page). They read TD: {checks, ranks, era: {id, skills}}; the team
   builder's TD is its team bundle, the roller sets TD.era to a fighter's era before using them. */
/* Skill checks out of a fight (as gravewounds/checks.py, data TD.checks): the one roll with a
   difficulty, opposed rolls (ties and double failures go to the side resisting), haggling. */
const CHK = () => TD.checks || { critical_fraction: 0.1, fumble_from: 96, difficulty: [{ id: "ordinary", mod: 0 }] };
const chkMod = diff => (CHK().difficulty.find(x => x.id === diff) || { mod: 0 }).mod;
function skillCheck(value, diff, roll){            // {target, roll, success, critical, fumble, margin}
  const C = CHK(), target = Math.max(0, value + chkMod(diff)), ok = roll <= target;
  return { target, roll, success: ok, critical: ok && roll <= Math.floor(target * C.critical_fraction), fumble: !ok && roll >= C.fumble_from, margin: ok ? target - roll : null };
}
const chkRank = c => [c.success ? 1 : 0, c.critical ? 1 : 0, c.success ? c.margin : 0];
const rankAbove = (x, y) => { for (let i = 0; i < x.length; i++) if (x[i] !== y[i]) return x[i] > y[i]; return false };
function opposedCheck(aValue, aDiff, aRoll, bValue, bRoll){   // {a, b, winner}: a must beat b
  const a = skillCheck(aValue, aDiff, aRoll), b = skillCheck(bValue, "ordinary", bRoll);
  return { a, b, winner: rankAbove(chkRank(a), chkRank(b)) ? "a" : "b" };
}
function haggle(price, persuade, aRoll, bRoll, seller = null){   // {outcome: win | critical | list | no_sale, price, opposed}
  const H = CHK().haggle || { seller: 50, win: -0.1, critical: -0.25 };
  const o = opposedCheck(persuade, "ordinary", aRoll, seller === null ? H.seller : seller, bRoll);
  if (o.a.fumble) return { outcome: "no_sale", price: null, opposed: o };
  if (o.winner === "a"){ const kind = o.a.critical ? "critical" : "win"; return { outcome: kind, price: price > 0 ? Math.max(0.25, Math.floor(price * (1 + H[kind]) * 4 + 0.5) / 4) : 0, opposed: o } }
  return { outcome: "list", price, opposed: o };
}
const CHK_STATS = ["str", "agi", "end", "wits", "nerve", "pres"];
const checkUses = () => (CHK().uses || []).filter(u => CHK_STATS.includes(u.skill) || TD.era.skills.some(s => s.id === u.skill));
/* Rank, pay, promotion and loot (as gravewounds/ranks.py, data TD.ranks), for the era TD.era. */
const RK = () => TD.ranks || {};
const rkQ = x => Math.floor(x * 4 + 0.5) / 4;
const rkEra = () => (RK().eras || {})[TD.era.id] || null;
const rkLadder = () => (rkEra() || {}).ladder || [];
const rkIndex = rid => Math.max(0, rkLadder().findIndex(r => r.id === rid));
function rkStart(career){ const L = rkLadder(); return L.length ? ((rkEra().start || {})[career] || L[0].id) : null }
function rkPay(region, career, rid){
  const E = rkEra() || {}, L = rkLadder(), i = rkIndex(rid);
  if (!L.length) return 0;
  const by = (E.pay_by || {})[region], base = by ? by[i] : L[i].pay;
  return base * ((E.career_pay || {})[career] ?? 1);
}
const rkWage = (region, career, rid, days) => rkQ(days * rkPay(region, career, rid) * ((rkEra() || {}).kept ?? 1));
function rkEligible(c, idx){                       // [ok, why not]
  const L = rkLadder(), R = RK(), r = L[idx];
  if (rkIndex(c.rank) !== idx - 1) return [false, "not the rank below"];
  if (r.deed_only && !c.deed) return [false, "only for a deed"];
  if (!c.deed && (c.rank_days || 0) < (r.years || 0) * (R.days_a_year || 365)) return [false, "too soon"];
  if (r.letters && (c.skills.letters || 0) < (R.literate ?? 20)) return [false, "cannot read and write"];
  return [true, null];
}
function rkPromote(team, vacancies, rng){          // every roll made: [{name, to, roll, target, success}]
  const L = rkLadder(), R = RK(), out = [];
  for (let idx = L.length - 1; idx > 0; idx--){
    const r = L[idx];
    while ((vacancies[r.id] || 0) > 0){
      const cands = team.filter(c => rkEligible(c, idx)[0]).sort((a, b) => (b.rank_days || 0) - (a.rank_days || 0));
      let won = null;
      for (const c of cands){
        let mod = c.deed ? (R.deed_bonus ?? 20) : 0;
        if (r.unlettered && (c.skills.letters || 0) < (R.literate ?? 20)) mod += r.unlettered;
        const k = skillCheck((c.skills.command || 0) + mod, r.diff || "ordinary", rng.randint(1, 100));
        out.push({ name: c.name, to: r.id, roll: k.roll, target: k.target, success: k.success });
        if (k.success){ won = c; break }
      }
      if (!won) break;
      won.rank = r.id; won.rank_days = 0; won.deed = false;
      vacancies[r.id] -= 1;
      if (idx - 1 > 0) vacancies[L[idx - 1].id] = (vacancies[L[idx - 1].id] || 0) + 1;
    }
  }
  for (const c of team) c.deed = false;
  return out;
}
function rkLoot(kind, c, rng){                      // {kind, roll, what, found, risk, opposed, caught, punished, days, horses, why}
  const R = RK(), L = (R.loot || {})[TD.era.id] || {};
  const out = { kind, roll: null, what: "", found: 0, risk: false, opposed: null, caught: false, punished: false, days: 0, horses: 0, why: "" };
  const plural = (n, w) => `${n} ${w}${n !== 1 ? "s" : ""}`;
  if (kind === "prize"){
    const P = L.prize;
    if (P){ const sh = rkLadder()[rkIndex(c.rank)].shares ?? 1; Object.assign(out, { what: `${sh} share${sh !== 1 ? "s" : ""} of prize money`, found: rkQ(P.share_days * sh), days: rkQ(P.share_days * sh), why: P.why || "" }) }
    return out;
  }
  if (kind === "horses"){
    const H = L.horses;
    if (H){ const n = rng.randint(H.per_raid[0], H.per_raid[1]); Object.assign(out, { what: n ? `${plural(n, "horse")} taken` : "no horses taken", horses: n, why: H.why || "" }) }
    return out;
  }
  if (kind === "ransom"){
    const X = L.ransom;
    if (X){ const v = rng.randint(X.days[0], X.days[1]); Object.assign(out, { what: "a prisoner ransomed", found: v, days: rkQ(v * (L.keep ?? 1)), why: X.why || "" }) }
    return out;
  }
  const sack = kind === "sack" || kind === "sack_after", rules = L[sack ? "sack" : "field"] || { allowed: false };
  const roll = rng.randint(1, 100), look = roll === 100 ? 100 : Math.min(99, roll + (sack ? (R.sack_bonus || 0) : 0));   // a windfall only on 100
  const row = R.finds.find(f => look <= f.to), v = row.days[1] > 0 ? rng.randint(row.days[0], row.days[1]) : 0;
  Object.assign(out, { roll, what: row.what, found: v, why: rules.why || "" });
  if (v <= 0) return out;
  const forbidden = kind === "sack_after" || !rules.allowed;
  if (forbidden || (rules.cap !== undefined && rules.cap !== null && v > rules.cap)){
    const o = opposedCheck(rules.provost ?? 50, "ordinary", rng.randint(1, 100), c.skills.stealth || 0, rng.randint(1, 100)), caught = o.winner === "a";
    Object.assign(out, { risk: true, opposed: o, caught, punished: caught && (o.a.critical || o.b.fumble) });
    if (out.caught) return out;
  }
  out.days = rkQ(v * (L.keep ?? 1));
  return out;
}
const rkTier = (rows, n) => (rows || [{ from: 0, name: "" }]).filter(r => n >= r.from).pop().name;
const rkStanding = honours => rkTier((RK().honours || {}).standing, honours);
const rkWealth = horses => rkTier((RK().honours || {}).wealth, horses);
/* Training (as gravewounds/training.py, data TD.training): a week with a teacher ticks the pupil's
   skill if the teacher's check succeeds; a master for hire, a teammate well ahead, or drill. */
const TRN = () => TD.training || {};
const trMasters = (place, skill = null) => (TRN().masters || []).filter(m => TD.era.skills.some(s => s.id === m.skill) && (skill === null || m.skill === skill) && (place === null || m.places.includes(place)));
const trTeammateOk = (teacher, pupil) => teacher >= pupil + (TRN().teammate_gap ?? 20);
const trWeek = (teacher, roll) => skillCheck(teacher, "ordinary", roll);
function trDrill(camped, bestCommand, roll){       // null if it did not camp enough of the week; else the drill check
  const D = { camped_days: 4, nco: 50, difficulty: "ordinary", ...(TRN().drill || {}) };
  if (camped < D.camped_days) return null;
  return skillCheck(Math.max(bestCommand, D.nco), D.difficulty, roll);
}
/* Carrying weight (as gravewounds/loads.py, data TD.loads): his order's kg (and armour where the
   era's orders leave it out) against his body weight and Strength gives a band. */
const LDS = () => TD.loads || {};
const ldEra = eid => LDS().eras?.[eid] || {};
function ldLoadKg(eid, order, kitClass, extra = 0){ // his load in kg
  const E = ldEra(eid);
  let kg = (E.kg?.[order] || 0) + extra;
  if (!E.armour_in_orders) kg += LDS().armour_kg?.[kitClass || "light"] || 0;
  return kg;
}
const ldBody = (eid, sex = "m") => (ldEra(eid).body_kg ?? 65) + (sex === "f" ? (LDS().woman_kg || 0) : 0);
const ldStrMult = strength => LDS().strength.findLast(r => strength >= r.from).mult;
function ldBand(load, body, strength, afraid = false){   // the band's index; a green man under fire one heavier
  const B = LDS().bands, r = load / (body * ldStrMult(strength));
  const i = B.findIndex(b => r <= b.upto);
  return Math.min(B.length - 1, i + (afraid ? 1 : 0));
}
function ldBlister(band, km, daysMarched = 0){       // % chance of sore feet: the band's for 20 km or more; a quarter once hardened
  let p = (LDS().bands[band].blister || 0) * Math.min(km, 20) / 20;
  if (daysMarched >= (LDS().hardened_days ?? 7)) p /= 4;
  return Math.trunc(p);
}
function ldFatigue(band, km){                       // steps of fatigue a day's km add in this band
  const fk = LDS().bands[band].fatigue_km;
  return fk ? Math.floor(km / fk) : 0;
}
/* Combat stress (as gravewounds/stress.py, data TD.stress): Strain, a share of it into Toll, a Nerve
   check at each multiple passed; rest, treatment, rotation and homecoming. */
const STR = () => TD.stress || {};
const ST_STATES = ["shaken", "strained", "exhaustion", "severe"];
const stNew = () => ({ strain: 0, toll: 0, state: null, broke: false });
const stTotal = st => st.strain + st.toll;
const stWorse = (a, b) => (a === null || a === undefined || ST_STATES.indexOf(b) > ST_STATES.indexOf(a) ? b : a);
function stAdd(st, amount, nerve, rng){            // [{at, roll, target, held, result}]: st changed in place
  const S = STR(), before = stTotal(st), every = S.check_every, out = [];
  st.strain += amount; st.toll += amount * S.toll_share;
  for (let k = Math.floor(before / every) + 1; k <= Math.floor(stTotal(st) / every); k++){
    const at = k * every, target = nerve + S.base - at - (st.broke ? S.relapse : 0), roll = rng.randint(1, 100);
    const held = roll <= target && roll < S.fail_from, row = { at, roll, target, held, result: null };
    if (!held){
      const n = rng.randint(1, 10) + Math.floor(Math.max(0, roll - target) / 10);
      row.result = S.results.find(r => n <= r.to).id;
      st.state = stWorse(st.state, row.result);
      if (row.result === "exhaustion" || row.result === "severe") st.broke = true;
    }
    out.push(row);
  }
  return out;
}
function stRest(st, days){                          // days out of the line
  if (days <= 0) return;
  st.strain = Math.max(0, st.strain - STR().rest_day * days);
  if (st.state === "shaken") st.state = null;
}
const stTreatments = eid => Object.keys(STR().treatment || {}).filter(k => !STR().treatment[k].eras || STR().treatment[k].eras.includes(eid));
function stTreat(st, where, roll){                  // {rtd, chance, roll, days}
  const T = STR().treatment[where], chance = T.rtd[st.state || "shaken"] ?? 0;
  st.strain = T.strain === "all" ? 0 : Math.max(0, st.strain - T.strain);
  if (T.toll) st.toll *= T.toll;
  const rtd = roll <= chance;
  if (rtd) st.state = null;
  return { rtd, chance, roll, days: T.days };
}
function stRelieve(st, kind){                       // rotation home or a homecoming
  st.strain = 0; st.toll *= STR()[kind].toll; st.state = null;
}
const ST_NAME_AT = { shaken: 0, strained: 1, exhaustion: 2, severe: 2 };
const stName = (eid, state) => (STR().names?.[eid] || ["shaken", "strained", "broken down"])[ST_NAME_AT[state]];
const stRow = state => (STR().results || []).find(r => r.id === state) || {};
const stRoll = { randint: (a, b) => a + crypto.getRandomValues(new Uint32Array(1))[0] % (b - a + 1) };
function xpStress(pid, source, nerve, why){         // a man takes a source's Strain (the shared store): -> the checks made
  if (!pid || !TD.stress) return [];
  const all = readXp(), x = xpOf(all, pid), st = (x.stress ||= stNew()), amount = STR().sources[source].strain;
  const ev = stAdd(st, amount, nerve, stRoll);
  x.stressLog ||= [];
  x.stressLog.unshift({ source, why: why || STR().sources[source].name, amount, ev });
  x.stressLog = x.stressLog.slice(0, 30);
  writeXp(all);
  return ev;
}
function xpStressDo(pid, fn){                        // change a man's stress record in the store with fn(st)
  if (!pid) return null;
  const all = readXp(), x = xpOf(all, pid), st = (x.stress ||= stNew()), r = fn(st);
  writeXp(all);
  return r;
}
/* Prisoners (as gravewounds/prisoners.py, data TD.prisoners): the roll on capture, a season of
   captivity, and ransom. */
const PRS = () => TD.prisoners || {};
const prContexts = eid => PRS().eras?.[eid] || [];
const prContext = (eid, cid) => { const cs = prContexts(eid); return cs.find(c => c.id === cid) || cs[0] || {} };
function prCapture(eid, cid, circumstances, roll){  // {roll, total, result: killed | stripped | held}
  const C = PRS(), ctx = prContext(eid, cid);
  const mods = circumstances.reduce((a, k) => { const m = C.circumstances[k]; return m && (!m.ransom_only || ctx.ransom) ? a + m.mod : a }, 0);
  const total = roll - mods, [k, s] = ctx.capture;
  let result = "held";
  if (total <= k) result = "killed"; else if (total <= s) result = "stripped";
  return { roll, total, result };
}
function prHazard(ctx, p, winter){
  const C = PRS();
  let h = (p.seasons || 0) === 0 || ctx.after === undefined ? ctx.hazard : ctx.after;
  if (winter) h *= 2;
  if (p.parole) h *= C.parole_hazard; else if (p.officer) h *= C.officer_hazard;
  return h + C.recapture_hazard * (p.recaptured || 0);
}
function prSeason(eid, p, rng, escape = false, stealth = 0, fieldcraft = 0, winter = false){   // {out, rolls, hazard, harsh, why?}
  const C = PRS(), ctx = prContext(eid, p.ctx), rolls = {}, h = prHazard(ctx, p, winter), harsh = h >= C.harsh_hazard;
  p.seasons = (p.seasons || 0) + 1;
  if (p.serving){ rolls.desert = rng.randint(1, 100); return { out: rolls.desert <= C.service_desert ? "escaped" : null, rolls, hazard: 0, harsh: false } }
  rolls.release = rng.randint(1, 100);
  if (rolls.release <= ctx.release) return { out: "released", rolls, hazard: h, harsh };
  if (escape){
    rolls.break = rng.randint(1, 100);
    if (rolls.break <= stealth + ctx.escape){
      rolls.home = rng.randint(1, 100);
      if (rolls.home <= fieldcraft + ctx.home) return { out: "escaped", rolls, hazard: h, harsh };
      p.recaptured = (p.recaptured || 0) + 1;
      rolls.life = rng.randint(1, 100);
      if (rolls.life <= ctx.recapture) return { out: "died", rolls, hazard: h, harsh, why: "killed when retaken" };
    }
  }
  rolls.death = rng.randint(1, 100);
  if (rolls.death <= h) return { out: "died", rolls, hazard: h, harsh, why: "died in captivity" };
  return { out: null, rolls, hazard: h, harsh };
}
const prQ = x => Math.floor(x * 4 + 0.5) / 4;
function prRansom(eid, cid, dayPay, rankIndex){       // his ransom in Days, or null
  const R = prContext(eid, cid).ransom;
  if (!R) return null;
  if (R.days !== undefined) return R.days;
  if (R.months_per_rank !== undefined) return prQ(R.months_per_rank * 30 * Math.max(1, dayPay) * (rankIndex + 1));
  return prQ(R.years * 365 * Math.max(1, dayPay) * (1 + (R.upkeep || 0)));
}
/* Hazards (as gravewounds/hazards.py, data TD.hazards): who can swim, swimming and drowning, cold
   water, fords, climbing, falls and chases. */
const HZ = () => TD.hazards || {};
function hzSwimAbility(eid, seamanship, roll){       // none, basic or strong
  const H = HZ(), sh = H.swimmers?.[eid] || { none: 50, strong: 10 };
  let a = "basic";
  if (roll <= sh.none) a = "none"; else if (roll > 100 - sh.strong) a = "strong";
  if (seamanship >= (H.seamanship_strong ?? 40)) return "strong";
  if (seamanship >= (H.seamanship_basic ?? 20) && a === "none") return "basic";
  return a;
}
function hzSwimTarget(end, ability, band, armour, water = {}){   // water: {current, flotation, minutes, cold}
  const S = HZ().swim, { current, flotation = false, minutes = 0, cold = 0 } = water;
  let t = end + S.ability[ability] + S.load[band] + (S.armour[armour] || 0) + (S.current[current] || 0);
  if (flotation) t += S.flotation;
  const over = minutes - HZ().cold[cold].fail_after;
  if (over > 0) t -= 10 * (Math.floor(over / 10) + 1);
  return t;
}
function hzSwimStep(step, target, roll){             // {check, step}
  const k = skillCheck(target, "ordinary", roll), last = HZ().swim.steps.length - 1;
  let next;
  if (k.success) next = k.critical ? Math.max(0, step - 1) : step;
  else next = Math.min(last, step + (k.fumble ? 2 : 1));
  return { check: k, step: next };
}
const hzColdShock = (nerve, cold, roll) => skillCheck(nerve + HZ().cold[cold].shock, "ordinary", roll);
function hzFordRisk(water, band){ const F = HZ().fords[water]; return band >= F.from_band ? F.difficulty : null }
function hzClimbTarget(agi, fieldcraft, surface, band, armour){
  const C = HZ().climb;
  return agi + Math.floor(fieldcraft / 2) + C.surfaces[surface].mod + C.load[band] + (C.armour[armour] || 0);
}
const hzClimbSteps = (surface, height) => Math.max(1, Math.ceil(Math.trunc(height) / HZ().climb.surfaces[surface].step_m));
function hzFall(height, landing, shift, roll, locRoll){   // {severity, wound, zone}
  const F = HZ().falls, rows = F.heights;
  let i = rows.findIndex(r => height <= r.upto);
  i = Math.min(rows.length - 1, Math.max(0, i + shift));
  let sevI = rows[i].bands.findIndex(b => roll <= b);
  if (sevI < 0) sevI = rows[i].bands.length;
  const sev = F.severities[sevI], zone = F.landings[landing].zones.find(([to]) => locRoll <= to)[1];
  return { severity: sev, wound: F.wound[sev] ?? null, zone: sev === "none" ? null : zone };
}
function hzChaseStep(gap, aTarget, aRoll, bTarget, bRoll, aSpeed, bSpeed){   // {gap, opposed}
  const C = HZ().chase, o = opposedCheck(aTarget, "ordinary", aRoll, bTarget, bRoll), a = o.a, b = o.b;
  let move;
  if (o.winner === "a") move = -(a.critical ? 2 : 1);
  else if (b.success && !(a.success && a.margin === b.margin && a.critical === b.critical)) move = b.critical ? 2 : 1;
  else if (aSpeed > bSpeed) move = -1;
  else move = bSpeed > aSpeed ? 1 : 0;
  return { gap: Math.min(C.gaps.length - 1, Math.max(0, gap + move)), opposed: o };
}
