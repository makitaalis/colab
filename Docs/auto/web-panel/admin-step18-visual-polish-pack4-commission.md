# Admin step-18 visual polish: pack-4 (commissioning без перегруза)

Дата: 2026-02-17

Цель: сделать `/admin/commission` современным и минималистичным, без “простыни” из карточек и перегруженного toolbar, сохранив E2E commissioning сценарий.

## Изменения (Domain: Старт)

Файл: `backend/app/admin_commission_page.py`.

1) Toolbar: primary vs advanced
- В toolbar оставлены только первичные элементы: `central_id` + `copy commands` + `copy page` + контекст.
- Остальные параметры (IP/vehicle/plate + вспомогательные кнопки) перенесены в `<details class="toolbarDetails" data-advanced-details="1">`.

2) Страница: primary vs secondary
- Primary контур теперь состоит из двух карточек:
  - `Комісія: статус і наступні дії`: объединены backend status + WG status в 2-колоночный grid, quick-links и кнопки refresh.
  - `Команди (копіпаст)`.
- Secondary контур вынесен в `<details class="domainSplitDetails" data-advanced-details="1">`:
  - полный чеклист commissioning,
  - локальные проверки (runs),
  - локальные профили.

3) Persistence secondary
- Состояние secondary details сохраняется в `localStorage`:
  - key: `passengers_admin_commission_secondary_details_v1`

## Проверки (server-first)

1) Admin smoke gate: `PASS`
- `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"`
2) Step-17 handoff checklist (регрессия): `PASS`
- `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/admin-step18-visual-polish-pack4-commission-checklist.md`

## Результат для UX

- Верх страницы отвечает на один вопрос: “готово ли подключение и что делать дальше”.
- Скрыта вторичная “операционная документация” (runs/profiles/checklist) без потери доступа.
- Toolbar перестал быть длинной линейкой из 15+ контролов.

