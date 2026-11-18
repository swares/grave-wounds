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
    men = pg.evaluate("() => S.chars.filter(c => c.uid && c.team).length")
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
          f"the escalade: the retinue's {men} named men go up the ladders against the guard with crossbows ({esc['fw']}, {esc['fk']})")
    check("Defending: The guard on the wall" in esc["msg"], "the French guard holds the wall; the English come in from the edge")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()


main(run, server)
