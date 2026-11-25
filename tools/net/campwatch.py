"""A watcher on the campaign console: his page and the console over WebRTC in one headless browser (no STUN).

    python3 tools/net/campwatch.py

The watcher's page is in a browser profile of its own, as on his own computer. The GM adds a watcher (copy and
paste); he opens his link, the GM pastes his reply. Then:
- He watches the first side to start with: its forces and its fogged map; no men of his own, no orders to give.
- He hears the public news only: not the GM's notes, nor a line meant for one player.
- Every order he sends is ignored.
- Set to everything by the GM: every force on his page and on his map, with no fog.
- A fight on the console's roller comes to his page, as its watcher: no side is his, and his page has no controls.
- Set to a side that is not in that fight, the fight goes from his page; when that side is in it, he watches it as
  that side, the enemy veiled.
- A battle on the console's field map comes to him too, as its watcher, and seats no side.
- On a phone his page is in tabs (Forces, Map, Fight while a fight is on, News), the fight's opened when it begins.

Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
from pathlib import Path
from playwright.sync_api import sync_playwright
from roomharness import check, failures, serve

MAP = "towton-1461"
site, BASE, ROOMS, stop = serve()                      # the room server stands by unused: this console copies and pastes

try:
    with sync_playwright() as p:
        br = p.chromium.launch(args=["--disable-features=WebRtcHideLocalIpsWithMdns"])
        gctx = br.new_context(viewport={"width": 1400, "height": 1100})
        wctx = br.new_context(viewport={"width": 1100, "height": 900})   # his own computer: nothing of the GM's storage
        gm, w = gctx.new_page(), wctx.new_page()
        errors = []
        for pg, who in ((gm, "console"), (w, "watcher")):
            pg.on("pageerror", lambda e, who=who: errors.append(f"{who}: {e}"))
            pg.on("dialog", lambda d: d.accept())
        gm.goto(BASE + "travel.html"); gm.evaluate("() => localStorage.clear()"); gm.reload()
        gm.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
        gm.evaluate(f"""() => {{ S.mapId = {MAP!r}; S.clock = {{}}; save();
          const fs = forcesHere(), a = fs[0]; save();
          const man = (name, f) => ({{ name, map: {MAP!r}, force: f.id, pid: 'pid-' + name, endurance: 50, str: 50, sex: 'm', fieldcraft: 40, leechcraft: 20, log: [], health: {{ cases: [], immune: {{}}, had: {{}}, dead: 0 }} }});
          localStorage.setItem('gravewounds-named', JSON.stringify({{ u1: man('Hal Ashby', a) }})) }}""")
        sides = gm.evaluate("() => [...new Set(forcesHere().map(f => f.side))]")
        first, other = sides[0], sides[1]
        ours = gm.evaluate(f"() => forcesHere().filter(f => f.side === {first!r}).map(f => f.name)")
        theirs = gm.evaluate(f"() => forcesHere().filter(f => f.side !== {first!r}).map(f => f.name)")
        gm.evaluate("() => localStorage.setItem('gw-room-server', 'off')")
        gm.goto(BASE + "campaign.html")
        gm.wait_for_function("() => typeof REC === 'object' && REC", timeout=15000)
        gm.evaluate("() => { setPhase('march'); render() }")
        gm.fill("#c-note", "The scouts saw Clifford's banners."); gm.uncheck("#c-note-gm"); gm.click("#c-add-note")
        gm.fill("#c-note", "Clifford waits in ambush at the ford."); gm.check("#c-note-gm"); gm.click("#c-add-note")
        gm.evaluate("() => { REC.players.push({ id: 'pp1', name: 'Scott', men: ['u1'] }); noteFor('A word for Scott alone.', ['player:pp1']); render(); renderPlayers() }")
        gm.wait_for_selector("#pl-watch")
        gm.uncheck("#pl-stun")
        gm.fill("#pl-name", "Anne")
        gm.click("#pl-watch")
        gm.wait_for_selector('textarea[data-pl-link]:below(:text("Anne"))', timeout=15000)
        pl = gm.evaluate("() => REC.players.find(x => x.watch)")
        check(pl and pl["name"] == "Anne" and pl["view"] == first and pl["men"] == [], f"the GM adds a watcher: no men, the first side's view to start with ({pl and pl['view']})")
        link = gm.evaluate("() => playerLink(PL.conn[REC.players.find(x => x.watch).id].code)")
        w.goto(link)
        w.wait_for_function("() => (document.querySelector('#p-reply') || {}).value", timeout=20000)
        gm.fill(f'textarea[data-pl-reply="{pl["id"]}"]', w.input_value("#p-reply"))
        gm.click(f'button[data-pl="accept"][data-id="{pl["id"]}"]')
        w.wait_for_function("() => document.body.classList.contains('watching')", timeout=20000)
        check("1 watching" in gm.inner_text("#c-players") and "0 connected" in gm.inner_text("#c-players"), "the console counts him as watching, not as a player")
        force, news = w.inner_text("#p-force"), w.inner_text("#p-news")
        check(all(n in force for n in ours) and not any(n in force for n in theirs), f"his page shows the first side's forces ({len(ours)}), none of the other's")
        check(not w.is_visible("#p-men") and w.inner_text("#h-pforce") == "The forces" and "watching" in w.inner_text("#p-who"), "no men panel of his own; worded for watching")
        check("scouts saw" in news and "ambush" not in news and "for Scott alone" not in news, "he hears the public news only: not the GM's notes, nor a line for one player")
        check(w.locator("#p-force .propose, #p-force [data-council-ask], #p-force [data-ready]").count() == 0, "no orders, proposals, councils or Ready on his page")
        w.wait_for_selector("#p-mapbox iframe", timeout=10000)
        mp = w.frame_locator("#p-mapbox iframe")
        mp.locator("#map svg .force").first.wait_for(timeout=15000)
        marks = mp.locator("#map svg .force:not(.ghost):not(.spotted) title").all_text_contents()
        check(all(any(t.startswith(n + " (") for t in marks) for n in ours) and not any(t.startswith(n + " (") for n in theirs for t in marks),
              f"his map shows the first side's forces, and not the other's it cannot see ({len(marks)} marks)")
        n0 = gm.evaluate("() => (REC.proposals || []).length")
        fid = gm.evaluate("() => newDay().marchSummary().forces[0].id")
        w.evaluate(f"() => {{ PG.send({{ t: 'propose', force: {fid}, what: 'halt' }}); PG.send({{ t: 'council', force: {fid}, why: 'x' }}); PG.send({{ t: 'ready', on: true }}) }}")
        gm.wait_for_timeout(600)
        check(gm.evaluate("() => (REC.proposals || []).length") == n0, "every order he sends is ignored")
        gm.select_option(f'select[data-pl-view="{pl["id"]}"]', "")
        w.wait_for_function(f"() => {theirs!r}.every(n => document.querySelector('#p-force').textContent.includes(n))", timeout=10000)
        mp.locator("#seat-key").filter(has_text="Every force").wait_for(timeout=10000)
        marks = mp.locator("#map svg .force title").all_text_contents()
        check(all(any(t.startswith(n + " (") for t in marks) for n in ours + theirs) and "everything" in w.inner_text("#p-who"),
              f"set to everything: every force on his page and his map, no fog ({len(marks)} marks)")
        # a fight on the console's roller
        gm.evaluate("() => { setPhase('fight'); render(); show('roller.html') }")
        gm.wait_for_function("() => !!rollerFrame()", timeout=20000)
        rf = next(f for f in gm.frames if f.url.endswith("roller.html"))
        rf.wait_for_function("() => typeof S === 'object' && S.chars.length > 1", timeout=20000)
        rf.evaluate("() => { gmStart(); for (const sd of sidesInOrder()) S.gm.sides[sd].ctl = 'script'; renderChars() }")
        w.wait_for_selector("#p-fight iframe", timeout=15000)
        inner = None
        for _ in range(60):
            inner = next((f for f in w.frames if "roller.html#relay" in f.url), None)
            if inner:
                break
            w.wait_for_timeout(250)
        inner.wait_for_function("() => document.body.classList.contains('watching') && document.querySelector('#chars').children.length > 1", timeout=15000)
        check(w.is_visible("#p-fight") and w.inner_text("#h-pfight") == "The fight", "a fight on the console's roller comes to his page")
        check(inner.locator("#chars .char.veiled").count() == 0 and "everything" in inner.inner_text("#g-status") and not inner.is_visible("#g-rollbar"),
              "as its watcher seeing everything: no card veiled, no controls")
        check(rf.evaluate("() => sidesInOrder().every(sd => gmSide(sd).ctl === 'script') && NETH.peers.some(p => p.relay && p.watch)"), "on the roller he is a watcher's seat: every side stays the script's")
        fight_sides = rf.evaluate("() => sidesInOrder()")
        gm.evaluate(f"() => setView({pl['id']!r}, {other!r})")
        if other not in fight_sides:
            w.wait_for_function("() => document.querySelector('#p-fight').hidden", timeout=15000)
            check(True, f"set to a side not in this fight ({other}), the fight goes from his page")
        rf.evaluate(f"() => {{ const sd = sidesInOrder()[0]; for (const c of S.chars) if (sideOf(c) === sd) c.side = {other!r}; renderChars() }}")   # the fight's first side is now the side he watches
        w.wait_for_function("() => !document.querySelector('#p-fight').hidden", timeout=15000)
        inner = None
        for _ in range(60):
            inner = next((f for f in w.frames if "roller.html#relay" in f.url), None)
            if inner and inner.evaluate("() => document.querySelectorAll('#chars .char').length") > 1:
                break
            w.wait_for_timeout(250)
        inner.wait_for_function("() => document.querySelectorAll('#chars .char.veiled').length > 0", timeout=15000)
        check(f"{other}'s view" in inner.inner_text("#g-status"), f"his side in the fight: he watches it as that side, the enemy veiled ({inner.inner_text('#g-status')[:50]})")
        gm.evaluate(f"() => setView({pl['id']!r}, '')")
        # a battle on the console's field map
        gm.evaluate("() => show('field.html')")
        gm.wait_for_function("() => !!fieldFrame()", timeout=20000)
        ff = next(f for f in gm.frames if f.url.endswith("field.html"))
        ff.wait_for_function("() => typeof S === 'object' && Array.isArray(S.units)", timeout=20000)
        ff.evaluate("() => { freshState(); render() }")
        w.wait_for_function("() => { const f = document.querySelector('#p-fight iframe'); return f && f.src.includes('field.html#relay') && f.contentDocument && f.contentDocument.querySelectorAll('#map .hx').length > 0 }", timeout=20000)
        fin = next(f for f in w.frames if "field.html#relay" in f.url)
        check(fin.evaluate("() => document.body.classList.contains('watching')") and fin.evaluate("() => document.querySelectorAll('#map g.unit').length") == 4,
              "a battle on the console's field map comes to him as its watcher, every unit shown")
        check(ff.evaluate("() => NETF.seats.some(p => p.relay && p.watch) && !seatedSide(0) && !seatedSide(1)"), "and seats no side there")
        # his page on a phone: in tabs, the battle's first while it is on
        w.set_viewport_size({"width": 390, "height": 844})
        tabs = [t for t in w.locator("#p-tabs button:visible").all_inner_texts()]
        check(tabs == ["Forces", "Map", "Fight", "News"] and w.get_attribute('#p-tabs [data-tab="fight"]', "aria-pressed") == "true"
              and w.is_visible("#p-fight") and not w.is_visible("#p-force"), f"on a phone his page is in tabs, the battle's open while it is on ({tabs})")
        w.click('#p-tabs [data-tab="map"]')
        check(w.is_visible("#p-mapbox iframe") and not w.is_visible("#p-fight") and not w.is_visible("#p-news"), "the Map tab shows his map alone")
        w.wait_for_timeout(400)
        w.screenshot(path=str(Path(__file__).parent / ".cache" / "campaign-watcher-phone.png"))
        w.click('#p-tabs [data-tab="news"]')
        check(w.is_visible("#p-news") and not w.is_visible("#p-mapbox"), "the News tab shows the news")
        gm.evaluate("() => show('travel.html')")
        w.wait_for_function("() => document.querySelector('#p-tabs [data-tab=fight]').hidden", timeout=15000)
        check(w.is_visible("#p-force") and w.get_attribute('#p-tabs [data-tab="forces"]', "aria-pressed") == "true", "the battle over, its tab goes and his page is back on the forces")
        w.set_viewport_size({"width": 1100, "height": 900})
        check(w.is_visible("#p-force") and w.is_visible("#p-news") and not w.is_visible("#p-tabs"), "on a wider screen every panel shows, with no tabs")
        check(not errors, f"no page errors {errors[:3]}")
        br.close()
finally:
    stop()

print(f"{'all checks passed' if not failures else str(len(failures)) + ' failed'}")
raise SystemExit(1 if failures else 0)
