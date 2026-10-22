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
function haggle(price, persuade, aRoll, bRoll, seller = null, selling = false){   // {outcome: win | critical | list | no_sale | cheated, price, opposed}
  const H = CHK().haggle || { seller: 50, win: -0.1, critical: -0.25 };
  const o = opposedCheck(persuade, "ordinary", aRoll, seller === null ? H.seller : seller, bRoll);
  if (selling) return haggleSell(H, price, o);
  if (o.a.fumble) return { outcome: "no_sale", price: null, opposed: o };
  if (o.winner === "a"){ const kind = o.a.critical ? "critical" : "win"; return { outcome: kind, price: price > 0 ? Math.max(0.25, Math.floor(price * (1 + H[kind]) * 4 + 0.5) / 4) : 0, opposed: o } }
  return { outcome: "list", price, opposed: o };
}
function haggleSell(H, price, o){                   // selling loot: a tenth more on a win, a quarter on a critical; a fumble, a fence cheats him
  const S = H.sell || { win: 0.1, critical: 0.25, fumble: -0.25 };
  let kind = "list";
  if (o.a.fumble) kind = "cheated";
  else if (o.winner === "a") kind = o.a.critical ? "critical" : "win";
  const rate = { cheated: S.fumble, win: S.win, critical: S.critical }[kind] || 0;
  return { outcome: kind, price: Math.floor(price * (1 + rate) * 4 + 0.5) / 4, opposed: o };
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
  if (c.course_rank === r.id && rkIndex(c.rank) < idx) return [true, null];   // an officer's course opens it
  if (rkIndex(c.rank) !== idx - 1) return [false, "not the rank below"];
  if (r.deed_only && !c.deed) return [false, "only for a deed"];
  if (!c.deed && (c.rank_days || 0) < (r.years || 0) * (R.days_a_year || 365)) return [false, "too soon"];
  if (r.letters && (c.skills.letters || 0) < (R.literate ?? 20)) return [false, "cannot read and write"];
  return [true, null];
}
function rkPresence(R, c){                         // a promotion's Presence, into his characteristics' changes, up to the cap (ranks.py _presence)
  const P = R.presence; if (!P || !c.stat_mods) return;
  const gain = Math.min(P.per_rank, P.cap - (c.pres_rank || 0));
  if (gain > 0){ c.stat_mods.pres = (c.stat_mods.pres || 0) + gain; c.pres_rank = (c.pres_rank || 0) + gain }
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
        if (c.patron_help) mod += TD.patrons?.promotion_bonus ?? 20;   // his patron's word (data/patrons.yaml)
        if (r.unlettered && (c.skills.letters || 0) < (R.literate ?? 20)) mod += r.unlettered;
        const k = skillCheck((c.skills.command || 0) + mod, r.diff || "ordinary", rng.randint(1, 100));
        out.push({ name: c.name, to: r.id, roll: k.roll, target: k.target, success: k.success });
        if (k.success){ won = c; break }
      }
      if (!won) break;
      const old = rkIndex(won.rank);                  // the rank he leaves (one below, or lower for a course's)
      won.rank = r.id; won.rank_days = 0; won.deed = false; won.patron_help = false; delete won.course_rank;
      rkPresence(R, won);
      vacancies[r.id] -= 1;
      if (old > 0) vacancies[L[old].id] = (vacancies[L[old].id] || 0) + 1;
    }
  }
  for (const c of team) c.deed = false;
  return out;
}
function rkPurchase(region, c, rid){                // what buying rank rid costs (the coin's smallest unit), less the commission he holds; null where not bought
  const P = RK().purchase || {};
  if (!(P.eras || []).includes(TD.era.id) || !(P.regions || []).includes(region) || !(rid in (P.prices || {}))) return null;
  const held = c.bought ? P.prices[c.bought] || 0 : 0;
  return Math.max(0, P.prices[rid] - held);
}
function rkCanBuy(region, c, vacancies){            // [rank he may buy, null] or [null, why not]
  const L = rkLadder(), i = rkIndex(c.rank), P = RK().purchase || {};
  for (let idx = i + 1; idx < L.length; idx++){
    const rid = L[idx].id;
    if (rkPurchase(region, c, rid) === null) continue;
    if ((vacancies[rid] || 0) <= 0) return [null, `no vacancy for ${L[idx].name.toLowerCase()}`];
    const [ok, why] = rkEligible(c, idx), first = idx === L.findIndex(r => r.id in P.prices);
    if (ok || why === "too soon" || (first && why === "not the rank below")) return [rid, null];
    return [null, why];
  }
  return [null, "nothing to buy"];
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
function trTeaches(m, skill){                      // a language master teaches any tongue ("tongue:<id>")
  if (m.skill === "tongue") return (m.eras || [TD.era.id]).includes(TD.era.id) && (skill === null || skill.startsWith("tongue:"));
  return TD.era.skills.some(s => s.id === m.skill) && (skill === null || m.skill === skill);
}
function trCourses(region, place){                 // the courses a man of this army can go on, where the team is
  return (TRN().courses || []).filter(k => k.eras.includes(TD.era.id) && (k.regions || [region]).includes(region) && (k.served || place === null || !k.places || k.places.includes(place)));
}
function trCourse(c, cid){                          // {gains, served, fee, rank}: c changed in place
  const k = TRN().courses.find(x => x.id === cid), have = new Set(TD.era.skills.map(s => s.id));
  const gains = Object.fromEntries(Object.entries(k.gains || {}).filter(([s]) => have.has(s)));
  for (const [s, n] of Object.entries(gains)) c.gains[s] = (c.gains[s] || 0) + n;
  if (k.rank) c.course_rank = k.rank;
  finishChar(c);
  return { gains, served: k.served ? k.weeks * 7 : 0, fee: k.fee || 0, rank: k.rank || null };
}
const trMasters = (place, skill = null) => (TRN().masters || []).filter(m => trTeaches(m, skill) && (place === null || m.places.includes(place)));
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
const WTS = () => TD.weights || {};
function ldItemKg(row){                             // what a bought row weighs (0: eaten, a lodging, a fare, a service, an animal)
  const W = WTS();
  if ((W.not_carried || []).includes(row.cat)) return 0;
  if ("kg" in row) return row.kg;
  const p = (W.patterns || []).find(x => new RegExp(x.match, "i").test(row.name));
  return p ? p.kg : W.categories?.[row.cat] ?? 0.5;
}
function ldAnimal(row){                             // the pack animal or vehicle a horse or travel row buys, or null
  if (row.cat !== "horse" && row.cat !== "travel") return null;
  return (WTS().animals || []).find(a => new RegExp(a.match, "i").test(row.name))?.id || null;
}
const ldCoinKg = (eid, days) => Math.max(0, days) * (WTS().coin_kg_day?.[eid] ?? 0);
const ldCarryKg = animals => (animals || []).reduce((t, a) => t + ((WTS().animals || []).find(x => x.id === a)?.load || 0), 0);
function ldCarried(eid, order, kitClass, extra = 0, carry = 0){   // his load less what his animals carry, never below his fighting order and armour
  const total = ldLoadKg(eid, order, kitClass, extra);
  return carry ? Math.max(ldLoadKg(eid, "fighting", kitClass, 0), total - carry) : total;
}
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
function stAmount(source, mods){                    // a source's Strain, a combat day's changed by his modifiers (summed, times 1 + the sum)
  const S = STR(), base = S.sources[source].strain;
  if (!(S.combat || []).includes(source)) return base;
  const sum = [...new Set(mods)].reduce((a, m) => a + (S.mods?.[m]?.add || 0), 0);
  return Math.max(0, base * (1 + sum));
}
function xpStress(pid, source, nerve, why, extra = []){   // a man takes a source's Strain (the shared store), with his own modifiers and any of the moment's: -> the checks made
  if (!pid || !TD.stress) return [];
  const all = readXp(), x = xpOf(all, pid), st = (x.stress ||= stNew()), amount = stAmount(source, [...(x.strainMods || []), ...extra]);
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
function hzFordWater(water, fd, fc){               // a ford's {depth, current, band} at fractions of its water's span (hazards.py ford_water)
  const F = HZ().fords, W = F.water[water], r1 = x => Math.floor(x * 10 + 0.5) / 10;
  const depth = r1(W.depth[0] + fd * (W.depth[1] - W.depth[0])), current = r1(W.current[0] + fc * (W.current[1] - W.current[0]));
  return { depth, current, band: F.currents.find(b => current <= b.upto) };
}
function hzFordRisk(depth, bandId, loadBand, mounted){   // the difficulty he crosses at, or null: deeper than he wades, anyone; else a heavy load
  const F = HZ().fords, b = F.currents.find(x => x.id === bandId), deep = depth > F.wade[mounted ? "mounted" : "foot"];
  return deep || loadBand >= F.from_band ? b.difficulty : null;
}
const hzHorseLost = (bandId, roll) => roll <= HZ().fords.currents.find(x => x.id === bandId).horse;
function hzWaterCold(high, low, flooded){          // the row of cold for the week's water
  const mean = (high + low) / 2, at = HZ().fords.cold_at, i = at.findIndex(t => mean > t);
  return Math.min(at.length, (i < 0 ? at.length : i) + (flooded ? 1 : 0));
}
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

/* Languages (as gravewounds/languages.py, data TD.languages): his own tongue at `native`, never
   ticked; others a percentage read in bands; a related tongue known at a share; talk skills capped
   by the tongue; words across tongues at the best tongue two men share; passing as a native. */
const LG = () => TD.languages || {};
const lgCap = t => LG().tongues[t]?.cap ?? (LG().max ?? 85);
const byCode = (a, b) => (a < b ? -1 : Number(a > b));     // as Python's sorted: by code point
function lgSet(c, t, v){ if (t !== c.native) c.tongues[t] = Math.max(c.tongues[t] || 0, v) }
function lgArmy(eid, region){ return LG().armies?.[eid]?.[region] || { own: [], others: [] } }
function lgRoll(eid, region, trait, drawback, rng){   // {native, tongues}: the dice as languages.py roll
  const L = LG(), A = lgArmy(eid, region), T = L.traits || {}, tr = T[trait] || {}, dr = T[drawback] || {};
  const native = lgNative(A, dr, rng.randint(1, 100));
  const c = { native, tongues: { [native]: L.native ?? 90 } };
  for (const [t, chance, [lo, hi]] of A.others || []){
    if (!(t in c.tongues) && rng.randint(1, 100) <= chance) c.tongues[t] = rng.randint(lo, hi);
  }
  for (const row of [tr, dr]) lgTraitTongues(c, A, row, rng);
  return c;
}
function lgNative(A, dr, r){                       // his own tongue: the drawback's list, or the army's shares
  if (dr.own?.length) return dr.own[Math.floor((r - 1) * dr.own.length / 100)];
  let acc = 0;
  for (const [t, share] of A.own){ acc += share; if (r <= acc) return t }
  return A.own[A.own.length - 1][0];
}
function lgExtra(c, A, row, rng){                  // a background's extra tongues, from his army's he lacks
  const pool = [...new Set([...A.own.map(x => x[0]), ...(A.others || []).map(x => x[0])])];
  for (let k = 0; k < row.extra; k++){
    const left = pool.filter(t => !(t in c.tongues));
    if (!left.length) return;
    const t = left[Math.floor((rng.randint(1, 100) - 1) * left.length / 100)];
    c.tongues[t] = rng.randint(row.range[0], row.range[1]);
  }
}
function lgTraitTongues(c, A, row, rng){           // what a trait or drawback gives
  if (row.extra) lgExtra(c, A, row, rng);
  if (row.enemy && A.enemy) lgSet(c, A.enemy, rng.randint(row.enemy[0], row.enemy[1]));
  for (const [t, v] of Object.entries(row.also || {})) lgSet(c, t, v);
  for (const [t, [lo, hi]] of Object.entries(row.has || {})) lgSet(c, t, rng.randint(lo, hi));
}
function lgValue(tongues, t){                      // his own figure, or a share of a related tongue
  let best = tongues[t] || 0;
  for (const [a, b, share] of LG().related || []){
    let other = null;
    if (a === t) other = b; else if (b === t) other = a;
    if (other && other in tongues) best = Math.max(best, Math.trunc(tongues[other] * share));
  }
  return best;
}
const lgBand = v => LG().bands.findLast(b => v >= b.from).name;
function lgShared(a, b){                           // [tongue, figure]: the best two men share
  const ids = new Set([...Object.keys(a), ...Object.keys(b)]);
  for (const r of LG().related || []){ ids.add(r[0]); ids.add(r[1]) }
  let best = null, bv = 0;
  for (const t of [...ids].sort(byCode)){
    const v = Math.min(lgValue(a, t), lgValue(b, t));
    if (v > bv){ best = t; bv = v }
  }
  return [best, bv];
}
const lgTalk = (skill, tongues, native, t) => (t === native ? skill : Math.min(skill, lgValue(tongues, t)));
function lgWords(v, roll, book = false, closed = false, diff = "ordinary"){   // {check, reading: full | meaning | gist | error}
  if (book && closed){ v = Math.max(v, LG().phrase_book ?? 25); diff = "easy" }
  const k = skillCheck(v, diff, roll);
  let reading = "gist";
  if (k.critical) reading = "full"; else if (k.success) reading = "meaning"; else if (k.fumble) reading = "error";
  return { check: k, reading };
}
const lgGrade = v => LG().passing.find(g => v >= g.from);
function lgPassing(v, watch, aRoll, bRoll){        // {grade, opposed (null: he cannot pass), passed}
  const g = lgGrade(v);
  if (!g.diff) return { grade: g.name, opposed: null, passed: false };
  const o = opposedCheck(v, g.diff, aRoll, watch, bRoll);
  return { grade: g.name, opposed: o, passed: o.winner === "a" };
}
const lgEscapeBonus = v => LG().escape_home.find(e => v >= e.from).mod;
function lgSeason(c, ticks, rng, gain = [1, 3]){   // [{tongue, roll, was, gain}]: his ticked tongues, by id
  const out = [];
  for (const t of [...new Set(ticks.filter(k => k.startsWith("tongue:")).map(k => k.slice(7)))].sort(byCode)){
    if (t === c.native || !LG().tongues[t]) continue;
    const was = c.tongues[t] || 0, r = rng.randint(1, 100);
    const up = r > was && was < lgCap(t) ? rng.randint(gain[0], gain[1]) : 0;
    c.tongues[t] = Math.min(lgCap(t), was + up);
    out.push({ tongue: t, roll: r, was, gain: c.tongues[t] - was });
  }
  return out;
}

/* Standing with patrons (as gravewounds/patrons.py, data TD.patrons): d100 Standing with each
   patron, read in bands; a favour at Standing + Persuade / 10 spends its cost (a critical nothing,
   a fumble offends him); events move it; rivals oppose; each season the patron's fate by era and
   each client's lot. */
const PT = () => TD.patrons || {};
const ptClamp = v => Math.max(0, Math.min(PT().max ?? 95, v));
const ptBand = v => PT().bands.findLast(b => v >= b.from).name;
const ptFavourRow = fid => PT().favours.find(f => f.id === fid);
function ptFavour(standing, persuade, fid, roll){   // {check, granted, offended, standing}
  const P = PT(), F = ptFavourRow(fid);
  const k = skillCheck(standing + Math.floor(persuade / (P.persuade_div ?? 10)), F.difficulty, roll);
  let after = standing;
  if (k.success && !(k.critical && (P.critical_free ?? true))) after = standing - F.cost;
  else if (k.fumble) after = standing + (P.offended ?? -10);
  return { check: k, granted: k.success, offended: k.fumble, standing: ptClamp(after) };
}
function ptMove(standing, event, rng, amount = 0){  // {standing, enemy}: a deed rolls its dice
  const E = PT().events[event];
  if ("to" in E) return { standing: E.to, enemy: !!E.enemy };
  let add = E.add ?? 0;
  if (E.dice) add = rng.randint(E.dice[0], E.dice[1]);
  else if (E.per_days) add = Math.floor(amount / E.per_days);
  else if (E.per) add = Math.trunc(amount) * E.per;
  return { standing: ptClamp(standing + add), enemy: false };
}
const ptRival = (a, b, aRoll, bRoll) => opposedCheck(a, "ordinary", aRoll, b, bRoll);
function ptFate(eid, roll){                         // the patron's fate this season, or null
  let acc = 0;
  for (const r of PT().fate?.[eid] || []){ acc += r.chance; if (roll <= acc) return r.id }
  return null;
}
function ptFateName(eid, fid){
  const row = (PT().fate?.[eid] || []).find(r => r.id === fid);
  return row?.name || PT().fates[fid].name;
}
function ptClient(fid, standing, roll = null, follow = true){   // {standing, result}
  const how = PT().fates[fid].clients;
  if (how === "ruin") return roll !== null && roll <= standing ? { standing: 0, result: "ruined" } : { standing: Math.floor(standing / 2), result: "clear" };
  if (how === "choose") return follow ? { standing, result: "follows" } : { standing: 0, result: "stays" };
  return { standing: Math.floor(standing / 2), result: how };
}
