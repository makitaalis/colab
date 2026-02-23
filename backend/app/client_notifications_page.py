from __future__ import annotations

from app.client_ui_kit import render_client_shell


def render_client_notifications_page() -> str:
    chips_html = """
      <span class="chip">канали та частота сповіщень</span>
      <span class="chip" id="whoami">роль: —</span>
    """
    toolbar_html = """
      <div class="toolbarMain">
        <button id="refresh">Оновити</button>
        <button id="save" class="primary">Зберегти</button>
        <button id="copyLink">Скопіювати посилання</button>
      </div>
      <div class="toolbarMeta">
        <span class="metaChip" id="filterSummary">контекст: налаштування сповіщень</span>
        <span class="status" id="status"></span>
      </div>
    """
    body_html = """
    <div class="card">
      <div class="summary">
        <span class="badge" id="sumChannels">КАНАЛИ: —</span>
        <span class="badge" id="sumLevel">ПРІОРИТЕТ: —</span>
        <span class="badge" id="sumDigest">ДАЙДЖЕСТ: —</span>
      </div>
      <div class="muted">Оберіть режим оповіщення, щоб балансувати швидкість реакції і обсяг повідомлень.</div>
    </div>

    <div class="card">
      <div class="sectionTitle">Канали</div>
      <div class="row">
        <label for="notifyEmail">Email-сповіщення</label>
        <input id="notifyEmail" type="checkbox" />
      </div>
      <div class="row">
        <label for="notifySms">SMS-сповіщення</label>
        <input id="notifySms" type="checkbox" />
      </div>
      <div class="row">
        <label for="notifyPush">Push-сповіщення</label>
        <input id="notifyPush" type="checkbox" />
      </div>
      <div class="row">
        <label for="notifyLevel">Рівень важливості</label>
        <select id="notifyLevel">
          <option value="critical">лише важливе</option>
          <option value="all" selected>усі оновлення</option>
        </select>
      </div>
      <div class="row">
        <label for="digestWindow">Дайджест</label>
        <select id="digestWindow">
          <option value="off">вимкнено</option>
          <option value="1h">щогодини</option>
          <option value="24h" selected>щодня</option>
        </select>
      </div>
      <div class="toolbar">
        <button id="presetCritical" class="smallbtn">Шаблон: критично</button>
        <button id="presetBalanced" class="smallbtn">Шаблон: збалансовано</button>
        <button id="presetRealtime" class="smallbtn">Шаблон: реальний час</button>
      </div>
      <div class="muted">Налаштування зберігаються в backend для поточного клієнтського контуру.</div>
    </div>

    <div class="card">
      <details id="notifySupportDetails" class="secondaryDetails">
        <summary>Деталі для підтримки</summary>
        <div class="secondaryBody">
          <div class="row">
            <label>Актор</label>
            <code id="supportActor">—</code>
          </div>
          <div class="row">
            <label>Попередній перегляд payload</label>
            <pre id="supportPayload" style="margin:0; white-space:pre-wrap;"></pre>
          </div>
          <div class="toolbar">
            <button id="copySupport" class="smallbtn">Копіювати payload</button>
          </div>
        </div>
      </details>
    </div>
    """
    script = """
  const ui = window.ClientUiKit;
  const SECONDARY_STORAGE_KEY = "passengers_client_notifications_secondary_v1";
  let loadedSettings = {};
  let whoamiState = { actor: "", role: "client" };
  function setBadge(id, cls, text) {
    const node = ui.byId(id);
    if (!node) return;
    node.className = `badge ${cls}`.trim();
    node.textContent = text;
  }
  function collect() {
    return {
      notify_email: !!ui.byId("notifyEmail").checked,
      notify_sms: !!ui.byId("notifySms").checked,
      notify_push: !!ui.byId("notifyPush").checked,
      notify_level: String(ui.byId("notifyLevel").value || "all"),
      digest_window: String(ui.byId("digestWindow").value || "24h"),
    };
  }
  function apply(payload) {
    ui.byId("notifyEmail").checked = !!payload.notify_email;
    ui.byId("notifySms").checked = !!payload.notify_sms;
    ui.byId("notifyPush").checked = !!payload.notify_push;
    ui.byId("notifyLevel").value = payload.notify_level || "all";
    ui.byId("digestWindow").value = payload.digest_window || "24h";
  }
  function enabledChannels(payload) {
    const checks = [payload.notify_email, payload.notify_sms, payload.notify_push];
    return checks.filter((item) => !!item).length;
  }
  function renderSummary(payload) {
    const channels = enabledChannels(payload);
    const level = String(payload.notify_level || "all");
    const digest = String(payload.digest_window || "24h");
    const levelLabel = level === "critical" ? "критичні" : "усі";
    const digestLabel = digest === "off" ? "вимкнено" : (digest === "1h" ? "щогодини" : "щодня");
    setBadge("sumChannels", channels >= 2 ? "good" : (channels === 1 ? "warn" : "bad"), `КАНАЛИ: ${channels}/3`);
    setBadge("sumLevel", level === "critical" ? "good" : "warn", `ПРІОРИТЕТ: ${levelLabel}`);
    setBadge("sumDigest", digest === "off" ? "warn" : "good", `ДАЙДЖЕСТ: ${digestLabel}`);
  }
  function renderSupport(payload) {
    ui.setText("supportActor", String(whoamiState.actor || "—"));
    ui.byId("supportPayload").textContent = JSON.stringify({
      actor: String(whoamiState.actor || ""),
      role: String(whoamiState.role || "client"),
      settings: payload,
    }, null, 2);
  }
  function syncFilterSummary(payload) {
    const channels = enabledChannels(payload);
    const level = String(payload.notify_level || "all");
    const digest = String(payload.digest_window || "24h");
    const levelLabel = level === "critical" ? "критичні" : "усі";
    const digestLabel = digest === "off" ? "вимкнено" : (digest === "1h" ? "щогодини" : "щодня");
    ui.setText("filterSummary", `контекст: канали=${channels}/3 · пріоритет=${levelLabel} · дайджест=${digestLabel}`);
  }
  function applyPreset(kind) {
    if (kind === "critical") {
      apply({ notify_email: true, notify_sms: true, notify_push: false, notify_level: "critical", digest_window: "off" });
      return;
    }
    if (kind === "realtime") {
      apply({ notify_email: true, notify_sms: true, notify_push: true, notify_level: "all", digest_window: "off" });
      return;
    }
    apply({ notify_email: true, notify_sms: false, notify_push: true, notify_level: "all", digest_window: "24h" });
  }
  function onFormChanged() {
    const payload = collect();
    renderSummary(payload);
    renderSupport(payload);
    syncFilterSummary(payload);
  }
  async function loadWhoami() {
    const whoami = await ui.loadWhoami();
    whoamiState = whoami || whoamiState;
    const isSupport = String(whoamiState.role || "client") === "admin-support";
    ui.setText("whoami", isSupport ? "роль: admin-support" : "роль: client");
    ui.bindDetailsState("notifySupportDetails", SECONDARY_STORAGE_KEY, isSupport);
  }
  async function load() {
    ui.setStatus("status", "Оновлення...");
    try {
      const data = await ui.apiGet("/api/client/notification-settings");
      loadedSettings = data && data.settings ? data.settings : {};
      apply(loadedSettings);
      renderSummary(loadedSettings);
      renderSupport(loadedSettings);
      syncFilterSummary(loadedSettings);
      ui.setStatus("status", "OK: налаштування завантажено");
    } catch (error) {
      ui.setStatus("status", `ПОМИЛКА: ${error && error.message ? error.message : "не вдалося завантажити налаштування"}`);
    }
  }
  async function save() {
    const payload = collect();
    ui.setStatus("status", "Збереження...");
    try {
      const data = await ui.apiPost("/api/client/notification-settings", payload);
      loadedSettings = data && data.settings ? data.settings : payload;
      apply(loadedSettings);
      renderSummary(loadedSettings);
      renderSupport(loadedSettings);
      syncFilterSummary(loadedSettings);
      ui.setStatus("status", "OK: налаштування збережено");
    } catch (error) {
      ui.setStatus("status", `ПОМИЛКА: ${error && error.message ? error.message : "не вдалося зберегти налаштування"}`);
    }
  }
  ui.byId("refresh").addEventListener("click", load);
  ui.byId("save").addEventListener("click", save);
  ui.byId("presetCritical").addEventListener("click", () => { applyPreset("critical"); onFormChanged(); });
  ui.byId("presetBalanced").addEventListener("click", () => { applyPreset("balanced"); onFormChanged(); });
  ui.byId("presetRealtime").addEventListener("click", () => { applyPreset("realtime"); onFormChanged(); });
  ui.byId("notifyEmail").addEventListener("change", onFormChanged);
  ui.byId("notifySms").addEventListener("change", onFormChanged);
  ui.byId("notifyPush").addEventListener("change", onFormChanged);
  ui.byId("notifyLevel").addEventListener("change", onFormChanged);
  ui.byId("digestWindow").addEventListener("change", onFormChanged);
  ui.byId("copySupport").addEventListener("click", () => ui.copyTextWithFallback(ui.byId("supportPayload").textContent || "", "Скопіюйте payload:", "Payload скопійовано", "Payload у prompt"));
  ui.byId("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  async function init() {
    await loadWhoami();
    await load();
  }
  init();
    """.strip()
    return render_client_shell(
        title="Passengers — Сповіщення клієнта",
        header_title="Сповіщення",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        current_nav="client-notifications",
    )
