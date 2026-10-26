#!/bin/bash
# commander.sh [seeds] [workers]: rebuild the enemy commander's benchmark (commander.json) under the current rules.
# Runs every battlefield seeds times (default 12) on dist/field.html, then commander.py. Build first (python3 build.py)
# so the page and dist/field-stamps.json are current. A run takes about 45 seconds on average: 12 seeds on 2 workers, about 3½ hours.
set -eu
here=$(cd "$(dirname "$0")" && pwd)
out=$(mktemp -d)
"$here/run.sh" "${1:-12}" "$out" "" "${2:-2}" 1 play
grep FAILED "$out/run.log" && { echo "some runs failed; see $out/run.log"; exit 1; }
rm -f "$here/commander.json"
python3 "$here/commander.py" "$out"
