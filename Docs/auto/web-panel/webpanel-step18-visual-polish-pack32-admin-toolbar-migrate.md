# Web-panel step-18 visual polish — pack-32 (admin toolbar migrate)

- date: `2026-02-17`
- scope: `admin`
- goal: довести всі admin сторінки до одного канону header toolbar (2 ряди) без побічних ефектів для inline `.toolbar` всередині сторінок.

## Что изменено

1. Core: container-стиль toolbar застосовується тільки в header

- `.toolbar` як inline-row збережено для використання всередині сторінок (actions rows).
- Container-стиль (`padding/border/background`) тепер тільки для `header .toolbar`.
- Додано `toolbarBtn` для навігаційних `<a>` у header toolbar (виглядає як кнопка).

Файл:

- `backend/app/admin_ui_kit.py`

2. Admin pages: міграція решти toolbar_html на `toolbarMain + toolbarMeta`

Переведено:

- `backend/app/admin_overview_page.py`
- `backend/app/admin_commission_page.py`
- `backend/app/admin_wg_page.py`
- `backend/app/admin_fleet_history_page.py`
- `backend/app/admin_fleet_policy_page.py`
- `backend/app/admin_fleet_notifications_page.py`
- `backend/app/admin_fleet_actions_page.py`
- `backend/app/admin_fleet_central_page.py`
- `backend/app/admin_fleet_incident_detail_page.py`

Правила:

- `copyLink` більше не `smallbtn` (єдиний розмір контролів в toolbar).
- `filterSummary/status` винесені в `toolbarMeta` (коли присутні).
- Навігаційні лінки в incident detail toolbar переведені на `toolbarBtn`.

3. Docs/Skill: канон зафіксовано

- Core doc: уточнення по admin toolbar + `toolbarBtn`.
- UI/UX skill: додані правила по `toolbarBtn`.

Файли:

- `Docs/Проект/Веб-панель/Ядро (Core).md`
- `skills/orangepi-passengers-webpanel-uiux/SKILL.md`

## Server-first валидация

- deploy на VPS: `rsync` змінених admin файлів
- VPS: `py_compile` + restart `api`
- `scripts/admin_panel_smoke_gate.sh` — PASS (після прогріву)
- `scripts/client_panel_step17_handoff_check.sh` — PASS:
  - `Docs/auto/web-panel/client-step17-handoff-checklist-pack32b.md`

Примечание:

- перший прогон smoke/step-17 одразу після restart може ловити `502` у warmup; verdict фіксуємо після повторного прогону.

