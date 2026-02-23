#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
install_client_support_lifecycle_timer.sh — install step-13 lifecycle timers on server

Usage:
  ./scripts/install_client_support_lifecycle_timer.sh [options]

Options:
  --server-host <host>   SSH host (default: 207.180.213.225)
  --server-user <user>   SSH user (default: alis)
  -h, --help             Show help
USAGE
}

SERVER_HOST="207.180.213.225"
SERVER_USER="alis"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

echo "== Install client support lifecycle timers =="
echo "target=${SERVER_USER}@${SERVER_HOST}"

ssh -4 "${SERVER_USER}@${SERVER_HOST}" 'bash -s' <<'REMOTE'
set -euo pipefail

sudo install -d -m 755 /opt/passengers-backend/ops-reports

sudo tee /usr/local/bin/passengers-client-support-inventory.sh >/dev/null <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

env_file="/opt/passengers-backend/.env"
report_file="/opt/passengers-backend/ops-reports/client-support-inventory-latest.md"
now_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

support_users=""
scope_bindings=""
if [[ -f "${env_file}" ]]; then
  support_users="$(sudo awk -F= '/^CLIENT_SUPPORT_USERS=/{print $2}' "${env_file}" | tail -n1)"
  scope_bindings="$(sudo awk -F= '/^CLIENT_SCOPE_BINDINGS=/{print $2}' "${env_file}" | tail -n1)"
fi
auth_users=""
if [[ -f /etc/nginx/passengers-client.htpasswd ]]; then
  auth_users="$(sudo awk -F: '{print $1}' /etc/nginx/passengers-client.htpasswd | paste -sd, -)"
fi

missing_auth=0
missing_scope=0
orphan_auth=0
naming_violations=0

auth_support_csv="$(printf '%s' "${auth_users}" | tr ',' '\n' | awk 'tolower($0) ~ /^support/ {print tolower($0)}' | paste -sd, -)"

while IFS= read -r actor; do
  actor="$(printf '%s' "${actor}" | xargs)"
  [[ -z "${actor}" ]] && continue
  actor_lc="$(printf '%s' "${actor}" | tr 'A-Z' 'a-z')"
  if ! printf ',%s,' "${auth_support_csv}" | grep -q ",${actor_lc},"; then
    missing_auth=$((missing_auth + 1))
  fi
  if ! printf '%s' "${scope_bindings}" | tr ',' '\n' | awk -F: -v a="${actor_lc}" 'tolower($1)==a {f=1} END{exit f?0:1}'; then
    missing_scope=$((missing_scope + 1))
  fi
  if [[ ! "${actor_lc}" =~ ^support-[a-z0-9][a-z0-9-]*$ ]]; then
    naming_violations=$((naming_violations + 1))
  fi
done < <(printf '%s' "${support_users}" | tr ',' '\n')

while IFS= read -r actor; do
  actor="$(printf '%s' "${actor}" | xargs)"
  [[ -z "${actor}" ]] && continue
  if ! printf ',%s,' "$(printf '%s' "${support_users}" | tr 'A-Z' 'a-z')" | grep -q ",${actor},"; then
    orphan_auth=$((orphan_auth + 1))
  fi
done < <(printf '%s' "${auth_support_csv}" | tr ',' '\n')

drift_total=$((missing_auth + missing_scope + orphan_auth + naming_violations))
status="PASS"
[[ "${drift_total}" -gt 0 ]] && status="FAIL"

{
  printf '# Client Support Inventory (Server Timer)\n\n'
  printf -- '- generated_at_utc: `%s`\n' "${now_utc}"
  printf -- '- source: `server:%s`\n\n' "$(hostname)"
  printf '## Raw State\n\n'
  printf -- '- `CLIENT_SUPPORT_USERS=%s`\n' "${support_users}"
  printf -- '- `CLIENT_SCOPE_BINDINGS=%s`\n' "${scope_bindings}"
  printf -- '- `CLIENT_AUTH_USERS=%s`\n\n' "${auth_users}"
  printf '## Drift Summary\n\n'
  printf -- '- missing_auth_entries: `%s`\n' "${missing_auth}"
  printf -- '- missing_scope_entries: `%s`\n' "${missing_scope}"
  printf -- '- orphan_auth_entries: `%s`\n' "${orphan_auth}"
  printf -- '- naming_violations: `%s`\n' "${naming_violations}"
  printf -- '- status: `%s`\n' "${status}"
} | sudo tee "${report_file}" >/dev/null
SCRIPT

sudo chmod 755 /usr/local/bin/passengers-client-support-inventory.sh

sudo tee /usr/local/bin/passengers-client-support-rotation-reminder.sh >/dev/null <<'SCRIPT'
#!/usr/bin/env bash
set -euo pipefail

env_file="/opt/passengers-backend/.env"
out_file="/opt/passengers-backend/ops-reports/client-support-rotation-reminder.txt"
now_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
support_users=""
if [[ -f "${env_file}" ]]; then
  support_users="$(sudo awk -F= '/^CLIENT_SUPPORT_USERS=/{print $2}' "${env_file}" | tail -n1)"
fi

{
  echo "rotation_reminder_utc=${now_utc}"
  echo "support_users=${support_users}"
  echo "action=prepare rotation plan and run scripts/client_support_rotation_batch.sh"
} | sudo tee "${out_file}" >/dev/null
SCRIPT

sudo chmod 755 /usr/local/bin/passengers-client-support-rotation-reminder.sh

sudo tee /etc/systemd/system/passengers-client-support-inventory.service >/dev/null <<'UNIT'
[Unit]
Description=Passengers client support inventory report
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/passengers-client-support-inventory.sh
UNIT

sudo tee /etc/systemd/system/passengers-client-support-inventory.timer >/dev/null <<'UNIT'
[Unit]
Description=Run passengers client support inventory report daily

[Timer]
OnCalendar=*-*-* 03:17:00 UTC
Persistent=true
Unit=passengers-client-support-inventory.service

[Install]
WantedBy=timers.target
UNIT

sudo tee /etc/systemd/system/passengers-client-support-rotation-reminder.service >/dev/null <<'UNIT'
[Unit]
Description=Passengers client support rotation reminder
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/local/bin/passengers-client-support-rotation-reminder.sh
UNIT

sudo tee /etc/systemd/system/passengers-client-support-rotation-reminder.timer >/dev/null <<'UNIT'
[Unit]
Description=Run passengers client support rotation reminder monthly

[Timer]
OnCalendar=Mon *-*-01 09:00:00 UTC
Persistent=true
Unit=passengers-client-support-rotation-reminder.service

[Install]
WantedBy=timers.target
UNIT

sudo systemctl daemon-reload
sudo systemctl enable --now passengers-client-support-inventory.timer
sudo systemctl enable --now passengers-client-support-rotation-reminder.timer
sudo systemctl start passengers-client-support-inventory.service
sudo systemctl start passengers-client-support-rotation-reminder.service

echo "INVENTORY_TIMER=$(systemctl is-active passengers-client-support-inventory.timer)"
echo "ROTATION_TIMER=$(systemctl is-active passengers-client-support-rotation-reminder.timer)"
echo "INVENTORY_REPORT=/opt/passengers-backend/ops-reports/client-support-inventory-latest.md"
echo "ROTATION_REPORT=/opt/passengers-backend/ops-reports/client-support-rotation-reminder.txt"
REMOTE

echo "Install complete."
