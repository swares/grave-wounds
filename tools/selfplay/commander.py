"""The enemy commander's benchmark: how the commander does playing each side of each battlefield, from self-play runs.

python3 commander.py <dir> [<dir> ...]   writes commander.json from the play results in the dirs (run.sh ... play)

A player "beats the enemy commander" on a battlefield when his result is better than the commander's typical
result for the same side: first the outcome (a win beats a draw beats a loss), then, for the same outcome, the
loss ratio (the enemy's men lost for each of his own). The bar is the commander's median run as that side, ranked
the same way, so a player who beats it did better than the commander does at least half the time.

Each battlefield's figures carry the stamp (dist/field-stamps.json) of the rules and battlefield they were run
under; build.py warns when they no longer match.
"""
import json
import os
import statistics
import sys
from datetime import date

from report import joined, winner

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
OUTCOME = {1: "win", 0: "draw", -1: "loss"}


def lost(r: dict, k: int) -> int:
    """Side k's men lost in run r: killed, left on the field, died, carried off and taken."""
    s = r["sides"][k]
    return s["killed"] + s["left"] + s["died"] + s["carried"] + s.get("taken", 0)


def ratio(r: dict, k: int) -> float:
    """The enemy's men lost for each of side k's (both plus one, so a side that lost no one still has a figure)."""
    return round((lost(r, 1 - k) + 1) / (lost(r, k) + 1), 2)


def outcome(j: dict, r: dict, k: int) -> int:
    w = winner(j, r)
    return 0 if w is None else (1 if w == k else -1)


def side(j: dict, k: int) -> dict:
    runs = j["runs"]
    ranked = sorted((outcome(j, r, k), ratio(r, k)) for r in runs)
    bar = ranked[len(ranked) // 2]
    n = len(runs)
    return {"side": j["sides"][k], "stance": (j.get("stances") or [None, None])[k],
            "won": round(sum(o == 1 for o, _ in ranked) / n, 2), "drew": round(sum(o == 0 for o, _ in ranked) / n, 2),
            "lost_share": round(statistics.median(lost(r, k) / max(1, r["sides"][k]["start"]) for r in runs), 3),
            "bar": {"outcome": OUTCOME[bar[0]], "ratio": bar[1]}}


def main(dirs: list) -> None:
    stamps = json.load(open(os.path.join(ROOT, "dist", "field-stamps.json")))
    out_p = os.path.join(HERE, "commander.json")
    out = json.load(open(out_p)) if os.path.exists(out_p) else {"fields": {}}
    by = {}
    for d in dirs:
        for j in joined(d):
            if j["fid"] in by:
                by[j["fid"]]["runs"] += j["runs"]
            else:
                by[j["fid"]] = j
    for fid, j in sorted(by.items()):
        out["fields"][fid] = {"stamp": stamps.get(fid), "runs": len(j["runs"]), "sides": [side(j, 0), side(j, 1)]}
        b = out["fields"][fid]["sides"]
        print(f"{fid:<24} {len(j['runs']):>3} runs  {b[0]['side'][:14]:<14} won {b[0]['won']:.0%} bar {b[0]['bar']}  "
              f"{b[1]['side'][:14]:<14} won {b[1]['won']:.0%} bar {b[1]['bar']}")
    out["updated"] = date.today().isoformat()
    out["about"] = ("The enemy commander's benchmark, written by tools/selfplay/commander.py: for each battlefield and "
                    "side, how often the commander won playing it against itself, and the bar a player beats: the "
                    "commander's median outcome, then its loss ratio (enemy men lost for each of the side's own).")
    with open(out_p, "w") as f:
        json.dump(out, f, indent=1, sort_keys=True)
        f.write("\n")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
    else:
        main(sys.argv[1:])
