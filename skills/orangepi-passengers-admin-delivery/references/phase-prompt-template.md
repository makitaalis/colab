# Phase Prompt Template

```text
Сделай phase-<N> модульной админки (<module_family>).
Ограничения:
1) не менять URL/API контракты;
2) сохранить роли viewer/operator/admin;
3) main.py оставить thin/composition-only.

Выполни:
1) вынеси/обнови код в backend/app/admin_*;
2) прогони локально py_compile + compileall;
3) выкатка на VPS в /opt/passengers-backend/app и rebuild api;
4) прогони scripts/admin_panel_smoke_gate.sh;
5) проверь изменённые endpoints отдельно;
6) проверь логи api на ResponseValidationError/Traceback/coroutine object;
7) обнови docs:
   - Docs/Проект/Админ-панель (модульная разработка).md
   - Docs/Проект/Операции.md
   - Docs/Проект/Промпты Codex (админка).md

Отчёт: список файлов, endpoint => status, итог PASS/FAIL, следующий phase.
```
