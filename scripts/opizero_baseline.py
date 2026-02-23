#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import ipaddress
import os
import re
import shlex
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


EXPECTED_LAN = ipaddress.ip_network("192.168.10.0/24")
EXPECTED_CENTRAL_IP_CIDR = "192.168.10.1/24"
EXPECTED_CENTRAL_HOSTNAME = "central-gw"
EXPECTED_CENTRAL_IFACE = "end0"
EXPECTED_CENTRAL_NM_PROFILE = "opizero3-static"


@dataclass(frozen=True)
class CommandResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str


def run(cmd: list[str], *, timeout_sec: int = 20, input_text: str | None = None) -> CommandResult:
    proc = subprocess.run(
        cmd,
        input=input_text,
        text=True,
        capture_output=True,
        timeout=timeout_sec,
        check=False,
    )
    return CommandResult(cmd=cmd, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def run_shell(cmd: str, *, timeout_sec: int = 20) -> CommandResult:
    return run(["bash", "-lc", cmd], timeout_sec=timeout_sec)


def ssh(host: str, user: str, remote_script: str, *, timeout_sec: int = 25) -> CommandResult:
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
        input_text=remote_script,
        timeout_sec=timeout_sec,
    )


def detect_local_ethernet_iface(preferred: str | None) -> str:
    if preferred:
        return preferred

    result = run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE", "dev", "status"])
    if result.returncode != 0:
        raise RuntimeError(f"nmcli failed: {result.stderr.strip()}")

    for line in result.stdout.splitlines():
        # DEVICE:TYPE:STATE
        parts = line.strip().split(":")
        if len(parts) != 3:
            continue
        device, device_type, state = parts
        if device_type == "ethernet" and state == "connected":
            return device

    raise RuntimeError("No connected ethernet interface detected. Pass --pc-iface explicitly.")


def parse_ipv4_cidrs(ip_addr_output: str) -> list[str]:
    # matches: inet 192.168.10.2/24
    cidrs: list[str] = []
    for line in ip_addr_output.splitlines():
        m = re.search(r"\binet\s+(\d+\.\d+\.\d+\.\d+/\d+)\b", line)
        if m:
            cidrs.append(m.group(1))
    return cidrs


def in_expected_lan(cidr: str) -> bool:
    try:
        interface = ipaddress.ip_interface(cidr)
    except ValueError:
        return False
    return interface.ip in EXPECTED_LAN


def markdown_code_block(text: str, lang: str = "") -> str:
    fence = "```"
    return f"{fence}{lang}\n{text.rstrip()}\n{fence}\n"


def format_cmd(cmd: list[str]) -> str:
    return " ".join(shlex.quote(c) for c in cmd)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Capture and document baseline configuration for PC + Orange Pi.")
    parser.add_argument("--host", default="192.168.10.1", help="Central host/IP (default: 192.168.10.1)")
    parser.add_argument("--user", default="orangepi", help="SSH user (default: orangepi)")
    parser.add_argument("--pc-iface", default=None, help="PC ethernet interface (auto-detect if omitted)")
    parser.add_argument(
        "--out-dir",
        default="Docs/auto",
        help="Output directory for generated Markdown (default: Docs/auto)",
    )
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    timestamp = dt.datetime.now(dt.UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    pc_iface = detect_local_ethernet_iface(args.pc_iface)

    local_nm = run(["nmcli", "-t", "-f", "DEVICE,TYPE,STATE,CONNECTION", "dev", "status"])
    local_ip = run(["ip", "-4", "addr", "show", "dev", pc_iface])
    local_route = run(["ip", "route", "show", "dev", pc_iface])

    local_cidrs = parse_ipv4_cidrs(local_ip.stdout)
    local_has_lan = any(in_expected_lan(c) for c in local_cidrs)
    local_has_legacy = any(ipaddress.ip_interface(c).ip in ipaddress.ip_network("192.168.50.0/24") for c in local_cidrs)

    remote_script = r"""
set +e
echo '=== hostname ==='
hostnamectl --static 2>/dev/null || hostname
echo '=== os-release ==='
cat /etc/os-release 2>/dev/null || true
echo '=== kernel ==='
uname -a 2>/dev/null || true
echo '=== ip_br_addr ==='
ip -br addr 2>/dev/null || true
echo '=== ip_route ==='
ip route 2>/dev/null || true
echo '=== nmcli_dev_status ==='
nmcli -t -f DEVICE,TYPE,STATE,CONNECTION dev status 2>/dev/null || true
echo '=== nmcli_active ==='
nmcli -t -f NAME,TYPE,DEVICE con show --active 2>/dev/null || true
echo '=== resolved_status ==='
resolvectl status 2>/dev/null || true
echo '=== timedatectl ==='
timedatectl status 2>/dev/null || true
echo '=== chrony_tracking ==='
command -v chronyc >/dev/null 2>&1 && chronyc tracking 2>/dev/null || echo 'chronyc not available'
echo '=== nftables_conf ==='
sed -n '1,200p' /etc/nftables.conf 2>/dev/null || true
echo '=== ssh_listen ==='
ss -tlnp 2>/dev/null | grep -E '(:22\\s|:22$)' || true
echo '=== ports ==='
ss -tulpen 2>/dev/null || true
"""

    remote = ssh(args.host, args.user, remote_script, timeout_sec=30)

    # Extract a few key fields from remote stdout
    remote_hostname = ""
    remote_has_expected_ip = False
    remote_nm_has_profile = False
    remote_time_synced = None  # None if unknown
    remote_chrony_synced = None  # None if unknown
    remote_chrony_refid = None  # None if unknown
    remote_chrony_stratum = None  # None if unknown
    remote_chrony_leap_status = None  # None if unknown
    remote_chrony_is_local_clock = False
    remote_ports: list[str] = []

    sections: dict[str, str] = {}
    current_key: str | None = None
    buf: list[str] = []
    for line in remote.stdout.splitlines():
        m = re.match(r"^===\s+([a-z0-9_]+)\s+===$", line.strip())
        if m:
            if current_key is not None:
                sections[current_key] = "\n".join(buf).rstrip() + "\n"
            current_key = m.group(1)
            buf = []
            continue
        buf.append(line)
    if current_key is not None:
        sections[current_key] = "\n".join(buf).rstrip() + "\n"

    if "hostname" in sections:
        remote_hostname = sections["hostname"].strip().splitlines()[0] if sections["hostname"].strip() else ""

    if "ip_br_addr" in sections:
        remote_has_expected_ip = EXPECTED_CENTRAL_IP_CIDR in sections["ip_br_addr"]

    if "nmcli_active" in sections:
        remote_nm_has_profile = f"{EXPECTED_CENTRAL_NM_PROFILE}:802-3-ethernet:{EXPECTED_CENTRAL_IFACE}" in sections[
            "nmcli_active"
        ]

    if "timedatectl" in sections:
        m = re.search(r"System clock synchronized:\s+(yes|no)", sections["timedatectl"])
        if m:
            remote_time_synced = m.group(1) == "yes"

    if "chrony_tracking" in sections:
        chrony_tracking = sections["chrony_tracking"]
        m = re.search(r"^Reference ID\s*:\s*([0-9A-Fa-f]+)\b", chrony_tracking, flags=re.MULTILINE)
        if m:
            remote_chrony_refid = m.group(1).upper()
        m = re.search(r"^Stratum\s*:\s*(\d+)\b", chrony_tracking, flags=re.MULTILINE)
        if m:
            remote_chrony_stratum = int(m.group(1))
        m = re.search(r"^Leap status\s*:\s*(.+)$", chrony_tracking, flags=re.MULTILINE)
        if m:
            remote_chrony_leap_status = m.group(1).strip()
            remote_chrony_synced = remote_chrony_leap_status.lower() != "not synchronised"
        remote_chrony_is_local_clock = remote_chrony_refid == "7F7F0101"

    if "ports" in sections:
        remote_ports = [ln.strip() for ln in sections["ports"].splitlines() if ln.strip().startswith(("tcp", "udp"))]

    summary_lines: list[str] = []
    def add_check(label: str, ok: bool, ok_details: str = "", warn_details: str = "") -> None:
        status = "OK" if ok else "WARN"
        details = ok_details if ok else warn_details
        suffix = f" — {details}" if details else ""
        summary_lines.append(f"- {status}: {label}{suffix}")

    add_check(
        "PC ethernet has 192.168.10.0/24 address",
        local_has_lan,
        ok_details=f"iface={pc_iface} cidrs={', '.join(local_cidrs) or 'none'}",
        warn_details=f"iface={pc_iface} cidrs={', '.join(local_cidrs) or 'none'}",
    )
    add_check(
        "PC ethernet has no legacy 192.168.50.0/24 address",
        not local_has_legacy,
        warn_details="remove extra address if present",
    )
    add_check(
        "Central hostname is central-gw",
        remote_hostname == EXPECTED_CENTRAL_HOSTNAME,
        ok_details=f"got={remote_hostname!r}",
        warn_details=f"got={remote_hostname!r}",
    )
    add_check(
        "Central has 192.168.10.1/24 on end0",
        remote_has_expected_ip,
        warn_details="expected 192.168.10.1/24 on end0",
    )
    add_check(
        "Central NM profile opizero3-static active on end0",
        remote_nm_has_profile,
        warn_details="expected opizero3-static:...:end0",
    )
    if remote_time_synced is not None:
        add_check(
            "Central system time synchronized",
            remote_time_synced,
            warn_details=(
                "chrony is running in local-clock mode (no GPS/Internet); OK for LAN consistency, not absolute time"
                if remote_chrony_is_local_clock
                else "follow Plan/3 if not synchronized"
            ),
        )
    else:
        add_check(
            "Central system time synchronized",
            False,
            warn_details="timedatectl not available",
        )

    if remote_chrony_synced is not None:
        chrony_details = (
            f"leap={remote_chrony_leap_status!r} stratum={remote_chrony_stratum} refid={remote_chrony_refid}"
            + (" (local-clock)" if remote_chrony_is_local_clock else "")
        )
        add_check(
            "Central NTP service (chrony) has valid reference",
            remote_chrony_synced,
            ok_details=chrony_details,
            warn_details=chrony_details,
        )

    if remote.returncode != 0:
        add_check(
            "SSH baseline capture succeeded",
            False,
            warn_details=f"ssh rc={remote.returncode}",
        )
    else:
        add_check("SSH baseline capture succeeded", True)

    summary = "\n".join(summary_lines) + "\n"

    pc_md = [
        f"# Baseline — PC (generated)\n",
        f"- Timestamp (UTC): `{timestamp}`\n",
        f"- Interface: `{pc_iface}`\n\n",
        "## Summary\n",
        summary,
        "\n## Raw\n",
        f"### `nmcli dev status`\n{markdown_code_block(local_nm.stdout, 'text')}",
        f"### `ip -4 addr show dev {pc_iface}`\n{markdown_code_block(local_ip.stdout, 'text')}",
        f"### `ip route show dev {pc_iface}`\n{markdown_code_block(local_route.stdout, 'text')}",
    ]

    central_md = [
        f"# Baseline — central-gw (generated)\n",
        f"- Timestamp (UTC): `{timestamp}`\n",
        f"- Target: `{args.user}@{args.host}`\n\n",
        "## Summary\n",
        summary,
        "\n## Raw (remote)\n",
    ]
    if remote.stderr.strip():
        central_md.append(f"### SSH stderr\n{markdown_code_block(remote.stderr, 'text')}")
    if remote.stdout.strip():
        central_md.append(markdown_code_block(remote.stdout, "text"))
    else:
        central_md.append("_No remote output captured._\n")

    # Light hints
    hints: list[str] = []
    if local_has_legacy:
        hints.append(f"- PC: remove `192.168.50.0/24` from `{pc_iface}` (keep only `192.168.10.x/24`).")
    if remote_time_synced is False:
        if remote_chrony_is_local_clock:
            hints.append(
                "- Central: running in **local-clock** NTP mode (no GPS/Internet); set correct time manually when commissioning and add GPS/Internet later for absolute timestamps (`Docs/настройка ПО/План/3. Синхронизация времени (критично для данных).md`)."
            )
        else:
            hints.append(
                "- Central: time is not synchronized yet; continue with `Docs/настройка ПО/План/3. Синхронизация времени (критично для данных).md`."
            )
    if remote_chrony_synced is False:
        hints.append(
            "- Central: chrony has no valid reference; edge nodes will not get consistent timestamps until this is fixed."
        )
    risky_ports: list[str] = []
    for port in ("111", "5201"):
        if any(re.search(rf":{port}\b", line) for line in remote_ports):
            risky_ports.append(port)
    if risky_ports:
        hints.append(
            "- Central: review listening ports (`"
            + "`, `".join(risky_ports)
            + "`) and disable/close if not needed in prod."
        )

    summary_md = [
        "# Baseline summary (generated)\n",
        f"- Timestamp (UTC): `{timestamp}`\n",
        f"- Central: `{args.user}@{args.host}`\n",
        f"- PC interface: `{pc_iface}`\n\n",
        "## Checks\n",
        summary,
        "\n## Next actions\n",
        ("\n".join(hints) + "\n") if hints else "- No actions detected.\n",
        "\n## Files\n",
        f"- `Docs/auto/baseline-pc.md`\n",
        f"- `Docs/auto/baseline-central-gw.md`\n",
    ]

    write_text(out_dir / "baseline-pc.md", "".join(pc_md))
    write_text(out_dir / "baseline-central-gw.md", "".join(central_md))
    write_text(out_dir / "baseline-summary.md", "".join(summary_md))

    print(f"Wrote: {out_dir/'baseline-summary.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
