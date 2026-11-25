"""Watchers: someone joined to an online fight or battle to watch it only, over WebRTC in one headless browser.

    python3 tools/net/watch.py

1. The field map (its Towton skirmish, 440 m apart on a dark night; the room server's own code on a local port,
   tools/net/fakerooms.mjs; no STUN): the GM invites a watcher by room code, on a phone-sized page.
   - He sees the first side's view to start with (its two units), with no orders to give.
   - On a phone it is in tabs: Map, Units, Log, Story.
   - He can pick a unit he sees to look at it; it does not change the GM's pick.
   - Every order he sends is ignored, on any side's move.
   - The GM sets him to see everything: he sees all four units.
2. The roller (a fight of two sides, by hand: the link and the reply pasted back): the GM invites a watcher.
   - He sees the first side's screen: the enemy's card veiled; no roll bar, no map buttons.
   - His choices are ignored, and he plays no side: both stay the script's.
   - Set to everything, the enemy's card is no longer veiled.
   - After the GM's page is reloaded, the watcher waits to be invited again, with what he sees.

Needs Node, Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
from roomharness import check, failures, serve

site, BASE, ROOMS, stop = serve()
FIELD, ROLLER = BASE + "field.html", BASE + "roller.html"
G_UNITS = "() => document.querySelectorAll('#map g.unit').length"
PHONE = {"width": 390, "height": 844}
SHOTS = Path(__file__).parent / ".cache"                    # the watcher's phone page, as a picture, for a look


def field(br, errors):
    ctx = br.new_context(viewport={"width": 1400, "height": 1100})
    gm = ctx.new_page()
    gm.on("pageerror", lambda e: errors.append(f"field gm: {e}"))
    gm.goto(FIELD)
    gm.evaluate(f"() => {{ localStorage.clear(); localStorage.setItem('gw-room-server', {ROOMS!r}) }}")
    gm.reload()
    gm.evaluate("() => { freshState(); [[8, 20], [6, 13], [52, 20], [54, 27]].forEach((h, i) => { S.units[i].pos = h }); render() }")
    gm.select_option("#sel-light", "night")
    gm.click("#net-box summary")
    gm.uncheck("#netf-stun")
    gm.click('button[data-netf="watch"]')
    gm.wait_for_selector("input[data-netf-link]", timeout=20000)
    link = gm.input_value("input[data-netf-link]")
    check("#room=" in link, "the field's watcher is invited by room code, like a player")
    phone = br.new_context(viewport=PHONE, is_mobile=True, has_touch=True).new_page()
    phone.on("pageerror", lambda e: errors.append(f"field watcher: {e}"))
    phone.goto(link)
    phone.wait_for_function("() => document.body.classList.contains('watching') && document.querySelectorAll('#map .hx').length > 0", timeout=30000)
    check(phone.evaluate(G_UNITS) == 2 and "Yorkists' view" in phone.inner_text("#g-status"),
          f"he sees the first side's view to start with ({phone.evaluate(G_UNITS)} units; {phone.inner_text('#g-status')[:60]})")
    check(not phone.is_visible("#g-next") and "1 watching" in gm.inner_text("#net-box") and "0 players" in gm.inner_text("#net-box"),
          "no End the move on his page; the GM's Play online counts him as watching, not playing")
    check(gm.evaluate("() => [aiOf(0), aiOf(1)]") == gm.evaluate("() => [aiOf(0), aiOf(1)]") and not gm.evaluate("() => seatedSide(0)"),
          "a watcher seats no side: it stays the GM's or the commander's")
    tabs = phone.locator("#g-tabs button").all_inner_texts()
    check(tabs == ["Map", "Units", "Log", "Story"] and phone.is_visible("#map") and not phone.is_visible("#units"), f"on a phone his page is in tabs, the map first ({tabs})")
    phone.click('#g-tabs [data-tab="units"]')
    check(phone.is_visible("#units") and not phone.is_visible("#map"), "the Units tab shows the units, not the map")
    gm_sel = gm.evaluate("() => S.sel")
    phone.click("#units li[data-id]")
    phone.wait_for_function("() => document.querySelector('#sel-box #sel-name')", timeout=10000)
    check(gm.evaluate("() => S.sel") == gm_sel, "he picks a unit he sees to look at it; the GM's pick stays his own")
    check(phone.locator("#sel-box button:visible, #sel-box select:visible").count() == 0, "the unit's panel shows him no orders")
    gm.click("#btn-next")                                         # the battle begins: the Yorkists move first
    gm.wait_for_function("() => S.phase === 0", timeout=10000)
    before = gm.evaluate("() => JSON.stringify([S.phase, S.units.map(u => [u.pos, u.facing])])")
    phone.evaluate("""() => { FG.send({ t: 'hex', h: [10, 20] }); FG.send({ t: 'click', id: 'btn-right' }); FG.send({ t: 'next' });
      FG.send({ t: 'change', id: 'sel-order', v: 'charge' }) }""")
    gm.wait_for_timeout(600)
    check(gm.evaluate("() => JSON.stringify([S.phase, S.units.map(u => [u.pos, u.facing])])") == before, "every order he sends is ignored, on the side's move he watches")
    gm.select_option('select[data-netf-view]', "")
    phone.click('#g-tabs [data-tab="map"]')
    phone.wait_for_function("() => document.querySelectorAll('#map g.unit').length === 4", timeout=10000)
    check("everything" in phone.inner_text("#g-status"), "set to everything by the GM, he sees all four units")
    SHOTS.mkdir(parents=True, exist_ok=True)
    phone.screenshot(path=str(SHOTS / "watcher-phone.png"))
    ctx.close()


def roller(br, errors):
    ctx = br.new_context(viewport={"width": 1400, "height": 1100})
    gm, w = ctx.new_page(), ctx.new_page()
    for pg, who in ((gm, "roller gm"), (w, "roller watcher")):
        pg.on("pageerror", lambda e, who=who: errors.append(f"{who}: {e}"))
    gm.goto(ROLLER); gm.evaluate("() => localStorage.clear()"); gm.reload()
    gm.evaluate("""() => { const [a, b] = S.chars; for (const c of S.chars){ c.wounds = []; c.blood = poolOf(c); c.state = null }
      a.pos = [6, 5]; b.pos = [9, 5]; renderChars() }""")
    me, foe = gm.evaluate("() => sidesInOrder()")
    gm.evaluate(f"() => {{ gmStart(); S.gm.sides[{foe!r}].ctl = 'script'; S.gm.sides[{me!r}].ctl = 'script'; renderChars() }}")   # the script plays both: a watcher must change neither
    gm.click("#net-bar summary"); gm.uncheck("#net-stun")
    gm.click('button[data-net="watch"]')
    gm.wait_for_selector("textarea[data-net-link]")
    w.goto(gm.input_value("textarea[data-net-link]"))
    w.wait_for_function("() => (document.querySelector('#g-reply') || {}).value", timeout=20000)
    check("to watch" in w.inner_text("#g-status") or "watcher" in w.inner_text("#g-join"), "the roller's watcher's page knows he joins to watch")
    gm.fill("textarea[data-net-reply]", w.input_value("#g-reply"))
    gm.click('button[data-net="accept"]')
    w.wait_for_function("() => document.body.classList.contains('watching') && document.querySelector('#chars').children.length > 0", timeout=20000)
    check(w.locator("#chars .char.veiled").count() == 1 and f"{me}'s view" in w.inner_text("#g-status"),
          f"he sees the first side's screen: the enemy's card veiled ({w.inner_text('#g-status')[:60]})")
    check(gm.evaluate(f"() => [gmSide({me!r}).ctl, gmSide({foe!r}).ctl]") == ["script", "script"], "both sides stay the script's: a watcher plays none")
    check(not w.is_visible("#g-rollbar") and w.locator("#map-actions button").count() == 0 and w.inner_text("#g-strike-h") == "The last strike",
          "no roll bar and no map buttons on his page")
    gm.evaluate("() => { S.gm.auto = false; gmFirstTurn(); renderChars() }")
    before = gm.evaluate("() => JSON.stringify([S.turn, S.chars.map(c => c.pos), S.events.length])")
    w.evaluate("() => { GUEST.send({ t: 'next' }); GUEST.send({ t: 'hex', h: [7, 5] }); GUEST.send({ t: 'map', act: 'stay' }); GUEST.send({ t: 'roll', rolls: { atk: 1 } }) }")
    gm.wait_for_timeout(500)
    check(gm.evaluate("() => JSON.stringify([S.turn, S.chars.map(c => c.pos), S.events.length])") == before, "his choices are ignored, on any turn")
    gm.select_option("select[data-net-view]", "gm")
    w.wait_for_function("() => document.querySelectorAll('#chars .char.veiled').length === 0", timeout=10000)
    check("everything" in w.inner_text("#g-status"), "set to everything, no card is veiled on his page")
    gm.reload()
    gm.wait_for_selector('button[data-net="again"]', timeout=10000)
    check(gm.evaluate("() => NETH.peers.map(p => [p.watch, p.view])") == [[True, "gm"]], "after the GM's page is reloaded, the watcher waits to be invited again, seeing everything")
    ctx.close()


try:
    with sync_playwright() as p:
        br = p.chromium.launch()
        errors = []
        field(br, errors)
        roller(br, errors)
        check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
        br.close()
finally:
    stop()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
