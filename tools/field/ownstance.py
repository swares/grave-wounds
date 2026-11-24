"""The commander's own choice of stance on the field map (field.html ownStance), in a headless browser.

    python3 tools/field/ownstance.py

1. The page's own Towton skirmish: left to its own choice, the side with more men attacks and the
   other holds (evenly matched, both attack); the choice is made when the battle begins and the log says why.
2. Agincourt laid out as drawn up: as fought (the English hold, the French attack).
3. From the travel map: fresh attackers attack and the defenders hold; worn attackers hold; fresh
   defenders outnumbering the attackers 1.5 times attack, and the attackers, outnumbered, hold.
Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "dist" / "field.html").as_uri()
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


DAY = 2440000


def handoff(def_men, att_men, att_worn):
    return {"from": "travel", "battle": "test:own", "mapId": "test", "map": "Test", "place": "Towton", "day": "29 March 1461", "time": "10:00",
            "start": {"day": DAY, "used": 2}, "battlefield": None, "camp": None, "noQuarter": [],
            "forces": [{"id": 1, "name": "Somerset's men", "side": "Lancastrians", "type": "foot", "men": def_men, "role": "defender", "care": None, "camp": None, "ammo": 1, "fatigue": 0, "hungry": False, "beatenDay": None},
                       {"id": 2, "name": "Edward's men", "side": "Yorkists", "type": "foot", "men": att_men, "role": "attacker", "care": None, "camp": None, "ammo": 1,
                        "fatigue": 3 if att_worn else 0, "hungry": False, "beatenDay": None}]}


STANCES = "() => [S.ai[0], S.ai[1]]"
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1400, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(PAGE)
    pg.evaluate("() => { localStorage.clear(); freshState(); render() }")
    opts = pg.eval_on_selector_all("#sel-ai0 option", "os => os.map(o => o.value)")
    check(opts == ["", "attack", "hold", "own"], f"the commander's select offers its own choice ({opts})")
    pg.evaluate("() => { S.units[0].men += 40; S.units[0].start += 40; render() }")   # the first side the bigger
    big = pg.evaluate("() => { const m = k => S.units.filter(u => u.side === S.sides[k]).reduce((t, u) => t + u.men, 0); return m(0) > m(1) ? 0 : 1 }")
    pg.select_option("#sel-ai0", "own")
    pg.select_option("#sel-ai1", "own")
    pg.evaluate("() => next()")
    st = pg.evaluate(STANCES)
    check(st[big] == "attack" and st[1 - big] == "hold", f"the skirmish: the side with more men attacks, the other holds ({st})")
    log = pg.evaluate("() => S.log.map(l => l.text).join(' | ')")
    check("attacks: the stronger" in log and "holds: the weaker" in log, "and the log says why")
    check("its own choice (attacking)" in pg.inner_text("#sel-ai" + str(big)), "the select shows what it chose")

    pg.evaluate("() => { localStorage.clear(); freshState(); render() }")
    pg.select_option("#sel-field", "agincourt-1415")
    pg.click("#btn-field")
    pg.select_option("#sel-ai0", "own")
    pg.select_option("#sel-ai1", "own")
    pg.evaluate("() => next()")
    st = pg.evaluate(STANCES)
    check(st == ["hold", "attack"] and "as the battle was fought" in pg.evaluate("() => S.log.map(l => l.text).join(' ')"),
          f"Agincourt as drawn up: as fought, the English hold and the French attack ({st})")

    for (dm, am, worn), want, what in (((2000, 2000, False), ["hold", "attack"], "fresh attackers attack, the defenders hold"),
                                        ((2000, 2000, True), ["hold", "hold"], "worn attackers hold"),
                                        ((4000, 2000, False), ["attack", "hold"], "fresh defenders outnumbering the attackers twice attack, and the outnumbered attackers hold")):
        pg.evaluate("h => { localStorage.clear(); localStorage.setItem('gravewounds-field-handoff', JSON.stringify(h)) }", handoff(dm, am, worn))
        pg.reload()
        pg.click("#btn-handoff")
        pg.evaluate("""() => { for (const f of S.forces){ const k = S.sides.indexOf(forceSide(f));
          S.units.push(newUnit({ name: f.name, side: S.sides[k], men: f.men, quality: 'regular', weapon: 'bill', kit: 'jack_sallet', formation: 'close', facing: k ? 3 : 0, force: f.id, pos: k ? [30, 20] : [10, 20] })) } render() }""")
        pg.select_option("#sel-ai0", "own")
        pg.select_option("#sel-ai1", "own")
        pg.evaluate("() => next()")
        st = pg.evaluate(STANCES)
        check(st == want, f"from the travel map, {what} ({st})")
    check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
    br.close()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
