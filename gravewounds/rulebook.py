"""The rule book (dist/rules.html). The chapters are in templates/rules/*.md, in our own
words. Every number in them is a placeholder filled from the data when the book is built:
{{name}} for a value (values()), {{table:name}} for a table (tables()), and {{ex.name}} for
the running example, which is worked out here with the game's own rules (example()). So the
book says what the pages do, and a change to the data changes the book. A placeholder with
no value stops the build."""
from __future__ import annotations

import re
from pathlib import Path

from . import combat as C
from .engine import armor_at, armor_steps, compose_wound, reduce_severity
from .model import Data

PLACE = re.compile(r"\{\{\s*([a-z_:.0-9]+)\s*\}\}")


def _pct(x: float) -> str:
    return f"{round(x * 100)}%"


def values(d: Data) -> dict:
    """The rule numbers the chapters quote, by name."""
    W, T, CB, U = d.wounds, d.wounds["tracking"], d.wounds["combat"], d.units
    SC, MV, CH, MO = CB["stop_check"], CB["move"], CB["characteristics"], CB["morale"]
    E, DZ, RC = d.teams["medieval"], d.disease, d.disease["recovery"]
    res = SC["results"]
    v = {
        "pain_step": CB["pain_step"], "pain_cap": T["pain_cap"], "pain_cap_pct": T["pain_cap"] * CB["pain_step"],
        "cap": CB["cap"], "crit_tenth": round(1 / CB["critical_fraction"]), "graze": CB["graze_margin"],
        "band_serious": CB["margin_bands"]["default"]["serious"], "band_critical": CB["margin_bands"]["default"]["critical"],
        "crit_stop": SC["critical_penalty"], "fail1": res[0]["upto"], "fail2": res[1]["upto"], "rounds1": res[0]["rounds"],
        "stunned_def": CB["states"]["stunned"]["defence"],
        "blood_pool": T["blood_pool"], "blood_per": CH["blood"]["per"],
        "blood_lo": T["blood_pool"] + (15 - 50) // CH["blood"]["per"], "blood_hi": T["blood_pool"] + (95 - 50) // CH["blood"]["per"],
        "init_die": CH["initiative"]["die"], "init_per": CH["initiative"]["agi_per"],
        "advance": MV["advance"], "run": MV["run"], "crawl": MV["crawl"], "hex_yd": round(MV["hex_m"] * 1.0936), "hex_m": MV["hex_m"],
        "morale_trigger": _pct(MO["trigger"]), "morale_heavy": _pct(MO["heavy"]), "leader_present": MO["leader_present"],
        "leader_down": MO["leader_down"], "heavy_losses": MO["heavy_losses"], "presence_per": CH["presence"]["per"],
        "bind_skilled": CB["first_aid"]["bind"],
        "toil_light": CH["toil"]["blows"]["light"], "toil_medium": CH["toil"]["blows"]["medium"], "toil_heavy": CH["toil"]["blows"]["heavy"],
        "stat_lo": E["stat_range"][0], "stat_hi": E["stat_range"][1], "array": ", ".join(map(str, E["array"])),
        "origin_gain": E["gain"], "first_term": E["first_term"], "term_main": E["term_main"], "term_second": E["term_second"],
        "event_gain": E["gain"], "age_start": E["age"]["start"], "age_term": E["age"]["per_term"], "skill_max": E["skill_max"],
        "scar_upto": E["old_wound"][0]["to"], "lasting": E["lasting"], "origins": len(E["origins"]), "careers": len(E["careers"]),
        "eras": len(d.teams),
        "big": RC["big"], "care_none": RC["care"]["none"], "care_shelter": RC["care"]["shelter"],
        "marched": RC["activity"]["marched"], "rest": RC["activity"]["rest"], "wet_cold": RC["wet_cold"], "filth": RC["filth"],
        "wound_every": DZ["wounds"]["wound"]["every"], "wound_easier": -DZ["wounds"]["wound"]["virulence"],
        "fever_lo": DZ["wounds"]["fever_after"][0], "fever_hi": DZ["wounds"]["fever_after"][1],
        "fever_low": DZ["wounds"]["fever_chance"]["low"], "fever_medium": DZ["wounds"]["fever_chance"]["medium"],
        "fever_high": DZ["wounds"]["fever_chance"]["high"], "fever_nocamp": DZ["wounds"]["fever_care"]["none"],
        "fever_quarters": -DZ["wounds"]["fever_care"]["shelter"], "fever_harder": DZ["wounds"]["fever"]["virulence"],
        "blood_night": DZ["named_blood_per_day"], "leech_per": 10,
        "stop_sev": " and ".join(SC["severities"]),
    }
    v["ex"] = example(d)
    return v


def tables(d: Data) -> dict:
    """Generated tables, as Markdown, by name."""
    T, CB, U, V = d.wounds["tracking"], d.wounds["combat"], d.units, d.wounds["vocabulary"]
    res, out = CB["stop_check"]["results"], {}
    out["qualities"] = _md(["Quality", "Attack", "Defence", "Nerve"],
                           [[q.capitalize(), f"{x['attack']}%", f"{x['defence']}%", x["nerve"]] for q, x in U["quality"].items()])
    lo, rows = 0, []
    for r in res:
        span = f"{lo + 1}–{r['upto']}" if "upto" in r else f"more than {lo}"
        st = CB["states"][r["state"]]
        rounds = f"for {r['rounds']} rounds" if r.get("rounds") else "until helped or the fight ends"
        rows.append([f"Failed by {span}", f"**{st['name']}** {rounds}", _state_text(st)])
        lo = r.get("upto", lo)
    out["stop"] = _md(["Result", "He is", "Which means"], [["Equal or under", "Fighting on", "No change"]] + rows)
    out["blood"] = _md(["Blood left", "Effect"], [[f"{_pct(t['at'])} or less" if t["at"] else "None", t["effect"]]
                                                 for t in sorted(T["thresholds"], key=lambda t: -t["at"])])
    out["bleed"] = _md(["Bleed", "Blood lost", "What it is"],
                       [[f"B{k}", _per_round(v), V["bleed"][k].replace(" - ", ": ") if k in V["bleed"] else ""]
                        for k, v in sorted(((int(k), v) for k, v in T["bleed_per_round"].items()))])
    out["impair"] = _md(["Impairment", "What it does", "Attack", "Defence"], _impair_rows(d))
    out["track"] = _md(["Step", "In a fight"], _track_rows(d))
    R = d.disease["recovery"]
    out["recovery"] = _md(["What", "To the roll"], [
        ["Care: no camp", f"{R['care']['none']:+d}"], ["Care: a camp", f"{R['care']['field']:+d}"], ["Care: quarters in houses", f"{R['care']['shelter']:+d}"],
        ["He marched that day", f"{R['activity']['marched']:+d}"], ["He rested", f"{R['activity']['rest']:+d}"],
        ["A night harder than the shelter (cold, wet)", f"{R['wet_cold']:+d}"], ["Poor hygiene", f"{R['filth']:+d}"],
        ["A leech with the force", "+ his Leechcraft ÷ 10"],
        ["Battle wounds heal easily", f"+{-d.disease['wounds']['wound']['virulence']}"],
        ["Wound fever is hard", f"−{d.disease['wounds']['fever']['virulence']}"]])
    E = d.teams["medieval"]
    names = {s["id"]: s["name"] for s in E["skills"]}
    out["careers"] = _md(["Career", "Main skill", "Second skill"], [[c["name"], names[c["main"]], names[c["second"]]] for c in E["careers"]])
    out["fq"] = _md(["Quality table", *[q.capitalize() for q in U["quality"]]],
                    [[k.capitalize(), *_ranges(rows)] for k, rows in E["followers"]["quality"].items()])
    return out


def _state_text(st: dict) -> str:
    if st.get("out"):
        return "Takes no part: no attack, no defence"
    if st.get("defence"):
        return f"No attack; −{st['defence']}% to his defence"
    return "No attack; he may move and defend"


def _per_round(v: float) -> str:
    if not v:
        return "none"
    if v < 1:
        return f"{round(v * 10)} a minute"
    return f"{v:g} a round"


def _impair_rows(d: Data) -> list:
    V, rows = d.wounds["vocabulary"]["impair"], []
    for k, r in d.wounds["combat"]["impair"].items():
        if "weapon_arm" in r or "shield_arm" in r:
            for arm in ("weapon_arm", "shield_arm"):
                e = r.get(arm, {})
                rows.append([f"{k.replace('_', ' ').capitalize()} ({arm.replace('_', ' ')})", V.get(k, ""), _neg(e.get("attack")), _neg(e.get("defence"))])
        else:
            rows.append([k.replace("_", " ").capitalize(), V.get(k, ""), _neg(r.get("attack")), _neg(r.get("defence"))])
    return rows


def _neg(x) -> str:
    return f"−{x}%" if x else "—"


def _track_rows(d: Data) -> list:
    F, rows = d.disease["in_fight"], []
    for s in d.disease["steps"]:
        r = F.get(s, {})
        bits = ([f"−{r['penalty']}% to attack and defence"] if r.get("penalty") else []) + (["cannot run"] if r.get("no_run") else []) \
            + (["crawls only"] if r.get("crawl") else []) + (["defends only"] if r.get("defend_only") else []) + (["too ill to fight"] if r.get("out") else [])
        rows.append([s.capitalize(), ", ".join(bits) or "—"])
    return rows


def _ranges(rows: list) -> list:
    out, lo = [], 1
    for r in rows:
        out.append(f"{lo:02d}–{r['to'] % 100:02d}")
        lo = r["to"] + 1
    return out


def _md(head: list, rows: list) -> str:
    return "\n".join(["| " + " | ".join(map(str, head)) + " |", "|" + "---|" * len(head)]
                     + ["| " + " | ".join(map(str, r)) + " |" for r in rows])


# ---------- the running example ----------

def example(d: Data) -> dict:
    """The retinue on the Towton road: a team made with seeded dice, and one fight worked
    through with the game's own rules and chosen dice (each die is given in the text)."""
    from .team import make_team
    from .units import SeededDice
    team = make_team(d, "medieval", "england", "retinue", "roll", SeededDice(3))
    lead, arch = team[0], next(c for c in team if c["career"] == "archer")
    leech = max(team, key=lambda c: c["skills"].get("leechcraft", 0))
    names = {s["id"]: s["name"] for s in d.teams["medieval"]["skills"]}
    ex = {"lead": lead["name"], "arch": arch["name"], "arch_first": arch["name"].split()[0], "leech": leech["name"],
          "leech_skill": leech["skills"]["leechcraft"], "leech_career": _career(d, leech)}
    s, base = arch["stats"], arch["base"]
    ex.update({f"a_{k}": v for k, v in s.items()}, a_bow=arch["attack"], a_def=arch["defence"], a_terms=arch["terms"], a_age=arch["age"],
              a_origin=arch["origin"].lower(), a_trait=arch["trait"].lower(), a_drawback=arch["drawback"].lower(),
              a_blood=d.wounds["tracking"]["blood_pool"] + (s["end"] - 50) // d.wounds["combat"]["characteristics"]["blood"]["per"],
              a_init=s["agi"] // d.wounds["combat"]["characteristics"]["initiative"]["agi_per"],
              a_events=" and ".join(e.rstrip(".").lower() for e in arch["events"]),
              a_skills=", ".join(f"{names[k]} {arch['skills'][k]}" for k in ("bow", "dodge", "fieldcraft", "stealth")))
    ex.update(_shot(d, arch), **_cut(d, arch), **_camp(d, arch, leech))
    return ex


def _career(d: Data, c: dict) -> str:
    return next(x["name"] for x in d.teams["medieval"]["careers"] if x["id"] == c["career"]).lower()


def _severity(d: Data, margin: int, critical: bool = False) -> str:
    b = d.wounds["combat"]["margin_bands"]["default"]
    if critical or margin >= b["critical"]:
        return "critical"
    return "serious" if margin >= b["serious"] else "light"


def _shot(d: Data, arch: dict) -> dict:
    """His arrow at a Lancastrian billman: a hit, the jack, the stop check."""
    q, roll, droll = d.units["quality"]["regular"], 21, 61
    margin = arch["attack"] - roll
    sev = _severity(d, margin)
    loc, mech, kit = "chest_l", "pierce", "jack_sallet"
    layers = armor_at(d, kit, loc)
    steps = sum(armor_steps(d, m, mech, arch["weapon"]) for m, _, _ in layers)
    raw = sum(armor_steps(d, m, mech, None) for m, _, _ in layers)
    sev2 = reduce_severity(sev, steps)
    fx = compose_wound(d, loc, mech, sev2)
    SC, sroll = d.wounds["combat"]["stop_check"], 47
    st = C.stop_check(d, q["nerve"], sev2, fx["pain"], sroll, 1.0, bool(fx.get("shock")))
    target = st["target"]
    return {"s_roll": roll, "s_margin": margin, "s_sev": sev, "s_def": q["defence"], "s_droll": droll, "s_loc": d.loc[loc]["name"].lower(),
            "s_raw": raw, "s_steps": steps, "s_after": sev2, "s_bleed": fx["bleed"], "s_pain": fx["pain"],
            "s_impair": ", ".join(fx["impair"]) or "none", "s_lethal": fx["lethal"], "s_nerve": q["nerve"], "s_target": target,
            "s_sroll": sroll, "s_by": st["fail_by"], "s_state": d.wounds["combat"]["states"][st["state"]]["name"].lower(),
            "s_rounds": next(r["rounds"] for r in SC["results"] if r["state"] == st["state"]),
            "s_attack": q["attack"]}


def _cut(d: Data, arch: dict) -> dict:
    """A billman's blow on him: the thigh opened, the tourniquet, what it costs him."""
    q, roll, droll = d.units["quality"]["regular"], 22, 58
    margin = q["attack"] - roll
    sev = _severity(d, margin)
    loc, mech = "thigh_r", "cut"
    fx = compose_wound(d, loc, mech, reduce_severity(sev, 0))
    T = d.wounds["tracking"]
    blood = d.wounds["tracking"]["blood_pool"] + (arch["stats"]["end"] - 50) // d.wounds["combat"]["characteristics"]["blood"]["per"]
    per = T["bleed_per_round"][fx["bleed"]]
    left = blood - 2 * per
    p = C.penalties(d, [{"loc": loc, "fx": fx}], left / blood, "R")
    th = next(t for t in sorted(T["thresholds"], key=lambda t: t["at"]) if left / blood <= t["at"]) if left / blood <= max(t["at"] for t in T["thresholds"]) else None
    MV = d.wounds["combat"]["move"]
    return {"c_attack": q["attack"], "c_roll": roll, "c_margin": margin, "c_sev": sev, "c_droll": droll, "c_loc": d.loc[loc]["name"].lower(),
            "c_bleed": fx["bleed"], "c_pain": fx["pain"], "c_impair": ", ".join(fx["impair"]) or "none", "c_lethal": fx["lethal"],
            "c_shock": "does not" if not fx.get("shock") else "does", "c_per": f"{per:g}", "c_rounds_dead": int(blood // per),
            "c_left": f"{left:g}", "c_blood": blood, "c_th": th["effect"].split(":")[0].lower() if th else "steady",
            "c_patt": p["attack"], "c_pdef": p["defence"], "c_adv": MV["advance"] // 2, "c_run": MV["run"] // 2,
            "c_infection": fx["infection"]}


def _camp(d: Data, arch: dict, leech: dict) -> dict:
    """Carried to camp: the wound on the track and its weekly checks."""
    DZ, R = d.disease, d.disease["recovery"]
    end, bonus = arch["stats"]["end"], leech["skills"]["leechcraft"] // 10
    target = end + R["care"]["field"] + R["activity"]["rest"] + bonus - DZ["wounds"]["wound"]["virulence"]
    r1, r2 = 52, 30
    fever = DZ["wounds"]["fever_chance"]["medium"] + DZ["wounds"]["fever_care"]["field"] - bonus
    blood = d.wounds["tracking"]["blood_pool"] + (end - 50) // d.wounds["combat"]["characteristics"]["blood"]["per"]
    return {"k_end": end, "k_bonus": bonus, "k_target": target, "k_r1": r1, "k_m1": target - r1, "k_r2": r2, "k_m2": target - r2,
            "k_start": DZ["wounds"]["start"]["serious"], "k_fever": fever, "k_froll": 64, "k_blood": blood}


# ---------- building the page ----------

def _fill(text: str, vals: dict, tabs: dict, where: str) -> str:
    def one(m):
        key = m.group(1)
        if key.startswith("table:"):
            if key[6:] not in tabs:
                raise ValueError(f"{where}: no table {key[6:]}")
            return tabs[key[6:]]
        node = vals
        for part in key.split("."):
            if not isinstance(node, dict) or part not in node:
                raise ValueError(f"{where}: no value for {{{{{key}}}}}")
            node = node[part]
        return str(node)
    return PLACE.sub(one, text)


def render(d: Data, root: Path) -> str:
    """dist/rules.html: the chapters filled and joined into the page template."""
    import markdown
    vals, tabs = values(d), tables(d)
    src = root / "templates" / "rules"
    body = "\n\n".join(_fill(p.read_text(encoding="utf-8"), vals, tabs, p.name) for p in sorted(src.glob("*.md")))
    md = markdown.Markdown(extensions=["tables", "admonition", "toc", "attr_list"], extension_configs={"toc": {"toc_depth": "1-2"}})
    html = md.convert(body)
    page = (root / "templates" / "rules.html").read_text(encoding="utf-8")
    return page.replace("{{TOC}}", md.toc).replace("{{BODY}}", html)
