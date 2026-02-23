# Checklist — pack-32 (admin toolbar migrate)

- date: `2026-02-17`
- target: `admin header toolbar`

## Manual UI checks

- На всіх admin сторінках toolbar в header читається як 2 ряди: controls + meta/status.
- Inline `.toolbar` всередині сторінок (в cards/secondary blocks) не став “контейнером” і не додає зайвий бордер/фон.
- На incident detail `← інциденти` і `вузол` виглядають як кнопки (але це лінки).
- `copyLink` має єдиний розмір і не “стиснутий” через `smallbtn`.

## Automated gates

- `scripts/admin_panel_smoke_gate.sh` — PASS
- `scripts/client_panel_step17_handoff_check.sh` — PASS (`Docs/auto/web-panel/client-step17-handoff-checklist-pack32b.md`)

