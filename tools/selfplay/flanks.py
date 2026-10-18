"""Flanking in self-play, from the runs run.sh ... flanks writes (flanks.js).

python3 flanks.py <dir>   a row for each battlefield (its runs summed), then the totals by era

Columns: exchanges with an enemy in hand-to-hand contact; spare unit-exchanges (steady, not in contact);
how many of those could reach an open flank or rear hex of a fighting enemy within one move or three;
flank or rear strikes, against front strikes; flank strikes by a unit that had such a chance in the five
exchanges before; volleys fired from off the target's front, as a share of all volleys.
"""
import json
import re
import sys
from pathlib import Path

KEYS = ["engaged", "spare", "chance1", "chance3", "strikes", "front", "taken", "volleys", "volleyFlank"]


def era(fid: str) -> str:
    return "before 1914" if int(re.search(r"(\d{4})", fid)[1]) < 1914 else "1914 on"


def gather(d: str) -> dict:
    """fid -> summed tallies over its runs and both sides."""
    root = Path(d).resolve()
    if not root.is_dir():
        raise SystemExit(f"not a directory: {d}")
    out = {}
    for p in sorted(root.glob("*.s*.json")):
        if p.resolve().parent != root:           # only the directory's own files
            continue
        try:
            j = json.loads(p.read_text())
        except ValueError:                        # still being written
            continue
        t = out.setdefault(j["fid"], dict.fromkeys(KEYS + ["runs"], 0))
        t["runs"] += 1
        for s in j["by"].values():
            for k in KEYS:
                t[k] += s.get(k, 0)
    return out


def pct(a: int, b: int) -> str:
    return f"{100 * a / b:.0f}%" if b else "-"


def row(name: str, t: dict) -> str:
    return (f"| {name} | {t['runs']} | {t['engaged']} | {t['spare']} | {pct(t['chance1'], t['spare'])} | {pct(t['chance3'], t['spare'])} "
            f"| {t['strikes']} / {t['front']} | {t['taken']} | {pct(t['volleyFlank'], t['volleys'])} |")


def main(d: str) -> None:
    g = gather(d)
    print("| Battlefield | Runs | Contact exchanges | Spare unit-exchanges | Chance, 1 move | Chance, 3 moves "
          "| Flank strikes / front | Taken | Volleys from a flank |")
    print("|---|---|---|---|---|---|---|---|---|")
    eras = {}
    for fid in sorted(g):
        print(row(fid, g[fid]))
        e = eras.setdefault(era(fid), dict.fromkeys(KEYS + ["runs"], 0))
        for k in e:
            e[k] += g[fid][k]
    for e in sorted(eras, reverse=True):
        print(row(f"**{e}**", eras[e]))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(__doc__)
        raise SystemExit(1)
    main(sys.argv[1])
