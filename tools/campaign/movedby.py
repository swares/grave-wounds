"""The commander on the march, on the pages: Moved by on the travel map and under Run the march.

    python3 tools/campaign/movedby.py

On the travel map's Towton map: Moved by offers each side to you or the commander; given York,
attacking, a press of the clock has the commander send its columns; with Edward's army beside a
Lancastrian force far smaller, a press sends the fight itself (the page opens on it, with its
handoff). On the campaign page in the march: Moved by is under Run the march, and a choice there
is kept and logged. Needs Python's playwright with Chromium and a built site.
"""
import json
from harness import check, main, serve

BASE, server = serve()


def run(pw):
    br = pw.chromium.launch()
    ctx = br.new_context(viewport={"width": 1400, "height": 1000})   # one browser's storage, both pages
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(BASE + "travel.html")
    pg.evaluate("() => localStorage.clear()")
    pg.reload()
    pg.select_option("#sel-map", "towton-1461")
    opts = pg.eval_on_selector_all("#moved-by select", "ss => ss.map(s => s.dataset.movedby)")
    check(sorted(opts) == ["Lancaster", "York"], f"Moved by offers each side ({opts})")
    pg.select_option("#moved-by select[data-movedby='York']", "attack")
    check(pg.evaluate("() => S.cmd['towton-1461'].York") == "attack" and "The commander moves York" in pg.inner_text("#msg"), "given to the commander, attacking, and the page says so")
    pg.click("#btn-clock-hour")
    check("The commander sends" in pg.inner_text("#msg"), f"a press of the clock: the commander sends York's columns ({pg.inner_text('#msg')[:120]})")
    check(pg.evaluate("() => forcesHere().filter(f => f.side === 'Lancaster').every(f => f.order !== 'march')"), "and Lancaster, moved by hand, is left alone")
    pg.evaluate("""() => { const fs = forcesHere(), a = fs.find(f => f.name.startsWith("Edward")), m = curMap(), far = [m.rows[0].length - 1, m.rows.length - 1];
      const e = fs.find(f => f.side === 'Lancaster'); for (const f of fs) if (f !== a && f !== e) f.pos = f.side === 'York' ? [0, 0] : far.slice();
      e.pos = [a.pos[0] + 1, a.pos[1]]; e.men = 300; a.men = 9000; render() }""")
    with pg.expect_navigation(timeout=15000):
        pg.click("#btn-clock-hour")
    check(pg.url.split("/")[-1].split("#")[0] in ("roller.html", "field.html"), f"in reach and the stronger, it sends its own fight: the page opens on it ({pg.url.split('/')[-1]})")
    hand = pg.evaluate("() => localStorage.getItem('gravewounds-handoff') || localStorage.getItem('gravewounds-field-handoff')")
    check(bool(hand) and "Edward" in hand, "with the fight's handoff")

    c = ctx.new_page()
    c.on("pageerror", lambda e: errors.append("campaign: " + str(e)))
    c.goto(BASE + "campaign.html")
    c.evaluate("() => { setPhase('march', 'test'); render() }")
    c.wait_for_selector("#c-march select[data-movedby]", timeout=10000)
    sel = c.eval_on_selector_all("#c-march select[data-movedby]", "ss => ss.map(s => [s.dataset.movedby, s.value])")
    check(dict(sel).get("York") == "attack", f"under Run the march, Moved by shows the travel map's choice ({sel})")
    c.select_option("#c-march select[data-movedby='Lancaster']", "hold")
    c.wait_for_function("() => JSON.parse(localStorage.getItem('gravewounds-travel')).cmd['towton-1461'].Lancaster === 'hold'", timeout=6000)
    check("The commander moves Lancaster, holding" in c.inner_text("body"), "a choice there is kept, and logged")
    check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
    br.close()


main(run, server)
