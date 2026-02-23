# Admin step-18 visual polish: pack-12 (notification rules без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/fleet/notifications` менее перегруженной: правила остаются в primary контуре, тестовая доставка уходит во вторичный сценарий; источники API читаются сразу.

## Изменения (Domain: Сповіщення)

Файл: `backend/app/admin_fleet_notifications_page.py`.

1) Primary: явный источник правил
- Добавлен `tableMeta` над блоком правил:
  - `джерело: /api/admin/fleet/notification-settings`
  - `контур: глобальні правила`

2) Secondary: тестовая доставка вынесена в `<details>`
- Тестовый блок перенесён в:
  - `<details id="notificationsSecondaryDetails" class="domainSplitDetails" data-advanced-details="1">…</details>`
- Persistence key: `passengers_admin_notifications_secondary_details_v1`.
- Добавлен доменный hint с переходом в `/admin/fleet/notify-center` для triage.

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack12-notification-rules-checklist.md`

