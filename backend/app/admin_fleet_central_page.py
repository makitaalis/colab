from __future__ import annotations

from html import escape
from urllib.parse import quote

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_central_page(*, central_id: str) -> str:
    safe_central = str(central_id or "").strip()
    central_display = escape(safe_central)
    central_q = quote(safe_central, safe="")
    chips_html = f"""
        <span class="chip">вузол: <code>{central_display}</code></span>
        <span class="chip" id="roleBadge">роль: —</span>
        <span class="chip" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
        <div class="toolbarMain">
          <button class="primary" id="refresh">Оновити</button>
          <label><input id="auto" type="checkbox" checked /> авто</label>
          <button id="copyLink" title="Скопіювати посилання на вузол">Скопіювати посилання</button>
        </div>
        <div class="toolbarMeta">
          <span class="metaChip sort" id="filterSummary">вузол: —</span>
          <span class="status" id="status"></span>
        </div>
    """
    body_html = """
    <div class="gridStats">
      <div class="card stat"><div class="statlabel">Рівень</div><div class="statvalue" id="vSev">—</div></div>
      <div class="card stat"><div class="statlabel">Пакети в черзі</div><div class="statvalue" id="vPending">0</div></div>
      <div class="card stat"><div class="statlabel">Вік WG рукостискання</div><div class="statvalue" id="vWgAge">—</div></div>
      <div class="card stat"><div class="statlabel">Алерти (активні/усі)</div><div class="statvalue" id="vAlerts">0/0</div></div>
    </div>

    <div class="card" style="margin-top:12px;">
      <div class="sectionHead">
        <div class="sectionTitle">Поточні алерти</div>
        <div class="sectionTools">
          <a class="quickLink" href="#" id="openIncidents">Відкрити інциденти</a>
          <a class="quickLink" href="/admin/fleet/policy?central_id={central_q}">Policy override</a>
          <a class="quickLink" href="/admin/fleet/notify-center?central_id={central_q}">Notify-center</a>
        </div>
      </div>
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code>/api/admin/fleet/central/{central_q}</code></span>
        <span class="metaChip mode">контур: <code>active alerts</code></span>
        <span class="metaChip mode">ліміт: <code>120</code>, actions: <code>200</code></span>
      </div>
      <div class="muted">Підтвердження/заглушення застосовується за ключем <code>(central_id, code)</code></div>
      <div class="tableWrap">
        <table id="alertsTbl" style="min-width: 980px;">
          <thead>
            <tr>
              <th>Рівень</th>
              <th>Код</th>
              <th>Повідомлення</th>
              <th>Стан</th>
              <th>Дії</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <details id="centralSecondaryDetails" class="domainSplitDetails" data-advanced-details="1" style="margin-top: 12px;">
      <summary>Історія та журнал дій (вторинний контур)</summary>
      <div class="domainSplitHint">
        Цей блок залишено для розширеного аналізу. Оперативний triage виконуйте через “Поточні алерти” та “Інциденти”.
      </div>

      <div class="card" style="margin-top:12px;">
        <div class="sectionHead">
          <div class="sectionTitle">Історія черги/сервісів</div>
          <div class="sectionTools">
            <a class="quickLink" href="/admin/fleet/history">KPI history</a>
            <a class="quickLink" href="/admin/audit">Аудит</a>
          </div>
        </div>
        <div class="tableMeta">
          <span class="metaChip source">джерело: <code>/api/admin/fleet/central/{central_q}</code></span>
          <span class="metaChip mode">контур: <code>heartbeat history</code></span>
        </div>
        <div class="muted">Останні heartbeat-записи для цього вузла</div>
        <div class="tableWrap">
          <table id="histTbl" style="min-width: 980px;">
            <thead>
              <tr>
                <th>ts_received</th>
                <th>Рівень</th>
                <th>pending</th>
                <th>pending_oldest</th>
                <th>wg_handshake</th>
                <th>events/sent</th>
                <th>services</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>

      <div class="card" style="margin-top:12px;">
        <div class="sectionHead">
          <div class="sectionTitle">Журнал дій адміністратора</div>
          <div class="sectionTools">
            <a class="quickLink" href="/admin/fleet/actions?central_id={central_q}">Відкрити журнал дій</a>
          </div>
        </div>
        <div class="tableMeta">
          <span class="metaChip source">джерело: <code>/api/admin/fleet/alerts/actions</code></span>
          <span class="metaChip mode">контур: <code>central filter</code></span>
        </div>
        <div class="muted">Журнал дій <code>ack/silence/unsilence</code> по алертах цього central</div>
        <div class="tableWrap">
          <table id="actTbl" style="min-width: 980px;">
            <thead>
              <tr>
                <th>Час</th>
                <th>Дія</th>
                <th>Код</th>
                <th>Актор</th>
                <th>Нотатка</th>
                <th>Заглушено до</th>
              </tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
      </div>
    </details>
    """
    extra_css = """
    .gridStats { display:grid; grid-template-columns: repeat(12, 1fr); gap: 12px; }
    .gridStats .stat { grid-column: span 3; }
    .statlabel { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
    .statvalue { font-size: 22px; font-weight: 700; }
    @media (max-width: 1100px) { .gridStats .stat { grid-column: span 6; } }
    @media (max-width: 700px) { .gridStats .stat { grid-column: span 12; } }
    """.strip()
    script = f"""
  const ui = window.AdminUiKit;
  const CENTRAL_ID = {safe_central!r};
  const CENTRAL_SECONDARY_DETAILS_STORAGE_KEY = "passengers_admin_fleet_central_secondary_details_v1";
  let adminRole = "viewer";
  let adminCaps = {{ read: true, operate: false, admin: false }};
  function setStatus(s) {{ ui.setStatus("status", s); }}
  function applyRoleUi() {{ ui.setText("roleBadge", `роль: ${{adminRole}}`); }}
  function canOperate() {{ return !!adminCaps.operate; }}
  async function loadWhoami() {{
    const data = await ui.loadWhoami();
    adminRole = data.role;
    adminCaps = data.capabilities || {{ read: true, operate: false, admin: false }};
    applyRoleUi();
  }}
  function initCentralSecondaryDetails() {{
    const node = document.getElementById("centralSecondaryDetails");
    if (!(node instanceof HTMLDetailsElement)) return;
    try {{
      const raw = String(localStorage.getItem(CENTRAL_SECONDARY_DETAILS_STORAGE_KEY) || "").trim().toLowerCase();
      if (raw) node.open = raw === "1" || raw === "true" || raw === "on" || raw === "yes";
    }} catch (_error) {{}}
    node.addEventListener("toggle", () => {{
      try {{ localStorage.setItem(CENTRAL_SECONDARY_DETAILS_STORAGE_KEY, node.open ? "1" : "0"); }} catch (_error) {{}}
    }});
  }}
  function fmtAge(sec) {{
    if (sec === null || sec === undefined) return "—";
    if (sec < 0) return "—";
    const m = Math.floor(sec / 60);
    const h = Math.floor(m / 60);
    const d = Math.floor(h / 24);
    if (d > 0) return `${{d}}д ${{h%24}}г`;
    if (h > 0) return `${{h}}г ${{m%60}}хв`;
    return `${{m}}хв ${{sec%60}}с`;
  }}
  function badgeClass(level) {{
    const val = String(level || "").toLowerCase();
    if (val === "good" || val === "warn" || val === "bad") return val;
    return "bad";
  }}
  function severityLabel(level) {{
    const normalized = String(level || "").toLowerCase();
    if (normalized === "good") return "СПРАВНО";
    if (normalized === "warn") return "ПОПЕРЕДЖЕННЯ";
    return "КРИТИЧНО";
  }}
  function actionLabel(action) {{
    const normalized = String(action || "").toLowerCase();
    if (normalized === "ack") return "ПІДТВЕРДЖЕНО";
    if (normalized === "silence") return "ЗАГЛУШЕНО";
    if (normalized === "unsilence") return "ЗНЯТО ЗАГЛУШЕННЯ";
    return "ДІЯ";
  }}
  async function ackAlert(code) {{
    if (!canOperate()) {{ setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }}
    await ui.apiPost("/api/admin/fleet/alerts/ack", {{ central_id: CENTRAL_ID, code, actor: "admin-ui", note: "підтверджено зі сторінки вузла" }});
    await refresh();
  }}
  async function silenceAlert(code) {{
    if (!canOperate()) {{ setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }}
    await ui.apiPost("/api/admin/fleet/alerts/silence", {{ central_id: CENTRAL_ID, code, duration_sec: 3600, actor: "admin-ui", note: "заглушено зі сторінки вузла" }});
    await refresh();
  }}
  async function unsilenceAlert(code) {{
    if (!canOperate()) {{ setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }}
    await ui.apiPost("/api/admin/fleet/alerts/unsilence", {{ central_id: CENTRAL_ID, code, actor: "admin-ui", note: "знято заглушення зі сторінки вузла" }});
    await refresh();
  }}
  async function refresh() {{
    setStatus("Завантаження...");
    try {{
      const data = await ui.apiGet(`/api/admin/fleet/central/${{encodeURIComponent(CENTRAL_ID)}}?limit=120&actions_limit=200`);
      const current = data.central || {{}};
      const history = Array.isArray(data.history) ? data.history : [];
      const actions = Array.isArray(data.actions) ? data.actions : [];
      const health = current.health || {{}};
      const queue = current.queue || {{}};
      const sev = badgeClass(health.severity);
      ui.byId("vSev").textContent = severityLabel(sev);
      ui.byId("vSev").className = `statvalue ${{sev}}`;
      ui.byId("vPending").textContent = queue.pending_batches ?? 0;
      ui.byId("vWgAge").textContent = fmtAge(queue.wg_latest_handshake_age_sec);
      ui.byId("vAlerts").textContent = `${{health.alerts_total ?? 0}}/${{health.alerts_all_total ?? 0}}`;

      const alerts = Array.isArray(current.alerts) ? current.alerts : [];
      const alertsBody = document.querySelector("#alertsTbl tbody");
      alertsBody.innerHTML = "";
      if (alerts.length === 0) {{
        const tr = document.createElement("tr");
        tr.innerHTML = '<td colspan="5"><span class="badge good">OK</span> Немає поточних алертів</td>';
        alertsBody.appendChild(tr);
      }} else {{
        for (const item of alerts) {{
          const row = document.createElement("tr");
          const code = String(item.code || "alert");
          const sevCls = badgeClass(item.severity);
          const stateParts = [];
          if (item.silenced) stateParts.push('<span class="badge warn">заглушено</span>');
          if (item.acked_at) stateParts.push('<span class="badge good">підтверджено</span>');
          if (stateParts.length === 0) stateParts.push('<span class="badge">відкрито</span>');
          const actionDisabled = canOperate() ? "" : "disabled";
          const incidentHref = `/admin/fleet/incidents/${{encodeURIComponent(CENTRAL_ID)}}/${{encodeURIComponent(code)}}`;
          row.innerHTML = `
            <td><span class="badge ${{sevCls}}">${{ui.esc(severityLabel(sevCls))}}</span></td>
            <td><a href="${{incidentHref}}"><code>${{ui.esc(code)}}</code></a></td>
            <td>${{ui.esc(item.message || "")}}</td>
            <td>${{stateParts.join(" ")}}</td>
            <td>
              <div class="actions">
                <button class="smallbtn opAction opActionAck" data-action="ack" ${{actionDisabled}}>Підтвердити</button>
                <button class="smallbtn opAction opActionSilence" data-action="silence" ${{actionDisabled}}>Пауза 1 год</button>
                <button class="smallbtn opAction opActionUnsilence" data-action="unsilence" ${{actionDisabled}}>Зняти заглушення</button>
              </div>
            </td>
          `;
          row.querySelector('button[data-action="ack"]')?.addEventListener("click", () => ackAlert(code));
          row.querySelector('button[data-action="silence"]')?.addEventListener("click", () => silenceAlert(code));
          row.querySelector('button[data-action="unsilence"]')?.addEventListener("click", () => unsilenceAlert(code));
          alertsBody.appendChild(row);
        }}
      }}

      const histBody = document.querySelector("#histTbl tbody");
      histBody.innerHTML = "";
      for (const item of history) {{
        const row = document.createElement("tr");
        const itemHealth = item.health || {{}};
        const itemQueue = item.queue || {{}};
        const itemServices = item.services || {{}};
        const sevItem = badgeClass(itemHealth.severity);
        const servicesText = Object.entries(itemServices).map(([k,v]) => `${{k}}:${{v}}`).join(" ");
        row.innerHTML = `
          <td><code>${{ui.esc(item.ts_received || "—")}}</code></td>
          <td><span class="badge ${{sevItem}}">${{ui.esc(severityLabel(sevItem))}}</span></td>
          <td><code>${{ui.esc(itemQueue.pending_batches ?? 0)}}</code></td>
          <td><code>${{ui.esc(fmtAge(itemQueue.pending_oldest_age_sec))}}</code></td>
          <td><code>${{ui.esc(fmtAge(itemQueue.wg_latest_handshake_age_sec))}}</code></td>
          <td><code>${{ui.esc(itemQueue.events_total ?? 0)}}/${{ui.esc(itemQueue.sent_batches ?? 0)}}</code></td>
          <td><code>${{ui.esc(servicesText)}}</code></td>
        `;
        histBody.appendChild(row);
      }}

      const actBody = document.querySelector("#actTbl tbody");
      actBody.innerHTML = "";
      if (actions.length === 0) {{
        const row = document.createElement("tr");
        row.innerHTML = '<td colspan="6"><span class="badge">—</span> Немає дій</td>';
        actBody.appendChild(row);
      }} else {{
        for (const item of actions) {{
          const row = document.createElement("tr");
          const action = String(item.action || "").toLowerCase();
          const actionClass = action === "ack" ? "good" : (action === "silence" ? "warn" : "bad");
          row.innerHTML = `
            <td><code>${{ui.esc(item.ts || "—")}}</code></td>
            <td><span class="badge ${{actionClass}}">${{ui.esc(actionLabel(item.action || "action"))}}</span></td>
            <td><code>${{ui.esc(item.code || "—")}}</code></td>
            <td><code>${{ui.esc(item.actor || "—")}}</code></td>
            <td>${{ui.esc(item.note || "")}}</td>
            <td><code>${{ui.esc(item.silenced_until || "—")}}</code></td>
          `;
          actBody.appendChild(row);
        }}
      }}

      ui.byId("updatedAt").textContent = `оновлено: ${{current.ts_received || history[0]?.ts_received || new Date().toLocaleString("uk-UA")}}`;
      setStatus(`OK: історія=${{history.length}}, дій=${{actions.length}}`);
    }} catch (error) {{
      setStatus(`ПОМИЛКА: ${{error}}`);
    }}
  }}

  ui.byId("openIncidents").addEventListener("click", (event) => {{
    event.preventDefault();
    window.location.href = `/admin/fleet/incidents?central_id=${{encodeURIComponent(CENTRAL_ID)}}&include_resolved=0`;
  }});
  ui.byId("filterSummary").textContent = `вузол: ${{CENTRAL_ID}}`;
  ui.byId("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  ui.byId("refresh").addEventListener("click", refresh);
  initCentralSecondaryDetails();
  loadWhoami().then(refresh);
  setInterval(() => {{ if (ui.byId("auto").checked) refresh(); }}, 10000);
    """.strip()

    return render_admin_shell(
        title="Адмін-панель Passengers — Центральний вузол",
        header_title="Деталі центрального вузла",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script,
        extra_css=extra_css,
        max_width=1360,
        current_nav="fleet",
    ).strip()
