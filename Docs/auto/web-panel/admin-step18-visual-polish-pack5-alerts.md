# Admin step-18 visual polish: pack-5 (alerts без перегруза)

Дата: 2026-02-17

Цель: снизить визуальную перегрузку `/admin/fleet/alerts`, оставив в primary только оперативный triage, а агрегированную “работу по коду” вынести во secondary.

## Изменения (Domain: Флот)

Файл: `backend/app/admin_fleet_alerts_page.py`.

1) Secondary: “Групи алертів за кодом”
- Блок группировки по коду вынесен в `<details id="alertsSecondaryDetails" class="domainSplitDetails" data-advanced-details="1">`.
- По умолчанию secondary свернут (страница короче, меньше вертикального шума).

2) Persistence secondary
- Состояние secondary details сохраняется в `localStorage`:
  - key: `passengers_admin_alerts_secondary_details_v1`

## Качество gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 handoff checklist (регрессия): `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack5-alerts-checklist.md`

## Примечание (gates)

Стабилизирован regression gate клиента (флак):
- `scripts/client_panel_regression_check.sh`: marker-check теперь retry x3 (warmup после restart/deploy).

