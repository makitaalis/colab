from __future__ import annotations

from fastapi import APIRouter
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.fragments import render_ping, render_time_chip
from app.webpanel_v2.domains.client.account import router as account_router
from app.webpanel_v2.domains.client.home import router as home_router
from app.webpanel_v2.domains.client.tickets import router as tickets_router
from app.webpanel_v2.domains.client.transport import router as transport_router

router = APIRouter(prefix="/client2")
router.include_router(home_router)
router.include_router(transport_router)
router.include_router(tickets_router)
router.include_router(account_router)


@router.get("/_fragment/time", response_class=HTMLResponse)
async def client2_fragment_time():
    return render_time_chip(theme="light")


@router.get("/_fragment/ping", response_class=HTMLResponse)
async def client2_fragment_ping():
    return render_ping(theme="light")

