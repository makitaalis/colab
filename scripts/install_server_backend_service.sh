#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
install_server_backend_service.sh — install systemd unit to keep backend Compose up after reboot

What it does:
  - installs /etc/systemd/system/passengers-backend.service
  - enables it on boot

Usage:
  ./scripts/install_server_backend_service.sh [options]

Options:
  --server-host <host>   SSH host (default: 207.180.213.225)
  --server-user <user>   SSH user (default: alis)
  -h, --help             Show help
EOF
}

SERVER_HOST="${SERVER_HOST:-207.180.213.225}"
SERVER_USER="${SERVER_USER:-alis}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8)

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/backend/passengers-backend.service" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-backend.service"

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "
set -euo pipefail
sudo apt-get update -y
if apt-cache show docker-compose-plugin >/dev/null 2>&1; then
  sudo apt-get install -y docker.io docker-compose-plugin
else
  sudo apt-get install -y docker.io docker-compose-v2
fi
sudo install -m 644 -o root -g root /tmp/passengers-backend.service /etc/systemd/system/passengers-backend.service
rm -f /tmp/passengers-backend.service
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-backend.service
sudo systemctl status passengers-backend.service --no-pager -n 40
"

echo "Backend systemd unit installed on ${SERVER_USER}@${SERVER_HOST}"
