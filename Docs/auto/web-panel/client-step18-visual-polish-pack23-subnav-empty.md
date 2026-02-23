# Client step-18 (pack-23): Subnav scroll + empty tables (clean hierarchy)

Дата: 2026-02-17

## Цель

- Сделать header/subnav более “плоским” визуально (меньше высоты, меньше шума).
- Сделать пустые таблицы понятными без дополнительных правок каждой страницы.

## Изменения (Core)

Файл: `backend/app/client_ui_kit.py`

1. `clientSubnav`:
- добавлен контейнерный стиль (рамка/фон),
- включён горизонтальный scroll вместо переносов строк,
- добавлен thin scrollbar + `scroll-snap`.
2. Empty-state таблиц:
- добавлены стили `.emptyState`, `.tableEmptyRow`,
- в `initShell()` добавлена авто-вставка строки `Немає даних` для пустых таблиц внутри `.tableWrap`.

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/client-step18-visual-polish-pack23-subnav-empty-checklist.md`).

