from __future__ import annotations

from app.client_ui_kit import render_client_shell


def render_client_vehicles_page() -> str:
    chips_html = """
      <span class="chip">стан закріплених транспортів</span>
      <span class="chip" id="whoami">роль: —</span>
    """
    toolbar_html = """
      <div class="toolbarMain">
        <select id="slaFilter">
          <option value="all">усі SLA</option>
          <option value="attention">потребують уваги</option>
          <option value="risk">ризик SLA</option>
          <option value="warn">увага SLA</option>
          <option value="ok">SLA в нормі</option>
        </select>
        <input id="q" type="search" placeholder="пошук: транспорт / маршрут" />
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
        <span class="badge" id="sumTotal">транспортів: 0</span>
        <span class="badge good" id="sumGood">в нормі: 0</span>
        <span class="badge warn" id="sumWarn">із затримками: 0</span>
        <span class="badge bad" id="sumBad">проблемні: 0</span>
        <span class="badge bad" id="sumSlaRisk">SLA ризик: 0</span>
        <span class="badge warn" id="sumEta">ETA avg +0 хв · max +0 хв</span>
      </div>
      <div class="sectionTitle">Потребують уваги</div>
      <div class="tableWrap">
        <table id="focusTbl" class="mobileFriendly" data-empty-title="OK" data-empty-tone="good" data-empty-text="Транспорт з відхиленнями не знайдено.">
          <thead>
            <tr>
              <th>Транспорт</th>
              <th class="mobileHide progressiveCol">Маршрут</th>
              <th>SLA</th>
              <th>ETA</th>
              <th class="mobileHide progressiveCol">Черга / інциденти</th>
              <th>Рекомендація</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <details id="allVehiclesDetails" class="secondaryDetails">
        <summary>Усі транспорти</summary>
        <div class="secondaryBody">
          <div class="tableWrap">
            <table id="allTbl" class="mobileFriendly" data-empty-title="Немає транспортів" data-empty-text="За поточним фільтром список порожній.">
              <thead>
                <tr>
                  <th>Транспорт</th>
                  <th class="mobileHide progressiveCol">Маршрут</th>
                  <th>Стан</th>
                  <th>SLA</th>
                  <th>ETA</th>
                  <th class="mobileHide progressiveCol">Оновлено</th>
                  <th class="mobileHide progressiveCol">Рекомендація</th>
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
  const SECONDARY_STORAGE_KEY = "passengers_client_vehicles_secondary_v1";
  function stateBadge(state) {
    const normalized = String(state || "").toLowerCase();
    if (normalized === "good") return '<span class="badge good">В НОРМІ</span>';
    if (normalized === "warn") return '<span class="badge warn">ЗАТРИМКА</span>';
    return '<span class="badge bad">ПРОБЛЕМА</span>';
  }
  function slaBadge(state) {
    const normalized = String(state || "").toLowerCase();
    if (normalized === "risk") return '<span class="badge bad">РИЗИК</span>';
    if (normalized === "warn") return '<span class="badge warn">УВАГА</span>';
    return '<span class="badge good">OK</span>';
  }
  function isAttention(item) {
    const normalized = String((item && item.sla_state) || "").toLowerCase();
    return normalized === "warn" || normalized === "risk";
  }
  function matchesSla(item, filter) {
    const normalized = String((item && item.sla_state) || "").toLowerCase();
    const mode = String(filter || "all").toLowerCase();
    if (mode === "attention") return normalized === "warn" || normalized === "risk";
    if (mode === "risk") return normalized === "risk";
    if (mode === "warn") return normalized === "warn";
    if (mode === "ok") return normalized === "ok";
    return true;
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const sla = String(ui.byId("slaFilter").value || "all").trim();
    const q = String(ui.byId("q").value || "").trim();
    if (sla && sla !== "all") params.set("sla", sla);
    if (q) params.set("q", q);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const sla = params.get("sla");
    const q = params.get("q");
    if (sla) ui.byId("slaFilter").value = String(sla);
    if (q !== null) ui.byId("q").value = String(q);
  }
  function syncFilterSummary() {
    const parts = [];
    const sla = String(ui.byId("slaFilter").value || "all").trim();
    const q = String(ui.byId("q").value || "").trim();
    if (sla !== "all") parts.push(`sla=${sla}`);
    if (q) parts.push(`q=${q}`);
    ui.setText("filterSummary", parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні");
  }
  function renderFocusRows(rows, emptyText) {
    const tbody = ui.byId("focusTbl").querySelector("tbody");
    tbody.innerHTML = "";
    for (const item of rows) {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><code>${ui.esc(item.id)}</code></td>
        <td class="mobileHide progressiveCol"><code>${ui.esc(item.route)}</code></td>
        <td>${slaBadge(item.sla_state)}</td>
        <td><span class="badge warn">+${Number(item.eta_delay_min || 0)} хв</span></td>
        <td class="mobileHide progressiveCol"><code>${Number(item.pending_batches || 0)} / ${Number(item.incidents_open || 0)}</code></td>
        <td>${ui.esc(item.hint)}</td>
      `;
      tbody.appendChild(row);
    }
    ui.applyEmptyTables();
  }
  function renderAllRows(rows, emptyText) {
    const tbody = ui.byId("allTbl").querySelector("tbody");
    tbody.innerHTML = "";
    for (const item of rows) {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><code>${ui.esc(item.id)}</code></td>
        <td class="mobileHide progressiveCol"><code>${ui.esc(item.route)}</code></td>
        <td>${stateBadge(item.state)}</td>
        <td>${slaBadge(item.sla_state)}</td>
        <td><span class="badge warn">+${Number(item.eta_delay_min || 0)} хв</span></td>
        <td class="mobileHide progressiveCol"><code>${ui.esc(item.updated_at)}</code></td>
        <td class="mobileHide progressiveCol">${ui.esc(item.hint)}</td>
      `;
      tbody.appendChild(row);
    }
    ui.applyEmptyTables();
  }
  async function initWhoami() {
    const whoami = await ui.loadWhoami();
    const isSupport = String(whoami.role || "client") === "admin-support";
    ui.setText("whoami", isSupport ? "роль: admin-support" : "роль: client");
    ui.bindDetailsState("allVehiclesDetails", SECONDARY_STORAGE_KEY, isSupport);
  }
  async function refresh() {
    const sla = String(ui.byId("slaFilter").value || "all").trim().toLowerCase();
    const q = String(ui.byId("q").value || "").trim().toLowerCase();
    ui.setStatus("status", "Оновлення...");
    try {
      const params = new URLSearchParams();
      if (q) params.set("q", q);
      params.set("limit", "300");
      const data = await ui.apiGet(`/api/client/vehicles?${params.toString()}`);
      const items = Array.isArray(data.vehicles) ? data.vehicles : [];
      const filtered = items.filter((item) => matchesSla(item, sla));
      const attention = filtered.filter((item) => isAttention(item));
      renderFocusRows(attention, "Немає транспортів із SLA/ETA відхиленнями");
      renderAllRows(filtered, "Нічого не знайдено за фільтрами");

      const total = filtered.length;
      const good = filtered.filter((item) => String(item.state || "").toLowerCase() === "good").length;
      const warn = filtered.filter((item) => String(item.state || "").toLowerCase() === "warn").length;
      const bad = filtered.filter((item) => String(item.state || "").toLowerCase() === "bad").length;
      const slaRisk = filtered.filter((item) => String(item.sla_state || "").toLowerCase() === "risk").length;
      const etaValues = filtered.map((item) => Number(item.eta_delay_min || 0));
      const etaAvg = etaValues.length ? Math.round((etaValues.reduce((acc, value) => acc + value, 0) / etaValues.length) * 10) / 10 : 0;
      const etaMax = etaValues.length ? Math.max(...etaValues) : 0;
      ui.setText("sumTotal", `транспортів: ${total}`);
      ui.setText("sumGood", `в нормі: ${good}`);
      ui.setText("sumWarn", `із затримками: ${warn}`);
      ui.setText("sumBad", `проблемні: ${bad}`);
      ui.setText("sumSlaRisk", `SLA ризик: ${slaRisk}`);
      ui.setText("sumEta", `ETA avg +${etaAvg} хв · max +${etaMax} хв`);
      ui.setStatus("status", `OK: увага=${attention.length}, показано=${total}`);
    } catch (error) {
      renderFocusRows([], "Не вдалося завантажити транспортні ризики");
      renderAllRows([], "Не вдалося завантажити транспорти");
      ui.setText("sumTotal", "транспортів: 0");
      ui.setText("sumGood", "в нормі: 0");
      ui.setText("sumWarn", "із затримками: 0");
      ui.setText("sumBad", "проблемні: 0");
      ui.setText("sumSlaRisk", "SLA ризик: 0");
      ui.setText("sumEta", "ETA avg +0 хв · max +0 хв");
      ui.setStatus("status", `ПОМИЛКА: ${error && error.message ? error.message : "запит не виконано"}`);
    }
  }
  function refreshWithUrl() {
    syncQueryFromFilters();
    syncFilterSummary();
    refresh();
  }
  ui.byId("refresh").addEventListener("click", refreshWithUrl);
  ui.byId("slaFilter").addEventListener("change", refreshWithUrl);
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
        title="Passengers — Мої транспорти",
        header_title="Мої транспорти",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        current_nav="client-vehicles",
    )
