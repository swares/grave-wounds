"""A team from the team builder through a fight on the roller, in a headless browser, served as the site is.

    python3 tools/campaign/team.py

The team builder's retinue goes to the roller; one control puts all its named men with a force on the
travel map; a fight sent from the travel map brings the named men and the team's followers by name; a man
taken prisoner on the roller goes to the team builder's Prisoners. (From the first solo play test, 27
October 2026.) Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
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
    def log_message(self, format, *args):
        return None


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_port}/dist/"
TRAVEL = {"mapId": "towton-1461", "forces": {"towton-1461": [
    {"id": 7, "name": "Sir Roger's retinue", "side": "York", "men": 20, "type": "foot", "pos": [19, 38]},
    {"id": 6, "name": "Clifford's horse", "side": "Lancaster", "men": 500, "type": "mounted", "pos": [23, 25]}]},
    "clock": {"towton-1461": {"day": 1, "used": 0}}}

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1400, "height": 1100})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE + "team.html"); pg.evaluate("() => localStorage.clear()"); pg.reload()
    pg.select_option("#sel-region", "england"); pg.select_option("#sel-template", "retinue")
    pg.click("#btn-roll")
    pg.evaluate(f"() => localStorage.setItem('gravewounds-travel', {json.dumps(json.dumps(TRAVEL))})")
    pg.click("#btn-send")
    pg.wait_for_function("() => location.pathname.endsWith('roller.html')", timeout=15000)
    pg.get_by_role("button", name="Add the team").first.click()
    pg.wait_for_function("() => S.chars.some(c => c.uid)", timeout=10000)
    named = pg.evaluate("() => S.chars.filter(c => c.uid).length")
    followers = pg.evaluate("() => S.chars.filter(c => c.follower).map(c => c.name)")
    check(named >= 4 and len(followers) >= 1, f"the team's {named} named men and {len(followers)} followers are on the roller")

    sel = pg.locator("select[data-teamwith]")
    check(sel.count() == 1 and "goes with" in pg.inner_text("#team-with").lower(), "one control puts the whole team with a force")
    sel.select_option("towton-1461:7")
    with_force = pg.evaluate("() => Object.values(JSON.parse(localStorage.getItem('gravewounds-named'))).filter(n => n.map === 'towton-1461' && n.force === 7).length")
    check(with_force == named, f"all {named} named men go with the retinue at once")

    handoff = {"from": "travel", "mapId": "towton-1461", "force": {"id": 7, "name": "Sir Roger's retinue", "side": "York", "men": 20, "type": "foot"},
               "place": "Sherburn-in-Elmet", "day": "27 Mar", "time": "10:00", "ground": "open",
               "foes": [{"id": 6, "name": "Clifford's horse", "side": "Lancaster", "men": 500, "type": "mounted"}]}
    pg.evaluate(f"() => localStorage.setItem('gravewounds-handoff', {json.dumps(json.dumps(handoff))})")
    pg.reload()
    pg.wait_for_selector("button[data-map=handoff]", timeout=10000)
    pg.click("button[data-map=handoff]")
    pg.wait_for_function("() => !S.handoff", timeout=8000)
    york = pg.evaluate("() => S.chars.filter(c => sideOf(c) === 'York').map(c => c.name)")
    check(len(york) == named + len(followers) and all(f in york for f in followers),
          f"the fight from the travel map brings the named men and the team's followers by name ({len(york)} of the retinue's 20)")
    check(pg.evaluate("() => S.chars.filter(c => sideOf(c) === 'Lancaster').length") == 8, "the enemy force brings its 8 as before")

    man = pg.evaluate("() => S.chars.find(c => c.uid && c.sheet).name")
    pid = pg.evaluate("() => S.chars.find(c => c.uid && c.sheet).sheet.pid")
    pg.evaluate("() => { S.wonBy = 'Lancaster'; S.afterOpen = true; renderChars() }")
    pg.locator("button[data-takenman]").first.click()
    lost = pg.evaluate(f"() => (JSON.parse(localStorage.getItem('gravewounds-purses'))[{json.dumps(pid)}] || {{}}).lost")
    check(lost == {"why": "taken prisoner"}, f"Taken prisoner after the fight marks {man} taken, for the team builder")
    check("taken prisoner" in pg.inner_text("#after-fight") and "taken" in pg.inner_text("#chars").lower(), "the roller shows him taken")
    pg.goto(BASE + "team.html")
    pg.wait_for_timeout(1500)
    check(man in pg.inner_text("#prisoners") and "is taken" in pg.inner_text("#prisoners"),
          "the team builder lists him under Prisoners, his capture to roll")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()
server.shutdown()
print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
sys.exit(1 if failures else 0)
