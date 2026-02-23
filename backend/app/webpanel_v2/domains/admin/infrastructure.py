from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.render import render_admin2

router = APIRouter()


@router.get("/wg", response_class=HTMLResponse)
async def admin2_wg(request: Request):
    return render_admin2(request, template_name="admin/placeholder.html", title="WireGuard v2", header_title="WireGuard (v2)")

