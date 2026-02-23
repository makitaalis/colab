#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
server_db_restore_check.sh — verify restore from latest backend DB backup on server

Usage:
  ./scripts/server_db_restore_check.sh [options]

Options:
  --server-host <host>   SSH host (default: 207.180.213.225)
  --server-user <user>   SSH user (default: alis)
  --backup-dir <dir>     Backup directory on server (default: /opt/passengers-backend/backups)
  -h, --help             Show help
EOF
}

SERVER_HOST="${SERVER_HOST:-207.180.213.225}"
SERVER_USER="${SERVER_USER:-alis}"
BACKUP_DIR="${BACKUP_DIR:-/opt/passengers-backend/backups}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --backup-dir) BACKUP_DIR="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8)

ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "
set -euo pipefail
latest=\$(ls -1t '${BACKUP_DIR}'/passengers-*.sqlite3.gz 2>/dev/null | head -n 1)
if [[ -z \"\${latest}\" ]]; then
  echo 'ERROR: no backups found' >&2
  exit 1
fi
tmp=/tmp/passengers-restore-check-\$\$.sqlite3
gzip -dc \"\${latest}\" > \"\${tmp}\"
python3 - \"\${tmp}\" <<'PY'
import json
import sqlite3
import sys

path = sys.argv[1]
conn = sqlite3.connect(path)
try:
    integrity = conn.execute('PRAGMA integrity_check;').fetchone()[0]
    tables = [row[0] for row in conn.execute(\"SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;\").fetchall()]
    stats = {}
    for table_name in ('stops', 'stop_door_counts', 'central_heartbeats'):
        try:
            stats[table_name] = conn.execute(f'SELECT COUNT(*) FROM {table_name};').fetchone()[0]
        except Exception:
            stats[table_name] = None
    payload = {'integrity': integrity, 'tables': tables, 'counts': stats}
    print(json.dumps(payload, ensure_ascii=False))
    if integrity != 'ok':
        raise SystemExit('integrity_check failed')
finally:
    conn.close()
PY
rm -f \"\${tmp}\"
echo \"latest_backup=\${latest}\"
echo 'status=ok'
"
