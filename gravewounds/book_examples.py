"""The period books' worked examples (templates/books/<book>/example.md): a team made with seeded
dice in each book's own era, and a fight worked through with the game's rules and chosen dice
(each die is given in the text). The Vietnam squad is rulebook_later.example; the medieval
retinue runs through the Rules. Values: bx (the Black-Powder Wars), wx (the World Wars), mx (the
Late Wars)."""
from __future__ import annotations

from . import combat as C
from .engine import armor_at, armor_steps, compose_wound, cover_digit, meets_layer, reduce_severity
from . import rulebook_later as LATER
from .model import Data

LETHAL = {"none": "would not kill him by itself", "days": "would kill him in days", "hours": "would kill him in hours",
          "minutes": "would kill him in minutes", "rounds": "would kill him in a few rounds", "instant": "kills him outright"}
STATES = {"defend_only": "only defend", "stunned": "do nothing, stunned,", "out": "take no more part in the fight"}


def values(d: Data) -> dict:
    return {"bx": black_powder(d), "wx": world_wars(d), "mx": late_wars(d)}


# ---------- shared ----------

def _team(d: Data, era: str, region: str, template: str, careers: tuple) -> tuple[dict, list]:
    """The first seeded team that has every named career and whose named men's first names
    and surnames all differ: (its template's entry, [leader, then one man per career])."""
    from .team import make_team
    from .units import SeededDice
    for seed in range(3, 300):
        team = make_team(d, era, region, template, "roll", SeededDice(seed))
        men = [team[0]] + [next((c for c in team[1:] if c["career"] == k), None) for k in careers]
        if None in men:
            continue
        if all(len({m["name"].split()[i] for m in men}) == len(men) for i in (0, -1)):
            T = next(t for t in d.teams[era]["templates"] if t["id"] == template)
            if max(c["skills"].get("leechcraft", 0) for c in team) > men[-1]["skills"].get("leechcraft", 0):
                continue                              # the text has the last named man treat, as the best Leechcraft on the side
            return T, men
    raise ValueError(f"book example: no seeded {era} {template} has {careers} with different names")


def _place(d: Data, loc: str) -> str:
    """'Thigh (left)' -> 'left thigh'; 'Chest (left)' -> 'chest, on the left'."""
    name = d.loc[loc]["name"].lower()
    for side in ("left", "right"):
        if name.endswith(f" ({side})"):
            base = name[: -len(side) - 3]
            return f"{base}, on the {side}" if base in ("skull", "chest") else f"{side} {base}"
    return name


def _material(d: Data, mid: str) -> str:
    """'Steel helmet (M1, Brodie)' -> 'steel helmet'; 'Soft Kevlar (...)' -> 'soft Kevlar'."""
    name = d.armor["materials"][mid]["name"].split(" (")[0]
    return name[:1].lower() + name[1:]


def _steps(n: int) -> str:
    return "nothing" if not n else f"{n} step{'s' if n > 1 else ''}"


def _man(c: dict, key: str) -> dict:
    return {key: c["name"], f"{key}_first": c["name"].split()[0], f"{key}_terms": c["terms"], f"{key}_age": c["age"],
            f"{key}_att": c["attack"], f"{key}_def": c["defence"], f"{key}_nerve": c["nerve"]}


def _career(d: Data, era: str, cid: str) -> str:
    return next(x["name"] for x in d.teams[era]["careers"] if x["id"] == cid)


def _hit(d: Data, p: str, attack: int, roll: int, droll: int, defence: int, wid: str, loc: str, mech: str,
         kit: str | None, man: dict, sroll: int) -> dict:
    """One blow worked through: the attack, the defence, the armour, the wound, the stop check
    and the Blood, as keys `p`_... for the text."""
    hit = C.attack_roll(d, attack, roll)
    if not hit["hit"] or C.defence_roll(defence, droll)["defended"]:
        raise ValueError(f"book example {p}: the blow must hit and not be defended ({attack}/{roll}, {defence}/{droll})")
    zone = d.loc[loc]["zone"]
    sev = C.margin_severity(d, hit["margin"], hit["critical"], wid, zone)
    if C.is_graze(d, hit["margin"], hit["critical"]):
        raise ValueError(f"book example {p}: the blow only grazes")
    layers = armor_at(d, kit, loc)
    digit = cover_digit(roll, None)[0]
    layer = meets_layer(layers, digit) if layers else None
    steps = armor_steps(d, layer[0], mech, wid) if layer else 0
    after = reduce_severity(sev, steps)
    out = {"attack": attack, "roll": roll, "margin": hit["margin"], "sev": sev, "droll": droll, "def": defence,
           "loc": _place(d, loc), "digit": digit, "steps": steps, "after": after,
           "armour": _material(d, layer[0]) if layer else "nothing", "steps_text": _steps(steps)}
    band = d.wounds["combat"]["margin_bands"]
    b = next(x for x in band["ballistic"] if zone in x["zones"]) if d.weapons[wid].get("threat") else band["default"]
    out["band"] = b["serious"]
    if after != "stopped":
        fx = compose_wound(d, loc, mech, after)
        blood = C.blood_pool(d, man["stats"]["end"])
        per = d.wounds["tracking"]["bleed_per_round"][fx["bleed"]]
        st = C.stop_check(d, man["nerve"], after, fx["pain"], sroll, 1.0, bool(fx.get("shock")))
        out.update(bleed=fx["bleed"], pain=fx["pain"], lethal=LETHAL[fx["lethal"]],
                   fracture="It breaks the bone. " if fx.get("fracture") else "", impair=" and ".join(fx["impair"]) or "nothing", blood=blood, per=f"{per:g}",
                   rounds=int(blood // per) if per else 0, shock=bool(st), nerve=man["nerve"], sroll=sroll)
        if st:
            out.update(target=st["target"], passed=st["passed"],
                       result=("passes: he fights on" if st["passed"] else
                               f"fails by {st['fail_by']}: he can {STATES[st['state']]}"
                               + (f" for {st['rounds']} rounds" if st.get("rounds") else "")))
    return {f"{p}_{k}": v for k, v in out.items()}


def _expect(book: str, v: dict, **want) -> None:
    """The text tells these outcomes; fail the build if the rules or data now give others."""
    bad = {k: v.get(k) for k, x in want.items() if v.get(k) != x}
    if bad:
        raise ValueError(f"book example, {book}: the text expects {want}, the rules now give {bad}")


def _bind(d: Data, p: str, loc: str, mech: str, sev: str, how: str, skill: int, roll: int) -> dict:
    fx = compose_wound(d, loc, mech, sev)
    r = C.first_aid(d, how, fx, d.loc[loc]["zone"] in ("arms", "legs"), skill, roll)
    return {f"{p}_roll": roll, f"{p}_skill": skill, f"{p}_done": r["done"], f"{p}_from": fx["bleed"], f"{p}_after": r["bleed"],
            f"{p}_steps": d.wounds["combat"]["first_aid"]["bind"]}


# ---------- the Black-Powder Wars: a British company at Albuera, 1811 ----------

def black_powder(d: Data) -> dict:
    T, (lead, sgt, line, surgeon) = _team(d, "horse_musket", "british_pen", "company", ("sergeant", "line", "surgeon"))
    WX, Q = d.weather, d.units["quality"]
    mf = WX["battle"]["misfire"][d.weapons["musket_smoothbore"]["ignition"]]
    storm = WX["conditions"]["storm"]
    v = {**_man(lead, "lead"), **_man(sgt, "sgt"), **_man(line, "line"), **_man(surgeon, "sur"),
         "lead_cmd": lead["skills"]["command"], "line_bayonet": line["skills"]["bayonet"],
         "sur_skill": surgeon["skills"]["leechcraft"], "sur_career": _career(d, "horse_musket", "surgeon").lower(),
         "followers": sum(n for _, n in T["followers"]), "team": T["name"].lower(),
         "mf_rain": mf[1], "mf_storm": mf[2], "storm_sight": LATER._sight(d, storm["visibility"]),
         "lance_reach": d.weapons["lance"]["reach"], "bayonet_reach": d.weapons["bayonet"]["reach"], "kit": d.armor["kits"][line["kit"]]["name"].lower()}
    # The lancer's thrust at the sergeant, from behind as the line breaks.
    v.update(_hit(d, "l", Q["veteran"]["attack"], 14, 47, sgt["defence"], "lance", "back_upper", "pierce", sgt["kit"], sgt, 31))
    # A French musket ball in the line man's thigh, at the volley before the storm.
    v.update(_hit(d, "b", Q["regular"]["attack"], 12, 71, line["defence"], "musket_smoothbore", "thigh_l", "ballistic", line["kit"], line, 40))
    v.update(_bind(d, "m", "thigh_l", "ballistic", v["b_after"], "bind", surgeon["skills"]["leechcraft"], 11))
    _expect("the Black-Powder Wars", v, l_shock=False, b_shock=True, m_done=True)
    return v


# ---------- the World Wars: a Newfoundland section at Beaumont-Hamel, 1916 ----------

def world_wars(d: Data) -> dict:
    T, (lead, rif, bomber, sb) = _team(d, "wwi", "newfoundland", "section", ("rifleman", "bomber", "stretcher_bearer"))
    U, Q = d.units, d.units["quality"]
    MG = U["machine_guns"]
    v = {**_man(lead, "lead"), **_man(rif, "rif"), **_man(bomber, "bomb"), **_man(sb, "sb"),
         "lead_cmd": lead["skills"]["command"], "sb_skill": sb["skills"]["leechcraft"],
         "sb_career": _career(d, "wwi", "stretcher_bearer").lower(), "followers": sum(n for _, n in T["followers"]),
         "team": T["name"].lower(), "kit": d.armor["kits"][rif["kit"]]["name"].split(" (")[0].lower(),
         "x_mg": U["missile"]["rate"]["machine_gun"], "x_aimed": round(1 / MG["tempo"]),
         "x_ext": U["formations"]["extended"]["per_hex"], "x_move": U["formations"]["extended"]["move"],
         "i_attack": U["indirect"]["attack"], "x_prone": U["suppression"]["prone"]}
    # A machine-gun round into the rifleman's thigh as he crosses the open.
    v.update(_hit(d, "g", Q["veteran"]["attack"], 9, 66, rif["defence"], "machine_gun", "thigh_r", "ballistic", rif["kit"], rif, 45))
    # A shell fragment on the bomber's helmet (and what it would have done to his face).
    v.update(_hit(d, "s", U["indirect"]["attack"], 31, 88, bomber["defence"], "mortar_artillery", "skull_l", "ballistic", bomber["kit"], bomber, 20))
    v["s_crit"] = next(b["critical"] for b in d.wounds["combat"]["margin_bands"]["ballistic"] if "head" in b["zones"])
    raw = C.margin_severity(d, U["indirect"]["attack"] - 31, False, "mortar_artillery", "head")
    v["s_rifle"] = _steps(armor_steps(d, "steel_helmet", "ballistic", "rifle_service"))
    v["s_raw"] = raw
    v.update(_bind(d, "m", "thigh_r", "ballistic", v["g_after"], "bind", sb["skills"]["leechcraft"], 23))
    _expect("the World Wars", v, g_shock=True, s_shock=True, s_sev="critical", s_after="serious", m_done=True)
    return v


# ---------- the Late Wars: a US section at Combat Outpost Keating, 2009 ----------

def late_wars(d: Data) -> dict:
    T, (lead, mg, gren, medic) = _team(d, "modern", "us_2005", "section", ("machine_gunner", "grenadier", "medic"))
    U, Q = d.units, d.units["quality"]
    I = U["indirect"]
    GS, G = I["kinds"]["gunship"], I["air"]["ground_fire"]
    kit = mg["kit"]
    layers = armor_at(d, kit, "chest_l")
    v = {**_man(lead, "lead"), **_man(mg, "mg"), **_man(gren, "gren"), **_man(medic, "med"),
         "lead_cmd": lead["skills"]["command"], "med_skill": medic["skills"]["leechcraft"],
         "followers": sum(n for _, n in T["followers"]), "team": T["name"].lower(), "kit": d.armor["kits"][kit]["name"].split(" (")[0],
         "plate_cover": layers[0][2] // 10, "x_seen": U["hidden"]["seen"], "x_mg_seen": U["hidden"]["mg_seen"],
         "a_gs_rate": GS["rate"], "a_gs_rounds": GS["rounds"], "a_mg": f"{G['mg']:g}", "a_exposed": GS["exposed"],
         "a_danger": f"{I['air']['fac']['danger']} hexes ({I['air']['fac']['danger'] * 2} m)",
         "ev_heli": U["aftermath"]["medevac"]["kinds"]["helicopter"]["hours"]}
    # A PKM round at the gunner's chest: the 3 of the roll meets the plate.
    v.update(_hit(d, "p", Q["regular"]["attack"], 23, 52, mg["defence"], "machine_gun", "chest_l", "ballistic", kit, mg, 50))
    # The same round read at a 7 would have met the soft vest beside the plate.
    soft = meets_layer(layers, 7)
    v["p_soft"] = _material(d, soft[0])
    n = armor_steps(d, soft[0], "ballistic", "machine_gun")
    v["p_soft_steps"] = _steps(n)
    v["p_soft_after"] = reduce_severity(v["p_sev"], n)
    # An RPG's fragment into the grenadier's leg, below the vest.
    v.update(_hit(d, "r", Q["regular"]["attack"], 8, 74, gren["defence"], "rpg", "thigh_l", "ballistic", gren["kit"], gren, 61))
    v.update(_bind(d, "t", "thigh_l", "ballistic", v["r_after"], "tourniquet", medic["skills"]["leechcraft"], 19))
    _expect("the Late Wars", v, p_after="stopped", r_shock=True, t_done=True, t_after=0)
    if v["p_soft_after"] == "stopped":
        raise ValueError("book example, the Late Wars: the text has the soft vest fail to stop the round")
    return v
