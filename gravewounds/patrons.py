"""Standing with patrons (data/patrons.yaml). The team builder (templates/ranks.js) repeats band,
favour, move, rival, fate and client exactly, taking the dice in the same order.

- Standing: d100 with each patron, read in bands.
- A favour: d100 at Standing + Persuade / 10, at the favour's difficulty; granted, it spends its
  cost (a critical spends nothing); a fumble offends him.
- Events move Standing; changing sides sets it to 0 and makes him an enemy.
- Each End of season the patron's fate by era; then each client's by that fate."""
from __future__ import annotations

from .checks import check, opposed
from .model import Data


def _cfg(d: Data) -> dict:
    return d.patrons or {}


def _clamp(d: Data, v: int) -> int:
    return max(0, min(_cfg(d).get("max", 95), v))


def band(d: Data, v: int) -> str:
    return [b for b in _cfg(d)["bands"] if v >= b["from"]][-1]["name"]


def favour_row(d: Data, fid: str) -> dict:
    return next(f for f in _cfg(d)["favours"] if f["id"] == fid)


def favour(d: Data, standing: int, persuade: int, fid: str, roll: int) -> dict:
    """Asking favour fid. -> {"check", "granted", "offended", "standing" (after)}"""
    P, F = _cfg(d), favour_row(d, fid)
    k = check(d, standing + persuade // P.get("persuade_div", 10), F["difficulty"], roll)
    after = standing
    if k["success"] and not (k["critical"] and P.get("critical_free", True)):
        after = standing - F["cost"]
    elif k["fumble"]:
        after = standing + P.get("offended", -10)
    return {"check": k, "granted": k["success"], "offended": k["fumble"], "standing": _clamp(d, after)}


def move(d: Data, standing: int, event: str, rng, amount: float = 0) -> dict:
    """An event: -> {"standing", "enemy"}. Dice: a deed's d10 (`dice`)."""
    E = _cfg(d)["events"][event]
    if "to" in E:
        return {"standing": E["to"], "enemy": bool(E.get("enemy"))}
    if "dice" in E:
        add = rng.randint(E["dice"][0], E["dice"][1])
    elif "per_days" in E:
        add = int(amount // E["per_days"])
    elif "per" in E:
        add = int(amount) * E["per"]
    else:
        add = E.get("add", 0)
    return {"standing": _clamp(d, standing + add), "enemy": False}


def rival(d: Data, a: int, b: int, a_roll: int, b_roll: int) -> dict:
    """Two clients wanting one favour or one vacancy: opposed Standing (a asks, b holds)."""
    return opposed(d, a, "ordinary", a_roll, b, b_roll)


def fate(d: Data, eid: str, roll: int) -> str | None:
    """The patron's fate this season: the first row whose running total the d100 is at or under."""
    acc = 0
    for r in (_cfg(d).get("fate") or {}).get(eid, []):
        acc += r["chance"]
        if roll <= acc:
            return r["id"]
    return None


def fate_name(d: Data, eid: str, fid: str) -> str:
    row = next((r for r in (_cfg(d).get("fate") or {}).get(eid, []) if r["id"] == fid), {})
    return row.get("name") or _cfg(d)["fates"][fid]["name"]


def client(d: Data, fid: str, standing: int, roll: int | None = None, follow: bool = True) -> dict:
    """A client's lot when his patron's fate is fid. -> {"standing", "result"}
    heir / half: half Standing; ruin: d100 at or under Standing shares the fall (0), else half;
    choose: follows (kept) or stays (0)."""
    how = _cfg(d)["fates"][fid]["clients"]
    if how == "ruin":
        if roll is not None and roll <= standing:
            return {"standing": 0, "result": "ruined"}
        return {"standing": standing // 2, "result": "clear"}
    if how == "choose":
        return {"standing": standing, "result": "follows"} if follow else {"standing": 0, "result": "stays"}
    return {"standing": standing // 2, "result": how}
