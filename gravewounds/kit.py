"""Boots and clothing wear out (data/kit.yaml). The travel page and the team builder
(templates/ranks.js) repeat day, state, mend and renews exactly."""
from __future__ import annotations

import math
import re

from .model import Data


def _cfg(d: Data) -> dict:
    return d.kit or {}


def _r(x: float) -> float:
    return math.floor(x * 1000 + 0.5) / 1000


def day(d: Data, eid: str, wear: dict, marched: float, wet: bool, hard: bool) -> dict:
    """A day's wear: boots if he marched, more on wet ground; clothing every day, twice on a hard
    night. -> new {boots, clothing}"""
    K, out = _cfg(d), {"boots": wear.get("boots", 0), "clothing": wear.get("clothing", 0)}
    if marched >= K["boots"]["march_hours"]:
        out["boots"] = _r(min(1, out["boots"] + (K["boots"]["wet"] if wet else 1) / K["boots"]["life"].get(eid, 60)))
    out["clothing"] = _r(min(1, out["clothing"] + (K["clothing"]["hard"] if hard else 1) / K["clothing"]["life"].get(eid, 120)))
    return out


def state(d: Data, w: float) -> str:
    """good, worn or out."""
    if w >= 1:
        return "out"
    return "worn" if w >= _cfg(d)["worn"] else "good"


def blister_mult(d: Data, w: float) -> float:
    """What his boots do to his chance of blistered feet."""
    s = state(d, w)
    return 1 if s == "good" else _cfg(d)["boots"]["blister"][s]


def shelter_loss(d: Data, w: float) -> int:
    """Steps of shelter his clothing takes off his night."""
    s = state(d, w)
    return 0 if s == "good" else _cfg(d)["clothing"]["shelter"][s]


def mend(d: Data, w: float, success: bool, fumble: bool) -> float:
    """A day's Mend kit: a success takes `mend` off; a fumble ruins it."""
    if fumble:
        return 1
    return _r(max(0, w - _cfg(d)["mend"])) if success else w


def renews(d: Data, name: str) -> str | None:
    """boots or clothing, if a price-list row by this name replaces it, else None."""
    for k, pat in (_cfg(d).get("renew") or {}).items():
        if re.search(pat, name, re.I):
            return k
    return None
