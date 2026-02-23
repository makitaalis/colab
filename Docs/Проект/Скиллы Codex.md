# Codex skills для проекта

Эти skills нужны, чтобы быстро и воспроизводимо:

- фиксировать “канон” по дверям/IP
- генерировать авто‑отчёты в `Docs/auto/`
- обновлять документацию по категориям (модули/операции/проблемы)
- поднимать/восстанавливать backend сервер и VPN WireGuard
- масштабировать rollout до 100–200 систем через реестр и шаблоны

## Установленные skills (в `$CODEX_HOME/skills`)

- `orangepi-passengers-baseline` — baseline + авто‑документация (PC + OPi).
- `orangepi-passengers-setup` — прошивка/первичная настройка OPi + порядок шагов.
- `orangepi-passengers-server` — bootstrap и операции по серверу (Ubuntu + Compose).
- `orangepi-passengers-docs` — поддержание документации и авто‑отчётов.

## Skills в репозитории для модульной админки

- `skills/orangepi-passengers-admin-modules/` — правила разбиения админки на модули, порядок реализации UI/API, чек deploy/валидации.
- `skills/orangepi-passengers-admin-alerts/` — отдельный workflow для operational alerts (группировка, массовые действия, мониторинг).
- `skills/orangepi-passengers-admin-refactor/` — этапный вынос кода из `backend/app/main.py` в модульные файлы с безопасным rollout/rollback.
- `skills/orangepi-passengers-admin-fleet-overview/` — развитие и рефакторинг модуля `/admin/fleet` (UX, фильтры, ops-feed, smoke-проверки).
- `skills/orangepi-passengers-admin-fleet-monitor/` — изменения и рефакторинг monitor snapshot/health/auto-notify (`/api/admin/fleet/monitor`, `/health`, `/health/notify-auto`).
- `skills/orangepi-passengers-admin-module-governance/` — правила этапного разделения админки по модулям, deploy/smoke gate и синхронизация docs/prompts/skills.
- `skills/orangepi-passengers-admin-module-factory/` — шаблон создания нового модуля админки (границы, файлы `page/ops`, thin-wrapper policy, rollout gates).
- `skills/orangepi-passengers-admin-delivery/` — end-to-end шаблон phase delivery (код → деплой VPS → unified smoke-gate → синхронизация docs/prompts/skills).
- `skills/orangepi-passengers-admin-ui-toolkit/` — перенос страниц на единый UI toolkit (`admin_ui_kit.py`), минимизация дублирования CSS/layout и сохранение API-контрактов.
- `skills/orangepi-passengers-admin-golden-shell/` — golden UI/UX shell для модулей админки: обязательные blocks (flow, density, tableMeta, action rhythm) без изменения backend API.
- `skills/orangepi-passengers-webpanel-uiux/` — единые UI/UX стандарты и IA меню для web-панели (admin+client): Core+Domains, визуальная чистота, server-first deploy и обновление docs.
- `skills/orangepi-passengers-doc-architecture/` — архитектура и governance документации (слои L0–L4, правила модульного деления, DoD обновлений, link hygiene).

Пакеты промптов:

- `Docs/Проект/Промпты Codex (админка).md` — этапные промпты для модульной разработки admin UI/API.
- `Docs/Проект/Промпты Codex (документация).md` — промпты для архитектуры docs, синхронизации канона и масштабирования.
  - phase-15: внутри toolkit также хранится общий JS helper (`window.AdminUiKit`) для debounce/Enter/clearFilters/status/api/whoami.
  - phase-16: heavy-страницы (`fleet/alerts/incidents/incident-detail`) подключают `base_admin_js()` и используют общие JS primitives.
  - phase-17: heavy-страницы переведены на `render_admin_shell` через `render_legacy_admin_page(...)` (без риска регрессий DOM/JS).
  - phase-18A: `render_legacy_admin_page(...)` автоматически извлекает `header/chips/toolbar/body` и рендерит через стандартный shell layout.
  - phase-18B(step): page-by-page переход heavy-страниц на чистый `render_admin_shell(...)` без `legacy_html`.
    - step-1 выполнен: `admin_fleet_incident_detail_page.py`
    - step-2 выполнен: `admin_fleet_incidents_page.py`
    - step-3 выполнен: `admin_fleet_alerts_page.py`
    - step-4 выполнен: `admin_fleet_page.py`
  - итог: phase-18B закрыт, heavy-страницы полностью на `render_admin_shell`.
  - phase-19: post-migration cleanup/hardening:
    - общий utility CSS поднят в `admin_ui_kit.py`;
    - `extra_css` heavy-страниц очищен от дублей base-темы;
    - в `scripts/admin_panel_smoke_gate.sh` добавлен `LEGACY_RENDER_CHECK` (`--strict-modules`).
  - phase-20: UI/UX polish (UA) поверх модульной базы:
    - улучшены focus/hover/contrast state в base toolkit;
    - повышена читаемость таблиц/фильтров и action controls на heavy-страницах;
    - smoke-gate + VPS checks без регрессий API.
  - phase-21: operator workflow/navigation:
    - добавлены явные flow-маршруты на `fleet/alerts/incidents`;
    - action controls сгруппированы через `opAction*` и быстрые переходы к `actions/audit`;
    - smoke-gate + flow-checks без регрессий.
  - phase-22: operator UX rhythm/density:
    - добавлены общие toolkit primitives `tableMeta/metaChip` и единый JS API плотности (`initDensityMode/applyDensityMode`);
    - `fleet/alerts/incidents` синхронизированы по source/sort/mode hints и regular/compact поведению;
    - smoke-gate + density/meta checks без регрессий API.
  - phase-23: golden shell + left sidebar:
    - `render_admin_shell(...)` получил единый sidebar-каркас (`appShell/sideNav/sideLink`);
    - модульные страницы используют `current_nav` для активного пункта меню;
    - smoke-gate + sidebar marker checks без регрессий API.
  - phase-24: operator workspace refinement:
    - в `AdminUiKit` добавлены sticky-context helpers (`save/load/clear/applyWorkspaceHint`);
    - добавлены latency helpers (`runActionWithLatency`, `formatLatency`) для действий `ack/silence/unsilence`;
    - `fleet/alerts/incidents/incident-detail` используют общий workspace-context и action-latency hints;
    - smoke-gate + workspace marker checks без регрессий API.
  - phase-25: command palette + presets:
    - `AdminUiKit` расширен command-palette helpers (`open/close/bindCommandPalette`);
    - добавлены preset helpers (`list/save/get/delete`) с хранением в localStorage;
    - `fleet/alerts/incidents` получили `Команди` + presets UI и hotkey `Ctrl/Cmd+K`;
    - smoke-gate + command/preset marker checks без регрессий API.
  - phase-26: cross-page preset portability:
    - preset helpers расширены namespace-режимом (`local/shared`);
    - добавлены JSON helpers (`export/importPresets`, `export/importPresetBundle`);
    - в `fleet/alerts/incidents` добавлены namespace switch + `Експорт/Імпорт`;
    - shared bundle поддерживает операторский набор scope: `fleet`, `fleet_alerts`, `fleet_incidents`.
  - phase-27: presets governance:
    - добавлены profile templates (`presetProfileTemplates`) и массовая установка (`installPresetProfiles`);
    - добавлен cleanup/retention (`cleanupPresets`) с архивом удалённых пресетов (`listPresetArchive`);
    - `fleet/alerts/incidents` получили `Профілі/Cleanup` и команды palette для governance.
  - phase-28: presets observability dashboard:
    - добавлены агрегированные helpers (`buildPresetScopeObservability`, `buildPresetObservabilityBundle`);
    - `fleet/alerts/incidents` получили hint `presetObservability` + кнопку `Метрики`;
    - в summary отображаются `local/shared/total/archived` и `last cleanup` по scope без изменения API.
  - phase-29: preset audit timeline:
    - добавлены timeline helpers (`listPresetTimeline`, `clearPresetTimeline`, `buildPresetTimelineSummary`, `buildPresetTimelineBundle`);
    - операции `save/delete/import/export/install/cleanup` автоматически пишут audit trail в localStorage;
    - `fleet/alerts/incidents` получили `presetTimelineHint`, кнопки `Журнал/Очистити журнал` и palette drill-down.
  - phase-30: preset conflict guard + merge simulator:
    - добавлены preview helpers (`simulatePresetImport`, `simulatePresetBundleImport`, `buildPresetMergePreview`);
    - сравнение выполняется по `name + ts + payload hash` и показывает `create/update/skip/conflicts/drop`;
    - `fleet/alerts/incidents` получили `presetMergeHint`, кнопку `Preview` и palette-команды `Preview merge / Імпорт merge / Імпорт replace`.
  - phase-31: protected baseline profiles (policy lock):
    - добавлены policy helpers (`getPresetProtectionState`, `setPresetProtectionLock`);
    - protected presets блокируются от delete/overwrite/import-conflict при lock=ON;
    - `fleet/alerts/incidents` получили `presetPolicyHint`, `Unlock/Lock` и explicit unlock confirm (`UNLOCK`).
  - phase-32: presets operations cockpit (scope batch):
    - добавлены batch helpers (`buildPresetOperationsSummary`, `simulatePresetOperations`, `applyPresetOperations`, `setPresetProtectionLockBatch`);
    - `fleet/alerts/incidents` получили `presetCockpitHint` + `Cockpit` control и palette-команды batch-операций;
    - массовые preview/apply/policy операции по scope выполняются UI-only, без изменения backend API/schema.
  - phase-33: cockpit timeline panel (batch audit):
    - добавлен helper `buildPresetCockpitTimeline` + UI panel helpers `openPresetCockpitTimelinePanel/closePresetCockpitTimelinePanel`;
    - `fleet/alerts/incidents` получили `presetCockpitTimelineHint` + `presetCockpitTimeline` control;
    - добавлены palette-команды `Cockpit timeline panel` и drill-down JSON по batch-событиям.
  - phase-34: cockpit rollout assistant (safe apply protocol):
    - добавлены helpers `buildPresetRolloutAssistant`, `applyPresetRolloutAssistant`, `getPresetRolloutLast`;
    - `fleet/alerts/incidents` получили `presetRolloutHint` + `presetRollout` control;
    - добавлены palette-команды `Rollout assistant merge/replace` и `Rollout last summary`.
  - phase-35: left navigation IA hardening:
    - side-nav переведён на группировку `Operations/Monitoring/Governance` с workflow jump-links;
    - добавлены visual trail/active states для operator route;
    - в flow cards добавлены compact jump-links между `fleet/alerts/incidents/audit`.
  - phase-36: navigation personalization:
    - в left shell добавлены `Quick Intents`, `Favorites`, `Recent`;
    - реализованы sidebar helpers localStorage (`favorites/recent`) и pin-toggle `☆/★`;
    - quick-intent deep-link `alerts?sev=bad` синхронизирован с фильтрами страницы.
  - phase-37: left-nav ergonomics hardening:
    - группы `Operations/Monitoring/Governance` сделаны сворачиваемыми (persisted state в localStorage);
    - добавлен reorder favorites (`↑/↓/remove`) прямо в sidebar;
    - добавлены hotkeys для intent-navigation (`Shift+Alt+A/I/U`).
  - phase-38: left-nav command hub:
    - добавлен inline `Command Hub` (intent-runner) в sidebar;
    - добавлен visual hotkeys cheat-sheet для discoverability;
    - добавлен focus mode (`Стандарт/Фокус`) с persisted state в localStorage.
  - phase-39: sidebar intelligence:
    - quick-intents и command-hub получили adaptive priority на базе context/recent/favorites/session usage;
    - добавлены context-aware hints в sidebar по текущему route/query;
    - добавлен блок session shortcuts (быстрый повтор последних операторских переходов).
  - phase-40: sidebar mission-control:
    - добавлены alert-first widgets (`bad/open/sla/queue`) в sidebar;
    - добавлены one-click triage presets для типовых аварийных сценариев;
    - добавлен sticky incident focus (detail/list/pin/clear) на базе workspace context.
  - phase-41: mission-control automation:
    - добавлены guided recovery playbooks (пошаговые runbooks в sidebar);
    - добавлен smart triage chaining (рекомендованный `next step` после preset);
    - добавлены operator handoff notes (save/context/clear) для передачи смены.
  - phase-42: mission-control evidence loop:
    - добавлены checklist completion badges для runbook шагов;
    - добавлен quick snapshot журнал (`capture/show/clear`) для postmortem;
    - добавлен handoff timeline/history с фиксацией `save/context/clear/snapshot`.
  - phase-43: mission-control response packs:
    - добавлен response-pack export (`generate/copy-template/export-json/clear`);
    - добавлен handoff template generator (оперативный summary);
    - добавлен быстрый review/copy flow для передачи смены.
  - phase-44: mission-control escalation routing:
    - добавлены rule-based routing profiles для response pack по `severity/status/code/path`;
    - добавлены channel-ready templates (`short/full/audit`) и выбор профиля/шаблона в sidebar;
    - добавлен dispatch review/copy flow (`apply-routing`, `auto-route`, `copy-route`) без изменения backend API/schema.
  - phase-45: mission-control delivery adapters:
    - добавлены channel adapters presets (`telegram/email/ticket`) поверх routing профилей;
    - добавлены delivery selector controls + preview summary (`adapter/variant/transport/subject`);
    - добавлен быстрый copy flow (`copy-delivery`, `copy-telegram`, `copy-email`, `copy-ticket`) без изменения backend API/schema.
  - phase-46: mission-control delivery state handoff:
    - добавлен delivery journal (`apply/copy`, adapter/variant/ts/context/route) для воспроизводимой передачи смены;
    - добавлен queue-ready handoff status summary в mission-control response-pack блок;
    - добавлены быстрые действия `show-delivery-journal` и `clear-delivery-journal` без изменения backend API/schema.
  - phase-47: mission-control delivery acknowledgment loop:
    - добавлены lifecycle actions `ack/retry/escalate` для управляемого post-delivery цикла;
    - добавлен SLA-state summary (`fresh/warn/stale` + timer/reason) в mission-control response-pack;
    - delivery journal и handoff timeline расширены событиями lifecycle для прозрачной передачи смены без изменения backend API/schema.
  - phase-48: mission-control delivery state automation:
    - добавлен suggestion engine (`ack/retry/escalate`) на базе SLA-state + delivery journal history;
    - добавлены bulk shortcuts (`bulk-ack-pending`, `bulk-retry-stale`, `bulk-escalate-stale`) для ускоренного triage;
    - добавлен explainability summary (`action/confidence/reason`) и кнопка применения рекомендации без изменения backend API/schema.
  - phase-49: mission-control delivery policy profiles + UI cleanup:
    - добавлены policy profiles (`balanced/aggressive/conservative`) и session override selector;
    - policy-aware automation обновлена (стратегии `warn/stale`, explainability по активному профилю);
    - улучшена визуальная чистота и удобство delivery-блока (секции, компактные button-группы, primary/disabled states) без изменения backend API/schema.
  - phase-50: mission-control UX refinement:
    - добавлены keyboard-first shortcuts для ключевых delivery операций (`apply/ack/retry/escalate/bulk/policy/journal`);
    - добавлены confirm/microcopy guardrails для рискованных действий (`retry/escalate/bulk`);
    - добавлен mobile sticky action footer для стабильно доступного recommended action без изменения backend API/schema.
  - phase-51: mission-control navigation ergonomics:
    - добавлены controls левой навигации (`search`, `compact`, `filter status`) и фильтрация групп/ссылок;
    - добавлен persist-компактный режим sidebar (`localStorage`) с mobile-friendly fallback;
    - улучшена скорость перехода между разделами без изменения backend API/schema.
  - phase-52: mission-control navigation accessibility polish:
    - добавлены ARIA-улучшения для nav-controls (`aria-live`, `aria-controls`, `aria-label`) и keyboard-flow (`Shift+Alt+N`, `Enter/ArrowDown/Escape`, `ArrowLeft/ArrowRight/Home/End`);
    - добавлен onboarding-блок навигации с сохранением состояния скрытия в `localStorage`;
    - улучшена доступность и onboarding без изменения backend API/schema.
  - phase-53: mission-control operator adoption telemetry:
    - добавлена локальная telemetry-модель nav-flow (`search/hotkeys/filter/group/compact/onboarding`) с хранением в `localStorage`;
    - добавлен adoption snapshot в handoff-блок (`actions/unique/top/last + compact/tips state`);
    - получен базовый observability-контур по освоению UI без изменения backend API/schema.
  - phase-54: mission-control operator coaching loop:
    - добавлены coaching helpers на базе telemetry (`adoptionEventCount`, `buildSidebarNavAdoptionCoaching`, `buildSidebarNavAdoptionSnapshot`);
    - добавлены handoff actions `show/export/reset adoption snapshot` и coaching summary в sidebar;
    - сохранён UI-only подход без изменения backend API/schema.
  - phase-55: mission-control coaching cadence scoreboard:
    - добавлены scorecard helpers (`buildSidebarNavAdoptionScorecard`, `buildSidebarNavNextActions`);
    - добавлены handoff-блоки `sideHandoffScorecard` и `sideHandoffNextActions`;
    - snapshot расширен полями `scorecard/next_actions` без изменения backend API/schema.
  - phase-56: mission-control coaching trendline history:
    - добавлены history/trend helpers и storage `MISSION_ADOPTION_HISTORY_STORAGE_KEY`;
    - добавлен handoff trend-блок `sideHandoffTrend` с `IMPROVING/STABLE/REGRESSING` и `delta`;
    - сохранение handoff-note теперь формирует history записи по scorecard.
  - phase-57: mission-control coaching reset-pack:
    - добавлены trend actions (`show/export/clear`) через `runMissionHandoffTrendAction`;
    - добавлены history lifecycle helpers и статус `sideHandoffTrendStatus`;
    - добавлены confirm-guardrails для безопасного clear trend history.
  - phase-58: mission-control coaching trend presets:
    - добавлены trend window presets (`last 3/5/10`) + persist selection в session storage;
    - добавлен compare summary `now vs baseline` в handoff блок без JSON-переходов.
  - phase-59: mission-control coaching decision cues:
    - добавлен helper `buildMissionAdoptionTrendCoach` с actionable подсказками по тренду;
    - добавлен handoff-блок `sideHandoffTrendCoach` и поле `trend_coach` в trend payload/snapshot.
  - phase-60: mission-control coaching handoff composer:
    - добавлены composer actions (`compose/copy/apply`) и summary-блок `sideHandoffComposer` в handoff;
    - добавлен генератор стандартизированного handoff шаблона из `scorecard + trend + trend_coach + next_actions`.
  - phase-61: mission-control handoff quality guard:
    - добавлены quality helpers + статус `ready/not-ready` в handoff блоке;
    - добавлен guardrail перед save (`blocked/override`) и timeline события качества.
  - phase-62 (следующий):
    - handoff quality profiles (`strict/balanced`) + policy-state в handoff summary;
    - цель: адаптировать строгость quality-гейта под реальные режимы эксплуатации.

Рекомендация:

- держать эти skills в Git как “канон команды”;
- при необходимости установить в `$CODEX_HOME/skills`, чтобы они автоматически триггерились в рабочих сессиях.
- для каждого этапа в итоге всегда писать:
  - что сделано и зачем;
  - что будет сделано следующим этапом и зачем.

Рекомендованная связка для модульной разработки админки:

- `orangepi-passengers-admin-module-governance` → фикс границ этапа/модуля;
- `orangepi-passengers-admin-ui-toolkit` → унификация UI shell + JS helpers;
- `orangepi-passengers-admin-golden-shell` → единый “золотой” UI/UX каркас модулей (IA + density + table contracts);
- `orangepi-passengers-admin-delivery` → деплой + smoke + синхронизация docs/prompts/skills.

Рекомендованная связка для развития документации:

- `orangepi-passengers-docs` → фикс фактического состояния (baseline/inventory) и категорий docs;
- `orangepi-passengers-doc-architecture` → управление структурой docs, split/merge модулей, правила синхронизации;
- `orangepi-passengers-admin-module-governance` → единый стандарт этапов для админ-панели и связанной документации.

Для server-операций (текущий baseline):

- использовать `orangepi-passengers-server` + единый аудит `scripts/server_security_posture_check.sh`;
- после каждого hardening/deploy прогоны: posture-check + `scripts/admin_panel_smoke_gate.sh`;
- включить периодический контроль: `scripts/install_server_security_posture_timer.sh`.

## Как запускать (в диалоге)

1) Явно назвать skill в сообщении: например `orangepi-passengers-docs` или `$orangepi-passengers-docs`.
2) Дальше — описать задачу (“обнови документацию”, “сгенерируй baseline”, “подними backend”, “добавь новый Central в WG”).

## Репозиторий

Исходники skills лежат в `skills/` (для переноса/версирования).

## Масштабирование (reproducible rollout)

Инструменты:

- реестр: `fleet/registry.csv`
- валидация/шаблоны: `scripts/fleet_registry.py`
- apply WG peer: `scripts/fleet_apply_wg_peer.py`
- apply central env: `scripts/fleet_apply_central_env.py`
- оркестратор: `scripts/fleet_rollout.sh`
- commissioning отчёт: `scripts/fleet_commission.py`
- план: `Docs/настройка ПО/План/11. Масштабирование 100-200 систем (реестр и шаблоны).md`
- этап связи и внедрения модулей: `Docs/настройка ПО/План/12. Связь Edge-Central-Server (этап внедрения модулей).md`
- стандарт модулей: `Docs/Проект/Стандарт интеграции модулей v1.md`

Обязательное правило масштаба:

- один транспорт = один `system_id` + один WG peer + один `central_id`;
- `central_id` должен совпадать с `system_id` (пример: `sys-0002`) для корректных `overrides/alerts/incidents`.

### Актуализация roadmap skills: phase-62

- phase-62: mission-control handoff quality profiles:
  - добавлены policy profiles (`strict/balanced`) с session persistence;
  - добавлен явный policy-state в handoff quality summary;
  - quality timeline/events расширены policy-контекстом.
- phase-63 (следующий):
  - handoff remediation assistant (one-click исправления по missing quality-check пунктам);
  - explainability-подсказки для снижения forced-override.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.

### Актуализация roadmap skills: phase-63

- phase-63: mission-control handoff remediation assistant:
  - добавлены one-click remediation actions для quality missing-пунктов;
  - добавлен explainability-блок причин блокировки save;
  - quality save-flow и timeline синхронизированы с `fix`-контекстом.
- phase-64 (следующий):
  - remediation telemetry summary (`applied/skipped/override-after-remediation/time-to-ready`);
  - KPI-слой в handoff для контроля эффекта quality-гейта.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.

### Актуализация roadmap skills: phase-64

- phase-64: mission-control handoff remediation telemetry:
  - добавлены remediation KPI метрики (`applied/skipped/override-after-remediation/time-to-ready`);
  - добавлен compact KPI summary в handoff UI;
  - lifecycle quality/remediation/save синхронизирован с telemetry обновлением.
- phase-65 (следующий):
  - remediation timeline drilldown по последним циклам;
  - экспорт KPI + разбор override-driven деградаций.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.

### Актуализация roadmap skills: phase-65

- phase-65: mission-control handoff remediation timeline drilldown:
  - добавлен last-N remediation timeline + preview в handoff;
  - добавлены show/export/clear actions для remediation JSON;
  - remediation lifecycle интегрирован с timeline событиями (`remediate/override-save/ready-save`).
- phase-66 (следующий):
  - remediation governance targets + compliance-state;
  - guided next-actions для управления отклонениями KPI.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.

### Актуализация roadmap skills: phase-71

- phase-71: mission-control remediation planner decision ledger:
  - planner decision ledger added (`show/export/clear`) with append on decision events;
  - decision coverage summary added (`planned vs logged`) for shift execution control;
  - decision operations traced in timeline (`remediation_decision_ledger_*`, `remediation_digest_plan_log_primary`).
- phase-72 (следующий):
  - decision backlog cockpit for coverage-gap (`missing decisions`);
  - handoff-ready summary for unresolved planner decisions.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.


### Актуализация roadmap skills: phase-72

- phase-72: mission-control remediation decision backlog cockpit:
  - added coverage-gap backlog panel (`missing decisions`) in mission-control;
  - added backlog actions (`backlog-show/export/copy`) and handoff-ready summary;
  - added timeline traces for backlog ops (`remediation_decision_backlog_*`).
- phase-73 (следующий):
  - remediation decision backlog closeout assistant (`ack/snooze/profile-check` from backlog);
  - batch closeout flow for top-missing decisions in shift handoff.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.


### Актуализация roadmap skills: phase-73

- phase-73: mission-control remediation decision backlog closeout assistant:
  - added direct backlog closeout actions (`backlog-item ack/snooze/profile-check`);
  - added batch closeout for top-missing decisions (`backlog-batch-*`);
  - added closeout timeline traces (`remediation_decision_backlog_closeout_item/batch`).
- phase-74 (следующий):
  - closeout governance board with KPI by decision-type and mode (`single/batch`);
  - shift-ready closeout JSON/export with remaining decision-gap.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.


### Актуализация roadmap skills: phase-74

- phase-74: mission-control remediation decision closeout governance board:
  - добавлена closeout governance сводка (`single/batch`, `ack/snooze/profile-check`, `remaining_gap`);
  - добавлены операции `closeout-governance-show/export` для shift-ready JSON;
  - добавлены timeline traces `remediation_decision_closeout_governance_show/export`.
- phase-75 (следующий):
  - closeout escalation routing по governance status и remaining gap;
  - escalation payload actions (`show/export/copy`) для handoff смены.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.


### Актуализация roadmap skills: phase-75

- phase-75: mission-control remediation closeout escalation routing:
  - добавлен escalation policy-layer по `status/remaining_gap` для closeout governance;
  - добавлены escalation actions `show/export/copy` + payload для handoff;
  - добавлены timeline traces `remediation_decision_closeout_escalation_show/export/copy`.
- phase-76 (следующий):
  - escalation execution logbook (`ack/snooze/resolve`) + SLA-age;
  - execution payload export для сменного handoff-контроля.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.


### Актуализация roadmap skills: phase-76

- phase-76: mission-control closeout escalation execution logbook:
  - добавлен execution journal с lifecycle actions (`ack/snooze/resolve`);
  - добавлен SLA-age контур (`IDLE/OK/WARN/STALE`) для escalation execution;
  - добавлены operations `Exec JSON/export/copy` и timeline traces execution lifecycle.
- phase-77 (следующий):
  - anomaly guard для execution logbook (repeat snooze, stale drift, unresolved routes);
  - recommended actions и anomaly report для сменного контроля.

Обязательное правило handoff отчёта по этапу (фикс):

- всегда писать, что сделано в текущем этапе и зачем;
- всегда писать, что будет сделано следующим этапом и зачем это нужно проекту.

## Обязательный protocol по завершению этапа

Для всех этапов разработки/настройки действует единый обязательный протокол:

1. Сначала фиксируется факт изменений в коде/конфиге.
2. Затем в той же итерации обновляются профильные документы (`Модули`, `Операции`, `Проблемы`, `INDEX` при необходимости).
3. Если менялся workflow, синхронизируются соответствующие `SKILL.md` и prompt-pack.
4. В конце этапа всегда указываются:
- следующий этап;
- зачем он нужен (ожидаемый технический эффект).

Нарушение этого протокола = этап не закрыт.

## Новый skill (камера)

- `skills/orangepi-passengers-camera-calibration/` — workflow калибровки OAK-D Lite depth-counting (`person+track_id+2 линии`, `wide-scan -> transport-strict -> manual tune -> health/logs`) с обязательной синхронизацией runbook после изменения параметров.
