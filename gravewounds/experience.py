"""Experience in play (data/experience.yaml). A skill a man uses well is ticked (a job term's
check that succeeds, a hit or a parry or dodge in the roller, Fieldcraft, Leechcraft, Stealth and
Watch on the travel map, first aid in the roller); the pages keep the ticks and the days he has served in a shared store
(templates/xp.js). At the end of a season the GM settles them on the team builder:

- each ticked skill, in the era's skill order, rolls d100; over the skill, it rises by the
  `gain` die (1d3), never past the era's skill_max;
- the days served are added to his count, and each full term of days (the era's age per_term
  years) gives him a later term's gains (term_main to his career's main skill, term_second to its
  second) and its years of age.

The team builder page (templates/team.js) repeats season exactly, taking the dice in the same
order: each ticked skill's d100, then its gain die when it rises."""
from __future__ import annotations

from .model import Data
from .team import era, finish


def term_days(d: Data, eid: str) -> int:
    """How many days served make a term in play: the era's years of age a term, in days."""
    return era(d, eid)["age"]["per_term"] * d.experience.get("days_a_year", 365)


def _career(T: dict, cid: str) -> dict:
    return next(c for c in T["careers"] if c["id"] == cid)


def season(d: Data, c: dict, ticks, served: int, rng) -> dict:
    """End of season for character `c` (changed in place): his ticked skills roll to rise, then
    `served` days are added toward his next term.
    -> {"rolls": [{"skill", "roll", "was", "gain"}], "terms": terms completed, "served": days now
        toward the next}"""
    T = era(d, c["era"])
    lo, hi = d.experience.get("gain", [1, 3])
    rolls = []
    for s in [s["id"] for s in T["skills"] if s["id"] in set(ticks)]:
        was, roll = c["skills"][s], rng.randint(1, 100)
        gain = rng.randint(lo, hi) if roll > was and was < T["skill_max"] else 0
        if gain:
            c["gains"][s] = c["gains"].get(s, 0) + gain
            finish(d, c)
        rolls.append({"skill": s, "roll": roll, "was": was, "gain": c["skills"][s] - was})
    c["served"] = c.get("served", 0) + max(0, served)
    per, done = term_days(d, c["era"]), 0
    while c["served"] >= per:
        c["served"] -= per
        car = _career(T, c["career"])
        c["gains"][car["main"]] = c["gains"].get(car["main"], 0) + T["term_main"]
        c["gains"][car["second"]] = c["gains"].get(car["second"], 0) + T["term_second"]
        c["age"] = c.get("age", 0) + T["age"]["per_term"]
        c["xp_terms"] = c.get("xp_terms", 0) + 1
        done += 1
    if done:
        finish(d, c)
    return {"rolls": rolls, "terms": done, "served": c["served"]}
