#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
install_server_security_posture_timer.sh — install security posture check timer on backend server

Usage:
  ./scripts/install_server_security_posture_timer.sh [options]

Options:
  --server-host <host>   SSH host (default: 207.180.213.225)
  --server-user <user>   SSH user (default: alis)
  -h, --help             Show help
USAGE
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

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "sudo mkdir -p /opt/passengers-backend/ops /opt/passengers-backend/ops-reports"

scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/health/passengers-security-posture.sh" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-security-posture.sh"
scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/health/passengers-security-posture.service" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-security-posture.service"
scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/health/passengers-security-posture.timer" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-security-posture.timer"

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "
set -euo pipefail
sudo install -m 750 -o root -g root /tmp/passengers-security-posture.sh /opt/passengers-backend/ops/passengers-security-posture.sh
sudo install -m 644 -o root -g root /tmp/passengers-security-posture.service /etc/systemd/system/passengers-security-posture.service
sudo install -m 644 -o root -g root /tmp/passengers-security-posture.timer /etc/systemd/system/passengers-security-posture.timer
rm -f /tmp/passengers-security-posture.sh /tmp/passengers-security-posture.service /tmp/passengers-security-posture.timer
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-security-posture.timer
sudo systemctl start passengers-security-posture.service
sudo systemctl is-active passengers-security-posture.timer
sudo systemctl list-timers --all | grep passengers-security-posture.timer
sudo ls -1t /opt/passengers-backend/ops-reports/security-posture-*.json | head -n 2
"

echo "Security posture timer installed on ${SERVER_USER}@${SERVER_HOST}"
