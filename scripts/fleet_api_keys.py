#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import secrets
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_KEYS_PATH = Path("fleet/secrets/system_api_keys.csv")
DEFAULT_ADMIN_TOKEN_PATH = Path("fleet/secrets/admin_api_key.txt")
DEFAULT_REGISTRY = Path("fleet/registry.csv")
DEFAULT_SERVER_HOST = "207.180.213.225"
DEFAULT_SERVER_USER = "alis"
DEFAULT_BACKEND_ENV_PATH = "/opt/passengers-backend/.env"


@dataclass
class KeyRow:
    system_id: str
    key: str
    status: str
    created_at: str
    rotated_from: str
    revoked_at: str
    notes: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def run(cmd: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, text=True, input=input_text, capture_output=True, check=False)


def ssh(user: str, host: str, remote_cmd: str, *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    control_path = f"/tmp/fleet_api_keys_mux_{host}_{user}"
    return run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=10",
            "-o",
            "ControlMaster=auto",
            "-o",
            "ControlPersist=60",
            "-o",
            f"ControlPath={control_path}",
            f"{user}@{host}",
            remote_cmd,
        ],
        input_text=input_text,
    )


def read_registry_system_ids(path: Path) -> set[str]:
    if not path.exists():
        raise SystemExit(f"Registry not found: {path}")
    systems: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if "system_id" not in set(reader.fieldnames or []):
            raise SystemExit(f"Registry has no system_id column: {path}")
        for row in reader:
            system_id = str((row.get("system_id") or "")).strip()
            if system_id:
                systems.add(system_id)
    return systems


def load_rows(path: Path) -> list[KeyRow]:
    if not path.exists():
        return []
    rows: list[KeyRow] = []
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"system_id", "key", "status", "created_at", "rotated_from", "revoked_at", "notes"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            raise SystemExit(f"Keys file missing columns: {', '.join(sorted(missing))}")
        for raw in reader:
            rows.append(
                KeyRow(
                    system_id=str(raw.get("system_id") or "").strip(),
                    key=str(raw.get("key") or "").strip(),
                    status=str(raw.get("status") or "").strip().lower(),
                    created_at=str(raw.get("created_at") or "").strip(),
                    rotated_from=str(raw.get("rotated_from") or "").strip(),
                    revoked_at=str(raw.get("revoked_at") or "").strip(),
                    notes=str(raw.get("notes") or "").strip(),
                )
            )
    return rows


def save_rows(path: Path, rows: list[KeyRow]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["system_id", "key", "status", "created_at", "rotated_from", "revoked_at", "notes"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "system_id": row.system_id,
                    "key": row.key,
                    "status": row.status,
                    "created_at": row.created_at,
                    "rotated_from": row.rotated_from,
                    "revoked_at": row.revoked_at,
                    "notes": row.notes,
                }
            )


def active_row(rows: list[KeyRow], system_id: str) -> KeyRow | None:
    found: KeyRow | None = None
    for row in rows:
        if row.system_id == system_id and row.status == "active":
            found = row
    return found


def random_key() -> str:
    return secrets.token_hex(24)


def ensure_admin_token(path: Path) -> str:
    if path.exists():
        token = path.read_text(encoding="utf-8", errors="replace").strip()
        if token:
            return token
    token = secrets.token_hex(24)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(token + "\n", encoding="utf-8")
    return token


def parse_env_text(text: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def merge_env_text(existing_text: str, updates: dict[str, str]) -> str:
    lines = existing_text.splitlines()
    key_to_index: dict[str, int] = {}
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _ = stripped.split("=", 1)
        key_to_index[key.strip()] = idx

    for key, value in updates.items():
        line = f"{key}={value}"
        if key in key_to_index:
            lines[key_to_index[key]] = line
        else:
            lines.append(line)

    return ("\n".join(lines).rstrip() + "\n") if lines else ""


def cmd_list(args: argparse.Namespace) -> int:
    rows = load_rows(args.keys_file)
    print(f"keys_file={args.keys_file}")
    print(f"rows={len(rows)}")
    for row in rows:
        masked = f"{row.key[:8]}...{row.key[-6:]}" if len(row.key) >= 14 else row.key
        print(
            f"{row.system_id} status={row.status} key={masked} created_at={row.created_at} revoked_at={row.revoked_at or '-'}"
        )
    return 0


def cmd_get(args: argparse.Namespace) -> int:
    rows = load_rows(args.keys_file)
    row = active_row(rows, args.system_id)
    if row is None:
        return 1
    print(row.key)
    return 0


def cmd_ensure(args: argparse.Namespace) -> int:
    valid_systems = read_registry_system_ids(args.registry)
    if args.system_id not in valid_systems:
        raise SystemExit(f"system_id not found in registry: {args.system_id}")

    rows = load_rows(args.keys_file)
    current = active_row(rows, args.system_id)
    if current is not None:
        print(f"system_id={args.system_id} status=exists key={current.key}")
        return 0

    key = random_key()
    rows.append(
        KeyRow(
            system_id=args.system_id,
            key=key,
            status="active",
            created_at=utc_now_iso(),
            rotated_from="",
            revoked_at="",
            notes=args.notes,
        )
    )
    save_rows(args.keys_file, rows)
    print(f"system_id={args.system_id} status=created key={key}")
    return 0


def cmd_rotate(args: argparse.Namespace) -> int:
    valid_systems = read_registry_system_ids(args.registry)
    if args.system_id not in valid_systems:
        raise SystemExit(f"system_id not found in registry: {args.system_id}")

    rows = load_rows(args.keys_file)
    now = utc_now_iso()
    old = active_row(rows, args.system_id)
    if old is not None:
        for idx, row in enumerate(rows):
            if row.system_id == args.system_id and row.status == "active" and row.key == old.key:
                rows[idx] = KeyRow(
                    system_id=row.system_id,
                    key=row.key,
                    status="rotated",
                    created_at=row.created_at,
                    rotated_from=row.rotated_from,
                    revoked_at=now,
                    notes=(row.notes + "; rotated").strip("; "),
                )
                break

    new_key = random_key()
    rows.append(
        KeyRow(
            system_id=args.system_id,
            key=new_key,
            status="active",
            created_at=now,
            rotated_from=(old.key if old else ""),
            revoked_at="",
            notes=args.notes,
        )
    )
    save_rows(args.keys_file, rows)
    print(f"system_id={args.system_id} status=rotated key={new_key}")
    return 0


def cmd_revoke(args: argparse.Namespace) -> int:
    rows = load_rows(args.keys_file)
    now = utc_now_iso()
    changed = False
    for idx, row in enumerate(rows):
        if row.system_id == args.system_id and row.status == "active":
            rows[idx] = KeyRow(
                system_id=row.system_id,
                key=row.key,
                status="revoked",
                created_at=row.created_at,
                rotated_from=row.rotated_from,
                revoked_at=now,
                notes=(row.notes + f"; revoked:{args.reason}").strip("; "),
            )
            changed = True
    if not changed:
        print(f"system_id={args.system_id} status=not_active")
        return 0
    save_rows(args.keys_file, rows)
    print(f"system_id={args.system_id} status=revoked")
    return 0


def cmd_sync_server(args: argparse.Namespace) -> int:
    rows = load_rows(args.keys_file)
    active = [row for row in rows if row.status == "active"]
    if not active:
        raise SystemExit("No active API keys to sync")

    active_sorted = sorted(active, key=lambda item: item.system_id)
    ingest_keys = ",".join(row.key for row in active_sorted)
    admin_key = ensure_admin_token(args.admin_token_file)

    remote_env = ssh(args.server_user, args.server_host, f"test -f '{args.backend_env_path}' && cat '{args.backend_env_path}' || true")
    if remote_env.returncode != 0:
        raise SystemExit(f"Cannot read remote env:\n{remote_env.stdout}{remote_env.stderr}")
    merged = merge_env_text(
        remote_env.stdout,
        {"PASSENGERS_API_KEYS": ingest_keys, "ADMIN_API_KEYS": admin_key},
    )

    upload = ssh(args.server_user, args.server_host, "cat > /tmp/passengers-backend.env.tmp", input_text=merged)
    if upload.returncode != 0:
        raise SystemExit(f"Cannot upload env file:\n{upload.stdout}{upload.stderr}")

    install = ssh(
        args.server_user,
        args.server_host,
        (
            f"install -m 640 -o {args.server_user} -g {args.server_user} "
            f"/tmp/passengers-backend.env.tmp '{args.backend_env_path}' && rm -f /tmp/passengers-backend.env.tmp"
        ),
    )
    if install.returncode != 0:
        raise SystemExit(f"Cannot install env file:\n{install.stdout}{install.stderr}")

    restart = ssh(
        args.server_user,
        args.server_host,
        "cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml up -d api",
    )
    if restart.returncode != 0:
        raise SystemExit(f"Cannot restart backend:\n{restart.stdout}{restart.stderr}")

    verify_ok = False
    verify_out = ""
    for _ in range(20):
        verify = ssh(
            args.server_user,
            args.server_host,
            f"curl -sS -H 'Authorization: Bearer {active_sorted[0].key}' http://10.66.0.1/health",
        )
        verify_out = f"{verify.stdout}{verify.stderr}"
        if verify.returncode == 0 and '"status":"ok"' in verify.stdout:
            verify_ok = True
            break
        time.sleep(1.0)
    if not verify_ok:
        raise SystemExit(f"Backend health check failed after retry:\n{verify_out}")

    sync_proxy = ssh(
        args.server_user,
        args.server_host,
        (
            "if [ -f /etc/nginx/conf.d/passengers-admin.conf ]; then "
            f"sudo tee /etc/nginx/passengers-admin-token.inc >/dev/null <<'EOF'\nset $passengers_admin_api_token \"{admin_key}\";\nEOF\n"
            "sudo chmod 640 /etc/nginx/passengers-admin-token.inc; "
            "sudo chown root:www-data /etc/nginx/passengers-admin-token.inc; "
            "sudo nginx -t && sudo systemctl reload nginx; "
            "fi"
        ),
    )
    if sync_proxy.returncode != 0:
        raise SystemExit(f"Cannot sync admin proxy token:\n{sync_proxy.stdout}{sync_proxy.stderr}")

    print(f"server={args.server_user}@{args.server_host}")
    print(f"active_ingest_keys={len(active_sorted)}")
    print(f"admin_api_key={admin_key[:8]}...{admin_key[-6:]}")
    print("status=synced")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage per-system API keys for fleet and sync to backend server.")
    parser.add_argument("--keys-file", type=Path, default=DEFAULT_KEYS_PATH, help="CSV storage for system API keys")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Fleet registry path")
    parser.add_argument(
        "--admin-token-file",
        type=Path,
        default=DEFAULT_ADMIN_TOKEN_PATH,
        help="Local file with admin API token for proxy/admin endpoints",
    )

    sub = parser.add_subparsers(dest="command", required=True)

    p_list = sub.add_parser("list", help="List key records")
    p_list.set_defaults(func=cmd_list)

    p_get = sub.add_parser("get", help="Print active key for system_id")
    p_get.add_argument("--system-id", required=True)
    p_get.set_defaults(func=cmd_get)

    p_ensure = sub.add_parser("ensure", help="Ensure active key exists for system_id")
    p_ensure.add_argument("--system-id", required=True)
    p_ensure.add_argument("--notes", default="created")
    p_ensure.set_defaults(func=cmd_ensure)

    p_rotate = sub.add_parser("rotate", help="Rotate active key for system_id")
    p_rotate.add_argument("--system-id", required=True)
    p_rotate.add_argument("--notes", default="rotated")
    p_rotate.set_defaults(func=cmd_rotate)

    p_revoke = sub.add_parser("revoke", help="Revoke active key for system_id")
    p_revoke.add_argument("--system-id", required=True)
    p_revoke.add_argument("--reason", default="manual")
    p_revoke.set_defaults(func=cmd_revoke)

    p_sync = sub.add_parser("sync-server", help="Sync active keys to backend server env and restart api")
    p_sync.add_argument("--server-host", default=DEFAULT_SERVER_HOST)
    p_sync.add_argument("--server-user", default=DEFAULT_SERVER_USER)
    p_sync.add_argument("--backend-env-path", default=DEFAULT_BACKEND_ENV_PATH)
    p_sync.set_defaults(func=cmd_sync_server)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())
