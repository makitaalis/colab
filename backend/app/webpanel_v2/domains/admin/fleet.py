from __future__ import annotations

import os
from datetime import datetime, timezone

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.db import list_central_heartbeats, list_incidents
from app.webpanel_v2.core.render import render_admin2, templates

router = APIRouter()


def _get_db_path() -> str:
    return os.environ.get("DB_PATH", "/data/passengers.sqlite3")


def _format_age(age_sec: int | None) -> str:
    if age_sec is None:
        return "—"
    seconds = max(0, int(age_sec))
    if seconds < 60:
        return f"{seconds}s"
    minutes, sec = divmod(seconds, 60)
    if minutes < 60:
        return f"{minutes}m {sec:02d}s"
    hours, minutes = divmod(minutes, 60)
    return f"{hours}h {minutes:02d}m"


def _severity_rank(severity: str) -> int:
    normalized = str(severity or "good").strip().lower()
    if normalized == "bad":
        return 0
    if normalized == "warn":
        return 1
    return 2


@router.get("/fleet", response_class=HTMLResponse)
async def admin2_fleet(request: Request):
    return render_admin2(request, template_name="admin/fleet.html", title="Флот v2", header_title="Стан флоту (v2)")


@router.get("/_fragment/fleet/monitor", response_class=HTMLResponse)
async def admin2_fleet_monitor_fragment(request: Request, limit: int = 80):
    bounded_limit = max(10, min(int(limit), 300))
    try:
        db_path = _get_db_path()
        centrals = await list_central_heartbeats(db_path)
        incidents = await list_incidents(db_path, include_resolved=False, limit=2000)
    except Exception:
        ctx = {
            "request": request,
            "fleet_total": 0,
            "fleet_bad": 0,
            "fleet_warn": 0,
            "fleet_pending": 0,
            "incident_total": 0,
            "incident_bad": 0,
            "incident_warn": 0,
            "generated_at": "error",
            "rows": [],
        }
        return templates.TemplateResponse("admin/fragments/fleet_monitor.html", ctx)

    fleet_total = len(centrals)
    fleet_bad = 0
    fleet_warn = 0
    fleet_pending = 0

    rows: list[dict] = []
    for item in centrals:
        health = item.get("health") or {}
        sev = str(health.get("severity") or "good").strip().lower()
        if sev == "bad":
            fleet_bad += 1
        elif sev == "warn":
            fleet_warn += 1

        queue = item.get("queue") or {}
        pending = int(queue.get("pending_batches") or 0)
        if pending > 0:
            fleet_pending += 1

        age_sec = item.get("age_sec")
        rows.append(
            {
                "central_id": str(item.get("central_id") or ""),
                "vehicle_id": str(item.get("vehicle_id") or "") or "—",
                "age": _format_age(age_sec if isinstance(age_sec, int) else None),
                "age_sec": int(age_sec) if isinstance(age_sec, int) else 0,
                "severity": sev if sev in {"good", "warn", "bad"} else "good",
                "pending": pending,
                "alerts_bad": int(health.get("alerts_bad") or 0),
                "alerts_warn": int(health.get("alerts_warn") or 0),
                "v1_href": f"/admin/fleet/central/{str(item.get('central_id') or '')}",
            }
        )

    rows.sort(key=lambda r: (_severity_rank(r.get("severity") or "good"), -int(r.get("age_sec") or 0)))
    rows = rows[:bounded_limit]

    incident_total = len(incidents)
    incident_bad = sum(1 for it in incidents if str(it.get("severity") or "").strip().lower() == "bad")
    incident_warn = sum(1 for it in incidents if str(it.get("severity") or "").strip().lower() == "warn")

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    ctx = {
        "request": request,
        "fleet_total": fleet_total,
        "fleet_bad": fleet_bad,
        "fleet_warn": fleet_warn,
        "fleet_pending": fleet_pending,
        "incident_total": incident_total,
        "incident_bad": incident_bad,
        "incident_warn": incident_warn,
        "generated_at": generated_at,
        "rows": rows,
    }
    return templates.TemplateResponse("admin/fragments/fleet_monitor.html", ctx)


@router.get("/fleet/alerts", response_class=HTMLResponse)
async def admin2_fleet_alerts(request: Request):
    return render_admin2(request, template_name="admin/placeholder.html", title="Алерти v2", header_title="Алерти (v2)")


@router.get("/fleet/incidents", response_class=HTMLResponse)
async def admin2_fleet_incidents(request: Request):
    return render_admin2(request, template_name="admin/placeholder.html", title="Інциденти v2", header_title="Інциденти (v2)")


@router.get("/fleet/actions", response_class=HTMLResponse)
async def admin2_fleet_actions(request: Request):
    return render_admin2(request, template_name="admin/placeholder.html", title="Дії операторів v2", header_title="Дії операторів (v2)")
