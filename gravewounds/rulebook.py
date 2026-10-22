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
from . import rulebook_later as LATER
from .engine import armor_at, armor_steps, compose_wound, reduce_severity
from .model import Data

PLACE = re.compile(r"\{\{\s*([a-z_:.0-9]+)\s*\}\}")


def _band_rows(bands: list) -> list:
    """[[span, name]] for bands given by their `from`: '0', '1-25', ..., '76+'."""
    rows = []
    for k, b in enumerate(bands):
        if k + 1 == len(bands):
            span = f"{b['from']}+"
        elif bands[k + 1]["from"] - 1 == b["from"]:
            span = str(b["from"])
        else:
            span = f"{b['from']}-{bands[k + 1]['from'] - 1}"
        rows.append([span, b["name"]])
    return rows

def _pct(x: float) -> str:
    return f"{round(x * 100)}%"



def _money_vars(d) -> dict:
    """The money rules' figures (money.yaml), with the medieval Day and a three-term purse in
    English money as the worked example."""
    from .money import equipment, fmt
    M, E = d.money, equipment(d, "medieval")
    cur = E["currencies"].get(E["currency"].get("default")) if E["currencies"] else None
    per = M.get("purse_days_per_term", 0)
    W = M.get("work") or {"terms": {"week": 7, "month": 30}, "failure": 0.5, "fumble_from": 96}
    return {"purse_days": per, "earn_days": M.get("earn_days_per_day", 0), "purse_three": 3 * per,
            "w_week": W["terms"]["week"], "w_month": W["terms"]["month"], "w_fail": _pct(W["failure"]), "w_fumble": W["fumble_from"],
            "w_eras": len(d.jobs) - 1,
            "day_coin": fmt(cur, cur["day"]) if cur and cur.get("day") else "a day's pay",
            "purse_three_coin": fmt(cur, 3 * per * cur["day"]) if cur and cur.get("day") else "",
            **_keep_vars(d, cur)}


def _keep_vars(d, cur) -> dict:
    """A day's keep for an English archer: in Days, and in pence where the coin has a Day."""
    from .money import keep_days, days_text_q, fmt
    k = keep_days(d, "medieval", "england") if "medieval" in d.equipment else None
    if not k:
        return {"keep_food": "a day's food", "keep_bed": "a night's bed"}
    say = lambda x: (f"{fmt(cur, int(x * cur['day'] + 0.5))} ({days_text_q(x)})" if cur and cur.get("day") else days_text_q(x))
    return {"keep_food": say(k["food"]), "keep_bed": say(k["bed"])}


def _army_money_rows(d: Data, eid: str) -> tuple[list, list]:
    """An era's armies: [era, army, coin, a Day, its source] rows, and [army, pay by rank] rows."""
    from .money import coin_text, region_currency
    from .ranks import ladder, pay_of
    E, T, days, pays = d.equipment[eid], d.teams[eid], [], []
    for reg in T["regions"]:
        cur = E["currencies"].get(region_currency(d, eid, reg["id"]) or "")
        if not cur:
            continue
        note = cur.get("day_note", "") + (" (an estimate)" if cur.get("day_approx") else "")
        days.append([T["name"], reg["name"], cur["name"], coin_text(d, eid, reg["id"], 1) or "no Day", note])
        if ladder(d, eid) and cur.get("day"):
            pays.append([reg["name"], " · ".join(f"{r['name']} {coin_text(d, eid, reg['id'], pay_of(d, eid, reg['id'], 'x', r['id']))}" for r in ladder(d, eid))])
    return days, pays


def _price_rows(d: Data, eid: str) -> list:
    """An era's price list: [item, when, price in its coin, about so many Days]."""
    from .money import days_text_q, price_text, row_days
    E, rows = d.equipment[eid], []
    for r in E["items"]:
        cur = E["currencies"][r.get("in") or E["currency"]["default"]]
        span = row_days(d, eid, r)
        days = "—" if span is None else days_text_q((span[0] + span[1]) / 2)
        per = f" ({r['per']})" if r.get("per") else ""
        rows.append([r["name"] + per, str(r.get("when", "")), price_text(cur, r["price"]), days])
    return rows


def _money_tables(d: Data) -> dict:
    """The money chapter's tables: each army's coin and its Day, pay by rank in that coin, and each
    era's price list in its coin with the Days it comes to."""
    out, day_rows, pay_rows = {}, [], []
    for eid in [e for e in d.teams if e in d.equipment]:
        days, pays = _army_money_rows(d, eid)
        day_rows += days
        pay_rows += pays
        out[f"prices_{eid}"] = _md(["Item", "When", "Price", "About"], _price_rows(d, eid))
    out["money_days"] = _md(["Era", "Army", "Coin", "A Day", "From"], day_rows)
    out["rank_pay"] = _md(["Army", "A day's pay by rank, before stoppages"], pay_rows)
    return out


def _talk_values(d: Data) -> dict:
    """The tongues', patrons', haggling's and march skills' numbers the chapters quote."""
    LG, PT, U = d.languages or {}, d.patrons or {}, d.uses or {}
    tongues = LG.get("tongues", {})
    sell = ((d.checks or {}).get("haggle") or {}).get("sell") or {"win": 0.1, "critical": 0.25, "fumble": -0.25}
    return {"sell_win": round(sell["win"] * 100), "sell_crit": round(sell["critical"] * 100), "sell_fumble": round(-sell["fumble"] * 100),
            "hunt_deer": (U.get("hunt") or {}).get("deer", 5), "hunt_buffalo": (U.get("hunt") or {}).get("buffalo", 40),
            "way_slow": (U.get("way") or {}).get("slow", 1.4),
            "lg_native": LG.get("native", 90), "lg_max": LG.get("max", 85), "lg_book": LG.get("phrase_book", 25),
            "lg_pidgin": (tongues.get("bamboo_english") or {}).get("cap", 35), "lg_sign": (tongues.get("plains_sign") or {}).get("cap", 75),
            "pt_start": PT.get("start", 30), "pt_persuade": PT.get("persuade_div", 10), "pt_offended": PT.get("offended", -10),
            "pt_promotion": PT.get("promotion_bonus", 20), "pt_season": (PT.get("events", {}).get("season") or {}).get("add", 2),
            **_fight_values(d)}


def _fight_values(d: Data) -> dict:
    """Rank in a fight: the numbers the Heroes section quotes."""
    H = (d.units or {}).get("heroes") or {}
    coup = ((d.ranks or {}).get("honours") or {}).get("coup") or [3]
    return {"f_rank_step": H.get("rank_step", 3), "f_rank_cap": H.get("rank_cap", 12), "f_officer": H.get("officer_exposure", 2), "f_coup": coup[0]}


def values(d: Data) -> dict:
    """The rule numbers the chapters quote, by name."""
    T, CB = d.wounds["tracking"], d.wounds["combat"]
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
        "deed_bonus": d.ranks.get("deed_bonus", 20), "literate": d.ranks.get("literate", 20), "sack_bonus": d.ranks.get("sack_bonus", 15),
        "st_base": d.stress.get("base", 115), "st_every": d.stress.get("check_every", 10), "st_toll": round(d.stress.get("toll_share", 0.4) * 100),
        "st_rest": d.stress.get("rest_day", 3.5),
        "chk_crit": round(d.checks.get("critical_fraction", 0.1) * 100), "chk_fumble": d.checks.get("fumble_from", 96),
        "haggle_seller": (d.checks.get("haggle") or {}).get("seller", 50), "haggle_win": round(-(d.checks.get("haggle") or {}).get("win", -0.1) * 100),
        "haggle_crit": round(-(d.checks.get("haggle") or {}).get("critical", -0.25) * 100),
        **_talk_values(d),
        "xp_lo": d.experience.get("gain", [1, 3])[0], "xp_hi": d.experience.get("gain", [1, 3])[1], "xp_season": d.experience.get("season_days", 91),
        "scar_upto": E["old_wound"][0]["to"], "lasting": E["lasting"], "origins": len(E["origins"]), "careers": len(E["careers"]),
        "eras": len(d.teams), **_money_vars(d),
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
    v.update(_field_values(d), **_travel_values(d), **LATER.values(d))
    v["ex"] = example(d)
    return v


def _yd(m: float) -> str:
    """'11 yards (10 m)' from metres, as the pages say it."""
    return f"{round(m * 1.0936):,} yards ({m:g} m)"


def _field_values(d: Data) -> dict:
    """The field map's numbers (units.yaml)."""
    U, M = d.units, d.units["melee"]
    MO, H = U["morale"], U["heroes"]
    return {
        "f_hex": _yd(U["hex_m"]), "ev_wagon": U["aftermath"]["medevac"]["kinds"]["wagon"]["hours"], "ev_motor": U["aftermath"]["medevac"]["kinds"]["motor"]["hours"],
        "ev_heli": U["aftermath"]["medevac"]["kinds"]["helicopter"]["hours"], "ev_heli_min": U["aftermath"]["medevac"]["kinds"]["helicopter"]["minutes"], "ammo_burn": round(U["ammunition"]["burn"] * 100), "ammo_low": round(U["ammunition"]["low"] * 100), "ammo_reach": U["ammunition"]["reach"],
        "ammo_bow": round(U["ammunition"]["loads"]["longbow"] / (U["missile"]["rate"]["longbow"] * U["ammunition"]["burn"])), "ammo_rifle": round(U["ammunition"]["loads"]["rifle_service"] / (U["missile"]["rate"]["rifle_service"] * U["ammunition"]["burn"])),
        "ammo_mg": round(U["ammunition"]["loads"]["machine_gun"] / (U["missile"]["rate"]["machine_gun"] * U["ammunition"]["burn"])), "ammo_morale": U["morale"]["mods"]["no_ammo"], "f_see_into": U["line_of_fire"].get("see_into", 1), "f_crest": U["line_of_fire"].get("crest_clear", 1), "f_rounds": U["exchange_rounds"], "f_tempo": round(1 / M["tempo"]),
        "f_flank": M["flank"]["attack"], "f_rear": M["rear"]["attack"], "f_charge": M["charge"]["attack"], "f_shaken": -M["shaken"]["attack"],
        "f_pikes": M["pikes"]["attack"], "f_charge_move": U["charge_move"], "f_mounted": U["mounted_move"],
        "f_trigger": _pct(MO["trigger"]), "f_shock": _pct(MO["shock"]), "f_shaken_by": MO["shaken_by"],
        "f_rout": U["rout"]["attack"], "f_rout_x": U["rout"]["exchanges"],
        "f_esc_pen": f"−{U['escalade']['penalty']}%", "f_esc_cross": U["escalade"]["cross"], "f_range_scale": U["range_scale"],
        "f_ground": U["to_ground"]["cover"], "f_tempo_h": f"{H['tempo']:g}", "f_exposure": f"{H['exposure']:g}", "f_duel": H["duel"],
        "f_bearers": H["bearers"], "f_back": H["back_after"], "f_first_aid": H["first_aid"],
        "f_post_pace": H["aid_post"]["pace"], "f_post_aid": H["aid_post"]["first_aid"],
        "f_saved_min": U["aftermath"]["saved"]["minutes"], "f_saved_field": U["aftermath"]["saved"]["hours"]["field"],
        "f_saved_shelter": U["aftermath"]["saved"]["hours"]["shelter"],
        "f_bow_rate": U["missile"]["rate"]["longbow"], "f_aimed": round(1 / U["missile"]["tempo"]),
        "c_remember": U["commander"]["remember"], "c_obj_radius": U["commander"]["objective"]["radius"],
        "c_obj_hold": U["commander"]["objective"]["hold"],
        "c_sp_held": U["commander"]["self_play"]["held"], "c_sp_limit": U["commander"]["self_play"]["limit"], "c_sp_after": U["commander"]["self_play"]["after_phases"], "c_sp_most": U["commander"]["self_play"]["most"], "c_sp_secure": LATER._field(d, U["commander"]["self_play"]["secure"]),
        "n_words": U["narrator"]["words"], "c_spot_moves": U["commander"]["spot"]["moves"],
        "c_sap_clear": U["commander"]["sappers"]["clear_of"],
        "c_keep_off": U["commander"]["keep_off"],
        "c_displace_shift": U["indirect"]["displace_shift"],
    }


def _travel_values(d: Data) -> dict:
    """The travel map's, camps' and the weather's numbers."""
    T, DZ, W, WX = d.terrain, d.disease, d.works, d.weather
    S = W["surprise"]
    return {
        "t_hours": T["hours_per_day"], "t_within": T["fight_within"], "t_start": f"{WX['daylight']['start_after_sunrise']:g}",
        "t_stop": f"{WX['daylight']['stop_before_sunset']:g}", "t_evening": W["evening_hours"], "t_share": _pct(W["work_share"]),
        "s_base": S["base"], "s_none": S["none"], "s_dark": S["dark"], "s_fog": S["fog"], "s_per": S["per"], "s_lo": S["range"][0], "s_hi": S["range"][1],
        "d_bearers": DZ["litters"]["bearers"], "d_march": DZ["litters"]["march"], "d_short": DZ["litters"]["short"],
        "d_unfit": DZ["unfit_from"], "d_carried": DZ["carried_from"], "d_end": DZ["endurance"],
        "sc_weeks": DZ["scurvy"]["after_days"] // 7, "sc_chance": DZ["scurvy"]["chance"], "sc_per": DZ["scurvy"]["per_week"], "sc_heal": DZ["scurvy"]["heal"],
        "fb_below_f": round(DZ["frostbite"]["below"] * 9 / 5 + 32), "fb_below": DZ["frostbite"]["below"],
        "w_deep": WX["ground"]["deep"], "w_flood": WX["ground"]["flood_days"],
        "t_foot_day": f"{T['forces']['foot']['kmh'] * T['hours_per_day'] / 1.609:.0f} miles ({T['forces']['foot']['kmh'] * T['hours_per_day']:g} km)",
        "w_snow_f": round(WX["snow_at_or_below"] * 9 / 5 + 32), "w_snow": WX["snow_at_or_below"],
    }


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
    out.update(_field_tables(d), **_travel_tables(d), **LATER.tables(d))
    if d.checks:
        from .checks import use_rows
        ur = use_rows(d, "medieval")
        out["skill_uses"] = _md(ur[0], ur[1:])
        out["difficulty"] = _md(["Difficulty", "Modifier", "When"], [[x["name"], _sign(x["mod"]) if x["mod"] else "±0", x.get("what", "")] for x in d.checks["difficulty"]])
    if d.ranks:
        RE = (d.ranks.get("eras") or {}).get("medieval") or {}
        out["ranks"] = _md(["Rank", "Pay (× a soldier's)", "Least years in the rank below", "Command check"],
                           [[r["name"], f"{r['pay']:g}", f"{r.get('years', 0):g}" if i else "—", (next((x["name"] for x in d.checks.get("difficulty", []) if x["id"] == r.get("diff")), "") + (", only after a deed" if r.get("deed_only") else "")) if i else "—"]
                            for i, r in enumerate(RE.get("ladder") or [])])
        out["finds"] = _md(["d100", "He finds", "Worth (Days)"], [[f"{lo}–{f['to']}" if lo != f["to"] else str(f["to"]), f["what"], "—" if not f["days"][1] else f"{f['days'][0]}–{f['days'][1]}"]
                                                              for f, lo in zip(d.ranks["finds"], [1] + [x["to"] + 1 for x in d.ranks["finds"][:-1]])])
    if d.languages:
        LG = d.languages
        tn = {k: v["name"] for k, v in LG["tongues"].items()}
        rows = []
        for eid, armies in LG["armies"].items():
            regions = {r["id"]: r["name"] for r in d.teams[eid]["regions"]}
            for rid, A in armies.items():
                own = ", ".join(f"{tn[t]} {s}%" for t, s in A["own"])
                others = ", ".join(f"{tn[t]} {ch}% ({lo}-{hi})" for t, ch, (lo, hi) in A.get("others", []))
                rows.append([regions[rid], own, others or "—"])
        out["tongue_armies"] = _md(["Army", "His own tongue (d100)", "Others he may have: chance (figure)"], rows)
        bands = LG["bands"]
        out["tongue_bands"] = _md(["Figure", "Reads as"], _band_rows(bands))
    if d.equipment:
        out.update(_money_tables(d))
    PU = ((d.units or {}).get("aftermath") or {}).get("pursuit")
    if PU:
        span = lambda r: f"{r[0]:g}-{r[1]:g} times" if r[1] else "none"
        out["pursuit"] = _md(["Wars", "Killed in the pursuit", "Taken prisoner"],
                             [[", ".join(PU[k]["conflicts"]), span(PU[k]["killed"]), span(PU[k]["prisoners"])] for k in ("melee", "black_powder", "modern")])
    SM = (d.stress or {}).get("mods")
    if SM:
        out["strain_mods"] = _md(["", "Strain"], [[m["name"][0].upper() + m["name"][1:], f"{m['add'] * 100:+.0f}%"] for m in SM.values()])
    if (d.training or {}).get("courses"):
        names = {e: d.teams[e]["name"].split(" (")[0] for e in d.teams}
        rows = []
        for k in d.training["courses"]:
            gains = ", ".join(f"{s} +{n}" for s, n in k.get("gains", {}).items())
            rows.append([k["name"], ", ".join(names[e] for e in k["eras"]), f"{k['weeks']} weeks", gains + (f"; opens {k['rank'].replace('_', ' ')}" if k.get("rank") else "")])
        out["courses"] = _md(["Course", "Eras", "Away", "Gains"], rows)
    if d.patrons:
        PT = d.patrons
        pb = PT["bands"]
        out["patron_bands"] = _md(["Standing", "He is"], _band_rows(pb))
        dn = {x["id"]: x["name"] for x in d.checks["difficulty"]}

        def _gives(f):
            bits = []
            if f.get("days"):
                bits.append(f"{f['days']} Days")
            if f.get("served"):
                bits.append(f"{f['served']} days served")
            if f.get("promotion"):
                bits.append(f"+{PT['promotion_bonus']} for the next vacancy")
            if f.get("ransom"):
                bits.append("his ransom")
            return ", ".join(bits) or "the GM's word"
        out["favours"] = _md(["Favour", "Difficulty", "Costs", "Gives"], [[f["name"], dn[f["difficulty"]], f"{f['cost']} Standing", _gives(f)] for f in PT["favours"]])

        def _ev(e):
            if "to" in e:
                return "Standing 0, and the patron is his enemy" if e.get("enemy") else f"Standing {e['to']}"
            if "dice" in e:
                return f"+1d{e['dice'][1]}"
            if "per_days" in e:
                return f"+1 for each {e['per_days']} Days"
            if "per" in e:
                return f"+{e['per']} a horse"
            return f"{e['add']:+d}"
        out["standing_events"] = _md(["Event", "Standing"], [[e["name"], _ev(e)] for e in PT["events"].values()])
        names = {e: d.teams[e]["name"] for e in d.teams}
        out["patron_fate"] = _md(["Era", "d100"], [[names[e], ", ".join(f"{r['chance']}% {r.get('name') or PT['fates'][r['id']]['name']}" for r in rows)]
                                                   for e, rows in PT["fate"].items()])
    if d.hazards:
        HZ = d.hazards
        sev = HZ["falls"]["severities"]

        def bands_text(bands):
            lo, out = 1, []
            for k, b in enumerate(bands + [100]):
                if b >= lo:
                    out.append(f"{lo}-{b} {sev[k]}" if b > lo else f"{b} {sev[k]}")
                    lo = b + 1
            return ", ".join(out)
        out["falls"] = _md(["Height", "d100"], [[r["name"], bands_text(r["bands"])] for r in HZ["falls"]["heights"]])
        out["swim_mods"] = _md(["", "Swimming"], [["A non-swimmer / basic / strong", " / ".join(f"{v:+d}" for v in HZ["swim"]["ability"].values())],
                                                  ["Load band, Unburdened to Immobile", " / ".join(f"{v:+d}" for v in HZ["swim"]["load"])],
                                                  ["Armour, light / medium / heavy", " / ".join(f"{v:+d}" for v in HZ["swim"]["armour"].values())],
                                                  ["Current, slow / moderate / fast / spate", " / ".join(f"{v:+d}" for v in HZ["swim"]["current"].values())],
                                                  ["Something to float on", f"+{HZ['swim']['flotation']}"]])
    if d.prisoners:
        en = {"medieval": "Medieval", "thirty_years": "Thirty Years' War", "horse_musket": "1700-1815", "crimea": "Crimea", "civil_war": "Civil War",
              "plains_nations": "Plains", "wwi": "1914-18", "wwii": "1939-45", "korea": "Korea", "vietnam": "Vietnam", "modern": "1982-2014"}
        rows = []
        for eid, cs in d.prisoners["eras"].items():
            for c in cs:
                extra = [x for x, on in (("ransom", c.get("ransom")), ("parole", c.get("parole")), ("service", c.get("service"))) if on]
                rows.append([en.get(eid, eid), c["name"], f"{c['capture'][0]}", f"{c['capture'][1]}", f"{c['release']}%", f"{c['hazard']:g}%" + (f" (then {c['after']:g}%)" if "after" in c else ""), ", ".join(extra) or "—"])
        out["prisoners"] = _md(["Era", "Captors", "Killed at or under", "Stripped at or under", "Released a season", "Dies a season", "Also"], rows)
    if d.stress:
        SX = d.stress
        out["strain"] = _md(["What", "Strain"], [[v["name"], f"+{v['strain']:g}"] for v in SX["sources"].values()])
        out["treatment"] = _md(["Where", "Days", "Back to duty: shaken", "strained", "broken down", "severely"],
                               [[t["name"] + (" (from 1916)" if "forward" == k else " (before 1914)" if k == "furlough" else ""), t["days"],
                                 *[f"{t['rtd'][x]}%" for x in ("shaken", "strained", "exhaustion", "severe")]] for k, t in SX["treatment"].items()])
    if d.loads:
        LB = d.loads["bands"]
        lo = [0] + [b["upto"] for b in LB[:-1]]
        out["loads"] = _md(["Band", "Load (share of his weight)", "March (% of the usual)", "Dodge", "Blisters (20 km)", "Extra fatigue"],
                           [[b["name"], f"{round(a * 100)}–{round(b['upto'] * 100)}%" if b["upto"] < 2 else f"over {round(a * 100)}%", f"{b['march']}%",
                             f"−{b['dodge']}" + (", no run" if b.get("run") is False else ""), f"{b['blister']}%",
                             f"a step every {b['fatigue_km']} km" if b.get("fatigue_km") else "—"] for b, a in zip(LB, lo)])
    if d.ageing:
        names = {"str": "Strength", "agi": "Agility", "end": "Endurance", "wits": "Wits"}

        def dice(v):
            if not v:
                return "—"
            n = v[0] if v[0] > 1 else ""
            return f"−{n}d{v[1]}"
        bands = d.ageing["decline"]
        out["ageing"] = _md(["Age (middle of the 4 years)", *names.values()],
                            [[f"{b['from']}–{nb['from'] - 1}" if nb else f"{b['from']} and over", *[dice(b.get(k)) for k in names]]
                             for b, nb in zip(bands, bands[1:] + [None]) if b["from"] > 0]
                            )
    if "medieval" in d.jobs:
        from .jobs import job_rows, trouble_rows
        jr, tr = job_rows(d, "medieval"), trouble_rows(d, "medieval")
        out["jobs"], out["job_trouble"] = _md(jr[0], jr[1:]), _md(tr[0], tr[1:])
    out["fq"] = _md(["Quality table", *[q.capitalize() for q in U["quality"]]],
                    [[k.capitalize(), *_ranges(rows)] for k, rows in E["followers"]["quality"].items()])
    return out


def _field_tables(d: Data) -> dict:
    U, M = d.units, d.units["morale"]["mods"]
    forms = [[f["name"], f["per_hex"], f["abreast"], f["ranks"], f["move"], f"×{f['missile_factor']:g}"] for k, f in U["formations"].items() if k not in ("armour",)]
    mods = [["Still steady, ranks closed", f"+{M['in_order']}"], ["A named leader with it, up", f"+{M['leader']}"], ["Its leader down", _sign(M["leader_down"])],
            ["Half its men down", _sign(M["heavy"])], ["Struck in flank or rear", _sign(M["flank"])], ["A steady friendly unit beside it", f"+{M['veteran_friends']}"],
            ["Dug in: gone to ground or in a bunker", f"+{M['dug_in']}"], ["Lost the exchange", f"−{M['losing_per_man']} a man more lost than it put down (at most −{M['losing_cap']})"]]
    return {"formations": _md(["Formation", "Men a hex", "Abreast", "Ranks", "Move (hexes)", "Shots at it count"], forms),
            "morale": _md(["Modifier", ""], mods)}


def _travel_tables(d: Data) -> dict:
    T, W, DZ = d.terrain, d.works, d.disease
    sp = [[f["name"], f"{f['kmh'] / 1.609:.1f} mph ({f['kmh']:g} km/h)", f"{f['kmh'] * T['hours_per_day'] / 1.609:.0f} miles ({f['kmh'] * T['hours_per_day']:g} km)"] for f in T["forces"].values()]
    ter = [[t["name"], f"×{t['cost']:g}" if t.get("cost") else "cannot enter"] for t in T["terrain"].values()]
    camps = [[c["name"], c["desc"], _needs(c), _sign(c["surprise"]), c["rest"]] for c in W["camps"].values()]
    dis = [[x["name"], x["caught"], f"{x['incubation'][0]}–{x['incubation'][1]} days", f"{x['deaths']:g}%"] for x in DZ["diseases"].values()]
    works = [[w["name"], _off(w.get("cover")), _cross(w.get("cross")), "yes" if w.get("blocks_melee") else "—"] for w in W["edge_works"].values()]
    works += [[w["name"], _off(w.get("cover_here") or w.get("cover_behind")), _cross(w.get("enter")), "—"] for w in W["hex_works"].values()]
    return {"speeds": _md(["Force", "Road speed", "A day on the road"], sp), "terrain": _md(["Terrain", "Time against a road"], ter),
            "camps": _md(["Camp", "What it is", "Needs", "Surprise", "Rest"], camps),
            "diseases": _md(["Disease", "Caught from", "Shows after", "Deaths per case (records)"], dis),
            "works": _md(["Work", "Cover", "Crossing", "Blocks close combat"], works), **_weather_tables(d)}


def _weather_tables(d: Data) -> dict:
    WX = d.weather
    wet = WX["battle"]["string_wet"]
    conds = [[c["name"], _sight(c.get("visibility")), _off(wet[c["wet"]])] for c in WX["conditions"].values()]
    winds = [[w["name"], _off(w["missile"]), _off(w["firearm"]), f"±{w['reach']}%" if w["reach"] else "—"] for w in WX["winds"]]
    mf = WX["battle"]["misfire"]
    fire = [[k.capitalize(), *[f"{v}%" if v else "—" for v in mf[k][1:]]] for k in mf]
    fat = [[f["name"], _off(f["penalty"]), f"{f['march']}%"] for f in WX["fatigue"]["levels"]]
    light = [[x["name"], _sight(x["sight"]), _off(x["aim"])] for x in WX["light"]["levels"].values()]
    return {"conditions": _md(["Weather", "Can aim to", "Bows and crossbows"], conds),
            "winds": _md(["Wind", "Bows, slings, thrown", "Firearms", "Range bands with or into it"], winds),
            "misfire": _md(["Ignition", "Rain or snow", "Heavy rain, storm, blizzard"], fire),
            "fatigue": _md(["Fatigue", "Attack and defence", "Marching speed"], fat),
            "light": _md(["Light", "Can see to aim", "Aimed fire"], light)}


def _needs(c: dict) -> str:
    """What a camp needs: tools, a village or town, or nothing."""
    if c.get("tools"):
        return "tools"
    return ", ".join(c["terrain"]) if c.get("terrain") else "—"


def _off(x) -> str:
    """'−20%' for a penalty, '—' for none."""
    return f"−{x}%" if x else "—"


def _sign(x: int) -> str:
    """+10, −20, 0."""
    if x > 0:
        return f"+{x}"
    return f"−{-x}" if x < 0 else "0"


def _sight(hexes) -> str:
    """Battle-map hexes (2 m) a man can see to aim, in yards and metres; '—' for no limit."""
    return "no limit" if hexes is None else f"{round(hexes * 2 * 1.0936):,} yards ({hexes * 2:,} m)"


def _cross(x) -> str:
    if x is None:
        return "cannot be crossed (breach it)"
    return f"+{x} movement" if x else "free"


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
    s = arch["stats"]
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
    idx = index_html(html)
    toc = md.toc.replace("</ul>\n</div>", '<li><a href="#index">Index</a></li>\n</ul>\n</div>') if idx else md.toc
    page = (root / "templates" / "rules.html").read_text(encoding="utf-8")
    return page.replace("{{TOC}}", toc).replace("{{BODY}}", html + idx)


HEAD = re.compile(r'<h([12]) id="([^"]+)">(.*?)</h\1>', re.S)
EXAMPLE = re.compile(r'<div class="admonition example">.*?</div>', re.S)
BOLD = re.compile(r"<strong>(.*?)</strong>", re.S)


def index_terms(html: str) -> dict:
    """{term: [(section id, section title)]}: each term set in bold in the book's text (not in
    the worked examples), under the nearest chapter or section heading before it. Numbers,
    dice and lead-ins of more than five words are left out; a lead-in's full stop, a step's
    number ("2. Origin.") and a leading article are dropped."""
    text = EXAMPLE.sub("", html)
    marks = sorted([(m.start(), "h", m.group(2), re.sub("<[^>]+>", "", m.group(3)).strip()) for m in HEAD.finditer(text)]
                   + [(m.start(), "b", re.sub("<[^>]+>", "", m.group(1)).strip(), None) for m in BOLD.finditer(text)])
    out, here = {}, None
    for _, kind, a, b in marks:
        if kind == "h":
            here = (a, b)
            continue
        term = _term(a)
        if term and here and here not in out.setdefault(term, []):
            out[term].append(here)
    return out


def _term(raw: str) -> str | None:
    """A bold run as an index term, or None (numbers, dice, long phrases)."""
    t = re.sub(r"^(\d+\.\s*|(a|an|the)\s+)", "", raw.strip(), flags=re.I).strip().rstrip(".:").strip()
    if not t or len(t.split()) > 5 or re.fullmatch(r"[\d%+\-–—\s,.d×x/()]+", t) or (t[0] == "d" and t[1:2].isdigit()):
        return None
    return t[0].upper() + t[1:]


def index_html(html: str) -> str:
    """The book's index: its terms (index_terms), A to Z, each linking to the sections it is in."""
    terms = index_terms(html)
    if not terms:
        return ""
    rows, letter = [], None
    for term in sorted(terms, key=lambda t: (t.casefold(), t)):
        if term[0].upper() != letter:
            letter = term[0].upper()
            rows.append(f'<h3 class="ix-letter">{letter}</h3>')
        links = ", ".join(f'<a href="#{sid}">{title}</a>' for sid, title in terms[term])
        rows.append(f'<p class="ix"><b>{term}</b>: {links}</p>')
    return '\n<h1 id="index">Index</h1>\n<div class="index">\n' + "\n".join(rows) + "\n</div>\n"
