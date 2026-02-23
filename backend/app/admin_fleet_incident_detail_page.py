from __future__ import annotations

import json

from app.admin_ui_kit import render_admin_shell


def render_admin_fleet_incident_detail_page(central_id: str, code: str) -> str:
    chips_html = """
        <span class="chip" id="incidentChip"></span>
        <span class="chip" id="workspaceHint">Контекст інциденту: —</span>
        <span class="chip mono" id="roleBadge">роль: —</span>
        <span class="chip" id="updatedAt">оновлено: —</span>
    """
    toolbar_html = """
        <div class="toolbarMain">
          <a class="toolbarBtn" id="incidentsBack" href="/admin/fleet/incidents">← інциденти</a>
          <a class="toolbarBtn" id="centralLinkBtn" href="#">вузол</a>
          <button class="primary" id="refresh">Оновити</button>
          <label><input id="auto" type="checkbox" checked /> авто</label>
          <button id="copyLink" title="Скопіювати поточне посилання (інцидент)">Скопіювати посилання</button>
        </div>
        <div class="toolbarMeta">
          <span class="status" id="status"></span>
        </div>
    """
    body_html = """
    <div class="grid">
      <div class="card stat"><div class="statlabel">Статус</div><div class="statvalue" id="vStatus">—</div></div>
      <div class="card stat"><div class="statlabel">Рівень</div><div class="statvalue" id="vSeverity">—</div></div>
      <div class="card stat"><div class="statlabel">Вік інциденту</div><div class="statvalue" id="vAge">—</div></div>
      <div class="card stat"><div class="statlabel">SLA</div><div class="statvalue" id="vSla">—</div></div>
    </div>

    <div class="card" style="margin-top:12px;">
      <div class="sectionHead">
        <div class="sectionTitle">Поточний стан</div>
        <div class="sectionTools">
          <a class="quickLink" id="openIncidentsLink" href="#">Інциденти</a>
          <a class="quickLink" id="openActionsLink" href="#">Журнал дій</a>
          <a class="quickLink" id="openNotifyLink" href="#">Доставка</a>
          <a class="quickLink" id="openPolicyLink" href="#">Policy</a>
          <a class="quickLink" id="openAuditLink" href="#">Аудит</a>
        </div>
      </div>
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code id="incidentSource">/api/admin/fleet/incidents/…</code></span>
        <span class="metaChip mode">ключ: <code>(central_id, code)</code></span>
        <span class="metaChip mode">limit: <code>120</code></span>
      </div>
      <div class="kv" id="stateKv"></div>
      <div class="hint" id="incidentMessageLine">повідомлення: —</div>
      <details class="advancedDetails" data-advanced-details="1" id="incidentMessageDetails">
        <summary>Повідомлення (детально)</summary>
        <pre class="tableWrap" style="max-height: 28vh; padding: 10px; margin-top:8px;"><code id="incidentMessage"></code></pre>
      </details>
      <div class="actions" style="margin-top:10px;">
        <button class="smallbtn" id="btnAck">Підтвердити</button>
        <button class="smallbtn" id="btnSilence">Пауза 1 год</button>
        <button class="smallbtn" id="btnUnsilence">Зняти заглушення</button>
      </div>
    </div>

    <div class="card" style="margin-top:12px;">
      <div class="sectionHead">
        <div class="sectionTitle">Таймлайн</div>
        <div class="sectionTools">
          <span class="muted">Heartbeat + дії адміністратора + доставка</span>
        </div>
      </div>
      <div class="tableMeta">
        <span class="metaChip source">джерело: <code id="timelineSource">/api/admin/fleet/incidents/…</code></span>
        <span class="metaChip sort">сортування: <code>нові → старі</code></span>
      </div>
      <div class="tableWrap" style="max-height: 44vh;">
        <table id="timelineTbl">
          <thead>
            <tr>
              <th>Час</th>
              <th>Тип</th>
              <th>Статус</th>
              <th>Деталі</th>
            </tr>
          </thead>
          <tbody></tbody>
        </table>
      </div>
    </div>

    <details id="incidentDebugDetails" class="domainSplitDetails" data-advanced-details="1" style="margin-top: 12px;">
      <summary>Діагностика (raw payload)</summary>
      <div class="domainSplitHint">
        Цей блок використовуйте для поглибленого аналізу контракту API або розбору нетипових станів.
      </div>
      <div class="sectionHead" style="margin-top: 10px;">
        <div class="sectionTitle">Payload</div>
        <div class="sectionTools">
          <button class="smallbtn" id="copyPayload">Копіювати</button>
        </div>
      </div>
      <pre class="tableWrap" style="max-height: 44vh; padding: 10px; margin-top:8px;"><code id="rawPayload"></code></pre>
      <div class="hint" id="rawPayloadHint"></div>
    </details>
    """
    extra_css = """
    .grid { display:grid; grid-template-columns: repeat(12, 1fr); gap: 12px; }
    .stat { grid-column: span 3; }
    .statlabel { color: var(--muted); font-size: 12px; margin-bottom: 6px; }
    .statvalue { font-size: 22px; font-weight: 700; }
    .actions { display:flex; gap: 6px; flex-wrap: wrap; }
    .kv { display:flex; gap: 10px; flex-wrap: wrap; margin-top: 8px; }
    .kv .item { background: rgba(255,255,255,.03); border: 1px solid var(--border); border-radius: 10px; padding: 6px 8px; font-size: 12px; }
    @media (max-width: 1100px) { .stat { grid-column: span 6; } }
    @media (max-width: 700px) { .stat { grid-column: span 12; } }
    """.strip()
    script = """
  const ui = window.AdminUiKit;
  const esc = ui.esc;
  const CENTRAL_ID = __CENTRAL_ID__;
  const CODE = __INCIDENT_CODE__;
  let adminRole = "viewer";
  let adminCaps = { read: true, operate: false, admin: false };
  document.getElementById("incidentChip").textContent = `${CENTRAL_ID}:${CODE}`;
  ui.saveWorkspaceContext({
    central_id: CENTRAL_ID,
    code: CODE,
    source: "incidents/detail",
    label: `${CENTRAL_ID}:${CODE}`,
  });
  ui.applyWorkspaceHint("workspaceHint", { prefix: "Контекст інциденту", maxAgeSec: 3 * 24 * 3600 });
  document.getElementById("centralLinkBtn").href = `/admin/fleet/central/${encodeURIComponent(CENTRAL_ID)}`;
  document.getElementById("incidentsBack").href = `/admin/fleet/incidents?central_id=${encodeURIComponent(CENTRAL_ID)}&include_resolved=0`;
  document.getElementById("openIncidentsLink").href = `/admin/fleet/incidents?central_id=${encodeURIComponent(CENTRAL_ID)}&include_resolved=0`;
  document.getElementById("openActionsLink").href = `/admin/fleet/actions?central_id=${encodeURIComponent(CENTRAL_ID)}&code=${encodeURIComponent(CODE)}`;
  document.getElementById("openNotifyLink").href = `/admin/fleet/notify-center?central_id=${encodeURIComponent(CENTRAL_ID)}&code=${encodeURIComponent(CODE)}`;
  document.getElementById("openPolicyLink").href = `/admin/fleet/policy?central_id=${encodeURIComponent(CENTRAL_ID)}`;
  document.getElementById("openAuditLink").href = `/admin/audit?q=${encodeURIComponent(CENTRAL_ID + ":" + CODE)}`;
  document.getElementById("copyLink").addEventListener("click", () => ui.copyTextWithFallback(window.location.href, "Скопіюйте посилання:", "Посилання скопійовано", "Посилання у prompt"));
  function setStatus(s) { ui.setStatus("status", s); }
  function applyRoleUi() {
    document.getElementById("roleBadge").textContent = `роль: ${adminRole}`;
    const disabled = !adminCaps.operate;
    document.getElementById("btnAck").disabled = disabled;
    document.getElementById("btnSilence").disabled = disabled;
    document.getElementById("btnUnsilence").disabled = disabled;
  }
  async function loadWhoami() {
    const data = await ui.loadWhoami();
    adminRole = data.role;
    adminCaps = data.capabilities || { read: true, operate: false, admin: false };
    applyRoleUi();
  }
  function fmtAge(sec) {
    if (sec === null || sec === undefined) return "—";
    if (sec < 0) return "—";
    const m = Math.floor(sec / 60);
    const h = Math.floor(m / 60);
    const d = Math.floor(h / 24);
    if (d > 0) return `${d}д ${h%24}г`;
    if (h > 0) return `${h}г ${m%60}хв`;
    return `${m}хв ${sec%60}с`;
  }
  function badgeClass(level) {
    const normalized = String(level || "").toLowerCase();
    if (normalized === "good" || normalized === "warn" || normalized === "bad") return normalized;
    return "bad";
  }
  function statusLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "open") return "ВІДКРИТО";
    if (normalized === "acked") return "ПІДТВЕРДЖЕНО";
    if (normalized === "silenced") return "ЗАГЛУШЕНО";
    if (normalized === "resolved") return "ВИРІШЕНО";
    return "НЕВІДОМО";
  }
  function severityLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "good") return "СПРАВНО";
    if (normalized === "warn") return "ПОПЕРЕДЖЕННЯ";
    return "КРИТИЧНО";
  }
  function actionClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "ack") return "good";
    if (normalized === "silence") return "warn";
    if (normalized === "unsilence") return "good";
    return "warn";
  }
  function actionLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "ack") return "ПІДТВЕРДЖЕНО";
    if (normalized === "silence") return "ЗАГЛУШЕНО";
    if (normalized === "unsilence") return "ЗНЯТО ЗАГЛУШЕННЯ";
    return "ДІЯ";
  }
  function notificationClass(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "sent") return "good";
    if (normalized === "skipped") return "warn";
    if (normalized === "failed") return "bad";
    return "warn";
  }
  function notificationLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "sent") return "НАДІСЛАНО";
    if (normalized === "skipped") return "ПРОПУЩЕНО";
    if (normalized === "failed") return "ПОМИЛКА";
    return "НЕВІДОМО";
  }
  function timelineTypeLabel(value) {
    const normalized = String(value || "").toLowerCase();
    if (normalized === "heartbeat") return "HEARTBEAT";
    if (normalized === "admin_action") return "ДІЯ АДМІНА";
    if (normalized === "notification") return "СПОВІЩЕННЯ";
    return "ПОДІЯ";
  }
  function timelineStatusClass(type, status) {
    const normalizedType = String(type || "").toLowerCase();
    if (normalizedType === "heartbeat") return badgeClass(status);
    if (normalizedType === "admin_action") return actionClass(status);
    if (normalizedType === "notification") return notificationClass(status);
    return "warn";
  }
  function timelineStatusLabel(type, status) {
    const normalizedType = String(type || "").toLowerCase();
    if (normalizedType === "heartbeat") return severityLabel(status);
    if (normalizedType === "admin_action") return actionLabel(status);
    if (normalizedType === "notification") return notificationLabel(status);
    return "ПОДІЯ";
  }
  async function apiPost(path, payload) {
    return ui.apiPost(path, payload);
  }
  function trimText(text, maxLen) {
    const raw = String(text || "");
    const normalized = raw.replace(/\\s+/g, " ").trim();
    if (normalized.length <= maxLen) return normalized;
    return normalized.slice(0, Math.max(0, maxLen - 1)) + "…";
  }
  async function doAck() {
    if (!adminCaps.operate) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    const result = await ui.runActionWithLatency(() =>
      apiPost("/api/admin/fleet/alerts/ack", { central_id: CENTRAL_ID, code: CODE, actor: "admin-ui", note: "підтверджено зі сторінки інциденту" })
    );
    if (!result.ok) { setStatus(`ПОМИЛКА підтвердження (${ui.formatLatency(result.elapsed_ms)}): ${result.error}`); return; }
    await refresh();
    setStatus(`ПІДТВЕРДЖЕНО: ${CENTRAL_ID}:${CODE} · ${ui.formatLatency(result.elapsed_ms)}`);
  }
  async function doSilence() {
    if (!adminCaps.operate) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    const result = await ui.runActionWithLatency(() =>
      apiPost("/api/admin/fleet/alerts/silence", { central_id: CENTRAL_ID, code: CODE, duration_sec: 3600, actor: "admin-ui", note: "заглушено зі сторінки інциденту" })
    );
    if (!result.ok) { setStatus(`ПОМИЛКА заглушення (${ui.formatLatency(result.elapsed_ms)}): ${result.error}`); return; }
    await refresh();
    setStatus(`ЗАГЛУШЕНО: ${CENTRAL_ID}:${CODE} · ${ui.formatLatency(result.elapsed_ms)}`);
  }
  async function doUnsilence() {
    if (!adminCaps.operate) { setStatus("ЛИШЕ ЧИТАННЯ: потрібна роль operator"); return; }
    const result = await ui.runActionWithLatency(() =>
      apiPost("/api/admin/fleet/alerts/unsilence", { central_id: CENTRAL_ID, code: CODE, actor: "admin-ui", note: "знято заглушення зі сторінки інциденту" })
    );
    if (!result.ok) { setStatus(`ПОМИЛКА зняття заглушення (${ui.formatLatency(result.elapsed_ms)}): ${result.error}`); return; }
    await refresh();
    setStatus(`ЗНЯТО ЗАГЛУШЕННЯ: ${CENTRAL_ID}:${CODE} · ${ui.formatLatency(result.elapsed_ms)}`);
  }
  function pushTimeline(rows, item) { if (item && item.ts) rows.push(item); }
  async function refresh() {
    setStatus("Завантаження...");
    try {
      const endpoint = `/api/admin/fleet/incidents/${encodeURIComponent(CENTRAL_ID)}/${encodeURIComponent(CODE)}?limit=120`;
      const data = await ui.apiGet(endpoint);
      const incident = data.incident || {};
      const actions = Array.isArray(data.actions) ? data.actions : [];
      const notifications = Array.isArray(data.notifications) ? data.notifications : [];
      const historyHits = Array.isArray(data.history_hits) ? data.history_hits : [];
      ui.setText("incidentSource", endpoint);
      ui.setText("timelineSource", endpoint);

      const statusVal = String(incident.status || "open");
      const severityVal = String(incident.severity || "bad");
      document.getElementById("vStatus").textContent = statusLabel(statusVal);
      document.getElementById("vStatus").className = `statvalue ${badgeClass(severityVal)}`;
      document.getElementById("vSeverity").textContent = severityLabel(severityVal);
      document.getElementById("vSeverity").className = `statvalue ${badgeClass(severityVal)}`;
      document.getElementById("vAge").textContent = fmtAge(incident.age_sec);
      document.getElementById("vSla").textContent = `${fmtAge(incident.sla_target_sec)}${incident.sla_breached ? " (порушено)" : ""}`;
      document.getElementById("vSla").className = `statvalue ${incident.sla_breached ? "bad" : "good"}`;

      const kv = document.getElementById("stateKv");
      const kvItems = [
        `транспорт: ${esc(incident.vehicle_id || "—")}`,
        `перша_поява: ${esc(incident.first_seen_ts || "—")}`,
        `остання_поява: ${esc(incident.last_seen_ts || "—")}`,
        `випадків: ${esc(incident.occurrences ?? 0)}`,
        `підтвердив: ${esc(incident.acked_by || "—")}`,
        `заглушено_до: ${esc(incident.silenced_until || "—")}`,
      ];
      kv.innerHTML = kvItems.map((item) => `<div class="item">${item}</div>`).join("");
      ui.setText("incidentMessageLine", `повідомлення: ${trimText(incident.message || "—", 140)}`);
      ui.byId("incidentMessage").textContent = String(incident.message || "—");

      const timeline = [];
      for (const hb of historyHits) {
        pushTimeline(timeline, {
          ts: hb.ts_received || hb.ts || "",
          type: "heartbeat",
          status: hb.severity || "warn",
          details: `алерт досі активний, вік=${fmtAge(hb.age_sec)}`,
        });
      }
      for (const action of actions) {
        pushTimeline(timeline, {
          ts: action.ts || "",
          type: "admin_action",
          status: action.action || "action",
          details: `${action.code || CODE} · актор=${action.actor || "—"} ${action.note || ""}`.trim(),
        });
      }
      for (const notif of notifications) {
        pushTimeline(timeline, {
          ts: notif.ts || "",
          type: "notification",
          status: notif.status || "unknown",
          details: `${notif.channel || "channel"} · ${notif.event || "event"} ${notif.error || ""}`.trim(),
        });
      }
      timeline.sort((a, b) => String(b.ts || "").localeCompare(String(a.ts || "")));

      const tbody = document.querySelector("#timelineTbl tbody");
      tbody.innerHTML = "";
      if (timeline.length === 0) {
        const row = document.createElement("tr");
        row.innerHTML = '<td colspan="4"><span class="badge">—</span> Немає таймлайну</td>';
        tbody.appendChild(row);
      } else {
        for (const item of timeline) {
          const row = document.createElement("tr");
          const statusClass = timelineStatusClass(item.type, item.status);
          const statusText = timelineStatusLabel(item.type, item.status);
          row.innerHTML = `
            <td><code>${esc(item.ts || "—")}</code></td>
            <td><code>${esc(timelineTypeLabel(item.type))}</code></td>
            <td><span class="badge ${statusClass}">${esc(statusText)}</span></td>
            <td>${esc(item.details || "")}</td>
          `;
          tbody.appendChild(row);
        }
      }

      document.getElementById("updatedAt").textContent = `оновлено: ${incident.last_seen_ts || new Date().toLocaleString("uk-UA")}`;
      setStatus(`OK: дій=${actions.length}, сповіщень=${notifications.length}, heartbeat_збігів=${historyHits.length}`);

      const raw = JSON.stringify(data || {}, null, 2);
      const rawMax = 90000;
      const rawShort = raw.length > rawMax ? raw.slice(0, rawMax) : raw;
      ui.byId("rawPayload").textContent = rawShort;
      ui.setText(
        "rawPayloadHint",
        raw.length > rawMax ? `показано перші ${rawMax} символів із ${raw.length}` : `розмір: ${raw.length} символів`
      );
    } catch (error) {
      setStatus(`ПОМИЛКА: ${error}`);
    }
  }
  ui.byId("copyPayload").addEventListener("click", () => ui.copyTextWithFallback(ui.byId("rawPayload").textContent || "", "Скопіюйте payload:", "Payload скопійовано", "Payload у prompt"));
  document.getElementById("refresh").addEventListener("click", refresh);
  document.getElementById("btnAck").addEventListener("click", doAck);
  document.getElementById("btnSilence").addEventListener("click", doSilence);
  document.getElementById("btnUnsilence").addEventListener("click", doUnsilence);
  loadWhoami().then(refresh);
  setInterval(() => { if (ui.byId("auto").checked) refresh(); }, 10000);
    """
    return render_admin_shell(
        title="Адмін-панель Passengers — Деталі інциденту",
        header_title="Деталі інциденту",
        chips_html=chips_html,
        toolbar_html=toolbar_html,
        body_html=body_html,
        script=script.replace("__CENTRAL_ID__", json.dumps(central_id)).replace("__INCIDENT_CODE__", json.dumps(code)),
        extra_css=extra_css,
        max_width=1360,
        current_nav="incidents",
    ).strip()
