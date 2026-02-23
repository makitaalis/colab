# Admin step-18 visual polish: pack-15 (overview без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin` (overview) менее “простынёй”: primary экран про контекст и onboarding, а глубокие операционные таблицы вынести во вторичный блок; добавить единый reset и сохранить состояние secondary.

## Изменения (Domain: Старт)

Файл: `backend/app/admin_overview_page.py`.

1) Toolbar: добавлен reset
- Добавлена кнопка `Скинути` (reset `q` + `central_id` commissioning).
- URL синхронизируется через существующий `syncQueryFromFilters()`.

2) Операционные таблицы вынесены в secondary `<details>`
- Добавлен блок:
  - `<details id="overviewSecondaryDetails" class="domainSplitDetails" data-advanced-details="1">…</details>`
- Persistence key: `passengers_admin_overview_secondary_details_v1`.
- Внутрь secondary перенесены:
  - “SLA таймери інцидентів”
  - “Потребує дій”
  - “Активні алерти”

3) Источники данных унифицированы
- На secondary таблицах добавлен `tableMeta` (source + сортировка) вместо разрозненных muted-линий.

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack15-overview-checklist.md`

