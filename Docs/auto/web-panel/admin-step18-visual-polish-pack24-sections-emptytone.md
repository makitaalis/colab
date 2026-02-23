# Admin step-18 (pack-24): Section rhythm + empty-state tones (clean pages)

Дата: 2026-02-17

## Цель

- Выровнять визуальную иерархию внутри карточек: единый заголовок секции + инструменты справа.
- Сделать empty-state таблиц “семантичным”: не только “нет данных”, но и тон (OK/attention) без ручной разметки на каждой странице.

## Изменения (Core)

Файл: `backend/app/admin_ui_kit.py`

1. Добавлены/уточнены стили секций:
- `.sectionTitle`, `.sectionKicker`,
- `.sectionHead` теперь даёт единый отступ снизу,
- `.sectionTools` выровнен под action-row.
2. Empty-state таблиц:
- поддержка `data-empty-title`, `data-empty-text`, `data-empty-tone` (`good|warn|bad|neutral`),
- добавлены tone-стили `.emptyState.tone-*`,
- `applyEmptyTables()` экспортирован как `AdminUiKit.applyEmptyTables()` (страницы могут вызывать после перерисовки таблицы).

## Изменения (Domains)

- В ряде admin-страниц убраны inline-заголовки вида `style="font-weight:600;"` в пользу `.sectionTitle`:
  - `backend/app/admin_overview_page.py`
  - `backend/app/admin_fleet_page.py`
  - `backend/app/admin_fleet_alerts_page.py`
  - `backend/app/admin_fleet_notify_center_page.py`
  - `backend/app/admin_fleet_notifications_page.py`
  - `backend/app/admin_fleet_central_page.py`
  - `backend/app/admin_fleet_history_page.py`
  - `backend/app/admin_wg_page.py`
  - `backend/app/admin_fleet_incident_detail_page.py`
  - `backend/app/admin_fleet_incidents_page.py`

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/admin-step18-visual-polish-pack24-sections-emptytone-checklist.md`).

