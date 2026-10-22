"""Rank, pay, promotion and loot (data/ranks.yaml). The team builder page (templates/team.js)
repeats start_rank, pay_of, wage, promote, loot, standing and wealth exactly, taking the dice in
the same order.

- Rank: each era's ladder, lowest first; a career may start higher (a sergeant, an officer).
- Wage: each day his force is fed by its army he earns his rank's pay (times his career's, and
  what is left after stoppages: `kept`), in Days; a day in arrears is owed instead.
- Promotion: a vacancy at a rank goes to the men one below, most senior first, who have served
  its years (or did a deed) and can read where it asks; each rolls Command at its difficulty
  until one succeeds, and his old rank falls vacant in turn.
- Loot: a d100 find (a sack adds to the roll), less the era's share for captain or hospital;
  where it is forbidden or past the era's cap, the provost's Watch against his Stealth: caught,
  he loses it, and on the provost's critical or his own fumble the era's punishment follows. Prize money: his rank's shares; a ransom; horses taken.
- Honours (the Plains nations): coups and horses taken build standing; horses are wealth."""
from __future__ import annotations

import math

from .checks import check, opposed
from .model import Data

KINDS = ("field", "sack", "sack_after", "prize", "ransom", "horses")


def _q(x: float) -> float:
    """To the nearest quarter Day, halves up."""
    return math.floor(x * 4 + 0.5) / 4


def era(d: Data, eid: str) -> dict | None:
    return (d.ranks.get("eras") or {}).get(eid)


def ladder(d: Data, eid: str) -> list[dict]:
    return (era(d, eid) or {}).get("ladder") or []


def rank_index(d: Data, eid: str, rid: str | None) -> int:
    ids = [r["id"] for r in ladder(d, eid)]
    return ids.index(rid) if rid in ids else 0


def start_rank(d: Data, eid: str, career: str) -> str | None:
    """The rank a career starts at: its `start`, or the bottom of the ladder (None: no ranks)."""
    L = ladder(d, eid)
    if not L:
        return None
    return (era(d, eid).get("start") or {}).get(career) or L[0]["id"]


def pay_of(d: Data, eid: str, region: str, career: str, rid: str) -> float:
    """His day's pay as a multiple of a private's: his rank's (his army's where it differs),
    times his career's."""
    E, i = era(d, eid) or {}, rank_index(d, eid, rid)
    L = ladder(d, eid)
    if not L:
        return 0
    by = (E.get("pay_by") or {}).get(region)
    base = by[i] if by else L[i]["pay"]
    return base * (E.get("career_pay") or {}).get(career, 1)


def wage(d: Data, eid: str, region: str, career: str, rid: str, days: int) -> float:
    """What `days` with his army earn him, in Days to the quarter, after stoppages."""
    E = era(d, eid) or {}
    return _q(days * pay_of(d, eid, region, career, rid) * E.get("kept", 1))


def eligible(d: Data, eid: str, c: dict, idx: int) -> tuple[bool, str | None]:
    """Can man `c` be promoted to rank `idx`: one below it, served its years (or a deed), able to
    read where it asks, and for a deed-only rank, a deed."""
    L, R = ladder(d, eid), d.ranks
    r = L[idx]
    if c.get("course_rank") == r["id"] and rank_index(d, eid, c.get("rank")) < idx:   # an officer's course opens it
        return True, None
    if rank_index(d, eid, c.get("rank")) != idx - 1:
        return False, "not the rank below"
    if r.get("deed_only") and not c.get("deed"):
        return False, "only for a deed"
    if not c.get("deed") and c.get("rank_days", 0) < r.get("years", 0) * R.get("days_a_year", 365):
        return False, "too soon"
    if r.get("letters") and c["skills"].get("letters", 0) < R.get("literate", 20):
        return False, "cannot read and write"
    return True, None


def _presence(R: dict, c: dict) -> None:
    """A promotion's Presence (ranks.yaml presence), into his characteristics' changes, up to the cap."""
    P = R.get("presence")
    if not P or "stat_mods" not in c:
        return
    gain = min(P["per_rank"], P["cap"] - c.get("pres_rank", 0))
    if gain > 0:
        c["stat_mods"]["pres"] = c["stat_mods"].get("pres", 0) + gain
        c["pres_rank"] = c.get("pres_rank", 0) + gain


def promote(d: Data, eid: str, team: list[dict], vacancies: dict, rng) -> list[dict]:
    """End of season's promotions (team and vacancies changed in place): from the top rank down,
    each vacancy is offered to the eligible men below, most senior first (rank_days, then their
    order on the team), each rolling Command until one succeeds. Deeds are then spent.
    -> [{"name", "to", "roll", "target", "success"}] every roll made"""
    L, R, out = ladder(d, eid), d.ranks, []
    for idx in range(len(L) - 1, 0, -1):
        r = L[idx]
        while vacancies.get(r["id"], 0) > 0:
            cands = [c for c in team if eligible(d, eid, c, idx)[0]]
            cands.sort(key=lambda c: -c.get("rank_days", 0))
            won = None
            for c in cands:
                mod = (R.get("deed_bonus", 20) if c.get("deed") else 0)
                if c.get("patron_help"):          # his patron's word (data/patrons.yaml)
                    mod += (d.patrons or {}).get("promotion_bonus", 20)
                if r.get("unlettered") and c["skills"].get("letters", 0) < R.get("literate", 20):
                    mod += r["unlettered"]
                k = check(d, c["skills"].get("command", 0) + mod, r.get("diff", "ordinary"), rng.randint(1, 100))
                out.append({"name": c["name"], "to": r["id"], "roll": k["roll"], "target": k["target"], "success": k["success"]})
                if k["success"]:
                    won = c
                    break
            if not won:
                break
            old = rank_index(d, eid, won.get("rank"))      # the rank he leaves (one below, or lower for a course's)
            won["rank"], won["rank_days"], won["deed"], won["patron_help"] = r["id"], 0, False, False
            won.pop("course_rank", None)
            _presence(R, won)
            vacancies[r["id"]] -= 1
            if old > 0:
                vacancies[L[old]["id"]] = vacancies.get(L[old]["id"], 0) + 1
    for c in team:
        c["deed"] = False
    return out


def loot(d: Data, eid: str, kind: str, c: dict, rng) -> dict:
    """One man's loot of a `kind` (field, sack, sack_after, prize, ransom, horses).
    -> {"kind", "roll", "what", "found", "risk", "opposed", "caught", "punished", "days", "horses", "why"}"""
    R = d.ranks
    L = (R.get("loot") or {}).get(eid) or {}
    out = {"kind": kind, "roll": None, "what": "", "found": 0, "risk": False, "opposed": None, "caught": False, "punished": False,
           "days": 0, "horses": 0, "why": ""}
    if kind == "prize":
        P = L.get("prize")
        if P:
            sh = ladder(d, eid)[rank_index(d, eid, c.get("rank"))].get("shares", 1)
            out.update(what=f"{sh:g} share{'s' if sh != 1 else ''} of prize money", found=_q(P["share_days"] * sh), days=_q(P["share_days"] * sh), why=P.get("why", ""))
        return out
    if kind == "horses":
        H = L.get("horses")
        if H:
            n = rng.randint(H["per_raid"][0], H["per_raid"][1])
            out.update(what=f"{n} horse{'s' if n != 1 else ''} taken" if n else "no horses taken", horses=n, why=H.get("why", ""))
        return out
    if kind == "ransom":
        X = L.get("ransom")
        if X:
            v = rng.randint(X["days"][0], X["days"][1])
            out.update(what="a prisoner ransomed", found=v, days=_q(v * L.get("keep", 1)), why=X.get("why", ""))
        return out
    rules = L.get("sack" if kind in ("sack", "sack_after") else "field") or {"allowed": False}
    roll = rng.randint(1, 100)
    look = 100 if roll == 100 else min(99, roll + (R.get("sack_bonus", 0) if kind in ("sack", "sack_after") else 0))   # a windfall only on 100
    row = next(f for f in R["finds"] if look <= f["to"])
    v = rng.randint(row["days"][0], row["days"][1]) if row["days"][1] > 0 else 0
    out.update(roll=roll, what=row["what"], found=v, why=rules.get("why", ""))
    if v <= 0:
        return out
    forbidden = kind == "sack_after" or not rules.get("allowed")
    if forbidden or (rules.get("cap") is not None and v > rules["cap"]):
        o = opposed(d, rules.get("provost", 50), "ordinary", rng.randint(1, 100), c["skills"].get("stealth", 0), rng.randint(1, 100))
        caught = o["winner"] == "a"
        out.update(risk=True, opposed=o, caught=caught, punished=caught and (o["a"]["critical"] or o["b"]["fumble"]))
        if out["caught"]:
            return out
    out["days"] = _q(v * L.get("keep", 1))
    return out


def purchase_price(d: Data, eid: str, region: str, c: dict, rid: str) -> int | None:
    """What buying rank rid costs him (the coin's smallest unit): its regulation price, less the
    one he holds (c["bought"]); None where commissions were not bought, or rid has no price."""
    P = (d.ranks or {}).get("purchase") or {}
    if eid not in P.get("eras", []) or region not in P.get("regions", []) or rid not in P.get("prices", {}):
        return None
    held = P["prices"].get(c.get("bought"), 0) if c.get("bought") else 0
    return max(0, P["prices"][rid] - held)


def can_buy(d: Data, eid: str, region: str, c: dict, vacancies: dict) -> tuple[str | None, str | None]:
    """(the rank he may buy, None) or (None, why not): the next rank with a price, vacant, and his
    eligibility but for the years (an ensigncy needs no rank below: a gentleman bought in)."""
    L = ladder(d, eid)
    i = rank_index(d, eid, c.get("rank"))
    for idx in range(i + 1, len(L)):
        rid = L[idx]["id"]
        if purchase_price(d, eid, region, c, rid) is None:
            continue
        if vacancies.get(rid, 0) <= 0:
            return None, f"no vacancy for {L[idx]['name'].lower()}"
        ok, why = eligible(d, eid, c, idx)
        first = idx == min(k for k, r in enumerate(L) if r["id"] in d.ranks["purchase"]["prices"])
        if ok or why == "too soon" or (first and why == "not the rank below"):
            return rid, None
        return None, why
    return None, "nothing to buy"


def standing(d: Data, honours: int) -> str:
    """A Plains man's standing by his honours."""
    rows = (d.ranks.get("honours") or {}).get("standing") or [{"from": 0, "name": ""}]
    return [r for r in rows if honours >= r["from"]][-1]["name"]


def wealth(d: Data, horses: int) -> str:
    """And his wealth by his horses."""
    rows = (d.ranks.get("honours") or {}).get("wealth") or [{"from": 0, "name": ""}]
    return [r for r in rows if horses >= r["from"]][-1]["name"]
