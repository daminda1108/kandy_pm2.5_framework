#!/usr/bin/env bash
# retry_until_done.sh LOG N CMD... -- re-run a RESUMABLE job until it exits 0 (network drops,
# Overpass 504s, GEE timeouts). Each attempt appends to LOG; waits 300 s between attempts.
log="$1"; n="$2"; shift 2
for i in $(seq 1 "$n"); do
  echo "=== attempt $i $(date -u +%FT%TZ)" >> "$log"
  PYTHONUTF8=1 "$@" >> "$log" 2>&1 && { echo "=== DONE attempt $i" >> "$log"; exit 0; }
  sleep 300
done
echo "=== GAVE UP after $n attempts" >> "$log"; exit 1
