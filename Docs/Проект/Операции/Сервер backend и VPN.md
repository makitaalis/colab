# Сервер backend и VPN

## TL;DR (вход + быстрые проверки)

Вход на VPS (канон: пользователь `alis`, доступ по SSH key):

```bash
ssh alis@207.180.213.225
```

Быстрые проверки на VPS:

```bash
ssh alis@207.180.213.225 'hostname && whoami && sudo -n true'
ssh alis@207.180.213.225 'sudo wg show'
ssh alis@207.180.213.225 'cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml ps'
ssh alis@207.180.213.225 'cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml logs --tail=120 api'
```

Публичная админка (из любой сети):

- URL: `https://207.180.213.225:8443/admin` (ожидаемо `401` без BasicAuth)
- WG peers UI: `https://207.180.213.225:8443/admin/wg`
- Client MVP UI (внутренний preview под BasicAuth): `https://207.180.213.225:8443/client`
- Client API preview: `https://207.180.213.225:8443/api/client/whoami`
- Если SSH недоступен при работающей `8443` — см. `Docs/Проект/Проблемы/Сервер и админка.md`.

## Проверка доступа к серверу

```bash
ssh alis@207.180.213.225 'hostname && sudo -n true'
ssh alis@207.180.213.225 'sudo ufw status verbose && sudo fail2ban-client status'
```

## Posture-check (единый контроль безопасности)

```bash
./scripts/server_security_posture_check.sh --server-host 207.180.213.225 --server-user alis --admin-user admin --admin-pass "<BASIC_AUTH_PASS>"
```

Если пароль хранится в многострочном файле с описанием, извлекать значение строки `- pass:`:

```bash
ADMIN_PASS=$(awk -F': ' '/^  - pass:/{print $2; exit}' 'pass admin panel')
./scripts/server_security_posture_check.sh --server-host 207.180.213.225 --server-user alis --admin-user admin --admin-pass "$ADMIN_PASS"
```

## Установка timer для авто-аудита posture

```bash
./scripts/install_server_security_posture_timer.sh --server-host 207.180.213.225 --server-user alis
ssh alis@207.180.213.225 'sudo systemctl list-timers --all | grep passengers-security-posture.timer'
ssh alis@207.180.213.225 'cat /opt/passengers-backend/ops-reports/security-posture-latest.json'
```

## Управление backend

```bash
ssh alis@207.180.213.225 'cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml ps'
ssh alis@207.180.213.225 'cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml logs --tail=200 api'
ssh alis@207.180.213.225 'cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml restart api'
```

## Авто-старт backend после reboot (systemd)

```bash
./scripts/install_server_backend_service.sh --server-host 207.180.213.225 --server-user alis
ssh alis@207.180.213.225 'sudo systemctl status passengers-backend.service --no-pager'
```

## Экспорт статуса WireGuard для админки (systemd timer)

```bash
./scripts/install_server_wg_exporter.sh --server-host 207.180.213.225 --server-user alis
ssh alis@207.180.213.225 'sudo systemctl status passengers-wg-export.timer --no-pager'
ssh alis@207.180.213.225 'sudo head -n 40 /opt/passengers-backend/wg/peers.json'
```

Важно:

- Всегда используйте `-f compose.yaml -f compose.server.yaml`. Если запустить `docker compose up ...` только с `compose.yaml`, пропадёт port mapping `10.66.0.1:80 -> 8000`, nginx начнёт отдавать `502 Bad Gateway` (upstream connection refused).
- Быстрая проверка после деплоя: `curl -k -u admin:<pass> https://127.0.0.1:8443/api/admin/whoami` должно вернуть `200`.
- Для client-контура: `curl -k -u admin:<pass> https://127.0.0.1:8443/api/client/whoami` должно вернуть `200`.
- Начиная с Client step-9:
  - client BasicAuth файл: `/etc/nginx/passengers-client.htpasswd`;
  - admin BasicAuth файл: `/etc/nginx/passengers-admin.htpasswd`;
  - rollout support-логина: `./scripts/client_support_rollout.sh ...`;
  - rollout scope-bindings: `./scripts/client_scope_rollout.sh --bindings "<actor:central[:vehicle],...>" ...`.
- Начиная с Client step-11:
  - канон actor: `support-<system_id>`;
  - matrix rollout (users + scope + post-check): `./scripts/client_support_matrix_rollout.sh --matrix-file <path> ...`;
  - шаблон матрицы: `Docs/Проект/Операции/client-support-onboarding-matrix.example`.
- Начиная с Client step-12:
  - lifecycle actions для support actor: `rotate/disable/revoke`;
  - lifecycle rollout script: `./scripts/client_support_lifecycle_rollout.sh --action <rotate|disable|revoke> --actor <support-...> ...`;
  - после `disable/revoke` actor должен получать `401` на `/api/client/whoami`.
- Начиная с Client step-13:
  - batch rotation script: `./scripts/client_support_rotation_batch.sh --plan-file <path> ...`;
  - inventory report script: `./scripts/client_support_inventory_report.sh --write <path>`;
  - install timers: `./scripts/install_client_support_lifecycle_timer.sh`;
  - server reports:
    - `/opt/passengers-backend/ops-reports/client-support-inventory-latest.md`;
    - `/opt/passengers-backend/ops-reports/client-support-rotation-reminder.txt`.
- Начиная с Client step-14:
  - UX-polish rollout report: `Docs/auto/web-panel/client-step14-ux-polish-rollout.md`;
  - при UI-only деплоях клиентской панели применять тот же server-first цикл:
    - `rsync -> py_compile -> docker compose ... --build api -> smoke/regression/security checks`.
- Начиная с Client step-15:
  - a11y+keyboard+copy rollout report: `Docs/auto/web-panel/client-step15-a11y-keyboard-copy-rollout.md`;
  - regression/audit checks должны подтверждать shell markers:
    - `skipLink`, `sideCompactToggle`, `clientMainContent`.
- Начиная с Client step-16:
  - keyboard-only acceptance report: `Docs/auto/web-panel/client-step16-accessibility-acceptance.md`;
  - operator acceptance script: `./scripts/client_panel_step16_accessibility_check.sh --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated" --write Docs/auto/web-panel/client-step16-accessibility-acceptance.md`.
- Начиная с Client step-17:
  - handoff checklist script: `./scripts/client_panel_step17_handoff_check.sh --write Docs/auto/web-panel/client-step17-handoff-checklist.md`;
  - handoff checklist report: `Docs/auto/web-panel/client-step17-handoff-checklist.md`.

## Проверка WG+health с Central

```bash
ssh orangepi@192.168.10.1 'ping -c 2 10.66.0.1 && curl -sS http://10.66.0.1/health'
```

## Backup/restore/hardening

- backup install: `scripts/install_server_db_backup.sh`
- restore check: `scripts/server_db_restore_check.sh`
- hardening: `scripts/install_server_admin_hardening.sh`
- fleet health auto: `scripts/install_server_fleet_health_auto.sh`
- security posture audit: `scripts/server_security_posture_check.sh`
- security posture timer: `scripts/install_server_security_posture_timer.sh`

## Полный набор команд

- `Docs/Проект/Операции (подробно).md`
