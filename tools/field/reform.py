"""Re-forming broken units (units.yaml morale.reform): Python against the built field page, on the same
units and dice.

    python3 tools/field/reform.py

A broken unit that lost no men, far from the enemy, checks Nerve less the penalty: on a battlefield that
turns re-forming on (reform: true), or on any battlefield with its leader up (reform.leader), his morale
bonus added. Plays 32 cases (with and without a reform battlefield; no leader, a leader hero up or down, a
unit marked with its leader up; four rolls) through gravewounds.units._reform_all and the page's
reformAll, checks they agree and that each comes out as the rule says. Needs Python 3 with PyYAML and
Node, and dist/field.html built; exits non-zero on any difference.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gravewounds import load                                 # noqa: E402
from gravewounds import units as U                           # noqa: E402


class Dice:
    """Scripted dice: each roll the case gives, in turn."""
    def __init__(self, rolls):
        self.rolls = list(rolls)

    def randint(self, lo, hi):
        return self.rolls.pop(0)


def unit(name, side, pos, state, heroes=None, leader=None):
    u = {"name": name, "side": side, "men": 300, "start": 400, "quality": "regular", "weapon": "musket_smoothbore",
         "kit": "none", "formation": "close", "width": 3, "pos": pos, "facing": 1, "state": state}
    if heroes is not None:
        u["heroes"] = heroes
    if leader:
        u["leader"] = leader
    return u


def cases():
    out = []
    for field in ({"reform": True}, {}):
        for lead in (None, "hero-up", "hero-down", "mark-up"):
            for roll in (25, 30, 45, 60):
                heroes = [{"id": 1, "name": "A leader", "leader": True, "state": "up" if lead == "hero-up" else "down", "rank_bonus": 6}] \
                    if lead in ("hero-up", "hero-down") else None
                us = [unit("Broken", "A", [10, 30], "broken", heroes, "up" if lead == "mark-up" else None), unit("Enemy", "B", [10, 5], "steady")]
                out.append({"field": field, "units": us, "roll": roll, "lead": lead})
    return out


def expected(d, c):
    """What the rule says: (re-forms, target or None)."""
    R, M = d.units["morale"]["reform"], d.units["morale"]["mods"]
    led = c["lead"] in ("hero-up", "mark-up") and R.get("leader")
    if not c["field"].get("reform") and not led:
        return False, None
    target = d.units["quality"]["regular"]["nerve"] - R["penalty"] + ((M["leader"] + (6 if c["lead"] == "hero-up" else 0)) if led else 0)
    return c["roll"] <= target, target


def main():
    d, cs = load(), cases()
    py = []
    for c in cs:
        us = json.loads(json.dumps(c["units"]))
        log = U._reform_all(d, us, [0, 0], Dice([c["roll"]]), c["field"])
        py.append([log, us[0]["state"]])
    page = (ROOT / "dist" / "field.html").as_posix()
    js_src = f"""
const {{ load }} = require({json.dumps((ROOT / 'tools' / 'selfplay' / 'page.js').as_posix())});
const {{ api }} = load({json.dumps(page)}, ["reformAll"]);
const cases = {json.dumps(cs)};
console.log(JSON.stringify(cases.map(c => {{ const us = JSON.parse(JSON.stringify(c.units)), r = [c.roll];
  const log = api.reformAll(us, [0, 0], {{ randint: () => r.shift() }}, c.field); return [log, us[0].state] }})));
"""
    js = json.loads(subprocess.run(["node", "-e", js_src], capture_output=True, text=True, check=True).stdout)
    bad = 0
    for c, p, j in zip(cs, py, js):
        reforms, target = expected(d, c)
        got = (p[1] == "shaken", p[0][0]["target"] if p[0] else None)
        if p != j or got != (reforms, target):
            bad += 1
            print(f"FAIL reform={bool(c['field'])} leader={c['lead']} roll={c['roll']}: python {p} page {j}, expected {(reforms, target)}")
    print(f"re-forming: {len(cs) - bad} of {len(cs)} cases as the rule says, Python and the page agreeing")
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
