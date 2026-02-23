from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.render import render_client2

router = APIRouter()


@router.get("/tickets", response_class=HTMLResponse)
async def client2_tickets(request: Request):
    return render_client2(request, template_name="client/placeholder.html", title="Звернення v2", header_title="Звернення (v2)")

