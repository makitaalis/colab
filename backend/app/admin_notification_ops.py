from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Awaitable, Callable

from fastapi import HTTPException

from app.db import get_incident_notification_by_id, get_notification_settings, update_notification_settings


async def build_notification_settings_response(
    *,
    db_path: str,
    normalize_notification_settings: Callable[[dict[str, str]], dict[str, Any]],
) -> dict[str, Any]:
    settings = await get_notification_settings(db_path)
    return {
        "status": "ok",
        "ts_generated": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "settings": normalize_notification_settings(settings),
    }


async def prepare_notification_settings_update(
    *,
    db_path: str,
    payload: Any,
    parse_iso_utc: Callable[[str | None], datetime | None],
    normalize_notification_settings: Callable[[dict[str, str]], dict[str, Any]],
) -> dict[str, Any]:
    updates: dict[str, str] = {}
    if payload.notify_telegram is not None:
        updates["notify_telegram"] = "1" if payload.notify_telegram else "0"
    if payload.notify_email is not None:
        updates["notify_email"] = "1" if payload.notify_email else "0"
    if payload.mute_until is not None:
        value = str(payload.mute_until).strip()
        if value:
            if parse_iso_utc(value) is None:
                raise HTTPException(status_code=400, detail="invalid_mute_until_iso")
            updates["mute_until"] = value
        else:
            updates["mute_until"] = ""
    if payload.rate_limit_sec is not None:
        updates["rate_limit_sec"] = str(max(30, min(int(payload.rate_limit_sec), 86400)))
    if payload.escalation_sec is not None:
        updates["escalation_sec"] = str(max(60, min(int(payload.escalation_sec), 604800)))
    if payload.min_severity is not None:
        severity = str(payload.min_severity).strip().lower()
        if severity not in {"good", "warn", "bad"}:
            raise HTTPException(status_code=400, detail="invalid_min_severity")
        updates["min_severity"] = severity
    if payload.stale_always_notify is not None:
        updates["stale_always_notify"] = "1" if payload.stale_always_notify else "0"

    settings = await update_notification_settings(db_path, updates=updates)
    return {
        "settings": normalize_notification_settings(settings),
        "updated_keys": sorted(list(updates.keys())),
    }


async def prepare_notification_test(
    *,
    db_path: str,
    payload: Any,
    notification_runtime_settings: Callable[[str], Awaitable[dict[str, Any]]],
    dispatch_test_notification: Callable[..., Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    severity = str(payload.severity or "warn").strip().lower()
    if severity not in {"good", "warn", "bad"}:
        raise HTTPException(status_code=400, detail="invalid_test_severity")

    runtime = await notification_runtime_settings(db_path)
    channel_mode = str(payload.channel or "auto").strip().lower()
    if channel_mode not in {"auto", "telegram", "email", "all"}:
        raise HTTPException(status_code=400, detail="invalid_test_channel")

    if channel_mode == "auto":
        channels: list[str] = []
        if bool(runtime.get("notify_telegram")):
            channels.append("telegram")
        if bool(runtime.get("notify_email")):
            channels.append("email")
    elif channel_mode == "all":
        channels = ["telegram", "email"]
    else:
        channels = [channel_mode]

    incident = {
        "event": "test",
        "severity": severity,
        "central_id": str(payload.central_id),
        "vehicle_id": "test_vehicle",
        "code": str(payload.code),
        "status": "open",
        "first_seen_ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "message": str(payload.message or "manual test notification"),
    }
    dispatch = await dispatch_test_notification(
        db_path,
        incident=incident,
        channels=channels,
        dry_run=bool(payload.dry_run),
        event_name="test",
    )
    return {
        "status": "ok",
        "channel_mode": channel_mode,
        "channels": channels,
        "dry_run": bool(payload.dry_run),
        "result": dispatch,
        "audit_details": {
            "central_id": payload.central_id,
            "code": payload.code,
            "channel_mode": channel_mode,
            "dry_run": bool(payload.dry_run),
            "channels": channels,
        },
    }


async def prepare_notification_retry(
    *,
    db_path: str,
    payload: Any,
    dispatch_test_notification: Callable[..., Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    notification_id = int(payload.notification_id)
    source = await get_incident_notification_by_id(
        db_path,
        notification_id=notification_id,
    )
    if source is None:
        raise HTTPException(status_code=404, detail="notification_not_found")

    channel = str(source.get("channel") or "").strip().lower()
    if channel not in {"telegram", "email"}:
        raise HTTPException(status_code=400, detail="retry_channel_not_supported")

    incident = {
        "event": "retry_manual",
        "severity": str(source.get("severity") or "warn"),
        "central_id": str(source.get("central_id") or ""),
        "vehicle_id": "manual_retry",
        "code": str(source.get("code") or "alert"),
        "status": "open",
        "first_seen_ts": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "message": str(source.get("message") or source.get("error") or f"manual retry for notification #{notification_id}"),
    }
    dispatch = await dispatch_test_notification(
        db_path,
        incident=incident,
        channels=[channel],
        dry_run=bool(payload.dry_run),
        event_name="retry_manual",
    )
    return {
        "status": "ok",
        "source": source,
        "dry_run": bool(payload.dry_run),
        "result": dispatch,
        "audit_details": {
            "notification_id": notification_id,
            "channel": channel,
            "dry_run": bool(payload.dry_run),
        },
    }
