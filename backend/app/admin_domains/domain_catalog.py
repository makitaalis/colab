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
    audience: str = "admin"
    doc_path: str = ""
    owner: str = "web-panel-admin"


ADMIN_PANEL_DOMAINS: tuple[PanelDomain, ...] = (
    PanelDomain(
        key="start",
        title="Старт",
        routes=(
            DomainRoute("overview", "Огляд системи", "/admin", "admin_overview_page.py", "fleet-overview"),
            DomainRoute("commission", "Підключення", "/admin/commission", "admin_commission_page.py", "commissioning"),
        ),
        doc_path="Docs/Проект/Веб-панель/Домен Старт.md",
    ),
    PanelDomain(
        key="fleet-ops",
        title="Флот",
        routes=(
            DomainRoute("fleet", "Стан флоту", "/admin/fleet", "admin_fleet_page.py", "fleet-overview"),
            DomainRoute("alerts", "Алерти", "/admin/fleet/alerts", "admin_fleet_alerts_page.py", "alerts-ops"),
            DomainRoute(
                "incidents",
                "Інциденти",
                "/admin/fleet/incidents?status=open&include_resolved=0",
                "admin_fleet_incidents_page.py",
                "incident-detail",
            ),
            DomainRoute("actions", "Дії операторів", "/admin/fleet/actions", "admin_fleet_actions_page.py", "alerts-actions"),
        ),
        doc_path="Docs/Проект/Веб-панель/Домен Флот.md",
    ),
    PanelDomain(
        key="notifications",
        title="Сповіщення",
        routes=(
            DomainRoute(
                "notify-center",
                "Доставка",
                "/admin/fleet/notify-center",
                "admin_fleet_notify_center_page.py",
                "notify-center",
            ),
            DomainRoute(
                "notifications",
                "Правила каналів",
                "/admin/fleet/notifications",
                "admin_fleet_notifications_page.py",
                "notification-rules",
            ),
        ),
        doc_path="Docs/Проект/Веб-панель/Домен Сповіщення.md",
    ),
    PanelDomain(
        key="analytics",
        title="Контроль і KPI",
        routes=(
            DomainRoute("history", "Історія KPI", "/admin/fleet/history", "admin_fleet_history_page.py", "policy-kpi"),
            DomainRoute("policy", "Політика", "/admin/fleet/policy", "admin_fleet_policy_page.py", "policy-kpi"),
            DomainRoute("audit", "Аудит", "/admin/audit", "admin_audit_page.py", "audit"),
        ),
        doc_path="Docs/Проект/Веб-панель/Домен Контроль и KPI.md",
    ),
    PanelDomain(
        key="infra",
        title="Інфраструктура",
        routes=(
            DomainRoute("wg", "WireGuard", "/admin/wg", "admin_wg_page.py", "wg-ops"),
        ),
        doc_path="Docs/Проект/Веб-панель/Домен Інфраструктура.md",
    ),
)


ADMIN_WORKFLOW_ORDER: tuple[str, ...] = ("fleet", "alerts", "incidents", "audit")
ADMIN_WORKFLOW_STEPS: dict[str, str] = {
    "fleet": "1",
    "alerts": "2",
    "incidents": "3",
    "audit": "4",
}
