"""Money and prices (data/money.yaml, data/equipment/<era>.yaml): each era's coins, a common
soldier's day's pay (a Day) in each, and priced kit. A price is kept as a whole number of the
coin's smallest unit (farthings for pounds, shillings and pence; kreuzer; cents), so nothing is
lost to rounding; Days are worked out from it, never stored. A character's purse is his
starting Days (money.yaml, per career term) plus his ledger: what he has earned at jobs and
spent since, as signed Days. The team builder page (templates/team.js) repeats fmt, row_days,
kit_value, purse, quarter_text, spend_check and shop exactly."""
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


def ledger_days(ledger: list | None) -> float:
    """What a character has earned less what he has spent since he was made, in Days."""
    return sum(e["days"] for e in ledger or [])


def purse(d: Data, eid: str, region: str, terms: int, ledger: list | None = None) -> dict:
    """A character's money: money.yaml's Days per career term, plus his ledger, and that sum in his
    region's coin where it has a Day (to the nearest smallest unit, halves up).
    -> {"days": float, "text": "£2 5s" or None}"""
    days = d.money.get("purse_days_per_term", 0) * terms + ledger_days(ledger)
    cid = region_currency(d, eid, region)
    cur = equipment(d, eid)["currencies"].get(cid) if cid else None
    text = fmt(cur, int(days * cur["day"] + 0.5)) if cur and cur.get("day") else None
    return {"days": days, "text": text}


QUARTERS = ("", "¼", "½", "¾")


def quarter_text(x: float) -> str:
    """Days to the nearest quarter, halves up: '104½', '1,200', '¾', '0'. Never below nothing."""
    q = int(max(x, 0) * 4 + 0.5)
    whole, part = divmod(q, 4)
    return f"{_group(whole)}{QUARTERS[part]}" if whole else (QUARTERS[part] or "0")


def spend_check(d: Data, c: dict, days: float) -> str | None:
    """Why he can't spend that many Days (nothing, or more than his purse holds), or None."""
    if not days or days <= 0:
        return "nothing to spend"
    have = purse(d, c["era"], c["region"], c["terms"], c.get("ledger"))["days"]
    return f"his purse holds {quarter_text(have)} Days" if days > have + 1e-9 else None


def spend(d: Data, c: dict, days: float, what: str) -> dict:
    """Take Days out of his purse for something bought or paid; raises ValueError if he can't."""
    why = spend_check(d, c, days)
    if why:
        raise ValueError(why)
    entry = {"days": -days, "what": what}
    c.setdefault("ledger", []).append(entry)
    return entry


def earn(c: dict, days: float, what: str) -> dict:
    """Put Days earned (a job's term) into his purse."""
    entry = {"days": days, "what": what}
    c.setdefault("ledger", []).append(entry)
    return entry


def shop(d: Data, eid: str, region: str) -> list[dict]:
    """What he can buy from the era's price list, in his Days: every row but pay, with a Day in
    his coin's family or its own, at the middle of a range, cheapest first within each category.
    -> [{"id", "name", "cat", "days", "text"}]"""
    E, out = equipment(d, eid), []
    for r in E["items"]:
        if r.get("cat") == "pay":
            continue
        span = row_days(d, eid, r, region)
        if span is None:
            continue
        cur = E["currencies"][r.get("in") or E["currency"]["default"]]
        name = r["name"] + (f" ({r['per']})" if r.get("per") else "")
        out.append({"id": r["id"], "name": name, "cat": r["cat"], "days": (span[0] + span[1]) / 2, "text": price_text(cur, r["price"])})
    order = sorted({r["cat"] for r in out})
    return sorted(out, key=lambda r: (order.index(r["cat"]), r["days"], r["name"]))


def days_text(x: float) -> str:
    """About how many Days: '43', 'under 1'. Halves round up, as team.js's Math.round."""
    return "under 1" if x < 1 else f"{int(x + 0.5):,}"


def money_line(d: Data, c: dict) -> str:
    """'Kit worth about 43 Days; purse 90 Days (£2 5s)' for a character sheet."""
    v = kit_value(d, c["era"], c["region"], c["kit"], c["weapon"])
    p = purse(d, c["era"], c["region"], c["terms"], c.get("ledger"))
    if v["unpriced"] and not v["days"]:
        kit = "kit not priced"
    else:
        kit = f"kit worth about {days_text(v['days'])} Days" + (" (part not priced)" if v["unpriced"] else "")
    coin = f" ({p['text']})" if p["text"] else ""
    return f"{kit[0].upper()}{kit[1:]}; purse {quarter_text(p['days'])} Days{coin}"
