from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_history_page() -> str:
    chips_html = """
        <span class="chip">бакетована health-історія флоту + сповіщення</span>
        <span class="chip" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
        <div class="toolbarMain">
          <label><input id="auto" type="checkbox" checked /> авто</label>
          <button id="clearFilters">Скинути</button>
          <button id="refresh" class="primary">Оновити</button>
          <button id="copyLink" title="Скопіювати поточне посилання (з урахуванням фільтрів)">Скопіювати посилання</button>
          <details class="toolbarDetails" data-advanced-details="1">
            <summary>Параметри</summary>
            <div class="toolbarDetailsGrid">
              <select id="window" title="вікно даних">
                <option value="1h">1 година</option>
                <option value="6h">6 годин</option>
                <option value="24h" selected>24 години</option>
                <option value="7d">7 днів</option>
              </select>
              <select id="bucket" title="крок бакетування">
                <option value="60">1 хв</option>
                <option value="300" selected>5 хв</option>
                <option value="900">15 хв</option>
                <option value="3600">60 хв</option>
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
      <div class="sectionHead">
        <div class="sectionTitle">Останній бакет</div>
        <div class="sectionTools">
          <a class="quickLink" href="/admin/fleet/policy">Політика</a>
          <a class="quickLink" href="/admin/audit">Аудит</a>
          <a class="quickLink" href="/admin/fleet/notify-center">Доставка</a>
        </div>
      </div>
      <div class="kpi">
        <span class="badge" id="kPriority">пріоритет: —</span>
        <span class="badge" id="kTime">бакет: —</span>
        <span class="badge" id="kCentrals">центральних вузлів: 0</span>
        <span class="badge good" id="kGood">справні: 0</span>
        <span class="badge warn" id="kWarn">попередження: 0</span>
        <span class="badge bad" id="kBad">критичні: 0</span>
        <span class="badge" id="kAlerts">алерти: 0</span>
        <span class="badge" id="kPending">у черзі: 0</span>
        <span class="badge bad" id="kNotifFail">помилки сповіщень: 0</span>
      </div>
    </div>

    <div class="card">
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code>/api/admin/fleet/metrics/history</code></span>
        <span class="metaChip sort">сортування: <code>нові → старі</code></span>
        <span class="metaChip mode" id="historyWindowChip">вікно: —</span>
      </div>
      <div class="tableWrap">
        <table id="tbl" style="min-width: 980px;">
          <thead>
            <tr>
              <th>Бакет</th>
              <th>Пріоритет</th>
              <th>Центральні вузли</th>
              <th>Справні</th>
              <th>Попередження</th>
              <th>Критичні</th>
              <th>Алерти</th>
              <th>У черзі</th>
              <th>WG застарілий</th>
              <th>Сповіщень надіслано</th>
              <th>Помилки сповіщень</th>
              <th>Пропущено сповіщень</th>
              <th>Дії</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>
    """
    script = """
  const ui = window.AdminUiKit;
  const DEFAULT_WINDOW = "24h";
  const DEFAULT_BUCKET = "300";
  function setStatus(s) { ui.setStatus("status", s); }
  function setSelectIfValid(id, value, allowed) {
    const normalized = String(value || "").trim();
    const element = ui.byId(id);
    if (!element) return;
    if (allowed.has(normalized)) element.value = normalized;
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    setSelectIfValid("window", params.get("window") || DEFAULT_WINDOW, new Set(["1h", "6h", "24h", "7d"]));
    const bucket = params.get("bucket_sec") || params.get("bucket");
    if (bucket !== null) setSelectIfValid("bucket", String(bucket), new Set(["60", "300", "900", "3600"]));
  }
  function resetFilters() {
    ui.byId("window").value = DEFAULT_WINDOW;
    ui.byId("bucket").value = DEFAULT_BUCKET;
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const windowVal = ui.val("window", DEFAULT_WINDOW);
    const bucketVal = ui.val("bucket", DEFAULT_BUCKET);
    if (windowVal && windowVal !== DEFAULT_WINDOW) params.set("window", windowVal);
    if (bucketVal && bucketVal !== DEFAULT_BUCKET) params.set("bucket_sec", bucketVal);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const parts = [];
    const windowVal = ui.val("window", DEFAULT_WINDOW);
    const bucketVal = ui.val("bucket", DEFAULT_BUCKET);
    const windowText = windowVal || DEFAULT_WINDOW;
    const bucketText = bucketVal || DEFAULT_BUCKET;
    ui.setText("historyWindowChip", `вікно: ${windowText} · крок: ${bucketText}s`);
    if (windowVal && windowVal !== DEFAULT_WINDOW) parts.push(`вікно=${windowVal}`);
    if (bucketVal && bucketVal !== DEFAULT_BUCKET) parts.push(`крок=${bucketVal}s`);
    const node = ui.byId("filterSummary");
    if (!node) return;
    node.textContent = parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні";
  }
  function priorityClass(bucket) {
    if ((bucket.bad || 0) > 0) return "bad";
    if ((bucket.warn || 0) > 0 || (bucket.alerts_total || 0) > 0 || (bucket.notifications_failed || 0) > 0) return "warn";
    return "good";
  }
  function priorityLabel(level) {
    if (level === "bad") return "КРИТИЧНО";
    if (level === "warn") return "ПОПЕРЕДЖЕННЯ";
    return "СПРАВНО";
  }
  function setLatest(bucket) {
    const priority = priorityClass(bucket);
    const priorityNode = document.getElementById("kPriority");
    priorityNode.className = `badge ${priority}`;
    priorityNode.textContent = `пріоритет: ${priorityLabel(priority)}`;
    document.getElementById("kTime").textContent = `бакет: ${bucket.ts_bucket || "—"}`;
    document.getElementById("kCentrals").textContent = `центральних вузлів: ${bucket.centrals || 0}`;
    document.getElementById("kGood").textContent = `справні: ${bucket.good || 0}`;
    document.getElementById("kWarn").textContent = `попередження: ${bucket.warn || 0}`;
    document.getElementById("kBad").textContent = `критичні: ${bucket.bad || 0}`;
    document.getElementById("kAlerts").textContent = `алерти: ${bucket.alerts_total || 0}`;
    document.getElementById("kPending").textContent = `у черзі: ${bucket.pending_batches_total || 0}`;
    document.getElementById("kNotifFail").textContent = `помилки сповіщень: ${bucket.notifications_failed || 0}`;
  }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const windowVal = ui.val("window", DEFAULT_WINDOW);
      const bucketVal = parseInt(ui.val("bucket", DEFAULT_BUCKET), 10);
      const params = new URLSearchParams();
      params.set("window", windowVal);
      params.set("bucket_sec", Number.isFinite(bucketVal) ? String(bucketVal) : DEFAULT_BUCKET);
      const data = await ui.apiGet(`/api/admin/fleet/metrics/history?${params.toString()}`);
      const buckets = Array.isArray(data.buckets) ? data.buckets : [];

      const tbody = document.querySelector("#tbl tbody");
      tbody.innerHTML = "";
      if (buckets.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = '<td colspan="13"><span class="badge">—</span> Немає даних за вибране вікно</td>';
        tbody.appendChild(row);
        setLatest({});
      } else {
        setLatest(buckets[buckets.length - 1]);
        for (const item of buckets.slice().reverse()) {
          const pClass = priorityClass(item);
          const row = document.createElement("tr");
          row.innerHTML = `
            <td><code>${ui.esc(item.ts_bucket || "—")}</code></td>
            <td><span class="badge ${pClass}">${priorityLabel(pClass)}</span></td>
            <td>${ui.esc(item.centrals ?? 0)}</td>
            <td>${ui.esc(item.good ?? 0)}</td>
            <td>${ui.esc(item.warn ?? 0)}</td>
            <td>${ui.esc(item.bad ?? 0)}</td>
            <td>${ui.esc(item.alerts_total ?? 0)}</td>
            <td>${ui.esc(item.pending_batches_total ?? 0)}</td>
            <td>${ui.esc(item.wg_stale ?? 0)}</td>
            <td>${ui.esc(item.notifications_sent ?? 0)}</td>
            <td>${ui.esc(item.notifications_failed ?? 0)}</td>
            <td>${ui.esc(item.notifications_skipped ?? 0)}</td>
            <td>${ui.esc(item.alert_actions ?? 0)}</td>
          `;
          tbody.appendChild(row);
        }
      }
      ui.setText("updatedAt", `оновлено: ${buckets[buckets.length - 1]?.ts_bucket || new Date().toLocaleString("uk-UA")}`);
      setStatus(`OK: бакетів=${buckets.length}, вікно=${data.window || "24h"}, крок=${data.bucket_sec || "300"}с`);
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
  ui.byId("bucket").addEventListener("change", refreshWithUrl);
  applyFiltersFromQuery();
  syncQueryFromFilters();
  syncFilterSummary();
  refresh();
  setInterval(() => { if (ui.byId("auto").checked) refresh(); }, 15000);
    """
    return render_admin_shell(
        title="Адмін-панель Passengers — Історія KPI",
        header_title="Історія KPI",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        max_width=1300,
        current_nav="history",
    ).strip()
