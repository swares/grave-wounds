"""Skill checks out of a fight (data/checks.yaml): the one roll with a difficulty, criticals and
fumbles, rolls of one man against another, haggling at the price list, and the table of what
each skill is used for. The team builder page (templates/team.js) repeats check, opposed and
haggle exactly."""
from __future__ import annotations

import math

from .model import Data

STATS = ("str", "agi", "end", "wits", "nerve", "pres")
OUTCOMES = ("win", "critical", "list", "no_sale", "cheated")


def _C(d: Data) -> dict:
    return d.checks or {"critical_fraction": 0.1, "fumble_from": 96, "difficulty": [{"id": "ordinary", "mod": 0}]}


def mod_of(d: Data, difficulty: str) -> int:
    """The difficulty's modifier (0 for one not in the table)."""
    return next((x["mod"] for x in _C(d)["difficulty"] if x["id"] == difficulty), 0)


def check(d: Data, value: int, difficulty: str, roll: int) -> dict:
    """One check: d100 `roll` against `value` plus the difficulty's modifier.
    -> {"target", "roll", "success", "critical", "fumble", "margin" (target - roll on a success, else None)}"""
    C = _C(d)
    target = max(0, value + mod_of(d, difficulty))
    ok = roll <= target
    return {"target": target, "roll": roll, "success": ok, "critical": ok and roll <= int(target * C["critical_fraction"]),
            "fumble": (not ok) and roll >= C["fumble_from"], "margin": target - roll if ok else None}


def _rank(c: dict) -> tuple:
    return (c["success"], c["critical"], c["margin"] if c["success"] else 0)


def opposed(d: Data, a_value: int, a_diff: str, a_roll: int, b_value: int, b_roll: int) -> dict:
    """The acting side (a, at its difficulty) against the side resisting (b, ordinary): a wins only
    by beating b (a success over a failure, a critical over a plain success, or a wider margin);
    a tie or both failing goes to b. -> {"a": check, "b": check, "winner": "a" or "b"}"""
    a, b = check(d, a_value, a_diff, a_roll), check(d, b_value, "ordinary", b_roll)
    return {"a": a, "b": b, "winner": "a" if _rank(a) > _rank(b) else "b"}


def _q(x: float) -> float:
    return math.floor(x * 4 + 0.5) / 4


def _sell(cfg: dict, price: float, o: dict) -> dict:
    """Selling loot: a tenth more on a win, a quarter on a critical; a fumble, a fence cheats him."""
    S = cfg.get("sell") or {"win": 0.1, "critical": 0.25, "fumble": -0.25}
    kind = "list"
    if o["a"]["fumble"]:
        kind = "cheated"
    elif o["winner"] == "a":
        kind = "critical" if o["a"]["critical"] else "win"
    rate = {"cheated": S["fumble"], "win": S["win"], "critical": S["critical"]}.get(kind, 0)
    return {"outcome": kind, "price": _q(price * (1 + rate)), "opposed": o}


def haggle(d: Data, price: float, persuade: int, a_roll: int, b_roll: int, seller: int | None = None, selling: bool = False) -> dict:
    """Haggling over `price` Days: his Persuade against the other side's. Buying, a win takes a
    tenth off (a quarter on a critical) and a fumble means no sale today; selling (`sell`), a win
    gets a tenth more (a quarter on a critical) and a fumble lets a fence cheat him of a quarter.
    -> {"outcome": win | critical | list | no_sale | cheated, "price" (Days, to the quarter; None for no sale), "opposed"}"""
    H = _C(d).get("haggle") or {"seller": 50, "win": -0.1, "critical": -0.25}
    o = opposed(d, persuade, "ordinary", a_roll, H["seller"] if seller is None else seller, b_roll)
    if selling:
        return _sell(H, price, o)
    if o["a"]["fumble"]:
        return {"outcome": "no_sale", "price": None, "opposed": o}
    if o["winner"] == "a":
        kind = "critical" if o["a"]["critical"] else "win"
        return {"outcome": kind, "price": max(0.25, math.floor(price * (1 + H[kind]) * 4 + 0.5) / 4) if price > 0 else 0, "opposed": o}
    return {"outcome": "list", "price": price, "opposed": o}


def uses(d: Data, eid: str) -> list[dict]:
    """The uses of skills in an era: those whose skill (or characteristic) the era has."""
    have = {s["id"] for s in d.teams[eid]["skills"]} | set(STATS)
    return [u for u in _C(d).get("uses", []) if u["skill"] in have]


def use_rows(d: Data, eid: str) -> list[list[str]]:
    """The uses table for the rule book: head row, then one a use."""
    T = d.teams[eid]
    names = {s["id"]: s["name"] for s in T["skills"]} | {c["id"]: c["name"] for c in T["characteristics"]}
    diff = {x["id"]: x["name"] for x in _C(d)["difficulty"]}
    rows = [["Skill", "Use", "Usually", "Against", "Success", "Failure", "Fumble"]]
    for u in uses(d, eid):
        ag = u.get("against")
        against = f"{u['against'].get('who', '')} ({names.get(ag.get('skill') or ag.get('stat'), '')})" if ag else "—"
        rows.append([names[u["skill"]], f"**{u['name']}**: {u['what']}", diff[u["difficulty"]], against, u["success"], u["failure"], u["fumble"]])
    return rows
