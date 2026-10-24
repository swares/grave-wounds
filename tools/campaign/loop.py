"""The campaign page over the real pages, in a headless browser, served as the site is (a local web server).

    python3 tools/campaign/loop.py [seed]

The pages' dice (the browser's crypto) are seeded, so a run can be repeated: seed 1 unless given
(CI runs seed 1; other seeds play other games). It follows a campaign round the loop: the team made in the team builder (in the frame), the march on the
travel map, a force's route given from the console, the clock run from it until the forces meet, the fight set up from it
and run on the roller from it, a battle sent to the field map and run, ended and sent back from it, a fight sent from it noticed and the console moved to it, the fight won on the roller, the
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


SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 1
# The test's dice: Park-Miller from the seed, in place of the browser's crypto, never for anything secret
# (the WebRTC keys of the online game are not made here: this test plays no online game).
DICE = """(() => { let s = Math.max(1, %d * 7919 %% 2147483647);
  crypto.getRandomValues = a => { for (let i = 0; i < a.length; i++){ s = (s * 16807) %% 2147483647; a[i] = s } return a } })();"""
PHASE = "() => REC.phase"
NO_TEAM = "not made yet"
RUN, SAID, NOTICE = "#c-run", "#c-march-said", "#c-notice"
FIGHTS = "#c-march .fights li"
B_NEXT, B_END, B_FIGHT = "#c-fight button[data-battlecmd='next']", "#c-fight button[data-battlecmd='end']", "button[data-fight]"
TAKE, LOG, TRAVEL = "#c-take-battle", "() => REC.log", "() => localStorage.getItem('gravewounds-travel')"


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
    ctx.add_init_script(DICE % SEED)                         # every page and frame: the same dice from the seed
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    ctx.on("weberror", lambda e: errors.append(str(e.error)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE + "campaign.html"); pg.evaluate("() => localStorage.clear()"); pg.reload()
    check(phase_of(pg) == "muster" and NO_TEAM in status_of(pg), "a new campaign starts at the muster, with no team")
    check("Players online" in pg.inner_text("#c-players") and pg.is_visible("#pl-add"), "Players online is there from the start, before any named men")
    check(pg.input_value("#c-map") == "" and "Choose a map" in pg.inner_text("#c-map"), "a new campaign has no map chosen yet: Map says so")
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
    pg.wait_for_selector(RUN, timeout=6000)
    # orders from the console: the first force's route set to a place, then back towards the enemy
    pg.locator("button[data-orders]").first.click()
    pg.wait_for_selector("tr.orders select[data-pick='to']", timeout=6000)
    pg.click("button[data-order='to']")                              # the place the row shows, not chosen first
    pg.wait_for_function("() => document.querySelector('#c-march-said').textContent.includes('will march to')", timeout=6000)
    first = json.loads(pg.evaluate(TRAVEL))["forces"]["towton-1461"][0]
    check(len(first["waypoints"]) == 1 and first["order"] == "march", f"Orders sets a force's route from the console ({pg.inner_text(SAID)[:80]})")
    foe = pg.locator("select[data-pick='to'] optgroup[label='The enemy'] option").first.get_attribute("value")
    pg.select_option("select[data-pick='to']", foe)
    pg.click("button[data-order='to']")
    pg.wait_for_function(f"() => JSON.parse(localStorage.getItem('gravewounds-travel')).forces['towton-1461'][0].waypoints.join() === {J(foe)}", timeout=6000)
    check(any("will march to" in e["data"]["text"] for e in pg.evaluate(LOG)), "orders go into the campaign's log, and a new route replaces the old")
    # a travel map open in another tab follows the console, and does not save its old day over it
    tab = ctx.new_page()
    tab.on("pageerror", lambda e: errors.append(str(e)))
    tab.goto(BASE + "travel.html")
    tab.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
    pg.click("button[data-order='halt']")
    pg.wait_for_function("() => JSON.parse(localStorage.getItem('gravewounds-travel')).forces['towton-1461'][0].order === 'halt'", timeout=6000)
    tab.wait_for_function("() => forcesHere()[0].order === 'halt'", timeout=6000)
    tab.evaluate("() => render()")                                  # the tab saves as it draws: the console's day, not its own old one
    check(json.loads(pg.evaluate(TRAVEL))["forces"]["towton-1461"][0]["order"] == "halt" and "moved on elsewhere" in tab.inner_text("#msg"),
          "a travel map open in another tab follows the console's orders, and saves them, not its old day")
    tab.close()
    pg.click("button[data-order='march']")
    pg.wait_for_function("() => JSON.parse(localStorage.getItem('gravewounds-travel')).forces['towton-1461'][0].order === 'march'", timeout=6000)
    pg.locator("button[data-orders]").first.click()                 # closed again
    # the campaign's map chosen from the console: another map, then back, each keeping its own state
    pg.wait_for_function("() => document.querySelector('#c-map').value === 'towton-1461'", timeout=8000)
    towton = json.loads(pg.evaluate(TRAVEL))["forces"]["towton-1461"]
    pg.select_option("#c-map", "agincourt-1415")
    pg.wait_for_function("() => JSON.parse(localStorage.getItem('gravewounds-travel')).mapId === 'agincourt-1415'", timeout=8000)
    pg.wait_for_function("() => document.querySelector('#c-status').textContent.includes('Agincourt')", timeout=8000)
    page_in_frame(pg).wait_for_function("() => typeof S === 'object' && S.mapId === 'agincourt-1415'", timeout=15000)
    check(any("marches on the map of" in e["data"]["text"] and "Agincourt" in e["data"]["text"] for e in pg.evaluate(LOG)) and "Agincourt" in pg.inner_text("#c-march"),
          "Map on the console moves the campaign to another map: the status, the march panel and the travel map in the frame follow, and the log says so")
    check(len(json.loads(pg.evaluate(TRAVEL))["forces"].get("agincourt-1415", [])) >= 1, "a map chosen the first time has its own forces")
    pg.select_option("#c-map", "towton-1461")
    pg.wait_for_function("() => JSON.parse(localStorage.getItem('gravewounds-travel')).mapId === 'towton-1461'", timeout=8000)
    check(json.loads(pg.evaluate(TRAVEL))["forces"]["towton-1461"] == towton, "back on the first map, its forces and orders are as they were")
    page_in_frame(pg).wait_for_function("() => typeof S === 'object' && S.mapId === 'towton-1461'", timeout=15000)
    # the GM's travel map as one side sees it: its own forces, and of the enemy only what it sees
    tf = page_in_frame(pg)
    side, unseen, mine_n = tf.evaluate("""() => { const fs = forcesHere(), sd = fs[0].side, seen = new Set(sightings(sd).map(o => o.id));
      return [sd, fs.filter(o => o.side !== sd && !seen.has(o.id)).map(o => o.name), fs.filter(o => o.side === sd).length] }""")
    all_n = tf.evaluate("() => document.querySelectorAll('#map svg .force').length")
    tf.select_option("#sel-view", side)
    shown = tf.evaluate("() => [...document.querySelectorAll('#map svg .force:not(.ghost) title')].map(t => t.textContent)")
    check(len(shown) < all_n and sum(1 for t in shown if any(t.startswith(n + " ·") for n in unseen)) == 0 and len(shown) >= mine_n,
          f"the GM's travel map as {side} sees it: its {mine_n} forces, none of the {len(unseen)} enemy forces it cannot see")
    tf.select_option("#sel-view", "")
    check(tf.evaluate("() => document.querySelectorAll('#map svg .force').length") == all_n, "and back to everything")
    rows = pg.locator("#c-march tbody tr").count()
    check(rows >= 2 and "Day 1" in pg.inner_text("#c-march"), f"the march panel shows the map's clock and its {rows} forces")
    met, presses = False, 0
    while not met and presses < 20:
        pg.click(RUN); presses += 1
        pg.wait_for_function("() => document.querySelector('#c-march-said').textContent.length > 0", timeout=8000)
        met = not pg.locator(NOTICE).is_hidden() and "have met" in pg.inner_text(NOTICE)
    said = pg.inner_text(SAID)
    check(met, f"Run the march moves the clock until forces meet, and says so ({presses} presses: {said[:90]})")
    texts = [e["data"]["text"] for e in pg.evaluate(LOG)]
    check(sum(1 for t in texts if " meet " in t or "Night passes" in t or "marching is done" in t or ":" in t) >= presses, "each move of the clock goes into the campaign's log")
    saved = json.loads(pg.evaluate(TRAVEL))
    pg.wait_for_timeout(500)
    page_in_frame(pg).wait_for_function("() => typeof clockNow === 'function'", timeout=15000)
    frame_clock = page_in_frame(pg).evaluate("() => clockNow()")
    check(frame_clock == saved["clock"]["towton-1461"], f"the travel map in the frame shows the day the console moved to ({frame_clock})")
    check("Travel map" in pg.inner_text("#c-showing"), "a meeting puts the travel map in the frame, to set up the fight")
    met_state = pg.evaluate(TRAVEL)   # kept, to set up the fight after the long march
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
    while presses < 25 and pg.locator(RUN).is_enabled() and "arrives" not in pg.inner_text(SAID):
        pg.click(RUN); presses += 1
    said = pg.inner_text(SAID)
    day = json.loads(pg.evaluate(TRAVEL))["clock"]["towton-1461"]["day"]
    named = pg.evaluate("() => JSON.parse(localStorage.getItem('gravewounds-travel')).forces['towton-1461'][0].log.slice(0, 40).join(' | ')")
    check(day >= 3 and "Night of" in named, f"marching on, nights pass from the console: day {day} after {presses} presses ({said[:70]})")   # it arrives, or (the dice) is too spent to go on
    check("Day " + str(day) in pg.inner_text("#c-march"), "the march panel follows the clock")
    pg.wait_for_timeout(3500)
    ended = [e["data"]["text"] for e in pg.evaluate(LOG) if "ended on the map of" in e["data"]["text"]]
    check(len(ended) >= 1 and "York" in ended[-1], f"the end of the days goes into the log by itself ({(ended or ['none'])[-1][:90]})")
    # back to where the forces met: the fight set up from the console
    pg.evaluate("(s) => localStorage.setItem('gravewounds-travel', s)", met_state)
    page_in_frame(pg).evaluate("() => location.reload()")
    pg.wait_for_selector(FIGHTS, timeout=8000)
    offered = pg.locator(FIGHTS).count()
    first = pg.locator(FIGHTS).first
    check(offered >= 1 and " against " in first.inner_text() and "Surprise:" in first.inner_text(), f"the console offers {offered} fight(s) where the forces met, with the odds of surprise")
    first.locator("select").select_option("roller")
    first.locator(B_FIGHT).first.click()
    pg.wait_for_function("() => REC.phase === 'fight'", timeout=6000)
    handoff = json.loads(pg.evaluate("() => localStorage.getItem('gravewounds-handoff')") or "null")
    check(bool(handoff) and handoff["foes"] and handoff["surprise"]["text"].startswith("Surprise"), f"sending it writes the roller's handoff as Fight here does ({(handoff or {}).get('place')})")
    pg.wait_for_function("() => document.querySelector('#c-showing').textContent.includes('Wound roller')", timeout=15000)
    check(any(e["data"]["text"].startswith("Fight set up:") for e in pg.evaluate(LOG)), "the console moves to the fight, logs it, and opens the roller")
    # the fight run from the console: the roller in the frame does it, and says how it stands
    pg.wait_for_selector("#c-fight button[data-fightcmd='start']", timeout=15000)
    sides_shown = pg.locator("#c-fight tbody tr").count()
    check(sides_shown == 2 and "Round 1" in pg.inner_text("#c-fight"), f"the console shows the roller's fight: the round and its {sides_shown} sides")
    pg.click("#c-fight button[data-fightcmd='start']")
    pg.wait_for_selector("#c-fight button[data-fightcmd='step']", timeout=6000)
    check(page_in_frame(pg).evaluate("() => gmOn()"), "Run the fight from the console turns on the roller's Run the fight")
    ended = None                                                       # a person's turn met on the way: ended from the console, and the script plays on
    for _ in range(12):
        if page_in_frame(pg).evaluate("() => (S.events || []).some(e => e.type === 'turn')") and ended is not None:
            break
        if pg.locator("#c-fight button[data-fightcmd='next']").count():
            before = page_in_frame(pg).evaluate("() => S.turn")
            pg.click("#c-fight button[data-fightcmd='next']")
            pg.wait_for_timeout(600)
            ended = page_in_frame(pg).evaluate("() => S.turn") != before
        else:
            pg.click("#c-fight button[data-fightcmd='step']")
            pg.wait_for_timeout(250)
    lines = pg.locator("#c-fight ol.log li").count()
    check(lines >= 1 and page_in_frame(pg).evaluate("() => (S.events || []).some(e => e.type === 'turn')"), f"Step plays the script on the roller, and the console shows its events ({lines} lines)")
    if ended is not None:
        check(ended, "a player's turn ended from the console moves the roller to the next fighter")
    pg.click("#c-fight button[data-fightcmd='undo']")
    pg.wait_for_timeout(300)
    check(page_in_frame(pg).evaluate("() => (S.events || []).some(e => e.type === 'undo')"), "Undo from the console takes back the script's last step")
    # a battle on the field map, run from the console: back to the march, the same meeting sent to the field map
    pg.click('#c-phases button[data-phase="march"]')
    pg.wait_for_selector(FIGHTS, timeout=10000)
    first = pg.locator(FIGHTS).first
    fid = int(first.locator(B_FIGHT).first.get_attribute("data-fight"))
    pg.evaluate("(id) => { MAP_CHOICE[id] = 'field:towton-1461' }", fid)   # on the Towton battlefield as drawn up (the GM's choice: units already placed)
    first.locator(B_FIGHT).first.click()
    pg.wait_for_function("() => REC.phase === 'fight' && document.querySelector('#c-showing').textContent.includes('Field map')", timeout=15000)
    pg.wait_for_selector("#c-fight button[data-battlecmd='setup']", timeout=15000)
    pg.click("#c-fight button[data-battlecmd='setup']")
    pg.wait_for_selector("#c-fight select[data-battleai='1']", timeout=10000)
    names = pg.locator("#c-fight tbody tr").all_inner_texts()
    check(len(names) == 2 and "units standing" in names[0], f"the console shows the field map's battle, set up from the travel map's handoff ({names[0][:60]})")
    for k in (0, 1):
        pg.select_option(f"#c-fight select[data-battleai='{k}']", "attack")
        pg.wait_for_timeout(300)
    pg.click(B_NEXT)              # Start the battle
    pg.wait_for_selector(B_END, timeout=10000)
    for _ in range(4):
        pg.click(B_NEXT)
        pg.wait_for_timeout(250)
    ex = page_in_frame(pg).evaluate("() => S.exchange")
    units = page_in_frame(pg).evaluate("() => S.units.length")
    check(ex >= 2 and units >= 2 and pg.locator("#c-fight ol.log li").count() >= 1, f"Start and Next from the console play the battle, the commander moving both sides ({units} units, exchange {ex})")
    for _ in range(40):                                                # on until a unit breaks, or the battle ends by itself
        if page_in_frame(pg).evaluate("() => S.phase === 'over' || S.units.some(u => u.state === 'broken' || u.state === 'fled')"):
            break
        pg.click(B_NEXT)
        pg.wait_for_timeout(200)
    pg.wait_for_timeout(3500)                                          # the console looks again
    routed = page_in_frame(pg).evaluate("() => S.units.filter(u => u.state === 'broken' || u.state === 'fled').map(u => u.name)")
    logged = [e["data"]["text"] for e in pg.evaluate(LOG) if "have broken" in e["data"]["text"] or "have fled" in e["data"]["text"]]
    check(len(routed) >= 1 and len(logged) == len(routed), f"each unit broken or fled goes into the campaign's log by itself ({routed})")
    if pg.locator(B_END).count():
        pg.click(B_END)
    pg.wait_for_selector("#c-fight button[data-battlecmd='send']", timeout=10000)
    pg.click("#c-fight button[data-battlecmd='send']")
    pg.wait_for_function("() => REC.phase === 'aftermath'", timeout=8000)
    check(pg.evaluate("() => !!localStorage.getItem('gravewounds-field-result')") and "over" in pg.inner_text(NOTICE),
          "ended and sent from the console, the battle's result waits for the travel map, and the console moves to the aftermath")
    # the travel map's state, then a fight sent from it, as Fight here writes it
    page_in_frame(pg).evaluate(f"""() => localStorage.setItem('gravewounds-travel', {J(J({"mapId": "towton-1461", "forces": {"towton-1461": [{"side": "York"}, {"side": "Lancaster"}]}, "clock": {"towton-1461": {"day": 3, "used": 4}}, "fought": []}))})""")
    page_in_frame(pg).evaluate(f"""() => localStorage.setItem('gravewounds-handoff', {J(J({"from": "travel", "force": {"name": "Will's lances", "side": "York"}, "place": "Ferrybridge", "foes": [{"name": "Clifford's flankers"}]}))})""")
    pg.wait_for_function("() => REC.phase === 'fight'", timeout=6000)
    notice = pg.inner_text(NOTICE)
    check("Ferrybridge" in notice and "Fight" in notice, f"a fight sent from the travel map moves the console to the fight ({notice})")
    check("day 3" in status_of(pg).lower() and "waiting on the Wound roller" in status_of(pg), "the status shows the map's day and the fight waiting on the roller")
    check(any("Ferrybridge" in e["data"]["text"] for e in pg.evaluate(LOG)), "the log records the encounter")
    # the roller, as Fight here sends it there; a fight won
    pg.click('#c-actions button.primary')
    pg.wait_for_function("() => document.querySelector('#c-showing').textContent.includes('Wound roller')", timeout=15000)
    pg.wait_for_function("() => { try { return typeof document.querySelector('#c-frame').contentWindow.renderChars === 'function' } catch { return false } }", timeout=15000)
    pg.wait_for_function("() => !!FIGHT && FIGHT.two", timeout=8000)
    winner = pg.evaluate("() => FIGHT.sides[0].side")
    pg.evaluate("(side) => tellRoller('won', { side })", winner)   # the GM marks the winner from the console, as After the fight does
    pg.wait_for_function("() => REC.phase === 'aftermath'", timeout=6000)
    check(f"{winner} won" in pg.inner_text(NOTICE) and page_in_frame(pg).evaluate("() => S.wonBy") == winner, f"the winner marked from the console moves it to the aftermath ({winner})")
    pg.evaluate(f"""() => localStorage.setItem('gravewounds-field-result', {J(J({"battle": "towton-1461:3:4:1", "mapId": "towton-1461", "place": "Ferrybridge", "minutes": 60, "forces": {}}))})""")
    pg.wait_for_selector(TAKE, timeout=6000)
    pg.click(TAKE)
    pg.wait_for_function("() => localStorage.getItem('gravewounds-field-result') === null", timeout=6000)
    check(any("battle at Ferrybridge is over" in e["data"]["text"] for e in pg.evaluate(LOG)) and pg.locator(TAKE).count() == 0,
          "the console takes a battle's result into the travel map, once, and logs it")
    # notes
    pg.fill("#c-note", "Hal took an arrow at the ford."); pg.uncheck("#c-note-gm"); pg.click("#c-add-note")
    pg.fill("#c-note", "Clifford's men will be back with more."); pg.check("#c-note-gm"); pg.click("#c-add-note")
    log = pg.evaluate("() => REC.log.map(e => [e.vis, e.data.text])")
    check(["public", "Hal took an arrow at the ford."] in log and [[], "Clifford's men will be back with more."] in log, "notes go in the log, public or for the GM")
    # the end of a season in the team builder: noticed, logged, on to downtime
    pg.evaluate("() => { const x = JSON.parse(localStorage.getItem('gravewounds-xp') || '{}'); x.p9 = { ticks: {}, served: 0, stamp: Date.now() }; localStorage.setItem('gravewounds-xp', JSON.stringify(x)) }")
    pg.wait_for_function("() => REC.phase === 'downtime'", timeout=6000)
    check("season has ended" in pg.inner_text(NOTICE) and any("season has ended" in e["data"]["text"] for e in pg.evaluate(LOG)), "the end of a season moves the console to downtime, and says so")
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
    pg.wait_for_function("() => REC.phase === 'downtime'", timeout=6000)
    check(" men" in status_of(pg) and NO_TEAM not in status_of(pg) and "Loaded the saved game" in pg.inner_text("#c-log"), "loading the file brings back the team, the phase and the log")
    check(pg.evaluate("() => localStorage.getItem('gravewounds-narrator')") is not None, "loading a save leaves this browser's narrator settings alone: they are not part of a game")
    bad = ROOT / "tools" / "campaign" / ".cache"; bad.mkdir(exist_ok=True)
    (bad / "not-a-save.json").write_text('{"hello": 1}')
    pg.set_input_files("#c-load", str(bad / "not-a-save.json"))
    pg.wait_for_function("() => document.querySelector('#c-saved').textContent.includes('Could not load')", timeout=4000)
    check(pg.evaluate(PHASE) == "downtime", "a file that is not a save is refused and changes nothing")
    pg.screenshot(path=str(bad / "campaign.png"), full_page=False)
    # campaigns side by side: this one kept, another started, then back to this one; a snapshot rolled back to
    pg.fill("#c-name", "Towton"); pg.press("#c-name", "Tab")
    pg.click('#c-slots button[data-slot="keep"]')
    pg.wait_for_function("() => SLOTS.some(x => x.id === REC.slot && x.name === 'Towton')", timeout=6000)
    check(True, "Keep it now keeps this campaign in the browser, under its name")
    team_before = status_of(pg)
    other = ctx.new_page()                                     # the team builder open in another tab: it must not write the old team back
    other.on("pageerror", lambda e: errors.append(str(e)))
    other.goto(BASE + "team.html")
    other.wait_for_function("() => typeof render === 'function'", timeout=15000)
    pg.click('#c-slots button[data-slot="another"]')
    pg.wait_for_function("() => REC.phase === 'muster' && SLOTS.length === 2", timeout=8000)
    pg.wait_for_timeout(3500)                                  # the console looks again: nothing from the other campaign is news here
    check(NO_TEAM in status_of(pg) and pg.evaluate("() => REC.log.length") == 1 and pg.evaluate("() => localStorage.getItem('gravewounds-travel')") is None,
          "Start another campaign keeps this one and starts with every page empty")
    other.wait_for_timeout(1500)
    check(pg.evaluate("() => localStorage.getItem('gravewounds-team-builder')") is None or NO_TEAM in status_of(pg),
          "a team builder open in another tab starts again from the empty campaign, and does not write the old team back")
    other.close()
    pg.click('#c-slots button[data-slot="switch"]')
    pg.wait_for_function("() => REC.name === 'Towton'", timeout=8000)
    check(pg.evaluate(PHASE) == "downtime" and status_of(pg) == team_before and "Back to Towton" in pg.inner_text("#c-log"),
          "Switch to it brings that campaign back whole: its team, map, phase and log")
    snaps = pg.evaluate("() => SLOTS.find(x => x.id === REC.slot).snaps.map(x => x.label)")
    check(len(snaps) >= 2, f"the campaign keeps snapshots as it moves on ({snaps[:4]})")
    pg.select_option("#c-snap", index=len(snaps) - 1)            # the oldest kept
    oldest = snaps[-1]
    pg.click('#c-slots button[data-slot="back"]')
    pg.wait_for_function(f"() => REC.log.some(e => e.data.text === 'Rolled back to: ' + {J(oldest)})", timeout=8000)
    check(True, f"Roll back takes every page back to a snapshot ({oldest})")
    pg.click('#c-slots button[data-slot="drop"]')
    pg.wait_for_function("() => SLOTS.length === 1", timeout=6000)
    check(pg.evaluate("() => SLOTS[0].id === REC.slot"), "Delete removes the other campaign, never this one")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()
server.shutdown()
print("all checks passed" if not failures else f"{len(failures)} failed")
sys.exit(1 if failures else 0)
