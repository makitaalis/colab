from __future__ import annotations

import json
import os
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from pathlib import Path
from typing import Annotated, Any
from urllib.error import URLError
from urllib.parse import urlencode
from urllib.request import Request as UrlRequest, urlopen

from fastapi import Depends, FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from app.db import (
    clear_alert_silence,
    delete_monitor_policy_override,
    get_alert_state,
    get_incident_by_key,
    get_incident_notification_by_id,
    get_incident_last_notification_state,
    get_monitor_policy_override,
    list_admin_audit,
    get_notification_settings,
    list_incident_notifications,
    list_incidents,
    list_alert_actions,
    list_monitor_policy_overrides,
    list_fleet_health_history_samples,
    get_central_heartbeat_history,
    ingest_central_heartbeat,
    ingest_stop,
    init_db,
    list_central_heartbeats,
    record_incident_notification,
    record_admin_audit,
    set_alert_ack,
    set_alert_silence,
    sync_incidents,
    upsert_monitor_policy_override,
    update_notification_settings,
    stats_vehicle,
)
from app.admin_alerts_ops import (
    build_alert_groups_response,
    build_alerts_response,
)
from app.admin_fleet_monitor_ops import collect_monitor_snapshot
from app.admin_fleet_policy_page import render_admin_fleet_policy_page
from app.admin_fleet_history_page import render_admin_fleet_history_page
from app.admin_fleet_notifications_page import render_admin_fleet_notifications_page
from app.admin_fleet_notify_center_page import render_admin_fleet_notify_center_page
from app.admin_fleet_incidents_page import render_admin_fleet_incidents_page
from app.admin_fleet_incident_detail_page import render_admin_fleet_incident_detail_page
from app.admin_fleet_actions_page import render_admin_fleet_actions_page
from app.admin_audit_page import render_admin_audit_page
from app.admin_wg_page import render_admin_wg_page
from app.admin_fleet_central_page import render_admin_fleet_central_page
from app.admin_incidents_ops import (
    build_alert_actions_response,
    build_incident_detail_response,
    build_incident_notifications_response,
    build_incidents_response,
)
from app.admin_audit_ops import build_admin_audit_response
from app.admin_notification_ops import (
    build_notification_settings_response,
    prepare_notification_retry,
    prepare_notification_settings_update,
    prepare_notification_test,
)
from app.admin_monitor_policy_ops import (
    build_monitor_policy_overrides_response,
    build_monitor_policy_response,
    prepare_monitor_policy_override_delete,
    prepare_monitor_policy_override_upsert,
    prepare_monitor_policy_update,
)
from app.admin_runtime_config import (
    load_notification_runtime_settings,
    normalize_monitor_policy_settings as runtime_normalize_monitor_policy_settings,
    normalize_notification_settings as runtime_normalize_notification_settings,
    resolve_health_notify_channels as runtime_resolve_health_notify_channels,
)
from app.admin_fleet_page import render_admin_fleet_page
from app.admin_fleet_alerts_page import render_admin_fleet_alerts_page
from app.admin_overview_page import render_admin_overview_page
from app.admin_commission_page import render_admin_commission_page
from app.client_home_page import render_client_home_page
from app.client_vehicles_page import render_client_vehicles_page
from app.client_tickets_page import render_client_tickets_page
from app.client_status_page import render_client_status_page
from app.client_profile_page import render_client_profile_page
from app.client_notifications_page import render_client_notifications_page
from app.client_ops import (
    build_client_home_response,
    build_client_notification_settings_response,
    build_client_profile_response,
    build_client_status_response,
    build_client_tickets_response,
    build_client_vehicles_response,
    update_client_notification_settings_response,
    update_client_profile_response,
)
from app.webpanel_v2.router import router as webpanel_v2_router


def _split_keys(raw: str) -> set[str]:
    keys: set[str] = set()
    for item in raw.replace("\n", ",").split(","):
        token = item.strip()
        if token:
            keys.add(token)
    return keys


def get_api_keys() -> set[str]:
    return _split_keys(os.environ.get("PASSENGERS_API_KEYS", ""))

def get_admin_api_keys() -> set[str]:
    raw = os.environ.get("ADMIN_API_KEYS", "")
    keys = _split_keys(raw)
    return keys


def get_client_api_keys() -> set[str]:
    raw = os.environ.get("CLIENT_API_KEYS", "")
    keys = _split_keys(raw)
    if keys:
        return keys
    fallback = get_admin_api_keys() or get_api_keys()
    return fallback


def get_client_support_users() -> set[str]:
    return {item.strip().lower() for item in _split_keys(os.environ.get("CLIENT_SUPPORT_USERS", "")) if item.strip()}


def _normalize_admin_role(value: str | None) -> str:
    normalized = str(value or "").strip().lower()
    if normalized in {"viewer", "operator", "admin"}:
        return normalized
    return "viewer"


def _admin_role_rank(role: str) -> int:
    ranks = {"viewer": 0, "operator": 1, "admin": 2}
    return ranks.get(_normalize_admin_role(role), 0)


def get_admin_key_roles() -> dict[str, str]:
    raw = str(os.environ.get("ADMIN_API_KEY_ROLES", "")).strip()
    mapping: dict[str, str] = {}
    if not raw:
        return mapping
    tokens = [item.strip() for item in raw.replace("\n", ",").split(",") if item.strip()]
    for item in tokens:
        if ":" not in item:
            continue
        key, role = item.split(":", 1)
        key_value = key.strip()
        if not key_value:
            continue
        mapping[key_value] = _normalize_admin_role(role)
    return mapping


def get_db_path() -> str:
    return os.environ.get("DB_PATH", "/data/passengers.sqlite3")

def get_wg_status_path() -> str:
    return os.environ.get("WG_STATUS_PATH", "/wg/peers.json")


def get_wg_conf_path() -> str:
    return os.environ.get("WG_CONF_PATH", "/wg/wg0.conf.redacted")


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _parse_iso_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _to_int(value: Any, default: int) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _severity_rank(level: str) -> int:
    normalized = str(level or "").strip().lower()
    ranks = {"good": 0, "warn": 1, "bad": 2}
    return ranks.get(normalized, 2)


def _severity_allowed(*, severity: str, min_severity: str) -> bool:
    return _severity_rank(severity) >= _severity_rank(min_severity)


def _resolve_bool_setting(
    settings: dict[str, str],
    *,
    key: str,
    env_key: str,
    default: bool,
) -> bool:
    raw = settings.get(key)
    if raw is None or str(raw).strip() == "":
        return _bool_env(env_key, default)
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


async def _notification_runtime_settings(db_path: str) -> dict[str, Any]:
    return await load_notification_runtime_settings(db_path)


def _normalize_notification_settings(settings: dict[str, str]) -> dict[str, Any]:
    return runtime_normalize_notification_settings(settings)


def _notification_message(incident: dict[str, Any]) -> tuple[str, str]:
    severity = str(incident.get("severity") or "bad").upper()
    event = str(incident.get("event") or "opened")
    central_id = str(incident.get("central_id") or "?")
    vehicle_id = str(incident.get("vehicle_id") or "—")
    code = str(incident.get("code") or "alert")
    status = str(incident.get("status") or "open")
    message = str(incident.get("message") or "")
    first_seen_ts = str(incident.get("first_seen_ts") or "—")
    subject = f"[passengers][{severity}] {central_id}:{code} ({event})"
    body = (
        f"event={event}\n"
        f"severity={severity}\n"
        f"central_id={central_id}\n"
        f"vehicle_id={vehicle_id}\n"
        f"code={code}\n"
        f"status={status}\n"
        f"first_seen={first_seen_ts}\n"
        f"message={message}\n"
    )
    return subject, body


def _send_telegram_notification(text: str) -> tuple[bool, str | None, str | None]:
    token = str(os.environ.get("ALERT_TELEGRAM_BOT_TOKEN", "")).strip()
    chat_id = str(os.environ.get("ALERT_TELEGRAM_CHAT_ID", "")).strip()
    if not token or not chat_id:
        return False, None, "telegram_not_configured"

    payload = urlencode({"chat_id": chat_id, "text": text[:3900], "disable_web_page_preview": "true"}).encode("utf-8")
    request = UrlRequest(
        f"https://api.telegram.org/bot{token}/sendMessage",
        data=payload,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=10) as response:
            if int(getattr(response, "status", 200)) >= 400:
                return False, chat_id, f"telegram_http_{getattr(response, 'status', 'error')}"
        return True, chat_id, None
    except URLError as exc:
        return False, chat_id, f"telegram_error:{exc}"
    except Exception as exc:
        return False, chat_id, f"telegram_error:{exc}"


def _send_email_notification(*, subject: str, body: str) -> tuple[bool, str | None, str | None]:
    recipients_raw = str(os.environ.get("ALERT_EMAIL_TO", "")).strip()
    smtp_host = str(os.environ.get("ALERT_SMTP_HOST", "")).strip()
    from_email = str(os.environ.get("ALERT_EMAIL_FROM", "")).strip()
    if not recipients_raw or not smtp_host or not from_email:
        return False, None, "email_not_configured"

    recipients = [item.strip() for item in recipients_raw.replace(";", ",").split(",") if item.strip()]
    if not recipients:
        return False, None, "email_recipients_empty"

    smtp_port = int(str(os.environ.get("ALERT_SMTP_PORT", "587")).strip() or "587")
    smtp_user = str(os.environ.get("ALERT_SMTP_USER", "")).strip()
    smtp_pass = str(os.environ.get("ALERT_SMTP_PASS", "")).strip()
    use_starttls = _bool_env("ALERT_SMTP_STARTTLS", True)

    msg = EmailMessage()
    msg["From"] = from_email
    msg["To"] = ", ".join(recipients)
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=12) as smtp:
            smtp.ehlo()
            if use_starttls:
                smtp.starttls(context=ssl.create_default_context())
                smtp.ehlo()
            if smtp_user and smtp_pass:
                smtp.login(smtp_user, smtp_pass)
            smtp.send_message(msg)
        return True, ",".join(recipients), None
    except Exception as exc:
        return False, ",".join(recipients), f"email_error:{exc}"


async def _dispatch_incident_notifications(db_path: str, events: list[dict[str, Any]]) -> dict[str, Any]:
    runtime = await _notification_runtime_settings(db_path)
    now_dt = datetime.now(timezone.utc)
    channels: list[str] = []
    if bool(runtime["notify_telegram"]):
        channels.append("telegram")
    if bool(runtime["notify_email"]):
        channels.append("email")

    active_incidents = await list_incidents(
        db_path,
        include_resolved=False,
        limit=5000,
    )
    latest_state = await get_incident_last_notification_state(db_path)

    merged_events: dict[tuple[str, str, str], dict[str, Any]] = {}
    for incident in events:
        central_id = str(incident.get("central_id") or "")
        code = str(incident.get("code") or "")
        event = str(incident.get("event") or "opened")
        if not central_id or not code:
            continue
        merged_events[(central_id, code, event)] = incident

    escalation_sec = int(runtime["escalation_sec"])
    rate_limit_sec = int(runtime["rate_limit_sec"])
    for incident in active_incidents:
        if str(incident.get("status") or "") != "open":
            continue
        age_sec = _to_int(incident.get("age_sec"), -1)
        if age_sec < escalation_sec:
            continue
        central_id = str(incident.get("central_id") or "")
        code = str(incident.get("code") or "")
        if not central_id or not code:
            continue
        latest = latest_state.get((central_id, code))
        if latest and str(latest.get("event") or "") == "escalation_policy":
            latest_ts = _parse_iso_utc(str(latest.get("ts") or ""))
            if latest_ts and int((now_dt - latest_ts).total_seconds()) < rate_limit_sec:
                continue
        escalation_event = dict(incident)
        escalation_event["event"] = "escalation_policy"
        merged_events[(central_id, code, "escalation_policy")] = escalation_event

    counters = {"total": 0, "sent": 0, "failed": 0, "skipped": 0}
    mute_until_dt = runtime.get("mute_until_dt")
    stale_always_notify = bool(runtime.get("stale_always_notify"))
    min_severity = str(runtime.get("min_severity") or "bad")

    def should_log_policy_skip(*, central_id: str, code: str, event_name: str) -> bool:
        latest = latest_state.get((central_id, code))
        if not latest:
            return True
        if str(latest.get("status") or "") != "skipped":
            return True
        if str(latest.get("event") or "") != event_name:
            return True
        latest_ts = _parse_iso_utc(str(latest.get("ts") or ""))
        if latest_ts is None:
            return True
        return int((now_dt - latest_ts).total_seconds()) >= rate_limit_sec

    for incident in merged_events.values():
        central_id = str(incident.get("central_id") or "")
        code = str(incident.get("code") or "")
        severity = str(incident.get("severity") or "bad")
        event_name = str(incident.get("event") or "opened")
        if not central_id or not code:
            continue

        is_stale = "stale" in code.lower()
        if not (_severity_allowed(severity=severity, min_severity=min_severity) or (is_stale and stale_always_notify)):
            counters["skipped"] += 1
            policy_event = "policy_filtered"
            if should_log_policy_skip(central_id=central_id, code=code, event_name=policy_event):
                await record_incident_notification(
                    db_path,
                    central_id=central_id,
                    code=code,
                    severity=severity,
                    event=policy_event,
                    channel="policy",
                    destination=None,
                    status="skipped",
                    message="notification filtered by min_severity",
                    error=f"filtered:min_severity={min_severity}",
                )
                latest_state[(central_id, code)] = {
                    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "event": policy_event,
                    "status": "skipped",
                    "channel": "policy",
                }
            continue

        if mute_until_dt and mute_until_dt > now_dt:
            counters["skipped"] += 1
            policy_event = "policy_muted"
            if should_log_policy_skip(central_id=central_id, code=code, event_name=policy_event):
                await record_incident_notification(
                    db_path,
                    central_id=central_id,
                    code=code,
                    severity=severity,
                    event=policy_event,
                    channel="policy",
                    destination=None,
                    status="skipped",
                    message="notification skipped by mute window",
                    error=f"muted_until:{runtime.get('mute_until')}",
                )
                latest_state[(central_id, code)] = {
                    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "event": policy_event,
                    "status": "skipped",
                    "channel": "policy",
                }
            continue

        latest = latest_state.get((central_id, code))
        if latest:
            latest_ts = _parse_iso_utc(str(latest.get("ts") or ""))
            if latest_ts and int((now_dt - latest_ts).total_seconds()) < rate_limit_sec:
                counters["skipped"] += 1
                policy_event = "policy_rate_limit"
                if should_log_policy_skip(central_id=central_id, code=code, event_name=policy_event):
                    await record_incident_notification(
                        db_path,
                        central_id=central_id,
                        code=code,
                        severity=severity,
                        event=policy_event,
                        channel="policy",
                        destination=None,
                        status="skipped",
                        message="notification skipped by rate limit",
                        error=f"rate_limit:{rate_limit_sec}s",
                    )
                    latest_state[(central_id, code)] = {
                        "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                        "event": policy_event,
                        "status": "skipped",
                        "channel": "policy",
                    }
                continue

        subject, body = _notification_message(incident)
        if not channels:
            counters["skipped"] += 1
            policy_event = "policy_channels_disabled"
            if should_log_policy_skip(central_id=central_id, code=code, event_name=policy_event):
                await record_incident_notification(
                    db_path,
                    central_id=central_id,
                    code=code,
                    severity=severity,
                    event=policy_event,
                    channel="policy",
                    destination=None,
                    status="skipped",
                    message=subject,
                    error="channels_disabled",
                )
                latest_state[(central_id, code)] = {
                    "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                    "event": policy_event,
                    "status": "skipped",
                    "channel": "policy",
                }
            continue

        for channel in channels:
            counters["total"] += 1
            if channel == "telegram":
                ok, destination, error = _send_telegram_notification(f"{subject}\n{body}")
            else:
                ok, destination, error = _send_email_notification(subject=subject, body=body)

            if ok:
                status = "sent"
                counters["sent"] += 1
            elif error and error.endswith("not_configured"):
                status = "skipped"
                counters["skipped"] += 1
            else:
                status = "failed"
                counters["failed"] += 1

            await record_incident_notification(
                db_path,
                central_id=central_id,
                code=code,
                severity=severity,
                event=event_name,
                channel=channel,
                destination=destination,
                status=status,
                message=subject,
                error=error,
            )

            latest_state[(central_id, code)] = {
                "ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
                "event": event_name,
                "status": status,
                "channel": channel,
            }
    return counters


async def _dispatch_test_notification(
    db_path: str,
    *,
    incident: dict[str, Any],
    channels: list[str],
    dry_run: bool,
    event_name: str = "test",
) -> dict[str, Any]:
    counters = {"total": 0, "sent": 0, "failed": 0, "skipped": 0}
    details: list[dict[str, Any]] = []
    subject, body = _notification_message(incident)

    if not channels:
        counters["skipped"] += 1
        details.append({"channel": "none", "status": "skipped", "error": "channels_empty"})
        return {"counters": counters, "details": details}

    if dry_run:
        for channel in channels:
            counters["total"] += 1
            counters["skipped"] += 1
            details.append({"channel": channel, "status": "skipped", "error": "dry_run"})
        return {"counters": counters, "details": details}

    for channel in channels:
        counters["total"] += 1
        if channel == "telegram":
            ok, destination, error = _send_telegram_notification(f"{subject}\n{body}")
        else:
            ok, destination, error = _send_email_notification(subject=subject, body=body)

        if ok:
            status = "sent"
            counters["sent"] += 1
        elif error and error.endswith("not_configured"):
            status = "skipped"
            counters["skipped"] += 1
        else:
            status = "failed"
            counters["failed"] += 1

        details.append({"channel": channel, "status": status, "destination": destination, "error": error})
        await record_incident_notification(
            db_path,
            central_id=str(incident.get("central_id") or ""),
            code=str(incident.get("code") or "test_notification"),
            severity=str(incident.get("severity") or "warn"),
            event=event_name,
            channel=channel,
            destination=destination,
            status=status,
            message=subject,
            error=error,
        )

    return {"counters": counters, "details": details}


async def require_api_key(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> str:
    api_keys = get_api_keys()
    if not api_keys:
        raise HTTPException(status_code=503, detail="server_not_configured")

    token = ""
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()

    if not token or token not in api_keys:
        raise HTTPException(status_code=401, detail="unauthorized")

    return token


def _extract_bearer_token(authorization: str | None) -> str:
    token = ""
    if authorization:
        parts = authorization.split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            token = parts[1].strip()
    return token


def _resolve_admin_role(token: str) -> str:
    role_map = get_admin_key_roles()
    if role_map:
        return _normalize_admin_role(role_map.get(token))
    return "admin"


def _resolve_admin_actor(request: Request, token: str) -> str:
    actor = (
        request.headers.get("x-admin-user")
        or request.headers.get("x-forwarded-user")
        or request.headers.get("x-remote-user")
        or request.headers.get("remote-user")
        or ""
    ).strip()
    if actor:
        return actor
    return f"key:{token[:8]}" if token else "unknown"


def _parse_client_scope_bindings() -> dict[str, dict[str, set[str]]]:
    raw = str(os.environ.get("CLIENT_SCOPE_BINDINGS", "")).strip()
    if not raw:
        return {}

    mapping: dict[str, dict[str, set[str]]] = {}
    for token in [item.strip() for item in raw.replace("\n", ",").split(",") if item.strip()]:
        parts = [item.strip() for item in token.split(":")]
        if len(parts) < 2:
            continue
        actor = parts[0].lower()
        central_id = parts[1]
        vehicle_id = parts[2] if len(parts) >= 3 else ""
        if not actor or not central_id:
            continue
        slot = mapping.setdefault(actor, {"central_ids": set(), "vehicle_ids": set()})
        slot["central_ids"].add(central_id)
        if vehicle_id:
            slot["vehicle_ids"].add(vehicle_id)
    return mapping


def _resolve_client_actor(request: Request, token: str) -> str:
    actor = (
        request.headers.get("x-client-user")
        or request.headers.get("x-forwarded-user")
        or request.headers.get("x-remote-user")
        or request.headers.get("remote-user")
        or ""
    ).strip()
    if actor:
        return actor
    return f"client:{token[:8]}" if token else "client:unknown"


def _resolve_client_scope(actor: str) -> dict[str, list[str]]:
    defaults_central = sorted(_split_keys(os.environ.get("CLIENT_DEFAULT_CENTRAL_IDS", "")))
    defaults_vehicle = sorted(_split_keys(os.environ.get("CLIENT_DEFAULT_VEHICLE_IDS", "")))
    if not defaults_central and not defaults_vehicle:
        defaults_central = sorted(_split_keys(os.environ.get("PASSENGERS_CLIENT_CENTRAL_IDS", "")))
        defaults_vehicle = sorted(_split_keys(os.environ.get("PASSENGERS_CLIENT_VEHICLE_IDS", "")))

    bindings = _parse_client_scope_bindings()
    actor_key = str(actor or "").strip().lower()
    slot = bindings.get(actor_key) or bindings.get("*")
    if slot:
        central_ids = sorted(slot.get("central_ids") or set())
        vehicle_ids = sorted(slot.get("vehicle_ids") or set())
        if central_ids or vehicle_ids:
            return {
                "central_ids": central_ids,
                "vehicle_ids": vehicle_ids,
            }
    return {
        "central_ids": defaults_central,
        "vehicle_ids": defaults_vehicle,
    }


def _resolve_client_role(actor: str) -> str:
    actor_key = str(actor or "").strip().lower()
    support_users = get_client_support_users()
    if "*" in support_users or actor_key in support_users:
        return "admin-support"
    return "client"


def _resolve_client_ip(request: Request) -> str | None:
    xff = (request.headers.get("x-forwarded-for") or "").strip()
    if xff:
        first = xff.split(",")[0].strip()
        if first:
            return first
    if request.client and request.client.host:
        return str(request.client.host)
    return None


async def require_client_context(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    api_keys = get_client_api_keys()
    if not api_keys:
        raise HTTPException(status_code=503, detail="server_not_configured")

    token = _extract_bearer_token(authorization)
    if not token or token not in api_keys:
        raise HTTPException(status_code=401, detail="unauthorized")

    actor = _resolve_client_actor(request, token)
    client_ip = _resolve_client_ip(request)
    return {
        "token": token,
        "actor": actor,
        "role": _resolve_client_role(actor),
        "client_ip": client_ip,
        "scope": _resolve_client_scope(actor),
    }


async def require_admin_context(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
) -> dict[str, Any]:
    api_keys = get_admin_api_keys() or get_api_keys()
    if not api_keys:
        raise HTTPException(status_code=503, detail="server_not_configured")

    token = _extract_bearer_token(authorization)

    if not token or token not in api_keys:
        raise HTTPException(status_code=401, detail="unauthorized")

    role = _resolve_admin_role(token)
    actor = _resolve_admin_actor(request, token)
    client_ip = _resolve_client_ip(request)
    return {"token": token, "role": role, "actor": actor, "client_ip": client_ip}


async def _audit_admin_event(
    *,
    ctx: dict[str, Any],
    request: Request,
    action: str,
    status: str,
    status_code: int,
    details: dict[str, Any] | None = None,
) -> None:
    try:
        await record_admin_audit(
            get_db_path(),
            actor=str(ctx.get("actor") or ""),
            role=str(ctx.get("role") or "viewer"),
            action=action,
            method=request.method,
            path=request.url.path,
            status=status,
            status_code=status_code,
            client_ip=str(ctx.get("client_ip") or "") or None,
            details=details,
        )
    except Exception:
        return


async def require_admin_viewer(
    ctx: dict[str, Any] = Depends(require_admin_context),
) -> dict[str, Any]:
    return ctx


async def require_admin_operator(
    request: Request,
    ctx: dict[str, Any] = Depends(require_admin_context),
) -> dict[str, Any]:
    if _admin_role_rank(str(ctx.get("role") or "viewer")) < _admin_role_rank("operator"):
        await _audit_admin_event(
            ctx=ctx,
            request=request,
            action="auth.forbidden",
            status="forbidden",
            status_code=403,
            details={"required_role": "operator"},
        )
        raise HTTPException(status_code=403, detail="forbidden_operator_required")
    return ctx


async def require_admin_admin(
    request: Request,
    ctx: dict[str, Any] = Depends(require_admin_context),
) -> dict[str, Any]:
    if _admin_role_rank(str(ctx.get("role") or "viewer")) < _admin_role_rank("admin"):
        await _audit_admin_event(
            ctx=ctx,
            request=request,
            action="auth.forbidden",
            status="forbidden",
            status_code=403,
            details={"required_role": "admin"},
        )
        raise HTTPException(status_code=403, detail="forbidden_admin_required")
    return ctx


async def require_admin_api_key(
    ctx: dict[str, Any] = Depends(require_admin_viewer),
) -> str:
    return str(ctx.get("token") or "")


async def require_client_api_key(
    ctx: dict[str, Any] = Depends(require_client_context),
) -> str:
    return str(ctx.get("token") or "")


def read_json_file(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"status": "no_data", "path": str(p)}
    text = p.read_text(encoding="utf-8", errors="replace")
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return {"status": "bad_json", "path": str(p)}
    if not isinstance(data, dict):
        return {"status": "bad_format", "path": str(p)}
    data.setdefault("status", "ok")
    return data


def read_text_file(path: str, *, max_bytes: int = 200_000) -> str:
    p = Path(path)
    if not p.exists():
        return f"# missing: {p}\n"
    raw = p.read_bytes()[:max_bytes]
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        return raw.decode("utf-8", errors="replace")


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _normalize_severity(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return normalized if normalized in {"good", "warn", "bad"} else "bad"


def _severity_rank(value: Any) -> int:
    levels = {"good": 0, "warn": 1, "bad": 2}
    return levels.get(_normalize_severity(value), 2)


def _build_fleet_overview(centrals: list[dict[str, Any]]) -> dict[str, Any]:
    totals: dict[str, Any] = {
        "centrals": len(centrals),
        "good": 0,
        "warn": 0,
        "bad": 0,
        "with_alerts": 0,
        "alerts_total": 0,
        "alerts_all_total": 0,
        "alerts_silenced": 0,
        "pending_batches_total": 0,
        "centrals_with_pending": 0,
        "centrals_wg_stale": 0,
        "doors_unreachable": 0,
    }
    alerts_flat: list[dict[str, Any]] = []

    for central in centrals:
        health = central.get("health") if isinstance(central.get("health"), dict) else {}
        severity = _normalize_severity(health.get("severity"))
        totals[severity] += 1

        alerts = central.get("alerts")
        if not isinstance(alerts, list):
            alerts = []
        active_alerts = [item for item in alerts if not (isinstance(item, dict) and bool(item.get("silenced")))]
        if active_alerts:
            totals["with_alerts"] += 1
        totals["alerts_all_total"] += len(alerts)
        totals["alerts_total"] += len(active_alerts)
        totals["alerts_silenced"] += max(0, len(alerts) - len(active_alerts))

        queue = central.get("queue") if isinstance(central.get("queue"), dict) else {}
        pending_batches = _safe_int(queue.get("pending_batches"), 0)
        if pending_batches > 0:
            totals["centrals_with_pending"] += 1
        totals["pending_batches_total"] += max(pending_batches, 0)

        wg_latest_handshake_age = _safe_int(queue.get("wg_latest_handshake_age_sec"), -1)
        if wg_latest_handshake_age >= 300:
            totals["centrals_wg_stale"] += 1

        doors = central.get("doors")
        if isinstance(doors, list):
            for door in doors:
                if isinstance(door, dict) and door.get("reachable") is False:
                    totals["doors_unreachable"] += 1

        for raw_alert in alerts:
            if not isinstance(raw_alert, dict):
                continue
            alerts_flat.append(
                {
                    "severity": _normalize_severity(raw_alert.get("severity")),
                    "code": str(raw_alert.get("code") or "alert"),
                    "message": str(raw_alert.get("message") or ""),
                    "central_id": str(central.get("central_id") or ""),
                    "vehicle_id": str(central.get("vehicle_id") or ""),
                    "age_sec": central.get("age_sec"),
                    "ts_received": central.get("ts_received"),
                    "silenced": bool(raw_alert.get("silenced", False)),
                    "silenced_until": raw_alert.get("silenced_until"),
                    "acked_at": raw_alert.get("acked_at"),
                    "acked_by": raw_alert.get("acked_by"),
                }
            )

    alerts_flat.sort(
        key=lambda item: (
            _severity_rank(item.get("severity")),
            _safe_int(item.get("age_sec"), -1),
            str(item.get("central_id") or ""),
        ),
        reverse=True,
    )

    if totals["centrals"] > 0:
        totals["healthy_ratio"] = round((totals["good"] / totals["centrals"]) * 100, 1)
    else:
        totals["healthy_ratio"] = 0.0

    return {
        "status": "ok",
        "ts_generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "totals": totals,
        "alerts": alerts_flat,
    }


def _filter_alerts_by_severity(alerts: list[dict[str, Any]], severity: str | None) -> list[dict[str, Any]]:
    if severity is None:
        return alerts
    normalized = str(severity).strip().lower()
    if normalized not in {"good", "warn", "bad"}:
        return alerts
    return [item for item in alerts if _normalize_severity(item.get("severity")) == normalized]


def _filter_silenced_alerts(alerts: list[dict[str, Any]], include_silenced: bool) -> list[dict[str, Any]]:
    if include_silenced:
        return alerts
    return [item for item in alerts if not bool(item.get("silenced", False))]


def _filter_alerts_by_identity(
    alerts: list[dict[str, Any]],
    *,
    central_id: str | None,
    code: str | None,
    q: str | None,
) -> list[dict[str, Any]]:
    current = alerts
    if central_id:
        central_id_norm = str(central_id).strip()
        if central_id_norm:
            current = [item for item in current if str(item.get("central_id") or "") == central_id_norm]
    if code:
        code_norm = str(code).strip()
        if code_norm:
            current = [item for item in current if str(item.get("code") or "") == code_norm]
    if q:
        query_norm = str(q).strip().lower()
        if query_norm:
            filtered: list[dict[str, Any]] = []
            for item in current:
                hay = " ".join(
                    [
                        str(item.get("central_id") or ""),
                        str(item.get("vehicle_id") or ""),
                        str(item.get("code") or ""),
                        str(item.get("message") or ""),
                        str(item.get("acked_by") or ""),
                    ]
                ).lower()
                if query_norm in hay:
                    filtered.append(item)
            current = filtered
    return current


def _parse_window_to_seconds(window: str | None) -> int:
    normalized = str(window or "24h").strip().lower()
    mapping = {
        "1h": 3600,
        "6h": 6 * 3600,
        "24h": 24 * 3600,
        "7d": 7 * 24 * 3600,
    }
    return mapping.get(normalized, 24 * 3600)


def _parse_bucket_to_seconds(bucket_sec: int | None, *, window_sec: int) -> int:
    default_bucket = 300
    parsed = _to_int(bucket_sec, default_bucket) if bucket_sec is not None else default_bucket
    parsed = max(60, min(parsed, 3600))
    max_points = 600
    min_bucket = max(60, window_sec // max_points)
    return max(parsed, min_bucket)


def _bucket_ts_iso(ts_value: str | None, *, bucket_sec: int) -> str | None:
    dt = _parse_iso_utc(ts_value)
    if dt is None:
        return None
    epoch = int(dt.timestamp())
    snapped = (epoch // bucket_sec) * bucket_sec
    return datetime.fromtimestamp(snapped, tz=timezone.utc).isoformat().replace("+00:00", "Z")


def _build_incident_totals(incidents: list[dict[str, Any]]) -> dict[str, int]:
    totals: dict[str, int] = {
        "total": len(incidents),
        "open": 0,
        "acked": 0,
        "silenced": 0,
        "resolved": 0,
        "good": 0,
        "warn": 0,
        "bad": 0,
        "sla_breached": 0,
    }
    for item in incidents:
        status_value = str(item.get("status") or "").strip().lower()
        severity_value = str(item.get("severity") or "").strip().lower()
        if status_value in totals:
            totals[status_value] += 1
        if severity_value in {"good", "warn", "bad"}:
            totals[severity_value] += 1
        if bool(item.get("sla_breached")):
            totals["sla_breached"] += 1
    return totals


def _build_attention_items(
    centrals: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
    *,
    limit: int,
    monitor_policy: dict[str, Any],
    overrides_by_central: dict[str, dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    overrides = overrides_by_central or {}

    incidents_by_central: dict[str, dict[str, int]] = {}
    for item in incidents:
        central_id = str(item.get("central_id") or "").strip()
        if not central_id:
            continue
        bucket = incidents_by_central.setdefault(
            central_id,
            {
                "open": 0,
                "bad": 0,
                "warn": 0,
                "sla_breached": 0,
            },
        )
        status_value = str(item.get("status") or "").strip().lower()
        severity_value = str(item.get("severity") or "").strip().lower()
        if status_value in {"open", "acked", "silenced"}:
            bucket["open"] += 1
        if severity_value == "bad":
            bucket["bad"] += 1
        elif severity_value == "warn":
            bucket["warn"] += 1
        if bool(item.get("sla_breached")):
            bucket["sla_breached"] += 1

    rows: list[dict[str, Any]] = []
    for central in centrals:
        central_id = str(central.get("central_id") or "").strip()
        if not central_id:
            continue
        override = overrides.get(central_id)
        warn_heartbeat_age_sec = int(override.get("warn_heartbeat_age_sec")) if isinstance(override, dict) and override.get("warn_heartbeat_age_sec") is not None else int(monitor_policy["warn_heartbeat_age_sec"])
        bad_heartbeat_age_sec = int(override.get("bad_heartbeat_age_sec")) if isinstance(override, dict) and override.get("bad_heartbeat_age_sec") is not None else int(monitor_policy["bad_heartbeat_age_sec"])
        warn_pending_batches = int(override.get("warn_pending_batches")) if isinstance(override, dict) and override.get("warn_pending_batches") is not None else int(monitor_policy["warn_pending_batches"])
        bad_pending_batches = int(override.get("bad_pending_batches")) if isinstance(override, dict) and override.get("bad_pending_batches") is not None else int(monitor_policy["bad_pending_batches"])
        warn_wg_age_sec = int(override.get("warn_wg_age_sec")) if isinstance(override, dict) and override.get("warn_wg_age_sec") is not None else int(monitor_policy["warn_wg_age_sec"])
        bad_wg_age_sec = int(override.get("bad_wg_age_sec")) if isinstance(override, dict) and override.get("bad_wg_age_sec") is not None else int(monitor_policy["bad_wg_age_sec"])
        vehicle_id = str(central.get("vehicle_id") or "")
        health = central.get("health") if isinstance(central.get("health"), dict) else {}
        severity = _normalize_severity(health.get("severity"))
        queue = central.get("queue") if isinstance(central.get("queue"), dict) else {}
        pending_batches = max(0, _to_int(queue.get("pending_batches"), 0))
        wg_age_sec = _to_int(queue.get("wg_latest_handshake_age_sec"), -1)
        heartbeat_age_sec = _to_int(central.get("age_sec"), -1)

        reasons: list[dict[str, str]] = []
        seen_codes: set[str] = set()
        raw_alerts = central.get("alerts")
        active_alerts = [
            item
            for item in (raw_alerts if isinstance(raw_alerts, list) else [])
            if isinstance(item, dict) and not bool(item.get("silenced", False))
        ]
        active_alerts.sort(key=lambda item: _severity_rank(str(item.get("severity") or "bad")), reverse=True)
        for alert in active_alerts[:3]:
            code = str(alert.get("code") or "alert")
            if code in seen_codes:
                continue
            seen_codes.add(code)
            reasons.append(
                {
                    "code": code,
                    "severity": _normalize_severity(alert.get("severity")),
                    "message": str(alert.get("message") or ""),
                }
            )

        if heartbeat_age_sec >= warn_heartbeat_age_sec and "heartbeat_stale" not in seen_codes:
            seen_codes.add("heartbeat_stale")
            reasons.append(
                {
                    "code": "heartbeat_stale",
                    "severity": "bad" if heartbeat_age_sec >= bad_heartbeat_age_sec else "warn",
                    "message": f"heartbeat age {heartbeat_age_sec}s",
                }
            )
        if wg_age_sec >= warn_wg_age_sec and "wg_handshake_stale" not in seen_codes:
            seen_codes.add("wg_handshake_stale")
            reasons.append(
                {
                    "code": "wg_handshake_stale",
                    "severity": "bad" if wg_age_sec >= bad_wg_age_sec else "warn",
                    "message": f"wireguard handshake age {wg_age_sec}s",
                }
            )
        if pending_batches >= warn_pending_batches and "pending_batches" not in seen_codes:
            seen_codes.add("pending_batches")
            reasons.append(
                {
                    "code": "pending_batches",
                    "severity": "bad" if pending_batches >= bad_pending_batches else "warn",
                    "message": f"pending batches {pending_batches}",
                }
            )

        incident_info = incidents_by_central.get(
            central_id,
            {"open": 0, "bad": 0, "warn": 0, "sla_breached": 0},
        )
        has_issue = (
            severity != "good"
            or bool(reasons)
            or incident_info["open"] > 0
            or incident_info["sla_breached"] > 0
        )
        if not has_issue:
            continue

        rows.append(
            {
                "central_id": central_id,
                "vehicle_id": vehicle_id,
                "severity": severity,
                "policy_source": "override" if isinstance(override, dict) else "global",
                "heartbeat_age_sec": heartbeat_age_sec,
                "pending_batches": pending_batches,
                "wg_latest_handshake_age_sec": wg_age_sec,
                "incidents_open": incident_info["open"],
                "incidents_bad": incident_info["bad"],
                "incidents_warn": incident_info["warn"],
                "incidents_sla_breached": incident_info["sla_breached"],
                "reasons": reasons,
            }
        )

    rows.sort(
        key=lambda item: (
            _severity_rank(item.get("severity")),
            _to_int(item.get("incidents_bad"), 0),
            _to_int(item.get("incidents_sla_breached"), 0),
            _to_int(item.get("pending_batches"), 0),
            _to_int(item.get("heartbeat_age_sec"), -1),
        ),
        reverse=True,
    )
    return rows[: max(1, min(int(limit), 100))]


def _build_monitor_state(
    *,
    fleet_totals: dict[str, Any],
    incident_totals: dict[str, int],
    notification_totals: dict[str, int],
    forbidden_total: int,
    attention: list[dict[str, Any]],
) -> dict[str, str]:
    severity = "good"
    attention_bad = False
    for row in attention:
        if _normalize_severity(row.get("severity")) == "bad":
            attention_bad = True
            break
        for reason in row.get("reasons") if isinstance(row.get("reasons"), list) else []:
            if isinstance(reason, dict) and _normalize_severity(reason.get("severity")) == "bad":
                attention_bad = True
                break
        if attention_bad:
            break

    if (
        _to_int(fleet_totals.get("bad"), 0) > 0
        or _to_int(incident_totals.get("sla_breached"), 0) > 0
        or _to_int(incident_totals.get("bad"), 0) > 0
        or attention_bad
    ):
        severity = "bad"
    elif (
        _to_int(fleet_totals.get("warn"), 0) > 0
        or _to_int(fleet_totals.get("pending_batches_total"), 0) > 0
        or _to_int(fleet_totals.get("centrals_wg_stale"), 0) > 0
        or _to_int(notification_totals.get("failed"), 0) > 0
        or forbidden_total > 0
        or bool(attention)
    ):
        severity = "warn"

    if severity == "good":
        message = "fleet healthy"
    elif severity == "warn":
        message = "attention required"
    else:
        message = "degraded fleet state"
    return {"severity": severity, "message": message}


def _normalize_monitor_policy_settings(settings: dict[str, str]) -> dict[str, Any]:
    return runtime_normalize_monitor_policy_settings(settings)


def _resolve_health_notify_channels(*, channel_mode: str, runtime: dict[str, Any]) -> list[str]:
    return runtime_resolve_health_notify_channels(channel_mode=channel_mode, runtime=runtime)


def _latest_fleet_health_auto_notification(notifications: list[dict[str, Any]]) -> dict[str, Any] | None:
    for item in notifications:
        event = str(item.get("event") or "").strip().lower()
        error = str(item.get("error") or "").strip().lower()
        if event in {"fleet_health_auto", "fleet_health_recovery"} and error != "dry_run":
            return item
    return None


async def _collect_monitor_snapshot(
    *,
    db_path: str,
    window: str,
    include_centrals: bool,
    limit_alerts: int,
    limit_attention: int,
) -> dict[str, Any]:
    return await collect_monitor_snapshot(
        db_path=db_path,
        window=window,
        include_centrals=include_centrals,
        limit_alerts=limit_alerts,
        limit_attention=limit_attention,
        list_central_heartbeats_fn=list_central_heartbeats,
        build_fleet_overview_fn=_build_fleet_overview,
        filter_silenced_alerts_fn=_filter_silenced_alerts,
        list_incidents_fn=list_incidents,
        build_incident_totals_fn=_build_incident_totals,
        parse_window_to_seconds_fn=_parse_window_to_seconds,
        list_incident_notifications_fn=list_incident_notifications,
        list_alert_actions_fn=list_alert_actions,
        list_admin_audit_fn=list_admin_audit,
        get_notification_settings_fn=get_notification_settings,
        normalize_monitor_policy_settings_fn=_normalize_monitor_policy_settings,
        list_monitor_policy_overrides_fn=list_monitor_policy_overrides,
        build_attention_items_fn=_build_attention_items,
        build_monitor_state_fn=_build_monitor_state,
    )


async def _collect_ops_feed(
    *,
    db_path: str,
    window: str,
    central_id: str | None,
    code: str | None,
    severity: str | None,
    include_resolved: bool,
    include_silenced: bool,
    q: str | None,
    limit: int,
) -> dict[str, Any]:
    now_dt = datetime.now(timezone.utc)
    window_seconds = _parse_window_to_seconds(window)
    since_dt = now_dt - timedelta(seconds=window_seconds)
    since_ts = since_dt.isoformat().replace("+00:00", "Z")
    bounded_limit = max(10, min(int(limit), 500))
    severity_filter = str(severity or "").strip().lower()
    if severity_filter not in {"good", "warn", "bad"}:
        severity_filter = ""

    incidents = await list_incidents(
        db_path,
        severity=severity_filter or None,
        central_id=central_id,
        code=code,
        q=q,
        include_resolved=bool(include_resolved),
        limit=max(bounded_limit * 4, 300),
    )

    notifications = await list_incident_notifications(
        db_path,
        central_id=central_id,
        code=code,
        since_ts=since_ts,
        q=q,
        limit=max(bounded_limit * 4, 300),
    )

    actions = await list_alert_actions(
        db_path,
        central_id=central_id,
        code=code,
        since_ts=since_ts,
        q=q,
        limit=max(bounded_limit * 4, 300),
    )

    centrals = await list_central_heartbeats(db_path)
    overview = _build_fleet_overview(centrals)
    alerts = _filter_alerts_by_severity(overview["alerts"], severity_filter or None)
    alerts = _filter_alerts_by_identity(
        alerts,
        central_id=central_id,
        code=code,
        q=q,
    )
    alerts = _filter_silenced_alerts(alerts, include_silenced)

    events: list[dict[str, Any]] = []
    for item in incidents:
        incident_status = str(item.get("status") or "open").strip().lower()
        if incident_status == "silenced" and not include_silenced:
            continue
        event_ts = str(item.get("last_seen_ts") or item.get("updated_at") or item.get("first_seen_ts") or "")
        events.append(
            {
                "ts": event_ts,
                "category": "incident",
                "severity": _normalize_severity(item.get("severity")),
                "status": incident_status or "open",
                "central_id": str(item.get("central_id") or ""),
                "vehicle_id": str(item.get("vehicle_id") or ""),
                "code": str(item.get("code") or ""),
                "message": str(item.get("message") or ""),
                "link": f"/admin/fleet/incidents/{item.get('central_id')}/{item.get('code')}",
                "meta": {
                    "age_sec": item.get("age_sec"),
                    "sla_target_sec": item.get("sla_target_sec"),
                    "sla_breached": bool(item.get("sla_breached")),
                    "occurrences": _to_int(item.get("occurrences"), 0),
                },
            }
        )

    for item in notifications:
        notification_severity = _normalize_severity(item.get("severity"))
        if severity_filter and notification_severity != severity_filter:
            continue
        events.append(
            {
                "ts": str(item.get("ts") or ""),
                "category": "notification",
                "severity": notification_severity,
                "status": str(item.get("status") or "unknown").strip().lower(),
                "central_id": str(item.get("central_id") or ""),
                "vehicle_id": "",
                "code": str(item.get("code") or ""),
                "message": str(item.get("message") or item.get("error") or ""),
                "link": f"/admin/fleet/incidents/{item.get('central_id')}/{item.get('code')}",
                "meta": {
                    "channel": str(item.get("channel") or ""),
                    "event": str(item.get("event") or ""),
                    "destination": str(item.get("destination") or ""),
                    "error": str(item.get("error") or ""),
                },
            }
        )

    for item in actions:
        action_name = str(item.get("action") or "").strip().lower()
        action_severity = "warn"
        if action_name == "ack":
            action_severity = "good"
        elif action_name == "silence":
            action_severity = "warn"
        elif action_name == "unsilence":
            action_severity = "good"
        if severity_filter and action_severity != severity_filter:
            continue
        events.append(
            {
                "ts": str(item.get("ts") or ""),
                "category": "action",
                "severity": action_severity,
                "status": action_name or "action",
                "central_id": str(item.get("central_id") or ""),
                "vehicle_id": "",
                "code": str(item.get("code") or ""),
                "message": str(item.get("note") or ""),
                "link": f"/admin/fleet/central/{item.get('central_id')}",
                "meta": {
                    "actor": str(item.get("actor") or ""),
                    "silenced_until": str(item.get("silenced_until") or ""),
                },
            }
        )

    for item in alerts:
        alert_dt = _parse_iso_utc(str(item.get("ts_received") or ""))
        if alert_dt is None:
            alert_age_sec = _to_int(item.get("age_sec"), -1)
            if alert_age_sec >= 0:
                alert_dt = now_dt - timedelta(seconds=alert_age_sec)
            else:
                alert_dt = now_dt
        if alert_dt < since_dt:
            continue
        events.append(
            {
                "ts": alert_dt.isoformat().replace("+00:00", "Z"),
                "category": "alert",
                "severity": _normalize_severity(item.get("severity")),
                "status": "silenced" if bool(item.get("silenced")) else "active",
                "central_id": str(item.get("central_id") or ""),
                "vehicle_id": str(item.get("vehicle_id") or ""),
                "code": str(item.get("code") or ""),
                "message": str(item.get("message") or ""),
                "link": f"/admin/fleet/incidents/{item.get('central_id')}/{item.get('code')}",
                "meta": {
                    "age_sec": _to_int(item.get("age_sec"), -1),
                    "acked_by": str(item.get("acked_by") or ""),
                    "silenced_until": str(item.get("silenced_until") or ""),
                },
            }
        )

    events.sort(
        key=lambda item: (
            _parse_iso_utc(str(item.get("ts") or "")) or datetime.fromtimestamp(0, tz=timezone.utc)
        ),
        reverse=True,
    )
    category_totals = {"incident": 0, "alert": 0, "notification": 0, "action": 0}
    severity_totals = {"good": 0, "warn": 0, "bad": 0}
    status_totals: dict[str, int] = {}
    for item in events:
        category_name = str(item.get("category") or "")
        severity_name = _normalize_severity(item.get("severity"))
        status_name = str(item.get("status") or "").strip().lower()
        if category_name in category_totals:
            category_totals[category_name] += 1
        if severity_name in severity_totals:
            severity_totals[severity_name] += 1
        if status_name:
            status_totals[status_name] = status_totals.get(status_name, 0) + 1

    return {
        "status": "ok",
        "ts_generated": now_dt.isoformat().replace("+00:00", "Z"),
        "window": window,
        "window_sec": window_seconds,
        "since_ts": since_ts,
        "include_resolved": bool(include_resolved),
        "include_silenced": bool(include_silenced),
        "total": len(events),
        "limit": bounded_limit,
        "events": events[:bounded_limit],
        "summary": {
            "categories": category_totals,
            "severity": severity_totals,
            "status": status_totals,
        },
        "sources": {
            "incidents_total": len(incidents),
            "alerts_total": len(alerts),
            "notifications_total": len(notifications),
            "actions_total": len(actions),
        },
    }


def _fleet_health_notification_message(snapshot: dict[str, Any], note: str | None = None) -> tuple[str, str]:
    state = snapshot.get("state") if isinstance(snapshot.get("state"), dict) else {}
    fleet = snapshot.get("fleet") if isinstance(snapshot.get("fleet"), dict) else {}
    incidents = snapshot.get("incidents") if isinstance(snapshot.get("incidents"), dict) else {}
    notifications = snapshot.get("notifications") if isinstance(snapshot.get("notifications"), dict) else {}
    security = snapshot.get("security") if isinstance(snapshot.get("security"), dict) else {}
    severity = str(state.get("severity") or "warn").strip().lower()
    subject = f"[passengers][fleet][{severity.upper()}] monitor snapshot"
    body_lines = [
        f"state={severity}",
        f"message={state.get('message') or ''}",
        f"window={snapshot.get('window') or '24h'}",
        f"ts_generated={snapshot.get('ts_generated') or ''}",
        f"centrals={fleet.get('centrals', 0)}",
        f"healthy_ratio={fleet.get('healthy_ratio', 0)}",
        f"warn={fleet.get('warn', 0)}",
        f"bad={fleet.get('bad', 0)}",
        f"pending_batches_total={fleet.get('pending_batches_total', 0)}",
        f"incidents_open={incidents.get('open', 0)}",
        f"incidents_sla_breached={incidents.get('sla_breached', 0)}",
        f"notifications_failed={notifications.get('failed', 0)}",
        f"forbidden_total={security.get('forbidden_total', 0)}",
        f"attention_total={snapshot.get('attention_total', 0)}",
        f"alerts_total={snapshot.get('alerts_total', 0)}",
    ]
    if note:
        body_lines.append(f"note={note}")
    return subject, "\n".join(body_lines) + "\n"


async def _dispatch_fleet_health_notification(
    db_path: str,
    *,
    snapshot: dict[str, Any],
    channels: list[str],
    dry_run: bool,
    event_name: str,
    note: str | None = None,
) -> dict[str, Any]:
    subject, body = _fleet_health_notification_message(snapshot, note=note)
    severity = str((snapshot.get("state") or {}).get("severity") or "warn").strip().lower()
    counters = {"sent": 0, "failed": 0, "skipped": 0}
    details: list[dict[str, Any]] = []

    for channel in channels:
        normalized = str(channel or "").strip().lower()
        if normalized not in {"telegram", "email"}:
            continue
        destination: str | None = None
        error: str | None = None
        ok = False
        if dry_run:
            status = "skipped"
            error = "dry_run"
            counters["skipped"] += 1
            if normalized == "telegram":
                destination = str(os.environ.get("ALERT_TELEGRAM_CHAT_ID", "")).strip() or None
            else:
                destination = str(os.environ.get("ALERT_EMAIL_TO", "")).strip() or None
        elif normalized == "telegram":
            ok, destination, error = _send_telegram_notification(text=body[:3900])
            if ok:
                status = "sent"
                counters["sent"] += 1
            elif error and error.endswith("not_configured"):
                status = "skipped"
                counters["skipped"] += 1
            else:
                status = "failed"
                counters["failed"] += 1
        else:
            ok, destination, error = _send_email_notification(subject=subject, body=body)
            if ok:
                status = "sent"
                counters["sent"] += 1
            elif error and error.endswith("not_configured"):
                status = "skipped"
                counters["skipped"] += 1
            else:
                status = "failed"
                counters["failed"] += 1

        details.append({"channel": normalized, "status": status, "destination": destination, "error": error})
        await record_incident_notification(
            db_path,
            central_id="fleet",
            code="fleet_health",
            severity=severity if severity in {"good", "warn", "bad"} else "warn",
            event=event_name,
            channel=normalized,
            destination=destination,
            status=status,
            message=subject,
            error=error,
        )

    return {"counters": counters, "details": details}


async def _evaluate_and_dispatch_fleet_health_auto(
    db_path: str,
    *,
    dry_run: bool,
    force: bool,
    note: str | None = None,
) -> dict[str, Any]:
    settings_raw = await get_notification_settings(db_path)
    policy = _normalize_monitor_policy_settings(settings_raw)
    enabled = bool(policy.get("fleet_health_auto_enabled"))
    window = str(policy.get("fleet_health_auto_window") or "24h")

    if not enabled and not force:
        return {
            "status": "ok",
            "enabled": False,
            "decision": "disabled",
            "reason": "fleet_health_auto_enabled=false",
            "dry_run": bool(dry_run),
            "force": bool(force),
            "policy": policy,
        }

    snapshot = await _collect_monitor_snapshot(
        db_path=db_path,
        window=window,
        include_centrals=False,
        limit_alerts=20,
        limit_attention=20,
    )
    current_severity = _normalize_severity((snapshot.get("state") or {}).get("severity"))
    min_severity = str(policy.get("fleet_health_auto_min_severity") or "bad")
    current_rank = _severity_rank(current_severity)
    threshold_rank = _severity_rank(min_severity)

    runtime = await _notification_runtime_settings(db_path)
    channel_mode = str(policy.get("fleet_health_auto_channel") or "auto")
    channels = _resolve_health_notify_channels(channel_mode=channel_mode, runtime=runtime)
    if not channels:
        return {
            "status": "ok",
            "enabled": enabled,
            "decision": "no_channels",
            "reason": f"channel_mode={channel_mode}",
            "dry_run": bool(dry_run),
            "force": bool(force),
            "policy": policy,
            "state": snapshot.get("state"),
            "channels": [],
        }

    history = await list_incident_notifications(
        db_path,
        central_id="fleet",
        code="fleet_health",
        limit=300,
    )
    last_auto = _latest_fleet_health_auto_notification(history)
    last_severity = _normalize_severity((last_auto or {}).get("severity"))
    last_ts = _parse_iso_utc(str((last_auto or {}).get("ts") or ""))
    elapsed_sec: int | None = None
    if last_ts is not None:
        elapsed_sec = max(0, int((datetime.now(timezone.utc) - last_ts).total_seconds()))
    min_interval_sec = int(policy.get("fleet_health_auto_min_interval_sec") or 900)

    decision = "skip"
    reason = "below_threshold"
    event_name = "fleet_health_auto"
    should_send = False
    currently_degraded = current_rank >= threshold_rank
    previously_degraded = (last_auto is not None) and (_severity_rank(last_severity) >= threshold_rank)

    if force:
        should_send = True
        decision = "forced"
        reason = "force=true"
    elif currently_degraded:
        if last_auto is None:
            should_send = True
            decision = "send"
            reason = "initial_degraded_state"
        elif last_severity != current_severity:
            should_send = True
            decision = "send"
            reason = f"state_changed:{last_severity}->{current_severity}"
        elif elapsed_sec is None or elapsed_sec >= min_interval_sec:
            should_send = True
            decision = "send"
            reason = f"rate_interval_elapsed:{elapsed_sec or min_interval_sec}s"
        else:
            decision = "skip"
            reason = f"rate_limited:{elapsed_sec}s<{min_interval_sec}s"
    else:
        if bool(policy.get("fleet_health_auto_notify_recovery")) and previously_degraded and last_severity != current_severity:
            should_send = True
            decision = "send"
            reason = f"recovery:{last_severity}->{current_severity}"
            event_name = "fleet_health_recovery"
        elif previously_degraded and not bool(policy.get("fleet_health_auto_notify_recovery")):
            decision = "skip"
            reason = "recovery_disabled"
        else:
            decision = "skip"
            reason = "below_threshold"

    if not should_send:
        return {
            "status": "ok",
            "enabled": enabled,
            "decision": decision,
            "reason": reason,
            "dry_run": bool(dry_run),
            "force": bool(force),
            "policy": policy,
            "state": snapshot.get("state"),
            "channels": channels,
            "last_auto": last_auto,
            "elapsed_sec": elapsed_sec,
        }

    dispatch = await _dispatch_fleet_health_notification(
        db_path,
        snapshot=snapshot,
        channels=channels,
        dry_run=bool(dry_run),
        event_name=event_name,
        note=note,
    )
    return {
        "status": "ok",
        "enabled": enabled,
        "decision": "sent" if not dry_run else "dry_run",
        "reason": reason,
        "dry_run": bool(dry_run),
        "force": bool(force),
        "policy": policy,
        "state": snapshot.get("state"),
        "channels": channels,
        "last_auto": last_auto,
        "elapsed_sec": elapsed_sec,
        "event": event_name,
        "result": dispatch,
        "snapshot": {
            "attention_total": snapshot.get("attention_total", 0),
            "alerts_total": snapshot.get("alerts_total", 0),
        },
    }


class StopGps(BaseModel):
    lat: float | None = None
    lon: float | None = None


class StopInfo(BaseModel):
    stop_id: str | None = None
    ts_start: str | None = None
    ts_end: str | None = None
    gps: StopGps | None = None


class DoorAgg(BaseModel):
    door_id: int = Field(ge=1, le=3)
    in_count: int = Field(alias="in", ge=0)
    out_count: int = Field(alias="out", ge=0)


class IngestStopPayload(BaseModel):
    schema_ver: int = 1
    vehicle_id: str = Field(min_length=1)
    batch_id: str = Field(min_length=1)
    ts_sent: str | None = None
    stop: StopInfo | None = None
    doors: list[DoorAgg] = Field(default_factory=list)


class IngestCentralHeartbeatPayload(BaseModel):
    schema_ver: int = 1
    central_id: str = Field(min_length=1)
    vehicle_id: str | None = None
    ts_sent: str | None = None
    time_sync: str | None = None
    gps: dict[str, Any] | None = None
    services: dict[str, str] = Field(default_factory=dict)
    queue: dict[str, Any] = Field(default_factory=dict)
    doors: list[dict[str, Any]] = Field(default_factory=list)


class AlertAckPayload(BaseModel):
    central_id: str = Field(min_length=1)
    code: str = Field(min_length=1)
    actor: str | None = None
    note: str | None = None


class AlertSilencePayload(BaseModel):
    central_id: str = Field(min_length=1)
    code: str = Field(min_length=1)
    duration_sec: int = Field(default=3600, ge=60, le=604800)
    actor: str | None = None
    note: str | None = None


class AlertUnsilencePayload(BaseModel):
    central_id: str = Field(min_length=1)
    code: str = Field(min_length=1)
    actor: str | None = None
    note: str | None = None


class NotificationSettingsPayload(BaseModel):
    notify_telegram: bool | None = None
    notify_email: bool | None = None
    mute_until: str | None = None
    rate_limit_sec: int | None = Field(default=None, ge=30, le=86400)
    min_severity: str | None = None
    stale_always_notify: bool | None = None
    escalation_sec: int | None = Field(default=None, ge=60, le=604800)


class NotificationTestPayload(BaseModel):
    central_id: str = Field(default="central-gw", min_length=1)
    code: str = Field(default="test_notification", min_length=1)
    severity: str = Field(default="warn")
    message: str = Field(default="manual test notification from admin ui")
    channel: str = Field(default="auto")
    dry_run: bool = False


class NotificationRetryPayload(BaseModel):
    notification_id: int = Field(ge=1)
    dry_run: bool = False


class MonitorPolicyPayload(BaseModel):
    warn_heartbeat_age_sec: int | None = Field(default=None, ge=30, le=3600)
    bad_heartbeat_age_sec: int | None = Field(default=None, ge=60, le=7200)
    warn_pending_batches: int | None = Field(default=None, ge=1, le=1000)
    bad_pending_batches: int | None = Field(default=None, ge=1, le=5000)
    warn_wg_age_sec: int | None = Field(default=None, ge=30, le=3600)
    bad_wg_age_sec: int | None = Field(default=None, ge=60, le=7200)
    fleet_health_auto_enabled: bool | None = None
    fleet_health_auto_notify_recovery: bool | None = None
    fleet_health_auto_min_interval_sec: int | None = Field(default=None, ge=60, le=86400)
    fleet_health_auto_min_severity: str | None = None
    fleet_health_auto_channel: str | None = None
    fleet_health_auto_window: str | None = None


class MonitorPolicyOverridePayload(BaseModel):
    central_id: str = Field(min_length=1)
    warn_heartbeat_age_sec: int | None = Field(default=None, ge=30, le=3600)
    bad_heartbeat_age_sec: int | None = Field(default=None, ge=60, le=7200)
    warn_pending_batches: int | None = Field(default=None, ge=1, le=1000)
    bad_pending_batches: int | None = Field(default=None, ge=1, le=5000)
    warn_wg_age_sec: int | None = Field(default=None, ge=30, le=3600)
    bad_wg_age_sec: int | None = Field(default=None, ge=60, le=7200)


class FleetHealthNotifyPayload(BaseModel):
    channel: str = Field(default="auto")
    window: str = Field(default="24h")
    dry_run: bool = Field(default=False)
    note: str | None = None


class ClientProfilePayload(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    company: str | None = Field(default=None, max_length=255)
    email: str | None = Field(default=None, max_length=255)
    phone: str | None = Field(default=None, max_length=255)
    locale: str | None = Field(default=None, max_length=16)


class ClientNotificationSettingsPayload(BaseModel):
    notify_email: bool | None = None
    notify_sms: bool | None = None
    notify_push: bool | None = None
    notify_level: str | None = Field(default=None, max_length=16)
    digest_window: str | None = Field(default=None, max_length=16)


app = FastAPI(title="Passengers Backend", version="0.1.0")

WEBPANEL_V2_DIR = Path(__file__).resolve().parent / "webpanel_v2"
app.mount("/static/v2", StaticFiles(directory=str(WEBPANEL_V2_DIR / "static")), name="static_v2")
app.include_router(webpanel_v2_router)


@app.on_event("startup")
async def _startup() -> None:
    await init_db(get_db_path())


@app.get("/health")
async def health() -> dict[str, Any]:
    return {"status": "ok"}


@app.get("/client", response_class=HTMLResponse)
async def client_home() -> str:
    return render_client_home_page()


@app.get("/client/vehicles", response_class=HTMLResponse)
async def client_vehicles() -> str:
    return render_client_vehicles_page()


@app.get("/client/tickets", response_class=HTMLResponse)
async def client_tickets() -> str:
    return render_client_tickets_page()


@app.get("/client/status", response_class=HTMLResponse)
async def client_status() -> str:
    return render_client_status_page()


@app.get("/client/profile", response_class=HTMLResponse)
async def client_profile() -> str:
    return render_client_profile_page()


@app.get("/client/notifications", response_class=HTMLResponse)
async def client_notifications() -> str:
    return render_client_notifications_page()


@app.get("/api/client/whoami")
async def client_whoami(
    _ctx: dict[str, Any] = Depends(require_client_context),
) -> dict[str, Any]:
    role = str(_ctx.get("role") or "client")
    return {
        "status": "ok",
        "actor": _ctx.get("actor"),
        "role": role,
        "scope": _ctx.get("scope"),
        "capabilities": {
            "read": True,
            "write_profile": True,
            "write_notifications": True,
            "support_console": role == "admin-support",
        },
    }


@app.get("/api/client/home")
async def client_home_data(
    _ctx: dict[str, Any] = Depends(require_client_context),
) -> dict[str, Any]:
    return await build_client_home_response(
        get_db_path(),
        scope=dict(_ctx.get("scope") or {}),
    )


@app.get("/api/client/vehicles")
async def client_vehicles_data(
    q: str | None = None,
    limit: int = 200,
    _ctx: dict[str, Any] = Depends(require_client_context),
) -> dict[str, Any]:
    return await build_client_vehicles_response(
        get_db_path(),
        scope=dict(_ctx.get("scope") or {}),
        q=q,
        limit=limit,
    )


@app.get("/api/client/tickets")
async def client_tickets_data(
    status: str | None = None,
    q: str | None = None,
    limit: int = 200,
    _ctx: dict[str, Any] = Depends(require_client_context),
) -> dict[str, Any]:
    return await build_client_tickets_response(
        get_db_path(),
        scope=dict(_ctx.get("scope") or {}),
        status=status,
        q=q,
        limit=limit,
    )


@app.get("/api/client/status")
async def client_status_data(
    limit: int = 120,
    _ctx: dict[str, Any] = Depends(require_client_context),
) -> dict[str, Any]:
    return await build_client_status_response(
        get_db_path(),
        scope=dict(_ctx.get("scope") or {}),
        limit=limit,
    )


@app.get("/api/client/profile")
async def client_profile_get(
    _ctx: dict[str, Any] = Depends(require_client_context),
) -> dict[str, Any]:
    actor = str(_ctx.get("actor") or "client")
    return await build_client_profile_response(
        get_db_path(),
        client_id=actor,
    )


@app.post("/api/client/profile")
async def client_profile_update(
    payload: ClientProfilePayload,
    _ctx: dict[str, Any] = Depends(require_client_context),
) -> dict[str, Any]:
    actor = str(_ctx.get("actor") or "client")
    return await update_client_profile_response(
        get_db_path(),
        client_id=actor,
        payload=payload.model_dump(exclude_none=True),
    )


@app.get("/api/client/notification-settings")
async def client_notification_settings_get(
    _ctx: dict[str, Any] = Depends(require_client_context),
) -> dict[str, Any]:
    actor = str(_ctx.get("actor") or "client")
    return await build_client_notification_settings_response(
        get_db_path(),
        client_id=actor,
    )


@app.post("/api/client/notification-settings")
async def client_notification_settings_update(
    payload: ClientNotificationSettingsPayload,
    _ctx: dict[str, Any] = Depends(require_client_context),
) -> dict[str, Any]:
    actor = str(_ctx.get("actor") or "client")
    return await update_client_notification_settings_response(
        get_db_path(),
        client_id=actor,
        payload=payload.model_dump(exclude_none=True),
    )


@app.get("/admin", response_class=HTMLResponse)
async def admin_index() -> str:
    return render_admin_overview_page()

@app.get("/admin/commission", response_class=HTMLResponse)
async def admin_commission_page() -> str:
    return render_admin_commission_page()


@app.get("/admin/wg", response_class=HTMLResponse)
async def admin_wg_page() -> str:
    return render_admin_wg_page()


@app.get("/admin/fleet", response_class=HTMLResponse)
async def admin_fleet_page() -> str:
    return render_admin_fleet_page()

@app.get("/admin/fleet/alerts", response_class=HTMLResponse)
async def admin_fleet_alerts_page() -> str:
    return render_admin_fleet_alerts_page()

@app.get("/admin/fleet/central/{central_id}", response_class=HTMLResponse)
async def admin_fleet_central_page(central_id: str) -> str:
    return render_admin_fleet_central_page(central_id=central_id)


@app.get("/admin/fleet/incidents", response_class=HTMLResponse)
async def admin_fleet_incidents_page() -> str:
    return render_admin_fleet_incidents_page()

@app.get("/admin/fleet/incidents/{central_id}/{code}", response_class=HTMLResponse)
async def admin_fleet_incident_detail_page(central_id: str, code: str) -> str:
    return render_admin_fleet_incident_detail_page(central_id=central_id, code=code)


@app.get("/admin/fleet/notifications", response_class=HTMLResponse)
async def admin_fleet_notifications_page() -> str:
    return render_admin_fleet_notifications_page()

@app.get("/admin/fleet/policy", response_class=HTMLResponse)
async def admin_fleet_policy_page() -> str:
    return render_admin_fleet_policy_page()

@app.get("/admin/fleet/history", response_class=HTMLResponse)
async def admin_fleet_history_page() -> str:
    return render_admin_fleet_history_page()

@app.get("/admin/fleet/notify-center", response_class=HTMLResponse)
async def admin_fleet_notify_center_page() -> str:
    return render_admin_fleet_notify_center_page()

@app.get("/admin/fleet/actions", response_class=HTMLResponse)
async def admin_fleet_actions_page() -> str:
    return render_admin_fleet_actions_page()

@app.get("/admin/audit", response_class=HTMLResponse)
async def admin_audit_page() -> str:
    return render_admin_audit_page()

@app.get("/api/admin/wg/peers")
async def admin_wg_peers(_token: str = Depends(require_admin_api_key)) -> dict[str, Any]:
    return read_json_file(get_wg_status_path())


@app.get("/api/admin/wg/conf", response_class=HTMLResponse)
async def admin_wg_conf(_token: str = Depends(require_admin_api_key)) -> str:
    return read_text_file(get_wg_conf_path())


@app.get("/api/admin/whoami")
async def admin_whoami(
    _ctx: dict[str, Any] = Depends(require_admin_viewer),
) -> dict[str, Any]:
    role = str(_ctx.get("role") or "viewer")
    capabilities = {
        "read": True,
        "operate": _admin_role_rank(role) >= _admin_role_rank("operator"),
        "admin": _admin_role_rank(role) >= _admin_role_rank("admin"),
    }
    return {
        "status": "ok",
        "actor": _ctx.get("actor"),
        "role": role,
        "capabilities": capabilities,
    }


@app.get("/api/admin/fleet/overview")
async def admin_fleet_overview(
    include_centrals: bool = False,
    severity: str | None = None,
    include_silenced: bool = False,
    central_id: str | None = None,
    code: str | None = None,
    q: str | None = None,
    limit: int = 200,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    centrals = await list_central_heartbeats(get_db_path())
    overview = _build_fleet_overview(centrals)
    filtered_alerts = _filter_alerts_by_severity(overview["alerts"], severity)
    filtered_alerts = _filter_alerts_by_identity(
        filtered_alerts,
        central_id=central_id,
        code=code,
        q=q,
    )
    filtered_alerts = _filter_silenced_alerts(filtered_alerts, include_silenced)
    bounded_limit = max(1, min(limit, 1000))
    payload: dict[str, Any] = {
        "status": "ok",
        "ts_generated": overview["ts_generated"],
        "totals": overview["totals"],
        "alerts_total": len(filtered_alerts),
        "alerts": filtered_alerts[:bounded_limit],
    }
    if include_centrals:
        payload["centrals"] = centrals
    return payload


@app.get("/api/admin/fleet/monitor")
async def admin_fleet_monitor(
    window: str = "24h",
    include_centrals: bool = False,
    limit_alerts: int = 30,
    limit_attention: int = 30,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return await _collect_monitor_snapshot(
        db_path=get_db_path(),
        window=window,
        include_centrals=include_centrals,
        limit_alerts=limit_alerts,
        limit_attention=limit_attention,
    )


@app.get("/api/admin/fleet/ops-feed")
async def admin_fleet_ops_feed(
    window: str = "24h",
    central_id: str | None = None,
    code: str | None = None,
    severity: str | None = None,
    include_resolved: bool = False,
    include_silenced: bool = False,
    q: str | None = None,
    limit: int = 120,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return await _collect_ops_feed(
        db_path=get_db_path(),
        window=window,
        central_id=central_id,
        code=code,
        severity=severity,
        include_resolved=include_resolved,
        include_silenced=include_silenced,
        q=q,
        limit=limit,
    )


@app.get("/api/admin/fleet/health")
async def admin_fleet_health(
    window: str = "24h",
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    snapshot = await _collect_monitor_snapshot(
        db_path=get_db_path(),
        window=window,
        include_centrals=False,
        limit_alerts=20,
        limit_attention=20,
    )
    return {
        "status": "ok",
        "ts_generated": snapshot.get("ts_generated"),
        "window": snapshot.get("window"),
        "window_sec": snapshot.get("window_sec"),
        "since_ts": snapshot.get("since_ts"),
        "state": snapshot.get("state"),
        "fleet": snapshot.get("fleet"),
        "incidents": snapshot.get("incidents"),
        "notifications": snapshot.get("notifications"),
        "security": snapshot.get("security"),
        "attention_total": snapshot.get("attention_total", 0),
        "alerts_total": snapshot.get("alerts_total", 0),
    }


@app.post("/api/admin/fleet/health/notify-test")
async def admin_fleet_health_notify_test(
    payload: FleetHealthNotifyPayload,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_operator),
) -> dict[str, Any]:
    channel_mode = str(payload.channel or "auto").strip().lower()
    if channel_mode not in {"auto", "telegram", "email", "all"}:
        raise HTTPException(status_code=400, detail="invalid_test_channel")

    runtime = await _notification_runtime_settings(get_db_path())
    if channel_mode == "auto":
        channels: list[str] = []
        if bool(runtime["notify_telegram"]):
            channels.append("telegram")
        if bool(runtime["notify_email"]):
            channels.append("email")
    elif channel_mode == "all":
        channels = ["telegram", "email"]
    else:
        channels = [channel_mode]

    snapshot = await _collect_monitor_snapshot(
        db_path=get_db_path(),
        window=str(payload.window or "24h"),
        include_centrals=False,
        limit_alerts=20,
        limit_attention=20,
    )
    dispatch = await _dispatch_fleet_health_notification(
        get_db_path(),
        snapshot=snapshot,
        channels=channels,
        dry_run=bool(payload.dry_run),
        event_name="fleet_health_test",
        note=str(payload.note or "").strip() or None,
    )
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="fleet.health.notify_test",
        status="ok",
        status_code=200,
        details={
            "channel_mode": channel_mode,
            "channels": channels,
            "dry_run": bool(payload.dry_run),
            "window": str(payload.window or "24h"),
        },
    )
    return {
        "status": "ok",
        "channel_mode": channel_mode,
        "channels": channels,
        "dry_run": bool(payload.dry_run),
        "snapshot": {
            "state": snapshot.get("state"),
            "attention_total": snapshot.get("attention_total", 0),
            "alerts_total": snapshot.get("alerts_total", 0),
        },
        "result": dispatch,
    }


@app.post("/api/admin/fleet/health/notify-auto")
async def admin_fleet_health_notify_auto(
    request: Request,
    dry_run: bool = False,
    force: bool = False,
    note: str | None = None,
    _ctx: dict[str, Any] = Depends(require_admin_operator),
) -> dict[str, Any]:
    result = await _evaluate_and_dispatch_fleet_health_auto(
        get_db_path(),
        dry_run=bool(dry_run),
        force=bool(force),
        note=str(note or "").strip() or None,
    )
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="fleet.health.notify_auto",
        status="ok",
        status_code=200,
        details={
            "decision": result.get("decision"),
            "reason": result.get("reason"),
            "dry_run": bool(dry_run),
            "force": bool(force),
        },
    )
    return result


@app.get("/api/admin/fleet/monitor-policy")
async def admin_fleet_monitor_policy_get(
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return await build_monitor_policy_response(
        db_path=get_db_path(),
        normalize_monitor_policy_settings=_normalize_monitor_policy_settings,
    )


@app.post("/api/admin/fleet/monitor-policy")
async def admin_fleet_monitor_policy_update(
    payload: MonitorPolicyPayload,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_admin),
) -> dict[str, Any]:
    result = await prepare_monitor_policy_update(
        db_path=get_db_path(),
        payload=payload,
        normalize_monitor_policy_settings=_normalize_monitor_policy_settings,
    )
    policy = result["policy"]
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="fleet.monitor_policy.update",
        status="ok",
        status_code=200,
        details={"updated_keys": result["updated_keys"], "policy": policy},
    )
    return {"status": "ok", "policy": policy}


@app.get("/api/admin/fleet/monitor-policy/overrides")
async def admin_fleet_monitor_policy_overrides_list(
    central_id: str | None = None,
    limit: int = 500,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return await build_monitor_policy_overrides_response(
        db_path=get_db_path(),
        central_id=central_id,
        limit=limit,
    )


@app.post("/api/admin/fleet/monitor-policy/overrides")
async def admin_fleet_monitor_policy_overrides_upsert(
    payload: MonitorPolicyOverridePayload,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_admin),
) -> dict[str, Any]:
    result = await prepare_monitor_policy_override_upsert(
        db_path=get_db_path(),
        payload=payload,
    )
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="fleet.monitor_policy.override.upsert",
        status="ok",
        status_code=200,
        details={"central_id": result["central_id"], "updated_keys": result["updated_keys"]},
    )
    return {"status": "ok", "override": result["override"]}


@app.delete("/api/admin/fleet/monitor-policy/overrides/{central_id}")
async def admin_fleet_monitor_policy_overrides_delete(
    central_id: str,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_admin),
) -> dict[str, Any]:
    result = await prepare_monitor_policy_override_delete(
        db_path=get_db_path(),
        central_id=central_id,
    )
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="fleet.monitor_policy.override.delete",
        status="ok",
        status_code=200,
        details={"central_id": result["central_id"]},
    )
    return result


@app.get("/api/admin/fleet/alerts")
async def admin_fleet_alerts(
    severity: str | None = None,
    include_silenced: bool = False,
    central_id: str | None = None,
    code: str | None = None,
    q: str | None = None,
    limit: int = 200,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    centrals = await list_central_heartbeats(get_db_path())
    overview = _build_fleet_overview(centrals)
    filtered_alerts = _filter_alerts_by_severity(overview["alerts"], severity)
    filtered_alerts = _filter_alerts_by_identity(
        filtered_alerts,
        central_id=central_id,
        code=code,
        q=q,
    )
    filtered_alerts = _filter_silenced_alerts(filtered_alerts, include_silenced)
    return build_alerts_response(
        filtered_alerts=filtered_alerts,
        ts_generated=str(overview["ts_generated"]),
        limit=limit,
    )


@app.get("/api/admin/fleet/alerts/groups")
async def admin_fleet_alert_groups(
    severity: str | None = None,
    include_silenced: bool = False,
    central_id: str | None = None,
    code: str | None = None,
    q: str | None = None,
    limit: int = 200,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    centrals = await list_central_heartbeats(get_db_path())
    overview = _build_fleet_overview(centrals)
    filtered_alerts = _filter_alerts_by_severity(overview["alerts"], severity)
    filtered_alerts = _filter_alerts_by_identity(
        filtered_alerts,
        central_id=central_id,
        code=code,
        q=q,
    )
    filtered_alerts = _filter_silenced_alerts(filtered_alerts, include_silenced)
    return build_alert_groups_response(
        filtered_alerts=filtered_alerts,
        ts_generated=str(overview["ts_generated"]),
        limit=limit,
        normalize_severity=_normalize_severity,
        severity_rank=_severity_rank,
        to_int=_to_int,
    )


@app.get("/api/admin/fleet/centrals")
async def admin_fleet_centrals(_token: str = Depends(require_admin_api_key)) -> dict[str, Any]:
    return {"status": "ok", "centrals": await list_central_heartbeats(get_db_path())}


@app.get("/api/admin/fleet/central/{central_id}")
async def admin_fleet_central_detail(
    central_id: str,
    limit: int = 120,
    actions_limit: int = 120,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    centrals = await list_central_heartbeats(get_db_path())
    current = next((item for item in centrals if str(item.get("central_id")) == central_id), None)
    history = await get_central_heartbeat_history(get_db_path(), central_id, limit=limit)
    actions = await list_alert_actions(get_db_path(), central_id=central_id, limit=actions_limit)
    if current is None and not history:
        raise HTTPException(status_code=404, detail="central_not_found")
    return {
        "status": "ok",
        "central_id": central_id,
        "central": current,
        "history": history,
        "actions": actions,
    }


@app.post("/api/admin/fleet/incidents/sync")
async def admin_fleet_incidents_sync(
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_operator),
) -> dict[str, Any]:
    centrals = await list_central_heartbeats(get_db_path())
    sync_result = await sync_incidents(get_db_path(), centrals=centrals)
    summary = {key: value for key, value in sync_result.items() if key != "notify"}
    summary["notify_total"] = len(sync_result.get("notify") or [])
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="incidents.sync",
        status="ok",
        status_code=200,
        details={"active_total": summary.get("active_total"), "notify_total": summary.get("notify_total")},
    )
    return {"status": "ok", "sync": summary}


@app.get("/api/admin/fleet/incidents")
async def admin_fleet_incidents(
    status: str | None = None,
    severity: str | None = None,
    central_id: str | None = None,
    code: str | None = None,
    q: str | None = None,
    sla_breached_only: bool = False,
    include_resolved: bool = True,
    limit: int = 200,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return await build_incidents_response(
        db_path=get_db_path(),
        status=status,
        severity=severity,
        central_id=central_id,
        code=code,
        q=q,
        sla_breached_only=sla_breached_only,
        include_resolved=include_resolved,
        limit=limit,
    )


@app.get("/api/admin/fleet/metrics/history")
async def admin_fleet_metrics_history(
    window: str = "24h",
    bucket_sec: int | None = None,
    limit_samples: int = 100_000,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    window_seconds = _parse_window_to_seconds(window)
    bucket_seconds = _parse_bucket_to_seconds(bucket_sec, window_sec=window_seconds)
    bounded_limit = max(1_000, min(int(limit_samples), 200_000))
    since_dt = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
    since_ts = since_dt.isoformat().replace("+00:00", "Z")

    samples = await list_fleet_health_history_samples(
        get_db_path(),
        since_ts=since_ts,
        limit=bounded_limit,
    )
    notifications = await list_incident_notifications(
        get_db_path(),
        since_ts=since_ts,
        limit=50_000,
    )
    actions = await list_alert_actions(
        get_db_path(),
        since_ts=since_ts,
        limit=50_000,
    )

    by_bucket: dict[str, dict[str, dict[str, Any]]] = {}
    for sample in samples:
        ts_bucket = _bucket_ts_iso(str(sample.get("ts_received") or ""), bucket_sec=bucket_seconds)
        central_id = str(sample.get("central_id") or "")
        if ts_bucket is None or not central_id:
            continue
        current = by_bucket.setdefault(ts_bucket, {})
        current[central_id] = sample

    notif_by_bucket: dict[str, dict[str, int]] = {}
    for item in notifications:
        ts_bucket = _bucket_ts_iso(str(item.get("ts") or ""), bucket_sec=bucket_seconds)
        if ts_bucket is None:
            continue
        status_map = notif_by_bucket.setdefault(ts_bucket, {"sent": 0, "failed": 0, "skipped": 0})
        normalized_status = str(item.get("status") or "").strip().lower()
        if normalized_status in status_map:
            status_map[normalized_status] += 1

    actions_by_bucket: dict[str, int] = {}
    for item in actions:
        ts_bucket = _bucket_ts_iso(str(item.get("ts") or ""), bucket_sec=bucket_seconds)
        if ts_bucket is None:
            continue
        actions_by_bucket[ts_bucket] = actions_by_bucket.get(ts_bucket, 0) + 1

    bucket_keys = sorted(set(by_bucket.keys()) | set(notif_by_bucket.keys()) | set(actions_by_bucket.keys()))
    buckets: list[dict[str, Any]] = []
    for ts_bucket in bucket_keys:
        bucket_row: dict[str, Any] = {
            "ts_bucket": ts_bucket,
            "centrals": 0,
            "good": 0,
            "warn": 0,
            "bad": 0,
            "alerts_total": 0,
            "pending_batches_total": 0,
            "wg_stale": 0,
            "notifications_sent": 0,
            "notifications_failed": 0,
            "notifications_skipped": 0,
            "alert_actions": actions_by_bucket.get(ts_bucket, 0),
        }
        central_rows = by_bucket.get(ts_bucket, {})
        bucket_row["centrals"] = len(central_rows)
        for sample in central_rows.values():
            severity = _normalize_severity(sample.get("severity"))
            bucket_row[severity] += 1
            bucket_row["alerts_total"] += max(0, _to_int(sample.get("alerts_total"), 0))
            bucket_row["pending_batches_total"] += max(0, _to_int(sample.get("pending_batches"), 0))
            if _to_int(sample.get("wg_latest_handshake_age_sec"), -1) >= 300:
                bucket_row["wg_stale"] += 1

        notif_counts = notif_by_bucket.get(ts_bucket, {})
        bucket_row["notifications_sent"] = notif_counts.get("sent", 0)
        bucket_row["notifications_failed"] = notif_counts.get("failed", 0)
        bucket_row["notifications_skipped"] = notif_counts.get("skipped", 0)
        buckets.append(bucket_row)

    return {
        "status": "ok",
        "window": window,
        "window_sec": window_seconds,
        "bucket_sec": bucket_seconds,
        "since_ts": since_ts,
        "buckets_total": len(buckets),
        "buckets": buckets,
    }


@app.get("/api/admin/fleet/incidents/{central_id}/{code}")
async def admin_fleet_incident_detail(
    central_id: str,
    code: str,
    limit: int = 120,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return await build_incident_detail_response(
        db_path=get_db_path(),
        central_id=central_id,
        code=code,
        limit=limit,
    )


@app.get("/api/admin/fleet/incidents/notifications")
async def admin_fleet_incident_notifications(
    central_id: str | None = None,
    code: str | None = None,
    channel: str | None = None,
    status: str | None = None,
    since_ts: str | None = None,
    q: str | None = None,
    limit: int = 200,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return await build_incident_notifications_response(
        db_path=get_db_path(),
        central_id=central_id,
        code=code,
        channel=channel,
        status=status,
        since_ts=since_ts,
        q=q,
        limit=limit,
    )


@app.get("/api/admin/fleet/notification-settings")
async def admin_notification_settings(
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return await build_notification_settings_response(
        db_path=get_db_path(),
        normalize_notification_settings=_normalize_notification_settings,
    )


@app.post("/api/admin/fleet/notification-settings")
async def admin_notification_settings_update(
    payload: NotificationSettingsPayload,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_admin),
) -> dict[str, Any]:
    result = await prepare_notification_settings_update(
        db_path=get_db_path(),
        payload=payload,
        parse_iso_utc=_parse_iso_utc,
        normalize_notification_settings=_normalize_notification_settings,
    )
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="notification.settings.update",
        status="ok",
        status_code=200,
        details={"updated_keys": result["updated_keys"]},
    )
    return {
        "status": "ok",
        "settings": result["settings"],
    }


@app.post("/api/admin/fleet/notification-settings/test")
async def admin_notification_settings_test(
    payload: NotificationTestPayload,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_operator),
) -> dict[str, Any]:
    result = await prepare_notification_test(
        db_path=get_db_path(),
        payload=payload,
        notification_runtime_settings=_notification_runtime_settings,
        dispatch_test_notification=_dispatch_test_notification,
    )
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="notification.test",
        status="ok",
        status_code=200,
        details=result["audit_details"],
    )
    return {key: value for key, value in result.items() if key != "audit_details"}


@app.post("/api/admin/fleet/notifications/retry")
async def admin_fleet_incident_notification_retry(
    payload: NotificationRetryPayload,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_operator),
) -> dict[str, Any]:
    result = await prepare_notification_retry(
        db_path=get_db_path(),
        payload=payload,
        dispatch_test_notification=_dispatch_test_notification,
    )
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="notification.retry",
        status="ok",
        status_code=200,
        details=result["audit_details"],
    )
    return {key: value for key, value in result.items() if key != "audit_details"}


@app.get("/api/admin/audit")
async def admin_audit_list(
    actor: str | None = None,
    role: str | None = None,
    action: str | None = None,
    path: str | None = None,
    status: str | None = None,
    since_ts: str | None = None,
    q: str | None = None,
    limit: int = 500,
    _ctx: dict[str, Any] = Depends(require_admin_admin),
) -> dict[str, Any]:
    return await build_admin_audit_response(
        db_path=get_db_path(),
        actor=actor,
        role=role,
        action=action,
        path=path,
        status=status,
        since_ts=since_ts,
        q=q,
        limit=limit,
    )


@app.get("/api/admin/fleet/alerts/actions")
async def admin_alert_actions(
    central_id: str | None = None,
    code: str | None = None,
    action: str | None = None,
    since_ts: str | None = None,
    q: str | None = None,
    limit: int = 200,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return await build_alert_actions_response(
        db_path=get_db_path(),
        central_id=central_id,
        code=code,
        action=action,
        since_ts=since_ts,
        q=q,
        limit=limit,
    )


@app.post("/api/admin/fleet/alerts/ack")
async def admin_alert_ack(
    payload: AlertAckPayload,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_operator),
) -> dict[str, Any]:
    state = await set_alert_ack(
        get_db_path(),
        central_id=payload.central_id,
        code=payload.code,
        actor=payload.actor,
        note=payload.note,
    )
    incident_sync = await sync_incidents(get_db_path())
    sync_summary = {key: value for key, value in incident_sync.items() if key != "notify"}
    sync_summary["notify_total"] = len(incident_sync.get("notify") or [])
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="alerts.ack",
        status="ok",
        status_code=200,
        details={"central_id": payload.central_id, "code": payload.code, "actor": payload.actor},
    )
    return {"status": "ok", "state": state, "incidents": sync_summary}


@app.post("/api/admin/fleet/alerts/silence")
async def admin_alert_silence(
    payload: AlertSilencePayload,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_operator),
) -> dict[str, Any]:
    state = await set_alert_silence(
        get_db_path(),
        central_id=payload.central_id,
        code=payload.code,
        duration_sec=payload.duration_sec,
        actor=payload.actor,
        note=payload.note,
    )
    incident_sync = await sync_incidents(get_db_path())
    sync_summary = {key: value for key, value in incident_sync.items() if key != "notify"}
    sync_summary["notify_total"] = len(incident_sync.get("notify") or [])
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="alerts.silence",
        status="ok",
        status_code=200,
        details={
            "central_id": payload.central_id,
            "code": payload.code,
            "duration_sec": payload.duration_sec,
            "actor": payload.actor,
        },
    )
    return {"status": "ok", "state": state, "incidents": sync_summary}


@app.post("/api/admin/fleet/alerts/unsilence")
async def admin_alert_unsilence(
    payload: AlertUnsilencePayload,
    request: Request,
    _ctx: dict[str, Any] = Depends(require_admin_operator),
) -> dict[str, Any]:
    state = await clear_alert_silence(
        get_db_path(),
        central_id=payload.central_id,
        code=payload.code,
        actor=payload.actor,
        note=payload.note,
    )
    incident_sync = await sync_incidents(get_db_path())
    sync_summary = {key: value for key, value in incident_sync.items() if key != "notify"}
    sync_summary["notify_total"] = len(incident_sync.get("notify") or [])
    await _audit_admin_event(
        ctx=_ctx,
        request=request,
        action="alerts.unsilence",
        status="ok",
        status_code=200,
        details={"central_id": payload.central_id, "code": payload.code, "actor": payload.actor},
    )
    return {"status": "ok", "state": state, "incidents": sync_summary}


@app.get("/api/admin/fleet/alerts/state/{central_id}/{code}")
async def admin_alert_state(
    central_id: str,
    code: str,
    _token: str = Depends(require_admin_api_key),
) -> dict[str, Any]:
    return {"status": "ok", "state": await get_alert_state(get_db_path(), central_id=central_id, code=code)}


@app.post("/api/v1/ingest/stops")
async def ingest_stops(
    payload: IngestStopPayload,
    _token: str = Depends(require_api_key),
) -> dict[str, Any]:
    normalized_payload = payload.model_dump(by_alias=True)
    result = await ingest_stop(get_db_path(), normalized_payload)
    return {"status": result.status, "ts_received": result.ts_received}


@app.post("/api/v1/ingest/central-heartbeat")
async def ingest_central_heartbeat_state(
    payload: IngestCentralHeartbeatPayload,
    _token: str = Depends(require_api_key),
) -> dict[str, Any]:
    normalized_payload = payload.model_dump(by_alias=True)
    result = await ingest_central_heartbeat(get_db_path(), normalized_payload)
    centrals = await list_central_heartbeats(get_db_path())
    incident_sync = await sync_incidents(get_db_path(), centrals=centrals)
    notifications = await _dispatch_incident_notifications(get_db_path(), incident_sync.get("notify") or [])
    sync_summary = {key: value for key, value in incident_sync.items() if key != "notify"}
    sync_summary["notify_total"] = len(incident_sync.get("notify") or [])
    return {
        "status": result.status,
        "ts_received": result.ts_received,
        "incidents": sync_summary,
        "notifications": notifications,
    }


@app.get("/api/v1/stats/vehicle/{vehicle_id}")
async def stats_vehicle_total(
    vehicle_id: str,
    _token: str = Depends(require_api_key),
) -> dict[str, Any]:
    return await stats_vehicle(get_db_path(), vehicle_id)
