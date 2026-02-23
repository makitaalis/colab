from __future__ import annotations

from typing import Any

from fastapi import HTTPException

from app.db import (
    get_central_heartbeat_history,
    get_incident_by_key,
    list_alert_actions,
    list_central_heartbeats,
    list_incident_notifications,
    list_incidents,
    sync_incidents,
)


def _sync_summary(sync_result: dict[str, Any]) -> dict[str, Any]:
    summary = {key: value for key, value in sync_result.items() if key != "notify"}
    summary["notify_total"] = len(sync_result.get("notify") or [])
    return summary


async def build_incidents_response(
    *,
    db_path: str,
    status: str | None,
    severity: str | None,
    central_id: str | None,
    code: str | None,
    q: str | None,
    sla_breached_only: bool,
    include_resolved: bool,
    limit: int,
) -> dict[str, Any]:
    centrals = await list_central_heartbeats(db_path)
    sync_result = await sync_incidents(db_path, centrals=centrals)
    incidents = await list_incidents(
        db_path,
        status=status,
        severity=severity,
        central_id=central_id,
        code=code,
        q=q,
        include_resolved=include_resolved,
        limit=limit,
    )
    if sla_breached_only:
        incidents = [item for item in incidents if bool(item.get("sla_breached"))]

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
        status_value = str(item.get("status") or "")
        severity_value = str(item.get("severity") or "")
        if status_value in totals:
            totals[status_value] += 1
        if severity_value in {"good", "warn", "bad"}:
            totals[severity_value] += 1
        if bool(item.get("sla_breached")):
            totals["sla_breached"] += 1

    return {
        "status": "ok",
        "totals": totals,
        "incidents": incidents,
        "sync": _sync_summary(sync_result),
    }


async def build_incident_detail_response(
    *,
    db_path: str,
    central_id: str,
    code: str,
    limit: int,
) -> dict[str, Any]:
    centrals = await list_central_heartbeats(db_path)
    sync_result = await sync_incidents(db_path, centrals=centrals)
    incident = await get_incident_by_key(db_path, central_id=central_id, code=code)
    if incident is None:
        raise HTTPException(status_code=404, detail="incident_not_found")

    bounded_limit = max(1, min(int(limit), 1000))
    actions = await list_alert_actions(db_path, central_id=central_id, code=code, limit=bounded_limit)
    notifications = await list_incident_notifications(db_path, central_id=central_id, code=code, limit=bounded_limit)
    history = await get_central_heartbeat_history(db_path, central_id=central_id, limit=bounded_limit)

    history_hits: list[dict[str, Any]] = []
    for row in history:
        alerts = row.get("alerts") if isinstance(row.get("alerts"), list) else []
        matched = next((item for item in alerts if str(item.get("code") or "") == code), None)
        if matched is None:
            continue
        history_hits.append(
            {
                "ts_received": row.get("ts_received"),
                "age_sec": row.get("age_sec"),
                "severity": matched.get("severity"),
                "message": matched.get("message"),
            }
        )

    return {
        "status": "ok",
        "central_id": central_id,
        "code": code,
        "incident": incident,
        "actions": actions,
        "notifications": notifications,
        "history_hits": history_hits,
        "sync": _sync_summary(sync_result),
    }


async def build_incident_notifications_response(
    *,
    db_path: str,
    central_id: str | None,
    code: str | None,
    channel: str | None,
    status: str | None,
    since_ts: str | None,
    q: str | None,
    limit: int,
) -> dict[str, Any]:
    notifications = await list_incident_notifications(
        db_path,
        central_id=central_id,
        code=code,
        channel=channel,
        status=status,
        since_ts=since_ts,
        q=q,
        limit=limit,
    )
    return {"status": "ok", "total": len(notifications), "notifications": notifications}


async def build_alert_actions_response(
    *,
    db_path: str,
    central_id: str | None,
    code: str | None,
    action: str | None,
    since_ts: str | None,
    q: str | None,
    limit: int,
) -> dict[str, Any]:
    actions = await list_alert_actions(
        db_path,
        central_id=central_id,
        code=code,
        action=action,
        since_ts=since_ts,
        q=q,
        limit=limit,
    )
    return {"status": "ok", "total": len(actions), "actions": actions}
