"""Work (data/money.yaml work, data/jobs/<era>.yaml): the jobs a soldier or adventurer can take
between fights, to give the downtime action "earn money" a shape. A job names the skill it is
checked on and the least he needs to be hired, its pay in Days for each day worked, its term (a
day, a week, a month or a contract), the places it is found, who may take it, its risk and a
hook. One skill check a term settles the pay (in full, half, or nothing on a fumble); one d100
a term at or under the risk brings trouble. The team builder page (templates/team.js) repeats
can_take and work_term exactly."""
from __future__ import annotations

from .model import Data

PLACES = ("town", "city", "village", "camp", "road", "frontier", "sea")
TERMS = ("day", "week", "month", "contract")


def jobs(d: Data, eid: str) -> dict:
    """An era's jobs file, or an empty one."""
    return d.jobs.get(eid) or {"jobs": [], "trouble": []}


def job(d: Data, eid: str, jid: str) -> dict:
    return next(j for j in jobs(d, eid)["jobs"] if j["id"] == jid)


def jobs_at(d: Data, eid: str, place: str | None = None) -> list[dict]:
    """The jobs going in a kind of place (all of them for no place), lawful first, then by pay."""
    rows = [j for j in jobs(d, eid)["jobs"] if place is None or place in j["places"]]
    return sorted(rows, key=lambda j: (bool(j.get("illegal")), -j["pay"], j["name"]))


def can_take(j: dict, c: dict) -> tuple[bool, str | None]:
    """(hired, why not): his career is among the job's `who` (or it is open to anyone), and his
    skill is at least its `min`."""
    who = j.get("who", "any")
    if who != "any" and c["career"] not in who:
        return False, "not his trade"
    if j.get("skill") and c["skills"].get(j["skill"], 0) < j.get("min", 0):
        return False, f"needs {j['skill']} {j['min']}"
    return True, None


def term_days(d: Data, j: dict, days: int | None = None) -> int:
    """How many days a term of the job runs: the term's length, or for a contract its `days`
    (low, high: the GM picks; the low end unless told)."""
    if days is not None:
        return days
    if j["term"] == "contract":
        lo = j["days"][0] if isinstance(j.get("days"), list) else j.get("days", 1)
        return lo
    return d.money["work"]["terms"][j["term"]]


def work_term(d: Data, eid: str, j: dict, c: dict, rng, days: int | None = None) -> dict:
    """One term of a job: the skill check (none for a job with no skill), then the trouble roll
    for a job with a risk, in that order (team.js takes the dice the same way).
    -> {"check", "outcome": success | failure | fumble, "days", "earned" (in Days), "trouble"
        (None, or {"roll", "text"} from the era's trouble table on a d10)}"""
    W = d.money["work"]
    n = term_days(d, j, days)
    check, outcome = None, "success"
    if j.get("skill"):
        check = rng.randint(1, 100)
        skill = c["skills"].get(j["skill"], 0)
        outcome = "success" if check <= skill else ("fumble" if check >= W["fumble_from"] else "failure")
    share = {"success": W["success"], "failure": W["failure"], "fumble": 0}[outcome]
    trouble = None
    if j.get("risk"):
        t = rng.randint(1, 100)
        if t <= j["risk"]:
            table = jobs(d, eid)["trouble"]
            pick = rng.randint(1, len(table)) if table else None
            trouble = {"roll": t, "text": table[pick - 1]["text"] if pick else j.get("hook", "")}
    return {"check": check, "outcome": outcome, "days": n, "earned": j["pay"] * n * share, "trouble": trouble}


QUARTERS = {0: "", 1: "¼", 2: "½", 3: "¾"}


def pay_text(j: dict) -> str:
    """A job's pay, which is kept in quarter Days: '¾ Day a day', '1½ Days a day'."""
    q = round(j["pay"] * 4)
    whole, part = divmod(q, 4)
    num = f"{whole if whole or not part else ''}{QUARTERS[part]}"
    return f"{num} Day{'s' if q > 4 else ''} a day"
