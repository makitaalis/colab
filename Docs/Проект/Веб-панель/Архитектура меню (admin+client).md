# Архитектура меню (admin+client)

Документ фиксирует каноничную IA-структуру `меню -> подменю` для web-панели, чтобы убрать перегрузку левого sidebar и разнести контент по понятным категориям.

Связанные стандарты:

- `Docs/Проект/Веб-панель (ядро и домены).md`
- `Docs/Проект/Веб-панель/Ядро (Core).md`
- `Docs/Проект/Админ-панель (UI-UX стандарт).md`

## 1) Принципы IA

1. Всегда 2 уровня навигации: `раздел -> подменю`.
2. В sidebar раскрыт только активный раздел.
3. На странице показывается только один primary-сценарий сверху.
4. Secondary-контент уходит в подменю или в `<details>`, но не в длинный вертикальный список.
5. `Simple`-режим sidebar = “hub-only”: в доменах видны только входы в разделы, а подменю живёт в `page subnav` на странице (и раскрывается при поиске по меню).
6. `Фокус`-режим sidebar = nav-only: только `раздел -> подменю` без вспомогательных sidebar-блоков.
7. Для клиента и админа единый каркас shell, но разная плотность данных.
8. Изменения IA вносятся только через `*_core/navigation.py` и `*_domains/domain_catalog.py`.

## 2) Канон меню admin

1. `Старт`
- `Огляд системи` (`/admin`, v2: `/admin2`)
- `Підключення` (`/admin/commission`, v2: `/admin2/commission`)

2. `Флот`
- `Стан флоту` (`/admin/fleet`, v2: `/admin2/fleet`)
- `Алерти` (`/admin/fleet/alerts`, v2: `/admin2/fleet/alerts`)
- `Інциденти` (`/admin/fleet/incidents`, v2: `/admin2/fleet/incidents`)
- `Дії операторів` (`/admin/fleet/actions`, v2: `/admin2/fleet/actions`)

3. `Сповіщення`
- `Доставка` (`/admin/fleet/notify-center`, v2: `/admin2/notify-center`)
- `Правила каналів` (`/admin/fleet/notifications`, v2: `/admin2/notifications`)

4. `Контроль і KPI`
- `Історія KPI` (`/admin/fleet/history`, v2: `/admin2/kpi/history`)
- `Політика` (`/admin/fleet/policy`, v2: `/admin2/policy`)
- `Аудит` (`/admin/audit`, v2: `/admin2/audit`)

5. `Інфраструктура`
- `WireGuard` (`/admin/wg`, v2: `/admin2/wg`)

Правило ёмкости: не более `5` top-level разделов и не более `7` подменю в разделе без отдельного пересмотра IA.

## 3) Канон меню client

1. `Огляд`
- `Огляд системи` (`/client`, v2: `/client2`)

2. `Транспорт і статуси`
- `Мої транспорти` (`/client/vehicles`, v2: `/client2/vehicles`)
- `Тікети` (`/client/tickets`, v2: `/client2/tickets`)
- `Статуси` (`/client/status`, v2: `/client2/status`)

3. `Акаунт`
- `Профіль` (`/client/profile`, v2: `/client2/profile`)
- `Сповіщення` (`/client/notifications`, v2: `/client2/notifications`)

Правило ёмкости: не более `3` top-level разделов для MVP/RC-контура клиента.

## 4) Раскладка контента по страницам

1. `Старт/Огляд`: только сводка состояния + быстрые входы в домены.
2. `Флот/Стан флоту`: оперативный triage и SLA-фокус, без длинной истории.
3. `Флот/Алерти`: группировка и подтверждение сигналов.
4. `Флот/Інциденти`: lifecycle инцидентов и handoff.
5. `Сповіщення/Доставка`: очередь и статус доставки.
6. `Сповіщення/Правила каналів`: policy и маршрутизация каналов.
7. `Контроль і KPI/Політика`: правила и overrides без журнала событий.
8. `Контроль і KPI/Історія KPI` и `Аудит`: только история/трассировка.
9. `Client/Огляд` и `Client/Мої транспорти`: SLA/ETA summary в primary, полный список во secondary.
10. `Client/Профіль` и `Client/Сповіщення`: паттерн `summary -> form -> support details`.

## 5) Визуальная минимизация (без перегруза)

1. Один экран = один основной вопрос пользователя.
2. Не более `4` KPI-карточек в первом ряду.
3. Не более `1` крупной таблицы в primary-контуре.
4. Дополнительные фильтры прячутся в toolbar `<details>`.
5. Для table-heavy экранов включается progressive columns toggle (`базово/детально`).

## 6) Step-17 status (done) и фокус step-18

Step-17 выполнен:

1. IA freeze зафиксирован в `Core + Domains`.
2. Добавлен единый RC/handoff script:
- `scripts/client_panel_step17_handoff_check.sh`.
3. Checklist run выполнен:
- `Docs/auto/web-panel/client-step17-handoff-checklist.md` (`PASS`).

Фокус step-18:

1. Инкрементальный content-split перегруженных экранов строго по канону меню.
2. Visual-density аудит (`sidebar/page/table`) без изменения API-контрактов.
3. Повторный прогон `step-17 checklist` после каждого UI-пакета.

## 7) Референсы 2025-2026

- Atlassian navigation system: https://atlassian.design/components/navigation-system/
- Fluent 2 nav/drawer: https://fluent2.microsoft.design/components/web/react/core/nav/usage
- Shopify Polaris IA: https://shopify.dev/docs/apps/build/design-considerations/information-architecture
