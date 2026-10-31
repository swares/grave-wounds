"""The player's coach: a player's page, joining by room code, in one headless browser with the GM's console.

    python3 tools/net/playercoach.py

The room server runs locally, as rooms.py runs it (roomharness.py). The start page's Join a game as a
player opens the code form, where the coach says to type the code; joined, it says what his panels are
(Got it); then how to propose orders, until he proposes; a fight coming to him shows its own step;
reloaded, the steps he has done stay done; No more tips puts it away. Needs Node, Python's playwright
with Chromium and a built site. Exits non-zero on any failure.
"""
import traceback
from playwright.sync_api import sync_playwright
from roomharness import CI, CONNECTED, add_player, campaign_with, check, failures, serve

COACH = "#p-coach"
SITE, BASE, ROOMS, stop = serve()


def coach(pg):
    return pg.inner_text(COACH) if pg.is_visible(COACH) else ""


def coach_says(pg, text):
    pg.wait_for_function(f"() => !document.querySelector('{COACH}').hidden && document.querySelector('{COACH}').textContent.includes({text!r})", timeout=10000)


try:
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--disable-features=WebRtcHideLocalIpsWithMdns"])
        gm = br.new_context(viewport={"width": 1400, "height": 1100}).new_page()
        errors = []

        def watch(pg):
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("dialog", lambda d: d.accept())
        watch(gm)
        campaign_with(gm, BASE, "towton-1461", {"u1": "Hal Ashby"})
        gm.goto(BASE + "campaign.html")
        gm.wait_for_selector("#pl-room", state="attached", timeout=15000)
        code = add_player(gm, ROOMS, "Scott", "u1")
        pl = br.new_context(viewport={"width": 1300, "height": 1000}).new_page(); watch(pl)
        pl.goto(SITE + "index.html")
        pl.click("a[href='dist/campaign.html#room']")
        pl.wait_for_selector("#p-code")
        check("room code" in coach(pl) and "Join" in coach(pl), f"the start page's button opens the code form, and the coach says what to do ({coach(pl)[:50]})")
        pl.goto(BASE + "campaign.html#room&s=" + ROOMS); pl.wait_for_selector("#p-code")   # this test's room server, as a GM's link names it
        pl.fill("#p-code", code); pl.click("#p-code-go")
        pl.wait_for_function(CONNECTED, timeout=30000)
        coach_says(pl, "Your men")
        check("Your force" in coach(pl) and "Your map" in coach(pl), "joined, the coach says what his panels are")
        pl.click(f"{COACH} button[data-pc='look']")
        coach_says(pl, "Propose")
        check("Propose this route" in coach(pl), "Got it moves it on: how to propose his force's orders")
        pl.locator("#p-force .propose button[data-propose='to']").first.click()
        pl.wait_for_timeout(500)
        check(not pl.is_visible(COACH), "once he has proposed, the coach has nothing more to say")
        pl.evaluate("() => pgFight({ t: 'screen' })")   # a fight comes to him (its screens are twopages.py's to test)
        check("Your fight" in coach(pl) and "Next fighter" in coach(pl), "a fight coming to him shows its own step")
        pl.click(f"{COACH} button[data-pc='fight']")
        pl.reload(); pl.wait_for_function(CONNECTED, timeout=45000); pl.wait_for_timeout(1500)
        check(not pl.is_visible(COACH), "reloaded, the steps he has done stay done")
        pl.evaluate("() => { localStorage.removeItem('gravewounds-player-coach'); pgCoach() }")
        pl.click(f"{COACH} button[data-pc='off']")
        check(not pl.is_visible(COACH), "No more tips puts it away")
        check(not errors, f"no page errors {errors[:3]}")
        br.close()
except Exception as e:                                # a timeout or error: where, as an annotation in CI
    print(traceback.format_exc())
    check(False, f"stopped: {str(e).splitlines()[0][:200]}")
finally:
    stop()
print(f"{'all checks passed' if not failures else str(len(failures)) + ' failed'}")
raise SystemExit(1 if failures else 0)
