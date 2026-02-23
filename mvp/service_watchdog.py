#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import socket
import subprocess
from dataclasses import dataclass
from typing import Any

from common import load_env_file, utc_now_iso


@dataclass(frozen=True)
class UnitExpectation:
    name: str
    should_be_active: bool = True
    should_be_enabled: bool = True


def run_command(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, check=False, capture_output=True, text=True, timeout=20)


def unit_load_state(unit: str) -> str:
    proc = run_command(["systemctl", "show", unit, "-p", "LoadState", "--value"])
    value = (proc.stdout or "").strip()
    if value:
        return value
    return "unknown"


def is_active(unit: str) -> str:
    proc = run_command(["systemctl", "is-active", unit])
    value = (proc.stdout or "").strip()
    if value:
        return value
    return "unknown"


def is_enabled(unit: str) -> str:
    proc = run_command(["systemctl", "is-enabled", unit])
    value = (proc.stdout or "").strip()
    if value:
        return value
    return "unknown"


def normalize_role(raw_role: str | None, hostname: str) -> str:
    role = (raw_role or "").strip().lower()
    if role in {"edge", "central"}:
        return role
    if hostname.startswith("door-"):
        return "edge"
    return "central"


def normalize_stop_mode(raw_mode: str | None) -> str:
    mode = (raw_mode or "").strip().lower()
    if mode in {"manual", "timer"}:
        return mode
    return "manual"


def expected_units(role: str, stop_mode: str) -> list[UnitExpectation]:
    units = [UnitExpectation(name="passengers-queue-maintenance.timer")]
    if role == "edge":
        units.append(UnitExpectation(name="passengers-edge-sender.service"))
        return units

    units.extend(
        [
            UnitExpectation(name="passengers-collector.service"),
            UnitExpectation(name="passengers-central-uplink.service"),
            UnitExpectation(name="passengers-central-heartbeat.timer"),
            UnitExpectation(name="wg-quick@wg0.service"),
        ]
    )
    if stop_mode == "timer":
        units.append(UnitExpectation(name="passengers-central-flush.timer"))
    else:
        units.append(
            UnitExpectation(
                name="passengers-central-flush.timer",
                should_be_active=False,
                should_be_enabled=False,
            )
        )
    return units


def enforce_unit(expectation: UnitExpectation, *, apply_changes: bool) -> dict[str, Any]:
    unit = expectation.name
    load_state = unit_load_state(unit)
    result: dict[str, Any] = {
        "unit": unit,
        "load_state": load_state,
        "expected_active": expectation.should_be_active,
        "expected_enabled": expectation.should_be_enabled,
        "actions": [],
    }
    if load_state != "loaded":
        result["status"] = "missing"
        return result

    active_before = is_active(unit)
    enabled_before = is_enabled(unit)
    result["active_before"] = active_before
    result["enabled_before"] = enabled_before

    if apply_changes:
        if expectation.should_be_enabled and enabled_before in {"disabled", "masked", "indirect", "unknown"}:
            proc = run_command(["systemctl", "enable", unit])
            result["actions"].append(
                {"action": "enable", "rc": proc.returncode, "stderr": (proc.stderr or "").strip()}
            )
        if not expectation.should_be_enabled and enabled_before in {"enabled", "static"}:
            proc = run_command(["systemctl", "disable", unit])
            result["actions"].append(
                {"action": "disable", "rc": proc.returncode, "stderr": (proc.stderr or "").strip()}
            )

        active_now = is_active(unit)
        if expectation.should_be_active and active_now != "active":
            proc = run_command(["systemctl", "restart", unit])
            result["actions"].append(
                {"action": "restart", "rc": proc.returncode, "stderr": (proc.stderr or "").strip()}
            )
        if not expectation.should_be_active and active_now == "active":
            proc = run_command(["systemctl", "stop", unit])
            result["actions"].append(
                {"action": "stop", "rc": proc.returncode, "stderr": (proc.stderr or "").strip()}
            )

    active_after = is_active(unit)
    enabled_after = is_enabled(unit)
    result["active_after"] = active_after
    result["enabled_after"] = enabled_after

    ok_active = active_after == "active" if expectation.should_be_active else active_after != "active"
    if expectation.should_be_enabled:
        ok_enabled = enabled_after in {"enabled", "static"}
    else:
        ok_enabled = enabled_after in {"disabled", "masked", "indirect", "unknown"}
    result["status"] = "ok" if ok_active and ok_enabled else "degraded"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Watchdog check for Passengers units: enforce active/enabled state and restart if needed."
    )
    parser.add_argument("--env", default="/etc/passengers/passengers.env")
    parser.add_argument("--check-only", action="store_true")
    args = parser.parse_args()

    env = load_env_file(args.env)
    host = socket.gethostname()
    role = normalize_role(env.get("NODE_ROLE"), host)
    stop_mode = normalize_stop_mode(env.get("STOP_MODE"))
    apply_changes = not args.check_only

    results = [enforce_unit(item, apply_changes=apply_changes) for item in expected_units(role, stop_mode)]
    degraded = [item for item in results if item.get("status") != "ok"]
    report = {
        "status": "ok" if not degraded else "degraded",
        "ts": utc_now_iso(),
        "host": host,
        "role": role,
        "stop_mode": stop_mode,
        "apply_changes": apply_changes,
        "units": results,
    }
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not degraded else 2


if __name__ == "__main__":
    raise SystemExit(main())
