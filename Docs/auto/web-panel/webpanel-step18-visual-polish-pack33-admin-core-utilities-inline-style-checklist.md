# Pack-33 Checklist (Admin Core Utilities, Inline-Style Reduction)

Дата: 2026-02-18

- [x] Core: добавлены `.wgBox/*` в `backend/app/admin_ui_kit.py`.
- [x] Core: добавлены utility-классы `.uMt*`, `.uMb*`, `.uJcStart`, `.uInlineRow`, `.uMinW*`, `.uMaxH40vh`.
- [x] Core: добавлен `.tableWrapPre` для `<pre class="tableWrap tableWrapPre">`.
- [x] Domains: `backend/app/admin_overview_page.py` переведён с inline на utilities.
- [x] Domains: `backend/app/admin_commission_page.py` переведён с inline на utilities.
- [x] Domains: `backend/app/admin_fleet_policy_page.py` toolbars + max-height переведены на utilities.
- [x] Domains: `backend/app/admin_fleet_notifications_page.py` toolbars + secondary spacing переведены на utilities.
- [x] Domains: `backend/app/admin_wg_page.py` pre/table/toolbars частично переведены на utilities.
- [x] Server-first: `py_compile` изменённых модулей = OK.
- [x] Server-first: restart `api` = OK.
- [x] Gate: `scripts/admin_panel_smoke_gate.sh` = PASS.
- [x] Docs: обновить `Docs/Проект/Веб-панель/Ядро (Core).md`.
- [x] Skill: обновить `skills/orangepi-passengers-webpanel-uiux/SKILL.md`.
- [x] Docs: записать в `Docs/Проект/Паспорт релиза документации.md`.
