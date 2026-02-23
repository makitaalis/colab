# Alerts Prompts

## Prompt: add grouped triage view

```text
Доработай /admin/fleet/alerts:
1) таблица групп по code;
2) в каждой группе кнопки ack/silence/unsilence для всех алертов этого code;
3) сохрани фильтры при action;
4) итог выполнения: success/failed.
```

## Prompt: harden bulk actions

```text
Усиль bulk-операции в alerts модуле:
- retries на временные 5xx;
- ограничение параллелизма;
- явный список ошибок по central_id/code;
- не блокировать UI при частичных сбоях.
```

## Prompt: incident-linked navigation

```text
Для каждой строки alerts добавь быстрый переход:
- на /admin/fleet/central/{central_id}
- на /admin/fleet/incidents/{central_id}/{code}
и проверь, что ссылки корректно экранируют central_id/code.
```
