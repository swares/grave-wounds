"""Presence and followers, in the team builder, in a headless browser, served as the site is.

    python3 tools/campaign/followers.py

A retinue rolled: the followers' line shows how many the leader's Presence keeps (the template's
14 times his band's share, data/followers.yaml); more than that brings a warning but can still be
added; at End of season half the men over the cap, rounded up, drift away (deserted or gone home)
and the counts drop with them; under the cap nobody leaves. Needs Python's playwright with Chromium
and a built site. Exits non-zero on any failure.
"""
import math, re, sys
from playwright.sync_api import sync_playwright
from harness import check, failures, serve

BASE, server = serve()
BANDS = [(29, 0.5), (44, 0.75), (59, 1), (74, 1.25), (999, 1.5)]

def cap_for(pres, total=14):
    return max(1, int(total * next(s for to, s in BANDS if pres <= to) + 0.5))

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1300, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE + "team.html"); pg.evaluate("() => localStorage.clear()"); pg.reload()
    pg.select_option("#sel-region", "england"); pg.select_option("#sel-template", "retinue")
    pg.click("#btn-roll")
    check(pg.evaluate("() => fwCap([['archer', 14]], 20)") == 7 and pg.evaluate("() => fwCap([['archer', 14]], 90)") == 21
          and pg.evaluate("() => fwCap([['archer', 14]], 50)") == 14, "the cap is 14 times the band's share: ½ at 20, 1 at 50, 1½ at 90")
    for pres, want in ((20, 7), (50, 14), (90, 21)):
        check(cap_for(pres) == want, f"the test's bands match at Presence {pres}")
    pg.evaluate("() => { const c = S.team.find(m => m.leader); c.base.pres = 20 - c.stat_mods.pres; finishChar(c); render() }")   # a weak leader keeps 7 of 14
    lead = pg.evaluate("() => S.team.find(m => m.leader).name")
    check(f"{lead}'s Presence 20 keeps 7" in pg.text_content("#fqual"), "the followers' line names the leader, his Presence and the cap")
    check("7 more than his Presence keeps: 4 will drift away" in pg.inner_text("#fover"), "over the cap: a warning, with how many will leave")
    pg.click("#fcounts button[data-fmore='0']")
    check(pg.evaluate("() => S.fcounts[0][1]") == 9 and "8 more" in pg.inner_text("#fover"), "more can still be added past the cap, and the warning counts them")
    pg.click("#fcounts button[data-fless='0']")
    pg.click("#btn-season")
    log = pg.evaluate("() => S.xplog.join('\\n')")
    gone = re.findall(r"(deserted|gone home)", log.split("drift away:")[-1]) if "drift away" in log else []
    check(pg.evaluate("() => S.crew.length") == 10 and len(gone) == 4, f"End of season: half the 7 over, rounded up, leave (4), leaving 10 ({len(gone)} logged)")
    check(pg.evaluate("() => S.fcounts.reduce((t, [, n]) => t + n, 0)") == 10, "the counts drop with them, so a reroll does not bring them back")
    pg.click("#btn-season")
    check(pg.evaluate("() => S.crew.length") == 8, "the next season half the 3 still over, rounded up, leave (2)")
    pg.evaluate("() => { const c = S.team.find(m => m.leader); c.base.pres = 90 - c.stat_mods.pres; finishChar(c); render() }")
    check(pg.inner_text("#fover") == "", "under the cap: no warning")
    pg.click("#btn-season")
    check(pg.evaluate("() => S.crew.length") == 8 and "drift away" not in pg.evaluate("() => S.xplog.join(' ')"), "under the cap nobody leaves")
    pg.select_option("#sel-template", "own")
    check("keeps" not in pg.text_content("#fqual"), "Your own team has no template followers, so no cap")
    check(not errors, "no page errors: " + "; ".join(errors[:3]))
    br.close()
server.shutdown()
print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
sys.exit(1 if failures else 0)
