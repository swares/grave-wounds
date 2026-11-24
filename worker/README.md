# The room server (room codes for online play)

A Cloudflare Worker that passes the two connection codes between the GM's campaign console and a
player's page, so nobody copies and pastes. Each player gets a room with a code to say aloud
(`WOLF-OAK-42`). The console puts his invitation in it and his page puts its reply back. When he is
lost, or either page reloads, the console invites him again and his page answers, by themselves.

The pages still connect to each other directly (WebRTC). No game data passes through the Worker,
only the connection codes. A room is forgotten 6 hours after it was last written.

Files:

- `rooms.js`: the Worker, with a Durable Object per room (`Room`).
- `wrangler.toml`: its settings. These are the allowed origins (`ALLOWED_ORIGINS`), the room
  life (`ROOM_HOURS`), and the Durable Object binding with its SQLite migration.
- `rooms.json`: the server's address, built into the site: `https://grave-wounds-rooms.waresscott.workers.dev`, deployed October 2026.

## Deploying it (once)

1. Make a free Cloudflare account, if you have none (dash.cloudflare.com).
2. In this folder, with Node 18 or later:

   ```
   npx wrangler login
   npx wrangler deploy
   ```

   `deploy` prints the Worker's address, like `https://grave-wounds-rooms.<your-subdomain>.workers.dev`.
   On a new account the first deploy may upload the Worker and then fail with "This Worker does not
   exist on your account [code: 10007]"; running `npx wrangler deploy` again finished it (October 2026).
3. Put that address in `rooms.json` (`{"server": "https://grave-wounds-rooms.<your-subdomain>.workers.dev"}`).
   Then rebuild the site (`python3 build.py`) and commit. The console and the players' pages then use
   it by themselves.

   Until then, a GM can try it from his own browser under **Players online → Room server** on the
   console. That choice is kept in that browser only, and his players' links carry the address.

If the site is served from anywhere but `https://swares.github.io`, add that origin to
`ALLOWED_ORIGINS` in `wrangler.toml` (commas between them) and deploy again. Pages on `localhost` or
`127.0.0.1` are always allowed, for testing.

## What it costs

Nothing on the Workers Free plan, as far as Cloudflare's pricing page says (checked October 2026).
It uses SQLite-backed Durable Objects, which the Free plan allows. The Free plan's limits include
100,000 Durable Object requests a day, and the Workers Free plan has its own daily request limit.

Pages ask a room every 1.5 seconds while they wait, then less often: every 5 seconds after two
minutes, and every 20 seconds after ten. A page left waiting all day makes about 4,300 requests. Each
request goes to the Worker and then to its Durable Object, so it counts against both limits. Over
the limit, requests fail until the next day (00:00 UTC). The pages then fall back to nothing: copy
and paste works with the room server setting left blank.

## The relay (TURN), for strict networks

The pages connect to each other directly, with a public STUN server to find each other. A few strict
networks (some workplaces, some mobile networks) block that, and then the pages cannot connect. A
**relay** carries their traffic instead. The Worker can hand the pages Cloudflare's own TURN relay,
and does nothing until it has its two secrets: without them, `GET /turn` answers 404 and the pages
use STUN alone, as before.

To turn it on:

1. In the Cloudflare dashboard, open **Realtime**, then **TURN Server**, and create a TURN key. Note
   its **Key ID** and its **API token** (the token is shown once).
2. In this folder:

   ```
   npx wrangler secret put TURN_KEY_ID
   npx wrangler secret put TURN_KEY_API_TOKEN
   npx wrangler deploy
   ```

   Each `secret put` asks for the value. Secrets are kept by Cloudflare, not in this repository.
3. Nothing to rebuild: the pages ask the room server for its relay (`GET /turn`) when they load, and
   use it from then on. Pages with the room server switched off, or with STUN unticked (everyone on
   one network), never ask.

Each `GET /turn` mints credentials that last `RELAY_HOURS` (6, in `wrangler.toml`), and leaves out the
port-53 address the response can carry, which browsers block. Only the site's pages may ask
(`ALLOWED_ORIGINS`), but that is a check browsers make: anyone who copies the address can get
credentials too. The relay is used only when a direct connection fails.

**What it costs** (Cloudflare's Realtime pricing page, checked November 2026): the first 1,000 GB a
month are free, shared with Cloudflare's other Realtime service, then $0.05 a GB. A game's traffic
is small (each player's screen as changes, a few kilobytes a move), so the free allowance should be
far more than a group of players uses. To turn it off, delete the two secrets
(`npx wrangler secret delete TURN_KEY_ID`) and deploy again.

## Testing it

`node tools/net/roomscheck.mjs` runs the Worker's own code with an in-memory stand-in for the Durable
Object namespace (`tools/net/fakerooms.mjs`), and the relay with a stand-in for Cloudflare's TURN API. `python3 tools/net/rooms.py` connects a console and two
players' pages through it in a headless browser. Both run in CI.

To try it on Cloudflare's own local runtime, run `npx wrangler dev` here, then:

```
O="Origin: http://127.0.0.1:1"
curl -s -X POST -H "$O" http://127.0.0.1:8787/rooms               # {"code":"SWORD-CAPE-14","key":"..."}
curl -s -X PUT -H "$O" -H "X-Room-Key: <key>" -H "Content-Type: application/json" \
  -d '{"data":"I"}' http://127.0.0.1:8787/rooms/<code>/invite       # {"v":1}
curl -s -H "$O" "http://127.0.0.1:8787/rooms/<code>/invite?after=0" # {"v":1,"data":"I"}
```

With `npx wrangler dev --var ROOM_HOURS:0.0005`, the room is gone (404) a few seconds later.

## What it does not do

- **No accounts and no rate limit.** Anyone with a room's code can read its invitation and answer
  it, as anyone with a copy-and-paste link can today. Only the first answer to each invitation is
  taken, and the GM's console shows who is connected. With about 4 million codes (203 words, two of them, and two digits) and rooms that
  live hours, guessing one is unlikely, but not impossible.
- **No relay (TURN).** Players on strict networks may still not connect.
