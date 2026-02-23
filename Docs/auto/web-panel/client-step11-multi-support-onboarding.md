# Client Step-11 Multi-Support Onboarding Rollout

- generated_at_utc: `2026-02-16T15:40:59Z`
- server: `207.180.213.225`
- matrix_file: `Docs/auto/web-panel/client-step11-support-matrix.txt`

## Applied Policy

- `CLIENT_SUPPORT_USERS=support-sys-0001`
- `CLIENT_SCOPE_BINDINGS=support-sys-0001:sys-0001`
- `client auth users=admin,support-sys-0001`

## Rollout Tooling

- Added script: `scripts/client_support_matrix_rollout.sh`
- Added matrix template: `Docs/Проект/Операции/client-support-onboarding-matrix.example`

## Verification

- `./scripts/client_support_matrix_rollout.sh --matrix-file Docs/auto/web-panel/client-step11-support-matrix.txt --admin-pass-file "pass admin panel"` => `RESULT: PASS`
- `./scripts/admin_panel_smoke_gate.sh ...` (inside rollout) => `PASS`
- `./scripts/client_panel_regression_check.sh --admin-pass-file "pass admin panel"` => `PASS`
- `./scripts/client_panel_regression_check.sh --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel"` => `PASS`
- `python3 scripts/client_panel_step7b_audit.py --admin-user support-sys-0001 --admin-pass-file "pass client support sys-0001 panel" --write Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001.md` => `PASS`
- `./scripts/server_security_posture_check.sh --server-host 207.180.213.225 --server-user alis --admin-user admin --admin-pass <secret>` => `PASS`

## Runtime Checks

- `support-sys-0001 -> /api/client/whoami` => `200`, `role=admin-support`, `scope.central_ids=["sys-0001"]`
- `support-sys-0001 -> /api/admin/whoami` => `401`
- `admin -> /api/client/whoami` => `role=client`
- `legacy support -> /api/client/whoami` => `401` (removed by matrix prune)

## Incident And Fix During Step-11

- first run returned temporary `502` immediately after API rebuild (warm-up race)
- fix: readiness retry added into `scripts/client_support_matrix_rollout.sh` before post-deploy validation
- rerun after fix => `PASS`
