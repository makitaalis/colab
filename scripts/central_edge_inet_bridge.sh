#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
central_edge_inet_bridge.sh — temporary internet bridge for edge nodes via Central (for provisioning)

Why:
  Edge nodes normally have NO internet. For apt/pip installs you can temporarily NAT via Central Wi‑Fi/LTE.

What it does on Central:
  - enables IPv4 forwarding
  - allows forwarding LAN->uplink in nft (inet filter forward)
  - adds MASQUERADE + forward rules via iptables-nft

Usage:
  ./scripts/central_edge_inet_bridge.sh <enable|disable> [options]

Options:
  --central-ip <ip>    Central IP (default: 192.168.10.1)
  --user <name>        SSH user (default: orangepi)
  --lan-if <if>        Central LAN interface (default: end0)
  --uplink-if <if>     Central uplink interface (default: wlan0)
  --edge-cidr <cidr>   Edge LAN CIDR (default: 192.168.10.0/24)
  -h, --help           Show help

On the edge node (example):
  sudo ip route replace default via 192.168.10.1 dev end0 metric 900
USAGE
}

ACTION="${1:-}"
shift || true

CENTRAL_IP="192.168.10.1"
OPI_USER="orangepi"
LAN_IF="end0"
UPLINK_IF="wlan0"
EDGE_CIDR="192.168.10.0/24"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --lan-if) LAN_IF="${2:-}"; shift 2 ;;
    --uplink-if) UPLINK_IF="${2:-}"; shift 2 ;;
    --edge-cidr) EDGE_CIDR="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ "${ACTION}" != "enable" && "${ACTION}" != "disable" ]]; then
  echo "ERROR: action must be enable|disable" >&2
  usage
  exit 2
fi

HOST="${OPI_USER}@${CENTRAL_IP}"
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

if [[ "${ACTION}" == "enable" ]]; then
  ssh "${HOST}" "sudo sh -lc '
set -e
echo 1 > /proc/sys/net/ipv4/ip_forward

# nft forward allow (Central has default drop policy in inet/filter/forward)
if ! nft list chain inet filter forward >/dev/null 2>&1; then
  nft add table inet filter
  nft add chain inet filter forward { type filter hook forward priority 0\\; policy drop\\; }
fi
if ! nft list chain inet filter forward | grep -q \"iifname \\\"${LAN_IF}\\\" oifname \\\"${UPLINK_IF}\\\"\"; then
  nft insert rule inet filter forward iifname \"${UPLINK_IF}\" oifname \"${LAN_IF}\" ip daddr ${EDGE_CIDR} ct state established,related accept
  nft insert rule inet filter forward iifname \"${LAN_IF}\" oifname \"${UPLINK_IF}\" ip saddr ${EDGE_CIDR} accept
fi

# iptables-nft NAT + forward (ok to be redundant with nft)
iptables -t nat -C POSTROUTING -o ${UPLINK_IF} -s ${EDGE_CIDR} -j MASQUERADE 2>/dev/null || iptables -t nat -A POSTROUTING -o ${UPLINK_IF} -s ${EDGE_CIDR} -j MASQUERADE
iptables -C FORWARD -i ${LAN_IF} -o ${UPLINK_IF} -s ${EDGE_CIDR} -j ACCEPT 2>/dev/null || iptables -A FORWARD -i ${LAN_IF} -o ${UPLINK_IF} -s ${EDGE_CIDR} -j ACCEPT
iptables -C FORWARD -i ${UPLINK_IF} -o ${LAN_IF} -d ${EDGE_CIDR} -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || iptables -A FORWARD -i ${UPLINK_IF} -o ${LAN_IF} -d ${EDGE_CIDR} -m state --state RELATED,ESTABLISHED -j ACCEPT

echo enabled
nft list chain inet filter forward
'"
  echo "NEXT (edge node): sudo ip route replace default via ${CENTRAL_IP} dev end0 metric 900"
else
  ssh "${HOST}" "sudo sh -lc '
set -e

# remove nft rules we added (match by text)
if nft list chain inet filter forward >/dev/null 2>&1; then
  nft -a list chain inet filter forward | awk \"/${LAN_IF}.*${UPLINK_IF}.*${EDGE_CIDR}/ {print \\$NF}\" | while read -r h; do nft delete rule inet filter forward handle \\\"\\$h\\\"; done || true
  nft -a list chain inet filter forward | awk \"/${UPLINK_IF}.*${LAN_IF}.*${EDGE_CIDR}/ {print \\$NF}\" | while read -r h; do nft delete rule inet filter forward handle \\\"\\$h\\\"; done || true
fi

iptables -t nat -D POSTROUTING -o ${UPLINK_IF} -s ${EDGE_CIDR} -j MASQUERADE 2>/dev/null || true
iptables -D FORWARD -i ${LAN_IF} -o ${UPLINK_IF} -s ${EDGE_CIDR} -j ACCEPT 2>/dev/null || true
iptables -D FORWARD -i ${UPLINK_IF} -o ${LAN_IF} -d ${EDGE_CIDR} -m state --state RELATED,ESTABLISHED -j ACCEPT 2>/dev/null || true

echo 0 > /proc/sys/net/ipv4/ip_forward || true
echo disabled
nft list chain inet filter forward 2>/dev/null || true
'"
  echo "Bridge disabled on Central."
fi

