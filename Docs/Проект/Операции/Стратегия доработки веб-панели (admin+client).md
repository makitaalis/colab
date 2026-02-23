# Стратегия доработки веб-панели (admin+client)

Документ задаёт практическую стратегию доработки web-панели по модели `Ядро + Домены`.

Связанные стандарты:

- `Docs/Проект/Веб-панель (ядро и домены).md`
- `Docs/Проект/Админ-панель (UI-UX стандарт).md`
- `Docs/Проект/Админ-панель (модульная разработка).md`

## 1) Продуктовые цели

1. Администратор:
- видеть риск и приоритет за 3–5 секунд;
- выполнять действия без перегрузки интерфейса.
2. Клиент:
- быстро понимать статус своего транспорта/обращений;
- получать минималистичный, понятный кабинет без операционного шума.

## 2) Архитектурная рамка

1. `Core`:
- shell, навигация, токены, общие компоненты и UX-паттерны.
2. `Domains`:
- предметные страницы и сценарии (без cross-DOM зависимостей).
3. `Server-first` rollout:
- любое изменение сначала проверяется на сервере через smoke-gate.

## 3) Этапы реализации

Этап 1. Foundation (завершён)
- внедрены `admin_core/admin_domains`;
- добавлен клиентский scaffold `client_core/client_domains`;
- IA меню/подменю переведена в доменную карту.

Этап 2. Content Split (завершён для admin-доменов)
- цель: снизить плотность страниц `fleet` и `notify-center`;
- принцип: одна страница = один основной сценарий.
- подэтапы по доменам:
  - `Старт`: только onboarding/контекст, без triage-таблиц;
  - `Флот`: оперативный triage отдельно от истории/аудита;
  - `Сповіщення`: правила каналов отдельно от delivery-операций;
  - `Контроль і KPI`: policy отдельно от audit-ленты;
  - `Інфраструктура`: только сетевая диагностика без fleet-перегруза.
- статус:
  - `Флот step-1` выполнен: secondary-блоки на `/admin/fleet` перенесены в сворачиваемую секцию.
  - `Сповіщення step-2` выполнен: delivery-журнал на `/admin/fleet/notify-center` вынесен в сворачиваемую secondary-секцию.
  - `Контроль і KPI step-3` выполнен: персональные override-и на `/admin/fleet/policy` вынесены в secondary-секцию, primary-контур policy оставлен сверху.
  - `Інфраструктура step-4` выполнен: server config на `/admin/wg` вынесен в secondary-секцию, базовая peer-диагностика оставлена в primary-контуре.
  - итог: content-split завершён для ключевых admin-доменов.

Этап 3. Client Panel MVP
- запустить отдельный клиентский shell и базовые страницы:
  - `Огляд`
  - `Мої транспорти`
  - `Тікети/Статуси`
  - `Профіль/Сповіщення`
- статус:
  - `step-1` выполнен: подняты route `/client*`, отдельный `client_ui_kit` и доменная IA клиента;
  - `step-2` выполнен: подключены `/api/client/*`, реализован минимальный auth/scope-контур клиента и UI переведён с mock на backend API.
  - `step-3` выполнен: `tickets/status` разнесены по `primary + secondary` без визуального перегруза, secondary-секции сворачиваемы и persistent.
  - `step-4` выполнен: роль `admin-support` внедрена в client whoami-контур, выполнен mobile tune таблиц.
  - `step-5` выполнен: `home/vehicles` упорядочены по SLA/ETA сценариям (`attention + full list`) и mobile readability.
  - `step-6` выполнен: `Профіль/Сповіщення` переведены в role-aware account-сценарий + добавлен e2e-runbook.
  - `step-7a` выполнен: добавлен автоматизированный regression gate (`scripts/client_panel_regression_check.sh`).
  - `step-7b` выполнен: проведён real-data UX-аудит и сформирован отчёт `Docs/auto/web-panel/client-step7b-ux-audit.md`.
  - `step-8a` выполнен: оформлен операторский playbook `Docs/Проект/Операции/Client admin-support playbook.md`.
  - `step-8b` выполнен: проведён acceptance-прогон `admin-support` с rollback, отчёт `Docs/auto/web-panel/client-step8b-support-acceptance.md`.
  - `step-9` выполнен: внедрён постоянный support-rollout (`scripts/client_support_rollout.sh`) с раздельными nginx auth-файлами.
  - `step-10` выполнен: включены `CLIENT_SCOPE_BINDINGS` для support-логина (`support:sys-0001`), отчёт `Docs/auto/web-panel/client-step10-scope-rollout.md`.
  - `step-11` выполнен: внедрён matrix-onboarding policy (`support-<system_id>`) через `scripts/client_support_matrix_rollout.sh`, отчёт `Docs/auto/web-panel/client-step11-multi-support-onboarding.md`.
  - `step-12` выполнен: внедрён lifecycle policy (`disable/rotate/revoke`) через `scripts/client_support_lifecycle_rollout.sh`, отчёт `Docs/auto/web-panel/client-step12-support-lifecycle-rollout.md`.
  - `step-13` выполнен: внедрён lifecycle automation pack (`rotation batch + inventory report + server timers`) через `scripts/client_support_rotation_batch.sh`, `scripts/client_support_inventory_report.sh`, `scripts/install_client_support_lifecycle_timer.sh`, отчёт `Docs/auto/web-panel/client-step13-lifecycle-automation-pack.md`.
  - `step-14` выполнен: UX polish client navigation (`compact sidebar + grouped submenu + progressive table columns`), отчёт `Docs/auto/web-panel/client-step14-ux-polish-rollout.md`.
  - `step-15` выполнен: accessibility + keyboard flow + copy audit client shell, отчёт `Docs/auto/web-panel/client-step15-a11y-keyboard-copy-rollout.md`.
  - `step-16` выполнен: operator accessibility-acceptance (`keyboard-only`) и фиксация client shell DoD, отчёт `Docs/auto/web-panel/client-step16-accessibility-acceptance.md`.
  - `step-17` выполнен: release-candidate stabilization и handoff checklist automation (`scripts/client_panel_step17_handoff_check.sh`), отчёты `Docs/auto/web-panel/client-step17-rc-kickoff.md` и `Docs/auto/web-panel/client-step17-handoff-checklist.md`.
  - `step-18` начат: visual polish pack-1 (admin header declutter + domainSplitDetails unification), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack1.md`.
  - `step-18` pack-2 выполнен: content-split на `/admin/fleet/incidents` (secondary details + persistence), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack2-incidents.md`.
  - `step-18` pack-3 выполнен: sidebar без перегруза (сворачиваемые mini-блоки + persistence), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack3-sidebar.md`.
  - `step-18` pack-4 выполнен: commissioning без перегруза (`/admin/commission`: toolbar split + primary/secondary + persistence), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack4-commission.md`.
  - `step-18` pack-5 выполнен: alerts без перегруза (`/admin/fleet/alerts`: groups-by-code в secondary + persistence), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack5-alerts.md`.
  - `step-18` pack-6 выполнен: notify-center без перегруза (`/admin/fleet/notify-center`: toolbar split + updatedAt chip + tableMeta), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack6-notify-center.md`.
  - `step-18` pack-7 выполнен: policy без перегруза (`/admin/fleet/policy`: авто-сповіщення в advanced details + persistence), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack7-policy.md`.
  - `step-18` pack-8 выполнен: history без перегруза (`/admin/fleet/history`: toolbar split + clear filters + tableMeta), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack8-history.md`.
  - `step-18` pack-9 выполнен: audit без перегруза (`/admin/audit`: toolbar split + header chips + tableMeta), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack9-audit.md`.
  - `step-18` pack-10 выполнен: actions без перегруза (`/admin/fleet/actions`: toolbar split + tableMeta), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack10-actions.md`.
  - `step-18` pack-11 выполнен: wg без перегруза (`/admin/wg`: tableMeta + advanced secondary), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack11-wg.md`.
  - `step-18` pack-12 выполнен: notification rules без перегруза (`/admin/fleet/notifications`: test в secondary + tableMeta), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack12-notification-rules.md`.
  - `step-18` pack-13 выполнен: central detail без перегруза (`/admin/fleet/central/{central_id}`: secondary history/actions + tableMeta), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack13-central-detail.md`.
  - `step-18` pack-14 выполнен: incident detail triage-first (`/admin/fleet/incidents/{central_id}/{code}`: message+debug в advanced details, toolbar declutter), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack14-incident-detail.md`.
  - `step-18` pack-15 выполнен: overview без перегруза (`/admin`: операционные таблицы в secondary + persistence), отчёт `Docs/auto/web-panel/admin-step18-visual-polish-pack15-overview.md`.
  - `step-18` pack-16 виконано: fleet без перегруза (`/admin/fleet`: advanced tools в окремий secondary details + persistence), звіт `Docs/auto/web-panel/admin-step18-visual-polish-pack16-fleet.md`.
  - `step-18` pack-17 виконано: incidents list без перегруза (`/admin/fleet/incidents`: advanced tools в окремий secondary details + persistence), звіт `Docs/auto/web-panel/admin-step18-visual-polish-pack17-incidents-list.md`.
  - `step-18` pack-18 виконано: sidebar IA (Simple=hub-only + пошук), звіт `Docs/auto/web-panel/admin-step18-visual-polish-pack18-sidebar-architecture.md`.
  - `step-18` pack-19 виконано: sidebar refine (Simple показує всі домени як hub links + пошук розкриває групи), звіт `Docs/auto/web-panel/admin-step18-visual-polish-pack19-sidebar-refine.md`.
  - `step-18` pack-20 виконано: core components polish (focus-visible + toolbar/details unification), звіт `Docs/auto/web-panel/admin-step18-visual-polish-pack20-core-components.md`.
  - `step-18` pack-21 виконано: client core components polish (controls/details/motion), звіт `Docs/auto/web-panel/client-step18-visual-polish-pack21-client-core-components.md`.
  - `step-18` pack-22 виконано: tables polish (readability + scroll rhythm) в admin+client, звіти `Docs/auto/web-panel/admin-step18-visual-polish-pack22-tables.md` і `Docs/auto/web-panel/client-step18-visual-polish-pack22-tables.md`.
  - `step-18` pack-23 виконано: subnav scroll + empty tables (менше висоти header, зрозумілі empty-state), звіти `Docs/auto/web-panel/admin-step18-visual-polish-pack23-subnav-empty.md` і `Docs/auto/web-panel/client-step18-visual-polish-pack23-subnav-empty.md`.
  - `step-18` pack-24 виконано: section rhythm + empty-state tones (єдина ієрархія секцій + semantic empty-state OK/neutral), звіти `Docs/auto/web-panel/admin-step18-visual-polish-pack24-sections-emptytone.md` і `Docs/auto/web-panel/client-step18-visual-polish-pack24-sections-emptytone.md`.
  - `step-18` pack-25 виконано: client sidebar search (пошук по меню + hotkeys, без прокрутки довгого sidebar), звіти `Docs/auto/web-panel/admin-step18-visual-polish-pack25-client-sidebar-search.md` і `Docs/auto/web-panel/client-step18-visual-polish-pack25-client-sidebar-search.md`.
  - `step-18` pack-26 виконано: header chips scroll (не роздуває header) + robust empty-state removal, звіти `Docs/auto/web-panel/admin-step18-visual-polish-pack26-header-chips.md` і `Docs/auto/web-panel/client-step18-visual-polish-pack26-header-chips.md`.
  - следующий подэтап: `step-18` (инкрементальный content-split по IA freeze и финальный visual-density аудит).

Этап 4. UX Polish
- унификация визуального ритма, отступов, состояний;
- улучшение мобильного восприятия;
- финальная чистка copy и CTA.

## 4) Backlog-политика

1. Любая задача метится:
- `core` или `domain`;
- `admin` или `client`;
- `ux`, `api`, `data`, `ops`.
2. Приоритеты:
- `P0`: безопасность, доступность, критичный triage;
- `P1`: информационная ясность и скорость операторских действий;
- `P2`: визуальный polish и вторичные удобства.

## 5) Контроль качества

Обязательный чек перед закрытием этапа:

1. `py_compile` по изменённым модулям.
2. Server deploy: `docker compose -f compose.yaml -f compose.server.yaml up -d --build api`.
3. `scripts/admin_panel_smoke_gate.sh` = PASS.
4. Обновлены этапные docs:
- `Админка модульные этапы`
- `Паспорт релиза документации`
- профильный стандарт (`UI-UX` / `ядро и домены`).

## 6) Критерии успеха

1. Левое меню компактно, с понятной двухуровневой иерархией.
2. Перегруженные страницы разделены по доменам и сценариям.
3. Админ и клиент получают разные по плотности, но единые по стилю интерфейсы.

## 7) Best-practice референсы (2025–2026)

- Atlassian navigation system:
  - https://atlassian.design/components/navigation-system/
- Atlassian new Jira navigation (rollout подход):
  - https://support.atlassian.com/jira-software-cloud/docs/what-is-the-new-navigation-in-jira/
- Fluent 2 navigation and drawer:
  - https://fluent2.microsoft.design/components/web/react/core/nav/usage
  - https://fluent2.microsoft.design/components/web/react/core/drawer/usage
- Shopify Polaris IA:
  - https://shopify.dev/docs/apps/build/design-considerations/information-architecture
