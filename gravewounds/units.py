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
            "light": 0, "serious": 0, "critical": 0, "down": 0, "dead": 0, "hurt": {}}


def _hurt(t: dict, sev: str, fx: dict, down: bool) -> None:
    """Remember a wounded man by severity, death clock, infection risk and whether he is down."""
    k = f"{sev}|{fx['lethal']}|{fx['infection']}|{1 if down else 0}"
    t["hurt"][k] = t["hurt"].get(k, 0) + 1


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
        _hurt(t, "light" if h["graze"] else sev, h["effects"], False)
        return
    nerve = quality(d, dfd["quality"])["nerve"] - (10 if sev == "critical" else 0)
    down = rng.randint(1, 100) > nerve
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
           penalty: int = 0, factor: float = 1.0, exposed: tuple = ()) -> dict | None:
    """One exchange of `men` shooting at a unit `field_hexes` away. penalty: extra % off
    (weather, cover); factor: the target formation's missile_factor. None if out of range."""
    band = field_range(d, att["weapon"], field_hexes)
    if band is None:
        return None
    S = d.units["missile"]
    shots = men * S["rate"].get(att["weapon"], S["default_rate"]) * S["tempo"] * factor
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
    """A blow aimed at a hero: his own parry, then the full wound roll on his kit."""
    if r > atk:
        return
    critical, dfn = r <= crit_at, hero["defence"] + shift
    if not critical and dfn > 0 and rng.randint(1, 100) <= dfn:
        return
    h = roll_hit(d, att["table"], att["weapon"], rng=rng, kit=hero.get("kit"), margin=atk - r, critical=critical)
    sev = h["severity"]
    if sev == "stopped":
        return
    hero["wounds"].append({"loc": h["location"], "mech": h["mechanism"], "sev": sev, "graze": h["graze"]})
    if h["effects"]["lethal"] in d.units["dead_if"]:
        hero["state"] = "dead"
    elif sev != "light" and not h["graze"] and rng.randint(1, 100) > hero["nerve"] - (10 if sev == "critical" else 0):
        hero["state"] = "down"
    t.setdefault("heroes", []).append({"hero": hero["id"], "name": hero["name"], "sev": sev, "loc": h["location"],
                                        "graze": h["graze"], "state": hero["state"]})


def _heroes(u: dict, roles: tuple) -> list:
    return [h for h in u.get("heroes", []) if h["state"] == "up" and h["role"] in roles]


def front_men(d: Data, u: dict) -> int:
    """Men in the unit's front rank: the ones a blow on its front falls among."""
    rows, men = footprint(d, u), men_by_hex(d, u)
    return sum(min(form(d, u)["abreast"], men[k]) for k in range(len(rows[0]))) if rows else 0


def _exposure(d: Data, u: dict, rout: bool, missile: bool = False) -> tuple:
    """(hero, chance) for each hero of unit u a blow on it may fall on."""
    if rout or missile:
        return tuple((h, 1 / max(1, u["men"])) for h in _heroes(u, ("front", "ranged", "behind" if rout else "")))
    return tuple((h, min(1, d.units["heroes"]["exposure"] / max(1, front_men(d, u)))) for h in _heroes(u, ("front", "ranged")))


def _hero_side(u: dict, hero: dict, table: str) -> dict:
    return {"table": table, "weapon": hero["weapon"], "kit": hero.get("kit"), "quality": u["quality"], "skill": hero["attack"]}


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


def _out(u: dict) -> bool:
    """Broken, fled or with no men: out of the fight for striking and shooting."""
    return u["state"] in ("broken", "fled") or u["men"] <= 0


def _strike_groups(d: Data, units: list, occ: dict, i: int, groups: dict, field: dict | None = None) -> None:
    """Add unit i's front hexes' strikes to groups {(i, j, situation, penalty, stakes): men}."""
    u = units[i]
    rows, men = footprint(d, u), men_by_hex(d, u)
    reach = d.weapons[u["weapon"]].get("reach", 1)
    abreast = form(d, u)["abreast"]
    per = abreast * (2 if reach >= d.units["melee"]["second_rank_reach"] else 1)
    for k, h in enumerate(rows[0] if rows else []):
        hit = _struck_hex(units, occ, u, h)
        if hit is None:
            continue
        j, dirn = hit
        x = step(h, dirn)
        blocked, pen, stk = _across(d, field, u, h, x, reach)
        n = min(abreast if reach >= 2 else 0, men[k]) if blocked else min(per, men[k])
        if n > 0:
            key = (i, j, arc(units[j]["facing"], dirn + 3), pen, stk)
            groups[key] = groups.get(key, 0) + n


# ---------- the field: ground, works and weather ----------
# field: {ground: {hex key: kind of ground (units.yaml ground; open if not given)}, works:
# {edges, hexes} as on the battle map (gravewounds/combat.py), weather: {cond, wind, ground:
# {mud, snow}} or None, size: [cols, rows]}. None: open ground, no works, no weather.

def _size(d: Data, field: dict | None) -> tuple:
    if field and field.get("size"):
        return tuple(field["size"])
    return d.units["map"]["cols"], d.units["map"]["rows"]


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
    """Who shoots at whom: [{att, dfd, men, dist, cover, penalty, misfire}]. A unit with a
    missile weapon, not broken and not in contact, shoots at the nearest enemy unit in range
    (and in sight, in the weather) in front of it (ties: the first listed). Its front hexes'
    first `shoot_ranks` ranks shoot. cover: % off from the works and ground at the nearest
    target hex; penalty and misfire: the weather's (gravewounds.combat.weather_attack)."""
    occ, out = occupancy(d, units), []
    for i, u in enumerate(units):
        if u["state"] in ("broken", "fled") or u["men"] <= 0 or "range" not in d.weapons[u["weapon"]]:
            continue
        if in_contact(d, units, occ, i):
            continue
        best = _target(d, units, i, field)
        if best is None:
            continue
        rows, men = footprint(d, u), men_by_hex(d, u)
        per_hex = form(d, u)["abreast"] * min(d.units["shoot_ranks"], form(d, u)["ranks"])
        shooters = sum(min(per_hex, men[k]) for k in range(len(rows[0])))
        wx = shot_weather(d, field, u["weapon"], best[0])
        out.append({"att": i, "dfd": best[1], "men": shooters, "dist": best[0], "cover": cover_at(d, field, best[2], best[3]),
                    "penalty": wx["penalty"], "misfire": wx["misfire"]})
    return out


def shot_weather(d: Data, field: dict | None, weapon: str, dist: int) -> dict:
    """The weather's effect on a shot `dist` field hexes away: {blocked, penalty, misfire}."""
    return C.weather_attack(d, (field or {}).get("weather"), weapon, dist * d.units["range_scale"])


def cover_at(d: Data, field: dict | None, h, t) -> int:
    """% off shots from hex h at hex t: the best of the works' cover and the ground's."""
    if not field:
        return 0
    cols, rows = _size(d, field)
    return max(C.missile_cover(d, _works(field), h, t, cols, rows)["cover"], ground_at(d, field, t).get("cover", 0))


def _target(d: Data, units: list, i: int, field: dict | None = None):
    """(distance, index, shooter hex, target hex) of the nearest enemy unit in range, in
    sight and in front of unit i, or None."""
    u, fv, best = units[i], _fvec(units[i]["facing"]), None
    front = footprint(d, u)[0]
    for j, e in enumerate(units):
        if e["side"] == u["side"] or e["men"] <= 0 or e["state"] == "fled":
            continue
        near = _nearest_ahead(d, u["weapon"], front, fv, [t for row in footprint(d, e) for t in row], field)
        if near is not None and (best is None or near[0] < best[0]):
            best = (near[0], j, near[1], near[2])
    return best


def _nearest_ahead(d: Data, weapon: str, front: list, fv: tuple, hexes: list, field: dict | None = None):
    """(distance, front hex, target hex): the shortest distance in range and in sight from a
    front hex to one of `hexes` ahead of the line, or None."""
    best = None
    for t in hexes:
        c = _cube(t)
        for h in front:
            s = _cube(h)
            if sum((c[k] - s[k]) * fv[k] for k in range(3)) <= 0:
                continue
            dist = hdist(h, t)
            if (best is None or dist < best[0]) and field_range(d, weapon, dist) is not None \
                    and not shot_weather(d, field, weapon, dist)["blocked"]:
                best = (dist, h, t)
    return best


def _side(u: dict, table: str) -> dict:
    return {"table": table, "weapon": u["weapon"], "kit": u.get("kit"), "quality": u["quality"]}


def exchange(d: Data, units: list, table: str, rng, field: dict | None = None) -> tuple[list, list]:
    """One exchange on the field map: every melee and volley at once from the present
    positions, then breaching, losses, morale, and a rout strike on any unit that breaks.
    Returns (units, log): log lines are {kind (melee, volley, hero, herohit, breach, rout,
    morale), ...}. field: the ground, works and weather (see field_ground); works being
    breached are updated in it, in place."""
    us = [_copy_unit(u) for u in units]
    lost, dead, dealt, flanked, log = [0] * len(us), [0] * len(us), [0] * len(us), [False] * len(us), []
    acc = (lost, dead, dealt)
    log += _strike_all(d, us, table, rng, acc, flanked, field)
    log += _shoot_all(d, us, table, rng, acc, field)
    log += _breach_all(d, us, field)
    occ = occupancy(d, us)
    before = [u["men"] for u in us]
    for i, u in enumerate(us):
        cut = min(lost[i], u["men"])
        u.update(men=u["men"] - cut, down=u.get("down", 0) + cut, dead=u.get("dead", 0) + min(dead[i], cut))
    log += _morale_all(d, us, occ, before, lost, dealt, flanked, rng, table)
    for u in us:
        u["charged"] = False
    return us, log


def _strike_all(d: Data, us: list, table: str, rng, acc: tuple, flanked: list, field: dict | None = None) -> list:
    """Every melee, each unit's front heroes striking with its first."""
    log, struck = [], set()
    for s in strikes(d, us, field):
        a, b = us[s["att"]], us[s["dfd"]]
        opts = {"situation": s["situation"], "charge": bool(a.get("charged")) and bool(a.get("mounted")) and not s.get("stakes"),
                "shaken": a["state"] == "shaken", "rout": s["rout"], "exposed": _exposure(d, b, s["rout"]), "penalty": s.get("penalty", 0)}
        t = _take_hurt(b, melee(d, _side(a, table), _side(b, table), s["men"], rng, **opts))
        _tally(*acc, s, t)
        flanked[s["dfd"]] = flanked[s["dfd"]] or s["situation"] in ("flank", "rear")
        log += _logged({"kind": "rout" if s["rout"] else "melee", **s}, t)
        if s["att"] in struck:
            continue
        struck.add(s["att"])
        for hero in _heroes(a, ("front",)):
            t = _take_hurt(b, melee(d, _hero_side(a, hero, table), _side(b, table), d.units["heroes"]["tempo"], rng, **opts))
            _tally(*acc, s, t)
            log += _logged({"kind": "hero", "hero": hero["id"], "name": hero["name"], "att": s["att"], "dfd": s["dfd"],
                            "situation": s["situation"]}, t)
    return log


def _shoot_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None = None) -> list:
    """Every volley, each unit's shooting heroes with it."""
    log = []
    for v in volleys(d, us, field):
        b = us[v["dfd"]]
        opts = {"factor": form(d, b)["missile_factor"] * (100 - v["misfire"]) / 100, "exposed": _exposure(d, b, False, True),
                "penalty": v["cover"] + v["penalty"]}
        t = _take_hurt(b, volley(d, _side(us[v["att"]], table), _side(b, table), v["men"], v["dist"], rng, **opts))
        _tally(*acc, v, t)
        log += _logged({"kind": "volley", **v}, t)
        for hero in _heroes(us[v["att"]], ("ranged",)):
            wx = shot_weather(d, field, hero["weapon"], v["dist"])
            if field_range(d, hero["weapon"], v["dist"]) is None or wx["blocked"]:
                continue
            hopts = {**opts, "factor": form(d, b)["missile_factor"] * (100 - wx["misfire"]) / 100, "penalty": v["cover"] + wx["penalty"]}
            t = _take_hurt(b, volley(d, _hero_side(us[v["att"]], hero, table), _side(b, table), d.units["heroes"]["tempo"], v["dist"], rng, **hopts))
            _tally(*acc, v, t)
            log += _logged({"kind": "hero", "hero": hero["id"], "name": hero["name"], "att": v["att"], "dfd": v["dfd"], "dist": v["dist"]}, t)
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
        if not u.get("breach") or _out(u):
            continue
        rows, men = footprint(d, u), men_by_hex(d, u)
        for k, h in enumerate(rows[0] if rows else []):
            hit = _breachable(d, field, u, h)
            if hit is None:
                continue
            kind, where, it = hit
            it["progress"] = it.get("progress", 0) + min(form(d, u)["abreast"], men[k]) * per
            if not C.intact(d, kind, it):
                log.append({"kind": "breach", "unit": i, "work": it["type"], "at": where})
    return log


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
                heroes=[dict(h, wounds=list(h.get("wounds", []))) for h in u.get("heroes", [])])


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
        t = _take_hurt(b, melee(d, _side(a, table), _side(b, table), a["men"], rng, rout=True, exposed=_exposure(d, b, True)))
        cut = min(t["down"], b["men"])
        b.update(men=b["men"] - cut, down=b["down"] + cut, dead=b["dead"] + min(t["dead"], cut))
        log += _logged({"kind": "rout", "att": i, "dfd": j, "men": a["men"], "situation": "rear", "rout": True}, t)
    return log


# ---------- movement ----------

def allowance(d: Data, u: dict) -> int:
    """Hexes a unit may move in an exchange (twice this for a charge)."""
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
    """Movement for the unit's middle hex to step from a to b: 1, plus works crossed and
    entered, plus the ground (rough, woods, marsh), plus deep mud or snow. None if it cannot."""
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
        for dirn in range(6):
            x = tuple(step(list(h), dirn))
            if not (0 <= x[0] < size[0] and 0 <= x[1] < size[1]) or f"{x[0]},{x[1]}" in occ:
                continue
            sc = step_cost(d, field, u, list(h), list(x))
            if sc is None or cost + sc > limit or cost + sc >= best.get(x, limit + 1):
                continue
            best[x] = cost + sc
            heapq.heappush(heap, (cost + sc, x))
    return None


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
