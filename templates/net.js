/* Play over the network: the GM's roller is the host, each player's page joins it over WebRTC.

   No server: the two pages set up the connection by passing two codes by hand (copy and paste,
   or a chat). The host makes an invitation for a seat (a side); the player opens it as a link,
   his page answers with a reply code; the GM pastes the reply in; the pages then talk directly
   over a data channel. A STUN server (by default a public one) lets pages find each other across
   the internet; there is no relay (TURN), so a few strict networks will not connect.

   What crosses the channel is JSON: the host sends each seat its own screen (see the roller's
   net section), the player sends his choices. Messages are cut into pieces the channel carries.
   NET.packCode / NET.unpackCode turn a session description into a short code and back (deflated,
   then base64url). build.py puts this file into the roller at its NET_JS marker; in Node it is a
   module (tools/net/test.js tests the codes and the pieces). */
const NET = (() => {
  const PIECE = 60000;                                   // under the 256 kB a Chromium data channel message may be
  const STUN = [{ urls: "stun:stun.l.google.com:19302" }];

  const toB64url = bytes => {
    let bin = "";
    for (const b of bytes) bin += String.fromCodePoint(b);
    let out = btoa(bin).replaceAll("+", "-").replaceAll("/", "_");
    while (out.endsWith("=")) out = out.slice(0, -1);   // no padding: safe in a link
    return out;
  };
  const fromB64url = text => {
    const b64 = text.replaceAll("-", "+").replaceAll("_", "/");
    const bin = atob(b64 + "=".repeat((4 - b64.length % 4) % 4));
    return Uint8Array.from(bin, ch => ch.codePointAt(0));
  };
  async function squeeze(bytes, how){                    // deflate or inflate through the browser's own streams
    const stream = new Blob([bytes]).stream().pipeThrough(how === "in" ? new DecompressionStream("deflate-raw") : new CompressionStream("deflate-raw"));
    return new Uint8Array(await new Response(stream).arrayBuffer());
  }
  async function packCode(obj){                          // {kind, seat, sdp, ...} -> a code to copy
    return toB64url(await squeeze(new TextEncoder().encode(JSON.stringify(obj)), "out"));
  }
  async function unpackCode(code){                       // the code back, or an error saying it is not one
    const clean = String(code).trim().replace(/^.*#join=/, "").replaceAll(/\s+/g, "");
    if (!/^[\w-]+$/.test(clean)) throw new Error("That is not a code from this page.");
    return JSON.parse(new TextDecoder().decode(await squeeze(fromB64url(clean), "in")));
  }

  function pieces(msg, n = PIECE){                       // a message as JSON pieces small enough to send
    const text = JSON.stringify(msg), id = toB64url(crypto.getRandomValues(new Uint8Array(6))), count = Math.max(1, Math.ceil(text.length / n));
    return Array.from({ length: count }, (_, k) => JSON.stringify({ id, k, of: count, part: text.slice(k * n, (k + 1) * n) }));
  }
  function joiner(){                                     // put pieces back together: feed(piece) -> the whole message, or null
    const open = new Map();
    return piece => {
      const p = JSON.parse(piece);
      if (!open.has(p.id)) open.set(p.id, []);
      const got = open.get(p.id);
      got[p.k] = p.part;
      if (got.filter(x => x !== undefined).length < p.of) return null;
      open.delete(p.id);
      return JSON.parse(got.join(""));
    };
  }

  function gathered(pc, wait = 4000){                    // the description once the network addresses are found (or after `wait`)
    return new Promise(done => {
      if (pc.iceGatheringState === "complete") return done(pc.localDescription);
      const finish = () => { clearTimeout(t); done(pc.localDescription) };
      const t = setTimeout(finish, wait);
      pc.addEventListener("icegatheringstatechange", () => { if (pc.iceGatheringState === "complete") finish() });
    });
  }
  function wire(ch, onMessage, onState){                 // a data channel's messages, whole, and its state
    const feed = joiner();
    ch.onmessage = e => { const m = feed(e.data); if (m) onMessage(m) };
    ch.onopen = () => onState("open");
    ch.onclose = () => onState("closed");
    return msg => { if (ch.readyState === "open") pieces(msg).forEach(p => ch.send(p)) };
  }

  // The host's end of one player's connection: invite(seat) -> link code; accept(reply) connects.
  function hostPeer({ seat, stun = true, onMessage, onState }){
    const pc = new RTCPeerConnection({ iceServers: stun ? STUN : [] });
    const ch = pc.createDataChannel("gravewounds", { ordered: true });
    const send = wire(ch, onMessage, onState);
    pc.onconnectionstatechange = () => { if (["failed", "disconnected"].includes(pc.connectionState)) onState(pc.connectionState) };
    return {
      seat, send, close: () => pc.close(),
      async invite(extra = {}){
        await pc.setLocalDescription(await pc.createOffer());
        const d = await gathered(pc);
        return packCode({ kind: "invite", seat, sdp: d.sdp, ...extra });
      },
      async accept(replyCode){
        const r = await unpackCode(replyCode);
        if (r.kind !== "reply") throw new Error("That is not a player's reply code.");
        await pc.setRemoteDescription({ type: "answer", sdp: r.sdp });
      },
    };
  }
  // The player's end: from the invitation, a reply code for the GM; then messages both ways.
  async function guestPeer({ invite, stun = true, onMessage, onState }){
    if (invite.kind !== "invite") throw new Error("That is not an invitation.");
    const pc = new RTCPeerConnection({ iceServers: stun ? STUN : [] });
    let send = () => {};
    pc.ondatachannel = e => { send = wire(e.channel, onMessage, onState) };
    pc.onconnectionstatechange = () => { if (["failed", "disconnected"].includes(pc.connectionState)) onState(pc.connectionState) };
    await pc.setRemoteDescription({ type: "offer", sdp: invite.sdp });
    await pc.setLocalDescription(await pc.createAnswer());
    const d = await gathered(pc);
    return { reply: await packCode({ kind: "reply", seat: invite.seat, sdp: d.sdp }), send: msg => send(msg), close: () => pc.close() };
  }

  return { packCode, unpackCode, pieces, joiner, hostPeer, guestPeer, PIECE };
})();

if (typeof module !== "undefined") module.exports = NET;   // Node (the tests); the page has no `module`
