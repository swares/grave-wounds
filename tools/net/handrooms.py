"""The players follow a GM handover through their rooms: two GMs' consoles and a player, in one headless browser.

    python3 tools/net/handrooms.py

The first GM adds three players with rooms; Scott opens his link and is connected, the other two wait.
The GM hands the game to Ann: his console lets Scott go (Scott's page falls back to waiting in his
room) and, reloaded, invites no one. Ann's console, in a browser of its own, loads the file and invites
every player through the same rooms: Scott is back with no new link, and the two still waiting are
listed together, one line each, for a group chat. Taking the game back would invite them again from the
first console. Needs Node, Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import tempfile
from pathlib import Path
from playwright.sync_api import sync_playwright
from roomharness import CONNECTED, add_player, campaign_with, check, failures, serve

MAP = "towton-1461"
_, BASE, ROOMS, stop = serve()
WAITING = "() => document.querySelector('#p-status').textContent.toLowerCase().includes('waiting')"
ROOMS_OF = "() => REC.players.map(pl => pl.room.code)"


def scott_at(pg):
    return pg.evaluate("() => PL.conn[REC.players.find(p => p.name === 'Scott').id]?.state")


try:
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--disable-features=WebRtcHideLocalIpsWithMdns"])
        errors = []

        def page(**kw):
            pg = br.new_context(viewport={"width": 1400, "height": 1100}, **kw).new_page()
            pg.on("pageerror", lambda e: errors.append(str(e)))
            pg.on("dialog", lambda d: d.accept())
            return pg
        gm = page(accept_downloads=True)
        campaign_with(gm, BASE, MAP, {"u1": "Hal Ashby", "u2": "Ann Fenwick"})
        gm.goto(BASE + "campaign.html")
        gm.wait_for_selector("#pl-room", state="attached", timeout=15000)
        codes = [add_player(gm, ROOMS, "Scott", "u1"), add_player(gm, ROOMS, "Kate", "u2"), add_player(gm, ROOMS, "Tom", "u2")]
        scott = page()
        scott.goto(gm.input_value(f'textarea[data-pl-link="{gm.evaluate("() => REC.players[0].id")}"]'))
        scott.wait_for_function(CONNECTED, timeout=30000)
        check(True, "Scott opens his room's link and is connected")

        # handed over: the first console lets him go, and invites no one again
        gm.fill("#c-name", "Towton"); gm.press("#c-name", "Tab")
        gm.click("#c-hand")
        gm.fill("#c-hand-to", "Ann")
        gm.fill("#c-hand-pass", "oak"); gm.fill("#c-hand-pass2", "oak")
        with gm.expect_download() as dl:
            gm.click("#c-hand-form button[type=submit]")
        path = Path(tempfile.mkdtemp()) / "handover.json"
        dl.value.save_as(path)
        check("wait in their rooms" in gm.inner_text("#c-saved"), "the first GM is told his players wait in their rooms for the next console")
        scott.wait_for_function(WAITING, timeout=20000)
        check(True, "Scott's page falls back to waiting in his room")
        gm.reload()
        gm.wait_for_selector("#c-handed:not([hidden])")
        gm.wait_for_timeout(3000)
        check(gm.evaluate("() => Object.keys(PL.conn).length === 0"), "the handed-over console, reloaded, invites no one")

        # the next GM loads the file: everyone invited through the same rooms
        ann = page()
        ann.goto(BASE + "campaign.html")
        ann.wait_for_selector("#pl-room", state="attached", timeout=15000)
        ann.click("#pl-room-box summary"); ann.fill("#pl-room", ROOMS); ann.click("#pl-room-set")
        ann.set_input_files("#c-load", str(path))
        ann.wait_for_function("() => REC.players.length === 3 && REC.players.every(pl => PL.conn[pl.id]?.room)", timeout=20000)
        check(ann.evaluate(ROOMS_OF) == codes, f"her console invites every player through the same rooms ({codes})")
        scott.wait_for_function(CONNECTED, timeout=45000)
        ann.wait_for_function("() => PL.conn[REC.players.find(p => p.name === 'Scott').id].state === 'open'", timeout=20000)
        check(scott_at(ann) == "open", "Scott is back, on her console, with no new link")
        ann.click("#pl-all summary")
        lines = ann.input_value("#pl-all-links").split("\n")
        check(len(lines) == 2 and lines[0].startswith("Kate: ") and f"#room={codes[1]}" in lines[0] and lines[1].startswith("Tom: "),
              f"the two still waiting are listed together, a line each ({lines})")
        ann.fill("#c-note", "Ann has the game."); ann.uncheck("#c-note-gm"); ann.click("#c-add-note")
        scott.wait_for_function("() => document.querySelector('#p-news').textContent.includes('Ann has the game.')", timeout=10000)
        check(True, "and his page follows her campaign")
        check(not errors, f"no page errors {errors[:3]}")
        br.close()
finally:
    stop()

print(f"{'all checks passed' if not failures else str(len(failures)) + ' failed'}")
raise SystemExit(1 if failures else 0)
