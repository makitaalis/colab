#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import shlex
import subprocess
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class CommandResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str


def run(cmd: list[str], *, timeout_sec: int = 30, input_text: str | None = None) -> CommandResult:
    proc = subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
        check=False,
    )
    return CommandResult(cmd=cmd, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def ssh(host: str, user: str, script: str, *, timeout_sec: int = 45) -> CommandResult:
    return run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "ConnectTimeout=5",
            "-o",
            "StrictHostKeyChecking=accept-new",
            f"{user}@{host}",
            "bash",
            "-s",
        ],
        input_text=script,
        timeout_sec=timeout_sec,
    )


def md_code(text: str, lang: str = "text") -> str:
    return f"```{lang}\n{text.rstrip()}\n```\n"


def write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


REMOTE_SCRIPT = r"""
set -euo pipefail

section() { echo; echo "===== $1 ====="; }

section "identity"
hostnamectl --static 2>/dev/null || hostname
cat /etc/os-release 2>/dev/null || true
uname -a 2>/dev/null || true

section "network"
ip -br addr 2>/dev/null || true
ip route 2>/dev/null || true
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION dev status 2>/dev/null || true
nmcli -t -f NAME,TYPE,DEVICE con show --active 2>/dev/null || true

section "time"
timedatectl status 2>/dev/null || true
command -v chronyc >/dev/null 2>&1 && chronyc tracking 2>/dev/null || true
timedatectl show -p NTPSynchronized --value 2>/dev/null || true

section "dns"
resolvectl status 2>/dev/null | sed -n '1,120p' || true

section "services"
systemctl is-active ssh 2>/dev/null || true
systemctl is-enabled ssh 2>/dev/null || true
systemctl is-active NetworkManager 2>/dev/null || true
systemctl is-active nftables 2>/dev/null || true
systemctl is-active systemd-resolved 2>/dev/null || true
systemctl is-active chrony 2>/dev/null || true
systemctl is-active systemd-timesyncd 2>/dev/null || true

section "ports"
ss -tulpen 2>/dev/null | sed -n '1,200p' || true

section "security"
sudo -n true && echo "sudo_nopass=yes" || echo "sudo_nopass=no"

section "nftables"
sudo -n true && sudo nft list ruleset 2>/dev/null | sed -n '1,220p' || true
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate inventory markdown for OPi nodes via SSH.")
    parser.add_argument("--user", default="orangepi", help="SSH user (default: orangepi)")
    parser.add_argument("--out-dir", default="Docs/auto/inventory", help="Output dir (default: Docs/auto/inventory)")
    parser.add_argument("hosts", nargs="+", help="Hosts/IPs to inventory")
    args = parser.parse_args()

    timestamp = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    out_dir = Path(args.out_dir)

    index_lines: list[str] = [
        "# Inventory (generated)\n",
        f"- Timestamp (UTC): `{timestamp}`\n",
        "\n## Hosts\n",
    ]

    for host in args.hosts:
        result = ssh(host, args.user, REMOTE_SCRIPT)
        safe_host = host.replace(":", "_")
        out_file = out_dir / f"{safe_host}.md"

        header = [
            f"# Inventory — `{args.user}@{host}`\n",
            f"- Timestamp (UTC): `{timestamp}`\n",
            f"- SSH command: `{shlex.join(['ssh', f'{args.user}@{host}'])}`\n\n",
        ]

        body = []
        if result.returncode != 0:
            body.append("## Status\n")
            body.append(f"- WARN: ssh return code `{result.returncode}`\n\n")
        if result.stderr.strip():
            body.append("## SSH stderr\n")
            body.append(md_code(result.stderr))
        body.append("## Raw\n")
        body.append(md_code(result.stdout or "_no output_"))

        write(out_file, "".join(header + body))
        index_lines.append(f"- `{out_file.as_posix()}`\n")

    write(out_dir / "INDEX.md", "".join(index_lines))
    print(f"Wrote: {out_dir/'INDEX.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
