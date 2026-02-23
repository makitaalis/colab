from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class DomainRoute:
    key: str
    label: str
    href: str
    page_file: str = ""
    api_group: str = ""


@dataclass(frozen=True)
class PanelDomain:
    key: str
    title: str
    routes: tuple[DomainRoute, ...]
    audience: str = "client"
    doc_path: str = ""
    owner: str = "web-panel-client"


CLIENT_PANEL_DOMAINS: tuple[PanelDomain, ...] = (
    PanelDomain(
        key="home",
        title="Кабінет",
        routes=(
            DomainRoute("client-home", "Огляд", "/client", "client_home_page.py", "client-home"),
            DomainRoute("client-vehicles", "Мої транспорти", "/client/vehicles", "client_vehicles_page.py", "client-vehicles"),
        ),
        doc_path="Docs/Проект/Веб-панель/Домен Клієнт.md",
    ),
    PanelDomain(
        key="tickets",
        title="Звернення",
        routes=(
            DomainRoute("client-tickets", "Тікети", "/client/tickets", "client_tickets_page.py", "client-tickets"),
            DomainRoute("client-status", "Статуси", "/client/status", "client_status_page.py", "client-status"),
        ),
        doc_path="Docs/Проект/Веб-панель/Домен Клієнт.md",
    ),
    PanelDomain(
        key="account",
        title="Профіль",
        routes=(
            DomainRoute("client-profile", "Профіль", "/client/profile", "client_profile_page.py", "client-profile"),
            DomainRoute("client-notifications", "Сповіщення", "/client/notifications", "client_notifications_page.py", "client-notifications"),
        ),
        doc_path="Docs/Проект/Веб-панель/Домен Клієнт.md",
    ),
)
