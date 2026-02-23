# Client Step-10 Scope Rollout

- date: `2026-02-16`
- server: `207.180.213.225`

## Target

- Включить per-support scope isolation через `CLIENT_SCOPE_BINDINGS`.

## Applied

- script:
  - `scripts/client_scope_rollout.sh`
- env:
  - `CLIENT_SCOPE_BINDINGS=support:sys-0001`

## Verification

- `/api/client/whoami` (support):
  - `role=admin-support`
  - `scope.central_ids=["sys-0001"]`
- `/api/client/vehicles?limit=20` (support):
  - `total=1` (виден только scoped central `sys-0001`)
- `/api/client/whoami` (admin):
  - `role=client`
  - scope defaults unchanged.
- checks:
  - `scripts/admin_panel_smoke_gate.sh` -> `PASS`
  - `scripts/client_panel_regression_check.sh --admin-user support ...` -> `PASS`
  - `scripts/client_panel_step7b_audit.py --admin-user support ...` -> `PASS`

## Notes

- rollback backup создан: `/opt/passengers-backend/.env.scope.20260216163153.bak`.
