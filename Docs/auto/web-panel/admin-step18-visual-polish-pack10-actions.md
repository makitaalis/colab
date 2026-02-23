# Admin step-18 visual polish: pack-10 (actions без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/fleet/actions` визуально короче: primary toolbar только про обновление/ссылку, фильтры в advanced секции, источник данных читается сразу (tableMeta).

## Изменения (Domain: Флот)

Файл: `backend/app/admin_fleet_actions_page.py`.

1) Toolbar: primary vs advanced
- Primary оставляет: `авто`, `скинути`, `оновити`, `copy link`, `filterSummary`.
- Фильтры (`central/code/q/action`) перенесены в `<details class="toolbarDetails" data-advanced-details="1">`.

2) Контекст “источник + лимит”
- Добавлен `tableMeta` над таблицей:
  - `джерело: /api/admin/fleet/alerts/actions`
  - `сортування: нові → старі`
  - `limit: 500`

## Стабилизация gates (флейки после рестарта)

1) `scripts/client_panel_step7b_audit.py`
- Добавлены ретраи на transient `0/502/503/504`, чтобы step-7b audit не падал на коротких сетевых глитчах.

2) `scripts/client_panel_step16_accessibility_check.sh`
- Добавлены ретраи и “мягкое” чтение HTML/кодов, чтобы step-16 acceptance не падал на `connection reset by peer` сразу после рестарта.

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack10-actions-checklist.md`

