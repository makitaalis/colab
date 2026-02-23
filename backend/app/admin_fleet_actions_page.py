from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_actions_page() -> str:
    chips_html = """
        <span class="chip">ack/silence/unsilence</span>
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
              <input id="central" type="text" placeholder="ідентифікатор вузла (точно)" />
              <input id="code" type="text" placeholder="код події (точно)" />
              <input id="q" type="text" placeholder="пошук актор/нотатка" />
              <select id="action" title="дія">
                <option value="all">усі дії</option>
                <option value="ack">підтвердження</option>
                <option value="silence">заглушення</option>
                <option value="unsilence">зняття заглушення</option>
              </select>
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
        <span class="metaChip source">джерело: <code>/api/admin/fleet/alerts/actions</code></span>
        <span class="metaChip sort">сортування: <code>нові → старі</code></span>
        <span class="metaChip mode">limit: <code>500</code></span>
      </div>
      <div class="tableWrap">
        <table id="tbl" style="min-width: 980px;">
          <thead>
            <tr>
              <th>Час</th>
              <th>Дія</th>
              <th>Вузол</th>
              <th>Код</th>
              <th>Актор</th>
              <th>Нотатка</th>
              <th>Заглушено до</th>
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
  function setStatus(s) { ui.setStatus("status", s); }
  function actionBadge(action) {
    const normalized = String(action || "").toLowerCase();
    if (normalized === "ack") return "good";
    if (normalized === "silence") return "warn";
    return "bad";
  }
  function actionLabel(action) {
    const normalized = String(action || "").toLowerCase();
    if (normalized === "ack") return "ПІДТВЕРДЖЕНО";
    if (normalized === "silence") return "ЗАГЛУШЕНО";
    if (normalized === "unsilence") return "ЗНЯТО ЗАГЛУШЕННЯ";
    return "ДІЯ";
  }
  function resetFilters() {
    ui.byId("central").value = "";
    ui.byId("code").value = "";
    ui.byId("q").value = "";
    ui.byId("action").value = "all";
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    if (q !== null) ui.byId("q").value = String(q);
    const central = params.get("central") || params.get("central_id");
    if (central !== null) ui.byId("central").value = String(central);
    const code = params.get("code");
    if (code !== null) ui.byId("code").value = String(code);
    const action = String(params.get("action") || "").trim().toLowerCase();
    if (action === "ack" || action === "silence" || action === "unsilence" || action === "all") {
      ui.byId("action").value = action || "all";
    }
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const central = ui.val("central");
    const code = ui.val("code");
    const q = ui.val("q");
    const action = ui.val("action").toLowerCase();
    if (q) params.set("q", q);
    if (central) params.set("central_id", central);
    if (code) params.set("code", code);
    if (action && action !== "all") params.set("action", action);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const parts = [];
    const central = ui.val("central");
    const code = ui.val("code");
    const q = ui.val("q");
    const action = ui.val("action").toLowerCase();
    if (q) parts.push(`q=${q}`);
    if (central) parts.push(`вузол=${central}`);
    if (code) parts.push(`код=${code}`);
    if (action && action !== "all") parts.push(`дія=${action}`);
    const node = ui.byId("filterSummary");
    if (!node) return;
    node.textContent = parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні";
  }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const params = new URLSearchParams();
      params.set("limit", "500");
      const central = ui.val("central");
      const code = ui.val("code");
      const q = ui.val("q");
      const action = ui.val("action").toLowerCase();
      if (central) params.set("central_id", central);
      if (code) params.set("code", code);
      if (q) params.set("q", q);
      if (action && action !== "all") params.set("action", action);
      const data = await ui.apiGet(`/api/admin/fleet/alerts/actions?${params.toString()}`);
      const actions = Array.isArray(data.actions) ? data.actions : [];
      const tbody = document.querySelector("#tbl tbody");
      tbody.innerHTML = "";
      if (actions.length === 0) {
        const tr = document.createElement("tr");
        tr.innerHTML = '<td colspan="7"><span class="badge">—</span> Немає дій за вибраними фільтрами</td>';
        tbody.appendChild(tr);
      } else {
        for (const item of actions) {
          const tr = document.createElement("tr");
          const centralId = String(item.central_id || "");
          const actionValue = String(item.action || "");
          const actionClass = actionBadge(actionValue);
          tr.innerHTML = `
            <td><code>${ui.esc(item.ts || "—")}</code></td>
            <td><span class="badge ${actionClass}">${ui.esc(actionLabel(actionValue))}</span></td>
            <td><a href="/admin/fleet/central/${encodeURIComponent(centralId)}"><code>${ui.esc(centralId || "—")}</code></a></td>
            <td><code>${ui.esc(item.code || "—")}</code></td>
            <td><code>${ui.esc(item.actor || "—")}</code></td>
            <td>${ui.esc(item.note || "")}</td>
            <td><code>${ui.esc(item.silenced_until || "—")}</code></td>
          `;
          tbody.appendChild(tr);
        }
      }
      ui.setText("updatedAt", `оновлено: ${actions[0]?.ts || new Date().toLocaleString("uk-UA")}`);
      setStatus(`OK: всього=${actions.length}`);
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
  ui.bindDebouncedInputs(["central", "code", "q"], refreshWithUrl, REFRESH_DELAY_MS);
  ui.byId("action").addEventListener("change", refreshWithUrl);
  ui.bindEnterRefresh(["central", "code", "q"], refreshWithUrl);
  applyFiltersFromQuery();
  syncQueryFromFilters();
  syncFilterSummary();
  refresh();
  setInterval(() => { if (ui.byId("auto").checked) refresh(); }, 10000);
    """
    return render_admin_shell(
        title="Адмін-панель Passengers — Дії флоту",
        header_title="Журнал дій флоту",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        max_width=1280,
        current_nav="actions",
    ).strip()
