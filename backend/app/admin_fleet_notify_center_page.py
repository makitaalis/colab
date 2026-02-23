from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_notify_center_page() -> str:
    chips_html = """
        <span class="chip" id="roleBadge">роль: —</span>
        <span class="chip">журнал доставки + ручний повтор</span>
        <span class="chip" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
        <div class="toolbarMain">
          <label><input id="auto" type="checkbox" checked /> авто</label>
          <button id="clearFilters">Скинути фільтри</button>
          <button id="refresh" class="primary">Оновити</button>
          <button id="copyLink" title="Скопіювати поточне посилання (з урахуванням фільтрів)">Скопіювати посилання</button>
          <details class="toolbarDetails" data-advanced-details="1">
            <summary>Фільтри</summary>
            <div class="toolbarDetailsGrid">
              <select id="window" title="вікно даних">
                <option value="1h">1 година</option>
                <option value="24h" selected>24 години</option>
                <option value="7d">7 днів</option>
              </select>
              <select id="statusFilter" title="статус доставки">
                <option value="all">усі статуси</option>
                <option value="failed">помилки</option>
                <option value="skipped">пропущені</option>
                <option value="sent">надіслані</option>
              </select>
              <select id="channelFilter" title="канал доставки">
                <option value="all">усі канали</option>
                <option value="telegram">telegram</option>
                <option value="email">email</option>
                <option value="policy">policy</option>
              </select>
              <input id="central" type="text" placeholder="ідентифікатор вузла" />
              <input id="code" type="text" placeholder="код події" />
              <input id="q" type="text" placeholder="пошук помилки/повідомлення" />
              <label><input id="dryRunRetry" type="checkbox" /> повтор (dry-run)</label>
            </div>
          </details>
        </div>
        <div class="toolbarMeta">
          <span class="metaChip sort" id="filterSummary">фільтри: стандартні</span>
          <span class="status" id="status"></span>
        </div>
    """
    extra_css = """
    #q { min-width: 280px; }
    #central { min-width: 220px; }
    #code { min-width: 180px; }
    """.strip()
    body_html = """
    <div class="card">
      <div class="sectionHead">
        <div class="sectionTitle">Оперативний огляд доставки</div>
        <div class="sectionTools">
          <a class="quickLink" href="/admin/fleet/incidents">Інциденти</a>
          <a class="quickLink" href="/admin/fleet/notifications">Правила</a>
          <a class="quickLink" href="/admin/fleet/policy">Політика</a>
        </div>
      </div>
      <div class="summary">
        <span class="badge" id="sumTotal">всього: 0</span>
        <span class="badge good" id="sumSent">надіслано: 0</span>
        <span class="badge bad" id="sumFailed">помилки: 0</span>
        <span class="badge warn" id="sumSkipped">пропущено: 0</span>
        <span class="badge" id="sumRetryable">помилки з повтором: 0</span>
      </div>
      <div class="domainSplitHint">
        Базовий triage виконуйте за агрегатами вище. Детальний журнал доставки та повторні дії винесено у секцію нижче.
      </div>
    </div>

    <details id="notifySecondaryDetails" class="domainSplitDetails" data-advanced-details="1">
      <summary>Журнал доставки та помилки (детально)</summary>
      <div class="domainSplitHint">
        Для масових збоїв спочатку перевіряйте <a class="quickLink" href="/admin/fleet/notifications">правила сповіщень</a>
        і <a class="quickLink" href="/admin/fleet/policy">політику моніторингу</a>, потім виконуйте ручний повтор у таблиці.
      </div>
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code>/api/admin/fleet/incidents/notifications</code> + <code>/api/admin/fleet/notifications/retry</code></span>
        <span class="metaChip sort" id="notifySinceChip">від: —</span>
      </div>
      <div class="tableWrap" style="max-height:68vh;">
        <table id="tbl" style="min-width:1280px;">
          <thead>
            <tr>
              <th>ID</th>
              <th>Час</th>
              <th>Статус</th>
              <th>Канал</th>
              <th>Подія</th>
              <th>Вузол</th>
              <th>Код</th>
              <th>Отримувач</th>
              <th>Помилка</th>
              <th>Дія</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </details>
    """
    script = """
  const ui = window.AdminUiKit;
  const REFRESH_DELAY_MS = 280;
  const NOTIFY_SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_notify_secondary_details_v1";
  let adminRole = "viewer";
  let adminCaps = { read: true, operate: false, admin: false };
  function setStatus(s) { ui.setStatus("status", s); }
  function applyRoleUi() {
    ui.setText("roleBadge", `роль: ${adminRole}`);
    ui.setDisabled("dryRunRetry", !adminCaps.operate);
  }
  async function loadWhoami() {
    const data = await ui.loadWhoami();
    adminRole = data.role;
    adminCaps = data.capabilities || { read: true, operate: false, admin: false };
    applyRoleUi();
  }
  function initNotifySecondaryDetails() {
    const node = document.getElementById("notifySecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {
      const raw = String(localStorage.getItem(NOTIFY_SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {}
    node.addEventListener("toggle", () => {
      try { localStorage.setItem(NOTIFY_SECONDARY_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); } catch (_error) {}
    });
  }
  function statusClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "sent") return "good";
    if (normalized === "skipped") return "warn";
    return "bad";
  }
  function statusLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "sent") return "НАДІСЛАНО";
    if (normalized === "skipped") return "ПРОПУЩЕНО";
    if (normalized === "failed") return "ПОМИЛКА";
    return "НЕВІДОМО";
  }
  function windowSeconds() { return ui.windowToSeconds(ui.byId("window").value, 24 * 3600); }
  function resetFilters() {
    ui.byId("statusFilter").value = "all";
    ui.byId("channelFilter").value = "all";
    ui.byId("central").value = "";
    ui.byId("code").value = "";
    ui.byId("q").value = "";
  }
  function setSelectIfValid(id, value, allowed) {
    const normalized = String(value || "").trim();
    const element = ui.byId(id);
    if (!element) return;
    if (allowed.has(normalized)) element.value = normalized;
  }
  function boolFromQuery(value, fallback) {
    if (value === null || value === undefined) return fallback;
    const normalized = String(value).trim().toLowerCase();
    if (normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on") return true;
    if (normalized === "0" || normalized === "false" || normalized === "no" || normalized === "off") return false;
    return fallback;
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    setSelectIfValid("window", params.get("window") || "24h", new Set(["1h", "24h", "7d"]));
    setSelectIfValid("statusFilter", params.get("status") || "all", new Set(["all", "failed", "skipped", "sent"]));
    setSelectIfValid("channelFilter", params.get("channel") || "all", new Set(["all", "telegram", "email", "policy"]));
    const central = params.get("central") || params.get("central_id");
    const code = params.get("code");
    const q = params.get("q");
    if (central !== null) ui.byId("central").value = String(central);
    if (code !== null) ui.byId("code").value = String(code);
    if (q !== null) ui.byId("q").value = String(q);
    ui.byId("dryRunRetry").checked = boolFromQuery(params.get("dry_run") ?? params.get("dryRun"), false);
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const windowVal = ui.byId("window").value || "24h";
    const status = ui.val("statusFilter", "all").toLowerCase();
    const channel = ui.val("channelFilter", "all").toLowerCase();
    const central = ui.val("central");
    const code = ui.val("code");
    const q = ui.val("q");
    const dryRun = !!ui.byId("dryRunRetry").checked;
    if (windowVal && windowVal !== "24h") params.set("window", windowVal);
    if (status && status !== "all") params.set("status", status);
    if (channel && channel !== "all") params.set("channel", channel);
    if (central) params.set("central_id", central);
    if (code) params.set("code", code);
    if (q) params.set("q", q);
    if (dryRun) params.set("dry_run", "1");
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const parts = [];
    const windowVal = ui.byId("window").value || "24h";
    const status = ui.val("statusFilter", "all").toLowerCase();
    const channel = ui.val("channelFilter", "all").toLowerCase();
    const central = ui.val("central");
    const code = ui.val("code");
    const q = ui.val("q");
    const dryRun = !!ui.byId("dryRunRetry").checked;
    if (windowVal && windowVal !== "24h") parts.push(`вікно=${windowVal}`);
    if (status && status !== "all") parts.push(`статус=${status}`);
    if (channel && channel !== "all") parts.push(`канал=${channel}`);
    if (central) parts.push(`вузол=${central}`);
    if (code) parts.push(`код=${code}`);
    if (q) parts.push(`q=${q}`);
    if (dryRun) parts.push("dry-run");
    const node = ui.byId("filterSummary");
    if (!node) return;
    node.textContent = parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні";
  }
  async function apiPost(path, payload) { return ui.apiPost(path, payload); }
  async function retryNotification(id) {
    if (!adminCaps.operate) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    setStatus(`Повторна відправка #${id}...`);
    try {
      const dryRun = !!ui.byId("dryRunRetry").checked;
      const data = await apiPost("/api/admin/fleet/notifications/retry", { notification_id: Number(id), dry_run: dryRun });
      const counters = data.result?.counters || {};
      setStatus(`RETRY УСПІХ: id=${id}, надіслано=${counters.sent || 0}, помилки=${counters.failed || 0}, пропущено=${counters.skipped || 0}`);
      await refresh();
    } catch (error) {
      setStatus("RETRY ПОМИЛКА: " + error);
    }
  }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const params = new URLSearchParams();
      params.set("limit", "700");
      const since = new Date(Date.now() - (windowSeconds() * 1000)).toISOString();
      params.set("since_ts", since);
      ui.setText("notifySinceChip", `від: ${since}`);
      const status = ui.val("statusFilter", "all").toLowerCase();
      const channel = ui.val("channelFilter", "all").toLowerCase();
      const central = ui.val("central");
      const code = ui.val("code");
      const q = ui.val("q");
      if (status !== "all") params.set("status", status);
      if (channel !== "all") params.set("channel", channel);
      if (central) params.set("central_id", central);
      if (code) params.set("code", code);
      if (q) params.set("q", q);

      const data = await ui.apiGet(`/api/admin/fleet/incidents/notifications?${params.toString()}`);
      const notifications = Array.isArray(data.notifications) ? data.notifications : [];

      let sent = 0;
      let failed = 0;
      let skipped = 0;
      let retryable = 0;
      for (const item of notifications) {
        const st = String(item.status || "").toLowerCase();
        const ch = String(item.channel || "").toLowerCase();
        if (st === "sent") sent += 1;
        else if (st === "failed") failed += 1;
        else if (st === "skipped") skipped += 1;
        if (st === "failed" && (ch === "telegram" || ch === "email")) retryable += 1;
      }
      document.getElementById("sumTotal").textContent = `всього: ${notifications.length}`;
      document.getElementById("sumSent").textContent = `надіслано: ${sent}`;
      document.getElementById("sumFailed").textContent = `помилки: ${failed}`;
      document.getElementById("sumSkipped").textContent = `пропущено: ${skipped}`;
      document.getElementById("sumRetryable").textContent = `помилки з повтором: ${retryable}`;

      const tbody = document.querySelector("#tbl tbody");
      tbody.innerHTML = "";
      if (notifications.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = '<td colspan="10"><span class="badge">—</span> Журнал сповіщень порожній для поточних фільтрів</td>';
        tbody.appendChild(row);
      } else {
        for (const item of notifications) {
          const st = String(item.status || "").toLowerCase();
          const ch = String(item.channel || "").toLowerCase();
          const retryAllowed = st === "failed" && (ch === "telegram" || ch === "email");
          const actionHtml = retryAllowed
            ? `<button class="smallbtn" data-retry-id="${Number(item.id || 0)}" ${adminCaps.operate ? "" : "disabled"}>Повторити</button>`
            : '<span class="badge">—</span>';
          const row = document.createElement("tr");
          row.innerHTML = `
            <td><code>${ui.esc(item.id ?? "—")}</code></td>
            <td><code>${ui.esc(item.ts || "—")}</code></td>
            <td><span class="badge ${statusClass(st)}">${ui.esc(statusLabel(st))}</span></td>
            <td><code>${ui.esc(ch || "—")}</code></td>
            <td><code>${ui.esc(item.event || "—")}</code></td>
            <td><code>${ui.esc(item.central_id || "—")}</code></td>
            <td><code>${ui.esc(item.code || "—")}</code></td>
            <td><code>${ui.esc(item.destination || "—")}</code></td>
            <td><code>${ui.esc(item.error || "—")}</code></td>
            <td>${actionHtml}</td>
          `;
          tbody.appendChild(row);
        }
      }

      for (const button of document.querySelectorAll("button[data-retry-id]")) {
        button.addEventListener("click", async (event) => {
          const target = event.currentTarget;
          const id = Number(target.getAttribute("data-retry-id") || "0");
          if (id > 0) await retryNotification(id);
        });
      }

      ui.setText("updatedAt", `оновлено: ${notifications[0]?.ts || new Date().toLocaleString("uk-UA")}`);
      setStatus(`OK: сповіщень=${notifications.length}, від=${since}`);
    } catch (error) {
      setStatus("ПОМИЛКА: " + error);
    }
  }
  function refreshWithUrl() {
    syncQueryFromFilters();
    syncFilterSummary();
    refresh();
  }
  ui.byId("refresh").addEventListener("click", refreshWithUrl);
  ui.byId("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  ui.bindClearFilters("clearFilters", resetFilters, refreshWithUrl);
  ui.byId("window").addEventListener("change", refreshWithUrl);
  ui.byId("statusFilter").addEventListener("change", refreshWithUrl);
  ui.byId("channelFilter").addEventListener("change", refreshWithUrl);
  ui.bindDebouncedInputs(["central", "code", "q"], refreshWithUrl, REFRESH_DELAY_MS);
  ui.bindEnterRefresh(["central", "code", "q"], refreshWithUrl);
  initNotifySecondaryDetails();
  applyFiltersFromQuery();
  syncQueryFromFilters();
  syncFilterSummary();
  loadWhoami().then(refresh);
  setInterval(() => { if (ui.byId("auto").checked) refresh(); }, 12000);
    """
    return render_admin_shell(
        title="Адмін-панель Passengers — Центр сповіщень",
        header_title="Центр сповіщень",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        extra_css=extra_css,
        max_width=1360,
        current_nav="notify-center",
    ).strip()
