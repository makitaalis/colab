#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
client_support_lifecycle_rollout.sh — step-12 support actor lifecycle (rotate/disable/revoke)

Usage:
  ./scripts/client_support_lifecycle_rollout.sh --action <rotate|disable|revoke> --actor <name> [options]

Options:
  --server-host <host>          SSH host (default: 207.180.213.225)
  --server-user <user>          SSH user (default: alis)
  --action <name>               rotate | disable | revoke (required)
  --actor <name>                Support actor login (required)
  --new-pass <value>            New password for rotate action
  --new-pass-file <path>        Read new password from file for rotate action
  --actor-pass <value>          Current actor password for disable/revoke verify
  --actor-pass-file <path>      Read current actor password from file
  --old-pass <value>            Old password verify for rotate (optional)
  --old-pass-file <path>        Read old password from file (optional)
  --admin-user <user>           Admin user for optional smoke-gate (default: admin)
  --admin-pass <pass>           Admin password for optional smoke-gate
  --admin-pass-file <path>      Read admin password from file
  --skip-smoke <0|1>            Skip admin_panel_smoke_gate (default: 0)
  --readiness-timeout-sec <sec> Wait timeout after api rebuild (default: 60)
  -h, --help                    Show help
USAGE
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

SERVER_HOST="207.180.213.225"
SERVER_USER="alis"
ACTION=""
ACTOR=""
NEW_PASS=""
NEW_PASS_FILE=""
ACTOR_PASS=""
ACTOR_PASS_FILE=""
OLD_PASS=""
OLD_PASS_FILE=""
ADMIN_USER="admin"
ADMIN_PASS=""
ADMIN_PASS_FILE=""
SKIP_SMOKE="0"
READINESS_TIMEOUT_SEC="60"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --action) ACTION="${2:-}"; shift 2 ;;
    --actor) ACTOR="${2:-}"; shift 2 ;;
    --new-pass) NEW_PASS="${2:-}"; shift 2 ;;
    --new-pass-file) NEW_PASS_FILE="${2:-}"; shift 2 ;;
    --actor-pass) ACTOR_PASS="${2:-}"; shift 2 ;;
    --actor-pass-file) ACTOR_PASS_FILE="${2:-}"; shift 2 ;;
    --old-pass) OLD_PASS="${2:-}"; shift 2 ;;
    --old-pass-file) OLD_PASS_FILE="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    --admin-pass-file) ADMIN_PASS_FILE="${2:-}"; shift 2 ;;
    --skip-smoke) SKIP_SMOKE="${2:-}"; shift 2 ;;
    --readiness-timeout-sec) READINESS_TIMEOUT_SEC="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

read_password_from_file() {
  local file_path="$1"
  if [[ ! -f "${file_path}" ]]; then
    return 1
  fi
  local value
  value="$(grep -m1 -E '^[[:space:]]*[-*]?[[:space:]]*(pass|password)[[:space:]]*:' "${file_path}" | sed -E 's/^[^:]*:[[:space:]]*//' || true)"
  if [[ -z "${value}" ]]; then
    value="$(head -n 1 "${file_path}" | tr -d '\r' | xargs || true)"
  fi
  printf '%s' "${value}"
}

require_zero_or_one() {
  local name="$1"
  local value="$2"
  if [[ "${value}" != "0" && "${value}" != "1" ]]; then
    echo "ERROR: ${name} must be 0 or 1" >&2
    exit 2
  fi
}

wait_for_actor_ready() {
  local actor="$1"
  local pass="$2"
  local timeout="$3"
  local waited=0
  while [[ "${waited}" -lt "${timeout}" ]]; do
    code="$(curl -k -u "${actor}:${pass}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
    if [[ "${code}" == "200" ]]; then
      return 0
    fi
    sleep 2
    waited=$((waited + 2))
  done
  return 1
}

if [[ -z "${ACTION}" || -z "${ACTOR}" ]]; then
  echo "ERROR: --action and --actor are required" >&2
  usage
  exit 2
fi

if [[ "${ACTION}" != "rotate" && "${ACTION}" != "disable" && "${ACTION}" != "revoke" ]]; then
  echo "ERROR: --action must be rotate|disable|revoke" >&2
  exit 2
fi

if [[ ! "${ACTOR}" =~ ^[a-z0-9][a-z0-9._-]*$ ]]; then
  echo "ERROR: invalid --actor value '${ACTOR}'" >&2
  exit 2
fi

require_zero_or_one "--skip-smoke" "${SKIP_SMOKE}"
if [[ ! "${READINESS_TIMEOUT_SEC}" =~ ^[0-9]+$ ]] || [[ "${READINESS_TIMEOUT_SEC}" -lt 5 ]]; then
  echo "ERROR: --readiness-timeout-sec must be integer >= 5" >&2
  exit 2
fi

if [[ -z "${NEW_PASS}" && -n "${NEW_PASS_FILE}" ]]; then
  NEW_PASS="$(read_password_from_file "${NEW_PASS_FILE}" || true)"
fi
if [[ -z "${ACTOR_PASS}" && -n "${ACTOR_PASS_FILE}" ]]; then
  ACTOR_PASS="$(read_password_from_file "${ACTOR_PASS_FILE}" || true)"
fi
if [[ -z "${OLD_PASS}" && -n "${OLD_PASS_FILE}" ]]; then
  OLD_PASS="$(read_password_from_file "${OLD_PASS_FILE}" || true)"
fi
if [[ -z "${ADMIN_PASS}" && -n "${ADMIN_PASS_FILE}" ]]; then
  ADMIN_PASS="$(read_password_from_file "${ADMIN_PASS_FILE}" || true)"
fi

if [[ "${ACTION}" == "rotate" && -z "${NEW_PASS}" ]]; then
  echo "ERROR: rotate action requires --new-pass or --new-pass-file" >&2
  exit 2
fi

if [[ "${ACTION}" != "rotate" && -z "${ACTOR_PASS}" ]]; then
  echo "ERROR: ${ACTION} action requires --actor-pass or --actor-pass-file for post-check" >&2
  exit 2
fi

if [[ "${ACTION}" == "rotate" && -z "${ACTOR_PASS}" ]]; then
  ACTOR_PASS="${NEW_PASS}"
fi

NEW_PASS_B64="$(printf '%s' "${NEW_PASS}" | base64 -w0)"

echo "== Client support lifecycle rollout =="
echo "Server: ${SERVER_USER}@${SERVER_HOST}"
echo "Action: ${ACTION}"
echo "Actor: ${ACTOR}"

if [[ "${ACTION}" == "rotate" && -n "${OLD_PASS}" ]]; then
  old_code_before="$(curl -k -u "${ACTOR}:${OLD_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
  echo "old password before rotate /api/client/whoami code=${old_code_before}"
fi

if [[ "${ACTION}" != "rotate" ]]; then
  pre_code="$(curl -k -u "${ACTOR}:${ACTOR_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
  echo "precheck /api/client/whoami code=${pre_code}"
fi

ssh -4 "${SERVER_USER}@${SERVER_HOST}" \
  "ACTION='${ACTION}' ACTOR='${ACTOR}' NEW_PASS_B64='${NEW_PASS_B64}' bash -s" <<'REMOTE'
set -euo pipefail

action="${ACTION}"
actor="${ACTOR}"
new_pass="$(printf '%s' "${NEW_PASS_B64}" | base64 -d)"

filter_csv_remove_actor() {
  local raw="$1"
  local actor_name="$2"
  printf '%s' "${raw}" \
    | tr '\n' ',' \
    | tr ',' '\n' \
    | awk -v actor_lc="$(printf '%s' "${actor_name}" | tr 'A-Z' 'a-z')" '
      NF {
        gsub(/^[ \t]+|[ \t]+$/, "", $0)
        if (tolower($0) != actor_lc) print $0
      }
    ' \
    | paste -sd, -
}

filter_scope_bindings_remove_actor() {
  local raw="$1"
  local actor_name="$2"
  printf '%s' "${raw}" \
    | tr '\n' ',' \
    | tr ',' '\n' \
    | awk -v actor_lc="$(printf '%s' "${actor_name}" | tr 'A-Z' 'a-z')" '
      NF {
        gsub(/^[ \t]+|[ \t]+$/, "", $0)
        split($0, parts, ":")
        if (tolower(parts[1]) != actor_lc) print $0
      }
    ' \
    | paste -sd, -
}

upsert_env_key() {
  local key="$1"
  local value="$2"
  local env_file="$3"
  if sudo grep -q "^${key}=" "${env_file}"; then
    sudo sed -i "s|^${key}=.*|${key}=${value}|" "${env_file}"
  else
    printf '\n%s=%s\n' "${key}" "${value}" | sudo tee -a "${env_file}" >/dev/null
  fi
}

if [[ ! -f /etc/nginx/passengers-client.htpasswd ]]; then
  sudo touch /etc/nginx/passengers-client.htpasswd
fi

if [[ "${action}" == "rotate" ]]; then
  sudo htpasswd -b /etc/nginx/passengers-client.htpasswd "${actor}" "${new_pass}" >/dev/null
  sudo chown root:www-data /etc/nginx/passengers-client.htpasswd
  sudo chmod 640 /etc/nginx/passengers-client.htpasswd
  echo "HTPASSWD_UPDATED=${actor}"
  echo "CLIENT_AUTH_USERS=$(sudo awk -F: '{print $1}' /etc/nginx/passengers-client.htpasswd | paste -sd, -)"
  exit 0
fi

sudo htpasswd -D /etc/nginx/passengers-client.htpasswd "${actor}" >/dev/null 2>&1 || true
sudo chown root:www-data /etc/nginx/passengers-client.htpasswd
sudo chmod 640 /etc/nginx/passengers-client.htpasswd

if [[ ! -f /opt/passengers-backend/.env ]]; then
  echo "ERROR: /opt/passengers-backend/.env not found" >&2
  exit 1
fi

ts="$(date +%Y%m%d%H%M%S)"
env_file="/opt/passengers-backend/.env"
env_backup="/opt/passengers-backend/.env.step12.${action}.${ts}.bak"
sudo cp "${env_file}" "${env_backup}"

current_support="$(sudo awk -F= '/^CLIENT_SUPPORT_USERS=/{print $2}' "${env_file}")"
new_support="$(filter_csv_remove_actor "${current_support}" "${actor}")"
upsert_env_key "CLIENT_SUPPORT_USERS" "${new_support}" "${env_file}"

current_scope="$(sudo awk -F= '/^CLIENT_SCOPE_BINDINGS=/{print $2}' "${env_file}")"
if [[ "${action}" == "revoke" ]]; then
  new_scope="$(filter_scope_bindings_remove_actor "${current_scope}" "${actor}")"
  upsert_env_key "CLIENT_SCOPE_BINDINGS" "${new_scope}" "${env_file}"
fi

cd /opt/passengers-backend
sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api >/dev/null

echo "ENV_BACKUP=${env_backup}"
echo "CLIENT_SUPPORT_USERS_NOW=$(sudo awk -F= '/^CLIENT_SUPPORT_USERS=/{print $2}' "${env_file}")"
echo "CLIENT_SCOPE_BINDINGS_NOW=$(sudo awk -F= '/^CLIENT_SCOPE_BINDINGS=/{print $2}' "${env_file}")"
echo "CLIENT_AUTH_USERS=$(sudo awk -F: '{print $1}' /etc/nginx/passengers-client.htpasswd | paste -sd, -)"
REMOTE

if [[ "${ACTION}" == "rotate" ]]; then
  if ! wait_for_actor_ready "${ACTOR}" "${NEW_PASS}" "${READINESS_TIMEOUT_SEC}"; then
    echo "ERROR: actor did not become ready after rotate" >&2
    exit 1
  fi
  whoami_code="$(curl -k -u "${ACTOR}:${NEW_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
  whoami_body="$(curl -k -u "${ACTOR}:${NEW_PASS}" -sS "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
  admin_code="$(curl -k -u "${ACTOR}:${NEW_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/admin/whoami" || true)"
  echo "post-rotate /api/client/whoami code=${whoami_code}"
  echo "post-rotate /api/admin/whoami code=${admin_code}"
  if [[ "${whoami_code}" != "200" ]]; then
    echo "ERROR: rotated actor cannot access client API" >&2
    exit 1
  fi
  if [[ "${whoami_body}" != *"\"role\":\"admin-support\""* ]]; then
    echo "ERROR: rotated actor role is not admin-support" >&2
    exit 1
  fi
  if [[ "${admin_code}" != "401" ]]; then
    echo "ERROR: rotated actor should not access admin API" >&2
    exit 1
  fi
  if [[ -n "${OLD_PASS}" ]]; then
    old_code_after="$(curl -k -u "${ACTOR}:${OLD_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
    echo "old password after rotate /api/client/whoami code=${old_code_after}"
    if [[ "${old_code_after}" != "401" ]]; then
      echo "ERROR: old password is still valid after rotate" >&2
      exit 1
    fi
  fi
else
  disabled_client_code="$(curl -k -u "${ACTOR}:${ACTOR_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
  disabled_admin_code="$(curl -k -u "${ACTOR}:${ACTOR_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/admin/whoami" || true)"
  echo "post-${ACTION} /api/client/whoami code=${disabled_client_code}"
  echo "post-${ACTION} /api/admin/whoami code=${disabled_admin_code}"
  if [[ "${disabled_client_code}" != "401" ]]; then
    echo "ERROR: actor should not access client API after ${ACTION}" >&2
    exit 1
  fi
  if [[ "${disabled_admin_code}" != "401" ]]; then
    echo "ERROR: actor should not access admin API after ${ACTION}" >&2
    exit 1
  fi
fi

if [[ "${SKIP_SMOKE}" == "0" ]]; then
  if [[ -n "${ADMIN_PASS}" ]]; then
    "${REPO_ROOT}/scripts/admin_panel_smoke_gate.sh" --server-host "${SERVER_HOST}" --server-user "${SERVER_USER}" --admin-user "${ADMIN_USER}" --admin-pass "${ADMIN_PASS}"
  else
    echo "WARN: smoke-gate skipped because admin password not provided"
  fi
fi

echo "RESULT: PASS"
