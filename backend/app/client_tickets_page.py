from __future__ import annotations

from app.client_ui_kit import render_client_shell


def render_client_tickets_page() -> str:
    chips_html = """
      <span class="chip">звернення до підтримки</span>
      <span class="chip" id="whoami">роль: —</span>
    """
    toolbar_html = """
      <div class="toolbarMain">
        <input id="q" type="search" placeholder="пошук: тема / номер" />
        <button id="refresh" class="primary">Оновити</button>
        <button id="tableToggle" class="tableToggle" data-table-toggle="progressive" data-open="0">Колонки: базово</button>
        <button id="copyLink">Скопіювати посилання</button>
      </div>
      <div class="toolbarMeta">
        <span class="metaChip" id="filterSummary">фільтри: стандартні</span>
        <span class="status" id="status"></span>
      </div>
    """
    body_html = """
    <div class="card">
      <div class="summary">
        <span class="badge" id="sumTotal">всього: 0</span>
        <span class="badge warn" id="sumOpen">активні: 0</span>
        <span class="badge warn" id="sumInProgress">в роботі: 0</span>
        <span class="badge good" id="sumResolved">вирішені: 0</span>
      </div>
      <div class="sectionTitle">Активні звернення</div>
      <div class="tableWrap">
        <table id="activeTbl" class="mobileFriendly" data-empty-title="OK" data-empty-tone="good" data-empty-text="Активних звернень не знайдено.">
          <thead>
            <tr>
                <th>Номер</th>
                <th>Тема</th>
                <th>Статус</th>
                <th>Оновлено</th>
                <th class="mobileHide progressiveCol">Коментар</th>
              </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <details id="resolvedDetails" class="secondaryDetails">
        <summary>Архів вирішених звернень</summary>
        <div class="secondaryBody">
          <div class="tableWrap">
            <table id="resolvedTbl" class="mobileFriendly" data-empty-title="Порожньо" data-empty-text="Архів за поточним фільтром порожній.">
              <thead>
                <tr>
                  <th>Номер</th>
                  <th>Тема</th>
                  <th>Статус</th>
                  <th>Оновлено</th>
                  <th class="mobileHide progressiveCol">Коментар</th>
                </tr>
              </thead>
              <tbody></tbody>
            </table>
          </div>
        </div>
      </details>
    </div>
    """
    script = """
  const ui = window.ClientUiKit;
  const SECONDARY_STORAGE_KEY = "passengers_client_tickets_secondary_v1";
  function statusMeta(value) {
    const s = String(value || "").toLowerCase();
    if (s === "resolved") return { cls: "good", label: "ВИРІШЕНО" };
    if (s === "in_progress") return { cls: "warn", label: "В РОБОТІ" };
    return { cls: "warn", label: "ВІДКРИТО" };
  }
  function ticketStatus(raw) {
    const normalized = String(raw || "").toLowerCase();
    if (normalized === "resolved") return "resolved";
    if (normalized === "in_progress") return "in_progress";
    return "open";
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    if (q !== null) ui.byId("q").value = String(q);
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const q = String(ui.byId("q").value || "").trim();
    if (q) params.set("q", q);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const q = String(ui.byId("q").value || "").trim();
    ui.setText("filterSummary", q ? `фільтри: q=${q}` : "фільтри: стандартні");
  }
  function renderRows(tableId, rows, emptyText) {
    const tbody = ui.byId(tableId).querySelector("tbody");
    tbody.innerHTML = "";
    for (const item of rows) {
      const meta = statusMeta(item.status);
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><code>${ui.esc(item.id)}</code></td>
        <td>${ui.esc(item.topic)}</td>
        <td><span class="badge ${meta.cls}">${meta.label}</span></td>
        <td><code>${ui.esc(item.updated_at)}</code></td>
        <td class="mobileHide progressiveCol">${ui.esc(item.note)}</td>
      `;
      tbody.appendChild(row);
    }
    const table = ui.byId(tableId);
    if (table && emptyText) table.setAttribute("data-empty-text", String(emptyText));
    ui.applyEmptyTables();
  }
  async function refresh() {
    const q = String(ui.byId("q").value || "").trim();
    ui.setStatus("status", "Оновлення...");
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      params.set("limit", "300");
      const data = await ui.apiGet(`/api/client/tickets?${params.toString()}`);
      const tickets = Array.isArray(data.tickets) ? data.tickets : [];

      const active = [];
      const resolved = [];
      for (const item of tickets) {
        const normalized = ticketStatus(item.status);
        if (normalized === "resolved") resolved.push(item);
        else active.push(item);
      }

      renderRows("activeTbl", active, "Активних звернень не знайдено");
      renderRows("resolvedTbl", resolved, "Архів за поточним фільтром порожній");

      const total = Number(data.total || tickets.length || 0);
      const open = active.length;
      const inProgress = active.filter((item) => ticketStatus(item.status) === "in_progress").length;
      ui.setText("sumTotal", `всього: ${total}`);
      ui.setText("sumOpen", `активні: ${open}`);
      ui.setText("sumInProgress", `в роботі: ${inProgress}`);
      ui.setText("sumResolved", `вирішені: ${resolved.length}`);
      ui.setStatus("status", `OK: активні=${open}, архів=${resolved.length}`);
    } catch (error) {
      renderRows("activeTbl", [], "Не вдалося завантажити активні звернення");
      renderRows("resolvedTbl", [], "Не вдалося завантажити архів звернень");
      ui.setText("sumTotal", "всього: 0");
      ui.setText("sumOpen", "активні: 0");
      ui.setText("sumInProgress", "в роботі: 0");
      ui.setText("sumResolved", "вирішені: 0");
      ui.setStatus("status", `ПОМИЛКА: ${error && error.message ? error.message : "запит не виконано"}`);
    }
  }
  async function initWhoami() {
    const whoami = await ui.loadWhoami();
    const isSupport = String(whoami.role || "client") === "admin-support";
    ui.setText("whoami", isSupport ? "роль: admin-support" : "роль: client");
    ui.bindDetailsState("resolvedDetails", SECONDARY_STORAGE_KEY, isSupport);
  }
  function refreshWithUrl() {
    syncQueryFromFilters();
    syncFilterSummary();
    refresh();
  }
  ui.byId("refresh").addEventListener("click", refreshWithUrl);
  ui.byId("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  ui.bindDebouncedInputs(["q"], refreshWithUrl, 220);
  ui.bindEnterRefresh(["q"], refreshWithUrl);
  async function init() {
    await initWhoami();
    applyFiltersFromQuery();
    syncQueryFromFilters();
    syncFilterSummary();
    await refresh();
  }
  init();
    """.strip()
    return render_client_shell(
        title="Passengers — Звернення клієнта",
        header_title="Тікети та звернення",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        current_nav="client-tickets",
    )
