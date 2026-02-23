# Checklist — pack-28 (chips без навигации)

- date: `2026-02-17`
- target: `admin+client`

## Manual UI checks

- Client: в header chips нет ссылок, только контекст (роль/описание/оновлено).
- Client: переходы между страницами доступны через sidebar и `clientSubnav`.
- Admin incident detail: “← інциденти” и “вузол” находятся в toolbar и ведут на корректные URL.
- Header визуально компактный: chips не “ломают” высоту header.

## Automated gates

- `scripts/admin_panel_smoke_gate.sh` — PASS
- `scripts/client_panel_step17_handoff_check.sh` — PASS (`Docs/auto/web-panel/client-step17-handoff-checklist-pack28b.md`)

