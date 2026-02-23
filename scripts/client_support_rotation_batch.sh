#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
client_support_rotation_batch.sh — step-13 batch password rotation for support actors

Usage:
  ./scripts/client_support_rotation_batch.sh --plan-file <path> [options]

Plan format (UTF-8 text, one record per line):
  actor|new_password_file|old_password_file

Where:
  actor              support actor name (support-<system_id>)
  new_password_file  local file with new password
  old_password_file  local file with old password (optional but recommended)

Options:
  --server-host <host>          SSH host (default: 207.180.213.225)
  --server-user <user>          SSH user (default: alis)
  --plan-file <path>            Rotation plan file (required)
  --admin-user <user>           Admin user for optional smoke-gate (default: admin)
  --admin-pass <pass>           Admin password for optional smoke-gate
  --admin-pass-file <path>      Read admin password from file
  --skip-smoke <0|1>            Skip smoke gate after batch (default: 0)
  --readiness-timeout-sec <sec> API readiness timeout per actor (default: 60)
  -h, --help                    Show help
USAGE
}

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd -- "${SCRIPT_DIR}/.." && pwd)"

SERVER_HOST="207.180.213.225"
SERVER_USER="alis"
PLAN_FILE=""
ADMIN_USER="admin"
ADMIN_PASS=""
ADMIN_PASS_FILE=""
SKIP_SMOKE="0"
READINESS_TIMEOUT_SEC="60"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
    --server-user) SERVER_USER="${2:-}"; shift 2 ;;
    --plan-file) PLAN_FILE="${2:-}"; shift 2 ;;
    --admin-user) ADMIN_USER="${2:-}"; shift 2 ;;
    --admin-pass) ADMIN_PASS="${2:-}"; shift 2 ;;
    --admin-pass-file) ADMIN_PASS_FILE="${2:-}"; shift 2 ;;
    --skip-smoke) SKIP_SMOKE="${2:-}"; shift 2 ;;
    --readiness-timeout-sec) READINESS_TIMEOUT_SEC="${2:-}"; shift 2 ;;
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

require_zero_or_one() {
  local name="$1"
  local value="$2"
  if [[ "${value}" != "0" && "${value}" != "1" ]]; then
    echo "ERROR: ${name} must be 0 or 1" >&2
    exit 2
  fi
}

if [[ -z "${PLAN_FILE}" ]]; then
  echo "ERROR: --plan-file is required" >&2
  usage
  exit 2
fi
if [[ ! -f "${PLAN_FILE}" ]]; then
  echo "ERROR: plan file not found: ${PLAN_FILE}" >&2
  exit 2
fi

require_zero_or_one "--skip-smoke" "${SKIP_SMOKE}"
if [[ ! "${READINESS_TIMEOUT_SEC}" =~ ^[0-9]+$ ]] || [[ "${READINESS_TIMEOUT_SEC}" -lt 5 ]]; then
  echo "ERROR: --readiness-timeout-sec must be integer >= 5" >&2
  exit 2
fi

if [[ -z "${ADMIN_PASS}" && -n "${ADMIN_PASS_FILE}" ]]; then
  ADMIN_PASS="$(read_password_from_file "${ADMIN_PASS_FILE}" || true)"
fi

declare -a ROTATED_ACTORS=()
line_no=0

while IFS= read -r raw_line || [[ -n "${raw_line}" ]]; do
  line_no=$((line_no + 1))
  line="$(printf '%s' "${raw_line}" | tr -d '\r')"
  stripped="$(trim "${line}")"
  if [[ -z "${stripped}" || "${stripped}" == \#* ]]; then
    continue
  fi

  IFS='|' read -r actor_raw new_file_raw old_file_raw extra <<<"${line}"
  if [[ -n "${extra:-}" ]]; then
    echo "ERROR: invalid plan line ${line_no} (expected 2 or 3 columns)" >&2
    exit 2
  fi

  actor="$(trim "${actor_raw:-}")"
  new_file="$(trim "${new_file_raw:-}")"
  old_file="$(trim "${old_file_raw:-}")"

  if [[ -z "${actor}" || -z "${new_file}" ]]; then
    echo "ERROR: plan line ${line_no} has empty actor/new_password_file" >&2
    exit 2
  fi
  if [[ ! "${actor}" =~ ^support-[a-z0-9][a-z0-9-]*$ ]]; then
    echo "ERROR: actor '${actor}' does not match support-<system_id> policy" >&2
    exit 2
  fi
  if [[ ! -f "${new_file}" ]]; then
    echo "ERROR: new password file not found for '${actor}': ${new_file}" >&2
    exit 2
  fi
  if [[ -n "${old_file}" && ! -f "${old_file}" ]]; then
    echo "ERROR: old password file not found for '${actor}': ${old_file}" >&2
    exit 2
  fi

  echo "== rotate actor ${actor} =="
  rotate_cmd=(
    "${REPO_ROOT}/scripts/client_support_lifecycle_rollout.sh"
    --server-host "${SERVER_HOST}"
    --server-user "${SERVER_USER}"
    --action rotate
    --actor "${actor}"
    --new-pass-file "${new_file}"
    --readiness-timeout-sec "${READINESS_TIMEOUT_SEC}"
    --skip-smoke 1
  )
  if [[ -n "${old_file}" ]]; then
    rotate_cmd+=(--old-pass-file "${old_file}")
  fi
  "${rotate_cmd[@]}"
  ROTATED_ACTORS+=("${actor}")
done <"${PLAN_FILE}"

if [[ "${#ROTATED_ACTORS[@]}" -eq 0 ]]; then
  echo "ERROR: plan has no active records" >&2
  exit 2
fi

echo "ROTATED_ACTORS=$(printf '%s' "${ROTATED_ACTORS[*]}" | tr ' ' ',')"

if [[ "${SKIP_SMOKE}" == "0" ]]; then
  if [[ -n "${ADMIN_PASS}" ]]; then
    "${REPO_ROOT}/scripts/admin_panel_smoke_gate.sh" \
      --server-host "${SERVER_HOST}" \
      --server-user "${SERVER_USER}" \
      --admin-user "${ADMIN_USER}" \
      --admin-pass "${ADMIN_PASS}"
  else
    echo "WARN: smoke-gate skipped because admin password not provided"
  fi
fi

echo "RESULT: PASS"
