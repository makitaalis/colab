#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
test_edge_central_resilience.sh — validate stage 12.1 (Edge -> Central outage and catch-up)

Usage:
  ./scripts/test_edge_central_resilience.sh [options]

Options:
  --central-ip <ip>       Central IP (default: 192.168.10.1)
  --door1-ip <ip>         Door-1 IP (default: 192.168.10.11)
  --door2-ip <ip>         Door-2 IP (default: 192.168.10.12)
  --opi-user <name>       SSH user for OPi nodes (default: orangepi)
  --events-per-door <n>   Events to enqueue on each door during outage (default: 4)
  --wait-drain-sec <n>    Max wait for edge outbox drain after restore (default: 90)
  --poll-sec <n>          Poll interval for drain checks (default: 2)
  --smoke                 Run scripts/mvp_e2e_smoke.sh after recovery
  --server-host <host>    Server host for smoke (default: 207.180.213.225)
  -h, --help              Show help
EOF
}

CENTRAL_IP="${CENTRAL_IP:-192.168.10.1}"
DOOR1_IP="${DOOR1_IP:-192.168.10.11}"
DOOR2_IP="${DOOR2_IP:-192.168.10.12}"
OPI_USER="${OPI_USER:-orangepi}"
EVENTS_PER_DOOR="${EVENTS_PER_DOOR:-4}"
WAIT_DRAIN_SEC="${WAIT_DRAIN_SEC:-90}"
POLL_SEC="${POLL_SEC:-2}"
RUN_SMOKE=0
SERVER_HOST="${SERVER_HOST:-207.180.213.225}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
    --door1-ip) DOOR1_IP="${2:-}"; shift 2 ;;
    --door2-ip) DOOR2_IP="${2:-}"; shift 2 ;;
    --opi-user) OPI_USER="${2:-}"; shift 2 ;;
    --events-per-door) EVENTS_PER_DOOR="${2:-}"; shift 2 ;;
    --wait-drain-sec) WAIT_DRAIN_SEC="${2:-}"; shift 2 ;;
    --poll-sec) POLL_SEC="${2:-}"; shift 2 ;;
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --smoke) RUN_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if ! [[ "${EVENTS_PER_DOOR}" =~ ^[0-9]+$ ]] || [[ "${EVENTS_PER_DOOR}" -lt 1 ]]; then
  echo "ERROR: --events-per-door must be integer >= 1" >&2
  exit 2
fi
if ! [[ "${WAIT_DRAIN_SEC}" =~ ^[0-9]+$ ]] || [[ "${WAIT_DRAIN_SEC}" -lt 5 ]]; then
  echo "ERROR: --wait-drain-sec must be integer >= 5" >&2
  exit 2
fi
if ! [[ "${POLL_SEC}" =~ ^[0-9]+$ ]] || [[ "${POLL_SEC}" -lt 1 ]]; then
  echo "ERROR: --poll-sec must be integer >= 1" >&2
  exit 2
fi

SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8)
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REPORT_DIR="${REPO_ROOT}/Docs/auto/transport-tests"
mkdir -p "${REPORT_DIR}"
TS_UTC="$(date -u +%Y%m%d-%H%M%SZ)"
REPORT_PATH="${REPORT_DIR}/edge-central-resilience-${TS_UTC}.md"

update_index() {
  local index="${REPORT_DIR}/INDEX.md"
  {
    echo "# Transport tests"
    echo
    find "${REPORT_DIR}" -maxdepth 1 -type f -name '*.md' ! -name 'INDEX.md' -printf '%T@ %p\n' \
      | sort -nr \
      | cut -d' ' -f2- \
      | while read -r file; do
          rel="${file#${REPO_ROOT}/}"
          echo "- \`${rel}\`"
        done
    echo
  } >"${index}"
}

ssh_central() {
  ssh "${SSH_OPTS[@]}" "${OPI_USER}@${CENTRAL_IP}" "$@"
}
ssh_door1() {
  ssh "${SSH_OPTS[@]}" "${OPI_USER}@${DOOR1_IP}" "$@"
}
ssh_door2() {
  ssh "${SSH_OPTS[@]}" "${OPI_USER}@${DOOR2_IP}" "$@"
}

count_edge_outbox() {
  local door="$1"
  if [[ "${door}" == "1" ]]; then
    ssh_door1 "python3 -c \"import sqlite3; c=sqlite3.connect('/var/lib/passengers/edge.sqlite3'); print(c.execute('select count(*) from outbox').fetchone()[0]); c.close()\""
  else
    ssh_door2 "python3 -c \"import sqlite3; c=sqlite3.connect('/var/lib/passengers/edge.sqlite3'); print(c.execute('select count(*) from outbox').fetchone()[0]); c.close()\""
  fi
}

count_central_events() {
  ssh_central "python3 -c \"import sqlite3; c=sqlite3.connect('/var/lib/passengers/central.sqlite3'); print(c.execute('select count(*) from events').fetchone()[0]); c.close()\""
}

service_state() {
  local host="$1" unit="$2"
  ssh "${SSH_OPTS[@]}" "${OPI_USER}@${host}" "systemctl is-active ${unit} 2>/dev/null || true"
}

fail=0
notes=()
add_note() { notes+=("$*"); }

cleanup() {
  ssh_central "sudo systemctl start passengers-collector.service >/dev/null 2>&1 || true" || true
}
trap cleanup EXIT

echo "== Pre-checks =="
for ip in "${CENTRAL_IP}" "${DOOR1_IP}" "${DOOR2_IP}"; do
  ping -c 1 -W 2 "${ip}" >/dev/null
done

collector_before="$(service_state "${CENTRAL_IP}" passengers-collector.service | tr -d '\r')"
edge1_before="$(service_state "${DOOR1_IP}" passengers-edge-sender.service | tr -d '\r')"
edge2_before="$(service_state "${DOOR2_IP}" passengers-edge-sender.service | tr -d '\r')"

if [[ "${collector_before}" != "active" ]]; then
  add_note "WARN: collector before test is '${collector_before}'"
fi
if [[ "${edge1_before}" != "active" || "${edge2_before}" != "active" ]]; then
  add_note "WARN: edge sender states before test: door1='${edge1_before}', door2='${edge2_before}'"
fi

base_outbox1="$(count_edge_outbox 1 | tr -d '\r')"
base_outbox2="$(count_edge_outbox 2 | tr -d '\r')"
base_events="$(count_central_events | tr -d '\r')"

echo "Base counts: outbox1=${base_outbox1} outbox2=${base_outbox2} central_events=${base_events}"

echo "== Simulate outage: stop collector on central =="
ssh_central "sudo systemctl stop passengers-collector.service"
sleep 2
collector_down="$(service_state "${CENTRAL_IP}" passengers-collector.service | tr -d '\r')"
if [[ "${collector_down}" == "active" ]]; then
  add_note "FAIL: collector failed to stop"
  fail=1
fi

echo "== Enqueue events on door nodes =="
for ((i=1; i<=EVENTS_PER_DOOR; i++)); do
  ssh_door1 "sudo python3 /opt/passengers-mvp/enqueue_event.py --door-id 2 --in 1 --out 0 >/dev/null"
  ssh_door2 "sudo python3 /opt/passengers-mvp/enqueue_event.py --door-id 3 --in 0 --out 1 >/dev/null"
done

sleep 3

outage_outbox1="$(count_edge_outbox 1 | tr -d '\r')"
outage_outbox2="$(count_edge_outbox 2 | tr -d '\r')"

min_outbox1=$((base_outbox1 + EVENTS_PER_DOOR))
min_outbox2=$((base_outbox2 + EVENTS_PER_DOOR))
if (( outage_outbox1 < min_outbox1 )); then
  add_note "FAIL: door-1 outbox during outage ${outage_outbox1} < expected ${min_outbox1}"
  fail=1
fi
if (( outage_outbox2 < min_outbox2 )); then
  add_note "FAIL: door-2 outbox during outage ${outage_outbox2} < expected ${min_outbox2}"
  fail=1
fi

echo "Outage counts: outbox1=${outage_outbox1} outbox2=${outage_outbox2}"

echo "== Restore collector and wait drain =="
ssh_central "sudo systemctl start passengers-collector.service"
sleep 2
collector_after_restore="$(service_state "${CENTRAL_IP}" passengers-collector.service | tr -d '\r')"
if [[ "${collector_after_restore}" != "active" ]]; then
  add_note "FAIL: collector did not return active (state='${collector_after_restore}')"
  fail=1
fi

drained=0
max_loops=$(( (WAIT_DRAIN_SEC + POLL_SEC - 1) / POLL_SEC ))
for ((loop=1; loop<=max_loops; loop++)); do
  now_outbox1="$(count_edge_outbox 1 | tr -d '\r')"
  now_outbox2="$(count_edge_outbox 2 | tr -d '\r')"
  echo "Drain attempt ${loop}/${max_loops}: outbox1=${now_outbox1} outbox2=${now_outbox2}"
  if (( now_outbox1 <= base_outbox1 && now_outbox2 <= base_outbox2 )); then
    drained=1
    break
  fi
  sleep "${POLL_SEC}"
done

final_outbox1="$(count_edge_outbox 1 | tr -d '\r')"
final_outbox2="$(count_edge_outbox 2 | tr -d '\r')"
final_events="$(count_central_events | tr -d '\r')"
expected_delta=$((EVENTS_PER_DOOR * 2))
actual_delta=$((final_events - base_events))

if (( drained == 0 )); then
  add_note "FAIL: outbox did not drain within ${WAIT_DRAIN_SEC}s"
  fail=1
fi
if (( actual_delta < expected_delta )); then
  add_note "FAIL: central events delta ${actual_delta} < expected ${expected_delta}"
  fail=1
fi

smoke_rc="skipped"
smoke_out=""
if (( RUN_SMOKE == 1 )); then
  echo "== Run smoke test =="
  set +e
  smoke_out="$("${REPO_ROOT}/scripts/mvp_e2e_smoke.sh" \
    --central-ip "${CENTRAL_IP}" \
    --door1-ip "${DOOR1_IP}" \
    --door2-ip "${DOOR2_IP}" \
    --server-host "${SERVER_HOST}" 2>&1)"
  smoke_rc=$?
  set -e
  if (( smoke_rc != 0 )); then
    add_note "FAIL: smoke test failed rc=${smoke_rc}"
    fail=1
  fi
fi

verdict="PASS"
if (( fail != 0 )); then
  verdict="FAIL"
fi

{
  echo "# Transport test — Edge to Central resilience"
  echo
  echo "- Timestamp (UTC): \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`"
  echo "- Verdict: **${verdict}**"
  echo "- Scenario: stop \`passengers-collector\`, enqueue on edges, restore collector, verify catch-up"
  echo
  echo "## Inputs"
  echo "- central: \`${OPI_USER}@${CENTRAL_IP}\`"
  echo "- door-1: \`${OPI_USER}@${DOOR1_IP}\`"
  echo "- door-2: \`${OPI_USER}@${DOOR2_IP}\`"
  echo "- events_per_door: \`${EVENTS_PER_DOOR}\`"
  echo "- wait_drain_sec: \`${WAIT_DRAIN_SEC}\`"
  echo
  echo "## Metrics"
  echo "- base_outbox: door-1=\`${base_outbox1}\`, door-2=\`${base_outbox2}\`"
  echo "- outage_outbox: door-1=\`${outage_outbox1}\`, door-2=\`${outage_outbox2}\`"
  echo "- final_outbox: door-1=\`${final_outbox1}\`, door-2=\`${final_outbox2}\`"
  echo "- central_events: base=\`${base_events}\`, final=\`${final_events}\`, delta=\`${actual_delta}\`"
  echo "- expected_delta: \`${expected_delta}\`"
  echo "- collector_state_before: \`${collector_before}\`"
  echo "- collector_state_during_outage: \`${collector_down}\`"
  echo "- collector_state_after_restore: \`${collector_after_restore}\`"
  echo
  echo "## Notes"
  if (( ${#notes[@]} == 0 )); then
    echo "- no warnings/errors"
  else
    for note in "${notes[@]}"; do
      echo "- ${note}"
    done
  fi
  echo
  echo "## Smoke"
  echo "- smoke_rc: \`${smoke_rc}\`"
  if [[ -n "${smoke_out}" ]]; then
    echo '```text'
    printf '%s\n' "${smoke_out}"
    echo '```'
  fi
} >"${REPORT_PATH}"

echo "Report: ${REPORT_PATH}"
echo "Verdict: ${verdict}"
update_index

if (( fail != 0 )); then
  exit 1
fi

exit 0
