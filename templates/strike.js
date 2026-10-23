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
   severity, cover), so the same dice give the same wound in both; tools/strike_test.js checks it.
   build.py puts this file into the roller at its STRIKE_JS marker. */
function makeStrike(DATA){
  const CMB = DATA.combat, MATS = DATA.armor.materials;
  const LOC = Object.fromEntries(DATA.locations.map(l => [l.id, l]));
  const KITS = Object.fromEntries(DATA.armor.kits.map(k => [k.id, k]));
  const LADDER = ["stopped", "light", "serious", "critical"];
  const look = (ranges, n) => ranges.find(r => n >= r.lo && n <= r.hi).id;

  /* ----- the pieces, as gravewounds/combat.py and engine.py ----- */
  function marginSeverity(margin, critical, wid, zone){
    if (critical) return "critical";
    const bands = CMB.margin_bands;
    let b = bands.default;
    if (DATA.weapons[wid].threat && bands.ballistic) b = bands.ballistic.find(x => x.zones.includes(zone));
    return margin >= b.critical ? "critical" : margin >= b.serious ? "serious" : "light";
  }
  function attackRoll(attack, roll, penalty){
    const eff = Math.max(0, attack - penalty), critAt = Math.floor(eff * CMB.critical_fraction), hit = roll <= eff;
    return { effective: eff, roll, hit, critical: hit && roll <= critAt, margin: hit ? eff - roll : null, base: attack, penalty };
  }
  function defenceRoll(defence, roll, penalty){
    const eff = Math.max(0, defence - penalty);
    return { effective: eff, roll, defended: roll <= eff, base: defence, penalty };
  }
  function armorAt(kitId, locId){ return ((KITS[kitId] || {}).layers || {})[LOC[locId].armor] || [] }
  function armorSteps(mat, mech, wid){
    const w = DATA.weapons[wid], m = MATS[mat], th = m.threats || {};
    const steps = mech === "ballistic" && w.threat && w.threat in th ? th[w.threat] : m[mech];
    const defeat = (w.armor_defeat || {})[mech] || 0;
    return Math.max(0, steps - defeat);
  }
  function sevTiers(mech, zone, wid){
    if (wid && DATA.weapons[wid].threat) mech = "ballistic";   // firearms and explosives
    const spec = DATA.severity_by_mechanism[mech];
    const tbl = spec && spec.tables.find(t => t.zones.includes(zone));
    return tbl ? tbl.tiers : DATA.severity;
  }
  function grazeFx(fx){ return { ...fx, bleed: Math.max(0, fx.bleed - 1), pain: Math.max(0, fx.pain - 1), shock: false } }
  function isGraze(margin, critical){ return margin !== null && margin !== undefined && !critical && margin <= CMB.graze_margin }
  const cannotAttack = p => !!p && p.flags.some(f => f === "incapacitated" || (CMB.states[f] || {}).no_attack);
  const lowerName = s => (/^[A-Z]{2}/.test(s) ? s : s.toLowerCase());   // "Bill" -> "bill", "MG" stays
  const d2 = n => n === 100 ? "00" : String(n).padStart(2, "0");

  function attackBlock(att, w){                     // why the attacker cannot attack at all, or null
    const A = att && att.pen;
    if (!A) return null;
    if (A.flags.includes("incapacitated")) return `${att.name} is incapacitated and cannot attack.`;
    if (cannotAttack(A)) return `${att.name} cannot attack: ${CMB.states[att.state].name.toLowerCase()}.`;
    if (A.flags.includes("cannot_wield") && w.melee !== "unarmed") return `${att.name} cannot hold a weapon in either hand.`;
    if (A.flags.includes("one_arm") && w.two_handed) return `${att.name} cannot use the ${lowerName(w.short || w.name)} with an arm hurt (it takes both hands): defend only.`;
    return null;
  }

  /* ----- the strike ----- */
  function resolveStrike(ctx, cmd, dice){
    const used = [], own = cmd.rolls || {};
    const take = (name, sides) => {                 // the player's own die if he gave one, else a rolled one
      const p = own[name], mine = Number.isInteger(p) && p >= 1 && p <= sides;
      const v = mine ? p : dice.randint(1, sides);
      used.push({ name, v, sides, by: mine ? "player" : "dice" });
      return v;
    };
    const effects = { closeIn: false, xp: null, free: null };
    const done = hit => ({ hit, dice: used, effects });
    const stray = !!cmd.stray, wid = ctx.weapon, w = DATA.weapons[wid];
    const atkPct = stray ? null : (cmd.atk ?? null);
    const base = { weapon: wid, table: ctx.table, ltable: ctx.ltable, mods: ctx.mods, aim: stray ? "" : cmd.aim || "", gap: !stray && !!cmd.gap, stray };
    const rc = ctx.rc || { range: null }, freeHit = !!ctx.freeHit;
    if (rc.blocked) return done({ ...base, fx: null, blocked: rc.blocked });
    base.range = rc.range;

    // the attack and the defence: {end} if no wound follows
    let att = { margin: null, crit: false, combat: null, roll: null };
    if (atkPct !== null){
      let blocked = attackBlock(ctx.attacker, w);
      const mf = !blocked && rc.range ? rc.range.misfire : 0;
      if (mf){                                      // wet priming: the shot may be lost
        const mr = take("misfire", 100);
        if (mr <= mf){
          if (freeHit) effects.free = "misfire";
          blocked = `Misfire: d100 ${d2(mr)} against ${mf}% — the wet weather spoiled the priming. The shot is lost.`;
        }
      }
      if (blocked) return done({ ...base, fx: null, blocked });
      effects.closeIn = true;
      const A = ctx.attacker && ctx.attacker.pen, D = ctx.defender && ctx.defender.pen;
      const ar = attackRoll(atkPct, take("atk", 100), (A ? A.attack : 0) + (rc.range ? rc.range.penalty : 0));
      const combat = { atk: ar, def: null, range: rc.range };
      if (ar.hit) effects.xp = "hit";
      if (!ar.hit){
        if (freeHit) effects.free = "miss";
        let st = null;                              // after a miss: does the shot go into the first man in the way?
        if (rc.range && rc.range.stray && (rc.range.way || []).length){
          const roll = take("stray", 100);
          st = { id: rc.range.way[0], roll, chance: rc.range.stray, hit: roll <= rc.range.stray };
        }
        return done({ ...base, fx: null, miss: true, combat, stray: st });
      }
      const defPct = cmd.def ?? null;
      if (defPct !== null && !ar.critical){
        const dr = defenceRoll(defPct, take("def", 100), D ? D.defence : 0);
        combat.def = dr;
        if (dr.defended){
          effects.xp = "defended";
          if (freeHit) effects.free = "parried or dodged";
          return done({ ...base, fx: null, defended: true, combat });
        }
      }
      att = { margin: ar.margin, crit: ar.critical, combat, roll: ar.roll };
    }

    // the wound: the aim paid for, then location, blow, severity and armour
    const cost = CMB.aim.cost, aimZone = stray ? "" : cmd.aim || "", gapAim = !stray && !!cmd.gap;
    let left = att.margin, zonePaid = false, zoned = null;
    const pays = () => att.margin === null || att.crit || left >= cost;
    if (aimZone && pays()){
      zoned = ctx.aimRanges || null;
      if (zoned){ zonePaid = true; if (att.margin !== null && !att.crit) left -= cost }
    }
    const rl = take("loc", 100), loc = look(zoned || ctx.ranges, rl);
    const layers = ctx.evidence ? [] : armorAt(ctx.armor, loc);
    const whole = layers.length === 1 && layers[0][1] === 1 && layers[0][2] === 100;
    const gapped = gapAim && layers.length > 0 && !whole && pays();   // a gap is paid for only where there is one
    if (gapped && att.margin !== null && !att.crit) left -= cost;
    const blow = w.choose && cmd.blow && w.mechanisms[cmd.blow] ? cmd.blow : null;   // a blow the attacker declared, or rolled
    const rm = blow ? null : take("mech", 100), mech = blow || look(w.mech_ranges, rm);
    let sevMode = att.margin !== null ? "margin" : cmd.sev || "roll";
    if (stray) sevMode = "roll";
    let sev, rs = null;
    if (sevMode === "margin") sev = marginSeverity(left, att.crit, wid, LOC[loc].zone);
    else if (sevMode !== "roll") sev = sevMode;      // the GM's pick
    else { rs = take("sev", 100); sev = sevTiers(mech, LOC[loc].zone, wid).find(x => rs >= x.d100[0] && rs <= x.d100[1]).id }

    let armor = null, final = sev;
    if (layers.length){                             // the attack roll's units digit (0 is 10), else a d10 (as gravewounds.engine.cover_digit)
      const fromAtk = att.roll !== null && att.roll !== undefined;
      const cover = whole || gapped ? null : (fromAtk ? (att.roll % 10 || 10) : take("cover", 10));
      const hitLayer = whole ? layers[0] : gapped ? null : layers.find(([, lo, hi]) => cover * 10 >= lo && cover * 10 <= hi);
      const mat = hitLayer ? hitLayer[0] : null, steps = hitLayer ? armorSteps(mat, mech, wid) : 0;
      final = LADDER[Math.max(0, LADDER.indexOf(sev) - steps)];
      armor = { mat, layers, rc: cover, rcAtk: !whole && fromAtk, covered: !!hitLayer, gapped: !!gapped, steps, from: sev, to: final };
    }
    const grazed = final !== "stopped" && isGraze(left, att.crit);
    const fx0 = final === "stopped" ? null : DATA.wounds[`${LOC[loc].class}|${mech}|${final}`];
    const fx = fx0 && grazed ? grazeFx(fx0) : fx0;
    return done({ loc, mech, sev: final, rolled: sev, fx, armor, combat: att.combat, graze: grazed, range: rc.range, free: freeHit, strayHit: stray,
      rolls: { loc: rl, mech: rm, sev: rs },
      aim: { zone: aimZone, zonePaid, gap: gapAim, gapPaid: gapped, margin: att.margin, left },
      weapon: wid, table: ctx.table, ltable: ctx.ltable, mods: ctx.mods });
  }

  return { resolveStrike, attackRoll, defenceRoll, marginSeverity, armorAt, armorSteps, sevTiers, grazeFx, isGraze, cannotAttack };
}
