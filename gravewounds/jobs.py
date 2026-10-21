"""Work (data/money.yaml work, data/jobs/<era>.yaml): the jobs a soldier or adventurer can take
between fights, to give the downtime action "earn money" a shape. A job names the skill it is
checked on and the least he needs to be hired, its pay in Days for each day worked, its term (a
day, a week, a month or a contract; or, with `lump`, a sum for the whole contract, `per` a
horse, a robe or a body), the places it is found, who may take it, its risk and a
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
    earned = j["pay"] * share * (1 if j.get("lump") else n)
    return {"check": check, "outcome": outcome, "days": n, "earned": earned, "trouble": trouble}


QUARTERS = {0: "", 1: "¼", 2: "½", 3: "¾"}


def pay_text(j: dict) -> str:
    """A job's pay, which is kept in quarter Days: '¾ Day a day', '1½ Days a day'."""
    q = round(j["pay"] * 4)
    if not q:
        return "unpaid"
    whole, part = divmod(q, 4)
    num = f"{whole:,}" if whole and not part else f"{whole if whole else ''}{QUARTERS[part]}"
    days = f"{num} Day{'s' if q > 4 else ''}"
    if j.get("lump"):
        return f"{days} {j['per']}" if j.get("per") else f"{days} for the job"
    return f"{days} a day"


def term_text(j: dict) -> str:
    """'a week', 'a contract of 7-21 days'."""
    if j["term"] != "contract":
        return {"day": "a day", "week": "a week", "month": "a month"}[j["term"]]
    lo, hi = j["days"]
    return f"{lo} day{'s' if lo > 1 else ''}" if lo == hi else f"{lo}-{hi} days"


def job_rows(d: Data, eid: str) -> list[list[str]]:
    """An era's jobs as a table, header first: lawful work, then the illegal (marked †)."""
    rows = [["Job", "Skill", "Pay", "Term", "Where", "Who", "Risk"]]
    names = {c["id"]: c["name"].lower() for c in d.teams[eid]["careers"]}
    skills = {s["id"]: s["name"] for s in d.teams[eid]["skills"]}
    for j in jobs_at(d, eid):
        skill = f"{skills[j['skill']]} {j.get('min', 0)}" if j.get("skill") else "none"
        who = "anyone" if j.get("who", "any") == "any" else ", ".join(names[w] for w in j["who"])
        rows.append([j["name"] + (" †" if j.get("illegal") else ""), skill, pay_text(j), term_text(j), ", ".join(j["places"]), who,
                     f"{j['risk']}%" if j.get("risk") else "none"])
    return rows


def trouble_rows(d: Data, eid: str) -> list[list[str]]:
    return [["d10", "Trouble"]] + [[str(t["roll"]), t["text"]] for t in jobs(d, eid)["trouble"]]


def work_rules(d: Data) -> list[str]:
    """Taking a job, as short rules for the PDF and Markdown (money.yaml work)."""
    W = d.money["work"]
    return [
        "<b>Finding work:</b> in a town, city, village, camp, on the road, the frontier or at sea, a man may take any job of his era found there "
        "that his career and skill allow (the job's least skill). Pay is in Days, a common soldier's day's pay, for each day worked, or a sum for a whole contract.",
        f"<b>A term:</b> a day, a week ({W['terms']['week']} days), a month ({W['terms']['month']} days) or a contract. One check on the job's skill a term: "
        f"at or under, full pay; over, {int(W['failure'] * 100)}%; {W['fumble_from']} or more and over, a fumble and nothing. A job with no skill pays in full.",
        "<b>Trouble:</b> a job with a risk takes one d100 a term: at or under the risk, trouble. The GM uses the job's hook, or rolls d10 on the era's trouble table. "
        "Jobs marked † are against the law.",
    ]
