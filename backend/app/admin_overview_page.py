from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_overview_page() -> str:
    chips_html = """
        <span class="chip">MVP</span>
        <span id="fleetState" class="badge good">СПРАВНО</span>
        <span id="whoami" class="chip">роль: —</span>
        <span id="updatedAt" class="chip">оновлено: —</span>
    """
    toolbar_html = """
        <div class="toolbarMain">
          <input id="q" type="text" placeholder="фільтр: вузол / транспорт / код / повідомлення" />
          <label><input id="auto" type="checkbox" checked /> авто</label>
          <button id="clearFilters">Скинути</button>
          <button id="refresh" class="primary">Оновити</button>
          <button id="copyLink" title="Скопіювати поточне посилання (з урахуванням фільтрів)">Скопіювати посилання</button>
        </div>
        <div class="toolbarMeta">
          <span class="metaChip sort" id="filterSummary">фільтри: стандартні</span>
          <span class="status" id="status"></span>
        </div>
    """
    body_html = """
    <div class="dashGrid">
      <div class="card dashStat"><div class="statlabel">Центральні вузли</div><div class="statvalue" id="vCentrals">0</div></div>
      <div class="card dashStat"><div class="statlabel">Частка справних</div><div class="statvalue good" id="vHealthy">0%</div></div>
      <div class="card dashStat"><div class="statlabel">Попередж./Критич.</div><div class="statvalue warn" id="vWarnBad">0 / 0</div></div>
      <div class="card dashStat"><div class="statlabel">Пакети в черзі</div><div class="statvalue bad" id="vPending">0</div></div>
      <div class="card dashStat"><div class="statlabel">Відкриті інциденти</div><div class="statvalue warn" id="vIncOpen">0</div></div>
      <div class="card dashStat"><div class="statlabel">Порушення SLA</div><div class="statvalue bad" id="vIncSla">0</div></div>
      <div class="card dashStat"><div class="statlabel">Невдалі сповіщення (24г)</div><div class="statvalue bad" id="vNotifFailed">0</div></div>
      <div class="card dashStat"><div class="statlabel">Заборонені запити (24г)</div><div class="statvalue warn" id="vForbidden">0</div></div>

      <div class="card dashWide" id="emptyState" hidden>
        <div class="sectionHead">
          <div class="sectionTitle">Немає даних флоту (ще немає heartbeat)</div>
          <div class="sectionTools">
            <a class="quickLink" href="/admin/wg">WireGuard</a>
            <a class="quickLink" href="/admin/fleet">Моніторинг флоту</a>
            <a class="quickLink" href="/admin/fleet/incidents?status=open&include_resolved=0">Інциденти</a>
          </div>
        </div>
	        <div class="muted">Це очікувано на ранньому етапі. Виконайте мінімальний чекліст, щоб підняти перший транспорт (central).</div>
	        <div class="kpi">
	          <span class="metaChip source">джерела: <code>/api/admin/fleet/monitor</code> + <code>/api/admin/fleet/incidents</code></span>
	          <span class="metaChip sort">оновлення: <code>10s</code> (авто)</span>
	        </div>
	        <div class="wgBox uMt10">
	          <div class="wgTitle">WireGuard статус (швидка перевірка)</div>
	          <div id="wgSummary" class="wgSummary">завантаження...</div>
	          <div class="wgHint muted">Джерело: <code>/api/admin/wg/peers</code>. Якщо немає handshake — флот не з’явиться.</div>
	        </div>
	        <ol class="hint uMt10" style="line-height:1.6;">
	          <li>Перевірте VPN: на <a href="/admin/wg">WireGuard</a> має бути handshake для central (вік &lt; 2 хв).</li>
	          <li>Перевірте, що central надсилає heartbeat у backend (після першого підключення таблиці заповняться автоматично).</li>
	          <li>Якщо є heartbeat, але тут пусто — відкрийте <a href="/admin/fleet">флот</a> і перевірте фільтри/режим <code>Просто</code>.</li>
	        </ol>
	      </div>

      <div class="card dashWide" id="commissionCard">
        <div class="sectionHead">
          <div class="sectionTitle">Швидке підключення транспорту (commissioning)</div>
          <div class="sectionTools">
            <a class="quickLink" href="/admin/wg">WireGuard</a>
            <a class="quickLink" href="/admin/fleet">Флот</a>
            <a class="quickLink" href="/admin/fleet/policy">Політика</a>
          </div>
	        </div>
	        <div class="muted">Введіть <code>central_id</code> (рекомендовано <code>sys-XXXX</code>) і відкривайте потрібні сторінки одним кліком.</div>
	        <div class="toolbar uJcStart uMt10">
	          <input id="commissionCentral" type="text" placeholder="central_id (наприклад sys-0002)" class="uMinW240" />
	          <a id="goCentral" class="quickLink disabledLink" href="#">Вузол</a>
	          <a id="goIncidents" class="quickLink disabledLink" href="#">Інциденти</a>
	          <a id="goPolicy" class="quickLink disabledLink" href="#">Персональні override-и</a>
	          <a id="goNotify" class="quickLink disabledLink" href="#">Центр сповіщень</a>
	          <button id="copyCommission" class="smallbtn" disabled>Копіювати набір</button>
	        </div>
	        <div id="commissionSuggestions" class="suggestionsRow" hidden></div>
	        <div class="muted uMt8" id="commissionHint">—</div>
	      </div>

      <div class="card dashWide">
      <details id="overviewSecondaryDetails" class="domainSplitDetails" data-advanced-details="1">
        <summary>Операційні таблиці (SLA / увага / алерти)</summary>
        <div class="domainSplitHint">
          Якщо потрібен глибокий triage, відкрийте профільні сторінки домена <a class="quickLink" href="/admin/fleet">Флот</a>,
          <a class="quickLink" href="/admin/fleet/incidents?status=open&include_resolved=0">Інциденти</a>,
          <a class="quickLink" href="/admin/fleet/alerts">Алерти</a>.
        </div>

	        <div class="card dashWide">
	          <div class="sectionHead">
	            <div class="sectionTitle">SLA таймери інцидентів</div>
	            <div class="sectionTools">
	              <a class="quickLink" href="/admin/fleet/incidents?status=open&include_resolved=0">Всі інциденти</a>
              <a class="quickLink" href="/admin/fleet/alerts">Оперативні алерти</a>
            </div>
          </div>
          <div class="tableMeta">
            <span class="metaChip source">джерело: <code>/api/admin/fleet/incidents?include_resolved=0</code></span>
            <span class="metaChip sort">сортування: <code>ризик SLA ↓</code></span>
          </div>
          <div class="muted">Активні інциденти (відкриті/підтверджені/заглушені), сортовано за ризиком порушення SLA</div>
          <div class="tableWrap">
            <table id="slaTbl" style="min-width: 940px;">
              <thead>
                <tr>
                  <th>Рівень</th>
                  <th>Вузол</th>
                  <th>Транспорт</th>
                  <th>Код</th>
                  <th>SLA таймер</th>
                  <th>Стан</th>
                  <th>Деталі</th>
                </tr>
              </thead>
              <tbody></tbody>
            </table>
	          </div>
	        </div>

		        <div class="card dashWide">
		          <div class="sectionHead">
		            <div class="sectionTitle">Потребує дій</div>
		            <div class="sectionTools">
		              <a class="quickLink" href="/admin/fleet">Флот</a>
	              <a class="quickLink" href="/admin/fleet/incidents?status=open&include_resolved=0">Інциденти</a>
	              <a class="quickLink" href="/admin/wg">WireGuard</a>
	            </div>
	          </div>
          <div class="tableMeta">
            <span class="metaChip source">джерело: <code>/api/admin/fleet/monitor.attention</code></span>
            <span class="metaChip sort">сортування: <code>severity ↓</code>, далі <code>age ↓</code></span>
          </div>
          <div class="tableWrap">
            <table id="attentionTbl" style="min-width: 1020px;">
              <thead>
                <tr>
                  <th>Рівень</th>
                  <th>Вузол</th>
                  <th>Транспорт</th>
                  <th>Причини</th>
                  <th>Інциденти</th>
                  <th>Черга/WG</th>
                  <th>Вік heartbeat</th>
                  <th>Деталі</th>
                </tr>
              </thead>
              <tbody></tbody>
            </table>
	          </div>
	        </div>

		        <div class="card dashWide">
		          <div class="sectionHead">
		            <div class="sectionTitle">Активні алерти</div>
		            <div class="sectionTools">
		              <a class="quickLink" href="/admin/fleet/notify-center">Центр сповіщень</a>
	              <a class="quickLink" href="/admin/fleet/notifications">Правила сповіщень</a>
	            </div>
	          </div>
          <div class="tableMeta">
            <span class="metaChip source">джерело: <code>/api/admin/fleet/monitor.alerts</code></span>
            <span class="metaChip sort">сортування: <code>bad → warn → good</code>, далі <code>age ↓</code></span>
          </div>
          <div class="tableWrap">
            <table id="alertsTbl" style="min-width: 1020px;">
              <thead>
                <tr>
                  <th>Рівень</th>
                  <th>Вузол</th>
                  <th>Транспорт</th>
                  <th>Код</th>
                  <th>Повідомлення</th>
                  <th>Вік heartbeat</th>
                  <th>SLA таймер</th>
                  <th>Деталі</th>
                </tr>
              </thead>
              <tbody></tbody>
            </table>
	          </div>
	        </div>
	      </details>
	    </div>
	    """
    extra_css = """
    .dashGrid { display: grid; grid-template-columns: repeat(12, 1fr); gap: 14px; margin-top: 6px; }
    .dashStat { grid-column: span 2; min-height: 96px; }
    .dashWide { grid-column: span 12; }
	    .statlabel { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
	    .statvalue { font-size: 24px; font-weight: 700; }
	    .slaMeter { width: 100%; min-width: 130px; height: 7px; border-radius: 999px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.08); overflow: hidden; margin-top: 5px; }
	    .slaFill { display:block; height: 100%; width: 4%; border-radius: 999px; }
	    .slaFill.good { background: var(--good); }
	    .slaFill.warn { background: var(--warn); }
	    .slaFill.bad { background: var(--bad); }
	    .disabledLink { pointer-events: none; opacity: .55; }
	    .suggestionsRow { margin-top: 10px; display:flex; flex-wrap: wrap; gap: 8px; align-items: center; }
	    .suggestLabel { font-size: 11px; color: var(--muted); letter-spacing: .03em; text-transform: uppercase; }
	    .suggestChip { display:inline-flex; align-items:center; gap: 8px; border-radius: 999px; border: 1px solid rgba(255,255,255,.14); background: rgba(255,255,255,.03); padding: 6px 10px; cursor: pointer; user-select:none; }
    .suggestChip:hover { border-color: rgba(127,176,255,.44); background: rgba(127,176,255,.10); }
    .suggestChip code { font-size: 12px; }
    .suggestAge { font-size: 11px; color: #c9d6ef; }
    .reason { margin-bottom: 5px; }
    .reason:last-child { margin-bottom: 0; }
    .empty { color: var(--muted); font-size: 13px; padding: 12px; }
    @media (max-width: 1220px) { .dashStat { grid-column: span 3; } }
    @media (max-width: 960px) { .dashStat { grid-column: span 4; } }
    @media (max-width: 700px) { .dashStat { grid-column: span 12; } }
    """.strip()
    script = """
  const ui = window.AdminUiKit;
  const OVERVIEW_SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_overview_secondary_details_v1";
  function isNil(value) { return value === null || value === undefined; }
  function nz(value, fallback) { return isNil(value) ? fallback : value; }
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
  function sevLabel(level) {
    const val = String(level || "").toLowerCase();
    if (val === "good") return "СПРАВНО";
    if (val === "warn") return "ПОПЕРЕДЖЕННЯ";
    return "КРИТИЧНО";
  }
  function sevClass(level) {
    const val = String(level || "").toLowerCase();
    if (val === "good" || val === "warn" || val === "bad") return val;
    return "bad";
  }
  function incidentKey(centralId, code) {
    return `${String(centralId || "").toLowerCase()}::${String(code || "").toLowerCase()}`;
  }
  function isActiveIncidentStatus(status) {
    const normalized = String(status || "").toLowerCase();
    return normalized === "open" || normalized === "acked" || normalized === "silenced";
  }
  function incidentStatusLabel(status) {
    const normalized = String(status || "").toLowerCase();
    if (normalized === "acked") return "ПІДТВЕРДЖЕНО";
    if (normalized === "silenced") return "ЗАГЛУШЕНО";
    if (normalized === "open") return "ВІДКРИТО";
    return "НЕВІДОМО";
  }
  function buildIncidentIndex(incidents) {
    const index = new Map();
    for (const item of Array.isArray(incidents) ? incidents : []) {
      index.set(incidentKey(item.central_id, item.code), item);
    }
    return index;
  }
  function slaTimerHtml(incident) {
    if (!incident) return '<span class="muted">—</span>';
    const ageSec = Number(incident.age_sec || 0);
    const targetSec = Number(incident.sla_target_sec || 0);
    const breached = !!incident.sla_breached;
    if (!Number.isFinite(targetSec) || targetSec <= 0) {
      return '<span class="badge">без SLA</span>';
    }
    const ratio = ageSec / targetSec;
    const severity = breached || ratio >= 1 ? "bad" : (ratio >= 0.75 ? "warn" : "good");
    const width = Math.max(4, Math.min(100, Math.round(ratio * 100)));
    const leftSec = Math.max(0, targetSec - ageSec);
    const label = breached ? "порушено" : `залишилось ${fmtAge(leftSec)}`;
    return `
      <div><span class="badge ${severity}">${label}</span></div>
      <div class="slaMeter"><span class="slaFill ${severity}" style="width:${width}%"></span></div>
      <div class="muted"><code>${fmtAge(ageSec)} / ${fmtAge(targetSec)}</code></div>
    `;
  }
  function setFleetState(level, message) {
    const badge = ui.byId("fleetState");
    const normalized = sevClass(level);
    badge.className = `badge ${normalized}`;
    badge.textContent = `${sevLabel(normalized)}${message ? (" · " + message) : ""}`;
  }
  function getFilterQuery() {
    return String(ui.byId("q").value || "").trim().toLowerCase();
  }
  function syncFilterSummary() {
    const parts = [];
    const query = String(ui.byId("q").value || "").trim();
    const central = String(ui.byId("commissionCentral")?.value || "").trim();
    if (query) parts.push(`q=${query}`);
    if (central) parts.push(`вузол=${central}`);
    const node = ui.byId("filterSummary");
    if (!node) return;
    node.textContent = parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні";
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const query = params.get("q");
    if (query !== null) ui.byId("q").value = String(query);
    const central = params.get("central") || params.get("central_id");
    if (central !== null && ui.byId("commissionCentral")) ui.byId("commissionCentral").value = String(central);
  }
  function resetFilters() {
    ui.byId("q").value = "";
    if (ui.byId("commissionCentral")) ui.byId("commissionCentral").value = "";
    updateCommissioningLinks();
  }
  function initOverviewSecondaryDetails() {
    const node = document.getElementById("overviewSecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {
      const raw = String(localStorage.getItem(OVERVIEW_SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {}
    node.addEventListener("toggle", () => {
      try { localStorage.setItem(OVERVIEW_SECONDARY_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); } catch (_error) {}
    });
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const query = String(ui.byId("q").value || "").trim();
    const central = String(ui.byId("commissionCentral")?.value || "").trim();
    if (query) params.set("q", query);
    if (central) params.set("central_id", central);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function reasonHtml(reasons) {
    if (!Array.isArray(reasons) || reasons.length === 0) return '<span class="muted">—</span>';
    return reasons.slice(0, 4).map((item) => {
      const sev = sevClass(item.severity);
      return `<div class="reason"><span class="badge ${sev}">${ui.esc(sevLabel(sev))}</span> <code>${ui.esc(item.code || "alert")}</code> ${ui.esc(item.message || "")}</div>`;
    }).join("");
  }
  function renderAttention(rows, query) {
    const tbody = document.querySelector("#attentionTbl tbody");
    tbody.innerHTML = "";
    const list = Array.isArray(rows) ? rows : [];
    const filtered = !query ? list : list.filter((row) => {
        const hay = [
          row.central_id,
          row.vehicle_id,
          ...(Array.isArray(row.reasons) ? row.reasons.map((item) => `${item.code} ${item.message}`) : []),
        ].join(" ").toLowerCase();
        return hay.includes(query);
    });
    if (filtered.length === 0) {
      tbody.innerHTML = query
        ? '<tr><td colspan="8" class="empty">Немає записів за фільтром</td></tr>'
        : '<tr><td colspan="8" class="empty">Немає вузлів, що потребують дій</td></tr>';
      return;
    }
      for (const row of filtered) {
        const sev = sevClass(row.severity);
        const central = encodeURIComponent(row.central_id || "");
        const incidentsUrl = `/admin/fleet/incidents?central_id=${central}&include_resolved=0`;
        const centralUrl = `/admin/fleet/central/${central}`;
        const tr = document.createElement("tr");
        tr.innerHTML = `
          <td><span class="badge ${sev}">${ui.esc(sevLabel(sev))}</span></td>
          <td><a href="${centralUrl}"><code>${ui.esc(row.central_id || "—")}</code></a></td>
        <td><code>${ui.esc(row.vehicle_id || "—")}</code></td>
        <td>${reasonHtml(row.reasons)}</td>
        <td><a href="${incidentsUrl}"><code>відкриті ${row.incidents_open || 0}</code></a> · критичні ${row.incidents_bad || 0} · SLA ${row.incidents_sla_breached || 0}</td>
        <td><code>черга ${row.pending_batches || 0}</code> · <code>wg ${fmtAge(row.wg_latest_handshake_age_sec)}</code></td>
        <td><code>${fmtAge(row.heartbeat_age_sec)}</code></td>
        <td>
          <div class="drillBtns">
            <a class="drillBtn" href="${centralUrl}">Вузол</a>
            <a class="drillBtn" href="${incidentsUrl}">Інциденти</a>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    }
  }
  function renderAlerts(rows, query, incidentsIndex) {
    const tbody = document.querySelector("#alertsTbl tbody");
    tbody.innerHTML = "";
    const list = Array.isArray(rows) ? rows : [];
    const filtered = !query ? list : list.filter((alert) => {
      const hay = [alert.central_id, alert.vehicle_id, alert.code, alert.message].join(" ").toLowerCase();
      return hay.includes(query);
    });
    if (filtered.length === 0) {
      const tr = document.createElement("tr");
      tr.innerHTML = query
        ? '<td colspan="8" class="empty">Немає активних алертів за фільтром</td>'
        : '<td colspan="8" class="empty">Немає активних алертів</td>';
      tbody.appendChild(tr);
      return;
    }
    for (const alert of filtered) {
      const sev = sevClass(alert.severity);
      const tr = document.createElement("tr");
      const central = encodeURIComponent(alert.central_id || "");
      const code = encodeURIComponent(alert.code || "");
      const incidentUrl = `/admin/fleet/incidents/${central}/${code}`;
      const centralUrl = `/admin/fleet/central/${central}`;
      const incident = incidentsIndex.get(incidentKey(alert.central_id, alert.code));
      tr.innerHTML = `
        <td><span class="badge ${sev}">${ui.esc(sevLabel(sev))}</span></td>
        <td><code>${ui.esc(alert.central_id || "—")}</code></td>
        <td><code>${ui.esc(alert.vehicle_id || "—")}</code></td>
        <td><a href="${incidentUrl}"><code>${ui.esc(alert.code || "alert")}</code></a></td>
        <td>${ui.esc(alert.message || "")}</td>
        <td><code>${ui.esc(fmtAge(alert.age_sec))}</code></td>
        <td>${slaTimerHtml(incident)}</td>
        <td>
          <div class="drillBtns">
            <a class="drillBtn" href="${centralUrl}">Вузол</a>
            <a class="drillBtn" href="${incidentUrl}">Інцидент</a>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    }
  }
  function renderSlaTimers(incidents, query) {
    const tbody = document.querySelector("#slaTbl tbody");
    tbody.innerHTML = "";
    const active = (Array.isArray(incidents) ? incidents : []).filter((item) => isActiveIncidentStatus(item.status));
    const filtered = !query ? active : active.filter((item) => {
      const hay = [item.central_id, item.vehicle_id, item.code, item.message].join(" ").toLowerCase();
      return hay.includes(query);
    });
    filtered.sort((left, right) => {
      const leftTarget = Number(left.sla_target_sec || 0);
      const rightTarget = Number(right.sla_target_sec || 0);
      const leftRatio = leftTarget > 0 ? Number(left.age_sec || 0) / leftTarget : 0;
      const rightRatio = rightTarget > 0 ? Number(right.age_sec || 0) / rightTarget : 0;
      if (Boolean(right.sla_breached) !== Boolean(left.sla_breached)) return Boolean(right.sla_breached) ? 1 : -1;
      if (rightRatio !== leftRatio) return rightRatio - leftRatio;
      return Number(right.age_sec || 0) - Number(left.age_sec || 0);
    });
    const top = filtered.slice(0, 18);
    if (top.length === 0) {
      tbody.innerHTML = query
        ? '<tr><td colspan="7" class="empty">Немає активних інцидентів за фільтром</td></tr>'
        : '<tr><td colspan="7" class="empty">Активних інцидентів немає</td></tr>';
      return;
    }
    for (const item of top) {
      const sev = sevClass(item.severity || "warn");
      const central = encodeURIComponent(item.central_id || "");
      const code = encodeURIComponent(item.code || "");
      const incidentUrl = `/admin/fleet/incidents/${central}/${code}`;
      const centralUrl = `/admin/fleet/central/${central}`;
      const tr = document.createElement("tr");
      tr.innerHTML = `
        <td><span class="badge ${sev}">${ui.esc(sevLabel(sev))}</span></td>
        <td><a href="${centralUrl}"><code>${ui.esc(item.central_id || "—")}</code></a></td>
        <td><code>${ui.esc(item.vehicle_id || "—")}</code></td>
        <td><a href="${incidentUrl}"><code>${ui.esc(item.code || "incident")}</code></a></td>
        <td>${slaTimerHtml(item)}</td>
        <td><span class="badge ${item.sla_breached ? "bad" : "warn"}">${ui.esc(incidentStatusLabel(item.status))}</span></td>
        <td>
          <div class="drillBtns">
            <a class="drillBtn" href="${centralUrl}">Вузол</a>
            <a class="drillBtn" href="${incidentUrl}">Інцидент</a>
          </div>
        </td>
      `;
      tbody.appendChild(tr);
    }
  }
  async function refreshWgSummary() {
    const node = ui.byId("wgSummary");
    if (!node) return;
    node.textContent = "завантаження...";
    try {
      const data = await ui.apiGet("/api/admin/wg/peers");
      const peers = Array.isArray(data.peers) ? data.peers : [];
      let good = 0;
      let warn = 0;
      let bad = 0;
      let unknown = 0;
      let bestFreshAge = null;
      for (const p of peers) {
        const age = p.latest_handshake_age_sec;
        if (age === null || age === undefined || age < 0) {
          unknown += 1;
          continue;
        }
        if (bestFreshAge === null || age < bestFreshAge) bestFreshAge = age;
        if (age <= 120) good += 1;
        else if (age <= 600) warn += 1;
        else bad += 1;
      }
      const ts = String(data.ts || "").trim();
      const freshText = bestFreshAge === null ? "—" : fmtAge(bestFreshAge);
      const parts = [
        `пірів=${peers.length}`,
        `fresh<2хв=${good}`,
        `warn<10хв=${warn}`,
        `stale>10хв=${bad}`,
        `без handshake=${unknown}`,
        `найсвіжіший=${freshText}`,
      ];
      const tail = ts ? ` · ts=<code>${ui.esc(ts)}</code>` : "";
      node.innerHTML = `<span class="badge ${bad > 0 ? "warn" : "good"}">WG</span> ${ui.esc(parts.join(" · "))}${tail}`;
    } catch (error) {
      node.innerHTML = `<span class="badge bad">WG</span> помилка читання <code>/api/admin/wg/peers</code>: <code>${ui.esc(String(error || ""))}</code>`;
    }
  }
  async function loadWhoami() {
    const data = await ui.loadWhoami();
    ui.setText("whoami", `роль: ${data.role || "viewer"} · актор: ${data.actor || "невідомо"}`);
  }
  let monitorData = null;
  let monitorIncidents = [];
  let monitorIncidentsIndex = new Map();
  const SYS_ID_RE = /^sys-[0-9]{4}$/i;
  function setCommissioningDisabled(disabled) {
    const ids = ["goCentral", "goIncidents", "goPolicy", "goNotify"];
    for (const id of ids) {
      const node = ui.byId(id);
      if (!node) continue;
      node.classList.toggle("disabledLink", disabled);
    }
    ui.byId("copyCommission").disabled = disabled;
  }
  function updateCommissioningLinks() {
    const central = String(ui.byId("commissionCentral")?.value || "").trim();
    const hint = ui.byId("commissionHint");
    if (!central) {
      setCommissioningDisabled(true);
      if (hint) hint.innerHTML = "Введіть <code>central_id</code>, щоб активувати швидкі посилання.";
      return;
    }
    const formatOk = SYS_ID_RE.test(central);
    const centralEnc = encodeURIComponent(central);
    const urlCentral = `/admin/fleet/central/${centralEnc}`;
    const urlIncidents = `/admin/fleet/incidents?central_id=${centralEnc}&include_resolved=0`;
    const urlPolicy = `/admin/fleet/policy?central_id=${centralEnc}`;
    const urlNotify = `/admin/fleet/notify-center?central_id=${centralEnc}`;
    ui.byId("goCentral").href = urlCentral;
    ui.byId("goIncidents").href = urlIncidents;
    ui.byId("goPolicy").href = urlPolicy;
    ui.byId("goNotify").href = urlNotify;
    setCommissioningDisabled(false);
    if (hint) {
      const format = formatOk
        ? '<span class="badge good">формат OK</span>'
        : '<span class="badge warn">формат не sys-XXXX</span>';
      hint.innerHTML = `${format} · <code>${ui.esc(central)}</code> · <code>${ui.esc(urlCentral)}</code>`;
    }
  }

  async function refreshCommissioningSuggestions() {
    const row = ui.byId("commissionSuggestions");
    if (!row) return;
    row.innerHTML = "";
    row.hidden = true;
    try {
      const data = await ui.apiGet("/api/admin/wg/peers");
      const peers = Array.isArray(data.peers) ? data.peers : [];
      const ranked = peers
        .map((p) => ({
          name: String(p.name || "").trim(),
          age: (p.latest_handshake_age_sec === null || p.latest_handshake_age_sec === undefined) ? null : Number(p.latest_handshake_age_sec),
        }))
        .filter((p) => p.name.length > 0)
        .sort((a, b) => {
          const left = a.age === null || !Number.isFinite(a.age) ? Number.POSITIVE_INFINITY : a.age;
          const right = b.age === null || !Number.isFinite(b.age) ? Number.POSITIVE_INFINITY : b.age;
          return left - right;
        })
        .slice(0, 10);
      if (ranked.length === 0) return;
      row.hidden = false;
      const label = document.createElement("span");
      label.className = "suggestLabel";
      label.textContent = "WG пірі (клік щоб підставити)";
      row.appendChild(label);
      for (const p of ranked) {
        const chip = document.createElement("span");
        chip.className = "suggestChip";
        const ageText = p.age === null || !Number.isFinite(p.age) ? "handshake: —" : `handshake: ${fmtAge(p.age)}`;
        chip.innerHTML = `<code>${ui.esc(p.name)}</code> <span class="suggestAge">${ui.esc(ageText)}</span>`;
        chip.addEventListener("click", () => {
          const input = ui.byId("commissionCentral");
          if (input) input.value = p.name;
          updateCommissioningLinks();
          syncQueryFromFilters();
          syncFilterSummary();
        });
        row.appendChild(chip);
      }
    } catch (_error) {
      // ignore: suggestions are a convenience layer; keep page usable without them
    }
  }

  async function refresh() {
    setStatus("Завантаження...");
    try {
      const [data, incidentsData] = await Promise.all([
        ui.apiGet("/api/admin/fleet/monitor?window=24h&limit_alerts=60&limit_attention=60"),
        ui.apiGet("/api/admin/fleet/incidents?include_resolved=0&limit=1200"),
      ]);
      const activeIncidents = (Array.isArray(incidentsData.incidents) ? incidentsData.incidents : []).filter((item) => isActiveIncidentStatus(item.status));
      const incidentsIndex = buildIncidentIndex(activeIncidents);
      monitorData = data;
      monitorIncidents = activeIncidents;
      monitorIncidentsIndex = incidentsIndex;

      const fleet = data.fleet || {};
      const incidents = data.incidents || {};
      const notifications = data.notifications || {};
      const security = data.security || {};
      ui.byId("vCentrals").textContent = nz(fleet.centrals, 0);
      ui.byId("vHealthy").textContent = `${nz(fleet.healthy_ratio, 0)}%`;
      ui.byId("vWarnBad").textContent = `${nz(fleet.warn, 0)} / ${nz(fleet.bad, 0)}`;
      ui.byId("vPending").textContent = nz(fleet.pending_batches_total, 0);
      ui.byId("vIncOpen").textContent = nz(incidents.open, 0);
      ui.byId("vIncSla").textContent = nz(incidents.sla_breached, 0);
      ui.byId("vNotifFailed").textContent = nz(notifications.failed, 0);
      ui.byId("vForbidden").textContent = nz(security.forbidden_total, 0);

      const state = data.state || {};
      const centralsCount = Number(fleet.centrals || 0);
      if (centralsCount <= 0) {
        setFleetState("warn", "немає heartbeats");
        ui.byId("emptyState").hidden = false;
        await refreshWgSummary();
      } else {
        setFleetState(state.severity || "good", state.message || "");
        ui.byId("emptyState").hidden = true;
      }
      ui.byId("updatedAt").textContent = `оновлено: ${data.ts_generated || "—"}`;
      const query = getFilterQuery();
      renderSlaTimers(activeIncidents, query);
      renderAttention(data.attention || [], query);
      renderAlerts(data.alerts || [], query, incidentsIndex);
      setStatus(`OK · увага=${data.attention_total || 0} · алерти=${data.alerts_total || 0} · інциденти=${activeIncidents.length} · оновлено=${data.ts_generated || "?"}`);
    } catch (error) {
      setFleetState("bad", "помилка API моніторингу");
      setStatus(`ПОМИЛКА: ${error}`);
    }
  }
  function applyFilter() {
    if (!monitorData) return;
    const query = getFilterQuery();
    renderSlaTimers(monitorIncidents, query);
    renderAttention(monitorData.attention || [], query);
    renderAlerts(monitorData.alerts || [], query, monitorIncidentsIndex);
  }
  let timerId = null;
  function setAuto(enabled) {
    if (timerId) {
      clearInterval(timerId);
      timerId = null;
    }
    if (enabled) {
      timerId = setInterval(refresh, 10000);
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
  ui.byId("q").addEventListener("input", () => { syncQueryFromFilters(); syncFilterSummary(); applyFilter(); });
  ui.byId("commissionCentral")?.addEventListener("input", ui.debounce(() => { updateCommissioningLinks(); syncQueryFromFilters(); syncFilterSummary(); }, 220));
  ui.byId("commissionCentral")?.addEventListener("keydown", (event) => {
    if (event.key === "Enter") {
      event.preventDefault();
      updateCommissioningLinks();
      syncQueryFromFilters();
      syncFilterSummary();
    }
  });
  ui.byId("copyCommission")?.addEventListener("click", () => {
    const central = String(ui.byId("commissionCentral")?.value || "").trim();
    if (!central) return;
    const centralEnc = encodeURIComponent(central);
    const origin = window.location.origin;
    const lines = [
      `central_id=${central}`,
      `${origin}/admin/fleet/central/${centralEnc}`,
      `${origin}/admin/fleet/incidents?central_id=${centralEnc}&include_resolved=0`,
      `${origin}/admin/fleet/policy?central_id=${centralEnc}`,
      `${origin}/admin/fleet/notify-center?central_id=${centralEnc}`,
    ];
    ui.copyTextWithFallback(lines.join("\\n"), "Скопіюйте набір посилань:", "Набір посилань скопійовано", "Набір у prompt");
  });
  ui.byId("auto").addEventListener("change", (event) => { setAuto(Boolean(event.target && event.target.checked)); });
  applyFiltersFromQuery();
  initOverviewSecondaryDetails();
  updateCommissioningLinks();
  syncQueryFromFilters();
  syncFilterSummary();
  refreshCommissioningSuggestions();
  loadWhoami().then(refreshWithUrl);
  setAuto(true);
    """.strip()
    return render_admin_shell(
        title="Адмін-панель Passengers — Огляд",
        header_title="Огляд флоту",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        extra_css=extra_css,
        max_width=1320,
        current_nav="overview",
    ).strip()
