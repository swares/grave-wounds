"""Quick-play's rates: the page's quickRates against gravewounds.units._quick_rates, and both against
the per-blow rules; and quick-play shellfire against rolling each man.

    python3 tools/field/quick.py

The rates are worked out exactly (every attack roll, location band and mechanism band, weighted by
its chance). This checks, for pairings from bows on plate to rifles on bare men, that the page and
the Python give the same shares, and that rolling 20,000 blows one at a time comes out within its
own spread of them. For shellfire (men at a burst's different distances), the page's quickStruck
and the Python's _quick_struck give the same men struck on the same dice, and 20,000 of them have
the mean and spread of rolling each man. Needs Python 3 with PyYAML and Node, and dist/field.html built; exits non-zero
on a difference.
"""
from __future__ import annotations

import json
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from gravewounds import load                                 # noqa: E402
from gravewounds import units as U                           # noqa: E402

CASES = [  # table, weapon, kit, quality, attack, parry
    ("towton-1461-all-hits", "longbow", "harness_1415", "regular", 60, 0),
    ("towton-1461-all-hits", "longbow", "jack_sallet", "regular", 40, 0),
    ("towton-1461-all-hits", "poleaxe", "full_plate", "veteran", 55, 45),
    ("towton-1461-all-hits", "sword", "gambeson", "green", 50, 25),
    ("visby-1361-adjusted", "crossbow", "gotland_levy", "regular", 50, 0),
]
SHARES = ("missed", "parried", "stopped", "down", "dead")


SHELL = [  # [men, struck %] for each hex each burst reached: a field gun's bursts on a company, some gone to ground
    [[30, 20], [40, 8], [40, 3], [20, 1], [10, 10], [25, 4]],
    [[8, 30], [12, 12], [12, 5], [16, 2], [10, 1], [10, 0.5]],
    [[4, 25], [4, 5]],
    [[100, 1.5], [60, 0.5]],
]
SEEDS = 200


def page_struck() -> list:
    js = ("const {load}=require('./tools/selfplay/page.js');const {api}=load('dist/field.html',['quickStruck']);"
          f"console.log(JSON.stringify({json.dumps(SHELL)}.map((r,i)=>Array.from({{length:{SEEDS}}},(_,k)=>api.quickStruck(r,new api.SeededDice(1000*i+k))))))")
    return json.loads(subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True, check=True).stdout)


def page_rates() -> list:
    js = ("const {load}=require('./tools/selfplay/page.js');const {api}=load('dist/field.html',['quickRates']);"
          f"console.log(JSON.stringify({json.dumps(CASES)}.map(c=>api.quickRates({{table:c[0],weapon:c[1]}},{{kit:c[2],quality:c[3]}},c[4],c[5]))))")
    return json.loads(subprocess.run(["node", "-e", js], cwd=ROOT, capture_output=True, text=True, check=True).stdout)


def main() -> int:
    d = load(ROOT / "data")
    failures = 0

    def check(ok, what):
        nonlocal failures
        print(("ok  " if ok else "FAIL"), what)
        failures += 0 if ok else 1

    for i, (c, pr) in enumerate(zip(CASES, page_rates())):
        table, weapon, kit, q, atk, dfn = c
        py = U._quick_rates(d, {"table": table, "weapon": weapon}, {"kit": kit, "quality": q}, atk, dfn)
        same = all(abs(py[k] - pr[k]) < 1e-9 for k in SHARES)
        check(same, f"{weapon} on {kit}, {q}, attack {atk}, parry {dfn}: the page and the Python agree "
                    f"(down {pr['down']:.4f}, {py['down']:.4f})")
        n, t, rng = 20000, U._new_tally(), random.Random(101 + i)
        crit_at = int(atk * d.wounds["combat"]["critical_fraction"])
        for _ in range(n):
            r = rng.randint(1, 100)
            if r > atk:
                continue
            crit = r <= crit_at
            if not crit and dfn > 0 and rng.randint(1, 100) <= dfn:
                continue
            U._wound(d, {"table": table, "weapon": weapon}, {"kit": kit, "quality": q}, atk - r, crit, rng, t, r)
        p, got = py["down"], t["down"] / n
        sd = (p * (1 - p) / n) ** 0.5
        check(abs(got - p) <= 4 * sd + 1e-9, f"{weapon} on {kit}: 20,000 blows one at a time put {got:.4f} down a blow, "
                                            f"the exact rate {p:.4f} (within 4 spreads, {sd:.4f})")
    for i, (reached, pg) in enumerate(zip(SHELL, page_struck())):
        py = [U._quick_struck(d, reached, U.SeededDice(1000 * i + k)) for k in range(SEEDS)]
        check(py == pg, f"shellfire {i + 1}: the page and the Python strike the same men on the same dice ({SEEDS} seeds)")
        n, rng = 20000, random.Random(301 + i)
        quick = [U._quick_struck(d, reached, rng) for _ in range(n)]
        each = [sum(1 for m, p in reached for _ in range(m) if rng.randint(1, 100) <= p) for _ in range(n)]
        mq, me = sum(quick) / n, sum(each) / n
        vq, ve = sum((x - mq) ** 2 for x in quick) / n, sum((x - me) ** 2 for x in each) / n
        var = sum(m * (int(p) / 100) * (1 - int(p) / 100) for m, p in reached)
        sd = (var / n) ** 0.5
        check(abs(mq - me) <= 5 * sd * 2 ** 0.5 + 1e-9 and abs(vq - ve) <= 0.1 * ve + 0.05,
              f"shellfire {i + 1}: 20,000 quick rolls {mq:.2f} struck (spread {vq:.2f}), each man rolled {me:.2f} ({ve:.2f})")
    print("all checks passed" if not failures else f"{failures} check(s) failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
