from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.db import (
    get_client_notification_settings,
    get_client_profile,
    list_central_heartbeats,
    list_incidents,
    upsert_client_notification_settings,
    upsert_client_profile,
)


def _parse_iso_utc(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except Exception:
        return None


def _normalize_scope_ids(raw_values: Any) -> set[str]:
    if isinstance(raw_values, (list, tuple, set)):
        values = raw_values
    elif raw_values is None:
        values = []
    else:
        values = [raw_values]
    result: set[str] = set()
    for item in values:
        value = str(item or "").strip()
        if value:
            result.add(value)
    return result


def _matches_scope(
    *,
    central_id: str | None,
    vehicle_id: str | None,
    central_ids: set[str],
    vehicle_ids: set[str],
) -> bool:
    central_value = str(central_id or "").strip()
    vehicle_value = str(vehicle_id or "").strip()
    if central_ids and central_value not in central_ids:
        return False
    if vehicle_ids and vehicle_value not in vehicle_ids:
        return False
    return True


def _scope_filter(
    rows: list[dict[str, Any]],
    *,
    central_ids: set[str],
    vehicle_ids: set[str],
) -> list[dict[str, Any]]:
    filtered: list[dict[str, Any]] = []
    for item in rows:
        if not isinstance(item, dict):
            continue
        if _matches_scope(
            central_id=str(item.get("central_id") or ""),
            vehicle_id=str(item.get("vehicle_id") or ""),
            central_ids=central_ids,
            vehicle_ids=vehicle_ids,
        ):
            filtered.append(item)
    return filtered


def _ticket_status_from_incident(status_value: str) -> str:
    normalized = str(status_value or "").strip().lower()
    if normalized == "resolved":
        return "resolved"
    if normalized == "acked":
        return "in_progress"
    return "open"


def _severity_rank(value: str) -> int:
    normalized = str(value or "").strip().lower()
    mapping = {"good": 0, "warn": 1, "bad": 2}
    return mapping.get(normalized, 2)


def _incident_impact_rank(value: str) -> int:
    normalized = str(value or "").strip().lower()
    mapping = {
        "ok": 0,
        "good": 0,
        "warn": 1,
        "risk": 2,
        "bad": 2,
    }
    return mapping.get(normalized, 1)


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, int):
            return value
        if isinstance(value, float):
            return int(value)
        raw = str(value).strip()
        if not raw:
            return default
        if "." in raw:
            return int(float(raw))
        return int(raw)
    except Exception:
        return default


def _estimate_eta_delay_min(*, severity: str, pending_batches: int, bad_incidents: int, warn_incidents: int) -> int:
    base = 0
    normalized = str(severity or "good").strip().lower()
    if normalized == "bad":
        base = 8
    elif normalized == "warn":
        base = 3
    pending_component = min(20, max(0, pending_batches) * 2)
    incident_component = max(0, bad_incidents) * 4 + max(0, warn_incidents) * 2
    return max(0, min(45, base + pending_component + incident_component))


def _resolve_sla_state(*, severity: str, pending_batches: int, bad_incidents: int, warn_incidents: int) -> str:
    normalized = str(severity or "good").strip().lower()
    if normalized == "bad" or bad_incidents > 0:
        return "risk"
    if normalized == "warn" or pending_batches >= 3 or warn_incidents > 0:
        return "warn"
    return "ok"


def _build_vehicle_rows(
    *,
    centrals: list[dict[str, Any]],
    incidents: list[dict[str, Any]],
    q: str | None,
) -> list[dict[str, Any]]:
    incidents_by_central: dict[str, dict[str, int]] = {}
    for item in incidents:
        central_id = str(item.get("central_id") or "").strip()
        if not central_id:
            continue
        bucket = incidents_by_central.setdefault(central_id, {"bad": 0, "warn": 0})
        incident_severity = str(item.get("severity") or "warn").strip().lower()
        if incident_severity == "bad":
            bucket["bad"] += 1
        elif incident_severity == "warn":
            bucket["warn"] += 1

    query_text = str(q or "").strip().lower()
    rows: list[dict[str, Any]] = []
    for central in centrals:
        severity = str(((central.get("health") or {}).get("severity")) or "good").strip().lower()
        if severity not in {"good", "warn", "bad"}:
            severity = "bad"

        vehicle_id = str(central.get("vehicle_id") or "").strip()
        central_id = str(central.get("central_id") or "").strip()
        queue = central.get("queue") if isinstance(central.get("queue"), dict) else {}
        pending_batches = max(0, _to_int(queue.get("pending_batches"), 0))
        bucket = incidents_by_central.get(central_id) or {"bad": 0, "warn": 0}
        bad_incidents = max(0, _to_int(bucket.get("bad"), 0))
        warn_incidents = max(0, _to_int(bucket.get("warn"), 0))
        incidents_open = bad_incidents + warn_incidents
        eta_delay_min = _estimate_eta_delay_min(
            severity=severity,
            pending_batches=pending_batches,
            bad_incidents=bad_incidents,
            warn_incidents=warn_incidents,
        )
        sla_state = _resolve_sla_state(
            severity=severity,
            pending_batches=pending_batches,
            bad_incidents=bad_incidents,
            warn_incidents=warn_incidents,
        )

        item = {
            "id": vehicle_id or central_id,
            "route": str(queue.get("route") or "—"),
            "state": severity,
            "updated_at": str(central.get("ts_received") or ""),
            "hint": (
                "Рухається за графіком"
                if sla_state == "ok"
                else ("Потрібно уточнити ETA з підтримкою" if sla_state == "warn" else "Є ризик SLA, підтримка вже в роботі")
            ),
            "central_id": central_id,
            "pending_batches": pending_batches,
            "incidents_open": incidents_open,
            "eta_delay_min": eta_delay_min,
            "sla_state": sla_state,
        }
        haystack = " ".join(
            [
                str(item.get("id") or ""),
                str(item.get("route") or ""),
                str(item.get("central_id") or ""),
                str(item.get("hint") or ""),
                str(item.get("sla_state") or ""),
            ]
        ).lower()
        if query_text and query_text not in haystack:
            continue
        rows.append(item)

    rows.sort(
        key=lambda item: (
            _severity_rank(str(item.get("state") or "bad")),
            _incident_impact_rank(str(item.get("sla_state") or "warn")),
            _to_int(item.get("eta_delay_min"), 0),
            str(item.get("updated_at") or ""),
        ),
        reverse=True,
    )
    return rows


async def build_client_home_response(
    db_path: str,
    *,
    scope: dict[str, Any],
) -> dict[str, Any]:
    central_ids = _normalize_scope_ids(scope.get("central_ids"))
    vehicle_ids = _normalize_scope_ids(scope.get("vehicle_ids"))

    centrals = _scope_filter(
        await list_central_heartbeats(db_path),
        central_ids=central_ids,
        vehicle_ids=vehicle_ids,
    )
    incidents = _scope_filter(
        await list_incidents(db_path, include_resolved=False, limit=1000),
        central_ids=central_ids,
        vehicle_ids=vehicle_ids,
    )

    vehicle_rows = _build_vehicle_rows(centrals=centrals, incidents=incidents, q=None)
    total = len(vehicle_rows)
    good = sum(1 for item in vehicle_rows if str(item.get("state") or "") == "good")
    warn = sum(1 for item in vehicle_rows if str(item.get("state") or "") == "warn")
    bad = sum(1 for item in vehicle_rows if str(item.get("state") or "") == "bad")
    latest_ts = ""

    for item in vehicle_rows:
        ts_value = str(item.get("updated_at") or "")
        if ts_value > latest_ts:
            latest_ts = ts_value

    open_tickets = 0
    in_progress_tickets = 0
    for incident in incidents:
        ticket_status = _ticket_status_from_incident(str(incident.get("status") or "open"))
        if ticket_status == "in_progress":
            in_progress_tickets += 1
        else:
            open_tickets += 1

    service_state = "good"
    if total == 0:
        service_state = "warn"
    elif bad > 0:
        service_state = "bad"
    elif warn > 0:
        service_state = "warn"

    sla_risk = sum(1 for item in vehicle_rows if str(item.get("sla_state") or "") == "risk")
    sla_warn = sum(1 for item in vehicle_rows if str(item.get("sla_state") or "") == "warn")
    eta_values = [_to_int(item.get("eta_delay_min"), 0) for item in vehicle_rows]
    eta_avg_delay_min = round(sum(eta_values) / len(eta_values), 1) if eta_values else 0.0
    eta_max_delay_min = max(eta_values) if eta_values else 0
    attention = [
        {
            "id": str(item.get("id") or ""),
            "route": str(item.get("route") or ""),
            "sla_state": str(item.get("sla_state") or "ok"),
            "eta_delay_min": _to_int(item.get("eta_delay_min"), 0),
            "hint": str(item.get("hint") or ""),
        }
        for item in vehicle_rows
        if str(item.get("sla_state") or "ok") in {"warn", "risk"}
    ][:5]

    return {
        "status": "ok",
        "summary": {
            "transport_total": total,
            "transport_good": good,
            "transport_warn": warn,
            "transport_bad": bad,
            "tickets_open": open_tickets,
            "tickets_in_progress": in_progress_tickets,
            "service_state": service_state,
            "sla_risk": sla_risk,
            "sla_warn": sla_warn,
            "eta_avg_delay_min": eta_avg_delay_min,
            "eta_max_delay_min": eta_max_delay_min,
            "updated_at": latest_ts,
        },
        "attention": attention,
    }


async def build_client_vehicles_response(
    db_path: str,
    *,
    scope: dict[str, Any],
    q: str | None,
    limit: int,
) -> dict[str, Any]:
    central_ids = _normalize_scope_ids(scope.get("central_ids"))
    vehicle_ids = _normalize_scope_ids(scope.get("vehicle_ids"))
    centrals = _scope_filter(
        await list_central_heartbeats(db_path),
        central_ids=central_ids,
        vehicle_ids=vehicle_ids,
    )
    incidents = _scope_filter(
        await list_incidents(db_path, include_resolved=False, limit=1500),
        central_ids=central_ids,
        vehicle_ids=vehicle_ids,
    )

    vehicles = _build_vehicle_rows(centrals=centrals, incidents=incidents, q=q)

    bounded_limit = max(1, min(_to_int(limit, 200), 500))
    sliced = vehicles[:bounded_limit]

    good = sum(1 for item in sliced if str(item.get("state") or "") == "good")
    warn = sum(1 for item in sliced if str(item.get("state") or "") == "warn")
    bad = sum(1 for item in sliced if str(item.get("state") or "") == "bad")
    sla_ok = sum(1 for item in sliced if str(item.get("sla_state") or "") == "ok")
    sla_warn = sum(1 for item in sliced if str(item.get("sla_state") or "") == "warn")
    sla_risk = sum(1 for item in sliced if str(item.get("sla_state") or "") == "risk")
    eta_values = [_to_int(item.get("eta_delay_min"), 0) for item in sliced]
    eta_avg_delay_min = round(sum(eta_values) / len(eta_values), 1) if eta_values else 0.0
    eta_max_delay_min = max(eta_values) if eta_values else 0

    return {
        "status": "ok",
        "total": len(sliced),
        "vehicles": sliced,
        "summary": {
            "good": good,
            "warn": warn,
            "bad": bad,
            "sla_ok": sla_ok,
            "sla_warn": sla_warn,
            "sla_risk": sla_risk,
            "eta_avg_delay_min": eta_avg_delay_min,
            "eta_max_delay_min": eta_max_delay_min,
        },
    }


async def build_client_tickets_response(
    db_path: str,
    *,
    scope: dict[str, Any],
    status: str | None,
    q: str | None,
    limit: int,
) -> dict[str, Any]:
    central_ids = _normalize_scope_ids(scope.get("central_ids"))
    vehicle_ids = _normalize_scope_ids(scope.get("vehicle_ids"))
    status_filter = str(status or "all").strip().lower()
    if status_filter not in {"all", "open", "in_progress", "resolved"}:
        status_filter = "all"
    query_text = str(q or "").strip().lower()

    incidents = _scope_filter(
        await list_incidents(db_path, include_resolved=True, limit=1500),
        central_ids=central_ids,
        vehicle_ids=vehicle_ids,
    )

    rows: list[dict[str, Any]] = []
    for item in incidents:
        ticket_status = _ticket_status_from_incident(str(item.get("status") or "open"))
        row = {
            "id": f"{str(item.get('central_id') or '')}:{str(item.get('code') or '')}",
            "topic": str(item.get("message") or item.get("code") or "Інцидент"),
            "status": ticket_status,
            "updated_at": str(item.get("updated_at") or item.get("last_seen_ts") or ""),
            "note": f"{str(item.get('severity') or 'bad').upper()} · {str(item.get('code') or '')}",
            "central_id": str(item.get("central_id") or ""),
            "vehicle_id": str(item.get("vehicle_id") or ""),
        }
        if status_filter != "all" and row["status"] != status_filter:
            continue
        haystack = " ".join([row["id"], row["topic"], row["note"], row["central_id"], row["vehicle_id"]]).lower()
        if query_text and query_text not in haystack:
            continue
        rows.append(row)

    rows.sort(key=lambda item: str(item.get("updated_at") or ""), reverse=True)
    bounded_limit = max(1, min(_to_int(limit, 200), 500))
    sliced = rows[:bounded_limit]

    total = len(sliced)
    open_total = sum(1 for item in sliced if str(item.get("status") or "") in {"open", "in_progress"})
    resolved_total = sum(1 for item in sliced if str(item.get("status") or "") == "resolved")

    return {
        "status": "ok",
        "total": total,
        "tickets": sliced,
        "summary": {
            "open": open_total,
            "resolved": resolved_total,
        },
    }


async def build_client_status_response(
    db_path: str,
    *,
    scope: dict[str, Any],
    limit: int,
) -> dict[str, Any]:
    central_ids = _normalize_scope_ids(scope.get("central_ids"))
    vehicle_ids = _normalize_scope_ids(scope.get("vehicle_ids"))

    incidents = _scope_filter(
        await list_incidents(db_path, include_resolved=True, limit=1200),
        central_ids=central_ids,
        vehicle_ids=vehicle_ids,
    )

    events: list[dict[str, Any]] = []
    for item in incidents:
        severity = str(item.get("severity") or "bad").strip().lower()
        incident_status = str(item.get("status") or "open").strip().lower()
        message = str(item.get("message") or item.get("code") or "Оновлення")
        if incident_status == "resolved":
            message = f"Вирішено: {message}"
        elif incident_status == "acked":
            message = f"У роботі підтримки: {message}"

        events.append(
            {
                "ts": str(item.get("updated_at") or item.get("last_seen_ts") or item.get("first_seen_ts") or ""),
                "category": str(item.get("vehicle_id") or item.get("central_id") or "Транспорт"),
                "level": severity if severity in {"good", "warn", "bad"} else "bad",
                "message": message,
                "code": str(item.get("code") or ""),
                "status": incident_status,
            }
        )

    events.sort(key=lambda item: _parse_iso_utc(str(item.get("ts") or "")) or datetime.fromtimestamp(0, tz=timezone.utc), reverse=True)
    bounded_limit = max(1, min(_to_int(limit, 120), 500))
    sliced = events[:bounded_limit]

    summary = {
        "good": sum(1 for item in sliced if str(item.get("level") or "") == "good"),
        "warn": sum(1 for item in sliced if str(item.get("level") or "") == "warn"),
        "bad": sum(1 for item in sliced if str(item.get("level") or "") == "bad"),
    }

    return {
        "status": "ok",
        "total": len(sliced),
        "events": sliced,
        "summary": summary,
    }


async def build_client_profile_response(
    db_path: str,
    *,
    client_id: str,
) -> dict[str, Any]:
    return {
        "status": "ok",
        "profile": await get_client_profile(db_path, client_id=client_id),
    }


async def update_client_profile_response(
    db_path: str,
    *,
    client_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "ok",
        "profile": await upsert_client_profile(db_path, client_id=client_id, profile=payload),
    }


async def build_client_notification_settings_response(
    db_path: str,
    *,
    client_id: str,
) -> dict[str, Any]:
    return {
        "status": "ok",
        "settings": await get_client_notification_settings(db_path, client_id=client_id),
    }


async def update_client_notification_settings_response(
    db_path: str,
    *,
    client_id: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": "ok",
        "settings": await upsert_client_notification_settings(
            db_path,
            client_id=client_id,
            settings=payload,
        ),
    }
