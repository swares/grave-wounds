"""The field page's data carries every key its rules read.

    python3 tools/field/keys.py

build.py's field_bundle copies only some keys of each weapon, armour material, kit and hit
location to the field page. A rule that reads a key left out finds nothing there and silently
does nothing: weapons.yaml defeat_only and min_range were left out until PR #584, so on the
field map arrows still beat plate and no minimum range held. This check finds the variables the
page's code takes from FD.weapons, FD.materials, FD.kits and FD.locations, and fails if it reads
a key of one of them that the source data has but the bundle leaves out. Needs Python 3 with
PyYAML; exits non-zero on a key read but not carried.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import build                                                 # noqa: E402
from gravewounds import load                                 # noqa: E402

CODE = [ROOT / "templates" / "units.js", ROOT / "templates" / "field.html"]
# Names the search matches that are not reads of the table: the same variable name used for
# something else elsewhere in the code.
NOT_READS = {("weapons", "id"): "w is also a wind in the weather code (winds.find(w => w.id === ...))"}


def read_keys(code: str, table: str) -> set[str]:
    """The keys the code reads from entries of FD.<table>: directly (FD.weapons[w].reach) or through
    a variable it took one into (const w = FD.weapons[wid] ... w.reach)."""
    names = set(re.findall(r"\b(\w+)\s*=\s*FD\." + table + r"\[", code))
    keys = set(re.findall(r"FD\." + table + r"\[[^\]]*\]\??\.(\w+)", code))
    for n in names:
        keys |= set(re.findall(r"\b" + re.escape(n) + r"\??\.(\w+)", code))
    return keys


def main() -> int:
    d = load(ROOT / "data")
    fb = build.field_bundle(d)
    code = "\n".join(p.read_text(encoding="utf-8") for p in CODE)
    source = {
        "weapons": set().union(*(w.keys() for w in d.weapons.values())),
        "materials": set().union(*(m.keys() for m in d.armor["materials"].values())),
        "kits": set().union(*(k.keys() for k in d.armor["kits"].values())),
        "locations": set().union(*(l.keys() for l in d.locations)),
    }
    failures = []
    for table, src in source.items():
        carried = set().union(*(e.keys() for e in fb[table].values()))
        missing = sorted(k for k in (read_keys(code, table) & src) - carried if (table, k) not in NOT_READS)
        print(("FAIL" if missing else "ok  "), f"FD.{table}: the page reads {', '.join(missing) or 'no key'} the bundle leaves out")
        failures += missing
    print("all checks passed" if not failures else f"{len(failures)} key(s) read but not carried")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
