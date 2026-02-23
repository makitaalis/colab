from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_commission_page() -> str:
    chips_html = """
        <span class="chip">підключення нового транспорту</span>
    """
    toolbar_html = """
        <div class="toolbarMain">
          <input id="centralId" type="text" placeholder="central_id / system_id (sys-0002)" class="uMinW240" />
          <button id="copyCmds" class="primary" disabled>Копіювати команди</button>
          <button id="copyLink" title="Скопіювати поточне посилання (з урахуванням параметрів)">Скопіювати сторінку</button>
          <details class="toolbarDetails" data-advanced-details="1">
            <summary>Параметри підключення та інструменти</summary>
            <div class="toolbarDetailsGrid uJcStart">
              <input id="centralIp" type="text" placeholder="IP central (192.168.10.1)" class="uMinW190" />
              <input id="door1Ip" type="text" placeholder="door-1 IP (192.168.10.11)" class="uMinW190" />
              <input id="door2Ip" type="text" placeholder="door-2 IP (192.168.10.12)" class="uMinW190" />
              <input id="vehicleId" type="text" placeholder="vehicle_id (bus-017)" class="uMinW150" />
              <input id="plate" type="text" placeholder="номер (AA1234BB)" class="uMinW150" />
              <label class="muted uInlineRow"><input id="openNewTab" type="checkbox" checked /> нова вкладка</label>
              <button id="useBackendVehicle" class="smallbtn" disabled title="Взяти vehicle_id з backend (якщо є)">Підставити vehicle_id</button>
              <button id="useBackendVehicleClearPlate" class="smallbtn" disabled title="Скинути номер (якщо зараз не потрібен)">Скинути номер</button>
              <button id="copyLinks" class="smallbtn" disabled>Копіювати посилання</button>
              <button id="copyEvidence" class="smallbtn" disabled title="Короткий звіт: WG + backend + інциденти + посилання">Копіювати звіт</button>
            </div>
          </details>
        </div>
        <div class="toolbarMeta">
          <span class="metaChip sort" id="filterSummary">контекст: —</span>
          <span class="status" id="status"></span>
        </div>
    """
    body_html = """
    <div class="card">
      <div class="sectionHead">
        <div>
          <div class="sectionTitle">Комісія: статус і наступні дії</div>
          <div class="muted">Джерела: <code>/api/admin/fleet/centrals</code> + <code>/api/admin/fleet/incidents</code> + <code>/api/admin/wg/peers</code></div>
        </div>
        <div class="sectionTools">
          <a class="quickLink" id="openAdminOverview" href="#">/admin?central_id=…</a>
          <a class="quickLink" id="openCentralPage" href="#">Вузол</a>
          <a class="quickLink" id="openWgPage" href="#">WG</a>
          <a class="quickLink" id="openIncidents" href="#">Інциденти</a>
          <a class="quickLink" id="openPolicy" href="#">Персональні override-и</a>
          <a class="quickLink" id="openNotify" href="#">Центр сповіщень</a>
          <label class="muted uInlineRow"><input id="autoBackend" type="checkbox" checked /> авто</label>
          <button id="refreshBackend" class="smallbtn">Оновити</button>
          <button id="refreshWg" class="smallbtn">WG</button>
        </div>
      </div>
      <div class="commissionGrid">
        <div id="backendStatus" class="wgBox">
          <div id="commissionVerdict" class="wgSummary uMb6">—</div>
          <div id="backendStatusLine" class="wgSummary">введіть <code>central_id</code> і натисніть “Оновити”</div>
          <div id="backendIncidentsLine" class="muted uMt6">—</div>
          <div id="backendNextAction" class="muted uMt6">—</div>
        </div>
        <div id="wgBox" class="wgBox">
          <div id="wgStatus" class="wgSummary">завантаження...</div>
          <div class="muted uMt6">Порада: handshake має бути “свіжий” (&lt; 2 хв). Якщо “стейл” — флот не з’явиться.</div>
        </div>
      </div>
      <div class="muted commissionChecklistLine">Чекліст: Реєстр → Bundle → WireGuard → Env на Central → Rollout-check → Перевірка в адмінці.</div>
    </div>

    <div class="card">
      <div class="sectionHead">
        <div>
          <div class="sectionTitle">Команди (копіпаст)</div>
          <div class="muted">Запускати на вашому ПК в репозиторії <code>OrangePi_passangers</code></div>
        </div>
        <div class="sectionTools">
          <button id="copyCmds2" class="smallbtn" disabled>Копіювати</button>
        </div>
      </div>
      <pre class="tableWrap commissionCmdWrap"><code id="cmdBlock">Введіть central_id, щоб побачити команди.</code></pre>
    </div>

    <details id="commissionSecondaryDetails" class="domainSplitDetails" data-advanced-details="1">
      <summary>Чекліст та локальні інструменти (runs, profiles)</summary>
      <div class="domainSplitHint">Ці блоки працюють локально у браузері (localStorage) і не запускають команди на сервері.</div>

      <div class="wgBox commissionSplitBlock">
        <div class="sectionHead">
          <div>
            <div class="sectionTitle">Чекліст підключення (E2E commissioning)</div>
            <div class="muted">Мета: швидко підключити новий транспорт (WireGuard + env + rollout-check + перевірка в адмінці)</div>
          </div>
        </div>
        <ol class="hint commissionChecklist">
          <li><b>Реєстр</b>: внесіть систему в <code>fleet/registry.csv</code> (правило масштабу: <code>system_id = central_id = sys-XXXX</code>).</li>
          <li><b>Bundle</b>: згенеруйте пакет команд/конфігів для <code>sys-XXXX</code> (<code>fleet/out/sys-XXXX/</code>).</li>
          <li><b>WireGuard</b>: додайте peer на сервер і добийтеся handshake (&lt; 2 хв).</li>
          <li><b>Env на Central</b>: застосуйте шаблон env (включно з backend API key) і перезапустіть сервіси.</li>
          <li><b>Rollout-check</b>: прогоніть <code>fleet_commission.py</code> (опційно зі <code>--smoke</code>).</li>
          <li><b>Адмінка</b>: переконайтеся, що central з’явився у флоті, алерти/черги читаються коректно.</li>
        </ol>
      </div>

      <div class="wgBox commissionSplitBlock">
        <div class="sectionHead">
          <div>
            <div class="sectionTitle">Перевірки (локально)</div>
            <div class="muted">Кнопки копіюють команду або фіксують результат у вашому браузері (localStorage).</div>
          </div>
          <div class="sectionTools">
            <button id="copyCheckCommission" class="smallbtn" disabled>Копіювати fleet_commission</button>
            <button id="copyCheckSmoke" class="smallbtn" disabled>Копіювати e2e smoke</button>
            <button id="markPass" class="smallbtn" disabled>Позначити PASS</button>
            <button id="markFail" class="smallbtn" disabled>Позначити FAIL</button>
            <button id="exportRuns" class="smallbtn">Експорт</button>
            <button id="importRuns" class="smallbtn">Імпорт</button>
            <button id="clearRuns" class="smallbtn">Очистити</button>
          </div>
        </div>
        <div id="runSummary" class="wgSummary">—</div>
        <div class="muted uMt6">Останні 12 записів:</div>
        <div class="tableWrap uMt8">
          <table id="runTbl" style="min-width: 980px;">
            <thead>
              <tr>
                <th>Час</th>
                <th>Тип</th>
                <th>Результат</th>
                <th>Нотатка</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>

      <div class="wgBox commissionSplitBlock">
        <div class="sectionHead">
          <div>
            <div class="sectionTitle">Профілі (локально)</div>
            <div class="muted">Прив’язка <code>central_id</code> → <code>vehicle_id/plate/IP</code> для швидкого повторного запуску commissioning.</div>
          </div>
          <div class="sectionTools">
            <select id="profileSelect" class="smallSelect" title="Виберіть профіль"></select>
            <button id="saveProfile" class="smallbtn" disabled>Зберегти</button>
            <button id="loadProfile" class="smallbtn" disabled>Завантажити</button>
            <button id="deleteProfile" class="smallbtn" disabled>Видалити</button>
            <button id="exportProfiles" class="smallbtn">Експорт</button>
            <button id="importProfiles" class="smallbtn">Імпорт</button>
          </div>
        </div>
        <div id="profileSummary" class="wgSummary">—</div>
      </div>
    </details>
    """
    extra_css = """
    .sectionTitle { font-weight: 700; }
    .disabledLink { pointer-events: none; opacity: .55; }
    #runTbl th, #runTbl td { vertical-align: top; }
    .smallSelect { min-height: 30px; border-radius: 10px; border: 1px solid rgba(255,255,255,.14); background: rgba(255,255,255,.03); color: #dbe7fd; font-size: 12px; padding: 4px 8px; }
    .commissionGrid { display: grid; grid-template-columns: repeat(auto-fit, minmax(340px, 1fr)); gap: 10px; margin-top: 10px; }
    .commissionChecklistLine { margin-top: 10px; line-height: 1.45; }
    .commissionCmdWrap { max-height: 46vh; padding: 10px; margin-top: 8px; }
    .commissionSplitBlock { margin-top: 10px; }
    .commissionChecklist { line-height: 1.7; margin: 8px 0 0; }
    """.strip()
    script = """
  const ui = window.AdminUiKit;
  const SYS_ID_RE = /^sys-[0-9]{4}$/i;
  const REFRESH_DELAY_MS = 220;
  const WG_FRESH_SEC = 120;
  const WG_WARN_SEC = 600;
  const HEARTBEAT_FRESH_SEC = 120;
  const HEARTBEAT_WARN_SEC = 600;
  let lastWgPeer = null;
  let lastFleetRow = null;
  let lastIncTotals = null;
  let lastCommissionLevel = null;
  let lastCommissionLabel = null;
  let lastNextHint = null;
  const RUNS_STORAGE_KEY = "passengers_admin_commission_runs_v1";
  const PROFILES_STORAGE_KEY = "passengers_admin_commission_profiles_v1";
  const SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_commission_secondary_details_v1";

  function loadSecondaryDetailsOpen() {
    try {
      const raw = String(localStorage.getItem(SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (!raw) return false;
      return raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {
      return false;
    }
  }
  function storeSecondaryDetailsOpen(open) {
    const value = open ? "1" : "0";
    try { localStorage.setItem(SECONDARY_DETAILS_STORAGE_KEY, value); } catch (_error) {}
    return value === "1";
  }
  function initSecondaryDetails() {
    const node = document.getElementById("commissionSecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    node.open = loadSecondaryDetailsOpen();
    node.addEventListener("toggle", () => {
      storeSecondaryDetailsOpen(node.open);
    });
  }

  function setStatus(text) { ui.setStatus("status", text); }
  function isBlank(value) { return !String(value || "").trim(); }
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

  function readCtx() {
    return {
      central_id: String(ui.byId("centralId").value || "").trim(),
      central_ip: String(ui.byId("centralIp").value || "").trim() || "192.168.10.1",
      door1_ip: String(ui.byId("door1Ip").value || "").trim() || "192.168.10.11",
      door2_ip: String(ui.byId("door2Ip").value || "").trim() || "192.168.10.12",
      vehicle_id: String(ui.byId("vehicleId").value || "").trim(),
      plate: String(ui.byId("plate").value || "").trim(),
    };
  }

  function applyCtxFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const cid = params.get("central_id") || params.get("system_id") || "";
    const cip = params.get("central_ip") || "";
    const d1 = params.get("door1_ip") || "";
    const d2 = params.get("door2_ip") || "";
    const vid = params.get("vehicle_id") || "";
    const plate = params.get("plate") || "";
    if (cid) ui.byId("centralId").value = cid;
    if (cip) ui.byId("centralIp").value = cip;
    if (d1) ui.byId("door1Ip").value = d1;
    if (d2) ui.byId("door2Ip").value = d2;
    if (vid) ui.byId("vehicleId").value = vid;
    if (plate) ui.byId("plate").value = plate;
  }

  function syncQueryFromCtx() {
    const ctx = readCtx();
    const params = new URLSearchParams();
    if (ctx.central_id) params.set("central_id", ctx.central_id);
    if (ctx.central_ip && ctx.central_ip !== "192.168.10.1") params.set("central_ip", ctx.central_ip);
    if (ctx.door1_ip && ctx.door1_ip !== "192.168.10.11") params.set("door1_ip", ctx.door1_ip);
    if (ctx.door2_ip && ctx.door2_ip !== "192.168.10.12") params.set("door2_ip", ctx.door2_ip);
    if (ctx.vehicle_id) params.set("vehicle_id", ctx.vehicle_id);
    if (ctx.plate) params.set("plate", ctx.plate);
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }

  function syncSummary() {
    const ctx = readCtx();
    const parts = [];
    if (ctx.central_id) parts.push(`вузол=${ctx.central_id}`);
    if (ctx.vehicle_id) parts.push(`bus=${ctx.vehicle_id}`);
    if (ctx.plate) parts.push(`plate=${ctx.plate}`);
    if (ctx.central_ip) parts.push(`central_ip=${ctx.central_ip}`);
    const node = ui.byId("filterSummary");
    node.textContent = parts.length ? `контекст: ${parts.join(" · ")}` : "контекст: —";
  }

  function setLinksEnabled(enabled) {
    ui.byId("copyCmds").disabled = !enabled;
    ui.byId("copyCmds2").disabled = !enabled;
    ui.byId("copyLinks").disabled = !enabled;
    ui.byId("copyEvidence").disabled = !enabled;
    ui.byId("copyCheckCommission").disabled = !enabled;
    ui.byId("copyCheckSmoke").disabled = !enabled;
    ui.byId("markPass").disabled = !enabled;
    ui.byId("markFail").disabled = !enabled;
    ui.byId("useBackendVehicle").disabled = !enabled;
    ui.byId("useBackendVehicleClearPlate").disabled = !enabled;
    ui.byId("saveProfile").disabled = !enabled;
    const ids = ["openAdminOverview", "openCentralPage", "openWgPage", "openIncidents", "openPolicy", "openNotify"];
    for (const id of ids) {
      const node = ui.byId(id);
      if (!node) continue;
      node.classList.toggle("disabledLink", !enabled);
    }
  }

  function renderCommands() {
    const ctx = readCtx();
    if (isBlank(ctx.central_id)) {
      ui.byId("cmdBlock").textContent = "Введіть central_id, щоб побачити команди.";
      setLinksEnabled(false);
      return;
    }
    const cid = ctx.central_id;
    const formatOk = SYS_ID_RE.test(cid);
    const lines = [
      `# Commissioning: ${cid}${formatOk ? "" : "  (WARN: формат не sys-XXXX)"}`,
      "",
      "# 0) Per-system API keys (рекомендовано для масштабу 100-200)",
      `python3 scripts/fleet_api_keys.py ensure --system-id ${cid}`,
      "# (оновлює PASSENGERS_API_KEYS + ADMIN_API_KEYS на VPS, перезапускає api)",
      "python3 scripts/fleet_api_keys.py sync-server",
      "",
      "# 1) Bundle (генерує fleet/out/<sys>/commands.md + templates)",
      `python3 scripts/fleet_registry.py bundle --system-id ${cid}`,
      "",
      "# 2) WireGuard peer на сервері (ідемпотентно)",
      `python3 scripts/fleet_apply_wg_peer.py --system-id ${cid} --ensure-central-key --fetch-central-pubkey`,
      "",
      "# 3) Env на Central (підтягує backend key з VPS, застосовує і перезапускає сервіси)",
      `python3 scripts/fleet_apply_central_env.py --system-id ${cid} --central-ip ${ctx.central_ip}`,
      "",
      "# 4) Rollout-check / commissioning report",
      `python3 scripts/fleet_commission.py --system-id ${cid} --smoke`,
      "",
      "# 5) Gate адмінки (UI/API) на VPS",
      `./scripts/admin_panel_smoke_gate.sh --admin-pass-file \"pass admin panel\"`,
    ];
    ui.byId("cmdBlock").textContent = lines.join("\\n");
    setLinksEnabled(true);
  }

  function updateQuickLinks() {
    const ctx = readCtx();
    if (isBlank(ctx.central_id)) return;
    const cidEnc = encodeURIComponent(ctx.central_id);
    const openNewTab = Boolean(ui.byId("openNewTab") && ui.byId("openNewTab").checked);
    const target = openNewTab ? "_blank" : "";
    const rel = openNewTab ? "noopener" : "";
    ui.byId("openAdminOverview").href = `/admin?central_id=${cidEnc}`;
    ui.byId("openCentralPage").href = `/admin/fleet/central/${cidEnc}`;
    ui.byId("openWgPage").href = `/admin/wg?q=${cidEnc}`;
    ui.byId("openIncidents").href = `/admin/fleet/incidents?central_id=${cidEnc}&include_resolved=0`;
    ui.byId("openPolicy").href = `/admin/fleet/policy?central_id=${cidEnc}`;
    ui.byId("openNotify").href = `/admin/fleet/notify-center?central_id=${cidEnc}`;
    const ids = ["openAdminOverview", "openCentralPage", "openWgPage", "openIncidents", "openPolicy", "openNotify"];
    for (const id of ids) {
      const node = ui.byId(id);
      if (!node) continue;
      if (openNewTab) {
        node.setAttribute("target", target);
        node.setAttribute("rel", rel);
      } else {
        node.removeAttribute("target");
        node.removeAttribute("rel");
      }
    }
  }

  function copyCommands() {
    const text = String(ui.byId("cmdBlock").textContent || "").trim();
    if (!text) return;
    ui.copyTextWithFallback(text, "Скопіюйте команди:", "Команди скопійовано", "Команди у prompt");
  }

  function copyLinks() {
    const ctx = readCtx();
    if (isBlank(ctx.central_id)) return;
    const cidEnc = encodeURIComponent(ctx.central_id);
    const origin = window.location.origin;
    const lines = [
      `central_id=${ctx.central_id}`,
      `${origin}/admin?central_id=${cidEnc}`,
      `${origin}/admin/commission?central_id=${cidEnc}`,
      `${origin}/admin/wg?q=${cidEnc}`,
      `${origin}/admin/fleet/central/${cidEnc}`,
      `${origin}/admin/fleet/incidents?central_id=${cidEnc}&include_resolved=0`,
      `${origin}/admin/fleet/policy?central_id=${cidEnc}`,
      `${origin}/admin/fleet/notify-center?central_id=${cidEnc}`,
    ];
    ui.copyTextWithFallback(lines.join("\\n"), "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt");
  }

  async function refreshWgBox() {
    const node = ui.byId("wgStatus");
    node.textContent = "завантаження...";
    try {
      const data = await ui.apiGet("/api/admin/wg/peers");
      const peers = Array.isArray(data.peers) ? data.peers : [];
      const ctx = readCtx();
      const cid = String(ctx.central_id || "").trim().toLowerCase();
      const match = cid ? peers.find((p) => String(p.name || "").trim().toLowerCase() === cid) : null;
      lastWgPeer = match ? match : null;
      if (!match) {
        node.innerHTML = `<span class="badge warn">WG</span> peer не знайдено (введіть <code>central_id</code>, або перевірте назву peer у <a href="/admin/wg">/admin/wg</a>)`;
        return;
      }
      const age = match.latest_handshake_age_sec;
      const cls = (age !== null && age !== undefined && age >= 0 && age <= 120) ? "good" : ((age !== null && age !== undefined && age >= 0 && age <= 600) ? "warn" : "bad");
      const tail = match.latest_handshake_ts ? ` · ts=<code>${ui.esc(String(match.latest_handshake_ts))}</code>` : "";
      node.innerHTML = `<span class="badge ${cls}">WG</span> <code>${ui.esc(match.name || "")}</code> · handshake=${ui.esc(fmtAge(age))}${tail} · endpoint=<code>${ui.esc(String(match.endpoint || "—"))}</code>`;
    } catch (error) {
      lastWgPeer = null;
      node.innerHTML = `<span class="badge bad">WG</span> помилка: <code>${ui.esc(String(error || ""))}</code>`;
    }
  }

  function onCtxChanged() {
    syncQueryFromCtx();
    syncSummary();
    renderCommands();
    updateQuickLinks();
    refreshBackendStatus();
    syncProfileControls();
    renderProfileSummary();
  }

  async function refreshBackendStatus() {
    const statusLine = ui.byId("backendStatusLine");
    const incidentsLine = ui.byId("backendIncidentsLine");
    const verdictLine = ui.byId("commissionVerdict");
    const nextActionLine = ui.byId("backendNextAction");
    const ctx = readCtx();
    const cid = String(ctx.central_id || "").trim();
    if (!cid) {
      verdictLine.innerHTML = '<span class="badge warn">COMMISSION</span> введіть <code>central_id</code>';
      statusLine.innerHTML = '<span class="badge warn">BACKEND</span> введіть <code>central_id</code>';
      incidentsLine.textContent = "—";
      nextActionLine.textContent = "—";
      lastFleetRow = null;
      lastIncTotals = null;
      lastCommissionLevel = "warn";
      lastCommissionLabel = "введіть central_id";
      lastNextHint = "";
      return;
    }
    statusLine.textContent = "завантаження...";
    incidentsLine.textContent = "—";
    verdictLine.textContent = "завантаження...";
    nextActionLine.textContent = "—";
    try {
      const cidEnc = encodeURIComponent(cid);
      const [centralsData, incidentsData] = await Promise.all([
        ui.apiGet("/api/admin/fleet/centrals"),
        ui.apiGet(`/api/admin/fleet/incidents?central_id=${cidEnc}&include_resolved=0&limit=200`),
      ]);
      const centrals = Array.isArray(centralsData.centrals) ? centralsData.centrals : [];
      const row = centrals.find((item) => String(item.central_id || "").trim().toLowerCase() === cid.toLowerCase()) || null;
      const totals = incidentsData.totals || {};
      const open = Number(totals.open ?? 0);
      const acked = Number(totals.acked ?? 0);
      const silenced = Number(totals.silenced ?? 0);
      const sla = Number(totals.sla_breached ?? 0);
      lastFleetRow = row ? row : null;
      lastIncTotals = totals ? totals : null;

      let commissionLevel = "warn";
      const nextActions = [];
      if (!row) {
        statusLine.innerHTML = `<span class="badge warn">BACKEND</span> <code>${ui.esc(cid)}</code> ще не з’явився у флоті (немає heartbeat).`;
        commissionLevel = "warn";
        nextActions.push("Перевірте WG peer (handshake) у /admin/wg.");
        nextActions.push("Перевірте Central env/services (чи запущені сервіси, чи заданий backend token).");
      } else {
        // Autofill vehicle_id from backend (only when UI field is empty).
        const backendVehicle = String(row.vehicle_id || "").trim();
        const vehicleInput = ui.byId("vehicleId");
        if (backendVehicle && vehicleInput && !String(vehicleInput.value || "").trim()) {
          vehicleInput.value = backendVehicle;
          // Keep shareable URL and header summary aligned.
          syncQueryFromCtx();
          syncSummary();
        }

        const health = row.health || {};
        const queue = row.queue || {};
        const sev = String(health.severity || "warn").toLowerCase();
        const sevCls = (sev === "good" || sev === "warn" || sev === "bad") ? sev : "warn";
        const heartbeatAge = row.age_sec;
        const pending = queue.pending_batches ?? queue.pending_batches_total ?? 0;
        const pendingOldest = queue.pending_oldest_age_sec;
        const wgAge = queue.wg_latest_handshake_age_sec;
        const vehicle = row.vehicle_id || "—";
        const alertsTotal = health.alerts_total ?? 0;
        const ts = row.ts_received || "—";
        statusLine.innerHTML = [
          `<span class="badge ${sevCls}">FLEET</span> <code>${ui.esc(cid)}</code> · vehicle=<code>${ui.esc(String(vehicle))}</code>`,
          `· heartbeat=${ui.esc(fmtAge(heartbeatAge))} · ts=<code>${ui.esc(String(ts))}</code>`,
          `· черга=<code>${ui.esc(String(pending))}</code> (oldest=${ui.esc(fmtAge(pendingOldest))})`,
          `· wg=${ui.esc(fmtAge(wgAge))} · алерти=<code>${ui.esc(String(alertsTotal))}</code>`,
        ].join(" ");

        const hb = (heartbeatAge === null || heartbeatAge === undefined) ? null : Number(heartbeatAge);
        const wg = (wgAge === null || wgAge === undefined) ? null : Number(wgAge);
        const hbState = (hb === null || !Number.isFinite(hb) || hb < 0) ? "bad" : (hb <= HEARTBEAT_FRESH_SEC ? "good" : (hb <= HEARTBEAT_WARN_SEC ? "warn" : "bad"));
        const wgState = (wg === null || !Number.isFinite(wg) || wg < 0) ? "bad" : (wg <= WG_FRESH_SEC ? "good" : (wg <= WG_WARN_SEC ? "warn" : "bad"));

        if (hbState === "bad" || wgState === "bad") commissionLevel = "bad";
        else if (hbState === "warn" || wgState === "warn") commissionLevel = "warn";
        else commissionLevel = "good";

        const uiVehicle = String(ui.byId("vehicleId")?.value || "").trim();
        if (backendVehicle && uiVehicle && backendVehicle !== uiVehicle) {
          if (commissionLevel === "good") commissionLevel = "warn";
          nextActions.unshift(`Увага: vehicle_id відрізняється (backend=${backendVehicle} vs UI=${uiVehicle}).`);
        }
        if (hbState !== "good") nextActions.push(`Heartbeat не свіжий (${fmtAge(hb)}). Перевірте, чи central відправляє heartbeat у backend.`);
        if (wgState !== "good") nextActions.push(`WG handshake не свіжий (${fmtAge(wg)}). Перевірте peer/маршрут/keepalive.`);
        if (Number(pending || 0) > 0 && Number(pendingOldest || 0) > 600) nextActions.push("Черга накопичується: перевірте відправку stop batches на сервер.");
      }

      incidentsLine.innerHTML = `<span class="badge ${open > 0 ? "warn" : "good"}">INCIDENTS</span> відкриті=<code>${ui.esc(String(open))}</code> · підтверджені=<code>${ui.esc(String(acked))}</code> · заглушені=<code>${ui.esc(String(silenced))}</code> · SLA=<code>${ui.esc(String(sla))}</code>`;

      if (sla > 0) {
        commissionLevel = "bad";
        nextActions.unshift("Є порушення SLA: відкрийте інциденти і зробіть triage першими.");
      } else if (open > 0 && commissionLevel === "good") {
        commissionLevel = "warn";
      }

      const commissionLabel = commissionLevel === "good" ? "ГОТОВО" : (commissionLevel === "warn" ? "ПОТРЕБУЄ УВАГИ" : "КРИТИЧНО");
      verdictLine.innerHTML = `<span class="badge ${commissionLevel}">COMMISSION</span> ${ui.esc(commissionLabel)} · <code>${ui.esc(cid)}</code>`;
      lastCommissionLevel = commissionLevel;
      lastCommissionLabel = commissionLabel;
      if (nextActions.length > 0) {
        const nextText = nextActions.slice(0, 3).join(" · ");
        lastNextHint = nextText;
        nextActionLine.innerHTML = `<span class="badge ${commissionLevel === "bad" ? "bad" : "warn"}">NEXT</span> ${nextActions.slice(0, 3).map((line) => ui.esc(String(line))).join(" · ")}`;
      } else {
        lastNextHint = "Нічого критичного. Можна переходити до наступних модулів або до тестових стопів.";
        nextActionLine.innerHTML = '<span class="badge good">NEXT</span> Нічого критичного. Можна переходити до наступних модулів (камера/GPS/RTC) або до тестових стопів.';
      }
    } catch (error) {
      verdictLine.innerHTML = `<span class="badge bad">COMMISSION</span> помилка`;
      statusLine.innerHTML = `<span class="badge bad">BACKEND</span> помилка: <code>${ui.esc(String(error || ""))}</code>`;
      incidentsLine.textContent = "—";
      nextActionLine.textContent = "—";
      lastFleetRow = null;
      lastIncTotals = null;
      lastCommissionLevel = "bad";
      lastCommissionLabel = "помилка";
      lastNextHint = "";
    }
  }

  function applyBackendVehicle() {
    if (!lastFleetRow) { window.alert("backend ще не повернув vehicle_id (немає heartbeat)."); return; }
    const backendVehicle = String(lastFleetRow.vehicle_id || "").trim();
    if (!backendVehicle) { window.alert("У backend поле vehicle_id порожнє."); return; }
    ui.byId("vehicleId").value = backendVehicle;
    syncQueryFromCtx();
    syncSummary();
    addRun({ ts: new Date().toISOString(), type: "identity", result: "info", note: `vehicle_id<-backend:${backendVehicle}` });
    refreshBackendStatus();
  }

  function clearPlate() {
    ui.byId("plate").value = "";
    syncQueryFromCtx();
    syncSummary();
    addRun({ ts: new Date().toISOString(), type: "identity", result: "info", note: "plate cleared" });
  }

  function copyEvidence() {
    const ctx = readCtx();
    const cid = String(ctx.central_id || "").trim();
    if (!cid) return;
    const origin = window.location.origin;
    const now = new Date().toISOString();
    const parts = [];
    parts.push(`# Evidence bundle`);
    parts.push(`ts=${now}`);
    parts.push(`central_id=${cid}`);
    if (ctx.vehicle_id) parts.push(`vehicle_id=${ctx.vehicle_id}`);
    if (ctx.plate) parts.push(`plate=${ctx.plate}`);
    parts.push(`central_ip=${ctx.central_ip}`);
    parts.push(`door2_ip=${ctx.door1_ip}`);
    parts.push(`door3_ip=${ctx.door2_ip}`);
    parts.push("");
    parts.push(`COMMISSION=${lastCommissionLabel || "—"} (${lastCommissionLevel || "—"})`);
    if (lastNextHint) parts.push(`NEXT=${lastNextHint}`);
    parts.push("");

    if (lastWgPeer) {
      const age = lastWgPeer.latest_handshake_age_sec;
      parts.push(`[WireGuard]`);
      parts.push(`peer=${lastWgPeer.name || "—"}`);
      parts.push(`handshake_age=${fmtAge(age)} (${age ?? "—"} sec)`);
      parts.push(`handshake_ts=${lastWgPeer.latest_handshake_ts || "—"}`);
      parts.push(`endpoint=${lastWgPeer.endpoint || "—"}`);
      parts.push(`allowed_ips=${Array.isArray(lastWgPeer.allowed_ips) ? lastWgPeer.allowed_ips.join(",") : "—"}`);
      parts.push("");
    } else {
      parts.push(`[WireGuard] peer=— (не знайдено / помилка API)`);
      parts.push("");
    }

    if (lastFleetRow) {
      const health = lastFleetRow.health || {};
      const queue = lastFleetRow.queue || {};
      parts.push(`[Backend fleet]`);
      parts.push(`vehicle_id=${lastFleetRow.vehicle_id || "—"}`);
      parts.push(`severity=${health.severity || "—"}`);
      parts.push(`heartbeat_age=${fmtAge(lastFleetRow.age_sec)} (${lastFleetRow.age_sec ?? "—"} sec)`);
      parts.push(`ts_received=${lastFleetRow.ts_received || "—"}`);
      parts.push(`pending_batches=${queue.pending_batches ?? queue.pending_batches_total ?? 0}`);
      parts.push(`pending_oldest_age=${fmtAge(queue.pending_oldest_age_sec)} (${queue.pending_oldest_age_sec ?? "—"} sec)`);
      parts.push(`wg_handshake_age=${fmtAge(queue.wg_latest_handshake_age_sec)} (${queue.wg_latest_handshake_age_sec ?? "—"} sec)`);
      parts.push(`alerts_total=${health.alerts_total ?? 0}`);
      parts.push("");
    } else {
      parts.push(`[Backend fleet] central відсутній (ще немає heartbeat)`);
      parts.push("");
    }

    if (lastIncTotals) {
      parts.push(`[Incidents totals]`);
      parts.push(`відкриті=${lastIncTotals.open ?? 0}`);
      parts.push(`підтверджені=${lastIncTotals.acked ?? 0}`);
      parts.push(`заглушені=${lastIncTotals.silenced ?? 0}`);
      parts.push(`sla_breached=${lastIncTotals.sla_breached ?? 0}`);
      parts.push("");
    }

    const cidEnc = encodeURIComponent(cid);
    parts.push(`[Links]`);
    parts.push(`${origin}/admin?central_id=${cidEnc}`);
    parts.push(`${origin}/admin/commission?central_id=${cidEnc}`);
    parts.push(`${origin}/admin/wg?q=${cidEnc}`);
    parts.push(`${origin}/admin/fleet/central/${cidEnc}`);
    parts.push(`${origin}/admin/fleet/incidents?central_id=${cidEnc}&include_resolved=0`);
    parts.push(`${origin}/admin/fleet/policy?central_id=${cidEnc}`);
    parts.push(`${origin}/admin/fleet/notify-center?central_id=${cidEnc}`);
    parts.push("");

    ui.copyTextWithFallback(parts.join("\\n"), "Скопіюйте звіт:", "Звіт скопійовано", "Звіт у prompt");
  }

  function loadRuns() {
    try {
      const raw = localStorage.getItem(RUNS_STORAGE_KEY) || "[]";
      const parsed = JSON.parse(raw);
      return Array.isArray(parsed) ? parsed : [];
    } catch (_error) {
      return [];
    }
  }
  function saveRuns(items) {
    try { localStorage.setItem(RUNS_STORAGE_KEY, JSON.stringify(items)); } catch (_error) { /* ignore */ }
  }
  function addRun(entry) {
    const items = loadRuns();
    items.unshift(entry);
    saveRuns(items.slice(0, 64));
    renderRuns();
  }
  function renderRuns() {
    const items = loadRuns();
    const tbody = document.querySelector("#runTbl tbody");
    tbody.innerHTML = "";
    const top = items.slice(0, 12);
    if (top.length === 0) {
      tbody.innerHTML = '<tr><td colspan="4" class="empty">Немає записів</td></tr>';
      ui.byId("runSummary").innerHTML = '<span class="badge">ПРОГОНИ</span> —';
      return;
    }
    const last = top[0];
    ui.byId("runSummary").innerHTML = `<span class="badge">ПРОГОНИ</span> останній: <code>${ui.esc(String(last.ts || "—"))}</code> · <code>${ui.esc(String(last.type || "—"))}</code> · <span class="badge ${ui.esc(String(last.result || "").toLowerCase() === "pass" ? "good" : "warn")}">${ui.esc(String(last.result || "—").toUpperCase())}</span>`;
    for (const item of top) {
      const tr = document.createElement("tr");
      const res = String(item.result || "—");
      const badgeCls = res.toLowerCase() === "pass" ? "good" : (res.toLowerCase() === "fail" ? "bad" : "warn");
      tr.innerHTML = `
        <td><code>${ui.esc(String(item.ts || "—"))}</code></td>
        <td><code>${ui.esc(String(item.type || "—"))}</code></td>
        <td><span class="badge ${badgeCls}">${ui.esc(res.toUpperCase())}</span></td>
        <td class="muted">${ui.esc(String(item.note || ""))}</td>
      `;
      tbody.appendChild(tr);
    }
  }

  function buildSmokeCmd(ctx) {
    const args = [
      "./scripts/mvp_e2e_smoke.sh",
      `--central-ip ${ctx.central_ip}`,
      "--server-host 207.180.213.225",
      `--door1-ip ${ctx.door1_ip}`,
      `--door2-ip ${ctx.door2_ip}`,
    ];
    return args.join(" ");
  }

  function buildCommissionCmd(ctx) {
    return `python3 scripts/fleet_commission.py --system-id ${ctx.central_id} --smoke`;
  }

  function copyCheckCommission() {
    const ctx = readCtx();
    if (!ctx.central_id) return;
    const cmd = buildCommissionCmd(ctx);
    addRun({ ts: new Date().toISOString(), type: "copy:fleet_commission", result: "info", note: cmd });
    ui.copyTextWithFallback(cmd, "Скопіюйте команду:", "Команду скопійовано", "Команда у prompt");
  }

  function copyCheckSmoke() {
    const ctx = readCtx();
    if (!ctx.central_id) return;
    const cmd = buildSmokeCmd(ctx);
    addRun({ ts: new Date().toISOString(), type: "copy:e2e_smoke", result: "info", note: cmd });
    ui.copyTextWithFallback(cmd, "Скопіюйте команду:", "Команду скопійовано", "Команда у prompt");
  }

  function markResult(result) {
    const ctx = readCtx();
    if (!ctx.central_id) return;
    const noteParts = [
      `central=${ctx.central_id}`,
      ctx.vehicle_id ? `bus=${ctx.vehicle_id}` : "",
      ctx.plate ? `plate=${ctx.plate}` : "",
      `commission=${lastCommissionLabel || "—"}(${lastCommissionLevel || "—"})`,
      lastNextHint ? `next=${lastNextHint}` : "",
    ].filter(Boolean);
    addRun({ ts: new Date().toISOString(), type: "mark", result, note: noteParts.join(" · ") });
  }

  function clearRuns() {
    saveRuns([]);
    renderRuns();
  }

  function exportRuns() {
    const items = loadRuns();
    const payload = {
      schema: "passengers-admin-commission-runs/v1",
      exported_at: new Date().toISOString(),
      total: items.length,
      runs: items,
    };
    const text = JSON.stringify(payload, null, 2);
    addRun({ ts: new Date().toISOString(), type: "export", result: "info", note: `runs=${items.length}` });
    ui.copyTextWithFallback(text, "Скопіюйте експорт JSON:", "Експорт скопійовано", "Експорт у prompt");
  }

  function importRuns() {
    const pasted = window.prompt("Вставте JSON з експорту runs:", "");
    if (!pasted) return;
    let data = null;
    try {
      data = JSON.parse(String(pasted));
    } catch (_error) {
      addRun({ ts: new Date().toISOString(), type: "import", result: "fail", note: "bad_json" });
      window.alert("Помилка: некоректний JSON");
      return;
    }
    const runs = (data && typeof data === "object" && Array.isArray(data.runs)) ? data.runs : null;
    if (!runs) {
      addRun({ ts: new Date().toISOString(), type: "import", result: "fail", note: "missing_runs" });
      window.alert("Помилка: JSON не містить поля runs[]");
      return;
    }
    // Merge by ts+type+result+note fingerprint (best-effort).
    const current = loadRuns();
    const seen = new Set(current.map((r) => `${r.ts}|${r.type}|${r.result}|${r.note}`));
    let added = 0;
    for (const r of runs) {
      if (!r || typeof r !== "object") continue;
      const fp = `${r.ts}|${r.type}|${r.result}|${r.note}`;
      if (seen.has(fp)) continue;
      current.push(r);
      seen.add(fp);
      added += 1;
    }
    // Sort desc by ts when possible.
    current.sort((a, b) => String(b.ts || "").localeCompare(String(a.ts || "")));
    saveRuns(current.slice(0, 64));
    addRun({ ts: new Date().toISOString(), type: "import", result: "pass", note: `added=${added} total=${Math.min(64, current.length)}` });
    renderRuns();
  }

  function loadProfiles() {
    try {
      const raw = localStorage.getItem(PROFILES_STORAGE_KEY) || "{}";
      const parsed = JSON.parse(raw);
      return parsed && typeof parsed === "object" ? parsed : {};
    } catch (_error) {
      return {};
    }
  }

  function saveProfiles(obj) {
    try { localStorage.setItem(PROFILES_STORAGE_KEY, JSON.stringify(obj)); } catch (_error) { /* ignore */ }
  }

  function listProfileKeys() {
    const profiles = loadProfiles();
    return Object.keys(profiles).sort((a, b) => a.localeCompare(b));
  }

  function syncProfileSelect() {
    const select = ui.byId("profileSelect");
    const prev = String(select.value || "").trim();
    const keys = listProfileKeys();
    select.innerHTML = "";
    const opt0 = document.createElement("option");
    opt0.value = "";
    opt0.textContent = "— профіль —";
    select.appendChild(opt0);
    const profiles = loadProfiles();
    for (const key of keys) {
      const p = profiles[key] || {};
      const label = [key, p.vehicle_id ? `(${p.vehicle_id})` : "", p.plate ? `[${p.plate}]` : ""].filter(Boolean).join(" ");
      const opt = document.createElement("option");
      opt.value = key;
      opt.textContent = label;
      select.appendChild(opt);
    }
    // Prefer: keep previous selection; otherwise select current central_id if exists.
    const ctx = readCtx();
    if (prev && keys.includes(prev)) select.value = prev;
    else if (ctx.central_id && keys.includes(ctx.central_id)) select.value = ctx.central_id;
    else select.value = "";
    syncProfileControls();
  }

  function syncProfileControls() {
    const ctx = readCtx();
    const selected = String(ui.byId("profileSelect").value || "").trim();
    ui.byId("saveProfile").disabled = !ctx.central_id;
    ui.byId("loadProfile").disabled = !selected;
    ui.byId("deleteProfile").disabled = !selected;
  }

  function renderProfileSummary() {
    const ctx = readCtx();
    const node = ui.byId("profileSummary");
    const profiles = loadProfiles();
    const currentKey = String(ctx.central_id || "").trim();
    const selected = String(ui.byId("profileSelect").value || "").trim();
    const key = currentKey || selected;
    if (!key) {
      node.innerHTML = '<span class="badge">PROFILE</span> введіть <code>central_id</code> або виберіть профіль';
      return;
    }
    const p = profiles[key];
    if (!p) {
      node.innerHTML = `<span class="badge warn">PROFILE</span> немає профілю для <code>${ui.esc(key)}</code>`;
      return;
    }
    node.innerHTML = `<span class="badge good">PROFILE</span> <code>${ui.esc(key)}</code> · bus=<code>${ui.esc(String(p.vehicle_id || "—"))}</code> · plate=<code>${ui.esc(String(p.plate || "—"))}</code> · central_ip=<code>${ui.esc(String(p.central_ip || "—"))}</code> · door2_ip=<code>${ui.esc(String(p.door1_ip || "—"))}</code> · door3_ip=<code>${ui.esc(String(p.door2_ip || "—"))}</code> · saved=<code>${ui.esc(String(p.saved_at || "—"))}</code>`;
  }

  function saveProfile() {
    const ctx = readCtx();
    if (!ctx.central_id) return;
    const profiles = loadProfiles();
    profiles[ctx.central_id] = {
      central_id: ctx.central_id,
      vehicle_id: ctx.vehicle_id,
      plate: ctx.plate,
      central_ip: ctx.central_ip,
      door1_ip: ctx.door1_ip,
      door2_ip: ctx.door2_ip,
      saved_at: new Date().toISOString(),
    };
    saveProfiles(profiles);
    addRun({ ts: new Date().toISOString(), type: "profile", result: "pass", note: `saved ${ctx.central_id}` });
    syncProfileSelect();
    renderProfileSummary();
  }

  function loadProfile() {
    const selected = String(ui.byId("profileSelect").value || "").trim();
    if (!selected) return;
    const profiles = loadProfiles();
    const p = profiles[selected];
    if (!p) return;
    ui.byId("centralId").value = String(p.central_id || selected);
    ui.byId("vehicleId").value = String(p.vehicle_id || "");
    ui.byId("plate").value = String(p.plate || "");
    ui.byId("centralIp").value = String(p.central_ip || "192.168.10.1");
    ui.byId("door1Ip").value = String(p.door1_ip || "192.168.10.11");
    ui.byId("door2Ip").value = String(p.door2_ip || "192.168.10.12");
    addRun({ ts: new Date().toISOString(), type: "profile", result: "info", note: `loaded ${selected}` });
    onCtxChanged();
  }

  function deleteProfile() {
    const selected = String(ui.byId("profileSelect").value || "").trim();
    if (!selected) return;
    if (!window.confirm(`Видалити профіль ${selected}?`)) return;
    const profiles = loadProfiles();
    delete profiles[selected];
    saveProfiles(profiles);
    addRun({ ts: new Date().toISOString(), type: "profile", result: "info", note: `deleted ${selected}` });
    syncProfileSelect();
    renderProfileSummary();
  }

  function exportProfiles() {
    const profiles = loadProfiles();
    const keys = Object.keys(profiles);
    const payload = {
      schema: "passengers-admin-commission-profiles/v1",
      exported_at: new Date().toISOString(),
      total: keys.length,
      profiles,
    };
    const text = JSON.stringify(payload, null, 2);
    addRun({ ts: new Date().toISOString(), type: "profiles:export", result: "info", note: `profiles=${keys.length}` });
    ui.copyTextWithFallback(text, "Скопіюйте JSON профілів:", "Профілі скопійовано", "Профілі у prompt");
  }

  function importProfiles() {
    const pasted = window.prompt("Вставте JSON з експорту profiles:", "");
    if (!pasted) return;
    let data = null;
    try { data = JSON.parse(String(pasted)); } catch (_error) { window.alert("Помилка: некоректний JSON"); return; }
    const incoming = (data && typeof data === "object" && data.profiles && typeof data.profiles === "object") ? data.profiles : null;
    if (!incoming) { window.alert("Помилка: JSON не містить profiles{}"); return; }
    const current = loadProfiles();
    let merged = 0;
    for (const [k, v] of Object.entries(incoming)) {
      if (!k) continue;
      if (!v || typeof v !== "object") continue;
      current[k] = v;
      merged += 1;
    }
    saveProfiles(current);
    addRun({ ts: new Date().toISOString(), type: "profiles:import", result: "pass", note: `merged=${merged}` });
    syncProfileSelect();
    renderProfileSummary();
  }

  ui.byId("copyCmds").addEventListener("click", copyCommands);
  ui.byId("copyCmds2").addEventListener("click", copyCommands);
  ui.byId("copyLinks").addEventListener("click", copyLinks);
  ui.byId("copyEvidence").addEventListener("click", copyEvidence);
  ui.byId("copyCheckCommission").addEventListener("click", copyCheckCommission);
  ui.byId("copyCheckSmoke").addEventListener("click", copyCheckSmoke);
  ui.byId("markPass").addEventListener("click", () => markResult("pass"));
  ui.byId("markFail").addEventListener("click", () => markResult("fail"));
  ui.byId("exportRuns").addEventListener("click", exportRuns);
  ui.byId("importRuns").addEventListener("click", importRuns);
  ui.byId("clearRuns").addEventListener("click", clearRuns);
  ui.byId("profileSelect").addEventListener("change", () => { syncProfileControls(); renderProfileSummary(); });
  ui.byId("saveProfile").addEventListener("click", saveProfile);
  ui.byId("loadProfile").addEventListener("click", loadProfile);
  ui.byId("deleteProfile").addEventListener("click", deleteProfile);
  ui.byId("exportProfiles").addEventListener("click", exportProfiles);
  ui.byId("importProfiles").addEventListener("click", importProfiles);
  ui.byId("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте сторінку:", "Посилання скопійовано", "Посилання у prompt"));
  ui.byId("refreshWg").addEventListener("click", refreshWgBox);
  ui.byId("refreshBackend").addEventListener("click", refreshBackendStatus);
  ui.byId("openNewTab").addEventListener("change", updateQuickLinks);
  ui.byId("useBackendVehicle").addEventListener("click", applyBackendVehicle);
  ui.byId("useBackendVehicleClearPlate").addEventListener("click", clearPlate);
  ui.bindDebouncedInputs(["centralId", "centralIp", "door1Ip", "door2Ip", "vehicleId", "plate"], onCtxChanged, REFRESH_DELAY_MS);
  ui.bindEnterRefresh(["centralId", "centralIp", "door1Ip", "door2Ip", "vehicleId", "plate"], onCtxChanged);

  applyCtxFromQuery();
  initSecondaryDetails();
  syncProfileSelect();
  onCtxChanged();
  renderRuns();
  renderProfileSummary();
  refreshWgBox();
  setInterval(() => { if (ui.byId("autoBackend").checked) refreshBackendStatus(); }, 12000);
    """.strip()
    return render_admin_shell(
        title="Адмін-панель Passengers — Підключення",
        header_title="Підключення (commissioning)",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        extra_css=extra_css,
        max_width=1320,
        current_nav="commission",
    ).strip()
