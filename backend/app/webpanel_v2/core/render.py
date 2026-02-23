from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import Request
from fastapi.templating import Jinja2Templates
from starlette.responses import Response

from app.webpanel_v2 import UI_BUILD
from app.webpanel_v2.core.fragments import utc_now_label
from app.webpanel_v2.core.nav import ADMIN_V2_NAV, CLIENT_V2_NAV, build_nav_state

ROOT_DIR = Path(__file__).resolve().parents[1]
templates = Jinja2Templates(directory=str(ROOT_DIR / "templates"))


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return ""


# Inline assets because nginx on the VPS currently doesn't proxy /static/* for v2.
V2_CSS = _read_text(ROOT_DIR / "static" / "v2.css")
V2_JS = _read_text(ROOT_DIR / "static" / "v2.js")
HTMX_JS = _read_text(ROOT_DIR / "static" / "vendor" / "htmx.min.js")


def render_admin2(request: Request, *, template_name: str, title: str, header_title: str) -> Response:
    nav = build_nav_state(path=str(request.url.path), nav_groups=ADMIN_V2_NAV)
    chips = [
        {"tone": "neutral", "text": "v2 preview"},
        {
            "id": "v2ServerTime",
            "tone": "muted",
            "text": f"сервер: {utc_now_label()}",
            "hx_get": "/admin2/_fragment/time",
            "hx_trigger": "load, every 10s",
            "hx_swap": "outerHTML",
        },
    ]
    ctx: dict[str, Any] = {
        "request": request,
        "ui_build": UI_BUILD,
        "theme": "dark",
        "kicker": "Passengers • Адмінка v2",
        "title": title,
        "header_title": header_title,
        "v2_css": V2_CSS,
        "v2_js": V2_JS,
        "htmx_js": HTMX_JS,
        "nav_groups": nav,
        "chips": chips,
    }
    return templates.TemplateResponse(template_name, ctx)


def render_client2(request: Request, *, template_name: str, title: str, header_title: str) -> Response:
    nav = build_nav_state(path=str(request.url.path), nav_groups=CLIENT_V2_NAV)
    chips = [
        {"tone": "neutral", "text": "v2 preview"},
        {
            "id": "v2ServerTime",
            "tone": "muted",
            "text": f"сервер: {utc_now_label()}",
            "hx_get": "/client2/_fragment/time",
            "hx_trigger": "load, every 15s",
            "hx_swap": "outerHTML",
        },
    ]
    ctx: dict[str, Any] = {
        "request": request,
        "ui_build": UI_BUILD,
        "theme": "light",
        "kicker": "Passengers • Кабінет v2",
        "title": title,
        "header_title": header_title,
        "v2_css": V2_CSS,
        "v2_js": V2_JS,
        "htmx_js": HTMX_JS,
        "nav_groups": nav,
        "chips": chips,
    }
    return templates.TemplateResponse(template_name, ctx)

