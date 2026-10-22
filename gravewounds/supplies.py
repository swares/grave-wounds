"""Supplies a force carries between fights (data/supplies.yaml): ammunition (a share of full
loads), rations (days a man), water (litres a man) and medical stores (a share). The travel page
(templates/ranks.js) repeats start, water_need, day, refill and medical_short exactly."""
from __future__ import annotations

import math

from .model import Data


def _cfg(d: Data) -> dict:
    return d.supplies or {}


def start(d: Data, eid: str) -> dict:
    """A force's supplies full: {ammo, rations, water, med}."""
    S = _cfg(d)
    return {"ammo": 1, "rations": S["rations"]["carried"].get(eid, 3), "water": S["water"]["carried"].get(eid, 1), "med": 1}


def water_need(d: Data, high: float) -> float:
    """Litres a marching man needs today, by the day's high."""
    return next(b["l"] for b in _cfg(d)["water"]["need"] if high <= b["upto"])


def _r(x: float) -> float:
    """To a thousandth, halves up (as the page's Math.round)."""
    return math.floor(x * 1000 + 0.5) / 1000


def day(d: Data, eid: str, sup: dict, fed: bool, foraged: bool, water_here: bool, high: float, men: int, wounded: int, sick: int) -> dict:
    """A day's use: rations unless fed or foraged; water unless by water (then filled); medical
    stores by the new wounded and the sick. -> {"sup", "hungry", "thirsty", "short"}"""
    S, out = _cfg(d), dict(sup)
    hungry = False
    if not fed and not foraged:
        if out["rations"] <= 0:
            hungry = True
        out["rations"] = max(0, out["rations"] - 1)
    thirsty = False
    if water_here:
        out["water"] = S["water"]["carried"].get(eid, 1)
    else:
        left = out["water"] - water_need(d, high)
        thirsty = left < 0
        out["water"] = _r(max(0, left))
    M = S["medical"]
    cap = max(1, men) / 100 * M["cases"]
    out["med"] = _r(max(0, out["med"] - (wounded + sick * M["sick_day"]) / cap))
    return {"sup": out, "hungry": hungry, "thirsty": thirsty, "short": out["med"] <= 0}


def refill(d: Data, eid: str, sup: dict, men: int, stock: dict | None = None) -> dict:
    """Filled at a depot (stock None), or from a train's stock (its days of rations, loads of
    ammunition and fills of medical stores for `serves` men), each as far as it goes.
    -> {"sup", "stock"}"""
    full, out = start(d, eid), dict(sup)
    if stock is None:
        out.update(ammo=1, rations=full["rations"], med=1)
        return {"sup": out, "stock": None}
    st, share = dict(stock), max(1, men) / _cfg(d)["train"]["serves"]
    for k, cap in (("rations", full["rations"]), ("ammo", 1), ("med", 1)):
        key = "medical" if k == "med" else k
        want = cap - out[k]
        if want <= 0 or st[key] <= 0:
            continue
        got = min(want, st[key] / share)
        out[k] = _r(out[k] + got)
        st[key] = _r(st[key] - got * share)
    return {"sup": out, "stock": st}


def train_stock(d: Data) -> dict:
    """A baggage train's stock when full."""
    T = _cfg(d)["train"]
    return {"rations": T["rations"], "ammo": T["ammo"], "medical": T["medical"]}


def medical_short(d: Data, sup: dict) -> bool:
    return sup.get("med", 1) <= 0
