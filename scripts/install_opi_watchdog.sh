#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
install_opi_watchdog.sh — enable watchdog baseline on OPi nodes

What it configures:
  1) systemd hardware watchdog (RuntimeWatchdogSec / ShutdownWatchdogSec)
  2) passengers service watchdog timer (checks/restarts critical units)

Usage:
  ./scripts/install_opi_watchdog.sh [options]

Options:
  --opi-user <user>              SSH user (default: orangepi)
  --runtime-watchdog-sec <sec>   RuntimeWatchdogSec value (default: 30s)
  --shutdown-watchdog-sec <sec>  ShutdownWatchdogSec value (default: 2min)
  --interval-sec <sec>           Service watchdog timer interval (default: 45)
  --hosts "<ip ip ip>"           Space-separated host list
  -h, --help                     Show help
EOF
}

OPI_USER="${OPI_USER:-orangepi}"
RUNTIME_WATCHDOG_SEC="${RUNTIME_WATCHDOG_SEC:-30s}"
SHUTDOWN_WATCHDOG_SEC="${SHUTDOWN_WATCHDOG_SEC:-2min}"
INTERVAL_SEC="${INTERVAL_SEC:-45}"
HOSTS="${HOSTS:-192.168.10.1 192.168.10.11 192.168.10.12}"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --opi-user) OPI_USER="${2:-}"; shift 2 ;;
    --runtime-watchdog-sec) RUNTIME_WATCHDOG_SEC="${2:-}"; shift 2 ;;
    --shutdown-watchdog-sec) SHUTDOWN_WATCHDOG_SEC="${2:-}"; shift 2 ;;
    --interval-sec) INTERVAL_SEC="${2:-}"; shift 2 ;;
    --hosts) HOSTS="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1" >&2; usage; exit 2 ;;
  esac
done

if ! [[ "${INTERVAL_SEC}" =~ ^[0-9]+$ ]] || [[ "${INTERVAL_SEC}" -lt 15 ]]; then
  echo "ERROR: --interval-sec must be integer >= 15" >&2
  exit 2
fi

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SSH_OPTS=(-o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=8)

for host in ${HOSTS}; do
  target="${OPI_USER}@${host}"
  echo "== ${target} =="
  scp "${SSH_OPTS[@]}" "${REPO_ROOT}/mvp/service_watchdog.py" "${target}:/tmp/passengers-service-watchdog.py"
  ssh "${SSH_OPTS[@]}" "${target}" "sudo bash -s" <<EOF
set -euo pipefail

sudo install -m 755 -o root -g root /tmp/passengers-service-watchdog.py /opt/passengers-mvp/service_watchdog.py
rm -f /tmp/passengers-service-watchdog.py

sudo tee /etc/systemd/system/passengers-service-watchdog.service >/dev/null <<'UNIT'
[Unit]
Description=Passengers service watchdog (ensure critical units are active)
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
User=root
Group=root
ExecStart=/usr/bin/python3 /opt/passengers-mvp/service_watchdog.py --env /etc/passengers/passengers.env
SuccessExitStatus=2
UNIT

sudo tee /etc/systemd/system/passengers-service-watchdog.timer >/dev/null <<UNIT
[Unit]
Description=Passengers service watchdog timer

[Timer]
OnBootSec=90s
OnUnitActiveSec=${INTERVAL_SEC}s
RandomizedDelaySec=5s
Persistent=true
Unit=passengers-service-watchdog.service

[Install]
WantedBy=timers.target
UNIT

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

echo "hostname=\$(hostname)"
echo "watchdog_devices:"
ls -l /dev/watchdog* 2>/dev/null || true
echo "RuntimeWatchdogSec=\$(grep -m1 '^RuntimeWatchdogSec=' /etc/systemd/system.conf | cut -d= -f2-)"
echo "ShutdownWatchdogSec=\$(grep -m1 '^ShutdownWatchdogSec=' /etc/systemd/system.conf | cut -d= -f2-)"
echo "watchdog_timer_active=\$(systemctl is-active passengers-service-watchdog.timer || true)"
echo "watchdog_timer_enabled=\$(systemctl is-enabled passengers-service-watchdog.timer || true)"
echo "watchdog_last_run:"
journalctl -u passengers-service-watchdog.service -n 2 --no-pager || true
EOF
  echo
done

echo "Done: watchdog baseline is applied to hosts: ${HOSTS}"
