"""The GM's coached first session in a headless browser, served as the site is: the start page's link to
campaign.html#gmstart.

    python3 tools/campaign/gmstart.py [seed]

The link starts a campaign on the Towton map, 1461; the team builder makes the Rules' example retinue and
the roller adds it and puts it with Edward's army. Then the GM presses what the coach says, phase by
phase: Done (on to march), Orders and Set the route, Until something happens until the army meets the
enemy, the fight set up on the roller and run by the script, the winner marked, the aftermath, downtime,
and the coach dismissed. A campaign already under way is kept beside it. Needs Python's playwright with
Chromium and a built site. Exits non-zero on any failure.
"""
import sys
import traceback
from playwright.sync_api import sync_playwright
from harness import DICE, check, failures, serve

BASE, server = serve()
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 1
COACH = "#c-coach"


def coach(pg):
    return pg.inner_text(COACH) if pg.is_visible(COACH) else ""


def wait_coach(pg, text, timeout=45000):
    pg.wait_for_function(f"() => !document.querySelector('{COACH}').hidden && document.querySelector('{COACH}').textContent.includes({text!r})", timeout=timeout)


def run(p):
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 1500, "height": 1200})
    ctx.add_init_script(DICE % SEED)
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE.replace("dist/", "") + "index.html")
    pg.evaluate("() => localStorage.clear()")
    pg.click("a[href='dist/campaign.html#gmstart']")
    wait_coach(pg, "1.")
    fr = pg.frame_locator("#c-frame")
    check("Edward's army" in coach(pg) and "Done: on to march" in coach(pg), f"the start page's link sets it all up, and the coach says what next ({coach(pg)[:70]})")
    named = pg.evaluate("() => Object.values(JSON.parse(localStorage.getItem('gravewounds-named') || '{}'))")
    check(len(named) == 6 and all(n.get("map") == "towton-1461" and n.get("force") == 1 for n in named), "the retinue's six men are named men, with Edward's army on the Towton map")
    check(pg.evaluate("() => REC.name") == "The road to Towton", "the campaign is named for it")
    pg.click("#c-next")
    wait_coach(pg, "2.")
    check("Orders" in coach(pg), "on the march, the coach says to give Edward's army its route")
    pg.locator("button[data-orders]").first.click()
    pg.wait_for_selector("tr.orders select[data-pick='to']", timeout=6000)
    towton = pg.locator("select[data-pick='to'] option", has_text="Towton").first.get_attribute("value")
    pg.select_option("select[data-pick='to']", towton)
    pg.click("button[data-order='to']")
    wait_coach(pg, "3.")
    check("Until something happens" in coach(pg), "with its route set, the coach says to move the clock on")
    for _ in range(25):
        if "4." in coach(pg) or not pg.locator("#c-run").is_enabled():
            break
        pg.click("#c-run"); pg.wait_for_timeout(800)
    check("Fights on offer" in coach(pg), f"when the army meets the enemy, the coach says to set up the fight ({coach(pg)[:60]})")
    first = pg.locator("#c-march .fights li").first
    first.locator("select").select_option("roller")
    first.locator("button[data-fight]").first.click()
    wait_coach(pg, "5.")
    check("Set up the fight" in coach(pg), "the fight sent, the coach says to take it in on the roller")
    pg.wait_for_function("() => document.querySelector('#c-showing').textContent.includes('Wound roller')", timeout=15000)
    fr.get_by_role("button", name="Set up the fight").first.click()
    wait_coach(pg, "6.")
    check("Run the fight" in coach(pg), "the fight on the roller, the coach says to run it")
    pg.click("#c-fight button[data-fightcmd='start']")
    wait_coach(pg, "7.")
    check("Play to my turn" in coach(pg), "running, the coach says how a turn goes")
    # a whole fight is the quick start's own test (quick.py): here the fight is called for York on the roller,
    # as After the fight's winner does
    pg.frames[1].evaluate("() => { S.wonBy = 'York'; S.afterOpen = true; save(); renderChars() }")
    wait_coach(pg, "8.")
    check("Send the result to the travel map" in coach(pg), "the winner marked, the coach moves to the aftermath")
    pg.click("#c-next")
    wait_coach(pg, "9.")
    check("Save the game to a file" in coach(pg), "in downtime, the coach says to save the game")
    pg.click(f"{COACH} button[data-coach='done']")
    pg.wait_for_timeout(500)
    check(not pg.is_visible(COACH), "Done with the coach hides it")
    # a campaign under way is kept beside the coached one (the link followed again, in the same tab)
    pg.evaluate("() => { location.hash = '#gmstart' }")
    wait_coach(pg, "1.")
    pg.wait_for_timeout(1500)
    kept = pg.evaluate("async () => (await IDB.all()).length")
    check(kept >= 2, f"a campaign under way is kept when the coached session starts again ({kept} in this browser)")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()


try:
    with sync_playwright() as pw:
        run(pw)
except Exception as e:                               # a timeout or error: where, as an annotation in CI
    print(traceback.format_exc())
    check(False, f"stopped: {str(e).splitlines()[0][:300]}")
server.shutdown()
if failures:
    print(f"{len(failures)} check(s) failed")
    sys.exit(1)
print("all checks passed")
