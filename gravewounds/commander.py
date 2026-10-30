"""The scripted enemy commander of the field map: each of its side's moves, it orders that
side's units in turn, by their quality (units.yaml commander). Mirrored exactly by
templates/units.js (command)."""
from __future__ import annotations

import heapq
import math

from . import combat as C, units as U
from .model import Data

ROUTED = ("broken", "fled")
MOVES = ("move", "charge", "advance", "fall_back", "close_up", "spot", "search")   # orders that take a unit somewhere new


def command(d: Data, units: list, side, size: tuple, field: dict | None, rng, exchange=None, stance: str = "attack",
            memory: dict | None = None, table: str | None = None) -> tuple:
    """Orders for every unit of `side`, in turn (each sees the moves before it, and knows of
    the enemies a unit ordered before it sees from where it went). exchange: units
    that came on in it (arrived) wait. stance: attack (close with the enemy) or hold (stand,
    charging only what it can reach). memory: where it last saw each enemy unit, kept between
    its moves (updated in place; see sightings). -> (units after, orders [{unit, act, ...}]).
    Each step's movement is worked out once while it orders (units.steps_remembered)."""
    with U.steps_remembered():
        return _command(d, units, side, (size, field, rng, exchange), stance, memory, table)


def _mark_stance(d: Data, us: list, side, stance: str) -> None:
    """Its stance on each of its units, for morale.posture: only a holding side's units hold a position."""
    if d.units["morale"].get("posture"):
        for u in us:
            if u["side"] == side:
                u["holding"] = stance == "hold"


def _command(d: Data, units: list, side, where: tuple, stance: str, memory: dict | None, table: str | None) -> tuple:
    """command, worked out: where is (size, field, rng, exchange)."""
    size, field, rng, exchange = where
    us, orders = [dict(u) for u in units], []
    _mark_stance(d, us, side, stance)
    memory = {} if memory is None else memory
    known = sightings(d, us, side, field, exchange, memory)
    aim = aims(d, us, side, field, stance, memory)
    goal = aim[1]                                # the field with the objective most of its units go for (with a second one marked)
    us, orders = _hook_up(d, us, side, (goal, known, exchange, stance))
    us, orders = _riders(d, us, side, (goal, known, exchange, stance), orders)
    _hold_back(d, us, side, known)
    orders += _plan_if_needed(d, us, side, (field, known, exchange, stance, table), rng)
    orders += plan_steps(d, us, side, (field, known, exchange))
    orders += _commit(d, us, side, known, memory, stance)
    if stance == "hold":
        orders += _fix_lines(d, us, side, (field, known, exchange))
    for i in range(len(us)):
        if us[i]["side"] != side or not _free(d, us, i, exchange):
            continue
        if stance == "attack" and _leaves_disabled(d, us[i]):   # it goes on without its immobilised vehicles
            n = us[i]["immobile"]
            us[i] = U.abandon_immobile(d, us[i])
            orders.append({"unit": i, "act": "abandon", "n": n})
        o = _order_one(d, us, i, (size, field, stance, known, exchange), (aim, table), rng.randint(1, 100))
        if o:
            orders.append({"unit": i, **o})
            _apply(us, i, o)
            if o["act"] in MOVES:                 # what it sees from where it went, the units after it know
                sightings(d, us, side, field, exchange, known)
    us = _give_way(d, us, side, (size, field, stance, exchange), (aim, known), orders)
    orders += _move_guns(d, us, side, (size, goal, stance, known, exchange))
    orders += _lay_guns(d, us, side, (size, goal, known, exchange))
    return us, orders + _call_fire(d, us, side, goal, known, (stance, exchange, orders, table))


def aims(d: Data, us: list, side, field: dict | None, stance: str, memory: dict) -> tuple:
    """(the field as its garrison of the first objective sees it, as the rest see it, the
    garrison's indices): with a second objective (objective2) marked, attacking, once its side
    holds the first, the rest go for the second while the units that stood on the first when it
    moved on (its garrison, kept in memory plan) stay; holding, once the enemy holds the first,
    all fall back to the second. Else (field, field, []). An attacker that no longer holds the
    first goes back for it, and picks a new garrison when it moves on again."""
    if not (field or {}).get("objective") or not field.get("objective2"):
        return field, field, []
    held, second, plan = U.objective_held(d, us, field)[0]["held"], U.second_view(field), memory.setdefault("plan", {})
    if stance != "attack":
        return (second, second, []) if held is not None and held != side else (field, field, [])
    if held != side:
        plan.pop("garrison", None)
        return field, field, []
    at, g = [list(field["objective"]), list(field["objective2"])], plan.get("garrison")
    if not g or g["at"] != at:
        r = U.objective_radii(d, field)[0]
        g = plan["garrison"] = {"at": at, "units": [u.get("id", k) for k, u in enumerate(us) if u["side"] == side and u["men"] > 0 and u["state"] not in ROUTED
                                                    and U.off_objective(d, u, field["objective"]) <= r]}
    return field, second, g["units"]


def _aim(us: list, i: int, aim: tuple) -> dict | None:
    """The field (objective) unit i goes for: the first's view if it is in the garrison (by id,
    else index), else the rest's (see aims)."""
    return aim[0] if us[i].get("id", i) in aim[2] else aim[1]


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
    of (else any), up to commander.reserve % of the side's men by the quality most of them have
    (not a unit the battlefield sends on a route, via, nor a vehicle with a main gun: self-play held
    Hue's tanks and Ontos back, then sent them to plug gaps in the blocks, where vehicles cannot go). Every unit of the side gets `reserve` (True or False), so it is done once."""
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
        if (U.is_battery(d, us[i]) or U.is_at_gun(d, us[i]) or _tractor(d, us[i]) or us[i].get("via")
                or (U.vehicle_kind(d, us[i]) or {}).get("gun") or us[i]["men"] > room):   # vehicles with a main gun go in with the attack
            continue
        us[i]["reserve"] = True
        room -= us[i]["men"]


def _formed(d: Data, u: dict) -> bool:
    """Close-order men who fight hand to hand (no missile weapon, not open order, not vehicles)."""
    return "range" not in d.weapons[u["weapon"]] and u.get("formation") != "open" and not u.get("vehicle")


def _screening(d: Data, u: dict, side) -> bool:
    """A steady open-order unit of the side with a missile weapon (not vehicles, batteries or anti-tank guns)."""
    return (u["side"] == side and u["state"] == "steady" and u["men"] > 0 and u.get("formation") == "open" and "range" in d.weapons[u["weapon"]]
            and not u.get("vehicle") and not U.is_battery(d, u) and not U.is_at_gun(d, u))


def _give_way(d: Data, us: list, side, where: tuple, ak: tuple, orders: list) -> list:
    """Attacking, after its units' orders: a formed unit that did not move or hesitate (not a
    reserve, not on a route), held up behind its own open-order shooters, has them step aside
    and is ordered again (_clear_way). where: (size, field, stance, exchange). Appends to
    orders; -> the units after."""
    if where[2] != "attack":
        return us
    done = {o["unit"] for o in orders if o["act"] in MOVES or o["act"] == "hesitate"}
    held = {o["unit"] for o in orders if o["act"] == "hesitate"}
    for i in range(len(us)):
        f = us[i]
        if f["side"] != side or i in done or f.get("via") or f.get("reserve") or f["state"] != "steady" or not _formed(d, f) or not _free(d, us, i, where[3]):
            continue
        orders += _clear_way(d, us, i, (where, ak, held))
    return us


def _clear_way(d: Data, us: list, i: int, ctx: tuple) -> list:
    """Formed unit i's own open-order shooters within commander.give_way hexes that are nearer
    its target than it is (not those that hesitated): if it would move nearer its target with
    them gone, those standing on the ground it would cross (its footprint at each hex of the
    straight way) step aside (_step_aside), and it is ordered again. -> the orders (the units
    changed in place)."""
    (size, field, _stance, exchange), (aim, known), held = ctx
    f = us[i]
    t = target(d, us, i, known, field)
    if t is None:
        return []
    tp = _where(us, t, known)["pos"]
    d0 = U.hdist(f["pos"], tp)
    screen = [k for k in range(len(us)) if k != i and k not in held and _screening(d, us[k], f["side"])
              and U.hdist(us[k]["pos"], f["pos"]) <= d.units["commander"]["give_way"] and U.hdist(us[k]["pos"], tp) < d0]
    if not screen:
        return []
    octx = (size, _plugging(_aim(us, i, aim), f), "attack", known, exchange)
    want = _order(d, [{**u, "pos": [-1000, -1000]} if k in screen else u for k, u in enumerate(us)], i, octx, 100)
    if not want or want["act"] not in MOVES or U.hdist(want["pos"], tp) >= d0:
        return []
    lane = {tuple(h) for x in U.ray(f["pos"], want["pos"], U.hdist(f["pos"], want["pos"]))
            for row in U.footprint(d, {**f, "pos": list(x), "facing": want["facing"]}) for h in row}
    out = []
    for k in screen:
        o = _step_aside(d, us, k, lane, (size, field, known)) if any(tuple(h) in lane for row in U.footprint(d, us[k]) for h in row) else None
        if o:
            out.append({"unit": k, **o})
            _apply(us, k, o)
    o = _order(d, us, i, octx, 100)
    if o and o["act"] in MOVES:
        out.append({"unit": i, **o, "through_screen": True})
        _apply(us, i, o)
    return out


def _step_aside(d: Data, us: list, k: int, lane: set, where: tuple) -> dict | None:
    """The best spot shooter k can reach (by score against its target, else least movement;
    then lowest row, then column) clear of the lane, facing as it is: a move order with why
    give_way, or None."""
    size, field, known = where
    s = us[k]
    t = target(d, us, k, known, field)
    tu = None if t is None else _where(us, t, known)
    best = None
    for h, cost in reachable(d, us, k, size, U.allowance(d, s), field).items():
        at = {**s, "pos": list(h)}
        if any(tuple(x) in lane for row in U.footprint(d, at) for x in row) or not U._fits(d, us, k, at, size, field):
            continue
        sc = score(d, field, s, tu, h, cost, True) if tu else -cost
        if best is None or sc > best[0] or (sc == best[0] and (h[1], h[0]) < (best[1][1], best[1][0])):
            best = (sc, list(h), cost)
    return {"act": "move", "pos": best[1], "facing": s["facing"], "cost": best[2], "why": "give_way"} if best else None


def _stalled(d: Data, us: list, side, known: dict, plan: dict) -> bool:
    """Attacking: True once commander.stall.moves of its moves in a row have neither put down
    commander.stall.down % of the enemy's starting men nor brought one of its units (not a
    reserve) nearer an enemy it knows of (the mark kept in plan, reset then)."""
    S = d.units["commander"]["stall"]
    foes = [u for u in us if u["side"] != side]
    down, start = sum(u.get("down", 0) for u in foes), sum(u.get("start") or u["men"] for u in foes)
    kf = [m for k, m in known.items() if k.isdigit()]
    mine = [u for u in us if u["side"] == side and not u.get("reserve") and u["men"] > 0 and u["state"] not in ROUTED]
    near = min((U.hdist(u["pos"], m["pos"]) for u in mine for m in kf), default=None) if kf and mine else None
    mark = plan.get("mark")
    if not mark or down - mark["down"] >= start * S["down"] / 100 or (near is not None and (mark["near"] is None or near < mark["near"])):
        plan["mark"] = {"down": down, "near": near, "quiet": 0}
        return False
    mark["quiet"] += 1
    if mark["quiet"] < S["moves"]:
        return False
    plan["mark"] = {"down": down, "near": near, "quiet": 0}
    return True


def _commit(d: Data, us: list, side, known: dict, memory: dict, stance: str = "attack") -> list:
    """Commit one reserve unit this move, the one nearest an enemy it knows of, when a unit of
    the side has broken or fled since its last move, when a known enemy is within
    commander.gap hexes of a reserve unit, (a veteran reserve unit) when an enemy unit has
    broken, or (attacking) when the attack has stalled (_stalled). Committed because a unit
    broke, it is the reserve unit nearest where that unit stood at its side's last move
    (_gap_left), and it goes to plug the gap there (plug). -> [the commit order], or []."""
    plan = memory.setdefault("plan", {})
    stall = stance == "attack" and _stalled(d, us, side, known, plan)
    own = sum(1 for u in us if u["side"] == side and u["state"] in ROUTED)
    foe = sum(1 for u in us if u["side"] != side and u["state"] in ROUTED)
    broke, foe_broke = own > plan.get("own", own), foe > plan.get("foe", foe)
    plan.update(own=own, foe=foe)
    hole = _gap_left(us, side, plan)
    held = [i for i, u in enumerate(us) if u["side"] == side and u.get("reserve") and u["men"] > 0 and u["state"] not in ROUTED]
    if not held:
        return []
    if broke and hole is not None:
        pick = min(held, key=lambda i: (U.hdist(us[i]["pos"], hole), i))
        us[pick]["reserve"], us[pick]["plug"] = False, list(hole)
        return [{"unit": pick, "act": "commit", "why": "broke", "at": list(hole)}]
    near = {i: min((U.hdist(us[i]["pos"], m["pos"]) for k, m in known.items() if k.isdigit()), default=10**6) for i in held}
    gap = [i for i in held if near[i] <= d.units["commander"]["gap"]]
    if broke or gap:
        pick, why = min(held, key=lambda i: (near[i], i)), "broke" if broke else "gap"
    elif foe_broke and any(us[i]["quality"] == "veteran" for i in held):
        pick, why = min((i for i in held if us[i]["quality"] == "veteran"), key=lambda i: (near[i], i)), "exploit"
    elif stall:
        pick, why = min(held, key=lambda i: (near[i], i)), "stall"
    else:
        return []
    us[pick]["reserve"] = False
    return [{"unit": pick, "act": "commit", "why": why}]


def _fix_lines(d: Data, us: list, side, ctx: tuple) -> list:
    """Holding, by day or at dusk (a line cannot be laid in the dark), each of its machine guns
    on foot, steady and with men (_fix_order): with no fixed line, laid on the nearest enemy it
    knows of within its reach, else ahead toward the nearest enemy it knows of (or along its
    facing); a line laid ahead is shifted once onto an enemy that comes into its reach off it.
    -> [fix orders]."""
    field, known, exchange = ctx
    light = U.light_of(d, field)
    if light is not None and ((field or {}).get("weather") or {}).get("light") != "dusk":
        return []
    out = []
    for i, u in enumerate(us):
        if u["side"] != side or u.get("vehicle") or not U.is_mg(d, u["weapon"]) or u["state"] != "steady" or u["men"] <= 0:
            continue
        if (exchange is not None and u.get("arrived") == exchange) or (u.get("fixed") and not u.get("fix_ahead")):
            continue
        o = _fix_order(d, us, i, field, known)
        if o is not None:
            us[i] = {k: v for k, v in u.items() if k != "fix_ahead"} | {"fixed": o["hex"], **({"fix_ahead": True} if o.get("ahead") else {})}
            out.append({"unit": i, **o})
    return out


def _fix_order(d: Data, us: list, i: int, field: dict | None, known: dict) -> dict | None:
    """Machine gun i's fixed line: on the nearest enemy it knows of within its reach (the lowest
    index of equals); with none, and no line yet, ahead (_line_ahead); a line laid ahead is
    shifted onto such an enemy only if it stands off the line (relay). None: no change."""
    u = us[i]
    foes = sorted((U.hdist(u["pos"], m["pos"]), int(k)) for k, m in known.items() if k.isdigit())
    near = [(dist, j) for dist, j in foes if dist > 0 and U.field_range(d, u["weapon"], dist) is not None]
    if near:
        j = near[0][1]
        at = list(known[str(j)]["pos"])
        if u.get("fixed") and _on_line(d, u, at):
            return None
        return {"act": "fix", "target": j, "hex": at, **({"relay": True} if u.get("fixed") else {})}
    if u.get("fixed"):
        return None
    toward = known[str(foes[0][1])]["pos"] if foes else None
    at = _line_ahead(d, u, field, toward)
    return None if at is None else {"act": "fix", "target": foes[0][1] if foes else None, "hex": at, "ahead": True}


def _on_line(d: Data, u: dict, h) -> bool:
    """Whether hex h lies within light.fixed_line.width of machine gun u's fixed line."""
    front = U.footprint(d, u)[0]
    g = front[len(front) // 2]
    n = U.hdist(g, u["fixed"])
    w = d.weather["light"]["fixed_line"]["width"]
    return n > 0 and any(U.hdist(x, h) <= w for x in U.ray(g, u["fixed"], n)[1:])


def _line_ahead(d: Data, u: dict, field: dict | None, toward) -> list | None:
    """The hex a machine gun lays a line ahead on: along the line from the middle of its front
    toward `toward` (an enemy it knows of, out of its reach), else along its facing, the
    furthest hex before the first it cannot reach or see (or the map's edge). None if not one."""
    front = U.footprint(d, u)[0]
    g, reach = front[len(front) // 2], max((n for n in range(1, 400) if U.field_range(d, u["weapon"], n) is not None), default=0)
    far = list(toward) if toward is not None else g
    for k in range(0 if toward is not None else 2 * reach):
        far = U.step(far, u["facing"] + k % 2)
    size, best = (field or {}).get("size") or [10**6, 10**6], None
    for x in U.ray(g, far, U.hdist(g, far))[1:]:
        on = 0 <= x[0] < size[0] and 0 <= x[1] < size[1]
        if not on or U.field_range(d, u["weapon"], U.hdist(u["pos"], x)) is None or not U._sees(d, field, u, x, U._sight_hexes(d, field, x, U._seer(u))):
            break
        best = list(x)
    return best


def _gap_left(us: list, side, plan: dict) -> list | None:
    """Where the first of its units (by id, else index) that has broken or fled since its last
    move stood then (plan stood), or None; then plan stood is where its standing units are now."""
    was = plan.get("stood") or {}
    hole = next((was[str(u.get("id", k))] for k, u in enumerate(us)
                 if u["side"] == side and u["state"] in ROUTED and str(u.get("id", k)) in was), None)
    plan["stood"] = {str(u.get("id", k)): list(u["pos"]) for k, u in enumerate(us) if u["side"] == side and u["state"] not in ROUTED and u["men"] > 0}
    return hole


def _plugging(field: dict | None, u: dict) -> dict | None:
    """The field as a reserve unit sent to plug a gap (plug) sees it: that hex its objective, at
    the commander's own radius; else the field."""
    return {**(field or {}), "objective": list(u["plug"]), "objective_radius": None} if u.get("plug") else field


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
# unhooked where they are. Attacking or holding, guns a known enemy could reach at a charge
# (with no steady friend on the line between) limber or hook up and pull back (threat,
# _pull_back).

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
    """At the start of its move, anti-tank guns on the map (not emplaced) hook up to the first
    empty tractor of their side beside them that can tow them (units.mount): attacking, with no
    known enemy in reach and somewhere to go; in either stance, under threat (threat), to be
    pulled back. The guns leave the list, so the enemy indices
    it remembers are moved down. -> (units, [hook orders])."""
    field, known, exchange, stance = ctx
    out, i = [], 0
    while i < len(us):
        u = us[i]
        if not U.is_at_gun(d, u) or u.get("emplaced") or not _gun_ready(d, us, i, side, exchange):
            i += 1
            continue
        _, goal, inr = _gun_goal(d, us, u, field, known)
        wants = (stance == "attack" and not inr and goal is not None) or threat(d, us, i, known) is not None
        j = next((k for k, c in enumerate(us) if k != i and U._cannot_mount(d, us, i, k) is None), None) if wants else None
        if j is None:
            i += 1
            continue
        us = U.mount(d, us, i, j)["units"]
        _drop_index(known, i)
        out = [{**o, "unit": o["unit"] - (o["unit"] > i)} for o in out]
        out.append({"unit": j - (j > i), "act": "hook", "guns": u.get("name")})
    return us, out


def _riders(d: Data, us: list, side, ctx: tuple, orders: list) -> tuple:
    """At the start of its move: its carriers' riders get down (_get_down); then, attacking, its
    foot units get aboard empty carriers beside them (_carrier_for). -> (units, orders)."""
    _, known, _, stance = ctx
    for j in range(len(us)):
        o = _get_down(d, us, j, side, ctx)
        if o:
            orders.append(o)
    if stance != "attack":
        return us, orders
    i = 0
    while i < len(us):
        j = _carrier_for(d, us, i, side, ctx)
        if j is None:
            i += 1
            continue
        name = us[i].get("name")
        us = U.mount(d, us, i, j)["units"]
        _drop_index(known, i)
        orders = [{**o, "unit": o["unit"] - (o["unit"] > i)} if isinstance(o.get("unit"), int) else o for o in orders]
        orders.append({"unit": j - (j > i), "act": "mount", "riders": name})
    return us, orders


def _in_reach(d: Data, weapons: list, dist: int) -> bool:
    """Any of these weapons (that shoot) reaches dist field hexes."""
    return any("range" in d.weapons[w] and U.field_range(d, w, dist) is not None for w in weapons)


def _enemy_in_reach(d: Data, at, weapons: list, known: dict) -> bool:
    """An enemy it knows of (where last seen) within reach of any of these weapons from hex at."""
    return any(_in_reach(d, weapons, U.hdist(at, m["pos"])) for k, m in known.items() if k.isdigit())


def _get_down(d: Data, us: list, j: int, side, ctx: tuple) -> dict | None:
    """Carrier j of the side with men aboard (not towed guns), out of contact and not broken,
    sets them down beside it (units.dismount; they move from the next exchange) once an enemy
    it knows of is within reach of their weapon or its own, or it stands at the objective.
    -> a dismount order, or None."""
    field, known, exchange, _ = ctx
    c, R = us[j], us[j].get("riders")
    if c["side"] != side or not c.get("vehicle") or not R or R.get("men", 0) <= 0 or U.is_at_gun(d, R) or c["state"] in ROUTED:
        return None
    obj = objective(field)
    at_obj = obj is not None and U.off_objective(d, c, obj) <= U.objective_radii(d, field)[0]
    if not at_obj and not _enemy_in_reach(d, c["pos"], [R["weapon"], c["weapon"]], known):
        return None
    r = U.dismount(d, us, j, U._size(d, field), field)
    if not r["ok"]:
        return None
    us[:] = r["units"][:-1] + [{**r["units"][-1], "arrived": exchange}]
    return {"unit": j, "act": "dismount", "riders": R.get("name")}


def _carrier_for(d: Data, us: list, i: int, side, ctx: tuple) -> int | None:
    """The first empty carrier of the side beside foot unit i that it can get aboard (units.mount;
    not gun tractors), if i is attacking, free, not in reserve or at the objective, and no enemy
    it knows of is within reach of its weapon or the carrier's (from where either stands). Else None."""
    field, known, exchange, _ = ctx
    u = us[i]
    if u["side"] != side or u.get("vehicle") or u.get("reserve") or not _free(d, us, i, exchange) or u["state"] != "steady":
        return None
    if u.get("digging") or u.get("mining") or u.get("clearing") or u.get("prone"):
        return None
    obj = objective(field)
    if obj is not None and U.off_objective(d, u, obj) <= U.objective_radii(d, field)[0]:
        return None
    for j, c in enumerate(us):
        if j == i or not c.get("vehicle") or _tractor(d, c) or c.get("immobile", 0) >= U.vehicles_left(d, c) or U._cannot_mount(d, us, i, j) is not None:
            continue
        if not any(_enemy_in_reach(d, at, [u["weapon"], c["weapon"]], known) for at in (u["pos"], c["pos"])):
            return j
    return None


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
    (_gun_order), or under threat limber and pull back (_pull_back); attacking, its empty
    tractors go to fetch guns (_fetch). -> [orders]."""
    size, field, stance, _, exchange = ctx
    out, claimed = [], set()
    for i in range(len(us)):
        u = us[i]
        if stance == "attack" and _tractor(d, u) and not u.get("riders") and _gun_ready(d, us, i, side, exchange):
            o = _fetch(d, us, i, ctx, claimed)
        elif not (U.is_battery(d, u) or (_tractor(d, u) and gun_reach(d, u))) or not _gun_ready(d, us, i, side, exchange):
            continue
        else:
            j = threat(d, us, i, ctx[3])
            o = _gun_order(d, us, i, ctx) if j is None else _pull_back(d, us, i, j, ctx)
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


def threat(d: Data, us: list, i: int, known: dict) -> int | None:
    """The enemy it knows of (where last seen; the nearest, then the lowest index) that could
    charge gun unit i this move, with no steady friendly unit on the straight line between: a
    unit not running within its allowance times charge_move. None if there is none."""
    u = us[i]
    foes = sorted((U.hdist(u["pos"], m["pos"]), int(k)) for k, m in known.items() if k.isdigit())
    for dist, j in foes:
        e = us[j]
        if e["state"] in ("broken", "fled") or e["men"] <= 0 or dist > U.allowance(d, e) * d.units["charge_move"]:
            continue
        if not _screened(d, us, i, _where(us, j, known)["pos"]):
            return j
    return None


def _screened(d: Data, us: list, i: int, a) -> bool:
    """A steady friendly unit of gun unit i (not guns or vehicles) has a hex on the straight
    line between hex a and the guns."""
    u = us[i]
    line = {C.hkey(x) for x in U.ray(list(a), list(u["pos"]), U.hdist(a, u["pos"]))[1:-1]}
    return any(k != i and x["side"] == u["side"] and x["state"] == "steady" and not U.is_battery(d, x) and not U.is_at_gun(d, x)
               and not x.get("vehicle") and any(C.hkey(h) in line for row in U.footprint(d, x) for h in row) for k, x in enumerate(us))


def _pull_back(d: Data, us: list, i: int, j: int, ctx: tuple) -> dict | None:
    """Gun unit i under threat from enemy j: a battery in action limbers; one limbered (or a
    tractor towing guns) goes to the hex in its allowance furthest from the enemy (where last
    seen), keeping its facing and touching no enemy (then the cheapest, then the lowest row and
    column). None if it can get no further away."""
    size, field, _, known, _ = ctx
    u = us[i]
    if U.is_battery(d, u) and not u.get("limbered"):
        return {"act": "limber", "target": j, "back": True}
    foe = _where(us, j, known)["pos"]
    foes = {k for k, x in U.occupancy(d, us).items() if us[x]["side"] != u["side"]}
    here = U.hdist(u["pos"], foe)
    cands = sorted((-U.hdist(list(h), foe), c, h[1], h[0]) for h, c in reachable(d, us, i, size, U.allowance(d, u), field).items())
    tries = d.units["commander"]["tries"]
    for far, c, row, col in cands:
        h = [col, row]
        if -far <= here:
            return None
        if _touches(d, {**u, "pos": h}, foes):
            continue
        if tries == 0:
            return None
        tries -= 1
        m = _legal(d, us, i, (h, u["facing"], c, False), (size, field))
        if m["ok"]:
            return {"act": "pull_back", "target": j, "pos": h, "facing": u["facing"], "cost": m["cost"]}
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


def _call_fire(d: Data, us: list, side, field: dict | None, known: dict, how: tuple = ("attack", None, (), None)) -> list:
    """First its batteries under counter-battery fire displace (_displace). In the dark, one
    battery lights an enemy it has lost sight of (_call_illum).
    Attacking, one battery lays smoke where its units are under fire (_call_smoke).
    Then one battery fires counter-battery on a located enemy battery (_call_counter), and,
    attacking, one puts a creeping barrage ahead of a unit closing on the enemy (_call_creep). Then each
    of its other off-map batteries (not tanks) with no mission, rounds and tubes, not
    displacing, and its aircraft that can fly (_free_air), is called on the enemy unit it sees now that scores best as a
    target for the side's unit nearest it (threat_score), at the first of its hexes the side
    can see, in the battery's reach, with none of the side's men within the kind's radius and
    scatter; aircraft fly a strafing run or napalm strip on a wide enemy front (_air_run)."""
    stance, exchange, orders, table = how
    out = _displace(d, field, side)
    free = [k for k, b in enumerate((field or {}).get("support") or []) if _free_battery(d, b, side)]
    out += _call_illum(d, us, side, field, (known, exchange), free)
    out += _call_smoke(d, us, side, field, known, free) if stance == "attack" else []
    out += _call_counter(d, field, side, free)
    out += _call_creep(d, us, side, field, (known, orders), free) if stance == "attack" else []
    air = [k for k, b in enumerate((field or {}).get("support") or []) if _free_air(d, field, b, side)]
    return out + _call_plain(d, us, side, field, (known, sorted(free + air), table, stance == "attack"))


def _call_plain(d: Data, us: list, side, field: dict | None, kt: tuple) -> list:
    """Each of the given batteries and aircraft still without a mission is called on the enemy
    it sees that scores best as a target (_fire_aim); aircraft fly a run on a wide front
    (_air_run). -> [fire orders]."""
    known, ks, table, attacking = kt
    out = []
    for k in ks:
        b = field["support"][k]
        K = d.units["indirect"]["kinds"][b["kind"]]
        aim = None if b.get("mission") else _fire_aim(d, us, side, field, known, (b, K), attacking)
        if aim:
            out.append(_plain_order(d, us, side, (k, b, K), (aim, table, field)))
    return out


def _plain_order(d: Data, us: list, side, bk: tuple, atf: tuple) -> dict:
    """Battery or aircraft k (b, kind K) is called on aim: its mission set (aircraft: a run on
    a wide front, _air_run). -> the fire order, noting a controller who sees the aim."""
    (k, b, K), (aim, table, field) = bk, atf
    run = _air_run(d, us, side, (b, K), aim, (table, field)) if K.get("air") else None
    b["mission"] = {"hex": aim[1], "wait": K["delay"], "repeat": False, **({"planned": True} if aim[2] else {}), **(run or {})}
    talked = {"fac": True} if K.get("air") and U._fac_sees(d, us, field, b, aim[1]) else {}
    return {"unit": None, "act": "fire", "battery": k, "target": aim[0], "hex": aim[1], **({"attack": run["attack"]} if run else {}), **talked}


def _call_creep(d: Data, us: list, side, field: dict | None, ko: tuple, free: list) -> list:
    """Attacking: of its units ordered this move to move or charge on a known enemy it can see
    within commander.creep.near hexes, the nearest (the first of equals) gets a creeping
    barrage on that enemy, at the first of its hexes the side can see, from the free battery
    (not aircraft) that reaches it and lands soonest with none of its men within the burst and
    scatter; it lifts step hexes every `every` exchanges along the unit's facing for `lines`
    lines. Not while one of its batteries is already creeping. -> [the order], or []."""
    known, orders = ko
    sup, CR = (field or {}).get("support") or [], d.units["commander"]["creep"]
    if any(b["side"] == side and (b.get("mission") or {}).get("creep") for b in sup):
        return []
    ours = [u for u in us if u["side"] == side and u["men"] > 0 and u["state"] != "fled"]
    pairs = sorted((U.hdist(us[o["unit"]]["pos"], _where(us, o["target"], known)["pos"]), o["unit"], o["target"]) for o in orders
                   if o.get("act") in ("move", "charge") and o.get("target") is not None and str(o["target"]) in known)
    for dist, i, t in pairs:
        h = next((x for x in _marks(d, us[t]) if U.spotted(d, us, field, side, x)), None) if dist <= CR["near"] else None
        if h is None:
            continue
        guns = sorted((d.units["indirect"]["kinds"][sup[k]["kind"]]["delay"], k) for k in free if not sup[k].get("mission")
                      and U.in_reach(d, sup[k], h)
                      and not _too_near(d, ours, h, d.units["indirect"]["kinds"][sup[k]["kind"]]["radius"] + d.units["indirect"]["kinds"][sup[k]["kind"]]["scatter"]))
        if guns:
            k = guns[0][1]
            sup[k]["mission"] = {"hex": list(h), "wait": guns[0][0], "repeat": True,
                                 "creep": {"step": CR["step"], "dir": us[i]["facing"], "every": CR["every"], "lines": CR["lines"]}}
            return [{"unit": None, "act": "creep", "battery": k, "target": t, "hex": list(h), "for": i}]
    return []


def _air_run(d: Data, us: list, side, bk: tuple, aim: tuple, tf: tuple) -> dict | None:
    """A strafing run or napalm strip for aircraft b (kind K) on enemy aim[0] at aim[1]: napalm
    if the aircraft carry it and the war allows it (table's battle) and the battlefield's year is
    not before its `from`, else strafing, when the
    target's front is at least the run's length; along its front; only if none of the side's
    men are within the scatter (_air_scatter: cut where a controller sees the aim) of a hex of
    the line. -> {attack, dir}, or None (a plain attack)."""
    (b, K), (j, h, *_), (table, field) = bk, aim, tf
    R = d.units["indirect"]["air"].get("runs") or {}
    rows = U.footprint(d, us[j])
    front = len(rows[0]) if rows else 0
    war = (d.tables.get(table) or {}).get("battle") if table else None
    ours = [u for u in us if u["side"] == side and u["men"] > 0 and u["state"] != "fled"]
    dirn = (us[j]["facing"] + 5) % 6
    for mode in ("napalm", "strafe"):
        r = R.get(mode)
        if not r or b["kind"] not in r["kinds"] or front < r["length"] or ("wars" in r and war not in r["wars"]) or _too_early(r, field):
            continue
        if not any(_too_near(d, ours, x, _air_scatter(d, us, field, (b, K), h)) for x in U.run_line(d, h, dirn, mode)):
            return {"attack": mode, "dir": dirn}
    return None


def _too_early(r: dict, field: dict | None) -> bool:
    """An attack run (napalm) not yet used in the battlefield's year (`from`); open ground with no
    year is never too early."""
    year = (field or {}).get("year")
    return bool(r.get("from") and year and year < r["from"])


def _displace(d: Data, field: dict | None, side) -> list:
    """Each of its located batteries that an enemy counter-battery mission is aimed at, not
    displacing already, with tubes and a kind that can move (displace > 0), displaces: its
    mission ends and it is silent for its kind's exchanges, then no longer located; a placed
    battery moves along its map edge (shifted). -> [displace orders]."""
    sup, out = (field or {}).get("support") or [], []
    for k, b in enumerate(sup):
        n = _displace_for(d, b, side)
        if not n:
            continue
        by = next((j for j, x in enumerate(sup) if x["side"] != side and (x.get("mission") or {}).get("battery") == k), None)
        if by is not None:
            b.update(displacing=n, mission=None)
            if b.get("place") is not None:
                b["to"] = shifted(d, field, b["place"], sup[by].get("place"))
            out.append({"unit": None, "act": "displace", "battery": k, "by": by, **({"to": b["to"]} if b.get("to") else {})})
    return out


def _displace_for(d: Data, b: dict, side) -> int:
    """The exchanges battery b of this side would be silent displacing, or 0 if it does not
    displace (not located, displacing already, no tubes, or a kind that cannot move)."""
    if b["side"] != side or not b.get("located") or b.get("displacing") or b.get("tubes", 0) <= 0:
        return 0
    return d.units["indirect"]["kinds"][b["kind"]].get("displace", 0)


def shifted(d: Data, field: dict, place, away) -> list:
    """Where a placed battery displaces to: indirect.displace_shift hexes along the map edge
    nearest its place (the first of equals: west, east, top, bottom), away from the enemy
    battery firing on it (if that one is placed), else toward the side with more room; the
    other way if it is at the end of the edge."""
    cols, rows = U._size(d, field)
    gaps = [place[0], cols - 1 - place[0], place[1], rows - 1 - place[1]]
    axis = 1 if gaps.index(min(gaps)) < 2 else 0          # along a west or east edge, rows change; else columns
    n, at, step = (cols, rows)[axis], place[axis], d.units["indirect"]["displace_shift"]
    if away is not None and away[axis] != at:
        way = -1 if away[axis] > at else 1
    else:
        way = 1 if at <= (n - 1) / 2 else -1
    new = min(n - 1, max(0, at + way * step))
    if new == at:
        new = min(n - 1, max(0, at - way * step))
    out = list(place)
    out[axis] = new
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


def _fire_aim(d: Data, us: list, side, field: dict | None, known: dict, bk: tuple, attacking: bool = False) -> tuple | None:
    """(enemy index, hex, planned) for battery b (kind K) to fire on, or None (_call_fire): none of
    its men within the burst and scatter (_air_scatter, and indirect.planned.scatter more for
    planned fire); for aircraft, an aim a controller of its side sees first, then the best-scoring.
    Attacking, a battery (not aircraft or tanks) may fire on an enemy standing near a place its side
    held when the battle began (_near_located), seen or not: planned fire."""
    b, K = bk
    P = d.units["indirect"].get("planned") or {}
    plan = _battery_plan(P, bk, attacking)
    best = None
    ours = [u for u in us if u["side"] == side and u["men"] > 0 and u["state"] != "fled"]
    if not ours:
        return None
    for j, e in enumerate(us):
        if e["side"] == side:
            continue
        h, planned = _aim_at(d, us, (side, field, known), (j, e), plan)
        if h is None or not _clear_shot(d, (us, ours, field), bk, h, P.get("scatter", 0) * planned):
            continue
        talked = bool(K.get("air")) and U._fac_sees(d, us, field, b, h)
        key = (not talked, -threat_score(d, _nearest(ours, e["pos"]), e, e), j)
        if best is None or key < best[0]:
            best = (key, (j, list(h), planned))
    return None if best is None else best[1]


def _battery_plan(planned: dict, bk: tuple, attacking: bool):
    """The battery's planned fire: "attack" (on the defenders' start positions), "hold" (its own
    defensive fire plan, a battery marked df), or None."""
    b, kind = bk
    if not _plans(planned, kind):
        return None
    if attacking:
        return "attack"
    return "hold" if b.get("df") else None


def _plans(planned: dict, kind: dict) -> bool:
    """Planned fire is on (indirect.planned) and the kind fires it: guns and mortars, not aircraft or tanks."""
    return bool(planned) and not kind.get("air") and not kind.get("direct")


def _clear_shot(d: Data, uof: tuple, bk: tuple, h, extra: int) -> bool:
    """Battery b reaches hex h, with none of the side's men within the burst and scatter (and extra)."""
    us, ours, field = uof
    b, K = bk
    return U.in_reach(d, b, h) and not _too_near(d, ours, h, K["radius"] + _air_scatter(d, us, field, bk, h) + extra)


def _aim_at(d: Data, us: list, sfk: tuple, je: tuple, plan) -> tuple:
    """(hex, planned) to aim at enemy j: the first of its hexes the side sees now, else, for planned
    fire, where it stands near a located place; (None, False) if neither."""
    side, field, known = sfk
    j, e = je
    seen = next((x for x in _marks(d, e) if U.spotted(d, us, field, side, x)), None) if str(j) in known else None
    if seen is not None:
        return seen, False
    if (plan == "attack" and _near_located(d, field, e)) or (plan == "hold" and _near_own(d, field, side, e)):
        return e["pos"], True
    return None, False


def _near_own(d: Data, field: dict | None, side, e: dict) -> bool:
    """Holding: enemy e within indirect.planned.defend hexes of a place the side itself held when the
    battle began (field.located): in its defensive fire plan."""
    far = d.units["indirect"]["planned"]["defend"]
    return e["men"] > 0 and e["state"] not in ROUTED and any(s == side and U.hdist(h, e["pos"]) <= far for s, h in (field or {}).get("located") or [])


def _near_located(d: Data, field: dict | None, e: dict) -> bool:
    """Standing within indirect.planned.near hexes of a place its side held when the battle began
    (field.located, set by battle.begin)."""
    near = d.units["indirect"]["planned"]["near"]
    return e["men"] > 0 and e["state"] not in ROUTED and any(s == e["side"] and U.hdist(h, e["pos"]) <= near for s, h in (field or {}).get("located") or [])


def _air_scatter(d: Data, us: list, field: dict | None, bk: tuple, h) -> int:
    """The scatter battery b (kind K) would have at hex h: for aircraft with a forward air
    controller of their side who sees h, cut by indirect.air.fac.scatter; else the kind's."""
    b, K = bk
    if K.get("air") and field and U._fac_sees(d, us, field, b, h):
        return K["scatter"] // d.units["indirect"]["air"]["fac"]["scatter"]
    return K["scatter"]


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
    """One unit's order, or None (it holds). ctx: (size, field, stance, known, exchange). A unit
    that has gone round on a plan's envelopment attacks, whatever its side's stance."""
    u, C = us[i], d.units["commander"]
    if _enveloping(u):
        ctx = (ctx[0], ctx[1], "attack", ctx[3], ctx[4])
    obj = objective(ctx[1])
    t = _focus(us, i, ctx[3], target(d, us, i, ctx[3], ctx[1]))
    if u["state"] != "steady":
        return _unsteady(d, us, i, t)
    away = _withdraw_order(d, us, i, ctx)
    if away is not None:
        return away
    if U.busy_digging(u) or u.get("resupplying"):
        return None
    ammo = _ammo_order(d, us, i, t, ctx)
    if ammo is not None:
        return ammo
    if u.get("reserve"):
        return _reserve_order(d, us, i, t, ctx)
    first = _pursuit(d, us, i, ctx) or _sapper_order(d, us, i, t, ctx) or _route_order(d, us, i, ctx)   # in that order
    if first is not None:
        return first
    task = _task_order(d, us, i, t, ctx)
    if task is not None:
        return task[0]
    if (obj is not None or ctx[2] == "hold") and _digs(d, us, i, ctx):
        return {"act": "dig", "target": t}
    if t is None and obj is None:
        return _search(d, us, i, ctx)
    if roll <= C["hesitate"].get(u["quality"], 0):
        return {"act": "hesitate", "target": t, "roll": roll}
    return _move_order(d, us, i, t, ctx)


def _order_one(d: Data, us: list, i: int, ctx: tuple, at: tuple, roll: int) -> dict | None:
    """Unit i's order this move, or None: its own, gone to ground under fire, an air controller's,
    marked if it goes to plug a gap. ctx: (size, field, stance, known, exchange); at: (aim, table)."""
    (size, field, stance, known, exchange), (aim, table) = ctx, at
    o = _down_under_fire(d, us, i, _order(d, us, i, (size, _plugging(_aim(us, i, aim), us[i]), stance, known, exchange), roll), stance, table)
    o = _spotter(d, us, i, o, (size, field, stance, known)) or o
    if o and us[i].get("plug") and o["act"] in ("advance", "fall_back"):
        o = {**o, "gap": True}                    # going to plug the gap, not the side's objective
    return o


def _down_under_fire(d: Data, us: list, i: int, o: dict | None, stance: str, table: str | None) -> dict | None:
    """Attacking, in a war of fire and movement (commander.bounds_all: the wound table's war), a
    modern foot unit fired on last exchange does not walk on: it goes to ground (or stays down)
    and fires, unless its target is pinned."""
    t = o.get("target") if o else None
    war = (d.tables.get(table) or {}).get("battle") if table else None
    if war not in (d.units["commander"].get("bounds_all") or []) or stance != "attack" or not o or o["act"] not in ("move", "advance") or not bounding(d, us, i, t):
        return o
    return None if us[i].get("prone") else {"act": "ground", "target": t}


def _leaves_disabled(d: Data, u: dict) -> bool:
    """Attacking, a vehicle unit with some vehicles that can still move leaves its immobilised
    ones (commander.leave_disabled)."""
    return bool(d.units["commander"].get("leave_disabled")) and bool(u.get("vehicle")) and u.get("immobile", 0) > 0 and U.vehicles_left(d, u) > u["immobile"]


def _move_order(d: Data, us: list, i: int, t: int | None, ctx: tuple) -> dict | None:
    """Its best order for the target (or the objective), narrowed to fit the ground if it would
    not move nearer (_narrowed), with when the target was last seen."""
    o0 = _best(d, us, i, t, ctx) if objective(ctx[1]) is None else _for_objective(d, us, i, t, ctx)
    o = _narrowed(d, us, i, t, ctx, o0) or o0
    return o if t is None else _last_seen(o, ctx[3], t, ctx[4])


# ---------- plans (data/plans.yaml; docs/units.md, Plans) ----------
TASK_KEYS = ("task", "focus", "goal")             # what a running step puts on its unit


def plan_steps(d: Data, us: list, side, ctx: tuple) -> list:
    """Start and end the side's plan steps (field plan: {side: [steps]}), in order, for each of
    their units standing: a step starts when its `when` fires (at once without one) and ends when
    its `until` fires or its task is done; a unit runs one step at a time, a later one replacing
    it. A step starts once for each unit (its index kept in the unit's `steps`). ctx: (field,
    known, exchange). -> orders [{unit, act: plan, step, do, start, why}] for the log."""
    field = ctx[0]
    out = []
    for k, st in enumerate(((field or {}).get("plan") or {}).get(side) or []):
        for i in range(len(us)):
            u = us[i]
            if u["side"] != side or u["name"] not in st["units"] or u["men"] <= 0 or u["state"] in ROUTED:
                continue
            run = u.get("task")
            if run and run["step"] == k:
                why = _task_done(us, i, run) or (_fires(d, us, (i, st), st["until"], ctx) if st.get("until") else None)
                if why:
                    _end_task(us, i)
                    out.append({"unit": i, "act": "plan", "step": k, "do": st["do"], "start": False, "why": why})
                continue
            if k in (u.get("steps") or []):
                continue
            why = _fires(d, us, (i, st), st["when"], ctx) if st.get("when") else {"start": True}
            if why:
                if run:
                    _end_task(us, i)
                _start_task(us, i, k, st, ctx[2])
                out.append({"unit": i, "act": "plan", "step": k, "do": st["do"], "start": True, "why": why})
    return out


def _start_task(us: list, i: int, k: int, st: dict, exchange) -> None:
    """Step k's task on unit i: withdraw_if gives it the account's withdrawal from now; envelop
    a route and its target; pin its target; advance_to its line; commit releases it from the
    reserve (to: the hex it goes to, as a unit plugging a gap). Any task but withdraw_if takes
    it out of the reserve."""
    u, do = us[i], st["do"]
    u["steps"] = [*(u.get("steps") or []), k]
    if do != "withdraw_if":
        u["reserve"] = False
    if do == "commit":
        if st.get("to"):
            u["plug"] = list(st["to"])
        return
    u["task"] = {"step": k, "do": do}
    if do == "withdraw_if":
        u["withdraw"] = {"at": exchange or 0, "to": st["to"] if isinstance(st["to"], str) else list(st["to"])}
    elif do == "envelop":
        u["via"] = [list(h) for h in st["via"]]
    elif do == "advance_to":
        u["goal"] = list(st["to"])
    if st.get("target") and do in ("envelop", "pin"):
        u["focus"] = st["target"]


def _end_task(us: list, i: int) -> None:
    """Unit i's running step ends: its task, target and line go (an envelopment's route and a
    withdrawal not yet done with it)."""
    u = us[i]
    do = u["task"]["do"]
    for key in TASK_KEYS:
        u.pop(key, None)
    if do == "envelop":
        u.pop("via", None)
    elif do == "withdraw_if":
        u.pop("withdraw", None)


def _task_done(us: list, i: int, run: dict) -> dict | None:
    """Why unit i's running task is done, or None: a withdrawal is over (at its hex, holding),
    its target has broken or is gone, an envelopment with no target has gone round."""
    u = us[i]
    if run["do"] == "withdraw_if" and not u.get("withdraw"):
        return {"done": True}
    if u.get("focus") and _named(us, u["focus"], u["side"], False) is None:
        return {"broken": u["focus"]}
    if run["do"] == "envelop" and not u.get("focus") and not u.get("via"):
        return {"done": True}
    return None


def _named(us: list, name: str, side, ours: bool) -> int | None:
    """The index of the unit of that name, of side (ours) or not, still standing; or None."""
    return next((j for j, e in enumerate(us) if e["name"] == name and (e["side"] == side) == ours and e["men"] > 0 and e["state"] not in ROUTED), None)


def _fires(d: Data, us: list, ist: tuple, w, ctx: tuple) -> dict | None:
    """The trigger that fires for unit i of step st, or None: w is a trigger, a list of them (the
    first that fires) or {all: [...]} (every one)."""
    if isinstance(w, list):
        return next((x for x in w if _fires(d, us, ist, x, ctx)), None)
    if "all" in w:
        return w if all(_fires(d, us, ist, x, ctx) for x in w["all"]) else None
    return w if _trigger(d, us, ist, w, ctx) else None


def _trigger(d: Data, us: list, ist: tuple, w: dict, ctx: tuple) -> bool:
    """One trigger for unit i of step st. ctx: (field, known, exchange)."""
    (i, st), (field, known, exchange) = ist, ctx
    u = us[i]
    if "exchange" in w:
        return (exchange or 0) >= w["exchange"]
    if "phase" in w:
        return w["phase"] in ((field or {}).get("begun") or [])
    if "light" in w:
        order = list(d.weather["light"]["levels"])
        return order.index(((field or {}).get("weather") or {}).get("light") or "day") >= order.index(w["light"])
    if "broken" in w:
        return any(e["name"] == w["broken"] and (e["men"] <= 0 or e["state"] in ROUTED) for e in us)
    if "pinned" in w:
        j = _named(us, w["pinned"], u["side"], False)
        pinning = any(x["side"] == u["side"] and (x.get("task") or {}).get("do") == "pin" and x.get("focus") == w["pinned"] for x in us)
        return j is not None and pinning and bool(us[j]["state"] == "shaken" or us[j].get("prone") or us[j].get("hit") or us[j].get("pinned"))
    if "lost" in w:
        mine = [e for e in us if e["side"] == u["side"] and (w.get("side") or e["name"] in st["units"])]
        start = sum(e["start"] for e in mine)
        return start > 0 and 100 * sum(e["start"] - max(0, e["men"]) for e in mine) >= w["lost"] * start
    if "outflanked" in w:
        reach = d.units["commander"]["plans"]["flank"]
        return any(k.isdigit() and int(k) < len(us) and us[int(k)]["side"] != u["side"] and us[int(k)]["state"] == "steady" and us[int(k)]["men"] > 0
                   and U.arc(u["facing"], U.bearing(u["pos"], m["pos"])) != "front" and U.unit_gap(d, u, _where(us, int(k), known)) <= reach
                   for k, m in (known or {}).items())
    return False


# ---------- the procedural planner (docs/units.md, The procedural planner) ----------
def _plan_if_needed(d: Data, us: list, side, ctx: tuple, rng) -> list:
    """With the planner on (field planner), for a side with no plan that has not planned yet and
    knows of an enemy: the commander writes its plan (plan_for) onto the field (plan, and planned:
    the template chosen). -> [the order that says so, for the log], or []. ctx: (field, known,
    exchange, stance, table)."""
    field, known = ctx[0], ctx[1]
    if not (field or {}).get("planner") or side in ((field.get("plan") or {})) or side in (field.get("planned") or {}):
        return []
    if not _known_foes(us, side, known):
        return []
    p = plan_for(d, us, side, ctx, rng)
    field["planned"] = {**(field.get("planned") or {}), side: p["template"]}
    if p["steps"]:
        field["plan"] = {**(field.get("plan") or {}), side: p["steps"]}
    return [{"act": "planned", "side": side, "template": p["template"], **({"by": p["by"]} if p.get("by") else {})}]


def _known_foes(us: list, side, known: dict | None) -> list:
    """The indices of the enemy units the side knows of, standing (in index order)."""
    return [int(k) for k in (known or {}) if k.isdigit() and int(k) < len(us) and us[int(k)]["side"] != side
            and us[int(k)]["men"] > 0 and us[int(k)]["state"] not in ROUTED]


def _cube_of(h) -> tuple:
    q = h[0] - (h[1] - (h[1] & 1)) // 2
    return q, h[1], -q - h[1]


def _dot(a: tuple, b: tuple) -> int:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _dir_cube(k: int) -> tuple:
    q, r = U.AX[k % 6]
    return q, r, -q - r


def _roles(d: Data, u: dict, modern: bool) -> set:
    """What a unit is for in a plan: fire, assault, mobile (a set, maybe empty)."""
    out, shoots = set(), "range" in d.weapons[u["weapon"]]
    if u.get("vehicle") or u.get("mounted"):
        out.add("mobile")
    if u.get("vehicle"):
        if U._gun_of(d, u) or shoots:
            out.add("fire")
        return out
    if modern and u["weapon"] in d.units["commander"]["ground_with"] and u["weapon"] != "machine_gun" and not u.get("mounted"):
        out.add("assault")
    elif shoots:
        out.add("fire")
    elif u.get("formation") == "close" or u.get("mounted"):
        out.add("assault")
    return out


def plan_for(d: Data, us: list, side, ctx: tuple, rng) -> dict:
    """The commander's own plan for side: {template, steps, by (the flank waypoint, if any)}. It reads
    the odds, the period, its units' roles, the known enemy's front and the open flanks, weighs the
    templates that fit (planner.weights) and picks one by the dice. ctx: (field, known, exchange,
    stance, table)."""
    field, known, exchange, stance, table = ctx
    P = d.units["commander"]["planner"]
    war = (d.tables.get(table) or {}).get("battle") if table else None
    modern = war in (d.units["commander"].get("bounds_all") or [])
    mine = [i for i, u in enumerate(us) if u["side"] == side and u["men"] > 0 and u["state"] not in ROUTED
            and not U.is_battery(d, u) and not U.is_at_gun(d, u)]
    foes = _known_foes(us, side, known)
    seen = {j: _where(us, j, known) for j in foes}
    force = lambda ix, w: sum(w(j)["men"] * U.quality(d, w(j)["quality"])["attack"] for j in ix)
    ours, theirs = force(mine, lambda j: us[j]), force(foes, lambda j: seen[j])
    roles = {i: _roles(d, us[i], modern) for i in mine}
    front = _front(us, mine, foes, seen)
    flanks = [f for f in (_flank(d, us, field, (front, +1), (mine, foes, seen)), _flank(d, us, field, (front, -1), (mine, foes, seen))) if f]
    flanks.sort(key=lambda f: f["cost"])
    mobile = [i for i in mine if "mobile" in roles[i]]
    W = P["weights"]
    cands = []
    if stance == "attack":
        if any(roles[i] & {"fire", "assault"} for i in mine):
            cands.append(("assault", W["assault"]))
        if mobile and flanks:
            cands.append(("single", W["single"]))
        if len(mobile) >= 2 and len(flanks) == 2 and ours >= P["double"] * theirs:
            cands.append(("double", W["double"]))
    else:
        if any(us[i].get("reserve") for i in mine):
            cands.append(("counter", W["counter"]))
        if theirs >= P["delay"] * ours:
            cands.append(("delay", W["delay"]))
        cands.append(("stand", W["stand"]))
    if not cands:
        return {"template": "stand", "steps": []}
    pick = cands[0][0]
    if len(cands) > 1:
        roll, total = rng.randint(1, sum(w for _, w in cands)), 0
        for name, w in cands:
            total += w
            if roll <= total:
                pick = name
                break
    return _template(d, us, (pick, mine, foes, seen, roles), (front, flanks, mobile), (exchange, modern, P))


def _front(us: list, mine: list, foes: list, seen: dict) -> dict:
    """The axis from the side to the known enemy (a hex direction, as units.bearing picks it), the
    lateral (left of the axis, as the two directions after it), and the enemy units at each end."""
    so = [sum(_cube_of(us[i]["pos"])[k] for i in mine) for k in range(3)]
    se = [sum(_cube_of(seen[j]["pos"])[k] for j in foes) for k in range(3)]
    v = tuple(len(mine) * se[k] - len(foes) * so[k] for k in range(3))
    dots = [_dot(v, _dir_cube(k)) for k in range(6)]
    axis = dots.index(max(dots))
    lat = tuple(a + b for a, b in zip(_dir_cube(axis + 1), _dir_cube(axis + 2)))
    p = {j: _dot(_cube_of(seen[j]["pos"]), lat) for j in foes}
    left = min(foes, key=lambda j: (-p[j], j))
    right = min(foes, key=lambda j: (p[j], j))
    return {"axis": axis, "lat": lat, "ends": {+1: left, -1: right}}


def _walk(h, axis: int, sgn: int, n: int, size) -> list | None:
    """n steps sideways from h (left of the axis for sgn +1, right for -1), alternating the two hex
    directions either side of the perpendicular; None if it leaves the map."""
    dirs = (axis + 1, axis + 2) if sgn > 0 else (axis - 1, axis - 2)
    h = list(h)
    for k in range(n):
        h = U.step(h, dirs[k % 2] % 6)
        if not (0 <= h[0] < size[0] and 0 <= h[1] < size[1]):
            return None
    return h


def _flank(d: Data, us: list, field: dict | None, fs: tuple, sides: tuple) -> dict | None:
    """The way round the enemy's end on one side (sgn +1 its left of our axis, -1 its right):
    {sgn, end (its end unit), via [W1, W2], cost (average going)}, or None if it is not open."""
    (front, sgn), (mine, foes, seen) = fs, sides
    P, size = d.units["commander"]["planner"], (field or {}).get("size") or [60, 40]
    end, lat = front["ends"][sgn], front["lat"]
    w2 = _walk(seen[end]["pos"], front["axis"], sgn, P["flank_gap"], size)
    if w2 is None:
        return None
    ours = min(mine, key=lambda i: (-sgn * _dot(_cube_of(us[i]["pos"]), lat), i))
    level = sgn * _dot(_cube_of(w2), lat)
    w1, h = None, list(us[ours]["pos"])
    for _ in range(size[0] + size[1]):
        if sgn * _dot(_cube_of(h), lat) >= level:
            w1 = h
            break
        h = _walk(h, front["axis"], sgn, 1, size)
        if h is None:
            return None
    if w1 is None:
        return None
    path = [x for a, b in ((us[ours]["pos"], w1), (w1, w2)) for x in U.ray(a, b, U.hdist(a, b))]
    cost, keys = 0, {k: g for k, g in d.units["ground"].items()}
    for x in path:
        kind = ((field or {}).get("ground") or {}).get(f"{x[0]},{x[1]}", "open")
        if keys[kind].get("impassable"):
            return None
        cost += keys[kind]["move"]
        if any(j != end and U.hdist(x, seen[j]["pos"]) < P["flank_gap"] for j in foes):
            return None
    if cost > P["going"] * len(path):
        return None
    return {"sgn": sgn, "end": end, "via": [list(w1), list(w2)], "cost": cost * 1000 // len(path)}


def _template(d: Data, us: list, who: tuple, ground: tuple, when: tuple) -> dict:
    """The chosen template's steps. who: (template, mine, foes, seen, roles); ground: (front,
    flanks, mobile); when: (exchange, modern, planner settings)."""
    pick, mine, foes, seen, roles = who
    front, flanks, mobile = ground
    exchange, modern, P = when
    name = lambda j: us[j]["name"]
    nearest = lambda i: min(foes, key=lambda j: (U.hdist(us[i]["pos"], seen[j]["pos"]), j))
    steps, by = [], None
    if pick == "stand":
        return {"template": "stand", "steps": []}
    if pick == "delay":
        edge = _behind(front["axis"])
        steps.append({"units": [name(i) for i in mine], "do": "withdraw_if", "to": edge, "when": [{"outflanked": True}, {"lost": 25}]})
        return {"template": "delay", "steps": steps}
    if pick == "counter":
        steps.append({"units": [name(i) for i in mine if us[i].get("reserve")], "do": "commit", "when": [{"broken": name(j)} for j in foes]})
        return {"template": "counter", "steps": steps}
    going = {"single": flanks[:1], "double": flanks[:2]}.get(pick, [])
    movers = set(mobile) if going else set()
    for i in mine:
        if i in movers:
            continue
        t = nearest(i)
        if "fire" in roles[i]:
            steps.append({"units": [name(i)], "do": "pin", "target": name(t)})
        elif "assault" in roles[i] and U.hdist(us[i]["pos"], seen[t]["pos"]) > P["start"] + d.units["commander"]["route"]["reach"]:
            line = U.ray(seen[t]["pos"], us[i]["pos"], P["start"])[-1]
            until = [{"exchange": (exchange or 0) + P["wait"]}]
            if modern:
                until = [{"pinned": name(t)}] + until
            steps.append({"units": [name(i)], "do": "advance_to", "to": list(line), "until": until})
    if going:
        lat = front["lat"]
        order = sorted(movers, key=lambda i: (-_dot(_cube_of(us[i]["pos"]), lat), i))   # leftmost first
        groups = [order] if len(going) == 1 else [order[:(len(order) + 1) // 2], order[(len(order) + 1) // 2:]]
        if len(going) == 2 and going[0]["sgn"] < 0:
            going = [going[1], going[0]]           # the left flank's force is the leftmost half
        for f, grp in zip(going, groups):
            if grp:
                steps.append({"units": [name(i) for i in grp], "do": "envelop", "via": f["via"], "target": name(f["end"])})
        by = going[0]["via"][-1]
    return {"template": pick, "steps": steps, **({"by": by} if by else {})}


def _behind(axis: int) -> str:
    """The map edge behind a side whose axis to the enemy is that hex direction: E: W; NE and NW
    (leaning north): S; W: E; SW and SE (leaning south): N."""
    return {0: "W", 1: "S", 2: "S", 3: "E", 4: "N", 5: "N"}[axis % 6]


def _enveloping(u: dict) -> bool:
    """On a plan's envelopment, its route done."""
    return (u.get("task") or {}).get("do") == "envelop" and not u.get("via")


def _focus(us: list, i: int, known: dict | None, t: int | None) -> int | None:
    """The plan's target for unit i (focus, by name) if it stands and its side knows of it, else t."""
    name = us[i].get("focus")
    if not name:
        return t
    j = _named(us, name, us[i]["side"], False)
    return j if j is not None and (known is None or str(j) in known) else t


def _task_order(d: Data, us: list, i: int, t: int | None, ctx: tuple) -> tuple | None:
    """(order or None) for a unit on a plan's advance_to or pin; None for any other unit (the
    rest of the chain orders it). advance_to: to its line (within commander.route.reach), then
    it stays there facing its target. pin: see _pin_order."""
    u = us[i]
    do = (u.get("task") or {}).get("do")
    if do == "advance_to":
        size, field, stance, known, exchange = ctx
        if U.hdist(u["pos"], u["goal"]) > d.units["commander"]["route"]["reach"]:
            o = _toward(d, us, i, t, (size, {**(field or {}), "objective": u["goal"], "objective_radius": None}, stance, known, exchange), "advance")
            if o is not None:
                return ({**o, "line": True},)
        return (_hold_line(d, us, i, t, known),)
    if do == "pin":
        return (None,) if t is None else (_pin_order(d, us, i, t, ctx),)
    return None


def _hold_line(d: Data, us: list, i: int, t: int | None, known: dict | None) -> dict | None:
    """Staying where it is, facing its target if any (going to ground under fire as any unit)."""
    if t is None:
        return None
    u = us[i]
    shooter = "range" in d.weapons[u["weapon"]] or bool(U._gun_of(d, u))
    return _stay(d, us, i, t, keep_front(u, U.bearing(u["pos"], _where(us, t, known)["pos"])), shooter)


def _pin_order(d: Data, us: list, i: int, t: int, ctx: tuple) -> dict | None:
    """Pinning target t: a unit that shoots (its weapon or main gun) goes to the hex it can reach
    furthest from t from which it can still hit it, and stays there firing (drawing back if it
    is closer); none in reach, it moves nearer. A unit that cannot shoot stands just beyond t's
    charge (t's move and a hex), nearest it, in sight of it. It never closes to contact."""
    size, field, stance, known, exchange = ctx
    u, tu = us[i], _where(us, t, known)
    shooter = "range" in d.weapons[u["weapon"]] or bool(U._gun_of(d, u))
    if _stuck(u):
        return _hold_line(d, us, i, t, known)
    free = {**u, "prone": False} if u.get("prone") else u
    base = [free if k == i else x for k, x in enumerate(us)]
    foes = {k for k, j in U.occupancy(d, base).items() if base[j]["side"] != u["side"]}
    keep = U.allowance(d, tu) + 1
    cands = []
    for h, c in reachable(d, base, i, size, U.allowance(d, free), field).items():
        h, dist = list(h), U.hdist(list(h), tu["pos"])
        if shooter:
            ok = dist >= 1 and ((U.field_range(d, u["weapon"], dist) is not None and _sees_to(d, field, u, (h, tu["pos"], dist)))
                                or _gun_in_range(d, field, u, (h, tu["pos"], dist))) and U.clear_sight(d, field, h, tu["pos"], dist)
            rank = -dist                          # furthest first
        else:
            ok = U.unit_gap(d, {**u, "pos": h}, tu) > keep and U.clear_sight(d, field, h, tu["pos"], dist)
            rank = dist                           # nearest first
        if ok:
            cands.append((rank, c, h[1], h[0]))
    for _, c, row, col in sorted(cands):
        h = [col, row]
        if h == list(u["pos"]):
            return _hold_line(d, us, i, t, known)
        f = U.bearing(h, tu["pos"])
        fs = [g for g in _facings(f, u["facing"]) if c + _turning(d, free, g) <= U.allowance(d, free) and not _touches(d, {**u, "pos": h, "facing": g}, foes)]
        if not fs:
            continue
        m, g = _legal_facing(d, base, i, (h, fs[0], c, False), (size, field, foes))
        if m["ok"]:
            return _rising(u, {"act": "move", "target": t, "pos": h, "facing": g, "cost": m["cost"], "pin": True})
    if cands:
        return _hold_line(d, us, i, t, known)
    o = _toward(d, us, i, t, (size, {**(field or {}), "objective": list(tu["pos"]), "objective_radius": None}, stance, known, exchange), "advance")
    return {**o, "pin": True} if o is not None else _hold_line(d, us, i, t, known)


def _withdraw_order(d: Data, us: list, i: int, ctx: tuple) -> dict | None:
    """Orders from the account (data/orders.yaml withdraw {at, to}): from exchange at, it falls
    back to hex to and holds it once there, or to map edge to and leaves the field there."""
    u = us[i]
    W = u.get("withdraw")
    if not W or (ctx[4] or 0) < W["at"]:
        return None
    size, edge = U._size(d, ctx[1]), isinstance(W["to"], str)
    if not edge and U.hdist(u["pos"], W["to"]) <= d.units["commander"]["route"]["reach"]:
        del u["withdraw"]
        u["hold"] = True
        return None
    if edge and any(U._edge_gap(W["to"], h, size) == 0 for row in U.footprint(d, u) for h in row):
        return {"act": "leave"}
    goal = _edge_straight(u["pos"], W["to"], size) if edge else W["to"]
    o = _toward(d, us, i, None, (ctx[0], {**ctx[1], "objective": goal, "objective_radius": None}, ctx[2], ctx[3], ctx[4]), "fall_back")
    return o if o is not None or not edge else {"act": "leave"}


def _edge_straight(h, edge: str, size) -> list:
    """The hex on map edge N, S, E or W straight from h."""
    cols, rows = size
    return {"N": [h[0], 0], "S": [h[0], rows - 1], "W": [0, h[1]], "E": [cols - 1, h[1]]}[edge]


def _narrowed(d: Data, us: list, i: int, t: int | None, ctx: tuple, o: dict | None) -> dict | None:
    """Attacking, a formed unit out of contact that would not move nearer its target closes in a
    quarter at a time, deeper, to the widest front that lets it move nearer (commander.narrow):
    the order with its new width, or None. Self-play showed the French at Agincourt held off by
    the narrowing ground, their 60-hex front unable to fit nearer the English line."""
    u = us[i]
    if not d.units["commander"].get("narrow") or ctx[2] != "attack" or t is None or not _formed(d, u) or u["width"] <= 1:
        return None
    if U.in_contact(d, us, U.occupancy(d, us), i) or (o is not None and o["act"] in MOVES):
        return None
    tu, obj = _where(us, t, ctx[3]), objective(ctx[1])
    now = U.unit_gap(d, u, tu)
    least = math.ceil(u.get("width0", u["width"]) * d.units["commander"]["narrow_to"])   # never narrower than this share of the front it started with
    for q in (3, 2, 1):
        w = max(least, 1, -(-u["width"] * q // 4))
        if w >= u["width"]:
            continue
        trial = [{**x, "width": w} if k == i else x for k, x in enumerate(us)]
        o2 = _best(d, trial, i, t, ctx) if obj is None else _for_objective(d, trial, i, t, ctx)
        if o2 is not None and o2["act"] in MOVES and U.unit_gap(d, {**u, "width": w, "pos": o2["pos"], "facing": o2["facing"]}, tu) < now:
            return {**o2, "width": w, "width0": u.get("width0", u["width"])}
    return None


VETERANS = ("veteran", "elite")                    # the qualities that rally from a pursuit


def _pursuit(d: Data, us: list, i: int, ctx: tuple) -> dict | None:
    """A steady unit that fights hand to hand (or a mounted one) goes after a broken enemy: horse
    one within a charge of it (its move times charge_move) with no standing enemy as near, foot
    one within its move nearer than any standing enemy; veterans give it up after
    commander.pursuit.rally moves with a standing enemy in reach. The move or charge toward it
    (pursue), its count kept on the unit (chased), or None (and the count dropped)."""
    u = us[i]
    o = _chase(d, us, i, ctx) if _may_pursue(d, u) else None
    if o is None:
        u.pop("chased", None)
        return None
    u["chased"] = u.get("chased", 0) + 1
    return {**o, "pursue": True}


def _may_pursue(d: Data, u: dict) -> bool:
    """Steady, not a vehicle, not on a route, and not a shooter on foot."""
    return u["state"] == "steady" and not u.get("vehicle") and not u.get("via") and ("range" not in d.weapons[u["weapon"]] or bool(u.get("mounted")))


def _chase(d: Data, us: list, i: int, ctx: tuple) -> dict | None:
    """The move or charge toward the broken enemy unit i goes after (_pursuit), or None."""
    u = us[i]
    reach = U.allowance(d, u) * (d.units["charge_move"] if u.get("mounted") else 1)
    best, standing = _broken_near(d, us, i, reach)
    if best is None or standing <= (reach if u.get("mounted") else best[0]):
        return None
    if u["quality"] in VETERANS and u.get("chased", 0) >= d.units["commander"]["pursuit"]["rally"] and standing <= reach:
        return None
    o = _best(d, us, i, best[1], (ctx[0], ctx[1], "attack", None, ctx[4]))
    return o if o and o["act"] in MOVES else None


def _broken_near(d: Data, us: list, i: int, reach: int) -> tuple:
    """((gap, index) of the nearest broken enemy within reach, or None; the gap to the nearest standing enemy)."""
    u, best, standing = us[i], None, float("inf")
    for j, e in enumerate(us):
        if e["side"] == u["side"] or e["men"] <= 0:
            continue
        gap = U.unit_gap(d, u, e)
        if e["state"] in ("steady", "shaken"):
            standing = min(standing, gap)
        elif e["state"] == "broken" and gap <= reach and (best is None or gap < best[0]):
            best = (gap, j)
    return best, standing


def _route_order(d: Data, us: list, i: int, ctx: tuple) -> dict | None:
    """A unit on its route (via: waypoints the battlefield gives it from the accounts, a flank
    march) goes on to the next, dropping each it reaches (within commander.route.reach hexes).
    It turns aside only for an enemy in contact or right across its way (_route_blocked); with
    none left, or no way on, None: it is ordered as any other unit."""
    u, reach = us[i], d.units["commander"]["route"]["reach"]
    if not u.get("via"):
        return None
    via = list(u["via"])
    while via and U.hdist(u["pos"], via[0]) <= reach:
        via.pop(0)
    if via:
        u["via"] = via
    else:
        del u["via"]
    if not via or _route_blocked(d, us, i, via[0], ctx[3]):
        return None
    size, field, stance, known, exchange = ctx
    return _toward(d, us, i, None, (size, {**(field or {}), "objective": via[0], "objective_radius": None}, stance, known, exchange), "advance")


def _route_blocked(d: Data, us: list, i: int, w, known: dict | None) -> bool:
    """In contact, or an enemy it knows of within its move of the straight way to waypoint w
    (within a hex of it)."""
    u = us[i]
    if U.in_contact(d, us, U.occupancy(d, us), i):
        return True
    way = U.ray(u["pos"], w, U.hdist(u["pos"], w))[1:U.allowance(d, u) + 1]
    return any(k.isdigit() and any(U.hdist(h, m["pos"]) <= 1 for h in way) for k, m in (known or {}).items())


def _search(d: Data, us: list, i: int, ctx: tuple) -> dict | None:
    """Attacking, with no objective and no enemy it knows of: it goes forward to find one, a move
    toward the last hex on the map straight ahead along its facing (as toward an objective).
    Holding, it stays (None)."""
    size, field, stance, known, exchange = ctx
    if stance != "attack":
        return None
    u, cols_rows = us[i], U._size(d, field)
    ahead, n = list(u["pos"]), 1
    while True:
        h = U.step(u["pos"], u["facing"], n)
        if not (0 <= h[0] < cols_rows[0] and 0 <= h[1] < cols_rows[1]):
            break
        ahead, n = list(h), n + 1
    if ahead == list(u["pos"]):
        return None
    return _toward(d, us, i, None, (size, {**(field or {}), "objective": ahead, "objective_radius": None}, stance, known, exchange), "search")


def _spotter(d: Data, us: list, i: int, o: dict | None, cx: tuple) -> dict | None:
    """Attacking, a forward air controller (a unit marked fac) that would otherwise stand or turn
    moves up to see a target for its side's aircraft: when they can fly and none of its
    controllers sees where an enemy it knows of stands (_to_see). cx: (size, field, stance, known)."""
    size, field, stance, known = cx
    u = us[i]
    if stance != "attack" or not u.get("fac") or (o is not None and o["act"] != "turn"):
        return None
    if u.get("prone") or u.get("reserve") or U.busy_digging(u):
        return None
    if not any(_free_air(d, field, b, u["side"]) for b in (field or {}).get("support") or []):
        return None
    if _own_fight(d, us, i, field):
        return None
    ranked = _ranked_foes(d, us, i, known, field)
    if not ranked or any(U._fac_sees(d, us, field, u, p) for _, p in ranked):
        return None
    return _to_see(d, us, i, ranked, (size, field))


def _own_fight(d: Data, us: list, i: int, field: dict | None) -> bool:
    """The controller has a fight of its own: an enemy touching it, an enemy it sees within its
    own weapon's reach (it shoots instead), or under fire: pinned, or it lost men last exchange
    (hit)."""
    u = us[i]
    if u.get("pinned") or u.get("hit") or U.in_contact(d, us, U.occupancy(d, us), i):
        return True
    if "range" not in d.weapons[u["weapon"]]:
        return False
    return any(e["side"] != u["side"] and e["state"] not in ROUTED and e["men"] > 0
               and U.field_range(d, u["weapon"], U.hdist(u["pos"], e["pos"])) is not None
               and U._sees(d, field, u, e["pos"], U._sight_hexes(d, field, e["pos"], U._seer(u))) for e in us)


def _ranked_foes(d: Data, us: list, i: int, known: dict | None, field: dict | None) -> list:
    """The enemies its side knows of, best target first (as target ranks them), each with where
    it was last seen: [(index, hex)]."""
    u = us[i]
    foes = sorted((-threat_score(d, u, us[j], _where(us, j, known)) - _guards(d, _where(us, j, known), field), j) for j, e in enumerate(us)
                  if e["side"] != u["side"] and e["state"] not in ROUTED and e["men"] > 0 and str(j) in (known or {}))
    return [(j, list(_where(us, j, known)["pos"])) for _, j in foes]


def _to_see(d: Data, us: list, i: int, ranked: list, where: tuple) -> dict | None:
    """The controller's spot: a hex within commander.spot.moves moves' worth of going (not where
    it stands, no known minefield on the straight way) from which, facing the enemy, it sees where
    an enemy it knows of stands, touching none. It prefers one out of the reach of the enemies it
    knows of (_safe_spot), if one costs no more than the cheapest by `safe` moves; else the
    cheapest. Of equally cheap ones, the one that sees the best target, then the lowest row and
    column. Within one move it goes there; further, it moves a move toward it (_step_to).
    -> a spot order, or None."""
    size, field = where
    u, C = us[i], d.units["commander"]
    allow, tries = U.allowance(d, u), C["tries"]
    foes = {k for k, j in U.occupancy(d, us).items() if us[j]["side"] != u["side"]}
    cands = _spot_cands(d, us, i, ranked, (size, field, foes))
    if not cands:
        return None
    safe = [x for x in cands if x[0] <= cands[0][0] + C["spot"]["safe"] * allow and _safe_spot(d, us, [x[3], x[2]], ranked)]
    for c, _, row, col, j, f in safe or cands:
        if tries <= 0:
            return None
        if c <= allow:
            tries -= 1
            m = U.move(d, us, i, [col, row], f, size, field)
            if m["ok"] and not m.get("charge"):
                return {"act": "spot", "target": j, "pos": [col, row], "facing": f, "cost": m["cost"]}
            continue
        o, tries = _step_to(d, us, i, ([col, row], j, ranked), (size, field, foes, tries))
        if o is not None:
            return o
    return None


def _spot_cands(d: Data, us: list, i: int, ranked: list, where: tuple) -> list:
    """[(movement, rank, row, col, enemy, facing)], cheapest first, for each hex within spot.moves
    moves (not its own, no known mines on the straight way) from which it sees a known enemy."""
    size, field, foes = where
    u = us[i]
    out = []
    for h, c in reachable(d, us, i, size, U.allowance(d, u) * d.units["commander"]["spot"]["moves"], field).items():
        if list(h) == list(u["pos"]) or _mined(field, u["pos"], h, u["side"]):
            continue
        seen = _sees_from(d, field, {**u, "pos": list(h)}, ranked, foes)
        if seen is not None:
            out.append((c, seen[0], h[1], h[0], seen[1], seen[2]))
    return sorted(out)


def _safe_spot(d: Data, us: list, h: list, ranked: list) -> bool:
    """No enemy its side knows of, where it was last seen, reaches hex h with its missile weapon."""
    return not any("range" in d.weapons[us[j]["weapon"]] and U.field_range(d, us[j]["weapon"], U.hdist(p, h)) is not None for j, p in ranked)


def _step_to(d: Data, us: list, i: int, aim: tuple, wt: tuple) -> tuple:
    """A move toward a spot beyond this move: the hex within its allowance nearest the spot (then
    the cheapest, the lowest row and column), nearer than it stands, touching no enemy, facing the
    enemy it goes to see; each try costs one of commander.tries. -> (order or None, tries left)."""
    (spot, j, ranked), (size, field, foes, tries) = aim, wt
    u = us[i]
    p = next(q for k, q in ranked if k == j)
    now = U.hdist(u["pos"], spot)
    steps = sorted((U.hdist(list(h), spot), c, h[1], h[0]) for h, c in reachable(d, us, i, size, U.allowance(d, u), field).items()
                   if U.hdist(list(h), spot) < now and not _mined(field, u["pos"], h, u["side"]))
    for _, _, row, col in steps:
        f = U.bearing([col, row], p)
        if _touches(d, {**u, "pos": [col, row], "facing": f}, foes):
            continue
        if tries <= 0:
            break
        tries -= 1
        m = U.move(d, us, i, [col, row], f, size, field)
        if m["ok"] and not m.get("charge"):
            return {"act": "spot", "target": j, "pos": [col, row], "facing": f, "cost": m["cost"], "toward": list(spot)}, tries
    return None, tries


def _sees_from(d: Data, field: dict | None, u: dict, ranked: list, foes: set) -> tuple | None:
    """(rank, enemy, facing) of the best-ranked enemy unit u, where it is placed, would see if it
    faced it without touching the enemy, or None."""
    for r, (j, p) in enumerate(ranked):
        there = {**u, "facing": U.bearing(u["pos"], p)}
        if not _touches(d, there, foes) and U._sees(d, field, there, p, U._sight_hexes(d, field, p, U._seer(there))):
            return r, j, there["facing"]
    return None


def _unsteady(d: Data, us: list, i: int, t: int | None) -> dict | None:
    """A shaken unit holds, going to ground under missile fire."""
    return {"act": "ground", "target": t} if not us[i].get("prone") and not us[i].get("vehicle") and under_fire(d, us, i) else None


def _ammo_order(d: Data, us: list, i: int, t: int | None, ctx: tuple) -> dict | None:
    """A unit low on ammunition or out of it, with a supply source in reach (units.supply_near),
    resupplies: out, at once; low, when no enemy it knows of is within its weapon's range.
    Out with no source in reach, attacking, it falls back toward its side's supply edge
    (holding, it stays and fights hand to hand). None otherwise."""
    u, (size, field, stance, known, exchange) = us[i], ctx
    state = U.ammo_state(d, u)
    if state not in ("low", "out"):
        return None
    if U.supply_near(d, us, i, field) is not None:
        seen = [m["pos"] for k, m in (known or {}).items() if k.isdigit()]
        if state == "out" or not any(U.field_range(d, u["weapon"], U.hdist(u["pos"], p)) is not None for p in seen):
            return {"act": "resupply", "target": t}
        return None
    edge = U.supply_edge(d, us, u["side"])
    if state != "out" or stance != "attack" or edge is None:
        return None
    goal = _edge_hex(edge, u["pos"], U._size(d, field))
    return _toward(d, us, i, t, (size, {**(field or {}), "objective": goal, "objective_radius": None}, stance, known, exchange), "fall_back")


def _edge_hex(edge: str, h, size: tuple) -> list:
    """The hex on map edge N, S, E or W straight across from h (in its column or row)."""
    cols, rows = size
    return {"N": [h[0], 0], "S": [h[0], rows - 1], "W": [0, h[1]], "E": [cols - 1, h[1]]}[edge]


def _reserve_order(d: Data, us: list, i: int, t: int | None, ctx: tuple) -> dict | None:
    """A reserve held back: it digs in where it waits when it is safe to (_safe_to_dig), else it
    stays, turning to face its target."""
    u = us[i]
    if U.can_dig(d, u) and not U.dug_here(u) and _safe_to_dig(d, us, i, ctx[3]):
        return {"act": "dig", "target": t}
    return None if t is None else _stay(d, us, i, t, u["facing"], "range" in d.weapons[u["weapon"]])


def _digs(d: Data, us: list, i: int, ctx: tuple) -> bool:
    """A unit digs in where it stands: at the objective (within its radius), or holding with no
    objective. One that can (units.can_dig), not dug in there already, safe (_safe_to_dig)."""
    u, field = us[i], ctx[1]
    if not U.can_dig(d, u) or U.dug_here(u):
        return False
    obj = objective(field)
    if obj is not None and U.off_objective(d, u, obj) > U.objective_radii(d, field)[0]:
        return False
    return _safe_to_dig(d, us, i, ctx[3])


def _safe_to_dig(d: Data, us: list, i: int, known: dict | None) -> bool:
    """Safe to dig (three exchanges without moving or firing): not under fire, and no enemy it
    knows of within its weapon's range. One gone to ground digs too."""
    if under_fire(d, us, i):
        return False
    u, seen = us[i], [m["pos"] for k, m in (known or {}).items() if k.isdigit()]
    return not any(U.field_range(d, u["weapon"], U.hdist(u["pos"], p)) is not None for p in seen)


def _sapper_order(d: Data, us: list, i: int, t: int | None, ctx: tuple) -> dict | None:
    """Sappers (units.can_sap) set to work: attacking, they lift the known mines (not their own
    side's) in the row ahead when the straight way to their target (where last seen) or the objective
    crosses known mines, and with that row clear but known enemy mines further on that way, they
    close up to the belt first (_close_up); holding, or at the objective, they lay mines there (_lays)."""
    u, field = us[i], ctx[1]
    if not U.can_sap(d, u):                       # (commanded units are out of contact)
        return None
    row = U.ahead_row(d, field, u)
    mines = (field or {}).get("mines") or {}
    goal = None
    if ctx[2] == "attack":
        goal = _where(us, t, ctx[3])["pos"] if t is not None else objective(field)
    if goal is not None and any(_foes_mine(mines.get(C.hkey(x)), u["side"]) for x in row) and _mined(field, u["pos"], goal, u["side"]):
        return {"act": "lift", "target": t}
    if goal is not None and _foes_on_way(field, u["pos"], goal, u["side"]):
        o = _close_up(d, us, i, (t, goal), ctx)
        if o:
            return o
    if _lays(d, us, i, ctx, row):
        return {"act": "lay", "target": t, "kind": _mine_kind(us, ctx[3])}
    return None


def _foes_on_way(field: dict | None, a, h, side) -> bool:
    """Known enemy minefield hexes (not its own side's) on the straight way from a to h."""
    mines = (field or {}).get("mines") or {}
    return list(a) != list(h) and any(_foes_mine(mines.get(C.hkey(x)), side) for x in U.ray(list(a), list(h), U.hdist(a, h))[1:])


def _close_up(d: Data, us: list, i: int, tg: tuple, ctx: tuple) -> dict | None:
    """Sappers close up to a known enemy minefield on their straight way to goal: step by step
    along that way, facing it, as far as they legally can within their move without a hex of
    theirs in known enemy mines, stopping once the row ahead is mined. -> a close_up order, or
    None if they cannot get on (then they act as any unit)."""
    (t, goal), (size, field) = tg, ctx[:2]
    u, mines = us[i], (field or {}).get("mines") or {}
    f, best = U.bearing(u["pos"], goal), None
    for p in U.ray(list(u["pos"]), list(goal), U.hdist(u["pos"], goal))[1:]:
        there = {**u, "pos": list(p), "facing": f}
        if any(_foes_mine(mines.get(C.hkey(x)), u["side"]) for row in U.footprint(d, there) for x in row):
            break
        m = U.move(d, us, i, list(p), f, size, field)
        if not m["ok"] or m.get("charge"):
            break
        best = (list(p), m["cost"])
        if any(_foes_mine(mines.get(C.hkey(x)), u["side"]) for x in U.ahead_row(d, field, there)):
            break
    if best is None:
        return None
    return {"act": "close_up", "target": t, "pos": best[0], "facing": f, "cost": best[1]}


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
    if off > U.objective_radii(d, ctx[1])[1] and (o is None or o["act"] != "charge") and not us[i].get("hold"):   # hold: its account has it stand where it is
        return _toward(d, us, i, t, ctx, "fall_back") or o
    return o


def _no_target(d: Data, us: list, i: int, ctx: tuple, off: int) -> dict | None:
    """With no enemy to go for: attacking, it advances on the objective unless at it; holding,
    it falls back toward it if further than objective.hold."""
    (radius, hold, _), attack = U.objective_radii(d, ctx[1]), ctx[2] == "attack"
    if off <= (radius if attack else hold) or (not attack and us[i].get("hold")):
        return None
    return _toward(d, us, i, None, ctx, "advance" if attack else "fall_back")


def _attack_objective(d: Data, us: list, i: int, t: int, ctx: tuple, off: int) -> dict | None:
    """Attacking with a target: at the objective it holds, unless its target (where last seen)
    is on the objective too: then it goes on attacking until the objective is clear. Else its
    best order, unless that is only to stand or turn while the target is not guarding the
    objective: then it advances."""
    radius = U.objective_radii(d, ctx[1])[0]
    if off <= radius and U.off_objective(d, _where(us, t, ctx[3]), objective(ctx[1])) > radius:
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
        fs = [g for g in _facings(f, u["facing"]) if c + _turning(d, free, g) <= allow and not _touches(d, {**u, "pos": h, "facing": g}, foes)]
        if not fs:
            continue
        if tries == 0:
            return None
        tries -= 1
        m, g = _legal_facing(d, base, i, (h, fs[0], c, False), (size, field, foes))
        if m["ok"]:
            return _rising(u, {"act": act, "target": t, "pos": h, "facing": g, "cost": m["cost"]})
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


def bounding(d: Data, us: list, i: int, t: int) -> bool:
    """Storming in bounds (commander.bounds): a modern unit (ground_with) that heeds cover, hit or
    pinned last exchange, stays down and fires this move unless its target is pinned (or it can
    charge home now: the caller's check)."""
    u, C = us[i], d.units["commander"]
    if not C.get("bounds") or u.get("vehicle") or u["weapon"] not in C["ground_with"] or C["cover"].get(u["quality"], 0) <= 0:
        return False
    return bool(u.get("hit") or u.get("pinned") or u.get("fired_on")) and (t is None or not us[t].get("pinned"))   # fired on, even if no one fell


def storming(d: Data, u: dict, t: dict, field: dict | None, stance: str) -> bool:
    """Attacking, a unit armed for storming (commander.storm: black powder with the bayonet)
    whose target holds works (units.holds_works): it closes and charges rather than firing."""
    return stance == "attack" and u["weapon"] in d.units["commander"]["storm"] and U.holds_works(d, field, u["pos"], t)


def support(d: Data, us: list, i: int) -> int:
    """Men times attack % of the steady friendly units (not guns or vehicles) touching unit i:
    they go in with it, and count toward its charge odds."""
    u = us[i]
    near = {C.hkey(U.step(h, n)) for row in U.footprint(d, u) for h in row for n in range(6)}
    return sum(x["men"] * U.quality(d, x["quality"])["attack"] for k, x in enumerate(us)
               if k != i and x["side"] == u["side"] and x["state"] == "steady" and not U.is_battery(d, x) and not x.get("vehicle")
               and any(C.hkey(h) in near for row in U.footprint(d, x) for h in row))


def may_charge(d: Data, u: dict, t: dict, stance: str = "attack", storm: bool = False, backing: int = 0) -> bool:
    """Men without missiles (or storming works), steady, with the odds its quality wants in its
    stance (charge_odds), counting the friends touching it (backing: their men times attack %)."""
    if ("range" in d.weapons[u["weapon"]] and not storm) or u["state"] != "steady":
        return False
    if _enveloping(u) and U.arc(t["facing"], U.bearing(t["pos"], u["pos"])) != "front":
        return True                               # gone round on a plan: it charges a flank or rear at any odds
    mine = u["men"] * U.quality(d, u["quality"])["attack"] + backing
    theirs = t["men"] * U.quality(d, t["quality"])["attack"]
    return 100 * mine >= d.units["commander"]["charge_odds"][stance].get(u["quality"], 100) * theirs


def _best(d: Data, us: list, i: int, t: int, ctx: tuple) -> dict | None:
    """The best-scoring hex it can legally reach, facing the target: a move, a charge, a turn,
    going to ground where it stands, or None (it holds). Holding, it only charges, else stays.
    If no hex it likes is in reach (facing away, the turn alone eats its move), it turns
    where it stands toward the target, as far as its move allows (_turn_toward)."""
    (size, field, stance, known, _), u = ctx, us[i]
    tu, hold = _where(us, t, known), stance == "hold"
    free = {**u, "prone": False} if u.get("prone") else u
    base = [free if k == i else x for k, x in enumerate(us)]
    storm = storming(d, u, tu, field, stance)
    shooter, charge = "range" in d.weapons[u["weapon"]] and not storm, may_charge(d, u, tu, stance, storm, support(d, us, i))
    best = _first_move(d, base, i, tu, (size, field), (charge, hold, shooter, storm))
    if storm and not (best and best[2]["charge"]) and bounding(d, us, i, t):   # storming in bounds: down and firing after a bound that drew fire
        return None if u.get("prone") else {"act": "ground", "target": t}
    if best is None:
        f = keep_front(u, U.bearing(u["pos"], tu["pos"]))
        f = _turn_toward(d, base, i, f, (size, field))
        return _stay(d, us, i, t, u["facing"] if f is None else f, shooter)   # no turn it can make: it still goes to ground under fire
    h, f, m = best
    if h == list(u["pos"]):
        return _stay(d, us, i, t, f, shooter)
    return {"act": "charge" if m["charge"] else "move", "target": t, "pos": h, "facing": f, "cost": m["cost"],
            **({"up": True} if u.get("prone") else {}), **({"through": m["through"]} if m.get("through") else {})}


def _turn_toward(d: Data, base: list, i: int, f: int, where: tuple) -> int | None:
    """The facing nearest f, turning the shorter way from where unit i faces, that it can
    reach this move where it stands (f itself if it can), or None (not even a step)."""
    size, field = where
    u = base[i]
    right = (f - u["facing"]) % 6
    sign = 1 if right <= 3 else -1
    for n in range(min(right, 6 - right), 0, -1):
        g = (u["facing"] + sign * n) % 6
        if U.move(d, base, i, u["pos"], g, size, field)["ok"]:
            return g
    return f if right == 0 and U.move(d, base, i, u["pos"], f, size, field)["ok"] else None


def _first_move(d: Data, base: list, i: int, tu: dict, where: tuple, how: tuple) -> tuple | None:
    """(hex, facing, move) for the best-scoring hex it will move to, or None. A hex touching
    the enemy is a charge (only with the odds); any other must be within its allowance (and
    holding, it goes nowhere but a charge). Lost in the dark or with vehicles that cannot
    move, it may only turn. It tries `tries` of them at most."""
    (size, field), (charge, hold, shooter, storm), u = where, how, base[i]
    if hold and not charge:
        return None
    allow, tries, stuck = U.allowance(d, u), d.units["commander"]["tries"], bool(u.get("lost") or u.get("immobile") or u.get("emplaced"))
    reach = _reach(d, base, i, (size, allow * (d.units["charge_move"] if charge else 1), field), charge and u["state"] == "steady")
    foes = {k for k, j in U.occupancy(d, base).items() if base[j]["side"] != u["side"]}
    for _, c, _, row, col in sorted((-score(d, field, u, tu, h, c, shooter, storm), c, aside(h, tu["pos"]), h[1], h[0]) for h, (c, _) in reach.items()):
        h, via = [col, row], reach[(col, row)][1]
        f = keep_front(u, U.bearing(h, tu["pos"]))
        touch = _touches(d, {**u, "pos": h, "facing": f}, foes)
        if _skips(touch, (charge, hold, via), c > allow, stuck and h != u["pos"]):
            continue
        if tries == 0:
            return None
        tries -= 1
        m, g = _legal_facing(d, base, i, (h, f, c, touch), (size, field, foes))
        if not _rejects(m, charge, hold):
            return h, g, _passing(d, base, i, (h, m, via))
    return None


def _passing(d: Data, base: list, i: int, move: tuple) -> dict:
    """The legal move m to h, with the friends it passes through if it came through them (via)."""
    h, m, via = move
    return {**m, "through": U.passed_through(d, base, i, h)} if via else m


def _reach(d: Data, base: list, i: int, how: tuple, through: bool) -> dict:
    """{hex: (least movement, passing through friends)}: hexes reached round its own side's
    units, and (through: a steady unit that may charge) those reached only through them."""
    size, limit, field = how
    out = {h: (c, False) for h, c in reachable(d, base, i, size, limit, field).items()}
    if through:
        for h, c in reachable(d, base, i, size, limit, field, through=True).items():
            if h not in out:
                out[h] = (c, True)
    return out


def keep_front(u: dict, b: int) -> int:
    """The facing to take toward direction b: its own if b is already in its front arc (no
    needless turn), else b."""
    return u["facing"] if U.arc(u["facing"], b) == "front" else b


def _skips(touch: bool, how: tuple, far: bool, stuck: bool) -> bool:
    """A hex it will not try: touching the enemy without the odds to charge; not touching but
    beyond its allowance (far), or anything but a charge when holding; reached only through
    its own men (via) but not a charge; or a new hex for a unit that may only turn (stuck)."""
    charge, hold, via = how
    if stuck or (via and not touch):
        return True
    return not charge if touch else hold or far


def _facings(f: int, now: int) -> list:
    """The facings to try for a move meant to face f: f, then a point either side, then two, then
    the one it has now (each once)."""
    out = []
    for g in (f, f + 1, f - 1, f + 2, f - 2, now):
        if g % 6 not in out:
            out.append(g % 6)
    return out


def _legal_facing(d: Data, base: list, i: int, to: tuple, wf: tuple) -> tuple:
    """(move, facing): _legal facing f; if it may not move there facing f (no room, or the turn
    too dear), the nearest facing (_facings) that it may, touching (or not) as before."""
    (h, f, c, touch), (size, field, foes) = to, wf
    m = _legal(d, base, i, to, (size, field))
    if m["ok"]:
        return m, f
    u = base[i]
    for g in _facings(f, u["facing"])[1:]:
        if _touches(d, {**u, "pos": h, "facing": g}, foes) != touch:
            continue
        m2 = _legal(d, base, i, (h, g, c, touch), (size, field))
        if m2["ok"]:
            return m2, g
    return m, f


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
    """Staying where it is: it turns to the target (a unit on the ground turns and stays down);
    else a unit on the ground stays down, or a unit with a modern weapon (ground_with) under
    fire goes to ground (if its quality heeds cover)."""
    u, C = us[i], d.units["commander"]
    if f != u["facing"]:
        return {"act": "turn", "target": t, "facing": f}
    if u.get("prone"):
        return None
    dig = shooter and not u.get("vehicle") and u["weapon"] in C["ground_with"] and C["cover"].get(u["quality"], 0) > 0 and under_fire(d, us, i)
    return {"act": "ground", "target": t} if dig else None


def aside(h, to) -> int:
    """How far hex h lies from hex `to` in a straight line (squared, in units where a hex's
    width is 2 and its rows 3 apart squared): among moves the commander likes equally, the
    one that keeps nearer the straight line wins, so a long advance does not drift sideways."""
    x, tx = 2 * h[0] + (h[1] & 1), 2 * to[0] + (to[1] & 1)
    return (x - tx) ** 2 + 3 * (h[1] - to[1]) ** 2


def score(d: Data, field: dict | None, u: dict, tu: dict, h: tuple, cost: int, shooter: bool, storm: bool = False) -> int:
    """How much the commander likes unit u ending at h (higher is better). Storming works, it
    takes no account of cover on the way."""
    C, q = d.units["commander"], u["quality"]
    dist = U.hdist(list(h), tu["pos"])
    s = (0 if storm else C["cover"].get(q, 0)) * U.cover_at(d, field, tu["pos"], list(h)) - cost - C["mines"].get(q, 0) * _mined(field, u["pos"], h, u["side"])
    if shooter:
        inr = (dist >= 1 and ((U.field_range(d, u["weapon"], dist) is not None and _sees_to(d, field, u, (h, tu["pos"], dist))) or _gun_in_range(d, field, u, (h, tu["pos"], dist)))
               and U.clear_sight(d, field, list(h), tu["pos"], dist))   # in range: and no woods, buildings or crest across the line from there
        stand = C["stand_off"] if inr and u.get("vehicle") and U._gun_of(d, u) and not _answers(d, field, tu, (tu["pos"], list(h), dist)) else 0
        return s + stand + (C["in_range"] if inr else -C["closing"] * dist) - (C["too_close"] if dist < C["keep_off"] else 0)
    flank = C["flank"].get(q, 0) if U.arc(tu["facing"], U.bearing(tu["pos"], list(h))) != "front" else 0
    return s - C["closing"] * dist + flank


def _sees_to(d: Data, field: dict | None, u: dict, shot: tuple) -> bool:
    """Whether the weather and light let u, at h, see t dist away. shot: (h, t, dist)."""
    h, t, dist = shot
    sight = U._sight_hexes(d, field, list(t), U._seer({**u, "pos": list(h)}))
    return sight is None or dist <= sight


def _gun_in_range(d: Data, field: dict | None, u: dict, shot: tuple) -> bool:
    """Whether u's main gun (a vehicle's, or anti-tank guns) reaches from h to t, dist apart, and
    the weather and light let it see t from there. shot: (h, t, dist)."""
    h, t, dist = shot
    G = U._gun_of(d, u)
    if not G or dist > G["range"]:
        return False
    sight = U._sight_hexes(d, field, list(t), U._seer({**u, "pos": list(h)}))
    return sight is None or dist <= sight


def _answers(d: Data, field: dict | None, e: dict, shot: tuple) -> bool:
    """Whether enemy unit e at a could shoot back at hex h, dist away: its own weapon or main gun
    reaches, and the weather and light let it see h. shot: (a, h, dist)."""
    a, h, dist = shot
    sight = U._sight_hexes(d, field, h, U._seer({**e, "pos": list(a)}))
    if sight is not None and dist > sight:
        return False
    if "range" in d.weapons.get(e["weapon"], {}) and U.field_range(d, e["weapon"], dist) is not None:
        return True
    G = U._gun_of(d, e)
    return bool(G) and dist <= G["range"]


def _mined(field: dict | None, a, h, side: int | None = None) -> int:
    """Hexes of minefields its side knows of (marked, found, or laid by its sappers) on the straight
    way from a to h, h included."""
    mines = (field or {}).get("mines") or {}
    if not mines or list(a) == list(h):
        return 0
    known = {k for k, m in mines.items() if U.known_mine(m, side)}
    return sum(1 for x in U.ray(list(a), list(h), U.hdist(a, h))[1:] if C.hkey(x) in known)


def reachable(d: Data, units: list, i: int, size: tuple, limit: int, field: dict | None = None, through: bool = False) -> dict:
    """{hex: least movement} for every hex the unit's middle hex can reach within limit (as
    units._path_len, which it agrees with), its own hex included; through: passing its own
    side's units (for a charge)."""
    occ = U.occupancy(d, U.mates(units, i, through))
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
    elif o["act"] == "leave":
        us[i] = {**u, "state": "fled", "withdrew": True}
    elif o["act"] == "dig":
        us[i] = {**u, "digging": {"at": list(u["pos"]), "n": 0}}
    elif o["act"] == "resupply":
        us[i] = {**u, "resupplying": True}
    elif o["act"] == "lay":
        us[i] = {**u, "mining": {"at": list(u["pos"]), "facing": u["facing"], "n": 0, "kind": o["kind"]}}
    elif o["act"] == "lift":
        us[i] = {**u, "clearing": {"at": list(u["pos"]), "facing": u["facing"], "n": 0}}
    elif o["act"] == "turn":
        us[i] = {**u, "facing": o["facing"]}
    elif o["act"] in MOVES:
        us[i] = {**u, "pos": o["pos"], "facing": o["facing"], "charged": o["act"] == "charge", **({"prone": False} if o.get("up") else {}), **({"width": o["width"], "width0": o["width0"]} if o.get("width") else {})}
        for k in o.get("through", []):                # the friends it charged through are jostled
            us[k] = {**us[k], "jostled": True}
