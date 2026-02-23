#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from dataclasses import asdict
from pathlib import Path

import fleet_registry as fr

DEFAULT_REGISTRY = Path("fleet/registry.csv")
DEFAULT_OUT = Path("fleet/templates/registry-sys-0002-0020.template.csv")
DEFAULT_CHECKLIST = Path("fleet/templates/checklist-sys-0002-0020.md")


def _system_id(num: int) -> str:
    return f"sys-{num:04d}"


def _vehicle_placeholder(num: int) -> str:
    return f"bus-{num:03d}_FILL_PLATE"


def _parse_system_num(value: str) -> int:
    if not value.startswith("sys-"):
        raise ValueError(f"bad system id: {value}")
    tail = value[4:]
    if not tail.isdigit():
        raise ValueError(f"bad system id: {value}")
    return int(tail)


def _next_free_wg(used: set[str]) -> str:
    for host in range(11, 255):
        candidate = f"10.66.0.{host}"
        if candidate in used:
            continue
        return candidate
    raise SystemExit("No free WG IP left in 10.66.0.0/24")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate manual batch template for fleet registry range.")
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY, help="Path to registry CSV")
    parser.add_argument("--from", dest="from_num", type=int, default=2, help="Start system number (default: 2)")
    parser.add_argument("--to", dest="to_num", type=int, default=20, help="End system number inclusive (default: 20)")
    parser.add_argument(
        "--server-endpoint",
        default=None,
        help="Override server endpoint host:port, defaults to endpoint from existing sys-0001",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUT, help="Output template CSV path")
    parser.add_argument(
        "--checklist-output",
        type=Path,
        default=DEFAULT_CHECKLIST,
        help="Output markdown checklist path",
    )
    return parser


def _render_checklist(from_num: int, to_num: int, output_csv: Path) -> str:
    return "\n".join(
        [
            f"# Checklist массового ввода `sys-{from_num:04d}..sys-{to_num:04d}`",
            "",
            f"1. Открыть шаблон: `{output_csv.as_posix()}`.",
            "2. Для каждой строки заполнить `vehicle_id` в формате `bus-XXX_AA1234BB`.",
            "3. Проверить, что `server_endpoint` корректный (`207.180.213.225:51820`) и единый.",
            "4. Не менять `wg_ip` без отдельного плана адресации.",
            "5. Перенести строки в `fleet/registry.csv` пакетами (рекомендуется 3–5 систем).",
            "6. После каждого пакета запускать:",
            "   - `python3 scripts/fleet_registry.py validate`",
            "   - `python3 scripts/fleet_scale_dry_run.py --target-systems 200`",
            "7. Для каждого `system_id` генерировать bundle:",
            "   - `python3 scripts/fleet_registry.py bundle --system-id <SYSTEM_ID>`",
            "8. Запускать rollout-check (без железа, только реестр+bundle+оркестратор):",
            "   - `python3 scripts/fleet_rollout_check.py --system-id <SYSTEM_ID>`",
            "9. Перед полевым вводом системы пройти e2e путь из `fleet/out/<SYSTEM_ID>/commands.md`.",
            "10. После фактического ввода фиксировать commissioning:",
            "   - `python3 scripts/fleet_commission.py --system-id <SYSTEM_ID> --smoke`",
            "",
        ]
    )


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.from_num < 1:
        raise SystemExit("--from must be >= 1")
    if args.to_num < args.from_num:
        raise SystemExit("--to must be >= --from")

    entries = fr._read_registry(args.registry)
    validation_errors = fr.validate_entries(entries)
    if validation_errors:
        raise SystemExit("Registry invalid; fix validation errors before generating templates")

    by_system_id = {item.system_id: item for item in entries}
    used_wg = {item.wg_ip for item in entries if item.wg_ip}
    endpoint = args.server_endpoint or (entries[0].server_endpoint if entries else "207.180.213.225:51820")

    out_rows: list[dict[str, str]] = []
    for number in range(args.from_num, args.to_num + 1):
        system_id = _system_id(number)
        existing = by_system_id.get(system_id)
        if existing is not None:
            out_rows.append(
                {
                    "system_id": existing.system_id,
                    "vehicle_id": existing.vehicle_id,
                    "wg_ip": existing.wg_ip,
                    "server_endpoint": existing.server_endpoint,
                    "status": existing.status,
                    "notes": existing.notes or "already_in_registry",
                }
            )
            continue

        wg_ip = _next_free_wg(used_wg)
        used_wg.add(wg_ip)
        out_rows.append(
            {
                "system_id": system_id,
                "vehicle_id": _vehicle_placeholder(number),
                "wg_ip": wg_ip,
                "server_endpoint": endpoint,
                "status": "planned",
                "notes": "template_manual_fill",
            }
        )

    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["system_id", "vehicle_id", "wg_ip", "server_endpoint", "status", "notes"]
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(out_rows)

    checklist_output = args.checklist_output
    checklist_output.parent.mkdir(parents=True, exist_ok=True)
    checklist_output.write_text(_render_checklist(args.from_num, args.to_num, output_path), encoding="utf-8")

    print(f"Wrote template: {output_path.as_posix()}")
    print(f"Wrote checklist: {checklist_output.as_posix()}")
    print(f"Rows: {len(out_rows)} (from {args.from_num} to {args.to_num})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
