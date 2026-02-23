# Client step-18 (pack-26): Header chips (horizontal scroll) + robust empty-state

Дата: 2026-02-17

## Цель

- Уменьшить “высоту” header в client shell: chips теперь в одну строку с горизонтальным скроллом.
- Укрепить empty-state таблиц: пустая строка не должна оставаться, если данные уже отрисованы.

## Изменения (Core)

Файл: `backend/app/client_ui_kit.py`

1. `.clientChips` переведён на nowrap + horizontal scroll.
2. `applyEmptyTables()` теперь удаляет `tr.tableEmptyRow`, если таблица содержит реальные строки.

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/client-step18-visual-polish-pack26-header-chips-checklist.md`).

