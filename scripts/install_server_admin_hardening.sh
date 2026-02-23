#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
install_server_admin_hardening.sh — apply nginx/fail2ban hardening for public admin panel

Usage:
  ./scripts/install_server_admin_hardening.sh [options]

Options:
  --server-host <host>        SSH host (default: 207.180.213.225)
  --server-user <user>        SSH user (default: alis)
  --admin-token-file <path>   Local admin API token file (default: fleet/secrets/admin_api_key.txt)
  -h, --help                  Show help
EOF
}

SERVER_HOST="${SERVER_HOST:-207.180.213.225}"
SERVER_USER="${SERVER_USER:-alis}"
ADMIN_TOKEN_FILE="${ADMIN_TOKEN_FILE:-fleet/secrets/admin_api_key.txt}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --admin-token-file) ADMIN_TOKEN_FILE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ ! -f "${ADMIN_TOKEN_FILE}" ]]; then
  mkdir -p "$(dirname "${ADMIN_TOKEN_FILE}")"
  python3 - <<'PY' > "${ADMIN_TOKEN_FILE}"
import secrets
print(secrets.token_hex(24))
PY
fi
ADMIN_TOKEN="$(tr -d '\r\n' < "${ADMIN_TOKEN_FILE}")"
if [[ -z "${ADMIN_TOKEN}" ]]; then
  echo "ERROR: admin token is empty in ${ADMIN_TOKEN_FILE}" >&2
  exit 1
fi

scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/nginx/passengers-admin.conf" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-admin.conf"
scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/fail2ban/nginx-limit-req.local" "${SERVER_USER}@${SERVER_HOST}:/tmp/nginx-limit-req.local"

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "
set -euo pipefail
sudo install -m 644 -o root -g root /tmp/passengers-admin.conf /etc/nginx/conf.d/passengers-admin.conf
sudo install -m 644 -o root -g root /tmp/nginx-limit-req.local /etc/fail2ban/jail.d/nginx-limit-req.local
rm -f /tmp/passengers-admin.conf /tmp/nginx-limit-req.local
sudo rm -f /etc/nginx/conf.d/passengers-admin-token.conf
sudo tee /etc/nginx/passengers-admin-token.inc >/dev/null <<'EOF'
set \$passengers_admin_api_token \"${ADMIN_TOKEN}\";
EOF
sudo chmod 640 /etc/nginx/passengers-admin-token.inc
sudo chown root:www-data /etc/nginx/passengers-admin-token.inc
if [[ ! -f /etc/nginx/passengers-client.htpasswd && -f /etc/nginx/passengers-admin.htpasswd ]]; then
  sudo cp /etc/nginx/passengers-admin.htpasswd /etc/nginx/passengers-client.htpasswd
fi
if [[ -f /etc/nginx/passengers-client.htpasswd ]]; then
  sudo chown root:www-data /etc/nginx/passengers-client.htpasswd
  sudo chmod 640 /etc/nginx/passengers-client.htpasswd
fi
sudo nginx -t
sudo systemctl reload nginx
sudo systemctl restart fail2ban
sudo fail2ban-client status nginx-http-auth || true
sudo fail2ban-client status nginx-limit-req || true
"

echo "Admin hardening applied on ${SERVER_USER}@${SERVER_HOST}"
