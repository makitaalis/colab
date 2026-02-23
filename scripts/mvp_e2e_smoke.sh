#!/usr/bin/env bash
set -euo pipefail

CENTRAL_IP="${CENTRAL_IP:-192.168.10.1}"
DOOR1_IP="${DOOR1_IP:-192.168.10.11}"
DOOR2_IP="${DOOR2_IP:-192.168.10.12}"
SERVER_HOST="${SERVER_HOST:-207.180.213.225}"

CENTRAL_USER="${CENTRAL_USER:-orangepi}"
DOOR_USER="${DOOR_USER:-orangepi}"
SERVER_USER="${SERVER_USER:-alis}"

DOOR1_IN="${DOOR1_IN:-3}"
DOOR1_OUT="${DOOR1_OUT:-1}"
DOOR2_IN="${DOOR2_IN:-1}"
DOOR2_OUT="${DOOR2_OUT:-2}"

MAX_WAIT_SEC="${MAX_WAIT_SEC:-45}"
POLL_SEC="${POLL_SEC:-3}"
SSH_TIMEOUT_SEC="${SSH_TIMEOUT_SEC:-8}"

usage() {
  cat <<'EOF'
Usage: ./scripts/mvp_e2e_smoke.sh [options]

Options:
  --central-ip <ip>     Central IP (default: 192.168.10.1)
  --door1-ip <ip>       Door-1 IP (default: 192.168.10.11)
  --door2-ip <ip>       Door-2 IP (default: 192.168.10.12)
  --server-host <host>  Backend server host (default: 207.180.213.225)
  --door1-in <n>        Test IN count for door-1 (default: 3)
  --door1-out <n>       Test OUT count for door-1 (default: 1)
  --door2-in <n>        Test IN count for door-2 (default: 1)
  --door2-out <n>       Test OUT count for door-2 (default: 2)
  --max-wait-sec <n>    Max wait for backend stats update (default: 45)
  --poll-sec <n>        Poll interval in seconds (default: 3)
  -h, --help            Show this help

Environment overrides:
  CENTRAL_IP, DOOR1_IP, DOOR2_IP, SERVER_HOST
  CENTRAL_USER, DOOR_USER, SERVER_USER
  DOOR1_IN, DOOR1_OUT, DOOR2_IN, DOOR2_OUT
  MAX_WAIT_SEC, POLL_SEC, SSH_TIMEOUT_SEC
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --central-ip) CENTRAL_IP="$2"; shift 2 ;;
    --door1-ip) DOOR1_IP="$2"; shift 2 ;;
    --door2-ip) DOOR2_IP="$2"; shift 2 ;;
    --server-host) SERVER_HOST="$2"; shift 2 ;;
    --door1-in) DOOR1_IN="$2"; shift 2 ;;
    --door1-out) DOOR1_OUT="$2"; shift 2 ;;
    --door2-in) DOOR2_IN="$2"; shift 2 ;;
    --door2-out) DOOR2_OUT="$2"; shift 2 ;;
    --max-wait-sec) MAX_WAIT_SEC="$2"; shift 2 ;;
    --poll-sec) POLL_SEC="$2"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout="${SSH_TIMEOUT_SEC}")

ssh_central() {
  ssh "${SSH_OPTS[@]}" "${CENTRAL_USER}@${CENTRAL_IP}" "$@"
}

ssh_door1() {
  ssh "${SSH_OPTS[@]}" "${DOOR_USER}@${DOOR1_IP}" "$@"
}

ssh_door2() {
  ssh "${SSH_OPTS[@]}" "${DOOR_USER}@${DOOR2_IP}" "$@"
}

ssh_server() {
  ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "$@"
}

parse_stats_triplet() {
  python3 -c 'import json,sys; d=json.load(sys.stdin); print(int(d.get("batches",0)), int(d.get("total_in",0)), int(d.get("total_out",0)))'
}

get_vehicle_id() {
  ssh_central "sudo sed -n 's/^VEHICLE_ID=//p' /etc/passengers/passengers.env | head -n1 | tr -d '\r'"
}

get_stop_mode() {
  local mode
  mode="$(ssh_central "sudo sed -n 's/^STOP_MODE=//p' /etc/passengers/passengers.env | head -n1 | tr -d '\r'")"
  mode="$(printf '%s' "${mode}" | tr '[:upper:]' '[:lower:]')"
  if [[ "${mode}" == "manual" || "${mode}" == "timer" ]]; then
    echo "${mode}"
    return 0
  fi
  echo "timer"
}

get_backend_stats_json() {
  local vehicle_id="$1"
  ssh_server "token=\$(grep -m1 '^PASSENGERS_API_KEYS=' /opt/passengers-backend/.env | cut -d= -f2 | tr -d '\r' | cut -d, -f1); curl -sS -H \"Authorization: Bearer \${token}\" http://10.66.0.1/api/v1/stats/vehicle/${vehicle_id}"
}

print_stage() {
  echo
  echo "== $* =="
}

print_stage "Check connectivity and service state"
stop_mode="$(get_stop_mode)"
ssh_central "hostname >/dev/null; systemctl is-active passengers-collector passengers-central-uplink passengers-central-heartbeat.timer >/dev/null"
if [[ "${stop_mode}" == "timer" ]]; then
  ssh_central "systemctl is-active passengers-central-flush.timer >/dev/null"
fi
ssh_door1 "hostname >/dev/null; systemctl is-active passengers-edge-sender >/dev/null"
ssh_door2 "hostname >/dev/null; systemctl is-active passengers-edge-sender >/dev/null"

vehicle_id="$(get_vehicle_id)"
if [[ -z "${vehicle_id}" ]]; then
  echo "ERROR: VEHICLE_ID is empty on central (/etc/passengers/passengers.env)" >&2
  exit 1
fi
echo "Vehicle: ${vehicle_id}"
echo "Stop mode: ${stop_mode}"

print_stage "Read baseline backend stats"
baseline_json="$(get_backend_stats_json "${vehicle_id}")"
read -r pre_batches pre_in pre_out < <(printf '%s' "${baseline_json}" | parse_stats_triplet)
echo "Before: batches=${pre_batches} in=${pre_in} out=${pre_out}"

expected_in=$((DOOR1_IN + DOOR2_IN))
expected_out=$((DOOR1_OUT + DOOR2_OUT))
echo "Expected minimum delta: batches>=1 in>=${expected_in} out>=${expected_out}"

print_stage "Enqueue test events on door nodes"
ssh_door1 "sudo python3 /opt/passengers-mvp/enqueue_event.py --door-id 2 --in ${DOOR1_IN} --out ${DOOR1_OUT}"
ssh_door2 "sudo python3 /opt/passengers-mvp/enqueue_event.py --door-id 3 --in ${DOOR2_IN} --out ${DOOR2_OUT}"

print_stage "Trigger manual flush on central"
ssh_central "sudo python3 /opt/passengers-mvp/central_flush.py --send-now --stop-mode ${stop_mode}"

print_stage "Wait for backend stats update"
attempt=0
max_attempts=$(( (MAX_WAIT_SEC + POLL_SEC - 1) / POLL_SEC ))
if (( max_attempts < 1 )); then
  max_attempts=1
fi

success=0
post_batches="${pre_batches}"
post_in="${pre_in}"
post_out="${pre_out}"

while (( attempt < max_attempts )); do
  attempt=$((attempt + 1))
  current_json="$(get_backend_stats_json "${vehicle_id}")"
  read -r post_batches post_in post_out < <(printf '%s' "${current_json}" | parse_stats_triplet)

  delta_batches=$((post_batches - pre_batches))
  delta_in=$((post_in - pre_in))
  delta_out=$((post_out - pre_out))
  echo "Attempt ${attempt}/${max_attempts}: delta_batches=${delta_batches} delta_in=${delta_in} delta_out=${delta_out}"

  if (( delta_batches >= 1 && delta_in >= expected_in && delta_out >= expected_out )); then
    success=1
    break
  fi

  sleep "${POLL_SEC}"
done

print_stage "Result"
final_delta_batches=$((post_batches - pre_batches))
final_delta_in=$((post_in - pre_in))
final_delta_out=$((post_out - pre_out))
echo "After:  batches=${post_batches} in=${post_in} out=${post_out}"
echo "Delta:  batches=${final_delta_batches} in=${final_delta_in} out=${final_delta_out}"

if (( success == 1 )); then
  echo "SMOKE TEST PASSED"
  exit 0
fi

echo "SMOKE TEST FAILED: expected batches>=1 in>=${expected_in} out>=${expected_out}" >&2
exit 1
