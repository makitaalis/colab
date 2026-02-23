#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
camera_mode_switch.sh — switch camera mode on a target node (Central or Door)

Modes:
  prod            Run production counter service (passengers-camera-counter.service)
  debug-stream    Run debug MJPEG stream service (passengers-camera-debug-stream.service)
  depth-counting  Run transport strict counting service (person + track_id + two lines)
  depth-height-multi  Run stereo-only depth height multi-tracking service
  oak-viewer      Stop all camera services and free camera for manual oak-viewer diagnostics

Usage:
  ./scripts/camera_mode_switch.sh --mode <prod|debug-stream|depth-counting|depth-height-multi|oak-viewer> [options]

Options:
  --camera-ip <ip>    Camera node IP (default: 192.168.10.1)
  --central-ip <ip>   Alias for --camera-ip (backward compatible)
  --user <name>       SSH user (default: orangepi)
  --debug-bind <ip>   Debug stream bind IP (default: 127.0.0.1)
  --debug-port <n>    Debug stream port (default: 8091)
  --status            Show current status only
  -h, --help          Show help
USAGE
}

MODE=""
CAMERA_IP="192.168.10.1"
OPI_USER="orangepi"
DEBUG_BIND="127.0.0.1"
DEBUG_PORT="8091"
STATUS_ONLY="0"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --mode) MODE="${2:-}"; shift 2 ;;
    --camera-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --central-ip) CAMERA_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --debug-bind) DEBUG_BIND="${2:-}"; shift 2 ;;
    --debug-port) DEBUG_PORT="${2:-}"; shift 2 ;;
    --status) STATUS_ONLY="1"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ "${STATUS_ONLY}" != "1" ]]; then
  case "${MODE}" in
    prod|debug-stream|depth-counting|depth-height-multi|oak-viewer) ;;
    *) echo "ERROR: --mode must be prod|debug-stream|depth-counting|depth-height-multi|oak-viewer" >&2; usage; exit 2 ;;
  esac
fi

HOST="${OPI_USER}@${CAMERA_IP}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REMOTE_DIR="/opt/passengers-mvp"
ENV_FILE="/etc/passengers/passengers.env"

ssh -n -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

show_status() {
  ssh -n "${HOST}" "echo '--- services ---';
for u in passengers-camera-counter.service passengers-camera-debug-stream.service passengers-camera-depth-counting.service passengers-camera-depth-height-multi.service; do
  echo \"[\$u]\";
  systemctl is-enabled \$u 2>/dev/null || true;
  systemctl is-active \$u 2>/dev/null || true;
done
echo '--- recent logs (counter) ---';
journalctl -u passengers-camera-counter.service -n 8 --no-pager 2>/dev/null || true
echo '--- recent logs (debug-stream) ---';
journalctl -u passengers-camera-debug-stream.service -n 8 --no-pager 2>/dev/null || true
echo '--- recent logs (depth-counting) ---';
journalctl -u passengers-camera-depth-counting.service -n 8 --no-pager 2>/dev/null || true
echo '--- recent logs (depth-height-multi) ---';
journalctl -u passengers-camera-depth-height-multi.service -n 8 --no-pager 2>/dev/null || true"
}

if [[ "${STATUS_ONLY}" == "1" ]]; then
  show_status
  exit 0
fi

sync_mvp() {
  ssh -n "${HOST}" "sudo mkdir -p '${REMOTE_DIR}' && sudo chown -R ${OPI_USER}:${OPI_USER} '${REMOTE_DIR}'"
  rsync -av --delete "${REPO_ROOT}/mvp/" "${HOST}:${REMOTE_DIR}/"
  ssh -n "${HOST}" "mkdir -p /home/${OPI_USER}/.cache /home/${OPI_USER}/.depthai_cached_models && chmod 700 /home/${OPI_USER}/.cache /home/${OPI_USER}/.depthai_cached_models"
}

ensure_env_defaults() {
  ssh -n "${HOST}" "sudo touch '${ENV_FILE}'
if ! sudo grep -q '^CAM_DEBUG_BIND=' '${ENV_FILE}'; then echo 'CAM_DEBUG_BIND=${DEBUG_BIND}' | sudo tee -a '${ENV_FILE}' >/dev/null; else sudo sed -i 's|^CAM_DEBUG_BIND=.*|CAM_DEBUG_BIND=${DEBUG_BIND}|' '${ENV_FILE}'; fi
if ! sudo grep -q '^CAM_DEBUG_PORT=' '${ENV_FILE}'; then echo 'CAM_DEBUG_PORT=${DEBUG_PORT}' | sudo tee -a '${ENV_FILE}' >/dev/null; else sudo sed -i 's|^CAM_DEBUG_PORT=.*|CAM_DEBUG_PORT=${DEBUG_PORT}|' '${ENV_FILE}'; fi
if ! sudo grep -q '^CAM_DEPTH_ENABLE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_ENABLE=1' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MIN_M=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MIN_M=0.40' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MAX_M=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MAX_M=1.50' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_HEAD_FRACTION=' '${ENV_FILE}'; then echo 'CAM_DEPTH_HEAD_FRACTION=0.45' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MIN_VALID_PX=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MIN_VALID_PX=25' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_FPS=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_FPS=10' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_MODEL=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_MODEL=yolov6-nano' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_MODEL_INPUT_SIZE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_MODEL_INPUT_SIZE=512x288' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_AXIS=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_AXIS=y' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_AXIS_POS=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_AXIS_POS=0.50' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_AXIS_HYST=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_AXIS_HYST=0.04' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_LINE_GAP_NORM=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_LINE_GAP_NORM=0.22' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_ANCHOR_MODE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_ANCHOR_MODE=center' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_CONFIDENCE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_CONFIDENCE=0.55' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_TRACKER_TYPE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_TRACKER_TYPE=short_term_imageless' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_MIN_TRACK_AGE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_MIN_TRACK_AGE=5' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_MAX_LOST_FRAMES=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_MAX_LOST_FRAMES=6' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_HANG_TIMEOUT_SEC=3.0' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_MIN_MOVE_NORM=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_MIN_MOVE_NORM=0.12' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_ROI=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_ROI=0.05,0.10,0.95,0.95' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_THRESHOLD_LOW=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_THRESHOLD_LOW=125' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_THRESHOLD_HIGH=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_THRESHOLD_HIGH=145' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_AREA_MIN=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_AREA_MIN=5000' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_KERNEL_SIZE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_KERNEL_SIZE=37' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_TRACK_GAP_SEC=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_TRACK_GAP_SEC=0.80' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC=0.60' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_INVERT=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_INVERT=0' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_FPS=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_FPS=10' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_MIN_M=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_MIN_M=0.35' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_MAX_M=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_MAX_M=0.95' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_PREVIEW_SIZE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_PREVIEW_SIZE=416x256' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_PREVIEW_FPS=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_PREVIEW_FPS=5' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_OUTPUT_SIZE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_OUTPUT_SIZE=320x200' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_AREA_MIN=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_AREA_MIN=180' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_KERNEL_SIZE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_KERNEL_SIZE=7' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_MAX_OBJECTS=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_MAX_OBJECTS=20' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_MATCH_DIST_PX=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_MATCH_DIST_PX=40' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_MIN_TRACK_AGE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_MIN_TRACK_AGE=3' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_MAX_LOST_FRAMES=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_MAX_LOST_FRAMES=6' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_HANG_TIMEOUT_SEC=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_HANG_TIMEOUT_SEC=3.0' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_COUNT_COOLDOWN_SEC=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_COUNT_COOLDOWN_SEC=1.0' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_PER_TRACK_REARM_SEC=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_PER_TRACK_REARM_SEC=1.2' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_WATERSHED_ENABLE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_WATERSHED_ENABLE=1' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MULTI_WATERSHED_DIST_RATIO=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MULTI_WATERSHED_DIST_RATIO=0.38' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_IMU_ENABLE=' '${ENV_FILE}'; then echo 'CAM_IMU_ENABLE=1' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_IMU_RATE_HZ=' '${ENV_FILE}'; then echo 'CAM_IMU_RATE_HZ=100' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_JPEG_QUALITY=' '${ENV_FILE}'; then echo 'CAM_JPEG_QUALITY=70' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
sudo chown root:${OPI_USER} '${ENV_FILE}'
sudo chmod 640 '${ENV_FILE}'"
}

ensure_debug_service() {
  sync_mvp
  ensure_env_defaults
  ssh -n "${HOST}" "sudo tee /etc/systemd/system/passengers-camera-debug-stream.service >/dev/null <<'UNIT'
[Unit]
Description=Passengers camera debug stream (OAK-D Lite MJPEG)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=120
StartLimitBurst=3

[Service]
User=${OPI_USER}
Group=${OPI_USER}
Environment=HOME=/home/${OPI_USER}
Environment=XDG_CACHE_HOME=/home/${OPI_USER}/.cache
WorkingDirectory=/home/${OPI_USER}
EnvironmentFile=${ENV_FILE}
TimeoutStartSec=330
ExecStartPre=/usr/bin/bash -lc 'for i in 1 2 3 4 5 6 7 8 9 10; do lsusb | grep -Eiq \"03e7:(2485|f63b)\" && exit 0; sleep 0.5; done; exit 1'
ExecStartPre=/usr/bin/python3 ${REMOTE_DIR}/preflight.py --mode central-collector --wait-timeout-sec 300 --poll-sec 2 --skip-time-sync
ExecStart=/usr/bin/bash -lc 'PY=/opt/passengers-venv/bin/python; [ -x \"\$PY\" ] || PY=/usr/bin/python3; exec \"\$PY\" ${REMOTE_DIR}/camera_debug_stream.py --env ${ENV_FILE} --bind ${DEBUG_BIND} --port ${DEBUG_PORT}'
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload"
}

ensure_depth_counting_service() {
  sync_mvp
  ensure_env_defaults
  ssh -n "${HOST}" "sudo tee /etc/systemd/system/passengers-camera-depth-counting.service >/dev/null <<'UNIT'
[Unit]
Description=Passengers transport strict counting (person+track_id+2 lines)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=120
StartLimitBurst=3

[Service]
User=${OPI_USER}
Group=${OPI_USER}
Environment=HOME=/home/${OPI_USER}
Environment=XDG_CACHE_HOME=/home/${OPI_USER}/.cache
WorkingDirectory=/home/${OPI_USER}
EnvironmentFile=${ENV_FILE}
TimeoutStartSec=330
ExecStartPre=/usr/bin/bash -lc 'for i in 1 2 3 4 5 6 7 8 9 10; do lsusb | grep -Eiq \"03e7:(2485|f63b)\" && exit 0; sleep 0.5; done; exit 1'
ExecStartPre=/usr/bin/python3 ${REMOTE_DIR}/preflight.py --mode central-collector --wait-timeout-sec 300 --poll-sec 2 --skip-time-sync
ExecStart=/usr/bin/bash -lc 'PY=/opt/passengers-venv/bin/python; [ -x \"\$PY\" ] || PY=/usr/bin/python3; exec \"\$PY\" ${REMOTE_DIR}/camera_transport_strict_counting.py --env ${ENV_FILE} --bind ${DEBUG_BIND} --port ${DEBUG_PORT}'
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload"
}

ensure_depth_height_multi_service() {
  sync_mvp
  ensure_env_defaults
  ssh -n "${HOST}" "sudo tee /etc/systemd/system/passengers-camera-depth-height-multi.service >/dev/null <<'UNIT'
[Unit]
Description=Passengers stereo-only depth height multi-tracking (2 lines)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=120
StartLimitBurst=3

[Service]
User=${OPI_USER}
Group=${OPI_USER}
Environment=HOME=/home/${OPI_USER}
Environment=XDG_CACHE_HOME=/home/${OPI_USER}/.cache
WorkingDirectory=/home/${OPI_USER}
EnvironmentFile=${ENV_FILE}
TimeoutStartSec=330
ExecStartPre=/usr/bin/bash -lc 'for i in 1 2 3 4 5 6 7 8 9 10; do lsusb | grep -Eiq \"03e7:(2485|f63b)\" && exit 0; sleep 0.5; done; exit 1'
ExecStartPre=/usr/bin/python3 ${REMOTE_DIR}/preflight.py --mode central-collector --wait-timeout-sec 300 --poll-sec 2 --skip-time-sync
ExecStart=/usr/bin/bash -lc 'PY=/opt/passengers-venv/bin/python; [ -x \"\$PY\" ] || PY=/usr/bin/python3; exec \"\$PY\" ${REMOTE_DIR}/camera_depth_height_multi.py --env ${ENV_FILE} --bind ${DEBUG_BIND} --port ${DEBUG_PORT}'
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload"
}

switch_prod() {
  ssh -n "${HOST}" "sudo systemctl disable --now passengers-camera-debug-stream.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-depth-counting.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-depth-height-multi.service >/dev/null 2>&1 || true
sudo systemctl enable --now passengers-camera-counter.service
sudo systemctl restart passengers-camera-counter.service"
  echo "Mode switched: prod"
}

switch_debug_stream() {
  ensure_debug_service
  ssh -n "${HOST}" "sudo systemctl disable --now passengers-camera-counter.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-depth-counting.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-depth-height-multi.service >/dev/null 2>&1 || true
sudo systemctl enable --now passengers-camera-debug-stream.service
sudo systemctl restart passengers-camera-debug-stream.service"
  echo "Mode switched: debug-stream"
  if [[ "${DEBUG_BIND}" == "127.0.0.1" ]]; then
    cat <<INFO
Open stream on PC via SSH tunnel:
  ssh -N -L ${DEBUG_PORT}:127.0.0.1:${DEBUG_PORT} ${HOST}
Then open in browser:
  http://127.0.0.1:${DEBUG_PORT}/
INFO
  else
    echo "Open in browser: http://${CAMERA_IP}:${DEBUG_PORT}/"
  fi
}

switch_depth_counting() {
  ensure_depth_counting_service
  ssh -n "${HOST}" "sudo systemctl disable --now passengers-camera-counter.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-debug-stream.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-depth-height-multi.service >/dev/null 2>&1 || true
sudo systemctl enable --now passengers-camera-depth-counting.service
sudo systemctl restart passengers-camera-depth-counting.service"
  echo "Mode switched: depth-counting"
  if [[ "${DEBUG_BIND}" == "127.0.0.1" ]]; then
    cat <<INFO
Open depth-counting stream on PC via SSH tunnel:
  ssh -N -L ${DEBUG_PORT}:127.0.0.1:${DEBUG_PORT} ${HOST}
Then open in browser:
  http://127.0.0.1:${DEBUG_PORT}/
INFO
  else
    echo "Open in browser: http://${CAMERA_IP}:${DEBUG_PORT}/"
  fi
}

switch_depth_height_multi() {
  ensure_depth_height_multi_service
  ssh -n "${HOST}" "sudo systemctl disable --now passengers-camera-counter.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-debug-stream.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-depth-counting.service >/dev/null 2>&1 || true
sudo systemctl enable --now passengers-camera-depth-height-multi.service
sudo systemctl restart passengers-camera-depth-height-multi.service"
  echo "Mode switched: depth-height-multi"
  if [[ "${DEBUG_BIND}" == "127.0.0.1" ]]; then
    cat <<INFO
Open depth-height-multi stream on PC via SSH tunnel:
  ssh -N -L ${DEBUG_PORT}:127.0.0.1:${DEBUG_PORT} ${HOST}
Then open in browser:
  http://127.0.0.1:${DEBUG_PORT}/
INFO
  else
    echo "Open in browser: http://${CAMERA_IP}:${DEBUG_PORT}/"
  fi
}

switch_oak_viewer() {
  ssh -n "${HOST}" "sudo systemctl disable --now passengers-camera-counter.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-debug-stream.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-depth-counting.service >/dev/null 2>&1 || true
sudo systemctl disable --now passengers-camera-depth-height-multi.service >/dev/null 2>&1 || true"
  cat <<INFO
Mode switched: oak-viewer (camera is freed, services stopped).
On your PC run oak-viewer manually for diagnostics.
After diagnostics return to production:
  ./scripts/camera_mode_switch.sh --mode prod --camera-ip ${CAMERA_IP} --user ${OPI_USER}
INFO
}

case "${MODE}" in
  prod) switch_prod ;;
  debug-stream) switch_debug_stream ;;
  depth-counting) switch_depth_counting ;;
  depth-height-multi) switch_depth_height_multi ;;
  oak-viewer) switch_oak_viewer ;;
esac

show_status
