from __future__ import annotations

from html import escape

from app.admin_domains.domain_catalog import (
    ADMIN_PANEL_DOMAINS,
    ADMIN_WORKFLOW_ORDER,
    ADMIN_WORKFLOW_STEPS,
)

NavItem = tuple[str, str, str, str, str]
NavGroup = tuple[str, str, tuple[NavItem, ...]]
WorkflowItem = tuple[str, str, str, str]


def _build_nav_groups() -> tuple[NavGroup, ...]:
    groups: list[NavGroup] = []
    for domain in ADMIN_PANEL_DOMAINS:
        items: list[NavItem] = []
        for index, route in enumerate(domain.routes):
            tier = "hub" if index == 0 else "sub"
            step = ADMIN_WORKFLOW_STEPS.get(route.key, "")
            items.append((route.key, route.label, route.href, step, tier))
        groups.append((domain.key, domain.title, tuple(items)))
    return tuple(groups)


ADMIN_NAV_GROUPS: tuple[NavGroup, ...] = _build_nav_groups()


def _build_nav_workflow(groups: tuple[NavGroup, ...]) -> tuple[WorkflowItem, ...]:
    lookup: dict[str, WorkflowItem] = {}
    for _group_key, _group_title, items in groups:
        for key, label, href, _step, _tier in items:
            step = ADMIN_WORKFLOW_STEPS.get(key, "")
            if not step or key in lookup:
                continue
            lookup[key] = (key, label, href, step)
    flow: list[WorkflowItem] = []
    for key in ADMIN_WORKFLOW_ORDER:
        item = lookup.get(key)
        if item is not None:
            flow.append(item)
    return tuple(flow)


ADMIN_NAV_WORKFLOW: tuple[WorkflowItem, ...] = _build_nav_workflow(ADMIN_NAV_GROUPS)


def find_active_nav_group(current_nav: str, groups: tuple[NavGroup, ...] = ADMIN_NAV_GROUPS) -> NavGroup | None:
    current = str(current_nav or "").strip().lower()
    if not current:
        return None
    for group in groups:
        if any(current == key for key, _label, _href, _step, _tier in group[2]):
            return group
    return None


def render_page_subnav(current_nav: str, groups: tuple[NavGroup, ...] = ADMIN_NAV_GROUPS) -> str:
    group = find_active_nav_group(current_nav, groups)
    if group is None:
        return ""
    _group_key, group_title, items = group
    if len(items) <= 1:
        return ""
    current = str(current_nav or "").strip().lower()
    links: list[str] = []
    for key, label, href, _step, _tier in items:
        classes = "pageSubnavItem active" if current == key else "pageSubnavItem"
        links.append(
            f'<a class="{classes}" href="{escape(href, quote=True)}" data-nav-key="{escape(key)}">{escape(label)}</a>'
        )
    return (
        '        <nav class="pageSubnav" aria-label="Підменю поточного розділу">\n'
        f'          <span class="pageSubnavLabel">{escape(group_title)}</span>\n'
        + "\n".join(f"          {item}" for item in links)
        + "\n        </nav>\n"
    )

