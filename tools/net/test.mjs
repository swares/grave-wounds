// The network layer's codes and pieces (templates/net.js), with no browser: the WebRTC part needs one
// and is tried in the two-page test (tools/net/twopages.py).
//   node tools/net/test.mjs
import assert from "node:assert/strict";
import { createRequire } from "node:module";
const NET = createRequire(import.meta.url)("../../templates/net.js");   // the page's own file: a script, not a module

let failed = 0, passed = 0;
async function check(name, fn){
  try { await fn(); passed++ } catch (e){ failed++; console.error(`FAIL ${name}\n  ${e.message.split("\n").slice(0, 6).join("\n  ")}`) }
}
const SDP = "v=0\r\no=- 4611731400430051336 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\n" + "a=candidate:1 1 udp 2122260223 192.168.1.20 54321 typ host\r\n".repeat(6);

await check("a code comes back as it went", async () => {
  const obj = { kind: "invite", seat: "side:Yorkists", sdp: SDP };
  const code = await NET.packCode(obj);
  assert.match(code, /^[\w-]+$/, "safe in a link");
  assert.ok(code.length < JSON.stringify(obj).length, "shorter than the description");
  assert.deepEqual(await NET.unpackCode(code), obj);
});
await check("a whole link, or a code with spaces and line breaks, is read as its code", async () => {
  const code = await NET.packCode({ kind: "reply", sdp: SDP });
  assert.equal((await NET.unpackCode(`https://swares.github.io/grave-wounds/dist/roller.html#join=${code}`)).kind, "reply");
  assert.equal((await NET.unpackCode(code.slice(0, 20) + "\n  " + code.slice(20))).kind, "reply");
});
await check("text that is not a code is refused", async () => {
  await assert.rejects(NET.unpackCode("hello there!"), /not a code/);
  await assert.rejects(NET.unpackCode("abcdefghijklmnop"));
});
await check("a long message is cut into pieces and put back together", () => {
  const msg = { html: "x".repeat(150000), n: 7 };
  const ps = NET.pieces(msg, 40000), feed = NET.joiner();
  assert.equal(ps.length, Math.ceil(JSON.stringify(msg).length / 40000));
  const got = ps.map(piece => feed(piece));
  assert.ok(got.slice(0, -1).every(m => m === null));
  assert.deepEqual(got.at(-1), msg);
});
await check("pieces of two messages mixed, and out of order, still make two messages", () => {
  const a = NET.pieces({ who: "a", pad: "a".repeat(250) }, 100), b = NET.pieces({ who: "b", pad: "b".repeat(250) }, 100), feed = NET.joiner();
  const mixed = [a[2], b[0], a[0], b[2], b[1], a[1], ...a.slice(3), ...b.slice(3)];
  const whole = mixed.map(piece => feed(piece)).filter(Boolean);
  assert.deepEqual(whole.map(m => m.who).sort((x, y) => x.localeCompare(y)), ["a", "b"]);
});
await check("a short message is one piece, under the channel's limit", () => {
  const ps = NET.pieces({ t: "next" });
  assert.equal(ps.length, 1);
  assert.ok(ps[0].length < NET.PIECE + 200);
});
const hexes = n => Array.from({ length: n }, (_, i) => `<polygon class="hex${i % 7 ? "" : " wood"}" data-h="${i % 30},${(i / 30) | 0}" points="1,2 3,4"/>`).join("");
await check("a changed drawing goes as its changes, and comes back the same", () => {
  let seed = 5;
  const roll = n => (seed = (seed * 16807) % 2147483647) % n;
  for (let t = 0; t < 60; t++){
    const was = `<svg>${hexes(400 + roll(50))}<g class="unit" data-x="${roll(90)}"></g></svg>`;
    const bits = was.split(/(?=<)/);
    for (let j = 0, n = roll(40); j < n; j++){               // some tags changed, dropped, put in, anywhere
      const at = roll(bits.length), what = roll(3);
      if (what === 0) bits[at] = bits[at].replace("hex", "hex reach");
      else if (what === 1) bits.splice(at, 1);
      else bits.splice(at, 0, `<circle r="${roll(9)}"/>`);
    }
    const now = bits.join("");
    const change = NET.edit(was, now);
    assert.equal(NET.apply(was, change), now, `case ${t}`);
    if (now !== was) assert.ok(JSON.stringify(change).length < now.length / 2, `case ${t}: smaller than the drawing (${JSON.stringify(change).length} of ${now.length})`);
  }
});
await check("a short panel, or one wholly redrawn, goes whole or cut, and still comes back the same", () => {
  assert.equal(NET.edit("<b>1</b>", "<b>2</b>"), "<b>2</b>");
  const was = hexes(300), now = hexes(300).replaceAll("hex", "hx");
  assert.equal(NET.apply(was, NET.edit(was, now)), now);
  assert.equal(NET.apply(was, NET.edit(was, was + "<i>x</i>")), was + "<i>x</i>");
  assert.equal(NET.apply("", NET.edit("", now)), now);
  assert.equal(NET.apply(undefined, now), now);
  assert.deepEqual(NET.apply(null, { acts: 1 }), { acts: 1 }, "an object that is not a change is itself");
});
await check("waiting in a room asks less often the longer it waits", async () => {
  assert.deepEqual([0, 119e3, 121e3, 599e3, 601e3, 36e5].map(NET.pollEvery), [1500, 1500, 5000, 5000, 20000, 20000]);
  let n = 0;
  assert.equal(await NET.poll(async () => (++n === 3 ? "here" : null), { every: () => 1 }), "here");
  assert.equal(await NET.poll(async () => null, { every: () => 1, stop: () => n++ > 5 }), null, "stopped");
  await assert.rejects(NET.poll(async () => { throw Object.assign(new Error("no such room"), { status: 404 }) }, { every: () => 1 }), /no such room/);
  let tries = 0;
  assert.equal(await NET.poll(async () => { if (++tries < 3) throw Object.assign(new Error("down"), { status: 503 }); return "up" }, { every: () => 1 }), "up", "the server failing is tried again");
});
console.log(`${passed} passed, ${failed} failed`);
process.exit(failed ? 1 : 0);
