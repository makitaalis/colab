# Admin step-18 visual polish: pack-9 (audit без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/audit` короче визуально: primary toolbar только про обновление/ссылку, а фильтры и параметры окна вынести в advanced секцию. Контекст источника и окна данных должен читаться без “простыни” контролов.

## Изменения (Domain: Контроль и KPI)

Файл: `backend/app/admin_audit_page.py`.

1) Header chips
- `оновлено: …` перенесено в header chips (контекст, а не действие).

2) Toolbar: primary vs advanced
- Primary оставляет: `авто`, `скинути`, `оновити`, `copy link`, `filterSummary`.
- Фильтры (`window/status/role/actor/action/q`) перенесены в `<details class="toolbarDetails" data-advanced-details="1">`.

3) Reset фильтрів исправлен
- `Скинути` теперь возвращает к стандартным значениям включая `window=24h`.

4) Контекст “источник + окно”
- Добавлен `tableMeta` над таблицей:
  - `джерело: /api/admin/audit`
  - `сортування: нові → старі`
  - чип `вікно: …` (динамический)

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack9-audit-checklist.md`

