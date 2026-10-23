"""The roller's GM script against itself, in the built page, in a headless browser.

    python3 tools/gm/selfplay.py [page] [seeds] [men a side]

For a spread of the roller's tables, two sides of each table's example fighters, both played by the
GM's script, on seeded dice, cautious, steady and reckless: does every fight run to an end (one
side standing, or no one left fighting), and how did it go? Prints a line a fight, and exits
non-zero if any fight stalls. Needs Python's playwright with Chromium (requirements.txt) and a
built page (python3 build.py). The brain's choices are design guesses; this catches a script that
never closes, never strikes or loops, not one that fights unlike the records.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
URL = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "dist" / "roller.html").resolve().as_uri()
SEEDS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
SIDE = int(sys.argv[3]) if len(sys.argv) > 3 else 3

SETUP = """([seed, n, stance]) => {
  let st = Math.max(1, seed % 2147483647);
  DICE.randint = (a, b) => { st = (st * 16807) % 2147483647; return a + (st % (b - a + 1)) };
  const conf = DATA.conflicts[DATA.tables[S.table].battle] || {}, ex = conf.examples || [];
  if (ex.length < 1) return null;
  const a = ex[0], b = ex[ex.length - 1];
  S.chars = []; S.events = []; S.round = 1; S.turn = null; S.tm = null; S.free = []; S.broken = {}; S.log = []; S.pending = [];
  for (let i = 0; i < n; i++){
    S.chars.push(newChar(`A${i + 1}`, a.kit, a.weapon, {}, "Reds"));
    S.chars.push(newChar(`B${i + 1}`, b.kit, b.weapon, {}, "Blues"));
  }
  gmStart();
  for (const sd of Object.keys(S.gm.sides)) S.gm.sides[sd] = { ...S.gm.sides[sd], ctl: "script", stance };
  S.gm.auto = false;
  renderChars();
  return { a: a.name + " (" + a.weapon + ", " + a.kit + ")", b: b.name + " (" + b.weapon + ", " + b.kit + ")" };
}"""
RESULT = """() => ({ won: winningSide(), round: S.round, steps: GMQ.steps, running: GMQ.running, msg: S.gmMsg,
  types: S.events.reduce((m, e) => (m[e.type] = (m[e.type] || 0) + 1, m), {}),
  outcomes: S.events.filter(e => e.type === 'strike').reduce((m, e) => (m[e.data.outcome] = (m[e.data.outcome] || 0) + 1, m), {}),
  down: S.chars.filter(isOut).map(c => c.name), why: S.events.filter(e => e.type === 'turn').reduce((m, e) => (m[e.data.why] = (m[e.data.why] || 0) + 1, m), {}) })"""

with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1400, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(URL); pg.evaluate("() => localStorage.clear()"); pg.reload()
    tables = pg.evaluate("() => Object.keys(DATA.tables).filter(t => (DATA.conflicts[DATA.tables[t].battle] || {}).examples)")
    picks = tables[::max(1, len(tables) // 8)][:8]
    ended = total = 0
    stalled = []
    for tid in picks:
        for seed in range(1, SEEDS + 1):
            for stance in ["steady", "cautious", "reckless"][: (1 if seed > 1 else 3)]:
                pg.goto(URL); pg.evaluate("() => localStorage.clear()"); pg.reload()
                pg.evaluate("t => switchTable(t)", tid)
                who = pg.evaluate(SETUP, [seed * 101, SIDE, stance])
                if not who: continue
                pg.evaluate("() => gmPlay()")
                pg.wait_for_function("() => !GMQ.running", timeout=180000)
                r = pg.evaluate(RESULT)
                over = bool(r["won"]) or r["msg"].startswith("No one is left")
                total += 1; ended += over
                if not over: stalled.append(f"{tid} s{seed} {stance}")
                print(f"{tid} s{seed} {stance}: {r['won'] or 'no one'} standing, round {r['round']}, {r['steps']} steps, strikes {r['outcomes']}, turns {r['why']}" + ("" if over else f"  STALLED: {r['msg']}"))
    print(f"{ended} of {total} fights ran to an end; page errors: {errors[:3]}")
    br.close()
    sys.exit(1 if stalled or errors else 0)
