# Admin step-18 visual polish: pack-11 (wg без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/wg` более минималистичным в primary контуре: быстрый поиск и обновление сверху, конфиг сервера строго во вторичном блоке, источник и SLA рукопожатий читаются сразу в `tableMeta`.

## Изменения (Domain: Інфраструктура)

Файл: `backend/app/admin_wg_page.py`.

1) Toolbar: чистый primary
- Убрана кнопка `Конфіг сервера` из primary toolbar (конфиг доступен во вторичном `<details>`).
- Добавлен `Скинути` (reset `q`) с синхронизацией URL и refresh.

2) Таблица пірів: `tableMeta` вместо “подсказки”
- Добавлен `tableMeta` над таблицей:
  - `джерело: /api/admin/wg/peers`
  - `сортування: name ↑`
  - `оновлення: ~15s`
  - `SLA: good ≤ 120s, warn ≤ 600s`

3) Secondary details помечены как advanced
- `wgSecondaryDetails` теперь `data-advanced-details="1"`: Simple-mode схлопывает вторичную диагностику.
- Убрана лишняя вложенная `.card` внутри secondary (меньше визуального шума).

## Gates

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 checklist: `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack11-wg-checklist.md`

