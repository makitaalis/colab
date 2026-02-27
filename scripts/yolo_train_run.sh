#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
yolo_train_run.sh — reproducible Ultralytics YOLOv8 training run with auto-docs

Creates a structured run folder under:
  Docs/auto/ml-training/yolov8-head/<UTC_TIMESTAMP>_<name>/

And writes:
  - preflight.json (dataset+env checks)
  - command.sh (exact training command)
  - results/ (copied key artifacts after training)

Training outputs (Ultralytics "runs") are directed to:
  ml/yolov8_head_finetune/runs/

Usage:
  ./scripts/yolo_train_run.sh --name <label> [options] [--execute]

Options:
  --name <label>      Run label (required)
  --dataset <path>    Dataset root (default: /home/alis/Документы/DataSet/brainwash.v1i.yolov8)
  --data <yaml>       Dataset yaml (default: ml/yolov8_head_finetune/data_head.yaml)
  --model <pt>        Base weights (default: ml/yolov8_head_finetune/weights/base/yolov8_head_scut_nano.pt)
  --project <path>    Ultralytics runs project dir (default: ml/yolov8_head_finetune/runs)
  --imgsz <n>         Image size (default: 640)
  --epochs <n>        Epochs (default: 80)
  --batch <n|auto>    Batch size (default: auto; mapped to -1)
  --device <id>       Device (default: 0)
  --workers <n>       Dataloader workers (default: 8)
  --seed <n>          Seed (default: 0)
  --notes <text>      Notes saved to notes.txt
  --execute           Actually run training (otherwise only prepares docs)

Examples:
  ./scripts/yolo_train_run.sh --name baseline640 --imgsz 640 --epochs 80
  ./scripts/yolo_train_run.sh --name baseline640 --imgsz 640 --epochs 80 --execute
  ./scripts/yolo_train_run.sh --name long640 --imgsz 640 --epochs 80 --project /home/alis/ml/runs/yolov8-head --execute
USAGE
}

NAME=""
DATASET_ROOT="/home/alis/Документы/DataSet/brainwash.v1i.yolov8"
DATA="ml/yolov8_head_finetune/data_head.yaml"
MODEL="ml/yolov8_head_finetune/weights/base/yolov8_head_scut_nano.pt"
PROJECT="ml/yolov8_head_finetune/runs"
IMGSZ="640"
EPOCHS="80"
BATCH="auto"
DEVICE="0"
WORKERS="8"
SEED="0"
NOTES=""
EXECUTE="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --name) NAME="${2:-}"; shift 2 ;;
    --dataset) DATASET_ROOT="${2:-}"; shift 2 ;;
    --data) DATA="${2:-}"; shift 2 ;;
    --model) MODEL="${2:-}"; shift 2 ;;
    --project) PROJECT="${2:-}"; shift 2 ;;
    --imgsz) IMGSZ="${2:-}"; shift 2 ;;
    --epochs) EPOCHS="${2:-}"; shift 2 ;;
    --batch) BATCH="${2:-}"; shift 2 ;;
    --device) DEVICE="${2:-}"; shift 2 ;;
    --workers) WORKERS="${2:-}"; shift 2 ;;
    --seed) SEED="${2:-}"; shift 2 ;;
    --notes) NOTES="${2:-}"; shift 2 ;;
    --execute) EXECUTE="1"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${NAME}" ]]; then
  echo "ERROR: --name is required" >&2
  usage
  exit 2
fi

if [[ "${BATCH}" == "auto" ]]; then
  # Ultralytics CLI expects int/float; -1 means auto-batch.
  BATCH="-1"
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${REPO_ROOT}"
PY="${REPO_ROOT}/.venv/bin/python"
YOLO_BIN="${REPO_ROOT}/.venv/bin/yolo"
if [[ ! -x "${PY}" ]]; then
  PY="python3"
fi
if [[ ! -x "${YOLO_BIN}" ]]; then
  YOLO_BIN="yolo"
fi

abs_path() {
  local p="$1"
  if [[ "${p}" == /* ]]; then
    printf '%s' "${p}"
  else
    printf '%s' "${REPO_ROOT}/${p}"
  fi
}

resolve_model_arg() {
  # Accept either:
  # - path to local weights (.pt)
  # - model spec (e.g. yolov8n.pt) which Ultralytics can auto-download/resolve
  # - URL
  local m="$1"
  if [[ "${m}" == http://* || "${m}" == https://* ]]; then
    printf '%s' "${m}"
    return 0
  fi
  if [[ "${m}" == /* ]]; then
    printf '%s' "${m}"
    return 0
  fi
  if [[ "${m}" == *"/"* ]]; then
    printf '%s' "${REPO_ROOT}/${m}"
    return 0
  fi
  if [[ -f "${REPO_ROOT}/${m}" ]]; then
    printf '%s' "${REPO_ROOT}/${m}"
    return 0
  fi
  # Fallback: treat as Ultralytics model spec (yolov8n.pt, etc.)
  printf '%s' "${m}"
}

DATA_PATH="$(abs_path "${DATA}")"
MODEL_ARG="$(resolve_model_arg "${MODEL}")"
PROJECT_PATH="$(abs_path "${PROJECT}")"
ts="$(date -u +%Y%m%dT%H%M%SZ)"
name_sanitized="$(printf '%s' "${NAME}" | tr ' ' '_' | tr -cd 'A-Za-z0-9._-')"
if [[ -z "${name_sanitized}" ]]; then name_sanitized="run"; fi

RUN_DOC_DIR="${REPO_ROOT}/Docs/auto/ml-training/yolov8-head/${ts}_${name_sanitized}"
mkdir -p "${RUN_DOC_DIR}/results"
echo "${ts}_${name_sanitized}" > "${REPO_ROOT}/Docs/auto/ml-training/yolov8-head/_latest.txt"

if [[ -n "${NOTES}" ]]; then
  printf '%s\n' "${NOTES}" > "${RUN_DOC_DIR}/notes.txt"
fi

if git -C "${REPO_ROOT}" rev-parse --verify HEAD >/dev/null 2>&1; then
  git -C "${REPO_ROOT}" rev-parse HEAD > "${RUN_DOC_DIR}/git_rev.txt" 2>/dev/null || true
else
  echo "NO_COMMITS" > "${RUN_DOC_DIR}/git_rev.txt"
fi
git -C "${REPO_ROOT}" status --porcelain=v1 --branch > "${RUN_DOC_DIR}/git_status.txt" 2>/dev/null || true
"${PY}" -m pip freeze > "${RUN_DOC_DIR}/pip_freeze.txt" 2>/dev/null || true
cp -f "${DATA_PATH}" "${RUN_DOC_DIR}/data_used.yaml" 2>/dev/null || true

cat > "${RUN_DOC_DIR}/plan.md" <<EOF
# YOLOv8 head fine-tune — plan

Timestamp (UTC): ${ts}
Label: ${name_sanitized}

## Inputs

- Dataset root: ${DATASET_ROOT}
- Data yaml: ${DATA_PATH}
- Base weights: ${MODEL_ARG}
- Ultralytics project dir: ${PROJECT_PATH}

## Run sequence (recommended)

0) Smoke (1 epoch) to catch env/dataset issues early.
1) Short baselines on current splits:
   - @640: imgsz=640, epochs=10, batch=-1 (auto), seed=0
   - @416: imgsz=416, epochs=10, batch=-1 (auto), seed=0
2) Rebuild anti-leak splits (group/video-aware), then do long runs there:
   - e.g. @640 or @416: epochs=80, batch=-1 (auto), seed=0
3) Compare only on \`valid\`; run \`test\` once after decisions.

## Pitfalls to avoid

- Split leakage (same video/sequence across splits) inflates metrics → rebuild splits by group/video if suspected.
- No negative images (empty label files) can increase false positives → add negatives if needed.
- Small objects: if recall drops at 416, prefer 640 (then decide how to export/deploy).

## This run

- Prepared command: \`command.sh\`
- Preflight output: \`preflight.json\` (look at warnings/issues)
EOF

echo "==> Preflight"
set +e
"${PY}" "${REPO_ROOT}/scripts/yolo_train_preflight.py" \
  --dataset "${DATASET_ROOT}" \
  --data-yaml "${DATA_PATH}" \
  --base-weights "${MODEL_ARG}" \
  --out "${RUN_DOC_DIR}/preflight.json" > "${RUN_DOC_DIR}/preflight.stdout.json"
preflight_rc="$?"
set -e

if [[ "${EXECUTE}" == "1" && "${preflight_rc}" != "0" ]]; then
  echo "ERROR: preflight failed (rc=${preflight_rc}), see: ${RUN_DOC_DIR}/preflight.json" >&2
  exit 2
fi

YOLO_PROJECT="${PROJECT_PATH}"
mkdir -p "${YOLO_PROJECT}"

CMD=(
  "${YOLO_BIN}" detect train
  model="${MODEL_ARG}"
  data="${DATA_PATH}"
  imgsz="${IMGSZ}"
  epochs="${EPOCHS}"
  batch="${BATCH}"
  device="${DEVICE}"
  workers="${WORKERS}"
  seed="${SEED}"
  project="${YOLO_PROJECT}"
  name="${ts}_${name_sanitized}"
)

{
  echo "#!/usr/bin/env bash"
  printf '%q ' "${CMD[@]}"
  echo
} > "${RUN_DOC_DIR}/command.sh"
chmod +x "${RUN_DOC_DIR}/command.sh"

echo "Prepared: ${RUN_DOC_DIR}"
echo "Ultralytics project: ${YOLO_PROJECT}"

if [[ "${EXECUTE}" != "1" ]]; then
  echo "Dry mode: training not executed (pass --execute)."
  exit 0
fi

echo "==> Train"
if command -v systemd-inhibit >/dev/null 2>&1; then
  systemd-inhibit --what=sleep --why="YOLOv8 training ${ts}_${name_sanitized}" --mode=block \
    "${RUN_DOC_DIR}/command.sh" | tee "${RUN_DOC_DIR}/train.log"
else
  "${RUN_DOC_DIR}/command.sh" | tee "${RUN_DOC_DIR}/train.log"
fi

RUN_DIR="${YOLO_PROJECT}/${ts}_${name_sanitized}"
if [[ ! -d "${RUN_DIR}" ]]; then
  echo "WARN: expected run dir not found: ${RUN_DIR}" >&2
  exit 0
fi

echo "==> Collect results"
for f in args.yaml results.csv results.png confusion_matrix.png confusion_matrix_normalized.png; do
  if [[ -f "${RUN_DIR}/${f}" ]]; then
    cp -f "${RUN_DIR}/${f}" "${RUN_DOC_DIR}/results/${f}"
  fi
done
if [[ -d "${RUN_DIR}/weights" ]]; then
  cp -f "${RUN_DIR}/weights/best.pt" "${RUN_DOC_DIR}/results/best.pt" 2>/dev/null || true
  cp -f "${RUN_DIR}/weights/last.pt" "${RUN_DOC_DIR}/results/last.pt" 2>/dev/null || true
fi

"${PY}" - <<'PY' "${RUN_DIR}" "${RUN_DOC_DIR}"
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

echo "Done. Results copied to: ${RUN_DOC_DIR}/results/"
