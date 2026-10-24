"""How to play (templates/guide.html) against the pages: every control it names is still on them.

    python3 tools/guide/check.py

Each <b class="ui">...</b> in the guide is a button, box or choice on a page. It must appear in the
pages' own source (templates/*.html, *.js) as written, or the guide has gone stale. Its links to
its own sections must land, and every page's top bar must link to it. Exits non-zero on any miss.
"""
import html, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
guide = (ROOT / "templates" / "guide.html").read_text(encoding="utf-8")
pages = "\n".join(p.read_text(encoding="utf-8") for p in sorted((ROOT / "templates").glob("*")) if p.suffix in (".html", ".js") and p.name != "guide.html")
labels = sorted({html.unescape(x).strip() for x in re.findall(r'<b class="ui">([^<]+)</b>', guide)})
missing = [x for x in labels if x not in pages and html.escape(x, quote=False) not in pages and x.replace("'", "\\'") not in pages]
ids = set(re.findall(r'\sid="([^"]+)"', guide))
dead = [a for a in re.findall(r'href="#([^"]+)"', guide) if a not in ids]
unlinked = [p.name for p in (ROOT / "templates").glob("*.html") if p.name in ("campaign.html", "roller.html", "travel.html", "field.html", "team.html", "rules.html") and 'href="guide.html"' not in p.read_text(encoding="utf-8")]
print(f"{len(labels)} controls named in the guide")
for x in missing:
    print("FAIL not on any page:", x)
for a in dead:
    print("FAIL a link to no section: #" + a)
for n in unlinked:
    print("FAIL no How to play link in", n)
bad = missing or dead or unlinked
print("all found" if not bad else "the guide needs updating")
sys.exit(1 if bad else 0)
