"""Camp disease for forces on the travel map (Grave Wounds). Mirrored exactly by the travel
page (templates/travel.html), between its 'shared with gravewounds/disease.py' markers.

A force's health is {cases, immune, had, dead}: cases is a list of the men now sick or
incubating, one disease each, as {d, inc (days until it shows), step (index into steps),
peak (0 once reached), shown (days since it showed), chronic}; immune counts survivors of a disease that
gives immunity; had counts men who have had a disease that relapses; dead is the total.
Dice come from `rng`, a function returning d100 (1-100), so both languages roll alike."""
from __future__ import annotations

from .model import Data


def _copy(health: dict) -> dict:
    return {"cases": [dict(c) for c in health["cases"]], "immune": dict(health["immune"]),
            "had": dict(health["had"]), "dead": health["dead"]}


def new_health() -> dict:
    return {"cases": [], "immune": {}, "had": {}, "dead": 0}


def _step(d: Data, name: str) -> int:
    return d.disease["steps"].index(name)


def _pick(lo: int, hi: int, rng) -> int:
    return lo + (rng() - 1) % (hi - lo + 1)


def counts(d: Data, health: dict, men: int) -> dict:
    """{sick (showing), incubating, unfit, carried, fit} for a force of `men`."""
    shown = [c for c in health["cases"] if c["inc"] == 0]
    unfit = sum(1 for c in shown if c["step"] >= _step(d, d.disease["unfit_from"]))
    carried = sum(1 for c in shown if c["step"] >= _step(d, d.disease["carried_from"]))
    return {"sick": len(shown), "incubating": len(health["cases"]) - len(shown),
            "unfit": unfit, "carried": carried, "fit": max(0, men - unfit)}


def march_pct(d: Data, fit: int, carried: int) -> int:
    """% of its speed a force can march while carrying `carried` men on litters."""
    L = d.disease["litters"]
    if carried == 0:
        return 100
    if fit == 0:
        return 0
    return L["short"] if fit < L["bearers"] * carried else L["march"]


def camp_hygiene(d: Data, gm: str | None, camp_kind: str | None) -> str:
    """The GM's setting if there is one, else the camp's (no camp: fair)."""
    return gm or d.disease["camp_hygiene"][camp_kind or "none"]


def camp_care(d: Data, camp_kind: str | None) -> str:
    return d.disease["camp_care"][camp_kind or "none"]


def week_factors(d: Data, o: dict) -> list:
    """The factors that apply this week. o: {hygiene, camped_days, terrain (id), highs (the
    week's daily highs), wet (the week's wet days, true/false), plague (bool)}."""
    D, f = d.disease, []
    if o["hygiene"] in ("poor", "good"):
        f.append(o["hygiene"])
    if o["camped_days"] >= D["staying_days"]:
        f.append("staying")
    f += [k for k, ts in D["terrain_factors"].items() if o["terrain"] in ts]
    highs = o["highs"]
    if highs:
        mean = sum(highs) / len(highs)
        if mean >= D["warm_at"]:
            f.append("warm")
        if max(highs) >= D["hot_at"]:
            f.append("hot")
        if sum(1 for w in o["wet"] if w) >= D["cold_wet_days"] and mean <= D["cold_wet_at"]:
            f.append("cold_wet")
    if o.get("plague"):
        f.append("plague")
    return f


def outbreak_chance(d: Data, did: str, factors: list) -> int:
    x = d.disease["diseases"][did]
    if any(n not in factors for n in x.get("needs", [])):
        return 0
    return max(0, min(100, x["base"] + sum(v for k, v in x["mods"].items() if k in factors)))


def _new_case(d: Data, did: str, rng) -> dict:
    x = d.disease["diseases"][did]
    inc = _pick(x["incubation"][0], x["incubation"][1], rng)
    roll = rng()
    peak = _step(d, next(r for r in x["peak"] if roll <= r["upto"])["step"])
    return {"d": did, "inc": inc, "step": 0, "peak": peak, "shown": 0, "chronic": False}


def catch_chance(d: Data, did: str, factors: list) -> float:
    """% chance a well man catches `did` this week: the outbreak chance times the chance he
    fails to resist (d100 over Endurance). A force is many men, so each rolls on his own
    rather than the whole force at once."""
    return outbreak_chance(d, did, factors) * (100 - d.disease["endurance"]) / 100


def _d10000(rng) -> int:
    return (rng() - 1) * 100 + rng()


def week(d: Data, health: dict, men: int, factors: list, rng) -> tuple[dict, list]:
    """The weekly roll: each well man who is not immune may catch each disease (d10000 against
    catch_chance x 100), then relapses. Returns (health, events); events are {kind: caught or
    relapse, d, n}."""
    D, h, ev = d.disease, _copy(health), []
    for did in D["diseases"]:
        p = catch_chance(d, did, factors) * 100
        if p <= 0:
            continue
        exposed = max(0, men - len(h["cases"]) - h["immune"].get(did, 0))
        caught = 0
        for _ in range(exposed):
            if _d10000(rng) <= p:
                h["cases"].append(_new_case(d, did, rng))
                caught += 1
        if caught:
            ev.append({"kind": "caught", "d": did, "n": caught})
    ev += _relapses(d, h, factors, rng)
    return h, ev


def _relapses(d: Data, h: dict, factors: list, rng) -> list:
    """Men who have had a relapsing disease fall ill with it again (at Serious) in marsh country."""
    ev = []
    for did, x in d.disease["diseases"].items():
        if not x.get("relapse") or "marsh" not in factors:
            continue
        back = sum(1 for _ in range(h["had"].get(did, 0)) if rng() <= x["relapse"])
        if back:
            h["had"][did] -= back
            s = _step(d, "serious")
            h["cases"] += [{"d": did, "inc": 0, "step": s, "peak": 0, "shown": 0, "chronic": False} for _ in range(back)]
            ev.append({"kind": "relapse", "d": did, "n": back})
    return ev


def _checks_today(x: dict, c: dict) -> bool:
    if c["chronic"]:
        return c["shown"] % 7 == 0
    return c["shown"] >= x.get("checks_from", 0)


def _recover(d: Data, c: dict, target: int, rng) -> str:
    """One recovery check on a case at or past its peak: 'dead', 'healed' or 'sick'."""
    x, big, deadly = d.disease["diseases"][c["d"]], d.disease["recovery"]["big"], len(d.disease["steps"]) - 1
    m = target - x["virulence"] - rng()
    if m >= big:
        c["step"] -= 2
    elif m >= 0:
        c["step"] -= 1
    elif c["step"] == deadly:
        return "dead"
    elif m <= -big:
        if x.get("chronic") and c["step"] <= _step(d, "serious"):
            c["chronic"], c["step"] = True, _step(d, "serious")
        else:
            c["step"] += 1
    return "healed" if c["step"] <= 0 else "sick"


def _case_day(d: Data, c: dict, target: int, rng, ev: dict) -> str:
    """One case's day: 'sick' while it lasts, else 'healed' or 'dead' (tallied in ev)."""
    x = d.disease["diseases"][c["d"]]
    if c["inc"] > 0:
        c["inc"] -= 1
        if c["inc"] == 0:
            c["step"] = _step(d, "mending")
            ev["shown"][c["d"]] = ev["shown"].get(c["d"], 0) + 1
        return "sick"
    c["shown"] += 1
    if c["step"] < c["peak"]:                 # climbing to its peak, once
        c["step"] += 1
        if c["step"] >= c["peak"]:
            c["peak"] = 0
        return "sick"
    out = _recover(d, c, target, rng) if _checks_today(x, c) else "sick"
    if out != "sick":
        ev[out][c["d"]] = ev[out].get(c["d"], 0) + 1
    return out


def day(d: Data, health: dict, ctx: dict, rng) -> tuple[dict, dict]:
    """A day passes: incubations run down, cases climb to their peak, then recover or worsen.
    ctx: {care (none, field or shelter), marched (bool), wet_cold (bool), filth (bool)}.
    Returns (health, {shown, healed, dead}: men by disease)."""
    D, R = d.disease, d.disease["recovery"]
    target = (D["endurance"] + R["care"][ctx["care"]] + R["activity"]["marched" if ctx["marched"] else "rest"]
              + (R["wet_cold"] if ctx["wet_cold"] else 0) + (R["filth"] if ctx["filth"] else 0))
    h = _copy(health)
    ev = {"shown": {}, "healed": {}, "dead": {}}
    keep = []
    for c in h["cases"]:
        x = D["diseases"][c["d"]]
        out = _case_day(d, c, target, rng, ev)
        if out == "sick":
            keep.append(c)
        elif out == "dead":
            h["dead"] += 1
        elif x.get("immune"):
            h["immune"][c["d"]] = h["immune"].get(c["d"], 0) + 1
        elif x.get("relapse"):
            h["had"][c["d"]] = h["had"].get(c["d"], 0) + 1
    h["cases"] = keep
    return h, ev


def seeded_d100(seed: int):
    """A repeatable d100 for simulations and tests (Park-Miller minimal standard generator),
    the same in Python and JavaScript; play uses real random dice."""
    state = [max(1, seed % 2147483647)]

    def roll() -> int:
        state[0] = state[0] * 16807 % 2147483647
        return state[0] % 100 + 1
    return roll


def simulate(d: Data, did: str, n: int, ctx: dict, rng, days: int = 300) -> dict:
    """n men who have caught `did`, followed until all are healed or dead (for tuning):
    {deaths (% of cases), sick_days (mean days showing)}."""
    h = new_health()
    h["cases"] = [_new_case(d, did, rng) for _ in range(n)]
    sick_days = 0
    for _ in range(days):
        if not h["cases"]:
            break
        h, _ = day(d, h, ctx, rng)
        sick_days += sum(1 for c in h["cases"] if c["inc"] == 0)
    return {"deaths": 100 * h["dead"] / n, "sick_days": sick_days / n}
