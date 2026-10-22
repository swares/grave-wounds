"""Character-scale hazards (data/hazards.yaml): who can swim, swimming and drowning, cold water,
fords on the travel map, climbing, falls and chases. The pages (templates/ranks.js) repeat
swim_ability, swim_target, swim_step, ford_risk, climb_target, fall and chase_step exactly, taking
the dice in the same order."""
from __future__ import annotations

from .checks import check, opposed
from .model import Data


def _cfg(d: Data) -> dict:
    return d.hazards or {}


def swim_ability(d: Data, eid: str, seamanship: int, roll: int) -> str:
    """none, basic or strong: d100 against his era's shares; Seamanship lifts it."""
    H = _cfg(d)
    sh = (H.get("swimmers") or {}).get(eid, {"none": 50, "strong": 10})
    a = "basic"
    if roll <= sh["none"]:
        a = "none"
    elif roll > 100 - sh["strong"]:
        a = "strong"
    if seamanship >= H.get("seamanship_strong", 40):
        return "strong"
    if seamanship >= H.get("seamanship_basic", 20) and a == "none":
        return "basic"
    return a


def swim_target(d: Data, end: int, ability: str, band: int, armour: str, current: str, flotation: bool = False,
                minutes: int = 0, cold: int = 0) -> int:
    """What he swims at this minute: Endurance + ability + load + armour + current (+ flotation),
    less 10 for each 10 minutes past the water's fail_after."""
    S = _cfg(d)["swim"]
    t = end + S["ability"][ability] + S["load"][band] + S["armour"].get(armour, 0) + S["current"].get(current, 0)
    if flotation:
        t += S["flotation"]
    over = minutes - _cfg(d)["cold"][cold]["fail_after"]
    if over > 0:
        t -= 10 * (over // 10 + 1)
    return t


def swim_step(d: Data, step: int, target: int, roll: int) -> dict:
    """A minute in the water: held, up a step on a critical, down one on a failure, two on a fumble.
    -> {"check", "step"} (step 4 is drowned)"""
    k = check(d, target, "ordinary", roll)
    last = len(_cfg(d)["swim"]["steps"]) - 1
    if k["success"]:
        new = max(0, step - 1) if k["critical"] else step
    else:
        new = min(last, step + (2 if k["fumble"] else 1))
    return {"check": k, "step": new}


def cold_shock(d: Data, nerve: int, cold: int, roll: int) -> dict:
    """The first minute in cold water: a Nerve check at the water's shock; failing, a step down."""
    return check(d, nerve + _cfg(d)["cold"][cold]["shock"], "ordinary", roll)


def ford_risk(d: Data, water: str, band: int) -> str | None:
    """The difficulty a man of this load band crosses at, or None if this water is no risk to him."""
    F = _cfg(d)["fords"][water]
    return F["difficulty"] if band >= F["from_band"] else None


def climb_target(d: Data, agi: int, fieldcraft: int, surface: str, band: int, armour: str) -> int:
    C = _cfg(d)["climb"]
    return agi + fieldcraft // 2 + C["surfaces"][surface]["mod"] + C["load"][band] + C["armour"].get(armour, 0)


def climb_steps(d: Data, surface: str, height: float) -> int:
    """How many checks a climb of `height` m takes."""
    s = _cfg(d)["climb"]["surfaces"][surface]["step_m"]
    return max(1, -(-int(height) // s))


def fall(d: Data, height: float, landing: str, shift: int, roll: int, loc_roll: int) -> dict:
    """A fall from `height` m: the severity on its row (shifted `shift` rows heavier, or lighter if
    negative), the wound's severity, and the zone it lands in.
    -> {"severity", "wound" (light | serious | critical | None), "zone"}"""
    F = _cfg(d)["falls"]
    rows = F["heights"]
    i = next(k for k, r in enumerate(rows) if height <= r["upto"])
    i = min(len(rows) - 1, max(0, i + shift))
    sev_i = next((k for k, b in enumerate(rows[i]["bands"]) if roll <= b), len(rows[i]["bands"]))
    sev = F["severities"][sev_i]
    zone = next(z for to, z in F["landings"][landing]["zones"] if loc_roll <= to)
    return {"severity": sev, "wound": F["wound"].get(sev), "zone": zone if sev != "none" else None}


def chase_step(d: Data, gap: int, a_target: int, a_roll: int, b_target: int, b_roll: int, a_speed: float, b_speed: float) -> dict:
    """A round of a chase: pursuer a against quarry b, opposed; the winner moves the gap a band (two
    on a critical); both failing, or a tie, goes to the faster. -> {"gap", "opposed"}"""
    C = _cfg(d)["chase"]
    o = opposed(d, a_target, "ordinary", a_roll, b_target, b_roll)
    a, b = o["a"], o["b"]
    if o["winner"] == "a":
        move = -(2 if a["critical"] else 1)
    elif b["success"] and not (a["success"] and a["margin"] == b["margin"] and a["critical"] == b["critical"]):
        move = 2 if b["critical"] else 1
    else:
        move = (b_speed > a_speed) - (a_speed > b_speed)   # a tie to the faster
    return {"gap": min(len(C["gaps"]) - 1, max(0, gap + move)), "opposed": o}
