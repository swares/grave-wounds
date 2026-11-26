"""The armoury (dist/armoury.html): each era's common weapons and armour, printed one era at a time.

    python3 tools/campaign/armoury.py

Every era has a section with its weapons and kits; the Era select (or #era in the link) shows one
and hides the rest; Show notes hides and shows the data's notes; the page fits a phone. Needs
Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "dist" / "armoury.html").as_uri()
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


SHOWN = "() => [...document.querySelectorAll('section[data-era]')].filter(s => s.offsetParent).map(s => s.dataset.era)"
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1100, "height": 900})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(PAGE)
    pg.evaluate("() => localStorage.clear()")
    pg.goto(PAGE + "#horse_musket")
    check(pg.evaluate(SHOWN) == ["horse_musket"], f"#horse_musket shows that era alone ({pg.evaluate(SHOWN)})")
    body = pg.inner_text("section[data-era=horse_musket]")
    check("Smoothbore musket" in body and "Bayonet" in body and "Cuirassier" in body, "with its musket, the bayonet that goes with it, and the cuirassier's kit")
    check("Range 25 / 50 / 100 hexes" in body and "Steel cuirass" in body, "the musket's range bands and the materials' steps")
    check(pg.is_visible("section[data-era=horse_musket] tr.note"), "the notes show")
    pg.uncheck("#notes")
    check(not pg.is_visible("section[data-era=horse_musket] tr.note"), "Show notes off hides them")
    pg.goto(PAGE + "#wwi")
    check("Bayonet" in pg.inner_text("section[data-era=wwi]"), "the First World War lists the bayonet its riflemen train in")
    for era in ("wwii", "korea", "vietnam", "modern"):
        pg.goto(PAGE + "#" + era)
        check("Bayonet" in pg.inner_text(f"section[data-era={era}]"), f"{era} lists the bayonet its riflemen's terms teach")
    pg.select_option("#era", "")
    check(len(pg.evaluate(SHOWN)) == 11, "Every era shows all eleven")
    pg.select_option("#era", "medieval")
    pg.reload()
    try:                                               # the page restores the choice as it loads; on a slow runner the check came first (CI, 25 November 2026)
        pg.wait_for_function(f"want => JSON.stringify(({SHOWN})()) === want", arg='["medieval"]', timeout=5000)
    except Exception:
        pass                                           # the check below says what it found
    check(pg.evaluate(SHOWN) == ["medieval"] and not pg.is_visible("section[data-era=medieval] tr.note"), "the choice is kept on reload")
    ph = br.new_page(viewport={"width": 390, "height": 800})
    ph.goto(PAGE)
    check(ph.evaluate("() => document.documentElement.scrollWidth") <= 390, "no sideways scroll on a phone")
    check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
    br.close()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
