# Admin step-18 visual polish: pack-17 (incidents list без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/fleet/incidents` более “triage-first”: operator route и таблица инцидентов должны быть главным экраном, а пресеты/cockpit/rollout и вторичная аналитика не должны создавать вертикальный шум.

## Изменения (Domain: Флот)

Файл: `backend/app/admin_fleet_incidents_page.py`.

1) Operator route: меньше вертикального шума
- Убран блок `<details class="advancedDetails">` из flow-карты.
- В flow-блоке оставлены только контекст и базовые действия:
  - `workspaceHint`
  - `Підставити контекст`
  - `Очистити контекст`
  - `Команди`

2) Advanced tools вынесены в отдельный `<details>`
- Добавлен блок:
  - `<details id="incToolsDetails" class="domainSplitDetails" data-advanced-details="1">…</details>`
- Persistence key: `passengers_admin_incidents_tools_details_v1`.
- Внутри: пресеты, кокпіт, rollout, observability hints.

3) Secondary analytics: меньше визуального шума
- Убрана лишняя вложенная `.card` вокруг таблицы delivery-журнала внутри `incSecondaryDetails`.

4) Toolbar унифицирован
- Кнопка reset переименована в `Скинути` (единый copy по админке).

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack17-incidents-list-checklist.md`

