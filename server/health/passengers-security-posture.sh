#!/usr/bin/env bash
set -euo pipefail

REPORT_DIR="${REPORT_DIR:-/opt/passengers-backend/ops-reports}"
BACKUP_DIR="${BACKUP_DIR:-/opt/passengers-backend/backups}"

CHECKS_TOTAL=0
CHECKS_FAIL=0
FAIL_NAMES=()

check_ok() {
  local name="$1"
  local cmd="$2"
  CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
  if eval "$cmd"; then
    echo "[PASS] ${name}"
  else
    echo "[FAIL] ${name}" >&2
    CHECKS_FAIL=$((CHECKS_FAIL + 1))
    FAIL_NAMES+=("${name}")
  fi
}

check_ok "ufw_active" "sudo ufw status verbose | grep -q '^Status: active'"
check_ok "ufw_ssh_limit" "sudo ufw status | grep -Eq 'OpenSSH( \\(v6\\))?[[:space:]]+LIMIT'"
check_ok "ufw_wg_allow" "sudo ufw status | grep -Eq '51820/udp( \\(v6\\))?[[:space:]]+ALLOW'"
check_ok "ufw_admin_allow" "sudo ufw status | grep -Eq '8443/tcp( \\(v6\\))?[[:space:]]+ALLOW'"
check_ok "fail2ban_jails" "sudo fail2ban-client status | grep -q 'sshd' && sudo fail2ban-client status | grep -q 'nginx-http-auth' && sudo fail2ban-client status | grep -q 'nginx-limit-req'"
check_ok "nginx_config" "sudo nginx -t >/dev/null 2>&1"
check_ok "nginx_auth_files" "sudo test -f /etc/nginx/conf.d/passengers-admin.conf && sudo test -f /etc/nginx/passengers-admin-token.inc && sudo test -f /etc/nginx/passengers-admin.htpasswd"
check_ok "critical_timers" "sudo systemctl is-active --quiet passengers-db-backup.timer && sudo systemctl is-active --quiet passengers-fleet-health-auto.timer && sudo systemctl is-active --quiet passengers-wg-export.timer"
check_ok "api_up" "cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml ps | grep -q 'passengers-backend-api-1.*Up'"
check_ok "db_backups_exist" "ls -1 ${BACKUP_DIR}/passengers-*.sqlite3.gz >/dev/null 2>&1"
check_ok "admin_protected" "curl -ksI https://127.0.0.1:8443/admin | grep -Eq '^HTTP/(1\\.1|2) 401'"
check_ok "security_header_config" "sudo grep -q 'Content-Security-Policy' /etc/nginx/conf.d/passengers-admin.conf && sudo grep -q 'Cross-Origin-Opener-Policy' /etc/nginx/conf.d/passengers-admin.conf && sudo grep -q 'Strict-Transport-Security' /etc/nginx/conf.d/passengers-admin.conf"

mkdir -p "${REPORT_DIR}"
TS_UTC="$(date -u +%Y%m%d-%H%M%SZ)"
REPORT_FILE="${REPORT_DIR}/security-posture-${TS_UTC}.json"
FAIL_LIST="$(IFS=,; echo "${FAIL_NAMES[*]:-}")"

CHECKS_TOTAL="${CHECKS_TOTAL}" CHECKS_FAIL="${CHECKS_FAIL}" FAIL_LIST="${FAIL_LIST}" TS_UTC="${TS_UTC}" python3 - "${REPORT_FILE}" <<'PY'
import json
import os
import sys

path = sys.argv[1]
payload = {
    "ts_utc": os.environ.get("TS_UTC", ""),
    "checks_total": int(os.environ.get("CHECKS_TOTAL", "0")),
    "checks_failed": int(os.environ.get("CHECKS_FAIL", "0")),
    "status": "ok" if int(os.environ.get("CHECKS_FAIL", "0")) == 0 else "fail",
    "failed_checks": [item for item in os.environ.get("FAIL_LIST", "").split(",") if item],
}
with open(path, "w", encoding="utf-8") as fh:
    json.dump(payload, fh, ensure_ascii=False, indent=2)
    fh.write("\n")
print(json.dumps(payload, ensure_ascii=False))
PY

ln -sfn "${REPORT_FILE}" "${REPORT_DIR}/security-posture-latest.json"

echo "summary: failed=${CHECKS_FAIL} total=${CHECKS_TOTAL}"
if [[ "${CHECKS_FAIL}" -gt 0 ]]; then
  exit 1
fi
