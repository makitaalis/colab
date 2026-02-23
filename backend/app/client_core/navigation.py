from __future__ import annotations

from app.client_domains.domain_catalog import CLIENT_PANEL_DOMAINS

ClientNavItem = tuple[str, str, str, str]
ClientNavGroup = tuple[str, str, tuple[ClientNavItem, ...]]


def build_client_nav_groups() -> tuple[ClientNavGroup, ...]:
    groups: list[ClientNavGroup] = []
    for domain in CLIENT_PANEL_DOMAINS:
        items: list[ClientNavItem] = []
        for index, route in enumerate(domain.routes):
            tier = "hub" if index == 0 else "sub"
            items.append((route.key, route.label, route.href, tier))
        groups.append((domain.key, domain.title, tuple(items)))
    return tuple(groups)


CLIENT_NAV_GROUPS: tuple[ClientNavGroup, ...] = build_client_nav_groups()

