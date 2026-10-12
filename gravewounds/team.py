"""Character generation (docs/team.md): a team of four to six made in a few rolls each, from an
era's tables (data/teams/<era>.yaml). The team builder page (templates/team.js) repeats these
rules exactly; build.py precomputes the old-wound location ranges both use."""
from __future__ import annotations

import re

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


# Women under arms (docs/team.md): a region's `women` block opens careers to women, at a share
# of the army's soldiers (in %, to two places; rolled on 1-10000); `no_women` says why a region
# has none. A woman takes the women's names (or the men's, for a woman who enlisted disguised
# as a man), no beard, and her own origins (`who: f`; `who: m` rows are men's only).
SHARE_DIE = 10000


def women_of(tables: dict, region: str) -> dict | None:
    """The region's women block, or None."""
    return _by_id(tables["regions"], region).get("women")


def open_to_women(tables: dict, region: str, career_id: str) -> tuple:
    """(open, why not): whether women can take this career in this region, and if not, why."""
    W = women_of(tables, region)
    if not W:
        return False, _by_id(tables["regions"], region).get("no_women") or "No women served in this army's fighting careers in these tables."
    if career_id not in W["careers"]:
        return False, W.get("closed") or "Closed to women in this army."
    return True, None


def _sex(tables: dict, region: str, career_id: str, sex: str, rng) -> str:
    """m or f: as chosen, or (roll) d10000 at or under the region's share x 100, for a career
    open to women in a region with a known share (no roll otherwise: a man)."""
    ok = open_to_women(tables, region, career_id)[0]
    if sex == "roll":
        share = (women_of(tables, region) or {}).get("share") if ok else None
        return "f" if share is not None and rng.randint(1, SHARE_DIE) <= round(share * 100) else "m"
    return "f" if sex == "f" and ok else "m"


def _name(reg: dict, sex: str, rng) -> str:
    """A name from the region's lists (a woman's from its women's lists, where it has them)."""
    W = (reg.get("women") or {}) if sex == "f" else {}
    names, bynames = W.get("names") or reg["names"], W.get("bynames") or reg["bynames"]
    return f"{names[rng.randint(1, len(names)) - 1]} {bynames[rng.randint(1, len(bynames)) - 1]}"


def _look(reg: dict, sex: str, rng) -> dict:
    """Coat colour and beard (both always rolled); a woman has no beard, and long hair."""
    beards = ["", "moustache", "beard", "stubble"]
    look = {"colour": reg["colours"][rng.randint(1, len(reg["colours"])) - 1], "beard": beards[rng.randint(1, 4) - 1]}
    if sex == "f":
        look.update(beard="", hair="long")
    return look


def origins_for(tables: dict, sex: str) -> list:
    """The origins a man or a woman rolls on: the shared rows and his or her own (`who`)."""
    return [o for o in tables["origins"] if o.get("who", sex) == sex]


PRONOUNS = {"he": "she", "He": "She", "his": "her", "His": "Her", "him": "her", "Him": "Her", "himself": "herself", "Himself": "Herself"}


def pron(text: str, sex: str = "m") -> str:
    """A table's text (written of a man) said of a woman: he, his, him and himself become hers."""
    if sex != "f":
        return text
    return re.sub(r"\b(" + "|".join(PRONOUNS) + r")\b", lambda m: PRONOUNS[m.group(1)], text)


def kit_for(career: dict, region: str) -> tuple:
    """(armour kit, weapon) for a career in a region."""
    k, w = career["kit"], career["weapon"]
    return k.get(region, k["default"]), w.get(region, w["default"])


def _stats(tables: dict, career: dict, mode: str, rng) -> dict:
    """Characteristics before any change: 3d6 x 5 each, in order, or the fixed array placed by
    the career's preferences."""
    if mode == "array":
        return dict(zip(career["prefers"], tables["array"]))
    return {c["id"]: 5 * sum(rng.randint(1, 6) for _ in range(3)) for c in tables["characteristics"]}


def _apply(mod: dict, stat_mods: dict, gains: dict) -> None:
    """A trait or drawback: characteristics into stat_mods, skills into gains (text ignored)."""
    for k, v in mod.items():
        if k == "text":
            continue
        target = stat_mods if k in stat_mods else gains
        target[k] = target.get(k, 0) + v


def make_character(d: Data, eid: str, region: str, career_id: str, terms: int, mode: str, rng,
                   ranges: dict | None = None, sex: str = "m") -> dict:
    """One character: characteristics, origin, career terms with their events and old wounds,
    name, look and kit. mode: roll (3d6 x 5) or array. The dice are taken in a fixed order
    (team.js takes them the same way): man or woman (only for sex "roll", at the region's
    share), the characteristics, the origin, each term (the row, then the wound chance unless
    the row always wounds, then the wound's location and kind), the name and the look."""
    T = era(d, eid)
    career = _by_id(T["careers"], career_id)
    ranges = ranges or old_wound_ranges(d, eid)
    sex = _sex(T, region, career_id, sex, rng)
    base = _stats(T, career, mode, rng)
    stat_mods = {c["id"]: 0 for c in T["characteristics"]}
    gains: dict = {}
    rows = origins_for(T, sex)
    origin = rows[(rng.randint(1, 100) - 1) * len(rows) // 100]
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
    name, look = _name(reg, sex, rng), _look(reg, sex, rng)
    kit, weapon = kit_for(career, region)
    c = {"name": name, "sex": sex, "era": eid, "region": region, "career": career_id, "terms": terms, "mode": mode,
         "base": base, "stat_mods": stat_mods, "gains": gains, "origin": origin["name"],
         "trait": origin["trait"]["text"], "drawback": origin["drawback"]["text"], "events": events, "old": old,
         "age": T["age"]["start"] + T["age"]["per_term"] * terms, "kit": kit, "weapon": weapon, "look": look}
    return finish(d, c)


def make_follower(d: Data, eid: str, region: str, career_id: str, table: str, rng, women: str = "none") -> dict:
    """One follower: a quality (d100 on the followers' `table`), man or woman (women "roll":
    at the region's share, for a career open to women), then a name and a look, in that order
    (team.js the same). Attack, defence and Nerve are the quality's (units.yaml); kit and
    weapon the career's in the region."""
    T = era(d, eid)
    career = _by_id(T["careers"], career_id)
    quality = _pick(T["followers"]["quality"][table], rng.randint(1, 100))["quality"]
    q = d.units["quality"][quality]
    sex = _sex(T, region, career_id, "roll", rng) if women == "roll" else "m"
    reg = _by_id(T["regions"], region)
    name, look = _name(reg, sex, rng), _look(reg, sex, rng)
    kit, weapon = kit_for(career, region)
    return {"name": name, "sex": sex, "career": career_id, "quality": quality, "attack": q["attack"], "defence": q["defence"],
            "nerve": q["nerve"], "kit": kit, "weapon": weapon, "look": look, "mounted": bool(career.get("mounted"))}


def make_followers(d: Data, eid: str, region: str, counts: list, table: str, rng, women: str = "none") -> list[dict]:
    """The followers: counts [[career, n], ...], in order."""
    return [make_follower(d, eid, region, cid, table, rng, women) for cid, n in counts for _ in range(n)]


def follower_line(d: Data, f: dict, eid: str = "medieval") -> str:
    """A follower in one line: "John Archer, archer, regular: bow 50%, defence 35%, Nerve 50; jack and sallet"."""
    career = _by_id(era(d, eid)["careers"], f["career"])
    return (f"{f['name']}{' (a woman)' if f.get('sex') == 'f' else ''}, {career['name'].lower()}, {f['quality']}: {d.weapons[f['weapon']]['short'].lower()} {f['attack']}%, "
            f"defence {f['defence']}%, Nerve {f['nerve']}; {d.armor['kits'][f['kit']]['name'].split(' (')[0].lower()}")


def _old_wound(d: Data, tables: dict, ranges: list, weapon: str, stat_mods: dict, rng) -> dict:
    """An old wound: where (the region's table), then a healed mark or a lasting hurt."""
    T = tables
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


def attack_for(tables: dict, c: dict, weapon: str) -> int | None:
    """His attack % with a weapon: the skill it is fought with; None for a weapon with no skill."""
    s = tables["weapon_skill"].get(weapon)
    return c["skills"][s] if s else None


def make_team(d: Data, eid: str, region: str, template: str, mode: str, rng, women: str = "none") -> list[dict]:
    """A team from a template: one character a slot, the first its leader. women "roll": each
    rolled man or woman at the region's share."""
    T, ranges = era(d, eid), old_wound_ranges(d, eid)
    sex = "roll" if women == "roll" else "m"
    team = [make_character(d, eid, region, cid, n, mode, rng, ranges, sex) for cid, n in _by_id(T["templates"], template)["slots"]]
    team[0]["leader"] = True
    return team


def _a(word: str) -> str:
    """'a mortar', 'an assault rifle'."""
    return ("an " if word[:1] in "aeiou" else "a ") + word


def fight_line(d: Data, c: dict) -> str:
    """What his characteristics do in a fight (combat.py): Blood, initiative, toil, and as leader, morale."""
    from .combat import blood_pool, toil_blows
    s, per = c["stats"], d.wounds["combat"]["characteristics"]
    bits = [f"Blood {blood_pool(d, s['end'])}", f"initiative d{per['initiative']['die']}+{s['agi'] // per['initiative']['agi_per']}",
            f"tires after {toil_blows(d, c['kit'], s['str'])} exchanges hand to hand"]
    if c.get("leader"):
        bits.append(f"leading, morale {(s['pres'] - 50) // per['presence']['per']:+d}")
    return ", ".join(bits)


def _woman_note(tables: dict, c: dict) -> str:
    """' (a woman)', or ' (a woman, enlisted as a man)' where women enlisted disguised."""
    disguised = (_by_id(tables["regions"], c["region"]).get("women") or {}).get("disguised")
    return " (a woman, enlisted as a man)" if disguised else " (a woman)"


def sheet(d: Data, c: dict) -> list[str]:
    """A character as lines of text."""
    T = era(d, c["era"])
    career = _by_id(T["careers"], c["career"])
    names = {s["id"]: s["name"] for s in T["skills"]}
    stats = ", ".join(f"{x['name'][:3]} {c['stats'][x['id']]}" for x in T["characteristics"])
    trained = ", ".join(f"{names[k]} {c['skills'][k]}" for k in names if c["gains"].get(k, 0) > 0)
    sx = c.get("sex", "m")
    woman = _woman_note(T, c) if sx == "f" else ""
    lines = [f"{c['name']}{' (leader)' if c.get('leader') else ''}{woman}: {career['name'].lower()}, {c['terms']} term{'s' if c['terms'] > 1 else ''}, age {c['age']}",
             f"  {stats}",
             f"  Origin: {c['origin'].lower()}. {pron(c['trait'], sx)}; {pron(c['drawback'], sx).lower()}.",
             f"  Skills: {trained}",
             f"  Arms: {d.weapons[c['weapon']]['name']} (attack {c['attack']}%), defence {c['defence']}%; {d.armor['kits'][c['kit']]['name']}"]
    lines.append("  In a fight: " + fight_line(d, c))
    lines += [f"  Term {i + 1}: {pron(e, sx)}" for i, e in enumerate(c["events"])]
    for w in c["old"]:
        hurt = f", {T['lasting']} off {_by_id(T['characteristics'], w['stat'])['name']}" if w["kind"] == "lasting" else ""
        lines.append(f"  Old wound: {d.loc[w['loc']]['name'].lower()}, from {_a(d.weapons[w['weapon']]['short'].lower())}: {'a lasting hurt' if w['kind'] == 'lasting' else 'a healed scar'}{hurt}")
    return lines
