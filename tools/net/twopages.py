"""The GM's roller and a player's page, connected over WebRTC in one headless browser (no STUN: same machine).

    python3 tools/net/twopages.py [page] [shots dir] [seed]

The GM invites a player for the first side, the player's page answers, the GM pastes the reply. Then:
the player's page shows his side's screen; the GM's script plays the other side; the player moves,
strikes with his own typed dice and ends his turn from his page; a choice that is not his to make is
ignored; and nothing the player's side may not see (the enemy's Blood, wounds' severity, effects or
stop checks) ever reaches his page. Needs Python's playwright with Chromium and a built page.
Exits non-zero on any failure.
"""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
URL = Path(sys.argv[1] if len(sys.argv) > 1 else ROOT / "dist" / "roller.html").resolve().as_uri()
SHOTS = Path(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else None
ENEMY_SECRETS = ["Blood <b>", "Bleeding", "Worst untreated", "Nerve", "lethal:", "stop check d100", "Serious", "Critical", "Light ", "critical ", "serious "]
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


with sync_playwright() as p:
    br = p.chromium.launch()
    ctx = br.new_context(viewport={"width": 1400, "height": 1100})
    gm, pl = ctx.new_page(), ctx.new_page()
    errors = []
    for pg in (gm, pl):
        pg.on("pageerror", lambda e: errors.append(str(e)))
    received = []                                      # every whole message the player's page gets, for the secrets check
    gm.goto(URL); gm.evaluate("() => localStorage.clear()"); gm.reload()
    seed = int(sys.argv[3]) if len(sys.argv) > 3 else 7   # a seed whose fight reaches the player's turn (in some, the arrows end it first)
    gm.evaluate("""s => { let st = s; DICE.randint = (a, b) => { st = (st * 16807) % 2147483647; return a + (st % (b - a + 1)) } }""", seed * 101)   # the same fight each run
    gm.evaluate("""() => { const [a, b] = S.chars; for (const c of S.chars){ c.wounds = []; c.blood = poolOf(c); c.state = null }
      a.pos = [6, 5]; b.pos = [9, 5]; renderChars() }""")
    me, foe = gm.evaluate("() => sidesInOrder()")
    # the invitation, the reply, the connection
    gm.click("#net-bar summary"); gm.uncheck("#net-stun")
    gm.click(f'button[data-net="invite"][data-side="{me}"]')
    gm.wait_for_selector("textarea[data-net-link]")
    link = gm.input_value("textarea[data-net-link]")
    check("#join=" in link and len(link) < 6000, f"the invitation is a link ({len(link)} characters)")
    pl.add_init_script("""(() => { const real = window.RTCPeerConnection; window.__got = [];
      window.RTCPeerConnection = function(...a){ const pc = new real(...a);
        pc.addEventListener('datachannel', e => e.channel.addEventListener('message', m => window.__got.push(m.data)));
        return pc }; window.RTCPeerConnection.prototype = real.prototype })()""")
    pl.goto(link)
    pl.wait_for_function("() => (document.querySelector('#g-reply') || {}).value", timeout=20000)
    reply = pl.input_value("#g-reply")
    gm.fill("textarea[data-net-reply]", reply)
    gm.click('button[data-net="accept"]')
    pl.wait_for_function("() => document.querySelector('#chars') && document.querySelector('#chars').children.length > 0", timeout=20000)
    check(True, "the player's page shows the fight once the GM pastes the reply")
    check(gm.evaluate("() => NETH.peers[0].state") == "open", "the GM's page shows him connected")
    check(gm.evaluate(f"() => gmSide({me!r}).ctl") == "player" and gm.evaluate(f"() => gmSide({foe!r}).ctl") == "script", "his side is a player's, the other the script's")
    check(gm.evaluate("() => screenSeat()") == "gm", "the GM's own page stays on the GM's screen")
    # a choice that is not his to make is ignored
    before = gm.evaluate("() => JSON.stringify([S.turn, S.chars.map(c => c.pos)])")
    pl.evaluate("() => { GUEST.send({ t: 'next' }); GUEST.send({ t: 'hex', h: [0, 0] }) }")
    gm.wait_for_timeout(400)
    check(gm.evaluate("() => JSON.stringify([S.turn, S.chars.map(c => c.pos)])") == before, "a move or Next fighter out of his turn is ignored")
    # the script plays the other side until it is his turn
    gm.evaluate("() => { S.gm.auto = true; gmPlay() }")
    try:
        pl.wait_for_function("() => (document.querySelector('#g-status') || {}).textContent.startsWith('Your turn')", timeout=60000)
    except Exception:
        print("     no turn for him:", gm.evaluate("() => [S.gmMsg, S.chars.map(c => [c.name, isOut(c)])]"))
        raise
    check(True, "the GM's script plays its side, then the player's page says it is his turn")
    # his move: a hex next to the enemy, then his strike with his own dice
    gm.evaluate(f"() => {{ for (const c of S.chars.filter(c => sideOf(c) === {me!r})){{ c.wounds = []; c.blood = poolOf(c); c.state = null }} restoreActing(); renderChars() }}")   # the GM heals him, so his strike can land whatever the arrows did
    foe_pos = gm.evaluate(f"() => S.chars.find(c => sideOf(c) === {foe!r}).pos")
    if gm.evaluate(f"() => {{ const t = turnInfo(); return ![...t.reach.keys()].some(k => hexDistance(k.split(',').map(Number), {foe_pos}) === 1 && t.reach.get(k) <= t.allow.advance) }}"):
        gm.evaluate(f"() => {{ const a = actingChar(), b = S.chars.find(c => sideOf(c) === {foe!r}); b.pos = [a.pos[0] + 2, a.pos[1]]; S.tm = null; renderChars() }}")   # the GM puts the enemy within reach
        foe_pos = gm.evaluate(f"() => S.chars.find(c => sideOf(c) === {foe!r}).pos")
    adj = gm.evaluate(f"() => {{ const t = turnInfo(); return [...t.reach.keys()].map(k => k.split(',').map(Number)).filter(h => hexDistance(h, {foe_pos}) === 1 && t.reach.get(h.join(',')) <= t.allow.advance)[0] || null }}")
    if adj:
        pl.click(f'#map .hex[data-h="{adj[0]},{adj[1]}"]', force=True)
        gm.wait_for_function(f"() => {{ const c = actingChar(); return c && c.pos[0] === {adj[0]} && c.pos[1] === {adj[1]} }}", timeout=10000)
        check(True, "his click on a hex moves his fighter on the GM's page")
    try:
        pl.wait_for_selector("#g-roll", timeout=10000)
    except Exception:
        print("     no roll for him:", gm.evaluate("() => [actingChar()?.name, attackerChar()?.name, defenderChar()?.name, S.chars.map(c => [c.name.slice(9, 16), c.pos, c.blood, c.state && c.state.id, isOut(c)]), netSeatTurn(NETH.peers[0].seat), S.tm]"))
        raise
    n = gm.evaluate("() => S.events.length")
    pl.fill('#g-rollbar [data-g="atk"]', "1"); pl.fill('#g-rollbar [data-g="loc"]', "50")   # a 1 is a critical: it cannot be parried
    pl.click("#g-roll")
    gm.wait_for_function(f"() => S.events.length > {n}", timeout=10000)
    ev = gm.evaluate(f"() => S.events.slice({n}).find(e => e.type === 'strike')")
    first = (ev or {}).get("data", {}).get("dice") or [None]
    check(first[0] == {"name": "atk", "v": 1, "sides": 100, "by": "player"}, f"his strike uses the die he typed on his own page {(ev or {}).get('data', {}).get('hit', {}).get('blocked', '')}")
    try:
        pl.wait_for_function("() => document.querySelector('#result').textContent.includes('How badly is the GM')", timeout=10000)
    except Exception:
        print("     result on his page:", pl.inner_text("#result")[:300], "| host hit:", gm.evaluate("() => [S.hit.def, S.hit.loc, S.hit.sev, screenSeat()]"))
        raise
    check(True, "his page shows where the blow landed, not how badly")
    if SHOTS:
        SHOTS.mkdir(parents=True, exist_ok=True)
        pl.screenshot(path=str(SHOTS / "player-page.png"), full_page=True)
    pl.click('#map-actions button[data-map="next"]')
    gm.wait_for_function(f"() => !actingChar() || sideOf(actingChar()) !== {me!r} || S.round > 1", timeout=10000)
    check(True, "his Next fighter ends his turn on the GM's page")
    gm.wait_for_function("() => !GMQ.running", timeout=60000)
    # nothing secret reached his page
    got = pl.evaluate("() => window.__got.join('')")
    enemy = gm.evaluate(f"() => S.chars.filter(c => sideOf(c) === {foe!r}).map(c => [c.name, c.blood, poolOf(c)])")
    check(len(got) > 10000, f"the player's page received its screens ({len(got)} characters in all)")
    check(any(b < pool for _, b, pool in enemy), f"the enemy was hurt, so the checks below mean something {enemy}")
    veiled_cards = " ".join(pl.locator("#chars .char.veiled").all_inner_texts())
    leaks = [s for s in ENEMY_SECRETS if s in veiled_cards]
    check(not leaks, f"the enemy's card on his page shows none of his secrets {leaks}")
    blood_lines = [f"{name}: \u2212" for name, _, _ in enemy] + [f"Blood <b>{b}</b>/{pool}" for _, b, pool in enemy if b != pool]
    check(not any(x in got for x in blood_lines), "no message to his page carries the enemy's Blood or bleeding lines")
    cleaned = pl.evaluate("""() => { const box = document.createElement('div');
      box.replaceChildren(...guestClean('<img src="x" onerror="window.__pwned=1"><a href=" javascript:alert(1)">l</a><script>window.__pwned=2</script><svg><circle onclick="x()" r="2"/></svg><b>ok</b>'));
      return box.innerHTML }""")
    check("onerror" not in cleaned and "javascript" not in cleaned and "<script" not in cleaned and "onclick" not in cleaned and "<b>ok</b>" in cleaned and "<circle" in cleaned,
          "his page drops anything in a drawing that could run, and keeps the rest")
    check(not errors, f"no page errors {errors[:3]}")
    br.close()

print(f"{'all checks passed' if not failures else str(len(failures)) + ' failed'}")
sys.exit(1 if failures else 0)
