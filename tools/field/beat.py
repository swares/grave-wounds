"""The field page's End the battle button and its Beat history panel, in a headless browser.

    python3 tools/field/beat.py

Lays out Snipe and Dak To with their armies as drawn up, checks the panel shows the battle as fought
and the enemy commander's odds, ends one battle by hand with the button (not scored: undecided), and
runs one with the commander on both sides to its end (a test run, not scored), then scores a side as
the player's and keeps it on the scorecard. Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
PAGE = (ROOT / "dist" / "field.html").as_uri()
BENCHED = len(json.loads((ROOT / "tools" / "selfplay" / "commander.json").read_text())["fields"])   # the battlefields with a benchmark
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1400, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(PAGE)

    pg.select_option("#sel-field", "snipe-1942")
    pg.click("#btn-field")
    text = pg.inner_text("#beat")
    check(pg.is_visible("#beat"), "a battlefield with its armies as drawn up shows Beat history")
    check("As fought: British won" in text, "the panel gives the battle as fought")
    check("British win 25%" in text and "To beat it:" in text, "the panel gives the commander's odds and the bar")
    check("older rules" not in text, "the benchmark was run under these rules")

    pg.select_option("#sel-ai1", index=1)
    pg.click("#btn-next")
    pg.click("#btn-end")
    check(pg.is_visible("#after-box"), "End the battle ends it (the after-battle box shows)")
    check("Not scored" in pg.inner_text("#beat"), "a battle ended by hand before it was decided is not scored")

    pg.click("#btn-reset")
    pg.select_option("#sel-field", "dakto-1967")
    pg.click("#btn-field")
    pg.select_option("#sel-ai0", index=1)
    pg.select_option("#sel-ai1", index=1)
    pg.click("#btn-next")
    pg.click("#btn-run")
    pg.wait_for_selector("#after-box:not([hidden])", timeout=300000)
    check("nothing is scored" in pg.inner_text("#beat"), "with the commander on both sides, a run is not scored")
    pg.evaluate("() => { S.ai = [null, S.ai[1]]; render() }")
    text = pg.inner_text("#beat")
    check("Your result as United States and ARVN" in text, "a side the commander did not play is scored")
    check("history" in text.split("Your result")[-1] and "enemy commander" in text.split("Your result")[-1],
          "the result is set against history and the commander")
    check("Your best here" not in text, "a run the commander played on both sides was not kept on the scorecard")
    pg.evaluate("() => { recordBeat(S.drawnUp); render() }")
    text = pg.inner_text("#beat")
    check("Your best here: United States and ARVN" in text, "a scored result is kept on the scorecard")
    check(f"of {BENCHED}" in text, "the scorecard counts the battlefields where the commander was beaten")
    card = pg.evaluate("() => JSON.parse(localStorage.getItem('gravewounds-beat'))")
    check(list(card) == ["dakto-1967"] and "0" in card["dakto-1967"], "the scorecard is kept in the browser, by battlefield and side")

    pg.click("#btn-reset")
    pg.click("#chk-armies")
    pg.click("#btn-field")
    check(pg.is_hidden("#beat"), "the ground alone, without the armies as drawn up, shows no panel")
    check(not errors, f"no page errors {errors}")
    browser.close()

print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
sys.exit(1 if failures else 0)
