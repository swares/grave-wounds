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

from .combat import camp_map_size, camp_radius, camp_works, edge_metres, hex_distance, neighbours, party_of, works_labour
from .model import Data
from .weather import flooded, terrain_pct


def _terrain_by_key(d: Data) -> dict:
    return {t["key"]: t for t in d.terrain["terrain"].values()}


def terrain_at(d: Data, m: dict, h) -> dict:
    return _terrain_by_key(d)[m["rows"][h[1]][h[0]]]


def force_types(ftype) -> list:
    """The force types in a force (one) or a column (its party's types)."""
    return [t for t, _ in party_of(0, ftype)]


def passable(d: Data, m: dict, h, ftype, ground: dict | None = None) -> bool:
    """True if this force, or every force in this column, can enter hex h on this ground."""
    t = terrain_at(d, m, h)
    barred = {x for ft in force_types(ftype) for x in d.terrain["forces"][ft].get("cannot_enter", [])}
    return t.get("cost") is not None and t["id"] not in barred and not flooded(d, t["id"], ground)


def column_kmh(d: Data, ftype) -> float:
    """Road speed of a force, or of a column: its slowest force's."""
    return min(d.terrain["forces"][ft]["kmh"] for ft in force_types(ftype))


def hex_weight(d: Data, t: dict, ground: dict | None = None) -> int:
    """A hex's share of a step, in whole numbers: cost x 100, more on mud or snow."""
    return math.floor(t["cost"] * terrain_pct(d, t["id"], ground) + 0.5)


def step_weight(d: Data, m: dict, a, b, ground: dict | None = None) -> int:
    return hex_weight(d, terrain_at(d, m, a), ground) + hex_weight(d, terrain_at(d, m, b), ground)


def step_hours(d: Data, m: dict, a, b, ftype, ground: dict | None = None, speed: int = 100) -> float:
    """Hours to cross from a to b. ftype: a force type or a column's party. speed: % of the
    road speed (fatigue; for a column, its most tired force's)."""
    return step_weight(d, m, a, b, ground) / 200 * m["hex_km"] / (column_kmh(d, ftype) * speed / 100)


def _trace(prev: dict, start, goal) -> list:
    path, h = [], tuple(goal)
    while h != tuple(start):
        path.append(list(h))
        h = prev[h]
    path.append(list(start))
    return path[::-1]


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
    seq, done = [1], set()

    def relax(h, dist, n):
        if not passable(d, m, n, ftype, ground):
            return
        nd = dist + step_weight(d, m, list(h), n, ground)
        t = tuple(n)
        if nd >= best.get(t, float("inf")):
            return
        best[t] = nd
        prev[t] = h
        heapq.heappush(heap, (nd, seq[0], t))
        seq[0] += 1

    while heap:
        dist, _, h = heapq.heappop(heap)
        if h in done:
            continue
        done.add(h)
        if list(h) == goal:
            break
        for n in neighbours(list(h), cols, rows):
            relax(h, dist, n)
    return _trace(prev, start, goal) if tuple(goal) in prev else None


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

def near_woods(d: Data, m: dict, h) -> bool:
    """True if the hex or one next to it is forest (timber to hand)."""
    cols, rows = len(m["rows"][0]), len(m["rows"])
    return any(terrain_at(d, m, x)["id"] == "forest" for x in [list(h)] + neighbours(list(h), cols, rows))


def camp_perimeter(d: Data, men: int, ftype: str) -> float:
    """Metres round a camp for this many men: the outer sides of its ring of battle-map hexes."""
    return (12 * camp_radius(d, men, ftype) + 6) * edge_metres(d)


def camp_hours(d: Data, m: dict, h, kind: str, men: int, ftype: str, tools: bool) -> dict:
    """How long this force takes to make this kind of camp here. {hours, labour, perimeter,
    woods} or {error} if it cannot (no tools, or quartering away from houses). The labour is
    that of the works the battle map lays out for this camp (gravewounds.combat.camp_works),
    with hauled timber unless there is forest at hand."""
    W = d.works
    c = W["camps"][kind]
    t = terrain_at(d, m, h)
    if c.get("terrain") and t["id"] not in c["terrain"]:
        return {"error": f"needs a {' or '.join(d.terrain['terrain'][x]['name'].lower() for x in c['terrain'])}"}
    if c.get("tools") and not tools:
        return {"error": "needs tools (spades and axes)"}
    woods = near_woods(d, m, h)
    labour = 0.0
    if c.get("layout"):
        n = camp_map_size(d, kind, men, ftype)
        labour = works_labour(d, camp_works(d, kind, men, ftype, n, n)["works"], not woods)
    hours = c["hours"] + labour / (men * W["work_share"])
    return {"hours": hours, "labour": labour, "perimeter": camp_perimeter(d, men, ftype), "woods": woods}


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


def camp_worked(d: Data, start: dict, day: int, used: float, hpd_list: list | None = None) -> float:
    """Hours of camp work from start {day, used} until (day, used). Work uses each day's
    marching hours and then evening_hours, as in camp_done. hpd_list: marching hours of the
    start day, the day after and so on."""
    ev, t = d.works["evening_hours"], 0.0
    for k in range(start["day"], day + 1):
        cap = _hpd(d, hpd_list, k - start["day"]) + ev
        begin = start["used"] if k == start["day"] else 0.0
        end = used if k == day else cap
        t += max(0.0, min(end, cap) - begin)
    return t


def camp_labour_done(d: Data, camp: dict, day: int, used: float, hpd_list: list | None = None) -> float:
    """Man-hours of the camp's works done by (day, used). camp: {start, setup (hours before the
    works begin), rate (man-hours an hour), labour (all of it)}. A camp without a start is done."""
    if not camp.get("start"):
        return camp.get("labour", 0)
    worked = camp_worked(d, camp["start"], day, used, hpd_list)
    return min(camp["labour"], max(0.0, worked - camp["setup"]) * camp["rate"])


# ---------- who fights ----------

def _camped(o: dict) -> bool:
    c = o.get("camp")
    return bool(c) and list(c["hex"]) == list(o["pos"])


def _arrived(o: dict) -> tuple:
    """When the force got where it is: when it began its camp there, if it has one (it was
    there while it dug), else its clock."""
    c = o.get("camp")
    if _camped(o) and c.get("from"):
        return c["from"]["day"], c["from"]["used"]
    return o["day"], o["used"]


def fight_plan(d: Data, forces: list, sel, wait: bool = True) -> dict:
    """Who fights if force `sel` (an id) sets up a fight. Forces: [{id, side, pos, camp, day,
    used}], camp {kind, hex, from?}. An enemy force must have marched to within `fight_within` hexes. If `sel` is not
    camped, the fight is at a camp within reach: a friendly force's first (it defends, and
    `sel` with it), else an enemy's (the enemy defends). The defender fights everyone of
    another side within reach of it. With `wait`, the fight starts when the defender's clock
    and every attacker's arrival are past (its camp is finished); without, as soon as the
    defender and every attacker have arrived. `early`: attacking now is sooner than waiting. Forces of the defender's side within reach join the
    defence if they had arrived by then. A camped force arrived when it began its camp
    (camp["from"]: {day, used}); any other force, at its clock.
    {defender, allies, attackers (ids, nearest first), late (allies not there yet), day, used,
    early};
    attackers is empty if no enemy is near."""
    reach = d.terrain["fight_within"]
    f = next(o for o in forces if o["id"] == sel)

    def near(x, same_side, camped_only=False):
        out = [(hex_distance(o["pos"], x["pos"]), i, o) for i, o in enumerate(forces)
               if o is not x and (o["side"] == x["side"]) == same_side
               and hex_distance(o["pos"], x["pos"]) <= reach and (_camped(o) or not camped_only)]
        return [o for _, _, o in sorted(out, key=lambda t: (t[0], t[1]))]
    defender = f
    if not _camped(f):                       # fight from a camp within reach: our own side's first
        camps = near(f, True, True) or near(f, False, True)
        if camps:
            defender = camps[0]
    attackers = near(defender, False)
    now = max([_arrived(defender)] + [_arrived(o) for o in attackers])
    ready = max((defender["day"], defender["used"]), now)
    day, used = ready if wait else now
    friends = near(defender, True)
    allies = [o["id"] for o in friends if _arrived(o) <= (day, used)]
    late = [o["id"] for o in friends if _arrived(o) > (day, used)]
    return {"defender": defender["id"], "allies": allies, "attackers": [o["id"] for o in attackers],
            "late": late, "day": day, "used": used, "early": now < ready}
