#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import time
import urllib.error
import urllib.request


def is_time_synchronized() -> tuple[bool, str]:
    commands = [
        ["timedatectl", "show", "--property=SystemClockSynchronized", "--value"],
        ["timedatectl", "show", "--property=NTPSynchronized", "--value"],
    ]
    observed: list[str] = []
    for cmd in commands:
        try:
            out = subprocess.check_output(cmd, text=True, stderr=subprocess.DEVNULL).strip().lower()
        except Exception:
            continue
        observed.append(out or "unknown")
        if out in {"yes", "true", "1"}:
            return True, "time_sync=yes"
    if observed:
        return False, f"time_sync={observed[0]}"
    return False, "time_sync=unknown"


def is_http_ok(url: str, timeout_sec: float) -> tuple[bool, str]:
    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            status = int(getattr(resp, "status", 200))
            return status == 200, f"http={status} url={url}"
    except urllib.error.HTTPError as e:
        return False, f"http={e.code} url={url}"
    except Exception as e:
        return False, f"http=down url={url} err={e}"


def split_urls(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def is_any_http_ok(urls: list[str], timeout_sec: float) -> tuple[bool, str]:
    last_info = ""
    for url in urls:
        ok, info = is_http_ok(url, timeout_sec=timeout_sec)
        last_info = info
        if ok:
            return True, info
    return False, last_info or "http=down url=?"


def checks_for_mode(mode: str) -> tuple[bool, bool, bool]:
    if mode == "edge":
        return True, True, False
    if mode == "central-uplink":
        return True, False, True
    if mode == "central-heartbeat":
        return True, False, True
    if mode in {"central-collector", "central-flush"}:
        return True, False, False
    raise ValueError(f"unsupported mode: {mode}")


def run_checks(
    need_time_sync: bool,
    need_central: bool,
    need_backend: bool,
    central_health_url: str,
    backend_health_url: str,
    http_timeout_sec: float,
) -> tuple[bool, list[str]]:
    parts: list[str] = []
    ok = True

    if need_time_sync:
        good, info = is_time_synchronized()
        parts.append(info)
        ok = ok and good

    if need_central:
        good, info = is_any_http_ok(split_urls(central_health_url), timeout_sec=http_timeout_sec)
        parts.append(f"central_{info}")
        ok = ok and good

    if need_backend:
        good, info = is_any_http_ok(split_urls(backend_health_url), timeout_sec=http_timeout_sec)
        parts.append(f"backend_{info}")
        ok = ok and good

    return ok, parts


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight checks before starting MVP services.")
    parser.add_argument(
        "--mode",
        required=True,
        choices=["edge", "central-collector", "central-uplink", "central-flush", "central-heartbeat"],
        help="Preset of required checks.",
    )
    parser.add_argument("--central-health-url", default="http://192.168.10.1:8080/health")
    parser.add_argument("--backend-health-url", default="http://10.66.0.1/health")
    parser.add_argument("--wait-timeout-sec", type=int, default=300, help="0 means wait forever.")
    parser.add_argument("--poll-sec", type=float, default=2.0)
    parser.add_argument("--http-timeout-sec", type=float, default=2.5)
    parser.add_argument("--skip-time-sync", action="store_true")
    parser.add_argument("--skip-central", action="store_true")
    parser.add_argument("--skip-backend", action="store_true")
    args = parser.parse_args()

    need_time_sync, need_central, need_backend = checks_for_mode(args.mode)
    if args.skip_time_sync:
        need_time_sync = False
    if args.skip_central:
        need_central = False
    if args.skip_backend:
        need_backend = False

    started = time.monotonic()
    deadline = None if args.wait_timeout_sec == 0 else started + float(args.wait_timeout_sec)
    last_log = 0.0
    last_signature = ""

    while True:
        ok, details = run_checks(
            need_time_sync=need_time_sync,
            need_central=need_central,
            need_backend=need_backend,
            central_health_url=args.central_health_url,
            backend_health_url=args.backend_health_url,
            http_timeout_sec=args.http_timeout_sec,
        )
        signature = "; ".join(details)
        now = time.monotonic()

        if ok:
            print(f"preflight ok: mode={args.mode}; {signature}")
            return 0

        should_log = signature != last_signature or now - last_log >= 10.0
        if should_log:
            elapsed = int(now - started)
            print(f"preflight waiting: mode={args.mode}; elapsed={elapsed}s; {signature}", flush=True)
            last_log = now
            last_signature = signature

        if deadline is not None and now >= deadline:
            print(f"preflight timeout: mode={args.mode}; waited={args.wait_timeout_sec}s; {signature}", flush=True)
            return 1

        time.sleep(max(0.2, args.poll_sec))


if __name__ == "__main__":
    raise SystemExit(main())
