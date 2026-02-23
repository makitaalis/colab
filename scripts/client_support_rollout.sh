#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
client_support_rollout.sh — rollout dedicated support logins for client panel

Usage:
  ./scripts/client_support_rollout.sh --support-user <user> --support-pass <pass> [options]
  ./scripts/client_support_rollout.sh --support-user <user> --support-pass-file <path> [options]

Options:
  --server-host <host>          SSH host (default: 207.180.213.225)
  --server-user <user>          SSH user (default: alis)
  --support-user <user>         Support login for client auth file (required)
  --support-pass <pass>         Support password
  --support-pass-file <path>    Read support password from file
  --support-users <csv>         Value for CLIENT_SUPPORT_USERS (default: support-user)
  --admin-user <user>           Admin BasicAuth user for verification (default: admin)
  --admin-pass <pass>           Admin BasicAuth password for verification (optional)
  --admin-pass-file <path>      Read admin password from file (optional)
  --keep-admin-client-auth <0|1> Keep admin user access in client htpasswd by copying admin file on first rollout (default: 1)
  --skip-smoke <0|1>            Skip admin_panel_smoke_gate execution (default: 0)
  -h, --help                    Show help
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

SERVER_HOST="207.180.213.225"
SERVER_USER="alis"
SUPPORT_USER=""
SUPPORT_PASS=""
SUPPORT_PASS_FILE=""
SUPPORT_USERS=""
ADMIN_USER="admin"
ADMIN_PASS=""
ADMIN_PASS_FILE=""
KEEP_ADMIN_CLIENT_AUTH="1"
SKIP_SMOKE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --support-user) SUPPORT_USER="${2:-}"; shift 2 ;;
    --support-pass) SUPPORT_PASS="${2:-}"; shift 2 ;;
    --support-pass-file) SUPPORT_PASS_FILE="${2:-}"; shift 2 ;;
    --support-users) SUPPORT_USERS="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    --admin-pass-file) ADMIN_PASS_FILE="${2:-}"; shift 2 ;;
    --keep-admin-client-auth) KEEP_ADMIN_CLIENT_AUTH="${2:-}"; shift 2 ;;
    --skip-smoke) SKIP_SMOKE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${SUPPORT_USER}" ]]; then
  echo "ERROR: --support-user is required" >&2
  exit 2
fi

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

if [[ -z "${SUPPORT_PASS}" && -n "${SUPPORT_PASS_FILE}" ]]; then
  SUPPORT_PASS="$(read_password_from_file "${SUPPORT_PASS_FILE}" || true)"
fi
if [[ -z "${SUPPORT_PASS}" ]]; then
  echo "ERROR: support password is required via --support-pass or --support-pass-file" >&2
  exit 2
fi

if [[ -z "${ADMIN_PASS}" && -n "${ADMIN_PASS_FILE}" ]]; then
  ADMIN_PASS="$(read_password_from_file "${ADMIN_PASS_FILE}" || true)"
fi

if [[ "${KEEP_ADMIN_CLIENT_AUTH}" != "0" && "${KEEP_ADMIN_CLIENT_AUTH}" != "1" ]]; then
  echo "ERROR: --keep-admin-client-auth must be 0 or 1" >&2
  exit 2
fi

if [[ "${SKIP_SMOKE}" != "0" && "${SKIP_SMOKE}" != "1" ]]; then
  echo "ERROR: --skip-smoke must be 0 or 1" >&2
  exit 2
fi

if [[ -z "${SUPPORT_USERS}" ]]; then
  SUPPORT_USERS="${SUPPORT_USER}"
fi

SUPPORT_PASS_B64="$(printf '%s' "${SUPPORT_PASS}" | base64 -w0)"

echo "== Client support rollout =="
echo "Server: ${SERVER_USER}@${SERVER_HOST}"
echo "Support user: ${SUPPORT_USER}"
echo "CLIENT_SUPPORT_USERS: ${SUPPORT_USERS}"

scp -q "${REPO_ROOT}/server/nginx/passengers-admin.conf" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-admin.conf"

ssh -4 "${SERVER_USER}@${SERVER_HOST}" \
  "SUPPORT_USER='${SUPPORT_USER}' SUPPORT_USERS='${SUPPORT_USERS}' SUPPORT_PASS_B64='${SUPPORT_PASS_B64}' KEEP_ADMIN_CLIENT_AUTH='${KEEP_ADMIN_CLIENT_AUTH}' bash -s" <<'REMOTE'
set -euo pipefail

SUPPORT_PASS="$(printf '%s' "${SUPPORT_PASS_B64}" | base64 -d)"

if [[ "${KEEP_ADMIN_CLIENT_AUTH}" == "1" && ! -f /etc/nginx/passengers-client.htpasswd ]]; then
  sudo cp /etc/nginx/passengers-admin.htpasswd /etc/nginx/passengers-client.htpasswd
fi

if [[ ! -f /etc/nginx/passengers-client.htpasswd ]]; then
  sudo touch /etc/nginx/passengers-client.htpasswd
fi

sudo htpasswd -b /etc/nginx/passengers-client.htpasswd "${SUPPORT_USER}" "${SUPPORT_PASS}" >/dev/null
sudo chown root:www-data /etc/nginx/passengers-client.htpasswd
sudo chmod 640 /etc/nginx/passengers-client.htpasswd

if [[ ! -f /opt/passengers-backend/.env ]]; then
  echo "ERROR: /opt/passengers-backend/.env not found" >&2
  exit 1
fi

TS="$(date +%Y%m%d%H%M%S)"
ENV_BAK="/opt/passengers-backend/.env.step9.${TS}.bak"
sudo cp /opt/passengers-backend/.env "${ENV_BAK}"

if sudo grep -q '^CLIENT_SUPPORT_USERS=' /opt/passengers-backend/.env; then
  sudo sed -i "s/^CLIENT_SUPPORT_USERS=.*/CLIENT_SUPPORT_USERS=${SUPPORT_USERS}/" /opt/passengers-backend/.env
else
  printf '\nCLIENT_SUPPORT_USERS=%s\n' "${SUPPORT_USERS}" | sudo tee -a /opt/passengers-backend/.env >/dev/null
fi

sudo install -m 644 -o root -g root /tmp/passengers-admin.conf /etc/nginx/conf.d/passengers-admin.conf
sudo rm -f /tmp/passengers-admin.conf
sudo nginx -t
sudo systemctl reload nginx

cd /opt/passengers-backend
sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api >/dev/null

echo "ENV_BACKUP=${ENV_BAK}"
echo "CLIENT_SUPPORT_USERS_NOW=$(sudo awk -F= '/^CLIENT_SUPPORT_USERS=/{print $2}' /opt/passengers-backend/.env)"
echo "CLIENT_AUTH_USERS=$(sudo awk -F: '{print $1}' /etc/nginx/passengers-client.htpasswd | tr '\n' ',' | sed 's/,$//')"
REMOTE

SUPPORT_CODE="$(curl -k -u "${SUPPORT_USER}:${SUPPORT_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
SUPPORT_WHOAMI="$(curl -k -u "${SUPPORT_USER}:${SUPPORT_PASS}" -sS "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
SUPPORT_ADMIN_CODE="$(curl -k -u "${SUPPORT_USER}:${SUPPORT_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/admin/whoami" || true)"

echo "support /api/client/whoami code=${SUPPORT_CODE}"
echo "support /api/admin/whoami code=${SUPPORT_ADMIN_CODE}"
echo "${SUPPORT_WHOAMI}"

if [[ "${SUPPORT_CODE}" != "200" ]]; then
  echo "ERROR: support client access check failed" >&2
  exit 1
fi

if [[ "${SUPPORT_WHOAMI}" != *"\"role\":\"admin-support\""* ]]; then
  echo "ERROR: support role is not admin-support" >&2
  exit 1
fi

if [[ "${SUPPORT_ADMIN_CODE}" != "401" ]]; then
  echo "ERROR: support user should not access /api/admin/whoami (expected 401)" >&2
  exit 1
fi

if [[ -n "${ADMIN_PASS}" ]]; then
  ADMIN_CLIENT_CODE="$(curl -k -u "${ADMIN_USER}:${ADMIN_PASS}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
  echo "admin /api/client/whoami code=${ADMIN_CLIENT_CODE}"
fi

if [[ "${SKIP_SMOKE}" == "0" ]]; then
  if [[ -n "${ADMIN_PASS}" ]]; then
    "${REPO_ROOT}/scripts/admin_panel_smoke_gate.sh" --server-host "${SERVER_HOST}" --server-user "${SERVER_USER}" --admin-user "${ADMIN_USER}" --admin-pass "${ADMIN_PASS}"
  else
    echo "WARN: smoke-gate skipped because admin password not provided"
  fi
fi

echo "Rollout completed."
