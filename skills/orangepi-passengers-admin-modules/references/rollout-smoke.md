# Rollout Smoke Template

## Deploy

```bash
scp backend/app/main.py alis@207.180.213.225:/tmp/passengers-main.py
ssh alis@207.180.213.225 'sudo install -m 644 -o alis -g alis /tmp/passengers-main.py /opt/passengers-backend/app/main.py && rm -f /tmp/passengers-main.py'
ssh alis@207.180.213.225 'cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api'
```

## API checks

```bash
ssh alis@207.180.213.225 'token=$(grep -m1 "^ADMIN_API_KEYS=" /opt/passengers-backend/.env | cut -d= -f2 | tr -d "\r" | cut -d, -f1); curl -sS -H "Authorization: Bearer ${token}" "http://10.66.0.1/api/admin/fleet/monitor?window=24h"'
```

## HTML checks

```bash
ssh alis@207.180.213.225 'curl -k -u "admin:<BASIC_AUTH_PASS>" -sS https://127.0.0.1:8443/admin/fleet | head -n 40'
```

## Logs

```bash
ssh alis@207.180.213.225 'cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml logs --tail=80 api'
```
