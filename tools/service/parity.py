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
        posture = t.choice([None] + sorted((d.posture or {}).get("postures", {})))   # NOSONAR: as above (the team's posture)
        out.append({"war": wid, "season": s["id"], "men": men, "rolled": rolled, "dice": dice, "posture": posture,
                    "want": sv.serve(d, wid, s["id"], men, rolled, seeded_d100(dice), posture)})
    return out


def fixed(d) -> dict:
    """Every action's hit chance at each position, the weapon for every d100, and small fights
    rolled for each state and picked by the GM (20 seeds each), and the followers' desertion each season."""
    pct, weapons, weeks, fights, desert, vac = {}, {}, {}, {}, {}, {}
    for wid, W in d.service.items():
        for s in W["seasons"]:
            desert[f"{wid}/{s['id']}"] = sv.desert_pct(W, s["id"])
            vac[f"{wid}/{s['id']}"] = sv.vacancy_pct(d, W, s["id"], s["actions"])
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
    return {"pct": pct, "weapons": weapons, "weeks": weeks, "fights": fights, "desert": desert, "vac": vac}


def fresh_ok() -> bool:
    """team.py's term-event row for a man who has had them all: the rolled one again, not an
    endless search (End of season after a long service; as team.js freshRow, checked in season.py)."""
    from gravewounds.team import _fresh   # noqa: PLC0415
    rows = [{"text": "a", "to": 50}, {"text": "b", "to": 100}]
    ok = _fresh(rows, 70, ["a", "b"])["text"] == "b" and _fresh(rows, 70, ["b"])["text"] == "a"
    print(("ok   " if ok else "FAIL ") + "team.py: a man who has had every term event gets the rolled one again")
    return ok


CAP_CASES = [([["archer", 10], ["spearman", 4]], 11, [["archer", 7], ["spearman", 4]]),
             ([["a", 3], ["b", 3]], 4, [["a", 2], ["b", 2]]),
             ([["a", 5], ["b", 1]], 5, [["a", 4], ["b", 1]]),
             ([["a", 2]], None, [["a", 2]])]   # as season.py checks team.js fwCapCounts


def cap_ok() -> bool:
    """team.py cap_counts: a muster cut to what the leader keeps, off the largest career."""
    from gravewounds.team import cap_counts   # noqa: PLC0415
    ok = all(cap_counts(c, k) == want for c, k, want in CAP_CASES)
    print(("ok   " if ok else "FAIL ") + "team.py: the muster cut to the cap, off the largest career")
    return ok


def main() -> int:
    if not fresh_ok() or not cap_ok():
        return 1
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 200
    seed = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    d = load(ROOT / "data")
    CACHE.mkdir(exist_ok=True)
    (CACHE / "data.json").write_text(json.dumps(service_bundle(d)), encoding="utf-8")
    (CACHE / "cases.json").write_text(json.dumps({"cases": cases(d, n, seed), "fixed": fixed(d)}), encoding="utf-8")
    return subprocess.run(["node", str(Path(__file__).parent / "test.js")], env={**os.environ, "SERVICE_PARITY": "1"}, check=False).returncode


if __name__ == "__main__":
    sys.exit(main())
