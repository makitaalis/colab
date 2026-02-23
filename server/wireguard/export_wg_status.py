#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def run(cmd: list[str]) -> str:
    proc = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if proc.returncode != 0:
        raise RuntimeError(f"cmd failed: {cmd!r} rc={proc.returncode} stderr={proc.stderr.strip()}")
    return proc.stdout


@dataclass(frozen=True)
class PeerNameMap:
    by_public_key: dict[str, str]


def parse_wg0_conf_names(conf_text: str) -> PeerNameMap:
    by_pub: dict[str, str] = {}
    current_name: str | None = None
    in_peer = False
    peer_pub: str | None = None

    for raw_line in conf_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            m = re.match(r"#\s*(?:name|peer|peer_name)\s*:\s*(.+)$", line, flags=re.IGNORECASE)
            if m:
                current_name = m.group(1).strip()
            continue
        if line.lower() == "[peer]":
            in_peer = True
            peer_pub = None
            continue
        if line.lower() == "[interface]":
            in_peer = False
            peer_pub = None
            continue
        if in_peer:
            m = re.match(r"publickey\s*=\s*(.+)$", line, flags=re.IGNORECASE)
            if m:
                peer_pub = m.group(1).strip()
                if current_name:
                    by_pub[peer_pub] = current_name
                continue

    return PeerNameMap(by_public_key=by_pub)


def redact_wg0_conf(conf_text: str) -> str:
    out_lines: list[str] = []
    for raw_line in conf_text.splitlines():
        if re.match(r"^\s*PrivateKey\s*=", raw_line, flags=re.IGNORECASE):
            out_lines.append("PrivateKey = __REDACTED__")
        else:
            out_lines.append(raw_line)
    return "\n".join(out_lines).rstrip() + "\n"


def parse_wg_dump(dump_text: str, names: PeerNameMap) -> dict:
    lines = [ln.strip() for ln in dump_text.splitlines() if ln.strip()]
    if not lines:
        return {"ts": utc_now_iso(), "status": "no_data"}

    # wireguard-tools has two common dump formats:
    # A) iface-name present:
    #    wg0 <privkey> <pubkey> <listen_port> <fwmark>
    #    wg0 <peer_pub> <preshared_key> <endpoint> <allowed_ips> <latest_handshake> <rx> <tx> <keepalive>
    # B) iface-name omitted:
    #    <privkey> <pubkey> <listen_port> <fwmark>
    #    <peer_pub> <preshared_key> <endpoint> <allowed_ips> <latest_handshake> <rx> <tx> <keepalive>
    first = lines[0].split("\t")
    if len(first) >= 5 and first[0] == "wg0":
        iface_name, _priv, iface_pub, listen_port, _fwmark = first[:5]
    elif len(first) >= 4:
        iface_name = "wg0"
        _priv, iface_pub, listen_port, _fwmark = first[:4]
    else:
        raise RuntimeError("unexpected wg dump format")

    peers = []
    now = int(time.time())
    for ln in lines[1:]:
        # A) wg0 <peer_pub> <preshared> <endpoint> <allowed_ips> <latest_handshake> <rx> <tx> <keepalive>
        # B) <peer_pub> <preshared> <endpoint> <allowed_ips> <latest_handshake> <rx> <tx> <keepalive>
        parts = ln.split("\t")
        if len(parts) >= 9 and parts[0] == "wg0":
            _iface, peer_pub, _psk, endpoint, allowed_ips_raw, hs_raw, rx_raw, tx_raw, ka_raw = parts[:9]
        elif len(parts) >= 8:
            peer_pub, _psk, endpoint, allowed_ips_raw, hs_raw, rx_raw, tx_raw, ka_raw = parts[:8]
        else:
            continue
        allowed_ips = [a.strip() for a in allowed_ips_raw.split(",") if a.strip()]
        hs = int(hs_raw)
        latest_ts = None
        age = None
        if hs > 0:
            latest_ts = datetime.fromtimestamp(hs, tz=timezone.utc).isoformat().replace("+00:00", "Z")
            age = max(0, now - hs)

        keepalive = 0 if ka_raw == "off" else int(ka_raw)
        peer_name = names.by_public_key.get(peer_pub)
        peer_block = "[Peer]\n"
        if peer_name:
            peer_block += f"# name: {peer_name}\n"
        peer_block += f"PublicKey = {peer_pub}\n"
        peer_block += f"AllowedIPs = {', '.join(allowed_ips)}\n"

        peers.append(
            {
                "name": peer_name,
                "public_key": peer_pub,
                "endpoint": endpoint if endpoint != "(none)" else None,
                "allowed_ips": allowed_ips,
                "latest_handshake_ts": latest_ts,
                "latest_handshake_age_sec": age,
                "rx_bytes": int(rx_raw),
                "tx_bytes": int(tx_raw),
                "persistent_keepalive": keepalive,
                "server_peer_block": peer_block,
            }
        )

    return {
        "ts": utc_now_iso(),
        "interface": {"name": iface_name, "public_key": iface_pub, "listen_port": int(listen_port)},
        "peers": peers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Export WireGuard wg0 status to JSON for admin panel.")
    parser.add_argument("--wg-conf", default="/etc/wireguard/wg0.conf")
    parser.add_argument("--out-dir", default="/opt/passengers-backend/wg")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    conf_text = Path(args.wg_conf).read_text(encoding="utf-8", errors="replace")
    names = parse_wg0_conf_names(conf_text)

    dump = run(["wg", "show", "wg0", "dump"])
    data = parse_wg_dump(dump, names)

    (out_dir / "peers.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (out_dir / "wg0.conf.redacted").write_text(redact_wg0_conf(conf_text), encoding="utf-8")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
