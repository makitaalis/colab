# MVP и тесты связи

## Базовый E2E

```bash
./scripts/deploy_passengers_mvp.sh
ssh orangepi@192.168.10.11 'python3 /opt/passengers-mvp/enqueue_event.py --door-id 2 --in 1 --out 0'
ssh orangepi@192.168.10.1 'python3 /opt/passengers-mvp/central_flush.py --send-now'
```

## Тест устойчивости 12.1/12.2

```bash
./scripts/test_edge_central_resilience.sh
./scripts/test_central_server_resilience.sh
./scripts/test_central_server_controlled_offline.sh --duration-min 45
```

## Важно

- Пока нет камер и модулей: работаем в режиме `MVP baseline`.
- Эталон для production фиксируется после подключения камеры/GPS/RTC/LTE.

## Полный набор команд

- `Docs/Проект/Операции (подробно).md`
