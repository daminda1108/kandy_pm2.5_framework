#!/usr/bin/env bash
# night_window.sh LOG TAG CMD... -- run a RESUMABLE download job only inside the free-download window
# SLT Fibre Starter: free data 00:00-07:00 SLST (slt.lk package page, checked 2026-10-04); the 80 GB anytime
# quota must never run out, because then ALL traffic, night included, drops to 64 kbps. Runs night after night
# until CMD exits 0, inside 00:05-06:45 (15-min margins), and logs the bytes each night used.
#
#   * waits until START (00:05 SLST), then runs CMD with NIGHT_DEADLINE (epoch seconds of STOP, 03:50)
#     in the environment. Downloaders check it (scripts/night_guard.py) before starting each new unit
#     of work and exit with code 75 ("come back tomorrow") when it has passed;
#   * backstop: at STOP + 4 min any process whose command line contains TAG is stopped (whole tree,
#     via PowerShell), because on Windows killing a venv launcher can leave its python child alive;
#   * every unit of work must be written atomically (temp file + os.replace), so a stop loses at most the
#     unit in progress, which the next night redoes;
#   * exit 0 from CMD = finished; anything else = resume next night. Gives up after MAX_NIGHTS.
log="$1"; tag="$2"; shift 2
START="${NIGHT_START:-00:05}"; STOP="${NIGHT_STOP:-06:45}"; MAX_NIGHTS="${MAX_NIGHTS:-10}"
rx() { powershell -NoProfile -Command "(Get-NetAdapterStatistics | Measure-Object -Property ReceivedBytes -Sum).Sum + (Get-NetAdapterStatistics | Measure-Object -Property SentBytes -Sum).Sum" 2>/dev/null | tr -cd '0-9'; }
epoch_at() { date -d "$(date +%F) $1" +%s; }            # today at HH:MM local
for night in $(seq 1 "$MAX_NIGHTS"); do
  now=$(date +%s); s=$(epoch_at "$START"); e=$(epoch_at "$STOP")
  if [ "$now" -ge "$e" ]; then                          # past today's window: wait for tomorrow's
    s=$((s + 86400)); e=$((e + 86400))
  fi
  if [ "$now" -lt "$s" ]; then
    echo "=== night $night: waiting until $(date -d @$s '+%F %T') $(date '+%Z')" >> "$log"
    sleep $((s - now))
  fi
  echo "=== night $night: start $(date '+%F %T %Z'), deadline $(date -d @$e '+%T')" >> "$log"
  ( sleep $((e - $(date +%s) + 240)); powershell -NoProfile -Command \
      "Get-CimInstance Win32_Process | Where-Object { \$_.CommandLine -match '$tag' -and \$_.Name -eq 'python.exe' } | ForEach-Object { Stop-Process -Id \$_.ProcessId -Force -ErrorAction SilentlyContinue }" \
      >/dev/null 2>&1; echo "=== backstop fired $(date '+%T')" >> "$log" ) &
  guard=$!
  b0=$(rx)
  NIGHT_DEADLINE="$e" PYTHONUTF8=1 PYTHONIOENCODING=utf-8 "$@" >> "$log" 2>&1
  rc=$?
  kill "$guard" 2>/dev/null
  b1=$(rx); gb=$(awk -v a="$b0" -v b="$b1" 'BEGIN{printf "%.2f", (b-a)/1e9}')
  echo "=== night $night: exit $rc at $(date '+%F %T'), all-adapter traffic this run ${gb} GB" >> "$log"
  if [ "$rc" -eq 0 ]; then echo "=== DONE" >> "$log"; exit 0; fi
  sleep 300                                             # avoid a tight loop if the job fails fast
done
echo "=== GAVE UP after $MAX_NIGHTS nights" >> "$log"; exit 1
