#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import fleet_registry as fr

DEFAULT_REPORT_ROOT = Path("Docs/auto/fleet-scale")
DEFAULT_REGISTRY = Path("fleet/registry.csv")
WG_POOL = [f"10.66.0.{host}" for host in range(11, 255)]


def _now_utc_stamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%SZ")


def _extract_system_number(system_id: str) -> int | None:
    if not system_id.startswith("sys-"):
        return None
    suffix = system_id[4:]
    if not suffix.isdigit():
        return None
    return int(suffix)


def _next_system_number(entries: list[fr.SystemEntry]) -> int:
    max_num = 0
    for item in entries:
        num = _extract_system_number(item.system_id)
        if num is None:
            continue
        max_num = max(max_num, num)
    return max_num + 1


def _vehicle_id_for(index_num: int, used: set[str]) -> str:
    for k in range(index_num, index_num + 10000):
        candidate = f"bus-{k:03d}_AA{k:04d}BB"
        if candidate not in used:
            return candidate
    raise SystemExit("Unable to generate unique vehicle_id in 10k attempts")


def _next_wg_ip(used: set[str]) -> str:
    for ip in WG_POOL:
        if ip not in used:
            return ip
    raise SystemExit("No free WG IP left in 10.66.0.11-10.66.0.254 pool")


def _write_csv(path: Path, entries: list[fr.SystemEntry]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["system_id", "vehicle_id", "wg_ip", "server_endpoint", "status", "notes"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in entries:
            row = asdict(item)
            row.pop("line_no", None)
            writer.writerow(row)


def _update_index(report_root: Path) -> None:
    index_path = report_root / "INDEX.md"
    files = sorted(
        [p for p in report_root.glob("*.md") if p.name != "INDEX.md"],
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    lines = ["# Fleet scale dry-run reports", ""]
    for report in files:
        lines.append(f"- `{report.as_posix()}`")
    lines.append("")
    index_path.write_text("\n".join(lines), encoding="utf-8")


def _render_report(
    *,
    report_path: Path,
    registry_path: Path,
    target_systems: int,
    existing_count: int,
    generated_count: int,
    total_count: int,
    next_wg_ip: str | None,
    final_wg_ip: str | None,
    first_new_system_id: str | None,
    last_new_system_id: str | None,
    sim_registry_path: Path,
    errors: list[str],
) -> None:
    verdict = "PASS" if not errors else "FAIL"
    lines = [
        "# Fleet scale dry-run",
        "",
        f"- Timestamp (UTC): `{datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}`",
        f"- Verdict: **{verdict}**",
        f"- Source registry: `{registry_path.as_posix()}`",
        f"- Simulated registry: `{sim_registry_path.as_posix()}`",
        "",
        "## Scope",
        f"- target_systems: `{target_systems}`",
        f"- existing_count: `{existing_count}`",
        f"- generated_count: `{generated_count}`",
        f"- total_count: `{total_count}`",
        "",
        "## Generated range",
        f"- first_new_system_id: `{first_new_system_id or '-'}`",
        f"- last_new_system_id: `{last_new_system_id or '-'}`",
        f"- next_free_wg_ip_before: `{next_wg_ip or '-'}`",
        f"- last_allocated_wg_ip: `{final_wg_ip or '-'}`",
        "",
        "## Validation",
    ]
    if errors:
        lines.append("- errors:")
        for err in errors:
            lines.append(f"  - {err}")
    else:
        lines.append("- no validation errors")
    lines.append("")
    report_path.write_text("\n".join(lines), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Dry-run scale validation for fleet/registry.csv")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to real fleet registry")
    parser.add_argument(
        "--target-systems",
        type=int,
        default=200,
        help="Target total systems for simulation (existing + generated)",
    )
    parser.add_argument(
        "--report-root",
        type=Path,
        default=DEFAULT_REPORT_ROOT,
        help="Directory for generated markdown report and simulated CSV",
    )
    parser.add_argument(
        "--server-endpoint",
        default=None,
        help="Server endpoint host:port for generated rows (defaults to first existing row or 207.180.213.225:51820)",
    )
    parser.add_argument("--status", default="planned", help="Status value for generated rows")
    parser.add_argument("--notes-prefix", default="auto-scale-dry-run", help="Notes prefix for generated rows")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.target_systems < 1:
        raise SystemExit("--target-systems must be >= 1")

    real_entries = fr._read_registry(args.registry)
    base_errors = fr.validate_entries(real_entries)
    if base_errors:
        print("Registry validation FAILED before dry-run:")
        for err in base_errors:
            print(f"- {err}")
        return 1

    report_root: Path = args.report_root
    report_root.mkdir(parents=True, exist_ok=True)
    stamp = _now_utc_stamp()

    existing_count = len(real_entries)
    generated_count = max(args.target_systems - existing_count, 0)
    next_wg_ip_before = fr.suggest_next_wg_ip(real_entries)

    generated_entries: list[fr.SystemEntry] = []
    used_system_ids = {item.system_id for item in real_entries}
    used_vehicle_ids = {item.vehicle_id for item in real_entries}
    used_wg_ips = {item.wg_ip for item in real_entries}

    next_num = _next_system_number(real_entries)
    endpoint_default = args.server_endpoint or (
        real_entries[0].server_endpoint if real_entries else "207.180.213.225:51820"
    )

    first_new_system_id: str | None = None
    last_new_system_id: str | None = None
    final_wg_ip: str | None = None

    while len(generated_entries) < generated_count:
        system_num = next_num
        system_id = f"sys-{system_num:04d}"
        next_num += 1
        if system_id in used_system_ids:
            continue
        vehicle_id = _vehicle_id_for(system_num, used_vehicle_ids)
        wg_ip = _next_wg_ip(used_wg_ips)

        entry = fr.SystemEntry(
            system_id=system_id,
            vehicle_id=vehicle_id,
            wg_ip=wg_ip,
            server_endpoint=endpoint_default,
            status=args.status,
            notes=f"{args.notes_prefix}-{stamp}",
            line_no=0,
        )
        generated_entries.append(entry)
        used_system_ids.add(system_id)
        used_vehicle_ids.add(vehicle_id)
        used_wg_ips.add(wg_ip)

        if first_new_system_id is None:
            first_new_system_id = system_id
        last_new_system_id = system_id
        final_wg_ip = wg_ip

    simulated_entries = [*real_entries, *generated_entries]
    validation_errors = fr.validate_entries(simulated_entries)

    sim_registry_path = report_root / f"registry-sim-{stamp}.csv"
    report_path = report_root / f"scale-dry-run-{stamp}.md"

    _write_csv(sim_registry_path, simulated_entries)
    _render_report(
        report_path=report_path,
        registry_path=args.registry,
        target_systems=args.target_systems,
        existing_count=existing_count,
        generated_count=generated_count,
        total_count=len(simulated_entries),
        next_wg_ip=next_wg_ip_before if generated_count > 0 else None,
        final_wg_ip=final_wg_ip if generated_count > 0 else None,
        first_new_system_id=first_new_system_id,
        last_new_system_id=last_new_system_id,
        sim_registry_path=sim_registry_path,
        errors=validation_errors,
    )
    _update_index(report_root)

    verdict = "PASS" if not validation_errors else "FAIL"
    print(f"Report: {report_path.as_posix()}")
    print(f"Simulated registry: {sim_registry_path.as_posix()}")
    print(
        f"Summary: verdict={verdict} existing={existing_count} generated={generated_count} total={len(simulated_entries)}"
    )
    return 0 if not validation_errors else 2


if __name__ == "__main__":
    raise SystemExit(main())
