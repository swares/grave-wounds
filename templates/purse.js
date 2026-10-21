/* Purses (as gravewounds/money.py): one saved account for each character, shared by the team
   builder, the wound roller and the travel map, keyed by his purse id (pid). His purse is his
   starting Days (money.yaml, per career term) plus his ledger of what he has earned and spent
   since, as signed Days. A man his army does not feed pays his keep from it (pay_keep). Browser
   storage can be off or empty: every read and write is guarded, and a page works without it. */
const PURSES_KEY = "gravewounds-purses";          // {pid: {name, era, region, terms, start, ledger: [{days, what}]}}
function readPurses(){ try{ return JSON.parse(localStorage.getItem(PURSES_KEY) || "{}") || {} }catch(e){ return {} } }
function writePurses(all){ try{ localStorage.setItem(PURSES_KEY, JSON.stringify(all)) }catch(e){ /* storage off: each page keeps its own copy */ } }
const newPid = () => Array.from(crypto.getRandomValues(new Uint32Array(2)), x => x.toString(36)).join("");
const ledgerDays = ledger => (ledger || []).reduce((a, e) => a + e.days, 0);
const purseLeft = p => (p ? p.start + ledgerDays(p.ledger) : 0);
const PURSE_Q = ["", "¼", "½", "¾"];
function quarterText(x){                          // Days to the nearest quarter, halves up: '104½', '1,200', '¾', '0'
  const q = Math.floor(Math.max(x, 0) * 4 + 0.5), whole = Math.floor(q / 4), part = q % 4;
  return whole ? `${whole.toLocaleString("en-US")}${PURSE_Q[part]}` : (PURSE_Q[part] || "0");
}
function daysQ(x){                               // '¾ Day', '1 Day', '1¼ Days', '0 Days'
  const q = Math.floor(Math.max(x, 0) * 4 + 0.5);
  return `${quarterText(x)} Day${q > 0 && q <= 4 ? "" : "s"}`;
}
function payKeep(have, days, food, bed){          // {paid, hungry, rough}: each day's food before its bed
  let paid = 0, hungry = 0, rough = 0;
  for (let i = 0; i < days; i++){
    if (have + 1e-9 >= food){ have -= food; paid += food } else hungry++;
    if (bed){
      if (have + 1e-9 >= bed){ have -= bed; paid += bed } else rough++;
    }
  }
  return { paid, hungry, rough };
}
