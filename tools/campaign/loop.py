"""The campaign page over the real pages, in a headless browser, served as the site is (a local web server).

    python3 tools/campaign/loop.py

It follows a campaign round the loop: the team made in the team builder (in the frame), the march on the
travel map run from the console until the forces meet, a fight sent from it noticed and the console moved to it, the fight won on the roller, the
aftermath; then the whole game saved to a file, cleared, and loaded back. The pages' writes are made from
inside the frame, as the pages make them. Needs Python's playwright with Chromium and a built site.
Exits non-zero on any failure.
"""
import functools, http.server, json, sys, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):   # the server's request lines would drown the checks
        return None


def frame_of(pg):
    """The page in the console's frame, for locating its elements."""
    return pg.frame_locator("#c-frame")


def page_in_frame(pg):
    """The page in the console's frame, for running code in it as the page does."""
    return pg.frames[1]


PHASE = "() => REC.phase"
NO_TEAM = "not made yet"


def phase_of(pg) -> str:
    return str(pg.evaluate(PHASE))


def status_of(pg) -> str:
    return pg.inner_text("#c-status")


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_port}/dist/"
J = json.dumps

with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 1500, "height": 1200}, accept_downloads=True)
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    ctx.on("weberror", lambda e: errors.append(str(e.error)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE + "campaign.html"); pg.evaluate("() => localStorage.clear()"); pg.reload()
    check(phase_of(pg) == "muster" and NO_TEAM in status_of(pg), "a new campaign starts at the muster, with no team")
    pg.wait_for_function("() => document.querySelector('#c-showing').textContent.includes('Team builder')", timeout=15000)
    check(True, "the team builder is in the frame")
    # the team, made in the team builder in the frame
    frame_of(pg).locator("#btn-roll").click()
    pg.wait_for_function("() => /\\d+ men/.test(document.querySelector('#c-status').textContent)", timeout=8000)
    check("Medieval" in pg.inner_text("#c-guide"), "the console sees the team the frame's page wrote, and its era")
    pg.click("#c-next")
    pg.wait_for_function("() => document.querySelector('#c-showing').textContent.includes('Travel map')", timeout=15000)
    check(phase_of(pg) == "march", "Done moves to the march, with the travel map in the frame")
    # Run the march: the travel map's forces given routes there, the clock moved on from here
    page_in_frame(pg).wait_for_function("() => typeof addWaypoint === 'function' && location.pathname.endsWith('travel.html')", timeout=15000)
    page_in_frame(pg).evaluate("""() => { S.mapId = 'towton-1461'; S.clock = {}; const fs = forcesHere();
      for (const f of fs){ const foe = fs.find(o => o.side !== f.side); if (foe) addWaypoint(f, foe.pos) } save() }""")
    pg.wait_for_function("() => !!document.querySelector('#c-run')", timeout=6000)
    rows = pg.locator("#c-march tbody tr").count()
    check(rows >= 2 and "Day 1" in pg.inner_text("#c-march"), f"the march panel shows the map's clock and its {rows} forces")
    met, presses = False, 0
    while not met and presses < 20:
        pg.click("#c-run"); presses += 1
        pg.wait_for_function("() => document.querySelector('#c-march-said').textContent.length > 0", timeout=8000)
        met = not pg.locator("#c-notice").is_hidden() and "have met" in pg.inner_text("#c-notice")
    said = pg.inner_text("#c-march-said")
    check(met, f"Run the march moves the clock until forces meet, and says so ({presses} presses: {said[:90]})")
    texts = [e["data"]["text"] for e in pg.evaluate("() => REC.log")]
    check(sum(1 for t in texts if " meet " in t or "Night passes" in t or "marching is done" in t or ":" in t) >= presses, "each move of the clock goes into the campaign's log")
    saved = json.loads(pg.evaluate("() => localStorage.getItem('gravewounds-travel')"))
    pg.wait_for_timeout(500)
    page_in_frame(pg).wait_for_function("() => typeof clockNow === 'function'", timeout=15000)
    frame_clock = page_in_frame(pg).evaluate("() => clockNow()")
    check(frame_clock == saved["clock"]["towton-1461"], f"the travel map in the frame shows the day the console moved to ({frame_clock})")
    check("Travel map" in pg.inner_text("#c-showing"), "a meeting puts the travel map in the frame, to set up the fight")
    # a long march with the enemy gone: the nights pass as the console moves the clock on
    page_in_frame(pg).evaluate("""() => { const all = forcesHere(), f = all[0], m = curMap(), foes = all.filter(o => o.side !== f.side);
      S.forces[S.mapId] = all.filter(o => o.side === f.side);   // the enemy gone from the map: nothing to meet
      for (const o of forcesHere()){ o.waypoints = []; o.path = null; o.order = "halt" }
      let best = null, far = -1;
      for (let r = 0; r < m.rows.length; r += 2) for (let c = 0; c < m.rows[0].length; c += 2){
        const d = Math.min(...foes.map(o => hexDistance(o.pos, [c, r]))), go = hexDistance(f.pos, [c, r]);
        if (d > far && go > 25 && go < 60 && passable(m, [c, r], colType(f), groundOf(f.day)) && plan(m, f.pos, [[c, r]], colType(f), groundOf(f.day))){ far = d; best = [c, r] } }
      addWaypoint(f, best); save() }""")
    pg.wait_for_timeout(3500)                                # the console looks again
    presses = 0
    while presses < 25 and pg.locator("#c-run").is_enabled() and "arrives" not in pg.inner_text("#c-march-said"):
        pg.click("#c-run"); presses += 1
    said = pg.inner_text("#c-march-said")
    day = json.loads(pg.evaluate("() => localStorage.getItem('gravewounds-travel')"))["clock"]["towton-1461"]["day"]
    named = pg.evaluate("() => JSON.parse(localStorage.getItem('gravewounds-travel')).forces['towton-1461'][0].log.slice(0, 40).join(' | ')")
    check("arrives" in said and day >= 3 and "Night of" in named, f"marching on, nights pass until it arrives: day {day} after {presses} presses ({said[:70]})")
    check("Day " + str(day) in pg.inner_text("#c-march"), "the march panel follows the clock")
    # the travel map's state, then a fight sent from it, as Fight here writes it
    page_in_frame(pg).evaluate(f"""() => localStorage.setItem('gravewounds-travel', {J(J({"mapId": "towton-1461", "forces": {"towton-1461": [{"side": "York"}, {"side": "Lancaster"}]}, "clock": {"towton-1461": {"day": 3, "used": 4}}, "fought": []}))})""")
    page_in_frame(pg).evaluate(f"""() => localStorage.setItem('gravewounds-handoff', {J(J({"from": "travel", "force": {"name": "Will's lances", "side": "York"}, "place": "Ferrybridge", "foes": [{"name": "Clifford's flankers"}]}))})""")
    pg.wait_for_function("() => REC.phase === 'fight'", timeout=6000)
    notice = pg.inner_text("#c-notice")
    check("Ferrybridge" in notice and "Fight" in notice, f"a fight sent from the travel map moves the console to the fight ({notice})")
    check("day 3" in status_of(pg).lower() and "waiting on the Wound roller" in status_of(pg), "the status shows the map's day and the fight waiting on the roller")
    check(any("Ferrybridge" in e["data"]["text"] for e in pg.evaluate("() => REC.log")), "the log records the encounter")
    # the roller, as Fight here sends it there; a fight won
    pg.click('#c-actions button.primary')
    pg.wait_for_function("() => document.querySelector('#c-showing').textContent.includes('Wound roller')", timeout=15000)
    pg.wait_for_function("() => { try { return typeof document.querySelector('#c-frame').contentWindow.renderChars === 'function' } catch { return false } }", timeout=15000)
    page_in_frame(pg).evaluate("() => { S.wonBy = 'York'; renderChars() }")   # the GM marks the winner in After the fight
    pg.wait_for_function("() => REC.phase === 'aftermath'", timeout=6000)
    check("York won" in pg.inner_text("#c-notice"), "a fight won on the roller moves the console to the aftermath")
    # notes
    pg.fill("#c-note", "Hal took an arrow at the ford."); pg.uncheck("#c-note-gm"); pg.click("#c-add-note")
    pg.fill("#c-note", "Clifford's men will be back with more."); pg.check("#c-note-gm"); pg.click("#c-add-note")
    log = pg.evaluate("() => REC.log.map(e => [e.vis, e.data.text])")
    check(["public", "Hal took an arrow at the ford."] in log and [[], "Clifford's men will be back with more."] in log, "notes go in the log, public or for the GM")
    # the whole game to a file; the narrator's key never in it
    pg.evaluate("() => localStorage.setItem('gravewounds-narrator', JSON.stringify({ key: 'sk-secret' }))")
    with pg.expect_download() as dl:
        pg.click("#c-save")
    saved = json.loads(Path(dl.value.path()).read_text())
    check(saved["format"] == "grave-wounds-save" and "gravewounds-campaign" in saved["keys"] and "gravewounds-team-builder" in saved["keys"], f"the save holds every page's state and the campaign's log ({len(saved['keys'])} entries)")
    check("gravewounds-narrator" not in saved["keys"] and "sk-secret" not in json.dumps(saved), "the narrator's service key is never in a save")
    # cleared, then loaded back
    save_path = Path(dl.value.path())
    pg.evaluate("() => { for (const k of Object.keys(localStorage)) if (k !== 'gravewounds-narrator') localStorage.removeItem(k) }"); pg.reload()
    check(pg.evaluate(PHASE) == "muster" and NO_TEAM in status_of(pg), "cleared, the console is back at a new campaign")
    pg.set_input_files("#c-load", str(save_path))
    pg.wait_for_function("() => REC.phase === 'aftermath'", timeout=6000)
    check(" men" in status_of(pg) and NO_TEAM not in status_of(pg) and "Loaded the saved game" in pg.inner_text("#c-log"), "loading the file brings back the team, the phase and the log")
    check(pg.evaluate("() => localStorage.getItem('gravewounds-narrator')") is not None, "loading a save leaves this browser's narrator settings alone: they are not part of a game")
    bad = ROOT / "tools" / "campaign" / ".cache"; bad.mkdir(exist_ok=True)
    (bad / "not-a-save.json").write_text('{"hello": 1}')
    pg.set_input_files("#c-load", str(bad / "not-a-save.json"))
    pg.wait_for_function("() => document.querySelector('#c-saved').textContent.includes('Could not load')", timeout=4000)
    check(pg.evaluate(PHASE) == "aftermath", "a file that is not a save is refused and changes nothing")
    pg.screenshot(path=str(bad / "campaign.png"), full_page=False)
    pg.click("#c-new")
    pg.wait_for_timeout(3500)                                  # the console looks again: the old fight must not be news to the new campaign
    check(pg.evaluate("() => [REC.phase, REC.log.length]") == ["muster", 1], "a new campaign starts a fresh log at the muster, and what the pages already hold is not news to it")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()
server.shutdown()
print("all checks passed" if not failures else f"{len(failures)} failed")
sys.exit(1 if failures else 0)
