#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
wifi_ap_rollout.sh — setup Central as Wi‑Fi AP + configure doors as Wi‑Fi clients (static IPs)

Goal:
  - Central is AP on wlan0 (no internet via Wi‑Fi)
  - LTE remains uplink (wwan0), WireGuard stays up
  - Doors have Wi‑Fi as full replacement for Ethernet (data + SSH), while Ethernet remains preferred for data path

Default addressing:
  - Ethernet LAN: 192.168.10.0/24 (central=192.168.10.1, door-1=192.168.10.11, door-2=192.168.10.12)
  - Wi‑Fi AP subnet: 192.168.20.0/24 (central=192.168.20.1, door-1=192.168.20.11, door-2=192.168.20.12)

Usage:
  ./scripts/wifi_ap_rollout.sh --ssid <SSID>

Options:
  --ssid <name>            Wi‑Fi SSID (required)
  --central-ip <ip>        Central Ethernet IP (default: 192.168.10.1)
  --door-1-ip <ip>         Door-1 Ethernet IP (default: 192.168.10.11)
  --door-2-ip <ip>         Door-2 Ethernet IP (default: 192.168.10.12)
  --user <name>            SSH user (default: orangepi)
  --wifi-cidr <cidr>       Wi‑Fi subnet CIDR (default: 192.168.20.0/24)
  --central-wifi-ip <cidr> Central Wi‑Fi IP/CIDR (default: 192.168.20.1/24)
  --door-1-wifi-ip <cidr>  Door-1 Wi‑Fi IP/CIDR (default: 192.168.20.11/24)
  --door-2-wifi-ip <cidr>  Door-2 Wi‑Fi IP/CIDR (default: 192.168.20.12/24)
  --ap-conn <name>         NM connection name on Central (default: passengers-fallback-ap)
  --door-conn <name>       NM connection name on Doors (default: passengers-fallback-wifi)
  --cooldown-sec <n>       CENTRAL_URL_COOLDOWN_SEC on doors (default: 5)
  --no-apply-nft           Do not touch nftables on Central
  --no-apply-chrony        Do not touch chrony config
  -h, --help               Show help

Security:
  - The script prompts for WPA2 passphrase (not echoed).
  - Passphrase is applied on devices via NetworkManager (stored on the nodes), not written to this repo.
USAGE
}

SSID=""
CENTRAL_IP="192.168.10.1"
DOOR1_IP="192.168.10.11"
DOOR2_IP="192.168.10.12"
OPI_USER="orangepi"
WIFI_CIDR="192.168.20.0/24"
CENTRAL_WIFI_IP_CIDR="192.168.20.1/24"
DOOR1_WIFI_IP_CIDR="192.168.20.11/24"
DOOR2_WIFI_IP_CIDR="192.168.20.12/24"
AP_CONN="passengers-fallback-ap"
DOOR_CONN="passengers-fallback-wifi"
COOLDOWN_SEC="5"
APPLY_NFT="1"
APPLY_CHRONY="1"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --ssid) SSID="${2:-}"; shift 2 ;;
    --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
    --door-1-ip) DOOR1_IP="${2:-}"; shift 2 ;;
    --door-2-ip) DOOR2_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --wifi-cidr) WIFI_CIDR="${2:-}"; shift 2 ;;
    --central-wifi-ip) CENTRAL_WIFI_IP_CIDR="${2:-}"; shift 2 ;;
    --door-1-wifi-ip) DOOR1_WIFI_IP_CIDR="${2:-}"; shift 2 ;;
    --door-2-wifi-ip) DOOR2_WIFI_IP_CIDR="${2:-}"; shift 2 ;;
    --ap-conn) AP_CONN="${2:-}"; shift 2 ;;
    --door-conn) DOOR_CONN="${2:-}"; shift 2 ;;
    --cooldown-sec) COOLDOWN_SEC="${2:-}"; shift 2 ;;
    --no-apply-nft) APPLY_NFT="0"; shift ;;
    --no-apply-chrony) APPLY_CHRONY="0"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if [[ -z "${SSID}" ]]; then
  echo "ERROR: --ssid is required" >&2
  usage
  exit 2
fi

if ! [[ "${COOLDOWN_SEC}" =~ ^[0-9]+$ ]] || [[ "${COOLDOWN_SEC}" -lt 1 ]]; then
  echo "ERROR: --cooldown-sec must be integer >= 1 (got: ${COOLDOWN_SEC})" >&2
  exit 2
fi

read -r -s -p "Enter WPA2 passphrase for SSID '${SSID}': " WIFI_PSK
echo
if [[ ${#WIFI_PSK} -lt 8 ]]; then
  echo "ERROR: WPA2 passphrase must be at least 8 chars" >&2
  exit 2
fi

CENTRAL_WIFI_IP="${CENTRAL_WIFI_IP_CIDR%/*}"
SSID_B64="$(printf %s "${SSID}" | base64 -w0)"
WIFI_PSK_B64="$(printf %s "${WIFI_PSK}" | base64 -w0)"

ssh_ok() {
  ssh -o BatchMode=yes -o StrictHostKeyChecking=accept-new -o ConnectTimeout=5 "$1" "true" >/dev/null
}

ssh_ok "${OPI_USER}@${CENTRAL_IP}"
ssh_ok "${OPI_USER}@${DOOR1_IP}"
ssh_ok "${OPI_USER}@${DOOR2_IP}"

echo "== Central: configure AP (${AP_CONN}) =="
ssh "${OPI_USER}@${CENTRAL_IP}" "sudo bash -lc '
set -euo pipefail

ssid=\"\$(printf %s \"${SSID_B64}\" | base64 -d)\"
psk=\"\$(printf %s \"${WIFI_PSK_B64}\" | base64 -d)\"

nmcli -t -f DEVICE,TYPE,STATE dev status | grep -q \"^wlan0:wifi:\" || true

if ! nmcli -t -f NAME con show | grep -Fxq \"${AP_CONN}\"; then
  nmcli con add type wifi ifname wlan0 con-name \"${AP_CONN}\" ssid \"\${ssid}\" \
    802-11-wireless.mode ap \
    802-11-wireless.band bg \
    ipv4.method manual ipv4.addresses ${CENTRAL_WIFI_IP_CIDR} ipv4.never-default yes \
    ipv6.method ignore >/dev/null
fi

nmcli con mod \"${AP_CONN}\" 802-11-wireless.mode ap
nmcli con mod \"${AP_CONN}\" 802-11-wireless.band bg
nmcli con mod \"${AP_CONN}\" 802-11-wireless.powersave 2
nmcli con mod \"${AP_CONN}\" connection.autoconnect yes connection.autoconnect-retries 0
nmcli con mod \"${AP_CONN}\" ipv4.method manual ipv4.addresses ${CENTRAL_WIFI_IP_CIDR} ipv4.never-default yes
nmcli con mod \"${AP_CONN}\" ipv6.method ignore
nmcli con mod \"${AP_CONN}\" wifi-sec.key-mgmt wpa-psk
nmcli con mod \"${AP_CONN}\" wifi-sec.psk \"\${psk}\"

# Bring down any other active Wi‑Fi connection on wlan0 (STA), then bring up AP.
active_wifi_name=\"\$(nmcli -t -f NAME,TYPE,DEVICE con show --active | awk -F: '\''\$2==\"802-11-wireless\" && \$3==\"wlan0\" {print \$1}'\'' | head -n1)\"
if [[ -n \"\${active_wifi_name}\" && \"\${active_wifi_name}\" != \"${AP_CONN}\" ]]; then
  nmcli con down \"\${active_wifi_name}\" || true
fi

nmcli con up \"${AP_CONN}\"
ip -br addr show dev wlan0
'"

echo "== Doors: connect to AP + set static IPs =="
configure_door_wifi() {
  local host_ip="$1"
  local wifi_ip_cidr="$2"
  ssh "${OPI_USER}@${host_ip}" "sudo bash -lc '
set -euo pipefail
ssid=\"\$(printf %s \"${SSID_B64}\" | base64 -d)\"
psk=\"\$(printf %s \"${WIFI_PSK_B64}\" | base64 -d)\"
rfkill unblock wifi || true
nmcli radio wifi on || true

if ! nmcli -t -f NAME con show | grep -Fxq \"${DOOR_CONN}\"; then
  nmcli con add type wifi ifname wlan0 con-name \"${DOOR_CONN}\" ssid \"\${ssid}\" >/dev/null
fi

nmcli con mod \"${DOOR_CONN}\" wifi-sec.key-mgmt wpa-psk
nmcli con mod \"${DOOR_CONN}\" wifi-sec.psk \"\${psk}\"
nmcli con mod \"${DOOR_CONN}\" 802-11-wireless.powersave 2
nmcli con mod \"${DOOR_CONN}\" connection.autoconnect yes connection.autoconnect-retries 0
nmcli con mod \"${DOOR_CONN}\" ipv4.method manual ipv4.addresses ${wifi_ip_cidr} ipv4.never-default yes ipv6.method ignore
nmcli con up \"${DOOR_CONN}\"

ip -br addr show dev wlan0
ping -c 1 -W 1 ${CENTRAL_WIFI_IP} >/dev/null || true
'"
}

configure_door_wifi "${DOOR1_IP}" "${DOOR1_WIFI_IP_CIDR}"
configure_door_wifi "${DOOR2_IP}" "${DOOR2_WIFI_IP_CIDR}"

echo "== Central: apply nftables rules for Wi‑Fi subnet (SSH/NTP/collector) =="
if [[ "${APPLY_NFT}" == "1" ]]; then
  ssh "${OPI_USER}@${CENTRAL_IP}" "sudo bash -lc '
set -euo pipefail
cp -a /etc/nftables.conf \"/etc/nftables.conf.bak.wifi.\$(date -u +%Y%m%dT%H%M%SZ)\"
cat >/etc/nftables.conf <<EOF
#!/usr/sbin/nft -f

flush ruleset

table inet filter {
  chain input {
    type filter hook input priority 0;
    policy drop;

    iif lo accept
    ct state established,related accept

    iifname \"end0\" tcp dport 22 accept
    iifname \"wlan0\" ip saddr ${WIFI_CIDR} tcp dport 22 accept

    # management via WireGuard (VPS -> Central)
    iifname \"wg0\" ip saddr 10.66.0.0/24 tcp dport 22 accept
    iifname \"wg0\" ip saddr 10.66.0.0/24 icmp type echo-request accept

    # NTP for edge nodes (chrony)
    iifname \"end0\" ip saddr 192.168.10.0/24 udp dport 123 accept
    iifname \"wlan0\" ip saddr ${WIFI_CIDR} udp dport 123 accept

    # Passengers collector (Edge -> Central)
    iifname \"end0\" ip saddr 192.168.10.0/24 tcp dport 8080 accept
    iifname \"wlan0\" ip saddr ${WIFI_CIDR} tcp dport 8080 accept

    # diagnostics: allow ping from local TS subnets
    iifname \"end0\" ip saddr 192.168.10.0/24 icmp type echo-request accept
    iifname \"wlan0\" ip saddr ${WIFI_CIDR} icmp type echo-request accept
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
nft -c -f /etc/nftables.conf
systemctl enable --now nftables
nft -f /etc/nftables.conf
'"
fi

echo "== Time: chrony (Central + doors) include Wi‑Fi subnet =="
if [[ "${APPLY_CHRONY}" == "1" ]]; then
  ssh "${OPI_USER}@${CENTRAL_IP}" "sudo bash -lc '
set -euo pipefail
cp -a /etc/chrony/chrony.conf \"/etc/chrony/chrony.conf.bak.wifi.\$(date -u +%Y%m%dT%H%M%SZ)\"

conf=\"\$(cat /etc/chrony/chrony.conf)\"
conf=\"\${conf/allow 192.168.10.0\\/24/allow 192.168.10.0\\/24\\nallow 192.168.20.0\\/24}\"

if ! grep -q \"^bindaddress 192.168.10.1$\" /etc/chrony/chrony.conf; then
  conf+=\"\\n\\n# bind only on internal interfaces\\nbindaddress 127.0.0.1\\nbindaddress 192.168.10.1\\nbindaddress 192.168.20.1\\n\"
fi

printf \"%s\\n\" \"\${conf}\" >/etc/chrony/chrony.conf
systemctl restart chrony
chronyc -n sources | sed -n \"1,20p\" || true
'"

  update_edge_chrony() {
    local host_ip="$1"
    ssh "${OPI_USER}@${host_ip}" "sudo bash -lc '
set -euo pipefail
cp -a /etc/chrony/chrony.conf \"/etc/chrony/chrony.conf.bak.wifi.\$(date -u +%Y%m%dT%H%M%SZ)\"

grep -q \"^server 192.168.20.1\" /etc/chrony/chrony.conf || \
  sed -i \"s/^server 192\\.168\\.10\\.1\\(.*\\)$/server 192.168.10.1\\1\\nserver 192.168.20.1 iburst/\" /etc/chrony/chrony.conf

systemctl restart chrony
chronyc -n sources | sed -n \"1,20p\" || true
'"
  }
  update_edge_chrony "${DOOR1_IP}"
  update_edge_chrony "${DOOR2_IP}"
fi

echo "== Edge env: prefer Ethernet URL, fallback to Wi‑Fi URL =="
set_edge_env() {
  local host_ip="$1"
  ssh "${OPI_USER}@${host_ip}" "sudo bash -lc '
set -euo pipefail
test -f /etc/passengers/passengers.env || exit 0
if grep -q \"^CENTRAL_URL=\" /etc/passengers/passengers.env; then
  sed -i \"s|^CENTRAL_URL=.*|CENTRAL_URL=http://192.168.10.1:8080/api/v1/edge/events,http://192.168.20.1:8080/api/v1/edge/events|\" /etc/passengers/passengers.env
else
  echo \"CENTRAL_URL=http://192.168.10.1:8080/api/v1/edge/events,http://192.168.20.1:8080/api/v1/edge/events\" >> /etc/passengers/passengers.env
fi
if grep -q \"^CENTRAL_URL_COOLDOWN_SEC=\" /etc/passengers/passengers.env; then
  sed -i \"s|^CENTRAL_URL_COOLDOWN_SEC=.*|CENTRAL_URL_COOLDOWN_SEC=${COOLDOWN_SEC}|\" /etc/passengers/passengers.env
else
  echo \"CENTRAL_URL_COOLDOWN_SEC=${COOLDOWN_SEC}\" >> /etc/passengers/passengers.env
fi
chown root:orangepi /etc/passengers/passengers.env
chmod 640 /etc/passengers/passengers.env
systemctl restart passengers-edge-sender.service 2>/dev/null || true
'"
}

set_edge_env "${DOOR1_IP}"
set_edge_env "${DOOR2_IP}"

echo "== Verify: health over Wi‑Fi (from doors) =="
ssh "${OPI_USER}@${DOOR1_IP}" "curl -sS --max-time 3 http://192.168.20.1:8080/health || true"
ssh "${OPI_USER}@${DOOR2_IP}" "curl -sS --max-time 3 http://192.168.20.1:8080/health || true"

echo "Done. Next: unplug Ethernet on a door and watch passengers-edge-sender + central collector logs."
