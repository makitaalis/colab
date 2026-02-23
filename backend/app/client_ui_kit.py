from __future__ import annotations

from html import escape

from app.client_core.navigation import CLIENT_NAV_GROUPS


def _nav_short_label(label: str) -> str:
    parts = [part for part in str(label).split() if part]
    if len(parts) >= 2:
        return (parts[0][:1] + parts[1][:1]).upper()
    if parts:
        return parts[0][:2].upper()
    return "--"

def _base_client_css() -> str:
    return """
    :root {
      --bg0: #f4f8ff;
      --bg1: #ffffff;
      --text: #1e2433;
      --muted: #5f6c85;
      --border: #d7dfef;
      --accent: #1f75ff;
      --accent-soft: #e7f0ff;
      --good: #1f9d63;
      --warn: #c98c00;
      --bad: #cc4242;
      --ctl-h: 34px;
    }
    * { box-sizing: border-box; }
    :focus-visible { outline: 2px solid #2c6ad8; outline-offset: 2px; }
    html, body {
      margin: 0;
      padding: 0;
      background: radial-gradient(1400px 900px at -10% -10%, #eaf2ff 0%, var(--bg0) 48%, #eef3fb 100%);
      color: var(--text);
    }
    body { font-family: "Manrope", "Noto Sans", "Helvetica Neue", sans-serif; }
    a { color: inherit; text-decoration: none; }
    code { font-family: "IBM Plex Mono", "Consolas", monospace; font-size: .92em; }
    .srOnly {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      border: 0;
      white-space: nowrap;
    }
    .skipLink {
      position: fixed;
      top: 8px;
      left: 8px;
      z-index: 9999;
      border: 1px solid #9cb9f0;
      border-radius: 10px;
      padding: 8px 10px;
      background: #fff;
      color: #1a3f7f;
      font-size: 13px;
      transform: translateY(-140%);
      transition: transform .14s ease;
    }
    .skipLink:focus-visible { transform: translateY(0); }

    .clientShell {
      width: min(1460px, calc(100vw - 28px));
      margin: 14px auto;
      display: grid;
      grid-template-columns: 250px 1fr;
      gap: 14px;
    }
    .clientShell.sideCompact { grid-template-columns: 92px 1fr; }
    .clientSide {
      background: linear-gradient(180deg, #f7fbff, #f0f5ff);
      border: 1px solid var(--border);
      border-radius: 18px;
      padding: 14px;
      position: sticky;
      top: 12px;
      height: fit-content;
    }
    .sideTop {
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 8px;
      margin-bottom: 10px;
    }
    .sideBrand { font-size: 14px; font-weight: 800; letter-spacing: .2px; margin-bottom: 2px; }
    .sideHint { font-size: 12px; color: var(--muted); margin-bottom: 12px; }
    .sideHotkeys { font-size: 11px; color: #486191; margin: -6px 0 10px; }
    .sideNavSearchWrap { display: block; margin: 6px 0 10px; }
    .sideNavSearch {
      width: 100%;
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 7px 9px;
      font-size: 13px;
      color: var(--text);
      background: #fff;
      min-height: var(--ctl-h);
    }
    .sideNavSearch::placeholder { color: #7b8aa7; }
    .sideNavFilterStatus { margin-top: 6px; font-size: 11px; color: #486191; }
    .sideNavFilterStatus:empty { display: none; }
    .sideLink.navFilteredOut,
    .sideGroupDetails.navFilteredOut { display: none !important; }
    .sideCompactBtn {
      border: 1px solid var(--border);
      border-radius: 10px;
      background: #fff;
      color: #304669;
      font-size: 12px;
      min-height: var(--ctl-h);
      padding: 6px 10px;
      cursor: pointer;
      transition: border-color .16s ease, transform .12s ease, background .16s ease;
    }
    .sideCompactBtn:hover { border-color: #b9caef; transform: translateY(-1px); background: #fbfdff; }
    .sideGroupDetails {
      border: 1px solid #d9e3f5;
      border-radius: 12px;
      background: #f8fbff;
      margin-bottom: 8px;
      overflow: hidden;
    }
    .sideGroupTitle {
      list-style: none;
      cursor: pointer;
      font-size: 12px;
      color: var(--muted);
      text-transform: uppercase;
      letter-spacing: .4px;
      padding: 8px 10px;
      border-bottom: 1px solid #e4ecfb;
      user-select: none;
      font-weight: 700;
    }
    .sideGroupTitle::-webkit-details-marker { display: none; }
    .sideGroupTitle::before { content: "▸"; margin-right: 6px; color: #6a84b8; }
    .sideGroupDetails[open] .sideGroupTitle::before { content: "▾"; }
    .sideLinks { display: grid; gap: 6px; padding: 8px; }
    .sideLink {
      border: 1px solid var(--border);
      border-radius: 12px;
      padding: 8px 10px;
      background: var(--bg1);
      font-size: 13px;
      color: #2e3850;
      display: flex;
      align-items: center;
      gap: 8px;
      transition: border-color .16s ease, transform .12s ease, background .16s ease;
    }
    .sideLink.tier-sub { margin-left: 8px; border-style: dashed; }
    .sideLinkShort {
      width: 20px;
      height: 20px;
      display: inline-flex;
      align-items: center;
      justify-content: center;
      border-radius: 8px;
      background: #ebf2ff;
      color: #3b5f9f;
      font-size: 11px;
      font-weight: 800;
      flex: 0 0 auto;
    }
    .sideLinkText { white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .sideLink:hover { border-color: #b9caef; transform: translateY(-1px); background: #fbfdff; }
    .sideLink.active {
      border-color: #98bbff;
      background: var(--accent-soft);
      color: #113f8b;
      font-weight: 700;
    }

    .clientShell.sideCompact .sideHint,
    .clientShell.sideCompact .sideHotkeys,
    .clientShell.sideCompact .sideNavSearchWrap,
    .clientShell.sideCompact .sideGroupTitle,
    .clientShell.sideCompact .sideLinkText { display: none; }
    .clientShell.sideCompact .sideBrand { font-size: 0; margin-bottom: 0; }
    .clientShell.sideCompact .sideBrand::before {
      content: "PS";
      font-size: 14px;
      font-weight: 800;
      color: #2f4f8a;
    }
    .clientShell.sideCompact .sideGroupDetails {
      border-color: #e7eefc;
      background: #f6f9ff;
      padding: 6px;
    }
    .clientShell.sideCompact .sideLinks { gap: 6px; }
    .clientShell.sideCompact .sideLink { justify-content: center; padding: 7px; }
    .clientShell.sideCompact .sideLinkShort { width: 22px; height: 22px; margin: 0; }
    .clientShell.sideCompact .sideLink.tier-sub { margin-left: 0; border-style: solid; }

    .clientMain {
      background: var(--bg1);
      border: 1px solid var(--border);
      border-radius: 18px;
      overflow: hidden;
    }
    .clientHeader {
      padding: 14px 16px 10px;
      border-bottom: 1px solid var(--border);
      background: linear-gradient(180deg, #ffffff, #f8fbff);
    }
    .clientTitle { font-size: 21px; font-weight: 800; margin: 0; }
    .clientChips, .clientSubnav, .clientToolbar {
      margin-top: 8px;
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }
    .clientChips {
      flex-wrap: nowrap;
      overflow-x: auto;
      overflow-y: hidden;
      padding-bottom: 2px;
      scrollbar-gutter: stable both-edges;
      scrollbar-width: thin;
      scrollbar-color: rgba(31,117,255,.35) rgba(0,0,0,.06);
      -webkit-overflow-scrolling: touch;
    }
    .clientChips .chip { flex: 0 0 auto; }
    .clientSubnav {
      flex-wrap: nowrap;
      overflow-x: auto;
      overflow-y: hidden;
      padding: 6px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #f6f9ff;
      scrollbar-gutter: stable both-edges;
      scrollbar-width: thin;
      scrollbar-color: rgba(31,117,255,.35) rgba(0,0,0,.06);
      -webkit-overflow-scrolling: touch;
      scroll-snap-type: x proximity;
    }
    .clientToolbar {
      flex-direction: column;
      flex-wrap: nowrap;
      align-items: stretch;
      padding: 8px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: #f6f9ff;
    }
    .clientToolbar .toolbarMain,
    .clientToolbar .toolbarMeta {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }
    .clientToolbar .toolbarMeta .status { margin-left: auto; }
    .chip, .metaChip {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      color: var(--muted);
      background: #f9fbff;
    }
    .subnavLink {
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      color: #34538f;
      background: #eef4ff;
      scroll-snap-align: start;
    }
    .subnavLink.active {
      background: #dceaff;
      border-color: #9cb9f8;
      font-weight: 700;
      color: #103b87;
    }
    .clientToolbar input[type="text"],
    .clientToolbar input[type="search"],
    .clientToolbar select {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 7px 9px;
      font-size: 13px;
      color: var(--text);
      background: #fff;
      min-height: var(--ctl-h);
      min-width: 160px;
    }
    .clientToolbar button, .smallbtn {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 7px 10px;
      background: #fff;
      color: #24324f;
      font-size: 13px;
      cursor: pointer;
      min-height: var(--ctl-h);
      font-weight: 700;
      transition: border-color .16s ease, transform .12s ease;
    }
    .clientToolbar button:hover, .smallbtn:hover { border-color: #b5c7ea; transform: translateY(-1px); }
    .clientToolbar button.primary { background: var(--accent); border-color: #1963d7; color: #fff; }
    .status { font-size: 12px; color: var(--muted); }

    .clientBody { padding: 14px 16px 16px; display: grid; gap: 12px; }
    .card {
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 12px;
      background: #fff;
    }
    .sectionTitle { font-size: 14px; font-weight: 800; margin: 0 0 8px; }
    .sectionKicker { margin-top: 6px; font-size: 12px; color: var(--muted); line-height: 1.45; }
    .sectionHead {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 10px;
    }
    .sectionTools {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
    }
    .summary { display: flex; flex-wrap: wrap; gap: 7px; margin: 0 0 10px; }
    .badge {
      display: inline-flex;
      align-items: center;
      border: 1px solid var(--border);
      border-radius: 999px;
      padding: 5px 10px;
      font-size: 12px;
      background: #f8fbff;
      color: #374662;
      font-weight: 700;
    }
    .badge.good { border-color: #89d4b2; color: #116540; background: #ebf8f1; }
    .badge.warn { border-color: #efcf82; color: #8a5d00; background: #fff6e0; }
    .badge.bad { border-color: #efb0b0; color: #8f2424; background: #fff1f1; }

    .tableWrap {
      overflow: auto;
      max-height: 72vh;
      border-radius: 14px;
      border: 1px solid var(--border);
      margin-top: 10px;
      background: linear-gradient(180deg, rgba(255,255,255,.92), rgba(249,252,255,.96));
      scrollbar-gutter: stable both-edges;
      scrollbar-color: rgba(31,117,255,.35) rgba(0,0,0,.06);
      position: relative;
    }
    body.tablesProgressiveOff .progressiveCol { display: none; }
    table {
      width: 100%;
      border-collapse: collapse;
      min-width: 880px;
      font-size: 13px;
      font-variant-numeric: tabular-nums;
    }
    th, td {
      border-bottom: 1px solid #ebeff8;
      padding: 9px 10px;
      text-align: left;
      vertical-align: top;
      line-height: 1.35;
    }
    th {
      background: #f5f8ff;
      color: #4b5d80;
      position: sticky;
      top: 0;
      z-index: 1;
      font-size: 12px;
      letter-spacing: .02em;
      white-space: nowrap;
    }
    tbody tr:nth-child(even) td { background: rgba(31,117,255,.03); }
    tbody tr:hover td { background: rgba(31,117,255,.08); }
    tr.tableEmptyRow td { padding: 18px 12px; }
    .emptyState {
      border: 1px dashed #c9d6ee;
      border-radius: 14px;
      padding: 14px 14px;
      background: #f9fbff;
      color: var(--muted);
    }
    .emptyState.tone-good { border-color: #89d4b2; background: #ebf8f1; }
    .emptyState.tone-warn { border-color: #efcf82; background: #fff6e0; }
    .emptyState.tone-bad { border-color: #efb0b0; background: #fff1f1; }
    .emptyTitle { font-size: 13px; font-weight: 800; letter-spacing: .01em; color: #1f3560; }
    .emptyHint { margin-top: 6px; font-size: 12px; line-height: 1.45; color: var(--muted); }
    .tableWrap::-webkit-scrollbar { height: 10px; width: 10px; }
    .tableWrap::-webkit-scrollbar-thumb {
      background: rgba(31,117,255,.22);
      border-radius: 999px;
      border: 2px solid rgba(0,0,0,0);
      background-clip: padding-box;
    }
    .tableWrap::-webkit-scrollbar-thumb:hover {
      background: rgba(31,117,255,.32);
      border: 2px solid rgba(0,0,0,0);
      background-clip: padding-box;
    }
    .tableWrap::-webkit-scrollbar-track { background: rgba(0,0,0,.04); border-radius: 999px; }

    .mobileHide { display: table-cell; }
    .muted { color: var(--muted); font-size: 12px; }
    .row {
      display: grid;
      grid-template-columns: minmax(160px, 260px) 1fr;
      gap: 10px;
      align-items: center;
      margin: 8px 0;
    }
    .row input, .row select {
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 8px 10px;
      font-size: 13px;
      min-height: var(--ctl-h);
    }
    .toolbar { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; }
    .tableToggle[data-open="0"] { background: #f8fbff; color: #385382; }
    .tableToggle[data-open="1"] { background: #e9f2ff; border-color: #9eb8ea; color: #1f4a91; font-weight: 700; }
    .sectionTitle { font-size: 14px; font-weight: 700; margin-bottom: 8px; }
    .secondaryDetails {
      border: 1px dashed #c9d6ee;
      border-radius: 12px;
      background: #f9fbff;
      padding: 8px 10px;
    }
    .secondaryDetails > summary {
      cursor: pointer;
      font-size: 13px;
      font-weight: 700;
      color: #37548a;
      user-select: none;
    }
    .secondaryDetails > summary::-webkit-details-marker { display: none; }
    .secondaryDetails > summary::before { content: "▸"; margin-right: 6px; color: #6a84b8; }
    .secondaryDetails[open] > summary::before { content: "▾"; }
    .secondaryBody { margin-top: 10px; }

    @media (max-width: 980px) {
      .clientShell { grid-template-columns: 1fr; width: calc(100vw - 18px); margin: 9px auto; }
      .clientShell.sideCompact { grid-template-columns: 1fr; }
      .clientSide { position: static; }
      .clientHeader { padding: 12px; }
      .clientBody { padding: 12px; }
      .row { grid-template-columns: 1fr; }
    }
    @media (max-width: 760px) {
      .clientToolbar .toolbarMain > *,
      .clientToolbar .toolbarMeta > * { flex: 1 1 100%; min-width: 0 !important; }
      .clientToolbar .toolbarMain button,
      .clientToolbar .toolbarMeta button,
      .smallbtn,
      .clientToolbar .toolbarMain select,
      .clientToolbar .toolbarMeta select,
      .clientToolbar .toolbarMain input[type="text"],
      .clientToolbar .toolbarMeta input[type="text"],
      .clientToolbar .toolbarMain input[type="search"],
      .clientToolbar .toolbarMeta input[type="search"] { width: 100%; }
      .clientToolbar .toolbarMeta .status { margin-left: 0; }
      table.mobileFriendly { font-size: 12px; min-width: 640px; }
      table.mobileFriendly th, table.mobileFriendly td { padding: 8px 8px; }
      table.mobileFriendly .mobileHide { display: none; }
    }
    @media (prefers-reduced-motion: reduce) {
      * {
        transition: none !important;
        scroll-behavior: auto !important;
      }
    }
    """.strip()

def _base_client_js() -> str:
    return """
    window.ClientUiKit = (() => {
      const NAV_COMPACT_STORAGE_KEY = "passengers_client_sidebar_compact_v1";
      const NAV_GROUP_STORAGE_PREFIX = "passengers_client_sidebar_group_";
      const TABLE_PROGRESSIVE_STORAGE_KEY = "passengers_client_tables_progressive_v1";
      let suppressGroupStateStore = false;
      const byId = (id) => document.getElementById(id);
      const setText = (id, value) => { const node = byId(id); if (node) node.textContent = String(value ?? ""); };
      const setStatus = (id, value) => {
        const node = byId(id);
        if (!node) return;
        node.setAttribute("role", "status");
        node.setAttribute("aria-live", "polite");
        node.textContent = String(value ?? "");
      };
      const esc = (value) => String(value ?? "").replace(/[&<>"']/g, (char) => (
        {"&":"&amp;","<":"&lt;",">":"&gt;","\"":"&quot;","'":"&#39;"}[char] || char
      ));
      const readBool = (storageKey, fallback = false) => {
        try {
          const raw = String(localStorage.getItem(storageKey) || "").trim().toLowerCase();
          if (!raw) return !!fallback;
          return raw === "1" || raw === "true" || raw === "yes" || raw === "on";
        } catch (_error) {
          return !!fallback;
        }
      };
      const storeBool = (storageKey, value) => {
        const normalized = !!value;
        try { localStorage.setItem(storageKey, normalized ? "1" : "0"); } catch (_error) {}
        return normalized;
      };
      const isElementVisible = (node) => !!(node && node.offsetParent !== null && !node.hasAttribute("disabled"));
      const focusFirst = (selectors) => {
        for (const selector of selectors) {
          const node = document.querySelector(selector);
          if (!(node instanceof HTMLElement)) continue;
          if (!isElementVisible(node)) continue;
          node.focus();
          return true;
        }
        return false;
      };
      const isEditableTarget = (target) => {
        if (!(target instanceof HTMLElement)) return false;
        if (target.isContentEditable) return true;
        const tag = target.tagName.toLowerCase();
        if (tag === "textarea" || tag === "select") return true;
        if (tag !== "input") return false;
        const input = target;
        const kind = String(input.type || "").toLowerCase();
        return kind !== "button" && kind !== "checkbox" && kind !== "radio";
      };
      const debounce = (fn, delay = 240) => {
        let timer = null;
        return (...args) => {
          if (timer) window.clearTimeout(timer);
          timer = window.setTimeout(() => { timer = null; fn(...args); }, delay);
        };
      };
      const bindDebouncedInputs = (ids, handler, delay = 240) => {
        const debounced = debounce(handler, delay);
        for (const id of ids) {
          const node = byId(id);
          if (!node) continue;
          node.addEventListener("input", debounced);
        }
      };
      const bindEnterRefresh = (ids, handler) => {
        for (const id of ids) {
          const node = byId(id);
          if (!node) continue;
          node.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              handler();
            }
          });
        }
      };
      const copyTextWithFallback = async (text, promptText, okText, fallbackText) => {
        const payload = String(text ?? "");
        try {
          if (navigator.clipboard && navigator.clipboard.writeText) {
            await navigator.clipboard.writeText(payload);
            if (okText) window.alert(okText);
            return true;
          }
        } catch (_error) {}
        window.prompt(promptText || "Скопіюйте текст:", payload);
        if (fallbackText) console.info(fallbackText);
        return false;
      };
      const fetchJson = async (path, init = {}) => {
        const response = await fetch(path, init);
        const text = await response.text();
        if (!response.ok) throw new Error(`${response.status} ${text}`);
        return text ? JSON.parse(text) : {};
      };
      const apiGet = async (path) => fetchJson(path);
      const apiPost = async (path, payload) => {
        const init = { method: "POST" };
        if (payload !== null && payload !== undefined) {
          init.headers = { "Content-Type": "application/json" };
          init.body = JSON.stringify(payload);
        }
        return fetchJson(path, init);
      };
      const loadWhoami = async () => {
        try {
          const data = await apiGet("/api/client/whoami");
          return {
            actor: String(data.actor || ""),
            role: String(data.role || "client"),
            scope: data.scope || { central_ids: [], vehicle_ids: [] },
            capabilities: data.capabilities || { read: true, write_profile: true, write_notifications: true, support_console: false },
          };
        } catch (_error) {
          return {
            actor: "",
            role: "client",
            scope: { central_ids: [], vehicle_ids: [] },
            capabilities: { read: true, write_profile: true, write_notifications: true, support_console: false },
          };
        }
      };
      const bindDetailsState = (id, storageKey, defaultOpen = false) => {
        const node = byId(id);
        if (!node) return;
        let current = readBool(storageKey, defaultOpen);
        node.open = !!current;
        node.addEventListener("toggle", () => {
          storeBool(storageKey, node.open);
        });
      };
      const sideGroupStateKey = (groupKey) => `${NAV_GROUP_STORAGE_PREFIX}${String(groupKey || "").trim().toLowerCase()}_v1`;
      const sideGroupNodes = () => Array.from(document.querySelectorAll(".sideGroupDetails[data-side-group]")).filter(
        (node) => node instanceof HTMLDetailsElement
      );
      const applySideGroupsState = (compactMode = false) => {
        suppressGroupStateStore = true;
        try {
          for (const node of sideGroupNodes()) {
            const key = String(node.dataset.sideGroup || "").trim().toLowerCase();
            const defaultOpen = String(node.dataset.defaultOpen || "0").trim() === "1";
            if (compactMode) {
              node.open = true;
              continue;
            }
            node.open = readBool(sideGroupStateKey(key), defaultOpen);
          }
        } finally {
          suppressGroupStateStore = false;
        }
      };
      const bindSideGroupPersistence = () => {
        for (const node of sideGroupNodes()) {
          node.addEventListener("toggle", () => {
            if (suppressGroupStateStore) return;
            const key = String(node.dataset.sideGroup || "").trim().toLowerCase();
            if (!key) return;
            storeBool(sideGroupStateKey(key), node.open);
          });
        }
      };
      const applySideCompactMode = (enabled) => {
        const active = !!enabled;
        const shell = document.querySelector(".clientShell");
        if (shell instanceof HTMLElement) shell.classList.toggle("sideCompact", active);
        const toggle = byId("sideCompactToggle");
        if (toggle) {
          toggle.setAttribute("aria-pressed", active ? "true" : "false");
          toggle.dataset.open = active ? "1" : "0";
          toggle.textContent = active ? "Комфорт" : "Компакт";
          toggle.title = active ? "Розгорнути sidebar" : "Стиснути sidebar";
        }
        applySideGroupsState(active);
        return active;
      };
      const bindSideCompactToggle = () => {
        const toggle = byId("sideCompactToggle");
        if (!toggle) return;
        toggle.addEventListener("click", () => {
          const next = !readBool(NAV_COMPACT_STORAGE_KEY, false);
          storeBool(NAV_COMPACT_STORAGE_KEY, next);
          applySideCompactMode(next);
        });
      };
      const applyProgressiveColumnsMode = (expanded) => {
        const active = !!expanded;
        document.body.classList.toggle("tablesProgressiveOff", !active);
        const toggles = Array.from(document.querySelectorAll(".tableToggle[data-table-toggle='progressive']"));
        for (const node of toggles) {
          if (!(node instanceof HTMLElement)) continue;
          node.dataset.open = active ? "1" : "0";
          node.textContent = active ? "Колонки: детально" : "Колонки: базово";
          node.setAttribute("aria-pressed", active ? "true" : "false");
        }
        return active;
      };
      const bindProgressiveColumnsToggle = () => {
        const toggles = Array.from(document.querySelectorAll(".tableToggle[data-table-toggle='progressive']"));
        for (const node of toggles) {
          if (!(node instanceof HTMLElement)) continue;
          node.addEventListener("click", () => {
            const next = !readBool(TABLE_PROGRESSIVE_STORAGE_KEY, false);
            storeBool(TABLE_PROGRESSIVE_STORAGE_KEY, next);
            applyProgressiveColumnsMode(next);
          });
        }
      };
	      const listVisibleSidebarNavLinks = () => Array.from(
	        document.querySelectorAll(".clientSide .sideLink:not(.navFilteredOut)")
	      ).filter((node) => node instanceof HTMLAnchorElement);
	      const applySidebarNavFilter = (rawValue = "", options = {}) => {
	        const source = options && typeof options === "object" ? options : {};
	        const query = String(rawValue || "").trim().toLowerCase();
	        document.body.classList.toggle("sideSearching", !!query);
	        const linkNodes = Array.from(document.querySelectorAll(".clientSide .sideLink"));
	        let visibleLinks = 0;
	        for (const link of linkNodes) {
	          if (!(link instanceof HTMLAnchorElement)) continue;
	          const label = String(link.textContent || "").trim().toLowerCase();
	          const href = String(link.getAttribute("href") || "").trim().toLowerCase();
	          const matches = !query || label.includes(query) || href.includes(query);
	          link.classList.toggle("navFilteredOut", !matches);
	          link.tabIndex = matches ? 0 : -1;
	          if (matches) visibleLinks += 1;
	        }
	        const groupNodes = sideGroupNodes();
	        let visibleGroups = 0;
	        suppressGroupStateStore = true;
	        try {
	          for (const group of groupNodes) {
	            const hasVisibleLink = !!group.querySelector(".sideLink:not(.navFilteredOut)");
	            const hideGroup = !!query && !hasVisibleLink;
	            group.classList.toggle("navFilteredOut", hideGroup);
	            if (!hideGroup) visibleGroups += 1;
	            if (query) group.open = true;
	          }
	        } finally {
	          suppressGroupStateStore = false;
	        }
	        if (!query) applySideGroupsState(readBool(NAV_COMPACT_STORAGE_KEY, false));
	        const statusNode = byId("clientSideNavFilterStatus");
	        if (statusNode) {
	          statusNode.textContent = query
	            ? `Фільтр: ${query} · links ${visibleLinks} · groups ${visibleGroups}`
	            : "";
	        }
	        if (source.track === true) {
	          const prevQuery = String(source.previous_query || "").trim().toLowerCase();
	          if (query && query !== prevQuery) console.info("client_nav_filter_apply", query);
	          else if (!query && !!prevQuery) console.info("client_nav_filter_clear");
	        }
	      };
	      const bindSidebarNavFilter = () => {
	        const filterNode = byId("clientSideNavFilter");
	        if (!(filterNode instanceof HTMLInputElement)) return;
	        if (filterNode.dataset.bound === "1") return;
	        const runFilter = debounce(() => {
	          const previousQuery = String(filterNode.dataset.lastQuery || "");
	          const nextQuery = String(filterNode.value || "");
	          applySidebarNavFilter(nextQuery, { track: true, source: "input", previous_query: previousQuery });
	          filterNode.dataset.lastQuery = nextQuery;
	        }, 140);
	        filterNode.addEventListener("input", () => runFilter());
	        filterNode.addEventListener("keydown", (event) => {
	          const key = String(event.key || "").trim().toLowerCase();
	          if (key === "escape") {
	            event.preventDefault();
	            const previousQuery = String(filterNode.dataset.lastQuery || filterNode.value || "");
	            filterNode.value = "";
	            applySidebarNavFilter("", { track: true, source: "escape", previous_query: previousQuery });
	            filterNode.dataset.lastQuery = "";
	            return;
	          }
	          if (key === "arrowdown") {
	            const links = listVisibleSidebarNavLinks();
	            if (links.length === 0) return;
	            event.preventDefault();
	            links[0].focus();
	            return;
	          }
	          if (key === "enter") {
	            const query = String(filterNode.value || "").trim();
	            if (!query) return;
	            const links = listVisibleSidebarNavLinks();
	            if (links.length !== 1) return;
	            event.preventDefault();
	            const href = String(links[0].getAttribute("href") || "").trim();
	            if (href) window.location.assign(href);
	          }
	        });
	        filterNode.dataset.bound = "1";
	        filterNode.dataset.lastQuery = String(filterNode.value || "");
	        applySidebarNavFilter(filterNode.value || "");
	      };
	      const bindShellHotkeys = () => {
	        document.addEventListener("keydown", (event) => {
	          const target = event.target;
	          const key = String(event.key || "");
	          if (!event.altKey && !event.shiftKey && key === "/" && !isEditableTarget(target)) {
            event.preventDefault();
            focusFirst([
              ".clientToolbar input[type='search']",
              ".clientToolbar input[type='text']",
              ".clientToolbar select",
            ]);
            return;
          }
          if (key === "Escape" && isEditableTarget(target)) {
            target.blur();
            return;
          }
	          if (!(event.altKey && event.shiftKey)) return;
	          const normalized = key.toLowerCase();
	          if (normalized === "m") {
	            event.preventDefault();
	            byId("sideCompactToggle")?.click();
	            return;
	          }
	          if (normalized === "n") {
	            const searchNode = byId("clientSideNavFilter");
	            if (searchNode instanceof HTMLInputElement && !searchNode.disabled && searchNode.offsetParent !== null) {
	              event.preventDefault();
	              searchNode.focus();
	              searchNode.select();
	            }
	            return;
	          }
	          if (normalized === "k") {
	            event.preventDefault();
	            byId("tableToggle")?.click();
	            return;
	          }
          if (normalized === "s") {
            event.preventDefault();
            focusFirst([".clientSide .sideLink.active", ".clientSide .sideLink"]);
            return;
          }
          if (normalized === "t") {
            event.preventDefault();
            focusFirst([
              ".clientToolbar button.primary",
              ".clientToolbar button",
              ".clientToolbar input[type='search']",
              ".clientToolbar input[type='text']",
              ".clientToolbar select",
            ]);
          }
        });
      };
	      const applyEmptyTables = () => {
	        const wraps = Array.from(document.querySelectorAll(".tableWrap"));
	        for (const wrap of wraps) {
	          if (!(wrap instanceof HTMLElement)) continue;
	          const table = wrap.querySelector("table");
	          if (!(table instanceof HTMLTableElement)) continue;
	          if (table.classList.contains("noEmptyInject")) continue;
	          const tbody = table.querySelector("tbody");
	          let dataRows = [];
	          if (tbody) {
	            dataRows = Array.from(tbody.querySelectorAll("tr")).filter((row) => !row.classList.contains("tableEmptyRow"));
          } else {
            const rows = Array.from(table.querySelectorAll("tr"));
            dataRows = rows.slice(1);
          }
	          const existingEmpty = Array.from(table.querySelectorAll("tr.tableEmptyRow"));
	          if (dataRows.length > 0) {
	            for (const row of existingEmpty) row.remove();
	            continue;
	          }
	          if (existingEmpty.length > 0) continue;
	          const titleText = String(
	            table.getAttribute("data-empty-title")
	            || wrap.getAttribute("data-empty-title")
	            || "Немає даних"
          ).trim();
          const tone = String(
            table.getAttribute("data-empty-tone")
            || wrap.getAttribute("data-empty-tone")
            || "neutral"
          ).trim().toLowerCase();
          const hintText = String(
            table.getAttribute("data-empty-text")
            || wrap.getAttribute("data-empty-text")
            || "Спробуйте змінити фільтри або період."
          ).trim();
          let columnCount = table.querySelectorAll("thead th").length;
          if (!columnCount) {
            const firstRow = table.querySelector("tr");
            if (firstRow) columnCount = Math.max(1, firstRow.children.length);
          }
          const body = tbody || (() => {
            const next = document.createElement("tbody");
            table.appendChild(next);
            return next;
          })();
          const tr = document.createElement("tr");
          tr.className = "tableEmptyRow";
          const td = document.createElement("td");
          td.colSpan = Math.max(1, columnCount || 1);
          const empty = document.createElement("div");
          empty.className = "emptyState";
          if (tone === "good" || tone === "warn" || tone === "bad") {
            empty.classList.add(`tone-${tone}`);
          }
          const title = document.createElement("div");
          title.className = "emptyTitle";
          title.textContent = titleText || "Немає даних";
          const hint = document.createElement("div");
          hint.className = "emptyHint";
          hint.textContent = hintText;
          empty.appendChild(title);
          if (hintText) empty.appendChild(hint);
          td.appendChild(empty);
          tr.appendChild(td);
          body.appendChild(tr);
        }
      };
	      const initShell = () => {
	        bindSideGroupPersistence();
	        bindSideCompactToggle();
	        bindSidebarNavFilter();
	        bindProgressiveColumnsToggle();
	        bindShellHotkeys();
	        applySideCompactMode(readBool(NAV_COMPACT_STORAGE_KEY, false));
	        applyProgressiveColumnsMode(readBool(TABLE_PROGRESSIVE_STORAGE_KEY, false));
	        applyEmptyTables();
	      };
      return {
        byId,
        setText,
        setStatus,
        esc,
        readBool,
        storeBool,
        debounce,
        bindDebouncedInputs,
        bindEnterRefresh,
        copyTextWithFallback,
        fetchJson,
        apiGet,
        apiPost,
        loadWhoami,
        bindDetailsState,
        applyEmptyTables,
        applyProgressiveColumnsMode,
        initShell,
      };
    })();
    """.strip()


def render_client_shell(
    *,
    title: str,
    header_title: str,
    chips_html: str,
    toolbar_html: str,
    body_html: str,
    script: str,
    current_nav: str = "",
    max_width: int = 1180,
    extra_css: str = "",
) -> str:
    current = str(current_nav).strip().lower()
    nav_group_html: list[str] = []
    subnav_links: list[str] = []

    for group_key, group_title, items in CLIENT_NAV_GROUPS:
        links: list[str] = []
        group_active = False
        for key, label, href, tier in items:
            active_class = " active" if current == key else ""
            if current == key:
                group_active = True
            tier_class = f" tier-{escape(tier)}"
            links.append(
                f'<a class="sideLink{tier_class}{active_class}" href="{escape(href, quote=True)}">'
                f'<span class="sideLinkShort">{escape(_nav_short_label(label))}</span>'
                f'<span class="sideLinkText">{escape(label)}</span>'
                "</a>"
            )
        open_attr = " open" if group_active else ""
        nav_group_html.append(
            f'<details class="sideGroupDetails" data-side-group="{escape(group_key)}" data-default-open="{"1" if group_active else "0"}"{open_attr}>'
            f'<summary class="sideGroupTitle">{escape(group_title)}</summary>'
            f'<div class="sideLinks">{"".join(links)}</div>'
            "</details>"
        )
        if group_active:
            for key, label, href, _tier in items:
                active_class = " active" if current == key else ""
                subnav_links.append(
                    f'<a class="subnavLink{active_class}" href="{escape(href, quote=True)}">{escape(label)}</a>'
                )

    if not subnav_links:
        for _group_key, _group_title, items in CLIENT_NAV_GROUPS[:1]:
            for key, label, href, _tier in items:
                active_class = " active" if current == key else ""
                subnav_links.append(
                    f'<a class="subnavLink{active_class}" href="{escape(href, quote=True)}">{escape(label)}</a>'
                )

    css = _base_client_css()
    if extra_css.strip():
        css += "\n" + extra_css.strip()
    style = f".clientShell{{width:min({int(max_width)}px,calc(100vw - 28px));}}"
    js = _base_client_js()
    safe_title = escape(title)
    safe_header = escape(header_title)

    ui_build = "2026-02-18-pack33"
    return f"""<!doctype html>
	<html lang="uk">
	<head>
	  <meta charset="utf-8" />
	  <meta name="viewport" content="width=device-width, initial-scale=1" />
	  <title>{safe_title}</title>
	  <style>{css}\n{style}</style>
	</head>
	<body data-ui-build="{ui_build}">
	  <a class="skipLink" href="#clientMainContent">Перейти до основного контенту</a>
	  <div class="clientShell">
	    <aside class="clientSide" aria-label="Навігація клієнтської панелі">
		      <div class="sideTop">
		        <div>
	          <div class="sideBrand">Passengers • Кабінет</div>
	          <div class="sideHint">Меню та підменю</div>
	          <div class="sideHotkeys">⌨ `/` пошук · `Alt+Shift+N` меню · `Alt+Shift+M` компакт · `Alt+Shift+K` колонки</div>
	          <label class="sideNavSearchWrap" for="clientSideNavFilter">
	            <input id="clientSideNavFilter" class="sideNavSearch" type="search" placeholder="Пошук меню" aria-label="Пошук по меню" aria-describedby="clientSideNavFilterStatus" />
	          </label>
	          <div id="clientSideNavFilterStatus" class="sideNavFilterStatus" aria-live="polite"></div>
	        </div>
	        <button id="sideCompactToggle" class="sideCompactBtn" type="button" aria-pressed="false" title="Стиснути sidebar">Компакт</button>
	      </div>
      {"".join(nav_group_html)}
    </aside>
    <main class="clientMain" id="clientMainContent" tabindex="-1">
      <header class="clientHeader">
        <h1 class="clientTitle">{safe_header}</h1>
        <div class="clientChips">{chips_html}</div>
        <div class="clientSubnav">{"".join(subnav_links)}</div>
        <div class="clientToolbar">{toolbar_html}</div>
      </header>
      <section class="clientBody">{body_html}</section>
    </main>
  </div>
  <script>{js}</script>
  <script>window.ClientUiKit.initShell();</script>
  <script>{script}</script>
</body>
</html>""".strip()
