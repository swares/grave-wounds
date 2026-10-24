/* The campaign: one record over the pages. The pages keep their own state in the browser and hand
   pieces to each other (the team to the roller, a fight from the travel map, a battle's result back).
   This file reads all of it, with no page, and says where the campaign stands and what comes next.

   CAMPAIGN.read(store) -> {key: text} of every Grave Wounds entry in the browser's storage, as stored
     (the narrator's settings left out: they may hold a service key).
   CAMPAIGN.status(raw, CD) -> what the pages hold now: the team, the named men, the travel map's
     day and forces, a fight handed off and not yet set up, the roller's and field map's fights.
   CAMPAIGN.suggest(phase, status, seen) -> {phase, why, mark} when the pages show the campaign has
     moved on (a fight sent from the travel map, a fight won or a battle's result sent back), else null.
     `seen` is the record of what was already noticed, so a thing is noticed once.
   CAMPAIGN.notices(status, seen, CD, temp) -> {news, forget}: what is worth the log by itself, once each: a
     named man's death or capture, sickness breaking out, a force out of supplies, a promotion, the end
     of a day, the end of a season.
   CAMPAIGN.saveFile(raw) / CAMPAIGN.checkFile(obj): the whole game as one file (every entry as stored),
     and the check that a file read back is one: the entries to write back.
   CD is the campaign page's data: the maps', eras', weather's and diseases' names. build.py puts this file into the campaign
   page at its CAMPAIGN_JS marker; in Node it is a module (tools/campaign/test.js). */
const CAMPAIGN = (() => {
  const PREFIX = "gravewounds-";
  const KEEP_OUT = new Set(["gravewounds-narrator"]);   // a service key may be in it: never in a save file
  const RECORD = "gravewounds-campaign";
  const PHASES = [
    { id: "muster", name: "Muster", page: "team.html" },
    { id: "march", name: "March", page: "travel.html" },
    { id: "fight", name: "Fight", page: "roller.html" },
    { id: "aftermath", name: "Aftermath", page: "roller.html" },
    { id: "downtime", name: "Downtime", page: "team.html" },
  ];
  const FORMAT = "grave-wounds-save";

  function read(store){
    const out = {};
    for (let i = 0; i < store.length; i++){
      const k = store.key(i);
      if (k?.startsWith(PREFIX) && !KEEP_OUT.has(k)) out[k] = store.getItem(k);
    }
    return out;
  }
  function parsed(raw){                              // the entries as values; a few are plain text (lethality, units)
    const out = {};
    for (const [k, v] of Object.entries(raw)){ try { out[k] = JSON.parse(v) } catch { out[k] = v } }
    return out;
  }
  const obj = v => (v && typeof v === "object" ? v : null);

  function teamStatus(snap, CD){
    const tb = obj(snap["gravewounds-team-builder"]) || {}, team = Array.isArray(tb.team) ? tb.team : [], held = tb.prisoners || [];
    const who = m => m.pid || m.name;
    return { era: tb.era || null, eraName: CD.eras?.[tb.era] || tb.era || null, men: team.map(m => m.name).filter(Boolean),
      lost: (tb.losses || []).length, prisoners: held.length,
      held: held.map(m => ({ id: who(m), name: m.name || "?" })),
      ranks: team.filter(m => m.rank).map(m => ({ id: who(m), name: m.name || "?", rank: m.rank })) };
  }
  function namedStatus(snap){
    const byUid = obj(snap["gravewounds-named"]) || {}, all = Object.values(byUid), purses = obj(snap["gravewounds-purses"]) || {};
    const fallen = Object.entries(byUid).filter(([, n]) => n.dead).map(([uid, n]) => ({ uid, name: n.name || "?", died: n.died || null,
      why: purses[n.pid]?.lost?.why || null, map: n.map || null, force: n.force ?? null }));
    return { men: all.length, withForce: all.filter(n => n.map && n.force !== undefined && n.force !== null).length,
      dead: fallen.length, sick: all.filter(n => (n.health?.cases || []).length).length, fallen };
  }
  function travelStatus(snap, CD){
    const t = obj(snap["gravewounds-travel"]);
    if (!t?.mapId) return null;
    const forces = t.forces?.[t.mapId] || [], clock = t.clock?.[t.mapId] || null;
    const m = CD.maps?.[t.mapId] || {};
    const shown = f => (f.health?.cases || []).filter(c => c.inc === 0);
    const bySide = {}, sick = [];
    for (const f of forces){
      const b = (bySide[f.side] ||= { forces: 0, men: 0, sick: 0 });
      b.forces++; b.men += f.men || 0; b.sick += shown(f).length;
      const by = {};
      for (const c of shown(f)) if (c.d !== "wound") by[c.d] = (by[c.d] || 0) + 1;   // battle wounds are the fight's news, not sickness
      for (const [d, n] of Object.entries(by)) sick.push({ force: f.id, name: f.name || "?", d, n });
    }
    const short = forces.filter(f => f.sup && f.type !== "wagons").map(f => ({ force: f.id, name: f.name || "?",
      out: [f.supHungry && "rations", f.thirsty && "water", (f.sup.med ?? 1) <= 0 && "medical stores", (f.sup.ammo ?? 1) <= 0 && "ammunition"].filter(Boolean) }))
      .filter(x => x.out.length);
    const days = t.wx?.[t.mapId]?.days || {};
    return { mapId: t.mapId, mapName: m.name || t.mapId, start: m.start_date || null, day: clock ? clock.day : null,
      forces: forces.length, sides: [...new Set(forces.map(f => f.side))], fought: (t.fought || []).length,
      names: Object.fromEntries(forces.map(f => [f.id, f.name])), bySide, sick, short, wx: days };
  }
  function fightStatus(snap){
    const r = obj(snap["gravewounds-chars"]), rh = obj(snap["gravewounds-handoff"]), fh = obj(snap["gravewounds-field-handoff"]);
    const chars = r && Array.isArray(r.chars) ? r.chars : [];
    const roller = chars.length ? { fighters: chars.length, sides: [...new Set(chars.map(c => (c.side || "Side A").trim() || "Side A"))], round: r.round || 1,
      wonBy: r.wonBy || null, strikes: (r.events || []).filter(e => e.type === "strike").length } : null;
    // the roller's named men felled (down, or out of the fight), each by his wound's event
    const named = new Map(chars.filter(c => c.sheet || c.pid).map(c => [c.id, c]));
    const fell = (r?.events || []).filter(e => e.type === "wound" && (e.pub?.down || e.pub?.state === "out") && named.has(e.pub?.who?.id))
      .map(e => ({ id: e.pub.who.id, n: e.n, name: e.pub.who.name, side: e.pub.who.side, round: e.round, how: e.pub.down ? "is down" : "is out of the fight" }));
    // a side broken on the roller (its morale check failed): the outcome everyone sees
    const broke = (r?.events || []).filter(e => e.type === "morale" && e.pub?.broken).map(e => ({ n: e.n, side: e.pub.side, round: e.round }));
    // the field map's units broken or fled, in the battle under way (or just over)
    const fm = obj(snap["gravewounds-field"]);
    const battle = fm && fm.phase !== "setup" ? (fm.from?.battle || (fm.sides || []).join(" v ")) : null;
    const routed = battle ? (fm.units || []).filter(u => u.state === "broken" || u.state === "fled")
      .map(u => ({ battle, id: u.id, name: u.name || "?", side: u.banner || u.side, state: u.state, exchange: fm.exchange || 0 })) : [];
    const result = obj(snap["gravewounds-field-result"]);
    const waiting = [];                              // fights sent from the travel map and not yet set up: a skirmish for the roller, a battle for the field map
    if (rh) waiting.push({ page: "roller.html", key: "gravewounds-handoff", place: rh.place || "", force: rh.force?.name || "", foes: (rh.foes || []).map(f => f.name) });
    if (fh) waiting.push({ page: "field.html", key: "gravewounds-field-handoff", place: fh.place || "", battle: fh.battle || "", day: fh.day || "", forces: (fh.forces || []).map(f => f.name) });
    return {
      sent: waiting[0] || null, waiting, fell, routed, broke,
      roller,
      fieldResult: result ? { battle: result.battle || "", place: result.place || "", minutes: result.minutes || 0,
        lost: Object.values(result.forces || {}).reduce((a, x) => a + (x.lost || 0), 0) } : null,
    };
  }
  function seasonStatus(snap){                       // the team builder's last End of season: the stamp it gives each man's experience
    const stamps = Object.values(obj(snap["gravewounds-xp"]) || {}).map(x => x?.stamp).filter(Boolean);
    return stamps.length ? { stamp: Math.max(...stamps), men: stamps.filter(x => x === Math.max(...stamps)).length } : null;
  }
  function status(raw, CD = {}){
    const snap = parsed(raw);
    return { team: teamStatus(snap, CD), named: namedStatus(snap), travel: travelStatus(snap, CD), fight: fightStatus(snap), season: seasonStatus(snap) };
  }

  // The campaign has moved on when the pages show it: noticed once each (seen holds what was noticed).
  function sentFight(sent, mark){
    const place = sent.place || "?", against = sent.foes?.length ? " against " + sent.foes.join(", ") : "";
    const who = sent.page === "field.html" ? "a battle at " + place : "a fight at " + place + against;
    return { phase: "fight", page: sent.page, why: `The travel map sent ${who}.`, mark };
  }
  function suggest(phase, st, seen = {}){
    const f = st.fight;
    for (const w of f.waiting){                      // each fight sent, noticed once (a skirmish still waiting does not hide a battle sent after it)
      const mark = `sent:${w.key}:${w.battle || w.place}:${w.force || ""}`;
      if (!seen[mark]) return sentFight(w, mark);
    }
    if (f.fieldResult){
      const mark = `field:${f.fieldResult.battle}`;
      if (!seen[mark]) return { phase: "aftermath", page: "travel.html", why: `The battle at ${f.fieldResult.place || "?"} is over: ${f.fieldResult.lost} men lost in ${f.fieldResult.minutes} minutes. Its result waits for the travel map.`, mark };
    }
    if (f.roller?.wonBy && phase === "fight"){
      const mark = `won:${f.roller.wonBy}:${f.roller.strikes}`;
      if (!seen[mark]) return { phase: "aftermath", page: "roller.html", why: `${f.roller.wonBy} won the fight on the roller.`, mark };
    }
    return null;
  }

  // What happened that is worth the log by itself, once each (seen holds what was noticed): a named man's
  // death, a named man felled on the roller, a unit broken or fled on the field map, a man taken
  // prisoner, sickness breaking out in a force, a force out of supplies, a man's new
  // rank, the end of a day on the travel map, the end of a season.
  // -> {news: [{mark, value, why, phase?}], forget: [marks]}: forget, the outbreaks that are over (a new
  // one is news again).
  const thousands = n => Number(n).toLocaleString("en-US");   // 25,000
  function deathNews(st, seen, CD){
    return st.named.fallen.filter(x => !seen["dead:" + x.uid]).map(x => {
      const of = x.died ? " of " + (CD.diseases?.[x.died] || x.died).toLowerCase() : "";
      const how = x.why && !of ? " (" + x.why + ")" : "";
      const t = st.travel, force = t && x.map === t.mapId && t.names[x.force] ? ", with " + t.names[x.force] : "";
      return { mark: "dead:" + x.uid, value: true, why: `${x.name} has died${of}${how}${force}.` };
    });
  }
  function sickNews(st, seen, CD){
    const t = st.travel, active = new Set(), news = [];
    for (const x of t?.sick || []){
      const mark = `sick:${t.mapId}:${x.force}:${x.d}`;
      active.add(mark);
      if (!seen[mark]) news.push({ mark, value: true, why: `${CD.diseases?.[x.d] || x.d} has broken out in ${x.name}: ${x.n} sick.` });
    }
    return { news, forget: Object.keys(seen).filter(k => k.startsWith("sick:") && !active.has(k)) };
  }
  function dayNews(st, seen, CD, temp){
    const t = st.travel;
    if (!t?.day) return [];
    const mark = "day:" + t.mapId, last = seen[mark];
    if (typeof last !== "number" || t.day <= last) return typeof last === "number" ? [] : [{ mark, value: t.day, why: null }];
    const ended = t.day - 1 === last ? `Day ${last} has ended` : `Days ${last} to ${t.day - 1} have ended`;
    const w = t.wx[t.day - 1]?.w, wx = w ? `: ${(CD.weather?.[w.cond] || w.cond).toLowerCase()}, ${temp(w.low)} to ${temp(w.high)}` : "";
    const sides = Object.entries(t.bySide).map(([side, b]) => `${side} ${b.forces === 1 ? "1 force" : b.forces + " forces"}, ${thousands(b.men)} men${b.sick ? ", " + thousands(b.sick) + " sick" : ""}`);
    return [{ mark, value: t.day, why: `${ended} on the map of ${t.mapName}${wx}. ${sides.join("; ")}.` }];
  }
  function heldNews(st, seen){                       // a man of the team taken prisoner
    return st.team.held.filter(m => !seen["held:" + m.id]).map(m => ({ mark: "held:" + m.id, value: true, why: `${m.name} has been taken prisoner.` }));
  }
  function rankNews(st, seen, CD){                   // a man's rank changed: first seen, only marked
    const names = CD.ranks?.[st.team.era] || {};
    return st.team.ranks.filter(m => seen["rank:" + m.id] !== m.rank).map(m => ({ mark: "rank:" + m.id, value: m.rank,
      why: seen["rank:" + m.id] === undefined ? null : `${m.name} is now ${(names[m.rank] || m.rank).toLowerCase()}.` }));
  }
  function shortNews(st, seen){                      // a force out of rations, water, medical stores or ammunition; news again once refilled and out again
    const t = st.travel, active = new Set(), news = [];
    for (const x of t?.short || []) for (const what of x.out){
      const mark = `out:${t.mapId}:${x.force}:${what}`;
      active.add(mark);
      if (!seen[mark]) news.push({ mark, value: true, why: `${x.name} is out of ${what}.` });
    }
    return { news, forget: Object.keys(seen).filter(k => k.startsWith("out:") && !active.has(k)) };
  }
  const felledNews = x => ({ mark: `fell:${x.id}:${x.n}`, why: `${x.name} (${x.side}) ${x.how}${x.round ? ", round " + x.round : ""}.` });
  const brokeNews = b => ({ mark: `broke:${b.n}:${b.side}`,
    why: `${b.side} ${b.side.endsWith("s") ? "break" : "breaks"} on the roller${b.round ? ", round " + b.round : ""}: they run or surrender.` });
  const routedNews = u => ({ mark: `routed:${u.battle}:${u.id}`,
    why: `${u.name} (${u.side}) ${u.state === "fled" ? "have fled the field" : "have broken"}, exchange ${u.exchange}.` });
  function fightNews(st, seen){                     // a named man felled or a side broken on the roller; a unit broken or fled on the field map
    const f = st.fight;
    return [...f.fell.map(felledNews), ...f.broke.map(brokeNews), ...f.routed.map(routedNews)]
      .filter(n => !seen[n.mark]).map(n => ({ ...n, value: true }));
  }
  function seasonNews(st, seen){
    const s = st.season;
    if (!s || seen["season:" + s.stamp]) return [];
    return [{ mark: "season:" + s.stamp, value: true, phase: "downtime",
      why: `The season has ended in the team builder: experience, rank and age rolled for ${s.men === 1 ? "1 man" : s.men + " men"}.` }];
  }
  function notices(st, seen = {}, CD = {}, temp = c => c + " °C"){   // temp: a temperature in the reader's units
    const sick = sickNews(st, seen, CD), out = shortNews(st, seen);
    return { news: [...fightNews(st, seen), ...deathNews(st, seen, CD), ...heldNews(st, seen), ...sick.news, ...out.news, ...rankNews(st, seen, CD), ...dayNews(st, seen, CD, temp), ...seasonNews(st, seen)],
      forget: [...sick.forget, ...out.forget] };
  }

  function saveFile(raw, name = ""){
    const keys = Object.fromEntries(Object.entries(raw).filter(([k, v]) => k.startsWith(PREFIX) && !KEEP_OUT.has(k) && typeof v === "string"));
    return { format: FORMAT, version: 1, name, saved: new Date().toISOString(), keys };
  }
  function checkFile(o){                             // the keys to write back, or an error saying what is wrong
    if (o?.format !== FORMAT) throw new Error("That file is not a Grave Wounds save.");
    if (o.version !== 1) throw new Error(`That save is version ${o.version}; this page reads version 1.`);
    if (!o.keys || typeof o.keys !== "object") throw new Error("That save holds nothing.");
    const keys = {};
    for (const [k, v] of Object.entries(o.keys)){
      if (typeof v !== "string") throw new Error(`That save is damaged (${k}).`);
      if (k.startsWith(PREFIX) && !KEEP_OUT.has(k)) keys[k] = v;
    }
    return keys;
  }

  // Campaign slots (the console keeps them in the browser's IndexedDB): each a save file's keys, with its
  // snapshots, the newest first, at most `keep` of them.
  function addSnap(snaps, snap, keep = 8){
    return [snap, ...(snaps || [])].slice(0, keep);
  }
  function slotName(slots, wanted = ""){             // a name not already taken: "Campaign 1", "Campaign 2"; "Towton", "Towton (2)"
    const taken = new Set((slots || []).map(x => x.name));
    const base = wanted.trim() || "Campaign";
    if (wanted.trim() && !taken.has(base)) return base;
    for (let n = wanted.trim() ? 2 : 1; ; n++){ const name = wanted.trim() ? `${base} (${n})` : `${base} ${n}`; if (!taken.has(name)) return name }
  }

  return { read, status, suggest, notices, saveFile, checkFile, addSnap, slotName, PHASES, RECORD, PREFIX, KEEP_OUT };
})();

if (typeof module !== "undefined") module.exports = CAMPAIGN;   // Node (the tests); the page has no `module`
