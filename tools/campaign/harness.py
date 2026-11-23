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
# The tests' dice, in place of the browser's crypto (never for anything secret).
# A page load counts itself in sessionStorage (which the tests' localStorage.clear() leaves), so each load of a
# page goes on with fresh dice rather than the same ones again, and a seed still gives the same run; mulberry32,
# started from the seed and the load's number, mixes well from the first roll. Each new page (tab) counts afresh.
DICE = """(() => { const seed = %d >>> 0; let n = 0;
  try { n = +(sessionStorage.getItem("gw-test-dice-loads") || 0); sessionStorage.setItem("gw-test-dice-loads", String(n + 1)) } catch {}
  let t = (Math.imul(seed + 1, 0x9E3779B1) ^ Math.imul(n + 1, 0x85EBCA77)) >>> 0;
  crypto.getRandomValues = a => { for (let i = 0; i < a.length; i++){ t = (t + 0x6D2B79F5) >>> 0; let z = t;
    z = Math.imul(z ^ (z >>> 15), z | 1); z ^= z + Math.imul(z ^ (z >>> 7), z | 61); a[i] = (z ^ (z >>> 14)) >>> 0 } return a } })();"""


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


def main(run, server):
    """Run a test's run(playwright), report a stop as a failed check, shut the server and exit."""
    import sys
    import traceback
    from playwright.sync_api import sync_playwright
    try:
        with sync_playwright() as pw:
            run(pw)
    except Exception as e:                           # a timeout or error: where, as an annotation in CI
        print(traceback.format_exc())
        check(False, f"stopped: {str(e).splitlines()[0][:300]}")
    server.shutdown()
    if failures:
        print(f"{len(failures)} check(s) failed")
        sys.exit(1)
    print("all checks passed")
