# Client Step-9 Support Rollout

- date: `2026-02-16`
- server: `207.180.213.225`

## Target

- Ввести выделенный support-login без использования `admin` для support-сценариев.
- Разделить nginx auth-файлы для `admin` и `client` контуров.

## Applied

- nginx config:
  - `/client*` и `/api/client/*` -> `/etc/nginx/passengers-client.htpasswd`
  - `/admin*` и `/api/admin/*` -> `/etc/nginx/passengers-admin.htpasswd`
- support rollout:
  - login: `support`
  - `CLIENT_SUPPORT_USERS=support`
  - client htpasswd users: `admin,support`

## Verification

- `support`:
  - `/api/client/whoami` -> `200`, `role=admin-support`
  - `/api/admin/whoami` -> `401`
- `admin`:
  - `/api/client/whoami` -> `200`, `role=client`
- gates:
  - `scripts/admin_panel_smoke_gate.sh` -> `PASS`
  - `scripts/client_panel_regression_check.sh` (admin) -> `PASS`
  - `scripts/client_panel_regression_check.sh` (support) -> `PASS`
  - `scripts/client_panel_step7b_audit.py` (support) -> `PASS`

## Notes

- initial rollout attempt surfaced nginx permission issue on `/etc/nginx/passengers-client.htpasswd` (`13: Permission denied`);
- fixed by ownership `root:www-data` + mode `640`;
- fix baked into `scripts/client_support_rollout.sh`.
