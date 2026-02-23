# Backend (API и админка)

## Назначение

- Принимать данные от Central.
- Хранить и агрегировать fleet-состояние.
- Давать admin API и web-панель для мониторинга/алертов/аудита.

## Ключевые API families

- ingest: `/api/v1/ingest/*`
- fleet monitor: `/api/admin/fleet/overview`, `/monitor`, `/health`
- incidents/alerts/actions: `/api/admin/fleet/incidents*`, `/alerts*`
- policy/notifications: `/api/admin/fleet/monitor-policy*`, `/notification-settings*`
- audit/RBAC: `/api/admin/whoami`, `/api/admin/audit`

## UI families

- `/admin`, `/admin/fleet`, `/admin/fleet/alerts`, `/admin/fleet/incidents`
- `/admin/fleet/policy`, `/admin/fleet/notifications`, `/admin/fleet/notify-center`
- `/admin/fleet/actions`, `/admin/audit`, `/admin/wg`

## Связанные документы

- Админка (модули): `Docs/Проект/Админ-панель (модульная разработка).md`
- Операции: `Docs/Проект/Операции.md`
- Подробно: `Docs/Проект/Модули (подробно).md`
