# LTE (EM7455) и GPS (USB) на Central

Цель: подготовить `central-gw` к работе с LTE/GPS модулями, без привязки к камере/RTC.

Важно:

- **PIN/APN не хранить** в репозитории; передавать параметрами команд.
- На старте Wi‑Fi может оставаться основным uplink, LTE — как fallback/боевой канал.

## Текущий статус (последняя проверка: 2026-02-15)

- Central видит модем Sierra EM7455/MC7455 (QMI): есть `/dev/cdc-wdm0`, `wwan0`, `ttyUSB*`.
- SIM в слоте определяется как `present`. Для Yezzz!/lifecell подключение поднимается через `APN=internet`.
- PIN: для стабильной автозагрузки **PIN1 отключён** на SIM (иначе после ребута потребуется ручной ввод PIN).
- GPS: вероятный источник GNSS — сам модем (NMEA на одном из `ttyUSB*`), включаем после готовности ModemManager.
- Маршрутизация: LTE сделан основным uplink (route metric ниже), Wi‑Fi — fallback.

## LTE: bootstrap (ModemManager + NetworkManager)

Скрипт устанавливает стек и (опционально) поднимает соединение по APN:

```bash
./scripts/central_lte_setup.sh --central-ip 192.168.10.1 --user orangepi --pin <PIN> --apn <APN>
```

Для Yezzz!/lifecell (тестовая SIM, 15GB) — рабочий дефолт:

- `APN: internet`
- username/password: пусто

### PIN: снимать или оставлять?

- PIN **не влияет** на “видимость SIM” (`present/absent`) — это про контакт/слот.
- PIN влияет на **авто‑подключение после reboot**: если PIN включён, модем будет `locked (sim-pin)` и LTE не поднимется без разблокировки.

Рекомендация для fleet (100–200 устройств, без ручного доступа): **снять PIN**.

Снять PIN на Central можно через ModemManager (пример для текущего `SIM/0`):

```bash
ssh orangepi@192.168.10.1 'sudo mmcli -L'
ssh orangepi@192.168.10.1 'sudo mmcli -m <MODEM_ID> | sed -n "1,120p"'
ssh orangepi@192.168.10.1 'sudo mmcli -i 0 --pin <PIN> --disable-pin'
ssh orangepi@192.168.10.1 'sudo qmicli -d /dev/cdc-wdm0 --device-open-proxy --uim-get-card-status | sed -n "1,120p"'
```

Ожидаемо в `qmicli`: `PIN1 state: 'disabled'`.

## Приоритет LTE vs Wi‑Fi (route metrics)

По умолчанию мы держим Wi‑Fi предпочтительным. Чтобы сделать LTE основным uplink:

- поставить LTE metric ниже;
- поставить Wi‑Fi metric выше.

Пример (LTE primary, Wi‑Fi fallback):

```bash
ssh orangepi@192.168.10.1 'sudo nmcli connection modify lte ipv4.route-metric 100 ipv6.route-metric 100'
ssh orangepi@192.168.10.1 'sudo nmcli connection modify \"|CHERDAK|5G\" ipv4.route-metric 900 ipv6.route-metric 900'
ssh orangepi@192.168.10.1 'sudo nmcli connection down lte || true; sudo nmcli connection up lte || true'
ssh orangepi@192.168.10.1 'sudo nmcli connection down \"|CHERDAK|5G\" || true; sudo nmcli connection up \"|CHERDAK|5G\" || true'
ssh orangepi@192.168.10.1 'ip r | sed -n \"1,20p\"'
```

Проверка, что дефолтный маршрут действительно через LTE:

```bash
ssh orangepi@192.168.10.1 'ip route get 1.1.1.1 | sed -n \"1,2p\"'
```

## Reboot-check (обязательная проверка)

После любых изменений LTE/PIN/metrics — делаем reboot и проверяем, что всё поднялось автоматически:

```bash
ssh orangepi@192.168.10.1 'sudo reboot'
# ждать 20–60 секунд
ssh orangepi@192.168.10.1 'sudo nmcli -t -f NAME,TYPE,DEVICE connection show --active'
ssh orangepi@192.168.10.1 'ip r | sed -n \"1,25p\"'
ssh orangepi@192.168.10.1 'ip route get 1.1.1.1 | sed -n \"1,2p\"'
ssh orangepi@192.168.10.1 'ping -c 2 1.1.1.1'
ssh orangepi@192.168.10.1 'ping -c 2 10.66.0.1 && curl -sS --max-time 4 http://10.66.0.1/health'
ssh orangepi@192.168.10.1 'journalctl -u passengers-central-heartbeat.service -n 10 --no-pager'
```

Если APN неизвестен:

```bash
./scripts/central_lte_setup.sh --central-ip 192.168.10.1 --user orangepi --pin <PIN>
```

Что проверить:

- `mmcli -L` показывает модем;
- `nmcli dev status` показывает поднятое GSM соединение (после указания APN);
- маршрутизация: Wi‑Fi остаётся предпочтительным (LTE metric выше), либо наоборот — по требованиям.

Диагностика SIM (если ModemManager ругается на `sim-missing`):

```bash
ssh orangepi@192.168.10.1 'sudo qmicli -d /dev/cdc-wdm0 --uim-get-card-status | sed -n "1,120p"'
```

Ожидаемо: `Card state: 'present'`. Если `absent` — SIM не видна модему (проверить слот/контакты/адаптер).

Практический чеклист “SIM absent”:

- вынуть/вставить SIM, проверить ориентацию;
- проверить адаптер nanoSIM→microSIM (часто проблема в контактах);
- если у модема есть выбор слота (SIM0/SIM1) — проверить, куда вставлена SIM физически;
- повторить проверку `qmicli ... --uim-get-card-status`.

## GPS: обнаружение USB устройства

```bash
./scripts/central_gps_detect.sh --central-ip 192.168.10.1 --user orangepi
```

Ожидаем:

- появление `/dev/serial/by-id/*` и/или `/dev/ttyACM*`/`/dev/ttyUSB*`;
- в `dmesg` видим, какой драйвер поднялся и какой `tty` выделен.

Примечание:

- у EM7455/MC7455 GNSS может приходить как NMEA на одном из `ttyUSB*` (часто интерфейс `if02`).

### GNSS через EM7455 (рекомендуемый путь)

На `central-gw` ModemManager помечает GNSS порт как `ttyUSB1 (gps)`, а AT порт как `ttyUSB2 (at)` (смотрите `mmcli -m <MODEM_ID>`).

Важно: пока модем в состоянии `failed (sim-missing)` или `locked (sim-pin)`, ModemManager не даст включить location. Поэтому порядок такой:

1) Сначала добиться `SIM present` (см. раздел LTE/SIM выше).
2) Затем включить модем и (если нужно) разблокировать PIN:

```bash
ssh orangepi@192.168.10.1 'sudo mmcli -L'
ssh orangepi@192.168.10.1 'sudo mmcli -m <MODEM_ID> --enable'
ssh orangepi@192.168.10.1 'sudo mmcli -m <MODEM_ID> --pin "<PIN>"'
```

3) Включить GPS‑NMEA в ModemManager и читать NMEA/координаты через `mmcli` (это самый стабильный путь для интеграции в сервисы):

```bash
ssh orangepi@192.168.10.1 'sudo mmcli -m <MODEM_ID> --location-enable-gps-nmea || true'
ssh orangepi@192.168.10.1 'sudo mmcli -m <MODEM_ID> --location-status | sed -n "1,120p"'
ssh orangepi@192.168.10.1 'sudo mmcli -m <MODEM_ID> --location-get | sed -n "1,160p"'
ssh orangepi@192.168.10.1 'sudo mmcli -m <MODEM_ID> --location-get -J | head -c 800; echo'
```

Примечание: `gps-unmanaged` на этом модеме может быть `Unsupported` — это нормально. В таком случае поток NMEA может **не** появляться в `cat /dev/ttyUSB1`, но ModemManager всё равно отдаёт NMEA в `--location-get`.

## GPS: автозапуск + “latest fix” файл (внедрено на Central)

Чтобы интеграция была стабильной (и не зависела от ручных `mmcli` после ребута), ставим сервисы снимка GPS:

```bash
./scripts/install_central_gps_services.sh --central-ip 192.168.10.1 --user orangepi --interval 10
```

Что появляется на `central-gw`:

- `passengers-gps-enable.service` — включение GNSS источников (oneshot после загрузки).
- `passengers-gps-snapshot.timer` → `passengers-gps-snapshot.service` — периодически пишет:
  - `/var/lib/passengers/gps/latest.json` (читается без `sudo`).

Проверка:

```bash
ssh orangepi@192.168.10.1 'systemctl status passengers-gps-snapshot.timer --no-pager | sed -n "1,30p"'
ssh orangepi@192.168.10.1 'cat /var/lib/passengers/gps/latest.json | head -c 800; echo'
```

Важно для тестов:

- в помещении/без антенны будет `fix=false`, `lat/lon=null` — это нормально.
- для первого fix: вынести антенну/устройство “под небо” и подождать 1–5 минут.

### Чек-лист “є реальний GPS fix”

1) На Central:

```bash
ssh orangepi@192.168.10.1 'cat /var/lib/passengers/gps/latest.json | head -c 900; echo'
```

Ожидаемо:

- `"fix": true`
- `"lat": <число>`, `"lon": <число>`

2) В админці:

- `https://207.180.213.225:8443/admin/fleet`
- в колонці `GPS` має бути `FIX` + координати.

### Live-моніторинг GPS fix (з ПК)

Поки ви на вулиці “ловите” fix, зручно запустити цикл:

```bash
ssh orangepi@192.168.10.1 'while true; do date -u; cat /var/lib/passengers/gps/latest.json; echo; sleep 2; done'
```

Якщо через ~10 хвилин під відкритим небом `fix=true` не з’явився:

- перевірити, що GNSS антена під’єднана саме до GNSS порту EM7455;
- перевірити живлення/USB стабільність модема;
- подивитись `sudo mmcli -m 0 --location-status` (чи увімкнені `gps-nmea/gps-raw`).

## Интеграция GPS в батч (Central→Backend)

`mvp/central_flush.py` теперь добавляет `stop.gps={lat,lon}` в payload, **только если**:

- в `/var/lib/passengers/gps/latest.json` есть `fix=true`;
- координаты не stale (по умолчанию `max_age_sec=120`).

Это позволит на backend сразу хранить `gps_lat/gps_lon` в `stops`, без изменения протокола.

### Smoke-тест без реального GPS fix (рекомендуется)

В помещении часто `fix=false`. Чтобы проверить “проводку” данных end-to-end, используйте mock‑тест:

```bash
./scripts/central_gps_payload_smoke.sh --central-ip 192.168.10.1 --user orangepi
```

Ожидаемо: вывод `stop.gps = {"lat": ..., "lon": ...}` (значит `central_flush.py` реально подхватывает GPS).

## GPS в heartbeat и админке (Central→Backend→UI)

`mvp/central_heartbeat.py` отправляет `gps` в heartbeat (fix/age/lat/lon), чтобы это можно было показывать в `/admin/fleet`.

Важно: чтобы колонка GPS появилась в админке, нужно **обновить backend на VPS** (см. `Docs/Проект/Операции/Сервер backend и VPN.md` → restart/rebuild compose).

## Следующий шаг (позже)

- если понадобится более богатая телеметрия (скорость/курс/точность) — расширяем `stop.gps` и/или добавляем GPS в heartbeat (потребует расширения backend модели).
- если появится отдельный USB GPS (не модем) — можно включить `gpsd` и использовать `gpspipe -w` как источник.
