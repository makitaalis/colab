from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.render import render_admin2

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def admin2_index(request: Request):
    return render_admin2(request, template_name="admin/index.html", title="Адмінка v2", header_title="Огляд (v2)")


@router.get("/commission", response_class=HTMLResponse)
async def admin2_commission(request: Request):
    return render_admin2(
        request,
        template_name="admin/placeholder.html",
        title="Підключення v2",
        header_title="Підключення (v2)",
    )
