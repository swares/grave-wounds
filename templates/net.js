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
   module (tools/net/test.mjs tests the codes, the pieces and the changes). */
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

  // The connection's ups and downs: lost (disconnected, failed) is said; a connection that comes back by
  // itself after a short drop (the network blinked) is said to be open again, while its channel is.
  function watch(pc, onState, channelOpen){
    let lost = false;
    pc.onconnectionstatechange = () => {
      const s = pc.connectionState;
      if (s === "failed" || s === "disconnected"){ lost = true; onState(s) }
      else if (s === "connected" && lost && channelOpen()){ lost = false; onState("open") }
    };
  }

  // The host's end of one player's connection: invite(seat) -> link code; accept(reply) connects.
  function hostPeer({ seat, stun = true, onMessage, onState }){
    const pc = new RTCPeerConnection({ iceServers: stun ? STUN : [] });
    const ch = pc.createDataChannel("gravewounds", { ordered: true });
    const send = wire(ch, onMessage, onState);
    watch(pc, onState, () => ch.readyState === "open");
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
    let send = () => {}, chan = null;
    pc.ondatachannel = e => { chan = e.channel; send = wire(chan, onMessage, onState) };
    watch(pc, onState, () => chan?.readyState === "open");
    await pc.setRemoteDescription({ type: "offer", sdp: invite.sdp });
    await pc.setLocalDescription(await pc.createAnswer());
    const d = await gathered(pc);
    return { reply: await packCode({ kind: "reply", seat: invite.seat, sdp: d.sdp }), send: msg => send(msg), close: () => pc.close() };
  }

  // A drawing that changed, sent as its changes: the HTML cut into tags, the tags that stayed the same
  // kept by count (Myers' shortest edit), the rest sent. edit(was, now) → now itself (short or not text),
  // { cut: [a, b, middle] } (all but the a characters at the start and b at the end, when that is
  // shorter or the changes are too many to look for) or { ops: [...] }: n > 0 keeps n tags, n < 0 drops
  // n, a string is put in. apply(was, change) is the other end's half: the new drawing.
  const SHORT = 2000, MOST_EDITS = 800;
  const tags = text => text.split(/(?=<)/);
  function shortestEdit(A, B){                           // Myers: the fewest drops and puts that make A into B, or null past MOST_EDITS
    const N = A.length, M = B.length, max = Math.min(N + M, MOST_EDITS), off = max + 1, trace = [];
    let V = new Int32Array(2 * max + 3);
    for (let d = 0; d <= max; d++){
      trace.push(V.slice());
      for (let k = -d; k <= d; k += 2){
        let x = (k === -d || (k !== d && V[off + k - 1] < V[off + k + 1])) ? V[off + k + 1] : V[off + k - 1] + 1, y = x - k;
        while (x < N && y < M && A[x] === B[y]){ x++; y++ }
        V[off + k] = x;
        if (x >= N && y >= M) return backtrack(trace, d, N, M, off, B);
      }
    }
    return null;
  }
  function backtrack(trace, D, N, M, off, B){
    const out = [];                                      // from the end: ["k"], ["d"], ["i", tag]
    let x = N, y = M;
    for (let d = D; d > 0; d--){
      const V = trace[d], k = x - y;
      const pk = (k === -d || (k !== d && V[off + k - 1] < V[off + k + 1])) ? k + 1 : k - 1;
      const px = V[off + pk], py = px - pk;
      while (x > px && y > py){ out.push(["k"]); x--; y-- }
      if (pk === k + 1) out.push(["i", B[py]]); else out.push(["d"]);
      x = px; y = py;
    }
    while (x > 0){ out.push(["k"]); x-- }
    return out.reverse();
  }
  function compact(steps){                               // the steps as the message carries them
    const ops = [];
    for (const [s, tag] of steps){
      const last = ops.length - 1;
      if (s === "i"){ if (typeof ops[last] === "string") ops[last] += tag; else ops.push(tag) }
      else {
        const n = s === "k" ? 1 : -1;
        if (typeof ops[last] === "number" && Math.sign(ops[last]) === n) ops[last] += n; else ops.push(n);
      }
    }
    return ops;
  }
  function edit(was, now){
    if (typeof was !== "string" || typeof now !== "string" || now.length < SHORT) return now;
    let a = 0, b = 0;
    const most = Math.min(was.length, now.length);
    while (a < most && was[a] === now[a]) a++;
    while (b < most - a && was[was.length - 1 - b] === now[now.length - 1 - b]) b++;
    const cut = { cut: [a, b, now.slice(a, now.length - b)] };
    if (cut.cut[2].length < 200) return cut;
    const steps = shortestEdit(tags(was), tags(now));
    if (!steps) return cut;
    const ops = { ops: compact(steps) };
    return JSON.stringify(ops).length < JSON.stringify(cut).length ? ops : cut;
  }
  function apply(was, change){
    if (!change || typeof change !== "object" || !(Array.isArray(change.cut) || Array.isArray(change.ops))) return change;   // anything else is itself
    const old = String(was ?? "");
    if (Array.isArray(change.cut)){ const [a, b, mid] = change.cut; return old.slice(0, a) + mid + old.slice(old.length - b) }
    const from = tags(old), out = [];
    let i = 0;
    for (const op of change.ops){
      if (typeof op === "string") out.push(op);
      else if (op > 0){ out.push(...from.slice(i, i + op)); i += op }
      else i -= op;
    }
    return out.join("");
  }

  // A seat's screen, as panels of HTML: the first whole, then each later one as only what changed.
  // screenPart(was, now, always) -> the message to send (now itself when there was none before; a
  // part {part: true, ...} with the `always` fields and the changed panels as edits), or null when
  // nothing at all changed. merge(screen, m) is the other end's half: the whole screen again.
  function screenPart(was, now, always = []){
    if (!was) return now;
    const part = { part: true };
    let changed = false;
    for (const [k, v] of Object.entries(now)){
      const same = JSON.stringify(v) === JSON.stringify(was[k]);
      if (always.includes(k)) part[k] = v;
      else if (!same) part[k] = edit(was[k], v);
      if (!same) changed = true;
    }
    return changed ? part : null;
  }
  function merge(screen, m){
    if (!m.part) return m;
    const whole = { ...screen, part: false };
    for (const [k, v] of Object.entries(m)) if (k !== "part") whole[k] = apply(screen?.[k], v);
    return whole;
  }
  // The host's drawing as elements, with nothing in it that could run (a player's page shows only this).
  const DROP = "script,iframe,object,embed,link,meta,base,form";
  function safeAttrs(el){                                // no event handler, no javascript: link
    for (const a of Array.from(el.attributes)){
      const name = a.name.toLowerCase(), v = a.value.replaceAll(/\s+/g, "").toLowerCase();
      const link = (name.endsWith("href") || name === "src") && v.startsWith("javascript:");
      if (name.startsWith("on") || link) el.removeAttribute(a.name);
    }
  }
  function clean(html){
    const doc = new DOMParser().parseFromString(`<body>${typeof html === "string" ? html : ""}</body>`, "text/html");
    doc.body.querySelectorAll(DROP).forEach(el => el.remove());
    doc.body.querySelectorAll("*").forEach(safeAttrs);
    return Array.from(doc.body.childNodes);
  }

  // Room codes: the two connection codes passed through a room server (worker/rooms.js, a Cloudflare
  // Worker) instead of by hand. rooms(server) -> {create, invite, invitation, reply, replied}; each a
  // promise of the server's answer, null for "nothing yet", or an error with its status.
  function rooms(server){
    const base = String(server || "").replace(/\/+$/, "");
    const at = (code, what) => `${base}/rooms/${encodeURIComponent(code)}/${what}`;
    async function call(method, url, { body, key } = {}){
      const headers = {};
      if (key) headers["X-Room-Key"] = key;
      if (body !== undefined) headers["Content-Type"] = "application/json";
      const r = await fetch(url, { method, headers, body: body === undefined ? undefined : JSON.stringify(body) });
      if (r.status === 204) return null;
      const out = await r.json().catch(() => ({}));
      if (!r.ok) throw Object.assign(new Error(out.error || `The room server said ${r.status}.`), { status: r.status });
      return out;
    }
    return {
      create: () => call("POST", `${base}/rooms`),                                         // -> {code, key}
      invite: (code, key, data) => call("PUT", at(code, "invite"), { key, body: { data } }),  // -> {v}
      invitation: (code, after = 0) => call("GET", `${at(code, "invite")}?after=${after}`),   // -> {v, data} or null
      reply: (code, v, data) => call("PUT", at(code, "reply"), { body: { v, data } }),
      replied: (code, key, v) => call("GET", `${at(code, "reply")}?v=${v}`, { key }),         // -> {data} or null
    };
  }
  // ask() again and again until it gives something, or stop() says to give up (-> null). A refusal
  // (a 4xx: no such room, not the host, already answered) ends it with that error; the network or the
  // server failing is tried again. It asks less often the longer it waits (a page left waiting must
  // not use up the server's day): every 1.5 s for two minutes, every 5 s to ten, then every 20 s.
  const pollEvery = waited => (waited < 120e3 ? 1500 : waited < 600e3 ? 5000 : 20000);
  function poll(ask, { stop = () => false, every = pollEvery } = {}){
    const from = Date.now();
    return new Promise((done, fail) => {
      const go = async () => {
        if (stop()) return done(null);
        try { const v = await ask(); if (v !== null && v !== undefined) return done(v) }
        catch (e){ if (e.status >= 400 && e.status < 500) return fail(e) }
        setTimeout(go, every(Date.now() - from));
      };
      go();
    });
  }

  return { packCode, unpackCode, pieces, joiner, hostPeer, guestPeer, PIECE, edit, apply, screenPart, merge, clean, rooms, poll, pollEvery };
})();

if (typeof module !== "undefined") module.exports = NET;   // Node (the tests); the page has no `module`
