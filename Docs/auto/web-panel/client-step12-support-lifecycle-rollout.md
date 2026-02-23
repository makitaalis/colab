# Client Step-12 Support Lifecycle Rollout

- generated_at_utc: `2026-02-16T15:50:08Z`
- server: `207.180.213.225`
- lifecycle scope: `rotate -> disable -> revoke` without downtime for active support actor

## Tooling Added

- lifecycle script: `scripts/client_support_lifecycle_rollout.sh`

## Controlled Scenario

1. Temporary actor onboarding for lifecycle validation:
- `support-sys-0099` added via matrix rollout
- matrix: `Docs/auto/web-panel/client-step12-lifecycle-matrix.txt`

2. Rotation:
- `support-sys-0099` password rotated using `client_support_lifecycle_rollout.sh --action rotate`
- old password returned `401` after rotation

3. Disable:
- `client_support_lifecycle_rollout.sh --action disable --actor support-sys-0099`
- actor removed from `CLIENT_SUPPORT_USERS` and client htpasswd
- actor client/admin API access => `401/401`

4. Revoke:
- `client_support_lifecycle_rollout.sh --action revoke --actor support-sys-0099`
- actor bindings removed from `CLIENT_SCOPE_BINDINGS`
- actor client/admin API access => `401/401`

## Final Server State

- `CLIENT_SUPPORT_USERS=support-sys-0001`
- `CLIENT_SCOPE_BINDINGS=support-sys-0001:sys-0001`
- client auth users: `admin,support-sys-0001`

## Verification

- `./scripts/client_support_matrix_rollout.sh --matrix-file Docs/auto/web-panel/client-step12-lifecycle-matrix.txt ...` => `PASS`
- `./scripts/client_support_lifecycle_rollout.sh --action rotate ...` => `PASS`
- `./scripts/client_support_lifecycle_rollout.sh --action disable ...` => `PASS`
- `./scripts/client_support_lifecycle_rollout.sh --action revoke ...` => `PASS`
- `./scripts/client_panel_regression_check.sh --admin-user support-sys-0001 ...` => `PASS`
- `python3 scripts/client_panel_step7b_audit.py --admin-user support-sys-0001 --write Docs/auto/web-panel/client-step7b-ux-audit-support-sys-0001-step12.md` => `PASS`
- `./scripts/server_security_posture_check.sh ...` => `PASS`

## Runtime Snapshot

- `admin -> /api/client/whoami` => `role=client`
- `support-sys-0001 -> /api/client/whoami` => `role=admin-support`, `scope.central_ids=["sys-0001"]`
- `support-sys-0099 -> /api/client/whoami` => `401`
