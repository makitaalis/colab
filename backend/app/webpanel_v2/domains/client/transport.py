from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.render import render_client2

router = APIRouter()


@router.get("/vehicles", response_class=HTMLResponse)
async def client2_vehicles(request: Request):
    return render_client2(request, template_name="client/placeholder.html", title="Транспорт v2", header_title="Мої транспорти (v2)")


@router.get("/status", response_class=HTMLResponse)
async def client2_status(request: Request):
    return render_client2(request, template_name="client/placeholder.html", title="Статус v2", header_title="Статус (v2)")

