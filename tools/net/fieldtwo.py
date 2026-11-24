"""The field map online: the GM's field page and a player's page, over WebRTC in one headless browser.

    python3 tools/net/fieldtwo.py

On the field page's own Towton skirmish, drawn up 440 m apart on a dark night (sight 25 hexes), with
the room server's own code on a local port (tools/net/fakerooms.mjs) and no STUN (same machine):

1. By hand: the GM invites a player for the Yorkists (a link), the player's page answers, the GM
   pastes the reply. The player's page shows the Yorkists' view: their two units, not the
   Lancastrians', and nothing naming them. In set-up it waits. In the battle, on his side's move, he
   picks a unit (the GM's own pick stays his), clicks a hex and it moves, and ends the move. A
   choice not his to make is ignored: an enemy he does not see, the GM's End the battle, a move on
   the other side's turn.
2. By room code: invited again through a room, his page (field.html#room=CODE) answers by itself.

Needs Node, Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
from playwright.sync_api import sync_playwright
from roomharness import check, failures, serve

site, BASE, ROOMS, stop = serve()
FIELD = BASE + "field.html"
G_UNITS = "() => document.querySelectorAll('#map g.unit').length"

try:
    with sync_playwright() as p:
        br = p.chromium.launch()
        ctx = br.new_context(viewport={"width": 1400, "height": 1100})
        gm, pl = ctx.new_page(), ctx.new_page()
        errors = []
        for pg in (gm, pl):
            pg.on("pageerror", lambda e, pg=pg: errors.append(f"{'gm' if pg is gm else 'player'}: {e}"))
        gm.goto(FIELD)
        gm.evaluate("() => { localStorage.clear(); localStorage.setItem('gw-room-server', 'off') }")
        gm.reload()
        gm.evaluate("() => { freshState(); [[8, 20], [6, 13], [52, 20], [54, 27]].forEach((h, i) => { S.units[i].pos = h }); render() }")
        gm.select_option("#sel-light", "night")
        gm.click("#net-box summary")
        gm.uncheck("#netf-stun")
        gm.click('button[data-netf="invite"][data-side="Yorkists"]')
        gm.wait_for_selector("textarea[data-netf-link]", timeout=20000)
        link = gm.input_value("textarea[data-netf-link]")
        check("#join=" in link, "with no room server, the invitation is a #join= link")

        pl.goto(link)
        pl.wait_for_selector("#g-reply", timeout=20000)
        gm.fill("textarea[data-netf-reply]", pl.input_value("#g-reply"))
        gm.click('button[data-netf="accept"]')
        pl.wait_for_function("() => document.querySelectorAll('#map .hx').length > 0", timeout=20000)
        check(pl.evaluate(G_UNITS) == 2, f"the player's page draws the Yorkists' two units, not the Lancastrians' ({pl.evaluate(G_UNITS)})")
        body = pl.inner_text("body")
        check("(Lancastrians)" not in body and "(Lancastrians)" not in pl.inner_html("body"), "and nothing on it names the Lancastrians' units (their side's name, in the legend, is no secret)")
        check(pl.inner_text("#g-next") == "The GM is setting up" and pl.is_disabled("#g-next"), "in set-up he waits for the GM")
        check("Use a public STUN" in gm.inner_text("#net-box") and "1 player connected" in gm.inner_text("#net-box"), "the GM's Play online shows him connected")

        gm.click("#btn-next")                                    # the battle begins: the Yorkists move first
        pl.wait_for_function("() => !document.querySelector('#g-next').disabled", timeout=10000)
        check("End Yorkists' move" == pl.inner_text("#g-next"), "on his side's move his page offers End the move")
        gm_sel = gm.evaluate("() => S.sel")
        pl.click("#units li[data-id]")                           # his first unit
        pl.wait_for_function("() => document.querySelector('#sel-box #sel-name')?.textContent.includes('Billmen')", timeout=10000)
        check(gm.evaluate("() => S.sel") == gm_sel, "his pick is his own: the GM's selected unit stays as it was")
        before = gm.evaluate("() => S.units[0].pos.join(',')")
        pl.click('#map .hx[data-h="10,20"]', force=True)
        gm.wait_for_function(f"() => S.units[0].pos.join(',') !== '{before}'", timeout=10000)
        check(gm.evaluate("() => S.units[0].pos.join(',')") == "10,20", "a hex he clicks moves his unit there on the GM's page")

        facing = gm.evaluate("() => S.units[0].facing")
        pl.click("#sel-box #btn-right")
        gm.wait_for_function(f"() => S.units[0].facing !== {facing}", timeout=10000)
        check(True, "Turn right on his selected unit's panel turns it on the GM's page")
        pl.evaluate("() => FG.send({ t: 'unit', id: 3 })")      # the Lancastrian billmen: unseen in the dark
        pl.evaluate("() => FG.send({ t: 'click', id: 'btn-end' })")   # the GM's End the battle
        gm.wait_for_timeout(600)
        check(gm.evaluate("() => NETF.seats[0].ui.sel") == 1, "an enemy his side does not see cannot be picked (his pick stays his billmen)")
        check(gm.evaluate("() => S.phase") == 0, "the GM's End the battle is not his to press")

        pl.click("#g-next")
        gm.wait_for_function("() => S.phase === 1", timeout=10000)
        check(True, "End the move from his page ends the Yorkists' move")
        pl.wait_for_function("() => document.querySelector('#g-next').disabled", timeout=10000)
        pos = gm.evaluate("() => S.units[1].pos.join(',')")
        pl.evaluate("() => FG.send({ t: 'hex', h: [8, 13] })")
        gm.wait_for_timeout(600)
        check(gm.evaluate("() => S.units[1].pos.join(',')") == pos, "on the other side's move his clicks move nothing")

        # 2. by room code: the GM's page invites him again through a room; his page answers by itself
        gm.evaluate(f"() => {{ localStorage.setItem('gw-room-server', {ROOMS!r}) }}")
        gm.click('button[data-netf="drop"]')
        gm.click('button[data-netf="invite"][data-side="Yorkists"]')
        gm.wait_for_selector("input[data-netf-link]", timeout=20000)
        room_link = gm.input_value("input[data-netf-link]")
        check("#room=" in room_link, f"with a room server the link is a room ({room_link.split('#')[1][:20]}...)")
        pl2 = ctx.new_page(); pl2.on("pageerror", lambda e: errors.append(f"player2: {e}"))
        pl2.goto(room_link)
        pl2.wait_for_function("() => document.querySelectorAll('#map .hx').length > 0", timeout=30000)
        check(pl2.evaluate(G_UNITS) == 2, "through the room, nothing pasted back, his page shows his side's view")

        check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
        br.close()
finally:
    stop()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
