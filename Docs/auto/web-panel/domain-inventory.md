# Web Panel Domain Inventory

- generated_at_utc: `2026-02-16T16:13:48+00:00`

## Admin Panel Domains

### Старт (`start`)
- audience: `admin`
- owner: `web-panel-admin`
- doc: `Docs/Проект/Веб-панель/Домен Старт.md`
- routes:
  - `overview` -> `/admin`, page `admin_overview_page.py`, api-group `fleet-overview`
  - `commission` -> `/admin/commission`, page `admin_commission_page.py`, api-group `commissioning`

### Флот (`fleet-ops`)
- audience: `admin`
- owner: `web-panel-admin`
- doc: `Docs/Проект/Веб-панель/Домен Флот.md`
- routes:
  - `fleet` -> `/admin/fleet`, page `admin_fleet_page.py`, api-group `fleet-overview`
  - `alerts` -> `/admin/fleet/alerts`, page `admin_fleet_alerts_page.py`, api-group `alerts-ops`
  - `incidents` -> `/admin/fleet/incidents?status=open&include_resolved=0`, page `admin_fleet_incidents_page.py`, api-group `incident-detail`
  - `actions` -> `/admin/fleet/actions`, page `admin_fleet_actions_page.py`, api-group `alerts-actions`

### Сповіщення (`notifications`)
- audience: `admin`
- owner: `web-panel-admin`
- doc: `Docs/Проект/Веб-панель/Домен Сповіщення.md`
- routes:
  - `notify-center` -> `/admin/fleet/notify-center`, page `admin_fleet_notify_center_page.py`, api-group `notify-center`
  - `notifications` -> `/admin/fleet/notifications`, page `admin_fleet_notifications_page.py`, api-group `notification-rules`

### Контроль і KPI (`analytics`)
- audience: `admin`
- owner: `web-panel-admin`
- doc: `Docs/Проект/Веб-панель/Домен Контроль и KPI.md`
- routes:
  - `history` -> `/admin/fleet/history`, page `admin_fleet_history_page.py`, api-group `policy-kpi`
  - `policy` -> `/admin/fleet/policy`, page `admin_fleet_policy_page.py`, api-group `policy-kpi`
  - `audit` -> `/admin/audit`, page `admin_audit_page.py`, api-group `audit`

### Інфраструктура (`infra`)
- audience: `admin`
- owner: `web-panel-admin`
- doc: `Docs/Проект/Веб-панель/Домен Інфраструктура.md`
- routes:
  - `wg` -> `/admin/wg`, page `admin_wg_page.py`, api-group `wg-ops`

## Client Panel Domains

### Кабінет (`home`)
- audience: `client`
- owner: `web-panel-client`
- doc: `Docs/Проект/Веб-панель/Домен Клієнт.md`
- routes:
  - `client-home` -> `/client`, page `client_home_page.py`, api-group `client-home`
  - `client-vehicles` -> `/client/vehicles`, page `client_vehicles_page.py`, api-group `client-vehicles`

### Звернення (`tickets`)
- audience: `client`
- owner: `web-panel-client`
- doc: `Docs/Проект/Веб-панель/Домен Клієнт.md`
- routes:
  - `client-tickets` -> `/client/tickets`, page `client_tickets_page.py`, api-group `client-tickets`
  - `client-status` -> `/client/status`, page `client_status_page.py`, api-group `client-status`

### Профіль (`account`)
- audience: `client`
- owner: `web-panel-client`
- doc: `Docs/Проект/Веб-панель/Домен Клієнт.md`
- routes:
  - `client-profile` -> `/client/profile`, page `client_profile_page.py`, api-group `client-profile`
  - `client-notifications` -> `/client/notifications`, page `client_notifications_page.py`, api-group `client-notifications`
