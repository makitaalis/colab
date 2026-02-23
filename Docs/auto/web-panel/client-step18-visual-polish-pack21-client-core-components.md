# Client step-18 (pack-21): Core components polish (controls/details/motion)

Дата: 2026-02-17

## Цель

Сделать клиентский UI визуально ровным и минималистичным:

- единая высота контролов,
- аккуратные hover/active состояния без “дрожания”,
- единый паттерн `<details>` для secondary-блоков,
- уважение `prefers-reduced-motion`.

## Изменения (Client Core)

Файл: `backend/app/client_ui_kit.py`

1. Добавлена переменная `--ctl-h: 34px` и применена к:
- `sideCompactBtn`,
- `clientToolbar` inputs/select/buttons,
- `row` inputs/select.
2. `secondaryDetails`:
- скрыт marker и добавлен chevron (`▸/▾`) в summary.
3. Добавлен `@media (prefers-reduced-motion: reduce)` для отключения transitions.
4. Hover-стили `sideCompactBtn` унифицированы с остальными контролами (border + лёгкий lift).

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/client-step18-visual-polish-pack21-client-core-components-checklist.md`).

