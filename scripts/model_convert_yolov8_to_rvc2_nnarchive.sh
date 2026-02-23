#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
model_convert_yolov8_to_rvc2_nnarchive.sh — convert YOLOv8 (Ultralytics) to Luxonis NNArchive (*.rvc2.tar.xz)

Primary goal: produce an offline artifact that DepthAI v3 can load with on-device YOLO parser:
  - convert via official Luxonis ModelConverter (RVC2)
  - patch NNArchive config.json with YOLO head metadata (parser=YOLO, subtype=yolov8/yolov8n, classes, outputs)

Official references:
  - https://docs.luxonis.com/software-v3/ai-inference/conversion/
  - https://docs.luxonis.com/software-v3/ai-inference/nn-archive/

Usage:
  ./scripts/model_convert_yolov8_to_rvc2_nnarchive.sh \
    --weights <model.pt|model.onnx> \
    --name <ARCHIVE_NAME> \
    --classes <csv> \
    [--imgsz 416] [--subtype yolov8] [--conf 0.4] [--iou 0.5]

Examples:
  # Head model (1 class)
  ./scripts/model_convert_yolov8_to_rvc2_nnarchive.sh \
    --weights mvp/models/src/yolov8_head_detector/yolov8_head_scut_nano.pt \
    --name HEAD_YOLOv8n_SCUT_Nano_416_YOLO_RAW \
    --classes head \
    --imgsz 416 \
    --subtype yolov8

Output:
  - Final patched archive: mvp/models/<NAME>_head.rvc2.tar.xz
  - Raw ModelConverter output dir: tools/modelconverter/shared_with_container/outputs/<NAME>_rvc2/
USAGE
}

WEIGHTS=""
NAME=""
CLASSES="head"
IMGSZ="416"
SUBTYPE="yolov8"
CONF="0.4"
IOU="0.5"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --weights) WEIGHTS="${2:-}"; shift 2 ;;
    --name) NAME="${2:-}"; shift 2 ;;
    --classes) CLASSES="${2:-}"; shift 2 ;;
    --imgsz) IMGSZ="${2:-}"; shift 2 ;;
    --subtype) SUBTYPE="${2:-}"; shift 2 ;;
    --conf) CONF="${2:-}"; shift 2 ;;
    --iou) IOU="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${WEIGHTS}" || -z "${NAME}" ]]; then
  echo "ERROR: --weights and --name are required" >&2
  usage
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
WEIGHTS_PATH="$(cd "${REPO_ROOT}" && python3 - <<PY
from pathlib import Path
p = Path(${WEIGHTS@Q}).expanduser()
print(str(p.resolve()))
PY
)"
if [[ ! -f "${WEIGHTS_PATH}" ]]; then
  echo "ERROR: weights file not found: ${WEIGHTS_PATH}" >&2
  exit 2
fi

WORK_ROOT="${REPO_ROOT}/tools/modelconverter/shared_with_container"
MODELS_DIR="${WORK_ROOT}/models"
CONFIGS_DIR="${WORK_ROOT}/configs"
OUTPUTS_DIR="${WORK_ROOT}/outputs"

mkdir -p "${MODELS_DIR}" "${CONFIGS_DIR}" "${OUTPUTS_DIR}"

SRC_ONNX="${MODELS_DIR}/${NAME}.onnx"
RAW_ONNX="${MODELS_DIR}/${NAME}_yolo_raw.onnx"

echo "==> Step 1/5: Export to ONNX (if needed)"
if [[ "${WEIGHTS_PATH}" == *.onnx ]]; then
  cp -f "${WEIGHTS_PATH}" "${SRC_ONNX}"
else
  python3 - <<PY
from ultralytics import YOLO
from pathlib import Path

weights = Path(${WEIGHTS_PATH@Q})
imgsz = int(${IMGSZ@Q})
dst = Path(${SRC_ONNX@Q})

model = YOLO(str(weights))
out = model.export(format="onnx", imgsz=imgsz, dynamic=False, opset=18)
out_path = Path(str(out)).resolve()
dst.parent.mkdir(parents=True, exist_ok=True)
dst.write_bytes(out_path.read_bytes())
print(f"Exported: {out_path} -> {dst}")
PY
fi

echo "==> Step 2/5: Find YOLOv8 raw outputs and rewrite graph outputs"
YOLO_OUTPUTS="$(python3 "${REPO_ROOT}/scripts/onnx_find_yolov8_raw_outputs.py" --model "${SRC_ONNX}" --imgsz "${IMGSZ}")"
echo "YOLO raw outputs: ${YOLO_OUTPUTS}"

python3 "${REPO_ROOT}/scripts/onnx_set_outputs.py" \
  --in "${SRC_ONNX}" \
  --out "${RAW_ONNX}" \
  --outputs "${YOLO_OUTPUTS}"

CFG_PATH="${CONFIGS_DIR}/${NAME}.yaml"
cat > "${CFG_PATH}" <<YAML
name: ${NAME}
input_model: /workspace/models/${NAME}_yolo_raw.onnx

mean_values: [0, 0, 0]
scale_values: [255, 255, 255]

inputs:
  - name: images
    shape: [1, 3, ${IMGSZ}, ${IMGSZ}]
    layout: NCHW

outputs:
$(printf '%s\n' "${YOLO_OUTPUTS}" | tr ',' '\n' | sed 's/^/  - name: /')
YAML

echo "==> Step 3/5: Run official Luxonis ModelConverter (RVC2 -> NNArchive)"
OUT_DIR="${OUTPUTS_DIR}/${NAME}_rvc2"
rm -rf "${OUT_DIR}"
mkdir -p "${OUT_DIR}"

docker run --rm \
  --user "$(id -u):$(id -g)" \
  -w /workspace \
  -v "${WORK_ROOT}:/workspace" \
  ghcr.io/luxonis/modelconverter-rvc2:2022.3.0-latest \
  convert rvc2 \
  --path "/workspace/configs/${NAME}.yaml" \
  --output-dir "/workspace/outputs/${NAME}_rvc2" \
  --to nn_archive

RAW_ARCHIVE="$(find "${OUT_DIR}" -maxdepth 1 -type f -name '*.rvc2.tar.xz' | head -n 1)"
if [[ -z "${RAW_ARCHIVE}" ]]; then
  echo "ERROR: ModelConverter did not produce *.rvc2.tar.xz in ${OUT_DIR}" >&2
  exit 1
fi
echo "Produced archive: ${RAW_ARCHIVE}"

echo "==> Step 4/5: Patch NNArchive with YOLO head metadata (parser=YOLO)"
FINAL_ARCHIVE="${REPO_ROOT}/mvp/models/${NAME}_head.rvc2.tar.xz"
python3 "${REPO_ROOT}/scripts/nnarchive_add_yolo_head.py" \
  --archive "${RAW_ARCHIVE}" \
  --out "${FINAL_ARCHIVE}" \
  --classes "${CLASSES}" \
  --subtype "${SUBTYPE}" \
  --conf-th "${CONF}" \
  --iou-th "${IOU}" \
  --yolo-outputs "${YOLO_OUTPUTS}"

echo "==> Step 5/5: Done"
echo "Final NNArchive: ${FINAL_ARCHIVE}"
echo "Next: deploy to device via ./scripts/camera_mode_switch.sh (depth-counting) and set:"
echo "  CAM_DEPTH_COUNT_MODEL=/opt/passengers-mvp/models/$(basename "${FINAL_ARCHIVE}")"
echo "  CAM_DEPTH_COUNT_MODEL_INPUT_SIZE=${IMGSZ}x${IMGSZ}"
