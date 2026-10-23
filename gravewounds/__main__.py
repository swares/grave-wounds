"""Command line: python -m gravewounds roll|list|check|disease|units|team|selfplay"""
from __future__ import annotations

import argparse
import random
import sys

from . import load, DataError
from .engine import roll_hit, describe, table_ranges


def fmt(n: int) -> str:
    return "00" if n == 100 else f"{n:02d}"


def main(argv=None) -> int:
    try:
        return _main(argv)
    except (KeyError, ValueError) as e:
        print("error:", str(e).strip("'\""), file=sys.stderr)
        return 2


def _main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="gravewounds", description="Historical hit-location roller")
    p.add_argument("--data", default="data", help="data folder (default: data)")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("roll", help="roll a hit")
    r.add_argument("--table", required=True)
    r.add_argument("--weapon", required=True)
    r.add_argument("--severity", choices=["light", "serious", "critical"],
                   help="use your system's severity instead of rolling")
    r.add_argument("--seed", type=int)
    r.add_argument("-n", type=int, default=1, help="number of hits")
    r.add_argument("--mod", action="append", default=[], help="situation modifier id (repeatable; they stack)")
    r.add_argument("--called", choices=["head", "torso", "arms", "legs"], help="called shot zone")
    r.add_argument("--blow", choices=["cut", "pierce", "crush"], help="the blow a cut-and-thrust weapon's wielder declares (else rolled)")
    r.add_argument("--armor", help="target armour kit id")
    r.add_argument("--shield", choices=["kit", "yes", "no"],
                   help="does the target carry a shield? 'kit' takes it from --armor; matters on tables that assume one (Visby)")
    r.add_argument("--attack", type=int, help="attack chance %%: roll the attack here; margin of success sets severity")
    r.add_argument("--defence", type=int, help="defender's parry/dodge chance %% (needs --attack)")
    r.add_argument("--att-penalty", type=int, default=0, help="attacker's wound penalty %%")
    r.add_argument("--def-penalty", type=int, default=0, help="defender's wound penalty %%")

    s = sub.add_parser("show", help="print a d100 table")
    s.add_argument("--table", required=True)
    s.add_argument("--weapon")
    s.add_argument("--mod", action="append", default=[], help="situation modifier id (repeatable)")

    sub.add_parser("list", help="list tables and weapons")
    sub.add_parser("check", help="validate the data set")
    ds = sub.add_parser("disease", help="simulate camp disease cases against the records (deaths per case)")
    ds.add_argument("-n", type=int, default=8000, help="cases per disease")
    ds.add_argument("--seed", type=int, default=3)
    us = sub.add_parser("units", help="unit combat: melee pace by armour and example fights")
    us.add_argument("--table", default="towton-1461-all-hits")
    us.add_argument("--runs", type=int, default=40)
    us.add_argument("--seed", type=int, default=1)

    ts = sub.add_parser("team", help="make a team of characters (character generation)")
    ts.add_argument("--era", default="medieval")
    ts.add_argument("--region", default=None, help="default: england for medieval, else the era's first region")
    ts.add_argument("--template", default=None, help="default: the era's first team")
    ts.add_argument("--array", action="store_true", help="the fixed array instead of 3d6 x 5")
    ts.add_argument("--women", choices=["none", "roll"], default="none", help="roll each member and follower man or woman at the army's share")
    ts.add_argument("--seed", type=int, default=None, help="repeatable dice")

    ws = sub.add_parser("work", help="jobs between fights: list an era's jobs, or work a term of one")
    ws.add_argument("--era", default="medieval")
    ws.add_argument("--place", default=None, help="town, city, village, camp, road, frontier or sea")
    ws.add_argument("--job", default=None, help="job id: work one term of it")
    ws.add_argument("--career", default=None, help="his career (default: the job's first, or the era's first)")
    ws.add_argument("--skill", type=int, default=None, help="his skill in the job's skill (default: the job's minimum)")
    ws.add_argument("--days", type=int, default=None, help="days worked (default: the term's length, or a contract's shortest)")
    ws.add_argument("--region", default=None, help="his army (default: the era's first): whose keep he pays")
    ws.add_argument("--purse", type=float, default=None, help="Days in his purse, to pay his keep from (default: what he earns)")
    ws.add_argument("--seed", type=int, default=None, help="repeatable dice")

    sp = sub.add_parser("selfplay", help="play a battlefield with the enemy commander on both sides, to its end")
    sp.add_argument("--field", required=True, help="battlefield id (data/fields)")
    sp.add_argument("--stances", default=None, help="attack,hold etc., one per side (default: the side the objective names attacks, the other holds; both attack with no objective)")
    sp.add_argument("-n", type=int, default=1, help="number of battles")
    sp.add_argument("--seed", type=int, default=1, help="the first battle's dice; each next battle the next seed")
    sp.add_argument("--story", action="store_true", help="also print each battle's turning points")

    a = p.parse_args(argv)
    try:
        d = load(a.data)
    except DataError as e:
        print("Data errors:\n" + str(e), file=sys.stderr)
        return 1

    if a.cmd == "selfplay":
        from .battle import points_text, self_play, stances, summary
        from .units import SeededDice
        if a.field not in d.fields:
            print(f"error: no battlefield {a.field}; there are: {', '.join(sorted(d.fields))}", file=sys.stderr)
            return 2
        how = a.stances.split(",") if a.stances else stances(d, a.field)
        if len(how) != 2 or any(x not in ("attack", "hold") for x in how):
            print("error: --stances takes two of attack or hold, e.g. attack,hold", file=sys.stderr)
            return 2
        print(f"{d.fields[a.field]['name']}: {d.fields[a.field]['sides'][0]} {how[0]}ing, {d.fields[a.field]['sides'][1]} {how[1]}ing.")
        for k in range(a.n):
            r = self_play(d, a.field, SeededDice(a.seed + k), how)
            print(f"Battle {k + 1} (seed {a.seed + k}): " + "\n".join(summary(d, r)))
            if a.story:
                print("\n".join(points_text(r)))
        return 0
    if a.cmd == "team":
        from .team import era, follower_line, make_followers, make_team, sheet
        from .units import SeededDice
        rng = SeededDice(a.seed) if a.seed is not None else random.Random()
        E = era(d, a.era)
        a.region = a.region or ("england" if a.era == "medieval" else E["regions"][0]["id"])
        a.template = a.template or E["templates"][0]["id"]
        for c in make_team(d, a.era, a.region, a.template, "array" if a.array else "roll", rng, a.women):
            print("\n".join(sheet(d, c)) + "\n")
        tpl = next(t for t in era(d, a.era)["templates"] if t["id"] == a.template)
        crew = make_followers(d, a.era, a.region, tpl.get("followers", []), tpl.get("follower_quality", "default"), rng, a.women)
        if crew:
            print(f"Followers ({len(crew)}):")
            for f in crew:
                print("  " + follower_line(d, f, a.era))
        return 0
    if a.cmd == "work":
        from . import jobs as J
        from .units import SeededDice
        if not a.job:
            for j in J.jobs_at(d, a.era, a.place):
                skill = f"{j['skill']} {j.get('min', 0)}+" if j.get("skill") else "no skill"
                who = "anyone" if j.get("who", "any") == "any" else ", ".join(j["who"])
                tags = (" [illegal]" if j.get("illegal") else "") + (" [approx]" if j.get("approx") else "")
                print(f"  {j['name']:<40} {J.pay_text(j):<24} {j['term']:<9} {skill:<16} risk {j.get('risk', 0):>2}%  {who}{tags}")
            return 0
        rng = SeededDice(a.seed) if a.seed is not None else random.Random()
        j = J.job(d, a.era, a.job)
        who = j.get("who", "any")
        career = a.career or (who[0] if who != "any" else d.teams[a.era]["careers"][0]["id"])
        c = {"career": career, "skills": {j["skill"]: a.skill if a.skill is not None else j.get("min", 0)} if j.get("skill") else {}}
        ok, why = J.can_take(j, c)
        if not ok:
            print(f"Not hired: {why}.")
            return 1
        r = J.work_term(d, a.era, j, c, rng, a.days)
        check = f"d100 {r['check']} against {c['skills'][j['skill']]}: {r['outcome']}" if r["check"] is not None else "no check"
        print(f"{j['name']}, {r['days']} day{'s' if r['days'] != 1 else ''}: {check}; earned {r['earned']:g} Days.")
        from .money import pay_keep, days_text_q
        region = a.region or d.teams[a.era]["regions"][0]["id"]
        k = J.keep_for(d, a.era, j, region, a.place)
        if j.get("board"):
            print("Fed by the job: no keep to pay.")
        elif k:
            pk = pay_keep((a.purse or 0) + r["earned"], r["days"], k["food"], k["bed"])
            more = (f"; went hungry {pk['hungry']} day{'s' if pk['hungry'] != 1 else ''}" if pk["hungry"] else "") + \
                   (f"; slept rough {pk['rough']} night{'s' if pk['rough'] != 1 else ''}" if pk["rough"] else "")
            print(f"Keep ({days_text_q(k['food'])} for food a day" + (f", {days_text_q(k['bed'])} a bed" if k["bed"] else "") + f"): paid {days_text_q(pk['paid'])}{more}.")
        if r["trouble"]:
            print(f"Trouble (d100 {r['trouble']['roll']} under {j['risk']}%): {r['trouble']['text']}")
            print(f"  The job's hook: {j['hook']}")
        return 0
    if a.cmd == "disease":
        from .disease import seeded_d100, simulate
        ctx = {"care": "field", "marched": False, "wet_cold": False, "filth": False}
        print("Resting in an ordinary camp (field care, not marching, dry):")
        for did, x in d.disease["diseases"].items():
            r = simulate(d, did, a.n, ctx, seeded_d100(a.seed))
            print(f"  {x['name']:<22} deaths {r['deaths']:5.1f}% (records {x['deaths']}%), "
                  f"sick {r['sick_days']:4.1f} days on average, virulence {x['virulence']}")
        from .disease import CAMP_EXAMPLES, camp_example
        print("A force of 1,000 in camp, dry weather (% dead of disease, median of 5 runs):")
        for label, weeks, hyg, hot, stay in CAMP_EXAMPLES:
            runs = sorted(camp_example(d, weeks, hyg, hot, stay, 1000, a.seed * 7 + k) for k in range(5))
            print(f"  {label:<38} {runs[2]:5.1f}%  (runs {runs[0]:.1f}-{runs[-1]:.1f})")
        if "scurvy" in d.disease:
            from .disease import SCURVY_EXAMPLES, simulate_scurvy
            S = d.disease["scurvy"]
            print(f"Scurvy, resting in an ordinary camp (virulence {S['virulence']}; records {S['deaths']}% with fresh food in time):")
            for fa in SCURVY_EXAMPLES:
                r = simulate_scurvy(d, a.n, fa, seeded_d100(a.seed))
                when = f"fresh food after {fa} weeks" if fa else "no fresh food for a year"
                print(f"  {when:<28} deaths {r['deaths']:5.1f}%, sick {r['sick_weeks']:4.1f} weeks on average")
        if "wounds" in d.disease:
            from .disease import WOUND_EXAMPLES, simulate_wounds
            print("Wounded carried from the field, resting (deaths / wound fever / days unfit):")
            for w in WOUND_EXAMPLES:
                cells = []
                for care in ("none", "field", "shelter"):
                    r = simulate_wounds(d, w, a.n // 4, care, seeded_d100(a.seed))
                    cells.append(f"{care} {r['deaths']:4.1f}% / {r['fever']:4.1f}% / {r['unfit_days']:4.1f}")
                print(f"  {w[0]:<8} {w[1]:<5} {w[2]:<6}  " + "   ".join(cells))
        return 0
    if a.cmd == "units":
        from .units import examples, pace
        print(f"Melee pace, regular swordsmen front to front ({a.table}), per minute:")
        for kit in ("none", "gambeson", "jack_sallet", "hauberk", "full_plate"):
            p = pace(d, a.table, kit, 2000, a.seed)
            print(f"  against {d.armor['kits'][kit]['name']:<52} {p['hit']:4.1f}% hit, {p['down']:4.1f}% put out of the fight")
        print(f"Example fights, 120 men a side, 30 abreast, {a.runs} runs each (medians):")
        for r in examples(d, a.table, a.runs, a.seed):
            print(f"  {r['label']:<40} breaks after {r['minutes']:>3} min; first side broke {r['a_broke']}, second {r['b_broke']}; "
                  f"winner {r['winner_down']} down, loser {r['loser_down']} down")
        from .units import hero_examples
        print(f"A hero leading regular billmen in jacks from the front, until one side breaks ({a.runs * 5} runs each):")
        for r in hero_examples(d, a.table, a.runs * 5, a.seed):
            print(f"  {r['label']:<22} wounded {r['wounded']:4.1f}%, down {r['down']:4.1f}%, killed {r['dead']:4.1f}%; "
                  f"men he put down {r['felled']:.2f} on average")
        from .units import gun_examples
        print(f"A battery of 6 guns (smoothbore, howitzers or rifled) firing for a minute at 1,600 men in close order ({a.runs * 5} runs each):")
        for r in gun_examples(d, a.runs * 5, a.seed):
            print(f"  {r['label']:<36} {r['struck']:5.1f} men struck, {r['down']:4.1f} put down")
        from .units import mg_examples
        print(f"Machine guns and magazine rifles (regular) firing for a minute at 100 riflemen ({a.runs * 5} runs each):")
        for r in mg_examples(d, a.runs * 5, a.seed):
            print(f"  {r['label']:<44} {r['hit']:5.1f} hit, {r['down']:4.1f} put down")
        from .units import shell_examples
        print(f"Indirect fire for a minute on the middle of 100 riflemen ({a.runs * 5} runs each):")
        for r in shell_examples(d, a.runs * 5, a.seed):
            print(f"  {r['label']:<44} {r['struck']:5.1f} struck, {r['down']:4.1f} put down, pinned {r['pinned']:3.0f}%")
        return 0
    if a.cmd == "check":
        for w in d.warnings:
            print("warning:", w)
        print(f"OK: {len(d.locations)} locations, {len(d.weapons)} weapons, {len(d.tables)} tables")
    elif a.cmd == "list":
        print("Tables:")
        for t in d.tables.values():
            print(f"  {t['id']:<24} {t['name']}  [{t['confidence']}]")
        print("Weapons:")
        for w in d.weapons.values():
            tag = f"  [threat: {w['threat']}]" if w.get("threat") else (f"  [melee: {w['melee']}]" if w.get("melee") else "")
            print(f"  {w['id']:<24} {w['name']}{tag}")
        print("Modifiers (--mod, stack; one per group):")
        for m in d.modifiers.values():
            g = f"  [group: {m['group']}]" if m.get("group") else ""
            print(f"  {m['id']:<24} {m['name']}{g}")
        print("Armour kits (--armor):")
        for k in d.armor["kits"].values():
            print(f"  {k['id']:<24} {k['name']}")
    elif a.cmd == "show":
        for row in table_ranges(d, a.table, a.weapon, a.mod):
            print(f"  {fmt(row['lo'])}-{fmt(row['hi'])}  {d.loc[row['id']]['name']}")
    elif a.cmd == "roll":
        from .model import resolve_table
        if a.armor and d.tables[resolve_table(d, a.table, a.weapon)]["armor"] == "baked_in":
            print("warning: this table already reflects the armour its source population wore; "
                  "use an all-hits, baseline, knife or unarmed table with --armor", file=sys.stderr)
        rng = random.Random(a.seed)
        from .combat import attack_roll, defence_roll
        for _ in range(a.n):
            margin = crit = aroll = None
            if a.attack is not None:
                ar_ = attack_roll(d, a.attack, rng.randint(1, 100), a.att_penalty)
                tag = " CRITICAL" if ar_["critical"] else ""
                print(f"Attack: d100 {fmt(ar_['roll'])} vs {ar_['effective']}% - "
                      + (f"hit, margin {ar_['margin']}{tag}" if ar_["hit"] else "miss"))
                if not ar_["hit"]:
                    continue
                if a.defence is not None and not ar_["critical"]:
                    dr = defence_roll(a.defence, rng.randint(1, 100), a.def_penalty)
                    print(f"Defence: d100 {fmt(dr['roll'])} vs {dr['effective']}% - " + ("defended" if dr["defended"] else "failed"))
                    if dr["defended"]:
                        continue
                margin, crit, aroll = ar_["margin"], ar_["critical"], ar_["roll"]
            shield = None
            if a.shield == "yes":
                shield = True
            elif a.shield == "no":
                shield = False
            elif a.shield == "kit":
                shield = bool((d.armor["kits"].get(a.armor or "none") or {}).get("shield", False))
            if a.blow and not d.weapons[a.weapon].get("choose"):
                raise SystemExit(f"{a.weapon} is not a cut-and-thrust weapon: its blow is not chosen")
            h = roll_hit(d, a.table, a.weapon, a.severity, rng, a.mod, a.called, a.armor, margin, bool(crit), shield,
                         mechanism=a.blow, attack_roll=aroll)
            rl = h["rolls"]
            loc_roll = fmt(rl["location"]) + (f"/{fmt(rl['location2'])}" if rl["location2"] else "")
            sev_roll = f" (d100 {fmt(rl['severity'])})" if rl["severity"] else ""
            ar = h["armor"]
            sev_txt = ar["from"] if ar else h["severity"]
            print(f"{h['location_name']} (d100 {loc_roll}) - "
                  f"{h['mechanism']} ({'declared' if rl['mechanism'] is None else 'd100 ' + fmt(rl['mechanism'])}) - {sev_txt}{sev_roll}"
                  + (" - graze: bleed and pain one step lower, no stop check" if h.get("graze") else ""))
            if h["table"] != a.table:
                print(f"    (close combat: location rolled on {d.tables[h['table']]['name']})")
            if ar:
                cov = (f", {'attack units digit' if aroll is not None else 'cover d10'} {ar['cover_roll'] % 10}"
                       if ar["cover_roll"] else "")
                if not ar["covered"]:
                    print(f"    Armour: gap, not covered{cov}")
                else:
                    mat = d.armor["materials"][ar["material"]]["name"]
                    print(f"    Armour: {mat}{cov} - {ar['steps']} step(s): {ar['from']} -> {ar['to']}")
            if h["effects"] is None:
                print("    Stopped by armour: bruise, no wound")
                continue
            for line in describe(d, h["effects"]):
                print("   ", line)
    return 0


if __name__ == "__main__":
    sys.exit(main())
