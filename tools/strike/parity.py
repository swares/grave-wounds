"""The roller's strike (templates/strike.js) against gravewounds.engine.roll_hit, on the same dice.

    python3 tools/strike/parity.py [cases] [seed]

Makes `cases` random strikes (table, weapon, armour kit, aim, gap, a declared blow, an attack roll
or none), plays each through Python's roll_hit with scripted dice, writes the data bundle and the
cases to tools/strike/.cache/, then runs tools/strike/test.js on them: the same strikes through the
JavaScript, each wound compared field by field, plus the unit tests of the attack phase and the
event log. Needs Python 3 with PyYAML and Node; exits non-zero on any difference.
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from build import bundle                                     # noqa: E402  the bundle the roller is built with
from gravewounds import load                                 # noqa: E402
from gravewounds.engine import roll_hit, table_ranges, aimed_ranges   # noqa: E402
from gravewounds.model import available_weapons, resolve_table        # noqa: E402

CACHE = Path(__file__).parent / ".cache"


class TestDice:
    """The test's own randomness: seeded, so a run can be repeated, and never used for anything secret.
    Every random choice the test makes goes through here."""
    def __init__(self, seed):
        self._rng = random.Random(seed)   # NOSONAR: test data that must repeat from its seed, not a security use

    def int(self, a, b):
        return self._rng.randint(a, b)    # NOSONAR: as above

    def pick(self, items):
        return items[self.int(0, len(items) - 1)]

    def chance(self, p):
        return self.int(1, 10000) <= p * 10000


class Recorded:
    """Dice that roll from the test's dice and keep what they gave, in order, for the JavaScript to replay."""
    def __init__(self, source):
        self.source, self.taken = source, []

    def randint(self, a, b):
        v = self.source.int(a, b)
        self.taken.append(v)
        return v


def attack(js_combat, atk_pct, roll):
    """The attack roll as strike.js makes it (no penalty): margin and critical, or a miss."""
    eff = max(0, atk_pct)
    hit = roll <= eff
    return hit, (eff - roll) if hit else None, hit and roll <= int(eff * js_combat["critical_fraction"])


def declared(d, b, td):
    """A random strike as the page would declare it: table, weapon, armour, aim, gap and a chosen blow."""
    tid = td.pick(list(d.tables))
    wid = td.pick(available_weapons(d, tid))
    ltid = resolve_table(d, tid, wid)
    armour_ok = b["tables"][ltid]["armor"] == "allowed"
    w = d.weapons[wid]
    blows = [m for m, v in w["mechanisms"].items() if v]
    return {
        "table": tid, "ltable": ltid, "weapon": wid, "evidence": not armour_ok,
        "kit": td.pick(list(d.armor["kits"])) if armour_ok and td.chance(0.8) else None,
        "aim": td.pick(list(d.zones)) if td.chance(0.35) else None,
        "gap": td.chance(0.3),
        "blow": td.pick(blows) if w.get("choose") and td.chance(0.5) else None,
    }


def attack_and_severity(b, td):
    """An attack roll that hits (so the margin decides the severity), or none, perhaps with the GM's pick."""
    out = {"atk": None, "atkRoll": None, "margin": None, "critical": False, "sev": None}
    if td.chance(0.7):
        out["atk"] = td.int(20, 95)
        out["atkRoll"] = td.int(1, out["atk"])
        _, out["margin"], out["critical"] = attack(b["combat"], out["atk"], out["atkRoll"])
    elif td.chance(0.2):
        out["sev"] = td.pick(["light", "serious", "critical"])
    return out


def py_result(py):
    armour = py["armor"] and {k: py["armor"][k] for k in ("material", "cover_roll", "covered", "gap_aimed", "steps", "from", "to")}
    return {"loc": py["location"], "mech": py["mechanism"], "sev": py["severity"], "graze": py["graze"],
            "fx": py["effects"], "aim": py["aim"], "rolls": py["rolls"], "armor": armour}


def cases(d, b, n, seed):
    td, out = TestDice(seed), []
    for _ in range(n):
        c, a = declared(d, b, td), attack_and_severity(b, td)
        dz = Recorded(td)
        py = roll_hit(d, c["table"], c["weapon"], severity=a["sev"], rng=dz, aim=c["aim"], kit=c["kit"], margin=a["margin"],
                      critical=a["critical"], mechanism=c["blow"], attack_roll=a["atkRoll"], gap=c["gap"])
        out.append({**c, "kit": c["kit"] or "none", "aim": c["aim"] or "", "blow": c["blow"] or "",
                    "atk": a["atk"], "atkRoll": a["atkRoll"], "sev": a["sev"] or "roll",
                    "ranges": table_ranges(d, c["table"], c["weapon"]),
                    "aimRanges": aimed_ranges(d, c["table"], c["weapon"], c["aim"]) if c["aim"] else None,
                    "dice": dz.taken, "py": py_result(py)})
    return out


def main(argv) -> int:
    n = int(argv[1]) if len(argv) > 1 else 2000
    seed = int(argv[2]) if len(argv) > 2 else 1
    d = load()
    b = bundle(d)
    CACHE.mkdir(exist_ok=True)
    (CACHE / "data.json").write_text(json.dumps(b), encoding="utf-8")
    (CACHE / "cases.json").write_text(json.dumps(cases(d, b, n, seed)), encoding="utf-8")
    return subprocess.call(["node", str(Path(__file__).parent / "test.js"), str(CACHE / "data.json"), str(CACHE / "cases.json")])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
