# Admin step-18 (pack-26): Header chips (horizontal scroll) + robust empty-state

Дата: 2026-02-17

## Цель

- Уменьшить визуальную “высоту” header: chips не должны превращаться в многострочную простыню.
- Сделать empty-state таблиц безопасным при динамической подгрузке данных (empty-row должен исчезать, когда появляются строки).

## Изменения (Core)

Файл: `backend/app/admin_ui_kit.py`

1. Header chips:
- chips вынесены в отдельный контейнер `.headerChips`,
- `.headerChips` работает как горизонтальный scroll (nowrap + overflow-x) с thin scrollbar,
- заголовок страницы остаётся стабильным, chips больше не раздувают header в 2–4 строки.
2. Empty-state таблиц:
- `applyEmptyTables()` теперь удаляет `tr.tableEmptyRow`, если в таблице появились реальные строки.

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/admin-step18-visual-polish-pack26-header-chips-checklist.md`).

