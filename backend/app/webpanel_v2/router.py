from __future__ import annotations

from fastapi import APIRouter, Request
from starlette.responses import HTMLResponse

from app.webpanel_v2.core.render import render_admin2, render_client2
from app.webpanel_v2.domains.admin.router import router as admin2_router
from app.webpanel_v2.domains.client.router import router as client2_router

router = APIRouter()


# FastAPI routers often canonicalize "/" with a trailing slash under a prefix (e.g. "/admin2/").
# We serve both variants ("/admin2" and "/admin2/") without redirects for cleaner URLs.
@router.get("/admin2", response_class=HTMLResponse)
async def admin2_index_noslash(request: Request):
    return render_admin2(request, template_name="admin/index.html", title="Адмінка v2", header_title="Огляд (v2)")


@router.get("/client2", response_class=HTMLResponse)
async def client2_home_noslash(request: Request):
    return render_client2(request, template_name="client/index.html", title="Кабінет v2", header_title="Огляд клієнта (v2)")


router.include_router(admin2_router)
router.include_router(client2_router)
