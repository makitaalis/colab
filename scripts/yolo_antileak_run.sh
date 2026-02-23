#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
yolo_antileak_run.sh — rebuild dataset splits without cross-split group leakage + auto-docs

Groups images by numeric prefix before '_' in filename (fallback: stem).
All images from the same group go to the same split.

Writes a structured report under:
  Docs/auto/ml-training/yolov8-head/antileak/<UTC>_<label>/

Usage:
  ./scripts/yolo_antileak_run.sh --label <name> [options]

Options:
  --src <path>     Source dataset root (default: /home/alis/Документы/DataSet/brainwash.v1i.yolov8)
  --dst <path>     Destination dataset root (default: /home/alis/Документы/DataSet/brainwash.v1i.yolov8_antileak)
  --seed <n>       Shuffle seed (default: 0)
  --mode <m>       hardlink|symlink|copy (default: hardlink)
  --names <csv>    Class names (default: head)

USAGE
}

LABEL=""
SRC="/home/alis/Документы/DataSet/brainwash.v1i.yolov8"
DST="/home/alis/Документы/DataSet/brainwash.v1i.yolov8_antileak"
SEED="0"
MODE="hardlink"
NAMES="head"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --label) LABEL="${2:-}"; shift 2 ;;
    --src) SRC="${2:-}"; shift 2 ;;
    --dst) DST="${2:-}"; shift 2 ;;
    --seed) SEED="${2:-}"; shift 2 ;;
    --mode) MODE="${2:-}"; shift 2 ;;
    --names) NAMES="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown arg: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${LABEL}" ]]; then
  echo "ERROR: --label is required" >&2
  usage
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
ts="$(date -u +%Y%m%dT%H%M%SZ)"
label_sanitized="$(printf '%s' "${LABEL}" | tr ' ' '_' | tr -cd 'A-Za-z0-9._-')"
if [[ -z "${label_sanitized}" ]]; then label_sanitized="antileak"; fi

DOC_DIR="${REPO_ROOT}/Docs/auto/ml-training/yolov8-head/antileak/${ts}_${label_sanitized}"
mkdir -p "${DOC_DIR}"

cat > "${DOC_DIR}/plan.md" <<EOF
# Anti-leak rebuild plan

Timestamp (UTC): ${ts}
Label: ${label_sanitized}

Goal: rebuild splits so that image groups (numeric prefix before '_') do not cross train/valid/test.

Source: ${SRC}
Destination: ${DST}
Mode: ${MODE}
Seed: ${SEED}
Names: ${NAMES}
EOF

python3 "${REPO_ROOT}/scripts/yolo_antileak_rebuild_dataset.py" \
  --src "${SRC}" \
  --dst "${DST}" \
  --seed "${SEED}" \
  --mode "${MODE}" \
  --names "${NAMES}" \
  --report "${DOC_DIR}/report.json" | tee "${DOC_DIR}/report.stdout.json" >/dev/null

cp -f "${DST}/data.yaml" "${DOC_DIR}/data.yaml"

cat > "${DOC_DIR}/next_steps.md" <<EOF
# Next steps

Train with the rebuilt dataset by pointing Ultralytics to:

- data yaml: ${DST}/data.yaml

Example:

\`\`\`bash
./scripts/yolo_train_run.sh --name baseline640_antileak --data ${DST}/data.yaml --imgsz 640 --epochs 10 --batch auto --execute
\`\`\`
EOF

echo "Anti-leak dataset prepared:"
echo "  dst=${DST}"
echo "  docs=${DOC_DIR}"

