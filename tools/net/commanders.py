"""Two commanders on the travel map online: the GM's campaign console hosts, each player commands a side.

    python3 tools/net/commanders.py

On the Towton map, with the commander moving York before (Moved by): the GM adds two players and
gives each a side to command (Commands: York, Commands: Lancaster), which takes York from the
commander. Each joins by his room's link (the room server's own code on a local port) from a
browser profile of his own. His page shows every
force of his side and none of the other's; he gives a force a route from his page and it is given
at once, with no proposal for the GM to accept; the other commander's page hears nothing of it.
Each presses Ready; the console says every commander is ready; the GM runs the clock, and the
ready marks clear for the next orders. Needs Python's playwright with Chromium and a built site.
Exits non-zero on any failure.
"""
from playwright.sync_api import sync_playwright
from roomharness import CONNECTED, add_player, check, failures, serve

MAP = "towton-1461"
site, BASE, ROOMS, stop = serve()

try:
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--disable-features=WebRtcHideLocalIpsWithMdns"])
        gctx = br.new_context(viewport={"width": 1400, "height": 1100})
        errors = []
        gm = gctx.new_page()
        gm.on("pageerror", lambda e: errors.append("gm: " + str(e)))
        gm.goto(BASE + "travel.html"); gm.evaluate("() => localStorage.clear()"); gm.reload()
        gm.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
        gm.evaluate(f"""() => {{ S.mapId = {MAP!r}; S.clock = {{}}; forcesHere(); S.cmd[{MAP!r}] = {{ York: 'attack' }}; save();
          const fs = forcesHere(), y = fs.find(f => f.side === 'York'), l = fs.find(f => f.side === 'Lancaster');
          const man = (name, f) => ({{ name, map: {MAP!r}, force: f.id, pid: 'pid-' + name, endurance: 50, str: 50, sex: 'm', fieldcraft: 40, leechcraft: 20, log: [], health: {{ cases: [], immune: {{}}, had: {{}}, dead: 0 }} }});
          localStorage.setItem('gravewounds-named', JSON.stringify({{ u1: man('Hal Ashby', y), u2: man('Wat Tyler', l) }})) }}""")
        york, lanc = gm.evaluate("() => ['York', 'Lancaster'].map(s => forcesHere().filter(f => f.side === s).map(f => f.name))")
        gm.goto(BASE + "campaign.html")
        gm.wait_for_function("() => typeof REC === 'object' && REC", timeout=15000)
        gm.evaluate("() => { setPhase('march'); render() }")
        gm.wait_for_selector("[data-pl-new]")
        codes = [add_player(gm, ROOMS, name, man) for name, man in (("Edward", "u1"), ("Somerset", "u2"))]
        ids = gm.evaluate("() => REC.players.map(p => p.id)")
        gm.select_option(f'select[data-pl-side="{ids[0]}"]', "York")
        gm.select_option(f'select[data-pl-side="{ids[1]}"]', "Lancaster")
        check(gm.evaluate("() => REC.players.map(p => p.side).join()") == "York,Lancaster", "the GM gives each player a side to command")
        check(gm.evaluate(f"() => JSON.parse(localStorage.getItem('gravewounds-travel')).cmd[{MAP!r}].York") is None,
              "a side a person commands is taken from the commander (Moved by)")

        pls = []
        for i, pid in enumerate(ids):                    # each on his own computer, by his room's link: nothing passed back by hand
            pg = br.new_context(viewport={"width": 1100, "height": 900}).new_page()
            pg.on("pageerror", lambda e, i=i: errors.append(f"player {i}: {e}"))
            pg.goto(gm.input_value(f'textarea[data-pl-link="{pid}"]'))
            pg.wait_for_function(CONNECTED, timeout=30000)
            pls.append(pg)
        ed, so = pls
        ed.wait_for_function("() => document.querySelector('#p-force').textContent.includes('You command York')", timeout=10000)
        force = ed.inner_text("#p-force")
        check(all(n in force for n in york) and not any(n in force for n in lanc), f"his page shows every force of York ({len(york)}) and none of Lancaster's")
        check("Give its orders" in force and "Give this route" in force, "with orders to give, not proposals")

        # Edward gives his first force a route: given at once, no proposal waiting for the GM
        box = ed.locator("#p-force .propose").first
        fid = int(box.get_attribute("data-force"))
        box.locator('button[data-propose="to"]').click()
        gm.wait_for_function(f"() => JSON.parse(localStorage.getItem('gravewounds-travel')).forces[{MAP!r}].find(f => f.id === {fid}).order === 'march'", timeout=10000)
        check(gm.evaluate("() => REC.proposals.filter(x => x.state === 'open').length") == 0, "his order is given at once: nothing waits for the GM to accept")
        check(gm.evaluate("() => REC.proposals.at(-1).state") == "given", "and the console keeps it as given")
        so.wait_for_timeout(600)
        check("orders:" not in so.inner_text("#p-news") and "Edward orders" not in so.inner_text("body"), "the other commander hears nothing of it")

        # both ready; the GM runs the clock; the marks clear
        for pg in pls:
            pg.click('#p-force button[data-ready="1"]')
        gm.wait_for_function("() => REC.players.every(p => p.ready)", timeout=10000)
        gm.wait_for_function("() => document.querySelector('#c-march').textContent.includes('Every commander is ready')", timeout=10000)
        check(True, "each presses Ready, and the console says every commander is ready")
        gm.click("#c-run")
        gm.wait_for_function("() => REC.players.every(p => !p.ready)", timeout=10000)
        ed.wait_for_function("() => document.querySelector('#p-force button[data-ready=\"1\"]')", timeout=10000)
        check(True, "the GM runs the clock, and each commander gives his next orders")
        check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
        br.close()
finally:
    stop()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
