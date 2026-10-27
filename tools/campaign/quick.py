"""The quick start in a headless browser, served as the site is: the start page's Play in 15 minutes.

    python3 tools/campaign/quick.py

The start page's button makes the Rules' running-example retinue in the team builder (the men the Rules'
examples name) and sets up the roller's fight against four Lancastrian billmen, the GM's script playing
them; the player's men are played here as a new player would, by the coach's words: Roll initiative,
Next fighter, Stay, click an enemy, Roll the hit, Next fighter, until the fight is over. Needs Python's
playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import sys
from playwright.sync_api import sync_playwright
from harness import ROOT, check, failures, serve

BASE, server = serve()
RULES = (ROOT / "dist" / "rules.html").read_text(encoding="utf-8")

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1400, "height": 1100})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE.replace("dist/", "") + "index.html")
    pg.evaluate("() => localStorage.clear()")
    pg.click("text=Play in 15 minutes")
    pg.wait_for_function("() => location.pathname.endsWith('roller.html') && typeof S === 'object' && S.quick", timeout=20000)
    men = pg.evaluate("() => S.chars.filter(c => c.sheet).map(c => c.name)")
    foes = pg.evaluate("() => S.chars.filter(c => sideOf(c) === 'Lancastrians').length")
    check(len(men) == 6 and foes == 4, f"Play in 15 minutes sets up the retinue's six against four billmen ({men})")
    check(all(m in RULES for m in men), "the six are the men the Rules' examples and Quick start name")
    check(pg.evaluate("() => gmOn() && gmSide('Lancastrians').ctl === 'script' && gmSide('The retinue').ctl === 'player'"),
          "the GM's script plays the billmen; the player plays the retinue")
    check(pg.is_visible("#coach") and "Roll initiative" in pg.inner_text("#coach"), "the coach says what to press first")
    check(pg.evaluate("() => location.hash") == "", "the page drops #quickstart, so a reload does not set it up again")

    pg.click("#btn-init"); pg.click("#btn-next")
    turns, struck = 0, 0
    for _ in range(400):
        if pg.evaluate("() => !!gmOver()"):
            break
        pg.wait_for_timeout(50)
        if not pg.evaluate("() => { const c = actingChar(); return !!c && !scripted(c) && !(GMQ.running) }"):
            continue
        coach = pg.inner_text("#coach")
        if "Click a hex" in coach and pg.locator("button[data-map=stay]").count():
            pg.click("button[data-map=stay]")
            turns += 1
        coach = pg.inner_text("#coach")
        if "Click an enemy" in coach:
            target = pg.evaluate("() => { const c = actingChar(), t = S.chars.find(o => sideOf(o) !== sideOf(c) && !isOut(o) && o.pos && canTarget(c, o)); return t ? t.id : null }")
            if target is not None:
                pg.click(f"#map .tok[data-id='{target}']")
                if pg.locator("button[data-map=roll]").count():
                    pg.click("button[data-map=roll]")
                    struck += 1
        pg.click("#btn-next")
    over = pg.evaluate("() => gmOver()")
    check(bool(over), f"played by the coach's words, the fight ends ({over}; {turns} turns, {struck} strikes by the player)")
    check(struck >= 1 and pg.evaluate("() => S.events.filter(e => e.type === 'wound').length") >= 1, "the player's men struck, and someone was wounded")
    check("Quick start" in pg.inner_text("#coach") and "After the fight" in pg.inner_text("#coach"), "at the end the coach points to After the fight and the Rules' Quick start")
    pg.click("#coach button[data-coach=done]")
    check(pg.is_hidden("#coach"), "Done puts the coach away")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()
server.shutdown()
print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
sys.exit(1 if failures else 0)
