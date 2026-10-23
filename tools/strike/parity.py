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


class Recorded:
    """Dice that roll from a seeded source and keep what they gave, in order, for the other side to replay."""
    def __init__(self, rng):
        self.rng, self.taken = rng, []

    def randint(self, a, b):
        v = self.rng.randint(a, b)
        self.taken.append([a, b, v])
        return v


def attack(js_combat, atk_pct, roll):
    """The attack roll as strike.js makes it (no penalty): margin and critical, or a miss."""
    eff = max(0, atk_pct)
    hit = roll <= eff
    return hit, (eff - roll) if hit else None, hit and roll <= int(eff * js_combat["critical_fraction"])


def cases(d, b, n, seed):
    rng = random.Random(seed)
    tables = list(d.tables)
    kits = list(d.armor["kits"])
    zones = list(d.zones)
    out = []
    while len(out) < n:
        tid = rng.choice(tables)
        wid = rng.choice(available_weapons(d, tid))
        ltid = resolve_table(d, tid, wid)
        armour_ok = b["tables"][ltid]["armor"] == "allowed"
        kit = rng.choice(kits) if armour_ok and rng.random() < 0.8 else None
        aim = rng.choice(zones) if rng.random() < 0.35 else None
        gap = rng.random() < 0.3
        w = d.weapons[wid]
        blows = [m for m, v in w["mechanisms"].items() if v]
        blow = rng.choice(blows) if w.get("choose") and rng.random() < 0.5 else None
        atk_pct = atk_roll = None
        margin, critical = None, False
        if rng.random() < 0.7:                          # an attack roll that hits, so the margin decides
            atk_pct = rng.randint(20, 95)
            atk_roll = rng.randint(1, atk_pct)
            _, margin, critical = attack(b["combat"], atk_pct, atk_roll)
        sev_pick = None
        if margin is None and rng.random() < 0.2:      # the GM picks the severity
            sev_pick = rng.choice(["light", "serious", "critical"])
        dz = Recorded(random.Random(rng.random()))
        py = roll_hit(d, tid, wid, severity=sev_pick, rng=dz, aim=aim, kit=kit, margin=margin, critical=critical,
                      mechanism=blow, attack_roll=atk_roll, gap=gap)
        out.append({
            "table": tid, "ltable": ltid, "weapon": wid, "kit": kit or "none", "evidence": not armour_ok,
            "aim": aim or "", "gap": gap, "blow": blow or "", "atk": atk_pct, "atkRoll": atk_roll, "sev": sev_pick or "roll",
            "ranges": table_ranges(d, tid, wid),
            "aimRanges": aimed_ranges(d, tid, wid, aim) if aim else None,
            "dice": [v for _, _, v in dz.taken],
            "py": {"loc": py["location"], "mech": py["mechanism"], "sev": py["severity"], "graze": py["graze"],
                   "fx": py["effects"], "aim": py["aim"], "rolls": py["rolls"],
                   "armor": py["armor"] and {k: py["armor"][k] for k in ("material", "cover_roll", "covered", "gap_aimed", "steps", "from", "to")}},
        })
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
