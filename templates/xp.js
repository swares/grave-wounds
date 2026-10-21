/* Experience (data/experience.yaml): the skills each character has used well since the last End
   of season, and the days he has served, kept by his purse id (pid) and shared by the team
   builder, the roller and the travel map. The team builder settles them at End of season
   (xpSeason in team.js) and puts his new sheet here (`sheet`, `stamp`) for the roller to pick up.
   Storage can be off: every read and write is guarded. */
const XP_KEY = "gravewounds-xp";                   // {pid: {ticks: {skill: why}, served: days, sheet?, stamp?}}
function readXp(){ try{ return JSON.parse(localStorage.getItem(XP_KEY) || "{}") || {} }catch(e){ return {} } }
function writeXp(all){ try{ localStorage.setItem(XP_KEY, JSON.stringify(all)) }catch(e){ /* storage off: no experience kept */ } }
const xpOf = (all, pid) => (all[pid] ||= { ticks: {}, served: 0 });
function xpTick(pid, skill, why){                  // he used this skill well: it rolls to rise at End of season
  if (!pid || !skill) return;
  const all = readXp(), x = xpOf(all, pid);
  x.ticks = x.ticks || {};
  if (!x.ticks[skill]) x.ticks[skill] = why || "used";
  writeXp(all);
}
function xpServe(pid, days){                       // days toward his next term
  if (!pid || !(days > 0)) return;
  const all = readXp(), x = xpOf(all, pid);
  x.served = (x.served || 0) + days;
  writeXp(all);
}
