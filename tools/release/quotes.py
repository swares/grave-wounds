"""Every direct quotation printed in the period books and the Rules, for the release check of what may be
reprinted (docs/backlog.md, Sources and Methods: the infringement check).

python3 tools/release/quotes.py [min words]   (default 12)

Reads the books' Markdown (templates/books, templates/rules) and lists each quotation of at least
`min words` outside a Sources list or heading, longest first: its words, file and line, and the start
of it. A title in quotes (a source's) is left out: one on a line of a Sources list, or followed by a
link or a year in brackets. The judgement (whose words, how old, quoted fairly) is a person's.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUOTE = re.compile(r'"([^"\n]{3,1200})"')


def quotes(path: Path, least: int) -> list:
    out, in_sources = [], False
    for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        s = line.strip()
        if s.startswith("#"):
            in_sources = "source" in s.lower()
            continue
        if re.match(r"^\*?(Sources?|Pictures?)\b", s):
            in_sources = True
            continue
        if in_sources and (s.startswith("- ") or s.startswith("* ")):
            continue
        for m in QUOTE.finditer(line):
            q, after = m.group(1), line[m.end():m.end() + 12]
            if re.match(r"\s*(\(|\[|,?\s*https?:|,?\s*\d{4})", after):    # a title: (year), [link] or a URL after it
                continue
            words = len(q.split())
            if words >= least:
                out.append((words, f"{path.relative_to(ROOT)}:{n}", q))
    return out


def main(least: int = 12) -> None:
    files = sorted((ROOT / "templates" / "books").rglob("*.md")) + sorted((ROOT / "templates" / "rules").glob("*.md"))
    rows = sorted((x for f in files for x in quotes(f, least)), reverse=True)
    print(f"{len(rows)} quotations of {least} words or more\n")
    for w, where, q in rows:
        print(f"{w:4d}  {where}\n      {q[:160]}{'...' if len(q) > 160 else ''}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 12)
