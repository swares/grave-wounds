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
- `rooms.json`: the server's address, built into the site. It is empty until you deploy.

## Deploying it (once)

1. Make a free Cloudflare account, if you have none (dash.cloudflare.com).
2. In this folder, with Node 18 or later:

   ```
   npx wrangler login
   npx wrangler deploy
   ```

   `deploy` prints the Worker's address, like `https://grave-wounds-rooms.<your-subdomain>.workers.dev`.
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

## Testing it

`node tools/net/roomscheck.mjs` runs the Worker's own code with an in-memory stand-in for the Durable
Object namespace (`tools/net/fakerooms.mjs`). To run the same checks against Cloudflare's local
runtime, start `npx wrangler dev` here and run
`ROOMS_LIVE=1 node tools/net/roomscheck.mjs`. `python3 tools/net/rooms.py` connects
a console and two players' pages through it in a headless browser.

## What it does not do

- **No accounts and no rate limit.** Anyone with a room's code can read its invitation and answer
  it, as anyone with a copy-and-paste link can today. Only the first answer to each invitation is
  taken, and the GM's console shows who is connected. With about 4 million codes (203 words, two of them, and two digits) and rooms that
  live hours, guessing one is unlikely, but not impossible.
- **No relay (TURN).** Players on strict networks may still not connect.
