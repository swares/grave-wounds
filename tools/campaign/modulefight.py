"""A print-and-play module's fight in a headless browser: team.html#<hash> sets up the module's four men
against its enemy on the roller, then the GM's script plays both sides, over several seeds, to check the fight
runs to an end and to see how it tends to go.

    python3 tools/campaign/modulefight.py baggage|escalade [fights]

Prints each fight's rounds and who was left standing, and how often the four held. The script stands in for
the players and fights to a finish (it knows nothing of a module's own rules on paper: the baggage's plunder,
the escalade's ladders and night), so this tests the set-up and the odds of a straight fight. Exits non-zero if
the set-up is wrong or a fight stalls. Needs Python's playwright with Chromium and a built site.
"""
import sys
import traceback
from pathlib import Path
from playwright.sync_api import sync_playwright
from harness import check, failures, serve

# Each module's fight: its enemy side, the four, how many enemies, and the one fighting at his own quality.
MODULES = {
    "baggage": {"foe": "Ysembart's raiders", "four": {"Robert Hayward", "Walter Carter", "Ralph Carter", "Henry of Ely"},
                "foes": 6, "special": ("Man-at-arms", "veteran")},
    "escalade": {"foe": "The French on the rampart", "four": {"William Green", "Donald Murray", "John Morris", "George Costello"},
                 "foes": 4, "special": ("Sergent", "veteran")},
}
NAME = sys.argv[1] if len(sys.argv) > 1 else "baggage"
MOD = MODULES[NAME]
FIGHTS = int(sys.argv[2]) if len(sys.argv) > 2 else 3
BASE, server = serve()
# The script playing both sides to the end, as tools/campaign/playtest.py plays the packet's fight.
RUN = Path(__file__).with_name("playtest.py").read_text(encoding="utf-8").split('RUN = """', 1)[1].split('"""', 1)[0]


def set_up(pg, seed):
    """The module's fight on the roller; on the first, check its men."""
    n = 4 + MOD["foes"]
    pg.goto(BASE + f"team.html#{NAME}")
    pg.wait_for_function(f"() => location.pathname.endsWith('roller.html') && typeof S === 'object' && S.chars && S.chars.length >= {n}", timeout=30000)
    if seed > 1:
        return
    c = pg.evaluate("() => S.chars.map(c => [c.name, sideOf(c), c.quality || ''])")
    who, q = MOD["special"]
    check(len(c) == n, f"{n} men on the field ({len(c)})")
    check(sum(1 for _, s, _ in c if s == MOD["foe"]) == MOD["foes"], f"{MOD['foes']} of them the enemy")
    check(MOD["four"] <= {x for x, _, _ in c}, "the four men of the module")
    check({x: y for x, s, y in c if s == MOD["foe"]}.get(who) == q, f"each enemy at his own quality ({who}: {q})")


def run(p):
    br = p.chromium.launch()
    held = 0
    for seed in range(1, FIGHTS + 1):
        ctx = br.new_context()
        pg = ctx.new_page()
        errors = []
        pg.on("pageerror", lambda e, errs=errors: errs.append(str(e)))
        set_up(pg, seed)
        r = pg.evaluate(RUN, seed)
        won = not (r["msg"] or "").startswith(MOD["foe"])    # the enemy left standing, or no one: the four held
        held += won
        print(seed, r["r"], "round", r["round"], "| four held" if won else "| enemy held", "|", (r["msg"] or "")[:60], "|",
              [(m["name"].split()[0], m["wounds"], m["state"]) for m in r["men"] if m["side"] != MOD["foe"]])
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
