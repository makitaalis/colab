# Fleet Prompts

## UX hardening

```text
Доработай /admin/fleet по UX:
- ускорь triage (быстрые фильтры и focus presets);
- добавь/проверь compact density;
- исключи white-screen при ошибках API;
- сохрани текущий URL и API контракт.
```

## Refactor step

```text
Сделай phase рефакторинга fleet-overview:
1) вынеси HTML/JS route /admin/fleet в отдельный модуль;
2) оставь thin-wrapper в main.py;
3) не меняй поведение фильтров/таблиц;
4) проверь py_compile и smoke на VPS.
```
