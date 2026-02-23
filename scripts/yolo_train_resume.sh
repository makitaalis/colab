#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
yolo_train_resume.sh — resume an interrupted YOLOv8 run and keep Docs/auto in sync

Usage:
  ./scripts/yolo_train_resume.sh --id <UTC_LABEL> [--device <id>]

Notes:
  - Uses systemd-inhibit (if available) to prevent sleep during training.
  - Appends logs to Docs/auto/.../train.log and collects artifacts at the end.
USAGE
}

ID=""
DEVICE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --id) ID="${2:-}"; shift 2 ;;
    --device) DEVICE="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${ID}" ]]; then
  echo "ERROR: --id is required" >&2
  usage
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
YOLO_BIN="${REPO_ROOT}/.venv/bin/yolo"
if [[ ! -x "${YOLO_BIN}" ]]; then
  YOLO_BIN="yolo"
fi

RUN_DIR="${REPO_ROOT}/ml/yolov8_head_finetune/runs/${ID}"
DOC_DIR="${REPO_ROOT}/Docs/auto/ml-training/yolov8-head/${ID}"
LAST_PT="${RUN_DIR}/weights/last.pt"

if [[ ! -d "${RUN_DIR}" ]]; then
  echo "ERROR: Ultralytics run dir not found: ${RUN_DIR}" >&2
  exit 2
fi
if [[ ! -d "${DOC_DIR}" ]]; then
  echo "ERROR: Docs dir not found: ${DOC_DIR}" >&2
  exit 2
fi
if [[ ! -f "${LAST_PT}" ]]; then
  echo "ERROR: last.pt not found: ${LAST_PT}" >&2
  exit 2
fi

mkdir -p "${DOC_DIR}/results"

ts="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '\n[%s] Resume requested: %s\n' "${ts}" "${LAST_PT}" >> "${DOC_DIR}/notes.txt"

CMD=( "${YOLO_BIN}" detect train resume=True model="${LAST_PT}" device="${DEVICE}" )

echo "==> Resume: ${ID}"
echo "Run dir: ${RUN_DIR}"
echo "Docs dir: ${DOC_DIR}"

if command -v systemd-inhibit >/dev/null 2>&1; then
  systemd-inhibit --what=sleep --why="YOLOv8 training resume ${ID}" --mode=block \
    "${CMD[@]}" 2>&1 | tee -a "${DOC_DIR}/train.log"
else
  "${CMD[@]}" 2>&1 | tee -a "${DOC_DIR}/train.log"
fi

./scripts/yolo_train_collect.sh --id "${ID}"
ts2="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
printf '[%s] Resume finished. Artifacts collected.\n' "${ts2}" >> "${DOC_DIR}/notes.txt"
