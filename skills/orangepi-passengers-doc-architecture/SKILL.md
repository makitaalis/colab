---
name: orangepi-passengers-doc-architecture
description: Documentation information architecture and governance workflow for OrangePi_passangers. Use when restructuring docs modules, defining canonical layers, enforcing update DoD, and keeping navigation consistent while the project scales.
---

# OrangePi Passengers Doc Architecture

## Canon

- Docs index: `Docs/Проект/INDEX.md`
- Doc architecture rules: `Docs/Проект/Документация (архитектура и правила).md`
- Skill catalog: `Docs/Проект/Скиллы Codex.md`

## Workflow

1) Assess current docs map:

```bash
find Docs/Проект -maxdepth 2 -type f | sort
```

2) Keep layered architecture (`L0`..`L4`) and avoid role mixing:

- `L0`: canon (`door_id`, network, time);
- `L1`: architecture/contracts;
- `L2`: operations/config/troubleshooting;
- `L3`: governance/prompts/skills;
- `L4`: generated reports in `Docs/auto/`.

3) Apply modular split rules:

- one document = one primary responsibility;
- if a section exceeds its role, split to a dedicated file;
- always add links in `Docs/Проект/INDEX.md`.

4) Sync rules after changes:

- update index links;
- update `Docs/Проект/Скиллы Codex.md` if new workflow skill is added;
- ensure terms stay canonical (`door_id`, hostname, `system_id`, `central_id`).

5) Validate navigation:

```bash
rg -n "Документация \\(архитектура и правила\\)|Шаблон документа модуля|Скиллы Codex" Docs/Проект/INDEX.md README.md
```

## Constraints

- Do not duplicate canonical tables outside canon files.
- Do not silently rename transport/system identifiers.
- Keep practical commands in `Docs/Проект/Операции.md`; keep concepts in architecture docs.

## Mandatory Stage Rule

- Documentation sync is mandatory after each change; stage is not done until docs are updated.
- End every stage with explicit "next step + purpose" statement.
