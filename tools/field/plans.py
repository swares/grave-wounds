"""The field page's plans (data/plans.yaml; docs/units.md, Plans), in a headless browser.

    python3 tools/field/plans.py

Lays out Cowpens with its armies as drawn up: the plan box shows for the side with a plan and not
for the other, the strip lists the plan, unticking the box takes the plan off the field and ticking
it puts it back. Then, with the commander on both sides, runs the battle until the horse's step
starts and checks the log says when the militia fell back and the horse went round, and the strip
shows a step running. Needs Python's playwright with
Chromium and a built site. Exits non-zero on any failure.
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


with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1400, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(PAGE)

    pg.select_option("#sel-field", "cowpens-1781")
    pg.click("#btn-field")
    check(pg.is_visible("#lbl-plan0") and pg.is_hidden("#lbl-plan1"), "the plan box shows for the side with a plan (the Americans) only")
    stage = pg.inner_text("#stage")
    check("Plans:" in stage and "Washington's horse going round (7th Fusiliers)" in stage, "the strip lists the plan in set-up")

    pg.click("#chk-plan0")
    check(pg.evaluate("() => !S.field.plan") and "Plans:" not in pg.inner_text("#stage"), "unticking the box takes the plan off the field")
    pg.click("#chk-plan0")
    check(pg.evaluate("() => !!S.field.plan?.Americans"), "ticking it puts the plan back")

    pg.select_option("#sel-ai0", index=2)          # holding, as fought
    pg.select_option("#sel-ai1", index=1)          # attacking, as fought
    pg.click("#btn-next")
    check(pg.is_disabled("#chk-plan0"), "the plan is chosen in set-up only")
    pg.click("#btn-run")
    pg.wait_for_function("() => S.log.some(l => l.text.startsWith(\"Plan: Washington's horse\"))", timeout=600000)
    pg.evaluate("() => stopRun()")
    lines = pg.evaluate("() => S.log.filter(l => l.text.startsWith('Plan: ')).map(l => l.text)")
    check("Plan: Militia line (Pickens) (Americans) fall back, as planned (The militia fall back has begun)." in lines
          or "Plan: Militia line (Pickens) (Americans) fall back, as planned (they have lost 15% of their men)." in lines,
          f"the log says when the militia fall back and why ({lines})")
    check("Plan: Washington's horse (Americans) go round to strike 7th Fusiliers in the flank (About-face and bayonets has begun)." in lines,
          f"the log says when the horse go round and why ({lines})")
    pg.evaluate("() => render()")
    stage = pg.inner_text("#stage")
    check("Plans running:" in stage and "Washington's horse going round" in stage, "the strip shows the step running")
    check(not errors, f"no page errors {errors}")
    browser.close()

print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
sys.exit(1 if failures else 0)
