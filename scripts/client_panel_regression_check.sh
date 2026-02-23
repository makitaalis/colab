#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
client_panel_regression_check.sh — regression check for client panel UI/API

Usage:
  ./scripts/client_panel_regression_check.sh --admin-pass <pass> [options]
  ./scripts/client_panel_regression_check.sh --admin-pass-file <path> [options]

Options:
  --base-url <url>        Base URL (default: https://207.180.213.225:8443)
  --admin-user <user>     BasicAuth user (default: admin)
  --admin-pass <pass>     BasicAuth password
  --admin-pass-file <p>   Read password from file
  -h, --help              Show this help
EOF
}

BASE_URL="https://207.180.213.225:8443"
ADMIN_USER="admin"
ADMIN_PASS=""
ADMIN_PASS_FILE=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url) BASE_URL="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    --admin-pass-file) ADMIN_PASS_FILE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${ADMIN_PASS}" && -n "${ADMIN_PASS_FILE}" ]]; then
  if [[ ! -f "${ADMIN_PASS_FILE}" ]]; then
    echo "ERROR: --admin-pass-file not found: ${ADMIN_PASS_FILE}" >&2
    exit 2
  fi
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

curl_code() {
  local url="$1"
  shift
  curl -k -s -o /dev/null -w "%{http_code}" "$@" "${url}"
}

echo "== Client panel regression check =="
echo "Base URL: ${BASE_URL}"

failed=0

check_auth_and_anon() {
  local path="$1"
  local auth_code anon_code
  auth_code="$(curl_code "${BASE_URL}${path}" -u "${ADMIN_USER}:${ADMIN_PASS}")"
  anon_code="$(curl_code "${BASE_URL}${path}")"
  echo "${path} auth=${auth_code} anon=${anon_code}"
  if [[ "${auth_code}" != "200" || "${anon_code}" != "401" ]]; then
    failed=1
  fi
}

check_marker() {
  local path="$1"
  local pattern="$2"
  local html code len attempt
  # Marker checks can be flaky right after deploy/restart (nginx/upstream warmup).
  # Retry a few times to avoid false negatives.
  for attempt in 1 2 3; do
    code="$(curl_code "${BASE_URL}${path}" -u "${ADMIN_USER}:${ADMIN_PASS}")"
    html="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -sS "${BASE_URL}${path}" || true)"
    len="${#html}"
    if printf '%s' "${html}" | grep -Eq "${pattern}"; then
      echo "${path} marker=ok"
      return 0
    fi
    if [[ "${attempt}" != "3" ]]; then
      sleep 0.8
    fi
  done
  echo "${path} marker=missing (${pattern}) code=${code} len=${len}"
  failed=1
}

check_auth_and_anon "/client/profile"
check_auth_and_anon "/client/notifications"
check_auth_and_anon "/api/client/profile"
check_auth_and_anon "/api/client/notification-settings"

check_marker "/client/profile" "whoami|profileSupportDetails|passengers_client_profile_secondary_v1|copySupport|skipLink|sideCompactToggle|clientMainContent"
check_marker "/client/notifications" "whoami|notifySupportDetails|presetCritical|passengers_client_notifications_secondary_v1|copySupport|skipLink|sideCompactToggle|clientMainContent"

profile_json="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -sS "${BASE_URL}/api/client/profile" || true)"
notify_json="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -sS "${BASE_URL}/api/client/notification-settings" || true)"

if printf '%s' "${profile_json}" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"'; then
  echo "/api/client/profile payload=ok"
else
  echo "/api/client/profile payload=invalid"
  failed=1
fi

if printf '%s' "${notify_json}" | grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"'; then
  echo "/api/client/notification-settings payload=ok"
else
  echo "/api/client/notification-settings payload=invalid"
  failed=1
fi

if [[ "${failed}" != "0" ]]; then
  echo "RESULT: FAIL"
  exit 1
fi

echo "RESULT: PASS"
