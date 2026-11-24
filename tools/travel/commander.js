// The commander on the march (templates/travelday.js), run with no page.
//   python3 tools/travel/parity.py [n] [seed]   (writes .cache/ and runs this after day.js)
"use strict";
const { assert, makeTravelDay, DATA, RULES, tally, check, fresh, snapshot } = require("./harness.js");

// The commander on the march (travelday.js command), with no page. Checked on real maps: a side given
// to it is ordered each press from what its side has seen, never from where the enemy is; the rules
// in their order (rations, rest, falling back, attacking or holding, the baggage); the side moved by
// hand is never touched; and the same dice play the same game, saved and restored or not.
const known = D => new Set(Object.values(D.S.seen[D.S.mapId] || {}).flatMap(m => Object.values(m).map(r => r.pos.join(","))));
function start(seed, mapId, side, stance){
  const D = fresh(seed).D;
  D.S.mapId = mapId;
  D.forcesHere();
  D.save();
  D.setCommander(side, stance);
  D.restore();
  return D;
}
const dest = f => (f.path && f.index < f.path.length - 1 ? f.path[f.path.length - 1].join(",") : null);
const sidesOf = D => [...new Set(D.forcesHere().map(f => f.side))];

for (const mapId of ["towton-1461", "agincourt-1415", "bull-run-1861", "generic-valley"].filter(id => DATA.maps[id])){
  const probe = start(1, mapId, "x", null), men = side => probe.forcesHere().filter(f => f.side === side).reduce((t, f) => t + f.men, 0);
  const A = sidesOf(probe).sort((x, y) => men(y) - men(x))[0];   // the stronger side: a weaker one rightly falls back rather than seek a fight
  const places = new Set((DATA.maps[mapId].places || []).filter(p => p.hex && (p.kind === "objective" || p.kind === "camp" || (p.depot || []).includes(A))).map(p => p.hex.join(",")));
  let said = [], met = false, D = null;
  check(`${mapId}: the commander attacking with ${A} orders its columns, only to places, its own columns and what it has seen`, () => {
    D = start(3, mapId, A, "attack");
    const others = () => JSON.stringify(D.forcesHere().filter(f => f.side !== A).map(f => [f.id, f.order || "halt", dest(f)]));
    const before = others();
    for (let i = 0; i < 30 && !met; i++){
      const seenBefore = known(D), ours = new Set(D.forcesHere().filter(f => f.side === A).map(f => f.pos.join(",")));
      const lines = D.command(); said.push(...lines);
      for (const f of D.forcesHere().filter(o => o.side === A && !o.with)){
        const d = dest(f);
        if (d && lines.some(l => l.includes(f.name))) assert.ok(places.has(d) || seenBefore.has(d) || ours.has(d) || known(D).has(d), `${f.name} sent to ${d}, not a place, a column of its own or a sighting`);
      }
      D.moveClock("event");
      met = Object.values(D.meetings()).length > 0;
      assert.equal(others(), before, `the side moved by hand was given orders`);
    }
    assert.ok(said.some(l => l.startsWith("The commander sends")), said.slice(0, 3).join(" | "));
  });
  check(`${mapId}: two commanders, both attacking, seek each other out: the forces meet within 40 presses`, () => {
    const E = start(3, mapId, A, "attack");
    E.setCommander(sidesOf(E).find(s => s !== A), "attack"); E.restore();
    let hit = false, lines = [];
    for (let i = 0; i < 40 && !hit; i++){ E.moveClock("event"); lines.push(E.S.msg); hit = Object.values(E.meetings()).length > 0 }
    assert.ok(hit, lines.slice(-3).join(" | "));
  });
}

check("rations gone: to its side's nearest depot", () => {
  const D = start(4, "agincourt-1415", "England", "attack"), f = D.forcesHere().find(o => o.side === "England" && o.type !== "wagons");
  f.supHungry = true;
  const depots = DATA.maps["agincourt-1415"].places.filter(p => (p.depot || []).includes("England")).map(p => p.hex.join(","));
  D.command();
  assert.ok(f.pos.join(",") === depots[0] && !dest(f) || depots.includes(dest(f)), `went to ${dest(f)}, depots ${depots}`);
});
check("exhausted: it rests until morning", () => {
  const D = start(4, "towton-1461", "York", "attack"), f = D.forcesHere().find(o => o.side === "York" && o.type !== "wagons");
  f.fatigue = 3;
  const lines = D.command();
  assert.ok(f.day > D.clockNow().day && lines.some(l => l.includes("rests")), lines.join(" | "));
});
check("beaten days ago: it falls back, not on", () => {
  const D = start(4, "towton-1461", "York", "attack"), f = D.forcesHere().find(o => o.side === "York" && o.type !== "wagons");
  f.beatenDay = D.clockNow().day;
  const lines = D.command();
  assert.ok(lines.some(l => l.includes(f.name) && l.includes("back, beaten")) || !dest(f), lines.join(" | "));
});
check("holding: it goes to the nearest objective, or makes a watched camp where it is", () => {
  const D = start(5, "towton-1461", "Lancaster", "hold");
  const objs = new Set(DATA.maps["towton-1461"].places.filter(p => p.kind === "objective").map(p => p.hex.join(",")));
  for (let i = 0; i < 12; i++){ D.command(); D.moveClock("event") }
  for (const f of D.forcesHere().filter(o => o.side === "Lancaster" && !o.with && o.type !== "wagons"))
    assert.ok(objs.has(dest(f)) || D.campHere(f) || f.order !== "march", `${f.name}: ${f.order} to ${dest(f)}`);
});
check("the same dice play the same game, saved and restored part way or not", () => {
  const run = stop => {
    let D = start(7, "towton-1461", "York", "attack");
    for (let i = 0; i < 14; i++){
      if (i === stop){ D.save(); D = makeTravelDay(DATA, RULES, { roll100: D.roll100 }); D.restore() }
      D.moveClock(i % 3 ? "event" : "hour");
    }
    return snapshot(D);
  };
  assert.equal(run(null), run(null));
  assert.equal(run(6), run(null));
});
check("moved by hand again, a side is left alone", () => {
  const D = start(8, "towton-1461", "York", "attack");
  D.setCommander("York", null); D.restore();
  assert.deepEqual(D.command(), []);
});

console.log(`${tally.passed} passed, ${tally.failed} failed`);
process.exit(tally.failed ? 1 : 0);
