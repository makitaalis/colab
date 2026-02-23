# Web-panel step-18 visual polish — pack-30 (client toolbar rows)

- date: `2026-02-17`
- scope: `client`
- goal: убрать “кашу” в toolbar при переносах строк и зафиксировать единый порядок controls/meta.

## Что изменено

1. Core: toolbar разделён на 2 ряда

- `clientToolbar` теперь column-контейнер.
- Внутри введены:
  - `.toolbarMain` (controls),
  - `.toolbarMeta` (metaChip/status).
- На mobile правила ширины применяются к элементам внутри `.toolbarMain/.toolbarMeta`.

Файл:

- `backend/app/client_ui_kit.py`

2. Client pages: toolbar_html приведён к канону

- Все client страницы переведены на структуру `toolbarMain + toolbarMeta`.
- Внутри toolbar убраны лишние классы `smallbtn` у кнопок (стиль задаёт Core).

Файлы:

- `backend/app/client_home_page.py`
- `backend/app/client_vehicles_page.py`
- `backend/app/client_tickets_page.py`
- `backend/app/client_status_page.py`
- `backend/app/client_profile_page.py`
- `backend/app/client_notifications_page.py`

3. Docs/Skill: канон toolbar rows зафиксирован

- Core doc: добавлен раздел `Client toolbar`.
- UI/UX skill: добавлено правило `toolbarMain/toolbarMeta` + запрет `smallbtn` в toolbar.

Файлы:

- `Docs/Проект/Веб-панель/Ядро (Core).md`
- `skills/orangepi-passengers-webpanel-uiux/SKILL.md`

## Server-first валидация

- deploy на VPS: `rsync` изменённых client файлов
- VPS: `py_compile` + restart `api`
- `scripts/admin_panel_smoke_gate.sh` — PASS (после прогрева)
- `scripts/client_panel_step17_handoff_check.sh` — PASS:
  - `Docs/auto/web-panel/client-step17-handoff-checklist-pack30b.md`

Примечание:

- первый прогон после restart может ловить `502` на отдельных HTML endpoints (warmup). Для verdict используем повтор после прогрева.

