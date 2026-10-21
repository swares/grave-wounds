"""Money and prices (data/money.yaml, data/equipment/<era>.yaml): each era's coins, a common
soldier's day's pay (a Day) in each, and priced kit. A price is kept as a whole number of the
coin's smallest unit (farthings for pounds, shillings and pence; kreuzer; cents), so nothing is
lost to rounding; Days are worked out from it, never stored. The team builder page
(templates/team.js) repeats fmt, row_days, kit_value and purse exactly."""
from __future__ import annotations

from fractions import Fraction

from .model import Data

FRACTIONS = {Fraction(1, 4): "¼", Fraction(1, 2): "½", Fraction(3, 4): "¾", Fraction(1, 3): "⅓", Fraction(2, 3): "⅔"}


def equipment(d: Data, eid: str) -> dict:
    """An era's equipment file, or an empty one."""
    return d.equipment.get(eid) or {"currencies": {}, "currency": {}, "items": []}


def currency(d: Data, eid: str, cid: str) -> dict:
    return equipment(d, eid)["currencies"][cid]


def region_currency(d: Data, eid: str, region: str | None) -> str | None:
    """The coin a region's soldiers were paid in: its own, or the era's default."""
    c = equipment(d, eid).get("currency") or {}
    return c.get(region, c.get("default")) if c else None


def _group(n: int) -> str:
    return f"{n:,}"


def fmt(cur: dict, amount: int) -> str:
    """An amount of base units as the period wrote it: £8 6s 8d, 6½d, 4 Rt 30 kr, $12.54, 75¢."""
    dec = cur.get("decimal")
    if dec:
        per = dec["per"]
        if amount < per and dec.get("small"):
            return f"{amount}{dec['small']}"
        whole, part = divmod(amount, per)
        return f"{dec['sym']}{_group(whole)}" + (f".{part:0{len(str(per)) - 1}d}" if part else "") + dec.get("suf", "")
    out, left = [], amount
    units = cur["units"]
    for i, u in enumerate(units):
        n, left = divmod(left, u["of"])
        last = i == len(units) - 1
        frac = FRACTIONS.get(Fraction(left, u["of"]), f" {left}/{u['of']}") if last and left else ""
        if n or frac:
            num = f"{_group(n) if n else ''}{frac}"
            out.append(f"{u['sym']}{num}" if u.get("pre") else f"{num}{u['sym']}")
    return " ".join(out) or "nothing"


def price_text(cur: dict, price) -> str:
    """A price or a low-high range: '12s-30s'."""
    if isinstance(price, list):
        return f"{fmt(cur, price[0])}–{fmt(cur, price[1])}"
    return fmt(cur, price)


def _span(price) -> tuple[int, int]:
    return (price[0], price[1]) if isinstance(price, list) else (price, price)


def row_days(d: Data, eid: str, row: dict, region: str | None = None) -> tuple[float, float] | None:
    """A row's price in Days (low, high). Seen from a region whose coin is of the same family as
    the row's, the region's Day is used (a Taliban fighter's dollar Day, not an American
    soldier's); otherwise the row's own coin's Day. None when that coin has no Day."""
    E = equipment(d, eid)
    cid = row.get("in") or E["currency"]["default"]
    cur = E["currencies"][cid]
    rc = region_currency(d, eid, region) if region else None
    if rc and E["currencies"][rc].get("coin") == cur.get("coin"):
        cur = E["currencies"][rc]
    if not cur.get("day"):
        return None
    lo, hi = _span(row["price"])
    return lo / cur["day"], hi / cur["day"]


def _linked(row: dict, key: str, value: str, region: str) -> bool:
    links = row.get(key)
    links = [links] if isinstance(links, str) else (links or [])
    return value in links and region in row.get("regions", [region])


def kit_value(d: Data, eid: str, region: str, kit: str, weapon: str) -> dict:
    """What a character's issued armour kit and weapon are worth, in Days: the sum of every
    priced row linked to them (a kit or weapon may be several rows: a brigandine and a sallet, a
    longbow and its arrows). Ranges are taken at their middle. 'none' armour is worth nothing.
    -> {"days": float, "unpriced": [what has no price]}"""
    rows, total, unpriced = equipment(d, eid)["items"], 0.0, []
    for key, value in (("kit", kit), ("weapon", weapon)):
        if key == "kit" and value == "none":
            continue
        found = [r for r in rows if _linked(r, key, value, region)]
        spans = [row_days(d, eid, r, region) for r in found]
        if not found or any(s is None for s in spans):
            unpriced.append(value)
            continue
        total += sum((lo + hi) / 2 for lo, hi in spans)
    return {"days": total, "unpriced": unpriced}


def purse(d: Data, eid: str, region: str, terms: int) -> dict:
    """A new character's money: money.yaml's Days per career term, and that sum in his region's
    coin where it has a Day. -> {"days": int, "text": "£2 5s" or None}"""
    days = d.money.get("purse_days_per_term", 0) * terms
    cid = region_currency(d, eid, region)
    cur = equipment(d, eid)["currencies"].get(cid) if cid else None
    text = fmt(cur, days * cur["day"]) if cur and cur.get("day") else None
    return {"days": days, "text": text}


def days_text(x: float) -> str:
    """About how many Days: '43', 'under 1'. Halves round up, as team.js's Math.round."""
    return "under 1" if x < 1 else f"{int(x + 0.5):,}"


def money_line(d: Data, c: dict) -> str:
    """'Kit worth about 43 Days; purse 90 Days (£2 5s)' for a character sheet."""
    v = kit_value(d, c["era"], c["region"], c["kit"], c["weapon"])
    p = purse(d, c["era"], c["region"], c["terms"])
    if v["unpriced"] and not v["days"]:
        kit = "kit not priced"
    else:
        kit = f"kit worth about {days_text(v['days'])} Days" + (" (part not priced)" if v["unpriced"] else "")
    coin = f" ({p['text']})" if p["text"] else ""
    return f"{kit[0].upper()}{kit[1:]}; purse {p['days']} Days{coin}"
