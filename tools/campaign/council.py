"""Camp roles and the evening council on the campaign console, in a headless browser, on the coached
Towton campaign.

    python3 tools/campaign/council.py [seed]

The GM holds the first council and fills the roles; roles change only while a council sits. The man a
role names makes its rolls, even with a better man in the force, and the GM can set another for one
roll. Each day stops for the evening council, and a council can be skipped. A role's man dead says a
council is needed and the best man rolls. A player sees his role, asks for a council, and the GM
declines one and hears another. Needs Python's playwright with Chromium and a built site. Exits
non-zero on any failure.
"""
import sys
import traceback
from playwright.sync_api import sync_playwright
from harness import DICE, check, failures, serve

BASE, server = serve()
SEED = int(sys.argv[1]) if len(sys.argv) > 1 else 1
SHOT = len(sys.argv) > 2


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
    pg.wait_for_function("() => document.querySelector('#c-coach').textContent.includes('Done: on to march')", timeout=45000)
    pg.click("#c-next")
    pg.wait_for_selector("#c-council button[data-council='open']", timeout=15000)
    fid = pg.evaluate("() => newDay().councilForces()[0]")
    check(pg.evaluate("() => newDay().councilView(newDay().councilForces()[0]).started") is False, "a campaign starts with no roles")
    check(pg.locator("#c-council select").count() == 0, "no role can be set until a council sits")
    men = pg.evaluate("""f => newDay().councilView(f).men.map(m => ({ uid: m.uid, name: m.name, fc: m.skills.fieldcraft || 0 }))""", fid)
    men.sort(key=lambda m: m["fc"])
    worst, best = men[0], men[-1]
    check(len(men) == 6 and best["fc"] > worst["fc"], f"six men with different Fieldcraft ({[m['fc'] for m in men]})")

    def roller(roll, skill):
        return pg.evaluate("""([f, roll, skill]) => { const d = newDay(); d.restore(); return d.rollerFor([d.forcesHere().find(x => x.id === f)], roll, skill) }""", [fid, roll, skill])

    check(roller("way", "fieldcraft")[0] == best["fc"], "with no roles the best man finds the way")
    pg.click("#c-council button[data-council='open']")
    pg.wait_for_selector("select[data-c-role='scout']")
    pg.select_option("select[data-c-role='scout']", worst["uid"])
    pg.wait_for_function("() => document.querySelector(\"select[data-c-role='scout']\").value !== ''")
    for role, m in (("leader", men[1]), ("quartermaster", men[2]), ("leech", men[3])):
        pg.select_option(f"select[data-c-role='{role}']", m["uid"])
        pg.wait_for_timeout(150)
    check(roller("way", "fieldcraft")[1] == worst["name"], "the scout finds the way though a better man is with the force")
    check(roller("way", "fieldcraft")[0] == worst["fc"], "and rolls his own Fieldcraft")
    check(roller("watch", "watch")[1] == worst["name"], "the scout keeps the watch")
    check(roller("hunt", "fieldcraft")[1] == men[2]["name"], "the quartermaster hunts")
    pg.locator("#c-council details summary").click()
    pg.select_option("select[data-c-roll='hunt']", men[4]["uid"])
    pg.wait_for_timeout(200)
    check(roller("hunt", "fieldcraft")[1] == men[4]["name"], "the GM can set another man for one roll")
    pg.locator("#c-council details summary").click() if pg.locator("select[data-c-roll='hunt']").is_visible() else None
    pg.click("#c-council button[data-council='end']")
    pg.wait_for_selector("#c-council button[data-council='open']")
    check(pg.locator("#c-council select").count() == 0, "the council over, the roles are fixed again")
    check("council, day" in pg.inner_text("#c-log"), "the council goes in the log")
    pg.wait_for_selector("#c-rest", timeout=6000)
    day = pg.evaluate("() => newDay().marchSummary().day")
    pg.click("#c-rest")
    pg.wait_for_selector("#c-council button[data-council='skip']", timeout=8000)
    s = pg.evaluate("() => newDay().marchSummary()")
    check(s["night"] and s["day"] == day, "resting stops at evening for the council, before the night passes")
    check("Evening council" in pg.inner_text("#c-council"), "the evening council is prompted")
    pg.screenshot(path="tools/campaign/.cache/council.png") if SHOT else None
    pg.click("#c-council button[data-council='skip']")
    pg.wait_for_function("() => !document.querySelector(\"#c-council button[data-council='skip']\")", timeout=6000)
    check(True, "it can be skipped")
    check("Pass the night" in pg.inner_text("#c-run"), "and the clock waits on the GM")
    pg.click("#c-run")
    pg.wait_for_function(f"() => newDay().marchSummary().day === {day + 1}", timeout=6000)
    check(True, "the next press passes the night")
    pg.locator("button[data-orders]").first.click()
    pg.wait_for_selector("tr.orders select[data-pick='to']", timeout=6000)
    towton = pg.locator("select[data-pick='to'] option", has_text="Towton").first.get_attribute("value")
    pg.select_option("select[data-pick='to']", towton)
    pg.click("button[data-order='to']")
    pg.wait_for_timeout(300)
    for _ in range(12):
        s = pg.evaluate("() => newDay().marchSummary()")
        if s["night"] or pg.locator("#c-march .fights li").count():
            break
        pg.click("#c-run")
        pg.wait_for_timeout(500)
    s = pg.evaluate("() => newDay().marchSummary()")
    check(s["day"] == day + 1, f"the march does not run past the evening (day {day + 1}, now {s['day']})")
    pg.evaluate("""u => { const a = JSON.parse(localStorage.getItem('gravewounds-named')); a[u].dead = true; localStorage.setItem('gravewounds-named', JSON.stringify(a)); render() }""", worst["uid"])
    pg.wait_for_timeout(300)
    check("A council is needed" in pg.inner_text("#c-council"), "a role's man dead says a council is needed")
    alive = sorted((m for m in men if m is not worst), key=lambda m: m["fc"])[-1]
    check(roller("way", "fieldcraft")[1] == alive["name"], "and the best man rolls until it is filled")
    pl = men[1]["uid"]
    pg.evaluate("u => { players().push({ id: 'p1', name: 'Ann', men: [u] }); saveRecord() }", pl)
    screen = pg.evaluate("() => playerScreen(players()[0]).force")
    check("Leader:" in screen and "(you)" in screen, "the player sees his role")
    check("Ask for a council" in screen, "and can ask for a council")
    pg.evaluate("f => playerCommand(players()[0], { t: 'council', force: f, why: 'roles' })", fid)
    pg.wait_for_timeout(200)
    check("Ann asks for a council" in pg.inner_text("#c-council"), "the GM sees the request")
    pg.evaluate("f => playerCommand(players()[0], { t: 'council', force: f + 99, why: 'roles' })", fid)
    pg.evaluate("f => playerCommand(players()[0], { t: 'council', force: f, why: 'nonsense' })", fid)
    check(pg.evaluate("() => asks().length") == 1, "a request for another force, or a second one, is ignored")
    pg.click("#c-council button[data-council='decline']")
    pg.wait_for_timeout(200)
    check("declined" in pg.evaluate("() => playerScreen(players()[0]).force"), "the player hears it was declined")
    pg.evaluate("f => playerCommand(players()[0], { t: 'council', force: f, why: 'rolls' })", fid)
    pg.wait_for_timeout(200)
    pg.locator("#c-council button[data-council='open']").first.click()
    pg.wait_for_selector("select[data-c-role='scout']")
    check(pg.evaluate("() => asks().filter(a => a.state === 'open').length") == 0, "holding the council answers the request")
    check("sitting" in pg.evaluate("() => playerScreen(players()[0]).force"), "and the player sees it sitting")
    pg.goto(BASE + "council-card.html")
    check("Quartermaster" in pg.inner_text("body"), "the printed council card is there")
    check(not errors, f"no page errors {errors[:2]}")
    br.close()


try:
    with sync_playwright() as p:
        run(p)
except Exception:
    traceback.print_exc()
    failures.append("the run stopped")
finally:
    server.shutdown()
sys.exit(1 if failures else 0)
