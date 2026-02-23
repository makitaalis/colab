#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import ipaddress
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

DEFAULT_REGISTRY = Path("fleet/registry.csv")
DEFAULT_OUT_ROOT = Path("fleet/out")
WG_NETWORK = ipaddress.ip_network("10.66.0.0/24")
RESERVED_WG_IPS = {
    ipaddress.ip_address("10.66.0.0"),
    ipaddress.ip_address("10.66.0.1"),
    ipaddress.ip_address("10.66.0.255"),
}
VALID_STATUSES = {"planned", "active", "retired", "lab", "disabled"}
SYSTEM_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{2,63}$")
HOST_PORT_RE = re.compile(r"^[A-Za-z0-9.-]+:[0-9]{1,5}$")


@dataclass(frozen=True)
class SystemEntry:
    system_id: str
    vehicle_id: str
    wg_ip: str
    server_endpoint: str
    status: str
    notes: str
    line_no: int


def _read_registry(path: Path) -> list[SystemEntry]:
    if not path.exists():
        raise SystemExit(f"Registry not found: {path}")

    rows: list[SystemEntry] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"system_id", "vehicle_id", "wg_ip", "server_endpoint", "status", "notes"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Registry missing columns: {', '.join(sorted(missing))}")
        for idx, raw in enumerate(reader, start=2):
            rows.append(
                SystemEntry(
                    system_id=(raw.get("system_id") or "").strip(),
                    vehicle_id=(raw.get("vehicle_id") or "").strip(),
                    wg_ip=(raw.get("wg_ip") or "").strip(),
                    server_endpoint=(raw.get("server_endpoint") or "").strip(),
                    status=(raw.get("status") or "").strip().lower(),
                    notes=(raw.get("notes") or "").strip(),
                    line_no=idx,
                )
            )
    return rows


def _validate_endpoint(value: str) -> bool:
    if not HOST_PORT_RE.match(value):
        return False
    host, port_text = value.rsplit(":", 1)
    if not host:
        return False
    try:
        port = int(port_text)
    except ValueError:
        return False
    return 1 <= port <= 65535


def _parse_ip(value: str) -> ipaddress.IPv4Address | None:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return None
    if not isinstance(ip, ipaddress.IPv4Address):
        return None
    return ip


def validate_entries(entries: Iterable[SystemEntry]) -> list[str]:
    errors: list[str] = []
    seen_system: dict[str, int] = {}
    seen_vehicle: dict[str, int] = {}
    seen_wg: dict[str, int] = {}

    for item in entries:
        prefix = f"line {item.line_no} ({item.system_id or 'no-system-id'})"

        if not item.system_id:
            errors.append(f"{prefix}: system_id is required")
        elif not SYSTEM_ID_RE.match(item.system_id):
            errors.append(f"{prefix}: invalid system_id '{item.system_id}'")

        if not item.vehicle_id:
            errors.append(f"{prefix}: vehicle_id is required")

        ip = _parse_ip(item.wg_ip)
        if ip is None:
            errors.append(f"{prefix}: invalid wg_ip '{item.wg_ip}'")
        else:
            if ip not in WG_NETWORK:
                errors.append(f"{prefix}: wg_ip '{item.wg_ip}' is outside {WG_NETWORK}")
            if ip in RESERVED_WG_IPS:
                errors.append(f"{prefix}: wg_ip '{item.wg_ip}' is reserved")

        if not _validate_endpoint(item.server_endpoint):
            errors.append(f"{prefix}: invalid server_endpoint '{item.server_endpoint}'")

        if item.status not in VALID_STATUSES:
            errors.append(f"{prefix}: invalid status '{item.status}'")

        if item.system_id:
            prev = seen_system.get(item.system_id)
            if prev is not None:
                errors.append(f"{prefix}: duplicate system_id '{item.system_id}' (first at line {prev})")
            else:
                seen_system[item.system_id] = item.line_no

        if item.vehicle_id:
            prev = seen_vehicle.get(item.vehicle_id)
            if prev is not None:
                errors.append(f"{prefix}: duplicate vehicle_id '{item.vehicle_id}' (first at line {prev})")
            else:
                seen_vehicle[item.vehicle_id] = item.line_no

        if item.wg_ip:
            prev = seen_wg.get(item.wg_ip)
            if prev is not None:
                errors.append(f"{prefix}: duplicate wg_ip '{item.wg_ip}' (first at line {prev})")
            else:
                seen_wg[item.wg_ip] = item.line_no

    return errors


def suggest_next_wg_ip(entries: Iterable[SystemEntry]) -> str:
    used = {row.wg_ip for row in entries if row.wg_ip}
    for host in range(11, 255):
        candidate = f"10.66.0.{host}"
        if candidate in used:
            continue
        ip = ipaddress.ip_address(candidate)
        if ip in RESERVED_WG_IPS:
            continue
        return candidate
    raise SystemExit("No free WG IP left in 10.66.0.0/24")


def _find_system(entries: Iterable[SystemEntry], system_id: str) -> SystemEntry:
    for item in entries:
        if item.system_id == system_id:
            return item
    raise SystemExit(f"system_id not found in registry: {system_id}")


def central_id_for_system(system_id: str) -> str:
    return system_id


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def bundle_system(
    *,
    item: SystemEntry,
    out_root: Path,
    backend_host: str,
    opi_user: str,
    server_ssh_user: str,
    server_pubkey: str | None,
) -> Path:
    central_id = central_id_for_system(item.system_id)
    server_host, server_port = item.server_endpoint.rsplit(":", 1)
    out_dir = out_root / item.system_id
    wg_dir = out_dir / "wireguard"
    passengers_dir = out_dir / "passengers"
    out_dir.mkdir(parents=True, exist_ok=True)
    wg_dir.mkdir(parents=True, exist_ok=True)
    passengers_dir.mkdir(parents=True, exist_ok=True)

    _write_text(
        out_dir / "fleet.env",
        "\n".join(
            [
                f"SYSTEM_ID={item.system_id}",
                f"VEHICLE_ID={item.vehicle_id}",
                f"CENTRAL_ID={central_id}",
                f"WG_IP={item.wg_ip}",
                f"SERVER_HOST={server_host}",
                f"SERVER_PORT={server_port}",
                f"SERVER_SSH_USER={server_ssh_user}",
                f"BACKEND_HOST={backend_host}",
                "CENTRAL_IP=192.168.10.1",
                "EDGE_IPS_CSV=192.168.10.11,192.168.10.12",
                f"OPI_USER={opi_user}",
                "STOP_MODE=manual",
                "STOP_FLUSH_INTERVAL_SEC=120",
                "",
            ]
        ),
    )

    _write_text(
        wg_dir / "server-peer.conf",
        "\n".join(
            [
                f"# BEGIN passengers system_id: {item.system_id}",
                "[Peer]",
                f"# system_id: {item.system_id}",
                f"# vehicle_id: {item.vehicle_id}",
                "PublicKey = <CENTRAL_PUBLIC_KEY>",
                f"AllowedIPs = {item.wg_ip}/32",
                f"# END passengers system_id: {item.system_id}",
                "",
            ]
        ),
    )

    server_pubkey_value = server_pubkey if server_pubkey else "<SERVER_PUBLIC_KEY>"
    _write_text(
        wg_dir / "central-wg0.conf.template",
        "\n".join(
            [
                "[Interface]",
                f"Address = {item.wg_ip}/32",
                "PrivateKey = <CENTRAL_PRIVATE_KEY>",
                "",
                "[Peer]",
                f"PublicKey = {server_pubkey_value}",
                f"Endpoint = {item.server_endpoint}",
                f"AllowedIPs = {backend_host}/32",
                "PersistentKeepalive = 25",
                "",
            ]
        ),
    )

    _write_text(
        passengers_dir / "central-passengers.env.template",
        "\n".join(
            [
                f"VEHICLE_ID={item.vehicle_id}",
                f"BACKEND_URL=http://{backend_host}/api/v1/ingest/stops",
                f"BACKEND_HEARTBEAT_URL=http://{backend_host}/api/v1/ingest/central-heartbeat",
                "BACKEND_API_KEY=<PUT_REAL_KEY_HERE>",
                f"CENTRAL_ID={central_id}",
                "STOP_MODE=manual",
                "STOP_FLUSH_INTERVAL_SEC=120",
                "CENTRAL_EVENTS_MAX_ROWS=300000",
                "CENTRAL_EVENTS_MAX_AGE_SEC=1209600",
                "CENTRAL_SENT_BATCHES_MAX_ROWS=50000",
                "CENTRAL_SENT_BATCHES_MAX_AGE_SEC=2592000",
                "CENTRAL_PENDING_BATCHES_MAX_ROWS=10000",
                "CENTRAL_PENDING_BATCHES_MAX_AGE_SEC=2592000",
                "CENTRAL_PENDING_BATCHES_DROP_AGE=0",
                "",
            ]
        ),
    )

    commands = f"""# {item.system_id} — quick start bundle

## 0) Preconditions
- Central + two Edge nodes are flashed and reachable on LAN.
- This bundle targets no-modules stage (no camera/GPS/RTC/LTE), offline profile enabled.

## 1) Validate and inspect bundle
python3 scripts/fleet_registry.py validate
ls -la {out_dir.as_posix()}

## 2) Ensure per-system API key and sync server
python3 scripts/fleet_api_keys.py ensure --system-id {item.system_id}
python3 scripts/fleet_api_keys.py sync-server --server-host {server_host} --server-user {server_ssh_user}

## 3) Apply WireGuard peer on server
python3 scripts/fleet_apply_wg_peer.py --system-id {item.system_id} --fetch-central-pubkey
# If central key missing:
# python3 scripts/fleet_apply_wg_peer.py --system-id {item.system_id} --fetch-central-pubkey --ensure-central-key

## 4) Deploy MVP services to this system
source {out_dir.as_posix()}/fleet.env
./scripts/deploy_passengers_mvp.sh \\
  --central-ip "${{CENTRAL_IP}}" \\
  --edge-ips "${{EDGE_IPS_CSV}}" \\
  --user "${{OPI_USER}}" \\
  --server-host "${{SERVER_HOST}}" \\
  --server-user "${{SERVER_SSH_USER}}" \\
  --backend-host "${{BACKEND_HOST}}" \\
  --stop-mode "${{STOP_MODE}}" \\
  --stop-flush-interval-sec "${{STOP_FLUSH_INTERVAL_SEC}}"

## 5) Apply central env template (vehicle/CENTRAL_ID/offline limits)
python3 scripts/fleet_apply_central_env.py --system-id {item.system_id}

## 6) Run smoke test
./scripts/mvp_e2e_smoke.sh --central-ip "${{CENTRAL_IP}}" --door1-ip 192.168.10.11 --door2-ip 192.168.10.12 --server-host "${{SERVER_HOST}}"

## 7) Save commissioning report
python3 scripts/fleet_commission.py --system-id {item.system_id} --smoke

## 8) Admin panel smoke-gate (after deploy/update)
./scripts/admin_panel_smoke_gate.sh --server-host {server_host} --server-user {server_ssh_user} --admin-user admin --admin-pass "<BASIC_AUTH_PASS>"
"""
    _write_text(out_dir / "commands.md", commands)
    return out_dir


def cmd_validate(args: argparse.Namespace) -> int:
    entries = _read_registry(args.registry)
    errors = validate_entries(entries)
    if errors:
        print("Registry validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1
    print(f"Registry OK: systems={len(entries)}")
    return 0


def cmd_next_wg_ip(args: argparse.Namespace) -> int:
    entries = _read_registry(args.registry)
    errors = validate_entries(entries)
    if errors:
        print("Registry invalid; cannot suggest WG IP until fixed.")
        for e in errors[:20]:
            print(f"- {e}")
        return 1
    print(suggest_next_wg_ip(entries))
    return 0


def cmd_bundle(args: argparse.Namespace) -> int:
    entries = _read_registry(args.registry)
    errors = validate_entries(entries)
    if errors:
        print("Registry validation FAILED:")
        for e in errors:
            print(f"- {e}")
        return 1

    item = _find_system(entries, args.system_id)
    out_dir = bundle_system(
        item=item,
        out_root=args.out_root,
        backend_host=args.backend_host,
        opi_user=args.opi_user,
        server_ssh_user=args.server_ssh_user,
        server_pubkey=args.server_pubkey,
    )
    print(f"Bundle generated: {out_dir}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Fleet registry tools for OPi rollout at scale.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to fleet registry CSV")

    sub = parser.add_subparsers(dest="command", required=True)

    p_validate = sub.add_parser("validate", help="Validate fleet registry")
    p_validate.set_defaults(func=cmd_validate)

    p_next = sub.add_parser("next-wg-ip", help="Suggest next free WG IP")
    p_next.set_defaults(func=cmd_next_wg_ip)

    p_bundle = sub.add_parser("bundle", help="Generate per-system configuration bundle")
    p_bundle.add_argument("--system-id", required=True, help="System id from registry (example: sys-0001)")
    p_bundle.add_argument("--out-root", type=Path, default=DEFAULT_OUT_ROOT, help="Output root directory")
    p_bundle.add_argument("--backend-host", default="10.66.0.1", help="Backend host reachable from central via WG")
    p_bundle.add_argument("--opi-user", default="orangepi", help="SSH user on OPi nodes")
    p_bundle.add_argument("--server-ssh-user", default="alis", help="SSH user on backend server")
    p_bundle.add_argument(
        "--server-pubkey",
        default=None,
        help="Optional server public key to embed into central wg template (otherwise placeholder)",
    )
    p_bundle.set_defaults(func=cmd_bundle)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
