/* The travel map's day, with no page: its state (the forces, their routes, camps, health and
   supplies, the weather rolled, the clock), the march, the night, and the one clock for every
   force on the map. Moved here from templates/travel.html unchanged, so the travel map and the
   campaign console run the same day.

   makeTravelDay(DATA, RULES, env) -> every function and value below by name, S (the state) among
   them. DATA is the travel page's data bundle; RULES is makeTravelRules(DATA, ...) (travelrules.js).
   env: {roll100} the game's d100 for weather, finding the way, blisters and the like (by default
   the browser's crypto). Some things are kept in the browser's storage as the other pages keep
   them, and read and written here as there: the travel state (save, restore), the named men,
   their purses and experience, dropped packs, the interpreter.

   It needs the shared rule files loaded first, as on the travel page: purse.js, xp.js, ranks.js
   (with TD set), events.js, measure.js, lethality.js and camp.js (with WK, CAMP_HEX_M, NEIGHBOURS,
   hexDistance, hkey and edgeKey). build.py puts this file into the travel page at its
   TRAVELDAY_JS marker; in Node it is a module (tools/travel/test.js). */
function hhmm(t){                              // hours as 24-hour clock time
  const h = Math.floor(t + 1e-9), mi = Math.round((t - h) * 60);
  return `${String(h + Math.floor(mi / 60)).padStart(2, "0")}:${String(mi % 60).padStart(2, "0")}`;
}
function makeTravelDay(DATA, RULES, env = {}){
  const { mapJdn, mapDate, marchWindow, rollWeather, WIND_NAMES, nextGround, nightRest, fatigueAfter, NEIGHBOURS, terrainAt, forceTypes, fordHere, passable, stepHours, plan, advance, hexDistance, campDone, before, laterOf, dzProfile, newHealth, dzStep, healthCounts, sickMarchPct, campHygiene, campCare, weekFactors, nursingOf, contagionOf, freshToday, fieldcraftNeeded, leechBonus, reopenOld, healthWeek, healthDay, neighbours } = RULES;
  const TER = DATA.terrain, TT = TER.terrain, FT = TER.forces;
  const WXD = DATA.weather, DZ = DATA.disease, WK = DATA.works;
  const roll100 = env.roll100 || (() => 1 + (crypto.getRandomValues(new Uint32Array(1))[0] % 100));   // a d100 for the weather
  const SIDE_NAMES = ["east", "north-east", "north-west", "west", "south-west", "south-east"];   // NEIGHBOURS' order, north up
  function sidesAround(m, h){                    // the terrain beyond each side of hex h, for the roller's battle map
    const cols = m.rows[0].length, rows = m.rows.length, around = {};
    NEIGHBOURS[h[1] & 1].forEach(([dc, dr], i) => {
      const n = [h[0] + dc, h[1] + dr];
      if (n[0] >= 0 && n[0] < cols && n[1] >= 0 && n[1] < rows) around[SIDE_NAMES[i]] = terrainAt(m, n).id;
    });
    const ford = [terrainAt(m, h).id, ...Object.values(around)].some(t => t === "ford" || t === "bridge");
    return { around, hex_m: m.hex_km * 1000, ford };
  }
  function sideToward(a, b){                      // which side of hex a faces hex b (north up), or null if the same hex
    const dx = (b[0] + 0.5 * (b[1] & 1)) - (a[0] + 0.5 * (a[1] & 1)), dy = (b[1] - a[1]) * Math.sqrt(3) / 2;
    if (!dx && !dy) return null;
    const turn = Math.round(Math.atan2(-dy, dx) / (Math.PI / 3));
    return SIDE_NAMES[((turn % 6) + 6) % 6];
  }
  function cameFrom(dfd, o){                     // which side of the defenders' hex the attackers come in from
    const side = sideToward(dfd.pos, o.pos);
    if (side) return side;
    return o.cameFrom ? sideToward(dfd.pos, o.cameFrom) : null;   // in the same hex: the way they marched in
  }
  function nearWoods(m, h){
    const cols = m.rows[0].length, rows = m.rows.length;
    return [h.slice(), ...neighbours(h, cols, rows)].some(x => terrainAt(m, x).id === "forest");
  }
  const campPerimeter = (men, ftype) => (12 * campRadius(men, ftype) + 6) * edgeMetres();
  function campHours(m, h, kind, men, ftype, tools, workers = null){   // sized for all the men; the fit `workers` dig
    const c = WK.camps[kind], t = terrainAt(m, h);
    if (c.terrain && !c.terrain.includes(t.id)) return { error: `needs a ${c.terrain.map(x => TT[x].name.toLowerCase()).join(" or ")}` };
    if (c.tools && !tools) return { error: "needs tools (spades and axes)" };
    const woods = nearWoods(m, h);
    let labour = 0;
    if (c.layout){                              // laid out as the battle map would, with a gate wherever a road leaves
      const n = campMapSize(kind, men, ftype), mid = [Math.floor(n / 2), Math.floor(n / 2)];
      const gate = campGates(t.id, { around: sidesAround(m, h).around }, n, n, mid, campRadius(men, ftype));
      labour = worksLabour(campWorks(kind, men, ftype, n, n, null, { gate }).works, !woods);
    }
    const hands = workers === null ? men : workers;
    if (labour && !hands) return { error: "has no fit men to dig" };
    return { hours: c.hours + (labour ? labour / (hands * WK.work_share) : 0), labour, perimeter: campPerimeter(men, ftype), woods };
  }

  const KEY = "gravewounds-travel";
  const S = { mapId: Object.keys(DATA.maps)[0], edits: {}, forces: {}, sel: {}, mode: "plan", paint: "forest", seq: 1, msg: "", wx: {}, plague: {}, fought: [], clock: {} };
  function save(){ try{ localStorage.setItem(KEY, JSON.stringify({ mapId: S.mapId, edits: S.edits, forces: S.forces, sel: S.sel, seq: S.seq, paint: S.paint, wx: S.wx, plague: S.plague, fought: S.fought, clock: S.clock })) }catch(e){} }
  function restore(){ try{ const j = JSON.parse(localStorage.getItem(KEY) || "null"); if (j?.mapId && DATA.maps[j.mapId]) Object.assign(S, j, { plague: j.plague || {}, fought: j.fought || [], clock: j.clock || {} }) }catch(e){ /* nothing saved, or unreadable: start fresh */ } }
  const baseMap = () => DATA.maps[S.mapId];
  function curMap(){                           // the map with any painting applied
    const b = baseMap();
    return { ...b, rows: S.edits[S.mapId] || b.rows };
  }
  const sameHex = (a, b) => !!(a && b) && a[0] === b[0] && a[1] === b[1];
  function forcesHere(){
    if (!S.forces[S.mapId]) S.forces[S.mapId] = (baseMap().forces || []).map(f => newForce(f.name, f.type, f.side, f.hex, f.men, f.tools, f.era));
    for (const f of S.forces[S.mapId]){
      if (!Number.isFinite(f.men) || f.men < 1) f.men = 10;
      if (typeof f.tools !== "boolean") f.tools = true;
      if (!("camp" in f)) f.camp = null;
      if (!Number.isFinite(f.fatigue) || f.fatigue < 0) f.fatigue = 0;
      if (!Number.isFinite(f.marched) || f.marched < 0) f.marched = 0;
    }
    return S.forces[S.mapId];
  }
  function newForce(name, type, side, hex, men = 10, tools = true, era = null){
    return { id: S.seq++, name, type, side: side || "Side A", men, tools, era: era || null, camp: null, pos: hex.slice(), waypoints: [], path: null, legs: [], index: 0, day: 1, used: 0, marched: 0, fatigue: 0, log: [] };
  }
  const selForce = () => { const fs = forcesHere(); return fs.find(f => f.id === S.sel[S.mapId]) || fs[0] || null };
  const sides = () => [...new Set(forcesHere().map(f => f.side))];
  // ----- the calendar and the weather on this map -----
  const MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
  const WEEKDAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];   // Julian Day 0 was a Monday
  const win = day => marchWindow(curMap(), day);
  const hpdOf = day => win(day).hours;
  const hpdList = (day, n = 60) => Array.from({ length: n }, (_, i) => hpdOf(day + i));
  const clock = (used, day) => hhmm(win(day).start + used);
  function dateText(day, short = false){
    const m = curMap(), [y, mo, d] = mapDate(m, day), wd = WEEKDAYS[((mapJdn(m, day) % 7) + 7) % 7];
    return short ? `${d} ${MONTHS[mo - 1].slice(0, 3)}` : `${wd} ${d} ${MONTHS[mo - 1]} ${y}`;
  }
  const wxState = () => S.wx[S.mapId] || (S.wx[S.mapId] = { days: {} });
  function dayWeather(day){                    // rolls, in order, any day not yet rolled
    const X = wxState(), m = curMap();
    for (let n = 1; n <= day; n++){
      if (X.days[n]) continue;
      const prev = X.days[n - 1];
      const w = rollWeather(m, n, prev ? prev.w : null, [roll100(), roll100(), roll100(), roll100(), roll100(), roll100(), roll100()]);
      X.days[n] = { w, ground: nextGround(prev ? prev.ground : null, w) };
    }
    return X.days[day];
  }
  function regroundFrom(day){                  // the ground follows from the weather, day by day
    const X = wxState();
    for (let n = day; X.days[n]; n++){ const prev = X.days[n - 1]; X.days[n].ground = nextGround(prev ? prev.ground : null, X.days[n].w) }
  }
  function rerollDay(day){
    const X = wxState(), prev = X.days[day - 1];
    dayWeather(day);
    X.days[day].w = rollWeather(curMap(), day, prev ? prev.w : null, [roll100(), roll100(), roll100(), roll100(), roll100(), roll100(), roll100()]);
    regroundFrom(day);
  }
  function setDay(day, patch){
    const X = wxState(); dayWeather(day);
    const w = { ...X.days[day].w, ...patch, gm: true };
    if ("high" in patch && w.low > w.high) w.low = w.high;      // keep low <= high
    if ("low" in patch && w.high < w.low) w.high = w.low;
    X.days[day].w = w;
    const mw = WXD.conditions[X.days[day].w.cond].min_wind, ids = WXD.winds.map(x => x.id);
    if (mw && ids.indexOf(X.days[day].w.wind) < ids.indexOf(mw)) X.days[day].w.wind = mw;
    regroundFrom(day);
  }
  const groundOf = day => dayWeather(day).ground;
  function knownGround(day){                    // the ground of `day` and of every later day already rolled
    const X = wxState(), out = [groundOf(day)];
    for (let n = day + 1; X.days[n]; n++) out.push(X.days[n].ground);
    return out;
  }
  const healthOf = f => f.health || (f.health = newHealth());
  const fitOf = f => healthCounts(healthOf(f), f.men);
  const horsesOf = f => (f.horses === null || f.horses === undefined ? f.men : f.horses);   // one a man until the GM or a loss sets it
  const horsePct = f => (DATA.events && EV_HORSE_TYPES.includes(f.type) ? evHorseMarchPct(DATA.events, f.type, f.men, horsesOf(f)) : 100);
  function speedOf(f){                           // % of road speed: fatigue, the sick it must carry, horses it has lost, its load
    const c = fitOf(f);
    return Math.min(WXD.fatigue.levels[f.fatigue || 0].march, sickMarchPct(c.fit, c.carried), horsePct(f), loadPct(f));
  }
  /* Loads (ranks.js; data DATA.loads): a force marches in its era's marching order unless the GM
     changes it. The roads' paces are already those of men in marching order, so a heavier order
     slows it and tires it more than that, and a lighter one does not speed it. Each named man's feet
     take the load's blister chance for the day's marching. */
  const loadEraOf = f => { const e = forceEra(f); return e && ((DATA.loads || {}).eras || {})[e] ? e : null };
  const loadOrder = f => f.loadOrder || "marching";
  function forceBands(f){                         // [band, the era's usual marching band] for its average man, or null
    const e = loadEraOf(f); if (!e) return null;
    const body = ldBody(e), b = o => ldBand(ldLoadKg(e, o, "light"), body, 50);
    return [b(loadOrder(f)), b("marching")];
  }
  function loadPct(f){
    const fb = forceBands(f); if (!fb) return 100;
    const B = DATA.loads.bands;
    return Math.min(100, Math.round(B[fb[0]].march / B[fb[1]].march * 100));
  }
  function loadOptions(f){                       // the force panel's orders; the chosen one with its band and pace
    const fb = forceBands(f), O = DATA.loads.orders, cur = loadOrder(f);
    const now = `(${DATA.loads.bands[fb[0]].name.toLowerCase()}, ${loadPct(f)}% pace)`;
    return Object.keys(O).map(o => o === cur ? `<option value="${o}" selected>${O[o]} ${now}</option>` : `<option value="${o}">${O[o]}</option>`).join("");
  }
  const marchedKm = f => (f.marched || 0) * FT[f.type].kmh;
  function loadTire(f){                           // fatigue steps the day's march adds for a load heavier than the usual
    const fb = forceBands(f); if (!fb) return 0;
    const km = marchedKm(f);
    return Math.max(0, ldFatigue(fb[0], km) - ldFatigue(fb[1], km));
  }
  function blisters(f){                           // each named man who marched: his load's chance of blistered or hurt feet
    const km = marchedKm(f), e = loadEraOf(f); if (!e || km <= 0) return [];
    const all = readNamed(), out = [];
    for (const [, n] of namedWith(all, f)){
      if (!ableNow(n)) continue;
      n.marchDays = (n.marchDays || 0) + 1;                // feet harden with days on the march
      if (((n.health || {}).cases || []).some(c => c.feet && c.step >= DZ.steps.indexOf("mending"))) continue;   // still sore
      const kg = ldCarried(e, loadOrder(f), n.kitLoad || "light", n.loadExtra || 0, n.carry || 0), band = ldBand(kg, ldBody(e, n.sex || "m"), n.str ?? 50);
      const shod = DATA.kit && n.pid ? ktBlister(xpKit(n.pid).boots) : 1;     // worn boots: more blisters
      if (roll100() > ldBlister(band, km, n.marchDays - 1) * shod) continue;
      const step = DZ.steps.indexOf("mending"), [lo, hi] = DZ.wounds.fever_after;
      n.health = n.health || newHealth();
      n.health.cases.push({ d: "wound", inc: 0, step, peak: 0, shown: 0, chronic: false, inf: "low", fever: lo + (roll100() - 1) % (hi - lo + 1), injury: true, feet: true });
      out.push(`${n.name}'s feet are blistered raw (${DATA.loads.bands[band].name.toLowerCase()} load)`);
    }
    writeNamed(all);
    return out;
  }
  function packsLost(f){                          // its men lost the packs they dropped before a fight: tonight without blankets or rations
    let all = []; try { all = JSON.parse(localStorage.getItem("gravewounds-packs-lost") || "[]") || [] } catch (e) { all = [] }
    const key = `${S.mapId}:${f.id}`; if (!all.includes(key)) return false;
    try { localStorage.setItem("gravewounds-packs-lost", JSON.stringify(all.filter(k => k !== key))) } catch (e) { /* storage off */ }
    return true;
  }
  function groundText(g){
    const bits = [];
    if (g.snow) bits.push(g.snow >= WXD.ground.deep ? "deep snow" : "snow lying");
    if (g.mud) bits.push(g.mud >= WXD.ground.deep ? "deep mud" : "muddy");
    if (g.flood) bits.push("fords flooded");
    return bits.join(", ") || "dry going";
  }
  const wxLine = d => { const w = d.w, c = WXD.conditions[w.cond], wn = WXD.winds.find(x => x.id === w.wind), from = w.dir && w.wind !== "calm" ? ` from the ${WIND_NAMES[w.dir]}` : ""; return `${c.name}, ${wn.name.toLowerCase()}${from}, ${tempOut(w.low)}\u2013${tempOut(w.high)} ${tempUnit()}` };
  // The night: rest by camp and weather, fatigue for the day, and the next morning.
  /* Languages (ranks.js: lgValue, lgTonguesAt; data DATA.languages.maps and the places' tongues):
     the people where a force stands speak a tongue, or several in mixed country (those the nearest
     place within place_km names, else the map's); foraging where no named man in the force
     gets by in any of them is Hard, and a man who spends `among_days` nights among them has their
     main tongue ticked. */
  const localTongues = f => lgTonguesAt(baseMap(), S.mapId, f.pos);
  const speaksLocal = (n, ts) => !!n.tongues && ts.some(t => lgValue(n.tongues, t) >= (DATA.languages.getting_by ?? 26));
  function tongueNames(ts){                      // "Turkish, Bulgarian or Albanian"
    const n = ts.map(t => DATA.languages.tongues[t].name);
    return n.length > 1 ? n.slice(0, -1).join(", ") + " or " + n.at(-1) : n.join("");
  }
  function interpHere(f){                        // the team's interpreter, if he speaks a local tongue and the team's named men are with this force
    const ts = localTongues(f); if (!ts.length) return null;
    let I = null;
    try { I = JSON.parse(localStorage.getItem("gravewounds-interpreter") || "null") } catch (e) { I = null /* unreadable: none */ }
    return ts.includes(I?.tongue) && namedWith(readNamed(), f).some(([, n]) => n.pid && ableNow(n)) ? I : null;
  }
  function forageTongue(f){                      // [modifier, note]: Hard where no one in the force gets by in a local tongue (or the team's interpreter speaks one)
    const ts = localTongues(f);
    if (!ts.length || interpHere(f) || namedWith(readNamed(), f).some(([, n]) => ableNow(n) && (speaksLocal(n, ts) || !n.tongues))) return [0, ""];
    return [DATA.languages.forage_without ?? -20, `, no one speaking ${tongueNames(ts)}`];
  }
  function foraged(f){                          // a named man's Fieldcraft roll finds fresh food on the day's march
    const [skill, who, pid] = bestSkill([f], "fieldcraft");
    if (!skill) return false;
    const [mod, why] = forageTongue(f), target = Math.max(0, skill + mod);
    const roll = roll100(), ok = roll <= target;
    if (ok) xpTick(pid, "fieldcraft", "foraging on the march");
    if (ok) f.log.unshift(`${dateText(f.day, true)}: ${who} foraged fresh food on the march (Fieldcraft ${target}${why}, rolled ${roll}).`);
    return ok;
  }
  /* Skills that do things (data DATA.uses): billets in a village or town, hunting for the pot, and
     finding the way off the road or in bad weather. The best named man in the force rolls; a skill
     used well is ticked. */
  const USES = () => DATA.uses || {};
  function bestTalk(f, skill){                   // [figure, name, pid]: the best named man at a talk skill, capped by the local tongue (or by the interpreter's figure, through him)
    const ts = localTongues(f), I = interpHere(f);
    let best = [0, null, null];
    for (const [, n] of namedWith(readNamed(), f)){
      if (!ableNow(n)) continue;
      const raw = (n.skills || {})[skill] || 0;
      let v = ts.length && n.tongues ? Math.max(...ts.map(t => lgTalk(raw, n.tongues, n.native, t))) : raw;
      if (I && n.pid) v = Math.max(v, Math.min(raw, I.figure));
      if (v > best[0]) best = [v, n.name, n.pid || null];
    }
    return best;
  }
  function billetCheck(f){                       // null if billeted; else why not (a force its army does not feed must find its own)
    const U = USES().billet;
    if (!U || fedByArmy(f) || !namedWith(readNamed(), f).length) return null;
    const [v, who, pid] = bestTalk(f, U.skill), k = skillCheck(v, U.difficulty, roll100());
    if (k.success){ xpTick(pid, U.skill, "finding billets"); f.log.unshift(`${dateText(f.day, true)}: ${who} finds them billets (Persuade ${k.target}, rolled ${k.roll}).`); return null }
    return `no one will take them in (${who || "no one"}'s Persuade ${k.target}, rolled ${k.roll})`;
  }
  const hostFeeds = (camp, era) => !!camp && camp.kind === "quartered" && (USES().billet?.feeds || []).includes(era);
  function huntNight(f){                         // Hunt for the pot: how many men the game feeds tonight
    const U = USES().hunt;
    if (!U || !f.hunt || !U.terrain.includes(terrainAt(curMap(), f.pos).id)) return 0;
    const [v, who, pid] = bestSkill([f], U.skill);
    if (!who) return 0;
    const k = skillCheck(v, U.difficulty, roll100());
    if (!k.success){ f.log.unshift(`${dateText(f.day, true)}: ${who} hunts and finds nothing (Fieldcraft ${k.target}, rolled ${k.roll}).`); return 0 }
    xpTick(pid, U.skill, "hunting for the pot");
    const buffalo = (U.buffalo_maps || []).includes(S.mapId), fed = (buffalo ? U.buffalo : U.deer) * (k.critical ? 2 : 1);
    f.log.unshift(`${dateText(f.day, true)}: ${who} brings in ${k.critical ? "two " : "a "}${buffalo ? "buffalo" : "deer"} (Fieldcraft ${k.target}, rolled ${k.roll}): meat for ${fed} men.`);
    return fed;
  }
  // ----- pack animals and carts (weights.yaml): wheels slow the force off the road and in mud; fodder where they cannot graze -----
  const animalRow = a => (TD.weights?.animals || []).find(x => x.id === a);
  function wheelsToday(f, m, g){                 // the day's pace for wheels in the force: 1, or slower off the road and in mud
    const W = TD.weights || {}, wheels = namedWith(readNamed(), f).some(([, n]) => (n.animals || []).some(a => animalRow(a)?.wheels));
    if (!wheels || !f.path || f.index + 1 >= f.path.length) return 1;
    const next = terrainAt(m, f.path[f.index + 1]).id, road = ["road", "bridge", "village", "town"].includes(next);
    return (road ? 1 : 1 / (W.off_road || 1)) * (g.mud ? 1 / (W.mud || 1) : 1);
  }
  function fodderNight(f, n, p){                 // a night's fodder for his animals where they cannot graze: Days from his purse
    const W = TD.weights || {}, grazes = (W.graze || []).includes(terrainAt(curMap(), f.pos).id);
    const due = (n.animals || []).map(animalRow).filter(a => a && !(grazes && !a.fuel)).reduce((t, a) => t + (a.forage || 0), 0);
    if (!due) return;
    if (purseLeft(p) + 1e-9 < due){ n.log = [`${dateText(f.day, true)}: no money for fodder or fuel; his animals and machines go short.`, ...(n.log || [])].slice(0, 20); return }
    p.ledger.push({ days: -due, what: `Fodder and fuel with ${f.name}` });
  }
  function wayToday(f, m){                       // the day's pace for finding the way: 1, or slower when the guide goes astray
    const U = USES().way;
    if (!U || !f.path || f.index + 1 >= f.path.length) return 1;
    if (f.wayDay === f.day) return f.waySlow || 1;
    f.wayDay = f.day; f.waySlow = 1;
    const cond = dayWeather(f.day).w.cond, next = terrainAt(m, f.path[f.index + 1]).id;
    if (!U.when.includes(cond) && ["road", "bridge", "village", "town"].includes(next)) return 1;   // a road through: no need of a guide
    const [v, who, pid] = bestSkill([f], U.skill);
    if (!who) return 1;
    const k = skillCheck(v, U.hard_in.includes(cond) ? "hard" : U.difficulty, roll100());
    if (k.success){ xpTick(pid, U.skill, "finding the way"); return 1 }
    f.waySlow = U.slow;
    let why = `${who} loses the way (Fieldcraft ${k.target}, rolled ${k.roll}): the day's march is slower`;
    if (k.fumble){ f.used = Math.min(hpdOf(f.day), (f.used || 0) + U.lost_hours); why += `, and an hour is lost going the wrong way` }
    f.log.unshift(`${dateText(f.day, true)}: ${why}.`);
    return U.slow;
  }
  function amongNight(f, n){                     // a night among the people where the force stands: a month of it ticks their main tongue
    const t = localTongues(f)[0];
    if (!t || !n.pid || !n.tongues || n.native === t) return;
    f.among ||= {};
    f.among[n.pid] = (f.among[n.pid] || 0) + 1;
    if (f.among[n.pid] < (DATA.languages.among_days ?? 30)) return;
    f.among[n.pid] = 0;
    xpTick(n.pid, "tongue:" + t, `a month among the ${DATA.languages.tongues[t].name} speakers`);
  }
  function endDay(f){
    const today = dayWeather(f.day), camp = campHere(f);
    const rest = nightRest(camp ? camp.kind : null, today.w);
    const before = f.fatigue || 0, after = fatigueAfter(before, f.marched || 0, today.w, today.ground, rest), L = WXD.fatigue.levels;
    const change = after === before ? "" : ` \u2014 ${L[before].name.toLowerCase()} \u2192 ${L[after].name.toLowerCase()}`;
    const where_ = camp ? WK.camps[camp.kind].name.toLowerCase() : "no camp";
    f.log.unshift(`Night of ${dateText(f.day, true)}: ${WXD.rest_levels[rest]} rest (${where_}; ${WXD.conditions[today.w.cond].name.toLowerCase()}, low ${fmtC(today.w.low)})${change}.`);
    const forage = terrainAt(curMap(), f.pos).forage, campedAll = !!camp && (f.marched || 0) <= 0;
    const found = !f.freshIssued && fieldcraftNeeded(forage, campedAll) && foraged(f);
    const fresh = freshToday(forage, campedAll, !!f.freshIssued, found);
    const before_ = f.noFresh || 0;
    f.noFresh = fresh ? 0 : before_ + 1;              // days without fresh food, for scurvy
    const fed = huntNight(f);
    f.huntFed = fed >= (f.men || 1);                   // the game feeds the whole force tonight
    if (f.huntFed && !fresh) f.noFresh = 0;
    keepNight(f, camp, before_, fed);
    const thirst = supplyNight(f, found, today);
    const lostPacks = packsLost(f);
    if (lostPacks){ f.log.unshift(`${dateText(f.day, true)}: the packs were lost with the field: no blankets or rations tonight.`); f.packsNight = true }
    const sore = blisters(f);
    if (sore.length) f.log.unshift(`${dateText(f.day, true)}: ${sore.join("; ")}.`);
    const nightTire = NIGHT() && (f.nightMarched || 0) >= NIGHT().min_hours ? NIGHT().fatigue : 0;   // a long night march
    if (nightTire) f.log.unshift(`${dateText(f.day, true)}: marched ${Math.round(f.nightMarched * 4) / 4} hours by night.`);
    const tire = eventsNight(f) + loadTire(f) + (lostPacks ? 1 : 0) + thirst + nightTire;
    healthNight(f, today, camp);
    f.fatigue = Math.min(L.length - 1, after + tire); f.day += 1; f.used = 0; f.marched = 0; f.packsNight = false; f.huntFed = false; f.thirsty = false; f.nightMarched = 0;
  }
  // ----- supplies between fights (ranks.js spDay, spRefill; data DATA.supplies) -----
  function supOf(f){                               // its supplies, full at first; a baggage train's stock too
    if (!DATA.supplies || !f) return null;
    f.sup ||= spStart(forceEra(f));
    if (f.type === "wagons") f.stock ||= spTrainStock();
    return f.sup;
  }
  function waterHere(f, w){                        // rain, or water at or beside its hex
    if (WXD.conditions[w.cond].precip !== "none") return true;
    const m = curMap(), src = DATA.supplies.water.sources;
    return [f.pos, ...neighbours(f.pos, m.rows[0].length, m.rows.length)].some(h => src.includes(terrainAt(m, h).id));
  }
  function supplyNight(f, foraged, today){          // the day's rations, water and medical stores: -> extra fatigue for thirst
    if (!supOf(f) || f.type === "wagons") return 0;
    const r = spDay(forceEra(f), f.sup, { fed: fedByArmy(f), foraged: !!foraged || !!f.huntFed, water: waterHere(f, today.w), high: today.w.high, men: f.men, wounded: f.newWounded || 0, sick: healthOf(f).cases.length });
    const was = !!f.supHungry;
    f.sup = r.sup; f.newWounded = 0; f.supHungry = r.hungry; f.thirsty = r.thirsty;
    if (r.hungry && !was) f.log.unshift(`${dateText(f.day, true)}: its rations are gone: the force goes hungry until it is fed or refilled.`);
    if (r.thirsty) f.log.unshift(`${dateText(f.day, true)}: no water to be had, and not enough carried: a thirsty night.`);
    if (r.short && !f.medShortSaid){ f.log.unshift(`${dateText(f.day, true)}: its medical stores are used up: its sick and wounded are cared for a step worse.`); f.medShortSaid = true }
    if (!r.short) f.medShortSaid = false;
    return r.thirsty ? DATA.supplies.water.thirst_fatigue : 0;
  }
  function depotHere(f){                           // its army's depot: where it started on the map, or a place marked a depot of its side
    const base = (baseMap().forces || []).find(b => b.name === f.name), at = h => h && h[0] === f.pos[0] && h[1] === f.pos[1];
    return at(base?.hex) || (baseMap().places || []).some(p => at(p.hex) && (p.depot || []).includes(f.side));
  }
  const trainHere = f => (S.forces[S.mapId] || []).find(o => o !== f && o.type === "wagons" && o.side === f.side && o.pos[0] === f.pos[0] && o.pos[1] === f.pos[1] && o.men > 0) || null;
  function refillForce(f, how){                    // at the depot, or from the train with it
    const eid = forceEra(f);
    if (how === "depot"){
      f.sup = spRefill(eid, supOf(f), f.men).sup; f.supHungry = false;
      const issued = DATA.kit && fedByArmy(f) ? namedWith(readNamed(), f).filter(([, n]) => n.pid) : [];   // its army issues new boots and clothing
      for (const [, n] of issued) xpKitSet(n.pid, { boots: 0, clothing: 0 });
      f.log.unshift(`${dateText(f.day, true)}: refilled at its depot${issued.length ? "; new boots and clothing issued to its named men" : ""}.`);
      return;
    }
    const t = trainHere(f); if (!t) return;
    supOf(t);
    const r = spRefill(eid, supOf(f), f.men, t.stock);
    f.sup = r.sup; t.stock = r.stock; if (f.sup.rations > 0) f.supHungry = false;
    f.log.unshift(`${dateText(f.day, true)}: drew supplies from ${t.name}.`);
  }
  function rationCost(f){                          // a day's rations for its men bought here, in Days, or null where none are to be had
    if (fedByArmy(f) || !BED_TERRAIN.includes(terrainAt(curMap(), f.pos).id)) return null;
    const k = (DATA.keep || {})[forceEra(f)] || {}, food = Object.values(k)[0]?.food;
    return food ? food * f.men : null;
  }
  function buyRations(f){                          // a day's rations for every man, paid by its named men from their purses
    const cost = rationCost(f); if (!cost) return;
    const purses = readPurses(), payers = namedWith(readNamed(), f).map(([, n]) => n.pid && purses[n.pid]).filter(Boolean);
    const have = payers.reduce((t, p) => t + Math.max(0, purseLeft(p)), 0);
    if (have + 1e-9 < cost){ S.msg = `${f.name} cannot buy a day's rations here: they cost ${cost.toFixed(1)} Days and its named men have ${have.toFixed(1)}.`; return }
    let left = cost;
    for (const p of payers){ const pay = Math.min(left, Math.max(0, purseLeft(p))); if (pay > 0){ p.ledger.push({ days: -pay, what: `Rations for ${f.name}` }); left -= pay } }
    writePurses(purses);
    f.sup.rations = spR(f.sup.rations + 1); f.supHungry = false;
    f.log.unshift(`${dateText(f.day, true)}: bought a day's rations for its ${f.men} men (${cost.toFixed(1)} Days from its named men's purses).`);
  }
  function supplyHtml(f){                          // the supplies line and its buttons
    const s = supOf(f); if (!s) return "";
    if (f.type === "wagons"){ const t = f.stock; return `Baggage train: ${+t.rations.toFixed(1)} days' rations, ${Math.round(t.ammo * 100)}% of a load of ammunition and ${Math.round(t.medical * 100)}% of a fill of medical stores, each for ${DATA.supplies.train.serves.toLocaleString("en-US")} men.` }
    const bits = [`ammunition ${Math.round(s.ammo * 100)}% of a load`, `rations ${+s.rations.toFixed(1)} day${s.rations === 1 ? "" : "s"}`, `water ${+s.water.toFixed(1)} L a man`, `medical stores ${Math.round(s.med * 100)}%`];
    const btn = (id, label, title) => `<button class="small" id="${id}" title="${esc(title)}">${label}</button>`;
    const acts = [depotHere(f) && btn("btn-sup-depot", "Refill at the depot", "Its army's depot: ammunition, rations and medical stores filled"),
      trainHere(f) && btn("btn-sup-train", "Draw from the train", "Its baggage train in this hex: as much as the train has for a force of its size"),
      rationCost(f) && btn("btn-sup-buy", "Buy a day's rations", `${rationCost(f).toFixed(1)} Days from its named men's purses`)].filter(Boolean).join(" ");
    return `Supplies: ${bits.join(", ")}${hungryNow(f) ? " (hungry)" : ""}. ${acts}`;
  }
  // ----- keep: a force its army does not feed; its named men pay from their purses (purse.js, money.py) -----
  const BED_TERRAIN = ["village", "town"];      // ground with a bed to be had for the night
  const fedByArmy = f => f.fed !== false;
  function keepLedger(p, f, paid){                  // a night's keep on his ledger: one line a stay with the force
    const last = p.ledger[p.ledger.length - 1], key = `${S.mapId}:${f.id}`;
    if (last?.keep && last.force === key){ last.days -= paid; last.keep += 1 }
    else p.ledger.push({ days: -paid, keep: 1, force: key });
    const e = p.ledger[p.ledger.length - 1];
    e.what = `Keep with ${f.name}, ${e.keep} day${e.keep === 1 ? "" : "s"}`;
  }
  function keepWants(f, n, pk, noFreshBefore){       // what he went without: hunger (no fresh food, and tired) and a bed
    const bits = [];
    if (pk.hungry){
      n.noFresh = (n.noFresh ?? noFreshBefore) + 1;  // he ate nothing: no fresh food for him either
      n.hungry = (n.hungry || 0) + 1;               // and it tires him: the roller adds a step for each day it has not seen
      bits.push("went hungry: no money for food");
    } else n.noFresh = f.noFresh;
    if (pk.rough) bits.push("slept rough: no money for a bed");
    if (!bits.length) return;
    const line = `${dateText(f.day, true)}: ${n.name} ${bits.join("; ")}.`;
    f.log.unshift(line);
    n.log = [line, ...(n.log || [])].slice(0, 20);
  }
  function keepMan(f, n, p, k, ctx){                 // one named man's night's keep: true if he paid anything
    const host = hostFeeds(ctx.camp, p.era), free = host || ctx.meat.left > 0;
    if (!host && ctx.meat.left > 0) ctx.meat.left -= 1;   // the hunt's meat, a man a share
    const pk = payKeep(purseLeft(p), 1, free ? 0 : k.food, ctx.bedHere ? k.bed : 0);
    if (pk.paid) keepLedger(p, f, pk.paid);
    keepWants(f, n, pk, ctx.noFreshBefore);
    const before = p.ledger.length;
    fodderNight(f, n, p);
    return !!pk.paid || p.ledger.length > before;
  }
  function keepNight(f, camp, noFreshBefore, hunted = 0){   // each named man's food (none if the host or the hunt feeds him), and a bed in a village or town unless camped
    const all = readNamed(), mine = namedWith(all, f);
    if (!mine.length) return;
    const purses = readPurses(), bedHere = !camp && BED_TERRAIN.includes(terrainAt(curMap(), f.pos).id);
    let spent = false;
    const meat = { left: hunted };
    for (const [, n] of mine){
      const p = n.pid ? purses[n.pid] : null, k = p ? ((DATA.keep || {})[p.era] || {})[p.region] : null;
      if (fedByArmy(f) || !k){ n.noFresh = f.noFresh; continue }   // fed with the force, or no money of his own to count
      spent = keepMan(f, n, p, k, { camp, bedHere, meat, noFreshBefore }) || spent;
    }
    writeNamed(all);
    if (spent) writePurses(purses);
  }
  function keepText(f){                          // the health panel's word on who feeds the force
    if (fedByArmy(f)) return "";
    const purses = readPurses(), mine = namedWith(readNamed(), f);
    const each = mine.map(([, n]) => { const p = n.pid ? purses[n.pid] : null; return p ? `${n.name} ${moneyQ(purseLeft(p), p.era, p.region)}` : null }).filter(Boolean);
    return `Not fed by its army: its named men pay a day's food from their purses, and a bed on nights in a village or town out of camp${each.length ? ` (left: ${each.join(", ")})` : ""}.`;
  }
  // ----- events on the march and in camp (events.js, gravewounds/events.py) -----
  function forceEra(f){                          // its own era (a map force may name one), or its map's period's
    const base = (baseMap().forces || []).find(b => b.name === f.name);
    return evEraOf(DATA.events || {}, curMap().period || baseMap().period, { era: f.era || base?.era || null });
  }
  const eventsOn = f => f.events !== false;
  const hungryNow = f => (f.shortFood || f.supHungry) && !f.huntFed;   // the GM's word, or its rations run out
  const conditionsOf = f => [(hungryNow(f) || f.packsNight) && "hungry", f.unpaid && "unpaid"].filter(Boolean);
  function eventsNight(f){                      // the night's desertion, straggling, injuries, horses and incident -> fatigue steps added
    const EV = DATA.events, era = EV && eventsOn(f) ? forceEra(f) : null;
    if (!era || !EV.eras[era]) return 0;
    const act = evActivity(f.marched || 0, !!f.withdrawing), fit = fitOf(f).fit;
    const horsed = EV_HORSE_TYPES.includes(f.type), before = horsed ? horsePct(f) : 100;
    const r = evDay(EV, DZ, era, f.type, fit, act, roll100, horsed ? horsesOf(f) : null, conditionsOf(f));
    const lost = r.desert + r.straggle + r.incident_lost;
    if (horsed){                                 // lost horses come off its count; a mounted deserter rides off on his
      const took = f.type === "mounted" ? r.desert : 0;
      if (r.horses || (took && f.horses !== null && f.horses !== undefined)) f.horses = Math.max(0, horsesOf(f) - r.horses - took);
    }
    if (lost) f.men = Math.max(0, f.men - lost);
    if (r.cases.length) healthOf(f).cases.push(...r.cases);
    const bits = evDayText(r);
    if (horsed && horsePct(f) < before){
      const band = (EV.horses_march[f.type] || []).filter(b => horsesOf(f) < b.below * f.men).sort((a, b) => a.pct - b.pct)[0];
      const why = band ? band.note.split(":")[0] : "";
      bits.push(f.type === "mounted" ? `too few horses: it now marches as foot (${horsePct(f)}% speed)` : `teams short: the wagons slow to ${horsePct(f)}% (${why})`);
    }
    if (f.namedAccidents) bits.push(...namedAccidents(f, era, act));
    if (bits.length) f.log.unshift(`${dateText(f.day, true)}: ${bits.join("; ")}.${r.incident && r.incident.hook ? " (" + r.incident.hook + ")" : ""}`);
    return r.fatigue || 0;
  }
  function namedAccidents(f, era, act){          // the GM's option: each named man with the force takes the injury chance too
    const all = readNamed(), t = evThreshold(evRate(DATA.events, era, "injury", act, conditionsOf(f))), out = [];
    if (!t) return out;
    for (const [, n] of namedWith(all, f)){
      if (evD1e6(roll100) > t) continue;
      const c = evInjuryCase(DATA.events, DZ, roll100);
      n.health = n.health || newHealth();
      n.health.cases.push(c);
      out.push(`${n.name} was injured (${DZ.steps[c.step]})`);
      n.log = [`${dateText(f.day, true)}: ${n.name} was injured on the march.`, ...(n.log || [])].slice(0, 20);
    }
    writeNamed(all);
    return out;
  }
  // ----- camp disease (rules in the shared block) -----
  const dzName = did => dzProfile(did).name.toLowerCase();
  const dzShort = did => dzName(did).split(" (")[0];    // "camp fever (typhus)" -> "camp fever"
  const tallyText = (o, verb) => Object.entries(o).map(([did, n]) => `${n} ${verb} (${dzShort(did)})`);
  function nightHardness(w){                    // the night's hardship: the weather and the cold
    const cold = Math.max(0, ...WXD.cold_hardship.filter(c => w.low <= c.low_at_or_below).map(c => c.add));
    return WXD.conditions[w.cond].hardship + cold;
  }
  const nightHard = (w, kind) => nightHardness(w) > WXD.shelter[kind || "none"];   // the night was harder than the shelter: cold and wet for recovery
  function healthNight(f, today, camp){         // the sick get better or worse; once a week, the outbreak roll
    const kind = camp ? camp.kind : null, hyg = campHygiene(f.hygiene || null, kind);
    const ctx = { care: campCare(kind, f), marched: (f.marched || 0) > 0, wet_cold: nightHard(today.w, kind), filth: hyg === "poor", fresh: (f.noFresh || 0) < DZ.week_days,
      leech: leechBonus(bestSkill([f], "leechcraft")[0]), low: today.w.low, shelter: WXD.shelter[kind || "none"], hardness: nightHardness(today.w) };
    namedNight(f, ctx, f.day % DZ.week_days === 0 ? weekFactorsFor(f, kind, hyg) : null);
    xpNight(f, ctx.wet_cold);
    const r = healthDay(healthOf(f), { ...ctx, men: f.men, unnursed: nursingOf(healthOf(f), f.men).unnursed }, roll100);
    f.health = r.health;
    const dead = Object.values(r.events.dead).reduce((t, n) => t + n, 0);
    if (dead) f.men = Math.max(0, f.men - dead);
    for (const k of Object.keys(f.health.immune)) f.health.immune[k] = Math.min(f.health.immune[k], f.men);
    const bits = [...tallyText(r.events.shown, "fell ill"), ...tallyText(r.events.dead, "died"), ...tallyText(r.events.healed, "recovered")];
    if (bits.length) f.log.unshift(`Night of ${dateText(f.day, true)}: ${bits.join("; ")}.`);
    if (f.day % DZ.week_days === 0) healthWeekFor(f, kind, hyg);
  }
  // ----- named characters with a force (the roller's fighters): their own course, own Endurance -----
  const NAMED_KEY = "gravewounds-named";        // {uid: {name, endurance, map, force, health, dead, log}}, shared with the roller
  function readNamed(){ try{ return JSON.parse(localStorage.getItem(NAMED_KEY) || "{}") || {} }catch(e){ return {} } }
  function writeNamed(all){ try{ localStorage.setItem(NAMED_KEY, JSON.stringify(all)) }catch(e){ /* storage off: they stay as they were */ } }
  const namedWith = (all, f) => Object.entries(all).filter(([, n]) => n.map === S.mapId && n.force === f.id && !n.dead);
  /* Fords (ranks.js: hzFordRisk, hzSwimTarget, hzSwimStep; data DATA.hazards.fords). A force may risk a
     flooded ford (not with wagons or guns). Crossing one, each named man heavy enough for the water
     (or anyone, in a flood) makes an Agility check (Ride for a horseman); swept off, he swims for the
     bank: near-drowned, or drowned. */
  const hasWagons = f => forceTypes(colType(f)).includes("wagons");
  const riskGround = (f, g) => (f.riskFord && !hasWagons(f) && g && (g.flood || 0) > 0 ? { ...g, flood: 0 } : g);
  function sweptOff(f, n, ford, band){             // he is in the water: minutes to the bank -> his fate
    const B = ford.water.band;
    let step = hzColdShock(n.nerve ?? 50, ford.cold, roll100()).success ? 0 : 1, worst = step;   // cold shock, the first minute
    for (let m = 0; m < B.rounds && step < 4; m++){
      const t = hzSwimTarget(n.end ?? 50, n.swim || "basic", band, n.kitLoad || "light", { current: B.id, minutes: m, cold: ford.cold });
      step = hzSwimStep(step, t, roll100()).step; worst = Math.max(worst, step);
    }
    if (step >= 4) return "drowned";
    return worst >= 3 ? "near-drowned" : "struggled out";
  }
  function fordMan(f, n, ford, e){                // one named man at the ford: a line if he is swept off
    const band = e ? ldBand(ldCarried(e, loadOrder(f), n.kitLoad || "light", n.loadExtra || 0, n.carry || 0), ldBody(e, n.sex || "m"), n.str ?? 50) : 0;
    const mounted = f.type === "mounted", W = ford.water, diff = hzFordRisk(W.depth, W.band.id, band, mounted);
    if (!diff) return null;
    const value = mounted ? (n.ride || n.agi || 50) : (n.agi ?? 50);
    if (skillCheck(value, diff, roll100()).success) return null;
    const fate = sweptOff(f, n, ford, band);
    if (fate === "drowned"){ n.dead = true; markLost(n.pid, "killed") }
    else if (fate === "near-drowned" && n.pid && DATA.stress) xpStress(n.pid, "near_miss", n.nerve ?? 50, "nearly drowned at a ford");
    const horse = mounted && hzHorseLost(W.band.id, roll100()) ? ", and his horse is drowned" : "";
    if (horse && (n.animals || []).includes("horse")){ n.animals.splice(n.animals.indexOf("horse"), 1); n.carry = Math.max(0, (n.carry || 0) - (animalRow("horse")?.load || 0)) }
    return `${n.name} is swept off his feet: ${fate}${horse}`;
  }
  function fordAt(h, g, w){                         // this ford's water today, and how cold it is
    const water = (g?.flood || 0) > 0 ? "flooded" : "normal";
    return { water: fordHere(curMap(), h, g), name: DATA.hazards.fords.water[water].name, cold: hzWaterCold(w.high, w.low, water === "flooded") };
  }
  function fordsCrossed(f, from, to, g){
    if (!DATA.hazards) return;
    const fords = f.path.slice(from + 1, to + 1).filter(h => terrainAt(curMap(), h).id === "ford");
    if (!fords.length) return;
    const e = loadEraOf(f), all = readNamed(), w = dayWeather(f.day).w;
    for (const h of fords){
      const ford = fordAt(h, g, w), W = ford.water, cn = DATA.hazards.cold[ford.cold].name, C = cn[0].toLowerCase() + cn.slice(1);
      const lines = namedWith(all, f).filter(([, n]) => ableNow(n) && !n.dead).map(([, n]) => fordMan(f, n, ford, e)).filter(Boolean);
      if (lines.length) f.log.unshift(`${dateText(f.day, true)}: ${ford.name}, ${W.depth} ft deep, the current ${W.current} m/s (${W.band.id}), the water ${C}: ${lines.join("; ")}.`);
    }
    writeNamed(all);
  }
  function strainNight(f, n){                    // combat stress: a day in the line adds Strain; a day out of it, camped, is rest
    if (!DATA.stress || !n.pid) return;
    if (f.inLine){
      const ev = xpStress(n.pid, "line_day", n.nerve ?? 50, undefined, (f.marched || 0) > 0 ? ["moving"] : []).filter(e => !e.held);   // on the move in the line: an advance or a withdrawal
      const era = forceEra(f);
      for (const e of ev) f.log.unshift(`${dateText(f.day, true)}: ${n.name}: ${stName(era, e.result)} (Nerve ${e.target}, rolled ${e.roll}).`);
    } else if ((f.marched || 0) <= 0) xpStressDo(n.pid, st => stRest(st, 1));
  }
  const hasCases = n => (n.health?.cases || []).length > 0;
  /* Boots and clothing (ranks.js kt*; data DATA.kit): a day's wear for each named man; on a day the
     force did not march, its best Craft mends the most worn piece among them (Mend kit). */
  function kitNight(f, mine, wetCold){
    const e = forceEra(f), g = groundOf(f.day), wet = (g?.mud || 0) > 0 || WXD.conditions[dayWeather(f.day).w.cond].precip !== "none";
    for (const [, n] of mine){
      if (!n.pid || !ableNow(n)) continue;
      const was = xpKit(n.pid), now = ktDay(e, was, f.marched || 0, wet, wetCold || ktShelterLoss(was.clothing) > 0);
      for (const k of ["boots", "clothing"]) if (ktState(now[k]) !== ktState(was[k]) && ktState(now[k]) !== "good")
        f.log.unshift(`${dateText(f.day, true)}: ${n.name}'s ${k} are ${ktState(now[k]) === "out" ? "worn out" : "wearing thin"}.`);
      xpKitSet(n.pid, now);
    }
    if ((f.marched || 0) <= 0) mendDay(f, mine);
  }
  function worstKit(mine){                        // the most worn boots or clothing among the named men: {n, part, w}, or null
    let worst = null;
    for (const [, n] of mine.filter(([, x]) => x.pid)){
      const k = xpKit(n.pid);
      for (const part of ["boots", "clothing"]) if (k[part] >= KTD().worn && (!worst || k[part] > worst.w)) worst = { n, part, w: k[part] };
    }
    return worst;
  }
  function MEND_WORD(r){                          // what a day's Mend kit came to
    if (r.fumble) return "ruins them";
    return r.success ? "mends them" : "cannot mend them yet";
  }
  function mendDay(f, mine){                      // a day out of the march: Mend kit on the most worn boots or clothing among the named men
    const worst = worstKit(mine);
    if (!worst) return;
    const [v, who, pid] = bestSkill([f], "craft");
    if (!who) return;
    const r = skillCheck(v, "ordinary", roll100()), kit = xpKit(worst.n.pid);
    kit[worst.part] = ktMend(kit[worst.part], r.success, r.fumble);
    xpKitSet(worst.n.pid, kit);
    if (r.success) xpTick(pid, "craft", "mending kit");
    const what = MEND_WORD(r);
    const whose = worst.n.name === who ? `his own ${worst.part}` : `${worst.n.name}'s ${worst.part}`;
    f.log.unshift(`${dateText(f.day, true)}: ${who} works on ${whose} (Craft ${r.target}, rolled ${r.roll}): ${what}.`);
  }
  function awayNight(f, n){                      // a night away for treatment counted off: true while he was away
    if (!n.pid || xpAwayDays(n.pid) <= 0) return false;
    if (xpAwayNight(n.pid)) f.log.unshift(`${dateText(f.day, true)}: ${n.name} is back from treatment.`);
    return true;
  }
  function xpNight(f, wetCold){                 // experience: a night served for each named man; a week nursing ticks the best Leechcraft; drill
    const all = readNamed(), mine = namedWith(all, f).filter(([, n]) => !n.dead);
    if (DATA.kit) kitNight(f, mine, wetCold);
    for (const [, n] of mine){
      if (awayNight(f, n)) continue;                        // away for treatment: no day served with the force
      xpServe(n.pid, 1);                                     // a day served
      if (fedByArmy(f)) xpArmy(n.pid, !!f.unpaid);           // and his army's pay, or arrears
      if (hungryNow(f) || f.packsNight || f.thirsty || wetCold || hasCases(n)) xpMark(n.pid, "hard", 1);   // a hard night: wear (ageing)
      strainNight(f, n);
      if (DATA.languages) amongNight(f, n);
    }
    if ((f.marched || 0) <= 0) f.campWeek = (f.campWeek || 0) + 1;     // drill: days of the week not marching
    if (f.day % DZ.week_days !== 0) return;
    const sick = healthOf(f).cases.length > 0 || mine.some(([, n]) => hasCases(n));
    if (sick){ const [lc, , pid] = bestSkill([f], "leechcraft", all); if (lc) xpTick(pid, "leechcraft", "nursing the sick") }
    drillWeek(f, all, mine);
    f.campWeek = 0;
  }
  function drillWeek(f, all, mine){             // the week's drill for a force its army feeds: the best Command (or its sergeants) rolls
    const able = mine.filter(([, n]) => n.drill && ableNow(n));
    if (!fedByArmy(f) || !able.length) return;
    const [cmd, who] = bestSkill([f], "command", all), r = trDrill(f.campWeek || 0, cmd, roll100());
    if (!r) return;
    if (r.success) for (const [, n] of able) xpTick(n.pid, n.drill, "drill in camp");
    const under = cmd > (DATA.training?.drill?.nco ?? 50) ? ` under ${who}` : "";
    const came = r.success ? "the named men's weapon skills are ticked" : "it came to little";
    f.log.unshift(`${dateText(f.day, true)}: a week's drill in camp${under} (${r.target}, rolled ${r.roll}): ${came}.`);
  }
  function clothedCtx(n, ctx){                    // his night with worn clothing: a step or two less shelter, so colder and wetter
    const loss = DATA.kit && n.pid ? ktShelterLoss(xpKit(n.pid).clothing) : 0;
    if (!loss) return ctx;
    const shelter = Math.max(0, ctx.shelter - loss);
    return { ...ctx, shelter, wet_cold: ctx.hardness > shelter };
  }
  function namedNight(f, ctx, factors){          // the day (and on the week's last day, the outbreak roll) for each named man with the force
    const all = readNamed(), mine = namedWith(all, f);
    if (!mine.length) return;
    const fh = healthOf(f), force = nursingOf(fh, f.men, !!f.cleanNurses);
    for (const [, n] of mine){
      const tended = force.nurses > 0 || mine.some(([, o]) => o !== n && nursesNow(o));   // nursed first, if anyone can
      const bits = namedDay(n, clothedCtx(n, ctx), tended ? 0 : 1);
      if (factors && !n.dead) bits.push(...namedWeek(n, factors, contagionOf(fh, f.men), nursesNow(n) ? { ...force, nurses: 1 } : null, n.noFresh ?? f.noFresh ?? 0));
      if (!bits.length) continue;
      const line = `${dateText(f.day, true)}: ${n.name} ${bits.join("; ")}.`;
      f.log.unshift(line);
      n.log = [line, ...(n.log || [])].slice(0, 20);
    }
    writeNamed(all);
  }
  const namedEnd = n => (Number.isFinite(n.endurance) ? n.endurance : DZ.endurance);
  function namedDay(n, ctx, unnursed){            // his night: his cases run their course -> what happened, in words
    const before = n.health || newHealth(), night = () => healthDay(before, { ...ctx, men: 1, unnursed }, roll100, namedEnd(n));
    let r = night(), spared = 0;
    while (r.health.dead && fateSpend(n.pid, `spared ${Object.keys(r.events.dead).map(dzShort).join(", ")} on the march`)){ r = night(); spared += 1 }   // a player character's fate: the night's checks rolled again, only to save his life (lethality.js)
    n.health = r.health;
    n.rest = (n.rest || 0) + 1;                   // a night with the force: the roller gives him back some blood
    const one = (o, verb) => Object.entries(o).map(([did, k]) => `${verb} (${k > 1 ? k + " " : ""}${dzShort(did)})`);   // a man, not a force
    const bits = [...one(r.events.shown, "fell ill"), ...one(r.events.healed, "recovered")];
    const howMany = spared > 1 ? ` (${spared})` : "";
    if (spared) bits.push(r.health.dead ? `spent his fate (${spared}) in vain` : `would have died, but fate spent${howMany}: he lives`);
    if (r.health.dead){
      n.dead = true;
      n.died = Object.keys(r.events.dead)[0];
      markLost(n.pid, ["wound", "fever"].includes(n.died) ? "died of wounds" : "died of disease");
      bits.push(`died (${Object.keys(r.events.dead).map(dzShort).join(", ")})`);
    }
    return bits;
  }
  // his outbreak roll: the camp's contagion, his patients' diseases if he nurses, and scurvy after noFresh days
  function namedWeek(n, factors, extra, nurse, noFresh = 0){
    const w = healthWeek(n.health || newHealth(), 1, factors, roll100, namedEnd(n), { extra, nurse, noFresh });
    n.health = w.health;
    const olds = n.old || [];
    if (w.events.some(x => x.kind === "scurvy")) n.health = reopenOld(n.health, olds);   // his old wounds reopen
    const plural = olds.length > 1 ? "s" : "", reopened = olds.length ? `: ${olds.length} old wound${plural} reopened` : "";
    const said = { caught: x => `caught ${dzShort(x.d)} (not showing yet)`, nursed: x => `caught ${dzShort(x.d)} nursing the sick (not showing yet)`,
      relapse: x => `fell ill with ${dzShort(x.d)} again`, scurvy: () => `fell ill with scurvy${reopened}` };
    return w.events.map(x => said[x.kind](x));
  }
  // A named man nurses the force's sick if the GM set him to and he is not too sick himself.
  const ableNow = n => !n.dead && !(n.pid && xpAwayDays(n.pid) > 0) && !((n.health || {}).cases || []).some(c => c.inc === 0 && c.step >= dzStep(DZ.unfit_from));   // not away for treatment of Strain
  const nursesNow = n => !!n.nurse && ableNow(n);
  // The best of a skill (from the roller's sheets) among the named men with these forces who are well enough: [value, name]
  function bestSkill(forces, skill, all = readNamed()){
    let best = [0, null, null];                  // [value, name, purse id (for experience)]
    for (const f of forces)
      for (const [, n] of namedWith(all, f)) if (ableNow(n) && ((n.skills || {})[skill] || 0) > best[0]) best = [n.skills[skill], n.name, n.pid || null];
    return best;
  }
  function namedLine(f){                        // the force's named men and how they are, for its panel
    const mine = Object.values(readNamed()).filter(n => n.map === S.mapId && n.force === f.id);
    if (!mine.length) return "";
    return mine.map(n => {
      if (n.dead) return `${n.name} (dead)`;
      const shown = (n.health ? n.health.cases : []).filter(c => c.inc === 0 && c.step > 0);
      if (!shown.length) return `${n.name} (well)`;
      const c = shown.reduce((a, b) => (b.step > a.step ? b : a));
      return `${n.name} (${dzShort(c.d)}, ${DZ.steps[c.step]})`;
    }).join("; ");
  }
  function weekFactorsFor(f, kind, hyg){        // this week's factors for the force where it is
    const days = Array.from({ length: DZ.week_days }, (_, i) => f.day - i).filter(dd => dd >= 1).map(dayWeather);
    const camp = campHere(f);
    return weekFactors({ hygiene: hyg, camped_days: camp && camp.from ? f.day - camp.from.day + 1 : 0, terrain: terrainAt(curMap(), f.pos).id,
      highs: days.map(x => x.w.high), wet: days.map(x => WXD.conditions[x.w.cond].precip !== "none"), plague: !!S.plague[S.mapId] });
  }
  function healthWeekFor(f, kind, hyg){
    const h = healthOf(f), r = healthWeek(h, f.men, weekFactorsFor(f, kind, hyg), roll100, DZ.endurance, { extra: contagionOf(h, f.men), nurse: nursingOf(h, f.men, !!f.cleanNurses), noFresh: f.noFresh || 0 });
    f.health = r.health;
    const later = " (not showing yet)";
    const said = { caught: e => `${e.n} caught ${dzName(e.d)}${later}`, nursed: e => `${e.n} nursing the sick caught ${dzName(e.d)}${later}`,
      relapse: e => `${e.n} fell ill with ${dzName(e.d)} again`, scurvy: e => `${e.n} fell ill with scurvy (${f.noFresh} days without fresh food)` };
    const bits = r.events.map(e => said[e.kind](e));
    f.log.unshift(`Week to ${dateText(f.day, true)}: ${bits.length ? bits.join("; ") : "no new cases"}.`);
  }
  const fmtH = h => { if (h < 1 / 120) return "no time"; let hh = Math.floor(h + 1e-9), mm = Math.round((h - hh) * 60); if (mm === 60){ hh++; mm = 0 } if (!hh) return `${mm} min`; return mm ? `${hh} h ${mm} min` : `${hh} h` };
  const placeAt = h => (baseMap().places || []).find(p => sameHex(p.hex, h));
  const where = h => { const p = placeAt(h); return p ? p.name : `${terrainAt(curMap(), h).name.toLowerCase()} at ${h[0] + 1},${h[1] + 1}` };

  // Why a force cannot go onto a hex, in words: "Baggage train (baggage wagons) cannot go into forest: ..."
  function refusal(name, type, h, verb){
    const t = terrainAt(curMap(), h), ft = FT[type], who = `${name} (${ft.name.toLowerCase()})`;
    if (t.cost !== null && t.cost !== undefined && !(ft.cannot_enter || []).includes(t.id)) return `${who} cannot ${verb} the ${t.name.toLowerCase()} today: it is flooded after heavy rain.`;
    if (t.cost === null || t.cost === undefined)
      return `${who} cannot ${verb} the ${t.name.toLowerCase()}${t.id === "river" ? ": cross only at a ford or a bridge" : ""}.`;
    const no = (ft.cannot_enter || []).map(x => TT[x].name.toLowerCase());
    return `${who} cannot ${verb} ${t.name.toLowerCase()}: ${ft.name.toLowerCase()} keep out of ${no.length > 1 ? no.slice(0, -1).join(", ") + " and " + no[no.length - 1] : no[0]}.`;
  }
  // Re-plan a force's route from where it stands now, through its remaining waypoints.
  // ----- columns: forces marching together behind a leader -----
  function leaderOf(f){ const L = f?.with ? forcesHere().find(o => o.id === f.with) : null; return L || f }
  function columnOf(f){ const L = leaderOf(f); return [L, ...forcesHere().filter(o => o !== L && o.with === L.id)] }
  const colType = L => { const c = columnOf(L); return c.length > 1 ? c.map(o => [o.type, o.men]) : L.type };
  const colSpeed = L => Math.min(...columnOf(L).map(o => speedOf(o)));
  const colMen = L => columnOf(L).reduce((t, o) => t + o.men, 0);
  const colTools = L => columnOf(L).some(o => o.tools);
  const colFit = L => columnOf(L).reduce((t, o) => t + fitOf(o).fit, 0);
  const colDiggers = L => columnOf(L).reduce((t, o) => { const c = fitOf(o); return t + c.fit - c.nurses }, 0);   // fit men not nursing
  const colName = L => (columnOf(L).length > 1 ? `${L.name}'s column` : L.name);
  function colRefusal(L, h, verb){                // which force in the column cannot go there, and why
    const g = groundOf(L.day), bad = columnOf(L).find(o => !passable(curMap(), h, o.type, g)) || L;
    const msg = refusal(bad.name, bad.type, h, verb);
    return columnOf(L).length > 1 ? `${msg} ${L.name}'s column keeps together.` : msg;
  }
  function joinOptions(f){                       // leaders of other columns on its side within reach
    const mine = columnOf(f);
    return forcesHere().filter(o => !o.with && !mine.includes(o) && o.side === f.side && hexDistance(o.pos, f.pos) <= TER.fight_within);
  }
  function joinColumn(f, target){                // f and any force marching with it close up on target's column
    const L = leaderOf(target), joiners = columnOf(f);
    let at = { day: L.day, used: L.used };
    for (const o of joiners) at = laterOf({ day: o.day, used: o.used }, at);
    const camp = campHere(L);
    for (const o of joiners){
      Object.assign(o, { with: L.id, pos: L.pos.slice(), waypoints: [], path: null, legs: [], index: 0, camp: camp ? { ...camp } : null });
      o.log.unshift(`${dateText(at.day, true)}, ${clock(at.used, at.day)}: closes up and marches with ${L.name}.`);
    }
    for (const o of columnOf(L)) Object.assign(o, { day: at.day, used: at.used });
    L.log.unshift(`${dateText(at.day, true)}, ${clock(at.used, at.day)}: ${namesList(joiners.map(o => o.name))} ${joiners.length > 1 ? "join" : "joins"} the column.`);
    if (!replan(L)){ L.waypoints = []; replan(L); S.msg = `${L.name}'s route was cleared: the column cannot follow it.` }
  }
  function leaveColumn(f){                       // f marches on its own; if it led, the next force leads the rest
    const rest = columnOf(f).filter(o => o !== f);
    if (f.with){ f.with = null; f.log.unshift(`${dateText(f.day, true)}, ${clock(f.used, f.day)}: leaves the column.`); return }
    if (!rest.length) return;
    const next = rest[0];
    next.with = null;
    for (const o of rest.slice(1)) o.with = next.id;
    f.log.unshift(`${dateText(f.day, true)}, ${clock(f.used, f.day)}: leaves the column; ${next.name} leads the rest.`);
  }
  function replan(f){
    const m = curMap();
    if (!f.waypoints.length){ f.path = null; f.legs = []; f.index = 0; f.carried = 0; return true }
    const path = plan(m, f.pos, f.waypoints, colType(f), groundOf(f.day));
    if (!path) return false;
    if (!f.path || !sameHex(f.path[f.index + 1], path[1])) f.carried = 0;   // a new way out: the part-marched hex is lost
    f.path = path; f.index = 0;
    f.legs = []; let at = 0;                   // where each waypoint falls on the path
    for (const w of f.waypoints){
      while (!sameHex(path[at], w)) at++;
      f.legs.push(at);
    }
    return true;
  }
  function addWaypoint(sel, h){                  // a column's route is its leader's
    const m = curMap(), f = leaderOf(sel);
    if (!passable(m, h, colType(f), groundOf(f.day))){ S.msg = colRefusal(f, h, "go into"); return }
    f.waypoints.push(h);
    if (!replan(f)){ f.waypoints.pop(); replan(f); S.msg = `${f.name} cannot reach ${where(h)} from here.`; return }
    f.order = "march";
    S.msg = "";
  }
  function noMarchText(f, col){                 // why a column cannot march at all
    const carry = col.some(o => sickMarchPct(fitOf(o).fit, fitOf(o).carried) === 0);
    return carry ? `${colName(f)} has no fit men to carry its sick. Rest until some recover.` : `${colName(f)} is too spent to march. Rest until next morning.`;
  }
  /* Marching by night (data DATA.uses.night): a force may march on after the day's marching hours,
     slower, with the guide's Fieldcraft once a night to keep the way. */
  const NIGHT = () => USES().night;
  const nightHoursOf = f => (leaderOf(f).nightMarch && NIGHT() ? NIGHT().hours : 0);
  function dayEnd(day){                           // the clock's end of the day: the marching hours, and longer while any column marches on by night
    const extra = forcesHere().filter(f => f.day === day && marching(f)).map(nightHoursOf);
    return hpdOf(day) + Math.max(0, ...extra);
  }
  const isNight = f => f.used >= hpdOf(f.day) - 1e-9;
  function nightWay(f, m){                        // the night's pace for finding the way: 1, or slower when the guide goes astray
    const U = NIGHT();
    if (f.nightWayDay === f.day) return f.nightSlow || 1;
    f.nightWayDay = f.day; f.nightSlow = 1;
    if (!f.path || f.index + 1 >= f.path.length) return 1;
    const next = terrainAt(m, f.path[f.index + 1]).id, road = ["road", "bridge", "village", "town"].includes(next);
    const [v, who, pid] = bestSkill([f], (USES().way || {}).skill || "fieldcraft");
    if (!who){ f.nightSlow = USES().way?.slow || 1.4; return f.nightSlow }
    const k = skillCheck(v, road ? U.road : U.difficulty, roll100());
    if (k.success){ xpTick(pid, "fieldcraft", "finding the way by night"); return 1 }
    f.nightSlow = USES().way?.slow || 1.4;
    let why = `${who} loses the way in the dark (Fieldcraft ${k.target}, rolled ${k.roll}): the night's march is slower`;
    if (k.fumble){ f.used = Math.min(hpdOf(f.day) + nightHoursOf(f), f.used + U.lost_hours); why += `, and ${U.lost_hours} hours go on the wrong road` }
    f.log.unshift(`${dateText(f.day, true)}: ${why}.`);
    return f.nightSlow;
  }
  function march(sel, hours){                    // the whole column marches together, at its slowest, within today's marching hours -> {steps, arrived} or {why}
    const f = leaderOf(sel), col = columnOf(f);
    if (!f.path || f.index >= f.path.length - 1) return { why: `${colName(f)} has no route to march.` };
    const m = curMap(), base = colSpeed(f);
    if (!base) return { why: noMarchText(f, col) };
    const g = riskGround(f, groundOf(f.day)), night = isNight(f);
    const speed = base / (night ? NIGHT().slow * nightWay(f, m) : wayToday(f, m)) / wheelsToday(f, m, g);
    if (f.path.slice(f.index + 1).some(h => !passable(m, h, colType(f), g)) && !replan(f))
      return { why: `${f.name} cannot get through today (${groundText(g)}). Wait, or add a waypoint to go round.` };
    const from = f.index, u0 = f.used;
    const r = advance(m, f.path, f.index, f.used, hours, { hpd: night ? hpdOf(f.day) + nightHoursOf(f) : hpdOf(f.day), ftype: colType(f), ground: g, speed, carried: f.carried || 0 });
    const steps = r.index - from;
    if (steps && f.camp){ f.log.unshift(`${dateText(f.day, true)}: breaks camp (${WK.camps[f.camp.kind].name.toLowerCase()}).`); f.camp = null }
    f.marched = (f.marched || 0) + (r.used - u0);
    if (night) f.nightMarched = (f.nightMarched || 0) + (r.used - u0);
    if (steps) fordsCrossed(f, from, r.index, groundOf(f.day));
    if (steps) f.cameFrom = f.path[r.index - 1].slice();     // the hex it last left: the way it came in
    f.index = r.index; f.used = r.used; f.carried = r.carried; f.pos = f.path[f.index].slice();
    const arrived = f.index >= f.path.length - 1;
    const passed = f.legs.filter(i => i > from && i <= f.index).length;
    if (passed){ f.waypoints = f.waypoints.slice(passed); f.legs = f.legs.slice(passed).map(i => i - f.index); f.path = f.path.slice(f.index); f.index = 0 }
    if (arrived){ f.path = null; f.legs = []; f.waypoints = []; f.index = 0; f.carried = 0; f.order = "halt" }
    for (const o of col.slice(1)) followLeader(o, f, steps);
    return { steps, arrived };
  }
  function followLeader(o, f, steps){            // a force in the column goes where its leader went
    if (steps && o.camp){ o.log.unshift(`${dateText(f.day, true)}: breaks camp (${WK.camps[o.camp.kind].name.toLowerCase()}).`); o.camp = null }
    Object.assign(o, { pos: f.pos.slice(), day: f.day, used: f.used, marched: f.marched });
    if (steps && f.cameFrom) o.cameFrom = f.cameFrom.slice();
  }
  // ----- one clock for every force on the map: orders, then the GM moves the clock on -----
  const CLOCK_STEP = 0.25;                       // hours: how finely the clock watches for forces meeting, at most
  const CLOCK_LEAST = 1 / 60;                     // hours: the finest step it takes
  function nextTick(c){                           // the clock's next step: a quarter hour, or less, to the moment the first marching column enters its next hex
    let dt = CLOCK_STEP;                          // (so a fast column cannot pass through an enemy's reach between two looks)
    const m = curMap();
    for (const f of forcesHere()){
      if (!marching(f) || busy(f, c)) continue;
      const speed = colSpeed(f);
      if (!speed) continue;
      const st = stepHours(m, f.path[f.index], f.path[f.index + 1], colType(f), groundOf(f.day), speed) - (f.carried || 0);
      if (st > 0) dt = Math.min(dt, st);
    }
    return Math.max(CLOCK_LEAST, dt);
  }
  const atOrAfter = (a, b) => !before(a, b);
  const busy = (f, c) => before(c, { day: f.day, used: f.used });   // still making camp or fighting
  function waitUntil(f, t){                      // a force waits where it is until t: its nights pass as nights in place
    while (f.day < t.day) endDay(f);
    if (f.day === t.day && f.used < t.used) f.used = t.used;
  }
  function clockNow(){                           // the map's clock; a saved campaign starts it at its latest force, the rest waiting for it
    if (S.clock[S.mapId]) return S.clock[S.mapId];
    let c = { day: 1, used: 0 };
    for (const f of forcesHere()) c = laterOf({ day: f.day, used: f.used }, c);
    for (const f of forcesHere()) waitUntil(f, c);
    S.clock[S.mapId] = c;
    return c;
  }
  const marching = f => !f.with && f.order === "march" && !!f.path && f.index < f.path.length - 1;
  const pairKey = (a, b) => (a.id < b.id ? a.id + "-" + b.id : b.id + "-" + a.id);
  function meetings(){                           // pairs of forces of different sides within fighting reach: {key: [a, b]}
    const fs = forcesHere(), out = {};
    for (const a of fs) for (const b of fs) if (a.id < b.id && a.side !== b.side && hexDistance(a.pos, b.pos) <= TER.fight_within) out[pairKey(a, b)] = [a, b];
    return out;
  }
  function nightFalls(c){                        // the night for every force on today's clock; the clock moves to the next morning -> camps finished in the evening [text]
    const done = forcesHere().filter(f => f.day === c.day && busy(f, c) && f.camp)
      .map(f => `${f.name} finished its ${WK.camps[f.camp.kind].name.toLowerCase()} at ${clock(f.used, f.day)} the evening before.`);
    for (const f of forcesHere()) if (f.day === c.day) endDay(f);
    c.day += 1; c.used = 0;
    return done;
  }
  function tickClock(c, dt, seen, moved){        // every force for dt hours: marching orders march, the rest wait -> events [text]
    const t = { day: c.day, used: c.used + dt }, wasBusy = forcesHere().filter(f => busy(f, c));
    const events = marchAll(c, dt, moved);
    for (const f of forcesHere()) if (!busy(f, t)) waitUntil(f, t);
    c.used = t.used;
    for (const f of wasBusy) if (!busy(f, c) && f.camp) events.push(`${f.name} has finished its ${WK.camps[f.camp.kind].name.toLowerCase()}.`);
    return events.concat(newMeetings(c, seen));
  }
  function marchAll(c, dt, moved){               // the columns with march orders march dt hours -> events [text]
    const events = [];
    for (const f of forcesHere()){
      if (!marching(f) || busy(f, c)) continue;
      const r = march(f, dt), m = moved[f.id] || (moved[f.id] = { from: { day: c.day, used: c.used }, steps: 0, arrived: false });
      if (r.why){ f.order = "halt"; events.push(r.why); continue }
      m.steps += r.steps; m.arrived = m.arrived || r.arrived;
      if (r.arrived) events.push(`${colName(f)} arrives at ${where(f.pos)}.`);
    }
    return events;
  }
  function newMeetings(c, seen){                 // forces of different sides newly within reach: they halt -> events [text]
    const met = new Map(), events = [];            // force -> the enemies it has just met
    for (const [k, [a, b]] of Object.entries(meetings())){
      if (seen.has(k)) continue;
      seen.add(k);
      for (const [x, y] of [[a, b], [b, a]]){
        if (!met.has(x)) met.set(x, []);
        met.get(x).push(y.name);
      }
    }
    if (!met.size) return events;
    for (const [o, foes] of met){
      leaderOf(o).order = "halt";
      o.log.unshift(`${dateText(c.day, true)}, ${clock(c.used, c.day)}: meets ${namesList(foes)}; halts.`);
    }
    const who = [...met.keys()];
    events.push(`${namesList(who.map(o => o.name))} meet near ${where(who[0].pos)}: they halt.`);
    S.sel[S.mapId] = who[0].id;
    return events;
  }
  function marchLogs(c, moved){                  // one log line a column for the clock's move, not one a step
    for (const [id, mv] of Object.entries(moved)){
      const f = byId(+id); if (!f) continue;
      const span = mv.from.day === c.day ? `${dateText(c.day, true)}, ${clock(mv.from.used, c.day)}\u2013${clock(f.used, f.day)}` : `${dateText(mv.from.day, true)}, ${clock(mv.from.used, mv.from.day)} to ${dateText(f.day, true)}, ${clock(f.used, f.day)}`;
      const what = mv.steps ? `marched ${fmtKm(mv.steps * curMap().hex_km)} to ${where(f.pos)}` : `pressed on towards ${where((f.path || [f.pos])[Math.min((f.path || [f.pos]).length - 1, (f.index || 0) + 1)])}`;
      const line = `${span}: ${what}${mv.arrived ? " \u2014 arrived" : ""}.`;
      f.log.unshift(line);
      for (const o of columnOf(f).slice(1)) o.log.unshift(`With ${f.name}: ${line.replace(/^[^:]*: /, "")}`);
      for (const o of columnOf(f)) o.log = o.log.slice(0, 40);
    }
  }
  const anyAtWork = c => forcesHere().some(f => marching(f) || busy(f, c));
  function passNight(c){                         // at nightfall, any move of the clock is the night
    for (const f of forcesHere()) if (marching(f) && !busy(f, c)) f.log.unshift(`${dateText(c.day, true)}: halts for the night.`);
    const done = nightFalls(c), extra = done.length ? " " + done.join(" ") : "";
    S.msg = `Night passes. ${dateText(c.day)}, ${clock(0, c.day)}: marching from now until ${clock(hpdOf(c.day), c.day)}.${extra}`;
  }
  function clockStep(c, kind, stop, dusk, seen, moved){   // one tick of the clock, never across the end of the day's marching hours -> events
    const toDusk = c.used < dusk - 1e-9 ? dusk - c.used : Infinity;
    const events = tickClock(c, Math.min(nextTick(c), stop - c.used, toDusk), seen, moved);
    return kind === "event" && !events.length && !anyAtWork(c) ? ["Every force has halted."] : events;
  }
  function runClock(c, kind){                    // quarter hour by quarter hour to the stop, or the first event -> events [text]
    const seen = new Set(Object.keys(meetings())), moved = {}, days0 = c.day;
    const end = kind === "hour" ? Math.min(c.used + 1, dayEnd(c.day)) : dayEnd(c.day);
    let events = [];
    while (!events.length){
      const stop = kind === "event" ? dayEnd(c.day) : end, dusk = hpdOf(c.day);
      if (c.used < stop - 1e-9){
        events = clockStep(c, kind, stop, dusk, seen, moved);
        continue;
      }
      if (kind !== "event" || c.day - days0 >= 14) break;
      marchLogs(c, moved);
      for (const k of Object.keys(moved)) delete moved[k];
      events = nightFalls(c);
    }
    marchLogs(c, moved);
    return events;
  }
  function moveClock(kind){                      // kind: "hour", "nightfall" or "event"; at nightfall any of them passes the night
    const c = clockNow();
    if (c.used >= dayEnd(c.day) - 1e-9) return passNight(c);
    if (kind === "event" && !anyAtWork(c)){ S.msg = "Nothing will happen: no force is marching or making camp. Give a force a route first."; return }
    const events = runClock(c, kind), now = `${dateText(c.day, true)}, ${clock(c.used, c.day)}`;
    if (events.length){ S.msg = `${now}: ${events.join(" ")}`; return }
    S.msg = c.used >= dayEnd(c.day) - 1e-9 ? `${now}: the day's marching is done; the next move passes the night.` : `${now}.`;
  }
  function restColumn(sel){                     // the whole column stops for the day: its night's rest now, and it waits for the clock to reach the next morning
    const f = leaderOf(sel);
    if (f.day > clockNow().day){ S.msg = `${colName(f)} is already resting until ${dateText(f.day, true)}.`; return }
    columnOf(f).forEach(endDay);
    if (f.waypoints.length) replan(f);
    f.order = "halt";
    S.msg = `${colName(f)} stops for the day and rests; it is ready again ${dateText(f.day, true)}, ${clock(0, f.day)}.`;
  }
  function setOrder(f, order){                   // a column's orders are its leader's
    const L = leaderOf(f);
    if (order === "march" && !(L.path && L.index < L.path.length - 1)){ L.order = "halt"; S.msg = `${colName(L)} has no route: click the map to give it one.`; return }
    L.order = order;
    S.msg = order === "march" ? `${colName(L)} will march on its route as the clock moves on.` : `${colName(L)} halts where it is.`;
  }

  const hexDist = hexDistance;
  const campHere = f => (f.camp && sameHex(f.camp.hex, f.pos) ? f.camp : null);
  // Time to make this camp now. A force already camped here does not pay the set-up hours
  // again when it changes to another kind (the site, fires and watch are done), and cannot
  // make the same kind twice.
  function campCost(sel, kind){                 // a column makes one camp: all its men dig, any tools serve
    const f = leaderOf(sel), r = campHours(curMap(), f.pos, kind, colMen(f), colType(f), colTools(f), colDiggers(f)), old = campHere(f);
    if (r.error) return r;
    if (old && old.kind === kind) return { error: "already has one here", same: true };
    let hours = r.hours;
    if (old && old.kind !== "bivouac") hours = Math.max(0, hours - WK.camps[kind].hours);
    return { ...r, hours, change: !!old };
  }
  function makeCamp(sel, kind){
    const f = leaderOf(sel), col = columnOf(f), r = campCost(f, kind);
    if (r.error){ S.msg = `${colName(f)} cannot make a ${WK.camps[kind].name.toLowerCase()} here: it ${r.error}.`; return }
    const refused = kind === "quartered" && !r.same ? billetCheck(f) : null;
    if (refused){ S.msg = `${colName(f)} cannot take quarters: ${refused}.`; f.log.unshift(`${dateText(f.day, true)}: ${refused}.`); return }
    const ev = WK.evening_hours, came = { day: f.day, used: f.used };
    if (f.used >= hpdOf(f.day) + ev - 1e-9) col.forEach(endDay);
    const d0 = f.day, u0 = f.used;
    let left = r.hours;
    while (f.used + left > hpdOf(f.day) + ev + 1e-9){ left -= hpdOf(f.day) + ev - f.used; col.forEach(endDay) }
    const from = r.change && campHere(f).from ? campHere(f).from : came;   // when it got here and began camping
    const rate = Math.max(1, colDiggers(f)) * WK.work_share;   // the fit men dig: for how far along the works are at any time
    f.used += left; f.camp = { kind, hex: f.pos.slice(), from, start: { day: d0, used: u0 }, labour: r.labour, rate, setup: Math.max(0, r.hours - r.labour / rate) };
    let what = "made a " + WK.camps[kind].name.toLowerCase();
    if (kind === "quartered") what = "took quarters";
    else if (r.change) what = "changed its camp to a " + WK.camps[kind].name.toLowerCase();
    const lab = r.labour ? ", " + Math.round(r.labour) + " man-hours" : "";
    const until = f.day === d0 ? clock(f.used, f.day) : `${dateText(f.day, true)}, ${clock(f.used, f.day)}`;
    f.log.unshift(`${dateText(d0, true)}, ${clock(u0, d0)} to ${until}: ${what} at ${where(f.pos)} (${fmtH(r.hours)}${lab}).`);
    for (const o of col.slice(1)){              // one camp for the column
      Object.assign(o, { camp: { ...f.camp }, day: f.day, used: f.used });
      o.log.unshift(`${dateText(d0, true)}, ${clock(u0, d0)} to ${until}: camps with ${f.name} (${WK.camps[kind].name.toLowerCase()}).`);
    }
    S.msg = "";
  }
  function campOption(f, k, cur){
    const r = campCost(f, k);
    let note = " · " + fmtH(r.hours);
    if (r.same) note = " (made)";
    else if (r.error) note = " (not here)";
    return `<option value="${k}" ${k === cur ? "selected" : ""}>${esc(WK.camps[k].name)}${note}</option>`;
  }
  function campText(sel, kind){
    const f = leaderOf(sel), c = WK.camps[kind], r = campCost(f, kind);
    if (r.same) return `${f.name} already has a ${c.name.toLowerCase()} here.`;
    if (r.error) return `${c.desc} Not here: it ${r.error}.`;
    const done = campDone(f.day, f.used, r.hours, hpdList(f.day));
    const until = done.day === f.day ? "" : ` (done ${dateText(done.day, true)}, ${clock(done.used, done.day)})`;
    const fit = colDiggers(f), men = colMen(f) === fit ? `${fit} men` : `${colMen(f)} men (${fit} fit to dig)`;
    return `${c.desc} ${men}: ${fmtH(r.hours)}${until}`
      + (r.labour ? `, ${Math.round(r.labour)} man-hours for a ${Math.round(r.perimeter)} m perimeter${(c.works || []).some(w => (WK.edge_works[w] || WK.hex_works[w]).haul) ? (r.woods ? ", timber to hand" : ", timber hauled from afar") : ""}` : "") + ".";
  }
  const esc = s => String(s).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll('"', "&quot;");
  function byId(id){ return forcesHere().find(o => o.id === id) }
  function namesList(xs){ return xs.length < 3 ? xs.join(" and ") : xs.slice(0, -1).join(", ") + " and " + xs[xs.length - 1] }

  return { SIDE_NAMES, sidesAround, sideToward, cameFrom, nearWoods, campPerimeter, campHours, KEY, S, save, restore, baseMap, curMap, sameHex, forcesHere, newForce, selForce, sides, MONTHS, WEEKDAYS, win, hpdOf, hpdList, clock, dateText, wxState, dayWeather, regroundFrom, rerollDay, setDay, groundOf, knownGround, healthOf, fitOf, horsesOf, horsePct, speedOf, loadEraOf, loadOrder, forceBands, loadPct, loadOptions, marchedKm, loadTire, blisters, packsLost, groundText, wxLine, localTongues, speaksLocal, tongueNames, interpHere, forageTongue, foraged, USES, bestTalk, billetCheck, hostFeeds, huntNight, animalRow, wheelsToday, fodderNight, wayToday, amongNight, endDay, supOf, waterHere, supplyNight, depotHere, trainHere, refillForce, rationCost, buyRations, supplyHtml, BED_TERRAIN, fedByArmy, keepLedger, keepWants, keepMan, keepNight, keepText, forceEra, eventsOn, hungryNow, conditionsOf, eventsNight, namedAccidents, dzName, dzShort, tallyText, nightHardness, nightHard, healthNight, NAMED_KEY, readNamed, writeNamed, namedWith, hasWagons, riskGround, sweptOff, fordMan, fordAt, fordsCrossed, strainNight, hasCases, kitNight, worstKit, MEND_WORD, mendDay, awayNight, xpNight, drillWeek, clothedCtx, namedNight, namedEnd, namedDay, namedWeek, ableNow, nursesNow, bestSkill, namedLine, weekFactorsFor, healthWeekFor, fmtH, placeAt, where, refusal, leaderOf, columnOf, colType, colSpeed, colMen, colTools, colFit, colDiggers, colName, colRefusal, joinOptions, joinColumn, leaveColumn, replan, addWaypoint, noMarchText, NIGHT, nightHoursOf, dayEnd, isNight, nightWay, march, followLeader, CLOCK_STEP, CLOCK_LEAST, nextTick, atOrAfter, busy, waitUntil, clockNow, marching, pairKey, meetings, nightFalls, tickClock, marchAll, newMeetings, marchLogs, anyAtWork, passNight, clockStep, runClock, moveClock, setOrder, hexDist, campHere, campCost, makeCamp, campOption, campText, esc, byId, namesList, restColumn, roll100 };
}

if (typeof module !== "undefined") module.exports = makeTravelDay;   // Node (the tests); the page has no `module`
