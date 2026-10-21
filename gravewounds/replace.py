"""Replacing a team's losses (data/replacements/<era>.yaml). A man is lost (killed, dead of his
wounds or of disease, taken prisoner, deserted, sent home) and the team fills the gap one of
three ways:

- roll: a new member rolled like any other, of the lost man's career and terms;
- assigned: the army sends a man through its own system (a reinforcement draft, a replacement
  depot, a recruit from the regiment's depot). He costs nothing, comes with the system's usual
  experience (`terms`) and arrives after its wait in days (`wait`, low-high);
- hire: the team engages a man (a mercenary, a substitute, a contractor) where the place
  allows. He comes with `terms` (low-high; the GM picks) and costs `cost` Days, plus `per_term`
  for each term past the lowest, from a purse.

A lost man's purse follows the era's practice (`effects`): share (his comrades divide it),
heirs (it goes home to his family) or lost (it goes with him, or is given away). The GM may
choose another. The team builder page (templates/team.js) repeats options, hire_cost and
settle exactly."""
from __future__ import annotations

from .model import Data

LOST_WHY = ("killed", "died of wounds", "died of disease", "taken prisoner", "deserted", "sent home")
PRACTICES = ("share", "heirs", "lost")


def replacements(d: Data, eid: str) -> dict:
    """An era's replacements file, or an empty one."""
    return d.replacements.get(eid) or {"assigned": [], "hire": [], "effects": {"default": {"practice": "heirs", "what": ""}}}


def _for(row: dict, region: str) -> bool:
    return not row.get("regions") or region in row["regions"]


def _careers(d: Data, eid: str, row: dict) -> list[str]:
    allowed = row.get("careers", "any")
    return [c["id"] for c in d.teams[eid]["careers"] if allowed == "any" or c["id"] in allowed]


def options(d: Data, eid: str, region: str, place: str | None, career: str, terms: int) -> list[dict]:
    """The ways to replace a man of `career` and `terms` lost from an army of `region`, with the
    team at `place` (town, city, village, camp, road, frontier, sea; None: anywhere): rolling a new
    man first, then the army's assigned replacements for that region, then the men to be hired
    there. -> [{"kind", "id", "name", "careers", "terms": [lo, hi], "wait": [lo, hi] or None,
                "cost": Days or None, "per_term", "what"}]"""
    R, out = replacements(d, eid), [{"kind": "roll", "id": "roll", "name": "Roll a new member", "careers": [career],
                                      "terms": [terms, terms], "wait": None, "cost": None, "per_term": 0,
                                      "what": "A new man of the same career and terms, rolled like any other."}]
    for kind in ("assigned", "hire"):
        for r in R.get(kind, []):
            if not _for(r, region) or (place and r.get("places") and place not in r["places"]):
                continue
            cs = _careers(d, eid, r)
            if not cs:
                continue
            t = r["terms"] if isinstance(r["terms"], list) else [r["terms"], r["terms"]]
            out.append({"kind": kind, "id": r["id"], "name": r["name"], "careers": cs, "terms": t,
                        "wait": r.get("wait") if kind == "assigned" else None,
                        "cost": r.get("cost", 0) if kind == "hire" else None, "per_term": r.get("per_term", 0) if kind == "hire" else 0,
                        "what": r.get("what", "")})
    return out


def pick_career(opt: dict, career: str) -> str:
    """The career an option fills the gap with: the lost man's where it allows it, else its first."""
    return career if career in opt["careers"] else opt["careers"][0]


def hire_cost(opt: dict, terms: int) -> float:
    """What hiring costs, in Days: its cost, plus per_term for each term past its lowest."""
    return (opt["cost"] or 0) + (opt.get("per_term") or 0) * max(0, terms - opt["terms"][0])


def effects(d: Data, eid: str, region: str) -> dict:
    """The era's practice with a lost man's purse, for his army. -> {"practice", "what", ...}"""
    E = replacements(d, eid).get("effects") or {}
    return {**(E.get("default") or {"practice": "heirs", "what": ""}), **((E.get("regions") or {}).get(region) or {})}


def settle(left: float, survivors: int, practice: str) -> dict:
    """What becomes of a lost man's `left` Days: shared among `survivors` (each gets an equal part;
    with no survivors it is lost), or gone to his heirs, or lost.
    -> {"each": Days for each survivor, "gone": Days out of the team}"""
    left = max(0.0, left)
    if practice == "share" and survivors > 0:
        return {"each": left / survivors, "gone": 0.0}
    return {"each": 0.0, "gone": left}
