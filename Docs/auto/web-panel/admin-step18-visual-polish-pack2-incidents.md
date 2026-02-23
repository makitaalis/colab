# Admin step-18 — Visual polish pack 2 (incidents content split)

- date: `2026-02-17`
- scope: `admin domain: Флот -> Інциденти`

## Цель

Снизить визуальную перегрузку страницы `/admin/fleet/incidents` и сделать primary triage короче:

- primary: KPI + фильтры + таблица инцидентов + bulk actions;
- secondary: SLA heatmap + журнал доставки сповіщень.

## Изменения

- `backend/app/admin_fleet_incidents_page.py`
  - блоки `Теплокарта SLA` и `Журнал доставки сповіщень` перенесены в `<details id="incSecondaryDetails" class="domainSplitDetails">`;
  - добавлен persistence состояния secondary details:
    - `passengers_admin_incidents_secondary_details_v1` в `localStorage`;
  - `data-advanced-details="1"` позволяет `Simple`-режиму сворачивать secondary блок автоматически.

## Server-first проверка

- Deploy: `rsync -> py_compile -> docker compose ... --build api`
- Gate: `Docs/auto/web-panel/admin-step18-visual-polish-pack2-incidents-checklist.md` — `PASS`

## Примечание

Скрипт страницы продолжает обновлять heatmap/journal даже если `<details>` закрыт (DOM элементы присутствуют, просто скрыты), чтобы открытие было мгновенным без дополнительной загрузки.
