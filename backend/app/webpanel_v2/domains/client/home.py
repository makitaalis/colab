from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.render import render_client2

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def client2_home(request: Request):
    return render_client2(request, template_name="client/index.html", title="Кабінет v2", header_title="Огляд клієнта (v2)")
