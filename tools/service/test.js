// A season of service (templates/service.js), run with no page, against the Python.
//   python3 tools/service/parity.py [n] [seed]   (writes .cache/ and runs this with SERVICE_PARITY=1)
"use strict";
const fs = require("node:fs");
const path = require("node:path");
const assert = require("node:assert/strict");

const makeTravelRules = require("../../templates/travelrules.js");
const makeService = require("../../templates/service.js");

const CACHE = path.join(__dirname, ".cache");
const readJson = p => JSON.parse(fs.readFileSync(p, "utf8"));
if (process.env.SERVICE_PARITY !== "1" || !fs.existsSync(path.join(CACHE, "cases.json"))){
  console.error("Run it through python3 tools/service/parity.py: the cases come from the Python.");
  process.exit(1);
}
const SV = readJson(path.join(CACHE, "data.json"));
const { cases, fixed } = readJson(path.join(CACHE, "cases.json"));
const S = makeService(SV, makeTravelRules(SV.rules));

function seededD100(seed){                         // as gravewounds.disease.seeded_d100
  let state = Math.max(1, seed % 2147483647);
  return () => { state = state * 16807 % 2147483647; return state % 100 + 1 };
}
let failed = 0, passed = 0;
function check(name, fn){
  try { fn(); passed++ } catch (e){ failed++; if (failed <= 20) console.error(`FAIL ${name}\n  ${e.message.split("\n").slice(0, 12).join("\n  ")}`) }
}
for (const [k, want] of Object.entries(fixed.pct)){
  const [wid, aid, p] = k.split("/");
  check(`hit chance ${k}`, () => assert.equal(S.hitPct(S.war(wid), aid, p, null, 20), want));
}
for (const [k, want] of Object.entries(fixed.weeks)){
  const [wid, sid, aid] = k.split("/");
  check(`week ${k}`, () => assert.equal(S.actionWeek(S.war(wid), sid, aid), want));
}
for (const [wid, want] of Object.entries(fixed.weapons)){
  check(`weapons ${wid}`, () => assert.deepEqual(want.map((_, i) => S.weaponFor(S.war(wid), i + 1)), want));
}
for (const [k, want] of Object.entries(fixed.fights)){
  const [wid, key, seed] = k.split("/"), W = S.war(wid);
  if (want === null) continue;
  const [st, fid] = key[0] === "=" ? [Object.keys(W.states)[0], key.slice(1)] : [key, null];
  check(`small fight ${k}`, () => assert.deepEqual(S.smallFight(W, st, seededD100(+seed), fid), want));
}
cases.forEach((c, i) => check(`season ${i} (${c.war} ${c.season})`, () => {
  const men = c.men.map(m => ({ ...m, endurance: m.endurance ?? undefined }));
  assert.deepEqual(S.serve(c.war, c.season, men, c.rolled, seededD100(c.dice)), c.want);
}));
console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
