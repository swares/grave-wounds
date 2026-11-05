"""The playtest packet (dist/playtest-packet.html): one fight and a week in camp, printed. The words
are in templates/playtest/packet.md; every number and table comes from the data, through the same
values and tables as the Rules, so the packet follows the rules. The four men are the Rules' own
running retinue, made with the same seeded dice."""

from __future__ import annotations

import html
import random
import re
from pathlib import Path

import markdown
import yaml

from . import disease as DZ
from . import rulebook as RB
from . import weather as WX
from .engine import compose_wound, table_ranges
from .model import Data
from .team import make_team
from .units import SeededDice

VERSION = "0.1, 5 November 2026"
LINK = "https://swares.github.io/grave-wounds/dist/team.html#playtest"
SITE = "https://swares.github.io/grave-wounds/"
EMAIL = "waresscott@gmail.com"
MEN = (("William of Ely", "leader", "Leader"), ("Gilbert Cooper", "scout", "Scout"),
       ("Edmund Miller", "quartermaster", "Quartermaster"), ("Nicholas Fletcher", "leech", "Leech"))
# Clifford's five (the roller's PLAYTEST in templates/roller.html lists the same men). Five, because the script
# playing both sides won 5 of 12 against five and 3 of 12 against seven with a serjeant (tools/campaign/playtest.py).
FOES = (("Billman", "jack_sallet", "bill", "regular"), ("Billman", "jack_sallet", "bill", "regular"),
        ("Billman", "jack_sallet", "bill", "regular"), ("Billman", "jack_sallet", "bill", "regular"),
        ("Archer", "jack_sallet", "longbow", "regular"))
TABLE = "towton-1461-all-hits"
WEAPONS = ("sword", "bill", "longbow", "dagger")
SKILLS = (("blade", "Blade"), ("polearm", "Polearm"), ("bow", "Bow"), ("parry", "Parry"), ("dodge", "Dodge"),
          ("leechcraft", "Leechcraft"), ("fieldcraft", "Fieldcraft"), ("watch", "Watch"), ("stealth", "Stealth"),
          ("persuade", "Persuade"), ("command", "Command"))
QUESTIONS = ("Did the margin-to-severity result feel fair?", "Was the fight fast enough to stay tense?",
             "Did you understand why a wound had the effect it did?", "Were the daily and weekly checks interesting?",
             "Did the weather and sickness change any decisions?", "Was the evening council worth its time?",
             "Did your role give you something to decide?", "Was the lethality right for the setting?",
             "Would you play a second session with these men?")


def _team(d: Data) -> dict:
    team = make_team(d, "medieval", "england", "retinue", "roll", SeededDice(3))
    return {c["name"]: c for c in team}


def _table(rows: list, head: list | None = None, cls: str = "") -> str:
    e = html.escape
    th = "<thead><tr>" + "".join(f"<th>{e(str(h))}</th>" for h in head) + "</tr></thead>" if head else ""
    body = "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}">{th}<tbody>{body}</tbody></table>'


def _hit(d: Data) -> str:
    cols = [{r["id"]: r for r in table_ranges(d, TABLE, w)} for w in WEAPONS]
    head = ["Place"] + [d.weapons[w].get("short", d.weapons[w]["name"]).split(" (")[0] for w in WEAPONS]
    rows = []
    for L in d.locations:
        cells = []
        f = lambda n: "00" if n == 100 else f"{n:02d}"
        for c in cols:
            r = c.get(L["id"])
            cells.append("–" if not r else (f(r["lo"]) if r["lo"] == r["hi"] else f"{f(r['lo'])}–{f(r['hi'])}"))
        rows.append([L["name"]] + cells)
    return _table(rows, head, "tight")


def _armour(d: Data) -> str:
    A = d.armor
    kits = [A["kits"][k] for k in ("brigandine_sallet", "jack_sallet")]
    mats = A["materials"]
    def cell(k, slot):
        v = (k.get("slots") or {}).get(slot)
        if not v:
            return "–"
        m, cover = (v, None) if isinstance(v, str) else (v.get("material"), v.get("cover"))
        if m is None:
            return "bands"
        p = mats[m]
        s = f"{p.get('cut', 0)}/{p.get('pierce', 0)}/{p.get('crush', 0)}"
        return f"{s} on {cover // 10}" if cover else s
    rows = []
    for slot in A["slots"]:
        c = [cell(k, slot) for k in kits]
        if any(x != "–" for x in c):
            rows.append([slot.replace("_", " ")] + c)
    return _table(rows, ["Part (steps: cut/pierce/crush)", "Brigandine and sallet", "Jack and sallet"], "tight")


def _short(w: dict) -> str:
    bits = [f"B{w.get('bleed', 0)} P{w.get('pain', 0)}"]
    if w.get("shock"):
        bits.append("S")
    if w.get("severed"):
        bits.append("severed")
    if w.get("lethal") and w["lethal"] != "none":
        bits.append(str(w["lethal"]))
    bits += [str(x).replace("_", " ") for x in w.get("impair", [])]
    return " ".join(bits)


def _effects(d: Data) -> str:
    seen, rows = {}, []
    for L in d.locations:
        seen.setdefault(L["class"], L)
    head = ["Place", "Fever", "Light cut", "Serious cut", "Critical cut", "Light thrust", "Serious thrust", "Critical thrust"]
    for cls, L in seen.items():
        row = [cls.replace("_", " ").capitalize(), compose_wound(d, L["id"], "pierce", "serious").get("infection", "")]
        for mech in ("cut", "pierce"):
            for sev in ("light", "serious", "critical"):
                row.append(_short(compose_wound(d, L["id"], mech, sev)))
        rows.append(row)
    return _table(rows, head, "effects")


def _sickness(d: Data) -> str:
    rows = []
    for name, f in (("Quarters, dead buried or far off", ["good"]), ("Watched camp", []), ("Bivouac", ["poor"]),
                    ("Quarters, dead unburied nearby", ["good", "dead"]), ("Watched camp, dead unburied", ["dead"]),
                    ("Bivouac, dead unburied", ["poor", "dead"])):
        rows.append([name, f"{DZ.catch_chance(d, 'flux', f, 50):.1f}".rstrip("0").rstrip(".") + "%"])
    return _table(rows, ["Camp", "Flux this week, Endurance 50"], "tight")


def _sheet(d: Data, c: dict, role: str, v: dict) -> str:
    e = html.escape
    per, pool = d.wounds["combat"]["characteristics"]["blood"]["per"], d.wounds["tracking"]["blood_pool"]
    blood = pool + (c["stats"]["end"] - 50) // per
    std = int(blood * d.wounds["lethality"]["presets"]["standard"]["blood"])
    s = c["stats"]
    stats = _table([[s["str"], s["agi"], s["end"], s["wits"], s["nerve"], s["pres"]]],
                   ["Strength", "Agility", "Endurance", "Wits", "Nerve", "Presence"], "tight")
    skills = _table([[f"{n} {c['skills'].get(k, 0)}" for k, n in SKILLS[i:i + 4]] for i in range(0, len(SKILLS), 4)], None, "tight")
    R = d.council["roles"][role]
    rolls = ", ".join(x["name"] for x in d.council["rolls"].values() if x["role"] == role)
    weapon = d.weapons[c["weapon"]]["name"].split(" (")[0]
    kit = d.armor["kits"][c["kit"]]["name"]
    career = RB._career(d, c).capitalize()
    track = _table([["", "", "", "", ""] for _ in range(4)], ["Place", "Wound", "Bleed, pain", "On the track", "Day"], "lined")
    old = "; ".join(f"{o['loc'].replace('_', ' ')}" for o in c.get("old", [])) or "none"
    return (f'<section class="page sheet"><h1>{e(c["name"])}</h1><p class="sub">{e(career)}, aged {c["age"]}. {e(c["origin"])}. '
            f'{e(c["trait"])}; {e(c["drawback"].lower())}. Old wound: {e(old)}.</p>'
            f'<p class="role"><b>Your role: {e(R["name"])}.</b> {e(R["decides"])} You roll for: {e(rolls)}.</p>'
            f'{stats}<p><b>{e(weapon)}:</b> Attack {c["attack"]}. <b>Defence:</b> {c["defence"]}. <b>Initiative:</b> d10 + {s["agi"] // 10}. '
            f'<b>Armour:</b> {e(kit)}.</p><p><b>Blood:</b> Standard {std}, Gritty {blood}. <b>Fate:</b> Standard 1, Gritty 0.</p>'
            f'<h2>Skills</h2>{skills}<h2>Blood now</h2><div class="blank small"></div><h2>Wounds</h2>{track}<h2>Notes</h2><div class="blank"></div>'
            f'__FOOT__</section>')


def _map() -> str:
    return ('<svg viewBox="0 0 480 170" role="img" aria-label="Sketch of the ford: the river across the middle, the ford, the broken bridge to the east, Clifford\'s men to the north, the four men to the south">'
            '<rect width="480" height="170" fill="#fff" stroke="#555"/><path d="M0 70 C120 60 240 95 480 72 L480 108 C240 130 120 98 0 106Z" fill="#cdd9e3"/>'
            '<rect x="190" y="74" width="62" height="42" fill="#e4dcc8" stroke="#777" stroke-dasharray="3 3"/><text x="221" y="99" font-size="11" text-anchor="middle">The ford</text>'
            '<path d="M410 64 v50 M425 64 v50" stroke="#333" stroke-width="3" stroke-dasharray="9 7"/><text x="417" y="60" font-size="11" text-anchor="middle">Broken bridge</text>'
            '<text x="221" y="26" font-size="12" text-anchor="middle">Clifford\'s men come from the north</text><text x="221" y="155" font-size="12" text-anchor="middle">Your four men, south bank</text>'
            '<text x="40" y="92" font-size="11">River Aire</text></svg>')


def _foes(d: Data) -> str:
    Q = d.units["quality"]
    rows = []
    for name, kit, w, q in FOES:
        rows.append([name, d.weapons[w]["name"].split(" (")[0], d.armor["kits"][kit]["name"].split(" (")[0], Q[q]["attack"], Q[q]["defence"], Q[q]["nerve"], d.wounds["tracking"]["blood_pool"]])
    return _table(rows, ["Man", "Weapon", "Armour", "Attack", "Defence", "Nerve", "Blood"], "tight")


def _weather(d: Data, root: Path) -> str:
    m = yaml.safe_load((root / "data" / "maps" / "towton-1461.yaml").read_text(encoding="utf-8"))
    rng, prev, rows = random.Random(1461), None, []
    C = d.weather["conditions"]
    for day in range(2, 9):
        w = WX.roll_weather(d, m, day, prev, [rng.randint(1, 100) for _ in range(7)])
        if day == 3:                                 # Palm Sunday: the snow of the record, not a roll
            w = {**w, "cond": "snow", "high": min(w["high"], 1), "low": min(w["low"], -2)}
        prev = w
        y, mo, dd = WX.map_date(m, day)
        hard = C[w["cond"]].get("precip", "none") != "none" or w["low"] <= 0
        rows.append([f"{dd} {'March' if mo == 3 else 'April'}", C[w["cond"]].get("name", w["cond"]), f"{round(w['high'] * 9 / 5 + 32)}°F", f"{round(w['low'] * 9 / 5 + 32)}°F", "Yes" if hard else "No"])
    return _table(rows, ["Day", "Weather", "High", "Low", "Hard night in the open?"], "tight")


def _camplog() -> str:
    days = ["28 Mar", "29 Mar", "30 Mar", "31 Mar", "1 Apr", "2 Apr", "3 Apr"]
    return _table([[x, "", "", "", "", ""] for x in days], ["Day", "Where, what camp", "Food left", "Council decided", "Rolls and results", "Who is worse or better"], "lined log")


def _feedback() -> str:
    return _table([[f"{i + 1}. {q}", "1  2  3  4  5", ""] for i, q in enumerate(QUESTIONS)], ["Question", "Score", "Comment"], "lined")


CSS = """
:root{--ink:#1d2128;--muted:#5b6370;--red:#8c1a2b;--line:#b9bec6}
*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--ink);font:10.2pt/1.34 Georgia,"Times New Roman",serif}
.page{width:8.5in;min-height:11in;padding:.36in .6in .48in;position:relative;margin:0 auto;page-break-after:always;break-after:page;overflow-wrap:break-word}
h1{font-size:19pt;margin:0 0 6px;color:var(--ink)}h1.cover,.cover{font-size:34pt}h2{font-size:12pt;margin:8px 0 3px}p{margin:0 0 5px}ul,ol{margin:0 0 5px;padding-left:1.25em}li{margin-bottom:2px}
a{color:var(--red)}table{border-collapse:collapse;width:100%;margin:2px 0 5px;font-size:8.6pt;font-family:Arial,Helvetica,sans-serif}th,td{border:1px solid var(--line);padding:2px 4px;text-align:left;vertical-align:top}th{background:#eef0f2}
table.tight{font-size:8.2pt}table.tight td,table.tight th{padding:1px 4px}table.effects{font-size:7.3pt}table.effects td,table.effects th{padding:2px 3px}table.lined td{height:30px}table.log td{height:62px}
.foot{position:absolute;left:.6in;right:.6in;bottom:.28in;display:flex;justify-content:space-between;font:7.5pt Arial,sans-serif;color:var(--muted)}
.blank{height:1.1in;border:1px solid var(--line)}.blank.small{height:.4in}.sub{color:var(--muted)}.role{border-left:3px solid var(--red);padding-left:8px}
.admonition{background:#f3f4f6;border-left:3px solid var(--red);padding:5px 9px;margin:5px 0}.admonition-title{font-weight:bold;margin:0}svg{display:block;width:100%;max-height:1.9in;margin:4px 0}
@media screen{body{background:#dfe2e6}.page{background:#fff;margin:12px auto;box-shadow:0 1px 4px #0003}}@media print{@page{size:Letter;margin:0}.page{margin:0}}
@media screen and (max-width:820px){.page{width:auto;min-height:0;padding:16px}.foot{position:static;margin-top:12px}table{display:block;overflow-x:auto}}
"""


def render(d: Data, root: Path) -> str:
    team, v, tabs = _team(d), RB.values(d), RB.tables(d, {"medieval"})
    gil = team["Gilbert Cooper"]
    v = {**v, "pt_version": VERSION, "pt_link": LINK, "pt_link_short": "swares.github.io/grave-wounds/dist/team.html#playtest", "pt_site": SITE, "pt_email": EMAIL,
         "pt_gil_attack": gil["attack"], "pt_gil_margin": gil["attack"] - 31, "pt_foe_def": d.units["quality"]["regular"]["defence"], "pt_foe_nerve": d.units["quality"]["regular"]["nerve"], "pt_foe_pain": 2 * v["pain_step"],
         "pt_rations": d.supplies["rations"]["carried"]["medieval"], "pt_bow_range": ", ".join(str(x) for x in d.weapons["longbow"]["range"]),
         "aim_cost": d.wounds["combat"]["aim"]["cost"], "dead_days": d.disease.get("dead_days", 14)}
    text = (root / "templates" / "playtest" / "packet.md").read_text(encoding="utf-8")
    sheets = "".join(_sheet(d, team[n], r, v) for n, r, _ in MEN)
    parts = {"hit": _hit(d), "armour": _armour(d), "effects": _effects(d), "sickness": _sickness(d), "map": _map(), "foes": _foes(d),
             "weather": _weather(d, root), "camplog": _camplog(), "feedback": _feedback()}
    text = text.replace("{{pt:sheets}}\n", "")
    keep = {}
    for k, h in parts.items():
        keep[f"@@{k}@@"] = h
        text = text.replace("{{pt:" + k + "}}", f"@@{k}@@")
    text = RB._fill(text, v, tabs, "templates/playtest/packet.md")
    foot = f'<div class="foot"><span>Grave Wounds playtest packet, version {html.escape(VERSION)}</span><span>© 2026 Scott Wares. All rights reserved. Free to copy for playtesting.</span></div>'
    pages = []
    for i, md in enumerate(p for p in text.split("<!-- page -->") if p.strip()):
        body = markdown.markdown(md, extensions=["tables", "admonition", "attr_list"])
        for k, h in keep.items():
            body = body.replace(f"<p>{k}</p>", h).replace(k, h)
        pages.append(f'<section class="page">{body}{foot}</section>')
        if '{#camp}' in md or 'id="camp"' in body:
            pages.append(sheets.replace("__FOOT__", foot))
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>Grave Wounds: playtest packet</title><style>{CSS}</style></head><body>{"".join(pages)}'
            '</body></html>\n')
