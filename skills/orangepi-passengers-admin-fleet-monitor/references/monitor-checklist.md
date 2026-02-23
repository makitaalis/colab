# Monitor Checklist

## Contract invariants

- `status`, `ts_generated`, `window`, `window_sec`, `since_ts`
- `state.severity` and `state.message`
- `fleet`, `incidents`, `notifications`, `security`
- `attention_total`, `alerts_total`

## Auto-notify checks

- `dry_run` path works without side effects
- `force=1` bypass works as designed
- decision values remain predictable (`disabled`, `below_threshold`, `rate_limited`, `dry_run`, `sent`)

## Smoke

- `GET /api/admin/fleet/monitor`
- `GET /api/admin/fleet/health`
- `POST /api/admin/fleet/health/notify-auto?dry_run=1&force=1`
- `GET /admin/fleet` still loads and shows monitor-driven data
