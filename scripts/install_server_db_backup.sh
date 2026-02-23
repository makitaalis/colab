#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
install_server_db_backup.sh — install DB backup script + systemd timer on backend server

Usage:
  ./scripts/install_server_db_backup.sh [options]

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

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "sudo mkdir -p /opt/passengers-backend/ops /opt/passengers-backend/backups"

scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/backup/passengers-db-backup.sh" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-db-backup.sh"
scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/backup/passengers-db-backup.service" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-db-backup.service"
scp "${SSH_OPTS[@]}" "${REPO_ROOT}/server/backup/passengers-db-backup.timer" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-db-backup.timer"

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "
sudo install -m 750 -o root -g root /tmp/passengers-db-backup.sh /opt/passengers-backend/ops/passengers-db-backup.sh
sudo install -m 644 -o root -g root /tmp/passengers-db-backup.service /etc/systemd/system/passengers-db-backup.service
sudo install -m 644 -o root -g root /tmp/passengers-db-backup.timer /etc/systemd/system/passengers-db-backup.timer
rm -f /tmp/passengers-db-backup.sh /tmp/passengers-db-backup.service /tmp/passengers-db-backup.timer
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-db-backup.timer
sudo systemctl start passengers-db-backup.service
sudo systemctl is-active passengers-db-backup.timer passengers-db-backup.service
sudo systemctl list-timers --all | grep passengers-db-backup.timer
ls -1t /opt/passengers-backend/backups/passengers-*.sqlite3.gz | head -n 3
"

echo "Backup timer installed on ${SERVER_USER}@${SERVER_HOST}"
