"""Calendar, daylight, daily weather, the ground, rest and fatigue (Grave Wounds).
Mirrored exactly by the travel page (templates/travel.html), between its 'shared with
gravewounds/weather.py' markers. Dates are whole numbers of days (Julian Day Numbers), so
the calendar sums are the same in both languages."""
from __future__ import annotations

import math

from .model import Data


# ---------- calendar ----------

def jdn(y: int, m: int, d: int, calendar: str) -> int:
    """Julian Day Number of a date in the Julian or Gregorian calendar."""
    a = (14 - m) // 12
    yy = y + 4800 - a
    mm = m + 12 * a - 3
    n = d + (153 * mm + 2) // 5 + 365 * yy + yy // 4 - 32083
    if calendar == "gregorian":
        n = n - yy // 100 + yy // 400 + 38
    return n


def from_jdn(n: int, calendar: str) -> tuple[int, int, int]:
    """(year, month, day) of a Julian Day Number in the calendar named."""
    if calendar == "gregorian":
        a = n + 32044
        b = (4 * a + 3) // 146097
        c = a - 146097 * b // 4
    else:
        b = 0
        c = n + 32082
    dd = (4 * c + 3) // 1461
    e = c - 1461 * dd // 4
    mm = (5 * e + 2) // 153
    day = e - (153 * mm + 2) // 5 + 1
    month = mm + 3 - 12 * (mm // 10)
    year = 100 * b + dd - 4800 + mm // 10
    return year, month, day


def parse_date(s: str) -> tuple[int, int, int]:
    neg = s.startswith("-")
    y, m, d = (int(x) for x in s.lstrip("-").split("-"))
    return (-y if neg else y), m, d


def map_date(m: dict, day: int) -> tuple[int, int, int]:
    """The date, in the map's own calendar, of day `day` (day 1 is the start date)."""
    y, mo, d = parse_date(m["start_date"])
    return from_jdn(jdn(y, mo, d, m["calendar"]) + day - 1, m["calendar"])


def solar_day_of_year(m: dict, day: int) -> int:
    """Day of the year 1-366 in the Gregorian calendar, which keeps step with the sun."""
    n = jdn(*parse_date(m["start_date"]), m["calendar"]) + day - 1
    y, _, _ = from_jdn(n, "gregorian")
    return n - jdn(y, 1, 1, "gregorian") + 1


def days_in_month(y: int, mo: int, calendar: str) -> int:
    ny, nm = (y + 1, 1) if mo == 12 else (y, mo + 1)
    return jdn(ny, nm, 1, calendar) - jdn(y, mo, 1, calendar)


# ---------- daylight ----------

def daylight(lat: float, doy: int) -> float:
    """Hours from sunrise to sunset (a simple solar model, good to a few minutes)."""
    rad = math.pi / 180
    decl = 23.44 * math.sin(2 * math.pi * (284 + doy) / 365)
    x = max(-1.0, min(1.0, -math.tan(lat * rad) * math.tan(decl * rad)))
    return 2 * (math.acos(x) * 180 / math.pi) / 15


def march_window(d: Data, m: dict, day: int) -> dict:
    """When the force can march on this day: {start, hours, sunrise, sunset} in hours of the
    day, local solar time. start and hours are on the quarter hour."""
    DL = d.weather["daylight"]
    dl = daylight(m["latitude"], solar_day_of_year(m, day))
    sunrise, sunset = 12 - dl / 2, 12 + dl / 2
    start = math.ceil((sunrise + DL["start_after_sunrise"]) * 4 - 1e-9) / 4
    end = math.floor((sunset - DL["stop_before_sunset"]) * 4 + 1e-9) / 4
    hours = max(DL["min_hours"], min(d.terrain["hours_per_day"], end - start))
    return {"start": start, "hours": hours, "sunrise": sunrise, "sunset": sunset}


# ---------- weather ----------

def _pick(rows: list, roll: int) -> dict:
    return next(r for r in rows if roll <= r["upto"])


def roll_weather(d: Data, m: dict, day: int, prev: dict | None, rolls: list[int]) -> dict:
    """A day's weather from five d100 rolls [wet, intensity or cloud, warmth, fog, wind] and
    the day before (None on the first day). {cond, wind, high, low, anomaly}."""
    WX = d.weather
    cl = WX["climates"][m["climate"]]
    y, mo, _ = map_date(m, day)
    dim = days_in_month(y, mo, m["calendar"])
    p = cl["rain"][mo - 1] / dim
    r = WX["persistence"]
    wet_before = bool(prev) and WX["conditions"][prev["cond"]]["precip"] != "none"
    pw = p + r * (1 - p) if wet_before else p * (1 - r)
    wet = rolls[0] <= math.floor(pw * 100 + 0.5)
    carry = math.trunc((prev["anomaly"] if prev else 0) * WX["anomaly_carry"])
    anomaly = carry + _pick(WX["anomaly"], rolls[2])["deg"]
    shift = m.get("climate_shift", 0)
    high = cl["high"][mo - 1] + shift + anomaly
    low = cl["low"][mo - 1] + shift + anomaly
    if wet:
        row = _pick(WX["intensity"], rolls[1])
        cond = row["snow"] if high <= WX["snow_at_or_below"] else row["rain"]
    elif rolls[3] <= math.floor(cl["fog"][mo - 1] / dim * 100 + 0.5):
        cond = "fog"
    else:
        cond = "fair" if rolls[1] <= WX["fair_upto"] else "overcast"
    winds = WX["winds"]
    wind = _pick(winds, rolls[4])["id"]
    floor_wind = WX["conditions"][cond].get("min_wind")
    ids = [w["id"] for w in winds]
    if floor_wind and ids.index(wind) < ids.index(floor_wind):
        wind = floor_wind
    return {"cond": cond, "wind": wind, "high": high, "low": low, "anomaly": anomaly}


def next_ground(d: Data, prev: dict | None, w: dict) -> dict:
    """The ground at the end of a day with weather w: {mud, snow, flood} (levels and days)."""
    G = d.weather["ground"]
    g = dict(prev) if prev else {"mud": 0, "snow": 0, "flood": 0}
    cond = w["cond"]
    precip = d.weather["conditions"][cond]["precip"]
    if cond in G["mud_add"]:
        g["mud"] = min(G["mud_max"], g["mud"] + G["mud_add"][cond])
    elif precip == "none":
        g["mud"] = max(0, g["mud"] - (G["mud_dry_warm"] if w["high"] >= G["warm_at"] else G["mud_dry"]))
    if cond in G["snow_add"]:
        g["snow"] = min(G["snow_max"], g["snow"] + G["snow_add"][cond])
    elif w["high"] > d.weather["snow_at_or_below"]:
        g["snow"] = max(0, g["snow"] - (G["snow_melt_mild"] if w["high"] >= G["mild_at"] else G["snow_melt"]))
    g["flood"] = G["flood_days"] if cond in G["flood_from"] else max(0, g["flood"] - 1)
    return g


def terrain_pct(d: Data, tid: str, ground: dict | None) -> int:
    """% of a terrain's time cost on this ground (100 = as dry)."""
    if not ground:
        return 100
    M = d.weather["march"]
    pct = 100
    if ground.get("mud", 0) >= 1:
        pct = max(pct, M["mud"].get(tid, 100))
    if ground.get("snow", 0) >= 1:
        pct = max(pct, M["snow"].get(tid, 100))
    return pct


def flooded(d: Data, tid: str, ground: dict | None) -> bool:
    return bool(ground and ground.get("flood", 0) > 0 and tid in d.weather["march"]["flooded"])


# ---------- rest and fatigue ----------

def night_rest(d: Data, camp: str | None, w: dict) -> int:
    """How well men sleep: index into rest_levels (0 bad ... 3 good)."""
    WX = d.weather
    levels = WX["rest_levels"]
    base = levels.index(d.works["camps"][camp]["rest"]) if camp else levels.index("poor")
    cold = max([c["add"] for c in WX["cold_hardship"] if w["low"] <= c["low_at_or_below"]] or [0])
    hardship = WX["conditions"][w["cond"]]["hardship"] + cold
    shelter = WX["shelter"][camp or "none"]
    return max(0, base - max(0, hardship - shelter))


def fatigue_after(d: Data, fatigue: int, marched: float, w: dict, ground: dict, rest: int) -> int:
    """Fatigue level next morning, from the day's marching and weather and the night's rest."""
    F = d.weather["fatigue"]
    add = 0
    if marched >= F["heat_cold_min_hours"] - 1e-9:
        for h in F["heat"]:
            if w["high"] >= h["high_at_or_over"]:
                add = max(add, h["add"])
        for c in F["cold"]:
            if w["high"] <= c["high_at_or_below"]:
                add = max(add, c["add"])
    deep = d.weather["ground"]["deep"]
    if marched >= F["heavy_going_hours"] - 1e-9 and (ground.get("mud", 0) >= deep or ground.get("snow", 0) >= deep):
        add += 1
    add += F["night"][d.weather["rest_levels"][rest]]
    return max(0, min(len(F["levels"]) - 1, fatigue + add))
