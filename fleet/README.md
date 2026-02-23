# Fleet Registry

Этот каталог хранит реестр всех систем (до 100–200 комплектов).

## Файл реестра

- `fleet/registry.csv`

Колонки:

- `system_id` — уникальный ID комплекта (`sys-0001`, `sys-0002`, …)
- `vehicle_id` — ID транспорта (`bus-017_AA1234BB`)
- `wg_ip` — уникальный WireGuard IP Central (`10.66.0.X`)
- `server_endpoint` — endpoint WG сервера (`host:port`)
- `status` — `planned|active|retired|lab|disabled`
- `notes` — комментарий

Правило масштаба:

- один транспорт = один `system_id` + один WG peer + один ingest key;
- `CENTRAL_ID` в bundle/central env должен совпадать с `system_id`.

## Команды

Проверка реестра:

```bash
python3 scripts/fleet_registry.py validate
```

Подсказать следующий свободный WG IP:

```bash
python3 scripts/fleet_registry.py next-wg-ip
```

Масштабный dry-run (не меняет боевой `fleet/registry.csv`, проверяет модель на 100–200 систем):

```bash
python3 scripts/fleet_scale_dry_run.py --target-systems 200
```

Артефакты:

- `Docs/auto/fleet-scale/scale-dry-run-<UTC>.md`
- `Docs/auto/fleet-scale/registry-sim-<UTC>.csv`
- `Docs/auto/fleet-scale/INDEX.md`

Сгенерировать пакет шаблонов для ручного ввода `sys-0002..sys-0020`:

```bash
python3 scripts/fleet_batch_template.py --from 2 --to 20
```

Результат:

- `fleet/templates/registry-sys-0002-0020.template.csv`
- `fleet/templates/checklist-sys-0002-0020.md`

Сгенерировать bundle для конкретной системы:

```bash
python3 scripts/fleet_registry.py bundle --system-id sys-0001
```

Результат создаётся в `fleet/out/<system_id>/`:

- `fleet.env`
- `wireguard/server-peer.conf`
- `wireguard/central-wg0.conf.template`
- `passengers/central-passengers.env.template`
- `commands.md`

В `fleet.env` и `central-passengers.env.template` заранее фиксируются:

- `STOP_MODE=manual` (текущий ранний этап проекта)
- `STOP_FLUSH_INTERVAL_SEC=120` (используется если `STOP_MODE=timer`)
- `CENTRAL_ID=<SYSTEM_ID>` (уникальная идентификация Central в backend/alerts)
- offline queue профиль:
  - `CENTRAL_EVENTS_MAX_ROWS=300000`
  - `CENTRAL_EVENTS_MAX_AGE_SEC=1209600`
  - `CENTRAL_SENT_BATCHES_MAX_ROWS=50000`
  - `CENTRAL_SENT_BATCHES_MAX_AGE_SEC=2592000`
  - `CENTRAL_PENDING_BATCHES_MAX_ROWS=10000`
  - `CENTRAL_PENDING_BATCHES_MAX_AGE_SEC=2592000`
  - `CENTRAL_PENDING_BATCHES_DROP_AGE=0`

## Автоматизаторы rollout

Применить peer в `/etc/wireguard/wg0.conf` на сервере (idempotent):

```bash
python3 scripts/fleet_apply_wg_peer.py --system-id sys-0001 --fetch-central-pubkey
```

Если у нового Central ещё нет ключей WG:

```bash
python3 scripts/fleet_apply_wg_peer.py --system-id sys-0001 --fetch-central-pubkey --ensure-central-key
```

Применить env для `central-gw` (подтянуть API key с сервера и перезапустить сервисы):

```bash
python3 scripts/fleet_apply_central_env.py --system-id sys-0001
```

Оркестратор этапов:

```bash
./scripts/fleet_rollout.sh --system-id sys-0001 --all-safe
./scripts/fleet_rollout.sh --system-id sys-0001 --apply-wg-peer --wg-fetch-central-pubkey --all-safe
```

Rollout-check отчёт (без железа, только реестр/bundle/orchestrator):

```bash
python3 scripts/fleet_rollout_check.py --system-id sys-0002
python3 scripts/fleet_rollout_check.py --from 2 --to 20
```

Commissioning проверки + отчёт:

```bash
python3 scripts/fleet_commission.py --system-id sys-0001 --smoke
```

## Per-system API keys

Локальные секреты (не коммитятся):

- `fleet/secrets/system_api_keys.csv`
- `fleet/secrets/admin_api_key.txt`

Создать ключ для системы:

```bash
python3 scripts/fleet_api_keys.py ensure --system-id sys-0002
```

Ротация/отзыв:

```bash
python3 scripts/fleet_api_keys.py rotate --system-id sys-0002
python3 scripts/fleet_api_keys.py revoke --system-id sys-0002 --reason maintenance
```

Синхронизация ключей на сервер (обновляет `PASSENGERS_API_KEYS`, `ADMIN_API_KEYS`, nginx admin token):

```bash
python3 scripts/fleet_api_keys.py sync-server --server-host 207.180.213.225 --server-user alis
```

Примечание:

- `fleet_apply_wg_peer.py --fetch-central-pubkey` автоматически подставляет ключ в `server-peer.conf` из `central-gw`.
