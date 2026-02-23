# Admin step-18 visual polish: pack-13 (central detail без перегруза)

Дата: 2026-02-17

Цель: сделать страницу детали узла `/admin/fleet/central/{central_id}` более “triage-first”: активные алерты и действия сверху, история и журналы во вторичном контуре, с явными источниками данных.

## Изменения (Domain: Флот)

Файл: `backend/app/admin_fleet_central_page.py`.

1) Primary: активные алерты остаются главным экраном
- Добавлен `tableMeta` для блока “Поточні алерти”:
  - `джерело: /api/admin/fleet/central/<central_id>`
  - `контур: active alerts`
  - `ліміт: 120`, `actions: 200`

2) Secondary: история и журнал действий вынесены в `<details>`
- Добавлен блок:
  - `<details id="centralSecondaryDetails" class="domainSplitDetails" data-advanced-details="1">…</details>`
- Persistence key: `passengers_admin_fleet_central_secondary_details_v1`.
- Внутри secondary:
  - “Історія черги/сервісів” + `tableMeta`;
  - “Журнал дій адміністратора” + `tableMeta` и ссылка в общий журнал дій с фильтром по central.

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack13-central-detail-checklist.md`

