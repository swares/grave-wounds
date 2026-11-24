/* A season of service: the same rules as gravewounds/service.py, taking the dice in the same order.
   makeService(SV, RULES) -> the rules by name. SV is the team builder's service bundle: {wars (data/service),
   mix: {war id: [[weapon, pct], ...]} (the war's own weapon_mix, else its table's: entries that name a weapon),
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
  function vacancyPct(W, sid, at){                 // the % chance of a vacancy a rank this season (as service.vacancy_pct; data/ranks.yaml season_vacancies)
    const R = SV.vacancies;
    if (!R) return 0;
    const s = season(W, sid), pct = at.reduce((t, a) => t + (hitPct(W, a) ?? 0), 0) + ((W.wastage || {})[s.state] || 0) + (R.background || 0);
    return Math.min(Math.trunc(R.cap ?? 90), pyRound(pct));
  }
  function takenPct(W, aid, position = "line", unit = null){   // his % chance of being taken, unhit (as service.taken_pct)
    const a = W.actions[aid];
    if (unit != null) return a.units[unit].taken != null ? Math.trunc(a.units[unit].taken) : 0;
    if (!a.taken) return 0;
    return Math.min(W.cap, pyRound(a.taken * W.positions[position].mult));
  }
  function desertPct(W, sid){                    // a follower's % chance of deserting in the season (as service.desert_pct)
    const s = season(W, sid);
    return "desertion" in s ? s.desertion : (W.desertion?.share ?? 0);
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
    return { care: st.care, marched: st.marched, wet_cold: factors(W, s, wk).includes("cold_wet"), filth: s.hygiene === "poor", leech: W.medicine || 0 };   // the era's medicine, on every recovery check
  }
  function weaponFor(W, roll){                   // d100 on the war's table's weapon_mix
    const mix = SV.mix[W.id], total = mix.reduce((t, [, p]) => t + p, 0);
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
  function woundStep(h){                         // as service.wound_step: his worst battle wound on the track
    const shown = h.cases.filter(c => (c.d === "wound" || c.d === "fever") && c.step > 0).map(c => c.step);
    return shown.length ? SV.steps[Math.max(...shown)] : null;
  }
  function unfit(h){                              // too sick or too badly wounded to march or fight
    const at = SV.steps.indexOf(SV.unfit_from);
    return h.cases.some(c => c.inc === 0 && c.step >= at);
  }
  function postureOf(p){                          // the team's posture through the season (data/posture.yaml), as service.posture_of
    const P = SV.posture || {};
    return (P.postures || {})[p || P.default || "duty"] || { small: 1, hit: 1, ticks: 0, promotion: 0 };
  }
  function serve(wid, sid, men, rolled, rng, posture = null){   // a season for the team, as service.serve; posture: its small scales the small fight's chance, its hit each man's hit chance
    const W = war(wid), s = season(W, sid), P = postureOf(posture), chance = Math.min(100, pyRound(W.small_war.chance[s.state] * P.small)), smallRoll = rng();
    const out = { small: smallRoll <= chance, small_roll: smallRoll, chance, men: [] };
    if (out.small && (W.small_fights || []).length) out.fight = smallFight(W, s.state, rng);
    const acts = s.actions.filter(a => rolled.includes(a))
      .sort((a, b) => actionWeek(W, sid, a) - actionWeek(W, sid, b) || s.actions.indexOf(a) - s.actions.indexOf(b));
    for (const m of men) out.men.push(manSeason(W, s, { ...m, hit_mult: P.hit, deed_mult: P.deed ?? 1 }, acts, rng));
    return out;
  }
  const between = (lo, hi, roll) => lo + Math.floor((roll - 1) * (hi - lo + 1) / 100);
  function smallFight(W, state, rng, fid = null){   // the season's small fight, as service.small_fight
    const all = W.small_fights, rolled = all.filter(f => !f.edge_only), fitting = rolled.filter(f => f.states.includes(state)), fits = fitting.length ? fitting : rolled;   // an edge's own fights come only with their battle
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
  function startHealth(m){                       // his case carried from the last season, or well (as service.start_health)
    if (!m.health) return RULES.newHealth();
    const h = RULES.copyHealth(m.health);
    h.dead = 0;
    return h;
  }
  function manSeason(W, s, m, acts, rng){
    let h = startHealth(m);
    const r = { name: m.name, dead: null, dead_week: null, sick_days: 0, wound: null, worst: null, hits: [], taken: null, missed: [], rolls: [], deeds: [], health: null };
    const end = m.endurance ?? undefined, sid = s.id;   // none: the typical man's
    for (let wk = 0; wk < weeks(W); wk++){
      for (const aid of acts.filter(a => actionWeek(W, sid, a) === wk)){
        action(W, aid, m, h, r, rng);
        if (r.taken){ r.taken.week = wk; r.worst = worstStep(h); r.wound = woundStep(h); r.health = h; return r }   // a prisoner: his season is over
      }
      if (wk === Math.floor(weeks(W) / 2) && (W.wastage || {})[s.state]) wastage(W, s, h, r, rng);
      const f = factors(W, s, wk);
      let ctx = dayCtx(W, s, wk);
      if (unfit(h)) ctx = { ...ctx, care: "shelter", marched: false, wet_cold: false };   // too sick to march or fight: in hospital this week
      h = RULES.healthWeek(h, 1, f, rng, end).health;
      for (let k = 0; k < 7; k++){
        const res = RULES.healthDay(h, ctx, rng, end);
        h = res.health;
        const dead = Object.keys(res.events.dead);
        if (dead.length){ r.dead = dead[0]; r.dead_week = wk; return r }
        if (h.cases.some(c => c.inc === 0 && c.step > 0 && c.d !== "wound")) r.sick_days++;
      }
    }
    r.worst = worstStep(h); r.wound = woundStep(h); r.health = h;     // his health carried into the next season
    return r;
  }
  function wastage(W, s, h, r, rng){             // the season's wastage in the line, as service._wastage
    if (r.hits.length || unfit(h)) return;
    const pct = W.wastage[s.state], roll = rng();
    r.rolls.push({ action: "wastage", pct, roll });
    if (roll <= pct) r.hits.push({ action: "wastage", pct, roll, weapon: weaponFor(W, rng()) });
  }
  function edgeScaled(W, pct, unit, edge){       // a unit's own figure, scaled by where an edge put him within it (as service._edge_scaled)
    if (pct === null || unit === null || !edge) return pct;
    return Math.min(W.cap, pyRound(pct * W.positions[edge].mult));
  }
  function action(W, aid, m, h, r, rng){         // one unplayed action: missed, or his hit roll
    if (r.hits.length){ r.missed.push({ action: aid, why: "wounded" }); return }
    if (unfit(h)){ r.missed.push({ action: aid, why: "sick" }); return }
    const edge = m.pos_at?.[aid] || null, pos = edge || m.position || "line";   // where he stands at this action (an edge's choice), else for the season
    const unit = m.unit?.[aid] ?? null;
    let pct = edgeScaled(W, hitPct(W, aid, pos, unit, m.share?.[aid] ?? null), unit, edge);
    if (pct !== null && (m.hit_mult ?? 1) !== 1) pct = Math.min(W.cap, pyRound(pct * m.hit_mult));   // the team's posture
    if (pct === null){ r.missed.push({ action: aid, why: "no share" }); return }
    const roll = rng();
    r.rolls.push({ action: aid, pct, roll });
    if (roll <= pct){ r.hits.push({ action: aid, pct, roll, weapon: weaponFor(W, rng()) }); return }
    const t = edgeScaled(W, takenPct(W, aid, pos, unit), unit, edge);
    if (t){ const tr = rng(); if (tr <= t){ r.taken = { action: aid, pct: t, roll: tr }; return } }   // came through unhit: taken?
    const dp = deedPct(pos, m.deed_mult ?? 1);
    if (dp){ const dr = rng(); if (dr <= dp) r.deeds.push({ action: aid, pct: dp, roll: dr, position: pos }) }   // unhit and free: a deed there?
  }
  function deedPct(pos, mult = 1, small = false){   // his % chance of a deed at a rolled action (or small fight), as service.deed_pct
    const D = SV.deeds;
    if (!D) return 0;
    const base = small ? (D.small || 0) : ((D.action || {})[pos] || 0);
    return Math.min(100, pyRound(base * mult));
  }
  return { postureOf, war, warsFor, season, seasonStart, weeks, actionWeek, hitPct, vacancyPct, deedPct, takenPct, desertPct, inWeek, factors, dayCtx, weaponFor, worstStep, woundStep, unfit, serve, between, smallFight };
}

if (typeof module !== "undefined") module.exports = makeService;   // Node (the tests); the page has no `module`
