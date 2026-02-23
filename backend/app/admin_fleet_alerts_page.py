from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_alerts_page() -> str:
    chips_html = """
        
        <span class="chip" id="roleBadge">роль: —</span>
        <span class="chip">оперативний triage алертів</span>
      
"""
    toolbar_html = """
        <div class="toolbarMain">
          <input id="q" type="text" placeholder="пошук: вузол / транспорт / код / текст" />
          <label><input id="auto" type="checkbox" checked /> авто</label>
          <button id="clearFilters">Скинути фільтри</button>
          <button id="refresh" class="primary">Оновити</button>
          <button id="copyLink" title="Скопіювати поточне посилання (з урахуванням фільтрів)">Скопіювати посилання</button>
          <details class="toolbarDetails" data-advanced-details="1">
            <summary>Фільтри</summary>
            <div class="toolbarDetailsGrid">
              <input id="central" type="text" placeholder="вузол (точно)" />
              <input id="code" type="text" placeholder="код (точно)" />
              <select id="sev">
                <option value="all">усі рівні</option>
                <option value="bad">критичні</option>
                <option value="warn">попередження</option>
                <option value="good">справні</option>
              </select>
              <select id="density" title="щільність таблиць">
                <option value="regular" selected>Звичайна</option>
                <option value="compact">Компактна</option>
              </select>
              <label><input id="includeSilenced" type="checkbox" /> включити заглушені</label>
            </div>
          </details>
        </div>
        <div class="toolbarMeta">
          <span class="metaChip sort" id="filterSummary">фільтри: стандартні</span>
          <span class="status" id="status"></span>
        </div>
      
"""
    body_html = """
    <div class="card flowCard">
      <div class="flowTitle">Операторський маршрут</div>
      <div class="flowRow">
        <a class="flowStep" href="/admin/fleet">1. Моніторинг флоту</a>
        <span class="flowStep current">2. Оперативні алерти</span>
        <a class="flowStep" href="/admin/fleet/incidents?status=open&include_resolved=0">3. Інциденти та дії</a>
        <a class="flowStep" href="/admin/audit">4. Аудит і контроль</a>
      </div>
      <div class="flowHint">Після групових дій перевіряйте зміни у журналі дій і аудиті.</div>
      <div class="sectionTools" style="margin-top:8px;">
        <a class="quickLink" href="/admin/fleet">До моніторингу</a>
        <a class="quickLink" href="/admin/fleet/incidents?status=open&include_resolved=0">До інцидентів</a>
        <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
        <a class="quickLink" href="/admin/audit">Аудит</a>
      </div>
      <details class="advancedDetails" data-advanced-details="1">
        <summary>Розширені інструменти (контекст / пресети)</summary>
        <div class="workspaceBar">
          <span id="workspaceHint" class="workspaceHint empty">Контекст інциденту: —</span>
          <span id="presetSummary" class="workspaceHint empty">Пресети: —</span>
          <span id="presetObservability" class="workspaceHint empty">Область: —</span>
          <span id="presetTimelineHint" class="workspaceHint empty">Журнал: —</span>
          <span id="presetMergeHint" class="workspaceHint empty">Злиття: —</span>
          <span id="presetPolicyHint" class="workspaceHint empty">Політика: —</span>
          <span id="presetCockpitHint" class="workspaceHint empty">Cockpit: —</span>
          <span id="presetCockpitTimelineHint" class="workspaceHint empty">Журнал кокпіта: —</span>
          <span id="presetRolloutHint" class="workspaceHint empty">Розгортання: —</span>
          <button id="workspaceApply" class="smallbtn">Підставити контекст</button>
          <button id="workspaceClear" class="smallbtn">Очистити контекст</button>
          <button id="cmdPaletteOpen" class="smallbtn">Команди</button>
          <select id="presetNamespace" title="простір пресетів">
            <option value="local" selected>локальні</option>
            <option value="shared">спільні</option>
          </select>
          <select id="presetSelect" title="збережені пресети">
            <option value="">пресети алертів</option>
          </select>
          <button id="presetSave" class="smallbtn">Зберегти</button>
          <button id="presetApply" class="smallbtn">Застосувати</button>
          <button id="presetDelete" class="smallbtn">Видалити</button>
          <button id="presetExport" class="smallbtn">Експорт</button>
          <button id="presetPreview" class="smallbtn">Попередній перегляд</button>
          <button id="presetImport" class="smallbtn">Імпорт</button>
          <button id="presetCockpit" class="smallbtn">Cockpit</button>
          <button id="presetCockpitTimeline" class="smallbtn">Журнал кокпіта</button>
          <button id="presetRollout" class="smallbtn">Розгортання</button>
          <button id="presetMetrics" class="smallbtn">Метрики</button>
          <button id="presetTimelineOpen" class="smallbtn">Журнал</button>
          <button id="presetTimelineClear" class="smallbtn">Очистити журнал</button>
          <button id="presetPolicyUnlock" class="smallbtn">Розблокувати</button>
          <button id="presetPolicyLock" class="smallbtn">Заблокувати</button>
          <button id="presetProfiles" class="smallbtn">Профілі</button>
          <button id="presetCleanup" class="smallbtn">Прибирання</button>
        </div>
      </details>
    </div>

    <div class="card">
      <div class="summary">
        <span class="badge" id="sumAlerts">алертів: 0</span>
        <span class="badge" id="sumGroups">груп кодів: 0</span>
        <span class="badge bad" id="sumBad">критичні: 0</span>
        <span class="badge warn" id="sumWarn">попередження: 0</span>
        <span class="badge good" id="sumGood">справні: 0</span>
        <span class="badge warn" id="sumSilenced">заглушені: 0</span>
      </div>
      <div class="tableMeta">
        <span class="metaChip source">джерела: <code>/api/admin/fleet/alerts</code> + <code>/api/admin/fleet/alerts/groups</code></span>
        <span class="metaChip sort">сортування: <code>severity ↓</code>, далі <code>age ↓</code></span>
        <span class="metaChip mode" id="densityBadge">щільність: Звичайна</span>
      </div>
    </div>

    <div class="card ops">
      <details id="alertsSecondaryDetails" class="domainSplitDetails" data-advanced-details="1">
        <summary>Групи алертів за кодом (secondary)</summary>
        <div class="domainSplitHint">Агрегація по коду для швидких групових дій. Primary контур нижче: оперативний список алертів.</div>
        <div class="sectionTools" style="margin-top:8px;">
          <a class="quickLink" href="/admin/fleet/incidents">Деталі інцидентів</a>
          <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
          <a class="quickLink" href="/admin/audit">Аудит</a>
        </div>
        <div class="tableWrap">
          <table id="grpTbl">
            <thead>
              <tr>
                <th>Пріоритет</th>
                <th>Код</th>
                <th>К-сть алертів</th>
                <th>Централей</th>
                <th>Заглушено</th>
                <th>Останній сигнал</th>
                <th>Дії по коду</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </details>
    </div>

	    <div class="card ops">
	      <div class="sectionHead">
	        <div class="sectionTitle">Оперативний список алертів</div>
	        <div class="sectionTools">
	          <span class="badge" id="selCount">обрано: 0</span>
	          <button id="bulkAck" class="smallbtn opAction opActionAck">Підтвердити обрані</button>
	          <button id="bulkSilence" class="smallbtn opAction opActionSilence">Пауза 1 год</button>
	          <button id="bulkUnsilence" class="smallbtn opAction opActionUnsilence">Зняти заглушення</button>
	          <button id="clearSel" class="smallbtn opAction">Очистити вибір</button>
	        </div>
	      </div>
      <div class="tableWrap">
        <table id="tbl">
          <thead>
            <tr>
              <th><input id="selAll" type="checkbox" /></th>
              <th>Рівень</th>
              <th>Вузол</th>
              <th>Транспорт</th>
              <th>Код</th>
              <th>Повідомлення</th>
              <th>Вік heartbeat</th>
              <th>Стан</th>
              <th>Дії</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
  
"""
    extra_css = """
    #q { min-width: 320px; }
    .toolbar input[type="text"] { min-width: 220px; }
    .toolbar select { min-width: 120px; }
    .summary { margin: 10px 0 2px; align-items:center; }
    .summary .badge { font-weight: 700; }
    .tableWrap { max-height: 66vh; margin-top: 10px; }
    .card .tableWrap { box-shadow: inset 0 1px 0 rgba(255,255,255,.03); }
    table { min-width: 1020px; }
    th, td { padding: 9px 9px; }
    .sectionHead { margin-bottom: 6px; }
    .sectionTools button.smallbtn { transition: transform .12s ease; }
    .sectionTools button.smallbtn:hover { transform: translateY(-1px); }
    .ops { margin-top: 14px; }
    body.density-compact th,
    body.density-compact td { padding: 6px 7px; }
    body.density-compact .smallbtn { padding: 4px 7px; font-size: 11px; }
    body.density-compact .tableWrap { max-height: 70vh; }
    #alertsSecondaryDetails .tableWrap { max-height: 56vh; }
  
""".strip()
    script = """
  const ui = window.AdminUiKit;
  const esc = ui.esc;
  let adminRole = "viewer";
  let adminCaps = { read: true, operate: false, admin: false };
  let currentAlerts = [];
  let selectedKeys = new Set();
  function fmtAge(sec) {
    if (sec === null || sec === undefined) return "—";
    if (sec < 0) return "—";
    if (sec < 5) return "щойно";
    const m = Math.floor(sec / 60);
    const h = Math.floor(m / 60);
    const d = Math.floor(h / 24);
    if (d > 0) return `${d}д ${h%24}г`;
    if (h > 0) return `${h}г ${m%60}хв`;
    return `${m}хв ${sec%60}с`;
  }
  function setStatus(text) { ui.setStatus("status", text); }
  function sevClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "good" || normalized === "warn" || normalized === "bad") return normalized;
    return "bad";
  }
  function sevLabel(value) {
    const normalized = sevClass(value);
    if (normalized === "good") return "СПРАВНО";
    if (normalized === "warn") return "ПОПЕРЕДЖЕННЯ";
    return "КРИТИЧНО";
  }
  function alertKey(item) {
    return `${String(item.central_id || "").toLowerCase()}::${String(item.code || "").toLowerCase()}`;
  }
  function canOperate() { return !!adminCaps.operate; }
  function query() { return (document.getElementById("q").value || "").trim().toLowerCase(); }
  function selectedCentral() { return (document.getElementById("central").value || "").trim(); }
  function selectedCode() { return (document.getElementById("code").value || "").trim(); }
  function selectedSeverity() { return (document.getElementById("sev").value || "all").toLowerCase(); }
  function includeSilenced() { return !!document.getElementById("includeSilenced").checked; }
  const PRESET_SCOPE = "fleet_alerts";
  const TEAM_PRESET_SCOPES = ["fleet", "fleet_alerts", "fleet_incidents"];
  let lastPresetImportRaw = "";
  let lastPresetPreview = null;
  let lastPresetCockpitRaw = "";
  let lastPresetCockpitPreview = null;
  let lastPresetCockpitScopes = [...TEAM_PRESET_SCOPES];
  let lastPresetRolloutPlan = null;
  const SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_alerts_secondary_details_v1";

  function loadSecondaryDetailsOpen() {
    try {
      const raw = String(localStorage.getItem(SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (!raw) return false;
      return raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {
      return false;
    }
  }
  function storeSecondaryDetailsOpen(open) {
    const value = open ? "1" : "0";
    try { localStorage.setItem(SECONDARY_DETAILS_STORAGE_KEY, value); } catch (_error) {}
    return value === "1";
  }
  function initSecondaryDetails() {
    const node = document.getElementById("alertsSecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    node.open = loadSecondaryDetailsOpen();
    node.addEventListener("toggle", () => {
      storeSecondaryDetailsOpen(node.open);
    });
  }
  const scheduleRefresh = ui.debounce(() => {
    syncQueryFromFilters();
    syncFilterSummary();
    refresh();
  }, 280);
  function syncDensityBadge(mode) {
    const label = ui.densityLabel(mode);
    document.getElementById("densityBadge").textContent = `щільність: ${label}`;
  }
  function rememberAlertContext(centralId, code, source) {
    const cleanCentral = String(centralId || "").trim();
    const cleanCode = String(code || "").trim();
    const label = cleanCentral && cleanCode ? `${cleanCentral}:${cleanCode}` : (cleanCentral || cleanCode || "");
    ui.saveWorkspaceContext({
      central_id: cleanCentral,
      code: cleanCode,
      source: source || "alerts",
      label,
    });
    refreshWorkspaceHint();
  }
  function refreshWorkspaceHint() {
    ui.applyWorkspaceHint("workspaceHint", { prefix: "Контекст інциденту", maxAgeSec: 3 * 24 * 3600 });
  }
  function collectPresetPayload() {
    return {
      q: document.getElementById("q").value || "",
      central: document.getElementById("central").value || "",
      code: document.getElementById("code").value || "",
      severity: document.getElementById("sev").value || "all",
      includeSilenced: !!document.getElementById("includeSilenced").checked,
    };
  }
  function selectedPresetNamespace() {
    return ui.normalizePresetNamespace(document.getElementById("presetNamespace").value || "local");
  }
  function formatTs(value) {
    const parsed = Date.parse(String(value || ""));
    if (!Number.isFinite(parsed)) return "—";
    return new Date(parsed).toLocaleString("uk-UA");
  }
  function timelineActionLabel(action) {
    const normalized = String(action || "").trim().toLowerCase();
    if (normalized === "save_preset") return "збереження";
    if (normalized === "delete_preset") return "видалення";
    if (normalized === "cleanup_presets") return "cleanup";
    if (normalized === "install_profiles") return "профілі";
    if (normalized === "import_presets") return "імпорт";
    if (normalized === "import_bundle") return "імпорт bundle";
    if (normalized === "export_presets") return "експорт";
    if (normalized === "export_bundle") return "експорт bundle";
    if (normalized === "policy_unlock") return "policy unlock";
    if (normalized === "policy_lock") return "блокування політики";
    if (normalized === "rollout_assistant_apply") return "rollout apply";
    return normalized || "подія";
  }
  function parsePresetPreview(raw, mode = "merge") {
    const namespace = selectedPresetNamespace();
    if (namespace === "shared") {
      return ui.simulatePresetBundleImport(raw, { namespace, mode, scopes: TEAM_PRESET_SCOPES });
    }
    return ui.simulatePresetImport(PRESET_SCOPE, raw, { namespace, mode });
  }
  function previewSummary(summary) {
    const source = summary && typeof summary === "object" ? summary : {};
    return `+${source.create || 0} ~${source.update || 0} ⟳${source.refresh_ts || 0} =${source.result_total || 0} !${source.conflicts || 0} -${source.drop || 0} lock=${source.protected_blocked || 0}`;
  }
  function previewPayloadForPrompt(preview) {
    const payload = preview && typeof preview === "object" ? { ...preview } : {};
    if (Array.isArray(payload.entries)) payload.entries = payload.entries.slice(0, 80);
    if (Array.isArray(payload.scopes)) {
      payload.scopes = payload.scopes.map((scope) => ({
        ...scope,
        entries: Array.isArray(scope && scope.entries) ? scope.entries.slice(0, 20) : [],
      }));
    }
    return payload;
  }
  function parseScopeList(raw) {
    const allowed = new Set(TEAM_PRESET_SCOPES.map((item) => String(item).toLowerCase()));
    const source = String(raw || "")
      .split(",")
      .map((item) => String(item || "").trim().toLowerCase())
      .filter((item) => !!item && allowed.has(item));
    return source.length > 0 ? Array.from(new Set(source.values())) : [...TEAM_PRESET_SCOPES];
  }
  function requestCockpitScopes() {
    const base = lastPresetCockpitScopes.length ? lastPresetCockpitScopes : TEAM_PRESET_SCOPES;
    const raw = String(window.prompt("Scopes для cockpit (через кому):", base.join(",")) || "").trim();
    const scopes = parseScopeList(raw);
    lastPresetCockpitScopes = scopes;
    return scopes;
  }
  function refreshPresetSummary() {
    const summaryNode = document.getElementById("presetSummary");
    const observabilityNode = document.getElementById("presetObservability");
    if (!summaryNode || !observabilityNode) return;
    try {
      const namespace = selectedPresetNamespace();
      const report = ui.buildPresetScopeObservability(PRESET_SCOPE);
      const activeTotal = namespace === "shared" ? report.shared_total : report.local_total;
      const activeArchived = namespace === "shared" ? report.shared_archived_total : report.local_archived_total;
      summaryNode.textContent = `Пресети(${namespace}): ${activeTotal} · архів=${activeArchived}`;
      summaryNode.classList.toggle("empty", activeTotal === 0 && activeArchived === 0);
      const localCleanup = report.local_last_cleanup_ts ? formatTs(report.local_last_cleanup_ts) : "—";
      const sharedCleanup = report.shared_last_cleanup_ts ? formatTs(report.shared_last_cleanup_ts) : "—";
      observabilityNode.textContent = `Scope ${PRESET_SCOPE}: total=${report.total} (L:${report.local_total}/S:${report.shared_total}) · архів=${report.archived_total} (L:${report.local_archived_total}/S:${report.shared_archived_total}) · cleanup L:${localCleanup} S:${sharedCleanup}`;
      observabilityNode.classList.toggle("empty", report.total === 0 && report.archived_total === 0 && !report.last_cleanup_ts);
    } catch (_error) {
      summaryNode.textContent = "Пресети: —";
      summaryNode.classList.add("empty");
      observabilityNode.textContent = "Область: —";
      observabilityNode.classList.add("empty");
    }
  }
  function refreshPresetMergeHint() {
    const node = document.getElementById("presetMergeHint");
    if (!node) return;
    const namespace = selectedPresetNamespace();
    if (!lastPresetPreview || String(lastPresetPreview.namespace || "") !== namespace) {
      node.textContent = "Злиття: —";
      node.classList.add("empty");
      return;
    }
    const mode = String(lastPresetPreview.mode || "merge");
    const summary = lastPresetPreview.summary || {};
    node.textContent = `Merge(${namespace}/${mode}): ${previewSummary(summary)}`;
    node.classList.toggle("empty", false);
  }
  function refreshPresetPolicyHint() {
    const node = document.getElementById("presetPolicyHint");
    if (!node) return;
    try {
      const namespace = selectedPresetNamespace();
      const state = ui.getPresetProtectionState(PRESET_SCOPE, { namespace });
      const lockText = state.locked ? "ЗАБЛОКОВАНО" : "РОЗБЛОКОВАНО";
      node.textContent = `Політика(${namespace}): ${lockText} · protected=${state.protected_total}`;
      node.classList.toggle("empty", false);
    } catch (_error) {
      node.textContent = "Політика: —";
      node.classList.add("empty");
    }
  }
  function refreshPresetCockpitHint() {
    const node = document.getElementById("presetCockpitHint");
    if (!node) return;
    const namespace = selectedPresetNamespace();
    if (lastPresetCockpitPreview && String(lastPresetCockpitPreview.namespace || "") === namespace) {
      const summary = lastPresetCockpitPreview.summary || {};
      node.textContent = `Cockpit(${namespace}): scopes=${summary.scope_count || 0} !${summary.conflicts || 0} lock=${summary.protected_blocked || 0} =${summary.result_total || 0}`;
      node.classList.toggle("empty", false);
      return;
    }
    try {
      const report = ui.buildPresetOperationsSummary({ namespace, scopes: lastPresetCockpitScopes });
      const summary = report.summary || {};
      node.textContent = `Cockpit(${namespace}): scopes=${summary.scope_count || 0} locked=${summary.locked_count || 0} presets=${summary.presets_total || 0}`;
      node.classList.toggle("empty", false);
    } catch (_error) {
      node.textContent = "Cockpit: —";
      node.classList.add("empty");
    }
  }
  function refreshPresetCockpitTimelineHint() {
    const node = document.getElementById("presetCockpitTimelineHint");
    if (!node) return;
    try {
      const namespace = selectedPresetNamespace();
      const report = ui.buildPresetCockpitTimeline({ namespace, scopes: lastPresetCockpitScopes, limit: 30 });
      const summary = report.summary || {};
      const lastTs = String(summary.last_ts || "");
      const lastAction = String(summary.last_action || "");
      node.textContent = `Cockpit журнал(${namespace}): ${summary.visible_total || 0} · остання: ${lastAction ? timelineActionLabel(lastAction) : "—"} · ${lastTs ? formatTs(lastTs) : "—"}`;
      node.classList.toggle("empty", Number(summary.visible_total || 0) === 0);
    } catch (_error) {
      node.textContent = "Журнал кокпіта: —";
      node.classList.add("empty");
    }
  }
  function openCockpitTimelineDetails(entry) {
    const payload = entry && typeof entry === "object" ? entry : {};
    window.prompt("Деталі таймлайну кокпіта (JSON):", JSON.stringify(payload, null, 2));
  }
  function showPresetCockpitTimelinePanel() {
    const namespace = selectedPresetNamespace();
    const scopes = lastPresetCockpitScopes.length ? lastPresetCockpitScopes : TEAM_PRESET_SCOPES;
    ui.openPresetCockpitTimelinePanel({
      title: "Cockpit журнал пресетів",
      namespace,
      scopes,
      limit: 120,
      onDrillDown: openCockpitTimelineDetails,
    });
    refreshPresetCockpitTimelineHint();
  }
  function rolloutPlanPayloadForPrompt(plan) {
    const source = plan && typeof plan === "object" ? plan : {};
    return {
      generated_at: String(source.generated_at || ""),
      namespace: String(source.namespace || ""),
      mode: String(source.mode || "merge"),
      scopes: Array.isArray(source.scopes) ? source.scopes : [],
      summary: source.summary && typeof source.summary === "object" ? source.summary : {},
      operations_summary: source.operations_summary && typeof source.operations_summary === "object" ? source.operations_summary : {},
      checklist: Array.isArray(source.checklist) ? source.checklist : [],
      postcheck: Array.isArray(source.postcheck) ? source.postcheck : [],
    };
  }
  function refreshPresetRolloutHint() {
    const node = document.getElementById("presetRolloutHint");
    if (!node) return;
    try {
      const namespace = selectedPresetNamespace();
      const last = ui.getPresetRolloutLast({ namespace });
      if (!last) {
        node.textContent = "Розгортання: —";
        node.classList.add("empty");
        return;
      }
      const resultSummary = last.summary && last.summary.result && typeof last.summary.result === "object" ? last.summary.result : {};
      node.textContent = `Розгортання(${namespace}): ${last.mode || "merge"} scopes=${(last.scopes || []).length} imported=${resultSummary.imported || 0} total=${resultSummary.total || 0} · ${last.ts ? formatTs(last.ts) : "—"}`;
      node.classList.toggle("empty", false);
    } catch (_error) {
      node.textContent = "Розгортання: —";
      node.classList.add("empty");
    }
  }
  function showLastPresetRolloutSummary() {
    const namespace = selectedPresetNamespace();
    const last = ui.getPresetRolloutLast({ namespace });
    if (!last) {
      setStatus(`Rollout summary відсутній (${namespace})`);
      refreshPresetRolloutHint();
      return;
    }
    window.prompt("Rollout last summary (JSON):", JSON.stringify(last, null, 2));
    refreshPresetRolloutHint();
  }
  function runPresetRolloutAssistant(defaultMode = "merge") {
    const namespace = selectedPresetNamespace();
    const scopes = requestCockpitScopes();
    const modeRaw = String(window.prompt("Режим розгортання (merge/replace):", defaultMode) || "").trim().toLowerCase();
    if (!modeRaw) return;
    const mode = modeRaw === "replace" ? "replace" : "merge";
    const raw = String(window.prompt(`JSON розгортання (${mode}):`, lastPresetCockpitRaw || lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const plan = ui.buildPresetRolloutAssistant(raw, { namespace, mode, scopes });
      lastPresetRolloutPlan = plan;
      lastPresetCockpitRaw = raw;
      window.prompt("Rollout dry-run plan (JSON):", JSON.stringify(rolloutPlanPayloadForPrompt(plan), null, 2));
      const rollbackBundle = String(plan.rollback_hint && plan.rollback_hint.bundle_json ? plan.rollback_hint.bundle_json : "");
      window.prompt("Rollback bundle JSON (збережіть до apply):", rollbackBundle);
      const checklistAck = String(window.prompt("Підтвердіть checklist: введіть CHECKLIST-OK", "") || "").trim().toUpperCase();
      if (checklistAck !== "CHECKLIST-OK") {
        setStatus(`Rollout ${mode} скасовано: checklist`);
        return;
      }
      const summary = plan.summary || {};
      const conflicts = Number(summary.conflicts || 0);
      const drops = Number(summary.drop || 0);
      const blocked = Number(summary.protected_blocked || 0);
      if (conflicts > 0 && !window.confirm(`Rollout: конфлікти=${conflicts}. Продовжити ${mode}?`)) {
        setStatus(`Rollout ${mode} скасовано: конфлікти=${conflicts}`);
        return;
      }
      if (mode === "replace" && drops > 0 && !window.confirm(`Rollout replace видалить ${drops} пресет(ів). Підтвердити?`)) {
        setStatus(`Rollout replace скасовано: drop=${drops}`);
        return;
      }
      let allowProtectedWrite = false;
      if (blocked > 0) {
        const phrase = String(window.prompt(`Rollout заблоковано policy (${blocked}). Введіть UNLOCK для продовження:`, "") || "").trim().toUpperCase();
        if (phrase !== "UNLOCK") {
          setStatus(`Rollout ${mode} скасовано: блокування політики`);
          return;
        }
        allowProtectedWrite = true;
      }
      const applyAck = String(window.prompt("Підтвердіть apply: введіть APPLY", "") || "").trim().toUpperCase();
      if (applyAck !== "APPLY") {
        setStatus(`Rollout ${mode} скасовано: apply`);
        return;
      }
      const result = ui.applyPresetRolloutAssistant(raw, { namespace, mode, scopes, allowProtectedWrite });
      loadPresetSelect("");
      const output = result && result.result && result.result.result && typeof result.result.result === "object"
        ? result.result.result
        : (result && result.result && typeof result.result === "object" ? result.result : {});
      setStatus(`Rollout ${mode}: imported=${output.imported || 0}, total=${output.total || 0}, scopes=${scopes.length}`);
      window.prompt("Rollout post-check (JSON):", JSON.stringify({ postcheck: plan.postcheck || [] }, null, 2));
      refreshPresetSummary();
      refreshPresetTimelineHint();
      refreshPresetMergeHint();
      refreshPresetPolicyHint();
      refreshPresetCockpitHint();
      refreshPresetCockpitTimelineHint();
      refreshPresetRolloutHint();
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Rollout заблоковано блокування політики (${namespace})`);
        refreshPresetPolicyHint();
      } else {
        setStatus(`ПОМИЛКА rollout assistant: ${error}`);
      }
    }
  }
  function previewPresetCockpit(mode = "merge") {
    const namespace = selectedPresetNamespace();
    const scopes = requestCockpitScopes();
    const raw = String(window.prompt(`JSON кокпіта (${mode}):`, lastPresetCockpitRaw || lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const preview = ui.simulatePresetOperations(raw, { namespace, mode, scopes });
      lastPresetCockpitRaw = raw;
      lastPresetCockpitPreview = preview;
      refreshPresetCockpitHint();
      window.prompt(`Попередній перегляд кокпіта ${mode} (JSON):`, JSON.stringify(previewPayloadForPrompt(preview), null, 2));
      setStatus(`Попередній перегляд кокпіта ${mode}: ${previewSummary(preview.summary || {})}`);
    } catch (error) {
      setStatus(`ПОМИЛКА cockpit preview: ${error}`);
    }
  }
  function applyPresetCockpit(mode = "merge") {
    const namespace = selectedPresetNamespace();
    const scopes = requestCockpitScopes();
    const raw = String(window.prompt(`Apply JSON кокпіта (${mode}):`, lastPresetCockpitRaw || lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const preview = ui.simulatePresetOperations(raw, { namespace, mode, scopes });
      lastPresetCockpitRaw = raw;
      lastPresetCockpitPreview = preview;
      refreshPresetCockpitHint();
      const summary = preview.summary || {};
      const conflicts = Number(summary.conflicts || 0);
      const drops = Number(summary.drop || 0);
      const blocked = Number(summary.protected_blocked || 0);
      if (conflicts > 0 && !window.confirm(`Cockpit: конфлікти=${conflicts}. Продовжити ${mode}?`)) {
        setStatus(`Cockpit ${mode} скасовано: конфлікти=${conflicts}`);
        return;
      }
      if (mode === "replace" && drops > 0 && !window.confirm(`Cockpit replace видалить ${drops} пресет(ів). Підтвердити?`)) {
        setStatus(`Cockpit replace скасовано: drop=${drops}`);
        return;
      }
      let allowProtectedWrite = false;
      if (blocked > 0) {
        const phrase = String(window.prompt(`Cockpit заблоковано policy (${blocked}). Введіть UNLOCK для продовження:`, "") || "").trim().toUpperCase();
        if (phrase !== "UNLOCK") {
          setStatus(`Cockpit ${mode} скасовано: блокування політики`);
          return;
        }
        allowProtectedWrite = true;
      }
      const result = ui.applyPresetOperations(raw, { namespace, mode, scopes, allowProtectedWrite });
      loadPresetSelect("");
      setStatus(`Cockpit ${mode}: imported=${result.result && result.result.imported ? result.result.imported : 0}, total=${result.result && result.result.total ? result.result.total : 0}, conflicts=${conflicts}, blocked=${blocked}`);
      refreshPresetSummary();
      refreshPresetTimelineHint();
      refreshPresetMergeHint();
      refreshPresetPolicyHint();
      refreshPresetCockpitHint();
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Cockpit заблоковано блокування політики (${namespace})`);
        refreshPresetPolicyHint();
      } else {
        setStatus(`ПОМИЛКА cockpit apply: ${error}`);
      }
    }
  }
  function setPresetCockpitLockBatch(locked) {
    const namespace = selectedPresetNamespace();
    const scopes = requestCockpitScopes();
    if (!locked) {
      const phrase = String(window.prompt(`Підтвердіть UNLOCK batch для ${scopes.join(",")} (${namespace}):`, "") || "").trim().toUpperCase();
      if (phrase !== "UNLOCK") {
        setStatus("Пакетне розблокування скасовано");
        return;
      }
    }
    const result = ui.setPresetProtectionLockBatch(scopes, locked, { namespace });
    setStatus(`Cockpit policy ${locked ? "lock" : "unlock"}: scopes=${result.summary.scope_count}, locked=${result.summary.locked_count}`);
    refreshPresetPolicyHint();
    refreshPresetTimelineHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
  }
  function lockPresetPolicy() {
    const namespace = selectedPresetNamespace();
    ui.setPresetProtectionLock(PRESET_SCOPE, true, { namespace });
    setStatus(`Policy lock увімкнено (${namespace})`);
    refreshPresetPolicyHint();
    refreshPresetTimelineHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
  }
  function unlockPresetPolicy() {
    const namespace = selectedPresetNamespace();
    const phrase = String(window.prompt(`Підтвердіть UNLOCK для ${PRESET_SCOPE} (${namespace}):`, "") || "").trim().toUpperCase();
    if (phrase !== "UNLOCK") {
      setStatus("Unlock скасовано");
      return;
    }
    ui.setPresetProtectionLock(PRESET_SCOPE, false, { namespace });
    setStatus(`Policy lock вимкнено (${namespace})`);
    refreshPresetPolicyHint();
    refreshPresetTimelineHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
  }
  function refreshPresetTimelineHint() {
    const node = document.getElementById("presetTimelineHint");
    if (!node) return;
    try {
      const namespace = selectedPresetNamespace();
      const summary = ui.buildPresetTimelineSummary(PRESET_SCOPE, { namespace });
      if (!summary.last_ts) {
        node.textContent = `Журнал(${namespace}): ${summary.count} · остання: —`;
        node.classList.toggle("empty", summary.count === 0);
        return;
      }
      node.textContent = `Журнал(${namespace}): ${summary.count} · остання: ${timelineActionLabel(summary.last_action)} · ${formatTs(summary.last_ts)}`;
      node.classList.toggle("empty", false);
    } catch (_error) {
      node.textContent = "Журнал: —";
      node.classList.add("empty");
    }
  }
  function showPresetTimeline() {
    const namespace = selectedPresetNamespace();
    const bundle = ui.buildPresetTimelineBundle({ namespace, scopes: TEAM_PRESET_SCOPES });
    window.prompt("Журнал пресетів (JSON):", JSON.stringify(bundle, null, 2));
    refreshPresetTimelineHint();
    refreshPresetCockpitTimelineHint();
  }
  function clearPresetTimelineEntries() {
    const namespace = selectedPresetNamespace();
    if (!window.confirm(`Очистити журнал пресетів для scope "${PRESET_SCOPE}" (${namespace})?`)) return;
    const removed = ui.clearPresetTimeline(PRESET_SCOPE, { namespace });
    setStatus(`Журнал очищено (${namespace}): видалено=${removed}`);
    refreshPresetTimelineHint();
    refreshPresetCockpitTimelineHint();
  }
  function openPresetTimelineDetails(item) {
    const entry = item && typeof item === "object" ? item : {};
    const label = timelineActionLabel(entry.action);
    const payload = {
      ts: String(entry.ts || ""),
      action: String(entry.action || ""),
      scope: String(entry.scope || PRESET_SCOPE),
      namespace: String(entry.namespace || selectedPresetNamespace()),
      details: entry.details && typeof entry.details === "object" ? entry.details : {},
    };
    window.prompt(`Деталі журналу: ${label}`, JSON.stringify(payload, null, 2));
  }
  function previewPresetImport(mode = "merge") {
    const raw = String(window.prompt(`Попередній перегляд JSON пресетів (${mode}):`, lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const preview = parsePresetPreview(raw, mode);
      lastPresetImportRaw = raw;
      lastPresetPreview = preview;
      refreshPresetMergeHint();
      window.prompt(`Попередній перегляд  (JSON):`, JSON.stringify(previewPayloadForPrompt(preview), null, 2));
      setStatus(`Попередній перегляд : ${previewSummary(preview.summary || {})}`);
    } catch (error) {
      setStatus(`ПОМИЛКА preview: ${error}`);
    }
  }
  function applyPresetPayload(payload) {
    const source = payload && typeof payload === "object" ? payload : {};
    document.getElementById("q").value = String(source.q || "");
    document.getElementById("central").value = String(source.central || "");
    document.getElementById("code").value = String(source.code || "");
    document.getElementById("sev").value = String(source.severity || "all");
    document.getElementById("includeSilenced").checked = !!source.includeSilenced;
  }
  function loadPresetSelect(selectedName) {
    const presets = ui.listPresets(PRESET_SCOPE, { namespace: selectedPresetNamespace() });
    const select = document.getElementById("presetSelect");
    const prev = selectedName || select.value || "";
    select.innerHTML = '<option value="">пресети алертів</option>';
    for (const item of presets) {
      const option = document.createElement("option");
      option.value = item.name;
      option.textContent = item.name;
      select.appendChild(option);
    }
    if (prev && presets.some((item) => item.name === prev)) select.value = prev;
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetMergeHint();
    refreshPresetPolicyHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
    refreshPresetRolloutHint();
  }
  function saveCurrentPreset() {
    const namespace = selectedPresetNamespace();
    const selected = document.getElementById("presetSelect").value || "";
    const name = String(window.prompt("Назва пресету алертів:", selected || "") || "").trim();
    if (!name) return;
    try {
      ui.savePreset(PRESET_SCOPE, name, collectPresetPayload(), { namespace });
      loadPresetSelect(name);
      setStatus(`Пресет збережено (${namespace}): ${name}`);
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Заборонено блокування політики (${namespace}): unlock потрібен для overwrite protected preset`);
        refreshPresetPolicyHint();
      } else {
        setStatus(`ПОМИЛКА save: ${error}`);
      }
    }
  }
  function applySelectedPreset() {
    const namespace = selectedPresetNamespace();
    const name = document.getElementById("presetSelect").value || "";
    if (!name) { setStatus("Оберіть пресет"); return; }
    const preset = ui.getPreset(PRESET_SCOPE, name, { namespace });
    if (!preset) { setStatus(`Пресет не знайдено: ${name}`); return; }
    applyPresetPayload(preset.data || {});
    setStatus(`Застосовано пресет (${namespace}): ${name}`);
    refresh();
  }
  function deleteSelectedPreset() {
    const namespace = selectedPresetNamespace();
    const name = document.getElementById("presetSelect").value || "";
    if (!name) { setStatus("Оберіть пресет"); return; }
    if (!window.confirm(`Видалити пресет "${name}"?`)) return;
    try {
      ui.deletePreset(PRESET_SCOPE, name, { namespace });
      loadPresetSelect("");
      setStatus(`Пресет видалено (${namespace}): ${name}`);
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Заборонено блокування політики (${namespace}): видалення захищеного пресету заблоковано`);
        refreshPresetPolicyHint();
      } else {
        setStatus(`ПОМИЛКА delete: ${error}`);
      }
    }
  }
  async function copyTextBestEffort(text) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch (_error) {}
    return false;
  }
  async function exportPresetData() {
    const namespace = selectedPresetNamespace();
    const raw = namespace === "shared"
      ? ui.exportPresetBundle({ namespace, scopes: TEAM_PRESET_SCOPES })
      : ui.exportPresets(PRESET_SCOPE, { namespace });
    const copied = await copyTextBestEffort(raw);
    window.prompt("JSON пресетів (скопіюйте):", raw);
    setStatus(`Експорт пресетів (${namespace})${copied ? " · скопійовано" : ""}`);
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetCockpitTimelineHint();
    refreshPresetRolloutHint();
  }
  function importPresetData(mode = "merge") {
    const namespace = selectedPresetNamespace();
    const raw = String(window.prompt(`Вставте JSON пресетів (${mode}):`, lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const preview = parsePresetPreview(raw, mode);
      lastPresetImportRaw = raw;
      lastPresetPreview = preview;
      refreshPresetMergeHint();
      const conflicts = Number(preview.summary && preview.summary.conflicts ? preview.summary.conflicts : 0);
      const drops = Number(preview.summary && preview.summary.drop ? preview.summary.drop : 0);
      if (conflicts > 0 && !window.confirm(`Виявлено конфлікти: ${conflicts}. Продовжити ${mode}?`)) {
        setStatus(`Імпорт ${mode} скасовано: конфлікти=${conflicts}`);
        return;
      }
      if (mode === "replace" && drops > 0 && !window.confirm(`Режим replace видалить ${drops} пресет(ів). Підтвердити?`)) {
        setStatus(`Імпорт replace скасовано: drop=${drops}`);
        return;
      }
      const result = namespace === "shared"
        ? ui.importPresetBundle(raw, { namespace, mode })
        : ui.importPresets(PRESET_SCOPE, raw, { namespace, mode });
      loadPresetSelect("");
      setStatus(`Імпорт ${mode} (${namespace}): імпортовано=${result.imported || 0}, всього=${result.total || 0}, конфлікти=${conflicts}`);
      refreshPresetSummary();
      refreshPresetTimelineHint();
      refreshPresetMergeHint();
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Імпорт заблоковано блокування політики (${namespace}): захищені пресети`);
        refreshPresetPolicyHint();
      } else {
        setStatus(`ПОМИЛКА імпорту: ${error}`);
      }
    }
  }
  function installScopeProfiles() {
    const namespace = selectedPresetNamespace();
    const result = ui.installPresetProfiles(PRESET_SCOPE, { namespace, overwrite: false });
    loadPresetSelect("");
    setStatus(`Профілі (${namespace}): додано=${result.installed}, всього=${result.total}, пропущено_захищені=${result.skipped_protected || 0}`);
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetPolicyHint();
  }
  function cleanupPresetStore() {
    const namespace = selectedPresetNamespace();
    const daysRaw = String(window.prompt("Retention днів для пресетів:", "30") || "").trim();
    const maxRaw = String(window.prompt("Максимум пресетів у scope:", "20") || "").trim();
    const days = parseInt(daysRaw || "30", 10);
    const maxEntries = parseInt(maxRaw || "20", 10);
    const result = ui.cleanupPresets(PRESET_SCOPE, {
      namespace,
      maxAgeDays: Number.isFinite(days) ? days : 30,
      maxEntries: Number.isFinite(maxEntries) ? maxEntries : 20,
      archive: true,
    });
    loadPresetSelect("");
    setStatus(`Очищення (${namespace}): видалено=${result.removed}, залишилось=${result.kept}, архів=${result.archived_total}`);
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetPolicyHint();
  }
  function showPresetMetrics() {
    const report = ui.buildPresetObservabilityBundle({ scopes: TEAM_PRESET_SCOPES });
    window.prompt("Метрики пресетів (JSON):", JSON.stringify(report, null, 2));
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetPolicyHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
    refreshPresetRolloutHint();
  }
  function openAlertsCommandPalette() {
    const namespace = selectedPresetNamespace();
    const presets = ui.listPresets(PRESET_SCOPE, { namespace });
    const timelineEntries = ui.listPresetTimeline(PRESET_SCOPE, { namespace, limit: 8 });
    const presetCommands = presets.map((item) => ({
      title: `Пресет: ${item.name}`,
      subtitle: `Застосувати збережений набір фільтрів (${namespace})`,
      run: () => {
        applyPresetPayload(item.data || {});
        setStatus(`Застосовано пресет: ${item.name}`);
        refresh();
      },
    }));
    const timelineCommands = timelineEntries.map((item) => ({
      title: `Журнал: ${timelineActionLabel(item.action)}`,
      subtitle: `${formatTs(item.ts)} · drill-down`,
      run: () => openPresetTimelineDetails(item),
    }));
    ui.openCommandPalette({
      title: "Команди алертів",
      commands: [
        { title: "Фільтр: критичні", subtitle: "severity=bad", run: () => { document.getElementById("sev").value = "bad"; refresh(); } },
        { title: "Фільтр: попередження", subtitle: "severity=warn", run: () => { document.getElementById("sev").value = "warn"; refresh(); } },
        { title: "Показати заглушені", subtitle: "includeSilenced=on", run: () => { document.getElementById("includeSilenced").checked = true; refresh(); } },
        { title: "Скинути фільтри", subtitle: "Повернути стандартний режим", run: clearFilters },
        { title: "Зберегти поточний пресет", subtitle: "Зберегти набір фільтрів у localStorage", run: saveCurrentPreset },
        { title: "Простір: локальні", subtitle: "Переключити на локальні пресети", run: () => { document.getElementById("presetNamespace").value = "local"; loadPresetSelect(""); } },
        { title: "Простір: спільні", subtitle: "Переключити на спільний простір пресетів", run: () => { document.getElementById("presetNamespace").value = "shared"; loadPresetSelect(""); } },
        { title: "Політика: розблокувати", subtitle: "Вимкнути блокування для захищених пресетів", run: unlockPresetPolicy },
        { title: "Політика: заблокувати", subtitle: "Увімкнути блокування для захищених пресетів", run: lockPresetPolicy },
        { title: "Експорт пресетів", subtitle: "Вивантажити JSON у буфер/діалог", run: exportPresetData },
        { title: "Попередній перегляд merge", subtitle: "Симуляція merge без запису", run: () => previewPresetImport("merge") },
        { title: "Імпорт merge", subtitle: "Застосувати merge імпорт", run: () => importPresetData("merge") },
        { title: "Імпорт replace", subtitle: "Застосувати replace імпорт", run: () => importPresetData("replace") },
        { title: "Cockpit: попередній перегляд", subtitle: "Пакетний попередній перегляд по scope", run: () => previewPresetCockpit("merge") },
        { title: "Cockpit: apply merge", subtitle: "Пакетне застосування merge по scope", run: () => applyPresetCockpit("merge") },
        { title: "Cockpit: apply replace", subtitle: "Пакетне застосування replace по scope", run: () => applyPresetCockpit("replace") },
        { title: "Cockpit: панель таймлайна", subtitle: "Фільтри scope/action/namespace", run: showPresetCockpitTimelinePanel },
        { title: "Розгортання: assistant merge", subtitle: "Безпечний протокол застосування (merge)", run: () => runPresetRolloutAssistant("merge") },
        { title: "Розгортання: assistant replace", subtitle: "Безпечний протокол застосування (replace)", run: () => runPresetRolloutAssistant("replace") },
        { title: "Розгортання: останній summary", subtitle: "Останній результат розгортання", run: showLastPresetRolloutSummary },
        { title: "Cockpit: policy unlock batch", subtitle: "Пакетне розблокування для scope", run: () => setPresetCockpitLockBatch(false) },
        { title: "Cockpit: блокування політики batch", subtitle: "Пакетне блокування для scope", run: () => setPresetCockpitLockBatch(true) },
        { title: "Встановити профілі scope", subtitle: "Додати стандартні профілі для alerts", run: installScopeProfiles },
        { title: "Прибирання пресетів", subtitle: "Retention + архівування старих пресетів", run: cleanupPresetStore },
        { title: "Метрики пресетів", subtitle: "Показати summary namespace/scope", run: showPresetMetrics },
        { title: "Журнал пресетів", subtitle: "Показати timeline scope/team", run: showPresetTimeline },
        { title: "Очистити журнал пресетів", subtitle: "Очистити timeline поточного scope", run: clearPresetTimelineEntries },
        ...timelineCommands,
        ...presetCommands,
      ],
    });
  }
  function applyWorkspaceContext() {
    const context = ui.loadWorkspaceContext({ maxAgeSec: 3 * 24 * 3600 });
    if (!context) {
      setStatus("Контекст не знайдено або застарів");
      refreshWorkspaceHint();
      return;
    }
    if (context.central_id) document.getElementById("central").value = context.central_id;
    if (context.code) document.getElementById("code").value = context.code;
    refreshWorkspaceHint();
    syncQueryFromFilters();
    refresh();
  }
  function clearFilters() {
    document.getElementById("q").value = "";
    document.getElementById("central").value = "";
    document.getElementById("code").value = "";
    document.getElementById("sev").value = "all";
    document.getElementById("includeSilenced").checked = false;
    syncQueryFromFilters();
    syncFilterSummary();
    refresh();
  }
  function boolFromQuery(value, fallback = false) {
    if (value === null || value === undefined) return !!fallback;
    const normalized = String(value).trim().toLowerCase();
    if (!normalized) return !!fallback;
    if (normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on") return true;
    if (normalized === "0" || normalized === "false" || normalized === "no" || normalized === "off") return false;
    return !!fallback;
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const sev = String(params.get("sev") || params.get("severity") || "").trim().toLowerCase();
    if (sev === "all" || sev === "good" || sev === "warn" || sev === "bad") {
      document.getElementById("sev").value = sev;
    }
    const q = params.get("q");
    if (q !== null) document.getElementById("q").value = String(q);
    const central = params.get("central") || params.get("central_id");
    if (central !== null) document.getElementById("central").value = String(central);
    const code = params.get("code");
    if (code !== null) document.getElementById("code").value = String(code);
    const includeSilenced = params.get("includeSilenced") ?? params.get("include_silenced");
    if (includeSilenced !== null) {
      document.getElementById("includeSilenced").checked = boolFromQuery(includeSilenced, false);
    }
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const q = String(document.getElementById("q").value || "").trim();
    const central = String(document.getElementById("central").value || "").trim();
    const code = String(document.getElementById("code").value || "").trim();
    const sev = String(document.getElementById("sev").value || "all").trim().toLowerCase();
    const includeSilenced = !!document.getElementById("includeSilenced").checked;
    if (q) params.set("q", q);
    if (central) params.set("central_id", central);
    if (code) params.set("code", code);
    if (sev && sev !== "all") params.set("severity", sev);
    if (includeSilenced) params.set("include_silenced", "1");
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const parts = [];
    const q = String(document.getElementById("q").value || "").trim();
    const central = String(document.getElementById("central").value || "").trim();
    const code = String(document.getElementById("code").value || "").trim();
    const sev = selectedSeverity();
    const silenced = includeSilenced();
    if (q) parts.push(`q=${q}`);
    if (central) parts.push(`вузол=${central}`);
    if (code) parts.push(`код=${code}`);
    if (sev && sev !== "all") parts.push(`рівень=${sev}`);
    if (silenced) parts.push("+заглушені");
    const node = document.getElementById("filterSummary");
    if (!node) return;
    node.textContent = parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні";
  }
  function actionLabel(action) {
    if (action === "ack") return "підтвердження";
    if (action === "silence") return "пауза";
    if (action === "unsilence") return "зняття паузи";
    return action;
  }
  async function apiPost(path, payload) {
    return ui.apiPost(path, payload);
  }
  async function loadWhoami() {
    const data = await ui.loadWhoami();
    adminRole = data.role;
    adminCaps = data.capabilities || { read: true, operate: false, admin: false };
    document.getElementById("roleBadge").textContent = `роль: ${adminRole}`;
    const disabled = !canOperate();
    ["bulkAck", "bulkSilence", "bulkUnsilence"].forEach((id) => {
      document.getElementById(id).disabled = disabled;
    });
  }
  function updateSelectedBadge() {
    document.getElementById("selCount").textContent = `обрано: ${selectedKeys.size}`;
    document.getElementById("selAll").checked = currentAlerts.length > 0 && selectedKeys.size === currentAlerts.length;
  }
  function renderGroups(data) {
    const groups = Array.isArray(data && data.groups) ? data.groups : [];
    const tbody = document.querySelector("#grpTbl tbody");
    tbody.innerHTML = "";
    if (groups.length === 0) {
      const tr = document.createElement("tr");
      tr.innerHTML = '<td colspan="7"><span class="badge good">OK</span> Немає груп алертів за вибраними фільтрами</td>';
      tbody.appendChild(tr);
      return;
    }
    for (const item of groups) {
      const tr = document.createElement("tr");
      const code = String(item.code || "alert");
      const sev = sevClass(item.dominant_severity);
      const actionsDisabled = canOperate() ? "" : "disabled";
      tr.innerHTML = `
        <td><span class="badge ${sev}">${esc(sevLabel(sev))}</span></td>
        <td><code>${esc(code)}</code></td>
        <td><code>${esc(item.total)}</code></td>
        <td><code>${esc(item.centrals_total)}</code></td>
        <td><code>${esc(item.silenced)}</code></td>
        <td><code>${esc(item.latest_ts || "—")}</code></td>
        <td>
          <div class="actions">
            <button class="smallbtn opAction opActionAck" data-action="ack" ${actionsDisabled}>Підтвердити</button>
            <button class="smallbtn opAction opActionSilence" data-action="silence" ${actionsDisabled}>Пауза 1 год</button>
            <button class="smallbtn opAction opActionUnsilence" data-action="unsilence" ${actionsDisabled}>Зняти заглушення</button>
          </div>
        </td>
      `;
      tr.querySelector('button[data-action="ack"]')?.addEventListener("click", () => runCodeAction(code, "ack"));
      tr.querySelector('button[data-action="silence"]')?.addEventListener("click", () => runCodeAction(code, "silence"));
      tr.querySelector('button[data-action="unsilence"]')?.addEventListener("click", () => runCodeAction(code, "unsilence"));
      tbody.appendChild(tr);
    }
  }
  function renderAlerts(alerts) {
    const tbody = document.querySelector("#tbl tbody");
    tbody.innerHTML = "";
    if (alerts.length === 0) {
      const tr = document.createElement("tr");
      tr.innerHTML = '<td colspan="9"><span class="badge good">OK</span> Немає активних алертів</td>';
      tbody.appendChild(tr);
      updateSelectedBadge();
      return;
    }
    for (const alert of alerts) {
      const tr = document.createElement("tr");
      const key = alertKey(alert);
      const sev = sevClass(alert.severity);
      const centralId = String(alert.central_id || "");
      const code = String(alert.code || "alert");
      const checked = selectedKeys.has(key) ? "checked" : "";
      const stateParts = [];
      if (alert.silenced) stateParts.push('<span class="badge warn">заглушено</span>');
      if (alert.acked_at) stateParts.push('<span class="badge good">підтверджено</span>');
      if (stateParts.length === 0) stateParts.push('<span class="badge">відкрито</span>');
      const actionsDisabled = canOperate() ? "" : "disabled";
      tr.innerHTML = `
        <td><input data-key="${esc(key)}" type="checkbox" ${checked} /></td>
        <td><span class="badge ${sev}">${esc(sevLabel(sev))}</span></td>
        <td><a href="/admin/fleet/central/${encodeURIComponent(centralId)}"><code>${esc(centralId || "—")}</code></a></td>
        <td><code>${esc(alert.vehicle_id || "—")}</code></td>
        <td><a data-workspace-incident-code="1" href="/admin/fleet/incidents/${encodeURIComponent(centralId)}/${encodeURIComponent(code)}"><code>${esc(code)}</code></a></td>
        <td>${esc(alert.message || "")}</td>
        <td><code>${fmtAge(alert.age_sec)}</code></td>
        <td>${stateParts.join(" ")}</td>
        <td>
          <div class="actions">
            <button class="smallbtn opAction opActionAck" data-action="ack" ${actionsDisabled}>Підтвердити</button>
            <button class="smallbtn opAction opActionSilence" data-action="silence" ${actionsDisabled}>Пауза 1 год</button>
            <button class="smallbtn opAction opActionUnsilence" data-action="unsilence" ${actionsDisabled}>Зняти заглушення</button>
          </div>
        </td>
      `;
      const checkbox = tr.querySelector('input[data-key]');
      if (checkbox) {
        checkbox.addEventListener("change", (event) => {
          if (event.target.checked) selectedKeys.add(key);
          else selectedKeys.delete(key);
          updateSelectedBadge();
        });
      }
      tr.querySelector('a[data-workspace-incident-code="1"]')?.addEventListener("click", () => {
        rememberAlertContext(centralId, code, "alerts/list");
      });
      tr.querySelector('button[data-action="ack"]')?.addEventListener("click", () => runAlertsAction([alert], "ack"));
      tr.querySelector('button[data-action="silence"]')?.addEventListener("click", () => runAlertsAction([alert], "silence"));
      tr.querySelector('button[data-action="unsilence"]')?.addEventListener("click", () => runAlertsAction([alert], "unsilence"));
      tbody.appendChild(tr);
    }
    updateSelectedBadge();
  }
  async function runAlertsAction(alerts, action) {
    if (!canOperate()) {
      setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator");
      return;
    }
    const payloads = Array.isArray(alerts) ? alerts : [];
    if (payloads.length === 0) {
      setStatus("Немає алертів для дії");
      return;
    }
    let ok = 0;
    let failed = 0;
    const actor = "admin-ui";
    const timing = await ui.runActionWithLatency(async () => {
      setStatus(`Виконую ${actionLabel(action)} для ${payloads.length} алертів...`);
      for (const alert of payloads) {
        const centralId = String(alert.central_id || "");
        const code = String(alert.code || "");
        const body = { central_id: centralId, code, actor };
        try {
          if (action === "ack") {
            await apiPost("/api/admin/fleet/alerts/ack", { ...body, note: "bulk ack from /admin/fleet/alerts" });
          } else if (action === "silence") {
            await apiPost("/api/admin/fleet/alerts/silence", { ...body, duration_sec: 3600, note: "bulk silence 1h from /admin/fleet/alerts" });
          } else {
            await apiPost("/api/admin/fleet/alerts/unsilence", { ...body, note: "bulk unsilence from /admin/fleet/alerts" });
          }
          ok += 1;
          rememberAlertContext(centralId, code, `alerts/${action}`);
        } catch (_error) {
          failed += 1;
        }
      }
    });
    if (!timing.ok) {
      setStatus(`ПОМИЛКА дії ${actionLabel(action)} (${ui.formatLatency(timing.elapsed_ms)}): ${timing.error}`);
      return;
    }
    setStatus(`Дія ${actionLabel(action)}: успіх=${ok}, помилки=${failed}, час=${ui.formatLatency(timing.elapsed_ms)}`);
    await refresh();
  }
  async function runCodeAction(code, action) {
    const targets = currentAlerts.filter((item) => String(item.code || "") === code);
    await runAlertsAction(targets, action);
  }
  async function runBulk(action) {
    const chosen = currentAlerts.filter((item) => selectedKeys.has(alertKey(item)));
    await runAlertsAction(chosen, action);
  }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const params = new URLSearchParams();
      params.set("limit", "1500");
      if (includeSilenced()) params.set("include_silenced", "1");
      const sev = selectedSeverity();
      if (sev !== "all") params.set("severity", sev);
      const qv = query();
      const central = selectedCentral();
      const code = selectedCode();
      if (qv) params.set("q", qv);
      if (central) params.set("central_id", central);
      if (code) params.set("code", code);

      const groupParams = new URLSearchParams(params);
      groupParams.set("limit", "500");

      const [alertsResp, groupsResp] = await Promise.all([
        fetch(`/api/admin/fleet/alerts?${params.toString()}`),
        fetch(`/api/admin/fleet/alerts/groups?${groupParams.toString()}`),
      ]);
      const alertsText = await alertsResp.text();
      if (!alertsResp.ok) throw new Error(`${alertsResp.status} ${alertsText}`);
      const groupsText = await groupsResp.text();
      if (!groupsResp.ok) throw new Error(`${groupsResp.status} ${groupsText}`);
      const alertsData = JSON.parse(alertsText);
      const groupsData = JSON.parse(groupsText);
      currentAlerts = Array.isArray(alertsData.alerts) ? alertsData.alerts : [];
      selectedKeys = new Set([...selectedKeys].filter((key) => currentAlerts.some((item) => alertKey(item) === key)));

      const severityTotals = groupsData.severity_totals || {};
      document.getElementById("sumAlerts").textContent = `алертів: ${alertsData.total ?? currentAlerts.length}`;
      document.getElementById("sumGroups").textContent = `груп кодів: ${groupsData.groups_total ?? 0}`;
      document.getElementById("sumBad").textContent = `критичні: ${severityTotals.bad || 0}`;
      document.getElementById("sumWarn").textContent = `попередження: ${severityTotals.warn || 0}`;
      document.getElementById("sumGood").textContent = `справні: ${severityTotals.good || 0}`;
      document.getElementById("sumSilenced").textContent = `заглушені: ${groupsData.silenced_total || 0}`;

      renderGroups(groupsData);
      renderAlerts(currentAlerts);
      setStatus(`OK: алертів=${currentAlerts.length}, груп=${groupsData.groups_total || 0}`);
    } catch (error) {
      setStatus(`ПОМИЛКА: ${error}`);
    }
  }
  document.getElementById("refresh").addEventListener("click", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  document.getElementById("q").addEventListener("input", scheduleRefresh);
  document.getElementById("central").addEventListener("input", scheduleRefresh);
  document.getElementById("code").addEventListener("input", scheduleRefresh);
  document.getElementById("sev").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("includeSilenced").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("clearFilters").addEventListener("click", clearFilters);
  document.getElementById("selAll").addEventListener("change", (event) => {
    if (event.target.checked) {
      selectedKeys = new Set(currentAlerts.map((item) => alertKey(item)));
    } else {
      selectedKeys.clear();
    }
    renderAlerts(currentAlerts);
  });
  document.getElementById("clearSel").addEventListener("click", () => {
    selectedKeys.clear();
    renderAlerts(currentAlerts);
  });
  document.getElementById("bulkAck").addEventListener("click", () => runBulk("ack"));
  document.getElementById("bulkSilence").addEventListener("click", () => runBulk("silence"));
  document.getElementById("bulkUnsilence").addEventListener("click", () => runBulk("unsilence"));
  document.getElementById("workspaceApply").addEventListener("click", applyWorkspaceContext);
  document.getElementById("workspaceClear").addEventListener("click", () => { ui.clearWorkspaceContext(); refreshWorkspaceHint(); });
  document.getElementById("cmdPaletteOpen").addEventListener("click", openAlertsCommandPalette);
  document.getElementById("presetNamespace").addEventListener("change", () => loadPresetSelect(""));
  document.getElementById("presetSave").addEventListener("click", saveCurrentPreset);
  document.getElementById("presetApply").addEventListener("click", applySelectedPreset);
  document.getElementById("presetDelete").addEventListener("click", deleteSelectedPreset);
  document.getElementById("presetExport").addEventListener("click", exportPresetData);
  document.getElementById("presetPreview").addEventListener("click", () => previewPresetImport("merge"));
  document.getElementById("presetImport").addEventListener("click", () => importPresetData("merge"));
  document.getElementById("presetCockpit").addEventListener("click", () => previewPresetCockpit("merge"));
  document.getElementById("presetCockpitTimeline").addEventListener("click", showPresetCockpitTimelinePanel);
  document.getElementById("presetRollout").addEventListener("click", () => runPresetRolloutAssistant("merge"));
  document.getElementById("presetMetrics").addEventListener("click", showPresetMetrics);
  document.getElementById("presetTimelineOpen").addEventListener("click", showPresetTimeline);
  document.getElementById("presetTimelineClear").addEventListener("click", clearPresetTimelineEntries);
  document.getElementById("presetPolicyUnlock").addEventListener("click", unlockPresetPolicy);
  document.getElementById("presetPolicyLock").addEventListener("click", lockPresetPolicy);
  document.getElementById("presetProfiles").addEventListener("click", installScopeProfiles);
  document.getElementById("presetCleanup").addEventListener("click", cleanupPresetStore);
  ui.bindEnterRefresh(["q", "central", "code"], () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  ui.bindCommandPalette(openAlertsCommandPalette);
  initSecondaryDetails();
  const densityMode = ui.initDensityMode("density", {
    storageKey: "fleet_alerts_density",
    className: "density-compact",
    onChange: syncDensityBadge,
  });
  syncDensityBadge(densityMode);
  applyFiltersFromQuery();
  syncQueryFromFilters();
  syncFilterSummary();
  refreshWorkspaceHint();
  loadPresetSelect("");
  refreshPresetSummary();
  refreshPresetTimelineHint();
  refreshPresetMergeHint();
  refreshPresetPolicyHint();
  refreshPresetCockpitHint();
  refreshPresetCockpitTimelineHint();
  refreshPresetRolloutHint();
  loadWhoami().then(refresh);
  setInterval(() => { if (ui.byId("auto").checked) refresh(); }, 10000);
""".strip()
    return render_admin_shell(
        title='Адмін-панель Passengers — Оперативні алерти',
        header_title='Оперативні алерти',
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        max_width=1340,
        extra_css=extra_css,
        current_nav="alerts",
    )
