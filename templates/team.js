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
  return finishChar({ name, sex, era: T.id, region, career: careerId, terms, mode, base, stat_mods: statMods, gains, origin: origin.name,
    trait: origin.trait.text, drawback: origin.drawback.text, events, old, age: T.age.start + T.age.per_term * terms, kit, weapon, look });
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
function purseFor(region, terms){                 // {days, text}: Days per term, and that sum in his army's coin
  const days = (TD.money?.purse_days_per_term || 0) * terms, cid = regionCoin(region), cur = cid ? TD.equip.currencies[cid] : null;
  return { days, text: cur && cur.day ? fmtMoney(cur, days * cur.day) : null };
}
const daysText = x => (x < 1 ? "under 1" : group(Math.round(x)));
function moneyLine(c){                            // as money.py money_line
  const v = kitValue(c.region, c.kit, c.weapon), p = purseFor(c.region, c.terms);
  const kit = v.unpriced.length && !v.days ? "kit not priced" : `kit worth about ${daysText(v.days)} Days${v.unpriced.length ? " (part not priced)" : ""}`;
  return `${kit[0].toUpperCase()}${kit.slice(1)}; purse ${p.days} Days${p.text ? ` (${p.text})` : ""}`;
}
