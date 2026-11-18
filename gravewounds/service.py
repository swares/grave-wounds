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
    seven times), with his own Endurance, under the season's state and hygiene.

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
            "filth": s["hygiene"] == "poor"}


def weapon_for(d: Data, W: dict, roll: int) -> str:
    """The weapon a hit came from: d100 on the war's table's weapon_mix (its entries that name a
    weapon, scaled to 100)."""
    mix = [(m["weapon"], float(m["pct"])) for m in d.tables[W["table"]].get("weapon_mix") or [] if m.get("weapon")]
    total, cum = sum(p for _, p in mix), 0.0
    for w, p in mix:
        cum += p
        if roll * total <= cum * 100:
            return w
    return mix[-1][0]


def _unfit(d: Data, health: dict) -> bool:
    step = dz.worst_step(d, health)
    return step is not None and d.disease["steps"].index(step) >= d.disease["steps"].index(d.disease["unfit_from"])


def serve(d: Data, wid: str, sid: str, men: list[dict], rolled: list[str], rng) -> dict:
    """A season for the team. men: [{name, endurance, position, unit: {aid: index}, share: {aid: %}}];
    rolled: the actions the team was at and does not play; rng: d100.
    -> {small (bool), small_roll, men: [{name, dead (disease id) and dead_week, sick_days, worst
       (his worst step at the season's end, or None), hits: [{action, pct, roll, weapon}],
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
    fits = [f for f in W["small_fights"] if state in f["states"]] or W["small_fights"]
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


def _man(d: Data, W: dict, s: dict, m: dict, acts: list, rng) -> dict:
    h, r = dz.new_health(), {"name": m["name"], "dead": None, "dead_week": None, "sick_days": 0,
                             "worst": None, "hits": [], "missed": [], "rolls": []}
    end, sid = m.get("endurance"), s["id"]
    for wk in range(weeks(W)):
        for aid in [a for a in acts if action_week(W, sid, a) == wk]:
            _action(d, W, aid, m, h, r, rng)
        f, ctx = factors(d, W, s, wk), day_ctx(W, s, wk)
        h, _ = dz.week(d, h, 1, f, rng, end)
        for _ in range(7):
            h, ev = dz.day(d, h, ctx, rng, end)
            if ev["dead"]:
                r["dead"], r["dead_week"] = next(iter(ev["dead"])), wk
                return r
            if any(c["inc"] == 0 and c["step"] > 0 for c in h["cases"]):
                r["sick_days"] += 1
    r["worst"] = dz.worst_step(d, h)
    return r


def _action(d: Data, W: dict, aid: str, m: dict, h: dict, r: dict, rng) -> None:
    """One unplayed action for one man: missed (already hit, or too sick), or his hit roll."""
    if r["hits"]:
        r["missed"].append({"action": aid, "why": "wounded"})
        return
    if _unfit(d, h):
        r["missed"].append({"action": aid, "why": "sick"})
        return
    pct = hit_pct(W, aid, m.get("position", "line"), (m.get("unit") or {}).get(aid), (m.get("share") or {}).get(aid))
    if pct is None:
        r["missed"].append({"action": aid, "why": "no share"})
        return
    roll = rng()
    r["rolls"].append({"action": aid, "pct": pct, "roll": roll})
    if roll <= pct:
        r["hits"].append({"action": aid, "pct": pct, "roll": roll, "weapon": weapon_for(d, W, rng())})


def calibrate(d: Data, wid: str, n: int, seed: int, position: str = "line", every: bool = True) -> dict:
    """n men of Endurance 50 through every season of the war, at every main action with a share
    (every=False: at none), for the calibration against the war's totals.
    -> {seasons, disease (% dead of disease a season), hits (% hit a season), totals (the
       records' same, a season)}"""
    W = war(d, wid)
    dead = hits = lives = 0
    for k in range(n):
        rng = dz.seeded_d100(seed * 1000003 + k)
        for s in W["seasons"]:
            rolled = [a for a in s["actions"] if every and W["actions"][a].get("main", True) and W["actions"][a].get("share") is not None]
            res = serve(d, wid, s["id"], [{"name": "x", "endurance": 50, "position": position}], rolled, rng)["men"][0]
            hits += len(res["hits"])
            lives += 1
            if res["dead"]:
                dead += 1
                break
    seasons = len(W["seasons"])
    T = W["totals"]
    return {"seasons": seasons, "disease": 100 * dead / lives, "hits": 100 * hits / lives,
            "totals": {"disease": 100 * T["disease"] / T["strength"] / seasons,
                       "hits": 100 * (T["killed"] + T["wounded"]) / T["strength"] / seasons}}
