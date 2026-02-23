# Сеть и WireGuard

## Типовые сбои

- WG пингуется, но backend health не доступен.
- WG peer не применяется из-за placeholder ключа.
- Временный `No route to host` к серверу (UFW limit/fail2ban).
- После миграции `CENTRAL_ID` видны старый и новый идентификаторы.
- `ssh` в LAN (`192.168.10.0/24`) внезапно стал `Connection timed out`.

## Базовые проверки

```bash
ssh orangepi@192.168.10.1 'ping -c 2 10.66.0.1 && curl -sS http://10.66.0.1/health'
ssh alis@207.180.213.225 'sudo wg show; sudo fail2ban-client status; sudo ufw status verbose'
python3 scripts/fleet_apply_wg_peer.py --system-id sys-0002 --fetch-central-pubkey --ensure-central-key
```

## SSH timeout до OPi в LAN (192.168.10.0/24)

Симптом:

- `ssh orangepi@192.168.10.11` → `Connection timed out`

Чек‑лист:

1) Проверить, что ноутбук действительно в сети `192.168.10.0/24`:

```bash
ip -brief addr
ip route
```

2) Проверить, что линк на Ethernet поднят и правильный интерфейс:

```bash
nmcli dev status
```

3) Если включён VPN/WARP — он может менять маршрутизацию и “ломать” доступ к локальной подсети:

- временно отключить WARP/VPN, или
- включить “allow LAN” / split‑tunnel и исключить `192.168.10.0/24`.

4) Проверить, что узел реально жив (питание/линк на свиче) и IP не поменялся:

```bash
ssh -o ConnectTimeout=5 orangepi@192.168.10.1 'hostname; ip -brief addr'
ssh -o ConnectTimeout=5 orangepi@192.168.10.11 'hostname; ip -brief addr'
```

## Источник подробных решений

- `Docs/Проект/Проблемы (подробно).md`
