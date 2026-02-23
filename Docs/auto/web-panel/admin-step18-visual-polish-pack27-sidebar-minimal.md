# Admin step-18 visual polish — pack-27 (sidebar minimal)

- date: `2026-02-17`
- scope: `admin sidebar`
- goal: убрать визуальную перегрузку слева, оставить “чистую” навигацию по умолчанию.

## Что изменено

1. `Simple` sidebar стал действительно минимальным:
- скрываются все mini-блоки sidebar (включая `favorites/recent/session`), остаётся только `меню -> подменю`.

2. `Фокус` sidebar = nav-only:
- режим фокуса показывает только навигацию, без вспомогательных sidebar-блоков.

3. Performance/шум:
- mission-ticker обновления выполняются только когда mission sidebar реально активен (не в `Simple` и не в `Фокус`).

## Код

- `backend/app/admin_ui_kit.py`

## Server-first валидация

- deploy: `rsync` → `/opt/passengers-backend/app/admin_ui_kit.py`
- VPS: `python3 -m py_compile app/admin_ui_kit.py` + `docker compose ... restart api`
- `scripts/admin_panel_smoke_gate.sh` — `PASS`
- `scripts/client_panel_step17_handoff_check.sh` — `PASS` (см. checklist ниже)

## Артефакты

- `Docs/auto/web-panel/client-step17-handoff-checklist-pack27b.md` (PASS)
- `Docs/auto/web-panel/client-step17-handoff-checklist-pack27.md` (FAIL, причина: warmup/502 сразу после restart)

