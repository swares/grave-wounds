"""The field page's side view (the View select; online, a seat's screen), in a headless browser.

    python3 tools/field/sideview.py

On the page's own Towton skirmish (Yorkist billmen and archers against Lancastrian), drawn up 440 m
apart on a dark night (sight 25 hexes): the GM's view draws every unit; the Yorkists' view draws only
theirs, and lists only theirs, and leaves out a log line naming an enemy it does not see; once the
Lancastrian billmen come within sight they are drawn, and when they go back out of it a mark stays
where they were last seen; the Lancastrians' view draws the Lancastrians; the choice is kept with
the battle. Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
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


DRAWN = "() => document.querySelectorAll('#map g.unit').length"
GHOSTS = "() => [...document.querySelectorAll('#map g.ghost title')].map(t => t.textContent)"
LISTED = "() => [...document.querySelectorAll('#units li')].map(li => li.textContent)"

with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1400, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(PAGE)
    pg.evaluate("() => { localStorage.clear(); freshState(); [[8, 20], [6, 13], [52, 20], [54, 27]].forEach((h, i) => { S.units[i].pos = h }); render() }")
    pg.select_option("#sel-light", "night")
    pg.click("#btn-next")                                   # into the battle: the sides keep what they see from here
    check(pg.evaluate(DRAWN) == 4, "the GM's view draws all four units")
    opts = pg.eval_on_selector_all("#sel-screen option", "os => os.map(o => o.textContent)")
    check(opts == ["Everything (the GM)", "Yorkists' view", "Lancastrians' view"], f"the View select offers the GM and each side ({opts})")

    pg.select_option("#sel-screen", "Yorkists")
    check(pg.evaluate(DRAWN) == 2, "the Yorkists' view draws only their two units on a dark night")
    check(all("Lancastrian" not in t and "Lanc" not in t for t in pg.evaluate(LISTED)) and len(pg.evaluate(LISTED)) == 2, "and lists only them")
    pg.evaluate("() => { S.log.unshift({ cls: 'morale', text: unitName(S.units[2]) + ' are steady.' }, { cls: 'morale', text: unitName(S.units[0]) + ' are steady.' }); render() }")
    log = pg.inner_text("#log")
    check(pg.evaluate("() => unitName(S.units[2])") not in log and pg.evaluate("() => unitName(S.units[0])") in log, "the log leaves out a line naming an enemy it does not see, and keeps its own")

    pg.evaluate("() => { S.units[2].pos = [12, 20]; render() }")      # the Lancastrian billmen come close
    check(pg.evaluate(DRAWN) == 3, "the enemy billmen, within sight, are drawn")
    pg.evaluate("() => { S.exchange += 1; S.units[2].pos = [52, 20]; render() }")   # and go back into the dark
    ghosts = pg.evaluate(GHOSTS)
    check(pg.evaluate(DRAWN) == 2 and len(ghosts) == 1 and "last seen here in exchange" in ghosts[0], f"out of sight again, a mark stays where they were last seen ({ghosts})")
    check(pg.evaluate("() => S.views.Yorkists['2'].pos.join(',')") == "12,20", "at the hex they were seen in")

    pg.evaluate("() => { S.sel = S.units[3].id; render() }")         # an enemy it does not see cannot stay selected
    check(pg.evaluate("() => S.sel") is None, "an unseen enemy is not selected in the side's view")

    pg.select_option("#sel-screen", "Lancastrians")
    check(pg.evaluate(DRAWN) == 2 and pg.evaluate("() => [...document.querySelectorAll('#units li')].length") == 2, "the Lancastrians' view draws and lists theirs")
    pg.reload()
    check(pg.evaluate("() => S.screen") == "Lancastrians" and pg.input_value("#sel-screen") == "Lancastrians", "the view is kept with the battle")
    pg.select_option("#sel-screen", "")
    check(pg.evaluate(DRAWN) == 4, "back to the GM's view, every unit is drawn")

    check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
    browser.close()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
