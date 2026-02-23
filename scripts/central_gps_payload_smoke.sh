#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
central_gps_payload_smoke.sh — verify that Central batches include stop.gps when GPS fix is present

This script runs on your PC and uses SSH to Central.
It will:
  1) pause passengers-gps-snapshot.timer (optional)
  2) write a mock /var/lib/passengers/gps/latest.json with fix=true
  3) insert one synthetic event into central.sqlite3
  4) run central_flush.py --no-send
  5) print stop.gps from the newest pending batch payload_json
  6) resume passengers-gps-snapshot.timer (if it was running)

Usage:
  ./scripts/central_gps_payload_smoke.sh [options]

Options:
  --central-ip <ip>   (default: 192.168.10.1)
  --user <name>       (default: orangepi)
  --lat <float>       (default: 50.4501)
  --lon <float>       (default: 30.5234)
  --keep-timer        do not stop/start gps snapshot timer
  -h, --help
USAGE
}

CENTRAL_IP="192.168.10.1"
OPI_USER="orangepi"
LAT="50.4501"
LON="30.5234"
KEEP_TIMER="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --lat) LAT="${2:-}"; shift 2 ;;
    --lon) LON="${2:-}"; shift 2 ;;
    --keep-timer) KEEP_TIMER="1"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

HOST="${OPI_USER}@${CENTRAL_IP}"
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true" >/dev/null

timer_was_active="0"
if [[ "${KEEP_TIMER}" != "1" ]]; then
  if ssh "${HOST}" "systemctl is-active --quiet passengers-gps-snapshot.timer"; then
    timer_was_active="1"
    ssh "${HOST}" "sudo systemctl stop passengers-gps-snapshot.timer"
  fi
fi

ssh "${HOST}" "sudo install -d -m 0755 /var/lib/passengers/gps
ts=\$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat <<EOF | sudo tee /var/lib/passengers/gps/latest.json >/dev/null
{\"updated_at\":\"\${ts}\",\"source\":\"mock\",\"fix\":true,\"lat\":${LAT},\"lon\":${LON}}
EOF
sudo chmod 0644 /var/lib/passengers/gps/latest.json
"

ssh "${HOST}" "python3 -" <<'PY'
import json
import sqlite3
from datetime import datetime, timezone

db = '/var/lib/passengers/central.sqlite3'
conn = sqlite3.connect(db, timeout=30)
conn.execute('PRAGMA foreign_keys=ON;')
conn.execute('PRAGMA journal_mode=WAL;')
conn.execute('PRAGMA synchronous=NORMAL;')
conn.execute('''CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  ts_received TEXT NOT NULL,
  node_id TEXT NOT NULL,
  door_id INTEGER NOT NULL,
  seq INTEGER NOT NULL,
  ts_event TEXT,
  in_count INTEGER NOT NULL,
  out_count INTEGER NOT NULL,
  confidence REAL,
  raw_json TEXT NOT NULL,
  UNIQUE(node_id, seq)
);''')

node_id = 'door-1'
door_id = 2
row = conn.execute('SELECT COALESCE(MAX(seq), 0) FROM events WHERE node_id=?;', (node_id,)).fetchone()
seq = int(row[0] or 0) + 1000
ts = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
payload = {"node_id": node_id, "door_id": door_id, "seq": seq, "ts": ts, "in": 1, "out": 0, "confidence": 0.99}
raw = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
conn.execute(
  'INSERT OR IGNORE INTO events(ts_received,node_id,door_id,seq,ts_event,in_count,out_count,confidence,raw_json) VALUES (?,?,?,?,?,?,?,?,?);',
  (ts, node_id, door_id, seq, ts, 1, 0, 0.99, raw),
)
conn.commit()
conn.close()
print('ok inserted synthetic event seq=', seq)
PY

ssh "${HOST}" "set -e; python3 /opt/passengers-mvp/central_flush.py --no-send >/dev/null; python3 -" <<'PY'
import json
import sqlite3

conn = sqlite3.connect('/var/lib/passengers/central.sqlite3', timeout=30)
conn.row_factory = sqlite3.Row
row = conn.execute("SELECT payload_json FROM batches_outbox WHERE status='pending' ORDER BY created_at DESC LIMIT 1;").fetchone()
conn.close()
if not row:
  raise SystemExit('no pending batch found')
payload = json.loads(row['payload_json'])
gps = ((payload.get('stop') or {}).get('gps') or None)
print('stop.gps =', json.dumps(gps, ensure_ascii=False))
PY

if [[ "${KEEP_TIMER}" != "1" ]]; then
  ssh "${HOST}" "sudo systemctl enable --now passengers-gps-snapshot.timer >/dev/null 2>&1 || true; sudo systemctl start passengers-gps-snapshot.timer >/dev/null 2>&1 || true"
fi

echo "OK: smoke done."
