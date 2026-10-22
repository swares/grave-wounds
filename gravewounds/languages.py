"""Languages (data/languages.yaml). The team builder, roller and travel map (templates/ranks.js)
repeat roll, value, band, shared, talk, words, passing, escape_bonus and season exactly, taking
the dice in the same order.

- A man's own tongue is at `native` and never ticked; others are a percentage, read in bands.
- A tongue he lacks is known at a share of a related one he has.
- Talk skills in a tongue are capped by it; words across tongues roll at the best tongue the two
  men share; passing as a native is opposed by the listener's Watch, its difficulty by his grade."""
from __future__ import annotations

from .checks import check, opposed
from .model import Data


def _cfg(d: Data) -> dict:
    return d.languages or {}


def _army(d: Data, eid: str, region: str) -> dict:
    return ((_cfg(d).get("armies") or {}).get(eid) or {}).get(region) or {"own": [], "others": []}


def cap(d: Data, t: str) -> int:
    """The highest a learned tongue rises: a pidgin's cap, else `max`."""
    L = _cfg(d)
    return (L["tongues"].get(t) or {}).get("cap", L.get("max", 85))


def _set(c: dict, t: str, v: int) -> None:
    if t != c["native"]:
        c["tongues"][t] = max(c["tongues"].get(t, 0), v)


def roll(d: Data, eid: str, region: str, trait: str, drawback: str, rng) -> dict:
    """His tongues at creation. Dice: d100 for his own tongue (by the army's shares, or among the
    drawback's `own` list); then each other tongue in order that he lacks, d100 against its chance
    and, if he has it, its range; then his trait's and drawback's tongues.
    -> {"native": id, "tongues": {id: value}}"""
    L, A = _cfg(d), _army(d, eid, region)
    T = L.get("traits") or {}
    tr, dr = T.get(trait) or {}, T.get(drawback) or {}
    r = rng.randint(1, 100)
    if dr.get("own"):
        native = dr["own"][(r - 1) * len(dr["own"]) // 100]
    else:
        native, acc = A["own"][-1][0], 0
        for t, share in A["own"]:
            acc += share
            if r <= acc:
                native = t
                break
    c = {"native": native, "tongues": {native: L.get("native", 90)}}
    for t, chance, (lo, hi) in A.get("others", []):
        if t in c["tongues"]:
            continue
        if rng.randint(1, 100) <= chance:
            c["tongues"][t] = rng.randint(lo, hi)
    for row in (tr, dr):
        if row.get("extra"):
            pool = [t for t, _ in A["own"]] + [t for t, _, _ in A.get("others", [])]
            for _ in range(row["extra"]):
                left = [t for t in dict.fromkeys(pool) if t not in c["tongues"]]
                if not left:
                    break
                t = left[(rng.randint(1, 100) - 1) * len(left) // 100]
                lo, hi = row["range"]
                c["tongues"][t] = rng.randint(lo, hi)
        if row.get("enemy") and A.get("enemy"):
            lo, hi = row["enemy"]
            _set(c, A["enemy"], rng.randint(lo, hi))
        for t, v in (row.get("also") or {}).items():
            _set(c, t, v)
        for t, (lo, hi) in (row.get("has") or {}).items():
            _set(c, t, rng.randint(lo, hi))
    return c


def value(d: Data, tongues: dict, t: str) -> int:
    """His figure in tongue t: his own, or a share of a related tongue he has (the better)."""
    best = tongues.get(t, 0)
    for a, b, share in _cfg(d).get("related", []):
        other = b if a == t else a if b == t else None
        if other and other in tongues:
            best = max(best, int(tongues[other] * share))
    return best


def band(d: Data, v: int) -> str:
    return [b for b in _cfg(d)["bands"] if v >= b["from"]][-1]["name"]


def shared(d: Data, a: dict, b: dict) -> tuple[str | None, int]:
    """The best tongue two men share and its figure (the lower of theirs); (None, 0) for none."""
    best, bv = None, 0
    for t in sorted(set(a) | set(b) | {x for r in _cfg(d).get("related", []) for x in r[:2]}):
        v = min(value(d, a, t), value(d, b, t))
        if v > bv:
            best, bv = t, v
    return best, bv


def talk(d: Data, skill: int, tongues: dict, native: str, t: str) -> int:
    """A talk skill used in tongue t: at most his figure in it (his own tongue: no cap)."""
    return skill if t == native else min(skill, value(d, tongues, t))


def words(d: Data, v: int, roll_: int, book: bool = False, closed: bool = False, diff: str = "ordinary") -> dict:
    """Words across tongues at figure v: -> {"check", "reading": full | meaning | gist | error}.
    A phrase book makes a closed question (yes or no, a number, a direction) Easy at no worse
    than `phrase_book`."""
    L = _cfg(d)
    if book and closed:
        v, diff = max(v, L.get("phrase_book", 25)), "easy"
    k = check(d, v, diff, roll_)
    if k["critical"]:
        reading = "full"
    elif k["success"]:
        reading = "meaning"
    elif k["fumble"]:
        reading = "error"
    else:
        reading = "gist"
    return {"check": k, "reading": reading}


def grade(d: Data, v: int) -> dict:
    return [g for g in _cfg(d)["passing"] if v >= g["from"]][0]


def passing(d: Data, v: int, watch: int, a_roll: int, b_roll: int) -> dict:
    """Passing as a native: his figure at his grade's difficulty against the listener's Watch.
    -> {"grade", "opposed" (None when he cannot pass), "passed"}"""
    g = grade(d, v)
    if not g["diff"]:
        return {"grade": g["name"], "opposed": None, "passed": False}
    o = opposed(d, v, g["diff"], a_roll, watch, b_roll)
    return {"grade": g["name"], "opposed": o, "passed": o["winner"] == "a"}


def escape_bonus(d: Data, v: int) -> int:
    """What his figure in the country's tongue adds to his Fieldcraft to reach his own side."""
    return [e for e in _cfg(d)["escape_home"] if v >= e["from"]][0]["mod"]


def season(d: Data, c: dict, ticks, rng, gain=(1, 3)) -> list[dict]:
    """End of season for his ticked tongues ("tongue:<id>", in id order; his own never): d100 over
    his figure rises by the gain dice, to the tongue's cap. -> [{"tongue", "roll", "was", "gain"}]"""
    out = []
    for t in sorted({k[7:] for k in ticks if k.startswith("tongue:")}):
        if t == c.get("native") or t not in _cfg(d)["tongues"]:
            continue
        was, r = c["tongues"].get(t, 0), rng.randint(1, 100)
        up = rng.randint(gain[0], gain[1]) if r > was and was < cap(d, t) else 0
        c["tongues"][t] = min(cap(d, t), was + up)
        out.append({"tongue": t, "roll": r, "was": was, "gain": c["tongues"][t] - was})
    return out
