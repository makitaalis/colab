# Admin step-18 visual polish: pack-14 (incident detail triage-first)

Дата: 2026-02-17

Цель: сделать `/admin/fleet/incidents/{central_id}/{code}` более “triage-first”: короткий primary toolbar, явные источники данных, длинные сообщения и raw-debug не должны перегружать первый экран.

## Изменения (Domain: Флот)

Файл: `backend/app/admin_fleet_incident_detail_page.py`.

1) Header chips вместо “простыни” в toolbar
- `роль` и `оновлено` перенесены в header chips.
- Toolbar оставляет только primary действия: `Оновити`, `авто`, `Скопіювати посилання`, `status`.

2) “Поточний стан”: быстрые переходы + tableMeta
- Добавлены quick links по сценарию: інциденти / журнал дій / доставка / policy / аудит.
- Добавлен `tableMeta` с источником endpoint и ключом `(central_id, code)`.

3) Сообщение инцидента без визуальной перегрузки
- В primary показана короткая строка `повідомлення: …` (trim).
- Полный текст вынесен в `<details class="advancedDetails" data-advanced-details="1">`.

4) Debug вынесен в secondary details
- Добавлен блок `Діагностика (raw payload)` как `<details class="domainSplitDetails" data-advanced-details="1">` с copy-кнопкой.

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack14-incident-detail-checklist.md`

