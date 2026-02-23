#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import ssl
import sys
from pathlib import Path
from typing import Any
from urllib import error, request


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Client panel step-7b real-data UX audit.")
    parser.add_argument("--base-url", default="https://207.180.213.225:8443", help="Base URL.")
    parser.add_argument("--admin-user", default="admin", help="BasicAuth user.")
    parser.add_argument("--admin-pass", default="", help="BasicAuth password.")
    parser.add_argument("--admin-pass-file", default="", help="Password file path.")
    parser.add_argument(
        "--write",
        default="Docs/auto/web-panel/client-step7b-ux-audit.md",
        help="Markdown report output path.",
    )
    return parser.parse_args()


def load_password(admin_pass: str, admin_pass_file: str) -> str:
    if admin_pass.strip():
        return admin_pass.strip()
    if not admin_pass_file:
        return ""
    path = Path(admin_pass_file)
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8", errors="replace")
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        line_low = line.lower()
        if "pass" in line_low and ":" in line:
            return line.split(":", 1)[1].strip()
    first_line = text.splitlines()[0].strip() if text.splitlines() else ""
    return first_line


def fetch(
    base_url: str,
    path: str,
    *,
    auth_header: str | None,
    timeout: float = 12.0,
) -> tuple[int, str]:
    url = f"{base_url.rstrip('/')}{path}"
    # Client endpoints can transiently fail around deploy/restart (nginx 502/503/504 or connection errors).
    # This audit is meant to validate UX/contracts, not punish warmup glitches.
    transient_codes = {0, 502, 503, 504}
    max_tries = 3
    delay_sec = 0.35

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    last_code = 0
    last_body = ""
    for attempt in range(1, max_tries + 1):
        req = request.Request(url, method="GET")
        if auth_header:
            req.add_header("Authorization", auth_header)
        try:
            with request.urlopen(req, timeout=timeout, context=ctx) as resp:
                body = resp.read().decode("utf-8", errors="replace")
                last_code, last_body = int(resp.getcode() or 0), body
        except error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            last_code, last_body = int(exc.code or 0), body
        except Exception as exc:  # pragma: no cover
            last_code, last_body = 0, f"ERROR: {exc}"

        if last_code not in transient_codes:
            break
        if attempt < max_tries:
            import time

            time.sleep(delay_sec)
    return last_code, last_body


def safe_json(text: str) -> dict[str, Any]:
    try:
        data = json.loads(text)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def ok(value: bool) -> str:
    return "PASS" if value else "FAIL"


def main() -> int:
    args = parse_args()
    password = load_password(args.admin_pass, args.admin_pass_file)
    if not password:
        print("ERROR: --admin-pass or --admin-pass-file is required", file=sys.stderr)
        return 2

    token_raw = f"{args.admin_user}:{password}".encode("utf-8")
    auth_header = "Basic " + base64.b64encode(token_raw).decode("ascii")

    checks: list[tuple[str, bool, str]] = []
    failed = False

    ui_paths = [
        "/client",
        "/client/vehicles",
        "/client/tickets",
        "/client/status",
        "/client/profile",
        "/client/notifications",
    ]
    api_paths = [
        "/api/client/whoami",
        "/api/client/home",
        "/api/client/vehicles?limit=20",
        "/api/client/tickets?limit=20",
        "/api/client/status?limit=20",
        "/api/client/profile",
        "/api/client/notification-settings",
    ]

    for path in ui_paths + api_paths:
        auth_code, _auth_body = fetch(args.base_url, path, auth_header=auth_header)
        anon_code, _anon_body = fetch(args.base_url, path, auth_header=None)
        is_ok = auth_code == 200 and anon_code == 401
        checks.append((f"{path} auth/anon", is_ok, f"auth={auth_code} anon={anon_code}"))
        failed = failed or (not is_ok)

    # HTML marker checks for role-aware account UX.
    profile_code, profile_html = fetch(args.base_url, "/client/profile", auth_header=auth_header)
    profile_marker_ok = profile_code == 200 and all(
        marker in profile_html
        for marker in (
            "whoami",
            "profileSupportDetails",
            "passengers_client_profile_secondary_v1",
            "copySupport",
            "profileReady",
            "skipLink",
            "sideCompactToggle",
            "clientMainContent",
        )
    )
    checks.append(("/client/profile markers", profile_marker_ok, "role-chip + secondary + summary"))
    failed = failed or (not profile_marker_ok)

    notify_code, notify_html = fetch(args.base_url, "/client/notifications", auth_header=auth_header)
    notify_marker_ok = notify_code == 200 and all(
        marker in notify_html
        for marker in (
            "whoami",
            "notifySupportDetails",
            "presetCritical",
            "passengers_client_notifications_secondary_v1",
            "sumChannels",
            "skipLink",
            "sideCompactToggle",
            "clientMainContent",
        )
    )
    checks.append(("/client/notifications markers", notify_marker_ok, "role-chip + presets + secondary + summary"))
    failed = failed or (not notify_marker_ok)

    # API contract checks.
    whoami_code, whoami_raw = fetch(args.base_url, "/api/client/whoami", auth_header=auth_header)
    whoami = safe_json(whoami_raw)
    whoami_ok = whoami_code == 200 and whoami.get("status") == "ok" and isinstance(whoami.get("capabilities"), dict)
    checks.append(("/api/client/whoami contract", whoami_ok, f"role={whoami.get('role')}"))
    failed = failed or (not whoami_ok)

    home_code, home_raw = fetch(args.base_url, "/api/client/home", auth_header=auth_header)
    home = safe_json(home_raw)
    home_summary = home.get("summary") if isinstance(home.get("summary"), dict) else {}
    home_ok = (
        home_code == 200
        and home.get("status") == "ok"
        and isinstance(home.get("attention"), list)
        and all(key in home_summary for key in ("sla_risk", "sla_warn", "eta_avg_delay_min", "eta_max_delay_min"))
    )
    checks.append(
        ("/api/client/home contract", home_ok, f"sla_risk={home_summary.get('sla_risk')} attention={len(home.get('attention') or [])}")
    )
    failed = failed or (not home_ok)

    vehicles_code, vehicles_raw = fetch(args.base_url, "/api/client/vehicles?limit=20", auth_header=auth_header)
    vehicles = safe_json(vehicles_raw)
    vehicles_summary = vehicles.get("summary") if isinstance(vehicles.get("summary"), dict) else {}
    rows = vehicles.get("vehicles") if isinstance(vehicles.get("vehicles"), list) else []
    row_contract_ok = True
    for item in rows:
        if not isinstance(item, dict):
            row_contract_ok = False
            break
        for key in ("sla_state", "eta_delay_min", "pending_batches", "incidents_open"):
            if key not in item:
                row_contract_ok = False
                break
        if not row_contract_ok:
            break
    vehicles_ok = (
        vehicles_code == 200
        and vehicles.get("status") == "ok"
        and row_contract_ok
        and all(key in vehicles_summary for key in ("sla_ok", "sla_warn", "sla_risk", "eta_avg_delay_min", "eta_max_delay_min"))
    )
    checks.append(("/api/client/vehicles contract", vehicles_ok, f"rows={len(rows)}"))
    failed = failed or (not vehicles_ok)

    profile_code_api, profile_raw_api = fetch(args.base_url, "/api/client/profile", auth_header=auth_header)
    profile_json = safe_json(profile_raw_api)
    profile_obj = profile_json.get("profile") if isinstance(profile_json.get("profile"), dict) else {}
    profile_ok = (
        profile_code_api == 200
        and profile_json.get("status") == "ok"
        and all(key in profile_obj for key in ("full_name", "email", "phone", "locale"))
    )
    checks.append(("/api/client/profile contract", profile_ok, f"locale={profile_obj.get('locale')}"))
    failed = failed or (not profile_ok)

    notify_code_api, notify_raw_api = fetch(args.base_url, "/api/client/notification-settings", auth_header=auth_header)
    notify_json = safe_json(notify_raw_api)
    notify_obj = notify_json.get("settings") if isinstance(notify_json.get("settings"), dict) else {}
    notify_ok = (
        notify_code_api == 200
        and notify_json.get("status") == "ok"
        and all(key in notify_obj for key in ("notify_email", "notify_sms", "notify_push", "notify_level", "digest_window"))
    )
    checks.append(("/api/client/notification-settings contract", notify_ok, f"level={notify_obj.get('notify_level')}"))
    failed = failed or (not notify_ok)

    now_utc = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    report_path = Path(args.write)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    lines.append("# Client Step-7b UX Audit")
    lines.append("")
    lines.append(f"- generated_at_utc: `{now_utc}`")
    lines.append(f"- base_url: `{args.base_url}`")
    lines.append("")
    lines.append("## Checks")
    lines.append("")
    lines.append("| Check | Result | Details |")
    lines.append("|---|---|---|")
    for name, is_ok, details in checks:
        lines.append(f"| `{name}` | `{ok(is_ok)}` | {details} |")
    lines.append("")
    lines.append("## Real Data Snapshot")
    lines.append("")
    lines.append(f"- role: `{whoami.get('role')}`")
    lines.append(f"- home.transport_total: `{home_summary.get('transport_total')}`")
    lines.append(f"- home.sla_risk/sla_warn: `{home_summary.get('sla_risk')}/{home_summary.get('sla_warn')}`")
    lines.append(
        f"- home.eta_avg/max: `{home_summary.get('eta_avg_delay_min')}/{home_summary.get('eta_max_delay_min')}`"
    )
    lines.append(f"- vehicles.rows: `{len(rows)}`")
    lines.append(
        f"- vehicles.sla_ok/warn/risk: `{vehicles_summary.get('sla_ok')}/{vehicles_summary.get('sla_warn')}/{vehicles_summary.get('sla_risk')}`"
    )
    lines.append(f"- profile.locale: `{profile_obj.get('locale')}`")
    lines.append(
        f"- notifications.level/digest: `{notify_obj.get('notify_level')}/{notify_obj.get('digest_window')}`"
    )
    lines.append("")
    lines.append("## Verdict")
    lines.append("")
    lines.append(f"- status: `{'PASS' if not failed else 'FAIL'}`")

    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Report written: {report_path}")
    print(f"RESULT: {'PASS' if not failed else 'FAIL'}")
    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
