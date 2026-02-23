from __future__ import annotations

from app.client_ui_kit import render_client_shell


def render_client_home_page() -> str:
    chips_html = """
      <span class="chip">клієнтський кабінет MVP</span>
      <span class="chip" id="whoami">роль: —</span>
      <span class="chip" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
      <div class="toolbarMain">
        <button id="tableToggle" class="tableToggle" data-table-toggle="progressive" data-open="0">Колонки: базово</button>
        <button id="copyLink">Скопіювати посилання</button>
      </div>
      <div class="toolbarMeta">
        <span class="metaChip" id="filterSummary">контекст: SLA/ETA огляд</span>
        <span class="status" id="status"></span>
      </div>
    """
    body_html = """
    <div class="card">
      <div class="summary">
        <span class="badge" id="kService">СЕРВІС: —</span>
        <span class="badge" id="kTickets">ЗВЕРНЕННЯ: —</span>
        <span class="badge" id="kFleet">ТРАНСПОРТ: —</span>
        <span class="badge" id="kSla">SLA: —</span>
        <span class="badge" id="kEta">ETA: —</span>
      </div>
      <div class="muted">Ключова інформація за поточну зміну: сервісний стан, SLA-ризики і прогнозована затримка.</div>
    </div>

    <div class="card">
      <div class="sectionTitle">Потребує дії зараз</div>
      <div class="tableWrap">
        <table id="attentionTbl" class="mobileFriendly" data-empty-title="OK" data-empty-tone="good" data-empty-text="Критичних SLA/ETA відхилень не зафіксовано.">
          <thead>
            <tr>
              <th>Транспорт</th>
              <th class="mobileHide progressiveCol">Маршрут</th>
              <th>SLA</th>
              <th>ETA</th>
              <th>Рекомендація</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <div class="card">
      <div class="sectionTitle">Швидкі дії</div>
      <div class="toolbar">
        <a class="smallbtn" href="/client/vehicles">Переглянути транспорти</a>
        <a class="smallbtn" href="/client/tickets">Мої звернення</a>
        <a class="smallbtn" href="/client/notifications">Налаштувати сповіщення</a>
      </div>
      <div class="muted" id="supportHint" style="margin-top:8px;"></div>
    </div>
    """
    script = """
  const ui = window.ClientUiKit;
  function setBadge(id, cls, text) {
    const node = ui.byId(id);
    if (!node) return;
    node.className = `badge ${cls}`.trim();
    node.textContent = text;
  }
  function fmtTs(value) {
    const raw = String(value || "").trim();
    if (!raw) return "—";
    const dt = new Date(raw);
    if (Number.isFinite(dt.getTime())) return dt.toLocaleString("uk-UA");
    return raw;
  }
  function slaBadge(value) {
    const state = String(value || "").toLowerCase();
    if (state === "risk") return '<span class="badge bad">РИЗИК</span>';
    if (state === "warn") return '<span class="badge warn">УВАГА</span>';
    return '<span class="badge good">OK</span>';
  }
  function renderAttention(items) {
    const tbody = ui.byId("attentionTbl").querySelector("tbody");
    tbody.innerHTML = "";
    for (const item of items) {
      const row = document.createElement("tr");
      row.innerHTML = `
        <td><code>${ui.esc(item.id)}</code></td>
        <td class="mobileHide progressiveCol"><code>${ui.esc(item.route)}</code></td>
        <td>${slaBadge(item.sla_state)}</td>
        <td><span class="badge warn">+${Number(item.eta_delay_min || 0)} хв</span></td>
        <td>${ui.esc(item.hint)}</td>
      `;
      tbody.appendChild(row);
    }
    ui.applyEmptyTables();
  }
  async function initWhoami() {
    const whoami = await ui.loadWhoami();
    const role = String(whoami.role || "client");
    ui.setText("whoami", role === "admin-support" ? "роль: admin-support" : "роль: client");
    ui.setText("supportHint", role === "admin-support"
      ? "Режим support: доступні розширені секції у Тікетах і Статусах."
      : "Режим client: показані лише ключові дані без технічного шуму.");
  }
  async function refresh() {
    ui.setStatus("status", "Оновлення...");
    try {
      const data = await ui.apiGet("/api/client/home");
      const summary = data && data.summary ? data.summary : {};
      const attention = Array.isArray(data.attention) ? data.attention : [];
      const service = String(summary.service_state || "warn").toLowerCase();
      const serviceCls = service === "good" ? "good" : (service === "bad" ? "bad" : "warn");
      const serviceLabel = service === "good" ? "СЕРВІС: доступний" : (service === "bad" ? "СЕРВІС: є проблеми" : "СЕРВІС: увага");
      setBadge("kService", serviceCls, serviceLabel);
      const ticketsActive = Number(summary.tickets_open || 0) + Number(summary.tickets_in_progress || 0);
      setBadge("kTickets", ticketsActive > 0 ? "warn" : "good", `ЗВЕРНЕННЯ: ${ticketsActive} активних`);
      setBadge(
        "kFleet",
        Number(summary.transport_bad || 0) > 0 ? "bad" : (Number(summary.transport_warn || 0) > 0 ? "warn" : "good"),
        `ТРАНСПОРТ: ${Number(summary.transport_total || 0)} од.`
      );
      setBadge(
        "kSla",
        Number(summary.sla_risk || 0) > 0 ? "bad" : (Number(summary.sla_warn || 0) > 0 ? "warn" : "good"),
        `SLA: ризик ${Number(summary.sla_risk || 0)} · увага ${Number(summary.sla_warn || 0)}`
      );
      setBadge(
        "kEta",
        Number(summary.eta_max_delay_min || 0) >= 12 ? "bad" : (Number(summary.eta_avg_delay_min || 0) >= 4 ? "warn" : "good"),
        `ETA: avg +${Number(summary.eta_avg_delay_min || 0)} хв · max +${Number(summary.eta_max_delay_min || 0)} хв`
      );
      renderAttention(attention);
      ui.setText(
        "filterSummary",
        attention.length > 0
          ? `контекст: SLA/ETA огляд · потребує дії=${attention.length}`
          : "контекст: SLA/ETA огляд · критичних відхилень немає"
      );
      ui.setText("updatedAt", `оновлено: ${fmtTs(summary.updated_at)}`);
      ui.setStatus("status", `OK: сервіс=${service}, дії=${attention.length}`);
    } catch (error) {
      renderAttention([]);
      ui.setStatus("status", `ПОМИЛКА: ${error && error.message ? error.message : "не вдалося завантажити дані"}`);
    }
  }
  ui.byId("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  async function init() {
    await initWhoami();
    await refresh();
  }
  init();
    """.strip()
    return render_client_shell(
        title="Passengers — Кабінет клієнта",
        header_title="Огляд клієнта",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        current_nav="client-home",
    )
