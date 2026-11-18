"""A season with the battalion, in a headless browser, served as the site is: the team builder to the roller.

    python3 tools/service/season.py

A company of the British in the Peninsula serves spring 1811 with Albuera ticked, as the 1/57th: each man's
hit roll and sickness are logged, the season's days go toward his term (counted as rolled), the calendar
moves on, and the hits wait for the roller. A term made mostly of rolled seasons gives no lifepath wound
chance. On the roller the first hit is rolled on the man as a hit with no attack roll, with the weapon the
season gave, and leaves the queue. Needs Python's playwright with Chromium and a built site. Exits non-zero
on any failure. Then the season's small fight: shown with its sizes, aims and sources, another picked, and
the picket at night played on the roller, the team's named men in the picket against French with muskets,
with the aims, the end and the source in the fight's notes.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "campaign"))
from harness import check, main, serve   # noqa: E402

BASE, server = serve()
SEEDED = """seed => { let s = Math.max(1, seed % 2147483647);
  realDice.randint = (a, b) => { s = s * 16807 % 2147483647; return a + s % (b - a + 1) } }"""
FIND = """() => {                                       // a seed whose season gives a hit and no death
  const men = S.team.map(c => ({ name: c.name, endurance: c.stats.end, position: "line", unit: { albuera: 0 }, share: {} }));
  for (let seed = 1; seed < 400; seed++){
    let s = seed; const d = () => { s = s * 16807 % 2147483647; return 1 + s % 100 };
    const r = SVC.serve("peninsula", "1811-spring", men, ["fuentes", "albuera"], d);
    if (r.men.some(m => m.hits.length) && !r.men.some(m => m.dead)) return seed;
  }
  return null;
}"""
QUEUE = "() => JSON.parse(localStorage.getItem('gravewounds-service-hits') || '[]')"


def run(p):
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1400, "height": 1100})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE + "team.html")
    pg.evaluate("() => localStorage.clear()")
    pg.reload()
    pg.select_option("#sel-era", "horse_musket")
    pg.select_option("#sel-region", "british_pen")
    pg.select_option("#sel-template", "company")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    check("Summer 1808" in pg.inner_text("#service"), "the battalion's war starts in summer 1808")
    k = pg.evaluate("() => SVC.war('peninsula').seasons.findIndex(s => s.id === '1811-spring')")
    pg.select_option("#sv-season", str(k))
    check("Albuera" in pg.inner_text("#service") and "Fuentes" in pg.inner_text("#service"), "spring 1811 lists Fuentes de Oñoro and Albuera")
    check(not pg.is_checked("input[data-svat=albuera]") and pg.is_checked("input[data-svat=fuentes]"),
          "Albuera (Beresford's corps) is not ticked by default; Fuentes (the main army) is")
    pg.check("input[data-svat=albuera]")
    pg.select_option("select[data-svunit=albuera]", "0")
    seed = pg.evaluate(FIND)
    check(seed is not None, f"a season with a hit found (seed {seed})")
    pg.evaluate(SEEDED, seed)
    n = pg.evaluate("() => S.team.length")
    pg.click("#btn-serve")
    log = pg.inner_text("#service")
    check("hit at Albuera" in log and "66%" in log, "the log gives the hit at Albuera at the 1/57th's 66%")
    q = pg.evaluate(QUEUE)
    check(len(q) >= 1 and all(h["table"] == "peninsular-1808-14-all-hits" and h["weapon"] for h in q),
          f"{len(q)} hit(s) wait for the roller, on the army's table, each with a weapon")
    served = pg.evaluate("() => { const X = readXp(); return S.team.map(c => [(X[c.pid] || {}).served || 0, c.rolled_days]) }")
    check(len(served) == n and all(s == [91, 91] for s in served), f"each man's 91 days count toward his term, as rolled ({served[:2]})")
    check(pg.evaluate("() => S.service.i") == k + 1 and "Summer 1811" in pg.inner_text("#sv-season option:checked"), "the calendar moves on to summer 1811")

    lived = pg.evaluate("""() => { const one = { randint: (a) => a }, out = [];
      for (const rolled of [0, xpTermDays()]){
        const c = structuredClone(S.team.find(m => m.career === 'line'));
        c.served = 0; c.rolled_days = rolled; const was = (c.old || []).length;
        const r = xpSeason(c, [], xpTermDays(), one);
        out.push([r.terms, (c.old || []).length - was, c.rolled_days]);
      }
      return out }""")
    check(lived[0][:2] == [1, 1] and lived[1] == [1, 0, 0], f"a term of rolled seasons gives no lifepath wound chance ({lived})")

    pg.click("#btn-send")
    pg.wait_for_function("() => location.pathname.endsWith('roller.html')", timeout=15000)
    pg.wait_for_function("() => typeof S === 'object' && Array.isArray(S.chars)", timeout=10000)
    pg.get_by_role("button", name="Add the team").first.click()
    pg.wait_for_function("() => S.chars.some(c => c.uid)", timeout=10000)
    pg.wait_for_selector("button[data-map=svcroll]")
    first = q[0]
    pg.click("button[data-map=svcroll]")
    pg.wait_for_function("() => S.hit", timeout=8000)
    hit = pg.evaluate("() => ({ who: defenderChar().name, weapon: S.weapon, table: S.table, attacker: S.attacker })")
    check(hit["who"] == first["name"] and hit["weapon"] == first["weapon"] and hit["table"] == first["table"] and hit["attacker"] == -1,
          f"the roller rolls {first['name']}'s wound with the season's weapon and no attacker ({hit})")
    check(len(pg.evaluate(QUEUE)) == len(q) - 1, "and it leaves the queue")
    check("A hit from the season (" in pg.inner_text("#result"), f"the roll says it is a hit from the season, not a stray shot ({pg.inner_text('#result')[:200]!r})")
    pg.click("#btn-apply")
    track = pg.evaluate(f"""() => {{ const n = Object.values(readNamed()).find(x => x.name === {json.dumps(first['name'])}); return n ? (n.health.cases || []).filter(k => k.d === 'wound').length : -1 }}""")
    check(track >= 1, f"applied, his wound goes onto his wound track in the shared record ({track})")
    wounded = first["name"]
    named = pg.evaluate("() => S.chars.filter(c => c.uid && !c.dead).length")

    # the season's small fight, played: back on the team builder, the picket at night goes to the roller
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    pg.evaluate("() => { const W = SVC.war('peninsula'); S.svcSmall = SVC.smallFight(W, 'quarters', svcD100, 'picket'); render() }")
    box = pg.inner_text("#service")
    check("A picket attacked at night" in box and "Hold the bridge" in box and "Barba del Puerco" in box, "the small fight is shown: what the accounts say, the sizes and the aims")
    check(pg.locator("#sv-fight option").count() == 8, "the GM can pick any of the war's 8 small fights")
    pg.select_option("#sv-fight", "foragers")
    check("French foragers caught at dawn" in pg.inner_text("#service"), "picking another rolls its sizes")
    pg.select_option("#sv-fight", "picket")
    pg.click("#btn-svplay")
    pg.wait_for_function("() => location.pathname.endsWith('roller.html')", timeout=15000)
    pg.wait_for_selector("button[data-map=handoff]", timeout=10000)
    check("From a season with the battalion" in pg.inner_text("#map-actions"), "the roller offers the small fight")
    pg.click("button[data-map=handoff]")
    pg.wait_for_function("() => !S.handoff", timeout=8000)
    sides = pg.evaluate("""() => { const b = S.chars.filter(c => sideOf(c) === 'British'), f = S.chars.filter(c => sideOf(c) === 'French');
      return { b: b.length, named: b.filter(c => c.uid).length, f: f.length, fw: [...new Set(f.map(c => c.weapon))], notes: S.pending.join(' | ') } }""")
    check(sides["named"] == named and sides["b"] >= named and sides["f"] >= 1,
          f"the team's {named} named men fight in the picket with its comrades, against the French ({sides['b']} and {sides['f']})")
    check(sides["fw"] == ["musket_smoothbore"], f"the French carry the fight's weapon ({sides['fw']})")
    check("Hold the bridge" in sides["notes"] and "It ends" in sides["notes"] and "Cope" in sides["notes"], "the aims, the end and the source are in the fight's notes")
    check(pg.evaluate("() => S.weather.cond") == "rain", "in the rain, as the fight says")
    dark = pg.evaluate("""() => { const was = S.weapon; S.weapon = 'musket_smoothbore'; const a = S.chars.find(c => c.uid);
      const out = { light: S.weather.light, far: darkOnAttack({ blocked: null, penalty: 0, notes: [] }, 30, a).blocked || '',
               near: darkOnAttack({ blocked: null, penalty: 0, notes: [] }, 10, a).penalty };
      S.weapon = was; return out }""")
    check(dark["light"] == "night" and "Dark night" in dark["far"] and dark["near"] == 20,
          f"in a dark night: no aimed shot beyond 25 hexes, and -20% within ({dark})")
    count = pg.evaluate("() => S.mapMsg.match(/The picket \\(British\\), (\\d+ of its \\d+ men|its \\d+ men)/)?.[1] || ''")
    check(count.startswith(str(sides["b"]) + " of its") or count == f"its {sides['b']} men" or (count.startswith("its ") and int(count.split()[1]) <= sides["b"]),
          f"the setup counts the team's men in the picket ({count}; {sides['b']} on the map)")
    odds = pg.evaluate("""() => { const m = S.mapMsg, b = m.match(/The picket \\(British\\), (?:(\\d+) of )?its (\\d+) men/), f = m.match(/\\(French\\), (?:(\\d+) of )?its (\\d+) men/);
      return { bHere: +(b[1] || b[2]), bAll: +b[2], fHere: +(f[1] || f[2]), fAll: +f[2] } }""")
    want = max(1, min(40, round(odds["bHere"] * odds["fAll"] / odds["bAll"])))
    check(odds["fHere"] == min(want, odds["fAll"]), f"the French come in at the rolled odds, not capped at 8 against the whole team ({odds}, wanted {want})")
    # the picket's own end: the GM's script plays both sides and stops when the roller calls it
    end = pg.evaluate("""() => {
      S.gm = { on: true, auto: false, sides: {} };
      for (const sd of new Set(S.chars.map(sideOf))) S.gm.sides[sd] = { ...gmSide(sd), ctl: "script", stance: "steady", quality: "regular" };
      let r = "acted", n = 0;
      try{ while (r === "acted" && n++ < 6000) r = gmStep() }catch(e){ return { err: e.stack } }
      renderChars();
      const fd = S.chars.filter(c => sideOf(c) === 'French'), down = fd.filter(c => isDown(c) || c.taken || c.fled).length;
      return { r, round: S.round, msg: S.gmMsg, called: S.fightEnd && S.fightEnd.called, won: S.wonBy, frac: down / fd.length,
               bar: (document.querySelector('#btn-fight-on') || {}).id || '', log: S.log.map(l => l.lines.join(' ')).join(' ') + ' ' + (S.pending || []).join(' ') } }""")
    check(not end.get("err"), f"the script plays the picket ({end.get('err', '')[:300]})")
    called = end.get("called") or {}
    check(end["r"] == "over" and "The fight's end" in end["msg"], f"the script stops at the fight's own end ({end['msg']}, round {end['round']})")
    check((called.get("won") == "British" and (end["frac"] >= 0.33 or end["round"] > 6 or called.get("why") == "French break")) or called.get("won") == "French",
          f"called by its end: 6 rounds, a third of the French down, or a side broken ({called}, French down {end['frac']:.2f})")
    check(end["won"] == called.get("won") and end["bar"] == "btn-fight-on", "the winner is marked, and the GM may fight on")
    pg.click("#btn-fight-on")
    on = pg.evaluate("() => ({ won: S.wonBy, r: gmStep(), on: S.fightEnd.on })")
    check(on["on"] and on["r"] != "over" or "still stand" in pg.evaluate("() => S.gmMsg"), f"Fight on sets the call aside and the script plays on ({on})")
    # held ground: the position lost at a round's end, and men getting away by their own edge
    held = pg.evaluate("""() => {
      const snap = JSON.stringify({ chars: S.chars, end: S.fightEnd, won: S.wonBy, broken: S.broken }), E = S.fightEnd, { cols, rows } = mapSize();
      const out = { hold: E.hold, radius: E.position.radius };
      S.broken = {}; S.wonBy = null; E.called = null; E.on = false; E.down = {}; E.rounds = null;
      const br = S.chars.filter(c => sideOf(c) === 'British'), fr = S.chars.filter(c => sideOf(c) === 'French');
      for (const c of S.chars){ c.taken = false; c.fled = false; c.away = false; c.blood = 100; c.wounds = []; c.state = null }
      br.forEach((c, i) => { c.pos = [cols - 1, i] });                       // all the picket out of the position
      fr[0].pos = E.position.centre.slice();                                  // a Frenchman in it
      out.midRound = fightEndCheck(false);
      out.atEnd = fightEndCheck(true);
      E.called = null; S.wonBy = null; E.hold = null; E.away = { side: 'French', share: 0.25 };
      const k = E.edges.French, edge = [[0, null], [cols - 1, null], [null, 0], [null, rows - 1]][k];
      fr.slice(0, Math.ceil(fr.length / 4)).forEach((c, i) => { c.pos = [edge[0] ?? i, edge[1] ?? i] });
      out.away = fightEndCheck(false);
      out.gone = fr.filter(c => c.away && !c.pos).length; out.need = Math.ceil(fr.length / 4);
      out.isOut = fr.filter(c => c.away).every(isOut);
      const was = JSON.parse(snap); S.chars = was.chars; S.fightEnd = was.end; S.wonBy = was.won; S.broken = was.broken;
      return out }""")
    check(held["hold"] == "British" and held["midRound"] is None and (held["atEnd"] or {}).get("won") == "French"
          and "hold" in held["atEnd"]["why"], f"the picket's bridge: lost at a round's end once the French stand in it and the picket does not ({held})")
    check((held["away"] or {}).get("won") == "French" and held["gone"] >= held["need"] and held["isOut"],
          f"and men on their own edge leave the field: once a share have got away, their side wins ({held['away']}, {held['gone']} gone, {held['need']} needed; any already on the edge go too)")
    # a man taken in a fight his side then wins is retaken
    rt = pg.evaluate("""() => { const c = S.chars.find(x => sideOf(x) === 'British' && x.sheet?.pid), was = S.wonBy;
      c.taken = true; markLost(c.sheet.pid, 'taken prisoner'); setWon('British');
      const out = { taken: c.taken, lost: !!(readPurses()[c.sheet.pid] || {}).lost, log: (S.pending || []).at(-1) }; S.wonBy = was; return out }""")
    check(not rt["taken"] and not rt["lost"] and "retaken" in (rt["log"] or ""), f"a man taken in a fight his side wins is retaken ({rt})")
    # a broken scripted side: the down beside an enemy taken, the down alone left, the held break away or are taken, the rest run
    yl = pg.evaluate("""() => {
      const snap = JSON.stringify({ chars: S.chars, gm: S.gm, broken: S.broken }), ri = DICE.randint, { cols, rows } = mapSize();
      S.gm = { on: true, auto: false, sides: { British: { ...gmSide('British'), ctl: 'script' }, French: { ...gmSide('French'), ctl: 'script' } } };
      const br = S.chars.filter(c => sideOf(c) === 'British').slice(0, 5), fr = S.chars.find(c => sideOf(c) === 'French');
      for (const c of S.chars){ c.pos = null; c.taken = false; c.fled = false; c.away = false; c.blood = 100; c.wounds = []; c.state = null }
      S.broken = {};
      fr.pos = [10, 8]; br[0].pos = [11, 8]; br[0].state = { id: 'out' };          // down, an enemy beside him
      br[1].pos = [2, 2]; br[1].state = { id: 'out' };                            // down, no one near
      br[2].pos = [9, 8]; br[3].pos = [10, 9]; br[4].pos = [cols - 2, rows - 2];  // two held, one clear
      const rolls = [1, 100]; DICE.randint = (a, b) => (rolls.length ? rolls.shift() : ri(a, b));
      S.broken.British = true;
      const lines = gmYield('British');
      DICE.randint = ri;
      const out = { down0: [isDown(br[0]), br[0].taken], down1: br[1].taken || br[1].fled, held: [br[2].fled, br[3].taken], clear: br[4].fled, lines };
      const was = JSON.parse(snap); S.chars = was.chars; S.gm = was.gm; S.broken = was.broken;
      return out }""")
    check(yl["down0"] == [True, True] and not yl["down1"] and yl["held"] == [True, True] and yl["clear"],
          f"a broken scripted side: the down beside an enemy taken, the down alone left, the held break away or are taken, the rest run ({yl['lines']})")
    # the picket was played only to see its end: its losses do not go on to the team builder
    pg.evaluate("() => { const all = readPurses(); for (const k in all) delete all[k].lost; writePurses(all); for (const c of S.chars) c.taken = false; save() }")
    # a case carried from the last season: the panel shows it, and the next season begins from it
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    asat = pg.evaluate("""() => { const W = SVC.war('peninsula'), f = W.small_fights.find(x => x.id === 'picket');
      return [svcAsAt(W, f, W.seasons.find(x => x.id === f.at)), svcAsAt(W, f, W.seasons[0])] }""")
    check(asat[0] == "" and "a fight of this kind, as in spring 1810" in asat[1], f"a fight from another season says so in its notes ({asat})")
    pg.evaluate("""hurt => { const c = S.team.find(x => x.name !== hurt) || S.team[0], H = { cases: [{ d: 'flux', inc: 0, step: 2, peak: 2, shown: 9, chronic: true }], immune: {}, had: {}, dead: 0 };
      c.svcHealth = H; const all = namedStore(), n = namedOf(all, c); if (n){ n.health = H; localStorage.setItem(NAMED_STORE, JSON.stringify(all)) } render() }""", wounded)   # not the man wounded last season: his wound stays on his track
    check("still serious from last season" in pg.inner_text("#service"), "a man still sick at the season's end shows so on the panel")
    pg.evaluate(SEEDED, 11)
    pg.click("#btn-serve")
    first = pg.evaluate("() => S.svclog.join(' ')")
    check("began the season serious" in pg.inner_text("#service"), f"and his next season begins from it ({first[:120]})")
    check(f"{wounded}: began the season" in pg.inner_text("#service") and "(his wounds)" in pg.inner_text("#service"),
          f"the man hit last season begins this one with his wounds on the track ({wounded}: {pg.evaluate('n => S.svclog.find(l => l.startsWith(n)) || S.svclog.join(' ')', wounded)[:300]!r})")

    # the second war: a Union company in the East
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "civil_war")
    pg.select_option("#sel-region", "union")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('acw_union_east').seasons.findIndex(s => s.id === '1863-summer')")
    pg.select_option("#sv-season", str(k))
    check("Summer 1863" in pg.inner_text("#sv-season option:checked") and "Gettysburg" in pg.inner_text("#service"), "a Union team serves the war in the East: summer 1863 has Gettysburg")
    check("1st Minnesota (82%)" in pg.inner_text("select[data-svunit=gettysburg]"), "with the 1st Minnesota's own 82%")
    check(pg.evaluate("() => SVC.weaponFor(SVC.war('acw_union_east'), 50)") == "rifle_musket", "and its hits come mostly from the rifle-musket")
    # and the other side: a Confederate team with the 4th Virginia
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "civil_war")
    pg.select_option("#sel-region", "confederacy")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('acw_confederate_east').seasons.findIndex(s => s.id === '1863-spring')")
    pg.select_option("#sv-season", str(k))
    cs = pg.inner_text("#service")
    check("Chancellorsville" in cs and "4th Virginia (48%)" in pg.inner_text("select[data-svunit=chancellorsville]"),
          "a Confederate team serves with the Stonewall Brigade: spring 1863 has Chancellorsville, with the 4th Virginia's own 48%")
    check(pg.evaluate("() => SVC.warsFor('civil_war', 'confederacy').map(W => W.id).join()") == "acw_confederate_east", "and only the Confederate war is offered to it")
    tk = pg.evaluate("""() => { const q = [99, 99, 10]; const rng = () => q.length ? q.shift() : 99;
      const r = SVC.serve('acw_confederate_east', '1864-spring', [{ name: 'x', endurance: 50, unit: { spotsylvania: 0 } }], ['spotsylvania'], rng).men[0];
      return r.taken }""")
    check((tk or {}).get("action") == "spotsylvania" and tk.get("pct") == 63, f"at the Mule Shoe as the 4th Virginia, a man not hit is taken on 63% ({tk})")
    pg.evaluate("""() => { const V = svcState(), W = SVC.war('acw_confederate_east'); V.war = W.id; V.i = W.seasons.findIndex(s => s.id === '1864-spring');
      V.unit = { spotsylvania: 0 }; V.at = { wilderness: false, spotsylvania: true }; window.__q = [99, 99, 10];
      realDice.randint = (a, b) => (window.__q.length ? window.__q.shift() : b); render() }""")
    n0 = pg.evaluate("() => S.team.length")
    pg.click("#btn-serve")
    took = pg.evaluate("() => ({ log: S.svclog.join(' '), team: S.team.length, prisoners: (S.prisoners || []).length })")
    check("taken prisoner at Spotsylvania" in took["log"] and took["team"] < n0 and took["prisoners"] >= 1,
          f"served, a man taken goes to the Prisoners ({n0} -> {took['team']}, {took['prisoners']} prisoners: {took['log'][:300]!r})")
    # the third war: an English retinue in Henry V's war, and an escalade played (the team attacking)
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "medieval")
    pg.select_option("#sel-region", "england")
    pg.select_option("#sel-template", "retinue")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('henry_v').seasons.findIndex(s => s.id === '1415-autumn')")
    pg.select_option("#sv-season", str(k))
    check("Agincourt" in pg.inner_text("#service") and "play it on the field map" in pg.inner_text("#service").lower(),
          "an English retinue's autumn 1415 has Agincourt, which can be played on its battlefield")
    pg.click("#btn-send")
    pg.wait_for_function("() => location.pathname.endsWith('roller.html')", timeout=15000)
    pg.wait_for_function("() => typeof S === 'object' && Array.isArray(S.chars)", timeout=10000)
    pg.get_by_role("button", name="Add the team").first.click()
    pg.wait_for_function("() => S.chars.some(c => c.uid)", timeout=10000)
    men = pg.evaluate("() => S.chars.filter(c => c.uid && c.team && !c.dead && !c.taken).length")   # not those lost in the picket played above
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    pg.evaluate("() => { const W = SVC.war('henry_v'); S.svcSmall = SVC.smallFight(W, 'campaign', svcD100, 'escalade'); render() }")
    pg.click("#btn-svplay")
    pg.wait_for_function("() => location.pathname.endsWith('roller.html')", timeout=15000)
    pg.wait_for_selector("button[data-map=handoff]", timeout=10000)
    pg.click("button[data-map=handoff]")
    pg.wait_for_function("() => !S.handoff", timeout=8000)
    esc = pg.evaluate("""() => { const e = S.chars.filter(c => sideOf(c) === 'English'), f = S.chars.filter(c => sideOf(c) === 'French');
      return { named: e.filter(c => c.uid).length, f: f.length, fw: [...new Set(f.map(c => c.weapon))], fk: [...new Set(f.map(c => c.kit))], msg: S.mapMsg } }""")
    check(esc["named"] == men and esc["fw"] == ["crossbow"] and esc["fk"] == ["brigandine_sallet"],
          f"the escalade: the retinue's {men} named men go up the ladders against the guard with crossbows ({esc['named']}, {esc['fw']}, {esc['fk']})")
    check("Defending: The guard on the wall" in esc["msg"], "the French guard holds the wall; the English come in from the edge")
    # the sixth war: the same English team with Edward of March, 1459-71
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    pg.select_option("#sv-war", "roses_edward")
    k = pg.evaluate("() => SVC.war('roses_edward').seasons.findIndex(s => s.id === '1461-spring')")
    pg.select_option("#sv-season", str(k))
    rs = pg.inner_text("#service")
    check("Towton" in rs and "Ferrybridge" in rs and "play it on the field map" in rs.lower(),
          "an English team can serve with Edward of March instead: spring 1461 has Ferrybridge and Towton, which can be played on its field")
    check(pg.evaluate("() => SVC.weaponFor(SVC.war('roses_edward'), 10)") == "longbow", "and its hits come first from the longbow")
    pg.evaluate("() => { const W = SVC.war('roses_edward'); S.svcSmall = SVC.smallFight(W, 'march', svcD100, 'bridge'); render() }")
    check("Clifford's horsemen" in pg.inner_text("#service"), "the bridge at dawn comes up as Ferrybridge's small fight")
    # the seventh: the same English team on the other side, with the northern Lancastrians
    pg.select_option("#sv-war", "roses_lancaster")
    k = pg.evaluate("() => SVC.war('roses_lancaster').seasons.findIndex(s => s.id === '1461-spring')")
    pg.select_option("#sv-season", str(k))
    rs = pg.inner_text("#service")
    check("Towton" in rs and "Ferrybridge" in rs and "40%" in rs, f"or with the northern Lancastrians: Towton lost at 40% (the dead times two) ({rs[:200]!r})")
    pg.evaluate("() => { const W = SVC.war('roses_lancaster'); S.svcSmall = SVC.smallFight(W, 'march', svcD100, 'bridge'); render() }")
    check("Clifford's horsemen" in pg.inner_text("#service") and pg.evaluate("() => SVC.war('roses_lancaster').small_fights[0].team_attacks"),
          "and the bridge at dawn from Clifford's side, attacking")
    # the fifth war: a British section in Italy
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "wwii")
    pg.select_option("#sel-region", "commonwealth")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('italy_british').seasons.findIndex(s => s.id === '1943-winter')")
    pg.select_option("#sv-season", str(k))
    it = pg.inner_text("#service")
    check("Capracotta" in it and "1st Royal Sussex on Snakeshead" in pg.inner_text("select[data-svunit=cassino_feb]"),
          "a British section in Italy: the mountain winter of 1943-44, and Snakeshead with the Royal Sussex's own figure")
    check(pg.evaluate("() => SVC.war('italy_british').medicine") == 20, "with the era's medicine on the sick")

    # the fourth war: a British section on the Western Front, and its wastage in the line
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "wwi")
    pg.select_option("#sel-region", "british")
    pg.select_option("#sel-template", "section")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('western_front').seasons.findIndex(s => s.id === '1916-spring')")
    pg.select_option("#sv-season", str(k))
    check("shelled or sniped in the line: 10% a man" in pg.inner_text("#service"), "holding the line, each man risks the wastage in the line")
    pg.evaluate(SEEDED, 3)
    pg.click("#btn-serve")
    log = pg.inner_text("#service")
    check(log.count("Shelled or sniped in the line: 10%") >= 1, "the season's log gives each man's wastage roll")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()


main(run, server)
