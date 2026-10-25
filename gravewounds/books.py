"""The rule book split into books (data/books.yaml): the Rules, from the chapters in
templates/rules and its modules (templates/rules/modules), and a period book for each era group, built from the data. A chapter's
{{era:name}} table (rulebook.ERA_TABLES) is each era's: the Rules point to it, each period book
shows its own eras' rows, and the Rules' Other periods shows the rows of the eras no book holds
yet. Every number comes from the data, as in the Rules."""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from . import rulebook as RB
from .model import Data

ERA = re.compile(r"\{\{era:([a-z_]+)\}\}")
PICTURE = re.compile(r"\{\{picture:([a-z0-9_-]+)\}\}")
SIDEBAR = re.compile(r"\{\{sidebar:([a-z0-9-]+)\}\}")
HEADING = re.compile(r"^(#{1,3}) (.+?) \{#([^}]+)\}\s*$")
RULES_FILE = "rules.html"
RULES_DESC = ("The Grave Wounds rules: how to play, making a team, the fight, wounds and recovery, battles of hundreds, "
              "the march and the camp, weather and works, the other eras, guns and fire support, vehicles, night and the air, "
              "money by era, with a medieval retinue and a Vietnam rifle squad followed through.")


def load_books(d: Data, root: Path) -> dict:
    """data/books.yaml's books, checked: every era and battlefield named exists, and none is in two books."""
    path = root / "data" / "books.yaml"
    books = (yaml.safe_load(path.read_text(encoding="utf-8")) or {}).get("books") or {}
    seen_e, seen_f = {}, {}
    for bid, B in books.items():
        for e in B["eras"]:
            if e not in d.teams:
                raise ValueError(f"books.yaml: {bid}: no era {e}")
            if e in seen_e:
                raise ValueError(f"books.yaml: era {e} is in {seen_e[e]} and {bid}")
            seen_e[e] = bid
        for f in B.get("fields", []):
            if f not in d.fields:
                raise ValueError(f"books.yaml: {bid}: no battlefield {f}")
            if f in seen_f:
                raise ValueError(f"books.yaml: battlefield {f} is in {seen_f[f]} and {bid}")
            seen_f[f] = bid
    return books


def other_eras(d: Data, books: dict) -> list:
    """The eras no period book holds yet, in the team builder's order: the Rules' Other periods."""
    from .rulebook_later import _era_start
    held = {e for B in books.values() for e in B["eras"]}
    return sorted((e for e in d.teams if e not in held), key=lambda e: _era_start(d.teams[e]))


def render_all(d: Data, root: Path) -> dict:
    """{file name in dist: page}: the Rules and every period book."""
    books = load_books(d, root)
    out = {RULES_FILE: render_rules(d, root, books)}
    for bid, B in books.items():
        out[B["file"]] = render_book(d, root, books, bid)
    return out


# ---------- the Rules ----------

def chapters(root: Path) -> list:
    """The Rules' chapter files in order: the core (templates/rules), then the modules
    (templates/rules/modules)."""
    R = root / "templates" / "rules"
    return sorted(R.glob("*.md")) + sorted((R / "modules").glob("*.md"))


def _era_spots(text: str) -> list:
    """[(table, heading anchor, heading)] for each {{era:...}} in a chapter, with the section it sits in."""
    spots, anchor, title = [], None, None
    for line in text.splitlines():
        m = HEADING.match(line)
        if m:
            title, anchor = m.group(2), m.group(3)
        for name in ERA.findall(line):
            spots.append((name, anchor, title))
    return spots


def _book_links(books: dict, here: str) -> str:
    """The header's links to the other books."""
    links = [(RULES_FILE, "Rules")] + [(B["file"], B["title"]) for B in books.values()]
    return "".join(f'<a href="{f}">{t}</a>' for f, t in links if f != here)


def _pointer(name: str, books: dict, others: list) -> str:
    """Where a Rules chapter's era table is: each book's own rows, and Other periods' for the rest."""
    where = [f"[{B['title']}]({B['file']}#era-{name})" for B in books.values()]
    if others:
        where.append(f"[Other periods](#other-{name}) (until their books are written)")
    return f"*{RB.ERA_TABLES[name]}: each period's figures are in its book: {', '.join(where)}.*"


def _era_block(d: Data, name: str, tabs: dict, eras: list, prefix: str) -> str:
    """An era table's rows for these eras; prices as one section an era."""
    if name == "prices":
        parts = [f"### {d.teams[e]['name']} {{#{prefix}-prices-{e}}}\n\n{tabs[f'prices_{e}']}" for e in eras if f"prices_{e}" in tabs]
        return "\n\n".join(parts) or "None."
    t = tabs.get(name, "")
    if t.count("\n") <= 1:
        return "None."
    return _drop_era_column(t) if len(eras) == 1 else t


def _drop_era_column(t: str) -> str:
    """A one-era book's table needs no Era column (every row would say the same)."""
    rows = t.split("\n")
    if not rows[0].startswith("| Era |"):
        return t
    return "\n".join("|" + r.split("|", 2)[2] for r in rows)


def render_rules(d: Data, root: Path, books: dict) -> str:
    """dist/rules.html: the chapters, each era table a pointer to the books, and Other periods."""
    vals, tabs = RB.values(d), RB.tables(d)
    vals["books_list"] = ", ".join(f"[{B['title']}]({B['file']}) ({B['dates']})" for B in books.values()) or "none yet"
    others = other_eras(d, books)
    otabs = RB.tables(d, set(others))
    spots, parts = [], []
    for p in chapters(root):
        text = p.read_text(encoding="utf-8")
        spots += [(n, a, t) for n, a, t in _era_spots(text)]
        text = ERA.sub(lambda m: _pointer(m.group(1), books, others), text)
        text = SIDEBAR.sub(lambda m: _sidebar(root, m.group(1)), text)
        text = PICTURE.sub(lambda m: _picture(root, m.group(1)), text)
        parts.append(RB._fill(text, vals, tabs, p.name))
    if others:
        parts.append(_other_periods(d, otabs, others, spots))
    return _page(root, "\n\n".join(parts), books, RULES_FILE, "Grave Wounds Rules", RULES_DESC, "The Rules")


def _other_periods(d: Data, tabs: dict, eras: list, spots: list) -> str:
    """The Rules' appendix: the era tables' rows for the eras no period book holds yet."""
    names = ", ".join(d.teams[e]["name"] for e in eras)
    out = ["# Other periods {#other-periods}",
           f"Until each period has its own book, its figures are here: {names}. Each section belongs to the "
           "rule it is linked to."]
    for name, anchor, title in spots:
        out.append(f"## {RB.ERA_TABLES[name]} {{#other-{name}}}")
        out.append(f"For [{title}](#{anchor}).")
        out.append(_era_block(d, name, tabs, eras, "other"))
    return "\n\n".join(out)


# ---------- a period book ----------

def render_book(d: Data, root: Path, books: dict, bid: str) -> str:
    """dist/<file>: a period book: what it switches on, its armies' figures, its wound tables
    and its battlefields."""
    B = books[bid]
    tabs = RB.tables(d, set(B["eras"]))
    spots = []
    for p in chapters(root):
        spots += _era_spots(p.read_text(encoding="utf-8"))
    fields = B.get("fields", [])
    used = _book_tables(d, B)
    md = [f"# {B['title']}, {B['dates']} {{#{bid}}}",
          B["intro"],
          f"The battlefields: {', '.join(f'[{_short(d.fields[f], d)}](#field-{f})' for f in fields)}."
          if fields else "",
          _content(root, bid, "intro.md"),
          "## What is switched on {#switched-on}",
          B["switched_on"],
          _switched_on(d, B),
          f"# The armies {{#{bid}-armies}}",
          *_armies(d, B, tabs, spots),
          f"# Wound tables {{#{bid}-tables}}",
          _tables_intro(used),
          *[_table_note(d, t, B) for t in used],
          f"# Battlefields {{#{bid}-fields}}",
          "Each battlefield lays out on the [field map](field.html) under *Battlefield*. What follows is what "
          "the field and its phases hold, and, briefly, what happened there.",
          *[_field_section(d, f, root, bid) for f in fields]]
    title = f"{B['title']}, {B['dates']}"
    desc = f"Grave Wounds: {title}. " + B["intro"].split(":")[0] + "."
    return _page(root, "\n\n".join(x for x in md if x), books, B["file"], f"Grave Wounds: {B['title']}", desc, B["title"])


def _short(f: dict, d: Data | None = None) -> str:
    """'Crécy, 26 August 1346 (the Vallée des Clercs)' -> 'Crécy 1346'; with the day and month when
    another battlefield has the same short name ('The Great Redan, 18 June 1855')."""
    name = f["name"].split(",")[0].split(" (")[0]
    year = re.search(r"(1\d{3}|20\d{2})", f["id"])
    short = f"{name} {year.group(1)}" if year and year.group(1) not in name else name
    if d is not None and any(g is not f and _short(g) == short for g in d.fields.values()):
        return f["name"].split(" (")[0]
    return short


def _switched_on(d: Data, B: dict) -> str:
    rows = []
    for e in B["eras"]:
        E = d.teams[e]
        term = E["age"]["per_term"]
        rows.append([E["name"], ", ".join(r.get("short") or r["name"] for r in E["regions"]),
                     f"{term} year{'s' if term > 1 else ''}, from age {E['age']['start']}",
                     ", ".join(s["name"] for s in E["skills"] if s.get("combat"))])
    return RB._md(["Era", "Armies", "A career term", "Fighting skills"], rows)


TEAM_TABLES = (("careers", "Careers"), ("fq", "Followers"), ("ranks", "Ranks"), ("jobs", "Work between fights"),
               ("job_trouble", "Trouble at work"), ("skill_uses", "What each skill is for"))


def _armies(d: Data, B: dict, tabs: dict, spots: list) -> list:
    """The book's eras' own tables: careers, followers, ranks, work and skill uses (as the Rules'
    Making a team), each era's under its own heading when the book holds several; then each era
    table's rows, linked to the rule they belong to."""
    out, eras = [], B["eras"]
    own = {e: RB.team_tables(d, e) for e in eras}
    for name, title in TEAM_TABLES:
        have = [e for e in eras if name in own[e]]
        if not have:
            continue
        out.append(f"## {title} {{#era-{'careers' if name == 'careers' else 'followers' if name == 'fq' else name}}}")
        if name == "careers" and "medieval" in eras:
            out.append("The Rules' [Making a team](rules.html#team) uses these same tables for its running example.")
        if len(eras) == 1:
            out.append(own[have[0]][name])
        else:
            for e in have:
                out += [f"### {d.teams[e]['name']} {{#era-{name}-{e}}}", own[e][name]]
    done = set()
    for name, anchor, title in spots:
        if name in done:
            continue
        done.add(name)
        out += [f"## {RB.ERA_TABLES[name]} {{#era-{name}}}", f"For the Rules' [{title}](rules.html#{anchor}).",
                _era_block(d, name, tabs, B["eras"], "era")]
    return out


def _book_tables(d: Data, B: dict) -> list:
    """The wound tables this book's battles roll on, their evidence, and the evidence of the same wars."""
    ids = {d.fields[f]["table"] for f in B.get("fields", [])}
    ids |= {r["table"] for e in B["eras"] for r in d.teams[e]["regions"] if r.get("table")}
    wars = {d.tables[t].get("battle") for t in ids} | {d.fields[f].get("period") for f in B.get("fields", [])}
    ids |= {d.tables[t]["derived_from"] for t in list(ids) if d.tables[t].get("derived_from")}
    ids |= {k for k, t in d.tables.items() if t.get("battle") in wars}
    return sorted(ids, key=lambda k: float(d.tables[k].get("order", 99)))


def _tables_intro(used: list) -> str:
    return ("Each battle rolls its wounds on a table built from the record of that war, and these are the "
            "notes on where each one comes from. The tables themselves are in the [printed tables](tables.pdf) "
            "and the [wound roller](roller.html). A *gameplay-adjusted* table is re-weighted from bone evidence "
            "to stand for every blow that landed, not only the ones that marked bone; an *evidence* table is "
            "the record itself.")


CONF = {"historical": "taken directly from a source", "fitted": "estimated to match published summary figures",
        "extrapolated": "a design estimate from analogous evidence"}


def _table_note(d: Data, tid: str, B: dict) -> str:
    """The free note on a wound table: what it counts, how sure it is, its sources, who rolls on it."""
    t = d.tables[tid]
    fields = [f"[{_short(d.fields[f], d)}](#field-{f})" for f in B.get("fields", []) if d.fields[f]["table"] == tid]
    armies = [r.get("short") or r["name"] for e in B["eras"] for r in d.teams[e]["regions"] if r.get("table") == tid]
    used = []
    if fields:
        used.append("the battlefields of " + ", ".join(fields))
    if armies:
        used.append("the armies of " + ", ".join(armies))
    lines = [f"## {t['name']} {{#table-{tid}}}", t.get("context", "")]
    note = t.get("confidence_note") if not t.get("derived_from") else ""   # an adjusted table's method: Sources and Methods
    lines.append(f"*How sure:* {CONF.get(t.get('confidence'), t.get('confidence', ''))}." + (f" {note}" if note else ""))
    if t.get("derived_from"):
        lines.append(f"*Built from:* [{d.tables[t['derived_from']]['name']}](#table-{t['derived_from']}).")
    lines.append("*Rolled by:* " + ("; ".join(used) + "." if used else "no battle here: it is the evidence the others are built from."))
    if t.get("sources"):
        lines.append("*Sources:*\n\n" + "\n".join(f"- {s}" for s in t["sources"]))
    return "\n\n".join(x for x in lines if x)


# ---------- a battlefield ----------

def _story(fid: str, root: Path | None = None) -> tuple[str, str]:
    """From a battlefield file's opening comments: (what happened, briefly; how the field is drawn)."""
    path = (root or Path(__file__).resolve().parent.parent) / "data" / "fields" / f"{fid}.yaml"
    paras, cur = [], []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.startswith("#"):
            break
        text = line[1:].strip()
        if not text:
            if cur:
                paras.append(" ".join(cur))
            cur = []
        elif not text.startswith("Generated by"):
            cur.append(text)
    if cur:
        paras.append(" ".join(cur))
    what = next((p.split(":", 1)[1].strip() for p in paras if p.lower().startswith("what happened")), "")
    drawn = " ".join(p for p in paras if not p.lower().startswith("what happened"))
    drawn = re.sub(r"\b(?:NORTH|SOUTH|EAST|WEST)(?: AT THE TOP)?\b", lambda m: m.group(0).lower(), drawn)
    return what[:1].upper() + what[1:], drawn


COMPASS = {"N": "north", "NE": "north-east", "E": "east", "SE": "south-east", "S": "south", "SW": "south-west", "W": "west", "NW": "north-west"}


def _cell(x) -> str:
    return str(x).replace("|", "/")


def _field_section(d: Data, fid: str, root: Path | None = None, bid: str | None = None) -> str:
    F, U = d.fields[fid], d.units
    sides = F["sides"]
    W = F.get("weather") or {}
    cond = (d.weather.get("conditions") or {}).get(W.get("cond"), {}).get("name", W.get("cond", "fair"))
    wind = next((w["name"] for w in d.weather["winds"] if w["id"] == W.get("wind")), W.get("wind", "calm"))
    facts = [f"*The armies:* {sides[0]} and {sides[1]}."]
    if F.get("objective"):
        o = F["objective"]
        facts.append(f"*Fought for:* {o['name']}, attacked by the {sides[o['side']]}.")
    else:
        facts.append("*Fought for:* no one place the map can mark.")
    w, h = F["size"]
    facts.append(f"*The field:* {w} by {h} hexes of {U['hex_m']} m, about {round(w * U['hex_m'], -1):,} by {round(h * U['hex_m'] * 0.866, -1):,.0f} m, "
                 f"{ {'N': 'north', 'S': 'south', 'E': 'east', 'W': 'west'}.get(F.get('up', 'N'), F.get('up', 'N')) } at the top.")
    sky = f"{cond}, {wind.lower()}" + (f" from the {COMPASS.get(W['dir'], W['dir'])}" if W.get("dir") else "")
    if W.get("light"):
        sky += f", {W['light']}"
    facts.append(f"*The weather:* {sky}.")
    facts.append(f"*Wounds:* [{d.tables[F['table']]['name']}](#table-{F['table']}).")
    T = F.get("travel")
    if T and T.get("map") in d.maps:
        place = T["place"][:1].lower() + T["place"][1:] if T["place"].startswith("The ") else T["place"]
        facts.append(f"*On the travel map:* {d.maps[T['map']]['name']}, at {place}.")
    if F.get("ends"):
        facts.append(f"*The record:* the fight lasted about {F['ends']} exchanges (a minute each).")
    what, drawn = _story(fid)
    out = [f"## {F['name']} {{#field-{fid}}}", "\n".join(f"- {x}" for x in facts)]
    history = _content(root, bid, f"fields/{fid}.md") if root and bid else ""
    if history:                                   # the book's researched history (templates/books/<book>/fields)
        out.append(history)
    elif what:                                    # else the battlefield file's own short account
        out += ["### What happened", what]
    if drawn:
        out += ["### How the field is drawn", drawn]
    out += ["### The armies as drawn up", *_order_of_battle(d, F)]
    if F.get("phases"):
        out += ["### The phases", RB._md(["From exchange", "Phase", "What happens"],
                                         [[p["at"], _cell(p["name"]), _cell(p.get("note", ""))] for p in F["phases"]])]
    return "\n\n".join(out)


def _order_of_battle(d: Data, F: dict) -> list:
    """Each side's units, a table a side: men, quality, weapon, armour, formation, and the phase
    that brings them on."""
    comes = {}
    for p in F.get("phases") or []:
        for n in p.get("arrive") or []:
            comes[n] = p["name"]
    forms = d.units.get("formations", {})
    out = []
    for s, side in enumerate(F["sides"]):
        rows = []
        for u in F.get("units", []):
            if u.get("side") != s:
                continue
            weapon = (d.weapons.get(u.get("weapon")) or {}).get("short") or (d.weapons.get(u.get("weapon")) or {}).get("name", u.get("weapon", ""))
            kit = (d.armor["kits"].get(u.get("kit")) or {}).get("name", u.get("kit") or "—")
            form = (forms.get(u.get("formation")) or {}).get("name", u.get("formation", ""))
            rows.append([_cell(u["name"]), f"{u['men']:,}", u.get("quality", ""), _cell(weapon), _cell(kit), form,
                         _cell(comes.get(u["name"], "at the start"))])
        men = sum(u["men"] for u in F.get("units", []) if u.get("side") == s)
        out += [f"**The {side}** ({men:,} men):", RB._md(["Unit", "Men", "Quality", "Weapon", "Armour", "Formation", "Comes on"], rows)]
    return out


# ---------- the book's own prose, sidebars and pictures ----------

def _content(root: Path, bid: str, name: str) -> str:
    """templates/books/<book>/<name> (a period book's own prose), its pictures filled; "" if there is none."""
    path = root / "templates" / "books" / bid / name
    if not path.exists():
        return ""
    return PICTURE.sub(lambda m: _picture(root, m.group(1)), path.read_text(encoding="utf-8")).strip()


def _sidebar(root: Path, name: str) -> str:
    """templates/books/rules-sidebars/<name>.md: a story set beside a rule in the Rules."""
    path = root / "templates" / "books" / "rules-sidebars" / f"{name}.md"
    if not path.exists():
        raise ValueError(f"no sidebar {name} (templates/books/rules-sidebars/{name}.md)")
    return path.read_text(encoding="utf-8").strip()


def _picture_books(root: Path) -> dict:
    """{data/pictures file stem: its book}: 'rules', '<book>-intro', or a battlefield's id."""
    books = (yaml.safe_load((root / "data" / "books.yaml").read_text(encoding="utf-8")) or {}).get("books") or {}
    out = {"rules": "rules"}
    for bid, B in books.items():
        out[f"{bid}-intro"] = bid
        out.update({f: bid for f in B.get("fields", [])})
    return out


def load_pictures(root: Path) -> dict:
    """{id: picture}: data/pictures/*.yaml. A picture's file lives in images/books/<book>/, the book
    being its YAML file's: rules.yaml the Rules', <book>-intro.yaml that book's, <battlefield>.yaml
    the book that holds the battlefield."""
    out, where = {}, _picture_books(root)
    for path in sorted((root / "data" / "pictures").glob("*.yaml")):
        folder = where.get(path.stem)
        if folder is None:
            raise ValueError(f"data/pictures/{path.name}: no book holds it (name it rules, <book>-intro or a battlefield id)")
        for P in yaml.safe_load(path.read_text(encoding="utf-8")) or []:
            for k in ("id", "file", "caption", "credit", "licence", "source"):
                if not P.get(k):
                    raise ValueError(f"{path.name}: picture {P.get('id', '?')} has no {k}")
            if P["id"] in out:
                raise ValueError(f"{path.name}: picture {P['id']} is defined twice")
            out[P["id"]] = {**P, "path": f"images/books/{folder}/{P['file']}"}
    return out


def _esc(x: str) -> str:
    return str(x).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _picture(root: Path, pid: str) -> str:
    """A picture as a captioned figure, credited; a captioned slot until its file is in images/."""
    P = load_pictures(root).get(pid)
    if P is None:
        raise ValueError(f"no picture {pid} in data/pictures")
    credit = (f'<span class="credit">{_esc(P["credit"])}. {_esc(P["licence"])}. '
              f'<a href="{_esc(P["source"])}">Source</a>.</span>')
    cap = f"<figcaption>{_esc(P['caption'])} {credit}</figcaption>"
    if (root / P["path"]).exists():
        img = f'<img src="{_esc(P["path"])}" alt="{_esc(P.get("alt") or P["caption"])}" loading="lazy">'
        return f'\n<figure class="pic">{img}{cap}</figure>\n'
    return (f'\n<figure class="pic slot"><div class="slot-box" role="img" aria-label="{_esc(P.get("alt") or P["caption"])}">'
            f'Picture to come<br><code>{_esc(P["path"])}</code></div>{cap}</figure>\n')


# ---------- the page ----------

def _page(root: Path, body: str, books: dict, here: str, title: str, desc: str, h1: str) -> str:
    import markdown
    md = markdown.Markdown(extensions=["tables", "admonition", "toc", "attr_list"], extension_configs={"toc": {"toc_depth": "1-2"}})
    html = md.convert(body)
    idx = RB.index_html(html)
    toc = md.toc.replace("</ul>\n</div>", '<li><a href="#index">Index</a></li>\n</ul>\n</div>') if idx else md.toc
    page = (root / "templates" / "rules.html").read_text(encoding="utf-8")
    return (page.replace("{{TITLE}}", title).replace("{{DESC}}", desc.replace('"', "&quot;")).replace("{{H1}}", h1)
            .replace("{{BOOKS}}", _book_links(books, here)).replace("{{TOC}}", toc).replace("{{BODY}}", html + idx))
