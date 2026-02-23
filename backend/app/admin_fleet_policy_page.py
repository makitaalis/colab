from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_policy_page() -> str:
    chips_html = """
        <span class="chip">пороги дашборда + health API</span>
        <span class="chip mono" id="whoami">роль: —</span>
        <span class="chip mono" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
      <div class="toolbarMain">
        <button id="copyLink" title="Скопіювати поточне посилання (з урахуванням контексту)">Скопіювати посилання</button>
      </div>
      <div class="toolbarMeta">
        <span class="metaChip sort" id="filterSummary">контекст: —</span>
      </div>
    """
    extra_css = """
    .sectionTitle { font-weight: 700; }
    """.strip()
    body_html = """
    <div class="card">
      <div class="sectionHead">
        <div class="sectionTitle">Глобальна політика моніторингу</div>
        <div class="sectionTools">
          <a class="quickLink" href="/admin/fleet/history">Історія KPI</a>
          <a class="quickLink" href="/admin/audit">Аудит</a>
          <a class="quickLink" href="/admin/fleet/notifications">Правила сповіщень</a>
        </div>
      </div>
      <div class="summary">
        <span class="badge bad">КРИТИЧНО (bad)</span>
        <span class="badge warn">ПОПЕРЕДЖЕННЯ (warn)</span>
        <span class="badge good">СПРАВНО (good)</span>
      </div>
      <div class="tableMeta">
        <span class="metaChip source">API: <code>/api/admin/fleet/monitor-policy</code> + <code>/api/admin/fleet/health/notify-auto</code></span>
      </div>
      <div class="row">
        <label for="warnHeartbeat">Поріг попередження heartbeat (сек)</label>
        <input id="warnHeartbeat" type="number" min="30" max="3600" />
      </div>
      <div class="row">
        <label for="badHeartbeat">Поріг критично heartbeat (сек)</label>
        <input id="badHeartbeat" type="number" min="60" max="7200" />
      </div>
      <div class="row">
        <label for="warnPending">Поріг попередження черги (пакети)</label>
        <input id="warnPending" type="number" min="1" max="1000" />
      </div>
      <div class="row">
        <label for="badPending">Поріг критично черги (пакети)</label>
        <input id="badPending" type="number" min="1" max="5000" />
      </div>
      <div class="row">
        <label for="warnWg">Поріг попередження WG (сек)</label>
        <input id="warnWg" type="number" min="30" max="3600" />
      </div>
      <div class="row">
        <label for="badWg">Поріг критично WG (сек)</label>
        <input id="badWg" type="number" min="60" max="7200" />
      </div>
      <div class="toolbar uJcStart uMt12">
        <button id="refresh">Оновити</button>
        <button id="save" class="primary">Зберегти</button>
      </div>
      <div class="domainSplitHint">Політика застосовується в <code>/api/admin/fleet/monitor</code>, <code>/api/admin/fleet/health</code> та у блоці <code>Потребує дій</code>.</div>
      <div class="status" id="status"></div>
    </div>

    <details id="policyAutoDetails" class="domainSplitDetails" data-advanced-details="1">
      <summary>Авто-сповіщення health флоту (advanced)</summary>
      <div class="domainSplitHint">Авто-модуль використовує глобальні пороги вище. Тут налаштовується канал, вікно аналізу та cadence.</div>
      <div class="row">
        <label for="autoEnabled">Увімкнути авто-сповіщення</label>
        <input id="autoEnabled" type="checkbox" />
      </div>
      <div class="row">
        <label for="autoChannel">Канал авто-сповіщень</label>
        <select id="autoChannel">
          <option value="auto" selected>автовибір</option>
          <option value="telegram">Telegram</option>
          <option value="email">Email</option>
          <option value="all">усі канали</option>
        </select>
      </div>
      <div class="row">
        <label for="autoWindow">Вікно авто-аналізу</label>
        <select id="autoWindow">
          <option value="1h">1 година</option>
          <option value="6h">6 годин</option>
          <option value="24h" selected>24 години</option>
          <option value="7d">7 днів</option>
        </select>
      </div>
      <div class="row">
        <label for="autoMinSeverity">Мінімальний рівень для авто-сповіщень</label>
        <select id="autoMinSeverity">
          <option value="bad" selected>критично (bad)</option>
          <option value="warn">попередження (warn)</option>
          <option value="good">усі події (good)</option>
        </select>
      </div>
      <div class="row">
        <label for="autoMinInterval">Мінімальний інтервал між авто-сповіщеннями (сек)</label>
        <input id="autoMinInterval" type="number" min="60" max="86400" />
      </div>
      <div class="row">
        <label for="autoRecovery">Надсилати сповіщення про відновлення</label>
        <input id="autoRecovery" type="checkbox" />
      </div>
      <div class="toolbar uJcStart uMt12">
        <button id="autoDry">Авто зараз (dry-run)</button>
        <button id="autoNow">Авто зараз</button>
      </div>
      <div class="status" id="autoStatus"></div>
    </div>

    <details id="policySecondaryDetails" class="domainSplitDetails" data-advanced-details="1">
      <summary>Персональні override-и (вторинний контур)</summary>
      <div class="domainSplitHint">
        Використовуйте override-и тільки для вузлів з нестандартним профілем ризику. Базовий сценарій керується глобальною політикою вище.
      </div>
      <div class="sectionTitle uMt8">Персональні override-и</div>
      <div class="hint">Перевизначає лише пороги для конкретного <code>central_id</code>. Якщо override відсутній — використовується глобальна політика.</div>
      <div class="row">
        <label for="ovCentral">ID вузла</label>
        <input id="ovCentral" type="text" placeholder="central-gw" />
      </div>
      <div class="row">
        <label for="ovWarnHeartbeat">Попередження heartbeat (сек)</label>
        <input id="ovWarnHeartbeat" type="number" min="30" max="3600" />
      </div>
      <div class="row">
        <label for="ovBadHeartbeat">Критично heartbeat (сек)</label>
        <input id="ovBadHeartbeat" type="number" min="60" max="7200" />
      </div>
      <div class="row">
        <label for="ovWarnPending">Попередження черги (пакети)</label>
        <input id="ovWarnPending" type="number" min="1" max="1000" />
      </div>
      <div class="row">
        <label for="ovBadPending">Критично черги (пакети)</label>
        <input id="ovBadPending" type="number" min="1" max="5000" />
      </div>
      <div class="row">
        <label for="ovWarnWg">Попередження WG (сек)</label>
        <input id="ovWarnWg" type="number" min="30" max="3600" />
      </div>
      <div class="row">
        <label for="ovBadWg">Критично WG (сек)</label>
        <input id="ovBadWg" type="number" min="60" max="7200" />
      </div>
      <div class="toolbar uJcStart uMt12">
        <button id="ovRefresh">Оновити override-и</button>
        <button id="ovUpsert" class="primary">Зберегти override</button>
        <button id="ovDelete">Видалити override</button>
      </div>
      <div class="status" id="ovStatus"></div>
      <div class="tableWrap uMaxH40vh">
        <table id="ovTbl" style="min-width:760px;">
          <thead>
            <tr>
              <th>ID вузла</th>
              <th>heartbeat попер./крит.</th>
              <th>черга попер./крит.</th>
              <th>wg попер./крит.</th>
              <th>оновлено</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </details>
    """
    script = """
  const ui = window.AdminUiKit;
  const POLICY_SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_policy_secondary_details_v1";
  const POLICY_AUTO_DETAILS_STORAGE_KEY = "passengers_admin_policy_auto_details_v1";
  let adminCaps = { read: true, operate: false, admin: false };
  function setStatus(s) { ui.setStatus("status", s); }
  function setAutoStatus(s) { ui.setStatus("autoStatus", s); }
  function setOvStatus(s) { ui.setStatus("ovStatus", s); }
  function setDisabled(id, disabled) { ui.setDisabled(id, disabled); }
  function toInt(id, fallback) { return ui.intVal(id, fallback); }
  function toOptInt(id) { return ui.optInt(id); }
  async function apiGet(path) { return ui.apiGet(path); }
  async function apiPost(path, payload) { return ui.apiPost(path, payload); }
  async function apiDelete(path) { return ui.apiDelete(path); }
  function applyUi() {
    const adminDisabled = !adminCaps.admin;
    for (const id of [
      "warnHeartbeat","badHeartbeat","warnPending","badPending","warnWg","badWg",
      "autoEnabled","autoChannel","autoWindow","autoMinSeverity","autoMinInterval","autoRecovery","save"
    ]) setDisabled(id, adminDisabled);
    for (const id of ["ovCentral","ovWarnHeartbeat","ovBadHeartbeat","ovWarnPending","ovBadPending","ovWarnWg","ovBadWg","ovUpsert","ovDelete"]) setDisabled(id, adminDisabled);
    const operatorDisabled = !adminCaps.operate;
    setDisabled("autoDry", operatorDisabled);
    setDisabled("autoNow", operatorDisabled);
  }
  async function loadWhoami() {
    const data = await ui.loadWhoami();
    ui.setText("whoami", `роль: ${data.role || "viewer"} · актор: ${data.actor || "невідомо"}`);
    adminCaps = data.capabilities || { read: true, operate: false, admin: false };
    applyUi();
  }
  function initPolicySecondaryDetails() {
    const node = document.getElementById("policySecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {
      const raw = String(localStorage.getItem(POLICY_SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {}
    node.addEventListener("toggle", () => {
      try { localStorage.setItem(POLICY_SECONDARY_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); } catch (_error) {}
    });
  }
  function initPolicyAutoDetails() {
    const node = document.getElementById("policyAutoDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {
      const raw = String(localStorage.getItem(POLICY_AUTO_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {}
    node.addEventListener("toggle", () => {
      try { localStorage.setItem(POLICY_AUTO_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); } catch (_error) {}
    });
  }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const data = await apiGet("/api/admin/fleet/monitor-policy");
      const p = data.policy || {};
      document.getElementById("warnHeartbeat").value = p.warn_heartbeat_age_sec ?? 120;
      document.getElementById("badHeartbeat").value = p.bad_heartbeat_age_sec ?? 600;
      document.getElementById("warnPending").value = p.warn_pending_batches ?? 1;
      document.getElementById("badPending").value = p.bad_pending_batches ?? 50;
      document.getElementById("warnWg").value = p.warn_wg_age_sec ?? 300;
      document.getElementById("badWg").value = p.bad_wg_age_sec ?? 1200;
      document.getElementById("autoEnabled").checked = !!p.fleet_health_auto_enabled;
      document.getElementById("autoChannel").value = p.fleet_health_auto_channel || "auto";
      document.getElementById("autoWindow").value = p.fleet_health_auto_window || "24h";
      document.getElementById("autoMinSeverity").value = p.fleet_health_auto_min_severity || "bad";
      document.getElementById("autoMinInterval").value = p.fleet_health_auto_min_interval_sec ?? 900;
      document.getElementById("autoRecovery").checked = !!p.fleet_health_auto_notify_recovery;
      ui.setText("updatedAt", `оновлено: ${new Date().toLocaleString("uk-UA")}`);
      setStatus("OK");
      await refreshOverrides();
    } catch (error) {
      setStatus(`ПОМИЛКА: ${error}`);
    }
  }
  function renderOverrides(rows) {
    const tbody = document.querySelector("#ovTbl tbody");
    tbody.innerHTML = "";
    const list = Array.isArray(rows) ? rows : [];
    if (list.length === 0) {
      tbody.innerHTML = '<tr><td colspan="5"><span class="mono">немає override-ів</span></td></tr>';
      return;
    }
    for (const row of list) {
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><code>${row.central_id || "—"}</code></td>
        <td><code>${row.warn_heartbeat_age_sec ?? "—"} / ${row.bad_heartbeat_age_sec ?? "—"}</code></td>
        <td><code>${row.warn_pending_batches ?? "—"} / ${row.bad_pending_batches ?? "—"}</code></td>
        <td><code>${row.warn_wg_age_sec ?? "—"} / ${row.bad_wg_age_sec ?? "—"}</code></td>
        <td><code>${row.updated_at || "—"}</code></td>
      `;
      tr.addEventListener("click", () => {
        document.getElementById("ovCentral").value = row.central_id || "";
        document.getElementById("ovWarnHeartbeat").value = row.warn_heartbeat_age_sec ?? "";
        document.getElementById("ovBadHeartbeat").value = row.bad_heartbeat_age_sec ?? "";
        document.getElementById("ovWarnPending").value = row.warn_pending_batches ?? "";
        document.getElementById("ovBadPending").value = row.bad_pending_batches ?? "";
        document.getElementById("ovWarnWg").value = row.warn_wg_age_sec ?? "";
        document.getElementById("ovBadWg").value = row.bad_wg_age_sec ?? "";
      });
      tbody.appendChild(tr);
    }
  }
  async function refreshOverrides() {
    setOvStatus("Завантаження override-ів...");
    try {
      const data = await apiGet("/api/admin/fleet/monitor-policy/overrides?limit=2000");
      const rows = data.overrides || [];
      renderOverrides(rows);
      setOvStatus(`OK: overrides=${rows.length}`);
    } catch (error) {
      setOvStatus(`ПОМИЛКА: ${error}`);
    }
  }
  async function upsertOverride() {
    if (!adminCaps.admin) { setOvStatus("ЛИШЕ ЧИТАННЯ: потрібна роль admin"); return; }
    const centralId = (document.getElementById("ovCentral").value || "").trim();
    if (!centralId) { setOvStatus("central_id є обов'язковим"); return; }
    const payload = {
      central_id: centralId,
      warn_heartbeat_age_sec: toOptInt("ovWarnHeartbeat"),
      bad_heartbeat_age_sec: toOptInt("ovBadHeartbeat"),
      warn_pending_batches: toOptInt("ovWarnPending"),
      bad_pending_batches: toOptInt("ovBadPending"),
      warn_wg_age_sec: toOptInt("ovWarnWg"),
      bad_wg_age_sec: toOptInt("ovBadWg"),
    };
    setOvStatus("Збереження override...");
    try {
      const data = await apiPost("/api/admin/fleet/monitor-policy/overrides", payload);
      setOvStatus(`ЗБЕРЕЖЕНО: ${JSON.stringify(data.override || {})}`);
      await refreshOverrides();
    } catch (error) {
      setOvStatus(`ПОМИЛКА: ${error}`);
    }
  }
  async function deleteOverride() {
    if (!adminCaps.admin) { setOvStatus("ЛИШЕ ЧИТАННЯ: потрібна роль admin"); return; }
    const centralId = (document.getElementById("ovCentral").value || "").trim();
    if (!centralId) { setOvStatus("central_id є обов'язковим"); return; }
    setOvStatus("Видалення override...");
    try {
      await apiDelete(`/api/admin/fleet/monitor-policy/overrides/${encodeURIComponent(centralId)}`);
      setOvStatus(`ВИДАЛЕНО: ${centralId}`);
      await refreshOverrides();
    } catch (error) {
      setOvStatus(`ПОМИЛКА: ${error}`);
    }
  }
  async function save() {
    if (!adminCaps.admin) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль admin"); return; }
    setStatus("Збереження...");
    try {
      const payload = {
        warn_heartbeat_age_sec: toInt("warnHeartbeat", 120),
        bad_heartbeat_age_sec: toInt("badHeartbeat", 600),
        warn_pending_batches: toInt("warnPending", 1),
        bad_pending_batches: toInt("badPending", 50),
        warn_wg_age_sec: toInt("warnWg", 300),
        bad_wg_age_sec: toInt("badWg", 1200),
        fleet_health_auto_enabled: !!document.getElementById("autoEnabled").checked,
        fleet_health_auto_channel: (document.getElementById("autoChannel").value || "auto").trim().toLowerCase(),
        fleet_health_auto_window: (document.getElementById("autoWindow").value || "24h").trim().toLowerCase(),
        fleet_health_auto_min_severity: (document.getElementById("autoMinSeverity").value || "bad").trim().toLowerCase(),
        fleet_health_auto_min_interval_sec: toInt("autoMinInterval", 900),
        fleet_health_auto_notify_recovery: !!document.getElementById("autoRecovery").checked,
      };
      const data = await apiPost("/api/admin/fleet/monitor-policy", payload);
      setStatus(`ЗБЕРЕЖЕНО: ${JSON.stringify(data.policy || {})}`);
      await refresh();
    } catch (error) {
      setStatus(`ПОМИЛКА: ${error}`);
    }
  }
  async function runAuto(dryRun) {
    if (!adminCaps.operate) { setAutoStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    setAutoStatus(dryRun ? "Запуск авто (dry-run)..." : "Запуск авто...");
    try {
      const params = new URLSearchParams();
      if (dryRun) params.set("dry_run", "1");
      params.set("force", "1");
      const data = await apiPost(`/api/admin/fleet/health/notify-auto?${params.toString()}`, null);
      const counters = data.result?.counters || {};
      setAutoStatus(`OK: рішення=${data.decision || "?"} причина=${data.reason || "?"} надіслано=${counters.sent || 0} помилки=${counters.failed || 0} пропущено=${counters.skipped || 0}`);
    } catch (error) {
      setAutoStatus(`ПОМИЛКА: ${error}`);
    }
  }
  ui.byId("refresh").addEventListener("click", refresh);
  ui.byId("save").addEventListener("click", save);
  ui.byId("autoDry").addEventListener("click", () => runAuto(true));
  ui.byId("autoNow").addEventListener("click", () => runAuto(false));
  ui.byId("ovRefresh").addEventListener("click", refreshOverrides);
  ui.byId("ovUpsert").addEventListener("click", upsertOverride);
  ui.byId("ovDelete").addEventListener("click", deleteOverride);
  ui.byId("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const central = params.get("central") || params.get("central_id");
    if (central) document.getElementById("ovCentral").value = String(central);
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const central = String(document.getElementById("ovCentral").value || "").trim();
    if (central) params.set("central_id", central);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const central = String(document.getElementById("ovCentral").value || "").trim();
    const node = document.getElementById("filterSummary");
    if (!node) return;
    node.textContent = central ? `контекст: вузол=${central}` : "контекст: —";
  }
  ui.bindDebouncedInputs(["ovCentral"], () => { syncQueryFromFilters(); syncFilterSummary(); }, 220);
  ui.bindEnterRefresh(["ovCentral"], () => { syncQueryFromFilters(); syncFilterSummary(); });
  initPolicyAutoDetails();
  initPolicySecondaryDetails();
  applyFiltersFromQuery();
  syncQueryFromFilters();
  syncFilterSummary();
  loadWhoami().then(refresh);
    """
    return render_admin_shell(
        title="Адмін-панель Passengers — Політика моніторингу",
        header_title="Політика моніторингу",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        extra_css=extra_css,
        max_width=980,
        current_nav="policy",
    ).strip()
