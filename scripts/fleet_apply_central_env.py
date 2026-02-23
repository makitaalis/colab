#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_REGISTRY = Path("fleet/registry.csv")
DEFAULT_BUNDLE_ROOT = Path("fleet/out")
DEFAULT_ENV_PATH = "/etc/passengers/passengers.env"
DEFAULT_BACKEND_ENV_PATH = "/opt/passengers-backend/.env"
DEFAULT_KEYS_FILE = Path("fleet/secrets/system_api_keys.csv")
KEY_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def run_command(cmd: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


def ssh_result(*, user: str, host: str, remote_cmd: str, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    cmd = [
        "ssh",
        "-o",
        "BatchMode=yes",
        "-o",
        "StrictHostKeyChecking=accept-new",
        "-o",
        "ConnectTimeout=10",
        f"{user}@{host}",
        remote_cmd,
    ]
    return run_command(cmd, input_text=input_text)


def read_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def parse_env_text(text: str) -> dict[str, str]:
    env: dict[str, str] = {}
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not KEY_RE.match(key):
            continue
        env[key] = value.strip()
    return env


def normalize_stop_mode(value: str | None) -> str:
    mode = str(value or "").strip().lower()
    if mode in {"manual", "timer"}:
        return mode
    return "timer"


def ensure_bundle(*, repo_root: Path, registry: Path, bundle_root: Path, system_id: str) -> Path:
    bundle_dir = bundle_root / system_id
    if bundle_dir.exists():
        return bundle_dir
    cmd = [
        sys.executable,
        str(repo_root / "scripts/fleet_registry.py"),
        "--registry",
        str(registry),
        "bundle",
        "--system-id",
        system_id,
        "--out-root",
        str(bundle_root),
    ]
    result = run_command(cmd)
    if result.returncode != 0:
        raise SystemExit(f"Failed to generate bundle:\n{result.stdout}{result.stderr}")
    return bundle_dir


def fetch_backend_api_key(*, server_user: str, server_host: str, backend_env_path: str) -> str:
    cmd = (
        f"grep -m1 '^PASSENGERS_API_KEYS=' '{backend_env_path}' | cut -d= -f2 | tr -d '\\r' | cut -d, -f1"
    )
    result = ssh_result(user=server_user, host=server_host, remote_cmd=cmd)
    if result.returncode != 0:
        raise SystemExit(f"Cannot fetch backend API key from server:\n{result.stdout}{result.stderr}")
    key = result.stdout.strip()
    if not key:
        raise SystemExit("Backend API key is empty in server env")
    return key


def fetch_local_system_api_key(*, keys_file: Path, system_id: str) -> str | None:
    if not keys_file.exists():
        return None
    with keys_file.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        required = {"system_id", "key", "status"}
        if not required.issubset(set(reader.fieldnames or [])):
            return None
        latest: str | None = None
        for row in reader:
            if str(row.get("system_id") or "").strip() != system_id:
                continue
            status = str(row.get("status") or "").strip().lower()
            if status != "active":
                continue
            key = str(row.get("key") or "").strip()
            if key:
                latest = key
    return latest


def fetch_remote_env(*, central_user: str, central_host: str, env_path: str) -> str:
    result = ssh_result(
        user=central_user,
        host=central_host,
        remote_cmd=f"sudo test -f '{env_path}' && sudo cat '{env_path}' || true",
    )
    if result.returncode != 0:
        raise SystemExit(f"Cannot read remote env file {env_path}:\n{result.stdout}{result.stderr}")
    return result.stdout


def merge_env_text(existing_text: str, updates: dict[str, str]) -> tuple[str, bool]:
    lines = existing_text.splitlines()
    key_to_index: dict[str, int] = {}
    for idx, raw in enumerate(lines):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _ = stripped.split("=", 1)
        key = key.strip()
        if KEY_RE.match(key):
            key_to_index[key] = idx

    for key, value in updates.items():
        line = f"{key}={value}"
        if key in key_to_index:
            lines[key_to_index[key]] = line
        else:
            lines.append(line)

    merged = ("\n".join(lines).rstrip() + "\n") if lines else ""
    changed = merged != existing_text
    return merged, changed


def push_remote_env(*, central_user: str, central_host: str, env_path: str, opi_user: str, content: str) -> None:
    tmp_path = "/tmp/passengers.env.sync.tmp"
    upload = ssh_result(
        user=central_user,
        host=central_host,
        remote_cmd=f"cat > '{tmp_path}'",
        input_text=content,
    )
    if upload.returncode != 0:
        raise SystemExit(f"Cannot upload env temp file:\n{upload.stdout}{upload.stderr}")

    install = ssh_result(
        user=central_user,
        host=central_host,
        remote_cmd=(
            f"sudo install -m 640 -o root -g '{opi_user}' '{tmp_path}' '{env_path}' "
            f"&& rm -f '{tmp_path}'"
        ),
    )
    if install.returncode != 0:
        raise SystemExit(f"Cannot install env file {env_path}:\n{install.stdout}{install.stderr}")


def restart_services(*, central_user: str, central_host: str, stop_mode: str) -> None:
    safe_mode = normalize_stop_mode(stop_mode)
    if safe_mode == "manual":
        mode_cmd = "sudo systemctl disable --now passengers-central-flush.timer >/dev/null 2>&1 || true;"
    else:
        mode_cmd = (
            "sudo systemctl enable --now passengers-central-flush.timer;"
            "sudo systemctl restart passengers-central-flush.timer;"
        )
    result = ssh_result(
        user=central_user,
        host=central_host,
        remote_cmd=(
            f"{mode_cmd}"
            "sudo systemctl restart passengers-central-uplink passengers-central-heartbeat.timer;"
            "sudo systemctl is-active passengers-central-uplink passengers-central-heartbeat.timer;"
            "systemctl is-enabled passengers-central-flush.timer 2>/dev/null || true;"
            "systemctl is-active passengers-central-flush.timer 2>/dev/null || true"
        ),
    )
    if result.returncode != 0:
        raise SystemExit(f"Cannot restart central services:\n{result.stdout}{result.stderr}")
    print(result.stdout.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply generated central passengers env template to central-gw.")
    parser.add_argument("--system-id", required=True, help="System id from fleet registry (example: sys-0001)")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to fleet registry CSV")
    parser.add_argument("--bundle-root", type=Path, default=DEFAULT_BUNDLE_ROOT, help="Fleet bundle root directory")
    parser.add_argument("--central-ip", default=None, help="Override central IP")
    parser.add_argument("--central-user", default=None, help="Override central SSH user")
    parser.add_argument("--server-host", default=None, help="Override backend server host")
    parser.add_argument("--server-user", default=None, help="Override backend server SSH user")
    parser.add_argument("--backend-api-key", default=None, help="Override backend API key (skip server fetch)")
    parser.add_argument("--env-path", default=DEFAULT_ENV_PATH, help="Remote env path on central")
    parser.add_argument("--backend-env-path", default=DEFAULT_BACKEND_ENV_PATH, help="Backend env path on server")
    parser.add_argument("--keys-file", type=Path, default=DEFAULT_KEYS_FILE, help="Local system API keys CSV")
    parser.add_argument("--no-restart", action="store_true", help="Do not restart central services")
    parser.add_argument("--dry-run", action="store_true", help="Show planned key updates, do not write remote env")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    registry = args.registry if args.registry.is_absolute() else (repo_root / args.registry)
    bundle_root = args.bundle_root if args.bundle_root.is_absolute() else (repo_root / args.bundle_root)
    bundle_dir = ensure_bundle(repo_root=repo_root, registry=registry, bundle_root=bundle_root, system_id=args.system_id)

    fleet_env_path = bundle_dir / "fleet.env"
    tmpl_env_path = bundle_dir / "passengers/central-passengers.env.template"
    if not fleet_env_path.exists():
        raise SystemExit(f"fleet.env missing: {fleet_env_path}")
    if not tmpl_env_path.exists():
        raise SystemExit(f"central-passengers.env.template missing: {tmpl_env_path}")

    fleet_env = read_env_file(fleet_env_path)
    updates = parse_env_text(tmpl_env_path.read_text(encoding="utf-8", errors="replace"))
    if not updates:
        raise SystemExit(f"No key-values found in template: {tmpl_env_path}")
    if not updates.get("CENTRAL_ID"):
        updates["CENTRAL_ID"] = args.system_id

    central_host = args.central_ip or fleet_env.get("CENTRAL_IP")
    central_user = args.central_user or fleet_env.get("OPI_USER", "orangepi")
    server_host = args.server_host or fleet_env.get("SERVER_HOST")
    server_user = args.server_user or fleet_env.get("SERVER_SSH_USER", "alis")
    if not central_host:
        raise SystemExit("CENTRAL_IP is not set (bundle or --central-ip)")

    api_key = args.backend_api_key
    if not api_key:
        local_keys_file = args.keys_file if args.keys_file.is_absolute() else (repo_root / args.keys_file)
        api_key = fetch_local_system_api_key(keys_file=local_keys_file, system_id=args.system_id)
    if not api_key:
        if not server_host:
            raise SystemExit("SERVER_HOST is not set (bundle or --server-host); cannot fetch BACKEND_API_KEY")
        api_key = fetch_backend_api_key(server_user=server_user, server_host=server_host, backend_env_path=args.backend_env_path)
    updates["BACKEND_API_KEY"] = api_key

    existing_text = fetch_remote_env(central_user=central_user, central_host=central_host, env_path=args.env_path)
    merged_text, changed = merge_env_text(existing_text, updates)
    effective_env = parse_env_text(merged_text)
    stop_mode = normalize_stop_mode(effective_env.get("STOP_MODE"))

    print(f"system_id={args.system_id}")
    print(f"central={central_user}@{central_host}")
    if server_host:
        print(f"server={server_user}@{server_host}")
    print(f"env_path={args.env_path}")
    print(f"keys={','.join(sorted(updates.keys()))}")
    print(f"stop_mode={stop_mode}")
    print(f"changed={str(changed).lower()}")

    if args.dry_run:
        print("dry_run=true (remote env not modified)")
        return 0

    if changed:
        push_remote_env(
            central_user=central_user,
            central_host=central_host,
            env_path=args.env_path,
            opi_user=central_user,
            content=merged_text,
        )

    if not args.no_restart:
        restart_services(central_user=central_user, central_host=central_host, stop_mode=stop_mode)

    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
