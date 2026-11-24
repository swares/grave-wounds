"""dist/armoury.html: the common weapons and armour of each era, as a printed booklet.

An era's common weapons and armour are what its careers start with (data/teams, `weapon` and
`kit`, every side's), the weapons of the skills its careers train in (`weapon_skill`, a career's
main or second skill or one its terms teach: a rifleman's bayonet), what its price list sells (data/equipment, an item's
`weapon` or `kit`), and what the guns among them fight with while reloading (`close`). Each line carries the game's
figures; the data's own note goes under it, shown or hidden by the page's Show notes switch. One era
is shown (and printed) at a time; its period book holds the war itself.
"""
from __future__ import annotations

from html import escape as esc

from .model import Data

THREATS = [("fragment", "Fragment"), ("pistol", "Pistol"), ("rifle", "Rifle"), ("rifle_ap", "Rifle, AP")]
MECH = ["cut", "pierce", "crush", "ballistic"]


def _ids(v) -> list[str]:
    """A career's `weapon` or `kit` (one id, a list, or ids by side), or an item's, as ids."""
    if isinstance(v, dict):
        return [x for y in v.values() for x in _ids(y)]
    if isinstance(v, list):
        return [x for y in v for x in _ids(y)]
    return [v] if v else []


def era_items(d: Data, era: str) -> tuple[list[str], list[str]]:
    """An era's common weapons and armour kits, in a stable order (as the data lists them)."""
    ws, ks = [], []
    T = d.teams[era]
    trained = {c.get(k) for c in T["careers"] for k in ("main", "second")} | {t.get("skill") for c in T["careers"] for t in c["terms"]}
    for c in T["careers"]:
        ws += _ids(c.get("weapon"))
        ks += _ids(c.get("kit"))
    ws += [w for w, sk in (T.get("weapon_skill") or {}).items() if sk in trained and d.weapons.get(w, {}).get("melee") != "unarmed"]   # the weapons of a skill a career trains in (a rifleman's bayonet)
    for i in (d.equipment.get(era) or {}).get("items", []):
        ws += _ids(i.get("weapon"))
        ks += _ids(i.get("kit"))
    for w in list(ws):
        ws += [x for x in (d.weapons.get(w) or {}).get("close", []) if x in d.weapons]
    ws = [w for w in dict.fromkeys(ws) if w in d.weapons]
    ks = [k for k in dict.fromkeys(ks) if k in d.armor["kits"]]
    return ws, ks


def weapon_use(d: Data, w: dict) -> str:
    """Reach in a fight, or range bands in hexes, as the roller says it."""
    if "reach" in w:
        return f"Reach {w['reach']}"
    if w.get("range"):
        hex_m = d.wounds["combat"]["move"]["hex_m"]
        s = f"Range {' / '.join(map(str, w['range']))} hexes (to {w['range'][-1] * hex_m:,} m)"
        return s + (f", not under {w['min_range']}" if w.get("min_range") else "") + (", off the map" if w.get("off_map") else "")
    return "Off the map" if w.get("off_map") else "-"


def against_armour(d: Data, w: dict) -> str:
    """What the weapon does to armour: its threat (a firearm's rating column), steps it beats."""
    out = []
    if w.get("threat"):
        out.append(f"as {dict(THREATS).get(w['threat'], w['threat']).lower()}")
    for m, n in (w.get("armor_defeat") or {}).items():
        only = ""
        if w.get("defeat_only"):
            only = " (" + ", ".join(d.armor["materials"][x]["name"].split(" (")[0].lower() for x in w["defeat_only"] if x in d.armor["materials"]) + " only)"
        out.append(f"beats {n} {m} step{'s' if n != 1 else ''}{only}")
    return "; ".join(out) or "-"


def _layers(v) -> list[tuple[str, int | None]]:
    """A kit slot (a material, one with a cover, or layers) as (material, cover) pairs."""
    if isinstance(v, list):
        return [x for y in v for x in _layers(y)]
    if isinstance(v, dict):
        return [(v.get("material"), v.get("cover"))]
    return [(v, None)]


def _slot(d: Data, slot: str, v) -> str:
    """'Chest, upper back: Plate (50%), then Mail over padding'."""
    parts = [d.armor["materials"].get(m, {}).get("name", m) + (f" ({c}%)" if c else "") for m, c in _layers(v)]
    return f"{d.armor['slots'].get(slot, slot)}: " + ", then ".join(parts)


def _materials(d: Data, kits: list[str]) -> list[str]:
    ms = [m for k in kits for v in d.armor["kits"][k].get("slots", {}).values() for m, _ in _layers(v)]
    return [m for m in dict.fromkeys(ms) if m in d.armor["materials"]]


def era_section(d: Data, era: str, book: dict | None) -> str:
    T = d.teams[era]
    ws, ks = era_items(d, era)
    rows = ""
    for wid in ws:
        w = d.weapons[wid]
        mix = ", ".join(f"{m} {p}%" for m, p in w["mechanisms"].items())
        close = ", ".join(d.weapons[x]["short"] for x in w.get("close", []) if x in d.weapons) or "-"
        rate = f"{w['shots_a_minute']} a minute" if w.get("shots_a_minute") else "-"
        rows += (f"<tr><th>{esc(w['name'])}</th><td>{esc(weapon_use(d, w))}</td><td>{esc(mix)}</td><td>{esc(rate)}</td>"
                 f"<td>{'-' if w.get('off_map') else 'Two' if w.get('two_handed') else 'One'}</td><td>{esc(against_armour(d, w))}</td><td>{esc(close)}</td></tr>")
        if w.get("notes"):
            rows += f"<tr class='note'><td colspan='7'>{esc(w['notes'])}</td></tr>"
    kits = ""
    for kid in ks:
        k = d.armor["kits"][kid]
        cov = "; ".join(_slot(d, s, v) for s, v in k.get("slots", {}).items()) or "Nothing"
        kits += f"<tr><th>{esc(k['name'])}</th><td>{esc(cov)}</td></tr>"
        if k.get("notes"):
            kits += f"<tr class='note'><td colspan='2'>{esc(k['notes'])}</td></tr>"
    ms = _materials(d, ks)
    mats = ""
    if ms:
        head = "".join(f"<th>{m.title()}</th>" for m in MECH) + "".join(f"<th>{n}</th>" for _, n in THREATS)
        body = ""
        for m in ms:
            M = d.armor["materials"][m]
            body += (f"<tr><th>{esc(M['name'])}</th>" + "".join(f"<td>{M.get(x, 0)}</td>" for x in MECH)
                     + "".join(f"<td>{(M.get('threats') or {}).get(t, 0)}</td>" for t, _ in THREATS) + "</tr>")
        mats = (f"<h3>Armour steps by material</h3><p class='small'>Steps a hit's severity is lowered by. A firearm reads its threat's column, not Ballistic.</p>"
                f"<table class='num'><thead><tr><th>Material</th>{head}</tr></thead><tbody>{body}</tbody></table>")
    link = f" <a class='book' href='{esc(book['file'])}'>The war itself: {esc(book['title'])}</a>" if book else ""
    return (f"<section data-era='{esc(era)}'><h2>{esc(T['name'])}</h2><p class='small'>{len(ws)} weapons and {len(ks)} armour kits: "
            f"what its careers start with or train in, and its price list sells.{link}</p>"
            f"<h3>Weapons</h3><table><thead><tr><th>Weapon</th><th>Use</th><th>Strikes</th><th>Rate</th><th>Hands</th><th>Against armour</th><th>While reloading</th></tr></thead><tbody>{rows}</tbody></table>"
            f"<h3>Armour kits</h3><table><thead><tr><th>Kit</th><th>Covers (a share is the hits there that meet it; then: the next layer)</th></tr></thead><tbody>{kits}</tbody></table>{mats}</section>")


def render(d: Data, books: dict, copyright_: str) -> str:
    by_era = {e: B for B in books.values() for e in B["eras"]}
    opts = "".join(f"<option value='{esc(e)}'>{esc(T['name'])}</option>" for e, T in d.teams.items())
    sections = "".join(era_section(d, e, by_era.get(e)) for e in d.teams)
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Grave Wounds: the armoury</title>
<style>body{{font:14px/1.35 Georgia,serif;max-width:60em;margin:1em auto;padding:0 16px;color:#222;background:#fff}}h1{{font-size:1.5em;margin:0}}
h2{{font-size:1.25em;margin:1.2em 0 .2em;border-bottom:2px solid #555}}h3{{font-size:1em;margin:.9em 0 .3em}}.small{{font-size:.85em;margin:.2em 0}}
.bar{{display:flex;flex-wrap:wrap;gap:.6em 1.2em;align-items:center;margin:.6em 0;padding:.5em;background:#f1ede4}}
.wrap{{overflow-x:auto}}table{{border-collapse:collapse;width:100%;font-size:.9em}}th,td{{border:1px solid #999;padding:3px 5px;text-align:left;vertical-align:top}}
thead th{{background:#e6e0d2}}tbody th{{font-weight:bold}}tr.note td{{font-size:.85em;color:#444;border-top:0;padding-left:1.5em}}table.num td{{text-align:center}}
body.nonotes tr.note{{display:none}}section.off{{display:none}}a.book{{margin-left:.4em}}footer{{font-size:.8em;margin-top:1em}}
@media print{{.bar{{display:none}}body{{margin:0;max-width:none;font-size:11px}}section:not(.off)~section:not(.off){{break-before:page}}tr{{break-inside:avoid}}}}</style></head><body>
<h1>The armoury</h1><p class="small">Grave Wounds: each era's common weapons and armour, with the game's figures. Pick an era and print it.</p>
<div class="bar"><label>Era <select id="era"><option value="">Every era</option>{opts}</select></label>
<label><input type="checkbox" id="notes" checked> Show notes</label><button type="button" onclick="print()">Print</button></div>
<div class="wrap">{sections}</div>
<footer>{esc(copyright_)} Hexes are {d.wounds['combat']['move']['hex_m']} m on the roller's map; range bands are short, medium and long.</footer>
<script>
(function () {{
  var sel = document.getElementById("era"), notes = document.getElementById("notes");
  function show() {{
    document.querySelectorAll("section[data-era]").forEach(function (s) {{ s.classList.toggle("off", !!sel.value && s.dataset.era !== sel.value); }});
    document.body.classList.toggle("nonotes", !notes.checked);
    try {{ localStorage.setItem("gw-armoury", JSON.stringify({{era: sel.value, notes: notes.checked}})); }} catch (e) {{}}
    try {{ history.replaceState(null, "", sel.value ? "#" + sel.value : location.pathname + location.search); }} catch (e) {{}}
  }}
  function fromHash() {{ var h = location.hash.slice(1); if (h && sel.querySelector("option[value='" + h + "']")) sel.value = h; }}
  try {{ var k = JSON.parse(localStorage.getItem("gw-armoury") || "null"); if (k) {{ sel.value = k.era || ""; notes.checked = k.notes !== false; }} }} catch (e) {{}}
  fromHash();
  sel.onchange = notes.onchange = show;
  window.addEventListener("hashchange", function () {{ fromHash(); show(); }});
  show();
}})();
</script></body></html>
"""
