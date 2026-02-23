#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
client_panel_step17_handoff_check.sh — release-candidate handoff checklist for client panel

Usage:
  ./scripts/client_panel_step17_handoff_check.sh [options]

Options:
  --base-url <url>            Base URL (default: https://207.180.213.225:8443)
  --server-host <host>        SSH host (default: 207.180.213.225)
  --server-user <user>        SSH user (default: alis)
  --support-user <user>       Client/support BasicAuth user (default: support-sys-0001)
  --support-pass <pass>       Client/support password
  --support-pass-file <path>  Client/support password file
  --admin-user <user>         Admin BasicAuth user (default: admin)
  --admin-pass <pass>         Admin password
  --admin-pass-file <path>    Admin password file
  --step16-write <path>       Step-16 acceptance report output path
  --audit-write <path>        Step7b audit report output path
  --write <path>              Step-17 checklist report output path
  -h, --help                  Show help
USAGE
}

BASE_URL="https://207.180.213.225:8443"
SERVER_HOST="207.180.213.225"
SERVER_USER="alis"
SUPPORT_USER="support-sys-0001"
SUPPORT_PASS=""
SUPPORT_PASS_FILE="pass client support sys-0001 panel step13-rotated"
ADMIN_USER="admin"
ADMIN_PASS=""
ADMIN_PASS_FILE="pass admin panel"
STEP16_WRITE="Docs/auto/web-panel/client-step16-accessibility-acceptance.md"
AUDIT_WRITE="Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001-step17.md"
WRITE_PATH="Docs/auto/web-panel/client-step17-handoff-checklist.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url) BASE_URL="${2:-}"; shift 2 ;;
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --support-user) SUPPORT_USER="${2:-}"; shift 2 ;;
    --support-pass) SUPPORT_PASS="${2:-}"; shift 2 ;;
    --support-pass-file) SUPPORT_PASS_FILE="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    --admin-pass-file) ADMIN_PASS_FILE="${2:-}"; shift 2 ;;
    --step16-write) STEP16_WRITE="${2:-}"; shift 2 ;;
    --audit-write) AUDIT_WRITE="${2:-}"; shift 2 ;;
    --write) WRITE_PATH="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

extract_pass() {
  local file="$1"
  local pass=""
  if [[ ! -f "${file}" ]]; then
    return 1
  fi
  pass="$(grep -m1 -E '^[[:space:]]*[-*]?[[:space:]]*(pass|password)[[:space:]]*:' "${file}" | sed -E 's/^[^:]*:[[:space:]]*//' || true)"
  if [[ -z "${pass}" ]]; then
    pass="$(grep -m1 -E '[^[:space:]]' "${file}" | tr -d '\r' | xargs || true)"
  fi
  printf '%s' "${pass}"
}

if [[ -z "${SUPPORT_PASS}" ]]; then
  if [[ -z "${SUPPORT_PASS_FILE}" ]]; then
    echo "ERROR: support password is required (--support-pass or --support-pass-file)" >&2
    exit 2
  fi
  SUPPORT_PASS="$(extract_pass "${SUPPORT_PASS_FILE}" || true)"
fi
if [[ -z "${SUPPORT_PASS}" ]]; then
  echo "ERROR: failed to resolve support password" >&2
  exit 2
fi

if [[ -z "${ADMIN_PASS}" ]]; then
  if [[ -z "${ADMIN_PASS_FILE}" ]]; then
    echo "ERROR: admin password is required (--admin-pass or --admin-pass-file)" >&2
    exit 2
  fi
  ADMIN_PASS="$(extract_pass "${ADMIN_PASS_FILE}" || true)"
fi
if [[ -z "${ADMIN_PASS}" ]]; then
  echo "ERROR: failed to resolve admin password" >&2
  exit 2
fi

CHECK_NAMES=()
CHECK_RESULTS=()
CHECK_DETAILS=()
CHECK_LOGS=()
FAILED=0

escape_md() {
  printf '%s' "$1" | sed 's/|/\\|/g'
}

run_check() {
  local name="$1"
  shift
  local log
  log="$(mktemp)"
  local rc
  set +e
  "$@" >"${log}" 2>&1
  rc=$?
  set -e
  local marker=""
  marker="$(grep -E 'RESULT:|summary: failed=|Report written:' "${log}" | tail -n 1 || true)"
  local detail="rc=${rc}"
  if [[ -n "${marker}" ]]; then
    detail="${detail}; ${marker}"
  fi
  CHECK_NAMES+=("${name}")
  CHECK_DETAILS+=("$(escape_md "${detail}")")
  CHECK_LOGS+=("${log}")
  if [[ "${rc}" -eq 0 ]]; then
    CHECK_RESULTS+=("PASS")
    echo "[PASS] ${name}"
  else
    CHECK_RESULTS+=("FAIL")
    FAILED=1
    echo "[FAIL] ${name}" >&2
  fi
}

echo "== Client step-17 handoff checklist =="
echo "base_url=${BASE_URL}"
echo "server=${SERVER_USER}@${SERVER_HOST}"
echo "support_user=${SUPPORT_USER}"
echo "admin_user=${ADMIN_USER}"

run_check "server access (ssh+sudo)" \
  ssh -4 "${SERVER_USER}@${SERVER_HOST}" "hostname && sudo -n true"

run_check "step-16 accessibility acceptance" \
  ./scripts/client_panel_step16_accessibility_check.sh \
    --base-url "${BASE_URL}" \
    --admin-user "${SUPPORT_USER}" \
    --admin-pass "${SUPPORT_PASS}" \
    --write "${STEP16_WRITE}"

run_check "admin smoke gate" \
  ./scripts/admin_panel_smoke_gate.sh \
    --server-host "${SERVER_HOST}" \
    --server-user "${SERVER_USER}" \
    --admin-user "${ADMIN_USER}" \
    --admin-pass "${ADMIN_PASS}"

run_check "client regression check" \
  ./scripts/client_panel_regression_check.sh \
    --base-url "${BASE_URL}" \
    --admin-user "${SUPPORT_USER}" \
    --admin-pass "${SUPPORT_PASS}"

run_check "client step7b audit" \
  python3 scripts/client_panel_step7b_audit.py \
    --base-url "${BASE_URL}" \
    --admin-user "${SUPPORT_USER}" \
    --admin-pass "${SUPPORT_PASS}" \
    --write "${AUDIT_WRITE}"

run_check "server security posture" \
  ./scripts/server_security_posture_check.sh \
    --server-host "${SERVER_HOST}" \
    --server-user "${SERVER_USER}" \
    --admin-user "${ADMIN_USER}" \
    --admin-pass "${ADMIN_PASS}"

now_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
mkdir -p "$(dirname "${WRITE_PATH}")"

{
  echo "# Client Step-17 Handoff Checklist"
  echo
  echo "- generated_at_utc: \`${now_utc}\`"
  echo "- base_url: \`${BASE_URL}\`"
  echo "- server: \`${SERVER_USER}@${SERVER_HOST}\`"
  echo "- support_user: \`${SUPPORT_USER}\`"
  echo "- admin_user: \`${ADMIN_USER}\`"
  echo "- step16_report: \`${STEP16_WRITE}\`"
  echo "- step7b_report: \`${AUDIT_WRITE}\`"
  echo
  echo "## Checks"
  echo
  echo "| Check | Result | Details |"
  echo "|---|---|---|"
  for i in "${!CHECK_NAMES[@]}"; do
    echo "| \`${CHECK_NAMES[$i]}\` | \`${CHECK_RESULTS[$i]}\` | ${CHECK_DETAILS[$i]} |"
  done
  echo
  echo "## Log Tails"
  echo
  for i in "${!CHECK_NAMES[@]}"; do
    echo "### ${CHECK_NAMES[$i]}"
    echo
    echo '```text'
    tail -n 20 "${CHECK_LOGS[$i]}" || true
    echo '```'
    echo
  done
  echo "## Verdict"
  echo
  if [[ "${FAILED}" == "0" ]]; then
    echo "- status: \`PASS\`"
  else
    echo "- status: \`FAIL\`"
  fi
} > "${WRITE_PATH}"

for log in "${CHECK_LOGS[@]}"; do
  rm -f "${log}" || true
done

echo "Report written: ${WRITE_PATH}"
if [[ "${FAILED}" == "0" ]]; then
  echo "RESULT: PASS"
  exit 0
fi

echo "RESULT: FAIL"
exit 1
