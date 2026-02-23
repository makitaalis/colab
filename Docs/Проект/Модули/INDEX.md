# Модули — обзор и границы

## Слои

- `edge layer`: сбор событий по дверям и отправка на Central.
- `central layer`: приём, буферизация, агрегация, uplink на сервер.
- `server layer`: ingest, fleet-monitoring, incidents, policy, audit.
- `infra layer`: сеть, время, watchdog, backup, rollout-инструменты.

## Инварианты

- `system_id` и `central_id` должны совпадать (`sys-XXXX`).
- Внутренняя LAN: `192.168.10.0/24`.
- Источник времени для edge — Central.
- До подключения камер/GPS/RTC/LTE используется режим `MVP baseline`.

## Ссылки

- Edge: `Docs/Проект/Модули/Edge (door узлы).md`
- Central: `Docs/Проект/Модули/Central (шлюз).md`
- Backend: `Docs/Проект/Модули/Backend (API и админка).md`
- Infra: `Docs/Проект/Модули/Инфраструктура и инструменты.md`
