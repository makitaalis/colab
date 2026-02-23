from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.render import render_client2

router = APIRouter()


@router.get("/profile", response_class=HTMLResponse)
async def client2_profile(request: Request):
    return render_client2(request, template_name="client/placeholder.html", title="Профіль v2", header_title="Профіль (v2)")


@router.get("/notifications", response_class=HTMLResponse)
async def client2_notifications(request: Request):
    return render_client2(request, template_name="client/placeholder.html", title="Сповіщення v2", header_title="Сповіщення (v2)")

