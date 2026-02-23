# Client step-18 (pack-25): Sidebar search (short menu + no overload)

Дата: 2026-02-17

## Цель

- Уменьшить когнитивную нагрузку от левого меню при росте количества разделов.
- Дать быстрый поиск по пунктам меню без прокрутки.

## Изменения (Core)

Файл: `backend/app/client_ui_kit.py`

1. В sidebar добавлен поиск по меню:
- поле `clientSideNavFilter` в верхней части sidebar,
- статус/счётчик результатов `clientSideNavFilterStatus`.
2. Логика фильтрации:
- скрывает пункты и группы без совпадений,
- при активном поиске временно раскрывает группы,
- `Esc` очищает поиск, `ArrowDown` фокусирует первый результат, `Enter` открывает если результат один.
3. Горячая клавиша:
- `Alt+Shift+N` фокус на поиск меню (обновлено в подсказке hotkeys).

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/client-step18-visual-polish-pack25-client-sidebar-search-checklist.md`).

