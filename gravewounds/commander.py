"""The scripted enemy commander of the field map: each of its side's moves, it orders that
side's units in turn, by their quality (units.yaml commander). Mirrored exactly by
templates/units.js (command)."""
from __future__ import annotations

import heapq

from . import combat as C, units as U
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
    if stance == "attack":
        us, orders = _hook_up(d, us, side, (field, known, exchange))
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
    orders += _move_guns(d, us, side, (size, field, stance, known, exchange))
    orders += _lay_guns(d, us, side, (size, field, known, exchange))
    return us, orders + _call_fire(d, us, side, field, known, (stance, exchange))


def _free(d: Data, us: list, i: int, exchange) -> bool:
    """A unit it can order: standing, not a battery, anti-tank guns or gun tractors, not in contact, not just come on."""
    u = us[i]
    if u["state"] in ROUTED or u["men"] <= 0 or U.is_battery(d, u) or U.is_at_gun(d, u) or _tractor(d, u):
        return False
    if exchange is not None and u.get("arrived") == exchange:
        return False
    return not U.in_contact(d, us, U.occupancy(d, us), i)


def _tractor(d: Data, u: dict) -> bool:
    """Gun tractors (a vehicle kind that tows): not ordered as other units (towing, see _move_guns)."""
    return bool((U.vehicle_kind(d, u) or {}).get("tows"))


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
        if U.is_battery(d, us[i]) or U.is_at_gun(d, us[i]) or _tractor(d, us[i]) or us[i]["men"] > room:
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
    nearest enemy it knows of (if the turn is legal), unless limbered or changing over."""
    size, field, known, exchange = ctx
    out, occ = [], U.occupancy(d, us)
    for i, u in enumerate(us):
        if not _turns_guns(d, us, i, side, (occ, exchange)):
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


# ---------- moving its guns ----------
# Attacking, its guns with no enemy it knows of in their reach (and, with none known, short of
# the objective) go forward: a battery limbers, then moves, then unlimbers once an enemy is in
# reach; anti-tank guns hook up to an empty tractor of their side beside them, are towed, and
# are unhooked once an enemy is in reach. They stop at the hex nearest their goal that has the
# enemy in reach but no nearer than commander.keep_off. Holding, its guns unlimber or are
# unhooked where they are, and never move.

TOW_SLACK = 4   # hexes from its tractor the guns may land when unhooked (units.dismount: up to 4 behind)


def gun_reach(d: Data, u: dict) -> int | None:
    """How far a gun unit's guns reach (a battery, anti-tank guns), or None. A tractor towing
    guns counts TOW_SLACK less, so the guns it unhooks are in reach wherever they land."""
    if U.is_battery(d, u):
        return U.gun_range(d, u)
    if U.is_at_gun(d, u):
        return d.units["anti_tank_guns"]["gun"]["range"]
    R = u.get("riders")
    return d.units["anti_tank_guns"]["gun"]["range"] - TOW_SLACK if R and U.is_at_gun(d, R) else None


def _gun_goal(d: Data, us: list, u: dict, field: dict | None, known: dict) -> tuple:
    """(target index or None, the hex to go for, in reach) for a gun unit: the nearest enemy it
    knows of (ties: the lowest index), else the objective while it is beyond its radius."""
    foes = sorted((U.hdist(u["pos"], m["pos"]), int(k)) for k, m in known.items() if k.isdigit())
    if foes:
        dist, j = foes[0]
        return j, list(_where(us, j, known)["pos"]), dist <= gun_reach(d, u)
    obj = objective(field)
    if obj is None or U.off_objective(d, u, obj) <= U.objective_radii(d, field)[0]:
        return None, None, True
    return None, obj, False


def _gun_ready(d: Data, us: list, i: int, side, exchange) -> bool:
    """A gun unit of the side it may order: steady, with men, not just come on, out of contact,
    not abandoned, changing over or resupplying."""
    u = us[i]
    if u["side"] != side or u["state"] != "steady" or u["men"] <= 0 or u.get("abandoned"):
        return False
    if (exchange is not None and u.get("arrived") == exchange) or u.get("limbering") or u.get("resupplying"):
        return False
    return not U.in_contact(d, us, U.occupancy(d, us), i)


def _hook_up(d: Data, us: list, side, ctx: tuple) -> tuple:
    """Attacking, at the start of its move: anti-tank guns on the map (not emplaced) with no
    known enemy in reach and somewhere to go hook up to the first empty tractor of their side
    beside them that can tow them (units.mount). The guns leave the list, so the enemy indices
    it remembers are moved down. -> (units, [hook orders])."""
    field, known, exchange = ctx
    out, i = [], 0
    while i < len(us):
        u = us[i]
        if not U.is_at_gun(d, u) or u.get("emplaced") or not _gun_ready(d, us, i, side, exchange):
            i += 1
            continue
        _, goal, inr = _gun_goal(d, us, u, field, known)
        j = None if inr or goal is None else next((k for k, c in enumerate(us) if k != i and U._cannot_mount(d, us, i, k) is None), None)
        if j is None:
            i += 1
            continue
        us = U.mount(d, us, i, j)["units"]
        _drop_index(known, i)
        out = [{**o, "unit": o["unit"] - (o["unit"] > i)} for o in out]
        out.append({"unit": j - (j > i), "act": "hook", "guns": u["name"]})
    return us, out


def _drop_index(known: dict, i: int) -> None:
    """Unit i has left the list: the enemy indices remembered above it move down one."""
    moved = {(str(int(k) - 1) if k.isdigit() and int(k) > i else k): v for k, v in known.items()}
    known.clear()
    known.update(moved)


def _turns_guns(d: Data, us: list, i: int, side, ctx: tuple) -> bool:
    """Unit i is a battery or anti-tank guns of the side in action: steady, with men, not
    limbered or changing over, not just come on, out of contact."""
    occ, exchange = ctx
    u = us[i]
    if u["side"] != side or not (U.is_battery(d, u) or U.is_at_gun(d, u)) or u["state"] != "steady" or u["men"] <= 0:
        return False
    if u.get("limbered") or u.get("limbering") or (exchange is not None and u.get("arrived") == exchange):
        return False
    return not U.in_contact(d, us, occ, i)


def _move_guns(d: Data, us: list, side, ctx: tuple) -> list:
    """Its batteries and tractors towing anti-tank guns: limber, move, unlimber or unhook
    (_gun_order); attacking, its empty tractors go to fetch guns (_fetch). -> [orders]."""
    size, field, stance, _, exchange = ctx
    out, claimed = [], set()
    for i in range(len(us)):
        u = us[i]
        if stance == "attack" and _tractor(d, u) and not u.get("riders") and _gun_ready(d, us, i, side, exchange):
            o = _fetch(d, us, i, ctx, claimed)
        elif not (U.is_battery(d, u) or (_tractor(d, u) and gun_reach(d, u))) or not _gun_ready(d, us, i, side, exchange):
            continue
        else:
            o = _gun_order(d, us, i, ctx)
        if o and _gun_apply(d, us, i, o, (size, field, exchange)):
            out.append({"unit": i, **o})
    return out


def _wants_tow(d: Data, us: list, g: int, ctx: tuple) -> bool:
    """Anti-tank guns g of the side would hook up (_hook_up): on the map, not emplaced, ready,
    with no known enemy in reach and somewhere to go."""
    _, field, _, known, exchange = ctx
    e = us[g]
    if not U.is_at_gun(d, e) or e.get("emplaced") or not _gun_ready(d, us, g, e["side"], exchange):
        return False
    _, goal, inr = _gun_goal(d, us, e, field, known)
    return goal is not None and not inr


def _fetch(d: Data, us: list, i: int, ctx: tuple, claimed: set) -> dict | None:
    """An empty tractor goes to fetch the nearest guns of its side that want a tow and that it
    can tow (no other tractor fetching them this move; the first of equals): to the hex in its
    allowance beside them it reaches cheapest, else as near them as it can, facing where the
    guns will go; it does not touch the enemy. They hook up at the side's next move."""
    size, field, _, known, _ = ctx
    u = us[i]
    guns = sorted((U.hdist(u["pos"], e["pos"]), g) for g, e in enumerate(us)
                  if e["side"] == u["side"] and g not in claimed and _wants_tow(d, us, g, ctx)
                  and not any(t() for t, _ in U._tow_checks(d, e, u)))
    if not guns:
        return None
    g = guns[0][1]
    claimed.add(g)
    goal = _gun_goal(d, us, us[g], field, known)[1]
    near = [x for r in U.footprint(d, us[g]) for x in r]
    foes = {k for k, j in U.occupancy(d, us).items() if us[j]["side"] != u["side"]}
    cands = []
    for h, c in reachable(d, us, i, size, U.allowance(d, u), field).items():
        f = U.bearing(list(h), goal)
        moved = {**u, "pos": list(h), "facing": f}
        gap = min(U.hdist(a, b) for r in U.footprint(d, moved) for a in r for b in near)
        cands.append((0 if gap <= 1 else gap, c, h[1], h[0], f))
    tries = d.units["commander"]["tries"]
    for _, c, row, col, f in sorted(cands):
        h = [col, row]
        if h == list(u["pos"]):
            return None
        if _touches(d, {**u, "pos": h, "facing": f}, foes):
            continue
        if tries == 0:
            return None
        tries -= 1
        m = _legal(d, us, i, (h, f, c, False), (size, field))
        if m["ok"]:
            return {"act": "fetch", "target": None, "guns": g, "pos": h, "facing": f, "cost": m["cost"]}
    return None


def _gun_order(d: Data, us: list, i: int, ctx: tuple) -> dict | None:
    """A battery or a tractor towing guns: holding, it unlimbers (or unhooks); attacking, with
    an enemy in reach it unlimbers (unhooks), else a battery in action limbers and one limbered
    (or a tractor) moves toward its goal (_gun_move)."""
    size, field, stance, known, _ = ctx
    u = us[i]
    battery = U.is_battery(d, u)
    t, goal, inr = _gun_goal(d, us, u, field, known)
    if stance == "hold" or inr:
        if battery:
            return {"act": "unlimber", "target": t} if u.get("limbered") else None
        return {"act": "unhook", "target": t}
    if battery and not u.get("limbered"):
        return {"act": "limber", "target": t}
    return _gun_move(d, us, i, (t, goal), (size, field))


def _gun_move(d: Data, us: list, i: int, aim: tuple, where: tuple) -> dict | None:
    """The best hex within its allowance, not touching the enemy, facing its goal: in reach of
    the enemy and no nearer than keep_off (else nearer is better), less the cost and known
    minefields on the way. -> a move (on a target) or advance (on the objective), or None."""
    (t, goal), (size, field), u = aim, where, us[i]
    foes = {k for k, j in U.occupancy(d, us).items() if us[j]["side"] != u["side"]}
    cands = [(-_gun_score(d, field, u, (h, c), aim), c, aside(h, goal), h[1], h[0]) for h, c in reachable(d, us, i, size, U.allowance(d, u), field).items()]
    tries = d.units["commander"]["tries"]
    for _, c, _, row, col in sorted(cands):
        h = [col, row]
        if h == list(u["pos"]):
            return None
        f = U.bearing(h, goal)
        if _touches(d, {**u, "pos": h, "facing": f}, foes):
            continue
        if tries == 0:
            return None
        tries -= 1
        m = _legal(d, us, i, (h, f, c, False), (size, field))
        if m["ok"]:
            return {"act": "move" if t is not None else "advance", "target": t, "pos": h, "facing": f, "cost": m["cost"]}
    return None


def _gun_score(d: Data, field: dict | None, u: dict, hc: tuple, aim: tuple) -> int:
    """How much it likes gun unit u ending at h, c hexes of movement away, going for aim
    (target, goal): in reach of the enemy and no nearer than keep_off (else nearer is better;
    on the objective, nearer), less the cost and known minefields on the way."""
    (h, c), (t, goal), K = hc, aim, d.units["commander"]
    dist = U.hdist(list(h), goal)
    s = -c - K["mines"].get(u["quality"], 0) * _mined(field, u["pos"], h, u["side"])
    if t is None:
        return s - K["closing"] * dist
    return s + (K["in_range"] if K["keep_off"] <= dist <= gun_reach(d, u) else -K["closing"] * dist) - (K["too_close"] if dist < K["keep_off"] else 0)


def _gun_apply(d: Data, us: list, i: int, o: dict, where: tuple) -> bool:
    """Carry out a gun order: limber or unlimber (changing over this exchange), move, or unhook
    the towed guns beside the tractor (in action from the next exchange; added last). False if
    the guns have no room to be unhooked."""
    size, field, exchange = where
    if o["act"] == "unhook":
        r = U.dismount(d, us, i, size, field)
        if not r["ok"]:
            return False
        us[:] = r["units"][:-1] + [{**r["units"][-1], "arrived": exchange, "unhooked": True}]
    elif o["act"] in ("limber", "unlimber"):
        us[i] = {**us[i], "limbering": True}
    else:
        us[i] = {**us[i], "pos": o["pos"], "facing": o["facing"]}
    return True


def _call_fire(d: Data, us: list, side, field: dict | None, known: dict, how: tuple = ("attack", None)) -> list:
    """First its batteries under counter-battery fire displace (_displace). In the dark, one
    battery lights an enemy it has lost sight of (_call_illum).
    Attacking, one battery lays smoke where its units are under fire (_call_smoke).
    Then one battery fires counter-battery on a located enemy battery (_call_counter). Then each
    of its other off-map batteries (not tanks) with no mission, rounds and tubes, not
    displacing, and its aircraft that can fly (_free_air), is called on the enemy unit it sees now that scores best as a
    target for the side's unit nearest it (threat_score), at the first of its hexes the side
    can see, in the battery's reach, with none of the side's men within the kind's radius and
    scatter."""
    stance, exchange = how
    out = _displace(d, field, side)
    free = [k for k, b in enumerate((field or {}).get("support") or []) if _free_battery(d, b, side)]
    out += _call_illum(d, us, side, field, (known, exchange), free)
    out += _call_smoke(d, us, side, field, known, free) if stance == "attack" else []
    out += _call_counter(d, field, side, free)
    air = [k for k, b in enumerate((field or {}).get("support") or []) if _free_air(d, field, b, side)]
    for k in sorted(free + air):
        b = field["support"][k]
        K = d.units["indirect"]["kinds"][b["kind"]]
        if b.get("mission"):
            continue
        aim = _fire_aim(d, us, side, field, known, (b, K))
        if aim:
            b["mission"] = {"hex": aim[1], "wait": K["delay"], "repeat": False}
            out.append({"unit": None, "act": "fire", "battery": k, "target": aim[0], "hex": aim[1]})
    return out


def _displace(d: Data, field: dict | None, side) -> list:
    """Each of its located batteries that an enemy counter-battery mission is aimed at, not
    displacing already, with tubes and a kind that can move (displace > 0), displaces: its
    mission ends and it is silent for its kind's exchanges, then no longer located (where it
    stands, if placed). -> [displace orders]."""
    sup, out = (field or {}).get("support") or [], []
    for k, b in enumerate(sup):
        n = d.units["indirect"]["kinds"][b["kind"]].get("displace", 0)
        if b["side"] != side or not b.get("located") or b.get("displacing") or b.get("tubes", 0) <= 0 or not n:
            continue
        by = next((j for j, x in enumerate(sup) if x["side"] != side and (x.get("mission") or {}).get("battery") == k), None)
        if by is not None:
            b.update(displacing=n, mission=None)
            out.append({"unit": None, "act": "displace", "battery": k, "by": by})
    return out


def _free_air(d: Data, field: dict | None, b: dict, side) -> bool:
    """Its aircraft on call it can send: no mission, attacks and aircraft left, not grounded
    by the weather or the dark (units.grounded)."""
    K = d.units["indirect"]["kinds"][b["kind"]]
    return bool(K.get("air")) and b["side"] == side and not b.get("mission") and b.get("rounds", 0) > 0 \
        and b.get("tubes", 0) > 0 and U.grounded(d, field, b) is None


def _call_illum(d: Data, us: list, side, field: dict | None, kx: tuple, free: list) -> list:
    """In the dark (a light with limited sight), illumination over the enemy it has lost sight
    of (remembered but not seen this exchange) nearest one of its units (the first of equals),
    at its last-seen middle hex if no flare or round lights it or is on its way there, by the free battery with
    illumination rounds (a kind with `illum`) that reaches it and lands soonest (the first of
    equals). -> [the illumination order], or []."""
    known, exchange = kx
    L = U.light_of(d, field)
    ours = [u for u in us if u["side"] == side and u["men"] > 0 and u["state"] != "fled"]
    if L is None or L.get("sight") is None or not ours:
        return []
    lost = sorted((min(U.hdist(o["pos"], m["pos"]) for o in ours), int(k)) for k, m in known.items()
                  if k.isdigit() and m["ex"] != (exchange or 0) and not U.lit(field, m["pos"]))
    sup = (field or {}).get("support") or []
    coming = [(b["mission"]["hex"], d.units["indirect"]["kinds"][b["kind"]].get("illum", 0)) for b in sup
              if b["side"] == side and (b.get("mission") or {}).get("illum")]
    lost = [(n, j) for n, j in lost if not any(U.hdist(known[str(j)]["pos"], c) <= r for c, r in coming)]
    for _, j in lost:
        h = list(known[str(j)]["pos"])
        guns = [(d.units["indirect"]["kinds"][sup[k]["kind"]]["delay"], k) for k in free
                if not sup[k].get("mission") and d.units["indirect"]["kinds"][sup[k]["kind"]].get("illum") and U.in_reach(d, sup[k], h)]
        if guns:
            k = min(guns)[1]
            sup[k]["mission"] = {"hex": h, "wait": d.units["indirect"]["kinds"][sup[k]["kind"]]["delay"], "repeat": False, "illum": True}
            return [{"unit": None, "act": "illum", "battery": k, "target": j, "hex": h}]
    return []


def _call_counter(d: Data, field: dict | None, side, free: list) -> list:
    """Counter-battery: of its free batteries with no mission that can reach (counter > 0, and
    in range of a placed target) a located enemy battery with tubes, the one with the highest
    counter % (the first of equals) fires on the reachable one with the most tubes served (the
    first of equals). -> [the counter order], or []."""
    sup = (field or {}).get("support") or []
    marks = [j for j, x in enumerate(sup) if x["side"] != side and x.get("located") and x.get("tubes", 0) > 0]
    best = None
    for k in free:
        b = sup[k]
        K = d.units["indirect"]["kinds"][b["kind"]]
        if b.get("mission") or not K.get("counter"):
            continue
        aims = [j for j in marks if sup[j].get("place") is None or U.in_reach(d, b, sup[j]["place"])]
        if aims and (best is None or K["counter"] > best[0]):
            best = (K["counter"], k, max(aims, key=lambda j: (U.served_tubes(d, sup[j]), -j)))
    if best is None:
        return []
    _, k, j = best
    sup[k]["mission"] = {"battery": j, "wait": d.units["indirect"]["kinds"][sup[k]["kind"]]["delay"], "repeat": False}
    return [{"unit": None, "act": "counter", "battery": k, "on": j}]


def _free_battery(d: Data, b: dict, side) -> bool:
    """One of its off-map batteries it can call: not tanks or aircraft, no mission, rounds and
    tubes, not displacing."""
    K = d.units["indirect"]["kinds"][b["kind"]]
    return not (b["side"] != side or b.get("mission") or K.get("direct") or K.get("air") or b.get("displacing") or b.get("rounds", 0) <= 0 or U.served_tubes(d, b) <= 0)


def _call_smoke(d: Data, us: list, side, field: dict | None, known: dict, free: list) -> list:
    """Smoke on an enemy shooting at its units: the nearest known enemy (the first of equals)
    whose missiles reach a unit of the side that cannot shoot back at it, at the first of its
    hexes the side can see and is not already smoked, by the free battery that reaches it and
    lands soonest (the first of equals). Not in the dark (sight shorter than light.flash) or
    when the wind blows smoke away at once (lasts 1). -> [the smoke order], or []."""
    S, wind = d.units["indirect"]["smoke"], (((field or {}).get("weather") or {}).get("wind") or "calm")
    L = U.light_of(d, field)
    if not free or S["lasts"].get(wind, 0) <= 1 or (L is not None and L.get("sight") is not None and L["sight"] < d.weather["light"]["flash"]):
        return []
    sm = (field or {}).get("smoke") or {}
    for _, j in _shooting_at(d, us, side, known):
        h = next((x for x in _marks(d, _where(us, j, known)) if U.spotted(d, us, field, side, x) and C.hkey(x) not in sm), None)
        if h is None:
            continue
        reach = [(d.units["indirect"]["kinds"][field["support"][k]["kind"]]["delay"], k) for k in free if U.in_reach(d, field["support"][k], h)]
        if reach:
            k = min(reach)[1]
            b = field["support"][k]
            b["mission"] = {"hex": list(h), "wait": d.units["indirect"]["kinds"][b["kind"]]["delay"], "repeat": False, "smoke": True}
            return [{"unit": None, "act": "smoke", "battery": k, "target": j, "hex": list(h)}]
    return []


def _shooting_at(d: Data, us: list, side, known: dict) -> list:
    """[(distance, enemy index)], nearest first: known enemies whose missiles reach a standing
    unit of the side that cannot shoot back at them (no missiles, or out of its range)."""
    out = set()
    for u in us:
        if u["side"] != side or u["state"] in ROUTED or u["men"] <= 0:
            continue
        for k, m in known.items():
            if not k.isdigit():
                continue
            e, dist = us[int(k)], U.hdist(m["pos"], u["pos"])
            hits = "range" in d.weapons[e["weapon"]] and U.field_range(d, e["weapon"], dist) is not None
            back = "range" in d.weapons[u["weapon"]] and U.field_range(d, u["weapon"], dist) is not None
            if hits and not back:
                out.add((dist, int(k)))
    return sorted(out)


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
        key = (-threat_score(d, _nearest(ours, e["pos"]), e, e), j)
        if best is None or key < best[0]:
            best = (key, (j, list(h)))
    return None if best is None else best[1]


def _nearest(ours: list, pos) -> dict:
    """The unit of ours whose middle hex is nearest pos (the first of equals)."""
    return min(ours, key=lambda o: U.hdist(o["pos"], pos))


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
    obj = objective(ctx[1])
    t = target(d, us, i, ctx[3], ctx[1])
    if u["state"] != "steady":
        return _unsteady(d, us, i, t)
    if u.get("reserve"):
        return None if t is None else _stay(d, us, i, t, u["facing"], "range" in d.weapons[u["weapon"]])
    if U.busy_digging(u):
        return None
    sap = _sapper_order(d, us, i, t, ctx)
    if sap is not None:
        return sap
    if t is None and obj is None:
        return None
    if obj is not None and _digs(d, us, i, ctx):
        return {"act": "dig", "target": t}
    if roll <= C["hesitate"].get(u["quality"], 0):
        return {"act": "hesitate", "target": t, "roll": roll}
    o = _best(d, us, i, t, ctx) if obj is None else _for_objective(d, us, i, t, ctx)
    return o if t is None else _last_seen(o, ctx[3], t, ctx[4])


def _unsteady(d: Data, us: list, i: int, t: int | None) -> dict | None:
    """A shaken unit holds, going to ground under missile fire."""
    return {"act": "ground", "target": t} if not us[i].get("prone") and under_fire(d, us, i) else None


def _digs(d: Data, us: list, i: int, ctx: tuple) -> bool:
    """A unit at the objective (within its radius) digs in: one that can (units.can_dig), not
    dug in where it stands, not under fire, and with no enemy it knows of in its range."""
    u, (_, field, _, known, _) = us[i], ctx
    if not U.can_dig(d, u) or U.dug_here(u) or U.off_objective(d, u, objective(field)) > U.objective_radii(d, field)[0]:
        return False
    if under_fire(d, us, i):
        return False
    seen = [m["pos"] for k, m in (known or {}).items() if k.isdigit()]
    return not any(U.field_range(d, u["weapon"], U.hdist(u["pos"], p)) is not None for p in seen)


def _sapper_order(d: Data, us: list, i: int, t: int | None, ctx: tuple) -> dict | None:
    """Sappers (units.can_sap) set to work: attacking, they lift the known mines (not their own
    side's) in the row ahead when the straight way to their target (where last seen) or the objective
    crosses known mines; holding, or at the objective, they lay mines there (_lays)."""
    u, field = us[i], ctx[1]
    if not U.can_sap(d, u):                       # (commanded units are out of contact)
        return None
    row = U.ahead_row(d, field, u)
    mines = (field or {}).get("mines") or {}
    if ctx[2] == "attack" and any(_foes_mine(mines.get(C.hkey(x)), u["side"]) for x in row):
        goal = _where(us, t, ctx[3])["pos"] if t is not None else objective(field)
        if goal is not None and _mined(field, u["pos"], goal, u["side"]):
            return {"act": "lift", "target": t}
    if _lays(d, us, i, ctx, row):
        return {"act": "lay", "target": t, "kind": _mine_kind(us, ctx[3])}
    return None


def _foes_mine(m: dict | None, side) -> bool:
    """A minefield hex it knows of that its own sappers did not lay (those do not strike it)."""
    return m is not None and U.known_mine(m) and m.get("side") != side


def _lays(d: Data, us: list, i: int, ctx: tuple, row: list) -> bool:
    """Holding (or at the objective, within its radius), no enemy it knows of
    within commander.sappers.clear_of hexes, and a hex of the row ahead free to mine."""
    u, (_, field, stance, known, _) = us[i], ctx
    obj = objective(field)
    if stance != "hold" and (obj is None or U.off_objective(d, u, obj) > U.objective_radii(d, field)[0]):
        return False
    near = d.units["commander"]["sappers"]["clear_of"]
    if any(U.hdist(u["pos"], m["pos"]) <= near for k, m in (known or {}).items() if k.isdigit()):
        return False
    mines, occ = (field or {}).get("mines") or {}, U.occupancy(d, us)
    return any(C.hkey(x) not in mines and C.hkey(x) not in occ for x in row)


def _mine_kind(us: list, known: dict | None) -> str:
    """Mixed if an enemy unit it knows of has vehicles, else anti-personnel."""
    return "mixed" if any(us[int(k)].get("vehicle") for k in (known or {}) if k.isdigit()) else "ap"


def objective(field: dict | None) -> list | None:
    """The hex the GM marked as the commander's objective (field objective), or None."""
    o = (field or {}).get("objective")
    return list(o) if o else None


def _for_objective(d: Data, us: list, i: int, t: int | None, ctx: tuple) -> dict | None:
    """With an objective (its radius, hold and guard: units.objective_radii). Attacking: a unit at it (within its radius) holds it
    (stays, charging only with a holder's odds); one with no enemy to go for, or one that would
    only stand or turn while its target is not guarding the objective, advances on it.
    Holding: a unit further than objective.hold from it falls back toward it unless it can
    charge; one with no enemy to go for and within that stays."""
    off = U.off_objective(d, us[i], objective(ctx[1]))
    if t is None:
        return _no_target(d, us, i, ctx, off)
    if ctx[2] == "attack":
        return _attack_objective(d, us, i, t, ctx, off)
    o = _best(d, us, i, t, ctx)
    if off > U.objective_radii(d, ctx[1])[1] and (o is None or o["act"] != "charge"):
        return _toward(d, us, i, t, ctx, "fall_back") or o
    return o


def _no_target(d: Data, us: list, i: int, ctx: tuple, off: int) -> dict | None:
    """With no enemy to go for: attacking, it advances on the objective unless at it; holding,
    it falls back toward it if further than objective.hold."""
    (radius, hold, _), attack = U.objective_radii(d, ctx[1]), ctx[2] == "attack"
    if off <= (radius if attack else hold):
        return None
    return _toward(d, us, i, None, ctx, "advance" if attack else "fall_back")


def _attack_objective(d: Data, us: list, i: int, t: int, ctx: tuple, off: int) -> dict | None:
    """Attacking with a target: at the objective it holds; else its best order, unless that
    is only to stand or turn while the target is not guarding the objective: then it advances."""
    if off <= U.objective_radii(d, ctx[1])[0]:
        return _best(d, us, i, t, (ctx[0], ctx[1], "hold", ctx[3], ctx[4]))
    o = _best(d, us, i, t, ctx)
    if (o is not None and o["act"] != "turn") or _guards(d, _where(us, t, ctx[3]), ctx[1]):
        return o
    return _toward(d, us, i, t, ctx, "advance") or o


def _toward(d: Data, us: list, i: int, t: int | None, ctx: tuple, act: str) -> dict | None:
    """A move (act advance or fall_back) toward the objective, within its allowance (its turn
    included) and touching no enemy, to the hex the commander likes best (_toward_hexes),
    facing the target if any, else the objective. None if it may only turn, or no such hex is
    nearer the objective."""
    (size, field, _, known, _), u = ctx, us[i]
    if _stuck(u):
        return None
    obj, tu = objective(field), None if t is None else _where(us, t, known)
    free = {**u, "prone": False} if u.get("prone") else u
    base = [free if k == i else x for k, x in enumerate(us)]
    foes = {k for k, j in U.occupancy(d, base).items() if base[j]["side"] != u["side"]}
    tries, allow = d.units["commander"]["tries"], U.allowance(d, free)
    for c, h in _toward_hexes(d, base, i, tu, (size, field)):
        f = _facing(h, tu, obj, u["facing"])
        if c + _turning(d, free, f) > allow or _touches(d, {**u, "pos": h, "facing": f}, foes):
            continue
        if tries == 0:
            return None
        tries -= 1
        m = _legal(d, base, i, (h, f, c, False), (size, field))
        if m["ok"]:
            return _rising(u, {"act": act, "target": t, "pos": h, "facing": f, "cost": m["cost"]})
    return None


def _stuck(u: dict) -> bool:
    """It may only turn: lost in the dark, with vehicles that cannot move, or emplaced."""
    return bool(u.get("lost") or u.get("immobile") or u.get("emplaced"))


def _rising(u: dict, o: dict) -> dict:
    """The order, marked as getting up first if the unit is on the ground."""
    return {**o, "up": True} if u.get("prone") else o


def _turning(d: Data, u: dict, f: int) -> int:
    """Movement unit u spends turning to facing f (without sweeping)."""
    return min((f - u["facing"]) % 6, (u["facing"] - f) % 6) * U.turn_cost(d, u)


def _toward_hexes(d: Data, base: list, i: int, tu: dict | None, where: tuple) -> list:
    """[(movement, hex)] the unit can reach within its allowance nearer the objective, best
    first: commander.closing a hex from the objective, a point a hex moved, known minefields
    on the way, less cover from the target (if any) by its quality."""
    (size, field), u, C = where, base[i], d.units["commander"]
    obj, q = objective(field), u["quality"]
    now, out = U.hdist(u["pos"], obj), []
    for h, c in reachable(d, base, i, size, U.allowance(d, u), field).items():
        if U.hdist(list(h), obj) >= now:
            continue
        cover = 0 if tu is None else C["cover"].get(q, 0) * U.cover_at(d, field, tu["pos"], list(h))
        out.append((C["closing"] * U.hdist(list(h), obj) + c + C["mines"].get(q, 0) * _mined(field, u["pos"], h, u["side"]) - cover, c, aside(h, obj), h[1], h[0]))
    return [(c, [col, row]) for _, c, _, row, col in sorted(out)]


def _facing(h: list, tu: dict | None, obj: list, facing: int) -> int:
    """Facing from h: toward the target if any, else the objective (as it was, at the objective)."""
    if tu is not None and list(tu["pos"]) != h:
        return U.bearing(h, tu["pos"])
    return facing if h == obj else U.bearing(h, obj)


def _last_seen(o: dict | None, known: dict | None, t: int, exchange) -> dict | None:
    """The order, with the exchange its target was last seen in ("last") if not this one."""
    last = (known or {}).get(str(t), {}).get("ex")
    return {**o, "last": last} if o and last is not None and last != (exchange or 0) else o


def target(d: Data, us: list, i: int, known: dict | None = None, field: dict | None = None) -> int | None:
    """The enemy unit it goes for among those its side knows of (known: sightings; None: every
    one standing), or None: the best by threat_score (the first of equals), with an objective
    on the field commander.objective.bonus more for one within its guard of it."""
    u = us[i]
    foes = [(-threat_score(d, u, us[j], _where(us, j, known)) - _guards(d, _where(us, j, known), field), j) for j, e in enumerate(us)
            if e["side"] != u["side"] and e["state"] not in ROUTED and e["men"] > 0 and (known is None or str(j) in known)]
    return min(foes)[1] if foes else None


def _guards(d: Data, seen: dict, field: dict | None) -> int:
    """commander.objective.bonus if the enemy (where it is known to be) is within the
    objective's guard (units.objective_radii) of it, else 0."""
    obj = objective(field)
    if obj is None or U.hdist(seen["pos"], obj) > U.objective_radii(d, field)[2]:
        return 0
    return d.units["commander"]["objective"]["bonus"]


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
    allow, tries, stuck = U.allowance(d, u), d.units["commander"]["tries"], bool(u.get("lost") or u.get("immobile") or u.get("emplaced"))
    reach = reachable(d, base, i, size, allow * (d.units["charge_move"] if charge else 1), field)
    foes = {k for k, j in U.occupancy(d, base).items() if base[j]["side"] != u["side"]}
    for _, c, _, row, col in sorted((-score(d, field, u, tu, h, c, shooter), c, aside(h, tu["pos"]), h[1], h[0]) for h, c in reach.items()):
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
    return any(C.hkey(U.step(h, dirn)) in foes for row in U.footprint(d, u) for h in row for dirn in range(6))


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


def aside(h, to) -> int:
    """How far hex h lies from hex `to` in a straight line (squared, in units where a hex's
    width is 2 and its rows 3 apart squared): among moves the commander likes equally, the
    one that keeps nearer the straight line wins, so a long advance does not drift sideways."""
    x, tx = 2 * h[0] + (h[1] & 1), 2 * to[0] + (to[1] & 1)
    return (x - tx) ** 2 + 3 * (h[1] - to[1]) ** 2


def score(d: Data, field: dict | None, u: dict, tu: dict, h: tuple, cost: int, shooter: bool) -> int:
    """How much the commander likes unit u ending at h (higher is better)."""
    C, q = d.units["commander"], u["quality"]
    dist = U.hdist(list(h), tu["pos"])
    s = C["cover"].get(q, 0) * U.cover_at(d, field, tu["pos"], list(h)) - cost - C["mines"].get(q, 0) * _mined(field, u["pos"], h, u["side"])
    if shooter:
        inr = dist >= 1 and U.field_range(d, u["weapon"], dist) is not None
        return s + (C["in_range"] if inr else -C["closing"] * dist) - (C["too_close"] if dist < C["keep_off"] else 0)
    flank = C["flank"].get(q, 0) if U.arc(tu["facing"], U.bearing(tu["pos"], list(h))) != "front" else 0
    return s - C["closing"] * dist + flank


def _mined(field: dict | None, a, h, side: int | None = None) -> int:
    """Hexes of minefields its side knows of (marked, found, or laid by its sappers) on the straight
    way from a to h, h included."""
    mines = (field or {}).get("mines") or {}
    if not mines or list(a) == list(h):
        return 0
    known = {k for k, m in mines.items() if U.known_mine(m, side)}
    return sum(1 for x in U.ray(list(a), list(h), U.hdist(a, h))[1:] if C.hkey(x) in known)


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
    elif o["act"] == "dig":
        us[i] = {**u, "digging": {"at": list(u["pos"]), "n": 0}}
    elif o["act"] == "lay":
        us[i] = {**u, "mining": {"at": list(u["pos"]), "facing": u["facing"], "n": 0, "kind": o["kind"]}}
    elif o["act"] == "lift":
        us[i] = {**u, "clearing": {"at": list(u["pos"]), "facing": u["facing"], "n": 0}}
    elif o["act"] == "turn":
        us[i] = {**u, "facing": o["facing"]}
    elif o["act"] in ("move", "charge", "advance", "fall_back"):
        us[i] = {**u, "pos": o["pos"], "facing": o["facing"], "charged": o["act"] == "charge", **({"prone": False} if o.get("up") else {})}
