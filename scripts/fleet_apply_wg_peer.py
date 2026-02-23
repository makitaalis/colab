#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

DEFAULT_REGISTRY = Path("fleet/registry.csv")
DEFAULT_BUNDLE_ROOT = Path("fleet/out")
DEFAULT_WG_CONF_PATH = "/etc/wireguard/wg0.conf"
DEFAULT_CENTRAL_PUBKEY_PATH = "/etc/wireguard/central.pub"
DEFAULT_CENTRAL_KEY_PATH = "/etc/wireguard/central.key"
WG_KEY_RE = re.compile(r"^[A-Za-z0-9+/]{43}=$")


def run_command(cmd: list[str], *, input_text: str | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        check=False,
    )


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


def upsert_peer_block(conf_text: str, peer_block: str, *, system_id: str) -> tuple[str, str]:
    begin_marker = f"# BEGIN passengers system_id: {system_id}"
    end_marker = f"# END passengers system_id: {system_id}"

    if begin_marker not in peer_block or end_marker not in peer_block:
        raise SystemExit(f"Peer block does not contain required markers for system_id={system_id}")

    pattern = re.compile(re.escape(begin_marker) + r".*?" + re.escape(end_marker) + r"\n?", re.DOTALL)
    replacement = peer_block.strip() + "\n"

    if pattern.search(conf_text):
        new_text = pattern.sub(replacement, conf_text, count=1)
        return new_text, "updated"

    if conf_text.strip():
        new_text = conf_text.rstrip() + "\n\n" + replacement
    else:
        new_text = replacement
    return new_text, "added"


def ssh_result(*, user: str, host: str, remote_cmd: str) -> subprocess.CompletedProcess[str]:
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
    return run_command(cmd)


def fetch_remote_file(*, user: str, host: str, path: str) -> str:
    result = ssh_result(user=user, host=host, remote_cmd=f"sudo cat '{path}'")
    if result.returncode != 0:
        raise SystemExit(f"Cannot read remote file {path}:\n{result.stdout}{result.stderr}")
    return result.stdout


def normalize_wg_public_key(raw: str) -> str:
    key = raw.strip()
    if not WG_KEY_RE.fullmatch(key):
        raise SystemExit(f"Invalid WireGuard public key format: '{key}'")
    return key


def fetch_central_public_key(
    *,
    user: str,
    host: str,
    pubkey_path: str,
    key_path: str,
    ensure_key: bool,
) -> str:
    if ensure_key:
        remote_cmd = (
            "sudo install -d -m 700 /etc/wireguard; "
            f"if [ ! -s '{pubkey_path}' ] || [ ! -s '{key_path}' ]; then "
            f"sudo sh -lc 'umask 077; wg genkey > \"{key_path}\"; wg pubkey < \"{key_path}\" > \"{pubkey_path}\"'; "
            "fi; "
            f"sudo cat '{pubkey_path}'"
        )
    else:
        remote_cmd = f"sudo cat '{pubkey_path}'"
    result = ssh_result(user=user, host=host, remote_cmd=remote_cmd)
    if result.returncode != 0:
        raise SystemExit(f"Cannot fetch central public key from {user}@{host}:\n{result.stdout}{result.stderr}")
    return normalize_wg_public_key(result.stdout)


def set_peer_public_key(peer_block: str, *, pubkey: str) -> str:
    replaced = re.sub(r"(?m)^PublicKey\s*=\s*.*$", f"PublicKey = {pubkey}", peer_block)
    if replaced == peer_block and "PublicKey" not in peer_block:
        raise SystemExit("Peer block has no PublicKey line")
    replaced = replaced.replace("<CENTRAL_PUBLIC_KEY>", pubkey)
    return replaced


def push_remote_file(*, user: str, host: str, path: str, content: str) -> None:
    tmp_path = f"/tmp/passengers-wg-{Path(path).name}.tmp"
    upload = run_command(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=10",
            f"{user}@{host}",
            f"cat > '{tmp_path}'",
        ],
        input_text=content,
    )
    if upload.returncode != 0:
        raise SystemExit(f"Cannot upload temp file:\n{upload.stdout}{upload.stderr}")

    install = ssh_result(
        user=user,
        host=host,
        remote_cmd=f"sudo install -m 600 -o root -g root '{tmp_path}' '{path}' && rm -f '{tmp_path}'",
    )
    if install.returncode != 0:
        raise SystemExit(f"Cannot install remote file {path}:\n{install.stdout}{install.stderr}")


def restart_wg(*, user: str, host: str) -> None:
    result = ssh_result(
        user=user,
        host=host,
        remote_cmd="sudo systemctl restart wg-quick@wg0 && sudo systemctl is-active wg-quick@wg0 && sudo wg show wg0 | sed -n '1,80p'",
    )
    if result.returncode != 0:
        raise SystemExit(f"Failed to restart wg-quick@wg0:\n{result.stdout}{result.stderr}")
    print(result.stdout.strip())


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply generated WireGuard peer block to server wg0.conf (idempotent).")
    parser.add_argument("--system-id", required=True, help="System id from fleet registry (example: sys-0001)")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to fleet registry CSV")
    parser.add_argument("--bundle-root", type=Path, default=DEFAULT_BUNDLE_ROOT, help="Fleet bundle root directory")
    parser.add_argument("--server-host", default=None, help="Override server host")
    parser.add_argument("--server-user", default=None, help="Override server SSH user")
    parser.add_argument("--central-host", default=None, help="Override central host to fetch central public key")
    parser.add_argument("--central-user", default=None, help="Override central SSH user")
    parser.add_argument(
        "--central-pubkey-path",
        default=DEFAULT_CENTRAL_PUBKEY_PATH,
        help="Public key path on central (default: /etc/wireguard/central.pub)",
    )
    parser.add_argument(
        "--central-key-path",
        default=DEFAULT_CENTRAL_KEY_PATH,
        help="Private key path on central, used when --ensure-central-key is set",
    )
    parser.add_argument(
        "--central-public-key",
        default=None,
        help="Explicit central public key; overrides fetch from central host",
    )
    parser.add_argument(
        "--fetch-central-pubkey",
        action="store_true",
        help="Fetch central public key via SSH if peer block still contains placeholder",
    )
    parser.add_argument(
        "--ensure-central-key",
        action="store_true",
        help="When fetching from central: generate central.key/central.pub if missing",
    )
    parser.add_argument("--wg-conf-path", default=DEFAULT_WG_CONF_PATH, help="Remote wg0 config path")
    parser.add_argument("--no-restart", action="store_true", help="Do not restart wg-quick@wg0")
    parser.add_argument("--dry-run", action="store_true", help="Print action only, do not modify remote file")
    parser.add_argument(
        "--allow-placeholder",
        action="store_true",
        help="Allow <CENTRAL_PUBLIC_KEY> placeholder in peer block (for lab preview only)",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    registry = args.registry if args.registry.is_absolute() else (repo_root / args.registry)
    bundle_root = args.bundle_root if args.bundle_root.is_absolute() else (repo_root / args.bundle_root)

    bundle_dir = ensure_bundle(repo_root=repo_root, registry=registry, bundle_root=bundle_root, system_id=args.system_id)
    peer_path = bundle_dir / "wireguard/server-peer.conf"
    fleet_env_path = bundle_dir / "fleet.env"
    if not peer_path.exists():
        raise SystemExit(f"Peer file missing: {peer_path}")
    if not fleet_env_path.exists():
        raise SystemExit(f"Fleet env missing: {fleet_env_path}")

    fleet_env = read_env_file(fleet_env_path)
    server_host = args.server_host or fleet_env.get("SERVER_HOST")
    server_user = args.server_user or fleet_env.get("SERVER_SSH_USER", "alis")
    if not server_host:
        raise SystemExit("SERVER_HOST is not set (bundle or --server-host)")
    central_host = args.central_host or fleet_env.get("CENTRAL_IP")
    central_user = args.central_user or fleet_env.get("OPI_USER", "orangepi")

    peer_block = peer_path.read_text(encoding="utf-8", errors="replace")
    placeholder = "<CENTRAL_PUBLIC_KEY>" in peer_block
    central_pubkey = args.central_public_key.strip() if args.central_public_key else ""
    if central_pubkey:
        central_pubkey = normalize_wg_public_key(central_pubkey)
    elif placeholder and args.fetch_central_pubkey:
        if not central_host:
            raise SystemExit("CENTRAL_IP is not set (bundle or --central-host) for --fetch-central-pubkey")
        central_pubkey = fetch_central_public_key(
            user=central_user,
            host=central_host,
            pubkey_path=args.central_pubkey_path,
            key_path=args.central_key_path,
            ensure_key=args.ensure_central_key,
        )

    if central_pubkey:
        updated_peer_block = set_peer_public_key(peer_block, pubkey=central_pubkey)
        if updated_peer_block != peer_block:
            peer_path.write_text(updated_peer_block, encoding="utf-8")
            peer_block = updated_peer_block

    if "<CENTRAL_PUBLIC_KEY>" in peer_block and not args.allow_placeholder:
        raise SystemExit(
            f"Peer block {peer_path} contains <CENTRAL_PUBLIC_KEY>. "
            "Use --fetch-central-pubkey or --central-public-key, or pass --allow-placeholder for dry lab preview."
        )

    remote_conf = fetch_remote_file(user=server_user, host=server_host, path=args.wg_conf_path)
    updated_conf, action = upsert_peer_block(remote_conf, peer_block, system_id=args.system_id)
    changed = updated_conf != remote_conf

    print(f"system_id={args.system_id}")
    print(f"server={server_user}@{server_host}")
    if central_pubkey:
        print(f"central_pubkey_source={'arg' if args.central_public_key else 'ssh'}")
    if args.fetch_central_pubkey and central_host:
        print(f"central={central_user}@{central_host}")
    print(f"wg_conf={args.wg_conf_path}")
    print(f"peer_action={action}")
    print(f"changed={str(changed).lower()}")

    if args.dry_run:
        print("dry_run=true (remote file not modified)")
        return 0

    if changed:
        push_remote_file(user=server_user, host=server_host, path=args.wg_conf_path, content=updated_conf)

    if not args.no_restart:
        restart_wg(user=server_user, host=server_host)

    print("done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
