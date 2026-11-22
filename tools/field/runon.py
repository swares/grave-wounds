"""The field page's Run on (docs/units.md, Running on), in a headless browser.

    python3 tools/field/runon.py

On the page's own Towton skirmish (Yorkist billmen and archers against Lancastrian), drawn up 440 m
apart, with seeded dice:
a march order is set and cleared from the unit's buttons and the map; the units run on toward their
march hexes and stop, before any blow or shot lands, once an enemy is within reach; Run on then
refuses to start; a unit reaching its march hex stops the run and drops the order; with nothing to stop
for, Stop stops it; with the commander on one side its side is ordered as ever; with the commander on
both, Run on is hidden (Run plays on). Needs Python's playwright with Chromium and a built site. Exits
non-zero on any failure.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "dist" / "field.html").as_uri()
SEED = 101
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


def fresh(pg):
    """The page's own skirmish, in set-up, with seeded dice."""
    pg.evaluate("() => { localStorage.clear(); freshState(); [[8, 20], [6, 13], [52, 20], [54, 27]].forEach((h, i) => { S.units[i].pos = h }); render() }")   # 440 m apart, beyond a longbow and a charge
    pg.evaluate("() => { const sd = new SeededDice(SEED); dice.randint = (a, b) => sd.randint(a, b); dice.random = () => sd.random() }".replace("SEED", str(SEED)))


def march(pg, i, h):
    pg.evaluate("([i, h]) => { S.units[i].march = h; render() }", [i, h])


def run_on(pg):
    pg.click("#btn-runon")
    pg.wait_for_function("() => !RUNON", timeout=300000)
    return pg.evaluate("() => S.msg")


FIRE = "() => S.log.filter(l => / strike | shoot at | fire /.test(l.text)).length"

with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1400, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(PAGE)

    # the order from the buttons and the map
    fresh(pg)
    pg.evaluate("() => { S.sel = S.units[0].id; render() }")
    pg.click("#btn-march")
    check(pg.inner_text("#btn-march") == "Click a hex…", "March to… waits for a hex")
    pg.click('.hx[data-h="30,20"]', force=True)
    check(pg.evaluate("() => JSON.stringify(S.units[0].march)") == "[30,20]", "clicking a hex gives the unit its march hex")
    check(pg.locator("#map text.march").count() == 1 and pg.inner_text("#btn-march") == "Stop marching", "the map marks the hex, the button stops the march")
    pg.click("#btn-march")
    check(pg.evaluate("() => !S.units[0].march") and pg.locator("#map text.march").count() == 0, "Stop marching clears it")
    check(pg.is_hidden("#btn-runon"), "Run on is not offered in set-up")

    # marching on the enemy: it stops with the enemy in reach, before anything lands
    fresh(pg)
    march(pg, 0, [46, 20])
    march(pg, 1, [45, 13])
    pg.click("#btn-next")
    before = pg.evaluate("() => S.units[0].pos.join(',')")
    msg = run_on(pg)
    print("     " + msg)
    check(msg.startswith("Run on stops after") and ("within reach" in msg or "within a charge" in msg or "in contact" in msg), "the run stops with an enemy in reach")
    check(pg.evaluate("() => S.exchange") > 2 and pg.evaluate("() => S.units[0].pos.join(',')") != before, "it ran on several exchanges, the billmen marching")
    check(pg.evaluate(FIRE) == 0, "nothing had landed when it stopped")
    pg.click("#btn-runon")
    check(pg.evaluate("() => S.msg").startswith("Not out of reach") and pg.evaluate("() => !RUNON"), "Run on refuses to start in reach")

    # reaching the march hex
    fresh(pg)
    march(pg, 1, [7, 13])
    pg.click("#btn-next")
    msg = run_on(pg)
    print("     " + msg)
    check("reached their march hex" in msg, "reaching its hex stops the run")
    check(pg.evaluate("() => !S.units[1].march && S.units[1].pos.join(',')") == "7,13", "the unit stands on it, the order done")

    # nothing to stop for: Stop
    fresh(pg)
    pg.click("#btn-next")
    pg.click("#btn-runon")
    pg.wait_for_function("() => S.exchange >= 4", timeout=60000)
    pg.click("#btn-runon")
    check(pg.evaluate("() => !RUNON") and "you stopped it" in pg.evaluate("() => S.msg"), "Stop stops it")
    check(pg.evaluate(FIRE) == 0, "both sides holding far apart, nothing landed")

    # the commander on one side
    fresh(pg)
    pg.select_option("#sel-ai1", "hold")
    march(pg, 0, [30, 20])
    pg.click("#btn-next")
    msg = run_on(pg)
    print("     " + msg)
    check(msg.startswith("Run on stops after"), "with the commander holding the other side, it runs on and stops")
    pg.select_option("#sel-ai0", "attack")
    check(pg.is_hidden("#btn-runon") and pg.is_visible("#btn-run"), "with the commander on both sides, Run on is hidden")

    check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
    browser.close()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
