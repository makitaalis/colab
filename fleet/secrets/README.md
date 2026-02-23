# Fleet secrets (local only)

Этот каталог хранит локальные секреты для управления системой:

- `system_api_keys.csv` — per-system ingest API keys (`system_id` → key).
- `admin_api_key.txt` — токен для backend admin API (через nginx proxy).

Файлы секретов игнорируются через `.gitignore`.
