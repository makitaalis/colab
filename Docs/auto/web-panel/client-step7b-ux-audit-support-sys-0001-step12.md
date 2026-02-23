# Client Step-7b UX Audit

- generated_at_utc: `2026-02-16T15:50:02+00:00`
- base_url: `https://207.180.213.225:8443`

## Checks

| Check | Result | Details |
|---|---|---|
| `/client auth/anon` | `PASS` | auth=200 anon=401 |
| `/client/vehicles auth/anon` | `PASS` | auth=200 anon=401 |
| `/client/tickets auth/anon` | `PASS` | auth=200 anon=401 |
| `/client/status auth/anon` | `PASS` | auth=200 anon=401 |
| `/client/profile auth/anon` | `PASS` | auth=200 anon=401 |
| `/client/notifications auth/anon` | `PASS` | auth=200 anon=401 |
| `/api/client/whoami auth/anon` | `PASS` | auth=200 anon=401 |
| `/api/client/home auth/anon` | `PASS` | auth=200 anon=401 |
| `/api/client/vehicles?limit=20 auth/anon` | `PASS` | auth=200 anon=401 |
| `/api/client/tickets?limit=20 auth/anon` | `PASS` | auth=200 anon=401 |
| `/api/client/status?limit=20 auth/anon` | `PASS` | auth=200 anon=401 |
| `/api/client/profile auth/anon` | `PASS` | auth=200 anon=401 |
| `/api/client/notification-settings auth/anon` | `PASS` | auth=200 anon=401 |
| `/client/profile markers` | `PASS` | role-chip + secondary + summary |
| `/client/notifications markers` | `PASS` | role-chip + presets + secondary + summary |
| `/api/client/whoami contract` | `PASS` | role=admin-support |
| `/api/client/home contract` | `PASS` | sla_risk=0 attention=1 |
| `/api/client/vehicles contract` | `PASS` | rows=1 |
| `/api/client/profile contract` | `PASS` | locale=uk |
| `/api/client/notification-settings contract` | `PASS` | level=all |

## Real Data Snapshot

- role: `admin-support`
- home.transport_total: `1`
- home.sla_risk/sla_warn: `0/1`
- home.eta_avg/max: `5.0/5`
- vehicles.rows: `1`
- vehicles.sla_ok/warn/risk: `0/1/0`
- profile.locale: `uk`
- notifications.level/digest: `all/24h`

## Verdict

- status: `PASS`
