/* Character generation: same rules as gravewounds/team.py, from the team bundle TD that build.py
   writes into the team builder page (TD.era: the era's tables; TD.ranges: old-wound location
   ranges by region and weapon; TD.locs, TD.weapons, TD.kits). The dice are taken in the same
   order as the Python rules. rng: {randint(a, b)}; SeededDice gives repeatable dice for tests. */
class SeededDice {
  constructor(seed){ this.state = Math.max(1, seed % 2147483647) }
  next(){ this.state = this.state * 16807 % 2147483647; return this.state }
  randint(a, b){ return a + this.next() % (b - a + 1) }
  random(){ return this.next() / 2147483647 }
}
const realDice = { randint: (a, b) => a + crypto.getRandomValues(new Uint32Array(1))[0] % (b - a + 1) };   // real dice for play
const byId = (rows, id) => rows.find(r => r.id === id);
const pickRow = (rows, roll) => rows.find(r => roll <= r.to);
/* Women under arms (as team.py): a region's `women` block opens careers at a share (%, rolled on
   1-10000); `no_women` says why a region has none. */
const SHARE_DIE = 10000;
const womenOf = region => byId(TD.era.regions, region).women || null;
function openToWomen(region, careerId){           // [open, why not]
  const W = womenOf(region);
  if (!W) return [false, byId(TD.era.regions, region).no_women || "No women served in this army's fighting careers in these tables."];
  if (!W.careers.includes(careerId)) return [false, W.closed || "Closed to women in this army."];
  return [true, null];
}
function sexFor(region, careerId, sex, rng){      // m or f: as chosen, or (roll) at the region's share, for an open career
  const ok = openToWomen(region, careerId)[0];
  if (sex === "roll"){
    const share = ok ? womenOf(region)?.share : null;
    return share !== null && share !== undefined && rng.randint(1, SHARE_DIE) <= Math.round(share * 100) ? "f" : "m";
  }
  return sex === "f" && ok ? "f" : "m";
}
function nameFor(reg, sex, rng){                  // a name; a woman's from the women's lists, where the region has them
  const W = sex === "f" ? reg.women || {} : {}, names = W.names || reg.names, bynames = W.bynames || reg.bynames;
  return `${names[rng.randint(1, names.length) - 1]} ${bynames[rng.randint(1, bynames.length) - 1]}`;
}
function lookFor(reg, sex, rng){                  // coat colour and beard, both always rolled; a woman has no beard, and long hair
  const beards = ["", "moustache", "beard", "stubble"];
  const look = { colour: reg.colours[rng.randint(1, reg.colours.length) - 1], beard: beards[rng.randint(1, 4) - 1] };
  if (sex === "f") Object.assign(look, { beard: "", hair: "long" });
  return look;
}
const originsFor = (T, sex) => T.origins.filter(o => (o.who ?? sex) === sex);   // the shared origins and his or her own
const PRONOUNS = { he: "she", He: "She", his: "her", His: "Her", him: "her", Him: "Her", himself: "herself", Himself: "Herself" };
const PRONOUN_RE = new RegExp(String.raw`\b(${Object.keys(PRONOUNS).join("|")})\b`, "g");
const pron = (text, sex = "m") => (sex === "f" ? text.replace(PRONOUN_RE, w => PRONOUNS[w]) : text);   // a table's text said of a woman
const kitFor = (T, career, region) => [career.kit[region] ?? career.kit.default, career.weapon[region] ?? career.weapon.default];
function statsFor(T, career, mode, rng){         // 3d6 x 5 each in order, or the fixed array by the career's preferences
  const out = {};
  if (mode === "array"){ career.prefers.forEach((c, i) => { out[c] = T.array[i] }); return out }
  for (const c of T.characteristics) out[c.id] = 5 * (rng.randint(1, 6) + rng.randint(1, 6) + rng.randint(1, 6));
  return out;
}
function applyMod(mod, statMods, gains){          // a trait or drawback: characteristics or skills
  for (const [k, v] of Object.entries(mod)){
    if (k === "text") continue;
    const target = k in statMods ? statMods : gains;
    target[k] = (target[k] || 0) + v;
  }
}
function freshRow(rows, roll, had){               // a row whose event he has had moves to the next one down
  let i = rows.indexOf(pickRow(rows, roll));
  while (had.includes(rows[i].text)) i = (i + 1) % rows.length;
  return rows[i];
}
const atRange = (ranges, roll) => ranges.find(([, hi]) => roll <= hi)[0];
function oldWound(T, ranges, weapon, statMods, rng){   // where, then a healed mark or a lasting hurt
  const loc = atRange(ranges, rng.randint(1, 100)), kind = pickRow(T.old_wound, rng.randint(1, 100)).kind;
  const w = { loc, weapon, kind };
  if (kind === "lasting"){
    const L = TD.locs[loc], stat = T.lasting_from[L.class === "face" ? "face" : L.zone];
    statMods[stat] -= T.lasting;
    w.stat = stat;
  }
  return w;
}
function makeCharacter(region, careerId, terms, mode, rng, sexWanted = "m"){
  const T = TD.era, career = byId(T.careers, careerId), sex = sexFor(region, careerId, sexWanted, rng), base = statsFor(T, career, mode, rng);
  const statMods = Object.fromEntries(T.characteristics.map(c => [c.id, 0])), gains = {};
  const rows = originsFor(T, sex), origin = rows[Math.floor((rng.randint(1, 100) - 1) * rows.length / 100)];
  gains[origin.gain] = (gains[origin.gain] || 0) + T.gain;
  applyMod(origin.trait, statMods, gains);
  applyMod(origin.drawback, statMods, gains);
  const events = [], old = [];
  for (let k = 0; k < terms; k++){
    const row = freshRow(career.terms, rng.randint(1, 100), events);
    for (const [skill, n] of [[career.main, k === 0 ? T.first_term : T.term_main], [career.second, T.term_second], [row.skill, T.gain]]) gains[skill] = (gains[skill] || 0) + n;
    events.push(row.text);
    if (row.wound || rng.randint(1, 100) <= career.wound) old.push(oldWound(T, TD.ranges[region][career.wound_weapon], career.wound_weapon, statMods, rng));
  }
  const reg = byId(T.regions, region), name = nameFor(reg, sex, rng), look = lookFor(reg, sex, rng);
  const [kit, weapon] = kitFor(T, career, region);
  const c = ({ name, sex, era: T.id, region, career: careerId, terms, mode, base, stat_mods: statMods, gains, origin: origin.name,
    trait: origin.trait.text, drawback: origin.drawback.text, events, old, age: T.age.start + T.age.per_term * terms, kit, weapon, look, aged_to: T.age.start });
  agSteps(c, rng);                                 // the years of his terms: decline, maturity, wear
  finishChar(c);
  if (TD.hazards) c.swim = hzSwimAbility(T.id, c.skills.seamanship || 0, rng.randint(1, 100));   // whether he can swim (the last of the dice)
  return c;
}
/* Ageing (as gravewounds/ageing.py, data TD.ageing): each `step` years of his age, his band's
   decline (older for his Wear), a step of maturity and Wear; the Worn Out check for each term. */
const AG_DECLINE = ["str", "agi", "end", "wits"], AG_MATURE = ["pres", "wits", "nerve"];
function agRoll(rng, dice){                       // dice[0]d(dice[1])
  let n = 0;
  for (let i = 0; i < dice[0]; i++){ n += rng.randint(1, dice[1]) }
  return n;
}
function agDecline(band, wear, W, rng, ch){       // the band's losses into ch: Endurance twice, the worse, with heavy Wear
  for (const k of AG_DECLINE){
    if (!band[k]) continue;
    let n = agRoll(rng, band[k]);
    if (k === "end" && wear >= W.end_twice) n = Math.max(n, agRoll(rng, band[k]));
    ch[k] = (ch[k] || 0) - n;
  }
}
function agMature(mid, M, mat, ch){               // a step of maturity into ch, from M.from to each one's `to`, at most its cap
  if (mid < M.from) return;
  for (const k of AG_MATURE){
    if (mid >= M[k].to || (mat[k] || 0) >= M[k].cap) continue;
    mat[k] = (mat[k] || 0) + 1;
    ch[k] = (ch[k] || 0) + 1;
  }
}
const byKey = (a, b) => a.localeCompare(b);
function agSteps(c, rng){                         // [{age, changes}]: c changed in place (stat_mods, wear, matured, aged_to)
  const A = TD.ageing; if (!A) return [];
  const step = A.step ?? 4, W = A.wear, out = [];
  c.aged_to ??= c.age; c.wear ??= 0; const mat = (c.matured ||= {});
  while (c.age - c.aged_to >= step){
    const mid = c.aged_to + step / 2, eff = mid + Math.floor(c.wear / W.per) * W.add_years;
    const band = A.decline.findLast(b => eff >= b.from), ch = {};
    agDecline(band, c.wear, W, rng, ch);
    agMature(mid, A.maturity, mat, ch);
    for (const [k, v] of Object.entries(ch)) c.stat_mods[k] = (c.stat_mods[k] || 0) + v;
    c.wear += W.per_step; c.aged_to += step;
    out.push({ age: c.aged_to, changes: Object.fromEntries(Object.keys(ch).sort(byKey).map(k => [k, ch[k]])) });
  }
  return out;
}
const agAddWear = (c, hard) => { c.wear = (c.wear || 0) + hard * (TD.ageing?.wear?.hard_season ?? 1) };
function agWornOut(c, years, roll){               // {checked, threshold, roll, worn, why}: stats current
  const O = TD.ageing?.worn_out, s = c.stats, age = c.age, wear = c.wear || 0;
  const out = { checked: false, threshold: 0, roll, worn: false, why: "" };
  if (!O) return out;
  if (age >= O.end_age && Math.min(s.str, s.agi, s.end) < O.any_below) return { ...out, checked: true, worn: true, why: "broken down: too weak to serve" };
  if (age >= O.end_age && s.end < O.end_below) return { ...out, checked: true, worn: true, why: "worn out: his wind is gone" };
  if (age < O.age && wear < O.wear) return out;
  const t = Math.max(0, Math.trunc((wear * O.per_wear + Math.max(0, age - O.age) * O.per_year - (s.end - 50) / O.end_per) * years / 4));
  const worn = roll <= t;
  return { ...out, checked: true, threshold: t, worn, why: worn ? "worn out by service" : "" };
}
function finishChar(c){                           // stats, skills, attack, defence and nerve from the parts
  const T = TD.era, [lo, hi] = T.stat_range;
  c.stats = Object.fromEntries(Object.entries(c.base).map(([k, v]) => [k, Math.max(lo, Math.min(hi, v + c.stat_mods[k]))]));
  c.skills = Object.fromEntries(T.skills.map(s => [s.id, Math.max(0, Math.min(T.skill_max, Math.floor(c.stats[s.of] / s.div) + (c.gains[s.id] || 0)))]));
  c.attack = attackFor(c, c.weapon);
  c.defence = Math.max(...T.defence.map(s => c.skills[s]));
  c.nerve = c.stats.nerve;
  return c;
}
/* Experience in play (as gravewounds/experience.py, data TD.xp): End of season rolls each ticked
   skill (d100 over it rises by the gain die) and counts the days served toward a term. */
const xpTermDays = () => TD.era.age.per_term * ((TD.xp || {}).days_a_year || 365);
function xpSeason(c, ticks, served, rng){         // {rolls: [{skill, roll, was, gain}], terms, served}: c changed in place
  const T = TD.era, [lo, hi] = (TD.xp || {}).gain || [1, 3], want = new Set(ticks), rolls = [];
  for (const s of T.skills.map(x => x.id).filter(id => want.has(id))){
    const was = c.skills[s], roll = rng.randint(1, 100);
    const gain = roll > was && was < T.skill_max ? rng.randint(lo, hi) : 0;
    if (gain){ c.gains[s] = (c.gains[s] || 0) + gain; finishChar(c) }
    rolls.push({ skill: s, roll, was, gain: c.skills[s] - was });
  }
  c.served = (c.served || 0) + Math.max(0, served);
  const per = xpTermDays(); let done = 0;
  while (c.served >= per){
    c.served -= per;
    const car = byId(T.careers, c.career);
    c.gains[car.main] = (c.gains[car.main] || 0) + T.term_main;
    c.gains[car.second] = (c.gains[car.second] || 0) + T.term_second;
    c.age = (c.age || 0) + T.age.per_term;
    c.xp_terms = (c.xp_terms || 0) + 1;
    done++;
  }
  if (done) finishChar(c);
  return { rolls, terms: done, served: c.served };
}
function attackFor(c, weapon){                    // his attack % with a weapon: its skill, or null
  const s = TD.era.weapon_skill[weapon];
  return s ? c.skills[s] : null;
}
function makeTeam(region, slots, mode, rng){      // one character a slot ([career, terms, sex?]: m, f or roll); the first leads
  const team = slots.map(([cid, n, sex]) => makeCharacter(region, cid, n, mode, rng, sex || "m"));
  if (team.length) team[0].leader = true;
  return team;
}

/* Followers (as gravewounds/team.py make_follower): a quality on d100, man or woman (women "roll":
   at the region's share), then a name and a look. */
function makeFollower(region, careerId, table, rng, women = "none"){
  const T = TD.era, career = byId(T.careers, careerId);
  const quality = pickRow(T.followers.quality[table], rng.randint(1, 100)).quality, q = TD.quality[quality];
  const sex = women === "roll" ? sexFor(region, careerId, "roll", rng) : "m";
  const reg = byId(T.regions, region), name = nameFor(reg, sex, rng), look = lookFor(reg, sex, rng);
  const [kit, weapon] = kitFor(T, career, region);
  return { name, sex, career: careerId, quality, attack: q.attack, defence: q.defence, nerve: q.nerve, kit, weapon, look, mounted: !!career.mounted };
}
const makeFollowers = (region, counts, table, rng, women = "none") => counts.flatMap(([cid, n]) => Array.from({ length: n }, () => makeFollower(region, cid, table, rng, women)));
function followerLine(f){                         // as team.py follower_line
  const career = byId(TD.era.careers, f.career).name.toLowerCase(), kit = TD.kits[f.kit].name.split(" (")[0].toLowerCase();
  return `${f.name}${f.sex === "f" ? " (a woman)" : ""}, ${career}, ${f.quality}: ${TD.weapons[f.weapon].short.toLowerCase()} ${f.attack}%, defence ${f.defence}%, Nerve ${f.nerve}; ${kit}`;
}

/* Money (as gravewounds/money.py): an era's coins (TD.equip.currencies), which coin each army was
   paid in (TD.equip.currency), the rows that price issued kit, and TD.money's rules. Prices are
   whole numbers of a coin's smallest unit; Days (a common soldier's day's pay) are worked out. */
const FRACS = { "1/4": "¼", "1/2": "½", "3/4": "¾", "1/3": "⅓", "2/3": "⅔" };
const gcd = (a, b) => (b ? gcd(b, a % b) : a);
const group = n => n.toLocaleString("en-US");
function fmtMoney(cur, amount){                   // £8 6s 8d, 6½d, 4 Rt 30 kr, $12.54, 75¢
  const dec = cur.decimal;
  if (dec){
    if (amount < dec.per && dec.small) return `${amount}${dec.small}`;
    const whole = Math.floor(amount / dec.per), part = amount % dec.per;
    return `${dec.sym}${group(whole)}${part ? "." + String(part).padStart(String(dec.per).length - 1, "0") : ""}${dec.suf || ""}`;
  }
  const out = []; let left = amount;
  cur.units.forEach((u, i) => {
    const n = Math.floor(left / u.of); left = left % u.of;
    const last = i === cur.units.length - 1;
    let frac = "";
    if (last && left){ const g = gcd(left, u.of), key = `${left / g}/${u.of / g}`; frac = FRACS[key] || ` ${left}/${u.of}` }
    if (n || frac){ const num = `${n ? group(n) : ""}${frac}`; out.push(u.pre ? `${u.sym}${num}` : `${num}${u.sym}`) }
  });
  return out.join(" ") || "nothing";
}
const regionCoin = region => { const c = TD.equip?.currency || {}; return c[region] ?? c.default ?? null };
function rowDays(row, region){                    // [low, high] in Days, or null where the coin has no Day
  const E = TD.equip, cid = row.in || E.currency.default, rc = region ? regionCoin(region) : null;
  let cur = E.currencies[cid];
  if (rc && E.currencies[rc].coin === cur.coin) cur = E.currencies[rc];
  if (!cur.day) return null;
  const [lo, hi] = Array.isArray(row.price) ? row.price : [row.price, row.price];
  return [lo / cur.day, hi / cur.day];
}
function linked(row, key, value, region){
  const links = typeof row[key] === "string" ? [row[key]] : row[key] || [];
  return links.includes(value) && (row.regions || [region]).includes(region);
}
function kitValue(region, kit, weapon){           // {days, unpriced}: issued kit and weapon, ranges at their middle
  let total = 0; const unpriced = [];
  for (const [key, value] of [["kit", kit], ["weapon", weapon]]){
    if (key === "kit" && value === "none") continue;
    const found = (TD.equip?.items || []).filter(r => linked(r, key, value, region)), spans = found.map(r => rowDays(r, region));
    if (!found.length || spans.some(s => s === null)){ unpriced.push(value); continue }
    total += spans.reduce((a, [lo, hi]) => a + (lo + hi) / 2, 0);
  }
  return { days: total, unpriced };
}
/* The purse (as money.py): starting Days per career term plus the ledger, what he has earned and
   spent since, as signed Days (ledgerDays and quarterText are in purse.js). */
function purseFor(region, terms, ledger){          // {days, text}: and that sum in his army's coin, halves up
  const days = (TD.money?.purse_days_per_term || 0) * terms + ledgerDays(ledger), cid = regionCoin(region), cur = cid ? TD.equip.currencies[cid] : null;
  return { days, text: cur && cur.day ? fmtMoney(cur, Math.floor(days * cur.day + 0.5)) : null };
}
function spendCheck(c, days){                     // why he can't spend that many Days, or null
  if (!days || days <= 0) return "nothing to spend";
  const have = purseFor(c.region, c.terms, c.ledger).days;
  return days > have + 1e-9 ? `his purse holds ${daysQ(have)}` : null;
}
function shopFor(region){                         // the era's price list in his Days, as money.py shop
  const E = TD.equip, out = [];
  for (const r of E?.shop || []){
    if (r.cat === "pay") continue;
    const span = rowDays(r, region); if (!span) continue;
    const cur = E.currencies[r.in || E.currency.default];
    out.push({ id: r.id, name: r.name + (r.per ? ` (${r.per})` : ""), cat: r.cat, days: (span[0] + span[1]) / 2,
      text: Array.isArray(r.price) ? `${fmtMoney(cur, r.price[0])}–${fmtMoney(cur, r.price[1])}` : fmtMoney(cur, r.price) });
  }
  const order = [...new Set(out.map(r => r.cat))].sort((a, b) => (a < b ? -1 : a > b ? 1 : 0));
  return out.sort((a, b) => (order.indexOf(a.cat) - order.indexOf(b.cat)) || (a.days - b.days) || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
}
const daysText = x => (x < 1 ? "under 1" : group(Math.round(x)));
function moneyLine(c){                            // as money.py money_line
  const v = kitValue(c.region, c.kit, c.weapon), p = purseFor(c.region, c.terms, c.ledger);
  const kit = v.unpriced.length && !v.days ? "kit not priced" : `kit worth about ${daysText(v.days)} Days${v.unpriced.length ? " (part not priced)" : ""}`;
  return `${kit[0].toUpperCase()}${kit.slice(1)}; purse ${daysQ(p.days)}${p.text ? ` (${p.text})` : ""}`;
}
/* Work (as gravewounds/jobs.py): an era's jobs (TD.jobs) and TD.money.work's rules. One skill
   check a term settles the pay, one d100 at or under the risk brings trouble, and a d10 picks it
   from the era's trouble table: the dice in that order. */
const QUARTERS = ["", "¼", "½", "¾"];
function jobsAt(place){                            // lawful first, then by pay, then by name
  const rows = (TD.jobs?.jobs || []).filter(j => !place || j.places.includes(place));
  return rows.sort((a, b) => (!!a.illegal - !!b.illegal) || (b.pay - a.pay) || (a.name < b.name ? -1 : a.name > b.name ? 1 : 0));
}
function canTake(j, c){                            // [hired, why not]
  const who = j.who ?? "any";
  if (who !== "any" && !who.includes(c.career)) return [false, "not his trade"];
  if (j.skill && (c.skills[j.skill] ?? 0) < (j.min ?? 0)) return [false, `needs ${j.skill} ${j.min}`];
  return [true, null];
}
function termDays(j, days){                        // a term's length; a contract's low end unless told
  if (days !== undefined && days !== null) return days;
  if (j.term === "contract") return Array.isArray(j.days) ? j.days[0] : (j.days ?? 1);
  return TD.money.work.terms[j.term];
}
function workTerm(j, c, rng, days){               // {check, outcome, days, earned, trouble}
  const W = TD.money.work, n = termDays(j, days);
  let check = null, outcome = "success";
  if (j.skill){
    check = rng.randint(1, 100);
    const skill = c.skills[j.skill] ?? 0;
    outcome = check <= skill ? "success" : (check >= W.fumble_from ? "fumble" : "failure");
  }
  const share = { success: W.success, failure: W.failure, fumble: 0 }[outcome];
  let trouble = null;
  if (j.risk){
    const t = rng.randint(1, 100);
    if (t <= j.risk){
      const table = TD.jobs.trouble, pick = table.length ? rng.randint(1, table.length) : null;
      trouble = { roll: t, text: pick ? table[pick - 1].text : (j.hook || "") };
    }
  }
  return { check, outcome, days: n, earned: j.pay * share * (j.lump ? 1 : n), trouble };
}
function payText(j){                               // '¾ Day a day', '1½ Days a day', '56 Days a horse'
  const q = Math.round(j.pay * 4);
  if (!q) return "unpaid";
  const whole = Math.floor(q / 4), part = q % 4;
  const num = whole && !part ? whole.toLocaleString("en-US") : `${whole || ""}${QUARTERS[part]}`;
  const days = `${num} Day${q > 4 ? "s" : ""}`;
  if (j.lump) return j.per ? `${days} ${j.per}` : `${days} for the job`;
  return `${days} a day`;
}
function termText(j){                              // 'a week', '7-21 days'
  if (j.term !== "contract") return { day: "a day", week: "a week", month: "a month" }[j.term];
  const [lo, hi] = j.days;
  return lo === hi ? `${lo} day${lo > 1 ? "s" : ""}` : `${lo}-${hi} days`;
}
const BED_PLACES = ["town", "city", "village", "road"];
function keepFor(j, region, place){                // as jobs.py keep_for: {food, bed} a day, or null where the job feeds him
  if (j.board) return null;
  const k = (TD.keep || {})[region];
  if (!k) return null;
  return { food: k.food, bed: BED_PLACES.includes(place) ? k.bed : 0 };
}
/* Replacing losses (as gravewounds/replace.py): TD.repl is the era's data/replacements file. */
const LOST_WHY = ["killed", "died of wounds", "died of disease", "taken prisoner", "deserted", "sent home"];
const replFor = (row, region) => !row.regions || !row.regions.length || row.regions.includes(region);
const replCareers = row => TD.era.careers.map(c => c.id).filter(id => (row.careers ?? "any") === "any" || row.careers.includes(id));
function replaceOptions(region, place, career, terms){   // roll first, then assigned, then hire
  const R = TD.repl || { assigned: [], hire: [] };
  const out = [{ kind: "roll", id: "roll", name: "Roll a new member", careers: [career], terms: [terms, terms], wait: null, cost: null, per_term: 0,
    what: "A new man of the same career and terms, rolled like any other." }];
  for (const kind of ["assigned", "hire"]){
    for (const r of R[kind] || []){
      if (!replFor(r, region) || (place && r.places && r.places.length && !r.places.includes(place))) continue;
      const cs = replCareers(r);
      if (!cs.length) continue;
      const t = Array.isArray(r.terms) ? r.terms : [r.terms, r.terms];
      out.push({ kind, id: r.id, name: r.name, careers: cs, terms: t, wait: kind === "assigned" ? (r.wait ?? null) : null,
        cost: kind === "hire" ? (r.cost ?? 0) : null, per_term: kind === "hire" ? (r.per_term ?? 0) : 0, what: r.what || "" });
    }
  }
  return out;
}
const pickCareer = (opt, career) => (opt.careers.includes(career) ? career : opt.careers[0]);
const hireCost = (opt, terms) => (opt.cost || 0) + (opt.per_term || 0) * Math.max(0, terms - opt.terms[0]);
function effectsFor(region){                       // the era's practice with a lost man's purse, for his army
  const E = (TD.repl && TD.repl.effects) || {};
  return { ...(E.default || { practice: "heirs", what: "" }), ...((E.regions || {})[region] || {}) };
}
function settleLost(left, survivors, practice){    // {each, gone}
  left = Math.max(0, left);
  if (practice === "share" && survivors > 0) return { each: left / survivors, gone: 0 };
  return { each: 0, gone: left };
}
