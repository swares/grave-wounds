// The room Worker (worker/rooms.js), its own code with an in-memory Durable Object namespace
// (tools/net/fakerooms.mjs) in place of Cloudflare's.
//   node tools/net/roomscheck.mjs
//   ROOMS_LIVE=1 node tools/net/roomscheck.mjs   the same against the Worker run by wrangler dev (port 8787)
//     (wrangler dev in worker/, Cloudflare's own local runtime); the alarm's check is skipped there
import assert from "node:assert/strict";
import worker from "../../worker/rooms.js";
import { makeEnv } from "./fakerooms.mjs";

let failed = 0, passed = 0;
async function check(name, fn){
  try { await fn(); passed++ } catch (e){ failed++; console.error(`FAIL ${name}\n  ${e.message.split("\n").slice(0, 6).join("\n  ")}`) }
}
const SITE = "https://swares.github.io";
const LIVE = process.env.ROOMS_LIVE === "1" ? "http://127.0.0.1:8787" : null;   // the Worker on this computer (wrangler dev, its own port)
function call(env, method, path, { body, key, origin = SITE } = {}){
  const headers = { Origin: origin };
  if (key) headers["X-Room-Key"] = key;
  if (body !== undefined) headers["Content-Type"] = "application/json";
  const init = { method, headers, body: body === undefined ? undefined : JSON.stringify(body) };
  if (LIVE) return fetch(new URL(path, LIVE), init);
  return worker.fetch(new Request(`https://rooms.example${path}`, init), env);
}
async function newRoom(env){
  const r = await call(env, "POST", "/rooms");
  assert.equal(r.status, 201);
  return r.json();
}

await check("a new room has a code to say aloud and a key for the host", async () => {
  const env = makeEnv(), { code, key } = await newRoom(env);
  assert.match(code, /^[A-Z]+-[A-Z]+-\d{2}$/);
  assert.match(key, /^[0-9a-f]{32}$/);
});
await check("the host's invitation reaches the player; his reply reaches the host", async () => {
  const env = makeEnv(), { code, key } = await newRoom(env);
  assert.equal((await call(env, "GET", `/rooms/${code}/invite?after=0`)).status, 204, "nothing yet");
  const put = await call(env, "PUT", `/rooms/${code}/invite`, { key, body: { data: "INVITE-1" } });
  assert.deepEqual(await put.json(), { v: 1 });
  const got = await call(env, "GET", `/rooms/${code.toLowerCase()}/invite?after=0`);   // typed in small letters: the same room
  assert.deepEqual(await got.json(), { v: 1, data: "INVITE-1" });
  assert.equal((await call(env, "GET", `/rooms/${code}/reply?v=1`, { key })).status, 204, "no reply yet");
  assert.equal((await call(env, "PUT", `/rooms/${code}/reply`, { body: { v: 1, data: "REPLY-1" } })).status, 200);
  assert.deepEqual(await (await call(env, "GET", `/rooms/${code}/reply?v=1`, { key })).json(), { data: "REPLY-1" });
});
await check("only the host may write the invitation or read the reply", async () => {
  const env = makeEnv(), { code, key } = await newRoom(env);
  assert.equal((await call(env, "PUT", `/rooms/${code}/invite`, { body: { data: "X" } })).status, 403);
  assert.equal((await call(env, "PUT", `/rooms/${code}/invite`, { key: "0".repeat(32), body: { data: "X" } })).status, 403);
  await call(env, "PUT", `/rooms/${code}/invite`, { key, body: { data: "I" } });
  await call(env, "PUT", `/rooms/${code}/reply`, { body: { v: 1, data: "R" } });
  assert.equal((await call(env, "GET", `/rooms/${code}/reply?v=1`)).status, 403);
});
await check("an invitation is answered once; a reply to an old one is refused", async () => {
  const env = makeEnv(), { code, key } = await newRoom(env);
  await call(env, "PUT", `/rooms/${code}/invite`, { key, body: { data: "I1" } });
  assert.equal((await call(env, "PUT", `/rooms/${code}/reply`, { body: { v: 1, data: "R1" } })).status, 200);
  assert.equal((await call(env, "PUT", `/rooms/${code}/reply`, { body: { v: 1, data: "SOMEONE ELSE" } })).status, 409);
  assert.deepEqual(await (await call(env, "GET", `/rooms/${code}/reply?v=1`, { key })).json(), { data: "R1" });
  await call(env, "PUT", `/rooms/${code}/invite`, { key, body: { data: "I2" } });   // invited again (he was lost): a new version
  assert.equal((await call(env, "PUT", `/rooms/${code}/reply`, { body: { v: 1, data: "LATE" } })).status, 409);
  assert.equal((await call(env, "GET", `/rooms/${code}/invite?after=1`)).status, 200, "a player who had version 1 sees there is a newer one");
  assert.equal((await call(env, "GET", `/rooms/${code}/invite?after=2`)).status, 204);
});
await check("a code not made, a bad path, a bad body or one too big is refused", async () => {
  const env = makeEnv(), { code, key } = await newRoom(env);
  assert.equal((await call(env, "GET", "/rooms/WOLF-OAK-99/invite?after=0")).status, code === "WOLF-OAK-99" ? 204 : 404);
  assert.equal((await call(env, "GET", "/rooms/not a code/invite")).status, 404);
  assert.equal((await call(env, "GET", "/other")).status, 404);
  assert.equal((await call(env, "PUT", `/rooms/${code}/invite`, { key, body: { nope: 1 } })).status, 400);
  assert.equal((await call(env, "PUT", `/rooms/${code}/invite`, { key, body: { data: "x".repeat(20000) } })).status, 400);
  assert.equal((await call(env, "PUT", `/rooms/${code}/reply`, { body: { v: "1", data: "R" } })).status, 400);
});
const REMOTE = !!LIVE;
await check("only the site's pages (and local ones) may call it", async () => {
  const env = makeEnv();
  assert.equal((await call(env, "POST", "/rooms", { origin: "https://evil.example" })).status, 403);
  const ok = await call(env, "POST", "/rooms", { origin: "http://127.0.0.1:8123" });
  assert.equal(ok.status, 201);
  assert.equal(ok.headers.get("Access-Control-Allow-Origin"), "http://127.0.0.1:8123");
  const pre = await call(env, "OPTIONS", "/rooms");
  assert.equal(pre.status, 204);
  assert.match(pre.headers.get("Access-Control-Allow-Headers"), /X-Room-Key/);
  if (REMOTE) return;                                          // its own settings are the deployed ones
  const other = makeEnv({ ALLOWED_ORIGINS: "https://mine.example, https://swares.github.io" });
  assert.equal((await call(other, "POST", "/rooms", { origin: "https://mine.example" })).status, 201);
});
await check("a room is forgotten when its time is up, and its code can be made again", async () => {
  if (REMOTE) return;
  const env = makeEnv({ ROOM_HOURS: "1" }), { code, key } = await newRoom(env);
  await call(env, "PUT", `/rooms/${code}/invite`, { key, body: { data: "I" } });
  const at = env.rooms.get(code).state.storage.alarmAt;
  assert.ok(at > Date.now() + 3500e3 && at <= Date.now() + 3600e3, "an hour after the last write");
  await env.runAlarms(at);
  assert.equal((await call(env, "GET", `/rooms/${code}/invite?after=0`)).status, 404);
  assert.equal((await env.ROOMS.get(code).fetch(new Request("https://room/create", { method: "POST" }))).status, 201);
});
await check("two rooms never share a code", async () => {
  const env = makeEnv(), made = await Promise.all(Array.from({ length: 300 }, () => newRoom(env)));
  assert.equal(new Set(made.map(r => r.code)).size, 300);
});

console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
