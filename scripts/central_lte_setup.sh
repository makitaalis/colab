#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
central_lte_setup.sh — bootstrap LTE stack on Central (EM7455/QMI via ModemManager + NetworkManager)

This script:
  1) installs ModemManager + tools (mmcli, libqmi-utils, libmbim-utils)
  2) starts/enables ModemManager
  3) (optional) unlocks SIM with PIN
  4) (optional) creates/updates a NetworkManager GSM connection with APN and brings it up

Usage:
  ./scripts/central_lte_setup.sh [options]

Options:
  --central-ip <ip>      Central IP (default: 192.168.10.1)
  --user <name>          SSH user (default: orangepi)
  --apn <apn>            APN for the SIM (optional; required to connect)
  --pin <pin>            SIM PIN (optional; do NOT store in repo)
  --con-name <name>      NM connection name (default: lte)
  --metric <n>           Route metric for LTE (default: 900; keeps Wi‑Fi preferred)
  -h, --help             Show help

Examples:
  ./scripts/central_lte_setup.sh --pin 0422 --apn internet
  ./scripts/central_lte_setup.sh --apn your.apn.here
USAGE
}

CENTRAL_IP="192.168.10.1"
OPI_USER="orangepi"
APN=""
SIM_PIN=""
CON_NAME="lte"
METRIC="900"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --apn) APN="${2:-}"; shift 2 ;;
    --pin) SIM_PIN="${2:-}"; shift 2 ;;
    --con-name) CON_NAME="${2:-}"; shift 2 ;;
    --metric) METRIC="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

HOST="${OPI_USER}@${CENTRAL_IP}"
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

wait_for_modem() {
  ssh "${HOST}" "for i in 1 2 3 4 5 6 7 8 9 10 11 12 13 14 15; do mmcli -L 2>/dev/null | grep -q '/org/freedesktop/ModemManager1/Modem/' && exit 0; sleep 1; done; exit 1" >/dev/null 2>&1
}

echo "== Install LTE packages on ${HOST} =="
ssh "${HOST}" "export DEBIAN_FRONTEND=noninteractive
sudo -E apt-get update -y >/dev/null
sudo -E apt-get install -y --no-install-recommends modemmanager libqmi-utils libmbim-utils >/dev/null
sudo systemctl enable --now ModemManager.service >/dev/null
sudo systemctl --no-pager --full status ModemManager.service | sed -n '1,8p'
mmcli -L || true
if lsusb | grep -qi '1199:9071'; then
  echo 'usb: sierra 1199:9071 present'
fi
if [ -e /dev/cdc-wdm0 ]; then
  sudo qmicli -d /dev/cdc-wdm0 --device-open-proxy --uim-get-card-status 2>/dev/null | sed -n '1,120p' || true
fi"

if ssh "${HOST}" "mmcli -L 2>/dev/null | grep -q '/org/freedesktop/ModemManager1/Modem/'"; then
  :
else
  echo "WARN: mmcli -L empty. Applying udev hint for qmi_wwan net port (Sierra 1199:9071) and retrying..."
  ssh "${HOST}" "cat <<'RULE' | sudo tee /etc/udev/rules.d/77-mm-sierra-qmi-net.rules >/dev/null
# Ensure ModemManager sees QMI net port for Sierra EM/MC74xx on qmi_wwan
ACTION!=\"add|change|move|bind\", GOTO=\"mm_sierra_qmi_net_end\"
SUBSYSTEM==\"net\", ENV{ID_NET_DRIVER}==\"qmi_wwan\", ATTRS{idVendor}==\"1199\", ATTRS{idProduct}==\"9071\", ENV{ID_MM_CANDIDATE}=\"1\", ENV{ID_MM_PORT_TYPE_QMI}=\"1\"
LABEL=\"mm_sierra_qmi_net_end\"
RULE
sudo udevadm control --reload-rules
sudo udevadm trigger --subsystem-match=net
sudo systemctl restart ModemManager.service
sleep 2
mmcli -L || true"
fi

if ! wait_for_modem; then
  echo "WARN: modem not detected yet (mmcli -L empty). Check USB wiring and dmesg on central."
  exit 0
fi

MODEM_ID="$(ssh "${HOST}" "mmcli -L 2>/dev/null | sed -n 's|.*/Modem/\\([0-9][0-9]*\\).*|\\1|p' | head -n 1" | tr -d '\r' || true)"
if [[ -z "${MODEM_ID}" ]]; then
  echo "WARN: modem not detected yet (mmcli -L empty). Check USB wiring and dmesg on central."
  exit 0
fi

echo "== Detected modem id: ${MODEM_ID} =="
ssh "${HOST}" "mmcli -m ${MODEM_ID} | sed -n '1,80p' || true"

echo "== Prefer 4G when available (allowed: 3g|4g, preferred: 4g) =="
ssh "${HOST}" "sudo mmcli -m ${MODEM_ID} --set-allowed-modes='3g|4g' --set-preferred-mode='4g' >/dev/null 2>&1 || true"

if [[ -n "${SIM_PIN}" ]]; then
  echo "== Unlock SIM with PIN (not stored) =="
  ssh "${HOST}" "sudo mmcli -m ${MODEM_ID} --pin='${SIM_PIN}' >/dev/null || true"
fi

if [[ -z "${APN}" ]]; then
  echo "NEXT: provide --apn to bring LTE up (APN is carrier-specific)."
  exit 0
fi

echo "== Create/Update NM connection '${CON_NAME}' (APN=${APN}) =="
ssh "${HOST}" "set -e
if sudo nmcli -t -f NAME connection show | grep -Fxq '${CON_NAME}'; then
  sudo nmcli connection modify '${CON_NAME}' gsm.apn '${APN}' connection.autoconnect yes ipv4.route-metric '${METRIC}'
else
  sudo nmcli connection add type gsm ifname '*' con-name '${CON_NAME}' gsm.apn '${APN}' connection.autoconnect yes ipv4.route-metric '${METRIC}'
fi
sudo nmcli connection up '${CON_NAME}' || true
sudo nmcli -f DEVICE,TYPE,STATE,CONNECTION dev status | sed -n '1,12p'
ip r | sed -n '1,20p'"

echo "LTE bootstrap done."
