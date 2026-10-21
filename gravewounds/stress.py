"""Combat stress (data/stress.yaml): Strain from fighting and loss, part of it into a lasting Toll;
a Nerve check each time Strain + Toll passes a multiple of check_every; results from shaken to a
breakdown; rest, treatment (with return-to-duty odds), rotation and homecoming. The pages
(templates/ranks.js) repeat add, rest, treat and relieve exactly, taking the dice in the same
order: for each threshold passed, the d100, and on a failure the d10."""
from __future__ import annotations

import math

from .model import Data

STATES = ("shaken", "strained", "exhaustion", "severe")


def _cfg(d: Data) -> dict:
    return d.stress or {}


def new() -> dict:
    return {"strain": 0.0, "toll": 0.0, "state": None, "broke": False}


def total(st: dict) -> float:
    return st["strain"] + st["toll"]


def _result(d: Data, roll10: int, margin: int) -> str:
    n = roll10 + margin // 10
    return next(r["id"] for r in _cfg(d)["results"] if n <= r["to"])


def _worse(a: str | None, b: str) -> str:
    return b if a is None or STATES.index(b) > STATES.index(a) else a


def add(d: Data, st: dict, amount: float, nerve: int, rng) -> list[dict]:
    """Strain (and its share of Toll) for a man of `nerve`; a check at each multiple passed.
    -> [{"at", "roll", "target", "held", "result"}] (st changed in place)"""
    S = _cfg(d)
    before = total(st)
    st["strain"] += amount
    st["toll"] += amount * S["toll_share"]
    out = []
    every = S["check_every"]
    for k in range(math.floor(before / every) + 1, math.floor(total(st) / every) + 1):
        at = k * every
        target = nerve + S["base"] - at - (S["relapse"] if st.get("broke") else 0)
        roll = rng.randint(1, 100)
        held = roll <= target and roll < S["fail_from"]
        row = {"at": at, "roll": roll, "target": target, "held": held, "result": None}
        if not held:
            row["result"] = _result(d, rng.randint(1, 10), max(0, roll - target))
            st["state"] = _worse(st.get("state"), row["result"])
            if row["result"] in ("exhaustion", "severe"):
                st["broke"] = True
        out.append(row)
    return out


def rest(d: Data, st: dict, days: int) -> None:
    """Days out of the line: rest_day Strain off each (never under 0); a day's rest ends Shaken."""
    if days <= 0:
        return
    st["strain"] = max(0.0, st["strain"] - _cfg(d)["rest_day"] * days)
    if st.get("state") == "shaken":
        st["state"] = None


def treatments(d: Data, eid: str) -> list[str]:
    """The treatments an era had."""
    return [k for k, t in _cfg(d)["treatment"].items() if not t.get("eras") or eid in t["eras"]]


def treat(d: Data, st: dict, where: str, roll: int) -> dict:
    """Treatment of his state: Strain lifted, and back to duty on d100 at or under its chance.
    -> {"rtd", "chance", "roll", "days"}"""
    T = _cfg(d)["treatment"][where]
    chance = T["rtd"].get(st.get("state") or "shaken", 0)
    st["strain"] = 0.0 if T["strain"] == "all" else max(0.0, st["strain"] - T["strain"])
    if T.get("toll"):
        st["toll"] *= T["toll"]
    rtd = roll <= chance
    if rtd:
        st["state"] = None
    return {"rtd": rtd, "chance": chance, "roll": roll, "days": T["days"]}


def relieve(d: Data, st: dict, kind: str) -> None:
    """Rotation home or a homecoming: Strain gone, Toll cut, the state lifted."""
    R = _cfg(d)[kind]
    st["strain"] = 0.0
    st["toll"] *= R["toll"]
    st["state"] = None
