# Monitor Prompts

## Refactor monitor composition

```text
Сделай phase рефакторинга monitor:
1) вынеси сбор snapshot в отдельный модуль;
2) оставь thin-wrapper в main.py;
3) не меняй API контракт monitor/health/notify-auto;
4) проверь dry-run notify-auto и state/attention/alerts ключи.
```

## Tune monitor attention

```text
Точно доработай attention-логику monitor без смены URL:
- уточни причины heartbeat/wg/pending;
- сохрани текущие пороги policy/overrides;
- покажи diff по state transitions (good/warn/bad).
```
