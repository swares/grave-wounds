// The network layer's codes and pieces (templates/net.js), with no browser: the WebRTC part needs one
// and is tried in the two-page test (tools/net/twopages.py).
//   node tools/net/test.js
"use strict";
const assert = require("node:assert/strict");
const NET = require("../../templates/net.js");

let failed = 0, passed = 0;
async function check(name, fn){
  try { await fn(); passed++ } catch (e){ failed++; console.error(`FAIL ${name}\n  ${e.message.split("\n").slice(0, 6).join("\n  ")}`) }
}
const SDP = "v=0\r\no=- 4611731400430051336 2 IN IP4 127.0.0.1\r\ns=-\r\nt=0 0\r\na=group:BUNDLE 0\r\n" + "a=candidate:1 1 udp 2122260223 192.168.1.20 54321 typ host\r\n".repeat(6);

(async () => {
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
    const got = ps.map(feed);
    assert.ok(got.slice(0, -1).every(m => m === null));
    assert.deepEqual(got.at(-1), msg);
  });
  await check("pieces of two messages mixed, and out of order, still make two messages", () => {
    const a = NET.pieces({ who: "a", pad: "a".repeat(250) }, 100), b = NET.pieces({ who: "b", pad: "b".repeat(250) }, 100), feed = NET.joiner();
    const mixed = [a[2], b[0], a[0], b[2], b[1], a[1], ...a.slice(3), ...b.slice(3)];
    const whole = mixed.map(feed).filter(Boolean);
    assert.deepEqual(whole.map(m => m.who).sort(), ["a", "b"]);
  });
  await check("a short message is one piece, under the channel's limit", () => {
    const ps = NET.pieces({ t: "next" });
    assert.equal(ps.length, 1);
    assert.ok(ps[0].length < NET.PIECE + 200);
  });
  console.log(`${passed} passed, ${failed} failed`);
  process.exit(failed ? 1 : 0);
})();
