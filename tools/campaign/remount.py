"""Horses on the travel map, in a headless browser, served as the site is.

    python3 tools/campaign/remount.py

On the Bull Run map: a hungry force loses its horses four times as fast (events.yaml conditions);
a mounted force its army feeds, short of horses at its depot, is made up to one horse a man by
Refill at the depot and the log counts the remounts; one with enough draws none. Needs Python's
playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import sys
from playwright.sync_api import sync_playwright
from harness import check, failures, serve

BASE, server = serve()

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1300, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE + "travel.html"); pg.evaluate("() => localStorage.clear()"); pg.reload()
    pg.select_option("#sel-map", "bull-run-1861")
    r = pg.evaluate("""() => { const era = 'civil_war', E = DATA.events;
      return [evRate(E, era, 'horses', 'march', []), evRate(E, era, 'horses', 'march', ['hungry'])] }""")
    check(abs(r[1] - 4 * r[0]) < 1e-12, f"hungry, horses die four times as fast ({r[0]} to {r[1]})")
    f = pg.evaluate("""() => { const f = S.forces[S.mapId].find(x => x.type === 'mounted' && fedByArmy(x) && depotHere(x));
      if (!f) return null; f.horses = Math.floor(f.men / 2); refillForce(f, 'depot');
      return { men: f.men, horses: f.horses, log: f.log[0] } }""")
    check(f is not None, "the map has a mounted force at its depot")
    if f:
        check(f["horses"] == f["men"], f"refilled at its depot, it is made up to a horse a man ({f['horses']} of {f['men']})")
        check("remount" in f["log"], f"the log counts the remounts: {f['log']}")
        again = pg.evaluate("""() => { const f = S.forces[S.mapId].find(x => x.type === 'mounted' && fedByArmy(x) && depotHere(x));
          f.horses = f.men + 5; refillForce(f, 'depot'); return { horses: f.horses, men: f.men, log: f.log[0] } }""")
        check(again["horses"] == again["men"] + 5 and "remount" not in again["log"], "a force with spare horses keeps them and draws none")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()
server.shutdown()
print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
sys.exit(1 if failures else 0)
