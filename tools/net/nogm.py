"""Commander against commander on the travel map with no GM: one commander hosts, the other joins online.

    python3 tools/net/nogm.py

On the Towton map the host adds two players, gives each a side to command (York, Lancaster), and ticks
No GM. Edward (York) plays at this console: his seat opens in another tab of the host's browser and
talks to the console over a BroadcastChannel. Somerset (Lancaster) joins from his own browser by his
room's link. Each presses Ready, and the clock runs by itself. With a York and a Lancaster force put
side by side at Towton, Edward's seat offers him the fight and Somerset's does not offer it to him
as an attacker; Edward attacks. The battle opens on Towton's battlefield in the console's frame, is
set up and started by itself, and each commander gets his own side's fight on his page. Ended, its
result goes back to the travel map by itself and the campaign returns to the march. Needs Python's
playwright with Chromium and a built site. Exits non-zero on any failure.
"""
from playwright.sync_api import sync_playwright
from roomharness import CONNECTED, add_player, check, failures, serve

MAP = "towton-1461"
site, BASE, ROOMS, stop = serve()
TRAVEL = "JSON.parse(localStorage.getItem('gravewounds-travel'))"

try:
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--disable-features=WebRtcHideLocalIpsWithMdns"])
        gctx = br.new_context(viewport={"width": 1400, "height": 1100})
        errors = []
        gm = gctx.new_page()
        gm.on("pageerror", lambda e: errors.append("console: " + str(e)))
        gm.goto(BASE + "travel.html"); gm.evaluate("() => localStorage.clear()"); gm.reload()
        gm.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
        gm.evaluate(f"""() => {{ S.mapId = {MAP!r}; S.clock = {{}}; forcesHere(); save();
          const fs = forcesHere(), y = fs.find(f => f.side === 'York'), l = fs.find(f => f.side === 'Lancaster');
          const man = (name, f) => ({{ name, map: {MAP!r}, force: f.id, pid: 'pid-' + name, endurance: 50, str: 50, sex: 'm', fieldcraft: 40, leechcraft: 20, log: [], health: {{ cases: [], immune: {{}}, had: {{}}, dead: 0 }} }});
          localStorage.setItem('gravewounds-named', JSON.stringify({{ u1: man('Hal Ashby', y), u2: man('Wat Tyler', l) }})) }}""")
        gm.goto(BASE + "campaign.html")
        gm.wait_for_function("() => typeof REC === 'object' && REC", timeout=15000)
        gm.evaluate("() => { setPhase('march'); render() }")
        gm.wait_for_selector("[data-pl-new]")
        for name, man in (("Edward", "u1"), ("Somerset", "u2")):
            add_player(gm, ROOMS, name, man)
        ids = gm.evaluate("() => REC.players.map(p => p.id)")
        gm.select_option(f'select[data-pl-side="{ids[0]}"]', "York")
        gm.select_option(f'select[data-pl-side="{ids[1]}"]', "Lancaster")
        gm.check("#c-nogm")
        check(gm.evaluate("() => REC.noGM") is True, "the host ticks No GM")

        # Edward plays at this console: his seat in another tab of the same browser
        gm.check(f'[data-pl-local="{ids[0]}"]')
        check(gm.evaluate("() => REC.players[0].local") is True, "Edward plays at this console")
        with gctx.expect_page() as pinfo:
            gm.click(f'button[data-pl="seat"][data-id="{ids[0]}"]')
        ed = pinfo.value
        ed.on("pageerror", lambda e: errors.append("Edward's seat: " + str(e)))
        ed.wait_for_function("() => document.querySelector('#p-force').textContent.includes('You command York')", timeout=15000)
        check("Your seat at this console" in ed.inner_text("#p-status"), "his seat opens in another tab and hears the console there")
        check(gm.evaluate(f"() => PL.conn[{ids[0]!r}].state") == "open", "the console counts him connected")

        so = br.new_context(viewport={"width": 1100, "height": 900}).new_page()
        so.on("pageerror", lambda e: errors.append("Somerset: " + str(e)))
        so.goto(gm.input_value(f'textarea[data-pl-link="{ids[1]}"]'))
        so.wait_for_function(CONNECTED, timeout=30000)
        so.wait_for_function("() => document.querySelector('#p-force').textContent.includes('You command Lancaster')", timeout=10000)
        check(True, "Somerset joins from his own browser by his room's link")

        # both ready: the clock runs by itself
        marches = "() => REC.log.filter(e => e.data.kind === 'march').length"
        before = gm.evaluate(marches)
        ed.click('#p-force button[data-ready="1"]')
        gm.wait_for_function("() => REC.players[0].ready", timeout=10000)
        gm.wait_for_timeout(500)
        check(gm.evaluate(marches) == before, "one commander ready: the clock waits")
        so.click('#p-force button[data-ready="1"]')
        gm.wait_for_function(f"() => REC.players.every(p => !p.ready) && ({marches[6:]}) > {before}", timeout=15000)
        check(True, "both ready: the clock runs by itself, and the ready marks clear")

        # a York and a Lancaster force side by side at Towton: Edward is offered the fight
        gm.evaluate(f"""() => {{ const T = {TRAVEL}, fs = T.forces[{MAP!r}];
          const y = fs.find(f => f.side === 'York'), l = fs.find(f => f.side === 'Lancaster');
          localStorage.setItem('gw-test-ids', JSON.stringify([y.id, l.id])) }}""")
        gm.goto(BASE + "travel.html")
        gm.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
        gm.evaluate("""() => { const [yid, lid] = JSON.parse(localStorage.getItem('gw-test-ids')), fs = forcesHere();
          const town = (DATA.maps[S.mapId].places || []).find(p => p.name === 'Towton'), y = fs.find(f => f.id === yid), l = fs.find(f => f.id === lid);
          for (const f of fs) if (f !== y && f !== l){ f.pos = [0, 0] }   // the rest far off
          y.pos = [...town.hex]; l.pos = [town.hex[0] + 1, town.hex[1]]; y.order = l.order = 'halt'; y.path = l.path = null; save() }""")
        gm.goto(BASE + "campaign.html")
        gm.wait_for_function("() => typeof REC === 'object' && REC", timeout=15000)
        ed.wait_for_function("() => document.querySelector('#p-force button[data-attack]')", timeout=20000)
        check(True, "Edward's seat offers him the fight")
        check("on its battlefield" in ed.inner_text("#p-force"), "on Towton's battlefield")
        so.wait_for_function("() => document.querySelector('#p-force').textContent.includes('You command Lancaster')", timeout=10000)
        offers = so.evaluate("() => [...document.querySelectorAll('#p-force button[data-attack]')].map(b => b.closest('li').textContent)")
        check(all("against" in t and t.split(" against ")[0].count("York") == 0 for t in offers), "Somerset is offered only fights his own side attacks")

        ed.locator("#p-force button[data-attack]").first.click()
        gm.wait_for_function("() => fieldFrame() && FIELD && FIELD.phase === 'moving'", timeout=30000)
        check(True, "the battle opens on the field map in the console's frame, set up and started by itself")
        ed.wait_for_function("() => !document.querySelector('#p-fight').hidden", timeout=20000)
        so.wait_for_function("() => !document.querySelector('#p-fight').hidden", timeout=20000)
        check(True, "each commander has his side's fight on his page")
        sides = gm.evaluate("() => fieldFrame().eval('NETF.seats.filter(x => x.relay).map(x => x.seat).sort().join()')")
        check(sides == "Lancaster,York", f"each seated on his own side ({sides})")

        # the battle ends: its result goes back to the travel map by itself, and on to the march
        gm.evaluate("() => tellField('end')")
        gm.wait_for_function("() => REC.phase === 'march' && REC.log.some(e => /battle|result/i.test(e.data.text || '') && e.data.kind === 'march')", timeout=30000)
        check(gm.evaluate(f"() => ({TRAVEL}.fought || []).length") >= 1, "the battle's result is taken into the travel map, and the campaign is back on the march")
        check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
        br.close()
finally:
    stop()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
