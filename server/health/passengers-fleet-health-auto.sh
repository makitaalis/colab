#!/usr/bin/env bash
set -euo pipefail

BACKEND_URL="${BACKEND_URL:-http://10.66.0.1}"
ENV_FILE="${ENV_FILE:-/opt/passengers-backend/.env}"
CURL_TIMEOUT_SEC="${CURL_TIMEOUT_SEC:-20}"

if [[ ! -f "${ENV_FILE}" ]]; then
  echo "ERROR: env file not found: ${ENV_FILE}" >&2
  exit 1
fi

ADMIN_TOKEN="$(grep -m1 '^ADMIN_API_KEYS=' "${ENV_FILE}" | cut -d= -f2 | tr -d '\r' | cut -d, -f1)"
if [[ -z "${ADMIN_TOKEN}" ]]; then
  echo "ERROR: ADMIN_API_KEYS is empty in ${ENV_FILE}" >&2
  exit 1
fi

URL="${BACKEND_URL%/}/api/admin/fleet/health/notify-auto"
RESP="$(
  curl -fsS --max-time "${CURL_TIMEOUT_SEC}" \
    -X POST \
    -H "Authorization: Bearer ${ADMIN_TOKEN}" \
    "${URL}"
)"

echo "${RESP}"

python3 - "${RESP}" <<'PY'
import json
import sys

raw = sys.argv[1]
payload = json.loads(raw)
if str(payload.get("status") or "") != "ok":
    raise SystemExit(f"bad_status: {payload.get('status')}")
decision = str(payload.get("decision") or "unknown")
reason = str(payload.get("reason") or "")
state = payload.get("state") or {}
print(f"decision={decision}")
print(f"reason={reason}")
print(f"severity={state.get('severity')}")
PY
