"""What the room-code browser tests share (rooms.py, playercoach.py): the site served as it is, the room
server on a local port (the Worker's own code, tools/net/fakerooms.mjs), a campaign with named men on a
map, and the checks (each failure an annotation in CI, readable without the log).

    from roomharness import check, failures, serve, campaign_with
    site, base, rooms, stop = serve()   # site: http://127.0.0.1:<port>/, base: its dist/, rooms: the room server's URL
"""
import functools, http.server, os, subprocess, threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CI = bool(os.environ.get("GITHUB_ACTIONS"))
CONNECTED = "() => document.querySelector('#p-status').textContent.startsWith('Connected')"
failures = []


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)
        if CI:
            print(f"::error title=check failed::{what}")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        return None


def serve():
    """The repository on a free local port and the room server beside it: (site URL, dist URL, rooms URL, stop)."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    rooms = subprocess.Popen(["node", str(ROOT / "tools" / "net" / "fakerooms.mjs")], stdout=subprocess.PIPE, text=True)
    url = rooms.stdout.readline().strip()
    site = f"http://127.0.0.1:{server.server_port}/"

    def stop():
        rooms.terminate()
        server.shutdown()
    return site, site + "dist/", url, stop


def campaign_with(gm, base, map_id, men):
    """A fresh campaign on map_id, the named men {uid: name} with its first force, kept as the travel map keeps it."""
    gm.goto(base + "travel.html"); gm.evaluate("() => localStorage.clear()"); gm.reload()
    gm.wait_for_function("() => typeof forcesHere === 'function'", timeout=15000)
    gm.evaluate("""([mapId, men]) => { S.mapId = mapId; S.clock = {}; const a = forcesHere()[0];
      const man = name => ({ name, map: mapId, force: a.id, pid: 'pid-' + name, endurance: 50, log: [], health: { cases: [], immune: {}, had: {}, dead: 0 } });
      localStorage.setItem('gravewounds-named', JSON.stringify(Object.fromEntries(Object.entries(men).map(([u, n]) => [u, man(n)])))); save() }""", [map_id, men])


def add_player(gm, rooms, name, uid):
    """The GM's room server chosen (once), and a player added for the named man uid: his room's code."""
    if rooms not in gm.inner_text("#c-players"):
        gm.click("#c-players details summary")
        gm.fill("#pl-room", rooms); gm.click("#pl-room-set")
    gm.fill("#pl-name", name); gm.uncheck("#pl-stun"); gm.check(f'[data-pl-new][value="{uid}"]'); gm.click("#pl-add")
    gm.wait_for_function(f"() => {{ const pl = REC.players.find(p => p.name === {name!r}); return pl && PL.conn[pl.id]?.room }}", timeout=15000)
    return gm.evaluate(f"() => PL.conn[REC.players.find(p => p.name === {name!r}).id].room")
