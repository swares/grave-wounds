"""Build every output from the data folder.

    python build.py            -> dist/tables.pdf, dist/tables.md,
                                  dist/gravewounds-data.json, dist/roller.html, dist/travel.html,
                                  dist/field.html,
                                  index.html (start page for GitHub Pages)
"""
from __future__ import annotations

import html as htmllib
import json
import re
import sys
from datetime import date
from pathlib import Path

from gravewounds import load, DataError
from gravewounds.engine import table_ranges, mechanism_ranges, severity_ranges, compose_wound, weapon_mix_ranges
from gravewounds.model import MECHANISMS, SEVERITIES, THREATS, available_weapons, commons_url, resolve_table, slot_layers

ROOT = Path(__file__).parent
DIST = ROOT / "dist"

CONF_LABEL = {
    "historical": "Historical - taken directly from a source",
    "fitted": "Fitted - estimated to match published summary figures",
    "extrapolated": "Extrapolated - design estimate from analogous evidence",
}


def d2(n: int) -> str:
    return "00" if n == 100 else f"{n:02d}"


def rng(lo: int, hi: int) -> str:
    return d2(lo) if lo == hi else f"{d2(lo)}-{d2(hi)}"


def short_effect(d, e: dict) -> str:
    parts = [f"B{e['bleed']}", f"P{e['pain']}"]
    if e["shock"]:
        parts.append("Stop check")
    if e["fracture"]:
        parts.append("Fracture")
    if e["severed"]:
        parts.append("SEVERED")
    parts += [i.replace("_", " ") for i in e["impair"]]
    if e["lethal"] != "none":
        parts.append(f"Lethal: {e['lethal']}")
    return ", ".join(parts)


def class_rep(d, cls_id: str) -> str:
    return next(l["id"] for l in d.locations if l["class"] == cls_id)


def own_weapons(d, tid: str) -> list[str]:
    """Weapons offered on a table that roll location on that table itself."""
    return [w for w in available_weapons(d, tid) if resolve_table(d, tid, w) == tid]


def weapon_groups(d, tid: str) -> list[list[str]]:
    """A table's own weapons grouped by identical location multipliers (they share d100 ranges)."""
    groups = {}
    for wid in own_weapons(d, tid):
        groups.setdefault(tuple(d.wmult[tid][wid]), []).append(wid)
    return list(groups.values())


def wshort(d, wid: str) -> str:
    return d.weapons[wid].get("short") or d.weapons[wid]["name"].split(" (")[0]


def close_combat_note(d, tid: str) -> str:
    away = {}
    for w in available_weapons(d, tid):
        r = resolve_table(d, tid, w)
        if r != tid:
            away.setdefault(r, []).append(wshort(d, w))
    def auto(r, ws):
        fm = sorted({m for w in available_weapons(d, tid) if resolve_table(d, tid, w) == r for m in d.weapons[w].get("fallback_mods") or []})
        return f" with {', '.join(d.modifiers[m]['name'] for m in fm)} applied" if fm else ""
    return " ".join(f"{', '.join(ws)}: roll location on <i>{d.tables[r]['name']}</i>{auto(r, ws)}." for r, ws in away.items())


def table_mods(d, tid: str) -> list[str]:
    allowed = d.tables[tid].get("modifiers")
    return [m for m in d.modifiers if allowed is None or m in allowed]


def situation_cols(d, tid: str, wid: str) -> list[tuple[str, dict]]:
    cols = [("Normal", {r["id"]: r for r in table_ranges(d, tid, wid)})]
    for mid in table_mods(d, tid):
        m = d.modifiers[mid]
        cols.append((m.get("short", m["name"]), {r["id"]: r for r in table_ranges(d, tid, wid, [mid])}))
    return cols


def mod_effect(d, m: dict) -> str:
    parts = []
    for z, v in (m.get("zone") or {}).items():
        parts.append(f"{z} x{v:g}")
    for sd, v in (m.get("side") or {}).items():
        parts.append(f"{'left' if sd == 'L' else 'right'} side x{v:g}")
    for lid, v in (m.get("loc") or {}).items():
        parts.append(f"{d.loc[lid]['name'].lower()} x{v:g}")
    return ", ".join(parts)


def slot_text(d, v) -> str:
    layers = slot_layers(v)
    if not layers:
        return "-"
    parts = []
    for mat, lo, hi in layers:
        name = d.armor["materials"][mat]["name"].split(" (")[0]
        parts.append(name if (lo, hi) == (1, 100) else f"{name} {rng(lo, hi)}")
    return " / ".join(parts)


KIT_GROUPS = (("visby", "Armour Kits: Visby 1361"), ("roses", "Armour Kits: Wars of the Roses (c.1460)"),
              ("generic", "Armour Kits: Medieval, generic"),
              ("musket", "Armour Kits: Early modern (1600-1815)"),
              ("modern", "Armour Kits: Modern (helmets, flak vests, Kevlar, plates)"))


def kit_grid(d, group: str) -> list[list[str]]:
    kits = [k for k in d.armor["kits"].values() if k.get("group") == group and k["id"] != "none"]
    rows = [["Slot (covers)"] + [k["name"] for k in kits]]
    for slot, covers in d.armor["slots"].items():
        rows.append([f"{slot} ({covers})"] + [slot_text(d, (k.get("slots") or {}).get(slot)) for k in kits])
    rows.append(["shield (Visby tables)"] + ["Yes" if k.get("shield") else "No" for k in kits])
    return rows


def regions_text(t: dict) -> str:
    rs = t.get("regions") or []
    if rs and "count" in rs[0]:
        n = sum(r["count"] for r in rs)
        return "; ".join(f"{r.get('label', r.get('zone', ''))} = {100 * r['count'] / n:.1f}%" for r in rs) + f" (n = {n:,})"
    return "; ".join(f"{r.get('label', r.get('zone', ''))} {r['pct']:g}%" for r in rs)


ARMOR_STEPS = [
    "Use armour only on tables marked <b>armour allowed</b> (all-hits, baseline, knife and unarmed tables). "
    "The other tables already show the effect of what their soldiers wore.",
    "Find the hit location's <b>armour slot</b> in the target's kit. Empty slot: no protection.",
    "If the slot shows d100 bands (e.g. <i>Rifle plate 01-65 / Soft Kevlar 66-00</i>), roll d100 to see which layer the hit meets. "
    "A roll above the last band is a gap: no protection.",
    "Protection = the material's steps against the wound mechanism. For gunfire use the weapon's <b>threat</b> column "
    "(fragment, pistol, rifle, AP rifle). Subtract the weapon's armour defeat, if any.",
    "Lower the severity that many steps: Critical > Serious > Light > Stopped. Stopped is a bruise, no wound.",
    "<b>Shields.</b> The Visby tables assume the target carries a shield. If the target's kit has none (every modern kit, "
    "and full plate), use the <b>No shield</b> column or situation.",
]
COMBAT_STEPS = [
    "Pick the <b>attacker</b> and the <b>defender</b>. Add up each one's wound penalties (table below), capped at the limit shown.",
    "Attacker rolls d100 against <b>attack % minus penalties</b> (on the battle map, also minus any range penalty). Equal or under hits; the <b>margin</b> is the effective chance minus the roll. "
    "A roll at or under a tenth of the effective chance is a <b>critical</b>: it cannot be defended.",
    "If the defender may parry or dodge, they roll d100 against <b>defence % minus penalties</b>; equal or under avoids the blow.",
    "On a hit, roll location and mechanism as usual. <b>Severity comes from the margin</b> (bands below) instead of the severity table.",
    "Wounds switch situations on by themselves: a defender who cannot stand is <b>Target down</b>, a defender whose shield arm is useless has "
    "<b>No shield</b>, and an attacker on the ground fights as <b>Attacker lower</b>.",
]
# How wound flags are named in print: the data's `shock` flag is Grave Wounds' stop check.
FLAG_LABEL = {"shock": "stop check"}


def stop_rules(d) -> list[str]:
    """Graze, stop check and team morale, as short rules for the PDF and Markdown (from wounds.yaml)."""
    CB = d.wounds["combat"]
    SC, ST, M = CB["stop_check"], CB["states"], CB["morale"]
    res = []
    lo = 1
    for r in SC["results"]:
        name = ST[r["state"]]["name"].lower()
        span = f"by {lo}-{r['upto']}" if "upto" in r else f"by more than {lo - 1}"
        res.append(f"{span}: <b>{name}</b>" + (f" for {r['rounds']} rounds" if r.get("rounds") else " until helped or the fight ends"))
        lo = r.get("upto", 0) + 1
    rat = ", ".join(f"{k} {v}" for k, v in SC["ratings"].items())
    stunned = ST.get("stunned", {}).get("defence")
    return [
        f"<b>Graze:</b> a hit by a margin of {CB['graze_margin']} or less (not a critical) only grazes: the wound's bleed and pain drop one step each and it calls for no stop check.",
        f"<b>Stop check:</b> a {' or '.join(SC['severities'])} wound marked for one (most are) calls for d100 against the fighter's <b>Nerve</b> ({rat}), "
        f"minus pain and blood-loss penalties, and -{SC['critical_penalty']} more for a critical wound. Equal or under: he fights on. "
        f"Failed {'; '.join(res)}. Defend only and stunned fighters cannot attack"
        + (f"; stunned also -{stunned}% defence." if stunned else ".")
        + f" Pain above {d.wounds['tracking']['pain_cap']} steps calls for a stop check every round.",
        f"<b>Team morale:</b> at the end of each round, a side with {int(M['trigger'] * 100)}% or more of its fighters down rolls d100 "
        f"against the best Nerve among those still up (its leader's, if he is up), +{M['leader_present']} with a leader up, "
        f"-{M['leader_down']} if a leader is down, -{M['heavy_losses']} once {int(M['heavy'] * 100)}% are down. Over: the side breaks and runs or surrenders.",
    ]


def move_rules(d) -> list[str]:
    """Battle map movement, leaving contact, reach and range, for the PDF and Markdown (from wounds.yaml)."""
    CB = d.wounds["combat"]
    M, ST = CB["move"], CB["states"]
    def lst(xs):
        xs = [x.replace("_", " ") for x in xs]
        return xs[0] if len(xs) == 1 else ", ".join(xs[:-1]) + " and " + xs[-1]
    imp = lambda xs: f"the {lst(xs)} impairment{'s' if len(xs) > 1 else ''}"
    bands = ", ".join(f"{b['band']} {'-%d%%' % b['penalty'] if b['penalty'] else '+0'}" for b in CB["range"])
    return [
        f"<b>Scale:</b> one hex is {yd(M['hex_m'])} and a round is 6 seconds. The map has pointy-top hexes; the roller's default is {M['map']['cols']} x {M['map']['rows']}.",
        f"<b>A fighter's turn:</b> stay in place, <b>advance</b> up to {M['advance']} hexes and still attack, or <b>run</b> up to {M['run']} hexes and not attack. "
        "He may pass through friends but not stop on them, and cannot enter an enemy's hex.",
        f"<b>Wounds and movement:</b> {imp(M['halved_by'])} halve both distances (round down); {imp(M['crawl_by'])} leave only a crawl of "
        f"{M['crawl']} hex; {imp(M['no_run_by'])} stops him running. A fighter who is {' or '.join(ST[s]['name'].lower() for s in M['no_move_states'])} cannot move. "
        "Defend only: he may move but not attack.",
        f"<b>Leaving contact:</b> a fighter who moves more than {M['careful_step']} hex and ends no longer next to an enemy he started beside gives "
        f"that enemy one free attack, if the enemy is up and able to attack. Stepping back {M['careful_step']} hex is a careful withdrawal and draws none.",
        f"<b>Reach and range:</b> a close-combat weapon strikes enemies within its reach (1 is the next hex). A missile weapon has short, medium and long "
        f"range in hexes, with attack modifiers {bands}; no shot past long range. Weapons marked off-map (artillery, mines, stakes) are not aimed on the map: the GM decides whom they hit.",
    ]


SEP6 = "|---|---|---|---|---|---|"     # a six-column Markdown table rule

def unit_rules(d) -> list[str]:
    U = d.units
    M, S, R, mo = U["melee"], U["missile"], U["rout"], U["morale"]
    return [
        f"<b>Unit combat (the rank and file, on the field map):</b> one exchange is about a minute. In melee the front rank of each hex touching "
        f"the enemy strikes ({U['formations']['close']['abreast']} men a hex face in close order; reach-2 weapons add the second rank). {M['tempo'] * 100:g}% of them make a telling attempt each exchange; "
        f"archers loose their rate a minute, {S['tempo'] * 100:g}% of the shots aimed at a man. Each attempt is an individual attack against the unit's attack %, "
        "parried on its defence % (not from flank or rear, nor against missiles), then location, severity from the margin, and armour, as for one fighter.",
        f"Light wounds and grazes fight on. Serious and critical wounds call for a stop check against the unit's Nerve; a failure is down. A wound fatal within rounds kills. "
        f"Flank +{M['flank']['attack']}, rear +{M['rear']['attack']}, a mounted charge +{M['charge']['attack']} at x{M['charge']['tempo']:g} tempo, shaken {M['shaken']['attack']}.",
        f"<b>Unit morale:</b> after an exchange a unit checks if it lost the exchange, has {int(mo['trigger'] * 100)}% of its men down, lost {int(mo['shock'] * 100)}% in the exchange, "
        f"or was struck in flank or rear: d100 against Nerve, +{mo['mods']['in_order']} while steady, +{mo['mods']['leader']} with a leader, {mo['mods']['leader_down']} if he is down, "
        f"{mo['mods']['heavy']} at half strength, {mo['mods']['flank']} if flanked, -{mo['mods']['losing_per_man']} a man it lost more than it put down (at most -{mo['mods']['losing_cap']}). "
        f"Steady fails: shaken; shaken fails: broken. A broken unit flees: every enemy in reach strikes it at +{R['attack']}, no parry, x{R['tempo']:g} tempo.",
    ] + _ground_rules(d) + _hero_rules(d) + _aftermath_rules(d)


def _ground_rules(d) -> list[str]:
    G = d.units.get("ground")
    if not G:
        return []
    parts = []
    for g in G.values():
        bits = [f"move {g['move']}"] + ([f"cover -{g['cover']}%"] if g.get("cover") else []) + ([f"-{g['height']}% striking up at it"] if g.get("height") else []) \
            + (["no horses"] if g.get("no_horse") else [])
        parts.append(f"{g['name'].lower()} ({', '.join(bits)})")
    return [
        "<b>Ground and works on the field map:</b> " + "; ".join(parts) + f". Works are the battle map's, along the {yd(d.units['hex_m'])} hex sides: "
        "only reach-2 weapons strike over a palisade, wall or barred gate, from the front rank; striking up a bank, ditch or wall costs its height; "
        "a volley takes the best cover where it lands. A unit ordered to breach puts half its front rank to hacking at the work in front "
        f"(a field-map side takes {d.units['hex_m'] / d.wounds['combat']['move']['hex_m']:g} times a battle-map side's breach figure). The battle map's weather applies.",
    ]


def _hero_rules(d) -> list[str]:
    H = d.units.get("heroes")
    if not H:
        return []
    return [
        f"<b>Heroes in units:</b> a named fighter in the front rank makes {H['tempo']:g} times a ranker's telling attempts with his own attack, "
        f"and blows on the front fall on him {H['exposure']:g} times as often as on a ranker there; a shooting hero looses {H['tempo']:g} times a ranker's aimed shots. "
        "His wounds use the full rules and his own stop check (a failure: down for the battle). A leader adds his unit's leader modifier while he is up.",
    ]


def _aftermath_rules(d) -> list[str]:
    A = d.units.get("aftermath")
    if not A:
        return []
    h = A["saved"]["hours"]
    return [
        "<b>After the battle:</b> a side with no unit standing has lost the field, and its men down there are left behind, dead. "
        f"A wound fatal in minutes kills unless he is bound in time ({A['saved']['minutes']}%); one fatal in hours kills unless his camp treats it "
        f"(no camp {h['none']}%, a camp {h['field']}%, quarters {h['shelter']}%). The rest are carried to camp and heal on the wound track (Camp disease).",
    ]


def unit_rows(d) -> list[list[str]]:
    """[quality, attack, defence, nerve] and missile rates."""
    return [[q.title(), f"{v['attack']}%", f"{v['defence']}%", str(v["nerve"])] for q, v in d.units["quality"].items()]


def disease_rules(d) -> list[str]:
    D = d.disease
    L = D["litters"]
    return [
        "<b>Camp disease (forces on the travel map):</b> each force counts its sick, by disease and by step on the track "
        "(mending, serious, grave, deadly). Once a week each well man may catch each disease: his chance is the outbreak chance below, "
        f"with the week's modifiers, times the chance he fails to resist (half, at Endurance {D['endurance']}). A man carries one disease at a time.",
        "A case shows after its incubation at mending, climbs a step a day to the peak rolled below, then makes a recovery check each day: "
        f"d100 against Endurance, plus care (no camp {D['recovery']['care']['none']}, a camp {D['recovery']['care']['field']:+d}, quarters {D['recovery']['care']['shelter']:+d}), "
        f"activity (marched {D['recovery']['activity']['marched']:+d}, rested {D['recovery']['activity']['rest']:+d}), "
        f"a cold wet night beyond the shelter {D['recovery']['wet_cold']:+d}, poor hygiene {D['recovery']['filth']:+d}, less the disease's virulence. "
        f"Success by {D['recovery']['big']} or more: two steps better; success: one; failure: no change; failure by {D['recovery']['big']} or more: one worse. "
        "At deadly, any failure kills. Typhus and plague leave survivors immune; ague relapses in marsh country; flux can turn chronic.",
        f"Men at serious or worse do not dig or fight. Grave and deadly cases go on litters: the force marches at {L['march']}%, "
        f"or {L['short']}% with fewer than {L['bearers']} fit men a litter, and cannot march with none. "
        "Hygiene comes from the camp (bivouac poor, quarters good, others fair) unless the GM sets it. Plague needs the GM's \"plague in the region\".",
    ] + _wound_track_rules(d)


def _wound_track_rules(d) -> list[str]:
    W = d.disease.get("wounds")
    if not W:
        return []
    st, fc, fcare = W["start"], W["fever_chance"], W["fever_care"]
    return [
        f"<b>The wounded (from the field map):</b> a wounded man starts at {st['light']} (light), {st['serious']} (serious) or {st['critical']} (critical), "
        f"and at {W['clock_step']['hours']} if the wound would kill in hours. He makes the same recovery check, but once every {W['wound']['every']} days, "
        f"at virulence {W['wound']['virulence']}. {W['fever_after'][0]}-{W['fever_after'][1]} days after the battle the wound turns septic on d100: "
        f"low infection risk {fc['low']}%, medium {fc['medium']}%, high {fc['high']}% (no camp {fcare['none']:+d}, quarters {fcare['shelter']:+d}). "
        f"Wound fever is one step worse and checks every day at virulence {W['fever']['virulence']}.",
    ]


def disease_rows(d) -> list[list[str]]:
    """[disease, caught from, shows after, outbreak chance and modifiers, peak, deaths]."""
    D, out = d.disease, []
    for x in D["diseases"].values():
        mods = ", ".join(f"{k.replace('_', ' ')} {v:+g}" for k, v in x["mods"].items())
        needs = " (only with " + " and ".join(x["needs"]) + ")" if x.get("needs") else ""
        lo = 1
        peak = []
        for r in x["peak"]:
            peak.append(f"{lo:02d}-{r['upto'] % 100:02d} {r['step']}")
            lo = r["upto"] + 1
        out.append([x["name"], x["caught"], f"{x['incubation'][0]}-{x['incubation'][1]} days",
                    f"{x['base']}%{needs}" + (f"; {mods}" if mods else ""), ", ".join(peak), f"{x['deaths']}% (virulence {x['virulence']})"])
    return out


def weather_rules(d) -> list[str]:
    WX = d.weather
    DL, F = WX["daylight"], WX["fatigue"]
    return [
        f"<b>Calendar and daylight:</b> each map has a start date (Julian or Gregorian), a latitude and a climate. The march starts "
        f"{DL['start_after_sunrise']:g} hour after sunrise and stops {DL['stop_before_sunset']:g} before sunset, up to {d.terrain['hours_per_day']} hours.",
        f"<b>Weather:</b> each day is rolled from the climate's monthly normals, wet and dry spells tending to last ({int(WX['persistence'] * 100)}% persistence). "
        f"Wet days fall as snow when the high is {WX['snow_at_or_below'] * 9 / 5 + 32:.0f} °F ({WX['snow_at_or_below']} °C) or less. The GM can change any day.",
        "<b>Ground:</b> rain builds mud and snow lies, wearing off in dry or mild weather; heavy rain floods fords for two days. "
        "Mud and snow slow the march (see the table below); deep mud or snow costs +1 movement per hex in battle.",
        "<b>Rest and fatigue:</b> the night's rest starts from the camp's and drops a step for each point of hardship (wet, cold) beyond its shelter. "
        f"Fatigue changes each night: heat or cold on a march of {F['heat_cold_min_hours']} hours or more, {F['heavy_going_hours']} hours in deep mud or snow, "
        "and the night (bad +1, poor 0, fair -1, good -2).",
    ]


def weather_tables(d) -> dict:
    WX = d.weather
    conds = [["Weather", "Missile sight", "Bows, crossbows", "Firearms", "Night hardship"]]
    for c in WX["conditions"].values():
        sw = WX["battle"]["string_wet"][c["wet"]]
        sight = "clear" if c.get("visibility") is None else f"{c['visibility']} hexes, {yd(c['visibility'] * d.wounds['combat']['move']['hex_m'])}"
        conds.append([c["name"], sight, f"-{sw}%" if sw else "-",
                      "may misfire" if c["wet"] else "-", str(c["hardship"])])
    mis = [["Ignition", "Dry", "Wet", "Very wet"]] + [[k.capitalize(), *[f"{x}%" for x in v]] for k, v in WX["battle"]["misfire"].items()]
    fat = [["Fatigue", "Attack and defence", "Marching speed"]] + [[l["name"], f"-{l['penalty']}%" if l["penalty"] else "-",
                                                                   "cannot march" if not l["march"] else f"{l['march']}%"] for l in WX["fatigue"]["levels"]]
    mon = ["J", "F", "M", "A", "M", "J", "J", "A", "S", "O", "N", "D"]
    clim = [["Climate", ""] + mon]
    for cl in WX["climates"].values():
        clim.extend([[cl["name"], "high/low °F"] + [f"{h * 9 / 5 + 32:.0f}/{l * 9 / 5 + 32:.0f}" for h, l in zip(cl["high"], cl["low"])],
                     ["", "(°C)"] + [f"{h}/{l}" for h, l in zip(cl["high"], cl["low"])],
                     ["", "wet days"] + [str(x) for x in cl["rain"]]])
    ground = [["Terrain", "Mud", "Snow"]] + [[t["name"], f"x{d.weather['march']['mud'].get(tid, 100) / 100:g}", f"x{d.weather['march']['snow'].get(tid, 100) / 100:g}"]
                                             for tid, t in d.terrain["terrain"].items() if t["cost"] is not None]
    return {"conds": conds, "misfire": mis, "fatigue": fat, "climates": clim, "ground": ground}


def travel_rules(d) -> list[str]:
    T = d.terrain
    return [
        f"<b>Travel map:</b> hexes are usually {mi(1)}. A force marches {T['hours_per_day']} hours a day from {T['day_starts']:02d}:00 at its type's road speed. "
        "Crossing from one hex to the next takes the average of the two terrains' time multipliers; rivers and lakes are crossed only at a ford or bridge.",
        "A force stops for the night rather than start a hex it cannot finish that day. Wagons cannot enter "
        + (lambda xs: ", ".join(xs[:-1]) + " or " + xs[-1] if len(xs) > 1 else "".join(xs))([TT_name(d, t) for t in T["forces"].get("wagons", {}).get("cannot_enter", [])]) + ".",
        "Speeds are for a small, fit band. A large army's column made less ground a day; cut its hours or speed to suit.",
        "<b>Marching together:</b> forces on one side within a hex can march as a column behind a leader. The column keeps out of ground any of them "
        "cannot enter, moves at its slowest and most tired force's pace, keeps one clock, and makes one camp sized for all its men, with every man digging.",
    ]


def TT_name(d, tid: str) -> str:
    return d.terrain["terrain"][tid]["name"].lower()


def travel_rows(d) -> list[list[str]]:
    """[terrain, time multiplier, miles (km) a day for each force type] (whole hexes of that terrain)."""
    T = d.terrain
    out = []
    for t in T["terrain"].values():
        row = [t["name"], "impassable" if t["cost"] is None else f"x{t['cost']:g}"]
        for fid, f in T["forces"].items():
            ok = t["cost"] is not None and t["id"] not in f.get("cannot_enter", [])
            km = f["kmh"] * T["hours_per_day"] / t["cost"] if ok else 0
            row.append(f"{km * 0.62137119:.0f} ({km:.0f})" if ok else "-")
        out.append(row)
    return out


def camp_rows(d) -> list[list[str]]:
    """[camp, what it is, needs, hours for 12 / 100 / 1,000 men on foot (timber hauled)]."""
    from gravewounds import travel as T
    W = d.works
    m = {"rows": ["." * 3] * 3, "hex_km": 1}                  # open ground, no woods near
    vm = {"rows": ["vvv"] * 3, "hex_km": 1}
    out = []
    for cid, c in W["camps"].items():
        needs = ", ".join(x for x in [("tools" if c.get("tools") else ""),
                                      ("a " + " or ".join(d.terrain["terrain"][t]["name"].lower() for t in c["terrain"]) if c.get("terrain") else "")] if x) or "-"
        hrs = []
        for men in (12, 100, 1000):
            r = T.camp_hours(d, vm if c.get("terrain") else m, [1, 1], cid, men, "foot", True)
            hrs.append("-" if "error" in r else (f"{r['hours']:.1f} h" if r["hours"] else "none"))
        out.append([c["name"], c["desc"], needs] + hrs)
    return out


def works_rows(d) -> list[list[str]]:
    """[work, where, labour, crossing, cover, height, breach]."""
    W = d.works
    out = []
    for wid, w in W["edge_works"].items():
        lab = f"{w['each']} man-h each" if "each" in w else ("not built in the field" if w.get("per_metre") is None else f"{w['per_metre']:g} man-h/m" + (f" (+{w['haul']:g} hauled)" if w.get("haul") else ""))
        cross = "barred (open: free)" if w.get("gate") else ("blocks" if w.get("cross") is None else f"+{w['cross']}")
        cov = f"-{w['cover']}%" + (" (high side)" if w.get("cover_side") == "high" else "") if w.get("cover") else "-"
        ht = f"-{w['height']}% attacking up" if w.get("height") else ("reach 2 only" if w.get("blocks_melee") else "-")
        if w.get("height") and w.get("blocks_melee"):
            ht += "; reach 2 only"
        out.append([w["name"], "edge", lab, cross, cov, ht, f"{w['breach']} man-rounds" if w.get("breach") else "-"])
    for wid, w in W["hex_works"].items():
        lab = f"{w['each']:g} man-h" + (f" (+{w['haul']:g} hauled)" if w.get("haul") else "") if w.get("each") else "carried"
        cross = "blocks" if w.get("enter") is None else (f"+{w['enter']}" if w["enter"] else "free")
        cov = (f"-{w['cover_here']}% in it" if w.get("cover_here") else "") or (f"-{w['cover_behind']}% behind it" if w.get("cover_behind") else "-")
        out.append([w["name"], "hex", lab, cross, cov, "no horses" if w.get("no_horse") else "-", f"{w['breach']} man-rounds" if w.get("breach") else "-"])
    return out


def works_rules(d) -> list[str]:
    W = d.works
    return [
        f"<b>Making camp:</b> a camp's works are those the battle map lays out for it: a ring of hexes big enough for the force (about {W['camp_area']['foot']} m2 a man on foot, "
        f"{W['camp_area']['mounted']} with horses), with the bank and palisade on its edge and the ditch one ring out. {int(W['work_share'] * 100)}% of the men work at once; the rest guard and cook. Work uses what is left of "
        f"the day's marching hours and then {W['evening_hours']} evening hours, so a camp made after the march costs no marching time; beyond that it runs on "
        "into the next day. Timber for palisades and stakes takes longer to fetch when no woods are within a hex. "
        f"A fight can be set up only once an enemy force has marched to within {d.terrain['fight_within']} hex of the camp. "
        "If it arrives before the camp is finished, the GM chooses: attack the works built so far, or wait. Works go up in the order listed, "
        "each kind all round from the gate before the next.",
        "<b>Works on the battle map:</b> ditches, banks, palisades, gates and walls lie along hex edges; stakes, abatis, pavises and wagons fill a hex. "
        "Crossing costs extra movement; a palisade, a barred gate or a wall stops movement until breached. Missile attacks on a man right behind a work lose its cover. "
        "In close combat only reach-2 weapons (spears, bills) strike over a palisade, gate or wall, and a man attacking up at a defender on the high side of a bank, ditch or wall takes its height penalty.",
        "<b>Breaching:</b> a fighter next to a work can spend his attack on it: one man-round. When the man-rounds reach the work's breach number it is open. "
        "A gate is opened or barred from inside.",
    ]


def reach_rows(d) -> list[list[str]]:
    """[weapon, reach or range] for every weapon, in data order."""
    out = []
    for w in d.weapons.values():
        if w.get("off_map"):
            v = "off-map (GM decides)"
        elif "reach" in w:
            v = f"reach {w['reach']}"
        else:
            hm = d.wounds["combat"]["move"]["hex_m"]
            v = " / ".join(str(x) for x in w["range"]) + " hexes (" + " / ".join(f"{round(x * hm * 1.0936133)}" for x in w["range"]) \
                + " yd; " + " / ".join(str(x * hm) for x in w["range"]) + " m)"
        out.append([w["name"], v])
    return out


CALLED_RULE = "Roll the location twice; keep whichever result lands in the called zone. If both or neither do, keep the first. Your system sets any to-hit penalty."


# --------------------------------------------------------------------------
# Bundle (single source for the web roller)
# --------------------------------------------------------------------------
def travel_bundle(d) -> dict:
    """What the travel page needs: terrain, force types and the maps."""
    return {
        "generated": date.today().isoformat(),
        "terrain": d.terrain,
        "works": d.works,
        "weather": d.weather,
        "disease": d.disease,
        "battle_hex_m": d.wounds["combat"]["move"]["hex_m"],
        "maps": {mid: {k: m.get(k) for k in ("id", "name", "hex_km", "rows", "places", "forces",
                                                "start_date", "calendar", "latitude", "climate", "climate_shift")} for mid, m in d.maps.items()},
    }


def yd(m: float) -> str:
    """A distance in metres as US units with metric in brackets: '27 yd (25 m)'."""
    y = m * 1.0936133
    return f"{y:.1f} yd ({m:g} m)" if y < 10 else f"{round(y):g} yd ({m:g} m)"


def mi(km: float) -> str:
    """A distance in kilometres as miles with km in brackets: '0.6 mi (1 km)'."""
    return f"{km * 0.62137119:.1f} mi ({km:g} km)"


CAMP_MARK = "/*__CAMP_JS__*/"
MEASURE_MARK = "/*__MEASURE_JS__*/"


def field_bundle(d) -> dict:
    """What the field map needs: the unit rules, and for every table and weapon the d100 ranges
    the wound roll looks up (precomputed here so the page rolls exactly as roll_hit does)."""
    from gravewounds.engine import armor_at
    rng3 = lambda rs: [[r["id"], r["lo"], r["hi"]] for r in rs]
    tables = {}
    for tid, t in d.tables.items():
        ws = available_weapons(d, tid)
        tables[tid] = {"name": t["name"], "label": t.get("label", t["name"]), "battle": t.get("battle", "Other"),
                       "weapons": ws, "ranges": {w: rng3(table_ranges(d, tid, w)) for w in ws}}
    used = sorted({w for t in tables.values() for w in t["weapons"]})
    keep = ("name", "short", "reach", "range", "threat", "armor_defeat", "off_map", "string", "ignition")
    mechs = sorted({m[0] for w in used for m in rng3(mechanism_ranges(d, w))})
    return {
        "generated": date.today().isoformat(),
        "units": d.units,
        "combat": {k: d.wounds["combat"][k] for k in ("critical_fraction", "graze_margin", "margin_bands", "range")},
        "tables": tables,
        "weapons": {w: {k: d.weapons[w][k] for k in keep if k in d.weapons[w]} for w in used},
        "mechanisms": {w: rng3(mechanism_ranges(d, w)) for w in used},
        "locations": {l["id"]: {"zone": l["zone"], "name": l["name"]} for l in d.locations},
        "kits": {k: {"name": v["name"], "layers": {l["id"]: [list(x) for x in armor_at(d, k, l["id"])] for l in d.locations}}
                 for k, v in d.armor["kits"].items()},
        "materials": {m: {k: v[k] for k in ("cut", "pierce", "crush", "ballistic", "threats") if k in v} for m, v in d.armor["materials"].items()},
        "effects": {l["id"]: {m: {s: _lethal_inf(compose_wound(d, l["id"], m, s)) for s in ("light", "serious", "critical")} for m in mechs}
                    for l in d.locations},
        "track": {"steps": d.disease["steps"], "wounds": d.disease["wounds"]},
        "works": d.works,
        "weather": {k: d.weather[k] for k in ("winds", "conditions", "battle", "ground")},
        "battle_hex_m": d.wounds["combat"]["move"]["hex_m"],
    }


def _lethal_inf(fx: dict) -> list:
    """[untreated time to death, infection risk] of a composed wound (the field page's two)."""
    return [fx["lethal"], fx["infection"]]


def bundle(d) -> dict:
    tables = {}
    for tid, t in d.tables.items():
        tables[tid] = {
            "id": tid, "name": t["name"], "label": t.get("label", t["name"]), "variant": t.get("variant"),
            "context": t.get("context", ""), "confidence": t.get("confidence"),
            "armor_note": t.get("armor_note", "").strip(), "status": t.get("status", "").strip(),
            "sources": t.get("sources", []), "weapons": available_weapons(d, tid), "own_weapons": t["weapons"],
            "resolve": {w: resolve_table(d, tid, w) for w in available_weapons(d, tid)},
            "wmult": d.wmult[tid], "armor": t["armor"], "native": t["native"], "weapon_bias": t["weapon_bias"],
            "assumes_shield": t["assumes_shield"],
            "battle": t.get("battle", "Other"), "confidence_note": t.get("confidence_note", ""),
            "regions": t.get("regions", []), "regions_text": regions_text(t), "modifiers": table_mods(d, tid),
            "weapon_mix": weapon_mix_ranges(d, tid), "weapon_mix_source": t.get("weapon_mix_source", ""),
            "weights": {l["id"]: float(t["weights"].get(l["id"], 0)) for l in d.locations},
        }
    wounds = {}
    for cid in d.wounds["classes"]:
        rep = class_rep(d, cid)
        for m in MECHANISMS:
            for s in SEVERITIES:
                wounds[f"{cid}|{m}|{s}"] = compose_wound(d, rep, m, s)
    return {
        "generated": date.today().isoformat(),
        "locations": d.locations,
        "weapons": {wid: {**w, "mech_ranges": mechanism_ranges(d, wid)} for wid, w in d.weapons.items()},
        "tables": tables,
        "severity": d.wounds["severity"]["tiers"],
        "severity_by_mechanism": d.wounds["severity"].get("by_mechanism") or {},
        "mechanisms": {m: {"name": v["name"], "desc": v["desc"]} for m, v in d.wounds["mechanisms"].items()},
        "vocabulary": d.wounds["vocabulary"],
        "tracking": d.wounds["tracking"],
        "combat": d.wounds["combat"],
        "works": d.works,
        "weather": d.weather,
        "wounds": wounds,
        "modifiers": list(d.modifiers.values()),
        "called_shot": d.called_shot,
        "armor": {"materials": d.armor["materials"], "slots": d.armor["slots"],
                  "kits": [{**k, "layers": {sl: slot_layers(v) for sl, v in (k.get("slots") or {}).items()}}
                           for k in d.armor["kits"].values()],
                  "sources": d.armor.get("sources", [])},
        "threats": list(THREATS),
        "conflicts": d.conflicts,
        "maps": load_maps(d),
    }


# --------------------------------------------------------------------------
# Markdown
# --------------------------------------------------------------------------
def markdown(d) -> str:
    out = ["# Hit Location & Wound Tables", "",
           f"Generated {date.today().isoformat()} from the data folder. Roll d100 (00 = 100).", "",
           "**Procedure:** 1) d100 location on the table for the fight and weapon (situation column if one applies; "
           "called shots roll twice). 2) d100 mechanism for the weapon. 3) Severity from your system's damage, or d100. "
           "4) Armour (adjusted tables): lower severity by the material's steps. "
           "5) Look up the wound by location class and severity, then apply the mechanism modifiers.", ""]
    prev_battle = None
    for tid, t in d.tables.items():
        if t.get("battle") != prev_battle:
            prev_battle = t.get("battle")
            c = d.conflicts.get(prev_battle)
            if c:
                out += [f"# {prev_battle}" + (f" ({c['period']})" if c.get("period") else ""), "", " ".join(c["summary"].split()), ""]
                if c.get("sides"):
                    out += ["| Side | Who | Armour |", "|---|---|---|"]
                    out += [f"| {x['name']} | {x['who']} | {x['armour']} |" for x in c["sides"]] + [""]
                if c.get("examples"):
                    out += ["**Example combatants**", "", "| Name | Side | Wears | Fights with | Notes | Picture |", SEP6]
                    out += [f"| {e['name']} | {e['side']} | {d.armor['kits'][e['kit']]['name']} | {d.weapons[e['weapon']]['name']} | {e.get('notes', '')} | "
                            + (f"[{e['image']['caption']}]({commons_url(e['image']['file'])})" if e.get("image") else "") + " |"
                            for e in c["examples"]] + [""]
                cmp_ = c.get("comparison")
                if cmp_:
                    out += [f"**{cmp_['title']}**", "", "| | " + " | ".join(cmp_["columns"]) + " |", "|---|" + "---|" * len(cmp_["columns"])]
                    out += ["| " + " | ".join(r) + " |" for r in cmp_["rows"]]
                    out += ["", " ".join(cmp_["note"].split()), "", f"Source: {cmp_['source']}", ""]
                if c.get("sources"):
                    out += ["Sources: " + " ".join(c["sources"]), ""]
        ws = own_weapons(d, tid)
        cols = {w: {r["id"]: r for r in table_ranges(d, tid, w)} for w in ws}
        out += [f"## {t['name']}", "", f"*{t.get('context','')}*", "",
                f"Confidence: **{CONF_LABEL[t['confidence']]}** · Armour: **{'allowed' if t['armor'] == 'allowed' else 'already reflected (do not apply)'}**", ""]
        out.append("| Location | " + " | ".join(wshort(d, w) for w in ws) + " |")
        out.append("|---|" + "---|" * len(ws))
        for loc in d.locations:
            cells = []
            for w in ws:
                r = cols[w].get(loc["id"])
                cells.append(rng(r["lo"], r["hi"]) if r else "-")
            if any(c != "-" for c in cells):
                out.append(f"| {loc['name']} | " + " | ".join(cells) + " |")
        if t.get("regions"):
            out += ["", f"**Source totals:** {regions_text(t)}. {t.get('confidence_note','')}"]
        if t.get("weapon_mix"):
            out += ["", "**What hit them? (d100)**", "", "| d100 | Cause |", "|---|---|"]
            out += [f"| {rng(r['lo'], r['hi'])} | {r['label']} |" for r in weapon_mix_ranges(d, tid)]
            out += ["", f"Source: {t.get('weapon_mix_source', '')}"]
        cc = close_combat_note(d, tid)
        if cc:
            out += ["", "**Close combat:** " + re.sub("</?i>", "*", cc)]
        out += ["", f"**Reading it:** {t.get('armor_note','').strip()}", "",
                f"**Status:** {t.get('status','').strip()}", "", "Sources:"]
        out += [f"- {s}" for s in t.get("sources", [])] + [""]

    out += ["## Situations", "",
            "Modifiers stack in the roller and CLI (one per group). Printed columns below show one situation at a time.", "",
            "| Situation | Group | Effect on weights | Notes |", "|---|---|---|---|"]
    for m in d.modifiers.values():
        used = ", ".join(t["name"].split(" - ")[0] for tid, t in d.tables.items() if m["id"] in table_mods(d, tid))
        out.append(f"| {m['name']} | {m.get('group','-')} | {mod_effect(d, m)} | {m['desc']} Tables: {', '.join(dict.fromkeys(used.split(', ')))} |")
    out += ["", f"**Called shot:** {CALLED_RULE}", ""]
    for tid, t in d.tables.items():
        groups = weapon_groups(d, tid)
        for group in (groups if t["native"] != "gunfire" else groups[:1]):
            wid = group[0]
            cols = situation_cols(d, tid, wid)
            out += [f"### {t['name']} - {' / '.join(wshort(d, w) for w in group)}", "",
                    "| Location | " + " | ".join(c for c, _ in cols) + " |", "|---|" + "---|" * len(cols)]
            for loc in d.locations:
                cells = [rng(c[loc["id"]]["lo"], c[loc["id"]]["hi"]) if loc["id"] in c else "-" for _, c in cols]
                if any(x != "-" for x in cells):
                    out.append(f"| {loc['name']} | " + " | ".join(cells) + " |")
            out.append("")

    CB, TR = d.wounds["combat"], d.wounds["tracking"]
    out += ["## Fighting while wounded", ""] + [f"{i}. {re.sub('</?b>', '**', x)}" for i, x in enumerate(COMBAT_STEPS, 1)]
    out += ["", f"Penalties add up; each total is capped at -{CB['cap']}%.", "", "| Cause | Attack | Defence | Also |", "|---|---|---|---|",
            f"| Pain, per step (max {TR['pain_cap']}) | -{CB['pain_step']}% | -{CB['pain_step']}% | |"]
    for th in sorted(TR["thresholds"], key=lambda t: -t["at"]):
        p_ = f"-{th['penalty']}%" if th.get("penalty") else "-"
        out.append(f"| Blood at {int(th['at'] * 100)}% or less | {p_} | {p_} | {'incapacitated' if th.get('incapacitated') else ('on the ground' if th.get('down') else '')} |")
    for imp, rule in CB["impair"].items():
        parts = [(f"{imp} ({arm.replace('_', ' ')})", rule[arm]) for arm in ("weapon_arm", "shield_arm") if arm in rule] \
            if ("weapon_arm" in rule or "shield_arm" in rule) else [(imp, rule)]
        for label, eff in parts:
            if eff:
                also = ", ".join(k.replace("_", " ") for k in ("down", "off_hand", "no_shield", "incapacitated") if eff.get(k))
                out.append(f"| {label.replace('_', ' ')} | {'-%d%%' % eff['attack'] if eff.get('attack') else '-'} | {'-%d%%' % eff['defence'] if eff.get('defence') else '-'} | {also} |")
    mb = CB["margin_bands"]
    out += ["", "| Severity by margin | Light | Serious | Critical |", "|---|---|---|---|",
            f"| Default | 0-{mb['default']['serious'] - 1} | {mb['default']['serious']}-{mb['default']['critical'] - 1} | {mb['default']['critical']}+ |"]
    out += [f"| Firearm/explosive, {', '.join(b['zones'])} | 0-{b['serious'] - 1} | {b['serious']}-{b['critical'] - 1} | {b['critical']}+ |" for b in mb.get("ballistic", [])]
    out += ["", "### Graze, stop check and morale", ""] + [re.sub("</?b>", "**", x) + "\n" for x in stop_rules(d)]
    out += ["### Battle map", ""] + [re.sub("</?b>", "**", x) + "\n" for x in move_rules(d)]
    out += ["| Weapon | Reach or range (short / medium / long) |", "|---|---|"] + [f"| {a} | {b} |" for a, b in reach_rows(d)] + [""]
    if d.works.get("camps"):
        out += ["## Camps and works", ""] + [re.sub("</?b>", "**", x) + "\n" for x in works_rules(d)]
        out += ["| Camp | What it is | Needs | 12 men | 100 men | 1,000 men |", SEP6] + ["| " + " | ".join(r) + " |" for r in camp_rows(d)] + [""]
        out += ["| Work | Lies on | Labour | Crossing | Cover | Close combat | Breach |", "|---|---|---|---|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in works_rows(d)] + [""]
    if d.weather:
        wt = weather_tables(d)
        md = lambda rows: ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])] + ["| " + " | ".join(r) + " |" for r in rows[1:]] + [""]
        out += ["## Weather", ""] + [re.sub("</?b>", "**", x) + "\n" for x in weather_rules(d)]
        out += md(wt["conds"]) + md(wt["misfire"]) + md(wt["fatigue"]) + md(wt["ground"]) + md(wt["climates"])
    if d.units:
        out += ["## Unit combat", ""] + [re.sub("</?b>", "**", x) + "\n" for x in unit_rules(d)]
        out += ["| Quality | Attack | Defence | Nerve |", "|---|---|---|---|"] + ["| " + " | ".join(r) + " |" for r in unit_rows(d)] + [""]
        rates = d.units["missile"]["rate"]
        out += ["| Missile weapon | Shots a minute |", "|---|---|"] + [f"| {d.weapons[w]['name']} | {n} |" for w, n in rates.items()] + [""]
    if d.disease:
        out += ["## Camp disease", ""] + [re.sub("</?b>", "**", x) + "\n" for x in disease_rules(d)]
        out += ["| Disease | Caught from | Shows after | Outbreak chance a week | Peak (d100) | Deaths per case in the records |", SEP6]
        out += ["| " + " | ".join(r) + " |" for r in disease_rows(d)] + [""]
    if d.terrain["terrain"]:
        ft = d.terrain["forces"]
        out += ["## Travel", ""] + [re.sub("</?b>", "**", x) + "\n" for x in travel_rules(d)]
        out += ["| Terrain | Time | " + " | ".join(f"{f['name']} mi (km) a day" for f in ft.values()) + " |",
                "|---|---|" + "---|" * len(ft)] + ["| " + " | ".join(r) + " |" for r in travel_rows(d)] + [""]

    out += ["## Armour", ""] + [f"{i}. {re.sub('<[^>]+>', '**', x)}" for i, x in enumerate(ARMOR_STEPS, 1)]
    mcols = [m for m in MECHANISMS if m != "ballistic"]
    out += ["", "| Material | " + " | ".join(m.title() for m in mcols) + " | " + " | ".join(f"Gunfire: {t}" for t in THREATS) + " |",
            "|---|" + "---|" * (len(mcols) + len(THREATS))]
    for mat in d.armor["materials"].values():
        th = mat.get("threats") or {}
        out.append(f"| {mat['name']} | " + " | ".join(str(mat[m]) for m in mcols) + " | "
                   + " | ".join(str(th.get(t, mat["ballistic"])) for t in THREATS) + " |")
    out += ["", "Weapon armour defeat: " + "; ".join(
        f"{w['name']}: {', '.join(f'-{v} vs {k}' for k, v in w['armor_defeat'].items())}"
        for w in d.weapons.values() if w.get("armor_defeat")), ""]
    for group, title in KIT_GROUPS:
        g = kit_grid(d, group)
        out += [f"### {title}", "", "| " + " | ".join(g[0]) + " |", "|" + "---|" * len(g[0])]
        out += ["| " + " | ".join(r) + " |" for r in g[1:]] + [""]
    out += ["Sources: " + " ".join(d.armor.get("sources", [])), ""]

    out += ["## Wound mechanism (d100)", "", "| Weapon | " + " | ".join(m.title() for m in MECHANISMS) + " | Threat |",
            "|---|" + "---|" * (len(MECHANISMS) + 1)]
    for wid, w in d.weapons.items():
        mr = {r["id"]: r for r in mechanism_ranges(d, wid)}
        out.append(f"| {w['name']} | " + " | ".join(rng(mr[m]["lo"], mr[m]["hi"]) if m in mr else "-" for m in MECHANISMS)
                   + f" | {w.get('threat') or ('melee: ' + w['melee'] if w.get('melee') else '-')} |")
    out += ["", "## Severity (d100, if your system doesn't decide it)", "", "| d100 | Severity | Guide |", "|---|---|---|"]
    for t in d.wounds["severity"]["tiers"]:
        out.append(f"| {rng(*t['d100'])} | {t['name']} | {t['guide']} |")
    for mech, spec in (d.wounds["severity"].get("by_mechanism") or {}).items():
        out += ["", f"### Severity for {d.wounds['mechanisms'][mech]['name'].lower()} hits", "",
                spec.get("note", "").strip(), "", "| Hit zone | Light | Serious | Critical |", "|---|---|---|---|"]
        for tbl in spec["tables"]:
            tr = {t["id"]: rng(*t["d100"]) for t in tbl["tiers"]}
            out.append(f"| {', '.join(tbl['zones'])} | {tr['light']} | {tr['serious']} | {tr['critical']} |")

    for m in MECHANISMS:
        out += ["", f"## Wound effects - {d.wounds['mechanisms'][m]['name']}",
                "", d.wounds["mechanisms"][m]["desc"], "",
                "| Location | Light | Serious | Critical | Infection |", "|---|---|---|---|---|"]
        for cid in d.wounds["classes"]:
            rep = class_rep(d, cid)
            es = [compose_wound(d, rep, m, s) for s in SEVERITIES]
            out.append(f"| {cid.replace('_',' ').title()} | " + " | ".join(short_effect(d, e) for e in es)
                       + f" | {es[1]['infection']} |")
    V = d.wounds["vocabulary"]
    out += ["", "## Key", "", "**B** = Bleed, **P** = Pain", ""]
    out += [f"- Bleed {k}: {v}" for k, v in V["bleed"].items()]
    out += [f"- Pain {k}: {v}" for k, v in V["pain"].items()]
    out += [f"- **{k.replace('_',' ')}**: {v}" for k, v in V["impair"].items()]
    out += [f"- **{FLAG_LABEL.get(k, k)}**: {v}" for k, v in V["flags"].items()]
    out += [f"- Lethal **{k}**: {V['lethal'][k]}" for k in V["lethal"]["order"]]
    T = d.wounds["tracking"]
    out += ["", "## Survival tracking (optional)", "", f"Blood pool: {T['blood_pool']} points.", ""]
    out += [f"- At {int(th['at']*100)}% Blood: {th['effect']}" for th in T["thresholds"]]
    out += [f"- {k.title()}: {v['note']}" for k, v in T["treatment"].items()]
    return "\n".join(out) + "\n"


# --------------------------------------------------------------------------
# PDF
# --------------------------------------------------------------------------
def render_figures(d, fig_js: str, out_dir: Path) -> dict:
    """PNG of every example combatant's figure, for the PDF: {(battle, index): path}.
    Uses a headless browser (Playwright + Chromium) to draw templates/figure.js exactly as the
    roller does. Optional: without Playwright the PDF is built without figures."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("note: Playwright not installed, so the PDF has no combatant figures "
              "(pip install playwright && playwright install chromium)")
        return {}
    items = []
    for battle, c in d.conflicts.items():
        for i, e in enumerate(c.get("examples") or []):
            items.append({"key": [battle, i], "kit": d.armor["kits"][e["kit"]], "weapon": d.weapons[e["weapon"]],
                          "conflict": {"sides": c.get("sides") or []}, "ex": e})
    maps = load_maps(d)
    out_dir.mkdir(parents=True, exist_ok=True)
    page_html = ("<!doctype html><meta charset='utf-8'><body style='margin:0;background:transparent;"
                 "--map-sea:#d5e1e6;--map-land:#cfc6ab;--map-coast:#8c8670;--map-hl:#b5a47a;--map-dot:#8e1b2c'>"
                 f"<script>{fig_js}</script><div id='f'></div><script>const I = {json.dumps(items)};"
                 "document.getElementById('f').innerHTML = I.map((x, n) => `<div id='g${n}' style='display:inline-block;padding:2px'>`"
                 " + FIG.svg({kit: x.kit, weapon: x.weapon, look: FIG.lookFor(x.conflict, x.ex), size: 160}) + '</div>').join('')"
                 f" + Object.entries({json.dumps(maps)}).map(([b, m], n) => `<div id='m${{n}}' style='display:inline-block'>` + FIG.map(m, 240, b) + '</div>').join('');</script>")
    found = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch()
            page = browser.new_page(device_scale_factor=2)
            page.set_content(page_html)
            for n, x in enumerate(items):
                f = out_dir / f"fig{n:03d}.png"
                page.locator(f"#g{n}").screenshot(path=str(f), omit_background=True)
                found[tuple(x["key"])] = f
            for n, battle in enumerate(maps):
                f = out_dir / f"map{n:03d}.png"
                page.locator(f"#m{n}").screenshot(path=str(f), omit_background=True)
                found[("map", battle)] = f
            browser.close()
    except Exception as e:                      # no browser installed, sandbox, etc.
        print(f"note: could not draw combatant figures for the PDF ({e.__class__.__name__}); building without them")
        return {}
    return found


def pdf(d, path: Path, figs: dict | None = None) -> None:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import Image as RLImage
    from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
                                    PageBreak, KeepTogether)

    ink, rule, band, accent = colors.HexColor("#1f1b16"), colors.HexColor("#b9ad99"), \
        colors.HexColor("#f2ece1"), colors.HexColor("#7a2e1f")
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("H1", parent=ss["Title"], fontName="Times-Bold", fontSize=20, textColor=ink, alignment=0, spaceAfter=4)
    H2 = ParagraphStyle("H2", parent=ss["Heading2"], fontName="Times-Bold", fontSize=14, textColor=accent, spaceBefore=6, spaceAfter=4)
    B = ParagraphStyle("B", parent=ss["BodyText"], fontName="Times-Roman", fontSize=9.5, leading=12, textColor=ink)
    S = ParagraphStyle("S", parent=B, fontSize=7.8, leading=9.6)
    C = ParagraphStyle("C", parent=B, fontName="Helvetica", fontSize=7.2, leading=8.6)
    CH = ParagraphStyle("CH", parent=C, fontName="Helvetica-Bold")

    def grid(data, widths, header_rows=1, zebra=True, font=8.5, row_h=None):
        t = Table(data, colWidths=widths, repeatRows=header_rows, rowHeights=row_h, hAlign="LEFT")
        st = [("FONT", (0, 0), (-1, -1), "Helvetica", font),
              ("FONT", (0, 0), (-1, header_rows - 1), "Helvetica-Bold", font),
              ("TEXTCOLOR", (0, 0), (-1, -1), ink),
              ("LINEBELOW", (0, header_rows - 1), (-1, header_rows - 1), 1, ink),
              ("LINEBELOW", (0, header_rows), (-1, -1), 0.25, rule),
              ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
              ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2)]
        if zebra:
            for i in range(header_rows, len(data)):
                if (i - header_rows) % 2:
                    st.append(("BACKGROUND", (0, i), (-1, i), band))
        t.setStyle(TableStyle(st))
        return t

    def footer(canv, doc):
        canv.saveState()
        canv.setFont("Helvetica", 7)
        canv.setFillColor(colors.HexColor("#6b6255"))
        canv.drawString(0.6 * inch, 0.45 * inch, "Hit Location & Wound Tables - generated from data/; weights marked 'fitted' are placeholders")
        canv.drawRightString(letter[0] - 0.6 * inch, 0.45 * inch, f"{doc.page}")
        canv.restoreState()

    doc = SimpleDocTemplate(str(path), pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch,
                            topMargin=0.6 * inch, bottomMargin=0.7 * inch,
                            title="Hit Location & Wound Tables", author="Grave Wounds")
    W = letter[0] - 1.2 * inch
    story = [Paragraph("Hit Location &amp; Wound Tables", H1),
             Paragraph("Historically weighted d100 hit locations with system-agnostic wound effects. Roll d100; 00 = 100.", B),
             Spacer(1, 8),
             Paragraph("<b>Procedure</b>", H2)]
    for i, step in enumerate([
        "Roll d100 on the <b>location table</b> for the fight, in the column for the attacking weapon. "
        "If a <b>situation</b> applies (shield side, target down, fleeing...), use that column on the weapon's situation page instead.",
        "<b>Called shot:</b> " + CALLED_RULE,
        "Roll d100 on the <b>mechanism table</b> for the weapon: cut, pierce or crush.",
        "Set <b>severity</b> from your own system's damage (see guide), or roll d100 on the severity table "
        "(ballistic hits use their own table, by hit zone).",
        "<b>Armour</b> (adjusted tables only): lower the severity by the armour's steps; see the Armour pages.",
        "Find the wound on the <b>wound effects</b> page for that mechanism: location row, severity column.",
        "Track it: Bleed drains Blood, Pain stacks as a penalty, the Lethal timer runs until treated."], 1):
        story.append(Paragraph(f"{i}. {step}", B))
    story += [Spacer(1, 6), Paragraph("<b>Evidence vs adjusted tables</b>", H2),
              Paragraph("<b>Evidence</b> tables show where blows marked bone, so armour and soft-tissue blind spots are already baked in: "
                        "don't subtract armour again. <b>Adjusted</b> tables show where blows land; resolve armour separately by the location's armour slot.", B),
              Spacer(1, 6), Paragraph("<b>Confidence</b>", H2)]
    story += [Paragraph(f"<b>{k.title()}</b> - {v.split(' - ')[1]}", B) for k, v in CONF_LABEL.items()]

    # Location tables, each conflict preceded by its history
    prev_battle = None
    for tid, t in d.tables.items():
        if t.get("battle") != prev_battle:
            prev_battle = t.get("battle")
            c = d.conflicts.get(prev_battle)
            if c:
                mapimg = (figs or {}).get(("map", prev_battle))
                head = Paragraph(f"{prev_battle}", H1)
                if mapimg:
                    npan = len(load_maps(d)[prev_battle]["panels"])
                    mw = 1.2 * inch * npan + 0.06 * inch * (npan - 1)
                    head = Table([[head, RLImage(str(mapimg), width=mw, height=0.9 * inch)]], colWidths=[W - mw - 0.1 * inch, mw + 0.1 * inch],
                                 style=TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("LEFTPADDING", (0, 0), (-1, -1), 0)]))
                story += [PageBreak(), head,
                          *([Paragraph(f"<i>{c['period']}</i>", B)] if c.get("period") else []), Spacer(1, 4),
                          Paragraph(" ".join(c["summary"].split()), B), Spacer(1, 8)]
                if c.get("sides"):
                    rows = [[Paragraph(x, CH) for x in ["Side", "Who fought", "How they used armour"]]]
                    rows += [[Paragraph(f"<b>{x['name']}</b>", C), Paragraph(x["who"], C), Paragraph(x["armour"], C)] for x in c["sides"]]
                    story += [Paragraph("Sides and armour", H2), grid(rows, [1.3 * inch, 2.2 * inch, W - 3.5 * inch]), Spacer(1, 8)]
                if c.get("examples"):
                    figs = figs or {}
                    fig = lambda i: (RLImage(str(figs[(prev_battle, i)]), width=0.32 * inch, height=0.64 * inch)
                                     if (prev_battle, i) in figs else "")
                    rows = [[Paragraph(x, CH) for x in ["", "Example", "Side", "Wears (armour kit)", "Fights with", "Notes"]]]
                    name = lambda e: (f"<b>{htmllib.escape(e['name'])}</b>" if not e.get("image") else
                                      f"<link href=\"{htmllib.escape(commons_url(e['image']['file']))}\" color=\"#8e1b2c\">"
                                      f"<b>{htmllib.escape(e['name'])}</b><br/><font size=\"6.5\">(picture)</font></link>")
                    rows += [[fig(i), Paragraph(name(e), C), Paragraph(e["side"], C),
                              Paragraph(d.armor["kits"][e["kit"]]["name"], C), Paragraph(d.weapons[e["weapon"]]["name"], C),
                              Paragraph(e.get("notes", ""), C)] for i, e in enumerate(c["examples"])]
                    story += [Paragraph("Example combatants", H2),
                              Paragraph("The kit is what they wear when hit (use it on a table that allows armour); "
                                        "the weapon is what they fight with. 'Picture' links to a period image of such a "
                                        "combatant on Wikimedia Commons.", S), Spacer(1, 3),
                              grid(rows, [0.45 * inch, 1.3 * inch, 1.0 * inch, 1.7 * inch, 1.3 * inch, W - 5.75 * inch]), Spacer(1, 6)]
                cmp_ = c.get("comparison")
                if cmp_:
                    rows = [[Paragraph(x, CH) for x in ["", *cmp_["columns"]]]] + [[Paragraph(f"<b>{r[0]}</b>", C)] + r[1:] for r in cmp_["rows"]]
                    n = len(cmp_["columns"])
                    story += [Paragraph(cmp_["title"], H2), grid(rows, [1.8 * inch] + [(W - 1.8 * inch) / n] * n, font=8.2),
                              Spacer(1, 4), Paragraph(" ".join(cmp_["note"].split()), S), Spacer(1, 2),
                              Paragraph(f"<b>Source.</b> {cmp_['source']}", S), Spacer(1, 6)]
                if c.get("sources"):
                    story += [Paragraph("<b>Sources.</b> " + " ".join(c["sources"]), S)]
        ws = own_weapons(d, tid)
        cols = {w: {r["id"]: r for r in table_ranges(d, tid, w)} for w in ws}
        head = [Paragraph("Location", CH), Paragraph("Zone", CH)] + [Paragraph(wshort(d, w), CH) for w in ws]
        rows = [head]
        for loc in d.locations:
            cells = [rng(cols[w][loc["id"]]["lo"], cols[w][loc["id"]]["hi"]) if loc["id"] in cols[w] else "-" for w in ws]
            if any(c != "-" for c in cells):
                rows.append([loc["name"], loc["zone"]] + cells)
        nw = len(ws)
        lw = 1.75 if nw <= 5 else 1.3
        widths = [lw * inch, 0.5 * inch] + [(W - (lw + 0.5) * inch) / nw] * nw
        cc = close_combat_note(d, tid)
        bias = {"raw": "", "pooled": " Weapons share the source's pooled odds (no weapon mix to separate them).",
                "recentred": " Weapon columns differ, but across the weapon mix below they average back to the source totals.",
                "sourced": " Each weapon column is that weapon's own recorded wounds from the source."}[t["weapon_bias"]]
        story += [PageBreak(), Paragraph(t["name"], H1),
                  Paragraph(f"<i>{t.get('context','')}</i>", B),
                  Paragraph(f"Confidence: <b>{CONF_LABEL[t['confidence']]}</b>. Armour: <b>"
                            + ("allowed" if t["armor"] == "allowed" else "already reflected, do not apply") + "</b>." + bias, B),
                  Spacer(1, 6),
                  grid(rows, widths, font=8.2 if nw > 5 else 8.6), Spacer(1, 8),
                  *( [Paragraph(f"<b>Close combat.</b> {cc}", S), Spacer(1, 3)] if cc else [] ),
                  *( [Paragraph(f"<b>Source totals.</b> {regions_text(t)}. {t.get('confidence_note','')}", S), Spacer(1, 3)]
                     if t.get("regions") else [] ),
                  *( [KeepTogether([Paragraph("What hit them? (d100)", H2),
                      grid([["d100", "Cause"]] + [[rng(r["lo"], r["hi"]), r["label"]] for r in weapon_mix_ranges(d, tid)],
                           [0.7 * inch, 2.6 * inch], font=8),
                      Paragraph(t.get("weapon_mix_source", ""), S), Spacer(1, 6)])]
                     if t.get("weapon_mix") else [] ),
                  Paragraph(f"<b>Reading it.</b> {t.get('armor_note','').strip()}", S), Spacer(1, 3),
                  Paragraph(f"<b>Status.</b> {t.get('status','').strip()}", S), Spacer(1, 3),
                  Paragraph("<b>Sources.</b> " + " | ".join(t.get("sources", [])), S)]

    # Situations
    srows_ = [[Paragraph(x, CH) for x in ["Situation", "Column", "Effect on weights", "Notes"]]]
    for m in d.modifiers.values():
        srows_.append([Paragraph(f"<b>{m['name']}</b>" + (f"<br/><i>group: {m['group']}</i>" if m.get("group") else ""), C),
                       Paragraph(m.get("short", ""), C), Paragraph(mod_effect(d, m), C),
                       Paragraph(m["desc"] + (" " + m["notes"] if m.get("notes") else ""), C)])
    story += [PageBreak(), Paragraph("Situations", H1),
              Paragraph("Each situation reshapes where blows land. The roller and CLI stack any number of them "
                        "(one per group: facing, height, posture, cover). On paper, each column shows one situation alone. "
                        "Each table offers only the situations that make sense for it.", B),
              Spacer(1, 6), grid(srows_, [1.7 * inch, 0.75 * inch, 2.2 * inch, W - 4.65 * inch]),
              Spacer(1, 8), Paragraph(f"<b>Called shot.</b> {CALLED_RULE}", B)]
    for tid, t in d.tables.items():
        groups = weapon_groups(d, tid)
        for group in (groups if t["native"] != "gunfire" else groups[:1]):
            wid = group[0]
            cols = situation_cols(d, tid, wid)
            rows = [[Paragraph("Location", CH)] + [Paragraph(c, CH) for c, _ in cols]]
            for loc in d.locations:
                cells = [rng(c[loc["id"]]["lo"], c[loc["id"]]["hi"]) if loc["id"] in c else "-" for _, c in cols]
                if any(x != "-" for x in cells):
                    rows.append([loc["name"]] + cells)
            n = len(cols)
            more = (" Other weapons on this table: use the roller or CLI." if t["native"] == "gunfire" and len(groups) > 1 else "")
            story += [PageBreak(), Paragraph(f"{t['name']}: {' / '.join(wshort(d, w) for w in group)}", H2),
                      Paragraph("By situation. Roll d100 in the column that fits; 00 = 100." + more, S), Spacer(1, 4),
                      grid(rows, [1.3 * inch] + [(W - 1.3 * inch) / n] * n, font=7.6)]

    # Mechanism & severity
    mrows = [[Paragraph(x, CH) for x in ["Weapon"] + [m.title() for m in MECHANISMS] + ["Threat", "Notes"]]]
    for wid, w in d.weapons.items():
        mr = {r["id"]: r for r in mechanism_ranges(d, wid)}
        mrows.append([Paragraph(w["name"], C)] + [rng(mr[m]["lo"], mr[m]["hi"]) if m in mr else "-" for m in MECHANISMS]
                     + [Paragraph(w.get("threat") or ("melee" if w.get("melee") else "-"), C), Paragraph(w.get("notes", ""), C)])
    srows = [["d100", "Severity", "Use when"]] + [[rng(*t["d100"]), t["name"], Paragraph(t["guide"], C)]
                                                 for t in d.wounds["severity"]["tiers"]]
    story += [PageBreak(), Paragraph("Wound Mechanism", H1),
              grid(mrows, [1.5 * inch] + [0.5 * inch] * len(MECHANISMS) + [0.55 * inch, W - 2.05 * inch - 0.5 * inch * len(MECHANISMS)], font=7.4), Spacer(1, 6)]
    story += [Paragraph(f"<b>{v['name']}</b> - {v['desc']}", B) for v in d.wounds["mechanisms"].values()]
    story += [Spacer(1, 10), Paragraph("Severity", H1),
              grid(srows, [0.6 * inch, 0.8 * inch, W - 1.4 * inch])]
    for mech, spec in (d.wounds["severity"].get("by_mechanism") or {}).items():
        brows = [["Hit zone", "Light", "Serious", "Critical"]]
        for tbl in spec["tables"]:
            tr = {t["id"]: rng(*t["d100"]) for t in tbl["tiers"]}
            brows.append([", ".join(tbl["zones"]), tr["light"], tr["serious"], tr["critical"]])
        story += [Spacer(1, 8), Paragraph(f"Severity for {d.wounds['mechanisms'][mech]['name'].lower()} hits", H2),
                  Paragraph("Use instead of the table above. " + spec.get("note", "").strip(), S), Spacer(1, 4),
                  grid(brows, [1.6 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch])]

    # Fighting while wounded
    CB, TR = d.wounds["combat"], d.wounds["tracking"]
    prow = [[Paragraph(x, CH) for x in ["Cause", "Attack", "Defence", "Also"]]]
    prow.append([Paragraph(f"Pain (per step, max {TR['pain_cap']} steps)", C), f"-{CB['pain_step']}%", f"-{CB['pain_step']}%", ""])
    for th in sorted(TR["thresholds"], key=lambda t: -t["at"]):
        extra = "incapacitated" if th.get("incapacitated") else ("on the ground" if th.get("down") else "")
        prow.append([Paragraph(f"Blood at {int(th['at'] * 100)}% or less", C), f"-{th.get('penalty', 0)}%" if th.get("penalty") else "-",
                     f"-{th.get('penalty', 0)}%" if th.get("penalty") else "-", extra])
    FLAGS = {"down": "on the ground", "off_hand": "fights off-hand", "no_shield": "no shield", "incapacitated": "incapacitated"}
    for imp, irule in CB["impair"].items():
        parts = [(f"{imp.replace('_', ' ')} ({arm.replace('_', ' ')})", irule[arm]) for arm in ("weapon_arm", "shield_arm") if arm in irule] \
            if ("weapon_arm" in irule or "shield_arm" in irule) else [(imp.replace("_", " "), irule)]
        for label, eff in parts:
            if not eff:
                continue
            prow.append([Paragraph(label, C), f"-{eff['attack']}%" if eff.get("attack") else "-",
                         f"-{eff['defence']}%" if eff.get("defence") else "-",
                         Paragraph(", ".join(v for k, v in FLAGS.items() if eff.get(k)), C)])
    mb = CB["margin_bands"]
    brow = [["Weapon / hit zone", "Light", "Serious", "Critical"],
            ["Default", f"margin 0-{mb['default']['serious'] - 1}", f"{mb['default']['serious']}-{mb['default']['critical'] - 1}", f"{mb['default']['critical']}+ or critical roll"]]
    for b in mb.get("ballistic", []):
        brow.append([f"Firearm or explosive: {', '.join(b['zones'])}", f"margin 0-{b['serious'] - 1}", f"{b['serious']}-{b['critical'] - 1}", f"{b['critical']}+ or critical roll"])
    auto = CB["auto_situations"]
    story += [PageBreak(), Paragraph("Fighting While Wounded", H1),
              Paragraph("Optional: resolve the attack here so that wounds count. Skip this page if your own system rolls the attack; "
                        "you can still use the penalty table for it.", B), Spacer(1, 4)]
    story += [Paragraph(f"{i}. {x}", B) for i, x in enumerate(COMBAT_STEPS, 1)]
    story += [Spacer(1, 6), Paragraph(f"Wound penalties (add up, each total capped at -{CB['cap']}%)", H2),
              Paragraph("Arm wounds count against the <b>weapon arm</b> (the side of the fighter's weapon hand, usually right) or the "
                        "<b>shield arm</b>. Wounds elsewhere that impair an arm count against the weapon arm. "
                        "Each impairment counts once however many wounds cause it. A fighter with neither hand usable cannot wield a weapon.", S),
              Spacer(1, 3), grid(prow, [2.3 * inch, 0.8 * inch, 0.8 * inch, W - 3.9 * inch], font=8), Spacer(1, 8),
              Paragraph("Severity from the margin of success", H2), grid(brow, [2.6 * inch] + [(W - 2.6 * inch) / 3] * 3, font=8),
              Spacer(1, 4),
              Paragraph(f"Automatic situations: defender cannot stand = {d.modifiers[auto['defender_down']]['name']}; "
                        f"defender's shield arm useless = {d.modifiers[auto['defender_no_shield']]['name']}; "
                        f"attacker on the ground = {d.modifiers[auto['attacker_down']]['name']} (where the table offers them).", S),
              Spacer(1, 8), KeepTogether([Paragraph("Graze, stop check and team morale", H2)] + [Paragraph(x, S) for x in stop_rules(d)])]
    rrows = [[Paragraph(x, CH) for x in ["Weapon", "Reach or range (short / medium / long)"]]] + [[Paragraph(a, C), b] for a, b in reach_rows(d)]
    story += [PageBreak(), Paragraph("Battle Map", H1)] + [Paragraph(x, B) for x in move_rules(d)] + [
              Spacer(1, 6), Paragraph("Weapon reach and range", H2),
              Paragraph("Ranges are design estimates from each weapon's effective range in its period.", S), Spacer(1, 3),
              grid(rrows, [2.9 * inch, W - 2.9 * inch], font=7.5)]
    if d.works.get("camps"):
        crow = [[Paragraph(x, CH) for x in ["Camp", "What it is", "Needs", "12 men", "100 men", "1,000 men"]]] + [[Paragraph(r[0], C), Paragraph(r[1], C)] + r[2:] for r in camp_rows(d)]
        wrow = [[Paragraph(x, CH) for x in ["Work", "Lies on", "Labour", "Crossing", "Cover", "Close combat", "Breach"]]] + [[Paragraph(x, C) for x in r] for r in works_rows(d)]
        story += [PageBreak(), Paragraph("Camps and Works", H1)] + [Paragraph(x, B) for x in works_rules(d)] + [
                  Spacer(1, 6), Paragraph("Camps (hours to make, on foot, timber hauled)", H2), Spacer(1, 3),
                  grid(crow, [1.1 * inch, W - 4.6 * inch, 0.9 * inch, 0.85 * inch, 0.85 * inch, 0.9 * inch], font=7.5), Spacer(1, 8),
                  Paragraph("Medieval works", H2), Spacer(1, 3),
                  grid(wrow, [0.9 * inch, 0.55 * inch, 1.2 * inch, 0.95 * inch, 1.0 * inch, W - 5.6 * inch, 1.0 * inch], font=7.5)]
    if d.weather:
        wt = weather_tables(d)
        hdr = lambda rows: [[Paragraph(x, CH) for x in rows[0]]] + rows[1:]
        story += [PageBreak(), Paragraph("Weather", H1)] + [Paragraph(x, B) for x in weather_rules(d)] + [
            Spacer(1, 6), Paragraph("Conditions", H2), grid(hdr(wt["conds"]), [1.3 * inch, 1.3 * inch, 1.2 * inch, 1.1 * inch, W - 4.9 * inch], font=8),
            Spacer(1, 6), KeepTogether([Paragraph("Misfires in the wet", H2), grid(hdr(wt["misfire"]), [1.5 * inch] + [1.0 * inch] * 3, font=8)]),
            Spacer(1, 6), KeepTogether([Paragraph("Fatigue", H2), grid(hdr(wt["fatigue"]), [1.5 * inch, 1.6 * inch, 1.6 * inch], font=8)]),
            Spacer(1, 6), KeepTogether([Paragraph("Mud and snow on the march (time x)", H2), grid(hdr(wt["ground"]), [1.6 * inch, 0.9 * inch, 0.9 * inch], font=8)]),
            Spacer(1, 6), KeepTogether([Paragraph("Climates (modern normals, °F with °C below, and days with rain or snow)", H2),
                                        grid(hdr([wt["climates"][0]] + [[Paragraph(r[0], C)] + r[1:] for r in wt["climates"][1:]]),
                                             [1.6 * inch, 0.6 * inch] + [(W - 2.2 * inch) / 12] * 12, font=6.5)])]
    if d.units:
        qrow = [[Paragraph(x, CH) for x in ["Quality", "Attack", "Defence", "Nerve"]]] + unit_rows(d)
        rrow = [[Paragraph(x, CH) for x in ["Missile weapon", "Shots a minute"]]] + [[d.weapons[w]["name"], str(n)] for w, n in d.units["missile"]["rate"].items()]
        story += [PageBreak(), Paragraph("Unit combat", H1)] + [Paragraph(x, B) for x in unit_rules(d)] + [
            Spacer(1, 6), KeepTogether([Paragraph("Unit quality", H2), grid(qrow, [1.4 * inch, 1.0 * inch, 1.0 * inch, 1.0 * inch], font=8)]),
            Spacer(1, 6), KeepTogether([Paragraph("Missile rates", H2), grid(rrow, [2.4 * inch, 1.2 * inch], font=8)])]
    if d.disease:
        drow = [[Paragraph(x, CH) for x in ["Disease", "Caught from", "Shows after", "Outbreak chance a week", "Peak (d100)", "Deaths per case"]]]
        drow += [[Paragraph(c, C) for c in r] for r in disease_rows(d)]
        story += [PageBreak(), Paragraph("Camp disease", H1)] + [Paragraph(x, B) for x in disease_rules(d)] + [
            Spacer(1, 6), grid(drow, [1.1 * inch, 1.5 * inch, 0.75 * inch, W - 5.75 * inch, 1.3 * inch, 1.1 * inch], font=7.5)]
    if d.terrain["terrain"]:
        ft = d.terrain["forces"]
        trow = [[Paragraph(x, CH) for x in ["Terrain", "Time"] + [f"{f['name']}<br/>mi (km) a day" for f in ft.values()]]] + travel_rows(d)
        story += [PageBreak(), Paragraph("Travel", H1)] + [Paragraph(x, B) for x in travel_rules(d)] + [
                  Spacer(1, 6), Paragraph("Terrain", H2),
                  Paragraph("Km a day across whole hexes of each terrain; a road day is the type's speed times its marching hours.", S), Spacer(1, 3),
                  grid(trow, [1.8 * inch, 0.9 * inch] + [(W - 2.7 * inch) / len(ft)] * len(ft), font=8)]

    # Armour
    mcols = [m for m in MECHANISMS if m != "ballistic"]
    matrows = [[Paragraph(x, CH) for x in ["Material"] + [f"vs {m.title()}" for m in mcols]
                + [f"Gunfire: {t.replace('_', ' ')}" for t in THREATS]]] + [
        [Paragraph(mat["name"], C)] + [str(mat[m]) for m in mcols]
        + [str((mat.get("threats") or {}).get(t, mat["ballistic"])) for t in THREATS] for mat in d.armor["materials"].values()]
    defeat = [["Weapon", "Armour defeat"]] + [
        [w["name"], ", ".join(f"ignores {v} step vs {k}" for k, v in w["armor_defeat"].items())]
        for w in d.weapons.values() if w.get("armor_defeat")]
    story += [PageBreak(), Paragraph("Armour", H1)]
    story += [Paragraph(f"{i}. {x}", B) for i, x in enumerate(ARMOR_STEPS, 1)]
    story += [Spacer(1, 8), Paragraph("Protection (severity steps)", H2),
              grid(matrows, [2.2 * inch] + [(W - 2.2 * inch) / (len(mcols) + len(THREATS))] * (len(mcols) + len(THREATS)), font=8), Spacer(1, 8),
              grid(defeat, [2.4 * inch, W - 2.4 * inch]), Spacer(1, 6),
              Paragraph("<b>Sources.</b> " + " ".join(d.armor.get("sources", [])), S)]
    for group, title in KIT_GROUPS:
        g = kit_grid(d, group)
        rows = [[Paragraph(x, CH) for x in g[0]]] + [[Paragraph(x, C) for x in r] for r in g[1:]]
        n = len(g[0]) - 1
        notes = [f"<b>{k['name']}:</b> {k['notes']}" for k in d.armor["kits"].values()
                 if k.get("group") == group and k.get("notes")]
        story += [PageBreak(), Paragraph(title, H1),
                  grid(rows, [1.3 * inch] + [(W - 1.3 * inch) / n] * n, font=7.4), Spacer(1, 4)]
        story += [Paragraph(x, S) for x in notes]

    # Wound effects, one page per mechanism
    for m in MECHANISMS:
        rows = [[Paragraph(x, CH) for x in ["Location", "Light", "Serious", "Critical", "Infection"]]]
        for cid in d.wounds["classes"]:
            rep = class_rep(d, cid)
            es = [compose_wound(d, rep, m, s) for s in SEVERITIES]
            rows.append([Paragraph(f"<b>{cid.replace('_',' ').title()}</b>", C)]
                        + [Paragraph(short_effect(d, e), C) for e in es] + [Paragraph(es[1]["infection"], C)])
        story += [PageBreak(), Paragraph(f"Wound Effects - {d.wounds['mechanisms'][m]['name']}", H1),
                  Paragraph(d.wounds["mechanisms"][m]["desc"] + " Left and right share a row. Effects are untreated.", B),
                  Spacer(1, 6),
                  grid(rows, [0.95 * inch, 1.35 * inch, 1.75 * inch,
                              W - 4.7 * inch, 0.65 * inch])]

    # Key & tracking
    V = d.wounds["vocabulary"]
    key = [["Term", "Meaning"]]
    key += [[f"B{k}", v] for k, v in V["bleed"].items()]
    key += [[f"P{k}", v] for k, v in V["pain"].items()]
    key += [[k.replace("_", " "), Paragraph(v, C)] for k, v in V["impair"].items()]
    key += [[FLAG_LABEL.get(k, k).capitalize(), Paragraph(v, C)] for k, v in V["flags"].items()]
    key += [[f"Lethal: {k}", Paragraph(V["lethal"][k], C)] for k in V["lethal"]["order"]]
    T = d.wounds["tracking"]
    trk = [["Blood", "Effect"]] + [[f"{int(th['at']*100)}%", th["effect"]] for th in T["thresholds"]]
    trt = [["Treatment", "Effect"]] + [[k.title(), Paragraph(v["note"], C)] for k, v in T["treatment"].items()]
    story += [PageBreak(), Paragraph("Key", H1), grid(key, [1.2 * inch, W - 1.2 * inch], font=8),
              Spacer(1, 10),
              KeepTogether([Paragraph("Survival Tracking (optional)", H1),
                            Paragraph(f"Each character has <b>{T['blood_pool']} Blood</b>. Bleed drains it; "
                                      f"total Pain above {T['pain_cap']} calls for a stop check each round.", B),
                            Spacer(1, 4), grid(trk, [0.8 * inch, W - 0.8 * inch], font=8), Spacer(1, 6),
                            grid(trt, [1.2 * inch, W - 1.2 * inch], font=8)])]
    doc.build(story, onFirstPage=footer, onLaterPages=footer)


# --------------------------------------------------------------------------
# Locator maps (data/maps.json, built by tools/maps/make_maps.mjs)
# --------------------------------------------------------------------------
_MAPS = None
_MAP_SEQ = 0


def load_maps(d) -> dict:
    """The conflict maps, checked against the `map:` entries they were built from."""
    global _MAPS
    if _MAPS is None:
        f = ROOT / "data" / "maps.json"
        maps = json.loads(f.read_text(encoding="utf-8")) if f.exists() else {}
        for battle, c in d.conflicts.items():
            spec = c.get("map")
            if spec and (battle not in maps or maps[battle].get("spec") != spec):
                print(f"warning: map for '{battle}' is missing or out of date; run: cd tools/maps && npm ci && node make_maps.mjs")
        _MAPS = {b: m for b, m in maps.items() if b in d.conflicts and d.conflicts[b].get("map")}
    return _MAPS


def map_svg(m, height: int = 48, title: str = "", width: int = 0) -> str:
    """Same drawing as FIG.map in templates/figure.js (for the static start page).
    Panels sit side by side at the given height; with a width instead, they stack
    vertically at that width (the start page's narrow icon column)."""
    if not m:
        return ""
    esc = htmllib.escape
    n, w, h, gap = len(m["panels"]), m["w"], m["h"], m["gap"]
    stack = bool(width)
    total = n * w + (n - 1) * gap
    tall = n * h + (n - 1) * gap
    dot_name = lambda x: ", ".join(x["names"]) + (" (no records used)" if x.get("context") else "")
    names = " | ".join((p["label"] + ": " if p.get("label") else "") + "; ".join(dot_name(x) for x in p["dots"]) for p in m["panels"])
    global _MAP_SEQ
    _MAP_SEQ += 1
    parts = []
    for i, p in enumerate(m["panels"]):
        dots = "".join(
            f'<circle cx="{x["x"]}" cy="{x["y"]}" r="{4.2 if len(x["names"]) > 1 else 3.4}" '
            + (f'fill="var(--map-sea)" stroke="var(--map-dot)" stroke-width="1.6"' if x.get("context")
               else f'fill="var(--map-dot)" stroke="var(--map-sea)" stroke-width="1.2"')
            + f'><title>{esc(dot_name(x))}</title></circle>' for x in p["dots"])
        parts.append(
            f'<g transform="translate({0 if stack else i * (w + gap)} {i * (h + gap) if stack else 0})"><title>{esc(p.get("label") or title)}</title>'
            f'<clipPath id="pm{_MAP_SEQ}-{i}"><rect width="{w}" height="{h}" rx="7"/></clipPath><g clip-path="url(#pm{_MAP_SEQ}-{i})">'
            f'<rect width="{w}" height="{h}" fill="var(--map-sea)"/>'
            f'<path d="{p["land"]}" fill="var(--map-land)" stroke="var(--map-coast)" stroke-width=".5" stroke-linejoin="round"/>'
            + (f'<path d="{p["lakes"]}" fill="var(--map-sea)" stroke="var(--map-coast)" stroke-width=".35"/>' if p.get("lakes") else "")
            + (f'<path d="{p["highlight"]}" fill="var(--map-hl)" stroke="var(--map-coast)" stroke-width=".5"/>' if p.get("highlight") else "")
            + (f'<path d="{p["borders"]}" fill="none" stroke="var(--map-coast)" stroke-width=".45" stroke-dasharray="1.6 1.2" opacity=".8"/>' if p.get("borders") else "")
            + '</g>' + dots + f'<rect x=".5" y=".5" width="{w - 1}" height="{h - 1}" rx="7" fill="none" stroke="var(--map-coast)" stroke-width="1"/></g>')
    vb, size = ((f"0 0 {w} {tall}", f'width="{width}" height="{round(width * tall / w)}"') if stack
                else (f"0 0 {total} {h}", f'width="{round(height * total / h)}" height="{height}"'))
    return (f'<svg viewBox="{vb}" {size} role="img" '
            f'aria-label="{esc(title)}: {esc(names)}"><title>{esc(title)}: {esc(names)}</title>' + "".join(parts) + '</svg>')


# --------------------------------------------------------------------------
# Start page (GitHub Pages serves index.html from the repository root)
# --------------------------------------------------------------------------
REPO_URL = "https://github.com/swares/grave-wounds"


def index_page(d) -> str:
    esc = htmllib.escape
    groups = {}
    for t in d.tables.values():                       # tables are already in display order
        groups.setdefault(t.get("battle", "Other"), []).append(t)
    items = []
    for battle, ts in groups.items():
        period = (d.conflicts.get(battle) or {}).get("period", "")
        n = len(ts)
        labels = " · ".join(esc(t.get("label", t["name"])) for t in ts)
        mp = load_maps(d).get(battle)
        items.append(
            f'      <li><span class="map">{map_svg(mp, title=battle, width=56) if mp else ""}</span><span class="name">{esc(battle)}</span>'
            f'<span class="period">{esc(str(period))}</span>'
            f'<span class="tables">{n} table{"s" if n != 1 else ""}: {labels}</span></li>')
    kits = [k for k in d.armor["kits"] if k != "none"]
    fill = {
        "TABLES": len(d.tables), "WARS": len(groups), "WEAPONS": len(d.weapons), "KITS": len(kits),
        "LOCS": len(d.locations), "WAR_LIST": "\n".join(items),
        "GENERATED": date.today().isoformat(), "REPO": REPO_URL,
    }
    out = (ROOT / "templates" / "index.html").read_text(encoding="utf-8")
    for k, v in fill.items():
        out = out.replace("{{" + k + "}}", str(v))
    leftover = re.findall(r"\{\{[A-Z_]+\}\}", out)
    if leftover:
        raise ValueError(f"templates/index.html: unfilled placeholders {leftover}")
    return out


# --------------------------------------------------------------------------
def main() -> int:
    try:
        d = load(ROOT / "data")
    except DataError as e:
        print("Data errors:\n" + str(e), file=sys.stderr)
        return 1
    for w in d.warnings:
        print("warning:", w)
    DIST.mkdir(exist_ok=True)
    b = bundle(d)
    (DIST / "gravewounds-data.json").write_text(json.dumps(b, indent=1), encoding="utf-8")
    (DIST / "tables.md").write_text(markdown(d), encoding="utf-8")
    fig_js = (ROOT / "templates" / "figure.js").read_text(encoding="utf-8")
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        pdf(d, DIST / "tables.pdf", render_figures(d, fig_js, Path(tmp)))
    tpl = (ROOT / "templates" / "roller.html").read_text(encoding="utf-8")
    from gravewounds.model import FIG_NAMES
    missing = [f"{k}:{n}" for k, names in FIG_NAMES.items() for n in names
               if not re.search(r"\b" + re.escape(n) + r"\s*:", fig_js)]
    if missing:
        print("templates/figure.js lacks drawings named in gravewounds/model.py FIG_NAMES: " + ", ".join(missing), file=sys.stderr)
        return 1
    html = tpl.replace("/*__FIGURE_JS__*/", fig_js.replace("</script>", "<\\/script>"))
    camp_js = (ROOT / "templates" / "camp.js").read_text(encoding="utf-8")
    works_js = (ROOT / "templates" / "works.js").read_text(encoding="utf-8")
    measure_js = (ROOT / "templates" / "measure.js").read_text(encoding="utf-8")
    html = html.replace(CAMP_MARK, camp_js).replace("/*__WORKS_JS__*/", works_js).replace(MEASURE_MARK, measure_js)
    html = html.replace("/*__GRAVEWOUNDS_DATA__*/null", json.dumps(b, separators=(",", ":")))
    (DIST / "roller.html").write_text(html, encoding="utf-8")
    tb = travel_bundle(d)
    ttpl = (ROOT / "templates" / "travel.html").read_text(encoding="utf-8")
    thtml = ttpl.replace(CAMP_MARK, camp_js).replace(MEASURE_MARK, measure_js).replace("/*__TRAVEL_DATA__*/null", json.dumps(tb, separators=(",", ":")))
    (DIST / "travel.html").write_text(thtml, encoding="utf-8")
    units_js = (ROOT / "templates" / "units.js").read_text(encoding="utf-8")
    ftpl = (ROOT / "templates" / "field.html").read_text(encoding="utf-8")
    fhtml = ftpl.replace("/*__WORKS_JS__*/", works_js).replace(CAMP_MARK, camp_js).replace(MEASURE_MARK, measure_js).replace("/*__UNITS_JS__*/", units_js).replace("/*__FIELD_DATA__*/null", json.dumps(field_bundle(d), separators=(",", ":")))
    (DIST / "field.html").write_text(fhtml, encoding="utf-8")
    (ROOT / "index.html").write_text(index_page(d), encoding="utf-8")
    print("Built:", ", ".join(p.name for p in sorted(DIST.iterdir())), "+ index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
