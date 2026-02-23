#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
camera_tuning_run.sh — capture one camera tuning run (env + health jsonl + logs + summary)

This script creates a per-run folder under:
  Docs/auto/camera-tuning/<camera-ip>/<UTC_TIMESTAMP>_<label>/

It snapshots:
  - /etc/passengers/passengers.env (full)
  - /health at start/end
  - JSONL samples from /health during the run (via camera_depth_live_probe.sh)
  - journalctl slice for the run window
  - computed summary.md

Usage:
  ./scripts/camera_tuning_run.sh --camera-ip <ip> --label <name> [options]

Options:
  --camera-ip <ip>    Camera node IP (required)
  --user <name>       SSH user (default: orangepi)
  --port <n>          Local debug HTTP port on node (default: 8091)
  --service <name>    systemd unit (default: passengers-camera-depth-counting.service)
  --seconds <n>       Run duration (default: 180)
  --label <name>      Run label (required; used in folder name)
  --notes <text>      Optional note (saved to notes.txt)
  -h, --help          Show help

Examples:
  ./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --preset head-yolov8-host-loose --health
  ./scripts/camera_tuning_run.sh --camera-ip 192.168.10.11 --label office_10x10_loose --seconds 180

USAGE
}

CAMERA_IP=""
OPI_USER="orangepi"
PORT="8091"
SERVICE_NAME="passengers-camera-depth-counting.service"
SECONDS_CAPTURE="180"
LABEL=""
NOTES=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --camera-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --port) PORT="${2:-}"; shift 2 ;;
    --service) SERVICE_NAME="${2:-}"; shift 2 ;;
    --seconds) SECONDS_CAPTURE="${2:-}"; shift 2 ;;
    --label) LABEL="${2:-}"; shift 2 ;;
    --notes) NOTES="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${CAMERA_IP}" ]]; then
  echo "ERROR: --camera-ip is required" >&2
  exit 2
fi
if [[ -z "${LABEL}" ]]; then
  echo "ERROR: --label is required" >&2
  exit 2
fi
if ! [[ "${SECONDS_CAPTURE}" =~ ^[0-9]+$ ]] || [[ "${SECONDS_CAPTURE}" -lt 5 ]]; then
  echo "ERROR: --seconds must be integer >= 5" >&2
  exit 2
fi

HOST="${OPI_USER}@${CAMERA_IP}"

ts_utc="$(date -u +%Y%m%dT%H%M%SZ)"
label_sanitized="$(printf '%s' "${LABEL}" | tr ' ' '_' | tr -cd 'A-Za-z0-9._-')"
if [[ -z "${label_sanitized}" ]]; then
  label_sanitized="run"
fi

RUN_DIR="Docs/auto/camera-tuning/${CAMERA_IP}/${ts_utc}_${label_sanitized}"
mkdir -p "${RUN_DIR}"

echo "== camera_tuning_run =="
echo "host=${HOST} port=${PORT} service=${SERVICE_NAME} seconds=${SECONDS_CAPTURE}"
echo "out=${RUN_DIR}"

if [[ -n "${NOTES}" ]]; then
  printf '%s\n' "${NOTES}" > "${RUN_DIR}/notes.txt"
fi

start_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

ssh -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "echo ok" >/dev/null
start_epoch="$(ssh "${HOST}" "date +%s" 2>/dev/null || date +%s)"

ssh "${HOST}" "sudo cat /etc/passengers/passengers.env 2>/dev/null || true" > "${RUN_DIR}/passengers.env"
ssh "${HOST}" "systemctl status '${SERVICE_NAME}' -n 80 --no-pager 2>/dev/null || true" > "${RUN_DIR}/service_status.txt"
ssh "${HOST}" "curl -fsS --max-time 3 http://127.0.0.1:${PORT}/health" > "${RUN_DIR}/health_start.json" || true
ssh "${HOST}" "curl -fsS --max-time 3 http://127.0.0.1:${PORT}/snapshot.jpg" > "${RUN_DIR}/snapshot_start.jpg" || true

echo "Walk now (10+10). Capturing /health samples..."
./scripts/camera_depth_live_probe.sh \
  --camera-ip "${CAMERA_IP}" \
  --user "${OPI_USER}" \
  --port "${PORT}" \
  --seconds "${SECONDS_CAPTURE}" \
  --out "${RUN_DIR}/health.jsonl" | tee "${RUN_DIR}/probe_compact.jsonl" >/dev/null

end_iso="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
end_epoch="$(ssh "${HOST}" "date +%s" 2>/dev/null || date +%s)"

ssh "${HOST}" "curl -fsS --max-time 3 http://127.0.0.1:${PORT}/health" > "${RUN_DIR}/health_end.json" || true
ssh "${HOST}" "curl -fsS --max-time 3 http://127.0.0.1:${PORT}/snapshot.jpg" > "${RUN_DIR}/snapshot_end.jpg" || true
ssh "${HOST}" "journalctl -u '${SERVICE_NAME}' --since '@${start_epoch}' --until '@${end_epoch}' -o cat --no-pager 2>/dev/null || true" > "${RUN_DIR}/journal.txt"

cat > "${RUN_DIR}/meta.json" <<EOF
{
  "camera_ip": "$(printf '%s' "${CAMERA_IP}")",
  "user": "$(printf '%s' "${OPI_USER}")",
  "port": $(printf '%s' "${PORT}"),
  "service": "$(printf '%s' "${SERVICE_NAME}")",
  "seconds": $(printf '%s' "${SECONDS_CAPTURE}"),
  "label": "$(printf '%s' "${LABEL}" | python3 -c 'import json,sys; print(json.dumps(sys.stdin.read().rstrip())[1:-1])')",
  "start_utc": "$(printf '%s' "${start_iso}")",
  "end_utc": "$(printf '%s' "${end_iso}")",
  "start_epoch": $(printf '%s' "${start_epoch}"),
  "end_epoch": $(printf '%s' "${end_epoch}")
}
EOF

python3 scripts/camera_tuning_summarize.py "${RUN_DIR}/health.jsonl" > "${RUN_DIR}/summary.md" || true

echo "DONE: ${RUN_DIR}"
echo "Next: open ${RUN_DIR}/summary.md"
