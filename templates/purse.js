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
/* Period money (as money.py fmt, coin_text, money_q): an era's coins and which army was paid in
   which (COINS, set by each page from its data: {era: {currencies, currency}}); an amount of a
   coin's smallest unit as the period wrote it; and Days in his army's coin, coin first. */
const FRACS = { "1/4": "¼", "1/2": "½", "3/4": "¾", "1/3": "⅓", "2/3": "⅔" };
const gcd = (a, b) => (b ? gcd(b, a % b) : a);
const group = n => n.toLocaleString("en-US");
const moneyPlural = sym => sym.startsWith(" ") && sym.endsWith("s") && sym.length > 3;   // ' bezants', not 's' or ' kr'
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
    if (n || frac){
      const num = `${n ? group(n) : ""}${frac}`, sym = n === 1 && !frac && moneyPlural(u.sym) ? u.sym.slice(0, -1) : u.sym;   // 1 bezant, 2 bezants
      out.push(u.pre ? `${sym}${num}` : `${num}${sym}`);
    }
  });
  return out.join(" ") || "nothing";
}
let COINS = {};
function coinOf(era, region){                      // his army's coin, where it has a Day; else null
  const E = COINS[era];
  if (!E || !E.currency) return null;
  const id = E.currency[region] ?? E.currency.default, cur = id ? E.currencies[id] : null;
  return cur && cur.day ? cur : null;
}
function coinText(days, era, region){              // '3s 6d', or null where the coin has no Day
  const cur = coinOf(era, region);
  return cur ? fmtMoney(cur, Math.floor(Math.abs(days) * cur.day + 0.5)) : null;
}
function moneyQ(days, era, region){                // '3s 6d (7 Days)', or '7 Days'
  const t = coinText(days, era, region);
  return t ? `${t} (${daysQ(days)})` : daysQ(days);
}
function markLost(pid, why){                      // the team builder takes him off the team when it next looks
  if (!pid) return;
  const all = readPurses();
  if (!all[pid] || all[pid].lost) return;
  all[pid].lost = { why };
  writePurses(all);
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
