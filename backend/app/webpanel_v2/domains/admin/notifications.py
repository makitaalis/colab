from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.render import render_admin2

router = APIRouter()


@router.get("/notify-center", response_class=HTMLResponse)
async def admin2_notify_center(request: Request):
    return render_admin2(request, template_name="admin/placeholder.html", title="Доставка v2", header_title="Доставка (v2)")


@router.get("/notifications", response_class=HTMLResponse)
async def admin2_notifications(request: Request):
    return render_admin2(
        request,
        template_name="admin/placeholder.html",
        title="Правила каналів v2",
        header_title="Правила каналів (v2)",
    )

