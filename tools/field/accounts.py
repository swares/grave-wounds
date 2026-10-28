"""The field page's Which account? box, in a headless browser.

    python3 tools/field/accounts.py

Lays out Wanat with its armies as drawn up: the game's own account first (the commander's benchmark shown);
then the insurgents as an Afghan official put them (more fighters, the armies drawn up again) and the
Apaches half an hour in (the phase moved), the panel then scoring against history only; Roll it picks an
option for each question; a battlefield with no accounts shows no box. Needs Python's playwright with
Chromium and a built site. Exits non-zero on any failure.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

PAGE = (Path(__file__).resolve().parents[2] / "dist" / "field.html").as_uri()
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


MEN = "() => S.units.filter(u => u.side === S.sides[1]).reduce((t, u) => t + u.men, 0) + S.waiting.filter(u => u.side === S.sides[1]).reduce((t, u) => t + u.men, 0)"
BOX = "#accounts"
APACHES = "() => S.stages.find(p => p.name === 'The Apaches arrive').at"

with sync_playwright() as p:
    browser = p.chromium.launch()
    pg = browser.new_page(viewport={"width": 1400, "height": 1000})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.goto(PAGE)
    pg.evaluate("() => localStorage.clear()")
    pg.reload()

    pg.select_option("#sel-field", "wanat-2008")
    check(pg.is_visible(BOX) and "how many fighters attacked?" in pg.inner_text(BOX).lower(), "choosing Wanat shows its questions")
    pg.click("#btn-field")
    own = pg.evaluate(MEN)
    check(own == 245 and pg.evaluate(APACHES) == 61, f"the game's own account: {own} fighters, the Apaches at exchange 61")
    check("To beat it:" in pg.inner_text("#beat"), "on the game's own account the commander's bar is shown")

    pg.select_option("select[data-account=fighters]", "2")
    more = pg.evaluate(MEN)
    check(430 <= more <= 450, f"400 to 500 (a single report): the armies drawn up again, {more} fighters")
    pg.select_option("select[data-account=apaches]", "1")
    check(pg.evaluate(APACHES) == 31, "the Apaches half an hour in: their phase moved to exchange 31")
    beat = pg.inner_text("#beat")
    check("scored against history only" in beat and "To beat it:" not in beat, "on another account the panel scores against history only")
    check("By the accounts you chose" in pg.inner_text("#msg"), "the message says which accounts the armies are drawn up by")

    pg.click("#btn-roll-accounts")
    picks = pg.evaluate("() => S.picks['wanat-2008']")
    check(picks["fighters"] in (0, 1, 2) and picks["apaches"] in (0, 1), f"Roll it picks an option for each question ({picks})")

    bad = pg.evaluate("""() => { const out = [];
      for (const [fid, B] of Object.entries(FD.fields)) for (const q of B.accounts || []) q.options.forEach((o, k) => {
        S.picks = { [fid]: { [q.id]: k } }; S.phase = "setup"; loadBattlefield(fid, true);
        const want = asAccounted(B, fid);
        if (!S.units.length && !S.waiting.length) out.push(`${fid} ${q.id} ${k}: no units`);
        if (k && !want.chosen.length) out.push(`${fid} ${q.id} ${k}: not chosen`);
        const crowded = S.units.filter((u, i) => !fits(S.units, i, u, SIZE, S.field)).filter(u => !S.msg.includes(u.name));
        if (crowded.length) out.push(`${fid} ${q.id} ${k}: ${crowded[0].name} does not fit, unsaid`) });
      return out }""")
    check(not bad, f"every option of every battlefield's accounts draws its armies up, each unit fitting or named to move ({bad[:3]})")
    pg.evaluate("() => { S.picks = {}; loadBattlefield('wanat-2008', true) }")

    pg.select_option("#sel-field", "snipe-1942")
    check(pg.is_hidden(BOX), "a battlefield with no accounts shows no box")
    check(not errors, f"no page errors {errors[:3]}")
    browser.close()

print("all checks passed" if not failures else f"{len(failures)} check(s) failed")
sys.exit(1 if failures else 0)
