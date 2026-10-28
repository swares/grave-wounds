"""A hero's papers and his epilogue, in the team builder, in a headless browser, served as the site is.

    python3 tools/campaign/papers.py

A retinue rolled: Papers shows his muster entry (his lifepath) and his surgeon's card (his old wounds, and
the roller's wounds for him), each marked as a game handout; a man discharged gets an epilogue from his
era's table and a discharge paper; a dead man a notice of death; and every era and army has an epilogue for
each way of leaving. Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import json, sys
from playwright.sync_api import sync_playwright
from harness import check, failures, serve

BASE, server = serve()
HANDOUT = "game handout"
BOX = "#papers"

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1300, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE + "team.html"); pg.evaluate("() => localStorage.clear()"); pg.reload()
    pg.select_option("#sel-region", "england"); pg.select_option("#sel-template", "retinue")
    pg.click("#btn-roll")
    c = pg.evaluate("() => ({ name: S.team[0].name, pid: S.team[0].pid, events: S.team[0].events.length, old: S.team[0].old.length })")
    roller = {"chars": [{"name": c["name"], "sheet": {"pid": c["pid"]}, "wounds": [{"loc": "thigh_l", "mech": "cut", "sev": "serious", "treated": "bound"}], "scars": [{"loc": "forearm_r"}]}]}
    pg.evaluate(f"() => localStorage.setItem('gravewounds-chars', {json.dumps(json.dumps(roller))})")
    pg.click("#sheets button[data-papers='0']")
    text = pg.inner_text(BOX)
    check(pg.is_visible(BOX) and "From the muster roll" in text and "barber-surgeon" in text.lower(), "Papers opens his muster entry and his surgeon's card, in his era's words")
    check(text.lower().count(HANDOUT) == 2, "each paper says it is a game handout")
    check(c["name"] in text and text.count("Term ") >= c["events"], f"the muster entry names him and gives his terms as a lifepath ({c['events']})")
    check("Thigh (left)" in text and "treated: bound" in text and "Forearm (right)" in text, "the surgeon's card has the roller's open and healed wounds for him")
    check("Off the roll" not in text, "a man still serving has no discharge paper")
    pg.click("#btn-papers-close")
    check(pg.is_hidden(BOX), "Close puts the papers away")

    pg.click("#sheets button[data-lose='1']")
    pg.select_option("select[data-lose-why='1']", "discharged")
    pg.click("button[data-lose-ok='1']")
    lost = pg.evaluate("() => S.losses[0]")
    check(lost["epilogue"] and lost["epilogue"]["kind"] == "alive" and len(lost["epilogue"]["text"]) > 20, f"a man discharged gets an epilogue ({lost['epilogue'] and lost['epilogue']['text'][:70]})")
    check(lost["epilogue"]["text"] in pg.inner_text("#losses"), "the losses show what became of him")
    pg.click("#losses button[data-papers-lost='0']")
    box = pg.evaluate("() => { const d = document.querySelector('#papers'), r = d.getBoundingClientRect(); return { top: r.top, bottom: r.bottom, vh: innerHeight, client: d.clientHeight, scroll: d.scrollHeight } }")
    check(box["top"] >= 0 and box["bottom"] <= box["vh"] and box["scroll"] > box["client"], f"the papers fit the window and scroll ({box})")
    pg.mouse.move(600, 500); pg.mouse.wheel(0, 4000); pg.wait_for_timeout(200)
    close = pg.evaluate("() => document.querySelector('#btn-papers-x').getBoundingClientRect().top")
    check(pg.evaluate("() => document.querySelector('#papers').scrollTop") > 0 and 0 <= close < 120, "scrolled down, the close button stays in sight")
    text = pg.inner_text(BOX)
    check("Off the roll" in text and "What became of him" in text and lost["epilogue"]["text"] in text, "his papers add a discharge with his epilogue")
    pg.click("#btn-papers-x")
    check(pg.is_hidden(BOX), "the × closes them")

    pg.click("#sheets button[data-lose='0']")
    pg.select_option("select[data-lose-why='0']", "killed")
    pg.click("button[data-lose-ok='0']")
    dead = pg.evaluate("() => S.losses[1]")
    check(dead["epilogue"]["kind"] == "dead", f"a man killed gets a dead man's epilogue ({dead['epilogue']['text'][:70]})")
    pg.click("#losses button[data-papers-lost='1']")
    check("Struck from the roll: dead" in pg.inner_text(BOX), "and a notice of death")
    pg.keyboard.press("Escape")
    check(pg.is_hidden(BOX), "Escape puts the papers away")

    missing = pg.evaluate("""() => { const out = [], m = { old: [] }, w = { old: [{ kind: 'lasting', loc: 'knee_l' }] };
      for (const [eid, E] of Object.entries(TD.eras)) for (const r of E.era.regions) for (const why of ['killed', 'deserted', 'sent home'])
        for (const old of [m, w]) { const x = epRoll(eid, { ...old, name: 'X', region: r.id, sex: 'm' }, why, realDice);
          if (!x) out.push(`${eid} ${r.id} ${why}${old.old.length ? ' (lasting)' : ''}`); else if (/\\{/.test(x.text)) out.push(`${eid}: ${x.text}`) }
      return out }""")
    check(not missing, f"every era and army has an epilogue for each way of leaving, its words filled ({missing[:4]})")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()
server.shutdown()
print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
sys.exit(1 if failures else 0)
