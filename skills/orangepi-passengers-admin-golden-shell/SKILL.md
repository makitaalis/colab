---
name: orangepi-passengers-admin-golden-shell
description: Golden UI/UX shell workflow for OrangePi_passangers admin pages. Use when standardizing module layout, density behavior, table meta hints, and operator action rhythm without changing backend API contracts.
---

# OrangePi Passengers Admin Golden Shell

## Canon

- Module roadmap: `Docs/Проект/Админ-панель (модульная разработка).md`
- Ops checks: `Docs/Проект/Операции.md`
- Prompt pack: `Docs/Проект/Промпты Codex (админка).md`
- Toolkit base: `backend/app/admin_ui_kit.py`

## Workflow

1) Keep boundaries:

- UI-only changes in page modules + `admin_ui_kit.py`.
- No route/API/schema changes.
- Preserve existing DOM IDs/data-hooks.

2) Enforce golden shell blocks for each module page:

- `flow` route card (operator path);
- left sidebar navigation (`appShell/sideNav/sideLink`) with active route via `current_nav`;
- top toolbar with filters + refresh + role/status;
- density switch (`regular/compact`) via `window.AdminUiKit.initDensityMode(...)`;
- table metadata row (`tableMeta/metaChip`) with source/sort/mode;
- workspace context row (`workspaceHint` + apply/clear actions) for operator continuity;
- command/preset row (`cmdPaletteOpen` + `presetSelect`) for быстрых operator сценариев;
- portability row (`presetNamespace` + `presetExport/presetImport`) for team-wide preset exchange;
- governance row (`presetProfiles` + `presetCleanup`) for profile rollout and retention policy;
- observability row (`presetSummary` + `presetObservability` + `presetMetrics`) for namespace/scope visibility;
- timeline row (`presetTimelineHint` + `presetTimelineOpen` + `presetTimelineClear`) for preset audit/drill-down;
- merge guard row (`presetMergeHint` + `presetPreview` + guarded `presetImport`) for safe import flow;
- policy row (`presetPolicyHint` + `presetPolicyUnlock` + `presetPolicyLock`) for protected baseline presets;
- cockpit row (`presetCockpitHint` + `presetCockpit`) for batch scope operations and consolidated preview/apply;
- cockpit timeline row (`presetCockpitTimelineHint` + `presetCockpitTimeline`) for batch audit and fast drill-down;
- rollout row (`presetRolloutHint` + `presetRollout`) for safe массовое применение preset-пакетов;
- grouped left IA (`sideGroups/sideGroup/sideJumpRow`) for predictable operator navigation at scale;
- personalization row (`Quick Intents` + `Favorites` + `Recent`) for fast repeated operator routes;
- ergonomics row (collapsible groups + favorites reorder + intent hotkeys) for high-frequency operator sessions;
- command-hub row (inline intent-runner + hotkeys cheat-sheet + focus mode) for incident-first navigation rhythm;
- sidebar-intelligence row (adaptive intents + context hints + session shortcuts) for faster triage continuity;
- mission-control row (alert-first widgets + one-click triage presets + sticky incident focus) for rapid operator response;
- mission-automation row (guided playbooks + smart chaining + handoff notes) for repeatable аварийное восстановление;
- mission-evidence row (checklist badges + snapshots + handoff timeline) for verifiable response continuity;
- mission-response-pack row (pack generation + template copy + JSON review) for fast shift handoff;
- action chips/buttons with clear role behavior (`viewer/operator/admin`).

3) Centralize shared behavior in toolkit:

- CSS primitives live in `base_admin_css()`;
- JS primitives live in `base_admin_js()` (`density`, `debounce`, `enter refresh`, `clear filters`, `whoami`, `api*`).
- sticky-context + latency helpers must stay in toolkit (`save/load/clear/applyWorkspaceHint`, `runActionWithLatency`, `formatLatency`).
- command/preset helpers must stay in toolkit (`open/close/bindCommandPalette`, `list/save/get/deletePreset`).
- shared namespace and JSON helpers must stay in toolkit (`normalizePresetNamespace`, `export/importPresets`, `export/importPresetBundle`).
- governance helpers must stay in toolkit (`presetProfileTemplates`, `installPresetProfiles`, `cleanupPresets`, `listPresetArchive`).
- observability helpers must stay in toolkit (`buildPresetScopeObservability`, `buildPresetObservabilityBundle`).
- timeline helpers must stay in toolkit (`listPresetTimeline`, `clearPresetTimeline`, `buildPresetTimelineSummary`, `buildPresetTimelineBundle`).
- merge-preview helpers must stay in toolkit (`simulatePresetImport`, `simulatePresetBundleImport`, `buildPresetMergePreview`).
- protection helpers must stay in toolkit (`getPresetProtectionState`, `setPresetProtectionLock`).
- cockpit helpers must stay in toolkit (`buildPresetOperationsSummary`, `simulatePresetOperations`, `applyPresetOperations`, `setPresetProtectionLockBatch`).
- cockpit timeline helpers must stay in toolkit (`buildPresetCockpitTimeline`, `openPresetCockpitTimelinePanel`, `closePresetCockpitTimelinePanel`).
- rollout helpers must stay in toolkit (`buildPresetRolloutAssistant`, `applyPresetRolloutAssistant`, `getPresetRolloutLast`).
- left IA helpers/styles must stay in toolkit (`sideGroups`, `sideJumpRow`, active trail classes), page modules only set `current_nav`.
- personalization helpers/styles must stay in toolkit (`load/storeSidebarFavorites`, `load/storeSidebarRecent`, `initSidebarPersonalization`).
- ergonomics helpers/styles must stay in toolkit (`load/storeSidebarCollapsedGroups`, `toggleSidebarGroup`, `bindSidebarQuickIntentHotkeys`).
- command-hub helpers/styles must stay in toolkit (`bindSidebarCommandHub`, `runQuickIntent`, `load/storeSidebarFocusMode`, `applySidebarFocusMode`).
- sidebar-intelligence helpers/styles must stay in toolkit (`buildAdaptiveSidebarIntents`, `buildSidebarContextHint`, `recordSidebarSessionShortcut`, `renderSidebarSessionShortcuts`).
- mission-control helpers/styles must stay in toolkit (`collectMissionMetrics`, `renderMissionWidgets`, `runMissionTriagePreset`, `runIncidentFocusAction`).
- mission-automation helpers/styles must stay in toolkit (`renderMissionPlaybooks`, `renderMissionChain`, `runMissionPlaybookStep`, `runMissionChainAction`, `renderMissionHandoffNotes`, `runMissionHandoffAction`).
- mission-evidence helpers/styles must stay in toolkit (`renderMissionChecklistSummary`, `runMissionSnapshotAction`, `renderMissionSnapshotSummary`, `renderMissionHandoffTimeline`, `runMissionHandoffHistoryAction`).
- mission-response-pack helpers/styles must stay in toolkit (`buildMissionResponsePack`, `buildMissionHandoffTemplate`, `runMissionResponsePackAction`, `renderMissionResponsePackSummary`).
- Page modules may only add page-specific logic.

4) Validate locally:

```bash
python3 -m py_compile backend/app/admin_ui_kit.py backend/app/main.py backend/app/admin_fleet_page.py backend/app/admin_fleet_alerts_page.py backend/app/admin_fleet_incidents_page.py
python3 -m compileall -q backend/app
bash -n scripts/admin_panel_smoke_gate.sh
```

5) Rollout + smoke on VPS:

```bash
rsync -av backend/app/admin_ui_kit.py backend/app/admin_fleet_page.py backend/app/admin_fleet_alerts_page.py backend/app/admin_fleet_incidents_page.py alis@207.180.213.225:/opt/passengers-backend/app/
ssh alis@207.180.213.225 'cd /opt/passengers-backend && sudo docker compose -f compose.yaml -f compose.server.yaml up -d --build api'
./scripts/admin_panel_smoke_gate.sh --server-host 207.180.213.225 --server-user alis --admin-user admin --admin-pass "<BASIC_AUTH_PASS>"
```

6) Sync docs:

- `Docs/Проект/Админ-панель (модульная разработка).md`
- `Docs/Проект/Операции.md`
- `Docs/Проект/Скиллы Codex.md`
- `Docs/Проект/Промпты Codex (админка).md` (if a new phase prompt was added)

7) Mandatory stage handoff:

- always state what was done in the current phase and why;
- always state the next phase, what will be done there, and why it is needed.
