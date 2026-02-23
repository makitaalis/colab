# Web-panel step-18 visual polish — pack-29 (client toolbar rhythm)

- date: `2026-02-17`
- scope: `client`
- goal: сделать toolbar визуально “чистым” и единообразным, а `updatedAt` перенести в контекст (chips).

## Что изменено

1. `clientToolbar` стал контейнером уровня Core

- добавлены `padding/border/background` (как у subnav), чтобы controls не “висели в воздухе” и визуально читались как единый блок.

Файл:

- `backend/app/client_ui_kit.py`

2. `updatedAt` вынесен из toolbar в chips (контекст)

- `updatedAt` считается контекстом страницы и теперь живёт в `chips_html`, а toolbar остаётся controls-only.

Файлы:

- `backend/app/client_home_page.py`
- `backend/app/client_status_page.py`

3. Skill обновлён правилом toolbar rhythm

- добавлен канон: `clientToolbar = controls-only`, `updatedAt` в chips, container-style в Core.

Файл:

- `skills/orangepi-passengers-webpanel-uiux/SKILL.md`

## Server-first валидация

- deploy на VPS: `rsync` (`client_ui_kit.py`, `client_home_page.py`, `client_status_page.py`)
- VPS: `py_compile` + restart `api`
- `scripts/admin_panel_smoke_gate.sh` — PASS (после прогрева)
- `scripts/client_panel_step17_handoff_check.sh` — PASS:
  - `Docs/auto/web-panel/client-step17-handoff-checklist-pack29b.md`

Примечание:

- сразу после restart возможны единичные `502/503` в warmup (nginx/upstream). Для итогового статуса используем повторный прогон после прогрева.

