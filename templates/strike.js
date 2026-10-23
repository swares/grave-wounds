/* The strike: the attack and defence rolls, then the wound's location, blow, severity and armour,
   as the rules decide them, with no page. makeStrike(DATA) gives the rules for the data bundle.

   resolveStrike(ctx, cmd, dice) -> {hit, dice, effects}
     ctx   the situation the page measures: the table and weapon, the location ranges (and the aimed
           zone's), the defender's armour kit, the range check, and each side's wound penalties.
     cmd   what the player declares: attack and defence percentages, aim, gap, a declared blow, the
           severity mode, a stray shot; and any dice he rolled himself (cmd.rolls: atk, def, loc, mech,
           sev, cover, misfire, stray). A die he did not roll is rolled with `dice`.
     dice  anything with randint(a, b): real dice in the page, seeded or scripted dice in a test.
   hit     what the page shows (S.hit), in the shape the page has always had.
   dice    every die the strike used, in the order rolled: {name, v, sides, by: "player" | "dice"}.
   effects what the page must do to its fighters afterwards: close in (rise from cover, toil), mark
           a skill used, close the free attack. The strike changes nothing itself.

   The wound takes its dice in the order gravewounds/engine.py roll_hit does (location, blow,
   severity, cover), so the same dice give the same wound in both; tools/strike/parity.py checks it.
   build.py puts this file into the roller at its STRIKE_JS marker; in Node it is a module. */

/* ----- pieces that need no data ----- */
const STRIKE_LADDER = ["stopped", "light", "serious", "critical"];
const strikeLook = (ranges, n) => ranges.find(r => n >= r.lo && n <= r.hi).id;
const strikeD2 = n => (n === 100 ? "00" : String(n).padStart(2, "0"));
const strikeLowerName = s => (/^[A-Z]{2}/.test(s) ? s : s.toLowerCase());   // "Bill" -> "bill", "MG" stays
function defenceRoll(defence, roll, penalty){
  const eff = Math.max(0, defence - penalty);
  return { effective: eff, roll, defended: roll <= eff, base: defence, penalty };
}
function grazeFx(fx){ return { ...fx, bleed: Math.max(0, fx.bleed - 1), pain: Math.max(0, fx.pain - 1), shock: false } }
function strikeDice(cmd, dice){                     // the dice a strike takes: the player's own if he gave one, else rolled
  const used = [], own = cmd.rolls || {};
  const take = (name, sides) => {
    const p = own[name], mine = Number.isInteger(p) && p >= 1 && p <= sides;
    const v = mine ? p : dice.randint(1, sides);
    used.push({ name, v, sides, by: mine ? "player" : "dice" });
    return v;
  };
  return { used, take };
}

function misfire(rc, take, effects, freeHit){     // wet priming: the shot is lost (text), or null
  const mf = rc.range ? rc.range.misfire : 0;
  if (!mf) return null;
  const mr = take("misfire", 100);
  if (mr > mf) return null;
  if (freeHit) effects.free = "misfire";
  return `Misfire: d100 ${strikeD2(mr)} against ${mf}% — the wet weather spoiled the priming. The shot is lost.`;
}
function strayShot(range, take){                  // after a miss: does the shot go into the first man in the way?
  if (!range?.stray || !(range.way || []).length) return null;
  const roll = take("stray", 100);
  return { id: range.way[0], roll, chance: range.stray, hit: roll <= range.stray };
}

function coverDigit(att, take){                    // the attack roll's units digit (0 is 10), else a d10 (as gravewounds.engine.cover_digit)
  const fromAtk = att.roll !== null && att.roll !== undefined;
  return { digit: fromAtk ? (att.roll % 10 || 10) : take("cover", 10), fromAtk };
}

function makeStrike(DATA){
  const CMB = DATA.combat, MATS = DATA.armor.materials;
  const LOC = Object.fromEntries(DATA.locations.map(l => [l.id, l]));
  const KITS = Object.fromEntries(DATA.armor.kits.map(k => [k.id, k]));

  /* ----- the pieces, as gravewounds/combat.py and engine.py ----- */
  function marginSeverity(margin, critical, wid, zone){
    if (critical) return "critical";
    const bands = CMB.margin_bands;
    let b = bands.default;
    if (DATA.weapons[wid].threat && bands.ballistic) b = bands.ballistic.find(x => x.zones.includes(zone));
    if (margin >= b.critical) return "critical";
    return margin >= b.serious ? "serious" : "light";
  }
  function attackRoll(attack, roll, penalty){
    const eff = Math.max(0, attack - penalty), critAt = Math.floor(eff * CMB.critical_fraction), hit = roll <= eff;
    return { effective: eff, roll, hit, critical: hit && roll <= critAt, margin: hit ? eff - roll : null, base: attack, penalty };
  }
  function armorAt(kitId, locId){ return KITS[kitId]?.layers?.[LOC[locId].armor] || [] }
  function armorSteps(mat, mech, wid){
    const w = DATA.weapons[wid], m = MATS[mat], th = m.threats || {};
    const steps = mech === "ballistic" && w.threat && w.threat in th ? th[w.threat] : m[mech];
    const defeat = w.armor_defeat?.[mech] || 0;
    return Math.max(0, steps - defeat);
  }
  function sevTiers(mech, zone, wid){
    if (wid && DATA.weapons[wid].threat) mech = "ballistic";   // firearms and explosives
    const tbl = DATA.severity_by_mechanism[mech]?.tables.find(t => t.zones.includes(zone));
    return tbl ? tbl.tiers : DATA.severity;
  }
  function isGraze(margin, critical){ return margin !== null && margin !== undefined && !critical && margin <= CMB.graze_margin }
  const cannotAttack = p => !!p && p.flags.some(f => f === "incapacitated" || CMB.states[f]?.no_attack);

  function attackBlock(att, w){                     // why the attacker cannot attack at all, or null
    const A = att?.pen;
    if (!A) return null;
    if (A.flags.includes("incapacitated")) return `${att.name} is incapacitated and cannot attack.`;
    if (cannotAttack(A)) return `${att.name} cannot attack: ${CMB.states[att.state].name.toLowerCase()}.`;
    if (A.flags.includes("cannot_wield") && w.melee !== "unarmed") return `${att.name} cannot hold a weapon in either hand.`;
    if (A.flags.includes("one_arm") && w.two_handed) return `${att.name} cannot use the ${strikeLowerName(w.short || w.name)} with an arm hurt (it takes both hands): defend only.`;
    return null;
  }

  // The attack and the defence: {end} if no wound follows, else {margin, crit, combat, roll}.
  function attackPhase(ctx, cmd, atkPct, take, effects){
    const rc = ctx.rc, freeHit = !!ctx.freeHit, w = DATA.weapons[ctx.weapon];
    const blocked = attackBlock(ctx.attacker, w) || misfire(rc, take, effects, freeHit);
    if (blocked) return { end: { blocked } };
    effects.closeIn = true;
    const A = ctx.attacker?.pen, D = ctx.defender?.pen;
    const ar = attackRoll(atkPct, take("atk", 100), (A ? A.attack : 0) + (rc.range ? rc.range.penalty : 0));
    const combat = { atk: ar, def: null, range: rc.range };
    if (!ar.hit){
      if (freeHit) effects.free = "miss";
      return { end: { miss: true, combat, stray: strayShot(rc.range, take) } };
    }
    effects.xp = "hit";
    const defPct = cmd.def ?? null;
    if (defPct !== null && !ar.critical){
      const dr = defenceRoll(defPct, take("def", 100), D ? D.defence : 0);
      combat.def = dr;
      if (dr.defended){
        effects.xp = "defended";
        if (freeHit) effects.free = "parried or dodged";
        return { end: { defended: true, combat } };
      }
    }
    return { margin: ar.margin, crit: ar.critical, combat, roll: ar.roll };
  }

  // What the declared aim costs (wounds.yaml combat.aim; as gravewounds.engine.roll_hit).
  function aimPlan(ctx, cmd, att){
    const stray = !!cmd.stray, plan = { zone: stray ? "" : cmd.aim || "", gap: !stray && !!cmd.gap, zonePaid: false, zoned: null, left: att.margin };
    plan.pays = () => att.margin === null || att.crit || plan.left >= CMB.aim.cost;
    plan.spend = () => { if (att.margin !== null && !att.crit) plan.left -= CMB.aim.cost };
    if (plan.zone && plan.pays() && ctx.aimRanges){ plan.zoned = ctx.aimRanges; plan.zonePaid = true; plan.spend() }
    return plan;
  }
  function severityOf(ctx, cmd, att, plan, mech, loc, take){   // {sev, rs}: from the margin, the GM's pick or the table
    const zone = LOC[loc].zone;
    if (cmd.stray || att.margin === null){
      const mode = cmd.stray ? "roll" : cmd.sev || "roll";
      if (mode !== "roll") return { sev: mode, rs: null };
      const rs = take("sev", 100);
      return { sev: sevTiers(mech, zone, ctx.weapon).find(x => rs >= x.d100[0] && rs <= x.d100[1]).id, rs };
    }
    return { sev: marginSeverity(plan.left, att.crit, ctx.weapon, zone), rs: null };
  }
  function armourOn(armour, sev, mech, att, take, wid){   // {armor, final}: the armour on the place hit lowers the severity
    const { layers, whole, gapped } = armour;
    if (!layers.length) return { armor: null, final: sev };
    const cd = whole || gapped ? { digit: null, fromAtk: att.roll !== null && att.roll !== undefined } : coverDigit(att, take);
    let hitLayer = null;
    if (whole) hitLayer = layers[0];
    else if (!gapped) hitLayer = layers.find(([, lo, hi]) => cd.digit * 10 >= lo && cd.digit * 10 <= hi) || null;
    const mat = hitLayer ? hitLayer[0] : null, steps = hitLayer ? armorSteps(mat, mech, wid) : 0;
    const final = STRIKE_LADDER[Math.max(0, STRIKE_LADDER.indexOf(sev) - steps)];
    return { armor: { mat, layers, rc: cd.digit, rcAtk: !whole && cd.fromAtk, covered: !!hitLayer, gapped: !!gapped, steps, from: sev, to: final }, final };
  }

  // The wound: the aim paid for, then location, blow, severity and armour.
  function woundPhase(ctx, cmd, att, take){
    const wid = ctx.weapon, w = DATA.weapons[wid], plan = aimPlan(ctx, cmd, att);
    const rl = take("loc", 100), loc = strikeLook(plan.zoned || ctx.ranges, rl);
    const layers = ctx.evidence ? [] : armorAt(ctx.armor, loc);
    const whole = layers.length === 1 && layers[0][1] === 1 && layers[0][2] === 100;
    const gapped = plan.gap && layers.length > 0 && !whole && plan.pays();   // a gap is paid for only where there is one
    if (gapped) plan.spend();
    const blow = w.choose && cmd.blow && w.mechanisms[cmd.blow] ? cmd.blow : null;   // a blow the attacker declared, or rolled
    const rm = blow ? null : take("mech", 100), mech = blow || strikeLook(w.mech_ranges, rm);
    const { sev, rs } = severityOf(ctx, cmd, att, plan, mech, loc, take);
    const { armor, final } = armourOn({ layers, whole, gapped }, sev, mech, att, take, wid);
    const grazed = final !== "stopped" && isGraze(plan.left, att.crit);
    const fx0 = final === "stopped" ? null : DATA.wounds[`${LOC[loc].class}|${mech}|${final}`];
    const fx = fx0 && grazed ? grazeFx(fx0) : fx0;
    return { loc, mech, sev: final, rolled: sev, fx, armor, combat: att.combat, graze: grazed, range: ctx.rc.range, free: !!ctx.freeHit, strayHit: !!cmd.stray,
      rolls: { loc: rl, mech: rm, sev: rs },
      aim: { zone: plan.zone, zonePaid: plan.zonePaid, gap: plan.gap, gapPaid: gapped, margin: att.margin, left: plan.left },
      weapon: wid, table: ctx.table, ltable: ctx.ltable, mods: ctx.mods };
  }

  function resolveStrike(ctx0, cmd, dice){
    const ctx = { ...ctx0, rc: ctx0.rc || { range: null } };
    const { used, take } = strikeDice(cmd, dice);
    const effects = { closeIn: false, xp: null, free: null };
    const done = hit => ({ hit, dice: used, effects });
    const stray = !!cmd.stray;
    const base = { weapon: ctx.weapon, table: ctx.table, ltable: ctx.ltable, mods: ctx.mods, aim: stray ? "" : cmd.aim || "", gap: !stray && !!cmd.gap, stray };
    if (ctx.rc.blocked) return done({ ...base, fx: null, blocked: ctx.rc.blocked });
    base.range = ctx.rc.range;
    let att = { margin: null, crit: false, combat: null, roll: null };
    const atkPct = stray ? null : (cmd.atk ?? null);
    if (atkPct !== null){
      att = attackPhase(ctx, cmd, atkPct, take, effects);
      if (att.end) return done({ ...base, fx: null, ...att.end });
    }
    return done(woundPhase(ctx, cmd, att, take));
  }

  return { resolveStrike, attackRoll, defenceRoll, marginSeverity, armorAt, armorSteps, sevTiers, grazeFx, isGraze, cannotAttack };
}

if (typeof module !== "undefined") module.exports = { makeStrike };   // Node (the tests); the page has no `module`
