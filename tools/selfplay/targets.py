"""The morale targets (docs/morale-redesign.md) from the runs run.sh ... targets writes.

python3 targets.py <dir> [<dir> ...]   one column of figures for each run directory
"""
import json
import re
import statistics
import sys
from pathlib import Path

BEFORE, AFTER = "before 1914", "1914 on"


def era(fid: str) -> str:
    """Before 1914 or after, by the battlefield's year."""
    return BEFORE if int(re.search(r"(\d{4})", fid)[1]) < 1914 else AFTER


def runs(d: str) -> list:
    """(fid, sides, run) for every run with targets in the per-seed files of directory d."""
    root = Path(d).resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {d}")
    out = []
    for p in sorted(root.glob("*.s*.json")):
        if p.resolve().parent != root:           # only the directory's own files
            continue
        try:
            j = json.loads(p.read_text())
        except ValueError:                        # still being written
            continue
        out += [(j["fid"], j["sides"], r) for r in j["runs"] if "targets" in r]
    return out


def quartiles(xs: list) -> str:
    if len(xs) < 4:
        return "-"
    q = statistics.quantiles(xs, n=4)
    return f"{q[0]:.0f}/{statistics.median(xs):.0f}/{q[2]:.0f}"


def gather(d: str) -> tuple:
    """(share down at breaking by era, loser/winner ratios, loser's % down in the rout, why counts)."""
    breaks, ratios, rout, why = {BEFORE: [], AFTER: []}, [], [], {}
    for fid, sides, r in runs(d):
        t = r["targets"]
        for b in t["breaks"]:
            breaks[era(fid)].append(b["share"])
            for w in b["why"] or ["(drain)"]:
                why[w] = why.get(w, 0) + 1
        lost = {s: t["down"].get(s, 0) / max(1, t["start"][s]) for s in sides}
        winner, loser = sorted(sides, key=lost.get)
        if lost[winner] > 0:
            ratios.append(lost[loser] / lost[winner])
        if t["down"].get(loser):
            rout.append(100 * t["routDown"].get(loser, 0) / t["down"][loser])
    return breaks, ratios, rout, why


def figures(d: str) -> dict:
    breaks, ratios, rout, why = gather(d)
    out = {}
    for e, xs in breaks.items():
        out[f"T1 share down at breaking, {e} (25%/median/75%)"] = quartiles(xs)
        out[f"T1 breaks under 10% down, {e}"] = f"{100 * sum(1 for x in xs if x < 10) / max(1, len(xs)):.0f}% of {len(xs)}"
    out["T2 loser's share lost / winner's (median)"] = f"{statistics.median(ratios):.1f}" if ratios else "-"
    out["T2 runs with the ratio 2 to 3"] = f"{100 * sum(1 for x in ratios if 2 <= x <= 3) / max(1, len(ratios)):.0f}%"
    out["T3 loser's men down in the rout (median %)"] = f"{statistics.median(rout):.0f}" if rout else "-"
    total = sum(why.values()) or 1
    out["T4 what called the breaking check"] = ", ".join(f"{k} {100 * v / total:.0f}%" for k, v in sorted(why.items(), key=lambda kv: -kv[1]))
    every = breaks[BEFORE] + breaks[AFTER]
    tenths = statistics.quantiles(every, n=10) if len(every) >= 10 else None
    out["T5 spread of share down at breaking (10%/90%)"] = f"{tenths[0]:.0f}/{tenths[-1]:.0f}" if tenths else "-"
    return out


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit
    cols = [(Path(d).name, figures(d)) for d in sys.argv[1:]]
    for k in cols[0][1]:
        print(f"{k}:")
        for name, f in cols:
            print(f"    {name:12} {f[k]}")
