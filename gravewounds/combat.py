"""Fighting while wounded: penalties from a fighter's wounds, the optional attack roll,
severity from the margin of success, the graze, the stop check and team morale.
Mirrored exactly by the web roller."""
from __future__ import annotations

import heapq
import math

from .model import Data


def penalties(d: Data, wounds: list[dict], blood_frac: float = 1.0, hand: str = "R",
              state: str | None = None, fatigue: int = 0) -> dict:
    """wounds: [{loc, fx}] where fx is a composed wound (pain, impair). hand: 'R' or 'L'.
    state: a stop-check result in force (defend_only, stunned, out) or None.
    fatigue: the fighter's fatigue level (weather.yaml fatigue.levels)."""
    C = d.wounds["combat"]
    T = d.wounds["tracking"]
    attack = defence = 0
    notes, flags = [], set()

    pain = min(sum(w["fx"]["pain"] for w in wounds), T["pain_cap"])
    if pain:
        attack += pain * C["pain_step"]
        defence += pain * C["pain_step"]
        notes.append(f"pain -{pain * C['pain_step']}%")

    for th in sorted(T["thresholds"], key=lambda t: t["at"]):
        if blood_frac <= th["at"]:
            if th.get("incapacitated"):
                flags.add("incapacitated")
            p = th.get("penalty", 0)
            attack += p
            defence += p
            if th.get("down"):
                flags.add("down")
            if p:
                notes.append(f"blood loss -{p}%")
            break

    seen = set()
    for w in wounds:
        loc = d.loc[w["loc"]]
        for imp in w["fx"].get("impair", []):
            rule = C["impair"].get(imp, {})
            if "weapon_arm" in rule or "shield_arm" in rule:
                arm = "shield_arm" if loc["zone"] == "arms" and loc["side"] in ("L", "R") and loc["side"] != hand else "weapon_arm"
                key, eff = (imp, arm), rule.get(arm, {})
            else:
                key, eff = (imp, None), rule
            if key in seen:
                continue
            seen.add(key)
            a, df = eff.get("attack", 0), eff.get("defence", 0)
            attack += a
            defence += df
            for f in ("down", "off_hand", "no_shield", "incapacitated"):
                if eff.get(f):
                    flags.add(f)
            if a or df:
                where = f" ({key[1].replace('_', ' ')})" if key[1] else ""
                notes.append(f"{imp.replace('_', ' ')}{where}" + (f" atk -{a}%" if a else "") + (f" def -{df}%" if df else ""))
    if "off_hand" in flags and any(k == ("grip", "shield_arm") or k == ("hand_useless", "shield_arm") or k == ("arm_useless", "shield_arm") for k in seen):
        flags.add("cannot_wield")
    if fatigue and d.weather:
        lv = d.weather["fatigue"]["levels"][fatigue]
        if lv["penalty"]:
            attack += lv["penalty"]
            defence += lv["penalty"]
            notes.append(f"{lv['name'].lower()} -{lv['penalty']}%")
    if state:
        rule = C["states"][state]
        flags.add(state)
        if rule.get("defence"):
            defence += rule["defence"]
            notes.append(f"{rule['name'].lower()} def -{rule['defence']}%")
    return {"attack": min(attack, C["cap"]), "defence": min(defence, C["cap"]),
            "flags": sorted(flags), "notes": notes}


def auto_situations(d: Data, att: dict | None, dfn: dict | None) -> list[str]:
    A = d.wounds["combat"]["auto_situations"]
    out = []
    if dfn and "down" in dfn["flags"]:
        out.append(A["defender_down"])
    if dfn and "no_shield" in dfn["flags"]:
        out.append(A["defender_no_shield"])
    if att and "down" in att["flags"]:
        out.append(A["attacker_down"])
    return out


def margin_severity(d: Data, margin: int, critical: bool, weapon_id: str, zone: str) -> str:
    if critical:
        return "critical"
    bands = d.wounds["combat"]["margin_bands"]
    b = bands["default"]
    if (d.weapons.get(weapon_id) or {}).get("threat") and "ballistic" in bands:
        b = next(x for x in bands["ballistic"] if zone in x["zones"])
    if margin >= b["critical"]:
        return "critical"
    if margin >= b["serious"]:
        return "serious"
    return "light"


def attack_roll(d: Data, attack: int, roll: int, penalty: int = 0) -> dict:
    eff = max(0, attack - penalty)
    crit_at = math.floor(eff * d.wounds["combat"]["critical_fraction"])
    hit = roll <= eff
    return {"effective": eff, "roll": roll, "hit": hit, "critical": hit and roll <= crit_at,
            "margin": eff - roll if hit else None}


def defence_roll(defence: int, roll: int, penalty: int = 0) -> dict:
    eff = max(0, defence - penalty)
    return {"effective": eff, "roll": roll, "defended": roll <= eff}


def graze(fx: dict) -> dict:
    """A grazing hit: the rolled wound with bleed and pain one step lower and no stop check."""
    g = dict(fx)
    g["bleed"] = max(0, fx["bleed"] - 1)
    g["pain"] = max(0, fx["pain"] - 1)
    g["shock"] = False
    return g


def is_graze(d: Data, margin: int | None, critical: bool) -> bool:
    return margin is not None and not critical and margin <= d.wounds["combat"]["graze_margin"]


def stop_target(d: Data, nerve: int, severity: str, pain_steps: int, blood_frac: float = 1.0) -> int:
    """Number to roll at or under on d100 for a stop check (may be 0 or less)."""
    C, T = d.wounds["combat"], d.wounds["tracking"]
    target = nerve - min(pain_steps, T["pain_cap"]) * C["pain_step"]
    th = next((t for t in sorted(T["thresholds"], key=lambda t: t["at"]) if blood_frac <= t["at"]), None)
    if th:
        target -= th.get("penalty", 0)
    if severity == "critical":
        target -= C["stop_check"]["critical_penalty"]
    return target


def stop_check(d: Data, nerve: int, severity: str, pain_steps: int, roll: int, blood_frac: float = 1.0,
               shock: bool = True) -> dict | None:
    """Stop check after a wound. None if the wound does not call for one (not serious or
    critical, or no `shock` flag). pain_steps: the fighter's total pain after the wound.
    Returns the target, the roll, whether he fights on, and on a failure the state and how
    many rounds it lasts (None: until cleared)."""
    SC = d.wounds["combat"]["stop_check"]
    if severity not in SC["severities"] or not shock:
        return None
    target = stop_target(d, nerve, severity, pain_steps, blood_frac)
    if roll <= target:
        return {"target": target, "roll": roll, "passed": True, "fail_by": 0, "state": None, "rounds": None}
    fail_by = roll - target
    res = next(r for r in SC["results"] if "upto" not in r or fail_by <= r["upto"])
    return {"target": target, "roll": roll, "passed": False, "fail_by": fail_by,
            "state": res["state"], "rounds": res.get("rounds")}


def pain_check(d: Data, nerve: int, pain_steps: int, roll: int, blood_frac: float = 1.0) -> dict | None:
    """End-of-round stop check for pain above the cap; None if pain is at or under it."""
    if pain_steps <= d.wounds["tracking"]["pain_cap"]:
        return None
    return stop_check(d, nerve, d.wounds["combat"]["stop_check"]["pain_round_as"], pain_steps, roll, blood_frac)


def morale_check(d: Data, fighters: list[dict], roll: int) -> dict | None:
    """Team morale at the end of a round. fighters: one side's [{nerve, down, leader}].
    None if fewer than the trigger share are down (or no one is left up)."""
    M = d.wounds["combat"]["morale"]
    n = len(fighters)
    down = sum(1 for f in fighters if f["down"])
    up = [f for f in fighters if not f["down"]]
    if not n or not up or down / n < M["trigger"]:
        return None
    leaders_up = [f for f in up if f.get("leader")]
    base = max(f["nerve"] for f in (leaders_up or up))
    target = base
    if leaders_up:
        target += M["leader_present"]
    if any(f.get("leader") and f["down"] for f in fighters):
        target -= M["leader_down"]
    if down / n >= M["heavy"]:
        target -= M["heavy_losses"]
    return {"target": target, "roll": roll, "down": down, "of": n, "broken": roll > target}


# ---------- battle map: hexes, movement, reach and range ----------
# Hexes are [col, row] on a pointy-top grid with odd rows shifted right.

def _cube(h) -> tuple[int, int, int]:
    c, r = h
    q = c - (r - (r & 1)) // 2
    return q, r, -q - r


def hex_distance(a, b) -> int:
    (q1, r1, s1), (q2, r2, s2) = _cube(a), _cube(b)
    return max(abs(q1 - q2), abs(r1 - r2), abs(s1 - s2))


_NEIGHBOURS = (((1, 0), (0, -1), (-1, -1), (-1, 0), (-1, 1), (0, 1)),   # even rows
               ((1, 0), (1, -1), (0, -1), (-1, 0), (0, 1), (1, 1)))     # odd rows


def neighbours(h, cols: int, rows: int) -> list[list[int]]:
    c, r = h
    out = []
    for dc, dr in _NEIGHBOURS[r & 1]:
        n = [c + dc, r + dr]
        if 0 <= n[0] < cols and 0 <= n[1] < rows:
            out.append(n)
    return out


def move_allowance(d: Data, wounds: list[dict], state: str | None = None) -> dict:
    """How far a fighter can go this turn: {advance, run} in hexes (run 0: he cannot run).
    wounds: [{fx}] as for penalties(). A fighter who is down or incapacitated gets no turn."""
    M = d.wounds["combat"]["move"]
    if state in M["no_move_states"]:
        return {"advance": 0, "run": 0}
    imp = {i for w in wounds for i in w["fx"].get("impair", [])}
    if imp & set(M["crawl_by"]):
        return {"advance": M["crawl"], "run": 0}
    adv, run = M["advance"], M["run"]
    if imp & set(M["halved_by"]):
        adv, run = adv // 2, run // 2
    if imp & set(M["no_run_by"]):
        run = 0
    return {"advance": adv, "run": run}


def reachable(start, steps: int, cols: int, rows: int, enemies, friends) -> dict:
    """Hexes a fighter can end on within `steps` hexes: {(col, row): cost}. He may pass
    through friends but not stop on them, and cannot enter an enemy's hex. The start is
    included at cost 0."""
    blocked = {tuple(e) for e in enemies}
    friendly = {tuple(f) for f in friends}
    best = {tuple(start): 0}
    frontier = [tuple(start)]
    for cost in range(1, steps + 1):
        nxt = []
        for h in frontier:
            for n in neighbours(h, cols, rows):
                t = tuple(n)
                if t in blocked or t in best:
                    continue
                best[t] = cost
                nxt.append(t)
        frontier = nxt
    return {h: c for h, c in best.items() if h not in friendly or c == 0}


def weapon_reach(d: Data, wid: str, dist: int) -> dict | None:
    """Can this weapon strike at `dist` hexes? None if not; else {band, penalty}, the
    attack penalty in %. Off-map weapons are not limited by the map."""
    w = d.weapons[wid]
    if w.get("off_map"):
        return {"band": "any", "penalty": 0}
    if dist < 1:
        return None
    if "reach" in w:
        return {"band": "reach", "penalty": 0} if dist <= w["reach"] else None
    for edge, b in zip(w["range"], d.wounds["combat"]["range"]):
        if dist <= edge:
            return {"band": b["band"], "penalty": b["penalty"]}
    return None


def free_attackers(d: Data, start, end, steps: int, enemies: list[dict]) -> list:
    """Enemies who get a free attack on a fighter leaving contact. enemies: [{id, pos,
    able}]; returns their ids, in the order given."""
    if steps <= d.wounds["combat"]["move"]["careful_step"]:
        return []
    return [e["id"] for e in enemies
            if e["able"] and hex_distance(start, e["pos"]) == 1 and hex_distance(end, e["pos"]) != 1]


# ---------- works on the battle map ----------
# works = {"edges": {edge_key: [item, ...]}, "hexes": {hex_key: item}}; an item is
# {"type", "progress" (man-rounds of breaching done), "open" and "inside" (gates: the hex
# key of the side it is barred from), "high" (hex key of the high, inner side, for banks,
# ditches and walls)}.

def hkey(h) -> str:
    return f"{h[0]},{h[1]}"


def edge_key(a, b) -> str:
    x, y = sorted([list(a), list(b)], key=lambda h: (h[1], h[0]))
    return hkey(x) + "|" + hkey(y)


def _spec(d: Data, kind: str, item: dict) -> dict:
    return d.works["edge_works" if kind == "edge" else "hex_works"][item["type"]]


def intact(d: Data, kind: str, item: dict) -> bool:
    b = _spec(d, kind, item).get("breach")
    return not (b and item.get("progress", 0) >= b)


def _edge_items(d: Data, works, a, b) -> list:
    """Intact items on the edge, leaving out open gates."""
    if not works:
        return []
    out = []
    for it in works.get("edges", {}).get(edge_key(a, b), []):
        if not intact(d, "edge", it):
            continue
        if _spec(d, "edge", it).get("gate") and it.get("open"):
            continue
        out.append(it)
    return out


def _hex_item(d: Data, works, h):
    it = (works or {}).get("hexes", {}).get(hkey(h))
    return it if it and intact(d, "hex", it) else None


def step_cost(d: Data, works, a, b) -> int | None:
    """Movement to step from hex a to the next hex b: 1, plus crossing the works on the
    edge and entering the works in b. None if a work stops him."""
    cost = 1
    for it in _edge_items(d, works, a, b):
        s = _spec(d, "edge", it)
        c = None if s.get("gate") else s.get("cross")      # open gates are already left out
        if c is None:
            return None
        cost += c
    it = _hex_item(d, works, b)
    if it:
        e = _spec(d, "hex", it).get("enter")
        if e is None:
            return None
        cost += e
    return cost


def reachable_works(d: Data, start, steps: int, cols: int, rows: int, enemies, friends, works, extra: int = 0) -> dict:
    """Like reachable(), but each step costs step_cost() (works slow or stop him), plus
    `extra` for every hex (deep mud or snow)."""
    blocked = {tuple(e) for e in enemies}
    friendly = {tuple(f) for f in friends}
    best = {tuple(start): 0}
    heap = [(0, 0, tuple(start))]
    seq, done = 1, set()
    while heap:
        cost, _, h = heapq.heappop(heap)
        if h in done:
            continue
        done.add(h)
        for n in neighbours(list(h), cols, rows):
            t = tuple(n)
            if t in blocked:
                continue
            sc = step_cost(d, works, list(h), n)
            if sc is not None:
                sc += extra
            if sc is None or cost + sc > steps:
                continue
            if cost + sc < best.get(t, steps + 1):
                best[t] = cost + sc
                heapq.heappush(heap, (cost + sc, seq, t))
                seq += 1
    return {h: c for h, c in best.items() if h not in friendly or c == 0}


def facing(target, attacker, cols: int, rows: int) -> list:
    """The target's neighbours nearest the attacker: what lies between them."""
    ns = neighbours(list(target), cols, rows)
    if not ns:
        return []
    best = min(hex_distance(n, attacker) for n in ns)
    return [n for n in ns if hex_distance(n, attacker) == best]


def missile_cover(d: Data, works, attacker, target, cols: int, rows: int) -> dict:
    """Cover a target has against a missile attack: {cover (% off the attack), work}."""
    best, what = 0, None
    it = _hex_item(d, works, target)
    if it and _spec(d, "hex", it).get("cover_here", 0) > best:
        best, what = _spec(d, "hex", it)["cover_here"], it["type"]
    for n in facing(target, attacker, cols, rows):
        for e in _edge_items(d, works, target, n):
            s = _spec(d, "edge", e)
            if s.get("cover_side", "both") == "high" and e.get("high") != hkey(target):
                continue
            if s.get("cover", 0) > best:
                best, what = s["cover"], e["type"]
        if list(n) != list(attacker):
            it = _hex_item(d, works, n)
            if it and _spec(d, "hex", it).get("cover_behind", 0) > best:
                best, what = _spec(d, "hex", it)["cover_behind"], it["type"]
    return {"cover": best, "work": what}


def melee_across(d: Data, works, attacker, target, reach: int, cols: int, rows: int) -> dict:
    """A close-combat attack across works: {blocked (only reach 2+ strikes over it),
    penalty (% off for attacking up at a man on the high side), work}."""
    cands = [list(attacker)] if hex_distance(attacker, target) == 1 else facing(target, attacker, cols, rows)
    blocked, penalty, what = False, 0, None
    for n in cands:
        pen = 0
        for e in _edge_items(d, works, target, n):
            s = _spec(d, "edge", e)
            if s.get("blocks_melee") and reach < 2 and hex_distance(attacker, target) == 1:
                blocked, what = True, e["type"]
            if s.get("height") and e.get("high") == hkey(target):
                pen += s["height"]
                what = what or e["type"]
        penalty = max(penalty, pen)
    return {"blocked": blocked, "penalty": penalty, "work": what}


def camp_radius(d: Data, men: int, ftype: str) -> int:
    """Hexes from the centre to the edge of a camp for this many men (2 m hexes)."""
    W = d.works
    area = max(W["camp_area_min"], men * W["camp_area"][ftype])
    n = area / (3 ** 0.5 / 2 * 4)
    r = 0
    while 3 * r * (r + 1) + 1 < n:
        r += 1
    return max(r, 1)


def camp_works(d: Data, kind: str, men: int, ftype: str, cols: int, rows: int) -> dict:
    """Battle-map layout for a camp in the middle of the map: {centre, radius, fits, works}.
    The camp is cut down to fit the map if it must (fits false)."""
    layout = d.works["camps"][kind].get("layout")
    centre = [cols // 2, rows // 2]
    r = camp_radius(d, men, ftype)
    extra = 2 if layout == "fortified" else 1
    fits = True

    def inside(rr):
        cnt = sum(1 for y in range(rows) for x in range(cols) if hex_distance(centre, [x, y]) <= rr)
        return cnt == 3 * rr * (rr + 1) + 1
    while r > 1 and not inside(r + extra):
        r -= 1
        fits = False
    works = {"edges": {}, "hexes": {}}
    if not layout:
        return {"centre": centre, "radius": r, "fits": fits, "works": works}
    gate_in, gate_out = [centre[0] + r, centre[1]], [centre[0] + r + 1, centre[1]]
    ring = [[x, y] for y in range(rows) for x in range(cols) if hex_distance(centre, [x, y]) == r]
    outer = [[x, y] for y in range(rows) for x in range(cols) if hex_distance(centre, [x, y]) == r + 1]
    if layout == "stakes":
        for h in outer:
            if h != gate_out:
                works["hexes"][hkey(h)] = {"type": "stakes", "progress": 0}
    elif layout == "fortified":
        for h in ring:
            for n in neighbours(h, cols, rows):
                if hex_distance(centre, n) == r + 1:
                    k = edge_key(h, n)
                    if h == gate_in and n == gate_out:
                        works["edges"][k] = [{"type": "gate", "progress": 0, "open": False, "inside": hkey(h)}]
                    else:
                        works["edges"][k] = [{"type": "bank", "progress": 0, "high": hkey(h)},
                                             {"type": "palisade", "progress": 0}]
        for h in outer:
            if h == gate_out:
                continue
            for n in neighbours(h, cols, rows):
                if hex_distance(centre, n) == r + 2:
                    works["edges"][edge_key(h, n)] = [{"type": "ditch", "progress": 0, "high": hkey(h)}]
    return {"centre": centre, "radius": r, "fits": fits, "works": works}


# ---------- weather in battle ----------

def deep_going(d: Data, ground: dict | None) -> int:
    """Extra movement per hex on the battle map for deep mud or snow."""
    if not ground or not d.weather:
        return 0
    deep = d.weather["ground"]["deep"]
    return d.weather["battle"]["deep_step"] if ground.get("mud", 0) >= deep or ground.get("snow", 0) >= deep else 0


def weather_attack(d: Data, weather: dict | None, wid: str, dist: int) -> dict:
    """What the weather does to a missile attack at `dist` hexes: {blocked (a reason, or
    None), penalty (% off), misfire (% chance), notes}. Close combat is not affected."""
    out = {"blocked": None, "penalty": 0, "misfire": 0, "notes": []}
    w = d.weapons[wid]
    if not weather or not d.weather or "range" not in w:
        return out
    WX = d.weather
    cond = WX["conditions"][weather["cond"]]
    vis = cond.get("visibility")
    if vis is not None and dist > vis:
        out["blocked"] = f"{cond['name']}: no one can be seen to aim at beyond {vis} hexes ({vis * 2} m)."
        return out
    wind = next(x for x in WX["winds"] if x["id"] == weather["wind"])
    if w.get("string"):
        p = WX["battle"]["string_wet"][cond["wet"]]
        if p:
            out["penalty"] += p
            out["notes"].append(f"wet string -{p}%")
    firearm = bool(w.get("ignition"))
    wp = wind["firearm"] if firearm else wind["missile"]
    if wp:
        out["penalty"] += wp
        out["notes"].append(f"{wind['name'].lower()} -{wp}%")
    if firearm:
        out["misfire"] = WX["battle"]["misfire"][w["ignition"]][cond["wet"]]
    return out
