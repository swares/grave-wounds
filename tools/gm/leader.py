"""A side's leader down calls a morale check: the roller's moraleCheck against gravewounds/combat.py
morale_check.

    python3 tools/gm/leader.py

Eight fighters, none to four down, the leader up or down, gone down this round or not: the page's
moraleCheck (taken from dist/roller.html and run in Node with the data) and the Python agree on
every case. Under a quarter down there is no check unless the leader went down this round; then
the side checks, at the leader-down penalty. Needs Python 3 with PyYAML, Node and a built
dist/roller.html. Exits non-zero on any failure.
"""
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from gravewounds import load                      # noqa: E402
from gravewounds.combat import morale_check       # noqa: E402

failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


d = load(ROOT / "data")
CASES = []
for down in (0, 1, 2, 4):
    for lead_down in (False, True):
        for fell in (False, True):
            fs = [{"nerve": 50 + i, "down": i < down, "leader": i == 0, "pres": 60} for i in range(8)]
            if lead_down:
                fs[0]["down"] = True
            CASES.append((fs, 55, fell and fs[0]["down"]))

src = (ROOT / "dist" / "roller.html").read_text(encoding="utf-8")
fn = re.search(r"function moraleCheck\(.*?\n\}", src, re.S).group(0)
C = d.wounds["combat"]
js = f"const CMB = {json.dumps({'morale': C['morale']})}, CHR = {json.dumps(C['characteristics'])};\n{fn}\n" \
     f"console.log(JSON.stringify({json.dumps(CASES)}.map(([fs, roll, fell]) => moraleCheck(fs, roll, fell))));"
page = json.loads(subprocess.run(["node", "-e", js], capture_output=True, text=True, check=True).stdout)
py = [morale_check(d, fs, roll, fell) for fs, roll, fell in CASES]
check(page == py, f"the page and the Python agree on all {len(CASES)} cases")
one = [{"nerve": 50, "down": i == 0, "leader": i == 0, "pres": 50} for i in range(8)]
check(morale_check(d, one, 50) is None, "one of eight down, the leader, and not this round: no check")
m = morale_check(d, one, 50, True)
check(m is not None and m["target"] == 50 - C["morale"]["leader_down"], f"he went down this round: the side checks, at -{C['morale']['leader_down']} ({m})")

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
sys.exit(1 if failures else 0)
