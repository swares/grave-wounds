"""Making a man on paper: an era's tables for the five steps of Making a team (the Rules), as the
team builder rolls them (templates/team.js, gravewounds/team.py), from data/teams.

The tables: each skill's characteristic and divisor; the origins on d100 (equal shares, the men's
and the women's lists); each career's main and second skills, wound chance, kit and weapon by
side; and each career's term events on d100. The period books print them under Making a team
(books.TEAM_TABLES); dist/makeaman.html prints one era's with the steps and a blank sheet.
"""
from __future__ import annotations

from html import escape as esc

from .model import Data


def _names(d: Data, eid: str) -> dict:
    E = d.teams[eid]
    return {**{c["id"]: c["name"] for c in E["characteristics"]}, **{s["id"]: s["name"] for s in E["skills"]}}


def _effect(names: dict, x: dict) -> str:
    """{'text': 'Strong back', 'str': 10} -> 'Strong back (Strength +10)'."""
    mods = [f"{names.get(k, k)} {v:+d}" for k, v in x.items() if k != "text"]
    return x["text"] + (f" ({', '.join(mods)})" if mods else "")


def d100_spans(n: int) -> list[str]:
    """The d100 spans of n equal rows, as the team builder reads them (row floor((roll-1)*n/100))."""
    rows = [[] for _ in range(n)]
    for r in range(1, 101):
        rows[(r - 1) * n // 100].append(r)
    return [(f"{x[0]:02d}" if x[0] == x[-1] else f"{x[0]:02d}–{x[-1]:02d}").replace("100", "00") for x in rows]


def _by_side(d: Data, eid: str, v, what) -> str:
    """A career's kit or weapon by side: the default, then the sides that differ."""
    if not isinstance(v, dict):
        return what(v)
    regions = {r["id"]: r["name"].split(" (")[0] for r in d.teams[eid]["regions"]}
    base = v.get("default")
    groups = {}
    for rid, x in v.items():
        if rid != "default" and x != base and rid in regions:
            groups.setdefault(x, []).append(regions[rid])
    return "; ".join([what(base)] + [f"{', '.join(rs)}: {what(x)}" for x, rs in groups.items()])


def rows(d: Data, eid: str) -> dict:
    """The era's tables as (head, rows), by name."""
    E, names = d.teams[eid], _names(d, eid)
    kit = lambda k: d.armor["kits"].get(k, {}).get("name", k or "none")
    wpn = lambda w: d.weapons.get(w, {}).get("short", w or "none")
    out = {"skills": (["Skill", "Starts at", "Fighting"],
                      [[s["name"], f"{names[s['of']]} ÷ {s['div']}", "yes" if s.get("combat") else ""] for s in E["skills"]])}
    for sex, key in (("m", "origins"), ("f", "origins_f")):
        os_ = [o for o in E["origins"] if (o.get("who") or sex) == sex]
        if sex == "f" and not any(o.get("who") == "f" for o in E["origins"]):
            continue
        out[key] = (["d100", "Origin", "Skill +" + str(E["gain"]), "Trait", "Drawback"],
                    [[sp, o["name"], names.get(o["gain"], o["gain"]), _effect(names, o["trait"]), _effect(names, o["drawback"])]
                     for sp, o in zip(d100_spans(len(os_)), os_)])
    out["career_kit"] = (["Career", "Main", "Second", "Old wound", "Kit", "Weapon"],
                         [[c["name"], names[c["main"]], names[c["second"]], f"{c['wound']}% ({wpn(c['wound_weapon'])})", _by_side(d, eid, c["kit"], kit), _by_side(d, eid, c["weapon"], wpn)]
                          for c in E["careers"]])
    terms = []
    for c in E["careers"]:
        lo = 1
        for t in c["terms"]:
            span = f"{lo:02d}–{t['to']:02d}".replace("100", "00") if t["to"] > lo else f"{lo:02d}"
            terms.append([c["name"], span, names.get(t["skill"], t["skill"]), t["text"] + (" *" if t.get("wound") else "")])
            lo = t["to"] + 1
    out["terms"] = (["Career", "d100", "Skill +" + str(E["gain"]), "Event (* an old wound)"], terms)
    out["sides"] = (["Side", "Old wounds roll on"], [[r["name"], d.tables.get(r.get("table"), {}).get("name", r.get("table") or "-")] for r in E["regions"]])
    return out


def _md(head, body) -> str:
    return "\n".join(["| " + " | ".join(head) + " |", "|" + "---|" * len(head)] + ["| " + " | ".join(str(c).replace("|", "/") for c in r) + " |" for r in body])


def book_tables(d: Data, eid: str) -> dict:
    """For a period book's Making a team: the tables as Markdown, by name."""
    R = rows(d, eid)
    return {k: _md(*v) for k, v in R.items()}


TITLES = {"skills": "Skills: where each starts", "origins": "Origins (d100)", "origins_f": "Origins of a woman (d100)",
          "career_kit": "Careers: skills, old-wound chance, kit and weapon", "terms": "Career terms (d100)", "sides": "Sides and their wound tables"}


def _table(head, body) -> str:
    return ("<table><thead><tr>" + "".join(f"<th>{esc(h)}</th>" for h in head) + "</tr></thead><tbody>"
            + "".join("<tr>" + "".join(f"<td>{esc(str(c))}</td>" for c in r) + "</tr>" for r in body) + "</tbody></table>")


def steps(d: Data, eid: str) -> str:
    """The five steps on one page, with the era's own figures."""
    E = d.teams[eid]
    chars = ", ".join(c["name"] for c in E["characteristics"])
    lasting = ", ".join(f"{d.teams[eid]['characteristics'][[c['id'] for c in E['characteristics']].index(v)]['name']} for the {k}" for k, v in E["lasting_from"].items())
    scar = E["old_wound"][0]["to"]
    defence = " or ".join(_names(d, eid)[x] for x in E.get("defence", []))
    return f"""<ol class="steps">
<li><b>Characteristics.</b> Roll 3d6 × 5 for each in order ({chars}; {E['stat_range'][0]} to 90), or place the array {', '.join(map(str, E['array']))}, highest where his career wants it.</li>
<li><b>Side and career.</b> Choose his side (its army) and his career. A woman's career is open only where the side's women's rules allow it (the Rules' Women under arms).</li>
<li><b>Origin.</b> Roll d100 on the origin table: one skill +{E['gain']}, a trait and a drawback.</li>
<li><b>Career terms.</b> The leader serves three, the others one or two. Each term: the main skill +{E['first_term']} in the first term, +{E['term_main']} after; the second skill +{E['term_second']}; and d100 on the career's terms for an event, its skill +{E['gain']}. An event he has had already moves to the next row down (from the last, to the first). He starts at about {E['age']['start']} and is {E['age']['per_term']} years older a term.</li>
<li><b>Old wounds.</b> Each term, an event marked * leaves an old wound, and so does a d100 at or under the career's old-wound chance. Roll its place on his side's wound table (the printed tables), in the column of the career's weapon in brackets (the first column if it has none), then d100: up to {scar} a healed scar; above, a lasting hurt, −{E['lasting']} to {lasting}.</li>
<li><b>Skills and kit.</b> Each skill starts at its characteristic ÷ the divisor (rounded down), plus what he gained, to {E['skill_max']} at most. His defence is his {defence}. Kit and weapon come with his career and side; a purse of Days for each term (the Rules' Money).</li>
</ol>"""


def sheet(d: Data, eid: str) -> str:
    E = d.teams[eid]
    chars = "".join(f"<tr><th>{esc(c['name'])}</th><td></td></tr>" for c in E["characteristics"])
    skills = "".join(f"<tr><th>{esc(s['name'])}</th><td></td></tr>" for s in E["skills"])
    lines = "".join(f"<tr><th>{x}</th><td></td></tr>" for x in ("Name", "Side", "Career", "Terms and age", "Origin", "Trait", "Drawback",
                                                                  "Events", "Old wounds", "Kit", "Weapon", "Defence", "Blood", "Purse (Days)"))
    return (f"<div class='sheet'><h3>A man: {esc(E['name'])}</h3><div class='cols'><table class='blank'>{lines}</table>"
            f"<div><table class='blank'>{chars}</table><table class='blank'>{skills}</table></div></div></div>")


def render(d: Data, copyright_: str) -> str:
    opts = "".join(f"<option value='{esc(e)}'>{esc(T['name'])}</option>" for e, T in d.teams.items())
    secs = ""
    for eid, E in d.teams.items():
        R = rows(d, eid)
        tabs = "".join(f"<h3>{esc(TITLES[k])}</h3>{_table(*R[k])}" for k in TITLES if k in R)
        secs += (f"<section data-era='{esc(eid)}'><h2>{esc(E['name'])}</h2><div class='page'>{steps(d, eid)}</div>"
                 f"<div class='tables'>{tabs}</div>{sheet(d, eid)}</section>")
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grave Wounds: making a man on paper</title>
<style>body{{font:14px/1.35 Georgia,serif;max-width:60em;margin:1em auto;padding:0 16px;color:#222;background:#fff}}h1{{font-size:1.5em;margin:0}}
h2{{font-size:1.25em;margin:1.2em 0 .2em;border-bottom:2px solid #555}}h3{{font-size:1em;margin:.9em 0 .3em}}.small{{font-size:.85em}}
.bar{{display:flex;flex-wrap:wrap;gap:.6em 1.2em;align-items:center;margin:.6em 0;padding:.5em;background:#f1ede4}}
.steps li{{margin:.3em 0}}.wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:.88em;margin-bottom:.4em}}th,td{{border:1px solid #999;padding:3px 5px;text-align:left;vertical-align:top}}
thead th{{background:#e6e0d2}}table.blank th{{width:9em;background:#f6f3ec;font-weight:normal}}table.blank td{{height:1.5em}}
.cols{{display:grid;grid-template-columns:1fr 1fr;gap:1em}}@media(max-width:640px){{.cols{{grid-template-columns:1fr}}}}
section.off{{display:none}}footer{{font-size:.8em;margin-top:1em}}
@media print{{.bar{{display:none}}body{{margin:0;max-width:none;font-size:11px}}section:not(.off)~section:not(.off){{break-before:page}}.tables,.sheet{{break-before:page}}tr{{break-inside:avoid}}}}</style></head><body>
<h1>Making a man on paper</h1><p class="small">Grave Wounds: the steps of the Rules' <a href="rules.html#five-steps">Making a team</a>, with one era's tables and a blank sheet, for a table with no team builder. Pick an era and print it.</p>
<div class="bar"><label>Era <select id="era"><option value="">Every era</option>{opts}</select></label><button type="button" onclick="print()">Print</button></div>
<div class="wrap">{secs}</div>
<footer>{esc(copyright_)}</footer>
<script>
(function () {{
  var sel = document.getElementById("era");
  function fromHash() {{ var h = location.hash.slice(1); if (h && sel.querySelector("option[value='" + h + "']")) sel.value = h; }}
  function show() {{
    document.querySelectorAll("section[data-era]").forEach(function (s) {{ s.classList.toggle("off", !!sel.value && s.dataset.era !== sel.value); }});
    try {{ localStorage.setItem("gw-makeaman", sel.value); }} catch (e) {{}}
    try {{ history.replaceState(null, "", sel.value ? "#" + sel.value : location.pathname + location.search); }} catch (e) {{}}
  }}
  try {{ sel.value = localStorage.getItem("gw-makeaman") || ""; }} catch (e) {{}}
  fromHash();
  sel.onchange = show;
  window.addEventListener("hashchange", function () {{ fromHash(); show(); }});
  show();
}})();
</script></body></html>
"""
