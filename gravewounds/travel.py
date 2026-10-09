"""Travel map: terrain, routes and marching (Grave Wounds). Mirrored exactly by the
travel page (templates/travel.html), between its 'shared with gravewounds/travel.py'
markers.

Hexes are [col, row] on a pointy-top grid with odd rows shifted right, as on the battle
map. Crossing from one hex to the next costs the average of the two terrains' `cost`
multipliers; in whole numbers that is cost_a*100 + cost_b*100 (the "weight"), and the
time is weight / 200 x hex_km / kmh hours."""
from __future__ import annotations

import heapq

from .combat import neighbours
from .model import Data


def _terrain_by_key(d: Data) -> dict:
    return {t["key"]: t for t in d.terrain["terrain"].values()}


def terrain_at(d: Data, m: dict, h) -> dict:
    return _terrain_by_key(d)[m["rows"][h[1]][h[0]]]


def passable(d: Data, m: dict, h, ftype: str) -> bool:
    t = terrain_at(d, m, h)
    return t.get("cost") is not None and t["id"] not in d.terrain["forces"][ftype].get("cannot_enter", [])


def step_weight(d: Data, m: dict, a, b) -> int:
    return round(terrain_at(d, m, a)["cost"] * 100) + round(terrain_at(d, m, b)["cost"] * 100)


def step_hours(d: Data, m: dict, a, b, ftype: str) -> float:
    return step_weight(d, m, a, b) / 200 * m["hex_km"] / d.terrain["forces"][ftype]["kmh"]


def route(d: Data, m: dict, start, goal, ftype: str) -> list | None:
    """Quickest path from start to goal for this kind of force: a list of hexes, start
    and goal included. None if the goal cannot be reached."""
    start, goal = list(start), list(goal)
    if start == goal:
        return [start]
    if not passable(d, m, goal, ftype):
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
            if not passable(d, m, n, ftype):
                continue
            nd = dist + step_weight(d, m, list(h), n)
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


def plan(d: Data, m: dict, start, waypoints: list, ftype: str) -> list | None:
    """Route through each waypoint in turn. None if any leg cannot be made."""
    path, at = [list(start)], list(start)
    for w in waypoints:
        leg = route(d, m, at, w, ftype)
        if leg is None:
            return None
        path += leg[1:]
        at = list(w)
    return path


def schedule(d: Data, m: dict, path: list, ftype: str, day: int = 1, used: float = 0.0) -> list[dict]:
    """When the force reaches each hex of the path, marching `hours_per_day` a day and
    stopping for the night rather than start a hex it cannot finish that day.
    [{hex, day, used}]: `used` is the marching hours spent that day on arrival."""
    hpd = d.terrain["hours_per_day"]
    out = [{"hex": list(path[0]), "day": day, "used": used}] if path else []
    for a, b in zip(path, path[1:]):
        st = step_hours(d, m, a, b, ftype)
        if used > 0 and used + st > hpd + 1e-9:
            day += 1
            used = 0.0
        used += st
        out.append({"hex": list(b), "day": day, "used": used})
    return out


def advance(d: Data, m: dict, path: list, index: int, day: int, used: float, hours: float, ftype: str) -> dict:
    """March along the path for up to `hours` (never past the end of the marching day).
    Returns {index, day, used}: where the force is on the path and its clock."""
    hpd = d.terrain["hours_per_day"]
    if used >= hpd - 1e-9:
        day += 1
        used = 0.0
    target = min(used + hours, hpd)
    while index + 1 < len(path):
        st = step_hours(d, m, path[index], path[index + 1], ftype)
        if used + st > target + 1e-9:
            break
        used += st
        index += 1
    if index + 1 < len(path):
        used = target
    return {"index": index, "day": day, "used": used}
