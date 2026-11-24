// What the travel day's tests share (day.js, commander.js): the browser the travel page runs in,
// with no page, the data parity.py writes, a check that counts, and a fresh day on seeded dice.
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");

const makeTravelRules = require("../../templates/travelrules.js");
const makeTravelDay = require("../../templates/travelday.js");

const CACHE = path.join(__dirname, ".cache");
if (process.env.TRAVEL_PARITY !== "1" || !fs.existsSync(path.join(CACHE, "shared.js"))){
  console.error("Run it through python3 tools/travel/parity.py: it writes the data and the shared files.");
  process.exit(1);
}
const DATA = JSON.parse(fs.readFileSync(path.join(CACHE, "data.json"), "utf8"));

// The browser the travel page runs in, as much as the day needs: storage, crypto's dice, and the
// shared rule files with the page's own names they read (as travel.html sets them).
const mem = new Map();
const store = {
  getItem: k => (mem.has(k) ? mem.get(k) : null), setItem: (k, v) => { mem.set(k, String(v)) }, removeItem: k => { mem.delete(k) },
  key: i => [...mem.keys()][i] ?? null, get length(){ return mem.size }, clear: () => mem.clear(),
};
Object.defineProperty(globalThis, "localStorage", { value: store, configurable: true });
let cryptoState = 1;
globalThis.crypto.getRandomValues = a => { for (let i = 0; i < a.length; i++){ cryptoState = (cryptoState * 48271) % 2147483647; a[i] = cryptoState } return a };
globalThis.TD = { checks: DATA.checks, training: DATA.training, loads: DATA.loads, weights: DATA.weights, supplies: DATA.supplies, kit: DATA.kit,
  stress: DATA.stress, hazards: DATA.hazards, languages: DATA.languages, era: { id: null, skills: [] } };
Object.assign(globalThis, require(path.join(CACHE, "shared.js")));
Object.assign(COINS, DATA.coins || {});
const RULES = makeTravelRules(DATA, { partyOf, hzCurrentBand, hzFordWater, spMedicalShort });
Object.assign(globalThis, { WK: DATA.works, CAMP_HEX_M: DATA.battle_hex_m, CG: DATA.ground,
  NEIGHBOURS: RULES.NEIGHBOURS, hexDistance: RULES.hexDistance, hkey: RULES.hkey, edgeKey: RULES.edgeKey });

const tally = { failed: 0, passed: 0 };
function check(name, fn){
  try { fn(); tally.passed++ } catch (e){ tally.failed++; console.error(`FAIL ${name}\n  ${String(e.stack || e).split("\n").slice(0, 8).join("\n  ")}`) }
}
const parkMiller = seed => { let s = Math.max(1, seed % 2147483647); return () => { s = (s * 16807) % 2147483647; return 1 + (s % 100) } };

function fresh(seed){                               // an empty browser and a new day on these dice
  store.clear();
  cryptoState = seed * 7919 + 1;
  return { D: makeTravelDay(DATA, RULES, { roll100: parkMiller(seed) }), seed };
}
function snapshot(D){                               // all a game is: the travel state and what the day keeps beside it
  D.save();
  return JSON.stringify(Object.fromEntries([...mem.entries()].sort(([a], [b]) => (a < b ? -1 : 1))));
}
module.exports = { fs, path, assert, makeTravelRules, makeTravelDay, DATA, RULES, mem, store, tally, check, parkMiller, fresh, snapshot };
