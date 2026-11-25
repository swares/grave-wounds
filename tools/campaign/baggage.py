"""The king's baggage module's fight in a headless browser: team.html#baggage sets up the four men (the
retinue rolled with seed 1415) against Ysembart's raiders on the roller, then the GM's script plays both
sides, over several seeds, to check the fight runs to an end and to see how it tends to go.

    python3 tools/campaign/baggage.py [fights]

Prints each fight's rounds and who was left standing, and how often the four held. The script stands in for
the players and fights the raiders to a finish (it knows nothing of the module's plunder rule), so this tests
the set-up and the odds of a straight fight. Exits non-zero if the set-up is wrong or a fight stalls. Needs
Python's playwright with Chromium and a built site.
"""
import sys
import traceback
from pathlib import Path
from playwright.sync_api import sync_playwright
from harness import check, failures, serve

BASE, server = serve()
FIGHTS = int(sys.argv[1]) if len(sys.argv) > 1 else 3
FOE = "Ysembart's raiders"
FOUR = {"Robert Hayward", "Walter Carter", "Ralph Carter", "Henry of Ely"}
# The script playing both sides to the end, as tools/campaign/playtest.py plays the packet's fight.
RUN = Path(__file__).with_name("playtest.py").read_text(encoding="utf-8").split('RUN = """', 1)[1].split('"""', 1)[0]


def run(p):
    br = p.chromium.launch()
    held = 0
    for seed in range(1, FIGHTS + 1):
        ctx = br.new_context()
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(BASE + "team.html#baggage")
        pg.wait_for_function("() => location.pathname.endsWith('roller.html') && typeof S === 'object' && S.chars && S.chars.length >= 10", timeout=30000)
        c = pg.evaluate("() => S.chars.map(c => [c.name, sideOf(c), c.quality || ''])")
        if seed == 1:
            check(len(c) == 10, f"ten men on the field ({len(c)})")
            check(sum(1 for _, s, _ in c if s == FOE) == 6, "six of them raiders")
            check(FOUR <= {n for n, _, _ in c}, "the four men of the module")
            check({n: q for n, s, q in c if s == FOE}.get("Man-at-arms") == "veteran", "each raider at his own quality (the man-at-arms a veteran)")
        r = pg.evaluate(RUN, seed)
        won = not (r["msg"] or "").startswith(FOE)       # the raiders left standing, or no one: the four held
        held += won
        print(seed, r["r"], "round", r["round"], "| four held" if won else "| raiders held", "|", (r["msg"] or "")[:60], "|", [(m["name"].split()[0], m["wounds"], m["state"]) for m in r["men"] if m["side"] != FOE])
        check(r["r"] == "over", f"fight {seed} runs to an end")
        check(not errors, f"no page errors in fight {seed} {errors[:1]}")
        ctx.close()
    print(f"the four held in {held} of {FIGHTS}")
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
