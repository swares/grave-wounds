"""Making a man on paper (dist/makeaman.html), and the same tables in the period books.

    python3 tools/campaign/makeaman.py

The page shows one era (the select, or #era): the steps, its tables and a blank sheet; its origin
spans read as the team builder reads its roll (row floor((roll-1)*n/100)); the choice is kept;
it fits a phone. The medieval book holds the origins and the career terms. Needs Python's
playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "dist" / "makeaman.html").as_uri()
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def row_of(roll, n):
    return (roll - 1) * n // 100


book = (ROOT / "dist" / "book-medieval.html").read_text(encoding="utf-8")
check("Origins (d100)" in book and "Career terms (d100)" in book and "Took a knight prisoner" in book,
      "the medieval book holds the origins and the career terms")

SHOWN = "() => [...document.querySelectorAll('section[data-era]')].filter(s => s.offsetParent).map(s => s.dataset.era)"
with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1100, "height": 900})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(PAGE)
    pg.evaluate("() => localStorage.clear()")
    SPANS = "() => [...document.querySelectorAll('section[data-era] h3')].filter(h => h.textContent.startsWith('Origins')).map(h => [...h.nextElementSibling.querySelectorAll('tbody tr td:first-child')].map(td => td.textContent))"
    for spans in pg.evaluate(SPANS):
        n, ok = len(spans), True
        for i, sp in enumerate(spans):
            lo, hi = (sp.split("–") if "–" in sp else [sp, sp])
            ok &= all(row_of(int(x) or 100, n) == i for x in (lo, hi))
        check(ok, f"the d100 spans of {n} origins read as the team builder rolls (row floor((roll-1)*n/100))")
    pg.goto(PAGE + "#wwi")
    check(pg.evaluate(SHOWN) == ["wwi"], f"#wwi shows that era alone ({pg.evaluate(SHOWN)})")
    sec = pg.inner_text("section[data-era=wwi]")
    check("Roll 3d6 × 5" in sec and "Origins (d100)" in sec and "Career terms (d100)" in sec and "Purse (Days)" in sec,
          "with the steps, the origins, the terms and a blank sheet")
    pg.select_option("#era", "medieval")
    pg.reload()
    check(pg.evaluate(SHOWN) == ["medieval"], "the choice is kept")
    ph = br.new_page(viewport={"width": 390, "height": 800})
    ph.goto(PAGE)
    check(ph.evaluate("() => document.documentElement.scrollWidth") <= 390, "no sideways scroll on a phone")
    check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
    br.close()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
