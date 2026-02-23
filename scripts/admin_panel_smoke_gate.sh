#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
admin_panel_smoke_gate.sh — unified smoke-gate for admin panel UI/API on VPS

Usage:
  ./scripts/admin_panel_smoke_gate.sh --admin-pass <pass> [options]
  ./scripts/admin_panel_smoke_gate.sh --admin-pass-file <path> [options]

Options:
  --server-host <host>    SSH host (default: 207.180.213.225)
  --server-user <user>    SSH user (default: alis)
  --admin-user <user>     Admin BasicAuth user (default: admin)
  --admin-pass <pass>     Admin BasicAuth password (required)
  --admin-pass-file <path> Read BasicAuth password from file (safer than CLI arg)
  --strict-logs <0|1>     Fail if API logs contain traceback patterns (default: 1)
  --strict-modules <0|1>  Fail if heavy pages still use legacy render path (default: 1)
  -h, --help              Show help
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

SERVER_HOST="207.180.213.225"
SERVER_USER="alis"
ADMIN_USER="admin"
ADMIN_PASS=""
ADMIN_PASS_FILE=""
STRICT_LOGS="1"
STRICT_MODULES="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    --admin-pass-file) ADMIN_PASS_FILE="${2:-}"; shift 2 ;;
    --strict-logs) STRICT_LOGS="${2:-}"; shift 2 ;;
    --strict-modules) STRICT_MODULES="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${ADMIN_PASS}" && -n "${ADMIN_PASS_FILE}" ]]; then
  if [[ ! -f "${ADMIN_PASS_FILE}" ]]; then
    echo "ERROR: --admin-pass-file not found: ${ADMIN_PASS_FILE}" >&2
    exit 2
  fi
  # Accept either raw password in the first line OR a line like: "pass: <value>" (optionally with bullet prefix).
  ADMIN_PASS="$(grep -m1 -E '^[[:space:]]*[-*]?[[:space:]]*(pass|password)[[:space:]]*:' "${ADMIN_PASS_FILE}" | sed -E 's/^[^:]*:[[:space:]]*//' || true)"
  if [[ -z "${ADMIN_PASS}" ]]; then
    ADMIN_PASS="$(head -n 1 "${ADMIN_PASS_FILE}" | tr -d '\r' | xargs || true)"
  fi
fi

if [[ -z "${ADMIN_PASS}" ]]; then
  echo "ERROR: --admin-pass or --admin-pass-file is required" >&2
  usage
  exit 2
fi

if [[ "${STRICT_MODULES}" == "1" ]]; then
  if command -v rg >/dev/null 2>&1; then
    legacy_hits="$(
      rg -n "render_legacy_admin_page\\(|legacy_html\\s*=" \
        "${REPO_ROOT}/backend/app/admin_fleet_page.py" \
        "${REPO_ROOT}/backend/app/admin_fleet_alerts_page.py" \
        "${REPO_ROOT}/backend/app/admin_fleet_incidents_page.py" \
        "${REPO_ROOT}/backend/app/admin_fleet_incident_detail_page.py" \
        "${REPO_ROOT}/backend/app/admin_fleet_central_page.py" \
        "${REPO_ROOT}/backend/app/admin_wg_page.py" || true
    )"
  else
    legacy_hits="$(
      grep -nE "render_legacy_admin_page\\(|legacy_html[[:space:]]*=" \
        "${REPO_ROOT}/backend/app/admin_fleet_page.py" \
        "${REPO_ROOT}/backend/app/admin_fleet_alerts_page.py" \
        "${REPO_ROOT}/backend/app/admin_fleet_incidents_page.py" \
        "${REPO_ROOT}/backend/app/admin_fleet_incident_detail_page.py" \
        "${REPO_ROOT}/backend/app/admin_fleet_central_page.py" \
        "${REPO_ROOT}/backend/app/admin_wg_page.py" || true
    )"
  fi
  if [[ -n "${legacy_hits}" ]]; then
    echo "LEGACY_RENDER_CHECK: failed"
    echo "${legacy_hits}"
    exit 1
  fi
  echo "LEGACY_RENDER_CHECK: ok"
fi

ADMIN_PASS_B64="$(printf '%s' "${ADMIN_PASS}" | base64 -w0)"

echo "== Admin panel smoke-gate =="
echo "Server: ${SERVER_USER}@${SERVER_HOST}"

ssh -4 "${SERVER_USER}@${SERVER_HOST}" \
  "ADMIN_USER='${ADMIN_USER}' ADMIN_PASS_B64='${ADMIN_PASS_B64}' STRICT_LOGS='${STRICT_LOGS}' bash -s" <<'REMOTE'
set -euo pipefail

BASE_URL="https://127.0.0.1:8443"
ADMIN_PASS="$(printf '%s' "${ADMIN_PASS_B64}" | base64 -d)"

echo "WARMUP"
ready=0
for _i in $(seq 1 30); do
  code="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -s -o /dev/null -w "%{http_code}" "${BASE_URL}/api/admin/whoami" || true)"
  if [[ "${code}" == "200" ]]; then
    ready=1
    break
  fi
  sleep 0.5
done
if [[ "${ready}" != "1" ]]; then
  echo "WARMUP_FAILED: /api/admin/whoami not ready"
fi

endpoints=(
  "/client"
  "/client/vehicles"
  "/client/tickets"
  "/client/status"
  "/client/profile"
  "/client/notifications"
  "/api/client/whoami"
  "/api/client/home"
  "/api/client/vehicles"
  "/api/client/tickets"
  "/api/client/status"
  "/api/client/profile"
  "/api/client/notification-settings"
  "/admin"
  "/admin/commission"
  "/admin/fleet"
  "/admin/fleet/alerts"
  "/admin/fleet/incidents"
  "/admin/fleet/notifications"
  "/admin/fleet/notify-center"
  "/admin/fleet/policy"
  "/admin/fleet/history"
  "/admin/fleet/actions"
  "/admin/audit"
  "/admin/wg"
  "/api/admin/whoami"
  "/api/admin/fleet/monitor"
  "/api/admin/fleet/centrals"
  "/api/admin/fleet/alerts/groups"
  "/api/admin/fleet/incidents"
  "/api/admin/fleet/incidents/notifications"
  "/api/admin/fleet/alerts/actions"
  "/api/admin/fleet/notification-settings"
  "/api/admin/audit"
  "/api/admin/wg/peers"
  "/api/admin/wg/conf"
)

curl_code() {
  local url="$1"
  curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -s -o /dev/null -w "%{http_code}" "${url}" || true
}

curl_code_with_retry() {
  local url="$1"
  local code=""
  local max_tries="3"
  local delay_sec="0.35"

  for attempt in $(seq 1 "${max_tries}"); do
    code="$(curl_code "${url}")"
    # nginx/conn warmups can return transient 502/503/504 (or 000 from curl).
    if [[ "${code}" == "200" ]]; then
      break
    fi
    if [[ "${code}" != "502" && "${code}" != "503" && "${code}" != "504" && "${code}" != "000" ]]; then
      break
    fi
    if [[ "${attempt}" -lt "${max_tries}" ]]; then
      echo "RETRY ${url} attempt=${attempt} code=${code}"
      sleep "${delay_sec}"
    fi
  done
  printf '%s' "${code}"
}

failed=0
for endpoint in "${endpoints[@]}"; do
  code="$(curl_code_with_retry "${BASE_URL}${endpoint}")"
  echo "${BASE_URL}${endpoint} => ${code}"
  if [[ "${code}" != "200" ]]; then
    failed=1
  fi
done

# Optional dynamic check: central detail UI/API for the first known central_id.
centrals_json="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -s "${BASE_URL}/api/admin/fleet/centrals" || true)"
first_central="$(
  python3 - <<'PY' 2>/dev/null || true
import json,sys
raw = sys.stdin.read().strip()
if not raw:
  sys.exit(0)
data = json.loads(raw)
items = data.get("centrals") or []
if not items:
  sys.exit(0)
cid = str((items[0] or {}).get("central_id") or "").strip()
if cid:
  print(cid)
PY
<<<"${centrals_json}"
)"
if [[ -n "${first_central}" ]]; then
  endpoint="/admin/fleet/central/${first_central}"
  code="$(curl_code_with_retry "${BASE_URL}${endpoint}")"
  echo "${BASE_URL}${endpoint} => ${code}"
  if [[ "${code}" != "200" ]]; then
    failed=1
  fi
  endpoint="/api/admin/fleet/central/${first_central}"
  code="$(curl_code_with_retry "${BASE_URL}${endpoint}")"
  echo "${BASE_URL}${endpoint} => ${code}"
  if [[ "${code}" != "200" ]]; then
    failed=1
  fi
else
  echo "DYNAMIC_CENTRAL_CHECK: skipped (no centrals)"
fi

# Optional dynamic check: incident detail UI/API for the first open incident.
incidents_json="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -s "${BASE_URL}/api/admin/fleet/incidents?include_resolved=0&limit=1" || true)"
first_incident="$(
  python3 - <<'PY' 2>/dev/null || true
import json,sys
raw = sys.stdin.read().strip()
if not raw:
  sys.exit(0)
data = json.loads(raw)
items = data.get("incidents") or []
if not items:
  sys.exit(0)
item = items[0] or {}
cid = str(item.get("central_id") or "").strip()
code = str(item.get("code") or "").strip()
if cid and code:
  print(cid + \"\\t\" + code)
PY
<<<"${incidents_json}"
)"
if [[ -n "${first_incident}" ]]; then
  cid="$(printf '%s' "${first_incident}" | cut -f1)"
  code_id="$(printf '%s' "${first_incident}" | cut -f2)"
  endpoint="/admin/fleet/incidents/${cid}/${code_id}"
  code="$(curl_code_with_retry "${BASE_URL}${endpoint}")"
  echo "${BASE_URL}${endpoint} => ${code}"
  if [[ "${code}" != "200" ]]; then
    failed=1
  fi
  endpoint="/api/admin/fleet/incidents/${cid}/${code_id}"
  code="$(curl_code_with_retry "${BASE_URL}${endpoint}")"
  echo "${BASE_URL}${endpoint} => ${code}"
  if [[ "${code}" != "200" ]]; then
    failed=1
  fi
else
  echo "DYNAMIC_INCIDENT_CHECK: skipped (no incidents)"
fi

echo "LOG_SCAN"
logs="$(sudo docker logs --tail 200 passengers-backend-api-1 2>&1 || true)"
if echo "${logs}" | grep -E "ResponseValidationError|Traceback|coroutine object" >/dev/null 2>&1; then
  echo "${logs}" | grep -E "ResponseValidationError|Traceback|coroutine object" || true
  if [[ "${STRICT_LOGS}" == "1" ]]; then
    failed=1
  fi
else
  echo "no_errors_found"
fi

exit "${failed}"
REMOTE
