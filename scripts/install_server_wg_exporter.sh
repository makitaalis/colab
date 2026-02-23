#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
install_server_wg_exporter.sh — install WireGuard status exporter + systemd timer on backend server

What it does:
  - installs /opt/passengers-backend/ops/export_wg_status.py
  - installs systemd units passengers-wg-export.{service,timer}
  - enables timer (updates /opt/passengers-backend/wg/peers.json каждые ~15s)

Usage:
  ./scripts/install_server_wg_exporter.sh [options]

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

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "
set -euo pipefail
sudo apt-get update -y
sudo apt-get install -y wireguard-tools python3
sudo mkdir -p /opt/passengers-backend/ops /opt/passengers-backend/wg
"

scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/wireguard/export_wg_status.py" "${SERVER_USER}@${SERVER_HOST}:/tmp/export_wg_status.py"
scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/wireguard/passengers-wg-export.service" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-wg-export.service"
scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/wireguard/passengers-wg-export.timer" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-wg-export.timer"

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "
set -euo pipefail
sudo install -m 755 -o root -g root /tmp/export_wg_status.py /opt/passengers-backend/ops/export_wg_status.py
sudo install -m 644 -o root -g root /tmp/passengers-wg-export.service /etc/systemd/system/passengers-wg-export.service
sudo install -m 644 -o root -g root /tmp/passengers-wg-export.timer /etc/systemd/system/passengers-wg-export.timer
rm -f /tmp/export_wg_status.py /tmp/passengers-wg-export.service /tmp/passengers-wg-export.timer
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-wg-export.timer
sudo systemctl start passengers-wg-export.service
sudo systemctl is-active passengers-wg-export.timer passengers-wg-export.service
sudo head -n 30 /opt/passengers-backend/wg/peers.json || true
"

echo "WG exporter timer installed on ${SERVER_USER}@${SERVER_HOST}"

