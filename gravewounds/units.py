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
           penalty: int = 0, factor: float = 1.0) -> dict | None:
    """One exchange of `men` shooting at a unit `field_hexes` away. penalty: extra % off
    (weather, cover); factor: the target formation's missile_factor. None if out of range."""
    band = field_range(d, att["weapon"], field_hexes)
    if band is None:
        return None
    S = d.units["missile"]
    shots = men * S["rate"].get(att["weapon"], S["default_rate"]) * S["tempo"] * factor
    atk = quality(d, att["quality"])["attack"] + att.get("attack", 0) - band["penalty"] - penalty
    return _blows(d, att, dfd, _count(shots, rng), atk, 0, rng)


def _blows(d: Data, att: dict, dfd: dict, n: int, atk: int, dfn: int, rng: random.Random) -> dict:
    t = _new_tally()
    t["blows"] = n
    atk = max(0, atk)
    crit_at = math.floor(atk * d.wounds["combat"]["critical_fraction"])
    for _ in range(n):
        r = rng.randint(1, 100)
        if r > atk:
            t["missed"] += 1
            continue
        critical = r <= crit_at
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


def strikes(d: Data, units: list) -> list:
    """Who strikes whom this exchange: [{att, dfd, men, situation, rout}], in a fixed order.
    Each front hex of a unit not broken strikes the enemy hex across its front (its first
    front side that has one) with its front rank, two ranks with reach-2 weapons. A broken
    unit is struck instead by every man of each enemy unit touching it."""
    occ, groups = occupancy(d, units), {}
    for i, u in enumerate(units):
        if not _out(u):
            _strike_groups(d, units, occ, i, groups)
    out = [{"att": i, "dfd": j, "men": n, "situation": sit, "rout": False} for (i, j, sit), n in sorted(groups.items())]
    for j, b in enumerate(units):
        if b["state"] == "broken" and b["men"] > 0:
            out += [{"att": i, "dfd": j, "men": units[i]["men"], "situation": "rear", "rout": True}
                    for i in _adjacent_units(d, units, occ, j)
                    if units[i]["side"] != b["side"] and units[i]["state"] not in ("broken", "fled")]
    return out


def _out(u: dict) -> bool:
    """Broken, fled or with no men: out of the fight for striking and shooting."""
    return u["state"] in ("broken", "fled") or u["men"] <= 0


def _strike_groups(d: Data, units: list, occ: dict, i: int, groups: dict) -> None:
    """Add unit i's front hexes' strikes to groups {(i, j, situation): men}."""
    u = units[i]
    rows, men = footprint(d, u), men_by_hex(d, u)
    reach = d.weapons[u["weapon"]].get("reach", 1)
    per = form(d, u)["abreast"] * (2 if reach >= d.units["melee"]["second_rank_reach"] else 1)
    for k, h in enumerate(rows[0] if rows else []):
        hit = _struck_hex(units, occ, u, h)
        if hit is not None:
            j, dirn = hit
            key = (i, j, arc(units[j]["facing"], dirn + 3))
            groups[key] = groups.get(key, 0) + min(per, men[k])


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


def volleys(d: Data, units: list) -> list:
    """Who shoots at whom: [{att, dfd, men, dist}]. A unit with a missile weapon, not broken
    and not in contact, shoots at the nearest enemy unit in range in front of it (ties: the
    first listed). Its front hexes' first `shoot_ranks` ranks shoot."""
    occ, out = occupancy(d, units), []
    for i, u in enumerate(units):
        if u["state"] in ("broken", "fled") or u["men"] <= 0 or "range" not in d.weapons[u["weapon"]]:
            continue
        if in_contact(d, units, occ, i):
            continue
        best = _target(d, units, i)
        if best is None:
            continue
        rows, men = footprint(d, u), men_by_hex(d, u)
        per_hex = form(d, u)["abreast"] * min(d.units["shoot_ranks"], form(d, u)["ranks"])
        shooters = sum(min(per_hex, men[k]) for k in range(len(rows[0])))
        out.append({"att": i, "dfd": best[1], "men": shooters, "dist": best[0]})
    return out


def _target(d: Data, units: list, i: int):
    """(distance, index) of the nearest enemy unit in range and in front of unit i, or None."""
    u, fv, best = units[i], _fvec(units[i]["facing"]), None
    front = footprint(d, u)[0]
    for j, e in enumerate(units):
        if e["side"] == u["side"] or e["men"] <= 0 or e["state"] == "fled":
            continue
        dist = _nearest_ahead(d, u["weapon"], front, fv, [t for row in footprint(d, e) for t in row])
        if dist is not None and (best is None or dist < best[0]):
            best = (dist, j)
    return best


def _nearest_ahead(d: Data, weapon: str, front: list, fv: tuple, hexes: list) -> int | None:
    """The shortest distance in range from a front hex to one of `hexes` ahead of the line."""
    best = None
    for t in hexes:
        c = _cube(t)
        for h in front:
            s = _cube(h)
            if sum((c[k] - s[k]) * fv[k] for k in range(3)) <= 0:
                continue
            dist = hdist(h, t)
            if field_range(d, weapon, dist) is not None and (best is None or dist < best):
                best = dist
    return best


def _side(u: dict, table: str) -> dict:
    return {"table": table, "weapon": u["weapon"], "kit": u.get("kit"), "quality": u["quality"]}


def exchange(d: Data, units: list, table: str, rng) -> tuple[list, list]:
    """One exchange on the field map: every melee and volley at once from the present
    positions, then losses, morale, and a rout strike on any unit that breaks. Returns
    (units, log): log lines are {kind (melee, volley, rout, morale), ...}."""
    us = [dict(u, hurt=dict(u.get("hurt", {}))) for u in units]
    lost, dead, dealt, flanked, log = [0] * len(us), [0] * len(us), [0] * len(us), [False] * len(us), []
    for s in strikes(d, us):
        a, b = us[s["att"]], us[s["dfd"]]
        t = melee(d, _side(a, table), _side(b, table), s["men"], rng, situation=s["situation"],
                  charge=bool(a.get("charged")) and bool(a.get("mounted")), shaken=a["state"] == "shaken", rout=s["rout"])
        t = _take_hurt(b, t)
        _tally(lost, dead, dealt, s, t)
        flanked[s["dfd"]] = flanked[s["dfd"]] or s["situation"] in ("flank", "rear")
        log.append({"kind": "rout" if s["rout"] else "melee", **s, **t})
    for v in volleys(d, us):
        t = volley(d, _side(us[v["att"]], table), _side(us[v["dfd"]], table), v["men"], v["dist"], rng,
                   factor=form(d, us[v["dfd"]])["missile_factor"])
        t = _take_hurt(us[v["dfd"]], t)
        _tally(lost, dead, dealt, v, t)
        log.append({"kind": "volley", **v, **t})
    occ = occupancy(d, us)
    before = [u["men"] for u in us]
    for i, u in enumerate(us):
        cut = min(lost[i], u["men"])
        u.update(men=u["men"] - cut, down=u.get("down", 0) + cut, dead=u.get("dead", 0) + min(dead[i], cut))
    log += _morale_all(d, us, occ, before, lost, dealt, flanked, rng, table)
    for u in us:
        u["charged"] = False
    return us, log


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
                "men": before[i], "state": u["state"], "leader": u.get("leader"), "flanked": flanked[i],
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
        t = _take_hurt(b, melee(d, _side(a, table), _side(b, table), a["men"], rng, rout=True))
        cut = min(t["down"], b["men"])
        b.update(men=b["men"] - cut, down=b["down"] + cut, dead=b["dead"] + min(t["dead"], cut))
        log.append({"kind": "rout", "att": i, "dfd": j, "men": a["men"], "situation": "rear", "rout": True, **t})
    return log


# ---------- movement ----------

def allowance(d: Data, u: dict) -> int:
    """Hexes a unit may move in an exchange (twice this for a charge)."""
    return d.units["mounted_move"] if u.get("mounted") else form(d, u)["move"]


def turn_cost(d: Data, u: dict) -> int:
    """Hexes of movement to turn the facing one step: 1 for every turn_per hexes of front."""
    n = math.ceil(max(1, u["men"]) / form(d, u)["per_hex"])
    return max(1, math.ceil(min(u["width"], n) / d.units["turn_per"]))


def _fits(d: Data, units: list, i: int, u: dict, size: tuple) -> bool:
    """Unit i placed as u: on the map and on no other unit's hexes."""
    occ = occupancy(d, [x for k, x in enumerate(units) if k != i])
    return all(0 <= h[0] < size[0] and 0 <= h[1] < size[1] and f"{h[0]},{h[1]}" not in occ
               for row in footprint(d, u) for h in row)


def _path_len(d: Data, units: list, i: int, goal, size: tuple, limit: int) -> int | None:
    """Fewest steps for the unit's middle hex from where it is to goal, not through other
    units' hexes; None if more than limit."""
    occ = occupancy(d, [x for k, x in enumerate(units) if k != i])
    start, seen, frontier = units[i]["pos"], {tuple(units[i]["pos"])}, [units[i]["pos"]]
    for n in range(limit + 1):
        if any(h == list(goal) for h in frontier):
            return n
        nxt = []
        for h in frontier:
            for dirn in range(6):
                x = step(h, dirn)
                if tuple(x) in seen or not (0 <= x[0] < size[0] and 0 <= x[1] < size[1]) or f"{x[0]},{x[1]}" in occ:
                    continue
                seen.add(tuple(x))
                nxt.append(x)
        frontier = nxt
    return None if list(goal) != start else 0


def move(d: Data, units: list, i: int, pos, facing: int, size: tuple) -> dict:
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
    steps = _path_len(d, units, i, pos, size, most)
    if steps is None:
        return {"ok": False, "why": "too far, or no way through"}
    moved = {**u, "pos": list(pos), "facing": facing % 6}
    if not _fits(d, units, i, moved, size):
        return {"ok": False, "why": "no room there"}
    cost = steps + turns * turn_cost(d, u)
    after = [moved if k == i else x for k, x in enumerate(units)]
    contact = in_contact(d, after, occupancy(d, after), i)
    if cost <= allowance(d, u):
        return {"ok": True, "cost": cost, "charge": contact and steps > 0}
    if contact and u["state"] == "steady" and cost <= most:
        return {"ok": True, "cost": cost, "charge": True}
    return {"ok": False, "why": "too far"}


def flee(d: Data, units: list, i: int, size: tuple) -> dict:
    """A broken unit runs straight back as far as its allowance takes it; off the map, it has
    fled the field. Returns the unit."""
    u = dict(units[i])
    back = (u["facing"] + 3) % 6
    for _ in range(allowance(d, u)):
        nxt = {**u, "pos": step(u["pos"], back)}
        if not all(0 <= h[0] < size[0] and 0 <= h[1] < size[1] for row in footprint(d, nxt) for h in row):
            return {**u, "state": "fled"}
        if not _fits(d, units, i, nxt, size):
            break
        u = nxt
    return u


# ---------- after the battle ----------

def standing(u: dict) -> bool:
    return u["men"] > 0 and u["state"] in ("steady", "shaken")


def aftermath(d: Data, units: list, care: list, rng) -> list:
    """What becomes of each unit's wounded when the battle ends (units.yaml aftermath). care:
    each unit's camp care (none, field, shelter). Returns, per unit, {left (down men left on a
    lost field, dead), died (of wounds before treatment), cases (survivors on the wound
    track)}. A man wounded twice is counted once: the down are capped at those down and not
    dead, the walking wounded at the men still on their feet."""
    A, d100 = d.units["aftermath"], (lambda: rng.randint(1, 100))
    lost_sides = {u["side"] for u in units} - {u["side"] for u in units if standing(u)}
    out = []
    for i, u in enumerate(units):
        r = {"left": 0, "died": 0, "cases": []}
        room = {"1": max(0, u.get("down", 0) - u.get("dead", 0)), "0": max(0, u["men"])}
        abandon = A["left_behind"] and u["side"] in lost_sides
        for k in sorted(u.get("hurt", {})):
            sev, lethal, inf, down = k.split("|")
            n = min(u["hurt"][k], room[down])
            room[down] -= n
            if down == "1" and abandon:
                r["left"] += n
                continue
            for _ in range(n):
                if _dies(A, lethal, care[i], d100):
                    r["died"] += 1
                else:
                    r["cases"].append(wound_case(d, sev, lethal, inf, d100))
        out.append(r)
    return out


def _dies(A: dict, lethal: str, care: str, d100) -> bool:
    """A wound that kills in minutes or hours: does it, before help comes?"""
    if lethal == "minutes":
        return d100() > A["saved"]["minutes"]
    if lethal == "hours":
        return d100() > A["saved"]["hours"][care]
    return False
