# Client MVP step-17 — RC IA freeze kickoff (2026-02-16)

## Цель

Зафиксировать release-candidate kickoff после `step-16`: синхронизировать IA `меню -> подменю`, обновить runbook и подтвердить серверные проверки.

## Что выполнено

1. Добавлен каноничный IA-документ:
- `Docs/Проект/Веб-панель/Архитектура меню (admin+client).md`.
2. Обновлены ссылки и runbook:
- `Docs/Проект/INDEX.md`;
- `Docs/Проект/Операции.md`;
- `Docs/Проект/Операции/Client admin-support playbook.md`;
- `Docs/Проект/Операции/Сервер backend и VPN.md`;
- `Docs/Проект/Веб-панель (ядро и домены).md`;
- `Docs/Проект/Веб-панель/Ядро (Core).md`;
- `Docs/Проект/Веб-панель/Домен Клієнт.md`.

## Контрольный прогон

1. `./scripts/client_panel_step16_accessibility_check.sh --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated" --write Docs/auto/web-panel/client-step16-accessibility-acceptance.md` — `PASS`.
2. `./scripts/admin_panel_smoke_gate.sh --admin-pass-file "pass admin panel"` — `PASS`.
3. `./scripts/client_panel_regression_check.sh --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated"` — `PASS`.
4. `python3 scripts/client_panel_step7b_audit.py --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel step13-rotated" --write Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001-step16.md` — `PASS`.
5. `./scripts/server_security_posture_check.sh --server-host 207.180.213.225 --server-user alis --admin-user admin --admin-pass "<resolved>"` — `PASS`.

## Примечание по безопасности

Если файл `pass admin panel` хранится как многострочный runbook, значение пароля для `server_security_posture_check.sh` нужно извлекать из строки `- pass: ...`, а не передавать весь файл как password.

## Итог

`step-17` переведён в состояние `kickoff`: IA freeze + синхронизированный runbook + валидированный server-first baseline.
