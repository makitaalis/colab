---
name: orangepi-passengers-admin-ui-toolkit
description: UI toolkit workflow for OrangePi_passangers admin panel pages. Use when extracting shared CSS/layout+JS helpers to admin_ui_kit.py, migrating page renderers to render_admin_shell(), and validating no API-contract regressions.
---

# OrangePi Passengers Admin UI Toolkit

## Canon

- Module roadmap: `Docs/Проект/Админ-панель (модульная разработка).md`
- Ops deploy checks: `Docs/Проект/Операции.md`
- Prompt pack: `Docs/Проект/Промпты Codex (админка).md`

## Workflow

1) Add/extend toolkit primitives in `backend/app/admin_ui_kit.py`:

- shared color tokens and table/toolbar/card styles;
- shared frontend helper `window.AdminUiKit` (`status`, `api*`, debounce, enter, clear-filters, whoami);
- `render_admin_shell(...)` layout wrapper;
- `render_legacy_admin_page(...)` wrapper for safe migration of legacy full-page renderers;
- `render_legacy_admin_page(...)` should auto-extract header/title/toolbar/body into shell mode when markup matches standard legacy pattern.
- keep API-independent UI helpers only.

2) Migrate target pages:

- replace duplicated `<style>`/layout with toolkit wrapper;
- for legacy pages without clean shell split, route them through `render_legacy_admin_page(...)` before full shell migration;
- for phase-18B full migration, convert heavy pages step-by-step in this order:
  - `admin_fleet_incident_detail_page.py` (done)
  - `admin_fleet_incidents_page.py` (done)
  - `admin_fleet_alerts_page.py` (done)
  - `admin_fleet_page.py` (done)
- after phase-18B completion, move to phase-19 cleanup:
  - keep `render_legacy_admin_page(...)` as fallback-only helper;
  - remove duplicated heavy-page CSS into shared toolkit primitives without changing API/UI contracts.
- after phase-19, run phase-20 UX polish:
  - improve focus/hover/readability states in `base_admin_css()`;
  - keep page modules API-neutral and preserve existing DOM IDs/hooks.
- after phase-20, run phase-21 operator workflow:
  - add explicit flow steps (fleet → alerts → incidents/actions → audit) on operator pages;
  - keep bulk/action handlers unchanged and style them via shared classes.
- after phase-21, run phase-22 operator UX rhythm:
  - align table density behavior across `fleet/alerts/incidents` via shared `initDensityMode(...)` helper;
  - expose source/sort/mode hints using shared `tableMeta/metaChip` primitives;
  - preserve existing DOM IDs/hooks and all backend API contracts.
- after phase-22, run phase-23 golden shell:
  - codify mandatory module shell blocks (flow + toolbar + tableMeta + density + action chips);
  - enforce these blocks as default for every new admin page module.
  - build shared left sidebar in toolkit (`appShell/sideNav/sideLink`) and set active item via `current_nav`.
- after phase-23, run phase-24 operator workspace refinement:
  - add sticky incident context helpers in toolkit (`save/load/clear/applyWorkspaceHint`);
  - expose action latency helpers (`runActionWithLatency`, `formatLatency`) for operator feedback;
  - wire workspace context + latency hints on `fleet/alerts/incidents/incident-detail` pages.
- after phase-24, run phase-25 command palette + presets:
  - add command palette helpers (`open/close/bindCommandPalette`) in toolkit;
  - add preset helpers (`list/save/get/delete`) with per-page scope in localStorage;
  - wire command/preset controls on `fleet/alerts/incidents` operator pages.
- after phase-25, run phase-26 cross-page portability:
  - add shared namespace support for presets (`local/shared`);
  - add JSON portability helpers (`export/importPresets`, `export/importPresetBundle`);
  - wire namespace switch + export/import controls on `fleet/alerts/incidents`.
- after phase-26, run phase-27 governance:
  - add profile templates and installer helpers (`presetProfileTemplates`, `installPresetProfiles`);
  - add retention/cleanup helpers with archive (`cleanupPresets`, `listPresetArchive`);
  - wire `Профілі/Cleanup` controls and palette commands on `fleet/alerts/incidents`.
- after phase-27, run phase-28 presets observability:
  - add scope-level observability helpers (`buildPresetScopeObservability`, `buildPresetObservabilityBundle`);
  - expose `local/shared/total/archived + last cleanup` metrics per scope;
  - wire `presetObservability` hint + `Метрики` control on `fleet/alerts/incidents`.
- after phase-28, run phase-29 presets timeline audit:
  - add timeline helpers (`listPresetTimeline`, `clearPresetTimeline`, `buildPresetTimelineSummary`, `buildPresetTimelineBundle`);
  - log preset lifecycle actions (`save/delete/import/export/install/cleanup`) into scope/namespace audit trail;
  - wire `presetTimelineHint` + `Журнал/Очистити журнал` controls and palette drill-down on `fleet/alerts/incidents`.
- after phase-29, run phase-30 conflict guard:
  - add merge preview helpers (`simulatePresetImport`, `simulatePresetBundleImport`, `buildPresetMergePreview`);
  - compare incoming/current presets by `name + ts + payload hash` in `merge/replace` modes;
  - wire `presetMergeHint` + `Preview` control and palette commands (`Preview merge`, `Імпорт merge`, `Імпорт replace`) on `fleet/alerts/incidents`.
- after phase-30, run phase-31 policy lock:
  - add protection helpers (`getPresetProtectionState`, `setPresetProtectionLock`) with protected registry from profile templates;
  - block delete/overwrite/import-conflict for protected presets while lock is enabled;
  - wire `presetPolicyHint` + `Unlock/Lock` controls and palette commands (`Policy unlock`, `Policy lock`) on `fleet/alerts/incidents`.
- after phase-31, run phase-32 presets operations cockpit:
  - add batch helpers (`buildPresetOperationsSummary`, `simulatePresetOperations`, `applyPresetOperations`, `setPresetProtectionLockBatch`);
  - wire `presetCockpitHint` + `presetCockpit` control on `fleet/alerts/incidents`;
  - add palette commands for cockpit batch flow (`preview/apply merge/apply replace/policy lock/policy unlock`).
- after phase-32, run phase-33 cockpit timeline panel:
  - add timeline aggregator helper (`buildPresetCockpitTimeline`) and panel helpers (`openPresetCockpitTimelinePanel`, `closePresetCockpitTimelinePanel`);
  - wire `presetCockpitTimelineHint` + `presetCockpitTimeline` control on `fleet/alerts/incidents`;
  - add palette command `Cockpit timeline panel` and keep drill-down JSON for every batch entry.
- after phase-33, run phase-34 rollout assistant:
  - add rollout helpers (`buildPresetRolloutAssistant`, `applyPresetRolloutAssistant`, `getPresetRolloutLast`);
  - wire `presetRolloutHint` + `presetRollout` control on `fleet/alerts/incidents`;
  - add safe apply flow (`dry-run -> rollback bundle -> checklist confirm -> apply`) and palette commands (`Rollout assistant`, `Rollout last summary`).
- after phase-34, run phase-35 left navigation IA hardening:
  - group sidebar into `Operations/Monitoring/Governance` with workflow jump-links;
  - keep active route + trail state for `fleet/alerts/incidents/audit`;
  - add compact jump-links in flow cards for fast operator transitions.
- after phase-35, run phase-36 navigation personalization:
  - add sidebar personalization sections (`Quick Intents`, `Favorites`, `Recent`);
  - keep favorites/recent state in localStorage and render with pin-toggle controls;
  - ensure quick-intent deep-links are reflected in page filter state (`alerts?sev=bad`).
- after phase-36, run phase-37 left-nav ergonomics hardening:
  - add collapsible side groups (`Operations/Monitoring/Governance`) with persisted state in localStorage;
  - add favorites reorder controls (`up/down/remove`) directly in sidebar;
  - add quick-intent hotkeys and keep them route-safe (`alerts bad`, `incidents open`, `audit`).
- after phase-37, run phase-38 left-nav command hub:
  - add inline command hub block with intent-runner buttons in sidebar;
  - add visual hotkeys cheat-sheet for intent discoverability;
  - add persisted sidebar focus mode (`standard/focus`) without breaking navigation.
- after phase-38, run phase-39 sidebar intelligence:
  - add adaptive ordering for quick-intents and command-hub actions based on context/recent/favorites/session;
  - add context-aware sidebar hints from current route/query state;
  - add session shortcuts block for last operator transitions/actions.
- after phase-39, run phase-40 sidebar mission-control:
  - add alert-first sidebar widgets based on existing page counters (UI-only);
  - add one-click triage preset buttons for critical/open/sla/queue scenarios;
  - add sticky incident focus block bound to shared workspace context (detail/list/pin/clear).
- after phase-40, run phase-41 mission-control automation:
  - add guided recovery playbooks in sidebar mission-control (step-by-step runbooks);
  - add smart triage chaining with recommended next step after preset/route detection;
  - add operator handoff notes (save/context/clear) with local persistence for shift transfer.
- after phase-41, run phase-42 mission-control evidence loop:
  - add checklist completion badges for runbook progress visibility;
  - add quick evidence snapshots (`capture/show/clear`) with local postmortem history;
  - add handoff timeline/history for `save/context/clear/snapshot` operator events.
- after phase-42, run phase-43 mission-control response packs:
  - add response-pack actions (`generate/copy-template/export-json/clear`) in mission-control;
  - add handoff template generator based on snapshot/checklist/timeline context;
  - add quick review/copy flow for shift handoff without backend API changes.
- after phase-43, run phase-44 mission-control escalation routing:
  - add rule-based routing profiles for response-pack by `severity/status/code/path`;
  - add channel-ready templates (`short/full/audit`) and profile/template selectors in mission-control;
  - add dispatch review/copy actions (`apply-routing/auto-route/copy-route`) without backend API changes.
- after phase-44, run phase-45 mission-control delivery adapters:
  - add channel adapters presets (`telegram/email/ticket`) on top of routing profile output;
  - add payload preview variants per channel for handoff-to-delivery continuity;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-45, run phase-46 mission-control delivery state handoff:
  - add delivery journal (copy/apply events, adapter/variant/timestamp) for operator shift continuity;
  - add queue-ready handoff status summary in sidebar mission-control without backend schema changes;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-46, run phase-47 mission-control delivery acknowledgment loop:
  - add explicit delivery lifecycle actions (`ack`, `retry`, `escalate`) on top of queue-ready state;
  - add SLA-state badges/timers to reduce handoff ambiguity between operators;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-47, run phase-48 mission-control delivery state automation:
  - add policy-ready action suggestions (`ack/retry/escalate`) based on SLA + recent journal history;
  - add bulk-friendly action shortcuts for faster triage on repeated incidents;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-48, run phase-49 mission-control delivery policy profiles:
  - add switchable policy profiles (`balanced/aggressive/conservative`) for suggestion tuning;
  - add session-level operator override for profile choice without backend writes;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-49, run phase-50 mission-control UX refinement:
  - add keyboard-first shortcuts and clearer action hierarchy for delivery operations;
  - add tooltip/microcopy confirmation hints for high-risk actions (retry/escalate/bulk);
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-50, run phase-51 mission-control navigation ergonomics:
  - improve left navigation for scale (`search/pin/compact`) in the same modular shell;
  - optimize mobile fallback for mission-control action density without changing API/schema;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-51, run phase-52 mission-control navigation accessibility polish:
  - add keyboard/ARIA-friendly navigation flow for `search/filter/compact` controls;
  - add onboarding hints for new operators to reduce time-to-first-effective-action;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-52, run phase-53 mission-control operator adoption telemetry:
  - add local UI telemetry summary for nav-search/hotkeys/compact usage;
  - add handoff-friendly adoption snapshot to monitor operator onboarding quality;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-53, run phase-54 mission-control operator coaching loop:
  - add actionable coaching hints based on telemetry gaps in nav-flow usage;
  - add handoff utilities (`reset/export adoption snapshot`) for shift governance;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-54, run phase-55 mission-control coaching cadence scoreboard:
  - add compact scoreboard (`pass/warn`) for core adoption practices per shift;
  - add explicit handoff next-actions (what must be trained next shift and why);
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-55, run phase-56 mission-control coaching trendline history:
  - add short history of scorecards across shifts with delta signal (`improving/stable/regressing`);
  - add quick trend hint for handoff decisions (where coaching effort should go next);
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-56, run phase-57 mission-control coaching reset-pack:
  - add handoff tools to `show/export/clear` trendline history for controlled reset cycles;
  - add confirm guardrails and status hints to avoid accidental history loss;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-57, run phase-58 mission-control coaching trend presets:
  - add fast trend-window presets (`last 3/5/10 saves`) for operator review;
  - add compact compare summary (`now vs baseline`) for shift handoff clarity;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-58, run phase-59 mission-control coaching decision cues:
  - add trend coaching helper with explicit next-step guidance (`improving/stable/regressing`);
  - render coaching cue in handoff and include it in trend JSON/export payload;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-59, run phase-60 mission-control coaching handoff composer:
  - add generated handoff template from `scorecard + trend + trend_coach + next_actions`;
  - add copy/apply controls for fast shift transfer without free-form drift;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-60, run phase-61 mission-control handoff quality guard:
  - add readiness checks for composer-based handoff completeness (`ready/not-ready` + missing items list);
  - add visual quality badges before operator runs `save handoff`;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- after phase-61, run phase-62 mission-control handoff quality profiles:
  - add quality policy profiles (`strict/balanced`) with session persistence;
  - reflect active policy in quality summary and quality timeline events;
  - keep route/API contracts unchanged and preserve existing DOM hooks.
- keep route path unchanged;
- keep JS fetch endpoints and payload contracts unchanged.

3) Apply UX minimum for filter-heavy pages:

- `Скинути фільтри` button;
- text input debounce (`~250-300ms`);
- Enter key for immediate refresh.
- bind these patterns through shared helper methods, not local copy-paste functions.

4) Validation:

```bash
python3 -m py_compile backend/app/admin_ui_kit.py backend/app/<page_module>.py backend/app/main.py
python3 -m compileall -q backend/app
bash -n scripts/admin_panel_smoke_gate.sh
```

5) VPS rollout and smoke:

- copy files to `/opt/passengers-backend/app`;
- `docker compose -f compose.yaml -f compose.server.yaml up -d --build api`;
- run `scripts/admin_panel_smoke_gate.sh` (with default strict module guard);
- verify page markers with curl/grep.

6) Mandatory stage handoff:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.

## References

- toolkit migration checklist: `references/toolkit-migration-checklist.md`

- after phase-62, run phase-63 mission-control handoff remediation assistant:
  - add one-click remediation actions for missing handoff quality items;
  - add explainability hints for blocked save and recommended first fix;
  - keep route/API contracts unchanged and preserve existing DOM hooks.

Mandatory reporting rule for every phase:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.

- after phase-63, run phase-64 mission-control handoff remediation telemetry:
  - add local remediation lifecycle metrics (`applied/skipped/override-after-remediation/time-to-ready`);
  - add compact KPI summary in handoff to evaluate remediation effect per shift;
  - keep route/API contracts unchanged and preserve existing DOM hooks.

Mandatory reporting rule for every phase:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.

- after phase-64, run phase-65 mission-control handoff remediation timeline drilldown:
  - add last-N remediation cycle timeline (status/action/ttr/override);
  - add JSON export for remediation KPI timeline analysis;
  - keep route/API contracts unchanged and preserve existing DOM hooks.

Mandatory reporting rule for every phase:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.

- after phase-65, run phase-66 mission-control handoff remediation governance pack:
  - add remediation KPI targets and compliance state (`ok/warn`);
  - add guided next-actions for target violations;
  - keep route/API contracts unchanged and preserve existing DOM hooks.

Mandatory reporting rule for every phase:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.

- after phase-66, run phase-67 mission-control handoff remediation governance incidents:
  - add local governance incident feed for remediation WARN cases;
  - add ack/snooze actions with incident trace in handoff timeline;
  - keep route/API contracts unchanged and preserve existing DOM hooks.

Mandatory reporting rule for every phase:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.


- after phase-67, run phase-68 mission-control handoff remediation incidents operations panel:
  - add incidents operations actions (`show/export/clear`) for governance feed;
  - add compact incidents SLA summary (`active/snoozed/acked`, oldest age);
  - trace incidents operations in handoff timeline;
  - keep route/API contracts unchanged and preserve existing DOM hooks.


- after phase-68, run phase-69 mission-control handoff remediation incidents digest board:
  - add incidents digest board for top fingerprints (`count/age/last-state`);
  - add guided triage hints for repeated WARN patterns;
  - keep route/API contracts unchanged and preserve existing DOM hooks.


- after phase-69, run phase-70 mission-control handoff remediation digest action planner:
  - add suggested-action planner per top digest fingerprint;
  - add handoff-ready action plan generation/export from digest context;
  - keep route/API contracts unchanged and preserve existing DOM hooks.


- after phase-70, run phase-71 mission-control remediation planner decision ledger:
  - add decision ledger (`show/export/clear`) for planner action outcomes;
  - add decision coverage summary (planned vs logged) for shift execution control;
  - keep route/API contracts unchanged and preserve existing DOM hooks.


- after phase-71, run phase-72 mission-control remediation decision backlog cockpit:
  - add coverage-gap backlog panel (`missing decisions`) with show/export/copy;
  - add handoff-ready summary for unresolved planner decisions;
  - keep route/API contracts unchanged and preserve existing DOM hooks.


- after phase-72, run phase-73 mission-control remediation decision backlog closeout assistant:
  - add quick closeout actions (`ack/snooze/profile-check`) directly from backlog missing-items;
  - add batch closeout flow for top-missing decisions in handoff shift;
  - keep route/API contracts unchanged and preserve existing DOM hooks.


- after phase-73, run phase-74 mission-control remediation decision closeout governance board:
  - add closeout KPI board (`single/batch`, decision-type counters, remaining gap);
  - add closeout governance show/export payload for shift handoff;
  - keep route/API contracts unchanged and preserve existing DOM hooks.


- after phase-74, run phase-75 mission-control remediation closeout escalation routing:
  - add escalation routing policy for closeout governance (`status/remaining_gap` thresholds and operator actions);
  - add escalation payload actions (`show/export/copy`) and timeline traces for shift handoff;
  - keep route/API contracts unchanged and preserve existing DOM hooks.

Mandatory reporting rule for every phase:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.


- after phase-75, run phase-76 mission-control closeout escalation execution logbook:
  - add escalation execution journal with lifecycle actions (`ack/snooze/resolve`) and stale SLA-age tracking;
  - add execution payload actions (`show/export/copy`) and timeline traces for shift handoff;
  - keep route/API contracts unchanged and preserve existing DOM hooks.

Mandatory reporting rule for every phase:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.


- after phase-76, run phase-77 mission-control closeout escalation execution anomaly guard:
  - add anomaly detection on escalation execution logbook (`repeat snooze`, `long stale`, unresolved route drift);
  - add anomaly payload actions (`show/export/copy`) and recommended actions in mission-control;
  - keep route/API contracts unchanged and preserve existing DOM hooks.

Mandatory reporting rule for every phase:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.
