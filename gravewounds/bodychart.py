"""The body hit-location chart drawn as SVG with no page: the same shapes as the roller's (templates/roller.html,
shapes), shaded by a table's odds for each place, for the books and the printed tables. A heat map of where the
wounds fell, from the records."""
from __future__ import annotations

import html

from .engine import table_ranges
from .model import Data

C = 90


def _shapes() -> list[tuple[str, str]]:
    """(location id, SVG element) for each place on the body, front and back (as roller.html shapes)."""
    s: list[tuple[str, str]] = []
    mirror = lambda x, w: 2 * C - x - w

    def rect(i, x, y, w, h, r=4):
        s.append((i, f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}"/>'))

    def pair(base, x, y, w, h, r):
        rect(base + "_r", x, y, w, h, r)
        rect(base + "_l", mirror(x, w), y, w, h, r)

    s.append(("skull_r", f'<path d="M{C},12 A22,27 0 0 0 {C},66 Z"/>'))
    s.append(("skull_l", f'<path d="M{C},12 A22,27 0 0 1 {C},66 Z"/>'))
    s.append(("face", f'<ellipse cx="{C}" cy="46" rx="12" ry="14"/>'))
    rect("neck", C - 8, 66, 16, 14, 3)
    s.append(("shoulder_r", f'<ellipse cx="{C - 27}" cy="90" rx="13" ry="11"/>'))
    s.append(("shoulder_l", f'<ellipse cx="{C + 27}" cy="90" rx="13" ry="11"/>'))
    rect("chest_r", C - 22, 80, 22, 46, 3)
    rect("chest_l", C, 80, 22, 46, 3)
    rect("abdomen", C - 22, 126, 44, 40, 3)
    rect("groin", C - 19, 166, 38, 22, 6)
    pair("upper_arm", C - 45, 100, 14, 50, 6)
    pair("forearm", C - 49, 152, 14, 52, 6)
    s.append(("hand_r", f'<ellipse cx="{C - 42}" cy="216" rx="9" ry="12"/>'))
    s.append(("hand_l", f'<ellipse cx="{C + 42}" cy="216" rx="9" ry="12"/>'))
    pair("thigh", C - 20, 190, 18, 68, 6)
    pair("knee", C - 19, 260, 16, 17, 6)
    pair("lower_leg", C - 18, 279, 14, 78, 6)
    s.append(("foot_r", f'<ellipse cx="{C - 15}" cy="366" rx="12" ry="7"/>'))
    s.append(("foot_l", f'<ellipse cx="{C + 15}" cy="366" rx="12" ry="7"/>'))
    rect("back_upper", 172, 80, 34, 46, 3)
    rect("back_lower", 172, 126, 34, 40, 3)
    return s


def odds(d: Data, table_id: str, weapon: str | None = None) -> dict:
    """{location id: % of hits} on the table (for that weapon's column, or the table's own weights)."""
    return {r["id"]: r["pct"] for r in table_ranges(d, table_id, weapon)}


def svg(d: Data, table_id: str, weapon: str | None = None, title: str = "", width: int = 150) -> str:
    """The chart for this table (and weapon): each place shaded by its share of the hits, the darkest the
    most; each place names itself and its % on hover; the three likeliest are said in the label."""
    p = odds(d, table_id, weapon)
    top = max(p.values()) if p else 1
    parts = []
    for i, el in _shapes():
        pct = p.get(i, 0)
        alpha = 0.06 + 0.84 * pct / top if top else 0.06
        name = html.escape(d.loc[i]["name"])
        parts.append(el.replace("/>", f' fill="#9b2226" fill-opacity="{alpha:.3f}" stroke="#555" stroke-width="0.6"><title>{name}: {pct:g}%</title></'
                                + el[1:el.index(" ")] + ">"))
    best = sorted(p.items(), key=lambda kv: -kv[1])[:3]
    said = "; ".join(f"{d.loc[k]['name'].lower()} {v:g}%" for k, v in best)
    label = html.escape(f"{title}: " if title else "") + "where the wounds fell, darkest most often: " + html.escape(said)
    return (f'<svg class="bodychart" viewBox="0 0 220 382" width="{width}" role="img" aria-label="{label}">'
            f'<text x="{C - 46}" y="20" font-size="10" fill="#666">R</text><text x="{C + 40}" y="20" font-size="10" fill="#666">L</text>'
            f'<text x="189" y="72" font-size="9" text-anchor="middle" fill="#666" letter-spacing="1">BACK</text>'
            + "".join(parts) + "</svg>")
