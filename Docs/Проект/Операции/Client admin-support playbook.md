# Client admin-support playbook

Документ фиксирует приёмочный сценарий для режима `admin-support` в клиентском контуре.

## Цель

- проверить, что support-режим даёт расширенную видимость без перегруза клиента;
- обеспечить единый сценарий handoff между оператором и поддержкой.

## Preconditions

1. Backend доступен на `https://207.180.213.225:8443`.
2. BasicAuth валиден (файл `pass admin panel`).
3. Для проверки `admin-support` в backend должен быть задан:
   - `CLIENT_SUPPORT_USERS=<login>`.

## Постоянный rollout support-логина (step-9)

```bash
./scripts/client_support_rollout.sh \
  --support-user support \
  --support-pass-file "pass client support panel" \
  --support-users support \
  --admin-pass-file "pass admin panel"
```

Что делает rollout:

1. Разделяет nginx auth-файлы:
- client: `/etc/nginx/passengers-client.htpasswd`
- admin: `/etc/nginx/passengers-admin.htpasswd`
2. Обновляет backend env:
- `CLIENT_SUPPORT_USERS=support`
3. Пересобирает API и проверяет:
- support -> `/api/client/whoami` (`admin-support`)

## Scope rollout (step-10)

```bash
./scripts/client_scope_rollout.sh \
  --bindings "support:sys-0001" \
  --admin-pass-file "pass admin panel"
```

Проверка после применения:

```bash
curl -k -u support:<SUPPORT_PASS> -sS "https://207.180.213.225:8443/api/client/whoami"
curl -k -u support:<SUPPORT_PASS> -sS "https://207.180.213.225:8443/api/client/vehicles?limit=20"
```
- support -> `/api/admin/whoami` (`401`)

## Multi-support onboarding policy (step-11)

Рекомендуемый канон для поддержки:

- actor naming: `support-<system_id>`;
- onboarding source: матрица `actor|password_file|scope_entries`;
- env формируются автоматически: `CLIENT_SUPPORT_USERS`, `CLIENT_SCOPE_BINDINGS`.

Пример матрицы:

```text
support-sys-0001|pass client support sys-0001 panel|sys-0001
```

```bash
./scripts/client_support_matrix_rollout.sh \
  --matrix-file Docs/auto/web-panel/client-step11-support-matrix.txt \
  --admin-pass-file "pass admin panel"
```

Что делает rollout:

1. Применяет nginx split auth и обновляет `passengers-client.htpasswd`.
2. Удаляет legacy `support*` логины, которых нет в матрице.
3. Обновляет backend env:
- `CLIENT_SUPPORT_USERS=<actors_from_matrix>`;
- `CLIENT_SCOPE_BINDINGS=<bindings_from_matrix>`.
4. Пересобирает API, ждёт readiness и запускает post-check:
- `whoami` + role/scope для каждого support actor;
- `401` для `/api/admin/whoami`;
- `client_panel_regression_check` (первый support actor);
- `admin_panel_smoke_gate` (если передан admin password).

## Support actor lifecycle policy (step-12)

Lifecycle actions для actor `support-<system_id>`:

- `rotate`: смена пароля actor без downtime;
- `disable`: временное отключение actor (удаление из `CLIENT_SUPPORT_USERS` + client htpasswd);
- `revoke`: полное удаление actor (disable + удаление из `CLIENT_SCOPE_BINDINGS`).

```bash
./scripts/client_support_lifecycle_rollout.sh \
  --action rotate \
  --actor support-sys-0001 \
  --new-pass-file "pass client support sys-0001 panel rotated" \
  --old-pass-file "pass client support sys-0001 panel" \
  --skip-smoke 1
```

```bash
./scripts/client_support_lifecycle_rollout.sh \
  --action disable \
  --actor support-sys-0001 \
  --actor-pass-file "pass client support sys-0001 panel rotated" \
  --skip-smoke 1
```

```bash
./scripts/client_support_lifecycle_rollout.sh \
  --action revoke \
  --actor support-sys-0001 \
  --actor-pass-file "pass client support sys-0001 panel rotated" \
  --admin-pass-file "pass admin panel"
```

Policy outcome:

1. rotate: новый пароль активен, старый пароль невалиден.
2. disable: actor получает `401` на `/api/client/*` и `/api/admin/*`.
3. revoke: actor удаляется из auth и scope-контура.

## Lifecycle automation pack (step-13)

Автоматизация lifecycle-операций:

1. Batch rotation:
```bash
./scripts/client_support_rotation_batch.sh \
  --plan-file Docs/auto/web-panel/client-step13-rotation-plan.txt \
  --admin-pass-file "pass admin panel"
```
2. Inventory/drift report:
```bash
./scripts/client_support_inventory_report.sh \
  --write Docs/auto/web-panel/client-support-inventory-latest.md
```
3. Server timers (daily inventory + monthly rotation reminder):
```bash
./scripts/install_client_support_lifecycle_timer.sh
ssh -4 alis@207.180.213.225 'sudo systemctl list-timers --all | grep -E "passengers-client-support-(inventory|rotation-reminder)"'
```

## Базовый preflight (read-only)

```bash
./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"
./scripts/client_panel_regression_check.sh --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated"
python3 scripts/client_panel_step7b_audit.py --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated" --write Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001-step16.md
./scripts/client_panel_step16_accessibility_check.sh --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated" --write Docs/auto/web-panel/client-step16-accessibility-acceptance.md
```

Ожидается `PASS` по всем шагам.

## Keyboard-only acceptance (step-16)

Операторский сценарий фиксации финального DoD client shell:

1. Проверить `role=admin-support` и `scope` через `/api/client/whoami`.
2. Проверить shell markers:
- `skipLink`, `sideCompactToggle`, `clientMainContent`.
3. Проверить keyboard shortcuts:
- `/`, `Esc`, `Alt+Shift+M`, `Alt+Shift+K`, `Alt+Shift+S`, `Alt+Shift+T`.
4. Проверить account copy markers:
- `Профіль` и `Сповіщення` без admin-терминологии.

## RC handoff checklist (step-17)

Единый прогон финального RC-checklist:

```bash
./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/client-step17-handoff-checklist.md
```

Ожидается:

- `RESULT: PASS`;
- обновлённые отчёты `step-16`, `step7b(step-17)` и `step-17 checklist`.

## Сценарий A: режим `client`

1. Проверить роль:
```bash
curl -k -u "admin:<BASIC_AUTH_PASS>" -sS "https://207.180.213.225:8443/api/client/whoami"
```
Ожидается:
- `role=client`
- `capabilities.support_console=false`

2. Проверить страницы:
- `/client/profile` (summary + форма + secondary details);
- `/client/notifications` (summary + presets + secondary details).

## Сценарий B: режим `admin-support`

1. Использовать policy actor из матрицы (пример):
- `support-sys-0001`.

2. Проверить роль:
```bash
curl -k -u "support-sys-0001:<SUPPORT_PASS>" -sS "https://207.180.213.225:8443/api/client/whoami"
```
Ожидается:
- `role=admin-support`
- `capabilities.support_console=true`
- `scope.central_ids` соответствует `CLIENT_SCOPE_BINDINGS` для actor.

3. Проверить UX-поведение:
- на `Тікети/Статуси/Профіль/Сповіщення` отображается `роль: admin-support`;
- secondary-блоки доступны для быстрого handoff;
- payload-copy работает на account-страницах.

## Rollback

1. Для восстановления отключённого actor выполнить matrix rollout (`step-11`) с нужным actor.
2. Для аварийного блокирования actor использовать `step-12` action `disable` или `revoke`.
3. Проверить итог:
- actor -> `/api/client/whoami` (`401`) при disable/revoke;
- основной actor поддержки сохраняет `role=admin-support`.

## Артефакты

- Реальный audit-отчёт: `Docs/auto/web-panel/client-step7b-ux-audit.md`
- Support audit (policy actor): `Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001.md`
- Этапный журнал: `Docs/Проект/Операции/Админка модульные этапы.md`
- Rollout-отчёт: `Docs/auto/web-panel/client-step9-support-rollout.md`
- Scope-отчёт: `Docs/auto/web-panel/client-step10-scope-rollout.md`
- Multi-support rollout: `Docs/auto/web-panel/client-step11-multi-support-onboarding.md`
- Lifecycle rollout: `Docs/auto/web-panel/client-step12-support-lifecycle-rollout.md`
- Lifecycle automation pack: `Docs/auto/web-panel/client-step13-lifecycle-automation-pack.md`
- UX polish rollout: `Docs/auto/web-panel/client-step14-ux-polish-rollout.md`
- A11y + keyboard + copy rollout: `Docs/auto/web-panel/client-step15-a11y-keyboard-copy-rollout.md`
- Keyboard-only acceptance: `Docs/auto/web-panel/client-step16-accessibility-acceptance.md`
- RC kickoff (IA freeze): `Docs/auto/web-panel/client-step17-rc-kickoff.md`
- RC handoff checklist: `Docs/auto/web-panel/client-step17-handoff-checklist.md`
- Support audit (step-16): `Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001-step16.md`
- Support audit (step-17): `Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001-step17.md`
- Latest support inventory: `Docs/auto/web-panel/client-support-inventory-latest.md`
