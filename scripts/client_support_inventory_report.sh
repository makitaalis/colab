#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
client_support_inventory_report.sh — step-13 support actor inventory/drift report

Usage:
  ./scripts/client_support_inventory_report.sh [options]

Options:
  --server-host <host>   SSH host (default: 207.180.213.225)
  --server-user <user>   SSH user (default: alis)
  --write <path>         Output markdown path (default: Docs/auto/web-panel/client-support-inventory-latest.md)
  -h, --help             Show help
USAGE
}

SERVER_HOST="207.180.213.225"
SERVER_USER="alis"
WRITE_PATH="Docs/auto/web-panel/client-support-inventory-latest.md"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --write) WRITE_PATH="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

trim() {
  local s="$1"
  s="${s#"${s%%[![:space:]]*}"}"
  s="${s%"${s##*[![:space:]]}"}"
  printf '%s' "$s"
}

csv_to_lines() {
  local raw="$1"
  while IFS= read -r item || [[ -n "${item}" ]]; do
    item="$(trim "${item}")"
    [[ -n "${item}" ]] && printf '%s\n' "${item}"
  done < <(printf '%s' "${raw}" | tr ',' '\n')
}

remote_payload="$(ssh -4 "${SERVER_USER}@${SERVER_HOST}" 'bash -s' <<'REMOTE'
set -euo pipefail
now_utc="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
env_file="/opt/passengers-backend/.env"
support_users=""
scope_bindings=""
if [[ -f "${env_file}" ]]; then
  support_users="$(sudo awk -F= '/^CLIENT_SUPPORT_USERS=/{print $2}' "${env_file}" | tail -n1)"
  scope_bindings="$(sudo awk -F= '/^CLIENT_SCOPE_BINDINGS=/{print $2}' "${env_file}" | tail -n1)"
fi
client_auth_users=""
if [[ -f /etc/nginx/passengers-client.htpasswd ]]; then
  client_auth_users="$(sudo awk -F: '{print $1}' /etc/nginx/passengers-client.htpasswd | paste -sd, -)"
fi
printf 'NOW_UTC=%s\n' "${now_utc}"
printf 'CLIENT_SUPPORT_USERS=%s\n' "${support_users}"
printf 'CLIENT_SCOPE_BINDINGS=%s\n' "${scope_bindings}"
printf 'CLIENT_AUTH_USERS=%s\n' "${client_auth_users}"
REMOTE
)"

now_utc="$(printf '%s\n' "${remote_payload}" | awk -F= '/^NOW_UTC=/{sub(/^NOW_UTC=/,"");print}' | tail -n1)"
support_csv="$(printf '%s\n' "${remote_payload}" | awk -F= '/^CLIENT_SUPPORT_USERS=/{sub(/^CLIENT_SUPPORT_USERS=/,"");print}' | tail -n1)"
scope_csv="$(printf '%s\n' "${remote_payload}" | awk -F= '/^CLIENT_SCOPE_BINDINGS=/{sub(/^CLIENT_SCOPE_BINDINGS=/,"");print}' | tail -n1)"
auth_csv="$(printf '%s\n' "${remote_payload}" | awk -F= '/^CLIENT_AUTH_USERS=/{sub(/^CLIENT_AUTH_USERS=/,"");print}' | tail -n1)"

declare -A actor_in_support=()
declare -A actor_in_auth=()
declare -A actor_scope_count=()
declare -A actor_scope_preview=()
declare -A actor_seen=()

while IFS= read -r actor; do
  actor_lc="$(printf '%s' "${actor}" | tr 'A-Z' 'a-z')"
  [[ -z "${actor_lc}" ]] && continue
  actor_in_support["${actor_lc}"]=1
  actor_seen["${actor_lc}"]=1
done < <(csv_to_lines "${support_csv}")

while IFS= read -r user; do
  user_lc="$(printf '%s' "${user}" | tr 'A-Z' 'a-z')"
  [[ -z "${user_lc}" ]] && continue
  if [[ "${user_lc}" == support* ]]; then
    actor_in_auth["${user_lc}"]=1
    actor_seen["${user_lc}"]=1
  fi
done < <(csv_to_lines "${auth_csv}")

while IFS= read -r binding; do
  token="$(trim "${binding}")"
  [[ -z "${token}" ]] && continue
  actor_part="${token%%:*}"
  actor_part="$(printf '%s' "${actor_part}" | tr 'A-Z' 'a-z')"
  [[ -z "${actor_part}" ]] && continue
  actor_seen["${actor_part}"]=1
  actor_scope_count["${actor_part}"]="$(( ${actor_scope_count[${actor_part}]:-0} + 1 ))"
  preview="${actor_scope_preview[${actor_part}]:-}"
  if [[ -z "${preview}" ]]; then
    actor_scope_preview["${actor_part}"]="${token}"
  else
    count_preview=$(printf '%s' "${preview}" | awk -F',' '{print NF}')
    if [[ "${count_preview}" -lt 3 ]]; then
      actor_scope_preview["${actor_part}"]="${preview},${token}"
    fi
  fi
done < <(csv_to_lines "${scope_csv}")

mkdir -p "$(dirname -- "${WRITE_PATH}")"

{
  echo "# Client Support Inventory"
  echo
  echo "- generated_at_utc: \`${now_utc}\`"
  echo "- server: \`${SERVER_HOST}\`"
  echo
  echo "## Raw State"
  echo
  echo "- \`CLIENT_SUPPORT_USERS=${support_csv}\`"
  echo "- \`CLIENT_SCOPE_BINDINGS=${scope_csv}\`"
  echo "- \`CLIENT_AUTH_USERS=${auth_csv}\`"
  echo
  echo "## Actor Matrix"
  echo
  echo "| actor | in_support_env | in_client_htpasswd | scope_entries | scope_preview | policy |"
  echo "|---|---|---|---:|---|---|"

  if [[ "${#actor_seen[@]}" -eq 0 ]]; then
    echo "| (none) | no | no | 0 | - | n/a |"
  else
    while IFS= read -r actor; do
      [[ -z "${actor}" ]] && continue
      in_support="no"
      in_auth="no"
      scope_count="${actor_scope_count[${actor}]:-0}"
      preview="${actor_scope_preview[${actor}]:--}"
      policy="ok"
      [[ -n "${actor_in_support[${actor}]:-}" ]] && in_support="yes"
      [[ -n "${actor_in_auth[${actor}]:-}" ]] && in_auth="yes"
      if [[ ! "${actor}" =~ ^support-[a-z0-9][a-z0-9-]*$ ]]; then
        policy="naming-violation"
      fi
      echo "| \`${actor}\` | ${in_support} | ${in_auth} | ${scope_count} | \`${preview}\` | ${policy} |"
    done < <(printf '%s\n' "${!actor_seen[@]}" | sort)
  fi

  missing_auth=0
  missing_scope=0
  orphan_auth=0
  orphan_scope=0
  naming_violations=0

  for actor in "${!actor_seen[@]}"; do
    [[ -n "${actor_in_support[${actor}]:-}" && -z "${actor_in_auth[${actor}]:-}" ]] && missing_auth=$((missing_auth + 1))
    [[ -n "${actor_in_support[${actor}]:-}" && "${actor_scope_count[${actor}]:-0}" -eq 0 ]] && missing_scope=$((missing_scope + 1))
    [[ -z "${actor_in_support[${actor}]:-}" && -n "${actor_in_auth[${actor}]:-}" ]] && orphan_auth=$((orphan_auth + 1))
    [[ -z "${actor_in_support[${actor}]:-}" && "${actor_scope_count[${actor}]:-0}" -gt 0 ]] && orphan_scope=$((orphan_scope + 1))
    [[ ! "${actor}" =~ ^support-[a-z0-9][a-z0-9-]*$ ]] && naming_violations=$((naming_violations + 1))
  done

  echo
  echo "## Drift Summary"
  echo
  echo "- missing_auth_entries: \`${missing_auth}\`"
  echo "- missing_scope_entries: \`${missing_scope}\`"
  echo "- orphan_auth_entries: \`${orphan_auth}\`"
  echo "- orphan_scope_entries: \`${orphan_scope}\`"
  echo "- naming_violations: \`${naming_violations}\`"

  drift_total=$((missing_auth + missing_scope + orphan_auth + orphan_scope + naming_violations))
  if [[ "${drift_total}" -eq 0 ]]; then
    echo "- status: \`PASS\`"
  else
    echo "- status: \`FAIL\`"
  fi
} >"${WRITE_PATH}"

echo "Report written: ${WRITE_PATH}"
