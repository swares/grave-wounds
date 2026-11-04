// Handing the game to the next GM (templates/campaign.js), with no browser: the GM-only notes sealed
// with the GMs' passphrase and read back, and the handover file's marks.
//   node tools/campaign/handover-test.mjs
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const C = createRequire(import.meta.url)("../../templates/campaign.js");

let failed = 0, passed = 0;
async function check(name, fn){
  try { await fn(); passed++ } catch (e){ failed++; console.error(`FAIL ${name}\n  ${e.message.split("\n").slice(0, 6).join("\n  ")}`) }
}
const PASS = "oak and ash", SALT = "AAAAAAAAAAAAAAAAAAAAAA==", SECRET = "The ambush is at the ford";
const log = [
  { n: 1, round: 1, type: "note", vis: "public", data: { phase: "march", text: "On to the march" } },
  { n: 2, round: 2, type: "note", vis: [], data: { phase: "march", text: SECRET } },
  { n: 3, round: 2, type: "note", vis: ["player:a"], data: { phase: "march", text: "Will hears of it" } },
];

await check("GM-only notes sealed, and read back with the passphrase and not without it", async () => {
  const s = await C.sealLog(log, PASS, SALT);
  assert.equal(C.sealed(s), 1);
  assert.equal(s[0].data.text, "On to the march");
  assert.equal(s[2].data.text, "Will hears of it");
  assert.ok(!JSON.stringify(s).includes("ambush"));
  assert.equal(s[1].data.phase, "march");
  assert.deepEqual(await C.unsealLog(s, PASS, SALT), log);
  await assert.rejects(C.unsealLog(s, "wrong", SALT), /passphrase/);
  assert.deepEqual(await C.sealLog(s, PASS, SALT), s);   // sealed once only
});

await check("the handover file: a save file, marked, the notes sealed, the old console's mark left out", async () => {
  const rec = { name: "Towton", phase: "march", log, seen: {}, handedTo: { to: "Ann" } };
  const raw = { "gravewounds-team-builder": "{}", "gravewounds-narrator": "{\"key\":\"sk-secret\"}", [C.RECORD]: JSON.stringify(rec) };
  const f = await C.handoverFile(raw, "Towton", { from: "Scott", to: "Ann", note: "The ford", day: 2 }, PASS);
  const keys = C.checkFile(structuredClone(f));
  const r = JSON.parse(keys[C.RECORD]);
  assert.deepEqual([r.handover.from, r.handover.to, r.handover.day, f.handover.note], ["Scott", "Ann", 2, "The ford"]);
  assert.equal(r.handedTo, undefined);
  assert.equal(C.sealed(r.log), 1);
  assert.ok(!keys[C.RECORD].includes("ambush"));
  assert.ok(!("gravewounds-narrator" in keys));
  assert.equal((await C.unsealLog(r.log, PASS, r.seal.salt))[1].data.text, SECRET);
  await assert.rejects(C.handoverFile(raw, "Towton", { to: "Ann" }, ""), /passphrase/);
});

console.log(`${passed} passed, ${failed} failed`);
process.exitCode = failed ? 1 : 0;
