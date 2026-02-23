#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
client_scope_rollout.sh — apply CLIENT_SCOPE_BINDINGS on server

Usage:
  ./scripts/client_scope_rollout.sh --bindings "<actor:central[:vehicle],...>" [options]

Options:
  --server-host <host>       SSH host (default: 207.180.213.225)
  --server-user <user>       SSH user (default: alis)
  --bindings <value>         CLIENT_SCOPE_BINDINGS value (required)
  --admin-user <user>        Admin user for optional smoke-gate (default: admin)
  --admin-pass <pass>        Admin password for optional smoke-gate
  --admin-pass-file <path>   Read admin password from file
  --skip-smoke <0|1>         Skip smoke-gate (default: 0)
  -h, --help                 Show help
EOF
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

SERVER_HOST="207.180.213.225"
SERVER_USER="alis"
BINDINGS=""
ADMIN_USER="admin"
ADMIN_PASS=""
ADMIN_PASS_FILE=""
SKIP_SMOKE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --bindings) BINDINGS="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    --admin-pass-file) ADMIN_PASS_FILE="${2:-}"; shift 2 ;;
    --skip-smoke) SKIP_SMOKE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${BINDINGS}" ]]; then
  echo "ERROR: --bindings is required" >&2
  exit 2
fi

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

if [[ -z "${ADMIN_PASS}" && -n "${ADMIN_PASS_FILE}" ]]; then
  ADMIN_PASS="$(read_password_from_file "${ADMIN_PASS_FILE}" || true)"
fi

if [[ "${SKIP_SMOKE}" != "0" && "${SKIP_SMOKE}" != "1" ]]; then
  echo "ERROR: --skip-smoke must be 0 or 1" >&2
  exit 2
fi

echo "== Client scope rollout =="
echo "Server: ${SERVER_USER}@${SERVER_HOST}"
echo "CLIENT_SCOPE_BINDINGS=${BINDINGS}"

ssh -4 "${SERVER_USER}@${SERVER_HOST}" "BINDINGS='${BINDINGS}' bash -s" <<'REMOTE'
set -euo pipefail

if [[ ! -f /opt/passengers-backend/.env ]]; then
  echo "ERROR: /opt/passengers-backend/.env not found" >&2
  exit 1
fi

TS="$(date +%Y%m%d%H%M%S)"
ENV_BAK="/opt/passengers-backend/.env.scope.${TS}.bak"
sudo cp /opt/passengers-backend/.env "${ENV_BAK}"

if sudo grep -q '^CLIENT_SCOPE_BINDINGS=' /opt/passengers-backend/.env; then
  sudo sed -i "s|^CLIENT_SCOPE_BINDINGS=.*|CLIENT_SCOPE_BINDINGS=${BINDINGS}|" /opt/passengers-backend/.env
else
  printf '\nCLIENT_SCOPE_BINDINGS=%s\n' "${BINDINGS}" | sudo tee -a /opt/passengers-backend/.env >/dev/null
fi

cd /opt/passengers-backend
sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api >/dev/null

echo "ENV_BACKUP=${ENV_BAK}"
echo "CLIENT_SCOPE_BINDINGS_NOW=$(sudo awk -F= '/^CLIENT_SCOPE_BINDINGS=/{print $2}' /opt/passengers-backend/.env)"
REMOTE

if [[ "${SKIP_SMOKE}" == "0" ]]; then
  if [[ -n "${ADMIN_PASS}" ]]; then
    "${REPO_ROOT}/scripts/admin_panel_smoke_gate.sh" --server-host "${SERVER_HOST}" --server-user "${SERVER_USER}" --admin-user "${ADMIN_USER}" --admin-pass "${ADMIN_PASS}"
  else
    echo "WARN: smoke-gate skipped because admin password not provided"
  fi
fi

echo "Scope rollout completed."
