# Alerts API Checklist

## Required endpoints

- `GET /api/admin/fleet/alerts`
- `GET /api/admin/fleet/alerts/groups`
- `GET /api/admin/fleet/incidents`
- `POST /api/admin/fleet/alerts/ack`
- `POST /api/admin/fleet/alerts/silence`
- `POST /api/admin/fleet/alerts/unsilence`

## Minimum filters

- `severity`
- `include_silenced`
- `central_id`
- `code`
- `q`
- bounded `limit`

## Grouping requirements (`alerts/groups`)

- group by `code`
- include:
  - `total`
  - `centrals_total`
  - `silenced`
  - `good/warn/bad`
  - `dominant_severity`
  - `latest_ts`

## Bulk actions

- operate on `(central_id, code)` pairs
- return per-request HTTP status
- expose aggregate result in UI (`success`, `failed`)
