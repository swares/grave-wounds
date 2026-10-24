/* The travel map's rules, with no page: the calendar, daylight, weather, rest and fatigue (as
   gravewounds/weather.py); routes, marching, camps' hours and who fights (as gravewounds/travel.py);
   camp disease (as gravewounds/disease.py). Moved here from templates/travel.html unchanged, so the
   travel map and anything else (the campaign console, the tests) run the same rules.

   makeTravelRules(DATA, lib) -> every rule below by name. DATA is the travel page's data bundle
   (terrain, weather, works, disease, hazards, supplies). lib holds the few rules that live in other
   shared files, for fords and medical stores: {partyOf (camp.js), hzCurrentBand, hzFordWater,
   spMedicalShort (ranks.js)}. Dice are the caller's: weather takes its d100 rolls as a list, disease
   an rng() giving 1-100. build.py puts this file into the travel page at its TRAVELRULES_JS marker;
   in Node it is a module (tools/travel/test.js). */
function makeTravelRules(DATA, lib = {}){
  const TER = DATA.terrain, TT = TER.terrain, FT = TER.forces;
  const BYKEY = Object.fromEntries(Object.values(TT).map(t => [t.key, t]));
  const WXD = DATA.weather, WK = DATA.works, DZ = DATA.disease;
  const partyOf = lib.partyOf || ((men, ftype) => (typeof ftype === "string" ? [[ftype, men]] : ftype.map(p => p.slice())));
  const { hzCurrentBand, hzFordWater, spMedicalShort } = lib;

  /* ---------- calendar, daylight, weather, rest and fatigue: same rules as gravewounds/weather.py ---------- */
  const fdiv = (a, b) => Math.floor(a / b);
  function jdn(y, m, d, calendar){
    const a = fdiv(14 - m, 12), yy = y + 4800 - a, mm = m + 12 * a - 3;
    let n = d + fdiv(153 * mm + 2, 5) + 365 * yy + fdiv(yy, 4) - 32083;
    if (calendar === "gregorian") n = n - fdiv(yy, 100) + fdiv(yy, 400) + 38;
    return n;
  }
  function fromJdn(n, calendar){
    let b = 0, c = n + 32082;
    if (calendar === "gregorian"){ const a = n + 32044; b = fdiv(4 * a + 3, 146097); c = a - fdiv(146097 * b, 4) }
    const dd = fdiv(4 * c + 3, 1461), e = c - fdiv(1461 * dd, 4), mm = fdiv(5 * e + 2, 153);
    return [100 * b + dd - 4800 + fdiv(mm, 10), mm + 3 - 12 * fdiv(mm, 10), e - fdiv(153 * mm + 2, 5) + 1];
  }
  function parseDate(s){
    const neg = s.startsWith("-"), [y, m, d] = s.replace(/^-/, "").split("-").map(Number);
    return [neg ? -y : y, m, d];
  }
  const mapJdn = (m, day) => jdn(...parseDate(m.start_date), m.calendar) + day - 1;
  const mapDate = (m, day) => fromJdn(mapJdn(m, day), m.calendar);
  function solarDayOfYear(m, day){
    const n = mapJdn(m, day), [y] = fromJdn(n, "gregorian");
    return n - jdn(y, 1, 1, "gregorian") + 1;
  }
  function daysInMonth(y, mo, calendar){
    const ny = mo === 12 ? y + 1 : y, nm = mo === 12 ? 1 : mo + 1;
    return jdn(ny, nm, 1, calendar) - jdn(y, mo, 1, calendar);
  }
  function daylight(lat, doy){
    const rad = Math.PI / 180, decl = 23.44 * Math.sin(2 * Math.PI * (284 + doy) / 365);
    const x = Math.max(-1, Math.min(1, -Math.tan(lat * rad) * Math.tan(decl * rad)));
    return 2 * (Math.acos(x) * 180 / Math.PI) / 15;
  }
  function marchWindow(m, day){
    const DL = WXD.daylight, dl = daylight(m.latitude, solarDayOfYear(m, day));
    const sunrise = 12 - dl / 2, sunset = 12 + dl / 2;
    const start = Math.ceil((sunrise + DL.start_after_sunrise) * 4 - 1e-9) / 4;
    const end = Math.floor((sunset - DL.stop_before_sunset) * 4 + 1e-9) / 4;
    const hours = Math.max(DL.min_hours, Math.min(TER.hours_per_day, end - start));
    return { start, hours, sunrise, sunset };
  }
  function coldLevel(low){                         // the field map's cold for this low: the coldest level it is at or under, or null
    const hit = Object.entries(WXD.cold?.levels || {}).filter(([, v]) => low !== null && low !== undefined && low <= v.below).sort((a, b) => a[1].below - b[1].below);
    return hit.length ? hit[0][0] : null;
  }
  const MOON_DAYS = 29.530588853, NEW_MOON_JDN = 2451550;   // the moon's month; a new moon (6 January 2000)
  const moonAge = n => (((n - NEW_MOON_JDN) % MOON_DAYS) + MOON_DAYS) % MOON_DAYS;
  function lightAt(m, day, hour, cond){            // day, dusk, moonlit or night at this hour (weather.yaml light)
    const L = WXD.light, w = marchWindow(m, day), t = ((hour % 24) + 24) % 24;
    if (Math.abs(t - w.sunrise) < L.dusk_hours || Math.abs(t - w.sunset) < L.dusk_hours) return "dusk";
    if (w.sunrise < t && t < w.sunset) return "day";
    const age = moonAge(mapJdn(m, day)), shown = (1 - Math.cos(2 * Math.PI * age / MOON_DAYS)) / 2;
    const up = (((t - (6 + age * 24 / MOON_DAYS)) % 24) + 24) % 24 < 12;
    return up && shown >= L.moon_from && L.moon_shows.includes(cond) ? "moonlit" : "night";
  }
  const pickRow = (rows, roll) => rows.find(r => roll <= r.upto);
  function rollWeather(m, day, prev, rolls){
    const cl = WXD.climates[m.climate], [y, mo] = mapDate(m, day), dim = daysInMonth(y, mo, m.calendar);
    const p = cl.rain[mo - 1] / dim, r = WXD.persistence;
    const wetBefore = !!prev && WXD.conditions[prev.cond].precip !== "none";
    const pw = wetBefore ? p + r * (1 - p) : p * (1 - r);
    const wet = rolls[0] <= Math.floor(pw * 100 + 0.5);
    const anomaly = Math.trunc((prev ? prev.anomaly : 0) * WXD.anomaly_carry) + pickRow(WXD.anomaly, rolls[2]).deg;
    const shift = m.climate_shift || 0;
    const high = cl.high[mo - 1] + shift + anomaly, low = cl.low[mo - 1] + shift + anomaly;
    let cond;
    if (wet){ const row = pickRow(WXD.intensity, rolls[1]); cond = high <= WXD.snow_at_or_below ? row.snow : row.rain }
    else if (rolls[3] <= Math.floor(cl.fog[mo - 1] / dim * 100 + 0.5)) cond = "fog";
    else cond = rolls[1] <= WXD.fair_upto ? "fair" : "overcast";
    const ids = WXD.winds.map(x => x.id);
    let wind = pickRow(WXD.winds, rolls[4]).id;
    const floorWind = WXD.conditions[cond].min_wind;
    if (floorWind && ids.indexOf(wind) < ids.indexOf(floorWind)) wind = floorWind;
    const out = { cond, wind, high, low, anomaly };
    if (rolls.length > 6) out.dir = windDir(cl, prev, rolls[5], rolls[6]);   // two more rolls: the wind's direction
    return out;
  }
  function windDir(cl, prev, keepRoll, pickRoll){   // the day before's on keepRoll <= wind_keep, else picked from the climate's prevailing winds
    const pts = WXD.wind_points;
    if (prev && pts.includes(prev.dir) && keepRoll <= WXD.wind_keep) return prev.dir;
    let acc = 0;
    for (let i = 0; i < pts.length; i++){ acc += cl.wind_from[i]; if (pickRoll <= acc) return pts[i] }
    return pts.at(-1);
  }
  const WIND_NAMES = { N: "north", NE: "north-east", E: "east", SE: "south-east", S: "south", SW: "south-west", W: "west", NW: "north-west" };
  function nextGround(prev, w){
    const G = WXD.ground, g = prev ? { ...prev } : { mud: 0, snow: 0, flood: 0 }, cond = w.cond;
    const precip = WXD.conditions[cond].precip;
    if (cond in G.mud_add) g.mud = Math.min(G.mud_max, g.mud + G.mud_add[cond]);
    else if (precip === "none") g.mud = Math.max(0, g.mud - (w.high >= G.warm_at ? G.mud_dry_warm : G.mud_dry));
    if (cond in G.snow_add) g.snow = Math.min(G.snow_max, g.snow + G.snow_add[cond]);
    else if (w.high > WXD.snow_at_or_below) g.snow = Math.max(0, g.snow - (w.high >= G.mild_at ? G.snow_melt_mild : G.snow_melt));
    g.flood = G.flood_from.includes(cond) ? G.flood_days : Math.max(0, g.flood - 1);
    return g;
  }
  function terrainPct(tid, ground){
    if (!ground) return 100;
    let pct = 100;
    if ((ground.mud || 0) >= 1) pct = Math.max(pct, WXD.march.mud[tid] ?? 100);
    if ((ground.snow || 0) >= 1) pct = Math.max(pct, WXD.march.snow[tid] ?? 100);
    return pct;
  }
  const flooded = (tid, ground) => !!(ground && (ground.flood || 0) > 0 && WXD.march.flooded.includes(tid));
  function nightRest(camp, w){
    const levels = WXD.rest_levels, base = levels.indexOf(camp ? WK.camps[camp].rest : "poor");
    const cold = Math.max(0, ...WXD.cold_hardship.filter(c => w.low <= c.low_at_or_below).map(c => c.add));
    const hardship = WXD.conditions[w.cond].hardship + cold, shelter = WXD.shelter[camp || "none"];
    return Math.max(0, base - Math.max(0, hardship - shelter));
  }
  function fatigueAfter(fatigue, marched, w, ground, rest){
    const F = WXD.fatigue;
    let add = 0;
    if (marched >= F.heat_cold_min_hours - 1e-9){
      for (const h of F.heat) if (w.high >= h.high_at_or_over) add = Math.max(add, h.add);
      for (const c of F.cold) if (w.high <= c.high_at_or_below) add = Math.max(add, c.add);
    }
    const deep = WXD.ground.deep;
    if (marched >= F.heavy_going_hours - 1e-9 && ((ground.mud || 0) >= deep || (ground.snow || 0) >= deep)) add += 1;
    add += F.night[WXD.rest_levels[rest]];
    return Math.max(0, Math.min(F.levels.length - 1, fatigue + add));
  }
  /* ---------- routes, marching, camps' hours and who fights: same rules as gravewounds/travel.py ---------- */
  const NEIGHBOURS = [[[1, 0], [0, -1], [-1, -1], [-1, 0], [-1, 1], [0, 1]], [[1, 0], [1, -1], [0, -1], [-1, 0], [0, 1], [1, 1]]];
  function neighbours([c, r], cols, rows){
    return NEIGHBOURS[r & 1].map(([dc, dr]) => [c + dc, r + dr]).filter(([x, y]) => x >= 0 && x < cols && y >= 0 && y < rows);
  }
  const terrainAt = (m, h) => BYKEY[m.rows[h[1]][h[0]]];
  const forceTypes = ftype => partyOf(0, ftype).map(p => p[0]);   // one force's type, or a column's types
  function fordFrac(h, k){                        // a fraction fixed by the hex, for its ford's depth (k 0) and current (k 1)
    const n = h[0] * 73 + h[1] * 151 + k * 233 + 17;
    return n * n % 1000003 * 48271 % 1000003 / 1000003;
  }
  function fordHere(m, h, ground = null){           // this ford's {depth, current, band}: a map place may set its own for ordinary water
    const flood = (ground?.flood || 0) > 0, p = (m.places || []).find(x => x.hex && x.hex[0] === h[0] && x.hex[1] === h[1] && "depth" in x);
    if (p && !flood) return { depth: p.depth, current: p.current, band: hzCurrentBand(p.current) };
    return hzFordWater(flood ? "flooded" : "normal", fordFrac(h, 0), fordFrac(h, 1));
  }
  function tooDeep(m, h, ftype, ground = null){    // a ford deeper than wheels can cross, for a force with baggage wagons
    const F = DATA.hazards?.fords;
    if (!F?.wade?.wheels || !forceTypes(ftype).includes("wagons") || terrainAt(m, h).id !== "ford") return false;
    if (+String(m.start_date || "9999").slice(0, 4) >= (F.wade.wheels_before ?? 9999)) return false;   // later, the wagons type is tanks and lorries
    return fordHere(m, h, ground).depth > F.wade.wheels;
  }
  function passable(m, h, ftype, ground = null){  // this force, or every force in this column, can enter h
    const t = terrainAt(m, h), barred = forceTypes(ftype).flatMap(ft => FT[ft].cannot_enter || []);
    return t.cost !== null && t.cost !== undefined && !barred.includes(t.id) && !flooded(t.id, ground) && !tooDeep(m, h, ftype, ground);
  }
  const columnKmh = ftype => Math.min(...forceTypes(ftype).map(ft => FT[ft].kmh));   // the slowest force's road speed
  const hexWeight = (t, ground) => Math.floor(t.cost * terrainPct(t.id, ground) + 0.5);
  const stepWeight = (m, a, b, ground = null) => hexWeight(terrainAt(m, a), ground) + hexWeight(terrainAt(m, b), ground);
  const stepHours = (m, a, b, ftype, ground = null, speed = 100) => stepWeight(m, a, b, ground) / 200 * m.hex_km / (columnKmh(ftype) * speed / 100);
  function heapPush(hp, x){ hp.push(x); let i = hp.length - 1; while (i > 0){ const p = (i - 1) >> 1; if (less(hp[p], hp[i])) break; [hp[p], hp[i]] = [hp[i], hp[p]]; i = p } }
  function heapPop(hp){
    const top = hp[0], last = hp.pop();
    if (hp.length){ hp[0] = last; let i = 0; for (;;){ const l = 2 * i + 1, r = l + 1; let m = i;
      if (l < hp.length && less(hp[l], hp[m])) m = l; if (r < hp.length && less(hp[r], hp[m])) m = r; if (m === i) break; [hp[m], hp[i]] = [hp[i], hp[m]]; i = m } }
    return top;
  }
  const less = (a, b) => a[0] < b[0] || (a[0] === b[0] && a[1] < b[1]);
  function tracePath(prev, start, goal){        // walk back from the goal along prev
    const key = h => h[0] + "," + h[1], path = [];
    let h = goal;
    while (key(h) !== key(start)){ path.push(h.slice()); h = prev.get(key(h)) }
    path.push(start.slice());
    return path.reverse();
  }
  function route(m, start, goal, ftype, ground = null){
    const key = h => h[0] + "," + h[1];
    if (start[0] === goal[0] && start[1] === goal[1]) return [start.slice()];
    if (!passable(m, goal, ftype, ground)) return null;
    const cols = m.rows[0].length, rows = m.rows.length;
    const best = new Map([[key(start), 0]]), prev = new Map(), done = new Set(), hp = [[0, 0, start]];
    let seq = 1;
    const relax = (h, dist, n) => {
      if (!passable(m, n, ftype, ground)) return;
      const nd = dist + stepWeight(m, h, n, ground), nk = key(n);
      if (nd >= (best.has(nk) ? best.get(nk) : Infinity)) return;
      best.set(nk, nd); prev.set(nk, h); heapPush(hp, [nd, seq++, n]);
    };
    while (hp.length){
      const [dist, , h] = heapPop(hp), k = key(h);
      if (done.has(k)) continue;
      done.add(k);
      if (h[0] === goal[0] && h[1] === goal[1]) break;
      for (const n of neighbours(h, cols, rows)) relax(h, dist, n);
    }
    return prev.has(key(goal)) ? tracePath(prev, start, goal) : null;
  }
  function plan(m, start, waypoints, ftype, ground = null){
    let path = [start.slice()], at = start.slice();
    for (const w of waypoints){
      const leg = route(m, at, w, ftype, ground);
      if (!leg) return null;
      path = path.concat(leg.slice(1)); at = w.slice();
    }
    return path;
  }
  const hpdAt = (list, i) => (list && list.length ? list[Math.min(i, list.length - 1)] : TER.hours_per_day);
  // opts: {hpdList, ground, speed} (see gravewounds/travel.py schedule)
  function groundAt(ground, i){                 // one ground for every day, or a list by day (the last repeats)
    if (!Array.isArray(ground)) return ground;
    return ground.length ? ground[Math.min(i, ground.length - 1)] : null;
  }
  // opts: {hpdList, ground (one for every day, or a list by day from `day`; the last repeats), speed}
  function schedule(m, path, ftype, day = 1, used = 0, opts = {}){
    const { hpdList = null, ground = null, speed = 100 } = opts;
    const first = day, out = path.length ? [{ hex: path[0].slice(), day, used }] : [];
    for (let i = 0; i + 1 < path.length; i++){
      let st = stepHours(m, path[i], path[i + 1], ftype, groundAt(ground, day - first), speed);
      if (used > 0 && used + st > hpdAt(hpdList, day - first) + 1e-9){
        day += 1;
        used = 0;
        st = stepHours(m, path[i], path[i + 1], ftype, groundAt(ground, day - first), speed);
      }
      used += st;
      out.push({ hex: path[i + 1].slice(), day, used });
    }
    return out;
  }
  // opts: {hpd, ftype, ground, speed} (see gravewounds/travel.py advance)
  function advance(m, path, index, used, hours, opts){   // -> {index, used, carried}: carried, hours already marched into the next hex
    const { hpd, ftype, ground = null, speed = 100, carried = 0 } = opts;
    const target = Math.min(used + hours, hpd), start = index;
    while (index + 1 < path.length){
      const st = Math.max(0, stepHours(m, path[index], path[index + 1], ftype, ground, speed) - (index === start ? carried : 0));
      if (used + st > target + 1e-9) break;
      used += st; index += 1;
    }
    if (index + 1 >= path.length) return { index, used, carried: 0 };
    return { index, used: Math.max(used, target), carried: (index === start ? carried : 0) + Math.max(0, target - used) };
  }
  function hexDistance(a, b){
    const cube = ([c, r]) => { const q = c - (r - (r & 1)) / 2; return [q, r, -q - r] };
    const x = cube(a), y = cube(b);
    return Math.max(Math.abs(x[0] - y[0]), Math.abs(x[1] - y[1]), Math.abs(x[2] - y[2]));
  }
  const hkey = h => h[0] + "," + h[1];
  function edgeKey(a, b){ const [x, y] = [a, b].slice().sort((p, q) => p[1] - q[1] || p[0] - q[0]); return hkey(x) + "|" + hkey(y) }
  function campDone(day, used, hours, hpdList = null){
    const ev = WK.evening_hours;
    let i = 0, left = hours;
    if (used >= hpdAt(hpdList, i) + ev - 1e-9){ day += 1; used = 0; i += 1 }
    while (used + left > hpdAt(hpdList, i) + ev + 1e-9){ left -= hpdAt(hpdList, i) + ev - used; day += 1; used = 0; i += 1 }
    return { day, used: used + left };
  }
  function campWorked(start, day, used, hpdList = null){   // hours of camp work from start until (day, used)
    const ev = WK.evening_hours;
    let t = 0;
    for (let k = start.day; k <= day; k++){
      const cap = hpdAt(hpdList, k - start.day) + ev, begin = k === start.day ? start.used : 0, end = k === day ? used : cap;
      t += Math.max(0, Math.min(end, cap) - begin);
    }
    return t;
  }
  function campLabourDone(camp, day, used, hpdList = null){  // man-hours of the camp's works done by (day, used)
    if (!camp.start) return camp.labour || 0;
    return Math.min(camp.labour, Math.max(0, campWorked(camp.start, day, used, hpdList) - camp.setup) * camp.rate);
  }
  // Who fights (as gravewounds.travel.fight_plan)
  const camped = o => !!o.camp && o.camp.hex[0] === o.pos[0] && o.camp.hex[1] === o.pos[1];
  function nearForces(forces, x, sameSide, campedOnly = false){
    const reach = TER.fight_within;
    return forces.map((o, i) => [hexDistance(o.pos, x.pos), i, o])
      .filter(([dd, , o]) => o !== x && (o.side === x.side) === sameSide && dd <= reach && (camped(o) || !campedOnly))
      .sort((p, q) => p[0] - q[0] || p[1] - q[1]).map(t => t[2]);
  }
  function arrived(o){                         // when it got here: when it began its camp here, else its clock
    return camped(o) && o.camp.from ? o.camp.from : { day: o.day, used: o.used };
  }
  const clockAfter = (o, day, used) => { const a = arrived(o); return a.day > day || (a.day === day && a.used > used) };
  const before = (a, b) => a.day < b.day || (a.day === b.day && a.used < b.used);
  const laterOf = (a, b) => (before(b, a) ? a : b);
  function fightPlan(forces, sel, wait = true){
    const f = forces.find(o => o.id === sel);
    let defender = f;
    if (!camped(f)){                           // fight from a camp within reach: our own side's first
      const ours = nearForces(forces, f, true, true), camps = ours.length ? ours : nearForces(forces, f, false, true);
      if (camps.length) defender = camps[0];
    }
    const attackers = nearForces(forces, defender, false);
    let now = arrived(defender);
    for (const o of attackers) now = laterOf(arrived(o), now);
    const ready = laterOf({ day: defender.day, used: defender.used }, now);
    const { day, used } = wait ? ready : now, early = before(now, ready);
    const friends = nearForces(forces, defender, true);
    return { defender: defender.id, allies: friends.filter(o => !clockAfter(o, day, used)).map(o => o.id),
      attackers: attackers.map(o => o.id), late: friends.filter(o => clockAfter(o, day, used)).map(o => o.id), day, used, early };
  }
  // Surprise (as gravewounds.travel.surprise): the defenders caught unawares
  function surpriseChance(campKind, dark, fog, stealth = 0, watch = 0){   // {chance, parts: [[why, n]]}
    const S0 = WK.surprise, camp = campKind ? WK.camps[campKind].surprise : S0.none;
    const parts = [["base", S0.base], ["camp", camp], ["dark", dark ? S0.dark : 0], ["fog", fog ? S0.fog : 0],
      ["stealth", Math.floor(Math.max(0, stealth) / S0.per)], ["watch", -Math.floor(Math.max(0, watch) / S0.per)]];
    const [lo, hi] = S0.range;
    return { chance: Math.max(lo, Math.min(hi, parts.reduce((t, [, n]) => t + n, 0))), parts: parts.filter(([, n]) => n) };
  }
  /* ---------- camp disease: same rules as gravewounds/disease.py ---------- */
  // A force's health: {cases, immune, had, dead}; cases are the men sick or incubating, one
  // disease each: {d, inc, step, peak (0 once reached), shown, chronic}. rng() returns d100.
  // Men carried from the field map are cases of "wound" (with inf and fever days) or "fever".
  const dzProfile = did => (did === "scurvy" || did === "frostbite" ? DZ[did] : DZ.diseases[did] || DZ.wounds[did]);
  const newHealth = () => ({ cases: [], immune: {}, had: {}, dead: 0 });
  const copyHealth = h => ({ cases: h.cases.map(c => ({ ...c })), immune: { ...h.immune }, had: { ...h.had }, dead: h.dead });
  const dzStep = name => DZ.steps.indexOf(name);
  const dzPick = (lo, hi, rng) => lo + (rng() - 1) % (hi - lo + 1);
  function healthCounts(health, men){           // {sick, incubating, unfit, carried, fit}
    const shown = health.cases.filter(c => c.inc === 0);
    const unfit = shown.filter(c => c.step >= dzStep(DZ.unfit_from)).length, carried = shown.filter(c => c.step >= dzStep(DZ.carried_from)).length;
    const fit = Math.max(0, men - unfit), nurses = Math.min(fit, Math.ceil(unfit / DZ.nursing.patients));
    return { sick: shown.length, incubating: health.cases.length - shown.length, unfit, carried, fit, nurses };
  }
  function sickMarchPct(fit, carried){          // % of its speed a force keeps while carrying litters
    const L = DZ.litters;
    if (carried === 0) return 100;
    if (fit === 0) return 0;
    return fit < L.bearers * carried ? L.short : L.march;
  }
  const campHygiene = (gm, campKind) => gm || DZ.camp_hygiene[campKind || "none"];
  const CARE_STEPS = ["none", "field", "shelter"];
  const campCare = (campKind, f = null) => {        // the camp's care, a step worse when the force's medical stores are gone
    const c = DZ.camp_care[campKind || "none"];
    return f?.sup && DATA.supplies && spMedicalShort(f.sup) ? CARE_STEPS[Math.max(0, CARE_STEPS.indexOf(c) - 1)] : c;
  };
  function weekFactors(o){                       // o: {hygiene, camped_days, terrain, highs, wet, plague}
    const f = [];
    if (o.hygiene === "poor" || o.hygiene === "good") f.push(o.hygiene);
    if (o.camped_days >= DZ.staying_days){
      f.push("staying");
      if (o.hygiene === "poor") f.push("crowded");
    }
    for (const [k, ts] of Object.entries(DZ.terrain_factors)) if (ts.includes(o.terrain)) f.push(k);
    f.push(...weatherFactors(o.highs, o.wet));
    if (o.plague) f.push("plague");
    return f;
  }
  function weatherFactors(highs, wet){            // the past week's warmth, heat, and cold wet
    if (!highs.length) return [];
    const f = [], mean = highs.reduce((t, x) => t + x, 0) / highs.length;
    if (mean >= DZ.warm_at) f.push("warm");
    if (Math.max(...highs) >= DZ.hot_at) f.push("hot");
    if (wet.filter(Boolean).length >= DZ.cold_wet_days && mean <= DZ.cold_wet_at) f.push("cold_wet");
    return f;
  }
  function outbreakChance(did, factors, extra = null){   // base + the factors' mods + contagion (extra: {did: add})
    const x = DZ.diseases[did];
    if ((x.needs || []).some(n => !factors.includes(n))) return 0;
    const add = Object.entries(x.mods).reduce((t, [k, v]) => t + (factors.includes(k) ? v : 0), 0);
    return Math.max(0, Math.min(100, x.base + add + ((extra || {})[did] || 0)));
  }
  const patientsOf = h => h.cases.filter(c => c.inc === 0 && c.step >= dzStep(DZ.unfit_from));   // the sick who need nursing, in order
  function nursingOf(h, men, clean = false){      // {patients: {did: n}, unfit, nurses, unnursed, clean}
    const N = DZ.nursing, pts = patientsOf(h), by = {};
    for (const c of pts) by[c.d] = (by[c.d] || 0) + 1;
    const fit = Math.max(0, men - pts.length), nurses = Math.min(fit, Math.ceil(pts.length / N.patients));
    return { patients: by, unfit: pts.length, nurses, unnursed: Math.max(0, pts.length - nurses * N.patients), clean };
  }
  function contagionOf(h, men){                   // {did: add}: outbreak chances raised by the men already sick
    const C = DZ.nursing.contagion, out = {};
    if (men <= 0) return out;
    for (const [did, add] of Object.entries(C.add)){
      const sick = h.cases.filter(c => c.d === did && c.inc === 0).length;
      out[did] = Math.floor((100 * sick) / (men * C.per)) * add;
    }
    return out;
  }
  function nurseChance(did, nurse, endurance = DZ.endurance){   // % a week one nurse catches it from his patients
    const s = DZ.nursing.spread[did];
    if (!s || !nurse.unfit || !nurse.patients[did] || (nurse.clean && s.clean)) return 0;
    return s.nurse * nurse.patients[did] / nurse.unfit * (100 - endurance) / 100;
  }
  function nursesCatch(h, men, nurse, rng, endurance){
    const ev = [];
    for (const did of Object.keys(DZ.nursing.spread)){
      const p = nurseChance(did, nurse, endurance) * 100;
      if (p <= 0) continue;
      const well = Math.max(0, men - h.cases.length - (h.immune[did] || 0));
      let caught = 0;
      for (let i = 0; i < Math.min(nurse.nurses, well); i++){
        if (d10000(rng) > p) continue;
        h.cases.push(newCase(did, rng));
        caught++;
      }
      if (caught) ev.push({ kind: "nursed", d: did, n: caught });
    }
    return ev;
  }
  function newCase(did, rng){
    const x = DZ.diseases[did], inc = dzPick(x.incubation[0], x.incubation[1], rng), roll = rng();
    return { d: did, inc, step: 0, peak: dzStep(x.peak.find(r => roll <= r.upto).step), shown: 0, chronic: false };
  }
  // % a well man catches it this week: a typical man's Endurance, or a named character's own
  const catchChance = (did, factors, endurance = DZ.endurance, extra = null) => outbreakChance(did, factors, extra) * (100 - endurance) / 100;
  const d10000 = rng => (rng() - 1) * 100 + rng();
  // fresh food today: good forage, fair when camped all day or found by a named man's Fieldcraft, or issued
  function freshToday(forage, camped, issued = false, found = false){
    const F = DZ.scurvy.fresh;
    return issued || F.forage.includes(forage) || (camped && F.camped.includes(forage)) || (found && F.fieldcraft.includes(forage));
  }
  const fieldcraftNeeded = (forage, camped) => !camped && DZ.scurvy.fresh.fieldcraft.includes(forage);   // only then can Fieldcraft find it
  const leechBonus = leechcraft => Math.floor(Math.max(0, leechcraft) / DZ.leech.per);
  function scurvyChance(noFresh, endurance = DZ.endurance){   // % a well man falls ill with scurvy this week
    const S = DZ.scurvy;
    if (noFresh < S.after_days) return 0;
    const weeks = Math.floor((noFresh - S.after_days) / DZ.week_days);
    return Math.min(100, S.chance + S.per_week * weeks) * (100 - endurance) / 100;
  }
  const scurvyCase = () => ({ d: "scurvy", inc: 0, step: dzStep("mending"), peak: 0, shown: 0, chronic: false });
  function scurvyWeek(h, men, noFresh, rng, endurance){   // each well man may fall ill (it shows at once)
    const p = scurvyChance(noFresh, endurance) * 100;
    if (p <= 0) return [];
    let ill = 0;
    for (let i = Math.max(0, men - h.cases.length); i > 0; i--){
      if (d10000(rng) > p) continue;
      h.cases.push(scurvyCase());
      ill++;
    }
    return ill ? [{ kind: "scurvy", d: "scurvy", n: ill }] : [];
  }
  function reopenOld(health, olds){              // scurvy reopens a named man's old wounds ({key, loc}) at Mending
    const h = copyHealth(health), have = new Set(h.cases.map(c => c.wid));
    for (const o of olds){
      const wid = "old:" + o.key;
      if (!have.has(wid)) h.cases.push({ d: "wound", inc: 0, step: dzStep("mending"), peak: 0, shown: 0, chronic: false, wid, old: true });
    }
    return h;
  }
  // The weekly roll: each well man may catch each disease (with the camp's contagion `more.extra`), then
  // scurvy after `more.noFresh` days without fresh food, then the nurses roll for what their patients have
  // (`more.nurse`: nursingOf), then relapses -> {health, events}
  function healthWeek(health, men, factors, rng, endurance = DZ.endurance, more = {}){
    const { extra = null, nurse = null, noFresh = 0 } = more;
    const h = copyHealth(health), ev = [];
    for (const did of Object.keys(DZ.diseases)){
      const p = catchChance(did, factors, endurance, extra) * 100;
      if (p <= 0) continue;
      const exposed = Math.max(0, men - h.cases.length - (h.immune[did] || 0));
      let caught = 0;
      for (let i = 0; i < exposed; i++){
        if (d10000(rng) > p) continue;
        h.cases.push(newCase(did, rng));
        caught++;
      }
      if (caught) ev.push({ kind: "caught", d: did, n: caught });
    }
    ev.push(...scurvyWeek(h, men, noFresh, rng, endurance));
    if (nurse) ev.push(...nursesCatch(h, men, nurse, rng, endurance));
    ev.push(...relapses(h, factors, rng));
    return { health: h, events: ev };
  }
  function relapses(h, factors, rng){           // men who have had a relapsing disease fall ill again, in marsh country
    const ev = [];
    for (const [did, x] of Object.entries(DZ.diseases)){
      if (!x.relapse || !factors.includes("marsh")) continue;
      let back = 0;
      for (let i = 0; i < (h.had[did] || 0); i++) if (rng() <= x.relapse) back++;
      if (!back) continue;
      h.had[did] -= back;
      for (let i = 0; i < back; i++) h.cases.push({ d: did, inc: 0, step: dzStep("serious"), peak: 0, shown: 0, chronic: false });
      ev.push({ kind: "relapse", d: did, n: back });
    }
    return ev;
  }
  function checksToday(x, c){
    if (c.chronic) return c.shown % 7 === 0;
    if (x.every) return c.shown % x.every === 0;
    return c.shown >= (x.checks_from || 0);
  }
  function recoverCase(c, target, rng){          // one recovery check: "dead", "healed" or "sick"
    const x = dzProfile(c.d), big = DZ.recovery.big, deadly = DZ.steps.length - 1, m = target - x.virulence - rng();
    if (m >= big) c.step -= 2;
    else if (m >= 0) c.step -= 1;
    else if (c.step === deadly) return "dead";
    else if (m <= -big){
      if (x.chronic && c.step <= dzStep("serious")){
        c.chronic = true;
        c.step = dzStep("serious");
      } else c.step += 1;
    }
    return c.step <= 0 ? "healed" : "sick";
  }
  function scurvyCheck(c, target, rng, fresh){   // weekly: fresh food heals; unfed, success holds and failure worsens
    const x = DZ.scurvy;
    if (fresh){
      c.step -= x.heal;
      return c.step <= 0 ? "healed" : "sick";
    }
    if (target - x.virulence - rng() >= 0) return "sick";
    if (c.step === DZ.steps.length - 1) return "dead";
    c.step += 1;
    return "sick";
  }
  function septic(c, care, rng, ev, leech = 0){   // a wound's fever day: it turns septic (wound fever, a step worse) or not
    const W = DZ.wounds;
    c.fever = 0;
    if (rng() > W.fever_chance[c.inf] + W.fever_care[care] - leech) return;
    c.d = "fever";
    c.step = Math.min(DZ.steps.length - 1, c.step + 1);
    ev.shown.fever = (ev.shown.fever || 0) + 1;
  }
  // one case's day: "sick" while it lasts, else "healed" or "dead". food: [fresh food in the past week, he has scurvy]
  function caseDay(c, target, rng, ev, care = "field", food = [false, false], leech = 0){
    if (c.fever){
      c.fever -= 1;
      if (c.fever === 0) septic(c, care, rng, ev, leech);
    }
    const x = dzProfile(c.d), tally = k => { ev[k][c.d] = (ev[k][c.d] || 0) + 1 };
    if (c.inc > 0){
      c.inc -= 1;
      if (c.inc === 0){
        c.step = dzStep("mending");
        tally("shown");
      }
      return "sick";
    }
    c.shown += 1;
    if (c.step < c.peak){                         // climbing to its peak, once
      c.step += 1;
      if (c.step >= c.peak) c.peak = 0;
      return "sick";
    }
    let out = "sick";
    if (checksToday(x, c) && !(c.old && food[1])) out = c.d === "scurvy" ? scurvyCheck(c, target, rng, food[0]) : recoverCase(c, target, rng);
    if (out !== "sick") tally(out);
    return out;
  }
  function healthDay(health, ctx, rng, endurance = DZ.endurance){   // a day passes -> {health, events: {shown, healed, dead}}
    const R = DZ.recovery;
    const lb = ctx.leech || 0;
    const target = endurance + R.care[ctx.care] + R.activity[ctx.marched ? "marched" : "rest"] + (ctx.wet_cold ? R.wet_cold : 0) + (ctx.filth ? R.filth : 0) + lb;
    const h = copyHealth(health), ev = { shown: {}, healed: {}, dead: {} }, keep = [];
    const pts = patientsOf(h), k = ctx.unnursed || 0, left = new Set(k ? pts.slice(pts.length - k) : []);   // the last that many get no one to tend them
    const alone = target - R.care[ctx.care] + R.care.none - lb, food = [!!ctx.fresh, h.cases.some(c => c.d === "scurvy")];
    for (const c of h.cases){
      const tended = !left.has(c), x = dzProfile(c.d);
      const out = tended ? caseDay(c, target, rng, ev, ctx.care, food, lb) : caseDay(c, alone, rng, ev, "none", food, 0);
      if (out === "sick") keep.push(c);
      else if (out === "dead") h.dead += 1;
      else if (x.immune) h.immune[c.d] = (h.immune[c.d] || 0) + 1;
      else if (x.relapse) h.had[c.d] = (h.had[c.d] || 0) + 1;
    }
    h.cases = keep;
    frostbiteNight(h, ctx, rng, endurance, ev);
    return { health: h, events: ev };
  }
  function frostbiteChance(low, shelter = 0, endurance = DZ.endurance){   // % a well man is frostbitten tonight (0 if not cold enough)
    const F = DZ.frostbite;
    if (!F || low === null || low === undefined || low > F.below) return 0;
    return Math.min(100, F.base + F.per_degree * (F.below - low)) * Math.max(0, 100 - F.shelter * shelter) / 100 * (100 - endurance) / 100;
  }
  function frostbiteNight(h, ctx, rng, endurance, ev){   // ctx: low, shelter, men; a bitten man shows at once
    const p = frostbiteChance(ctx.low, ctx.shelter || 0, endurance) * 100;
    if (p <= 0) return;
    const F = DZ.frostbite;
    for (let k = Math.max(0, (ctx.men || 0) - h.cases.length); k > 0; k--){
      if (d10000(rng) > p) continue;
      const r = rng(), step = F.peak.find(x => r <= x.upto).step;
      h.cases.push({ d: "frostbite", inc: 0, step: dzStep(step), peak: 0, shown: 0, chronic: false });
      ev.shown.frostbite = (ev.shown.frostbite || 0) + 1;
    }
  }
  return { fdiv, jdn, fromJdn, parseDate, mapJdn, mapDate, solarDayOfYear, daysInMonth, daylight, marchWindow, coldLevel, MOON_DAYS, NEW_MOON_JDN, moonAge, lightAt, pickRow, rollWeather, windDir, WIND_NAMES, nextGround, terrainPct, flooded, nightRest, fatigueAfter, NEIGHBOURS, neighbours, terrainAt, forceTypes, fordFrac, fordHere, tooDeep, passable, columnKmh, hexWeight, stepWeight, stepHours, heapPush, heapPop, less, tracePath, route, plan, hpdAt, groundAt, schedule, advance, hexDistance, hkey, edgeKey, campDone, campWorked, campLabourDone, camped, nearForces, arrived, clockAfter, before, laterOf, fightPlan, surpriseChance, dzProfile, newHealth, copyHealth, dzStep, dzPick, healthCounts, sickMarchPct, campHygiene, CARE_STEPS, campCare, weekFactors, weatherFactors, outbreakChance, patientsOf, nursingOf, contagionOf, nurseChance, nursesCatch, newCase, catchChance, d10000, freshToday, fieldcraftNeeded, leechBonus, scurvyChance, scurvyCase, scurvyWeek, reopenOld, healthWeek, relapses, checksToday, recoverCase, scurvyCheck, septic, caseDay, healthDay, frostbiteChance, frostbiteNight };
}

if (typeof module !== "undefined") module.exports = makeTravelRules;   // Node (the tests); the page has no `module`
