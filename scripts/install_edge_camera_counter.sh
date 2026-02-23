#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
install_edge_camera_counter.sh — deploy camera counter service to an edge node (door)

Installs prerequisites (python3-opencv + pip depthai) and configures:
  - passengers-camera-counter.service (stores to edge outbox for edge_sender)

Usage:
  ./scripts/install_edge_camera_counter.sh [options]

Options:
  --edge-ip <ip>            Edge node IP with camera (default: 192.168.10.11)
  --camera-ip <ip>          Alias for --edge-ip
  --user <name>             SSH user (default: orangepi)
  --env-file <path>         Env file on node (default: /etc/passengers/passengers.env)
  --remote-dir <path>       Remote MVP dir (default: /opt/passengers-mvp)
  --db <path>               Edge DB path (default: /var/lib/passengers/edge.sqlite3)
  --door-id <n>             door_id for this camera (default: 2)
  --warmup-seconds <n>      Dry-run warmup seconds before enabling service (default: 15)
  --no-enable               Install unit but do not enable/start service
  -h, --help                Show help

Notes:
  - Requires passwordless sudo on the node (recommended for automation).
  - Camera must be visible in `lsusb` as Myriad VPU (`03e7:2485` or `03e7:f63b`).
USAGE
}

EDGE_IP="192.168.10.11"
OPI_USER="orangepi"
ENV_FILE="/etc/passengers/passengers.env"
REMOTE_DIR="/opt/passengers-mvp"
EDGE_DB="/var/lib/passengers/edge.sqlite3"
DOOR_ID="2"
WARMUP_SECONDS="15"
ENABLE_SERVICE="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --edge-ip) EDGE_IP="${2:-}"; shift 2 ;;
    --camera-ip) EDGE_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --env-file) ENV_FILE="${2:-}"; shift 2 ;;
    --remote-dir) REMOTE_DIR="${2:-}"; shift 2 ;;
    --db) EDGE_DB="${2:-}"; shift 2 ;;
    --door-id) DOOR_ID="${2:-}"; shift 2 ;;
    --warmup-seconds) WARMUP_SECONDS="${2:-}"; shift 2 ;;
    --no-enable) ENABLE_SERVICE="0"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

HOST="${OPI_USER}@${EDGE_IP}"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

echo "== Installing system deps on ${HOST} =="
ssh "${HOST}" "export DEBIAN_FRONTEND=noninteractive
sudo -E apt-get update -y >/dev/null
sudo -E apt-get install -y --no-install-recommends python3-venv python3-pip python3-opencv python3-numpy usbutils ca-certificates curl >/dev/null
echo 'SUBSYSTEM==\"usb\", ATTRS{idVendor}==\"03e7\", MODE=\"0666\"' | sudo tee /etc/udev/rules.d/80-movidius.rules >/dev/null
sudo udevadm control --reload-rules
sudo udevadm trigger
sudo mkdir -p /opt/passengers-venv && sudo chown -R ${OPI_USER}:${OPI_USER} /opt/passengers-venv
python3 -m venv --system-site-packages /opt/passengers-venv >/dev/null
/opt/passengers-venv/bin/pip install -q --upgrade pip
/opt/passengers-venv/bin/pip install -q --upgrade 'depthai==3.3.0'
/opt/passengers-venv/bin/python -c 'import depthai as dai; print(\"depthai\", dai.__version__)' >/dev/null"

echo "== Syncing MVP code to ${HOST}:${REMOTE_DIR} =="
ssh "${HOST}" "sudo mkdir -p '${REMOTE_DIR}' '/var/lib/passengers' '/etc/passengers' && sudo chown -R ${OPI_USER}:${OPI_USER} '${REMOTE_DIR}' '/var/lib/passengers'"
rsync -av --delete "${REPO_ROOT}/mvp/" "${HOST}:${REMOTE_DIR}/"

ssh "${HOST}" "mkdir -p /home/${OPI_USER}/.cache /home/${OPI_USER}/.depthai_cached_models && chmod 700 /home/${OPI_USER}/.cache /home/${OPI_USER}/.depthai_cached_models"

echo "== Ensuring env defaults on ${HOST}:${ENV_FILE} =="
ssh "${HOST}" "sudo touch '${ENV_FILE}'
if ! sudo grep -q '^NODE_ID=' '${ENV_FILE}'; then echo 'NODE_ID=door-unknown' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^NODE_ROLE=' '${ENV_FILE}'; then echo 'NODE_ROLE=edge' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^DOOR_ID=' '${ENV_FILE}'; then echo 'DOOR_ID=${DOOR_ID}' | sudo tee -a '${ENV_FILE}' >/dev/null; fi
if ! sudo grep -q '^CAM_COUNTER_STORE=' '${ENV_FILE}'; then echo 'CAM_COUNTER_STORE=edge' | sudo tee -a '${ENV_FILE}' >/dev/null; else sudo sed -i 's|^CAM_COUNTER_STORE=.*|CAM_COUNTER_STORE=edge|' '${ENV_FILE}'; fi
if ! sudo grep -q '^CAM_COUNTER_DOOR_ID=' '${ENV_FILE}'; then echo 'CAM_COUNTER_DOOR_ID=${DOOR_ID}' | sudo tee -a '${ENV_FILE}' >/dev/null; else sudo sed -i 's|^CAM_COUNTER_DOOR_ID=.*|CAM_COUNTER_DOOR_ID=${DOOR_ID}|' '${ENV_FILE}'; fi
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
sudo chown root:${OPI_USER} '${ENV_FILE}'
sudo chmod 640 '${ENV_FILE}'"

echo "== Installing systemd unit on ${HOST} =="
ssh "${HOST}" "sudo tee /etc/systemd/system/passengers-camera-counter.service >/dev/null <<'UNIT'
[Unit]
Description=Passengers camera counter (OAK-D Lite -> edge outbox)
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
ExecStart=/usr/bin/bash -lc 'PY=/opt/passengers-venv/bin/python; [ -x \"\$PY\" ] || PY=/usr/bin/python3; exec \"\$PY\" ${REMOTE_DIR}/camera_counter.py --env ${ENV_FILE} --store edge --db ${EDGE_DB}'
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload"

echo "== Warmup dry-run (${WARMUP_SECONDS}s) on ${HOST} =="
ssh "${HOST}" "python3 ${REMOTE_DIR}/camera_counter.py --env ${ENV_FILE} --store edge --db ${EDGE_DB} --dry-run --run-seconds ${WARMUP_SECONDS}" || true

if [[ "${ENABLE_SERVICE}" == "1" ]]; then
  ssh "${HOST}" "sudo systemctl enable --now passengers-camera-counter.service
sudo systemctl restart passengers-camera-counter.service
sudo systemctl --no-pager --full status passengers-camera-counter.service | sed -n '1,20p'"
else
  echo "Installed unit only (service not enabled due to --no-enable)"
fi

echo "Edge camera counter deployment complete on ${HOST}"
