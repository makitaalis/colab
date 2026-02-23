#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
yolo_train_collect.sh — copy Ultralytics run artifacts into Docs/auto and write summary

Usage:
  ./scripts/yolo_train_collect.sh --id <UTC_LABEL>

Where <UTC_LABEL> matches both:
  - ml/yolov8_head_finetune/runs/<UTC_LABEL>/
  - Docs/auto/ml-training/yolov8-head/<UTC_LABEL>/
USAGE
}

ID=""
while [[ $# -gt 0 ]]; do
  case "$1" in
    --id) ID="${2:-}"; shift 2 ;;
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
PY="${REPO_ROOT}/.venv/bin/python"
if [[ ! -x "${PY}" ]]; then
  PY="python3"
fi

RUN_DIR="${REPO_ROOT}/ml/yolov8_head_finetune/runs/${ID}"
DOC_DIR="${REPO_ROOT}/Docs/auto/ml-training/yolov8-head/${ID}"

if [[ ! -d "${RUN_DIR}" ]]; then
  echo "ERROR: Ultralytics run dir not found: ${RUN_DIR}" >&2
  exit 2
fi
if [[ ! -d "${DOC_DIR}" ]]; then
  echo "ERROR: Docs dir not found: ${DOC_DIR}" >&2
  exit 2
fi

mkdir -p "${DOC_DIR}/results"

for f in args.yaml results.csv results.png labels.jpg confusion_matrix.png confusion_matrix_normalized.png; do
  if [[ -f "${RUN_DIR}/${f}" ]]; then
    cp -f "${RUN_DIR}/${f}" "${DOC_DIR}/results/${f}"
  fi
done
if [[ -d "${RUN_DIR}/weights" ]]; then
  cp -f "${RUN_DIR}/weights/best.pt" "${DOC_DIR}/results/best.pt" 2>/dev/null || true
  cp -f "${RUN_DIR}/weights/last.pt" "${DOC_DIR}/results/last.pt" 2>/dev/null || true
fi

"${PY}" - <<'PY' "${RUN_DIR}" "${DOC_DIR}"
import csv
import sys
from pathlib import Path

run_dir = Path(sys.argv[1])
doc_dir = Path(sys.argv[2])
res = run_dir / "results.csv"

summary_path = doc_dir / "results" / "summary.md"
if not res.exists():
    summary_path.write_text("No results.csv found\n", encoding="utf-8")
    raise SystemExit(0)

with res.open("r", encoding="utf-8", errors="replace", newline="") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

if not rows:
    summary_path.write_text("Empty results.csv\n", encoding="utf-8")
    raise SystemExit(0)

key = None
for k in ["metrics/mAP50-95(B)", "metrics/mAP50-95"]:
    if k in rows[0]:
        key = k
        break
if key is None:
    key = list(rows[0].keys())[-1]

def fnum(v: str) -> float:
    try:
        return float(v)
    except Exception:
        return float("-inf")

best = max(rows, key=lambda r: fnum(r.get(key, "")))

out = [
    "# Summary",
    f"run_dir: {run_dir}",
    f"best_by: {key}",
    "",
]
for k in ["epoch", key, "metrics/precision(B)", "metrics/recall(B)", "metrics/mAP50(B)", "metrics/mAP50-95(B)"]:
    if k in best:
        out.append(f"- {k}: {best[k]}")

summary_path.write_text("\n".join(out) + "\n", encoding="utf-8")
PY

echo "Collected. Docs: ${DOC_DIR}/results/"
