#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
install_central_gps_services.sh — install GPS/GNSS snapshot services on Central (ModemManager-based)

What it installs on Central:
  - /usr/local/sbin/passengers-gps-enable        (enable GNSS sources via mmcli)
  - /usr/local/sbin/passengers-gps-snapshot      (write /var/lib/passengers/gps/latest.json)
  - systemd:
      passengers-gps-enable.service              (oneshot on boot)
      passengers-gps-snapshot.service            (oneshot, invoked by timer)
      passengers-gps-snapshot.timer              (periodic snapshots)

Usage:
  ./scripts/install_central_gps_services.sh [options]

Options:
  --central-ip <ip>     Central IP (default: 192.168.10.1)
  --user <name>         SSH user (default: orangepi)
  --modem-id <id|auto>  ModemManager modem id (default: auto)
  --interval <sec>      Snapshot interval seconds (default: 10)
  -h, --help            Show help

Notes:
  - Does NOT store APN/PIN in this repo.
  - Requires ModemManager + mmcli already installed on Central (see ./scripts/central_lte_setup.sh).
USAGE
}

CENTRAL_IP="192.168.10.1"
OPI_USER="orangepi"
MODEM_ID="auto"
INTERVAL_SEC="10"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --central-ip) CENTRAL_IP="${2:-}"; shift 2 ;;
    --user) OPI_USER="${2:-}"; shift 2 ;;
    --modem-id) MODEM_ID="${2:-}"; shift 2 ;;
    --interval) INTERVAL_SEC="${2:-}"; shift 2 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 2 ;;
  esac
done

if ! [[ "${INTERVAL_SEC}" =~ ^[0-9]+$ ]] || [[ "${INTERVAL_SEC}" -lt 2 ]]; then
  echo "Bad --interval: ${INTERVAL_SEC} (need integer >= 2)" >&2
  exit 2
fi

HOST="${OPI_USER}@${CENTRAL_IP}"
ssh -o BatchMode=yes -o ConnectTimeout=8 -o StrictHostKeyChecking=accept-new "${HOST}" "true"

echo "== Install GPS services on ${HOST} =="

ssh "${HOST}" "set -e
sudo install -d -m 0755 /usr/local/sbin /etc/systemd/system /var/lib/passengers/gps

cat <<'EOF' | sudo tee /usr/local/sbin/passengers-gps-enable >/dev/null
#!/usr/bin/env bash
set -euo pipefail

MODEM_ID=\"\${1:-auto}\"

pick_modem() {
  mmcli -L 2>/dev/null | sed -n 's|.*/Modem/\\([0-9][0-9]*\\).*|\\1|p' | head -n1
}

if [[ \"\$MODEM_ID\" == \"auto\" || -z \"\$MODEM_ID\" ]]; then
  MODEM_ID=\"\$(pick_modem || true)\"
fi

if [[ -z \"\$MODEM_ID\" ]]; then
  echo \"no_modem\"
  exit 0
fi

# Enable sources (ignore unsupported ones).
mmcli -m \"\$MODEM_ID\" --location-enable-3gpp >/dev/null 2>&1 || true
mmcli -m \"\$MODEM_ID\" --location-enable-gps-nmea >/dev/null 2>&1 || true
mmcli -m \"\$MODEM_ID\" --location-enable-gps-raw >/dev/null 2>&1 || true
mmcli -m \"\$MODEM_ID\" --location-enable-agps-msb >/dev/null 2>&1 || true
mmcli -m \"\$MODEM_ID\" --location-enable-agps-msa >/dev/null 2>&1 || true

# Prefer faster refresh while in MVP/debug. (0 disables explicit rate.)
mmcli -m \"\$MODEM_ID\" --location-set-gps-refresh-rate=5 >/dev/null 2>&1 || true

echo \"ok modem=\$MODEM_ID\"
EOF

sudo chmod 0755 /usr/local/sbin/passengers-gps-enable

cat <<'EOF' | sudo tee /usr/local/sbin/passengers-gps-snapshot >/dev/null
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import subprocess
import tempfile
from typing import Any


def utc_now_iso() -> str:
    return dt.datetime.utcnow().replace(microsecond=0).isoformat() + \"Z\"


def sh(args: list[str]) -> str:
    return subprocess.check_output(args, text=True, stderr=subprocess.DEVNULL)


def pick_modem_id() -> str | None:
    try:
        out = sh([\"mmcli\", \"-L\"])
    except Exception:
        return None
    m = re.search(r\"/Modem/(\\d+)\", out)
    return m.group(1) if m else None


def parse_float(value: Any) -> float | None:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s or s == \"--\":
        return None
    try:
        return float(s)
    except Exception:
        return None


def atomic_write_json(path: str, obj: Any) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(prefix=\".tmp.\", dir=os.path.dirname(path))
    try:
        with os.fdopen(fd, \"w\", encoding=\"utf-8\") as f:
            json.dump(obj, f, ensure_ascii=False, separators=(\",\", \":\"))
            f.write(\"\\n\")
        try:
            os.chmod(tmp, 0o644)
        except Exception:
            pass
        os.replace(tmp, path)
    finally:
        try:
            if os.path.exists(tmp):
                os.unlink(tmp)
        except Exception:
            pass


def main() -> int:
    ap = argparse.ArgumentParser(description=\"Snapshot GNSS location via ModemManager mmcli and write JSON state.\")
    ap.add_argument(\"--modem-id\", default=\"auto\", help=\"Modem id, or 'auto' (default).\" )
    ap.add_argument(\"--out\", default=\"/var/lib/passengers/gps/latest.json\")
    args = ap.parse_args()

    modem_id = args.modem_id
    if modem_id == \"auto\":
        modem_id = pick_modem_id() or \"\"

    state: dict[str, Any] = {
        \"updated_at\": utc_now_iso(),
        \"source\": \"mmcli\",
        \"modem_id\": modem_id or None,
        \"fix\": False,
        \"lat\": None,
        \"lon\": None,
        \"alt_m\": None,
        \"utc\": None,
        \"nmea\": [],
        \"cell\": None,
        \"error\": None,
    }

    if not modem_id:
        state[\"error\"] = \"no_modem\"
        atomic_write_json(args.out, state)
        return 0

    try:
        raw = sh([\"mmcli\", \"-m\", str(modem_id), \"--location-get\", \"-J\"])
        data = json.loads(raw)
    except Exception as e:
        state[\"error\"] = f\"mmcli_location_get_failed:{type(e).__name__}\"
        atomic_write_json(args.out, state)
        return 0

    loc = (((data or {}).get(\"modem\") or {}).get(\"location\") or {})
    gps = (loc.get(\"gps\") or {})
    g3pp = (loc.get(\"3gpp\") or {})

    state[\"lat\"] = parse_float(gps.get(\"latitude\"))
    state[\"lon\"] = parse_float(gps.get(\"longitude\"))
    state[\"alt_m\"] = parse_float(gps.get(\"altitude\"))
    state[\"utc\"] = gps.get(\"utc\") if gps.get(\"utc\") not in (None, \"--\") else None

    nmea = gps.get(\"nmea\")
    if isinstance(nmea, list):
        state[\"nmea\"] = [str(x) for x in nmea[:32]]

    if any(g3pp.get(k) for k in (\"mcc\", \"mnc\", \"lac\", \"tac\", \"cid\")):
        state[\"cell\"] = {
            \"mcc\": g3pp.get(\"mcc\"),
            \"mnc\": g3pp.get(\"mnc\"),
            \"lac\": g3pp.get(\"lac\"),
            \"tac\": g3pp.get(\"tac\"),
            \"cid\": g3pp.get(\"cid\"),
        }

    state[\"fix\"] = bool(state[\"lat\"] is not None and state[\"lon\"] is not None)
    atomic_write_json(args.out, state)
    return 0


if __name__ == \"__main__\":
    raise SystemExit(main())
EOF

sudo chmod 0755 /usr/local/sbin/passengers-gps-snapshot

cat <<EOF | sudo tee /etc/systemd/system/passengers-gps-enable.service >/dev/null
[Unit]
Description=Passengers GPS enable (ModemManager GNSS sources)
After=ModemManager.service NetworkManager.service
Wants=ModemManager.service NetworkManager.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/passengers-gps-enable ${MODEM_ID}
TimeoutStartSec=30

[Install]
WantedBy=multi-user.target
EOF

cat <<'EOF' | sudo tee /etc/systemd/system/passengers-gps-snapshot.service >/dev/null
[Unit]
Description=Passengers GPS snapshot (write latest.json)
After=passengers-gps-enable.service
Wants=passengers-gps-enable.service

[Service]
Type=oneshot
ExecStart=/usr/local/sbin/passengers-gps-snapshot
TimeoutStartSec=20
EOF

cat <<EOF | sudo tee /etc/systemd/system/passengers-gps-snapshot.timer >/dev/null
[Unit]
Description=Passengers GPS snapshot timer

[Timer]
OnBootSec=15s
OnUnitActiveSec=${INTERVAL_SEC}s
AccuracySec=1s
Unit=passengers-gps-snapshot.service

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable --now passengers-gps-enable.service >/dev/null
sudo systemctl enable --now passengers-gps-snapshot.timer >/dev/null

sudo systemctl --no-pager --full status passengers-gps-enable.service | sed -n '1,40p'
sudo systemctl --no-pager --full status passengers-gps-snapshot.timer | sed -n '1,40p'
sudo /usr/local/sbin/passengers-gps-snapshot >/dev/null 2>&1 || true
sudo cat /var/lib/passengers/gps/latest.json 2>/dev/null | head -c 600; echo
"

echo "OK: GPS services installed."
