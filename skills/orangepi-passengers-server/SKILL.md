---
name: orangepi-passengers-server
description: Backend server bootstrap and operations for the OrangePi_passangers project. Use when setting up or rehydrating the external Ubuntu server (UFW/fail2ban/SSH hardening/Docker Compose), deploying the backend service, and keeping server-related documentation in sync.
---

# OrangePi Passengers Server

## Canon

- Backend MVP plan: `Docs/настройка ПО/План/4. Backend сервер (Ubuntu + Docker Compose).md`
- Backend contract: `Docs/Проект/Сервер (Central→Backend).md`

## Workflow

1) Verify SSH access (key-only) and sudo:

```bash
ssh alis@207.180.213.225 'sudo -n true && hostname'
```

2) Verify protections:

```bash
ssh alis@207.180.213.225 'sudo ufw status verbose && sudo fail2ban-client status'
```

3) Deploy backend (Docker Compose):

- Source: `backend/`
- Target: `/opt/passengers-backend`
- Use compose override for server:

```bash
cd /opt/passengers-backend
sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build
```

4) Keep docs aligned:

- Ops index: `Docs/Проект/Операции.md`
- Scale plan: `Docs/настройка ПО/План/11. Масштабирование 100-200 систем (реестр и шаблоны).md`

Scale identity rule:

- for each transport use unique `central_id` equal to `system_id` (`sys-XXXX`);
- use this `central_id` in `/api/admin/fleet/monitor-policy/overrides` and incident filters.

5) For new Central peer rollout use:

```bash
python3 scripts/fleet_apply_wg_peer.py --system-id <SYSTEM_ID>
```
