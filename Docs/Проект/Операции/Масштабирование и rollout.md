# Масштабирование и rollout

## Реестр и валидация

```bash
python3 scripts/fleet_registry.py validate
python3 scripts/fleet_registry.py next-wg-ip
python3 scripts/fleet_scale_dry_run.py --target-systems 200
```

## Rollout одной системы

```bash
python3 scripts/fleet_registry.py bundle --system-id sys-0002
python3 scripts/fleet_apply_wg_peer.py --system-id sys-0002 --fetch-central-pubkey --ensure-central-key
python3 scripts/fleet_apply_central_env.py --system-id sys-0002
./scripts/fleet_rollout.sh --system-id sys-0002
python3 scripts/fleet_commission.py --system-id sys-0002
```

## Массовый шаблон

```bash
python3 scripts/fleet_batch_template.py --from-id 2 --to-id 20
```

## Правило масштаба

- один транспорт = один `system_id` = один `central_id` = один WG peer.

## Полный набор команд

- `Docs/Проект/Операции (подробно).md`
