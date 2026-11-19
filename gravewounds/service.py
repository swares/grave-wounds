"""A season of service (data/service): a named man serving with a line battalion passes a season
in one step, against his war's calendar.

- The team: d100 for a small fight this season (small_war chance by the season's state).
- Each man, week by week through the season (season_days / 7 weeks):
  - each action of the season in that week that the team was at and does not play: if he is
    neither dead, nor hit already, nor unfit with sickness, d100 against his hit chance (the army's
    share lost times his position's multiplier, at most the cap; or a battalion's own figure the
    GM picks; or the GM's share where the sources give none); a hit takes a d100 for the weapon
    (the war's table's weapon_mix) and is sent to the roller, which rolls the wound;
  - then the week's sickness on the camp-disease track (disease.week for one man, then disease.day
    seven times), with his own Endurance, under the season's state and hygiene; a man unfit with
    sickness at the week's start spends it in hospital (sheltered care, not marching, dry). A case
    still running at the season's end goes on into his next season.

The team builder (templates/service.js) repeats serve exactly, taking the dice in the same order.
Design: project doc "between-battles-design"."""
from __future__ import annotations

from datetime import date

from .model import Data
from . import disease as dz

SEASON_MONTH = {"spring": 3, "summer": 6, "autumn": 9, "winter": 12}


def war(d: Data, wid: str) -> dict:
    return d.service[wid]


def wars_for(d: Data, eid: str, region: str | None = None) -> list[dict]:
    """The wars a man of this era (and army) can serve a season in."""
    return [W for W in d.service.values() if W["era"] == eid and (region is None or region in W["regions"])]


def season(W: dict, sid: str) -> dict:
    return next(s for s in W["seasons"] if s["id"] == sid)


def season_start(sid: str) -> date:
    """'1811-spring' -> 1 March 1811 (winter: 1 December of its first year)."""
    y, q = sid.split("-")
    return date(int(y), SEASON_MONTH[q], 1)


def weeks(W: dict) -> int:
    return W["season_days"] // 7


def action_week(W: dict, sid: str, aid: str) -> int:
    """The week of the season an action falls in (0 to weeks - 1)."""
    a = W["actions"][aid]
    n = (date.fromisoformat(str(a["date"])) - season_start(sid)).days // 7
    return max(0, min(weeks(W) - 1, n))


def hit_pct(W: dict, aid: str, position: str = "line", unit: int | None = None, share: float | None = None) -> int | None:
    """His % chance of being hit in an unplayed action: a battalion's own figure (unit: its index in
    the action's units), else the army's share (or the GM's `share`, where the sources give none)
    times his position's multiplier, at most the cap. None: no share to roll on."""
    a = W["actions"][aid]
    if unit is not None:
        return int(a["units"][unit]["share"])
    s = a.get("share")
    if s is None:
        s = share
    if s is None:
        return None
    return min(W["cap"], round(s * W["positions"][position]["mult"]))


def taken_pct(W: dict, aid: str, position: str = "line", unit: int | None = None) -> int:
    """His % chance of being taken prisoner in an unplayed action he came through unhit: a
    battalion's own `taken` (unit: its index), else the action's `taken` (the missing of those
    engaged where only missing is counted: ours, most were prisoners) times his position's
    multiplier, at most the cap. 0: none counted."""
    a = W["actions"][aid]
    if unit is not None:
        u = a["units"][unit]
        return int(u["taken"]) if u.get("taken") is not None else 0
    t = a.get("taken")
    if not t:
        return 0
    return min(W["cap"], round(t * W["positions"][position]["mult"]))


def in_week(n: int, wk: int, of: int) -> bool:
    """Whether a factor that holds `n` weeks of `of` holds in week wk: spread evenly through the season."""
    return (wk + 1) * n // of > wk * n // of


def factors(d: Data, W: dict, s: dict, wk: int) -> list:
    """The disease track's factors in a week of the season: hygiene, staying (and crowded), and
    the season's own in the weeks they hold."""
    st, f = W["states"][s["state"]], []
    if s["hygiene"] in ("poor", "good"):
        f.append(s["hygiene"])
    if st["staying"]:
        f.append("staying")
        if s["hygiene"] == "poor":
            f.append("crowded")
    return f + [k for k, n in (s.get("factors") or {}).items() if in_week(n, wk, weeks(W))]


def day_ctx(W: dict, s: dict, wk: int) -> dict:
    """The disease track's day in a week of the season: care, marching, cold and wet, filth."""
    st = W["states"][s["state"]]
    return {"care": st["care"], "marched": st["marched"], "wet_cold": "cold_wet" in factors(None, W, s, wk),
            "filth": s["hygiene"] == "poor", "leech": W.get("medicine", 0)}   # the era's medicine, on every recovery check


def mix_of(d: Data, W: dict) -> list:
    """[(weapon, pct)]: the war's own weapon_mix, else its table's (entries that name a weapon)."""
    return [(m["weapon"], float(m["pct"])) for m in W.get("weapon_mix") or d.tables[W["table"]].get("weapon_mix") or [] if m.get("weapon")]


def weapon_for(d: Data, W: dict, roll: int) -> str:
    """The weapon a hit came from: d100 on the war's weapon mix (mix_of), scaled to 100."""
    mix = mix_of(d, W)
    total, cum = sum(p for _, p in mix), 0.0
    for w, p in mix:
        cum += p
        if roll * total <= cum * 100:
            return w
    return mix[-1][0]


def wound_step(d: Data, health: dict) -> str | None:
    """His worst battle wound on the wound track (wound and wound fever), or None."""
    shown = [c["step"] for c in health["cases"] if c["d"] in ("wound", "fever") and c["step"] > 0]
    return d.disease["steps"][max(shown)] if shown else None


def _unfit(d: Data, health: dict) -> bool:
    """Too sick or too badly wounded to march or fight: a case at unfit_from or worse."""
    at = d.disease["steps"].index(d.disease["unfit_from"])
    return any(c["inc"] == 0 and c["step"] >= at for c in health["cases"])


def serve(d: Data, wid: str, sid: str, men: list[dict], rolled: list[str], rng) -> dict:
    """A season for the team. men: [{name, endurance, position, pos_at: {aid: position}, unit: {aid: index}, share: {aid: %},
    health (his case carried from the last season, or none)}];
    rolled: the actions the team was at and does not play; rng: d100.
    -> {small (bool), small_roll, men: [{name, dead (disease id) and dead_week, sick_days, worst
       (his worst step at the season's end, or None), hits: [{action, pct, roll, weapon}],
       taken ({action, pct, roll, week}: taken prisoner, his season over, or None),
       missed: [{action, why}], rolls: [{action, pct, roll}]}]}"""
    W, s = war(d, wid), season(war(d, wid), sid)
    chance = W["small_war"]["chance"][s["state"]]
    small_roll = rng()
    out = {"small": small_roll <= chance, "small_roll": small_roll, "chance": chance, "men": []}
    if out["small"] and W.get("small_fights"):
        out["fight"] = small_fight(W, s["state"], rng)
    acts = sorted([a for a in s["actions"] if a in rolled], key=lambda a: (action_week(W, sid, a), s["actions"].index(a)))
    for m in men:
        out["men"].append(_man(d, W, s, m, acts, rng))
    return out


def between(lo: int, hi: int, roll: int) -> int:
    """A number from lo to hi on a d100."""
    return lo + (roll - 1) * (hi - lo + 1) // 100


def small_fight(W: dict, state: str, rng, fid: str | None = None) -> dict:
    """The season's small fight: d100 on the fights that fit the state, by weight (or the GM's
    `fid`, with no roll), then a d100 for the size of the team's party, one for each enemy force,
    and one for surprise where the fight has a chance of it.
    -> {id, roll, side (men), foes ([men]), surprise_roll, surprised}"""
    rolled = [f for f in W["small_fights"] if not f.get("edge_only")]   # an edge's own fights come only with their battle
    fits = [f for f in rolled if state in f["states"]] or rolled
    roll = None
    if fid is None:
        roll, total, cum = rng(), sum(f["weight"] for f in fits), 0
        f = fits[-1]
        for x in fits:
            cum += x["weight"]
            if roll * total <= cum * 100:
                f = x
                break
    else:
        f = next(x for x in W["small_fights"] if x["id"] == fid)
    out = {"id": f["id"], "roll": roll, "side": between(*f["side"]["men"], rng()),
           "foes": [between(*o["men"], rng()) for o in f["foes"]], "surprise_roll": None, "surprised": False}
    if f.get("surprise"):
        out["surprise_roll"] = rng()
        out["surprised"] = out["surprise_roll"] <= f["surprise"]["chance"]
    return out


def start_health(m: dict) -> dict:
    """A man's health at the season's start: his case carried from the last season (m health), or well."""
    if not m.get("health"):
        return dz.new_health()
    h = dz._copy(m["health"])
    h["dead"] = 0
    return h


def _man(d: Data, W: dict, s: dict, m: dict, acts: list, rng) -> dict:
    h, r = start_health(m), {"name": m["name"], "dead": None, "dead_week": None, "sick_days": 0, "wound": None,
                             "worst": None, "hits": [], "taken": None, "missed": [], "rolls": [], "health": None}
    end, sid = m.get("endurance"), s["id"]
    for wk in range(weeks(W)):
        for aid in [a for a in acts if action_week(W, sid, a) == wk]:
            _action(d, W, aid, m, h, r, rng)
            if r["taken"]:                           # taken prisoner: his season with the battalion is over
                r["taken"]["week"] = wk
                r["worst"], r["wound"], r["health"] = dz.worst_step(d, h), wound_step(d, h), h
                return r
        if wk == weeks(W) // 2 and (W.get("wastage") or {}).get(s["state"]):
            _wastage(d, W, s, h, r, rng)
        f, ctx = factors(d, W, s, wk), day_ctx(W, s, wk)
        if _unfit(d, h):                             # too sick to march or fight: in hospital this week
            ctx = {**ctx, "care": "shelter", "marched": False, "wet_cold": False}
        h, _ = dz.week(d, h, 1, f, rng, end)
        for _ in range(7):
            h, ev = dz.day(d, h, ctx, rng, end)
            if ev["dead"]:
                r["dead"], r["dead_week"] = next(iter(ev["dead"])), wk
                return r
            if any(c["inc"] == 0 and c["step"] > 0 and c["d"] != "wound" for c in h["cases"]):
                r["sick_days"] += 1
    r["worst"], r["wound"], r["health"] = dz.worst_step(d, h), wound_step(d, h), h   # his health carried into the next season
    return r


WASTAGE = "wastage"   # the hits of a season in the line, outside its named actions


def _wastage(d: Data, W: dict, s: dict, h: dict, r: dict, rng) -> None:
    """The season's wastage in the line (wastage: % by state), rolled once at mid-season for a man
    neither hit already nor unfit: shelled or sniped on the quiet days between the named actions."""
    if r["hits"] or _unfit(d, h):
        return
    pct, roll = W["wastage"][s["state"]], rng()
    r["rolls"].append({"action": WASTAGE, "pct": pct, "roll": roll})
    if roll <= pct:
        r["hits"].append({"action": WASTAGE, "pct": pct, "roll": roll, "weapon": weapon_for(d, W, rng())})


def _action(d: Data, W: dict, aid: str, m: dict, h: dict, r: dict, rng) -> None:
    """One unplayed action for one man: missed (already hit, or too sick), or his hit roll."""
    if r["hits"]:
        r["missed"].append({"action": aid, "why": "wounded"})
        return
    if _unfit(d, h):
        r["missed"].append({"action": aid, "why": "sick"})
        return
    pos = (m.get("pos_at") or {}).get(aid) or m.get("position", "line")   # where he stands at this action (an edge's choice), else for the season
    pct = hit_pct(W, aid, pos, (m.get("unit") or {}).get(aid), (m.get("share") or {}).get(aid))
    if pct is None:
        r["missed"].append({"action": aid, "why": "no share"})
        return
    roll = rng()
    r["rolls"].append({"action": aid, "pct": pct, "roll": roll})
    if roll <= pct:
        r["hits"].append({"action": aid, "pct": pct, "roll": roll, "weapon": weapon_for(d, W, rng())})
        return
    t = taken_pct(W, aid, pos, (m.get("unit") or {}).get(aid))
    if t:                                           # came through unhit: taken in the rout or the surrender?
        roll = rng()
        if roll <= t:
            r["taken"] = {"action": aid, "pct": t, "roll": roll}


def calibrate(d: Data, wid: str, n: int, seed: int, position: str = "line", every: bool = True) -> dict:
    """n men of Endurance 50 through every season of the war, at every main action with a share
    (every=False: at none), for the calibration against the war's totals.
    -> {seasons, disease (% dead of disease a season), hits (% hit a season), totals (the
       records' same, a season)}"""
    W = war(d, wid)
    dead = hits = lives = 0
    for k in range(n):
        rng, health = dz.seeded_d100(seed * 1000003 + k), None
        for s in W["seasons"]:
            rolled = [a for a in s["actions"] if every and W["actions"][a].get("main", True) and W["actions"][a].get("share") is not None]
            res = serve(d, wid, s["id"], [{"name": "x", "endurance": 50, "position": position, "health": health}], rolled, rng)["men"][0]
            health = res["health"]                  # his case carried into the next season
            if res["taken"]:                         # a prisoner: off the battalion's rolls
                break
            hits += len(res["hits"])
            lives += 1
            if res["dead"]:
                dead += 1
                break
    T = W.get("totals")
    if not T:                                       # a war with no army-wide totals in the records
        return {"seasons": len(W["seasons"]), "disease": 100 * dead / lives, "hits": 100 * hits / lives, "totals": None}
    seasons = T.get("seasons", len(W["seasons"]))   # the seasons a man of `strength` served, where the records count men by term
    return {"seasons": seasons, "disease": 100 * dead / lives, "hits": 100 * hits / lives,
            "totals": {"disease": 100 * T["disease"] / T["strength"] / seasons,
                       "hits": 100 * (T["killed"] + T["wounded"]) / T["strength"] / seasons}}
