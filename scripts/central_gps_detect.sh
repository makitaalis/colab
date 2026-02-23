#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
central_gps_detect.sh — detect USB GPS device on Central and print candidate /dev paths

Usage:
  ./scripts/central_gps_detect.sh [options]

Options:
  --central-ip <ip>   Central IP (default: 192.168.10.1)
  --user <name>       SSH user (default: orangepi)
  -h, --help          Show help
USAGE
}

CENTRAL_IP="192.168.10.1"
OPI_USER="orangepi"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

HOST="${OPI_USER}@${CENTRAL_IP}"
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

ssh "${HOST}" "echo '== dmesg (gps-ish) =='
dmesg -T | egrep -i 'gps|gnss|u-blox|ublox|ttyACM|ttyUSB|cdc_acm|pl2303|cp210|ftdi' | tail -n 80 || true
echo
echo '== /dev candidates =='
ls -la /dev/serial/by-id 2>/dev/null || true
ls -la /dev/ttyACM* /dev/ttyUSB* 2>/dev/null || true
"
