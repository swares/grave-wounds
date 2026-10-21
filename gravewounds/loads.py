"""Carrying weight (data/loads.yaml): a man's load in his era's order (fighting, marching or full
kit) plus his armour where the orders leave it out, against his body weight and Strength, falls in
a band; the band slows and tires a march, blisters the feet, and costs Dodge and the run in a fight
(a green man under fire a band heavier). The team builder, the roller and the travel map
(templates/ranks.js) repeat load_kg, band_of, blister_chance and extra_fatigue exactly."""
from __future__ import annotations

from .model import Data


def _cfg(d: Data) -> dict:
    return d.loads or {}


def era_loads(d: Data, eid: str) -> dict:
    return (_cfg(d).get("eras") or {}).get(eid) or {}


def kit_class(d: Data, kit: str | None) -> str:
    """light, medium or heavy: the kit's load for toil (wounds.yaml), light if not listed."""
    return d.wounds["combat"]["characteristics"]["toil"]["load"].get(kit or "", "light")


def load_kg(d: Data, eid: str, order: str, kit: str | None, extra: float = 0) -> float:
    """His load in kg: his era's order, his armour where the orders leave it out, and the GM's extra."""
    E = era_loads(d, eid)
    kg = (E.get("kg") or {}).get(order, 0) + extra
    if not E.get("armour_in_orders"):
        kg += _cfg(d).get("armour_kg", {}).get(kit_class(d, kit), 0)
    return kg


def body_kg(d: Data, eid: str, sex: str = "m") -> float:
    return era_loads(d, eid).get("body_kg", 65) + (_cfg(d).get("woman_kg", 0) if sex == "f" else 0)


def strength_mult(d: Data, strength: int) -> float:
    return [r for r in _cfg(d)["strength"] if strength >= r["from"]][-1]["mult"]


def band_of(d: Data, load: float, body: float, strength: int, afraid: bool = False) -> int:
    """The band's index: load / (body x Strength's multiplier) against the bands' shares; a green man
    under fire one band heavier."""
    B = _cfg(d)["bands"]
    r = load / (body * strength_mult(d, strength))
    i = next(k for k, b in enumerate(B) if r <= b["upto"])
    return min(len(B) - 1, i + (1 if afraid else 0))


def blister_chance(d: Data, band: int, km: float, days_marched: int = 0) -> int:
    """% chance of blistered or hurt feet after `km` of a day's march in this band: the band's for
    20 km or more; a quarter once his feet have hardened (hardened_days days on the march)."""
    p = _cfg(d)["bands"][band].get("blister", 0) * min(km, 20) / 20
    if days_marched >= _cfg(d).get("hardened_days", 7):
        p /= 4
    return int(p)


def extra_fatigue(d: Data, band: int, km: float) -> int:
    """Steps of fatigue a day's `km` add in this band (none for a light load)."""
    fk = _cfg(d)["bands"][band].get("fatigue_km")
    return int(km // fk) if fk else 0
