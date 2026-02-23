#!/usr/bin/env bash
set -euo pipefail

CAMERA_IP="192.168.10.1"
OPI_USER="orangepi"
ENV_FILE="/etc/passengers/passengers.env"
SERVICE_NAME="passengers-camera-depth-counting.service"
PRESET=""
RESTART_SERVICE="1"
SHOW_ONLY="0"
HEALTH_SNAPSHOT="0"
HEALTH_WAIT_SEC="25"
declare -a SETS=()
declare -a SETS_USER=()

usage() {
  cat <<'USAGE'
camera_depth_calibrate.sh — quick calibration helper for depth-counting mode

Usage:
  ./scripts/camera_depth_calibrate.sh [options]

Options:
  --camera-ip <ip>        Camera node IP (default: 192.168.10.1)
  --central-ip <ip>       Alias for --camera-ip (backward compatible)
  --user <name>           SSH user (default: orangepi)
  --show                  Show current CAM_DEPTH_COUNT_* values and exit
  --health                Show one /health snapshot after changes
  --health-wait-sec <n>   Max wait for /health readiness (default: 25)
  --preset <name>         Apply preset: baseline|wide-scan|door-tight|transport-strict|transport-fast-pass|commissioning-no-depth|commissioning-depth-soft|head-yolov8-host|head-yolov8-host-loose|head-yolov8-host-strict|head-yolov8-host-depth-wz|head-yolov8-host-nofilter|head-yolov8-host-depth-wz-commissioning|head-yolov8-host-depth-commissioning
  --set KEY=VALUE         Set explicit env value (repeatable)
  --no-restart            Do not restart depth-counting service
  -h, --help              Show help

Examples:
  ./scripts/camera_depth_calibrate.sh --show --health
  ./scripts/camera_depth_calibrate.sh --preset wide-scan --health
  ./scripts/camera_depth_calibrate.sh --preset transport-strict --health
  ./scripts/camera_depth_calibrate.sh --preset transport-fast-pass --health
  ./scripts/camera_depth_calibrate.sh --set CAM_DEPTH_COUNT_ROI=0.10,0.12,0.90,0.95 --set CAM_DEPTH_COUNT_AREA_MIN=2600 --health
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --camera-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --central-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --show) SHOW_ONLY="1"; shift ;;
    --health) HEALTH_SNAPSHOT="1"; shift ;;
    --health-wait-sec) HEALTH_WAIT_SEC="${2:-}"; shift 2 ;;
    --preset) PRESET="${2:-}"; shift 2 ;;
    --set) SETS_USER+=("${2:-}"); shift 2 ;;
    --no-restart) RESTART_SERVICE="0"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

HOST="${OPI_USER}@${CAMERA_IP}"

ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

show_current() {
  ssh "${HOST}" "echo '--- CAM_DEPTH_COUNT_/CAM_IMU_* (from ${ENV_FILE}) ---';
sudo awk -F= '/^CAM_DEPTH_COUNT_|^CAM_IMU_|^CAM_DEBUG_BIND=|^CAM_DEBUG_PORT=/{print \$0}' '${ENV_FILE}' | sort;
echo '--- service state ---';
systemctl is-active '${SERVICE_NAME}' 2>/dev/null || true"
}

append_kv() {
  local key="$1"
  local value="$2"
  SETS+=("${key}=${value}")
}

apply_preset() {
  case "${PRESET}" in
    "") ;;
    baseline)
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.55"
      append_kv "CAM_DEPTH_COUNT_TRACKER_TYPE" "short_term_imageless"
      append_kv "CAM_DEPTH_COUNT_AXIS" "y"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.04"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.20"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "5"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "6"
      append_kv "CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC" "3.0"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.12"
      append_kv "CAM_DEPTH_COUNT_ROI" "0.05,0.10,0.95,0.95"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_LOW" "125"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_HIGH" "145"
      append_kv "CAM_DEPTH_COUNT_AREA_MIN" "5000"
      append_kv "CAM_DEPTH_COUNT_KERNEL_SIZE" "37"
      append_kv "CAM_DEPTH_COUNT_TRACK_GAP_SEC" "0.80"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.60"
      ;;
    wide-scan)
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.48"
      append_kv "CAM_DEPTH_COUNT_TRACKER_TYPE" "short_term_imageless"
      append_kv "CAM_DEPTH_COUNT_AXIS" "y"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.05"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.18"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "4"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "8"
      append_kv "CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC" "3.5"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.08"
      append_kv "CAM_DEPTH_COUNT_ROI" "0.04,0.08,0.96,0.97"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_LOW" "18"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_HIGH" "220"
      append_kv "CAM_DEPTH_COUNT_AREA_MIN" "1800"
      append_kv "CAM_DEPTH_COUNT_KERNEL_SIZE" "19"
      append_kv "CAM_DEPTH_COUNT_TRACK_GAP_SEC" "1.00"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.75"
      ;;
    door-tight)
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.60"
      append_kv "CAM_DEPTH_COUNT_TRACKER_TYPE" "short_term_imageless"
      append_kv "CAM_DEPTH_COUNT_AXIS" "y"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.52"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.04"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.22"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "6"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "6"
      append_kv "CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC" "2.8"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.14"
      append_kv "CAM_DEPTH_COUNT_ROI" "0.16,0.10,0.88,0.95"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_LOW" "25"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_HIGH" "180"
      append_kv "CAM_DEPTH_COUNT_AREA_MIN" "2800"
      append_kv "CAM_DEPTH_COUNT_KERNEL_SIZE" "23"
      append_kv "CAM_DEPTH_COUNT_TRACK_GAP_SEC" "0.90"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.65"
      ;;
    transport-strict)
      append_kv "CAM_DEPTH_COUNT_FPS" "10"
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.65"
      append_kv "CAM_DEPTH_COUNT_TRACKER_TYPE" "short_term_imageless"
      append_kv "CAM_DEPTH_COUNT_AXIS" "y"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.04"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.25"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "leading_edge"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "8"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "5"
      append_kv "CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC" "2.5"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.18"
      append_kv "CAM_DEPTH_COUNT_ROI" "0.14,0.12,0.90,0.97"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_LOW" "28"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_HIGH" "170"
      append_kv "CAM_DEPTH_COUNT_AREA_MIN" "3600"
      append_kv "CAM_DEPTH_COUNT_KERNEL_SIZE" "25"
      append_kv "CAM_DEPTH_COUNT_TRACK_GAP_SEC" "0.33"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "1.80"
      append_kv "CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC" "2.40"
      ;;
    transport-fast-pass)
      append_kv "CAM_DEPTH_ENABLE" "1"
      append_kv "CAM_DEPTH_MIN_M" "0.20"
      append_kv "CAM_DEPTH_MAX_M" "2.50"
      append_kv "CAM_DEPTH_COUNT_FPS" "10"
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.30"
      append_kv "CAM_DEPTH_COUNT_TRACKER_TYPE" "short_term_imageless"
      append_kv "CAM_DEPTH_COUNT_AXIS" "x"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.01"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.14"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "1"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "10"
      append_kv "CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC" "8.0"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.04"
      append_kv "CAM_DEPTH_COUNT_ROI" "0.06,0.06,0.94,0.98"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_LOW" "28"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_HIGH" "170"
      append_kv "CAM_DEPTH_COUNT_AREA_MIN" "3600"
      append_kv "CAM_DEPTH_COUNT_KERNEL_SIZE" "25"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.60"
      append_kv "CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC" "1.20"
      append_kv "CAM_JPEG_QUALITY" "70"
      ;;
    commissioning-no-depth)
      append_kv "CAM_DEPTH_ENABLE" "0"
      append_kv "CAM_DEPTH_COUNT_FPS" "10"
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.20"
      append_kv "CAM_DEPTH_COUNT_TRACKER_TYPE" "short_term_imageless"
      append_kv "CAM_DEPTH_COUNT_AXIS" "y"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.78"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.00"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.10"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "1"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "5"
      append_kv "CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC" "8.0"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.02"
      append_kv "CAM_DEPTH_COUNT_ROI" "0.14,0.12,0.90,0.97"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_LOW" "28"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_HIGH" "170"
      append_kv "CAM_DEPTH_COUNT_AREA_MIN" "3600"
      append_kv "CAM_DEPTH_COUNT_KERNEL_SIZE" "25"
      append_kv "CAM_DEPTH_COUNT_TRACK_GAP_SEC" "0.33"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.80"
      ;;
    commissioning-depth-soft)
      append_kv "CAM_DEPTH_ENABLE" "1"
      append_kv "CAM_DEPTH_MIN_M" "0.20"
      append_kv "CAM_DEPTH_MAX_M" "2.50"
      append_kv "CAM_DEPTH_COUNT_FPS" "10"
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.20"
      append_kv "CAM_DEPTH_COUNT_TRACKER_TYPE" "short_term_imageless"
      append_kv "CAM_DEPTH_COUNT_AXIS" "y"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.78"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.00"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.10"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "1"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "5"
      append_kv "CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC" "8.0"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.02"
      append_kv "CAM_DEPTH_COUNT_ROI" "0.14,0.12,0.90,0.97"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_LOW" "28"
      append_kv "CAM_DEPTH_COUNT_THRESHOLD_HIGH" "170"
      append_kv "CAM_DEPTH_COUNT_AREA_MIN" "3600"
      append_kv "CAM_DEPTH_COUNT_KERNEL_SIZE" "25"
      append_kv "CAM_DEPTH_COUNT_TRACK_GAP_SEC" "0.33"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.80"
      ;;
    head-yolov8-host)
      append_kv "CAM_DEPTH_COUNT_BACKEND" "host-yolov8-raw"
      append_kv "CAM_DEPTH_ENABLE" "0"
      # Default geometry for top-down door flow (people move top->bottom on screen => cross horizontal lines => AXIS=x).
      append_kv "CAM_DEPTH_COUNT_AXIS" "x"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.01"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.22"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_INFER_MIDDLE_FROM_SPAN" "0"
      append_kv "CAM_DEPTH_COUNT_MIN_SIDE_FRAMES_BEFORE_MIDDLE" "1"
      append_kv "CAM_DEPTH_COUNT_MAX_JUMP_PX" "0"
      append_kv "CAM_DEPTH_COUNT_ROI" ""
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.30"
      append_kv "CAM_DEPTH_COUNT_DNN_CONFIDENCE" "0.20"
      append_kv "CAM_DEPTH_COUNT_NMS_IOU" "0.5"
      append_kv "CAM_DEPTH_COUNT_MAX_DET" "120"
      append_kv "CAM_DEPTH_COUNT_MATCH_DIST_PX" "90"
      ;;
    head-yolov8-host-loose)
      # Commissioning preset: maximize recall, reduce ROI-induced resets; tighten later with depth+ROI once stable.
      append_kv "CAM_DEPTH_COUNT_BACKEND" "host-yolov8-raw"
      append_kv "CAM_DEPTH_ENABLE" "0"
      append_kv "CAM_DEPTH_COUNT_AXIS" "x"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.01"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.22"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_INFER_MIDDLE_FROM_SPAN" "0"
      append_kv "CAM_DEPTH_COUNT_MIN_SIDE_FRAMES_BEFORE_MIDDLE" "1"
      append_kv "CAM_DEPTH_COUNT_MAX_JUMP_PX" "0"
      append_kv "CAM_DEPTH_COUNT_ROI" ""
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.12"
      append_kv "CAM_DEPTH_COUNT_DNN_CONFIDENCE" "0.06"
      append_kv "CAM_DEPTH_COUNT_NMS_IOU" "0.55"
      append_kv "CAM_DEPTH_COUNT_MAX_DET" "180"
      append_kv "CAM_DEPTH_COUNT_MATCH_DIST_PX" "160"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "1"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "12"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.35"
      append_kv "CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC" "0.70"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.02"
      # Relax head bbox filters (416x416 input space).
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_W_PX" "20"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_H_PX" "20"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AREA_PX2" "400"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_W_PX" "240"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_H_PX" "280"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AREA_PX2" "70000"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AR" "0.45"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AR" "2.50"
      ;;
    head-yolov8-host-strict)
      # Strict head preset (static bbox size/AR) for 1080p->416 pipeline. Add depth-gate afterwards.
      append_kv "CAM_DEPTH_COUNT_BACKEND" "host-yolov8-raw"
      append_kv "CAM_DEPTH_ENABLE" "0"
      append_kv "CAM_DEPTH_COUNT_AXIS" "x"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.01"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.22"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_INFER_MIDDLE_FROM_SPAN" "0"
      append_kv "CAM_DEPTH_COUNT_MIN_SIDE_FRAMES_BEFORE_MIDDLE" "2"
      append_kv "CAM_DEPTH_COUNT_MAX_JUMP_PX" "120"
      append_kv "CAM_DEPTH_COUNT_ROI" ""
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.30"
      append_kv "CAM_DEPTH_COUNT_DNN_CONFIDENCE" "0.20"
      append_kv "CAM_DEPTH_COUNT_NMS_IOU" "0.5"
      append_kv "CAM_DEPTH_COUNT_MAX_DET" "120"
      append_kv "CAM_DEPTH_COUNT_MATCH_DIST_PX" "120"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "2"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "10"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.50"
      append_kv "CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC" "0.90"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.02"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_W_PX" "28"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_H_PX" "28"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AREA_PX2" "900"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_W_PX" "150"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_H_PX" "170"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AREA_PX2" "22000"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AR" "0.70"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AR" "1.40"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_WZ" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_WZ" ""
      ;;
    head-yolov8-host-depth-wz)
      # Strict + depth gate + physical width-vs-depth constraint (w*Z) to suppress false detections.
      append_kv "CAM_DEPTH_COUNT_BACKEND" "host-yolov8-raw"
      append_kv "CAM_DEPTH_ENABLE" "1"
      append_kv "CAM_DEPTH_MIN_M" "0.40"
      append_kv "CAM_DEPTH_MAX_M" "1.80"
      append_kv "CAM_DEPTH_HEAD_FRACTION" "0.60"
      append_kv "CAM_DEPTH_HEAD_REGION" "top"
      append_kv "CAM_DEPTH_COUNT_AXIS" "x"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.01"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.22"
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "center"
      append_kv "CAM_DEPTH_COUNT_INFER_MIDDLE_FROM_SPAN" "0"
      append_kv "CAM_DEPTH_COUNT_MIN_SIDE_FRAMES_BEFORE_MIDDLE" "2"
      append_kv "CAM_DEPTH_COUNT_MAX_JUMP_PX" "120"
      append_kv "CAM_DEPTH_COUNT_ROI" ""
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.30"
      append_kv "CAM_DEPTH_COUNT_DNN_CONFIDENCE" "0.20"
      append_kv "CAM_DEPTH_COUNT_NMS_IOU" "0.5"
      append_kv "CAM_DEPTH_COUNT_MAX_DET" "120"
      append_kv "CAM_DEPTH_COUNT_MATCH_DIST_PX" "120"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "2"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "10"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.50"
      append_kv "CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC" "0.90"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.02"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_W_PX" "28"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_H_PX" "28"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AREA_PX2" "900"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_W_PX" "150"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_H_PX" "170"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AREA_PX2" "22000"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AR" "0.70"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AR" "1.40"
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_WZ" "45"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_WZ" "110"
      ;;
    head-yolov8-host-nofilter)
      # Debug preset: disable bbox filters completely to validate geometry/counting logic.
      append_kv "CAM_DEPTH_COUNT_BACKEND" "host-yolov8-raw"
      append_kv "CAM_DEPTH_ENABLE" "0"
      append_kv "CAM_DEPTH_COUNT_AXIS" "x"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.01"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.22"
      append_kv "CAM_DEPTH_COUNT_ROI" ""
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "leading_edge"
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.06"
      append_kv "CAM_DEPTH_COUNT_DNN_CONFIDENCE" "0.04"
      append_kv "CAM_DEPTH_COUNT_NMS_IOU" "0.55"
      append_kv "CAM_DEPTH_COUNT_MAX_DET" "220"
      append_kv "CAM_DEPTH_COUNT_MATCH_DIST_PX" "180"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "1"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "14"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.25"
      append_kv "CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC" "0.45"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.02"
      # Disable bbox filters
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_W_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_H_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AREA_PX2" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_W_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_H_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AREA_PX2" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AR" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AR" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_WZ" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_WZ" ""
      ;;
    head-yolov8-host-depth-wz-commissioning)
      # Commissioning: keep bbox filters disabled, but enable depth gate + w*Z to suppress many false positives.
      append_kv "CAM_DEPTH_COUNT_BACKEND" "host-yolov8-raw"
      append_kv "CAM_DEPTH_ENABLE" "1"
      append_kv "CAM_DEPTH_MIN_M" "0.40"
      append_kv "CAM_DEPTH_MAX_M" "1.80"
      append_kv "CAM_DEPTH_HEAD_FRACTION" "0.60"
      append_kv "CAM_DEPTH_HEAD_REGION" "top"
      append_kv "CAM_DEPTH_COUNT_AXIS" "x"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.01"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.22"
      append_kv "CAM_DEPTH_COUNT_ROI" ""
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "leading_edge"
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.06"
      append_kv "CAM_DEPTH_COUNT_DNN_CONFIDENCE" "0.04"
      append_kv "CAM_DEPTH_COUNT_NMS_IOU" "0.55"
      append_kv "CAM_DEPTH_COUNT_MAX_DET" "220"
      append_kv "CAM_DEPTH_COUNT_MATCH_DIST_PX" "180"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "1"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "14"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.25"
      append_kv "CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC" "0.45"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.02"
      # Disable bbox filters (commissioning).
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_W_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_H_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AREA_PX2" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_W_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_H_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AREA_PX2" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AR" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AR" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_WZ" "45"
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_WZ" "110"
      ;;
    head-yolov8-host-depth-commissioning)
      # Depth commissioning: validate depth availability first (without w*Z); widen depth output to reduce depth_missing.
      append_kv "CAM_DEPTH_COUNT_BACKEND" "host-yolov8-raw"
      append_kv "CAM_DEPTH_ENABLE" "1"
      append_kv "CAM_DEPTH_MIN_M" "0.35"
      append_kv "CAM_DEPTH_MAX_M" "2.20"
      append_kv "CAM_DEPTH_OUTPUT_SIZE" "640x400"
      append_kv "CAM_DEPTH_HEAD_FRACTION" "1.00"
      append_kv "CAM_DEPTH_HEAD_REGION" "top"
      append_kv "CAM_DEPTH_MIN_VALID_PX" "8"
      append_kv "CAM_DEPTH_COUNT_AXIS" "x"
      append_kv "CAM_DEPTH_COUNT_AXIS_POS" "0.50"
      append_kv "CAM_DEPTH_COUNT_AXIS_HYST" "0.01"
      append_kv "CAM_DEPTH_COUNT_LINE_GAP_NORM" "0.22"
      append_kv "CAM_DEPTH_COUNT_ROI" ""
      append_kv "CAM_DEPTH_COUNT_ANCHOR_MODE" "leading_edge"
      append_kv "CAM_DEPTH_COUNT_CONFIDENCE" "0.06"
      append_kv "CAM_DEPTH_COUNT_DNN_CONFIDENCE" "0.04"
      append_kv "CAM_DEPTH_COUNT_NMS_IOU" "0.55"
      append_kv "CAM_DEPTH_COUNT_MAX_DET" "220"
      append_kv "CAM_DEPTH_COUNT_MATCH_DIST_PX" "180"
      append_kv "CAM_DEPTH_COUNT_MIN_TRACK_AGE" "1"
      append_kv "CAM_DEPTH_COUNT_MAX_LOST_FRAMES" "14"
      append_kv "CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC" "0.25"
      append_kv "CAM_DEPTH_COUNT_PER_TRACK_REARM_SEC" "0.45"
      append_kv "CAM_DEPTH_COUNT_MIN_MOVE_NORM" "0.02"
      # Disable bbox filters
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_W_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_H_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AREA_PX2" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_W_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_H_PX" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AREA_PX2" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_AR" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_AR" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MIN_WZ" ""
      append_kv "CAM_DEPTH_COUNT_BBOX_MAX_WZ" ""
      ;;
    *)
      echo "ERROR: unknown preset '${PRESET}'. Allowed: baseline|wide-scan|door-tight|transport-strict|transport-fast-pass|commissioning-no-depth|commissioning-depth-soft|head-yolov8-host|head-yolov8-host-loose|head-yolov8-host-strict|head-yolov8-host-depth-wz|head-yolov8-host-nofilter|head-yolov8-host-depth-wz-commissioning|head-yolov8-host-depth-commissioning" >&2
      exit 2
      ;;
  esac
}

apply_kv_remote() {
  local kv="$1"
  local key="${kv%%=*}"
  local value="${kv#*=}"
  if [[ -z "${key}" || "${key}" == "${value}" ]]; then
    echo "ERROR: invalid --set '${kv}', expected KEY=VALUE" >&2
    exit 2
  fi
  ssh "${HOST}" "sudo touch '${ENV_FILE}';
if sudo grep -q '^${key}=' '${ENV_FILE}'; then
  sudo sed -i 's|^${key}=.*|${key}=${value}|' '${ENV_FILE}';
else
  echo '${key}=${value}' | sudo tee -a '${ENV_FILE}' >/dev/null;
fi"
}

health_snapshot() {
  local port="8091"
  port="$(ssh "${HOST}" "sudo awk -F= '/^CAM_DEBUG_PORT=/{print \$2; exit}' '${ENV_FILE}' 2>/dev/null || true" | tr -d '\r' | tail -n 1)"
  if [[ -z "${port}" ]]; then
    port="8091"
  fi
  local waited=0
  local step=2
  echo "--- /health ---"
  while (( waited <= HEALTH_WAIT_SEC )); do
    if ssh "${HOST}" "curl -fsS --max-time 2 http://127.0.0.1:${port}/health"; then
      echo
      return 0
    fi
    sleep "${step}"
    waited=$((waited + step))
  done
  echo "WARN: health endpoint still unavailable after ${HEALTH_WAIT_SEC}s"
  return 1
}

if [[ "${SHOW_ONLY}" == "1" && -z "${PRESET}" && ${#SETS_USER[@]} -eq 0 ]]; then
  show_current
  if [[ "${HEALTH_SNAPSHOT}" == "1" ]]; then
    health_snapshot || true
  fi
  exit 0
fi

apply_preset
if [[ ${#SETS_USER[@]} -gt 0 ]]; then
  SETS+=("${SETS_USER[@]}")
fi

if [[ ${#SETS[@]} -eq 0 ]]; then
  echo "No updates requested. Use --preset and/or --set KEY=VALUE." >&2
  exit 2
fi

echo "Applying ${#SETS[@]} setting(s) on ${HOST}"
for kv in "${SETS[@]}"; do
  apply_kv_remote "${kv}"
  echo "  ok: ${kv}"
done

ssh "${HOST}" "sudo chown root:${OPI_USER} '${ENV_FILE}'; sudo chmod 640 '${ENV_FILE}'"

if [[ "${RESTART_SERVICE}" == "1" ]]; then
  ssh "${HOST}" "sudo systemctl restart '${SERVICE_NAME}'"
  echo "Service restarted: ${SERVICE_NAME}"
fi

show_current

if [[ "${HEALTH_SNAPSHOT}" == "1" ]]; then
  health_snapshot || true
fi

echo "Calibration step done."
