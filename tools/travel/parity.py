"""The travel map's rules (templates/travelrules.js) against gravewounds/weather.py, travel.py and
disease.py, on the same inputs and the same dice.

    python3 tools/travel/parity.py [cases] [seed]

Makes `cases` random cases of each kind: a run of days' weather and ground with each day's light,
marching hours, rest and fatigue; a route on a real map with its schedule, a march along it and the
hexes either side passable or not (fords and flood included); camp work against the clock; who
fights when forces meet, and the odds of surprise; a force's health over weeks and days of camp disease, with wounds, scurvy,
frostbite and nursing. Each is played through the Python with scripted dice, written with the travel
page's data bundle to tools/travel/.cache/, then tools/travel/test.js plays them through the
JavaScript and compares every result. Needs Python 3 with PyYAML and Node; exits non-zero on any
difference.
"""
from __future__ import annotations

import copy
import json
import os
import random
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from build import travel_bundle                              # noqa: E402  the bundle the travel page is built with
from gravewounds import load                                 # noqa: E402
from gravewounds import disease as dz, travel as tv, weather as wx   # noqa: E402
from gravewounds.combat import hex_distance                  # noqa: E402

CACHE = Path(__file__).parent / ".cache"


class TestDice:
    """The test's own randomness: seeded, so a run can be repeated, and never used for anything secret."""
    def __init__(self, seed):
        self._rng = random.Random(seed)   # NOSONAR: test data that must repeat from its seed, not a security use

    def int(self, a, b):
        return self._rng.randint(a, b)    # NOSONAR: as above

    def pick(self, items):
        return self._rng.choice(list(items))   # NOSONAR: as above

    def chance(self, p):
        return self._rng.random() < p          # NOSONAR: as above

    def quarter(self, lo, hi):                 # hours on the quarter hour
        return self.int(int(lo * 4), int(hi * 4)) / 4


class Script:
    """The game's d100s for one case, drawn as the Python asks for them and kept in order, so the
    JavaScript gets the same."""
    def __init__(self, t: TestDice):
        self.t, self.rolls = t, []

    @property
    def used(self):
        return len(self.rolls)

    def __call__(self):
        self.rolls.append(self.t.int(1, 100))
        return self.rolls[-1]


def weather_case(d, t, mid):
    m = d.maps[mid]
    first, n = t.int(1, 300), t.int(3, 12)
    days, prev, ground = [], None, None
    for day in range(first, first + n):
        rolls = [t.int(1, 100) for _ in range(t.pick([5, 7]))]
        w = wx.roll_weather(d, m, day, prev, rolls)
        ground = wx.next_ground(d, ground, w)
        camp = t.pick([None] + list(d.works["camps"]))
        rest = wx.night_rest(d, camp, w)
        fat, marched, hour = t.int(0, len(d.weather["fatigue"]["levels"]) - 1), t.quarter(0, 12), t.quarter(0, 23.75)
        days.append({"day": day, "rolls": rolls, "camp": camp, "fatigue": fat, "marched": marched, "hour": hour,
                     "out": {"w": w, "ground": ground, "date": list(wx.map_date(m, day)), "window": wx.march_window(d, m, day),
                             "light": wx.light_at(d, m, day, hour, w["cond"]), "cold": wx.cold_level(d, w["low"]), "rest": rest,
                             "fatigue": wx.fatigue_after(d, fat, marched, w, ground, rest),
                             "pct": {tid: wx.terrain_pct(d, tid, ground) for tid in d.terrain["terrain"]},
                             "flooded": [tid for tid in d.terrain["terrain"] if wx.flooded(d, tid, ground)]}})
        prev = w
    return {"kind": "weather", "map": mid, "days": days}


def random_ground(t):
    return t.pick([None, {"mud": t.int(0, 3), "snow": t.int(0, 3), "flood": t.int(0, 2)}, {"mud": 0, "snow": 0, "flood": 0}])


def random_ftype(d, t):
    types = list(d.terrain["forces"])
    if t.chance(0.25):
        return [[ft, t.int(10, 400)] for ft in sorted({t.pick(types) for _ in range(t.int(2, 3))})]
    return t.pick(types)


def ford_hexes(m):
    return [[c, r] for r, row in enumerate(m["rows"]) for c, k in enumerate(row) if k in FORD_KEYS]


def route_case(d, t, mid):
    m = d.maps[mid]
    cols, rows = len(m["rows"][0]), len(m["rows"])
    fords = ford_hexes(m)
    ftype, ground = random_ftype(d, t), random_ground(t)
    start = None
    while start is None or not tv.passable(d, m, start, ftype, ground):   # a force stands where it can be
        start = t.pick(fords) if fords and t.chance(0.3) else [t.int(0, cols - 1), t.int(0, rows - 1)]
    goal = [min(cols - 1, max(0, start[0] + t.int(-12, 12))), min(rows - 1, max(0, start[1] + t.int(-12, 12)))]
    path = tv.route(d, m, start, goal, ftype, ground)
    out = {"path": path, "passable": {}, "fords": {}}
    for h in [start, goal] + (fords[:6] if fords else []):
        out["passable"][f"{h[0]},{h[1]}"] = tv.passable(d, m, h, ftype, ground)
    for h in fords[:6]:
        out["fords"][f"{h[0]},{h[1]}"] = [tv.ford_here(d, m, h, ground), tv.too_deep(d, m, h, ftype, ground)]
    case = {"kind": "route", "map": mid, "start": start, "goal": goal, "ftype": ftype, "ground": ground, "fordHexes": fords[:6], "out": out}
    if path and len(path) > 1:
        day, used, speed = t.int(1, 40), t.quarter(0, 6), t.pick([100, 100, 75, 50, 33])
        hpd = [t.quarter(4, 12) for _ in range(t.int(0, 4))] or None
        sground = [random_ground(t) for _ in range(t.int(1, 3))] if t.chance(0.5) else ground
        index = t.int(0, len(path) - 2)
        a = {"at": t.quarter(0, 8), "hours": t.quarter(0, 6), "today": t.quarter(4, 12), "carried": t.pick([0, 0, t.quarter(0, 1)])}
        case["march"] = {"day": day, "used": used, "speed": speed, "hpd": hpd, "sground": sground, "index": index, **a}
        out["schedule"] = tv.schedule(d, m, path, ftype, day, used, hpd, sground, speed)
        out["advance"] = tv.advance(d, m, path, index, a["at"], a["hours"], a["today"], ftype, ground, speed, a["carried"])
        out["hours"] = [tv.step_hours(d, m, x, y, ftype, ground, speed) for x, y in zip(path, path[1:])]
        out["plan"] = tv.plan(d, m, start, [path[len(path) // 2], goal], ftype, ground)
    return case


def camp_case(d, t):
    hpd = [t.quarter(4, 12) for _ in range(t.int(0, 4))] or None
    day, used, hours = t.int(1, 30), t.quarter(0, 14), t.quarter(0, 40)
    start = {"day": day, "used": used}
    later = {"day": day + t.int(0, 3), "used": t.quarter(0, 14)}
    if later["day"] == day and later["used"] < used:
        later["used"] = used
    camp = {"start": start if t.chance(0.8) else None, "setup": t.quarter(0, 3), "rate": t.int(5, 400), "labour": t.int(0, 5000)}
    return {"kind": "camp", "hpd": hpd, "day": day, "used": used, "hours": hours, "later": later, "camp": camp,
            "out": {"done": tv.camp_done(d, day, used, hours, hpd), "worked": tv.camp_worked(d, start, later["day"], later["used"], hpd),
                    "labour": tv.camp_labour_done(d, camp, later["day"], later["used"], hpd)}}


def fight_case(d, t):
    forces = []
    for i in range(t.int(2, 6)):
        pos = [t.int(0, 4), t.int(0, 4)]
        f = {"id": i + 1, "side": t.pick(["A", "B"]), "pos": pos, "camp": None, "day": t.int(1, 3), "used": t.quarter(0, 10)}
        if t.chance(0.4):
            f["camp"] = {"kind": t.pick(list(d.works["camps"])), "hex": pos if t.chance(0.8) else [pos[0] + 1, pos[1]]}
            if t.chance(0.6):
                f["camp"]["from"] = {"day": t.int(1, f["day"]), "used": t.quarter(0, 10)}
        forces.append(f)
    if len({f["side"] for f in forces}) < 2:
        forces[0]["side"] = "B" if forces[1]["side"] == "A" else "A"
    sel, wait = t.pick([f["id"] for f in forces]), t.chance(0.5)
    return {"kind": "fight", "forces": forces, "sel": sel, "wait": wait,
            "out": tv.fight_plan(d, forces, sel, wait), "dist": [[hex_distance(a["pos"], b["pos"]) for b in forces] for a in forces]}


def surprise_case(d, t):
    camp = t.pick([None] + list(d.works["camps"]))
    dark, fog, stealth, watch = t.chance(0.4), t.chance(0.3), t.pick([0, t.int(0, 120)]), t.pick([0, t.int(0, 120)])
    return {"kind": "surprise", "camp": camp, "dark": dark, "fog": fog, "stealth": stealth, "watch": watch,
            "out": tv.surprise(d, camp, dark, fog, stealth, watch)}


def health_case(d, t):
    D = d.disease
    men = t.int(1, 300)
    h = dz.new_health()
    for _ in range(t.int(0, 6)):        # wounds from a fight, some already feverish
        h["cases"].append({"d": "wound", "inc": 0, "step": t.int(1, len(D["steps"]) - 1), "peak": 0, "shown": t.int(0, 5), "chronic": False,
                           "inf": t.pick(list(D["wounds"]["fever_chance"])), "fever": t.int(0, 4)})
    if t.chance(0.3):
        h = dz.reopen(d, h, [{"key": f"m{i}", "loc": "arm"} for i in range(t.int(1, 3))])
    init, rng, steps = copy.deepcopy(h), Script(t), []
    terrains = list(d.terrain["terrain"])
    for _ in range(t.int(2, 10)):
        if t.chance(0.3):
            o = {"hygiene": t.pick(["poor", "fair", "good"]), "camped_days": t.int(0, 30), "terrain": t.pick(terrains),
                 "highs": [t.int(-5, 38) for _ in range(t.int(0, 7))], "wet": [t.chance(0.4) for _ in range(7)], "plague": t.chance(0.1)}
            factors = dz.week_factors(d, o)
            clean = t.chance(0.3)
            nurse, extra = dz.nursing(d, h, men, clean), dz.contagion(d, h, men)
            end = t.pick([None, t.int(20, 80)])
            no_fresh = t.pick([0, t.int(0, 120)])
            h, ev = dz.week(d, h, men, factors, rng, end, extra, nurse, no_fresh)
            steps.append({"op": "week", "o": o, "clean": clean, "end": end, "noFresh": no_fresh,
                          "out": {"factors": factors, "nurse": nurse, "extra": extra, "health": h, "events": ev, "used": rng.used,
                                  "chances": {did: [dz.outbreak_chance(d, did, factors, extra), dz.catch_chance(d, did, factors, end, extra),
                                                    dz.nurse_chance(d, did, nurse, end) if did in D["nursing"]["spread"] else 0] for did in D["diseases"]},
                                  "scurvy": dz.scurvy_chance(d, no_fresh, end)}})
        else:
            pts = dz.nursing(d, h, men)
            ctx = {"care": t.pick(["none", "field", "shelter"]), "marched": t.chance(0.5), "wet_cold": t.chance(0.2), "filth": t.chance(0.2),
                   "unnursed": t.int(0, pts["unfit"]) if t.chance(0.4) else 0, "fresh": t.chance(0.5), "leech": t.pick([0, 0, 1, 2]),
                   "low": t.pick([None, t.int(-30, 15)]), "shelter": t.int(0, 3), "men": men}
            end = t.pick([None, t.int(20, 80)])
            h, ev = dz.day(d, h, ctx, rng, end)
            steps.append({"op": "day", "ctx": ctx, "end": end, "out": {"health": h, "events": ev, "used": rng.used,
                                                                     "frost": dz.frostbite_chance(d, ctx["low"], ctx["shelter"], end)}})
        steps[-1]["out"]["counts"] = dz.counts(d, h, men)
        c = steps[-1]["out"]["counts"]
        steps[-1]["out"]["pct"] = dz.march_pct(d, c["fit"], c["carried"])
    forage = t.pick(sorted({f for x in D["scurvy"]["fresh"].values() for f in x} | {"none"}))
    camped, issued, found = t.chance(0.5), t.chance(0.2), t.chance(0.5)
    forage = t.pick(sorted({f for x in D["scurvy"]["fresh"].values() for f in x} | {"none"}))
    camped, issued, found, leech = t.chance(0.5), t.chance(0.2), t.chance(0.5), t.int(0, 90)
    return {"kind": "health", "men": men, "init": init, "rolls": rng.rolls, "steps": steps,
            "fresh": {"forage": forage, "camped": camped, "issued": issued, "found": found, "leech": leech,
                      "out": [dz.fresh_today(d, forage, camped, issued, found), dz.fieldcraft_needed(d, forage, camped),
                              dz.leech_bonus(d, leech)]}}


FORD_KEYS: set = set()


def cases(d, n, seed):
    global FORD_KEYS
    t = TestDice(seed)
    FORD_KEYS = {x["key"] for x in d.terrain["terrain"].values() if x["id"] in ("ford",)}
    maps = sorted(d.maps)
    out = []
    for _ in range(n):
        out.append(weather_case(d, t, t.pick(maps)))
        out.append(route_case(d, t, t.pick(maps)))
        out.append(camp_case(d, t))
        out.append(fight_case(d, t))
        out.append(surprise_case(d, t))
    for _ in range(n):
        out.append(health_case(d, t))
    return out


SHARED = ["purse.js", "xp.js", "ranks.js", "events.js", "measure.js", "lethality.js", "camp.js"]


def top_names(text: str) -> list:
    """The names a shared file declares at its top level (function, const, let), in order."""
    names = []
    for line in text.split("\n"):
        m = re.match(r"(?:async\s+)?function\s+(\w+)\s*\(", line)
        if m:
            names.append(m.group(1))
            continue
        m = re.match(r"(?:const|let)\s+(.*)", line)
        if not m:
            continue
        depth, cur, parts = 0, "", []
        for ch in m.group(1):
            depth += ch in "([{"
            depth -= ch in ")]}"
            if ch == "," and depth == 0:
                parts.append(cur)
                cur = ""
            else:
                cur += ch
        parts.append(cur)
        names += [mm.group(1) for mm in (re.match(r"\s*(\w+)\s*=", x) for x in parts) if mm]
    return list(dict.fromkeys(names))


def write_shared(d) -> None:
    """The shared rule files the travel day needs, as the travel page has them (one script, the
    lethality presets filled in as build.py fills them), made one Node module for test.js."""
    lethal = {"default": d.wounds["lethality"]["default"], "presets": d.wounds["lethality"]["presets"]}
    parts = [(ROOT / "templates" / f).read_text(encoding="utf-8") for f in SHARED]
    text = "\n".join(parts).replace("/*__LETHAL_DATA__*/null", json.dumps(lethal))
    out = "// Made by tools/travel/parity.py from templates/" + ", ".join(SHARED) + ": do not edit.\n" + text
    out += "\nmodule.exports = { " + ", ".join(top_names(text)) + " };\n"
    (CACHE / "shared.js").write_text(out, encoding="utf-8")


def check_page() -> int:
    """The built pages' scripts parse (node --check): a name declared twice in a page's script, say one
    a shared file also declares, is caught here as it would stop the page loading."""
    bad = 0
    for name in ("travel.html", "campaign.html", "roller.html", "team.html", "field.html"):   # every page with rules in it
        page, wrong = (ROOT / "dist" / name).read_text(encoding="utf-8"), 0
        for i, js in enumerate(re.findall(r"<script>(.*?)</script>", page, re.S)):
            f = CACHE / f"{name}-{i}.js"
            f.write_text(js, encoding="utf-8")
            wrong += subprocess.call(["node", "--check", str(f)]) != 0
        print(f"dist/{name}: its scripts parse" if not wrong else f"dist/{name}: {wrong} script(s) do not parse")
        bad += wrong
    return 1 if bad else 0


def main(argv) -> int:
    n = int(argv[1]) if len(argv) > 1 else 200
    seed = int(argv[2]) if len(argv) > 2 else 1
    d = load()
    CACHE.mkdir(exist_ok=True)
    (CACHE / "data.json").write_text(json.dumps(travel_bundle(d)), encoding="utf-8")
    (CACHE / "cases.json").write_text(json.dumps(cases(d, n, seed)), encoding="utf-8")
    write_shared(d)
    env = {**os.environ, "TRAVEL_PARITY": "1"}
    rules = subprocess.call(["node", str(Path(__file__).parent / "test.js")], env=env)
    day = subprocess.call(["node", str(Path(__file__).parent / "day.js")], env=env)
    return rules or day or check_page()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
