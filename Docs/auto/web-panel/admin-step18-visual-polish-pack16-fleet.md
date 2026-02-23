# Admin step-18 visual polish: pack-16 (fleet без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/fleet` менее перегруженной сверху: operator route и контекст доступны сразу, а пресеты/cockpit/rollout не занимают первичный экран.

## Изменения (Domain: Флот)

Файл: `backend/app/admin_fleet_page.py`.

1) Operator route: меньше вертикального шума
- Убран “простынный” `<details class="advancedDetails">` из flow-карты.
- Контекст инцидента и базовые действия оставлены прямо в flow-блоке:
  - `workspaceHint`
  - `Підставити контекст`
  - `Очистити контекст`
  - `Команди`

2) Advanced tools вынесены в отдельный secondary `<details>`
- Добавлен блок:
  - `<details id="fleetToolsDetails" class="domainSplitDetails" data-advanced-details="1">…</details>`
- Persistence key: `passengers_admin_fleet_tools_details_v1`.
- Внутри: пресеты, cockpit, rollout, observability hints.

3) Secondary analytics помечена как advanced
- `fleetSecondaryDetails` теперь `data-advanced-details="1"` (Simple-mode схлопывает вторичную аналитику).

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack16-fleet-checklist.md`

