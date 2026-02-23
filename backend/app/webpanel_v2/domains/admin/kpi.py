from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.render import render_admin2

router = APIRouter()


@router.get("/kpi/history", response_class=HTMLResponse)
async def admin2_kpi_history(request: Request):
    return render_admin2(request, template_name="admin/placeholder.html", title="Історія KPI v2", header_title="Історія KPI (v2)")


@router.get("/policy", response_class=HTMLResponse)
async def admin2_policy(request: Request):
    return render_admin2(request, template_name="admin/placeholder.html", title="Політика v2", header_title="Політика (v2)")


@router.get("/audit", response_class=HTMLResponse)
async def admin2_audit(request: Request):
    return render_admin2(request, template_name="admin/placeholder.html", title="Аудит v2", header_title="Аудит (v2)")

