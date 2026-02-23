# Client step-18 (pack-24): Section rhythm + empty-state tones (clean pages)

Дата: 2026-02-17

## Цель

- Сделать карточки и секции визуально “ровными” (одинаковый заголовок и отступы).
- Убрать ручные “пустые строки таблицы” из JS и заменить на единый core empty-state с тоном (`OK` как good).

## Изменения (Core)

Файл: `backend/app/client_ui_kit.py`

1. Добавлены секционные классы:
- `.sectionTitle`, `.sectionKicker`,
- `.sectionHead`, `.sectionTools` (как в admin, но в light-теме).
2. Empty-state таблиц:
- поддержка `data-empty-title`, `data-empty-text`, `data-empty-tone`,
- добавлены tone-стили `.emptyState.tone-*`,
- `applyEmptyTables()` экспортирован как `ClientUiKit.applyEmptyTables()`.

## Изменения (Domains)

1. Табличные страницы клиента переведены на core empty-state:
- `backend/app/client_home_page.py` (attention: `OK` tone-good),
- `backend/app/client_vehicles_page.py` (focus: `OK` tone-good, all: neutral),
- `backend/app/client_tickets_page.py` (active: `OK` tone-good, archive: neutral),
- `backend/app/client_status_page.py` (focus: `OK` tone-good, all: neutral).
2. Убраны inline-заголовки секций в пользу `.sectionTitle`:
- `backend/app/client_profile_page.py`
- `backend/app/client_notifications_page.py`

## Проверки

1. VPS deploy + `py_compile`: PASS.
2. `scripts/admin_panel_smoke_gate.sh`: PASS.
3. `scripts/client_panel_step17_handoff_check.sh`: PASS (`Docs/auto/web-panel/client-step18-visual-polish-pack24-sections-emptytone-checklist.md`).

