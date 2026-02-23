#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
install_central_camera_counter.sh — deploy camera counter service to central-gw

Usage:
  ./scripts/install_central_camera_counter.sh [options]

Options:
  --central-ip <ip>          Central node IP (default: 192.168.10.1)
  --user <name>              SSH user (default: orangepi)
  --env-file <path>          Env file on node (default: /etc/passengers/passengers.env)
  --remote-dir <path>        Remote MVP dir (default: /opt/passengers-mvp)
  --db <path>                Central DB path (default: /var/lib/passengers/central.sqlite3)
  --warmup-seconds <n>       Dry-run warmup seconds before enabling service (default: 20)
  --no-enable                Install unit but do not enable/start service
  -h, --help                 Show help
USAGE
}

CENTRAL_IP="192.168.10.1"
OPI_USER="orangepi"
ENV_FILE="/etc/passengers/passengers.env"
REMOTE_DIR="/opt/passengers-mvp"
CENTRAL_DB="/var/lib/passengers/central.sqlite3"
WARMUP_SECONDS="20"
ENABLE_SERVICE="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --env-file) ENV_FILE="${2:-}"; shift 2 ;;
    --remote-dir) REMOTE_DIR="${2:-}"; shift 2 ;;
    --db) CENTRAL_DB="${2:-}"; shift 2 ;;
    --warmup-seconds) WARMUP_SECONDS="${2:-}"; shift 2 ;;
    --no-enable) ENABLE_SERVICE="0"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

HOST="${OPI_USER}@${CENTRAL_IP}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

ssh "${HOST}" "sudo mkdir -p '${REMOTE_DIR}' && sudo chown -R ${OPI_USER}:${OPI_USER} '${REMOTE_DIR}'"
rsync -av --delete "${REPO_ROOT}/mvp/" "${HOST}:${REMOTE_DIR}/"

ssh "${HOST}" "mkdir -p /home/${OPI_USER}/.cache /home/${OPI_USER}/.depthai_cached_models && chmod 700 /home/${OPI_USER}/.cache /home/${OPI_USER}/.depthai_cached_models"

ssh "${HOST}" "sudo touch '${ENV_FILE}'
if ! sudo grep -q '^NODE_ID=' '${ENV_FILE}'; then echo 'NODE_ID=central-gw' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_NODE_ID=' '${ENV_FILE}'; then echo 'CAM_COUNTER_NODE_ID=central-gw-cam' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_DOOR_ID=' '${ENV_FILE}'; then echo 'CAM_COUNTER_DOOR_ID=1' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_AXIS=' '${ENV_FILE}'; then echo 'CAM_COUNTER_AXIS=y' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_AXIS_POS=' '${ENV_FILE}'; then echo 'CAM_COUNTER_AXIS_POS=0.50' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_HYSTERESIS=' '${ENV_FILE}'; then echo 'CAM_COUNTER_HYSTERESIS=0.04' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_MIN_TRACK_AGE=' '${ENV_FILE}'; then echo 'CAM_COUNTER_MIN_TRACK_AGE=3' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_FPS=' '${ENV_FILE}'; then echo 'CAM_COUNTER_FPS=10' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_CONFIDENCE=' '${ENV_FILE}'; then echo 'CAM_COUNTER_CONFIDENCE=0.45' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_MODEL=' '${ENV_FILE}'; then echo 'CAM_COUNTER_MODEL=yolov6-nano' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_TRACKER_TYPE=' '${ENV_FILE}'; then echo 'CAM_COUNTER_TRACKER_TYPE=short_term_imageless' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_TRACKER_BIRTH=' '${ENV_FILE}'; then echo 'CAM_COUNTER_TRACKER_BIRTH=4' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_TRACKER_LIFESPAN=' '${ENV_FILE}'; then echo 'CAM_COUNTER_TRACKER_LIFESPAN=15' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_TRACKER_OCCLUSION=' '${ENV_FILE}'; then echo 'CAM_COUNTER_TRACKER_OCCLUSION=0.40' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_LOG_INTERVAL_SEC=' '${ENV_FILE}'; then echo 'CAM_COUNTER_LOG_INTERVAL_SEC=15' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_ENABLE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_ENABLE=1' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MIN_M=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MIN_M=0.40' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MAX_M=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MAX_M=1.50' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_HEAD_FRACTION=' '${ENV_FILE}'; then echo 'CAM_DEPTH_HEAD_FRACTION=0.45' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_MIN_VALID_PX=' '${ENV_FILE}'; then echo 'CAM_DEPTH_MIN_VALID_PX=25' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_FPS=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_FPS=10' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_AXIS=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_AXIS=y' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_AXIS_POS=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_AXIS_POS=0.50' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_AXIS_HYST=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_AXIS_HYST=0.04' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_ROI=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_ROI=0.05,0.10,0.95,0.95' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_THRESHOLD_LOW=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_THRESHOLD_LOW=125' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_THRESHOLD_HIGH=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_THRESHOLD_HIGH=145' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_AREA_MIN=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_AREA_MIN=5000' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_KERNEL_SIZE=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_KERNEL_SIZE=37' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_TRACK_GAP_SEC=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_TRACK_GAP_SEC=0.80' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_COUNT_COOLDOWN_SEC=0.60' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_DEPTH_COUNT_INVERT=' '${ENV_FILE}'; then echo 'CAM_DEPTH_COUNT_INVERT=0' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_IMU_ENABLE=' '${ENV_FILE}'; then echo 'CAM_IMU_ENABLE=1' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_IMU_RATE_HZ=' '${ENV_FILE}'; then echo 'CAM_IMU_RATE_HZ=100' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
sudo chown root:${OPI_USER} '${ENV_FILE}'
sudo chmod 640 '${ENV_FILE}'"

ssh "${HOST}" "sudo tee /etc/systemd/system/passengers-camera-counter.service >/dev/null <<UNIT
[Unit]
Description=Passengers camera counter (OAK-D Lite -> central events)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0

[Service]
User=${OPI_USER}
Group=${OPI_USER}
Environment=HOME=/home/${OPI_USER}
Environment=XDG_CACHE_HOME=/home/${OPI_USER}/.cache
WorkingDirectory=/home/${OPI_USER}
EnvironmentFile=${ENV_FILE}
TimeoutStartSec=330
ExecStartPre=/usr/bin/python3 ${REMOTE_DIR}/preflight.py --mode central-collector --wait-timeout-sec 300 --poll-sec 2
ExecStart=/usr/bin/python3 ${REMOTE_DIR}/camera_counter.py --env ${ENV_FILE} --db ${CENTRAL_DB}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload"

ssh "${HOST}" "python3 ${REMOTE_DIR}/camera_counter.py --env ${ENV_FILE} --db ${CENTRAL_DB} --dry-run --run-seconds ${WARMUP_SECONDS}" || true

if [[ "${ENABLE_SERVICE}" == "1" ]]; then
  ssh "${HOST}" "sudo systemctl enable --now passengers-camera-counter.service
sudo systemctl restart passengers-camera-counter.service
sudo systemctl --no-pager --full status passengers-camera-counter.service | sed -n '1,20p'"
else
  echo "Installed unit only (service not enabled due to --no-enable)"
fi

echo "Camera counter deployment complete on ${HOST}"
