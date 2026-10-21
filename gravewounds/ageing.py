"""Ageing (data/ageing.yaml): every `step` years of a man's age, his age band's decline (by the
middle of those years, older for his Wear), a step of maturity, and Wear; and the Worn Out check
for each term he serves from 35 (or with heavy Wear). Used when a character is made (team.py:
the years of his terms) and at End of season for the terms he serves in play. The team builder
(templates/team.js) repeats steps, add_wear and worn_out exactly, taking the dice in the same
order: for each step, Strength, Agility, Endurance (twice, the worse, with heavy Wear), Wits."""
from __future__ import annotations

from .model import Data

DECLINE_ORDER = ("str", "agi", "end", "wits")
MATURE_ORDER = ("pres", "wits", "nerve")


def _A(d: Data) -> dict:
    return d.ageing or {}


def _roll(rng, dice) -> int:
    return sum(rng.randint(1, dice[1]) for _ in range(dice[0]))


def steps(d: Data, c: dict, rng) -> list[dict]:
    """Every pending step from c["aged_to"] to c["age"] (c changed in place: stat_mods, wear,
    matured, aged_to). -> [{"age", "changes": {stat: +/-n}}]"""
    A = _A(d)
    if not A:
        return []
    step, W, M = A.get("step", 4), A["wear"], A["maturity"]
    c.setdefault("aged_to", c["age"])
    c.setdefault("wear", 0)
    mat = c.setdefault("matured", {})
    out = []
    while c["age"] - c["aged_to"] >= step:
        mid = c["aged_to"] + step / 2
        eff = mid + (c["wear"] // W["per"]) * W["add_years"]
        band = [b for b in A["decline"] if eff >= b["from"]][-1]
        ch = {}
        for k in DECLINE_ORDER:
            if band.get(k):
                n = _roll(rng, band[k])
                if k == "end" and c["wear"] >= W["end_twice"]:
                    n = max(n, _roll(rng, band[k]))
                ch[k] = ch.get(k, 0) - n
        if mid >= M["from"]:
            for k in MATURE_ORDER:
                if mid < M[k]["to"] and mat.get(k, 0) < M[k]["cap"]:
                    mat[k] = mat.get(k, 0) + 1
                    ch[k] = ch.get(k, 0) + 1
        for k, v in ch.items():
            c["stat_mods"][k] = c["stat_mods"].get(k, 0) + v
        c["wear"] += W["per_step"]
        c["aged_to"] += step
        out.append({"age": c["aged_to"], "changes": {k: ch[k] for k in sorted(ch)}})
    return out


def add_wear(d: Data, c: dict, hard_seasons: int) -> None:
    """A season's hardship: hard_season Wear for each."""
    c["wear"] = c.get("wear", 0) + hard_seasons * _A(d).get("wear", {}).get("hard_season", 1)


def worn_out(d: Data, c: dict, years: float, roll: int) -> dict:
    """The Worn Out check for `years` of service just ended (stats must be current).
    -> {"checked", "threshold", "roll", "worn", "why"}"""
    O = _A(d).get("worn_out")
    s, age, wear = c["stats"], c["age"], c.get("wear", 0)
    out = {"checked": False, "threshold": 0, "roll": roll, "worn": False, "why": ""}
    if not O:
        return out
    if age >= O["end_age"] and min(s["str"], s["agi"], s["end"]) < O["any_below"]:
        return {**out, "checked": True, "worn": True, "why": "broken down: too weak to serve"}
    if age >= O["end_age"] and s["end"] < O["end_below"]:
        return {**out, "checked": True, "worn": True, "why": "worn out: his wind is gone"}
    if age < O["age"] and wear < O["wear"]:
        return out
    t = (wear * O["per_wear"] + max(0, age - O["age"]) * O["per_year"] - (s["end"] - 50) / O["end_per"]) * years / 4
    t = max(0, int(t))
    worn = roll <= t
    return {**out, "checked": True, "threshold": t, "worn": worn, "why": "worn out by service" if worn else ""}
