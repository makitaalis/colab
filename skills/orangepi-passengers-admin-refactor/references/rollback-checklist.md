# Rollback Checklist

Use if deploy introduces regressions.

## Fast rollback

1) Restore previous `main.py` and extracted module files on server.
2) Rebuild api container.
3) Re-run smoke checks for impacted routes.

## Verify after rollback

- affected API returns previous schema;
- UI route no white screen;
- container logs clean.

## Record incident

- add root-cause and fix notes to `Docs/Проект/Проблемы.md`.
