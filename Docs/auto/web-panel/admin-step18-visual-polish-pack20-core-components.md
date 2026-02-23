# Admin step-18 (pack-20): Core components polish (focus/controls/details)

Дата: 2026-02-17

## Цель

Сделать интерфейс визуально “ровным” без правок каждой страницы:

- единые размеры контролов (кнопки/инпуты в toolbar),
- понятный keyboard-focus (`:focus-visible`),
- единый паттерн `<details>` (chevron + open-state),
- исправить “сломанный” формат CSS в media-query блоках.

## Изменения (Core)

Файл: `backend/app/admin_ui_kit.py`

1. Добавлен `:focus-visible` для `a/button/summary/input/select/textarea`.
2. Единая высота контролов через `--ctl-h: 34px`:
- `toolbar` inputs/select,
- глобальные `button` (и `button.primary`).
3. `button.primary` теперь визуально стабильный (border + hover).
4. `<details>`:
- добавлен chevron (`▸`) и ротация при `open` для `details.toolbarDetails` и `details.advancedDetails`.
5. CSS maintenance:
- выправлен формат блока `@media (max-width: 1080px)`,
- добавлен `prefers-reduced-motion: reduce`.

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/admin-step18-visual-polish-pack20-core-components-checklist.md`).

