"""A season with the battalion, in a headless browser, served as the site is: the team builder to the roller.

    python3 tools/service/season.py

A company of the British in the Peninsula serves spring 1811 with Albuera ticked, as the 1/57th: each man's
hit roll and sickness are logged, the season's days go toward his term (counted as rolled), the calendar
moves on, and the hits wait for the roller. A term made mostly of rolled seasons gives no lifepath wound
chance. On the roller the first hit is rolled on the man as a hit with no attack roll, with the weapon the
season gave, and leaves the queue. Needs Python's playwright with Chromium and a built site. Exits non-zero
on any failure. Then the season's small fight: shown with its sizes, aims and sources, another picked, and
the picket at night played on the roller, the team's named men in the picket against French with muskets,
with the aims, the end and the source in the fight's notes.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "campaign"))
from harness import check, main, serve   # noqa: E402

BASE, server = serve()
SEEDED = """seed => { let s = Math.max(1, seed % 2147483647);
  realDice.randint = (a, b) => { s = s * 16807 % 2147483647; return a + s % (b - a + 1) } }"""
FIND = """() => {                                       // a seed whose season gives a hit and no death
  const men = S.team.map(c => ({ name: c.name, endurance: c.stats.end, position: "line", unit: { albuera: 0 }, share: {} }));
  for (let seed = 1; seed < 400; seed++){
    let s = seed; const d = () => { s = s * 16807 % 2147483647; return 1 + s % 100 };
    const r = SVC.serve("peninsula", "1811-spring", men, ["fuentes", "albuera"], d);
    if (r.men.some(m => m.hits.length) && !r.men.some(m => m.dead)) return seed;
  }
  return null;
}"""
SERVICE = "#service"
ADDTEAM = "button[data-map=addteam]"
NO_HANDOFF = "() => !S.handoff"
AT_ROLLER = "() => location.pathname.endsWith('roller.html')"
TEAM_N = "() => S.team.length"
HANDOFF = "button[data-map=handoff]"
SEND = "#btn-send"
CLEAR = "() => localStorage.clear()"
QUEUE = "() => JSON.parse(localStorage.getItem('gravewounds-service-hits') || '[]')"


def followers(pg):
    """The followers through a season: rolled as the named men are, a hit's severity for his fate,
    the war's desertion (or the GM's), and recruits in winter quarters for the lost."""
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "horse_musket")
    pg.select_option("#sel-region", "british_pen")
    pg.select_option("#sel-template", "company")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    n0, cap0 = pg.evaluate("() => [S.crew.length, followerCap().cap]")
    sv = pg.inner_text(SERVICE)
    check(n0 == min(16, cap0) and f"The followers ({n0})" in sv and "Desertion 0.3% a season" in sv,
          f"the company's 16 followers, or what its leader keeps if fewer, serve too, deserting at 0.3% a season ({n0}, cap {cap0})")
    k = pg.evaluate("() => SVC.war('peninsula').seasons.findIndex(s => s.id === '1811-summer')")
    pg.select_option("#sv-season", str(k))
    pg.fill("#sv-desert", "100")
    pg.evaluate(SEEDED, 11)
    pg.click("#btn-serve")
    log = pg.inner_text(SERVICE)
    left = pg.evaluate("() => [S.crew.length, (S.flost || []).length, S.fcounts.reduce((t, [, n]) => t + n, 0)]")
    check(f"The followers ({n0}, desertion 100%)" in log and "deserted" in log and left == [0, n0, 0],
          f"at the GM's 100% every follower is gone, deserted unless sickness or a wound took him first ({left})")
    q = pg.evaluate("() => SVC.war('peninsula').seasons.findIndex((s, i) => i > S.service.i && s.state === 'quarters')")
    pg.select_option("#sv-season", str(q))
    pg.fill("#sv-desert", "0")
    pg.click("#btn-serve")
    log = pg.inner_text(SERVICE)
    got = pg.evaluate("() => { const c = followerCap(); return [S.crew.length, c ? c.cap : null, (S.flost || []).length, S.fcounts.reduce((t, [, n]) => t + n, 0)] }")
    want = min(got[1] or 16, 16)
    check("Drafts:" in log and "(a draft from the depot or second battalion)" in log, f"in winter quarters recruits come up: {log[log.find('Drafts:'):][:120]!r}")
    want = min(want, n0)
    check(got[0] == want and got[2] == n0 - want and got[3] == got[0],
          f"as many as the leader's Presence keeps, no more than were mustered, and the counts follow ({got})")
    fate = pg.evaluate("""() => { const was = realDice.randint, f = S.crew[0], out = [];
      for (const r of [40, 70, 95]){ realDice.randint = () => r; out.push(svcCrewHit(f, 'Albuera').gone) }
      realDice.randint = was; return out }""")
    check(fate == [None, "invalided home", "died of wounds"], f"a hit follower: light stays, serious invalided home, critical dies of it ({fate})")
    pcts = pg.evaluate("() => { const W = SVC.war('acw_confederate_east'); return [SVC.desertPct(W, '1864-winter'), SVC.desertPct(W, '1863-summer'), SVC.desertPct(SVC.war('western_front'), '1916-summer')] }")
    check(pcts == [8, 1.1, 0.03], f"the 4th Virginia's followers desert at 8% in the Petersburg winter, 1.1% otherwise; the Western Front's 0.03% ({pcts})")
    tiny = pg.evaluate("() => { const was = realDice.randint; let n = 0; realDice.randint = (a, b) => 1; n += svcDeserts(0.03) ? 1 : 0; realDice.randint = (a, b) => 100; n += svcDeserts(0.03) ? 10 : 0; realDice.randint = was; return n }")
    check(tiny == 1, f"a share under 1% is rolled on d10000 ({tiny})")
    lost_in_fights(pg)
    drafts_and_names(pg)
    culps_hill(pg)
    sidearms(pg)
    reloads(pg)
    hedged_garden(pg)
    foes_mixed(pg)
    muster_cap(pg)


def sidearms(pg):
    """A bowman's sidearm: an archer strikes with his sword when the man he strikes is next to him,
    with his longbow when he is not."""
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "medieval")
    pg.select_option("#sel-region", "england")
    pg.select_option("#sel-template", "retinue")
    pg.click("#btn-roll")
    pg.click(SEND)
    pg.wait_for_selector(ADDTEAM)
    pg.click(ADDTEAM)
    w = pg.evaluate("""() => { const a = S.chars.find(c => c.follower && c.weapon === 'longbow'), d = S.chars.find(c => c !== a);
      a.pos = [5, 5]; d.pos = [6, 5]; const near = strikeWeapon(a, d); d.pos = [12, 5]; const far = strikeWeapon(a, d);
      return [a.sidearm, near, far] }""")
    check(w == ["sword", "sword", "longbow"], f"an archer follower comes with his sword: next to his man he strikes with it, at a distance with his longbow ({w})")


def reloads(pg):
    """The rate of shot: a slow missile weapon reloads for round(60 / (6 x shots)) - 1 rounds after
    a shot; while he reloads he cannot shoot, and strikes a man next to him with his weapon's close
    one (the bayonet)."""
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "horse_musket")
    pg.select_option("#sel-region", "british_pen")
    pg.select_option("#sel-template", "company")
    pg.click("#btn-roll")
    pg.click(SEND)
    pg.wait_for_selector(ADDTEAM)
    pg.click(ADDTEAM)
    r = pg.evaluate("""() => {
      const rounds = ['musket_smoothbore', 'rifle_flintlock', 'matchlock_musket', 'crossbow', 'longbow', 'breechloader', 'rpg', 'bazooka', 'recoilless', 'atgm'].map(reloadRounds);
      const a = S.chars.find(c => c.follower && c.weapon === 'musket_smoothbore'), d = S.chars.find(c => c !== a);
      d.side = 'The French'; a.pos = [5, 5]; d.pos = [6, 5]; S.round = 3; S.turn = a.id;
      S.attacker = S.chars.indexOf(a); S.active = S.chars.indexOf(d); S.weapon = 'musket_smoothbore';
      startReload(a);
      const at = a.loadedAt, near = strikeWeapon(a, d), blocked = rangeCheck().blocked || '';
      d.pos = [12, 5]; const far = strikeWeapon(a, d);
      S.round = at; const ready = [reloading(a), rangeCheck().blocked || ''];
      S.weapon = 'revolver'; delete a.loadedAt; delete a.cylinder; const cyl = [];
      for (let i = 0; i < 7; i++){ S.round = 10 + i; const free = !reloading(a); if (free) startReload(a); cyl.push(free ? (a.loadedAt || 0) : 'loading') }
      const mins = [weaponReach('rpg', 2), weaponReach('rpg', 3), weaponReach('atgm', 32), weaponReach('atgm', 33)].map(x => !!x);
      return { rounds, at, near, far, blocked, ready, cyl, mins } }""")
    check(r["rounds"] == [2, 4, 6, 2, 0, 0, 1, 1, 1, 4], f"rounds to reload: musket 2 (three a minute), flintlock rifle 4, matchlock 6, crossbow 2; longbow and breechloader none; RPG, bazooka and recoilless rifle 1; ATGM 4 ({r['rounds']})")
    check(r["at"] == 6 and r["near"] == "bayonet" and r["far"] == "musket_smoothbore" and "is reloading his" in r["blocked"],
          f"a musket fired in round 3 shoots again in round 6; meanwhile he cannot shoot, and the man next to him gets the bayonet ({r})")
    check(r["ready"] == [False, ""], f"loaded again in round 6 ({r['ready']})")
    check(r["mins"] == [False, True, False, True], f"minimum ranges: an RPG cannot strike under 3 hexes (5 m to arm), an ATGM under 33 (the TOW's 65 m) ({r['mins']})")
    check(r["cyl"] == [0, 0, 0, 0, 0, 31, "loading"], f"a revolver shoots six rounds running, then reloads its cylinder for 15 rounds (90 seconds): shoots again in round 31 ({r['cyl']})")


def hedged_garden(pg):
    """Valmont's hedged garden: a found camp, laid on the map round the party, not built."""
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "medieval")
    pg.select_option("#sel-region", "england")
    pg.select_option("#sel-template", "retinue")
    pg.click("#btn-roll")
    pg.click(SEND)
    pg.wait_for_selector(ADDTEAM)
    pg.click(ADDTEAM)
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    pg.evaluate("""() => { const W = SVC.war('henry_v'); svcState(); Object.assign(S.service, { war: 'henry_v', i: 0, with: {}, pos: {}, at: {}, played: {}, unit: {}, share: {} });
      S.svcSmall = SVC.smallFight(W, 'garrison', () => 1, 'raid'); svcPlayFight() }""")
    pg.wait_for_selector(HANDOFF)
    pg.click(HANDOFF)
    pg.wait_for_function("() => !S.handoff")
    r = pg.evaluate("""() => { const kinds = Object.values(S.works.edges).flat().map(x => x.type);
      return [kinds.length, [...new Set(kinds)], Object.keys(S.works.hexes).length] }""")
    check(r[0] > 20 and r[1] == ["hedge"] and r[2] == 0, f"the raid at Valmont comes with its hedged garden round the party, all hedge, nothing to build ({r})")
    ring = pg.evaluate("""() => { const keys = Object.keys(S.works.edges), hs = keys.flatMap(k => k.split('|').map(x => x.split(',').map(Number)));
      const c = S.fightEnd.position.centre, r = S.fightEnd.position.radius, team = S.chars.filter(x => x.team && x.pos);
      return [r, team.filter(x => hexDistance(x.pos, c) === r).length, team.length, S.chars.filter(x => !x.team && x.pos).every(x => hexDistance(x.pos, c) > r)] }""")
    check(ring[1] == ring[2] and ring[2] > 0 and ring[3], f"the party lines the hedge, every man on the ring just inside it, the French outside ({ring})")


def muster_cap(pg):
    """A new muster: no more followers than the leader's Presence keeps (as team.py cap_counts)."""
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "horse_musket")
    pg.select_option("#sel-region", "british_pen")
    pg.select_option("#sel-template", "company")
    r = pg.evaluate("""() => { const cases = [[[["archer", 10], ["spearman", 4]], 11], [[["a", 3], ["b", 3]], 4], [[["a", 5], ["b", 1]], 5], [[["a", 2]], null]];
      const cut = cases.map(([c, k]) => fwCapCounts(c, k));
      const got = []; for (let i = 0; i < 40; i++){ S.fcounts = tplFollowers(S.template); rollTeam(); const cap = followerCap(); got.push([S.crew.length, cap.cap, tplFollowers(S.template).reduce((t, [, n]) => t + n, 0)]) }
      return { cut, got } }""")
    check(r["cut"] == [[["archer", 7], ["spearman", 4]], [["a", 2], ["b", 2]], [["a", 4], ["b", 1]], [["a", 2]]], f"team.js cuts a muster as team.py does, off the largest career ({r['cut']})")
    check(all(n == min(cap, full) for n, cap, full in r["got"]) and any(cap < full for _, cap, full in r["got"]),
          f"40 new companies: each musters its template's followers, or what its leader's Presence keeps if fewer ({r['got'][:6]}...)")


def foes_mixed(pg):
    """A Roses garrison: one man-at-arms in nine in plate, the rest archers with swords for close combat."""
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "medieval")
    pg.select_option("#sel-region", "england")
    pg.select_option("#sel-template", "retinue")
    pg.click("#btn-roll")
    pg.click(SEND)
    pg.wait_for_selector(ADDTEAM)
    pg.click(ADDTEAM)
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    pg.evaluate("""() => { const W = SVC.war('roses_edward'); svcState(); Object.assign(S.service, { war: 'roses_edward', i: 0, with: {}, pos: {}, at: {}, played: {}, unit: {}, share: {} });
      S.svcSmall = SVC.smallFight(W, 'siege', () => 1, 'foray'); svcPlayFight() }""")
    pg.wait_for_selector(HANDOFF)
    pg.click(HANDOFF)
    pg.wait_for_function("() => !S.handoff")
    r = pg.evaluate("""() => { const f = S.chars.filter(c => !c.team); const kinds = {};
      for (const c of f) { const k = `${c.kit}/${c.weapon}/${c.sidearm || ''}`; kinds[k] = (kinds[k] || 0) + 1 } return kinds }""")
    ks = sorted(r)
    check(ks == ["full_plate/poleaxe/", "jack_sallet/longbow/sword"] and r["jack_sallet/longbow/sword"] > r["full_plate/poleaxe/"],
          f"the foray's garrison: a few men-at-arms in plate with poleaxes, the rest archers in jacks with swords for close combat ({r})")


def culps_hill(pg):
    """The second edge: the 4th Virginia's Gettysburg, Brinkerhoff's Ridge to the rocks below Greene's works."""
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "civil_war")
    pg.select_option("#sel-region", "confederacy")
    pg.select_option("#sel-template", "squad")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('acw_confederate_east').seasons.findIndex(s => s.id === '1863-summer')")
    pg.select_option("#sv-season", str(k))
    ed = pg.inner_text(SERVICE)
    check(all(x in ed for x in ("The edge of Gettysburg: Culp's Hill", "Brinkerhoff's Ridge", "The night march to the hill", "Up the hill with Major Terry", "Pinned below the works")),
          "summer 1863: Gettysburg has its edge, from Brinkerhoff's Ridge to the rocks below the works")
    check("The Stonewall Brigade at Culp's Hill" in pg.inner_text("select[data-svunit=gettysburg]"), "and the brigade's own figure to choose")
    check(pg.locator("button[data-svedgeplay='gettysburg:pinned']").count() == 0, "the rocks wait for the men who go up with Terry")
    pg.locator("input[data-svedgechoice^='gettysburg:terry:']").first.check()
    check(pg.locator("button[data-svedgeplay='gettysburg:pinned']").count() == 1, "a man with Terry: the rocks can be played or rolled")
    h = pg.evaluate("""() => { let got = null;
      const set = localStorage.setItem.bind(localStorage); localStorage.setItem = (k, v) => { if (k === 'gravewounds-handoff') got = JSON.parse(v); else set(k, v) };
      try{ svcEdgePlay('gettysburg:pinned') }catch(e){}
      localStorage.setItem = set; return got }""")
    check(h and len(h["only"]) == 1 and (h["end"].get("away") or {}).get("side") and h["force"]["side"] == "Union" and h["foes"][0]["side"] == "Confederate",
          f"the rocks go to the roller with only Terry's men, attacking up at the Union works, and won by getting back down ({(h or {}).get('end')})")
    pg.wait_for_function(AT_ROLLER)
    tb = pg.evaluate("t => [DATA.tables[t] ? t : null, !!DATA.tables[t] && DATA.tables[t].weapons.includes('rifle_musket'), document.querySelector('#sel-table') ? 1 : 0]", (h or {}).get("table"))
    check(tb[:2] == ["acw-1861-all-hits", True], f"a season's small fight goes to the roller with its war's own wound table and weapons, not the roller's first ({tb})")
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    pg.select_option("#sv-season", str(k))
    pg.evaluate("() => { const V = svcState(); V.edge = { gettysburg: { done: {}, chosen: { terry: { [S.team[0].pid]: true } }, failed: {} } }; V.unit.gettysburg = '0'; render() }")
    pg.evaluate("() => { realDice.randint = (a, b) => b }")   # no one hit or taken: the chances only
    pg.click("#btn-serve")
    log = pg.evaluate("() => S.svclog")
    first = next((x for x in log if "as its edge set" in x), "")
    rest = [x for x in log if "Gettysburg: " in x and "as its edge set" not in x]
    check("Gettysburg: 68%" in first and rest and all("Gettysburg: 17%" in x for x in rest),
          f"with the brigade's own figure, the man with Terry is hit at 17% x 4 = 68%, the rest at the brigade's 17% ({first[:160]!r})")


def drafts_and_names(pg):
    """Followers' names are not repeated in a team, and a season's drafts come by the army's way of
    the time: volunteers before conscription, conscripts from April 1862, the Union's camps of
    distribution from July 1863."""
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "civil_war")
    pg.select_option("#sel-region", "union")
    pg.select_option("#sel-template", "recruits")
    pg.click("#btn-roll")
    dup = pg.evaluate("""() => { let worst = 0;
      for (let k = 0; k < 10; k++){ rollTeam(); const all = [...S.team, ...S.crew].map(x => x.name); worst = Math.max(worst, all.length - new Set(all).size) }
      return worst }""")
    check(dup == 0, f"ten rolls of a team and its 16 recruits: no two men of the team share a name, named or follower ({dup})")
    fresh = pg.evaluate("""() => { const rows = TD.era.careers[0].terms, all = rows.map(r => r.text), t0 = performance.now();
      const row = freshRow(rows, 50, all); return [row === pickRow(rows, 50), performance.now() - t0 < 100] }""")
    check(fresh == [True, True], f"a man who has had every term event of his career (a long service) gets the rolled one again, not an endless search ({fresh})")
    ways = pg.evaluate("""() => { const out = {};
      for (const [reg, sid] of [['union', '1862-winter'], ['union', '1863-winter'], ['confederacy', '1861-autumn'], ['confederacy', '1862-winter']]){
        S.region = reg; out[reg + ' ' + sid] = svcDraftWay({ id: sid }).id }
      S.region = 'union'; return out }""")
    check(ways == {"union 1862-winter": "regimental_recruiting", "union 1863-winter": "distribution_camp",
                   "confederacy 1861-autumn": "regimental_recruiting", "confederacy 1862-winter": "camp_of_instruction"},
          f"drafts by the army's way of the time ({ways})")


def lost_in_fights(pg):
    """Followers lost in a fight come off the team builder: the roller sends each follower's fate by
    his id (dead, taken or left behind, a serious wound invalided; a light one stays), once; the field
    map its follower units' losses by career."""
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "horse_musket")
    pg.select_option("#sel-region", "british_pen")
    pg.select_option("#sel-template", "company")
    pg.click("#btn-roll")
    ids = pg.evaluate("() => S.crew.map(f => f.fid)")
    check(len(ids) >= 12 and len(set(ids)) == len(ids) and all(ids), f"each follower has his own id ({len(ids)} mustered)")
    pg.click(SEND)
    pg.wait_for_selector(ADDTEAM)
    pg.click(ADDTEAM)
    sent = pg.evaluate("""() => {
      const F = S.chars.filter(c => c.follower), fate = {}, sev = {};
      fate[F[0].id] = "killed"; fate[F[1].id] = "taken"; fate[F[2].id] = "left"; fate[F[3].id] = "wounded"; fate[F[4].id] = "wounded"; fate[F[5].id] = "died";
      sev[F[3].id] = "serious"; sev[F[4].id] = "light";
      fighterFate = c => fate[c.id] || null;
      worstWound = c => ({ sev: sev[c.id] });
      followersBack();
      const fx = Object.entries(DATA.wounds).find(([k]) => k.endsWith('|light'));
      F[4].wounds = [{ loc: 'face', mech: fx[0].split('|')[1], sev: 'light', graze: false, fx: structuredClone(fx[1]), treated: '' }];
      F[4].state = { id: 'out' }; F[4].blood = 3; F[4].fatigue = 4; save();   // the light one stays, as the fight left him
      const again = followersToSend().length;
      return { fids: F.slice(0, 6).map(c => c.follower.fid), back: JSON.parse(localStorage.getItem('gravewounds-followers-back')), again, log: S.afterLog[0] } }""")
    fates = [o["fate"] for o in sent["back"][0]["fates"]]
    check(fates == ["dead", "taken", "taken", "invalided", "dead"] and sent["again"] == 0,
          f"the roller sends the dead, the taken and left behind, the seriously wounded; the lightly wounded stays; each once ({fates}, {sent['log']!r})")
    pg.goto(BASE + "team.html")
    pg.wait_for_function("() => S.crew.length === 11")
    t = pg.evaluate("() => [S.crew.map(f => f.fid), S.flost.length, S.fcounts.reduce((a, [, n]) => a + n, 0), S.msg]")
    gone = [n for k, n in enumerate(sent["fids"]) if k != 4]
    check(not any(n in t[0] for n in gone) and sent["fids"][4] in t[0] and t[1] == 5 and t[2] == 11,
          f"the team builder takes them off its followers, their careers to the drafts ({t[3]!r})")
    out = pg.evaluate("() => { const c = S.team[1]; svcState().with[c.pid] = false; return c.pid }")   # as if taken in the season roll: no longer serving
    pg.evaluate("() => { const W = SVC.war('peninsula'); S.svcSmall = SVC.smallFight(W, 'campaign', svcD100, 'picket'); svcPlayFight() }")
    pg.wait_for_function(AT_ROLLER)
    pg.wait_for_selector(HANDOFF)
    pg.click(HANDOFF)
    pg.wait_for_function(NO_HANDOFF)
    tbl = pg.evaluate("() => S.table")
    check(tbl == "peninsular-1808-14-officers", f"the roller fights it on the war's table ({tbl})")
    fol = pg.evaluate("() => S.chars.filter(c => c.follower).map(c => [c.follower.fid, !!c.followerSent])")
    check(sorted(f for f, _ in fol) == sorted(t[0]) and not any(x for _, x in fol),
          f"the next small fight brings the followers as the team builder has them now (the lost gone), each to be sent back again ({len(fol)})")
    stayed = pg.evaluate(f"() => {{ const c = S.chars.find(x => x.follower && x.follower.fid === {json.dumps(sent['fids'][4])}); return c ? [c.wounds.length, c.state?.id !== 'out', c.blood === poolOf(c), c.fatigue] : null }}")
    check(stayed == [0, True, True, 0], f"a season on, the follower who stayed with a light wound comes healed, rested and on his feet ({stayed})")
    here = pg.evaluate("() => S.chars.filter(c => c.uid && c.forceId != null).map(c => c.sheet.pid)")
    check(out not in here and len(here) >= 1, f"and only the named men serving now: the man no longer with the battalion stays out ({out}, {here})")
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    pg.click("#btn-field")
    pg.wait_for_selector("#btn-teamin")
    pg.click("#btn-teamin")
    got = pg.evaluate("""() => {
      S.after = afterUnits().map(() => ({ killed: 0, died: 0, left: 0, taken: 0, cases: [] }));
      const i = S.units.findIndex(u => u.team_career === 'line');
      S.after[i] = { killed: 2, died: 1, left: 1, taken: 1, cases: [{ step: trStep(TR.wounds.start.serious) }, { step: trStep(TR.wounds.start.light) }] };
      followersBack();
      return [i, JSON.parse(localStorage.getItem('gravewounds-followers-back'))] }""")
    check(got[0] >= 0 and got[1][0]["counts"] == [{"career": "line", "dead": 3, "taken": 2, "invalided": 1}],
          f"the field map sends its follower unit's losses by career ({got})")
    pg.goto(BASE + "team.html")
    pg.wait_for_function("() => S.crew.length === 5")
    check("From the field map:" in pg.evaluate("() => S.msg"), "and the team builder takes six of the line off at random")
    units = pg.evaluate("() => { S.fcounts.push(['surgeon', 2]); S.crew.push(...makeFollowers(S.region, [['surgeon', 2]], 'default', realDice)); return fieldUnits() }")
    check(units[0].get("medic_careers") == ["surgeon", "surgeon"], f"followers of a healing career go with the biggest unit as its medics, by career ({units})")
    pg.goto(BASE + "field.html")
    med = pg.evaluate("""() => { const u = { team_medics: ['surgeon', 'surgeon', 'surgeon'], start: 10 };
      const all = medicsLost(u, { killed: 6, died: 0, left: 0, taken: 4, cases: [] }), none = medicsLost(u, { killed: 0, died: 0, left: 0, taken: 0, cases: [] });
      return [all.length, all.every(x => x.career === 'surgeon' && x.dead + x.taken === 1), none.length] }""")
    check(med == [3, True, 0], f"the medics are lost at the unit's loss rate: all of a unit that lost every man, none of one that lost none ({med})")


def run(p):
    br = p.chromium.launch()
    pg = br.new_page(viewport={"width": 1400, "height": 1100})
    errors = []
    pg.on("pageerror", lambda e: errors.append(str(e)))
    pg.on("dialog", lambda d: d.accept())
    pg.goto(BASE + "team.html")
    pg.evaluate(CLEAR)
    pg.reload()
    pg.select_option("#sel-era", "horse_musket")
    pg.select_option("#sel-region", "british_pen")
    pg.select_option("#sel-template", "company")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    check("Summer 1808" in pg.inner_text(SERVICE), "the battalion's war starts in summer 1808")
    k = pg.evaluate("() => SVC.war('peninsula').seasons.findIndex(s => s.id === '1811-spring')")
    pg.select_option("#sv-season", str(k))
    check("Albuera" in pg.inner_text(SERVICE) and "Fuentes" in pg.inner_text(SERVICE), "spring 1811 lists Fuentes de Oñoro and Albuera")
    check(not pg.is_checked("input[data-svat=albuera]") and pg.is_checked("input[data-svat=fuentes]"),
          "Albuera (Beresford's corps) is not ticked by default; Fuentes (the main army) is")
    pg.check("input[data-svat=albuera]")
    pg.select_option("select[data-svunit=albuera]", "0")
    seed = pg.evaluate(FIND)
    check(seed is not None, f"a season with a hit found (seed {seed})")
    pg.evaluate(SEEDED, seed)
    n = pg.evaluate(TEAM_N)
    pg.click("#btn-serve")
    log = pg.inner_text(SERVICE)
    check("hit at Albuera" in log and "66%" in log, "the log gives the hit at Albuera at the 1/57th's 66%")
    q = pg.evaluate(QUEUE)
    check(len(q) >= 1 and all(h["table"] == "peninsular-1808-14-all-hits" and h["weapon"] for h in q),
          f"{len(q)} hit(s) wait for the roller, on the army's table, each with a weapon")
    served = pg.evaluate("() => { const X = readXp(); return S.team.map(c => [(X[c.pid] || {}).served || 0, c.rolled_days]) }")
    check(len(served) == n and all(s == [91, 91] for s in served), f"each man's 91 days count toward his term, as rolled ({served[:2]})")
    check(pg.evaluate("() => S.service.i") == k + 1 and "Summer 1811" in pg.inner_text("#sv-season option:checked"), "the calendar moves on to summer 1811")

    lived = pg.evaluate("""() => { const one = { randint: (a) => a }, out = [];
      for (const rolled of [0, xpTermDays()]){
        const c = structuredClone(S.team.find(m => m.career === 'line'));
        c.served = 0; c.rolled_days = rolled; const was = (c.old || []).length;
        const r = xpSeason(c, [], xpTermDays(), one);
        out.push([r.terms, (c.old || []).length - was, c.rolled_days]);
      }
      return out }""")
    check(lived[0][:2] == [1, 1] and lived[1] == [1, 0, 0], f"a term of rolled seasons gives no lifepath wound chance ({lived})")

    pg.click(SEND)
    pg.wait_for_function(AT_ROLLER, timeout=15000)
    pg.wait_for_function("() => typeof S === 'object' && Array.isArray(S.chars)", timeout=10000)
    pg.get_by_role("button", name="Add the team").first.click()
    pg.wait_for_function("() => S.chars.some(c => c.uid)", timeout=10000)
    pg.wait_for_selector("button[data-map=svcroll]")
    first = q[0]
    pg.click("button[data-map=svcroll]")
    pg.wait_for_function("() => S.hit", timeout=8000)
    hit = pg.evaluate("() => ({ who: defenderChar().name, weapon: S.weapon, table: S.table, attacker: S.attacker })")
    check(hit["who"] == first["name"] and hit["weapon"] == first["weapon"] and hit["table"] == first["table"] and hit["attacker"] == -1,
          f"the roller rolls {first['name']}'s wound with the season's weapon and no attacker ({hit})")
    check(len(pg.evaluate(QUEUE)) == len(q) - 1, "and it leaves the queue")
    check("A hit from the season (" in pg.inner_text("#result"), f"the roll says it is a hit from the season, not a stray shot ({pg.inner_text('#result')[:200]!r})")
    pg.click("#btn-apply")
    track = pg.evaluate(f"""() => {{ const n = Object.values(readNamed()).find(x => x.name === {json.dumps(first['name'])}); return n ? (n.health.cases || []).filter(k => k.d === 'wound').length : -1 }}""")
    check(track >= 1, f"applied, his wound goes onto his wound track in the shared record ({track})")
    wounded = first["name"]
    named = pg.evaluate("() => S.chars.filter(c => c.uid && !c.dead).length")

    # the season's small fight, played: back on the team builder, the picket at night goes to the roller
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    pg.evaluate("() => { const W = SVC.war('peninsula'); S.svcSmall = SVC.smallFight(W, 'quarters', svcD100, 'picket'); render() }")
    box = pg.inner_text(SERVICE)
    check("A picket attacked at night" in box and "Hold the bridge" in box and "Barba del Puerco" in box, "the small fight is shown: what the accounts say, the sizes and the aims")
    check(pg.locator("#sv-fight option").count() == 8, "the GM can pick any of the war's 8 small fights")
    pg.select_option("#sv-fight", "foragers")
    check("French foragers caught at dawn" in pg.inner_text(SERVICE), "picking another rolls its sizes")
    fault = pg.evaluate("""() => { const was = S.svcSmall; S.svcSmall = { ...was, id: 'no-such-fight' }; S.msg = '';
      let r; try { svcPlayFight(); r = S.msg } catch { /* the fault itself, as wanted */ r = 'thrown' } S.svcSmall = was; return r }""")
    check(fault == "thrown", f"a fault in building the fight shows as itself, not as the browser refusing to keep it ({fault!r})")
    pg.select_option("#sv-fight", "picket")
    pg.click("#btn-svplay")
    pg.wait_for_function(AT_ROLLER, timeout=15000)
    pg.wait_for_selector(HANDOFF, timeout=10000)
    check("From a season with the battalion" in pg.inner_text("#map-actions"), "the roller offers the small fight")
    pg.click(HANDOFF)
    pg.wait_for_function(NO_HANDOFF, timeout=8000)
    sides = pg.evaluate("""() => { const b = S.chars.filter(c => sideOf(c) === 'British'), f = S.chars.filter(c => sideOf(c) === 'French');
      return { b: b.length, named: b.filter(c => c.uid).length, f: f.length, fw: [...new Set(f.map(c => c.weapon))], notes: S.pending.join(' | ') } }""")
    check(sides["named"] == named and sides["b"] >= named and sides["f"] >= 1,
          f"the team's {named} named men fight in the picket with its comrades, against the French ({sides['b']} and {sides['f']})")
    check(sides["fw"] == ["musket_smoothbore"], f"the French carry the fight's weapon ({sides['fw']})")
    check("Hold the bridge" in sides["notes"] and "It ends" in sides["notes"] and "Cope" in sides["notes"], "the aims, the end and the source are in the fight's notes")
    check(pg.evaluate("() => S.weather.cond") == "rain", "in the rain, as the fight says")
    dark = pg.evaluate("""() => { const was = S.weapon; S.weapon = 'musket_smoothbore'; const a = S.chars.find(c => c.uid);
      const out = { light: S.weather.light, far: darkOnAttack({ blocked: null, penalty: 0, notes: [] }, 30, a).blocked || '',
               near: darkOnAttack({ blocked: null, penalty: 0, notes: [] }, 10, a).penalty };
      S.weapon = was; return out }""")
    check(dark["light"] == "night" and "Dark night" in dark["far"] and dark["near"] == 20,
          f"in a dark night: no aimed shot beyond 25 hexes, and -20% within ({dark})")
    count = pg.evaluate("() => S.mapMsg.match(/The picket \\(British\\), (\\d+ of its \\d+ men|its \\d+ men)/)?.[1] || ''")
    check(count.startswith(str(sides["b"]) + " of its") or count == f"its {sides['b']} men" or (count.startswith("its ") and int(count.split()[1]) <= sides["b"]),
          f"the setup counts the team's men in the picket ({count}; {sides['b']} on the map)")
    odds = pg.evaluate("""() => { const m = S.mapMsg, b = m.match(/The picket \\(British\\), (?:(\\d+) of )?its (\\d+) men/), f = m.match(/\\(French\\), (?:(\\d+) of )?its (\\d+) men/);
      return { bHere: +(b[1] || b[2]), bAll: +b[2], fHere: +(f[1] || f[2]), fAll: +f[2] } }""")
    want = max(1, min(40, round(odds["bHere"] * odds["fAll"] / odds["bAll"])))
    check(odds["fHere"] == min(want, odds["fAll"]), f"the French come in at the rolled odds, not capped at 8 against the whole team ({odds}, wanted {want})")
    # the picket's own end: the GM's script plays both sides and stops when the roller calls it
    end = pg.evaluate("""() => {
      S.gm = { on: true, auto: false, sides: {} };
      for (const sd of new Set(S.chars.map(sideOf))) S.gm.sides[sd] = { ...gmSide(sd), ctl: "script", stance: "steady", quality: "regular" };
      let r = "acted", n = 0;
      try{ while (r === "acted" && n++ < 6000) r = gmStep() }catch(e){ return { err: e.stack } }
      renderChars();
      const fd = S.chars.filter(c => sideOf(c) === 'French'), down = fd.filter(c => isDown(c) || c.taken || c.fled).length;
      return { r, round: S.round, msg: S.gmMsg, called: S.fightEnd && S.fightEnd.called, won: S.wonBy, frac: down / fd.length,
               bar: (document.querySelector('#btn-fight-on') || {}).id || '', log: S.log.map(l => l.lines.join(' ')).join(' ') + ' ' + (S.pending || []).join(' ') } }""")
    check(not end.get("err"), f"the script plays the picket ({end.get('err', '')[:300]})")
    called = end.get("called") or {}
    check(end["r"] == "over" and "The fight's end" in end["msg"], f"the script stops at the fight's own end ({end['msg']}, round {end['round']})")
    check((called.get("won") == "British" and (end["frac"] >= 0.33 or end["round"] > 6 or called.get("why") == "French break")) or called.get("won") == "French",
          f"called by its end: 6 rounds, a third of the French down, or a side broken ({called}, French down {end['frac']:.2f})")
    check(end["won"] == called.get("won") and end["bar"] == "btn-fight-on", "the winner is marked, and the GM may fight on")
    pg.click("#btn-fight-on")
    on = pg.evaluate("""() => ({ won: S.wonBy, r: gmStep(), on: S.fightEnd.on, msg: S.gmMsg,
      able: new Set(S.chars.filter(c => !isOut(c) && !c.taken && !c.fled && !c.away).map(sideOf)).size })""")
    check(on["on"] and (on["r"] != "over" or on["able"] < 2), f"Fight on sets the call aside and the script plays on, unless one side has no one left able ({on})")
    # held ground: the position lost at a round's end, and men getting away by their own edge
    held = pg.evaluate("""() => {
      const snap = JSON.stringify({ chars: S.chars, end: S.fightEnd, won: S.wonBy, broken: S.broken }), E = S.fightEnd, { cols, rows } = mapSize();
      const out = { hold: E.hold, radius: E.position.radius };
      S.broken = {}; S.wonBy = null; E.called = null; E.on = false; E.down = {}; E.rounds = null;
      const br = S.chars.filter(c => sideOf(c) === 'British'), fr = S.chars.filter(c => sideOf(c) === 'French');
      for (const c of S.chars){ c.taken = false; c.fled = false; c.away = false; c.blood = 100; c.wounds = []; c.state = null }
      br.forEach((c, i) => { c.pos = [cols - 1, i] });                       // all the picket out of the position
      fr[0].pos = E.position.centre.slice();                                  // a Frenchman in it
      out.midRound = fightEndCheck(false);
      out.atEnd = fightEndCheck(true);
      E.called = null; S.wonBy = null; E.hold = null; E.away = { side: 'French', share: 0.25 };
      const k = E.edges.French, edge = [[0, null], [cols - 1, null], [null, 0], [null, rows - 1]][k];
      fr.slice(0, Math.ceil(fr.length / 4)).forEach((c, i) => { c.pos = [edge[0] ?? i, edge[1] ?? i] });
      out.away = fightEndCheck(false);
      out.gone = fr.filter(c => c.away && !c.pos).length; out.need = Math.ceil(fr.length / 4);
      out.isOut = fr.filter(c => c.away).every(isOut);
      const was = JSON.parse(snap); S.chars = was.chars; S.fightEnd = was.end; S.wonBy = was.won; S.broken = was.broken;
      return out }""")
    check(held["hold"] == "British" and held["midRound"] is None and (held["atEnd"] or {}).get("won") == "French"
          and "hold" in held["atEnd"]["why"], f"the picket's bridge: lost at a round's end once the French stand in it and the picket does not ({held})")
    check((held["away"] or {}).get("won") == "French" and held["gone"] >= held["need"] and held["isOut"],
          f"and men on their own edge leave the field: once a share have got away, their side wins ({held['away']}, {held['gone']} gone, {held['need']} needed; any already on the edge go too)")
    # a man taken in a fight his side then wins is retaken
    rt = pg.evaluate("""() => { const c = S.chars.find(x => sideOf(x) === 'British' && x.sheet?.pid), was = S.wonBy;
      c.taken = true; markLost(c.sheet.pid, 'taken prisoner'); setWon('British');
      const out = { taken: c.taken, lost: !!(readPurses()[c.sheet.pid] || {}).lost, log: (S.pending || []).at(-1) }; S.wonBy = was; return out }""")
    check(not rt["taken"] and not rt["lost"] and "retaken" in (rt["log"] or ""), f"a man taken in a fight his side wins is retaken ({rt})")
    # a broken scripted side: the down beside an enemy taken, the down alone left, the held break away or are taken, the rest run
    yl = pg.evaluate("""() => {
      const snap = JSON.stringify({ chars: S.chars, gm: S.gm, broken: S.broken }), ri = DICE.randint, { cols, rows } = mapSize();
      S.gm = { on: true, auto: false, sides: { British: { ...gmSide('British'), ctl: 'script' }, French: { ...gmSide('French'), ctl: 'script' } } };
      const br = S.chars.filter(c => sideOf(c) === 'British' && !namedMan(c)).slice(0, 5), fr = S.chars.find(c => sideOf(c) === 'French');
      const nm = S.chars.filter(c => sideOf(c) === 'British' && c.sheet?.pid).slice(0, 2);
      for (const c of S.chars){ c.pos = null; c.taken = false; c.fled = false; c.away = false; c.blood = 100; c.wounds = []; c.state = null }
      S.broken = {};
      fr.pos = [10, 8]; br[0].pos = [11, 8]; br[0].state = { id: 'out' };          // down, an enemy beside him
      br[1].pos = [2, 2]; br[1].state = { id: 'out' };                            // down, no one near
      br[2].pos = [9, 8]; br[3].pos = [10, 9]; br[4].pos = [cols - 2, rows - 2];  // two held, one clear
      nm[0].pos = [11, 7]; nm[0].state = { id: 'out' }; nm[1].pos = [9, 9];        // the team's named men: one down beside the enemy, one held
      const asked = gmQuarter().join(' ');
      const rolls = [1, 100]; DICE.randint = (a, b) => (rolls.length ? rolls.shift() : ri(a, b));
      S.broken.British = true;
      const lines = gmYield('British');
      DICE.randint = ri;
      const out = { down0: [isDown(br[0]), br[0].taken], down1: br[1].taken || br[1].fled, held: [br[2].fled, br[3].taken], clear: br[4].fled, lines,
        named: [nm[0].taken, nm[0].fled, nm[1].taken, nm[1].fled || isDown(nm[1]), nm.length], askedNamed: nm.some(c => asked.includes(c.name)) };
      const was = JSON.parse(snap); S.chars = was.chars; S.gm = was.gm; S.broken = was.broken;
      return out }""")
    check(yl["down0"] == [True, True] and not yl["down1"] and yl["held"] == [True, True] and yl["clear"],
          f"a broken scripted side: the down beside an enemy taken, the down alone left, the held break away or are taken, the rest run ({yl['lines']})")
    ba = pg.evaluate("""() => { const f = S.chars.find(c => !c.sheet?.stats), m = S.chars.find(c => c.sheet?.stats), was = f.rating, out = [];
      for (const q of ['green', 'regular', 'veteran']){ f.rating = q; out.push(breakAwayAt(f)) }
      f.rating = was; out.push(breakAwayAt(m) === Math.max(statOf(m, 'agi'), skillAt(m, 'dodge'))); return out }""")
    check(ba == [35, 50, 65, True], f"a held man breaks away on his Agility or Dodge, or without a sheet on his quality: green 35, regular 50, veteran 65 ({ba})")
    check(yl["named"] == [False, False, False, True, 2] and not yl["askedNamed"],
          f"but the script never surrenders the team's named men: down, he is left where he lies; held, he breaks away (or, down from what he carried in from the season, lies); none asks for quarter ({yl['named']}, {yl['lines']})")
    # the picket was played only to see its end: its losses do not go on to the team builder
    pg.evaluate("() => { const all = readPurses(); for (const k in all) delete all[k].lost; writePurses(all); for (const c of S.chars) c.taken = false; save() }")
    # a case carried from the last season: the panel shows it, and the next season begins from it
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    asat = pg.evaluate("""() => { const W = SVC.war('peninsula'), f = W.small_fights.find(x => x.id === 'picket');
      return [svcAsAt(W, f, W.seasons.find(x => x.id === f.at)), svcAsAt(W, f, W.seasons[0])] }""")
    check(asat[0] == "" and "a fight of this kind, as in spring 1810" in asat[1], f"a fight from another season says so in its notes ({asat})")
    pg.evaluate("""hurt => { const c = S.team.find(x => x.name !== hurt) || S.team[0], H = { cases: [{ d: 'flux', inc: 0, step: 2, peak: 2, shown: 9, chronic: true }], immune: {}, had: {}, dead: 0 };
      c.svcHealth = H; const all = namedStore(), n = namedOf(all, c); if (n){ n.health = H; localStorage.setItem(NAMED_STORE, JSON.stringify(all)) } render() }""", wounded)   # not the man wounded last season: his wound stays on his track
    check("still serious from last season" in pg.inner_text(SERVICE), "a man still sick at the season's end shows so on the panel")
    pg.evaluate(SEEDED, 11)
    pg.click("#btn-serve")
    first = pg.evaluate("() => S.svclog.join(' ')")
    check("began the season serious" in pg.inner_text(SERVICE), f"and his next season begins from it ({first[:120]})")
    check(f"{wounded}: began the season" in pg.inner_text(SERVICE) and "(his wounds)" in pg.inner_text(SERVICE),
          f"the man hit last season begins this one with his wounds on the track ({wounded}: {pg.evaluate("n => S.svclog.find(l => l.startsWith(n)) || S.svclog.join(' ')", wounded)[:300]!r})")

    # the second war: a Union company in the East
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "civil_war")
    pg.select_option("#sel-region", "union")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('acw_union_east').seasons.findIndex(s => s.id === '1863-summer')")
    pg.select_option("#sv-season", str(k))
    check("Summer 1863" in pg.inner_text("#sv-season option:checked") and "Gettysburg" in pg.inner_text(SERVICE), "a Union team serves the war in the East: summer 1863 has Gettysburg")
    check("1st Minnesota (82%)" in pg.inner_text("select[data-svunit=gettysburg]"), "with the 1st Minnesota's own 82%")
    check(pg.evaluate("() => SVC.weaponFor(SVC.war('acw_union_east'), 50)") == "rifle_musket", "and its hits come mostly from the rifle-musket")
    # and the other side: a Confederate team with the 4th Virginia
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "civil_war")
    pg.select_option("#sel-region", "confederacy")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('acw_confederate_east').seasons.findIndex(s => s.id === '1863-spring')")
    pg.select_option("#sv-season", str(k))
    cs = pg.inner_text(SERVICE)
    check("Chancellorsville" in cs and "4th Virginia (48%)" in pg.inner_text("select[data-svunit=chancellorsville]"),
          "a Confederate team serves with the Stonewall Brigade: spring 1863 has Chancellorsville, with the 4th Virginia's own 48%")
    check(pg.evaluate("() => SVC.warsFor('civil_war', 'confederacy').map(W => W.id).join()") == "acw_confederate_east", "and only the Confederate war is offered to it")
    tk = pg.evaluate("""() => { const q = [99, 99, 10]; const rng = () => q.length ? q.shift() : 99;
      const r = SVC.serve('acw_confederate_east', '1864-spring', [{ name: 'x', endurance: 50, unit: { spotsylvania: 0 } }], ['spotsylvania'], rng).men[0];
      return r.taken }""")
    check((tk or {}).get("action") == "spotsylvania" and tk.get("pct") == 63, f"at the Mule Shoe as the 4th Virginia, a man not hit is taken on 63% ({tk})")
    pg.evaluate("""() => { const V = svcState(), W = SVC.war('acw_confederate_east'); V.war = W.id; V.i = W.seasons.findIndex(s => s.id === '1864-spring');
      V.unit = { spotsylvania: 0 }; V.at = { wilderness: false, spotsylvania: true }; window.__q = [99, 99, 10];
      realDice.randint = (a, b) => (window.__q.length ? window.__q.shift() : b); render() }""")
    n0 = pg.evaluate(TEAM_N)
    pg.click("#btn-serve")
    took = pg.evaluate("() => ({ log: S.svclog.join(' '), team: S.team.length, prisoners: (S.prisoners || []).length })")
    check("taken prisoner at Spotsylvania" in took["log"] and took["team"] < n0 and took["prisoners"] >= 1,
          f"served, a man taken goes to the Prisoners ({n0} -> {took['team']}, {took['prisoners']} prisoners: {took['log'][:300]!r})")
    # layer 3: the edge of Badajoz, a British company in spring 1812
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "horse_musket")
    pg.select_option("#sel-region", "british_pen")
    pg.select_option("#sel-template", "company")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('peninsula').seasons.findIndex(s => s.id === '1812-spring')")
    pg.select_option("#sv-season", str(k))
    ed = pg.inner_text(SERVICE)
    check(all(x in ed for x in ("The edge of Badajoz", "The sortie on the parallels", "Volunteers for the forlorn hope", "Into the ditch", "Two hours at the breaches")),
          "spring 1812: Badajoz has its edge, four scenes before the storm")
    check(pg.locator("button[data-svedgeplay='badajoz:ditch']").count() == 0, "the ditch waits for volunteers")
    vol = pg.evaluate("() => S.team[0].name")
    pg.locator("input[data-svedgechoice^='badajoz:hope:']").first.check()
    check(pg.locator("button[data-svedgeplay='badajoz:ditch']").count() == 1, f"a volunteer ({vol}): the ditch can be played or rolled")
    pg.evaluate("() => { window.__q = [99, 1, 1, 1, 1, 1, 1, 1]; realDice.randint = (a, b) => (window.__q.length ? window.__q.shift() : b) }")   # the first man fails his Nerve, the rest hold
    pg.click("button[data-svedgecheck='badajoz:breaches']")
    chk = pg.evaluate("() => S.svclog.at(-1)")
    check("fails (99" in chk and "kept back" not in chk, f"two hours at the breaches: each man's Nerve rolled ({chk[:160]})")
    at = pg.evaluate("() => { const V = svcState(), W = SVC.war(V.war); return svcEdgeAt(W, V, 'badajoz') }")
    first = pg.evaluate("() => S.team[0].pid")
    check(at.get(first) == "reserve", f"the man who failed his Nerve stands in reserve at the storm, the check after the choice ({at})")
    pg.evaluate("() => { const V = svcState(); const st = svcEdge(V, 'badajoz'); delete st.failed[S.team[0].pid]; render() }")
    at = pg.evaluate("() => { const V = svcState(), W = SVC.war(V.war); return svcEdgeAt(W, V, 'badajoz') }")
    check(at.get(first) == "thick", f"a volunteer who holds stands in the thick of it ({at})")
    pg.evaluate("() => { realDice.randint = (a, b) => b }")
    pg.click("#btn-serve")
    served = pg.evaluate("() => S.svclog.join(' ')")
    check("in the thick of it at badajoz, as its edge set" in served.lower(), f"served: the storm rolled with the volunteer in the thick of it ({served[:240]!r})")
    h = pg.evaluate("""() => { const V = svcState(); V.i -= 1; V.edge = { badajoz: { done: {}, chosen: { hope: { [S.team[0].pid]: true } }, failed: {} } }; render();
      let got = null;
      const set = localStorage.setItem.bind(localStorage); localStorage.setItem = (k, v) => { if (k === 'gravewounds-handoff') got = JSON.parse(v); else set(k, v) };
      try{ svcEdgePlay('badajoz:ditch') }catch(e){}
      localStorage.setItem = set; return got }""")
    check(h and h["only"] == [first] and h["light"] == "night" and h["title"] == "Into the ditch", f"the ditch goes to the roller with only the volunteer, at night ({(h or {}).get('only')}, {(h or {}).get('light')})")
    pg.wait_for_function(AT_ROLLER)
    # the third war: an English retinue in Henry V's war, and an escalade played (the team attacking)
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "medieval")
    pg.select_option("#sel-region", "england")
    pg.select_option("#sel-template", "retinue")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('henry_v').seasons.findIndex(s => s.id === '1415-autumn')")
    pg.select_option("#sv-season", str(k))
    check("Agincourt" in pg.inner_text(SERVICE) and "play it on the field map" in pg.inner_text(SERVICE).lower(),
          "an English retinue's autumn 1415 has Agincourt, which can be played on its battlefield")
    pg.click(SEND)
    pg.wait_for_function(AT_ROLLER, timeout=15000)
    pg.wait_for_function("() => typeof S === 'object' && Array.isArray(S.chars)", timeout=10000)
    pg.get_by_role("button", name="Add the team").first.click()
    pg.wait_for_function("() => S.chars.some(c => c.uid)", timeout=10000)
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    men = pg.evaluate(TEAM_N)   # the retinue's own, not the company's men still on the roller from before
    pg.evaluate("() => { const W = SVC.war('henry_v'); S.svcSmall = SVC.smallFight(W, 'campaign', svcD100, 'escalade'); render() }")
    pg.click("#btn-svplay")
    pg.wait_for_function(AT_ROLLER, timeout=15000)
    pg.wait_for_selector(HANDOFF, timeout=10000)
    pg.click(HANDOFF)
    pg.wait_for_function(NO_HANDOFF, timeout=8000)
    esc = pg.evaluate("""() => { const e = S.chars.filter(c => sideOf(c) === 'English'), f = S.chars.filter(c => sideOf(c) === 'French');
      return { named: e.filter(c => c.uid).length, f: f.length, fw: [...new Set(f.map(c => c.weapon))], fk: [...new Set(f.map(c => c.kit))], msg: S.mapMsg } }""")
    check(esc["named"] == men and esc["fw"] == ["crossbow"] and esc["fk"] == ["brigandine_sallet"],
          f"the escalade: the retinue's {men} named men go up the ladders against the guard with crossbows ({esc['named']}, {esc['fw']}, {esc['fk']})")
    check("Defending: The guard on the wall" in esc["msg"], "the French guard holds the wall; the English come in from the edge")
    # the sixth war: the same English team with Edward of March, 1459-71
    pg.goto(BASE + "team.html")
    pg.wait_for_selector("#h-service")
    pg.select_option("#sv-war", "roses_edward")
    k = pg.evaluate("() => SVC.war('roses_edward').seasons.findIndex(s => s.id === '1461-spring')")
    pg.select_option("#sv-season", str(k))
    rs = pg.inner_text(SERVICE)
    check("Towton" in rs and "Ferrybridge" in rs and "play it on the field map" in rs.lower(),
          "an English team can serve with Edward of March instead: spring 1461 has Ferrybridge and Towton, which can be played on its field")
    check(pg.evaluate("() => SVC.weaponFor(SVC.war('roses_edward'), 10)") == "longbow", "and its hits come first from the longbow")
    pg.evaluate("() => { const W = SVC.war('roses_edward'); S.svcSmall = SVC.smallFight(W, 'march', svcD100, 'bridge'); render() }")
    check("Clifford's horsemen" in pg.inner_text(SERVICE), "the bridge at dawn comes up as Ferrybridge's small fight")
    # the seventh: the same English team on the other side, with the northern Lancastrians
    pg.select_option("#sv-war", "roses_lancaster")
    k = pg.evaluate("() => SVC.war('roses_lancaster').seasons.findIndex(s => s.id === '1461-spring')")
    pg.select_option("#sv-season", str(k))
    rs = pg.inner_text(SERVICE)
    check("Towton" in rs and "Ferrybridge" in rs and "40%" in rs, f"or with the northern Lancastrians: Towton lost at 40% (the dead times two) ({rs[:200]!r})")
    pg.evaluate("() => { const W = SVC.war('roses_lancaster'); S.svcSmall = SVC.smallFight(W, 'march', svcD100, 'bridge'); render() }")
    check("Clifford's horsemen" in pg.inner_text(SERVICE) and pg.evaluate("() => SVC.war('roses_lancaster').small_fights[0].team_attacks"),
          "and the bridge at dawn from Clifford's side, attacking")
    # the fifth war: a British section in Italy
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "wwii")
    pg.select_option("#sel-region", "commonwealth")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('italy_british').seasons.findIndex(s => s.id === '1943-winter')")
    pg.select_option("#sv-season", str(k))
    it = pg.inner_text(SERVICE)
    check("Capracotta" in it and "1st Royal Sussex on Snakeshead" in pg.inner_text("select[data-svunit=cassino_feb]"),
          "a British section in Italy: the mountain winter of 1943-44, and Snakeshead with the Royal Sussex's own figure")
    check(pg.evaluate("() => SVC.war('italy_british').medicine") == 20, "with the era's medicine on the sick")

    # the fourth war: a British section on the Western Front, and its wastage in the line
    pg.goto(BASE + "team.html")
    pg.select_option("#sel-era", "wwi")
    pg.select_option("#sel-region", "british")
    pg.select_option("#sel-template", "section")
    pg.click("#btn-roll")
    pg.wait_for_selector("#h-service")
    k = pg.evaluate("() => SVC.war('western_front').seasons.findIndex(s => s.id === '1916-spring')")
    pg.select_option("#sv-season", str(k))
    check("shelled or sniped in the line: 10% a man" in pg.inner_text(SERVICE), "holding the line, each man risks the wastage in the line")
    pg.evaluate(SEEDED, 3)
    pg.click("#btn-serve")
    log = pg.inner_text(SERVICE)
    check(log.count("Shelled or sniped in the line: 10%") >= 1, "the season's log gives each man's wastage roll")
    stale = pg.evaluate("""() => { S.flost = ['line', 'archer']; const W = SVC.war('western_front'), lines = [];
      try { svcDrafts(W, W.seasons.find(x => x.state === 'trenches'), lines) } catch (e) { return e.message }
      return S.flost.length }""")
    check(stale == 0, f"a loss kept from another era's muster owes no draft and breaks nothing ({stale})")
    followers(pg)
    check(not errors, f"no page errors {errors[:3]}")
    br.close()


main(run, server)
