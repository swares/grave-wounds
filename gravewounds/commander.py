"""The scripted enemy commander of the field map: each of its side's moves, it orders that
side's units in turn, by their quality (units.yaml commander). Mirrored exactly by
templates/units.js (command)."""
from __future__ import annotations

import heapq

from . import units as U
from .model import Data

ROUTED = ("broken", "fled")


def command(d: Data, units: list, side, size: tuple, field: dict | None, rng, exchange=None, stance: str = "attack") -> tuple:
    """Orders for every unit of `side`, in turn (each sees the moves before it). exchange: units
    that came on in it (arrived) wait. stance: attack (close with the enemy) or hold (stand,
    charging only what it can reach). -> (units after, orders [{unit, act, ...}])."""
    us, orders = [dict(u) for u in units], []
    for i in range(len(us)):
        if us[i]["side"] != side or not _free(d, us, i, exchange):
            continue
        roll = rng.randint(1, 100)
        o = _order(d, us, i, (size, field, stance), roll)
        if o:
            orders.append({"unit": i, **o})
            _apply(us, i, o)
    return us, orders


def _free(d: Data, us: list, i: int, exchange) -> bool:
    """A unit it can order: standing, not a battery, not in contact, not just come on."""
    u = us[i]
    if u["state"] in ROUTED or u["men"] <= 0 or U.is_battery(d, u):
        return False
    if exchange is not None and u.get("arrived") == exchange:
        return False
    return not U.in_contact(d, us, U.occupancy(d, us), i)


def _order(d: Data, us: list, i: int, ctx: tuple, roll: int) -> dict | None:
    """One unit's order, or None (it holds). ctx: (size, field, stance)."""
    u, C = us[i], d.units["commander"]
    t = target(d, us, i)
    if t is None:
        return None
    if u["state"] != "steady":
        return {"act": "ground", "target": t} if not u.get("prone") and under_fire(d, us, i) else None
    if roll <= C["hesitate"].get(u["quality"], 0):
        return {"act": "hesitate", "target": t, "roll": roll}
    return _best(d, us, i, t, ctx)


def target(d: Data, us: list, i: int) -> int | None:
    """The nearest enemy unit still standing (the first of equals), or None."""
    u = us[i]
    foes = [(U.hdist(u["pos"], e["pos"]), j) for j, e in enumerate(us)
            if e["side"] != u["side"] and e["state"] not in ROUTED and e["men"] > 0]
    return min(foes)[1] if foes else None


def under_fire(d: Data, us: list, i: int) -> bool:
    """An enemy unit's missile weapon reaches unit i."""
    u = us[i]
    return any(e["side"] != u["side"] and e["state"] not in ROUTED and e["men"] > 0 and "range" in d.weapons[e["weapon"]]
               and U.field_range(d, e["weapon"], U.hdist(e["pos"], u["pos"])) is not None for e in us)


def may_charge(d: Data, u: dict, t: dict, stance: str = "attack") -> bool:
    """Men without missiles, steady, with the odds its quality wants in its stance (charge_odds)."""
    if "range" in d.weapons[u["weapon"]] or u["state"] != "steady":
        return False
    mine = u["men"] * U.quality(d, u["quality"])["attack"]
    theirs = t["men"] * U.quality(d, t["quality"])["attack"]
    return 100 * mine >= d.units["commander"]["charge_odds"][stance].get(u["quality"], 100) * theirs


def _best(d: Data, us: list, i: int, t: int, ctx: tuple) -> dict | None:
    """The best-scoring hex it can legally reach, facing the target: a move, a charge, a turn,
    going to ground where it stands, or None (it holds). Holding, it only charges, else stays."""
    (size, field, stance), u, tu = ctx, us[i], us[t]
    hold = stance == "hold"
    free = {**u, "prone": False} if u.get("prone") else u
    base = [free if k == i else x for k, x in enumerate(us)]
    shooter, charge = "range" in d.weapons[u["weapon"]], may_charge(d, u, tu, stance)
    best = _first_move(d, base, i, tu, (size, field), (charge, hold, shooter))
    if best is None:
        f = U.bearing(u["pos"], tu["pos"])
        return _stay(d, us, i, t, f, shooter) if hold and U.move(d, base, i, u["pos"], f, size, field)["ok"] else None
    h, f, m = best
    if h == list(u["pos"]):
        return _stay(d, us, i, t, f, shooter)
    return {"act": "charge" if m["charge"] else "move", "target": t, "pos": h, "facing": f, "cost": m["cost"],
            **({"up": True} if u.get("prone") else {})}


def _first_move(d: Data, base: list, i: int, tu: dict, where: tuple, how: tuple) -> tuple | None:
    """(hex, facing, move) for the best-scoring hex it will move to, or None. A hex touching
    the enemy is a charge (only with the odds); any other must be within its allowance (and
    holding, it goes nowhere but a charge). Lost in the dark or with vehicles that cannot
    move, it may only turn. It tries `tries` of them at most."""
    (size, field), (charge, hold, shooter), u = where, how, base[i]
    if hold and not charge:
        return None
    allow, tries, stuck = U.allowance(d, u), d.units["commander"]["tries"], bool(u.get("lost") or u.get("immobile"))
    reach = reachable(d, base, i, size, allow * (d.units["charge_move"] if charge else 1), field)
    foes = {k for k, j in U.occupancy(d, base).items() if base[j]["side"] != u["side"]}
    for _, c, row, col in sorted((-score(d, field, u, tu, h, c, shooter), c, h[1], h[0]) for h, c in reach.items()):
        h = [col, row]
        f = U.bearing(h, tu["pos"])
        touch = _touches(d, {**u, "pos": h, "facing": f}, foes)
        if ((not charge) if touch else (hold or c > allow)) or (stuck and h != u["pos"]):
            continue
        if tries == 0:
            return None
        tries -= 1
        m = _legal(d, base, i, (h, f, c, touch), (size, field))
        if not _rejects(m, charge, hold):
            return h, f, m
    return None


def _legal(d: Data, base: list, i: int, to: tuple, where: tuple) -> dict:
    """units.move for a hex whose least movement (c) and contact (touch) are known, without
    finding the path again: {ok, cost, charge}. (The commander never orders a unit that is
    running or in contact, and one that may only turn tries no other hex.)"""
    (h, f, c, touch), (size, field), u = to, where, base[i]
    moved = {**u, "pos": h, "facing": f % 6}
    if not U._fits(d, base, i, moved, size, field):
        return {"ok": False}
    turns = min((f - u["facing"]) % 6, (u["facing"] - f) % 6)
    cost = c + turns * U.turn_cost(d, u) + (U.sweep_cost(d, field, {**u, "pos": h}, moved) if turns else 0)
    allow = U.allowance(d, u)
    if cost <= allow:
        return {"ok": True, "cost": cost, "charge": touch and c > 0}
    if touch and u["state"] == "steady" and cost <= allow * d.units["charge_move"]:
        return {"ok": True, "cost": cost, "charge": True}
    return {"ok": False}


def _touches(d: Data, u: dict, foes: set) -> bool:
    """Unit u, placed so, touches a hex the enemy stands on (as units.in_contact)."""
    return any("{0},{1}".format(*U.step(h, dirn)) in foes for row in U.footprint(d, u) for h in row for dirn in range(6))


def _rejects(m: dict, charge: bool, hold: bool) -> bool:
    """A move it will not make: illegal, a charge it has not the odds for, or (holding) anything
    but a charge."""
    if not m["ok"]:
        return True
    return not charge if m["charge"] else hold


def _stay(d: Data, us: list, i: int, t: int, f: int, shooter: bool) -> dict | None:
    """Staying where it is: a unit on the ground stays down; else it turns to the target, or a
    unit with a modern weapon (ground_with) under fire goes to ground (if its quality heeds cover)."""
    u, C = us[i], d.units["commander"]
    if u.get("prone"):
        return None
    if f != u["facing"]:
        return {"act": "turn", "target": t, "facing": f}
    dig = shooter and u["weapon"] in C["ground_with"] and C["cover"].get(u["quality"], 0) > 0 and under_fire(d, us, i)
    return {"act": "ground", "target": t} if dig else None


def score(d: Data, field: dict | None, u: dict, tu: dict, h: tuple, cost: int, shooter: bool) -> int:
    """How much the commander likes unit u ending at h (higher is better)."""
    C, q = d.units["commander"], u["quality"]
    dist = U.hdist(list(h), tu["pos"])
    s = C["cover"].get(q, 0) * U.cover_at(d, field, tu["pos"], list(h)) - cost
    if shooter:
        inr = dist >= 1 and U.field_range(d, u["weapon"], dist) is not None
        return s + (C["in_range"] if inr else -C["closing"] * dist) - (C["too_close"] if dist < C["keep_off"] else 0)
    flank = C["flank"].get(q, 0) if U.arc(tu["facing"], U.bearing(tu["pos"], list(h))) != "front" else 0
    return s - C["closing"] * dist + flank


def reachable(d: Data, units: list, i: int, size: tuple, limit: int, field: dict | None = None) -> dict:
    """{hex: least movement} for every hex the unit's middle hex can reach within limit (as
    units._path_len, which it agrees with), its own hex included."""
    occ = U.occupancy(d, [x for k, x in enumerate(units) if k != i])
    start = tuple(units[i]["pos"])
    best, heap, done = {start: 0}, [(0, start)], {}
    while heap:
        cost, h = heapq.heappop(heap)
        if h in done:
            continue
        done[h] = cost
        for x, c in U._steps_from(d, field, units[i], h, occ, size):
            if cost + c <= limit and cost + c < best.get(x, limit + 1):
                best[x] = cost + c
                heapq.heappush(heap, (cost + c, x))
    return done


def _apply(us: list, i: int, o: dict) -> None:
    """Carry out an order on the units (as the page's own move: charged when it charges)."""
    u = us[i]
    if o["act"] == "ground":
        us[i] = {**u, "prone": True}
    elif o["act"] == "turn":
        us[i] = {**u, "facing": o["facing"]}
    elif o["act"] in ("move", "charge"):
        us[i] = {**u, "pos": o["pos"], "facing": o["facing"], "charged": o["act"] == "charge", **({"prone": False} if o.get("up") else {})}
