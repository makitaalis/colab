from __future__ import annotations

from app.client_ui_kit import render_client_shell


def render_client_status_page() -> str:
    chips_html = """
      <span class="chip">оперативні оновлення для клієнта</span>
      <span class="chip" id="whoami">роль: —</span>
      <span class="chip" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
      <div class="toolbarMain">
        <select id="levelFilter">
          <option value="all">усі рівні</option>
          <option value="attention">потребує уваги</option>
          <option value="critical">лише критичні</option>
        </select>
        <input id="q" type="search" placeholder="пошук: категорія / повідомлення" />
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
        <span class="badge good" id="sumGood">СТАБІЛЬНО: 0</span>
        <span class="badge warn" id="sumWarn">УВАГА: 0</span>
        <span class="badge bad" id="sumBad">ПРОБЛЕМИ: 0</span>
      </div>
      <div class="muted">Нижче відображається стрічка статусів у зрозумілому форматі без технічних термінів.</div>
    </div>

    <div class="card">
      <div class="sectionTitle">Потребує уваги зараз</div>
      <div class="tableWrap">
        <table id="focusTbl" class="mobileFriendly" data-empty-title="OK" data-empty-tone="good" data-empty-text="Немає статусів, що потребують уваги.">
          <thead>
            <tr>
              <th>Час</th>
              <th class="mobileHide progressiveCol">Категорія</th>
              <th>Стан</th>
              <th>Що це означає</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <details id="fullTimelineDetails" class="secondaryDetails">
        <summary>Повна стрічка статусів</summary>
        <div class="secondaryBody">
          <div class="tableWrap">
            <table id="allTbl" class="mobileFriendly" data-empty-title="Порожньо" data-empty-text="Стрічка статусів за фільтром порожня.">
              <thead>
                <tr>
                  <th>Час</th>
                  <th class="mobileHide progressiveCol">Категорія</th>
                  <th>Стан</th>
                  <th>Що це означає</th>
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
  const SECONDARY_STORAGE_KEY = "passengers_client_status_secondary_v1";
  function levelBadge(level) {
    const s = String(level || "").toLowerCase();
    if (s === "good") return '<span class="badge good">СТАБІЛЬНО</span>';
    if (s === "warn") return '<span class="badge warn">УВАГА</span>';
    return '<span class="badge bad">ПРОБЛЕМА</span>';
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const level = params.get("level");
    const q = params.get("q");
    if (level) ui.byId("levelFilter").value = String(level);
    if (q !== null) ui.byId("q").value = String(q);
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const level = String(ui.byId("levelFilter").value || "all").trim();
    const q = String(ui.byId("q").value || "").trim();
    if (level && level !== "all") params.set("level", level);
    if (q) params.set("q", q);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const parts = [];
    const level = String(ui.byId("levelFilter").value || "all").trim();
    const q = String(ui.byId("q").value || "").trim();
    if (level !== "all") parts.push(`level=${level}`);
    if (q) parts.push(`q=${q}`);
    ui.setText("filterSummary", parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні");
  }
  function matchesLevel(level, filter) {
    const normalized = String(level || "").toLowerCase();
    const f = String(filter || "all").toLowerCase();
    if (f === "critical") return normalized === "bad";
    if (f === "attention") return normalized === "warn" || normalized === "bad";
    return true;
  }
  function isAttention(level) {
    const normalized = String(level || "").toLowerCase();
    return normalized === "warn" || normalized === "bad";
  }
  function renderRows(tableId, rows, emptyText) {
    const tbody = ui.byId(tableId).querySelector("tbody");
    tbody.innerHTML = "";
    for (const item of rows) {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><code>${ui.esc(item.ts)}</code></td>
        <td class="mobileHide progressiveCol">${ui.esc(item.category)}</td>
        <td>${levelBadge(item.level)}</td>
        <td>${ui.esc(item.message)}</td>
      `;
      tbody.appendChild(row);
    }
    const table = ui.byId(tableId);
    if (table && emptyText) table.setAttribute("data-empty-text", String(emptyText));
    ui.applyEmptyTables();
  }
  async function refresh() {
    const level = String(ui.byId("levelFilter").value || "all").trim();
    const q = String(ui.byId("q").value || "").trim().toLowerCase();
    ui.setStatus("status", "Оновлення...");
    try {
      const data = await ui.apiGet("/api/client/status?limit=220");
      const events = Array.isArray(data.events) ? data.events : [];
      const filtered = [];
      for (const item of events) {
        const hay = `${String(item.ts || "")} ${String(item.category || "")} ${String(item.message || "")} ${String(item.code || "")}`.toLowerCase();
        if (q && !hay.includes(q)) continue;
        if (!matchesLevel(item.level, level)) continue;
        filtered.push(item);
      }

      const focus = filtered.filter((item) => isAttention(item.level));
      renderRows("focusTbl", focus, "Немає статусів, що потребують уваги");
      renderRows("allTbl", filtered, "Стрічка статусів за фільтром порожня");

      const good = filtered.filter((item) => String(item.level || "").toLowerCase() === "good").length;
      const warn = filtered.filter((item) => String(item.level || "").toLowerCase() === "warn").length;
      const bad = filtered.filter((item) => String(item.level || "").toLowerCase() === "bad").length;
      ui.setText("sumGood", `СТАБІЛЬНО: ${good}`);
      ui.setText("sumWarn", `УВАГА: ${warn}`);
      ui.setText("sumBad", `ПРОБЛЕМИ: ${bad}`);
      ui.setText("updatedAt", `оновлено: ${new Date().toLocaleString("uk-UA")}`);
      ui.setStatus("status", `OK: увага=${focus.length}, у стрічці=${filtered.length}`);
    } catch (error) {
      renderRows("focusTbl", [], "Не вдалося завантажити статуси уваги");
      renderRows("allTbl", [], "Не вдалося завантажити стрічку статусів");
      ui.setText("sumGood", "СТАБІЛЬНО: 0");
      ui.setText("sumWarn", "УВАГА: 0");
      ui.setText("sumBad", "ПРОБЛЕМИ: 0");
      ui.setStatus("status", `ПОМИЛКА: ${error && error.message ? error.message : "запит не виконано"}`);
    }
  }
  async function initWhoami() {
    const whoami = await ui.loadWhoami();
    const isSupport = String(whoami.role || "client") === "admin-support";
    ui.setText("whoami", isSupport ? "роль: admin-support" : "роль: client");
    ui.bindDetailsState("fullTimelineDetails", SECONDARY_STORAGE_KEY, isSupport);
  }
  function refreshWithUrl() {
    syncQueryFromFilters();
    syncFilterSummary();
    refresh();
  }
  ui.byId("refresh").addEventListener("click", refreshWithUrl);
  ui.byId("levelFilter").addEventListener("change", refreshWithUrl);
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
        title="Passengers — Статуси клієнта",
        header_title="Поточні статуси",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        current_nav="client-status",
    )
