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
import re
import random
from contextlib import contextmanager

from . import combat as C
from .combat import weapon_reach
from .disease import wound_case
from .combat import graze
from .engine import compose_wound, reduce_severity, roll_hit
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


def _wound(d: Data, att: dict, dfd: dict, margin: int, critical: bool, rng: random.Random, t: dict,
           attack_roll: int | None = None) -> None:
    """One blow that got through: roll it (armour read on the attack roll's units digit), then
    the stop check and death."""
    h = roll_hit(d, att["table"], att["weapon"], rng=rng, kit=dfd.get("kit"), margin=margin,
                 critical=critical, shield=dfd.get("shield"), attack_roll=attack_roll)
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
    if (d.units.get("quick") or {}).get("blows"):
        return _quick_blows(d, att, dfd, n, max(0, atk), dfn, rng, exposed, shift)
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
        _wound(d, att, dfd, atk - r, critical, rng, t, r)
    return t


# ---------- quick-play blows (units.yaml quick.blows): one roll for a striking group ----------
# The share of tries that end each way (missed, parried, stopped, a light, serious or critical wound,
# a man down or dead, and each kind of wound for the aftermath) is the per-blow rules' own, worked out
# once for each pairing from quick.samples tries on dice of its own (the stand-in for the printed
# table). A group's men down are then one d100 read on the binomial curve for its tries at that share
# (the per-blow dice's own spread); the dead and the lightly wounded among them are the averages,
# rounded at random (bookkeeping, not a table roll). As the field page's quickBlows.
_QUICK: dict = {}


def _num(x) -> str:
    """A number as the page writes it (40, not 40.0)."""
    return str(int(x)) if float(x).is_integer() else repr(float(x))


def _quick_rates(d: Data, att: dict, dfd: dict, atk, dfn) -> dict:
    """Per try: the share missed, parried, stopped, hit, light, serious, critical, down and dead, and
    of each kind of wound (hurt), from quick.samples tries on the pairing's own dice."""
    key = "|".join([att.get("table") or "", att.get("weapon") or "", dfd.get("kit") or "", dfd.get("quality") or "", _num(atk), _num(dfn)])
    if key in _QUICK:
        return _QUICK[key]
    h = 7
    for c in key:
        h = (h * 31 + ord(c)) % 2147483646
    own, S, t = SeededDice(1 + h), d.units["quick"]["samples"], _new_tally()
    crit_at = math.floor(atk * d.wounds["combat"]["critical_fraction"])
    for _ in range(S):
        r = own.randint(1, 100)
        if r > atk:
            t["missed"] += 1
            continue
        critical = r <= crit_at
        if not critical and dfn > 0 and own.randint(1, 100) <= dfn:
            t["parried"] += 1
            continue
        _wound(d, att, dfd, atk - r, critical, own, t, r)
    rates = {k: v / S for k, v in t.items() if k not in ("hurt", "blows")}
    rates["hurt"] = {k: v / S for k, v in t["hurt"].items()}
    _QUICK[key] = rates
    return rates


def _round(x: float) -> int:
    """Half up, as the page rounds."""
    return math.floor(x + 0.5)


def _random_round(x: float, rng) -> int:
    """Whole men, right on average: the fraction rounded up by chance."""
    return math.floor(x) + (1 if rng.random() < x - math.floor(x) else 0)


def _normal_at(p: float) -> float:
    """The standard normal curve's p point (Acklam's approximation)."""
    a = [-39.69683028665376, 220.9460984245205, -275.9285104469687, 138.357751867269, -30.66479806614716, 2.506628277459239]
    b = [-54.47609879822406, 161.5858368580409, -155.6989798598866, 66.80131188771972, -13.28068155288572]
    c = [-0.007784894002430293, -0.3223964580411365, -2.400758277161838, -2.549732539343734, 4.374664141464968, 2.938163982698783]
    e = [0.007784695709041462, 0.3224671290700398, 2.445134137142996, 3.754408661907416]

    def tail(x):
        q = math.sqrt(-2 * math.log(x))
        return (((((c[0] * q + c[1]) * q + c[2]) * q + c[3]) * q + c[4]) * q + c[5]) / ((((e[0] * q + e[1]) * q + e[2]) * q + e[3]) * q + 1)
    if p < 0.02425:
        return tail(p)
    if p > 1 - 0.02425:
        return -tail(1 - p)
    q = p - 0.5
    r = q * q
    return (((((a[0] * r + a[1]) * r + a[2]) * r + a[3]) * r + a[4]) * r + a[5]) * q / (((((b[0] * r + b[1]) * r + b[2]) * r + b[3]) * r + b[4]) * r + 1)


def _quick_down(d: Data, n: int, q: float, rng) -> int:
    """The men down of n tries that each put a man down at chance q: one d100 read on the binomial
    curve (its own percentiles for a small group, the normal curve's from quick.normal_from men's spread)."""
    if n <= 0 or q <= 0:
        return 0
    p = (rng.randint(1, 100) - 0.5) / 100
    mean = n * q
    v = mean * (1 - q)
    if v >= d.units["quick"]["normal_from"]:
        return min(n, max(0, _round(mean + _normal_at(p) * math.sqrt(v))))
    k, term = 0, (1 - q) ** n
    cum = term
    while cum < p and k < n:
        term *= (n - k) / (k + 1) * q / (1 - q)
        k += 1
        cum += term
    return k


def _shares(entries: list, total: int) -> dict:
    """total split over (key, weight) by largest remainder."""
    s, out = 0.0, {}
    for _, w in entries:                     # added in order, as the page does (Python's sum() compensates, which can split a tie the other way)
        s += w
    if total <= 0 or s <= 0:
        return out
    raw = [(k, total * w / s) for k, w in entries]
    left = total
    for k, x in raw:
        out[k] = math.floor(x)
        left -= out[k]
    for k, _ in sorted(((k, x - math.floor(x)) for k, x in raw), key=lambda kv: (-kv[1], kv[0]))[:left]:
        out[k] += 1
    return out


def _quick_blows(d: Data, att: dict, dfd: dict, n: int, atk, dfn, rng, exposed: tuple, shift: int) -> dict:
    """As _blows, but the rankers' blows in one roll; a blow that falls on a hero is still rolled."""
    t = _new_tally()
    crit_at = math.floor(atk * d.wounds["combat"]["critical_fraction"])
    t["blows"] = n
    tries = n
    if exposed:
        for _ in range(n):
            hero = _aimed_at(exposed, rng)
            if hero is not None:
                _hero_blow(d, att, hero, rng.randint(1, 100), atk, crit_at, shift, rng, t)
                tries -= 1
    if tries <= 0:                            # every blow fell on a hero, or none came
        return t
    R = _quick_rates(d, att, dfd, atk, dfn)
    mean = tries * R["down"]
    down = _quick_down(d, tries, R["down"], rng)
    k = down / mean if mean > 0 else 0
    for f in ("missed", "parried", "stopped"):
        t[f] = _round(tries * R[f])          # for the log only
    t["down"] = down
    t["dead"] = min(down, _random_round(tries * R["dead"] * k, rng))
    hurt_down = [(key, w) for key, w in R["hurt"].items() if key.endswith("|1")]
    hurt_up = [(key, w) for key, w in R["hurt"].items() if key.endswith("|0")]
    t["hurt"].update(_shares(hurt_down, down - t["dead"]))
    for key, w in hurt_up:
        m = _random_round(tries * w, rng)     # the lightly wounded who fight on: the average
        if m:
            t["hurt"][key] = m
    for key, m in t["hurt"].items():
        t[key.split("|")[0]] += m
    t["hits"] = t["light"] + t["serious"] + t["critical"] + t["dead"]
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
    h = roll_hit(d, att["table"], att["weapon"], rng=rng, kit=hero.get("kit"), margin=atk - r, critical=critical,
                 attack_roll=r)
    sev = h["severity"]
    fx = None if sev == "stopped" else compose_wound(d, h["location"], h["mechanism"], sev)   # the wound before any graze
    spent = 0
    while sev != "stopped" and fx["lethal"] in d.units["dead_if"] and hero.get("fate", 0) > 0:
        hero["fate"] -= 1                         # a player character's fate saves his life: the wound a step less
        spent += 1
        sev = reduce_severity(sev, 1)
        fx = None if sev == "stopped" else compose_wound(d, h["location"], h["mechanism"], sev)
    if sev == "stopped":
        if spent:
            t.setdefault("heroes", []).append({"hero": hero["id"], "name": hero["name"], "sev": sev, "loc": h["location"],
                                               "graze": False, "state": hero["state"], "fate_spent": spent})
        return
    if h["graze"]:
        fx = graze(fx)
    bleed, pain, shock = (fx["bleed"], fx["pain"], False) if h["graze"] else (fx["bleed"], fx["pain"], bool(fx.get("shock")))
    hero["wounds"].append({"loc": h["location"], "mech": h["mechanism"], "sev": sev, "graze": h["graze"], "bleed": bleed, "pain": pain, "impair": list(fx.get("impair") or [])})
    if fx["lethal"] in d.units["dead_if"]:
        hero["state"] = "dead"
    elif {"down", "incapacitated"} & set(hero_penalties(d, hero)[2]):
        hero["state"] = "down"                    # a wound that fells him or knocks him out (collapse, cannot stand, unconscious)
    else:
        nerve = _hero_nerve(hero, sev)            # a player character's lethality: more Nerve, or no check below critical
        if nerve is not None:
            _hero_check(d, hero, C.stop_check(d, nerve, sev, hero_pain(hero), rng.randint(1, 100) if _checks(d, sev, shock) else 0,
                                              hero_blood(d, hero)[0] / hero_blood(d, hero)[1], shock))
    t.setdefault("heroes", []).append({"hero": hero["id"], "name": hero["name"], "sev": sev, "loc": h["location"],
                                        "graze": h["graze"], "state": hero["state"], **({"fate_spent": spent} if spent else {})})


def _hero_nerve(hero: dict, sev: str) -> int | None:
    """A hero's Nerve for a stop check on a wound of this severity: a player character's
    lethality (stop_bonus, stop_crit_only, set by the field page from the GM's setting) adds to
    it, or spares him the check below critical (None). Others: his Nerve."""
    if hero.get("stop_crit_only") and sev != "critical":
        return None
    return hero["nerve"] + hero.get("stop_bonus", 0)


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


def _heroes_after(d: Data, us: list, rng, quiet: list | None = None, cautery: bool = False, closed: frozenset = frozenset()) -> list:
    """End of an exchange for every hero not dead, taken or carried off the map: a hold wears
    off; first aid if his unit had a quiet exchange (quiet[i]; cautery: the battle's era
    cauterises), or at the aid post every exchange; he bleeds (with his unit, lying out, on
    his way back or at the post), his Blood's thresholds can put him down, and pain above the
    cap calls for a stop check. Then bearers due back rejoin their units. closed: the sides whose
    aid post is moving this exchange (no first aid there)."""
    log = []
    for i, u in enumerate(us):
        for hero in u.get("heroes", []):
            if hero["state"] in ("dead", "prisoner") or (hero.get("carried") and not hero.get("post")):   # off the map: out of the battle
                continue
            log += _hero_end(d, (i, u, hero), rng, (quiet and quiet[i], cautery, closed))
    return log + _bearers_back(us)


def _hero_end(d: Data, iuh: tuple, rng, how: tuple) -> list:
    """One hero's end of the exchange (_heroes_after): first aid (none at a post that is
    moving), then bleeding. how: (quiet, cautery, closed sides). -> log lines."""
    (i, u, hero), (quiet, cautery, closed), out = iuh, how, []
    aid = None if hero.get("post") and u["side"] in closed else _aid_for(d, u, hero, rng, (quiet, cautery))
    if aid:
        out.append({"kind": "heroaid", "unit": i, **aid})
    line = _hero_after(d, hero, rng)
    if line:
        out.append({"kind": "herobled", "unit": i, **line})
    return out


def _aid_for(d: Data, u: dict, hero: dict, rng, when: tuple) -> dict | None:
    """First aid this exchange: at the aid post, always, at heroes.aid_post.first_aid; with his
    unit, in a quiet exchange, by its best healer. when: (quiet, cautery)."""
    quiet, cautery = when
    if hero.get("post"):
        return _first_aid(d, hero, rng, (d.units["heroes"]["aid_post"]["first_aid"], "the aid post"), cautery)
    if quiet and not _off_field(hero):
        return _first_aid(d, hero, rng, _healer(d, u), cautery)
    return None


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
    out, chance = [], quarter(d, table)
    up = {u["side"] for u in units if standing(u)}
    for i, u in enumerate(units):
        for h in (h for h in u.get("heroes", []) if _lying_out(u, h)):
            line = {"unit": i, "hero": h["id"], "name": h["name"]}
            if u["side"] in up or not up:
                out.append({**line, "fate": "found"})
                continue
            roll = rng.randint(1, 100)
            fate = "prisoner" if roll <= chance else "killed"
            if fate == "killed" and h.get("fate", 0) > 0:
                h["fate"] -= 1                    # a player character's fate spares his life: taken instead
                fate, line["fate_spent"] = "prisoner", True
            out.append({**line, "fate": fate, "roll": roll, "chance": chance})
    return out


def quarter(d: Data, table: str) -> int:
    """% that a man the enemy finds lying out is taken prisoner (heroes.quarter, by the wound
    table's war), else killed."""
    Q = d.units["heroes"]["quarter"]
    return Q.get((d.tables.get(table) or {}).get("battle"), Q["default"])


def _lying_out(u: dict, h: dict) -> bool:
    """A hero still on the field who cannot leave it with his unit: left behind, on his way
    back, or down with a unit that is no longer standing (not dead, taken or carried back)."""
    if h["state"] in ("dead", "prisoner") or h.get("carried"):
        return False
    return bool(h.get("left") or h.get("going")) or (not standing(u) and h["state"] == "down")


def _off_field(hero: dict) -> bool:
    """Left behind, on his way back, or carried to the rear or the aid post: out of his
    unit's fight."""
    return bool(hero.get("left") or hero.get("carried") or hero.get("going"))


def _parties_after(d: Data, us: list, field: dict | None) -> list:
    """Each party on its way back goes on along the cheapest way to its side's aid post (or,
    with none or no way there, to the map edge the way back; party_way), and arrives if it gets
    there: the hero is carried (safe; at the post, its care), and the bearers set off back to
    their unit, due after as many exchanges as the carry took. A hero who cannot walk with no
    bearers left lies where he is; one killed on the way leaves his bearers to go back."""
    log = []
    for i, u in enumerate(us):
        for hero in u.get("heroes", []):
            g = hero.get("going")
            if not g:
                continue
            line = _party_stops(d, u, hero) or _party_moves(d, us, field, i, hero)
            if line:
                log.append({"kind": "party", "unit": i, "hero": hero["id"], "name": hero["name"], **line})
    return log


def _party_stops(d: Data, u: dict, hero: dict) -> dict | None:
    """A party that cannot go on: its hero killed or taken (the bearers go back), or unable to
    walk with no bearers (he lies where he is). -> a log line, or None."""
    g = hero["going"]
    if hero["state"] in ("dead", "prisoner"):
        del hero["going"]
        _bearers_off(u, g)
        return {"what": "stopped", "at": g["pos"]}
    if g["bearers"] <= 0 and _lame(d, hero):
        del hero["going"]
        hero["left"], hero["at"] = True, g["pos"]
        return {"what": "lies", "at": g["pos"]}
    return None


def _party_moves(d: Data, us: list, field: dict | None, i: int, hero: dict) -> dict | None:
    """The party goes on toward its aim (the post, or the edge), heroes.aid_post.pace movement an
    exchange along the cheapest way (party_way); arriving, the hero is carried. With no way to
    the post it makes for the map edge instead (logged once)."""
    u, g = us[i], hero["going"]
    post = aid_post(field, u["side"])
    g["ex"] += 1
    way, note = party_way(d, us, field, i, (g, post))
    if way is None:
        return note
    g["pos"], arrived = way
    if not arrived:
        return note
    del hero["going"]
    hero["carried"] = True
    if post and not g.get("no_way"):
        hero["post"] = True
    _bearers_off(u, g)
    return {"what": "edge" if g.get("no_way") or not post else "post", "at": list(g["pos"])}


def party_way(d: Data, us: list, field: dict | None, i: int, gp: tuple) -> tuple:
    """((where the party gets to this exchange, arrived?), a log line or None), or (None, line)
    if no way leads anywhere: to the post if a way leads there, else to the map edge the way
    back (else any edge), by the cheapest way over the ground and works, through its own side's
    units and round the enemy's (_ways_to). It spends heroes.aid_post.pace movement as a unit
    would (at least a step an exchange)."""
    (g, post), u = gp, us[i]
    size, pos = _size(d, field), tuple(g["pos"])
    blocked = {k for j, e in enumerate(us) if e["side"] != u["side"] and e["men"] > 0 for k in _hexes_of(d, e)} - {pos}
    walker, note = {"side": u["side"], "mounted": False}, None
    ways = _ways_to(d, field, walker, [tuple(post["at"])], (blocked, size)) if post and not g.get("no_way") else {}
    aim = post["at"] if pos in ways else None
    if post and pos not in ways and not g.get("no_way"):
        g["no_way"], note = True, {"what": "no_way", "at": list(post["at"])}
    if pos not in ways:
        aim = _edge(d, field, list(pos), g["dir"])
        ways = _ways_to(d, field, walker, [tuple(aim)], (blocked, size))
    if pos not in ways:
        ways = _ways_to(d, field, walker, _border(size), (blocked, size))
    if pos not in ways:
        return None, note
    return _go_along(d, field, walker, (pos, aim), (ways, blocked, size)), note


def _hexes_of(d: Data, u: dict) -> list:
    """The hexes unit u stands on, as 'c,r' keys turned to tuples."""
    return [tuple(x) for row in footprint(d, u) for x in row]


def _border(size: tuple) -> list:
    """Every hex on the map's edge, in column then row order."""
    cols, rows = size
    return sorted({(c, r) for c in range(cols) for r in range(rows) if c in (0, cols - 1) or r in (0, rows - 1)})


def _ways_to(d: Data, field: dict | None, walker: dict, aims: list, bs: tuple) -> dict:
    """{hex: the least movement from it to the nearest of aims} over the ground and works
    (step_cost), not through blocked hexes: a search out from the aims, a cost at a time."""
    best = {a: 0 for a in aims if a not in bs[0]}
    todo, k = {0: sorted(best)}, 0
    while todo:
        for y in todo.pop(k, []):
            if best[y] == k:
                _relax_into(d, field, walker, (y, k), (best, todo, bs))
        k += 1
    return best


def _relax_into(d: Data, field: dict | None, walker: dict, yk: tuple, ctx: tuple) -> None:
    """Each neighbour x of y (at least movement k from the aims) that steps into y more cheaply
    than found so far gets its new least movement, and waits its turn in todo."""
    (y, k), (best, todo, (blocked, size)) = yk, ctx
    for dirn in range(6):
        x = tuple(step(list(y), dirn))
        if not (0 <= x[0] < size[0] and 0 <= x[1] < size[1]) or x in blocked:
            continue
        c = step_cost(d, field, walker, list(x), list(y))
        if c is not None and k + c < best.get(x, 10**9):
            best[x] = k + c
            todo.setdefault(k + c, []).append(x)


def _go_along(d: Data, field: dict | None, walker: dict, pa: tuple, wbs: tuple) -> tuple:
    """(where it gets, arrived?): from pos, step after step down the ways (to a neighbour whose
    step and way left add up to the way from here: the nearest the straight line toward aim,
    the first by direction of equals), while the pace lasts, at least a step."""
    (pos, aim), (ways, blocked, _) = pa, wbs
    line = ray(list(pos), list(aim), hdist(pos, aim))
    left, moved = d.units["heroes"]["aid_post"]["pace"], False
    while ways[pos] > 0:
        nxt = _next_down(d, field, walker, pos, (ways, blocked, line))
        if nxt is None or (moved and nxt[1] > left):
            break
        pos, left, moved = nxt[0], left - nxt[1], True
    return list(pos), ways[pos] == 0


def _next_down(d: Data, field: dict | None, walker: dict, pos: tuple, wbl: tuple) -> tuple | None:
    """(hex, cost) of the step down the ways from pos nearest the line (first by direction of equals)."""
    (ways, blocked, line), best = wbl, None
    for dirn in range(6):
        x = tuple(step(list(pos), dirn))
        if x not in ways or x in blocked:
            continue
        c = step_cost(d, field, walker, list(pos), list(x))
        if c is None or c + ways[x] != ways[pos]:
            continue
        off = min(hdist(x, y) for y in line)
        if best is None or off < best[0]:
            best = (off, x, c)
    return best and best[1:]


def _bearers_off(u: dict, g: dict) -> None:
    """A party's bearers set off back to their unit: due after as many exchanges as it went."""
    if g["bearers"] > 0:
        u["away"] = [*u.get("away", []), {"men": g["bearers"], "left": max(1, g["ex"])}]


def _edge(d: Data, field: dict | None, h, dirn: int) -> list:
    """The last hex on the map going from h in direction dirn."""
    cols, rows = _size(d, field)
    while True:
        x = step(h, dirn)
        if not (0 <= x[0] < cols and 0 <= x[1] < rows):
            return list(h)
        h = x


def _lying_after(d: Data, us: list, table: str, rng) -> list:
    """Heroes lying out (left behind, on a hex): a unit of his side standing on his hex picks
    him up (he goes with it, behind), but not the unit that left him until it has moved off;
    an enemy unit, not broken, standing there takes him prisoner at the war's quarter %, else
    kills him."""
    log, occ = [], occupancy(d, us)
    for i, u in enumerate(us):
        for hero in [h for h in u.get("heroes", []) if h.get("left") and h.get("at") and h["state"] not in ("dead", "prisoner")]:
            line = _lying_one(d, us, (i, occ.get(C.hkey(hero["at"]))), hero, (table, rng))
            if line:
                log.append(line)
    return log


def _lying_one(d: Data, us: list, ij: tuple, hero: dict, tr: tuple) -> dict | None:
    """One hero lying out of unit i, with unit j (or None) on his hex: fetched, found, or left."""
    (i, j), u = ij, us[ij[0]]
    if hero.get("left_by") is not None and (j is None or us[j]["id"] != hero["left_by"]):
        del hero["left_by"]                       # the unit that left him has moved off: it may come back for him
    if j is None or _out(us[j]) or us[j].get("vehicle") or hero.get("left_by") is not None:
        return None
    if us[j]["side"] != u["side"]:
        return {"kind": "found", "unit": i, "by": j, **_taken(d, hero, *tr)}
    u["heroes"].remove(hero)
    hero.pop("left"), hero.pop("at")
    us[j]["heroes"] = [*us[j].get("heroes", []), {**hero, "role": "behind"}]
    return {"kind": "fetched", "unit": j, "from": i, "hero": hero["id"], "name": hero["name"]}


def _taken(d: Data, hero: dict, table: str, rng) -> dict:
    """The enemy finds him: d100 at or under the war's quarter % takes him prisoner, else he is killed."""
    roll, chance = rng.randint(1, 100), quarter(d, table)
    fate, spared = ("prisoner" if roll <= chance else "killed"), False
    if fate == "killed" and hero.get("fate", 0) > 0:
        hero["fate"] -= 1                         # a player character's fate spares his life: taken instead
        fate, spared = "prisoner", True
    hero["state"] = "prisoner" if fate == "prisoner" else "dead"
    hero.pop("post", None)
    return {"hero": hero["id"], "name": hero["name"], "fate": fate, "roll": roll, "chance": chance, **({"fate_spent": True} if spared else {})}


def _posts_after(d: Data, us: list, field: dict | None, table: str, rng) -> list:
    """An aid post with an enemy unit (not broken or fled, with men) within
    heroes.aid_post.overrun hexes is overrun: the heroes there are taken or killed (_taken)."""
    log, reach = [], d.units["heroes"]["aid_post"]["overrun"]
    for p in (field or {}).get("posts") or []:
        if p.get("overrun") or not any(u["side"] != p["side"] and not _out(u) and any(hdist(x, p["at"]) <= reach for row in footprint(d, u) for x in row) for u in us):
            continue
        p["overrun"] = True
        log.append({"kind": "overrun_post", "side": p["side"], "at": p["at"]})
        for i, u in enumerate(us):
            log += [{"kind": "found", "unit": i, "at_post": True, **_taken(d, h, table, rng)}
                    for h in u.get("heroes", []) if h.get("post") and u["side"] == p["side"] and h["state"] not in ("dead", "prisoner")]
    return log


def _shell_parties(d: Data, us: list, field: dict, bursts: list, kind: dict, att: dict, rng) -> list:
    """Shell bursts near parties on their way back: the hero and each bearer struck at the %
    for his distance (as men in the open, less the ground's cover). Struck bearers roll their
    wounds as the unit's men (put down: lost to it); the hero, in full."""
    log = []
    for i, u in enumerate(us):
        for hero in u.get("heroes", []):
            if hero.get("going") and hero["state"] not in ("dead", "prisoner"):
                line = _shell_party(d, field, u, hero, (bursts, kind, att), rng)
                if line:
                    log.append({"kind": "partyhit", "unit": i, **line})
    return log


def _shell_party(d: Data, field: dict, u: dict, hero: dict, fire: tuple, rng) -> dict | None:
    (bursts, kind, att), g = fire, hero["going"]
    cut, hits, struck = _shell_cut(d, field, g["pos"], False), 0, 0
    for at in bursts:
        dist = hdist(g["pos"], at)
        if dist > kind["radius"]:
            continue
        p = kind["struck"][dist] * cut
        hits += rng.randint(1, 100) <= p
        struck += sum(1 for _ in range(g["bearers"]) if rng.randint(1, 100) <= p)
    if not hits and not struck:
        return None
    atk = d.units["indirect"]["attack"]
    t = _blows(d, att, _side(u, att["table"]), struck, atk, 0, rng)
    th = _new_tally()
    crit_at = math.floor(atk * d.wounds["combat"]["critical_fraction"])
    for _ in range(hits):
        if hero["state"] != "dead":
            _hero_blow(d, att, hero, rng.randint(1, 100), atk, crit_at, -1000, rng, th)
    g["bearers"] -= t["down"]
    u.update(down=u.get("down", 0) + t["down"], dead=u.get("dead", 0) + t["dead"])
    _take_hurt(u, t)
    return {"hero": hero["id"], "name": hero["name"], "at": g["pos"], "struck": struck, "down": t["down"], "dead": t["dead"],
            "hits": th.get("heroes", []), "state": hero["state"]}


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


def carry_back(d: Data, units: list, i: int, hero_id, field: dict | None = None) -> str | None:
    """Unit i sends `bearers` of its men to carry hero hero_id back. With an aid post for its
    side (field.posts), they set off for it as a party on the map (_parties_after); with none,
    he leaves the battle at once (safe) and they come back after `back_after` exchanges.
    -> None, or why not."""
    H, u = d.units["heroes"], units[i]
    hero = _hero_of(u, hero_id)
    if hero is None or not lamed(d, hero):
        return "he can walk, or is not with the unit"
    if u["state"] not in ("steady", "shaken"):
        return "the unit is running"
    if u["men"] <= H["bearers"]:
        return f"the unit has not {H['bearers']} men to spare"
    u["men"] -= H["bearers"]
    if aid_post(field, u["side"]):
        hero["going"] = _party(u, H["bearers"])
        return None
    hero["carried"] = True
    u["away"] = [*u.get("away", []), {"men": H["bearers"], "left": H["back_after"]}]
    return None


def walk_back(d: Data, units: list, i: int, hero_id) -> str | None:
    """Hero hero_id, wounded but able to walk (up, not lamed), leaves unit i and goes back
    alone: to his side's aid post, or the map edge behind his unit. -> None, or why not."""
    u = units[i]
    hero = _hero_of(u, hero_id)
    if hero is None or hero["state"] != "up" or _off_field(hero):
        return "he is not up with the unit"
    if lamed(d, hero):
        return "he cannot walk: carry him back"
    if not hero.get("wounds") and not hero.get("old"):
        return "he is not wounded"
    hero["going"] = _party(u, 0)
    return None


def leave(d: Data, units: list, i: int, hero_id) -> str | None:
    """Unit i leaves lamed or down hero hero_id behind: he lies on its hex (left, at), where a
    unit can fetch him (_lying_after), it too once it has moved off. -> None, or why not."""
    u = units[i]
    hero = _hero_of(u, hero_id)
    if hero is None or not lamed(d, hero):
        return "he can walk, or is not with the unit"
    hero.update(left=True, at=list(u["pos"]), left_by=u["id"])
    return None


def _hero_of(u: dict, hero_id) -> dict | None:
    return next((h for h in u.get("heroes", []) if h["id"] == hero_id), None)


def _party(u: dict, bearers: int) -> dict:
    """A party setting off back from unit u: where it is, its bearers, the way back (away
    from the unit's front) and the exchanges it has been going."""
    return {"pos": list(u["pos"]), "bearers": bearers, "dir": (u["facing"] + 3) % 6, "ex": 0}


def posts_moving(field: dict | None) -> frozenset:
    """The sides whose aid post is moving this exchange (moving: exchanges left): closed, it gives no first aid."""
    return frozenset(p["side"] for p in (field or {}).get("posts") or [] if p.get("moving"))


def _posts_settle(field: dict | None) -> None:
    """After the exchange, a moving aid post counts down; at 0 it is open again."""
    for p in (field or {}).get("posts") or []:
        if p.get("moving"):
            p["moving"] -= 1
            if p["moving"] <= 0:
                del p["moving"]


def aid_post(field: dict | None, side) -> dict | None:
    """Side's aid post on the field (field.posts: [{side, at, overrun}]) if not overrun, or None."""
    return next((p for p in (field or {}).get("posts") or [] if p["side"] == side and not p.get("overrun")), None)


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
    how = _treat(d, hero, w, healer, cautery)
    w["aid"] = how                            # the roller marks it treated (on the field) when he goes back
    if any(w is o for o in hero.get("old") or []):
        T = d.wounds["tracking"]
        hero["old_bleed"] = sum(round(T["bleed_per_round"][o.get("bleed", 0)] * d.units["exchange_rounds"]) for o in hero["old"])
    return {**line, "stopped": True, "bleed": w["bleed"], "how": how}


def _treat(d: Data, hero: dict, w: dict, healer: tuple | None, cautery: bool) -> str:
    """A successful first aid on wound w: tourniquet a limb, cauterise the body (cautery), or
    bind. -> how."""
    H = d.units["heroes"]
    limb = (d.loc.get(w["loc"]) or {}).get("zone") in ("arms", "legs")
    if limb and w["bleed"] >= H["tourniquet_from"]:
        w["bleed"] = 0
        return "tourniquet"
    if cautery and not limb and w["bleed"] >= H["cautery"]["from_bleed"]:
        w["bleed"] = 0
        if not healer:
            w["pain"] = min(d.wounds["tracking"]["pain_cap"], w.get("pain", 0) + H["cautery"]["pain"])
            _sum_old_pain(hero, w)
        return "cauterise"
    w["bleed"] = max(0, w["bleed"] - (d.wounds["combat"]["first_aid"]["bind"] if healer else 1))
    return "bind"


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
    nerve = _hero_nerve(hero, d.wounds["combat"]["stop_check"]["pain_round_as"])
    if hero["state"] == "up" and hero_pain(hero) > T["pain_cap"] and nerve is not None:
        _hero_check(d, hero, C.pain_check(d, nerve, hero_pain(hero), rng.randint(1, 100), hero["blood"] / pool))
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
    """A hero who slows his unit: not dead or off the field, and cannot walk (_lame)."""
    if hero["state"] == "dead" or _off_field(hero):
        return False
    return _lame(d, hero)


def _lame(d: Data, hero: dict) -> bool:
    """Down, or with a wound (from this battle or one he came with) that lames him
    (heroes.lamed): he cannot walk."""
    lame = d.units["heroes"]["lamed"]
    return hero["state"] != "up" or any(i in lame for w in (hero.get("old") or []) + hero.get("wounds", []) for i in w.get("impair") or [])


def front_men(d: Data, u: dict) -> int:
    """Men in the unit's front rank: the ones a blow on its front falls among."""
    rows, men = footprint(d, u), men_by_hex(d, u)
    return sum(min(form(d, u)["abreast"], men[k]) for k in range(len(rows[0]))) if rows else 0


def _exposure(d: Data, u: dict, rout: bool, missile: bool = False) -> tuple:
    """(hero, chance) for each hero of unit u a blow on it may fall on."""
    H = d.units["heroes"]
    mark = lambda h: H.get("officer_exposure", 1) if h.get("officer") else 1   # an officer draws fire
    if rout or missile:
        return tuple((h, min(1, mark(h) / max(1, u["men"]))) for h in _heroes(u, ("front", "ranged", "behind" if rout else "")))
    return tuple((h, min(1, mark(h) * H["exposure"] / max(1, front_men(d, u)))) for h in _heroes(u, ("front", "ranged")))


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
    beside it), contact, holds (holding a position), hand_lost and hand_dealt (hand to hand
    this exchange)}. Returns {check (bool),
    target, state}."""
    M = d.units["morale"]
    if unit["state"] == "broken":
        return {"check": False, "target": None, "state": "broken"}
    if M.get("posture_flank") and unit.get("holds"):
        unit = {**unit, "flanked": False}   # holding a position, its men face every way (morale.posture_flank)
    struck = _attrition(M, unit) or unit["lost"] >= M["shock"] * max(1, unit["men"]) or unit.get("flanked") or _losing(M, unit)
    rally = unit["state"] == "shaken" and not unit.get("contact")
    if not struck and not rally:
        return {"check": False, "target": None, "state": unit["state"]}
    target = quality(d, unit["quality"])["nerve"] + _morale_mods(M["mods"], unit)
    if roll <= target:
        return {"check": True, "target": target, "state": "steady" if rally and not struck else unit["state"]}
    return {"check": True, "target": target, "state": _failed(M, unit, roll - target, rally and not struck)}


def _holding(unit: dict) -> bool:
    """Holding a position (morale.posture) and not struck in flank or rear."""
    return bool(unit.get("holds")) and not unit.get("flanked")


def _losing(mo: dict, unit: dict) -> bool:
    """Lost the exchange in contact: more men down than it put down; holding a position
    (morale.posture_hand), only by its losses hand to hand."""
    if not unit.get("contact"):
        return False
    if mo.get("posture_hand") and _holding(unit):
        return unit.get("hand_lost", 0) > unit.get("hand_dealt", 0)
    return unit.get("lost", 0) > unit.get("dealt", 0)


def _attrition(mo: dict, unit: dict) -> bool:
    """A quarter down (morale.trigger): every exchange in the open; holding a position, only in an
    exchange it lost men."""
    return unit["down"] >= mo["trigger"] * unit["start"] and (unit["lost"] > 0 or not _holding(unit))


def _failed(mo: dict, unit: dict, by: int, rallying: bool = False) -> str:
    """A failed check: a steady unit is shaken, unless it fails badly while flanked or with
    half its men down; a shaken unit breaks, unless it was only trying to rally (rallying):
    then it stays shaken."""
    if unit["state"] == "shaken":
        return "shaken" if rallying else "broken"
    hard = unit.get("flanked") or unit["down"] >= unit["start"] / 2
    return "broken" if hard and by > mo["shaken_by"] else "shaken"


def _morale_mods(mods: dict, unit: dict) -> int:
    m = 0
    if unit.get("leader") == "up":
        m += mods["leader"] + max([h.get("rank_bonus", 0) for h in unit.get("heroes", []) if h.get("leader") and h.get("state") == "up"] or [0])
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
    if unit.get("no_ammo"):
        m += mods.get("no_ammo", 0)
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


def unit_gap(d: Data, a: dict, b: dict) -> int:
    """Hexes between the nearest hexes of two units (1: side by side)."""
    hb = [h for row in footprint(d, b) for h in row]
    return min((hdist(h, x) for row in footprint(d, a) for h in row for x in hb), default=10**9)


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
    return d.units["vehicles"]["armour"][u.get("armour") or K["armour"]] if K else None   # its own (a battlefield's armour), else its kind's


def hurts_armour(d: Data, weapon: str) -> bool:
    """Whether a man's weapon can knock out a vehicle (vehicles.anti_armour)."""
    return weapon in ((d.units.get("vehicles") or {}).get("anti_armour") or {})


def soft(d: Data, u: dict) -> bool:
    """A soft-skinned vehicle unit (its armour has a `small` %): small arms can hurt it."""
    return "small" in (armour_of(d, u) or {})


def _shot_at_vehicle(d: Data, weapon: str) -> dict:
    """How a man's weapon is fired at a vehicle: its anti_armour line, else small arms
    (vehicles.small_arms rate, machine guns `mg`) on the armour's `small` row."""
    V = d.units["vehicles"]
    if weapon in V.get("anti_armour", {}):
        return V["anti_armour"][weapon]
    S = V["small_arms"]
    return {"rate": S["mg"] if weapon in d.units["machine_guns"]["weapons"] else S["rate"], "row": "small"}


def bearing(t, h) -> int:
    """The direction (0-5, as step) from hex t that points most nearly at hex h (the first of equals)."""
    a, b = _cube(t), _cube(h)
    v = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
    dots = [v[0] * q + v[1] * r + v[2] * (-q - r) for q, r in AX]
    return dots.index(max(dots))


def kill_chance(d: Data, u: dict, row: str, h, t) -> int:
    """% that a hit from hex h on vehicle unit u (at its hex t) knocks a vehicle out: its armour's
    `row` %, times vehicles.aspect for a flank or rear shot (by u's facing), to 100 at most."""
    A = armour_of(d, u)
    side = arc(u["facing"], bearing(t, h)) if h is not None and t is not None and list(h) != list(t) else "front"
    if side == "front" and row in (A.get("front") or {}):
        return A["front"][row]                    # composite armour: proof from the front
    return min(100, int(A[row] * (d.units["vehicles"].get("aspect") or {}).get(side, 1)))


def _harm(d: Data, u: dict, n: int, lost: int, rng) -> dict:
    """n hits on vehicle unit u that did not knock one out: each is on the turret at
    vehicles.damage.turret %, else the hull, and may immobilise a vehicle or put its main gun out
    by that part's line, up to the vehicles it has left. -> {immobilised, gun, turret}."""
    D, left, out = d.units["vehicles"]["damage"], vehicles_left(d, u, lost), {"immobilised": 0, "gun": 0, "turret": 0}
    for _ in range(n):
        turret = rng.randint(1, 100) <= D["turret"]
        P = D["turret_hit" if turret else "hull_hit"]
        out["turret"] += turret
        r = rng.randint(1, 100)
        if r <= P["immobilised"]:
            out["immobilised"] += 1
        elif r <= P["immobilised"] + P["gun"]:
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


def cornered(d: Data, units: list, i: int, after: dict) -> bool:
    """Broken unit i cannot run (after its flee it would stand where it is) with an enemy touching
    it, and its side gives up (rout.surrender; not fights_on)."""
    u = units[i]
    if not d.units["rout"].get("surrender") or u.get("fights_on") or after["state"] == "fled" or list(after["pos"]) != list(u["pos"]):
        return False
    return in_contact(d, units, occupancy(d, units), i)


def surrender(u: dict, quarter_pct: int) -> dict:
    """A cornered unit gives up: quarter % of its men standing taken prisoner, the rest killed;
    its heroes on their feet taken. -> {unit, taken, killed}"""
    taken = u["men"] * quarter_pct // 100
    killed = u["men"] - taken
    heroes = [{**h, "state": "prisoner"} if h.get("state") == "up" and not _off_field(h) else h for h in u.get("heroes") or []]
    unit = {**u, "state": "fled", "men": 0, "down": u.get("down", 0) + u["men"], "dead": u.get("dead", 0) + killed,
            "taken": u.get("taken", 0) + taken, "surrendered": True, "heroes": heroes}
    return {"unit": unit, "taken": taken, "killed": killed}


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
        pen, stk, n = _hex_blows(d, field, (u, units[j]), (h, x, reach), (men[k], per, abreast, k in busy))
        if n > 0:
            key = (i, j, arc(units[j]["facing"], dirn + 3), pen, stk)
            groups[key] = groups.get(key, 0) + n


def _hex_blows(d: Data, field: dict | None, pair: tuple, where: tuple, ranks: tuple) -> tuple:
    """(penalty %, stakes, strikers) for one front hex of unit u at its enemy across the side
    from h to x: across a work that blocks hand to hand, men with ladders fight from them (at
    escalade.penalty), and the defenders' front rank strikes back at the men on the ladders."""
    (u, e), (h, x, reach), (men, per, abreast, busy) = pair, where, ranks
    E = d.units["escalade"]
    blocked, pen, stk = _across(d, field, u, h, x, reach)
    climbing = blocked and reach < 2 and has_ladders(u)
    defends = blocked and reach < 2 and not climbing and has_ladders(e)
    n = _hex_strikers(men, abreast if defends else per, abreast, reach if blocked and not defends else 0, busy, E["share"] if climbing else 0)
    return pen + (E["penalty"] if climbing else 0), stk, n


def _hex_strikers(men: int, per: int, abreast: int, blocked_reach: int, busy: bool, climb: float = 0) -> int:
    """Men of one front hex who strike: per; across a wall (blocked_reach: the weapon's reach,
    else 0) only the front rank of reach-2 weapons, or with ladders (climb: escalade.share) that
    share of the front rank (at least one); less the front rank if it is breaching."""
    n = min(per, men)
    if blocked_reach:
        if blocked_reach >= 2:
            n = min(abreast, men)
        else:
            n = max(1, math.floor(min(abreast, men) * climb)) if climb and men > 0 else 0
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
    ground keys), its works laid on the hexes and hex sides, its weather and size, its landing
    zones, supply dumps (each with its side's name, as the battle's units have), fire support and
    objective (the hex the battle was fought for) if any, and its year (`year`, else the year in
    its id: the napalm limit)."""
    f, keys = d.fields[fid], {g["key"]: k for k, g in d.units["ground"].items()}
    ground = {f"{c},{r}": keys[ch] for r, row in enumerate(f["rows"]) for c, ch in enumerate(row.strip()) if keys[ch] != "open"}
    works = _field_works(d, f.get("works") or {})
    wx = f.get("weather") or {"cond": "fair", "wind": "calm", "ground": {"mud": 0, "snow": 0}}
    out = {"ground": ground, "works": works, "weather": wx, "size": list(f["size"]), "up": f.get("up", "N")}
    year = f.get("year") or next((int(y) for y in re.findall(r"(?<!\d)(1\d{3}|20\d{2})(?!\d)", fid)), None)
    if year:
        out["year"] = year
    if f.get("lz"):
        out["lz"] = [list(h) for h in f["lz"]]
    if f.get("dumps"):
        out["dumps"] = [{"at": list(m["at"]), "side": f["sides"][m["side"]]} for m in f["dumps"]]
    if f.get("objective"):
        out["objective"] = list(f["objective"]["at"])
        if f["objective"].get("radius"):
            out["objective_radius"] = f["objective"]["radius"]
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
             "rounds": s["tubes"] * K[s["kind"]]["rounds"], "mission": None, **({"place": list(s["place"])} if s.get("place") else {}), **({"df": True} if s.get("df") else {})} for s in f["support"]]


def fire_control_of(d: Data, o: dict, table: str) -> str | None:
    """A tank unit's fire control (vehicles.fire_control): the battlefield's (fc), else its
    war's by the wound table's battle; None for a vehicle kind without one, or no vehicle."""
    kind = d.units["vehicles"]["kinds"].get(o.get("vehicle") or "") or {}
    if not kind.get("fc"):
        return None
    return o.get("fc") or d.units["vehicles"]["fire_control"]["by_war"].get((d.tables.get(table) or {}).get("battle"))


def vehicle_device(d: Data, table: str) -> str | None:
    """The night-vision device a vehicle unit carries by default in the war of this wound table
    (weather.yaml light.night_vision.vehicles), or None."""
    war = (d.tables.get(table) or {}).get("battle")
    return (((d.weather or {}).get("light") or {}).get("night_vision") or {}).get("vehicles", {}).get(war)


def battlefield_units(d: Data, fid: str) -> list:
    """The armies as drawn up on a battlefield, as units ready to fight (not those that come
    in by air: `lands`); vehicle units with no night device get their war's (vehicle_device)."""
    out, dev = [], vehicle_device(d, d.fields[fid]["table"])
    for u in (x for x in d.fields[fid].get("units", []) if "lands" not in x):
        out.append({**u, "start": u["men"], "down": 0, "dead": 0, "hurt": {}, "heroes": [], "state": "steady",
                    "mounted": bool(u.get("mounted")), "charged": False, "leader": None,
                    **({"nv": dev} if u.get("vehicle") and not u.get("nv") and dev else {})})
    return out


def ground_at(d: Data, field: dict | None, h) -> dict:
    """The ground kind's spec at hex h (open if unpainted), remembered for the field's ground (_ground_memo)."""
    at = _ground_memo(d, field)["at"]
    key = (h[0], h[1])
    g = at.get(key)
    if g is None:
        g = at[key] = d.units["ground"][((field or {}).get("ground") or {}).get(f"{h[0]},{h[1]}", "open")]
    return g


_GROUND_MEMO = {}   # id(field ground) -> (that ground, its size, the data, {"at": hex -> ground spec, "lines": (h, t) -> sight line})
_NO_GROUND = {}


def _ground_memo(d: Data, field: dict | None) -> dict:
    """What stands on each hex and what each sight line crosses, worked out once for a field's
    ground: the rules never repaint a field during a battle (as the page's groundMemo)."""
    g = (field or {}).get("ground") or _NO_GROUND
    hit = _GROUND_MEMO.get(id(g))
    if hit is None or hit[0] is not g or hit[1] != len(g) or hit[2] is not d:
        hit = (g, len(g), d, {"at": {}, "lines": {}})
        _GROUND_MEMO[id(g)] = hit
    return hit[3]


def _sight_line(d: Data, field: dict | None, h, t, dist: int) -> int:
    """The ground's part of a sight line from h to t (dist apart), worked out once, packed in a
    number: dead ground between (_crest_on) 1, a clear sight to aim (_sight_on) 2, the hexes of
    light cover between (_thin_on) times 4."""
    lines, key = _ground_memo(d, field)["lines"], ((h[0] + 1024) * 4096 + h[1] + 1024) * 16777216 + (t[0] + 1024) * 4096 + t[1] + 1024
    s = lines.get(key)
    if s is None:
        line = ray(h, t, dist)
        s = lines[key] = (1 if _crest_on(d, field, h, t, line) else 0) + (2 if _sight_on(d, field, h, t, line) else 0) + 4 * _thin_on(d, field, h, line)
    return s


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
        if u["state"] in ("broken", "fled") or u["men"] <= 0 or busy_digging(u):
            continue
        if in_contact(d, units, occ, i) and not in_bunker(d, field, u):
            continue
        if "range" in d.weapons[u["weapon"]] and ammo_state(d, u) != "out" and not (u.get("resupplying") and ammo_full(d, u)):
            out += _volley_of(d, units, occ, field, i)
        out += _rider_volley(d, units, occ, field, i)
    return out


def _volley_of(d: Data, units: list, occ: dict, field: dict | None, i: int, men: int | None = None) -> list:
    """Unit i's volley at its target ([v] or []); men: the shooters (default its front ranks)."""
    u = units[i]
    best, blind = _target(d, units, i, field, occ), False
    if best is None and men is None:
        best = _fixed_target(d, units, i, field, occ)
        blind = best is not None
    if best is None:
        return []
    wx = shot_weather(d, field, u["weapon"], best[0], best[2], best[3], _seer(u, blind=blind))
    if wx["blocked"]:
        return []
    up, longer = height_edge(d, field, u["weapon"], best[2], best[3])
    shooters = _shooters(d, u, field) if men is None else men
    v = {"att": i, "dfd": best[1], "men": shooters / 2 if men is None and ammo_state(d, u) == "low" else shooters, "dist": best[0],
         "cover": share_cover(d, field, best[2], units[best[1]]) + ground_cover(d, units[best[1]]) + shield_cover(d, units[best[1]], best[3], best[2]),
         "penalty": wx["penalty"] - up, "misfire": wx["misfire"], "reach": wx.get("reach", 0) + longer, "from": best[2], "to": best[3], "height": up,
         "over": line_fire(d, units, occ, field, i, best[1], best[2], best[3], best[0]), "seen": seen_share(d, field, units[best[1]], best[3], u["weapon"])}
    v.update({k: True for k in ("blind", "flash", "beam") if wx.get(k)})
    if men is None and is_mg(d, u["weapon"]):
        v.update(_beaten(d, units, occ, field, i, best))
    return [v]


def rider_shooters(d: Data, u: dict) -> int:
    """Men of vehicle unit u's riders who can shoot: through an IFV's firing ports (`ports`) or
    from a tank's hull (`rides`), vehicles.rider_fire share of them (0 if they cannot)."""
    K, R = vehicle_kind(d, u), u.get("riders")
    if not K or not R or R["men"] <= 0 or R.get("state") in ("broken", "fled") or "range" not in d.weapons[R["weapon"]]:
        return 0
    F = d.units["vehicles"]["rider_fire"]
    share = 0
    if K.get("ports"):
        share = F["ports"]
    elif K.get("rides"):
        share = F["hull"]
    return math.floor(R["men"] * share)


def _rider_volley(d: Data, units: list, occ: dict, field: dict | None, i: int) -> list:
    """Vehicle unit i's riders shooting from it (rider_shooters), at their own weapon's target
    from its hexes: [v with riders True] or []."""
    n, R = rider_shooters(d, units[i]), units[i].get("riders")
    if n <= 0 or ammo_state(d, R) == "out":
        return []
    n = n / 2 if ammo_state(d, R) == "low" else n
    pseudo = [*units[:i], {**units[i], "weapon": R["weapon"], "kit": R.get("kit"), "quality": R["quality"], "nv": R.get("nv")}, *units[i + 1:]]
    return [{**v, "riders": True} for v in _volley_of(d, pseudo, occ, field, i, n)]


def _shooter(us: list, v: dict) -> dict:
    """The unit a volley is fired by: its vehicle's riders for a riders' volley."""
    return us[v["att"]]["riders"] if v.get("riders") else us[v["att"]]


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
    """% off shots at a unit gone to ground (or emplaced)."""
    return d.units["to_ground"]["cover"] if low(u) else 0


def low(u: dict) -> bool:
    """Gone to ground, or emplaced or dug in where it stands, and not running."""
    return bool(u.get("prone") or ((u.get("emplaced") or dug_here(u)) and u["state"] not in ("broken", "fled")))


def dug_here(u: dict) -> bool:
    """It stands where it dug in (dug: the hex it dug in at; it leaves its holes when it moves)."""
    return bool(u.get("dug")) and list(u["dug"]) == list(u["pos"])


def busy_digging(u: dict) -> bool:
    """Digging in, or sappers laying or lifting mines: it does not shoot."""
    return bool(u.get("digging") or u.get("mining") or u.get("clearing"))


def can_dig(d: Data, u: dict) -> bool:
    """A foot unit with a modern weapon (commander.ground_with) can dig in: not a vehicle,
    mounted men, a battery, anti-tank guns or emplaced."""
    return (u["weapon"] in d.units["commander"]["ground_with"] and not u.get("vehicle") and not u.get("mounted")
            and not is_battery(d, u) and not is_at_gun(d, u) and not u.get("emplaced"))


def _dig_all(d: Data, us: list) -> list:
    """End of the exchange: each unit digging (digging: {at, n}) that is still where it began,
    standing and out of contact digs on; after dig_in.exchanges it is dug in there (dug) and
    logged. One that moved, broke or came into contact stops."""
    occ, out = occupancy(d, us), []
    for i, u in enumerate(us):
        g = u.get("digging")
        if not g:
            continue
        if list(g["at"]) != list(u["pos"]) or u["state"] in ("broken", "fled") or u["men"] <= 0 or in_contact(d, us, occ, i):
            del u["digging"]
            continue
        n = g["n"] + 1
        if n < d.units["dig_in"]["exchanges"]:
            u["digging"] = {"at": list(g["at"]), "n": n}
            continue
        del u["digging"]
        u["dug"] = list(u["pos"])
        out.append({"kind": "dug", "unit": i})
    return out


def can_sap(d: Data, u: dict) -> bool:
    """Sappers can lay or lift mines: a foot unit marked sappers, not mounted, a battery or guns."""
    return (bool(u.get("sappers")) and not u.get("vehicle") and not u.get("mounted")
            and not is_battery(d, u) and not is_at_gun(d, u))


def ahead_row(d: Data, field: dict | None, u: dict) -> list:
    """The row of hexes just ahead of unit u's front row (as wide as it), on the map."""
    rows = footprint(d, u)
    cols, nrows = _size(d, field)
    return [x for x in (step(h, u["facing"]) for h in (rows[0] if rows else [])) if 0 <= x[0] < cols and 0 <= x[1] < nrows]


def known_mine(m: dict, side: int | None = None) -> bool:
    """A minefield hex a side knows of: marked, found (something went into it), or laid by
    that side's sappers (side)."""
    return not m.get("hidden") or bool(m.get("found")) or (side is not None and m.get("side") == side)


def _sapper_done(d: Data, field: dict, u: dict, task: str, w: dict, occ: dict) -> tuple:
    """Unit u's mining or clearing finished: (log kind, hexes) laid (where no unit stands) or
    lifted in the row ahead."""
    M = field.setdefault("mines", {})
    row = ahead_row(d, field, u)
    if task == "mining":
        hexes = [x for x in row if C.hkey(x) not in M and C.hkey(x) not in occ]
        for x in hexes:
            M[C.hkey(x)] = {"kind": w["kind"], "hidden": True, "side": u["side"]}
        return "laid", hexes
    hexes = [x for x in row if C.hkey(x) in M and known_mine(M[C.hkey(x)], u["side"])]
    for x in hexes:
        del M[C.hkey(x)]
    return "lifted", hexes


def _sapper_task(u: dict) -> str | None:
    """The sappers' work under way: mining, clearing or None."""
    if u.get("mining"):
        return "mining"
    return "clearing" if u.get("clearing") else None


def _sapper_stops(d: Data, us: list, occ: dict, i: int, w: dict) -> bool:
    """Unit i's work w stops: not sappers, moved or turned, running, gone, or in contact."""
    u = us[i]
    return (not can_sap(d, u) or list(w["at"]) != list(u["pos"]) or w["facing"] != u["facing"]
            or u["state"] in ("broken", "fled") or u["men"] <= 0 or in_contact(d, us, occ, i))


def _sappers_all(d: Data, us: list, field: dict | None) -> list:
    """End of the exchange: sappers mining ({at, facing, n, kind}) or clearing ({at, facing, n})
    that are still where and as they began, standing and out of contact, work on (sappers only); after
    mines.sappers lay (or clear) exchanges the row ahead of their front is mined, hidden, where no unit stands (or its
    known minefield hexes lifted) and logged. One that moved, turned, broke or came into contact stops."""
    if field is None:
        for u in us:
            u.pop("mining", None)
            u.pop("clearing", None)
        return []
    occ, out, S = occupancy(d, us), [], d.units["mines"]["sappers"]
    for i, u in enumerate(us):
        task = _sapper_task(u)
        if not task:
            continue
        w = u[task]
        if _sapper_stops(d, us, occ, i, w):
            del u[task]
            continue
        n = w["n"] + 1
        if n < S["lay" if task == "mining" else "clear"]:
            u[task] = {**w, "at": list(w["at"]), "n": n}
            continue
        del u[task]
        kind, hexes = _sapper_done(d, field, u, task, w, occ)
        out.append({"kind": kind, "unit": i, "hexes": len(hexes), **({"mine": w["kind"]} if task == "mining" else {})})
    return out


def has_shields(d: Data, u: dict) -> bool:
    """Its guns have shields: a weapon that always had them (gun_shields.weapons), or one that
    sometimes did (optional) on a unit the GM marked shielded."""
    S = d.units.get("gun_shields") or {}
    return u["weapon"] in S.get("weapons", []) or (bool(u.get("shielded")) and u["weapon"] in S.get("optional", []))


def shield_cover(d: Data, u: dict, t, h) -> int:
    """% off small-arms fire from hex h at unit u (its hex t): its guns' shields
    (gun_shields), from its front only."""
    S = d.units.get("gun_shields") or {}
    if not has_shields(d, u) or list(h) == list(t):
        return 0
    return S["cover"] if arc(u["facing"], bearing(t, h)) == "front" else 0


def seen_share(d: Data, field: dict | None, u: dict, at, weapon: str | None = None) -> float:
    """The share of aimed shots at unit u (its hex `at` aimed at) that find a man: hidden.seen %
    (hidden.mg_seen % for a machine gun) if it is gone to ground, in a bunker or in ground that
    hides it, else all of them."""
    H = d.units.get("hidden")
    if not H:
        return 1
    if low(u) or in_bunker(d, field, u) or (at is not None and hides_at(d, field, at)):
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


def _screen_hexes(d: Data, field: dict | None, flag: str = "screen") -> set:
    """The keys ("q,r") of the field's hexes whose ground screens sight (flag screen: woods,
    buildings) or thins it (flag light: scrub, orchards)."""
    g = (field or {}).get("ground") or {}
    hit = _SCREENS.get((id(g), flag))
    if hit is None or hit[0] is not g or hit[1] != len(g):
        hit = (g, len(g), {k for k, v in g.items() if d.units["ground"].get(v, {}).get(flag)})
        _SCREENS[(id(g), flag)] = hit
    return hit[2]


def _raised_hexes(d: Data, field: dict | None) -> dict:
    """The field's open ground that stands above the flat ("q,r": height): slopes and high ground
    (tall buildings screen sight as buildings do, so they are left to clear_sight)."""
    g, kinds = (field or {}).get("ground") or {}, d.units["ground"]
    hit = _SCREENS.get((id(g), "height"))
    if hit is None or hit[0] is not g or hit[1] != len(g):
        hit = (g, len(g), {k: kinds[v]["height"] for k, v in g.items() if kinds.get(v, {}).get("height", 0) > 0 and not kinds[v].get("screen")})
        _SCREENS[(id(g), "height")] = hit
    return hit[2]


def over_crest(d: Data, field: dict | None, h, t, dist: int) -> bool:
    """Dead ground: whether open ground (a slope or high ground) higher than both h and t stands
    on the line between them (_crest_on), remembered for the field's ground."""
    return bool(_raised_hexes(d, field)) and (_sight_line(d, field, h, t, dist) & 1) > 0


def thinned(d: Data, field: dict | None, h, t, dist: int) -> int:
    """How many hexes of light cover (scrub, orchards) lie on the line from h to t, not the
    ends, as high as where the man at h stands (_thin_on), remembered for the field's ground."""
    return _sight_line(d, field, h, t, dist) >> 2 if _screen_hexes(d, field, "light") else 0


def clear_sight(d: Data, field: dict | None, h, t, dist: int) -> bool:
    """Whether a man at hex h sees hex t to aim at it (_sight_on), remembered for the field's ground."""
    if not _screen_hexes(d, field) and not _screen_hexes(d, field, "light") and not _raised_hexes(d, field):
        return True
    return (_sight_line(d, field, h, t, dist) & 2) > 0


def smoked_line(field: dict | None, h, t, dist: int) -> bool:
    """Whether smoke hangs over any hex of the line from h to t (its ends too): a smoke hex i
    hexes from h is on the line only as its step i (combat.ray_at)."""
    for k in (field or {}).get("smoke") or {}:
        x = [int(v) for v in k.split(",")]
        i = hdist(h, x)
        if i <= dist and hdist(x, t) == dist - i and C.ray_at(h, t, i) == x:
            return True
    return False


def _crest_on(d: Data, field: dict | None, h, t, line: list) -> bool:
    """Dead ground on the line: open ground (a slope or high ground) higher than both h and t
    between them (not within line_of_fire.crest_clear hexes of either end: a man just behind a
    crest sees over it, and is seen)."""
    raised = _raised_hexes(d, field)
    if not raised:
        return False
    k = d.units["line_of_fire"].get("crest_clear", 1)
    top = max(height_at(d, field, h), height_at(d, field, t))
    return any(raised.get(f"{y[0]},{y[1]}", 0) > top for y in line[1 + k:len(line) - 1 - k])


def _thin_on(d: Data, field: dict | None, h, line: list) -> int:
    """The hexes of light cover (scrub, orchards) on the line, not the ends, as high as where
    the man at h stands."""
    thin = _screen_hexes(d, field, "light")
    if not thin:
        return 0
    up = height_at(d, field, h)
    return sum(1 for y in line[1:len(line) - 1] if f"{y[0]},{y[1]}" in thin and height_at(d, field, y) >= up)


def _sight_on(d: Data, field: dict | None, h, t, line: list) -> bool:
    """Whether a man at h sees t to aim at it (line: the ray between them): no ground higher than both
    ends between (_crest_on: dead ground), no ground that screens (woods, buildings) on the line
    between as high as where he stands, past the first line_of_fire.see_into hexes at either end
    (he sees out of a screen's edge, and into it), and no more than line_of_fire.thin.blind_past
    hexes of light cover between."""
    cover, L = _screen_hexes(d, field), d.units["line_of_fire"]
    if not cover and not _screen_hexes(d, field, "light") and not _raised_hexes(d, field):
        return True
    k, up = L.get("see_into", 1), height_at(d, field, h)
    if _crest_on(d, field, h, t, line):
        return False
    if any(f"{y[0]},{y[1]}" in cover and height_at(d, field, y) >= up for y in line[1 + k:len(line) - 1 - k]):
        return False
    return _thin_on(d, field, h, line) <= L["thin"]["blind_past"]


def shot_weather(d: Data, field: dict | None, weapon: str, dist: int, h=None, t=None, seer: dict | None = None) -> dict:
    """The weather's effect on a shot `dist` field hexes away, from hex h to hex t (for the
    wind's direction): {blocked, penalty, misfire, reach}. Smoke on the line blocks it, and so
    do woods and buildings between (clear_sight), unless it is fired blind. seer:
    the shooter in the dark, {kit, blind} (see in_the_dark)."""
    shot = h is not None and t is not None
    if shot and smoked_line(field, h, t, dist) and not sees_smoke(d, seer):
        return {"blocked": "Smoke: no one can see to shoot through it.", "penalty": 0, "misfire": 0, "reach": 0}
    if shot and not (seer or {}).get("blind") and over_crest(d, field, h, t, dist):
        return {"blocked": "Higher ground between: dead ground, no one can see over it to shoot.", "penalty": 0, "misfire": 0, "reach": 0}
    if shot and not (seer or {}).get("blind") and not clear_sight(d, field, h, t, dist):
        return {"blocked": "Woods, buildings or thick scrub between: no one can see to aim through them.", "penalty": 0, "misfire": 0, "reach": 0}
    if is_gun(d, weapon):
        return gun_weather(d, field, dist, h, t, seer)
    out = in_the_cold(d, field, weapon, in_the_dark(d, field, dist, t, C.weather_attack(d, (field or {}).get("weather"), weapon, _seen_at(d, field, dist, seer), h, t, _up(field)), seer))
    return _thin_fire(d, field, out, (h, t, dist) if shot else None)


def _seen_at(d: Data, field: dict | None, dist: int, seer: dict | None) -> int:
    """How far the shooter must see to aim, in 2 m hexes, against the weather's sight: 0 when it
    does not count (fired blind down a fixed line, or a thermal sight within its reach in a
    sandstorm)."""
    far = dist * d.units["range_scale"]
    cond = d.weather["conditions"].get(((field or {}).get("weather") or {}).get("cond")) if d.weather else None
    if (seer or {}).get("blind") or ((cond or {}).get("thermal") and sees_smoke(d, seer) and far <= cond["thermal"]):
        return 0
    return far


def _thin_fire(d: Data, field: dict | None, out: dict, shot: tuple) -> dict:
    """Aimed fire through light cover: line_of_fire.thin.per % off for each hex of it between."""
    n = thinned(d, field, *shot) if shot and not out["blocked"] else 0
    return {**out, "penalty": out["penalty"] + n * d.units["line_of_fire"]["thin"]["per"]} if n else out


def cold_of(d: Data, field: dict | None) -> dict | None:
    """The field's cold (weather.cold, a weather.yaml cold level), or None."""
    return ((d.weather or {}).get("cold") or {}).get("levels", {}).get(((field or {}).get("weather") or {}).get("cold") or "")


def in_the_cold(d: Data, field: dict | None, weapon: str, out: dict) -> dict:
    """In hard cold the automatic weapons (weather.yaml cold.jams) misfire the level's `jam` % more."""
    L = cold_of(d, field)
    if L and not out["blocked"] and weapon in d.weather["cold"]["jams"]:
        out["misfire"] = min(100, out["misfire"] + L["jam"])
    return stopped(d, field, weapon, out)


def stoppage_of(d: Data, war, weapon: str):
    """The % of an automatic weapon's fire lost to stoppages in this war (units.yaml
    reliability.stoppage): the war's figure for the weapon, else its `all`; 0 if none."""
    S = (d.units.get("reliability") or {}).get("stoppage") or {}
    W = (S.get("by_war") or {}).get(war)
    if not W or weapon not in S.get("weapons", []):
        return 0
    return W.get(weapon, W.get("all", 0))


def stopped(d: Data, field: dict | None, weapon: str, out: dict) -> dict:
    """Stoppages on top of the weather's misfires (field.war, set as the battle begins)."""
    p = 0 if out["blocked"] else stoppage_of(d, (field or {}).get("war"), weapon)
    if p:
        out["misfire"] = min(100, out["misfire"] + p)
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
    sight, aim = dark_sight(d, L, night_device(d, seer, field))
    far = dist * d.units["range_scale"]
    if sight is not None and far > sight:
        if flashing(field, t) and far <= d.weather["light"]["flash"]:
            out["flash"] = True
        elif beaming(field, t) and sees_beam(d, seer, field) and far <= d.weather["light"]["night_vision"]["beam"]:
            out["beam"] = True
        else:
            out["blocked"] = f"{L['name']}: no one can be seen to aim at beyond {sight // d.units['range_scale']} hexes."
            return out
    out["penalty"] += aim
    return out


def night_device(d: Data, seer: dict | None, field: dict | None = None) -> str | None:
    """The night-vision device a shooter or watcher ({kit, nv, at}) carries: the unit's own (nv;
    "none" for none), else his kit's (light.night_vision.kits carry its kit_device), else None.
    With the field: None if the device `washes` out where he stands, in a flare's light."""
    s, N = seer or {}, (d.weather or {}).get("light", {}).get("night_vision") or {}
    dev = None
    if s.get("nv"):
        dev = None if s["nv"] == "none" else s["nv"]
    elif s.get("kit") in (N.get("kits") or []):
        dev = N.get("kit_device")
    if dev and field is not None and ((N.get("devices") or {}).get(dev) or {}).get("washes") and lit(field, s.get("at")):
        return None
    return dev


def _seer(u: dict, **k) -> dict:
    """A unit as a shooter or watcher for the dark: its kit, its night-vision device, and where it
    stands (for a flare's washout)."""
    return {"kit": u.get("kit"), "nv": u.get("nv"), "at": u.get("pos"), **k}


def beaming(field: dict | None, t) -> bool:
    """Whether hex t is one a unit fired from by its infrared beam last exchange (field.beams)."""
    return t is not None and list(t) in ((field or {}).get("beams") or [])


def sees_beam(d: Data, seer: dict | None, field: dict | None) -> bool:
    """Whether the watcher's device (not washed out) picks up an infrared beam."""
    dev = (d.weather["light"].get("night_vision") or {}).get("devices", {}).get(night_device(d, seer, field) or "")
    return bool(dev and dev.get("sees_beam"))


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


def _beams(d: Data, us: list, log: list, field: dict | None) -> None:
    """After the shooting, in any dark: field.beams becomes the hexes of every unit that fired by its
    infrared searchlight (a device with `beam`, not washed out), seen by enemy infrared and
    intensifier devices through the next exchange; else none."""
    if field is None:
        return
    L = light_of(d, field)
    if L is None or L["sight"] is None:
        field.pop("beams", None)
        return
    devs = d.weather["light"]["night_vision"].get("devices") or {}
    fired = sorted({x["att"] for x in log if x.get("kind") in FLASHING and x.get("att") is not None})
    fired = [i for i in fired if (devs.get(night_device(d, _seer(us[i]), field) or "") or {}).get("beam")]
    hexes = sorted({tuple(h) for i in fired for row in footprint(d, us[i]) for h in row})
    if hexes:
        field["beams"] = [list(h) for h in hexes]
    else:
        field.pop("beams", None)


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
    an odd second d100, else right; not if it no longer fits), strays a hex on along that wrong
    facing (_stray), and cannot move for light.lost_for exchanges. -> {lost (bool), unit,
    strayed (bool)}."""
    u, L = units[i], light_of(d, field)
    if L is None or not L.get("lost"):
        return {"lost": False, "unit": u, "strayed": False}
    chance = max(0, min(100, L["lost"] + (60 - quality(d, u["quality"])["nerve"]) // 2))
    if rng.randint(1, 100) > chance:
        return {"lost": False, "unit": u, "strayed": False}
    left = rng.randint(1, 100) % 2 == 0
    turned = {**u, "facing": (u["facing"] + (1 if left else -1)) % 6, "lost": d.weather["light"]["lost_for"]}
    if not _fits(d, units, i, turned, size, field):
        return {"lost": True, "unit": {**turned, "facing": u["facing"]}, "strayed": False}
    gone = _stray(d, units, i, turned, (left, size, field))
    return {"lost": True, "unit": gone or turned, "strayed": gone is not None}


def _stray(d: Data, units: list, i: int, u: dict, how: tuple) -> dict | None:
    """A lost unit, turned to u, goes on a hex along its wrong facing: the front hexside on the
    side it turned to (veering left, the left one). None if that would take it off the map, onto
    other units or ground it cannot stand on, or into contact with the enemy."""
    left, size, field = how
    moved = {**u, "pos": step(u["pos"], u["facing"] + (1 if left else 0))}
    if not _fits(d, units, i, moved, size, field):
        return None
    after = units[:i] + [moved] + units[i + 1:]
    return None if in_contact(d, after, occupancy(d, after), i) else moved


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


def holds_works(d: Data, field: dict | None, h, t: dict) -> bool:
    """Unit t holds works against an attack from hex h: dug in or emplaced where it stands, or
    any hex of it with cover from the works toward h, or in ground that hides men (buildings,
    rubble)."""
    if dug_here(t) or t.get("emplaced"):
        return True
    if not field:
        return False
    cols, rows = _size(d, field)
    return any(ground_at(d, field, x).get("hides") or C.missile_cover(d, _works(field), h, x, cols, rows)["cover"] > 0
               for row in footprint(d, t) for x in row)


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
        if e["side"] == u["side"] or e["men"] <= 0 or e["state"] == "fled" or (e.get("vehicle") and not hurts_armour(d, u["weapon"]) and not soft(d, e) and not exposed(d, e)):
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


def _beyond_reach(d: Data, weapon: str, dist: int) -> bool:
    """Out of range even with its bands doubled (the wind and height add at most half): a
    shortcut that changes nothing."""
    return not is_gun(d, weapon) and not d.weapons[weapon].get("off_map") and field_range(d, weapon, dist, 100) is None


def _can_shoot(d: Data, u: dict, field: dict | None, shot: tuple, clear) -> bool:
    """Unit u's weapon reaches from h to t (shot: (h, t, dist)), in sight, with a line of fire."""
    h, t, dist = shot
    if _beyond_reach(d, u["weapon"], dist):          # out of range however the wind and height help: no need to look
        return False
    wx = shot_weather(d, field, u["weapon"], dist, h, t, _seer(u))
    reach = wx.get("reach", 0) + height_edge(d, field, u["weapon"], h, t)[1]
    return not wx["blocked"] and _reaches(d, u, dist, reach) and (clear is None or clear(h, t, dist))


def _nearest_ahead(d: Data, u: dict, front: list, fv: tuple, hexes: list, field: dict | None = None, clear=None):
    """(distance, front hex, target hex): the shortest distance in range of unit u's weapon and
    in sight from a front hex to one of `hexes` ahead of the line (with a line of fire), or None."""
    best = None
    for t in hexes:
        c = _cube(t)
        for h in front:
            s = _cube(h)
            if sum((c[k] - s[k]) * fv[k] for k in range(3)) <= 0:
                continue
            dist = hdist(h, t)
            if (best is None or dist < best[0]) and _can_shoot(d, u, field, (h, t, dist), clear):
                best = (dist, h, t)
    return best


def _side(u: dict, table: str, d: Data | None = None) -> dict:
    """A unit as a fighting side: hand to hand (d given), a battery's crews fight with their own
    weapon, and a tired unit strikes and parries worse."""
    weapon = melee_weapon(d, u) if d else u["weapon"]
    return {"table": table, "weapon": weapon, "kit": u.get("kit"), "quality": u["quality"], **(_tired(d, u) if d else {})}


def _shooter_side(d: Data, u: dict, table: str) -> dict:
    """A unit as a side shooting: its own weapon, its aim worse if it is tired."""
    return {**_side(u, table), **_tired(d, u)}


def _tired(d: Data, u: dict) -> dict:
    """The attack and defence a unit's fatigue costs it (weather.yaml fatigue levels); {} if fresh."""
    pen = d.weather["fatigue"]["levels"][u["fatigue"]]["penalty"] if u.get("fatigue") else 0
    return {"attack": -pen, "defence": -pen} if pen else {}


def _toil_going(d: Data, us: list, field: dict | None) -> None:
    """In deep mud or snow, every hex a unit (not a vehicle) went since the last exchange is a toil."""
    if C.deep_going(d, ((field or {}).get("weather") or {}).get("ground")) <= 0:
        return
    for u in us:
        if u.get("toil_from") and not u.get("vehicle"):
            tire(d, u, hdist(u["toil_from"], u["pos"]))


def _toil_fought(d: Data, us: list, fought: set) -> None:
    """End of the exchange: a toil for each unit that struck or was struck hand to hand; where each
    unit stands now is where its next going is counted from."""
    for k in sorted(fought):
        tire(d, us[k], 1)
    for u in us:
        u["toil_from"] = list(u["pos"])


def tire(d: Data, u: dict, n: int) -> None:
    """n more toil for unit u: a fatigue step worse each time its kit's load of toil is reached
    (wounds.yaml characteristics.toil blows, kits not listed light), to `worst` at most."""
    T = d.wounds["combat"]["characteristics"]["toil"]
    need = T["blows"][T["load"].get(u.get("kit"), "light")]
    toil, f = u.get("toil", 0) + n, u.get("fatigue", 0)
    while toil >= need:
        toil -= need
        if f < T["worst"]:
            f += 1
    u["toil"] = toil
    if f:
        u["fatigue"] = f


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
    _toil_going(d, us, field)
    log += _mines_all(d, us, table, rng, acc, field)
    log += _closing_all(d, us, table, rng, acc, field)
    lost0, dealt0 = list(lost), list(dealt)
    struck = _strike_all(d, us, table, rng, acc, flanked, field, lost0)
    hand = ([x - y for x, y in zip(lost, lost0)], [x - y for x, y in zip(dealt, dealt0)])   # hand to hand this exchange (morale.posture_hand)
    fought = {l[k] for l in struck if l["kind"] == "melee" for k in ("att", "dfd")}
    log += struck
    log += _shoot_all(d, us, table, rng, acc, field, under)
    log += _indirect_all(d, us, table, rng, acc, field, under)
    log += _assault_all(d, us, table, rng, acc, field)
    if field is not None:
        field["blast"] = blast_weapon(d, table) is not None   # demolition charges on this table (walls)
    log += _breach_all(d, us, field)
    occ = occupancy(d, us)
    before = [u["men"] for u in us]
    fired = _fired_on(log)
    for i, u in enumerate(us):
        if i in fired:
            u["fired_on"] = True                    # shot at this exchange, hit or not: for storming in bounds
        else:
            u.pop("fired_on", None)
        cut = min(lost[i], u["men"])
        u.update(men=u["men"] - cut, down=u.get("down", 0) + cut, dead=u.get("dead", 0) + min(dead[i], cut))
        if cut > 0:
            u["hit"] = True                         # it lost men this exchange: under fire, for the next moves
        else:
            u.pop("hit", None)
    log += _morale_all(d, us, occ, before, (lost, dealt, flanked, hand), rng, table, field)
    log += _suppress_all(d, us, under, rng)
    log += _heroes_after(d, us, rng, [not lost[i] and not under[i] and not in_contact(d, us, occ, i) for i in range(len(us))], cauterises(d, table), posts_moving(field))
    log += _parties_after(d, us, field)
    log += _lying_after(d, us, table, rng)
    log += _posts_after(d, us, field, table, rng)
    _posts_settle(field)
    log += _dig_all(d, us)
    log += _sappers_all(d, us, field)
    _toil_fought(d, us, fought)
    _unhooked_after(us)
    for i, u in enumerate(us):
        u["charged"] = False
        u.pop("jostled", None)
        if u.get("resupplying") and ammo_full(d, u):
            log.append({"kind": "resupplied", "unit": i})
        _battery_after(d, u)
        if u.get("pinned"):
            u["pinned"] -= 1
        if u.get("lost"):
            u["lost"] -= 1
    _flashes(d, us, log, field)
    _beams(d, us, log, field)
    for b in (field or {}).get("support") or []:
        if b.get("mission") and b["mission"].get("wait", 0) > 0:
            b["mission"]["wait"] -= 1
    log += _displace_all(field)
    log += _overrun_all(d, us, field)
    _smoke_thins(field)
    _smoke_drifts(d, field)
    _lit_fades(field)
    log += landings(d, us, table, rng, field)
    log += _air_drops(d, field, rng)
    log += _vehicles_after(d, us, field)
    log += objective_held(d, us, field)
    _mark_was(us, field)
    return us, log


def off_objective(d: Data, u: dict, obj) -> int:
    """Hexes from unit u's nearest hex to the objective hex (10**6 if it has no hexes)."""
    return min((hdist(h, obj) for row in footprint(d, u) for h in row), default=10**6)


def objective_radii(d: Data, field: dict | None) -> tuple:
    """(radius, hold, guard) of the field's objective: commander.objective's, each widened by
    as much as the field's own objective_radius (a battlefield's place) exceeds its radius."""
    R = d.units["commander"]["objective"]
    r = (field or {}).get("objective_radius") or R["radius"]
    return r, R["hold"] + r - R["radius"], R["guard"] + r - R["radius"]


def second_view(field: dict) -> dict:
    """The field as the commander sees it for the GM's second objective (objective2): a shallow
    copy with that hex as its objective, at the commander's own radius. Read only: nothing that
    orders units sets keys on the field."""
    return {**field, "objective": list(field["objective2"]), "objective_radius": None}


def objective_held(d: Data, us: list, field: dict | None) -> list:
    """With an objective marked on the field: [{kind objective, hex, sides (those with a standing
    unit within its radius (objective_radii) of it, in the units' order), held (the one side
    there, else None)}], and a second line (second: True) for a second objective, else []."""
    if not (field or {}).get("objective"):
        return []
    out = [_held_at(d, us, field)]
    if field.get("objective2"):
        out.append({**_held_at(d, us, second_view(field)), "second": True})
    return out


def _held_at(d: Data, us: list, field: dict) -> dict:
    """{kind objective, hex, sides, held} for the field's objective (see objective_held)."""
    obj, r = field["objective"], objective_radii(d, field)[0]
    sides = list(dict.fromkeys(u["side"] for u in us if u["state"] not in ("broken", "fled") and u["men"] > 0 and off_objective(d, u, obj) <= r))
    return {"kind": "objective", "hex": list(obj), "sides": sides, "held": sides[0] if len(sides) == 1 else None}


def _mark_was(us: list, field: dict | None) -> None:
    """With minefields down, where each unit's next moves begin (the ground it crosses)."""
    if (field or {}).get("mines"):
        for u in us:
            u["was"] = [list(u["pos"]), u["facing"]]


# ---------- minefields ----------

def crossed(d: Data, u: dict, field: dict | None = None) -> list:
    """The hexes unit u went into since `was` (where it stood when the moves began): its footprint
    at each step of the way it went (went), less the hexes it started on, in order."""
    was = u.get("was")
    if not was or (list(was[0]) == list(u["pos"]) and was[1] == u["facing"]):
        return []
    old = {C.hkey(x) for row in footprint(d, {**u, "pos": list(was[0]), "facing": was[1]}) for x in row}
    out, seen = [], set(old)
    for p in went(d, field, u, was[0]):
        for x in (x for row in footprint(d, {**u, "pos": list(p)}) for x in row):
            if C.hkey(x) not in seen:
                seen.add(C.hkey(x))
                out.append(x)
    return out


def went(d: Data, field: dict | None, u: dict, start) -> list:
    """The middle hex's way from start to where unit u stands, start left out ([pos] if it only
    turned): the cheapest way over the ground and works within its move (mine_path) that
    crosses the fewest minefield hexes its side knows of; else a straight line."""
    if list(start) == list(u["pos"]):
        return [list(u["pos"])]
    return (mine_path(d, field, u, start) if field else None) or ray(list(start), u["pos"], hdist(start, u["pos"]))[1:]


def mine_path(d: Data, field: dict, u: dict, start) -> list | None:
    """The way (hexes after start) to u's position, within its allowance (times charge_move if
    it charged), crossing the fewest hexes of known enemy minefields (known_mine) in its
    footprint, then costing the least; None if there is none. Other units are left out (they
    have moved since). Of equal ways, the one nearest the straight line (_way_back)."""
    limit = allowance(d, u) * (d.units["charge_move"] if u.get("charged") else 1)
    size, goal, s = _size(d, field), tuple(u["pos"]), tuple(start)
    if limit <= 0 or hdist(s, goal) > limit:
        return None
    mines, steps = field.get("mines") or {}, {}
    levels = _mine_levels(d, field, u, (s, limit, size), (mines, steps))
    ends = [(levels[c][goal], c) for c in range(limit + 1) if goal in levels[c]]
    if not ends:
        return None
    m, c = min(ends)
    return _way_back(d, field, u, (goal, c, m), (levels, steps, mines, size, s))


def _mine_levels(d: Data, field: dict, u: dict, run: tuple, ms: tuple) -> list:
    """For each movement spent (0 to limit), {hex: the fewest known enemy minefield hexes
    crossed to reach it for exactly that movement}, from start."""
    (s, limit, size), (mines, steps) = run, ms
    levels = [{} for _ in range(limit + 1)]
    levels[0][s] = 0
    for c in range(limit + 1):
        for h, m0 in sorted(levels[c].items()):
            for x, sc in _steps_cached(d, field, u, h, size, steps):
                m = m0 + _known_mines_at(d, u, x, mines) if c + sc <= limit else None
                if m is not None and m < levels[c + sc].get(x, 10**9):
                    levels[c + sc][x] = m
    return levels


def _steps_cached(d: Data, field: dict, u: dict, h: tuple, size: tuple, steps: dict) -> list:
    """_steps_from for hex h, other units left out, worked out once."""
    if h not in steps:
        steps[h] = _steps_from(d, field, u, h, {}, size)
    return steps[h]


def _known_mines_at(d: Data, u: dict, x, mines: dict) -> int:
    """Hexes of u's footprint at x in minefields its side knows of that are not its own side's."""
    return sum(1 for row in footprint(d, {**u, "pos": list(x)}) for y in row
               if C.hkey(y) in mines and mines[C.hkey(y)].get("side") != u["side"] and known_mine(mines[C.hkey(y)], u["side"]))


def _step_into(d: Data, field: dict, u: dict, ph: tuple, ss: tuple) -> int | None:
    """What it costs the middle hex to step from p into h (None if it cannot, or p is off the map)."""
    (p, h), (size, steps) = ph, ss
    if not (0 <= p[0] < size[0] and 0 <= p[1] < size[1]):
        return None
    return next((k for x, k in _steps_cached(d, field, u, p, size, steps) if x == h), None)


def _way_back(d: Data, field: dict, u: dict, end: tuple, ctx: tuple) -> list | None:
    """From (hex, cost, mines) back to the start: at each hex the neighbour that steps into it at
    a level and mines count that fit, the nearest the straight line from the start (the first by
    direction of equals). -> the hexes after the start, or None if the trail breaks."""
    (h, c, m), (levels, steps, mines, size, start) = end, ctx
    line, out = ray(list(start), list(h), hdist(start, h)), [list(h)]
    while c > 0:
        here = _known_mines_at(d, u, h, mines)
        best = _step_back(d, field, u, (h, c, m - here), (levels, steps, size, line))
        if best is None:
            return None
        h, c, m = best[1], c - best[2], m - here
        if c > 0:
            out.append(list(h))
    return out[::-1]


def _step_back(d: Data, field: dict, u: dict, at: tuple, ctx: tuple) -> tuple | None:
    """(off the line, hex, cost) of the neighbour of h that steps into it from the level below
    with `want` mines: the nearest the straight line, the first by direction of equals."""
    (h, c, want), (levels, steps, size, line), best = at, ctx, None
    for dirn in range(6):
        p = tuple(step(list(h), dirn))
        sc = _step_into(d, field, u, (p, h), (size, steps))
        if sc is None or sc > c or levels[c - sc].get(p) != want:
            continue
        off = min(hdist(p, x) for x in line)
        if best is None or off < best[0]:
            best = (off, p, sc)
    return best


def _mines_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None) -> list:
    """Units that went into minefield hexes (crossed) set them off, before the shooting: men
    struck at the kind's `men` % (a hex's worth a hex) and wounded as by a mine; vehicles struck
    at its `vehicles` %, then knocked out at their armour's `mine` %, else immobilised. Each
    field set off is found (shown on the map). Mines a side's own sappers laid (side) do not
    strike that side: its men know where they lie."""
    mines, log = (field or {}).get("mines"), []
    if not mines:
        return log
    for i, u in enumerate(us):
        if u["men"] <= 0 or u["state"] == "fled":
            continue
        hit = [x for x in crossed(d, u, field) if C.hkey(x) in mines and mines[C.hkey(x)].get("side") != u["side"]]
        if hit:
            for x in hit:
                mines[C.hkey(x)]["found"] = True
            log += _set_off(d, us, i, [mines[C.hkey(x)]["kind"] for x in hit], (table, rng, acc))
    return log


def _mines_vehicles(d: Data, us: list, i: int, kinds: list, lc: tuple) -> list:
    """Vehicle unit i in minefield hexes: a vehicle struck at the kind's `vehicles` % for each,
    knocked out at its armour's `mine` %, else immobilised. lc: (log line, (table, dice, tallies))."""
    line, (table, rng, acc) = lc
    M, u = d.units["mines"], us[i]
    struck = sum(1 for k in kinds if rng.randint(1, 100) <= M["kinds"][k]["vehicles"])
    kills = sum(1 for _ in range(struck) if rng.randint(1, 100) <= armour_of(d, u)["mine"])
    k = knock_out(d, us, i, kills, (table, rng), acc)
    left = vehicles_left(d, u, acc[0][i])
    immobile = min(left, struck - k["knocked"])
    u["immobile"] = min(left, u.get("immobile", 0) + immobile)
    return _logged({**line, "struck": struck, "knocked": k["knocked"], "crew": k["crew"], "immobilised": immobile, **_riders_line(k)}, k["tally"])


def _set_off(d: Data, us: list, i: int, kinds: list, ctx: tuple) -> list:
    """Unit i in minefield hexes of these kinds: its men or vehicles struck (_mines_all)."""
    table, rng, acc = ctx
    M, u = d.units["mines"], us[i]
    line = {"kind": "mines", "unit": i, "hexes": len(kinds)}
    if u.get("vehicle"):
        return _mines_vehicles(d, us, i, kinds, (line, ctx))
    per = form(d, u)["per_hex"]
    struck = sum(1 for k in kinds for _ in range(min(per, u["men"])) if rng.randint(1, 100) <= M["kinds"][k]["men"])
    weapon = M["weapon"] if M["weapon"] in (d.tables.get(table) or {}).get("weapons", []) else None
    if not struck or weapon is None:
        return [{**line, "struck": struck, "down": 0, "dead": 0}]
    t = _take_hurt(u, _blows(d, {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}, _side(u, table), struck, M["attack"], 0, rng, _exposure(d, u, False, True), -1000))
    acc[0][i] += t["down"]
    acc[1][i] += t["dead"]
    return _logged({**line, "struck": struck}, t)


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
    """End of the exchange: each side's helicopters away come back as their turnaround runs
    out; then the lifts (field.lifts: [{unit, lz, left, kind}]: kind in (men coming on), supply
    (a dump to the zone) or out (a unit lifted away)) fly in the order called, each with as many
    of its side's free helicopters as it needs (carry men each; a supply lift one), at most
    heliborne.at_once at a zone this exchange. A lift waits while its zone is blocked or there
    is no room. At a hot zone each man landing is struck (_hot_landing) and each helicopter may
    be hit (_helo_hits)."""
    if "heliborne" not in d.units or not field:
        return []
    for H in field.get("helos") or []:
        H["away"] = [t - 1 for t in H.get("away", []) if t > 1]
    lifts, log, used = field.get("lifts") or [], [], {}
    for lf in lifts:
        if lf["left"] > 0:
            log += _fly(d, us, (table, rng, field), lf, used)
    field["lifts"] = [lf for lf in lifts if lf["left"] > 0]
    return log


def helos(d: Data, field: dict, side) -> dict:
    """A side's helicopters (field.helos, made from heliborne's defaults the first time):
    {side, aircraft, carry, turnaround, away: [exchanges until back], damaged, downed}."""
    for H in field.setdefault("helos", []):
        if H["side"] == side:
            return H
    D = d.units["heliborne"]
    H = {"side": side, "aircraft": D["aircraft"], "carry": D["carry"], "turnaround": D["turnaround"], "away": [], "damaged": 0, "downed": 0}
    field["helos"].append(H)
    return H


def helos_free(H: dict) -> int:
    """Helicopters ready to fly: not away, damaged or downed."""
    return max(0, H["aircraft"] - len(H.get("away", [])) - H.get("damaged", 0) - H.get("downed", 0))


def _fly(d: Data, us: list, ctx: tuple, lf: dict, used: dict) -> list:
    """One lift this exchange, if its side has helicopters free and its zone room (see landings)."""
    table, rng, field = ctx
    side, key = lf["unit"]["side"], f"{lf['lz'][0]},{lf['lz'][1]}"
    H, kind = helos(d, field, side), lf.get("kind", "in")
    can = min(d.units["heliborne"]["at_once"] - used.get(key, 0), helos_free(H))
    if can <= 0:
        return []
    state = lz_state(d, us, field, side, lf["lz"])
    if state == "blocked":
        return [{"kind": "waveoff", "name": lf["unit"]["name"], "side": side, "lz": lf["lz"], "why": "blocked"}]
    if kind == "in" and any(u.get("id") is not None and u.get("id") == lf["unit"].get("id") and u["state"] in ("broken", "fled") for u in us):
        lf["left"] = 0                            # its men on the ground have broken: the rest of the lift turns back
        return [{"kind": "waveoff", "name": lf["unit"]["name"], "side": side, "lz": lf["lz"], "why": "routed"}]
    if kind == "supply":
        n, log = 1, _supply_lift(field, lf)
    elif kind == "out":
        n, log = _lift_out(d, us, (field, H, can), lf)
    else:
        n, log = _land(d, us, (table, rng, field), lf, min(lf["left"], can * H["carry"]))
        n = -(-n // H["carry"])
    if n <= 0:
        return log
    used[key] = used.get(key, 0) + n
    return log + _helo_hits(d, (rng, field), H, (n, state == "hot", lf))


def _supply_lift(field: dict, lf: dict) -> list:
    """A helicopter sets down a supply dump on its zone."""
    field.setdefault("dumps", []).append({"at": list(lf["lz"]), "side": lf["unit"]["side"]})
    lf["left"] = 0
    return [{"kind": "helisupply", "side": lf["unit"]["side"], "lz": list(lf["lz"])}]


def _lift_out(d: Data, us: list, fhc: tuple, lf: dict) -> tuple:
    """A unit lifted away: as many of its men as the free helicopters carry (fewer if it has
    fewer), if it still stands within heliborne.zone hexes of the zone, out of contact. Its men
    flown out are safe (flown). -> (helicopters used, log)."""
    field, H, can = fhc
    i = next((k for k, u in enumerate(us) if u.get("id") is not None and u.get("id") == lf["unit"].get("id")), None)
    u = None if i is None else us[i]
    if u is None or u["men"] <= 0 or u["state"] in ("broken", "fled"):
        lf["left"] = 0
        return 0, []
    near = min(hdist(h, lf["lz"]) for row in footprint(d, u) for h in row) <= d.units["heliborne"]["zone"]
    if not near or in_contact(d, us, occupancy(d, us), i):
        return 0, [{"kind": "waveoff", "name": lf["unit"]["name"], "side": u["side"], "lz": lf["lz"], "why": "contact" if near else "far"}]
    n = min(u["men"], can * H["carry"])
    u.update(men=u["men"] - n, flown=u.get("flown", 0) + n)
    lf["left"] = u["men"]
    if not u["men"]:
        u.pop("boarding", None)
    return -(-n // H["carry"]), [{"kind": "flownout", "unit": i, "name": lf["unit"]["name"], "side": u["side"], "lz": lf["lz"], "men": n, "all": not u["men"]}]


def _helo_hits(d: Data, rf: tuple, H: dict, nhl: tuple) -> list:
    """The helicopters of a lift: at a hot zone each is hit at heliborne.hit %, then downed at
    heliborne.downed % (a wreck near the zone) or else damaged; either is lost for the battle.
    The rest are away for their turnaround. -> log lines for those hit."""
    (rng, field), (n, hot, lf), D = rf, nhl, d.units["heliborne"]
    hit = sum(1 for _ in range(n) if hot and rng.randint(1, 100) <= D["hit"])
    downed = sum(1 for _ in range(hit) if rng.randint(1, 100) <= D["downed"])
    H["damaged"] = H.get("damaged", 0) + hit - downed
    H["downed"] = H.get("downed", 0) + downed
    H.setdefault("away", []).extend([H["turnaround"]] * (n - hit))
    for _ in range(downed):
        _wreck_near(d, field, lf["lz"])
    return [{"kind": "helohit", "side": H["side"], "lz": list(lf["lz"]), "hit": hit, "downed": downed}] if hit else []


def _wreck_near(d: Data, field: dict, lz) -> None:
    """A downed helicopter's wreck on the nearest hex to the zone (within heliborne.zone) with no work on it."""
    if not field.get("works"):
        field["works"] = {"edges": {}, "hexes": {}}
    hexes = field["works"].setdefault("hexes", {})
    for h in within(lz, d.units["heliborne"]["zone"]):
        if f"{h[0]},{h[1]}" not in hexes:
            hexes[f"{h[0]},{h[1]}"] = {"type": "wreck", "progress": 0}
            return


def _land(d: Data, us: list, ctx: tuple, lf: dict, n: int) -> tuple:
    """n of a lift's men landing at its zone, if they fit. -> (men landed, log)."""
    table, rng, field = ctx
    side, name = lf["unit"]["side"], lf["unit"]["name"]
    state = lz_state(d, us, field, side, lf["lz"])
    i = next((k for k, u in enumerate(us) if u.get("id") is not None and u.get("id") == lf["unit"].get("id")), len(us))
    u = dict(us[i]) if i < len(us) else {**lf["unit"], "pos": list(lf["lz"]), "men": 0, "start": 0, "down": 0, "dead": 0, "hurt": {}, "heroes": [], "state": "steady"}
    u.update(men=u["men"] + n, start=u["start"] + n)
    spots = [u["pos"]] if i < len(us) else within(lf["lz"], d.units["heliborne"]["zone"])
    u["pos"] = next((list(h) for h in spots if _fits(d, us, i, {**u, "pos": list(h)}, _size(d, field), field)), None)
    if u["pos"] is None:
        return 0, [{"kind": "waveoff", "name": name, "side": side, "lz": lf["lz"], "why": "room"}]
    if i < len(us):
        us[i].update(men=u["men"], start=u["start"])
    else:
        us.append(u)
    lf["left"] -= n
    line = {"kind": "landed", "unit": i, "dfd": i, "name": name, "side": side, "lz": lf["lz"], "men": n, "hot": state == "hot", "first": u["start"] == n}
    if state != "hot":
        return n, [line]
    return n, _hot_landing(d, us[i], (table, rng), n, line)


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


_FIRE = {"volley", "beaten", "shelled", "tankfire", "antiarmour", "rocketfire", "cannon", "ricochet"}


def _fired_on(log: list) -> set:
    """The units fired on in an exchange's log: missiles, guns, shells and rockets, not hand to
    hand."""
    return {l["dfd"] for l in log if l.get("dfd") is not None and (l.get("kind") in _FIRE or (l.get("kind") == "hero" and "dist" in l))}


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


def ammo_full(d: Data, u: dict) -> int | None:
    """A unit's full load in exchanges of fire (ammunition.loads / (missile.rate * burn), rounded,
    at least 1), or None if it does not count ammunition: no missile weapon or no load for it,
    a vehicle, a battery or anti-tank guns (they count their own rounds)."""
    A = d.units.get("ammunition") or {}
    load = (A.get("loads") or {}).get(u["weapon"])
    if not load or u.get("vehicle") or "range" not in d.weapons[u["weapon"]] or is_battery(d, u) or is_at_gun(d, u):
        return None
    S = d.units["missile"]
    return max(1, math.floor(load / (S["rate"].get(u["weapon"], S["default_rate"]) * A["burn"]) + 0.5))


def fire_left(d: Data, u: dict) -> int | None:
    """Exchanges of fire it has left (its full load unless it has spent some: u.ammo), or None."""
    full = ammo_full(d, u)
    return None if full is None else min(full, u.get("ammo", full))


def ammo_state(d: Data, u: dict) -> str | None:
    """full, low (at or under ammunition.low of a full load) or out; None if it does not count."""
    full, left = ammo_full(d, u), fire_left(d, u)
    if full is None:
        return None
    if left <= 0:
        return "out"
    return "low" if left <= full * d.units["ammunition"]["low"] else "full"


def _spend(d: Data, us: list, v: dict) -> None:
    """A volley fired: its shooters (the vehicle's riders for a riders' volley) use an exchange of fire."""
    u = us[v["att"]]
    who = u["riders"] if v.get("riders") else u
    left = fire_left(d, who)
    if left is not None:
        who["ammo"] = max(0, left - 1)


def supply_edge(d: Data, us: list, side) -> str | None:
    """The map edge its supplies come from: behind the way most of the side's standing men face
    (N, S, E or W), or None if it has none."""
    n = [0] * 6
    for u in us:
        if u["side"] == side and u["men"] > 0 and u["state"] != "fled":
            n[u["facing"] % 6] += u["men"]
    return None if max(n) == 0 else EDGE_BEHIND[n.index(max(n))]


EDGE_BEHIND = ("W", "S", "E", "E", "N", "W")   # the map edge behind units facing 0-5


def supply_near(d: Data, us: list, i: int, field: dict | None) -> str | None:
    """What it can draw ammunition from within ammunition.reach hexes: edge (its side's supply
    edge), vehicle (a steady supply vehicle of its side) or dump (a supply dump), or None."""
    A, u = d.units["ammunition"], us[i]
    reach, hexes = A["reach"], [h for row in footprint(d, u) for h in row]
    edge = supply_edge(d, us, u["side"])
    if edge is not None and min(_edge_gap(edge, h, _size(d, field)) for h in hexes) < reach:
        return "edge"
    for j, e in enumerate(us):
        if j != i and e["side"] == u["side"] and e["state"] == "steady" and e["men"] > 0 and e.get("vehicle") in A["vehicles"] \
                and min(hdist(h, x) for h in hexes for row in footprint(d, e) for x in row) <= reach:
            return "vehicle"
    if any(m.get("side") == u["side"] and min(hdist(h, m["at"]) for h in hexes) <= reach for m in (field or {}).get("dumps") or []):
        return "dump"
    return None


def _air_drops(d: Data, field: dict | None, rng) -> list:
    """End of the exchange: each supply drop called (field drops: {at, side}) lands as a dump,
    a d6 direction and 0 to ammunition.air_drop.scatter hexes off where it was aimed (kept on
    the map). -> [drop log lines]."""
    drops = (field or {}).pop("drops", None) or []
    out, (cols, rows) = [], _size(d, field)
    for m in drops:
        dirn, n = rng.randint(1, 6) - 1, rng.randint(0, d.units["ammunition"]["air_drop"]["scatter"])
        h = step(m["at"], dirn, n)
        at = [min(max(h[0], 0), cols - 1), min(max(h[1], 0), rows - 1)]
        field.setdefault("dumps", []).append({"at": at, "side": m["side"]})
        out.append({"kind": "drop", "side": m["side"], "aim": list(m["at"]), "at": at})
    return out


def _edge_gap(edge: str, h, size: tuple) -> int:
    """How many hexes lie between hex h and map edge N, S, E or W (0 on the edge)."""
    cols, rows = size
    return {"N": h[1], "S": rows - 1 - h[1], "W": h[0], "E": cols - 1 - h[0]}[edge]


def _shoot_all(d: Data, us: list, table: str, rng, acc: tuple, field: dict | None = None, under: list | None = None) -> list:
    """Every volley, each unit's shooting heroes with it. under: marks the units a machine gun
    fired on (suppression)."""
    log = []
    for v in volleys(d, us, field):
        _mark_mg(d, us, v, under)
        _spend(d, us, v)
        b = us[v["dfd"]]
        opts = {"factor": form(d, b)["missile_factor"] * (100 - v["misfire"]) / 100 * v["seen"], "exposed": _exposure(d, b, False, True),
                "penalty": v["cover"] + v["penalty"] + v["over"], "reach": v["reach"]}
        if b.get("vehicle"):
            log += _armour_volley(d, us, (table, rng, acc), v, opts)
            continue
        if hurts_armour(d, _shooter(us, v)["weapon"]):
            log += _rocket_volley(d, us, (table, rng, acc), (field, under), v)
            continue
        t = _take_hurt(b, volley(d, _shooter_side(d, _shooter(us, v), table), _side(b, table), v["men"], v["dist"], rng, **opts))
        _tally(*acc, v, t)
        log += _logged({"kind": "volley", **v}, t)
        if v.get("behind") is not None:
            log += _beaten_fire(d, us, table, rng, acc, v)
        if not v.get("riders"):
            log += _hero_shots(d, us, (table, rng, acc), field, v, opts)
    for c in cannonades(d, us, field):
        log += _fire_battery(d, us, table, rng, acc, c)
    return log + _vehicle_guns(d, us, (table, rng, acc), field, under)


def _hero_shots(d: Data, us: list, ctx: tuple, field: dict | None, v: dict, opts: dict) -> list:
    """The shooting unit's heroes with missile weapons fire with its volley v."""
    (table, rng, acc), b, log = ctx, us[v["dfd"]], []
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
    return log


def _aim_at(d: Data, att: dict, A: dict, band: dict, penalty: int) -> int:
    """The % an anti-armour round hits: a guided missile's fixed `hit` %, else the shooter's
    attack less the range band; less cover and the rest either way."""
    return (A["hit"] if A.get("hit") is not None else _attack(d, att) - band["penalty"]) - penalty


def _rocket_volley(d: Data, us: list, ctx: tuple, env: tuple, v: dict) -> list:
    """Rockets and recoilless rounds at men: each aimed at the target's hex (the window, not a man
    seen) that hits bursts there as the indirect kind `rocket`."""
    (table, rng, acc), (field, under) = ctx, env
    att = _shooter_side(d, _shooter(us, v), table)
    band = field_range(d, att["weapon"], v["dist"], v["reach"])
    if band is None:
        return []
    A = _shot_at_vehicle(d, att["weapon"])
    n = _count(v["men"] * A["rate"] * (100 - v["misfire"]) / 100, rng)
    atk = _aim_at(d, att, A, band, v["penalty"])
    hits = sum(1 for _ in range(n) if rng.randint(1, 100) <= atk)
    log = [{"kind": "rocketfire", "att": v["att"], "dfd": v["dfd"], "dist": v["dist"], "shots": n, "hit": hits, "at": list(v["to"])}]
    weapon = shell_weapon(d, table)
    if hits and weapon and field:
        marks = under if under is not None else [False] * len(us)
        log += _shell_units(d, us, (table, weapon), rng, acc, field, marks, None, {"kind": "rocket", "name": us[v["att"]].get("name"), "spec": d.units["indirect"]["rocket"]}, [list(v["to"])] * hits)
    return log


def _armour_volley(d: Data, us: list, ctx: tuple, v: dict, opts: dict) -> list:
    """Anti-armour weapons (and small arms at soft-skinned vehicles) at a vehicle unit: each
    aimed shot that hits (as at men) knocks a vehicle out at its armour's row % (`rpg`, `atgm`,
    or `small`); a small-arms hit that does not does no other harm."""
    table, rng, acc = ctx
    att = _shooter_side(d, _shooter(us, v), table)
    band = field_range(d, att["weapon"], v["dist"], opts["reach"])
    if band is None:
        return []
    A = _shot_at_vehicle(d, att["weapon"])
    n = _count(v["men"] * A["rate"] * opts["factor"], rng)
    atk = _aim_at(d, att, A, band, opts["penalty"])
    hits = sum(1 for _ in range(n) if rng.randint(1, 100) <= atk)
    p = kill_chance(d, us[v["dfd"]], A["row"], v["from"], v["to"]) if A["row"] in armour_of(d, us[v["dfd"]]) else 0
    kills = sum(1 for _ in range(hits) if p and rng.randint(1, 100) <= p)
    k = knock_out(d, us, v["dfd"], kills, (table, rng), acc)
    harm = _harm(d, us[v["dfd"]], 0 if A["row"] == "small" else hits - k["knocked"], acc[0][v["dfd"]], rng)
    shot = _riders_shot(d, us[v["dfd"]], hits - k["knocked"], att, (table, rng)) if A["row"] == "small" else {}
    acc[2][v["att"]] += k["crew"]
    line = {"kind": "antiarmour", **v, "shots": n, "hit": hits, "knocked": k["knocked"], "crew": k["crew"], "struck": k["struck"], "kill": p, **_harm_line(harm), **_riders_line(k), **shot}
    return _logged(line, k["tally"])


def _harm_line(harm: dict) -> dict:
    """The log's immobilised, gun and turret-hit counts, when there are any."""
    return {k: v for k, v in (("immobilised", harm["immobilised"]), ("gun_out", harm["gun"]), ("turret", harm["turret"])) if v}


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


def _riders_shot(d: Data, u: dict, n: int, att: dict, tr: tuple) -> dict:
    """Small-arms hits on a soft-skinned carrier that knocked none out: each strikes one of its
    riders (up to as many as ride), wounded by the shooter's weapon (taken off the riders at
    once). -> the log's rshot, rshotdown and rshotdead, or {}."""
    R = u.get("riders")
    if not R or R["men"] <= 0 or n <= 0:
        return {}
    table, rng = tr
    struck = min(n, R["men"])
    t = _take_hurt(R, _blows(d, {"table": table, "weapon": att["weapon"], "kit": None, "quality": "regular"}, _side(R, table), struck, d.units["indirect"]["attack"], 0, rng, (), -1000))
    down = min(t["down"], R["men"])
    R.update(men=R["men"] - down, down=R.get("down", 0) + down, dead=R.get("dead", 0) + min(t["dead"], down))
    return {"rshot": struck, "rshotdown": down, "rshotdead": min(t["dead"], down)}


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
        gun = _gun_of(d, u)
        if gun and not _out(u):
            log += _main_gun(d, us, i, gun, (ctx, field, under))
    return log


def _gun_of(d: Data, u: dict) -> dict | None:
    """A unit's main gun: a vehicle kind's, or an anti-tank gun unit's (anti_tank_guns.gun;
    none while it resupplies)."""
    if is_at_gun(d, u):
        return None if u.get("resupplying") or u.get("unhooked") else d.units["anti_tank_guns"]["gun"]
    kind = vehicle_kind(d, u)
    if not kind or not kind.get("gun"):
        return None
    F = d.units["vehicles"]["fire_control"].get(u["fc"]) if u.get("fc") else None
    return {**kind["gun"], "range": F["range"], "hit": F["hit"]} if F else kind["gun"]   # a tank's gun hits and reaches by its fire control


def _guns_firing(d: Data, u: dict) -> int:
    """How many main guns a unit fires: its vehicles whose guns work, or its anti-tank guns served."""
    return at_guns(d, u) if is_at_gun(d, u) else max(0, vehicles_left(d, u) - u.get("gunless", 0))


def at_rounds(d: Data, u: dict) -> int:
    """Rounds an anti-tank gun unit has left: anti_tank_guns.rounds a gun it brought, less those fired."""
    A = d.units["anti_tank_guns"]
    return max(0, math.ceil(u.get("start", u["men"]) / A["crew"]) * A["rounds"] - u.get("spent", 0))


def _main_gun(d: Data, us: list, i: int, gun: dict, env: tuple) -> list:
    """Vehicle unit i's main gun this exchange (env: (table, dice, tallies), field, under fire):
    at its gun target, if it has one and guns that still work."""
    ctx, field, under = env
    table, rng, acc = ctx
    u, best = us[i], _gun_target(d, us, i, field, gun)
    if best is None:
        return []
    dist, j, h, t = best
    rounds = _guns_firing(d, u) * gun["rate"]
    if is_at_gun(d, u):
        rounds = min(rounds, at_rounds(d, u))
        u["spent"] = u.get("spent", 0) + rounds
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
    if under is None or not is_mg(d, _shooter(us, v)["weapon"]):
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
    hits = volley(d, _shooter_side(d, us[v["att"]], table), _side(bh, table), r["men"], r["dist"], rng, **opts)
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
    vis = _thermal_sight(d, d.weather["conditions"][cond], d.weather["conditions"][cond].get("visibility"), seer) if cond and d.weather else None
    L = light_of(d, field)
    dark = dark_sight(d, L, night_device(d, seer, field))[0] if L and not lit(field, h) else None
    if dark is not None and flashing(field, h):
        dark = max(dark, d.weather["light"]["flash"])
    if dark is not None and beaming(field, h) and sees_beam(d, seer, field):
        dark = max(dark, d.weather["light"]["night_vision"]["beam"])
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
        if clear_sight(d, field, x, h, dist) and (not smoked_line(field, x, h, dist) or sees_smoke(d, _seer(u))):
            return True
    return False


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
    us, rng, field = ctx[0], ctx[3], ctx[5]
    (k, b, shells), (air, fac) = fire, flight
    K = d.units["indirect"]["kinds"][b["kind"]]
    marked = air and not fac and C.hkey(b["mission"]["hex"]) in ((field or {}).get("smoke") or {})
    scatter = K["scatter"] // d.units["indirect"]["air"]["fac"]["scatter"] if fac or marked else K["scatter"]
    run = b["mission"].get("attack") if air else None
    log = _runs(d, ctx, k, b, shells, scatter) if run in (d.units["indirect"]["air"].get("runs") or {}) else _bombard(d, ctx, k, b, shells, scatter)
    if fac:
        log[0]["fac"] = True
    if marked:
        log[0]["marked"] = True
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
    """% an aircraft attacking hex h is hit: the enemy's machine guns, rockets and rifles within
    indirect.air.ground_fire.reach of it, times the kind's exposed, at most cap; then its
    anti-aircraft guns within aa_reach, `aa` % a gun served times exposed, the whole at most aa_cap."""
    G, K = d.units["indirect"]["air"]["ground_fire"], d.units["indirect"]["kinds"][b["kind"]]
    chance, flak = 0.0, 0.0
    for u in us:
        w = u["weapon"]
        aa = w in G.get("aa_weapons", [])
        reach = G["aa_reach"] if aa else G["reach"]
        if u["side"] == b["side"] or _out(u) or u.get("vehicle") or not any(hdist(x, h) <= reach for row in footprint(d, u) for x in row):
            continue
        if aa:
            flak += G["aa"] * mg_guns(d, u)
        elif is_mg(d, w):
            chance += G["mg"] * mg_guns(d, u)
        elif w in G["rockets"]:
            chance += G["rocket"]
        elif "range" in d.weapons[w] and not is_gun(d, w) and w not in d.units["line_of_fire"]["arcing"]:
            chance += G["rifles"] * u["men"] / 100
    return min(G["aa_cap"], min(G["cap"], chance * K.get("exposed", 1)) + flak * K.get("exposed", 1))


def _ground_fire(d: Data, us: list, flight: tuple, attacking: int, rng) -> list:
    """Ground fire at the aircraft that attacked (flight: support index, battery): each is lost
    at _flak %; a lost one takes its share of the remaining attacks. -> a log line, or none."""
    k, b = flight
    chance = _flak(d, us, b, b["mission"]["hex"])
    if chance <= 0 or b["tubes"] <= 0:
        return []
    hit = min(b["tubes"], sum(1 for _ in range(attacking) if rng.randint(1, 100) <= chance))
    if not hit:
        return []
    downed = sum(1 for _ in range(hit) if rng.randint(1, 100) <= d.units["indirect"]["air"]["ground_fire"]["downed"])
    share = b["rounds"] // b["tubes"]
    b["tubes"] -= hit
    b["rounds"] = max(0, b["rounds"] - share * hit)
    return [{"kind": "airloss", "sup": k, "name": b["name"], "side": b["side"], "lost": downed, "damaged": hit - downed, "left": b["tubes"]}]


def _bombard(d: Data, ctx: tuple, k: int, b: dict, shells: int, scatter: int | None = None) -> list:
    """A battery's shells on a hex (ctx: units, table, shell weapon, dice, tallies, field, under
    fire): where each lands (0 to scatter hexes off; the kind's, unless given), then smoke laid,
    or the men struck and bunkers knocked."""
    us, table, weapon, rng, acc, field, under = ctx
    K, m, bursts = d.units["indirect"]["kinds"][b["kind"]], b["mission"], []
    scatter = (K["scatter"] if scatter is None else scatter) + (d.units["indirect"]["planned"]["scatter"] if m.get("planned") else 0)   # planned fire: on the place, not an observer's correction
    for _ in range(shells):
        dirn, far = rng.randint(0, 5), rng.randint(0, scatter)
        bursts.append(step(m["hex"], dirn, far))
    log = [{"kind": "barrage", "sup": k, "name": b["name"], "side": b["side"], "shells": shells, "at": m["hex"], "bursts": bursts,
            "smoke": bool(m.get("smoke"))}]
    if m.get("smoke"):
        _lay_smoke(d, field, bursts)
    else:
        log += _shell_units(d, us, (table, weapon), rng, acc, field, under, k, b, bursts)
        log += _shell_parties(d, us, field, bursts, K, {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}, rng)
        log += _knock_bunkers(d, field, k, b, bursts, rng)
    return log


def run_line(d: Data, at, dirn: int, mode: str) -> list:
    """The hexes of an attack run (indirect.air.runs[mode]): `length` hexes through at, along dirn."""
    n = d.units["indirect"]["air"]["runs"][mode]["length"]
    return [step(at, dirn, o) for o in range(-((n - 1) // 2), n // 2 + 1)]


def _runs(d: Data, ctx: tuple, k: int, b: dict, passes: int, scatter: int) -> list:
    """Aircraft's strafing runs or napalm strips (the mission's `attack`, along its `dir`): each
    pass's line scatters as a burst does, then the men and vehicles on every line are struck."""
    us, table, weapon, rng, acc, field, under = ctx
    m = b["mission"]
    R, lines = d.units["indirect"]["air"]["runs"][m["attack"]], []
    for _ in range(passes):
        dirn, far = rng.randint(0, 5), rng.randint(0, scatter)
        lines.append(run_line(d, step(m["hex"], dirn, far), m.get("dir", 0), m["attack"]))
    hexes = [h for line in lines for h in line]
    log = [{"kind": "barrage", "sup": k, "name": b["name"], "side": b["side"], "shells": passes, "at": m["hex"], "bursts": hexes, "smoke": False, "run": m["attack"]}]
    K = {**d.units["indirect"]["kinds"][b["kind"]], "knock": R["knock"]}
    for i, u in enumerate(us):
        if u.get("vehicle"):
            log += _shell_vehicle(d, us, i, hexes, K, (table, rng), acc, (k, b))
            continue
        log += _run_struck(d, (us, i, field, under), (k, b, m["attack"], hexes), (table, weapon), (rng, acc))
    return log


def _run_struck(d: Data, where: tuple, fire: tuple, tw: tuple, ra: tuple) -> list:
    """Unit i's men on the run's hexes: each struck at the run's `struck` % (strafing: times the
    shellfire cut for its hex). Strafing wounds as the table's machine gun, else shell fragments;
    napalm puts them down with critical burns, `dead` % killed."""
    (us, i, field, under), (k, b, mode, hexes), (table, weapon), (rng, acc) = where, fire, tw, ra
    u, R = us[i], d.units["indirect"]["air"]["runs"][mode]
    if u["men"] <= 0 or u["state"] == "fled":
        return []
    keys = [C.hkey(h) for h in hexes]
    struck, near = 0, False
    for h, n in zip((h for row in footprint(d, u) for h in row), men_by_hex(d, u)):
        times = keys.count(C.hkey(h))
        if not times:
            continue
        near = True
        p = R["struck"] * (_shell_cut(d, field, h, low(u)) if mode == "strafe" else 1)
        struck += sum(1 for _ in range(times * n) if rng.randint(1, 100) <= p)
    if not near:
        return []
    under[i] = True
    if not struck:
        return []
    if mode == "napalm":
        t = _burns(struck, R["dead"], rng)
    else:
        gun = "machine_gun" if "machine_gun" in (d.tables.get(table) or {}).get("weapons", []) else weapon
        t = _blows(d, {"table": table, "weapon": gun, "kit": None, "quality": "regular"}, _side(u, table), struck, d.units["indirect"]["attack"], 0, rng,
                   _exposure(d, u, False, True), -1000)
    t = _take_hurt(u, t)
    acc[0][i] += t["down"]
    acc[1][i] += t["dead"]
    return _logged({"kind": "shelled", "sup": k, "name": b["name"], "dfd": i, "struck": struck, "run": mode}, t)


def _burns(struck: int, dead: int, rng) -> dict:
    """Men reached by flame: each down with critical burns, `dead` % of them killed outright."""
    t = _new_tally()
    t.update(blows=struck, hits=struck, critical=struck, down=struck)
    for _ in range(struck):
        if rng.randint(1, 100) <= dead:
            t["dead"] += 1
        else:
            _hurt(t, "critical", {"lethal": "days", "infection": "high"}, True)
    return t


def _knock_bunkers(d: Data, field: dict, k: int, b: dict, bursts: list, rng) -> list:
    """Each shell bursting on an intact bunker's hex knocks it out at the kind's `knock` %, and
    opens each intact work that shells open (`shelled`: a stone wall) on that hex's sides at the
    same %."""
    knock, log = d.units["indirect"]["kinds"][b["kind"]].get("knock", 0), []
    if not knock:
        return log
    works = _works(field)
    for at in bursts:
        it = bunker_at(d, field, at)
        if it and rng.randint(1, 100) <= knock:
            it["out"] = True
            log.append({"kind": "knocked", "sup": k, "name": b["name"], "side": b["side"], "at": at})
        for dirn in range(6):
            for w in C._edge_items(d, works, at, step(at, dirn)):
                if C._spec(d, "edge", w).get("shelled") and rng.randint(1, 100) <= knock:
                    w["out"] = True
                    log.append({"kind": "knocked", "sup": k, "name": b["name"], "side": b["side"], "at": at, "work": w["type"]})
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
    `near_struck`. The struck crewmen roll wounds; those put down are lost to the battery
    (crew_down, crew_dead), their wounds kept on it (hurt) as on a unit."""
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
    tg["crew_down"] = tg.get("crew_down", 0) + t["down"]
    tg["crew_dead"] = tg.get("crew_dead", 0) + t["dead"]
    tg.setdefault("hurt", {})
    t = _take_hurt(tg, t)                       # the crews' wounds, kept by kind for the after-battle reckoning
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
    K, log = b.get("spec") or I["kinds"][b["kind"]], []   # spec: a burst that is no battery's (rockets at men)
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
    log = []
    if direct and p > 0:
        rng = tr[1]
        kills = sum(1 for _ in range(direct) if rng.randint(1, 100) <= p)
        k = knock_out(d, us, i, kills, tr, acc)
        if k["knocked"]:
            log = _logged({"kind": "knocked_out", "sup": src[0], "name": src[1]["name"], "dfd": i, "knocked": k["knocked"], "crew": k["crew"], "struck": k["struck"], **_riders_line(k)}, k["tally"])
    return log + _hull_shelled(d, us, i, bursts, kind, tr, src)


def _hull_shelled(d: Data, us: list, i: int, bursts: list, kind: dict, tr: tuple, src: tuple) -> list:
    """Men riding on vehicle unit i's hulls (exposed), spread over its hexes (the first hexes one
    more), struck by the bursts as men in the open (the kind's struck % by distance, no cover),
    at most all of them, and wounded as by shellfire. -> a `hullshelled` log line, or []."""
    u = us[i]
    if not exposed(d, u):
        return []
    R, (table, rng) = u["riders"], tr
    hexes = [h for row in footprint(d, u) for h in row]
    base, extra = divmod(R["men"], len(hexes))
    men, struck, near = [base + (1 if j < extra else 0) for j in range(len(hexes))], 0, False
    for at in bursts:
        for h, n in zip(hexes, men):
            dist = hdist(h, at)
            if dist <= kind["radius"]:
                near = True
                struck += sum(1 for _ in range(n) if rng.randint(1, 100) <= kind["struck"][dist])
    struck = min(struck, R["men"])
    weapon = shell_weapon(d, table)
    if not near or not struck or not weapon:
        return []
    t = _take_hurt(R, _blows(d, {"table": table, "weapon": weapon, "kit": None, "quality": "regular"}, _side(R, table), struck, d.units["indirect"]["attack"], 0, rng, (), -1000))
    down = min(t["down"], R["men"])
    R.update(men=R["men"] - down, down=R.get("down", 0) + down, dead=R.get("dead", 0) + min(t["dead"], down))
    return [{"kind": "hullshelled", "sup": src[0], "name": src[1]["name"], "dfd": i, "struck": struck, "down": down, "dead": min(t["dead"], down)}]


def _shell_struck_unit(d: Data, field: dict, u: dict, bursts: list, kind: dict, rng) -> int | None:
    """Men of unit u struck by these bursts: each man in a hex within a burst's radius at the %
    for his distance (gone to ground, less; ground cover, less). None if no burst came near.
    Quick-play (quick.blows): the sum of those chances is the average, rolled once."""
    if u["men"] <= 0 or u["state"] == "fled":
        return None
    hexes = [h for row in footprint(d, u) for h in row]
    men, cuts, rooms = men_by_hex(d, u), [_shell_cut(d, field, h, low(u)) for h in hexes], [_in_room(d, field, h) for h in hexes]
    reached = [(n, p) for at in bursts for h, n, cut, room in zip(hexes, men, cuts, rooms) if (p := _burst_pct(kind, hdist(h, at), cut, room)) is not None]
    if not reached:
        return None
    if (d.units.get("quick") or {}).get("blows"):
        return _quick_struck(d, reached, rng)
    return sum(1 for n, p in reached for _ in range(n) if rng.randint(1, 100) <= p)


def _quick_struck(d: Data, reached: list, rng) -> int:
    """Quick-play shellfire: (men, struck %) for each hex each burst reached; one d100 on the curve."""
    tries, mean = 0, 0.0
    for n, p in reached:
        tries += n
        mean += n * min(100, max(0, math.floor(p))) / 100
    return _quick_down(d, tries, mean / tries if tries > 0 else 0, rng)


def _burst_pct(kind: dict, dist: int, cut: float, room: bool = False):
    """A man's struck % this far from a burst (times the hex's cut), or None beyond its radius.
    Direct-fire HE bursting in a building hex (room): the kind's `room` %, with no cut."""
    if dist > kind["radius"]:
        return None
    return kind["room"] if kind.get("room") and dist == 0 and room else kind["struck"][dist] * cut


def _in_room(d: Data, field: dict | None, h) -> bool:
    """A building hex: direct-fire HE bursts in its rooms (indirect.room_ground)."""
    ground = ((field or {}).get("ground") or {}).get(f"{h[0]},{h[1]}", "open")
    return ground in (d.units["indirect"].get("room_ground") or [])


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
        t = _burns(struck, d.units["assault"]["flame_dead"], rng)
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
        target = quality(d, u["quality"])["nerve"] + (S["prone"] if low(u) else 0)
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
    """(edge or hex, its key, the item): the first work hex h's front rank can hack at, or blow
    open with demolition charges (`charge`, on a table with the blast weapon: field["blast"])."""
    works = _works(field)
    for dirn in (u["facing"], u["facing"] + 1):
        x = step(h, dirn)
        for it in C._edge_items(d, works, h, x):
            if _can_open(d, field, "edge", it):
                return "edge", C.edge_key(h, x), it
        it = C._hex_item(d, works, x)
        if it and _can_open(d, field, "hex", it):
            return "hex", C.hkey(x), it
    return None


def _can_open(d: Data, field: dict, kind: str, it: dict) -> bool:
    """Men can open this work: by hand (`breach`), or with charges (`charge`) where the table has them."""
    s = C._spec(d, kind, it)
    return bool(s.get("breach") or (s.get("charge") and field.get("blast")))


def _copy_unit(u: dict) -> dict:
    return dict(u, hurt=dict(u.get("hurt", {})),
                heroes=[dict(h, wounds=list(h.get("wounds", [])), **({"held": dict(h["held"])} if h.get("held") else {}),
                             **({"going": dict(h["going"])} if h.get("going") else {})) for h in u.get("heroes", [])])


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


def _vehicle_losses(d: Data, u: dict, before: int, lost: int) -> tuple:
    """(down, lost this exchange) for its morale: a vehicle unit's in whole vehicles gone (their
    crews), not crewmen hit in vehicles still fighting."""
    kind = vehicle_kind(d, u)
    if not kind:
        return u["down"], lost
    crew = kind["crew"]
    start_v, was_v, now_v = -(-u["start"] // crew), -(-before // crew), vehicles_left(d, u)
    return (start_v - now_v) * crew, max(0, was_v - now_v) * crew


def cover_lying(d: Data, field: dict | None, u: dict) -> bool:
    """Gone to ground in ground that gives cover (morale.posture_cover)."""
    if not d.units["morale"].get("posture_cover") or not u.get("prone") or not field:
        return False
    return any(ground_at(d, field, x).get("cover", 0) > 0 for row in footprint(d, u) for x in row)


def holds_position(d: Data, us: list, i: int, field: dict | None) -> bool:
    """Unit i holds a position: in a bunker, gone to ground in cover (morale.posture_cover), or
    holding works toward the nearest standing enemy (dug in, emplaced, the works' cover, ground
    that hides men)."""
    u = us[i]
    if in_bunker(d, field, u) or cover_lying(d, field, u):
        return True
    at, best = None, math.inf
    for e in us:
        if e["side"] != u["side"] and e["men"] > 0 and e["state"] not in ("broken", "fled"):
            dd = hdist(e["pos"], u["pos"])
            if dd < best:
                at, best = e["pos"], dd
    return holds_works(d, field, at or u["pos"], u)


def _morale_all(d: Data, us: list, occ: dict, before: list, acc: tuple, rng, table: str = "", field: dict | None = None) -> list:
    """Every unit still in the fight checks; any that breaks is struck at once by the enemies
    touching it, every man of them."""
    (lost, dealt, flanked, hand), log, broke = acc, [], []
    M = d.units["morale"]
    for i, u in enumerate(us):
        if u["state"] in ("broken", "fled") or u["men"] <= 0:
            continue
        near = _adjacent_units(d, us, occ, i)
        down, lost_now = _vehicle_losses(d, u, before[i], lost[i])
        unit = {"quality": u["quality"], "start": u["start"], "down": down, "lost": lost_now, "dealt": dealt[i],
                "men": before[i], "state": u["state"], "leader": leader_state(u), "flanked": flanked[i],
                "contact": any(us[j]["side"] != u["side"] for j in near),
                "friends": any(us[j]["side"] == u["side"] and us[j]["state"] == "steady" for j in near),
                "dug": low(u) or in_bunker(d, field, u), "no_ammo": ammo_state(d, u) == "out",
                "holds": bool(M.get("posture")) and bool(u.get("holding")) and holds_position(d, us, i, field),
                "hand_lost": hand[0][i], "hand_dealt": hand[1][i]}
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
    if (u.get("boarding") or (u.get("resupplying") and (is_at_gun(d, u) or ammo_full(d, u)))) and u["state"] not in ("broken", "fled"):
        return 0
    if is_battery(d, u) and not u.get("abandoned") and u["state"] != "broken":   # crews running from their guns run on foot
        if u.get("limbering") or u.get("resupplying"):
            return 0
        if not u.get("limbered"):
            return _jostled(d, u, _carrying(d, u, d.units["artillery"]["pushed"]))
    return _jostled(d, u, _carrying(d, u, d.units["mounted_move"] if u.get("mounted") else form(d, u)["move"]))


def _jostled(d: Data, u: dict, move: int) -> int:
    """A move cut by rout.jostle (rounded down) for a unit a broken friend ran through this
    exchange (a broken unit itself runs at full speed)."""
    if u.get("jostled") and u["state"] not in ("broken", "fled"):
        return math.floor(move * (1 - d.units["rout"]["jostle"]))
    return move


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


def has_ladders(u: dict) -> bool:
    """A unit on foot marked with ladders (escalade)."""
    return bool(u.get("ladders")) and not u.get("mounted") and not u.get("vehicle")


def _wall_between(d: Data, field: dict, a, b) -> bool:
    """A palisade, wall or barred gate between hexes a and b (open gates are left out)."""
    for it in C._edge_items(d, _works(field), a, b):
        s = C._spec(d, "edge", it)
        if s.get("cross") is None or s.get("gate"):
            return True
    return False


_STEPS = []   # while a commander orders its side (steps_remembered): {(id(field), mover, a, b): movement}; nothing it orders changes the works, ground or weather


@contextmanager
def steps_remembered():
    """Remember each step's movement while the commander orders its side (commander.command):
    the works, ground and weather do not change until the exchange, so a step costs the same each
    time a unit's moves are weighed."""
    _STEPS.append({})
    try:
        yield
    finally:
        _STEPS.pop()


def _mover(u: dict) -> str:
    """What a step's movement depends on in the unit: vehicle, horse, ladders or foot."""
    if u.get("vehicle"):
        return "v"
    if u.get("mounted"):
        return "m"
    return "l" if has_ladders(u) else "f"


def step_cost(d: Data, field: dict | None, u: dict, a, b) -> int | None:
    """Movement for one hex of a unit to step from a to b: 1, plus works crossed and entered,
    plus the ground (rough, woods, marsh), plus deep mud or snow. None if it cannot. A unit pays
    the worst of all its hexes' (_front_cost). Remembered while a commander orders its side."""
    if not field:
        return 1
    if not _STEPS:
        return _step_cost(d, field, u, a, b)
    memo, key = _STEPS[-1], (id(field), _mover(u), a[0], a[1], b[0], b[1])
    if key not in memo:
        memo[key] = _step_cost(d, field, u, a, b)
    return memo[key]


def _step_cost(d: Data, field: dict, u: dict, a, b) -> int | None:
    """step_cost, worked out."""
    if not _can_enter(d, field, u, b):
        return None
    c = C.step_cost(d, _works(field), a, b, climb=d.units["escalade"]["cross"] if has_ladders(u) else None)
    if c is None:
        return None
    wx = field.get("weather") or {}
    going = d.units["vehicles"]["ground"][_ground_key(field, b)] if u.get("vehicle") else ground_at(d, field, b)["move"]
    return c + going - 1 + C.deep_going(d, wx.get("ground")) + (cold_of(d, field) or {}).get("move", 0) + (light_of(d, field) or {}).get("move", 0)


def _ground_key(field: dict | None, h) -> str:
    """The ground kind painted on hex h (open if none)."""
    return ((field or {}).get("ground") or {}).get(f"{h[0]},{h[1]}", "open")


def _path_len(d: Data, units: list, i: int, goal, size: tuple, limit: int, field: dict | None = None, through: bool = False) -> int | None:
    """Least movement for the unit's middle hex from where it is to goal (step_cost), not
    through other units' hexes (through: only the enemy's); None if more than limit."""
    occ = occupancy(d, mates(units, i, through))
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
    steps, through = _charge_path(d, units, i, pos, (size, most, field))
    if steps is None:
        return {"ok": False, "why": "too far, or no way through"}
    moved = {**u, "pos": list(pos), "facing": facing % 6}
    if not _fits(d, units, i, moved, size, field):
        return {"ok": False, "why": "no room there"}
    cost = steps + turns * turn_cost(d, u) + (sweep_cost(d, field, {**u, "pos": list(pos)}, moved) if turns else 0)
    after = [moved if k == i else x for k, x in enumerate(units)]
    contact = in_contact(d, after, occupancy(d, after), i)
    if through and not contact:
        return {"ok": False, "why": "it can pass through its own men only to charge"}
    passed = {"through": passed_through(d, units, i, pos)} if through else {}
    if cost <= allowance(d, u):
        return {"ok": True, "cost": cost, "charge": contact and steps > 0, **passed}
    if contact and u["state"] == "steady" and cost <= most:
        return {"ok": True, "cost": cost, "charge": True, **passed}
    return {"ok": False, "why": "too far"}


def _charge_path(d: Data, units: list, i: int, pos, how: tuple) -> tuple:
    """(least movement, passing through friends): round its own side's units, else (a steady
    unit, for a charge) through them."""
    size, most, field = how
    steps = _path_len(d, units, i, pos, size, most, field)
    if steps is not None or units[i]["state"] != "steady":
        return steps, False
    return _path_len(d, units, i, pos, size, most, field, through=True), True


def passed_through(d: Data, units: list, i: int, pos) -> list:
    """The friendly units (not running) a charge from where unit i stands to pos passes
    through: those with a hex on the straight line between (indices, in order)."""
    u = units[i]
    line = {C.hkey(x) for x in ray(list(u["pos"]), list(pos), hdist(u["pos"], pos))}
    return [k for k, x in enumerate(units) if k != i and x["side"] == u["side"] and x["state"] not in ("broken", "fled")
            and any(C.hkey(h) in line for row in footprint(d, x) for h in row)]


def mates(units: list, i: int, through: bool) -> list:
    """The other units whose hexes unit i's middle hex may not pass: all of them, or (through,
    for a charge) only the enemy's."""
    u = units[i]
    return [x for k, x in enumerate(units) if k != i and not (through and x["side"] == u["side"])]


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
    if u.get("emplaced") and goes:
        return "it is emplaced, dug in for the battle (it may turn)"
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
    """Men a vehicle unit can carry: its vehicles left times its kind's `carry`, or `rides`
    (men on the hull), 0 if neither."""
    K = vehicle_kind(d, u)
    return vehicles_left(d, u) * (K.get("carry") or K.get("rides", 0)) if K else 0


def exposed(d: Data, u: dict) -> bool:
    """Men riding on the outside of a vehicle unit (its kind `rides`), whom small arms can hit."""
    K = vehicle_kind(d, u)
    return bool(K and K.get("rides") and (u.get("riders") or {}).get("men", 0) > 0)


def tows(d: Data, u: dict) -> int:
    """Anti-tank guns a vehicle unit can tow: its vehicles left times its kind's `tows` (0 if none)."""
    K = vehicle_kind(d, u)
    return vehicles_left(d, u) * K.get("tows", 0) if K else 0


def _cannot_mount(d: Data, units: list, i: int, j: int) -> str | None:
    """Why foot unit i cannot get aboard vehicle unit j (anti-tank guns: hook up to its
    tractors), or None."""
    u, c, occ = units[i], units[j], occupancy(d, units)
    checks = _tow_checks(d, u, c) if is_at_gun(d, u) else [
        (lambda: u.get("vehicle") or is_gun(d, u["weapon"]) or u.get("mounted"), "only men on foot can ride"),
        (lambda: not c.get("vehicle") or c["side"] != u["side"] or carries(d, c) <= 0, "those are not its side's carriers"),
        (lambda: c.get("riders"), "they carry men already"),
        (lambda: u["men"] > carries(d, c), f"they have room for {carries(d, c)}"),
    ]
    checks += [
        (lambda: _out(u) or _out(c) or in_contact(d, units, occ, i) or in_contact(d, units, occ, j), "one of them is in contact or broken"),
        (lambda: min(hdist(a, b) for r1 in footprint(d, u) for a in r1 for r2 in footprint(d, c) for b in r2) > 1, "they are not beside the carriers"),
    ]
    return next((why for test, why in checks if test()), None)


def _tow_checks(d: Data, u: dict, c: dict) -> list:
    """Anti-tank guns hooking up: to their side's tractors, towing nothing yet, enough of them,
    not emplaced."""
    return [
        (lambda: u.get("emplaced"), "the guns are emplaced"),
        (lambda: not c.get("vehicle") or c["side"] != u["side"] or tows(d, c) <= 0, "those are not its side's gun tractors"),
        (lambda: c.get("riders"), "they tow guns already"),
        (lambda: at_guns(d, u) > tows(d, c), f"they can tow {tows(d, c)}"),
    ]


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
    fled the field (as has one with no men left in it). Running into its own side's units it runs on through them to the first
    free ground beyond (rout.through times its allowance at most), else it stops where it last
    stood clear. Returns the unit."""
    u = dict(units[i])
    if not any(footprint(d, u)):                 # no men left standing in it: it is gone
        return {**u, "state": "fled"}
    back, allow = (u["facing"] + 3) % 6, allowance(d, u)
    # Its own side's other units do not stop it: it may pass through them, but not end on them.
    others = [x for k, x in enumerate(units) if k == i or x["side"] != u["side"]]
    j = next(k for k, x in enumerate(others) if x is units[i])
    clear = u
    for n in range(allow * d.units["rout"]["through"]):
        nxt = {**u, "pos": step(u["pos"], back)}
        if not all(0 <= h[0] < size[0] and 0 <= h[1] < size[1] for row in footprint(d, nxt) for h in row):
            return {**u, "state": "fled"}
        if step_cost(d, field, u, u["pos"], nxt["pos"]) is None or not _fits(d, others, j, nxt, size, field):
            break
        u = nxt
        if _fits(d, units, i, u, size, field):
            clear = u
            if n + 1 >= allow:
                break
    return clear


def ran_through(d: Data, units: list, i: int, after: dict) -> list:
    """The friendly units unit i passed through running straight back from where it stands to
    after (flee): indices, in order."""
    u, out = dict(units[i]), []
    back = (u["facing"] + 3) % 6
    while list(u["pos"]) != list(after["pos"]) and after["state"] != "fled":
        u = {**u, "pos": step(u["pos"], back)}
        hexes = {C.hkey(h) for row in footprint(d, u) for h in row}
        for k, x in enumerate(units):
            if k != i and k not in out and x["side"] == u["side"] and x["state"] not in ("broken", "fled") and hexes & {C.hkey(h) for row in footprint(d, x) for h in row}:
                out.append(k)
    return out


def run_away(d: Data, units: list, i: int, size: tuple, field: dict | None = None) -> list:
    """Units after broken unit i runs (flee), the friends it ran through jostled (rout.jostle:
    their move cut this exchange)."""
    after = flee(d, units, i, size, field)
    hit = set(ran_through(d, units, i, after))
    return [after if k == i else ({**x, "jostled": True} if k in hit else x) for k, x in enumerate(units)]



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


def aftermath(d: Data, units: list, care: list, rng, medevac: list | None = None) -> list:
    """What becomes of each unit's wounded when the battle ends (units.yaml aftermath). care:
    each unit's camp care (none, field, shelter); medevac: each unit's side's medevac kind
    (aftermath.medevac.kinds) or None. Returns, per unit, {left (down men left on a lost field,
    dead), died (of wounds before treatment), cases (survivors on the wound track)}. A man
    wounded twice is counted once: the down are capped at those down and not dead, the walking
    wounded at the men still on their feet."""
    am, d100 = d.units["aftermath"], (lambda: rng.randint(1, 100))
    lost_sides = {u["side"] for u in units} - {u["side"] for u in units if standing(u)}
    ev = medevac or [None] * len(units)
    return [_unit_after(d, u, (care[i], ev[i]), am["left_behind"] and u["side"] in lost_sides, d100) for i, u in enumerate(units)]


def medevac_kind(d: Data, table: str, has_lz: bool, helos_left: bool) -> str | None:
    """A side's medevac in this war (aftermath.medevac.battles by the table's battle), helicopters
    falling back (fallback) without a landing zone or a helicopter left; None if none."""
    M = d.units["aftermath"].get("medevac") or {}
    kind = (M.get("battles") or {}).get((d.tables.get(table) or {}).get("battle"))
    if kind and M["kinds"][kind].get("fallback") and not (has_lz and helos_left):
        kind = M["kinds"][kind]["fallback"]
    return kind


def _unit_after(d: Data, u: dict, ce: tuple, abandon: bool, d100) -> dict:
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
            if _dies(d.units["aftermath"], lethal, ce, d100):
                r["died"] += 1
            else:
                r["cases"].append(wound_case(d, sev, lethal, inf, d100))
    return r


def _dies(am: dict, lethal: str, ce: tuple, d100) -> bool:
    """A wound that kills in minutes or hours: does it, before help comes? ce: (camp care,
    medevac kind or None): the medevac's figures where they are better."""
    care, ev = ce
    K = (am.get("medevac") or {}).get("kinds", {}).get(ev) or {}
    if lethal == "minutes":
        return d100() > max(am["saved"]["minutes"], K.get("minutes", 0))
    if lethal == "hours":
        return d100() > max(am["saved"]["hours"][care], K.get("hours", 0))
    return False


# ---------- guns ----------
# A battery: a unit whose weapon is a gun (units.yaml artillery), its men the crews. It is
# limbered (u["limbered"]: moves, cannot fire) or not; u["limbering"]: changing over this
# exchange (neither moves nor fires); u["abandoned"]: broke and left its guns.

def is_gun(d: Data, weapon: str) -> bool:
    return weapon in d.units.get("artillery", {}).get("guns", [])


def is_battery(d: Data, u: dict) -> bool:
    return is_gun(d, u["weapon"])


def is_at_gun(d: Data, u: dict) -> bool:
    """An anti-tank gun unit (units.yaml anti_tank_guns)."""
    return u["weapon"] in (d.units.get("anti_tank_guns") or {}).get("weapons", [])


def at_guns(d: Data, u: dict) -> int:
    """An anti-tank gun unit's guns still served: one a crew, while a man of the crew is up."""
    return math.ceil(max(0, u["men"]) / d.units["anti_tank_guns"]["crew"])


def melee_weapon(d: Data, u: dict) -> str:
    """The weapon a unit fights hand to hand with: a battery's or an anti-tank gun's crews have their own."""
    if is_battery(d, u):
        return d.units["artillery"]["crew_weapon"]
    return d.units["anti_tank_guns"]["crew_weapon"] if is_at_gun(d, u) else u["weapon"]


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
    vis = _thermal_sight(d, cond, vis, seer)
    if vis is not None and dist * d.units["range_scale"] > vis:
        out["blocked"] = f"{cond['name']}: the guns cannot be laid on what cannot be seen."
        return out
    out["penalty"] = next(x for x in d.weather["winds"] if x["id"] == weather["wind"])["firearm"]
    return in_the_dark(d, field, dist, t, out, seer)


def _thermal_sight(d: Data, cond: dict | None, vis, seer: dict | None):
    """How far a man sees to aim in this weather: a thermal sight further through a sandstorm
    (weather.yaml conditions' thermal, in 2 m hexes)."""
    if vis is not None and (cond or {}).get("thermal") and sees_smoke(d, seer):
        return max(vis, cond["thermal"])
    return vis


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
    the battery; one that cannot fire on its target fires with the rest. Each carries its own
    share of the rounds left, by its guns (rounded down; the rest stay with the battery's
    guns), so a section is not starved when rounds run low."""
    u = units[i]
    guns, ammo, spare, firing = guns_served(d, u), ammo_left(d, u), guns_served(d, u) - 1, []
    for sec in sections(u):
        n = min(sec.get("guns", 0), spare)
        at = _named_target(d, units, i, field, occ, sec.get("target")) if n > 0 else None
        if at is not None:
            firing.append((sec, n, at, ammo * n // guns))
            spare -= n
    main_guns, main_ammo = guns - sum(f[1] for f in firing), ammo - sum(f[3] for f in firing)
    out = [_battery_fire(d, units, (occ, field), i, best, {"guns": main_guns, "ammo": main_ammo, "shot": u.get("shot")})]
    for sec, n, at, share in firing:
        if share > 0:
            out.append(_battery_fire(d, units, (occ, field), i, at, {"guns": n, "ammo": share, "shot": sec.get("shot"), "section": True}))
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


def _unhooked_after(us: list) -> None:
    """End of the exchange: anti-tank guns unhooked this move are in action."""
    for u in us:
        u.pop("unhooked", None)


def _battery_after(d: Data, u: dict) -> None:
    """At the end of an exchange: a battery that was changing over is now limbered or not, one
    that was resupplying has its rounds again, and one that has broken has left its guns."""
    if is_at_gun(d, u) and u.get("resupplying"):
        u["spent"], u["resupplying"] = 0, False
    if u.get("resupplying") and ammo_full(d, u):
        u.pop("ammo", None)
        u["resupplying"] = False
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
