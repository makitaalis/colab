#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
deploy_passengers_mvp.sh — deploy MVP services to one OPi system (central + 2 doors)

Usage:
  ./scripts/deploy_passengers_mvp.sh [options]

Options:
  --central-ip <ip>      Central IP (default: 192.168.10.1)
  --central-wifi-ip <ip> Central Wi‑Fi fallback IP (default: 192.168.20.1)
  --central-wifi-cidr <cidr> Central Wi‑Fi fallback CIDR (default: 192.168.20.0/24)
  --edge-ips <csv>       Edge IP list, comma separated (default: 192.168.10.11,192.168.10.12)
  --user <name>          SSH user for OPi nodes (default: orangepi)
  --server-host <host>   Backend server host for API key fetch (default: 207.180.213.225)
  --server-user <name>   SSH user on backend server (default: alis)
  --backend-host <ip>    Backend VPN host IP (default: 10.66.0.1)
  --central-port <port>  Collector port on central (default: 8080)
  --central-bind <ip>    Collector bind IP (default: 0.0.0.0)
  --stop-mode <mode>     Stop mode on central: timer|manual (default: manual)
  --stop-flush-interval-sec <n>  Flush timer interval in seconds (default: 120)
  --runtime-watchdog-sec <value>  systemd RuntimeWatchdogSec (default: 30s)
  --shutdown-watchdog-sec <value> systemd ShutdownWatchdogSec (default: 2min)
  --service-watchdog-interval-sec <n>  Passengers watchdog timer interval (default: 45)
  -h, --help             Show help

Environment overrides:
  CENTRAL_IP, CENTRAL_WIFI_IP, CENTRAL_WIFI_CIDR, EDGE_IPS_CSV, OPI_USER, SERVER_HOST, SERVER_SSH_USER, BACKEND_HOST, CENTRAL_PORT, CENTRAL_BIND,
  STOP_MODE, STOP_FLUSH_INTERVAL_SEC, RUNTIME_WATCHDOG_SEC, SHUTDOWN_WATCHDOG_SEC, SERVICE_WATCHDOG_INTERVAL_SEC
EOF
}

CENTRAL_IP="${CENTRAL_IP:-192.168.10.1}"
CENTRAL_WIFI_IP="${CENTRAL_WIFI_IP:-192.168.20.1}"
CENTRAL_WIFI_CIDR="${CENTRAL_WIFI_CIDR:-192.168.20.0/24}"
EDGE_IPS_CSV="${EDGE_IPS_CSV:-192.168.10.11,192.168.10.12}"
OPI_USER="${OPI_USER:-orangepi}"
SERVER_HOST="${SERVER_HOST:-207.180.213.225}"
SERVER_SSH_USER="${SERVER_SSH_USER:-alis}"
BACKEND_HOST="${BACKEND_HOST:-10.66.0.1}"
CENTRAL_PORT="${CENTRAL_PORT:-8080}"
CENTRAL_BIND="${CENTRAL_BIND:-}"
STOP_MODE="${STOP_MODE:-manual}"
STOP_FLUSH_INTERVAL_SEC="${STOP_FLUSH_INTERVAL_SEC:-120}"
RUNTIME_WATCHDOG_SEC="${RUNTIME_WATCHDOG_SEC:-30s}"
SHUTDOWN_WATCHDOG_SEC="${SHUTDOWN_WATCHDOG_SEC:-2min}"
SERVICE_WATCHDOG_INTERVAL_SEC="${SERVICE_WATCHDOG_INTERVAL_SEC:-45}"
EDGE_IPS=()

parse_args() {
  while [[ $# -gt 0 ]]; do
    case "$1" in
      --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
      --central-wifi-ip) CENTRAL_WIFI_IP="${2:-}"; shift 2 ;;
      --central-wifi-cidr) CENTRAL_WIFI_CIDR="${2:-}"; shift 2 ;;
      --edge-ips) EDGE_IPS_CSV="${2:-}"; shift 2 ;;
      --user) OPI_USER="${2:-}"; shift 2 ;;
      --server-host) SERVER_HOST="${2:-}"; shift 2 ;;
      --server-user) SERVER_SSH_USER="${2:-}"; shift 2 ;;
      --backend-host) BACKEND_HOST="${2:-}"; shift 2 ;;
      --central-port) CENTRAL_PORT="${2:-}"; shift 2 ;;
      --central-bind) CENTRAL_BIND="${2:-}"; shift 2 ;;
      --stop-mode) STOP_MODE="${2:-}"; shift 2 ;;
      --stop-flush-interval-sec) STOP_FLUSH_INTERVAL_SEC="${2:-}"; shift 2 ;;
      --runtime-watchdog-sec) RUNTIME_WATCHDOG_SEC="${2:-}"; shift 2 ;;
      --shutdown-watchdog-sec) SHUTDOWN_WATCHDOG_SEC="${2:-}"; shift 2 ;;
      --service-watchdog-interval-sec) SERVICE_WATCHDOG_INTERVAL_SEC="${2:-}"; shift 2 ;;
      -h|--help) usage; exit 0 ;;
      *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
    esac
  done
}

parse_edge_ips() {
  EDGE_IPS=()
  IFS=',' read -r -a EDGE_IPS <<<"${EDGE_IPS_CSV}"
  local cleaned=()
  local ip
  for ip in "${EDGE_IPS[@]}"; do
    ip="${ip//[[:space:]]/}"
    [[ -n "${ip}" ]] && cleaned+=("${ip}")
  done
  EDGE_IPS=("${cleaned[@]}")
}

derive_network_vars() {
  if [[ -z "${CENTRAL_BIND}" ]]; then
    CENTRAL_BIND="0.0.0.0"
  fi
  CENTRAL_URL="http://${CENTRAL_IP}:${CENTRAL_PORT}/api/v1/edge/events,http://${CENTRAL_WIFI_IP}:${CENTRAL_PORT}/api/v1/edge/events"
  CENTRAL_HEALTH_URL="http://${CENTRAL_IP}:${CENTRAL_PORT}/health,http://${CENTRAL_WIFI_IP}:${CENTRAL_PORT}/health"
  BACKEND_URL_DEFAULT="http://${BACKEND_HOST}/api/v1/ingest/stops"
  BACKEND_HEALTH_URL="http://${BACKEND_HOST}/health"
  BACKEND_HEARTBEAT_URL_DEFAULT="http://${BACKEND_HOST}/api/v1/ingest/central-heartbeat"
}

parse_args "$@"
parse_edge_ips
derive_network_vars

if [[ "${STOP_MODE}" != "timer" && "${STOP_MODE}" != "manual" ]]; then
  echo "ERROR: --stop-mode must be timer|manual (got: ${STOP_MODE})" >&2
  exit 2
fi

if ! [[ "${STOP_FLUSH_INTERVAL_SEC}" =~ ^[0-9]+$ ]] || [[ "${STOP_FLUSH_INTERVAL_SEC}" -lt 10 ]]; then
  echo "ERROR: --stop-flush-interval-sec must be integer >= 10 (got: ${STOP_FLUSH_INTERVAL_SEC})" >&2
  exit 2
fi
if ! [[ "${SERVICE_WATCHDOG_INTERVAL_SEC}" =~ ^[0-9]+$ ]] || [[ "${SERVICE_WATCHDOG_INTERVAL_SEC}" -lt 15 ]]; then
  echo "ERROR: --service-watchdog-interval-sec must be integer >= 15 (got: ${SERVICE_WATCHDOG_INTERVAL_SEC})" >&2
  exit 2
fi

if [[ ${#EDGE_IPS[@]} -lt 1 ]]; then
  echo "ERROR: at least one edge IP is required (use --edge-ips)" >&2
  exit 2
fi

REMOTE_DIR="/opt/passengers-mvp"
REMOTE_DATA_DIR="/var/lib/passengers"
REMOTE_ENV_DIR="/etc/passengers"
REMOTE_ENV_FILE="/etc/passengers/passengers.env"

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

require_ssh() {
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 "$1" "true" >/dev/null
}

deploy_files() {
  local host="$1"
  ssh "$host" "sudo mkdir -p '${REMOTE_DIR}' '${REMOTE_DATA_DIR}' '${REMOTE_ENV_DIR}' && sudo chown -R ${OPI_USER}:${OPI_USER} '${REMOTE_DIR}' '${REMOTE_DATA_DIR}'"
  rsync -a --delete "${REPO_ROOT}/mvp/" "${host}:${REMOTE_DIR}/"
}

install_unit_central() {
  local host="$1"
  ssh "$host" "sudo tee /etc/systemd/system/passengers-collector.service >/dev/null <<'EOF'
[Unit]
Description=Passengers collector (Edge -> Central)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0

[Service]
User=${OPI_USER}
Group=${OPI_USER}
TimeoutStartSec=330
ExecStartPre=/usr/bin/python3 ${REMOTE_DIR}/preflight.py --mode central-collector --wait-timeout-sec 300 --poll-sec 2
ExecStart=/usr/bin/python3 ${REMOTE_DIR}/collector.py --bind ${CENTRAL_BIND} --port ${CENTRAL_PORT} --db ${REMOTE_DATA_DIR}/central.sqlite3
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-collector.service
sudo systemctl restart passengers-collector.service
sudo systemctl --no-pager --full status passengers-collector.service | sed -n '1,12p'
"
}

install_unit_central_uplink() {
  local host="$1"
  ssh "$host" "sudo tee /etc/systemd/system/passengers-central-uplink.service >/dev/null <<'EOF'
[Unit]
Description=Passengers central uplink sender (SQLite -> Backend HTTP)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0

[Service]
User=${OPI_USER}
Group=${OPI_USER}
EnvironmentFile=${REMOTE_ENV_FILE}
TimeoutStartSec=330
ExecStartPre=/usr/bin/python3 ${REMOTE_DIR}/preflight.py --mode central-uplink --backend-health-url ${BACKEND_HEALTH_URL} --wait-timeout-sec 300 --poll-sec 2
ExecStart=/usr/bin/python3 ${REMOTE_DIR}/central_uplink_sender.py --db ${REMOTE_DATA_DIR}/central.sqlite3
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-central-uplink.service
sudo systemctl restart passengers-central-uplink.service
sudo systemctl --no-pager --full status passengers-central-uplink.service | sed -n '1,12p'
"
}

install_unit_central_flush() {
  local host="$1"
  ssh "$host" "sudo tee /etc/systemd/system/passengers-central-flush.service >/dev/null <<'EOF'
[Unit]
Description=Passengers central auto flush (manual stop emulation)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0

[Service]
Type=oneshot
User=${OPI_USER}
Group=${OPI_USER}
EnvironmentFile=${REMOTE_ENV_FILE}
TimeoutStartSec=330
ExecStartPre=/usr/bin/python3 ${REMOTE_DIR}/preflight.py --mode central-flush --wait-timeout-sec 300 --poll-sec 2
ExecStart=/usr/bin/python3 ${REMOTE_DIR}/central_flush.py --send-now --stop-mode ${STOP_MODE}
EOF
sudo tee /etc/systemd/system/passengers-central-flush.timer >/dev/null <<'EOF'
[Unit]
Description=Passengers central auto flush timer

[Timer]
OnBootSec=90s
OnUnitActiveSec=${STOP_FLUSH_INTERVAL_SEC}s
RandomizedDelaySec=15s
Persistent=true
Unit=passengers-central-flush.service

[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload
"
}

sync_central_stop_mode() {
  local host="$1"
  if [[ "${STOP_MODE}" == "manual" ]]; then
    ssh "$host" "sudo systemctl disable --now passengers-central-flush.timer >/dev/null 2>&1 || true
systemctl is-enabled passengers-central-flush.timer 2>/dev/null || true
systemctl is-active passengers-central-flush.timer 2>/dev/null || true"
  else
    ssh "$host" "sudo systemctl enable --now passengers-central-flush.timer
sudo systemctl restart passengers-central-flush.timer
sudo systemctl --no-pager --full status passengers-central-flush.timer | sed -n '1,12p'"
  fi
}

install_unit_central_heartbeat() {
  local host="$1"
  ssh "$host" "sudo tee /etc/systemd/system/passengers-central-heartbeat.service >/dev/null <<'EOF'
[Unit]
Description=Passengers central heartbeat reporter (Central -> Backend)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0

[Service]
Type=oneshot
User=root
Group=root
EnvironmentFile=${REMOTE_ENV_FILE}
TimeoutStartSec=330
ExecStartPre=/usr/bin/python3 ${REMOTE_DIR}/preflight.py --mode central-heartbeat --backend-health-url ${BACKEND_HEALTH_URL} --wait-timeout-sec 300 --poll-sec 2
ExecStart=/usr/bin/python3 ${REMOTE_DIR}/central_heartbeat.py --db ${REMOTE_DATA_DIR}/central.sqlite3
EOF
sudo tee /etc/systemd/system/passengers-central-heartbeat.timer >/dev/null <<'EOF'
[Unit]
Description=Passengers central heartbeat timer

[Timer]
OnBootSec=60s
OnUnitActiveSec=45s
RandomizedDelaySec=10s
Persistent=true
Unit=passengers-central-heartbeat.service

[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-central-heartbeat.timer
sudo systemctl restart passengers-central-heartbeat.timer
sudo systemctl --no-pager --full status passengers-central-heartbeat.timer | sed -n '1,12p'
"
}

install_unit_edge() {
  local host="$1"
  ssh "$host" "sudo tee /etc/systemd/system/passengers-edge-sender.service >/dev/null <<'EOF'
[Unit]
Description=Passengers edge sender (SQLite -> Central HTTP)
Wants=network-online.target
After=network-online.target
StartLimitIntervalSec=0

[Service]
User=${OPI_USER}
Group=${OPI_USER}
EnvironmentFile=${REMOTE_ENV_FILE}
TimeoutStartSec=330
ExecStartPre=/usr/bin/python3 ${REMOTE_DIR}/preflight.py --mode edge --central-health-url ${CENTRAL_HEALTH_URL} --wait-timeout-sec 300 --poll-sec 2
ExecStart=/usr/bin/python3 ${REMOTE_DIR}/edge_sender.py --db ${REMOTE_DATA_DIR}/edge.sqlite3
Restart=always
RestartSec=2

[Install]
WantedBy=multi-user.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-edge-sender.service
sudo systemctl restart passengers-edge-sender.service
sudo systemctl --no-pager --full status passengers-edge-sender.service | sed -n '1,12p'
"
}

install_unit_queue_maintenance() {
  local host="$1"
  ssh "$host" "sudo tee /etc/systemd/system/passengers-queue-maintenance.service >/dev/null <<'EOF'
[Unit]
Description=Passengers queue maintenance (retention/limits)
Wants=network-online.target
After=network-online.target

[Service]
Type=oneshot
User=${OPI_USER}
Group=${OPI_USER}
EnvironmentFile=${REMOTE_ENV_FILE}
ExecStart=/usr/bin/python3 ${REMOTE_DIR}/queue_maintainer.py --mode auto --env ${REMOTE_ENV_FILE} --edge-db ${REMOTE_DATA_DIR}/edge.sqlite3 --central-db ${REMOTE_DATA_DIR}/central.sqlite3
EOF
sudo tee /etc/systemd/system/passengers-queue-maintenance.timer >/dev/null <<'EOF'
[Unit]
Description=Passengers queue maintenance timer

[Timer]
OnBootSec=5m
OnUnitActiveSec=15m
RandomizedDelaySec=60s
Persistent=true
Unit=passengers-queue-maintenance.service

[Install]
WantedBy=timers.target
EOF
sudo systemctl daemon-reload
sudo systemctl enable --now passengers-queue-maintenance.timer
sudo systemctl restart passengers-queue-maintenance.timer
sudo systemctl start passengers-queue-maintenance.service
sudo systemctl --no-pager --full status passengers-queue-maintenance.timer | sed -n '1,12p'
"
}

install_unit_service_watchdog() {
  local host="$1"
  ssh "$host" "sudo tee /etc/systemd/system/passengers-service-watchdog.service >/dev/null <<'EOF'
[Unit]
Description=Passengers service watchdog (ensure critical units are active)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=root
Group=root
ExecStart=/usr/bin/python3 ${REMOTE_DIR}/service_watchdog.py --env ${REMOTE_ENV_FILE}
SuccessExitStatus=2
EOF
sudo tee /etc/systemd/system/passengers-service-watchdog.timer >/dev/null <<'EOF'
[Unit]
Description=Passengers service watchdog timer

[Timer]
OnBootSec=90s
OnUnitActiveSec=${SERVICE_WATCHDOG_INTERVAL_SEC}s
RandomizedDelaySec=5s
Persistent=true
Unit=passengers-service-watchdog.service

[Install]
WantedBy=timers.target
EOF
if grep -q '^#\\?RuntimeWatchdogSec=' /etc/systemd/system.conf; then
  sudo sed -i 's|^#\\?RuntimeWatchdogSec=.*|RuntimeWatchdogSec=${RUNTIME_WATCHDOG_SEC}|' /etc/systemd/system.conf
else
  echo 'RuntimeWatchdogSec=${RUNTIME_WATCHDOG_SEC}' | sudo tee -a /etc/systemd/system.conf >/dev/null
fi
if grep -q '^#\\?ShutdownWatchdogSec=' /etc/systemd/system.conf; then
  sudo sed -i 's|^#\\?ShutdownWatchdogSec=.*|ShutdownWatchdogSec=${SHUTDOWN_WATCHDOG_SEC}|' /etc/systemd/system.conf
else
  echo 'ShutdownWatchdogSec=${SHUTDOWN_WATCHDOG_SEC}' | sudo tee -a /etc/systemd/system.conf >/dev/null
fi
sudo systemctl daemon-reload
sudo systemctl daemon-reexec || true
sudo systemctl enable --now passengers-service-watchdog.timer
sudo systemctl restart passengers-service-watchdog.timer
sudo systemctl start passengers-service-watchdog.service
sudo systemctl --no-pager --full status passengers-service-watchdog.timer | sed -n '1,12p'
"
}

write_env_edge() {
  local host="$1"
  local node_id
  node_id="$(ssh "$host" "hostnamectl --static 2>/dev/null || hostname")"
  local door_id="0"
  case "$node_id" in
    door-1) door_id="2" ;;
    door-2) door_id="3" ;;
    *) door_id="0" ;;
  esac
  ssh "$host" "sudo tee '${REMOTE_ENV_FILE}' >/dev/null <<EOF
# Passengers project env (edge)
NODE_ID=${node_id}
DOOR_ID=${door_id}
NODE_ROLE=edge
CENTRAL_URL=${CENTRAL_URL}
CENTRAL_URL_COOLDOWN_SEC=5
EDGE_OUTBOX_MAX_ROWS=50000
EDGE_OUTBOX_MAX_AGE_SEC=172800
EOF
sudo chown root:${OPI_USER} '${REMOTE_ENV_FILE}'
sudo chmod 640 '${REMOTE_ENV_FILE}'
"
}

write_env_central_skeleton() {
  local host="$1"
  ssh "$host" "sudo touch '${REMOTE_ENV_FILE}'
if ! sudo grep -q '^VEHICLE_ID=' '${REMOTE_ENV_FILE}'; then
  echo 'VEHICLE_ID=bus-000_AA0000AA' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^BACKEND_URL=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^BACKEND_URL=.*|BACKEND_URL=${BACKEND_URL_DEFAULT}|' '${REMOTE_ENV_FILE}'
else
  echo 'BACKEND_URL=${BACKEND_URL_DEFAULT}' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^BACKEND_HEARTBEAT_URL=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^BACKEND_HEARTBEAT_URL=.*|BACKEND_HEARTBEAT_URL=${BACKEND_HEARTBEAT_URL_DEFAULT}|' '${REMOTE_ENV_FILE}'
else
  echo 'BACKEND_HEARTBEAT_URL=${BACKEND_HEARTBEAT_URL_DEFAULT}' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if ! sudo grep -q '^BACKEND_API_KEY=' '${REMOTE_ENV_FILE}'; then
  echo 'BACKEND_API_KEY=__PUT_REAL_KEY_HERE__' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^NODE_ROLE=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^NODE_ROLE=.*|NODE_ROLE=central|' '${REMOTE_ENV_FILE}'
else
  echo 'NODE_ROLE=central' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^STOP_MODE=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^STOP_MODE=.*|STOP_MODE=${STOP_MODE}|' '${REMOTE_ENV_FILE}'
else
  echo 'STOP_MODE=${STOP_MODE}' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^STOP_FLUSH_INTERVAL_SEC=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^STOP_FLUSH_INTERVAL_SEC=.*|STOP_FLUSH_INTERVAL_SEC=${STOP_FLUSH_INTERVAL_SEC}|' '${REMOTE_ENV_FILE}'
else
  echo 'STOP_FLUSH_INTERVAL_SEC=${STOP_FLUSH_INTERVAL_SEC}' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^CENTRAL_EVENTS_MAX_ROWS=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^CENTRAL_EVENTS_MAX_ROWS=.*|CENTRAL_EVENTS_MAX_ROWS=300000|' '${REMOTE_ENV_FILE}'
else
  echo 'CENTRAL_EVENTS_MAX_ROWS=300000' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^CENTRAL_EVENTS_MAX_AGE_SEC=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^CENTRAL_EVENTS_MAX_AGE_SEC=.*|CENTRAL_EVENTS_MAX_AGE_SEC=1209600|' '${REMOTE_ENV_FILE}'
else
  echo 'CENTRAL_EVENTS_MAX_AGE_SEC=1209600' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^CENTRAL_SENT_BATCHES_MAX_ROWS=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^CENTRAL_SENT_BATCHES_MAX_ROWS=.*|CENTRAL_SENT_BATCHES_MAX_ROWS=50000|' '${REMOTE_ENV_FILE}'
else
  echo 'CENTRAL_SENT_BATCHES_MAX_ROWS=50000' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^CENTRAL_SENT_BATCHES_MAX_AGE_SEC=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^CENTRAL_SENT_BATCHES_MAX_AGE_SEC=.*|CENTRAL_SENT_BATCHES_MAX_AGE_SEC=2592000|' '${REMOTE_ENV_FILE}'
else
  echo 'CENTRAL_SENT_BATCHES_MAX_AGE_SEC=2592000' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^CENTRAL_PENDING_BATCHES_MAX_ROWS=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^CENTRAL_PENDING_BATCHES_MAX_ROWS=.*|CENTRAL_PENDING_BATCHES_MAX_ROWS=10000|' '${REMOTE_ENV_FILE}'
else
  echo 'CENTRAL_PENDING_BATCHES_MAX_ROWS=10000' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^CENTRAL_PENDING_BATCHES_MAX_AGE_SEC=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^CENTRAL_PENDING_BATCHES_MAX_AGE_SEC=.*|CENTRAL_PENDING_BATCHES_MAX_AGE_SEC=2592000|' '${REMOTE_ENV_FILE}'
else
  echo 'CENTRAL_PENDING_BATCHES_MAX_AGE_SEC=2592000' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
if sudo grep -q '^CENTRAL_PENDING_BATCHES_DROP_AGE=' '${REMOTE_ENV_FILE}'; then
  sudo sed -i 's|^CENTRAL_PENDING_BATCHES_DROP_AGE=.*|CENTRAL_PENDING_BATCHES_DROP_AGE=0|' '${REMOTE_ENV_FILE}'
else
  echo 'CENTRAL_PENDING_BATCHES_DROP_AGE=0' | sudo tee -a '${REMOTE_ENV_FILE}' >/dev/null
fi
sudo chown root:${OPI_USER} '${REMOTE_ENV_FILE}'
sudo chmod 640 '${REMOTE_ENV_FILE}'
"
}

set_backend_key_from_server() {
  local host="$1"
  local api_key
  api_key="$(
    ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8 "${SERVER_SSH_USER}@${SERVER_HOST}" \
      "grep -m1 '^PASSENGERS_API_KEYS=' /opt/passengers-backend/.env | cut -d= -f2- | tr -d '\r' | cut -d, -f1" \
      | head -n1 | tr -d '\r'
  )"
  if [[ -z "${api_key}" ]]; then
    echo "WARN: failed to fetch backend api key from server"
    return 0
  fi
  ssh "$host" "sudo sed -i \"s/^BACKEND_API_KEY=.*/BACKEND_API_KEY=${api_key//\//\\/}/\" '${REMOTE_ENV_FILE}'"
}

open_central_port_firewall() {
  local host="$1"
  ssh "$host" "sudo tee /etc/nftables.conf >/dev/null <<'EOF'
#!/usr/sbin/nft -f

flush ruleset

 table inet filter {
  chain input {
    type filter hook input priority 0;
    policy drop;

    iif lo accept
    ct state established,related accept

    iifname \"end0\" tcp dport 22 accept
    iifname \"wlan0\" ip saddr ${CENTRAL_WIFI_CIDR} tcp dport 22 accept

    # management via WireGuard (VPS -> Central)
    iifname \"wg0\" ip saddr 10.66.0.0/24 tcp dport 22 accept
    iifname \"wg0\" ip saddr 10.66.0.0/24 icmp type echo-request accept

    # NTP for edge nodes (chrony)
    iifname \"end0\" ip saddr 192.168.10.0/24 udp dport 123 accept
    iifname \"wlan0\" ip saddr ${CENTRAL_WIFI_CIDR} udp dport 123 accept

    # Passengers collector (Edge -> Central)
    iifname \"end0\" ip saddr 192.168.10.0/24 tcp dport ${CENTRAL_PORT} accept
    iifname \"wlan0\" ip saddr ${CENTRAL_WIFI_CIDR} tcp dport ${CENTRAL_PORT} accept

    # diagnostics: allow ping from local TS subnet
    iifname \"end0\" ip saddr 192.168.10.0/24 icmp type echo-request accept
    iifname \"wlan0\" ip saddr ${CENTRAL_WIFI_CIDR} icmp type echo-request accept
    iifname \"end0\" ip6 nexthdr icmpv6 icmpv6 type echo-request accept
  }

  chain forward {
    type filter hook forward priority 0;
    policy drop;
  }

  chain output {
    type filter hook output priority 0;
    policy accept;
  }
}
EOF
sudo nft -f /etc/nftables.conf"
}

main() {
  echo "Checking SSH..."
  require_ssh "${OPI_USER}@${CENTRAL_IP}"
  for ip in "${EDGE_IPS[@]}"; do
    require_ssh "${OPI_USER}@${ip}"
  done

  echo "Deploying to central..."
  deploy_files "${OPI_USER}@${CENTRAL_IP}"
  write_env_central_skeleton "${OPI_USER}@${CENTRAL_IP}"
  set_backend_key_from_server "${OPI_USER}@${CENTRAL_IP}" || true
  install_unit_central "${OPI_USER}@${CENTRAL_IP}"
  install_unit_central_uplink "${OPI_USER}@${CENTRAL_IP}"
  install_unit_central_flush "${OPI_USER}@${CENTRAL_IP}"
  sync_central_stop_mode "${OPI_USER}@${CENTRAL_IP}"
  install_unit_central_heartbeat "${OPI_USER}@${CENTRAL_IP}"
  install_unit_queue_maintenance "${OPI_USER}@${CENTRAL_IP}"
  install_unit_service_watchdog "${OPI_USER}@${CENTRAL_IP}"
  open_central_port_firewall "${OPI_USER}@${CENTRAL_IP}"

  echo "Deploying to edges..."
  for ip in "${EDGE_IPS[@]}"; do
    deploy_files "${OPI_USER}@${ip}"
    write_env_edge "${OPI_USER}@${ip}"
    install_unit_edge "${OPI_USER}@${ip}"
    install_unit_queue_maintenance "${OPI_USER}@${ip}"
    install_unit_service_watchdog "${OPI_USER}@${ip}"
  done

  echo "Done."
  echo "Central health: curl -sS http://${CENTRAL_IP}:${CENTRAL_PORT}/health"
}

main "$@"
