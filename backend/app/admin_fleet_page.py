from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_page() -> str:
    chips_html = """
        <span class="chip">heartbeat центральних вузлів</span>
        <span class="chip" id="roleBadge">роль: —</span>
        <span class="chip" id="updatedAt">оновлено: —</span>
"""
    toolbar_html = """
        <div class="toolbarMain">
          <input id="q" type="text" placeholder="пошук: вузол / транспорт / сервіс" />
          <label><input id="auto" type="checkbox" checked /> авто</label>
          <button id="clearFilters">Скинути фільтри</button>
          <button id="refresh" class="primary">Оновити</button>
          <button id="copyLink" title="Скопіювати поточне посилання (з урахуванням фільтрів)">Скопіювати посилання</button>
          <details class="toolbarDetails" data-advanced-details="1">
            <summary>Фільтри</summary>
            <div class="toolbarDetailsGrid">
              <input id="alertCentral" type="text" placeholder="вузол (точно)" />
              <input id="alertCode" type="text" placeholder="код (точно)" />
              <select id="sev">
                <option value="all">усі рівні</option>
                <option value="bad">критичні (bad)</option>
                <option value="warn">попередження (warn)</option>
                <option value="good">справні (good)</option>
              </select>
              <select id="opsWindow" title="вікно оперативної стрічки">
                <option value="1h">Стрічка 1г</option>
                <option value="6h">Стрічка 6г</option>
                <option value="24h" selected>Стрічка 24г</option>
                <option value="7d">Стрічка 7д</option>
              </select>
              <select id="density" title="щільність таблиць">
                <option value="regular" selected>Звичайна</option>
                <option value="compact">Компактна</option>
              </select>
              <label><input id="includeSilenced" type="checkbox" /> включити заглушені</label>
              <label><input id="onlyAlerts" type="checkbox" /> лише з алертами</label>
            </div>
          </details>
        </div>
        <div class="toolbarMeta">
          <span class="metaChip sort" id="filterSummary">фільтри: стандартні</span>
          <span class="status" id="status"></span>
        </div>
      
"""
    body_html = """
    <div class="card flowCard" style="margin-bottom: 14px;">
      <div class="flowTitle">Операторський маршрут</div>
      <div class="flowRow">
        <span class="flowStep current">1. Моніторинг флоту</span>
        <a class="flowStep" href="/admin/fleet/alerts">2. Оперативні алерти</a>
        <a class="flowStep" href="/admin/fleet/incidents?status=open&include_resolved=0">3. Інциденти та дії</a>
        <a class="flowStep" href="/admin/audit">4. Аудит і контроль</a>
      </div>
      <div class="flowHint">Використовуйте швидкі переходи для циклу: виявлення → дія → перевірка.</div>
      <div class="sectionTools" style="margin-top:8px;">
        <a class="quickLink" href="/admin/fleet/alerts">До алертів</a>
        <a class="quickLink" href="/admin/fleet/incidents?status=open&include_resolved=0">До інцидентів</a>
        <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
        <a class="quickLink" href="/admin/audit">Аудит</a>
      </div>
      <div class="workspaceBar" style="margin-top: 10px;">
        <span id="workspaceHint" class="workspaceHint empty">Контекст інциденту: —</span>
        <button id="workspaceApply" class="smallbtn">Підставити контекст</button>
        <button id="workspaceClear" class="smallbtn">Очистити контекст</button>
        <button id="cmdPaletteOpen" class="smallbtn">Команди</button>
      </div>
    </div>

    <details id="fleetToolsDetails" class="domainSplitDetails" data-advanced-details="1" style="margin-top: 14px;">
      <summary>Розширені інструменти (пресети / cockpit / rollout)</summary>
      <div class="domainSplitHint">
        Цей блок залишено для advanced-операцій (пресети, cockpit, rollout). Для щоденного triage використовуйте `Фокус` і профільні сторінки (Alerts/Incidents).
      </div>
      <div class="workspaceBar" style="margin-top: 10px;">
        <span id="presetSummary" class="workspaceHint empty">Пресети: —</span>
        <span id="presetObservability" class="workspaceHint empty">Область: —</span>
        <span id="presetTimelineHint" class="workspaceHint empty">Журнал: —</span>
        <span id="presetMergeHint" class="workspaceHint empty">Злиття: —</span>
        <span id="presetPolicyHint" class="workspaceHint empty">Політика: —</span>
        <span id="presetCockpitHint" class="workspaceHint empty">Cockpit: —</span>
        <span id="presetCockpitTimelineHint" class="workspaceHint empty">Журнал кокпіта: —</span>
        <span id="presetRolloutHint" class="workspaceHint empty">Розгортання: —</span>
        <select id="presetNamespace" title="простір пресетів">
          <option value="local" selected>локальні</option>
          <option value="shared">спільні</option>
        </select>
        <select id="presetSelect" title="збережені пресети">
          <option value="">пресети флоту</option>
        </select>
        <button id="presetSave" class="smallbtn">Зберегти</button>
        <button id="presetApply" class="smallbtn">Застосувати</button>
        <button id="presetDelete" class="smallbtn">Видалити</button>
        <button id="presetExport" class="smallbtn">Експорт</button>
        <button id="presetPreview" class="smallbtn">Попередній перегляд</button>
        <button id="presetImport" class="smallbtn">Імпорт</button>
        <button id="presetCockpit" class="smallbtn">Cockpit</button>
        <button id="presetCockpitTimeline" class="smallbtn">Журнал кокпіта</button>
        <button id="presetRollout" class="smallbtn">Розгортання</button>
        <button id="presetMetrics" class="smallbtn">Метрики</button>
        <button id="presetTimelineOpen" class="smallbtn">Журнал</button>
        <button id="presetTimelineClear" class="smallbtn">Очистити журнал</button>
        <button id="presetPolicyUnlock" class="smallbtn">Розблокувати</button>
        <button id="presetPolicyLock" class="smallbtn">Заблокувати</button>
        <button id="presetProfiles" class="smallbtn">Профілі</button>
        <button id="presetCleanup" class="smallbtn">Прибирання</button>
      </div>
    </details>

    <div class="card" style="margin-bottom: 14px;">
      <div class="sectionHead">
        <div class="sectionTitle">Оперативний пріоритет</div>
        <div class="sectionTools">
          <a class="quickLink" href="/admin/fleet/incidents">Перейти до інцидентів</a>
          <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
          <a class="quickLink" href="/admin/audit">Аудит</a>
        </div>
      </div>
      <div class="priorityGrid">
        <div class="priorityCard bad">
          <div class="priorityTitle">Критичні вузли</div>
          <div class="priorityValue bad" id="prioBadNodes">0</div>
        </div>
        <div class="priorityCard warn">
          <div class="priorityTitle">WG stale вузли</div>
          <div class="priorityValue warn" id="prioWgNodes">0</div>
        </div>
        <div class="priorityCard warn">
          <div class="priorityTitle">Вузли з чергою</div>
          <div class="priorityValue warn" id="prioQueueNodes">0</div>
        </div>
        <div class="priorityCard bad">
          <div class="priorityTitle">SLA порушено</div>
          <div class="priorityValue bad" id="prioSlaBreached">0</div>
        </div>
      </div>
      <div class="focusControls">
        <button id="focusBad" class="focusBtn bad">Фокус: критичні</button>
        <button id="focusWg" class="focusBtn warn">Фокус: WG stale</button>
        <button id="focusQueue" class="focusBtn warn">Фокус: черга</button>
        <button id="focusDoorStale" class="focusBtn warn">Фокус: door stale</button>
        <button id="focusReset" class="focusBtn good">Скинути фокус</button>
      </div>
      <div id="fleetFocusState" class="focusState good">Фільтри: стандартний режим</div>
    </div>

    <div class="card">
      <div class="sectionHead">
        <div class="sectionTitle">Центральні вузли</div>
        <div class="sectionTools">
          <a class="quickLink" href="/admin/fleet/incidents">Інциденти</a>
          <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
          <a class="quickLink" href="/admin/fleet/notify-center">Сповіщення</a>
          <a class="quickLink" href="/admin/audit">Аудит</a>
        </div>
      </div>
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code>/api/admin/fleet/overview?include_centrals=1</code></span>
        <span class="metaChip sort">сортування: <code>central_id ↑</code></span>
        <span class="metaChip mode" id="densityBadge">щільність: Звичайна</span>
      </div>
      <div class="summary">
        <span class="badge" id="sumTotal">центральних вузлів: 0</span>
        <span class="badge good" id="sumGood">справні: 0</span>
        <span class="badge warn" id="sumWarn">попередження: 0</span>
        <span class="badge bad" id="sumBad">критичні: 0</span>
        <span class="badge" id="sumAlerts">алерти: 0</span>
        <span class="badge" id="sumSilenced">заглушені: 0</span>
        <span class="badge" id="sumPending">у черзі: 0</span>
        <span class="badge" id="sumWg">застарілий WG: 0</span>
        <span class="badge" id="sumDoors">недоступні двері: 0</span>
      </div>
      <div class="tableWrap" style="margin-top: 10px;">
        <table id="tbl">
          <thead>
            <tr>
              <th>Статус</th>
              <th>Вузол</th>
              <th>Транспорт</th>
              <th>Останній heartbeat</th>
              <th>Алерти</th>
              <th>Синхронізація часу</th>
              <th>GPS</th>
              <th>Сервіси</th>
              <th>Черга</th>
              <th>Двері</th>
              <th>Деталі</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <details id="fleetSecondaryDetails" class="domainSplitDetails" data-advanced-details="1" style="margin-top: 14px;">
      <summary>Вторинна аналітика (алерти та стрічка подій)</summary>
      <div class="domainSplitHint">
        Основний triage виконуйте через <a class="quickLink" href="/admin/fleet/alerts">оперативні алерти</a> та
        <a class="quickLink" href="/admin/fleet/incidents">інциденти</a>. Цей блок залишено для розширеного перегляду контексту.
      </div>
      <div class="sectionTools" style="margin-top: 8px;">
        <a class="quickLink" href="/admin/fleet/alerts">Оперативні алерти</a>
        <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
        <a class="quickLink" href="/admin/fleet/notify-center">Сповіщення</a>
      </div>

      <div class="card" style="margin-top: 10px;">
        <div class="sectionHead">
          <div class="sectionTitle">Потік алертів</div>
          <div class="sectionTools">
            <a class="quickLink" href="/admin/fleet/alerts">Оперативні алерти</a>
            <a class="quickLink" href="/admin/fleet/incidents">Всі інциденти</a>
          </div>
        </div>
        <div class="tableMeta">
          <span class="metaChip source">джерело: <code>/api/admin/fleet/alerts</code></span>
          <span class="metaChip sort">сортування: <code>bad → warn → good</code>, далі <code>age ↓</code></span>
        </div>
        <div class="tableWrap" style="margin-top: 10px; max-height: 32vh;">
          <table id="alertsTbl">
            <thead>
              <tr>
                <th>Рівень</th>
                <th>Вузол</th>
                <th>Транспорт</th>
                <th>Код</th>
                <th>Повідомлення</th>
                <th>Вік heartbeat</th>
                <th>SLA таймер</th>
                <th>Стан</th>
                <th>Дії</th>
                <th>Деталі</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>

      <div class="card" style="margin-top: 14px;">
        <div class="sectionHead">
          <div class="sectionTitle">Оперативна стрічка подій</div>
          <div class="sectionTools">
            <a class="quickLink" href="/admin/fleet/alerts">Оперативні алерти</a>
            <a class="quickLink" href="/admin/fleet/actions">Журнал дій</a>
            <a class="quickLink" href="/admin/fleet/notify-center">Сповіщення</a>
          </div>
        </div>
        <div class="tableMeta">
          <span class="metaChip source">джерело: <code>/api/admin/fleet/ops-feed</code></span>
          <span class="metaChip sort">сортування: <code>ts ↓</code> (найновіші зверху)</span>
        </div>
        <div class="summary">
          <span class="badge" id="opsTotal">подій: 0</span>
          <span class="badge bad" id="opsBad">критичні: 0</span>
          <span class="badge warn" id="opsWarn">попередження: 0</span>
          <span class="badge good" id="opsGood">справні: 0</span>
          <span class="badge" id="opsInc">інциденти: 0</span>
          <span class="badge" id="opsAlert">алерти: 0</span>
          <span class="badge" id="opsNotif">сповіщення: 0</span>
          <span class="badge" id="opsAct">дії: 0</span>
        </div>
        <div class="tableWrap" style="margin-top: 10px; max-height: 36vh;">
          <table id="opsTbl">
            <thead>
              <tr>
                <th>Час</th>
                <th>Категорія</th>
                <th>Рівень</th>
                <th>Вузол</th>
                <th>Код / Подія</th>
                <th>Стан</th>
                <th>Деталі</th>
                <th>Перехід</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </details>
  
"""
    extra_css = """
    #q { min-width: 320px; }
    .toolbar input[type="text"] { min-width: 220px; }
    .toolbar select { min-width: 120px; }
    table { min-width: 1140px; }
    th, td { padding: 10px 10px; }
    .pill { display:inline-flex; align-items:center; gap: 6px; padding: 3px 10px; border-radius: 999px; border: 1px solid var(--border); font-size: 12px; }
    .dot { width: 8px; height: 8px; border-radius: 50%; background: var(--muted); display: inline-block; }
    .good .dot { background: var(--good); }
    .warn .dot { background: var(--warn); }
    .bad .dot { background: var(--bad); }
    .kvs { margin: 0; padding: 0; list-style: none; }
    .kvs li { margin: 0 0 4px; font-size: 12px; color: var(--muted); white-space: nowrap; }
    .badges { display:flex; flex-wrap: wrap; gap: 6px; }
    .summary { margin: 10px 0 2px; align-items:center; }
    .summary .badge { font-weight: 700; }
    .slaMeter { width: 100%; min-width: 130px; height: 7px; border-radius: 999px; background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.08); overflow: hidden; margin-top: 5px; }
    .slaFill { display:block; height: 100%; width: 4%; border-radius: 999px; }
    .slaFill.good { background: var(--good); }
    .slaFill.warn { background: var(--warn); }
    .slaFill.bad { background: var(--bad); }
    .priorityGrid { display:grid; grid-template-columns: repeat(4, minmax(180px, 1fr)); gap: 10px; margin-top: 10px; }
    .priorityCard { border: 1px solid var(--border); border-radius: 12px; padding: 10px; background: rgba(255,255,255,.03); }
    .priorityCard { transition: border-color .18s ease, transform .12s ease, background .18s ease; }
    .priorityCard:hover { transform: translateY(-1px); }
    .priorityCard.bad { border-color: rgba(255,93,93,.35); background: rgba(255,93,93,.08); }
    .priorityCard.warn { border-color: rgba(242,201,76,.35); background: rgba(242,201,76,.08); }
    .priorityCard.good { border-color: rgba(40,209,124,.35); background: rgba(40,209,124,.08); }
    .priorityTitle { color: var(--muted); font-size: 12px; }
    .priorityValue { font-size: 24px; font-weight: 700; margin-top: 4px; }
    .focusControls { display:flex; gap: 8px; flex-wrap: wrap; margin-top: 10px; }
    .focusBtn { padding: 6px 10px; border-radius: 999px; font-size: 12px; border: 1px solid var(--border); background: rgba(255,255,255,.04); color: var(--text); cursor: pointer; }
    .focusBtn { transition: border-color .18s ease, background .18s ease, transform .12s ease; }
    .focusBtn:hover { transform: translateY(-1px); }
    .focusBtn.active { box-shadow: inset 0 0 0 1px rgba(255,255,255,.16); }
    .focusBtn.bad.active { border-color: rgba(255,93,93,.5); background: rgba(255,93,93,.15); }
    .focusBtn.warn.active { border-color: rgba(242,201,76,.5); background: rgba(242,201,76,.15); }
    .focusBtn.good.active { border-color: rgba(40,209,124,.5); background: rgba(40,209,124,.15); }
    .focusState { margin-top: 10px; border: 1px solid var(--border); border-radius: 12px; padding: 8px 10px; font-size: 12px; font-weight: 600; color: var(--muted); background: rgba(255,255,255,.02); }
    .focusState.good { border-color: rgba(40,209,124,.3); background: rgba(40,209,124,.08); color: #9cebc5; }
    .focusState.warn { border-color: rgba(242,201,76,.3); background: rgba(242,201,76,.10); color: #ffe09c; }
    .focusState.bad { border-color: rgba(255,93,93,.35); background: rgba(255,93,93,.10); color: #ffb1b1; }
    .opsNote { margin-top: 4px; color: var(--muted); font-size: 12px; }
    .opsState { display:flex; gap: 6px; flex-wrap: wrap; align-items: center; }
    .opsCode { font-size: 12px; color: var(--text); }
    .opsCategory { text-transform: uppercase; letter-spacing: .2px; }
    .opsMeta { color: var(--muted); font-size: 12px; }
    .opsRow td { font-size: 13px; }
    body.density-compact th,
    body.density-compact td { padding: 6px 8px; }
    body.density-compact .kvs li { margin-bottom: 2px; font-size: 11px; }
    body.density-compact .smallbtn { padding: 4px 7px; font-size: 11px; }
    body.density-compact .drillBtn { padding: 3px 7px; font-size: 11px; }
    body.density-compact .opsRow td { font-size: 12px; }
    @media (max-width: 980px) { .priorityGrid { grid-template-columns: repeat(2, minmax(180px, 1fr)); } }
    @media (max-width: 560px) { .priorityGrid { grid-template-columns: 1fr; } }
  
""".strip()
    script = """
  const ui = window.AdminUiKit;
  const esc = ui.esc;
  const FLEET_SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_fleet_secondary_details_v1";
  const FLEET_TOOLS_DETAILS_STORAGE_KEY = "passengers_admin_fleet_tools_details_v1";
  let adminRole = "viewer";
  let adminCaps = { read: true, operate: false, admin: false };
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
  function setStatus(s) { ui.setStatus("status", s); }
  function sevLabel(level) {
    const normalized = String(level || "").toLowerCase();
    if (normalized === "good") return "СПРАВНО";
    if (normalized === "warn") return "ПОПЕРЕДЖЕННЯ";
    return "КРИТИЧНО";
  }
  function gpsCellHtml(gps) {
    const g = gps && typeof gps === "object" ? gps : null;
    if (!g) return '<span class="badge">—</span>';
    const fix = !!g.fix;
    const age = g.age_sec === null || g.age_sec === undefined ? null : Number(g.age_sec);
    if (!fix) {
      const hint = age !== null && !Number.isNaN(age) ? `оновл.: ${fmtAge(age)}` : "оновл.: —";
      return `<div class="badges"><span class="badge warn">NO FIX</span><span class="badge">${esc(hint)}</span></div>`;
    }
    const lat = g.lat === null || g.lat === undefined ? null : Number(g.lat);
    const lon = g.lon === null || g.lon === undefined ? null : Number(g.lon);
    const coords = lat !== null && lon !== null && !Number.isNaN(lat) && !Number.isNaN(lon)
      ? `${lat.toFixed(5)}, ${lon.toFixed(5)}`
      : "коорд.: —";
    const hint = age !== null && !Number.isNaN(age) ? `оновл.: ${fmtAge(age)}` : "оновл.: —";
    return `<div class="kvs"><div><span class="badge good">FIX</span> <code>${esc(coords)}</code></div><div class="muted">${esc(hint)}</div></div>`;
  }
  function opsCategoryLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "incident") return "ІНЦИДЕНТ";
    if (normalized === "alert") return "АЛЕРТ";
    if (normalized === "notification") return "СПОВІЩЕННЯ";
    if (normalized === "action") return "ДІЯ";
    return "ПОДІЯ";
  }
  function opsStatusClass(category, status) {
    const normalizedCategory = String(category || "").toLowerCase();
    const normalizedStatus = String(status || "").toLowerCase();
    if (normalizedCategory === "notification") {
      if (normalizedStatus === "sent") return "good";
      if (normalizedStatus === "skipped") return "warn";
      return "bad";
    }
    if (normalizedCategory === "action") {
      if (normalizedStatus === "ack" || normalizedStatus === "unsilence") return "good";
      if (normalizedStatus === "silence") return "warn";
      return "warn";
    }
    if (normalizedCategory === "incident") {
      if (normalizedStatus === "resolved") return "good";
      if (normalizedStatus === "acked" || normalizedStatus === "silenced") return "warn";
      return "bad";
    }
    if (normalizedCategory === "alert") {
      if (normalizedStatus === "silenced") return "warn";
      return "bad";
    }
    return "warn";
  }
  function opsStatusLabel(category, status) {
    const normalizedCategory = String(category || "").toLowerCase();
    const normalizedStatus = String(status || "").toLowerCase();
    if (normalizedCategory === "notification") {
      if (normalizedStatus === "sent") return "НАДІСЛАНО";
      if (normalizedStatus === "skipped") return "ПРОПУЩЕНО";
      if (normalizedStatus === "failed") return "ПОМИЛКА";
      return "НЕВІДОМО";
    }
    if (normalizedCategory === "action") {
      if (normalizedStatus === "ack") return "ПІДТВЕРДЖЕНО";
      if (normalizedStatus === "silence") return "ЗАГЛУШЕНО";
      if (normalizedStatus === "unsilence") return "ЗНЯТО ЗАГЛУШЕННЯ";
      return "ДІЯ";
    }
    if (normalizedCategory === "incident") {
      if (normalizedStatus === "open") return "ВІДКРИТО";
      if (normalizedStatus === "acked") return "ПІДТВЕРДЖЕНО";
      if (normalizedStatus === "silenced") return "ЗАГЛУШЕНО";
      if (normalizedStatus === "resolved") return "ВИРІШЕНО";
      return "ІНЦИДЕНТ";
    }
    if (normalizedCategory === "alert") {
      if (normalizedStatus === "silenced") return "ЗАГЛУШЕНО";
      return "АКТИВНО";
    }
    return "ПОДІЯ";
  }
  function renderOpsFeed(data) {
    const summary = data && data.summary ? data.summary : {};
    const categories = summary.categories || {};
    const severity = summary.severity || {};
    const events = Array.isArray(data && data.events) ? data.events : [];
    document.getElementById("opsTotal").textContent = `подій: ${data && data.total ? data.total : events.length}`;
    document.getElementById("opsBad").textContent = `критичні: ${severity.bad || 0}`;
    document.getElementById("opsWarn").textContent = `попередження: ${severity.warn || 0}`;
    document.getElementById("opsGood").textContent = `справні: ${severity.good || 0}`;
    document.getElementById("opsInc").textContent = `інциденти: ${categories.incident || 0}`;
    document.getElementById("opsAlert").textContent = `алерти: ${categories.alert || 0}`;
    document.getElementById("opsNotif").textContent = `сповіщення: ${categories.notification || 0}`;
    document.getElementById("opsAct").textContent = `дії: ${categories.action || 0}`;

    const tbody = document.querySelector("#opsTbl tbody");
    tbody.innerHTML = "";
    if (events.length === 0) {
      const row = document.createElement("tr");
      row.innerHTML = '<td colspan="8"><span class="badge good">OK</span> Події за вибраним вікном відсутні</td>';
      tbody.appendChild(row);
      return;
    }
    for (const item of events) {
      const row = document.createElement("tr");
      row.className = "opsRow";
      const category = String(item.category || "");
      const status = String(item.status || "");
      const statusClass = opsStatusClass(category, status);
      const centralId = String(item.central_id || "");
      const code = String(item.code || "");
      const link = String(item.link || "").trim();
      const noteParts = [];
      if (item.meta && item.meta.channel) noteParts.push(`канал=${item.meta.channel}`);
      if (item.meta && item.meta.event) noteParts.push(`event=${item.meta.event}`);
      if (item.meta && item.meta.actor) noteParts.push(`актор=${item.meta.actor}`);
      if (item.meta && item.meta.sla_breached) noteParts.push("SLA порушено");
      if (item.meta && item.meta.silenced_until) noteParts.push(`до=${item.meta.silenced_until}`);
      const details = String(item.message || "");
      row.innerHTML = `
        <td><code>${ui.esc(item.ts || "—")}</code></td>
        <td><span class="badge opsCategory">${ui.esc(opsCategoryLabel(category))}</span></td>
        <td><span class="badge ${statusClass}">${ui.esc(sevLabel(item.severity || "warn"))}</span></td>
        <td><a href="/admin/fleet/central/${encodeURIComponent(centralId)}"><code>${ui.esc(centralId || "—")}</code></a></td>
        <td><span class="opsCode"><code>${ui.esc(code || "—")}</code></span></td>
        <td><span class="badge ${statusClass}">${ui.esc(opsStatusLabel(category, status))}</span></td>
        <td><div>${ui.esc(details || "—")}</div><div class="opsNote">${ui.esc(noteParts.join(" · ") || "—")}</div></td>
        <td>${link ? `<a class="drillBtn" data-workspace-link="1" href="${ui.esc(link)}">Відкрити</a>` : '<span class="badge">—</span>'}</td>
      `;
      row.querySelector('a[data-workspace-link="1"]')?.addEventListener("click", () => {
        saveWorkspaceContext(centralId, code, "fleet/ops-feed");
      });
      tbody.appendChild(row);
    }
  }
  function applyRoleUi() {
    document.getElementById("roleBadge").textContent = `роль: ${adminRole}`;
  }
  function initFleetSecondaryDetails() {
    const node = document.getElementById("fleetSecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {
      const raw = String(localStorage.getItem(FLEET_SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {}
    node.addEventListener("toggle", () => {
      try { localStorage.setItem(FLEET_SECONDARY_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); } catch (_error) {}
    });
  }
  function initFleetToolsDetails() {
    const node = document.getElementById("fleetToolsDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {
      const raw = String(localStorage.getItem(FLEET_TOOLS_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {}
    node.addEventListener("toggle", () => {
      try { localStorage.setItem(FLEET_TOOLS_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); } catch (_error) {}
    });
  }
  function canOperate() { return !!adminCaps.operate; }
  async function loadWhoami() {
    const data = await ui.loadWhoami();
    adminRole = data.role;
    adminCaps = data.capabilities || { read: true, operate: false, admin: false };
    applyRoleUi();
  }
  function query() { return (document.getElementById("q").value || "").trim().toLowerCase(); }
  function alertCentral() { return (document.getElementById("alertCentral").value || "").trim(); }
  function alertCode() { return (document.getElementById("alertCode").value || "").trim(); }
  function selectedSeverity() { return (document.getElementById("sev").value || "all").toLowerCase(); }
  function selectedOpsWindow() { return (document.getElementById("opsWindow").value || "24h").toLowerCase(); }
  const PRESET_SCOPE = "fleet";
  const TEAM_PRESET_SCOPES = ["fleet", "fleet_alerts", "fleet_incidents"];
  let lastPresetImportRaw = "";
  let lastPresetPreview = null;
  let lastPresetCockpitRaw = "";
  let lastPresetCockpitPreview = null;
  let lastPresetCockpitScopes = [...TEAM_PRESET_SCOPES];
  let lastPresetRolloutPlan = null;
  const scheduleRefresh = ui.debounce(() => {
    syncQueryFromFilters();
    syncFilterSummary();
    refresh();
  }, 280);
  function syncDensityBadge(mode) {
    const label = ui.densityLabel(mode);
    document.getElementById("densityBadge").textContent = `щільність: ${label}`;
  }
  function saveWorkspaceContext(centralId, code, source) {
    const cleanCentral = String(centralId || "").trim();
    const cleanCode = String(code || "").trim();
    const label = cleanCentral && cleanCode ? `${cleanCentral}:${cleanCode}` : (cleanCentral || cleanCode || "");
    ui.saveWorkspaceContext({
      central_id: cleanCentral,
      code: cleanCode,
      source: source || "fleet",
      label,
    });
    refreshWorkspaceHint();
  }
  function refreshWorkspaceHint() {
    ui.applyWorkspaceHint("workspaceHint", { prefix: "Контекст інциденту", maxAgeSec: 3 * 24 * 3600 });
  }
  function collectPresetPayload() {
    return {
      q: document.getElementById("q").value || "",
      alertCentral: document.getElementById("alertCentral").value || "",
      alertCode: document.getElementById("alertCode").value || "",
      severity: document.getElementById("sev").value || "all",
      includeSilenced: !!document.getElementById("includeSilenced").checked,
      onlyAlerts: !!document.getElementById("onlyAlerts").checked,
      opsWindow: document.getElementById("opsWindow").value || "24h",
    };
  }
  function selectedPresetNamespace() {
    return ui.normalizePresetNamespace(document.getElementById("presetNamespace").value || "local");
  }
  function formatTs(value) {
    const parsed = Date.parse(String(value || ""));
    if (!Number.isFinite(parsed)) return "—";
    return new Date(parsed).toLocaleString("uk-UA");
  }
  function timelineActionLabel(action) {
    const normalized = String(action || "").trim().toLowerCase();
    if (normalized === "save_preset") return "збереження";
    if (normalized === "delete_preset") return "видалення";
    if (normalized === "cleanup_presets") return "cleanup";
    if (normalized === "install_profiles") return "профілі";
    if (normalized === "import_presets") return "імпорт";
    if (normalized === "import_bundle") return "імпорт bundle";
    if (normalized === "export_presets") return "експорт";
    if (normalized === "export_bundle") return "експорт bundle";
    if (normalized === "policy_unlock") return "policy unlock";
    if (normalized === "policy_lock") return "блокування політики";
    if (normalized === "rollout_assistant_apply") return "rollout apply";
    return normalized || "подія";
  }
  function parsePresetPreview(raw, mode = "merge") {
    const namespace = selectedPresetNamespace();
    if (namespace === "shared") {
      return ui.simulatePresetBundleImport(raw, { namespace, mode, scopes: TEAM_PRESET_SCOPES });
    }
    return ui.simulatePresetImport(PRESET_SCOPE, raw, { namespace, mode });
  }
  function previewSummary(summary) {
    const source = summary && typeof summary === "object" ? summary : {};
    return `+${source.create || 0} ~${source.update || 0} ⟳${source.refresh_ts || 0} =${source.result_total || 0} !${source.conflicts || 0} -${source.drop || 0} lock=${source.protected_blocked || 0}`;
  }
  function previewPayloadForPrompt(preview) {
    const payload = preview && typeof preview === "object" ? { ...preview } : {};
    if (Array.isArray(payload.entries)) payload.entries = payload.entries.slice(0, 80);
    if (Array.isArray(payload.scopes)) {
      payload.scopes = payload.scopes.map((scope) => ({
        ...scope,
        entries: Array.isArray(scope && scope.entries) ? scope.entries.slice(0, 20) : [],
      }));
    }
    return payload;
  }
  function parseScopeList(raw) {
    const allowed = new Set(TEAM_PRESET_SCOPES.map((item) => String(item).toLowerCase()));
    const source = String(raw || "")
      .split(",")
      .map((item) => String(item || "").trim().toLowerCase())
      .filter((item) => !!item && allowed.has(item));
    return source.length > 0 ? Array.from(new Set(source.values())) : [...TEAM_PRESET_SCOPES];
  }
  function requestCockpitScopes() {
    const base = lastPresetCockpitScopes.length ? lastPresetCockpitScopes : TEAM_PRESET_SCOPES;
    const raw = String(window.prompt("Scopes для cockpit (через кому):", base.join(",")) || "").trim();
    const scopes = parseScopeList(raw);
    lastPresetCockpitScopes = scopes;
    return scopes;
  }
  function refreshPresetSummary() {
    const summaryNode = document.getElementById("presetSummary");
    const observabilityNode = document.getElementById("presetObservability");
    if (!summaryNode || !observabilityNode) return;
    try {
      const namespace = selectedPresetNamespace();
      const report = ui.buildPresetScopeObservability(PRESET_SCOPE);
      const activeTotal = namespace === "shared" ? report.shared_total : report.local_total;
      const activeArchived = namespace === "shared" ? report.shared_archived_total : report.local_archived_total;
      summaryNode.textContent = `Пресети(${namespace}): ${activeTotal} · архів=${activeArchived}`;
      summaryNode.classList.toggle("empty", activeTotal === 0 && activeArchived === 0);
      const localCleanup = report.local_last_cleanup_ts ? formatTs(report.local_last_cleanup_ts) : "—";
      const sharedCleanup = report.shared_last_cleanup_ts ? formatTs(report.shared_last_cleanup_ts) : "—";
      observabilityNode.textContent = `Scope ${PRESET_SCOPE}: total=${report.total} (L:${report.local_total}/S:${report.shared_total}) · архів=${report.archived_total} (L:${report.local_archived_total}/S:${report.shared_archived_total}) · cleanup L:${localCleanup} S:${sharedCleanup}`;
      observabilityNode.classList.toggle("empty", report.total === 0 && report.archived_total === 0 && !report.last_cleanup_ts);
    } catch (_error) {
      summaryNode.textContent = "Пресети: —";
      summaryNode.classList.add("empty");
      observabilityNode.textContent = "Область: —";
      observabilityNode.classList.add("empty");
    }
  }
  function refreshPresetMergeHint() {
    const node = document.getElementById("presetMergeHint");
    if (!node) return;
    const namespace = selectedPresetNamespace();
    if (!lastPresetPreview || String(lastPresetPreview.namespace || "") !== namespace) {
      node.textContent = "Злиття: —";
      node.classList.add("empty");
      return;
    }
    const mode = String(lastPresetPreview.mode || "merge");
    const summary = lastPresetPreview.summary || {};
    node.textContent = `Merge(${namespace}/${mode}): ${previewSummary(summary)}`;
    node.classList.toggle("empty", false);
  }
  function refreshPresetPolicyHint() {
    const node = document.getElementById("presetPolicyHint");
    if (!node) return;
    try {
      const namespace = selectedPresetNamespace();
      const state = ui.getPresetProtectionState(PRESET_SCOPE, { namespace });
      const lockText = state.locked ? "ЗАБЛОКОВАНО" : "РОЗБЛОКОВАНО";
      node.textContent = `Політика(${namespace}): ${lockText} · protected=${state.protected_total}`;
      node.classList.toggle("empty", false);
    } catch (_error) {
      node.textContent = "Політика: —";
      node.classList.add("empty");
    }
  }
  function refreshPresetCockpitHint() {
    const node = document.getElementById("presetCockpitHint");
    if (!node) return;
    const namespace = selectedPresetNamespace();
    if (lastPresetCockpitPreview && String(lastPresetCockpitPreview.namespace || "") === namespace) {
      const summary = lastPresetCockpitPreview.summary || {};
      node.textContent = `Cockpit(${namespace}): scopes=${summary.scope_count || 0} !${summary.conflicts || 0} lock=${summary.protected_blocked || 0} =${summary.result_total || 0}`;
      node.classList.toggle("empty", false);
      return;
    }
    try {
      const report = ui.buildPresetOperationsSummary({ namespace, scopes: lastPresetCockpitScopes });
      const summary = report.summary || {};
      node.textContent = `Cockpit(${namespace}): scopes=${summary.scope_count || 0} locked=${summary.locked_count || 0} presets=${summary.presets_total || 0}`;
      node.classList.toggle("empty", false);
    } catch (_error) {
      node.textContent = "Cockpit: —";
      node.classList.add("empty");
    }
  }
  function refreshPresetCockpitTimelineHint() {
    const node = document.getElementById("presetCockpitTimelineHint");
    if (!node) return;
    try {
      const namespace = selectedPresetNamespace();
      const report = ui.buildPresetCockpitTimeline({ namespace, scopes: lastPresetCockpitScopes, limit: 30 });
      const summary = report.summary || {};
      const lastTs = String(summary.last_ts || "");
      const lastAction = String(summary.last_action || "");
      node.textContent = `Журнал кокпіта(${namespace}): ${summary.visible_total || 0} · остання: ${lastAction ? timelineActionLabel(lastAction) : "—"} · ${lastTs ? formatTs(lastTs) : "—"}`;
      node.classList.toggle("empty", Number(summary.visible_total || 0) === 0);
    } catch (_error) {
      node.textContent = "Журнал кокпіта: —";
      node.classList.add("empty");
    }
  }
  function openCockpitTimelineDetails(entry) {
    const payload = entry && typeof entry === "object" ? entry : {};
    window.prompt("Деталі таймлайну кокпіта (JSON):", JSON.stringify(payload, null, 2));
  }
  function showPresetCockpitTimelinePanel() {
    const namespace = selectedPresetNamespace();
    const scopes = lastPresetCockpitScopes.length ? lastPresetCockpitScopes : TEAM_PRESET_SCOPES;
    ui.openPresetCockpitTimelinePanel({
      title: "Cockpit журнал пресетів",
      namespace,
      scopes,
      limit: 120,
      onDrillDown: openCockpitTimelineDetails,
    });
    refreshPresetCockpitTimelineHint();
  }
  function rolloutPlanPayloadForPrompt(plan) {
    const source = plan && typeof plan === "object" ? plan : {};
    return {
      generated_at: String(source.generated_at || ""),
      namespace: String(source.namespace || ""),
      mode: String(source.mode || "merge"),
      scopes: Array.isArray(source.scopes) ? source.scopes : [],
      summary: source.summary && typeof source.summary === "object" ? source.summary : {},
      operations_summary: source.operations_summary && typeof source.operations_summary === "object" ? source.operations_summary : {},
      checklist: Array.isArray(source.checklist) ? source.checklist : [],
      postcheck: Array.isArray(source.postcheck) ? source.postcheck : [],
    };
  }
  function refreshPresetRolloutHint() {
    const node = document.getElementById("presetRolloutHint");
    if (!node) return;
    try {
      const namespace = selectedPresetNamespace();
      const last = ui.getPresetRolloutLast({ namespace });
      if (!last) {
        node.textContent = "Розгортання: —";
        node.classList.add("empty");
        return;
      }
      const resultSummary = last.summary && last.summary.result && typeof last.summary.result === "object" ? last.summary.result : {};
      node.textContent = `Розгортання(${namespace}): ${last.mode || "merge"} scopes=${(last.scopes || []).length} imported=${resultSummary.imported || 0} total=${resultSummary.total || 0} · ${last.ts ? formatTs(last.ts) : "—"}`;
      node.classList.toggle("empty", false);
    } catch (_error) {
      node.textContent = "Розгортання: —";
      node.classList.add("empty");
    }
  }
  function showLastPresetRolloutSummary() {
    const namespace = selectedPresetNamespace();
    const last = ui.getPresetRolloutLast({ namespace });
    if (!last) {
      setStatus(`Розгортання: summary відсутній (${namespace})`);
      refreshPresetRolloutHint();
      return;
    }
    window.prompt("Останній summary розгортання (JSON):", JSON.stringify(last, null, 2));
    refreshPresetRolloutHint();
  }
  function runPresetRolloutAssistant(defaultMode = "merge") {
    const namespace = selectedPresetNamespace();
    const scopes = requestCockpitScopes();
    const modeRaw = String(window.prompt("Режим розгортання (merge/replace):", defaultMode) || "").trim().toLowerCase();
    if (!modeRaw) return;
    const mode = modeRaw === "replace" ? "replace" : "merge";
    const raw = String(window.prompt(`JSON розгортання (${mode}):`, lastPresetCockpitRaw || lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const plan = ui.buildPresetRolloutAssistant(raw, { namespace, mode, scopes });
      lastPresetRolloutPlan = plan;
      lastPresetCockpitRaw = raw;
      window.prompt("План dry-run розгортання (JSON):", JSON.stringify(rolloutPlanPayloadForPrompt(plan), null, 2));
      const rollbackBundle = String(plan.rollback_hint && plan.rollback_hint.bundle_json ? plan.rollback_hint.bundle_json : "");
      window.prompt("Rollback bundle JSON (збережіть до apply):", rollbackBundle);
      const checklistAck = String(window.prompt("Підтвердіть checklist: введіть CHECKLIST-OK", "") || "").trim().toUpperCase();
      if (checklistAck !== "CHECKLIST-OK") {
        setStatus(`Розгортання ${mode} скасовано: checklist`);
        return;
      }
      const summary = plan.summary || {};
      const conflicts = Number(summary.conflicts || 0);
      const drops = Number(summary.drop || 0);
      const blocked = Number(summary.protected_blocked || 0);
      if (conflicts > 0 && !window.confirm(`Розгортання: конфлікти=${conflicts}. Продовжити ${mode}?`)) {
        setStatus(`Розгортання ${mode} скасовано: конфлікти=${conflicts}`);
        return;
      }
      if (mode === "replace" && drops > 0 && !window.confirm(`Розгортання replace видалить ${drops} пресет(ів). Підтвердити?`)) {
        setStatus(`Розгортання replace скасовано: drop=${drops}`);
        return;
      }
      let allowProtectedWrite = false;
      if (blocked > 0) {
        const phrase = String(window.prompt(`Розгортання заблоковано policy (${blocked}). Введіть UNLOCK для продовження:`, "") || "").trim().toUpperCase();
        if (phrase !== "UNLOCK") {
          setStatus(`Розгортання ${mode} скасовано: блокування політики`);
          return;
        }
        allowProtectedWrite = true;
      }
      const applyAck = String(window.prompt("Підтвердіть apply: введіть APPLY", "") || "").trim().toUpperCase();
      if (applyAck !== "APPLY") {
        setStatus(`Розгортання ${mode} скасовано: apply`);
        return;
      }
      const result = ui.applyPresetRolloutAssistant(raw, { namespace, mode, scopes, allowProtectedWrite });
      loadPresetSelect("");
      const output = result && result.result && result.result.result && typeof result.result.result === "object"
        ? result.result.result
        : (result && result.result && typeof result.result === "object" ? result.result : {});
      setStatus(`Розгортання ${mode}: imported=${output.imported || 0}, total=${output.total || 0}, scopes=${scopes.length}`);
      window.prompt("Post-check розгортання (JSON):", JSON.stringify({ postcheck: plan.postcheck || [] }, null, 2));
      refreshPresetSummary();
      refreshPresetTimelineHint();
      refreshPresetMergeHint();
      refreshPresetPolicyHint();
      refreshPresetCockpitHint();
      refreshPresetCockpitTimelineHint();
      refreshPresetRolloutHint();
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Розгортання заблоковано блокування політики (${namespace})`);
        refreshPresetPolicyHint();
      } else {
        setStatus(`ПОМИЛКА assistant розгортання: ${error}`);
      }
    }
  }
  function previewPresetCockpit(mode = "merge") {
    const namespace = selectedPresetNamespace();
    const scopes = requestCockpitScopes();
    const raw = String(window.prompt(`JSON кокпіта (${mode}):`, lastPresetCockpitRaw || lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const preview = ui.simulatePresetOperations(raw, { namespace, mode, scopes });
      lastPresetCockpitRaw = raw;
      lastPresetCockpitPreview = preview;
      refreshPresetCockpitHint();
      window.prompt(`Попередній перегляд кокпіта ${mode} (JSON):`, JSON.stringify(previewPayloadForPrompt(preview), null, 2));
      setStatus(`Попередній перегляд кокпіта ${mode}: ${previewSummary(preview.summary || {})}`);
    } catch (error) {
      setStatus(`ПОМИЛКА preview кокпіта: ${error}`);
    }
  }
  function applyPresetCockpit(mode = "merge") {
    const namespace = selectedPresetNamespace();
    const scopes = requestCockpitScopes();
    const raw = String(window.prompt(`Apply JSON кокпіта (${mode}):`, lastPresetCockpitRaw || lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const preview = ui.simulatePresetOperations(raw, { namespace, mode, scopes });
      lastPresetCockpitRaw = raw;
      lastPresetCockpitPreview = preview;
      refreshPresetCockpitHint();
      const summary = preview.summary || {};
      const conflicts = Number(summary.conflicts || 0);
      const drops = Number(summary.drop || 0);
      const blocked = Number(summary.protected_blocked || 0);
      if (conflicts > 0 && !window.confirm(`Cockpit: конфлікти=${conflicts}. Продовжити ${mode}?`)) {
        setStatus(`Cockpit ${mode} скасовано: конфлікти=${conflicts}`);
        return;
      }
      if (mode === "replace" && drops > 0 && !window.confirm(`Cockpit replace видалить ${drops} пресет(ів). Підтвердити?`)) {
        setStatus(`Cockpit replace скасовано: drop=${drops}`);
        return;
      }
      let allowProtectedWrite = false;
      if (blocked > 0) {
        const phrase = String(window.prompt(`Cockpit заблоковано policy (${blocked}). Введіть UNLOCK для продовження:`, "") || "").trim().toUpperCase();
        if (phrase !== "UNLOCK") {
          setStatus(`Cockpit ${mode} скасовано: блокування політики`);
          return;
        }
        allowProtectedWrite = true;
      }
      const result = ui.applyPresetOperations(raw, { namespace, mode, scopes, allowProtectedWrite });
      loadPresetSelect("");
      setStatus(`Cockpit ${mode}: imported=${result.result && result.result.imported ? result.result.imported : 0}, total=${result.result && result.result.total ? result.result.total : 0}, conflicts=${conflicts}, blocked=${blocked}`);
      refreshPresetSummary();
      refreshPresetTimelineHint();
      refreshPresetMergeHint();
      refreshPresetPolicyHint();
      refreshPresetCockpitHint();
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Cockpit заблоковано блокування політики (${namespace})`);
        refreshPresetPolicyHint();
      } else {
        setStatus(`ПОМИЛКА cockpit apply: ${error}`);
      }
    }
  }
  function setPresetCockpitLockBatch(locked) {
    const namespace = selectedPresetNamespace();
    const scopes = requestCockpitScopes();
    if (!locked) {
      const phrase = String(window.prompt(`Підтвердіть UNLOCK batch для ${scopes.join(",")} (${namespace}):`, "") || "").trim().toUpperCase();
      if (phrase !== "UNLOCK") {
        setStatus("Пакетне розблокування скасовано");
        return;
      }
    }
    const result = ui.setPresetProtectionLockBatch(scopes, locked, { namespace });
    setStatus(`Cockpit policy ${locked ? "lock" : "unlock"}: scopes=${result.summary.scope_count}, locked=${result.summary.locked_count}`);
    refreshPresetPolicyHint();
    refreshPresetTimelineHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
  }
  function lockPresetPolicy() {
    const namespace = selectedPresetNamespace();
    ui.setPresetProtectionLock(PRESET_SCOPE, true, { namespace });
    setStatus(`Policy lock увімкнено (${namespace})`);
    refreshPresetPolicyHint();
    refreshPresetTimelineHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
  }
  function unlockPresetPolicy() {
    const namespace = selectedPresetNamespace();
    const phrase = String(window.prompt(`Підтвердіть UNLOCK для ${PRESET_SCOPE} (${namespace}):`, "") || "").trim().toUpperCase();
    if (phrase !== "UNLOCK") {
      setStatus("Unlock скасовано");
      return;
    }
    ui.setPresetProtectionLock(PRESET_SCOPE, false, { namespace });
    setStatus(`Policy lock вимкнено (${namespace})`);
    refreshPresetPolicyHint();
    refreshPresetTimelineHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
  }
  function refreshPresetTimelineHint() {
    const node = document.getElementById("presetTimelineHint");
    if (!node) return;
    try {
      const namespace = selectedPresetNamespace();
      const summary = ui.buildPresetTimelineSummary(PRESET_SCOPE, { namespace });
      if (!summary.last_ts) {
        node.textContent = `Журнал(${namespace}): ${summary.count} · остання: —`;
        node.classList.toggle("empty", summary.count === 0);
        return;
      }
      node.textContent = `Журнал(${namespace}): ${summary.count} · остання: ${timelineActionLabel(summary.last_action)} · ${formatTs(summary.last_ts)}`;
      node.classList.toggle("empty", false);
    } catch (_error) {
      node.textContent = "Журнал: —";
      node.classList.add("empty");
    }
  }
  function showPresetTimeline() {
    const namespace = selectedPresetNamespace();
    const bundle = ui.buildPresetTimelineBundle({ namespace, scopes: TEAM_PRESET_SCOPES });
    window.prompt("Журнал пресетів (JSON):", JSON.stringify(bundle, null, 2));
    refreshPresetTimelineHint();
    refreshPresetCockpitTimelineHint();
  }
  function clearPresetTimelineEntries() {
    const namespace = selectedPresetNamespace();
    if (!window.confirm(`Очистити журнал пресетів для scope "${PRESET_SCOPE}" (${namespace})?`)) return;
    const removed = ui.clearPresetTimeline(PRESET_SCOPE, { namespace });
    setStatus(`Журнал очищено (${namespace}): видалено=${removed}`);
    refreshPresetTimelineHint();
    refreshPresetCockpitTimelineHint();
  }
  function openPresetTimelineDetails(item) {
    const entry = item && typeof item === "object" ? item : {};
    const label = timelineActionLabel(entry.action);
    const payload = {
      ts: String(entry.ts || ""),
      action: String(entry.action || ""),
      scope: String(entry.scope || PRESET_SCOPE),
      namespace: String(entry.namespace || selectedPresetNamespace()),
      details: entry.details && typeof entry.details === "object" ? entry.details : {},
    };
    window.prompt(`Деталі журналу: ${label}`, JSON.stringify(payload, null, 2));
  }
  function previewPresetImport(mode = "merge") {
    const raw = String(window.prompt(`Попередній перегляд JSON пресетів (${mode}):`, lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const preview = parsePresetPreview(raw, mode);
      lastPresetImportRaw = raw;
      lastPresetPreview = preview;
      refreshPresetMergeHint();
      window.prompt(`Попередній перегляд  (JSON):`, JSON.stringify(previewPayloadForPrompt(preview), null, 2));
      setStatus(`Попередній перегляд : ${previewSummary(preview.summary || {})}`);
    } catch (error) {
      setStatus(`ПОМИЛКА preview: ${error}`);
    }
  }
  function applyPresetPayload(payload) {
    const source = payload && typeof payload === "object" ? payload : {};
    document.getElementById("q").value = String(source.q || "");
    document.getElementById("alertCentral").value = String(source.alertCentral || "");
    document.getElementById("alertCode").value = String(source.alertCode || "");
    document.getElementById("sev").value = String(source.severity || "all");
    document.getElementById("includeSilenced").checked = !!source.includeSilenced;
    document.getElementById("onlyAlerts").checked = !!source.onlyAlerts;
    document.getElementById("opsWindow").value = String(source.opsWindow || "24h");
  }
  function loadPresetSelect(selectedName) {
    const presets = ui.listPresets(PRESET_SCOPE, { namespace: selectedPresetNamespace() });
    const select = document.getElementById("presetSelect");
    const prev = selectedName || select.value || "";
    select.innerHTML = '<option value="">пресети флоту</option>';
    for (const item of presets) {
      const option = document.createElement("option");
      option.value = item.name;
      option.textContent = item.name;
      select.appendChild(option);
    }
    if (prev && presets.some((item) => item.name === prev)) {
      select.value = prev;
    }
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetMergeHint();
    refreshPresetPolicyHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
    refreshPresetRolloutHint();
  }
  function saveCurrentPreset() {
    const namespace = selectedPresetNamespace();
    const selected = document.getElementById("presetSelect").value || "";
    const name = String(window.prompt("Назва пресету флоту:", selected || "") || "").trim();
    if (!name) return;
    try {
      ui.savePreset(PRESET_SCOPE, name, collectPresetPayload(), { namespace });
      loadPresetSelect(name);
      setStatus(`Пресет збережено (${namespace}): ${name}`);
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Заборонено блокування політики (${namespace}): unlock потрібен для overwrite protected preset`);
        refreshPresetPolicyHint();
        refreshPresetCockpitHint();
      } else {
        setStatus(`ПОМИЛКА save: ${error}`);
      }
    }
  }
  function applySelectedPreset() {
    const namespace = selectedPresetNamespace();
    const name = document.getElementById("presetSelect").value || "";
    if (!name) {
      setStatus("Оберіть пресет");
      return;
    }
    const preset = ui.getPreset(PRESET_SCOPE, name, { namespace });
    if (!preset) {
      setStatus(`Пресет не знайдено: ${name}`);
      return;
    }
    applyPresetPayload(preset.data || {});
    setStatus(`Застосовано пресет (${namespace}): ${name}`);
    refresh();
  }
  function deleteSelectedPreset() {
    const namespace = selectedPresetNamespace();
    const name = document.getElementById("presetSelect").value || "";
    if (!name) {
      setStatus("Оберіть пресет");
      return;
    }
    if (!window.confirm(`Видалити пресет "${name}"?`)) return;
    try {
      ui.deletePreset(PRESET_SCOPE, name, { namespace });
      loadPresetSelect("");
      setStatus(`Пресет видалено (${namespace}): ${name}`);
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Заборонено блокування політики (${namespace}): видалення захищеного пресету заблоковано`);
        refreshPresetPolicyHint();
        refreshPresetCockpitHint();
      } else {
        setStatus(`ПОМИЛКА delete: ${error}`);
      }
    }
  }
  async function copyTextBestEffort(text) {
    try {
      if (navigator.clipboard && navigator.clipboard.writeText) {
        await navigator.clipboard.writeText(text);
        return true;
      }
    } catch (_error) {}
    return false;
  }
  async function exportPresetData() {
    const namespace = selectedPresetNamespace();
    let raw = "";
    if (namespace === "shared") {
      raw = ui.exportPresetBundle({ namespace, scopes: TEAM_PRESET_SCOPES });
    } else {
      raw = ui.exportPresets(PRESET_SCOPE, { namespace });
    }
    const copied = await copyTextBestEffort(raw);
    window.prompt("JSON пресетів (скопіюйте):", raw);
    setStatus(`Експорт пресетів (${namespace})${copied ? " · скопійовано" : ""}`);
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
    refreshPresetRolloutHint();
  }
  function importPresetData(mode = "merge") {
    const namespace = selectedPresetNamespace();
    const raw = String(window.prompt(`Вставте JSON пресетів (${mode}):`, lastPresetImportRaw || "") || "").trim();
    if (!raw) return;
    try {
      const preview = parsePresetPreview(raw, mode);
      lastPresetImportRaw = raw;
      lastPresetPreview = preview;
      refreshPresetMergeHint();
      const conflicts = Number(preview.summary && preview.summary.conflicts ? preview.summary.conflicts : 0);
      const drops = Number(preview.summary && preview.summary.drop ? preview.summary.drop : 0);
      if (conflicts > 0 && !window.confirm(`Виявлено конфлікти: ${conflicts}. Продовжити ${mode}?`)) {
        setStatus(`Імпорт ${mode} скасовано: конфлікти=${conflicts}`);
        return;
      }
      if (mode === "replace" && drops > 0 && !window.confirm(`Режим replace видалить ${drops} пресет(ів). Підтвердити?`)) {
        setStatus(`Імпорт replace скасовано: drop=${drops}`);
        return;
      }
      let result = {};
      if (namespace === "shared") {
        result = ui.importPresetBundle(raw, { namespace, mode });
      } else {
        result = ui.importPresets(PRESET_SCOPE, raw, { namespace, mode });
      }
      loadPresetSelect("");
      setStatus(`Імпорт ${mode} (${namespace}): імпортовано=${result.imported || 0}, всього=${result.total || 0}, конфлікти=${conflicts}`);
      refreshPresetSummary();
      refreshPresetTimelineHint();
      refreshPresetMergeHint();
      refreshPresetPolicyHint();
      refreshPresetCockpitHint();
    } catch (error) {
      if (String(error).includes("preset_protected_locked")) {
        setStatus(`Імпорт заблоковано блокування політики (${namespace}): захищені пресети`);
        refreshPresetPolicyHint();
        refreshPresetCockpitHint();
      } else {
        setStatus(`ПОМИЛКА імпорту: ${error}`);
      }
    }
  }
  function installScopeProfiles() {
    const namespace = selectedPresetNamespace();
    const result = ui.installPresetProfiles(PRESET_SCOPE, { namespace, overwrite: false });
    loadPresetSelect("");
    setStatus(`Профілі (${namespace}): додано=${result.installed}, всього=${result.total}, пропущено_захищені=${result.skipped_protected || 0}`);
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetPolicyHint();
    refreshPresetCockpitHint();
  }
  function installTeamProfilesAllScopes() {
    const namespace = selectedPresetNamespace();
    let installed = 0;
    let total = 0;
    for (const scope of TEAM_PRESET_SCOPES) {
      const result = ui.installPresetProfiles(scope, { namespace, overwrite: false });
      installed += Number(result.installed || 0);
      total += Number(result.total || 0);
    }
    loadPresetSelect("");
    setStatus(`Team-профілі (${namespace}): додано=${installed}, сумарно=${total}`);
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetPolicyHint();
    refreshPresetCockpitHint();
  }
  function cleanupPresetStore() {
    const namespace = selectedPresetNamespace();
    const daysRaw = String(window.prompt("Retention днів для пресетів:", "30") || "").trim();
    const maxRaw = String(window.prompt("Максимум пресетів у scope:", "20") || "").trim();
    const days = parseInt(daysRaw || "30", 10);
    const maxEntries = parseInt(maxRaw || "20", 10);
    const result = ui.cleanupPresets(PRESET_SCOPE, {
      namespace,
      maxAgeDays: Number.isFinite(days) ? days : 30,
      maxEntries: Number.isFinite(maxEntries) ? maxEntries : 20,
      archive: true,
    });
    loadPresetSelect("");
    setStatus(`Очищення (${namespace}): видалено=${result.removed}, залишилось=${result.kept}, архів=${result.archived_total}`);
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetPolicyHint();
    refreshPresetCockpitHint();
  }
  function showPresetMetrics() {
    const report = ui.buildPresetObservabilityBundle({ scopes: TEAM_PRESET_SCOPES });
    window.prompt("Метрики пресетів (JSON):", JSON.stringify(report, null, 2));
    refreshPresetSummary();
    refreshPresetTimelineHint();
    refreshPresetPolicyHint();
    refreshPresetCockpitHint();
    refreshPresetCockpitTimelineHint();
    refreshPresetRolloutHint();
  }
  function openFleetCommandPalette() {
    const namespace = selectedPresetNamespace();
    const presets = ui.listPresets(PRESET_SCOPE, { namespace });
    const timelineEntries = ui.listPresetTimeline(PRESET_SCOPE, { namespace, limit: 8 });
    const presetCommands = presets.map((item) => ({
      title: `Пресет: ${item.name}`,
      subtitle: `Застосувати збережений набір фільтрів (${namespace})`,
      run: () => {
        applyPresetPayload(item.data || {});
        setStatus(`Застосовано пресет: ${item.name}`);
        refresh();
      },
    }));
    const timelineCommands = timelineEntries.map((item) => ({
      title: `Журнал: ${timelineActionLabel(item.action)}`,
      subtitle: `${formatTs(item.ts)} · drill-down`,
      run: () => openPresetTimelineDetails(item),
    }));
    ui.openCommandPalette({
      title: "Команди флоту",
      commands: [
        { title: "Фокус: критичні", subtitle: "severity=bad, onlyAlerts=on", run: () => applyFocusPreset("bad") },
        { title: "Фокус: WG stale", subtitle: "code=wg_stale", run: () => applyFocusPreset("wg") },
        { title: "Фокус: черга", subtitle: "code=pending_batches_high", run: () => applyFocusPreset("queue") },
        { title: "Фокус: door stale", subtitle: "code=door_events_stale", run: () => applyFocusPreset("door_stale") },
        { title: "Скинути фільтри", subtitle: "Повернути стандартний режим", run: clearFilters },
        { title: "Зберегти поточний пресет", subtitle: "Зберегти набір фільтрів у localStorage", run: saveCurrentPreset },
        { title: "Простір: локальні", subtitle: "Переключити на локальні пресети", run: () => { document.getElementById("presetNamespace").value = "local"; loadPresetSelect(""); } },
        { title: "Простір: спільні", subtitle: "Переключити на спільний простір пресетів", run: () => { document.getElementById("presetNamespace").value = "shared"; loadPresetSelect(""); } },
        { title: "Політика: розблокувати", subtitle: "Вимкнути блокування для захищених пресетів", run: unlockPresetPolicy },
        { title: "Політика: заблокувати", subtitle: "Увімкнути блокування для захищених пресетів", run: lockPresetPolicy },
        { title: "Cockpit: попередній перегляд", subtitle: "Пакетний попередній перегляд по scope", run: () => previewPresetCockpit("merge") },
        { title: "Cockpit: apply merge", subtitle: "Пакетне застосування merge по scope", run: () => applyPresetCockpit("merge") },
        { title: "Cockpit: apply replace", subtitle: "Пакетне застосування replace по scope", run: () => applyPresetCockpit("replace") },
        { title: "Cockpit: панель таймлайна", subtitle: "Фільтри scope/action/namespace", run: showPresetCockpitTimelinePanel },
        { title: "Розгортання: assistant merge", subtitle: "Безпечний протокол застосування (merge)", run: () => runPresetRolloutAssistant("merge") },
        { title: "Розгортання: assistant replace", subtitle: "Безпечний протокол застосування (replace)", run: () => runPresetRolloutAssistant("replace") },
        { title: "Розгортання: останній summary", subtitle: "Останній результат розгортання", run: showLastPresetRolloutSummary },
        { title: "Cockpit: policy unlock batch", subtitle: "Пакетне розблокування для scope", run: () => setPresetCockpitLockBatch(false) },
        { title: "Cockpit: блокування політики batch", subtitle: "Пакетне блокування для scope", run: () => setPresetCockpitLockBatch(true) },
        { title: "Експорт пресетів", subtitle: "Вивантажити JSON у буфер/діалог", run: exportPresetData },
        { title: "Попередній перегляд merge", subtitle: "Симуляція merge без запису", run: () => previewPresetImport("merge") },
        { title: "Імпорт merge", subtitle: "Застосувати merge імпорт", run: () => importPresetData("merge") },
        { title: "Імпорт replace", subtitle: "Застосувати replace імпорт", run: () => importPresetData("replace") },
        { title: "Встановити профілі scope", subtitle: "Додати стандартні профілі для поточної сторінки", run: installScopeProfiles },
        { title: "Встановити team-профілі", subtitle: "Додати стандартні профілі для fleet/alerts/incidents", run: installTeamProfilesAllScopes },
        { title: "Cleanup пресетів", subtitle: "Retention + архівування старих пресетів", run: cleanupPresetStore },
        { title: "Метрики пресетів", subtitle: "Показати summary namespace/scope", run: showPresetMetrics },
        { title: "Журнал пресетів", subtitle: "Показати timeline scope/team", run: showPresetTimeline },
        { title: "Очистити журнал пресетів", subtitle: "Очистити timeline поточного scope", run: clearPresetTimelineEntries },
        ...timelineCommands,
        ...presetCommands,
      ],
    });
  }
  function applyWorkspaceContext() {
    const context = ui.loadWorkspaceContext({ maxAgeSec: 3 * 24 * 3600 });
    if (!context) {
      setStatus("Контекст не знайдено або застарів");
      refreshWorkspaceHint();
      return;
    }
    if (context.central_id) document.getElementById("alertCentral").value = context.central_id;
    if (context.code) document.getElementById("alertCode").value = context.code;
    refreshWorkspaceHint();
    syncQueryFromFilters();
    refresh();
  }
  function clearFilters() {
    document.getElementById("q").value = "";
    document.getElementById("alertCentral").value = "";
    document.getElementById("alertCode").value = "";
    document.getElementById("sev").value = "all";
    document.getElementById("includeSilenced").checked = false;
    document.getElementById("onlyAlerts").checked = false;
    applyFocusPreset("reset");
  }
  function boolFromQuery(value, fallback = false) {
    if (value === null || value === undefined) return !!fallback;
    const normalized = String(value).trim().toLowerCase();
    if (!normalized) return !!fallback;
    if (normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on") return true;
    if (normalized === "0" || normalized === "false" || normalized === "no" || normalized === "off") return false;
    return !!fallback;
  }
  function applyFiltersFromQuery() {
    const params = new URLSearchParams(window.location.search);
    const q = params.get("q");
    if (q !== null) document.getElementById("q").value = String(q);
    const central = params.get("central") || params.get("central_id");
    if (central !== null) document.getElementById("alertCentral").value = String(central);
    const code = params.get("code");
    if (code !== null) document.getElementById("alertCode").value = String(code);
    const sev = String(params.get("sev") || params.get("severity") || "").trim().toLowerCase();
    if (sev === "all" || sev === "good" || sev === "warn" || sev === "bad") document.getElementById("sev").value = sev;
    const opsWindow = String(params.get("ops_window") || params.get("opsWindow") || params.get("window") || "").trim().toLowerCase();
    if (opsWindow) {
      const allowed = new Set(["1h", "6h", "24h", "7d"]);
      if (allowed.has(opsWindow)) document.getElementById("opsWindow").value = opsWindow;
    }
    const includeSilenced = params.get("include_silenced") ?? params.get("includeSilenced");
    if (includeSilenced !== null) document.getElementById("includeSilenced").checked = boolFromQuery(includeSilenced, false);
    const onlyAlerts = params.get("only_alerts") ?? params.get("onlyAlerts");
    if (onlyAlerts !== null) document.getElementById("onlyAlerts").checked = boolFromQuery(onlyAlerts, false);
  }
  function syncQueryFromFilters() {
    const params = new URLSearchParams();
    const q = String(document.getElementById("q").value || "").trim();
    const central = String(document.getElementById("alertCentral").value || "").trim();
    const code = String(document.getElementById("alertCode").value || "").trim();
    const sev = selectedSeverity();
    const opsWindow = selectedOpsWindow();
    const includeSilenced = !!document.getElementById("includeSilenced").checked;
    const onlyAlerts = !!document.getElementById("onlyAlerts").checked;
    if (q) params.set("q", q);
    if (central) params.set("central_id", central);
    if (code) params.set("code", code);
    if (sev && sev !== "all") params.set("severity", sev);
    if (opsWindow && opsWindow !== "24h") params.set("ops_window", opsWindow);
    if (includeSilenced) params.set("include_silenced", "1");
    if (onlyAlerts) params.set("only_alerts", "1");
    const qs = params.toString();
    const next = qs ? `${window.location.pathname}?${qs}` : window.location.pathname;
    const current = `${window.location.pathname}${window.location.search}`;
    if (next !== current) window.history.replaceState({}, "", next);
  }
  function syncFilterSummary() {
    const parts = [];
    const q = String(document.getElementById("q").value || "").trim();
    const central = String(document.getElementById("alertCentral").value || "").trim();
    const code = String(document.getElementById("alertCode").value || "").trim();
    const sev = selectedSeverity();
    const opsWindow = selectedOpsWindow();
    const includeSilenced = !!document.getElementById("includeSilenced").checked;
    const onlyAlerts = !!document.getElementById("onlyAlerts").checked;
    if (q) parts.push(`q=${q}`);
    if (central) parts.push(`вузол=${central}`);
    if (code) parts.push(`код=${code}`);
    if (sev && sev !== "all") parts.push(`рівень=${sev}`);
    if (opsWindow && opsWindow !== "24h") parts.push(`стрічка=${opsWindow}`);
    if (includeSilenced) parts.push("+заглушені");
    if (onlyAlerts) parts.push("лише з алертами");
    const node = document.getElementById("filterSummary");
    if (!node) return;
    node.textContent = parts.length ? `фільтри: ${parts.join(" · ")}` : "фільтри: стандартні";
  }
  function setFocusState(level, text) {
    const node = document.getElementById("fleetFocusState");
    node.className = `focusState ${level}`;
    node.textContent = text;
  }
  function setFocusButtonState(id, active) {
    const element = document.getElementById(id);
    if (!element) return;
    if (active) element.classList.add("active");
    else element.classList.remove("active");
  }
  function syncFocusButtons() {
    const sevFilter = selectedSeverity();
    const codeFilter = alertCode().toLowerCase();
    const onlyAlerts = !!document.getElementById("onlyAlerts").checked;
    setFocusButtonState("focusBad", sevFilter === "bad" && onlyAlerts && !codeFilter);
    setFocusButtonState("focusWg", codeFilter === "wg_stale");
    setFocusButtonState("focusQueue", codeFilter === "pending_batches_high");
    setFocusButtonState("focusDoorStale", codeFilter === "door_events_stale");
    setFocusButtonState("focusReset", sevFilter === "all" && !onlyAlerts && !codeFilter);
  }
  function applyFocusPreset(mode) {
    const sev = document.getElementById("sev");
    const code = document.getElementById("alertCode");
    const onlyAlerts = document.getElementById("onlyAlerts");
    if (mode === "bad") {
      sev.value = "bad";
      code.value = "";
      onlyAlerts.checked = true;
    } else if (mode === "wg") {
      sev.value = "all";
      code.value = "wg_stale";
      onlyAlerts.checked = true;
    } else if (mode === "queue") {
      sev.value = "all";
      code.value = "pending_batches_high";
      onlyAlerts.checked = true;
    } else if (mode === "door_stale") {
      sev.value = "all";
      code.value = "door_events_stale";
      onlyAlerts.checked = true;
    } else {
      sev.value = "all";
      code.value = "";
      onlyAlerts.checked = false;
    }
    syncQueryFromFilters();
    refresh();
  }
  function sevClass(level, fallbackAgeSec) {
    if (level === "good" || level === "warn" || level === "bad") return level;
    if (fallbackAgeSec === null || fallbackAgeSec === undefined) return "bad";
    if (fallbackAgeSec <= 75) return "good";
    if (fallbackAgeSec <= 240) return "warn";
    return "bad";
  }
  function badgeClass(level) {
    const normalized = String(level || "").toLowerCase();
    if (normalized === "good" || normalized === "warn" || normalized === "bad") return normalized;
    return "bad";
  }
  function incidentKey(centralId, code) {
    return `${String(centralId || "").toLowerCase()}::${String(code || "").toLowerCase()}`;
  }
  function isActiveIncidentStatus(status) {
    const normalized = String(status || "").toLowerCase();
    return normalized === "open" || normalized === "acked" || normalized === "silenced";
  }
  function buildIncidentIndex(incidents) {
    const index = new Map();
    for (const item of Array.isArray(incidents) ? incidents : []) {
      index.set(incidentKey(item.central_id, item.code), item);
    }
    return index;
  }
  function slaTimerHtml(incident) {
    if (!incident) return '<span class="badge">немає</span>';
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
  function matches(item, q) {
    if (!q) return true;
    const serviceText = Object.entries(item.services || {}).map(([k,v]) => `${k}:${v}`).join(" ");
    const doorsText = (item.doors || []).map(d => `${d.node_id || ""} ${d.door_id || ""} ${d.last_event_age_sec || ""}`).join(" ");
    const alertsText = (item.alerts || []).map(a => `${a.code || ""} ${a.message || ""}`).join(" ");
    const hay = [
      item.central_id || "",
      item.vehicle_id || "",
      item.time_sync || "",
      serviceText,
      doorsText,
      alertsText,
    ].join(" ").toLowerCase();
    return hay.includes(q);
  }
  async function apiPost(path, payload) {
    return ui.apiPost(path, payload);
  }
  async function ackAlert(centralId, code) {
    if (!canOperate()) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    const actor = "admin-ui";
    const result = await ui.runActionWithLatency(() =>
      apiPost("/api/admin/fleet/alerts/ack", { central_id: centralId, code, actor, note: "підтверджено з /admin/fleet" })
    );
    if (!result.ok) { setStatus(`ПОМИЛКА підтвердження (${ui.formatLatency(result.elapsed_ms)}): ${result.error}`); return; }
    saveWorkspaceContext(centralId, code, "fleet/ack");
    await refresh();
    setStatus(`ПІДТВЕРДЖЕНО: ${centralId}:${code} · ${ui.formatLatency(result.elapsed_ms)}`);
  }
  async function silenceAlert(centralId, code, durationSec) {
    if (!canOperate()) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    const actor = "admin-ui";
    const result = await ui.runActionWithLatency(() =>
      apiPost("/api/admin/fleet/alerts/silence", { central_id: centralId, code, duration_sec: durationSec, actor, note: `заглушено на ${durationSec}с з /admin/fleet` })
    );
    if (!result.ok) { setStatus(`ПОМИЛКА заглушення (${ui.formatLatency(result.elapsed_ms)}): ${result.error}`); return; }
    saveWorkspaceContext(centralId, code, "fleet/silence");
    await refresh();
    setStatus(`ЗАГЛУШЕНО: ${centralId}:${code} · ${ui.formatLatency(result.elapsed_ms)}`);
  }
  async function unsilenceAlert(centralId, code) {
    if (!canOperate()) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    const actor = "admin-ui";
    const result = await ui.runActionWithLatency(() =>
      apiPost("/api/admin/fleet/alerts/unsilence", { central_id: centralId, code, actor, note: "знято заглушення з /admin/fleet" })
    );
    if (!result.ok) { setStatus(`ПОМИЛКА зняття заглушення (${ui.formatLatency(result.elapsed_ms)}): ${result.error}`); return; }
    saveWorkspaceContext(centralId, code, "fleet/unsilence");
    await refresh();
    setStatus(`ЗНЯТО ЗАГЛУШЕННЯ: ${centralId}:${code} · ${ui.formatLatency(result.elapsed_ms)}`);
  }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const q = query();
      const alertCentralFilter = alertCentral();
      const alertCodeFilter = alertCode();
      const sevFilter = selectedSeverity();
      const includeSilenced = !!document.getElementById("includeSilenced").checked;
      const onlyAlerts = !!document.getElementById("onlyAlerts").checked;
      const overviewUrl = `/api/admin/fleet/overview?include_centrals=1&limit=200&include_silenced=${includeSilenced ? "1" : "0"}`;
      const currentResp = await fetch(overviewUrl);
      const currentText = await currentResp.text();
      if (!currentResp.ok) throw new Error(`${currentResp.status} ${currentText}`);
      const currentData = JSON.parse(currentText);
      const centrals = Array.isArray(currentData.centrals) ? currentData.centrals : [];
      const totals = currentData.totals || {};
      const alertsParams = new URLSearchParams();
      alertsParams.set("limit", "500");
      alertsParams.set("include_silenced", includeSilenced ? "1" : "0");
      if (sevFilter !== "all") alertsParams.set("severity", sevFilter);
      if (q) alertsParams.set("q", q);
      if (alertCentralFilter) alertsParams.set("central_id", alertCentralFilter);
      if (alertCodeFilter) alertsParams.set("code", alertCodeFilter);
      const alertsResp = await fetch(`/api/admin/fleet/alerts?${alertsParams.toString()}`);
      const alertsText = await alertsResp.text();
      if (!alertsResp.ok) throw new Error(`${alertsResp.status} ${alertsText}`);
      const alertsData = JSON.parse(alertsText);
      const summaryAlerts = Array.isArray(alertsData.alerts) ? alertsData.alerts : [];
      const incidentsParams = new URLSearchParams();
      incidentsParams.set("limit", "1500");
      incidentsParams.set("include_resolved", "0");
      if (q) incidentsParams.set("q", q);
      if (alertCentralFilter) incidentsParams.set("central_id", alertCentralFilter);
      if (alertCodeFilter) incidentsParams.set("code", alertCodeFilter);
      const incidentsResp = await fetch(`/api/admin/fleet/incidents?${incidentsParams.toString()}`);
      const incidentsText = await incidentsResp.text();
      if (!incidentsResp.ok) throw new Error(`${incidentsResp.status} ${incidentsText}`);
      const incidentsData = JSON.parse(incidentsText);
      const activeIncidents = (Array.isArray(incidentsData.incidents) ? incidentsData.incidents : []).filter((item) => isActiveIncidentStatus(item.status));
      const incidentsIndex = buildIncidentIndex(activeIncidents);
      const opsWindow = selectedOpsWindow();
      const opsParams = new URLSearchParams();
      opsParams.set("window", opsWindow);
      opsParams.set("limit", "80");
      opsParams.set("include_resolved", "0");
      opsParams.set("include_silenced", includeSilenced ? "1" : "0");
      if (q) opsParams.set("q", q);
      if (alertCentralFilter) opsParams.set("central_id", alertCentralFilter);
      if (alertCodeFilter) opsParams.set("code", alertCodeFilter);
      if (sevFilter !== "all") opsParams.set("severity", sevFilter);
      const opsResp = await fetch(`/api/admin/fleet/ops-feed?${opsParams.toString()}`);
      const opsText = await opsResp.text();
      if (!opsResp.ok) throw new Error(`${opsResp.status} ${opsText}`);
      const opsData = JSON.parse(opsText);
      renderOpsFeed(opsData);
      const tbody = document.querySelector("#tbl tbody");
      tbody.innerHTML = "";
      centrals.sort((a, b) => (a.central_id || "").localeCompare(b.central_id || ""));
      let shown = 0;
      for (const c of centrals) {
        if (alertCentralFilter && String(c.central_id || "") !== alertCentralFilter) continue;
        if (!matches(c, q)) continue;
        const alerts = Array.isArray(c.alerts) ? c.alerts : [];
        if (alertCodeFilter && !alerts.some((a) => String(a.code || "") === alertCodeFilter)) continue;
        const alertsVisible = includeSilenced ? alerts : alerts.filter((a) => !a.silenced);
        if (onlyAlerts && alertsVisible.length === 0) continue;
        const cls = sevClass(c.health?.severity, c.age_sec);
        if (sevFilter !== "all" && cls !== sevFilter) continue;
        shown += 1;
        const services = c.services || {};
        const queue = c.queue || {};
        const doors = Array.isArray(c.doors) ? c.doors : [];
        const gps = c.gps || null;
        const servicesHtml = Object.entries(services)
          .map(([k,v]) => `<li><code>${esc(k)}</code>: <code>${esc(v)}</code></li>`)
          .join("");
        const queueHtml = [
          `<li>подій_всього: <code>${esc(queue.events_total)}</code></li>`,
          `<li>пакетів_у_черзі: <code>${esc(queue.pending_batches)}</code></li>`,
          `<li>вік_найстаршого_в_черзі: <code>${fmtAge(queue.pending_oldest_age_sec)}</code></li>`,
          `<li>надіслано_пакетів: <code>${esc(queue.sent_batches)}</code></li>`,
          `<li>wg_рукостискання: <code>${fmtAge(queue.wg_latest_handshake_age_sec)}</code></li>`,
          `<li>час_останньої_події: <code>${esc(queue.last_event_ts_received || "—")}</code></li>`,
        ].join("");
        const doorsHtml = doors.length
          ? doors.map((d) => `<li><code>${esc(d.node_id || "?")}</code> door=<code>${esc(d.door_id || "?")}</code> age=<code>${fmtAge(d.last_event_age_sec)}</code></li>`).join("")
          : `<li>—</li>`;
        const alertsHtml = alertsVisible.length
          ? alertsVisible.slice(0, 5).map((a) => {
            const badges = [
              `<span class="badge ${esc(a.severity || "bad")}">${esc(sevLabel(a.severity || "bad"))}</span>`,
              a.silenced ? '<span class="badge warn">ЗАГЛУШЕНО</span>' : "",
              a.acked_at ? '<span class="badge good">ПІДТВЕРДЖЕНО</span>' : "",
            ].join(" ");
            return `<li>${badges} <code>${esc(a.code || "alert")}</code> ${esc(a.message || "")}</li>`;
          }).join("")
          : `<li><span class="badge good">OK</span></li>`;
        const tr = document.createElement("tr");
        const centralId = String(c.central_id || "");
        const centralHref = `/admin/fleet/central/${encodeURIComponent(centralId)}`;
        const incidentsHref = `/admin/fleet/incidents?central=${encodeURIComponent(centralId)}`;
        tr.innerHTML = `
          <td><span class="pill ${cls}"><span class="dot"></span>${sevLabel(cls)}</span></td>
          <td><a href="${centralHref}"><code>${esc(c.central_id)}</code></a></td>
          <td><code>${esc(c.vehicle_id || "—")}</code></td>
          <td>${fmtAge(c.age_sec)}<div class="muted"><code>${esc(c.ts_received || "—")}</code></div></td>
          <td><ul class="kvs">${alertsHtml}</ul></td>
          <td><code>${esc(c.time_sync || "невідомо")}</code></td>
          <td>${gpsCellHtml(gps)}</td>
          <td><ul class="kvs">${servicesHtml || "<li>—</li>"}</ul></td>
          <td><ul class="kvs">${queueHtml}</ul></td>
          <td><ul class="kvs">${doorsHtml}</ul></td>
          <td>
            <div class="drillBtns">
              <a class="drillBtn" href="${centralHref}">Вузол</a>
              <a class="drillBtn" data-workspace-central="1" href="${incidentsHref}">Інциденти</a>
            </div>
          </td>
        `;
        tr.querySelector('a[data-workspace-central="1"]')?.addEventListener("click", () => {
          saveWorkspaceContext(centralId, "", "fleet/central");
        });
        tbody.appendChild(tr);
      }
      document.getElementById("sumTotal").textContent = `центральних вузлів: ${totals.centrals ?? centrals.length}`;
      document.getElementById("sumGood").textContent = `справні: ${totals.good ?? 0}`;
      document.getElementById("sumWarn").textContent = `попередження: ${totals.warn ?? 0}`;
      document.getElementById("sumBad").textContent = `критичні: ${totals.bad ?? 0}`;
      document.getElementById("sumAlerts").textContent = `алерти: ${alertsData.total ?? summaryAlerts.length}`;
      document.getElementById("sumSilenced").textContent = `заглушені: ${totals.alerts_silenced ?? 0}`;
      document.getElementById("sumPending").textContent = `у черзі: ${totals.pending_batches_total ?? 0}`;
      document.getElementById("sumWg").textContent = `застарілий WG: ${totals.centrals_wg_stale ?? 0}`;
      document.getElementById("sumDoors").textContent = `недоступні двері: ${totals.doors_unreachable ?? 0}`;
      document.getElementById("updatedAt").textContent = `оновлено: ${currentData.ts_generated || alertsData.ts_generated || "—"}`;
      const slaBreached = activeIncidents.filter((item) => !!item.sla_breached).length;
      document.getElementById("prioBadNodes").textContent = String(totals.bad ?? 0);
      document.getElementById("prioWgNodes").textContent = String(totals.centrals_wg_stale ?? 0);
      document.getElementById("prioQueueNodes").textContent = String(totals.centrals_with_pending ?? 0);
      document.getElementById("prioSlaBreached").textContent = String(slaBreached);
      const focusParts = [];
      if (sevFilter !== "all") focusParts.push(`рівень=${sevFilter}`);
      if (alertCentralFilter) focusParts.push(`вузол=${alertCentralFilter}`);
      if (alertCodeFilter) focusParts.push(`код=${alertCodeFilter}`);
      if (onlyAlerts) focusParts.push("лише з алертами");
      if (includeSilenced) focusParts.push("включено заглушені");
      let focusLevel = "good";
      if (sevFilter === "bad" || alertCodeFilter === "wg_stale" || alertCodeFilter === "door_events_stale" || alertCodeFilter === "pending_batches_high") {
        focusLevel = "bad";
      } else if (sevFilter === "warn" || onlyAlerts || !!alertCentralFilter || !!alertCodeFilter) {
        focusLevel = "warn";
      }
      setFocusState(focusLevel, focusParts.length ? `Фільтри: ${focusParts.join(" · ")}` : "Фільтри: стандартний режим");
      syncFocusButtons();

      const alertsBody = document.querySelector("#alertsTbl tbody");
      alertsBody.innerHTML = "";
      if (summaryAlerts.length === 0) {
        const tr = document.createElement("tr");
        tr.innerHTML = '<td colspan="10"><span class="badge good">OK</span> Немає активних алертів</td>';
        alertsBody.appendChild(tr);
      } else {
        for (const alert of summaryAlerts) {
          const tr = document.createElement("tr");
          const sev = badgeClass(alert.severity);
          const centralId = String(alert.central_id || "");
          const code = String(alert.code || "alert");
          const incidentHref = `/admin/fleet/incidents/${encodeURIComponent(centralId)}/${encodeURIComponent(code)}`;
          const incident = incidentsIndex.get(incidentKey(centralId, code));
          const isSilenced = !!alert.silenced;
          const stateParts = [];
          if (isSilenced) stateParts.push(`<span class="badge warn">заглушено</span>`);
          if (alert.acked_at) stateParts.push(`<span class="badge good">підтверджено</span>`);
          if (stateParts.length === 0) stateParts.push('<span class="badge">відкрито</span>');
          const actionDisabled = canOperate() ? "" : "disabled";
          tr.innerHTML = `
            <td><span class="badge ${sev}">${esc(sevLabel(sev))}</span></td>
            <td><a href="/admin/fleet/central/${encodeURIComponent(centralId)}"><code>${esc(centralId || "—")}</code></a></td>
            <td><code>${esc(alert.vehicle_id || "—")}</code></td>
            <td><a data-workspace-incident-code="1" href="${incidentHref}"><code>${esc(code)}</code></a></td>
            <td>${esc(alert.message || "")}</td>
            <td><code>${fmtAge(alert.age_sec)}</code></td>
            <td>${slaTimerHtml(incident)}</td>
            <td>${stateParts.join(" ")}</td>
            <td>
              <div class="actions">
                <button class="smallbtn opAction opActionAck" data-action="ack" ${actionDisabled}>Підтвердити</button>
                <button class="smallbtn opAction opActionSilence" data-action="silence" ${actionDisabled}>Пауза 1 год</button>
                <button class="smallbtn opAction opActionUnsilence" data-action="unsilence" ${actionDisabled}>Зняти заглушення</button>
              </div>
            </td>
            <td>
              <div class="drillBtns">
                <a class="drillBtn" href="/admin/fleet/central/${encodeURIComponent(centralId)}">Вузол</a>
                <a class="drillBtn" data-workspace-incident-link="1" href="${incidentHref}">Інцидент</a>
              </div>
            </td>
          `;
          tr.querySelector('a[data-workspace-incident-code="1"]')?.addEventListener("click", () => saveWorkspaceContext(centralId, code, "fleet/alerts"));
          tr.querySelector('a[data-workspace-incident-link="1"]')?.addEventListener("click", () => saveWorkspaceContext(centralId, code, "fleet/alerts"));
          tr.querySelector('button[data-action="ack"]')?.addEventListener("click", () => ackAlert(centralId, code));
          tr.querySelector('button[data-action="silence"]')?.addEventListener("click", () => silenceAlert(centralId, code, 3600));
          tr.querySelector('button[data-action="unsilence"]')?.addEventListener("click", () => unsilenceAlert(centralId, code));
          alertsBody.appendChild(tr);
        }
      }
      const centralFilterState = alertCentralFilter ? `, вузол=${alertCentralFilter}` : "";
      const codeFilterState = alertCodeFilter ? `, код=${alertCodeFilter}` : "";
      setStatus(`OK: вузлів=${centrals.length}, показано=${shown}, алертів=${summaryAlerts.length}, активних_інцидентів=${activeIncidents.length}, ops_window=${opsWindow}${centralFilterState}${codeFilterState}`);
    } catch (e) {
      setStatus("ПОМИЛКА: " + e);
    }
  }

  document.getElementById("refresh").addEventListener("click", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  document.getElementById("q").addEventListener("input", scheduleRefresh);
  document.getElementById("alertCentral").addEventListener("input", scheduleRefresh);
  document.getElementById("alertCode").addEventListener("input", scheduleRefresh);
  document.getElementById("sev").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("opsWindow").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("includeSilenced").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("onlyAlerts").addEventListener("change", () => { syncQueryFromFilters(); syncFilterSummary(); refresh(); });
  document.getElementById("clearFilters").addEventListener("click", () => { clearFilters(); syncQueryFromFilters(); syncFilterSummary(); });
  document.getElementById("focusBad").addEventListener("click", () => applyFocusPreset("bad"));
  document.getElementById("focusWg").addEventListener("click", () => applyFocusPreset("wg"));
  document.getElementById("focusQueue").addEventListener("click", () => applyFocusPreset("queue"));
  document.getElementById("focusDoorStale").addEventListener("click", () => applyFocusPreset("door_stale"));
  document.getElementById("focusReset").addEventListener("click", () => applyFocusPreset("reset"));
  document.getElementById("workspaceApply").addEventListener("click", applyWorkspaceContext);
  document.getElementById("workspaceClear").addEventListener("click", () => { ui.clearWorkspaceContext(); refreshWorkspaceHint(); });
  document.getElementById("cmdPaletteOpen").addEventListener("click", openFleetCommandPalette);
  document.getElementById("presetNamespace").addEventListener("change", () => loadPresetSelect(""));
  document.getElementById("presetSave").addEventListener("click", saveCurrentPreset);
  document.getElementById("presetApply").addEventListener("click", applySelectedPreset);
  document.getElementById("presetDelete").addEventListener("click", deleteSelectedPreset);
  document.getElementById("presetExport").addEventListener("click", exportPresetData);
  document.getElementById("presetPreview").addEventListener("click", () => previewPresetImport("merge"));
  document.getElementById("presetImport").addEventListener("click", () => importPresetData("merge"));
  document.getElementById("presetCockpit").addEventListener("click", () => previewPresetCockpit("merge"));
  document.getElementById("presetCockpitTimeline").addEventListener("click", showPresetCockpitTimelinePanel);
  document.getElementById("presetRollout").addEventListener("click", () => runPresetRolloutAssistant("merge"));
  document.getElementById("presetMetrics").addEventListener("click", showPresetMetrics);
  document.getElementById("presetTimelineOpen").addEventListener("click", showPresetTimeline);
  document.getElementById("presetTimelineClear").addEventListener("click", clearPresetTimelineEntries);
  document.getElementById("presetPolicyUnlock").addEventListener("click", unlockPresetPolicy);
  document.getElementById("presetPolicyLock").addEventListener("click", lockPresetPolicy);
  document.getElementById("presetProfiles").addEventListener("click", installScopeProfiles);
  document.getElementById("presetCleanup").addEventListener("click", cleanupPresetStore);
  ui.bindEnterRefresh(["q", "alertCentral", "alertCode"], () => { syncQueryFromFilters(); refresh(); });
  ui.bindCommandPalette(openFleetCommandPalette);
  const densityMode = ui.initDensityMode("density", {
    storageKey: "fleet_density",
    className: "density-compact",
    onChange: syncDensityBadge,
  });
  syncDensityBadge(densityMode);
  applyFiltersFromQuery();
  syncQueryFromFilters();
  syncFilterSummary();
  refreshWorkspaceHint();
  initFleetSecondaryDetails();
  initFleetToolsDetails();
  loadPresetSelect("");
  refreshPresetSummary();
  refreshPresetTimelineHint();
  refreshPresetMergeHint();
  refreshPresetPolicyHint();
  refreshPresetCockpitHint();
  refreshPresetCockpitTimelineHint();
  refreshPresetRolloutHint();
  loadWhoami().then(refresh);
  setInterval(() => { if (ui.byId("auto").checked) refresh(); }, 10000);
""".strip()
    return render_admin_shell(
        title='Адмін-панель Passengers — Флот',
        header_title='Моніторинг флоту',
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        max_width=1340,
        extra_css=extra_css,
        current_nav="fleet",
    )
