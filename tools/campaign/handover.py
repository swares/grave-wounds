"""Handing the game to the next GM, in a headless browser: two GMs, two browsers.

    python3 tools/campaign/handover.py

The first GM names the campaign, writes a public note and a GM-only note, and hands the game to Ann
with a passphrase: the file comes down, his console stands handed over (its panels inert), and Take it
back gives it him again. The second GM, in a browser of her own, loads the file: the GM-only note is
sealed (its words nowhere in the file), the wrong passphrase leaves it sealed, and the right one opens
it. Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import json
import sys
import tempfile
import traceback
from pathlib import Path
from playwright.sync_api import sync_playwright
from harness import check, failures, serve

BASE, server = serve()
SECRET = "The ambush waits at the ford"


def run(p):
    br = p.chromium.launch()
    errors = []
    one = br.new_context(viewport={"width": 1400, "height": 1100}, accept_downloads=True)
    pg = one.new_page()
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE + "campaign.html")
    pg.evaluate("() => localStorage.clear()")
    pg.reload()
    pg.fill("#c-name", "Towton")
    pg.press("#c-name", "Tab")
    pg.uncheck("#c-note-gm")
    pg.fill("#c-note", "The army marches at dawn")
    pg.click("#c-add-note")
    pg.check("#c-note-gm")
    pg.fill("#c-note", SECRET)
    pg.click("#c-add-note")
    pg.click("#c-hand")
    pg.fill("#c-hand-from", "Scott")
    pg.fill("#c-hand-to", "Ann")
    pg.fill("#c-hand-note", "Watch the ford")
    pg.fill("#c-hand-pass", "oak and ash")
    pg.fill("#c-hand-pass2", "oak and ash")
    with pg.expect_download() as dl:
        pg.click("#c-hand-form button[type=submit]")
    path = Path(tempfile.mkdtemp()) / "handover.json"
    dl.value.save_as(path)
    text = path.read_text()
    f = json.loads(text)
    check(f.get("handover", {}).get("to") == "Ann" and f["handover"].get("note") == "Watch the ford", "the file says who it is for, with the note")
    check(SECRET not in text and "The army marches at dawn" in text, "the GM-only note is sealed in the file; the public one is not")
    check("narrator" not in "".join(f["keys"]), "the narrator's settings stay out of it")
    pg.wait_for_selector("#c-handed:not([hidden])")
    check("Ann" in pg.inner_text("#c-handed"), "the old console says it was handed to Ann")
    check(pg.evaluate("() => document.querySelector('#c-players').inert && document.querySelector('#c-frame').closest('section').inert"), "its panels stand still (inert)")
    check(pg.evaluate("() => !document.querySelector('#c-save').closest('section').inert"), "save and load still work on it")
    pg.click("#c-take-back")
    check(pg.is_hidden("#c-handed") and not pg.evaluate("() => document.querySelector('#c-players').inert"), "Take it back makes it the game again")

    two = br.new_context(viewport={"width": 1400, "height": 1100})
    p2 = two.new_page()
    p2.on("pageerror", lambda e: errors.append(str(e)))
    p2.on("dialog", lambda d: d.accept())
    p2.goto(BASE + "campaign.html")
    p2.set_input_files("#c-load", str(path))
    p2.wait_for_selector("#c-unseal:not([hidden])")
    say = p2.inner_text("#c-unseal")
    check("Scott" in say and "Watch the ford" in say and "1 GM note is sealed" in say, f"the next GM sees who handed it over, the note, and one sealed note ({say[:90]})")
    check(SECRET not in p2.inner_text("#c-log") and "sealed GM note" in p2.inner_text("#c-log"), "the sealed note shows as sealed in her log")
    check(p2.is_hidden("#c-handed"), "her copy is not marked handed over")
    p2.fill("#c-unseal-pass", "wrong")
    p2.click("#c-unseal-go")
    p2.wait_for_function("() => document.querySelector('#c-saved').textContent.includes('does not open')", timeout=15000)
    check("does not open" in p2.inner_text("#c-saved") and SECRET not in p2.inner_text("#c-log"), "a wrong passphrase leaves it sealed")
    p2.fill("#c-unseal-pass", "oak and ash")
    p2.click("#c-unseal-go")
    p2.wait_for_selector("#c-unseal", state="hidden")
    check(SECRET in p2.inner_text("#c-log"), "the right one opens it")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()


try:
    with sync_playwright() as pw:
        run(pw)
except Exception as e:                               # a timeout or error: where, as an annotation in CI
    print(traceback.format_exc())
    check(False, f"stopped: {str(e).splitlines()[0][:300]}")
server.shutdown()
if failures:
    print(f"{len(failures)} check(s) failed")
    sys.exit(1)
print("all checks passed")
