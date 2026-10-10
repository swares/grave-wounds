"""Travel map: terrain, routes and marching (Grave Wounds). Mirrored exactly by the
travel page (templates/travel.html), between its 'shared with gravewounds/travel.py'
markers.

Hexes are [col, row] on a pointy-top grid with odd rows shifted right, as on the battle
map. Crossing from one hex to the next costs the average of the two terrains' `cost`
multipliers; in whole numbers that is cost_a*100 + cost_b*100 (the "weight"), and the
time is weight / 200 x hex_km / kmh hours."""
from __future__ import annotations

import heapq
import math

from .combat import neighbours
from .model import Data
from .weather import flooded, terrain_pct


def _terrain_by_key(d: Data) -> dict:
    return {t["key"]: t for t in d.terrain["terrain"].values()}


def terrain_at(d: Data, m: dict, h) -> dict:
    return _terrain_by_key(d)[m["rows"][h[1]][h[0]]]


def passable(d: Data, m: dict, h, ftype: str, ground: dict | None = None) -> bool:
    t = terrain_at(d, m, h)
    return (t.get("cost") is not None and t["id"] not in d.terrain["forces"][ftype].get("cannot_enter", [])
            and not flooded(d, t["id"], ground))


def hex_weight(d: Data, t: dict, ground: dict | None = None) -> int:
    """A hex's share of a step, in whole numbers: cost x 100, more on mud or snow."""
    return math.floor(t["cost"] * terrain_pct(d, t["id"], ground) + 0.5)


def step_weight(d: Data, m: dict, a, b, ground: dict | None = None) -> int:
    return hex_weight(d, terrain_at(d, m, a), ground) + hex_weight(d, terrain_at(d, m, b), ground)


def step_hours(d: Data, m: dict, a, b, ftype: str, ground: dict | None = None, speed: int = 100) -> float:
    """Hours to cross from a to b. speed: % of the force's road speed (fatigue)."""
    return step_weight(d, m, a, b, ground) / 200 * m["hex_km"] / (d.terrain["forces"][ftype]["kmh"] * speed / 100)


def route(d: Data, m: dict, start, goal, ftype: str, ground: dict | None = None) -> list | None:
    """Quickest path from start to goal for this kind of force on this ground: a list of
    hexes, start and goal included. None if the goal cannot be reached."""
    start, goal = list(start), list(goal)
    if start == goal:
        return [start]
    if not passable(d, m, goal, ftype, ground):
        return None
    cols, rows = len(m["rows"][0]), len(m["rows"])
    best = {tuple(start): 0}
    prev = {}
    heap = [(0, 0, tuple(start))]
    seq, done = 1, set()
    while heap:
        dist, _, h = heapq.heappop(heap)
        if h in done:
            continue
        done.add(h)
        if list(h) == goal:
            break
        for n in neighbours(list(h), cols, rows):
            if not passable(d, m, n, ftype, ground):
                continue
            nd = dist + step_weight(d, m, list(h), n, ground)
            t = tuple(n)
            if nd < best.get(t, float("inf")):
                best[t] = nd
                prev[t] = h
                heapq.heappush(heap, (nd, seq, t))
                seq += 1
    if tuple(goal) not in prev:
        return None
    path, h = [], tuple(goal)
    while h != tuple(start):
        path.append(list(h))
        h = prev[h]
    path.append(list(start))
    return path[::-1]


def plan(d: Data, m: dict, start, waypoints: list, ftype: str, ground: dict | None = None) -> list | None:
    """Route through each waypoint in turn. None if any leg cannot be made."""
    path, at = [list(start)], list(start)
    for w in waypoints:
        leg = route(d, m, at, w, ftype, ground)
        if leg is None:
            return None
        path += leg[1:]
        at = list(w)
    return path


def _hpd(d: Data, hpd_list, i: int) -> float:
    if not hpd_list:
        return d.terrain["hours_per_day"]
    return hpd_list[min(i, len(hpd_list) - 1)]


def schedule(d: Data, m: dict, path: list, ftype: str, day: int = 1, used: float = 0.0,
             hpd_list: list | None = None, ground: dict | None = None, speed: int = 100) -> list[dict]:
    """When the force reaches each hex of the path, stopping for the night rather than
    start a hex it cannot finish that day. hpd_list: marching hours of `day`, the day after
    and so on (the last repeats); ground: as now (an estimate for later days).
    [{hex, day, used}]: `used` is the marching hours spent that day on arrival."""
    first = day
    out = [{"hex": list(path[0]), "day": day, "used": used}] if path else []
    for a, b in zip(path, path[1:]):
        st = step_hours(d, m, a, b, ftype, ground, speed)
        if used > 0 and used + st > _hpd(d, hpd_list, day - first) + 1e-9:
            day += 1
            used = 0.0
        used += st
        out.append({"hex": list(b), "day": day, "used": used})
    return out


def advance(d: Data, m: dict, path: list, index: int, used: float, hours: float, hpd: float, ftype: str,
            ground: dict | None = None, speed: int = 100) -> dict:
    """March along the path for up to `hours`, never past `hpd`, the day's marching hours.
    Returns {index, used}. A new day is the caller's business."""
    target = min(used + hours, hpd)
    while index + 1 < len(path):
        st = step_hours(d, m, path[index], path[index + 1], ftype, ground, speed)
        if used + st > target + 1e-9:
            break
        used += st
        index += 1
    if index + 1 < len(path):
        used = max(used, target)
    return {"index": index, "used": used}


# ---------- making camp ----------

BATTLE_HEX_M = 2      # the battle map's hex (wounds.yaml combat.move.hex_m); camp works are laid out on it


def near_woods(d: Data, m: dict, h) -> bool:
    """True if the hex or one next to it is forest (timber to hand)."""
    cols, rows = len(m["rows"][0]), len(m["rows"])
    return any(terrain_at(d, m, x)["id"] == "forest" for x in [list(h)] + neighbours(list(h), cols, rows))


def camp_perimeter(d: Data, men: int, ftype: str) -> float:
    """Metres round a camp for this many men: a circle of their camp area."""
    W = d.works
    area = max(W["camp_area_min"], men * W["camp_area"][ftype])
    return 2 * (3.141592653589793 * area) ** 0.5


def camp_hours(d: Data, m: dict, h, kind: str, men: int, ftype: str, tools: bool) -> dict:
    """How long this force takes to make this kind of camp here. {hours, labour, perimeter,
    woods} or {error} if it cannot (no tools, or quartering away from houses)."""
    W = d.works
    c = W["camps"][kind]
    t = terrain_at(d, m, h)
    if c.get("terrain") and t["id"] not in c["terrain"]:
        return {"error": f"needs a {' or '.join(d.terrain['terrain'][x]['name'].lower() for x in c['terrain'])}"}
    if c.get("tools") and not tools:
        return {"error": "needs tools (spades and axes)"}
    woods = near_woods(d, m, h)
    per = camp_perimeter(d, men, ftype)
    labour = 0.0
    for w in c.get("works", []):
        if w in W["edge_works"]:
            e = W["edge_works"][w]
            if "each" in e:
                labour += e["each"]
            else:
                labour += (e["per_metre"] + (0 if woods else e.get("haul", 0))) * per
        else:
            x = W["hex_works"][w]
            labour += (x["each"] + (0 if woods else x.get("haul", 0))) * per / BATTLE_HEX_M
    hours = c["hours"] + labour / (men * W["work_share"])
    return {"hours": hours, "labour": labour, "perimeter": per, "woods": woods}


def camp_done(d: Data, day: int, used: float, hours: float, hpd_list: list | None = None) -> dict:
    """The force's clock when the camp is finished. Camp work can use the day's marching
    hours and then `evening_hours` more; beyond that it runs on into the next day (and
    that day's marching hours). hpd_list: marching hours of `day`, the next day and so on."""
    ev, i = d.works["evening_hours"], 0
    if used >= _hpd(d, hpd_list, i) + ev - 1e-9:
        day += 1
        used = 0.0
        i += 1
    left = hours
    while used + left > _hpd(d, hpd_list, i) + ev + 1e-9:
        left -= _hpd(d, hpd_list, i) + ev - used
        day += 1
        used = 0.0
        i += 1
    return {"day": day, "used": used + left}
