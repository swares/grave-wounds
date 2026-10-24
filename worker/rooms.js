/* Room codes for Grave Wounds online play: a Cloudflare Worker with a Durable Object per room.

   The pages still connect to each other directly (WebRTC); this only passes the two connection
   codes between them, so nobody copies and pastes. No game data comes here.

     POST /rooms                      a new room -> 201 {code, key} (code: "WOLF-OAK-42"; key: the host's)
     PUT  /rooms/CODE/invite          the host's invitation {data}, with X-Room-Key -> {v} (each one a new version)
     GET  /rooms/CODE/invite?after=V  the invitation newer than V -> 200 {v, data}, or 204 none yet
     PUT  /rooms/CODE/reply           the player's reply to version v {v, data} -> 200; 409 if stale or already answered
     GET  /rooms/CODE/reply?v=V       the reply to version V, with X-Room-Key -> 200 {data}, or 204 none yet

   A room forgets everything ROOM_HOURS after it was last written (an alarm deletes it). Only pages
   from ALLOWED_ORIGINS (a comma list; localhost is always allowed, for testing) may call it.
   Deploy: see worker/README.md. Tested with no Cloudflare by tools/net/rooms.test.mjs. */

const WORDS = ("ash oak elm yew fir bay ivy rye oat hay elk fox owl jay ram ewe cow hen bee ant eel cod " +
  "wolf bear hawk crow dove wren lark swan boar hare mole newt toad frog moth wasp " +
  "iron gold lead salt wool silk flax hemp rope sail mast keel helm oar bow axe pike lance spear " +
  "sword shield mail coif boot belt cloak hood glove ring torc horn drum bell harp lute pipe " +
  "fort keep tower gate wall moat ditch bank ford bridge mill barn byre croft field marsh moor fell " +
  "hill dale vale glen burn beck pool lake mere sea bay cove cape isle rock crag peak cave well " +
  "road lane path way inn hall camp tent fire smoke ember coal flint stone brick tile slate " +
  "bread ale mead wine milk cheese meat fish salt plum pear apple nut bean pea leek kale corn " +
  "king queen duke earl lord lady knight squire monk friar priest bishop smith miller baker " +
  "archer ranger rider scout guard watch herald page cook nurse " +
  "north south east west dawn dusk noon night frost snow rain hail mist storm wind gale " +
  "red blue green grey black white brown amber " +
  "bold brave grim stern swift sly keen calm wild free").split(" ").filter((w, i, all) => all.indexOf(w) === i);
const CODE = /^[A-Z]+-[A-Z]+-\d{2}$/;
const MAX_BODY = 16384;                                    // a connection code is a few hundred characters; this is room to spare
const json = (body, status = 200, headers = {}) => new Response(JSON.stringify(body), { status, headers: { "Content-Type": "application/json", ...headers } });
const empty = (status, headers = {}) => new Response(null, { status, headers });
const pick = n => crypto.getRandomValues(new Uint32Array(1))[0] % n;
const newCode = () => `${WORDS[pick(WORDS.length)]}-${WORDS[pick(WORDS.length)]}-${String(pick(100)).padStart(2, "0")}`.toUpperCase();
const newKey = () => Array.from(crypto.getRandomValues(new Uint8Array(16)), b => b.toString(16).padStart(2, "0")).join("");
const LOCAL = /^https?:\/\/(localhost|127\.0\.0\.1)(:\d+)?$/;

function corsHeaders(request, env){                         // only the site's own pages (and local ones) may call it
  const origin = request.headers.get("Origin") || "";
  const allowed = String(env.ALLOWED_ORIGINS || "https://swares.github.io").split(",").map(s => s.trim()).filter(Boolean);
  if (!origin || !(allowed.includes("*") || allowed.includes(origin) || LOCAL.test(origin))) return null;
  return { "Access-Control-Allow-Origin": origin, "Access-Control-Allow-Methods": "GET, POST, PUT, OPTIONS",
    "Access-Control-Allow-Headers": "Content-Type, X-Room-Key", "Access-Control-Max-Age": "86400", Vary: "Origin" };
}
function withHeaders(response, headers){
  const out = new Response(response.body, response);
  for (const [k, v] of Object.entries(headers)) out.headers.set(k, v);
  return out;
}

export default {
  async fetch(request, env){
    const cors = corsHeaders(request, env);
    if (!cors) return empty(403);
    if (request.method === "OPTIONS") return empty(204, cors);
    const url = new URL(request.url), parts = url.pathname.split("/").filter(Boolean);
    if (parts[0] !== "rooms") return json({ error: "not found" }, 404, cors);
    if (parts.length === 1 && request.method === "POST"){
      for (let i = 0; i < 8; i++){                          // a code not in use (a room that exists says so)
        const code = newCode(), stub = env.ROOMS.get(env.ROOMS.idFromName(code));
        const r = await stub.fetch(new Request("https://room/create", { method: "POST" }));
        if (r.status === 201) return json({ code, key: (await r.json()).key }, 201, cors);
      }
      return json({ error: "no free code" }, 503, cors);
    }
    const code = (parts[1] || "").toUpperCase(), what = parts[2];
    if (parts.length !== 3 || !CODE.test(code) || !["invite", "reply"].includes(what)) return json({ error: "not found" }, 404, cors);
    const stub = env.ROOMS.get(env.ROOMS.idFromName(code));
    const inner = new Request(`https://room/${what}${url.search}`, { method: request.method, headers: request.headers,
      body: ["PUT", "POST"].includes(request.method) ? await request.text() : undefined });
    return withHeaders(await stub.fetch(inner), cors);
  },
};

export class Room {
  constructor(state, env){
    this.state = state;
    this.env = env;
  }
  get ttl(){ return (Number(this.env?.ROOM_HOURS) || 6) * 3600 * 1000 }
  async touch(){ await this.state.storage.setAlarm(Date.now() + this.ttl) }
  async alarm(){ await this.state.storage.deleteAll() }   // the room is forgotten
  async body(request){                                     // the JSON body, or null if too big or not JSON
    const text = await request.text();
    if (text.length > MAX_BODY) return null;
    try { const b = JSON.parse(text); return b && typeof b === "object" ? b : null } catch { return null }
  }
  async fetch(request){
    const url = new URL(request.url), what = url.pathname.slice(1), st = this.state.storage, m = request.method;
    if (what === "create" && m === "POST"){
      if (await st.get("key")) return empty(409);
      const key = newKey();
      await st.put("key", key);
      await this.touch();
      return json({ key }, 201);
    }
    const key = await st.get("key");
    if (!key) return json({ error: "no such room" }, 404);
    const host = request.headers.get("X-Room-Key") === key;
    if (what === "invite" && m === "PUT"){
      if (!host) return json({ error: "not the host" }, 403);
      const b = await this.body(request);
      if (typeof b?.data !== "string") return json({ error: "bad invitation" }, 400);
      const v = ((await st.get("invite"))?.v || 0) + 1;
      await st.put("invite", { v, data: b.data });
      await st.delete("reply");
      await this.touch();
      return json({ v });
    }
    if (what === "invite" && m === "GET"){
      const after = Number(url.searchParams.get("after")) || 0, inv = await st.get("invite");
      return inv && inv.v > after ? json(inv) : empty(204);
    }
    if (what === "reply" && m === "PUT"){
      const b = await this.body(request), inv = await st.get("invite");
      if (typeof b?.data !== "string" || !Number.isInteger(b.v)) return json({ error: "bad reply" }, 400);
      if (inv?.v !== b.v) return json({ error: "that invitation is old" }, 409);
      if ((await st.get("reply"))?.v === b.v) return json({ error: "already answered" }, 409);
      await st.put("reply", { v: b.v, data: b.data });
      await this.touch();
      return json({ ok: true });
    }
    if (what === "reply" && m === "GET"){
      if (!host) return json({ error: "not the host" }, 403);
      const v = Number(url.searchParams.get("v")), rep = await st.get("reply");
      return rep && rep.v === v ? json({ data: rep.data }) : empty(204);
    }
    return json({ error: "not found" }, 404);
  }
}
