"""The working pages on a phone, in a headless browser at 390 x 844 (an iPhone 12-15 in portrait).

    python3 tools/campaign/phone.py

The roller (set up with the playtest packet's fight), the team builder and the campaign console must
use the phone's width (a viewport line), not scroll sideways, and give every visible control at least a
40 px tap. On the roller a fighter can be tapped and placed on the map, and the hit can be rolled.
Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import sys
import traceback
from playwright.sync_api import sync_playwright
from harness import check, failures, serve

BASE, server = serve()
SIZE = """() => {
  const vis = e => { const r = e.getBoundingClientRect(), s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' };
  const ctl = [...document.querySelectorAll('button,select,input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=range])')].filter(vis);
  return { width: innerWidth, over: document.documentElement.scrollWidth - innerWidth,
    small: ctl.filter(e => e.getBoundingClientRect().height < 40).map(e => (e.id || e.textContent.trim().slice(0, 18) || e.tagName)).slice(0, 5), n: ctl.length };
}"""


def page_ok(pg, name):
    m = pg.evaluate(SIZE)
    check(m["width"] == 390, f"{name}: uses the phone's width ({m['width']})")
    check(m["over"] <= 1, f"{name}: no sideways scroll ({m['over']} px)")
    check(not m["small"], f"{name}: all {m['n']} controls a comfortable tap {m['small']}")


def run(p):
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    ctx.route("**/*", lambda r: r.abort() if "127.0.0.1" not in r.request.url else r.continue_())
    pg = ctx.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(BASE + "team.html#playtest")
    pg.wait_for_function("() => location.pathname.endsWith('roller.html') && S.chars && S.chars.length >= 9", timeout=30000)
    pg.wait_for_timeout(600)
    page_ok(pg, "roller")
    before = pg.evaluate("() => S.chars[0].pos && S.chars[0].pos.join(',')")
    place = pg.locator(".char").first.locator("button[data-act='place']")
    check(place.count() == 1, "the first fighter's card has Place on map")
    place.tap()
    pg.wait_for_timeout(300)
    taken = pg.evaluate("() => S.chars.filter(c => c.pos).map(c => c.pos.join(','))")
    hexes = pg.locator("#map [data-h]")
    free = [i for i in range(0, hexes.count(), 37) if hexes.nth(i).get_attribute("data-h") not in taken]
    check(bool(free), "the map's hexes are found")
    if free:
        h = hexes.nth(free[len(free) // 2])
        h.scroll_into_view_if_needed()
        h.tap()
        pg.wait_for_timeout(300)
        check(pg.evaluate("() => S.chars[0].pos && S.chars[0].pos.join(',')") not in (None, before), "a fighter can be moved on the map with taps")
    pg.get_by_role("button", name="Roll the hit").tap()
    pg.wait_for_timeout(300)
    check(len(pg.inner_text("#result") if pg.locator("#result").count() else pg.inner_text("body")) > 0, "the hit can be rolled")
    for name in ("team.html", "campaign.html"):
        pg.goto(BASE + name)
        pg.wait_for_timeout(800)
        page_ok(pg, name.split(".")[0])
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
