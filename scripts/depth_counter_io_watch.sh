#!/usr/bin/env bash
set -euo pipefail

CAMERA_IP="192.168.10.11"
OPI_USER="orangepi"
BOOTSTRAP_SINCE="today"
SHOW_HEARTBEAT="1"
POLL_SEC="1.0"
UNIT="passengers-camera-depth-counting.service"

usage() {
  cat <<'USAGE'
depth_counter_io_watch.sh — watch only IN/OUT from depth counting events (strict or depth-height-multi)

Usage:
  ./scripts/depth_counter_io_watch.sh [options]

Options:
  --camera-ip <ip>    Camera node IP (default: 192.168.10.11)
  --central-ip <ip>   Alias for --camera-ip
  --user <name>       SSH user (default: orangepi)
  --unit <name>       Systemd unit (default: passengers-camera-depth-counting.service)
  --bootstrap-since <expr>
                      Initial totals window (default: "today")
  --poll-sec <float>  Health polling interval seconds (default: 1.0)
  --no-heartbeat
                      Do not print heartbeat lines with current totals
  -h, --help          Show help

Examples:
  ./scripts/depth_counter_io_watch.sh
  ./scripts/depth_counter_io_watch.sh --camera-ip 192.168.10.11 --user orangepi
  ./scripts/depth_counter_io_watch.sh --unit passengers-camera-depth-height-multi.service
  ./scripts/depth_counter_io_watch.sh --poll-sec 0.5
  ./scripts/depth_counter_io_watch.sh --bootstrap-since "2 hours ago"
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --camera-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --central-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --unit) UNIT="${2:-}"; shift 2 ;;
    --bootstrap-since) BOOTSTRAP_SINCE="${2:-}"; shift 2 ;;
    --poll-sec) POLL_SEC="${2:-}"; shift 2 ;;
    --no-heartbeat) SHOW_HEARTBEAT="0"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

HOST="${OPI_USER}@${CAMERA_IP}"

echo "Watching IN/OUT on ${HOST} (${UNIT}, Ctrl+C to stop)"
echo "Format: HH:MM:SS IN_TOTAL=<n> OUT_TOTAL=<n> (+in/+out)"

ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

bootstrap_cmd="journalctl -u ${UNIT} -o cat --no-pager"
if [[ -n "${BOOTSTRAP_SINCE}" ]]; then
  bootstrap_cmd+=" --since $(printf '%q' "${BOOTSTRAP_SINCE}")"
fi

bootstrap_raw="$(
  # shellcheck disable=SC2029
  ssh "${HOST}" "${bootstrap_cmd}" \
    | awk '
      /transport-strict event:|depth-height-multi event:/ {
        in_inc=0; out_inc=0;
        for (i=1; i<=NF; i++) {
          if ($i ~ /^in=/)  { split($i,a,"="); in_inc=a[2]+0; }
          if ($i ~ /^out=/) { split($i,b,"="); out_inc=b[2]+0; }
        }
        in_total += in_inc;
        out_total += out_inc;
      }
      END { printf "%d %d", in_total+0, out_total+0 }
    '
)"

bootstrap_in="$(echo "${bootstrap_raw}" | awk '{print $1+0}')"
bootstrap_out="$(echo "${bootstrap_raw}" | awk '{print $2+0}')"
echo "Initial totals since '${BOOTSTRAP_SINCE}': IN=${bootstrap_in} OUT=${bootstrap_out}"

health_once_cmd="python3 - <<'PY'
import json, urllib.request
try:
    with urllib.request.urlopen('http://127.0.0.1:8091/health', timeout=3) as resp:
        data = json.loads(resp.read().decode('utf-8', errors='ignore'))
    print(f\"{int(data.get('count_in', 0))} {int(data.get('count_out', 0))} {int(data.get('events_total', 0))}\")
except Exception:
    print('0 0 0')
PY"

# shellcheck disable=SC2029
health_raw="$(ssh "${HOST}" "${health_once_cmd}")"
session_in_start="$(echo "${health_raw}" | awk '{print $1+0}')"
session_out_start="$(echo "${health_raw}" | awk '{print $2+0}')"
session_events="$(echo "${health_raw}" | awk '{print $3+0}')"
echo "Depth session baseline: IN=${session_in_start} OUT=${session_out_start} events=${session_events}"

offset_in=$((bootstrap_in - session_in_start))
offset_out=$((bootstrap_out - session_out_start))
prev_session_in="${session_in_start}"
prev_session_out="${session_out_start}"
prev_total_in="${bootstrap_in}"
prev_total_out="${bootstrap_out}"
last_hb_ts=0

watch_cmd="python3 - <<'PY'
import json
import time
import urllib.request

url = 'http://127.0.0.1:8091/health'
poll = float('${POLL_SEC}')
while True:
    try:
        with urllib.request.urlopen(url, timeout=2) as resp:
            data = json.loads(resp.read().decode('utf-8', errors='ignore'))
        print(f\"OK {int(data.get('count_in', 0))} {int(data.get('count_out', 0))} {int(data.get('events_total', 0))}\", flush=True)
    except Exception:
        print('ERR 0 0 0', flush=True)
    time.sleep(poll)
PY"

# shellcheck disable=SC2029
ssh "${HOST}" "${watch_cmd}" | while read -r status session_in session_out events_total; do
  now_ts="$(date +%s)"
  if [[ "${status}" != "OK" ]]; then
    if [[ "${SHOW_HEARTBEAT}" == "1" ]] && (( now_ts - last_hb_ts >= 10 )); then
      echo "$(date +%H:%M:%S) HB IN_TOTAL=${prev_total_in} OUT_TOTAL=${prev_total_out} events=? (health unavailable)"
      last_hb_ts="${now_ts}"
    fi
    continue
  fi

  if (( session_in < prev_session_in || session_out < prev_session_out )); then
    offset_in=$((prev_total_in - session_in))
    offset_out=$((prev_total_out - session_out))
  fi

  total_in=$((offset_in + session_in))
  total_out=$((offset_out + session_out))
  inc_in=$((total_in - prev_total_in))
  inc_out=$((total_out - prev_total_out))

  if (( inc_in != 0 || inc_out != 0 )); then
    echo "$(date +%H:%M:%S) IN_TOTAL=${total_in} OUT_TOTAL=${total_out} (+${inc_in}/+${inc_out}) events=${events_total}"
  elif [[ "${SHOW_HEARTBEAT}" == "1" ]] && (( now_ts - last_hb_ts >= 10 )); then
    echo "$(date +%H:%M:%S) HB IN_TOTAL=${total_in} OUT_TOTAL=${total_out} events=${events_total}"
    last_hb_ts="${now_ts}"
  fi

  prev_session_in="${session_in}"
  prev_session_out="${session_out}"
  prev_total_in="${total_in}"
  prev_total_out="${total_out}"
done
