"""On the roller, a side whose leader falls checks morale that round, and not again for him.

    python3 tools/gm/leaderpage.py

Eight men of side A with their captain down (and the round's morale die 1, so they hold): the
round's checks have A check; the next round's do not, for the same fall. Needs Python's
playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


with sync_playwright() as p:
    br = p.chromium.launch()
    pg = br.new_page()
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto((ROOT / "dist" / "roller.html").as_uri())
    rounds = pg.evaluate("""() => {
      S.broken = {}; S.leadersFell = {};
      S.chars = [newChar("Captain", "none", null, {}, "A"), ...[1, 2, 3, 4, 5, 6, 7].map(i => newChar("Man " + i, "none", null, {}, "A")), newChar("Foe", "none", null, {}, "B"), newChar("Foe 2", "none", null, {}, "B")];
      S.chars[0].leader = true;
      S.chars[0].state = { id: "out", rounds: null };
      document.querySelector("#in-morale").value = "1";   // it holds, so the second round is not skipped for a broken side
      const first = moraleChecks().filter(l => l.startsWith("Morale, A")).length;
      const second = moraleChecks().filter(l => l.startsWith("Morale, A")).length;
      return [first, second, !!S.broken.A];
    }""")
    check(rounds == [1, 0, False], f"on the roller a side whose leader falls checks that round, and not again for it ({rounds})")
    check(not errors, "no page errors" + ("" if not errors else ": " + "; ".join(errors)))
    br.close()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
