#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
test_central_server_resilience.sh — validate stage 12.2 (Central -> Server outage and catch-up)

Usage:
  ./scripts/test_central_server_resilience.sh [options]

Options:
  --central-ip <ip>       Central IP (default: 192.168.10.1)
  --door1-ip <ip>         Door-1 IP (default: 192.168.10.11)
  --door2-ip <ip>         Door-2 IP (default: 192.168.10.12)
  --opi-user <name>       SSH user for OPi nodes (default: orangepi)
  --server-host <host>    Backend server host (default: 207.180.213.225)
  --server-user <name>    Backend server user (default: alis)
  --events-per-door <n>   Events to enqueue per door during outage (default: 2)
  --wait-drain-sec <n>    Max wait for pending batch drain (default: 120)
  --poll-sec <n>          Poll interval while waiting drain (default: 2)
  --smoke                 Run scripts/mvp_e2e_smoke.sh after recovery
  -h, --help              Show this help
EOF
}

CENTRAL_IP="${CENTRAL_IP:-192.168.10.1}"
DOOR1_IP="${DOOR1_IP:-192.168.10.11}"
DOOR2_IP="${DOOR2_IP:-192.168.10.12}"
OPI_USER="${OPI_USER:-orangepi}"
SERVER_HOST="${SERVER_HOST:-207.180.213.225}"
SERVER_USER="${SERVER_USER:-alis}"
EVENTS_PER_DOOR="${EVENTS_PER_DOOR:-2}"
WAIT_DRAIN_SEC="${WAIT_DRAIN_SEC:-120}"
POLL_SEC="${POLL_SEC:-2}"
RUN_SMOKE=0

while [[ $# -gt 0 ]]; do
  case "$1" in
    --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
    --door1-ip) DOOR1_IP="${2:-}"; shift 2 ;;
    --door2-ip) DOOR2_IP="${2:-}"; shift 2 ;;
    --opi-user) OPI_USER="${2:-}"; shift 2 ;;
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --events-per-door) EVENTS_PER_DOOR="${2:-}"; shift 2 ;;
    --wait-drain-sec) WAIT_DRAIN_SEC="${2:-}"; shift 2 ;;
    --poll-sec) POLL_SEC="${2:-}"; shift 2 ;;
    --smoke) RUN_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if ! [[ "${EVENTS_PER_DOOR}" =~ ^[0-9]+$ ]] || [[ "${EVENTS_PER_DOOR}" -lt 1 ]]; then
  echo "ERROR: --events-per-door must be integer >= 1" >&2
  exit 2
fi
if ! [[ "${WAIT_DRAIN_SEC}" =~ ^[0-9]+$ ]] || [[ "${WAIT_DRAIN_SEC}" -lt 10 ]]; then
  echo "ERROR: --wait-drain-sec must be integer >= 10" >&2
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
REPORT_PATH="${REPORT_DIR}/central-server-resilience-${TS_UTC}.md"

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

ssh_server() {
  ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "$@"
}

pending_count() {
  ssh_central "python3 -c \"import sqlite3; c=sqlite3.connect('/var/lib/passengers/central.sqlite3'); print(c.execute(\\\"select count(*) from batches_outbox where status='pending'\\\").fetchone()[0]); c.close()\""
}

sent_count() {
  ssh_central "python3 -c \"import sqlite3; c=sqlite3.connect('/var/lib/passengers/central.sqlite3'); print(c.execute(\\\"select count(*) from batches_outbox where status='sent'\\\").fetchone()[0]); c.close()\""
}

service_state() {
  local host="$1" unit="$2" user="$3"
  ssh "${SSH_OPTS[@]}" "${user}@${host}" "systemctl is-active ${unit} 2>/dev/null || true"
}

central_wg_ip() {
  ssh_central "ip -4 -o addr show dev wg0 2>/dev/null | awk '{print \$4}' | cut -d/ -f1 | head -n1"
}

wg_peer_handshake_epoch() {
  local ip="$1"
  if [[ -z "${ip}" ]]; then
    echo "0"
    return 0
  fi
  ssh_server "sudo wg show wg0 dump | awk -F'\t' -v needle='${ip}/32' 'NR>1 && index(\$4, needle)>0 {print \$5; exit}'"
}

fail=0
notes=()
add_note() { notes+=("$*"); }

cleanup() {
  ssh_central "sudo systemctl start wg-quick@wg0 >/dev/null 2>&1 || true" || true
}
trap cleanup EXIT

echo "== Pre-checks =="
for ip in "${CENTRAL_IP}" "${DOOR1_IP}" "${DOOR2_IP}"; do
  ping -c 1 -W 2 "${ip}" >/dev/null
done

uplink_before="$(service_state "${CENTRAL_IP}" passengers-central-uplink.service "${OPI_USER}" | tr -d '\r')"
wg_before="$(service_state "${CENTRAL_IP}" wg-quick@wg0.service "${OPI_USER}" | tr -d '\r')"

if [[ "${uplink_before}" != "active" ]]; then
  add_note "WARN: uplink before test is '${uplink_before}'"
fi
if [[ "${wg_before}" != "active" ]]; then
  add_note "WARN: wg before test is '${wg_before}'"
fi

base_pending="$(pending_count | tr -d '\r')"
base_sent="$(sent_count | tr -d '\r')"
wg_ip_before="$(central_wg_ip | tr -d '\r')"
handshake_before="$(wg_peer_handshake_epoch "${wg_ip_before}" | tr -d '\r')"
if [[ -z "${handshake_before}" ]]; then handshake_before="0"; fi

echo "Base counts: pending=${base_pending} sent=${base_sent} wg_ip=${wg_ip_before}"

echo "== Simulate outage: stop wg on central =="
ssh_central "sudo systemctl stop wg-quick@wg0.service"
sleep 2
wg_down="$(service_state "${CENTRAL_IP}" wg-quick@wg0.service "${OPI_USER}" | tr -d '\r')"
if [[ "${wg_down}" == "active" ]]; then
  add_note "FAIL: wg did not stop"
  fail=1
fi

echo "== Enqueue edge events and force central flush =="
for ((i=1; i<=EVENTS_PER_DOOR; i++)); do
  ssh_door1 "sudo python3 /opt/passengers-mvp/enqueue_event.py --door-id 2 --in 1 --out 0 >/dev/null"
  ssh_door2 "sudo python3 /opt/passengers-mvp/enqueue_event.py --door-id 3 --in 0 --out 1 >/dev/null"
done
sleep 3
ssh_central "sudo python3 /opt/passengers-mvp/central_flush.py --send-now --stop-mode manual >/dev/null"
sleep 2

outage_pending="$(pending_count | tr -d '\r')"
expected_pending_min=$((base_pending + 1))
if (( outage_pending < expected_pending_min )); then
  add_note "FAIL: pending during outage ${outage_pending} < expected ${expected_pending_min}"
  fail=1
fi

echo "Outage counts: pending=${outage_pending}"

echo "== Restore wg and wait pending drain =="
ssh_central "sudo systemctl start wg-quick@wg0.service"
sleep 2
wg_after_restore="$(service_state "${CENTRAL_IP}" wg-quick@wg0.service "${OPI_USER}" | tr -d '\r')"
if [[ "${wg_after_restore}" != "active" ]]; then
  add_note "FAIL: wg did not return active (state='${wg_after_restore}')"
  fail=1
fi

drained=0
max_loops=$(( (WAIT_DRAIN_SEC + POLL_SEC - 1) / POLL_SEC ))
for ((loop=1; loop<=max_loops; loop++)); do
  now_pending="$(pending_count | tr -d '\r')"
  now_sent="$(sent_count | tr -d '\r')"
  echo "Drain attempt ${loop}/${max_loops}: pending=${now_pending} sent=${now_sent}"
  if (( now_pending <= base_pending && now_sent >= base_sent + 1 )); then
    drained=1
    break
  fi
  sleep "${POLL_SEC}"
done

final_pending="$(pending_count | tr -d '\r')"
final_sent="$(sent_count | tr -d '\r')"
if (( drained == 0 )); then
  add_note "FAIL: pending did not drain within ${WAIT_DRAIN_SEC}s"
  fail=1
fi
if (( final_sent < base_sent + 1 )); then
  add_note "FAIL: sent count did not increase (base=${base_sent}, final=${final_sent})"
  fail=1
fi

wg_ip_after="$(central_wg_ip | tr -d '\r')"
handshake_after="$(wg_peer_handshake_epoch "${wg_ip_after}" | tr -d '\r')"
if [[ -z "${handshake_after}" ]]; then handshake_after="0"; fi
if (( handshake_after <= 0 )); then
  add_note "WARN: no WG handshake after restore"
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
  echo "# Transport test — Central to Server resilience"
  echo
  echo "- Timestamp (UTC): \`$(date -u +%Y-%m-%dT%H:%M:%SZ)\`"
  echo "- Verdict: **${verdict}**"
  echo "- Scenario: stop \`wg-quick@wg0\` on central, create pending batch, restore WG, verify drain"
  echo
  echo "## Inputs"
  echo "- central: \`${OPI_USER}@${CENTRAL_IP}\`"
  echo "- server: \`${SERVER_USER}@${SERVER_HOST}\`"
  echo "- door-1: \`${OPI_USER}@${DOOR1_IP}\`"
  echo "- door-2: \`${OPI_USER}@${DOOR2_IP}\`"
  echo "- events_per_door: \`${EVENTS_PER_DOOR}\`"
  echo "- wait_drain_sec: \`${WAIT_DRAIN_SEC}\`"
  echo
  echo "## Metrics"
  echo "- pending: base=\`${base_pending}\`, outage=\`${outage_pending}\`, final=\`${final_pending}\`"
  echo "- sent: base=\`${base_sent}\`, final=\`${final_sent}\`"
  echo "- wg_state: before=\`${wg_before}\`, outage=\`${wg_down}\`, restored=\`${wg_after_restore}\`"
  echo "- wg_ip: before=\`${wg_ip_before}\`, after=\`${wg_ip_after}\`"
  echo "- handshake_epoch: before=\`${handshake_before}\`, after=\`${handshake_after}\`"
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

update_index
echo "Report: ${REPORT_PATH}"
echo "Verdict: ${verdict}"

if (( fail != 0 )); then
  exit 1
fi
exit 0
