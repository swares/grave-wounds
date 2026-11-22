#!/bin/bash
# commander.sh [seeds] [workers]: rebuild the enemy commander's benchmark (commander.json) under the current rules.
# Runs every battlefield seeds times (default 12) on dist/field.html, then commander.py. Build first (python3 build.py)
# so the page and dist/field-stamps.json are current. A run takes about 45 seconds on average: 36 seeds on 2 workers, about 10 hours
# here; the selfplay workflow on GitHub (16 jobs) takes about 35 minutes. 36, not 12: on a swingy battlefield 12 seeds can be
# far off (Agincourt's English won 67% on 12, 44% on 36 and about 37% on 60).
set -eu
here=$(cd "$(dirname "$0")" && pwd)
out=$(mktemp -d)
"$here/run.sh" "${1:-36}" "$out" "" "${2:-2}" 1 play
grep FAILED "$out/run.log" && { echo "some runs failed; see $out/run.log"; exit 1; }
rm -f "$here/commander.json"
python3 "$here/commander.py" "$out"
