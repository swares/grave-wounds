"""The working pages on a phone, in a headless browser at 390 x 844 (an iPhone 12-15 in portrait).

    python3 tools/campaign/phone.py

The roller (set up with the playtest packet's fight), the field and travel maps, the team builder and
the campaign console must
use the phone's width (a viewport line), not scroll sideways, and give every visible control at least a
40 px tap. On the roller a fighter can be tapped and placed on the map, and the hit can be rolled.
On the maps, + twice makes a hex a fingertip, Fit shows the whole width, two fingers spread zoom in, and,
zoomed in, a tap on the field map moves a unit. The field's order bar sits at the foot of the screen,
steps through the units, scrolls the map to them, and presses the page's own buttons.
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


FIELD = """() => { const s = [...document.querySelectorAll('select')].find(x => [...x.options].some(o => /Towton/.test(o.text)));
  s.value = [...s.options].find(o => /Towton/.test(o.text)).value; s.dispatchEvent(new Event('change', { bubbles: true }));
  [...document.querySelectorAll('button')].find(b => /Lay it out/.test(b.textContent)).click() }"""
HEXW = """() => { const p = [...document.querySelectorAll('#map svg [data-h]')].slice(0, 60).map(e => e.getBoundingClientRect().width).filter(w => w > 0).sort((a, b) => a - b);
  return Math.round(p[Math.floor(p.length / 2)] || 0) }"""
PINCH = """() => { const box = document.querySelector('#map'), r = box.getBoundingClientRect(), cx = r.left + r.width / 2, cy = r.top + Math.min(r.height, 300) / 2;
  const T = (id, x) => new Touch({ identifier: id, target: box, clientX: x, clientY: cy });
  const ev = (type, a, b) => box.dispatchEvent(new TouchEvent(type, { touches: [T(1, a), T(2, b)], targetTouches: [T(1, a), T(2, b)], changedTouches: [T(1, a), T(2, b)], bubbles: true, cancelable: true }));
  ev('touchstart', cx - 30, cx + 30); ev('touchmove', cx - 60, cx + 60); ev('touchmove', cx - 90, cx + 90);
  box.dispatchEvent(new TouchEvent('touchend', { touches: [], changedTouches: [T(1, cx - 90)], bubbles: true })) }"""


def bar_checks(pg):
    """The field's order bar: on the screen at the foot, its buttons press the page's own."""
    bar = pg.locator("#orderbar")
    check(bar.is_visible(), "field: the order bar shows on a phone")
    box = bar.bounding_box() or {"y": 0, "height": 0}
    check(abs(box["y"] + box["height"] - 844) < 2, f"field: and sits at the foot of the screen ({box})")
    was = pg.evaluate("() => S.sel")
    pg.locator("#ob-next-unit").tap()
    pg.wait_for_timeout(300)
    now = pg.evaluate("() => S.sel")
    check(now != was and pg.locator("#ob-name").inner_text().endswith(pg.evaluate("() => selUnit().name")), f"field: ▶ selects the next unit ({was} to {now}), named in the bar")
    inbox = """() => { const b = $('#map').getBoundingClientRect(), [hx, hy] = xy(selUnit().pos), p = new DOMPoint(hx, hy).matrixTransform($('#map svg').getScreenCTM());
      return p.x > b.left && p.x < b.right && p.y > b.top && p.y < b.bottom && p.y < innerHeight - $('#orderbar').offsetHeight }"""
    check(pg.evaluate(inbox), "field: and the zoomed map scrolls to it")
    f0 = pg.evaluate("() => { S.msg = ''; render(); return selUnit().facing }")
    pg.locator("#orderbar [data-for='btn-left']").tap()
    pg.wait_for_timeout(200)
    check(pg.evaluate("() => selUnit().facing") != f0 or pg.evaluate("() => !!S.msg"), "field: the bar's Turn left turns it, or says why not")
    check(pg.locator("#ob-phase").inner_text() == pg.locator("#btn-next").inner_text(), "field: the bar's last button is the page's Start the battle / Next")
    pg.locator("#ob-phase").tap()
    pg.wait_for_timeout(600)
    check(pg.evaluate("() => S.phase") != "setup" and pg.locator("#ob-phase").inner_text() == pg.locator("#btn-next").inner_text(), f"field: and pressing it starts the battle ({pg.locator('#ob-phase').inner_text()})")
    pg.locator("#ob-more").tap()
    pg.wait_for_timeout(300)
    check(pg.evaluate("() => Math.abs($('#h-sel').getBoundingClientRect().top) < 60"), "field: More goes to the selected unit's full orders")
    pg.set_viewport_size({"width": 1280, "height": 900})
    pg.wait_for_timeout(200)
    check(not bar.is_visible(), "field: on a desktop the bar is not shown")
    pg.set_viewport_size({"width": 390, "height": 844})


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
    for name, setup in (("field.html", FIELD), ("travel.html", "")):
        pg.goto(BASE + name)
        pg.wait_for_timeout(900)
        if setup:
            pg.evaluate(setup)
            pg.wait_for_timeout(1200)
        page = name.split(".")[0]
        page_ok(pg, page)
        hx = pg.evaluate(HEXW)
        pg.locator(".zoombar button[data-z='in']").first.tap()
        pg.locator(".zoombar button[data-z='in']").first.tap()
        pg.wait_for_timeout(200)
        big = pg.evaluate(HEXW)
        check(big >= 40, f"{page}: + twice makes a hex a fingertip ({hx} to {big} px)")
        pg.locator(".zoombar button[data-z='fit']").first.tap()
        pg.wait_for_timeout(200)
        check(pg.evaluate("() => { const b = document.querySelector('#map'), s = b.querySelector('svg'); return s.getBoundingClientRect().width <= b.clientWidth + 1 }"), f"{page}: Fit shows the whole width")
        f0 = pg.evaluate(HEXW)
        pg.evaluate(PINCH)
        pg.wait_for_timeout(200)
        check(pg.evaluate(HEXW) > f0 * 1.8, f"{page}: two fingers spread zoom in ({f0} to {pg.evaluate(HEXW)} px)")
    pg.goto(BASE + "field.html")
    pg.wait_for_timeout(900)
    pg.evaluate(FIELD)
    pg.wait_for_timeout(1200)
    for _ in range(2):
        pg.locator(".zoombar button[data-z='in']").first.tap()
    pg.evaluate("() => { const u = S.units.find(x => x.pos); S.sel = u.id; S.tool = 'unit'; window.__was = u.pos.join(',') }")
    target = pg.evaluate("""() => { const u = S.units.find(x => x.id === S.sel), occ = occupancy(S.units);
      for (const d of [3, -3, 4, -4, 5, -5]) for (const e of [0, 1, -1, 2, -2]) {
        const h = [u.pos[0] + e, u.pos[1] + d], k = h.join(',');
        if (occ[hk(h)] === undefined && document.querySelector(`#map [data-h="${k}"]`)) return k }
      return null }""")
    if target:
        h = pg.locator(f"#map [data-h='{target}']").first
        h.scroll_into_view_if_needed()
        pg.evaluate("() => { S.msg = ''; window.__seen = null; const m = $('#map'); m.addEventListener('click', e => { const p = e.target.closest('.hx'); window.__seen = p && p.dataset.h }, { capture: true, once: true }) }")
        h.tap()
        pg.wait_for_timeout(300)
        check(pg.evaluate("() => window.__seen") == target, f"field: zoomed in, a tap lands on the hex under the finger ({target})")
        check(pg.evaluate("() => S.units.find(x => x.id === S.sel).pos.join(',') !== window.__was || !!S.msg"), "field: and the selected unit is moved, or told why not")
    else:
        check(False, "field: a hex next to the unit is found")
    bar_checks(pg)
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
