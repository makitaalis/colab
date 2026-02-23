# Домен Контроль и KPI

## Назначение

Политики мониторинга, исторические KPI и аудит действий.

## Route scope

- `/admin/fleet/history`
- `/admin/fleet/policy`
- `/admin/audit`

## API scope

- `/api/admin/fleet/monitor-policy`
- `/api/admin/fleet/monitor-policy/overrides`
- `/api/admin/fleet/metrics/history`
- `/api/admin/audit`

## UX-контракт домена

1. Конфигурация (`policy`) и контроль исполнения (`audit/history`) отображаются раздельно.
2. В каждом отчёте видны окно данных и источник.
3. Любое изменение policy сопровождается явной фиксацией статуса.

## Ограничения

- не добавлять оперативные triage-действия из домена `Флот`;
- не размещать сетевую диагностику (это домен `Інфраструктура`).

## Definition of Done

1. Policy override редактируется без потери контекста `central_id`.
2. История KPI и аудит поддерживают shareable URL.
3. Статусы `ok/forbidden/error` читаются без дополнительной расшифровки.

## Прогресс content-split (2026-02-16)

- `/admin/fleet/policy` разгружен по сценарию:
  - primary: `Глобальна політика моніторингу` (пороги + авто-health);
  - secondary: `Персональні override-и` перенесены в сворачиваемый блок.
- Состояние secondary-блока сохраняется локально:
  - key: `passengers_admin_policy_secondary_details_v1`.
- UX-эффект:
  - первичный policy-контур читается без перегрузки;
  - override-сценарий доступен по запросу и не мешает базовой настройке политики.

## Прогресс visual polish (2026-02-17)

- `/admin/fleet/policy` доведен по visual-density:
  - авто-сповіщення вынесены в advanced `<details>` (persistent):
    - key: `passengers_admin_policy_auto_details_v1`.
  - override-контур помечен `data-advanced-details="1"` (Simple-mode схлопывает).

- `/admin/fleet/history` доведен по visual-density:
  - primary toolbar оставляет действия, параметры окна вынесены в advanced `<details class="toolbarDetails">`;
  - добавлен явный reset фільтрів (standard: `24h` + `300s`) + shareable URL;
  - добавлен `tableMeta` с источником `/api/admin/fleet/metrics/history` и чипом `вікно: …`.

- `/admin/audit` доведен по visual-density:
  - фильтры вынесены в advanced `<details class="toolbarDetails">`, primary toolbar оставляет действия;
  - `оновлено: …` перенесено в header chips;
  - добавлен `tableMeta` с источником `/api/admin/audit` и чипом `вікно: …`.
