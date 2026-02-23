from __future__ import annotations

from typing import Any, Callable

from fastapi import HTTPException

from app.db import (
    delete_monitor_policy_override,
    get_monitor_policy_override,
    get_notification_settings,
    list_monitor_policy_overrides,
    update_notification_settings,
    upsert_monitor_policy_override,
)


async def build_monitor_policy_response(
    *,
    db_path: str,
    normalize_monitor_policy_settings: Callable[[dict[str, str]], dict[str, Any]],
) -> dict[str, Any]:
    settings = await get_notification_settings(db_path)
    return {
        "status": "ok",
        "policy": normalize_monitor_policy_settings(settings),
    }


async def prepare_monitor_policy_update(
    *,
    db_path: str,
    payload: Any,
    normalize_monitor_policy_settings: Callable[[dict[str, str]], dict[str, Any]],
) -> dict[str, Any]:
    updates: dict[str, str] = {}
    if payload.warn_heartbeat_age_sec is not None:
        updates["monitor_warn_heartbeat_age_sec"] = str(max(30, min(int(payload.warn_heartbeat_age_sec), 3600)))
    if payload.bad_heartbeat_age_sec is not None:
        updates["monitor_bad_heartbeat_age_sec"] = str(max(60, min(int(payload.bad_heartbeat_age_sec), 7200)))
    if payload.warn_pending_batches is not None:
        updates["monitor_warn_pending_batches"] = str(max(1, min(int(payload.warn_pending_batches), 1000)))
    if payload.bad_pending_batches is not None:
        updates["monitor_bad_pending_batches"] = str(max(1, min(int(payload.bad_pending_batches), 5000)))
    if payload.warn_wg_age_sec is not None:
        updates["monitor_warn_wg_age_sec"] = str(max(30, min(int(payload.warn_wg_age_sec), 3600)))
    if payload.bad_wg_age_sec is not None:
        updates["monitor_bad_wg_age_sec"] = str(max(60, min(int(payload.bad_wg_age_sec), 7200)))
    if payload.fleet_health_auto_enabled is not None:
        updates["fleet_health_auto_enabled"] = "1" if payload.fleet_health_auto_enabled else "0"
    if payload.fleet_health_auto_notify_recovery is not None:
        updates["fleet_health_auto_notify_recovery"] = "1" if payload.fleet_health_auto_notify_recovery else "0"
    if payload.fleet_health_auto_min_interval_sec is not None:
        updates["fleet_health_auto_min_interval_sec"] = str(max(60, min(int(payload.fleet_health_auto_min_interval_sec), 86400)))
    if payload.fleet_health_auto_min_severity is not None:
        normalized = str(payload.fleet_health_auto_min_severity).strip().lower()
        if normalized not in {"good", "warn", "bad"}:
            raise HTTPException(status_code=400, detail="invalid_fleet_health_auto_min_severity")
        updates["fleet_health_auto_min_severity"] = normalized
    if payload.fleet_health_auto_channel is not None:
        channel_mode = str(payload.fleet_health_auto_channel).strip().lower()
        if channel_mode not in {"auto", "telegram", "email", "all"}:
            raise HTTPException(status_code=400, detail="invalid_fleet_health_auto_channel")
        updates["fleet_health_auto_channel"] = channel_mode
    if payload.fleet_health_auto_window is not None:
        window = str(payload.fleet_health_auto_window).strip().lower()
        if window not in {"1h", "6h", "24h", "7d"}:
            raise HTTPException(status_code=400, detail="invalid_fleet_health_auto_window")
        updates["fleet_health_auto_window"] = window

    settings = await update_notification_settings(db_path, updates=updates)
    policy = normalize_monitor_policy_settings(settings)
    return {"policy": policy, "updated_keys": sorted(list(updates.keys()))}


async def build_monitor_policy_overrides_response(
    *,
    db_path: str,
    central_id: str | None,
    limit: int,
) -> dict[str, Any]:
    rows = await list_monitor_policy_overrides(
        db_path,
        central_id=central_id,
        limit=limit,
    )
    return {
        "status": "ok",
        "total": len(rows),
        "overrides": rows,
    }


async def prepare_monitor_policy_override_upsert(
    *,
    db_path: str,
    payload: Any,
) -> dict[str, Any]:
    central_id = str(payload.central_id or "").strip()
    if not central_id:
        raise HTTPException(status_code=400, detail="invalid_central_id")

    updates: dict[str, int | None] = {}
    if payload.warn_heartbeat_age_sec is not None:
        updates["warn_heartbeat_age_sec"] = max(30, min(int(payload.warn_heartbeat_age_sec), 3600))
    if payload.bad_heartbeat_age_sec is not None:
        updates["bad_heartbeat_age_sec"] = max(60, min(int(payload.bad_heartbeat_age_sec), 7200))
    if payload.warn_pending_batches is not None:
        updates["warn_pending_batches"] = max(1, min(int(payload.warn_pending_batches), 1000))
    if payload.bad_pending_batches is not None:
        updates["bad_pending_batches"] = max(1, min(int(payload.bad_pending_batches), 5000))
    if payload.warn_wg_age_sec is not None:
        updates["warn_wg_age_sec"] = max(30, min(int(payload.warn_wg_age_sec), 3600))
    if payload.bad_wg_age_sec is not None:
        updates["bad_wg_age_sec"] = max(60, min(int(payload.bad_wg_age_sec), 7200))
    if not updates:
        raise HTTPException(status_code=400, detail="no_override_fields")

    current = await get_monitor_policy_override(db_path, central_id=central_id)
    warn_hb = updates.get("warn_heartbeat_age_sec")
    if warn_hb is None and isinstance(current, dict):
        warn_hb = current.get("warn_heartbeat_age_sec")
    bad_hb = updates.get("bad_heartbeat_age_sec")
    if bad_hb is None and isinstance(current, dict):
        bad_hb = current.get("bad_heartbeat_age_sec")
    if warn_hb is not None and bad_hb is not None and int(bad_hb) <= int(warn_hb):
        updates["bad_heartbeat_age_sec"] = min(7200, int(warn_hb) + 30)

    warn_pending = updates.get("warn_pending_batches")
    if warn_pending is None and isinstance(current, dict):
        warn_pending = current.get("warn_pending_batches")
    bad_pending = updates.get("bad_pending_batches")
    if bad_pending is None and isinstance(current, dict):
        bad_pending = current.get("bad_pending_batches")
    if warn_pending is not None and bad_pending is not None and int(bad_pending) <= int(warn_pending):
        updates["bad_pending_batches"] = min(5000, int(warn_pending) + 1)

    warn_wg = updates.get("warn_wg_age_sec")
    if warn_wg is None and isinstance(current, dict):
        warn_wg = current.get("warn_wg_age_sec")
    bad_wg = updates.get("bad_wg_age_sec")
    if bad_wg is None and isinstance(current, dict):
        bad_wg = current.get("bad_wg_age_sec")
    if warn_wg is not None and bad_wg is not None and int(bad_wg) <= int(warn_wg):
        updates["bad_wg_age_sec"] = min(7200, int(warn_wg) + 30)

    row = await upsert_monitor_policy_override(
        db_path,
        central_id=central_id,
        values=updates,
    )
    return {
        "status": "ok",
        "override": row,
        "central_id": central_id,
        "updated_keys": sorted(list(updates.keys())),
    }


async def prepare_monitor_policy_override_delete(
    *,
    db_path: str,
    central_id: str,
) -> dict[str, Any]:
    normalized = str(central_id or "").strip()
    if not normalized:
        raise HTTPException(status_code=400, detail="invalid_central_id")
    deleted = await delete_monitor_policy_override(db_path, central_id=normalized)
    if not deleted:
        raise HTTPException(status_code=404, detail="override_not_found")
    return {"status": "ok", "deleted": True, "central_id": normalized}
