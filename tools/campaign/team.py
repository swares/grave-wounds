"""A team from the team builder through a fight on the roller, in a headless browser, served as the site is.

    python3 tools/campaign/team.py

The team builder's retinue goes to the roller; one control puts all its named men with a force on the
travel map; a fight sent from the travel map brings the named men and the team's followers by name; a man
taken prisoner on the roller goes to the team builder's Prisoners; the page's example pair makes way for the team, which takes its force's side; the
setup says the travel map's odds the cap of 8 hides. (From the first solo play test, 27 October 2026.) Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import json, sys
from playwright.sync_api import sync_playwright
from harness import check, failures, serve

BASE, server = serve()
TRAVEL = {"mapId": "towton-1461", "forces": {"towton-1461": [
    {"id": 7, "name": "Sir Roger's retinue", "side": "York", "men": 20, "type": "foot", "pos": [19, 38], "log": [], "day": 1, "used": 0},
    {"id": 6, "name": "Clifford's horse", "side": "Lancaster", "men": 500, "type": "mounted", "pos": [23, 25], "log": [], "day": 1, "used": 0}]},
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
    pg.wait_for_function("() => typeof S === 'object' && Array.isArray(S.chars)", timeout=10000)
    had = pg.evaluate("() => S.chars.filter(c => c.example).length")
    pg.get_by_role("button", name="Add the team").first.click()
    pg.wait_for_function("() => S.chars.some(c => c.uid)", timeout=10000)
    named = pg.evaluate("() => S.chars.filter(c => c.uid).length")
    followers = pg.evaluate("() => S.chars.filter(c => c.follower).map(c => c.name)")
    check(named >= 4 and len(followers) >= 1, f"the team's {named} named men and {len(followers)} followers are on the roller")
    check(had == 2 and not pg.evaluate("() => S.chars.some(c => c.example)"), f"the page's example pair ({had}) makes way for the team")

    sel = pg.locator("select[data-teamwith]")
    check(sel.count() == 1 and "goes with" in pg.inner_text("#team-with").lower(), "one control puts the whole team with a force")
    sel.select_option("towton-1461:7")
    with_force = pg.evaluate("() => Object.values(JSON.parse(localStorage.getItem('gravewounds-named'))).filter(n => n.map === 'towton-1461' && n.force === 7).length")
    check(with_force == named, f"all {named} named men go with the retinue at once")
    sides = pg.evaluate("() => [...new Set(S.chars.filter(c => c.team).map(c => c.side))]")
    check(sides == ["York"], f"the team takes its force's side ({sides})")

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
    odds = pg.evaluate("() => S.pending.find(p => p.startsWith('The odds on the travel map')) || ''")
    check("20 men against 500" in odds and "1 to 25" in odds and "Ask the dice" in odds, f"the setup says what the cap of 8 hides ({odds[:90]})")

    man = pg.evaluate("() => S.chars.find(c => c.uid && c.sheet).name")
    pid = pg.evaluate("() => S.chars.find(c => c.uid && c.sheet).sheet.pid")
    pg.evaluate("() => { S.wonBy = 'Lancaster'; S.afterOpen = true; renderChars() }")
    pg.locator("button[data-takenman]").first.click()
    lost = pg.evaluate(f"() => (JSON.parse(localStorage.getItem('gravewounds-purses'))[{json.dumps(pid)}] || {{}}).lost")
    check(lost == {"why": "taken prisoner"}, f"Taken prisoner after the fight marks {man} taken, for the team builder")
    check("taken prisoner" in pg.inner_text("#after-fight") and "taken" in pg.inner_text("#chars").lower(), "the roller shows him taken")
    lost_york = pg.evaluate("() => S.chars.filter(c => sideOf(c) === 'York' && (c.taken || isDown(c))).length")
    pg.click("#btn-to-travel")
    r = json.loads(pg.evaluate("() => localStorage.getItem('gravewounds-field-result')") or "null")
    check(r and r["kind"] == "skirmish" and r["beaten"] == [7] and r["forces"]["7"]["taken"] >= 1,
          f"Send the result to the travel map writes each force's losses and the beaten force ({r and r['forces']['7']})")
    pg.goto(BASE + "travel.html")
    pg.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
    ret = pg.evaluate("() => { const f = forcesHere().find(o => o.id === 7); return { men: f.men, pos: f.pos, log: f.log.slice(0, 3) } }")
    check(ret["men"] == 20 - r["forces"]["7"]["lost"] and any(l.startswith("Skirmish at Sherburn-in-Elmet") for l in ret["log"]),
          f"the travel map takes the skirmish in: the retinue has {ret['men']} men ({ret['log'][:2]})")
    check(ret["pos"] != [19, 38] and any("fell back" in l for l in ret["log"]), f"the beaten retinue fell back ({ret['pos']})")
    check(pg.evaluate("() => localStorage.getItem('gravewounds-field-result')") is None, "and the result is used once")
    pg.goto(BASE + "team.html")
    pg.wait_for_timeout(1500)
    check(man in pg.inner_text("#prisoners") and "is taken" in pg.inner_text("#prisoners"),
          "the team builder lists him under Prisoners, his capture to roll")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()
server.shutdown()
print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
sys.exit(1 if failures else 0)
