// The room Worker (worker/rooms.js) run with no Cloudflare: its own code, with an in-memory Durable
// Object namespace in place of Cloudflare's (storage get/put/delete/deleteAll, alarms), for the tests.
//   import { makeEnv, serve } from "./fakerooms.mjs"
//   node tools/net/fakerooms.mjs [port]   serves it on localhost for the browser test (prints its URL)
import http from "node:http";
import worker, { Room } from "../../worker/rooms.js";

class Storage {
  constructor(){ this.map = new Map(); this.alarmAt = null }
  async get(k){ return structuredClone(this.map.get(k)) }
  async put(k, v){ this.map.set(k, structuredClone(v)) }
  async delete(k){ return this.map.delete(k) }
  async deleteAll(){ this.map.clear() }
  async setAlarm(t){ this.alarmAt = t }
  async getAlarm(){ return this.alarmAt }
}
export function makeEnv(vars = {}){
  const rooms = new Map();
  const env = { ...vars };
  env.ROOMS = {
    idFromName: name => name,
    get(id){
      if (!rooms.has(id)){ const state = { storage: new Storage() }; rooms.set(id, { state, obj: new Room(state, env), queue: Promise.resolve() }) }
      const r = rooms.get(id);
      return { fetch: req => {                              // one request at a time, as a Durable Object takes them
        const run = r.queue.then(() => r.obj.fetch(req));
        r.queue = run.catch(() => null);
        return run;
      } };
    },
  };
  env.rooms = rooms;                                        // for the tests: run the alarms that are due
  env.runAlarms = async (now = Date.now()) => {
    const due = [...rooms.values()].filter(r => r.state.storage.alarmAt !== null && r.state.storage.alarmAt <= now);
    for (const r of due) r.state.storage.alarmAt = null;
    await Promise.all(due.map(r => r.obj.alarm()));
  };
  return env;
}
export function serve(port = 0, vars = {}){                  // the Worker on a local port -> Promise<{url, server, env}>
  const env = makeEnv(vars);
  const server = http.createServer(async (req, res) => {
    const chunks = [];
    for await (const c of req) chunks.push(c);
    const body = chunks.length ? Buffer.concat(chunks) : undefined;
    const at = new URL(req.url, "http://127.0.0.1");          // the path and query only: always this server
    const request = new Request(`http://127.0.0.1${at.pathname}${at.search}`, { method: req.method, headers: req.headers, body: ["GET", "HEAD", "OPTIONS"].includes(req.method) ? undefined : body });
    const r = await worker.fetch(request, env);
    res.writeHead(r.status, Object.fromEntries(r.headers));
    res.end(Buffer.from(await r.arrayBuffer()));
  });
  return new Promise(ok => server.listen(port, "127.0.0.1", () => ok({ url: `http://127.0.0.1:${server.address().port}`, server, env })));
}
if (process.argv[1] && import.meta.url.endsWith(process.argv[1].split("/").pop())){
  const { url } = await serve(Number(process.argv[2]) || 0);
  console.log(url);
}
