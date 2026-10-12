"""Camp disease for forces on the travel map (Grave Wounds). Mirrored exactly by the travel
page (templates/travel.html), between its 'shared with gravewounds/disease.py' markers.

A force's health is {cases, immune, had, dead}: cases is a list of the men now sick or
incubating, one disease each, as {d, inc (days until it shows), step (index into steps),
peak (0 once reached), shown (days since it showed), chronic}; immune counts survivors of a disease that
gives immunity; had counts men who have had a disease that relapses; dead is the total.
Dice come from `rng`, a function returning d100 (1-100), so both languages roll alike.

Men wounded on the field map join the same list as cases of `wound` (healing, checked by the
week) carrying `inf` (the wound's infection risk) and `fever` (days until it turns septic or
not); a septic wound becomes a case of `fever` (wound fever), checked every day."""
from __future__ import annotations

from .model import Data


def _copy(health: dict) -> dict:
    return {"cases": [dict(c) for c in health["cases"]], "immune": dict(health["immune"]),
            "had": dict(health["had"]), "dead": health["dead"]}


def new_health() -> dict:
    return {"cases": [], "immune": {}, "had": {}, "dead": 0}


def profile(d: Data, did: str) -> dict:
    """A disease's profile, the wound track's (wound, fever), or scurvy's."""
    if did in ("scurvy", "frostbite"):
        return d.disease[did]
    return d.disease["diseases"].get(did) or d.disease["wounds"][did]


def wound_case(d: Data, severity: str, lethal: str, infection: str, rng) -> dict:
    """A man carried from the field with a wound of this severity, death clock and infection
    risk: his case on the wound track."""
    W = d.disease["wounds"]
    step = max(_step(d, W["start"][severity]), _step(d, W["clock_step"].get(lethal, "healed")))
    return {"d": "wound", "inc": 0, "step": step, "peak": 0, "shown": 0, "chronic": False,
            "inf": infection, "fever": _pick(W["fever_after"][0], W["fever_after"][1], rng)}


def _step(d: Data, name: str) -> int:
    return d.disease["steps"].index(name)


def _pick(lo: int, hi: int, rng) -> int:
    return lo + (rng() - 1) % (hi - lo + 1)


def counts(d: Data, health: dict, men: int) -> dict:
    """{sick (showing), incubating, unfit, carried, fit, nurses (fit men nursing the unfit)} for a force of `men`."""
    shown = [c for c in health["cases"] if c["inc"] == 0]
    unfit = sum(1 for c in shown if c["step"] >= _step(d, d.disease["unfit_from"]))
    carried = sum(1 for c in shown if c["step"] >= _step(d, d.disease["carried_from"]))
    fit = max(0, men - unfit)
    return {"sick": len(shown), "incubating": len(health["cases"]) - len(shown),
            "unfit": unfit, "carried": carried, "fit": fit, "nurses": min(fit, -(-unfit // d.disease["nursing"]["patients"]))}


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
        if o["hygiene"] == "poor":
            f.append("crowded")
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


def outbreak_chance(d: Data, did: str, factors: list, extra: dict | None = None) -> int:
    """The week's outbreak chance: base + the factors' mods + contagion (extra: {did: add})."""
    x = d.disease["diseases"][did]
    if any(n not in factors for n in x.get("needs", [])):
        return 0
    add = (extra or {}).get(did, 0)
    return max(0, min(100, x["base"] + sum(v for k, v in x["mods"].items() if k in factors) + add))


def _patients(d: Data, health: dict) -> list:
    """The cases that need nursing: showing, at Serious or worse, in list order."""
    u = _step(d, d.disease["unfit_from"])
    return [c for c in health["cases"] if c["inc"] == 0 and c["step"] >= u]


def nursing(d: Data, health: dict, men: int, clean: bool = False) -> dict:
    """The force's nursing this week: {patients: {did: n}, unfit, nurses (fit men tending
    them, as many as are needed and can be spared), unnursed (sick beyond what they can tend),
    clean}."""
    N, pts = d.disease["nursing"], _patients(d, health)
    by = {}
    for c in pts:
        by[c["d"]] = by.get(c["d"], 0) + 1
    fit = max(0, men - len(pts))
    need = -(-len(pts) // N["patients"])
    nurses = min(fit, need)
    return {"patients": by, "unfit": len(pts), "nurses": nurses,
            "unnursed": max(0, len(pts) - nurses * N["patients"]), "clean": clean}


def contagion(d: Data, health: dict, men: int) -> dict:
    """{did: add}: the camp's outbreak chances raised by the men already sick (showing)."""
    C, out = d.disease["nursing"]["contagion"], {}
    if men <= 0:
        return out
    for did, add in C["add"].items():
        sick = sum(1 for c in health["cases"] if c["d"] == did and c["inc"] == 0)
        out[did] = (100 * sick) // (men * C["per"]) * add
    return out


def nurse_chance(d: Data, did: str, nurse: dict, endurance: int | None = None) -> float:
    """% a week that one nurse catches `did` from his patients (resisted with Endurance)."""
    s = d.disease["nursing"]["spread"].get(did)
    if not s or not nurse["unfit"] or not nurse["patients"].get(did) or (nurse["clean"] and s.get("clean")):
        return 0.0
    e = d.disease["endurance"] if endurance is None else endurance
    return s["nurse"] * nurse["patients"][did] / nurse["unfit"] * (100 - e) / 100


def _new_case(d: Data, did: str, rng) -> dict:
    x = d.disease["diseases"][did]
    inc = _pick(x["incubation"][0], x["incubation"][1], rng)
    roll = rng()
    peak = _step(d, next(r for r in x["peak"] if roll <= r["upto"])["step"])
    return {"d": did, "inc": inc, "step": 0, "peak": peak, "shown": 0, "chronic": False}


def catch_chance(d: Data, did: str, factors: list, endurance: int | None = None, extra: dict | None = None) -> float:
    """% chance a well man catches `did` this week: the outbreak chance times the chance he
    fails to resist (d100 over Endurance: a typical man's, or a named character's own). A
    force is many men, so each rolls on his own rather than the whole force at once."""
    e = d.disease["endurance"] if endurance is None else endurance
    return outbreak_chance(d, did, factors, extra) * (100 - e) / 100


def fresh_today(d: Data, forage: str, camped: bool, issued: bool = False, found: bool = False) -> bool:
    """Did the force get fresh food today? Its hex's forage (good), or fair forage when it
    spent the whole day camped there (not marching) or a named man's Fieldcraft found it
    (found: fieldcraft_finds), or the GM issued it."""
    F = d.disease["scurvy"]["fresh"]
    return (issued or forage in F["forage"] or (camped and forage in F["camped"])
            or (found and forage in F["fieldcraft"]))


def fieldcraft_needed(d: Data, forage: str, camped: bool) -> bool:
    """A Fieldcraft roll can find fresh food only on a march day on this kind of forage."""
    return not camped and forage in d.disease["scurvy"]["fresh"]["fieldcraft"]


def leech_bonus(d: Data, leechcraft: int) -> int:
    """The best named leech with a force: + to recovery checks, - to the septic chance."""
    return max(0, leechcraft) // d.disease["leech"]["per"]


def scurvy_chance(d: Data, no_fresh: int, endurance: int | None = None) -> float:
    """% chance a well man falls ill with scurvy this week, after `no_fresh` days without
    fresh food: none before `after_days`, then `chance`, `per_week` more each week."""
    S = d.disease["scurvy"]
    if no_fresh < S["after_days"]:
        return 0.0
    weeks = (no_fresh - S["after_days"]) // d.disease["week_days"]
    e = d.disease["endurance"] if endurance is None else endurance
    return min(100, S["chance"] + S["per_week"] * weeks) * (100 - e) / 100


def _scurvy_case(d: Data) -> dict:
    return {"d": "scurvy", "inc": 0, "step": _step(d, "mending"), "peak": 0, "shown": 0, "chronic": False}


def _scurvy_week(d: Data, h: dict, men: int, no_fresh: int, rng, endurance: int | None) -> list:
    """Each well man may fall ill with scurvy (it shows at once, at Mending)."""
    p = scurvy_chance(d, no_fresh, endurance) * 100
    if p <= 0:
        return []
    ill = 0
    for _ in range(max(0, men - len(h["cases"]))):
        if _d10000(rng) <= p:
            h["cases"].append(_scurvy_case(d))
            ill += 1
    return [{"kind": "scurvy", "d": "scurvy", "n": ill}] if ill else []


def reopen(d: Data, health: dict, olds: list) -> dict:
    """Scurvy reopens a named man's old wounds: each ({key, loc}: from his sheet, or a scar)
    not already open comes back on the wound track at Mending, keyed by wid 'old:<key>'."""
    h = _copy(health)
    have = {c.get("wid") for c in h["cases"]}
    for o in olds:
        wid = "old:" + str(o["key"])
        if wid not in have:
            h["cases"].append({"d": "wound", "inc": 0, "step": _step(d, "mending"), "peak": 0, "shown": 0,
                               "chronic": False, "wid": wid, "old": True})
    return h


def _d10000(rng) -> int:
    return (rng() - 1) * 100 + rng()


def week(d: Data, health: dict, men: int, factors: list, rng, endurance: int | None = None,
         extra: dict | None = None, nurse: dict | None = None, no_fresh: int = 0) -> tuple[dict, list]:
    """The weekly roll: each well man who is not immune may catch each disease (d10000 against
    catch_chance x 100, with the camp's contagion `extra`), then scurvy after `no_fresh` days
    without fresh food, then the nurses roll for what their patients have (`nurse`: nursing(),
    its `nurses` the men who roll), then relapses. Returns (health, events); events are
    {kind: caught, scurvy, nursed or relapse, d, n}. endurance: a named
    character's own (men 1), or the typical man's."""
    D, h, ev = d.disease, _copy(health), []
    for did in D["diseases"]:
        p = catch_chance(d, did, factors, endurance, extra) * 100
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
    ev += _scurvy_week(d, h, men, no_fresh, rng, endurance)
    if nurse:
        ev += _nurses_catch(d, h, men, nurse, rng, endurance)
    ev += _relapses(d, h, factors, rng)
    return h, ev


def _nurses_catch(d: Data, h: dict, men: int, nurse: dict, rng, endurance: int | None) -> list:
    """Each nurse who is well and not immune may catch each disease his patients have."""
    ev = []
    for did in d.disease["nursing"]["spread"]:
        p = nurse_chance(d, did, nurse, endurance) * 100
        if p <= 0:
            continue
        well = max(0, men - len(h["cases"]) - h["immune"].get(did, 0))
        caught = 0
        for _ in range(min(nurse["nurses"], well)):
            if _d10000(rng) <= p:
                h["cases"].append(_new_case(d, did, rng))
                caught += 1
        if caught:
            ev.append({"kind": "nursed", "d": did, "n": caught})
    return ev


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
    if x.get("every"):
        return c["shown"] % x["every"] == 0
    return c["shown"] >= x.get("checks_from", 0)


def _recover(d: Data, c: dict, target: int, rng) -> str:
    """One recovery check on a case at or past its peak: 'dead', 'healed' or 'sick'."""
    x, big, deadly = profile(d, c["d"]), d.disease["recovery"]["big"], len(d.disease["steps"]) - 1
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


def _scurvy_check(d: Data, c: dict, target: int, rng, fresh: bool) -> str:
    """Scurvy's weekly check: fresh food heals `heal` steps; without it, success holds and
    failure is a step worse (at Deadly, dead)."""
    x = d.disease["scurvy"]
    if fresh:
        c["step"] -= x["heal"]
        return "healed" if c["step"] <= 0 else "sick"
    if target - x["virulence"] - rng() >= 0:
        return "sick"
    if c["step"] == len(d.disease["steps"]) - 1:
        return "dead"
    c["step"] += 1
    return "sick"


def _septic(d: Data, c: dict, care: str, rng, ev: dict, leech: int = 0) -> None:
    """A wound's fever day: it turns septic (wound fever, one step worse) or it does not."""
    W = d.disease["wounds"]
    c["fever"] = 0
    if rng() <= W["fever_chance"][c["inf"]] + W["fever_care"][care] - leech:
        c["d"], c["step"] = "fever", min(len(d.disease["steps"]) - 1, c["step"] + 1)
        ev["shown"]["fever"] = ev["shown"].get("fever", 0) + 1


def _case_day(d: Data, c: dict, target: int, rng, ev: dict, care: str = "field", food: tuple = (False, False), leech: int = 0) -> str:
    """One case's day: 'sick' while it lasts, else 'healed' or 'dead' (tallied in ev).
    food: (fresh food in the past week, he has scurvy): an old wound it reopened cannot heal
    while it lasts."""
    if c.get("fever"):
        c["fever"] -= 1
        if c["fever"] == 0:
            _septic(d, c, care, rng, ev, leech)
    x = profile(d, c["d"])
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
    if not _checks_today(x, c) or (c.get("old") and food[1]):
        out = "sick"
    elif c["d"] == "scurvy":
        out = _scurvy_check(d, c, target, rng, food[0])
    else:
        out = _recover(d, c, target, rng)
    if out != "sick":
        ev[out][c["d"]] = ev[out].get(c["d"], 0) + 1
    return out


def day(d: Data, health: dict, ctx: dict, rng, endurance: int | None = None) -> tuple[dict, dict]:
    """A day passes: incubations run down, cases climb to their peak, then recover or worsen.
    ctx: {care (none, field or shelter), marched (bool), wet_cold (bool), filth (bool), unnursed
    (the last that many sick needing nursing get none: no care), fresh (fresh food in the past
    week, for scurvy), leech (leech_bonus of the best named leech with the force; not for
    the untended)}.
    endurance: a named character's own, or the typical man's.
    Returns (health, {shown, healed, dead}: men by disease)."""
    R = d.disease["recovery"]
    target = _day_target(d, ctx, endurance)
    h = _copy(health)
    ev = {"shown": {}, "healed": {}, "dead": {}}
    keep = []
    pts = _patients(d, h)
    left = set(map(id, pts[len(pts) - ctx.get("unnursed", 0):])) if ctx.get("unnursed", 0) else set()
    lb = ctx.get("leech", 0)
    alone = target - R["care"][ctx["care"]] + R["care"]["none"] - lb     # no one to tend him
    food = (bool(ctx.get("fresh")), any(c["d"] == "scurvy" for c in h["cases"]))
    for c in h["cases"]:
        tended = id(c) not in left
        out = _case_day(d, c, target if tended else alone, rng, ev, ctx["care"] if tended else "none", food, lb if tended else 0)
        if out == "sick":
            keep.append(c)
        else:
            _close_case(d, h, c, out)
    h["cases"] = keep
    _frostbite_night(d, h, ctx, rng, endurance, ev)
    return h, ev


def frostbite_chance(d: Data, low, shelter: int = 0, endurance: int | None = None) -> float:
    """% chance a well man is frostbitten on a night with this low (degrees C) under this much
    shelter (weather.yaml shelter); 0 if it is not cold enough."""
    F = d.disease.get("frostbite")
    if not F or low is None or low > F["below"]:
        return 0.0
    e = d.disease["endurance"] if endurance is None else endurance
    return min(100, F["base"] + F["per_degree"] * (F["below"] - low)) * max(0, 100 - F["shelter"] * shelter) / 100 * (100 - e) / 100


def _frostbite_night(d: Data, h: dict, ctx: dict, rng, endurance: int | None, ev: dict) -> None:
    """The night's frostbite (ctx: low, shelter, men): each well man may be bitten; it shows at once."""
    p = frostbite_chance(d, ctx.get("low"), ctx.get("shelter", 0), endurance) * 100
    if p <= 0:
        return
    F = d.disease["frostbite"]
    for _ in range(max(0, ctx.get("men", 0) - len(h["cases"]))):
        if _d10000(rng) <= p:
            r = rng()
            step = next(x["step"] for x in F["peak"] if r <= x["upto"])
            h["cases"].append({"d": "frostbite", "inc": 0, "step": _step(d, step), "peak": 0, "shown": 0, "chronic": False})
            ev["shown"]["frostbite"] = ev["shown"].get("frostbite", 0) + 1


def _day_target(d: Data, ctx: dict, endurance: int | None) -> int:
    """The day's recovery target before virulence: Endurance, care, activity, conditions, a leech."""
    D, R = d.disease, d.disease["recovery"]
    return ((D["endurance"] if endurance is None else endurance) + R["care"][ctx["care"]] + R["activity"]["marched" if ctx["marched"] else "rest"]
            + (R["wet_cold"] if ctx["wet_cold"] else 0) + (R["filth"] if ctx["filth"] else 0) + ctx.get("leech", 0))


def _close_case(d: Data, h: dict, c: dict, out: str) -> None:
    """A case over: dead, or healed and immune, or healed and liable to relapse."""
    x = profile(d, c["d"])
    if out == "dead":
        h["dead"] += 1
    elif x.get("immune"):
        h["immune"][c["d"]] = h["immune"].get(c["d"], 0) + 1
    elif x.get("relapse"):
        h["had"][c["d"]] = h["had"].get(c["d"], 0) + 1


def worst_step(d: Data, health: dict) -> str | None:
    """A named character's worst step of sickness that shows (not incubating), or None. His
    wounds on the wound track do not count (their own pain and impairment stand for them);
    wound fever does."""
    shown = [c["step"] for c in health["cases"] if c["inc"] == 0 and c["step"] > 0 and c["d"] != "wound"]
    return d.disease["steps"][max(shown)] if shown else None


def to_camp(d: Data, health: dict, wounds: list, rng) -> dict:
    """A named man sent to camp: each of his battle wounds ({wid, sev, lethal, infection}) not
    already on the wound track starts there (wound_case), keyed by its wid."""
    h, have = _copy(health), {c.get("wid") for c in health["cases"]}
    for w in wounds:
        if w["wid"] in have or w["sev"] not in d.disease["wounds"]["start"]:
            continue
        c = wound_case(d, w["sev"], w["lethal"], w["infection"], rng)
        c["wid"] = w["wid"]
        h["cases"].append(c)
    return h


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


WOUND_EXAMPLES = [("light", "none", "low"), ("serious", "none", "medium"), ("critical", "none", "medium"),
                  ("serious", "hours", "high"), ("critical", "days", "high")]


def simulate_wounds(d: Data, wound: tuple, n: int, care: str, rng, days: int = 300) -> dict:
    """n men carried to camp with this (severity, lethal, infection) wound, resting, followed
    until healed or dead (for tuning): {deaths, fever (% who got wound fever), unfit_days}."""
    h = new_health()
    h["cases"] = [wound_case(d, *wound, rng) for _ in range(n)]
    fever = unfit = 0
    ctx = {"care": care, "marched": False, "wet_cold": False, "filth": False}
    for _ in range(days):
        if not h["cases"]:
            break
        h, ev = day(d, h, ctx, rng)
        fever += ev["shown"].get("fever", 0)
        unfit += sum(1 for c in h["cases"] if c["step"] >= _step(d, d.disease["unfit_from"]))
    return {"deaths": 100 * h["dead"] / n, "fever": 100 * fever / n, "unfit_days": unfit / n}


CAMP_EXAMPLES = [   # (label, weeks, hygiene, hot, staying from week)
    ("A fair camp held a year", 52, "fair", False, 4),
    ("Six weeks in a poor bivouac", 6, "poor", False, 4),
    ("A hot, filthy siege camp, six weeks", 6, "poor", True, 0),
    ("Good quarters for a year", 52, "good", False, 4),
]


def camp_example(d: Data, weeks: int, hygiene: str, hot: bool, stay_from: int, men: int, seed: int) -> float:
    """% of a force of `men` dead of disease after `weeks` resting in camp (dry weather, no
    marsh or town): the calibration marks in disease.yaml."""
    rng, h, start = seeded_d100(seed), new_health(), men
    ctx = {"care": "shelter" if hygiene == "good" else "field", "marched": False, "wet_cold": False, "filth": hygiene == "poor"}
    for w in range(weeks):
        f = [hygiene] if hygiene != "fair" else []
        if hot:
            f.append("hot")
        if w >= stay_from:
            f += ["staying", "crowded"] if hygiene == "poor" else ["staying"]
        h, _ = week(d, h, men, f, rng, None, contagion(d, h, men), nursing(d, h, men))
        for _ in range(d.disease["week_days"]):
            h, ev = day(d, h, {**ctx, "unnursed": nursing(d, h, men)["unnursed"]}, rng)
            men -= sum(ev["dead"].values())
    return 100 * (start - men) / start


SCURVY_EXAMPLES = [4, 8, 12, None]    # weeks after it shows that fresh food comes (None: never)


def simulate_scurvy(d: Data, n: int, fresh_after: int | None, rng, weeks: int = 52) -> dict:
    """n men with scurvy resting in an ordinary camp, fresh food coming `fresh_after` weeks
    after it shows (None: never), followed until healed or dead or `weeks` pass (for tuning):
    {deaths (% of cases), sick_weeks (mean weeks showing)}."""
    h = new_health()
    h["cases"] = [_scurvy_case(d) for _ in range(n)]
    sick = 0
    for day_no in range(1, weeks * d.disease["week_days"] + 1):
        if not h["cases"]:
            break
        fresh = fresh_after is not None and day_no > fresh_after * d.disease["week_days"]
        h, _ = day(d, h, {"care": "field", "marched": False, "wet_cold": False, "filth": False, "fresh": fresh}, rng)
        sick += len(h["cases"])
    return {"deaths": 100 * h["dead"] / n, "sick_weeks": sick / n / d.disease["week_days"]}
