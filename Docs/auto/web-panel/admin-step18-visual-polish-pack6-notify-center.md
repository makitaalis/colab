# Admin step-18 visual polish: pack-6 (notify-center без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/fleet/notify-center` визуально короче и “собраннее”: context chips в header, короткий primary toolbar, фильтры и детальный журнал не должны давить на первый экран.

## Изменения (Domain: Сповіщення)

Файл: `backend/app/admin_fleet_notify_center_page.py`.

1) Header chips
- `оновлено: …` перемещено из toolbar в header chips (контекст, а не действие).

2) Toolbar: primary vs advanced
- В toolbar оставлены первичные действия: `авто`, `скинути`, `оновити`, `copy link`, `filterSummary`.
- Фильтры (window/status/channel/central/code/q/dry-run) перенесены в `<details class="toolbarDetails" data-advanced-details="1">`.

3) Secondary details помечены как advanced
- `notifySecondaryDetails` теперь `data-advanced-details="1"` (Simple-mode автоматически схлопывает).

4) Убрана лишняя вложенная “карточка” вокруг таблицы
- Внутри secondary оставлены `tableMeta + tableWrap` без дополнительного `.card` (меньше визуального шума).
- Добавлен `notifySinceChip` (показывает `since_ts`).

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack6-notify-center-checklist.md`

