from __future__ import annotations

from fastapi import APIRouter
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.fragments import render_ping, render_time_chip
from app.webpanel_v2.domains.admin.fleet import router as fleet_router
from app.webpanel_v2.domains.admin.infrastructure import router as infra_router
from app.webpanel_v2.domains.admin.kpi import router as kpi_router
from app.webpanel_v2.domains.admin.notifications import router as notify_router
from app.webpanel_v2.domains.admin.start import router as start_router

router = APIRouter(prefix="/admin2")
router.include_router(start_router)
router.include_router(fleet_router)
router.include_router(notify_router)
router.include_router(kpi_router)
router.include_router(infra_router)


@router.get("/_fragment/time", response_class=HTMLResponse)
async def admin2_fragment_time():
    return render_time_chip(theme="dark")


@router.get("/_fragment/ping", response_class=HTMLResponse)
async def admin2_fragment_ping():
    return render_ping(theme="dark")

