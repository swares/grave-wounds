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


def _cfg(d: Data) -> dict:
    return d.ageing or {}


def _roll(rng, dice) -> int:
    return sum(rng.randint(1, dice[1]) for _ in range(dice[0]))


def _decline(band: dict, wear: int, wcfg: dict, rng, ch: dict) -> None:
    """The band's losses into ch: Endurance twice, the worse, with heavy Wear."""
    for k in DECLINE_ORDER:
        if not band.get(k):
            continue
        n = _roll(rng, band[k])
        if k == "end" and wear >= wcfg["end_twice"]:
            n = max(n, _roll(rng, band[k]))
        ch[k] = ch.get(k, 0) - n


def _mature(mid: float, mcfg: dict, mat: dict, ch: dict) -> None:
    """A step of maturity into ch, from mcfg["from"] to each one's `to`, at most its cap."""
    if mid < mcfg["from"]:
        return
    for k in MATURE_ORDER:
        if mid >= mcfg[k]["to"] or mat.get(k, 0) >= mcfg[k]["cap"]:
            continue
        mat[k] = mat.get(k, 0) + 1
        ch[k] = ch.get(k, 0) + 1


def steps(d: Data, c: dict, rng) -> list[dict]:
    """Every pending step from c["aged_to"] to c["age"] (c changed in place: stat_mods, wear,
    matured, aged_to). -> [{"age", "changes": {stat: +/-n}}]"""
    A = _cfg(d)
    if not A:
        return []
    step, W = A.get("step", 4), A["wear"]
    c.setdefault("aged_to", c["age"])
    c.setdefault("wear", 0)
    mat = c.setdefault("matured", {})
    out = []
    while c["age"] - c["aged_to"] >= step:
        mid = c["aged_to"] + step / 2
        eff = mid + (c["wear"] // W["per"]) * W["add_years"]
        band = [b for b in A["decline"] if eff >= b["from"]][-1]
        ch: dict = {}
        _decline(band, c["wear"], W, rng, ch)
        _mature(mid, A["maturity"], mat, ch)
        for k, v in ch.items():
            c["stat_mods"][k] = c["stat_mods"].get(k, 0) + v
        older = c.get("enlisted", 0) >= (A.get("enlist") or {}).get("older_from", 999)
        c["wear"] += W["per_step"] * ((A.get("enlist") or {}).get("older_wear", 1) if older else 1)
        c["aged_to"] += step
        out.append({"age": c["aged_to"], "changes": {k: ch[k] for k in sorted(ch)}})
    return out


def limits(d: Data, eid: str, region: str) -> dict | None:
    """{min, max} for his army's enlistment (a region's own where it has them), or None."""
    E = ((_cfg(d).get("enlist") or {}).get("eras") or {}).get(eid)
    if not E:
        return None
    R = (E.get("regions") or {}).get(region) or {}
    return {"min": R.get("min", E["min"]), "max": R.get("max", E["max"])}


def enlist(d: Data, eid: str, region: str, start: int, rng) -> dict:
    """His age at enlistment: {"age", "lied"} (lied: "under", "over" or None). The era's start age
    raised to the army's least; then d100 for a boy under age or an older recruit."""
    L = limits(d, eid, region)
    if not L:
        return {"age": start, "lied": None}
    E = _cfg(d)["enlist"]
    sh = E["shares"].get(eid, E["shares"]["default"])
    r = rng.randint(1, 100)
    if r <= sh["under"]:
        return {"age": L["min"] - rng.randint(1, E["under_years"]), "lied": "under"}
    if r > 100 - sh["older"]:
        top = max(E["older_from"], L["max"] + E["over_years"])
        age = rng.randint(E["older_from"], top)
        return {"age": age, "lied": "over" if age > L["max"] else None}
    return {"age": max(start, L["min"]), "lied": None}


def found_out(d: Data, c: dict, roll: int) -> bool:
    """End of season: is a man under or over age found out (d100 at or under found_out)?"""
    return bool(c.get("lied")) and roll <= _cfg(d)["enlist"]["found_out"]


def still_lying(d: Data, c: dict) -> str | None:
    """His lie still stands: a boy until he is of age, an older man through his first term."""
    L = limits(d, c["era"], c["region"])
    if not L or not c.get("lied"):
        return None
    if c["lied"] == "under":
        return "under" if c["age"] < L["min"] else None
    return "over" if c.get("xp_terms", 0) < 1 else None


def add_wear(d: Data, c: dict, hard_seasons: int) -> None:
    """A season's hardship: hard_season Wear for each."""
    c["wear"] = c.get("wear", 0) + hard_seasons * _cfg(d).get("wear", {}).get("hard_season", 1)


def worn_out(d: Data, c: dict, years: float, roll: int) -> dict:
    """The Worn Out check for `years` of service just ended (stats must be current).
    -> {"checked", "threshold", "roll", "worn", "why"}"""
    O = _cfg(d).get("worn_out")
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
