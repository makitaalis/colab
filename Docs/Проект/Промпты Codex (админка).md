# Промпты Codex (админка)

Набор рабочих промптов для модульной доработки админ-панели.

## Глобальное правило отчётности этапа

Для любого этапа обязательно завершать ответ блоком:

1) что сделано в текущем этапе и зачем;
2) какой следующий этап;
3) что будет сделано в следующем этапе и зачем это нужно.

## 1) Новый модуль (UI + API)

```text
Сделай новый модуль admin-panel: <module_name>.
Требования:
1) UI route: /admin/fleet/<module_slug>
2) API route: /api/admin/fleet/<module_slug>...
3) Роли: viewer/operator/admin
4) Массовые операции через API с аудитом
5) Обнови docs: Docs/Проект/INDEX.md, Docs/Проект/Операции.md, Docs/Проект/Проблемы.md (если нужно)
6) Проверь py_compile и curl smoke на VPS
```

## 2) UX-итерация существующего модуля

```text
Улучши UX модуля <module_name> без изменения бизнес-логики.
Сделай:
- компактный режим таблиц;
- быстрые фильтры и reset;
- устойчивость к ошибкам API (без белого экрана);
- mobile/tablet адаптацию.
 - UA-first тексты в UI (минимум sidebar/ключевые CTA).
После изменений: py_compile + curl проверки route/API.
```

## 3) Alerts triage и массовые действия

```text
Доработай alerts-ops:
1) группировка по code;
2) массовые действия ack/silence/unsilence по выбранным и по группе;
3) статус выполнения: успех/ошибки;
4) фильтры central_id/code/severity/include_silenced;
5) обнови документацию операций и проблем.
```

## 4) Безопасный rollout на VPS

```text
Выкати изменения админки на сервер 207.180.213.225 (путь /opt/passengers-backend).
Шаги:
1) копия файлов;
2) docker compose up -d --build api;
3) проверка API curl (monitor/alerts/новые routes);
4) проверка HTML routes через https://127.0.0.1:8443;
5) хвост логов контейнера api.
Отчитай конкретные endpoints и статусы.
```

## 5) Модульный рефакторинг монолита

```text
Сделай этапный рефакторинг admin-монолита.
Этап <N>:
- вынеси модуль <module_name> из backend/app/main.py в отдельный router;
- сохрани обратную совместимость URL;
- не меняй поведение API;
- добавь smoke-check и обнови Docs/Проект/Админ-панель (модульная разработка).md.
```

## 6) Gate перед деплоем (без регрессий)

```text
Проверь готовность админки к деплою по модульному gate:
1) py_compile для backend/app/main.py и всех новых module files;
2) локальный compileall;
3) деплой в /opt/passengers-backend и docker compose up -d --build api;
4) curl smoke по UI/API матрице;
5) docker logs api без ResponseValidationError/Traceback.
Выведи таблицу endpoint => status и список найденных ошибок.
```

## 7) Создание нового модуля через шаблон

```text
Собери новый модуль админки по шаблону:
module: <name>
UI: <route>
API: <routes>
Сделай:
1) отдельный файл страницы/ops;
2) thin-wrapper в main.py;
3) role guard viewer/operator/admin;
4) обновление docs + prompts + skills;
5) smoke на VPS.
```

## 8) Карта модулей и очередь этапов

```text
Обнови roadmap модульной админки:
- какие UI/API уже вынесены;
- что осталось в main.py;
- порядок следующих 3 этапов;
- риски каждого этапа и критерий готовности.
Обнови Docs/Проект/Админ-панель (модульная разработка).md и дай короткий план выполнения.
```

## 9) Этапный вынос incidents UI

```text
Сделай phase extraction для incidents UI:
1) вынеси /admin/fleet/incidents в отдельный module file;
2) вынеси /admin/fleet/incidents/{central_id}/{code} в отдельный module file;
3) в main.py оставь thin-routes;
4) не меняй URL и параметры;
5) прогоняй py_compile + smoke на VPS и обнови docs.
```

## 10) Этапный вынос actions/audit UI

```text
Сделай phase extraction для actions/audit UI:
1) вынеси /admin/fleet/actions в отдельный module file;
2) вынеси /admin/audit в отдельный module file;
3) оставь thin-routes в main.py;
4) не меняй API/route контракты;
5) зафиксируй smoke по UI_ACTIONS/UI_AUDIT/API_ALERT_ACTIONS/API_AUDIT.
```

## 11) Прогон unified smoke-gate

```text
Прогони unified smoke-gate админки через scripts/admin_panel_smoke_gate.sh.
Требования:
1) проверить все базовые /admin и /api/admin endpoints;
2) убедиться, что все статусы 200;
3) проверить логи контейнера api на ResponseValidationError/Traceback/coroutine object;
4) дать короткий отчёт endpoint => status и итог PASS/FAIL.
```

## 11.1) Commissioning UX на `/admin` (швидкі посилання)

```text
Доработай commissioning-блок на /admin (без изменения API).
Цель: ускорить первичное подключение нового транспорта (sys-XXXX) даже до появления heartbeat.
Сделай:
1) поддержка query string central_id (shareable URL);
2) быстрые ссылки на: /admin/fleet/central/{central_id}, /incidents, /policy, /notify-center;
3) кнопка “копировать набор ссылок”;
4) подсказки/валидация формата sys-XXXX (предупреждение, но не блокировать);
5) подсказки WG peers (по /api/admin/wg/peers) как кликабельные chips для подстановки central_id.
После изменений: compileall + scripts/admin_panel_smoke_gate.sh + обнови docs (Админ-панель + Паспорт релиза).
```

## 12) Этапный вынос incidents/actions/audit API

```text
Сделай phase extraction API-логики:
1) вынеси /api/admin/fleet/incidents* и /api/admin/fleet/alerts/actions в отдельный ops module;
2) вынеси /api/admin/audit в отдельный ops module;
3) оставь в main.py только thin-handlers;
4) не меняй response schema и URL;
5) проверь локально compile + VPS smoke + unified smoke-gate.
```

## 13) Этапный вынос notification/policy API

```text
Сделай phase extraction API-логики:
1) вынеси /api/admin/fleet/notification-settings, /test, /retry в отдельный notification ops module;
2) вынеси /api/admin/fleet/monitor-policy и /monitor-policy/overrides* в отдельный monitor-policy ops module;
3) оставь в main.py thin-handlers + audit hooks;
4) не меняй response schema и URL;
5) проверь GET + safe POST (dry-run) на VPS и зафиксируй в docs.
```

## 14) Закрыть `main.py` как composition-only (runtime/config extraction)

```text
Сделай phase extraction runtime/config:
1) вынеси runtime helpers notification/policy в отдельный module file (например admin_runtime_config.py);
2) в main.py оставь только thin-wrapper для runtime helpers;
3) не меняй публичные API/route контракты;
4) прогони py_compile + compileall;
5) выкатка на VPS: main.py + новые modules;
6) прогони scripts/admin_panel_smoke_gate.sh и отдельные проверки:
   - /api/admin/fleet/monitor-policy
   - /api/admin/fleet/monitor-policy/overrides
   - /api/admin/fleet/notification-settings
   - /api/admin/fleet/notification-settings/test (dry_run)
   - /api/admin/fleet/notifications/retry (dry_run)
7) обнови docs (Админ-панель, Операции, Скиллы при необходимости).
```

## 15) UI/UX итерация (UA-first + фильтры без перегруза API)

```text
Сделай phase UI/UX для админки без изменения API-контрактов:
1) украинизируй copy на target pages (заголовки, кнопки, filter labels);
2) унифицируй кнопки действий (Підтвердити / Пауза 1 год / Зняти заглушення);
3) добавь clear-filters в страницы с множеством фильтров;
3.1) добавь в header:
  - кнопку `Скопіювати посилання` (копирует текущий URL с query-фильтрами);
  - `фільтри: ...` summary, чтобы видеть активные фильтры без раскрытия блока `Фільтри`;
4) для text filters внедри debounce (~250-300ms) + Enter для немедленного refresh;
5) не менять URL, payload и response schema;
6) локально py_compile + compileall;
7) выкатить на VPS и прогнать scripts/admin_panel_smoke_gate.sh;
8) отдельно проверить HTML через curl -k -u ... и grep по новым UI-меткам;
9) обновить docs: Админ-панель (модульная разработка) и Операции.
```

## 16) Вынести страницу на `admin_ui_kit`

```text
Сделай phase migration страницы admin UI на общий toolkit:
1) вынеси общий layout/CSS в backend/app/admin_ui_kit.py (если ещё не вынесено);
2) переведи страницу(ы) <list> на render_admin_shell(...);
3) не менять JS API вызовы, URL и response schema;
4) для filter-heavy страниц добавить:
   - кнопку "Скинути фільтри"
   - debounce 250-300ms для text input
   - Enter => immediate refresh
5) локально py_compile + compileall;
6) выкатить на VPS и прогнать scripts/admin_panel_smoke_gate.sh;
7) сделать curl/grep проверку новых UI маркеров;
8) обновить docs: Админ-панель (модульная разработка), Операции.
```

## 17) Toolkit migration пакетом (phase-14B)

```text
Сделай batch migration страниц на admin_ui_kit:
target:
- /admin/fleet/policy
- /admin/fleet/notifications
- /admin/fleet/notify-center

Требования:
1) заменить дублируемый layout/CSS на render_admin_shell(...);
2) не менять JS fetch-endpoints и payload/response контракты;
3) для notify-center внедрить clear-filters + debounce 250-300ms + Enter refresh;
4) локально py_compile + compileall;
5) деплой на VPS и scripts/admin_panel_smoke_gate.sh;
6) отдельный curl/grep check для UI заголовков и clear-filters;
7) обновить docs (Админ-панель, Операции).
```

## 18) Вынести общий JS helper в `admin_ui_kit` (phase-15)

```text
Сделай phase-15 для модульной админки:
1) добавь в backend/app/admin_ui_kit.py общий JS helper (window.AdminUiKit) с методами:
   - setStatus/setText/esc
   - apiGet/apiPost/apiDelete/fetchJson
   - debounce + bindDebouncedInputs
   - bindEnterRefresh
   - bindClearFilters
   - windowToSeconds
   - loadWhoami
2) переведи страницы:
   - /admin/audit
   - /admin/fleet/actions
   - /admin/fleet/history
   - /admin/fleet/policy
   - /admin/fleet/notifications
   - /admin/fleet/notify-center
   на общий helper без изменения API-контрактов/URL;
3) локально py_compile + compileall;
4) выкатить на VPS и прогнать scripts/admin_panel_smoke_gate.sh;
5) отдельно проверить, что в HTML всех 6 страниц присутствует window.AdminUiKit;
6) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы (если skill обновлён).
```

## 19) Module Factory: новый модуль админки по шаблону

```text
Собери новый модуль админки по module-factory шаблону.
Параметры:
- module_name: <name>
- ui_route: /admin/fleet/<slug>
- api_routes: /api/admin/fleet/<slug>...

Требования:
1) зафиксировать границы модуля (один UI route + один API family + role matrix viewer/operator/admin);
2) создать `backend/app/admin_<slug>_page.py` на `render_admin_shell(...)`;
3) вынести API-логику в `backend/app/admin_<slug>_ops.py` (если не trivially simple);
4) в `backend/app/main.py` оставить только thin-routes;
5) в JS страницы использовать `window.AdminUiKit` (без локального copy-paste helperов);
6) локально py_compile + compileall;
7) деплой на VPS + scripts/admin_panel_smoke_gate.sh + target curl checks;
8) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 20) Heavy pages на `AdminUiKit` primitives (phase-16)

```text
Сделай phase-16 модульной админки: переведи heavy-страницы на общий JS toolkit.
Цели:
- /admin/fleet
- /admin/fleet/alerts
- /admin/fleet/incidents
- /admin/fleet/incidents/{central_id}/{code}

Требования:
1) подключить `window.AdminUiKit` через `base_admin_js()` в page renderer;
2) заменить локальные helper-функции на primitives:
   - setStatus/setText
   - loadWhoami
   - apiPost (и apiGet/apiDelete при необходимости)
   - debounce + Enter-bind
   - esc;
3) не менять URL, payload и response schema API;
4) сохранить role-guard и текущую UX-логику фильтров/bulk-actions;
5) локально py_compile + compileall;
6) деплой на VPS + scripts/admin_panel_smoke_gate.sh;
7) проверить через curl, что на всех 4 страницах есть `window.AdminUiKit`;
8) обновить docs: Админ-панель (модульная разработка), Операции.
```

## 21) Перевод legacy heavy-pages на `render_admin_shell` wrapper (phase-17)

```text
Сделай phase-17: переведи legacy heavy-страницы на render_admin_shell без переписывания DOM.
Цели:
- /admin/fleet
- /admin/fleet/alerts
- /admin/fleet/incidents
- /admin/fleet/incidents/{central_id}/{code}

Требования:
1) в `admin_ui_kit.py` добавь безопасный путь для legacy миграции:
   - `shell_layout` режим для `render_admin_shell`;
   - helper `render_legacy_admin_page(...)`, который парсит legacy `<style>/<body>/<script>` и рендерит через общий shell.
2) в target pages:
   - заменить прямой возврат full HTML на `render_legacy_admin_page(...)`;
   - оставить существующий DOM/JS без изменения логики;
   - сохранить URL/API и role behavior.
3) локально py_compile + compileall;
4) деплой на VPS + scripts/admin_panel_smoke_gate.sh;
5) проверить HTML-маркер `window.AdminUiKit` на всех 4 страницах;
6) обновить docs: Админ-панель (модульная разработка), Операции.
```

## 22) Auto extraction из legacy в shell (phase-18A)

```text
Сделай phase-18A: улучшить render_legacy_admin_page для heavy-страниц.
Требования:
1) в `admin_ui_kit.py` добавить auto extraction из legacy HTML:
   - извлекать style/body/script;
   - извлекать header_title/chips/toolbar из `<header><div class="title">...` и `<div class="toolbar">...`;
   - рендерить через `render_admin_shell(...)` в стандартном shell layout;
   - fallback на `shell_layout=False`, если структура нестандартная.
2) не менять JS/API контракты страниц;
3) локально py_compile + compileall;
4) деплой на VPS + unified smoke-gate;
5) проверить HTML-маркеры shell (`<header>` + `<div class="title">`) на heavy-страницах;
6) обновить docs: Админ-панель (модульная разработка), Операции.
```

## 23) Чистый `render_admin_shell` для одной heavy-страницы (phase-18B step)

```text
Сделай phase-18B step для страницы <target_page_module>.
Требования:
1) убрать full-page `legacy_html` блок из модуля;
2) перейти на явные секции:
   - chips_html
   - toolbar_html
   - body_html
   - extra_css
   - script
   и `return render_admin_shell(...)`;
3) не менять URL, API endpoints, payload/response schema;
4) сохранить role behavior и UX-actions;
5) локально py_compile + compileall;
6) деплой на VPS + unified smoke-gate;
7) отдельный curl check для target UI route;
8) обновить docs: Админ-панель (модульная разработка), Операции.
```

## 24) Phase-19: post-migration cleanup после закрытия heavy pages

```text
Сделай phase-19 cleanup после полного перехода heavy-страниц на `render_admin_shell`.

Требования:
1) убедиться, что `render_legacy_admin_page(...)` больше не используется heavy-модулями (`rg` check);
2) оставить `render_legacy_admin_page(...)` только как fallback/helper (без удаления API-функций, если нужны для будущих страниц);
3) вынести повторяющиеся CSS-фрагменты heavy-страниц в `admin_ui_kit.py` без изменения DOM/JS контрактов;
4) не менять route paths, API endpoints, payload/response schema;
5) локально py_compile + compileall;
6) деплой на VPS + unified smoke-gate;
7) target curl checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`;
8) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
9) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 25) Phase-20: UI/UX polish (UA) на модульной базе

```text
Сделай phase-20 для админки (без изменения API-контрактов и маршрутов).

Цели:
- улучшить читаемость и визуальную иерархию `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`;
- сохранить украинскую локализацию UI и текущую операционную логику;
- не трогать payload/response schema backend API.

Требования:
1) изменения только в page-render модулях и/или `admin_ui_kit.py` (UI слой);
2) улучшить spacing/контраст/состояния фильтров и action-кнопок, не ломая текущие ID/DOM-hooks;
3) сохранить role-guard и bulk operations;
4) локально py_compile + compileall;
5) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
6) target curl checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`;
7) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
8) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 26) Phase-21: операторские потоки и навигация

```text
Сделай phase-21 для админки: улучшить operator workflow без изменений backend schema/API.

Цели:
- ускорить сценарий "увидел инцидент → подтвердил/заглушил → проверил аудит";
- добавить более явные action-path в `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`;
- сохранить украинскую локализацию и существующие DOM hooks (ID/data-атрибуты).

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules), без изменений payload/response;
2) улучшить навигационные link-блоки и action grouping;
3) не ломать role-guard/bulk operations/filters;
4) локально py_compile + compileall + bash -n smoke script;
5) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
6) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
7) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
8) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 27) Phase-22: operator UX rhythm (density/readability)

```text
Сделай phase-22 для админки: выровнять UX-ритм операторских страниц без изменения backend API/schema.

Цели:
- привести `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents` к единому ритму действий;
- улучшить читаемость плотных таблиц в regular/compact режиме;
- сохранить flow-маршрут и role-guard.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) улучшить table density/sorting hints/status chips без изменения ID/data hooks;
3) сохранить bulk/action сценарии и текущие фильтры;
4) локально py_compile + compileall + bash -n smoke script;
5) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
6) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
7) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
8) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 28) Phase-23: golden module shell (IA + UX contracts)

```text
Сделай phase-23 для админки: зафиксируй "golden module shell" для новых страниц без изменений backend API/schema.

Цели:
- единая информационная архитектура для /admin/fleet* модулей;
- единый layout-каркас (header/chips/toolbar/table-meta/cards) и contracts по UX-поведению;
- убрать UI-дрейф при добавлении новых модулей.

Требования:
1) только UI/docs/skills слой (`admin_ui_kit.py`, page modules, docs, skills);
2) определить и внедрить обязательные блоки:
   - flow-route
   - density mode (regular/compact)
   - tableMeta (source/sort/mode)
   - status/action chips;
3) сохранить существующие DOM hooks (ID/data-атрибуты), role-guard и bulk-actions;
4) не менять route paths, API endpoints, payload/response schema;
5) локально py_compile + compileall + bash -n smoke script;
6) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
7) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
8) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы + соответствующий skill workflow.
```

## 29) Phase-24: operator workspace refinement

```text
Сделай phase-24 для админки: улучшить operator workspace поверх golden shell без изменения backend API/schema.

Цели:
- уменьшить время до действия (ack/silence/unsilence);
- закрепить контекст инцидента между страницами (fleet → alerts → incidents);
- улучшить UX-сигналы при bulk-операциях.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules), без изменения payload/response;
2) добавить sticky context hints и быстрые action-presets в рамках существующих DOM hooks;
3) сохранить role-guard и текущие маршруты;
4) локально py_compile + compileall + bash -n smoke script;
5) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
6) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
7) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
8) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 30) Phase-25: operator command palette + saved presets

```text
Сделай phase-25 для админки: добавить operator command palette и сохранённые пресеты фильтров без изменения backend API/schema.

Цели:
- ускорить переключение между рабочими режимами (critical/wg/queue/sla/open);
- сохранить персональные пресеты фильтров оператора в localStorage;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить command palette (keyboard-first) и список сохранённых пресетов (save/apply/delete);
3) сохранить role-guard, bulk-actions и текущие DOM hooks;
4) локально py_compile + compileall + bash -n smoke script;
5) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
6) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
7) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
8) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 31) Phase-26: cross-page preset portability

```text
Сделай phase-26 для админки: добавить переносимость пресетов между страницами (экспорт/импорт JSON + общий namespace) без изменения backend API/schema.

Цели:
- упростить передачу пресетов между операторами;
- хранить пресеты в контролируемом shared-формате;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить экспорт/импорт пресетов с валидацией схемы;
3) сохранить role-guard, bulk-actions и текущие DOM hooks;
4) локально py_compile + compileall + bash -n smoke script;
5) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
6) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
7) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
8) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 32) Phase-27: presets governance + cleanup policy

```text
Сделай phase-27 для админки: ввести governance пресетов (operator/team profiles + cleanup policy) без изменения backend API/schema.

Цели:
- стандартизировать наборы пресетов для команды операторов;
- ввести политику cleanup/retention для локальных и shared пресетов;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить profile templates (например critical/wg/queue/sla) с явным ownership;
3) добавить cleanup-политику (архив/удаление старых пресетов) в localStorage namespace;
4) сохранить role-guard, bulk-actions и текущие DOM hooks;
5) локально py_compile + compileall + bash -n smoke script;
6) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
7) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
8) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
9) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 33) Phase-28: presets observability dashboard

```text
Сделай phase-28 для админки: добавить observability по пресетам (namespace/scope metrics + last cleanup) без изменения backend API/schema.

Цели:
- видеть текущее состояние пресетов у operator/team;
- контролировать рост archive и результат cleanup;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить сводку metrics: total/local/shared/archived + last cleanup per scope;
3) интегрировать summary в `fleet/alerts/incidents` без ломки текущих DOM hooks;
4) локально py_compile + compileall + bash -n smoke script;
5) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
6) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
7) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
8) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 34) Phase-29: preset audit timeline (UI-only)

```text
Сделай phase-29 для админки: добавить timeline-журнал операций с пресетами (cleanup/import/export/profile install) по scope без изменения backend API/schema.

Цели:
- дать оператору быстрый ответ “кто/когда менял пресеты” в рамках текущего браузерного namespace;
- упростить разбор причин дрейфа фильтров между local/shared;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить timeline helper в toolkit на базе localStorage audit trail;
3) отобразить timeline в `fleet/alerts/incidents` (workspace row/card), сохранив текущие DOM hooks;
4) добавить команды palette для просмотра/очистки timeline;
5) локально py_compile + compileall + bash -n smoke script;
6) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
7) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
8) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
9) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 35) Phase-30: preset conflict guard + merge simulator

```text
Сделай phase-30 для админки: добавить conflict guard для пресетов и merge simulator (local/shared) перед import/replace без изменения backend API/schema.

Цели:
- снизить риск перезаписи полезных operator/team пресетов при импорте;
- показать до применения, какие записи будут created/updated/skipped;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить helper для dry-run сравнения наборов (по name + ts + payload hash);
3) добавить UI preview (summary + список конфликтов) на `fleet/alerts/incidents`;
4) добавить команды palette: preview merge / apply replace / apply merge;
5) локально py_compile + compileall + bash -n smoke script;
6) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
7) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
8) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
9) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 36) Phase-31: protected baseline profiles (policy lock)

```text
Сделай phase-31 для админки: добавить policy lock для baseline-пресетов (protected profiles) без изменения backend API/schema.

Цели:
- защитить обязательные operator/team профили от случайного delete/overwrite;
- разрешить override только через явное подтверждение оператора;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить registry protected preset names per scope + helper проверки;
3) блокировать delete/overwrite protected presets по умолчанию и давать explicit unlock confirm;
4) показать protection-state в `fleet/alerts/incidents` (hint/chip) и palette-команды unlock/relock;
5) локально py_compile + compileall + bash -n smoke script;
6) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
7) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
8) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
9) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 37) Phase-32: presets operations cockpit (scope batch)

```text
Сделай phase-32 для админки: добавить presets operations cockpit (batch операции по scope) без изменения backend API/schema.

Цели:
- дать оператору единое место для preview/import/policy/timeline по `fleet`, `fleet_alerts`, `fleet_incidents`;
- ускорить массовые операции при rollout новых Central;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить cockpit helper для batch preview/apply (merge/replace) по нескольким scope;
3) добавить массовые действия policy lock/unlock по выбранным scope;
4) отобразить consolidated summary (conflicts, protected_blocked, result_total) в `fleet/alerts/incidents`;
5) добавить palette-команды для batch режима;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 38) Phase-33: cockpit timeline panel (batch audit)

```text
Сделай phase-33 для админки: добавить cockpit timeline panel для массовых preset-операций (batch audit/drill-down) без изменения backend API/schema.

Цели:
- ускорить разбор массовых изменений пресетов по scope/namespace/action/result;
- дать оператору быстрый drill-down по последним batch-операциям из workspace row;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить helper получения агрегированной ленты cockpit-операций по scope/namespace (с limit/filter);
3) добавить UI panel для timeline на `fleet/alerts/incidents` с фильтрами `scope/action/namespace`;
4) добавить palette-команды для открытия panel и быстрого просмотра последних batch-событий;
5) локально py_compile + compileall + bash -n smoke script;
6) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
7) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
8) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
9) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 39) Phase-34: cockpit rollout assistant (safe apply protocol)

```text
Сделай phase-34 для админки: добавить cockpit rollout assistant (UI-only мастер безопасного массового применения пресетов) без изменения backend API/schema.

Цели:
- стандартизировать operator-protocol для batch apply по новым системам;
- снизить риск ошибок при масштабировании 100-200 транспортов;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить assistant flow: `scope selection -> dry-run summary -> apply confirm -> post-check hints`;
3) отобразить rollback hint и обязательный checklist перед apply;
4) добавить palette-команды для запуска assistant и просмотра последнего rollout summary;
5) локально py_compile + compileall + bash -n smoke script;
6) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
7) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
8) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
9) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 40) Phase-35: left navigation IA hardening

```text
Сделай phase-35 для админки: усилить left navigation IA (модульные группы + jump-links + active workflow state) без изменения backend API/schema.

Цели:
- сделать левое меню устойчивым для масштабирования модулей и операторских сценариев;
- сократить время переходов между `fleet/alerts/incidents/audit` и governance-модулями;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) перегруппировать side-nav по категориям (Operations / Monitoring / Governance / Audit);
3) добавить compact jump-links в ключевых карточках операторского workflow;
4) сохранить текущие DOM hooks и active-route подсветку;
5) локально py_compile + compileall + bash -n smoke script;
6) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
7) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
8) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
9) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 41) Phase-36: navigation personalization

```text
Сделай phase-36 для админки: добавить personalization в left shell (favorites + recent pages + quick intents) без изменения backend API/schema.

Цели:
- ускорить повторяющиеся operator-маршруты;
- дать персональные быстрые переходы без ломки общего IA;
- не менять URL/API endpoints/payload/response schema.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить localStorage favorites и recent pages в sidebar;
3) добавить quick intents для ключевых действий (`alerts bad`, `incidents open`, `audit`);
4) сохранить группировку `Operations/Monitoring/Governance` и active trail;
5) локально py_compile + compileall + bash -n smoke script;
6) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
7) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
8) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
9) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 42) Phase-37: left-nav ergonomics hardening

```text
Сделай phase-37 для админки: усилить эргономику левого меню (collapsible groups + reorder favorites + quick hotkeys) без изменения backend API/schema.

Цели:
- ускорить операторские переходы при длинной сессии и большом числе модулей;
- уменьшить визуальный шум за счёт сворачиваемых групп;
- сохранить текущий IA-каркас и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить collapsed-state для `Operations/Monitoring/Governance` с хранением в localStorage;
3) добавить reorder favorites (up/down или drag-drop) в sidebar;
4) добавить быстрые хоткеи для intent-переходов (`alerts bad`, `incidents open`, `audit`);
5) сохранить active/trail state и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 43) Phase-38: left-nav command hub

```text
Сделай phase-38 для админки: развить левое меню в command hub (inline intent-runner + keyboard cheat-sheet + focus mode) без изменения backend API/schema.

Цели:
- ускорить operator-переходы без открытия лишних страниц/панелей;
- сделать горячие клавиши discoverable прямо в UI;
- сохранить модульный IA и текущую совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить inline command-hub блок в sidebar с запуском ключевых intent-сценариев;
3) добавить visual keyboard cheat-sheet для доступных hotkeys;
4) добавить focus mode для sidebar (компактный вид без потери навигации);
5) сохранить active/trail state и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 44) Phase-39: sidebar intelligence

```text
Сделай phase-39 для админки: развить sidebar intelligence (adaptive intent priority + context-aware hints + session shortcuts) без изменения backend API/schema.

Цели:
- поднимать наиболее полезные intent-сценарии в зависимости от текущего operator-контекста;
- сократить количество лишних переходов при реагировании на алерты/инциденты;
- сохранить модульный IA, быстрый доступ и текущую совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить адаптивный приоритет intent-кнопок по recent/favorites/session context;
3) добавить context-aware sidebar hints (например, по query/state текущей страницы);
4) добавить session shortcuts (последние 3-5 операторских переходов/действий) в sidebar;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 45) Phase-40: sidebar mission-control

```text
Сделай phase-40 для админки: развить sidebar в mission-control (alert-first widgets + one-click triage presets + sticky incident focus) без изменения backend API/schema.

Цели:
- сократить время реакции оператора на критические состояния;
- дать быстрый вход в triage-потоки без ручной настройки фильтров;
- сохранить модульный IA и текущую совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить alert-first sidebar widgets (критичность/очередь/stale акценты) без новых API;
3) добавить one-click triage presets для типовых аварийных сценариев;
4) добавить sticky incident focus (переход и удержание текущего контекста инцидента);
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 46) Phase-41: mission-control automation

```text
Сделай phase-41 для админки: развить mission-control automation (guided recovery playbooks + smart triage chaining + operator handoff notes) без изменения backend API/schema.

Цели:
- ускорить повторяемые recovery-цепочки без ручной координации;
- уменьшить вероятность пропуска шагов при аварийных сценариях;
- сохранить модульный IA и текущую совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить guided recovery playbooks в sidebar mission-control (пошаговые runbooks);
3) добавить smart triage chaining (следующий рекомендованный шаг после выбора triage preset);
4) добавить operator handoff notes (короткие session заметки для передачи смены);
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 47) Phase-42: mission-control evidence loop

```text
Сделай phase-42 для админки: развить mission-control evidence loop (postmortem snapshots + handoff timeline + checklist badges) без изменения backend API/schema.

Цели:
- сделать recovery-работу проверяемой и воспроизводимой между сменами;
- сократить ручные потери контекста после triage;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить быстрый postmortem snapshot из mission-control (контекст + counters + triage preset);
3) добавить handoff timeline/history (локальный журнал заметок с временем);
4) добавить checklist completion badges для runbook-кроков;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 48) Phase-43: mission-control response packs

```text
Сделай phase-43 для админки: развить mission-control response packs (actionable export package + handoff template) без изменения backend API/schema.

Цели:
- ускорить передачу аварийного контекста между операторами;
- сделать evidence-данные готовыми для внешней передачи без ручной сборки;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить response-pack export из mission-control (snapshot + checklist + handoff timeline);
3) добавить handoff template генерацию (краткий операционный summary);
4) добавить быстрый review/copy flow перед передачей смены;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 49) Phase-44: mission-control escalation routing

```text
Сделай phase-44 для админки: развить mission-control escalation routing (rule-based response-pack routing + channel-ready templates) без изменения backend API/schema.

Цели:
- ускорить маршрутизацию инцидентов по типам/критичности;
- стандартизировать передачу response pack в внешние каналы;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить rule-based routing профили для response pack (по severity/code/status);
3) добавить channel-ready шаблоны (короткий, полный, audit-oriented);
4) добавить быстрый выбор профиля и review/copy flow;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 50) Phase-45: mission-control delivery adapters

```text
Сделай phase-45 для админки: развить mission-control delivery adapters (channel-specific handoff adapters на базе response-pack routing) без изменения backend API/schema.

Цели:
- ускорить передачу инцидентов во внешние каналы (Telegram/Email/Web ticket) без ручного форматирования;
- стандартизировать payload для разных каналов из единого response pack;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить channel adapters presets (telegram/email/ticket) поверх phase-44 routing;
3) добавить preview-панель payload variants (short/full/audit + channel envelope);
4) добавить быстрый copy flow: `copy-telegram`, `copy-email`, `copy-ticket`;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 51) Phase-46: mission-control delivery state handoff

```text
Сделай phase-46 для админки: развить mission-control delivery state handoff (delivery journal + queue-ready handoff status) без изменения backend API/schema.

Цели:
- сделать передачу смены воспроизводимой после delivery actions;
- фиксировать историю применений/copy для adapter/variant в рамках operator flow;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить delivery journal (события apply/copy: adapter, variant, ts, context);
3) добавить queue-ready handoff status summary в mission-control;
4) добавить быстрые действия `show-delivery-journal` и `clear-delivery-journal`;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 52) Phase-47: mission-control delivery acknowledgment loop

```text
Сделай phase-47 для админки: развить mission-control delivery acknowledgment loop (ack/retry/escalate lifecycle + SLA-state badges) без изменения backend API/schema.

Цели:
- закрыть цикл доставки после queue-ready handoff;
- снизить риск потери контекста между операторами смены;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить lifecycle actions `ack-delivery`, `retry-delivery`, `escalate-delivery`;
3) добавить SLA-state summary (`fresh/warn/stale`) для delivery/handoff состояния;
4) расширить delivery journal событиями lifecycle (ack/retry/escalate + причина);
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 53) Phase-48: mission-control delivery state automation

```text
Сделай phase-48 для админки: развить mission-control delivery state automation (policy-ready suggestions + bulk action shortcuts) без изменения backend API/schema.

Цели:
- сократить ручные решения оператора по post-delivery действиям;
- ускорить triage повторяющихся инцидентов при масштабировании;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить suggestion engine для `ack/retry/escalate` на базе SLA-state + delivery journal history;
3) добавить bulk-friendly shortcuts для применения рекомендованных действий;
4) добавить summary explainability (`почему рекомендовано это действие`);
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 54) Phase-49: mission-control delivery policy profiles

```text
Сделай phase-49 для админки: развить mission-control delivery policy profiles (balanced/aggressive/conservative + session override) без изменения backend API/schema.

Цели:
- стандартизировать поведение suggestion engine под разные режимы эксплуатации;
- уменьшить ручную перенастройку операторов в смене;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить policy profile selector для delivery automation;
3) добавить session override (локальное хранение выбранного профиля);
4) обновить explainability summary с учётом активного policy profile;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 55) Phase-50: mission-control UX refinement

```text
Сделай phase-50 для админки: развить mission-control UX refinement (keyboard-first flow + action clarity) без изменения backend API/schema.

Цели:
- снизить время triage и количество ошибочных нажатий в delivery flow;
- улучшить визуальную чистоту и понятность высокорисковых действий;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить keyboard shortcuts для ключевых delivery actions;
3) добавить tooltip/microcopy для retry/escalate/bulk операций;
4) добавить mobile-friendly sticky action footer для mission-control delivery блока;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы.
```

## 56) Phase-51: mission-control navigation ergonomics

```text
Сделай phase-51 для админки: развить mission-control navigation ergonomics (левая навигация + мобильный fallback) без изменения backend API/schema.

Цели:
- ускорить перемещение по разделам при ежедневной работе операторов;
- сохранить визуальную чистоту и устойчивость интерфейса при росте числа модулей;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) улучшить левое меню: быстрый поиск по action-группам и пин ключевых секций;
3) добавить компактный режим навигации с понятным mobile fallback;
4) не ломать текущие quick intents/hotkeys и mission-control delivery блок;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 57) Phase-52: mission-control navigation accessibility polish

```text
Сделай phase-52 для админки: развить mission-control navigation accessibility polish (ARIA/keyboard/onboarding) без изменения backend API/schema.

Цели:
- сделать новую левую навигацию удобной для клавиатурной работы и screen-reader сценариев;
- снизить time-to-first-action для новых операторов;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить ARIA-атрибуты и клавиатурную доступность для controls `search/filter/compact` и групп навигации;
3) добавить onboarding-подсказки (краткие и неинтрузивные) по новым nav-actions;
4) не ломать текущие quick intents/hotkeys и mission-control delivery блок;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 58) Phase-53: mission-control operator adoption telemetry

```text
Сделай phase-53 для админки: развить mission-control operator adoption telemetry (UI-only) без изменения backend API/schema.

Цели:
- измерять фактическое использование нового nav-flow (`search/hotkeys/compact`) в смене;
- добавить handoff-сводку по adoption для контроля адаптации операторов;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить локальный telemetry summary по nav-действиям (session/local storage);
3) добавить компактный блок adoption snapshot в mission-control/handoff зоне;
4) не ломать текущие quick intents/hotkeys и delivery controls;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 59) Phase-54: mission-control operator coaching loop

```text
Сделай phase-54 для админки: развить mission-control operator coaching loop (UI-only) без изменения backend API/schema.

Цели:
- превращать telemetry nav-flow в практические рекомендации для операторов смены;
- добавить handoff-инструменты управления adoption snapshot (`reset/export`);
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить coaching hints на базе telemetry (какие действия недоиспользуются);
3) добавить в handoff-блок кнопки `show/export/reset adoption snapshot`;
4) не ломать текущие quick intents/hotkeys, delivery controls и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 60) Phase-55: mission-control coaching cadence scoreboard

```text
Сделай phase-55 для админки: развить mission-control coaching cadence scoreboard (UI-only) без изменения backend API/schema.

Цели:
- сделать качество смен сравнимым через единый scorecard adoption-практик;
- зафиксировать в handoff конкретные next-actions (что тренируем следующей сменой);
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить scorecard по ключевым adoption check-практикам (`pass/warn`, %);
3) добавить next-actions блок в handoff на основе coaching gaps;
4) не ломать текущие quick intents/hotkeys, delivery controls и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 61) Phase-56: mission-control coaching trendline history

```text
Сделай phase-56 для админки: развить mission-control coaching trendline history (UI-only) без изменения backend API/schema.

Цели:
- показать динамику качества смен (не только текущий scorecard, но и тренд);
- дать оператору быстрый сигнал `improving/stable/regressing` в handoff;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить локальную историю scorecard по последним сменам (кольцевой буфер);
3) добавить расчет delta и trend-tone (`improving/stable/regressing`);
4) вывести compact trend summary в handoff рядом с scorecard/next-actions;
5) не ломать текущие quick intents/hotkeys, delivery controls и handoff timeline;
6) сохранить active/trail/focus-mode и текущие DOM hooks;
7) локально py_compile + compileall + bash -n smoke script;
8) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
9) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
10) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
11) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
12) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 62) Phase-57: mission-control coaching reset-pack

```text
Сделай phase-57 для админки: развить mission-control coaching reset-pack (UI-only) без изменения backend API/schema.

Цели:
- добавить управляемый lifecycle trendline history между этапами rollout;
- дать оператору инструменты `show/export/clear` истории coaching-метрик;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить actions для trend history (`show`, `export`, `clear`) в handoff;
3) добавить confirm guardrails для `clear` и статус history (`active/reset recently`);
4) не ломать текущие quick intents/hotkeys, delivery controls, scorecard и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 63) Phase-58: mission-control coaching trend presets

```text
Сделай phase-58 для админки: развить mission-control coaching trend presets (UI-only) без изменения backend API/schema.

Цели:
- ускорить операторский обзор динамики смен через preset-окна trendline;
- добавить компактное сравнение `now vs baseline` без ручного анализа JSON;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить trend window presets (`last 3`, `last 5`, `last 10 saves`) в handoff;
3) добавить compare summary (`now vs baseline`) с понятным tone-сигналом;
4) не ломать текущие quick intents/hotkeys, delivery controls, scorecard/trend и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 64) Phase-59: mission-control coaching decision cues

```text
Сделай phase-59 для админки: развить mission-control coaching decision cues (UI-only) без изменения backend API/schema.

Цели:
- дать оператору быстрый ответ “что делать дальше” прямо в handoff-блоке;
- связать trend/compare/scorecard в единый coaching cue для следующей смены;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить helper для coaching cue по trend (`improving/stable/regressing` + actionable text);
3) вывести coaching cue в mission-control handoff рядом с trend/compare;
4) расширить trend JSON/export payload этим cue для handoff continuity;
5) не ломать текущие quick intents/hotkeys, delivery controls, scorecard/trend и handoff timeline;
6) сохранить active/trail/focus-mode и текущие DOM hooks;
7) локально py_compile + compileall + bash -n smoke script;
8) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
9) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
10) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
11) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
12) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 65) Phase-60: mission-control coaching handoff composer

```text
Сделай phase-60 для админки: развить mission-control coaching handoff composer (UI-only) без изменения backend API/schema.

Цели:
- стандартизировать handoff-текст смены по единому шаблону;
- сократить время передачи смены и снизить пропуски критичных пунктов;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить composer шаблона handoff на базе `scorecard + trend + trend_coach + next_actions`;
3) добавить copy/apply controls для быстрого применения шаблона в `sideHandoffInput`;
4) не ломать текущие quick intents/hotkeys, delivery controls, scorecard/trend и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 66) Phase-61: mission-control handoff quality guard

```text
Сделай phase-61 для админки: развить mission-control handoff quality guard (UI-only) без изменения backend API/schema.

Цели:
- фиксировать минимальный стандарт качества handoff перед передачей смены;
- снизить риск неполной передачи контекста между операторами;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить quality checks для composer-output (`scorecard/trend/coach/next-actions/context`);
3) добавить явный статус `ready/not-ready` и список недостающих пунктов в handoff блоке;
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 67) Phase-62: mission-control handoff quality profiles

```text
Сделай phase-62 для админки: развить mission-control handoff quality profiles (UI-only) без изменения backend API/schema.

Цели:
- дать оператору управляемую строгость quality-гейта (`strict/balanced`);
- сделать policy-состояние явным в handoff перед save;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить profile selector quality policy (`strict/balanced`) с session-persist;
3) адаптировать критерии `buildMissionHandoffQualityState` под выбранный policy;
4) добавить policy-state в `sideHandoffQuality` и timeline events качества;
5) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality и handoff timeline;
6) сохранить active/trail/focus-mode и текущие DOM hooks;
7) локально py_compile + compileall + bash -n smoke script;
8) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
9) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
10) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
11) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
12) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 68) Phase-63: mission-control handoff remediation assistant

```text
Сделай phase-63 для админки: развить mission-control handoff remediation assistant (UI-only) без изменения backend API/schema.

Цели:
- уменьшить количество forced-override при сохранении handoff;
- ускорить исправление `NOT-READY` состояния через one-click remediation;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить remediation actions по missing quality-check пунктам (минимум: note/context/next-actions/composer consistency);
3) добавить explainability-блок: почему save заблокирован и какой шаг исправления рекомендован первым;
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 69) Phase-64: mission-control handoff remediation telemetry

```text
Сделай phase-64 для админки: развить mission-control handoff remediation telemetry (UI-only) без изменения backend API/schema.

Цели:
- измерять эффект remediation assistant на качество handoff;
- видеть в смене, снижается ли forced-override после remediation;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить локальный telemetry контур remediation lifecycle (`applied/skipped`, `override-after-remediation`, `time-to-ready`);
3) добавить compact KPI summary в handoff-блок;
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 70) Phase-65: mission-control handoff remediation timeline drilldown

```text
Сделай phase-65 для админки: развить mission-control handoff remediation timeline drilldown (UI-only) без изменения backend API/schema.

Цели:
- перейти от агрегированных KPI remediation к анализу по отдельным сменам;
- выявлять причины override-after-remediation в последних циклах;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить drilldown timeline по remediation cycles (`last N` с key fields: status, action, ttr, override);
3) добавить export JSON для remediation timeline/KPI;
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 71) Phase-66: mission-control handoff remediation governance pack

```text
Сделай phase-66 для админки: развить mission-control handoff remediation governance pack (UI-only) без изменения backend API/schema.

Цели:
- перевести remediation KPI из наблюдения в управляемый governance-контур;
- видеть compliance относительно целевых порогов (`override/ttr`) в каждой смене;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить policy targets для remediation KPI и compliance state (`ok/warn`);
3) добавить guided next-actions по violations target;
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```

## 72) Phase-67: mission-control handoff remediation governance incidents

```text
Сделай phase-67 для админки: развить mission-control handoff remediation governance incidents (UI-only) без изменения backend API/schema.

Цели:
- замкнуть governance-контур от KPI WARN к операционным действиям;
- дать оператору локальный incident feed по отклонениям remediation compliance;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить локальный governance-incident feed по WARN случаям (`last N`);
3) добавить действия `ack/snooze` для governance incidents с trace в handoff timeline;
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance и handoff timeline;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 73) Phase-68: mission-control handoff remediation incidents operations panel

```text
Сделай phase-68 для админки: развить mission-control handoff remediation incidents operations panel (UI-only) без изменения backend API/schema.

Цели:
- сделать governance-incidents fully-operational для дежурной смены;
- добавить быстрый incidents-journal toolkit внутри handoff-блока;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить incidents operations actions: `show/export/clear` для локального governance incident feed;
3) добавить compact incidents SLA summary (`active/snoozed/acked`, oldest age);
4) добавить trace incidents operations в handoff timeline;
5) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance и handoff timeline;
6) сохранить active/trail/focus-mode и текущие DOM hooks;
7) локально py_compile + compileall + bash -n smoke script;
8) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
9) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
10) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
11) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
12) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 74) Phase-69: mission-control handoff remediation incidents digest board

```text
Сделай phase-69 для админки: развить mission-control handoff remediation incidents digest board (UI-only) без изменения backend API/schema.

Цели:
- сократить время разбора повторяющихся governance WARN в смене;
- дать оператору ранжированный digest по top incident fingerprints;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить digest board по incidents fingerprints (`count`, `oldest age`, `last state`);
3) добавить guided triage hints для top-repeat fingerprints;
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance/incidents;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 75) Phase-70: mission-control handoff remediation digest action planner

```text
Сделай phase-70 для админки: развить mission-control handoff remediation digest action planner (UI-only) без изменения backend API/schema.

Цели:
- перевести incidents digest из аналитики в управляемые действия;
- дать оператору suggested-action план по top fingerprints;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить planner по top fingerprints с suggested actions (`ack/snooze/escalate/profile-check`);
3) добавить генерацию handoff-ready action plan (copy/export) из digest;
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance/incidents/digest;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 76) Phase-71: mission-control remediation planner decision ledger

```text
Сделай phase-71 для админки: развить mission-control remediation planner decision ledger (UI-only) без изменения backend API/schema.

Цели:
- обеспечить трассируемость решений по digest planner в смене;
- видеть покрытие исполнения suggested actions по top fingerprints;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить decision ledger для planner (`show/export/clear`, append на decision events);
3) добавить compact decision coverage summary (planned vs logged);
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance/incidents/digest/planner;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 77) Phase-72: mission-control remediation decision backlog cockpit

```text
Сделай phase-72 для админки: развить mission-control remediation decision backlog cockpit (UI-only) без изменения backend API/schema.

Цели:
- дать оператору список незакрытых planner-решений (coverage-gap);
- ускорить закрытие missing-decisions в рамках смены;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить backlog панель по `missing decisions` из coverage;
3) добавить backlog actions (`show/export/copy`) для handoff-ready summary;
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance/incidents/digest/planner/ledger;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 78) Phase-73: mission-control remediation decision backlog closeout assistant

```text
Сделай phase-73 для админки: развить mission-control remediation decision backlog closeout assistant (UI-only) без изменения backend API/schema.

Цели:
- закрывать `missing decisions` напрямую из backlog без ручного обхода блоков;
- сократить decision-gap к концу смены;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить closeout actions для backlog (`ack/snooze/profile-check`) по конкретной missing-записи;
3) добавить batch closeout для top-missing (без backend writes, только локальный decision ledger);
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance/incidents/digest/planner/ledger/backlog;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 79) Phase-74: mission-control remediation decision closeout governance board

```text
Сделай phase-74 для админки: развить mission-control remediation decision closeout governance board (UI-only) без изменения backend API/schema.

Цели:
- сделать closeout backlog-решений измеримым в смене;
- видеть баланс `single/batch` и decision-type (`ack/snooze/profile-check`);
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить closeout governance summary (`single/batch`, decision-type counters, remaining gap);
3) добавить show/export actions для closeout governance payload (shift-ready JSON);
4) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance/incidents/digest/planner/ledger/backlog/closeout;
5) сохранить active/trail/focus-mode и текущие DOM hooks;
6) локально py_compile + compileall + bash -n smoke script;
7) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
8) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
9) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
10) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
11) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 80) Phase-75: mission-control remediation closeout escalation routing

```text
Сделай phase-75 для админки: развить mission-control remediation closeout escalation routing (UI-only) без изменения backend API/schema.

Цели:
- перевести closeout governance в управляемый escalation-loop по `status/remaining_gap`;
- обеспечить прозрачный shift handoff по эскалациям remediation backlog;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить escalation policy-helpers для closeout governance (`open/progress/risk/closed` + thresholds);
3) добавить actions `show/export/copy` для escalation payload и handoff-ready summary;
4) добавить timeline traces по escalation decisions;
5) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance/incidents/digest/planner/ledger/backlog/closeout;
6) сохранить active/trail/focus-mode и текущие DOM hooks;
7) локально py_compile + compileall + bash -n smoke script;
8) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
9) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
10) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
11) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
12) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 81) Phase-76: mission-control closeout escalation execution logbook

```text
Сделай phase-76 для админки: развить mission-control closeout escalation execution logbook (UI-only) без изменения backend API/schema.

Цели:
- замкнуть выполнение escalation-routing в смене (`ack/snooze/resolve`);
- добавить контроль stale escalation по SLA-age;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить escalation execution journal с lifecycle actions (`ack/snooze/resolve`);
3) добавить escalation SLA-age summary и stale-подсветку;
4) добавить actions `show/export/copy` для execution payload;
5) добавить timeline traces по escalation execution actions;
6) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance/incidents/digest/planner/ledger/backlog/closeout/escalation;
7) сохранить active/trail/focus-mode и текущие DOM hooks;
8) локально py_compile + compileall + bash -n smoke script;
9) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
10) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
11) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
12) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
13) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```


## 82) Phase-77: mission-control closeout escalation execution anomaly guard

```text
Сделай phase-77 для админки: развить mission-control closeout escalation execution anomaly guard (UI-only) без изменения backend API/schema.

Цели:
- выявлять ранние аномалии исполнения escalation (`repeat snooze`, `long stale`, `missing resolve`);
- давать оператору приоритетные next-actions в том же mission-control блоке;
- сохранить модульный IA и совместимость URL/API.

Требования:
1) только UI-слой (`admin_ui_kit.py` + page modules);
2) добавить anomaly detection helpers поверх execution logbook;
3) добавить anomaly summary/board + actions `show/export/copy` для anomaly payload;
4) добавить recommended actions controls для fast remediation anomaly;
5) добавить timeline traces по anomaly lifecycle;
6) не ломать текущие quick intents/hotkeys, delivery controls, trend/composer/quality/remediation/timeline/governance/incidents/digest/planner/ledger/backlog/closeout/escalation/execution;
7) сохранить active/trail/focus-mode и текущие DOM hooks;
8) локально py_compile + compileall + bash -n smoke script;
9) деплой на VPS + `scripts/admin_panel_smoke_gate.sh`;
10) target checks: `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`, `/admin/audit`;
11) лог API без `ResponseValidationError|Traceback|coroutine object|ERROR`;
12) обновить docs: Админ-панель (модульная разработка), Операции, Скиллы;
13) в итоге обязательно зафиксировать: что сделано и зачем, и что будет сделано следующим этапом и зачем.
```
