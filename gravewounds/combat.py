"""Fighting while wounded: penalties from a fighter's wounds, the optional attack roll,
severity from the margin of success, the graze, the stop check and team morale.
Mirrored exactly by the web roller."""
from __future__ import annotations

import heapq
import math

from .model import Data


def penalties(d: Data, wounds: list[dict], blood_frac: float = 1.0, hand: str = "R",
              state: str | None = None, fatigue: int = 0, sick: str | None = None) -> dict:
    """wounds: [{loc, fx}] where fx is a composed wound (pain, impair). hand: 'R' or 'L'.
    state: a stop-check result in force (defend_only, stunned, out) or None.
    fatigue: the fighter's fatigue level (weather.yaml fatigue.levels).
    sick: a named character's worst step of sickness (disease.yaml in_fight), or None."""
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
    if any(k[0] in C.get("one_arm", ()) for k in seen):   # an arm hurt: no two-handed weapon
        flags.add("one_arm")
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
    attack, defence = _sick_penalties(d, sick, attack, defence, flags, notes)
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


def first_aid(d: Data, how: str, fx: dict, limb: bool, leechcraft: int | None = None, roll: int | None = None) -> dict:
    """A treatment (bind, tourniquet, cauterise) on a wound's {bleed, pain}: {done, bleed,
    pain}. leechcraft: the best on his side (None: no sheets there, unrolled, as before);
    roll: d100 against it. Success binds `bind` steps and cauterises without more pain."""
    bleed, pain = fx["bleed"], fx["pain"]
    if how == "tourniquet" and not limb:
        return {"done": False, "bleed": bleed, "pain": pain}
    good = leechcraft is not None
    if good and roll > leechcraft:
        return {"done": False, "bleed": bleed, "pain": pain}
    if how == "bind":
        bleed = max(0, bleed - (d.wounds["combat"]["first_aid"]["bind"] if good else 1))
    elif how == "tourniquet":
        bleed = 0
    elif how == "cauterise":
        bleed, pain = 0, pain if good else min(3, pain + 1)
    return {"done": True, "bleed": bleed, "pain": pain}


def initiative(d: Data, agility: int | None, roll: int) -> int:
    """Rolled initiative: the die (roll, 1..die) + Agility / agi_per (50 without a sheet)."""
    I = d.wounds["combat"]["characteristics"]["initiative"]
    return roll + (50 if agility is None else agility) // I["agi_per"]


def lethality(d: Data, name: str | None = None) -> dict:
    """A lethality preset (wounds.yaml lethality): the named one, else the default."""
    L = d.wounds["lethality"]
    return {"id": name or L["default"], **L["presets"][name or L["default"]]}


def blood_pool(d: Data, endurance: int | None, preset: dict | None = None) -> int:
    """A fighter's Blood pool: tracking.blood_pool + (Endurance - 50) / per, rounded down; a
    player character's times his lethality preset's blood (preset: lethality(); None for anyone else)."""
    per = d.wounds["combat"]["characteristics"]["blood"]["per"]
    pool = d.wounds["tracking"]["blood_pool"] + ((50 if endurance is None else endurance) - 50) // per
    return int(pool * float(preset["blood"])) if preset else pool


def pc_stop(preset: dict | None, nerve: int, severity: str) -> int | None:
    """A player character's Nerve for the stop check under his lethality preset, or None if
    the preset spares him the check for this severity (stop_critical_only). Anyone else: nerve."""
    if not preset:
        return nerve
    if preset["stop_critical_only"] and severity != "critical":
        return None
    return nerve + preset["stop_bonus"]


def kit_load(d: Data, kit: str | None) -> str:
    return d.wounds["combat"]["characteristics"]["toil"]["load"].get(kit or "none", "light")


def toil_blows(d: Data, kit: str | None, strength: int | None) -> int:
    """Hand-to-hand exchanges per fatigue step: the kit's load, scaled by Strength / 50 (rounded)."""
    b = d.wounds["combat"]["characteristics"]["toil"]["blows"][kit_load(d, kit)]
    return max(1, (b * (50 if strength is None else strength) + 25) // 50)


def toil(d: Data, fatigue: int, toil_count: int, kit: str | None, strength: int | None) -> tuple[int, int]:
    """One more hand-to-hand exchange: (fatigue, toil count) after it."""
    T, n = d.wounds["combat"]["characteristics"]["toil"], toil_count + 1
    need = toil_blows(d, kit, strength)
    if n < need:
        return fatigue, n
    if fatigue >= T["worst"]:
        return fatigue, n - need
    return fatigue + 1, n - need


def morale_check(d: Data, fighters: list[dict], roll: int) -> dict | None:
    """Team morale at the end of a round. fighters: one side's [{nerve, down, leader, pres}]
    (pres: Presence, 50 without a sheet). None if fewer than the trigger share are down (or
    no one is left up)."""
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
        per = d.wounds["combat"]["characteristics"]["presence"]["per"]
        target += M["leader_present"] + (max(f.get("pres", 50) for f in leaders_up) - 50) // per
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


def _cube_round(x: float, y: float, z: float) -> list:
    """The offset hex nearest a point in cube coordinates."""
    rx, ry, rz = math.floor(x + 0.5), math.floor(y + 0.5), math.floor(z + 0.5)
    dx, dy, dz = abs(rx - x), abs(ry - y), abs(rz - z)
    if dx > dy and dx > dz:
        rx = -ry - rz
    elif dy > dz:
        ry = -rx - rz
    return [rx + (ry - (ry & 1)) // 2, ry]


def _ray_point(s, c, k: int, i: int) -> list:
    """Step i of the line from cube s toward cube c, k steps apart (nudged off ties)."""
    return _cube_round(s[0] + (c[0] - s[0]) * i / k + 1e-6, s[1] + (c[1] - s[1]) * i / k + 2e-6, s[2] + (c[2] - s[2]) * i / k - 3e-6)


def ray(a, b, n: int) -> list:
    """The hexes on the line from hex a through hex b, n steps (b is step hdist(a, b))."""
    s, c, k = _cube(a), _cube(b), hex_distance(a, b)
    if k == 0:
        return [list(a)]
    return [_ray_point(s, c, k, i) for i in range(n + 1)]


def ray_at(a, b, i: int) -> list:
    """Step i of ray(a, b, ...): the one hex of the line i hexes from a."""
    k = hex_distance(a, b)
    return list(a) if k == 0 else _ray_point(_cube(a), _cube(b), k, i)


def neighbours(h, cols: int, rows: int) -> list[list[int]]:
    c, r = h
    out = []
    for dc, dr in _NEIGHBOURS[r & 1]:
        n = [c + dc, r + dr]
        if 0 <= n[0] < cols and 0 <= n[1] < rows:
            out.append(n)
    return out


def _sick_penalties(d: Data, sick: str | None, attack: int, defence: int, flags: set, notes: list) -> tuple:
    """Sickness in a fight (disease.yaml in_fight): its penalty, and defend only or out."""
    rule = (d.disease.get("in_fight") or {}).get(sick or "", {})
    if rule.get("penalty"):
        attack += rule["penalty"]
        defence += rule["penalty"]
        notes.append(f"sick ({sick}) -{rule['penalty']}%")
    if rule.get("defend_only"):
        flags.add("defend_only")
    if rule.get("out"):
        flags.add("out")
    return attack, defence


def move_allowance(d: Data, wounds: list[dict], state: str | None = None, sick: str | None = None) -> dict:
    """How far a fighter can go this turn: {advance, run} in hexes (run 0: he cannot run).
    wounds: [{fx}] as for penalties(). A fighter who is down or incapacitated gets no turn.
    sick: a named character's worst step of sickness (disease.yaml in_fight)."""
    M = d.wounds["combat"]["move"]
    rule = (d.disease.get("in_fight") or {}).get(sick or "", {})
    if state in M["no_move_states"] or rule.get("out"):
        return {"advance": 0, "run": 0}
    imp = {i for w in wounds for i in w["fx"].get("impair", [])}
    if imp & set(M["crawl_by"]) or rule.get("crawl"):
        return {"advance": M["crawl"], "run": 0}
    adv, run = M["advance"], M["run"]
    if imp & set(M["halved_by"]):
        adv, run = adv // 2, run // 2
    if imp & set(M["no_run_by"]) or rule.get("no_run"):
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


def _under_sight(ground, frm, to, k: int, i: int, x) -> bool:
    """Whether hex x, i steps along the k-step line from frm to to, lies below the line of sight
    between the two (so a man there is shot over)."""
    return level_at(ground, x) * k < level_at(ground, frm) * (k - i) + level_at(ground, to) * i


def sight_clear(ground, frm, to) -> bool:
    """Whether no higher ground between hexes frm and to rises above the line between them."""
    k = hex_distance(frm, to)
    return all(level_at(ground, x) * k <= level_at(ground, frm) * (k - i) + level_at(ground, to) * i
               for i, x in enumerate(ray(frm, to, k)[1:-1], 1)) if k > 1 else True


def in_the_way(d: Data, wid: str, frm, to, others, ground=None) -> dict:
    """Fighters standing between a shooter at hex frm and his target at hex to on the battle map
    (others: [(id, hex)], not the two of them; men on ground below the line of sight are shot
    over): {men (ids, nearest the shooter first), penalty (% off the shot), stray (% a miss
    strikes the first of them instead; none for bows loosing high over them)}."""
    L, k = d.wounds["combat"]["line_of_fire"], hex_distance(frm, to)
    at = {tuple(h): i for i, h in others}
    line = list(enumerate(ray(frm, to, k)[1:-1], 1)) if k > 1 else []
    men = [at[tuple(x)] for i, x in line if tuple(x) in at and not _under_sight(ground, frm, to, k, i, x)]
    if not men:
        return {"men": [], "penalty": 0, "stray": 0}
    return {"men": men, "penalty": min(L["max"], L["per_man"] * len(men)), "stray": 0 if wid in L["arcing"] else L["stray"]}


def height_effects(d: Data, ground, a, b, melee: bool) -> dict:
    """Fighting from hex a at hex b across height: {situation (the auto situation key, or None),
    penalty (% off a close-combat blow up at a higher man), reach (% on a missile's range shot
    down from higher ground)}."""
    G, diff = d.wounds["combat"]["ground"], level_at(ground, a) - level_at(ground, b)
    out = {"situation": None, "penalty": 0, "reach": 0}
    if diff > 0:
        out["situation"] = "attacker_higher"
        out["reach"] = 0 if melee else G["downhill_reach"] * diff
    elif diff < 0:
        out["situation"] = "defender_higher"
        out["penalty"] = G["uphill"] * min(2, -diff) if melee else 0
    return out


def rising_cost(d: Data, in_cover: bool, risen: int = 0) -> int:
    """Hexes of his move a fighter spends getting up this turn: combat.ground.rise from cover
    (to move, or to strike in close combat; shooting needs none), or what he has already spent."""
    return d.wounds["combat"]["ground"]["rise"] if in_cover else risen


def ground_cover(d: Data, ground, h, taking_cover: bool = False) -> dict:
    """What a man at hex h has against missiles from the ground and from taking cover: {cover
    (%, the better), low (low cover hides his lower body), kind}."""
    g = ground_spec(d, ground, h)
    cover = max(g.get("cover", 0), d.wounds["combat"]["ground"]["take_cover"] if taking_cover else 0)
    return {"cover": cover, "low": bool(g.get("low")) or taking_cover, "kind": ((ground or {}).get("kinds") or {}).get(hkey(h), "open")}


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
    if item.get("out"):                               # a bunker knocked out by assault or shellfire
        return False
    s = _spec(d, kind, item)
    b = s.get("breach") or s.get("charge")            # a wall opened by demolition charges
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


def ground_spec(d: Data, ground, h) -> dict:
    """The battle map's ground at hex h (ground: {kinds: {hex key: kind}, levels: {hex key: n}})."""
    G = d.wounds["combat"]["ground"]["kinds"]
    return G[((ground or {}).get("kinds") or {}).get(hkey(h), "open")]


def level_at(ground, h) -> int:
    """The battle map's height level at hex h (0 if not set)."""
    return ((ground or {}).get("levels") or {}).get(hkey(h), 0)


def ground_step(d: Data, ground, a, b) -> int:
    """Extra movement from hex a into hex b for its ground and for climbing."""
    if not ground:
        return 0
    return ground_spec(d, ground, b)["move"] + d.wounds["combat"]["ground"]["climb"] * max(0, level_at(ground, b) - level_at(ground, a))


def seed_number(text: str) -> int:
    """A repeatable seed from a string (FNV-1a, 32 bits), as the roller's seedNumber."""
    h = 2166136261
    for ch in text.encode("utf-8"):
        h = ((h ^ ch) * 16777619) & 0xFFFFFFFF
    return h


class _Park:
    """Park-Miller minimal standard, as units.SeededDice and the roller's parkMiller."""

    def __init__(self, seed: int):
        self.state = max(1, seed % 2147483647)

    def randint(self, a: int, b: int) -> int:
        self.state = self.state * 16807 % 2147483647
        return a + self.state % (b - a + 1)


GROUND_ORDER = ("marsh", "brush", "rough")     # laid in this order; a hex keeps the first


def _lay_rises(ground: dict, spec: dict, cols: int, rows: int, rng: _Park) -> None:
    for _ in range(spec.get("rises", 0)):
        top_hex = [rng.randint(0, cols - 1), rng.randint(0, rows - 1)]
        top, spread = rng.randint(1, spec["top"]), rng.randint(3, 6)
        for r in range(rows):
            for c in range(cols):
                lv = top - hex_distance([c, r], top_hex) // spread
                k = f"{c},{r}"
                if lv > ground["levels"].get(k, 0):
                    ground["levels"][k] = lv


def _lay_clumps(ground: dict, kind: str, target: int, cols: int, rows: int, rng: _Park) -> None:
    painted, tries = 0, 0
    while painted < target and tries < 4 * cols * rows:
        h, size = [rng.randint(0, cols - 1), rng.randint(0, rows - 1)], rng.randint(3, 12)
        for _ in range(size):
            tries += 1
            k = hkey(h)
            if k not in ground["kinds"]:
                ground["kinds"][k] = kind
                painted += 1
                if painted >= target:
                    return
            nb = neighbours(h, cols, rows)
            h = nb[rng.randint(0, len(nb) - 1)]


def seed_ground(d: Data, terrain: str, cols: int, rows: int, seed: int, clear=None, edges=None) -> dict:
    """A battle map's ground laid out like a travel terrain: {kinds, levels}. clear: (centre,
    radius) of a camp, cleared and levelled to its middle. edges: the neighbouring travel
    hexes (see edge_bands); the sides the map reaches past go in ground["sides"]."""
    seeds = d.wounds["combat"]["ground"]["seed"]
    spec, rng = seeds.get(terrain) or seeds["open"], _Park(seed)
    ground = {"kinds": {}, "levels": {}}
    _lay_rises(ground, spec, cols, rows, rng)
    for kind in GROUND_ORDER:
        _lay_clumps(ground, kind, int(spec.get(kind, 0) * cols * rows + 0.5), cols, rows, rng)
    if edges:
        ground["sides"] = edge_bands(d, ground, terrain, cols, rows, seed, edges)
        through_lines(d, ground, terrain, cols, rows, seed, edges, clear)
    if clear:
        clear_ground(ground, clear[0], clear[1], cols, rows)
    return ground


_S3 = math.sqrt(3) / 2
SIDES = (("east", (1.0, 0.0)), ("north-east", (0.5, -_S3)), ("north-west", (-0.5, -_S3)),
         ("west", (-1.0, 0.0)), ("south-west", (-0.5, _S3)), ("south-east", (0.5, _S3)))   # north is up


def hex_spot(hex_m: float, seed: int) -> list:
    """A repeatable spot inside a travel hex hex_m across (flat to flat), in whole metres from
    its middle, x east and y south."""
    rng, a = _Park(seed), hex_m / 2
    c = int(a / _S3) + 1
    while True:
        p = [rng.randint(-c, c), rng.randint(-c, c)]
        if all(p[0] * u[0] + p[1] * u[1] <= a for _, u in SIDES):
            return p


def _map_xy(hm: float, cols: int, rows: int, c: int, r: int) -> list:
    """Hex (c, r) of the battle map in metres from the map's middle, x east and y south."""
    return [hm * (c + 0.5 * (r & 1)) - hm * (cols - 0.5) / 2, hm * _S3 * r - hm * _S3 * (rows - 1) / 2]


def _side_plans(d: Data, terrain: str, cols: int, rows: int, seed: int, edges: dict) -> dict:
    """For each side with other country beyond it: {terrain, river width and ford, or its layout}."""
    E, rng, plans = d.wounds["combat"]["ground"]["edges"], _Park(seed + 1), {}
    for i, (name, _u) in enumerate(SIDES):
        t = (edges.get("around") or {}).get(name)
        if not t or t == terrain:
            continue
        plan = {"terrain": t}
        if t == "river":
            plan["width"] = rng.randint(*E["river_width"])
            if edges.get("ford"):
                plan["ford"] = [rng.randint(-E["ford_shift"], E["ford_shift"]), rng.randint(*E["ford_width"])]
        elif t != "lake":
            plan["layout"] = seed_ground(d, t, cols, rows, (seed + 7919 * (i + 1)) % 2147483647)
        plans[name] = plan
    return plans


def _set_hex(ground: dict, k: str, kind, level) -> None:
    if kind:
        ground["kinds"][k] = kind
    else:
        ground["kinds"].pop(k, None)
    if level:
        ground["levels"][k] = level
    else:
        ground["levels"].pop(k, None)


def _beyond(plan: dict, pt: list, u, depth: float, spot: list, hm: float, k: str):
    """(kind, level) for a hex depth metres past a side, in the country beyond it."""
    if plan["terrain"] == "lake":
        return "water", 0
    if plan["terrain"] == "river":
        if depth > plan["width"] * hm:
            return None, 0
        f = plan.get("ford")
        if f:
            v = (-u[1], u[0])                        # along the side
            along = pt[0] * v[0] + pt[1] * v[1] - (spot[0] * v[0] + spot[1] * v[1]) - f[0] * hm
            if abs(along) <= f[1] * hm / 2:
                return "marsh", 0
        return "water", 0
    L = plan["layout"]
    return L["kinds"].get(k), L["levels"].get(k, 0)


def _past_side(plans: dict, pt: list, a: float):
    """(side, metres past it, its direction) for the planned side pt lies furthest past, or Nones."""
    best, depth, bu = None, 0.0, None
    for name, u in SIDES:
        if name not in plans:
            continue
        dd = pt[0] * u[0] + pt[1] * u[1] - a
        if dd > depth:
            best, depth, bu = name, dd, u
    return best, depth, bu


def _near_rays(q: list, rays: list, half: float) -> bool:
    """Whether point q (metres from the map's middle) lies within half metres of any ray from the
    middle in the directions rays."""
    for u in rays:
        t = q[0] * u[0] + q[1] * u[1]
        x = q[0] * u[1] - q[1] * u[0]
        off = q[0] * q[0] + q[1] * q[1] if t < 0 else x * x
        if off <= half * half:
            return True
    return False


def _near_placed(q: list, rays: list, half: float) -> bool:
    """_near_rays for rays each with its own start: [(origin, direction)]."""
    return any(_near_rays([q[0] - o[0], q[1] - o[1]], [u], half) for o, u in rays)


def _through_rays(d: Data, terrain: str, around: dict, what: str) -> list:
    """The directions a road or river runs from the map's middle: toward each linked neighbour."""
    T = d.wounds["combat"]["ground"]["through"][what]
    if terrain not in T["hexes"]:
        return []
    return [u for name, u in SIDES if around.get(name) in T["links"]]


def _ray_gap(p: list, origin: list, rays: list) -> float:
    """The least squared distance (square metres) from point p to rays starting at origin."""
    best = None
    for u in rays:
        q = [p[0] - origin[0], p[1] - origin[1]]
        t = q[0] * u[0] + q[1] * u[1]
        x = q[0] * u[1] - q[1] * u[0]
        off = q[0] * q[0] + q[1] * q[1] if t < 0 else x * x
        best = off if best is None or off < best else best
    return best


def bank_normal(d: Data, terrain: str, edges: dict):
    """At a crossing hex, the way from a camp to the river past it (a unit vector, x east and y
    south): toward the attackers (edges["toward"]), or, when they came along the river or from
    nowhere known, either way, fixed by the fight's spot seed. None when no river runs through."""
    rivers = _through_rays(d, terrain, edges.get("around") or {}, "river")
    if not rivers:
        return None
    n, a = (-rivers[0][1], rivers[0][0]), dict(SIDES).get(edges.get("toward"))
    side = n[0] * a[0] + n[1] * a[1] if a else 0
    if abs(side) < 0.25:                         # along the river, or no direction: the fight decides
        sign = 1 if edges.get("spot_seed", 0) & 1 else -1
    else:
        sign = 1 if side > 0 else -1
    return (sign * n[0], sign * n[1])


def _reach(hm: float, cols: int, rows: int, n) -> float:
    """How far the battle map runs from its middle in direction n, to its furthest corner."""
    return hm * (cols - 0.5) / 2 * abs(n[0]) + hm * _S3 * (rows - 1) / 2 * abs(n[1])


def _hex_at(hm: float, cols: int, rows: int, p: list) -> list:
    """The battle-map hex (on the map or off it) nearest point p, metres from the map's middle."""
    rf = (p[1] + hm * _S3 * (rows - 1) / 2) / (hm * _S3)
    qf = (p[0] + hm * (cols - 0.5) / 2) / hm - rf / 2
    return _cube_round(qf, rf, -qf - rf)


def camp_centre(d: Data, terrain: str, edges: dict, cols: int, rows: int, radius: int, outer: int) -> list:
    """Where a camp with works stands at a crossing: the map's middle, moved back from the river
    just enough for the river at its widest and its far bank, keeping 2 hexes of map behind the
    camp's outer works (radius + outer). A camp too big for the map moves back as far as that
    needs, its centre off the map if need be, so the stretch facing the river is shown.
    Elsewhere, the middle."""
    mid = [cols // 2, rows // 2]
    n = bank_normal(d, terrain, edges) if edges else None
    if not n:
        return mid
    G, hm = d.wounds["combat"]["ground"], d.wounds["combat"]["move"]["hex_m"]
    B, e = G["camp_bank"], _reach(hm, cols, rows, n)
    need = (radius + B["gap"] + G["edges"]["river_width"][1] + B["far"]) * hm
    s = max(0.0, need - e)
    if _camp_fits(mid, radius + outer, cols, rows):
        s = min(s, max(0.0, e - (radius + outer + 2) * hm))
    m = _map_xy(hm, cols, rows, mid[0], mid[1])
    return _hex_at(hm, cols, rows, [m[0] - n[0] * s, m[1] - n[1] * s])


def camp_gate(d: Data, terrain: str, edges: dict, cols: int, rows: int, centre, radius: int) -> int:
    """The side (0 east, then anticlockwise as SIDES) a camp at a crossing has its gate on: toward
    where the road nearest the river's way meets the river's near bank, or straight at the river
    when no road goes that way. 0 (east) elsewhere."""
    n = bank_normal(d, terrain, edges) if edges else None
    if not n:
        return 0
    G, hm = d.wounds["combat"]["ground"], d.wounds["combat"]["move"]["hex_m"]
    cxy = _map_xy(hm, cols, rows, centre[0], centre[1])
    roads = _through_rays(d, terrain, edges.get("around") or {}, "road")
    u = max(roads, key=lambda v: v[0] * n[0] + v[1] * n[1], default=None)
    way = list(n)
    if u and u[0] * n[0] + u[1] * n[1] > 0.3:
        bank = cxy[0] * n[0] + cxy[1] * n[1] + (radius + G["camp_bank"]["gap"]) * hm   # the near bank, along n
        t = bank / (u[0] * n[0] + u[1] * n[1])
        way = [u[0] * t - cxy[0], u[1] * t - cxy[1]]
    best, bd = 0, None
    for i, (_name, v) in enumerate(SIDES):
        dd = v[0] * way[0] + v[1] * way[1]
        if bd is None or dd > bd:
            best, bd = i, dd
    return best


def camp_gates(d: Data, terrain: str, edges: dict, cols: int, rows: int, centre, radius: int) -> list:
    """A camp's gate sides, main gate first: the main gate (camp_gate: toward the crossing, or
    east), then one more on each side a road leaves the camp by (roads run from the camp's
    middle), but not the road to the river at a crossing, which leaves by the main gate."""
    main = camp_gate(d, terrain, edges, cols, rows, centre, radius)
    gates = [main]
    roads = _through_rays(d, terrain, (edges or {}).get("around") or {}, "road") if edges else []
    n = bank_normal(d, terrain, edges) if edges else None
    for i, (_name, u) in enumerate(SIDES):
        if u not in roads or i in gates:
            continue
        if n and u[0] * n[0] + u[1] * n[1] > 0.3:
            continue
        gates.append(i)
    return gates


def _camp_bank(d: Data, size: tuple, clear, rivers: list, width: int, n) -> tuple:
    """Where the river runs when the defenders camp with works at the crossing: (the point its
    rays start from, its width in hexes). It passes the camp in direction n (bank_normal), gap
    hexes clear of the camp's edge."""
    G, hm = d.wounds["combat"]["ground"], d.wounds["combat"]["move"]["hex_m"]
    B, cols, rows = G["camp_bank"], size[0], size[1]
    centre, radius = clear[0], clear[1]
    cxy = _map_xy(hm, cols, rows, centre[0], centre[1])
    reach = _reach(hm, cols, rows, n) - (cxy[0] * n[0] + cxy[1] * n[1])
    near = (radius + B["gap"]) * hm
    width = max(G["edges"]["river_width"][0], min(width, int((reach - near) / hm) - B["far"]))
    s, clear_by = near + width * hm / 2, near + width * hm / 2
    for _ in range(400):                         # a bend may swing back toward the camp: move further out
        origin = [cxy[0] + n[0] * s, cxy[1] + n[1] * s]
        if _ray_gap(cxy, origin, rivers) >= clear_by * clear_by:
            break
        s += hm
    return origin, width


def _road_starts(d: Data, terrain: str, edges: dict, size: tuple, roads: list, river: bool, clear) -> list:
    """Each road as (where it starts, its direction): from the map's middle, or with a camp with
    works, from the camp's middle by its gates, the road to the river at a crossing by the main gate."""
    if not (clear and len(clear) > 2):
        return [((0.0, 0.0), u) for u in roads]
    hm, (cols, rows) = d.wounds["combat"]["move"]["hex_m"], size
    mid_xy = _map_xy(hm, cols, rows, clear[0][0], clear[0][1])
    rays = [((mid_xy[0], mid_xy[1]), u) for u in roads]
    if river:
        gate_xy = _map_xy(hm, cols, rows, *ring_walk(clear[0], clear[1] + 1, _gate_list(clear[2])[0])[0])
        n = bank_normal(d, terrain, edges)
        rays = [((gate_xy[0], gate_xy[1]) if u[0] * n[0] + u[1] * n[1] > 0.3 else o, u) for o, u in rays]
    return rays


def through_lines(d: Data, ground: dict, terrain: str, cols: int, rows: int, seed: int, edges: dict, clear=None) -> None:
    """A river and a road through the defenders' own travel hex, drawn through the map's middle
    (the river past the camp, on one bank, when the defenders camp there with works)."""
    G = d.wounds["combat"]["ground"]
    E, hm, around = G["edges"], d.wounds["combat"]["move"]["hex_m"], edges.get("around") or {}
    rivers, roads, rng = _through_rays(d, terrain, around, "river"), _through_rays(d, terrain, around, "road"), _Park(seed + 2)
    river_w = rng.randint(*E["river_width"]) if rivers else 0
    ford_w = rng.randint(*E["ford_width"]) if rivers else 0
    road_w = rng.randint(*G["through"]["road"]["width"]) if roads else 0
    origin = [0.0, 0.0]
    if rivers and clear:
        origin, river_w = _camp_bank(d, (cols, rows), clear, rivers, river_w, bank_normal(d, terrain, edges))
    road_rays = _road_starts(d, terrain, edges, (cols, rows), roads, bool(rivers), clear)
    cross = road_rays or ([((0.0, 0.0), (-rivers[0][1], rivers[0][0])), ((0.0, 0.0), (rivers[0][1], -rivers[0][0]))] if rivers else [])
    plan = {"terrain": terrain, "rivers": rivers, "roads": road_rays, "cross": cross, "origin": origin,
            "river": river_w * hm / 2, "ford": ford_w * hm / 2, "road": road_w * hm / 2}
    for r in range(rows):
        for c in range(cols):
            _through_hex(ground, f"{c},{r}", _map_xy(hm, cols, rows, c, r), plan)


def _through_hex(ground: dict, k: str, q: list, plan: dict) -> None:
    """One hex of through_lines: the river, then the road (by a ford or bridge over the river)."""
    o = plan["origin"]
    if plan["rivers"] and _near_rays([q[0] - o[0], q[1] - o[1]], plan["rivers"], plan["river"]):
        _set_hex(ground, k, "water", 0)
    wet = ground["kinds"].get(k) == "water"
    if wet and plan["terrain"] == "ford" and _near_placed(q, plan["cross"], plan["ford"]):
        _set_hex(ground, k, "marsh", 0)
    elif plan["roads"] and _near_placed(q, plan["roads"], plan["road"]):
        if not wet:
            ground["kinds"][k] = "road"
        elif plan["terrain"] == "bridge":
            _set_hex(ground, k, "bridge", 0)


def edge_bands(d: Data, ground: dict, terrain: str, cols: int, rows: int, seed: int, edges: dict) -> list:
    """Lay the country beyond the defenders' travel hex where the battle map reaches past its
    sides. edges: {around: {side: travel terrain}, hex_m: the travel hex across, spot_seed,
    ford: a ford or bridge next to the hex}. Returns [[side, terrain, metres from the fight's
    middle to that side]] for the sides reached."""
    hm, a = d.wounds["combat"]["move"]["hex_m"], edges["hex_m"] / 2
    spot = hex_spot(edges["hex_m"], edges["spot_seed"])
    plans = _side_plans(d, terrain, cols, rows, seed, edges)
    reached = set()
    for r in range(rows):
        for c in range(cols):
            q = _map_xy(hm, cols, rows, c, r)
            pt = [spot[0] + q[0], spot[1] + q[1]]
            best, depth, bu = _past_side(plans, pt, a)
            if best:
                reached.add(best)
                _set_hex(ground, f"{c},{r}", *_beyond(plans[best], pt, bu, depth, spot, hm, f"{c},{r}"))
    return [[name, plans[name]["terrain"], int(a - (spot[0] * u[0] + spot[1] * u[1]) + 0.5)] for name, u in SIDES if name in reached]


def clear_ground(ground: dict, centre, radius: int, cols: int, rows: int) -> None:
    """Inside a camp: open ground, level with its middle."""
    mid = level_at(ground, centre)
    for r in range(rows):
        for c in range(cols):
            if hex_distance([c, r], centre) > radius:
                continue
            k = f"{c},{r}"
            ground["kinds"].pop(k, None)
            if mid:
                ground["levels"][k] = mid
            else:
                ground["levels"].pop(k, None)


def step_cost(d: Data, works, a, b, ground=None, climb: int | None = None, deep_stops: bool = False, short: bool = False) -> int | None:
    """Movement to step from hex a to the next hex b: 1, plus crossing the works on the
    edge and entering the works in b, plus its ground and any climb. None if a work stops him.
    climb: with ladders, a work that cannot be crossed (a wall, a palisade, a barred gate) costs
    this instead, and a deep ditch only its `cross` (as one with ladders already down in it).
    deep_stops: a deep ditch with no ladders down in it stops him (a charge without ladders).
    short: his ladders are short: a tall work (a wall) still stops him."""
    cost = 1 + ground_step(d, ground, a, b)
    for it in _edge_items(d, works, a, b):
        s = _spec(d, "edge", it)
        c = None if s.get("gate") else s.get("cross")      # open gates are already left out
        if it.get("deep") and not it.get("laddered") and climb is None:
            if deep_stops:
                return None
            c = s["deep"]
        if c is None:
            c = None if short and s.get("tall") else climb
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


def reachable_works(d: Data, start, steps: int, cols: int, rows: int, enemies, friends, works, extra: int = 0, ground=None) -> dict:
    """Like reachable(), but each step costs step_cost() (works and ground slow or stop him),
    plus `extra` for every hex (deep mud or snow)."""
    blocked = {tuple(e) for e in enemies}
    friendly = {tuple(f) for f in friends}
    best = {tuple(start): 0}
    heap = [(0, 0, tuple(start))]
    seq, done = [1], set()

    def relax(h, cost, n):
        t = tuple(n)
        if t in blocked:
            return
        sc = step_cost(d, works, list(h), n, ground)
        if sc is None:
            return
        nc = cost + sc + extra
        if nc > steps or nc >= best.get(t, steps + 1):
            return
        best[t] = nc
        heapq.heappush(heap, (nc, seq[0], t))
        seq[0] += 1

    while heap:
        cost, _, h = heapq.heappop(heap)
        if h in done:
            continue
        done.add(h)
        for n in neighbours(list(h), cols, rows):
            relax(h, cost, n)
    return {h: c for h, c in best.items() if h not in friendly or c == 0}


def facing(target, attacker, cols: int, rows: int) -> list:
    """The target's neighbours nearest the attacker: what lies between them."""
    ns = neighbours(list(target), cols, rows)
    if not ns:
        return []
    best = min(hex_distance(n, attacker) for n in ns)
    return [n for n in ns if hex_distance(n, attacker) == best]


def missile_cover(d: Data, works, attacker, target, cols: int, rows: int) -> dict:
    """Cover a target has against a missile attack: {cover (% off the attack), work}. A man at
    the foot of a wall (or bank) gets no cover from it against a man shooting down from its
    high side, right above him."""
    best, what = 0, None
    it = _hex_item(d, works, target)
    if it and _spec(d, "hex", it).get("cover_here", 0) > best:
        best, what = _spec(d, "hex", it)["cover_here"], it["type"]
    for n in facing(target, attacker, cols, rows):
        for e in _edge_items(d, works, target, n):
            s = _spec(d, "edge", e)
            if s.get("cover_side", "both") == "high" and e.get("high") != hkey(target):
                continue
            if list(n) == list(attacker) and e.get("high") == hkey(n):
                continue                            # shot at from the top of the wall he stands under: no cover at its foot
            if s.get("cover", 0) > best:
                best, what = s["cover"], e["type"]
        if list(n) != list(attacker):
            it = _hex_item(d, works, n)
            if it and _spec(d, "hex", it).get("cover_behind", 0) > best:
                best, what = _spec(d, "hex", it)["cover_behind"], it["type"]
    return {"cover": best, "work": what}


def melee_across(d: Data, works, attacker, target, reach: int, cols: int, rows: int) -> dict:
    """A close-combat attack across works: {blocked (only reach 2+ strikes over it: a wall,
    palisade or gate, or a deep ditch with no ladders down in it),
    penalty (% off for attacking up at a man on the high side), work}."""
    cands = [list(attacker)] if hex_distance(attacker, target) == 1 else facing(target, attacker, cols, rows)
    blocked, penalty, what = False, 0, None
    for n in cands:
        pen = 0
        for e in _edge_items(d, works, target, n):
            s = _spec(d, "edge", e)
            if (s.get("blocks_melee") or (e.get("deep") and not e.get("laddered"))) and reach < 2 and hex_distance(attacker, target) == 1:
                blocked, what = True, e["type"]      # a wall, or a deep ditch with no ladders down in it
            if s.get("height") and e.get("high") == hkey(target):
                pen += s["height"]
                what = what or e["type"]
        penalty = max(penalty, pen)
    return {"blocked": blocked, "penalty": penalty, "work": what}


def party_of(men: int, ftype) -> list:
    """A force type as a party, [[type, men]]. A column of several forces is given as its
    party already: [[type, men], ...] (ftype a list), and `men` is then its total."""
    return [[ftype, men]] if isinstance(ftype, str) else [list(p) for p in ftype]


def camp_radius(d: Data, men: int, ftype, hex_m: float | None = None) -> int:
    """Hexes from the centre to the edge of a camp for this many men. ftype: a force type, or
    a column's party (see party_of). hex_m: the map's hex across the flats in metres (the
    battle map's 2 m unless given; the field map's is 10)."""
    W = d.works
    hm = hex_m or d.wounds["combat"]["move"]["hex_m"]
    area = max(W["camp_area_min"], sum(n * W["camp_area"][t] for t, n in party_of(men, ftype)))
    n = area / (3 ** 0.5 / 2 * hm * hm)
    r = 0
    while 3 * r * (r + 1) + 1 < n:
        r += 1
    return max(r, 1)


def edge_metres(d: Data, hex_m: float | None = None) -> float:
    """Length of one side of a hex, in metres: the battle map's (hex_m across the flats)
    unless another hex size is given."""
    return (hex_m or d.wounds["combat"]["move"]["hex_m"]) / 3 ** 0.5


def _edge_labour(s: dict, hauled: bool, em: float) -> float:
    if "each" in s:
        return s["each"]
    return (s.get("per_metre", 0) + (s.get("haul", 0) if hauled else 0)) * em


def works_labour(d: Data, works, hauled: bool = False, hex_m: float | None = None) -> float:
    """Man-hours to build these works: per_metre along each hex side, `each` for gates and
    for each hex of stakes or abatis, plus `haul` when the timber is hauled from afar."""
    W, em, t = d.works, edge_metres(d, hex_m), 0.0
    for items in (works or {}).get("edges", {}).values():
        t += sum(_edge_labour(W["edge_works"][it["type"]], hauled, em) for it in items)
    for it in (works or {}).get("hexes", {}).values():
        s = W["hex_works"][it["type"]]
        t += s.get("each", 0) + (s.get("haul", 0) if hauled else 0)
    return t


def camp_map_size(d: Data, kind: str, men: int, ftype: str) -> int:
    """Columns (and rows) of a battle map just big enough for this camp and its works."""
    extra = 2 if d.works["camps"][kind].get("layout") == "fortified" else 1
    return 2 * (camp_radius(d, men, ftype) + extra) + 3


AXIAL_DIRS = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]   # E, NE, NW, W, SW, SE


def ring_walk(centre, k: int, start: int = 0) -> list:
    """The hexes k from the centre, in order round the ring from side start (0 east, then
    anticlockwise as AXIAL_DIRS: the gate side)."""
    if k == 0:
        return [list(centre)]
    sq, sr = AXIAL_DIRS[start]
    q, r = centre[0] - (centre[1] - (centre[1] & 1)) // 2 + k * sq, centre[1] + k * sr
    out = []
    for i in range(6):
        dq, dr = AXIAL_DIRS[(i + start + 2) % 6]
        for _ in range(k):
            out.append([q + (r - (r & 1)) // 2, r])
            q, r = q + dq, r + dr
    return out


def _camp_fits(centre, rr: int, cols: int, rows: int) -> bool:
    cnt = sum(1 for y in range(rows) for x in range(cols) if hex_distance(centre, [x, y]) <= rr)
    return cnt == 3 * rr * (rr + 1) + 1


def _around(h) -> list:
    """All six neighbours, on the map or not (a big camp runs off the map)."""
    return [[h[0] + dc, h[1] + dr] for dc, dr in _NEIGHBOURS[h[1] & 1]]


def _gate_list(gate) -> list:
    """A camp's gate sides: one side, or a list with the main gate first."""
    return list(gate) if isinstance(gate, (list, tuple)) else [gate]


def _ways_out(centre, r: int, gates: list) -> list:
    """The hexes just outside each gate, left open."""
    return [ring_walk(centre, r + 1, g)[0] for g in gates]


def _stake_pieces(centre, r: int, gate=0) -> dict:
    gates = _gate_list(gate)
    out = _ways_out(centre, r, gates)
    return {"stakes": [("hex", (h,), {"type": "stakes", "progress": 0}) for h in ring_walk(centre, r + 1, gates[0]) if h not in out]}


def _wall_pieces(out: dict, centre, r: int, gate=0) -> None:
    """Bank and palisade round the ring, and the gates."""
    gates = _gate_list(gate)
    pairs = [(ring_walk(centre, r, g)[0], ring_walk(centre, r + 1, g)[0]) for g in gates]
    for h in ring_walk(centre, r, gates[0]):
        for n in (x for x in _around(h) if hex_distance(centre, x) == r + 1):
            if any(h == gi and n == go for gi, go in pairs):
                out["gate"].append(("edge", (h, n), {"type": "gate", "progress": 0, "open": False, "inside": hkey(h)}))
                continue
            out["bank"].append(("edge", (h, n), {"type": "bank", "progress": 0, "high": hkey(h)}))
            out["palisade"].append(("edge", (h, n), {"type": "palisade", "progress": 0}))


def _ditch_pieces(out: dict, centre, r: int, gate=0) -> None:
    """The ditch one ring out, leaving the way to each gate."""
    gates = _gate_list(gate)
    ways = _ways_out(centre, r, gates)
    for h in (x for x in ring_walk(centre, r + 1, gates[0]) if x not in ways):
        for n in (x for x in _around(h) if hex_distance(centre, x) == r + 2):
            out["ditch"].append(("edge", (h, n), {"type": "ditch", "progress": 0, "high": hkey(h)}))


def _camp_pieces(layout: str, centre, r: int, gate=0) -> dict:
    """Every piece of the camp's works, by type, each in the order it is built round the ring
    from the main gate, on the map or not: {type: [(kind, hexes, item)]}. gate: the gate's side,
    or a list of sides with the main gate first."""
    if layout == "stakes":
        return _stake_pieces(centre, r, gate)
    out = {"ditch": [], "bank": [], "palisade": [], "gate": []}
    _wall_pieces(out, centre, r, gate)
    _ditch_pieces(out, centre, r, gate)
    return out


def _piece_labour(d: Data, kind: str, item: dict, hauled: bool, hex_m: float | None = None) -> float:
    if kind == "edge":
        return _edge_labour(d.works["edge_works"][item["type"]], hauled, edge_metres(d, hex_m))
    s = d.works["hex_works"][item["type"]]
    return s.get("each", 0) + (s.get("haul", 0) if hauled else 0)


CAMP_ROOM = 6     # hexes left between a camp too big for the map and the attackers' edge


def camp_works(d: Data, kind: str, men: int, ftype, cols: int, rows: int,
               done: float | None = None, hauled: bool = False, hex_m: float | None = None, at=None, gate=0) -> dict:
    """Battle-map layout for a camp: {centre, radius, fits, works}. A camp that fits sits in the
    middle of the map. One that does not is laid out at its true size with its centre moved
    west, so the stretch with the gate (on the east) is on the map, CAMP_ROOM hexes from the
    east edge where the attackers wait; the rest runs off the map (fits false). done:
    man-hours of work done so far (None: finished). The works go up in the order the camp lists
    them (works.yaml), each kind all round the ring from the gate before the next starts; a
    piece appears once its labour (with hauled timber if `hauled`) is done and it is on the map.
    hex_m: the map's hex size (the battle map's unless given; the field map's is 10 m). at: a
    centre to use instead of the middle (camp_centre, for a camp at a crossing), kept even when
    the camp does not fit; gate: the side its gate is on (camp_gate; east unless given), or a
    list of sides with the main gate first (camp_gates)."""
    c = d.works["camps"][kind]
    layout = c.get("layout")
    r = camp_radius(d, men, ftype, hex_m)
    extra = 2 if layout == "fortified" else 1
    centre = list(at) if at else [cols // 2, rows // 2]
    fits = _camp_fits(centre, r + extra, cols, rows)
    if not fits and not at:
        centre = [cols - 1 - CAMP_ROOM - (r + extra), rows // 2]
    works = {"edges": {}, "hexes": {}}
    if layout:
        _lay(d, c, _camp_pieces(layout, centre, r, gate), works, done, hauled, (cols, rows), hex_m)
    return {"centre": centre, "radius": r, "fits": fits, "works": works}


def _lay(d: Data, c: dict, pieces: dict, works: dict, done: float | None, hauled: bool, size, hex_m=None) -> None:
    """Put the pieces into works in building order, stopping where the labour done runs out.
    Pieces off the map count towards the labour but are not shown."""
    def on(h):
        return 0 <= h[0] < size[0] and 0 <= h[1] < size[1]
    spent = 0.0
    for where, hexes, item in (p for kind in c["works"] for p in pieces[kind]):
        spent += _piece_labour(d, where, item, hauled, hex_m)
        if done is not None and spent > done + 1e-9:
            return
        if not all(on(h) for h in hexes):
            continue
        if where == "hex":
            works["hexes"][hkey(hexes[0])] = item
        else:
            works["edges"].setdefault(edge_key(*hexes), []).append(item)


# ---------- weather in battle ----------

def deep_going(d: Data, ground: dict | None) -> int:
    """Extra movement per hex on the battle map for deep mud or snow."""
    if not ground or not d.weather:
        return 0
    deep = d.weather["ground"]["deep"]
    return d.weather["battle"]["deep_step"] if ground.get("mud", 0) >= deep or ground.get("snow", 0) >= deep else 0


WIND_VECTORS = {0: (0.0, -1.0), 1: (math.sqrt(0.5), -math.sqrt(0.5)), 2: (1.0, 0.0), 3: (math.sqrt(0.5), math.sqrt(0.5)),
                4: (0.0, 1.0), 5: (-math.sqrt(0.5), math.sqrt(0.5)), 6: (-1.0, 0.0), 7: (-math.sqrt(0.5), -math.sqrt(0.5))}


def wind_lie(d: Data, weather: dict | None, frm, to, up: str = "N") -> str | None:
    """How a shot from hex frm to hex to lies to the wind: "with" (the wind behind it, within
    45 degrees), "against" (into it, within 45 degrees), "across", or None (calm, no direction
    or no hexes). up: the compass point at the top of the map."""
    pts = d.weather.get("wind_points", [])
    if not weather or not frm or not to or weather.get("dir") not in pts or weather.get("wind") == "calm":
        return None
    k = (pts.index(weather["dir"]) - pts.index(up) + 4) % 8          # where it blows to, on the page
    wx, wy = WIND_VECTORS[k]
    q1, q2 = frm[0] - (frm[1] - (frm[1] & 1)) / 2, to[0] - (to[1] - (to[1] & 1)) / 2
    dr = to[1] - frm[1]
    dx, dy = math.sqrt(3) * ((q2 - q1) + dr / 2), 1.5 * dr
    n = math.hypot(dx, dy)
    if n == 0:
        return None
    dot = dx * wx + dy * wy
    if dot >= math.sqrt(0.5) * n - 1e-9:
        return "with"
    if dot <= -math.sqrt(0.5) * n + 1e-9:
        return "against"
    return "across"


def _sight(d: Data, cond: dict, lie: str | None, out: dict):
    """How far a shooter can see to aim (battle hexes, None for clear): less with rain or snow
    driven into his face."""
    vis = cond.get("visibility")
    if vis is not None and lie == "against" and cond["precip"] != "none":
        vis = vis * d.weather["driven_sight"] // 100
        out["notes"].append(f"{cond['precip']} in their faces")
    return vis


def _wind_reach(w: dict, wind: dict, lie: str | None, out: dict) -> None:
    """With the wind a bow, crossbow or sling reaches further; into it, less and harder."""
    if lie not in ("with", "against") or w.get("ignition") or not wind.get("reach"):
        return
    out["reach"] = wind["reach"] if lie == "with" else -wind["reach"]
    out["notes"].append(f"{'with' if lie == 'with' else 'into'} the wind, reach {out['reach']:+d}%")
    if lie == "against" and wind.get("into_wind"):
        out["penalty"] += wind["into_wind"]
        out["notes"].append(f"into the wind -{wind['into_wind']}%")


def weather_attack(d: Data, weather: dict | None, wid: str, dist: int, frm=None, to=None, up: str = "N") -> dict:
    """What the weather does to a missile attack at `dist` hexes, from hex frm to hex to (for
    the wind's direction): {blocked (a reason, or None), penalty (% off), misfire (% chance),
    reach (% on the range bands: with the wind +, into it -), notes}. Close combat is not affected."""
    out = {"blocked": None, "penalty": 0, "misfire": 0, "reach": 0, "notes": []}
    w = d.weapons[wid]
    if not weather or not d.weather or "range" not in w:
        return out
    WX = d.weather
    cond = WX["conditions"][weather["cond"]]
    lie = wind_lie(d, weather, frm, to, up)
    vis = _sight(d, cond, lie, out)
    if vis is not None and dist > vis:
        out["blocked"] = f"{cond['name']}: no one can be seen to aim at beyond {vis} hexes ({vis * 2} m)."
        return out
    wind = next(x for x in WX["winds"] if x["id"] == weather["wind"])
    _wind_reach(w, wind, lie, out)
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
