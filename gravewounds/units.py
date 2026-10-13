"""Unit combat (Grave Wounds): the rank and file fight as units, resolved in bulk once an
exchange (about a minute). Only the men actually striking roll, and each telling blow goes
through the individual rules: attack and defence d100, a critical cannot be parried, the
margin sets severity, then hit location, mechanism and armour from the battle's tables
(gravewounds.engine.roll_hit). Numbers are in data/units.yaml; see docs/units.md.

A side is {table, weapon, kit, quality, shield (bool or None), attack (extra %), defence
(extra %)}. The field map (or the GM) says how many men are striking: see fighters()."""
from __future__ import annotations

import heapq
import math
import random

from . import combat as C
from .combat import weapon_reach
from .disease import wound_case
from .engine import roll_hit
from .model import Data


def quality(d: Data, q: str) -> dict:
    return d.units["quality"][q]


def fighters(d: Data, front: int, reach: int) -> int:
    """Men striking in melee: the `front` men in the front rank touching the enemy, and one
    more rank for each hex of reach past the first, up to close order's ranks."""
    return front * min(reach, d.units["formations"]["close"]["ranks"])


def field_range(d: Data, wid: str, field_hexes: int, reach: int = 0) -> dict | None:
    """A weapon's range band at this many field-map hexes (weapon ranges are battle-map hexes);
    reach: % on the bands from the wind (with it +, into it -)."""
    return weapon_reach(d, wid, field_hexes * d.units["range_scale"] * 100 / (100 + reach))


def _count(n: float, rng: random.Random) -> int:
    """n blows, with the fraction rounded by chance (so tempo works on small units too)."""
    whole = math.floor(n)
    return whole + (1 if rng.random() < n - whole else 0)


def _new_tally() -> dict:
    return {"blows": 0, "missed": 0, "parried": 0, "stopped": 0, "hits": 0,
            "light": 0, "serious": 0, "critical": 0, "down": 0, "dead": 0, "hurt": {}}


def _hurt(t: dict, sev: str, fx: dict, down: bool) -> None:
    """Remember a wounded man by severity, death clock, infection risk and whether he is down."""
    k = f"{sev}|{fx['lethal']}|{fx['infection']}|{1 if down else 0}"
    t["hurt"][k] = t["hurt"].get(k, 0) + 1


def _wound(d: Data, att: dict, dfd: dict, margin: int, critical: bool, rng: random.Random, t: dict) -> None:
    """One blow that got through: roll it, then the stop check and death."""
    h = roll_hit(d, att["table"], att["weapon"], rng=rng, kit=dfd.get("kit"), margin=margin,
                 critical=critical, shield=dfd.get("shield"))
    sev, modern = h["severity"], att["weapon"] in d.units["modern_fire"]["weapons"]
    if sev == "stopped":
        t["stopped"] += 1
        return
    t["hits"] += 1
    t[sev] += 1
    if h["effects"]["lethal"] in d.units["dead_if"]:
        t["dead"] += 1
        t["down"] += 1
        return
    if h["graze"] or (sev == "light" and not modern):
        _hurt(t, "light", h["effects"], False)
        return
    down = (modern and sev != "light") or rng.randint(1, 100) > quality(d, dfd["quality"])["nerve"] - (10 if sev == "critical" else 0)
    if down:
        t["down"] += 1
    _hurt(t, sev, h["effects"], down)


def _attack(d: Data, side: dict) -> int:
    """A side's attack %: a hero's own skill, else his unit's quality; plus any extra."""
    return side.get("skill", quality(d, side["quality"])["attack"]) + side.get("attack", 0)


def melee(d: Data, att: dict, dfd: dict, men: int, rng: random.Random, situation: str = "front",
          charge: bool = False, shaken: bool = False, rout: bool = False, exposed: tuple = (), penalty: int = 0) -> dict:
    """One exchange of `men` striking at a unit. situation: front, flank or rear. rout: the
    defender is broken and fleeing: then `men` should be all the pursuers, who strike in open
    order. exposed: (hero, chance) for heroes in the struck unit whom a blow may fall on.
    Returns a tally of blows and what they did."""
    M, U = d.units["melee"], d.units
    tempo, atk = M["tempo"], _attack(d, att) - penalty
    base = dfn = quality(d, dfd["quality"])["defence"] + dfd.get("defence", 0)
    if situation in ("flank", "rear"):
        atk += M[situation]["attack"]
        dfn += M[situation]["defence"]
    if charge:
        atk += M["charge"]["attack"]
        tempo *= M["charge"]["tempo"]
    if shaken:
        atk += M["shaken"]["attack"]
    if rout:
        atk += U["rout"]["attack"]
        tempo *= U["rout"]["tempo"]
        dfn = 0
    shift = dfn - base if dfn > 0 else -1000      # a hero's defence moves with his unit's; none if it has none
    return _blows(d, att, dfd, _count(men * tempo, rng), atk, dfn, rng, exposed, shift)


def volley(d: Data, att: dict, dfd: dict, men: float, field_hexes: int, rng: random.Random,
           penalty: int = 0, factor: float = 1.0, exposed: tuple = (), reach: int = 0) -> dict | None:
    """One exchange of `men` shooting at a unit `field_hexes` away (a machine-gun team: its
    served guns, at machine_guns.tempo). penalty: extra % off (weather, cover); factor: the
    target formation's missile_factor; reach: the wind's % on the range bands. None if out of
    range."""
    shot = _volley_shots(d, att, men, field_hexes, rng, (penalty, factor, reach))
    return None if shot is None else _blows(d, att, dfd, shot[0], shot[1], 0, rng, exposed, -1000)


def _volley_shots(d: Data, att: dict, men: float, field_hexes: int, rng, mods: tuple = (0, 1.0, 0)):
    """(aimed shots, attack %) of a volley (mods: penalty, factor, reach as volley's), or None if out of range."""
    penalty, factor, reach = mods
    band = field_range(d, att["weapon"], field_hexes, reach)
    if band is None:
        return None
    S = d.units["missile"]
    tempo = d.units["machine_guns"]["tempo"] if is_mg(d, att["weapon"]) else S["tempo"]
    shots = men * S["rate"].get(att["weapon"], S["default_rate"]) * tempo * factor
    return _count(shots, rng), _attack(d, att) - band["penalty"] - penalty


def _blows(d: Data, att: dict, dfd: dict, n: int, atk: int, dfn: int, rng: random.Random,
           exposed: tuple = (), shift: int = 0) -> dict:
    t = _new_tally()
    t["blows"] = n
    atk = max(0, atk)
    crit_at = math.floor(atk * d.wounds["combat"]["critical_fraction"])
    for _ in range(n):
        hero = _aimed_at(exposed, rng)
        r = rng.randint(1, 100)
        if hero is not None:
            _hero_blow(d, att, hero, r, atk, crit_at, shift, rng, t)
            continue
        if r > atk:
            t["missed"] += 1
            continue
        critical = r <= crit_at
        if not critical and dfn > 0 and rng.randint(1, 100) <= dfn:
            t["parried"] += 1
            continue
        _wound(d, att, dfd, atk - r, critical, rng, t)
    return t


# ---------- heroes ----------
# A named fighter from the wound roller with a unit: {id, name, role (front, ranged or
# behind), attack, defence, nerve, weapon, kit, leader, state (up, down or dead), wounds}.
# He is extra to the unit's men. Front: strikes with his own skill each time his unit fights
# hand to hand, and blows on his unit's front may fall on him. Ranged: shoots with his own
# skill each time his unit shoots, and is at risk from missiles and in contact. Behind:
# only in a rout. His wounds use the full rules and go back to the roller.

def _aimed_at(exposed: tuple, rng):
    """The hero a blow falls on, or None: each hero still up, in turn, by his chance."""
    for hero, p in exposed:
        if hero["state"] == "up" and rng.random() < p:
            return hero
    return None


def _hero_blow(d: Data, att: dict, hero: dict, r: int, atk: int, crit_at: int, shift: int, rng, t: dict) -> None:
    """A blow aimed at a hero: his own parry (none if stunned; less for his wounds), then the
    full wound roll on his kit, and the roller's stop check."""
    if r > atk:
        return
    critical = r <= crit_at
    dfn = 0 if _held(hero) == "stunned" else hero["defence"] + shift - hero_penalties(d, hero)[1]
    if not critical and dfn > 0 and rng.randint(1, 100) <= dfn:
        return
    h = roll_hit(d, att["table"], att["weapon"], rng=rng, kit=hero.get("kit"), margin=atk - r, critical=critical)
    sev = h["severity"]
    if sev == "stopped":
        return
    fx = h["effects"]
    bleed, pain, shock = (max(0, fx["bleed"] - 1), max(0, fx["pain"] - 1), False) if h["graze"] else (fx["bleed"], fx["pain"], bool(fx.get("shock")))
    hero["wounds"].append({"loc": h["location"], "mech": h["mechanism"], "sev": sev, "graze": h["graze"], "bleed": bleed, "pain": pain, "impair": list(fx.get("impair") or [])})
    if fx["lethal"] in d.units["dead_if"]:
        hero["state"] = "dead"
    elif {"down", "incapacitated"} & set(hero_penalties(d, hero)[2]):
        hero["state"] = "down"                    # a wound that fells him or knocks him out (collapse, cannot stand, unconscious)
    else:
        _hero_check(d, hero, C.stop_check(d, hero["nerve"], sev, hero_pain(hero), rng.randint(1, 100) if _checks(d, sev, shock) else 0,
                                          hero_blood(d, hero)[0] / hero_blood(d, hero)[1], shock))
    t.setdefault("heroes", []).append({"hero": hero["id"], "name": hero["name"], "sev": sev, "loc": h["location"],
                                        "graze": h["graze"], "state": hero["state"]})


def _checks(d: Data, sev: str, shock: bool) -> bool:
    """Whether a wound calls for the stop check (so its die is rolled)."""
    return shock and sev in d.wounds["combat"]["stop_check"]["severities"]


def _hero_check(d: Data, hero: dict, res: dict | None) -> None:
    """A stop check's result on a hero: out puts him down; defend only or stunned holds him
    for his next exchange (a worse hold replaces a milder one)."""
    if not res or res["passed"]:
        return
    if res["state"] == "out":
        hero["state"] = "down"
        return
    order = list(d.wounds["combat"]["states"])
    if not hero.get("held") or order.index(res["state"]) >= order.index(hero["held"]["state"]):
        hero["held"] = {"state": res["state"], "left": 2}


def _held(hero: dict) -> str | None:
    """defend_only or stunned while a stop check holds him, else None."""
    h = hero.get("held")
    return h["state"] if h and h["left"] > 0 else None


def hero_pain(hero: dict) -> int:
    """Pain steps: the wounds he came with and those he took here."""
    return hero.get("old_pain", 0) + sum(w.get("pain", 0) for w in hero.get("wounds", []))


def hero_blood(d: Data, hero: dict) -> tuple:
    """(Blood left, his pool)."""
    pool = hero.get("pool") or d.wounds["tracking"]["blood_pool"]
    return hero.get("blood", pool), pool


def _threshold(d: Data, frac: float) -> dict | None:
    return next((t for t in sorted(d.wounds["tracking"]["thresholds"], key=lambda t: t["at"]) if frac <= t["at"]), None)


def hero_penalties(d: Data, hero: dict) -> tuple:
    """(% off his attack, % off his defence, flags), as the roller's penalties: pain (to the cap)
    and Blood lost; his wounds' impairments, the ones he came with (old) and those taken here
    (combat.impair, by his weapon hand); his sickness (sick: disease.yaml in_fight)."""
    C_, T = d.wounds["combat"], d.wounds["tracking"]
    blood, pool = hero_blood(d, hero)
    ws = (hero.get("old") or [{"loc": None, "pain": hero.get("old_pain", 0), "impair": []}]) + hero.get("wounds", [])
    pain = min(sum(w.get("pain", 0) for w in ws), T["pain_cap"]) * C_["pain_step"]
    attack, defence, flags = pain, pain, set()
    th = _threshold(d, blood / pool)
    if th:
        attack, defence = attack + th.get("penalty", 0), defence + th.get("penalty", 0)
        flags |= {f for f in ("down", "incapacitated") if th.get(f)}
    a, df, f = _impairments(d, ws, hero.get("hand", "R"))
    rule = (d.disease.get("in_fight") or {}).get(hero.get("sick") or "", {})
    flags |= f | {k for k in ("defend_only", "out") if rule.get(k)}
    attack += a + rule.get("penalty", 0)
    defence += df + rule.get("penalty", 0)
    return min(attack, C_["cap"]), min(defence, C_["cap"]), sorted(flags)


IMPAIR_FLAGS = ("down", "off_hand", "no_shield", "incapacitated")


def _impairments(d: Data, ws: list, hand: str) -> tuple:
    """(% off attack, % off defence, flags) from the impairments of wounds ws ({loc, impair}),
    each counted once (an arm's by which arm it is), as gravewounds.combat.penalties."""
    attack = defence = 0
    seen, flags = set(), set()
    for key, eff in (_impair_effect(d, w, imp, hand) for w in ws for imp in w.get("impair") or []):
        if key in seen:
            continue
        seen.add(key)
        attack, defence = attack + eff.get("attack", 0), defence + eff.get("defence", 0)
        flags |= {f for f in IMPAIR_FLAGS if eff.get(f)}
    if any(k[0] in d.wounds["combat"].get("one_arm", ()) for k in seen):   # an arm hurt: no two-handed weapon
        flags.add("one_arm")
    return attack, defence, flags


def _impair_effect(d: Data, w: dict, imp: str, hand: str) -> tuple:
    """(key, effect) of impairment imp on wound w: an arm's impairment by which arm it is
    (the shield arm if the wound is on the arm that is not his weapon hand)."""
    rule = d.wounds["combat"]["impair"].get(imp, {})
    if "weapon_arm" not in rule and "shield_arm" not in rule:
        return (imp, None), rule
    loc = d.loc.get(w["loc"]) or {}
    arm = "shield_arm" if loc.get("zone") == "arms" and loc.get("side") in ("L", "R") and loc["side"] != hand else "weapon_arm"
    return (imp, arm), rule.get(arm, {})


def _heroes_after(d: Data, us: list, rng, quiet: list | None = None, cautery: bool = False) -> list:
    """End of an exchange for every hero not dead and still on the field: a hold wears off,
    first aid if his unit had a quiet exchange (quiet[i]; cautery: the battle's era cauterises),
    he bleeds, his Blood's thresholds can put him down, and pain above the cap calls for a stop
    check. Then bearers due back rejoin their units."""
    log = []
    for i, u in enumerate(us):
        for hero in u.get("heroes", []):
            if hero["state"] == "dead" or _off_field(hero):   # left behind or carried back: out of the battle
                continue
            if quiet and quiet[i]:
                log += [{"kind": "heroaid", "unit": i, **x} for x in [_first_aid(d, hero, rng, _healer(d, u), cautery)] if x]
            line = _hero_after(d, hero, rng)
            if line:
                log.append({"kind": "herobled", "unit": i, **line})
    return log + _bearers_back(us)


def cauterises(d: Data, table: str) -> bool:
    """Whether the battle's era cauterises wounds a tourniquet cannot reach (by its wound
    table's war: heroes.cautery.battles)."""
    return (d.tables.get(table) or {}).get("battle") in d.units["heroes"]["cautery"]["battles"]


def hero_fates(d: Data, units: list, table: str, rng) -> list:
    """After the battle, each hero still on the field who cannot leave it with his unit: left
    behind, or down with a unit that broke, fled or was destroyed. His own side holds the field
    if it has a unit still standing (or neither side has): he is found. Otherwise d100 at or
    under heroes.quarter % for the war makes him a prisoner, else he is killed. -> [{unit, hero,
    name, fate (found, prisoner or killed), roll, chance}], unit by unit."""
    Q, out = d.units["heroes"]["quarter"], []
    up = {u["side"] for u in units if u["men"] > 0 and u["state"] in ("steady", "shaken")}
    chance = Q.get((d.tables.get(table) or {}).get("battle"), Q["default"])
    for i, u in enumerate(units):
        gone = u["men"] <= 0 or u["state"] not in ("steady", "shaken")
        for h in u.get("heroes", []):
            if h["state"] == "dead" or h.get("carried") or not (h.get("left") or (gone and h["state"] == "down")):
                continue
            if u["side"] in up or not up:
                out.append({"unit": i, "hero": h["id"], "name": h["name"], "fate": "found"})
                continue
            roll = rng.randint(1, 100)
            out.append({"unit": i, "hero": h["id"], "name": h["name"], "fate": "prisoner" if roll <= chance else "killed", "roll": roll, "chance": chance})
    return out


def _off_field(hero: dict) -> bool:
    """Left behind, or carried to the rear: out of the battle."""
    return bool(hero.get("left") or hero.get("carried"))


def _bearers_back(us: list) -> list:
    """Each party of bearers counts down an exchange; due back, it rejoins its unit if the
    unit still stands (steady or shaken), else stays at the rear. -> log lines."""
    log = []
    for i, u in enumerate(us):
        if not u.get("away"):
            continue
        due = [dict(a, left=a["left"] - 1) for a in u["away"]]
        back = sum(a["men"] for a in due if a["left"] <= 0) if u["state"] in ("steady", "shaken") and u["men"] > 0 else 0
        u["away"] = [a for a in due if a["left"] > 0 or not back]
        if back:
            u["men"] += back
            log.append({"kind": "bearers", "unit": i, "men": back})
    return log


def carry_back(d: Data, units: list, i: int, hero_id) -> str | None:
    """Unit i sends `bearers` of its men to carry hero hero_id to the rear: he leaves the
    battle (safe), and they come back after `back_after` exchanges. -> None, or why not."""
    H, u = d.units["heroes"], units[i]
    hero = next((h for h in u.get("heroes", []) if h["id"] == hero_id), None)
    if hero is None or not lamed(d, hero):
        return "he can walk, or is not with the unit"
    if u["state"] not in ("steady", "shaken"):
        return "the unit is running"
    if u["men"] <= H["bearers"]:
        return f"the unit has not {H['bearers']} men to spare"
    hero["carried"] = True
    u["men"] -= H["bearers"]
    u["away"] = [*u.get("away", []), {"men": H["bearers"], "left": H["back_after"]}]
    return None


def _healer(d: Data, u: dict) -> tuple | None:
    """(Leechcraft, name) of unit u's best healer: its heroes still up with Leechcraft, and its
    medics (heroes.medic % by their quality) while it has men; or None (his comrades bind as
    best they can). A hero is preferred to medics as good."""
    up = [(h["leech"], h["name"]) for h in u.get("heroes", []) if h["state"] == "up" and not _off_field(h) and h.get("leech") is not None]
    if u.get("medics") and u["men"] > 0:
        up.append((d.units["heroes"]["medic"][u.get("medic_quality") or u["quality"]], "the medics"))
    if not up:
        return None
    return max(up, key=lambda x: x[0])


def _first_aid(d: Data, hero: dict, rng, healer: tuple | None = None, cautery: bool = False) -> dict | None:
    """First aid in a quiet exchange on his worst-bleeding wound, from this battle or one he
    came with (old, with its bleed): the healer's Leechcraft % (else heroes.first_aid %); a
    success tourniquets an arm or leg bleeding heroes.tourniquet_from or more (it stops), or
    binds combat.first_aid.bind steps (1 with no healer). Where a tourniquet cannot go, a
    wound bleeding heroes.cautery.from_bleed or more is cauterised in an era that did
    (cautery): it stops, at heroes.cautery.pain more pain unless a healer did it. -> a log
    line, or None."""
    ws = [w for w in hero["wounds"] if w.get("bleed", 0) > 0] + [w for w in hero.get("old") or [] if w.get("bleed", 0) > 0]
    if not ws:
        return None
    w, H = max(ws, key=lambda x: x["bleed"]), d.units["heroes"]
    line = {"hero": hero["id"], "name": hero["name"], "loc": w["loc"], **({"by": healer[1]} if healer else {})}
    if rng.randint(1, 100) > (healer[0] if healer else H["first_aid"]):
        return {**line, "stopped": False, "bleed": w["bleed"]}
    limb = (d.loc.get(w["loc"]) or {}).get("zone") in ("arms", "legs")
    if limb and w["bleed"] >= H["tourniquet_from"]:
        w["bleed"], how = 0, "tourniquet"
    elif cautery and not limb and w["bleed"] >= H["cautery"]["from_bleed"]:
        w["bleed"], how = 0, "cauterise"
        if not healer:
            w["pain"] = min(d.wounds["tracking"]["pain_cap"], w.get("pain", 0) + H["cautery"]["pain"])
            _sum_old_pain(hero, w)
    else:
        w["bleed"], how = max(0, w["bleed"] - (d.wounds["combat"]["first_aid"]["bind"] if healer else 1)), "bind"
    w["aid"] = how                            # the roller marks it treated (on the field) when he goes back
    if any(w is o for o in hero.get("old") or []):
        T = d.wounds["tracking"]
        hero["old_bleed"] = sum(round(T["bleed_per_round"][o.get("bleed", 0)] * d.units["exchange_rounds"]) for o in hero["old"])
    return {**line, "stopped": True, "bleed": w["bleed"], "how": how}


def _sum_old_pain(hero: dict, w: dict) -> None:
    """An old wound's pain changed: his old pain is theirs again."""
    if any(w is o for o in hero.get("old") or []):
        hero["old_pain"] = sum(o.get("pain", 0) for o in hero["old"])


def _hero_after(d: Data, hero: dict, rng) -> dict | None:
    """One hero's end of an exchange; a log line if he crossed a Blood threshold or went down."""
    T = d.wounds["tracking"]
    if hero.get("held"):
        hero["held"]["left"] -= 1
    blood, pool, was_up = *hero_blood(d, hero), hero["state"] == "up"
    lost = hero.get("old_bleed", 0) + sum(round(T["bleed_per_round"][w.get("bleed", 0)] * d.units["exchange_rounds"]) for w in hero["wounds"])
    if not lost and not (was_up and hero_pain(hero) > T["pain_cap"]):
        return None
    before = _threshold(d, blood / pool)
    hero["blood"] = max(0, blood - lost)
    after = _threshold(d, hero["blood"] / pool)
    if was_up and after and (after.get("down") or after.get("incapacitated")):
        hero["state"] = "down"
    if hero["blood"] <= 0:
        hero["dying"] = True
    if hero["state"] == "up" and hero_pain(hero) > T["pain_cap"]:
        _hero_check(d, hero, C.pain_check(d, hero["nerve"], hero_pain(hero), rng.randint(1, 100), hero["blood"] / pool))
    if after is before and not (was_up and hero["state"] != "up"):
        return None
    return {"hero": hero["id"], "name": hero["name"], "lost": lost, "blood": hero["blood"], "pool": pool, "state": hero["state"]}


def _heroes(u: dict, roles: tuple) -> list:
    return [h for h in u.get("heroes", []) if h["state"] == "up" and not _off_field(h) and h["role"] in roles]


def _acting(d: Data, u: dict, roles: tuple) -> list:
    """Heroes up who strike or shoot this exchange (_strikes)."""
    return [h for h in _heroes(u, roles) if _strikes(d, h)]


def _strikes(d: Data, hero: dict) -> bool:
    """Not held by a stop check, not too sick to do more than defend (defend_only), and not
    hurt in either arm (one_arm) with a two-handed weapon: he can strike or shoot."""
    if _held(hero) or hero.get("defend_only"):
        return False
    return not (d.weapons.get(hero["weapon"], {}).get("two_handed") and "one_arm" in hero_penalties(d, hero)[2])


def lamed(d: Data, hero: dict) -> bool:
    """A hero who slows his unit: not dead or left behind, and down (carried) or with a
    wound (from this battle or one he came with) that lames him (heroes.lamed)."""
    if hero["state"] == "dead" or _off_field(hero):
        return False
    lame = d.units["heroes"]["lamed"]
    return hero["state"] == "down" or any(i in lame for w in (hero.get("old") or []) + hero.get("wounds", []) for i in w.get("impair") or [])


def front_men(d: Data, u: dict) -> int:
    """Men in the unit's front rank: the ones a blow on its front falls among."""
    rows, men = footprint(d, u), men_by_hex(d, u)
    return sum(min(form(d, u)["abreast"], men[k]) for k in range(len(rows[0]))) if rows else 0


def _exposure(d: Data, u: dict, rout: bool, missile: bool = False) -> tuple:
    """(hero, chance) for each hero of unit u a blow on it may fall on."""
    if rout or missile:
        return tuple((h, 1 / max(1, u["men"])) for h in _heroes(u, ("front", "ranged", "behind" if rout else "")))
    return tuple((h, min(1, d.units["heroes"]["exposure"] / max(1, front_men(d, u)))) for h in _heroes(u, ("front", "ranged")))


def _hero_side(u: dict, hero: dict, table: str, d: Data | None = None) -> dict:
    """A hero as a fighting side: his own skill, less his wounds' penalty (d given)."""
    pen = hero_penalties(d, hero)[0] if d else 0
    return {"table": table, "weapon": hero["weapon"], "kit": hero.get("kit"), "quality": u["quality"], "skill": hero["attack"] - pen}


def leader_state(u: dict) -> str | None:
    """up if a leader hero of the unit is up, down if it has leaders and none is, else None."""
    ls = [h for h in u.get("heroes", []) if h.get("leader")]
    if not ls:
        return u.get("leader")
    return "up" if any(h["state"] == "up" and not _off_field(h) for h in ls) else "down"


def morale(d: Data, unit: dict, roll: int) -> dict:
    """A unit's check after an exchange. unit: {quality, start, down (all so far), lost (this
    exchange), dealt (enemy put down by it this exchange), men (before this exchange), state
    (steady, shaken or broken), leader (None, up or down), flanked, friends (a steady friend
    beside it), contact}. Returns {check (bool),
    target, state}."""
    M = d.units["morale"]
    if unit["state"] == "broken":
        return {"check": False, "target": None, "state": "broken"}
    losing = unit.get("lost", 0) > unit.get("dealt", 0) and unit.get("contact")
    struck = (unit["down"] >= M["trigger"] * unit["start"] or unit["lost"] >= M["shock"] * max(1, unit["men"])
              or unit.get("flanked") or losing)
    rally = unit["state"] == "shaken" and not unit.get("contact")
    if not struck and not rally:
        return {"check": False, "target": None, "state": unit["state"]}
    target = quality(d, unit["quality"])["nerve"] + _morale_mods(M["mods"], unit)
    if roll <= target:
        return {"check": True, "target": target, "state": "steady" if rally and not struck else unit["state"]}
    return {"check": True, "target": target, "state": _failed(M, unit, roll - target)}


def _failed(mo: dict, unit: dict, by: int) -> str:
    """A failed check: a steady unit is shaken, unless it fails badly while flanked or with
    half its men down; a shaken unit breaks."""
    if unit["state"] == "shaken":
        return "broken"
    hard = unit.get("flanked") or unit["down"] >= unit["start"] / 2
    return "broken" if hard and by > mo["shaken_by"] else "shaken"


def _morale_mods(mods: dict, unit: dict) -> int:
    m = 0
    if unit.get("leader") == "up":
        m += mods["leader"]
    elif unit.get("leader") == "down":
        m += mods["leader_down"]
    if unit["down"] >= unit["start"] / 2:
        m += mods["heavy"]
    if unit.get("flanked"):
        m += mods["flank"]
    if unit.get("friends"):
        m += mods["veteran_friends"]
    if unit.get("state") == "steady":
        m += mods["in_order"]
    if unit.get("dug"):
        m += mods.get("dug_in", 0)
    m -= min(mods["losing_cap"], mods["losing_per_man"] * max(0, unit.get("lost", 0) - unit.get("dealt", 0)))
    return m


def fight(d: Data, a: dict, b: dict, rng: random.Random, exchanges: int = 60, front: int = 30) -> dict:
    """Two units in a straight melee, front to front, until one breaks or `exchanges` pass;
    then the winner pursues for one exchange. a and b: sides plus {men, reach}. For tuning
    and examples: {exchanges, a: {...}, b: {...}, broke}."""
    st = {k: {"men": u["men"], "start": u["men"], "down": 0, "dead": 0, "hits": 0, "state": "steady",
              "quality": u["quality"], "leader": u.get("leader")} for k, u in (("a", a), ("b", b))}
    n = 0
    for n in range(1, exchanges + 1):
        ta = melee(d, a, b, min(fighters(d, front, a.get("reach", 1)), st["a"]["men"]), rng, shaken=st["a"]["state"] == "shaken")
        tb = melee(d, b, a, min(fighters(d, front, b.get("reach", 1)), st["b"]["men"]), rng, shaken=st["b"]["state"] == "shaken")
        st["a"]["dealt"], st["b"]["dealt"] = ta["down"], tb["down"]
        for side, t in (("b", ta), ("a", tb)):
            s = st[side]
            s["lost"], s["hits"] = t["down"], s["hits"] + t["hits"]
            s["down"] += t["down"]
            s["dead"] += t["dead"]
        for side in ("a", "b"):
            s = st[side]
            s["state"] = morale(d, {**s, "contact": True}, rng.randint(1, 100))["state"]
            s["men"] -= s["lost"]
        broke = [k for k in ("a", "b") if st[k]["state"] == "broken"]
        if broke:
            loser = broke[0]
            _pursue(d, (b, a) if loser == "a" else (a, b), st["b" if loser == "a" else "a"], st[loser], rng)
            return {"exchanges": n, "a": st["a"], "b": st["b"], "broke": loser}
    return {"exchanges": n, "a": st["a"], "b": st["b"], "broke": None}


def _pursue(d: Data, sides: tuple, ws: dict, ls: dict, rng: random.Random) -> None:
    """The winner cuts down the fleeing loser for rout.exchanges exchanges, all its men striking."""
    w, lo = sides
    for _ in range(d.units["rout"]["exchanges"]):
        if ls["men"] <= 0:
            return
        t = melee(d, w, lo, ws["men"], rng, rout=True)
        cut = min(t["down"], ls["men"])
        ls["down"] += cut
        ls["dead"] += min(t["dead"], cut)
        ls["men"] -= cut


class SeededDice:
    """Repeatable dice for simulations and examples (Park-Miller minimal standard), with the
    two calls the rules use: randint(a, b) and random(). Play uses real random dice."""

    def __init__(self, seed: int):
        self.state = max(1, seed % 2147483647)

    def _next(self) -> int:
        self.state = self.state * 16807 % 2147483647
        return self.state

    def randint(self, a: int, b: int) -> int:
        return a + self._next() % (b - a + 1)

    def random(self) -> float:
        return self._next() / 2147483647


EXAMPLES = [   # (label, a, b) for `python3 -m gravewounds units`: 120 men a side, 30 abreast
    ("Equal regulars, no armour", {"quality": "regular", "kit": "none"}, {"quality": "regular", "kit": "none"}),
    ("Equal regulars in jacks", {"quality": "regular", "kit": "jack_sallet"}, {"quality": "regular", "kit": "jack_sallet"}),
    ("Regulars v greens, in jacks", {"quality": "regular", "kit": "jack_sallet"}, {"quality": "green", "kit": "jack_sallet"}),
    ("Bills v swords, in jacks", {"quality": "regular", "kit": "jack_sallet", "weapon": "bill", "reach": 2},
     {"quality": "regular", "kit": "jack_sallet"}),
    ("Veterans in mail v unarmoured regulars", {"quality": "veteran", "kit": "hauberk"}, {"quality": "regular", "kit": "none"}),
]


def examples(d: Data, table: str, runs: int, seed: int) -> list[dict]:
    """The example matchups, each fought `runs` times: medians of minutes to a break and of
    men down on each side, and how often each side broke."""
    out = []
    for label, a, b in EXAMPLES:
        side = lambda x: {"table": table, "weapon": "sword", "men": 120, "reach": 1, **x}
        rs = [fight(d, side(a), side(b), SeededDice(seed + i), exchanges=120) for i in range(runs)]
        done = [r for r in rs if r["broke"]]
        med = lambda xs: sorted(xs)[len(xs) // 2] if xs else 0
        out.append({"label": label, "minutes": med([r["exchanges"] for r in rs]),
                    "a_broke": sum(1 for r in rs if r["broke"] == "a"), "b_broke": sum(1 for r in rs if r["broke"] == "b"),
                    "winner_down": med([r["b" if r["broke"] == "a" else "a"]["down"] for r in done]),
                    "loser_down": med([r[r["broke"]]["down"] for r in done])})
    return out


def pace(d: Data, table: str, kit: str, exchanges: int, seed: int) -> dict:
    """% of the men in contact hit, and put down, a minute: regular swordsmen, front to front."""
    rng, side = SeededDice(seed), {"table": table, "weapon": "sword", "quality": "regular"}
    hits = down = 0
    for _ in range(exchanges):
        t = melee(d, side, {**side, "kit": kit}, 10, rng)
        hits, down = hits + t["hits"], down + t["down"]
    return {"hit": 100 * hits / (10 * exchanges), "down": 100 * down / (10 * exchanges)}


# ---------- the field map ----------
# Hexes are [col, row], pointy-top, odd rows shifted right, as on the other maps. A unit is
# {id, name, side, men, start, down, dead, quality, weapon, kit, formation (close or open),
# mounted, width (hexes of front), pos (the middle of its front row), facing (0-5),
# state (steady, shaken, broken or fled), charged}. Facing f points at the corner between
# hexsides f and f+1 (E, NE, NW, W, SW, SE = 0-5): the front is those two sides, the flanks
# the sides along the line (f+2, f+5), the rear the other two (f+3, f+4).

AX = [(1, 0), (1, -1), (0, -1), (-1, 0), (-1, 1), (0, 1)]   # E, NE, NW, W, SW, SE (axial)


def step(h, dirn: int, n: int = 1) -> list:
    """The hex n steps from h in direction dirn."""
    q, r = h[0] - (h[1] - (h[1] & 1)) // 2, h[1]
    dq, dr = AX[dirn % 6]
    q, r = q + dq * n, r + dr * n
    return [q + (r - (r & 1)) // 2, r]


def _cube(h) -> tuple:
    q = h[0] - (h[1] - (h[1] & 1)) // 2
    return q, h[1], -q - h[1]


def hdist(a, b) -> int:
    x, y = _cube(a), _cube(b)
    return max(abs(x[0] - y[0]), abs(x[1] - y[1]), abs(x[2] - y[2]))


ray = C.ray   # the hexes on a line (gravewounds.combat)


def arc(facing: int, dirn: int) -> str:
    """front, flank or rear: where direction dirn falls for a unit with this facing."""
    k = (dirn - facing) % 6
    if k in (0, 1):
        return "front"
    return "flank" if k in (2, 5) else "rear"


def form(d: Data, u: dict) -> dict:
    """A unit's formation; a vehicle unit's is one vehicle a hex, at its kind's move."""
    F = d.units["formations"][u["formation"]]
    K = vehicle_kind(d, u)
    return {**F, "per_hex": K["crew"], "move": K["move"]} if K else F


def vehicle_kind(d: Data, u: dict) -> dict | None:
    """A vehicle unit's kind (units.yaml vehicles.kinds), or None for men on foot or horse."""
    return d.units["vehicles"]["kinds"][u["vehicle"]] if u.get("vehicle") else None


def vehicles_left(d: Data, u: dict, lost: int = 0) -> int:
    """How many vehicles a vehicle unit still has, its crews' losses `lost` this exchange taken off."""
    K = vehicle_kind(d, u)
    return math.ceil(max(0, u["men"] - lost) / K["crew"]) if K else 0


def armour_of(d: Data, u: dict) -> dict | None:
    """A vehicle unit's armour (units.yaml vehicles.armour), or None."""
    K = vehicle_kind(d, u)
    return d.units["vehicles"]["armour"][K["armour"]] if K else None


def hurts_armour(d: Data, weapon: str) -> bool:
    """Whether a man's weapon can knock out a vehicle (vehicles.anti_armour)."""
    return weapon in ((d.units.get("vehicles") or {}).get("anti_armour") or {})


def bearing(t, h) -> int:
    """The direction (0-5, as step) from hex t that points most nearly at hex h (the first of equals)."""
    a, b = _cube(t), _cube(h)
    v = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    dots = [v[0] * q + v[1] * r + v[2] * (-q - r) for q, r in AX]
    return dots.index(max(dots))


def kill_chance(d: Data, u: dict, row: str, h, t) -> int:
    """% that a hit from hex h on vehicle unit u (at its hex t) knocks a vehicle out: its armour's
    `row` %, times vehicles.aspect for a flank or rear shot (by u's facing), to 100 at most."""
    p = armour_of(d, u)[row]
    side = arc(u["facing"], bearing(t, h)) if h is not None and t is not None and list(h) != list(t) else "front"
    return min(100, int(p * (d.units["vehicles"].get("aspect") or {}).get(side, 1)))


def _harm(d: Data, u: dict, n: int, lost: int, rng) -> dict:
    """n hits on vehicle unit u that did not knock one out: each may immobilise a vehicle or put
    its main gun out (vehicles.damage), up to the vehicles it has left. -> {immobilised, gun}."""
    D, left, out = d.units["vehicles"].get("damage") or {}, vehicles_left(d, u, lost), {"immobilised": 0, "gun": 0}
    for _ in range(n):
        r = rng.randint(1, 100)
        if r <= D.get("immobilised", 0):
            out["immobilised"] += 1
        elif r <= D.get("immobilised", 0) + D.get("gun", 0):
            out["gun"] += 1
    u["immobile"] = min(left, u.get("immobile", 0) + out["immobilised"])
    u["gunless"] = min(left, u.get("gunless", 0) + out["gun"])
    return out


def footprint(d: Data, u: dict) -> list:
    """The unit's hexes as rows, front row first; each row runs along the line. Empty if it
    has no men left or has fled."""
    if u["men"] <= 0 or u["state"] == "fled":
        return []
    n = math.ceil(u["men"] / form(d, u)["per_hex"])
    w = max(1, min(u["width"], n))
    v = u["facing"]
    start, rows, k = step(u["pos"], v + 2, (w - 1) // 2), [], 0
    while k < n:
        base = step(start, v + 3, len(rows))
        row = [step(base, v + 5, i) for i in range(min(w, n - k))]
        k += len(row)
        rows.append(row)
    return rows


def men_by_hex(d: Data, u: dict) -> list:
    """Men in each hex of the footprint, row by row (front hexes full first)."""
    per, out, left = form(d, u)["per_hex"], [], u["men"]
    for row in footprint(d, u):
        for _ in row:
            out.append(min(per, left))
            left -= out[-1]
    return out


def occupancy(d: Data, units: list) -> dict:
    """hex key -> unit index, for every unit on the map."""
    occ = {}
    for i, u in enumerate(units):
        for row in footprint(d, u):
            for h in row:
                occ[f"{h[0]},{h[1]}"] = i
    return occ


def _adjacent_units(d: Data, units: list, occ: dict, i: int) -> list:
    """Indexes of the units touching unit i (sorted)."""
    out = set()
    for row in footprint(d, units[i]):
        for h in row:
            for dirn in range(6):
                j = occ.get("{0},{1}".format(*step(h, dirn)))
                if j is not None and j != i:
                    out.add(j)
    return sorted(out)


def in_contact(d: Data, units: list, occ: dict, i: int) -> bool:
    return any(units[j]["side"] != units[i]["side"] for j in _adjacent_units(d, units, occ, i))


def strikes(d: Data, units: list, field: dict | None = None) -> list:
    """Who strikes whom this exchange: [{att, dfd, men, situation, rout}], in a fixed order.
    Each front hex of a unit not broken strikes the enemy hex across its front (its first
    front side that has one) with its front rank, two ranks with reach-2 weapons. A broken
    unit is struck instead by every man of each enemy unit touching it. On a field with works
    and ground (see field_ground), a blow across a palisade or wall comes only from reach-2
    weapons, in the front rank; attacking up a bank, ditch or wall or onto high ground costs
    `penalty`; and horses get no charge into stakes or felled trees (`stakes`)."""
    occ, groups = occupancy(d, units), {}
    for i, u in enumerate(units):
        if not _out(u):
            _strike_groups(d, units, occ, i, groups, field)
    out = [{"att": i, "dfd": j, "men": n, "situation": sit, "rout": False, "penalty": pen, "stakes": stk}
           for (i, j, sit, pen, stk), n in sorted(groups.items()) if not units[i].get("vehicle") and not units[j].get("vehicle")]
    for j, b in enumerate(units):
        if b["state"] == "broken" and b["men"] > 0 and not b.get("vehicle"):
            out += [{"att": i, "dfd": j, "men": units[i]["men"], "situation": "rear", "rout": True}
                    for i in _adjacent_units(d, units, occ, j)
                    if units[i]["side"] != b["side"] and units[i]["state"] not in ("broken", "fled") and not units[i].get("vehicle")]
    return out


def pike_front(d: Data, u: dict) -> bool:
    """Whether a unit presents a front of pikes to horse: steady, in a pike formation, with a pike."""
    P = d.units["melee"]["pikes"]
    return u["state"] == "steady" and u["formation"] in P["formations"] and melee_weapon(d, u) in P["weapons"] and not u.get("mounted")


def bunker_at(d: Data, field: dict | None, h) -> dict | None:
    """The intact bunker (a hex work assault.works names) in hex h, or None."""
    hexes = ((_works(field) or {}).get("hexes") or {})
    it = hexes.get(f"{h[0]},{h[1]}") if hexes else None
    return it if it and it["type"] in d.units["assault"]["works"] and C.intact(d, "hex", it) else None


def in_bunker(d: Data, field: dict | None, u: dict) -> bool:
    """Whether any of a unit's hexes is in an intact bunker."""
    return bool(field) and any(bunker_at(d, field, h) for row in footprint(d, u) for h in row)


def _out(u: dict) -> bool:
    """Broken, fled or with no men: out of the fight for striking and shooting."""
    return u["state"] in ("broken", "fled") or u["men"] <= 0


def _strike_groups(d: Data, units: list, occ: dict, i: int, groups: dict, field: dict | None = None) -> None:
    """Add unit i's front hexes' strikes to groups {(i, j, situation, penalty, stakes): men}."""
    u = units[i]
    rows, men = footprint(d, u), men_by_hex(d, u)
    reach = d.weapons[melee_weapon(d, u)].get("reach", 1)
    abreast = form(d, u)["abreast"]
    per, busy = abreast * min(reach, form(d, u)["ranks"]), breaching(d, field, u)
    for k, h in enumerate(rows[0] if rows else []):
        hit = _struck_hex(units, occ, u, h)
        if hit is None:
            continue
        j, dirn = hit
        x = step(h, dirn)
        if bunker_at(d, field, h) or bunker_at(d, field, x):
            continue                                  # no blows into or out of an intact bunker: it must be stormed
        blocked, pen, stk = _across(d, field, u, h, x, reach)
        n = _hex_strikers(men[k], per, abreast, reach if blocked else 0, k in busy)
        if n > 0:
            key = (i, j, arc(units[j]["facing"], dirn + 3), pen, stk)
            groups[key] = groups.get(key, 0) + n


def _hex_strikers(men: int, per: int, abreast: int, blocked_reach: int, busy: bool) -> int:
    """Men of one front hex who strike: per; across a wall (blocked_reach: the weapon's reach,
    else 0) only the front rank of reach-2 weapons; less the front rank if it is breaching."""
    n = min(per, men)
    if blocked_reach:
        n = min(abreast, men) if blocked_reach >= 2 else 0
    if busy:
        n = max(0, n - min(abreast, men))          # the front rank is hacking at the works
    return n


# ---------- the field: ground, works and weather ----------
# field: {ground: {hex key: kind of ground (units.yaml ground; open if not given)}, works:
# {edges, hexes} as on the battle map (gravewounds/combat.py), weather: {cond, wind, ground:
# {mud, snow}} or None, size: [cols, rows]}. None: open ground, no works, no weather.

def _size(d: Data, field: dict | None) -> tuple:
    if field and field.get("size"):
        return tuple(field["size"])
    return d.units["map"]["cols"], d.units["map"]["rows"]


def battlefield(d: Data, fid: str) -> dict:
    """A battlefield from data/fields as a field: the ground from its rows of letters (units.yaml
    ground keys), its works laid on the hexes and hex sides, its weather and size."""
    f, keys = d.fields[fid], {g["key"]: k for k, g in d.units["ground"].items()}
    ground = {f"{c},{r}": keys[ch] for r, row in enumerate(f["rows"]) for c, ch in enumerate(row.strip()) if keys[ch] != "open"}
    works = _field_works(d, f.get("works") or {})
    wx = f.get("weather") or {"cond": "fair", "wind": "calm", "ground": {"mud": 0, "snow": 0}}
    out = {"ground": ground, "works": works, "weather": wx, "size": list(f["size"]), "up": f.get("up", "N")}
    if f.get("lz"):
        out["lz"] = [list(h) for h in f["lz"]]
    if f.get("support"):
        out["support"] = _field_support(d, f)
    return out


def _field_works(d: Data, fw: dict) -> dict:
    """A battlefield's works laid on its hexes and hex sides, none of them begun."""
    works = {"edges": {}, "hexes": {}}
    for w in fw.get("hexes", []):
        for h in w["at"]:
            works["hexes"][C.hkey(h)] = {"type": w["type"], "progress": 0}
    for w in fw.get("edges", []):
        for a, b in w["at"]:
            it = {"type": w["type"], "progress": 0}
            if d.works["edge_works"][w["type"]].get("height"):
                it["high"] = C.hkey(a)
            if w["type"] == "gate":
                it.update({"open": False, "inside": C.hkey(a)})
            works["edges"].setdefault(C.edge_key(a, b), []).append(it)
    return works


def _field_support(d: Data, f: dict) -> list:
    """A battlefield's own fire support, each with its full stock of rounds and no mission yet."""
    K = d.units["indirect"]["kinds"]
    return [{"name": s["name"], "army": s["side"], "side": f["sides"][s["side"]], "kind": s["kind"], "tubes": s["tubes"],
             "rounds": s["tubes"] * K[s["kind"]]["rounds"], "mission": None, **({"place": list(s["place"])} if s.get("place") else {})} for s in f["support"]]


def battlefield_units(d: Data, fid: str) -> list:
    """The armies as drawn up on a battlefield, as units ready to fight (not those that come
    in by air: `lands`)."""
    out = []
    for u in (x for x in d.fields[fid].get("units", []) if "lands" not in x):
        out.append({**u, "start": u["men"], "down": 0, "dead": 0, "hurt": {}, "heroes": [], "state": "steady",
                    "mounted": bool(u.get("mounted")), "charged": False, "leader": None})
    return out


def ground_at(d: Data, field: dict | None, h) -> dict:
    kind = ((field or {}).get("ground") or {}).get(f"{h[0]},{h[1]}", "open")
    return d.units["ground"][kind]


def _works(field: dict | None):
    return (field or {}).get("works")


def _across(d: Data, field: dict | None, u: dict, h, x, reach: int) -> tuple:
    """A blow from hex h at hex x: (blocked: only reach-2 strikes over it, penalty %, stakes:
    horses get no charge into it)."""
    if not field:
        return False, 0, False
    cols, rows = _size(d, field)
    m = C.melee_across(d, _works(field), h, x, reach, cols, rows)
    pen = m["penalty"]
    pen += max(0, height_at(d, field, x) - height_at(d, field, h))
    it = C._hex_item(d, _works(field), x)
    stk = bool(u.get("mounted") and it and C._spec(d, "hex", it).get("no_horse"))
    return m["blocked"], pen, stk


def _struck_hex(units: list, occ: dict, u: dict, h) -> tuple | None:
    """(enemy index, direction) across the first of hex h's front sides with a standing enemy."""
    for dirn in (u["facing"], u["facing"] + 1):
        j = occ.get("{0},{1}".format(*step(h, dirn)))
        if j is not None and units[j]["side"] != u["side"] and units[j]["state"] != "broken":
            return j, dirn
    return None


def _fvec(facing: int) -> tuple:
    a, b = AX[facing % 6], AX[(facing + 1) % 6]
    q, r = a[0] + b[0], a[1] + b[1]
    return q, r, -q - r


def volleys(d: Data, units: list, field: dict | None = None) -> list:
    """Who shoots at whom: [{att, dfd, men, dist, cover, penalty, misfire, reach, from, to,
    over}]. A unit with a missile weapon, not broken and not in contact, shoots at the nearest
    enemy unit in range (and in sight, in the weather, with a line of fire: see line_fire) in
    front of it (ties: the first listed); over: % off for loosing high over units between. Its front hexes'
    first `shoot_ranks` ranks shoot. cover: % off from the works and ground at the nearest
    target hex; penalty and misfire: the weather's (gravewounds.combat.weather_attack)."""
    occ, out = occupancy(d, units), []
    for i, u in enumerate(units):
        if u["state"] in ("broken", "fled") or u["men"] <= 0 or "range" not in d.weapons[u["weapon"]]:
            continue
        if in_contact(d, units, occ, i) and not in_bunker(d, field, u):
            continue
        best, blind = _target(d, units, i, field, occ), False
        if best is None:
            best = _fixed_target(d, units, i, field, occ)
            blind = best is not None
        if best is None:
            continue
        wx = shot_weather(d, field, u["weapon"], best[0], best[2], best[3], _seer(u, blind=blind))
        if wx["blocked"]:
            continue
        up, longer = height_edge(d, field, u["weapon"], best[2], best[3])
        v = {"att": i, "dfd": best[1], "men": _shooters(d, u, field), "dist": best[0], "cover": share_cover(d, field, best[2], units[best[1]]) + ground_cover(d, units[best[1]]),
             "penalty": wx["penalty"] - up, "misfire": wx["misfire"], "reach": wx.get("reach", 0) + longer, "from": best[2], "to": best[3], "height": up,
             "over": line_fire(d, units, occ, field, i, best[1], best[2], best[3], best[0]), "seen": seen_share(d, field, units[best[1]], best[3], u["weapon"])}
        v.update({k: True for k in ("blind", "flash") if wx.get(k)})
        if is_mg(d, u["weapon"]):
            v.update(_beaten(d, units, occ, field, i, best))
        out.append(v)
    return out


def _fixed_target(d: Data, units: list, i: int, field: dict | None, occ: dict):
    """(distance, index, shooter hex, target hex) for a machine gun laid on a fixed line (u.fixed,
    a hex) firing blind in the dark: the nearest enemy with a hex within light.fixed_line.width of
    the line from the middle of its front to that hex, in range and with a line of fire; else None."""
    u = units[i]
    if not u.get("fixed") or not is_mg(d, u["weapon"]) or light_of(d, field) is None:
        return None
    front = footprint(d, u)[0]
    h = front[len(front) // 2]
    n = hdist(h, u["fixed"])
    if n == 0:
        return None
    aim, best = (h, ray(h, u["fixed"], n)[1:], d.weather["light"]["fixed_line"]["width"]), None
    for j, e in enumerate(units):
        if e["side"] != u["side"] and not _out(e) and not e.get("vehicle"):
            best = _nearest_on_line(d, units, (occ, field, i, j), aim, best)
    return best


def _nearest_on_line(d: Data, units: list, ctx: tuple, aim: tuple, best):
    """The nearest hex of unit j on a fixed line (aim: the gun's hex, the line, its width) that
    gun unit i reaches with a line of fire, if nearer than best; else best."""
    occ, field, i, j = ctx
    h, line, width = aim
    for t in (x for row in footprint(d, units[j]) for x in row):
        dist = hdist(h, t)
        if (best is not None and dist >= best[0]) or min(hdist(t, x) for x in line) > width or not _reaches(d, units[i], dist):
            continue
        if line_fire(d, units, occ, field, i, j, h, t, dist) is not None:
            best = (dist, j, h, t)
    return best


def _shooters(d: Data, u: dict, field: dict | None = None) -> float:
    """Who shoots: a machine-gun team's served guns; any other unit's front hexes' first
    shoot_ranks ranks, less the front rank of each hex breaching the works. A pinned unit,
    suppression.fire of them."""
    if is_mg(d, u["weapon"]):
        n = mg_guns(d, u)
    else:
        rows, men, ab = footprint(d, u), men_by_hex(d, u), form(d, u)["abreast"]
        per_hex = ab * min(d.units["shoot_ranks"], form(d, u)["ranks"])
        busy = breaching(d, field, u)
        n = sum(max(0, min(per_hex, men[k]) - (min(ab, men[k]) if k in busy else 0)) for k in range(len(rows[0])))
    return n * d.units["suppression"]["fire"] if u.get("pinned") else n


def is_mg(d: Data, weapon: str) -> bool:
    return weapon in (d.units.get("machine_guns") or {}).get("weapons", [])


def mg_guns(d: Data, u: dict) -> int:
    """A machine-gun team's guns still served: one a crew, while a man of the crew is up."""
    return math.ceil(max(0, u["men"]) / d.units["machine_guns"]["crew"])


def ground_cover(d: Data, u: dict) -> int:
    """% off shots at a unit gone to ground."""
    return d.units["to_ground"]["cover"] if u.get("prone") else 0


def seen_share(d: Data, field: dict | None, u: dict, at, weapon: str | None = None) -> float:
    """The share of aimed shots at unit u (its hex `at` aimed at) that find a man: hidden.seen %
    (hidden.mg_seen % for a machine gun) if it is gone to ground, in a bunker or in ground that
    hides it, else all of them."""
    H = d.units.get("hidden")
    if not H:
        return 1
    if u.get("prone") or in_bunker(d, field, u) or (at is not None and hides_at(d, field, at)):
        return H.get("mg_seen", H["seen"]) / 100 if weapon and is_mg(d, weapon) else H["seen"] / 100
    return 1


def hides_at(d: Data, field: dict | None, h) -> bool:
    """Whether men in hex h are hidden by its ground (`hides`) or a hex work (works.yaml `hides`: a trench)."""
    if ground_at(d, field, h).get("hides"):
        return True
    it = ((_works(field) or {}).get("hexes") or {}).get(f"{h[0]},{h[1]}")
    return bool(it) and bool(d.works.get("hex_works", {}).get(it["type"], {}).get("hides"))


def _beaten(d: Data, units: list, occ: dict, field: dict | None, i: int, best: tuple) -> dict:
    """A machine gun's beaten zone past its target: {behind (unit index or None), beyond (hexes
    past the target), bcover (% off there: ground and going to ground)}."""
    dist, j, h, t = best
    for k, x in enumerate(ray(h, t, dist + d.units["machine_guns"]["beaten"]["beyond"])[dist:]):
        if ground_at(d, field, x).get("stops_shot"):
            break
        b = occ.get(f"{x[0]},{x[1]}")
        if k > 0 and b is not None and b not in (i, j) and not units[b].get("vehicle"):
            return {"behind": b, "beyond": k, "bcover": ground_at(d, field, x).get("cover", 0) + ground_cover(d, units[b]),
                    "bseen": seen_share(d, field, units[b], x, units[i]["weapon"])}
    return {"behind": None, "beyond": 0, "bcover": 0, "bseen": 1}


_SCREENS = {}   # id(field ground) -> (that ground, its size, the hexes that screen): the rules never repaint a field


def _screen_hexes(d: Data, field: dict | None) -> set:
    """The keys ("q,r") of the field's hexes whose ground screens sight (woods, buildings)."""
    g = (field or {}).get("ground") or {}
    hit = _SCREENS.get(id(g))
    if hit is None or hit[0] is not g or hit[1] != len(g):
        hit = (g, len(g), {k for k, v in g.items() if d.units["ground"].get(v, {}).get("screen")})
        _SCREENS[id(g)] = hit
    return hit[2]


def clear_sight(d: Data, field: dict | None, h, t, dist: int, line: list | None = None) -> bool:
    """Whether a man at hex h sees hex t to aim at it: no ground that screens (woods, buildings)
    on the line between as high as where he stands, past the first line_of_fire.see_into hexes
    at either end (he sees out of a screen's edge, and into it). line: ray(h, t, dist), if known."""
    cover = _screen_hexes(d, field)
    if not cover:
        return True
    k = d.units["line_of_fire"].get("see_into", 1)
    line, up = line or ray(h, t, dist), height_at(d, field, h)
    return not any(f"{y[0]},{y[1]}" in cover and height_at(d, field, y) >= up for y in line[1 + k:len(line) - 1 - k])


def shot_weather(d: Data, field: dict | None, weapon: str, dist: int, h=None, t=None, seer: dict | None = None) -> dict:
    """The weather's effect on a shot `dist` field hexes away, from hex h to hex t (for the
    wind's direction): {blocked, penalty, misfire, reach}. Smoke on the line blocks it, and so
    do woods and buildings between (clear_sight), unless it is fired blind. seer:
    the shooter in the dark, {kit, blind} (see in_the_dark)."""
    line = ray(h, t, dist) if h is not None and t is not None and ((field or {}).get("smoke") or _screen_hexes(d, field)) else None
    if line and smoked(field, line) and not sees_smoke(d, seer):
        return {"blocked": "Smoke: no one can see to shoot through it.", "penalty": 0, "misfire": 0, "reach": 0}
    if line and not (seer or {}).get("blind") and not clear_sight(d, field, h, t, dist, line):
        return {"blocked": "Woods or buildings between: no one can see to aim through them.", "penalty": 0, "misfire": 0, "reach": 0}
    if is_gun(d, weapon):
        return gun_weather(d, field, dist, h, t, seer)
    return in_the_cold(d, field, weapon, in_the_dark(d, field, dist, t, C.weather_attack(d, (field or {}).get("weather"), weapon, 0 if (seer or {}).get("blind") else dist * d.units["range_scale"], h, t, _up(field)), seer))


def cold_of(d: Data, field: dict | None) -> dict | None:
    """The field's cold (weather.cold, a weather.yaml cold level), or None."""
    return ((d.weather or {}).get("cold") or {}).get("levels", {}).get(((field or {}).get("weather") or {}).get("cold") or "")


def in_the_cold(d: Data, field: dict | None, weapon: str, out: dict) -> dict:
    """In hard cold the automatic weapons (weather.yaml cold.jams) misfire the level's `jam` % more."""
    L = cold_of(d, field)
    if L and not out["blocked"] and weapon in d.weather["cold"]["jams"]:
        out["misfire"] = min(100, out["misfire"] + L["jam"])
    return out


def light_of(d: Data, field: dict | None) -> dict | None:
    """The field's light (weather.light, from weather.yaml light.levels), or None by day."""
    levels = ((d.weather or {}).get("light") or {}).get("levels") or {}
    L = levels.get(((field or {}).get("weather") or {}).get("light") or "day")
    return L if L and (L.get("sight") is not None or L.get("aim")) else None


def lit(field: dict | None, h) -> bool:
    """Whether a flare or an illumination round lights hex h: field.lit is [{at, radius, left}]."""
    return h is not None and any(hdist(h, x["at"]) <= x["radius"] for x in (field or {}).get("lit") or [])


def in_the_dark(d: Data, field: dict | None, dist: int, t, out: dict, seer: dict | None = None) -> dict:
    """The dark on a shot `dist` field hexes at hex t (none if it is lit): no aiming beyond the
    light's sight (a shooter's night sight further: dark_sight), and its aim % off; a target
    that fired in the dark is seen by its flashes out to light.flash (out["flash"]); a machine
    gun firing blind down a fixed line (seer["blind"]) needs no sight, light.fixed_line.aim % off."""
    L = light_of(d, field)
    if out["blocked"] or L is None or lit(field, t):
        return out
    if (seer or {}).get("blind"):
        out["penalty"] += d.weather["light"]["fixed_line"]["aim"]
        out["blind"] = True
        return out
    sight, aim = dark_sight(d, L, night_device(d, seer))
    if sight is not None and dist * d.units["range_scale"] > sight:
        if not (flashing(field, t) and dist * d.units["range_scale"] <= d.weather["light"]["flash"]):
            out["blocked"] = f"{L['name']}: no one can be seen to aim at beyond {sight // d.units['range_scale']} hexes."
            return out
        out["flash"] = True
    out["penalty"] += aim
    return out


def night_device(d: Data, seer: dict | None) -> str | None:
    """The night-vision device a shooter or watcher ({kit, nv}) carries: the unit's own (nv;
    "none" for none), else his kit's (light.night_vision.kits carry its kit_device), else None."""
    s, N = seer or {}, (d.weather or {}).get("light", {}).get("night_vision") or {}
    if s.get("nv"):
        return None if s["nv"] == "none" else s["nv"]
    return N.get("kit_device") if s.get("kit") in (N.get("kits") or []) else None


def _seer(u: dict, **k) -> dict:
    """A unit as a shooter or watcher for the dark: its kit and its night-vision device."""
    return {"kit": u.get("kit"), "nv": u.get("nv"), **k}


def dark_sight(d: Data, level: dict, device: str | None) -> tuple:
    """(sight in battle hexes or None, aim % off) in the light level for a man with this
    night-vision device (light.night_vision.devices; None: his eyes only)."""
    dev = ((d.weather["light"].get("night_vision") or {}).get("devices") or {}).get(device or "")
    if not dev:
        return level["sight"], level["aim"]
    return (None if level["sight"] is None else max(level["sight"], dev["sight"])), min(level["aim"], dev["aim"])


def sees_smoke(d: Data, seer: dict | None) -> bool:
    """Whether the shooter's or watcher's device (a thermal sight) sees through smoke."""
    dev = ((d.weather or {}).get("light", {}).get("night_vision") or {}).get("devices", {}).get(night_device(d, seer) or "")
    return bool(dev and dev.get("smoke"))


def flashing(field: dict | None, t) -> bool:
    """Whether hex t is one a unit fired from in the dark last exchange (field.flashes)."""
    return t is not None and list(t) in ((field or {}).get("flashes") or [])


FLASHING = ("volley", "hero", "antiarmour", "tankfire", "cannon")


def _flashes(d: Data, us: list, log: list, field: dict | None) -> None:
    """After the shooting: in the dark (not dusk), field.flashes becomes the hexes of every unit
    that fired this exchange (seen by their flashes through the next); else none."""
    if field is None:
        return
    L = light_of(d, field)
    if L is None or L["sight"] is None or L["sight"] >= d.weather["light"]["flash"]:
        field.pop("flashes", None)
        return
    fired = sorted({x["att"] for x in log if x.get("kind") in FLASHING and x.get("att") is not None})
    field["flashes"] = sorted({tuple(h) for i in fired for row in footprint(d, us[i]) for h in row})
    field["flashes"] = [list(h) for h in field["flashes"]]
    if not field["flashes"]:
        field.pop("flashes")


def night_drift(d: Data, units: list, i: int, size: tuple, field: dict | None, rng) -> dict:
    """A unit that moved in the dark may lose its direction: d100 at or under the light's `lost`
    % plus half of (60 - its nerve) (rounded down). Then it ends turned one point off (left on
    an odd second d100, else right; not if it no longer fits) and cannot move for light.lost_for
    exchanges. -> {lost (bool), unit}."""
    u, L = units[i], light_of(d, field)
    if L is None or not L.get("lost"):
        return {"lost": False, "unit": u}
    chance = max(0, min(100, L["lost"] + (60 - quality(d, u["quality"])["nerve"]) // 2))
    if rng.randint(1, 100) > chance:
        return {"lost": False, "unit": u}
    turned = {**u, "facing": (u["facing"] + (-1 if rng.randint(1, 100) % 2 else 1)) % 6, "lost": d.weather["light"]["lost_for"]}
    if not _fits(d, units, i, turned, size, field):
        turned["facing"] = u["facing"]
    return {"lost": True, "unit": turned}


def height_edge(d: Data, field: dict | None, weapon: str, h, t) -> tuple:
    """(% to hit, % longer range bands) for a shot from hex h at hex t: down from high ground
    +, up at it -; none for guns or on level ground."""
    if not field or is_gun(d, weapon):
        return 0, 0
    diff, H = height_at(d, field, h) - height_at(d, field, t), d.units["high_ground"]
    if diff > 0:
        return H["shoot"] * diff // 10, H["reach"] * diff // 10
    return (-(H["shoot"] * -diff // 10), 0) if diff < 0 else (0, 0)


def height_at(d: Data, field: dict | None, h) -> int:
    """How high the ground at hex h stands (0, a slope 5, high ground or tall buildings 10)."""
    return ground_at(d, field, h).get("height", 0) if field else 0


def _up(field: dict | None) -> str:
    """The compass point at the top of the field map (north, unless the battlefield says)."""
    return (field or {}).get("up") or "N"


def _reaches(d: Data, u: dict, dist: int, reach: int = 0) -> bool:
    """Whether a unit's weapon shoots this many field hexes: a battery's guns to their range."""
    if is_gun(d, u["weapon"]):
        return dist <= gun_range(d, u)
    return field_range(d, u["weapon"], dist, reach) is not None


def share_cover(d: Data, field: dict | None, h, target: dict) -> int:
    """% off a volley from hex h at a unit: the average cover of its row nearest h (half a line
    behind a wall gets half the wall's cover), rounded down."""
    if not field:
        return 0
    rows = footprint(d, target)
    if not rows:
        return 0
    row = min(rows, key=lambda r: min(hdist(h, t) for t in r))
    return sum(cover_at(d, field, h, t) for t in row) // len(row)


def cover_at(d: Data, field: dict | None, h, t) -> int:
    """% off shots from hex h at hex t: the best of the works' cover and the ground's."""
    if not field:
        return 0
    cols, rows = _size(d, field)
    return max(C.missile_cover(d, _works(field), h, t, cols, rows)["cover"], ground_at(d, field, t).get("cover", 0))


def _target(d: Data, units: list, i: int, field: dict | None = None, occ: dict | None = None):
    """(distance, index, shooter hex, target hex) of the nearest enemy unit in range, in
    sight and in front of unit i, or None. A battery fires at the unit the GM named
    (u["target"], its id) if it can, and needs a clear line of fire (occ given)."""
    u, fv, best = units[i], _fvec(units[i]["facing"]), None
    front = footprint(d, u)[0]
    named = _named_target(d, units, i, field, occ, u.get("target"))
    if named is not None:
        return named
    for j, e in enumerate(units):
        if e["side"] == u["side"] or e["men"] <= 0 or e["state"] == "fled" or (e.get("vehicle") and not hurts_armour(d, u["weapon"])):
            continue
        near = _nearest_ahead(d, u, front, fv, [t for row in footprint(d, e) for t in row], field, _clear_fn(d, units, occ, field, i, j))
        if near is not None and (best is None or near[0] < best[0]):
            best = (near[0], j, near[1], near[2])
    return best


def _named_target(d: Data, units: list, i: int, field: dict | None, occ: dict | None, tid):
    """A target the GM named for a battery (tid, a unit's id), as _target gives it, if it can be fired on."""
    u = units[i]
    if occ is None or tid is None:
        return None
    j = next((k for k, e in enumerate(units) if e.get("id") == tid), None)
    if j is None or units[j]["side"] == u["side"] or _out(units[j]):
        return None
    hexes = [t for row in footprint(d, units[j]) for t in row]
    near = _nearest_ahead(d, u, footprint(d, u)[0], _fvec(u["facing"]), hexes, field, _clear_fn(d, units, occ, field, i, j))
    return None if near is None else (near[0], j, near[1], near[2])


def _clear_fn(d: Data, units: list, occ: dict | None, field: dict | None, i: int, j: int):
    """A test that unit i has a line of fire from h to t (see line_fire); None without occ."""
    if occ is None:
        return None
    return lambda h, t, dist: line_fire(d, units, occ, field, i, j, h, t, dist) is not None


def line_fire(d: Data, units: list, occ: dict, field: dict | None, i: int, j: int, h, t, dist: int):
    """Unit i shooting from hex h at unit j's hex t: None if another unit between blocks it,
    else the % off (bows loosing high over units). From high ground a unit shoots over units
    on lower ground; guns only with round shot, never canister; shell goes over anything."""
    u, high, pen = units[i], height_at(d, field, h), 0
    over, arc = True, u["weapon"] in d.units["line_of_fire"]["arcing"]
    if is_gun(d, u["weapon"]):
        over = dist > d.units["artillery"]["canister_to"]
        if over and gun_kind(u) == "howitzer":
            return 0
    for x in ray(h, t, dist)[1:-1]:
        k = occ.get(f"{x[0]},{x[1]}")
        if k is None or k in (i, j) or (over and high > height_at(d, field, x)):
            continue
        if not arc:
            return None
        pen = d.units["line_of_fire"]["arc_penalty"]
    return pen


def _nearest_ahead(d: Data, u: dict, front: list, fv: tuple, hexes: list, field: dict | None = None, clear=None):
    """(distance, front hex, target hex): the shortest distance in range of unit u's weapon and
    in sight from a front hex to one of `hexes` ahead of the line (with a line of fire), or None."""
    best, weapon = None, u["weapon"]
    for t in hexes:
        c = _cube(t)
        for h in front:
            s = _cube(h)
            if sum((c[k] - s[k]) * fv[k] for k in range(3)) <= 0:
                continue
            dist = hdist(h, t)
            if best is not None and dist >= best[0]:
                continue
            wx = shot_weather(d, field, weapon, dist, h, t, _seer(u))
            reach = wx.get("reach", 0) + height_edge(d, field, weapon, h, t)[1]
            if not wx["blocked"] and _reaches(d, u, dist, reach) and (clear is None or clear(h, t, dist)):
                best = (dist, h, t)
    return best


def _side(u: dict, table: str, d: Data | None = None) -> dict:
    """A unit as a fighting side: hand to hand, a battery's crews fight with their own weapon."""
    weapon = melee_weapon(d, u) if d else u["weapon"]
    return {"table": table, "weapon": weapon, "kit": u.get("kit"), "quality": u["quality"]}


def exchange(d: Data, units: list, table: str, rng, field: dict | None = None) -> tuple[list, list]:
    """One exchange on the field map: every melee and volley at once from the present
    positions, then breaching, losses, morale, and a rout strike on any unit that breaks.
    Returns (units, log): log lines are {kind (melee, volley, hero, herohit, breach, rout,
    morale), ...}. field: the ground, works and weather (see field_ground); works being
    breached are updated in it, in place."""
    us = [_copy_unit(u) for u in units]
    lost, dead, dealt, flanked, log = [0] * len(us), [0] * len(us), [0] * len(us), [False] * len(us), []
    acc = (lost, dead, dealt)
    under = [False] * len(us)                     # under shellfire or machine-gun fire this exchange (suppression)
    log += _closing_all(d, us, table, rng, acc, field)
    log += _strike_all(d, us, table, rng, acc, flanked, field, list(lost))
    log += _shoot_all(d, us, table, rng, acc, field, under)
    log += _indirect_all(d, us, table, rng, acc, field, under)
    log += _assault_all(d, us, table, rng, acc, field)
    log += _breach_all(d, us, field)
    occ = occupancy(d, us)
    before = [u["men"] for u in us]
    for i, u in enumerate(us):
        cut = min(lost[i], u["men"])
        u.update(men=u["men"] - cut, down=u.get("down", 0) + cut, dead=u.get("dead", 0) + min(dead[i], cut))
    log += _morale_all(d, us, occ, before, (lost, dealt, flanked), rng, table, field)
    log += _suppress_all(d, us, under, rng)
    log += _heroes_after(d, us, rng, [not lost[i] and not under[i] and not in_contact(d, us, occ, i) for i in range(len(us))], cauterises(d, table))
    for u in us:
        u["charged"] = False
        _battery_after(d, u)
        if u.get("pinned"):
            u["pinned"] -= 1
        if u.get("lost"):
            u["lost"] -= 1
    _flashes(d, us, log, field)
    for b in (field or {}).get("support") or []:
        if b.get("mission") and b["mission"].get("wait", 0) > 0:
            b["mission"]["wait"] -= 1
    log += _displace_all(field)
    log += _overrun_all(d, us, field)
    _smoke_thins(field)
    _smoke_drifts(d, field)
    _lit_fades(field)
    log += landings(d, us, table, rng, field)
    log += _vehicles_after(d, us, field)
    return us, log


def lz_state(d: Data, units: list, field: dict | None, side, lz) -> str:
    """A landing zone for `side`: blocked (an enemy unit, not fled, within heliborne.blocked
    hexes), hot (an enemy unit, not broken or fled, could shoot at its hex) or cold."""
    H, hot = d.units["heliborne"], False
    for u in units:
        if u["side"] == side or u["men"] <= 0 or u["state"] == "fled":
            continue
        hexes = [x for row in footprint(d, u) for x in row]
        if any(hdist(x, lz) <= H["blocked"] for x in hexes):
            return "blocked"
        hot = hot or (not _out(u) and _could_shoot(d, field, u, hexes, lz))
    return "hot" if hot else "cold"


def _could_shoot(d: Data, field: dict | None, u: dict, hexes: list, t) -> bool:
    """Whether unit u (on these hexes) has a weapon that reaches hex t and sees it to aim."""
    if "range" not in d.weapons[u["weapon"]]:
        return False
    for x in hexes:
        dist = hdist(x, t)
        wx = shot_weather(d, field, u["weapon"], dist, x, t, _seer(u))
        if not wx["blocked"] and _reaches(d, u, dist, wx.get("reach", 0)):
            return True
    return False


def landings(d: Data, us: list, table: str, rng, field: dict | None) -> list:
    """Men coming on by air (field.lifts: [{unit, lz, left}]): up to heliborne.lift a landing
    zone this exchange, in order; a lift waits while its zone is blocked or there is no room.
    A unit's first men to land join the battle as a new unit. At a hot zone each man is struck
    at heliborne.hot % and rolls a wound as one struck by shellfire."""
    lifts, log = (field or {}).get("lifts") or [], []
    if not lifts or "heliborne" not in d.units:
        return log
    room = {}
    for lf in lifts:
        key = f"{lf['lz'][0]},{lf['lz'][1]}"
        room.setdefault(key, d.units["heliborne"]["lift"])
        if room[key] > 0 and lf["left"] > 0:
            log += _land(d, us, table, rng, field, lf, room, key)
    field["lifts"] = [lf for lf in lifts if lf["left"] > 0]
    return log


def _land(d: Data, us: list, table: str, rng, field: dict, lf: dict, room: dict, key: str) -> list:
    """One lift's men landing at its zone this exchange, if they can (see landings)."""
    side, name = lf["unit"]["side"], lf["unit"]["name"]
    state = lz_state(d, us, field, side, lf["lz"])
    if state == "blocked":
        return [{"kind": "waveoff", "name": name, "side": side, "lz": lf["lz"], "why": "blocked"}]
    n = min(room[key], lf["left"])
    i = next((k for k, u in enumerate(us) if u.get("id") is not None and u.get("id") == lf["unit"].get("id")), len(us))
    u = dict(us[i]) if i < len(us) else {**lf["unit"], "pos": list(lf["lz"]), "men": 0, "start": 0, "down": 0, "dead": 0, "hurt": {}, "heroes": [], "state": "steady"}
    u.update(men=u["men"] + n, start=u["start"] + n)
    spots = [u["pos"]] if i < len(us) else within(lf["lz"], d.units["heliborne"]["zone"])
    u["pos"] = next((list(h) for h in spots if _fits(d, us, i, {**u, "pos": list(h)}, _size(d, field), field)), None)
    if u["pos"] is None:
        return [{"kind": "waveoff", "name": name, "side": side, "lz": lf["lz"], "why": "room"}]
    if i < len(us):
        us[i].update(men=u["men"], start=u["start"])
    else:
        us.append(u)
    room[key] -= n
    lf["left"] -= n
    line = {"kind": "landed", "unit": i, "dfd": i, "name": name, "side": side, "lz": lf["lz"], "men": n, "hot": state == "hot", "first": u["start"] == n}
    if state != "hot":
        return [line]
    return _hot_landing(d, us[i], (table, rng), n, line)


def _hot_landing(d: Data, u: dict, tr: tuple, n: int, line: dict) -> list:
    """The men of a lift landing at a hot zone: each struck at heliborne.hot %, wounds rolled
    as shellfire; those put down are down at once."""
    table, rng = tr
    weapon = shell_weapon(d, table)
    struck = sum(1 for _ in range(n) if rng.randint(1, 100) <= d.units["heliborne"]["hot"])
    if not weapon or not struck:
        return [{**line, "struck": struck}]
    t = _take_hurt(u, _blows(d, {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}, _side(u, table), struck,
                             d.units["indirect"]["attack"], 0, rng, _exposure(d, u, False, True), -1000))
    cut = min(t["down"], u["men"])
    u.update(men=u["men"] - cut, down=u.get("down", 0) + cut, dead=u.get("dead", 0) + min(t["dead"], cut))
    return _logged({**line, "struck": struck}, t)


def _displace_all(field: dict | None) -> list:
    """Batteries displacing count down; one that has moved is no longer located, and missions on it end."""
    sup, log = (field or {}).get("support") or [], []
    for k, b in enumerate(sup):
        if not b.get("displacing"):
            continue
        b["displacing"] -= 1
        if not b["displacing"]:
            log.append(_displaced(sup, k))
    return log


def _displaced(sup: list, k: int) -> dict:
    """Battery k has moved: no longer located, at its plotted new place, and missions on it end."""
    b = sup[k]
    b["located"] = False
    if b.get("to") is not None:
        b["place"] = b.pop("to")              # its new position, plotted when it was ordered to move
    for x in sup:
        if x.get("mission") and x["mission"].get("battery") == k:
            x["mission"] = None
    return {"kind": "displaced", "sup": k, "name": b["name"], "side": b["side"], **({"place": b["place"]} if b.get("place") is not None else {})}


def downwind(d: Data, field: dict | None):
    """The hex side (0-5) the field's wind blows smoke through, or None in calm air or with no direction."""
    weather, pts = (field or {}).get("weather") or {}, d.weather.get("wind_points", []) if d.weather else []
    if weather.get("dir") not in pts or weather.get("wind", "calm") == "calm":
        return None
    wx, wy = C.WIND_VECTORS[(pts.index(weather["dir"]) - pts.index(_up(field)) + 4) % 8]
    best, side = None, None
    for dirn in range(6):
        dq, dr = AX[dirn]
        dot = math.sqrt(3) * (dq + dr / 2) * wx + 1.5 * dr * wy
        if best is None or dot > best + 1e-9:
            best, side = dot, dirn
    return side


def _smoke_drifts(d: Data, field: dict | None) -> None:
    """Smoke moves `drift` hexes downwind; what leaves the map is gone."""
    sm = (field or {}).get("smoke")
    side = downwind(d, field) if sm else None
    n = d.units["indirect"]["smoke"].get("drift", {}).get(((field or {}).get("weather") or {}).get("wind") or "calm", 0)
    if side is None or not n:
        return
    size, out = field.get("size"), {}
    for key, left in sm.items():
        h = step([int(x) for x in key.split(",")], side, n)
        if size and not (0 <= h[0] < size[0] and 0 <= h[1] < size[1]):
            continue
        k2 = f"{h[0]},{h[1]}"
        out[k2] = max(out.get(k2, 0), left)
    field["smoke"] = out


def _smoke_thins(field: dict | None) -> None:
    """Smoke hangs one exchange less; gone at none."""
    sm = (field or {}).get("smoke")
    if sm:
        field["smoke"] = {h: n - 1 for h, n in sm.items() if n > 1}


def _closing_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None = None) -> list:
    """Batteries charged in front fire canister into the charge as it comes in (closing_fire)."""
    log = []
    for c in closing_fire(d, us, field):
        log += _fire_battery(d, us, table, rng, acc, c)
    return log


def _strike_all(d: Data, us: list, table: str, rng, acc: tuple, flanked: list, field: dict | None = None, thinned: list | None = None) -> list:
    """Every melee, each unit's front heroes striking with its first (or dueling the enemy's).
    thinned: men each unit lost to canister as it came in (closing fire), its striking men cut
    in the same share (rounded down)."""
    log, struck, dueled = [], set(), set()
    for s in strikes(d, us, field):
        s = _thin(s, us, thinned)
        a, b = us[s["att"]], us[s["dfd"]]
        opts = _melee_opts(d, a, b, s)
        t = _take_hurt(b, melee(d, _side(a, table, d), _side(b, table, d), s["men"], rng, **opts))
        _tally(*acc, s, t)
        flanked[s["dfd"]] = flanked[s["dfd"]] or s["situation"] in ("flank", "rear")
        log += _logged({"kind": "rout" if s["rout"] else "melee", **s}, t)
        if s["att"] in struck:
            continue
        struck.add(s["att"])
        log += _front_heroes(d, (a, b), s, (table, rng, acc), opts, dueled)
    return log


def _thin(s: dict, us: list, thinned: list | None) -> dict:
    """Strike s with its men cut in the share its unit lost to closing canister (not a rout)."""
    cut = thinned[s["att"]] if thinned else 0
    if not cut or s["rout"]:
        return s
    men = us[s["att"]]["men"]
    left = s["men"] * max(0, men - cut) // max(1, men)
    return {**s, "men": left, "thinned": s["men"] - left}


def _melee_opts(d: Data, a: dict, b: dict, s: dict) -> dict:
    """The melee options for strike s by unit a on unit b: situation, a charge by horse (not
    into stakes or a pike front), shaken, rout, exposure, and pikes against horse."""
    charge = bool(a.get("charged")) and bool(a.get("mounted")) and not s.get("stakes") and not (s["situation"] == "front" and pike_front(d, b))
    vs_horse = d.units["melee"]["pikes"]["attack"] if b.get("mounted") and pike_front(d, a) else 0
    return {"situation": s["situation"], "charge": charge, "shaken": a["state"] == "shaken", "rout": s["rout"],
            "exposed": _exposure(d, b, s["rout"]), "penalty": s.get("penalty", 0) - vs_horse}


def _front_heroes(d: Data, units: tuple, s: dict, ctx: tuple, opts: dict, dueled: set) -> list:
    """A striking unit's front heroes: each duels the enemy's first free front hero, or strikes its rankers."""
    (a, b), (table, rng, acc), log = units, ctx, []
    for hero in _acting(d, a, ("front",)):
        if hero["id"] in dueled:
            continue
        foe = None if s["rout"] else next((h for h in _heroes(b, ("front",)) if h["id"] not in dueled), None)
        if foe is not None:
            log += _duel(d, (a, b), (hero, foe), table, rng, s, dueled)
            continue
        t = _take_hurt(b, melee(d, _hero_side(a, hero, table, d), _side(b, table, d), d.units["heroes"]["tempo"], rng, **opts))
        _tally(*acc, s, t)
        log += _logged({"kind": "hero", "hero": hero["id"], "name": hero["name"], "att": s["att"], "dfd": s["dfd"],
                        "situation": s["situation"]}, t)
    return log


def _duel(d: Data, units: tuple, pair: tuple, table: str, rng, s: dict, dueled: set) -> list:
    """Two front heroes fight each other: each makes heroes.duel attempts at the other with the
    full rules (the one whose unit struck first, first), instead of at the rankers."""
    (a, b), (hero, foe), log = units, pair, []
    dueled.update((hero["id"], foe["id"]))
    for x, y, ux, k in ((hero, foe, a, s["att"]), (foe, hero, b, s["dfd"])):
        if x["state"] != "up" or not _strikes(d, x) or y["state"] != "up":
            continue
        side = _hero_side(ux, x, table, d)
        atk = max(0, side["skill"])
        crit_at, t = math.floor(atk * d.wounds["combat"]["critical_fraction"]), _new_tally()
        t["blows"] = _count(d.units["heroes"]["duel"], rng)
        for _ in range(t["blows"]):
            if y["state"] != "up":
                break
            _hero_blow(d, side, y, rng.randint(1, 100), atk, crit_at, 0, rng, t)
        hits = t.pop("heroes", [])
        log.append({"kind": "duel", "unit": k, "hero": x["id"], "name": x["name"], "foe": y["id"], "fname": y["name"], "blows": t["blows"]})
        log += [{"kind": "herohit", "unit": s["dfd"] if k == s["att"] else s["att"], **h} for h in hits]
    return log


def _shoot_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None = None, under: list | None = None) -> list:
    """Every volley, each unit's shooting heroes with it. under: marks the units a machine gun
    fired on (suppression)."""
    log = []
    for v in volleys(d, us, field):
        _mark_mg(d, us, v, under)
        b = us[v["dfd"]]
        opts = {"factor": form(d, b)["missile_factor"] * (100 - v["misfire"]) / 100 * v["seen"], "exposed": _exposure(d, b, False, True),
                "penalty": v["cover"] + v["penalty"] + v["over"], "reach": v["reach"]}
        if b.get("vehicle"):
            log += _armour_volley(d, us, (table, rng, acc), v, opts)
            continue
        t = _take_hurt(b, volley(d, _side(us[v["att"]], table), _side(b, table), v["men"], v["dist"], rng, **opts))
        _tally(*acc, v, t)
        log += _logged({"kind": "volley", **v}, t)
        if v.get("behind") is not None:
            log += _beaten_fire(d, us, table, rng, acc, v)
        for hero in _acting(d, us[v["att"]], ("ranged",)):
            wx = shot_weather(d, field, hero["weapon"], v["dist"], v["from"], v["to"], {"kit": hero.get("kit"), "blind": v.get("blind", False)})
            up, longer = height_edge(d, field, hero["weapon"], v["from"], v["to"])
            if wx["blocked"] or field_range(d, hero["weapon"], v["dist"], wx["reach"] + longer) is None:
                continue
            hopts = {**opts, "factor": form(d, b)["missile_factor"] * (100 - wx["misfire"]) / 100 * v["seen"], "penalty": v["cover"] + wx["penalty"] - up + v["over"],
                     "reach": wx["reach"] + longer}
            t = _take_hurt(b, volley(d, _hero_side(us[v["att"]], hero, table, d), _side(b, table), d.units["heroes"]["tempo"], v["dist"], rng, **hopts))
            _tally(*acc, v, t)
            log += _logged({"kind": "hero", "hero": hero["id"], "name": hero["name"], "att": v["att"], "dfd": v["dfd"], "dist": v["dist"]}, t)
    for c in cannonades(d, us, field):
        log += _fire_battery(d, us, table, rng, acc, c)
    return log + _vehicle_guns(d, us, (table, rng, acc), field, under)


def _armour_volley(d: Data, us: list, ctx: tuple, v: dict, opts: dict) -> list:
    """Anti-armour weapons at a vehicle unit: each aimed shot that hits (as at men) knocks a
    vehicle out at its armour's `rpg` %."""
    table, rng, acc = ctx
    att = _side(us[v["att"]], table)
    band = field_range(d, att["weapon"], v["dist"], opts["reach"])
    if band is None:
        return []
    A = d.units["vehicles"]["anti_armour"][att["weapon"]]
    n = _count(v["men"] * A["rate"] * opts["factor"], rng)
    atk = _attack(d, att) - band["penalty"] - opts["penalty"]
    hits = sum(1 for _ in range(n) if rng.randint(1, 100) <= atk)
    p = kill_chance(d, us[v["dfd"]], A["row"], v["from"], v["to"])
    kills = sum(1 for _ in range(hits) if rng.randint(1, 100) <= p)
    k = knock_out(d, us, v["dfd"], kills, (table, rng), acc)
    harm = _harm(d, us[v["dfd"]], hits - k["knocked"], acc[0][v["dfd"]], rng)
    acc[2][v["att"]] += k["crew"]
    line = {"kind": "antiarmour", **v, "shots": n, "hit": hits, "knocked": k["knocked"], "crew": k["crew"], "struck": k["struck"], "kill": p, **_harm_line(harm), **_riders_line(k)}
    return _logged(line, k["tally"])


def _harm_line(harm: dict) -> dict:
    """The log's immobilised and gun counts, when there are any."""
    return {k: v for k, v in (("immobilised", harm["immobilised"]), ("gun_out", harm["gun"])) if v}


def _riders_line(k: dict) -> dict:
    """The log's riders struck and down, when any were."""
    return {k2: k[k1] for k1, k2 in (("riders_struck", "rstruck"), ("riders_down", "rdown"), ("riders_dead", "rdead")) if k.get(k1)}


def knock_out(d: Data, us: list, i: int, n: int, tr: tuple, acc: tuple) -> dict:
    """Knock out up to n of vehicle unit i's vehicles: their crews are out of the fight, each
    struck at vehicles.crew_struck % and wounded as by shellfire. -> {knocked, crew, struck, tally}."""
    table, rng = tr
    lost, dead, _ = acc
    u, K, V = us[i], vehicle_kind(d, us[i]), d.units["vehicles"]
    n = min(n, vehicles_left(d, u, lost[i]))
    if n <= 0:
        return {"knocked": 0, "crew": 0, "struck": 0, "tally": _new_tally()}
    crew = min(n * K["crew"], u["men"] - lost[i])
    struck = sum(1 for _ in range(crew) if rng.randint(1, 100) <= V["crew_struck"])
    weapon = shell_weapon(d, table)
    t = _blows(d, {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}, _side(u, table), struck, d.units["indirect"]["attack"], 0, rng, (), -1000) \
        if struck and weapon else _new_tally()
    t = _take_hurt(u, t)
    left = vehicles_left(d, u, lost[i])
    lost[i] += crew
    dead[i] += min(t["dead"], crew)
    return {"knocked": n, "crew": crew, "struck": struck, "tally": t, **_riders_hit(d, u, n, left, tr)}


def _riders_hit(d: Data, u: dict, n: int, left: int, tr: tuple) -> dict:
    """The riders in n of a carrier unit's `left` vehicles, knocked out: each struck at
    vehicles.riders_struck % and wounded as by shellfire (taken off the riders at once)."""
    R = u.get("riders")
    if not R or R["men"] <= 0 or left <= 0:
        return {}
    table, rng = tr
    share = min(R["men"], math.ceil(R["men"] * n / left))
    struck = sum(1 for _ in range(share) if rng.randint(1, 100) <= d.units["vehicles"]["riders_struck"])
    weapon = shell_weapon(d, table)
    if not struck or not weapon:
        return {"riders_struck": struck}
    t = _take_hurt(R, _blows(d, {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}, _side(R, table), struck, d.units["indirect"]["attack"], 0, rng, (), -1000))
    down = min(t["down"], R["men"])
    R.update(men=R["men"] - down, down=R.get("down", 0) + down, dead=R.get("dead", 0) + min(t["dead"], down))
    return {"riders_struck": struck, "riders_down": down, "riders_dead": min(t["dead"], down)}


def _vehicle_guns(d: Data, us: list, ctx: tuple, field: dict | None, under: list | None) -> list:
    """Each vehicle unit with a main gun fires `rate` rounds a vehicle at its gun target: at
    vehicles, hits by range and knocks by armour; at men, bursts on their nearest hex as the
    indirect kind `he` does."""
    log = []
    for i, u in enumerate(us):
        kind = vehicle_kind(d, u)
        gun = kind.get("gun") if kind else None
        if gun and not _out(u):
            log += _main_gun(d, us, i, gun, (ctx, field, under))
    return log


def _main_gun(d: Data, us: list, i: int, gun: dict, env: tuple) -> list:
    """Vehicle unit i's main gun this exchange (env: (table, dice, tallies), field, under fire):
    at its gun target, if it has one and guns that still work."""
    ctx, field, under = env
    table, rng, acc = ctx
    u, best = us[i], _gun_target(d, us, i, field, gun)
    if best is None:
        return []
    dist, j, h, t = best
    rounds = max(0, vehicles_left(d, u) - u.get("gunless", 0)) * gun["rate"]
    if rounds <= 0:
        return []
    if us[j].get("vehicle"):
        return _gun_at_vehicle(d, us, (i, j, dist, rounds, h, t), gun, ctx)
    log = [{"kind": "tankfire", "att": i, "dfd": j, "dist": dist, "rounds": rounds, "at": t}]
    weapon = shell_weapon(d, table)
    if weapon and field:
        log += _shell_units(d, us, (table, weapon), rng, acc, field, under or [False] * len(us), None, {"kind": gun["he"], "name": u.get("name")}, [list(t)] * rounds)
    return log


def _gun_at_vehicle(d: Data, us: list, shot: tuple, gun: dict, ctx: tuple) -> list:
    """A main gun's rounds at a vehicle unit (shot: gun unit, target, distance, rounds): hits by
    range, knocks by the target's armour."""
    i, j, dist, rounds, h, t = shot
    table, rng, acc = ctx
    hits = sum(1 for _ in range(rounds) if rng.randint(1, 100) <= _chance_at(gun["hit"], dist))
    p = kill_chance(d, us[j], "gun", h, t)
    kills = sum(1 for _ in range(hits) if rng.randint(1, 100) <= p)
    k = knock_out(d, us, j, kills, (table, rng), acc)
    harm = _harm(d, us[j], hits - k["knocked"], acc[0][j], rng)
    acc[2][i] += k["crew"]
    line = {"kind": "tankfire", "att": i, "dfd": j, "dist": dist, "rounds": rounds, "hit": hits, "knocked": k["knocked"], "crew": k["crew"], "struck": k["struck"], "kill": p,
            **_harm_line(harm), **_riders_line(k)}
    return _logged(line, k["tally"])


def _gun_target(d: Data, us: list, i: int, field: dict | None, gun: dict):
    """(distance, index, gun hex, target hex) for vehicle unit i's main gun: the nearest enemy
    vehicle in range, in sight and in front with a line of fire, else the nearest such unit."""
    u, occ = us[i], occupancy(d, us)
    front, fv, best = footprint(d, u)[0], _fvec(u["facing"]), None
    for j, e in enumerate(us):
        if e["side"] == u["side"] or e["men"] <= 0 or e["state"] == "fled":
            continue
        clear = _clear_fn(d, us, occ, field, i, j)
        for t, h in ((x, h) for row in footprint(d, e) for x in row for h in front):
            dist = hdist(h, t)
            key = (0 if e.get("vehicle") else 1, dist)
            if dist <= gun["range"] and (best is None or key < best[0]) and _can_lay(d, field, clear, fv, (h, t, dist), _seer(u)):
                best = (key, (dist, j, h, t))
    return None if best is None else best[1]


def _can_lay(d: Data, field: dict | None, clear, fv: tuple, line: tuple, seer: dict | None = None) -> bool:
    """Whether a gun at h can be laid on t: ahead, in sight (seer: the crew's night device), with a clear line of fire."""
    h, t, dist = line
    return _ahead(fv, h, t) and clear_sight(d, field, h, t, dist) and not gun_weather(d, field, dist, h, t, seer)["blocked"] and (clear is None or clear(h, t, dist))


def _ahead(fv: tuple, h, t) -> bool:
    """Whether hex t is in front of hex h for a unit facing fv."""
    c, s = _cube(t), _cube(h)
    return sum((c[k] - s[k]) * fv[k] for k in range(3)) > 0


def _mark_mg(d: Data, us: list, v: dict, under: list | None) -> None:
    """A machine gun's target, and any unit in its beaten zone, check for suppression."""
    if under is None or not is_mg(d, us[v["att"]]["weapon"]):
        return
    under[v["dfd"]] = True
    if v.get("behind") is not None:
        under[v["behind"]] = True


def _beaten_fire(d: Data, us: list, table: str, rng, acc: tuple, v: dict) -> list:
    """A machine gun's cone falling on into the unit behind its target."""
    k, bh = v["behind"], us[v["behind"]]
    r = {**v, "dfd": k, "dist": v["dist"] + v["beyond"], "men": v["men"] * d.units["machine_guns"]["beaten"]["share"] / 100}
    opts = {"factor": form(d, bh)["missile_factor"] * (100 - v["misfire"]) / 100 * v.get("bseen", 1), "exposed": _exposure(d, bh, False, True),
            "penalty": v["bcover"] + v["penalty"], "reach": v["reach"]}
    hits = volley(d, _side(us[v["att"]], table), _side(bh, table), r["men"], r["dist"], rng, **opts)
    if hits is None:
        return []
    t = _take_hurt(bh, hits)
    lost, dead, dealt = acc
    _tally(lost, dead, dealt, r, t)
    return _logged({"kind": "beaten", **r}, t)


# ---------- indirect fire (data/units.yaml indirect) ----------

def shell_weapon(d: Data, table: str) -> str | None:
    """The weapon whose wound data shell fragments use on this table, or None (no indirect fire)."""
    from .model import available_weapons
    I, have = d.units["indirect"], available_weapons(d, table)
    return next((w for w in (I["weapon"], I["fallback"]) if w in have), None)


def spotted(d: Data, units: list, field: dict | None, side, h) -> bool:
    """Whether a unit of `side` (not broken or fled) can see hex h to call fire on it: within
    the weather's sight and the light's (unless h is lit), with no woods between."""
    return any(u["side"] == side and u["men"] > 0 and u["state"] not in ("broken", "fled") and _sees(d, field, u, h, _sight_hexes(d, field, h, _seer(u))) for u in units)


def _sight_hexes(d: Data, field: dict | None, h=None, seer: dict | None = None) -> int | None:
    """How far the weather and the light let a man (seer: his kit and night device) see hex h, in
    field hexes (None: as far as the map). A lit hex is seen as by day; one that fired in the
    dark last exchange, out to light.flash."""
    cond = ((field or {}).get("weather") or {}).get("cond")
    vis = d.weather["conditions"][cond].get("visibility") if cond and d.weather else None
    L = light_of(d, field)
    dark = dark_sight(d, L, night_device(d, seer))[0] if L and not lit(field, h) else None
    if dark is not None and flashing(field, h):
        dark = max(dark, d.weather["light"]["flash"])
    if dark is not None:
        vis = dark if vis is None else min(vis, dark)
    return None if vis is None else vis // d.units["range_scale"]


def _sees(d: Data, field: dict | None, u: dict, h, sight: int | None) -> bool:
    """Whether any hex of unit u sees hex h: within sight, with a clear sight past woods and
    buildings (clear_sight: from higher ground he sees over them, and into and out of a cover's
    edge) and no smoke on the line (the two ends included)."""
    for x in (x for row in footprint(d, u) for x in row):
        dist = hdist(x, h)
        if sight is not None and dist > sight:
            continue
        line = ray(x, h, dist)
        if clear_sight(d, field, x, h, dist, line) and (not smoked(field, line) or sees_smoke(d, _seer(u))):
            return True
    return False


def smoked(field: dict | None, hexes) -> bool:
    """Whether smoke hangs over any of these hexes."""
    sm = (field or {}).get("smoke") or {}
    return bool(sm) and any(f"{h[0]},{h[1]}" in sm for h in hexes)


def within(h, radius: int) -> list:
    """Hex h and every hex within `radius` of it."""
    out = [list(h)]
    for n in range(1, radius + 1):
        for a in range(6):
            corner = step(h, a, n)
            out += [step(corner, a + 2, j) for j in range(n)]
    return out


def _indirect_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None, under: list) -> list:
    """Every fire mission due this exchange (in the order of the support list)."""
    log, weapon = [], shell_weapon(d, table)
    if not field or weapon is None:
        return log
    for k, b in enumerate(field.get("support") or []):
        if _due(d, field, b):
            log += _fire_mission(d, us, table, weapon, rng, acc, field, under, k, b)
    return log


def _due(d: Data, field: dict, b: dict) -> bool:
    """Whether a battery's mission fires this exchange: called, its wait over, rounds and tubes
    left, not moving, (aircraft) able to fly, and its aim within reach of where it stands."""
    m = b.get("mission")
    if not m or m.get("wait", 0) > 0 or b.get("rounds", 0) <= 0 or served_tubes(d, b) <= 0 or b.get("displacing"):
        return False
    return grounded(d, field, b) is None and _aim_in_reach(d, field, b)


def reach_of(d: Data, b: dict) -> int | None:
    """How far a battery placed on or behind the map reaches, in field hexes (its kind's `range`),
    or None: off the map with no place, or a kind without one (tanks, aircraft)."""
    r = d.units["indirect"]["kinds"][b["kind"]].get("range")
    return r if r is not None and b.get("place") is not None else None


def in_reach(d: Data, b: dict, h) -> bool:
    """Whether a battery can fire on hex h from where it stands (always, if it has no place)."""
    r = reach_of(d, b)
    return r is None or h is None or hdist(b["place"], h) <= r


def _aim_in_reach(d: Data, field: dict, b: dict) -> bool:
    """A mission's aim within the battery's reach: its hex, or the enemy battery's place."""
    m = b["mission"]
    if m.get("battery") is not None:
        sup = field.get("support") or []
        tg = sup[m["battery"]] if 0 <= m["battery"] < len(sup) else None
        return tg is None or tg.get("place") is None or in_reach(d, b, tg["place"])
    return in_reach(d, b, m.get("hex"))


def _overrun_all(d: Data, us: list, field: dict | None) -> list:
    """A battery placed on the map with an enemy unit (on its feet, not running) within a hex of
    its place is overrun: its tubes are lost and its mission ends."""
    log = []
    for k, b in enumerate((field or {}).get("support") or []):
        if b.get("place") is None or b.get("tubes", 0) <= 0:
            continue
        if any(u["side"] != b["side"] and not _out(u) and any(hdist(h, b["place"]) <= 1 for row in footprint(d, u) for h in row) for u in us):
            b.update(tubes=0, mission=None, overrun=True)
            log.append({"kind": "overrun", "sup": k, "name": b["name"], "side": b["side"]})
    return log


def grounded(d: Data, field: dict | None, b: dict) -> str | None:
    """Why aircraft cannot fly (a condition or a light name), or None: in the weather
    indirect.air.grounded lists, or in the dark without by_night."""
    I = d.units["indirect"]
    K, A = I["kinds"][b["kind"]], I.get("air") or {}
    if not K.get("air"):
        return None
    wx = (field or {}).get("weather") or {}
    if wx.get("cond") in A.get("grounded", []):
        return wx["cond"]
    if not K.get("by_night") and (wx.get("light") or "day") in A.get("night", []):
        return wx["light"]
    return None


def crew_of(d: Data, b: dict) -> int:
    """An off-map battery's crewmen still serving: `crew` a tube it came with, less those lost."""
    return b["crew"] if "crew" in b else b.get("tubes", 0) * d.units["indirect"]["kinds"][b["kind"]].get("crew", 0)


def served_tubes(d: Data, b: dict) -> int:
    """The tubes an off-map battery can fire: those not knocked out that it has `serve` men each for."""
    K = d.units["indirect"]["kinds"][b["kind"]]
    if "serve" not in K:
        return b.get("tubes", 0)
    return min(b.get("tubes", 0), crew_of(d, b) // K["serve"])


def _fire_mission(d: Data, us: list, table: str, weapon: str, rng, acc: tuple, field: dict, under: list, k: int, b: dict) -> list:
    """One battery's shells this exchange: illumination over a hex (a round a tube), on an enemy
    battery (counter-battery), or on a hex (_bombard). A battery that fires is located; a
    creeping mission moves on."""
    K, m = d.units["indirect"]["kinds"][b["kind"]], b["mission"]
    air = bool(K.get("air")) and m.get("hex") is not None and not m.get("illum")
    fac = air and _fac_sees(d, us, field, b, m["hex"])
    if air and not fac and _friends_near(d, us, b, m["hex"]):
        return [{"kind": "airhold", "sup": k, "name": b["name"], "side": b["side"], "at": m["hex"]}]
    shells = min(served_tubes(d, b) * (1 if m.get("illum") else K["rate"]), b["rounds"])
    b["rounds"] -= shells
    if not K.get("direct") and not K.get("air"):
        b["located"] = True                       # tanks close behind the line and aircraft are never located
    if m.get("illum"):
        _light_up(d, field, m["hex"], K.get("illum", 0), 1)
        log = [{"kind": "barrage", "sup": k, "name": b["name"], "side": b["side"], "shells": shells, "at": m["hex"], "bursts": [], "smoke": False, "illum": True}]
    elif m.get("battery") is not None:
        log = _counter_fire(d, field, (k, b, shells, K), (table, weapon), rng)
    else:
        log = _on_hex(d, (us, table, weapon, rng, acc, field, under), (k, b, shells), (air, fac))
    _mission_on(b, m, field.get("size"))
    return log


def _on_hex(d: Data, ctx: tuple, fire: tuple, flight: tuple) -> list:
    """Shells or an air attack on a hex (fire: support index, battery, shells; flight: whether
    aircraft, and whether a forward air controller talks them on: less scatter), then the
    ground fire at the aircraft."""
    us, rng = ctx[0], ctx[3]
    (k, b, shells), (air, fac) = fire, flight
    K = d.units["indirect"]["kinds"][b["kind"]]
    scatter = K["scatter"] // d.units["indirect"]["air"]["fac"]["scatter"] if fac else K["scatter"]
    log = _bombard(d, ctx, k, b, shells, scatter)
    if fac:
        log[0]["fac"] = True
    if air:
        log += _ground_fire(d, us, (k, b), -(-shells // K["rate"]), rng)
    return log


def _fac_sees(d: Data, us: list, field: dict, b: dict, h) -> bool:
    """Whether a forward air controller (a unit marked fac, of the aircraft's side, on its feet) sees hex h."""
    return any(u.get("fac") and u["side"] == b["side"] and not _out(u) and _sees(d, field, u, h, _sight_hexes(d, field, h, _seer(u))) for u in us)


def _friends_near(d: Data, us: list, b: dict, h) -> bool:
    """Whether a unit of the aircraft's side has a hex within indirect.air.fac.danger of hex h."""
    r = d.units["indirect"]["air"]["fac"]["danger"]
    return any(u["side"] == b["side"] and u["men"] > 0 and any(hdist(x, h) <= r for row in footprint(d, u) for x in row) for u in us)


def _flak(d: Data, us: list, b: dict, h) -> float:
    """% an aircraft attacking hex h is shot down: the enemy's machine guns, rockets and rifles
    within indirect.air.ground_fire.reach of it, times the kind's exposed, at most cap."""
    G, K = d.units["indirect"]["air"]["ground_fire"], d.units["indirect"]["kinds"][b["kind"]]
    chance = 0.0
    for u in us:
        if u["side"] == b["side"] or _out(u) or u.get("vehicle") or not any(hdist(x, h) <= G["reach"] for row in footprint(d, u) for x in row):
            continue
        w = u["weapon"]
        if is_mg(d, w):
            chance += G["mg"] * mg_guns(d, u)
        elif w in G["rockets"]:
            chance += G["rocket"]
        elif "range" in d.weapons[w] and not is_gun(d, w) and w not in d.units["line_of_fire"]["arcing"]:
            chance += G["rifles"] * u["men"] / 100
    return min(G["cap"], chance * K.get("exposed", 1))


def _ground_fire(d: Data, us: list, flight: tuple, attacking: int, rng) -> list:
    """Ground fire at the aircraft that attacked (flight: support index, battery): each is lost
    at _flak %; a lost one takes its share of the remaining attacks. -> a log line, or none."""
    k, b = flight
    chance = _flak(d, us, b, b["mission"]["hex"])
    if chance <= 0 or b["tubes"] <= 0:
        return []
    lost = min(b["tubes"], sum(1 for _ in range(attacking) if rng.randint(1, 100) <= chance))
    if not lost:
        return []
    share = b["rounds"] // b["tubes"]
    b["tubes"] -= lost
    b["rounds"] = max(0, b["rounds"] - share * lost)
    return [{"kind": "airloss", "sup": k, "name": b["name"], "side": b["side"], "lost": lost, "left": b["tubes"]}]


def _bombard(d: Data, ctx: tuple, k: int, b: dict, shells: int, scatter: int | None = None) -> list:
    """A battery's shells on a hex (ctx: units, table, shell weapon, dice, tallies, field, under
    fire): where each lands (0 to scatter hexes off; the kind's, unless given), then smoke laid,
    or the men struck and bunkers knocked."""
    us, table, weapon, rng, acc, field, under = ctx
    K, m, bursts = d.units["indirect"]["kinds"][b["kind"]], b["mission"], []
    scatter = K["scatter"] if scatter is None else scatter
    for _ in range(shells):
        dirn, far = rng.randint(0, 5), rng.randint(0, scatter)
        bursts.append(step(m["hex"], dirn, far))
    log = [{"kind": "barrage", "sup": k, "name": b["name"], "side": b["side"], "shells": shells, "at": m["hex"], "bursts": bursts,
            "smoke": bool(m.get("smoke"))}]
    if m.get("smoke"):
        _lay_smoke(d, field, bursts)
    else:
        log += _shell_units(d, us, (table, weapon), rng, acc, field, under, k, b, bursts)
        log += _knock_bunkers(d, field, k, b, bursts, rng)
    return log


def _knock_bunkers(d: Data, field: dict, k: int, b: dict, bursts: list, rng) -> list:
    """Each shell bursting on an intact bunker's hex knocks it out at the kind's `knock` %."""
    knock, log = d.units["indirect"]["kinds"][b["kind"]].get("knock", 0), []
    if not knock:
        return log
    for at in bursts:
        it = bunker_at(d, field, at)
        if it and rng.randint(1, 100) <= knock:
            it["out"] = True
            log.append({"kind": "knocked", "sup": k, "name": b["name"], "side": b["side"], "at": at})
    return log


def _mission_on(b: dict, m: dict, size) -> None:
    """After a battery fires: a single mission ends; a creeping one keeps to its fire plan,
    lifting its aim on after `every` exchanges on a line, and ends after its `lines` lines or
    when its aim leaves the map."""
    if not m.get("repeat"):
        b["mission"] = None
        return
    cr = m.get("creep")
    if not cr:
        return
    cr["on"] = cr.get("on", 0) + 1
    if cr["on"] < cr.get("every", 1):
        return
    cr["on"] = 0
    if cr.get("lines") and cr.get("line", 1) >= cr["lines"]:
        if not cr.get("legs"):
            b["mission"] = None
            return
        nxt, cr["legs"] = cr["legs"][0], cr["legs"][1:]   # the fire plan's next leg: its own lift, direction and lines
        cr.update(step=nxt["step"], dir=nxt["dir"], lines=nxt.get("lines", 0), line=0, done=0)
    cr["line"] = cr.get("line", 1) + 1
    for _ in range(cr["step"]):
        m["hex"] = step(m["hex"], cr["dir"] + cr.get("done", 0) % 2)
        cr["done"] = cr.get("done", 0) + 1
    if size and not (0 <= m["hex"][0] < size[0] and 0 <= m["hex"][1] < size[1]):
        b["mission"] = None


def _counter_fire(d: Data, field: dict, fire: tuple, tw: tuple, rng) -> list:
    """Counter-battery (fire: battery index, battery, shells, its kind; tw: table and shell
    weapon): each shell lands among the target's guns at the kind's counter %, knocking out a
    tube and striking `among` crewmen, or at `near` times that % bursts close by, striking
    `near_struck`. The struck crewmen roll wounds; those put down are lost to the battery."""
    k, b, shells, kind = fire
    j, sup, CB = b["mission"]["battery"], field["support"], d.units["indirect"]["counter_battery"]
    tg = sup[j] if 0 <= j < len(sup) else None
    if tg is None or tg["side"] == b["side"]:
        b["mission"] = None
        return []
    hits = struck = 0
    for _ in range(shells):
        r = rng.randint(1, 100)
        if r <= kind["counter"]:
            hits += 1
            struck += CB["among"]
        elif r <= kind["counter"] * CB["near"]:
            struck += CB["near_struck"]
    knocked, crew = min(tg["tubes"], hits), crew_of(d, tg)
    struck = min(struck, crew)
    table, weapon = tw
    t = _blows(d, {"table": table, "weapon": weapon, "kit": None, "quality": "regular"},
               {"table": table, "weapon": weapon, "kit": "none", "quality": "regular"}, struck, d.units["indirect"]["attack"], 0, rng, (), -1000)
    tg["tubes"] -= knocked
    tg["crew"] = crew - t["down"]
    tg["crew_dead"] = tg.get("crew_dead", 0) + t["dead"]
    if served_tubes(d, tg) <= 0:
        tg["mission"] = None
    return [{"kind": "counter", "sup": k, "name": b["name"], "side": b["side"], "shells": shells, "target": j, "tname": tg["name"],
             "knocked": knocked, "left": tg["tubes"], "struck": struck, "down": t["down"], "dead": t["dead"], "crew": tg["crew"],
             "served": served_tubes(d, tg)}]


def _light_up(d: Data, field: dict, at, radius: int, late: int = 0) -> None:
    """A flare or illumination round lights the hexes within `radius` of hex `at` for
    light.lasts exchanges (+ late: fired after the shooting, it lights none in this one)."""
    if radius > 0:
        field.setdefault("lit", []).append({"at": list(at), "radius": radius, "left": d.weather["light"]["lasts"] + late})


def _lit_fades(field: dict | None) -> None:
    """Flares and illumination burn one exchange less; gone at none."""
    if (field or {}).get("lit"):
        field["lit"] = [{**x, "left": x["left"] - 1} for x in field["lit"] if x["left"] > 1]


def _lay_smoke(d: Data, field: dict, bursts: list) -> None:
    """Smoke over each burst's hex and those within the radius, for as long as the wind lets it hang."""
    S = d.units["indirect"]["smoke"]
    lasts = S["lasts"][((field.get("weather") or {}).get("wind")) or "calm"]
    sm = field.setdefault("smoke", {})
    for at in bursts:
        for h in within(at, S["radius"]):
            key = f"{h[0]},{h[1]}"
            sm[key] = max(sm.get(key, 0), lasts)


def _shell_units(d: Data, us: list, tw: tuple, rng, acc: tuple, field: dict, under: list, k: int | None, b: dict, bursts: list) -> list:
    """The men struck in every unit by a battery's bursts, and their wounds."""
    I, (table, weapon) = d.units["indirect"], tw
    K, log = I["kinds"][b["kind"]], []
    att = {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}
    lost, dead, _ = acc
    for i, u in enumerate(us):
        if u.get("vehicle"):
            log += _shell_vehicle(d, us, i, bursts, K, (table, rng), acc, (k, b))
            continue
        struck = _shell_struck_unit(d, field, u, bursts, K, rng)
        if struck is None:
            continue
        under[i] = True
        if not struck:
            continue
        t = _take_hurt(u, _blows(d, att, _side(u, table), struck, I["attack"], 0, rng, _exposure(d, u, False, True), -1000))
        lost[i] += t["down"]
        dead[i] += t["dead"]
        log += _logged({"kind": "shelled", "sup": k, "name": b["name"], "dfd": i, "struck": struck}, t)
    return log


def _shell_vehicle(d: Data, us: list, i: int, bursts: list, kind: dict, tr: tuple, acc: tuple, src: tuple) -> list:
    """Shells or bombs bursting in a vehicle's own hex: each knocks it out at the kind's `knock`
    % times the vehicle's armour `shell`."""
    u = us[i]
    if u["men"] <= 0 or u["state"] == "fled":
        return []
    hexes = {f"{h[0]},{h[1]}" for row in footprint(d, u) for h in row}
    direct = sum(1 for at in bursts if f"{at[0]},{at[1]}" in hexes)
    p = kind.get("knock", 0) * armour_of(d, u)["shell"]
    if not direct or p <= 0:
        return []
    rng = tr[1]
    kills = sum(1 for _ in range(direct) if rng.randint(1, 100) <= p)
    k = knock_out(d, us, i, kills, tr, acc)
    if not k["knocked"]:
        return []
    return _logged({"kind": "knocked_out", "sup": src[0], "name": src[1]["name"], "dfd": i, "knocked": k["knocked"], "crew": k["crew"], "struck": k["struck"], **_riders_line(k)}, k["tally"])


def _shell_struck_unit(d: Data, field: dict, u: dict, bursts: list, kind: dict, rng) -> int | None:
    """Men of unit u struck by these bursts: each man in a hex within a burst's radius at the %
    for his distance (gone to ground, less; ground cover, less). None if no burst came near."""
    if u["men"] <= 0 or u["state"] == "fled":
        return None
    hexes = [h for row in footprint(d, u) for h in row]
    men, near, struck = men_by_hex(d, u), False, 0
    cuts = [_shell_cut(d, field, h, u.get("prone")) for h in hexes]
    for at in bursts:
        for h, n, cut in zip(hexes, men, cuts):
            dist = hdist(h, at)
            if dist > kind["radius"]:
                continue
            near = True
            p = kind["struck"][dist] * cut
            struck += sum(1 for _ in range(n) if rng.randint(1, 100) <= p)
    return struck if near else None


def _shell_cut(d: Data, field: dict | None, h, prone) -> float:
    """What shellfire's struck % is multiplied by for men in hex h: in woods, tree bursts (no
    cover, more struck, going to ground helps less); elsewhere going to ground and the ground's cover."""
    I = d.units["indirect"]
    TB = I["tree_burst"]
    bk = bunker_at(d, field, h)
    shelter = (100 - d.works["hex_works"][bk["type"]].get("cover_here", 0)) / 100 if bk else 1
    if ((field or {}).get("ground") or {}).get(f"{h[0]},{h[1]}", "open") in TB["ground"]:
        return TB["factor"] * (TB["prone"] if prone else 1) * shelter
    return (I["prone"] if prone else 1) * (100 - ground_at(d, field, h).get("cover", 0)) / 100 * shelter


def blast_weapon(d: Data, table: str) -> str | None:
    """The weapon whose wounds a storming party's grenades and charges use on this table, or None
    (no storming of bunkers)."""
    from .model import available_weapons
    A, have = d.units["assault"], available_weapons(d, table)
    return next((w for w in (A["weapon"], A["fallback"]) if w in have), None)


def _assault_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None) -> list:
    """Every unit ordered to storm the bunkers across its front: one roll for each bunker."""
    weapon, log = blast_weapon(d, table), []
    if not field or weapon is None:
        return log
    occ = occupancy(d, us)
    for i, u in enumerate(us):
        if u.get("assault") in d.units["assault"]["means"] and not _out(u):
            log += _storm(d, us, occ, i, (table, weapon), rng, acc, field)
    return log


def _storm(d: Data, us: list, occ: dict, i: int, tw: tuple, rng, acc: tuple, field: dict) -> list:
    """Unit i storms each intact, held bunker next to its front hexes once."""
    u, A, log, done = us[i], d.units["assault"], [], set()
    M = A["means"][u["assault"]]
    for h in (footprint(d, u) or [[]])[0]:
        hit = _struck_hex(us, occ, u, h)
        if hit is None:
            continue
        j, dirn = hit
        x = step(h, dirn)
        it = bunker_at(d, field, x)
        if it is None or f"{x[0]},{x[1]}" in done:
            continue
        done.add(f"{x[0]},{x[1]}")
        need, roll = M["knock"] + (A["pinned"] if us[j].get("pinned") else 0), rng.randint(1, 100)
        line = {"kind": "assault", "unit": i, "dfd": j, "means": u["assault"], "at": x, "roll": roll, "need": need, "out": roll <= need}
        if roll > need:
            log.append(line)
            continue
        it["out"] = True
        t = _bunker_struck(d, us, j, x, M, tw, rng, acc)
        acc[2][i] += t["down"]
        log += _logged(line, t)
    return log


def _bunker_struck(d: Data, us: list, j: int, x, means: dict, tw: tuple, rng, acc: tuple) -> dict:
    """The men in a bunker's hex when it falls: `struck` % of them, by blast or by flame."""
    b, (table, weapon) = us[j], tw
    hexes = [h for row in footprint(d, b) for h in row]
    k = next((n for n, h in enumerate(hexes) if h[0] == x[0] and h[1] == x[1]), None)
    there = men_by_hex(d, b)[k] if k is not None else 0
    struck = sum(1 for _ in range(there) if rng.randint(1, 100) <= means["struck"])
    if means.get("flame"):
        t = _new_tally()
        t.update(blows=struck, hits=struck, critical=struck, down=struck)
        for _ in range(struck):
            if rng.randint(1, 100) <= d.units["assault"]["flame_dead"]:
                t["dead"] += 1
            else:
                _hurt(t, "critical", {"lethal": "days", "infection": "high"}, True)
    else:
        att = {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}
        t = _blows(d, att, _side(b, table), struck, d.units["assault"]["attack"], 0, rng, _exposure(d, b, False, True), -1000)
    t = _take_hurt(b, t)
    lost, dead, _ = acc
    lost[j] += t["down"]
    dead[j] += t["dead"]
    return {**t, "struck": struck}


def _suppress_all(d: Data, us: list, under: list, rng) -> list:
    """Units under shellfire or machine-gun fire this exchange check Nerve; a failure pins them
    for the next exchange."""
    S, log = d.units["suppression"], []
    for i, u in enumerate(us):
        if not under[i] or u["men"] <= 0 or u["state"] in ("broken", "fled"):
            continue
        target = quality(d, u["quality"])["nerve"] + (S["prone"] if u.get("prone") else 0)
        roll = rng.randint(1, 100)
        if roll > target:
            u["pinned"] = 2
            log.append({"kind": "pinned", "unit": i, "roll": roll, "target": target})
    return log


def _fire_battery(d: Data, us: list, table: str, rng, acc: tuple, c: dict) -> list:
    """One battery's fire: at its target, any guns it knocks out there, then any balls that
    bound on into the unit behind."""
    a, b = us[c["att"]], us[c["dfd"]]
    gun = {**_side(a, table), "weapon": a["weapon"]}
    t = _take_hurt(b, cannonade(d, gun, b, c, rng, _exposure(d, b, False, True)))
    a["spent"] = a.get("spent", 0) + c["rounds"]
    if b.get("id") is not None:
        a["fired"] = {**(a.get("fired") or {}), str(b["id"]): c["dist"]}
    if t.get("dismounted"):
        b["guns_lost"] = b.get("guns_lost", 0) + t["dismounted"]
    lost, dead, dealt = acc
    _tally(lost, dead, dealt, c, t)
    log = _logged({"kind": "cannon", **c}, t)
    k = c["behind"]
    if k is not None:
        bh = us[k]
        t = _take_hurt(bh, ricochet(d, gun, bh, c, rng, _exposure(d, bh, False, True)))
        _tally(lost, dead, dealt, {"att": c["att"], "dfd": k}, t)
        log += _logged({"kind": "ricochet", **c, "dfd": k}, t)
    return log


def _breach_all(d: Data, us: list, field: dict | None) -> list:
    """Units ordered to breach (unit["breach"]) hack at the works on their front: each front
    hex's front rank works at the first breachable work across its front sides, or in the hex
    beyond. Progress is in the battle map's man-rounds, so a field hex side, `scale` times as
    long, takes `scale` times the work."""
    if not field or not _works(field):
        return []
    log, scale = [], d.units["hex_m"] / d.wounds["combat"]["move"]["hex_m"]
    per = d.units["exchange_rounds"] * d.units["breach_share"] / scale
    for i, u in enumerate(us):
        if u.get("breach") and not _out(u):
            log += _unit_breach(d, field, i, u, per)
    return log


def _unit_breach(d: Data, field: dict, i: int, u: dict, per: float) -> list:
    log, rows, men = [], footprint(d, u), men_by_hex(d, u)
    for k, h in enumerate(rows[0] if rows else []):
        hit = _breachable(d, field, u, h)
        if hit is None:
            continue
        kind, where, it = hit
        it["progress"] = it.get("progress", 0) + min(form(d, u)["abreast"], men[k]) * per
        if not C.intact(d, kind, it):
            log.append({"kind": "breach", "unit": i, "work": it["type"], "at": where})
    return log


def breaching(d: Data, field: dict | None, u: dict) -> set:
    """Indexes of the front hexes whose front rank is breaching works this exchange."""
    if not field or not u.get("breach") or not _works(field):
        return set()
    return {k for k, h in enumerate((footprint(d, u) or [[]])[0]) if _breachable(d, field, u, h)}


def _breachable(d: Data, field: dict, u: dict, h):
    """(edge or hex, its key, the item): the first work hex h's front rank can hack at."""
    works = _works(field)
    for dirn in (u["facing"], u["facing"] + 1):
        x = step(h, dirn)
        for it in C._edge_items(d, works, h, x):
            if C._spec(d, "edge", it).get("breach"):
                return "edge", C.edge_key(h, x), it
        it = C._hex_item(d, works, x)
        if it and C._spec(d, "hex", it).get("breach"):
            return "hex", C.hkey(x), it
    return None


def _copy_unit(u: dict) -> dict:
    return dict(u, hurt=dict(u.get("hurt", {})),
                heroes=[dict(h, wounds=list(h.get("wounds", [])), **({"held": dict(h["held"])} if h.get("held") else {})) for h in u.get("heroes", [])])


def _logged(line: dict, t: dict) -> list:
    """A log line for a tally, then one line for each blow that fell on a hero."""
    t = dict(t)
    hits = t.pop("heroes", [])
    return [{**line, **t}] + [{"kind": "herohit", "unit": line["dfd"], **h} for h in hits]


def _take_hurt(u: dict, t: dict) -> dict:
    """Move a tally's wounded onto the unit struck; the tally (for the log) keeps the rest."""
    t = dict(t)
    for k, n in t.pop("hurt", {}).items():
        u["hurt"][k] = u["hurt"].get(k, 0) + n
    return t


def _tally(lost: list, dead: list, dealt: list, s: dict, t: dict) -> None:
    lost[s["dfd"]] += t["down"]
    dead[s["dfd"]] += t["dead"]
    dealt[s["att"]] += t["down"]


def _morale_all(d: Data, us: list, occ: dict, before: list, acc: tuple, rng, table: str = "", field: dict | None = None) -> list:
    """Every unit still in the fight checks; any that breaks is struck at once by the enemies
    touching it, every man of them."""
    (lost, dealt, flanked), log, broke = acc, [], []
    for i, u in enumerate(us):
        if u["state"] in ("broken", "fled") or u["men"] <= 0:
            continue
        near = _adjacent_units(d, us, occ, i)
        unit = {"quality": u["quality"], "start": u["start"], "down": u["down"], "lost": lost[i], "dealt": dealt[i],
                "men": before[i], "state": u["state"], "leader": leader_state(u), "flanked": flanked[i],
                "contact": any(us[j]["side"] != u["side"] for j in near),
                "friends": any(us[j]["side"] == u["side"] and us[j]["state"] == "steady" for j in near),
                "dug": bool(u.get("prone")) or in_bunker(d, field, u)}
        m = morale(d, unit, rng.randint(1, 100))
        if m["check"]:
            log.append({"kind": "morale", "unit": i, "target": m["target"], "from": u["state"], "state": m["state"]})
        if m["state"] == "broken":
            broke.append(i)
        u["state"] = m["state"]
    for j in broke:
        log += _rout_strike(d, us, occ, j, table, rng)
    return log


def _rout_strike(d: Data, us: list, occ: dict, j: int, table: str, rng) -> list:
    """A unit that has just broken is struck by every man of each enemy unit touching it."""
    log = []
    for i in _adjacent_units(d, us, occ, j):
        a, b = us[i], us[j]
        if a["side"] == b["side"] or a["state"] in ("broken", "fled") or a["men"] <= 0 or b["men"] <= 0:
            continue
        t = _take_hurt(b, melee(d, _side(a, table, d), _side(b, table, d), a["men"], rng, rout=True, exposed=_exposure(d, b, True)))
        cut = min(t["down"], b["men"])
        b.update(men=b["men"] - cut, down=b["down"] + cut, dead=b["dead"] + min(t["dead"], cut))
        log += _logged({"kind": "rout", "att": i, "dfd": j, "men": a["men"], "situation": "rear", "rout": True}, t)
    return log


# ---------- movement ----------

def allowance(d: Data, u: dict) -> int:
    """Hexes a unit may move in an exchange (twice this for a charge). A battery limbering,
    unlimbering or resupplying does not move; unlimbered, it can only be manhandled a hex or so."""
    if (u.get("prone") or u.get("pinned")) and u["state"] not in ("broken", "fled"):   # gone to ground or pinned (a broken unit gets up and runs)
        return 0
    if is_battery(d, u) and not u.get("abandoned") and u["state"] != "broken":   # crews running from their guns run on foot
        if u.get("limbering") or u.get("resupplying"):
            return 0
        if not u.get("limbered"):
            return _carrying(d, u, d.units["artillery"]["pushed"])
    return _carrying(d, u, d.units["mounted_move"] if u.get("mounted") else form(d, u)["move"])


def _carrying(d: Data, u: dict, move: int) -> int:
    """A unit's move, slowed (heroes.carried, at least 1 hex) if it has a lamed hero with it."""
    if move and any(lamed(d, h) for h in u.get("heroes", [])):
        return max(1, math.floor(move * d.units["heroes"]["carried"]))
    return move


def turn_cost(d: Data, u: dict) -> int:
    """Hexes of movement to turn the facing one step: 1 for every turn_per hexes of front."""
    n = math.ceil(max(1, u["men"]) / form(d, u)["per_hex"])
    return max(1, math.ceil(min(u["width"], n) / d.units["turn_per"]))


def _fits(d: Data, units: list, i: int, u: dict, size: tuple, field: dict | None = None) -> bool:
    """Unit i placed as u: on the map, on no other unit's hexes, and on ground it can stand on
    (no wagons; for horses, no marsh, stakes or felled trees), with no palisade or wall
    running through it."""
    occ = occupancy(d, [x for k, x in enumerate(units) if k != i])
    hexes = [h for row in footprint(d, u) for h in row]
    if not all(0 <= h[0] < size[0] and 0 <= h[1] < size[1] and f"{h[0]},{h[1]}" not in occ for h in hexes):
        return False
    return not field or _stands(d, field, u, hexes)


def _stands(d: Data, field: dict, u: dict, hexes: list) -> bool:
    keys = {f"{h[0]},{h[1]}" for h in hexes}
    for h in hexes:
        if not _can_enter(d, field, u, h):
            return False
        for dirn in range(6):
            x = step(h, dirn)
            if f"{x[0]},{x[1]}" in keys and _wall_between(d, field, h, x):
                return False
    return True


def _can_enter(d: Data, field: dict, u: dict, h) -> bool:
    if ground_at(d, field, h).get("impassable"):
        return False
    if u.get("vehicle") and _ground_key(field, h) not in d.units["vehicles"]["ground"]:
        return False
    it = C._hex_item(d, _works(field), h)
    if it and C._spec(d, "hex", it).get("enter") is None:
        return False
    if not u.get("mounted"):
        return True
    return not ground_at(d, field, h).get("no_horse") and not (it and C._spec(d, "hex", it).get("no_horse"))


def _wall_between(d: Data, field: dict, a, b) -> bool:
    """A palisade, wall or barred gate between hexes a and b (open gates are left out)."""
    for it in C._edge_items(d, _works(field), a, b):
        s = C._spec(d, "edge", it)
        if s.get("cross") is None or s.get("gate"):
            return True
    return False


def step_cost(d: Data, field: dict | None, u: dict, a, b) -> int | None:
    """Movement for one hex of a unit to step from a to b: 1, plus works crossed and entered,
    plus the ground (rough, woods, marsh), plus deep mud or snow. None if it cannot. A unit pays
    the worst of all its hexes' (_front_cost)."""
    if not field:
        return 1
    if not _can_enter(d, field, u, b):
        return None
    c = C.step_cost(d, _works(field), a, b)
    if c is None:
        return None
    wx = field.get("weather") or {}
    going = d.units["vehicles"]["ground"][_ground_key(field, b)] if u.get("vehicle") else ground_at(d, field, b)["move"]
    return c + going - 1 + C.deep_going(d, wx.get("ground")) + (cold_of(d, field) or {}).get("move", 0) + (light_of(d, field) or {}).get("move", 0)


def _ground_key(field: dict | None, h) -> str:
    """The ground kind painted on hex h (open if none)."""
    return ((field or {}).get("ground") or {}).get(f"{h[0]},{h[1]}", "open")


def _path_len(d: Data, units: list, i: int, goal, size: tuple, limit: int, field: dict | None = None) -> int | None:
    """Least movement for the unit's middle hex from where it is to goal (step_cost), not
    through other units' hexes; None if more than limit."""
    occ = occupancy(d, [x for k, x in enumerate(units) if k != i])
    u, start = units[i], tuple(units[i]["pos"])
    best, heap, done = {start: 0}, [(0, start)], set()
    while heap:
        cost, h = heapq.heappop(heap)
        if h in done:
            continue
        if list(h) == list(goal):
            return cost
        done.add(h)
        for x, c in _steps_from(d, field, u, h, occ, size):
            if cost + c <= limit and cost + c < best.get(x, limit + 1):
                best[x] = cost + c
                heapq.heappush(heap, (cost + c, x))
    return None


def _steps_from(d: Data, field: dict | None, u: dict, h: tuple, occ: dict, size: tuple) -> list:
    """(hex, cost) for each step the unit's middle hex can take from h: the worst that any hex
    of the unit, front, flanks and rear, pays for the same step (one that cannot step blocks it)."""
    out, front = [], [x for row in footprint(d, {**u, "pos": list(h)}) for x in row] if field else [list(h)]
    for dirn in range(6):
        x = tuple(step(list(h), dirn))
        if not (0 <= x[0] < size[0] and 0 <= x[1] < size[1]) or f"{x[0]},{x[1]}" in occ:
            continue
        sc = _front_cost(d, field, u, front, dirn, size)
        if sc is not None:
            out.append((x, sc))
    return out


def _front_cost(d: Data, field: dict | None, u: dict, front: list, dirn: int, size: tuple) -> int | None:
    """The worst step cost of a front row's hexes stepping in direction dirn (off the map: not counted)."""
    worst = 0
    for f in front:
        y = step(f, dirn)
        if not (0 <= y[0] < size[0] and 0 <= y[1] < size[1]):
            continue
        c = step_cost(d, field, u, f, y)
        if c is None:
            return None
        worst = max(worst, c)
    return worst or 1


def move(d: Data, units: list, i: int, pos, facing: int, size: tuple, field: dict | None = None) -> dict:
    """Can unit i end its move with its middle front hex at pos, facing `facing`? {ok, cost,
    charge, why}. Turning costs turn_cost a step. A unit already in contact cannot move. A
    move that ends in contact with an enemy may be up to charge_move times the allowance (a
    charge; not for a shaken unit)."""
    u = units[i]
    why = _held_still(d, units, i, pos, facing)
    if why:
        return {"ok": False, "why": why}
    turns = min((facing - u["facing"]) % 6, (u["facing"] - facing) % 6)
    most = allowance(d, u) * d.units["charge_move"]
    steps = _path_len(d, units, i, pos, size, most, field)
    if steps is None:
        return {"ok": False, "why": "too far, or no way through"}
    moved = {**u, "pos": list(pos), "facing": facing % 6}
    if not _fits(d, units, i, moved, size, field):
        return {"ok": False, "why": "no room there"}
    cost = steps + turns * turn_cost(d, u) + (sweep_cost(d, field, {**u, "pos": list(pos)}, moved) if turns else 0)
    after = [moved if k == i else x for k, x in enumerate(units)]
    contact = in_contact(d, after, occupancy(d, after), i)
    if cost <= allowance(d, u):
        return {"ok": True, "cost": cost, "charge": contact and steps > 0}
    if contact and u["state"] == "steady" and cost <= most:
        return {"ok": True, "cost": cost, "charge": True}
    return {"ok": False, "why": "too far"}


def _held_still(d: Data, units: list, i: int, pos, facing: int) -> str | None:
    """Why unit i cannot move to pos (or turn to facing) at all, or None: running, in contact,
    lost in the dark, or with vehicles that cannot move."""
    u = units[i]
    goes = list(pos) != u["pos"]
    if u["state"] in ("broken", "fled"):
        return "it is running"
    if in_contact(d, units, occupancy(d, units), i) and (goes or facing != u["facing"]):
        return "it is in contact"
    if u.get("lost") and goes:
        return "it has lost its way in the dark (it may turn)"
    if u.get("immobile") and goes:
        return f"{u['immobile']} of its vehicles cannot move (abandon them to move on; it may turn)"
    return None


def sweep_cost(d: Data, field: dict | None, before: dict, after: dict) -> int:
    """What a unit turning from `before` to `after` pays for the ground its ends sweep over: the
    worst extra going (its move less 1) of the hexes it comes to stand on that it did not before."""
    if not field:
        return 0
    old = {tuple(x) for row in footprint(d, before) for x in row}
    new = [x for row in footprint(d, after) for x in row if tuple(x) not in old]
    going = (lambda x: d.units["vehicles"]["ground"].get(_ground_key(field, x), 1)) if after.get("vehicle") else (lambda x: ground_at(d, field, x)["move"])
    return max([going(x) - 1 for x in new] + [0])


def abandon_immobile(d: Data, u: dict) -> dict:
    """A vehicle unit leaves its immobilised vehicles: their crews leave the fight unhurt
    (bailed). Returns the unit."""
    K, n = vehicle_kind(d, u), u.get("immobile", 0)
    if not K or n <= 0:
        return u
    out = min(u["men"], n * K["crew"])
    v = {**u, "men": u["men"] - out, "bailed": u.get("bailed", 0) + out, "immobile": 0}
    v["gunless"] = min(v.get("gunless", 0), vehicles_left(d, v))
    return v


def carries(d: Data, u: dict) -> int:
    """Men a vehicle unit can carry: its vehicles left times its kind's `carry` (0 if none)."""
    K = vehicle_kind(d, u)
    return vehicles_left(d, u) * K.get("carry", 0) if K else 0


def _cannot_mount(d: Data, units: list, i: int, j: int) -> str | None:
    """Why foot unit i cannot get aboard vehicle unit j, or None."""
    u, c, occ = units[i], units[j], occupancy(d, units)
    checks = [
        (lambda: u.get("vehicle") or is_gun(d, u["weapon"]) or u.get("mounted"), "only men on foot can ride"),
        (lambda: not c.get("vehicle") or c["side"] != u["side"] or carries(d, c) <= 0, "those are not its side's carriers"),
        (lambda: c.get("riders"), "they carry men already"),
        (lambda: u["men"] > carries(d, c), f"they have room for {carries(d, c)}"),
        (lambda: _out(u) or _out(c) or in_contact(d, units, occ, i) or in_contact(d, units, occ, j), "one of them is in contact or broken"),
        (lambda: min(hdist(a, b) for r1 in footprint(d, u) for a in r1 for r2 in footprint(d, c) for b in r2) > 1, "they are not beside the carriers"),
    ]
    return next((why for test, why in checks if test()), None)


def mount(d: Data, units: list, i: int, j: int) -> dict:
    """Foot unit i gets aboard vehicle unit j (its side's carriers, room for all its men, within a
    hex of them, neither in contact, j carrying no one yet). -> {ok, why, units}: unit i goes
    into j's riders."""
    why = _cannot_mount(d, units, i, j)
    if why:
        return {"ok": False, "why": why, "units": units}
    rider = {k: v for k, v in units[i].items() if k not in ("pos", "facing")}
    out = [{**x, "riders": rider} if k == j else x for k, x in enumerate(units) if k != i]
    return {"ok": True, "why": None, "units": out}


def dismount(d: Data, units: list, j: int, size: tuple, field: dict | None = None) -> dict:
    """Vehicle unit j's riders get down beside it: behind it if they fit, else beside it or in
    front, facing its way (spots tried in a fixed order). -> {ok, why, units}: the riders are
    added as the last unit."""
    c = units[j]
    R = c.get("riders")
    if not R:
        return {"ok": False, "why": "no one is aboard", "units": units}
    back, f = (c["facing"] + 3) % 6, c["facing"]
    for dirn, n in [(back, 1), (back, 2), ((f + 2) % 6, 1), ((f + 5) % 6, 1), ((f + 2) % 6, 2), ((f + 5) % 6, 2), (f, 1), (back, 3), (back, 4)]:
        spot = {**R, "pos": step(c["pos"], dirn, n), "facing": f}
        trial = [*units, spot]
        if _fits(d, trial, len(units), spot, size, field):
            out = [{k: v for k, v in x.items() if k != "riders"} if k == j else x for k, x in enumerate(units)]
            return {"ok": True, "why": None, "units": [*out, spot]}
    return {"ok": False, "why": "no room to get down beside them", "units": units}


def _vehicles_after(d: Data, us: list, field: dict | None) -> list:
    """After the losses: a vehicle unit's immobilised and gunless vehicles are no more than it has
    left; the riders of one with none left get down where it stood (log lines)."""
    log = []
    for j, u in enumerate(list(us)):
        if not u.get("vehicle"):
            continue
        left = vehicles_left(d, u)
        for k in ("immobile", "gunless"):
            if k in u:
                u[k] = min(u[k], left)
        if left == 0 and u.get("riders") and u["riders"]["men"] > 0:
            r = dismount(d, us, j, _size(d, field), field)
            if r["ok"]:
                us[:] = r["units"]
                log.append({"kind": "bailout", "unit": j, "riders": len(us) - 1, "men": us[-1]["men"]})
    return log


def flee(d: Data, units: list, i: int, size: tuple, field: dict | None = None) -> dict:
    """A broken unit runs straight back as far as its allowance takes it; off the map, it has
    fled the field. Returns the unit."""
    u = dict(units[i])
    back = (u["facing"] + 3) % 6
    for _ in range(allowance(d, u)):
        nxt = {**u, "pos": step(u["pos"], back)}
        if not all(0 <= h[0] < size[0] and 0 <= h[1] < size[1] for row in footprint(d, nxt) for h in row):
            return {**u, "state": "fled"}
        if step_cost(d, field, u, u["pos"], nxt["pos"]) is None or not _fits(d, units, i, nxt, size, field):
            break
        u = nxt
    return u



HERO_EXAMPLES = [("Knight in mail", "hauberk"), ("Knight in plate", "full_plate"), ("Champion, no armour", "none")]


def hero_examples(d: Data, table: str, runs: int, seed: int) -> list[dict]:
    """A hero (attack 65, defence 45, Nerve 65, sword) leading 120 regular billmen in jacks
    from the front against the same, fought until one side breaks: % of runs he was wounded,
    down and killed, and the men he put down (mean)."""
    out = []
    for label, kit in HERO_EXAMPLES:
        r = {"label": label, "wounded": 0, "down": 0, "dead": 0, "felled": 0}
        for k in range(runs):
            rng = SeededDice(seed * 7919 + k)
            us = [_example_unit(0, [20, 20], 0), _example_unit(1, [21, 20], 3)]
            us[0]["heroes"] = [{"id": 1, "name": "Hero", "role": "front", "attack": 65, "defence": 45, "nerve": 65,
                                "weapon": "sword", "kit": kit, "leader": True, "state": "up", "wounds": []}]
            for _ in range(60):
                us, log = exchange(d, us, table, rng)
                r["felled"] += sum(x["down"] for x in log if x["kind"] == "hero")
                if any(u["state"] == "broken" for u in us):
                    break
            h = us[0]["heroes"][0]
            r["wounded"] += bool(h["wounds"])
            r["down"] += h["state"] == "down"
            r["dead"] += h["state"] == "dead"
        out.append({**r, **{k: 100 * r[k] / runs for k in ("wounded", "down", "dead")}, "felled": r["felled"] / runs})
    return out


def _example_unit(side: int, pos: list, facing: int) -> dict:
    return {"side": side, "pos": pos, "facing": facing, "men": 120, "start": 120, "down": 0, "dead": 0, "width": 3,
            "quality": "regular", "weapon": "bill", "kit": "jack_sallet", "formation": "close", "state": "steady",
            "mounted": False, "charged": False, "leader": None}

# ---------- after the battle ----------

def standing(u: dict) -> bool:
    return u["men"] > 0 and u["state"] in ("steady", "shaken")


def aftermath(d: Data, units: list, care: list, rng) -> list:
    """What becomes of each unit's wounded when the battle ends (units.yaml aftermath). care:
    each unit's camp care (none, field, shelter). Returns, per unit, {left (down men left on a
    lost field, dead), died (of wounds before treatment), cases (survivors on the wound
    track)}. A man wounded twice is counted once: the down are capped at those down and not
    dead, the walking wounded at the men still on their feet."""
    am, d100 = d.units["aftermath"], (lambda: rng.randint(1, 100))
    lost_sides = {u["side"] for u in units} - {u["side"] for u in units if standing(u)}
    return [_unit_after(d, u, care[i], am["left_behind"] and u["side"] in lost_sides, d100) for i, u in enumerate(units)]


def _unit_after(d: Data, u: dict, care: str, abandon: bool, d100) -> dict:
    """One unit's wounded after the battle: left behind, dead of their wounds, or carried."""
    r = {"left": 0, "died": 0, "cases": []}
    room = {"1": max(0, u.get("down", 0) - u.get("dead", 0)), "0": max(0, u["men"])}
    for k in sorted(u.get("hurt", {})):
        sev, lethal, inf, down = k.split("|")
        n = min(u["hurt"][k], room[down])
        room[down] -= n
        if down == "1" and abandon:
            r["left"] += n
            continue
        for _ in range(n):
            if _dies(d.units["aftermath"], lethal, care, d100):
                r["died"] += 1
            else:
                r["cases"].append(wound_case(d, sev, lethal, inf, d100))
    return r


def _dies(am: dict, lethal: str, care: str, d100) -> bool:
    """A wound that kills in minutes or hours: does it, before help comes?"""
    if lethal == "minutes":
        return d100() > am["saved"]["minutes"]
    if lethal == "hours":
        return d100() > am["saved"]["hours"][care]
    return False


# ---------- guns ----------
# A battery: a unit whose weapon is a gun (units.yaml artillery), its men the crews. It is
# limbered (u["limbered"]: moves, cannot fire) or not; u["limbering"]: changing over this
# exchange (neither moves nor fires); u["abandoned"]: broke and left its guns.

def is_gun(d: Data, weapon: str) -> bool:
    return weapon in d.units.get("artillery", {}).get("guns", [])


def is_battery(d: Data, u: dict) -> bool:
    return is_gun(d, u["weapon"])


def melee_weapon(d: Data, u: dict) -> str:
    """The weapon a unit fights hand to hand with: a battery's crews have their own."""
    return d.units["artillery"]["crew_weapon"] if is_battery(d, u) else u["weapon"]


def guns_of(d: Data, u: dict) -> int:
    """The guns a battery brought into action: one for every `crew` men it started with."""
    return math.ceil(u.get("start", u["men"]) / d.units["artillery"]["crew"])


def guns_served(d: Data, u: dict) -> int:
    """Guns the crews still serve: one for every `crew` men left, up to the guns not knocked out."""
    crew = d.units["artillery"]["crew"]
    return max(0, min(guns_of(d, u) - u.get("guns_lost", 0), math.ceil(max(0, u["men"]) / crew)))


def ammo_left(d: Data, u: dict) -> int:
    """Rounds the battery has left: `ammo` a gun it brought, less those it has fired."""
    return max(0, guns_of(d, u) * d.units["artillery"]["ammo"] - u.get("spent", 0))


def gun_weather(d: Data, field: dict | None, dist: int, h=None, t=None, seer: dict | None = None) -> dict:
    """The weather's effect on guns: no laying them on what cannot be seen (less with rain or
    snow driven into the gunners' faces); the wind as on firearms; no reach from the wind."""
    out = {"blocked": None, "penalty": 0, "misfire": 0, "reach": 0}
    weather = (field or {}).get("weather")
    if not weather or not d.weather:
        return out
    cond = d.weather["conditions"][weather["cond"]]
    vis = cond.get("visibility")
    if vis is not None and cond["precip"] != "none" and C.wind_lie(d, weather, h, t, _up(field)) == "against":
        vis = vis * d.weather["driven_sight"] // 100
    if vis is not None and dist * d.units["range_scale"] > vis:
        out["blocked"] = f"{cond['name']}: the guns cannot be laid on what cannot be seen."
        return out
    out["penalty"] = next(x for x in d.weather["winds"] if x["id"] == weather["wind"])["firearm"]
    return in_the_dark(d, field, dist, t, out, seer)


def _chance_at(bands: list, dist: int) -> int:
    """The % for this distance from [[up to hexes, %], ...]; 0 beyond the last."""
    return next((ch for to, ch in bands if dist <= to), 0)


def _can_fire(d: Data, u: dict) -> bool:
    """Unlimbered, not changing over or resupplying, not broken, with guns served and rounds left."""
    if not is_battery(d, u) or _out(u) or u.get("abandoned"):
        return False
    if u.get("limbered") or u.get("limbering") or u.get("resupplying"):
        return False
    return guns_served(d, u) > 0 and ammo_left(d, u) > 0


def cannonades(d: Data, units: list, field: dict | None = None) -> list:
    """Which batteries fire at whom: [{att, dfd, guns, rounds, dist, shot (canister, round or
    shell), cover, penalty, named, graze, behind, beyond, fuse, section}]. A battery fires unlimbered, not changing over, not
    broken and not in contact, with the guns its crews still serve and the rounds it has left,
    at its named target or the nearest enemy in range, in sight and in front, with a clear line
    of fire; a section it split off (u["section"]: {target, guns, shot}) at that target, if it
    can. The shot is the GM's order (u["shot"]) if the guns have it and it reaches, else by range.
    behind: the unit a bounding round-shot ball can strike, beyond: how far past; fuse: the
    gunners' fuse setting (shell)."""
    occ, out, A = occupancy(d, units), [], d.units.get("artillery")
    for i, u in enumerate(units):
        if not A or not _can_fire(d, u) or in_contact(d, units, occ, i):
            continue
        best = _target(d, units, i, field, occ)
        if best is not None:
            out += _battery_fires(d, units, occ, field, i, best)
    return out


def sections(u: dict) -> list:
    """The sections a battery has split off, in order ({target, guns, shot}): u.sections, or the
    single u.section of older saves."""
    return list(u.get("sections") or ([u["section"]] if u.get("section") else []))


def _battery_fires(d: Data, units: list, occ: dict, field: dict | None, i: int, best: tuple) -> list:
    """Battery i's fire at best, and each section's at its own target, in order, if it can fire
    on it: a section takes its guns from those the battery still has, at least one staying with
    the battery; one that cannot fire on its target fires with the rest. The rounds go to the
    battery's guns first, then to the sections in order."""
    u = units[i]
    guns, ammo, spare, firing = guns_served(d, u), ammo_left(d, u), guns_served(d, u) - 1, []
    for sec in sections(u):
        n = min(sec.get("guns", 0), spare)
        at = _named_target(d, units, i, field, occ, sec.get("target")) if n > 0 else None
        if at is not None:
            firing.append((sec, n, at))
            spare -= n
    main = _battery_fire(d, units, (occ, field), i, best, {"guns": guns - sum(n for _, n, _ in firing), "ammo": ammo, "shot": u.get("shot")})
    out, left = [main], ammo - main["rounds"]
    for sec, n, at in firing:
        if left <= 0:
            break
        f = _battery_fire(d, units, (occ, field), i, at, {"guns": n, "ammo": left, "shot": sec.get("shot"), "section": True})
        out.append(f)
        left -= f["rounds"]
    return out


def _battery_fire(d: Data, units: list, ground: tuple, i: int, best: tuple, order: dict) -> dict:
    """Guns of battery i firing at best (from _target), as cannonades gives it. ground: (occ,
    field); order: {guns, ammo (rounds left), shot (ordered, or None), per (rounds a gun),
    section}."""
    (occ, field), A, u = ground, d.units["artillery"], units[i]
    wx, shot = gun_weather(d, field, best[0], best[2], best[3], _seer(u)), _shot(d, u, best[0], order.get("shot"))
    behind = _ricochet_at(d, occ, field, i, best) if shot == "round" else None
    graze = A["canister"]["graze"] if shot == "canister" and best[0] > A["canister"]["strike"][0][0] and _firm(d, field, best) else 0
    tgt = units[best[1]]
    tid = tgt.get("id")
    return {"att": i, "dfd": best[1], "guns": order["guns"], "rounds": min(order["guns"] * order.get("per", A["rounds"]), order["ammo"]),
            "dist": best[0], "shot": shot, "cover": cover_at(d, field, best[2], best[3]) + ground_cover(d, tgt), "penalty": wx["penalty"],
            "named": bool(order.get("section")) or (tid is not None and tid == u.get("target")), "graze": graze, "bore": gun_kind(u),
            "behind": behind[0] if behind else None, "beyond": behind[1] if behind else 0,
            "fuse": fuse_setting(d, u, tid, best[0]) if shot == "shell" else 0, "section": bool(order.get("section"))}


def fuse_setting(d: Data, u: dict, tid, dist: int) -> int:
    """How far the gunners' cut fuses widen the air band (narrow it, if negative): the crews'
    quality, and more if the battery fired at this target last exchange at much the same range."""
    F = d.units["artillery"].get("set_fuse")
    if not F:
        return 0
    was = (u.get("laid") or {}).get(str(tid)) if tid is not None else None
    return F["quality"].get(u["quality"], 0) + (F["ranged"] if was is not None and abs(was - dist) <= F["within"] else 0)


def closing_fire(d: Data, units: list, field: dict | None = None) -> list:
    """Batteries charged in front this exchange (as cannonades gives them, closing: True): each
    that can fire gives its first charger `closing` rounds of canister a gun as it comes in."""
    A, out = d.units.get("artillery"), []
    if not A or "closing" not in A:
        return out
    occ = occupancy(d, units)
    for i, u in enumerate(units):
        best = _charger(d, units, occ, field, i) if _can_fire(d, u) else None
        if best is not None:
            order = {"guns": guns_served(d, u), "ammo": ammo_left(d, u), "shot": "canister", "per": A["closing"]}
            out.append({**_battery_fire(d, units, (occ, field), i, best, order), "named": False, "closing": True})
    return out


def _charger(d: Data, units: list, occ: dict, field: dict | None, i: int):
    """(distance, index, gun hex, its hex) of the first enemy that charged battery i in front this exchange, or None."""
    u = units[i]
    front, fv = footprint(d, u)[0], _fvec(u["facing"])
    for j in _adjacent_units(d, units, occ, i):
        e = units[j]
        if e["side"] == u["side"] or not e.get("charged") or _out(e):
            continue
        near = _nearest_ahead(d, u, front, fv, [t for row in footprint(d, e) for t in row], field)
        if near is not None:
            return near[0], j, near[1], near[2]
    return None


def gun_kind(u: dict) -> str:
    """A battery's guns: smoothbore, rifled or howitzer (a battery saved as howitzer: true, howitzer)."""
    return u.get("guns") or ("howitzer" if u.get("howitzer") else "smoothbore")


def gun_range(d: Data, u: dict) -> int:
    """How far a battery's guns reach, in field hexes: rifled guns further."""
    A = d.units["artillery"]
    return A["rifled"]["range"] if gun_kind(u) == "rifled" else A["range"]


def _shot(d: Data, u: dict, dist: int, want: str | None = None) -> str:
    """The shot ordered (want), if the guns fire it and it reaches (canister only within
    canister range); else canister within canister range, beyond it shell from howitzers and
    rifled guns, round shot from smoothbores."""
    A = d.units["artillery"]
    if want in A.get("shots", {}).get(gun_kind(u), []) and (want != "canister" or dist <= A["canister_to"]):
        return want
    if dist <= A["canister_to"]:
        return "canister"
    return "round" if gun_kind(u) == "smoothbore" else "shell"


def _firm(d: Data, field: dict | None, best: tuple) -> bool:
    """Firm ground all the way from the gun to the target hex: no mud or snow, nothing that stops shot."""
    dist, _, h, t = best
    return not _soft(d, field) and not any(ground_at(d, field, x).get("stops_shot") for x in ray(h, t, dist)[1:])


def _soft(d: Data, field: dict | None) -> bool:
    """Mud or snow deep enough to stop a ball bounding."""
    g, soft = ((field or {}).get("weather") or {}).get("ground") or {}, d.units["artillery"]["ricochet"]["soft"]
    return g.get("mud", 0) >= soft or g.get("snow", 0) >= soft


def _ricochet_at(d: Data, occ: dict, field: dict | None, i: int, best: tuple):
    """(unit index, hexes past the target) of the first other unit a ball fired from best's
    shooter hex at its target hex bounds into, or None (soft or broken ground stops it)."""
    if _soft(d, field):
        return None
    dist, j, h, t = best
    beyond = d.units["artillery"]["ricochet"]["beyond"]
    for k, x in enumerate(ray(h, t, dist + beyond)[dist:]):
        if ground_at(d, field, x).get("stops_shot"):
            return None
        u = occ.get(f"{x[0]},{x[1]}")
        if k > 0 and u is not None and u not in (i, j):
            return u, k
    return None


def _canister_struck(art: dict, c: dict, cut: float, rounds: int, rng) -> int:
    """Men hit by canister: each ball a chance (more on firm ground, the balls skipping on; a
    rifle's canister throws fewer balls)."""
    p = (_chance_at(art["canister"]["strike"], c["dist"]) + c.get("graze", 0)) * cut
    balls = art["rifled"]["canister_balls"] if c.get("bore") == "rifled" else art["canister"]["balls"]
    return sum(rng.randint(1, 100) <= p for _ in range(rounds * balls))


def _fuse_at(bands: list, roll: int) -> str:
    """What a shell's fuse does on this d100 roll: [[up to, early|air|ground|blind], ...]."""
    return next(what for to, what in bands if roll <= to)


def set_fuse(bands: list, by: int) -> list:
    """The fuse table with its air band widened by `by` (narrowed, if negative), taken from or
    given to the band after it, and never past its neighbours."""
    out = []
    for k, (to, what) in enumerate(bands):
        if what == "air" and by:
            lo, hi = bands[k - 1][0] if k else 0, bands[k + 1][0] if k + 1 < len(bands) else 100
            to = max(lo, min(hi, to + by))
        out.append([to, what])
    return out


def _shell_struck(art: dict, c: dict, factor: float, rounds: int, rng) -> tuple:
    """(men hit, shells that burst on the unit, of them in the air): each shell falls on the unit
    with the chance for its range (times factor: formation and weather; a rifle's own figures
    and percussion fuse for rifled guns), then its fuse decides:
    early (harmless), air (fragments at air_hit %, cover counting half), ground (fragment_hit %,
    less the cover) or blind."""
    H = art["howitzer"]
    R = art["rifled"] if c.get("bore") == "rifled" else H          # rifled shell: its own strike and percussion fuse
    p, fuses = _chance_at(R["strike"], c["dist"]) * factor, set_fuse(R["fuse"], c.get("fuse", 0))
    hit_at = {"air": H["air_hit"] * (100 - c["cover"] / 2) / 100, "ground": H["fragment_hit"] * (100 - c["cover"]) / 100}
    struck = bursts = air = 0
    for _ in range(rounds):
        if rng.randint(1, 100) > p:
            continue
        fuse = _fuse_at(fuses, rng.randint(1, 100))
        if fuse not in hit_at:
            continue
        bursts += 1
        air += fuse == "air"
        struck += sum(rng.randint(1, 100) <= hit_at[fuse] for _ in range(H["fragments"]))
    return struck, bursts, air


def _round_shot_struck(d: Data, art: dict, p: float, rounds: int, target: dict, rng) -> tuple:
    """(men hit, balls that struck) by round shot: each ball that strikes the unit (p %) goes
    through its ranks."""
    rs = art["round_shot"]
    path = min(rs["path_max"], form(d, target)["ranks"] * len(footprint(d, target)))
    struck = hits = 0
    for _ in range(rounds):
        if rng.randint(1, 100) <= p:
            hits += 1
            struck += sum(rng.randint(1, 100) <= rs["file"] for _ in range(path))
    return struck, hits


def cannonade(d: Data, att: dict, target: dict, c: dict, rng, exposed: tuple = ()) -> dict:
    """One exchange of a battery's fire (att: the battery as a side, with its gun; c, from
    cannonades) at the target unit: the men struck, then a wound roll for each."""
    A = d.units["artillery"]
    rounds = c["rounds"]
    cut = form(d, target)["missile_factor"] * (100 - c["cover"] - c["penalty"]) / 100
    hits = air = 0
    if c["shot"] == "canister":
        struck = _canister_struck(A, c, cut, rounds, rng)
    elif c["shot"] == "shell":
        struck, hits, air = _shell_struck(A, c, form(d, target)["missile_factor"] * (100 - c["penalty"]) / 100, rounds, rng)
    else:
        struck, hits = _round_shot_struck(d, A, _chance_at(A["round_shot"]["strike"], c["dist"]) * cut, rounds, target, rng)
    t = _blows(d, att, _side(target, att["table"]), struck, A["attack"], 0, rng, exposed, -1000)
    if c["shot"] == "shell":
        t["bursts"], t["air"] = hits, air
    if is_battery(d, target):
        t["dismounted"] = min(sum(rng.randint(1, 100) <= A["dismount"] for _ in range(hits)), guns_served(d, target))
    return t


def ricochet(d: Data, att: dict, target: dict, c: dict, rng, exposed: tuple = ()) -> dict:
    """The balls of a battery's round shot that bound on into the unit behind its target
    (c from cannonades: behind, beyond): the men struck, then a wound roll for each."""
    A = d.units["artillery"]
    p = _chance_at(A["ricochet"]["strike"], c["beyond"]) * form(d, target)["missile_factor"]
    struck, _ = _round_shot_struck(d, A, p, c["rounds"], target, rng)
    return _blows(d, att, _side(target, att["table"]), struck, A["attack"], 0, rng, exposed, -1000)


def _battery_after(d: Data, u: dict) -> None:
    """At the end of an exchange: a battery that was changing over is now limbered or not, one
    that was resupplying has its rounds again, and one that has broken has left its guns."""
    if not is_battery(d, u):
        return
    u["laid"] = u.pop("fired", None) or {}
    if u.get("resupplying"):
        u["spent"] = 0
        u["resupplying"] = False
    if u.get("limbering"):
        u["limbered"] = not u.get("limbered")
        u["limbering"] = False
    if u["state"] in ("broken", "fled"):
        u["abandoned"] = True


GUN_EXAMPLES = (("canister at 200 m, a line", 20, 40, "smoothbore"), ("round shot at 400 m, a line", 40, 40, "smoothbore"),
                ("round shot at 400 m, a column", 40, 10, "smoothbore"), ("round shot at 800 m, a column", 80, 10, "smoothbore"),
                ("howitzers, shell at 400 m, a line", 40, 40, "howitzer"), ("howitzers, shell at 400 m, a column", 40, 10, "howitzer"),
                ("howitzers, shell at 800 m, a column", 80, 10, "howitzer"), ("rifled, canister at 200 m, a line", 20, 40, "rifled"),
                ("rifled, shell at 400 m, a column", 40, 10, "rifled"), ("rifled, shell at 800 m, a column", 80, 10, "rifled"),
                ("rifled, shell at 1,400 m, a column", 140, 10, "rifled"))


def gun_examples(d: Data, runs: int, seed: int) -> list[dict]:
    """A battery of 6 guns (60 regular crews; smoothbore, howitzers or rifled) firing for one
    minute at 1,600 unarmoured men in close order, as a line (40 hexes wide) or a column (10
    wide): men struck and men put down (means), on the Peninsular table."""
    table, out = "peninsular-1808-14-all-hits", []
    for label, dist, width, how in GUN_EXAMPLES:
        struck = down = 0
        for k in range(runs):
            bat = {**_example_unit(0, [30, 200], 1), "men": 60, "start": 60, "weapon": "artillery_smoothbore", "formation": "battery", "guns": how}
            tgt = {**_example_unit(1, [30, 200 - dist], 4), "men": 1600, "start": 1600, "width": width, "weapon": "musket_smoothbore", "kit": "none"}
            _, log = exchange(d, [bat, tgt], table, SeededDice(seed * 7907 + k), {"ground": {}, "works": None, "weather": None, "size": [60, 220]})
            for line in log:
                if line["kind"] == "cannon":
                    struck += line["blows"]
                    down += line["down"]
        out.append({"label": label, "struck": struck / runs, "down": down / runs})
    return out


MG_EXAMPLES = (   # (label, shooter weapon, shooters, shooter formation, distance in hexes, target formation, target width, prone)
    ("2 machine guns, 400 m, close order", "machine_gun", 10, "mg", 40, "close", 3, False),
    ("2 machine guns, 400 m, extended order", "machine_gun", 10, "mg", 40, "extended", 34, False),
    ("2 machine guns, 400 m, extended, to ground", "machine_gun", 10, "mg", 40, "extended", 34, True),
    ("2 machine guns, 800 m, extended order", "machine_gun", 10, "mg", 80, "extended", 34, False),
    ("100 riflemen, 400 m, close order", "rifle_service", 100, "extended", 40, "close", 3, False),
    ("100 riflemen, 400 m, extended order", "rifle_service", 100, "extended", 40, "extended", 34, False),
    ("100 riflemen, 400 m, extended, to ground", "rifle_service", 100, "extended", 40, "extended", 34, True),
)


def mg_examples(d: Data, runs: int, seed: int) -> list[dict]:
    """Machine guns and magazine rifles (regular, on the First World War table) firing for one
    minute at 100 regular unarmoured riflemen: men hit and put down (means)."""
    table, out = "wwi-1914-18-wounds", []
    for label, weapon, men, fm, dist, tfm, width, prone in MG_EXAMPLES:
        hit = down = 0
        for k in range(runs):
            sh = {**_example_unit(0, [60, 200], 1), "men": men, "start": men, "weapon": weapon, "formation": fm, "kit": "none",
                  "width": math.ceil(men / d.units["formations"][fm]["per_hex"])}
            tg = {**_example_unit(1, [60, 200 - dist], 4), "men": 100, "start": 100, "width": width, "weapon": "rifle_service", "formation": tfm,
                  "kit": "none", "prone": prone}
            _, log = exchange(d, [sh, tg], table, SeededDice(seed * 7919 + k), {"ground": {}, "works": None, "weather": None, "size": [120, 220]})
            for line in log:
                if line["kind"] == "volley" and line["att"] == 0:
                    hit += line["hits"]
                    down += line["down"]
        out.append({"label": label, "hit": hit / runs, "down": down / runs})
    return out


SHELL_EXAMPLES = (   # (label, kind, tubes, target formation, width, prone, ground under the target)
    ("2 mortars, close order", "mortar", 2, "close", 3, False, "open"),
    ("2 mortars, extended order", "mortar", 2, "extended", 34, False, "open"),
    ("4 field guns, close order", "field", 4, "close", 3, False, "open"),
    ("4 field guns, extended order", "field", 4, "extended", 34, False, "open"),
    ("4 field guns, extended, to ground", "field", 4, "extended", 34, True, "open"),
    ("4 field guns, extended, in woods", "field", 4, "extended", 34, False, "woods"),
    ("4 field guns, extended, to ground in woods", "field", 4, "extended", 34, True, "woods"),
    ("4 heavy howitzers, extended order", "howitzer", 4, "extended", 34, False, "open"),
)


def shell_examples(d: Data, runs: int, seed: int) -> list[dict]:
    """A battery's fire for one minute on the middle of 100 regular unarmoured riflemen (First
    World War table): men struck and put down, and how often the unit is pinned (means)."""
    table, out = "wwi-1914-18-wounds", []
    for label, kind, tubes, tfm, width, prone, ground in SHELL_EXAMPLES:
        struck = down = pinned = 0
        under = {} if ground == "open" else {f"{c},{r}": ground for c in range(20, 100) for r in range(90, 110)}
        for k in range(runs):
            tg = {**_example_unit(1, [60, 100], 4), "men": 100, "start": 100, "width": width, "weapon": "rifle_service", "formation": tfm,
                  "kit": "none", "prone": prone}
            field = {"ground": under, "works": None, "weather": None, "size": [120, 200],
                     "support": [{"name": "Battery", "side": 0, "kind": kind, "tubes": tubes, "rounds": 999, "mission": {"hex": [60, 100], "wait": 0}}]}
            us, log = exchange(d, [tg], table, SeededDice(seed * 7927 + k), field)
            for line in log:
                if line["kind"] == "shelled":
                    struck += line["struck"]
                    down += line["down"]
            pinned += 1 if us[0].get("pinned") else 0
        out.append({"label": label, "struck": struck / runs, "down": down / runs, "pinned": 100 * pinned / runs})
    return out
