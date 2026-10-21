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
