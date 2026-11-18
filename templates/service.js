/* A season of service: the same rules as gravewounds/service.py, taking the dice in the same order.
   makeService(SV, RULES) -> the rules by name. SV is the team builder's service bundle: {wars (data/service),
   mix: {table id: [[weapon, pct], ...]} (each war's table's weapon_mix entries that name a weapon),
   steps, unfit_from (disease.yaml)}. RULES is makeTravelRules (templates/travelrules.js) over the
   disease data: the camp-disease track a sick man runs. rng(): a d100. build.py puts this file into
   the team builder at its SERVICE_JS marker; in Node it is a module (tools/service/test.js). */
function makeService(SV, RULES){
  const MONTH = { spring: 3, summer: 6, autumn: 9, winter: 12 };
  const DAY_MS = 86400000;
  const war = wid => SV.wars[wid];
  const warsFor = (eid, region) => Object.values(SV.wars).filter(W => W.era === eid && (region == null || W.regions.includes(region)));
  const season = (W, sid) => W.seasons.find(s => s.id === sid);
  function seasonStart(sid){                     // '1811-spring' -> 1 March 1811, as a day count (UTC)
    const [y, q] = sid.split("-");
    return Date.UTC(+y, MONTH[q] - 1, 1) / DAY_MS;
  }
  const weeks = W => Math.floor(W.season_days / 7);
  function actionWeek(W, sid, aid){              // the week of the season an action falls in
    const [y, m, d] = W.actions[aid].date.split("-").map(Number);
    const n = Math.floor((Date.UTC(y, m - 1, d) / DAY_MS - seasonStart(sid)) / 7);
    return Math.max(0, Math.min(weeks(W) - 1, n));
  }
  function hitPct(W, aid, position = "line", unit = null, share = null){   // his % chance of being hit, or null
    const a = W.actions[aid];
    if (unit != null) return Math.trunc(a.units[unit].share);
    const s = a.share ?? share;
    if (s == null) return null;
    return Math.min(W.cap, pyRound(s * W.positions[position].mult));
  }
  function pyRound(x){                           // Python's round(): halves to even
    const f = Math.floor(x), r = x - f;
    if (Math.abs(r - 0.5) > 1e-9) return Math.round(x);
    return f % 2 === 0 ? f : f + 1;
  }
  const inWeek = (n, wk, of) => Math.floor((wk + 1) * n / of) > Math.floor(wk * n / of);
  function factors(W, s, wk){                    // the disease track's factors in a week of the season
    const st = W.states[s.state], f = [];
    if (s.hygiene === "poor" || s.hygiene === "good") f.push(s.hygiene);
    if (st.staying){
      f.push("staying");
      if (s.hygiene === "poor") f.push("crowded");
    }
    for (const [k, n] of Object.entries(s.factors || {})) if (inWeek(n, wk, weeks(W))) f.push(k);
    return f;
  }
  function dayCtx(W, s, wk){
    const st = W.states[s.state];
    return { care: st.care, marched: st.marched, wet_cold: factors(W, s, wk).includes("cold_wet"), filth: s.hygiene === "poor" };
  }
  function weaponFor(W, roll){                   // d100 on the war's table's weapon_mix
    const mix = SV.mix[W.table], total = mix.reduce((t, [, p]) => t + p, 0);
    let cum = 0;
    for (const [w, p] of mix){
      cum += p;
      if (roll * total <= cum * 100) return w;
    }
    return mix[mix.length - 1][0];
  }
  function worstStep(h){                         // as disease.worst_step: his worst step of sickness that shows
    const shown = h.cases.filter(c => c.inc === 0 && c.step > 0 && c.d !== "wound").map(c => c.step);
    return shown.length ? SV.steps[Math.max(...shown)] : null;
  }
  function unfit(h){
    const st = worstStep(h);
    return st !== null && SV.steps.indexOf(st) >= SV.steps.indexOf(SV.unfit_from);
  }
  function serve(wid, sid, men, rolled, rng){    // a season for the team, as service.serve
    const W = war(wid), s = season(W, sid), chance = W.small_war.chance[s.state], smallRoll = rng();
    const out = { small: smallRoll <= chance, small_roll: smallRoll, chance, men: [] };
    if (out.small && (W.small_fights || []).length) out.fight = smallFight(W, s.state, rng);
    const acts = s.actions.filter(a => rolled.includes(a))
      .sort((a, b) => actionWeek(W, sid, a) - actionWeek(W, sid, b) || s.actions.indexOf(a) - s.actions.indexOf(b));
    for (const m of men) out.men.push(manSeason(W, s, m, acts, rng));
    return out;
  }
  const between = (lo, hi, roll) => lo + Math.floor((roll - 1) * (hi - lo + 1) / 100);
  function smallFight(W, state, rng, fid = null){   // the season's small fight, as service.small_fight
    const all = W.small_fights, fitting = all.filter(f => f.states.includes(state)), fits = fitting.length ? fitting : all;
    let roll = null, f;
    if (fid === null){
      roll = rng();
      const total = fits.reduce((t, x) => t + x.weight, 0);
      let cum = 0;
      f = fits[fits.length - 1];
      for (const x of fits){
        cum += x.weight;
        if (roll * total <= cum * 100){ f = x; break }
      }
    } else f = all.find(x => x.id === fid);
    const out = { id: f.id, roll, side: between(...f.side.men, rng()), foes: f.foes.map(o => between(...o.men, rng())), surprise_roll: null, surprised: false };
    if (f.surprise){
      out.surprise_roll = rng();
      out.surprised = out.surprise_roll <= f.surprise.chance;
    }
    return out;
  }
  function manSeason(W, s, m, acts, rng){
    let h = RULES.newHealth();
    const r = { name: m.name, dead: null, dead_week: null, sick_days: 0, worst: null, hits: [], missed: [], rolls: [] };
    const end = m.endurance ?? undefined, sid = s.id;   // none: the typical man's
    for (let wk = 0; wk < weeks(W); wk++){
      for (const aid of acts.filter(a => actionWeek(W, sid, a) === wk)) action(W, aid, m, h, r, rng);
      const f = factors(W, s, wk), ctx = dayCtx(W, s, wk);
      h = RULES.healthWeek(h, 1, f, rng, end).health;
      for (let k = 0; k < 7; k++){
        const res = RULES.healthDay(h, ctx, rng, end);
        h = res.health;
        const dead = Object.keys(res.events.dead);
        if (dead.length){ r.dead = dead[0]; r.dead_week = wk; return r }
        if (h.cases.some(c => c.inc === 0 && c.step > 0)) r.sick_days++;
      }
    }
    r.worst = worstStep(h);
    return r;
  }
  function action(W, aid, m, h, r, rng){         // one unplayed action: missed, or his hit roll
    if (r.hits.length){ r.missed.push({ action: aid, why: "wounded" }); return }
    if (unfit(h)){ r.missed.push({ action: aid, why: "sick" }); return }
    const pct = hitPct(W, aid, m.position || "line", (m.unit || {})[aid] ?? null, (m.share || {})[aid] ?? null);
    if (pct === null){ r.missed.push({ action: aid, why: "no share" }); return }
    const roll = rng();
    r.rolls.push({ action: aid, pct, roll });
    if (roll <= pct) r.hits.push({ action: aid, pct, roll, weapon: weaponFor(W, rng()) });
  }
  return { war, warsFor, season, seasonStart, weeks, actionWeek, hitPct, inWeek, factors, dayCtx, weaponFor, worstStep, serve, between, smallFight };
}

if (typeof module !== "undefined") module.exports = makeService;   // Node (the tests); the page has no `module`
