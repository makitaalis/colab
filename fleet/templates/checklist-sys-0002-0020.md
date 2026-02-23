# Checklist массового ввода `sys-0002..sys-0020`

1. Открыть шаблон: `fleet/templates/registry-sys-0002-0020.template.csv`.
2. Для каждой строки заполнить `vehicle_id` в формате `bus-XXX_AA1234BB`.
3. Проверить, что `server_endpoint` корректный (`207.180.213.225:51820`) и единый.
4. Не менять `wg_ip` без отдельного плана адресации.
5. Перенести строки в `fleet/registry.csv` пакетами (рекомендуется 3–5 систем).
6. После каждого пакета запускать:
   - `python3 scripts/fleet_registry.py validate`
   - `python3 scripts/fleet_scale_dry_run.py --target-systems 200`
7. Для каждого `system_id` генерировать bundle:
   - `python3 scripts/fleet_registry.py bundle --system-id <SYSTEM_ID>`
8. Запускать rollout-check (без железа, только реестр+bundle+оркестратор):
   - `python3 scripts/fleet_rollout_check.py --system-id <SYSTEM_ID>`
9. Перед полевым вводом системы пройти e2e путь из `fleet/out/<SYSTEM_ID>/commands.md`.
10. После фактического ввода фиксировать commissioning:
   - `python3 scripts/fleet_commission.py --system-id <SYSTEM_ID> --smoke`
