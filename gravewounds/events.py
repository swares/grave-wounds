"""Events on the march and in camp (data/events.yaml): each night of the travel map, a force's
fit men each take the era's chances of deserting, straggling and being injured, its horses of
dying or going lame, and the force a chance of an incident, by what it did that day (camp,
march or withdraw). Deserters and stragglers come off its men; the injured join its wound track
(at the step the `injury` table gives, with a wound-fever day as any wound); lost horses are
reported. An incident is a d100 row of the era's table that may cost men or a step of fatigue.
The travel page (templates/events.js) repeats activity, era_of and day exactly, taking the dice
in the same order: each man's desertion roll, then straggling, then injury (with the injury's
step and fever day as each injury is found), then horses; then the incident chance, the row and
the men it costs."""
from __future__ import annotations

from .model import Data

ACTIVITIES = ("camp", "march", "withdraw")
KINDS = ("desert", "straggle", "injury", "horses")
HORSE_TYPES = ("mounted", "wagons")
MILLION = 1_000_000


def era_of(d: Data, period: str | None, force: dict) -> str | None:
    """The era whose events a force rolls: its own `era`, or its map's period's."""
    return force.get("era") or (d.events.get("periods") or {}).get(period or "")


def activity(marched: float, withdrawing: bool) -> str:
    """What the force did that day: withdraw (the GM's tick), march (it marched at all) or camp."""
    return "withdraw" if withdrawing else ("march" if marched > 0 else "camp")


def _d1e6(rng) -> int:
    """1 to 1,000,000 from three d100 (rng() gives 1-100)."""
    return (rng() - 1) * 10000 + (rng() - 1) * 100 + rng()


def _pick(lo: int, hi: int, rng) -> int:
    return lo + (rng() - 1) % (hi - lo + 1)


def _threshold(rate: float) -> int:
    return int(rate * MILLION + 0.5)


def injury_case(d: Data, rng) -> dict:
    """An injured man's case on the wound track: his step on d100 (events.yaml injury), and his
    wound-fever day as any wound's (disease.yaml wounds.fever_after)."""
    roll = rng()
    step_name = next(r["step"] for r in d.events["injury"] if roll <= r["to"])
    lo, hi = d.disease["wounds"]["fever_after"]
    return {"d": "wound", "inc": 0, "step": d.disease["steps"].index(step_name), "peak": 0, "shown": 0, "chronic": False,
            "inf": "low", "fever": _pick(lo, hi, rng), "injury": True}


def rate(d: Data, era: str, kind: str, act: str, conditions=()) -> float:
    """A chance per man per day: the era's for this activity, times the largest multiplier among
    the force's conditions (events.yaml conditions: hungry, unpaid; they do not stack, since a
    starving army is seldom paid), never above 1."""
    r = (d.events["eras"][era]["rates"].get(kind) or {}).get(act, 0)
    C = d.events.get("conditions") or {}
    return min(1.0, r * max([C.get(c, {}).get(kind, 1) for c in conditions] + [1]))


def horse_march_pct(d: Data, ftype: str, men: int, horses: int | None) -> int:
    """% of its speed a mounted force or wagon train keeps with `horses` left for its `men`
    (events.yaml horses_march: the lowest band it falls under); 100 with enough, or for others."""
    bands = (d.events.get("horses_march") or {}).get(ftype)
    if not bands or horses is None or men <= 0:
        return 100
    pct = 100
    for b in bands:
        if horses < b["below"] * men:
            pct = min(pct, b["pct"])
    return pct


def day(d: Data, era: str, ftype: str, men: int, act: str, rng, horses: int | None = None, conditions=()) -> dict:
    """One night's events for a force of `men` fit men of type `ftype`, after a day of `act`,
    with `horses` horses (None: one a man still with it) and the GM's `conditions`.
    -> {"desert", "straggle", "injury" (count), "cases" (their wound-track cases), "horses",
        "incident" (the row, or None), "incident_lost", "fatigue"}"""
    E = d.events["eras"][era]
    R = E["rates"]
    conditions = list(conditions)
    out = {"desert": 0, "straggle": 0, "injury": 0, "cases": [], "horses": 0, "incident": None, "incident_lost": 0, "fatigue": 0}
    left = men
    for kind in ("desert", "straggle"):
        t = _threshold(rate(d, era, kind, act, conditions))
        n = 0
        if t:
            for _ in range(left):
                if _d1e6(rng) <= t:
                    n += 1
        out[kind] = n
        left -= n
    t = _threshold(rate(d, era, "injury", act, conditions))
    if t:
        for _ in range(left):
            if _d1e6(rng) <= t:
                out["injury"] += 1
                out["cases"].append(injury_case(d, rng))
    if ftype in HORSE_TYPES and "horses" in R:
        t = _threshold(rate(d, era, "horses", act, conditions))
        if t:
            for _ in range(left if horses is None else max(0, horses)):
                if _d1e6(rng) <= t:
                    out["horses"] += 1
    left -= out["injury"]
    if E.get("incident") and rng() <= E["incident"]:
        roll = rng()
        row = next(r for r in E["incidents"] if roll <= r["to"])
        fits = (not row.get("types") or ftype in row["types"]) and men >= row.get("min_men", 0) and men <= row.get("max_men", 10 ** 9)
        if fits:
            out["incident"] = row
            if row.get("lose"):
                out["incident_lost"] = min(max(0, left), _pick(row["lose"][0], row["lose"][1], rng))
            out["fatigue"] = row.get("fatigue", 0)
    return out


def day_text(r: dict) -> list[str]:
    """The night's events in words, for the force's log."""
    bits = []
    for kind, word in (("desert", "deserted"), ("straggle", "fell out and were lost"), ("injury", "injured")):
        if r[kind]:
            bits.append(f"{r[kind]} {word.replace('were', 'was') if r[kind] == 1 else word}")
    if r["horses"]:
        bits.append(f"{r['horses']} horse{'s' if r['horses'] != 1 else ''} lost")
    if r["incident"] and not r["incident"].get("quiet"):
        bits.append(r["incident"]["text"].rstrip(".") + (f" ({r['incident_lost']} lost)" if r["incident_lost"] else ""))
    return bits
