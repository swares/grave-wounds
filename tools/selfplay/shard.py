"""One shard of a self-play measurement, for running it in parallel (the selfplay workflow).

python3 shard.py <shard> <shards> <seeds> [first seed] [fields folder]

Prints "<field id> <seed>" for every battlefield x seed in this shard: all the jobs, longest
first by times.txt, dealt round-robin over the shards so each gets a fair share of the long ones.
"""
import os
import sys
from pathlib import Path

here = Path(__file__).resolve().parent
fields = here.parent.parent / "data" / "fields"


def jobs(seeds: int, first: int, folder: Path = fields) -> list:
    """Every (field id, seed), longest first."""
    times = here / "times.txt"
    t = {}
    for line in times.read_text().splitlines() if times.exists() else []:
        if line.strip():
            f, secs = line.split()
            t[f] = secs
    fids = sorted(f[:-5] for f in os.listdir(folder) if f.endswith(".yaml"))
    return [(f, k) for _, f, k in sorted(((float(t.get(f, 0)), f, k) for f in fids for k in range(first, first + seeds)),
                                         key=lambda x: (-x[0], x[1], x[2]))]


def main(argv: list) -> None:
    if len(argv) < 3:
        print(__doc__)
        raise SystemExit(1)
    shard, shards, seeds = int(argv[0]), int(argv[1]), int(argv[2])
    first = int(argv[3]) if len(argv) > 3 else 1
    folder = Path(argv[4]) if len(argv) > 4 else fields
    for n, (f, k) in enumerate(jobs(seeds, first, folder)):
        if n % shards == shard:
            print(f, k)


if __name__ == "__main__":
    main(sys.argv[1:])
