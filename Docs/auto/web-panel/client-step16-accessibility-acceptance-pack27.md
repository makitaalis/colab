# Client Step-16 Accessibility Acceptance

- generated_at_utc: `2026-02-17T21:35:22Z`
- base_url: `https://207.180.213.225:8443`
- actor: `support-sys-0001`

## Checks

| Check | Result | Details |
|---|---|---|
| `/client auth/anon` | `PASS` | auth=200 anon=401 |
| `/client/profile auth/anon` | `PASS` | auth=200 anon=401 |
| `/client/notifications auth/anon` | `PASS` | auth=200 anon=401 |
| `/api/client/whoami auth/anon` | `PASS` | auth=200 anon=401 |
| `/api/client/whoami role` | `PASS` | admin-support |
| `client shell a11y markers` | `PASS` | markers=11 |
| `profile copy markers` | `PASS` | markers=4 |
| `notifications copy markers` | `PASS` | markers=7 |

## Keyboard-Only Operator Scenario

1. Open any client page and press `/` -> toolbar search/input gets focus.
2. Press `Esc` in focused input -> focus leaves editable field.
3. Press `Alt+Shift+M` -> sidebar compact mode toggles.
4. Press `Alt+Shift+K` -> table columns toggle switches base/detailed mode.
5. Press `Alt+Shift+S` -> focus moves to active/first sidebar link.
6. Press `Alt+Shift+T` -> focus moves to primary toolbar action.

## Verdict

- status: `PASS`
