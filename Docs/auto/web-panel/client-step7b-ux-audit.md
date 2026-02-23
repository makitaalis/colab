# Client Step-7b UX Audit

- generated_at_utc: `2026-02-16T15:30:48+00:00`
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
| `/api/client/whoami contract` | `PASS` | role=client |
| `/api/client/home contract` | `PASS` | sla_risk=1 attention=2 |
| `/api/client/vehicles contract` | `PASS` | rows=2 |
| `/api/client/profile contract` | `PASS` | locale=uk |
| `/api/client/notification-settings contract` | `PASS` | level=critical |

## Real Data Snapshot

- role: `client`
- home.transport_total: `2`
- home.sla_risk/sla_warn: `1/1`
- home.eta_avg/max: `9.5/14`
- vehicles.rows: `2`
- vehicles.sla_ok/warn/risk: `0/1/1`
- profile.locale: `uk`
- notifications.level/digest: `critical/1h`

## Verdict

- status: `PASS`
