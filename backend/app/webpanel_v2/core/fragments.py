from __future__ import annotations

from datetime import datetime, timezone


def utc_now_label() -> str:
    ts = datetime.now(timezone.utc)
    return ts.strftime("%Y-%m-%d %H:%M:%S UTC")


def render_time_chip(*, theme: str) -> str:
    label = utc_now_label()
    chip_class = "v2Chip v2Chip--muted"
    if theme == "dark":
        chip_class += " v2Chip--dark"
    return f'<span id="v2ServerTime" class="{chip_class}">сервер: {label}</span>'


def render_ping(*, theme: str) -> str:
    label = utc_now_label()
    cls = "v2Ping v2Ping--dark" if theme == "dark" else "v2Ping"
    return f'<span class="{cls}">OK · {label}</span>'

