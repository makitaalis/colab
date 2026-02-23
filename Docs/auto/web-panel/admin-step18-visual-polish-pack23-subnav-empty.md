# Admin step-18 (pack-23): Subnav scroll + empty tables (clean hierarchy)

Дата: 2026-02-17

## Цель

1. Уменьшить визуальную высоту header/subnav (особенно когда подпунктов много).
2. Сделать пустые таблицы понятными (вместо “пустого прямоугольника”).

## Изменения (Core)

Файл: `backend/app/admin_ui_kit.py`

1. `pageSubnav`:
- переведён в горизонтальный scroll (без многострочного wrap),
- добавлен sticky label слева (чтобы “Контекст” не терялся при скролле),
- добавлены `scroll-snap` и thin scrollbar для контролируемого ощущения.
2. Empty-state таблиц:
- добавлены стили `.emptyState`, `.tableEmptyRow`,
- в JS добавлена авто-вставка строки `Немає даних` для пустых таблиц внутри `.tableWrap`.

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/admin-step18-visual-polish-pack23-subnav-empty-checklist.md`).

