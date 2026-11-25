"""Print-and-play modules (data/modules/*.yaml), each built to dist/<file>.html: a scenario with its
pregenerated men, map, counters, the enemy's roster, the tables it needs and a quick reference. The
words are in the module's `text` (Markdown); every number and table comes from the data, through the
same values and tables as the Rules, so a module follows the rules. The first is Ferrybridge, the
playtest packet (data/modules/ferrybridge.yaml): one fight and a week in camp, its four men the Rules'
own running retinue, made with the same seeded dice."""

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

SITE = "https://swares.github.io/grave-wounds/"
# Feedback goes through the Google Form, not a printed email address. The packet prints the short address of
# feedback.html, which build.py writes to forward to the form, so it can be typed from paper.
FORM = "https://docs.google.com/forms/d/e/1FAIpQLSfGgYKRfBpDth3odGXHWHI1iXSNCmscYczxBW7BE_2Pv9-Hwg/viewform"
FEEDBACK = SITE + "feedback.html"
M: dict = {}                                       # the module being built (load_module): its men, foes, map and words


def modules(root: Path) -> list[str]:
    """The modules in data/modules, by id."""
    return sorted(p.stem for p in (root / "data" / "modules").glob("*.yaml"))


def load_module(root: Path, mid: str) -> dict:
    """data/modules/<mid>.yaml, checked: its men, foes and parts named."""
    m = yaml.safe_load((root / "data" / "modules" / f"{mid}.yaml").read_text(encoding="utf-8"))
    for k in ("id", "title", "footer", "file", "text", "version", "team", "men", "foes", "table", "weapons", "battlemap", "weather"):
        if k not in m:
            raise ValueError(f"data/modules/{mid}.yaml: no {k}")
    B = m["battlemap"]
    for k in ("hex", "cols", "rows", "aria", "areas"):
        if k not in B:
            raise ValueError(f"data/modules/{mid}.yaml: battlemap has no {k}")
    return m


def _men() -> list:
    return [(x["name"], x["role"]) for x in M["men"]]


def _foelist() -> list:
    return [(x["name"], x["kit"], x["weapon"], x["quality"]) for x in M["foes"]]


def _team(d: Data) -> dict:
    T = M["team"]
    team = make_team(d, T["era"], T["region"], T["template"], T["mode"], SeededDice(T["seed"]))
    return {c["name"]: c for c in team}


def _table(rows: list, head: list | None = None, cls: str = "") -> str:
    e = html.escape
    th = "<thead><tr>" + "".join(f"<th>{e(str(h))}</th>" for h in head) + "</tr></thead>" if head else ""
    body = "".join("<tr>" + "".join(f"<td>{e(str(c))}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}">{th}<tbody>{body}</tbody></table>'


def _hit(d: Data) -> str:
    cols = [{r["id"]: r for r in table_ranges(d, M["table"], w)} for w in M["weapons"]]
    head = ["Place"] + [d.weapons[w].get("short", d.weapons[w]["name"]).split(" (")[0] for w in M["weapons"]]
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
    kits = [A["kits"][k] for k, _ in M["armour"]]
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
    return _table(rows, ["Part (steps: cut/pierce/crush)", *[head for _, head in M["armour"]]], "tight")


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
    for name, f in M["camps"]:
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
    SK = M["skills"]
    skills = _table([[f"{n} {c['skills'].get(k, 0)}" for k, n in SK[i:i + 4]] for i in range(0, len(SK), 4)], None, "tight")
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
    return "".join(M["sketch"])


# ---------- the kit for playing on paper: a hex map, counters, the enemy's roster and a blank sheet ----------
# The map is pointy-topped hexes, odd rows pushed right, at the module's `hex` inches across, so the counters sit in one.


def _hexpath(cx: float, cy: float, r: float) -> str:
    import math
    pts = [(cx + r * math.cos(math.radians(60 * i - 30)), cy + r * math.sin(math.radians(60 * i - 30))) for i in range(6)]
    return "M" + " L".join(f"{x:.3f} {y:.3f}" for x, y in pts) + "Z"


def _fill(B: dict, row: int, col: int) -> str:
    """A hex's colour: the last of the map's `areas` holding it (rows and cols are [from, to), all if left out)."""
    fill = B.get("fill", "#fff")
    for a in B["areas"]:
        rows, cols = a.get("rows") or [0, B["rows"]], a.get("cols") or [0, B["cols"]]
        if rows[0] <= row < rows[1] and cols[0] <= col < cols[1]:
            fill = a["fill"]
    return fill


def _label(B: dict, L: dict, geo: dict) -> str:
    """One of the map's `labels`: x in hexes across (or left, mid, right), y at a row's top (or top,
    bottom) plus `dy` inches; size, anchor, italic and bold as given."""
    x = {"left": 0.05, "mid": geo["w"] / 2, "right": geo["w"] - 0.08}.get(L["x"]) if isinstance(L["x"], str) else geo["hex"] * L["x"]
    y = {"top": geo["top"], "bottom": geo["h"]}.get(L["y"]) if isinstance(L["y"], str) else geo["top"] + geo["r"] + L["y"] * 1.5 * geo["r"]
    style = (' font-style="italic"' if L.get("italic") else "") + (' font-weight="bold"' if L.get("bold") else "")
    anchor = f' text-anchor="{L["anchor"]}"' if L.get("anchor", "middle") != "start" else ""
    return f'<text x="{x:.3f}" y="{y + L.get("dy", 0):.3f}" font-size="{L.get("size", 0.16)}"{anchor}{style}>{html.escape(L["text"])}</text>'


def _battlemap() -> str:
    """The module's map as a printed hex map, true to size on Letter: its ground in `areas` (each a block of
    rows and columns and its colour, later ones on top), its `labels`, and an approach track above if it has one."""
    import math
    B = M["battlemap"]
    HEX, COLS, ROWS, TRACK = B["hex"], B["cols"], B["rows"], B.get("track", 0)
    e = html.escape
    r = HEX / math.sqrt(3)                         # centre to corner
    w, top = COLS * HEX + HEX / 2, 0.62 if TRACK else 0.1
    hexes = []
    for row in range(ROWS):
        for col in range(COLS):
            cx = HEX / 2 + col * HEX + (HEX / 2 if row % 2 else 0)
            cy = top + r + row * 1.5 * r
            hexes.append(f'<path d="{_hexpath(cx, cy, r)}" fill="{_fill(B, row, col)}" stroke="#7d8590" stroke-width="0.01"/>')
    h = top + r * 2 + (ROWS - 1) * 1.5 * r
    track = ""
    if TRACK:
        box = (w - 0.1) / TRACK
        track = "".join(f'<rect x="{0.05 + i * box:.3f}" y="0.2" width="{box - 0.03:.3f}" height="0.32" fill="#fff" stroke="#7d8590" stroke-width="0.012"/>'
                        f'<text x="{0.05 + i * box + box / 2:.3f}" y="0.42" font-size="0.15" text-anchor="middle">{TRACK - i}</text>' for i in range(TRACK))
        track += f'<text x="0.05" y="0.15" font-size="0.13">{e(B["track_label"].format(track=TRACK), quote=False)}</text>'
    geo = {"w": w, "h": h, "top": top, "r": r, "hex": HEX}
    labels = "".join(_label(B, L, geo) for L in B.get("labels", []))
    return (f'<svg class="mapsheet" viewBox="0 0 {w:.3f} {h + 0.02:.3f}" width="{w:.3f}in" height="{h + 0.02:.3f}in" role="img" '
            f'aria-label="{e(B["aria"])}">'
            f'{track}{"".join(hexes)}{labels}</svg>')


def _counters(team: dict) -> str:
    """Counters to cut out: the four, Clifford's five, and markers."""
    e = html.escape
    def ctr(top: str, bottom: str, cls: str) -> str:
        return f'<div class="ctr {cls}"><b>{e(top)}</b><span>{e(bottom)}</span></div>'
    short = M["short"]
    men = [ctr(n.split(" ")[0], short.get(team[n]["weapon"], team[n]["weapon"]), "york") for n, _ in _men()]
    foes = [ctr(_foe_name(i, name), short[w], "clifford") for i, (name, _, w, _) in enumerate(_foelist())]
    marks = ([ctr("Down", "", "mark")] * 9 + [ctr("Stopped", "", "mark")] * 6 + [ctr("Bound", "", "mark")] * 6 + [ctr("Prisoner", "", "mark")] * 3
             + [ctr("Bleed", f"B{n}", "mark bleed") for n in (1, 2, 3) for _ in range(5)] + [ctr("Aimed", "", "mark")] * 4
             + [ctr("Fate", "used", "mark")] * 4 + [ctr("Round", "", "mark round")] * 2)
    return (f'<p class="sub">Print on card, or glue to card, and cut along the lines. Each fits in a hex of the map. A man\'s Bleed marker shows his bleeding step (B1 to B3), his wounds\' bleed added up (<i>Wounds</i> gives the Blood it costs each round); swap it as wounds are bound.</p>'
            f'<h2>{e(M["men_side"])}</h2><div class="ctrs">{"".join(men)}</div><h2>{e(M["foe_side"], quote=False)}</h2><div class="ctrs">{"".join(foes)}</div>'
            f'<h2>Markers</h2><div class="ctrs">{"".join(marks)}</div>')


def _foe_name(i: int, name: str) -> str:
    """A foe's name on his counter and the roster: numbered when the module has more than one of the name."""
    names = [x["name"] for x in M["foes"]]
    return f"{name} {i + 1}" if names.count(name) > 1 else name


def _roster(d: Data) -> str:
    """The GM's roster of Clifford's five: initiative, the numbers, Blood to tick off, wounds."""
    e = html.escape
    Q, pool = d.units["quality"], d.wounds["tracking"]["blood_pool"]
    boxes = '<span class="ticks">' + "☐" * pool + "</span>"
    rows = []
    for i, (name, kit, w, q) in enumerate(_foelist()):
        nm = _foe_name(i, name)
        rows.append(f'<tr><td><b>{e(nm)}</b><br>{e(d.weapons[w]["name"].split(" (")[0])}, {e(d.armor["kits"][kit]["name"].split(" (")[0].lower())}</td>'
                    f'<td></td><td>{Q[q]["attack"]}</td><td>{Q[q]["defence"]}</td><td>{Q[q]["nerve"]}</td><td>{boxes}</td><td></td></tr>')
    rounds = "".join(f"<td>{i}</td>" for i in range(1, 21))
    return (f'<table class="roster"><thead><tr><th>Man</th><th>Init.</th><th>Attack</th><th>Defence</th><th>Nerve</th><th>Blood (tick one off each lost)</th><th>Wounds: place, severity, bleed, pain</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table><h2>Rounds</h2><table class="rounds"><tr>{rounds}</tr></table>')


def _blank_sheet() -> str:
    """A character sheet to fill in by hand, laid out as the four's."""
    stats = _table([["", "", "", "", "", ""]], ["Strength", "Agility", "Endurance", "Wits", "Nerve", "Presence"], "lined")
    SK = M["skills"]
    skills = _table([[f"{n}" for _, n in SK[i:i + 4]] for i in range(0, len(SK), 4)], None, "lined")
    track = _table([["", "", "", "", ""] for _ in range(5)], ["Place", "Wound", "Bleed, pain", "On the track", "Day"], "lined")
    return ('<section class="page sheet"><h1>Name: <span class="line"></span></h1><p class="sub">Career, age, origin, trait, drawback, old wounds:</p><div class="blank small"></div>'
            '<p class="role"><b>Role:</b> <span class="line"></span></p>'
            f'{stats}<p><b>Weapon:</b> <span class="line short"></span> <b>Attack:</b> <span class="line tiny"></span> <b>Defence:</b> <span class="line tiny"></span> '
            '<b>Initiative:</b> d10 + Agility ÷ 10 <b>Armour:</b> <span class="line short"></span></p>'
            '<p><b>Blood:</b> Standard <span class="line tiny"></span> Gritty <span class="line tiny"></span> <b>Fate:</b> Standard 1, Gritty 0.</p>'
            f'<h2>Skills</h2>{skills}<h2>Blood now</h2><div class="blank small"></div><h2>Wounds</h2>{track}<h2>Notes</h2><div class="blank"></div>'
            '__FOOT__</section>')


def _rates(d: Data) -> str:
    """Blood lost a round at each bleeding step, in words: '1 Blood every 10 rounds' for a fraction."""
    out = []
    for k, r in sorted((int(k), r) for k, r in d.wounds["tracking"]["bleed_per_round"].items()):
        if k:
            out.append(f"B{k}, " + (f"1 Blood every {round(1 / r)} rounds" if r < 1 else f"{r:g} a round"))
    return "; ".join(out)

def _contents(pages: list) -> str:
    """The cover's list of what is on which page, worked out from the pages as laid out: runs of pages
    together, and the pages with a blank back ('own sheet') each on a row, the four characters on one."""
    import re
    def title(p):
        m = re.search(r"<h1[^>]*>(.*?)</h1>", p, re.S)
        return re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    rows, run = [], []
    def flush():
        if run:
            n = f"{run[0][0]}–{run[-1][0]}" if len(run) > 1 else str(run[0][0])
            rows.append((n, ", ".join(t for _, t in run), ""))
            run.clear()
    chars = []
    for i, p in enumerate(pages, 1):
        if "blankpage" in p:
            continue
        own = i < len(pages) and "blankpage" in pages[i]
        t = "The cover" if i == 1 else "A blank character sheet" if t_is_blank(p) else title(p)
        if own and 'class="page sheet"' in p and not t_is_blank(p):
            flush(); chars.append((i, t)); continue
        if chars:
            rows.append((", ".join(str(n) for n, _ in chars), "The characters: " + ", ".join(t for _, t in chars), "Own sheet each"))
            chars = []
        if own:
            flush(); rows.append((str(i), t, "Own sheet"))
        else:
            run.append((i, t))
    flush()
    body = "".join(f"<tr><td>{n}</td><td>{html.escape(t)}</td><td>{o}</td></tr>" for n, t, o in rows)
    return f'<table class="contents"><thead><tr><th>Pages</th><th>What\'s there</th><th>Printed both sides</th></tr></thead><tbody>{body}</tbody></table>'


def t_is_blank(p: str) -> bool:
    return "Name: <span" in p


def _foes(d: Data) -> str:
    Q = d.units["quality"]
    rows = []
    for name, kit, w, q in _foelist():
        rows.append([name, d.weapons[w]["name"].split(" (")[0], d.armor["kits"][kit]["name"].split(" (")[0], Q[q]["attack"], Q[q]["defence"], Q[q]["nerve"], d.wounds["tracking"]["blood_pool"]])
    return _table(rows, ["Man", "Weapon", "Armour", "Attack", "Defence", "Nerve", "Blood"], "tight")


def _weather(d: Data, root: Path) -> str:
    W = M["weather"]
    m = yaml.safe_load((root / "data" / "maps" / f"{W['map']}.yaml").read_text(encoding="utf-8"))
    rng, prev, rows = random.Random(W["seed"]), None, []
    C = d.weather["conditions"]
    for day in range(W["days"][0], W["days"][1] + 1):
        w = WX.roll_weather(d, m, day, prev, [rng.randint(1, 100) for _ in range(7)])
        fx = (W.get("fixed") or {}).get(day)
        if fx:                                       # the record's day, not a roll (Ferrybridge: the snow of Palm Sunday)
            w = {**w, "cond": fx["cond"], "high": min(w["high"], fx["high_at_most"]), "low": min(w["low"], fx["low_at_most"])}
        prev = w
        y, mo, dd = WX.map_date(m, day)
        hard = C[w["cond"]].get("precip", "none") != "none" or w["low"] <= 0
        rows.append([f"{dd} {'March' if mo == 3 else 'April'}", C[w["cond"]].get("name", w["cond"]), f"{round(w['high'] * 9 / 5 + 32)}°F", f"{round(w['low'] * 9 / 5 + 32)}°F", "Yes" if hard else "No"])
    return _table(rows, ["Day", "Weather", "High", "Low", "Hard night in the open?"], "tight")


def _camplog() -> str:
    return _table([[x, "", "", "", "", ""] for x in M["camp_log"]], ["Day", "Where, what camp", "Food left", "Council decided", "Rolls and results", "Who is worse or better"], "lined log")


def _feedback() -> str:
    return _table([[f"{i + 1}. {q}", "1  2  3  4  5", ""] for i, q in enumerate(M["questions"])], ["Question", "Score", "Comment"], "lined")


CSS = """
:root{--ink:#1d2128;--muted:#5b6370;--red:#8c1a2b;--line:#b9bec6}
*{box-sizing:border-box}body{margin:0;background:#fff;color:var(--ink);font:10.2pt/1.34 Georgia,"Times New Roman",serif}
.page{width:8.5in;min-height:11in;padding:.36in .6in .48in;position:relative;margin:0 auto;page-break-after:always;break-after:page;overflow-wrap:break-word}
h1{font-size:19pt;margin:0 0 6px;color:var(--ink)}h1.cover,.cover{font-size:34pt}h2{font-size:12pt;margin:8px 0 3px}p{margin:0 0 5px}ul,ol{margin:0 0 5px;padding-left:1.25em}li{margin-bottom:2px}
a{color:var(--red)}table{border-collapse:collapse;width:100%;margin:2px 0 5px;font-size:8.6pt;font-family:Arial,Helvetica,sans-serif}th,td{border:1px solid var(--line);padding:2px 4px;text-align:left;vertical-align:top}th{background:#eef0f2}
table.tight{font-size:8.2pt}table.tight td,table.tight th{padding:1px 4px}table.effects{font-size:7.3pt}table.effects td,table.effects th{padding:2px 3px}table.lined td{height:30px}table.log td{height:62px}
.foot{position:absolute;left:.6in;right:.6in;bottom:.28in;display:flex;justify-content:space-between;font:7.5pt Arial,sans-serif;color:var(--muted)}
.blank{height:1.1in;border:1px solid var(--line)}.blank.small{height:.4in}.sub{color:var(--muted)}.role{border-left:3px solid var(--red);padding-left:8px}
svg.mapsheet{max-height:none;width:auto;margin:2px auto}
.ctrs{display:flex;flex-wrap:wrap;gap:0;margin:2px 0 8px}.ctr{width:0.47in;height:0.30in;border:1px dashed #777;display:flex;flex-direction:column;align-items:center;justify-content:center;font:6.6pt/1.1 Arial,sans-serif;text-align:center;overflow:hidden}
.ctr b{font-size:6.2pt;white-space:nowrap}.ctr span{font-size:5.8pt}
.blankpage .sub{position:absolute;top:45%;left:.6in;right:.6in;text-align:center}
@media screen{.blankpage{display:none}}.ctr.bleed{background:#fde8e8}
section:has(#reference) p{font-size:11.2pt;line-height:1.38;margin-bottom:8px}.ctr.york{background:#e9eef7;border-left:4px solid #3c5a99}.ctr.clifford{background:#f7e6e6;border-left:4px solid #8c1a2b}.ctr.mark{background:#f4f4f4}.ctr.round{background:#fff6cc}
table.roster td{height:62px}table.roster .ticks{font-size:11pt;letter-spacing:1px;line-height:1.3}table.rounds td{text-align:center;height:24px}
.line{display:inline-block;border-bottom:1px solid var(--ink);min-width:3.2in;height:1em}.line.short{min-width:1.3in}.line.tiny{min-width:.45in}
.admonition{background:#f3f4f6;border-left:3px solid var(--red);padding:5px 9px;margin:5px 0}.admonition-title{font-weight:bold;margin:0}svg{display:block;width:100%;max-height:1.9in;margin:4px 0}
.getpdf{max-width:8.5in;margin:12px auto 0;padding:10px 14px;background:#fff6cc;border:1px solid #d9c46a;font:11pt/1.4 Arial,sans-serif}.getpdf a{font-weight:bold}
@media print{.getpdf{display:none}}
@media screen{body{background:#dfe2e6}.page{background:#fff;margin:12px auto;box-shadow:0 1px 4px #0003}}@media print{@page{size:Letter;margin:0}.page{margin:0}}
@media screen and (max-width:820px){.page{width:auto;min-height:0;padding:16px}.foot{position:static;margin-top:12px}table{display:block;overflow-x:auto}}
"""


def _getpdf(out: str) -> str:
    """On screen only: the packet as a PDF to download (build.py prints it beside this page)."""
    n = out.count('<section class="page')
    return (f'<div class="getpdf"><a href="{M["file"]}.pdf" download>Download the packet as a PDF</a> ({n} Letter pages). '
            'Print it at actual size (100%), on both sides: each character, the reference, the map and the counters then have a sheet of their own.</div>')

def render(d: Data, root: Path, mid: str = "ferrybridge") -> str:
    """The module mid as one printable page."""
    global M
    M = load_module(root, mid)
    T, X = M["team"], M["example"]
    team, v, tabs = _team(d), RB.values(d), RB.tables(d, {T["era"]})
    ex, bow, q = team[X["man"]], d.weapons[X["bow"]]["range"], d.units["quality"][M["foes"][0]["quality"]]
    v = {**v, "pt_version": M["version"], "pt_link": M["link"], "pt_link_short": M["link_short"], "pt_site": SITE, "pt_feedback": FEEDBACK, "pt_feedback_short": FEEDBACK.removeprefix("https://"),
         "pt_gil_attack": ex["attack"], "pt_gil_margin": ex["attack"] - X["roll"], "pt_foe_def": q["defence"], "pt_foe_nerve": q["nerve"], "pt_foe_pain": 2 * v["pain_step"],
         "pt_rations": d.supplies["rations"]["carried"][M["rations_era"]], "pt_bow_range": ", ".join(str(x) for x in bow),
         "aim_cost": d.wounds["combat"]["aim"]["cost"], "dead_days": d.disease.get("dead_days", 14),
         "pt_bleed_rates": _rates(d), "pt_track": M["battlemap"]["track"], "pt_short": bow[0], "pt_medium": bow[1], "pt_long": bow[2]}
    text = (root / M["text"]).read_text(encoding="utf-8")
    sheets = [_sheet(d, team[n], r, v) for n, r in _men()] + [_blank_sheet()]
    parts = {"hit": _hit(d), "armour": _armour(d), "effects": _effects(d), "sickness": _sickness(d), "map": _map(), "foes": _foes(d),
             "weather": _weather(d, root), "camplog": _camplog(), "feedback": _feedback(),
             "battlemap": _battlemap(), "counters": _counters(team), "roster": _roster(d)}
    text = text.replace("{{pt:sheets}}\n", "")
    keep = {}
    for k, h in parts.items():
        keep[f"@@{k}@@"] = h
        text = text.replace("{{pt:" + k + "}}", f"@@{k}@@")
    text = RB._fill(text, v, tabs, M["text"])
    foot = (f'<div class="foot"><span>{html.escape(M["footer"])}, version {html.escape(M["version"])}</span><span class="pageno">Page __PAGE__</span>'
            '<span>© 2026 Scott Wares. All rights reserved. Free to copy for playtesting.</span></div>')
    blank = ('<section class="page blankpage"><p class="sub">This page is left blank, so that printed on both sides each character, '
             'the quick reference, the map and the counters have a sheet of their own.</p>__FOOT__</section>')
    pages = []
    for i, md in enumerate(p for p in text.split("<!-- page -->") if p.strip()):
        body = markdown.markdown(md, extensions=["tables", "admonition", "attr_list"])
        for k, h in keep.items():
            body = body.replace(f"<p>{k}</p>", h).replace(k, h)
        own = any(f'id="{k}"' in body for k in ("reference", "battlemap", "counters"))
        pages.append((f'<section class="page">{body}__FOOT__</section>', own))
        if '{#camp}' in md or 'id="camp"' in body:
            pages += [(sh, True) for sh in sheets]
    # Printed on both sides, a page to hand out or cut up (each character, the blank sheet, the reference, the map,
    # the counters) gets a sheet of its own: it starts on a front, and its back is left blank.
    out = []
    for page, own in pages:
        if own and len(out) % 2:
            out.append(blank)
        out.append(page)
        if own:
            out.append(blank)
    out[0] = out[0].replace("<p>@@contents@@</p>", _contents(out))
    out = "".join(out)
    for n in range(1, out.count("__FOOT__") + 1):    # number the pages in order, one footer to a page
        out = out.replace("__FOOT__", foot.replace("__PAGE__", str(n)), 1)
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>{html.escape(M["title"])}</title><style>{CSS}</style></head><body>{_getpdf(out)}{out}'
            '</body></html>\n')
