"""Unit combat (Grave Wounds): the rank and file fight as units, resolved in bulk once an
exchange (about a minute). Only the men actually striking roll, and each telling blow goes
through the individual rules: attack and defence d100, a critical cannot be parried, the
margin sets severity, then hit location, mechanism and armour from the battle's tables
(gravewounds.engine.roll_hit). Numbers are in data/units.yaml; see docs/units.md.

A side is {table, weapon, kit, quality, shield (bool or None), attack (extra %), defence
(extra %)}. The field map (or the GM) says how many men are striking: see fighters()."""
from __future__ import annotations

import heapq
import math
import random

from . import combat as C
from .combat import weapon_reach
from .disease import wound_case
from .engine import roll_hit
from .model import Data


def quality(d: Data, q: str) -> dict:
    return d.units["quality"][q]


def fighters(d: Data, front: int, reach: int) -> int:
    """Men striking in melee: the `front` men in the front rank touching the enemy, and one
    more rank for each hex of reach past the first, up to close order's ranks."""
    return front * min(reach, d.units["formations"]["close"]["ranks"])


def field_range(d: Data, wid: str, field_hexes: int, reach: int = 0) -> dict | None:
    """A weapon's range band at this many field-map hexes (weapon ranges are battle-map hexes);
    reach: % on the bands from the wind (with it +, into it -)."""
    return weapon_reach(d, wid, field_hexes * d.units["range_scale"] * 100 / (100 + reach))


def _count(n: float, rng: random.Random) -> int:
    """n blows, with the fraction rounded by chance (so tempo works on small units too)."""
    whole = math.floor(n)
    return whole + (1 if rng.random() < n - whole else 0)


def _new_tally() -> dict:
    return {"blows": 0, "missed": 0, "parried": 0, "stopped": 0, "hits": 0,
            "light": 0, "serious": 0, "critical": 0, "down": 0, "dead": 0, "hurt": {}}


def _hurt(t: dict, sev: str, fx: dict, down: bool) -> None:
    """Remember a wounded man by severity, death clock, infection risk and whether he is down."""
    k = f"{sev}|{fx['lethal']}|{fx['infection']}|{1 if down else 0}"
    t["hurt"][k] = t["hurt"].get(k, 0) + 1


def _wound(d: Data, att: dict, dfd: dict, margin: int, critical: bool, rng: random.Random, t: dict) -> None:
    """One blow that got through: roll it, then the stop check and death."""
    h = roll_hit(d, att["table"], att["weapon"], rng=rng, kit=dfd.get("kit"), margin=margin,
                 critical=critical, shield=dfd.get("shield"))
    sev, modern = h["severity"], att["weapon"] in d.units["modern_fire"]["weapons"]
    if sev == "stopped":
        t["stopped"] += 1
        return
    t["hits"] += 1
    t[sev] += 1
    if h["effects"]["lethal"] in d.units["dead_if"]:
        t["dead"] += 1
        t["down"] += 1
        return
    if h["graze"] or (sev == "light" and not modern):
        _hurt(t, "light", h["effects"], False)
        return
    down = (modern and sev != "light") or rng.randint(1, 100) > quality(d, dfd["quality"])["nerve"] - (10 if sev == "critical" else 0)
    if down:
        t["down"] += 1
    _hurt(t, sev, h["effects"], down)


def _attack(d: Data, side: dict) -> int:
    """A side's attack %: a hero's own skill, else his unit's quality; plus any extra."""
    return side.get("skill", quality(d, side["quality"])["attack"]) + side.get("attack", 0)


def melee(d: Data, att: dict, dfd: dict, men: int, rng: random.Random, situation: str = "front",
          charge: bool = False, shaken: bool = False, rout: bool = False, exposed: tuple = (), penalty: int = 0) -> dict:
    """One exchange of `men` striking at a unit. situation: front, flank or rear. rout: the
    defender is broken and fleeing: then `men` should be all the pursuers, who strike in open
    order. exposed: (hero, chance) for heroes in the struck unit whom a blow may fall on.
    Returns a tally of blows and what they did."""
    M, U = d.units["melee"], d.units
    tempo, atk = M["tempo"], _attack(d, att) - penalty
    base = dfn = quality(d, dfd["quality"])["defence"] + dfd.get("defence", 0)
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
    shift = dfn - base if dfn > 0 else -1000      # a hero's defence moves with his unit's; none if it has none
    return _blows(d, att, dfd, _count(men * tempo, rng), atk, dfn, rng, exposed, shift)


def volley(d: Data, att: dict, dfd: dict, men: float, field_hexes: int, rng: random.Random,
           penalty: int = 0, factor: float = 1.0, exposed: tuple = (), reach: int = 0) -> dict | None:
    """One exchange of `men` shooting at a unit `field_hexes` away (a machine-gun team: its
    served guns, at machine_guns.tempo). penalty: extra % off (weather, cover); factor: the
    target formation's missile_factor; reach: the wind's % on the range bands. None if out of
    range."""
    band = field_range(d, att["weapon"], field_hexes, reach)
    if band is None:
        return None
    S = d.units["missile"]
    tempo = d.units["machine_guns"]["tempo"] if is_mg(d, att["weapon"]) else S["tempo"]
    shots = men * S["rate"].get(att["weapon"], S["default_rate"]) * tempo * factor
    atk = _attack(d, att) - band["penalty"] - penalty
    return _blows(d, att, dfd, _count(shots, rng), atk, 0, rng, exposed, -1000)


def _blows(d: Data, att: dict, dfd: dict, n: int, atk: int, dfn: int, rng: random.Random,
           exposed: tuple = (), shift: int = 0) -> dict:
    t = _new_tally()
    t["blows"] = n
    atk = max(0, atk)
    crit_at = math.floor(atk * d.wounds["combat"]["critical_fraction"])
    for _ in range(n):
        hero = _aimed_at(exposed, rng)
        r = rng.randint(1, 100)
        if hero is not None:
            _hero_blow(d, att, hero, r, atk, crit_at, shift, rng, t)
            continue
        if r > atk:
            t["missed"] += 1
            continue
        critical = r <= crit_at
        if not critical and dfn > 0 and rng.randint(1, 100) <= dfn:
            t["parried"] += 1
            continue
        _wound(d, att, dfd, atk - r, critical, rng, t)
    return t


# ---------- heroes ----------
# A named fighter from the wound roller with a unit: {id, name, role (front, ranged or
# behind), attack, defence, nerve, weapon, kit, leader, state (up, down or dead), wounds}.
# He is extra to the unit's men. Front: strikes with his own skill each time his unit fights
# hand to hand, and blows on his unit's front may fall on him. Ranged: shoots with his own
# skill each time his unit shoots, and is at risk from missiles and in contact. Behind:
# only in a rout. His wounds use the full rules and go back to the roller.

def _aimed_at(exposed: tuple, rng):
    """The hero a blow falls on, or None: each hero still up, in turn, by his chance."""
    for hero, p in exposed:
        if hero["state"] == "up" and rng.random() < p:
            return hero
    return None


def _hero_blow(d: Data, att: dict, hero: dict, r: int, atk: int, crit_at: int, shift: int, rng, t: dict) -> None:
    """A blow aimed at a hero: his own parry (none if stunned; less for his wounds), then the
    full wound roll on his kit, and the roller's stop check."""
    if r > atk:
        return
    critical = r <= crit_at
    dfn = 0 if _held(hero) == "stunned" else hero["defence"] + shift - hero_penalty(d, hero)
    if not critical and dfn > 0 and rng.randint(1, 100) <= dfn:
        return
    h = roll_hit(d, att["table"], att["weapon"], rng=rng, kit=hero.get("kit"), margin=atk - r, critical=critical)
    sev = h["severity"]
    if sev == "stopped":
        return
    fx = h["effects"]
    bleed, pain, shock = (max(0, fx["bleed"] - 1), max(0, fx["pain"] - 1), False) if h["graze"] else (fx["bleed"], fx["pain"], bool(fx.get("shock")))
    hero["wounds"].append({"loc": h["location"], "mech": h["mechanism"], "sev": sev, "graze": h["graze"], "bleed": bleed, "pain": pain})
    if fx["lethal"] in d.units["dead_if"]:
        hero["state"] = "dead"
    else:
        _hero_check(d, hero, C.stop_check(d, hero["nerve"], sev, hero_pain(hero), rng.randint(1, 100) if _checks(d, sev, shock) else 0,
                                          hero_blood(d, hero)[0] / hero_blood(d, hero)[1], shock))
    t.setdefault("heroes", []).append({"hero": hero["id"], "name": hero["name"], "sev": sev, "loc": h["location"],
                                        "graze": h["graze"], "state": hero["state"]})


def _checks(d: Data, sev: str, shock: bool) -> bool:
    """Whether a wound calls for the stop check (so its die is rolled)."""
    return shock and sev in d.wounds["combat"]["stop_check"]["severities"]


def _hero_check(d: Data, hero: dict, res: dict | None) -> None:
    """A stop check's result on a hero: out puts him down; defend only or stunned holds him
    for his next exchange (a worse hold replaces a milder one)."""
    if not res or res["passed"]:
        return
    if res["state"] == "out":
        hero["state"] = "down"
        return
    order = list(d.wounds["combat"]["states"])
    if not hero.get("held") or order.index(res["state"]) >= order.index(hero["held"]["state"]):
        hero["held"] = {"state": res["state"], "left": 2}


def _held(hero: dict) -> str | None:
    """defend_only or stunned while a stop check holds him, else None."""
    h = hero.get("held")
    return h["state"] if h and h["left"] > 0 else None


def hero_pain(hero: dict) -> int:
    """Pain steps: the wounds he came with and those he took here."""
    return hero.get("old_pain", 0) + sum(w.get("pain", 0) for w in hero.get("wounds", []))


def hero_blood(d: Data, hero: dict) -> tuple:
    """(Blood left, his pool)."""
    pool = hero.get("pool") or d.wounds["tracking"]["blood_pool"]
    return hero.get("blood", pool), pool


def _threshold(d: Data, frac: float) -> dict | None:
    return next((t for t in sorted(d.wounds["tracking"]["thresholds"], key=lambda t: t["at"]) if frac <= t["at"]), None)


def hero_penalty(d: Data, hero: dict) -> int:
    """% off his attack and defence: pain (to the cap) and Blood lost."""
    T, C_ = d.wounds["tracking"], d.wounds["combat"]
    blood, pool = hero_blood(d, hero)
    th = _threshold(d, blood / pool)
    return min(hero_pain(hero), T["pain_cap"]) * C_["pain_step"] + ((th or {}).get("penalty") or 0)


def _heroes_after(d: Data, us: list, rng) -> list:
    """End of an exchange for every hero not dead: a hold wears off, he bleeds, his Blood's
    thresholds can put him down, and pain above the cap calls for a stop check."""
    log = []
    for i, u in enumerate(us):
        for hero in u.get("heroes", []):
            line = _hero_after(d, hero, rng) if hero["state"] != "dead" else None
            if line:
                log.append({"kind": "herobled", "unit": i, **line})
    return log


def _hero_after(d: Data, hero: dict, rng) -> dict | None:
    """One hero's end of an exchange; a log line if he crossed a Blood threshold or went down."""
    T = d.wounds["tracking"]
    if hero.get("held"):
        hero["held"]["left"] -= 1
    blood, pool, was_up = *hero_blood(d, hero), hero["state"] == "up"
    lost = hero.get("old_bleed", 0) + sum(round(T["bleed_per_round"][w.get("bleed", 0)] * d.units["exchange_rounds"]) for w in hero["wounds"])
    if not lost and not (was_up and hero_pain(hero) > T["pain_cap"]):
        return None
    before = _threshold(d, blood / pool)
    hero["blood"] = max(0, blood - lost)
    after = _threshold(d, hero["blood"] / pool)
    if was_up and after and (after.get("down") or after.get("incapacitated")):
        hero["state"] = "down"
    if hero["blood"] <= 0:
        hero["dying"] = True
    if hero["state"] == "up" and hero_pain(hero) > T["pain_cap"]:
        _hero_check(d, hero, C.pain_check(d, hero["nerve"], hero_pain(hero), rng.randint(1, 100), hero["blood"] / pool))
    if after is before and not (was_up and hero["state"] != "up"):
        return None
    return {"hero": hero["id"], "name": hero["name"], "lost": lost, "blood": hero["blood"], "pool": pool, "state": hero["state"]}


def _heroes(u: dict, roles: tuple) -> list:
    return [h for h in u.get("heroes", []) if h["state"] == "up" and h["role"] in roles]


def _acting(u: dict, roles: tuple) -> list:
    """Heroes up and not held by a stop check: the ones who strike or shoot this exchange."""
    return [h for h in _heroes(u, roles) if not _held(h)]


def front_men(d: Data, u: dict) -> int:
    """Men in the unit's front rank: the ones a blow on its front falls among."""
    rows, men = footprint(d, u), men_by_hex(d, u)
    return sum(min(form(d, u)["abreast"], men[k]) for k in range(len(rows[0]))) if rows else 0


def _exposure(d: Data, u: dict, rout: bool, missile: bool = False) -> tuple:
    """(hero, chance) for each hero of unit u a blow on it may fall on."""
    if rout or missile:
        return tuple((h, 1 / max(1, u["men"])) for h in _heroes(u, ("front", "ranged", "behind" if rout else "")))
    return tuple((h, min(1, d.units["heroes"]["exposure"] / max(1, front_men(d, u)))) for h in _heroes(u, ("front", "ranged")))


def _hero_side(u: dict, hero: dict, table: str, d: Data | None = None) -> dict:
    """A hero as a fighting side: his own skill, less his wounds' penalty (d given)."""
    pen = hero_penalty(d, hero) if d else 0
    return {"table": table, "weapon": hero["weapon"], "kit": hero.get("kit"), "quality": u["quality"], "skill": hero["attack"] - pen}


def leader_state(u: dict) -> str | None:
    """up if a leader hero of the unit is up, down if it has leaders and none is, else None."""
    ls = [h for h in u.get("heroes", []) if h.get("leader")]
    if not ls:
        return u.get("leader")
    return "up" if any(h["state"] == "up" for h in ls) else "down"


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


# ---------- the field map ----------
# Hexes are [col, row], pointy-top, odd rows shifted right, as on the other maps. A unit is
# {id, name, side, men, start, down, dead, quality, weapon, kit, formation (close or open),
# mounted, width (hexes of front), pos (the middle of its front row), facing (0-5),
# state (steady, shaken, broken or fled), charged}. Facing f points at the corner between
# hexsides f and f+1 (E, NE, NW, W, SW, SE = 0-5): the front is those two sides, the flanks
# the sides along the line (f+2, f+5), the rear the other two (f+3, f+4).

AX = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]   # E, NE, NW, W, SW, SE (axial)


def step(h, dirn: int, n: int = 1) -> list:
    """The hex n steps from h in direction dirn."""
    q, r = h[0] - (h[1] - (h[1] & 1)) // 2, h[1]
    dq, dr = AX[dirn % 6]
    q, r = q + dq * n, r + dr * n
    return [q + (r - (r & 1)) // 2, r]


def _cube(h) -> tuple:
    q = h[0] - (h[1] - (h[1] & 1)) // 2
    return q, h[1], -q - h[1]


def hdist(a, b) -> int:
    x, y = _cube(a), _cube(b)
    return max(abs(x[0] - y[0]), abs(x[1] - y[1]), abs(x[2] - y[2]))


ray = C.ray   # the hexes on a line (gravewounds.combat)


def arc(facing: int, dirn: int) -> str:
    """front, flank or rear: where direction dirn falls for a unit with this facing."""
    k = (dirn - facing) % 6
    if k in (0, 1):
        return "front"
    return "flank" if k in (2, 5) else "rear"


def form(d: Data, u: dict) -> dict:
    return d.units["formations"][u["formation"]]


def footprint(d: Data, u: dict) -> list:
    """The unit's hexes as rows, front row first; each row runs along the line. Empty if it
    has no men left or has fled."""
    if u["men"] <= 0 or u["state"] == "fled":
        return []
    n = math.ceil(u["men"] / form(d, u)["per_hex"])
    w = max(1, min(u["width"], n))
    v = u["facing"]
    start, rows, k = step(u["pos"], v + 2, (w - 1) // 2), [], 0
    while k < n:
        base = step(start, v + 3, len(rows))
        row = [step(base, v + 5, i) for i in range(min(w, n - k))]
        k += len(row)
        rows.append(row)
    return rows


def men_by_hex(d: Data, u: dict) -> list:
    """Men in each hex of the footprint, row by row (front hexes full first)."""
    per, out, left = form(d, u)["per_hex"], [], u["men"]
    for row in footprint(d, u):
        for _ in row:
            out.append(min(per, left))
            left -= out[-1]
    return out


def occupancy(d: Data, units: list) -> dict:
    """hex key -> unit index, for every unit on the map."""
    occ = {}
    for i, u in enumerate(units):
        for row in footprint(d, u):
            for h in row:
                occ[f"{h[0]},{h[1]}"] = i
    return occ


def _adjacent_units(d: Data, units: list, occ: dict, i: int) -> list:
    """Indexes of the units touching unit i (sorted)."""
    out = set()
    for row in footprint(d, units[i]):
        for h in row:
            for dirn in range(6):
                j = occ.get("{0},{1}".format(*step(h, dirn)))
                if j is not None and j != i:
                    out.add(j)
    return sorted(out)


def in_contact(d: Data, units: list, occ: dict, i: int) -> bool:
    return any(units[j]["side"] != units[i]["side"] for j in _adjacent_units(d, units, occ, i))


def strikes(d: Data, units: list, field: dict | None = None) -> list:
    """Who strikes whom this exchange: [{att, dfd, men, situation, rout}], in a fixed order.
    Each front hex of a unit not broken strikes the enemy hex across its front (its first
    front side that has one) with its front rank, two ranks with reach-2 weapons. A broken
    unit is struck instead by every man of each enemy unit touching it. On a field with works
    and ground (see field_ground), a blow across a palisade or wall comes only from reach-2
    weapons, in the front rank; attacking up a bank, ditch or wall or onto high ground costs
    `penalty`; and horses get no charge into stakes or felled trees (`stakes`)."""
    occ, groups = occupancy(d, units), {}
    for i, u in enumerate(units):
        if not _out(u):
            _strike_groups(d, units, occ, i, groups, field)
    out = [{"att": i, "dfd": j, "men": n, "situation": sit, "rout": False, "penalty": pen, "stakes": stk}
           for (i, j, sit, pen, stk), n in sorted(groups.items())]
    for j, b in enumerate(units):
        if b["state"] == "broken" and b["men"] > 0:
            out += [{"att": i, "dfd": j, "men": units[i]["men"], "situation": "rear", "rout": True}
                    for i in _adjacent_units(d, units, occ, j)
                    if units[i]["side"] != b["side"] and units[i]["state"] not in ("broken", "fled")]
    return out


def pike_front(d: Data, u: dict) -> bool:
    """Whether a unit presents a front of pikes to horse: steady, in a pike formation, with a pike."""
    P = d.units["melee"]["pikes"]
    return u["state"] == "steady" and u["formation"] in P["formations"] and melee_weapon(d, u) in P["weapons"] and not u.get("mounted")


def bunker_at(d: Data, field: dict | None, h) -> dict | None:
    """The intact bunker (a hex work assault.works names) in hex h, or None."""
    hexes = ((_works(field) or {}).get("hexes") or {})
    it = hexes.get(f"{h[0]},{h[1]}") if hexes else None
    return it if it and it["type"] in d.units["assault"]["works"] and C.intact(d, "hex", it) else None


def in_bunker(d: Data, field: dict | None, u: dict) -> bool:
    """Whether any of a unit's hexes is in an intact bunker."""
    return bool(field) and any(bunker_at(d, field, h) for row in footprint(d, u) for h in row)


def _out(u: dict) -> bool:
    """Broken, fled or with no men: out of the fight for striking and shooting."""
    return u["state"] in ("broken", "fled") or u["men"] <= 0


def _strike_groups(d: Data, units: list, occ: dict, i: int, groups: dict, field: dict | None = None) -> None:
    """Add unit i's front hexes' strikes to groups {(i, j, situation, penalty, stakes): men}."""
    u = units[i]
    rows, men = footprint(d, u), men_by_hex(d, u)
    reach = d.weapons[melee_weapon(d, u)].get("reach", 1)
    abreast = form(d, u)["abreast"]
    per, busy = abreast * min(reach, form(d, u)["ranks"]), breaching(d, field, u)
    for k, h in enumerate(rows[0] if rows else []):
        hit = _struck_hex(units, occ, u, h)
        if hit is None:
            continue
        j, dirn = hit
        x = step(h, dirn)
        if bunker_at(d, field, h) or bunker_at(d, field, x):
            continue                                  # no blows into or out of an intact bunker: it must be stormed
        blocked, pen, stk = _across(d, field, u, h, x, reach)
        n = _hex_strikers(men[k], per, abreast, reach if blocked else 0, k in busy)
        if n > 0:
            key = (i, j, arc(units[j]["facing"], dirn + 3), pen, stk)
            groups[key] = groups.get(key, 0) + n


def _hex_strikers(men: int, per: int, abreast: int, blocked_reach: int, busy: bool) -> int:
    """Men of one front hex who strike: per; across a wall (blocked_reach: the weapon's reach,
    else 0) only the front rank of reach-2 weapons; less the front rank if it is breaching."""
    n = min(per, men)
    if blocked_reach:
        n = min(abreast, men) if blocked_reach >= 2 else 0
    if busy:
        n = max(0, n - min(abreast, men))          # the front rank is hacking at the works
    return n


# ---------- the field: ground, works and weather ----------
# field: {ground: {hex key: kind of ground (units.yaml ground; open if not given)}, works:
# {edges, hexes} as on the battle map (gravewounds/combat.py), weather: {cond, wind, ground:
# {mud, snow}} or None, size: [cols, rows]}. None: open ground, no works, no weather.

def _size(d: Data, field: dict | None) -> tuple:
    if field and field.get("size"):
        return tuple(field["size"])
    return d.units["map"]["cols"], d.units["map"]["rows"]


def battlefield(d: Data, fid: str) -> dict:
    """A battlefield from data/fields as a field: the ground from its rows of letters (units.yaml
    ground keys), its works laid on the hexes and hex sides, its weather and size."""
    f, keys = d.fields[fid], {g["key"]: k for k, g in d.units["ground"].items()}
    ground = {f"{c},{r}": keys[ch] for r, row in enumerate(f["rows"]) for c, ch in enumerate(row.strip()) if keys[ch] != "open"}
    works = _field_works(d, f.get("works") or {})
    wx = f.get("weather") or {"cond": "fair", "wind": "calm", "ground": {"mud": 0, "snow": 0}}
    out = {"ground": ground, "works": works, "weather": wx, "size": list(f["size"]), "up": f.get("up", "N")}
    if f.get("support"):
        out["support"] = _field_support(d, f)
    return out


def _field_works(d: Data, fw: dict) -> dict:
    """A battlefield's works laid on its hexes and hex sides, none of them begun."""
    works = {"edges": {}, "hexes": {}}
    for w in fw.get("hexes", []):
        for h in w["at"]:
            works["hexes"][C.hkey(h)] = {"type": w["type"], "progress": 0}
    for w in fw.get("edges", []):
        for a, b in w["at"]:
            it = {"type": w["type"], "progress": 0}
            if d.works["edge_works"][w["type"]].get("height"):
                it["high"] = C.hkey(a)
            if w["type"] == "gate":
                it.update({"open": False, "inside": C.hkey(a)})
            works["edges"].setdefault(C.edge_key(a, b), []).append(it)
    return works


def _field_support(d: Data, f: dict) -> list:
    """A battlefield's own fire support, each with its full stock of rounds and no mission yet."""
    K = d.units["indirect"]["kinds"]
    return [{"name": s["name"], "army": s["side"], "side": f["sides"][s["side"]], "kind": s["kind"], "tubes": s["tubes"],
             "rounds": s["tubes"] * K[s["kind"]]["rounds"], "mission": None} for s in f["support"]]


def battlefield_units(d: Data, fid: str) -> list:
    """The armies as drawn up on a battlefield, as units ready to fight."""
    out = []
    for u in d.fields[fid].get("units", []):
        out.append({**u, "start": u["men"], "down": 0, "dead": 0, "hurt": {}, "heroes": [], "state": "steady",
                    "mounted": bool(u.get("mounted")), "charged": False, "leader": None})
    return out


def ground_at(d: Data, field: dict | None, h) -> dict:
    kind = ((field or {}).get("ground") or {}).get(f"{h[0]},{h[1]}", "open")
    return d.units["ground"][kind]


def _works(field: dict | None):
    return (field or {}).get("works")


def _across(d: Data, field: dict | None, u: dict, h, x, reach: int) -> tuple:
    """A blow from hex h at hex x: (blocked: only reach-2 strikes over it, penalty %, stakes:
    horses get no charge into it)."""
    if not field:
        return False, 0, False
    cols, rows = _size(d, field)
    m = C.melee_across(d, _works(field), h, x, reach, cols, rows)
    pen = m["penalty"]
    gx, gh = ground_at(d, field, x), ground_at(d, field, h)
    if gx.get("height") and not gh.get("height"):
        pen += gx["height"]
    it = C._hex_item(d, _works(field), x)
    stk = bool(u.get("mounted") and it and C._spec(d, "hex", it).get("no_horse"))
    return m["blocked"], pen, stk


def _struck_hex(units: list, occ: dict, u: dict, h) -> tuple | None:
    """(enemy index, direction) across the first of hex h's front sides with a standing enemy."""
    for dirn in (u["facing"], u["facing"] + 1):
        j = occ.get("{0},{1}".format(*step(h, dirn)))
        if j is not None and units[j]["side"] != u["side"] and units[j]["state"] != "broken":
            return j, dirn
    return None


def _fvec(facing: int) -> tuple:
    a, b = AX[facing % 6], AX[(facing + 1) % 6]
    q, r = a[0] + b[0], a[1] + b[1]
    return q, r, -q - r


def volleys(d: Data, units: list, field: dict | None = None) -> list:
    """Who shoots at whom: [{att, dfd, men, dist, cover, penalty, misfire, reach, from, to,
    over}]. A unit with a missile weapon, not broken and not in contact, shoots at the nearest
    enemy unit in range (and in sight, in the weather, with a line of fire: see line_fire) in
    front of it (ties: the first listed); over: % off for loosing high over units between. Its front hexes'
    first `shoot_ranks` ranks shoot. cover: % off from the works and ground at the nearest
    target hex; penalty and misfire: the weather's (gravewounds.combat.weather_attack)."""
    occ, out = occupancy(d, units), []
    for i, u in enumerate(units):
        if u["state"] in ("broken", "fled") or u["men"] <= 0 or "range" not in d.weapons[u["weapon"]]:
            continue
        if in_contact(d, units, occ, i) and not in_bunker(d, field, u):
            continue
        best = _target(d, units, i, field, occ)
        if best is None:
            continue
        wx = shot_weather(d, field, u["weapon"], best[0], best[2], best[3])
        up, longer = height_edge(d, field, u["weapon"], best[2], best[3])
        v = {"att": i, "dfd": best[1], "men": _shooters(d, u, field), "dist": best[0], "cover": share_cover(d, field, best[2], units[best[1]]) + ground_cover(d, units[best[1]]),
             "penalty": wx["penalty"] - up, "misfire": wx["misfire"], "reach": wx.get("reach", 0) + longer, "from": best[2], "to": best[3], "height": up,
             "over": line_fire(d, units, occ, field, i, best[1], best[2], best[3], best[0])}
        if is_mg(d, u["weapon"]):
            v.update(_beaten(d, units, occ, field, i, best))
        out.append(v)
    return out


def _shooters(d: Data, u: dict, field: dict | None = None) -> float:
    """Who shoots: a machine-gun team's served guns; any other unit's front hexes' first
    shoot_ranks ranks, less the front rank of each hex breaching the works. A pinned unit,
    suppression.fire of them."""
    if is_mg(d, u["weapon"]):
        n = mg_guns(d, u)
    else:
        rows, men, ab = footprint(d, u), men_by_hex(d, u), form(d, u)["abreast"]
        per_hex = ab * min(d.units["shoot_ranks"], form(d, u)["ranks"])
        busy = breaching(d, field, u)
        n = sum(max(0, min(per_hex, men[k]) - (min(ab, men[k]) if k in busy else 0)) for k in range(len(rows[0])))
    return n * d.units["suppression"]["fire"] if u.get("pinned") else n


def is_mg(d: Data, weapon: str) -> bool:
    return weapon in (d.units.get("machine_guns") or {}).get("weapons", [])


def mg_guns(d: Data, u: dict) -> int:
    """A machine-gun team's guns still served: one a crew, while a man of the crew is up."""
    return math.ceil(max(0, u["men"]) / d.units["machine_guns"]["crew"])


def ground_cover(d: Data, u: dict) -> int:
    """% off shots at a unit gone to ground."""
    return d.units["to_ground"]["cover"] if u.get("prone") else 0


def _beaten(d: Data, units: list, occ: dict, field: dict | None, i: int, best: tuple) -> dict:
    """A machine gun's beaten zone past its target: {behind (unit index or None), beyond (hexes
    past the target), bcover (% off there: ground and going to ground)}."""
    dist, j, h, t = best
    for k, x in enumerate(ray(h, t, dist + d.units["machine_guns"]["beaten"]["beyond"])[dist:]):
        if ground_at(d, field, x).get("stops_shot"):
            break
        b = occ.get(f"{x[0]},{x[1]}")
        if k > 0 and b is not None and b not in (i, j):
            return {"behind": b, "beyond": k, "bcover": ground_at(d, field, x).get("cover", 0) + ground_cover(d, units[b])}
    return {"behind": None, "beyond": 0, "bcover": 0}


def shot_weather(d: Data, field: dict | None, weapon: str, dist: int, h=None, t=None) -> dict:
    """The weather's effect on a shot `dist` field hexes away, from hex h to hex t (for the
    wind's direction): {blocked, penalty, misfire, reach}. Smoke on the line blocks it."""
    if h is not None and t is not None and smoked(field, ray(h, t, dist)):
        return {"blocked": "Smoke: no one can see to shoot through it.", "penalty": 0, "misfire": 0, "reach": 0}
    if is_gun(d, weapon):
        return gun_weather(d, field, dist, h, t)
    return C.weather_attack(d, (field or {}).get("weather"), weapon, dist * d.units["range_scale"], h, t, _up(field))


def height_edge(d: Data, field: dict | None, weapon: str, h, t) -> tuple:
    """(% to hit, % longer range bands) for a shot from hex h at hex t: down from high ground
    +, up at it -; none for guns or on level ground."""
    if not field or is_gun(d, weapon):
        return 0, 0
    a, b = bool(ground_at(d, field, h).get("height")), bool(ground_at(d, field, t).get("height"))
    H = d.units["high_ground"]
    if a and not b:
        return H["shoot"], H["reach"]
    return (-H["shoot"], 0) if b and not a else (0, 0)


def _up(field: dict | None) -> str:
    """The compass point at the top of the field map (north, unless the battlefield says)."""
    return (field or {}).get("up") or "N"


def _reaches(d: Data, u: dict, dist: int, reach: int = 0) -> bool:
    """Whether a unit's weapon shoots this many field hexes: a battery's guns to their range."""
    if is_gun(d, u["weapon"]):
        return dist <= gun_range(d, u)
    return field_range(d, u["weapon"], dist, reach) is not None


def share_cover(d: Data, field: dict | None, h, target: dict) -> int:
    """% off a volley from hex h at a unit: the average cover of its row nearest h (half a line
    behind a wall gets half the wall's cover), rounded down."""
    if not field:
        return 0
    rows = footprint(d, target)
    if not rows:
        return 0
    row = min(rows, key=lambda r: min(hdist(h, t) for t in r))
    return sum(cover_at(d, field, h, t) for t in row) // len(row)


def cover_at(d: Data, field: dict | None, h, t) -> int:
    """% off shots from hex h at hex t: the best of the works' cover and the ground's."""
    if not field:
        return 0
    cols, rows = _size(d, field)
    return max(C.missile_cover(d, _works(field), h, t, cols, rows)["cover"], ground_at(d, field, t).get("cover", 0))


def _target(d: Data, units: list, i: int, field: dict | None = None, occ: dict | None = None):
    """(distance, index, shooter hex, target hex) of the nearest enemy unit in range, in
    sight and in front of unit i, or None. A battery fires at the unit the GM named
    (u["target"], its id) if it can, and needs a clear line of fire (occ given)."""
    u, fv, best = units[i], _fvec(units[i]["facing"]), None
    front = footprint(d, u)[0]
    named = _named_target(d, units, i, field, occ, u.get("target"))
    if named is not None:
        return named
    for j, e in enumerate(units):
        if e["side"] == u["side"] or e["men"] <= 0 or e["state"] == "fled":
            continue
        near = _nearest_ahead(d, u, front, fv, [t for row in footprint(d, e) for t in row], field, _clear_fn(d, units, occ, field, i, j))
        if near is not None and (best is None or near[0] < best[0]):
            best = (near[0], j, near[1], near[2])
    return best


def _named_target(d: Data, units: list, i: int, field: dict | None, occ: dict | None, tid):
    """A target the GM named for a battery (tid, a unit's id), as _target gives it, if it can be fired on."""
    u = units[i]
    if occ is None or tid is None:
        return None
    j = next((k for k, e in enumerate(units) if e.get("id") == tid), None)
    if j is None or units[j]["side"] == u["side"] or _out(units[j]):
        return None
    hexes = [t for row in footprint(d, units[j]) for t in row]
    near = _nearest_ahead(d, u, footprint(d, u)[0], _fvec(u["facing"]), hexes, field, _clear_fn(d, units, occ, field, i, j))
    return None if near is None else (near[0], j, near[1], near[2])


def _clear_fn(d: Data, units: list, occ: dict | None, field: dict | None, i: int, j: int):
    """A test that unit i has a line of fire from h to t (see line_fire); None without occ."""
    if occ is None:
        return None
    return lambda h, t, dist: line_fire(d, units, occ, field, i, j, h, t, dist) is not None


def line_fire(d: Data, units: list, occ: dict, field: dict | None, i: int, j: int, h, t, dist: int):
    """Unit i shooting from hex h at unit j's hex t: None if another unit between blocks it,
    else the % off (bows loosing high over units). From high ground a unit shoots over units
    on lower ground; guns only with round shot, never canister; shell goes over anything."""
    u, high, pen = units[i], ground_at(d, field, h).get("height"), 0
    over, arc = True, u["weapon"] in d.units["line_of_fire"]["arcing"]
    if is_gun(d, u["weapon"]):
        over = dist > d.units["artillery"]["canister_to"]
        if over and gun_kind(u) == "howitzer":
            return 0
    for x in ray(h, t, dist)[1:-1]:
        k = occ.get(f"{x[0]},{x[1]}")
        if k is None or k in (i, j) or (over and high and not ground_at(d, field, x).get("height")):
            continue
        if not arc:
            return None
        pen = d.units["line_of_fire"]["arc_penalty"]
    return pen


def _nearest_ahead(d: Data, u: dict, front: list, fv: tuple, hexes: list, field: dict | None = None, clear=None):
    """(distance, front hex, target hex): the shortest distance in range of unit u's weapon and
    in sight from a front hex to one of `hexes` ahead of the line (with a line of fire), or None."""
    best, weapon = None, u["weapon"]
    for t in hexes:
        c = _cube(t)
        for h in front:
            s = _cube(h)
            if sum((c[k] - s[k]) * fv[k] for k in range(3)) <= 0:
                continue
            dist = hdist(h, t)
            if best is not None and dist >= best[0]:
                continue
            wx = shot_weather(d, field, weapon, dist, h, t)
            reach = wx.get("reach", 0) + height_edge(d, field, weapon, h, t)[1]
            if not wx["blocked"] and _reaches(d, u, dist, reach) and (clear is None or clear(h, t, dist)):
                best = (dist, h, t)
    return best


def _side(u: dict, table: str, d: Data | None = None) -> dict:
    """A unit as a fighting side: hand to hand, a battery's crews fight with their own weapon."""
    weapon = melee_weapon(d, u) if d else u["weapon"]
    return {"table": table, "weapon": weapon, "kit": u.get("kit"), "quality": u["quality"]}


def exchange(d: Data, units: list, table: str, rng, field: dict | None = None) -> tuple[list, list]:
    """One exchange on the field map: every melee and volley at once from the present
    positions, then breaching, losses, morale, and a rout strike on any unit that breaks.
    Returns (units, log): log lines are {kind (melee, volley, hero, herohit, breach, rout,
    morale), ...}. field: the ground, works and weather (see field_ground); works being
    breached are updated in it, in place."""
    us = [_copy_unit(u) for u in units]
    lost, dead, dealt, flanked, log = [0] * len(us), [0] * len(us), [0] * len(us), [False] * len(us), []
    acc = (lost, dead, dealt)
    under = [False] * len(us)                     # under shellfire or machine-gun fire this exchange (suppression)
    log += _closing_all(d, us, table, rng, acc, field)
    log += _strike_all(d, us, table, rng, acc, flanked, field)
    log += _shoot_all(d, us, table, rng, acc, field, under)
    log += _indirect_all(d, us, table, rng, acc, field, under)
    log += _assault_all(d, us, table, rng, acc, field)
    log += _breach_all(d, us, field)
    occ = occupancy(d, us)
    before = [u["men"] for u in us]
    for i, u in enumerate(us):
        cut = min(lost[i], u["men"])
        u.update(men=u["men"] - cut, down=u.get("down", 0) + cut, dead=u.get("dead", 0) + min(dead[i], cut))
    log += _morale_all(d, us, occ, before, lost, dealt, flanked, rng, table)
    log += _suppress_all(d, us, under, rng)
    log += _heroes_after(d, us, rng)
    for u in us:
        u["charged"] = False
        _battery_after(d, u)
        if u.get("pinned"):
            u["pinned"] -= 1
    for b in (field or {}).get("support") or []:
        if b.get("mission") and b["mission"].get("wait", 0) > 0:
            b["mission"]["wait"] -= 1
    log += _displace_all(field)
    _smoke_thins(field)
    _smoke_drifts(d, field)
    return us, log


def _displace_all(field: dict | None) -> list:
    """Batteries displacing count down; one that has moved is no longer located, and missions on it end."""
    sup, log = (field or {}).get("support") or [], []
    for k, b in enumerate(sup):
        if not b.get("displacing"):
            continue
        b["displacing"] -= 1
        if b["displacing"]:
            continue
        b["located"] = False
        for x in sup:
            if x.get("mission") and x["mission"].get("battery") == k:
                x["mission"] = None
        log.append({"kind": "displaced", "sup": k, "name": b["name"], "side": b["side"]})
    return log


def downwind(d: Data, field: dict | None):
    """The hex side (0-5) the field's wind blows smoke through, or None in calm air or with no direction."""
    weather, pts = (field or {}).get("weather") or {}, d.weather.get("wind_points", []) if d.weather else []
    if weather.get("dir") not in pts or weather.get("wind", "calm") == "calm":
        return None
    wx, wy = C.WIND_VECTORS[(pts.index(weather["dir"]) - pts.index(_up(field)) + 4) % 8]
    best, side = None, None
    for dirn in range(6):
        dq, dr = AX[dirn]
        dot = math.sqrt(3) * (dq + dr / 2) * wx + 1.5 * dr * wy
        if best is None or dot > best + 1e-9:
            best, side = dot, dirn
    return side


def _smoke_drifts(d: Data, field: dict | None) -> None:
    """Smoke moves `drift` hexes downwind; what leaves the map is gone."""
    sm = (field or {}).get("smoke")
    side = downwind(d, field) if sm else None
    n = d.units["indirect"]["smoke"].get("drift", {}).get(((field or {}).get("weather") or {}).get("wind") or "calm", 0)
    if side is None or not n:
        return
    size, out = field.get("size"), {}
    for key, left in sm.items():
        h = step([int(x) for x in key.split(",")], side, n)
        if size and not (0 <= h[0] < size[0] and 0 <= h[1] < size[1]):
            continue
        k2 = f"{h[0]},{h[1]}"
        out[k2] = max(out.get(k2, 0), left)
    field["smoke"] = out


def _smoke_thins(field: dict | None) -> None:
    """Smoke hangs one exchange less; gone at none."""
    sm = (field or {}).get("smoke")
    if sm:
        field["smoke"] = {h: n - 1 for h, n in sm.items() if n > 1}


def _closing_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None = None) -> list:
    """Batteries charged in front fire canister into the charge as it comes in (closing_fire)."""
    log = []
    for c in closing_fire(d, us, field):
        log += _fire_battery(d, us, table, rng, acc, c)
    return log


def _strike_all(d: Data, us: list, table: str, rng, acc: tuple, flanked: list, field: dict | None = None) -> list:
    """Every melee, each unit's front heroes striking with its first (or dueling the enemy's)."""
    log, struck, dueled = [], set(), set()
    for s in strikes(d, us, field):
        a, b = us[s["att"]], us[s["dfd"]]
        charge = bool(a.get("charged")) and bool(a.get("mounted")) and not s.get("stakes") and not (s["situation"] == "front" and pike_front(d, b))
        vs_horse = d.units["melee"]["pikes"]["attack"] if b.get("mounted") and pike_front(d, a) else 0
        opts = {"situation": s["situation"], "charge": charge, "shaken": a["state"] == "shaken", "rout": s["rout"],
                "exposed": _exposure(d, b, s["rout"]), "penalty": s.get("penalty", 0) - vs_horse}
        t = _take_hurt(b, melee(d, _side(a, table, d), _side(b, table, d), s["men"], rng, **opts))
        _tally(*acc, s, t)
        flanked[s["dfd"]] = flanked[s["dfd"]] or s["situation"] in ("flank", "rear")
        log += _logged({"kind": "rout" if s["rout"] else "melee", **s}, t)
        if s["att"] in struck:
            continue
        struck.add(s["att"])
        log += _front_heroes(d, (a, b), s, (table, rng, acc), opts, dueled)
    return log


def _front_heroes(d: Data, units: tuple, s: dict, ctx: tuple, opts: dict, dueled: set) -> list:
    """A striking unit's front heroes: each duels the enemy's first free front hero, or strikes its rankers."""
    (a, b), (table, rng, acc), log = units, ctx, []
    for hero in _acting(a, ("front",)):
        if hero["id"] in dueled:
            continue
        foe = None if s["rout"] else next((h for h in _heroes(b, ("front",)) if h["id"] not in dueled), None)
        if foe is not None:
            log += _duel(d, (a, b), (hero, foe), table, rng, s, dueled)
            continue
        t = _take_hurt(b, melee(d, _hero_side(a, hero, table, d), _side(b, table, d), d.units["heroes"]["tempo"], rng, **opts))
        _tally(*acc, s, t)
        log += _logged({"kind": "hero", "hero": hero["id"], "name": hero["name"], "att": s["att"], "dfd": s["dfd"],
                        "situation": s["situation"]}, t)
    return log


def _duel(d: Data, units: tuple, pair: tuple, table: str, rng, s: dict, dueled: set) -> list:
    """Two front heroes fight each other: each makes heroes.duel attempts at the other with the
    full rules (the one whose unit struck first, first), instead of at the rankers."""
    (a, b), (hero, foe), log = units, pair, []
    dueled.update((hero["id"], foe["id"]))
    for x, y, ux, k in ((hero, foe, a, s["att"]), (foe, hero, b, s["dfd"])):
        if x["state"] != "up" or _held(x) or y["state"] != "up":
            continue
        side = _hero_side(ux, x, table, d)
        atk = max(0, side["skill"])
        crit_at, t = math.floor(atk * d.wounds["combat"]["critical_fraction"]), _new_tally()
        t["blows"] = _count(d.units["heroes"]["duel"], rng)
        for _ in range(t["blows"]):
            if y["state"] != "up":
                break
            _hero_blow(d, side, y, rng.randint(1, 100), atk, crit_at, 0, rng, t)
        hits = t.pop("heroes", [])
        log.append({"kind": "duel", "unit": k, "hero": x["id"], "name": x["name"], "foe": y["id"], "fname": y["name"], "blows": t["blows"]})
        log += [{"kind": "herohit", "unit": s["dfd"] if k == s["att"] else s["att"], **h} for h in hits]
    return log


def _shoot_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None = None, under: list | None = None) -> list:
    """Every volley, each unit's shooting heroes with it. under: marks the units a machine gun
    fired on (suppression)."""
    log = []
    for v in volleys(d, us, field):
        _mark_mg(d, us, v, under)
        b = us[v["dfd"]]
        opts = {"factor": form(d, b)["missile_factor"] * (100 - v["misfire"]) / 100, "exposed": _exposure(d, b, False, True),
                "penalty": v["cover"] + v["penalty"] + v["over"], "reach": v["reach"]}
        t = _take_hurt(b, volley(d, _side(us[v["att"]], table), _side(b, table), v["men"], v["dist"], rng, **opts))
        _tally(*acc, v, t)
        log += _logged({"kind": "volley", **v}, t)
        if v.get("behind") is not None:
            log += _beaten_fire(d, us, table, rng, acc, v)
        for hero in _acting(us[v["att"]], ("ranged",)):
            wx = shot_weather(d, field, hero["weapon"], v["dist"], v["from"], v["to"])
            up, longer = height_edge(d, field, hero["weapon"], v["from"], v["to"])
            if wx["blocked"] or field_range(d, hero["weapon"], v["dist"], wx["reach"] + longer) is None:
                continue
            hopts = {**opts, "factor": form(d, b)["missile_factor"] * (100 - wx["misfire"]) / 100, "penalty": v["cover"] + wx["penalty"] - up + v["over"],
                     "reach": wx["reach"] + longer}
            t = _take_hurt(b, volley(d, _hero_side(us[v["att"]], hero, table, d), _side(b, table), d.units["heroes"]["tempo"], v["dist"], rng, **hopts))
            _tally(*acc, v, t)
            log += _logged({"kind": "hero", "hero": hero["id"], "name": hero["name"], "att": v["att"], "dfd": v["dfd"], "dist": v["dist"]}, t)
    for c in cannonades(d, us, field):
        log += _fire_battery(d, us, table, rng, acc, c)
    return log


def _mark_mg(d: Data, us: list, v: dict, under: list | None) -> None:
    """A machine gun's target, and any unit in its beaten zone, check for suppression."""
    if under is None or not is_mg(d, us[v["att"]]["weapon"]):
        return
    under[v["dfd"]] = True
    if v.get("behind") is not None:
        under[v["behind"]] = True


def _beaten_fire(d: Data, us: list, table: str, rng, acc: tuple, v: dict) -> list:
    """A machine gun's cone falling on into the unit behind its target."""
    k, bh = v["behind"], us[v["behind"]]
    r = {**v, "dfd": k, "dist": v["dist"] + v["beyond"], "men": v["men"] * d.units["machine_guns"]["beaten"]["share"] / 100}
    opts = {"factor": form(d, bh)["missile_factor"] * (100 - v["misfire"]) / 100, "exposed": _exposure(d, bh, False, True),
            "penalty": v["bcover"] + v["penalty"], "reach": v["reach"]}
    hits = volley(d, _side(us[v["att"]], table), _side(bh, table), r["men"], r["dist"], rng, **opts)
    if hits is None:
        return []
    t = _take_hurt(bh, hits)
    lost, dead, dealt = acc
    _tally(lost, dead, dealt, r, t)
    return _logged({"kind": "beaten", **r}, t)


# ---------- indirect fire (data/units.yaml indirect) ----------

def shell_weapon(d: Data, table: str) -> str | None:
    """The weapon whose wound data shell fragments use on this table, or None (no indirect fire)."""
    from .model import available_weapons
    I, have = d.units["indirect"], available_weapons(d, table)
    return next((w for w in (I["weapon"], I["fallback"]) if w in have), None)


def spotted(d: Data, units: list, field: dict | None, side, h) -> bool:
    """Whether a unit of `side` (not broken or fled) can see hex h to call fire on it: within
    the weather's sight, with no woods between."""
    sight = _sight_hexes(d, field)
    return any(u["side"] == side and u["men"] > 0 and u["state"] not in ("broken", "fled") and _sees(d, field, u, h, sight) for u in units)


def _sight_hexes(d: Data, field: dict | None) -> int | None:
    """How far the weather lets a man see, in field hexes (None: as far as the map)."""
    cond = ((field or {}).get("weather") or {}).get("cond")
    vis = d.weather["conditions"][cond].get("visibility") if cond and d.weather else None
    return None if vis is None else vis // d.units["range_scale"]


def _sees(d: Data, field: dict | None, u: dict, h, sight: int | None) -> bool:
    """Whether any hex of unit u sees hex h: within sight, with no woods between and no smoke
    on the line (the two ends included)."""
    for x in (x for row in footprint(d, u) for x in row):
        dist = hdist(x, h)
        if sight is not None and dist > sight:
            continue
        line = ray(x, h, dist)
        if not any(ground_at(d, field, y).get("cover") for y in line[1:-1]) and not smoked(field, line):
            return True
    return False


def smoked(field: dict | None, hexes) -> bool:
    """Whether smoke hangs over any of these hexes."""
    sm = (field or {}).get("smoke") or {}
    return bool(sm) and any(f"{h[0]},{h[1]}" in sm for h in hexes)


def within(h, radius: int) -> list:
    """Hex h and every hex within `radius` of it."""
    out = [list(h)]
    for n in range(1, radius + 1):
        for a in range(6):
            corner = step(h, a, n)
            out += [step(corner, a + 2, j) for j in range(n)]
    return out


def _indirect_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None, under: list) -> list:
    """Every fire mission due this exchange (in the order of the support list)."""
    log, weapon = [], shell_weapon(d, table)
    if not field or weapon is None:
        return log
    for k, b in enumerate(field.get("support") or []):
        m = b.get("mission")
        if not m or m.get("wait", 0) > 0 or b.get("rounds", 0) <= 0 or served_tubes(d, b) <= 0 or b.get("displacing"):
            continue
        log += _fire_mission(d, us, table, weapon, rng, acc, field, under, k, b)
    return log


def crew_of(d: Data, b: dict) -> int:
    """An off-map battery's crewmen still serving: `crew` a tube it came with, less those lost."""
    return b["crew"] if "crew" in b else b.get("tubes", 0) * d.units["indirect"]["kinds"][b["kind"]].get("crew", 0)


def served_tubes(d: Data, b: dict) -> int:
    """The tubes an off-map battery can fire: those not knocked out that it has `serve` men each for."""
    K = d.units["indirect"]["kinds"][b["kind"]]
    if "serve" not in K:
        return b.get("tubes", 0)
    return min(b.get("tubes", 0), crew_of(d, b) // K["serve"])


def _fire_mission(d: Data, us: list, table: str, weapon: str, rng, acc: tuple, field: dict, under: list, k: int, b: dict) -> list:
    """One battery's shells this exchange: on an enemy battery (counter-battery), or on a hex:
    where each lands, then smoke laid or the men struck in every unit. A battery that fires is
    located; a creeping mission moves on."""
    K, m = d.units["indirect"]["kinds"][b["kind"]], b["mission"]
    shells = min(served_tubes(d, b) * K["rate"], b["rounds"])
    b["rounds"] -= shells
    if not K.get("direct"):
        b["located"] = True                       # tanks close behind the line are never located
    if m.get("battery") is not None:
        log = _counter_fire(d, field, (k, b, shells, K), (table, weapon), rng)
    else:
        bursts = []
        for _ in range(shells):
            dirn, far = rng.randint(0, 5), rng.randint(0, K["scatter"])
            bursts.append(step(m["hex"], dirn, far))
        log = [{"kind": "barrage", "sup": k, "name": b["name"], "side": b["side"], "shells": shells, "at": m["hex"], "bursts": bursts,
                "smoke": bool(m.get("smoke"))}]
        if m.get("smoke"):
            _lay_smoke(d, field, bursts)
        else:
            log += _shell_units(d, us, (table, weapon), rng, acc, field, under, k, b, bursts)
            log += _knock_bunkers(d, field, k, b, bursts, rng)
    _mission_on(b, m, field.get("size"))
    return log


def _knock_bunkers(d: Data, field: dict, k: int, b: dict, bursts: list, rng) -> list:
    """Each shell bursting on an intact bunker's hex knocks it out at the kind's `knock` %."""
    knock, log = d.units["indirect"]["kinds"][b["kind"]].get("knock", 0), []
    if not knock:
        return log
    for at in bursts:
        it = bunker_at(d, field, at)
        if it and rng.randint(1, 100) <= knock:
            it["out"] = True
            log.append({"kind": "knocked", "sup": k, "name": b["name"], "side": b["side"], "at": at})
    return log


def _mission_on(b: dict, m: dict, size) -> None:
    """After a battery fires: a single mission ends; a creeping one keeps to its fire plan,
    lifting its aim on after `every` exchanges on a line, and ends after its `lines` lines or
    when its aim leaves the map."""
    if not m.get("repeat"):
        b["mission"] = None
        return
    cr = m.get("creep")
    if not cr:
        return
    cr["on"] = cr.get("on", 0) + 1
    if cr["on"] < cr.get("every", 1):
        return
    cr["on"] = 0
    if cr.get("lines") and cr.get("line", 1) >= cr["lines"]:
        b["mission"] = None
        return
    cr["line"] = cr.get("line", 1) + 1
    for _ in range(cr["step"]):
        m["hex"] = step(m["hex"], cr["dir"] + cr.get("done", 0) % 2)
        cr["done"] = cr.get("done", 0) + 1
    if size and not (0 <= m["hex"][0] < size[0] and 0 <= m["hex"][1] < size[1]):
        b["mission"] = None


def _counter_fire(d: Data, field: dict, fire: tuple, tw: tuple, rng) -> list:
    """Counter-battery (fire: battery index, battery, shells, its kind; tw: table and shell
    weapon): each shell lands among the target's guns at the kind's counter %, knocking out a
    tube and striking `among` crewmen, or at `near` times that % bursts close by, striking
    `near_struck`. The struck crewmen roll wounds; those put down are lost to the battery."""
    k, b, shells, kind = fire
    j, sup, CB = b["mission"]["battery"], field["support"], d.units["indirect"]["counter_battery"]
    tg = sup[j] if 0 <= j < len(sup) else None
    if tg is None or tg["side"] == b["side"]:
        b["mission"] = None
        return []
    hits = struck = 0
    for _ in range(shells):
        r = rng.randint(1, 100)
        if r <= kind["counter"]:
            hits += 1
            struck += CB["among"]
        elif r <= kind["counter"] * CB["near"]:
            struck += CB["near_struck"]
    knocked, crew = min(tg["tubes"], hits), crew_of(d, tg)
    struck = min(struck, crew)
    table, weapon = tw
    t = _blows(d, {"table": table, "weapon": weapon, "kit": None, "quality": "regular"},
               {"table": table, "weapon": weapon, "kit": "none", "quality": "regular"}, struck, d.units["indirect"]["attack"], 0, rng, (), -1000)
    tg["tubes"] -= knocked
    tg["crew"] = crew - t["down"]
    tg["crew_dead"] = tg.get("crew_dead", 0) + t["dead"]
    if served_tubes(d, tg) <= 0:
        tg["mission"] = None
    return [{"kind": "counter", "sup": k, "name": b["name"], "side": b["side"], "shells": shells, "target": j, "tname": tg["name"],
             "knocked": knocked, "left": tg["tubes"], "struck": struck, "down": t["down"], "dead": t["dead"], "crew": tg["crew"],
             "served": served_tubes(d, tg)}]


def _lay_smoke(d: Data, field: dict, bursts: list) -> None:
    """Smoke over each burst's hex and those within the radius, for as long as the wind lets it hang."""
    S = d.units["indirect"]["smoke"]
    lasts = S["lasts"][((field.get("weather") or {}).get("wind")) or "calm"]
    sm = field.setdefault("smoke", {})
    for at in bursts:
        for h in within(at, S["radius"]):
            key = f"{h[0]},{h[1]}"
            sm[key] = max(sm.get(key, 0), lasts)


def _shell_units(d: Data, us: list, tw: tuple, rng, acc: tuple, field: dict, under: list, k: int, b: dict, bursts: list) -> list:
    """The men struck in every unit by a battery's bursts, and their wounds."""
    I, (table, weapon) = d.units["indirect"], tw
    K, log = I["kinds"][b["kind"]], []
    att = {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}
    lost, dead, _ = acc
    for i, u in enumerate(us):
        struck = _shell_struck_unit(d, field, u, bursts, K, rng)
        if struck is None:
            continue
        under[i] = True
        if not struck:
            continue
        t = _take_hurt(u, _blows(d, att, _side(u, table), struck, I["attack"], 0, rng, _exposure(d, u, False, True), -1000))
        lost[i] += t["down"]
        dead[i] += t["dead"]
        log += _logged({"kind": "shelled", "sup": k, "name": b["name"], "dfd": i, "struck": struck}, t)
    return log


def _shell_struck_unit(d: Data, field: dict, u: dict, bursts: list, kind: dict, rng) -> int | None:
    """Men of unit u struck by these bursts: each man in a hex within a burst's radius at the %
    for his distance (gone to ground, less; ground cover, less). None if no burst came near."""
    if u["men"] <= 0 or u["state"] == "fled":
        return None
    hexes = [h for row in footprint(d, u) for h in row]
    men, near, struck = men_by_hex(d, u), False, 0
    cuts = [_shell_cut(d, field, h, u.get("prone")) for h in hexes]
    for at in bursts:
        for h, n, cut in zip(hexes, men, cuts):
            dist = hdist(h, at)
            if dist > kind["radius"]:
                continue
            near = True
            p = kind["struck"][dist] * cut
            struck += sum(1 for _ in range(n) if rng.randint(1, 100) <= p)
    return struck if near else None


def _shell_cut(d: Data, field: dict | None, h, prone) -> float:
    """What shellfire's struck % is multiplied by for men in hex h: in woods, tree bursts (no
    cover, more struck, going to ground helps less); elsewhere going to ground and the ground's cover."""
    I = d.units["indirect"]
    TB = I["tree_burst"]
    bk = bunker_at(d, field, h)
    shelter = (100 - d.works["hex_works"][bk["type"]].get("cover_here", 0)) / 100 if bk else 1
    if ((field or {}).get("ground") or {}).get(f"{h[0]},{h[1]}", "open") in TB["ground"]:
        return TB["factor"] * (TB["prone"] if prone else 1) * shelter
    return (I["prone"] if prone else 1) * (100 - ground_at(d, field, h).get("cover", 0)) / 100 * shelter


def blast_weapon(d: Data, table: str) -> str | None:
    """The weapon whose wounds a storming party's grenades and charges use on this table, or None
    (no storming of bunkers)."""
    from .model import available_weapons
    A, have = d.units["assault"], available_weapons(d, table)
    return next((w for w in (A["weapon"], A["fallback"]) if w in have), None)


def _assault_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None) -> list:
    """Every unit ordered to storm the bunkers across its front: one roll for each bunker."""
    weapon, log = blast_weapon(d, table), []
    if not field or weapon is None:
        return log
    occ = occupancy(d, us)
    for i, u in enumerate(us):
        if u.get("assault") in d.units["assault"]["means"] and not _out(u):
            log += _storm(d, us, occ, i, (table, weapon), rng, acc, field)
    return log


def _storm(d: Data, us: list, occ: dict, i: int, tw: tuple, rng, acc: tuple, field: dict) -> list:
    """Unit i storms each intact, held bunker next to its front hexes once."""
    u, A, log, done = us[i], d.units["assault"], [], set()
    M = A["means"][u["assault"]]
    for h in (footprint(d, u) or [[]])[0]:
        hit = _struck_hex(us, occ, u, h)
        if hit is None:
            continue
        j, dirn = hit
        x = step(h, dirn)
        it = bunker_at(d, field, x)
        if it is None or f"{x[0]},{x[1]}" in done:
            continue
        done.add(f"{x[0]},{x[1]}")
        need, roll = M["knock"] + (A["pinned"] if us[j].get("pinned") else 0), rng.randint(1, 100)
        line = {"kind": "assault", "unit": i, "dfd": j, "means": u["assault"], "at": x, "roll": roll, "need": need, "out": roll <= need}
        if roll > need:
            log.append(line)
            continue
        it["out"] = True
        t = _bunker_struck(d, us, j, x, M, tw, rng, acc)
        acc[2][i] += t["down"]
        log += _logged(line, t)
    return log


def _bunker_struck(d: Data, us: list, j: int, x, means: dict, tw: tuple, rng, acc: tuple) -> dict:
    """The men in a bunker's hex when it falls: `struck` % of them, by blast or by flame."""
    b, (table, weapon) = us[j], tw
    hexes = [h for row in footprint(d, b) for h in row]
    k = next((n for n, h in enumerate(hexes) if h[0] == x[0] and h[1] == x[1]), None)
    there = men_by_hex(d, b)[k] if k is not None else 0
    struck = sum(1 for _ in range(there) if rng.randint(1, 100) <= means["struck"])
    if means.get("flame"):
        t = _new_tally()
        t.update(blows=struck, hits=struck, critical=struck, down=struck)
        for _ in range(struck):
            if rng.randint(1, 100) <= d.units["assault"]["flame_dead"]:
                t["dead"] += 1
            else:
                _hurt(t, "critical", {"lethal": "days", "infection": "high"}, True)
    else:
        att = {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}
        t = _blows(d, att, _side(b, table), struck, d.units["assault"]["attack"], 0, rng, _exposure(d, b, False, True), -1000)
    t = _take_hurt(b, t)
    lost, dead, _ = acc
    lost[j] += t["down"]
    dead[j] += t["dead"]
    return {**t, "struck": struck}


def _suppress_all(d: Data, us: list, under: list, rng) -> list:
    """Units under shellfire or machine-gun fire this exchange check Nerve; a failure pins them
    for the next exchange."""
    S, log = d.units["suppression"], []
    for i, u in enumerate(us):
        if not under[i] or u["men"] <= 0 or u["state"] in ("broken", "fled"):
            continue
        target = quality(d, u["quality"])["nerve"] + (S["prone"] if u.get("prone") else 0)
        roll = rng.randint(1, 100)
        if roll > target:
            u["pinned"] = 2
            log.append({"kind": "pinned", "unit": i, "roll": roll, "target": target})
    return log


def _fire_battery(d: Data, us: list, table: str, rng, acc: tuple, c: dict) -> list:
    """One battery's fire: at its target, any guns it knocks out there, then any balls that
    bound on into the unit behind."""
    a, b = us[c["att"]], us[c["dfd"]]
    gun = {**_side(a, table), "weapon": a["weapon"]}
    t = _take_hurt(b, cannonade(d, gun, b, c, rng, _exposure(d, b, False, True)))
    a["spent"] = a.get("spent", 0) + c["rounds"]
    if b.get("id") is not None:
        a["fired"] = {**(a.get("fired") or {}), str(b["id"]): c["dist"]}
    if t.get("dismounted"):
        b["guns_lost"] = b.get("guns_lost", 0) + t["dismounted"]
    lost, dead, dealt = acc
    _tally(lost, dead, dealt, c, t)
    log = _logged({"kind": "cannon", **c}, t)
    k = c["behind"]
    if k is not None:
        bh = us[k]
        t = _take_hurt(bh, ricochet(d, gun, bh, c, rng, _exposure(d, bh, False, True)))
        _tally(lost, dead, dealt, {"att": c["att"], "dfd": k}, t)
        log += _logged({"kind": "ricochet", **c, "dfd": k}, t)
    return log


def _breach_all(d: Data, us: list, field: dict | None) -> list:
    """Units ordered to breach (unit["breach"]) hack at the works on their front: each front
    hex's front rank works at the first breachable work across its front sides, or in the hex
    beyond. Progress is in the battle map's man-rounds, so a field hex side, `scale` times as
    long, takes `scale` times the work."""
    if not field or not _works(field):
        return []
    log, scale = [], d.units["hex_m"] / d.wounds["combat"]["move"]["hex_m"]
    per = d.units["exchange_rounds"] * d.units["breach_share"] / scale
    for i, u in enumerate(us):
        if u.get("breach") and not _out(u):
            log += _unit_breach(d, field, i, u, per)
    return log


def _unit_breach(d: Data, field: dict, i: int, u: dict, per: float) -> list:
    log, rows, men = [], footprint(d, u), men_by_hex(d, u)
    for k, h in enumerate(rows[0] if rows else []):
        hit = _breachable(d, field, u, h)
        if hit is None:
            continue
        kind, where, it = hit
        it["progress"] = it.get("progress", 0) + min(form(d, u)["abreast"], men[k]) * per
        if not C.intact(d, kind, it):
            log.append({"kind": "breach", "unit": i, "work": it["type"], "at": where})
    return log


def breaching(d: Data, field: dict | None, u: dict) -> set:
    """Indexes of the front hexes whose front rank is breaching works this exchange."""
    if not field or not u.get("breach") or not _works(field):
        return set()
    return {k for k, h in enumerate((footprint(d, u) or [[]])[0]) if _breachable(d, field, u, h)}


def _breachable(d: Data, field: dict, u: dict, h):
    """(edge or hex, its key, the item): the first work hex h's front rank can hack at."""
    works = _works(field)
    for dirn in (u["facing"], u["facing"] + 1):
        x = step(h, dirn)
        for it in C._edge_items(d, works, h, x):
            if C._spec(d, "edge", it).get("breach"):
                return "edge", C.edge_key(h, x), it
        it = C._hex_item(d, works, x)
        if it and C._spec(d, "hex", it).get("breach"):
            return "hex", C.hkey(x), it
    return None


def _copy_unit(u: dict) -> dict:
    return dict(u, hurt=dict(u.get("hurt", {})),
                heroes=[dict(h, wounds=list(h.get("wounds", [])), **({"held": dict(h["held"])} if h.get("held") else {})) for h in u.get("heroes", [])])


def _logged(line: dict, t: dict) -> list:
    """A log line for a tally, then one line for each blow that fell on a hero."""
    t = dict(t)
    hits = t.pop("heroes", [])
    return [{**line, **t}] + [{"kind": "herohit", "unit": line["dfd"], **h} for h in hits]


def _take_hurt(u: dict, t: dict) -> dict:
    """Move a tally's wounded onto the unit struck; the tally (for the log) keeps the rest."""
    t = dict(t)
    for k, n in t.pop("hurt", {}).items():
        u["hurt"][k] = u["hurt"].get(k, 0) + n
    return t


def _tally(lost: list, dead: list, dealt: list, s: dict, t: dict) -> None:
    lost[s["dfd"]] += t["down"]
    dead[s["dfd"]] += t["dead"]
    dealt[s["att"]] += t["down"]


def _morale_all(d: Data, us: list, occ: dict, before: list, lost: list, dealt: list, flanked: list, rng,
                table: str = "") -> list:
    """Every unit still in the fight checks; any that breaks is struck at once by the enemies
    touching it, every man of them."""
    log, broke = [], []
    for i, u in enumerate(us):
        if u["state"] in ("broken", "fled") or u["men"] <= 0:
            continue
        near = _adjacent_units(d, us, occ, i)
        unit = {"quality": u["quality"], "start": u["start"], "down": u["down"], "lost": lost[i], "dealt": dealt[i],
                "men": before[i], "state": u["state"], "leader": leader_state(u), "flanked": flanked[i],
                "contact": any(us[j]["side"] != u["side"] for j in near),
                "friends": any(us[j]["side"] == u["side"] and us[j]["state"] == "steady" for j in near)}
        m = morale(d, unit, rng.randint(1, 100))
        if m["check"]:
            log.append({"kind": "morale", "unit": i, "target": m["target"], "from": u["state"], "state": m["state"]})
        if m["state"] == "broken":
            broke.append(i)
        u["state"] = m["state"]
    for j in broke:
        log += _rout_strike(d, us, occ, j, table, rng)
    return log


def _rout_strike(d: Data, us: list, occ: dict, j: int, table: str, rng) -> list:
    """A unit that has just broken is struck by every man of each enemy unit touching it."""
    log = []
    for i in _adjacent_units(d, us, occ, j):
        a, b = us[i], us[j]
        if a["side"] == b["side"] or a["state"] in ("broken", "fled") or a["men"] <= 0 or b["men"] <= 0:
            continue
        t = _take_hurt(b, melee(d, _side(a, table, d), _side(b, table, d), a["men"], rng, rout=True, exposed=_exposure(d, b, True)))
        cut = min(t["down"], b["men"])
        b.update(men=b["men"] - cut, down=b["down"] + cut, dead=b["dead"] + min(t["dead"], cut))
        log += _logged({"kind": "rout", "att": i, "dfd": j, "men": a["men"], "situation": "rear", "rout": True}, t)
    return log


# ---------- movement ----------

def allowance(d: Data, u: dict) -> int:
    """Hexes a unit may move in an exchange (twice this for a charge). A battery limbering,
    unlimbering or resupplying does not move; unlimbered, it can only be manhandled a hex or so."""
    if (u.get("prone") or u.get("pinned")) and u["state"] not in ("broken", "fled"):   # gone to ground or pinned (a broken unit gets up and runs)
        return 0
    if is_battery(d, u) and not u.get("abandoned") and u["state"] != "broken":   # crews running from their guns run on foot
        if u.get("limbering") or u.get("resupplying"):
            return 0
        if not u.get("limbered"):
            return d.units["artillery"]["pushed"]
    return d.units["mounted_move"] if u.get("mounted") else form(d, u)["move"]


def turn_cost(d: Data, u: dict) -> int:
    """Hexes of movement to turn the facing one step: 1 for every turn_per hexes of front."""
    n = math.ceil(max(1, u["men"]) / form(d, u)["per_hex"])
    return max(1, math.ceil(min(u["width"], n) / d.units["turn_per"]))


def _fits(d: Data, units: list, i: int, u: dict, size: tuple, field: dict | None = None) -> bool:
    """Unit i placed as u: on the map, on no other unit's hexes, and on ground it can stand on
    (no wagons; for horses, no marsh, stakes or felled trees), with no palisade or wall
    running through it."""
    occ = occupancy(d, [x for k, x in enumerate(units) if k != i])
    hexes = [h for row in footprint(d, u) for h in row]
    if not all(0 <= h[0] < size[0] and 0 <= h[1] < size[1] and f"{h[0]},{h[1]}" not in occ for h in hexes):
        return False
    return not field or _stands(d, field, u, hexes)


def _stands(d: Data, field: dict, u: dict, hexes: list) -> bool:
    keys = {f"{h[0]},{h[1]}" for h in hexes}
    for h in hexes:
        if not _can_enter(d, field, u, h):
            return False
        for dirn in range(6):
            x = step(h, dirn)
            if f"{x[0]},{x[1]}" in keys and _wall_between(d, field, h, x):
                return False
    return True


def _can_enter(d: Data, field: dict, u: dict, h) -> bool:
    if ground_at(d, field, h).get("impassable"):
        return False
    it = C._hex_item(d, _works(field), h)
    if it and C._spec(d, "hex", it).get("enter") is None:
        return False
    if not u.get("mounted"):
        return True
    return not ground_at(d, field, h).get("no_horse") and not (it and C._spec(d, "hex", it).get("no_horse"))


def _wall_between(d: Data, field: dict, a, b) -> bool:
    """A palisade, wall or barred gate between hexes a and b (open gates are left out)."""
    for it in C._edge_items(d, _works(field), a, b):
        s = C._spec(d, "edge", it)
        if s.get("cross") is None or s.get("gate"):
            return True
    return False


def step_cost(d: Data, field: dict | None, u: dict, a, b) -> int | None:
    """Movement for one hex of a unit to step from a to b: 1, plus works crossed and entered,
    plus the ground (rough, woods, marsh), plus deep mud or snow. None if it cannot. A unit pays
    the worst of its front row's (_front_cost)."""
    if not field:
        return 1
    if not _can_enter(d, field, u, b):
        return None
    c = C.step_cost(d, _works(field), a, b)
    if c is None:
        return None
    wx = field.get("weather") or {}
    return c + ground_at(d, field, b)["move"] - 1 + C.deep_going(d, wx.get("ground"))


def _path_len(d: Data, units: list, i: int, goal, size: tuple, limit: int, field: dict | None = None) -> int | None:
    """Least movement for the unit's middle hex from where it is to goal (step_cost), not
    through other units' hexes; None if more than limit."""
    occ = occupancy(d, [x for k, x in enumerate(units) if k != i])
    u, start = units[i], tuple(units[i]["pos"])
    best, heap, done = {start: 0}, [(0, start)], set()
    while heap:
        cost, h = heapq.heappop(heap)
        if h in done:
            continue
        if list(h) == list(goal):
            return cost
        done.add(h)
        for x, c in _steps_from(d, field, u, h, occ, size):
            if cost + c <= limit and cost + c < best.get(x, limit + 1):
                best[x] = cost + c
                heapq.heappush(heap, (cost + c, x))
    return None


def _steps_from(d: Data, field: dict | None, u: dict, h: tuple, occ: dict, size: tuple) -> list:
    """(hex, cost) for each step the unit's middle hex can take from h: the worst that any hex
    of its front row pays for the same step (one that cannot step blocks it)."""
    out, front = [], (footprint(d, {**u, "pos": list(h)}) or [[]])[0] if field else [list(h)]
    for dirn in range(6):
        x = tuple(step(list(h), dirn))
        if not (0 <= x[0] < size[0] and 0 <= x[1] < size[1]) or f"{x[0]},{x[1]}" in occ:
            continue
        sc = _front_cost(d, field, u, front, dirn, size)
        if sc is not None:
            out.append((x, sc))
    return out


def _front_cost(d: Data, field: dict | None, u: dict, front: list, dirn: int, size: tuple) -> int | None:
    """The worst step cost of a front row's hexes stepping in direction dirn (off the map: not counted)."""
    worst = 0
    for f in front:
        y = step(f, dirn)
        if not (0 <= y[0] < size[0] and 0 <= y[1] < size[1]):
            continue
        c = step_cost(d, field, u, f, y)
        if c is None:
            return None
        worst = max(worst, c)
    return worst or 1


def move(d: Data, units: list, i: int, pos, facing: int, size: tuple, field: dict | None = None) -> dict:
    """Can unit i end its move with its middle front hex at pos, facing `facing`? {ok, cost,
    charge, why}. Turning costs turn_cost a step. A unit already in contact cannot move. A
    move that ends in contact with an enemy may be up to charge_move times the allowance (a
    charge; not for a shaken unit)."""
    u = units[i]
    if u["state"] in ("broken", "fled"):
        return {"ok": False, "why": "it is running"}
    if in_contact(d, units, occupancy(d, units), i) and (list(pos) != u["pos"] or facing != u["facing"]):
        return {"ok": False, "why": "it is in contact"}
    turns = min((facing - u["facing"]) % 6, (u["facing"] - facing) % 6)
    most = allowance(d, u) * d.units["charge_move"]
    steps = _path_len(d, units, i, pos, size, most, field)
    if steps is None:
        return {"ok": False, "why": "too far, or no way through"}
    moved = {**u, "pos": list(pos), "facing": facing % 6}
    if not _fits(d, units, i, moved, size, field):
        return {"ok": False, "why": "no room there"}
    cost = steps + turns * turn_cost(d, u)
    after = [moved if k == i else x for k, x in enumerate(units)]
    contact = in_contact(d, after, occupancy(d, after), i)
    if cost <= allowance(d, u):
        return {"ok": True, "cost": cost, "charge": contact and steps > 0}
    if contact and u["state"] == "steady" and cost <= most:
        return {"ok": True, "cost": cost, "charge": True}
    return {"ok": False, "why": "too far"}


def flee(d: Data, units: list, i: int, size: tuple, field: dict | None = None) -> dict:
    """A broken unit runs straight back as far as its allowance takes it; off the map, it has
    fled the field. Returns the unit."""
    u = dict(units[i])
    back = (u["facing"] + 3) % 6
    for _ in range(allowance(d, u)):
        nxt = {**u, "pos": step(u["pos"], back)}
        if not all(0 <= h[0] < size[0] and 0 <= h[1] < size[1] for row in footprint(d, nxt) for h in row):
            return {**u, "state": "fled"}
        if step_cost(d, field, u, u["pos"], nxt["pos"]) is None or not _fits(d, units, i, nxt, size, field):
            break
        u = nxt
    return u



HERO_EXAMPLES = [("Knight in mail", "hauberk"), ("Knight in plate", "full_plate"), ("Champion, no armour", "none")]


def hero_examples(d: Data, table: str, runs: int, seed: int) -> list[dict]:
    """A hero (attack 65, defence 45, Nerve 65, sword) leading 120 regular billmen in jacks
    from the front against the same, fought until one side breaks: % of runs he was wounded,
    down and killed, and the men he put down (mean)."""
    out = []
    for label, kit in HERO_EXAMPLES:
        r = {"label": label, "wounded": 0, "down": 0, "dead": 0, "felled": 0}
        for k in range(runs):
            rng = SeededDice(seed * 7919 + k)
            us = [_example_unit(0, [20, 20], 0), _example_unit(1, [21, 20], 3)]
            us[0]["heroes"] = [{"id": 1, "name": "Hero", "role": "front", "attack": 65, "defence": 45, "nerve": 65,
                                "weapon": "sword", "kit": kit, "leader": True, "state": "up", "wounds": []}]
            for _ in range(60):
                us, log = exchange(d, us, table, rng)
                r["felled"] += sum(x["down"] for x in log if x["kind"] == "hero")
                if any(u["state"] == "broken" for u in us):
                    break
            h = us[0]["heroes"][0]
            r["wounded"] += bool(h["wounds"])
            r["down"] += h["state"] == "down"
            r["dead"] += h["state"] == "dead"
        out.append({**r, **{k: 100 * r[k] / runs for k in ("wounded", "down", "dead")}, "felled": r["felled"] / runs})
    return out


def _example_unit(side: int, pos: list, facing: int) -> dict:
    return {"side": side, "pos": pos, "facing": facing, "men": 120, "start": 120, "down": 0, "dead": 0, "width": 3,
            "quality": "regular", "weapon": "bill", "kit": "jack_sallet", "formation": "close", "state": "steady",
            "mounted": False, "charged": False, "leader": None}

# ---------- after the battle ----------

def standing(u: dict) -> bool:
    return u["men"] > 0 and u["state"] in ("steady", "shaken")


def aftermath(d: Data, units: list, care: list, rng) -> list:
    """What becomes of each unit's wounded when the battle ends (units.yaml aftermath). care:
    each unit's camp care (none, field, shelter). Returns, per unit, {left (down men left on a
    lost field, dead), died (of wounds before treatment), cases (survivors on the wound
    track)}. A man wounded twice is counted once: the down are capped at those down and not
    dead, the walking wounded at the men still on their feet."""
    am, d100 = d.units["aftermath"], (lambda: rng.randint(1, 100))
    lost_sides = {u["side"] for u in units} - {u["side"] for u in units if standing(u)}
    return [_unit_after(d, u, care[i], am["left_behind"] and u["side"] in lost_sides, d100) for i, u in enumerate(units)]


def _unit_after(d: Data, u: dict, care: str, abandon: bool, d100) -> dict:
    """One unit's wounded after the battle: left behind, dead of their wounds, or carried."""
    r = {"left": 0, "died": 0, "cases": []}
    room = {"1": max(0, u.get("down", 0) - u.get("dead", 0)), "0": max(0, u["men"])}
    for k in sorted(u.get("hurt", {})):
        sev, lethal, inf, down = k.split("|")
        n = min(u["hurt"][k], room[down])
        room[down] -= n
        if down == "1" and abandon:
            r["left"] += n
            continue
        for _ in range(n):
            if _dies(d.units["aftermath"], lethal, care, d100):
                r["died"] += 1
            else:
                r["cases"].append(wound_case(d, sev, lethal, inf, d100))
    return r


def _dies(am: dict, lethal: str, care: str, d100) -> bool:
    """A wound that kills in minutes or hours: does it, before help comes?"""
    if lethal == "minutes":
        return d100() > am["saved"]["minutes"]
    if lethal == "hours":
        return d100() > am["saved"]["hours"][care]
    return False


# ---------- guns ----------
# A battery: a unit whose weapon is a gun (units.yaml artillery), its men the crews. It is
# limbered (u["limbered"]: moves, cannot fire) or not; u["limbering"]: changing over this
# exchange (neither moves nor fires); u["abandoned"]: broke and left its guns.

def is_gun(d: Data, weapon: str) -> bool:
    return weapon in d.units.get("artillery", {}).get("guns", [])


def is_battery(d: Data, u: dict) -> bool:
    return is_gun(d, u["weapon"])


def melee_weapon(d: Data, u: dict) -> str:
    """The weapon a unit fights hand to hand with: a battery's crews have their own."""
    return d.units["artillery"]["crew_weapon"] if is_battery(d, u) else u["weapon"]


def guns_of(d: Data, u: dict) -> int:
    """The guns a battery brought into action: one for every `crew` men it started with."""
    return math.ceil(u.get("start", u["men"]) / d.units["artillery"]["crew"])


def guns_served(d: Data, u: dict) -> int:
    """Guns the crews still serve: one for every `crew` men left, up to the guns not knocked out."""
    crew = d.units["artillery"]["crew"]
    return max(0, min(guns_of(d, u) - u.get("guns_lost", 0), math.ceil(max(0, u["men"]) / crew)))


def ammo_left(d: Data, u: dict) -> int:
    """Rounds the battery has left: `ammo` a gun it brought, less those it has fired."""
    return max(0, guns_of(d, u) * d.units["artillery"]["ammo"] - u.get("spent", 0))


def gun_weather(d: Data, field: dict | None, dist: int, h=None, t=None) -> dict:
    """The weather's effect on guns: no laying them on what cannot be seen (less with rain or
    snow driven into the gunners' faces); the wind as on firearms; no reach from the wind."""
    out = {"blocked": None, "penalty": 0, "misfire": 0, "reach": 0}
    weather = (field or {}).get("weather")
    if not weather or not d.weather:
        return out
    cond = d.weather["conditions"][weather["cond"]]
    vis = cond.get("visibility")
    if vis is not None and cond["precip"] != "none" and C.wind_lie(d, weather, h, t, _up(field)) == "against":
        vis = vis * d.weather["driven_sight"] // 100
    if vis is not None and dist * d.units["range_scale"] > vis:
        out["blocked"] = f"{cond['name']}: the guns cannot be laid on what cannot be seen."
        return out
    out["penalty"] = next(x for x in d.weather["winds"] if x["id"] == weather["wind"])["firearm"]
    return out


def _chance_at(bands: list, dist: int) -> int:
    """The % for this distance from [[up to hexes, %], ...]; 0 beyond the last."""
    return next((ch for to, ch in bands if dist <= to), 0)


def _can_fire(d: Data, u: dict) -> bool:
    """Unlimbered, not changing over or resupplying, not broken, with guns served and rounds left."""
    if not is_battery(d, u) or _out(u) or u.get("abandoned"):
        return False
    if u.get("limbered") or u.get("limbering") or u.get("resupplying"):
        return False
    return guns_served(d, u) > 0 and ammo_left(d, u) > 0


def cannonades(d: Data, units: list, field: dict | None = None) -> list:
    """Which batteries fire at whom: [{att, dfd, guns, rounds, dist, shot (canister, round or
    shell), cover, penalty, named, graze, behind, beyond, fuse, section}]. A battery fires unlimbered, not changing over, not
    broken and not in contact, with the guns its crews still serve and the rounds it has left,
    at its named target or the nearest enemy in range, in sight and in front, with a clear line
    of fire; a section it split off (u["section"]: {target, guns, shot}) at that target, if it
    can. The shot is the GM's order (u["shot"]) if the guns have it and it reaches, else by range.
    behind: the unit a bounding round-shot ball can strike, beyond: how far past; fuse: the
    gunners' fuse setting (shell)."""
    occ, out, A = occupancy(d, units), [], d.units.get("artillery")
    for i, u in enumerate(units):
        if not A or not _can_fire(d, u) or in_contact(d, units, occ, i):
            continue
        best = _target(d, units, i, field, occ)
        if best is not None:
            out += _battery_fires(d, units, occ, field, i, best)
    return out


def _battery_fires(d: Data, units: list, occ: dict, field: dict | None, i: int, best: tuple) -> list:
    """Battery i's fire at best, and its section's at the section's target if it split one off."""
    u = units[i]
    guns, ammo, sec = guns_served(d, u), ammo_left(d, u), u.get("section") or {}
    n = min(sec.get("guns", 0), guns - 1)
    at = _named_target(d, units, i, field, occ, sec.get("target")) if n > 0 else None
    main = _battery_fire(d, units, (occ, field), i, best, {"guns": guns - n if at else guns, "ammo": ammo, "shot": u.get("shot")})
    if at is None or ammo <= main["rounds"]:
        return [main]
    return [main, _battery_fire(d, units, (occ, field), i, at, {"guns": n, "ammo": ammo - main["rounds"], "shot": sec.get("shot"), "section": True})]


def _battery_fire(d: Data, units: list, ground: tuple, i: int, best: tuple, order: dict) -> dict:
    """Guns of battery i firing at best (from _target), as cannonades gives it. ground: (occ,
    field); order: {guns, ammo (rounds left), shot (ordered, or None), per (rounds a gun),
    section}."""
    (occ, field), A, u = ground, d.units["artillery"], units[i]
    wx, shot = gun_weather(d, field, best[0], best[2], best[3]), _shot(d, u, best[0], order.get("shot"))
    behind = _ricochet_at(d, occ, field, i, best) if shot == "round" else None
    graze = A["canister"]["graze"] if shot == "canister" and best[0] > A["canister"]["strike"][0][0] and _firm(d, field, best) else 0
    tgt = units[best[1]]
    tid = tgt.get("id")
    return {"att": i, "dfd": best[1], "guns": order["guns"], "rounds": min(order["guns"] * order.get("per", A["rounds"]), order["ammo"]),
            "dist": best[0], "shot": shot, "cover": cover_at(d, field, best[2], best[3]) + ground_cover(d, tgt), "penalty": wx["penalty"],
            "named": bool(order.get("section")) or (tid is not None and tid == u.get("target")), "graze": graze, "bore": gun_kind(u),
            "behind": behind[0] if behind else None, "beyond": behind[1] if behind else 0,
            "fuse": fuse_setting(d, u, tid, best[0]) if shot == "shell" else 0, "section": bool(order.get("section"))}


def fuse_setting(d: Data, u: dict, tid, dist: int) -> int:
    """How far the gunners' cut fuses widen the air band (narrow it, if negative): the crews'
    quality, and more if the battery fired at this target last exchange at much the same range."""
    F = d.units["artillery"].get("set_fuse")
    if not F:
        return 0
    was = (u.get("laid") or {}).get(str(tid)) if tid is not None else None
    return F["quality"].get(u["quality"], 0) + (F["ranged"] if was is not None and abs(was - dist) <= F["within"] else 0)


def closing_fire(d: Data, units: list, field: dict | None = None) -> list:
    """Batteries charged in front this exchange (as cannonades gives them, closing: True): each
    that can fire gives its first charger `closing` rounds of canister a gun as it comes in."""
    A, out = d.units.get("artillery"), []
    if not A or "closing" not in A:
        return out
    occ = occupancy(d, units)
    for i, u in enumerate(units):
        best = _charger(d, units, occ, field, i) if _can_fire(d, u) else None
        if best is not None:
            order = {"guns": guns_served(d, u), "ammo": ammo_left(d, u), "shot": "canister", "per": A["closing"]}
            out.append({**_battery_fire(d, units, (occ, field), i, best, order), "named": False, "closing": True})
    return out


def _charger(d: Data, units: list, occ: dict, field: dict | None, i: int):
    """(distance, index, gun hex, its hex) of the first enemy that charged battery i in front this exchange, or None."""
    u = units[i]
    front, fv = footprint(d, u)[0], _fvec(u["facing"])
    for j in _adjacent_units(d, units, occ, i):
        e = units[j]
        if e["side"] == u["side"] or not e.get("charged") or _out(e):
            continue
        near = _nearest_ahead(d, u, front, fv, [t for row in footprint(d, e) for t in row], field)
        if near is not None:
            return near[0], j, near[1], near[2]
    return None


def gun_kind(u: dict) -> str:
    """A battery's guns: smoothbore, rifled or howitzer (a battery saved as howitzer: true, howitzer)."""
    return u.get("guns") or ("howitzer" if u.get("howitzer") else "smoothbore")


def gun_range(d: Data, u: dict) -> int:
    """How far a battery's guns reach, in field hexes: rifled guns further."""
    A = d.units["artillery"]
    return A["rifled"]["range"] if gun_kind(u) == "rifled" else A["range"]


def _shot(d: Data, u: dict, dist: int, want: str | None = None) -> str:
    """The shot ordered (want), if the guns fire it and it reaches (canister only within
    canister range); else canister within canister range, beyond it shell from howitzers and
    rifled guns, round shot from smoothbores."""
    A = d.units["artillery"]
    if want in A.get("shots", {}).get(gun_kind(u), []) and (want != "canister" or dist <= A["canister_to"]):
        return want
    if dist <= A["canister_to"]:
        return "canister"
    return "round" if gun_kind(u) == "smoothbore" else "shell"


def _firm(d: Data, field: dict | None, best: tuple) -> bool:
    """Firm ground all the way from the gun to the target hex: no mud or snow, nothing that stops shot."""
    dist, _, h, t = best
    return not _soft(d, field) and not any(ground_at(d, field, x).get("stops_shot") for x in ray(h, t, dist)[1:])


def _soft(d: Data, field: dict | None) -> bool:
    """Mud or snow deep enough to stop a ball bounding."""
    g, soft = ((field or {}).get("weather") or {}).get("ground") or {}, d.units["artillery"]["ricochet"]["soft"]
    return g.get("mud", 0) >= soft or g.get("snow", 0) >= soft


def _ricochet_at(d: Data, occ: dict, field: dict | None, i: int, best: tuple):
    """(unit index, hexes past the target) of the first other unit a ball fired from best's
    shooter hex at its target hex bounds into, or None (soft or broken ground stops it)."""
    if _soft(d, field):
        return None
    dist, j, h, t = best
    beyond = d.units["artillery"]["ricochet"]["beyond"]
    for k, x in enumerate(ray(h, t, dist + beyond)[dist:]):
        if ground_at(d, field, x).get("stops_shot"):
            return None
        u = occ.get(f"{x[0]},{x[1]}")
        if k > 0 and u is not None and u not in (i, j):
            return u, k
    return None


def _canister_struck(art: dict, c: dict, cut: float, rounds: int, rng) -> int:
    """Men hit by canister: each ball a chance (more on firm ground, the balls skipping on; a
    rifle's canister throws fewer balls)."""
    p = (_chance_at(art["canister"]["strike"], c["dist"]) + c.get("graze", 0)) * cut
    balls = art["rifled"]["canister_balls"] if c.get("bore") == "rifled" else art["canister"]["balls"]
    return sum(rng.randint(1, 100) <= p for _ in range(rounds * balls))


def _fuse_at(bands: list, roll: int) -> str:
    """What a shell's fuse does on this d100 roll: [[up to, early|air|ground|blind], ...]."""
    return next(what for to, what in bands if roll <= to)


def set_fuse(bands: list, by: int) -> list:
    """The fuse table with its air band widened by `by` (narrowed, if negative), taken from or
    given to the band after it, and never past its neighbours."""
    out = []
    for k, (to, what) in enumerate(bands):
        if what == "air" and by:
            lo, hi = bands[k - 1][0] if k else 0, bands[k + 1][0] if k + 1 < len(bands) else 100
            to = max(lo, min(hi, to + by))
        out.append([to, what])
    return out


def _shell_struck(art: dict, c: dict, factor: float, rounds: int, rng) -> tuple:
    """(men hit, shells that burst on the unit, of them in the air): each shell falls on the unit
    with the chance for its range (times factor: formation and weather; a rifle's own figures
    and percussion fuse for rifled guns), then its fuse decides:
    early (harmless), air (fragments at air_hit %, cover counting half), ground (fragment_hit %,
    less the cover) or blind."""
    H = art["howitzer"]
    R = art["rifled"] if c.get("bore") == "rifled" else H          # rifled shell: its own strike and percussion fuse
    p, fuses = _chance_at(R["strike"], c["dist"]) * factor, set_fuse(R["fuse"], c.get("fuse", 0))
    hit_at = {"air": H["air_hit"] * (100 - c["cover"] / 2) / 100, "ground": H["fragment_hit"] * (100 - c["cover"]) / 100}
    struck = bursts = air = 0
    for _ in range(rounds):
        if rng.randint(1, 100) > p:
            continue
        fuse = _fuse_at(fuses, rng.randint(1, 100))
        if fuse not in hit_at:
            continue
        bursts += 1
        air += fuse == "air"
        struck += sum(rng.randint(1, 100) <= hit_at[fuse] for _ in range(H["fragments"]))
    return struck, bursts, air


def _round_shot_struck(d: Data, art: dict, p: float, rounds: int, target: dict, rng) -> tuple:
    """(men hit, balls that struck) by round shot: each ball that strikes the unit (p %) goes
    through its ranks."""
    rs = art["round_shot"]
    path = min(rs["path_max"], form(d, target)["ranks"] * len(footprint(d, target)))
    struck = hits = 0
    for _ in range(rounds):
        if rng.randint(1, 100) <= p:
            hits += 1
            struck += sum(rng.randint(1, 100) <= rs["file"] for _ in range(path))
    return struck, hits


def cannonade(d: Data, att: dict, target: dict, c: dict, rng, exposed: tuple = ()) -> dict:
    """One exchange of a battery's fire (att: the battery as a side, with its gun; c, from
    cannonades) at the target unit: the men struck, then a wound roll for each."""
    A = d.units["artillery"]
    rounds = c["rounds"]
    cut = form(d, target)["missile_factor"] * (100 - c["cover"] - c["penalty"]) / 100
    hits = air = 0
    if c["shot"] == "canister":
        struck = _canister_struck(A, c, cut, rounds, rng)
    elif c["shot"] == "shell":
        struck, hits, air = _shell_struck(A, c, form(d, target)["missile_factor"] * (100 - c["penalty"]) / 100, rounds, rng)
    else:
        struck, hits = _round_shot_struck(d, A, _chance_at(A["round_shot"]["strike"], c["dist"]) * cut, rounds, target, rng)
    t = _blows(d, att, _side(target, att["table"]), struck, A["attack"], 0, rng, exposed, -1000)
    if c["shot"] == "shell":
        t["bursts"], t["air"] = hits, air
    if is_battery(d, target):
        t["dismounted"] = min(sum(rng.randint(1, 100) <= A["dismount"] for _ in range(hits)), guns_served(d, target))
    return t


def ricochet(d: Data, att: dict, target: dict, c: dict, rng, exposed: tuple = ()) -> dict:
    """The balls of a battery's round shot that bound on into the unit behind its target
    (c from cannonades: behind, beyond): the men struck, then a wound roll for each."""
    A = d.units["artillery"]
    p = _chance_at(A["ricochet"]["strike"], c["beyond"]) * form(d, target)["missile_factor"]
    struck, _ = _round_shot_struck(d, A, p, c["rounds"], target, rng)
    return _blows(d, att, _side(target, att["table"]), struck, A["attack"], 0, rng, exposed, -1000)


def _battery_after(d: Data, u: dict) -> None:
    """At the end of an exchange: a battery that was changing over is now limbered or not, one
    that was resupplying has its rounds again, and one that has broken has left its guns."""
    if not is_battery(d, u):
        return
    u["laid"] = u.pop("fired", None) or {}
    if u.get("resupplying"):
        u["spent"] = 0
        u["resupplying"] = False
    if u.get("limbering"):
        u["limbered"] = not u.get("limbered")
        u["limbering"] = False
    if u["state"] in ("broken", "fled"):
        u["abandoned"] = True


GUN_EXAMPLES = (("canister at 200 m, a line", 20, 40, "smoothbore"), ("round shot at 400 m, a line", 40, 40, "smoothbore"),
                ("round shot at 400 m, a column", 40, 10, "smoothbore"), ("round shot at 800 m, a column", 80, 10, "smoothbore"),
                ("howitzers, shell at 400 m, a line", 40, 40, "howitzer"), ("howitzers, shell at 400 m, a column", 40, 10, "howitzer"),
                ("howitzers, shell at 800 m, a column", 80, 10, "howitzer"), ("rifled, canister at 200 m, a line", 20, 40, "rifled"),
                ("rifled, shell at 400 m, a column", 40, 10, "rifled"), ("rifled, shell at 800 m, a column", 80, 10, "rifled"),
                ("rifled, shell at 1,400 m, a column", 140, 10, "rifled"))


def gun_examples(d: Data, runs: int, seed: int) -> list[dict]:
    """A battery of 6 guns (60 regular crews; smoothbore, howitzers or rifled) firing for one
    minute at 1,600 unarmoured men in close order, as a line (40 hexes wide) or a column (10
    wide): men struck and men put down (means), on the Peninsular table."""
    table, out = "peninsular-1808-14-all-hits", []
    for label, dist, width, how in GUN_EXAMPLES:
        struck = down = 0
        for k in range(runs):
            bat = {**_example_unit(0, [30, 200], 1), "men": 60, "start": 60, "weapon": "artillery_smoothbore", "formation": "battery", "guns": how}
            tgt = {**_example_unit(1, [30, 200 - dist], 4), "men": 1600, "start": 1600, "width": width, "weapon": "musket_smoothbore", "kit": "none"}
            _, log = exchange(d, [bat, tgt], table, SeededDice(seed * 7907 + k), {"ground": {}, "works": None, "weather": None, "size": [60, 220]})
            for line in log:
                if line["kind"] == "cannon":
                    struck += line["blows"]
                    down += line["down"]
        out.append({"label": label, "struck": struck / runs, "down": down / runs})
    return out


MG_EXAMPLES = (   # (label, shooter weapon, shooters, shooter formation, distance in hexes, target formation, target width, prone)
    ("2 machine guns, 400 m, close order", "machine_gun", 10, "mg", 40, "close", 3, False),
    ("2 machine guns, 400 m, extended order", "machine_gun", 10, "mg", 40, "extended", 34, False),
    ("2 machine guns, 400 m, extended, to ground", "machine_gun", 10, "mg", 40, "extended", 34, True),
    ("2 machine guns, 800 m, extended order", "machine_gun", 10, "mg", 80, "extended", 34, False),
    ("100 riflemen, 400 m, close order", "rifle_service", 100, "extended", 40, "close", 3, False),
    ("100 riflemen, 400 m, extended order", "rifle_service", 100, "extended", 40, "extended", 34, False),
    ("100 riflemen, 400 m, extended, to ground", "rifle_service", 100, "extended", 40, "extended", 34, True),
)


def mg_examples(d: Data, runs: int, seed: int) -> list[dict]:
    """Machine guns and magazine rifles (regular, on the First World War table) firing for one
    minute at 100 regular unarmoured riflemen: men hit and put down (means)."""
    table, out = "wwi-1914-18-wounds", []
    for label, weapon, men, fm, dist, tfm, width, prone in MG_EXAMPLES:
        hit = down = 0
        for k in range(runs):
            sh = {**_example_unit(0, [60, 200], 1), "men": men, "start": men, "weapon": weapon, "formation": fm, "kit": "none",
                  "width": math.ceil(men / d.units["formations"][fm]["per_hex"])}
            tg = {**_example_unit(1, [60, 200 - dist], 4), "men": 100, "start": 100, "width": width, "weapon": "rifle_service", "formation": tfm,
                  "kit": "none", "prone": prone}
            _, log = exchange(d, [sh, tg], table, SeededDice(seed * 7919 + k), {"ground": {}, "works": None, "weather": None, "size": [120, 220]})
            for line in log:
                if line["kind"] == "volley" and line["att"] == 0:
                    hit += line["hits"]
                    down += line["down"]
        out.append({"label": label, "hit": hit / runs, "down": down / runs})
    return out


SHELL_EXAMPLES = (   # (label, kind, tubes, target formation, width, prone, ground under the target)
    ("2 mortars, close order", "mortar", 2, "close", 3, False, "open"),
    ("2 mortars, extended order", "mortar", 2, "extended", 34, False, "open"),
    ("4 field guns, close order", "field", 4, "close", 3, False, "open"),
    ("4 field guns, extended order", "field", 4, "extended", 34, False, "open"),
    ("4 field guns, extended, to ground", "field", 4, "extended", 34, True, "open"),
    ("4 field guns, extended, in woods", "field", 4, "extended", 34, False, "woods"),
    ("4 field guns, extended, to ground in woods", "field", 4, "extended", 34, True, "woods"),
    ("4 heavy howitzers, extended order", "howitzer", 4, "extended", 34, False, "open"),
)


def shell_examples(d: Data, runs: int, seed: int) -> list[dict]:
    """A battery's fire for one minute on the middle of 100 regular unarmoured riflemen (First
    World War table): men struck and put down, and how often the unit is pinned (means)."""
    table, out = "wwi-1914-18-wounds", []
    for label, kind, tubes, tfm, width, prone, ground in SHELL_EXAMPLES:
        struck = down = pinned = 0
        under = {} if ground == "open" else {f"{c},{r}": ground for c in range(20, 100) for r in range(90, 110)}
        for k in range(runs):
            tg = {**_example_unit(1, [60, 100], 4), "men": 100, "start": 100, "width": width, "weapon": "rifle_service", "formation": tfm,
                  "kit": "none", "prone": prone}
            field = {"ground": under, "works": None, "weather": None, "size": [120, 200],
                     "support": [{"name": "Battery", "side": 0, "kind": kind, "tubes": tubes, "rounds": 999, "mission": {"hex": [60, 100], "wait": 0}}]}
            us, log = exchange(d, [tg], table, SeededDice(seed * 7927 + k), field)
            for line in log:
                if line["kind"] == "shelled":
                    struck += line["struck"]
                    down += line["down"]
            pinned += 1 if us[0].get("pinned") else 0
        out.append({"label": label, "struck": struck / runs, "down": down / runs, "pinned": 100 * pinned / runs})
    return out
