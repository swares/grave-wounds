"""The playtest packet's fight in a headless browser: team.html#playtest sets up the four men against
Clifford's five on the roller, then the GM's script plays both sides, over several seeds, to check
the fight runs to an end and to see how it tends to go.

    python3 tools/campaign/playtest.py [fights]

Prints each fight's rounds, who won and how the four came out. The script stands in for the players,
so this tests the set-up and the odds, not the players' tactics. Exits non-zero if the set-up is wrong
or a fight stalls. Needs Python's playwright with Chromium and a built site.
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


def run(p):
    br = p.chromium.launch()
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
