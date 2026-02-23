# Admin step-18 visual polish: pack-8 (history без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/fleet/history` более минималистичным и предсказуемым: короткий primary toolbar, “параметры” в advanced секции, понятный контекст окна данных и источника.

## Изменения (Domain: Контроль и KPI)

Файл: `backend/app/admin_fleet_history_page.py`.

1) Toolbar: primary vs advanced
- В primary оставлены действия: `авто`, `скинути`, `оновити`, `скопіювати посилання`.
- Параметры окна (`window`) и бакетирования (`bucket`) перенесены в `<details class="toolbarDetails" data-advanced-details="1">`.

2) Clear filters
- Добавлена явная кнопка `Скинути` (reset на стандартные значения: `window=24h`, `bucket=300`) с обновлением URL и таблицы.

3) Контекст “источник + окно”
- Добавлен `tableMeta` над таблицей:
  - `джерело: /api/admin/fleet/metrics/history`
  - `сортування: нові → старі`
  - чип `вікно: …` (динамически: окно + шаг бакетирования)

4) Быстрые переходы по сценарию
- В блок “Останній бакет” добавлены quick links: `Політика`, `Аудит`, `Доставка`.

## Стабилизация gates

Файл: `scripts/admin_panel_smoke_gate.sh`.

- Добавлены ретраи для transient `502/503/504/000` на уровне endpoint-check (уменьшает флейк на прогреве nginx/upstream).

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack8-history-checklist.md`

