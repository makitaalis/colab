# Admin step-18 visual polish: pack-7 (policy без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/fleet/policy` более минималистичным: primary экран про пороги, advanced настройки авто-сповіщень и override-сценарий не должны создавать “простыню”.

## Изменения (Domain: Контроль и KPI)

Файл: `backend/app/admin_fleet_policy_page.py`.

1) Primary: пороги и сохранение
- Primary контур оставляет только пороги (heartbeat/queue/wg) + `refresh/save` + статус.
- Добавлен `tableMeta` с API источниками.

2) Advanced: авто-сповіщення вынесены в `<details>`
- Новый блок: `<details id="policyAutoDetails" class="domainSplitDetails" data-advanced-details="1">`.
- Persistence key: `passengers_admin_policy_auto_details_v1`.
- Кнопки `Авто зараз (dry-run)` и `Авто зараз` перенесены внутрь advanced блока.

3) Secondary: override-контур
- `policySecondaryDetails` помечен `data-advanced-details="1"` (Simple-mode схлопывает).
- Убрана лишняя вложенная `.card` внутри secondary (меньше визуального шума).

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack7-policy-checklist.md`

