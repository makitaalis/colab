# Module Template

Use this checklist when creating/changing admin modules.

## Contract

- `module_id`:
- UI route:
- API route(s):
- role behavior (`viewer/operator/admin`):
- dependencies (WG, incidents, notifications, policy):

## UI requirements

- filter bar (q/central/code/severity where relevant);
- status line (loading/error/ok summary);
- no white screen on partial API failures;
- link back to parent module (`/admin/fleet` or `/admin`).

## API requirements

- idempotent GETs for listing/summary;
- POST actions with audit trail;
- bounded `limit` and safe defaults.

## Validation

- `python3 -m py_compile backend/app/main.py`
- `curl` to new/changed API route(s)
- `curl -k -u ... https://127.0.0.1:8443/<route>` contains expected ids

## Documentation

- `Docs/Проект/INDEX.md`
- `Docs/Проект/Операции.md`
- `Docs/Проект/Проблемы.md` (if needed)
