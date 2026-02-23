#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import datetime as dt
import subprocess
import sys
from pathlib import Path

DEFAULT_REGISTRY = Path("fleet/registry.csv")
DEFAULT_BUNDLE_ROOT = Path("fleet/out")
DEFAULT_REPORT_ROOT = Path("Docs/auto/fleet-rollout")


class RunResult:
    def __init__(self, cmd: list[str], returncode: int, stdout: str, stderr: str) -> None:
        self.cmd = cmd
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr

    @property
    def output(self) -> str:
        data = (self.stdout or "") + (self.stderr or "")
        return data.strip()


def run(cmd: list[str], *, timeout_sec: int = 90) -> RunResult:
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=timeout_sec)
    return RunResult(cmd=cmd, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)


def now_stamp() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M%SZ")


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_registry_ids(path: Path) -> set[str]:
    ids: set[str] = set()
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sid = str(row.get("system_id") or "").strip()
            if sid:
                ids.add(sid)
    return ids


def make_system_ids(*, single_ids: list[str], from_num: int | None, to_num: int | None) -> list[str]:
    if single_ids:
        out: list[str] = []
        seen: set[str] = set()
        for value in single_ids:
            sid = value.strip()
            if not sid or sid in seen:
                continue
            seen.add(sid)
            out.append(sid)
        return out
    if from_num is None or to_num is None:
        raise SystemExit("Use --system-id <id> or --from <n> --to <n>")
    if from_num < 1 or to_num < from_num:
        raise SystemExit("Invalid range: --from must be >=1 and --to >= --from")
    return [f"sys-{n:04d}" for n in range(from_num, to_num + 1)]


def required_template_checks(template_text: str) -> list[str]:
    required = [
        "CENTRAL_ID=",
        "STOP_MODE=manual",
        "STOP_FLUSH_INTERVAL_SEC=120",
        "CENTRAL_EVENTS_MAX_ROWS=300000",
        "CENTRAL_EVENTS_MAX_AGE_SEC=1209600",
        "CENTRAL_SENT_BATCHES_MAX_ROWS=50000",
        "CENTRAL_SENT_BATCHES_MAX_AGE_SEC=2592000",
        "CENTRAL_PENDING_BATCHES_MAX_ROWS=10000",
        "CENTRAL_PENDING_BATCHES_MAX_AGE_SEC=2592000",
        "CENTRAL_PENDING_BATCHES_DROP_AGE=0",
    ]
    missing: list[str] = []
    for key in required:
        if key not in template_text:
            missing.append(key)
    return missing


def required_commands_checks(commands_text: str) -> list[str]:
    required = [
        "fleet_api_keys.py ensure",
        "fleet_api_keys.py sync-server",
        "fleet_apply_wg_peer.py",
        "deploy_passengers_mvp.sh",
        "fleet_apply_central_env.py",
        "mvp_e2e_smoke.sh",
        "fleet_commission.py",
        "admin_panel_smoke_gate.sh",
    ]
    missing: list[str] = []
    for item in required:
        if item not in commands_text:
            missing.append(item)
    return missing


def render_report(
    *,
    system_id: str,
    validate_result: RunResult,
    bundle_result: RunResult,
    rollout_result: RunResult,
    check_lines: list[str],
    verdict: str,
) -> str:
    lines = [
        f"# Fleet rollout-check — {system_id}",
        "",
        f"- Timestamp (UTC): `{now_iso()}`",
        f"- Verdict: **{verdict}**",
        "- Scope: registry + bundle + orchestrator check (no hardware actions)",
        "",
        "## validate",
        "```text",
        validate_result.output or "_no output_",
        "```",
        "",
        "## bundle",
        "```text",
        bundle_result.output or "_no output_",
        "```",
        "",
        "## rollout-check",
        "```text",
        rollout_result.output or "_no output_",
        "```",
        "",
        "## bundle checks",
    ]
    for row in check_lines:
        lines.append(f"- {row}")
    lines.append("")
    return "\n".join(lines)


def update_index(report_root: Path, repo_root: Path) -> None:
    index = report_root / "INDEX.md"
    files = sorted(
        [p for p in report_root.glob("*.md") if p.name != "INDEX.md"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    lines = ["# Fleet rollout checks", ""]
    for file in files:
        try:
            rel = file.relative_to(repo_root).as_posix()
        except ValueError:
            rel = file.as_posix()
        lines.append(f"- `{rel}`")
    lines.append("")
    index.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate rollout-check reports for fleet systems.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Registry CSV path")
    parser.add_argument("--bundle-root", type=Path, default=DEFAULT_BUNDLE_ROOT, help="Bundle root path")
    parser.add_argument("--report-root", type=Path, default=DEFAULT_REPORT_ROOT, help="Report output root")
    parser.add_argument("--system-id", action="append", default=[], help="System ID, can be repeated")
    parser.add_argument("--from", dest="from_num", type=int, default=None, help="Range start number")
    parser.add_argument("--to", dest="to_num", type=int, default=None, help="Range end number")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    registry = args.registry if args.registry.is_absolute() else (repo_root / args.registry)
    bundle_root = args.bundle_root if args.bundle_root.is_absolute() else (repo_root / args.bundle_root)
    report_root = args.report_root if args.report_root.is_absolute() else (repo_root / args.report_root)

    if not registry.exists():
        raise SystemExit(f"Registry not found: {registry}")

    system_ids = make_system_ids(single_ids=args.system_id, from_num=args.from_num, to_num=args.to_num)
    known_ids = parse_registry_ids(registry)
    unknown = [sid for sid in system_ids if sid not in known_ids]
    if unknown:
        raise SystemExit(f"System IDs missing in registry: {', '.join(unknown)}")

    report_root.mkdir(parents=True, exist_ok=True)
    validate_result = run([sys.executable, str(repo_root / "scripts/fleet_registry.py"), "--registry", str(registry), "validate"])
    if validate_result.returncode != 0:
        raise SystemExit(f"Registry validation failed:\n{validate_result.output}")

    failed = 0
    stamp = now_stamp()

    for system_id in system_ids:
        bundle_result = run(
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
            ]
        )
        rollout_result = run(
            [
                str(repo_root / "scripts/fleet_rollout.sh"),
                "--system-id",
                system_id,
                "--registry",
                str(registry),
                "--bundle-root",
                str(bundle_root),
            ]
        )

        check_lines: list[str] = []
        verdict = "PASS"

        bundle_dir = bundle_root / system_id
        fleet_env = bundle_dir / "fleet.env"
        server_peer = bundle_dir / "wireguard/server-peer.conf"
        central_env_tmpl = bundle_dir / "passengers/central-passengers.env.template"
        commands_md = bundle_dir / "commands.md"

        for path in (fleet_env, server_peer, central_env_tmpl, commands_md):
            if path.exists():
                check_lines.append(f"OK: exists `{path.as_posix()}`")
            else:
                check_lines.append(f"FAIL: missing `{path.as_posix()}`")
                verdict = "FAIL"

        if central_env_tmpl.exists():
            text = central_env_tmpl.read_text(encoding="utf-8", errors="replace")
            missing = required_template_checks(text)
            if missing:
                verdict = "FAIL"
                check_lines.append(f"FAIL: missing central template keys: {', '.join(missing)}")
            else:
                check_lines.append("OK: central template includes offline profile keys")
            if f"CENTRAL_ID={system_id}" in text:
                check_lines.append(f"OK: CENTRAL_ID matches `{system_id}`")
            else:
                verdict = "FAIL"
                check_lines.append(f"FAIL: CENTRAL_ID is not `{system_id}`")

        if commands_md.exists():
            cmd_text = commands_md.read_text(encoding="utf-8", errors="replace")
            missing = required_commands_checks(cmd_text)
            if missing:
                verdict = "FAIL"
                check_lines.append(f"FAIL: commands.md missing steps: {', '.join(missing)}")
            else:
                check_lines.append("OK: commands.md includes full e2e path")

        if bundle_result.returncode != 0:
            verdict = "FAIL"
            check_lines.append(f"FAIL: bundle command rc={bundle_result.returncode}")
        else:
            check_lines.append("OK: bundle command rc=0")

        if rollout_result.returncode != 0:
            verdict = "FAIL"
            check_lines.append(f"FAIL: rollout-check command rc={rollout_result.returncode}")
        else:
            check_lines.append("OK: rollout-check command rc=0")

        report_text = render_report(
            system_id=system_id,
            validate_result=validate_result,
            bundle_result=bundle_result,
            rollout_result=rollout_result,
            check_lines=check_lines,
            verdict=verdict,
        )
        report_path = report_root / f"{system_id}-rollout-check-{stamp}.md"
        report_path.write_text(report_text, encoding="utf-8")
        print(f"{system_id}: {verdict} -> {report_path.as_posix()}")
        if verdict != "PASS":
            failed += 1

    update_index(report_root, repo_root)
    if failed:
        print(f"Completed with failures: {failed}/{len(system_ids)}")
        return 2
    print(f"Completed: PASS ({len(system_ids)} systems)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
