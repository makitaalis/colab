from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_incidents_page() -> str:
    chips_html = """
        <span class="chip">відкриті / підтверджені / заглушені / вирішені</span>
        <span class="chip" id="roleBadge">роль: —</span>
        <span class="chip" id="updatedAt">оновлено: —</span>
"""
    toolbar_html = """
        <div class="toolbarMain">
          <input id="q" type="text" placeholder="пошук повідомлення" />
          <label><input id="auto" type="checkbox" checked /> авто</label>
          <button id="clearFilters">Скинути</button>
          <button id="refresh" class="primary">Оновити</button>
          <button id="copyLink" title="Скопіювати поточне посилання (з урахуванням фільтрів)">Скопіювати посилання</button>
          <details class="toolbarDetails" data-advanced-details="1">
            <summary>Фільтри</summary>
            <div class="toolbarDetailsGrid">
              <input id="central" type="text" placeholder="ідентифікатор вузла" />
              <input id="code" type="text" placeholder="код інциденту" />
              <select id="statusFilter">
                <option value="all">усі статуси</option>
                <option value="open">відкриті</option>
                <option value="acked">підтверджені</option>
                <option value="silenced">заглушені</option>
                <option value="resolved">вирішені</option>
              </select>
              <select id="severityFilter">
                <option value="all">усі рівні</option>
                <option value="bad">критичні</option>
                <option value="warn">попередження</option>
                <option value="good">справні</option>
              </select>
              <select id="density" title="щільність таблиць">
                <option value="regular" selected>Звичайна</option>
                <option value="compact">Компактна</option>
              </select>
              <label><input id="slaOnly" type="checkbox" /> лише порушення SLA</label>
              <label><input id="resolvedToggle" type="checkbox" checked /> включити вирішені</label>
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
        <a class="flowStep" href="/admin/fleet/alerts">2. Оперативні алерти</a>
        <span class="flowStep current">3. Інциденти та дії</span>
        <a class="flowStep" href="/admin/audit">4. Аудит і контроль</a>
      </div>
      <div class="flowHint">Робочий цикл: відфільтруйте відкриті інциденти, виконайте дію, перевірте журнал дій і аудит.</div>
      <div class="sectionTools" style="margin-top:8px;">
        <a class="quickLink" href="/admin/fleet">До моніторингу</a>
        <a class="quickLink" href="/admin/fleet/alerts">До алертів</a>
        <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
        <a class="quickLink" href="/admin/audit">Аудит</a>
      </div>
      <div class="workspaceBar" style="margin-top: 10px;">
        <span id="workspaceHint" class="workspaceHint empty">Контекст інциденту: —</span>
        <button id="workspaceApply" class="smallbtn">Підставити контекст</button>
        <button id="workspaceClear" class="smallbtn">Очистити контекст</button>
        <button id="cmdPaletteOpen" class="smallbtn">Команди</button>
      </div>
    </div>

    <details id="incToolsDetails" class="domainSplitDetails" data-advanced-details="1" style="margin-top: 14px;">
      <summary>Розширені інструменти (пресети / кокпіт / rollout)</summary>
      <div class="domainSplitHint">
        Цей блок залишено для advanced-операцій (пресети, кокпіт, rollout). Для щоденного triage використовуйте фокус-фільтри і bulk actions у таблиці інцидентів.
      </div>
      <div class="workspaceBar" style="margin-top: 10px;">
        <span id="presetSummary" class="workspaceHint empty">Пресети: —</span>
        <span id="presetObservability" class="workspaceHint empty">Область: —</span>
        <span id="presetTimelineHint" class="workspaceHint empty">Журнал: —</span>
        <span id="presetMergeHint" class="workspaceHint empty">Злиття: —</span>
        <span id="presetPolicyHint" class="workspaceHint empty">Політика: —</span>
        <span id="presetCockpitHint" class="workspaceHint empty">Кокпіт: —</span>
        <span id="presetCockpitTimelineHint" class="workspaceHint empty">Журнал кокпіта: —</span>
        <span id="presetRolloutHint" class="workspaceHint empty">Розгортання: —</span>
        <select id="presetNamespace" title="простір пресетів">
          <option value="local" selected>локальні</option>
          <option value="shared">спільні</option>
        </select>
        <select id="presetSelect" title="збережені пресети">
          <option value="">пресети інцидентів</option>
        </select>
        <button id="presetSave" class="smallbtn">Зберегти</button>
        <button id="presetApply" class="smallbtn">Застосувати</button>
        <button id="presetDelete" class="smallbtn">Видалити</button>
        <button id="presetExport" class="smallbtn">Експорт</button>
        <button id="presetPreview" class="smallbtn">Попередній перегляд</button>
        <button id="presetImport" class="smallbtn">Імпорт</button>
        <button id="presetCockpit" class="smallbtn">Кокпіт</button>
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

    <div class="card">
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code>/api/admin/fleet/incidents</code></span>
        <span class="metaChip sort">сортування: <code>severity ↓</code>, далі <code>age ↓</code></span>
        <span class="metaChip mode" id="densityBadge">щільність: Звичайна</span>
      </div>
      <div class="kpiGrid">
        <div class="kpi"><div class="kpiLabel">Відкриті</div><div class="kpiValue bad" id="kpiOpen">0</div></div>
        <div class="kpi"><div class="kpiLabel">Критичні</div><div class="kpiValue bad" id="kpiBad">0</div></div>
        <div class="kpi"><div class="kpiLabel">Попередження</div><div class="kpiValue warn" id="kpiWarn">0</div></div>
        <div class="kpi"><div class="kpiLabel">Порушення SLA</div><div class="kpiValue bad" id="kpiSla">0</div></div>
      </div>
      <div class="summary">
        <span class="badge" id="sumTotal">всього: 0</span>
        <span class="badge status-badge open" id="sumOpen">відкриті: 0</span>
        <span class="badge status-badge acked" id="sumAcked">підтверджені: 0</span>
        <span class="badge status-badge silenced" id="sumSilenced">заглушені: 0</span>
        <span class="badge status-badge resolved" id="sumResolved">вирішені: 0</span>
        <span class="badge bad" id="sumBad">критичні: 0</span>
        <span class="badge warn" id="sumWarn">попередження: 0</span>
        <span class="badge good" id="sumGood">справні: 0</span>
        <span class="badge bad" id="sumSla">Порушення SLA: 0</span>
      </div>
      <div class="quickFilters">
        <button id="quickOpen" class="quickBtn warn">Фокус: відкриті</button>
        <button id="quickBad" class="quickBtn bad">Фокус: критичні</button>
        <button id="quickSla" class="quickBtn bad">Фокус: SLA порушення</button>
        <button id="quickSilenced" class="quickBtn warn">Фокус: заглушені</button>
        <button id="quickReset" class="quickBtn good">Скинути фільтри</button>
      </div>
      <div id="incFilterState" class="filterState good">Фільтри: стандартний режим</div>
      <div class="actionsBar">
        <label><input id="selectAll" type="checkbox" /> обрати всі видимі</label>
        <span class="badge" id="selCount">обрано: 0</span>
        <button id="bulkAck" class="opAction opActionAck">Підтвердити вибрані</button>
        <button id="bulkSilence" class="opAction opActionSilence">Пауза 1 год</button>
        <button id="bulkUnsilence" class="opAction opActionUnsilence">Зняти заглушення</button>
        <button id="clearSelection" class="opAction">Скинути вибір</button>
      </div>
      <div class="tableWrap">
        <table id="incTbl">
          <thead>
            <tr>
              <th class="checkCol">✓</th>
              <th>Статус</th>
              <th>Рівень</th>
              <th>Вузол</th>
              <th>Код</th>
              <th>Вік інциденту</th>
              <th>SLA</th>
              <th>Перше / Останнє</th>
              <th>Повідомлення</th>
              <th>Стан</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <details id="incSecondaryDetails" class="domainSplitDetails" data-advanced-details="1">
      <summary>Вторинна аналітика (SLA heatmap + журнал доставки)</summary>
      <div class="domainSplitHint">
        Primary triage виконуйте у таблиці інцидентів вище (фокус-фільтри + bulk actions).
        Тут зібрано додаткові контекстні блоки для розбору причин і handoff.
      </div>

      <div class="heatmapWrap" style="margin-top: 10px;">
        <div class="sectionHead">
          <div class="sectionTitle">Теплокарта SLA</div>
          <div class="sectionTools">
            <a class="quickLink" href="/admin/audit">Аудит</a>
            <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
          </div>
        </div>
        <div class="muted">Кожна клітинка — активний інцидент (відкриті/підтверджені/заглушені). Натисніть клітинку для переходу у деталі.</div>
        <div class="summary">
          <span class="badge good" id="heatGood">зелена зона: 0</span>
          <span class="badge warn" id="heatWarn">ризик: 0</span>
          <span class="badge bad" id="heatBad">порушено: 0</span>
          <span class="badge" id="heatNone">без SLA: 0</span>
        </div>
        <div class="heatmapGrid" id="slaHeatmap"></div>
      </div>

      <div style="margin-top: 12px;">
        <div class="sectionHead">
          <div class="sectionTitle">Журнал доставки сповіщень</div>
          <div class="sectionTools">
            <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
            <a class="quickLink" href="/admin/audit">Аудит</a>
          </div>
        </div>
        <div class="tableMeta">
          <span class="metaChip source">джерело: <code>/api/admin/fleet/incidents/notifications</code></span>
          <span class="metaChip sort">сортування: <code>ts ↓</code></span>
        </div>
        <div class="tableWrap">
          <table id="notifTbl">
            <thead>
              <tr>
                <th>Час</th>
                <th>Статус</th>
                <th>Канал</th>
                <th>Подія</th>
                <th>Вузол</th>
                <th>Код</th>
                <th>Отримувач</th>
                <th>Помилка</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </details>
  
"""
    extra_css = """
    #q { min-width: 320px; }
    .toolbar input[type="text"] { min-width: 180px; }
    .toolbar select { min-width: 120px; }
    .kpiGrid { display:grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin-top: 10px; }
    .kpi { border: 1px solid var(--border); border-radius: 12px; padding: 10px; background: rgba(255,255,255,.03); }
    .kpiLabel { color: var(--muted); font-size: 12px; }
    .kpiValue { font-size: 22px; font-weight: 700; }
    .kpiValue.good { color: #9cebc5; }
    .kpiValue.warn { color: #ffe09c; }
    .kpiValue.bad { color: #ffb1b1; }
    .status-badge { text-transform: uppercase; }
    .status-badge.open { color: #ffb1b1; border-color: rgba(255,93,93,.35); background: rgba(255,93,93,.12); }
    .status-badge.acked { color: #cfe2ff; border-color: rgba(127,176,255,.45); background: rgba(127,176,255,.14); }
    .status-badge.silenced { color: #ffe09c; border-color: rgba(242,201,76,.35); background: rgba(242,201,76,.12); }
    .status-badge.resolved { color: #9cebc5; border-color: rgba(40,209,124,.35); background: rgba(40,209,124,.12); }
    .actionsBar { display:flex; gap: 8px; flex-wrap: wrap; align-items:center; margin-top: 10px; }
    .actionsBar label { display:flex; align-items:center; gap: 6px; color: var(--muted); font-size: 12px; }
    .actionsBar button { padding: 6px 9px; border-radius: 10px; font-size: 12px; }
    .quickFilters { display:flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
    .quickBtn { padding: 6px 10px; border-radius: 999px; font-size: 12px; border: 1px solid var(--border); background: rgba(255,255,255,.04); color: var(--text); cursor: pointer; }
    .quickBtn { transition: border-color .18s ease, background .18s ease, transform .12s ease; }
    .quickBtn:hover { transform: translateY(-1px); }
    .quickBtn.active { box-shadow: inset 0 0 0 1px rgba(255,255,255,.16); }
    .quickBtn.bad.active { border-color: rgba(255,93,93,.5); background: rgba(255,93,93,.15); }
    .quickBtn.warn.active { border-color: rgba(242,201,76,.5); background: rgba(242,201,76,.15); }
    .quickBtn.good.active { border-color: rgba(40,209,124,.5); background: rgba(40,209,124,.15); }
    .filterState { margin-top: 10px; border: 1px solid var(--border); border-radius: 12px; padding: 8px 10px; font-size: 12px; font-weight: 600; color: var(--muted); background: rgba(255,255,255,.02); }
    .filterState.good { border-color: rgba(40,209,124,.3); background: rgba(40,209,124,.08); color: #9cebc5; }
    .filterState.warn { border-color: rgba(242,201,76,.3); background: rgba(242,201,76,.10); color: #ffe09c; }
    .filterState.bad { border-color: rgba(255,93,93,.35); background: rgba(255,93,93,.10); color: #ffb1b1; }
    .heatmapWrap { margin-top: 10px; border: 1px solid var(--border); border-radius: 12px; padding: 10px; background: rgba(255,255,255,.02); }
    .heatmapGrid { display:grid; grid-template-columns: repeat(auto-fill, minmax(12px, 1fr)); gap: 4px; margin-top: 8px; }
    .heatCell { width: 100%; aspect-ratio: 1 / 1; border-radius: 4px; border: 1px solid rgba(255,255,255,.08); display:block; transition: transform .12s ease, filter .16s ease; }
    .heatCell:hover { transform: translateY(-1px); filter: brightness(1.06); }
    .heatCell.good { background: rgba(40,209,124,.45); }
    .heatCell.warn { background: rgba(242,201,76,.55); }
    .heatCell.bad { background: rgba(255,93,93,.55); }
    .heatCell.none { background: rgba(255,255,255,.10); }
    .checkCol { width: 36px; text-align: center; }
    .tableWrap { overflow:auto; max-height: 48vh; border-radius: 14px; border: 1px solid var(--border); margin-top: 10px; }
    table { width: 100%; border-collapse: collapse; min-width: 1160px; }
    body.density-compact th,
    body.density-compact td { padding: 7px 8px; }
    body.density-compact .kpiValue { font-size: 18px; }
    body.density-compact .actionsBar button { padding: 5px 8px; font-size: 11px; }
    body.density-compact .tableWrap { max-height: 56vh; }
    @media (max-width: 960px) { .kpiGrid { grid-template-columns: repeat(2, 1fr); } }
    @media (max-width: 560px) { .kpiGrid { grid-template-columns: 1fr; } }
  
""".strip()
    script = """
  const ui = window.AdminUiKit;
  const esc = ui.esc;
  const INC_SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_incidents_secondary_details_v1";
  const INC_TOOLS_DETAILS_STORAGE_KEY = "passengers_admin_incidents_tools_details_v1";
  let adminRole = "viewer";
  let adminCaps = { read: true, operate: false, admin: false };
  const selectedKeys = new Set();
  let currentIncidentMap = new Map();
  let visibleKeys = [];
  const PRESET_SCOPE = "fleet_incidents";
  const TEAM_PRESET_SCOPES = ["fleet", "fleet_alerts", "fleet_incidents"];
  let lastPresetImportRaw = "";
  let lastPresetPreview = null;
  let lastPresetCockpitRaw = "";
  let lastPresetCockpitPreview = null;
  let lastPresetCockpitScopes = [...TEAM_PRESET_SCOPES];
  let lastPresetRolloutPlan = null;
  function setStatus(s) { ui.setStatus("status", s); }
  function val(id) { return ui.val(id); }
  function loadSecondaryDetailsOpen() {
    try {
      const raw = String(localStorage.getItem(INC_SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (!raw) return false;
      return raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {
      return false;
    }
  }
  function storeSecondaryDetailsOpen(open) {
    try { localStorage.setItem(INC_SECONDARY_DETAILS_STORAGE_KEY, open ? "1" : "0"); } catch (_error) {}
  }
  function initSecondaryDetails() {
    const node = document.getElementById("incSecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    node.open = loadSecondaryDetailsOpen();
    node.addEventListener("toggle", () => {
      storeSecondaryDetailsOpen(!!node.open);
    });
  }
  function initToolsDetails() {
    const node = document.getElementById("incToolsDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {
      const raw = String(localStorage.getItem(INC_TOOLS_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {}
    node.addEventListener("toggle", () => {
      try { localStorage.setItem(INC_TOOLS_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); } catch (_error) {}
    });
  }
  const scheduleRefresh = ui.debounce(() => {
    syncQueryFromFilters();
    syncFilterSummary();
    refresh();
  }, 280);
  function clearFilters() {
    applyIncidentPreset("reset");
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const central = String(document.getElementById("central").value || "").trim();
    const code = String(document.getElementById("code").value || "").trim();
    const query = String(document.getElementById("q").value || "").trim();
    const statusFilter = String(document.getElementById("statusFilter").value || "all").trim().toLowerCase();
    const severityFilter = String(document.getElementById("severityFilter").value || "all").trim().toLowerCase();
    const includeResolved = !!document.getElementById("resolvedToggle").checked;
    const slaOnly = !!document.getElementById("slaOnly").checked;
    if (central) params.set("central_id", central);
    if (code) params.set("code", code);
    if (query) params.set("q", query);
    if (statusFilter && statusFilter !== "all") params.set("status", statusFilter);
    if (severityFilter && severityFilter !== "all") params.set("severity", severityFilter);
    if (!includeResolved) params.set("include_resolved", "0");
    if (slaOnly) params.set("sla_breached_only", "1");
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const parts = [];
    const central = String(document.getElementById("central").value || "").trim();
    const code = String(document.getElementById("code").value || "").trim();
    const query = String(document.getElementById("q").value || "").trim();
    const statusFilter = String(document.getElementById("statusFilter").value || "all").trim().toLowerCase();
    const severityFilter = String(document.getElementById("severityFilter").value || "all").trim().toLowerCase();
    const includeResolved = !!document.getElementById("resolvedToggle").checked;
    const slaOnly = !!document.getElementById("slaOnly").checked;
    if (query) parts.push(`q=${query}`);
    if (central) parts.push(`вузол=${central}`);
    if (code) parts.push(`код=${code}`);
    if (statusFilter && statusFilter !== "all") parts.push(`статус=${statusFilter}`);
    if (severityFilter && severityFilter !== "all") parts.push(`рівень=${severityFilter}`);
    if (!includeResolved) parts.push("без вирішених");
    if (slaOnly) parts.push("лише SLA");
    const node = document.getElementById("filterSummary");
    if (!node) return;
    node.textContent = parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні";
  }
  function rememberIncidentContext(centralId, code, source) {
    const cleanCentral = String(centralId || "").trim();
    const cleanCode = String(code || "").trim();
    const label = cleanCentral && cleanCode ? `${cleanCentral}:${cleanCode}` : (cleanCentral || cleanCode || "");
    ui.saveWorkspaceContext({
      central_id: cleanCentral,
      code: cleanCode,
      source: source || "incidents",
      label,
    });
    refreshWorkspaceHint();
  }
  function refreshWorkspaceHint() {
    ui.applyWorkspaceHint("workspaceHint", { prefix: "Контекст інциденту", maxAgeSec: 3 * 24 * 3600 });
  }
  function collectPresetPayload() {
    return {
      central: document.getElementById("central").value || "",
      code: document.getElementById("code").value || "",
      q: document.getElementById("q").value || "",
      status: document.getElementById("statusFilter").value || "all",
      severity: document.getElementById("severityFilter").value || "all",
      slaOnly: !!document.getElementById("slaOnly").checked,
      includeResolved: !!document.getElementById("resolvedToggle").checked,
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
    if (normalized === "policy_lock") return "policy lock";
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
      summaryNode.textContent = `Пресети(${namespace}): ${activeTotal} · archive=${activeArchived}`;
      summaryNode.classList.toggle("empty", activeTotal === 0 && activeArchived === 0);
      const localCleanup = report.local_last_cleanup_ts ? formatTs(report.local_last_cleanup_ts) : "—";
      const sharedCleanup = report.shared_last_cleanup_ts ? formatTs(report.shared_last_cleanup_ts) : "—";
      observabilityNode.textContent = `Scope ${PRESET_SCOPE}: total=${report.total} (L:${report.local_total}/S:${report.shared_total}) · archive=${report.archived_total} (L:${report.local_archived_total}/S:${report.shared_archived_total}) · cleanup L:${localCleanup} S:${sharedCleanup}`;
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
      node.textContent = `Кокпіт(${namespace}): scopes=${summary.scope_count || 0} !${summary.conflicts || 0} lock=${summary.protected_blocked || 0} =${summary.result_total || 0}`;
      node.classList.toggle("empty", false);
      return;
    }
    try {
      const report = ui.buildPresetOperationsSummary({ namespace, scopes: lastPresetCockpitScopes });
      const summary = report.summary || {};
      node.textContent = `Кокпіт(${namespace}): scopes=${summary.scope_count || 0} locked=${summary.locked_count || 0} presets=${summary.presets_total || 0}`;
      node.classList.toggle("empty", false);
    } catch (_error) {
      node.textContent = "Кокпіт: —";
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
          setStatus(`Rollout ${mode} скасовано: policy lock`);
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
        setStatus(`Rollout заблоковано policy lock (${namespace})`);
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
      setStatus(`ПОМИЛКА preview кокпіта: ${error}`);
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
      if (conflicts > 0 && !window.confirm(`Кокпіт: конфлікти=${conflicts}. Продовжити ${mode}?`)) {
        setStatus(`Кокпіт ${mode} скасовано: конфлікти=${conflicts}`);
        return;
      }
      if (mode === "replace" && drops > 0 && !window.confirm(`Кокпіт replace видалить ${drops} пресет(ів). Підтвердити?`)) {
        setStatus(`Кокпіт replace скасовано: drop=${drops}`);
        return;
      }
      let allowProtectedWrite = false;
      if (blocked > 0) {
        const phrase = String(window.prompt(`Кокпіт заблоковано policy (${blocked}). Введіть UNLOCK для продовження:`, "") || "").trim().toUpperCase();
        if (phrase !== "UNLOCK") {
          setStatus(`Кокпіт ${mode} скасовано: policy lock`);
          return;
        }
        allowProtectedWrite = true;
      }
      const result = ui.applyPresetOperations(raw, { namespace, mode, scopes, allowProtectedWrite });
      loadPresetSelect("");
      setStatus(`Кокпіт ${mode}: imported=${result.result && result.result.imported ? result.result.imported : 0}, total=${result.result && result.result.total ? result.result.total : 0}, conflicts=${conflicts}, blocked=${blocked}`);
      refreshPresetSummary();
      refreshPresetTimelineHint();
      refreshPresetMergeHint();
      refreshPresetPolicyHint();
      refreshPresetCockpitHint();
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Кокпіт заблоковано policy lock (${namespace})`);
        refreshPresetPolicyHint();
      } else {
        setStatus(`ПОМИЛКА apply кокпіта: ${error}`);
      }
    }
  }
  function setPresetCockpitLockBatch(locked) {
    const namespace = selectedPresetNamespace();
    const scopes = requestCockpitScopes();
    if (!locked) {
      const phrase = String(window.prompt(`Підтвердіть UNLOCK batch для ${scopes.join(",")} (${namespace}):`, "") || "").trim().toUpperCase();
      if (phrase !== "UNLOCK") {
        setStatus("Batch unlock скасовано");
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
    document.getElementById("central").value = String(source.central || "");
    document.getElementById("code").value = String(source.code || "");
    document.getElementById("q").value = String(source.q || "");
    document.getElementById("statusFilter").value = String(source.status || "all");
    document.getElementById("severityFilter").value = String(source.severity || "all");
    document.getElementById("slaOnly").checked = !!source.slaOnly;
    document.getElementById("resolvedToggle").checked = !!source.includeResolved;
  }
  function loadPresetSelect(selectedName) {
    const presets = ui.listPresets(PRESET_SCOPE, { namespace: selectedPresetNamespace() });
    const select = document.getElementById("presetSelect");
    const prev = selectedName || select.value || "";
    select.innerHTML = '<option value="">пресети інцидентів</option>';
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
    const name = String(window.prompt("Назва пресету інцидентів:", selected || "") || "").trim();
    if (!name) return;
    try {
      ui.savePreset(PRESET_SCOPE, name, collectPresetPayload(), { namespace });
      loadPresetSelect(name);
      setStatus(`Пресет збережено (${namespace}): ${name}`);
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Заборонено policy lock (${namespace}): unlock потрібен для overwrite protected preset`);
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
        setStatus(`Заборонено policy lock (${namespace}): delete protected preset заблоковано`);
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
        setStatus(`Імпорт заблоковано policy lock (${namespace}): захищені пресети`);
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
    setStatus(`Профілі (${namespace}): додано=${result.installed}, всього=${result.total}, protected_skip=${result.skipped_protected || 0}`);
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
    setStatus(`Cleanup (${namespace}): видалено=${result.removed}, залишилось=${result.kept}, archive=${result.archived_total}`);
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
  function openIncidentsCommandPalette() {
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
      title: "Команди інцидентів",
      commands: [
        { title: "Фокус: відкриті", subtitle: "status=open, include_resolved=0", run: () => applyIncidentPreset("open") },
        { title: "Фокус: критичні", subtitle: "severity=bad", run: () => applyIncidentPreset("bad") },
        { title: "Фокус: SLA порушення", subtitle: "sla_breached_only=1", run: () => applyIncidentPreset("sla") },
        { title: "Фокус: заглушені", subtitle: "status=silenced", run: () => applyIncidentPreset("silenced") },
        { title: "Скинути фільтри", subtitle: "Повернути стандартний режим", run: () => applyIncidentPreset("reset") },
        { title: "Зберегти поточний пресет", subtitle: "Зберегти набір фільтрів у localStorage", run: saveCurrentPreset },
        { title: "Простір: локальні", subtitle: "Переключити на локальні пресети", run: () => { document.getElementById("presetNamespace").value = "local"; loadPresetSelect(""); } },
        { title: "Простір: спільні", subtitle: "Переключити на спільний простір пресетів", run: () => { document.getElementById("presetNamespace").value = "shared"; loadPresetSelect(""); } },
        { title: "Політика: розблокувати", subtitle: "Вимкнути блокування для захищених пресетів", run: unlockPresetPolicy },
        { title: "Політика: заблокувати", subtitle: "Увімкнути блокування для захищених пресетів", run: lockPresetPolicy },
        { title: "Експорт пресетів", subtitle: "Вивантажити JSON у буфер/діалог", run: exportPresetData },
        { title: "Попередній перегляд merge", subtitle: "Симуляція merge без запису", run: () => previewPresetImport("merge") },
        { title: "Імпорт merge", subtitle: "Застосувати merge імпорт", run: () => importPresetData("merge") },
        { title: "Імпорт replace", subtitle: "Застосувати replace імпорт", run: () => importPresetData("replace") },
        { title: "Кокпіт: preview", subtitle: "Batch preview по scope", run: () => previewPresetCockpit("merge") },
        { title: "Кокпіт: apply merge", subtitle: "Batch apply merge по scope", run: () => applyPresetCockpit("merge") },
        { title: "Кокпіт: apply replace", subtitle: "Batch apply replace по scope", run: () => applyPresetCockpit("replace") },
        { title: "Кокпіт: панель таймлайна", subtitle: "Фільтри scope/action/namespace", run: showPresetCockpitTimelinePanel },
        { title: "Розгортання: assistant merge", subtitle: "Safe apply protocol (merge)", run: () => runPresetRolloutAssistant("merge") },
        { title: "Розгортання: assistant replace", subtitle: "Safe apply protocol (replace)", run: () => runPresetRolloutAssistant("replace") },
        { title: "Розгортання: останній summary", subtitle: "Останній результат розгортання", run: showLastPresetRolloutSummary },
        { title: "Кокпіт: policy unlock batch", subtitle: "Batch unlock для scope", run: () => setPresetCockpitLockBatch(false) },
        { title: "Кокпіт: policy lock batch", subtitle: "Batch lock для scope", run: () => setPresetCockpitLockBatch(true) },
        { title: "Встановити профілі scope", subtitle: "Додати стандартні профілі для incidents", run: installScopeProfiles },
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
    if (context.code) document.getElementById("statusFilter").value = "all";
    refreshWorkspaceHint();
    syncQueryFromFilters();
    refresh();
  }
  function setDisabled(id, disabled) {
    ui.setDisabled(id, disabled);
  }
  function syncDensityBadge(mode) {
    const label = ui.densityLabel(mode);
    document.getElementById("densityBadge").textContent = `щільність: ${label}`;
  }
  function applyRoleUi() {
    document.getElementById("roleBadge").textContent = `роль: ${adminRole}`;
    const bulkDisabled = !adminCaps.operate;
    setDisabled("bulkAck", bulkDisabled);
    setDisabled("bulkSilence", bulkDisabled);
    setDisabled("bulkUnsilence", bulkDisabled);
    updateSelectionUi();
  }
  function setIncFilterState(level, text) {
    const node = document.getElementById("incFilterState");
    node.className = `filterState ${level}`;
    node.textContent = text;
  }
  function setQuickButtonState(id, active) {
    const element = document.getElementById(id);
    if (!element) return;
    if (active) element.classList.add("active");
    else element.classList.remove("active");
  }
  function syncIncidentQuickFilters() {
    const statusFilter = val("statusFilter").toLowerCase();
    const severityFilter = val("severityFilter").toLowerCase();
    const slaOnly = !!document.getElementById("slaOnly").checked;
    const includeResolved = !!document.getElementById("resolvedToggle").checked;
    const isOpenFocus = statusFilter === "open" && severityFilter === "all" && !slaOnly && !includeResolved;
    const isBadFocus = severityFilter === "bad" && statusFilter === "all" && !slaOnly && !includeResolved;
    const isSlaFocus = slaOnly && statusFilter === "all" && severityFilter === "all";
    const isSilencedFocus = statusFilter === "silenced" && severityFilter === "all" && !slaOnly;
    const isResetFocus = statusFilter === "all" && severityFilter === "all" && !slaOnly && includeResolved && !val("central") && !val("code") && !val("q");
    setQuickButtonState("quickOpen", isOpenFocus);
    setQuickButtonState("quickBad", isBadFocus);
    setQuickButtonState("quickSla", isSlaFocus);
    setQuickButtonState("quickSilenced", isSilencedFocus);
    setQuickButtonState("quickReset", isResetFocus);
  }
  function applyIncidentPreset(mode) {
    const statusFilter = document.getElementById("statusFilter");
    const severityFilter = document.getElementById("severityFilter");
    const slaOnly = document.getElementById("slaOnly");
    const includeResolved = document.getElementById("resolvedToggle");
    if (mode === "open") {
      statusFilter.value = "open";
      severityFilter.value = "all";
      slaOnly.checked = false;
      includeResolved.checked = false;
    } else if (mode === "bad") {
      statusFilter.value = "all";
      severityFilter.value = "bad";
      slaOnly.checked = false;
      includeResolved.checked = false;
    } else if (mode === "sla") {
      statusFilter.value = "all";
      severityFilter.value = "all";
      slaOnly.checked = true;
      includeResolved.checked = false;
    } else if (mode === "silenced") {
      statusFilter.value = "silenced";
      severityFilter.value = "all";
      slaOnly.checked = false;
      includeResolved.checked = true;
    } else {
      statusFilter.value = "all";
      severityFilter.value = "all";
      slaOnly.checked = false;
      includeResolved.checked = true;
      document.getElementById("central").value = "";
      document.getElementById("code").value = "";
      document.getElementById("q").value = "";
    }
    syncQueryFromFilters();
    syncFilterSummary();
    refresh();
  }
  async function loadWhoami() {
    const data = await ui.loadWhoami();
    adminRole = data.role;
    adminCaps = data.capabilities || { read: true, operate: false, admin: false };
    applyRoleUi();
  }
  function fmtAge(sec) {
    if (sec === null || sec === undefined) return "—";
    if (sec < 0) return "—";
    const m = Math.floor(sec / 60);
    const h = Math.floor(m / 60);
    const d = Math.floor(h / 24);
    if (d > 0) return `${d}д ${h%24}г`;
    if (h > 0) return `${h}г ${m%60}хв`;
    return `${m}хв ${sec%60}с`;
  }
  function severityLabel(level) {
    const normalized = String(level || "").toLowerCase();
    if (normalized === "good") return "СПРАВНО";
    if (normalized === "warn") return "ПОПЕРЕДЖЕННЯ";
    return "КРИТИЧНО";
  }
  function statusLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "open") return "ВІДКРИТО";
    if (normalized === "acked") return "ПІДТВЕРДЖЕНО";
    if (normalized === "silenced") return "ЗАГЛУШЕНО";
    if (normalized === "resolved") return "ВИРІШЕНО";
    return "ВІДКРИТО";
  }
  function notificationStatusLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "sent") return "НАДІСЛАНО";
    if (normalized === "skipped") return "ПРОПУЩЕНО";
    if (normalized === "failed") return "ПОМИЛКА";
    return "НЕВІДОМО";
  }
  function clsSeverity(level) {
    const normalized = String(level || "").toLowerCase();
    if (normalized === "good" || normalized === "warn" || normalized === "bad") return normalized;
    return "bad";
  }
  function clsStatus(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "open" || normalized === "acked" || normalized === "silenced" || normalized === "resolved") return normalized;
    return "open";
  }
  function countBy(items, key) {
    const map = {};
    for (const item of items) {
      const value = String(item?.[key] || "");
      map[value] = (map[value] || 0) + 1;
    }
    return map;
  }
  function incidentKey(centralId, code) {
    return `${String(centralId || "").toLowerCase()}::${String(code || "").toLowerCase()}`;
  }
  function isActiveIncidentStatus(status) {
    const normalized = String(status || "").toLowerCase();
    return normalized === "open" || normalized === "acked" || normalized === "silenced";
  }
  function slaSeverity(item) {
    const target = Number(item?.sla_target_sec || 0);
    const age = Number(item?.age_sec || 0);
    if (!Number.isFinite(target) || target <= 0) return "none";
    if (Boolean(item?.sla_breached)) return "bad";
    const ratio = age / target;
    if (ratio >= 1) return "bad";
    if (ratio >= 0.75) return "warn";
    return "good";
  }
  function slaHeatTitle(item) {
    const target = Number(item?.sla_target_sec || 0);
    const age = Number(item?.age_sec || 0);
    if (!Number.isFinite(target) || target <= 0) {
      return `${item.central_id || "вузол"}:${item.code || "інцидент"} · без SLA`;
    }
    const ratio = Math.max(0, Math.round((age / target) * 100));
    return `${item.central_id || "вузол"}:${item.code || "інцидент"} · ${ratio}% · ${fmtAge(age)} / ${fmtAge(target)}`;
  }
  function renderSlaHeatmap(incidents) {
    const container = document.getElementById("slaHeatmap");
    container.innerHTML = "";
    const active = (Array.isArray(incidents) ? incidents : []).filter((item) => isActiveIncidentStatus(item.status));
    const cells = active.slice(0, 280);
    let good = 0;
    let warn = 0;
    let bad = 0;
    let none = 0;
    for (const item of active) {
      const severity = slaSeverity(item);
      if (severity === "good") good += 1;
      else if (severity === "warn") warn += 1;
      else if (severity === "bad") bad += 1;
      else none += 1;
    }
    for (const item of cells) {
      const severity = slaSeverity(item);
      const centralId = encodeURIComponent(item.central_id || "");
      const code = encodeURIComponent(item.code || "incident");
      const cell = document.createElement("a");
      cell.className = `heatCell ${severity}`;
      cell.href = `/admin/fleet/incidents/${centralId}/${code}`;
      cell.title = slaHeatTitle(item);
      cell.dataset.workspaceCentral = String(item.central_id || "");
      cell.dataset.workspaceCode = String(item.code || "incident");
      cell.addEventListener("click", () => {
        rememberIncidentContext(item.central_id || "", item.code || "incident", "incidents/heatmap");
      });
      container.appendChild(cell);
    }
    document.getElementById("heatGood").textContent = `зелена зона: ${good}`;
    document.getElementById("heatWarn").textContent = `ризик: ${warn}`;
    document.getElementById("heatBad").textContent = `порушено: ${bad}`;
    document.getElementById("heatNone").textContent = `без SLA: ${none}`;
    if (active.length === 0) {
      container.innerHTML = '<span class="muted">Немає активних інцидентів для теплокарти</span>';
    }
  }
  function updateSelectionUi() {
    const selectedVisible = visibleKeys.filter((key) => selectedKeys.has(key)).length;
    document.getElementById("selCount").textContent = `обрано: ${selectedKeys.size}`;
    const selectAll = document.getElementById("selectAll");
    const allSelected = visibleKeys.length > 0 && selectedVisible === visibleKeys.length;
    selectAll.checked = allSelected;
    selectAll.indeterminate = selectedVisible > 0 && selectedVisible < visibleKeys.length;
    const hasSelected = selectedKeys.size > 0;
    setDisabled("bulkAck", !adminCaps.operate || !hasSelected);
    setDisabled("bulkSilence", !adminCaps.operate || !hasSelected);
    setDisabled("bulkUnsilence", !adminCaps.operate || !hasSelected);
  }
  function clearSelection() {
    selectedKeys.clear();
    updateSelectionUi();
  }
  function toggleSelectAll(checked) {
    if (checked) {
      for (const key of visibleKeys) selectedKeys.add(key);
    } else {
      for (const key of visibleKeys) selectedKeys.delete(key);
    }
    updateSelectionUi();
  }
  function bulkActionLabel(action) {
    if (action === "ack") return "підтвердження";
    if (action === "silence") return "заглушення";
    if (action === "unsilence") return "зняття заглушення";
    return action;
  }
  async function apiPost(path, payload) {
    return ui.apiPost(path, payload);
  }
  async function runBulk(action) {
    if (!adminCaps.operate) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    const keys = Array.from(selectedKeys).filter((key) => currentIncidentMap.has(key));
    if (keys.length === 0) { setStatus("Немає вибраних інцидентів"); return; }
    const timing = await ui.runActionWithLatency(async () => {
      setStatus(`Виконую ${bulkActionLabel(action)} для ${keys.length} інцидентів...`);
      const requests = keys.map((key) => {
        const incident = currentIncidentMap.get(key);
        const payload = {
          central_id: incident.central_id,
          code: incident.code,
          actor: "admin-ui",
        };
        if (action === "ack") {
          return apiPost("/api/admin/fleet/alerts/ack", { ...payload, note: "масове підтвердження з /admin/fleet/incidents" });
        }
        if (action === "silence") {
          return apiPost("/api/admin/fleet/alerts/silence", { ...payload, duration_sec: 3600, note: "масове заглушення 1г з /admin/fleet/incidents" });
        }
        return apiPost("/api/admin/fleet/alerts/unsilence", { ...payload, note: "масове зняття заглушення з /admin/fleet/incidents" });
      });
      return Promise.allSettled(requests);
    });
    if (!timing.ok) {
      setStatus(`ПОМИЛКА масової дії (${ui.formatLatency(timing.elapsed_ms)}): ${timing.error}`);
      return;
    }
    const results = Array.isArray(timing.result) ? timing.result : [];
    const ok = results.filter((result) => result.status === "fulfilled").length;
    const failed = results.length - ok;
    const firstIncident = currentIncidentMap.get(keys[0]);
    if (firstIncident) {
      rememberIncidentContext(firstIncident.central_id, firstIncident.code, `incidents/${action}`);
    }
    selectedKeys.clear();
    await refresh();
    setStatus(`Масова дія (${bulkActionLabel(action)}): успіх=${ok}, помилки=${failed}, час=${ui.formatLatency(timing.elapsed_ms)}`);
  }
  function setSelectIfValid(id, value) {
    const element = document.getElementById(id);
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized) return;
    const values = Array.from(element.options || []).map((item) => String(item.value || "").toLowerCase());
    if (values.includes(normalized)) {
      element.value = normalized;
    }
  }
  function boolFromQuery(value, fallback) {
    if (value === null || value === undefined) return fallback;
    const normalized = String(value).trim().toLowerCase();
    if (normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on") return true;
    if (normalized === "0" || normalized === "false" || normalized === "no" || normalized === "off") return false;
    return fallback;
  }
  function initFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const central = params.get("central") || params.get("central_id");
    const code = params.get("code");
    const query = params.get("q");
    if (central) document.getElementById("central").value = central;
    if (code) document.getElementById("code").value = code;
    if (query) document.getElementById("q").value = query;
    setSelectIfValid("statusFilter", params.get("status") || "all");
    setSelectIfValid("severityFilter", params.get("severity") || "all");
    const slaOnly = params.get("slaOnly") ?? params.get("sla_breached_only");
    const includeResolved = params.get("includeResolved") ?? params.get("include_resolved");
    document.getElementById("slaOnly").checked = boolFromQuery(slaOnly, false);
    document.getElementById("resolvedToggle").checked = boolFromQuery(includeResolved, true);
    document.getElementById("auto").checked = boolFromQuery(params.get("auto"), true);
  }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const params = new URLSearchParams();
      params.set("limit", "500");
      const statusFilter = val("statusFilter").toLowerCase();
      const severityFilter = val("severityFilter").toLowerCase();
      const central = val("central");
      const code = val("code");
      const query = val("q");
      const includeResolved = !!document.getElementById("resolvedToggle").checked;
      const slaOnly = !!document.getElementById("slaOnly").checked;
      if (statusFilter && statusFilter !== "all") params.set("status", statusFilter);
      if (severityFilter && severityFilter !== "all") params.set("severity", severityFilter);
      if (central) params.set("central_id", central);
      if (code) params.set("code", code);
      if (query) params.set("q", query);
      params.set("include_resolved", includeResolved ? "1" : "0");
      params.set("sla_breached_only", slaOnly ? "1" : "0");

      const incResp = await fetch(`/api/admin/fleet/incidents?${params.toString()}`);
      const incText = await incResp.text();
      if (!incResp.ok) throw new Error(`${incResp.status} ${incText}`);
      const incData = JSON.parse(incText);
      const incidents = Array.isArray(incData.incidents) ? incData.incidents : [];
      currentIncidentMap = new Map();
      visibleKeys = [];
      for (const item of incidents) {
        const key = incidentKey(item.central_id, item.code || "alert");
        currentIncidentMap.set(key, item);
      }
      for (const key of Array.from(selectedKeys)) {
        if (!currentIncidentMap.has(key)) selectedKeys.delete(key);
      }
      renderSlaHeatmap(incidents);

      const notifParams = new URLSearchParams();
      notifParams.set("limit", "200");
      if (central) notifParams.set("central_id", central);
      if (code) notifParams.set("code", code);
      if (query) notifParams.set("q", query);
      const notifResp = await fetch(`/api/admin/fleet/incidents/notifications?${notifParams.toString()}`);
      const notifText = await notifResp.text();
      if (!notifResp.ok) throw new Error(`${notifResp.status} ${notifText}`);
      const notifData = JSON.parse(notifText);
      const notifications = Array.isArray(notifData.notifications) ? notifData.notifications : [];

      const statusCounts = countBy(incidents, "status");
      const severityCounts = countBy(incidents, "severity");
      const slaBreached = incidents.filter((item) => !!item.sla_breached).length;
      document.getElementById("sumTotal").textContent = `всього: ${incidents.length}`;
      document.getElementById("sumOpen").textContent = `відкриті: ${statusCounts.open || 0}`;
      document.getElementById("sumAcked").textContent = `підтверджені: ${statusCounts.acked || 0}`;
      document.getElementById("sumSilenced").textContent = `заглушені: ${statusCounts.silenced || 0}`;
      document.getElementById("sumResolved").textContent = `вирішені: ${statusCounts.resolved || 0}`;
      document.getElementById("sumBad").textContent = `критичні: ${severityCounts.bad || 0}`;
      document.getElementById("sumWarn").textContent = `попередження: ${severityCounts.warn || 0}`;
      document.getElementById("sumGood").textContent = `справні: ${severityCounts.good || 0}`;
      document.getElementById("sumSla").textContent = `Порушення SLA: ${slaBreached}`;
      document.getElementById("kpiOpen").textContent = String(statusCounts.open || 0);
      document.getElementById("kpiBad").textContent = String(severityCounts.bad || 0);
      document.getElementById("kpiWarn").textContent = String(severityCounts.warn || 0);
      document.getElementById("kpiSla").textContent = String(slaBreached);
      const filterParts = [];
      if (statusFilter !== "all") filterParts.push(`статус=${statusFilter}`);
      if (severityFilter !== "all") filterParts.push(`рівень=${severityFilter}`);
      if (slaOnly) filterParts.push("лише порушення SLA");
      if (!includeResolved) filterParts.push("без вирішених");
      if (central) filterParts.push(`вузол=${central}`);
      if (code) filterParts.push(`код=${code}`);
      if (query) filterParts.push(`пошук=${query}`);
      let filterLevel = "good";
      if (severityFilter === "bad" || slaOnly) filterLevel = "bad";
      else if (statusFilter !== "all" || !includeResolved || !!central || !!code || !!query) filterLevel = "warn";
      setIncFilterState(filterLevel, filterParts.length ? `Фільтри: ${filterParts.join(" · ")}` : "Фільтри: стандартний режим");
      syncIncidentQuickFilters();

      const incBody = document.querySelector("#incTbl tbody");
      incBody.innerHTML = "";
      if (incidents.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = '<td colspan="10"><span class="badge good">OK</span> Інцидентів за вибраними фільтрами немає</td>';
        incBody.appendChild(row);
      } else {
        for (const item of incidents) {
          const row = document.createElement("tr");
          const statusClass = clsStatus(item.status);
          const severityClass = clsSeverity(item.severity);
          const centralId = String(item.central_id || "");
          const incidentCode = String(item.code || "alert");
          const key = incidentKey(centralId, incidentCode);
          visibleKeys.push(key);
          const stateBits = [];
          if (item.acked_at) stateBits.push(`<span class="badge">підтв.=${esc(item.acked_by || "—")}</span>`);
          if (item.silenced_until) stateBits.push(`<span class="badge warn">до=${esc(item.silenced_until)}</span>`);
            if (item.sla_breached) stateBits.push('<span class="badge bad">Порушення SLA</span>');
          const checked = selectedKeys.has(key) ? "checked" : "";
          row.innerHTML = `
            <td class="checkCol"><input type="checkbox" data-select-key="${esc(key)}" ${checked} /></td>
            <td><span class="badge status-badge ${statusClass}">${esc(statusLabel(statusClass))}</span></td>
            <td><span class="badge ${severityClass}">${esc(severityLabel(severityClass))}</span></td>
            <td><a href="/admin/fleet/central/${encodeURIComponent(centralId)}"><code>${esc(centralId || "—")}</code></a></td>
            <td><a data-workspace-incident-link="1" href="/admin/fleet/incidents/${encodeURIComponent(centralId)}/${encodeURIComponent(incidentCode)}"><code>${esc(incidentCode)}</code></a></td>
            <td><code>${fmtAge(item.age_sec)}</code><div class="muted">випадків=${esc(item.occurrences ?? 0)}</div></td>
            <td><code>${fmtAge(item.sla_target_sec)}</code></td>
            <td><code>${esc(item.first_seen_ts || "—")}</code><div class="muted"><code>${esc(item.last_seen_ts || "—")}</code></div></td>
            <td>${esc(item.message || "")}</td>
            <td>${stateBits.join(" ") || '<span class="badge">—</span>'}</td>
          `;
          row.querySelector('a[data-workspace-incident-link="1"]')?.addEventListener("click", () => {
            rememberIncidentContext(centralId, incidentCode, "incidents/list");
          });
          row.querySelector('input[data-select-key]')?.addEventListener("change", (event) => {
            const checkbox = event.currentTarget;
            const selected = !!checkbox.checked;
            if (selected) selectedKeys.add(key);
            else selectedKeys.delete(key);
            updateSelectionUi();
          });
          incBody.appendChild(row);
        }
      }
      updateSelectionUi();

      const notifBody = document.querySelector("#notifTbl tbody");
      notifBody.innerHTML = "";
      if (notifications.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = '<td colspan="8"><span class="badge">—</span> Журнал відправлень порожній</td>';
        notifBody.appendChild(row);
      } else {
        for (const item of notifications) {
          const row = document.createElement("tr");
          const st = String(item.status || "").toLowerCase();
          const statusClass = st === "sent" ? "good" : (st === "skipped" ? "warn" : "bad");
          row.innerHTML = `
            <td><code>${esc(item.ts || "—")}</code></td>
            <td><span class="badge ${statusClass}">${esc(notificationStatusLabel(st))}</span></td>
            <td><code>${esc(item.channel || "—")}</code></td>
            <td><code>${esc(item.event || "—")}</code></td>
            <td><code>${esc(item.central_id || "—")}</code></td>
            <td><code>${esc(item.code || "—")}</code></td>
            <td><code>${esc(item.destination || "—")}</code></td>
            <td><code>${esc(item.error || "—")}</code></td>
          `;
          notifBody.appendChild(row);
        }
      }

      document.getElementById("updatedAt").textContent = `оновлено: ${new Date().toLocaleString("uk-UA")}`;
      setStatus(`OK: інцидентів=${incidents.length}, сповіщень=${notifications.length}, лише_sla=${slaOnly ? "увімкнено" : "вимкнено"}`);
    } catch (error) {
      setStatus(`ПОМИЛКА: ${error}`);
    }
  }
  document.getElementById("refresh").addEventListener("click", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  document.getElementById("central").addEventListener("input", scheduleRefresh);
  document.getElementById("code").addEventListener("input", scheduleRefresh);
  document.getElementById("q").addEventListener("input", scheduleRefresh);
  document.getElementById("statusFilter").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("severityFilter").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("slaOnly").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("resolvedToggle").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("clearFilters").addEventListener("click", clearFilters);
  document.getElementById("selectAll").addEventListener("change", (event) => toggleSelectAll(!!event.target.checked));
  document.getElementById("clearSelection").addEventListener("click", () => clearSelection());
  document.getElementById("bulkAck").addEventListener("click", () => runBulk("ack"));
  document.getElementById("bulkSilence").addEventListener("click", () => runBulk("silence"));
  document.getElementById("bulkUnsilence").addEventListener("click", () => runBulk("unsilence"));
  document.getElementById("quickOpen").addEventListener("click", () => applyIncidentPreset("open"));
  document.getElementById("quickBad").addEventListener("click", () => applyIncidentPreset("bad"));
  document.getElementById("quickSla").addEventListener("click", () => applyIncidentPreset("sla"));
  document.getElementById("quickSilenced").addEventListener("click", () => applyIncidentPreset("silenced"));
  document.getElementById("quickReset").addEventListener("click", () => applyIncidentPreset("reset"));
  document.getElementById("workspaceApply").addEventListener("click", applyWorkspaceContext);
  document.getElementById("workspaceClear").addEventListener("click", () => { ui.clearWorkspaceContext(); refreshWorkspaceHint(); });
  document.getElementById("cmdPaletteOpen").addEventListener("click", openIncidentsCommandPalette);
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
  ui.bindEnterRefresh(["central", "code", "q"], () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  ui.bindCommandPalette(openIncidentsCommandPalette);
  initSecondaryDetails();
  initToolsDetails();
  const densityMode = ui.initDensityMode("density", {
    storageKey: "fleet_incidents_density",
    className: "density-compact",
    onChange: syncDensityBadge,
  });
  syncDensityBadge(densityMode);
  initFromQuery();
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
        title="Адмін-панель Passengers — Інциденти",
        header_title='Інциденти флоту',
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        max_width=1360,
        extra_css=extra_css,
        current_nav="incidents",
    )
