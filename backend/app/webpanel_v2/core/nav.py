from __future__ import annotations

from copy import deepcopy

# v2 IA: 2 levels (`group -> items`). Keep the sidebar short; deeper splits go into page-level subnav.

ADMIN_V2_NAV: list[dict] = [
    {
        "title": "Старт",
        "items": [
            {"key": "overview", "label": "Огляд", "href": "/admin2"},
            {"key": "commission", "label": "Підключення", "href": "/admin2/commission"},
        ],
    },
    {
        "title": "Флот",
        "items": [
            {"key": "fleet", "label": "Стан флоту", "href": "/admin2/fleet"},
            {"key": "alerts", "label": "Алерти", "href": "/admin2/fleet/alerts"},
            {"key": "incidents", "label": "Інциденти", "href": "/admin2/fleet/incidents"},
            {"key": "actions", "label": "Дії операторів", "href": "/admin2/fleet/actions"},
        ],
    },
    {
        "title": "Сповіщення",
        "items": [
            {"key": "notify_center", "label": "Доставка", "href": "/admin2/notify-center"},
            {"key": "notifications", "label": "Правила каналів", "href": "/admin2/notifications"},
        ],
    },
    {
        "title": "Контроль і KPI",
        "items": [
            {"key": "kpi_history", "label": "Історія KPI", "href": "/admin2/kpi/history"},
            {"key": "policy", "label": "Політика", "href": "/admin2/policy"},
            {"key": "audit", "label": "Аудит", "href": "/admin2/audit"},
        ],
    },
    {
        "title": "Інфраструктура",
        "items": [
            {"key": "wg", "label": "WireGuard", "href": "/admin2/wg"},
        ],
    },
]

CLIENT_V2_NAV: list[dict] = [
    {
        "title": "Огляд",
        "items": [
            {"key": "home", "label": "Огляд", "href": "/client2"},
        ],
    },
    {
        "title": "Транспорт і статуси",
        "items": [
            {"key": "vehicles", "label": "Мої транспорти", "href": "/client2/vehicles"},
            {"key": "tickets", "label": "Звернення", "href": "/client2/tickets"},
            {"key": "status", "label": "Статус", "href": "/client2/status"},
        ],
    },
    {
        "title": "Акаунт",
        "items": [
            {"key": "profile", "label": "Профіль", "href": "/client2/profile"},
            {"key": "notifications", "label": "Сповіщення", "href": "/client2/notifications"},
        ],
    },
]


def _best_active_key(path: str, nav_groups: list[dict]) -> str | None:
    best_key: str | None = None
    best_len = -1
    normalized = path.rstrip("/") or "/"
    for group in nav_groups:
        for item in group.get("items") or []:
            href = str(item.get("href") or "").rstrip("/") or "/"
            if normalized == href or normalized.startswith(href + "/"):
                if len(href) > best_len:
                    best_len = len(href)
                    best_key = str(item.get("key") or "") or None
    return best_key


def build_nav_state(*, path: str, nav_groups: list[dict]) -> list[dict]:
    """Adds `active` on items and `open` on groups (2-level IA)."""
    active_key = _best_active_key(path, nav_groups)
    groups = deepcopy(nav_groups)
    for group in groups:
        open_group = False
        for item in group.get("items") or []:
            is_active = active_key is not None and item.get("key") == active_key
            item["active"] = bool(is_active)
            open_group = open_group or bool(is_active)
        group["open"] = bool(open_group)
    return groups

