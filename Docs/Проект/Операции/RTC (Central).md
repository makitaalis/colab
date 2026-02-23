# RTC (Central / `central-gw`)

Цель: после полного обесточивания/перезагрузки `central-gw` должен поднимать **адекватное системное время из RTC** даже без интернета/GPS, чтобы:

- корректно стартовали сервисы и логи;
- `chrony` мог дальше раздавать единое время в LAN;
- при появлении интернета/GPS время уточнялось, а RTC обновлялся.

## Факт по текущему стенду (2026-02-16)

- `central-gw` имеет встроенный SoC RTC: `sun6i-rtc 7000000.rtc` (`/dev/rtc0`).
- В образе Debian Bookworm для OPi отсутствуют штатные unit’ы `systemd-hwclock-set.service` (поэтому добавляем свой ранний unit).
- Внешний I2C RTC модуль (DS3231) подключён к `central-gw`, но **I2C-линия должна быть поднята правильным overlay** и не должна конфликтовать с Ethernet.
- DS3231 детектится на `i2c-3`:
  - `0x68` — сам RTC (`ds3231`);
  - `0x57` — EEPROM на плате (если присутствует, это нормально).

### Фактическая проверка (2026-02-16, UTC)

Проверка выполнена по SSH на `orangepi@192.168.10.1`.

- `overlays=ph-i2c3` в `/boot/orangepiEnv.txt` — соответствует принятой схеме.
- `i2cdetect -y 3` показал `UU` на `0x68` и `57` на `0x57` (штатно для DS3231 + EEPROM).
- На узле есть `/dev/rtc0` (SoC) и `/dev/rtc1` (внешний DS3231).
- `hwclock --rtc=/dev/rtc1 --show` совпадает с `date -u` с расхождением на уровне миллисекунд.
- `passengers-rtc-writeback.timer` активен, `passengers-rtc-writeback.service` завершался с `status=0/SUCCESS`.
- `chronyc tracking`: синхронизация есть (`Leap status: Normal`, `Stratum: 2`).
- `rtc-init.service` и `passengers-rtc-external.service` включены и отрабатывают успешно (`Result=success`).

Примечание:

- в момент проверки `rtc0` отставал от `rtc1`; рабочим источником времени для boot-инициализации остаётся `rtc1` через `/usr/local/sbin/passengers-rtc-hctosys`.

## Важно: I2C пины на OPi Zero 3 и конфликт с Ethernet

На OPi Zero 3 часть “pi-*” pin-групп использует SoC пины `PI*`, которые на этой плате задействованы под `emac0` (RGMII).

Практический вывод для стенда:

- **Не включать** `overlays=pi-i2c2` на `central-gw`: этот вариант использует `PI9/PI10` и **ломает Ethernet** (`end0` исчезает).
- Для RTC на пинах `SDA/SCL` (header pin `3/5`) включаем **`overlays=ph-i2c3`**, который поднимает I2C3 на `PH4/PH5` (без конфликта с `emac0`).

### Проверенная распиновка 26‑pin header (Orange Pi Zero 3)

Для DS3231/DS1307 подключаемся к **I2C3 (TWI3)** на 26‑pin разъёме:

| OPi Zero 3 pin | Сигнал | SoC pin | RTC module |
|---:|---|---|---|
| 1 | 3.3V | — | `VCC` |
| 3 | I2C3 SDA | `PH5` | `SDA` |
| 5 | I2C3 SCL | `PH4` | `SCL` |
| 6 | GND | — | `GND` |

Важно: `Pin 6 (GND)` физически находится **в соседней колонке** (чётные пины), поэтому один “однорядный” коннектор `1×4` в одной колонке обычно приводит к ошибке питания/земли.

Текущее значение (должно быть так):

```bash
grep -n '^overlays' /boot/orangepiEnv.txt
# overlays=ph-i2c3
```

После изменения overlay — reboot обязателен.

## Диагностика: “I2C bus locked” (частая причина)

Если `dmesg` показывает `I2C bus locked` на нужном bus (например `i2c-3`) — это почти всегда:

- перепутаны `SDA/SCL` на модуле RTC,
- или одна из линий замкнута на `GND/3.3V`,
- или смещён разъём на 1 пин.

Быстрый тест:

```bash
sudo timeout 3 /usr/sbin/i2cdetect -y 3 || echo "BUS LOCKED/TIMEOUT"
dmesg | tail -n 200 | grep -i 'I2C bus locked' || true
```

## Что сделано на `central-gw`

### 1) Пакеты для диагностики I2C (на будущее)

```bash
sudo apt-get update
sudo apt-get install -y i2c-tools
```

### 1.1) Включить нужный I2C overlay (OPi Zero 3)

Файл:

```bash
sudo nano /boot/orangepiEnv.txt
```

Строка:

```ini
overlays=ph-i2c3
```

Перезагрузка:

```bash
sudo reboot
```

### 1.2) Проверка, что DS3231 виден на шине

```bash
sudo /usr/sbin/i2cdetect -l
sudo /usr/sbin/i2cdetect -y 3
```

Ожидаемо увидеть:

- `UU` на `0x68` (нормально: адрес уже занят драйвером `ds3231`);
- иногда `57` (EEPROM на плате модуля);
- `68` (без `UU`) возможно до привязки драйвера.

### 2) Ранний unit чтения времени из RTC на boot

```bash
sudo tee /etc/systemd/system/rtc-init.service >/dev/null <<'EOF'
[Unit]
Description=Initialize system time from RTC
DefaultDependencies=no
Before=sysinit.target
After=local-fs.target

[Service]
Type=oneshot
ExecStart=/sbin/hwclock --hctosys

[Install]
WantedBy=sysinit.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable rtc-init.service
```

Проверка:

```bash
systemctl status rtc-init.service --no-pager
journalctl -b -u rtc-init.service --no-pager
```

### 3) Зафиксировать UTC-режим hwclock (создать `/etc/adjtime`)

```bash
sudo hwclock --systohc --utc
cat /etc/adjtime
```

Ожидаемо: последняя строка `UTC`, а `timedatectl` показывает `RTC in local TZ: no`.

### 4) RTC write-back при корректном времени

У нас `chrony` на `central-gw` уже включает `rtcsync`, поэтому после синхронизации (интернет/GPS) ядро будет периодически обновлять RTC.

Проверка:

```bash
chronyc tracking
sudo hwclock --show
```

## Поднятие внешнего DS3231 как `/dev/rtc1` + автозапуск (как у нас на стенде)

### A) Разово: привязать драйвер и создать `/dev/rtc1`

```bash
sudo modprobe rtc-ds1307
echo ds3231 0x68 | sudo tee /sys/class/i2c-adapter/i2c-3/new_device
ls -l /dev/rtc*
```

Проверка:

```bash
sudo hwclock --rtc=/dev/rtc1 --show
```

Если время на DS3231 “нулевое” (например 2000‑01‑01) — это нормально для нового модуля без батарейки/после сброса. Записываем текущее системное время:

```bash
sudo hwclock --systohc --utc --rtc=/dev/rtc1
sudo hwclock --rtc=/dev/rtc1 --show
```

### B) На boot: автоматически поднимать DS3231 и читать время из него

У нас стоят units:

- `/etc/systemd/system/passengers-rtc-external.service` — поднимает `ds3231` на `i2c-3:0x68` (создаёт `/dev/rtc1`);
- `/etc/systemd/system/rtc-init.service` — читает время на boot через `/usr/local/sbin/passengers-rtc-hctosys` (использует `/dev/rtc1`, если он есть);
- `/etc/systemd/system/passengers-rtc-writeback.timer` — раз в ~30 минут пишет системное время обратно в DS3231 (только если `NTPSynchronized=yes`, иначе пропускает).

Быстрые проверки:

```bash
systemctl status passengers-rtc-external.service rtc-init.service passengers-rtc-writeback.timer --no-pager
sudo hwclock --rtc=/dev/rtc1 --show
```

## Отложенный тест (сделать позже): cold-start без интернета

Цель: убедиться, что после полного обесточивания `central-gw` поднимает корректное время **только из DS3231**, без Wi‑Fi/LTE/NTP.

Сценарий:

1) На `central-gw` отключить интернет-линки:

```bash
sudo nmcli radio wifi off || true
sudo nmcli connection down lte || true
```

2) Полностью обесточить `central-gw` на 30–60 секунд (вытащить питание).
3) Включить питание и сразу (в первые 1–2 минуты) проверить:

```bash
date -u
sudo hwclock --rtc=/dev/rtc1 --show
journalctl -b -u passengers-rtc-external.service -u rtc-init.service --no-pager | tail -n 80
```

Ожидаемо:

- `date -u` близко к реальному времени;
- `/dev/rtc1` существует и отдаёт адекватное время;
- `rtc-init.service` отрабатывает без ошибок.

## Проверка внешнего RTC модуля (диагностика / переподключение)

1) Убедиться, что нужная шина есть и модуль виден:

```bash
sudo i2cdetect -l
sudo i2cdetect -y 3
```

Для DS3231 ожидаем `UU` или `68` на адресе `0x68` (в зависимости от того, привязан ли драйвер в момент проверки).

2) Проверить устройство RTC и чтение времени:

```bash
ls -l /dev/rtc*
sudo hwclock --rtc=/dev/rtc1 --show
```

3) Если после переподключения `rtc1` не поднялся, переинициализировать драйвер:

```bash
sudo /usr/local/sbin/passengers-rtc-external-setup
ls -l /dev/rtc*
sudo hwclock --rtc=/dev/rtc1 --show
```
