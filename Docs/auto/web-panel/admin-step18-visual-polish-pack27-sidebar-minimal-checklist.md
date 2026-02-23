# Checklist — admin pack-27 (sidebar minimal)

- date: `2026-02-17`
- target: `admin sidebar`

## Manual UI checks

- `Simple` ON: sidebar содержит только навигацию (`раздел -> подменю`), mini-блоки не видны.
- `Розширено` ON: mini-блоки доступны и сворачиваемые, без “длинной простыни” по умолчанию.
- `Фокус` ON: sidebar nav-only (без jump-row/mini-блоков).
- Поиск в меню: результат не прячется в collapsed-группе, `Enter` открывает единственный найденный пункт.
- Нет визуального “скачка” страницы при переключении `Просто/Розширено` (advanced `<details>` не авто-раскрываются).

## Automated gates

- `scripts/admin_panel_smoke_gate.sh` — `PASS`
- `scripts/client_panel_step17_handoff_check.sh` — `PASS` (`Docs/auto/web-panel/client-step17-handoff-checklist-pack27b.md`)

