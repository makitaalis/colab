# Admin step-18 — Visual polish pack 1 (header declutter + split-details unification)

- date: `2026-02-17`
- scope: `admin core`

## Цель

Снизить визуальную перегрузку admin-страниц:

- убрать дублирующую навигацию из header (chips больше не “второе меню”);
- унифицировать `domainSplitDetails` стиль в `Core`;
- сделать переключение `Просто/Розширено` менее “шумным” (не авто-раскрывать длинные блоки).

## Изменения (код)

- `backend/app/admin_ui_kit.py`
  - добавлен общий стиль `.domainSplitDetails` / `.domainSplitHint`;
  - `applySidebarSimpleMode`: при включении `Simple` закрывает `details[data-advanced-details="1"]`, но при выключении `Simple` не раскрывает их автоматически.
- Header declutter (убраны nav-links chips, оставлен только контекст):
  - `backend/app/admin_fleet_page.py`
  - `backend/app/admin_fleet_alerts_page.py`
  - `backend/app/admin_fleet_incidents_page.py`
  - `backend/app/admin_fleet_incident_detail_page.py`
  - `backend/app/admin_fleet_actions_page.py`
  - `backend/app/admin_fleet_notifications_page.py`
  - `backend/app/admin_fleet_notify_center_page.py`
  - `backend/app/admin_fleet_policy_page.py`
  - `backend/app/admin_fleet_history_page.py`
  - `backend/app/admin_fleet_central_page.py`
  - `backend/app/admin_audit_page.py`
  - `backend/app/admin_commission_page.py`
  - `backend/app/admin_wg_page.py`

## Server-first проверка

Выкатка:

1. `rsync` обновлённых `admin_*` модулей в `/opt/passengers-backend/app`.
2. `python3 -m py_compile ...` на сервере.
3. `docker compose -f compose.yaml -f compose.server.yaml up -d --build api`.

Контроль:

- `scripts/admin_panel_smoke_gate.sh` — `PASS`
- `scripts/server_security_posture_check.sh` — `PASS`
- RC/handoff gate: `scripts/client_panel_step17_handoff_check.sh` — `PASS`

## Следующий пакет (step-18)

- привести “перегруженные” страницы к одному паттерну `Primary + Secondary` без дублирования действий в нескольких местах;
- сделать визуальную унификацию `sectionHead/summary/tableMeta` (одинаковый ритм и отступы).
