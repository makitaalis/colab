#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
server_security_posture_check.sh — verify baseline security/ops posture on backend server

Usage:
  ./scripts/server_security_posture_check.sh [options]

Options:
  --server-host <host>   SSH host (default: 207.180.213.225)
  --server-user <user>   SSH user (default: alis)
  --admin-user <user>    BasicAuth user for /admin checks (default: admin)
  --admin-pass <pass>    BasicAuth password for /admin checks (optional)
  -h, --help             Show help
USAGE
}

SERVER_HOST="${SERVER_HOST:-207.180.213.225}"
SERVER_USER="${SERVER_USER:-alis}"
ADMIN_USER="${ADMIN_USER:-admin}"
ADMIN_PASS="${ADMIN_PASS:-}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8)

run_remote_snapshot() {
  local tries=0
  local max_tries=4
  local delay=4
  while (( tries < max_tries )); do
    if ssh "${SSH_OPTS[@]}" "${SERVER_USER}@${SERVER_HOST}" "bash -s -- \"${ADMIN_USER}\" \"${ADMIN_PASS}\"" <<'REMOTE'
set -euo pipefail
ADMIN_USER="$1"
ADMIN_PASS="$2"

mark() {
  local name="$1"
  local val="$2"
  echo "CHK_${name}=${val}"
}

ufw_status="$(sudo ufw status verbose || true)"
f2b_status="$(sudo fail2ban-client status || true)"
docker_ps="$(cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml ps 2>/dev/null || true)"
timers="$(sudo systemctl is-active passengers-db-backup.timer passengers-fleet-health-auto.timer passengers-wg-export.timer 2>/dev/null || true)"

mark SSH 1
[[ "$ufw_status" =~ ^Status:\ active ]] && mark UFW_ACTIVE 1 || mark UFW_ACTIVE 0
[[ "$ufw_status" == *"22/tcp (OpenSSH)"*"LIMIT IN"* ]] && mark UFW_SSH_LIMIT 1 || mark UFW_SSH_LIMIT 0
[[ "$ufw_status" == *"51820/udp"*"ALLOW IN"* ]] && mark UFW_WG_ALLOW 1 || mark UFW_WG_ALLOW 0
[[ "$ufw_status" == *"8443/tcp"*"ALLOW IN"* ]] && mark UFW_ADMIN_ALLOW 1 || mark UFW_ADMIN_ALLOW 0
[[ "$f2b_status" == *"sshd"* && "$f2b_status" == *"nginx-http-auth"* && "$f2b_status" == *"nginx-limit-req"* ]] && mark F2B_JAILS 1 || mark F2B_JAILS 0
sudo nginx -t >/dev/null 2>&1 && mark NGINX_CONFIG 1 || mark NGINX_CONFIG 0
sudo test -f /etc/nginx/conf.d/passengers-admin.conf && sudo test -f /etc/nginx/passengers-admin-token.inc && sudo test -f /etc/nginx/passengers-admin.htpasswd && mark NGINX_AUTH_FILES 1 || mark NGINX_AUTH_FILES 0
sudo test -f /etc/nginx/passengers-client.htpasswd && mark NGINX_CLIENT_AUTH_FILE 1 || mark NGINX_CLIENT_AUTH_FILE 0
[[ "$timers" != *"inactive"* && -n "$timers" ]] && mark TIMERS 1 || mark TIMERS 0
[[ "$docker_ps" == *"passengers-backend-api-1"*"Up"* ]] && mark API_UP 1 || mark API_UP 0
ls -1 /opt/passengers-backend/backups/passengers-*.sqlite3.gz >/dev/null 2>&1 && mark BACKUPS 1 || mark BACKUPS 0

unauth_hdr="$(curl -ksI https://127.0.0.1:8443/admin || true)"
[[ "$unauth_hdr" == *"HTTP/2 401"* || "$unauth_hdr" == *"HTTP/1.1 401"* ]] && mark ADMIN_PROTECTED 1 || mark ADMIN_PROTECTED 0

if [[ -n "$ADMIN_PASS" ]]; then
  whoami="$(curl -ksS -u "$ADMIN_USER:$ADMIN_PASS" https://127.0.0.1:8443/api/admin/whoami || true)"
  [[ "$whoami" == *"\"role\""* ]] && mark ADMIN_API_AUTH 1 || mark ADMIN_API_AUTH 0

  headers="$(curl -ksS -D - -o /dev/null -u "$ADMIN_USER:$ADMIN_PASS" https://127.0.0.1:8443/admin || true)"
  [[ "$headers" == *"content-security-policy:"* || "$headers" == *"Content-Security-Policy:"* ]] && csp=1 || csp=0
  [[ "$headers" == *"x-frame-options:"* || "$headers" == *"X-Frame-Options:"* ]] && xfo=1 || xfo=0
  [[ "$headers" == *"strict-transport-security:"* || "$headers" == *"Strict-Transport-Security:"* ]] && hsts=1 || hsts=0
  [[ "$headers" == *"cross-origin-opener-policy:"* || "$headers" == *"Cross-Origin-Opener-Policy:"* ]] && coop=1 || coop=0
  [[ "$headers" == *"cross-origin-resource-policy:"* || "$headers" == *"Cross-Origin-Resource-Policy:"* ]] && corp=1 || corp=0
  if [[ "$csp" == 1 && "$xfo" == 1 && "$hsts" == 1 && "$coop" == 1 && "$corp" == 1 ]]; then
    mark SECURITY_HEADERS 1
  else
    mark SECURITY_HEADERS 0
  fi
fi
REMOTE
    then
      return 0
    fi
    tries=$((tries + 1))
    if (( tries >= max_tries )); then
      return 1
    fi
    sleep "${delay}"
  done
}

echo "== Server security posture check =="
echo "target=${SERVER_USER}@${SERVER_HOST}"

if ! SNAPSHOT="$(run_remote_snapshot)"; then
  echo "[FAIL] ssh connectivity / snapshot" >&2
  exit 1
fi

CHECKS_TOTAL=0
CHECKS_FAIL=0

print_check() {
  local key="$1"
  local label="$2"
  local required="$3"
  local value
  value="$(echo "${SNAPSHOT}" | sed -n "s/^CHK_${key}=//p" | tail -n1)"
  if [[ -z "${value}" ]]; then
    if [[ "${required}" == "yes" ]]; then
      CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
      CHECKS_FAIL=$((CHECKS_FAIL + 1))
      echo "[FAIL] ${label}" >&2
    fi
    return
  fi
  CHECKS_TOTAL=$((CHECKS_TOTAL + 1))
  if [[ "${value}" == "1" ]]; then
    echo "[PASS] ${label}"
  else
    CHECKS_FAIL=$((CHECKS_FAIL + 1))
    echo "[FAIL] ${label}" >&2
  fi
}

print_check SSH "ssh connectivity" yes
print_check UFW_ACTIVE "ufw active" yes
print_check UFW_SSH_LIMIT "ufw ssh rate-limit" yes
print_check UFW_WG_ALLOW "ufw wireguard allow" yes
print_check UFW_ADMIN_ALLOW "ufw admin port allow" yes
print_check F2B_JAILS "fail2ban jails present" yes
print_check NGINX_CONFIG "nginx config valid" yes
print_check NGINX_AUTH_FILES "nginx admin auth files present" yes
print_check NGINX_CLIENT_AUTH_FILE "nginx client auth file present" yes
print_check TIMERS "critical timers active" yes
print_check API_UP "api container up" yes
print_check BACKUPS "db backups exist" yes
print_check ADMIN_PROTECTED "admin endpoint protected by basic auth" yes

if [[ -n "${ADMIN_PASS}" ]]; then
  print_check ADMIN_API_AUTH "admin api auth proxy works" yes
  print_check SECURITY_HEADERS "security headers present on /admin" yes
fi

echo "summary: failed=${CHECKS_FAIL} total=${CHECKS_TOTAL}"
if [[ "${CHECKS_FAIL}" -gt 0 ]]; then
  exit 1
fi
