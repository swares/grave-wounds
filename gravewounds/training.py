"""Training (data/training.yaml): a week with a teacher ticks the pupil's skill for End of season
(experience.py) if the teacher's check succeeds. Teachers are a master for hire (his skill
counts as master_skill, his fee in Days a week, in the places he is found), a teammate at least
teammate_gap better, or the army's drill in camp. The team builder and the travel map
(templates/ranks.js) repeat masters_for, teammate_ok, week and drill_week exactly."""
from __future__ import annotations

from .checks import check
from .model import Data

DRILL_DEFAULTS = {"camped_days": 4, "nco": 50, "difficulty": "ordinary"}


def masters_for(d: Data, eid: str, place: str | None, skill: str | None = None) -> list[dict]:
    """The masters to be hired in an era (one with his skill) at a kind of place (None: anywhere),
    for one skill or all."""
    have = {s["id"] for s in d.teams[eid]["skills"]}
    return [m for m in (d.training or {}).get("masters", []) if m["skill"] in have and (skill is None or m["skill"] == skill)
            and (place is None or place in m["places"])]


def teammate_ok(d: Data, teacher: int, pupil: int) -> bool:
    """A teammate can teach a skill he has at least teammate_gap above the pupil's."""
    return teacher >= pupil + (d.training or {}).get("teammate_gap", 20)


def week(d: Data, teacher: int, roll: int) -> dict:
    """A week's lessons: the teacher's check (Ordinary). -> check(): success ticks the pupil."""
    return check(d, teacher, "ordinary", roll)


def drill_week(d: Data, camped: int, best_command: int, roll: int) -> dict | None:
    """A force's week of drill: None if it camped fewer than camped_days days; else the check of
    the best Command with it (or the army's sergeants' nco, whichever is more)."""
    D = {**DRILL_DEFAULTS, **((d.training or {}).get("drill") or {})}
    if camped < D["camped_days"]:
        return None
    return check(d, max(best_command, D["nco"]), D["difficulty"], roll)
