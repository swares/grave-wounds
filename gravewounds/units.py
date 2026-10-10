"""Unit combat (Grave Wounds): the rank and file fight as units, resolved in bulk once an
exchange (about a minute). Only the men actually striking roll, and each telling blow goes
through the individual rules: attack and defence d100, a critical cannot be parried, the
margin sets severity, then hit location, mechanism and armour from the battle's tables
(gravewounds.engine.roll_hit). Numbers are in data/units.yaml; see docs/units.md.

A side is {table, weapon, kit, quality, shield (bool or None), attack (extra %), defence
(extra %)}. The field map (or the GM) says how many men are striking: see fighters()."""
from __future__ import annotations

import math
import random

from .combat import weapon_reach
from .engine import roll_hit
from .model import Data


def quality(d: Data, q: str) -> dict:
    return d.units["quality"][q]


def fighters(d: Data, front: int, reach: int) -> int:
    """Men striking in melee: the `front` men in the front rank touching the enemy, and the
    second rank too with reach-2 weapons."""
    return front * (2 if reach >= d.units["melee"]["second_rank_reach"] else 1)


def field_range(d: Data, wid: str, field_hexes: int) -> dict | None:
    """A weapon's range band at this many field-map hexes (weapon ranges are battle-map hexes)."""
    return weapon_reach(d, wid, field_hexes * d.units["range_scale"])


def _count(n: float, rng: random.Random) -> int:
    """n blows, with the fraction rounded by chance (so tempo works on small units too)."""
    whole = math.floor(n)
    return whole + (1 if rng.random() < n - whole else 0)


def _new_tally() -> dict:
    return {"blows": 0, "missed": 0, "parried": 0, "stopped": 0, "hits": 0,
            "light": 0, "serious": 0, "critical": 0, "down": 0, "dead": 0}


def _wound(d: Data, att: dict, dfd: dict, margin: int, critical: bool, rng: random.Random, t: dict) -> None:
    """One blow that got through: roll it, then the stop check and death."""
    h = roll_hit(d, att["table"], att["weapon"], rng=rng, kit=dfd.get("kit"), margin=margin,
                 critical=critical, shield=dfd.get("shield"))
    sev = h["severity"]
    if sev == "stopped":
        t["stopped"] += 1
        return
    t["hits"] += 1
    t[sev] += 1
    if h["effects"]["lethal"] in d.units["dead_if"]:
        t["dead"] += 1
        t["down"] += 1
        return
    if sev == "light" or h["graze"]:
        return
    nerve = quality(d, dfd["quality"])["nerve"] - (10 if sev == "critical" else 0)
    if rng.randint(1, 100) > nerve:
        t["down"] += 1


def melee(d: Data, att: dict, dfd: dict, men: int, rng: random.Random, situation: str = "front",
          charge: bool = False, shaken: bool = False, rout: bool = False) -> dict:
    """One exchange of `men` striking at a unit. situation: front, flank or rear. rout: the
    defender is broken and fleeing: then `men` should be all the pursuers, who strike in open
    order. Returns a tally of blows and what they did."""
    M, U = d.units["melee"], d.units
    tempo, atk = M["tempo"], quality(d, att["quality"])["attack"] + att.get("attack", 0)
    dfn = quality(d, dfd["quality"])["defence"] + dfd.get("defence", 0)
    if situation in ("flank", "rear"):
        atk += M[situation]["attack"]
        dfn += M[situation]["defence"]
    if charge:
        atk += M["charge"]["attack"]
        tempo *= M["charge"]["tempo"]
    if shaken:
        atk += M["shaken"]["attack"]
    if rout:
        atk += U["rout"]["attack"]
        tempo *= U["rout"]["tempo"]
        dfn = 0
    return _blows(d, att, dfd, _count(men * tempo, rng), atk, dfn, rng)


def volley(d: Data, att: dict, dfd: dict, men: int, field_hexes: int, rng: random.Random,
           penalty: int = 0) -> dict | None:
    """One exchange of `men` shooting at a unit `field_hexes` away. penalty: extra % off
    (weather, cover). None if out of range."""
    band = field_range(d, att["weapon"], field_hexes)
    if band is None:
        return None
    S = d.units["missile"]
    shots = men * S["rate"].get(att["weapon"], S["default_rate"]) * S["tempo"]
    atk = quality(d, att["quality"])["attack"] + att.get("attack", 0) - band["penalty"] - penalty
    return _blows(d, att, dfd, _count(shots, rng), atk, 0, rng)


def _blows(d: Data, att: dict, dfd: dict, n: int, atk: int, dfn: int, rng: random.Random) -> dict:
    t = _new_tally()
    t["blows"] = n
    crit_at = d.wounds["combat"]["critical_fraction"]
    for _ in range(n):
        r = rng.randint(1, 100)
        if r > atk:
            t["missed"] += 1
            continue
        critical = r <= atk * crit_at
        if not critical and dfn > 0 and rng.randint(1, 100) <= dfn:
            t["parried"] += 1
            continue
        _wound(d, att, dfd, atk - r, critical, rng, t)
    return t


def morale(d: Data, unit: dict, roll: int) -> dict:
    """A unit's check after an exchange. unit: {quality, start, down (all so far), lost (this
    exchange), dealt (enemy put down by it this exchange), men (before this exchange), state
    (steady, shaken or broken), leader (None, up or down), flanked, friends (a steady friend
    beside it), contact}. Returns {check (bool),
    target, state}."""
    M = d.units["morale"]
    if unit["state"] == "broken":
        return {"check": False, "target": None, "state": "broken"}
    losing = unit.get("lost", 0) > unit.get("dealt", 0) and unit.get("contact")
    struck = (unit["down"] >= M["trigger"] * unit["start"] or unit["lost"] >= M["shock"] * max(1, unit["men"])
              or unit.get("flanked") or losing)
    rally = unit["state"] == "shaken" and not unit.get("contact")
    if not struck and not rally:
        return {"check": False, "target": None, "state": unit["state"]}
    target = quality(d, unit["quality"])["nerve"] + _morale_mods(M["mods"], unit)
    if roll <= target:
        return {"check": True, "target": target, "state": "steady" if rally and not struck else unit["state"]}
    return {"check": True, "target": target, "state": _failed(M, unit, roll - target)}


def _failed(mo: dict, unit: dict, by: int) -> str:
    """A failed check: a steady unit is shaken, unless it fails badly while flanked or with
    half its men down; a shaken unit breaks."""
    if unit["state"] == "shaken":
        return "broken"
    hard = unit.get("flanked") or unit["down"] >= unit["start"] / 2
    return "broken" if hard and by > mo["shaken_by"] else "shaken"


def _morale_mods(mods: dict, unit: dict) -> int:
    m = 0
    if unit.get("leader") == "up":
        m += mods["leader"]
    elif unit.get("leader") == "down":
        m += mods["leader_down"]
    if unit["down"] >= unit["start"] / 2:
        m += mods["heavy"]
    if unit.get("flanked"):
        m += mods["flank"]
    if unit.get("friends"):
        m += mods["veteran_friends"]
    if unit.get("state") == "steady":
        m += mods["in_order"]
    m -= min(mods["losing_cap"], mods["losing_per_man"] * max(0, unit.get("lost", 0) - unit.get("dealt", 0)))
    return m


def fight(d: Data, a: dict, b: dict, rng: random.Random, exchanges: int = 60, front: int = 30) -> dict:
    """Two units in a straight melee, front to front, until one breaks or `exchanges` pass;
    then the winner pursues for one exchange. a and b: sides plus {men, reach}. For tuning
    and examples: {exchanges, a: {...}, b: {...}, broke}."""
    st = {k: {"men": u["men"], "start": u["men"], "down": 0, "dead": 0, "hits": 0, "state": "steady",
              "quality": u["quality"], "leader": u.get("leader")} for k, u in (("a", a), ("b", b))}
    n = 0
    for n in range(1, exchanges + 1):
        ta = melee(d, a, b, min(fighters(d, front, a.get("reach", 1)), st["a"]["men"]), rng, shaken=st["a"]["state"] == "shaken")
        tb = melee(d, b, a, min(fighters(d, front, b.get("reach", 1)), st["b"]["men"]), rng, shaken=st["b"]["state"] == "shaken")
        st["a"]["dealt"], st["b"]["dealt"] = ta["down"], tb["down"]
        for side, t in (("b", ta), ("a", tb)):
            s = st[side]
            s["lost"], s["hits"] = t["down"], s["hits"] + t["hits"]
            s["down"] += t["down"]
            s["dead"] += t["dead"]
        for side in ("a", "b"):
            s = st[side]
            s["state"] = morale(d, {**s, "contact": True}, rng.randint(1, 100))["state"]
            s["men"] -= s["lost"]
        broke = [k for k in ("a", "b") if st[k]["state"] == "broken"]
        if broke:
            loser = broke[0]
            _pursue(d, (b, a) if loser == "a" else (a, b), st["b" if loser == "a" else "a"], st[loser], rng)
            return {"exchanges": n, "a": st["a"], "b": st["b"], "broke": loser}
    return {"exchanges": n, "a": st["a"], "b": st["b"], "broke": None}


def _pursue(d: Data, sides: tuple, ws: dict, ls: dict, rng: random.Random) -> None:
    """The winner cuts down the fleeing loser for rout.exchanges exchanges, all its men striking."""
    w, lo = sides
    for _ in range(d.units["rout"]["exchanges"]):
        if ls["men"] <= 0:
            return
        t = melee(d, w, lo, ws["men"], rng, rout=True)
        cut = min(t["down"], ls["men"])
        ls["down"] += cut
        ls["dead"] += min(t["dead"], cut)
        ls["men"] -= cut


class SeededDice:
    """Repeatable dice for simulations and examples (Park-Miller minimal standard), with the
    two calls the rules use: randint(a, b) and random(). Play uses real random dice."""

    def __init__(self, seed: int):
        self.state = max(1, seed % 2147483647)

    def _next(self) -> int:
        self.state = self.state * 16807 % 2147483647
        return self.state

    def randint(self, a: int, b: int) -> int:
        return a + self._next() % (b - a + 1)

    def random(self) -> float:
        return self._next() / 2147483647


EXAMPLES = [   # (label, a, b) for `python3 -m gravewounds units`: 120 men a side, 30 abreast
    ("Equal regulars, no armour", {"quality": "regular", "kit": "none"}, {"quality": "regular", "kit": "none"}),
    ("Equal regulars in jacks", {"quality": "regular", "kit": "jack_sallet"}, {"quality": "regular", "kit": "jack_sallet"}),
    ("Regulars v greens, in jacks", {"quality": "regular", "kit": "jack_sallet"}, {"quality": "green", "kit": "jack_sallet"}),
    ("Bills v swords, in jacks", {"quality": "regular", "kit": "jack_sallet", "weapon": "bill", "reach": 2},
     {"quality": "regular", "kit": "jack_sallet"}),
    ("Veterans in mail v unarmoured regulars", {"quality": "veteran", "kit": "hauberk"}, {"quality": "regular", "kit": "none"}),
]


def examples(d: Data, table: str, runs: int, seed: int) -> list[dict]:
    """The example matchups, each fought `runs` times: medians of minutes to a break and of
    men down on each side, and how often each side broke."""
    out = []
    for label, a, b in EXAMPLES:
        side = lambda x: {"table": table, "weapon": "sword", "men": 120, "reach": 1, **x}
        rs = [fight(d, side(a), side(b), SeededDice(seed + i), exchanges=120) for i in range(runs)]
        done = [r for r in rs if r["broke"]]
        med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
        out.append({"label": label, "minutes": med([r["exchanges"] for r in rs]),
                    "a_broke": sum(1 for r in rs if r["broke"] == "a"), "b_broke": sum(1 for r in rs if r["broke"] == "b"),
                    "winner_down": med([r["b" if r["broke"] == "a" else "a"]["down"] for r in done]),
                    "loser_down": med([r[r["broke"]]["down"] for r in done])})
    return out


def pace(d: Data, table: str, kit: str, exchanges: int, seed: int) -> dict:
    """% of the men in contact hit, and put down, a minute: regular swordsmen, front to front."""
    rng, side = SeededDice(seed), {"table": table, "weapon": "sword", "quality": "regular"}
    hits = down = 0
    for _ in range(exchanges):
        t = melee(d, side, {**side, "kit": kit}, 10, rng)
        hits, down = hits + t["hits"], down + t["down"]
    return {"hit": 100 * hits / (10 * exchanges), "down": 100 * down / (10 * exchanges)}
