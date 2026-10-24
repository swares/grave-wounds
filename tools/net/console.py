"""The GM's campaign console and a player's page, connected over WebRTC in one headless browser (no STUN).

    python3 tools/net/console.py

The player's page is in a browser profile of its own, as on his own computer: it holds nothing of
the GM's. The GM adds a player for two named men; the player opens his link, the GM pastes his reply.
Then: his page shows his men, the force they are with, and the campaign's public news; nothing of
the enemy's force, its named man, or the GM's own notes reaches it. The march moves on from the
console and his page follows, by changes only. His page reloaded keeps his last screen and rejoins;
the console reloaded remembers who plays whom and invites him again. He proposes his force's orders;
the GM accepts one (given as the console gives it) and declines another; one not his is ignored;
the GM turns proposals off. His named man in a fight on the
console's roller: the fight comes to his page on the same link, his side his to play, his Next
ending his turn there, and the fight gone from his page when the roller leaves the frame. Needs Python's playwright with
Chromium and a built site. Exits non-zero on any failure.
"""
import functools, http.server, json, threading
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[2]
MAP = "towton-1461"
failures = []
# Every message the player's page gets, put back together from the channel's pieces
GOT = """() => { const whole = {}, out = [];
  for (const x of window.__got){ const p = JSON.parse(x); (whole[p.id] ||= []).push(p);
    if (whole[p.id].length === p.of) out.push(whole[p.id].sort((a, b) => a.k - b.k).map(q => q.part).join("")) }
  return out }"""
TAP = """(() => { const real = window.RTCPeerConnection; window.__got = [];
  window.RTCPeerConnection = function(...a){ const pc = new real(...a);
    pc.addEventListener('datachannel', e => e.channel.addEventListener('message', m => window.__got.push(m.data)));
    return pc }; window.RTCPeerConnection.prototype = real.prototype })()"""


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return None


server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
threading.Thread(target=server.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{server.server_port}/dist/"
shots = Path(__file__).parent / ".cache"
shots.mkdir(exist_ok=True)


def connect(gm, pl, link):
    """The player opens the link; the GM pastes his reply; both wait for the connection."""
    was = pl.evaluate("() => (document.querySelector('#p-reply') || {}).value || ''") if pl.url.startswith(BASE) else ""
    pl.goto(link)
    pl.wait_for_function("was => { const v = (document.querySelector('#p-reply') || {}).value; return v && v !== was }", arg=was, timeout=20000)
    reply = pl.input_value("#p-reply")
    gm.fill("textarea[data-pl-reply]", reply)
    gm.click('button[data-pl="accept"]')
    pl.wait_for_function("() => document.querySelector('#p-status').textContent.startsWith('Connected')", timeout=20000)


with sync_playwright() as p:
    br = p.chromium.launch(args=["--disable-features=WebRtcHideLocalIpsWithMdns"])
    gctx = br.new_context(viewport={"width": 1400, "height": 1100})
    pctx = br.new_context(viewport={"width": 1100, "height": 900})   # his own computer: nothing of the GM's storage
    pctx.add_init_script(TAP)
    gm, pl = gctx.new_page(), pctx.new_page()
    errors = []
    for pg in (gm, pl):
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.on("dialog", lambda d: d.accept())
    # the campaign: a map with its forces, two named men with the first force, one with the enemy's
    gm.goto(BASE + "travel.html"); gm.evaluate("() => localStorage.clear()"); gm.reload()
    gm.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
    gm.evaluate(f"""() => {{ S.mapId = {MAP!r}; S.clock = {{}}; const fs = forcesHere(), a = fs[0], foe = fs.find(o => o.side !== a.side);
      addWaypoint(a, foe.pos); a.order = 'march'; save();
      const man = (name, f) => ({{ name, map: {MAP!r}, force: f.id, pid: 'pid-' + name, endurance: 50, str: 50, sex: 'm', fieldcraft: 40, leechcraft: 20, log: [], health: {{ cases: [], immune: {{}}, had: {{}}, dead: 0 }} }});
      localStorage.setItem('gravewounds-named', JSON.stringify({{ u1: man('Hal Ashby', a), u2: man('Wat Tyler', a), u3: man('Clifford Spy', foe) }}));
      localStorage.setItem('gravewounds-purses', JSON.stringify({{ 'pid-Hal Ashby': {{ name: 'Hal Ashby', start: 12, ledger: [] }} }})) }}""")
    mine, enemy, mine_id, enemy_id = gm.evaluate("() => { const fs = forcesHere(), a = fs[0], b = fs.find(o => o.side !== a.side); return [a.name, b.name, a.id, b.id] }")
    gm.evaluate("() => localStorage.setItem('gw-room-server', 'off')")   # copy and paste (rooms: rooms.py), not the site's own room server
    gm.goto(BASE + "campaign.html")
    gm.wait_for_function("() => typeof REC === 'object' && REC", timeout=15000)
    gm.evaluate("() => { setPhase('march'); render() }")
    gm.fill("#c-note", "The scouts saw Clifford's banners."); gm.uncheck("#c-note-gm"); gm.click("#c-add-note")
    gm.fill("#c-note", "Clifford waits in ambush at the ford."); gm.check("#c-note-gm"); gm.click("#c-add-note")
    # the player added for his two men; his link, his reply
    gm.wait_for_selector("[data-pl-new]")
    gm.fill("#pl-name", "Scott"); gm.uncheck("#pl-stun")
    gm.check('[data-pl-new][value="u1"]'); gm.check('[data-pl-new][value="u2"]')
    gm.click("#pl-add")
    gm.wait_for_selector("textarea[data-pl-link]", timeout=15000)
    check(gm.evaluate("() => REC.players.length === 1 && REC.players[0].men.join() === 'u1,u2'"), "the GM adds a player for two named men; who plays whom is kept with the campaign")
    link = gm.input_value("textarea[data-pl-link]")
    check("campaign.html#join=" in link and len(link) < 6000, f"his invitation is a link to the campaign page ({len(link)} characters)")
    connect(gm, pl, link)
    check("connected" in gm.inner_text("#c-players"), "his reply pasted, the console shows him connected")
    pl.wait_for_function("() => document.querySelector('#p-men').textContent.includes('Hal Ashby')", timeout=10000)
    men, force, news = pl.inner_text("#p-men"), pl.inner_text("#p-force"), pl.inner_text("#p-news")
    check("Hal Ashby" in men and "Wat Tyler" in men and "Clifford Spy" not in men, "his page shows his two men, and not the enemy's named man")
    check("12 Days" in men or "12" in men, f"his man's purse ({men.splitlines()[1] if len(men.splitlines()) > 1 else men})")
    check(mine in force and "Day 1" in force, f"his page shows the force his men are with ({mine}) and the map's day")
    check(enemy not in force, f"and nothing of the enemy's force ({enemy})")
    check("scouts saw" in news and "ambush" not in news and "Scott is added as a player" in news and "Scott joins" in news, "the campaign's public news reaches him; the GM's own notes do not")
    check(gm.evaluate("() => REC.log.filter(e => e.data.text === 'Scott joins').length") == 1, "his joining is logged when his page connects, once")
    # the march moves on from the console: his page follows, by changes
    day_before = pl.inner_text("#p-force").splitlines()[0]
    gm.click("#c-run")                                   # until something happens: the forces meet, or a night passes
    pl.wait_for_function(f"() => document.querySelector('#p-force').textContent.split('\\n')[0] !== {json.dumps(day_before)} || !document.querySelector('#p-force').textContent.includes({json.dumps(day_before)})", timeout=10000)
    gm.wait_for_timeout(500)
    check(pl.inner_text("#p-force").splitlines()[0] != day_before, f"the console's march moves on, and his page follows ({pl.inner_text('#p-force').splitlines()[0]})")
    msgs = [json.loads(x) for x in pl.evaluate(GOT)]
    sizes = [len(json.dumps(m)) for m in msgs]
    check(len(msgs) >= 2 and not msgs[0].get("part") and all(m.get("part") for m in msgs[1:]) and max(sizes[1:]) < sizes[0],
          f"his first screen comes whole, then only what changed ({sizes[0]} characters, then {sizes[1:]})")
    same = pl.evaluate("() => PG.screen"), gm.evaluate("() => playerScreen(REC.players[0])")
    check(all(same[0][k] == same[1][k] for k in ("men", "force", "news")), "the screen put together from the changes is the console's drawing for him")
    marched = gm.evaluate("() => REC.log.filter(e => e.data.kind === 'march').map(e => e.data.text)")
    check(marched and not any(t[:40] in pl.inner_text("#p-news") for t in marched), f"the march's word on every force stays in the console's log, not his news ({marched[-1][:60] if marched else ''})")
    raw = "".join(pl.evaluate(GOT))
    check(enemy not in raw and "Clifford Spy" not in raw and "ambush" not in raw, "no message to his page names the enemy's force, its named man, or the GM's notes")
    # his map: his side's forces; of the enemy, only what his side sees now, or where it last saw it
    pl.wait_for_selector("#p-mapbox iframe", timeout=10000)
    mp = pl.frame_locator("#p-mapbox iframe")
    mp.locator("#map svg .force").first.wait_for(timeout=15000)
    marks = mp.locator("#map svg .force title").all_text_contents()
    seen = [t for t in marks if t.endswith("seen now")]
    ours = gm.evaluate(f"() => newDay().marchSummary().forces.filter(f => f.side === newDay().marchSummary().forces.find(x => x.name === {mine!r}).side).map(f => f.name)")
    check(all(any(t.startswith(n + " (") for t in marks) for n in ours), f"his map shows his side's forces ({len(ours)})")
    check(not any(t.startswith(enemy + " (") for t in marks), f"and not the enemy his side cannot see ({enemy})")
    met = [x for x in seen if x.startswith("Clifford's horse")]
    check(bool(met) and "about" in met[0] and "men" not in met[0], f"the enemy force his men met is on his map, roughly sized ({met[:1]})")
    was = gm.evaluate("() => localStorage.getItem('gravewounds-travel')")
    gm.evaluate(f"""() => {{ const t = JSON.parse(localStorage.getItem('gravewounds-travel')), f = t.forces[{MAP!r}].find(x => x.name === "Clifford's horse");
      f.pos = [1, 1]; f.path = null; f.waypoints = []; localStorage.setItem('gravewounds-travel', JSON.stringify(t)); render() }}""")
    mp.locator("#map svg .force.ghost").first.wait_for(timeout=15000)
    ghost = mp.locator("#map svg .force.ghost title").first.text_content()
    check(ghost.startswith("Clifford's horse") and "last seen here" in ghost and not any(t.startswith("Clifford's horse") and t.endswith("seen now") for t in mp.locator("#map svg .force title").all_text_contents()),
          f"gone out of sight, it stays where it was last seen, faded, with when ({ghost[-40:]})")
    check("[1,1]" not in "".join(pl.evaluate(GOT)).replace(" ", ""), "and where it went never reaches his page")
    pl.locator("#p-mapbox").screenshot(path=str(shots / "player-map.png"))
    gm.evaluate("w => { localStorage.setItem('gravewounds-travel', w); render() }", was)   # back where it met his force, for the fight below
    # his proposed orders: sent from his page, waiting for the GM, accepted or declined there
    TRAVEL_FORCE = f"() => JSON.parse(localStorage.getItem('gravewounds-travel')).forces[{MAP!r}].find(f => f.id === {mine_id})"
    OPEN = "() => REC.proposals.filter(x => x.state === 'open').length"
    pl.wait_for_selector(f'#p-force .propose[data-force="{mine_id}"] select[data-pick="to"]', timeout=10000)
    place = pl.evaluate(f"""() => {{ const s = document.querySelector('#p-force .propose[data-force="{mine_id}"] select[data-pick="to"]'); s.selectedIndex = s.options.length - 1; return [s.value, s.options[s.selectedIndex].text] }}""")
    check(enemy not in pl.inner_text("#p-force"), "his order choices list places, not where the enemy is")
    before = gm.evaluate(TRAVEL_FORCE)
    pl.click(f'#p-force .propose[data-force="{mine_id}"] button[data-propose="to"]')
    gm.wait_for_function(f"() => {OPEN[6:]} === 1", timeout=10000)
    check(place[1] in gm.inner_text("#c-players") and "Scott proposes" in gm.inner_text("#c-notice"), f"his proposal ({place[1]}) waits on the console, and the GM is told")
    check(gm.evaluate(TRAVEL_FORCE)["waypoints"] == before["waypoints"], "a proposal changes nothing until the GM accepts it")
    pl.evaluate(f"() => {{ PG.send({{ t: 'propose', force: {enemy_id}, what: 'halt' }}); PG.send({{ t: 'propose', force: {mine_id}, what: 'to', arg: '0,0' }}); PG.send({{ t: 'propose', force: {mine_id}, what: 'burn' }}) }}")
    gm.wait_for_timeout(600)
    check(gm.evaluate("() => REC.proposals.length") == 1, "a proposal for a force not his, or not among its choices, is ignored")
    gm.click('button[data-prop="yes"]')
    gm.wait_for_function(f"() => {TRAVEL_FORCE[6:]}.waypoints.join() === {json.dumps(place[0])}", timeout=10000)
    pl.wait_for_function("() => document.querySelector('#p-force').textContent.includes('accepted')", timeout=10000)
    check("accepts" in pl.inner_text("#p-news"), "the GM accepts it: the force's route is set as the console sets it, and his page says so")
    pl.click(f'#p-force .propose[data-force="{mine_id}"] button[data-propose="rest"]')
    gm.wait_for_function(f"() => {OPEN[6:]} === 1", timeout=10000)
    day_was = gm.evaluate(TRAVEL_FORCE)["day"]
    gm.click('button[data-prop="no"]')
    pl.wait_for_function("() => document.querySelector('#p-force').textContent.includes('declined')", timeout=10000)
    check(gm.evaluate(TRAVEL_FORCE)["day"] == day_was, "the GM declines one: nothing changes, and his page says so")
    gm.uncheck("#pl-propose")
    pl.wait_for_function("() => !document.querySelector('#p-force .propose select')", timeout=10000)
    check("giving the orders himself" in pl.inner_text("#p-force"), "the GM turns proposals off: the choices go from his page")
    gm.check("#pl-propose")
    # his men changed by the GM: his page follows
    gm.uncheck('[data-pl-man][value="u2"]')
    pl.wait_for_function("() => !document.querySelector('#p-men').textContent.includes('Wat Tyler')", timeout=10000)
    check(True, "the GM changes which men he plays, and his page follows")
    # his page reloaded: his last screen at once, then rejoined on a new link
    pl.reload()
    pl.wait_for_function("() => document.querySelector('#p-men').textContent.includes('Hal Ashby')", timeout=10000)
    check("Rejoining" in pl.inner_text("#p-status"), "his page reloaded shows his last screen while it rejoins")
    gm.wait_for_selector('button[data-pl="invite"]', timeout=15000)
    check("Invite again" in gm.inner_text("#c-players"), "the console sees him gone, and offers Invite again")
    gm.click('button[data-pl="invite"]')
    gm.wait_for_selector("textarea[data-pl-link]", timeout=15000)
    connect(gm, pl, gm.input_value("textarea[data-pl-link]"))
    check("Hal Ashby" in pl.inner_text("#p-men"), "Invite again and his new link: he is back")
    check(gm.evaluate("() => REC.log.filter(e => e.data.text === 'Scott rejoins').length") >= 1, "and the log says he rejoins")
    # the console reloaded: who plays whom remembered, invited again
    gm.reload()
    gm.wait_for_selector('button[data-pl="invite"]', timeout=15000)
    check("Scott" in gm.inner_text("#c-players") and "Invite" in gm.inner_text("#c-players"), "the console reloaded remembers its player and offers to invite him")
    pl.wait_for_function("() => document.querySelector('#p-status').textContent.startsWith('Lost')", timeout=20000)
    check("Hal Ashby" in pl.inner_text("#p-men"), "his page, its console gone, keeps his last screen and offers to rejoin")
    gm.click('button[data-pl="invite"]')
    gm.wait_for_selector("textarea[data-pl-link]", timeout=15000)
    relink = gm.input_value("textarea[data-pl-link]")
    pl.fill("#p-relink", relink); pl.click("#p-rejoin")
    pl.wait_for_function("() => (document.querySelector('#p-reply') || {}).value && !document.querySelector('#p-join').hidden && document.querySelector('#p-copy')", timeout=20000)
    gm.fill("textarea[data-pl-reply]", pl.input_value("#p-reply")); gm.click('button[data-pl="accept"]')
    pl.wait_for_function("() => document.querySelector('#p-status').textContent.startsWith('Connected')", timeout=20000)
    check(not pl.is_visible("#p-join"), "he rejoins from the link pasted into his page, and the reply box goes away")
    # his fight through the same link: the roller in the console's frame, his man on one side
    gm.evaluate("() => { setPhase('fight'); render(); show('roller.html') }")
    gm.wait_for_function("() => !!rollerFrame()", timeout=20000)
    rf = next(f for f in gm.frames if f.url.endswith("roller.html"))
    rf.wait_for_function("() => typeof S === 'object' && S.chars.length > 1", timeout=20000)
    me, foe = rf.evaluate("""() => { const [a, b] = S.chars; for (const c of S.chars){ c.wounds = []; c.blood = poolOf(c); c.state = null }
      a.uid = 'u1'; a.name = 'Hal Ashby'; a.pos = [6, 5]; b.pos = [9, 5]; renderChars(); return [sideOf(a), sideOf(b)] }""")
    pl.wait_for_selector("#p-fight iframe", timeout=15000)
    pf = pl.frame_locator("#p-fight iframe")
    pf.locator("#chars .char").first.wait_for(timeout=15000)
    check(pl.is_visible("#p-fight") and pf.locator("#chars .char").count() >= 2, "his named man in a fight on the console's roller: his page shows the fight, on the same link")
    check(rf.evaluate(f"() => gmSide({me!r}).ctl") == "player" and rf.evaluate(f"() => gmSide({foe!r}).ctl") == "script", f"the roller gives his man's side ({me}) to him, the other to the script")
    rf.evaluate("""s => { let st = s; DICE.randint = (a, b) => { st = (st * 16807) % 2147483647; return a + (st % (b - a + 1)) } }""", 707)   # the same fight each run (as twopages.py)
    rf.evaluate("() => { S.gm.auto = true; gmPlay() }")
    inner = next(f for f in pl.frames if "roller.html#relay" in f.url)
    inner.wait_for_function("() => (document.querySelector('#g-status') || {}).textContent.startsWith('Your turn')", timeout=60000)
    check(True, "the script plays its side, then his page says it is his turn")
    pl.screenshot(path=str(shots / "campaign-player-fight.png"), full_page=False)
    before = rf.evaluate("() => S.round")
    inner.click('#map-actions button[data-map="next"]')
    rf.wait_for_function(f"() => !actingChar() || sideOf(actingChar()) !== {me!r} || S.round > {before}", timeout=10000)
    check(True, "his Next fighter, clicked on his page, ends his turn on the console's roller")
    veiled = " ".join(inner.locator("#chars .char.veiled").all_inner_texts())
    check(veiled and "Blood" not in veiled and "Nerve" not in veiled, "the enemy's card on his page is veiled: no Blood, no Nerve")
    # a fight set up from the travel map: his named man comes into it as himself, and the fight comes to his page
    titles = gm.evaluate(f"() => newDay().fightsOnOffer().filter(x => x.title.includes({mine!r})).map(x => [x.id, x.title])")
    check(bool(titles), f"a fight is on offer for his force ({titles[:1]})")
    gm.evaluate(f"() => newDay().sendFightFor({titles[0][0]}, 0, 'roller')")
    rf.evaluate("() => { S.handoff = JSON.parse(localStorage.getItem('gravewounds-handoff')); setupHandoff(); renderChars() }")
    hal = rf.evaluate("() => { const c = S.chars.find(c => c.uid === 'u1'); return c && [c.name, sideOf(c), c.sheet === undefined, S.pending.join(' | ')] }")
    york = gm.evaluate(f"() => newDay().marchSummary().forces.find(f => f.name === {mine!r}).side")
    check(bool(hal) and hal[0] == "Hal Ashby" and hal[1] == york and "Named men with their forces: Hal Ashby" in hal[3],
          f"the fight set up from the travel map brings his named man in as himself, on his force's side ({hal[:2] if hal else None})")
    check(rf.evaluate("() => S.chars.filter(c => !c.uid).length") >= 2, "with the forces' other men beside him")
    pl.wait_for_function("() => { const f = document.querySelector('#p-fight iframe'); return f && f.contentDocument && (f.contentDocument.querySelector('#chars') || {}).textContent?.includes('Hal Ashby') }", timeout=15000)
    check(rf.evaluate(f"() => gmSide({york!r}).ctl") == "player", "and his page plays his side in it, with no new link")
    gm.evaluate("() => show('travel.html')")
    pl.wait_for_function("() => document.querySelector('#p-fight').hidden", timeout=15000)
    check(True, "the roller gone from the console, his fight goes from his page")
    gm.screenshot(path=str(Path(__file__).parent / ".cache" / "campaign-gm.png"), full_page=True)
    pl.screenshot(path=str(shots / "campaign-player.png"), full_page=True)
    check(not errors, f"no page errors {errors[:3]}")
    br.close()

print(f"{'all checks passed' if not failures else str(len(failures)) + ' failed'}")
raise SystemExit(1 if failures else 0)
