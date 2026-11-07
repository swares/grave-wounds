"""The playtest packet's fight in a headless browser: team.html#playtest sets up the four men against
Clifford's five on the roller, then the GM's script plays both sides, over several seeds, to check
the fight runs to an end and to see how it tends to go.

    python3 tools/campaign/playtest.py [fights]

Prints each fight's rounds, who won and how the four came out. The script stands in for the players,
so this tests the set-up and the odds, not the players' tactics. It also opens the printed packet and checks
the kit for playing on paper: the map, the counters (each fits a hex), the enemy's roster, the quick
reference and a blank sheet, on 27 numbered Letter pages; the sheets and the cut-ups have blank backs. Exits non-zero if the set-up is wrong or a fight stalls. Needs Python's playwright with Chromium and a built site.
"""
import sys
import traceback
from playwright.sync_api import sync_playwright
from harness import check, failures, serve

BASE, server = serve()
FIGHTS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
RUN = """seed => {
  let st = Math.max(1, seed * 7919 % 2147483647);
  DICE.randint = (a, b) => { st = (st * 16807) % 2147483647; return a + (st % (b - a + 1)) };
  S.gm.auto = false;
  for (const sd of new Set(S.chars.map(sideOf))) S.gm.sides[sd] = { ...gmSide(sd), ctl: "script", stance: "steady", quality: "regular" };
  let r = "acted", n = 0;
  while (r === "acted" && n++ < 6000) r = gmStep();
  const men = S.chars.map(c => ({ name: c.name, side: sideOf(c), blood: c.blood, wounds: c.wounds.length, state: c.state || "" }));
  return { r, n, round: S.round, msg: S.gmMsg, broken: S.broken, men };
}"""


def paper(br):
    """The packet as printed: the kit's pages are there and the counters fit the map's hexes."""
    pg = br.new_page()
    pg.goto(BASE + "playtest-packet.html")
    ids = pg.evaluate("() => [...document.querySelectorAll('h1[id]')].map(h => h.id)")
    check({"reference", "battlemap", "counters", "roster"} <= set(ids), f"the paper kit's pages are in the packet {ids[-4:]}")
    hexes = pg.evaluate("() => document.querySelectorAll('svg.mapsheet path').length")
    check(hexes == 12 * 17, f"the map has its 12 × 17 hexes ({hexes})")
    hexw = pg.evaluate("() => { const r = document.querySelector('svg.mapsheet path').getBoundingClientRect(); return r.width }")
    cw, ch = pg.evaluate("() => { const r = document.querySelector('.ctr').getBoundingClientRect(); return [r.width, r.height] }")
    side = hexw / 3 ** 0.5                         # a pointy-topped hex's straight sides
    check(abs(hexw - 0.55 * 96) < 1.5 and cw < hexw and ch <= side,
          f"printed true to size, a counter ({cw:.0f} × {ch:.0f} px) fits in a hex ({hexw:.0f} px across), no taller than its straight sides ({side:.0f} px)")
    men = pg.evaluate("() => [...document.querySelectorAll('.ctr.york, .ctr.clifford')].length")
    check(men == 9, f"a counter for each of the nine men ({men})")
    check(pg.evaluate("() => document.querySelectorAll('table.roster tbody tr').length") == 5, "the roster has Clifford's five")
    check(pg.evaluate("() => [...document.querySelectorAll('.sheet h1')].some(h => h.textContent.startsWith('Name:'))"), "a blank sheet to fill in")
    check(not pg.evaluate("() => /\\{\\{|@@/.test(document.body.innerHTML)"), "no value left unfilled")
    pdf = pg.pdf(format="Letter", print_background=True, prefer_css_page_size=True)
    n = pdf.count(b"/Type /Page") - pdf.count(b"/Type /Pages")
    check(n == 27, f"it prints on 27 Letter pages ({n})")
    nos = pg.evaluate("() => [...document.querySelectorAll('.pageno')].map(e => +e.textContent.replace('Page ', ''))")
    check(nos == list(range(1, n + 1)), f"each page is numbered, 1 to {n} ({nos[:3]} … {nos[-2:]})")
    kinds = """() => [...document.querySelectorAll('section.page')].map(s => s.classList.contains('blankpage') ? 'blank'
      : s.classList.contains('sheet') ? 'sheet' : (s.querySelector('h1[id]') || {}).id || '')"""
    pages = pg.evaluate(kinds)
    own = [i for i, k in enumerate(pages) if k in ("sheet", "reference", "battlemap", "counters")]
    check(len(own) == 8 and all(i % 2 == 0 and pages[i + 1] == "blank" for i in own),
          f"printed on both sides, the five sheets, the reference, the map and the counters each start a sheet with a blank back (pages {[i + 1 for i in own]})")
    check(pages.count("blank") == 8, f"and no other blank pages ({pages.count('blank')})")
    pg.close()


def run(p):
    br = p.chromium.launch()
    paper(br)
    wins, rounds, down = {}, [], 0
    for seed in range(1, FIGHTS + 1):
        ctx = br.new_context()
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(BASE + "team.html#playtest")
        pg.wait_for_function("() => location.pathname.endsWith('roller.html') && typeof S === 'object' && S.chars && S.chars.length >= 9", timeout=30000)
        c = pg.evaluate("() => S.chars.map(c => [c.name, sideOf(c)])")
        if seed == 1:
            check(len(c) == 9, f"nine men on the field ({len(c)})")
            check(sum(1 for _, s in c if s == "Clifford's men") == 5, "five of them Clifford's")
            check({"William of Ely", "Gilbert Cooper", "Edmund Miller", "Nicholas Fletcher"} <= {n for n, _ in c}, "the four men of the packet")
        r = pg.evaluate(RUN, seed)
        print(seed, r["r"], "round", r["round"], "|", (r["msg"] or "")[:70], "|", [(m["name"].split()[0], m["wounds"], m["state"]) for m in r["men"] if m["side"] != "Clifford's men"])
        check(r["r"] == "over", f"fight {seed} runs to an end")
        check(not errors, f"no page errors in fight {seed} {errors[:1]}")
        rounds.append(r["round"])
        ctx.close()
    print("rounds", rounds)
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
