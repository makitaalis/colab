# Web-panel step-18 visual polish — pack-28 (chips без навигации)

- date: `2026-02-17`
- scope: `admin+client`
- goal: chips в header = только контекст, навигацию вынести в subnav/toolbar, снизить “шум” в header.

## Что изменено

1. Client: убраны навигационные ссылки из header chips

- Удалены `<a class="chip" ...>` переходы между страницами.
- Навигация остаётся в:
  - sidebar (`меню -> подменю`),
  - `clientSubnav` под заголовком (контекст текущего раздела).

Файлы:

- `backend/app/client_home_page.py`
- `backend/app/client_vehicles_page.py`
- `backend/app/client_tickets_page.py`
- `backend/app/client_status_page.py`
- `backend/app/client_profile_page.py`
- `backend/app/client_notifications_page.py`

2. Admin: incident detail — навигация вынесена в toolbar

- `chips_html` оставлен только для контекста (incident/workspace/role/updatedAt).
- Ссылки “← інциденти” и “вузол” перенесены в `toolbar_html` и получают корректные `href` через JS.

Файл:

- `backend/app/admin_fleet_incident_detail_page.py`

3. Skill: зафиксирован запрет ссылок в chips

- В UI/UX skill добавлено правило: `<a class="chip"...>` запрещены, любые переходы живут в `subnav`/`toolbar`.

Файл:

- `skills/orangepi-passengers-webpanel-uiux/SKILL.md`

## Server-first валидация

- deploy на VPS: `rsync` изменённых `*_page.py`
- VPS: `py_compile` + restart `api`
- `scripts/admin_panel_smoke_gate.sh` — PASS
- `scripts/client_panel_step17_handoff_check.sh` — PASS:
  - `Docs/auto/web-panel/client-step17-handoff-checklist-pack28b.md`

Примечание:

- первый прогон step-16 в составе step-17 может ловить `502` на `/client` сразу после restart (warmup). При повторе после прогрева — PASS.

