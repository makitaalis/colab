#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/opt/passengers-backend/backups}"
DB_PATH="${DB_PATH:-/var/lib/docker/volumes/passengers-backend_passengers_data/_data/passengers.sqlite3}"
KEEP_LAST="${KEEP_LAST:-30}"
KEEP_DAYS="${KEEP_DAYS:-14}"

TS_UTC="$(date -u +%Y%m%d-%H%M%SZ)"
TMP_DB="/tmp/passengers-backup-${TS_UTC}.sqlite3"
OUT_GZ="${BACKUP_DIR}/passengers-${TS_UTC}.sqlite3.gz"
OUT_SUM="${OUT_GZ}.sha256"

mkdir -p "${BACKUP_DIR}"

if [[ ! -f "${DB_PATH}" ]]; then
  echo "ERROR: DB not found: ${DB_PATH}" >&2
  exit 1
fi

python3 - "${DB_PATH}" "${TMP_DB}" <<'PY'
import sqlite3
import sys

src_path, dst_path = sys.argv[1], sys.argv[2]
src = sqlite3.connect(f"file:{src_path}?mode=ro", uri=True)
dst = sqlite3.connect(dst_path)
try:
    src.backup(dst)
finally:
    dst.close()
    src.close()
PY

python3 - "${TMP_DB}" <<'PY'
import sqlite3
import sys

path = sys.argv[1]
conn = sqlite3.connect(path)
try:
    row = conn.execute("PRAGMA integrity_check;").fetchone()
    status = row[0] if row else "unknown"
    if status != "ok":
        raise SystemExit(f"integrity_check failed: {status}")
finally:
    conn.close()
PY

gzip -c "${TMP_DB}" > "${OUT_GZ}"
sha256sum "${OUT_GZ}" > "${OUT_SUM}"
rm -f "${TMP_DB}"

find "${BACKUP_DIR}" -type f -name 'passengers-*.sqlite3.gz' -mtime +"${KEEP_DAYS}" -delete || true
find "${BACKUP_DIR}" -type f -name 'passengers-*.sqlite3.gz.sha256' -mtime +"${KEEP_DAYS}" -delete || true

if [[ "${KEEP_LAST}" =~ ^[0-9]+$ ]] && [[ "${KEEP_LAST}" -gt 0 ]]; then
  ls -1t "${BACKUP_DIR}"/passengers-*.sqlite3.gz 2>/dev/null | tail -n +"$((KEEP_LAST + 1))" | xargs -r rm -f
  ls -1t "${BACKUP_DIR}"/passengers-*.sqlite3.gz.sha256 2>/dev/null | tail -n +"$((KEEP_LAST + 1))" | xargs -r rm -f
fi

echo "backup_file=${OUT_GZ}"
echo "checksum_file=${OUT_SUM}"
echo "status=ok"
