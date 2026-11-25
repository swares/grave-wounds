/* The scripted fighter: what a fighter on a side the GM's script plays does with his turn, with no
   page. The page measures his situation (where he can move, whom he could strike from each hex,
   how hurt everyone is) and the brain picks: where to move or whether to take cover, whom to
   strike, whether to aim for a gap, and which blow a named man declares. The rules then run as
   for anyone else (strike.js); the brain never rolls a die.

   FIGHTER.chooseTurn(view) -> {move, cover, target, gap, blow, aid, why}
     view.me        {id, ranged, frac (Blood left, 0-1), named, blows (a cut-and-thrust weapon's
                    blows, else []), attack (his attack % after wounds), able (can attack at all),
                    reloading (rounds before his slow weapon shoots again, 0 when loaded)}
     view.away      true when his side wins by getting away off its own edge; view.edgeDist(hex)
                    is how far a hex is from that edge
     view.here      his hex, "col,row"
     view.reach     [{hex, cost, run}]: the hexes he can reach this turn (run: no attack after)
     view.enemies   [{id, hex, frac, armoured (partly covered: a gap to aim for), plated (armour
                    the blows meet)}], only those still fighting
     view.targetsFrom(hex) -> [{id, dist, penalty}]: whom he could strike from that hex
     view.dist(hexA, hexB) -> hexes between them
     view.storming  optional: his side storms a wall by its ladders and he is still below its top; he
                    makes for the ladders and over, rather than stand and shoot from below (ours)
     view.pathDist(hex) -> optional: steps from that hex to the nearest enemy going round works a man
                    cannot cross (a palisade's gate or gap, a wall's ladders, a river's ford or bridge); when given, closing in and
                    falling back go by it
     view.coverAt(hex) -> the cover % a shooter would have there
     view.losing    his side is near breaking (morale)
     view.stance    "cautious" | "steady" | "reckless" (the GM's setting for the side)
     view.me.bleed  the share of his Blood he loses a round (0 when not bleeding)
     view.friends   [{id, hex, down, bleed}]: his side's other men on the map, not taken
   aid      a man of his side he gives first aid this turn (himself, or one he is next to after
            his move), or absent; he does not strike
   move     a hex to move to, or null to stay
   cover    true: he goes to ground instead (no attack)
   target   the enemy he strikes (from where he ends up), or null
   why      a few words for the log: why he did it

   The choices are design guesses, not calibrated: closest and most hurt first (a shooter: the clearest
   shot first), close in when he
   cannot reach anyone, fall back when badly hurt by his stance. First aid, out of an enemy's
   reach (no enemy next to him): he binds his own wound if it bleeds badly; by his stance, a
   cautious man treats the worst-bleeding comrade he can reach, a steady one only a comrade who
   is down, a reckless one no one. build.py puts this file into the
   roller at its FIGHTER_JS marker; in Node it is a module (tools/gm/test.js). */

const FIGHTER = (() => {                          // one name in the page: its helpers stay inside
  const STANCES = {
    cautious: { fallBack: 0.6, fallBackLosing: 1, gapAttack: 70, runs: false, keepRange: 3, aid: "any" },
    steady:   { fallBack: 0.35, fallBackLosing: 0.6, gapAttack: 60, runs: true, keepRange: 2, aid: "down" },
    reckless: { fallBack: 0, fallBackLosing: 0, gapAttack: 50, runs: true, keepRange: 1, aid: "none" },
  };
  const SELF_BLEED = 0.05;                          // he binds his own wound at a twentieth of his Blood a round or more (a design guess)
  const byKey = (a, b) => (a < b ? -1 : Number(a > b));

  const SHOT_TIE = 10;                              // a shooter's best shot: within 10 of the clearest counts as as good (a design guess, ours)
  function pickTarget(options, enemies, ranged = false){   // the most hurt first, then the easiest, then the nearest; a shooter the clearest shot first (the most hurt among those within SHOT_TIE of it)
    const frac = Object.fromEntries(enemies.map(e => [e.id, e.frac]));
    const best = ranged && options.length ? Math.min(...options.map(o => o.penalty)) : null;
    const pool = ranged ? options.filter(o => o.penalty <= best + SHOT_TIE) : options;
    return pool.slice().sort((a, b) => (frac[a.id] - frac[b.id]) || (a.penalty - b.penalty) || (a.dist - b.dist) || (a.id - b.id))[0] || null;
  }
  function nearestEnemy(view, hex){
    if (view.pathDist) return view.pathDist(hex);
    let best = Infinity;
    for (const e of view.enemies) best = Math.min(best, view.dist(hex, e.hex));
    return best;
  }
  function declare(view, st, target){               // the aim and blow he declares at this enemy
    const e = view.enemies.find(x => x.id === target.id) || {};
    const gap = !!e.armoured && view.me.attack - target.penalty >= st.gapAttack;
    let blow = "";
    if (view.me.named && view.me.blows.length){     // named men declare; the rest strike their weapon's mix
      const want = e.plated ? "thrust" : "cut";
      blow = view.me.blows.includes(want) ? want : view.me.blows[0];
    }
    return { gap, blow };
  }
  function strikeFrom(view, st, move, why){         // the turn, given where he ends up
    const hex = move || view.here, running = move ? (view.reach.find(r => r.hex === move) || {}).run : false;
    const t = running || !view.me.able ? null : pickTarget(view.targetsFrom(hex), view.enemies, view.me.ranged);
    if (!t) return { move, cover: false, target: null, gap: false, blow: "", why };
    return { move, cover: false, target: t.id, ...declare(view, st, t), why };
  }
  function fallBack(view, st){                      // badly hurt: the hex farthest from the enemy, or cover for a shooter
    let best = { hex: null, d: nearestEnemy(view, view.here), cover: view.coverAt(view.here) };
    for (const r of view.reach.slice().sort((a, b) => byKey(a.hex, b.hex))){
      if (r.run && !st.runs) continue;
      const d = nearestEnemy(view, r.hex);
      if (d > best.d) best = { hex: r.hex, d, cover: view.coverAt(r.hex) };
    }
    if (!best.hex && view.me.ranged && !view.coverAt(view.here)) return { move: null, cover: true, target: null, gap: false, blow: "", why: "badly hurt: goes to ground" };
    return strikeFrom(view, st, best.hex, best.hex ? "badly hurt: falls back" : "badly hurt: holds where he is");
  }
  function closeIn(view, st){                       // nobody in reach: the hex nearest the enemy he can get to
    let best = null;
    for (const r of view.reach.slice().sort((a, b) => byKey(a.hex, b.hex))){
      if (r.run && !st.runs) continue;
      const d = nearestEnemy(view, r.hex);
      if (view.me.ranged && d < st.keepRange) continue;   // a shooter does not walk into their arms
      if (!best || d < best.d || (d === best.d && r.cost < best.cost)) best = { hex: r.hex, d, cost: r.cost };
    }
    return strikeFrom(view, st, best ? best.hex : null, best ? "closes with the enemy" : "cannot get closer: holds");
  }

  function storm(view, st){                         // storming a wall: a man next to him he strikes (with the bayonet or his sidearm if he must); else he goes for the ladders and over, loaded or not (ours)
    if (view.me.able && view.targetsFrom(view.here).some(t => t.dist <= 1)) return strikeFrom(view, st, null, "strikes the man at the top");
    const go = closeIn({ ...view, me: { ...view.me, ranged: false } }, st);
    return go.move ? { ...go, why: "makes for the ladders" } : go;
  }
  const safe = (view, hex) => nearestEnemy(view, hex) > 1;   // no enemy next to that hex
  function makeAway(view, st){                      // his side wins by getting away: the hex he can reach nearest his own edge (ours)
    let best = { hex: null, d: view.edgeDist(view.here), cost: 0 };
    for (const r of view.reach.slice().sort((a, b) => byKey(a.hex, b.hex))){
      if (r.run && !st.runs) continue;
      const d = view.edgeDist(r.hex);
      if (d < best.d || (d === best.d && best.hex && r.cost < best.cost)) best = { hex: r.hex, d, cost: r.cost };
    }
    if (!best.hex) return strikeFrom(view, st, null, "cannot get nearer his edge: holds");
    return strikeFrom(view, st, best.hex, "makes for his own edge");   // and strikes on the way if he can
  }
  const aiding = (move, id, why) => ({ move, cover: false, target: null, gap: false, blow: "", aid: id, why });
  function firstAid(view, st){                      // a turn of first aid, or null
    if ((view.me.bleed || 0) >= SELF_BLEED && safe(view, view.here)) return aiding(null, view.me.id, "binds his own wound");
    if (st.aid === "none" || !safe(view, view.here)) return null;   // a man in contact fights on
    if (view.me.reloading) return null;            // reloading: his hands are full (ours)
    if (view.me.ranged && view.me.able && view.targetsFrom(view.here).length) return null;   // a shooter with a target keeps shooting; he tends others when he has no one to shoot at (ours)
    const hurt = (view.friends || []).filter(f => f.bleed > 0 && (st.aid === "any" || f.down) && safe(view, f.hex)).sort((a, b) => (b.bleed - a.bleed) || (a.id - b.id));
    for (const f of hurt){
      if (view.dist(view.here, f.hex) <= 1 && safe(view, view.here)) return aiding(null, f.id, "gives first aid");
      const to = view.reach.filter(r => !r.run && view.dist(r.hex, f.hex) === 1 && safe(view, r.hex))
        .sort((a, b) => (a.cost - b.cost) || byKey(a.hex, b.hex))[0];
      if (to) return aiding(to.hex, f.id, "goes to a wounded comrade");
    }
    return null;
  }

  function chooseTurn(view){
    const st = STANCES[view.stance] || STANCES.steady;
    if (!view.enemies.length) return { move: null, cover: false, target: null, gap: false, blow: "", why: "no enemy left" };
    const aid = firstAid(view, st);
    if (aid) return aid;
    const hurt = view.me.frac <= (view.losing ? st.fallBackLosing : st.fallBack);
    if (hurt && st.fallBack > 0) return fallBack(view, st);
    if (view.away && safe(view, view.here)) return makeAway(view, st);   // his side wins by getting away: he makes for his edge
    if (view.storming) return storm(view, st);
    if (view.me.reloading){                        // reloading: he stays where he is; a man next to him he strikes with his sidearm or the butt (ours)
      if (view.me.able && view.targetsFrom(view.here).length) return strikeFrom(view, st, null, "strikes the man next to him while he reloads");
      return { move: null, cover: false, target: null, gap: false, blow: "", why: "reloads" };
    }
    if (view.me.able && view.targetsFrom(view.here).length) return strikeFrom(view, st, null, "strikes from where he stands");   // a shooter with a target stays (moving for a clearer shot drew men out of trenches and lines: PR #596)
    if (view.me.able){                             // a hex he can advance to and still strike from: the nearest, a shooter's with the best shot
      const from = view.reach.filter(r => !r.run).map(r => ({ ...r, t: pickTarget(view.targetsFrom(r.hex), view.enemies, view.me.ranged) })).filter(r => r.t);
      if (from.length){
        const score = r => (view.me.ranged ? [r.t.penalty - view.coverAt(r.hex), r.cost] : [r.cost, r.t.penalty]);
        from.sort((a, b) => { const x = score(a), y = score(b); return (x[0] - y[0]) || (x[1] - y[1]) || byKey(a.hex, b.hex) });
        return strikeFrom(view, st, from[0].hex, "advances and strikes");
      }
    }
    return closeIn(view, st);
  }

  return { chooseTurn, STANCES };
})();

if (typeof module !== "undefined") module.exports = FIGHTER;   // Node (the tests); the page has no `module`
