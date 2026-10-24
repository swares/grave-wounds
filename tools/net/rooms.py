"""Room codes: the GM's console and two players' pages connected through the room server, in one headless browser.

    python3 tools/net/rooms.py

The room server is the Worker's own code (worker/rooms.js) on a local port, with an in-memory
Durable Object namespace in place of Cloudflare's (tools/net/fakerooms.mjs). Each player's page is
in a browser profile of its own. The GM adds two players; one opens his room's link, the other
types her room's code; both connect with nothing passed back by hand. A wrong code is told. A
player's page reloaded, and then the console reloaded, both come back by themselves. Needs Node,
Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import functools, http.server, subprocess, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
MAP = "towton-1461"
CONNECTED = "() => document.querySelector('#p-status').textContent.startsWith('Connected')"
PANEL, CODE = "#c-players", "#p-code"
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
BASE = f"http://127.0.0.1:{server.server_port}/dist/"
rooms = subprocess.Popen(["node", str(ROOT / "tools" / "net" / "fakerooms.mjs")], stdout=subprocess.PIPE, text=True)
ROOMS = rooms.stdout.readline().strip()


def men_of(page):
    return page.inner_text("#p-men")


try:
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--disable-features=WebRtcHideLocalIpsWithMdns"])
        gctx = br.new_context(viewport={"width": 1400, "height": 1100})
        gm = gctx.new_page()
        pages = [gm]
        errors = []

        def watch(pg):
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("dialog", lambda d: d.accept())
        watch(gm)
        # the campaign: a map, two named men with the first force; the room server chosen in this browser
        gm.goto(BASE + "travel.html"); gm.evaluate("() => localStorage.clear()"); gm.reload()
        gm.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
        gm.evaluate(f"""() => {{ S.mapId = {MAP!r}; S.clock = {{}}; save(); const a = forcesHere()[0];
          const man = name => ({{ name, map: {MAP!r}, force: a.id, pid: 'pid-' + name, endurance: 50, log: [], health: {{ cases: [], immune: {{}}, had: {{}}, dead: 0 }} }});
          localStorage.setItem('gravewounds-named', JSON.stringify({{ u1: man('Hal Ashby'), u2: man('Ann Fenwick') }})) }}""")
        gm.goto(BASE + "campaign.html")
        gm.wait_for_selector("#pl-room", state="attached", timeout=15000)
        gm.click(PANEL + " details summary")
        gm.fill("#pl-room", ROOMS); gm.click("#pl-room-set")
        check(ROOMS in gm.inner_text(PANEL) and "invited again by itself" in gm.inner_text(PANEL), f"the GM chooses a room server ({ROOMS})")
        for name, uid in (("Scott", "u1"), ("Ann", "u2")):
            gm.fill("#pl-name", name); gm.uncheck("#pl-stun"); gm.check(f'[data-pl-new][value="{uid}"]'); gm.click("#pl-add")
            gm.wait_for_function(f"() => {{ const pl = REC.players.find(p => p.name === {name!r}); return pl && PL.conn[pl.id]?.room }}", timeout=15000)
        codes = gm.evaluate("() => REC.players.map(pl => PL.conn[pl.id].room)")
        check(len(set(codes)) == 2 and all(c.count("-") == 2 for c in codes), f"each player gets a room of his own, with a code to say aloud ({codes})")
        check("Paste the reply" not in gm.inner_text(PANEL), "no reply to paste: the console waits for it in his room")
        link = gm.input_value(f'textarea[data-pl-link="{gm.evaluate("() => REC.players[0].id")}"]')
        check(f"#room={codes[0]}" in link and "&s=" in link, "his link names his room and the server")
        # Scott by his link
        sctx = br.new_context(); scott = sctx.new_page(); watch(scott); pages.append(scott)
        scott.goto(link)
        scott.wait_for_function(CONNECTED, timeout=30000)
        scott.wait_for_function("() => document.querySelector('#p-men').textContent.includes('Hal Ashby')", timeout=10000)
        check("Ann Fenwick" not in men_of(scott), "he opens his link and is connected, nothing passed back by hand; he sees his man, not hers")
        # Ann by typing her code (and a wrong one first)
        actx = br.new_context(); ann = actx.new_page(); watch(ann); pages.append(ann)
        ann.goto(BASE + "campaign.html#room&s=" + ROOMS)
        ann.wait_for_selector(CODE)
        ann.fill(CODE, "nope-nope-00"); ann.click("#p-code-go")
        ann.wait_for_function("() => document.querySelector('#p-status').textContent.includes('no room')", timeout=10000)
        check(True, "a code that is no room is told, and the code can be typed again")
        ann.fill(CODE, codes[1].lower()); ann.click("#p-code-go")
        ann.wait_for_function(CONNECTED, timeout=30000)
        ann.wait_for_function("() => document.querySelector('#p-men').textContent.includes('Ann Fenwick')", timeout=10000)
        check(gm.evaluate("() => REC.players.every(pl => PL.conn[pl.id].state === 'open')"), "she types her room's code (in small letters) and is connected too")
        # his page reloaded: back by itself
        scott.reload()
        scott.wait_for_function("() => document.querySelector('#p-men').textContent.includes('Hal Ashby')", timeout=10000)
        scott.wait_for_function(CONNECTED, timeout=45000)
        check(True, "his page reloaded comes back by itself: the console invites him again, his page answers")
        # the console reloaded: both back by themselves
        gm.reload()
        gm.wait_for_function("() => REC.players.length === 2 && REC.players.every(pl => PL.conn[pl.id]?.state === 'open')", timeout=60000)
        for pg in (scott, ann):
            pg.wait_for_function(CONNECTED, timeout=20000)
        check(True, "the console reloaded: both players are back by themselves, on the same room codes")
        check(gm.evaluate("() => REC.players.map(pl => pl.room.code)") == codes, "their rooms stay theirs")
        gm.fill("#c-note", "Rooms work."); gm.uncheck("#c-note-gm"); gm.click("#c-add-note")
        scott.wait_for_function("() => document.querySelector('#p-news').textContent.includes('Rooms work.')", timeout=10000)
        check(True, "and his page follows the campaign again")
        shots = Path(__file__).parent / ".cache"; shots.mkdir(exist_ok=True)
        gm.locator(PANEL).screenshot(path=str(shots / "rooms-gm.png"))
        check(not errors, f"no page errors {errors[:3]}")
        br.close()
finally:
    rooms.terminate()

print(f"{'all checks passed' if not failures else str(len(failures)) + ' failed'}")
raise SystemExit(1 if failures else 0)
