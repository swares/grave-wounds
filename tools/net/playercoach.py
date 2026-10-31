"""The player's coach: a player's page, joining by room code, in one headless browser with the GM's console.

    python3 tools/net/playercoach.py

The room server is the Worker's own code on a local port (tools/net/fakerooms.mjs), as rooms.py runs it.
The start page's Join a game as a player opens the code form, where the coach says to type the code;
joined, it says what his panels are (Got it); then how to propose orders, until he proposes; a fight
coming to him shows its own step; reloaded, the steps he has done stay done; No more tips puts it away.
Needs Node, Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import functools, http.server, subprocess, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
MAP = "towton-1461"
CONNECTED = "() => document.querySelector('#p-status').textContent.startsWith('Connected')"
COACH = "#p-coach"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return None


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
SITE = f"http://127.0.0.1:{server.server_port}/"
BASE = SITE + "dist/"
rooms = subprocess.Popen(["node", str(ROOT / "tools" / "net" / "fakerooms.mjs")], stdout=subprocess.PIPE, text=True)
ROOMS = rooms.stdout.readline().strip()


def coach(pg):
    return pg.inner_text(COACH) if pg.is_visible(COACH) else ""


try:
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--disable-features=WebRtcHideLocalIpsWithMdns"])
        gm = br.new_context(viewport={"width": 1400, "height": 1100}).new_page()
        errors = []

        def watch(pg):
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("dialog", lambda d: d.accept())
        watch(gm)
        gm.goto(BASE + "travel.html"); gm.evaluate("() => localStorage.clear()"); gm.reload()
        gm.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
        gm.evaluate(f"""() => {{ S.mapId = {MAP!r}; S.clock = {{}}; save(); const a = forcesHere()[0];
          const man = name => ({{ name, map: {MAP!r}, force: a.id, pid: 'pid-' + name, endurance: 50, log: [], health: {{ cases: [], immune: {{}}, had: {{}}, dead: 0 }} }});
          localStorage.setItem('gravewounds-named', JSON.stringify({{ u1: man('Hal Ashby') }})); save() }}""")
        gm.goto(BASE + "campaign.html")
        gm.wait_for_selector("#pl-room", state="attached", timeout=15000)
        gm.click("#c-players details summary")
        gm.fill("#pl-room", ROOMS); gm.click("#pl-room-set")
        gm.fill("#pl-name", "Scott"); gm.uncheck("#pl-stun"); gm.check('[data-pl-new][value="u1"]'); gm.click("#pl-add")
        gm.wait_for_function("() => { const pl = REC.players.find(p => p.name === 'Scott'); return pl && PL.conn[pl.id]?.room }", timeout=15000)
        code = gm.evaluate("() => PL.conn[REC.players[0].id].room")
        # the player: the start page's button, then his code
        pl = br.new_context(viewport={"width": 1300, "height": 1000}).new_page(); watch(pl)
        pl.goto(SITE + "index.html")
        pl.click("a[href='dist/campaign.html#room']")
        pl.wait_for_selector("#p-code")
        if ROOMS not in pl.url:                       # the test's room server, as a GM's link names it (the start page names the site's own)
            pl.goto(BASE + "campaign.html#room&s=" + ROOMS); pl.wait_for_selector("#p-code")
        check("room code" in coach(pl) and "Join" in coach(pl), f"the start page's button opens the code form, and the coach says what to do ({coach(pl)[:50]})")
        pl.fill("#p-code", code); pl.click("#p-code-go")
        pl.wait_for_function(CONNECTED, timeout=30000)
        pl.wait_for_function(f"() => !document.querySelector('{COACH}').hidden && document.querySelector('{COACH}').textContent.includes('Your men')", timeout=10000)
        check("Your force" in coach(pl) and "Your map" in coach(pl), "joined, the coach says what his panels are")
        pl.click(f"{COACH} button[data-pc='look']")
        pl.wait_for_function(f"() => document.querySelector('{COACH}').textContent.includes('Propose')", timeout=10000)
        check("Propose this route" in coach(pl), "Got it moves it on: how to propose his force's orders")
        pl.locator("#p-force .propose button[data-propose='to']").first.click()
        gm.wait_for_function("() => (REC.proposals || []).length > 0 || document.querySelector('#c-players').textContent.includes('Accept')", timeout=15000)
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
finally:
    rooms.terminate()
print(f"{'all checks passed' if not failures else str(len(failures)) + ' failed'}")
raise SystemExit(1 if failures else 0)
