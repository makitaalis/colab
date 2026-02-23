#!/usr/bin/env python3
from __future__ import annotations

import argparse
import dataclasses
import datetime as dt
import json
import shlex
import subprocess
import sys
from pathlib import Path

DEFAULT_REGISTRY = Path("fleet/registry.csv")
DEFAULT_BUNDLE_ROOT = Path("fleet/out")
DEFAULT_REPORT_DIR = Path("Docs/auto/commissioning")


@dataclasses.dataclass(frozen=True)
class CommandResult:
    cmd: list[str]
    returncode: int
    stdout: str
    stderr: str


@dataclasses.dataclass
class CheckItem:
    level: str
    name: str
    details: str


@dataclasses.dataclass(frozen=True)
class Context:
    system_id: str
    central_ip: str
    edge_ips: list[str]
    opi_user: str
    server_host: str
    server_user: str
    vehicle_id: str
    wg_ip: str
    smoke: bool
    repo_root: Path
    out_dir: Path


def run(cmd: list[str], *, timeout_sec: int = 30, input_text: str | None = None) -> CommandResult:
    proc = subprocess.run(
        cmd,
        text=True,
        input=input_text,
        capture_output=True,
        timeout=timeout_sec,
        check=False,
    )
    return CommandResult(cmd=cmd, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def ssh_cmd(host: str, user: str, remote_cmd: str, *, timeout_sec: int = 20) -> CommandResult:
    return run(
        [
            "ssh",
            "-o",
            "BatchMode=yes",
            "-o",
            "StrictHostKeyChecking=accept-new",
            "-o",
            "ConnectTimeout=8",
            f"{user}@{host}",
            remote_cmd,
        ],
        timeout_sec=timeout_sec,
    )


def ensure_bundle(repo_root: Path, registry: Path, bundle_root: Path, system_id: str) -> Path:
    bundle_dir = bundle_root / system_id
    if bundle_dir.exists():
        return bundle_dir
    result = run(
        [
            sys.executable,
            str(repo_root / "scripts/fleet_registry.py"),
            "--registry",
            str(registry),
            "bundle",
            "--system-id",
            system_id,
            "--out-root",
            str(bundle_root),
        ],
        timeout_sec=40,
    )
    if result.returncode != 0:
        raise SystemExit(f"Cannot generate bundle:\n{result.stdout}{result.stderr}")
    return bundle_dir


def read_env_file(path: Path) -> dict[str, str]:
    env: dict[str, str] = {}
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env[key.strip()] = value.strip()
    return env


def normalize_stop_mode(value: str | None) -> str:
    mode = str(value or "").strip().lower()
    if mode in {"manual", "timer"}:
        return mode
    return "unknown"


def ping_ok(ip: str) -> CommandResult:
    return run(["ping", "-c", "1", "-W", "2", ip], timeout_sec=5)


def add(items: list[CheckItem], level: str, name: str, details: str) -> None:
    items.append(CheckItem(level=level, name=name, details=details))


def service_state(host: str, user: str, unit: str) -> str:
    result = ssh_cmd(host, user, f"systemctl is-active {shlex.quote(unit)} 2>/dev/null || true")
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def service_enabled(host: str, user: str, unit: str) -> str:
    result = ssh_cmd(host, user, f"systemctl is-enabled {shlex.quote(unit)} 2>/dev/null || true")
    if result.returncode != 0:
        return "unknown"
    return result.stdout.strip() or "unknown"


def fetch_text(host: str, user: str, remote_cmd: str) -> str:
    result = ssh_cmd(host, user, remote_cmd)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def run_smoke(ctx: Context) -> CommandResult:
    cmd = [
        str(ctx.repo_root / "scripts/mvp_e2e_smoke.sh"),
        "--central-ip",
        ctx.central_ip,
        "--server-host",
        ctx.server_host,
    ]
    if len(ctx.edge_ips) >= 1:
        cmd.extend(["--door1-ip", ctx.edge_ips[0]])
    if len(ctx.edge_ips) >= 2:
        cmd.extend(["--door2-ip", ctx.edge_ips[1]])
    return run(cmd, timeout_sec=240)


def fetch_fleet(ctx: Context) -> tuple[dict[str, object] | None, str]:
    remote = (
        "token=$(grep -m1 '^ADMIN_API_KEYS=' /opt/passengers-backend/.env | cut -d= -f2 | tr -d '\\r' | cut -d, -f1); "
        "if [ -z \"$token\" ]; then "
        "token=$(grep -m1 '^PASSENGERS_API_KEYS=' /opt/passengers-backend/.env | cut -d= -f2 | tr -d '\\r' | cut -d, -f1); "
        "fi; "
        "curl -sS -H \"Authorization: Bearer ${token}\" http://10.66.0.1/api/admin/fleet/centrals"
    )
    result = ssh_cmd(ctx.server_host, ctx.server_user, remote, timeout_sec=20)
    if result.returncode != 0:
        return None, result.stderr.strip() or result.stdout.strip()
    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        return None, f"bad_json: {exc}"
    if not isinstance(payload, dict):
        return None, "bad_json_root"
    return payload, ""


def fetch_wg_peer(ctx: Context) -> tuple[dict[str, str] | None, str]:
    remote = (
        "sudo wg show wg0 dump | awk -F'\\t' "
        f" -v ip='{ctx.wg_ip}/32' 'NR>1 && index($4, ip)>0 {{print $1\"\\t\"$5\"\\t\"$3\"\\t\"$4; exit}}'"
    )
    result = ssh_cmd(ctx.server_host, ctx.server_user, remote, timeout_sec=15)
    if result.returncode != 0:
        return None, result.stderr.strip() or result.stdout.strip()
    line = result.stdout.strip()
    if not line:
        return None, "peer_not_found"
    parts = line.split("\t")
    if len(parts) < 4:
        return None, "peer_bad_dump"
    return {
        "public_key": parts[0],
        "latest_handshake_epoch": parts[1],
        "endpoint": parts[2],
        "allowed_ips": parts[3],
    }, ""


def render_report(
    *,
    ctx: Context,
    checks: list[CheckItem],
    fleet_entry: dict[str, object] | None,
    fleet_raw: dict[str, object] | None,
    wg_peer: dict[str, str] | None,
    smoke_result: CommandResult | None,
    written_at: dt.datetime,
) -> str:
    ts_iso = written_at.replace(microsecond=0).isoformat().replace("+00:00", "Z")
    ok_count = sum(1 for c in checks if c.level == "ok")
    warn_count = sum(1 for c in checks if c.level == "warn")
    fail_count = sum(1 for c in checks if c.level == "fail")
    verdict = "PASS" if fail_count == 0 else "FAIL"

    lines: list[str] = [
        f"# Commissioning report — `{ctx.system_id}`",
        "",
        f"- Timestamp (UTC): `{ts_iso}`",
        f"- Verdict: **{verdict}**",
        f"- Checks: ok={ok_count}, warn={warn_count}, fail={fail_count}",
        "",
        "## Inputs",
        f"- central: `{ctx.opi_user}@{ctx.central_ip}`",
        f"- edges: `{', '.join(ctx.edge_ips)}`",
        f"- server: `{ctx.server_user}@{ctx.server_host}`",
        f"- vehicle_id: `{ctx.vehicle_id}`",
        f"- wg_ip: `{ctx.wg_ip}`",
        "",
        "## Checks",
    ]

    for item in checks:
        badge = item.level.upper()
        lines.append(f"- {badge}: {item.name} — {item.details}")

    lines.extend(["", "## Fleet API"])
    if fleet_entry is None:
        lines.append("- not_available")
    else:
        health = fleet_entry.get("health") if isinstance(fleet_entry.get("health"), dict) else {}
        severity = str(health.get("severity") or "unknown")
        alerts_total = int(health.get("alerts_total") or 0)
        lines.append(f"- central_id: `{fleet_entry.get('central_id')}`")
        lines.append(f"- severity: `{severity}` alerts_total={alerts_total}")
        queue = fleet_entry.get("queue") if isinstance(fleet_entry.get("queue"), dict) else {}
        if queue:
            lines.append(
                f"- queue: pending={queue.get('pending_batches')} sent={queue.get('sent_batches')} stop_mode={queue.get('stop_mode')}"
            )

    lines.extend(["", "## WireGuard"])
    if wg_peer is None:
        lines.append("- peer_not_found")
    else:
        handshake_epoch = str(wg_peer.get("latest_handshake_epoch") or "0")
        lines.append(f"- allowed_ips: `{wg_peer.get('allowed_ips')}`")
        lines.append(f"- endpoint: `{wg_peer.get('endpoint')}`")
        lines.append(f"- latest_handshake_epoch: `{handshake_epoch}`")

    lines.extend(["", "## Smoke"])
    if smoke_result is None:
        lines.append("- skipped")
    else:
        lines.append(f"- exit_code: `{smoke_result.returncode}`")
        lines.append("```text")
        lines.append((smoke_result.stdout or "").strip() or "_no stdout_")
        lines.append("```")
        if smoke_result.stderr.strip():
            lines.append("```text")
            lines.append(smoke_result.stderr.strip())
            lines.append("```")

    if fleet_raw is not None:
        lines.extend(["", "## Fleet Raw", "```json", json.dumps(fleet_raw, ensure_ascii=False, indent=2), "```"])

    lines.append("")
    return "\n".join(lines)


def write_report(out_dir: Path, system_id: str, content: str, ts: dt.datetime, repo_root: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = ts.strftime("%Y%m%d-%H%M%SZ")
    report = out_dir / f"{system_id}-{stamp}.md"
    report.write_text(content, encoding="utf-8")

    reports = sorted((p for p in out_dir.glob("*.md") if p.name != "INDEX.md"), key=lambda p: p.name, reverse=True)
    index_lines = ["# Commissioning reports", ""]
    for path in reports:
        try:
            rel = path.relative_to(repo_root).as_posix()
        except ValueError:
            rel = path.as_posix()
        index_lines.append(f"- `{rel}`")
    index_lines.append("")
    (out_dir / "INDEX.md").write_text("\n".join(index_lines), encoding="utf-8")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Commissioning checks + report for one fleet system.")
    parser.add_argument("--system-id", required=True, help="System ID from fleet registry, e.g. sys-0001")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to fleet registry CSV")
    parser.add_argument("--bundle-root", type=Path, default=DEFAULT_BUNDLE_ROOT, help="Path to fleet bundle root")
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_REPORT_DIR, help="Report output dir")
    parser.add_argument("--smoke", action="store_true", help="Run scripts/mvp_e2e_smoke.sh and include output")
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    registry = args.registry if args.registry.is_absolute() else (repo_root / args.registry)
    bundle_root = args.bundle_root if args.bundle_root.is_absolute() else (repo_root / args.bundle_root)
    out_dir = args.out_dir if args.out_dir.is_absolute() else (repo_root / args.out_dir)

    bundle_dir = ensure_bundle(repo_root, registry, bundle_root, args.system_id)
    fleet_env_path = bundle_dir / "fleet.env"
    if not fleet_env_path.exists():
        raise SystemExit(f"Missing fleet.env: {fleet_env_path}")
    env = read_env_file(fleet_env_path)

    central_ip = env.get("CENTRAL_IP", "").strip()
    edge_ips = [ip.strip() for ip in env.get("EDGE_IPS_CSV", "").split(",") if ip.strip()]
    opi_user = env.get("OPI_USER", "orangepi").strip() or "orangepi"
    server_host = env.get("SERVER_HOST", "").strip()
    server_user = env.get("SERVER_SSH_USER", "alis").strip() or "alis"
    vehicle_id = env.get("VEHICLE_ID", "").strip() or "unknown"
    wg_ip = env.get("WG_IP", "").strip()

    if not central_ip:
        raise SystemExit(f"CENTRAL_IP missing in {fleet_env_path}")
    if not edge_ips:
        raise SystemExit(f"EDGE_IPS_CSV missing in {fleet_env_path}")
    if not server_host:
        raise SystemExit(f"SERVER_HOST missing in {fleet_env_path}")
    if not wg_ip:
        raise SystemExit(f"WG_IP missing in {fleet_env_path}")

    ctx = Context(
        system_id=args.system_id,
        central_ip=central_ip,
        edge_ips=edge_ips,
        opi_user=opi_user,
        server_host=server_host,
        server_user=server_user,
        vehicle_id=vehicle_id,
        wg_ip=wg_ip,
        smoke=args.smoke,
        repo_root=repo_root,
        out_dir=out_dir,
    )

    checks: list[CheckItem] = []

    host_map: list[tuple[str, str]] = [("central-gw", ctx.central_ip)]
    for idx, ip in enumerate(ctx.edge_ips):
        expected = "door-1" if idx == 0 else "door-2" if idx == 1 else f"edge-{idx+1}"
        host_map.append((expected, ip))

    for expected_host, ip in host_map:
        ping = ping_ok(ip)
        if ping.returncode == 0:
            add(checks, "ok", f"{ip} ping", "reachable")
        else:
            add(checks, "fail", f"{ip} ping", "unreachable")
            continue

        probe = ssh_cmd(ip, ctx.opi_user, "hostname")
        if probe.returncode != 0:
            add(checks, "fail", f"{ip} ssh", "cannot connect via ssh")
            continue
        actual_host = probe.stdout.strip() or "unknown"
        if actual_host == expected_host:
            add(checks, "ok", f"{ip} hostname", actual_host)
        else:
            add(checks, "warn", f"{ip} hostname", f"expected={expected_host} got={actual_host}")

        system_state = fetch_text(ip, ctx.opi_user, "systemctl is-system-running 2>/dev/null || true")
        if system_state == "running":
            add(checks, "ok", f"{ip} system state", "running")
        else:
            add(checks, "fail", f"{ip} system state", system_state or "unknown")

    # Central services + stop mode.
    central_stop_mode = normalize_stop_mode(
        fetch_text(
            ctx.central_ip,
            ctx.opi_user,
            "sudo sed -n 's/^STOP_MODE=//p' /etc/passengers/passengers.env | head -n1",
        )
    )
    if central_stop_mode == "unknown":
        add(checks, "warn", "central stop_mode", "missing or invalid in /etc/passengers/passengers.env")
    else:
        add(checks, "ok", "central stop_mode", central_stop_mode)

    for unit in ("passengers-collector.service", "passengers-central-uplink.service", "passengers-central-heartbeat.timer"):
        state = service_state(ctx.central_ip, ctx.opi_user, unit)
        if state == "active":
            add(checks, "ok", f"central {unit}", state)
        else:
            add(checks, "fail", f"central {unit}", state)

    for unit in ("wg-quick@wg0.service", "chrony.service"):
        state = service_state(ctx.central_ip, ctx.opi_user, unit)
        if state == "active":
            add(checks, "ok", f"central {unit}", state)
        else:
            add(checks, "warn", f"central {unit}", state)

    flush_active = service_state(ctx.central_ip, ctx.opi_user, "passengers-central-flush.timer")
    flush_enabled = service_enabled(ctx.central_ip, ctx.opi_user, "passengers-central-flush.timer")
    if central_stop_mode == "timer":
        if flush_active == "active":
            add(checks, "ok", "central passengers-central-flush.timer", f"active ({flush_enabled})")
        else:
            add(checks, "fail", "central passengers-central-flush.timer", f"{flush_active} ({flush_enabled})")
    elif central_stop_mode == "manual":
        if flush_active in {"inactive", "failed", "unknown"}:
            add(checks, "ok", "central passengers-central-flush.timer", f"{flush_active} ({flush_enabled}) in manual mode")
        else:
            add(checks, "warn", "central passengers-central-flush.timer", f"{flush_active} ({flush_enabled}) in manual mode")
    else:
        add(checks, "warn", "central passengers-central-flush.timer", f"{flush_active} ({flush_enabled})")

    # Edge services.
    for idx, ip in enumerate(ctx.edge_ips):
        label = "door-1" if idx == 0 else "door-2" if idx == 1 else f"edge-{idx+1}"
        for unit in ("passengers-edge-sender.service", "chrony.service"):
            state = service_state(ip, ctx.opi_user, unit)
            if state == "active":
                add(checks, "ok", f"{label} {unit}", state)
            else:
                add(checks, "fail", f"{label} {unit}", state)

    smoke_result: CommandResult | None = None
    if ctx.smoke:
        smoke_result = run_smoke(ctx)
        if smoke_result.returncode == 0:
            add(checks, "ok", "smoke", "passed")
        else:
            add(checks, "fail", "smoke", f"failed rc={smoke_result.returncode}")

    fleet_payload, fleet_error = fetch_fleet(ctx)
    fleet_entry: dict[str, object] | None = None
    if fleet_payload is None:
        add(checks, "warn", "fleet api", fleet_error or "unreachable")
    else:
        centrals = fleet_payload.get("centrals")
        if not isinstance(centrals, list):
            add(checks, "warn", "fleet api", "centrals list missing")
        else:
            central_id = fetch_text(
                ctx.central_ip,
                ctx.opi_user,
                "sudo sed -n 's/^CENTRAL_ID=//p' /etc/passengers/passengers.env | head -n1",
            ) or ctx.system_id
            for item in centrals:
                if not isinstance(item, dict):
                    continue
                if str(item.get("central_id") or "") == central_id:
                    fleet_entry = item
                    break
            if fleet_entry is None:
                add(checks, "warn", "fleet api", f"central_id not found: {central_id}")
            else:
                health = fleet_entry.get("health") if isinstance(fleet_entry.get("health"), dict) else {}
                severity = str(health.get("severity") or "unknown")
                if severity == "bad":
                    add(checks, "fail", "fleet api severity", severity)
                elif severity == "warn":
                    add(checks, "warn", "fleet api severity", severity)
                else:
                    add(checks, "ok", "fleet api severity", severity)

    wg_peer, wg_error = fetch_wg_peer(ctx)
    if wg_peer is None:
        add(checks, "warn", "wireguard peer", wg_error or "unknown")
    else:
        try:
            handshake_epoch = int(wg_peer.get("latest_handshake_epoch") or "0")
        except ValueError:
            handshake_epoch = 0
        now_epoch = int(dt.datetime.now(dt.UTC).timestamp())
        if handshake_epoch <= 0:
            add(checks, "warn", "wireguard handshake", "no handshake yet")
        else:
            age = max(0, now_epoch - handshake_epoch)
            if age > 600:
                add(checks, "warn", "wireguard handshake", f"age={age}s")
            else:
                add(checks, "ok", "wireguard handshake", f"age={age}s")

    now = dt.datetime.now(dt.UTC)
    report = render_report(
        ctx=ctx,
        checks=checks,
        fleet_entry=fleet_entry,
        fleet_raw=fleet_payload,
        wg_peer=wg_peer,
        smoke_result=smoke_result,
        written_at=now,
    )
    report_path = write_report(ctx.out_dir, ctx.system_id, report, now, ctx.repo_root)
    fail_count = sum(1 for item in checks if item.level == "fail")
    warn_count = sum(1 for item in checks if item.level == "warn")

    print(f"Report: {report_path.as_posix()}")
    print(f"Summary: fail={fail_count} warn={warn_count} ok={len(checks) - fail_count - warn_count}")
    return 1 if fail_count > 0 else 0


if __name__ == "__main__":
    raise SystemExit(main())
