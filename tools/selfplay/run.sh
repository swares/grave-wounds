#!/bin/bash
# run.sh <seeds> <out dir> [page] [workers] [first seed] [tool]: every battlefield x seed as its own job, the longest
# first (by times.txt, if there), shared among the workers. tool: play (default; out/<fid>.s<k>.json, joined by
# report.py), quality (the commander report) or targets (play's runs with the morale targets). Progress and failures go to out/run.log.
set -u
here=$(cd "$(dirname "$0")" && pwd); root=$(cd "$here/../.." && pwd)
seeds=$1; out=$2; page=${3:-$root/dist/field.html}; workers=${4:-2}; first=${5:-1}; tool=${6:-play}
mkdir -p "$out"; log=$out/run.log; : > "$log"; queue=$out/.queue
python3 - "$root/data/fields" "$here/times.txt" "$seeds" "$first" > "$queue" <<'PY'
import os, sys
fields, times, n, first = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
fids = sorted(f[:-5] for f in os.listdir(fields) if f.endswith(".yaml"))
t = dict(line.split() for line in open(times)) if os.path.exists(times) else {}
for _, f, k in sorted(((float(t.get(f, 0)), f, k) for f in fids for k in range(first, first + n)), key=lambda x: -x[0]):
    print(f, k)
PY
job(){
  local fid=$1 k=$2
  if [[ "$tool" == quality || "$tool" == targets ]]; then node "$here/$tool.js" "$fid" "$k" "$page" > "$out/$fid.s$k.json"
  else node "$here/play.js" "$fid" 1 "$out/$fid.s$k.json" "$page" "$k"; fi
  return $?
}
worker(){
  local j fid k
  while :; do
    j=$(flock "$queue.lock" sh -c 'j=$(head -1 "$0"); [ -n "$j" ] && sed -i 1d "$0"; echo "$j"' "$queue")
    [[ -z "$j" ]] && break
    read -r fid k <<< "$j"
    job "$fid" "$k" >> "$log" 2>&1 || echo "$fid s$k FAILED" >> "$log"
  done
  return 0
}
for _ in $(seq "$workers"); do worker & done
wait
rm -f "$queue" "$queue.lock"
echo "ALL DONE" >> "$log"
