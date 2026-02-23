from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_wg_page() -> str:
    chips_html = """
        <span class="chip">піри WireGuard + handshake</span>
        <span class="chip" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
        <div class="toolbarMain">
          <input id="q" type="text" placeholder="пошук: назва / IP / endpoint / pubkey" />
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
    extra_css = ""
    body_html = """
    <div class="card uMb14">
      <div class="sectionHead">
        <div class="sectionTitle">Базова мережева діагностика (WireGuard піри)</div>
        <div class="sectionTools">
          <a class="quickLink" href="/admin/fleet">Стан флоту</a>
          <a class="quickLink" href="/admin/commission">Підключення</a>
          <a class="quickLink" href="/admin/audit">Аудит</a>
        </div>
      </div>
      <div class="summary">
        <span class="badge" id="peerTotal">пірів: 0</span>
        <span class="badge good" id="peerGood">справні: 0</span>
        <span class="badge warn" id="peerWarn">попередження: 0</span>
        <span class="badge bad" id="peerBad">критичні: 0</span>
      </div>
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code>/api/admin/wg/peers</code></span>
        <span class="metaChip sort">сортування: <code>name ↑</code></span>
        <span class="metaChip mode">оновлення: <code>~15s</code></span>
        <span class="metaChip mode">SLA: <code>good ≤ 120s</code>, <code>warn ≤ 600s</code></span>
      </div>
      <div class="tableWrap">
        <table id="tbl" style="min-width: 980px;">
          <thead>
            <tr>
              <th>Статус</th>
              <th>Назва</th>
              <th>Дозволені IP</th>
              <th>Ендпоінт</th>
              <th>Рукостискання</th>
              <th>Rx/Tx</th>
              <th>Конфіг peer</th>
              <th>Публічний ключ</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <details id="wgSecondaryDetails" class="domainSplitDetails" data-advanced-details="1">
      <summary>Конфіг сервера WireGuard (вторинна діагностика)</summary>
	      <div class="domainSplitHint">
	        Цей блок використовуйте для поглибленого аналізу конфігурації. Базовий операторський контроль виконуйте у таблиці пірів вище.
	      </div>
	      <div class="sectionHead uMt10">
	        <div>
	          <div class="sectionTitle">Конфіг сервера (редаговано)</div>
	          <div class="muted"><code>/api/admin/wg/conf</code></div>
	        </div>
	        <div class="sectionTools">
	          <button id="copyConf" class="smallbtn">Копіювати</button>
	        </div>
	      </div>
	      <pre class="tableWrap tableWrapPre uMaxH40vh"><code id="conf"></code></pre>
	    </details>
    """
    script = """
  const ui = window.AdminUiKit;
  const REFRESH_DELAY_MS = 240;
  const WG_SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_wg_secondary_details_v1";
  let wgConfLoaded = false;
  function setStatus(s) { ui.setStatus("status", s); }
  function q() { return (ui.byId("q").value || "").trim().toLowerCase(); }
  function resetFilters() { ui.byId("q").value = ""; }
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
  function fmtBytes(n) {
    if (n === null || n === undefined) return "—";
    const units = ["B","KiB","MiB","GiB","TiB"];
    let i = 0;
    let v = n;
    while (v >= 1024 && i < units.length - 1) { v /= 1024; i++; }
    return `${v.toFixed(i === 0 ? 0 : 1)} ${units[i]}`;
  }
  function peerClass(ageSec) {
    if (ageSec === null || ageSec === undefined) return "bad";
    if (ageSec < 0) return "bad";
    if (ageSec <= 120) return "good";
    if (ageSec <= 600) return "warn";
    return "bad";
  }
  function peerStatusLabel(level) {
    const normalized = String(level || "").toLowerCase();
    if (normalized === "good") return "СПРАВНО";
    if (normalized === "warn") return "ПОПЕРЕДЖЕННЯ";
    return "КРИТИЧНО";
  }
  function matches(p, query) {
    if (!query) return true;
    const hay = [
      p.name || "",
      (p.allowed_ips || []).join(","),
      p.endpoint || "",
      p.public_key || "",
    ].join(" ").toLowerCase();
    return hay.includes(query);
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const query = params.get("q");
    if (query !== null) ui.byId("q").value = String(query);
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const query = String(ui.byId("q").value || "").trim();
    if (query) params.set("q", query);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const parts = [];
    const query = String(ui.byId("q").value || "").trim();
    if (query) parts.push(`q=${query}`);
    const node = ui.byId("filterSummary");
    if (!node) return;
    node.textContent = parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні";
  }
  function initWgSecondaryDetails() {
    const node = document.getElementById("wgSecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {
      const raw = String(localStorage.getItem(WG_SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {}
    node.addEventListener("toggle", () => {
      try { localStorage.setItem(WG_SECONDARY_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); } catch (_error) {}
      if (node.open && !wgConfLoaded) loadConf();
    });
    if (node.open && !wgConfLoaded) loadConf();
  }

  async function fetchText(path) {
    const resp = await fetch(path);
    const text = await resp.text();
    if (!resp.ok) throw new Error(`${resp.status} ${text}`);
    return text;
  }

  async function refresh() {
    setStatus("Завантаження...");
    try {
      const data = await ui.apiGet("/api/admin/wg/peers");
      const peers = Array.isArray(data.peers) ? data.peers : [];
      const query = q();
      peers.sort((a,b) => (a.name||"").localeCompare(b.name||"") || String(a.allowed_ips||"").localeCompare(String(b.allowed_ips||"")));
      const tbody = document.querySelector("#tbl tbody");
      tbody.innerHTML = "";
      let shown = 0;
      let good = 0;
      let warn = 0;
      let bad = 0;
      for (const p of peers) {
        if (!matches(p, query)) continue;
        shown += 1;
        const tr = document.createElement("tr");
        const name = String(p.name || "");
        const allowed = (p.allowed_ips || []).join(", ");
        const endpoint = String(p.endpoint || "");
        const hsAge = p.latest_handshake_age_sec;
        const rx = fmtBytes(p.rx_bytes);
        const tx = fmtBytes(p.tx_bytes);
        const pub = String(p.public_key || "");
        const peerBlock = String(p.server_peer_block || "");
        const cls = peerClass(hsAge);
        if (cls === "good") good += 1;
        else if (cls === "warn") warn += 1;
        else bad += 1;
        const hsTs = String(p.latest_handshake_ts || "");
        const shortPub = pub ? (pub.slice(0,16) + "…") : "—";
        tr.innerHTML = `
          <td><span class="badge ${cls}">${ui.esc(peerStatusLabel(cls))}</span></td>
          <td>${name ? `<code>${ui.esc(name)}</code>` : "—"}</td>
          <td><code>${ui.esc(allowed)}</code></td>
          <td><code>${ui.esc(endpoint)}</code></td>
          <td>${ui.esc(fmtAge(hsAge))}<div class="muted"><code>${ui.esc(hsTs)}</code></div></td>
          <td><code>${ui.esc(rx)}</code> / <code>${ui.esc(tx)}</code></td>
          <td>
            <details>
              <summary>показати</summary>
              <div class="toolbar uJcStart uMt8">
                <button class="smallbtn" data-copy-peer="1">Копіювати</button>
              </div>
              <pre class="tableWrap tableWrapPre uMt8" style="max-height: 240px;"><code>${ui.esc(peerBlock)}</code></pre>
            </details>
          </td>
          <td><code title="${ui.esc(pub)}">${ui.esc(shortPub)}</code></td>
        `;
        tr.querySelector('button[data-copy-peer="1"]')?.addEventListener("click", () => {
          ui.copyTextWithFallback(peerBlock, "Скопіюйте peer-конфіг:", "Peer-конфіг скопійовано", "Peer-конфіг у prompt");
        });
        tbody.appendChild(tr);
      }
      document.getElementById("peerTotal").textContent = `пірів: ${shown}/${peers.length}`;
      document.getElementById("peerGood").textContent = `справні: ${good}`;
      document.getElementById("peerWarn").textContent = `попередження: ${warn}`;
      document.getElementById("peerBad").textContent = `критичні: ${bad}`;
      ui.setText("updatedAt", `оновлено: ${data.ts || new Date().toLocaleString("uk-UA")}`);
      setStatus(`OK: показано=${shown}/${peers.length} (q=${query || "—"})`);
    } catch (error) {
      setStatus("ПОМИЛКА: " + error);
    }
  }

  async function loadConf() {
    setStatus("Завантаження конфігу...");
    try {
      const text = await fetchText("/api/admin/wg/conf");
      ui.byId("conf").textContent = text;
      wgConfLoaded = true;
      setStatus("OK: конфіг завантажено");
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
  ui.byId("copyConf").addEventListener("click", () => ui.copyTextWithFallback(ui.byId("conf").textContent || "", "Скопіюйте конфіг:", "Конфіг сервера скопійовано", "Конфіг у prompt"));
  ui.bindClearFilters("clearFilters", resetFilters, refreshWithUrl);
  ui.bindDebouncedInputs(["q"], refreshWithUrl, REFRESH_DELAY_MS);
  ui.bindEnterRefresh(["q"], refreshWithUrl);
  initWgSecondaryDetails();
  applyFiltersFromQuery();
  syncQueryFromFilters();
  syncFilterSummary();
  refresh();
  setInterval(() => { if (ui.byId("auto").checked) refresh(); }, 10000);
    """.strip()
    return render_admin_shell(
        title="Адмін-панель Passengers — WireGuard",
        header_title="WireGuard (піри)",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        extra_css=extra_css,
        max_width=1300,
        current_nav="wg",
    ).strip()
