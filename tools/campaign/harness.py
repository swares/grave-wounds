"""What the campaign's browser tests share: the site served as it is (a local web server) and the checks.

    from harness import check, failures, serve
    base, server = serve()   # base: http://127.0.0.1:<port>/dist/
"""
import functools
import http.server
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
failures = []
# The tests' dice: Park-Miller from the seed, in place of the browser's crypto (never for anything secret).
DICE = """(() => { let s = Math.max(1, %d * 7919 %% 2147483647);
  crypto.getRandomValues = a => { for (let i = 0; i < a.length; i++){ s = (s * 16807) %% 2147483647; a[i] = s } return a } })();"""


CI = bool(__import__("os").environ.get("GITHUB_ACTIONS"))


def check(ok, what):
    print(("ok   " if ok else "FAIL ") + what)
    if not ok:
        failures.append(what)
        if CI:                                       # an annotation on the run, readable without the log
            print(f"::error title=check failed::{what}")


class Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):   # the server's request lines would drown the checks
        return None


def serve():
    """The repository served on a free local port: (the dist/ URL, the server, to shut down)."""
    server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quiet, directory=str(ROOT)))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return f"http://127.0.0.1:{server.server_port}/dist/", server
