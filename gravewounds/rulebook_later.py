"""The rule book's third part (templates/rules/09-13): the other eras, modern fire and the guns,
vehicles, night and the air, and a worked example from a later war. Values and tables are
filled from the data, as in rulebook.py; the running example of that war is worked out here
with the game's own rules and chosen dice (each die is given in the text)."""
from __future__ import annotations

from . import combat as C
from .engine import armor_at, armor_steps, compose_wound, reduce_severity
from .model import Data


def _yd(m: float) -> str:
    """'219 yards (200 m)' from metres; '2.2 miles (3.6 km)' from 2 km on."""
    if m >= 2000:
        return f"{m / 1609.344:.1f} miles ({m / 1000:g} km)"
    return f"{round(m * 1.0936):,} yards ({m:,g} m)"


def _field(d: Data, hexes: int) -> str:
    """Field-map hexes as yards and metres."""
    return _yd(hexes * d.units["hex_m"])


def _sight(d: Data, hexes) -> str:
    """Battle-map sight hexes (range_scale to a field hex) in yards and metres."""
    return "no limit" if hexes is None else _yd(hexes * d.units["hex_m"] / d.units["range_scale"])


def _md(head: list, rows: list) -> str:
    return "\n".join(["| " + " | ".join(map(str, head)) + " |", "|" + "---|" * len(head)]
                     + ["| " + " | ".join(map(str, r)) + " |" for r in rows])


def _signed(x: int) -> str:
    """+12%, −3%."""
    return f"+{x}%" if x >= 0 else f"−{-x}%"


def _hexes(n: int) -> str:
    return f"{n} hex" if n == 1 else f"{n} hexes"


def _pcts(xs) -> str:
    return ", ".join(f"{x:g}" for x in xs)


# ---------- values ----------

def values(d: Data) -> dict:
    """The numbers chapters 9-13 quote, by name."""
    v = {}
    for part in (_era_values, _fire_values, _gun_values, _support_values, _vehicle_values, _night_values, _air_values):
        v.update(part(d))
    v["lx"] = example(d)
    return v


def _era_values(d: Data) -> dict:
    T = d.teams
    return {"e_ww_term": T["wwi"]["age"]["per_term"], "e_term": T["medieval"]["age"]["per_term"], "e_others": len(T) - 1}


def _fire_values(d: Data) -> dict:
    U = d.units
    MG, R = U["machine_guns"], U["missile"]["rate"]
    return {"x_bolt": R["rifle_service"], "x_assault": R["rifle_assault"], "x_smg": R["pistol_smg"], "x_mg": R["machine_gun"],
            "x_mg_crew": MG["crew"], "x_mg_aimed": round(1 / MG["tempo"]), "x_beaten": _field(d, MG["beaten"]["beyond"]),
            "x_beaten_share": MG["beaten"]["share"], "x_ground": U["to_ground"]["cover"], "x_seen": U["hidden"]["seen"],
            "x_mg_seen": U["hidden"]["mg_seen"], "x_dug_in": U["morale"]["mods"]["dug_in"], "x_sup_prone": U["suppression"]["prone"],
            "x_ext_move": U["formations"]["extended"]["move"], "x_ext_men": U["formations"]["extended"]["per_hex"]}


def _gun_values(d: Data) -> dict:
    A = d.units["artillery"]
    return {"g_crew": A["crew"], "g_per_hex": d.units["formations"]["battery"]["per_hex"], "g_range": _field(d, A["range"]),
            "g_canister": _field(d, A["canister_to"]), "g_rifled": _field(d, A["rifled"]["range"]), "g_ammo": A["ammo"],
            "g_attack": A["attack"], "g_balls": A["canister"]["balls"], "g_file": A["round_shot"]["file"],
            "g_ricochet": _field(d, A["ricochet"]["beyond"]), "g_pushed": A["pushed"]}


def _support_values(d: Data) -> dict:
    I, S = d.units["indirect"], d.units["assault"]
    K = I["kinds"]
    return {"i_attack": I["attack"], "i_prone": f"{I['prone']:g}", "i_tree": f"{I['tree_burst']['factor']:g}",
            "i_tree_prone": f"{I['tree_burst']['prone']:g}", "i_creep": I["creep"]["max"], "i_each": I["creep"]["every_max"],
            "i_cb_field": K["field"]["counter"], "i_cb_how": K["howitzer"]["counter"], "i_cb_among": I["counter_battery"]["among"],
            "i_cb_near": I["counter_battery"]["near"], "i_tank_knock": K["tank"]["knock"], "i_how_knock": K["howitzer"]["knock"],
            "b_pinned": S["pinned"], "b_flame_dead": S["flame_dead"]}


def _vehicle_values(d: Data) -> dict:
    V = d.units["vehicles"]
    A = V["anti_armour"]
    return {"v_flank": f"{V['aspect']['flank']:g}", "v_rear": f"{V['aspect']['rear']:g}", "v_rocket_per": round(1 / A["rpg"]["rate"]),
            "v_atgm_per": round(1 / A["atgm"]["rate"]), "v_turret": V["damage"]["turret"],
            "v_t_imm": V["damage"]["turret_hit"]["immobilised"], "v_t_gun": V["damage"]["turret_hit"]["gun"],
            "v_h_imm": V["damage"]["hull_hit"]["immobilised"], "v_h_gun": V["damage"]["hull_hit"]["gun"],
            **_at_mine_values(d),
            "v_crew_struck": V["crew_struck"], "v_riders_struck": V["riders_struck"], "v_shell_light": f"{V['armour']['light']['shell'] / V['armour']['heavy']['shell']:g}",
            "v_fb_knock": d.units["indirect"]["kinds"]["fighter_bomber"]["knock"]}


def _at_mine_values(d: Data) -> dict:
    """Anti-tank guns and minefields."""
    A, M, V = d.units["anti_tank_guns"], d.units["mines"], d.units["vehicles"]["armour"]
    g = A["gun"]
    return {"at_crew": A["crew"], "at_range": _field(d, g["range"]), "at_rate": g["rate"], "at_hit": "/".join(str(h[1]) for h in g["hit"]),
            "at_move": d.units["formations"]["at_gun"]["move"], "m_attack": M["attack"], "m_heavy": V["heavy"]["mine"], "m_light": V["light"]["mine"]}


def _night_values(d: Data) -> dict:
    L, Q = d.weather["light"], d.units["quality"]
    lost = {q: (60 - Q[q]["nerve"]) // 2 for q in Q}
    return {"n_flash_under": _sight(d, L["flash"]), "n_flash": _sight(d, L["flash"]), "n_flare": _field(d, L["flare"]),
            "n_lasts": L["lasts"], "n_fixed": L["fixed_line"]["aim"], "n_fixed_width": L["fixed_line"]["width"],
            "n_lost": ", ".join(f"{q} {_signed(lost[q])}" for q in Q), "n_dark": _sight(d, L["levels"]["night"]["sight"]),
            "n_moon": _sight(d, L["levels"]["moonlit"]["sight"])}


def _air_values(d: Data) -> dict:
    I, H, WX = d.units["indirect"], d.units["heliborne"], d.weather
    A, FB, GS = I["air"], I["kinds"]["fighter_bomber"], I["kinds"]["gunship"]
    G = A["ground_fire"]
    cond = WX["conditions"]
    return {"a_grounded": ", ".join(cond[c]["name"].lower() for c in A["grounded"]), "a_fb_delay": FB["delay"], "a_fb_rate": FB["rate"],
            "a_fb_sorties": FB["rounds"] // FB["rate"], "a_gs_rate": GS["rate"], "a_gs_rounds": GS["rounds"], "a_reach": _field(d, G["reach"]),
            "a_mg": f"{G['mg']:g}", "a_rocket": f"{G['rocket']:g}", "a_rifles": f"{G['rifles']:g}", "a_cap": G["cap"], "a_gs_exposed": GS["exposed"],
            "a_danger": _field(d, A["fac"]["danger"]), "h_lift": H["lift"], "h_blocked": H["blocked"], "h_hot": H["hot"], "h_zone": H["zone"]}


# ---------- tables ----------

def tables(d: Data) -> dict:
    """The tables chapters 9-13 show, as Markdown, by name."""
    return {"eras": _eras(d), "women": _women(d), "indirect": _indirect(d), "smoke": _smoke(d), "assault": _assault(d),
            "vehicles": _vehicles(d), "armour": _armour(d), "dark": _dark(d), "nvd": _nvd(d), "air": _air(d), "mines": _mines(d)}


def _mines(d: Data) -> str:
    rows = [[k["name"], f"{k['men']}%" if k["men"] else "—", f"{k['vehicles']}%" if k["vehicles"] else "—"] for k in d.units["mines"]["kinds"].values()]
    return _md(["Minefield", "Each man going into a hex struck", "Each vehicle going into a hex struck"], rows)


def _eras(d: Data) -> str:
    rows = []
    for E in sorted(d.teams.values(), key=_era_start):
        if E["id"] == "medieval":
            continue
        fight = ", ".join(s["name"] for s in E["skills"] if s.get("combat") and s["id"] not in COMMON)
        armies = ", ".join(r.get("short") or r["name"] for r in E["regions"])
        term = E["age"]["per_term"]
        rows.append([E["name"], armies, fight, len(E["careers"]), f"{term} year{'s' if term > 1 else ''}"])
    return _md(["Era", "Armies", "Fighting skills", "Careers", "A term"], rows)


COMMON = ("brawl", "parry", "dodge")


def _era_start(era: dict) -> int:
    """The first year in an era's name: 'Thirty Years' War (1618-1648)' -> 1618."""
    digits = era["name"].split("(")[-1][:4]
    return int(digits) if digits.isdigit() else 0


def _women(d: Data) -> str:
    rows = []
    for E in sorted(d.teams.values(), key=_era_start):
        careers = {c["id"]: c["name"].lower() for c in E["careers"]}
        for r in E["regions"]:
            W = r.get("women")
            if W:
                share = "chosen, never rolled" if W.get("share") is None else f"{W['share']:g}%"
                rows.append([f"{E['name'].split(' (')[0]}: {r.get('short') or r['name']}", share, ", ".join(careers[c] for c in W["careers"])])
    return _md(["Army", "Share", "Careers open to women"], rows)


def _indirect(d: Data) -> str:
    rows = []
    for k in d.units["indirect"]["kinds"].values():
        if k.get("air"):
            continue
        reach = _field(d, k["range"]) if k.get("range") else "in sight"
        lands = "next exchange" if k["delay"] else "this exchange"
        scatter = _hexes(k["scatter"]) if k["scatter"] else "none"
        rows.append([k["name"], reach, k["rate"], k["rounds"], lands, scatter, _pcts(k["struck"])])
    return _md(["Kind", "Reach", "Shells a minute a tube", "Rounds a tube", "Lands", "Scatter", "Struck % at 0, 1, 2 … hexes"], rows)


def _smoke(d: Data) -> str:
    S, names = d.units["indirect"]["smoke"], {w["id"]: w["name"] for w in d.weather["winds"]} if all("id" in w for w in d.weather["winds"]) else {}
    rows = [[names.get(w, w.capitalize()), S["lasts"][w] - 1 or "none: blown away", S["drift"][w] or "—"] for w in S["lasts"]]
    return _md(["Wind", "Exchanges it screens after landing", "Drifts (hexes an exchange)"], rows)


def _assault(d: Data) -> str:
    rows = [[m["name"], f"{m['knock']} or less", f"{m['struck']}%" + (", burned" if m.get("flame") else ", as grenade wounds")]
            for m in d.units["assault"]["means"].values()]
    return _md(["Means", "Knocks the bunker out on d100", "Men in its hex struck"], rows)


def _vehicles(d: Data) -> str:
    rows = []
    for k in d.units["vehicles"]["kinds"].values():
        g = k.get("gun")
        gun = f"{_field(d, g['range'])}, {g['rate']} a vehicle, hits {'/'.join(str(h[1]) for h in g['hit'])}%" if g else "machine guns only"
        rows.append([k["name"], k["crew"], k["move"], k["armour"], gun, k.get("carry") or "—"])
    return _md(["Vehicle", "Crew", "Move (hexes)", "Armour", "Main gun: reach, rounds, hits (close / mid / full)", "Carries"], rows)


def _armour(d: Data) -> str:
    A = d.units["vehicles"]["armour"]
    what = [("rpg", "A rocket (RPG, bazooka, recoilless rifle)"), ("atgm", "A guided missile"), ("gun", "A main gun")]
    return _md(["A hit from", "Heavy armour (tanks)", "Light armour"], [[t, f"{A['heavy'][k]}%", f"{A['light'][k]}%"] for k, t in what])


def _dark(d: Data) -> str:
    L = d.weather["light"]["levels"]
    return _md(["Light", "Movement", "Losing direction"],
               [[x["name"], f"+{x['move']} a hex" if x["move"] else "—", f"{x['lost']}%" if x["lost"] else "—"] for x in L.values()])


def _nvd(d: Data) -> str:
    rows = [[x["name"], _sight(d, x["sight"]), f"−{x['aim']}%" if x["aim"] else "as by day", "yes" if x.get("smoke") else "—"]
            for x in d.weather["light"]["night_vision"]["devices"].values()]
    return _md(["Device", "Sees to", "Aims at worst", "Through smoke"], rows)


def _air(d: Data) -> str:
    K = d.units["indirect"]["kinds"]
    rows = []
    for k in (K["fighter_bomber"], K["gunship"]):
        comes = f"{k['delay']} exchanges after the call" if k["delay"] else "at once"
        rows.append([k["name"], comes, f"{k['rate']} {k['shot'][1]}", k["rounds"], _hexes(k["scatter"]), _pcts(k["struck"]),
                     "yes" if k.get("by_night") else "no"])
    return _md(["Aircraft", "Comes", "An aircraft an exchange", "In all", "Scatter", "Struck % at 0, 1, 2 … hexes", "By night"], rows)


# ---------- the later war's example ----------

def example(d: Data) -> dict:
    """A US Army rifle squad in Vietnam, made with seeded dice, and a night's fight worked
    through with the game's own rules and chosen dice."""
    from .team import make_team
    from .units import SeededDice
    team = make_team(d, "vietnam", "us_army", "squad", "roll", SeededDice(3))
    lead = team[0]
    mg = next(c for c in team if c["career"] == "machine_gunner")
    gren = next(c for c in team if c["career"] == "grenadier")
    medic = next(c for c in team if c["career"] == "medic")
    E = d.teams["vietnam"]
    kit = d.armor["kits"][mg["kit"]]
    ex = {"lead": lead["name"], "lead_terms": lead["terms"], "lead_age": lead["age"], "lead_cmd": lead["skills"]["command"],
          "mg": mg["name"], "mg_first": mg["name"].split()[0], "mg_skill": mg["attack"], "mg_def": mg["defence"], "mg_terms": mg["terms"],
          "gren": gren["name"], "gren_first": gren["name"].split()[0], "medic": medic["name"], "medic_first": medic["name"].split()[0],
          "medic_skill": medic["skills"]["leechcraft"], "kit": kit["name"], "squad": next(t["name"] for t in E["templates"] if t["id"] == "squad").lower(),
          "followers": sum(n for _, n in next(t for t in E["templates"] if t["id"] == "squad")["followers"])}
    ex.update(_ak(d, mg), **_grenade(d, mg["kit"]), **_bind(d, medic))
    return ex


def _ak(d: Data, mg: dict) -> dict:
    """An AK round at the gunner: his right arm, the stop check, the gun he cannot fire."""
    q, roll, droll, sroll = d.units["quality"]["regular"], 15, 40, 22
    hit = C.attack_roll(d, q["attack"], roll)
    loc, wid = "upper_arm_r", "rifle_assault"
    sev = C.margin_severity(d, hit["margin"], hit["critical"], wid, d.loc[loc]["zone"])
    fx = compose_wound(d, loc, "ballistic", sev)
    st = C.stop_check(d, mg["nerve"], sev, fx["pain"], sroll, 1.0, bool(fx.get("shock")))
    blood = C.blood_pool(d, mg["stats"]["end"])
    per = d.wounds["tracking"]["bleed_per_round"][fx["bleed"]]
    return {"k_attack": q["attack"], "k_roll": roll, "k_margin": hit["margin"], "k_sev": sev, "k_droll": droll, "k_loc": d.loc[loc]["name"].lower(),
            "k_bleed": fx["bleed"], "k_pain": fx["pain"], "k_nerve": mg["nerve"], "k_target": st["target"], "k_sroll": sroll,
            "k_passed": "passes" if st["passed"] else "fails", "k_blood": blood, "k_per": f"{per:g}", "k_rounds": int(blood // per) if per else 0,
            "k_band": _band(d, "arms"), "k_weapon": d.weapons["machine_gun"]["name"].lower()}


def _band(d: Data, zone: str) -> int:
    return next(b["serious"] for b in d.wounds["combat"]["margin_bands"]["ballistic"] if zone in b["zones"])


def _grenade(d: Data, kit_id: str) -> dict:
    """A grenade's fragment into the grenadier's chest, and the vest that stops it."""
    q, roll = d.units["quality"]["regular"], 25
    hit = C.attack_roll(d, q["attack"], roll)
    loc, wid = "chest_l", "hand_grenade"
    sev = C.margin_severity(d, hit["margin"], hit["critical"], wid, d.loc[loc]["zone"])
    layers = armor_at(d, kit_id, loc)
    steps = sum(armor_steps(d, m, "ballistic", wid) for m, _, _ in layers)
    rifle = sum(armor_steps(d, m, "ballistic", "rifle_assault") for m, _, _ in layers)
    mat = d.armor["materials"][layers[0][0]]["name"] if layers else "none"
    return {"r_roll": roll, "r_margin": hit["margin"], "r_sev": sev, "r_band": _band(d, "torso"), "r_loc": d.loc[loc]["name"].lower(),
            "r_steps": steps, "r_after": reduce_severity(sev, steps), "r_rifle": f"{rifle} steps" if rifle else "nothing", "r_vest": mat[:1].lower() + mat[1:]}


def _bind(d: Data, medic: dict) -> dict:
    """The medic binds the gunner's arm."""
    fx = compose_wound(d, "upper_arm_r", "ballistic", "serious")
    roll = 12
    r = C.first_aid(d, "bind", fx, True, medic["skills"]["leechcraft"], roll)
    return {"m_roll": roll, "m_done": "binds it" if r["done"] else "fails", "m_steps": d.wounds["combat"]["first_aid"]["bind"],
            "m_after": r["bleed"], "m_impair": d.wounds["combat"]["impair"]["arm"]["weapon_arm"]["attack"]}
