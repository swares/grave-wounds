"""Prisoners (data/prisoners.yaml): the roll on capture by the captor's situation, and each season
of captivity: release, an escape if he tries, the death check, Strain and the toll on his health;
ransom by rank, officers' parole, and an offer of service in the captor's army. The team builder
(templates/ranks.js) repeats capture, season and ransom_days exactly, taking the dice in the same
order: the release d100; if he tries, the break-out and home-run d100s and on recapture the
d100 for his life; then the death d100."""
from __future__ import annotations

import math

from .model import Data


def _cfg(d: Data) -> dict:
    return d.prisoners or {}


def contexts(d: Data, eid: str) -> list[dict]:
    return (_cfg(d).get("eras") or {}).get(eid) or []


def context(d: Data, eid: str, cid: str | None) -> dict:
    cs = contexts(d, eid)
    return next((c for c in cs if c["id"] == cid), cs[0] if cs else {})


def capture(d: Data, eid: str, cid: str, circumstances, roll: int) -> dict:
    """On capture: d100 less the circumstances (a stormed garrison makes it worse, a formal
    surrender better) against the context's bands: at or under the first, killed; the second,
    stripped; else held. -> {"roll", "total", "result": killed | stripped | held}"""
    C, ctx = _cfg(d), context(d, eid, cid)
    mods = sum(C["circumstances"][k]["mod"] for k in circumstances
               if k in C["circumstances"] and (not C["circumstances"][k].get("ransom_only") or ctx.get("ransom")))
    total = roll - mods
    k, s = ctx["capture"]
    result = "killed" if total <= k else "stripped" if total <= s else "held"
    return {"roll": roll, "total": total, "result": result}


def hazard(d: Data, ctx: dict, p: dict, winter: bool) -> float:
    """His death hazard this season (%): the context's (its `after` once past the first seasons),
    doubled in a hard winter, halved for an officer, a quarter on parole, + recaptures."""
    C = _cfg(d)
    h = ctx["hazard"] if p.get("seasons", 0) == 0 or "after" not in ctx else ctx["after"]
    if winter:
        h *= 2
    if p.get("parole"):
        h *= C["parole_hazard"]
    elif p.get("officer"):
        h *= C["officer_hazard"]
    return h + C["recapture_hazard"] * p.get("recaptured", 0)


def season(d: Data, eid: str, p: dict, rng, escape: bool = False, stealth: int = 0, fieldcraft: int = 0, winter: bool = False) -> dict:
    """A season of captivity for prisoner record p (changed in place: seasons, recaptured, harsh).
    -> {"out": released | escaped | died | None, "rolls": {...}, "hazard", "harsh"}"""
    C, ctx = _cfg(d), context(d, eid, p.get("ctx"))
    rolls = {}
    h = hazard(d, ctx, p, winter)
    harsh = h >= C["harsh_hazard"]
    p["seasons"] = p.get("seasons", 0) + 1
    if p.get("serving"):
        rolls["desert"] = rng.randint(1, 100)
        out = "escaped" if rolls["desert"] <= C["service_desert"] else None
        return {"out": out, "rolls": rolls, "hazard": 0, "harsh": False}
    rolls["release"] = rng.randint(1, 100)
    if rolls["release"] <= ctx["release"]:
        return {"out": "released", "rolls": rolls, "hazard": h, "harsh": harsh}
    if escape:
        rolls["break"] = rng.randint(1, 100)
        if rolls["break"] <= stealth + ctx["escape"]:
            rolls["home"] = rng.randint(1, 100)
            if rolls["home"] <= fieldcraft + ctx["home"]:
                return {"out": "escaped", "rolls": rolls, "hazard": h, "harsh": harsh}
            p["recaptured"] = p.get("recaptured", 0) + 1
            rolls["life"] = rng.randint(1, 100)
            if rolls["life"] <= ctx["recapture"]:
                return {"out": "died", "rolls": rolls, "hazard": h, "harsh": harsh, "why": "killed when retaken"}
    rolls["death"] = rng.randint(1, 100)
    if rolls["death"] <= h:
        return {"out": "died", "rolls": rolls, "hazard": h, "harsh": harsh, "why": "died in captivity"}
    return {"out": None, "rolls": rolls, "hazard": h, "harsh": harsh}


def ransom_days(d: Data, eid: str, cid: str, day_pay: float, rank_index: int) -> float | None:
    """His ransom in Days, where the context had ransom: `years` of his pay (+ upkeep), or
    `months_per_rank` months of it for each step of rank, or a fixed `days`."""
    R = context(d, eid, cid).get("ransom")
    if not R:
        return None
    if "days" in R:
        return R["days"]
    if "months_per_rank" in R:
        return _q(R["months_per_rank"] * 30 * max(1, day_pay) * (rank_index + 1))
    return _q(R["years"] * 365 * max(1, day_pay) * (1 + R.get("upkeep", 0)))


def _q(x: float) -> float:
    return math.floor(x * 4 + 0.5) / 4
