/* Lethality: the GM's setting for how much the player characters (the team builder's sheeted
   men, the field map's heroes) are spared. One setting for all pages, remembered in the
   browser like US | Metric; wounds.yaml lethality holds the presets. build.py puts this file
   into each page at its LETHAL_JS marker. */
const LETHAL_KEY = "gravewounds-lethality";
const LETHALITY = /*__LETHAL_DATA__*/null;            // {default, presets: {id: {name, fate, blood, stop_bonus, stop_critical_only, desc}}}
let lethalId = LETHALITY.default;
try{ const v = localStorage.getItem(LETHAL_KEY); if (v && LETHALITY.presets[v]) lethalId = v }catch(e){ /* storage off: the default */ }
const lethalSetting = () => ({ id: lethalId, ...LETHALITY.presets[lethalId] });
// A player character's Blood pool under the setting (as gravewounds.combat.blood_pool with a preset).
const pcPool = pool => Math.floor(pool * lethalSetting().blood);
// A player character's Nerve for a stop check on a wound of this severity, or null if the
// setting spares him the check (as gravewounds.combat.pc_stop).
function pcNerve(nerve, sev){
  const L = lethalSetting();
  if (L.stop_critical_only && sev !== "critical") return null;
  return nerve + L.stop_bonus;
}
// Fate points: what he has spent this season is kept with his experience, by his purse id (the
// shared gravewounds-xp store, as xp.js), and End of season clears it. What he has left is the
// setting's fate less that, so turning the dial changes it at once.
const FATE_KEY = "gravewounds-xp";
function fateRead(){ try{ return JSON.parse(localStorage.getItem(FATE_KEY) || "{}") || {} }catch(e){ return {} } }
function fateLeft(pid){ return pid ? Math.max(0, lethalSetting().fate - ((fateRead()[pid] || {}).fate_spent || 0)) : 0 }
function fateSpend(pid, why, n = 1){             // spend n of his fate points; false if he has too few
  if (!pid || fateLeft(pid) < n) return false;
  const all = fateRead(), x = (all[pid] ||= { ticks: {}, served: 0 });
  x.fate_spent = (x.fate_spent || 0) + n;
  (x.fate_log ||= []).push(why);
  try{ localStorage.setItem(FATE_KEY, JSON.stringify(all)) }catch(e){ return false /* storage off: it cannot be kept */ }
  return true;
}
// The Gritty | Standard | Heroic switch in a page's header. onChange redraws the page.
function lethalToggle(el, onChange){
  const draw = () => {
    el.innerHTML = Object.entries(LETHALITY.presets).map(([id, p]) => `<button type="button" class="small" data-lethal="${id}" aria-pressed="${lethalId === id}" title="${p.desc} Player characters: ${p.fate} fate a season, Blood ×${p.blood}${p.stop_critical_only ? ", stop check only for critical wounds" : p.stop_bonus ? `, +${p.stop_bonus} Nerve on the stop check` : ""}.">${p.name}</button>`).join("");
  };
  el.addEventListener("click", e => {
    const b = e.target.closest("button[data-lethal]");
    if (!b || b.dataset.lethal === lethalId) return;
    lethalId = b.dataset.lethal;
    try{ localStorage.setItem(LETHAL_KEY, lethalId) }catch(err){ /* storage off: the choice lasts while the page is open */ }
    draw();
    onChange();
  });
  draw();
}
