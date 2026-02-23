from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable


async def collect_monitor_snapshot(
    *,
    db_path: str,
    window: str,
    include_centrals: bool,
    limit_alerts: int,
    limit_attention: int,
    list_central_heartbeats_fn: Callable[[str], Awaitable[list[dict[str, Any]]]],
    build_fleet_overview_fn: Callable[[list[dict[str, Any]]], dict[str, Any]],
    filter_silenced_alerts_fn: Callable[[list[dict[str, Any]], bool], list[dict[str, Any]]],
    list_incidents_fn: Callable[..., Awaitable[list[dict[str, Any]]]],
    build_incident_totals_fn: Callable[[list[dict[str, Any]]], dict[str, int]],
    parse_window_to_seconds_fn: Callable[[str | None], int],
    list_incident_notifications_fn: Callable[..., Awaitable[list[dict[str, Any]]]],
    list_alert_actions_fn: Callable[..., Awaitable[list[dict[str, Any]]]],
    list_admin_audit_fn: Callable[..., Awaitable[list[dict[str, Any]]]],
    get_notification_settings_fn: Callable[[str], Awaitable[dict[str, str]]],
    normalize_monitor_policy_settings_fn: Callable[[dict[str, str]], dict[str, Any]],
    list_monitor_policy_overrides_fn: Callable[..., Awaitable[list[dict[str, Any]]]],
    build_attention_items_fn: Callable[..., list[dict[str, Any]]],
    build_monitor_state_fn: Callable[..., dict[str, str]],
) -> dict[str, Any]:
    centrals = await list_central_heartbeats_fn(db_path)
    overview = build_fleet_overview_fn(centrals)
    active_alerts = filter_silenced_alerts_fn(overview["alerts"], False)
    bounded_alerts_limit = max(1, min(int(limit_alerts), 200))

    incidents = await list_incidents_fn(
        db_path,
        include_resolved=False,
        limit=2000,
    )
    incident_totals = build_incident_totals_fn(incidents)

    window_seconds = parse_window_to_seconds_fn(window)
    since_dt = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
    since_ts = since_dt.isoformat().replace("+00:00", "Z")

    notifications = await list_incident_notifications_fn(
        db_path,
        since_ts=since_ts,
        limit=5000,
    )
    notification_totals = {"sent": 0, "failed": 0, "skipped": 0}
    for item in notifications:
        key = str(item.get("status") or "").strip().lower()
        if key in notification_totals:
            notification_totals[key] += 1

    actions = await list_alert_actions_fn(
        db_path,
        since_ts=since_ts,
        limit=5000,
    )
    forbidden = await list_admin_audit_fn(
        db_path,
        status="forbidden",
        since_ts=since_ts,
        limit=5000,
    )

    settings_raw = await get_notification_settings_fn(db_path)
    monitor_policy = normalize_monitor_policy_settings_fn(settings_raw)
    monitor_policy_overrides = await list_monitor_policy_overrides_fn(db_path, limit=5000)
    overrides_map = {
        str(item.get("central_id") or ""): item
        for item in monitor_policy_overrides
        if str(item.get("central_id") or "")
    }
    attention = build_attention_items_fn(
        centrals,
        incidents,
        limit=limit_attention,
        monitor_policy=monitor_policy,
        overrides_by_central=overrides_map,
    )
    state = build_monitor_state_fn(
        fleet_totals=overview["totals"],
        incident_totals=incident_totals,
        notification_totals=notification_totals,
        forbidden_total=len(forbidden),
        attention=attention,
    )
    payload: dict[str, Any] = {
        "status": "ok",
        "ts_generated": overview["ts_generated"],
        "window": window,
        "window_sec": window_seconds,
        "since_ts": since_ts,
        "state": state,
        "fleet": overview["totals"],
        "incidents": incident_totals,
        "notifications": {
            "window_sec": window_seconds,
            "total": len(notifications),
            "sent": notification_totals["sent"],
            "failed": notification_totals["failed"],
            "skipped": notification_totals["skipped"],
        },
        "actions": {
            "window_sec": window_seconds,
            "total": len(actions),
        },
        "security": {
            "window_sec": window_seconds,
            "forbidden_total": len(forbidden),
        },
        "monitor_policy": monitor_policy,
        "monitor_policy_overrides_total": len(monitor_policy_overrides),
        "attention_total": len(attention),
        "attention": attention,
        "alerts_total": len(active_alerts),
        "alerts": active_alerts[:bounded_alerts_limit],
    }
    if include_centrals:
        payload["centrals"] = centrals
    return payload
