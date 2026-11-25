"""The GM's script in a camp with works (the roller), in a headless browser: the way round, not as the crow flies.

    python3 tools/campaign/campways.py

A fortified camp from the travel map (its ditch, bank, palisade and one gate), eight men in it and eight raiders
outside, all with swords:
- Gate barred: no way in, so the script presses up to the works as the crow flies, as before (no way round given).
- Gate open: a raider far from it goes round towards it, each step bringing him nearer by the way in.
- Half built (gaps in the palisade): the way round goes through the gaps.
- Open ground: no works, so no way round is worked out at all.

Needs Python's playwright with Chromium and a built site. Exits non-zero on any failure.
"""
import json
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "net"))
from roomharness import check, failures, serve   # noqa: E402

site, BASE, ROOMS, stop = serve()
HANDOFF = {"from": "travel", "force": {"id": 1, "name": "The camp", "side": "York", "men": 8, "type": "foot", "fatigue": 0},
           "camp": "fortified", "done": None, "built": 100, "hauled": False,
           "foes": [{"id": 2, "name": "The raiders", "side": "Lancaster", "men": 8, "type": "foot", "fatigue": 0, "km": 1, "from": "north-east"}],
           "allies": [], "place": "the camp", "ground": "open", "groundSeed": "camp", "edges": None, "day": "1 Mar", "time": "noon",
           "weather": {"cond": "fair", "wind": "calm", "ground": {"mud": 0, "snow": 0, "flood": 0}}, "surprise": None}
SET_UP = """([h, gate]) => { S.handoff = h; setupHandoff(); S.handoff = null;
  for (const items of Object.values(S.works.edges)) for (const it of items) if (it.type === 'gate') it.open = gate;
  for (const c of S.chars) c.weapon = 'sword';
  gmStart(); for (const sd of sidesInOrder()) S.gm.sides[sd].ctl = 'script'; S.gm.auto = false; renderChars() }"""
# A raider's turn: put him where he starts, give him the turn, let the script choose; -> [way round given, way before, way after, straight before, straight after]
TURN = """name => { const c = S.chars.find(x => x.name === name), foes = S.chars.filter(o => sideOf(o) !== sideOf(c));
  S.turn = c.id; S.tm = null; S.attacker = S.chars.indexOf(c); applyAttackerWeapon();
  const w = wayRound(c, foes), d = worksDistance(foes), near = h => Math.min(...foes.map(o => hexDistance(h, o.pos)));
  const before = [d(hkey(c.pos)), near(c.pos)];
  gmMove(c);
  return [!!w.pathDist, before[0], d(hkey(c.pos)), before[1], near(c.pos)] }"""

try:
    with sync_playwright() as p:
        br = p.chromium.launch()
        errors = []
        pg = br.new_page()
        pg.on("pageerror", lambda e: errors.append(str(e)))
        pg.goto(BASE + "roller.html"); pg.evaluate("() => localStorage.clear()"); pg.reload()
        pg.wait_for_function("() => typeof S === 'object' && typeof setupHandoff === 'function'")

        pg.evaluate(SET_UP, [HANDOFF, False])
        gates = pg.evaluate("() => Object.values(S.works.edges).flat().filter(i => i.type === 'gate').length")
        check(gates == 1 and pg.evaluate("() => worksStop()"), f"a fortified camp: works a man cannot cross, one gate ({gates})")
        r = pg.evaluate(TURN, "The raiders 1")
        check(not r[0], "gate barred: no way in, so no way round is given (he presses up to the works as before)")

        pg.evaluate(SET_UP, [HANDOFF, True])
        r = pg.evaluate(TURN, "The raiders 1")
        check(r[0] and r[2] < r[1], f"gate open: he goes round by the gate, nearer by the way in ({r[1]} to {r[2]} steps; as the crow flies {r[3]} to {r[4]})")

        half = {**HANDOFF, "done": 300, "built": 60}
        pg.evaluate(SET_UP, [half, False])
        pal = pg.evaluate("() => Object.values(S.works.edges).flat().filter(i => i.type === 'palisade' && intact('edge', i)).length")
        r = pg.evaluate(TURN, "The raiders 1")
        check(0 < pal < 53 and r[0] and r[2] < r[1], f"half built ({pal} palisade sides): the way round goes through the gaps ({r[1]} to {r[2]} steps)")

        pg.evaluate("() => { S.works = { edges: {}, hexes: {} }; renderChars() }")
        check(not pg.evaluate("() => worksStop()") and pg.evaluate("() => !wayRound(S.chars[0], S.chars.filter(o => sideOf(o) !== sideOf(S.chars[0]))).pathDist"),
              "open ground: no works in the way, so none is worked out (the script closes in as the crow flies)")
        check(not errors, f"no page errors {errors[:3]}")
        br.close()
finally:
    stop()

print("all checks passed" if not failures else f"{len(failures)} failure(s)")
raise SystemExit(1 if failures else 0)
