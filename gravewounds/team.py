"""Character generation (docs/team.md): a team of four to six made in a few rolls each, from an
era's tables (data/teams/<era>.yaml). The team builder page (templates/team.js) repeats these
rules exactly; build.py precomputes the old-wound location ranges both use."""
from __future__ import annotations

from . import engine as E
from .model import Data


def era(d: Data, eid: str) -> dict:
    return d.teams[eid]


def _by_id(rows: list, rid: str) -> dict:
    return next(r for r in rows if r["id"] == rid)


def old_wound_ranges(d: Data, eid: str) -> dict:
    """{region id: {weapon id: [[location, up to d100], ...]}}: where an old wound falls, rolled on
    the region's hit-location table for each weapon careers are hurt by."""
    T, out = era(d, eid), {}
    weapons = sorted({c["wound_weapon"] for c in T["careers"]})
    for r in T["regions"]:
        out[r["id"]] = {w: [[x["id"], x["hi"]] for x in E.to_d100(E.effective_weights(d, r["table"], w))] for w in weapons}
    return out


def _pick(rows: list, roll: int) -> dict:
    """The row for a d100 roll on [{to, ...}]."""
    return next(r for r in rows if roll <= r["to"])


def _fresh(rows: list, roll: int, had: list) -> dict:
    """The term row for a d100 roll; one whose event he has already had moves to the next row
    down (round to the top)."""
    i = rows.index(_pick(rows, roll))
    while rows[i]["text"] in had:
        i = (i + 1) % len(rows)
    return rows[i]


def _at(ranges: list, roll: int) -> str:
    return next(loc for loc, hi in ranges if roll <= hi)


def kit_for(T: dict, career: dict, region: str) -> tuple:
    """(armour kit, weapon) for a career in a region."""
    k, w = career["kit"], career["weapon"]
    return k.get(region, k["default"]), w.get(region, w["default"])


def _stats(T: dict, career: dict, mode: str, rng) -> dict:
    """Characteristics before any change: 3d6 x 5 each, in order, or the fixed array placed by
    the career's preferences."""
    if mode == "array":
        return dict(zip(career["prefers"], T["array"]))
    return {c["id"]: 5 * sum(rng.randint(1, 6) for _ in range(3)) for c in T["characteristics"]}


def _apply(mod: dict, stat_mods: dict, gains: dict) -> None:
    """A trait or drawback: characteristics into stat_mods, skills into gains (text ignored)."""
    for k, v in mod.items():
        if k == "text":
            continue
        target = stat_mods if k in stat_mods else gains
        target[k] = target.get(k, 0) + v


def make_character(d: Data, eid: str, region: str, career_id: str, terms: int, mode: str, rng,
                   ranges: dict | None = None) -> dict:
    """One character: characteristics, origin, career terms with their events and old wounds,
    name, look and kit. mode: roll (3d6 x 5) or array. The dice are taken in a fixed order
    (team.js takes them the same way): the characteristics, the origin, each term (the row,
    then the wound chance unless the row always wounds, then the wound's location and kind),
    the name and the look."""
    T = era(d, eid)
    career = _by_id(T["careers"], career_id)
    ranges = ranges or old_wound_ranges(d, eid)
    base = _stats(T, career, mode, rng)
    stat_mods = {c["id"]: 0 for c in T["characteristics"]}
    gains: dict = {}
    origin = T["origins"][(rng.randint(1, 100) - 1) * len(T["origins"]) // 100]
    gains[origin["gain"]] = gains.get(origin["gain"], 0) + T["gain"]
    _apply(origin["trait"], stat_mods, gains)
    _apply(origin["drawback"], stat_mods, gains)
    events, old = [], []
    for k in range(terms):
        row = _fresh(career["terms"], rng.randint(1, 100), events)
        for skill, n in ((career["main"], T["first_term"] if k == 0 else T["term_main"]), (career["second"], T["term_second"]), (row["skill"], T["gain"])):
            gains[skill] = gains.get(skill, 0) + n
        events.append(row["text"])
        if row.get("wound") or rng.randint(1, 100) <= career["wound"]:
            old.append(_old_wound(d, T, ranges[region][career["wound_weapon"]], career["wound_weapon"], stat_mods, rng))
    reg = _by_id(T["regions"], region)
    name = f"{reg['names'][rng.randint(1, len(reg['names'])) - 1]} {reg['bynames'][rng.randint(1, len(reg['bynames'])) - 1]}"
    beards = ["", "moustache", "beard", "stubble"]
    look = {"colour": reg["colours"][rng.randint(1, len(reg["colours"])) - 1], "beard": beards[rng.randint(1, 4) - 1]}
    kit, weapon = kit_for(T, career, region)
    c = {"name": name, "era": eid, "region": region, "career": career_id, "terms": terms, "mode": mode,
         "base": base, "stat_mods": stat_mods, "gains": gains, "origin": origin["name"],
         "trait": origin["trait"]["text"], "drawback": origin["drawback"]["text"], "events": events, "old": old,
         "age": T["age"]["start"] + T["age"]["per_term"] * terms, "kit": kit, "weapon": weapon, "look": look}
    return finish(d, c)


def _old_wound(d: Data, T: dict, ranges: list, weapon: str, stat_mods: dict, rng) -> dict:
    """An old wound: where (the region's table), then a healed mark or a lasting hurt."""
    loc = _at(ranges, rng.randint(1, 100))
    kind = _pick(T["old_wound"], rng.randint(1, 100))["kind"]
    w = {"loc": loc, "weapon": weapon, "kind": kind}
    if kind == "lasting":
        L = d.loc[loc]
        stat = T["lasting_from"]["face" if L["class"] == "face" else L["zone"]]
        stat_mods[stat] -= T["lasting"]
        w["stat"] = stat
    return w


def finish(d: Data, c: dict) -> dict:
    """The derived figures, from base characteristics, their changes and the skill gains:
    stats, skills, attack (his weapon's skill), defence (best of parry and dodge), nerve."""
    T = era(d, c["era"])
    lo, hi = T["stat_range"]
    c["stats"] = {k: max(lo, min(hi, v + c["stat_mods"][k])) for k, v in c["base"].items()}
    c["skills"] = {s["id"]: max(0, min(T["skill_max"], c["stats"][s["of"]] // s["div"] + c["gains"].get(s["id"], 0))) for s in T["skills"]}
    c["attack"] = attack_for(T, c, c["weapon"])
    c["defence"] = max(c["skills"][s] for s in T["defence"])
    c["nerve"] = c["stats"]["nerve"]
    return c


def attack_for(T: dict, c: dict, weapon: str) -> int | None:
    """His attack % with a weapon: the skill it is fought with; None for a weapon with no skill."""
    s = T["weapon_skill"].get(weapon)
    return c["skills"][s] if s else None


def make_team(d: Data, eid: str, region: str, template: str, mode: str, rng) -> list[dict]:
    """A team from a template: one character a slot, the first its leader."""
    T, ranges = era(d, eid), old_wound_ranges(d, eid)
    team = [make_character(d, eid, region, cid, n, mode, rng, ranges) for cid, n in _by_id(T["templates"], template)["slots"]]
    team[0]["leader"] = True
    return team


def sheet(d: Data, c: dict) -> list[str]:
    """A character as lines of text."""
    T = era(d, c["era"])
    career = _by_id(T["careers"], c["career"])
    names = {s["id"]: s["name"] for s in T["skills"]}
    stats = ", ".join(f"{x['name'][:3]} {c['stats'][x['id']]}" for x in T["characteristics"])
    trained = ", ".join(f"{names[k]} {c['skills'][k]}" for k in names if c["gains"].get(k, 0) > 0)
    lines = [f"{c['name']}{' (leader)' if c.get('leader') else ''}: {career['name'].lower()}, {c['terms']} term{'s' if c['terms'] > 1 else ''}, age {c['age']}",
             f"  {stats}",
             f"  Origin: {c['origin'].lower()}. {c['trait']}; {c['drawback'].lower()}.",
             f"  Skills: {trained}",
             f"  Arms: {d.weapons[c['weapon']]['name']} (attack {c['attack']}%), defence {c['defence']}%; {d.armor['kits'][c['kit']]['name']}"]
    lines += [f"  Term {i + 1}: {e}" for i, e in enumerate(c["events"])]
    for w in c["old"]:
        hurt = f", {T['lasting']} off {_by_id(T['characteristics'], w['stat'])['name']}" if w["kind"] == "lasting" else ""
        lines.append(f"  Old wound: {d.loc[w['loc']]['name'].lower()}, from a {d.weapons[w['weapon']]['short'].lower()}: {'a lasting hurt' if w['kind'] == 'lasting' else 'a healed scar'}{hurt}")
    return lines
