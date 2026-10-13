"""The scripted enemy commander of the field map: each of its side's moves, it orders that
side's units in turn, by their quality (units.yaml commander). Mirrored exactly by
templates/units.js (command)."""
from __future__ import annotations

import heapq

from . import units as U
from .model import Data

ROUTED = ("broken", "fled")


def command(d: Data, units: list, side, size: tuple, field: dict | None, rng, exchange=None, stance: str = "attack",
            memory: dict | None = None) -> tuple:
    """Orders for every unit of `side`, in turn (each sees the moves before it). exchange: units
    that came on in it (arrived) wait. stance: attack (close with the enemy) or hold (stand,
    charging only what it can reach). memory: where it last saw each enemy unit, kept between
    its moves (updated in place; see sightings). -> (units after, orders [{unit, act, ...}])."""
    us, orders = [dict(u) for u in units], []
    memory = {} if memory is None else memory
    known = sightings(d, us, side, field, exchange, memory)
    _hold_back(d, us, side, known)
    orders += _commit(d, us, side, known, memory)
    for i in range(len(us)):
        if us[i]["side"] != side or not _free(d, us, i, exchange):
            continue
        roll = rng.randint(1, 100)
        o = _order(d, us, i, (size, field, stance, known, exchange), roll)
        if o:
            orders.append({"unit": i, **o})
            _apply(us, i, o)
    orders += _lay_guns(d, us, side, (size, field, known, exchange))
    return us, orders + _call_fire(d, us, side, field, known)


def _free(d: Data, us: list, i: int, exchange) -> bool:
    """A unit it can order: standing, not a battery or anti-tank guns, not in contact, not just come on."""
    u = us[i]
    if u["state"] in ROUTED or u["men"] <= 0 or U.is_battery(d, u) or U.is_at_gun(d, u):
        return False
    if exchange is not None and u.get("arrived") == exchange:
        return False
    return not U.in_contact(d, us, U.occupancy(d, us), i)


def _hold_back(d: Data, us: list, side, known: dict) -> None:
    """At its first move, unless the GM has marked reserves for the side (any of its units has
    `reserve` set), it holds back its rearmost units, furthest from the nearest enemy it knows
    of (else any), up to commander.reserve % of the side's men by the quality most of them have.
    Every unit of the side gets `reserve` (True or False), so it is done once."""
    mine = [i for i, u in enumerate(us) if u["side"] == side and u["men"] > 0 and u["state"] not in ROUTED]
    if not mine or any("reserve" in us[i] for i in mine):
        return
    men, by_q = sum(us[i]["men"] for i in mine), {}
    for i in mine:
        by_q[us[i]["quality"]] = by_q.get(us[i]["quality"], 0) + us[i]["men"]
    q = max(sorted(by_q), key=lambda k: by_q[k])
    room = men * d.units["commander"]["reserve"].get(q, 0) // 100
    foes = [j for j, e in enumerate(us) if e["side"] != side and e["men"] > 0 and e["state"] not in ROUTED and (not known or str(j) in known)]
    far = sorted(mine, key=lambda i: (-min((U.hdist(us[i]["pos"], _where(us, j, known)["pos"]) for j in foes), default=0), i))
    for i in mine:
        us[i]["reserve"] = False
    for i in far:
        if U.is_battery(d, us[i]) or U.is_at_gun(d, us[i]) or us[i]["men"] > room:
            continue
        us[i]["reserve"] = True
        room -= us[i]["men"]


def _commit(d: Data, us: list, side, known: dict, memory: dict) -> list:
    """Commit one reserve unit this move, the one nearest an enemy it knows of, when a unit of
    the side has broken or fled since its last move, when a known enemy is within
    commander.gap hexes of a reserve unit, or (a veteran reserve unit) when an enemy unit has
    broken. -> [the commit order], or []."""
    plan = memory.setdefault("plan", {})
    own = sum(1 for u in us if u["side"] == side and u["state"] in ROUTED)
    foe = sum(1 for u in us if u["side"] != side and u["state"] in ROUTED)
    broke, foe_broke = own > plan.get("own", own), foe > plan.get("foe", foe)
    plan.update(own=own, foe=foe)
    held = [i for i, u in enumerate(us) if u["side"] == side and u.get("reserve") and u["men"] > 0 and u["state"] not in ROUTED]
    if not held:
        return []
    near = {i: min((U.hdist(us[i]["pos"], m["pos"]) for k, m in known.items() if k.isdigit()), default=10**6) for i in held}
    gap = [i for i in held if near[i] <= d.units["commander"]["gap"]]
    if broke or gap:
        pick, why = min(held, key=lambda i: (near[i], i)), "broke" if broke else "gap"
    elif foe_broke and any(us[i]["quality"] == "veteran" for i in held):
        pick, why = min((i for i in held if us[i]["quality"] == "veteran"), key=lambda i: (near[i], i)), "exploit"
    else:
        return []
    us[pick]["reserve"] = False
    return [{"unit": pick, "act": "commit", "why": why}]


def _lay_guns(d: Data, us: list, side, ctx: tuple) -> list:
    """Its batteries and anti-tank guns on the map, steady and out of contact, turn to face the
    nearest enemy it knows of (if the turn is legal). It never moves, limbers or displaces them."""
    size, field, known, exchange = ctx
    out, occ = [], U.occupancy(d, us)
    for i, u in enumerate(us):
        if u["side"] != side or not (U.is_battery(d, u) or U.is_at_gun(d, u)) or u["state"] != "steady" or u["men"] <= 0:
            continue
        if (exchange is not None and u.get("arrived") == exchange) or U.in_contact(d, us, occ, i):
            continue
        foes = [(U.hdist(u["pos"], m["pos"]), int(k)) for k, m in known.items() if k.isdigit()]
        if not foes:
            continue
        j = min(foes)[1]
        f = U.bearing(u["pos"], _where(us, j, known)["pos"])
        if f != u["facing"] and U.move(d, us, i, u["pos"], f, size, field)["ok"]:
            us[i] = {**u, "facing": f}
            out.append({"unit": i, "act": "turn", "target": j, "facing": f})
    return out


def _call_fire(d: Data, us: list, side, field: dict | None, known: dict) -> list:
    """Each of its off-map batteries (not tanks or aircraft) with no mission, rounds and tubes,
    not displacing, is called on the enemy unit it sees now that scores best as a target for
    the side's unit nearest it (threat_score), at the first of its hexes the side can see, in
    the battery's reach, with none of the side's men within the kind's radius and scatter."""
    out = []
    for k, b in enumerate((field or {}).get("support") or []):
        K = d.units["indirect"]["kinds"][b["kind"]]
        if b["side"] != side or b.get("mission") or K.get("direct") or K.get("air") or b.get("displacing") or b.get("rounds", 0) <= 0 or U.served_tubes(d, b) <= 0:
            continue
        aim = _fire_aim(d, us, side, field, known, (b, K))
        if aim:
            b["mission"] = {"hex": aim[1], "wait": K["delay"], "repeat": False}
            out.append({"unit": None, "act": "fire", "battery": k, "target": aim[0], "hex": aim[1]})
    return out


def _fire_aim(d: Data, us: list, side, field: dict | None, known: dict, bk: tuple) -> tuple | None:
    """(enemy index, hex) for battery b (kind K) to fire on, or None (_call_fire)."""
    b, K = bk
    best = None
    ours = [u for u in us if u["side"] == side and u["men"] > 0 and u["state"] != "fled"]
    for j, e in enumerate(us):
        if e["side"] == side or str(j) not in known or not ours:
            continue
        h = next((x for x in _marks(d, e) if U.spotted(d, us, field, side, x)), None)
        if h is None or not U.in_reach(d, b, h) or _too_near(d, ours, h, K["radius"] + K["scatter"]):
            continue
        u = min(ours, key=lambda o: U.hdist(o["pos"], e["pos"]))
        key = (-threat_score(d, u, e, e), j)
        if best is None or key < best[0]:
            best = (key, (j, list(h)))
    return None if best is None else best[1]


def _marks(d: Data, e: dict) -> list:
    """The hexes the enemy unit is seen by: its middle hex, then either end of its front row."""
    rows = U.footprint(d, e)
    return [e["pos"]] + ([rows[0][0], rows[0][-1]] if rows else [])


def _too_near(d: Data, ours: list, h, r: int) -> bool:
    """Whether any of the side's units has a hex within r of hex h."""
    return any(U.hdist(x, h) <= r for u in ours for row in U.footprint(d, u) for x in row)


def sightings(d: Data, us: list, side, field: dict | None, exchange, memory: dict) -> dict:
    """Where the side knows each enemy unit to be: {index (str): {pos, facing, ex}}. An enemy
    one of its units can see now (units.spotted: sight, light, woods, smoke) at its middle hex
    or either end of its front is set where it stands; one not seen for more than `remember`
    exchanges, or broken, fled or gone, is forgotten. memory is updated in place."""
    ex = exchange or 0
    for j, e in enumerate(us):
        k = str(j)
        if e["side"] == side:
            continue
        if e["state"] in ROUTED or e["men"] <= 0:
            memory.pop(k, None)
        elif _seen(d, us, side, field, e):
            memory[k] = {"pos": list(e["pos"]), "facing": e["facing"], "ex": ex}
        elif k in memory and ex - memory[k]["ex"] > d.units["commander"]["remember"]:
            del memory[k]
    return memory


def _seen(d: Data, us: list, side, field: dict | None, e: dict) -> bool:
    """A unit of side sees enemy e: its middle hex or either end of its front row."""
    return any(U.spotted(d, us, field, side, h) for h in _marks(d, e))


def _order(d: Data, us: list, i: int, ctx: tuple, roll: int) -> dict | None:
    """One unit's order, or None (it holds). ctx: (size, field, stance, known, exchange)."""
    u, C = us[i], d.units["commander"]
    t = target(d, us, i, ctx[3])
    if u["state"] != "steady":
        return {"act": "ground", "target": t} if not u.get("prone") and under_fire(d, us, i) else None
    if t is None:
        return None
    if u.get("reserve"):
        return _stay(d, us, i, t, u["facing"], "range" in d.weapons[u["weapon"]])
    if roll <= C["hesitate"].get(u["quality"], 0):
        return {"act": "hesitate", "target": t, "roll": roll}
    return _last_seen(_best(d, us, i, t, ctx), ctx[3], t, ctx[4])


def _last_seen(o: dict | None, known: dict | None, t: int, exchange) -> dict | None:
    """The order, with the exchange its target was last seen in ("last") if not this one."""
    last = (known or {}).get(str(t), {}).get("ex")
    return {**o, "last": last} if o and last is not None and last != (exchange or 0) else o


def target(d: Data, us: list, i: int, known: dict | None = None) -> int | None:
    """The enemy unit it goes for among those its side knows of (known: sightings; None: every
    one standing), or None: the best by threat_score (the first of equals)."""
    u = us[i]
    foes = [(-threat_score(d, u, us[j], _where(us, j, known)), j) for j, e in enumerate(us)
            if e["side"] != u["side"] and e["state"] not in ROUTED and e["men"] > 0 and (known is None or str(j) in known)]
    return min(foes)[1] if foes else None


def _where(us: list, j: int, known: dict | None) -> dict:
    """Enemy unit j as the side knows it: where it was last seen (as it is if seen now)."""
    m = (known or {}).get(str(j))
    return us[j] if m is None else {**us[j], "pos": m["pos"], "facing": m["facing"]}


def threat_score(d: Data, u: dict, e: dict, seen: dict) -> int:
    """How much unit u wants enemy e (seen: e where u's side knows it to be): `closing` off a
    hex away, and by its quality's `sense`, the % of e's men down times `hurt`, `shaken` if e
    is shaken, and `threat` if e is a danger to u (shooters for men without missiles, men
    without missiles in a charge's reach for shooters). Green men take the nearest."""
    C = d.units["commander"]
    dist = U.hdist(u["pos"], seen["pos"])
    sense = C["sense"].get(u["quality"], 0)
    if not sense:
        return -C["closing"] * dist
    down = (e.get("down") or 0) * 100 // max(1, e.get("start") or e["men"])
    shooter, theirs = "range" in d.weapons[u["weapon"]], "range" in d.weapons[e["weapon"]]
    danger = (not shooter and theirs) or (shooter and not theirs and dist <= U.allowance(d, e) * d.units["charge_move"])
    weak = C["hurt"] * down + (C["shaken"] if e["state"] == "shaken" else 0) + (C["threat"] if danger else 0)
    return sense * weak - C["closing"] * dist


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
    (size, field, stance, known, _), u = ctx, us[i]
    tu, hold = _where(us, t, known), stance == "hold"
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
        if _skips(touch, (charge, hold), c > allow, stuck and h != u["pos"]):
            continue
        if tries == 0:
            return None
        tries -= 1
        m = _legal(d, base, i, (h, f, c, touch), (size, field))
        if not _rejects(m, charge, hold):
            return h, f, m
    return None


def _skips(touch: bool, how: tuple, far: bool, stuck: bool) -> bool:
    """A hex it will not try: touching the enemy without the odds to charge; not touching but
    beyond its allowance (far), or anything but a charge when holding; or a new hex for a unit
    that may only turn (stuck)."""
    charge, hold = how
    if stuck:
        return True
    return not charge if touch else hold or far


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
    s = C["cover"].get(q, 0) * U.cover_at(d, field, tu["pos"], list(h)) - cost - C["mines"].get(q, 0) * _mined(field, u["pos"], h)
    if shooter:
        inr = dist >= 1 and U.field_range(d, u["weapon"], dist) is not None
        return s + (C["in_range"] if inr else -C["closing"] * dist) - (C["too_close"] if dist < C["keep_off"] else 0)
    flank = C["flank"].get(q, 0) if U.arc(tu["facing"], U.bearing(tu["pos"], list(h))) != "front" else 0
    return s - C["closing"] * dist + flank


def _mined(field: dict | None, a, h) -> int:
    """Hexes of minefields it knows of (marked, or found) on the straight way from a to h, h included."""
    mines = (field or {}).get("mines") or {}
    if not mines or list(a) == list(h):
        return 0
    known = {k for k, m in mines.items() if not m.get("hidden") or m.get("found")}
    return sum(1 for x in U.ray(list(a), list(h), U.hdist(a, h))[1:] if "{0},{1}".format(*x) in known)


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
