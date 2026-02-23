# Edge (door узлы)

## Назначение

- Собирать события вход/выход по дверям.
- Локально буферизовать при недоступности Central.
- Догонять очередь после восстановления связи.

## MVP baseline (без камеры)

- Сервис: `passengers-edge-sender`.
- Очередь: `/var/lib/passengers/edge.sqlite3` (`outbox`).
- Гейт запуска: `preflight.py` (время синхронизировано + Central доступен).

## Контракт

- Отправка в Central: `POST /api/v1/edge/events`.
- Идентичность узла: `NODE_ID`, `DOOR_ID` в `/etc/passengers/passengers.env`.

## Связанные документы

- Протокол: `Docs/Проект/Протокол (Edge→Central).md`
- Конфигурация: `Docs/Проект/Конфигурация.md`
- Подробно: `Docs/Проект/Модули (подробно).md`
