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
function makeCharacter(region, careerId, terms, mode, rng){
  const T = TD.era, career = byId(T.careers, careerId), base = statsFor(T, career, mode, rng);
  const statMods = Object.fromEntries(T.characteristics.map(c => [c.id, 0])), gains = {};
  const origin = T.origins[Math.floor((rng.randint(1, 100) - 1) * T.origins.length / 100)];
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
  const reg = byId(T.regions, region), beards = ["", "moustache", "beard", "stubble"];
  const name = `${reg.names[rng.randint(1, reg.names.length) - 1]} ${reg.bynames[rng.randint(1, reg.bynames.length) - 1]}`;
  const look = { colour: reg.colours[rng.randint(1, reg.colours.length) - 1], beard: beards[rng.randint(1, 4) - 1] };
  const [kit, weapon] = kitFor(T, career, region);
  return finishChar({ name, era: T.id, region, career: careerId, terms, mode, base, stat_mods: statMods, gains, origin: origin.name,
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
function makeTeam(region, slots, mode, rng){      // one character a slot ([career, terms]); the first leads
  const team = slots.map(([cid, n]) => makeCharacter(region, cid, n, mode, rng));
  if (team.length) team[0].leader = true;
  return team;
}
