---
name: orangepi-passengers-setup
description: Provisioning and operations workflow for the OrangePi_passangers project. Use when setting up/rehydrating OPi nodes (central-gw, door-1, door-2), flashing SD cards, verifying network/time, enabling passwordless sudo, generating baseline/inventory reports, and keeping the docs aligned before proceeding to application services.
---

# OrangePi Passengers Setup

## Canon first

Door mapping and IPs must match the canon:

- `Docs/настройка ПО/План/0. Паспорт дверей (door_id ↔ hostname ↔ IP).md`

## Workflow (recommended order)

### 1) Flash + offline setup (doors)

Use:

- `scripts/flash_opizero3_sd.sh`
- `Docs/настройка ПО/0 - базовая настройка ОС/1 - Загрузка ОС на Флеш карту/2 - Быстрая прошивка SD и офлайн настройка door-1 door-2 (LAN+SSH).md`

### 2) Verify baseline

```bash
python3 scripts/opizero_baseline.py --host 192.168.10.1 --user orangepi
python3 scripts/opizero_inventory.py --user orangepi 192.168.10.1 192.168.10.11 192.168.10.12
```

### 3) Enable passwordless sudo (optional)

```bash
./scripts/enable_passwordless_sudo.sh enable 192.168.10.1 192.168.10.11 192.168.10.12
```

Doc: `Docs/настройка ПО/План/1.3 Passwordless sudo (опционально).md`

### 4) Watchdog baseline (required for transport)

```bash
./scripts/install_opi_watchdog.sh --opi-user orangepi --hosts '192.168.10.1 192.168.10.11 192.168.10.12' --runtime-watchdog-sec 30s --shutdown-watchdog-sec 2min --interval-sec 45
```

### 5) Offline queue profile (no modules stage)

```bash
python3 scripts/fleet_registry.py bundle --system-id <SYSTEM_ID>
python3 scripts/fleet_apply_central_env.py --system-id <SYSTEM_ID>
```

This applies central queue limits, including pending batch caps:

- `CENTRAL_PENDING_BATCHES_MAX_ROWS`
- `CENTRAL_PENDING_BATCHES_MAX_AGE_SEC`
- `CENTRAL_PENDING_BATCHES_DROP_AGE`

### 6) Time sync

Continue with:

- `Docs/настройка ПО/План/3. Синхронизация времени (критично для данных).md`

### 7) Backend server (Ubuntu + Compose)

Continue with:

- `Docs/настройка ПО/План/4. Backend сервер (Ubuntu + Docker Compose).md`

### 8) MVP pipeline (no GPS/RTC)

Continue with:

- `Docs/настройка ПО/План/5. MVP контур (Edge→Central→Backend) без GPS-RTC.md`

### 8.1) Controlled offline validation (Central -> Server)

Before marking system as baseline-ready, run long offline test:

```bash
./scripts/test_central_server_controlled_offline.sh --outage-sec 1800 --cycle-sec 60 --events-per-cycle 1 --wait-drain-sec 900 --poll-sec 5 --smoke
python3 scripts/fleet_commission.py --system-id <SYSTEM_ID> --smoke
```

### 9) Scale rollout for 100–200 systems

Use registry + bundle generation before flashing/deploy:

```bash
python3 scripts/fleet_registry.py validate
python3 scripts/fleet_registry.py next-wg-ip
python3 scripts/fleet_registry.py bundle --system-id <SYSTEM_ID>
```

Mandatory scale rule:

- one transport = one `system_id` + one WG peer + one ingest key;
- generated `CENTRAL_ID` must be unique and equal to `SYSTEM_ID` in `fleet/out/<SYSTEM_ID>/passengers/central-passengers.env.template`.

Then apply rollout helpers:

```bash
python3 scripts/fleet_apply_wg_peer.py --system-id <SYSTEM_ID>
python3 scripts/fleet_apply_central_env.py --system-id <SYSTEM_ID>
./scripts/fleet_rollout.sh --system-id <SYSTEM_ID> --all-safe
python3 scripts/fleet_rollout_check.py --system-id <SYSTEM_ID>
```

Canon for scale workflow:

- `Docs/настройка ПО/План/11. Масштабирование 100-200 систем (реестр и шаблоны).md`

## Keep docs updated

Use the docs index:

- `Docs/Проект/INDEX.md`
