"""Build every output from the data folder.

    python build.py            -> dist/tables.pdf, dist/tables.md,
                                  dist/gravewounds-data.json, dist/roller.html, dist/travel.html,
                                  dist/field.html, dist/team.html, dist/rules.html (the rule book),
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
from gravewounds.model import MECHANISMS, SEVERITIES, THREATS, available_weapons, commons_url, resolve_table, slot_layers, periods

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
    "Attacker rolls d100 against <b>attack % minus penalties</b> (on the battle map, also minus any range penalty and men in the way). Equal or under hits; the <b>margin</b> is the effective chance minus the roll. "
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
        _characteristics_rule(d),
    ]


def _characteristics_rule(d) -> str:
    C, T = d.wounds["combat"]["characteristics"], d.wounds["tracking"]
    b = C["toil"]["blows"]
    return (f"<b>Characteristics:</b> a team-builder character's sheet counts in the fight (anyone else counts 50 in each). "
            f"Initiative: d{C['initiative']['die']} + Agility / {C['initiative']['agi_per']}. Blood: {T['blood_pool']} + (Endurance - 50) / {C['blood']['per']}. "
            f"Toil: each hand-to-hand exchange he attacks or defends in counts, and every {b['light']} (light kit), {b['medium']} (medium) or {b['heavy']} (heavy), "
            f"times Strength / 50, he is a fatigue step worse, to {d.weather['fatigue']['levels'][C['toil']['worst']]['name'].lower()} at most. "
            f"A leader who is up adds (Presence - 50) / {C['presence']['per']} to his side's morale. Rounded down throughout. "
            f"First aid: on a side with any team-builder character, the best Leechcraft among those up rolls each treatment; success binds "
            f"{d.wounds['combat']['first_aid']['bind']} bleed steps and cauterises without more pain, failure does nothing.")


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
        f"the enemy strikes ({U['formations']['close']['abreast']} men a hex face in close order; a rank more for each hex of reach past the first: two for spears and bills, three for pikes). {M['tempo'] * 100:g}% of them make a telling attempt each exchange; "
        f"archers loose their rate a minute, {S['tempo'] * 100:g}% of the shots aimed at a man. Each attempt is an individual attack against the unit's attack %, "
        "parried on its defence % (not from flank or rear, nor against missiles), then location, severity from the margin, and armour, as for one fighter.",
        f"Light wounds and grazes fight on. Serious and critical wounds call for a stop check against the unit's Nerve; a failure is down. "
        f"From breech-loaders (the 1860s on) and shell a serious or critical wound is always down and a light one calls for the stop check. A wound fatal within rounds kills. "
        f"Flank +{M['flank']['attack']}, rear +{M['rear']['attack']}, a mounted charge +{M['charge']['attack']} at x{M['charge']['tempo']:g} tempo (none onto a steady front of pikes in close order, whose men strike horse at +{M['pikes']['attack']}), shaken {M['shaken']['attack']}. "
        f"Men in an intact bunker can't be fought hand to hand; it is stormed with grenades, satchel charges or flamethrowers "
        f"({', '.join(str(m['knock']) + '%' for m in U['assault']['means'].values())} an exchange to knock it out).",
        f"<b>Unit morale:</b> after an exchange a unit checks if it lost the exchange, has {int(mo['trigger'] * 100)}% of its men down, lost {int(mo['shock'] * 100)}% in the exchange, "
        f"or was struck in flank or rear: d100 against Nerve, +{mo['mods']['in_order']} while steady, +{mo['mods']['leader']} with a leader, {mo['mods']['leader_down']} if he is down, "
        f"{mo['mods']['heavy']} at half strength, {mo['mods']['flank']} if flanked, +{mo['mods']['dug_in']} dug in, -{mo['mods']['losing_per_man']} a man it lost more than it put down (at most -{mo['mods']['losing_cap']}). "
        f"Steady fails: shaken; shaken fails: broken. A broken unit flees: every enemy in reach strikes it at +{R['attack']}, no parry, x{R['tempo']:g} tempo. On the field map it runs on through its own side's units to clear ground (up to {R['through']} times its move); each it runs through moves {round(100 * (1 - R['jostle']))}% of its move that exchange.",
    ] + _ground_rules(d) + _gun_rules(d) + _mg_rules(d) + _hero_rules(d) + _commander_rules(d) + _aftermath_rules(d)


def _mg_rules(d) -> list[str]:
    U = d.units
    M, F, R = U.get("machine_guns"), U["formations"], U["missile"]["rate"]
    if not M:
        return []
    ext = F["extended"]
    return [
        f"<b>Modern infantry:</b> extended order is {ext['per_hex']} men a hex (shots at it x{ext['missile_factor']:g}, {ext['move']} hexes a move). "
        f"Magazine rifles fire {R['rifle_service']} rounds a minute, self-loading and assault rifles {R['rifle_assault']}, pistols and submachine guns {R['pistol_smg']}. "
        f"A unit can go to ground on its own move: shots at it -{U['to_ground']['cover']}%, and it cannot move until it gets up. "
        f"Digging in: out of contact, {U['dig_in']['exchanges']} exchanges neither moving nor firing, and it counts as gone to ground while it stays in its holes (it may move, leaving them). "
        f"Hidden men (gone to ground, in a bunker or in buildings): only {U['hidden']['seen']}% of the aimed shots at them find a man ({U['hidden']['mg_seen']}% of a machine gun's), "
        f"and dug in they get +{U['morale']['mods']['dug_in']} on morale.",
        f"<b>Machine guns:</b> a team is a gun and {M['crew']} crew a hex, the gun served while one of its crew is up. Each gun fires {R['machine_gun']} rounds a minute, "
        f"{M['tempo'] * 100:g}% of them rolled as aimed shots. Its beaten zone: the first other unit, friend or foe, within {M['beaten']['beyond']} hexes past the target on the line "
        f"of fire takes {M['beaten']['share']}% as many shots at that range (ground that stops shot stops it).",
    ] + _indirect_rules(d)


def _indirect_rules(d) -> list[str]:
    I, S = d.units.get("indirect"), d.units.get("suppression")
    if not I:
        return []
    def lands(k):
        if not k["delay"]:
            return "this exchange"
        return "next exchange" if k["delay"] == 1 else f"in {k['delay']} exchanges"
    kinds = "; ".join(f"{k['name'].lower()} {k['rate']} a minute {'an aircraft' if k.get('air') else 'a tube'}, lands {lands(k)}, scatter {k['scatter']}, "
                      f"struck % by distance {'/'.join(f'{x:g}' for x in k['struck'])}" for k in I["kinds"].values())
    return [
        f"<b>Indirect fire:</b> off-map batteries on call, on a hex one of the side's units can see (in the weather, no woods between). Each shell scatters "
        f"(d6 direction, 0 to scatter hexes); every man within the radius is struck at the % for his distance (x{I['prone']:g} gone to ground, less ground cover) "
        f"and wounds as a shell fragment at {I['attack']}%. {kinds}.",
        _support_rules(I),
    ] + _heliborne_rules(d) + _vehicle_rules(d) + [
        f"<b>Suppression:</b> a unit shelled or under machine-gun fire checks Nerve at the end of the exchange (+{S['prone']} gone to ground); a failure pins it "
        f"for the next exchange: no move, {S['fire'] * 100:g}% of its fire.",
    ]


def _support_rules(ind: dict) -> str:
    """Counter-battery, crews, displacing, smoke drift and fire plans, for the book."""
    I = ind
    CB, K = I["counter_battery"], I["kinds"]
    crews = ", ".join(f"{k['name'].lower()} {k['crew']} (fires with {k['serve']})" for k in K.values() if "crew" in k and not k.get("direct"))
    moves = ", ".join(f"{k['name'].lower()} {k['displace']}" for k in K.values() if k.get("displace"))
    drift = ", ".join(f"{w} {n}" for w, n in I["smoke"]["drift"].items())
    return (f"<b>Counter-battery and fire plans:</b> crews a tube: {crews}. A located battery can be fired on with no one seeing it: each shell lands among "
            f"the guns at the kind's counter %, knocking out a tube and striking {CB['among']} crewmen, or at {CB['near']} times that bursts close by, striking "
            f"{CB['near_struck']}; struck crewmen roll wounds and those put down are lost, and a tube without its men is silent. Displacing, a battery is silent "
            f"for its exchanges ({moves}) and then unlocated. Smoke drifts downwind each exchange, by hexes: {drift}. A creeping barrage keeps a fire plan: "
            f"1 to {I['creep']['max']} hexes a lift, 1 to {I['creep']['every_max']} exchanges on each line, a set number of lines, then up to eight more legs, each the same way or turned. "
            "A battery may be placed on the map: it then reaches only its range ("
            + ", ".join(f"{k['name'].lower()} {k['range']} hexes" for k in K.values() if k.get("range"))
            + "), counter-battery fire reaches it only from within range, an enemy within a hex of it overruns it, and displacing it moves it to a new place."
            + (" Illumination (one round a tube, called on any hex) lights the hexes round it, out to " + ", ".join(f"{k['illum']} ({k['name'].lower()})" for k in K.values() if k.get("illum"))
               + " hexes, for the light's exchanges after the one it is fired in." if any(k.get("illum") for k in K.values()) else "")
            + _air_rules(I))


def _vehicle_rules(d) -> list[str]:
    V = d.units.get("vehicles")
    if not V:
        return []
    kinds = "; ".join(f"{k['name'].lower()}: {k['crew']} crew, move {k['move']}, {k['armour']} armour" + (f", main gun to {k['gun']['range']} hexes, {k['gun']['rate']} a vehicle an exchange" if k.get("gun") else "")
                      + (f", carries {k['carry']} men a vehicle" if k.get("carry") else "") + (f", {k['rides']} men can ride on its hull" if k.get("rides") else "") + (f", tows {k['tows']} anti-tank gun" if k.get("tows") else "") for k in V["kinds"].values())
    arm = "; ".join(f"{name}: rocket {a['rpg']}%, guided missile {a['atgm']}%, gun {a['gun']}%, shell x{a['shell']:g}" for name, a in V["armour"].items())
    going = ", ".join(f"{d.units['ground'][g]['name'].lower()} {c}" for g, c in V["ground"].items())
    at = ", ".join(f"{d.weapons[w]['short']} {a['rate']:g} a man" for w, a in V["anti_armour"].items())
    asp, dm = V.get("aspect") or {}, V.get("damage") or {}
    S = V.get("small_arms") or {}
    soft = [n for n, a in V["armour"].items() if "small" in a]
    softly = (f" Soft-skinned vehicles ({', '.join(soft)}): small arms shoot at them too, {S.get('rate', 0):g} aimed shots a man ({S.get('mg', 0):g} a machine gunner) an exchange, "
              f"each hit knocking one out at {', '.join(str(V['armour'][n]['small']) for n in soft)}%, no lesser damage.") if soft else ""
    return [f"<b>Vehicles:</b> one a hex ({kinds}). Small arms cannot hurt armoured vehicles; no one fights them hand to hand.{softly} Anti-armour weapons fire "
            + at + f" an exchange, every round aimed; a hit knocks a vehicle out by its armour ({arm}), x{asp.get('flank', 1):g} into the flank and x{asp.get('rear', 1):g} into the rear. "
            f"A hit that does not knock it out strikes the turret at {dm['turret']}% (gun out {dm['turret_hit']['gun']}%, immobilised {dm['turret_hit']['immobilised']}%), "
            f"else the hull (immobilised {dm['hull_hit']['immobilised']}%, gun out {dm['hull_hit']['gun']}%); a unit cannot move until it abandons "
            "its immobilised vehicles (their crews leave unhurt). "
            f"A main gun hits a vehicle by range, or bursts on men as a tank's round on call; a shell or bomb in a vehicle's hex knocks it out at the kind's knock % times shell. "
            f"A knocked-out vehicle's crew are out of the fight, each struck at {V['crew_struck']}%. Carriers take a foot unit aboard from beside them and set it down beside them; "
            f"riders in a knocked-out carrier are each struck at {V['riders_struck']}%; a small-arms hit on a soft-skinned carrier (lorries) that does not knock it out strikes a rider, and small arms shoot at men riding on a tank's hull (rides), each hit striking one; shells near the tanks strike them as men in the open. Riders shoot from IFVs' firing ports ({V['rider_fire']['ports']:.0%} of them) and from tank hulls ({V['rider_fire']['hull']:.0%}); not from carriers or lorries. Going a hex: {going}; nothing else."] + _at_mine_rules(d)


def _at_mine_rules(d) -> list[str]:
    A, M = d.units.get("anti_tank_guns"), d.units.get("mines")
    out = []
    if A:
        g = A["gun"]
        out.append(f"<b>Anti-tank guns (1939-53):</b> a unit of towed guns, {A['crew']} men a gun, a gun a hex, manhandled {d.units['formations']['at_gun']['move']} hexes. "
                   f"Each gun served fires {g['rate']} round an exchange to {g['range']} hexes as a tank's main gun, vehicles first (hits {'/'.join(str(h[1]) for h in g['hit'])}% by range, "
                   f"knocking out by the armour's gun %), high explosive at men, {A['rounds']} rounds a gun (resupply as a battery). Gun tractors tow one gun each: hooked up the guns move with them and do not fire; unhooked, they fire from the next exchange. Its crews are men: small arms and shells strike them. "
                   "The enemy commander tows them forward and unhooks them in reach.")
    S = d.units.get("gun_shields")
    if S:
        names = ", ".join(d.weapons[w]["name"].split(" (")[0].lower() + "s" for w in S["weapons"])
        out.append(f"<b>Gun shields and emplacements:</b> shields ({names}; machine guns the GM marks shielded in set-up) take {S['cover']}% off small arms from the gun's front only. "
                   f"In set-up the GM can emplace a gun unit (anti-tank, anti-aircraft, machine guns, batteries): while it stands it counts as gone to ground "
                   f"(-{d.units['to_ground']['cover']}%, hidden, steadier) and cannot move, though it may turn; a unit that breaks leaves its pits.")
    if M:
        kinds = "; ".join(f"{k['name'].lower()}: men {k['men']}%, vehicles {k['vehicles']}%" for k in M["kinds"].values())
        V = d.units["vehicles"]["armour"]
        out.append(f"<b>Minefields (1939 on):</b> painted before the battle, marked or hidden (shown once set off). A unit that moved into minefield hexes "
                   f"(its footprint along the cheapest way within its move from where it began that crosses the fewest known minefield hexes, nearest the straight line of equals) sets them off before the shooting, a hex's worth of men a hex struck at the kind's % ({kinds}), "
                   f"wounded as by a mine at {M['attack']}%; a vehicle struck is knocked out at {V['heavy']['mine']}% (heavy) or {V['light']['mine']}% (light), else immobilised. "
                   f"Sappers (a foot unit so marked), standing out of contact and neither moving nor firing, lay a hidden field in the row ahead of their front in {M['sappers']['lay']} exchanges, "
                   f"or lift the known mines there in {M['sappers']['clear']}; their own side knows their mines, which do not strike it.")
    return out


def _heliborne_rules(d) -> list[str]:
    H = d.units.get("heliborne")
    if not H:
        return []
    return [f"<b>Landing by air:</b> a field can mark landing zones; a unit can come on by air at one, up to {H['lift']} men a zone at the end of each "
            f"exchange, its first men on the zone or the nearest spot within {H['zone']} hexes where they fit. None land while an enemy unit stands within "
            f"{H['blocked']} hexes of the zone. If an enemy unit could shoot at the zone it is hot: each man landing is struck at {H['hot']}% and wounds as by "
            "shellfire. A downed helicopter (a work the GM places at any time) is cover for the men in its hex."]


def _air_rules(ind: dict) -> str:
    """Aircraft on call, for the book."""
    planes = [k for k in ind["kinds"].values() if k.get("air")]
    if not planes:
        return ""
    A = ind.get("air") or {}

    def when(k):
        return "at once" if not k["delay"] else f"{k['delay']} exchanges later"
    kinds = "; ".join(f"{k['name'].lower()}: {k['rounds'] // k['rate']} sorties an aircraft, {when(k)}" + ("" if k.get("by_night") else ", not at night") for k in planes)
    wx = [c.replace("_", " ") for c in A.get("grounded", [])]
    G, F = A["ground_fire"], A["fac"]
    exposed = "; ".join(f"{k['name'].split(' (')[0].lower()} x{k.get('exposed', 1):g}" for k in planes)
    return (f" <b>Aircraft</b> are called like batteries ({kinds}). They are never located, have no crews to lose, and do not fly in "
            + (", ".join(wx[:-1]) + " or " + wx[-1] if len(wx) > 1 else "".join(wx)) + ". "
            + f"<b>Ground fire:</b> each attack run, every aircraft attacking is brought down at {G['mg']:g}% for each enemy machine gun served, {G['rocket']:g}% for each enemy unit with "
            + " or ".join({"rpg": "RPGs", "recoilless": "recoilless rifles"}.get(w, w.replace("_", " ")) for w in G["rockets"]) + f" and {G['rifles']:g}% for every 100 enemy riflemen within {G['reach']} hexes of the aim "
            + f"({exposed}), at most {G['cap']:g}%; anti-aircraft guns within {G['aa_reach']} hexes add {G['aa']:g}% a gun served (times exposed), the whole at most {G['aa_cap']:g}%. "
            + f"Of the aircraft hit, {G['downed']}% are brought down and the rest turn for home damaged; either way it takes its share of the flight's attacks with it. "
            + _run_rules(A)
            + f"<b>Forward air controllers:</b> with a unit marked as one seeing the aim, aircraft scatter 1/{F['scatter']} as far; without, they hold off any target within {F['danger']} hexes of their own men.")


def _run_rules(air: dict) -> str:
    """Strafing runs and napalm strips, and marking the target with smoke."""
    R = air.get("runs") or {}
    s, n = R.get("strafe"), R.get("napalm")
    if not (s and n):
        return ""
    return (f"<b>Attack runs:</b> a strafing run strikes every man on a line of {s['length']} hexes at {s['struck']}% (less cover and going to ground), "
            f"a napalm strip every man on {n['length']} hexes at {n['struck']}% (no cover helps; critical burns, {n['dead']}% killed); vehicles on the line knocked out "
            f"at {s['knock']}% and {n['knock']}% times their armour's shell. Napalm only from 1944. An aimed hex marked with smoke scatters an air attack half as far. ")


def _ground_rules(d) -> list[str]:
    G = d.units.get("ground")
    if not G:
        return []
    parts = []
    for g in G.values():
        bits = [f"move {g['move']}"] + ([f"cover -{g['cover']}%"] if g.get("cover") else []) + ([f"height {g['height']}: -{g['height']}% striking up at it, +{d.units['high_ground']['shoot'] * g['height'] // 10}% shooting down from it"] if g.get("height") else []) \
            + (["no horses"] if g.get("no_horse") else []) + (["hides men"] if g.get("hides") else [])
        parts.append(f"{g['name'].lower()} ({', '.join(bits)})")
    return [
        "<b>Ground and works on the field map:</b> " + "; ".join(parts) + f". Works are the battle map's, along the {yd(d.units['hex_m'])} hex sides: "
        "only reach-2 weapons strike over a palisade, wall or barred gate, from the front rank; striking up a bank, ditch or wall costs its height; "
        "a volley takes the best cover where it lands. Each step costs the worst of all the unit's hexes, and a turn adds the worst extra going of the ground its ends sweep; "
        f"woods and buildings between block aimed fire, direct gun fire and the sight for calling fire, except the {d.units['line_of_fire'].get('see_into', 1)} hex next to either end "
        "(a man sees out of a wood's edge and into it); "
        f"scrub and orchards thin sight instead: each hex of them between costs aimed fire {d.units['line_of_fire']['thin']['per']}%, and more than "
        f"{d.units['line_of_fire']['thin']['blind_past']} block it as woods do; rubble's low heaps give cover but do not block sight; from higher ground a man sees over lower woods and roofs and shoots over units below; "
        "shell fire and a machine gun's fixed line need no sight. A unit ordered to breach puts half its front rank to hacking at the work in front "
        f"(a field-map side takes {d.units['hex_m'] / d.wounds['combat']['move']['hex_m']:g} times a battle-map side's breach figure). "
        f"Escalade: men on foot marked with ladders fight across a palisade, wall or barred gate, {round(100 * d.units['escalade']['share'])}% of each front hex's front rank (at least one) at -{d.units['escalade']['penalty']}%, the defenders' front rank striking back, "
        f"and climb over it for {d.units['escalade']['cross']} hexes of movement. The battle map's weather applies.",
    ]


def _gun_rules(d) -> list[str]:
    A = d.units.get("artillery")
    if not A:
        return []
    m = d.units["hex_m"]
    rs, cn, rc = A["round_shot"], A["canister"], A["ricochet"]
    bands = lambda b: ", ".join(f"{ch}% to {yd(to * m)}" for to, ch in b)
    return [
        f"<b>Guns:</b> a battery is a unit armed with guns, in battery order; its men are the crews, {A['crew']} to a gun, and as crews fall fewer guns are served. "
        f"Each served gun fires {A['rounds']} round an exchange at the nearest enemy in front within {yd(A['range'] * m)}: canister to {yd(A['canister_to'] * m)}, round shot beyond. "
        f"Round shot strikes the unit ({bands(rs['strike'])}), then each man in its path (the ranks deep, at most {rs['path_max']}) is hit at {rs['file']}%, so columns suffer most. "
        f"Canister throws {cn['balls']} chances a round ({bands(cn['strike'])}). Cover, the weather and open order cut both. Each man hit takes a wound roll at {A['attack']}% with no parry.",
        f"<b>Targets and line of fire:</b> the GM can name a battery's target; it fires at it when it can, otherwise at the nearest. "
        "The GM can order its shot (canister only within canister range) and split off sections of its guns at other targets, each with its own shot (one gun stays with the battery). "
        f"Gunners cut fuses: the air band of the fuse table grows by crew quality {_signed(A['set_fuse']['quality'])}, and {A['set_fuse']['ranged']} more on a target fired at last exchange "
        f"at much the same range. A battery charged in front fires {A['closing']} round of canister a gun into the charge as it comes in, and the men it cuts down do not strike. No unit shoots through another unit, "
        "friend or enemy, except from high ground over a unit on lower ground (guns: round shot, never canister); "
        f"bows and crossbows may loose high over units at {d.units['line_of_fire']['arc_penalty']}% off. "
        f"<b>Shell:</b> howitzers fire shell beyond canister range over anything between; a shell lands ({bands(A['howitzer']['strike'])}), "
        f"then its fuse does, before the gunners' setting: {_fuse_text(A['howitzer']['fuse'])}; a burst throws {A['howitzer']['fragments']} chances at {A['howitzer']['air_hit']}% in the air "
        f"(cover counts half) or {A['howitzer']['fragment_hit']}% on the ground. "
        f"Canister gains {cn['graze']}% beyond {yd(cn['strike'][0][0] * m)} on firm ground. "
        f"<b>Rifled guns</b> reach {yd(A['rifled']['range'] * m)} and fire percussion shell beyond canister range on a flat path (a clear line of fire, no bounding): "
        f"it falls on the target ({bands(A['rifled']['strike'])}) and its fuse does, before the setting: {_fuse_text(A['rifled']['fuse'])}; their canister throws {A['rifled']['canister_balls']} balls a round. "
        f"<b>Ricochet:</b> on firm ground round shot bounds on, striking the first other unit within {yd(rc['beyond'] * m)} past the target ({bands(rc['strike'])} past it) "
        "and going through its ranks; rough ground, woods, marsh, mud or snow stop it. "
        f"A round-shot strike on the battery it is fired at knocks out a gun at {A['dismount']}%. <b>Ammunition:</b> {A['ammo']} rounds a gun; resupplying takes an exchange out of contact, without moving or firing.",
        f"<b>Limbering:</b> a limbered battery moves but cannot fire; unlimbered it fires but can only be manhandled {A['pushed']} hexes. Changing over takes an exchange, "
        f"without moving or firing. Hand to hand the crews fight with {d.weapons[A['crew_weapon']]['name'].lower()}. A battery that breaks loses its guns.",
    ]


def _signed(by_quality: dict) -> str:
    """'(green −10, regular 0, veteran +10)'."""
    return "(" + ", ".join(f"{q} {'+' if v > 0 else '−' if v < 0 else ''}{abs(v)}" for q, v in by_quality.items()) + ")"


def _fuse_text(bands) -> str:
    """'15% early, 25% air, 45% ground, 15% blind' from [[up to, what], ...]."""
    out, lo = [], 0
    for to, what in bands:
        out.append(f"{to - lo}% {what}")
        lo = to
    return ", ".join(out)


def _one_arm_text(cb: dict) -> str:
    """'an arm, grip, hand useless or arm useless' impairment, for the rules."""
    names = [x.replace("_", " ") for x in cb.get("one_arm", [])]
    return "an " + (", ".join(names[:-1]) + " or " + names[-1] if len(names) > 1 else "".join(names)) + " impairment"


def _two_handed_text(d) -> str:
    """The two-handed weapons, by short name."""
    names = [w.get("short", w["name"]) for w in d.weapons.values() if w.get("two_handed")]
    return ", ".join(dict.fromkeys(n if n[:2].isupper() else n.lower() for n in names))


def _commander_rules(d) -> list[str]:
    K = d.units.get("commander")
    if not K:
        return []
    by = lambda t: ", ".join(f"{q} {t[q]}" for q in d.units["quality"])
    return [
        "<b>The enemy commander (field map, optional):</b> it orders one side, attacking or holding, at the start of each of its moves; Undo puts the move back. "
        f"It knows an enemy only if one of its units sees it (sight, light, woods, smoke, as calling fire), or saw it in the last {K['remember']} exchanges (where it was then); with none known, a unit holds. "
        f"Each unit's target, among those it knows: {K['closing']} points off a hex away, and times its quality's sense ({by(K['sense'])}): {K['hurt']} a % of the enemy's men down, "
        f"{K['shaken']} if it is shaken, {K['threat']} if it is a danger to the unit (shooters, for men without missiles; men without missiles within a charge, for shooters). Shaken, it holds (and goes to ground under missile fire). Steady, it hesitates on d100 at or under {by(K['hesitate'])}%; "
        f"otherwise it takes the best hex it can reach facing the target: {K['closing']} points a hex nearer, cover % times {by(K['cover'])}, less a point a hex moved; of equals, the hex nearest the straight line to it. "
        f"Shooters stop where the target is in range, keep {K['keep_off']} hexes off, and never charge; with a modern weapon they go to ground under fire. "
        f"Storming works: attacking, {', '.join(d.weapons[w]['name'] for w in K.get('storm', []))} do not stop at range when the target is dug in, behind works giving it cover, or in buildings or rubble; they close (ignoring cover) and charge as men without missiles. "
        "A unit whose target is already in its front arc keeps its facing. "
        f"Others charge only if their men × attack % (with those of steady friends touching them) is at least this % of the target's: attacking {by(K['charge_odds']['attack'])}; holding {by(K['charge_odds']['hold'])}. "
        "A steady unit charging may pass through its own side's units (not to move otherwise); those on its straight line are jostled, their move halved that exchange. "
        f"Holding, a side leaves its ground only to charge. Reserve: at its first move (unless the GM marks reserves) it holds back its rearmost units up to {by(K['reserve'])}% of its men; "
        f"they hold until it commits one a move, when a unit of its side breaks, an enemy it knows of comes within {K['gap']} hexes of one, or (veterans) an enemy breaks. "
        f"Objective (a hex the GM marks, optional): attacking, a unit within {K['objective']['radius']} of it holds it (charging only with holding odds); one with no enemy to go for, "
        f"or that would only stand or turn while its target is more than {K['objective']['guard']} from the objective, advances on it (nearest hex in its allowance). Holding, a unit more than "
        f"{K['objective']['hold']} from it falls back to it unless it can charge. Enemies within {K['objective']['guard']} of it score {K['objective']['bonus']} more as targets; the log names who holds it each exchange. "
        "A battlefield's objective has its own radius (the position as drawn), and the other distances widen by as much. "
        "A second objective (GM-marked): attacking, once its side holds the first, the units on the first stay and the rest go for the second, going back for the first if the enemy retakes it; "
        "holding, once the enemy holds the first, its units fall back to the second. "
        f"Known minefields on the way cost {by(K['mines'])} points a hex. Its batteries and anti-tank guns on the map, in action, turn to face the nearest enemy it knows of; its off-map "
        "batteries with no mission, and its aircraft that can fly, are called on the enemy it sees that scores best as a target (aircraft: one its air controllers see first), never where its own men are within the burst and scatter (cut where a controller sees the aim); "
        "aircraft fly a napalm strip (where the war used it) or a strafing run along an enemy front as wide as the run, if its own men are clear of the line by the scatter. "
        f"Attacking, one battery puts a creeping barrage on an enemy within {K['creep']['near']} hexes of a unit moving or charging on it, lifting {K['creep']['step']} hex an exchange along the unit's facing for {K['creep']['lines']} lines. "
        "Attacking, one battery first lays smoke (the soonest to land) on the nearest enemy shooting at its men who cannot reply, unless it is dark, a gale blows or the hex is smoked. "
        f"Its located batteries that an enemy counter-battery mission is aimed at displace first (a placed one moves its place {d.units['indirect']['displace_shift']} hexes along the nearest map edge, away from the battery firing). "
        "In the dark, one battery with illumination (the soonest to land) lights the enemy it has lost sight of nearest its men, where last seen, unless lit or a round is on its way. "
        "Then one battery, the one with the best counter % that reaches one, fires counter-battery on the located enemy battery with the most tubes served. "
        f"Its sappers, attacking, lift the known enemy mines in the row ahead when the straight way to their target (or the objective) crosses known mines, first closing up along that way to the belt (as far as their move goes without entering known mines) and so working a lane through it row by row; holding, or at the objective, "
        f"with no enemy it knows of within {K['sappers']['clear_of']} hexes, they lay mines in the row ahead (mixed if the enemy it knows of has vehicles, else anti-personnel). "
        f"Attacking, its guns with no known enemy in reach go forward: a battery limbers, moves and unlimbers once one is in reach; anti-tank guns hook up to an empty tractor beside them and are unhooked in reach "
        f"(the tractor counting 4 hexes less; empty tractors fetch them); moving guns stop in reach, no nearer than {K['keep_off']} hexes. Holding, its guns unlimber or unhook where they stand. "
        "Attacking or holding, guns a known enemy could reach at a charge, with no steady unit of its side on the line between, limber (or hook up) and pull back to the hex in their allowance furthest from it. "
        "Attacking, an empty tractor drives beside the nearest guns that want a tow, to hook them up next move. "
        "Attacking, a foot unit beside empty carriers of its side (not tractors) with room for it gets aboard while no enemy it knows of is in reach of its weapon or the carriers'; its carriers set riders down once one is, or at the objective. "
        "Holding, by day or at dusk, its machine guns on foot with no fixed line are laid on the nearest enemy it knows of within their reach. It leaves works to the GM.",
    ]


def _hero_rules(d) -> list[str]:
    H = d.units.get("heroes")
    if not H:
        return []
    return [
        f"<b>Heroes in units:</b> a named fighter in the front rank makes {H['tempo']:g} times a ranker's telling attempts with his own attack, "
        f"and blows on the front fall on him {H['exposure']:g} times as often as on a ranker there; a shooting hero looses {H['tempo']:g} times a ranker's aimed shots. "
        "His wounds use the full rules and his own stop check (a failure: down for the battle); their pain, his Blood lost, their impairments (an arm, a leg, dazed), "
        "the ones he came with too, and his sickness come off his attack and defence as in the wound roller, and too sick to do more than defend, he only defends. "
        "In a quiet exchange (his unit not in contact, not under fire, no losses) his worst-bleeding wound, from this battle or one he came with, gets first aid: "
        f"the best Leechcraft among his unit's heroes still up rolls, a success binding {d.wounds['combat']['first_aid']['bind']} steps of bleeding; with no one who has Leechcraft, his comrades bind one step at {H['first_aid']}%. "
        f"On a success an arm or leg bleeding {H['tourniquet_from']} or more is tourniqueted instead: it stops. "
        "With an arm hurt (an arm wound, a lost grip, a useless hand or arm, either side) he cannot use a two-handed weapon (bows, crossbows, long guns, pole arms): he only defends, "
        "here and in the roller. Lamed (a leg wound, cannot stand, collapsed, slowed) or down and carried, he halves his unit's move "
        f"(times {H['carried']:g}, at least 1 hex) until {H['bearers']} of its men carry him back or it leaves him behind, lying on its hex. "
        f"With an aid post for his side (placed by the GM) they carry him there, {H['aid_post']['pace']} movement an exchange by the cheapest way (round water, walls and enemy units; to the map edge if no way leads to the post), shells striking the party as men in the open, "
        f"and come back after as long; with none, he leaves the battle at once and they return after {H['back_after']} exchanges unless the unit has broken. "
        f"A wounded hero who can walk may go back alone the same way (to the post, or the map edge behind his unit). At the post he gets first aid every exchange at {H['aid_post']['first_aid']}%, "
        f"and his wounds go back to the roller treated; an enemy unit within {H['aid_post']['overrun']} hex of it overruns it, taking or killing the men there by quarter. "
        "A hero left lying is picked up by a unit of his side standing on his hex, or found by an enemy one (quarter). A unit's medics give first aid at "
        f"{', '.join(f'{q} {v}%' for q, v in H['medic'].items())}. In the wars before 1914 a heavy bleed a tourniquet cannot reach is cauterised "
        f"(+{H['cautery']['pain']} pain unless a healer does it). A hero left on the field at the end (left behind, on his way back, or down with a unit that broke) is found if his side "
        f"holds the field; else d100 against the war's quarter (default {H['quarter']['default']}%) makes him a prisoner, over it he is killed. "
        "A leader adds his unit's leader modifier while he is up.",
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


def team_eras(d) -> list[str]:
    """The eras with team tables, medieval first, then in the order of their years."""
    order = ["medieval", "thirty_years", "horse_musket", "crimea", "civil_war", "plains_nations", "wwi", "wwii", "korea", "vietnam", "modern"]
    return [e for e in order if e in d.teams] + sorted(e for e in d.teams if e not in order)


def team_rules(d, eid: str = "medieval") -> list[str]:
    """Character generation, as short rules for the PDF and Markdown (data/teams). The first era
    gets the whole method; the others only what differs."""
    T = d.teams[eid]
    if eid != team_eras(d)[0]:
        skills = ", ".join(s["name"] for s in T["skills"] if s.get("combat"))
        return [f"<b>{T['name']}:</b> made exactly as the medieval era's, in the same five steps, from the tables below. "
                f"Fighting skills: {skills}. Each region takes its war's wound table, for old wounds and for the roller.", _follower_rule(d, T)] + _women_rule(T)
    ch = ", ".join(c["name"] for c in T["characteristics"])
    return [
        f"<b>{T['name']}: a team in twenty minutes.</b> A player runs a team of four to six; the first member leads. Each character is made in five steps.",
        f"<b>1. Characteristics:</b> {ch}: roll 3d6 x 5 for each in order (15-90), or take the array {', '.join(map(str, T['array']))} "
        "and place it, highest first, in the order his career prefers (the GM may let him swap two).",
        f"<b>2. Origin:</b> d100 on the origin table: a skill +{T['gain']}, a trait and its drawback (a characteristic +/-10 or a skill +/-{T['gain']}).",
        f"<b>3. Career terms:</b> leaders serve three terms, the rest one or two. Each term: his career's main skill +{T['first_term']} the first term and "
        f"+{T['term_main']} after, its second skill +{T['term_second']}, and d100 on the career's table: the skill named +{T['gain']} and the event. "
        "An event he has already had moves to the next row down. Nobody dies in generation. "
        f"He is {T['age']['start']} plus {T['age']['per_term']} a term.",
        "<b>4. Old wounds:</b> a row marked * leaves an old wound, as does d100 at or under the career's old-wound %. Roll its location on the region's "
        f"wound table for the weapon shown, then d100: {T['old_wound'][0]['to']} or less a healed scar; more, a lasting hurt: "
        f"-{T['lasting']} to Wits (head), Presence (face), Strength (arms), Agility (legs) or Endurance (body).",
        f"<b>5. Skills and kit:</b> each skill starts at a characteristic divided as shown (rounded down), plus what he gained, at most {T['skill_max']}. "
        "His attack is the skill his weapon is fought with; his defence the better of Parry and Dodge; his Nerve the characteristic. "
        "Kit and weapon come with his career and region (the table below).",
        _follower_rule(d, T),
    ]


def _women_rule(tables) -> list[str]:
    """Where women served under arms in this era: each army's share and open careers (data/teams women)."""
    names = {c["id"]: c["name"].lower() for c in tables["careers"]}
    rows = [(r, r["women"]) for r in tables["regions"] if r.get("women")]
    if not rows:
        return []
    def one(r, women):
        share = f"{women['share']:g}%" if women.get("share") is not None else "no reliable share: chosen, never rolled"
        how = ", enlisted disguised as men" if women.get("disguised") else ""
        return f"{r['name']} ({share}{how}): {', '.join(names[c] for c in women['careers'])}"
    return ["<b>Women under arms:</b> a member may be a woman (her own name lists and origins, no beard; the texts say she and her), "
            "chosen or rolled d10000 at or under the army's share x 100 before the characteristics, for a career open to women: "
            + "; ".join(one(r, W) for r, W in rows) + ". Elsewhere these careers were closed to them."]


def _follower_rule(d, tables) -> str:
    Q, U = tables["followers"]["quality"], d.units["quality"]
    def band(rows):
        lo, out = 1, []
        for r in rows:
            out.append(f"{lo:02d}-{r['to'] % 100:02d} {r['quality']}")
            lo = r["to"] + 1
        return ", ".join(out)
    tables = "; ".join(f"{k}: {band(v)}" for k, v in Q.items())
    qs = ", ".join(f"{k} {v['attack']}/{v['defence']}/{v['nerve']}" for k, v in U.items())
    return (f"<b>Followers:</b> a big team's other men get one line each: a career (for kit and weapon), a name, and a quality on d100 ({tables}), "
            f"which gives attack/defence/Nerve ({qs}). No characteristics or skills (50 in each in the roller). The team's followers are in the table below.")


def team_tables(d, eid: str = "medieval") -> dict:
    """The generation tables as rows: skills, origins, careers, events, templates."""
    T = d.teams[eid]
    sk = {s["id"]: s["name"] for s in T["skills"]}
    st = {c["id"]: c["name"] for c in T["characteristics"]}
    nm = lambda k: sk.get(k) or st.get(k)
    mod = lambda m: "; ".join(f"{m['text']} ({nm(k)} {v:+d})" for k, v in m.items() if k != "text")
    per = 100 // len(T["origins"])
    weapons = {}
    for w, s in T["weapon_skill"].items():
        weapons.setdefault(s, []).append(d.weapons[w]["short"].lower())
    skills = [["Skill", "Starts at", "Weapons"]] + [[s["name"], f"{st[s['of']]} / {s['div']}", ", ".join(weapons.get(s["id"], []))] for s in T["skills"]]
    origins = [["d100", "Origin", "Skill", "Trait", "Drawback"]] + [
        [f"{i * per + 1:02d}-{(i + 1) * per:02d}".replace("96-100", "96-00"), o["name"], sk[o["gain"]], mod(o["trait"]), mod(o["drawback"])] for i, o in enumerate(T["origins"])]
    careers = [["Career", "Main skill", "Second", "Old wound", "Hurt by"]] + [
        [c["name"], sk[c["main"]], sk[c["second"]], f"{c['wound']}%", d.weapons[c["wound_weapon"]]["short"].lower()] for c in T["careers"]]
    events = [["Career", "d100", "Skill", "Event"]]
    for c in T["careers"]:
        lo = 1
        for r in c["terms"]:
            events.append([c["name"], f"{lo:02d}-{r['to']:02d}".replace("-100", "-00"), sk[r["skill"]], r["text"] + (" *" if r.get("wound") else "")])
            lo = r["to"] + 1
    regions = T["regions"]
    many = len(T["regions"]) > 6                  # a wide table: the kit's first words only ("Interceptor vest")
    def kitname(k):
        name = d.armor["kits"][k]["name"].split(" (")[0]
        if not many:
            return name
        return "No armour" if k == "none" else name.split(",")[0]
    kits = [["Career"] + [r.get("short") or r["name"].split(" (")[0] for r in regions]] + [
        [c["name"]] + [f"{kitname(c['kit'].get(r['id'], c['kit']['default']))}; {d.weapons[c['weapon'].get(r['id'], c['weapon']['default'])]['short'].lower()}" for r in regions]
        for c in T["careers"]]
    names = {c["id"]: c["name"] for c in T["careers"]}
    teams = [["Team", "Members (terms)", "Followers (quality table)"]] + [[t["name"], ", ".join(f"{names[c]} ({n})" for c, n in t["slots"]),
              ", ".join(f"{n} {names[c].lower()}" for c, n in t.get("followers", [])) + f" ({t.get('follower_quality', 'default')})"] for t in T["templates"]]
    return {"skills": skills, "origins": origins, "careers": careers, "events": events, "kits": kits, "teams": teams}


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
        f"<b>A leech:</b> the best Leechcraft among the named men with a force (alive, not too sick to work) adds Leechcraft / {D['leech']['per']} "
        "to every recovery check of its sick and wounded, and takes as much off each wound's chance of turning septic.",
    ] + _scurvy_rules(d) + _frostbite_rules(d) + _wound_track_rules(d)


def _fc(c: float) -> str:
    """A temperature, US units first: '5 °F (-15 °C)'."""
    return f"{c * 9 / 5 + 32:.0f} °F ({c:g} °C)"


def _frostbite_rules(d) -> list[str]:
    F, C = d.disease.get("frostbite"), (d.weather or {}).get("cold")
    if not F:
        return []

    def level(v):
        move = f", +{v['move']} movement a hex" if v.get("move") else ""
        return f"{v['name'].lower()} (low at or under {_fc(v['below'])}): automatic weapons misfire {v['jam']}% more{move}"
    levels = "; ".join(level(v) for v in (C or {}).get("levels", {}).values())
    return [f"<b>Frostbite:</b> on a night whose low is {_fc(F['below'])} or colder, each well man may be frostbitten: {F['base']}% plus {F['per_degree']}% "
            f"a degree colder, less {F['shelter']}% of that for each point of the camp's shelter, times the chance he fails to resist. It shows at once "
            f"(d100: mending, serious or grave) and is checked every {F['every']} days at virulence {F['virulence']}."
            + (f" <b>Cold in battle:</b> {levels}." if levels else "")]


def _scurvy_rules(d) -> list[str]:
    S = d.disease.get("scurvy")
    if not S:
        return []
    return [
        f"<b>Scurvy:</b> each force counts its days without fresh food. A day ends it in farmland, a village or a town, or in open country, "
        f"forest or hills if the force camped there all day and foraged, or on a march day there if a named man's Fieldcraft roll finds it, "
        f"or when the GM issues fresh food. After {S['after_days']} days "
        f"without it, each week every well man may fall ill: {S['chance']}% the first week, {S['per_week']} more each week after, "
        f"times the chance he fails to resist. It shows at once at mending and is checked once a week: with fresh food in the past "
        f"week, {S['heal']} steps better; without it, the recovery check at virulence {S['virulence']}: success holds, failure is one "
        f"step worse, and failure at deadly kills. A named character's old wounds and scars reopen at mending and cannot heal until "
        f"the scurvy has. Records: {S['deaths']}% of cases died in the Union army; far more with no fresh food at all.",
    ]


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
    ] + _light_rules(d)


def _light_rules(d) -> list[str]:
    L = d.weather.get("light")
    if not L:
        return []
    rs, hm = d.units["range_scale"], d.units["hex_m"]
    lv = "; ".join(f"{v['name'].lower()}: " + ("" if v["sight"] is None else f"no aiming or calling fire beyond {v['sight'] // rs} hexes, {yd(v['sight'] // rs * hm)}, ")
                   + f"aimed fire -{v['aim']}%" for v in L["levels"].values() if v["sight"] is not None or v["aim"])
    return [f"<b>Light on the field map:</b> {lv}. A hex lit by a flare or illumination is seen as by day for {L['lasts']} exchanges; the GM's flare lights "
            f"{L['flare']} hexes round it. A battle from the travel map takes the hour's light: dusk within {L['dusk_hours'] * 60:g} minutes of sunrise or sunset; "
            f"at night moonlit when the moon is up, at least {L['moon_from'] * 100:g}% lit and the sky clear, else dark.",
            f"<b>Fighting in the dark:</b> a unit that fired when sight is under {L['flash'] // rs} hexes is seen by its muzzle flashes out to {L['flash'] // rs} hexes "
            "through the next exchange. Night-vision devices (a unit's own, or its kit's: "
            + ", ".join(d.armor["kits"][k]["name"].split(" (")[0].split(",")[0] for k in L["night_vision"]["kits"]) + f" carry {L['night_vision']['devices'][L['night_vision']['kit_device']]['name'].split(' (')[0].lower()}): "
            + "; ".join(f"{v['name']} sees {v['sight'] // rs} hexes, " + (f"aims -{v['aim']}% at worst" if v["aim"] else "aims as by day")
                        + (", and through smoke" if v.get("smoke") else "") for v in L["night_vision"]["devices"].values())
            + ". Vehicles with none chosen carry their war's: " + ", ".join(f"{w} {L['night_vision']['devices'][v]['name'].split(' (')[0].lower()}" for w, v in (L["night_vision"].get("vehicles") or {}).items())
            + ". A machine gun laid on "
            f"a fixed line by day or at dusk fires blind down it in the dark at the nearest enemy within {L['fixed_line']['width']} hex of it, -{L['fixed_line']['aim']}%. "
            "Moving: " + "; ".join(f"{v['name'].lower()} +{v['move']} a hex" for v in L["levels"].values() if v["move"])
            + ". A unit that moved may lose its way: " + "; ".join(f"{v['name'].lower()} {v['lost']}%" for v in L["levels"].values() if v["lost"])
            + f", plus half of (60 - its Nerve); it turns one point off its line and cannot move for {L['lost_for'] - 1} exchange."]


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
        "<b>One clock:</b> every force on a map keeps the same time. Each has orders (march on its route, or halt); the GM moves the clock on an hour, "
        "to nightfall, or until something happens (an arrival, a camp finished, or forces of different sides within fighting reach, when both halt). "
        "A force making camp or fighting is busy until it is done. A march stopped mid-hex keeps the time spent on it.",
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
    W, L = d.works, d.wounds["combat"]["line_of_fire"]
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
        f"<b>In the way:</b> each fighter standing on the line between a shooter and his target costs the shot {L['per_man']}% (at most {L['max']}%). "
        f"A miss goes into the first man in the way at {L['stray']}%: roll the hit on him with no attack roll and the severity table. "
        "Bows and crossbows loose high over the men in the way: the penalty, but never a stray.",
        _surprise_rule(d),
    ] + ground_rules(d)


def _surprise_rule(d) -> str:
    S, C = d.works["surprise"], d.works["camps"]
    camps = ", ".join(f"{v['name'].lower()} {v['surprise']:+d}" for v in C.values())
    return (f"<b>Surprise:</b> when a fight is set up from the travel map, d100 against {S['base']}% + the camp's shift (no camp {S['none']:+d}; {camps}) "
            f"+ {S['dark']} if it starts between sunset and sunrise + {S['fog']} in fog + the attackers' best Stealth / {S['per']} "
            f"- the defenders' best Watch / {S['per']} (named characters with the forces), within {S['range'][0]}-{S['range'][1]}%. "
            "Surprised: in the wound roller the defenders and their friends cannot act in round 1; on the field map their units start shaken.")


def ground_rules(d) -> list[str]:
    G = d.wounds["combat"]["ground"]
    K, E = G["kinds"], G["edges"]
    return [
        f"<b>Ground:</b> the GM paints hexes as rocks and rubble, woods and brush, marsh, deep water, road or bridge (roads and bridges are open going). Entering rocks or woods costs +{K['rough']['move']} hex of movement, "
        f"marsh +{K['marsh']['move']}; no one enters or stands in deep water, though shots cross it. A shot at a man in rocks loses {K['rough']['cover']}% and the rocks hide his legs (the table's behind-cover situation); "
        f"in woods it loses {K['brush']['cover']}%. Cover from a work counts instead when it is better.",
        f"<b>Height:</b> hexes stand at level 0 to {G['max_level']}; each level climbed costs +{G['climb']} hex of movement. "
        "A blow or shot from higher ground takes the attacker-higher situation (head and shoulders), and from lower ground attacker-lower. "
        f"A man striking uphill in close combat loses {G['uphill']}% a level (two levels at most). A shot downhill reaches {G['downhill_reach']}% further a level. "
        "Higher ground rising above the straight line between shooter and target blocks the shot; men in the way below that line are shot over.",
        "<b>Laying out ground:</b> a fight sent from the travel map lays its ground out like the defenders' travel hex: clumps of woods, rocks and marsh "
        "and a rise or two, in the shares below; inside a camp's works the ground is cleared and level. "
        "The fight stands at a fixed spot in that hex: where the map reaches past a side of the hex, the ground beyond is laid out like the neighbouring hex, "
        f"a lake as deep water and a river as a band of deep water {E['river_width'][0]} to {E['river_width'][1]} hexes wide, with a ford "
        f"{E['ford_width'][0]} to {E['ford_width'][1]} hexes wide (marsh to wade) when a ford or bridge is next to the hex. "
        "A fight in a road, ford or bridge hex is on the road or at the crossing: the road (and at a ford or bridge the river) runs through the map's middle "
        "toward the neighbouring hexes it links to, crossing the river by a ford or a bridge; a camp with works there stands on the bank away from the attackers, moved back from the middle as far as the river needs (a camp too big for the map showing the stretch facing the river), the river passing it and the gate facing the crossing; a camp on a road has a gate wherever a road leaves it. Attackers come in on the map's edge facing the way they came (in the defenders' own hex, from the side of the hex they last left), on the dry hexes nearest it. "
        + "; ".join(f"{d.terrain['terrain'][t]['name']}: " + ", ".join([f"{G['kinds'][k]['name'].lower()} {round(v * 100)}%" for k, v in x.items() if k in G['kinds']]
                    + ([f"{x['rises']} rise{'s' if x['rises'] > 1 else ''} to level {x['top']}"] if x.get('rises') else [])) for t, x in G["seed"].items()) + ".",
        f"<b>Taking cover:</b> on his turn a fighter may go to ground instead of moving or attacking. Until he moves or strikes in close combat, "
        f"shots at him lose {G['take_cover']}% (or the ground's cover if better) and hit as behind cover, and blows at him hit as at a man down. "
        f"Getting up takes {G['rise']} hexes of his move, to move on or to strike in close combat; he may shoot from cover without getting up.",
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
        "ground": {k: d.wounds["combat"]["ground"][k] for k in ("through", "camp_bank")},   # a camp's gates (camp.js)
        "maps": {mid: {**{k: m.get(k) for k in ("id", "name", "hex_km", "rows", "places", "forces",
                                                   "start_date", "calendar", "latitude", "climate", "climate_shift")}, "period": periods(d)["maps"][mid]}
                 for mid, m in d.maps.items()},
        "period_order": periods(d)["order"],
        "battlefields": {fid: {"name": f["name"], **f["travel"]} for fid, f in d.fields.items() if f.get("travel")},
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
    from gravewounds.units import battlefield
    rng3 = lambda rs: [[r["id"], r["lo"], r["hi"]] for r in rs]
    tables = {}
    for tid, t in d.tables.items():
        ws = available_weapons(d, tid)
        tables[tid] = {"name": t["name"], "label": t.get("label", t["name"]), "battle": t.get("battle", "Other"),
                       "weapons": ws, "ranges": {w: rng3(table_ranges(d, tid, w)) for w in ws}}
    used = sorted({w for t in tables.values() for w in t["weapons"]})
    keep = ("name", "short", "reach", "range", "threat", "armor_defeat", "off_map", "string", "ignition", "two_handed")
    mechs = sorted({m[0] for w in used for m in rng3(mechanism_ranges(d, w))})
    return {
        "generated": date.today().isoformat(),
        "units": d.units,
        "combat": {k: d.wounds["combat"][k] for k in ("critical_fraction", "graze_margin", "margin_bands", "range", "pain_step", "stop_check", "states", "impair", "cap", "first_aid", "one_arm")},
        "in_fight": d.disease.get("in_fight") or {},
        "tracking": {k: d.wounds["tracking"][k] for k in ("blood_pool", "thresholds", "pain_cap", "bleed_per_round")},
        "blood_per": d.wounds["combat"]["characteristics"]["blood"]["per"],
        "tables": tables,
        "weapons": {w: {k: d.weapons[w][k] for k in keep if k in d.weapons[w]} for w in used},
        "mechanisms": {w: rng3(mechanism_ranges(d, w)) for w in used},
        "locations": {l["id"]: {"zone": l["zone"], "name": l["name"], "side": l.get("side")} for l in d.locations},
        "kits": {k: {"name": v["name"], "layers": {l["id"]: [list(x) for x in armor_at(d, k, l["id"])] for l in d.locations}}
                 for k, v in d.armor["kits"].items()},
        "materials": {m: {k: v[k] for k in ("cut", "pierce", "crush", "ballistic", "threats") if k in v} for m, v in d.armor["materials"].items()},
        "effects": {l["id"]: {m: {s: _lethal_inf(compose_wound(d, l["id"], m, s)) for s in ("light", "serious", "critical")} for m in mechs}
                    for l in d.locations},
        "track": {"steps": d.disease["steps"], "wounds": d.disease["wounds"]},
        "works": d.works,
        "weather": {k: d.weather[k] for k in ("winds", "conditions", "battle", "ground", "wind_points", "driven_sight", "light", "cold") if k in d.weather},
        "battle_hex_m": d.wounds["combat"]["move"]["hex_m"],
        "fields": {fid: {"name": f["name"], "sides": f["sides"], "table": f["table"], "field": battlefield(d, fid), "units": f.get("units", []), "objective": f.get("objective"), "markers": f.get("markers"), "entry": f.get("entry"), "phases": f.get("phases"),
                         "travel": f.get("travel"), "period": periods(d)["fields"][fid]}
                   for fid, f in d.fields.items()},
        "period_order": periods(d)["order"],
        "mapStarts": {mid: str(m.get("start_date", "")) for mid, m in d.maps.items()},
    }


def _lethal_inf(fx: dict) -> list:
    """[untreated time to death, infection risk, bleed, pain, shock, impairments] of a composed
    wound (the field page's: the last four for heroes)."""
    return [fx["lethal"], fx["infection"], fx["bleed"], fx["pain"], bool(fx.get("shock")), list(fx.get("impair") or [])]


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
        "combat": {**d.wounds["combat"], "ground": {**d.wounds["combat"]["ground"],
                   "terrain_names": {t: x["name"] for t, x in d.terrain["terrain"].items()}}},
        "works": d.works,
        "disease": {"steps": d.disease["steps"], "in_fight": d.disease["in_fight"], "endurance": d.disease["endurance"],   # named characters' sickness
                    "wounds": {k: d.disease["wounds"][k] for k in ("start", "clock_step", "fever_after")}, "blood_per_day": d.disease["named_blood_per_day"],
                    "names": {k: v["name"] for k, v in {**d.disease["diseases"], "scurvy": d.disease["scurvy"], **({"frostbite": d.disease["frostbite"]} if "frostbite" in d.disease else {}), **{w: d.disease["wounds"][w] for w in ("wound", "fever")}}.items()}},
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
    if d.teams:
        mdt = lambda rows: ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * len(rows[0])] + ["| " + " | ".join(r) + " |" for r in rows[1:]] + [""]
        out += ["## Team generation", ""]
        for eid in team_eras(d):
            tt = team_tables(d, eid)
            out += [f"### {d.teams[eid]['name']}", ""] + [re.sub("</?b>", "**", x) + "\n" for x in team_rules(d, eid)]
            out += mdt(tt["skills"]) + mdt(tt["origins"]) + mdt(tt["careers"]) + mdt(tt["events"]) + mdt(tt["kits"]) + mdt(tt["teams"])
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
                        "Each impairment counts once however many wounds cause it. A fighter with neither hand usable cannot wield a weapon. "
                        f"With {_one_arm_text(CB)} on either arm he cannot attack with a two-handed weapon ({_two_handed_text(d)}): he only defends.", S),
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
    if d.teams:
        cell = lambda rows: [[Paragraph(x, CH) for x in rows[0]]] + [[Paragraph(str(c), C) for c in r] for r in rows[1:]]
        for k, eid in enumerate(team_eras(d)):
            tt, nreg = team_tables(d, eid), len(d.teams[eid]["regions"])
            head = [PageBreak(), Paragraph("Team generation", H1)] if k == 0 else [PageBreak()]
            story += head + [Paragraph(d.teams[eid]["name"], H2)] + [Paragraph(x, B) for x in team_rules(d, eid)] + [
                Spacer(1, 6), Paragraph("Skills", H2), grid(cell(tt["skills"]), [1.6 * inch, 1.3 * inch, W - 2.9 * inch], font=7.5),
                Spacer(1, 6), Paragraph("Origins", H2), grid(cell(tt["origins"]), [0.6 * inch, 1.9 * inch, 1.0 * inch, (W - 3.5 * inch) / 2, (W - 3.5 * inch) / 2], font=7.5),
                Spacer(1, 6), Paragraph("Careers", H2), grid(cell(tt["careers"]), [1.9 * inch, 1.2 * inch, 1.2 * inch, 0.9 * inch, W - 5.2 * inch], font=7.5),
                Spacer(1, 6), Paragraph("Career terms (* leaves an old wound)", H2), grid(cell(tt["events"]), [1.7 * inch, 0.6 * inch, 1.1 * inch, W - 3.4 * inch], font=7.5),
                Spacer(1, 6), Paragraph("Kit and weapon by region", H2), grid(cell(tt["kits"]), [(1.1 if nreg > 6 else 1.5) * inch] + [(W - (1.1 if nreg > 6 else 1.5) * inch) / nreg] * nreg, font=6.5 if nreg > 6 else 7),
                Spacer(1, 6), Paragraph("Teams", H2), grid(cell(tt["teams"]), [1.6 * inch, (W - 1.6 * inch) / 2, (W - 1.6 * inch) / 2], font=7.5)]
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


def team_bundle(d) -> dict:
    """What the team builder needs: every era's tables and old-wound location ranges (TD.eras;
    the page points TD.era and TD.ranges at the one chosen), and the names, kits and weapons its
    sheets and figures show."""
    from gravewounds.team import old_wound_ranges
    kits, weapons = set(), set()
    for T in d.teams.values():
        kits |= {c["kit"].get(r["id"], c["kit"]["default"]) for c in T["careers"] for r in T["regions"]}
        weapons |= set(T["weapon_skill"]) | {c["wound_weapon"] for c in T["careers"]}
        weapons |= {c["weapon"].get(r["id"], c["weapon"]["default"]) for c in T["careers"] for r in T["regions"]}
    eras = {eid: {"era": d.teams[eid], "ranges": old_wound_ranges(d, eid)} for eid in team_eras(d)}
    first = team_eras(d)[0]
    return {"eras": eras, "era": eras[first]["era"], "ranges": eras[first]["ranges"],
            "locs": {l["id"]: {"name": l["name"], "zone": l["zone"], "class": l["class"]} for l in d.locations},
            "kits": {k: d.armor["kits"][k] for k in sorted(kits)},
            "fight": {"blood_pool": d.wounds["tracking"]["blood_pool"], "chr": d.wounds["combat"]["characteristics"]},
            "quality": d.units["quality"],   # followers' attack, defence and Nerve
            "weapons": {w: d.weapons[w] for w in sorted(weapons) if w in d.weapons}}


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
    team_js = (ROOT / "templates" / "team.js").read_text(encoding="utf-8")
    gtpl = (ROOT / "templates" / "team.html").read_text(encoding="utf-8")
    ghtml = gtpl.replace("/*__FIGURE_JS__*/", fig_js.replace("</script>", "<\\/script>")).replace("/*__TEAM_JS__*/", team_js)
    (DIST / "team.html").write_text(ghtml.replace("/*__TEAM_DATA__*/null", json.dumps(team_bundle(d), separators=(",", ":"))), encoding="utf-8")
    from gravewounds.rulebook import render as rule_book
    (DIST / "rules.html").write_text(rule_book(d, ROOT), encoding="utf-8")
    (ROOT / "index.html").write_text(index_page(d), encoding="utf-8")
    print("Built:", ", ".join(p.name for p in sorted(DIST.iterdir())), "+ index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
