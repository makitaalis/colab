# Client step-18 (pack-22): Tables polish (readability + maintainable CSS)

Дата: 2026-02-17

## Цель

1. Улучшить читаемость таблиц в client shell (sticky header, zebra/hover, скролл-ритм).
2. Привести базовый CSS клиента к единому читабельному виду (чтобы Core правила проще поддерживать).

## Изменения (Core)

Файл: `backend/app/client_ui_kit.py`

1. Исправлено определение `_base_client_css()`:
- функция возвращена на модульный уровень (не должна быть вложенной в другую функцию),
- CSS блок отформатирован в многострочный вид для maintenance.
2. Таблицы:
- `.tableWrap` получил `max-height: 72vh`, `scrollbar-gutter: stable`, стилизацию скроллбаров,
- `table` получил `min-width: 880px` и `font-variant-numeric: tabular-nums`,
- sticky `th` + `white-space: nowrap`,
- zebra + hover для сканирования строк.

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/client-step18-visual-polish-pack22-tables-checklist.md`).

