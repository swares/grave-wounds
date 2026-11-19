"""A season of service (templates/service.js) against gravewounds/service.py, on the same inputs and dice.

    python3 tools/service/parity.py [cases] [seed]

Makes `cases` random seasons of the team: a war's season, one to four men (Endurance, position, a
battalion's own figure or the GM's share where the sources give none) and the actions they were at;
plays each through the Python with a seeded d100, writes them with the team builder's service bundle to
tools/service/.cache/, then tools/service/test.js plays them through the JavaScript with the same dice
and compares every result, with every action's hit chance and every weapon roll. Needs Python 3 with
PyYAML and Node; exits non-zero on any difference.
"""
from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from build import service_bundle                  # noqa: E402  the bundle the team builder is built with
from gravewounds import load                      # noqa: E402
from gravewounds import service as sv             # noqa: E402
from gravewounds.disease import seeded_d100       # noqa: E402

CACHE = Path(__file__).parent / ".cache"


def cases(d, n: int, seed: int) -> list[dict]:
    t = random.Random(seed)   # NOSONAR: test data that must repeat from its seed, not a security use
    out = []
    for k in range(n):
        wid = t.choice(sorted(d.service))   # NOSONAR: as above
        W = d.service[wid]
        s = t.choice(W["seasons"])          # NOSONAR: as above
        men = []
        for j in range(t.randint(1, 4)):    # NOSONAR: as above
            m = {"name": f"m{j}", "endurance": t.choice([None, 30, 50, 70]), "position": t.choice(sorted(W["positions"]))}   # NOSONAR: as above
            for aid in s["actions"]:
                a = W["actions"][aid]
                if a.get("units") and t.random() < 0.3:   # NOSONAR: as above
                    m.setdefault("unit", {})[aid] = t.randrange(len(a["units"]))   # NOSONAR: as above
                if a.get("share") is None and t.random() < 0.7:   # NOSONAR: as above
                    m.setdefault("share", {})[aid] = t.randint(1, 60)   # NOSONAR: as above
                if t.random() < 0.2:   # NOSONAR
                    m.setdefault("pos_at", {})[aid] = t.choice(sorted(W["positions"]))   # NOSONAR
            if t.random() < 0.4:   # NOSONAR: as above (a case carried from a season before)
                m["health"] = sv.serve(d, wid, s["id"], [{"name": m["name"], "endurance": m["endurance"]}], [], seeded_d100(seed * 31 + k * 7 + j))["men"][0]["health"]
            if t.random() < 0.3:   # NOSONAR: as above (a battle wound on his track, from the roller)
                h = m.get("health") or {"cases": [], "immune": {}, "had": {}, "dead": 0}
                h["cases"].append({"d": "wound", "inc": 0, "step": t.randint(1, 3), "peak": 0, "shown": 0, "chronic": False,   # NOSONAR: as above
                                   "inf": t.choice(["low", "medium", "high"]), "fever": t.randint(2, 6), "wid": f"w{j}"})   # NOSONAR: as above
                m["health"] = h
            men.append(m)
        rolled = [a for a in s["actions"] if t.random() < 0.8]   # NOSONAR: as above
        dice = seed * 7919 + k
        out.append({"war": wid, "season": s["id"], "men": men, "rolled": rolled, "dice": dice,
                    "want": sv.serve(d, wid, s["id"], men, rolled, seeded_d100(dice))})
    return out


def fixed(d) -> dict:
    """Every action's hit chance at each position, the weapon for every d100, and small fights
    rolled for each state and picked by the GM (20 seeds each)."""
    pct, weapons, weeks, fights = {}, {}, {}, {}
    for wid, W in d.service.items():
        for s in W["seasons"]:
            for aid in s["actions"]:
                weeks[f"{wid}/{s['id']}/{aid}"] = sv.action_week(W, s["id"], aid)
        for aid in W["actions"]:
            for p in W["positions"]:
                pct[f"{wid}/{aid}/{p}"] = sv.hit_pct(W, aid, p, None, 20)
        weapons[wid] = [sv.weapon_for(d, W, r) for r in range(1, 101)]
        for key in list(W["states"]) + ["=" + f["id"] for f in W.get("small_fights", [])]:
            for seed in range(1, 21):
                st, fid = (key, None) if key[0] != "=" else (next(iter(W["states"])), key[1:])
                fights[f"{wid}/{key}/{seed}"] = sv.small_fight(W, st, seeded_d100(seed), fid) if W.get("small_fights") else None
    return {"pct": pct, "weapons": weapons, "weeks": weeks, "fights": fights}


def main() -> int:
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    d = load(ROOT / "data")
    CACHE.mkdir(exist_ok=True)
    (CACHE / "data.json").write_text(json.dumps(service_bundle(d)), encoding="utf-8")
    (CACHE / "cases.json").write_text(json.dumps({"cases": cases(d, n, seed), "fixed": fixed(d)}), encoding="utf-8")
    return subprocess.run(["node", str(Path(__file__).parent / "test.js")], env={**os.environ, "SERVICE_PARITY": "1"}, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
