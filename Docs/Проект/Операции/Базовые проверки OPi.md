# Базовые проверки OPi

## Доступность узлов

```bash
ping -c 1 192.168.10.1
ping -c 1 192.168.10.11
ping -c 1 192.168.10.12
ssh orangepi@192.168.10.1 'hostnamectl --static'
ssh orangepi@192.168.10.11 'hostnamectl --static'
ssh orangepi@192.168.10.12 'hostnamectl --static'
```

## Post-reboot health

```bash
ssh orangepi@192.168.10.1 'systemctl is-system-running; systemctl --failed --no-legend'
ssh orangepi@192.168.10.11 'systemctl is-system-running; systemctl --failed --no-legend'
ssh orangepi@192.168.10.12 'systemctl is-system-running; systemctl --failed --no-legend'
```

## Baseline / inventory

```bash
python3 scripts/opizero_baseline.py --host 192.168.10.1 --user orangepi
python3 scripts/opizero_inventory.py --user orangepi 192.168.10.1 192.168.10.11 192.168.10.12
```

## Полный набор команд

- `Docs/Проект/Операции (подробно).md`
