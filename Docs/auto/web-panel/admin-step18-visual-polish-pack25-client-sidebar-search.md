# Admin step-18 (pack-25): Client sidebar search (cross-panel UX parity)

Дата: 2026-02-17

## Цель

Зафиксировать единый core-паттерн навигации: в admin sidebar уже есть поиск, в client sidebar добавлен аналогичный (минималистичный) поиск по пунктам меню.

## Изменения (Core)

Файл: `backend/app/client_ui_kit.py`

- Добавлен поиск по меню клиента (input + фильтрация групп/ссылок + hotkey).

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/admin-step18-visual-polish-pack25-client-sidebar-search-checklist.md`).

