from __future__ import annotations

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_notifications_page() -> str:
    chips_html = """
        <span class="chip">пауза / ліміти / ескалація</span>
        <span class="chip mono" id="whoamiBadge">роль: —</span>
        <span class="chip mono" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
      <div class="toolbarMain">
        <button id="copyLink" title="Скопіювати посилання на сторінку налаштувань">Скопіювати посилання</button>
      </div>
      <div class="toolbarMeta">
        <span class="metaChip sort" id="filterSummary">контекст: глобальні правила сповіщень</span>
      </div>
    """
    body_html = """
    <div class="card">
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code>/api/admin/fleet/notification-settings</code></span>
        <span class="metaChip sort">контур: <code>глобальні правила</code></span>
      </div>
      <div class="summary">
        <span class="badge bad">КРИТИЧНО (bad)</span>
        <span class="badge warn">ПОПЕРЕДЖЕННЯ (warn)</span>
        <span class="badge good">СПРАВНО (good)</span>
      </div>
      <div class="row">
        <label for="notifyTelegram">Надсилати в Telegram</label>
        <input id="notifyTelegram" type="checkbox" />
      </div>
      <div class="row">
        <label for="notifyEmail">Надсилати на Email</label>
        <input id="notifyEmail" type="checkbox" />
      </div>
      <div class="row">
        <label for="minSeverity">Мінімальний рівень сповіщень</label>
        <select id="minSeverity">
          <option value="bad">критичні (bad)</option>
          <option value="warn">попередження (warn)</option>
          <option value="good">усі події (good)</option>
        </select>
      </div>
      <div class="row">
        <label for="staleAlways">Сповіщати про stale завжди</label>
        <input id="staleAlways" type="checkbox" />
      </div>
      <div class="row">
        <label for="rateLimit">Антифлуд (сек)</label>
        <input id="rateLimit" type="number" min="30" max="86400" />
      </div>
      <div class="row">
        <label for="escalationSec">Ескалація через (сек)</label>
        <input id="escalationSec" type="number" min="60" max="604800" />
      </div>
      <div class="row">
        <label for="muteUntil">Пауза сповіщень до (ISO UTC)</label>
        <input id="muteUntil" type="text" placeholder="2026-02-07T20:00:00Z" />
      </div>
      <div class="toolbar uJcStart uMt12">
        <button id="refresh">Оновити</button>
        <button id="save" class="primary">Зберегти</button>
        <button id="clearMute">Скинути паузу</button>
      </div>
      <div class="status" id="status"></div>
    </div>

    <details id="notificationsSecondaryDetails" class="domainSplitDetails uMt14" data-advanced-details="1">
      <summary>Тестова доставка (вторинний сценарій)</summary>
      <div class="domainSplitHint">
        Використовуйте цей блок для перевірки каналу доставки та запису у delivery-журнал. Для операційного triage використовуйте <a class="quickLink" href="/admin/fleet/notify-center">центр доставки</a>.
      </div>
      <div class="card">
        <div class="sectionHead">
          <div>
            <div class="sectionTitle">Надіслати тестове сповіщення</div>
            <div class="muted"><code>/api/admin/fleet/notification-settings/test</code></div>
          </div>
        </div>
        <div class="tableMeta">
          <span class="metaChip source">джерело: <code>/api/admin/fleet/notification-settings/test</code></span>
          <span class="metaChip mode">роль: <code>operator</code></span>
        </div>
        <div class="row">
          <label for="testCentral">ID вузла</label>
          <input id="testCentral" type="text" value="central-gw" />
        </div>
        <div class="row">
          <label for="testCode">Код події</label>
          <input id="testCode" type="text" value="test_notification" />
        </div>
        <div class="row">
          <label for="testSeverity">Рівень події</label>
          <select id="testSeverity">
            <option value="bad">критично (bad)</option>
            <option value="warn" selected>попередження (warn)</option>
            <option value="good">інфо (good)</option>
          </select>
        </div>
        <div class="row">
          <label for="testChannel">Канал доставки</label>
          <select id="testChannel">
            <option value="auto" selected>автовибір</option>
            <option value="telegram">Telegram</option>
            <option value="email">Email</option>
            <option value="all">усі канали</option>
          </select>
        </div>
        <div class="row">
          <label for="testMessage">Текст повідомлення</label>
          <input id="testMessage" type="text" value="ручне тестове сповіщення з адмін-панелі" />
        </div>
        <div class="row">
          <label for="testDryRun">Dry-run (без відправки)</label>
          <input id="testDryRun" type="checkbox" />
        </div>
        <div class="toolbar uJcStart uMt12">
          <button id="testSend" class="primary">Надіслати тест</button>
          <button id="healthTest">Надіслати тест health флоту</button>
        </div>
        <div class="status" id="testStatus"></div>
      </div>
    </details>
    """
    script = """
  const ui = window.AdminUiKit;
  const NOTIFICATIONS_SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_notifications_secondary_details_v1";
  let adminRole = "viewer";
  let adminCaps = { read: true, operate: false, admin: false };
  function setStatus(s) { ui.setStatus("status", s); }
  function setTestStatus(s) { ui.setStatus("testStatus", s); }
  function setDisabled(id, disabled) { ui.setDisabled(id, disabled); }
  function initNotificationsSecondaryDetails() {
    const node = document.getElementById("notificationsSecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {
      const raw = String(localStorage.getItem(NOTIFICATIONS_SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    } catch (_error) {}
    node.addEventListener("toggle", () => {
      try { localStorage.setItem(NOTIFICATIONS_SECONDARY_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); } catch (_error) {}
    });
  }
  function syncFilterSummary() {
    const node = document.getElementById("filterSummary");
    if (!node) return;
    node.textContent = "контекст: глобальні правила сповіщень";
  }
  function applyRoleUi() {
    ui.setText("whoamiBadge", `роль: ${adminRole}`);
    const adminOnlyIds = [
      "notifyTelegram", "notifyEmail", "minSeverity", "staleAlways",
      "rateLimit", "escalationSec", "muteUntil", "save", "clearMute"
    ];
    for (const id of adminOnlyIds) setDisabled(id, !adminCaps.admin);
    const operatorOnlyIds = ["testCentral", "testCode", "testSeverity", "testChannel", "testMessage", "testDryRun", "testSend"];
    for (const id of operatorOnlyIds) setDisabled(id, !adminCaps.operate);
  }
  async function loadWhoami() {
    const data = await ui.loadWhoami();
    adminRole = data.role;
    adminCaps = data.capabilities || { read: true, operate: false, admin: false };
    applyRoleUi();
  }
  async function apiGet(path) { return ui.apiGet(path); }
  async function apiPost(path, payload) { return ui.apiPost(path, payload); }
  function toInt(id, fallback) { return ui.intVal(id, fallback); }
  function severityLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "good") return "СПРАВНО";
    if (normalized === "warn") return "ПОПЕРЕДЖЕННЯ";
    if (normalized === "bad") return "КРИТИЧНО";
    return "НЕВІДОМО";
  }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const data = await apiGet("/api/admin/fleet/notification-settings");
      const settings = data.settings || {};
      document.getElementById("notifyTelegram").checked = !!settings.notify_telegram;
      document.getElementById("notifyEmail").checked = !!settings.notify_email;
      document.getElementById("minSeverity").value = settings.min_severity || "bad";
      document.getElementById("staleAlways").checked = !!settings.stale_always_notify;
      document.getElementById("rateLimit").value = settings.rate_limit_sec ?? 300;
      document.getElementById("escalationSec").value = settings.escalation_sec ?? 1800;
      document.getElementById("muteUntil").value = settings.mute_until || "";
      ui.setText("updatedAt", `оновлено: ${data.ts_generated || "—"}`);
      setStatus("OK");
    } catch (error) {
      setStatus("ПОМИЛКА: " + error);
    }
  }
  async function save() {
    if (!adminCaps.admin) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль admin"); return; }
    setStatus("Збереження...");
    try {
      const payload = {
        notify_telegram: !!document.getElementById("notifyTelegram").checked,
        notify_email: !!document.getElementById("notifyEmail").checked,
        min_severity: (document.getElementById("minSeverity").value || "bad").trim().toLowerCase(),
        stale_always_notify: !!document.getElementById("staleAlways").checked,
        rate_limit_sec: toInt("rateLimit", 300),
        escalation_sec: toInt("escalationSec", 1800),
        mute_until: (document.getElementById("muteUntil").value || "").trim() || null,
      };
      const data = await apiPost("/api/admin/fleet/notification-settings", payload);
      setStatus(`ЗБЕРЕЖЕНО: ${JSON.stringify(data.settings || {})}`);
      await refresh();
    } catch (error) {
      setStatus("ПОМИЛКА: " + error);
    }
  }
  async function clearMute() {
    document.getElementById("muteUntil").value = "";
    await save();
  }
  async function sendTest() {
    if (!adminCaps.operate) { setTestStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    setTestStatus("Надсилання...");
    try {
      const payload = {
        central_id: (document.getElementById("testCentral").value || "central-gw").trim(),
        code: (document.getElementById("testCode").value || "test_notification").trim(),
        severity: (document.getElementById("testSeverity").value || "warn").trim().toLowerCase(),
        channel: (document.getElementById("testChannel").value || "auto").trim().toLowerCase(),
        message: (document.getElementById("testMessage").value || "ручне тестове сповіщення з адмін-панелі").trim(),
        dry_run: !!document.getElementById("testDryRun").checked,
      };
      const data = await apiPost("/api/admin/fleet/notification-settings/test", payload);
      const counters = data.result?.counters || {};
      setTestStatus(`OK: канали=${(data.channels || []).join(",") || "немає"} надіслано=${counters.sent || 0} помилки=${counters.failed || 0} пропущено=${counters.skipped || 0}`);
    } catch (error) {
      setTestStatus("ПОМИЛКА: " + error);
    }
  }
  async function sendHealthTest() {
    if (!adminCaps.operate) { setTestStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    setTestStatus("Надсилання тесту health флоту...");
    try {
      const payload = {
        channel: (document.getElementById("testChannel").value || "auto").trim().toLowerCase(),
        dry_run: !!document.getElementById("testDryRun").checked,
        window: "24h",
        note: (document.getElementById("testMessage").value || "").trim() || null,
      };
      const data = await apiPost("/api/admin/fleet/health/notify-test", payload);
      const counters = data.result?.counters || {};
      const state = data.snapshot?.state?.severity || "невідомо";
      setTestStatus(`OK: флот=${severityLabel(state)} канали=${(data.channels || []).join(",") || "немає"} надіслано=${counters.sent || 0} помилки=${counters.failed || 0} пропущено=${counters.skipped || 0}`);
    } catch (error) {
      setTestStatus("ПОМИЛКА: " + error);
    }
  }
  ui.byId("refresh").addEventListener("click", refresh);
  ui.byId("save").addEventListener("click", save);
  ui.byId("clearMute").addEventListener("click", clearMute);
  ui.byId("testSend").addEventListener("click", sendTest);
  ui.byId("healthTest").addEventListener("click", sendHealthTest);
  ui.byId("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  syncFilterSummary();
  initNotificationsSecondaryDetails();
  loadWhoami().then(refresh);
    """
    return render_admin_shell(
        title="Адмін-панель Passengers — Правила сповіщень",
        header_title="Правила сповіщень",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        max_width=980,
        current_nav="notifications",
    ).strip()
