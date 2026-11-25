"""A print-and-play module's fight in a headless browser: team.html#<hash> sets up the module's four men
against its enemy on the roller, then the GM's script plays both sides, over several seeds, to check the fight
runs to an end and to see how it tends to go.

    python3 tools/campaign/modulefight.py baggage|escalade [fights]

Prints each fight's rounds and who was left standing, and how often the four held. The script stands in for
the players and fights to a finish. It knows nothing of the baggage's plunder rule on paper; the escalade's map,
ladders, night and fires are laid on the roller (ESCALADE.field) and the script fights on them. Exits non-zero
if the set-up is wrong or a fight stalls. Needs Python's playwright with Chromium and a built site.
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
                 "foes": 3, "special": ("Sergent", "veteran")},
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
    if NAME == "escalade":                            # the module's map: three ladders, the wall's face, the fires, a dark night, the four in the ditch
        f = pg.evaluate("() => ({ladders: Object.keys(S.ladders || {}).length, face: Object.values(S.ground.kinds).filter(k => k === 'wall_face').length,"
                        " lit: (S.lit || []).length, light: S.weather.light, four: S.chars.filter(c => sideOf(c) !== ESCALADE.side).map(c => c.pos[1])})")
        check(f["ladders"] == 3 and f["face"] == 9, f"three ladders in the wall's face ({f['ladders']}, {f['face']})")
        check(f["lit"] == 14 and f["light"] == "night", f"two fires on a dark night ({f['lit']} lit, {f['light']})")
        check(all(r > 10 for r in f["four"]), f"the four start in the ditch ({f['four']})")
        # The ladder rules on a copy of the fight (the page is set up afresh for each fight): onto a ladder takes
        # the whole move and only from next to it; off it onto the parapet is a step; a failed stop check on it
        # is a fall to its foot, fallen for two rounds, with a check again on landing.
        L = pg.evaluate("""() => {
          const keep = structuredClone(S), c = S.chars.find(x => x.name === "Donald Murray");
          S.turn = c.id; S.tm = null; c.pos = [3, 11];
          const foot = turnInfo().reach, past = [...foot.keys()].filter(k => +k.split(",")[1] < 10);
          c.pos = [3, 12]; S.tm = null;
          const back = turnInfo().reach;
          c.pos = [3, 10]; S.tm = null;
          const top = turnInfo().reach;
          S.weapon = "musket_smoothbore";
          const dark = [darkOnAttack({ penalty: 0, notes: [] }, 5, c, [2, 5]).penalty, darkOnAttack({ penalty: 0, notes: [] }, 5, c, [5, 5]).penalty];
          const line = stopResult(c, { passed: false, roll: 99, target: 10, fail_by: 89, state: "stunned", rounds: 2 }, "", () => ({ passed: true, roll: 5, target: 50 }));
          const out = { onto: foot.get("3,10"), past, dark, fromBack: back.has("3,10"), up: top.get("3,9") || top.get("2,9"), face: foot.has("2,10"),
                        fell: c.pos.join(","), state: c.state, line };
          for (const k of Object.keys(S)) delete S[k];
          Object.assign(S, keep);
          return out;
        }""")
        check(L["onto"] == 4 and not L["fromBack"] and not L["past"], f"onto a ladder: the whole advance, only from next to it, and no further ({L['onto']}, {L['fromBack']}, {L['past'][:3]})")
        check(L["up"] == 1 and not L["face"], f"off the ladder onto the parapet in a step; no one on the wall's face ({L['up']}, {L['face']})")
        check(L["dark"] == [0, 20], f"the dark night's -20, but not at a man in the firelight ({L['dark']})")
        check(L["fell"] == "3,11" and (L["state"] or {}).get("id") == "fallen" and (L["state"] or {}).get("rounds") == 2 and "on landing" in L["line"],
              f"a failed stop check on the ladder: a fall to its foot ({L['fell']}, {L['state']})")


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
