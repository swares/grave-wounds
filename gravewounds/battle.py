"""The turn of the field map: a battle's moves and exchanges, from set-up to the end, as the
page plays them, and self-play (the enemy commander on both sides). A battle's state bt is a
dict: sides, table, units, field, size, exchange, phase ("setup", 0, 1 or "over"), stages,
stageNo, waiting, start, entry, seq. Mirrored exactly by templates/units.js (the turn)."""
from __future__ import annotations

import copy
import math

from . import commander as K, units as U
from .model import Data

EDGE_FACING = {"S": 1, "N": 4, "W": 0, "E": 3}
OPPOSITE = {"S": "N", "N": "S", "W": "E", "E": "W"}
EDGE_BEHIND = ["W", "S", "E", "E", "N", "W"]      # the map edge behind units facing 0-5


def side_index(bt: dict, u: dict) -> int:
    return 0 if u["side"] == bt["sides"][0] else 1


def _support(bt: dict) -> list:
    return bt["field"].setdefault("support", [])


def make_unit(d: Data, o: dict, uid: int, table: str) -> dict:
    """A new unit as the GM or a battlefield draws it."""
    nv = o.get("nv") or (U.vehicle_device(d, table) if o.get("vehicle") else None)
    fc = U.fire_control_of(d, o, table)
    u = {"id": uid, "name": o["name"], "side": o["side"], "banner": o.get("banner") or None, "force": o.get("force"), "men": o["men"],
         "start": o["men"], "down": 0, "dead": 0, "hurt": {}, "heroes": [], "quality": o["quality"], "weapon": o["weapon"],
         "kit": o["kit"], "formation": o["formation"], "mounted": bool(o.get("mounted"))}
    if U.is_gun(d, o["weapon"]):
        u["guns"] = U.gun_kind(o)
    u.update({"width": o.get("width") or math.ceil(o["men"] / U.form(d, o)["per_hex"]), "pos": o["pos"], "facing": o["facing"],
              "state": "steady", "charged": False})
    u.update(_unit_marks(o))
    if nv:
        u["nv"] = nv
    if fc:
        u["fc"] = fc
    if o.get("medics"):
        u.update({"medics": o["medics"], "medic_quality": o.get("medic_quality") or o["quality"]})
    return u


def _unit_marks(o: dict) -> dict:
    """The marks a drawn unit carries if set: flags, its vehicle, type and size, a machine gun's
    fixed line, a route's waypoints and its orders from the account (hold, withdraw; copied)."""
    out = {k: True for k in ("prone", "emplaced", "fac", "ladders") if o.get(k)}
    out.update({k: o[k] for k in ("vehicle", "type", "size", "armour") if o.get(k)})
    if o.get("fixed"):
        out["fixed"] = list(o["fixed"])
    if o.get("via"):
        out["via"] = [list(h) for h in o["via"]]
    if o.get("hold"):
        out["hold"] = True
    if o.get("fights_on"):
        out["fights_on"] = True
    if o.get("unfit") is not None:
        out["unfit"] = o["unfit"]
    if o.get("he") is False:
        out["he"] = False
    if o.get("asFought"):
        out["asFought"] = True
    if o.get("withdraw"):
        out["withdraw"] = {"at": o["withdraw"]["at"], "to": o["withdraw"]["to"]}
    return out


def ensure_tags(bt: dict) -> None:
    """Each unit's number on its side, kept for the battle (B3 stays B3)."""
    for u in sorted(bt["units"], key=lambda x: x["id"]):
        if not u.get("n"):
            k = side_index(bt, u)
            u["n"] = 1 + max([0] + [v["n"] for v in bt["units"] if v.get("n") and side_index(bt, v) == k])


def stand_or_fly(bt: dict, unit: dict, lands) -> None:
    """A battlefield's unit: on the field, or (lands: a landing zone's index) waiting to come in by air."""
    zones = bt["field"].get("lz") or []
    lz = zones[lands] if isinstance(lands, int) and 0 <= lands < len(zones) else None
    if not lz:
        bt["units"].append(unit)
        return
    tmpl = {k: v for k, v in unit.items() if k not in ("men", "start", "down", "dead", "hurt", "heroes", "state")}
    bt["field"].setdefault("lifts", []).append({"unit": {**tmpl, "pos": list(lz)}, "lz": list(lz), "left": unit["men"]})


def hold_for_stages(bt: dict, phases) -> None:
    """The battlefield's phases; the units they bring on wait off the map (numbered first)."""
    if not phases:
        return
    ensure_tags(bt)
    bt["stages"], bt["stageNo"], bt["waiting"] = copy.deepcopy(phases), -1, []
    lifts, sup = bt["field"].get("lifts") or [], _support(bt)
    for i, st in enumerate(bt["stages"]):
        for name in st.get("arrive") or []:
            u = next((v for v in bt["units"] if v["name"] == name), None)
            lf = next((x for x in lifts if x["unit"]["name"] == name), None)
            b = next((x for x in sup if x["name"] == name), None)
            if u:
                bt["waiting"].append({"stage": i, "unit": u})
                bt["units"] = [v for v in bt["units"] if v is not u]
            elif lf:
                bt["waiting"].append({"stage": i, "unit": lf["unit"], "lift": lf})
                bt["field"]["lifts"] = [x for x in bt["field"]["lifts"] if x is not lf]
            elif b:
                bt["waiting"].append({"stage": i, "unit": {"name": b["name"]}, "support": b})
                bt["field"]["support"] = [x for x in _support(bt) if x is not b]


def set_up(d: Data, fid: str, planner: bool = False) -> dict:
    """A battlefield with its armies as drawn up, before the battle starts. planner: the commander
    plans for itself on a side with no written plan (docs/units.md, The procedural planner)."""
    F = d.fields[fid]
    field = U.battlefield(d, fid)
    if planner:
        field["planner"] = True
    bt = {"sides": list(F["sides"]), "table": F["table"], "units": [], "field": field, "exchange": 0, "phase": "setup", "stages": None,
         "stageNo": -1, "waiting": [], "start": None, "entry": F.get("entry") or None, "seq": 1, "ends": F.get("ends") or None}
    bt["size"] = list(field["size"])
    field["lifts"] = []
    plan = side_plan(F)
    if plan:
        field["plan"] = plan
    for u in F.get("units", []):
        unit = make_unit(d, {**u, "side": F["sides"][u["side"]], "asFought": True}, bt["seq"], bt["table"])
        bt["seq"] += 1
        stand_or_fly(bt, unit, u.get("lands"))
    hold_for_stages(bt, F.get("phases"))
    return bt


def side_plan(F: dict, off: tuple = ()) -> dict | None:
    """A battlefield's plan (data/plans.yaml) for its armies as drawn up, by side name: {side:
    [steps]}, leaving out the sides in off (indices whose plan the GM has switched off)."""
    sides = ((F.get("plan") or {}).get("sides") or {})
    out = {F["sides"][int(k)]: steps for k, steps in sides.items() if int(k) not in off and steps}
    return out or None


def _fielded(bt: dict, k: int) -> bool:
    return any(side_index(bt, u) == k and u["men"] > 0 and u["state"] != "fled" for u in bt["units"])


def side_facing(bt: dict, k: int) -> int:
    """The way most of a side's men face (its starting edge's way if it has none left)."""
    n = [0] * 6
    for u in bt["units"]:
        if side_index(bt, u) == k and u["men"] > 0 and u["state"] != "fled":
            n[u["facing"] % 6] += u["men"]
    if max(n) > 0:
        return n.index(max(n))
    return 3 if k else 0


def entry_edge(bt: dict, k: int) -> str:
    """Where side k's new units come in: the battlefield's entry, else the edge behind the way most
    of its men face; the other side's opposite edge if they would share one."""
    if bt.get("entry"):
        return bt["entry"][k]

    def own(s):
        return EDGE_BEHIND[side_facing(bt, s) % 6] if _fielded(bt, s) else None
    mine, theirs = own(k), own(1 - k)
    if mine and not (k == 1 and mine == theirs):
        return mine
    if theirs:
        return OPPOSITE[theirs]
    return "E" if k else "W"


def _mid(m: int) -> list:
    out = [m // 2 + (-1 if i % 2 else 1) * math.ceil(i / 2) for i in range(m)]
    return [x for x in out if 0 <= x < m]


def entry_spots(size, facing: int, ranks: int) -> list:
    """Front hexes for a unit `ranks` deep with its rear at the map edge behind a side facing this
    way, middle outwards."""
    W, H = size
    out = []
    for dd in range(ranks, ranks + 12):
        if facing == 1:
            out += [[c, H - 1 - dd] for c in _mid(W)]
        elif facing == 4:
            out += [[c, dd] for c in _mid(W)]
        elif facing in (0, 5):
            out += [[dd, r] for r in _mid(H)]
        else:
            out += [[W - 1 - dd, r] for r in _mid(H)]
    return out


def entry_widths(size, w: int) -> list:
    """The widths to try: as asked (at most the map's width), then a quarter narrower each time, to 1."""
    out, x = [], min(w, size[0] - 4)
    while x >= 1:
        out.append(x)
        x = min(x - 1, math.floor(x * 0.75)) if x > 1 else 0
    return out


def place_arrival(d: Data, bt: dict, u: dict, k: int) -> dict | None:
    """Where an arriving unit comes on: where the battlefield draws it if there is room, else at
    its side's entry edge; None if no room."""
    n = len(bt["units"])
    if U._fits(d, bt["units"] + [u], n, u, bt["size"], bt["field"]):
        return u
    facing = EDGE_FACING[entry_edge(bt, k)]
    for width in entry_widths(bt["size"], u["width"]):
        ranks = len(U.footprint(d, {**u, "width": width, "pos": [0, 0], "facing": facing}))
        for h in entry_spots(bt["size"], facing, ranks):
            v = {**u, "width": width, "pos": h, "facing": facing}
            if U._fits(d, bt["units"] + [v], n, v, bt["size"], bt["field"]):
                return v
    return None


def _phase_due(bt: dict, st: dict) -> bool:
    """A phase's time has come: its exchange (at the latest), or sooner on an event: when {fires: a
    unit's name, wait} that many exchanges after the unit first fired; when {after} that many after
    the phase before began."""
    if st["at"] <= bt["exchange"]:
        return True
    on = st.get("when") or {}
    if on.get("fires"):
        f = (bt.get("fired") or {}).get(on["fires"])
        return f is not None and f + on.get("wait", 0) <= bt["exchange"]
    if "after" in on:
        s = (bt.get("stageBegan") or {}).get(bt["stageNo"])
        return s is not None and s + on["after"] <= bt["exchange"]
    return False


def _note_fired(bt: dict, log: list) -> None:
    """The exchange each unit first fired a volley (bt.fired: {name: exchange}), for phases that begin on it."""
    fired = bt.setdefault("fired", {})
    for line in log or []:
        if line.get("kind") == "volley" and line.get("att") is not None and line["att"] < len(bt["units"]):
            fired.setdefault(bt["units"][line["att"]]["name"], bt["exchange"])


def advance_stages(d: Data, bt: dict) -> dict:
    """At the start of an exchange: begin each phase whose exchange has come, and bring on its
    units (any with no room wait for the next exchange)."""
    out = {"begun": [], "came": [], "flying": [], "onCall": []}
    if not bt.get("stages"):
        return out
    while bt["stageNo"] + 1 < len(bt["stages"]) and _phase_due(bt, bt["stages"][bt["stageNo"] + 1]):
        bt["stageNo"] += 1
        bt.setdefault("stageBegan", {})[bt["stageNo"]] = bt["exchange"]
        bt["field"]["begun"] = [*(bt["field"].get("begun") or []), bt["stages"][bt["stageNo"]]["name"]]   # for plans' phase triggers
        out["begun"].append(bt["stageNo"])
        _light_of_phase(d, bt, bt["stages"][bt["stageNo"]], out)
    keep = []
    for w in bt["waiting"]:
        if w["stage"] > bt["stageNo"]:
            keep.append(w)
        elif w.get("support"):
            _support(bt).append(w["support"])
            out["onCall"].append(w["support"]["name"])
        elif w.get("lift"):
            bt["field"].setdefault("lifts", []).append(w["lift"])
            out["flying"].append({"name": w["unit"]["name"], "left": w["lift"]["left"]})
        else:
            at = place_arrival(d, bt, w["unit"], side_index(bt, w["unit"]))
            if not at:
                keep.append(w)
                continue
            bt["units"].append({**at, "arrived": bt["exchange"]})
            out["came"].append(len(bt["units"]) - 1)
    bt["waiting"] = keep
    return out


def _light_of_phase(d: Data, bt: dict, st: dict, out: dict) -> None:
    """A phase that sets the light (light: a weather.yaml light level) changes the field's from
    then on (sunset, dawn); one that sets the weather (weather: {cond, wind}) changes it (a squall);
    out["light"], out["weather"]: {phase index: its name}."""
    if st.get("weather"):
        W = st["weather"]
        bt["field"]["weather"] = {**(bt["field"].get("weather") or {}), **W}
        wind = (", " + next(w["name"] for w in d.weather["winds"] if w["id"] == W["wind"]).lower()) if W.get("wind") else ""
        out.setdefault("weather", {})[bt["stageNo"]] = (d.weather["conditions"][W["cond"]]["name"] if W.get("cond") else "") + wind
    if not st.get("light"):
        return
    bt["field"]["weather"] = {**(bt["field"].get("weather") or {}), "light": st["light"]}
    out.setdefault("light", {})[bt["stageNo"]] = d.weather["light"]["levels"][st["light"]]["name"]


def mark_starts(bt: dict) -> None:
    """With minefields down, where each unit's first moves begin (the ground it crosses)."""
    if bt["field"].get("mines"):
        for u in bt["units"]:
            u["was"] = [list(u["pos"]), u["facing"]]


def start_phase(d: Data, bt: dict, k: int) -> list:
    """Side k's move; at the start of an exchange every broken unit runs first."""
    bt["phase"], ran = k, []
    for i in range(len(bt["units"])):
        if k != 0 or bt["units"][i]["state"] != "broken":
            continue
        after = U.flee(d, bt["units"], i, bt["size"], bt["field"])
        if U.cornered(d, bt["units"], i, after):
            s = U.surrender(bt["units"][i], U.quarter(d, bt["table"]))
            bt["units"][i] = s["unit"]
            ran.append({"unit": i, "through": [], "fled": True, "surrendered": True, "taken": s["taken"], "killed": s["killed"]})
            continue
        through = U.ran_through(d, bt["units"], i, after)
        bt["units"] = U.run_away(d, bt["units"], i, bt["size"], bt["field"])
        ran.append({"unit": i, "through": through, "fled": bt["units"][i]["state"] == "fled"})
    bt["start"] = [dict(u) for u in bt["units"]]
    return ran


def drifts(d: Data, bt: dict, k: int, rng) -> list:
    """In the dark, each unit of side k that moved this phase may lose its direction."""
    if not U.light_of(d, bt["field"]):
        return []
    out = []
    for i, u in enumerate(list(bt["units"])):
        was = (bt.get("start") or [])[i] if i < len(bt.get("start") or []) else None
        if u["side"] != bt["sides"][k] or not was or list(was["pos"]) == list(u["pos"]):
            continue
        r = U.night_drift(d, bt["units"], i, bt["size"], bt["field"], rng)
        if not r["lost"]:
            continue
        bt["units"][i] = r["unit"]
        out.append({"unit": i, "strayed": bool(r.get("strayed")), "turned": r["unit"]["facing"] != u["facing"]})
    return out


def realign_starts(bt: dict) -> None:
    """bt.start by unit id, after units joined or left the list (a unit whose riders changed starts as it is)."""
    was = bt.get("start") or []

    def rid(x):
        return (x.get("riders") or {}).get("id")
    out = []
    for u in bt["units"]:
        s = next((x for x in was if x["id"] == u["id"]), None)
        out.append(s if s and rid(s) == rid(u) else dict(u))
    bt["start"] = out


def _unfit_pct(u: dict, war) -> float:
    """A unit's unfit %: a battlefield's own figure (unfit); its armies as fought are what fought,
    so else none; else (drawn by the GM or from the travel map) the war's."""
    if u.get("unfit") is not None:
        return u["unfit"]
    return 0 if u.get("asFought") else war


def unfit_vehicles(d: Data, bt: dict, rng) -> list:
    """As a battle begins, each vehicle is unfit at its unit's `unfit` %, else units.yaml
    reliability.unfit % (by war): left out with its crew, unhurt, a unit keeping at least one.
    [{unit, unfit}]."""
    war, out = ((d.units.get("reliability") or {}).get("unfit") or {}).get(bt["field"].get("war")) or 0, []
    if rng is None:
        return out
    for i, u in enumerate(bt["units"]):
        K, n = U.vehicle_kind(d, u), U.vehicles_left(d, u)
        pct = _unfit_pct(u, war)
        if not K or n < 1 or not pct:
            continue
        k = min(sum(1 for _ in range(n) if rng.randint(1, 100) <= pct), n - 1)
        if k:
            u["men"] = max(K["crew"], u["men"] - k * K["crew"])
            out.append({"unit": i, "unfit": k})
    return out


def _moved(bt: dict, k: int, starts: list, i: int, u: dict) -> int:
    """How many hexes vehicle unit i of side k has moved this phase (0 if not one, or not on the map)."""
    was = starts[i] if i < len(starts) else None
    if u["side"] != bt["sides"][k] or not u.get("vehicle") or not was or not u.get("pos") or not was.get("pos"):
        return 0
    return U.hdist(was["pos"], u["pos"])


def breakdowns(d: Data, bt: dict, k: int, rng) -> list:
    """A war's vehicles (units.yaml reliability.per_hex) that moved this phase break down
    (immobilised) at that % for each hex moved. [{unit, broke}]."""
    p, out = ((d.units.get("reliability") or {}).get("per_hex") or {}).get(bt["field"].get("war")) or 0, []
    if not p:
        return out
    starts = bt.get("start") or []
    for i, u in enumerate(bt["units"]):
        hexes = _moved(bt, k, starts, i, u)
        n = U.vehicles_left(d, u) - (u.get("immobile") or 0)
        if not hexes or n < 1:
            continue
        q = math.floor((1 - (1 - p / 100) ** hexes) * 10000 + 0.5)
        broke = sum(1 for _ in range(n) if rng.randint(1, 10000) <= q)
        if broke:
            u["immobile"] = (u.get("immobile") or 0) + broke
            out.append({"unit": i, "broke": broke})
    return out


def begin(d: Data, bt: dict, rng=None) -> dict:
    """Set-up done: the first exchange begins, side 0 to move."""
    bt["exchange"] = 1
    bt["field"]["war"] = (d.tables.get(bt["table"]) or {}).get("battle") if bt.get("table") else None   # the war of its wound table: stoppages and breakdowns (reliability)
    unfit = unfit_vehicles(d, bt, rng)
    stages = advance_stages(d, bt)
    mark_starts(bt)
    bt["field"]["located"] = [[u["side"], list(u["pos"])] for u in bt["units"] if u.get("pos")]   # where each unit stood when the battle began: located before it, for planned fire (indirect.planned)
    return {"stages": stages, "ran": start_phase(d, bt, 0), "unfit": unfit}


def end_move(d: Data, bt: dict, rng) -> dict:
    """The moving side's move is done: after side 0, side 1 moves; after side 1, the exchange is
    fought and the next begins."""
    if bt["phase"] == 0:
        lost, broke = drifts(d, bt, 0, rng), breakdowns(d, bt, 0, rng)
        return {"lost": lost, "broke": broke, "log": None, "stages": None, "ran": start_phase(d, bt, 1)}
    lost, broke = drifts(d, bt, 1, rng), breakdowns(d, bt, 1, rng)
    bt["units"], log = U.exchange(d, bt["units"], bt["table"], rng, bt["field"])
    _note_fired(bt, log)
    bt["exchange"] += 1
    stages = advance_stages(d, bt)
    return {"lost": lost, "broke": broke, "log": log, "stages": stages, "ran": start_phase(d, bt, 0)}


def commander_memory(bt: dict, memo: dict) -> dict:
    """M {n, mem}: where a side's commander last saw each enemy unit (by index), forgotten when
    units joined or left the list since."""
    if memo["n"] != len(bt["units"]):
        memo["mem"], memo["n"] = {}, len(bt["units"])
    return memo["mem"]


def command_move(d: Data, bt: dict, stance: str, memo: dict, rng) -> list:
    """The commander orders the moving side (M: its memory, see commander_memory): its orders."""
    n = len(bt["units"])
    bt["units"], orders = K.command(d, bt["units"], bt["sides"][bt["phase"]], bt["size"], bt["field"], rng, bt["exchange"], stance,
                                   commander_memory(bt, memo), bt["table"])
    if len(bt["units"]) != n:
        realign_starts(bt)
    memo["n"] = len(bt["units"])
    return orders


def _standing(bt: dict, k: int) -> bool:
    return any(u["side"] == bt["sides"][k] and u["men"] > 0 and u["state"] in ("steady", "shaken") for u in bt["units"])


def secured(d: Data, bt: dict, side) -> bool:
    """No standing enemy of side within commander.self_play.secure hexes of the (first) objective,
    and none still to come."""
    r, at = d.units["commander"]["self_play"]["secure"], bt["field"]["objective"]
    if to_come(bt, 1 - bt["sides"].index(side)):
        return False
    return not any(u["side"] != side and u["men"] > 0 and u["state"] in STANDING and U.hdist(u["pos"], at) <= r for u in bt["units"])


def to_come(bt: dict, k: int) -> bool:
    """Side k has units still to come on: a later phase's (not fire support), or by air."""
    return (any(not w.get("support") and side_index(bt, w["unit"]) == k for w in bt.get("waiting") or [])
            or any(lf["unit"]["side"] == bt["sides"][k] and lf["left"] > 0 for lf in bt["field"].get("lifts") or []))


def stop_reason(d: Data, bt: dict, held: dict, how: list) -> dict | None:
    """After an exchange of a self-played battle: why it stops, or None; held {side, n}: which
    attacking side held the (first) objective and for how many exchanges running, updated (a
    holding side on its own ground has not taken it; it ends the run only once every phase has begun);
    how: each side's stance (commander.self_play)."""
    P = d.units["commander"]["self_play"]
    gone = [k for k in (0, 1) if not _standing(bt, k) and not to_come(bt, k)]
    lines = U.objective_held(d, bt["units"], bt["field"])
    h = lines[0]["held"] if lines else None
    if not held.get("seen"):                       # who held it after the first exchange: holding it from the start is not taking it
        held["seen"], held["start"] = True, h
    elif h != held.get("start"):                   # once it has changed hands, taking it counts
        held["start"] = None
    o = h if h is not None and h != held.get("start") and how[bt["sides"].index(h)] == "attack" and secured(d, bt, h) else None
    if o is None:
        held["n"] = 0
    elif o == held["side"]:
        held["n"] += 1
    else:
        held["n"] = 1
    held["side"] = o
    if gone:
        return {"why": "gone", "sides": gone}
    if held["n"] >= P["held"] and not phases_to_come(bt):
        return {"why": "held", "side": o}
    if bt["exchange"] - 1 >= play_limit(d, bt):
        return {"why": "limit"}
    return None


def phases_to_come(bt: dict) -> bool:
    """A phase of the battlefield's account has still to begin: holding the objective does not end
    a self-played run yet."""
    return any(s["at"] >= bt["exchange"] for s in bt.get("stages") or [])


def play_limit(d: Data, bt: dict) -> int:
    """The exchanges a self-played battle runs at most: the limit, or after_phases past its last
    phase's start, or as long as the battlefield's account says it was fought (ends) if later;
    never more than most."""
    P = d.units["commander"]["self_play"]
    last = max([0] + [s["at"] for s in bt.get("stages") or []])
    return max(P["limit"], min(P["most"], max(last + P["after_phases"] if last else 0, bt.get("ends") or 0)))


def stances(d: Data, fid: str | None) -> list:
    """A self-played battle's stances: the side the battlefield's objective names attacks and the
    other holds; else its stances as fought (a field with no objective); else both attack."""
    F = d.fields.get(fid) or {} if fid else {}
    o = F.get("objective")
    if o:
        return ["attack" if k == o["side"] else "hold" for k in (0, 1)]
    return list(F["stances"]) if F.get("stances") else ["attack", "attack"]


def crews(d: Data, bt: dict) -> list:
    """Each fire-support battery with crews (not aircraft), as a unit for the after-battle reckoning."""
    kinds = d.units["indirect"]["kinds"]
    return [{"id": f"sup{k}", "name": b["name"], "side": b["side"], "men": b["crew"], "start": b["crew"] + (b.get("crew_down") or 0),
             "down": b.get("crew_down") or 0, "dead": b.get("crew_dead") or 0, "hurt": b.get("hurt") or {}, "state": "steady", "heroes": []}
            for k, b in enumerate(_support(bt)) if not (kinds.get(b["kind"]) or {}).get("air") and isinstance(b.get("crew"), int) and not isinstance(b.get("crew"), bool)]


def after_all(d: Data, bt: dict) -> list:
    """Every unit, the men still aboard carriers too, and the batteries' crews."""
    return bt["units"] + [u["riders"] for u in bt["units"] if u.get("riders")] + crews(d, bt)


def side_medevac(d: Data, bt: dict, k: int) -> str | None:
    """Side k's medevac kind (its war's, helicopters falling back without a zone or a helicopter left), or None."""
    left = False
    if d.units.get("heliborne"):
        H = U.helos(d, bt["field"], bt["sides"][k])
        left = H["aircraft"] - (H.get("damaged") or 0) - (H.get("downed") or 0) > 0
    return U.medevac_kind(d, bt["table"], len(bt["field"].get("lz") or []) > 0, left)


def after_battle(d: Data, bt: dict, care: list, evac: list, rng) -> dict:
    """The battle over: each unit's aftermath (care, evac: per unit) and the heroes' fates, applied."""
    every = after_all(d, bt)
    am = U.aftermath(d, every, care, rng, evac)
    after = [{"id": u["id"], "killed": u.get("dead") or 0, **am[i], **({"taken": u["taken"]} if u.get("taken") else {})} for i, u in enumerate(every)]   # taken: its men who surrendered
    fates = U.hero_fates(d, bt["units"], bt["table"], rng)
    for f in fates:
        for h in (x for x in bt["units"][f["unit"]]["heroes"] if x["id"] == f["hero"]):
            if f["fate"] == "killed":
                h["state"] = "dead"
            elif f["fate"] == "prisoner":
                h["state"] = "prisoner"
            h["fate"] = f["fate"]
    bt["phase"] = "over"
    return {"all": every, "after": after, "fates": fates}


STANDING = ("steady", "shaken")


def points_base(d: Data, bt: dict) -> dict:
    """The state turning points are measured from: each unit's state by id, and who held each objective."""
    return {"states": {u["id"]: u["state"] for u in bt["units"]}, "held": [o["held"] for o in U.objective_held(d, bt["units"], bt["field"])]}


def commits_of(bt: dict, orders: list) -> list:
    """The reserve units a commander's orders committed, by id."""
    return [bt["units"][o["unit"]]["id"] for o in orders if o["act"] == "commit" and o["unit"] < len(bt["units"])]


def _side_points(bt: dict, base: dict, commits: list) -> list:
    """Each side's units broken or fled since base, and its reserves committed."""
    out = []
    for k, side in enumerate(bt["sides"]):
        mine = [u for u in bt["units"] if u["side"] == side and u["id"] in base["states"]]
        broke = [u["id"] for u in mine if base["states"][u["id"]] in STANDING and u["state"] not in STANDING]
        fled = [u["id"] for u in mine if base["states"][u["id"]] != "fled" and u["state"] == "fled"]
        if broke or fled:
            out.append({"kind": "broke", "side": k, "units": broke, "fled": fled})
        c = [x for x in commits if any(u["id"] == x and u["side"] == side for u in bt["units"])]
        if c:
            out.append({"kind": "commit", "side": k, "units": c})
    return out


def turning_points(d: Data, bt: dict, base: dict, stages: dict | None, commits: list) -> list:
    """Since base: phases begun (and who came on), units broken or fled by side, objectives taken
    or lost, reserves committed (ids by side)."""
    lights, skies = (stages or {}).get("light") or {}, (stages or {}).get("weather") or {}
    out = [{"kind": "phase", "stage": i, "came": [bt["units"][k]["id"] for k in stages.get("came", [])], **({"light": lights[i]} if i in lights else {}), **({"weather": skies[i]} if i in skies else {})}
           for i in (stages or {}).get("begun", [])]
    out += _side_points(bt, base, commits)
    for i, o in enumerate(U.objective_held(d, bt["units"], bt["field"])):
        was = base["held"][i] if i < len(base["held"]) else None
        if o["held"] != was:
            out.append({"kind": "objective", "second": bool(o.get("second")), "held": o["held"], "was": was})
    return out


def end_point(d: Data, bt: dict, stop: dict | None, every: list, after: list) -> dict:
    """The battle's end, as a turning point: why it stopped (None: the GM ended it), each side's men
    killed, left on the field, died of wounds, carried to camp, and units still standing."""
    sides = []
    for side in bt["sides"]:
        rows = [(u, a) for u, a in zip(every, after) if u["side"] == side]
        sides.append({"start": sum(u.get("start") or 0 for u, _ in rows), "killed": sum(a["killed"] for _, a in rows),
                      "left": sum(a["left"] for _, a in rows), "died": sum(a["died"] for _, a in rows),
                      "carried": sum(len(a["cases"]) for _, a in rows), "taken": sum(a.get("taken", 0) for _, a in rows),
                      "standing": sum(1 for u in bt["units"] if u["side"] == side and u["men"] > 0 and u["state"] in STANDING)})
    return {"kind": "end", "exchanges": bt["exchange"] - 1, "stop": stop, "sides": sides,
            "held": [o["held"] for o in U.objective_held(d, bt["units"], bt["field"])]}


def self_play(d: Data, fid: str, rng, how: list | None = None, planner: bool = False) -> dict:
    """A battlefield played to its end by the commander on both sides: {battle, stop, orders, after, fates, points};
    planner: it plans for itself on a side with no written plan."""
    bt = set_up(d, fid, planner)
    st, mem, held = how or stances(d, fid), [{"n": -1, "mem": {}}, {"n": -1, "mem": {}}], {"side": None, "n": 0}
    opening = begin(d, bt, rng)
    points, stop, orders, base = [], None, 0, points_base(d, bt)
    first = turning_points(d, bt, base, opening["stages"], [])
    if first:
        points.append({"exchange": 0, "points": first})
    while not stop:
        ex, commits, stages = bt["exchange"], [], None
        for k in (0, 1):
            o = command_move(d, bt, st[k], mem[k], rng)
            orders += len(o)
            commits += commits_of(bt, o)
            stages = end_move(d, bt, rng)["stages"] or stages
        pts = turning_points(d, bt, base, stages, commits)
        if pts:
            points.append({"exchange": ex, "points": pts})
        base = points_base(d, bt)
        stop = stop_reason(d, bt, held, st)
    every = after_all(d, bt)
    evac = [side_medevac(d, bt, 0), side_medevac(d, bt, 1)]
    r = after_battle(d, bt, ["field"] * len(every), [evac[side_index(bt, u)] for u in every], rng)
    points.append({"exchange": bt["exchange"] - 1, "points": [end_point(d, bt, stop, every, r["after"])]})
    return {"battle": bt, "stop": stop, "orders": orders, "after": r["after"], "fates": r["fates"], "points": points}


STOP_TEXT = {"gone": "no unit left standing", "held": "the objective taken and held", "limit": "the exchange limit reached"}


def summary(d: Data, r: dict) -> list:
    """A self-played battle in a few lines: why it stopped, after how many exchanges, and each
    side's men: at the start, killed, left on the field, died of wounds, carried to camp, and
    still standing."""
    bt, P = r["battle"], d.units["commander"]["self_play"]
    st = r["stop"]
    why = {"gone": lambda: " and ".join(bt["sides"][k] for k in st["sides"]) + " with no unit left standing",
           "held": lambda: f"{st['side']} took the objective and held it {P['held']} exchanges running",
           "limit": lambda: f"{play_limit(d, bt)} exchanges fought"}[st["why"]]()
    out = [f"Stopped after {bt['exchange'] - 1} exchanges: {why}. {r['orders']} orders given."]
    every = after_all(d, bt)
    for k, side in enumerate(bt["sides"]):
        rows = [(u, a) for u, a in zip(every, r["after"]) if u["side"] == side]
        n = {"start": sum(u.get("start", 0) for u, _ in rows), "killed": sum(a["killed"] for _, a in rows),
             "left": sum(a["left"] for _, a in rows), "died": sum(a["died"] for _, a in rows), "carried": sum(len(a["cases"]) for _, a in rows)}
        up = sum(1 for u in bt["units"] if u["side"] == side and u["men"] > 0 and u["state"] in ("steady", "shaken"))
        out.append(f"  {side}: {n['start']} men; {n['killed']} killed, {n['left']} left on the field, {n['died']} died of wounds, "
                   f"{n['carried']} wounded carried to camp; {up} unit(s) still standing")
    return out


def _names(bt: dict, ids: list) -> str:
    by_id = {u["id"]: u["name"] for u in bt["units"]}
    return ", ".join(by_id[i] for i in ids if i in by_id)


def _phase_text(bt: dict, p: dict) -> str:
    came, light = _names(bt, p["came"]), p.get("light")
    return f"Phase {p['stage'] + 1} of {len(bt['stages'])}: {bt['stages'][p['stage']]['name']}." + (f" The light: {light}." if light else "") + (f" Coming on: {came}." if came else "")


def _broke_text(bt: dict, p: dict) -> str:
    side = bt["sides"][p["side"]]
    bits = [f"{side}: {_names(bt, p['units'])} broke." if p["units"] else "", f"{side}: {_names(bt, p['fled'])} fled the field." if p["fled"] else ""]
    return " ".join(x for x in bits if x)


def _objective_text(bt: dict, p: dict) -> str:
    what = "the second objective" if p["second"] else "the objective"
    if not p["held"]:
        return f"{p['was']} no longer held {what}."
    return f"{p['held']} took {what}" + (f" from {p['was']}." if p["was"] else ".")


POINT_TEXT = {"phase": _phase_text, "broke": _broke_text, "objective": _objective_text,
              "commit": lambda bt, p: f"{bt['sides'][p['side']]} committed {_names(bt, p['units'])} from the reserve.",
              "end": lambda bt, p: f"The battle ended after {p['exchanges']} exchanges."}


def points_text(r: dict) -> list:
    """A self-played battle's turning points in plain words, a line an exchange (the page tells them
    the same way in its narrative)."""
    bt = r["battle"]
    return [f"  {'Exchange ' + str(x['exchange']) if x['exchange'] else 'The opening'}: " + " ".join(POINT_TEXT[p["kind"]](bt, p) for p in x["points"])
            for x in r["points"]]
