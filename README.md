# OrangePi_passangers — документация развёртывания

В этом репозитории сейчас лежит **эксплуатационная документация** по развёртыванию стенда/системы на **Orange Pi Zero 3** для подсчёта пассажиров (Door-узлы + Central).

## Базовая сеть (основной путь)

Единственная используемая адресация в проекте:

- `192.168.10.0/24` — внутренняя LAN
- `central-gw` (4GB): `192.168.10.1`
- `door-1` (1GB): `192.168.10.11`
- `door-2` (1GB): `192.168.10.12`

## Двери (физическая нумерация)

Единый “канон” по соответствию `door_id ↔ hostname ↔ IP`:

- `Docs/настройка ПО/План/0. Паспорт дверей (door_id ↔ hostname ↔ IP).md`

## Что читать и в каком порядке

0. Индекс проекта (архитектура/модули/операции/проблемы): `Docs/Проект/INDEX.md`
0.1. Архитектура документации и правила изменений: `Docs/Проект/Документация (архитектура и правила).md`
0.2. Паспорт текущего релиза документации: `Docs/Проект/Паспорт релиза документации.md`
1. План “с нуля до работающей системы”: `Docs/настройка ПО/План/с нуля до работающей системы.md`
2. Сеть и роли (статические IP, firewall, DNS, hostname): `Docs/настройка ПО/План/2. Сетевые адреса и роли.md`
2.1. (Опционально) Резервный канал Door↔Central по Wi‑Fi: `Docs/настройка ПО/План/2.1. Резервный канал Door↔Central по Wi‑Fi.md`
3. Время (критично для данных): `Docs/настройка ПО/План/3. Синхронизация времени (критично для данных).md`
4. Backend сервер (Ubuntu + Docker Compose): `Docs/настройка ПО/План/4. Backend сервер (Ubuntu + Docker Compose).md`
5. Если SSH недоступен / не получается зайти: `Docs/настройка ПО/Обязательно.md` и `Docs/настройка ПО/0 - базовая настройка ОС/2 - Первый запуск/Доп шаг если обычный SSH не работает..md`
6. (Опционально) `sudo` без пароля для автоматизации: `Docs/настройка ПО/План/1.3 Passwordless sudo (опционально).md`
7. Масштабирование 100–200 систем (реестр + шаблоны): `Docs/настройка ПО/План/11. Масштабирование 100-200 систем (реестр и шаблоны).md`
8. Этап связи и внедрения модулей (камера/GPS/RTC/LTE): `Docs/настройка ПО/План/12. Связь Edge-Central-Server (этап внедрения модулей).md`

Стандарт подключения модулей:

- `Docs/Проект/Стандарт интеграции модулей v1.md`

## Автопроверка базовой конфигурации (PC + Central)

Скрипт собирает текущее состояние ПК (Ethernet) и `central-gw` по SSH и генерирует отчёт в `Docs/auto/`:

```bash
python3 scripts/opizero_baseline.py --host 192.168.10.1 --user orangepi
```

Результат:

- `Docs/auto/baseline-summary.md`
- `Docs/auto/baseline-pc.md`
- `Docs/auto/baseline-central-gw.md`

## Авто‑инвентаризация всех OPi

```bash
python3 scripts/opizero_inventory.py --user orangepi 192.168.10.1 192.168.10.11 192.168.10.12
```

Результат: `Docs/auto/inventory/INDEX.md`.

## Прошивка и офлайн‑настройка door‑1 / door‑2

Скрипт для прошивки microSD и офлайн‑настройки сети `192.168.10.0/24` + SSH:

- `scripts/flash_opizero3_sd.sh`
- Док: `Docs/настройка ПО/0 - базовая настройка ОС/1 - Загрузка ОС на Флеш карту/2 - Быстрая прошивка SD и офлайн настройка door-1 door-2 (LAN+SSH).md`

## Масштабирование и быстрый rollout

- Реестр систем: `fleet/registry.csv`
- Инструмент валидации/генерации bundle: `scripts/fleet_registry.py`
- Применение WG peer на сервере: `scripts/fleet_apply_wg_peer.py`
- Применение env шаблона на central: `scripts/fleet_apply_central_env.py`
- Оркестратор rollout: `scripts/fleet_rollout.sh`
- Commissioning отчёт системы: `scripts/fleet_commission.py`
- Транспортный тест 12.1 (обрыв Edge→Central): `scripts/test_edge_central_resilience.sh`
- Транспортный тест 12.2 (обрыв Central→Server/WG): `scripts/test_central_server_resilience.sh`
- Масштабный dry-run реестра (до 100–200 систем): `scripts/fleet_scale_dry_run.py`
- Шаблон пакета `sys-0002..sys-0020`: `scripts/fleet_batch_template.py` + `fleet/templates/`
- Per-system API keys (ensure/rotate/revoke/sync): `scripts/fleet_api_keys.py`
- Бэкапы БД сервера + restore-check: `scripts/install_server_db_backup.sh`, `scripts/server_db_restore_check.sh`
- Hardening публичной админки: `scripts/install_server_admin_hardening.sh`
- Деплой для произвольного комплекта: `scripts/deploy_passengers_mvp.sh --help`

## Камера: интерактивное меню режимов

Для удобного переключения режимов камеры и открытия видео/health в браузере:

```bash
./scripts/camera_mode_menu.sh --camera-ip 192.168.10.11 --user orangepi --debug-port 8091
```

Документация по шагам: `Docs/Проект/Операции/Камера OAK-D Lite (Luxonis).md`.

Depth baseline для OAK-D Lite:

- head/shoulders depth-gate: `0.40–1.50 м`;
- настраивается через `CAM_DEPTH_*` в `/etc/passengers/passengers.env`.

Дополнительно доступен отдельный режим `depth-counting` (transport strict):

- `person + track_id + две линии A/B`;
- учитывается только полное пересечение линии (in/out), с `depth-gate` для снижения ложных;
- web-диагностика: `http://127.0.0.1:8091/` и `http://127.0.0.1:8091/health`.

- переключение: `./scripts/camera_mode_switch.sh --mode depth-counting --camera-ip 192.168.10.11 --user orangepi`
- через интерактивное меню: пункты `5`/`6` в `./scripts/camera_mode_menu.sh`

Быстрая калибровка `depth-counting`:

- helper: `./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --show --health`
- стартовый пресет: `./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset wide-scan --health`
- профиль “меньше ложных” (транспорт, старт с FPS=10): `./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset transport-strict --health`
- профиль commissioning/debug без depth-gate: `./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset commissioning-no-depth --health`
- профиль commissioning c depth-gate (мягкий): `./scripts/camera_depth_calibrate.sh --camera-ip 192.168.10.11 --user orangepi --preset commissioning-depth-soft --health`
- live root-cause probe: `./scripts/camera_depth_live_probe.sh --camera-ip 192.168.10.11 --user orangepi --seconds 60 --out /tmp/door1-live.jsonl`
- через меню: пункты `16` (calibration helper) и `17` (5x health snapshot).

IMU-диагностика в `depth-counting`:

- в `http://127.0.0.1:8091/health` доступны `imu_*` поля (acc/gyro);
- управление через env: `CAM_IMU_ENABLE`, `CAM_IMU_RATE_HZ`.
