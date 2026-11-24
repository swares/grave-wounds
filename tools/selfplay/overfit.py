"""Overfitting to the benchmark: the commander's match rate on the battlefields added last against the rest.

    python3 tools/selfplay/overfit.py [cut-off date, default 2026-10-20]

The benchmark (commander.json, 36 runs a battlefield) is also what the rules are tuned against, so
its overall match rate can rise for the wrong reason. The battlefields added after the cut-off were
tuned least. For each group: how many, the mean and median share of runs that came out as the battle
did (the winner as fought, from actual.json; the two fought to a draw are left out), how many fall
under half, and the pooled share with its 95% spread. Also by how often each battlefield's file has
been changed (git log --follow), the work done on it. Reads the repository's git history.
"""
import json
import math
import statistics as st
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CUT = sys.argv[1] if len(sys.argv) > 1 else "2026-10-20"
bench = json.loads((ROOT / "tools/selfplay/commander.json").read_text())["fields"]
actual = json.loads((ROOT / "tools/selfplay/actual.json").read_text())


def history(fid):
    out = subprocess.run(["git", "log", "--format=%as", "--follow", "--", f"data/fields/{fid}.yaml"], capture_output=True, text=True, cwd=ROOT).stdout.split()
    return (out[-1] if out else "?"), len(out)


rows = []
for fid, b in bench.items():
    w = actual.get(fid, {}).get("won")
    if not isinstance(w, int):
        continue
    first, changes = history(fid)
    rows.append({"fid": fid, "first": first, "changes": changes, "match": b["sides"][w]["won"], "runs": b["runs"]})


def report(name, rs):
    if not rs:
        return print(f"{name}: none")
    m = [r["match"] for r in rs]
    n = sum(r["runs"] for r in rs)
    p = sum(r["match"] * r["runs"] for r in rs) / n
    print(f"{name}: {len(rs)} battlefields, mean {st.mean(m):.0%}, median {st.median(m):.0%}, {sum(v < 0.5 for v in m)} under half;"
          f" pooled {p:.1%} of {n} runs (±{1.96 * math.sqrt(p * (1 - p) / n):.1%})")


report("All", rows)
report(f"Added before {CUT}", [r for r in rows if r["first"] < CUT])
report(f"Added from {CUT}", [r for r in rows if r["first"] >= CUT])
report("Changed 4 times or fewer", [r for r in rows if r["changes"] <= 4])
report("Changed 8 times or more", [r for r in rows if r["changes"] >= 8])
print(f"\nFrom {CUT}, lowest first:")
for r in sorted((r for r in rows if r["first"] >= CUT), key=lambda r: r["match"]):
    print(f"  {r['fid']:<22} {r['match']:.0%}  added {r['first']}, changed {r['changes']} times")
