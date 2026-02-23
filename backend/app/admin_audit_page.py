from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_audit_page() -> str:
    chips_html = """
        <span class="chip" id="whoami">роль: —</span>
        <span class="chip" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
        <div class="toolbarMain">
          <label><input id="auto" type="checkbox" checked /> авто</label>
          <button id="clearFilters">Скинути</button>
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
              <select id="statusFilter" title="статус">
                <option value="all">усі статуси</option>
                <option value="ok">успіх</option>
                <option value="forbidden">заборонено</option>
                <option value="error">помилка</option>
              </select>
              <select id="roleFilter" title="роль">
                <option value="all">усі ролі</option>
                <option value="viewer">viewer</option>
                <option value="operator">operator</option>
                <option value="admin">admin</option>
              </select>
              <input id="actor" type="text" placeholder="актор" />
              <input id="action" type="text" placeholder="дія" />
              <input id="q" type="text" placeholder="пошук деталі/шлях" />
            </div>
          </details>
        </div>
        <div class="toolbarMeta">
          <span class="metaChip sort" id="filterSummary">фільтри: стандартні</span>
          <span class="status" id="status"></span>
        </div>
    """
    body_html = """
    <div class="card">
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code>/api/admin/audit</code></span>
        <span class="metaChip sort">сортування: <code>нові → старі</code></span>
        <span class="metaChip mode" id="auditWindowChip">вікно: —</span>
      </div>
      <div class="tableWrap">
        <table id="tbl" style="min-width: 1360px;">
          <thead>
            <tr>
              <th>ID</th>
              <th>Час</th>
              <th>Статус</th>
              <th>Актор</th>
              <th>Роль</th>
              <th>Дія</th>
              <th>Метод</th>
              <th>Шлях</th>
              <th>Код</th>
              <th>IP клієнта</th>
              <th>Деталі</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
    """
    script = """
  const ui = window.AdminUiKit;
  const REFRESH_DELAY_MS = 280;
  const DEFAULT_WINDOW = "24h";
  function setStatus(s) { ui.setStatus("status", s); }
  function statusClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "ok") return "good";
    if (normalized === "forbidden") return "warn";
    return "bad";
  }
  function statusLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "ok") return "УСПІХ";
    if (normalized === "forbidden") return "ЗАБОРОНЕНО";
    if (normalized === "error") return "ПОМИЛКА";
    return "НЕВІДОМО";
  }
  function windowSeconds() { return ui.windowToSeconds(ui.byId("window").value, 24 * 3600); }
  function setSelectIfValid(id, value, allowed) {
    const normalized = String(value || "").trim();
    const element = ui.byId(id);
    if (!element) return;
    if (allowed.has(normalized)) element.value = normalized;
  }
  function resetFilters() {
    ui.byId("window").value = DEFAULT_WINDOW;
    ui.byId("statusFilter").value = "all";
    ui.byId("roleFilter").value = "all";
    ui.byId("actor").value = "";
    ui.byId("action").value = "";
    ui.byId("q").value = "";
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    setSelectIfValid("window", params.get("window") || DEFAULT_WINDOW, new Set(["1h", "24h", "7d"]));
    setSelectIfValid("statusFilter", params.get("status") || "all", new Set(["all", "ok", "forbidden", "error"]));
    setSelectIfValid("roleFilter", params.get("role") || "all", new Set(["all", "viewer", "operator", "admin"]));
    const actor = params.get("actor");
    const action = params.get("action");
    const q = params.get("q");
    if (actor !== null) ui.byId("actor").value = String(actor);
    if (action !== null) ui.byId("action").value = String(action);
    if (q !== null) ui.byId("q").value = String(q);
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const windowVal = ui.byId("window").value || DEFAULT_WINDOW;
    const statusVal = ui.val("statusFilter", "all").toLowerCase();
    const roleVal = ui.val("roleFilter", "all").toLowerCase();
    const actor = ui.val("actor");
    const action = ui.val("action");
    const q = ui.val("q");
    if (windowVal && windowVal !== DEFAULT_WINDOW) params.set("window", windowVal);
    if (statusVal && statusVal !== "all") params.set("status", statusVal);
    if (roleVal && roleVal !== "all") params.set("role", roleVal);
    if (actor) params.set("actor", actor);
    if (action) params.set("action", action);
    if (q) params.set("q", q);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const parts = [];
    const windowVal = ui.byId("window").value || DEFAULT_WINDOW;
    const statusVal = ui.val("statusFilter", "all").toLowerCase();
    const roleVal = ui.val("roleFilter", "all").toLowerCase();
    const actor = ui.val("actor");
    const action = ui.val("action");
    const q = ui.val("q");
    ui.setText("auditWindowChip", `вікно: ${windowVal || DEFAULT_WINDOW}`);
    if (windowVal && windowVal !== DEFAULT_WINDOW) parts.push(`вікно=${windowVal}`);
    if (statusVal && statusVal !== "all") parts.push(`статус=${statusVal}`);
    if (roleVal && roleVal !== "all") parts.push(`роль=${roleVal}`);
    if (actor) parts.push(`актор=${actor}`);
    if (action) parts.push(`дія=${action}`);
    if (q) parts.push(`q=${q}`);
    const node = ui.byId("filterSummary");
    if (!node) return;
    node.textContent = parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні";
  }
  async function loadWhoami() {
    const data = await ui.loadWhoami();
    ui.setText("whoami", `роль: ${data.role || "?"}, актор: ${data.actor || "?"}`);
  }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const params = new URLSearchParams();
      params.set("limit", "700");
      const since = new Date(Date.now() - (windowSeconds() * 1000)).toISOString();
      params.set("since_ts", since);

      const statusVal = ui.val("statusFilter", "all").toLowerCase();
      const roleVal = ui.val("roleFilter", "all").toLowerCase();
      const actor = ui.val("actor");
      const action = ui.val("action");
      const q = ui.val("q");
      if (statusVal !== "all") params.set("status", statusVal);
      if (roleVal !== "all") params.set("role", roleVal);
      if (actor) params.set("actor", actor);
      if (action) params.set("action", action);
      if (q) params.set("q", q);

      const data = await ui.apiGet(`/api/admin/audit?${params.toString()}`);
      const rows = Array.isArray(data.audit) ? data.audit : [];
      const tbody = document.querySelector("#tbl tbody");
      tbody.innerHTML = "";
      if (rows.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = '<td colspan="11"><span class="badge">—</span> Немає записів за поточними фільтрами</td>';
        tbody.appendChild(row);
      } else {
        for (const item of rows) {
          const st = String(item.status || "").toLowerCase();
          const details = item.details ? JSON.stringify(item.details) : "";
          const row = document.createElement("tr");
          row.innerHTML = `
            <td><code>${ui.esc(item.id ?? "—")}</code></td>
            <td><code>${ui.esc(item.ts || "—")}</code></td>
            <td><span class="badge ${statusClass(st)}">${ui.esc(statusLabel(st))}</span></td>
            <td><code>${ui.esc(item.actor || "—")}</code></td>
            <td><code>${ui.esc(item.role || "—")}</code></td>
            <td><code>${ui.esc(item.action || "—")}</code></td>
            <td><code>${ui.esc(item.method || "—")}</code></td>
            <td><code>${ui.esc(item.path || "—")}</code></td>
            <td><code>${ui.esc(item.status_code ?? "—")}</code></td>
            <td><code>${ui.esc(item.client_ip || "—")}</code></td>
            <td><code>${ui.esc(details || "—")}</code></td>
          `;
          tbody.appendChild(row);
        }
      }
      ui.setText("updatedAt", `оновлено: ${rows[0]?.ts || new Date().toLocaleString("uk-UA")}`);
      setStatus(`OK: записів=${rows.length}, від=${since}`);
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
  ui.byId("roleFilter").addEventListener("change", refreshWithUrl);
  ui.bindDebouncedInputs(["actor", "action", "q"], refreshWithUrl, REFRESH_DELAY_MS);
  ui.bindEnterRefresh(["actor", "action", "q"], refreshWithUrl);
  loadWhoami();
  applyFiltersFromQuery();
  syncQueryFromFilters();
  syncFilterSummary();
  refresh();
  setInterval(() => { if (ui.byId("auto").checked) refresh(); }, 12000);
    """
    return render_admin_shell(
        title="Адмін-панель Passengers — Аудит",
        header_title="Журнал аудиту адміна",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        max_width=1380,
        current_nav="audit",
    ).strip()
