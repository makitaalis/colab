#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
client_panel_step16_accessibility_check.sh — step-16 accessibility/keyboard acceptance for client shell

Usage:
  ./scripts/client_panel_step16_accessibility_check.sh --admin-pass <pass> [options]
  ./scripts/client_panel_step16_accessibility_check.sh --admin-pass-file <path> [options]

Options:
  --base-url <url>        Base URL (default: https://207.180.213.225:8443)
  --admin-user <user>     BasicAuth user (default: support-sys-0001)
  --admin-pass <pass>     BasicAuth password
  --admin-pass-file <p>   Read password from file
  --write <path>          Markdown report output path
  -h, --help              Show this help
USAGE
}

BASE_URL="https://207.180.213.225:8443"
ADMIN_USER="support-sys-0001"
ADMIN_PASS=""
ADMIN_PASS_FILE=""
WRITE_PATH="Docs/auto/web-panel/client-step16-accessibility-acceptance.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --base-url) BASE_URL="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    --admin-pass-file) ADMIN_PASS_FILE="${2:-}"; shift 2 ;;
    --write) WRITE_PATH="${2:-}"; shift 2 ;;
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
  local code=""
  code="$(curl -k -s -o /dev/null -w "%{http_code}" "$@" "${url}" 2>/dev/null || true)"
  [[ -n "${code}" ]] || code="000"
  printf '%s' "${code}"
}

curl_code_with_retry() {
  local url="$1"
  shift
  local code=""
  local max_tries="3"
  local delay_sec="0.35"
  for attempt in $(seq 1 "${max_tries}"); do
    code="$(curl_code "${url}" "$@")"
    if [[ "${code}" == "200" || "${code}" == "401" ]]; then
      break
    fi
    if [[ "${code}" != "000" && "${code}" != "502" && "${code}" != "503" && "${code}" != "504" ]]; then
      break
    fi
    if [[ "${attempt}" -lt "${max_tries}" ]]; then
      sleep "${delay_sec}"
    fi
  done
  printf '%s' "${code}"
}

fetch_html() {
  local path="$1"
  local max_tries="3"
  local delay_sec="0.35"
  local html=""
  for attempt in $(seq 1 "${max_tries}"); do
    html="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -sS --max-time 12 "${BASE_URL}${path}" 2>/dev/null || true)"
    if [[ -n "${html}" ]]; then
      break
    fi
    if [[ "${attempt}" -lt "${max_tries}" ]]; then
      sleep "${delay_sec}"
    fi
  done
  printf '%s' "${html}"
}

failed=0
rows=()

add_row() {
  local name="$1"
  local ok="$2"
  local details="$3"
  rows+=("| \`${name}\` | \`${ok}\` | ${details} |")
}

check_auth_anon() {
  local path="$1"
  local auth_code anon_code
  auth_code="$(curl_code_with_retry "${BASE_URL}${path}" -u "${ADMIN_USER}:${ADMIN_PASS}")"
  anon_code="$(curl_code_with_retry "${BASE_URL}${path}")"
  if [[ "${auth_code}" == "200" && "${anon_code}" == "401" ]]; then
    add_row "${path} auth/anon" "PASS" "auth=${auth_code} anon=${anon_code}"
  else
    add_row "${path} auth/anon" "FAIL" "auth=${auth_code} anon=${anon_code}"
    failed=1
  fi
}

check_markers() {
  local path="$1"
  local label="$2"
  shift 2
  local html missing=()
  html="$(fetch_html "${path}")"
  for marker in "$@"; do
    if ! grep -Fq "${marker}" <<< "${html}"; then
      missing+=("${marker}")
    fi
  done
  if [[ ${#missing[@]} -eq 0 ]]; then
    add_row "${label}" "PASS" "markers=${#@}"
  else
    add_row "${label}" "FAIL" "missing=$(printf '%s; ' "${missing[@]}")"
    failed=1
  fi
}

check_auth_anon "/client"
check_auth_anon "/client/profile"
check_auth_anon "/client/notifications"
check_auth_anon "/api/client/whoami"

whoami_json="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -sS --max-time 12 "${BASE_URL}/api/client/whoami" 2>/dev/null || true)"
if [[ -z "${whoami_json}" ]]; then
  sleep 0.35
  whoami_json="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -sS --max-time 12 "${BASE_URL}/api/client/whoami" 2>/dev/null || true)"
fi
if grep -Eq '"status"[[:space:]]*:[[:space:]]*"ok"' <<< "${whoami_json}" && grep -Eq '"role"[[:space:]]*:[[:space:]]*"admin-support"' <<< "${whoami_json}"; then
  add_row "/api/client/whoami role" "PASS" "admin-support"
else
  add_row "/api/client/whoami role" "FAIL" "expected role=admin-support"
  failed=1
fi

check_markers "/client" "client shell a11y markers" \
  "class=\"skipLink\"" \
  "id=\"clientMainContent\"" \
  "id=\"sideCompactToggle\"" \
  "sideHotkeys" \
  "Alt+Shift+M" \
  "Alt+Shift+K" \
  "if (normalized === \"m\")" \
  "if (normalized === \"k\")" \
  "if (normalized === \"s\")" \
  "if (normalized === \"t\")" \
  "key === \"Escape\""

check_markers "/client/profile" "profile copy markers" \
  "profileSupportDetails" \
  "Контур доступу" \
  "Попередній перегляд payload" \
  'контакт=${hasContact ? "готовий" : "відсутній"}'

check_markers "/client/notifications" "notifications copy markers" \
  "notifySupportDetails" \
  "Шаблон: критично" \
  "Шаблон: збалансовано" \
  "Шаблон: реальний час" \
  "контекст: канали=" \
  "пріоритет=" \
  "дайджест="

now_utc="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"
mkdir -p "$(dirname "${WRITE_PATH}")"

{
  echo "# Client Step-16 Accessibility Acceptance"
  echo
  echo "- generated_at_utc: \`${now_utc}\`"
  echo "- base_url: \`${BASE_URL}\`"
  echo "- actor: \`${ADMIN_USER}\`"
  echo
  echo "## Checks"
  echo
  echo "| Check | Result | Details |"
  echo "|---|---|---|"
  printf '%s\n' "${rows[@]}"
  echo
  echo "## Keyboard-Only Operator Scenario"
  echo
  echo "1. Open any client page and press \`/\` -> toolbar search/input gets focus."
  echo "2. Press \`Esc\` in focused input -> focus leaves editable field."
  echo "3. Press \`Alt+Shift+M\` -> sidebar compact mode toggles."
  echo "4. Press \`Alt+Shift+K\` -> table columns toggle switches base/detailed mode."
  echo "5. Press \`Alt+Shift+S\` -> focus moves to active/first sidebar link."
  echo "6. Press \`Alt+Shift+T\` -> focus moves to primary toolbar action."
  echo
  echo "## Verdict"
  echo
  if [[ "${failed}" == "0" ]]; then
    echo "- status: \`PASS\`"
  else
    echo "- status: \`FAIL\`"
  fi
} > "${WRITE_PATH}"

echo "Report written: ${WRITE_PATH}"
if [[ "${failed}" == "0" ]]; then
  echo "RESULT: PASS"
  exit 0
fi

echo "RESULT: FAIL"
exit 1
