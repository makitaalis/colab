#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
client_support_matrix_rollout.sh — step-11 multi-support onboarding rollout

Usage:
  ./scripts/client_support_matrix_rollout.sh --matrix-file <path> [options]

Matrix format (UTF-8 text, one record per line):
  actor|password_file|scope_entries

Where:
  actor         login name for /etc/nginx/passengers-client.htpasswd
  password_file local file with password (first line or pass:/password: pattern)
  scope_entries one or many entries split by ';' or ',' in form central_id[:vehicle_id]

Example:
  support-sys-0001|pass client support sys-0001 panel|sys-0001
  support-sys-0002|pass client support sys-0002 panel|sys-0002;sys-0002:veh-14

Options:
  --server-host <host>          SSH host (default: 207.180.213.225)
  --server-user <user>          SSH user (default: alis)
  --matrix-file <path>          Onboarding matrix file (required)
  --admin-user <user>           Admin BasicAuth user for optional smoke-gate (default: admin)
  --admin-pass <pass>           Admin BasicAuth password (optional)
  --admin-pass-file <path>      Read admin password from file (optional)
  --keep-admin-client-auth <0|1> Copy admin htpasswd on first rollout if client file is missing (default: 1)
  --allow-legacy-actors <0|1>   Allow actors not matching support-<system_id> (default: 0)
  --prune-legacy-support <0|1>  Remove support* users not present in matrix (default: 1)
  --readiness-timeout-sec <sec> Wait timeout for client API readiness after deploy (default: 60)
  --skip-smoke <0|1>            Skip admin_panel_smoke_gate (default: 0)
  --skip-support-regression <0|1> Skip client_panel_regression_check for first support actor (default: 0)
  -h, --help                    Show help
USAGE
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

SERVER_HOST="207.180.213.225"
SERVER_USER="alis"
MATRIX_FILE=""
ADMIN_USER="admin"
ADMIN_PASS=""
ADMIN_PASS_FILE=""
KEEP_ADMIN_CLIENT_AUTH="1"
ALLOW_LEGACY_ACTORS="0"
PRUNE_LEGACY_SUPPORT="1"
READINESS_TIMEOUT_SEC="60"
SKIP_SMOKE="0"
SKIP_SUPPORT_REGRESSION="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --matrix-file) MATRIX_FILE="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    --admin-pass-file) ADMIN_PASS_FILE="${2:-}"; shift 2 ;;
    --keep-admin-client-auth) KEEP_ADMIN_CLIENT_AUTH="${2:-}"; shift 2 ;;
    --allow-legacy-actors) ALLOW_LEGACY_ACTORS="${2:-}"; shift 2 ;;
    --prune-legacy-support) PRUNE_LEGACY_SUPPORT="${2:-}"; shift 2 ;;
    --readiness-timeout-sec) READINESS_TIMEOUT_SEC="${2:-}"; shift 2 ;;
    --skip-smoke) SKIP_SMOKE="${2:-}"; shift 2 ;;
    --skip-support-regression) SKIP_SUPPORT_REGRESSION="${2:-}"; shift 2 ;;
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

read_password_from_file() {
  local file_path="$1"
  if [[ ! -f "${file_path}" ]]; then
    return 1
  fi
  local value
  value="$(grep -m1 -E '^[[:space:]]*[-*]?[[:space:]]*(pass|password)[[:space:]]*:' "${file_path}" | sed -E 's/^[^:]*:[[:space:]]*//' || true)"
  if [[ -z "${value}" ]]; then
    value="$(head -n 1 "${file_path}" | tr -d '\r' | xargs || true)"
  fi
  printf '%s' "${value}"
}

join_by_comma() {
  local out=""
  local item
  for item in "$@"; do
    if [[ -z "${out}" ]]; then
      out="${item}"
    else
      out+=",${item}"
    fi
  done
  printf '%s' "${out}"
}

require_zero_or_one() {
  local name="$1"
  local value="$2"
  if [[ "${value}" != "0" && "${value}" != "1" ]]; then
    echo "ERROR: ${name} must be 0 or 1" >&2
    exit 2
  fi
}

if [[ -z "${MATRIX_FILE}" ]]; then
  echo "ERROR: --matrix-file is required" >&2
  usage
  exit 2
fi

if [[ ! -f "${MATRIX_FILE}" ]]; then
  echo "ERROR: matrix file not found: ${MATRIX_FILE}" >&2
  exit 2
fi

require_zero_or_one "--keep-admin-client-auth" "${KEEP_ADMIN_CLIENT_AUTH}"
require_zero_or_one "--allow-legacy-actors" "${ALLOW_LEGACY_ACTORS}"
require_zero_or_one "--prune-legacy-support" "${PRUNE_LEGACY_SUPPORT}"
require_zero_or_one "--skip-smoke" "${SKIP_SMOKE}"
require_zero_or_one "--skip-support-regression" "${SKIP_SUPPORT_REGRESSION}"
if [[ ! "${READINESS_TIMEOUT_SEC}" =~ ^[0-9]+$ ]] || [[ "${READINESS_TIMEOUT_SEC}" -lt 5 ]]; then
  echo "ERROR: --readiness-timeout-sec must be integer >= 5" >&2
  exit 2
fi

if [[ -z "${ADMIN_PASS}" && -n "${ADMIN_PASS_FILE}" ]]; then
  ADMIN_PASS="$(read_password_from_file "${ADMIN_PASS_FILE}" || true)"
fi

declare -a ACTORS=()
declare -a PASSWORDS=()
declare -a USER_PASS_ROWS=()
declare -a BINDINGS=()
declare -A ACTOR_SEEN=()
declare -A BINDING_SEEN=()
declare -A ACTOR_CENTRALS=()

line_no=0
while IFS= read -r raw_line || [[ -n "${raw_line}" ]]; do
  line_no=$((line_no + 1))
  line="$(printf '%s' "${raw_line}" | tr -d '\r')"
  stripped="$(trim "${line}")"
  if [[ -z "${stripped}" || "${stripped}" == \#* ]]; then
    continue
  fi

  IFS='|' read -r actor_raw pass_file_raw scopes_raw extra <<<"${line}"
  if [[ -n "${extra:-}" ]]; then
    echo "ERROR: invalid matrix line ${line_no} (expected 3 columns separated by '|')" >&2
    exit 2
  fi

  actor="$(trim "${actor_raw:-}")"
  pass_file="$(trim "${pass_file_raw:-}")"
  scopes_spec="$(trim "${scopes_raw:-}")"

  if [[ -z "${actor}" || -z "${pass_file}" || -z "${scopes_spec}" ]]; then
    echo "ERROR: matrix line ${line_no} has empty actor/password_file/scope_entries" >&2
    exit 2
  fi

  if [[ ! "${actor}" =~ ^[a-z0-9][a-z0-9._-]*$ ]]; then
    echo "ERROR: invalid actor '${actor}' on line ${line_no}" >&2
    exit 2
  fi

  if [[ "${ALLOW_LEGACY_ACTORS}" == "0" && ! "${actor}" =~ ^support-[a-z0-9][a-z0-9-]*$ ]]; then
    echo "ERROR: actor '${actor}' on line ${line_no} does not match policy support-<system_id>; pass --allow-legacy-actors 1 to override" >&2
    exit 2
  fi

  if [[ -n "${ACTOR_SEEN[${actor}]:-}" ]]; then
    echo "ERROR: duplicate actor '${actor}' in matrix" >&2
    exit 2
  fi
  ACTOR_SEEN["${actor}"]=1

  password="$(read_password_from_file "${pass_file}" || true)"
  if [[ -z "${password}" ]]; then
    echo "ERROR: cannot read password for actor '${actor}' from file '${pass_file}'" >&2
    exit 2
  fi

  ACTORS+=("${actor}")
  PASSWORDS+=("${password}")
  USER_PASS_ROWS+=("${actor}|$(printf '%s' "${password}" | base64 -w0)")

  scopes_csv="${scopes_spec//;/,}"
  IFS=',' read -r -a scope_items <<<"${scopes_csv}"
  valid_scope_for_actor=0
  for scope_item in "${scope_items[@]}"; do
    entry="$(trim "${scope_item}")"
    [[ -z "${entry}" ]] && continue
    if [[ ! "${entry}" =~ ^[A-Za-z0-9._-]+(:[A-Za-z0-9._-]+)?$ ]]; then
      echo "ERROR: invalid scope entry '${entry}' for actor '${actor}'" >&2
      exit 2
    fi
    binding="${actor}:${entry}"
    if [[ -z "${BINDING_SEEN[${binding}]:-}" ]]; then
      BINDING_SEEN["${binding}"]=1
      BINDINGS+=("${binding}")
    fi
    central="${entry%%:*}"
    existing_centrals="${ACTOR_CENTRALS[${actor}]:-}"
    case ",${existing_centrals}," in
      *,"${central}",*) ;;
      *)
        if [[ -n "${existing_centrals}" ]]; then
          ACTOR_CENTRALS["${actor}"]="${existing_centrals},${central}"
        else
          ACTOR_CENTRALS["${actor}"]="${central}"
        fi
        ;;
    esac
    valid_scope_for_actor=1
  done

  if [[ "${valid_scope_for_actor}" != "1" ]]; then
    echo "ERROR: actor '${actor}' has no valid scope entries" >&2
    exit 2
  fi

done <"${MATRIX_FILE}"

if [[ "${#ACTORS[@]}" -eq 0 ]]; then
  echo "ERROR: matrix has no active records" >&2
  exit 2
fi

SUPPORT_USERS="$(join_by_comma "${ACTORS[@]}")"
SCOPE_BINDINGS="$(join_by_comma "${BINDINGS[@]}")"
USER_PASS_ROWS_B64="$(printf '%s\n' "${USER_PASS_ROWS[@]}" | base64 -w0)"
SUPPORT_USERS_B64="$(printf '%s' "${SUPPORT_USERS}" | base64 -w0)"
SCOPE_BINDINGS_B64="$(printf '%s' "${SCOPE_BINDINGS}" | base64 -w0)"

echo "== Client multi-support onboarding rollout =="
echo "Server: ${SERVER_USER}@${SERVER_HOST}"
echo "Matrix file: ${MATRIX_FILE}"
echo "Actors: ${SUPPORT_USERS}"
echo "CLIENT_SCOPE_BINDINGS: ${SCOPE_BINDINGS}"

scp -q "${REPO_ROOT}/server/nginx/passengers-admin.conf" "${SERVER_USER}@${SERVER_HOST}:/tmp/passengers-admin.conf"

ssh -4 "${SERVER_USER}@${SERVER_HOST}" \
  "USER_PASS_ROWS_B64='${USER_PASS_ROWS_B64}' SUPPORT_USERS_B64='${SUPPORT_USERS_B64}' SCOPE_BINDINGS_B64='${SCOPE_BINDINGS_B64}' KEEP_ADMIN_CLIENT_AUTH='${KEEP_ADMIN_CLIENT_AUTH}' PRUNE_LEGACY_SUPPORT='${PRUNE_LEGACY_SUPPORT}' bash -s" <<'REMOTE'
set -euo pipefail

SUPPORT_USERS="$(printf '%s' "${SUPPORT_USERS_B64}" | base64 -d)"
SCOPE_BINDINGS="$(printf '%s' "${SCOPE_BINDINGS_B64}" | base64 -d)"
USER_PASS_ROWS="$(printf '%s' "${USER_PASS_ROWS_B64}" | base64 -d)"

if [[ "${KEEP_ADMIN_CLIENT_AUTH}" == "1" && ! -f /etc/nginx/passengers-client.htpasswd ]]; then
  sudo cp /etc/nginx/passengers-admin.htpasswd /etc/nginx/passengers-client.htpasswd
fi

if [[ ! -f /etc/nginx/passengers-client.htpasswd ]]; then
  sudo touch /etc/nginx/passengers-client.htpasswd
fi

if [[ "${PRUNE_LEGACY_SUPPORT}" == "1" ]]; then
  while IFS= read -r existing_user; do
    [[ -z "${existing_user}" ]] && continue
    if [[ "${existing_user}" == support* ]]; then
      case ",${SUPPORT_USERS}," in
        *,"${existing_user}",*) ;;
        *) sudo htpasswd -D /etc/nginx/passengers-client.htpasswd "${existing_user}" >/dev/null || true ;;
      esac
    fi
  done < <(sudo awk -F: '{print $1}' /etc/nginx/passengers-client.htpasswd)
fi

while IFS='|' read -r actor pass_b64; do
  [[ -z "${actor}" ]] && continue
  password="$(printf '%s' "${pass_b64}" | base64 -d)"
  sudo htpasswd -b /etc/nginx/passengers-client.htpasswd "${actor}" "${password}" >/dev/null
done <<<"${USER_PASS_ROWS}"

sudo chown root:www-data /etc/nginx/passengers-client.htpasswd
sudo chmod 640 /etc/nginx/passengers-client.htpasswd

if [[ ! -f /opt/passengers-backend/.env ]]; then
  echo "ERROR: /opt/passengers-backend/.env not found" >&2
  exit 1
fi

TS="$(date +%Y%m%d%H%M%S)"
ENV_BAK="/opt/passengers-backend/.env.step11.${TS}.bak"
sudo cp /opt/passengers-backend/.env "${ENV_BAK}"

if sudo grep -q '^CLIENT_SUPPORT_USERS=' /opt/passengers-backend/.env; then
  sudo sed -i "s|^CLIENT_SUPPORT_USERS=.*|CLIENT_SUPPORT_USERS=${SUPPORT_USERS}|" /opt/passengers-backend/.env
else
  printf '\nCLIENT_SUPPORT_USERS=%s\n' "${SUPPORT_USERS}" | sudo tee -a /opt/passengers-backend/.env >/dev/null
fi

if sudo grep -q '^CLIENT_SCOPE_BINDINGS=' /opt/passengers-backend/.env; then
  sudo sed -i "s|^CLIENT_SCOPE_BINDINGS=.*|CLIENT_SCOPE_BINDINGS=${SCOPE_BINDINGS}|" /opt/passengers-backend/.env
else
  printf '\nCLIENT_SCOPE_BINDINGS=%s\n' "${SCOPE_BINDINGS}" | sudo tee -a /opt/passengers-backend/.env >/dev/null
fi

sudo install -m 644 -o root -g root /tmp/passengers-admin.conf /etc/nginx/conf.d/passengers-admin.conf
sudo rm -f /tmp/passengers-admin.conf
sudo nginx -t
sudo systemctl reload nginx

cd /opt/passengers-backend
sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api >/dev/null

echo "ENV_BACKUP=${ENV_BAK}"
echo "CLIENT_SUPPORT_USERS_NOW=$(sudo awk -F= '/^CLIENT_SUPPORT_USERS=/{print $2}' /opt/passengers-backend/.env)"
echo "CLIENT_SCOPE_BINDINGS_NOW=$(sudo awk -F= '/^CLIENT_SCOPE_BINDINGS=/{print $2}' /opt/passengers-backend/.env)"
echo "CLIENT_AUTH_USERS=$(sudo awk -F: '{print $1}' /etc/nginx/passengers-client.htpasswd | tr '\n' ',' | sed 's/,$//')"
REMOTE

failed=0
first_actor="${ACTORS[0]}"
first_pass="${PASSWORDS[0]}"

wait_for_client_ready() {
  local actor="$1"
  local pass="$2"
  local timeout="$3"
  local waited=0
  while [[ "${waited}" -lt "${timeout}" ]]; do
    code="$(curl -k -u "${actor}:${pass}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
    if [[ "${code}" == "200" ]]; then
      return 0
    fi
    sleep 2
    waited=$((waited + 2))
  done
  return 1
}

if ! wait_for_client_ready "${first_actor}" "${first_pass}" "${READINESS_TIMEOUT_SEC}"; then
  echo "ERROR: client API did not become ready within ${READINESS_TIMEOUT_SEC}s" >&2
  failed=1
fi

for idx in "${!ACTORS[@]}"; do
  actor="${ACTORS[${idx}]}"
  pass="${PASSWORDS[${idx}]}"

  whoami_code="$(curl -k -u "${actor}:${pass}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
  whoami_body="$(curl -k -u "${actor}:${pass}" -sS "https://${SERVER_HOST}:8443/api/client/whoami" || true)"
  admin_code="$(curl -k -u "${actor}:${pass}" -s -o /dev/null -w "%{http_code}" "https://${SERVER_HOST}:8443/api/admin/whoami" || true)"

  echo "${actor} /api/client/whoami code=${whoami_code}"
  echo "${actor} /api/admin/whoami code=${admin_code}"

  if [[ "${whoami_code}" != "200" ]]; then
    echo "ERROR: ${actor} client access check failed" >&2
    failed=1
  fi

  if [[ "${whoami_body}" != *"\"role\":\"admin-support\""* ]]; then
    echo "ERROR: ${actor} role is not admin-support" >&2
    failed=1
  fi

  if [[ "${admin_code}" != "401" ]]; then
    echo "ERROR: ${actor} should not access /api/admin/whoami (expected 401)" >&2
    failed=1
  fi

  IFS=',' read -r -a expected_centrals <<<"${ACTOR_CENTRALS[${actor}]}"
  for central_id in "${expected_centrals[@]}"; do
    ctrim="$(trim "${central_id}")"
    [[ -z "${ctrim}" ]] && continue
    if [[ "${whoami_body}" != *"\"${ctrim}\""* ]]; then
      echo "ERROR: ${actor} whoami scope does not contain central '${ctrim}'" >&2
      failed=1
    fi
  done

done

if [[ "${failed}" != "0" ]]; then
  echo "RESULT: FAIL"
  exit 1
fi

if [[ "${SKIP_SUPPORT_REGRESSION}" == "0" ]]; then
  "${REPO_ROOT}/scripts/client_panel_regression_check.sh" --base-url "https://${SERVER_HOST}:8443" --admin-user "${first_actor}" --admin-pass "${first_pass}"
fi

if [[ "${SKIP_SMOKE}" == "0" ]]; then
  if [[ -n "${ADMIN_PASS}" ]]; then
    "${REPO_ROOT}/scripts/admin_panel_smoke_gate.sh" --server-host "${SERVER_HOST}" --server-user "${SERVER_USER}" --admin-user "${ADMIN_USER}" --admin-pass "${ADMIN_PASS}"
  else
    echo "WARN: smoke-gate skipped because admin password not provided"
  fi
fi

echo "RESULT: PASS"
