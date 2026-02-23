#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
install_server_fleet_health_auto.sh — install fleet health auto notify script + systemd timer on backend server

Usage:
  ./scripts/install_server_fleet_health_auto.sh [options]

Options:
  --server-host <host>   SSH host (default: 207.180.213.225)
  --server-user <user>   SSH user (default: alis)
  -h, --help             Show help
EOF
}

SERVER_HOST="${SERVER_HOST:-207.180.213.225}"
SERVER_USER="${SERVER_USER:-alis}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8)

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "sudo mkdir -p /opt/passengers-backend/ops"

scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/health/passengers-fleet-health-auto.sh" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-fleet-health-auto.sh"
scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/health/passengers-fleet-health-auto.service" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-fleet-health-auto.service"
scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/health/passengers-fleet-health-auto.timer" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-fleet-health-auto.timer"

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "
set -euo pipefail
sudo install -m 750 -o root -g root /tmp/passengers-fleet-health-auto.sh /opt/passengers-backend/ops/passengers-fleet-health-auto.sh
sudo install -m 644 -o root -g root /tmp/passengers-fleet-health-auto.service /etc/systemd/system/passengers-fleet-health-auto.service
sudo install -m 644 -o root -g root /tmp/passengers-fleet-health-auto.timer /etc/systemd/system/passengers-fleet-health-auto.timer
rm -f /tmp/passengers-fleet-health-auto.sh /tmp/passengers-fleet-health-auto.service /tmp/passengers-fleet-health-auto.timer
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-fleet-health-auto.timer
sudo systemctl start passengers-fleet-health-auto.service
sudo systemctl is-active passengers-fleet-health-auto.timer passengers-fleet-health-auto.service
sudo systemctl list-timers --all | grep passengers-fleet-health-auto.timer
"

echo "Fleet health auto timer installed on ${SERVER_USER}@${SERVER_HOST}"
