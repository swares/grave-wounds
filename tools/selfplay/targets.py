"""The morale targets (docs/morale-redesign.md) from the runs run.sh ... targets writes.

python3 targets.py <dir> [<dir> ...]   one column of figures for each run directory
"""
import glob
import json
import os
import re
import statistics
import sys


def era(fid: str) -> str:
    """Before 1914 or after, by the battlefield's year."""
    return "before 1914" if int(re.search(r"(\d{4})", fid)[1]) < 1914 else "1914 on"


def runs(d: str) -> list:
    """(fid, run) for every run in d's per-seed files."""
    out = []
    for p in sorted(glob.glob(os.path.join(d, "*.s*.json"))):
        try:
            j = json.load(open(p))
        except ValueError:                        # still being written
            continue
        out += [(j["fid"], j["sides"], r) for r in j["runs"] if "targets" in r]
    return out


def quartiles(xs: list) -> str:
    if len(xs) < 4:
        return "-"
    q = statistics.quantiles(xs, n=4)
    return f"{q[0]:.0f}/{statistics.median(xs):.0f}/{q[2]:.0f}"


def figures(d: str) -> dict:
    breaks = {"before 1914": [], "1914 on": []}
    ratios, rout_share, why = [], [], {}
    for fid, sides, r in runs(d):
        t = r["targets"]
        for b in t["breaks"]:
            breaks[era(fid)].append(b["share"])
            for w in b["why"] or ["(drain)"]:
                why[w] = why.get(w, 0) + 1
        share = {s: t["down"].get(s, 0) / max(1, t["start"][s]) for s in sides}
        lo, hi = sorted(sides, key=lambda s: share[s])
        if share[lo] > 0:
            ratios.append(share[hi] / share[lo])
        if t["down"].get(hi):
            rout_share.append(100 * t["routDown"].get(hi, 0) / t["down"][hi])
    out = {}
    for e, xs in breaks.items():
        out[f"T1 share down at breaking, {e} (25%/median/75%)"] = quartiles(xs)
        out[f"T1 breaks under 10% down, {e}"] = f"{100 * sum(1 for x in xs if x < 10) / max(1, len(xs)):.0f}% of {len(xs)}"
    out["T2 loser's share lost / winner's (median)"] = f"{statistics.median(ratios):.1f}" if ratios else "-"
    out["T2 runs with the ratio 2 to 3"] = f"{100 * sum(1 for x in ratios if 2 <= x <= 3) / max(1, len(ratios)):.0f}%"
    out["T3 loser's men down in the rout (median %)"] = f"{statistics.median(rout_share):.0f}" if rout_share else "-"
    total = sum(why.values()) or 1
    out["T4 what called the breaking check"] = ", ".join(f"{k} {100 * v / total:.0f}%" for k, v in sorted(why.items(), key=lambda kv: -kv[1]))
    allx = breaks["before 1914"] + breaks["1914 on"]
    out["T5 spread of share down at breaking (10%/90%)"] = (f"{statistics.quantiles(allx, n=10)[0]:.0f}/{statistics.quantiles(allx, n=10)[-1]:.0f}" if len(allx) >= 10 else "-")
    return out


if __name__ == "__main__":
    cols = [(d, figures(d)) for d in sys.argv[1:]] or [print(__doc__)]
    for k in (cols[0][1] if cols and cols[0] else {}):
        print(f"{k}:")
        for d, f in cols:
            print(f"    {os.path.basename(d.rstrip('/')):12} {f[k]}")
