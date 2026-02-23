from __future__ import annotations

from app.client_ui_kit import render_client_shell


def render_client_profile_page() -> str:
    chips_html = """
      <span class="chip">контактні дані клієнта</span>
      <span class="chip" id="whoami">роль: —</span>
    """
    toolbar_html = """
      <div class="toolbarMain">
        <button id="refresh">Оновити</button>
        <button id="save" class="primary">Зберегти</button>
        <button id="reset">Скинути до збереженого</button>
        <button id="copyLink">Скопіювати посилання</button>
      </div>
      <div class="toolbarMeta">
        <span class="metaChip" id="filterSummary">контекст: профіль клієнта</span>
        <span class="status" id="status"></span>
      </div>
    """
    body_html = """
    <div class="card">
      <div class="summary">
        <span class="badge" id="profileReady">ПРОФІЛЬ: —</span>
        <span class="badge" id="contactReady">КОНТАКТ: —</span>
        <span class="badge good" id="localeBadge">МОВА: UK</span>
      </div>
      <div class="muted" id="updatedAt">збережено: —</div>
    </div>

    <div class="card">
      <div class="sectionTitle">Профіль</div>
      <div class="row">
        <label for="fullName">Ім'я та прізвище</label>
        <input id="fullName" type="text" placeholder="Іван Петренко" />
      </div>
      <div class="row">
        <label for="company">Компанія</label>
        <input id="company" type="text" placeholder="ТОВ Пасажир Сервіс" />
      </div>
      <div class="row">
        <label for="email">Email</label>
        <input id="email" type="text" placeholder="client@example.com" />
      </div>
      <div class="row">
        <label for="phone">Телефон</label>
        <input id="phone" type="text" placeholder="+380XXXXXXXXX" />
      </div>
      <div class="row">
        <label for="locale">Мова інтерфейсу</label>
        <select id="locale">
          <option value="uk" selected>Українська</option>
          <option value="en">English</option>
        </select>
      </div>
      <div class="muted">Заповніть щонайменше один канал зв'язку (email або телефон), щоб підтримка могла швидко підтвердити ETA.</div>
    </div>

    <div class="card">
      <details id="profileSupportDetails" class="secondaryDetails">
        <summary>Деталі для підтримки</summary>
        <div class="secondaryBody">
          <div class="row">
            <label>Актор</label>
            <code id="supportActor">—</code>
          </div>
          <div class="row">
            <label>Контур доступу</label>
            <code id="supportScope">—</code>
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
  const SECONDARY_STORAGE_KEY = "passengers_client_profile_secondary_v1";
  let loadedProfile = {};
  let whoamiState = { actor: "", role: "client", scope: { central_ids: [], vehicle_ids: [] } };
  function setBadge(id, cls, text) {
    const node = ui.byId(id);
    if (!node) return;
    node.className = `badge ${cls}`.trim();
    node.textContent = text;
  }
  function nonEmpty(value) {
    return String(value || "").trim();
  }
  function collect() {
    return {
      full_name: nonEmpty(ui.byId("fullName").value),
      company: nonEmpty(ui.byId("company").value),
      email: nonEmpty(ui.byId("email").value),
      phone: nonEmpty(ui.byId("phone").value),
      locale: String(ui.byId("locale").value || "uk"),
    };
  }
  function apply(payload) {
    ui.byId("fullName").value = String(payload.full_name || "");
    ui.byId("company").value = String(payload.company || "");
    ui.byId("email").value = String(payload.email || "");
    ui.byId("phone").value = String(payload.phone || "");
    const locale = String(payload.locale || "uk").toLowerCase();
    ui.byId("locale").value = (locale === "en" ? "en" : "uk");
  }
  function profileFilledCount(payload) {
    const checks = [payload.full_name, payload.company, payload.email, payload.phone];
    return checks.filter((item) => nonEmpty(item).length > 0).length;
  }
  function renderSummary(payload, savedAtText = "") {
    const filled = profileFilledCount(payload);
    const locale = String(payload.locale || "uk").toLowerCase();
    const hasContact = nonEmpty(payload.email) || nonEmpty(payload.phone);
    setBadge("profileReady", filled >= 3 ? "good" : (filled >= 1 ? "warn" : "bad"), `ПРОФІЛЬ: ${filled}/4`);
    setBadge("contactReady", hasContact ? "good" : "bad", hasContact ? "КОНТАКТ: готовий" : "КОНТАКТ: відсутній");
    setBadge("localeBadge", locale === "en" ? "warn" : "good", locale === "en" ? "МОВА: EN" : "МОВА: UK");
    ui.setText("updatedAt", savedAtText ? `збережено: ${savedAtText}` : "збережено: —");
  }
  function renderSupport(payload) {
    const centralIds = Array.isArray(whoamiState.scope && whoamiState.scope.central_ids) ? whoamiState.scope.central_ids : [];
    const vehicleIds = Array.isArray(whoamiState.scope && whoamiState.scope.vehicle_ids) ? whoamiState.scope.vehicle_ids : [];
    const scopeText = `central=${centralIds.length ? centralIds.join(",") : "all"} · vehicle=${vehicleIds.length ? vehicleIds.join(",") : "all"}`;
    ui.setText("supportActor", String(whoamiState.actor || "—"));
    ui.setText("supportScope", scopeText);
    ui.byId("supportPayload").textContent = JSON.stringify({
      actor: String(whoamiState.actor || ""),
      role: String(whoamiState.role || "client"),
      profile: payload,
    }, null, 2);
  }
  function syncFilterSummary(payload) {
    const filled = profileFilledCount(payload);
    const hasContact = nonEmpty(payload.email) || nonEmpty(payload.phone);
    ui.setText("filterSummary", `контекст: профіль ${filled}/4 · контакт=${hasContact ? "готовий" : "відсутній"}`);
  }
  async function loadWhoami() {
    const whoami = await ui.loadWhoami();
    whoamiState = whoami || whoamiState;
    const isSupport = String(whoamiState.role || "client") === "admin-support";
    ui.setText("whoami", isSupport ? "роль: admin-support" : "роль: client");
    ui.bindDetailsState("profileSupportDetails", SECONDARY_STORAGE_KEY, isSupport);
  }
  async function load() {
    ui.setStatus("status", "Оновлення...");
    try {
      const data = await ui.apiGet("/api/client/profile");
      loadedProfile = data && data.profile ? data.profile : {};
      apply(loadedProfile);
      renderSummary(loadedProfile);
      renderSupport(loadedProfile);
      syncFilterSummary(loadedProfile);
      ui.setStatus("status", "OK: профіль завантажено");
    } catch (error) {
      ui.setStatus("status", `ПОМИЛКА: ${error && error.message ? error.message : "не вдалося завантажити профіль"}`);
    }
  }
  async function save() {
    const payload = collect();
    ui.setStatus("status", "Збереження...");
    try {
      const data = await ui.apiPost("/api/client/profile", payload);
      loadedProfile = data && data.profile ? data.profile : payload;
      apply(loadedProfile);
      renderSummary(loadedProfile, new Date().toLocaleString("uk-UA"));
      renderSupport(loadedProfile);
      syncFilterSummary(loadedProfile);
      ui.setStatus("status", "OK: профіль збережено");
    } catch (error) {
      ui.setStatus("status", `ПОМИЛКА: ${error && error.message ? error.message : "не вдалося зберегти профіль"}`);
    }
  }
  function resetToSaved() {
    apply(loadedProfile || {});
    renderSummary(loadedProfile || {});
    renderSupport(loadedProfile || {});
    syncFilterSummary(loadedProfile || {});
    ui.setStatus("status", "OK: відновлено збережену версію");
  }
  ui.byId("refresh").addEventListener("click", load);
  ui.byId("save").addEventListener("click", save);
  ui.byId("reset").addEventListener("click", resetToSaved);
  ui.byId("copySupport").addEventListener("click", () => ui.copyTextWithFallback(ui.byId("supportPayload").textContent || "", "Скопіюйте payload:", "Payload скопійовано", "Payload у prompt"));
  ui.byId("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  ui.bindDebouncedInputs(["fullName", "company", "email", "phone"], () => syncFilterSummary(collect()), 180);
  ui.byId("locale").addEventListener("change", () => {
    const payload = collect();
    renderSummary(payload);
    syncFilterSummary(payload);
  });
  async function init() {
    await loadWhoami();
    await load();
  }
  init();
    """.strip()
    return render_client_shell(
        title="Passengers — Профіль клієнта",
        header_title="Профіль",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        current_nav="client-profile",
    )
