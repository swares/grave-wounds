"""A travel-map force's state carried into a field battle (field.html forceState), in a headless browser.

    python3 tools/field/worn.py

A battle sent from the travel map to Towton's battlefield: the defenders exhausted, hungry and
beaten three days before; the attackers fresh, and beaten ten days before (past units.yaml's
morale beaten_days). Set up and begun, the defenders' units start exhausted (weather.yaml's
fatigue level, off their attack and defence), hungry and beaten (the morale mods), and the
log says so; the attackers' start as they were. The commander's select names the defenders'
state. Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import json
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
HANDOFF = {"from": "travel", "battle": "test:worn", "mapId": "test", "map": "Test", "place": "Towton", "day": "29 March 1461", "time": "10:00",
           "start": {"day": DAY, "used": 2}, "battlefield": "towton-1461", "camp": None, "noQuarter": [],
           "forces": [{"id": 1, "name": "Somerset's men", "side": "Lancastrians", "type": "foot", "men": 4000, "role": "defender", "care": None, "camp": None, "ammo": 1,
                       "fatigue": 3, "hungry": True, "beatenDay": DAY - 3},
                      {"id": 2, "name": "Edward's men", "side": "Yorkists", "type": "foot", "men": 4000, "role": "attacker", "care": None, "camp": None, "ammo": 1,
                       "fatigue": 0, "hungry": False, "beatenDay": DAY - 10}]}

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1400, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(PAGE)
    pg.evaluate("h => { localStorage.clear(); localStorage.setItem('gravewounds-field-handoff', JSON.stringify(h)) }", HANDOFF)
    pg.reload()
    pg.click("#btn-handoff")
    n = pg.evaluate("() => S.units.length")
    check(n > 0, f"the battlefield is drawn up from the two forces ({n} units)")
    label = pg.evaluate("() => [0, 1].map(k => document.getElementById('ai-label' + k).textContent)")
    check(any("exhausted, hungry, beaten days ago" in t for t in label) and not all("(" in t for t in label),
          f"the commander's select names the worn side's state, and only its ({label})")
    pg.evaluate("() => next()")
    st = pg.evaluate("() => S.units.map(u => ({ f: forceOf(u)?.id, fatigue: u.fatigue || 0, hungry: !!u.hungry, beaten: !!u.beaten }))")
    worn = [u for u in st if u["f"] == 1]
    fresh = [u for u in st if u["f"] == 2]
    check(worn and all(u["fatigue"] >= 3 and u["hungry"] and u["beaten"] for u in worn), "the defenders' units start exhausted, hungry and beaten")
    check(fresh and all(not u["hungry"] and not u["beaten"] for u in fresh), "the attackers' start as they were (their beating ten days back is past the week)")
    log = pg.evaluate("() => S.log.map(l => l.text).join(' | ')")
    check("Somerset's men come to the fight exhausted, hungry, beaten days ago" in log, "the log says what the defenders bring")
    mods = pg.evaluate("() => { const M = UD.morale.mods, base = { start: 100, down: 0, state: 'steady' }; return [moraleMods(M, base), moraleMods(M, { ...base, hungry: true, beaten: true })] }")
    check(mods[1] == mods[0] - 20, f"hungry and beaten cost their morale mods ({mods})")
    check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
    br.close()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
