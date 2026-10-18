"""Self-play reports from the results run.sh writes.

python3 report.py winners <dir>          each battlefield's runs against the battle as fought
python3 report.py diff <before> <after>  the battlefields whose results changed, and the totals
python3 report.py quality <dir>          how each side's commander used its units (run.sh ... quality)
"""
import glob
import json
import os
import re
import statistics
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def joined(d: str) -> list:
    """The play results in d, each battlefield's per-seed files (<fid>.s<k>.json) joined, runs in seed order."""
    by = {}
    for p in glob.glob(os.path.join(d, "*.s*.json")):
        m = re.match(r"(.+)\.s(\d+)\.json$", os.path.basename(p))
        by.setdefault(m[1], []).append((int(m[2]), p))
    out = []
    for fid in sorted(by):
        parts = [json.load(open(p)) for _, p in sorted(by[fid])]
        out.append({**parts[0], "runs": [r for x in parts for r in x["runs"]]})
    return out


def lost_share(r: dict, k: int) -> float:
    """Side k's men lost in run r (killed, left, died, carried), as a share of its men."""
    s = r["sides"][k]
    return (s["killed"] + s["left"] + s["died"] + s["carried"]) / max(1, s["start"])


def winner(j: dict, r: dict):
    """The side index that won run r (None: both gone): the side left standing; the attacker if it took and held
    the objective; else with an objective the side holding it at the end; else the side with the smaller share lost."""
    sides, stop = j["sides"], r["stop"]
    if stop["why"] == "gone":
        return None if len(stop["sides"]) == 2 else 1 - stop["sides"][0]
    if stop["why"] == "held":
        return sides.index(stop["side"])
    if j["objective"]:
        att = j["objective"]["side"]
        return att if (r["held"] or [None])[0] == sides[att] else 1 - att
    stand = [r["sides"][k]["standing"] for k in (0, 1)]
    if stand[0] == 0 and stand[1] > 0:
        return 1
    if stand[1] == 0 and stand[0] > 0:
        return 0
    return 0 if lost_share(r, 0) < lost_share(r, 1) else 1


def took_it(j: dict, r: dict) -> bool:
    """Run r ended with the attacker holding the objective (secured or not)."""
    att = (j["objective"] or {}).get("side")
    return att is not None and (r["held"] or [None])[0] == j["sides"][att]


def matches(j: dict, r: dict, a: dict) -> bool:
    """Run r came out as the battle did (a: its line in actual.json): the same winner; or, for a battle fought to a
    draw in which the attacker took the objective (Lundy's Lane, Cassino town), a draw or the attacker holding it
    at the end: the fight on the field went the attacker's way, and the draw came after (the Americans withdrew
    from Lundy's Lane; the paratroops held the rest of Cassino)."""
    w = winner(j, r)
    return w == a["won"] or (a["won"] is None and a.get("objective") == "taken" and took_it(j, r))


def rows(d: str) -> dict:
    """{fid: (runs matched, runs, % lost side 0, % lost side 1, median exchanges, stops, as fought)}."""
    actual = json.load(open(os.path.join(HERE, "actual.json")))
    out = {}
    for j in joined(d):
        a, runs = actual[j["fid"]], j["runs"]
        won = [matches(j, r, a) for r in runs]
        stops = {}
        for r in runs:
            stops[r["stop"]["why"]] = stops.get(r["stop"]["why"], 0) + 1
        cas = [statistics.median(lost_share(r, k) * 100 for r in runs) for k in (0, 1)]
        who = "draw" if a["won"] is None else j["sides"][a["won"]]
        out[j["fid"]] = (sum(won), len(runs), cas[0], cas[1],
                         statistics.median(r["exchanges"] for r in runs), stops, who, j["sides"])
    return out


def line(fid: str, x: tuple) -> str:
    m, n, c0, c1, ex, stops, who, sides = x
    return (f"{fid:<24} actual: {who[:22]:<22} matched {m}/{n}  lost {sides[0][:12]} {c0:5.1f}% / "
            f"{sides[1][:12]} {c1:5.1f}%  exchanges {ex:>5}  stops {stops}")


def total(r: dict) -> str:
    return f"{sum(x[0] for x in r.values())}/{sum(x[1] for x in r.values())} runs matched the actual winner"


def winners(d: str) -> None:
    r = rows(d)
    for fid, x in r.items():
        print(line(fid, x))
    print("overall:", total(r))


def diff(a: str, b: str) -> None:
    ra, rb = rows(a), rows(b)
    print("before:", total(ra))
    print("after: ", total(rb))
    for fid in sorted(set(ra) & set(rb)):
        x, y = ra[fid], rb[fid]
        if x[:5] != y[:5]:
            print(f"{fid:<24} {x[0]}/{x[1]} -> {y[0]}/{y[1]}  lost {x[2]:.1f}%/{x[3]:.1f}% -> {y[2]:.1f}%/{y[3]:.1f}%  exchanges {x[4]} -> {y[4]}")


def quality(d: str) -> None:
    by = {}
    for p in sorted(glob.glob(os.path.join(d, "*.s*.json"))):
        j = json.load(open(p))
        for s in j["sides"]:
            by.setdefault((j["fid"], s["side"], s["stance"]), []).append(s)
    print(f"{'battlefield':22} {'side':14} {'stance':7} idle%  peak%  spread  hitIdle%  never fired or fought")
    for (fid, side, stance), ss in sorted(by.items()):
        av = lambda k: round(sum(x[k] or 0 for x in ss) / len(ss))
        spread = round(sum((x["lastFirst"] or 0) - (x["firstEngaged"] or 0) for x in ss) / len(ss))
        idle = ", ".join(sorted({u["name"] for x in ss for u in x["idleWhy"]}))
        print(f"{fid[:22]:22} {side[:14]:14} {stance:7} {av('idleMen'):5} {av('peakEngaged'):6} {spread:7} {av('lostIdle'):9}  {idle[:110]}")
    att = [x["idleMen"] for (_, _, stance), ss in by.items() if stance == "attack" for x in ss]
    if att:
        print(f"attacking sides: {sum(att) / len(att):.1f}% of men never fought, on average")


if __name__ == "__main__":
    cmd, *args = sys.argv[1:] or ["help"]
    {"winners": winners, "diff": diff, "quality": quality}.get(cmd, lambda *_: print(__doc__))(*args)
