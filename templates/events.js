/* Events on the march and in camp (as gravewounds/events.py): EV is data/events.yaml, DZ the
   disease data. The dice are taken in the same order: each man's desertion roll, then
   straggling, then injury (its step and fever day as each is found), then horses; then the
   incident chance, the row and the men it costs. rng() gives 1-100. */
const EV_HORSE_TYPES = ["mounted", "wagons"];
const evEraOf = (EV, period, force) => force.era || (EV.periods || {})[period || ""] || null;
const evActivity = (marched, withdrawing) => (withdrawing ? "withdraw" : marched > 0 ? "march" : "camp");
const evD1e6 = rng => (rng() - 1) * 10000 + (rng() - 1) * 100 + rng();
const evPick = (lo, hi, rng) => lo + (rng() - 1) % (hi - lo + 1);
const evThreshold = rate => Math.floor(rate * 1000000 + 0.5);
function evInjuryCase(EV, DZ, rng){               // his step on d100, and a wound-fever day as any wound's
  const roll = rng(), stepName = EV.injury.find(r => roll <= r.to).step, [lo, hi] = DZ.wounds.fever_after;
  return { d: "wound", inc: 0, step: DZ.steps.indexOf(stepName), peak: 0, shown: 0, chronic: false, inf: "low", fever: evPick(lo, hi, rng), injury: true };
}
function evDay(EV, DZ, era, ftype, men, act, rng, horses = true){
  const E = EV.eras[era], R = E.rates;
  const out = { desert: 0, straggle: 0, injury: 0, cases: [], horses: 0, incident: null, incident_lost: 0, fatigue: 0 };
  let left = men;
  for (const kind of ["desert", "straggle"]){
    const t = evThreshold(((R[kind] || {})[act]) || 0);
    let n = 0;
    if (t) for (let i = 0; i < left; i++) if (evD1e6(rng) <= t) n++;
    out[kind] = n; left -= n;
  }
  const ti = evThreshold(((R.injury || {})[act]) || 0);
  if (ti) for (let i = 0; i < left; i++) if (evD1e6(rng) <= ti){ out.injury++; out.cases.push(evInjuryCase(EV, DZ, rng)) }
  if (horses && EV_HORSE_TYPES.includes(ftype) && R.horses){
    const th = evThreshold(R.horses[act] || 0);
    if (th) for (let i = 0; i < left; i++) if (evD1e6(rng) <= th) out.horses++;
  }
  left -= out.injury;
  if (E.incident && rng() <= E.incident){
    const roll = rng(), row = E.incidents.find(r => roll <= r.to);
    const fits = (!row.types || !row.types.length || row.types.includes(ftype)) && men >= (row.min_men ?? 0) && men <= (row.max_men ?? 1e9);
    if (fits){
      out.incident = row;
      if (row.lose) out.incident_lost = Math.min(Math.max(0, left), evPick(row.lose[0], row.lose[1], rng));
      out.fatigue = row.fatigue || 0;
    }
  }
  return out;
}
function evDayText(r){                            // the night's events in words, for the force's log
  const bits = [];
  for (const [kind, word] of [["desert", "deserted"], ["straggle", "fell out and were lost"], ["injury", "injured"]]) if (r[kind]) bits.push(`${r[kind]} ${word}`);
  if (r.horses) bits.push(`${r.horses} horse${r.horses !== 1 ? "s" : ""} lost`);
  if (r.incident && !r.incident.quiet) bits.push(r.incident.text.replace(/\.$/, "") + (r.incident_lost ? ` (${r.incident_lost} lost)` : ""));
  return bits;
}
