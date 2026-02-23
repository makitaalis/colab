# Web-panel step-18 visual polish — pack-31 (admin toolbar rows)

- date: `2026-02-17`
- scope: `admin`
- goal: сделать toolbar предсказуемым и “чистым”: controls отдельно, meta/status отдельно; убрать случайную разнобойность размеров кнопок.

## Что изменено

1. Core: admin toolbar получил канон `toolbarMain + toolbarMeta`

- В `.toolbar` добавлен контейнерный стиль (padding/border/background) для визуальной группировки controls.
- Добавлены правила для:
  - `.toolbarMain` (controls + advanced `<details>`),
  - `.toolbarMeta` (filterSummary/status).
- Mobile (<=760px): элементы внутри `toolbarMain/toolbarMeta` становятся в колонку (100% ширины).

Файл:

- `backend/app/admin_ui_kit.py`

2. Ключевые страницы admin переведены на новый toolbar-каркас

- `fleet`, `alerts`, `incidents`, `audit`, `notify-center`:
  - toolbar разбит на `toolbarMain` и `toolbarMeta`;
  - `copyLink` больше не `smallbtn` (единый размер контролов в toolbar).

Файлы:

- `backend/app/admin_fleet_page.py`
- `backend/app/admin_fleet_alerts_page.py`
- `backend/app/admin_fleet_incidents_page.py`
- `backend/app/admin_audit_page.py`
- `backend/app/admin_fleet_notify_center_page.py`

3. Docs/Skill: канон admin toolbar закреплён

- Core doc: добавлен раздел `Admin toolbar`.
- UI/UX skill: добавлены правила `toolbarMain/toolbarMeta` для admin.

Файлы:

- `Docs/Проект/Веб-панель/Ядро (Core).md`
- `skills/orangepi-passengers-webpanel-uiux/SKILL.md`

## Server-first валидация

- deploy на VPS: `rsync` изменённых admin файлов
- VPS: `py_compile` + restart `api`
- `scripts/admin_panel_smoke_gate.sh` — PASS (после прогрева)
- `scripts/client_panel_step17_handoff_check.sh` — PASS:
  - `Docs/auto/web-panel/client-step17-handoff-checklist-pack31b.md`

Примечание:

- первый прогон после restart может ловить `502` на части client API endpoints в warmup. Для verdict используем повтор после прогрева.

