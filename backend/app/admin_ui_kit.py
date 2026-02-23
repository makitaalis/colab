from __future__ import annotations

import re
from html import escape

from app.admin_core.navigation import (
    ADMIN_NAV_GROUPS,
    ADMIN_NAV_WORKFLOW,
    render_page_subnav,
)


def base_admin_css() -> str:
    return """
	    :root {
	      --bg: #0b1020;
	      --panel: #111a33;
	      --surface: rgba(255,255,255,.03);
	      --surface-strong: rgba(255,255,255,.06);
	      --muted: #9aa7c1;
	      --text: #e8eefc;
	      --border: rgba(255,255,255,.10);
	      --focus: rgba(127,176,255,.55);
	      --good: #28d17c;
	      --warn: #f2c94c;
	      --bad: #ff5d5d;
	      --btn: rgba(255,255,255,.06);
	      --btn2: rgba(127,176,255,.14);
	      --link: #7fb0ff;
	      --ctl-h: 34px;
	    }
    * { box-sizing: border-box; }
    body {
      font-family: system-ui, -apple-system, Segoe UI, Roboto, Ubuntu, Cantarell, Noto Sans, Arial, sans-serif;
      margin: 0;
      line-height: 1.4;
      background:
        radial-gradient(1100px 520px at 14% -6%, rgba(127,176,255,.14), transparent 52%),
        radial-gradient(1000px 500px at 88% -8%, rgba(40,209,124,.08), transparent 60%),
        var(--bg);
      color: var(--text);
    }
    .toast {
      position: fixed;
      right: 14px;
      bottom: 14px;
      z-index: 9999;
      max-width: min(560px, calc(100vw - 28px));
      border-radius: 14px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(17,26,51,.92);
      box-shadow: 0 14px 44px rgba(0,0,0,.35);
      padding: 10px 12px;
      font-size: 12px;
      color: #e8eefc;
      white-space: pre-wrap;
    }
    .toast .toastTitle { font-weight: 800; letter-spacing: .02em; margin-bottom: 4px; }
    .toast .toastBody { color: #c9d7f1; }
    .toast .toastClose {
      float: right;
      margin-left: 10px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(255,255,255,.04);
      color: #dbe7fd;
      border-radius: 999px;
      padding: 2px 8px;
      font-size: 11px;
      cursor: pointer;
    }
    .toast .toastClose:hover { border-color: rgba(127,176,255,.44); background: rgba(127,176,255,.12); }
	    a { color: var(--link); text-decoration: none; transition: color .18s ease; }
	    a:hover { color: #a6c7ff; }
	    a:focus-visible {
	      outline: 2px solid rgba(127,176,255,.55);
	      outline-offset: 2px;
	      border-radius: 8px;
	    }
	    button:focus-visible,
	    summary:focus-visible,
	    input:focus-visible,
	    select:focus-visible,
	    textarea:focus-visible {
	      outline: 2px solid rgba(127,176,255,.55);
	      outline-offset: 2px;
	    }
    .wrap { margin: 0 auto; padding: 22px 18px 60px; }
    .appShell {
      display: grid;
      grid-template-columns: 248px minmax(0, 1fr);
      gap: 14px;
      align-items: start;
      transition: grid-template-columns .18s ease;
    }
    .mainPane { min-width: 0; }
    .sideNav {
      position: sticky;
      top: 14px;
      border: 1px solid var(--border);
      border-radius: 16px;
      background: rgba(17,26,51,.82);
      box-shadow: 0 10px 30px rgba(0,0,0,.22);
      padding: 12px;
      transition: padding .18s ease, border-color .18s ease, background .18s ease;
    }
    .sideBrand {
      font-size: 13px;
      font-weight: 700;
      letter-spacing: .02em;
      color: #d6e3fb;
      margin-bottom: 10px;
      padding: 0 4px;
    }
    .sideNavTools {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      align-items: center;
      margin: 0 2px 8px;
    }
    .sideNavSearchWrap {
      display: block;
      grid-column: 1 / -1;
    }
    .sideNavSearch {
      width: 100%;
      min-height: 30px;
      border-radius: 9px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.03);
      color: #dbe7fd;
      font-size: 12px;
      padding: 6px 9px;
      transition: border-color .18s ease, background .18s ease, box-shadow .18s ease;
    }
    .sideNavSearch::placeholder {
      color: #9fb0cf;
    }
    .sideNavSearch:focus {
      outline: none;
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.10);
      box-shadow: 0 0 0 2px rgba(127,176,255,.20);
    }
    .sideNavCompactBtn {
      min-height: 30px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.03);
      color: #c9d7f1;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .03em;
      padding: 4px 10px;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease;
    }
    .sideNavModeBtn {
      min-height: 30px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.03);
      color: #c9d7f1;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .03em;
      padding: 4px 10px;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease;
    }
    .sideNavFocusBtn {
      min-height: 30px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.03);
      color: #c9d7f1;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .03em;
      padding: 4px 10px;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease;
    }
    .sideNavHelpBtn {
      min-height: 30px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.03);
      color: #c9d7f1;
      font-size: 11px;
      font-weight: 700;
      letter-spacing: .03em;
      padding: 4px 10px;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease;
    }
    .sideNavHelpBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
    }
    .sideNavHelpBtn[aria-expanded="true"] {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
      color: #e7f0ff;
    }
    .sideNavCompactBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
    }
    .sideNavModeBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
    }
    .sideNavFocusBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
    }
    .sideNavCompactBtn[aria-pressed="true"] {
      border-color: rgba(40,209,124,.45);
      background: rgba(40,209,124,.14);
      color: #dff8ea;
    }
    .sideNavModeBtn[aria-pressed="true"] {
      border-color: rgba(127,176,255,.55);
      background: rgba(127,176,255,.18);
      color: #e7f0ff;
    }
    .sideNavFocusBtn[aria-pressed="true"] {
      border-color: rgba(40,209,124,.45);
      background: rgba(40,209,124,.14);
      color: #dff8ea;
    }
    .sideNavFilterStatus {
      margin: 0 4px 8px;
      color: #9fb0cf;
      font-size: 10px;
      letter-spacing: .03em;
      min-height: 14px;
    }
    .sideNavOnboarding {
      margin: 0 2px 8px;
      border: 1px solid rgba(127,176,255,.26);
      border-radius: 10px;
      background: rgba(127,176,255,.08);
      padding: 8px;
    }
    .sideNavOnboarding[hidden] {
      display: none !important;
    }
    .sideNavOnboardingTitle {
      margin: 0;
      font-size: 11px;
      color: #d7e7ff;
      font-weight: 700;
      letter-spacing: .03em;
      text-transform: uppercase;
    }
    .sideNavOnboardingList {
      margin: 6px 0 0;
      padding-left: 16px;
      color: #c8d9f7;
      font-size: 11px;
      line-height: 1.35;
    }
    .sideNavOnboardingFoot {
      margin-top: 8px;
      display: flex;
      justify-content: flex-end;
    }
    .sideNavOnboardingDismiss {
      min-height: 24px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(255,255,255,.05);
      color: #dbe8ff;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 10px;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease;
    }
    .sideNavOnboardingDismiss:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
    }
    .sideList {
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .sideLinkWrap {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      gap: 6px;
      align-items: center;
    }
    .sideLinkWrap.noPin {
      grid-template-columns: minmax(0, 1fr);
    }
    .sideHint {
      font-size: 11px;
      color: var(--muted);
      letter-spacing: .04em;
      text-transform: uppercase;
      margin: 0 4px 8px;
    }
    .sideJumpRow {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      margin-bottom: 10px;
    }
    .sideJump {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 28px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.12);
      background: rgba(255,255,255,.03);
      color: #c9d7f1;
      font-size: 11px;
      font-weight: 700;
      transition: border-color .18s ease, background .18s ease, transform .12s ease, color .18s ease;
    }
    .sideJump:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
      transform: translateY(-1px);
    }
    .sideJump.active {
      border-color: rgba(40,209,124,.45);
      background: rgba(40,209,124,.16);
      color: #dff8ea;
    }
    .sideGroups {
      display: flex;
      flex-direction: column;
      gap: 10px;
    }
    .sideGroup {
      border: 1px solid rgba(255,255,255,.08);
      border-radius: 12px;
      background: rgba(255,255,255,.02);
      padding: 8px;
    }
    .sideGroup.active {
      border-color: rgba(127,176,255,.34);
      background: rgba(127,176,255,.08);
    }
    .sideGroup.collapsed .sideList {
      display: none;
    }
    .sideJump.navFilteredOut,
    .sideGroup.navFilteredOut,
    .sideLinkWrap.navFilteredOut {
      display: none !important;
    }
    .sideGroupHead {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 6px;
    }
    .sideGroupTitle {
      width: 100%;
      display: inline-flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 9px;
      background: rgba(255,255,255,.03);
      padding: 4px 8px;
      font-size: 11px;
      color: #c5d5f2;
      letter-spacing: .04em;
      text-transform: uppercase;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease;
    }
    .sideGroupTitle:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
    }
    .sideGroupChevron {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      width: 14px;
      font-size: 11px;
      transition: transform .18s ease;
    }
    .sideGroup.collapsed .sideGroupChevron {
      transform: rotate(-90deg);
    }
    .sideLink {
      display: flex;
      align-items: center;
      min-height: 36px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,.10);
      background: rgba(255,255,255,.02);
      color: #c9d7f1;
      font-size: 13px;
      font-weight: 600;
      padding: 7px 10px;
      transition: border-color .18s ease, background .18s ease, transform .12s ease, color .18s ease;
    }
    .sideLink:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
      transform: translateY(-1px);
    }
    .sideLinkHub {
      border-color: rgba(127,176,255,.22);
      background: rgba(127,176,255,.08);
      font-weight: 700;
    }
    .sideLinkSub {
      min-height: 32px;
      margin-left: 12px;
      padding: 6px 9px 6px 11px;
      border-style: dashed;
      background: rgba(255,255,255,.01);
      font-size: 12px;
      font-weight: 600;
    }
    .sideLink.active {
      border-color: rgba(40,209,124,.45);
      background: rgba(40,209,124,.14);
      color: #dff8ea;
    }
    .sideLink.trail {
      border-color: rgba(127,176,255,.28);
      background: rgba(127,176,255,.10);
      color: #dbe6fb;
    }
    .sideLabel {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
      padding-right: 8px;
    }
    .sideLinkSub .sideLabel::before {
      content: "•";
      display: inline-flex;
      margin-right: 6px;
      color: #8fa6cc;
    }
    .sideStep {
      border: 1px solid rgba(255,255,255,.16);
      border-radius: 999px;
      padding: 1px 6px;
      font-size: 10px;
      letter-spacing: .04em;
      color: #d4e1fb;
      background: rgba(255,255,255,.05);
      white-space: nowrap;
    }
    .sideLink.active .sideStep {
      border-color: rgba(40,209,124,.45);
      background: rgba(40,209,124,.16);
      color: #dff8ea;
    }
    .sidePin {
      width: 28px;
      min-height: 28px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.03);
      color: #c9d7f1;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, transform .12s ease, color .18s ease;
    }
    .sidePin:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
      transform: translateY(-1px);
    }
    .sidePin.active {
      border-color: rgba(242,201,76,.52);
      background: rgba(242,201,76,.18);
      color: #ffe7ae;
    }
    .sideMiniHead {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-top: 8px;
    }
    .sideMiniHeadActions {
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .sideMiniToggle {
      width: 26px;
      min-height: 26px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.03);
      color: #c9d7f1;
      font-size: 12px;
      font-weight: 900;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease, transform .12s ease;
    }
    .sideMiniToggle:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
      transform: translateY(-1px);
    }
    .sideMiniChevron {
      display: inline-block;
      transition: transform .16s ease;
    }
    .sideMiniSection.collapsed .sideMiniChevron {
      transform: rotate(-90deg);
    }
    .sideMiniBody[hidden] { display: none !important; }
    .sideMiniList {
      display: flex;
      flex-direction: column;
      gap: 6px;
      margin-top: 6px;
    }
    .sideMiniLink {
      display: inline-flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      min-height: 30px;
      border-radius: 9px;
      border: 1px solid rgba(255,255,255,.10);
      background: rgba(255,255,255,.02);
      color: #cad8f2;
      font-size: 12px;
      font-weight: 600;
      padding: 5px 8px;
      transition: border-color .18s ease, background .18s ease, transform .12s ease, color .18s ease;
    }
    .sideMiniLink:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
      transform: translateY(-1px);
    }
    .sideMiniLink.active {
      border-color: rgba(40,209,124,.45);
      background: rgba(40,209,124,.16);
      color: #dff8ea;
    }
    .sideMiniHotkey {
      border: 1px solid rgba(255,255,255,.16);
      border-radius: 999px;
      padding: 1px 6px;
      font-size: 10px;
      letter-spacing: .03em;
      color: #d4e1fb;
      background: rgba(255,255,255,.04);
      white-space: nowrap;
    }
    .sideSessionMeta {
      font-size: 10px;
      color: #c7d5f0;
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 999px;
      padding: 1px 6px;
      background: rgba(255,255,255,.03);
      white-space: nowrap;
    }
    .sideMiniRow {
      display: grid;
      grid-template-columns: minmax(0, 1fr) auto;
      align-items: center;
      gap: 6px;
    }
    .sideMiniActions {
      display: inline-flex;
      gap: 4px;
    }
    .sideMiniAction {
      width: 22px;
      min-height: 22px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.03);
      color: #c9d7f1;
      font-size: 10px;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease;
    }
    .sideMiniAction:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
    }
    .sideMiniAction:disabled {
      opacity: .45;
      cursor: default;
      transform: none;
    }
    .sideMiniEmpty {
      display: inline-flex;
      align-items: center;
      min-height: 28px;
      color: var(--muted);
      border: 1px dashed rgba(255,255,255,.18);
      border-radius: 9px;
      padding: 4px 8px;
      font-size: 11px;
    }
    .sideMiniBtn {
      min-height: 24px;
      border-radius: 999px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.03);
      color: #c9d7f1;
      font-size: 10px;
      font-weight: 700;
      padding: 2px 8px;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease;
    }
    .sideMiniBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
    }
    .sideMiniSection {
      margin-top: 6px;
    }
    .sideNav.compact {
      padding: 9px;
    }
    .sideNav.compact .sideBrand {
      margin-bottom: 8px;
      font-size: 12px;
    }
    .sideNav.compact .sideHint {
      margin-bottom: 6px;
    }
    .sideNav.compact .sideJump {
      min-height: 26px;
      font-size: 10px;
    }
    .sideNav.compact .sideGroup {
      padding: 6px;
    }
    .sideNav.compact .sideGroupTitle {
      padding: 4px 7px;
      font-size: 10px;
    }
    .sideNav.compact .sideLink {
      min-height: 32px;
      font-size: 12px;
      padding: 6px 8px;
    }
    .sideNav.compact .sideLinkSub {
      min-height: 28px;
      margin-left: 10px;
      padding-left: 8px;
      font-size: 11px;
    }
    .sideNav.compact .sidePin {
      width: 24px;
      min-height: 24px;
      font-size: 12px;
    }
    .sideNav.compact .sideMiniSection[data-side-mini="cheat"] {
      display: none;
    }
    .sideHub {
      margin-top: 8px;
      border: 1px solid rgba(127,176,255,.22);
      border-radius: 11px;
      background: rgba(127,176,255,.08);
      padding: 8px;
    }
    .sideMissionGrid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
      margin-top: 6px;
    }
    .sideMissionCard {
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 9px;
      background: rgba(255,255,255,.04);
      padding: 6px;
    }
    .sideMissionCard strong {
      display: block;
      font-size: 15px;
      line-height: 1.2;
      color: #e9f1ff;
    }
    .sideMissionCard span {
      display: block;
      margin-top: 3px;
      font-size: 10px;
      color: #c9d7ef;
      letter-spacing: .02em;
    }
    .sideMissionCard.bad {
      border-color: rgba(255,93,93,.42);
      background: rgba(255,93,93,.10);
    }
    .sideMissionCard.warn {
      border-color: rgba(242,201,76,.42);
      background: rgba(242,201,76,.12);
    }
    .sideMissionCard.good {
      border-color: rgba(40,209,124,.42);
      background: rgba(40,209,124,.10);
    }
    .sideMissionPresets {
      margin-top: 6px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .sideMissionPresetBtn {
      min-height: 28px;
      border-radius: 9px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.05);
      color: #dbe7fc;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease, transform .12s ease;
    }
    .sideMissionPresetBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
      color: #edf4ff;
      transform: translateY(-1px);
    }
    .sideMissionStatus {
      margin-top: 6px;
      font-size: 10px;
      color: #c9d7ef;
    }
    .sideChecklistRow {
      margin-top: 6px;
      display: flex;
      flex-wrap: wrap;
      gap: 4px;
      align-items: center;
    }
    .sideChecklistBadge {
      border: 1px solid rgba(255,255,255,.16);
      border-radius: 999px;
      padding: 1px 7px;
      font-size: 10px;
      letter-spacing: .02em;
      color: #d5e2fb;
      background: rgba(255,255,255,.04);
    }
    .sideChecklistBadge.done {
      border-color: rgba(40,209,124,.44);
      background: rgba(40,209,124,.15);
      color: #dff8ea;
    }
    .sideChecklistBadge.current {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
      color: #e4eeff;
    }
    .sideChecklistBadge.next {
      border-color: rgba(242,201,76,.44);
      background: rgba(242,201,76,.15);
      color: #ffe8ad;
    }
    .sideMissionPlaybooks {
      margin-top: 6px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .sidePlaybookRow {
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 9px;
      background: rgba(255,255,255,.04);
      padding: 6px;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    .sidePlaybookRow.done {
      border-color: rgba(40,209,124,.35);
      background: rgba(40,209,124,.10);
    }
    .sidePlaybookRow.current {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.14);
    }
    .sidePlaybookRow.next {
      border-color: rgba(242,201,76,.44);
      background: rgba(242,201,76,.14);
    }
    .sidePlaybookHead {
      display: flex;
      align-items: baseline;
      justify-content: space-between;
      gap: 6px;
      font-size: 11px;
      color: #e7efff;
    }
    .sidePlaybookMeta {
      font-size: 10px;
      color: #bfd0ef;
      letter-spacing: .02em;
    }
    .sidePlaybookHint {
      font-size: 10px;
      color: #c9d7ef;
      line-height: 1.3;
    }
    .sidePlaybookBtn {
      min-height: 24px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.05);
      color: #dbe7fc;
      font-size: 10px;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease, transform .12s ease;
    }
    .sidePlaybookBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
      color: #edf4ff;
      transform: translateY(-1px);
    }
    .sidePlaybookBtn:disabled {
      opacity: .48;
      cursor: default;
      transform: none;
    }
    .sideMissionChain {
      margin-top: 6px;
      border: 1px dashed rgba(255,255,255,.20);
      border-radius: 9px;
      padding: 6px;
      display: flex;
      flex-direction: column;
      gap: 6px;
      background: rgba(255,255,255,.02);
    }
    .sideMissionChainTitle {
      font-size: 10px;
      color: #c9d7ef;
      text-transform: uppercase;
      letter-spacing: .03em;
    }
    .sideMissionChainText {
      font-size: 11px;
      color: #e7efff;
      line-height: 1.3;
    }
    .sideMissionChainBtn {
      min-height: 26px;
      border-radius: 9px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.05);
      color: #dbe7fc;
      font-size: 10px;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease, transform .12s ease;
    }
    .sideMissionChainBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
      color: #edf4ff;
      transform: translateY(-1px);
    }
    .sideSnapshotBox {
      margin-top: 6px;
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 9px;
      background: rgba(255,255,255,.03);
      padding: 6px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .sideSnapshotTools {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 6px;
    }
    .sideSnapshotTools.two {
      grid-template-columns: repeat(2, minmax(0, 1fr));
    }
    .sideSnapshotTools.one {
      grid-template-columns: minmax(0, 1fr);
    }
    .sideSnapshotBtn {
      min-height: 24px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.05);
      color: #dbe7fc;
      font-size: 10px;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease, transform .12s ease;
    }
    .sideSnapshotBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
      color: #edf4ff;
      transform: translateY(-1px);
    }
    .sideSnapshotBtn:disabled {
      opacity: .48;
      cursor: default;
      transform: none;
    }
    .sideSnapshotBtn.primary {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.18);
      color: #edf4ff;
    }
    .sideSnapshotBtn.primary:hover {
      border-color: rgba(160,200,255,.62);
      background: rgba(127,176,255,.28);
    }
    .sideSnapshotSummary {
      font-size: 10px;
      color: #c9d7ef;
      line-height: 1.35;
      white-space: pre-line;
    }
    .sideSnapshotSection {
      margin-top: 2px;
      font-size: 10px;
      color: #c4d4f0;
      letter-spacing: .03em;
      text-transform: uppercase;
    }
    .sideDeliverySticky {
      display: none;
    }
    .sideSlaRow {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .sideSlaBadge {
      border: 1px solid rgba(255,255,255,.18);
      border-radius: 999px;
      padding: 1px 8px;
      font-size: 10px;
      font-weight: 700;
      letter-spacing: .03em;
      color: #deebff;
      background: rgba(255,255,255,.04);
      text-transform: uppercase;
    }
    .sideSlaBadge.fresh {
      border-color: rgba(40,209,124,.44);
      background: rgba(40,209,124,.15);
      color: #dff8ea;
    }
    .sideSlaBadge.warn {
      border-color: rgba(242,201,76,.44);
      background: rgba(242,201,76,.15);
      color: #ffe8ad;
    }
    .sideSlaBadge.stale {
      border-color: rgba(255,93,93,.44);
      background: rgba(255,93,93,.13);
      color: #ffd1d1;
    }
    .sideSlaMeta {
      font-size: 10px;
      color: #bfd0ef;
      letter-spacing: .02em;
    }
    .sideSlaReason {
      margin-top: 3px;
      font-size: 10px;
      color: #dbe8ff;
      line-height: 1.3;
    }
    .sideSuggestRow {
      display: flex;
      align-items: center;
      gap: 6px;
      flex-wrap: wrap;
    }
    .sideSuggestBadge {
      border: 1px solid rgba(127,176,255,.42);
      border-radius: 999px;
      padding: 1px 8px;
      font-size: 10px;
      font-weight: 700;
      color: #dfeaff;
      background: rgba(127,176,255,.14);
      letter-spacing: .02em;
    }
    .sideSuggestReason {
      margin-top: 3px;
      font-size: 10px;
      color: #d9e7ff;
      line-height: 1.3;
    }
    .sideRoutingSelect {
      width: 100%;
      min-height: 26px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(11,16,32,.62);
      color: #e8f0ff;
      font-size: 11px;
      padding: 4px 6px;
    }
    .sideRoutingSelect:focus {
      outline: none;
      border-color: rgba(127,176,255,.55);
      box-shadow: 0 0 0 2px rgba(127,176,255,.18);
    }
    .sideRoutingRow {
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .sideRoutingLabel {
      font-size: 10px;
      color: #c6d6f2;
      letter-spacing: .03em;
      text-transform: uppercase;
    }
    .sideHandoffBox {
      margin-top: 6px;
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 9px;
      background: rgba(255,255,255,.03);
      padding: 6px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .sideHandoffInput {
      width: 100%;
      min-height: 72px;
      resize: vertical;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(11,16,32,.65);
      color: #e9f1ff;
      font-size: 11px;
      line-height: 1.35;
      padding: 6px 8px;
    }
    .sideHandoffInput:focus {
      outline: none;
      border-color: rgba(127,176,255,.55);
      box-shadow: 0 0 0 2px rgba(127,176,255,.18);
    }
    .sideHandoffTools {
      display: grid;
      grid-template-columns: repeat(3, minmax(0, 1fr));
      gap: 6px;
    }
    .sideHandoffBtn {
      min-height: 24px;
      border-radius: 8px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.05);
      color: #dbe7fc;
      font-size: 10px;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease, transform .12s ease;
    }
    .sideHandoffBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
      color: #edf4ff;
      transform: translateY(-1px);
    }
    .sideHandoffBtn.active,
    .sideHandoffBtn[aria-pressed="true"] {
      border-color: rgba(127,176,255,.60);
      background: rgba(127,176,255,.22);
      color: #f2f7ff;
    }
    .sideHandoffMeta {
      font-size: 10px;
      color: #c9d7ef;
    }
    .sideHandoffAdoption {
      border: 1px dashed rgba(255,255,255,.20);
      border-radius: 8px;
      background: rgba(255,255,255,.02);
      padding: 5px 6px;
      white-space: pre-line;
      line-height: 1.35;
    }
    .sideHandoffQualityText {
      margin-top: 6px;
      font-size: 10px;
      color: #c9d7ef;
    }
    .sideHandoffQualityBadges {
      margin-top: 6px;
      display: flex;
      flex-wrap: wrap;
      gap: 6px;
    }
    .sideHandoffTimeline {
      margin-top: 2px;
      display: flex;
      flex-direction: column;
      gap: 5px;
    }
    .sideHandoffTimelineRow {
      border: 1px dashed rgba(255,255,255,.20);
      border-radius: 8px;
      padding: 5px 6px;
      background: rgba(255,255,255,.02);
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .sideHandoffTimelineMeta {
      font-size: 10px;
      color: #bfd0ef;
      letter-spacing: .02em;
      display: flex;
      justify-content: space-between;
      gap: 6px;
    }
    .sideHandoffTimelineBody {
      font-size: 10px;
      color: #e7efff;
      line-height: 1.35;
      white-space: pre-line;
    }
    .sideFocusBox {
      margin-top: 6px;
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 9px;
      background: rgba(255,255,255,.03);
      padding: 6px;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }
    .sideFocusTitle {
      font-size: 10px;
      color: #c9d7ef;
      letter-spacing: .03em;
      text-transform: uppercase;
    }
    .sideFocusValue {
      font-size: 12px;
      color: #ecf3ff;
      line-height: 1.3;
    }
    .sideFocusActions {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
    }
    .sideFocusBtn {
      min-height: 26px;
      border-radius: 9px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.05);
      color: #dbe7fc;
      font-size: 10px;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease, transform .12s ease;
    }
    .sideFocusBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
      color: #edf4ff;
      transform: translateY(-1px);
    }
    .sideFocusBtn.full {
      grid-column: 1 / -1;
    }
    .sideHubHint {
      margin: 0 0 6px;
      font-size: 10px;
      color: #cbd9f4;
      letter-spacing: .03em;
      text-transform: uppercase;
    }
    .sideHubGrid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 6px;
    }
    .sideHubBtn {
      min-height: 28px;
      border-radius: 9px;
      border: 1px solid rgba(255,255,255,.14);
      background: rgba(255,255,255,.05);
      color: #d7e3fb;
      font-size: 11px;
      font-weight: 700;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, color .18s ease, transform .12s ease;
    }
    .sideHubBtn:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.16);
      color: #ecf4ff;
      transform: translateY(-1px);
    }
    .sideHubBtn:active {
      transform: translateY(0);
    }
    .sideHubBtn.full {
      grid-column: 1 / -1;
    }
    .sideFocusState {
      margin-top: 6px;
      font-size: 10px;
      color: #cad8f1;
      letter-spacing: .02em;
    }
    .sideCheatList {
      display: grid;
      grid-template-columns: minmax(0, 1fr);
      gap: 6px;
      margin-top: 6px;
    }
    .sideCheatRow {
      display: grid;
      grid-template-columns: auto minmax(0, 1fr);
      align-items: center;
      gap: 6px;
      border: 1px dashed rgba(255,255,255,.18);
      border-radius: 9px;
      padding: 4px 6px;
      font-size: 11px;
      color: #ccd9f2;
    }
    .sideCheatRow code {
      font-size: 10px;
      border: 1px solid rgba(255,255,255,.16);
      border-radius: 999px;
      padding: 1px 6px;
      background: rgba(255,255,255,.04);
      color: #e6efff;
      white-space: nowrap;
    }
    body.sidebar-focus .appShell {
      grid-template-columns: 220px minmax(0, 1fr);
    }
    body.sidebar-focus .sideNav {
      padding: 10px;
      border-color: rgba(127,176,255,.24);
    }
    body.sidebar-focus .sideBrand {
      margin-bottom: 6px;
    }
    body.sidebar-focus .sideJumpRow,
    body.sidebar-focus .sideMiniSection[data-side-mini="quick"],
    body.sidebar-focus .sideMiniSection[data-side-mini="hub"],
    body.sidebar-focus .sideMiniSection[data-side-mini="mission"],
    body.sidebar-focus .sideMiniSection[data-side-mini="cheat"],
    body.sidebar-focus .sideMiniSection[data-side-mini="favorites"],
    body.sidebar-focus .sideMiniSection[data-side-mini="recent"],
    body.sidebar-focus .sideMiniSection[data-side-mini="session"] {
      display: none;
    }
    body.sidebar-focus .sideHub {
      margin-top: 4px;
      background: rgba(127,176,255,.10);
    }
    body.sidebar-focus .sideCheatList {
      display: none;
    }
    body.sidebar-simple .sideNav .sideMiniSection[data-side-mini="quick"],
    body.sidebar-simple .sideNav .sideMiniSection[data-side-mini="hub"],
    body.sidebar-simple .sideNav .sideMiniSection[data-side-mini="mission"],
    body.sidebar-simple .sideNav .sideMiniSection[data-side-mini="cheat"],
    body.sidebar-simple .sideNav .sideMiniSection[data-side-mini="favorites"],
    body.sidebar-simple .sideNav .sideMiniSection[data-side-mini="recent"],
    body.sidebar-simple .sideNav .sideMiniSection[data-side-mini="session"] {
      display: none;
    }
    body.sidebar-simple:not(.sidebar-searching) .sideLinkWrap[data-nav-tier="sub"]:not(.active) {
      display: none;
    }
    body.sidebar-simple .sideGroupChevron {
      display: none;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
      margin-bottom: 14px;
    }
	    .title {
	      display: flex;
	      align-items: center;
	      gap: 10px;
	      flex-wrap: wrap;
	      min-width: 260px;
	      flex: 1 1 520px;
	    }
	    .title h1 { margin: 0; font-size: 20px; }
	    .headerChips {
	      display: flex;
	      align-items: center;
	      gap: 6px;
	      flex-wrap: nowrap;
	      overflow-x: auto;
	      overflow-y: hidden;
	      padding-bottom: 2px;
	      min-width: min(340px, 100%);
	      max-width: 100%;
	      scrollbar-gutter: stable both-edges;
	      scrollbar-width: thin;
	      scrollbar-color: rgba(127,176,255,.34) rgba(255,255,255,.04);
	      -webkit-overflow-scrolling: touch;
	    }
	    .headerChips .chip { flex: 0 0 auto; }
    .chip {
      font-size: 12px;
      color: var(--muted);
      border: 1px solid var(--border);
      padding: 3px 8px;
      border-radius: 999px;
      background: var(--surface);
      transition: border-color .18s ease, color .18s ease, background .18s ease;
    }
    .chip:hover { border-color: rgba(127,176,255,.35); color: #c8d6ee; background: rgba(127,176,255,.09); }
    .toolbar { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; justify-content: flex-end; }
    header .toolbar {
      padding: 8px;
      border: 1px solid rgba(255,255,255,.10);
      border-radius: 14px;
      background: rgba(255,255,255,.03);
    }
    header .toolbar .toolbarMain,
    header .toolbar .toolbarMeta {
      width: 100%;
      display: flex;
      align-items: center;
      gap: 10px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    header .toolbar .toolbarMeta {
      justify-content: flex-start;
      border-top: 1px dashed rgba(255,255,255,.10);
      padding-top: 8px;
      margin-top: 2px;
    }
    header .toolbar .toolbarMeta .status { margin-left: auto; }
    header .toolbar .toolbarBtn {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: 12px;
      background: var(--btn);
      color: var(--text);
      min-height: var(--ctl-h);
      font-size: 12px;
      font-weight: 700;
      letter-spacing: .01em;
      cursor: pointer;
      transition: border-color .18s ease, background .18s ease, transform .12s ease, box-shadow .18s ease;
    }
    header .toolbar .toolbarBtn:hover { border-color: rgba(127,176,255,.4); background: rgba(127,176,255,.11); }
    header .toolbar .toolbarBtn:active { transform: translateY(1px); }
	    .pageSubnav {
	      margin: 10px 0 12px;
	      display: flex;
	      flex-wrap: nowrap;
	      align-items: center;
	      gap: 6px;
	      padding: 8px;
	      border: 1px solid rgba(255,255,255,.10);
	      border-radius: 11px;
	      background: rgba(255,255,255,.03);
	      overflow-x: auto;
	      overflow-y: hidden;
	      scrollbar-gutter: stable both-edges;
	      scrollbar-width: thin;
	      scrollbar-color: rgba(127,176,255,.34) rgba(255,255,255,.04);
	      -webkit-overflow-scrolling: touch;
	      scroll-snap-type: x proximity;
	    }
	    .pageSubnavLabel {
	      color: #9fb0cf;
	      font-size: 11px;
	      font-weight: 700;
	      letter-spacing: .04em;
	      text-transform: uppercase;
	      margin-right: 2px;
	      position: sticky;
	      left: 0;
	      z-index: 2;
	      padding-right: 6px;
	      background: linear-gradient(90deg, rgba(18,28,55,.92) 0%, rgba(18,28,55,.64) 70%, rgba(18,28,55,0) 100%);
	    }
	    .pageSubnavItem {
	      display: inline-flex;
	      align-items: center;
	      min-height: 30px;
	      border-radius: 999px;
	      border: 1px solid rgba(255,255,255,.14);
	      background: rgba(255,255,255,.03);
	      color: #c9d7f1;
	      font-size: 12px;
	      font-weight: 600;
	      padding: 4px 10px;
	      transition: border-color .18s ease, background .18s ease, color .18s ease;
	      scroll-snap-align: start;
	    }
    .pageSubnavItem:hover {
      border-color: rgba(127,176,255,.44);
      background: rgba(127,176,255,.12);
      color: #e1ebff;
    }
    .pageSubnavItem.active {
      border-color: rgba(40,209,124,.45);
      background: rgba(40,209,124,.16);
      color: #dff8ea;
    }
    .domainSplitDetails {
      border: 1px solid var(--border);
      border-radius: 14px;
      background: rgba(255,255,255,.02);
      padding: 10px 12px 12px;
      margin-top: 14px;
    }
    .domainSplitDetails > summary {
      cursor: pointer;
      font-size: 13px;
      font-weight: 700;
      color: #d6e3fb;
      list-style: none;
    }
    .domainSplitDetails > summary::-webkit-details-marker { display: none; }
    .domainSplitDetails > summary::before {
      content: "▸";
      display: inline-block;
      margin-right: 8px;
      transition: transform .18s ease;
      color: #9fb0cf;
    }
    .domainSplitDetails[open] > summary::before { transform: rotate(90deg); }
    .domainSplitHint {
      margin-top: 8px;
      font-size: 12px;
      color: var(--muted);
      line-height: 1.45;
    }
	    .toolbar input[type="text"],
	    .toolbar input[type="number"] {
	      padding: 8px 10px;
	      border: 1px solid var(--border);
	      border-radius: 12px;
	      background: rgba(17,26,51,.75);
	      color: var(--text);
	      min-height: var(--ctl-h);
	      min-width: 120px;
	      transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
	    }
	    .toolbar select {
	      padding: 8px 10px;
	      border: 1px solid var(--border);
	      border-radius: 12px;
	      background: rgba(17,26,51,.75);
	      color: var(--text);
	      min-height: var(--ctl-h);
	      min-width: 110px;
	      transition: border-color .18s ease, box-shadow .18s ease, background .18s ease;
	    }
    .toolbar input[type="text"]:focus,
    .toolbar input[type="number"]:focus,
    .toolbar select:focus {
      outline: none;
      border-color: var(--focus);
      box-shadow: 0 0 0 2px rgba(127,176,255,.22);
      background: rgba(17,26,51,.92);
    }
    .toolbar label { display: flex; align-items: center; gap: 8px; color: var(--muted); font-size: 12px; }
	    button {
	      padding: 8px 10px;
	      border: 1px solid var(--border);
	      border-radius: 12px;
	      background: var(--btn);
	      color: var(--text);
	      cursor: pointer;
	      min-height: var(--ctl-h);
	      font-size: 12px;
	      font-weight: 700;
	      letter-spacing: .01em;
	      transition: border-color .18s ease, background .18s ease, transform .12s ease, box-shadow .18s ease;
	    }
	    button.primary {
	      background: var(--btn2);
	      border-color: rgba(127,176,255,.28);
	    }
	    button:hover { border-color: rgba(127,176,255,.4); background: rgba(127,176,255,.11); }
	    button.primary:hover {
	      border-color: rgba(127,176,255,.55);
	      background: rgba(127,176,255,.18);
	    }
    button:disabled { opacity: .5; cursor: not-allowed; }
    button:disabled:hover { border-color: var(--border); background: var(--btn); }
    button:active { transform: translateY(1px); }
	    .status { color: var(--muted); font-size: 12px; }
	    .muted { color: var(--muted); font-size: 12px; }
	    .hint { color: var(--muted); font-size: 12px; margin-top: 8px; }
	    .mono { font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace; }
	    /* Shared "status box" pattern used across admin domains (WG/commission/overview). */
	    .wgBox {
	      border: 1px solid rgba(127,176,255,.20);
	      background: rgba(127,176,255,.05);
	      border-radius: 14px;
	      padding: 10px 12px;
	    }
	    .wgTitle { font-weight: 700; font-size: 12px; letter-spacing: .02em; }
	    .wgSummary { font-size: 12px; color: #c9d6ef; }
	    .wgSummary code { font-size: 12px; }
	    .wgBox .wgSummary + .wgSummary { margin-top: 6px; }
	    .wgHint { margin-top: 6px; }

	    /* Core utilities: prefer these over repeating inline styles. */
	    .uMt6 { margin-top: 6px; }
	    .uMt8 { margin-top: 8px; }
	    .uMt10 { margin-top: 10px; }
	    .uMt12 { margin-top: 12px; }
	    .uMt14 { margin-top: 14px; }
	    .uMb6 { margin-bottom: 6px; }
	    .uMb14 { margin-bottom: 14px; }
	    .uJcStart { justify-content: flex-start !important; }
	    .uInlineRow { display: inline-flex; gap: 8px; align-items: center; }
	    .uMaxH40vh { max-height: 40vh; }
	    .uMinW150 { min-width: 150px; }
	    .uMinW190 { min-width: 190px; }
	    .uMinW240 { min-width: 240px; }

	    /* Use with <pre class="tableWrap tableWrapPre">...</pre> to avoid inline padding styles. */
	    .tableWrap.tableWrapPre { padding: 10px; }
    .card {
      border: 1px solid var(--border);
      background: rgba(17,26,51,.75);
      border-radius: 16px;
      padding: 14px;
      box-shadow: 0 10px 30px rgba(0,0,0,.25);
      margin-top: 12px;
    }
    .summary, .kpi { display: flex; gap: 8px; flex-wrap: wrap; margin-top: 8px; }
    .badge {
      font-size: 11px;
      padding: 2px 8px;
      border-radius: 999px;
      border: 1px solid var(--border);
      display: inline-block;
      font-weight: 600;
    }
    .badge.good { color: #9cebc5; border-color: rgba(40,209,124,.35); background: rgba(40,209,124,.12); }
	    .badge.warn { color: #ffe09c; border-color: rgba(242,201,76,.35); background: rgba(242,201,76,.12); }
	    .badge.bad { color: #ffb1b1; border-color: rgba(255,93,93,.35); background: rgba(255,93,93,.12); }
	    .sectionTitle { font-size: 14px; font-weight: 800; letter-spacing: .01em; }
	    .sectionKicker { margin-top: 6px; font-size: 12px; color: var(--muted); line-height: 1.45; }
	    .sectionHead { display: flex; align-items: center; justify-content: space-between; gap: 10px; flex-wrap: wrap; margin-bottom: 10px; }
	    .sectionTools { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; justify-content: flex-end; }
	    .tableMeta { display: flex; gap: 8px; flex-wrap: wrap; align-items: center; margin-top: 8px; }
	    .metaChip {
	      font-size: 11px;
	      letter-spacing: .02em;
      color: #c9d6ef;
      border: 1px solid rgba(255,255,255,.14);
      border-radius: 999px;
      padding: 3px 9px;
      background: rgba(255,255,255,.04);
    }
    .metaChip.sort {
      color: #ffe9b4;
      border-color: rgba(242,201,76,.34);
      background: rgba(242,201,76,.14);
    }
    .metaChip.source {
      color: #b7ddff;
      border-color: rgba(127,176,255,.34);
      background: rgba(127,176,255,.12);
    }
    .metaChip.mode {
      color: #ccf3dd;
      border-color: rgba(40,209,124,.36);
      background: rgba(40,209,124,.14);
    }
    .flowCard { border-color: rgba(127,176,255,.24); background: linear-gradient(180deg, rgba(127,176,255,.08), rgba(127,176,255,.03)); }
    .flowTitle { font-size: 13px; font-weight: 700; letter-spacing: .01em; }
    .flowRow {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(170px, 1fr));
      gap: 8px;
      margin-top: 8px;
    }
    .flowStep {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      gap: 6px;
      min-height: 34px;
      border: 1px solid rgba(255,255,255,.15);
      border-radius: 10px;
      color: #d2def5;
      background: rgba(255,255,255,.03);
      font-size: 12px;
      font-weight: 600;
      padding: 6px 10px;
      transition: border-color .18s ease, background .18s ease, transform .12s ease;
    }
    .flowStep:hover { transform: translateY(-1px); border-color: rgba(127,176,255,.5); background: rgba(127,176,255,.12); }
    .flowStep.current {
      border-color: rgba(40,209,124,.52);
      background: rgba(40,209,124,.16);
      color: #dbfbe9;
    }
    .flowHint { margin-top: 8px; font-size: 12px; color: #b9c7df; }
    .workspaceBar {
      display: flex;
      align-items: center;
      gap: 8px;
      flex-wrap: wrap;
      margin-top: 10px;
    }
    .workspaceHint {
      font-size: 12px;
      color: #cfdaf1;
      border: 1px solid rgba(127,176,255,.28);
      border-radius: 999px;
      background: rgba(127,176,255,.10);
      padding: 4px 10px;
      min-height: 28px;
      display: inline-flex;
      align-items: center;
    }
    .workspaceHint.empty {
      color: var(--muted);
      border-color: rgba(255,255,255,.16);
      background: rgba(255,255,255,.03);
    }
    .workspaceBar select {
      min-width: 180px;
      max-width: 240px;
      min-height: 30px;
      border-radius: 10px;
      border: 1px solid var(--border);
      background: rgba(17,26,51,.75);
      color: var(--text);
      padding: 5px 8px;
    }
    details.advancedDetails {
      margin-top: 10px;
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 14px;
      background: rgba(255,255,255,.02);
      padding: 8px 10px;
    }
	    details.advancedDetails > summary {
	      cursor: pointer;
	      font-size: 12px;
	      font-weight: 800;
	      letter-spacing: .02em;
	      color: #d6e3fb;
	      list-style: none;
	      user-select: none;
	    }
	    details.advancedDetails > summary::-webkit-details-marker { display: none; }
	    details.advancedDetails > summary::before {
	      content: "▸";
	      display: inline-block;
	      margin-right: 8px;
	      transition: transform .18s ease;
	      color: #9fb0cf;
	    }
	    details.advancedDetails[open] > summary::before { transform: rotate(90deg); }
	    details.advancedDetails[open] {
	      border-color: rgba(127,176,255,.24);
	      background: rgba(127,176,255,.06);
	    }
    details.advancedDetails .workspaceBar {
      margin-top: 10px;
    }
    details.toolbarDetails {
      border: 1px solid rgba(255,255,255,.12);
      border-radius: 12px;
      background: rgba(255,255,255,.02);
      padding: 4px 8px;
    }
	    details.toolbarDetails > summary {
	      cursor: pointer;
	      font-size: 12px;
	      font-weight: 800;
	      letter-spacing: .02em;
	      color: var(--muted);
	      list-style: none;
	      user-select: none;
	    }
	    details.toolbarDetails > summary::-webkit-details-marker { display: none; }
	    details.toolbarDetails > summary::before {
	      content: "▸";
	      display: inline-block;
	      margin-right: 8px;
	      transition: transform .18s ease;
	      color: #9fb0cf;
	    }
	    details.toolbarDetails[open] > summary::before { transform: rotate(90deg); }
	    details.toolbarDetails[open] {
	      border-color: rgba(127,176,255,.24);
	      background: rgba(127,176,255,.06);
	    }
    .toolbarDetailsGrid {
      display: flex;
      flex-wrap: wrap;
      align-items: center;
      justify-content: flex-end;
      gap: 10px;
      margin-top: 8px;
    }
    .cmdOverlay {
      position: fixed;
      inset: 0;
      background: rgba(5,10,22,.62);
      backdrop-filter: blur(2px);
      display: none;
      align-items: flex-start;
      justify-content: center;
      padding: 80px 16px 24px;
      z-index: 80;
    }
    .cmdOverlay.open { display: flex; }
    .cockpitTimelineOverlay {
      position: fixed;
      inset: 0;
      background: rgba(5,10,22,.62);
      backdrop-filter: blur(2px);
      display: none;
      align-items: flex-start;
      justify-content: center;
      padding: 58px 16px 20px;
      z-index: 81;
    }
    .cockpitTimelineOverlay.open { display: flex; }
    .cmdDialog {
      width: min(760px, 100%);
      border: 1px solid rgba(127,176,255,.30);
      border-radius: 14px;
      background: rgba(17,26,51,.97);
      box-shadow: 0 24px 60px rgba(0,0,0,.42);
      overflow: hidden;
    }
    .cockpitTimelineDialog {
      width: min(1120px, 100%);
      border: 1px solid rgba(127,176,255,.30);
      border-radius: 14px;
      background: rgba(17,26,51,.97);
      box-shadow: 0 24px 60px rgba(0,0,0,.42);
      overflow: hidden;
    }
    .cockpitTimelineFilters {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 8px;
      padding: 10px 12px;
      border-bottom: 1px solid rgba(255,255,255,.10);
      background: rgba(9,15,30,.92);
    }
    .cockpitTimelineField {
      display: flex;
      flex-direction: column;
      gap: 4px;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: .02em;
    }
    .cockpitTimelineField select,
    .cockpitTimelineField input {
      width: 100%;
      min-height: 32px;
      border-radius: 10px;
      border: 1px solid rgba(255,255,255,.16);
      background: rgba(17,26,51,.72);
      color: var(--text);
      padding: 6px 8px;
      font-size: 12px;
    }
    .cockpitTimelineActions {
      display: flex;
      gap: 8px;
      align-items: flex-end;
      flex-wrap: wrap;
    }
    .cockpitTimelineSummary {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
      padding: 8px 12px;
      border-bottom: 1px solid rgba(255,255,255,.08);
      background: rgba(127,176,255,.06);
    }
    .cockpitTimelineTableWrap {
      max-height: min(58vh, 540px);
      overflow: auto;
    }
    .cockpitTimelineTable {
      width: 100%;
      min-width: 920px;
      border-collapse: collapse;
    }
    .cockpitTimelineTable th,
    .cockpitTimelineTable td {
      padding: 8px 9px;
      border-bottom: 1px solid rgba(255,255,255,.08);
      vertical-align: top;
      text-align: left;
      font-size: 12px;
    }
    .cockpitTimelineTable th {
      position: sticky;
      top: 0;
      z-index: 1;
      background: rgba(0,0,0,.24);
      color: var(--muted);
    }
    .cockpitTimelineTable tbody tr:hover td {
      background: rgba(127,176,255,.10);
    }
    .cockpitTimelineActionsCell {
      white-space: nowrap;
    }
    .cmdHead {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      padding: 10px 12px;
      border-bottom: 1px solid rgba(255,255,255,.10);
      font-size: 12px;
      color: #cbd8f1;
      background: rgba(127,176,255,.08);
    }
    .cmdSearch {
      width: 100%;
      border: 0;
      border-bottom: 1px solid rgba(255,255,255,.12);
      background: rgba(9,15,30,.96);
      color: var(--text);
      font-size: 14px;
      padding: 11px 12px;
      outline: none;
    }
    .cmdSearch:focus { border-bottom-color: rgba(127,176,255,.45); }
    .cmdList {
      max-height: min(52vh, 460px);
      overflow: auto;
    }
    .cmdItem {
      width: 100%;
      text-align: left;
      border: 0;
      border-bottom: 1px solid rgba(255,255,255,.06);
      background: transparent;
      color: var(--text);
      padding: 10px 12px;
      cursor: pointer;
    }
    .cmdItem:hover,
    .cmdItem.active {
      background: rgba(127,176,255,.12);
    }
    .cmdTitle {
      display: block;
      font-size: 13px;
      font-weight: 700;
      color: #d9e6ff;
    }
    .cmdSub {
      display: block;
      margin-top: 2px;
      font-size: 12px;
      color: var(--muted);
    }
    .quickLink {
      color: var(--muted);
      border: 1px solid var(--border);
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      background: var(--surface);
      transition: border-color .18s ease, color .18s ease, background .18s ease;
    }
    .quickLink:hover { border-color: rgba(127,176,255,.38); color: #d5e2f7; background: rgba(127,176,255,.10); }
    .actions { display: flex; gap: 6px; flex-wrap: wrap; }
    .smallbtn { padding: 5px 8px; border-radius: 9px; font-size: 12px; }
    .opAction { font-weight: 700; }
    .opActionAck { border-color: rgba(40,209,124,.35); background: rgba(40,209,124,.12); }
    .opActionSilence { border-color: rgba(242,201,76,.35); background: rgba(242,201,76,.14); }
    .opActionUnsilence { border-color: rgba(127,176,255,.35); background: rgba(127,176,255,.12); }
    .drillBtns { display: flex; gap: 6px; flex-wrap: wrap; }
    .drillBtn {
      color: var(--text);
      border: 1px solid var(--border);
      background: rgba(255,255,255,.04);
      padding: 4px 8px;
      border-radius: 999px;
      font-size: 12px;
      transition: border-color .18s ease, background .18s ease;
    }
    .drillBtn:hover { border-color: rgba(127,176,255,.38); background: rgba(127,176,255,.10); }
    .row {
      display: grid;
      grid-template-columns: 280px 1fr;
      gap: 10px;
      align-items: center;
      margin: 8px 0;
    }
    .row label { color: var(--muted); font-size: 13px; }
    .row input[type="number"],
    .row input[type="text"],
    .row select {
      width: 100%;
      padding: 8px 10px;
      border: 1px solid var(--border);
      border-radius: 10px;
      background: rgba(17,26,51,.75);
      color: var(--text);
    }
    .row input[type="checkbox"] { width: 18px; height: 18px; }
		    .tableWrap {
		      position: relative;
		      overflow: auto;
		      max-height: 72vh;
		      border-radius: 14px;
		      border: 1px solid var(--border);
		      margin-top: 10px;
		      background: linear-gradient(180deg, rgba(255,255,255,.02), rgba(255,255,255,.01));
		      scrollbar-gutter: stable both-edges;
		      scrollbar-color: rgba(127,176,255,.32) rgba(255,255,255,.04);
		    }
	    table {
	      width: 100%;
	      border-collapse: collapse;
	      min-width: 920px;
	      font-variant-numeric: tabular-nums;
	    }
	    th, td {
	      text-align: left;
	      border-bottom: 1px solid rgba(255,255,255,.06);
	      padding: 9px 10px;
	      vertical-align: top;
	      line-height: 1.35;
	    }
	    th {
	      background: rgba(0,0,0,.22);
	      position: sticky;
	      top: 0;
	      z-index: 1;
	      font-size: 12px;
	      letter-spacing: .02em;
	      color: var(--muted);
	      white-space: nowrap;
	    }
		    tbody tr:nth-child(even) td { background: rgba(255,255,255,.012); }
		    tbody tr:hover td { background: rgba(127,176,255,.08); }
		    tr.tableEmptyRow td { padding: 18px 12px; }
		    .emptyState {
		      border: 1px dashed rgba(255,255,255,.16);
		      border-radius: 14px;
		      padding: 14px 14px;
		      background: rgba(255,255,255,.02);
		      color: var(--muted);
		    }
		    .emptyState.tone-good { border-color: rgba(40,209,124,.34); background: rgba(40,209,124,.08); }
		    .emptyState.tone-warn { border-color: rgba(242,201,76,.34); background: rgba(242,201,76,.08); }
		    .emptyState.tone-bad { border-color: rgba(255,93,93,.34); background: rgba(255,93,93,.08); }
		    .emptyTitle { font-size: 13px; font-weight: 800; letter-spacing: .01em; color: #d6e3fb; }
		    .emptyHint { margin-top: 6px; font-size: 12px; line-height: 1.45; color: var(--muted); }
		    .tableWrap::-webkit-scrollbar { height: 10px; width: 10px; }
	    .tableWrap::-webkit-scrollbar-thumb { background: rgba(127,176,255,.24); border-radius: 999px; border: 2px solid rgba(0,0,0,0); background-clip: padding-box; }
	    .tableWrap::-webkit-scrollbar-thumb:hover { background: rgba(127,176,255,.34); border: 2px solid rgba(0,0,0,0); background-clip: padding-box; }
	    .tableWrap::-webkit-scrollbar-track { background: rgba(255,255,255,.03); border-radius: 999px; }
	    code {
	      font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono", "Courier New", monospace;
	      font-size: 12px;
	    }
	    @media (max-width: 760px) {
	      .row { grid-template-columns: 1fr; }
	      header .toolbar .toolbarMain > *,
	      header .toolbar .toolbarMeta > * {
	        flex: 1 1 100%;
	        min-width: 0 !important;
	      }
	      header .toolbar .toolbarMain button,
	      header .toolbar .toolbarMain input[type="text"],
	      header .toolbar .toolbarMain input[type="number"],
	      header .toolbar .toolbarMain select,
	      header .toolbar .toolbarMain .toolbarBtn,
	      header .toolbar .toolbarMeta button,
	      header .toolbar .toolbarMeta input[type="text"],
	      header .toolbar .toolbarMeta input[type="number"],
	      header .toolbar .toolbarMeta select,
	      header .toolbar .toolbarMeta .toolbarBtn {
	        width: 100%;
	      }
	      header .toolbar .toolbarMeta .status { margin-left: 0; }
	      .sideDeliverySticky {
	        grid-template-columns: repeat(2, minmax(0, 1fr));
	      }
	      .sideDeliverySticky .wide {
	        grid-column: 1 / -1;
	      }
	    }
	    @media (max-width: 1080px) {
	      .appShell { grid-template-columns: 1fr; }
	      .sideNav {
	        position: static;
	        overflow-x: hidden;
	        padding: 10px;
	      }
	      .sideBrand { margin-bottom: 8px; }
	      .sideJumpRow { grid-template-columns: repeat(4, minmax(0, 1fr)); }
      .sideGroups {
        display: flex;
        flex-direction: row;
        gap: 8px;
        overflow-x: auto;
        padding-bottom: 2px;
      }
      .sideGroup {
        min-width: 220px;
      }
      .sideMiniList { min-width: 220px; }
      .sideHub {
        min-width: 220px;
      }
      .sideCheatList {
        min-width: 220px;
      }
      .sideList {
        flex-direction: column;
        gap: 6px;
        min-width: 0;
      }
	      .sideLink {
	        min-height: 32px;
	      }
	      .sideNavTools { grid-template-columns: minmax(0, 1fr); }
	      .sideNavCompactBtn { width: 100%; }
	      .sideNavModeBtn { width: 100%; }
	      .sideNavFocusBtn { width: 100%; }
	      .sideNavHelpBtn { width: 100%; }
	      .sideDeliverySticky {
	        display: grid;
	        grid-template-columns: repeat(3, minmax(0, 1fr));
	        gap: 6px;
	        position: sticky;
        bottom: 0;
        z-index: 4;
        padding-top: 8px;
        margin-top: 4px;
        background: linear-gradient(180deg, rgba(13,23,47,.08) 0%, rgba(13,23,47,.86) 36%);
      }
      .sideDeliverySticky .wide {
        grid-column: 1 / -1;
      }
      .sideDeliverySticky .sideSnapshotBtn {
        min-height: 30px;
        font-size: 11px;
      }
      .sideNav.compact .sideGroups {
        gap: 6px;
      }
	      .sideNav.compact .sideGroup {
	        min-width: 196px;
	      }
	    }
	    @media (prefers-reduced-motion: reduce) {
	      * {
	        transition: none !important;
	        scroll-behavior: auto !important;
	      }
	    }
	    """.strip()


def base_admin_js() -> str:
    return """
    window.AdminUiKit = (() => {
      const WORKSPACE_STORAGE_KEY = "passengers_admin_workspace_context_v1";
      const PRESETS_STORAGE_PREFIX = "passengers_admin_filter_presets_v1:";
      const PRESET_ARCHIVE_STORAGE_PREFIX = "passengers_admin_filter_presets_archive_v1:";
      const PRESET_CLEANUP_REPORT_PREFIX = "passengers_admin_filter_presets_cleanup_v1:";
      const PRESET_TIMELINE_STORAGE_PREFIX = "passengers_admin_filter_presets_timeline_v1:";
      const PRESET_POLICY_LOCK_PREFIX = "passengers_admin_filter_presets_policy_lock_v1:";
      const PRESET_ROLLOUT_LAST_PREFIX = "passengers_admin_filter_presets_rollout_last_v1:";
      const NAV_FAVORITES_STORAGE_KEY = "passengers_admin_sidebar_favorites_v1";
      const NAV_RECENT_STORAGE_KEY = "passengers_admin_sidebar_recent_v1";
      const NAV_GROUPS_COLLAPSE_STORAGE_KEY = "passengers_admin_sidebar_collapsed_groups_v1";
      const NAV_MINI_COLLAPSE_STORAGE_KEY = "passengers_admin_sidebar_collapsed_mini_v1";
      const NAV_FOCUS_MODE_STORAGE_KEY = "passengers_admin_sidebar_focus_mode_v1";
      const NAV_COMPACT_MODE_STORAGE_KEY = "passengers_admin_sidebar_compact_mode_v1";
      const NAV_SIMPLE_MODE_STORAGE_KEY = "passengers_admin_sidebar_simple_mode_v1";
      const NAV_ONBOARDING_DISMISSED_STORAGE_KEY = "passengers_admin_sidebar_nav_onboarding_dismissed_v1";
      const NAV_ADOPTION_STORAGE_KEY = "passengers_admin_sidebar_nav_adoption_v1";
      const NAV_SESSION_SHORTCUTS_STORAGE_KEY = "passengers_admin_sidebar_session_shortcuts_v1";
      const NAV_INTENT_USAGE_STORAGE_KEY = "passengers_admin_sidebar_intent_usage_v1";
      const MISSION_LAST_PRESET_STORAGE_KEY = "passengers_admin_mission_last_preset_v1";
      const MISSION_HANDOFF_STORAGE_KEY = "passengers_admin_mission_handoff_v1";
      const MISSION_HANDOFF_TIMELINE_STORAGE_KEY = "passengers_admin_mission_handoff_timeline_v1";
      const MISSION_HANDOFF_COMPOSER_STORAGE_KEY = "passengers_admin_mission_handoff_composer_v1";
      const MISSION_HANDOFF_QUALITY_PROFILE_STORAGE_KEY = "passengers_admin_mission_handoff_quality_profile_v1";
      const MISSION_HANDOFF_REMEDIATION_METRICS_STORAGE_KEY = "passengers_admin_mission_handoff_remediation_metrics_v1";
      const MISSION_HANDOFF_REMEDIATION_TIMELINE_STORAGE_KEY = "passengers_admin_mission_handoff_remediation_timeline_v1";
      const MISSION_HANDOFF_REMEDIATION_GOVERNANCE_STORAGE_KEY = "passengers_admin_mission_handoff_remediation_governance_v1";
      const MISSION_HANDOFF_REMEDIATION_INCIDENTS_STORAGE_KEY = "passengers_admin_mission_handoff_remediation_incidents_v1";
      const MISSION_HANDOFF_REMEDIATION_DECISION_LEDGER_STORAGE_KEY = "passengers_admin_mission_handoff_remediation_decision_ledger_v1";
      const MISSION_ADOPTION_HISTORY_STORAGE_KEY = "passengers_admin_mission_adoption_history_v1";
      const MISSION_ADOPTION_HISTORY_META_STORAGE_KEY = "passengers_admin_mission_adoption_history_meta_v1";
      const MISSION_ADOPTION_TREND_WINDOW_STORAGE_KEY = "passengers_admin_mission_adoption_trend_window_v1";
      const MISSION_SNAPSHOT_STORAGE_KEY = "passengers_admin_mission_snapshots_v1";
      const MISSION_RESPONSE_PACK_STORAGE_KEY = "passengers_admin_mission_response_pack_v1";
      const MISSION_RESPONSE_ROUTING_STORAGE_KEY = "passengers_admin_mission_response_routing_v1";
      const MISSION_DELIVERY_ADAPTER_STORAGE_KEY = "passengers_admin_mission_delivery_adapter_v1";
      const MISSION_DELIVERY_POLICY_STORAGE_KEY = "passengers_admin_mission_delivery_policy_v1";
      const MISSION_DELIVERY_JOURNAL_STORAGE_KEY = "passengers_admin_mission_delivery_journal_v1";
      const MISSION_HANDOFF_MAX_LENGTH = 560;
      const MISSION_EVIDENCE_LIMIT = 48;
      const MISSION_ADOPTION_HISTORY_LIMIT = 24;
      const MISSION_ADOPTION_TREND_WINDOWS = [3, 5, 10];
      const MISSION_DELIVERY_JOURNAL_LIMIT = 64;
      const MISSION_HANDOFF_REMEDIATION_TTR_LIMIT = 24;
      const MISSION_HANDOFF_REMEDIATION_TIMELINE_LIMIT = 48;
      const MISSION_HANDOFF_REMEDIATION_INCIDENTS_LIMIT = 32;
      const MISSION_HANDOFF_REMEDIATION_INCIDENT_SNOOZE_MIN = 30;
      const MISSION_HANDOFF_REMEDIATION_DECISION_LEDGER_LIMIT = 96;
      const MISSION_HANDOFF_REMEDIATION_DECISION_BACKLOG_CLOSEOUT_LIMIT = 3;
      const MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_POLICIES = [
        { id: "closed", statuses: ["closed"], min_remaining_gap: 0, max_remaining_gap: 0, level: "none", route: "handoff-only", channel: "none", action: "monitor-only", reason: "decision gap closed" },
        { id: "risk_critical", statuses: ["risk"], min_remaining_gap: 3, max_remaining_gap: 999, level: "critical", route: "incident-escalation", channel: "telegram+ticket", action: "escalate-now", reason: "risk status with large remaining gap" },
        { id: "open_critical", statuses: ["open"], min_remaining_gap: 3, max_remaining_gap: 999, level: "high", route: "incident-escalation", channel: "ticket", action: "escalate-now", reason: "open status with large remaining gap" },
        { id: "risk_watch", statuses: ["risk"], min_remaining_gap: 1, max_remaining_gap: 2, level: "high", route: "shift-supervisor", channel: "telegram", action: "escalate-watch", reason: "risk status with unresolved closeout" },
        { id: "open_watch", statuses: ["open", "progress"], min_remaining_gap: 1, max_remaining_gap: 2, level: "medium", route: "next-shift", channel: "handoff+ticket", action: "queue-next-shift", reason: "non-zero remaining gap" },
      ];
      const MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_EXECUTION_STORAGE_KEY = "passengers_admin_mission_handoff_remediation_closeout_escalation_execution_v1";
      const MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_EXECUTION_LIMIT = 64;
      const MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_SLA_STALE_SEC = 20 * 60;
      const MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_SNOOZE_MIN = 30;
      const MISSION_HANDOFF_REMEDIATION_GOVERNANCE_PROFILES = [
        { id: "standard", label: "Standard", target_max_override_rate_pct: 25, target_p95_ttr_sec: 300 },
        { id: "tight", label: "Tight", target_max_override_rate_pct: 15, target_p95_ttr_sec: 180 },
      ];
      const MISSION_DELIVERY_SLA_WARN_SEC = 10 * 60;
      const MISSION_DELIVERY_SLA_STALE_SEC = 30 * 60;
      const MISSION_DELIVERY_BULK_LIMIT = 3;
      const MISSION_HANDOFF_QUALITY_PROFILES = [
        {
          id: "strict",
          label: "Strict",
          note_min_chars: 140,
          coach_min_chars: 16,
          min_next_actions: 2,
          require_context: true,
          require_composer_match: true,
          critical_checks: ["context", "coach", "next_actions", "note_size", "composer"],
        },
        {
          id: "balanced",
          label: "Balanced",
          note_min_chars: 110,
          coach_min_chars: 10,
          min_next_actions: 1,
          require_context: true,
          require_composer_match: false,
          critical_checks: ["context", "coach", "note_size"],
        },
      ];
      const SIDEBAR_INTENTS = [
        {
          id: "alerts-bad",
          label: "Критичні алерти",
          href: "/admin/fleet/alerts?sev=bad",
          hotkey: "Shift+Alt+A",
          nav_key: "alerts",
        },
        {
          id: "incidents-open",
          label: "Відкриті інциденти",
          href: "/admin/fleet/incidents?status=open&include_resolved=0",
          hotkey: "Shift+Alt+I",
          nav_key: "incidents",
        },
        {
          id: "audit-last",
          label: "Останній аудит",
          href: "/admin/audit",
          hotkey: "Shift+Alt+U",
          nav_key: "audit",
        },
      ];
      const NAV_ADOPTION_EVENT_LABELS = {
        nav_search_focus: "Search focus",
        nav_search_hotkey_focus: "Hotkey focus",
        nav_search_input: "Search input",
        nav_search_clear: "Search clear",
        nav_search_enter_open: "Search open",
        nav_search_arrowdown: "Search jump",
        nav_filter_apply: "Filter apply",
        nav_filter_clear: "Filter clear",
        nav_group_toggle: "Group toggle",
        nav_group_expand: "Group expand",
        nav_group_collapse: "Group collapse",
        nav_compact_enable: "Compact on",
        nav_compact_disable: "Compact off",
        nav_onboarding_open: "Tips open",
        nav_onboarding_close: "Tips close",
        nav_onboarding_dismiss: "Tips dismiss",
        nav_adoption_show: "Adoption show",
        nav_adoption_export: "Adoption export",
        nav_adoption_reset: "Adoption reset",
        nav_trend_history_show: "Trend show",
        nav_trend_history_export: "Trend export",
        nav_trend_history_clear: "Trend clear",
        nav_trend_window_set: "Trend window set",
      };
      const MISSION_TRIAGE_PRESETS = [
        {
          id: "critical-alerts",
          label: "Triage: bad alerts",
          href: "/admin/fleet/alerts?sev=bad&includeSilenced=0",
          metric: "bad",
        },
        {
          id: "open-incidents",
          label: "Triage: open incidents",
          href: "/admin/fleet/incidents?status=open&include_resolved=0",
          metric: "open",
        },
        {
          id: "sla-breach",
          label: "Triage: SLA breach",
          href: "/admin/fleet/incidents?sla_breached_only=1&include_resolved=0",
          metric: "sla",
        },
        {
          id: "queue-focus",
          label: "Triage: queue backlog",
          href: "/admin/fleet/incidents?status=open&include_resolved=0&q=queue",
          metric: "queue",
        },
      ];
      const MISSION_PLAYBOOKS = {
        "critical-alerts": [
          {
            id: "critical-alerts-step-1",
            label: "Критичні алерти",
            hint: "Відкрий sev=bad та перевір code/central без silenced.",
            href: "/admin/fleet/alerts?sev=bad&includeSilenced=0",
          },
          {
            id: "critical-alerts-step-2",
            label: "Відкриті інциденти",
            hint: "Перейди в open incidents та перевір повторювані code.",
            href: "/admin/fleet/incidents?status=open&include_resolved=0",
          },
          {
            id: "critical-alerts-step-3",
            label: "Аудит дій",
            hint: "Перевір останні ack/silence та зафіксуй handoff.",
            href: "/admin/audit",
          },
        ],
        "open-incidents": [
          {
            id: "open-incidents-step-1",
            label: "Open incidents",
            hint: "Почни з backlog відкритих інцидентів.",
            href: "/admin/fleet/incidents?status=open&include_resolved=0",
          },
          {
            id: "open-incidents-step-2",
            label: "SLA перевищення",
            hint: "Виділи інциденти зі SLA breach для пріоритету.",
            href: "/admin/fleet/incidents?sla_breached_only=1&include_resolved=0",
          },
          {
            id: "open-incidents-step-3",
            label: "Аудит і передача",
            hint: "Звір дії в audit і запиши handoff note.",
            href: "/admin/audit",
          },
        ],
        "sla-breach": [
          {
            id: "sla-breach-step-1",
            label: "SLA breach",
            hint: "Перевір інциденти, що вийшли за SLA.",
            href: "/admin/fleet/incidents?sla_breached_only=1&include_resolved=0",
          },
          {
            id: "sla-breach-step-2",
            label: "Пов'язані алерти",
            hint: "Зістав інциденти з bad alerts для root-cause.",
            href: "/admin/fleet/alerts?sev=bad&includeSilenced=0",
          },
          {
            id: "sla-breach-step-3",
            label: "Операційна фіксація",
            hint: "Виконай ручні дії й підтверди в аудиті.",
            href: "/admin/audit",
          },
        ],
        "queue-focus": [
          {
            id: "queue-focus-step-1",
            label: "Черга інцидентів",
            hint: "Фокус на queue/backlog в open incidents.",
            href: "/admin/fleet/incidents?status=open&include_resolved=0&q=queue",
          },
          {
            id: "queue-focus-step-2",
            label: "Fleet monitor",
            hint: "Звір pending/wg/stale counters у fleet overview.",
            href: "/admin/fleet",
          },
          {
            id: "queue-focus-step-3",
            label: "Audit handoff",
            hint: "Зафіксуй виконані кроки перед передачею зміни.",
            href: "/admin/audit",
          },
        ],
      };
      const MISSION_ROUTING_PROFILES = [
        {
          id: "critical-p1",
          label: "P1 Critical",
          channel: "noc-p1",
          priority: "p1",
          default_template: "short",
          rank: 90,
          match: {
            severity_any: ["bad", "critical"],
            status_any: ["open", "new", "investigating"],
          },
        },
        {
          id: "network-wg",
          label: "Network / WG",
          channel: "netops-l2",
          priority: "p1",
          default_template: "full",
          rank: 80,
          match: {
            code_contains_any: ["wg", "wireguard", "vpn", "tunnel", "network", "link", "lte"],
            status_any: ["open", "new", "all"],
          },
        },
        {
          id: "queue-backlog",
          label: "Queue Backlog",
          channel: "ops-backlog",
          priority: "p2",
          default_template: "full",
          rank: 70,
          match: {
            code_contains_any: ["queue", "pending", "backlog", "batch"],
            status_any: ["open", "new", "all"],
          },
        },
        {
          id: "audit-followup",
          label: "Audit Follow-up",
          channel: "ops-audit",
          priority: "p3",
          default_template: "audit",
          rank: 50,
          match: {
            path_any: ["/admin/audit"],
          },
        },
        {
          id: "standard-ops",
          label: "Standard Ops",
          channel: "ops-general",
          priority: "p2",
          default_template: "short",
          rank: 10,
          match: {},
        },
      ];
      const MISSION_CHANNEL_TEMPLATE_VARIANTS = [
        { id: "short", label: "Короткий" },
        { id: "full", label: "Повний" },
        { id: "audit", label: "Audit" },
      ];
      const MISSION_DELIVERY_ADAPTERS = [
        {
          id: "telegram",
          label: "Telegram",
          target: "@ops_alerts",
          transport: "chat",
        },
        {
          id: "email",
          label: "Email",
          target: "ops@company.local",
          transport: "email",
        },
        {
          id: "ticket",
          label: "Web Ticket",
          target: "ops-queue",
          transport: "ticket",
        },
      ];
      const MISSION_DELIVERY_POLICY_PROFILES = [
        {
          id: "balanced",
          label: "Balanced",
          warn_sec: 10 * 60,
          stale_sec: 30 * 60,
          bulk_limit: 3,
          stale_strategy: "escalate-first",
          warn_strategy: "ack",
        },
        {
          id: "aggressive",
          label: "Aggressive",
          warn_sec: 5 * 60,
          stale_sec: 15 * 60,
          bulk_limit: 5,
          stale_strategy: "escalate-first",
          warn_strategy: "ack-fast",
        },
        {
          id: "conservative",
          label: "Conservative",
          warn_sec: 15 * 60,
          stale_sec: 45 * 60,
          bulk_limit: 2,
          stale_strategy: "retry-first",
          warn_strategy: "observe",
        },
      ];
      let paletteState = null;
      let cockpitTimelineState = null;
      function byId(id) { return document.getElementById(id); }
      function setText(id, text) {
        const node = byId(id);
        if (node) node.textContent = String(text ?? "");
      }
      function setStatus(id, text) { setText(id, text); }
      function esc(text) {
        return String(text ?? "")
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;");
      }
      function val(id, fallback = "") {
        const node = byId(id);
        if (!node) return String(fallback ?? "");
        return String(node.value ?? "").trim();
      }
      function intVal(id, fallback) {
        const parsed = parseInt(val(id, ""), 10);
        return Number.isFinite(parsed) ? parsed : fallback;
      }
      function optInt(id) {
        const raw = val(id, "");
        if (!raw) return null;
        const parsed = parseInt(raw, 10);
        return Number.isFinite(parsed) ? parsed : null;
      }
      function setDisabled(id, disabled) {
        const node = byId(id);
        if (node) node.disabled = !!disabled;
      }
      function loadSidebarFavorites() {
        try {
          const raw = JSON.parse(localStorage.getItem(NAV_FAVORITES_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw
            .map((item) => String(item || "").trim().toLowerCase())
            .filter((item) => !!item)
            .slice(0, 12);
        } catch (_error) {
          return [];
        }
      }
      function storeSidebarFavorites(items) {
        const source = Array.isArray(items) ? items : [];
        const set = new Set();
        for (const item of source) {
          const clean = String(item || "").trim().toLowerCase();
          if (!clean) continue;
          set.add(clean);
        }
        const normalized = Array.from(set.values()).slice(0, 12);
        try { localStorage.setItem(NAV_FAVORITES_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function loadSidebarRecent() {
        try {
          const raw = JSON.parse(localStorage.getItem(NAV_RECENT_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw
            .map((item) => {
              const source = item && typeof item === "object" ? item : {};
              return {
                key: String(source.key || "").trim().toLowerCase(),
                label: String(source.label || "").trim(),
                href: String(source.href || "").trim(),
                ts: String(source.ts || "").trim(),
              };
            })
            .filter((item) => !!item.key && !!item.label && !!item.href)
            .slice(0, 12);
        } catch (_error) {
          return [];
        }
      }
      function storeSidebarRecent(items) {
        const source = Array.isArray(items) ? items : [];
        const normalized = source
          .map((item) => {
            const current = item && typeof item === "object" ? item : {};
            return {
              key: String(current.key || "").trim().toLowerCase(),
              label: String(current.label || "").trim(),
              href: String(current.href || "").trim(),
              ts: String(current.ts || "").trim(),
            };
          })
          .filter((item) => !!item.key && !!item.label && !!item.href)
          .slice(0, 12);
        try { localStorage.setItem(NAV_RECENT_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function loadSidebarCollapsedGroups() {
        try {
          const storageRaw = localStorage.getItem(NAV_GROUPS_COLLAPSE_STORAGE_KEY);
          if (!storageRaw) {
            return Array.from(document.querySelectorAll(".sideGroup.collapsed[data-side-group]"))
              .map((node) => String(node.getAttribute("data-side-group") || "").trim().toLowerCase())
              .filter((item) => !!item)
              .slice(0, 8);
          }
          const raw = JSON.parse(storageRaw);
          if (!Array.isArray(raw)) return [];
          return raw
            .map((item) => String(item || "").trim().toLowerCase())
            .filter((item) => !!item)
            .slice(0, 8);
        } catch (_error) {
          return Array.from(document.querySelectorAll(".sideGroup.collapsed[data-side-group]"))
            .map((node) => String(node.getAttribute("data-side-group") || "").trim().toLowerCase())
            .filter((item) => !!item)
            .slice(0, 8);
        }
      }
      function storeSidebarCollapsedGroups(items) {
        const source = Array.isArray(items) ? items : [];
        const set = new Set();
        for (const item of source) {
          const clean = String(item || "").trim().toLowerCase();
          if (!clean) continue;
          set.add(clean);
        }
        const normalized = Array.from(set.values()).slice(0, 8);
        try { localStorage.setItem(NAV_GROUPS_COLLAPSE_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function loadSidebarCollapsedMiniSections() {
        // Defaults: keep Favorites visible, collapse other heavy sidebar blocks to avoid vertical overload.
        const defaults = ["quick", "hub", "mission", "cheat", "recent", "session"];
        try {
          const storageRaw = localStorage.getItem(NAV_MINI_COLLAPSE_STORAGE_KEY);
          if (!storageRaw) return defaults;
          const raw = JSON.parse(storageRaw);
          if (!Array.isArray(raw)) return defaults;
          return raw
            .map((item) => String(item || "").trim().toLowerCase())
            .filter((item) => !!item)
            .slice(0, 12);
        } catch (_error) {
          return defaults;
        }
      }
      function storeSidebarCollapsedMiniSections(items) {
        const source = Array.isArray(items) ? items : [];
        const set = new Set();
        for (const item of source) {
          const clean = String(item || "").trim().toLowerCase();
          if (!clean) continue;
          set.add(clean);
        }
        const normalized = Array.from(set.values()).slice(0, 12);
        try { localStorage.setItem(NAV_MINI_COLLAPSE_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function loadSidebarFocusMode() {
        try {
          const raw = String(localStorage.getItem(NAV_FOCUS_MODE_STORAGE_KEY) || "").trim().toLowerCase();
          if (!raw) return false;
          return raw === "1" || raw === "true" || raw === "on" || raw === "yes";
        } catch (_error) {
          return false;
        }
      }
      function storeSidebarFocusMode(enabled) {
        const value = enabled ? "1" : "0";
        try { localStorage.setItem(NAV_FOCUS_MODE_STORAGE_KEY, value); } catch (_error) {}
        return value === "1";
      }
      function loadSidebarCompactMode() {
        try {
          const raw = String(localStorage.getItem(NAV_COMPACT_MODE_STORAGE_KEY) || "").trim().toLowerCase();
          if (!raw) return false;
          return raw === "1" || raw === "true" || raw === "on" || raw === "yes";
        } catch (_error) {
          return false;
        }
      }
      function storeSidebarCompactMode(enabled) {
        const value = enabled ? "1" : "0";
        try { localStorage.setItem(NAV_COMPACT_MODE_STORAGE_KEY, value); } catch (_error) {}
        return value === "1";
      }
      function loadSidebarSimpleMode() {
        try {
          const raw = String(localStorage.getItem(NAV_SIMPLE_MODE_STORAGE_KEY) || "").trim().toLowerCase();
          if (!raw) return true;
          return raw === "1" || raw === "true" || raw === "on" || raw === "yes";
        } catch (_error) {
          return true;
        }
      }
      function storeSidebarSimpleMode(enabled) {
        const value = enabled ? "1" : "0";
        try { localStorage.setItem(NAV_SIMPLE_MODE_STORAGE_KEY, value); } catch (_error) {}
        return value === "1";
      }
      function isSidebarNavOnboardingDismissed() {
        try {
          const raw = String(localStorage.getItem(NAV_ONBOARDING_DISMISSED_STORAGE_KEY) || "").trim().toLowerCase();
          if (!raw) return false;
          return raw === "1" || raw === "true" || raw === "on" || raw === "yes";
        } catch (_error) {
          return false;
        }
      }
      function storeSidebarNavOnboardingDismissed(dismissed) {
        const value = dismissed ? "1" : "0";
        try { localStorage.setItem(NAV_ONBOARDING_DISMISSED_STORAGE_KEY, value); } catch (_error) {}
        return value === "1";
      }
      function applySidebarFocusMode(enabled) {
        const active = !!enabled;
        document.body.classList.toggle("sidebar-focus", active);
        const toggle = byId("sideFocusToggle");
        if (toggle) {
          toggle.setAttribute("aria-pressed", active ? "true" : "false");
          toggle.textContent = active ? "Фокус" : "Стандарт";
          toggle.title = active ? "Вимкнути фокус-режим" : "Увімкнути фокус-режим";
        }
        const statusNode = byId("sideFocusState");
        if (statusNode) {
          statusNode.textContent = active
            ? "Фокус: тільки навігація"
            : "Стандарт: повний sidebar (навігація + інструменти)";
        }
        return active;
      }
      function applySidebarCompactMode(enabled) {
        const active = !!enabled;
        const sideNav = document.querySelector(".sideNav");
        if (sideNav instanceof HTMLElement) sideNav.classList.toggle("compact", active);
        const toggle = byId("sideNavCompactToggle");
        if (toggle) {
          toggle.setAttribute("aria-pressed", active ? "true" : "false");
          toggle.textContent = active ? "Комфорт" : "Компакт";
          toggle.title = active ? "Вимкнути компактний режим" : "Увімкнути компактний режим";
        }
        return active;
      }
      function applySidebarSimpleMode(enabled) {
        const active = !!enabled;
        document.body.classList.toggle("sidebar-simple", active);
        const toggle = byId("sideNavModeToggle");
        if (toggle) {
          toggle.setAttribute("aria-pressed", active ? "true" : "false");
          toggle.textContent = active ? "Просто" : "Розширено";
          toggle.title = active ? "Показати розширені блоки sidebar" : "Приховати розширені блоки sidebar";
        }
        const advancedDetails = Array.from(document.querySelectorAll('details[data-advanced-details="1"]'));
        for (const node of advancedDetails) {
          if (!(node instanceof HTMLDetailsElement)) continue;
          // Entering Simple should reduce vertical noise (collapse advanced blocks).
          // Leaving Simple must not auto-expand everything (it is visually jarring on long pages).
          if (active) node.open = false;
        }
        try { refreshSidebarGroups(); } catch (_error) {}
        return active;
      }
      function refreshSidebarMiniSections() {
        const collapsedSet = new Set(loadSidebarCollapsedMiniSections());
        const sections = Array.from(document.querySelectorAll(".sideMiniSection[data-side-mini]"));
        for (const section of sections) {
          if (!(section instanceof HTMLElement)) continue;
          const key = String(section.getAttribute("data-side-mini") || "").trim().toLowerCase();
          if (!key) continue;
          const collapsed = collapsedSet.has(key);
          section.classList.toggle("collapsed", collapsed);
          const body = byId(`sideMiniBody-${key}`);
          if (body instanceof HTMLElement) body.hidden = collapsed;
          const toggle = section.querySelector(`button.sideMiniToggle[data-side-mini-toggle="${key}"]`);
          if (toggle instanceof HTMLButtonElement) {
            toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
            toggle.title = collapsed ? "Розгорнути блок" : "Згорнути блок";
          }
        }
      }
      function toggleSidebarMiniSection(key) {
        const cleanKey = String(key || "").trim().toLowerCase();
        if (!cleanKey) return;
        const current = loadSidebarCollapsedMiniSections();
        const index = current.indexOf(cleanKey);
        if (index >= 0) current.splice(index, 1);
        else current.push(cleanKey);
        storeSidebarCollapsedMiniSections(current);
        refreshSidebarMiniSections();
      }
      function setSidebarNavOnboardingVisible(visible, options = {}) {
        const active = !!visible;
        const source = options && typeof options === "object" ? options : {};
        const onboarding = byId("sideNavOnboarding");
        const helpToggle = byId("sideNavHelpToggle");
        if (onboarding) onboarding.hidden = !active;
        if (helpToggle) {
          helpToggle.setAttribute("aria-expanded", active ? "true" : "false");
          helpToggle.title = active ? "Приховати підказки" : "Показати підказки";
        }
        if (source.persistDismiss === true) storeSidebarNavOnboardingDismissed(!active);
        return active;
      }
      function loadSidebarNavAdoption() {
        try {
          const raw = JSON.parse(localStorage.getItem(NAV_ADOPTION_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          const sourceEvents = source.events && typeof source.events === "object" ? source.events : {};
          const events = {};
          for (const [eventId, payload] of Object.entries(sourceEvents)) {
            const cleanId = String(eventId || "").trim().toLowerCase();
            if (!cleanId) continue;
            const item = payload && typeof payload === "object" ? payload : {};
            const count = Math.floor(Number(item.count || 0));
            if (!Number.isFinite(count) || count <= 0) continue;
            events[cleanId] = {
              count: Math.min(50000, count),
              last_ts: String(item.last_ts || "").trim(),
            };
          }
          return {
            first_ts: String(source.first_ts || "").trim(),
            last_ts: String(source.last_ts || "").trim(),
            events,
          };
        } catch (_error) {
          return { first_ts: "", last_ts: "", events: {} };
        }
      }
      function storeSidebarNavAdoption(state) {
        const source = state && typeof state === "object" ? state : {};
        const sourceEvents = source.events && typeof source.events === "object" ? source.events : {};
        const events = {};
        const keys = Object.keys(sourceEvents).slice(0, 64);
        for (const eventId of keys) {
          const cleanId = String(eventId || "").trim().toLowerCase();
          if (!cleanId) continue;
          const item = sourceEvents[eventId] && typeof sourceEvents[eventId] === "object" ? sourceEvents[eventId] : {};
          const count = Math.floor(Number(item.count || 0));
          if (!Number.isFinite(count) || count <= 0) continue;
          events[cleanId] = {
            count: Math.min(50000, count),
            last_ts: String(item.last_ts || "").trim(),
          };
        }
        const payload = {
          first_ts: String(source.first_ts || "").trim(),
          last_ts: String(source.last_ts || "").trim(),
          events,
        };
        try { localStorage.setItem(NAV_ADOPTION_STORAGE_KEY, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function navAdoptionEventLabel(eventId) {
        const cleanId = String(eventId || "").trim().toLowerCase();
        if (!cleanId) return "event";
        return NAV_ADOPTION_EVENT_LABELS[cleanId] || cleanId;
      }
      function buildSidebarNavAdoptionSummary() {
        const telemetry = loadSidebarNavAdoption();
        const eventCounts = {};
        const entries = Object.entries(telemetry.events || {})
          .map(([eventId, payload]) => {
            const item = payload && typeof payload === "object" ? payload : {};
            const count = Math.floor(Number(item.count || 0));
            const lastTs = String(item.last_ts || "").trim();
            const cleanId = String(eventId || "").trim().toLowerCase();
            if (cleanId && Number.isFinite(count) && count > 0) eventCounts[cleanId] = count;
            return {
              id: cleanId,
              label: navAdoptionEventLabel(eventId),
              count: Number.isFinite(count) && count > 0 ? count : 0,
              last_ts: lastTs,
              last_value: Number.isFinite(Date.parse(lastTs)) ? Date.parse(lastTs) : 0,
            };
          })
          .filter((item) => !!item.id && item.count > 0)
          .sort((left, right) => {
            if (right.count !== left.count) return right.count - left.count;
            return right.last_value - left.last_value;
          });
        const total = entries.reduce((acc, item) => acc + Number(item.count || 0), 0);
        return {
          total_actions: total,
          unique_events: entries.length,
          first_ts: String(telemetry.first_ts || "").trim(),
          last_ts: String(telemetry.last_ts || "").trim(),
          compact_enabled: loadSidebarCompactMode(),
          onboarding_hidden: isSidebarNavOnboardingDismissed(),
          event_counts: eventCounts,
          top_events: entries.slice(0, 4),
        };
      }
      function adoptionEventCount(summary, eventId) {
        const source = summary && typeof summary === "object" ? summary : {};
        const counts = source.event_counts && typeof source.event_counts === "object" ? source.event_counts : {};
        const cleanId = String(eventId || "").trim().toLowerCase();
        const value = Number(counts[cleanId] || 0);
        return Number.isFinite(value) && value > 0 ? value : 0;
      }
      function buildSidebarNavAdoptionCoaching(summary = null) {
        const source = summary && typeof summary === "object" ? summary : buildSidebarNavAdoptionSummary();
        const hints = [];
        const completed = [];
        const searchOpen = adoptionEventCount(source, "nav_search_enter_open");
        const searchHotkey = adoptionEventCount(source, "nav_search_hotkey_focus");
        const groupToggle = adoptionEventCount(source, "nav_group_toggle");
        const compactOn = adoptionEventCount(source, "nav_compact_enable");
        const onboardingDismiss = adoptionEventCount(source, "nav_onboarding_dismiss");
        if (searchOpen > 0) completed.push("search-open");
        else hints.push("Використай пошук меню + Enter для швидкого відкриття єдиного розділу.");
        if (searchHotkey > 0) completed.push("search-hotkey");
        else hints.push("Додай у рутину Shift+Alt+N для швидкого фокусу на nav-search.");
        if (groupToggle > 0) completed.push("group-toggle");
        else hints.push("Згорни/розгорни хоча б одну групу меню для чистішого робочого простору.");
        if (compactOn > 0) completed.push("compact-mode");
        else hints.push("Перевір compact-режим у щільних змінах (багато одночасних інцидентів).");
        if (onboardingDismiss > 0 || source.onboarding_hidden) completed.push("onboarding-control");
        else hints.push("Після ознайомлення з підказками закрий onboarding, щоб зменшити шум.");
        const totalChecks = 5;
        const score = Math.round((completed.length / totalChecks) * 100);
        let level = "onboarding";
        if (score >= 80) level = "steady";
        else if (score >= 50) level = "progressing";
        const levelLabel = level === "steady"
          ? "steady"
          : (level === "progressing" ? "progressing" : "onboarding");
        return {
          level,
          level_label: levelLabel,
          score,
          hints: hints.slice(0, 3),
          completed: completed.length,
          total_checks: totalChecks,
        };
      }
      function buildSidebarNavAdoptionScorecard(summary = null) {
        const source = summary && typeof summary === "object" ? summary : buildSidebarNavAdoptionSummary();
        const groupActivity = (
          adoptionEventCount(source, "nav_group_toggle")
          + adoptionEventCount(source, "nav_group_expand")
          + adoptionEventCount(source, "nav_group_collapse")
        );
        const onboardingActivityRaw = (
          adoptionEventCount(source, "nav_onboarding_dismiss")
          + adoptionEventCount(source, "nav_onboarding_close")
        );
        const onboardingActivity = onboardingActivityRaw > 0
          ? onboardingActivityRaw
          : (source.onboarding_hidden ? 1 : 0);
        const checks = [
          {
            id: "search-open",
            label: "Search Enter open",
            count: adoptionEventCount(source, "nav_search_enter_open"),
            next_action: "Відкрий цільовий розділ через nav-search + Enter.",
          },
          {
            id: "search-hotkey",
            label: "Hotkey focus",
            count: adoptionEventCount(source, "nav_search_hotkey_focus"),
            next_action: "Застосуй Shift+Alt+N для швидкого фокусу на пошук.",
          },
          {
            id: "group-control",
            label: "Group control",
            count: groupActivity,
            next_action: "Згорни/розгорни групу меню для чистого робочого простору.",
          },
          {
            id: "compact-mode",
            label: "Compact mode",
            count: adoptionEventCount(source, "nav_compact_enable"),
            next_action: "Увімкни compact режим у щільному triage-сценарії.",
          },
          {
            id: "tips-control",
            label: "Tips control",
            count: onboardingActivity,
            next_action: "Після ознайомлення закрий onboarding tips, щоб зменшити шум.",
          },
        ].map((item) => {
          const count = Math.max(0, Math.floor(Number(item.count || 0)));
          return {
            id: item.id,
            label: item.label,
            count,
            status: count > 0 ? "pass" : "warn",
            next_action: item.next_action,
          };
        });
        const total = checks.length;
        const passed = checks.filter((item) => item.status === "pass").length;
        const percent = total > 0 ? Math.round((passed / total) * 100) : 0;
        const tone = passed >= Math.max(4, total - 1) ? "pass" : "warn";
        return {
          checks,
          total,
          passed,
          percent,
          tone,
        };
      }
      function buildSidebarNavNextActions(scorecard = null, coaching = null) {
        const sourceScorecard = scorecard && typeof scorecard === "object"
          ? scorecard
          : buildSidebarNavAdoptionScorecard();
        const sourceCoaching = coaching && typeof coaching === "object"
          ? coaching
          : buildSidebarNavAdoptionCoaching();
        const actions = [];
        for (const item of sourceScorecard.checks || []) {
          if (String(item.status || "") !== "warn") continue;
          const text = String(item.next_action || "").trim();
          if (text) actions.push(text);
          if (actions.length >= 2) break;
        }
        for (const hint of sourceCoaching.hints || []) {
          const text = String(hint || "").trim();
          if (!text || actions.includes(text)) continue;
          actions.push(text);
          if (actions.length >= 3) break;
        }
        if (actions.length === 0) actions.push("Паттерн стабільний: зафіксуй поточний workflow як еталон зміни.");
        return actions.slice(0, 3);
      }
      function missionAdoptionHistoryTsValue(ts) {
        const parsed = Date.parse(String(ts || ""));
        return Number.isFinite(parsed) ? parsed : 0;
      }
      function loadMissionAdoptionHistory() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_ADOPTION_HISTORY_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw
            .map((item) => {
              const source = item && typeof item === "object" ? item : {};
              const scorePercent = Math.max(0, Math.min(100, Math.round(Number(source.score_percent || 0))));
              const passed = Math.max(0, Math.round(Number(source.passed || 0)));
              const total = Math.max(passed, Math.round(Number(source.total || 0)));
              return {
                id: String(source.id || "").trim(),
                ts: String(source.ts || "").trim(),
                score_percent: scorePercent,
                passed,
                total,
                tone: String(source.tone || "").trim().toLowerCase(),
                actions: Math.max(0, Math.round(Number(source.actions || 0))),
                unique_events: Math.max(0, Math.round(Number(source.unique_events || 0))),
                context: missionTrimText(String(source.context || ""), 96),
                reason: missionTrimText(String(source.reason || ""), 96),
              };
            })
            .filter((item) => !!item.ts && item.total > 0)
            .sort((left, right) => missionAdoptionHistoryTsValue(right.ts) - missionAdoptionHistoryTsValue(left.ts))
            .slice(0, MISSION_ADOPTION_HISTORY_LIMIT);
        } catch (_error) {
          return [];
        }
      }
      function storeMissionAdoptionHistory(items = []) {
        const source = Array.isArray(items) ? items : [];
        const normalized = source
          .map((item) => {
            const current = item && typeof item === "object" ? item : {};
            const scorePercent = Math.max(0, Math.min(100, Math.round(Number(current.score_percent || 0))));
            const passed = Math.max(0, Math.round(Number(current.passed || 0)));
            const total = Math.max(passed, Math.round(Number(current.total || 0)));
            return {
              id: String(current.id || "").trim() || `${Date.now()}-${Math.floor(Math.random() * 100000)}`,
              ts: String(current.ts || "").trim() || new Date().toISOString(),
              score_percent: scorePercent,
              passed,
              total,
              tone: missionTrimText(String(current.tone || "warn").trim().toLowerCase(), 24),
              actions: Math.max(0, Math.round(Number(current.actions || 0))),
              unique_events: Math.max(0, Math.round(Number(current.unique_events || 0))),
              context: missionTrimText(String(current.context || ""), 96),
              reason: missionTrimText(String(current.reason || ""), 96),
            };
          })
          .filter((item) => !!item.ts && item.total > 0)
          .sort((left, right) => missionAdoptionHistoryTsValue(right.ts) - missionAdoptionHistoryTsValue(left.ts))
          .slice(0, MISSION_ADOPTION_HISTORY_LIMIT);
        try { localStorage.setItem(MISSION_ADOPTION_HISTORY_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function loadMissionAdoptionHistoryMeta() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_ADOPTION_HISTORY_META_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          return {
            last_reset_ts: String(source.last_reset_ts || "").trim(),
            last_reset_reason: missionTrimText(String(source.last_reset_reason || ""), 96),
          };
        } catch (_error) {
          return { last_reset_ts: "", last_reset_reason: "" };
        }
      }
      function storeMissionAdoptionHistoryMeta(meta = {}) {
        const source = meta && typeof meta === "object" ? meta : {};
        const payload = {
          last_reset_ts: String(source.last_reset_ts || "").trim(),
          last_reset_reason: missionTrimText(String(source.last_reset_reason || ""), 96),
        };
        try { localStorage.setItem(MISSION_ADOPTION_HISTORY_META_STORAGE_KEY, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function clearMissionAdoptionHistory(options = {}) {
        const source = options && typeof options === "object" ? options : {};
        storeMissionAdoptionHistory([]);
        return storeMissionAdoptionHistoryMeta({
          last_reset_ts: String(source.ts || new Date().toISOString()),
          last_reset_reason: String(source.reason || "manual clear"),
        });
      }
      function buildMissionAdoptionHistoryLifecycle(history = null) {
        const sourceHistory = Array.isArray(history) ? history : loadMissionAdoptionHistory();
        const meta = loadMissionAdoptionHistoryMeta();
        const resetValue = Date.parse(String(meta.last_reset_ts || ""));
        const nowValue = Date.now();
        const resetAgeSec = Number.isFinite(resetValue) ? Math.max(0, Math.round((nowValue - resetValue) / 1000)) : null;
        const resetRecent = Number.isFinite(resetAgeSec) && Number(resetAgeSec) <= 24 * 3600;
        if (sourceHistory.length > 0) {
          return {
            status_id: "active",
            status_label: "ACTIVE",
            reset_recent: resetRecent,
            reset_age_sec: resetAgeSec,
            reset_age_label: Number.isFinite(resetAgeSec) ? formatAgeShort(Number(resetAgeSec)) : "",
            reset_reason: String(meta.last_reset_reason || "").trim(),
          };
        }
        if (resetRecent) {
          return {
            status_id: "reset_recently",
            status_label: "RESET_RECENTLY",
            reset_recent: true,
            reset_age_sec: resetAgeSec,
            reset_age_label: Number.isFinite(resetAgeSec) ? formatAgeShort(Number(resetAgeSec)) : "",
            reset_reason: String(meta.last_reset_reason || "").trim(),
          };
        }
        return {
          status_id: "empty",
          status_label: "EMPTY",
          reset_recent: false,
          reset_age_sec: resetAgeSec,
          reset_age_label: Number.isFinite(resetAgeSec) ? formatAgeShort(Number(resetAgeSec)) : "",
          reset_reason: String(meta.last_reset_reason || "").trim(),
        };
      }
      function normalizeMissionAdoptionTrendWindow(value, fallback = 5) {
        const numeric = Math.max(1, Math.round(Number(value || 0)));
        if (MISSION_ADOPTION_TREND_WINDOWS.includes(numeric)) return numeric;
        const fallbackNumeric = Math.max(1, Math.round(Number(fallback || 5)));
        if (MISSION_ADOPTION_TREND_WINDOWS.includes(fallbackNumeric)) return fallbackNumeric;
        return 5;
      }
      function loadMissionAdoptionTrendWindow() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(MISSION_ADOPTION_TREND_WINDOW_STORAGE_KEY) || "null");
          if (raw && typeof raw === "object") return normalizeMissionAdoptionTrendWindow(raw.window_size, 5);
          return normalizeMissionAdoptionTrendWindow(raw, 5);
        } catch (_error) {
          return 5;
        }
      }
      function storeMissionAdoptionTrendWindow(value) {
        const windowSize = normalizeMissionAdoptionTrendWindow(value, 5);
        try { sessionStorage.setItem(MISSION_ADOPTION_TREND_WINDOW_STORAGE_KEY, JSON.stringify({ window_size: windowSize })); } catch (_error) {}
        return windowSize;
      }
      function appendMissionAdoptionHistoryEntry(options = {}) {
        const source = options && typeof options === "object" ? options : {};
        const summary = source.summary && typeof source.summary === "object" ? source.summary : buildSidebarNavAdoptionSummary();
        const scorecard = source.scorecard && typeof source.scorecard === "object" ? source.scorecard : buildSidebarNavAdoptionScorecard(summary);
        if (!scorecard.total || scorecard.total <= 0) return loadMissionAdoptionHistory();
        const nowTs = String(source.ts || new Date().toISOString());
        const context = missionTrimText(String(source.context || ""), 96);
        const reason = missionTrimText(String(source.reason || "handoff save"), 96);
        const current = loadMissionAdoptionHistory();
        const latest = current.length > 0 ? current[0] : null;
        const nowValue = missionAdoptionHistoryTsValue(nowTs);
        const latestValue = latest ? missionAdoptionHistoryTsValue(latest.ts) : 0;
        const sameScore = !!latest
          && Number(latest.score_percent || 0) === Number(scorecard.percent || 0)
          && Number(latest.passed || 0) === Number(scorecard.passed || 0)
          && Number(latest.total || 0) === Number(scorecard.total || 0);
        const withinMergeWindow = latestValue > 0 && nowValue > 0 && Math.abs(nowValue - latestValue) <= 15 * 60 * 1000;
        if (latest && sameScore && withinMergeWindow) {
          current[0] = {
            ...latest,
            ts: nowTs,
            context: context || latest.context || "",
            reason: reason || latest.reason || "",
            actions: Math.max(Number(summary.total_actions || 0), Number(latest.actions || 0)),
            unique_events: Math.max(Number(summary.unique_events || 0), Number(latest.unique_events || 0)),
          };
          return storeMissionAdoptionHistory(current);
        }
        current.unshift({
          id: `${Date.now()}-${Math.floor(Math.random() * 100000)}`,
          ts: nowTs,
          score_percent: Number(scorecard.percent || 0),
          passed: Number(scorecard.passed || 0),
          total: Number(scorecard.total || 0),
          tone: String(scorecard.tone || "warn").trim().toLowerCase(),
          actions: Number(summary.total_actions || 0),
          unique_events: Number(summary.unique_events || 0),
          context,
          reason,
        });
        return storeMissionAdoptionHistory(current);
      }
      function buildMissionAdoptionTrend(history = null, options = {}) {
        const source = Array.isArray(history) ? history : loadMissionAdoptionHistory();
        const sourceOptions = options && typeof options === "object" ? options : {};
        const windowSize = normalizeMissionAdoptionTrendWindow(sourceOptions.window_size, loadMissionAdoptionTrendWindow());
        const scoped = source.slice(0, windowSize);
        const latest = scoped.length > 0 ? scoped[0] : null;
        const previous = scoped.length > 1 ? scoped[1] : null;
        const baseline = scoped.length > 1 ? scoped[scoped.length - 1] : null;
        if (!latest) {
          return {
            tone: "stable",
            label: "NO-DATA",
            delta_percent: 0,
            latest: null,
            previous: null,
            baseline: null,
            sample_size: source.length,
            considered_size: scoped.length,
            window_size: windowSize,
            reason: "потрібно зберегти хоча б одну зміну",
          };
        }
        if (!baseline) {
          return {
            tone: "stable",
            label: "BASELINE",
            delta_percent: 0,
            latest,
            previous,
            baseline: null,
            sample_size: source.length,
            considered_size: scoped.length,
            window_size: windowSize,
            reason: "потрібно щонайменше 2 збереження у вибраному вікні",
          };
        }
        const delta = Number(latest.score_percent || 0) - Number(baseline.score_percent || 0);
        let tone = "stable";
        let label = "STABLE";
        let reason = "динаміка в межах норми";
        if (delta >= 8) {
          tone = "improving";
          label = "IMPROVING";
          reason = "якість adoption зростає";
        } else if (delta <= -8) {
          tone = "regressing";
          label = "REGRESSING";
          reason = "потрібно підсилити coaching у наступній зміні";
        }
        return {
          tone,
          label,
          delta_percent: delta,
          latest,
          previous,
          baseline,
          sample_size: source.length,
          considered_size: scoped.length,
          window_size: windowSize,
          reason,
        };
      }
      function buildMissionAdoptionCompareSummary(trend = null, history = null) {
        const sourceHistory = Array.isArray(history) ? history : loadMissionAdoptionHistory();
        const sourceTrend = trend && typeof trend === "object" ? trend : buildMissionAdoptionTrend(sourceHistory, {});
        const latest = sourceTrend.latest;
        const baseline = sourceTrend.baseline;
        const windowSize = Number(sourceTrend.window_size || loadMissionAdoptionTrendWindow());
        const consideredSize = Number(sourceTrend.considered_size || 0);
        if (!latest) return `Compare: NO-DATA · збережіть handoff для baseline (window ${windowSize}).`;
        const latestText = `${Number(latest.score_percent || 0)}% (${Number(latest.passed || 0)}/${Number(latest.total || 0)})`;
        if (!baseline) return `Compare: now ${latestText} · baseline ще формується · window last ${Math.max(consideredSize, 1)}/${windowSize}.`;
        const baselineText = `${Number(baseline.score_percent || 0)}% (${Number(baseline.passed || 0)}/${Number(baseline.total || 0)})`;
        const delta = Number(sourceTrend.delta_percent || 0);
        const deltaLabel = delta > 0 ? `+${delta}` : `${delta}`;
        return `Compare: now ${latestText} vs baseline ${baselineText} · Δ${deltaLabel}pp · window last ${consideredSize}/${windowSize}.`;
      }
      function buildMissionAdoptionTrendCoach(trend = null, history = null) {
        const sourceHistory = Array.isArray(history) ? history : loadMissionAdoptionHistory();
        const sourceTrend = trend && typeof trend === "object" ? trend : buildMissionAdoptionTrend(sourceHistory, {});
        const latest = sourceTrend.latest;
        const previous = sourceTrend.previous;
        const baseline = sourceTrend.baseline;
        const windowSize = Number(sourceTrend.window_size || loadMissionAdoptionTrendWindow());
        const consideredSize = Number(sourceTrend.considered_size || 0);
        if (!latest) {
          return {
            tone: "start",
            text: `Trend coach: старт — зафіксуйте 2+ handoff notes (window ${windowSize}), щоб отримати baseline.`,
          };
        }
        if (!baseline) {
          return {
            tone: "baseline",
            text: `Trend coach: baseline формується (${Math.max(consideredSize, 1)}/${windowSize}). Продовжуйте стабільні handoff-save.`,
          };
        }
        const deltaBaseline = Number(sourceTrend.delta_percent || 0);
        const deltaPrev = previous
          ? Number(latest.score_percent || 0) - Number(previous.score_percent || 0)
          : 0;
        const prevLabel = deltaPrev > 0 ? `+${deltaPrev}` : `${deltaPrev}`;
        if (String(sourceTrend.tone || "").trim().toLowerCase() === "regressing") {
          return {
            tone: "regressing",
            text: `Trend coach: регрес Δ${deltaBaseline}pp (до baseline), крок до попередньої зміни ${prevLabel}pp. Фокус: nav-search + hotkeys + clear handoff context.`,
          };
        }
        if (String(sourceTrend.tone || "").trim().toLowerCase() === "improving") {
          return {
            tone: "improving",
            text: `Trend coach: прогрес Δ+${Math.abs(deltaBaseline)}pp (до baseline), крок до попередньої зміни ${prevLabel}pp. Закріпіть практики та збережіть у handoff next-actions.`,
          };
        }
        const latestScore = Number(latest.score_percent || 0);
        if (latestScore >= 80) {
          return {
            tone: "stable-good",
            text: `Trend coach: стабільно добре (${latestScore}%). Тримайте cadence handoff і перевіряйте onboarding нових операторів.`,
          };
        }
        return {
          tone: "stable-warn",
          text: `Trend coach: стабільно, але є запас (${latestScore}%). Підсиліть workflow: critical->incidents->audit та фіксуйте ризики в handoff.`,
        };
      }
      function renderMissionHandoffTrendWindowControls(windowSize = null) {
        const activeWindow = normalizeMissionAdoptionTrendWindow(windowSize, loadMissionAdoptionTrendWindow());
        const nodes = Array.from(document.querySelectorAll("button[data-handoff-trend-window]"));
        for (const node of nodes) {
          if (!(node instanceof HTMLButtonElement)) continue;
          const value = normalizeMissionAdoptionTrendWindow(node.getAttribute("data-handoff-trend-window"), activeWindow);
          const active = value === activeWindow;
          node.classList.toggle("active", active);
          node.setAttribute("aria-pressed", active ? "true" : "false");
        }
      }
      function renderMissionHandoffAdoptionTrend(trend = null, history = null) {
        const node = byId("sideHandoffTrend");
        const statusNode = byId("sideHandoffTrendStatus");
        const compareNode = byId("sideHandoffTrendCompare");
        const coachNode = byId("sideHandoffTrendCoach");
        if (!node) return;
        const sourceHistory = Array.isArray(history) ? history : loadMissionAdoptionHistory();
        const trendWindow = loadMissionAdoptionTrendWindow();
        const sourceTrend = trend && typeof trend === "object"
          ? trend
          : buildMissionAdoptionTrend(sourceHistory, { window_size: trendWindow });
        const coach = buildMissionAdoptionTrendCoach(sourceTrend, sourceHistory);
        const lifecycle = buildMissionAdoptionHistoryLifecycle(sourceHistory);
        renderMissionHandoffTrendWindowControls(sourceTrend.window_size);
        const historyStatusText = lifecycle.status_id === "reset_recently"
          ? `History: ${lifecycle.status_label} · ${lifecycle.reset_age_label || "just now"} ago${lifecycle.reset_reason ? ` · ${lifecycle.reset_reason}` : ""} · window=${sourceTrend.window_size}`
          : `History: ${lifecycle.status_label}${lifecycle.reset_recent && lifecycle.reset_age_label ? ` · reset ${lifecycle.reset_age_label} ago` : ""} · window=${sourceTrend.window_size}`;
        if (statusNode) statusNode.textContent = historyStatusText;
        if (compareNode) compareNode.textContent = buildMissionAdoptionCompareSummary(sourceTrend, sourceHistory);
        if (coachNode) coachNode.textContent = String(coach.text || "Trend coach: —");
        if (!sourceTrend.latest) {
          node.textContent = `Trend: NO-DATA · збережіть handoff для формування baseline (window ${sourceTrend.window_size}).`;
          return;
        }
        const latest = sourceTrend.latest;
        const baseline = sourceTrend.baseline;
        const delta = Number(sourceTrend.delta_percent || 0);
        const deltaLabel = delta > 0 ? `+${delta}` : `${delta}`;
        const latestStamp = formatSessionTime(latest.ts);
        if (!baseline) {
          node.textContent = `Trend: ${sourceTrend.label} · ${Number(latest.score_percent || 0)}% (${Number(latest.passed || 0)}/${Number(latest.total || 0)}) · ${latestStamp}\nReason: ${sourceTrend.reason}`;
          return;
        }
        const baselineStamp = formatSessionTime(baseline.ts);
        node.textContent = `Trend: ${sourceTrend.label} · Δ${deltaLabel}pp · now ${Number(latest.score_percent || 0)}% (${Number(latest.passed || 0)}/${Number(latest.total || 0)}) · baseline ${Number(baseline.score_percent || 0)}% (${Number(baseline.passed || 0)}/${Number(baseline.total || 0)})\nWindow: last ${sourceTrend.considered_size}/${sourceTrend.window_size} saves · ${latestStamp} vs ${baselineStamp}\nReason: ${sourceTrend.reason}`;
      }
      function buildSidebarNavAdoptionSnapshot() {
        const telemetry = loadSidebarNavAdoption();
        const summary = buildSidebarNavAdoptionSummary();
        const coaching = buildSidebarNavAdoptionCoaching(summary);
        const scorecard = buildSidebarNavAdoptionScorecard(summary);
        const nextActions = buildSidebarNavNextActions(scorecard, coaching);
        const adoptionHistory = loadMissionAdoptionHistory();
        const trendWindow = loadMissionAdoptionTrendWindow();
        const trend = buildMissionAdoptionTrend(adoptionHistory, { window_size: trendWindow });
        const compareSummary = buildMissionAdoptionCompareSummary(trend, adoptionHistory);
        const trendCoach = buildMissionAdoptionTrendCoach(trend, adoptionHistory);
        const lifecycle = buildMissionAdoptionHistoryLifecycle(adoptionHistory);
        const events = Object.entries(telemetry.events || {})
          .map(([eventId, payload]) => {
            const item = payload && typeof payload === "object" ? payload : {};
            const count = Math.floor(Number(item.count || 0));
            const lastTs = String(item.last_ts || "").trim();
            return {
              event_id: String(eventId || "").trim().toLowerCase(),
              label: navAdoptionEventLabel(eventId),
              count: Number.isFinite(count) && count > 0 ? count : 0,
              last_ts: lastTs,
            };
          })
          .filter((item) => !!item.event_id && item.count > 0)
          .sort((left, right) => {
            if (right.count !== left.count) return right.count - left.count;
            return String(right.last_ts || "").localeCompare(String(left.last_ts || ""));
          });
        return {
          kind: "passengers.mission.nav_adoption_snapshot.v1",
          generated_at: new Date().toISOString(),
          summary,
          coaching,
          scorecard,
          trend,
          trend_window: trendWindow,
          compare_summary: compareSummary,
          trend_coach: trendCoach,
          history_lifecycle: lifecycle,
          history: adoptionHistory.slice(0, 8),
          next_actions: nextActions,
          events,
        };
      }
      function clearSidebarNavAdoption() {
        try { localStorage.removeItem(NAV_ADOPTION_STORAGE_KEY); } catch (_error) {}
        renderMissionHandoffAdoptionSummary();
        return { first_ts: "", last_ts: "", events: {} };
      }
      function renderMissionHandoffAdoptionSummary() {
        const node = byId("sideHandoffAdoption");
        const coachingNode = byId("sideHandoffCoaching");
        const scorecardNode = byId("sideHandoffScorecard");
        const trendNode = byId("sideHandoffTrend");
        const nextActionsNode = byId("sideHandoffNextActions");
        if (!node) return;
        const summary = buildSidebarNavAdoptionSummary();
        const coaching = buildSidebarNavAdoptionCoaching(summary);
        const scorecard = buildSidebarNavAdoptionScorecard(summary);
        const adoptionHistory = loadMissionAdoptionHistory();
        const trend = buildMissionAdoptionTrend(adoptionHistory, { window_size: loadMissionAdoptionTrendWindow() });
        const nextActions = buildSidebarNavNextActions(scorecard, coaching);
        if (summary.total_actions <= 0) {
          node.textContent = "Adoption: nav-flow ще без дій";
          if (coachingNode) coachingNode.textContent = "Coach: стартуй із nav-search та compact-toggle.";
          if (scorecardNode) scorecardNode.textContent = "Scorecard: 0/5 · WARN · немає практик за зміну.";
          if (trendNode) renderMissionHandoffAdoptionTrend(trend, adoptionHistory);
          if (nextActionsNode) nextActionsNode.textContent = "Next actions:\n1) Відкрий цільовий розділ через nav-search + Enter.\n2) Застосуй Shift+Alt+N для швидкого фокусу на пошук.";
          return;
        }
        const top = summary.top_events.length > 0
          ? summary.top_events.map((item) => `${item.label} ${item.count}`).join(" · ")
          : "—";
        const lastStamp = summary.last_ts ? formatSessionTime(summary.last_ts) : "—";
        const compactState = summary.compact_enabled ? "compact=on" : "compact=off";
        const tipsState = summary.onboarding_hidden ? "tips=hidden" : "tips=visible";
        node.textContent = `Adoption: actions=${summary.total_actions} events=${summary.unique_events} · ${compactState} · ${tipsState}\nTop: ${top}\nLast: ${lastStamp}`;
        if (coachingNode) {
          const hint = coaching.hints.length > 0 ? coaching.hints[0] : "Паттерн стабільний, можна масштабувати на нові зміни.";
          coachingNode.textContent = `Coach: ${coaching.level_label} ${coaching.score}% · ${hint}`;
        }
        if (scorecardNode) {
          const statuses = scorecard.checks
            .map((item) => `${item.status === "pass" ? "OK" : "WARN"} ${item.label}`)
            .join(" · ");
          scorecardNode.textContent = `Scorecard: ${scorecard.passed}/${scorecard.total} · ${scorecard.percent}% · ${String(scorecard.tone || "warn").toUpperCase()}\n${statuses}`;
        }
        if (trendNode) renderMissionHandoffAdoptionTrend(trend, adoptionHistory);
        if (nextActionsNode) {
          const lines = nextActions.map((item, index) => `${index + 1}) ${item}`);
          nextActionsNode.textContent = `Next actions:\n${lines.join("\n")}`;
        }
        renderMissionHandoffComposerSummary();
      }
      function recordSidebarNavAdoptionEvent(eventId, options = {}) {
        const cleanId = String(eventId || "").trim().toLowerCase();
        if (!cleanId) return null;
        const source = options && typeof options === "object" ? options : {};
        const now = String(source.ts || new Date().toISOString());
        const telemetry = loadSidebarNavAdoption();
        const events = telemetry.events && typeof telemetry.events === "object" ? telemetry.events : {};
        const current = events[cleanId] && typeof events[cleanId] === "object" ? events[cleanId] : { count: 0, last_ts: "" };
        const count = Math.floor(Number(current.count || 0));
        const nextCount = Number.isFinite(count) && count > 0 ? count + 1 : 1;
        events[cleanId] = {
          count: Math.min(50000, nextCount),
          last_ts: now,
        };
        telemetry.events = events;
        if (!telemetry.first_ts) telemetry.first_ts = now;
        telemetry.last_ts = now;
        storeSidebarNavAdoption(telemetry);
        renderMissionHandoffAdoptionSummary();
        return telemetry;
      }
      function loadSidebarIntentUsage() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(NAV_INTENT_USAGE_STORAGE_KEY) || "{}");
          const source = raw && typeof raw === "object" ? raw : {};
          const output = {};
          for (const item of SIDEBAR_INTENTS) {
            const key = String(item.id || "").trim().toLowerCase();
            const value = Number(source[key] || 0);
            if (!key || !Number.isFinite(value) || value <= 0) continue;
            output[key] = Math.min(200, Math.floor(value));
          }
          return output;
        } catch (_error) {
          return {};
        }
      }
      function storeSidebarIntentUsage(usage) {
        const source = usage && typeof usage === "object" ? usage : {};
        const output = {};
        for (const item of SIDEBAR_INTENTS) {
          const key = String(item.id || "").trim().toLowerCase();
          const value = Number(source[key] || 0);
          if (!key || !Number.isFinite(value) || value <= 0) continue;
          output[key] = Math.min(200, Math.floor(value));
        }
        try { sessionStorage.setItem(NAV_INTENT_USAGE_STORAGE_KEY, JSON.stringify(output)); } catch (_error) {}
        return output;
      }
      function loadSidebarSessionShortcuts() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(NAV_SESSION_SHORTCUTS_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw
            .map((item) => {
              const source = item && typeof item === "object" ? item : {};
              return {
                key: String(source.key || "").trim().toLowerCase(),
                label: String(source.label || "").trim(),
                href: String(source.href || "").trim(),
                ts: String(source.ts || "").trim(),
              };
            })
            .filter((item) => !!item.key && !!item.label && !!item.href)
            .slice(0, 8);
        } catch (_error) {
          return [];
        }
      }
      function storeSidebarSessionShortcuts(items) {
        const source = Array.isArray(items) ? items : [];
        const normalized = source
          .map((item) => {
            const current = item && typeof item === "object" ? item : {};
            return {
              key: String(current.key || "").trim().toLowerCase(),
              label: String(current.label || "").trim(),
              href: String(current.href || "").trim(),
              ts: String(current.ts || "").trim(),
            };
          })
          .filter((item) => !!item.key && !!item.label && !!item.href)
          .slice(0, 8);
        try { sessionStorage.setItem(NAV_SESSION_SHORTCUTS_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function formatSessionTime(ts) {
        const parsed = Date.parse(String(ts || ""));
        if (!Number.isFinite(parsed)) return "now";
        try {
          return new Date(parsed).toLocaleTimeString("uk-UA", { hour: "2-digit", minute: "2-digit" });
        } catch (_error) {
          return "now";
        }
      }
      function copyTextWithFallback(text, promptTitle, successMessage, promptMessage) {
        const payload = String(text || "").trim();
        if (!payload) return Promise.resolve(false);
        if (navigator.clipboard && window.isSecureContext && typeof navigator.clipboard.writeText === "function") {
          return navigator.clipboard.writeText(payload)
            .then(() => {
              const node = byId("sideMissionStatus");
              if (node && successMessage) node.textContent = String(successMessage);
              return true;
            })
            .catch((_error) => {
              window.prompt(String(promptTitle || "Copy text:"), payload);
              const node = byId("sideMissionStatus");
              if (node && promptMessage) node.textContent = String(promptMessage);
              return true;
            });
        }
        window.prompt(String(promptTitle || "Copy text:"), payload);
        const node = byId("sideMissionStatus");
        if (node && promptMessage) node.textContent = String(promptMessage);
        return Promise.resolve(true);
      }
      function renderSidebarSessionShortcuts() {
        const node = byId("sideSessionList");
        if (!node) return;
        const items = loadSidebarSessionShortcuts().slice(0, 5);
        if (items.length === 0) {
          node.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        node.innerHTML = items
          .map((item) => (
            `<a class="sideMiniLink" href="${esc(item.href)}">`
            + `<span>${esc(item.label)}</span>`
            + `<span class="sideSessionMeta">${esc(formatSessionTime(item.ts))}</span>`
            + `</a>`
          ))
          .join("");
      }
      function recordSidebarSessionShortcut(entry) {
        const source = entry && typeof entry === "object" ? entry : {};
        const key = String(source.key || "").trim().toLowerCase();
        const label = String(source.label || "").trim();
        const href = String(source.href || "").trim();
        if (!key || !label || !href) return;
        const list = loadSidebarSessionShortcuts().filter((item) => item.key !== key && item.href !== href);
        list.unshift({ key, label, href, ts: new Date().toISOString() });
        storeSidebarSessionShortcuts(list);
        renderSidebarSessionShortcuts();
      }
      function detectSidebarCurrentIntent() {
        const path = String(window.location.pathname || "");
        const params = new URLSearchParams(String(window.location.search || ""));
        if (path === "/admin/audit") return "audit-last";
        if (path === "/admin/fleet/alerts") {
          const sev = String(params.get("sev") || params.get("severity") || "all").trim().toLowerCase();
          if (sev === "bad") return "alerts-bad";
        }
        if (path === "/admin/fleet/incidents") {
          const status = String(params.get("status") || "all").trim().toLowerCase();
          const includeResolvedRaw = String(params.get("includeResolved") || params.get("include_resolved") || "").trim().toLowerCase();
          const includeResolved = includeResolvedRaw === "1" || includeResolvedRaw === "true" || includeResolvedRaw === "yes" || includeResolvedRaw === "on";
          if (status === "open" && !includeResolved) return "incidents-open";
        }
        return "";
      }
      function buildSidebarContextHint() {
        const path = String(window.location.pathname || "");
        const params = new URLSearchParams(String(window.location.search || ""));
        if (path === "/admin/fleet/alerts") {
          const sev = String(params.get("sev") || params.get("severity") || "all").trim().toLowerCase();
          const central = String(params.get("central") || params.get("central_id") || "").trim();
          const code = String(params.get("code") || "").trim();
          const q = String(params.get("q") || "").trim();
          const parts = [`alerts sev=${sev || "all"}`];
          if (central) parts.push(`central=${central}`);
          if (code) parts.push(`code=${code}`);
          if (q) parts.push(`q=${q}`);
          return `Контекст: ${parts.join(" · ")}`;
        }
        if (path === "/admin/fleet/incidents") {
          const status = String(params.get("status") || "all").trim().toLowerCase();
          const severity = String(params.get("severity") || "all").trim().toLowerCase();
          const includeResolved = String(params.get("includeResolved") || params.get("include_resolved") || "1").trim().toLowerCase();
          const parts = [`incidents status=${status || "all"}`, `sev=${severity || "all"}`];
          if (includeResolved === "0" || includeResolved === "false" || includeResolved === "off" || includeResolved === "no") {
            parts.push("include_resolved=0");
          }
          return `Контекст: ${parts.join(" · ")}`;
        }
        if (path === "/admin/audit") return "Контекст: audit trail / контроль доступів";
        if (path === "/admin/fleet") return "Контекст: fleet overview / monitor";
        return "Контекст: стандартний операторський режим";
      }
      function renderSidebarContextHint() {
        const node = byId("sideContextHint");
        if (!node) return;
        node.textContent = buildSidebarContextHint();
      }
      function buildAdaptiveSidebarIntents() {
        const currentIntent = detectSidebarCurrentIntent();
        const favorites = new Set(loadSidebarFavorites());
        const recents = loadSidebarRecent();
        const usage = loadSidebarIntentUsage();
        const session = loadSidebarSessionShortcuts();
        const source = SIDEBAR_INTENTS.map((item, index) => {
          const intent = item && typeof item === "object" ? item : {};
          const intentId = String(intent.id || "").trim().toLowerCase();
          const navKey = String(intent.nav_key || "").trim().toLowerCase();
          let score = 100 - index * 5;
          if (currentIntent && currentIntent === intentId) score += 60;
          if (favorites.has(navKey)) score += 22;
          if (recents.some((entry) => String(entry.key || "") === navKey)) score += 10;
          score += Math.min(24, Number(usage[intentId] || 0) * 3);
          const sessionIndex = session.findIndex((entry) => String(entry.key || "") === `intent:${intentId}`);
          if (sessionIndex >= 0) score += Math.max(3, 14 - sessionIndex * 3);
          return {
            ...intent,
            id: intentId,
            nav_key: navKey,
            score,
            order: index,
          };
        });
        source.sort((left, right) => {
          if (left.score !== right.score) return right.score - left.score;
          return left.order - right.order;
        });
        return source;
      }
      function renderSidebarIntentSections() {
        const quickNode = byId("sideQuickIntentList");
        const hubNode = byId("sideHubGrid");
        if (!quickNode && !hubNode) return;
        const intents = buildAdaptiveSidebarIntents();
        if (quickNode) {
          quickNode.innerHTML = intents
            .map((intent) => (
              `<a class="sideMiniLink" data-quick-intent="${esc(intent.id)}" href="${esc(intent.href)}">`
              + `<span>${esc(intent.label)}</span>`
              + `<span class="sideMiniHotkey">${esc(intent.hotkey)}</span>`
              + `</a>`
            ))
            .join("");
        }
        if (hubNode) {
          hubNode.innerHTML = intents
            .map((intent) => (
              `<button class="sideHubBtn" type="button" data-intent-run="${esc(intent.id)}">${esc(intent.label)}</button>`
            ))
            .join("");
        }
      }
      function recordSidebarIntentUsage(intentId) {
        const clean = String(intentId || "").trim().toLowerCase();
        if (!clean) return;
        const usage = loadSidebarIntentUsage();
        usage[clean] = Number(usage[clean] || 0) + 1;
        storeSidebarIntentUsage(usage);
      }
      function extractCounterFromNode(node) {
        if (!node) return 0;
        const text = String(node.textContent || "");
        const matches = text.match(/[0-9]+/g);
        if (!matches || matches.length === 0) return 0;
        const last = matches[matches.length - 1];
        const value = Number(last || 0);
        return Number.isFinite(value) ? value : 0;
      }
      function readCounterByIds(ids) {
        const source = Array.isArray(ids) ? ids : [];
        for (const id of source) {
          const node = byId(String(id || ""));
          if (!node) continue;
          const value = extractCounterFromNode(node);
          if (value > 0 || String(node.textContent || "").match(/[0-9]/)) return value;
        }
        return 0;
      }
      function collectMissionMetrics() {
        const bad = readCounterByIds(["prioBadNodes", "sumBad"]);
        const queue = readCounterByIds(["prioQueueNodes", "sumPending"]);
        const wg = readCounterByIds(["prioWgNodes", "sumWg"]);
        const sla = readCounterByIds(["prioSlaBreached", "sumSla", "kpiSla"]);
        const open = readCounterByIds(["sumOpen"]);
        return { bad, queue, wg, sla, open };
      }
      function missionCardTone(value) {
        const num = Number(value || 0);
        if (num > 0) return "bad";
        return "good";
      }
      function renderMissionWidgets() {
        const node = byId("sideMissionGrid");
        if (!node) return;
        const metrics = collectMissionMetrics();
        node.innerHTML = [
          { key: "bad", label: "Bad", value: metrics.bad },
          { key: "open", label: "Open", value: metrics.open },
          { key: "sla", label: "SLA", value: metrics.sla },
          { key: "queue", label: "Queue", value: metrics.queue },
        ]
          .map((item) => (
            `<div class="sideMissionCard ${missionCardTone(item.value)}">`
            + `<strong>${esc(item.value)}</strong>`
            + `<span>${esc(item.label)}</span>`
            + `</div>`
          ))
          .join("");
      }
      function buildMissionPresetOrder() {
        const metrics = collectMissionMetrics();
        const currentIntent = detectSidebarCurrentIntent();
        const usage = loadSidebarIntentUsage();
        const source = MISSION_TRIAGE_PRESETS.map((preset, index) => {
          const item = preset && typeof preset === "object" ? preset : {};
          const metricKey = String(item.metric || "").trim().toLowerCase();
          const metricValue = Number(metrics[metricKey] || 0);
          let score = metricValue * 10 + (100 - index);
          if (currentIntent === "alerts-bad" && item.id === "critical-alerts") score += 40;
          if (currentIntent === "incidents-open" && item.id === "open-incidents") score += 40;
          if (currentIntent === "incidents-open" && item.id === "sla-breach") score += 16;
          score += Math.min(20, Number(usage[`triage:${String(item.id || "").trim().toLowerCase()}`] || 0) * 2);
          return { ...item, score, order: index };
        });
        source.sort((left, right) => {
          if (left.score !== right.score) return right.score - left.score;
          return left.order - right.order;
        });
        return source;
      }
      function renderMissionPresets() {
        const node = byId("sideMissionPresetList");
        if (!node) return;
        const items = buildMissionPresetOrder();
        node.innerHTML = items
          .map((item) => (
            `<button class="sideMissionPresetBtn" type="button" data-triage-run="${esc(item.id)}">${esc(item.label)}</button>`
          ))
          .join("");
      }
      function parseMissionHref(href) {
        const source = String(href || "").trim();
        if (!source) return null;
        try {
          const parsed = new URL(source, window.location.origin);
          return { path: parsed.pathname, params: parsed.searchParams };
        } catch (_error) {
          return null;
        }
      }
      function missionHrefParamCount(href) {
        const parsed = parseMissionHref(href);
        if (!parsed) return 0;
        let count = 0;
        for (const _entry of parsed.params.entries()) count += 1;
        return count;
      }
      function missionHrefMatchesLocation(href) {
        const parsed = parseMissionHref(href);
        if (!parsed) return false;
        const currentPath = String(window.location.pathname || "");
        if (parsed.path !== currentPath) return false;
        const currentParams = new URLSearchParams(String(window.location.search || ""));
        for (const [key, value] of parsed.params.entries()) {
          const currentValue = String(currentParams.get(key) || "");
          if (currentValue !== String(value || "")) return false;
        }
        return true;
      }
      function loadMissionLastPreset() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(MISSION_LAST_PRESET_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          const presetId = String(source.preset_id || "").trim().toLowerCase();
          const ts = String(source.ts || "").trim();
          const sourceText = String(source.source || "").trim();
          const nextIndex = Number(source.next_index);
          if (!presetId) return null;
          return {
            preset_id: presetId,
            ts,
            source: sourceText,
            next_index: Number.isFinite(nextIndex) ? Math.max(0, Math.floor(nextIndex)) : 0,
          };
        } catch (_error) {
          return null;
        }
      }
      function storeMissionLastPreset(presetId, options = {}) {
        const clean = String(presetId || "").trim().toLowerCase();
        if (!clean) return null;
        const nextIndexRaw = Number(options.next_index);
        const payload = {
          preset_id: clean,
          ts: String(options.ts || new Date().toISOString()),
          source: String(options.source || "mission").trim(),
          next_index: Number.isFinite(nextIndexRaw) ? Math.max(0, Math.floor(nextIndexRaw)) : 0,
        };
        try { sessionStorage.setItem(MISSION_LAST_PRESET_STORAGE_KEY, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function detectMissionPresetFromLocation() {
        const candidates = MISSION_TRIAGE_PRESETS
          .map((item, index) => ({
            item,
            order: index,
            weight: missionHrefParamCount(item && item.href),
          }))
          .sort((left, right) => {
            if (left.weight !== right.weight) return right.weight - left.weight;
            return left.order - right.order;
          });
        for (const entry of candidates) {
          const preset = entry.item && typeof entry.item === "object" ? entry.item : {};
          if (missionHrefMatchesLocation(preset.href)) {
            return String(preset.id || "").trim().toLowerCase();
          }
        }
        return "";
      }
      function resolveMissionPresetId() {
        const fromRoute = detectMissionPresetFromLocation();
        if (fromRoute) return fromRoute;
        const last = loadMissionLastPreset();
        if (last && last.preset_id) return String(last.preset_id || "").trim().toLowerCase();
        const ordered = buildMissionPresetOrder();
        if (ordered.length > 0) return String(ordered[0].id || "").trim().toLowerCase();
        return String(MISSION_TRIAGE_PRESETS[0] && MISSION_TRIAGE_PRESETS[0].id || "").trim().toLowerCase();
      }
      function missionPlaybookSteps(presetId) {
        const clean = String(presetId || "").trim().toLowerCase();
        const source = MISSION_PLAYBOOKS[clean];
        if (Array.isArray(source) && source.length > 0) return source;
        return [];
      }
      function buildMissionPlaybookState(presetId) {
        const cleanPreset = String(presetId || "").trim().toLowerCase();
        const steps = missionPlaybookSteps(cleanPreset);
        let activeIndex = -1;
        for (let index = 0; index < steps.length; index += 1) {
          if (missionHrefMatchesLocation(steps[index] && steps[index].href)) {
            activeIndex = index;
            break;
          }
        }
        const last = loadMissionLastPreset();
        let nextIndex = 0;
        if (activeIndex >= 0) nextIndex = activeIndex + 1;
        else if (last && last.preset_id === cleanPreset) nextIndex = Number(last.next_index || 0);
        if (nextIndex < 0) nextIndex = 0;
        if (nextIndex >= steps.length) nextIndex = -1;
        const currentStep = activeIndex >= 0 ? steps[activeIndex] : null;
        const nextStep = nextIndex >= 0 ? steps[nextIndex] : null;
        return {
          preset_id: cleanPreset,
          steps,
          active_index: activeIndex,
          next_index: nextIndex,
          current_step: currentStep,
          next_step: nextStep,
        };
      }
      function missionTrimText(text, maxLength = 160) {
        const source = String(text || "").trim().replace(/\\s+/g, " ");
        if (!source) return "";
        const safeLength = Number.isFinite(Number(maxLength)) ? Math.max(12, Math.floor(maxLength)) : 160;
        if (source.length <= safeLength) return source;
        return `${source.slice(0, Math.max(8, safeLength - 1)).trim()}…`;
      }
      function missionPresetLabelById(presetId) {
        const clean = String(presetId || "").trim().toLowerCase();
        const preset = MISSION_TRIAGE_PRESETS.find((item) => String(item.id || "").trim().toLowerCase() === clean);
        return String(preset && preset.label || clean || "preset").trim();
      }
      function buildMissionChecklistSummary(state) {
        const source = state && typeof state === "object" ? state : {};
        const steps = Array.isArray(source.steps) ? source.steps : [];
        const activeIndex = Number(source.active_index);
        let doneCount = 0;
        if (Number.isFinite(activeIndex) && activeIndex > 0) doneCount = Math.min(steps.length, Math.floor(activeIndex));
        else if (Number.isFinite(activeIndex) && activeIndex === -1 && Number(source.next_index) === -1) doneCount = steps.length;
        const totalCount = steps.length;
        const percent = totalCount > 0 ? Math.round((doneCount / totalCount) * 100) : 0;
        return {
          done: doneCount,
          total: totalCount,
          percent,
          is_complete: totalCount > 0 && doneCount >= totalCount,
        };
      }
      function listMissionSnapshots() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_SNAPSHOT_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw
            .map((item) => {
              const source = item && typeof item === "object" ? item : {};
              const metrics = source.metrics && typeof source.metrics === "object" ? source.metrics : {};
              const context = source.context && typeof source.context === "object" ? source.context : {};
              const checklist = source.checklist && typeof source.checklist === "object" ? source.checklist : {};
              return {
                id: String(source.id || "").trim(),
                ts: String(source.ts || "").trim(),
                preset_id: String(source.preset_id || "").trim().toLowerCase(),
                preset_label: String(source.preset_label || "").trim(),
                route: String(source.route || "").trim(),
                metrics: {
                  bad: Number(metrics.bad || 0),
                  open: Number(metrics.open || 0),
                  sla: Number(metrics.sla || 0),
                  queue: Number(metrics.queue || 0),
                  wg: Number(metrics.wg || 0),
                },
                checklist: {
                  done: Number(checklist.done || 0),
                  total: Number(checklist.total || 0),
                },
                context: {
                  label: String(context.label || "").trim(),
                  central_id: String(context.central_id || "").trim(),
                  code: String(context.code || "").trim(),
                },
                handoff_text: String(source.handoff_text || "").trim(),
              };
            })
            .filter((item) => !!item.ts)
            .slice(0, MISSION_EVIDENCE_LIMIT);
        } catch (_error) {
          return [];
        }
      }
      function storeMissionSnapshots(items) {
        const source = Array.isArray(items) ? items : [];
        const normalized = source
          .map((item) => {
            const current = item && typeof item === "object" ? item : {};
            return {
              id: String(current.id || "").trim(),
              ts: String(current.ts || "").trim(),
              preset_id: String(current.preset_id || "").trim().toLowerCase(),
              preset_label: String(current.preset_label || "").trim(),
              route: String(current.route || "").trim(),
              metrics: current.metrics && typeof current.metrics === "object" ? current.metrics : {},
              checklist: current.checklist && typeof current.checklist === "object" ? current.checklist : {},
              context: current.context && typeof current.context === "object" ? current.context : {},
              handoff_text: String(current.handoff_text || "").trim(),
            };
          })
          .filter((item) => !!item.ts)
          .slice(0, MISSION_EVIDENCE_LIMIT);
        try { localStorage.setItem(MISSION_SNAPSHOT_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function appendMissionSnapshot(entry) {
        const current = listMissionSnapshots();
        const source = entry && typeof entry === "object" ? entry : {};
        current.unshift(source);
        return storeMissionSnapshots(current);
      }
      function buildMissionSnapshotPayload(options = {}) {
        const source = options && typeof options === "object" ? options : {};
        const presetId = String(source.preset_id || resolveMissionPresetId()).trim().toLowerCase();
        const presetLabel = missionPresetLabelById(presetId);
        const playbookState = buildMissionPlaybookState(presetId);
        const checklist = buildMissionChecklistSummary(playbookState);
        const context = loadWorkspaceContext({ maxAgeSec: 14 * 24 * 3600 });
        const metrics = collectMissionMetrics();
        const handoff = loadMissionHandoffNote();
        const ts = new Date().toISOString();
        return {
          id: `${Date.now()}-${Math.floor(Math.random() * 100000)}`,
          ts,
          preset_id: presetId,
          preset_label: presetLabel,
          route: `${String(window.location.pathname || "")}${String(window.location.search || "")}`,
          metrics: {
            bad: Number(metrics.bad || 0),
            open: Number(metrics.open || 0),
            sla: Number(metrics.sla || 0),
            queue: Number(metrics.queue || 0),
            wg: Number(metrics.wg || 0),
          },
          checklist: {
            done: Number(checklist.done || 0),
            total: Number(checklist.total || 0),
          },
          context: context ? {
            label: String(context.label || "").trim(),
            central_id: String(context.central_id || "").trim(),
            code: String(context.code || "").trim(),
          } : {
            label: "",
            central_id: "",
            code: "",
          },
          handoff_text: missionTrimText(handoff && handoff.text || "", 160),
        };
      }
      function captureMissionSnapshot(options = {}) {
        const payload = buildMissionSnapshotPayload(options);
        appendMissionSnapshot(payload);
        return payload;
      }
      function renderMissionSnapshotSummary() {
        const node = byId("sideMissionSnapshotSummary");
        if (!node) return;
        const snapshots = listMissionSnapshots();
        if (snapshots.length === 0) {
          node.textContent = "Snapshot: —";
          return;
        }
        const item = snapshots[0];
        const stamp = formatSessionTime(item.ts);
        const checklistDone = Number(item.checklist && item.checklist.done || 0);
        const checklistTotal = Number(item.checklist && item.checklist.total || 0);
        const contextLabel = missionTrimText(String(item.context && item.context.label || ""), 72);
        const parts = [
          `Snapshot ${stamp}`,
          `${String(item.preset_label || item.preset_id || "preset")}`,
          `bad=${Number(item.metrics && item.metrics.bad || 0)} open=${Number(item.metrics && item.metrics.open || 0)} sla=${Number(item.metrics && item.metrics.sla || 0)} queue=${Number(item.metrics && item.metrics.queue || 0)}`,
          `checklist ${checklistDone}/${checklistTotal}`,
        ];
        if (contextLabel) parts.push(`ctx: ${contextLabel}`);
        if (item.handoff_text) parts.push(`handoff: ${missionTrimText(item.handoff_text, 84)}`);
        node.textContent = parts.join("\n");
      }
      function runMissionSnapshotAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        const statusNode = byId("sideMissionStatus");
        if (mode === "capture") {
          const payload = captureMissionSnapshot();
          appendMissionHandoffTimelineEvent("snapshot", {
            ts: payload.ts,
            context: String(payload.context && payload.context.label || ""),
            text: `preset=${payload.preset_id} bad=${payload.metrics.bad} open=${payload.metrics.open} sla=${payload.metrics.sla} queue=${payload.metrics.queue}`,
          });
          renderMissionSnapshotSummary();
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Snapshot: ${formatSessionTime(payload.ts)} збережено`;
          return true;
        }
        if (mode === "show") {
          const snapshots = listMissionSnapshots();
          if (snapshots.length === 0) {
            if (statusNode) statusNode.textContent = "Snapshot: журнал порожній";
            return false;
          }
          window.prompt("Mission snapshots (JSON):", JSON.stringify({ kind: "passengers.mission.snapshots.v1", items: snapshots.slice(0, 12) }, null, 2));
          if (statusNode) statusNode.textContent = `Snapshot: показано ${Math.min(12, snapshots.length)}`;
          return true;
        }
        if (mode === "clear") {
          storeMissionSnapshots([]);
          renderMissionSnapshotSummary();
          if (statusNode) statusNode.textContent = "Snapshot: журнал очищено";
          return true;
        }
        return false;
      }
      function loadMissionResponsePack() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(MISSION_RESPONSE_PACK_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          const kind = String(source.kind || "").trim();
          const generatedAt = String(source.generated_at || "").trim();
          if (!kind || !generatedAt) return null;
          return source;
        } catch (_error) {
          return null;
        }
      }
      function storeMissionResponsePack(pack) {
        const source = pack && typeof pack === "object" ? pack : null;
        if (!source) return null;
        try { sessionStorage.setItem(MISSION_RESPONSE_PACK_STORAGE_KEY, JSON.stringify(source)); } catch (_error) {}
        return source;
      }
      function clearMissionResponsePack() {
        try { sessionStorage.removeItem(MISSION_RESPONSE_PACK_STORAGE_KEY); } catch (_error) {}
      }
      function normalizeMissionRoutingProfileId(value, fallback = "auto") {
        const clean = String(value || "").trim().toLowerCase();
        if (!clean) return String(fallback || "auto");
        if (clean === "auto") return "auto";
        if (MISSION_ROUTING_PROFILES.some((item) => String(item.id || "").trim().toLowerCase() === clean)) return clean;
        return String(fallback || "auto");
      }
      function normalizeMissionRoutingTemplateKind(value, fallback = "short") {
        const clean = String(value || "").trim().toLowerCase();
        if (!clean) return String(fallback || "short");
        if (MISSION_CHANNEL_TEMPLATE_VARIANTS.some((item) => String(item.id || "").trim().toLowerCase() === clean)) return clean;
        return String(fallback || "short");
      }
      function loadMissionRoutingSelection() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(MISSION_RESPONSE_ROUTING_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          return {
            profile_id: normalizeMissionRoutingProfileId(source.profile_id, "auto"),
            template_kind: normalizeMissionRoutingTemplateKind(source.template_kind, "short"),
          };
        } catch (_error) {
          return { profile_id: "auto", template_kind: "short" };
        }
      }
      function storeMissionRoutingSelection(selection = {}) {
        const payload = {
          profile_id: normalizeMissionRoutingProfileId(selection.profile_id, "auto"),
          template_kind: normalizeMissionRoutingTemplateKind(selection.template_kind, "short"),
        };
        try { sessionStorage.setItem(MISSION_RESPONSE_ROUTING_STORAGE_KEY, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function missionRoutingProfileById(profileId) {
        const clean = String(profileId || "").trim().toLowerCase();
        return MISSION_ROUTING_PROFILES.find((item) => String(item.id || "").trim().toLowerCase() === clean) || null;
      }
      function parseIncidentDetailFromPath(pathname) {
        const path = String(pathname || "").trim();
        const match = path.match(/^\\/admin\\/fleet\\/incidents\\/([^\\/]+)\\/([^\\/]+)$/);
        if (!match) return { central_id: "", code: "" };
        let centralId = "";
        let code = "";
        try { centralId = decodeURIComponent(String(match[1] || "")); } catch (_error) { centralId = String(match[1] || ""); }
        try { code = decodeURIComponent(String(match[2] || "")); } catch (_error) { code = String(match[2] || ""); }
        return {
          central_id: String(centralId || "").trim(),
          code: String(code || "").trim(),
        };
      }
      function buildMissionRoutingSignal(pack = {}) {
        const source = pack && typeof pack === "object" ? pack : {};
        const context = source.context && typeof source.context === "object" ? source.context : {};
        const path = String(window.location.pathname || "").trim();
        const params = new URLSearchParams(String(window.location.search || ""));
        const detail = parseIncidentDetailFromPath(path);
        const centralId = String(
          context.central_id
          || params.get("central_id")
          || params.get("central")
          || detail.central_id
          || ""
        ).trim();
        const code = String(
          context.code
          || params.get("code")
          || detail.code
          || ""
        ).trim().toLowerCase();
        let severity = String(params.get("severity") || params.get("sev") || "").trim().toLowerCase();
        if (!severity && path === "/admin/fleet/alerts") severity = "all";
        if (!severity && Number(source.snapshot && source.snapshot.metrics && source.snapshot.metrics.bad || 0) > 0) severity = "bad";
        if (!severity) severity = "all";
        let status = String(params.get("status") || "").trim().toLowerCase();
        if (!status && (path === "/admin/fleet/incidents" || path.startsWith("/admin/fleet/incidents/"))) status = "open";
        if (!status) status = "all";
        const contextLabel = String(context.label || (centralId && code ? `${centralId}:${code}` : centralId || code || "")).trim();
        return {
          path,
          central_id: centralId,
          code,
          severity,
          status,
          context_label: contextLabel,
        };
      }
      function missionRoutingIncludesAny(textValue, candidates) {
        const text = String(textValue || "").trim().toLowerCase();
        const list = Array.isArray(candidates) ? candidates : [];
        if (!text || list.length === 0) return false;
        return list.some((item) => {
          const token = String(item || "").trim().toLowerCase();
          if (!token) return false;
          return text.includes(token);
        });
      }
      function missionRoutingMatchProfile(profile, signal) {
        const candidate = profile && typeof profile === "object" ? profile : {};
        const match = candidate.match && typeof candidate.match === "object" ? candidate.match : {};
        const source = signal && typeof signal === "object" ? signal : {};
        const reasons = [];
        if (Array.isArray(match.path_any) && match.path_any.length > 0) {
          const pathOk = match.path_any.some((item) => String(item || "").trim() === String(source.path || ""));
          if (!pathOk) return { ok: false, reasons: [] };
          reasons.push(`path=${String(source.path || "")}`);
        }
        if (Array.isArray(match.status_any) && match.status_any.length > 0) {
          const status = String(source.status || "").trim().toLowerCase();
          const statusOk = match.status_any.some((item) => {
            const candidateStatus = String(item || "").trim().toLowerCase();
            if (!candidateStatus || candidateStatus === "all") return true;
            return candidateStatus === status;
          });
          if (!statusOk) return { ok: false, reasons: [] };
          reasons.push(`status=${status || "all"}`);
        }
        if (Array.isArray(match.severity_any) && match.severity_any.length > 0) {
          const severity = String(source.severity || "").trim().toLowerCase();
          const severityOk = match.severity_any.some((item) => {
            const candidateSeverity = String(item || "").trim().toLowerCase();
            if (!candidateSeverity || candidateSeverity === "all") return true;
            return candidateSeverity === severity;
          });
          if (!severityOk) return { ok: false, reasons: [] };
          reasons.push(`sev=${severity || "all"}`);
        }
        if (Array.isArray(match.code_contains_any) && match.code_contains_any.length > 0) {
          const code = String(source.code || "").trim().toLowerCase();
          const codeOk = missionRoutingIncludesAny(code, match.code_contains_any);
          if (!codeOk) return { ok: false, reasons: [] };
          reasons.push(`code=${code || "n/a"}`);
        }
        return { ok: true, reasons };
      }
      function resolveMissionRoutingProfile(pack = {}, selection = {}) {
        const signal = buildMissionRoutingSignal(pack);
        const preferredId = normalizeMissionRoutingProfileId(selection.profile_id, "auto");
        if (preferredId !== "auto") {
          const manualProfile = missionRoutingProfileById(preferredId) || missionRoutingProfileById("standard-ops");
          const tested = missionRoutingMatchProfile(manualProfile, signal);
          return {
            mode: "manual",
            signal,
            profile: manualProfile || MISSION_ROUTING_PROFILES[MISSION_ROUTING_PROFILES.length - 1],
            reasons: tested.ok ? tested.reasons : ["manual override"],
          };
        }
        let winner = missionRoutingProfileById("standard-ops") || MISSION_ROUTING_PROFILES[MISSION_ROUTING_PROFILES.length - 1];
        let winnerReasons = ["fallback"];
        let winnerScore = Number(winner && winner.rank || 0);
        for (const profile of MISSION_ROUTING_PROFILES) {
          const profileId = String(profile && profile.id || "").trim().toLowerCase();
          if (!profileId || profileId === "standard-ops") continue;
          const tested = missionRoutingMatchProfile(profile, signal);
          if (!tested.ok) continue;
          const score = Number(profile.rank || 0) * 10 + tested.reasons.length;
          if (score > winnerScore) {
            winner = profile;
            winnerReasons = tested.reasons;
            winnerScore = score;
          }
        }
        return {
          mode: "auto",
          signal,
          profile: winner,
          reasons: winnerReasons,
        };
      }
      function buildMissionRoutingDispatchNote(pack = {}) {
        const source = pack && typeof pack === "object" ? pack : {};
        const routing = source.routing && typeof source.routing === "object" ? source.routing : {};
        const signal = source.routing_signal && typeof source.routing_signal === "object" ? source.routing_signal : {};
        const context = source.context && typeof source.context === "object" ? source.context : {};
        const checklist = source.checklist && typeof source.checklist === "object" ? source.checklist : {};
        const lines = [];
        lines.push(`Dispatch: ${String(routing.channel || "ops-general")} (${String(routing.priority || "p2").toUpperCase()})`);
        lines.push(`Profile: ${String(routing.profile_label || routing.profile_id || "standard-ops")} · mode=${String(routing.mode || "auto")}`);
        lines.push(`Route: ${String(source.route || "—")}`);
        lines.push(`Context: ${String(context.label || signal.context_label || "—")}`);
        lines.push(`Incident: central=${String(signal.central_id || context.central_id || "—")} code=${String(signal.code || context.code || "—")}`);
        lines.push(`State: sev=${String(signal.severity || "all")} status=${String(signal.status || "all")}`);
        lines.push(`Checklist: ${Number(checklist.done || 0)}/${Number(checklist.total || 0)} (${Number(checklist.percent || 0)}%)`);
        const reason = Array.isArray(routing.reasons) ? routing.reasons.filter((item) => !!String(item || "").trim()) : [];
        if (reason.length > 0) lines.push(`Rule: ${reason.join(", ")}`);
        return lines.join("\n");
      }
      function buildMissionChannelTemplate(pack = {}, templateKind = "short") {
        const source = pack && typeof pack === "object" ? pack : {};
        const kind = normalizeMissionRoutingTemplateKind(templateKind, "short");
        const routing = source.routing && typeof source.routing === "object" ? source.routing : {};
        const signal = source.routing_signal && typeof source.routing_signal === "object" ? source.routing_signal : {};
        const context = source.context && typeof source.context === "object" ? source.context : {};
        const snapshot = source.snapshot && typeof source.snapshot === "object" ? source.snapshot : {};
        const metrics = snapshot.metrics && typeof snapshot.metrics === "object" ? snapshot.metrics : {};
        const checklist = source.checklist && typeof source.checklist === "object" ? source.checklist : {};
        const timeline = Array.isArray(source.handoff_timeline) ? source.handoff_timeline : [];
        const common = [
          `system: ${String(context.central_id || signal.central_id || "—")}`,
          `code: ${String(signal.code || context.code || "—")}`,
          `severity/status: ${String(signal.severity || "all")}/${String(signal.status || "all")}`,
          `route: ${String(routing.channel || "ops-general")} (${String(routing.priority || "p2").toUpperCase()})`,
          `checklist: ${Number(checklist.done || 0)}/${Number(checklist.total || 0)} (${Number(checklist.percent || 0)}%)`,
        ];
        if (kind === "short") {
          return [
            `[${String(routing.priority || "p2").toUpperCase()}] ${String(routing.channel || "ops-general")} · ${String(context.label || signal.context_label || "incident")}`,
            `ts: ${String(source.generated_at || new Date().toISOString())}`,
            ...common,
            `next: triage + action owner + ETA`,
          ].join("\n");
        }
        if (kind === "audit") {
          const reason = Array.isArray(routing.reasons) ? routing.reasons.join(", ") : "";
          return [
            `Audit Handoff (${String(routing.profile_label || routing.profile_id || "standard-ops")})`,
            `generated_at: ${String(source.generated_at || new Date().toISOString())}`,
            `route: ${String(source.route || "—")}`,
            ...common,
            `metrics: bad=${Number(metrics.bad || 0)} open=${Number(metrics.open || 0)} sla=${Number(metrics.sla || 0)} queue=${Number(metrics.queue || 0)} wg=${Number(metrics.wg || 0)}`,
            `rule_match: ${reason || "fallback"}`,
            `timeline_last: ${timeline.length > 0 ? missionTrimText(String(timeline[0] && timeline[0].text || "—"), 92) : "—"}`,
          ].join("\n");
        }
        const timelineLines = timeline.slice(0, 5).map((item) => {
          const stamp = formatSessionTime(String(item && item.ts || ""));
          const text = missionTrimText(String(item && item.text || ""), 110);
          return `- [${stamp}] ${String(item && item.kind || "event")}: ${text || "—"}`;
        });
        return [
          `Escalation Package (${String(routing.profile_label || routing.profile_id || "standard-ops")})`,
          `generated_at: ${String(source.generated_at || new Date().toISOString())}`,
          ...common,
          `context: ${String(context.label || signal.context_label || "—")}`,
          `metrics: bad=${Number(metrics.bad || 0)} open=${Number(metrics.open || 0)} sla=${Number(metrics.sla || 0)} queue=${Number(metrics.queue || 0)} wg=${Number(metrics.wg || 0)}`,
          `handoff: ${missionTrimText(String(source.handoff_text || ""), 160) || "—"}`,
          "recent_timeline:",
          ...(timelineLines.length > 0 ? timelineLines : ["- —"]),
        ].join("\n");
      }
      function buildMissionChannelTemplates(pack = {}) {
        const source = pack && typeof pack === "object" ? pack : {};
        const output = {};
        for (const variant of MISSION_CHANNEL_TEMPLATE_VARIANTS) {
          const templateId = String(variant && variant.id || "").trim().toLowerCase();
          if (!templateId) continue;
          output[templateId] = buildMissionChannelTemplate(source, templateId);
        }
        return output;
      }
      function renderMissionResponseRoutingControls() {
        const profileNode = byId("sideRoutingProfile");
        const templateNode = byId("sideRoutingTemplate");
        if (profileNode && profileNode.dataset.ready !== "1") {
          const options = [{ id: "auto", label: "Auto (rule-based)" }]
            .concat(MISSION_ROUTING_PROFILES.map((item) => ({
              id: String(item.id || "").trim().toLowerCase(),
              label: String(item.label || item.id || "").trim(),
            })));
          profileNode.innerHTML = options
            .map((item) => `<option value="${esc(item.id)}">${esc(item.label)}</option>`)
            .join("");
          profileNode.dataset.ready = "1";
        }
        if (templateNode && templateNode.dataset.ready !== "1") {
          templateNode.innerHTML = MISSION_CHANNEL_TEMPLATE_VARIANTS
            .map((item) => `<option value="${esc(item.id)}">${esc(item.label)}</option>`)
            .join("");
          templateNode.dataset.ready = "1";
        }
        const selection = loadMissionRoutingSelection();
        if (profileNode) profileNode.value = normalizeMissionRoutingProfileId(selection.profile_id, "auto");
        if (templateNode) templateNode.value = normalizeMissionRoutingTemplateKind(selection.template_kind, "short");
      }
      function syncMissionRoutingSelectionFromControls(options = {}) {
        const source = options && typeof options === "object" ? options : {};
        const profileNode = byId("sideRoutingProfile");
        const templateNode = byId("sideRoutingTemplate");
        const current = loadMissionRoutingSelection();
        const next = storeMissionRoutingSelection({
          profile_id: source.forceAuto ? "auto" : String(profileNode && profileNode.value || current.profile_id || "auto"),
          template_kind: String(templateNode && templateNode.value || current.template_kind || "short"),
        });
        renderMissionResponseRoutingControls();
        return next;
      }
      function renderMissionResponseRoutingSummary() {
        const node = byId("sideResponseRoutingSummary");
        if (!node) return;
        const pack = loadMissionResponsePack();
        if (!pack) {
          node.textContent = "Routing: —";
          return;
        }
        const routing = pack.routing && typeof pack.routing === "object" ? pack.routing : {};
        const signal = pack.routing_signal && typeof pack.routing_signal === "object" ? pack.routing_signal : {};
        const templateKind = normalizeMissionRoutingTemplateKind(pack.channel_template_kind || "short", "short");
        const reasons = Array.isArray(routing.reasons) ? routing.reasons.filter((item) => !!String(item || "").trim()) : [];
        const lines = [
          `Routing ${String(routing.mode || "auto")} · ${String(routing.profile_label || routing.profile_id || "standard-ops")}`,
          `channel=${String(routing.channel || "ops-general")} priority=${String(routing.priority || "p2").toUpperCase()} template=${templateKind}`,
          `sev=${String(signal.severity || "all")} status=${String(signal.status || "all")} code=${String(signal.code || "—")}`,
        ];
        if (reasons.length > 0) lines.push(`rule: ${reasons.join(", ")}`);
        node.textContent = lines.join("\n");
      }
      function normalizeMissionDeliveryAdapterId(value, fallback = "telegram") {
        const clean = String(value || "").trim().toLowerCase();
        if (!clean) return String(fallback || "telegram");
        if (MISSION_DELIVERY_ADAPTERS.some((item) => String(item.id || "").trim().toLowerCase() === clean)) return clean;
        return String(fallback || "telegram");
      }
      function normalizeMissionDeliveryVariantKind(value, fallback = "short") {
        return normalizeMissionRoutingTemplateKind(value, fallback || "short");
      }
      function loadMissionDeliverySelection() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(MISSION_DELIVERY_ADAPTER_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          return {
            adapter_id: normalizeMissionDeliveryAdapterId(source.adapter_id, "telegram"),
            variant_kind: normalizeMissionDeliveryVariantKind(source.variant_kind, "short"),
          };
        } catch (_error) {
          return { adapter_id: "telegram", variant_kind: "short" };
        }
      }
      function storeMissionDeliverySelection(selection = {}) {
        const payload = {
          adapter_id: normalizeMissionDeliveryAdapterId(selection.adapter_id, "telegram"),
          variant_kind: normalizeMissionDeliveryVariantKind(selection.variant_kind, "short"),
        };
        try { sessionStorage.setItem(MISSION_DELIVERY_ADAPTER_STORAGE_KEY, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function missionDeliveryAdapterById(adapterId) {
        const clean = String(adapterId || "").trim().toLowerCase();
        return MISSION_DELIVERY_ADAPTERS.find((item) => String(item.id || "").trim().toLowerCase() === clean) || null;
      }
      function buildMissionDeliveryPayload(pack = {}, adapterId = "telegram", variantKind = "short") {
        const source = pack && typeof pack === "object" ? pack : {};
        const routing = source.routing && typeof source.routing === "object" ? source.routing : {};
        const signal = source.routing_signal && typeof source.routing_signal === "object" ? source.routing_signal : {};
        const context = source.context && typeof source.context === "object" ? source.context : {};
        const checklist = source.checklist && typeof source.checklist === "object" ? source.checklist : {};
        const deliveryAdapter = missionDeliveryAdapterById(adapterId) || missionDeliveryAdapterById("telegram");
        const safeAdapterId = String(deliveryAdapter && deliveryAdapter.id || "telegram");
        const safeVariant = normalizeMissionDeliveryVariantKind(variantKind, "short");
        const templateSource = source.channel_templates && typeof source.channel_templates === "object"
          ? source.channel_templates
          : {};
        const message = String(
          templateSource[safeVariant]
          || source.channel_template
          || source.handoff_template
          || ""
        ).trim();
        const dispatch = String(source.routing_dispatch || buildMissionRoutingDispatchNote(source) || "").trim();
        const priority = String(routing.priority || "p2").toUpperCase();
        const incidentLabel = String(context.label || signal.context_label || "incident").trim();
        const central = String(context.central_id || signal.central_id || "—").trim() || "—";
        const code = String(context.code || signal.code || "—").trim() || "—";
        const subject = `[Passengers][${priority}] ${incidentLabel}`;
        const title = `[${priority}] ${incidentLabel} (${code})`;
        const body = [message, "", dispatch].join("\n").trim();
        if (safeAdapterId === "telegram") {
          const preview = [
            "#telegram",
            `target: ${String(deliveryAdapter && deliveryAdapter.target || "@ops_alerts")}`,
            `priority: ${priority}`,
            `route_channel: ${String(routing.channel || "ops-general")}`,
            "---",
            body,
          ].join("\n");
          return {
            kind: "passengers.mission.delivery_payload.v1",
            adapter_id: safeAdapterId,
            adapter_label: String(deliveryAdapter && deliveryAdapter.label || "Telegram"),
            variant_kind: safeVariant,
            target: String(deliveryAdapter && deliveryAdapter.target || "@ops_alerts"),
            transport: String(deliveryAdapter && deliveryAdapter.transport || "chat"),
            central_id: central,
            code,
            subject: "",
            title,
            message: body,
            preview,
          };
        }
        if (safeAdapterId === "email") {
          const preview = [
            "#email",
            `to: ${String(deliveryAdapter && deliveryAdapter.target || "ops@company.local")}`,
            `subject: ${subject}`,
            "---",
            body,
          ].join("\n");
          return {
            kind: "passengers.mission.delivery_payload.v1",
            adapter_id: safeAdapterId,
            adapter_label: String(deliveryAdapter && deliveryAdapter.label || "Email"),
            variant_kind: safeVariant,
            target: String(deliveryAdapter && deliveryAdapter.target || "ops@company.local"),
            transport: String(deliveryAdapter && deliveryAdapter.transport || "email"),
            central_id: central,
            code,
            subject,
            title,
            message: body,
            preview,
          };
        }
        const ticketPayload = {
          title,
          priority,
          central_id: central,
          code,
          severity: String(signal.severity || "all"),
          status: String(signal.status || "all"),
          channel: String(routing.channel || "ops-general"),
          checklist: `${Number(checklist.done || 0)}/${Number(checklist.total || 0)} (${Number(checklist.percent || 0)}%)`,
          description: body,
          generated_at: String(source.generated_at || new Date().toISOString()),
        };
        const preview = [
          "#ticket",
          `queue: ${String(deliveryAdapter && deliveryAdapter.target || "ops-queue")}`,
          `title: ${title}`,
          "---",
          JSON.stringify(ticketPayload, null, 2),
        ].join("\n");
        return {
          kind: "passengers.mission.delivery_payload.v1",
          adapter_id: safeAdapterId,
          adapter_label: String(deliveryAdapter && deliveryAdapter.label || "Web Ticket"),
          variant_kind: safeVariant,
          target: String(deliveryAdapter && deliveryAdapter.target || "ops-queue"),
          transport: String(deliveryAdapter && deliveryAdapter.transport || "ticket"),
          central_id: central,
          code,
          subject,
          title,
          message: body,
          payload: ticketPayload,
          preview,
        };
      }
      function buildMissionDeliveryTemplates(pack = {}) {
        const source = pack && typeof pack === "object" ? pack : {};
        const output = {};
        for (const adapter of MISSION_DELIVERY_ADAPTERS) {
          const adapterId = String(adapter && adapter.id || "").trim().toLowerCase();
          if (!adapterId) continue;
          output[adapterId] = {};
          for (const variant of MISSION_CHANNEL_TEMPLATE_VARIANTS) {
            const variantId = String(variant && variant.id || "").trim().toLowerCase();
            if (!variantId) continue;
            output[adapterId][variantId] = buildMissionDeliveryPayload(source, adapterId, variantId);
          }
        }
        return output;
      }
      function renderMissionDeliveryControls() {
        const adapterNode = byId("sideDeliveryAdapter");
        const variantNode = byId("sideDeliveryVariant");
        if (adapterNode && adapterNode.dataset.ready !== "1") {
          adapterNode.innerHTML = MISSION_DELIVERY_ADAPTERS
            .map((item) => `<option value="${esc(item.id)}">${esc(item.label)}</option>`)
            .join("");
          adapterNode.dataset.ready = "1";
        }
        if (variantNode && variantNode.dataset.ready !== "1") {
          variantNode.innerHTML = MISSION_CHANNEL_TEMPLATE_VARIANTS
            .map((item) => `<option value="${esc(item.id)}">${esc(item.label)}</option>`)
            .join("");
          variantNode.dataset.ready = "1";
        }
        const selection = loadMissionDeliverySelection();
        if (adapterNode) adapterNode.value = normalizeMissionDeliveryAdapterId(selection.adapter_id, "telegram");
        if (variantNode) variantNode.value = normalizeMissionDeliveryVariantKind(selection.variant_kind, "short");
      }
      function syncMissionDeliverySelectionFromControls(options = {}) {
        const source = options && typeof options === "object" ? options : {};
        const adapterNode = byId("sideDeliveryAdapter");
        const variantNode = byId("sideDeliveryVariant");
        const current = loadMissionDeliverySelection();
        const next = storeMissionDeliverySelection({
          adapter_id: source.adapter_id || String(adapterNode && adapterNode.value || current.adapter_id || "telegram"),
          variant_kind: source.variant_kind || String(variantNode && variantNode.value || current.variant_kind || "short"),
        });
        renderMissionDeliveryControls();
        return next;
      }
      function normalizeMissionDeliveryPolicyProfileId(value, fallback = "auto") {
        const clean = String(value || "").trim().toLowerCase();
        if (!clean) return String(fallback || "auto");
        if (clean === "auto") return "auto";
        if (MISSION_DELIVERY_POLICY_PROFILES.some((item) => String(item.id || "").trim().toLowerCase() === clean)) return clean;
        return String(fallback || "auto");
      }
      function loadMissionDeliveryPolicySelection() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(MISSION_DELIVERY_POLICY_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          return { profile_id: normalizeMissionDeliveryPolicyProfileId(source.profile_id, "auto") };
        } catch (_error) {
          return { profile_id: "auto" };
        }
      }
      function storeMissionDeliveryPolicySelection(selection = {}) {
        const payload = { profile_id: normalizeMissionDeliveryPolicyProfileId(selection.profile_id, "auto") };
        try { sessionStorage.setItem(MISSION_DELIVERY_POLICY_STORAGE_KEY, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function missionDeliveryPolicyById(profileId) {
        const clean = String(profileId || "").trim().toLowerCase();
        return MISSION_DELIVERY_POLICY_PROFILES.find((item) => String(item.id || "").trim().toLowerCase() === clean) || null;
      }
      function resolveMissionDeliveryPolicyProfile(pack = null) {
        const selection = loadMissionDeliveryPolicySelection();
        const currentPack = pack && typeof pack === "object" ? pack : loadMissionResponsePack();
        const signal = currentPack && currentPack.routing_signal && typeof currentPack.routing_signal === "object"
          ? currentPack.routing_signal
          : {};
        const routing = currentPack && currentPack.routing && typeof currentPack.routing === "object"
          ? currentPack.routing
          : {};
        const routePath = String(currentPack && currentPack.route || window.location.pathname || "").trim().toLowerCase();
        const selectedId = normalizeMissionDeliveryPolicyProfileId(selection.profile_id, "auto");
        if (selectedId !== "auto") {
          const explicit = missionDeliveryPolicyById(selectedId) || missionDeliveryPolicyById("balanced");
          return {
            mode: "override",
            selected_profile_id: selectedId,
            profile_id: String(explicit && explicit.id || "balanced"),
            profile: explicit || null,
            reason: "manual session override",
          };
        }
        const severity = String(signal.severity || "").trim().toLowerCase();
        const status = String(signal.status || "").trim().toLowerCase();
        const priority = String(routing.priority || "").trim().toLowerCase();
        let autoId = "balanced";
        let reason = "default balanced";
        if (severity === "bad" || severity === "critical" || priority === "p1") {
          autoId = "aggressive";
          reason = "critical severity/priority";
        } else if (priority === "p3" || status === "resolved" || routePath.startsWith("/admin/audit")) {
          autoId = "conservative";
          reason = "low-priority or audit context";
        }
        const resolved = missionDeliveryPolicyById(autoId) || missionDeliveryPolicyById("balanced");
        return {
          mode: "auto",
          selected_profile_id: "auto",
          profile_id: String(resolved && resolved.id || "balanced"),
          profile: resolved || null,
          reason,
        };
      }
      function syncMissionDeliveryPolicySelectionFromControls(options = {}) {
        const source = options && typeof options === "object" ? options : {};
        const profileNode = byId("sideDeliveryPolicyProfile");
        const current = loadMissionDeliveryPolicySelection();
        const next = storeMissionDeliveryPolicySelection({
          profile_id: String(source.profile_id || (profileNode && profileNode.value) || current.profile_id || "auto"),
        });
        return next;
      }
      function renderMissionDeliveryPolicyControls(pack = null) {
        const profileNode = byId("sideDeliveryPolicyProfile");
        const summaryNode = byId("sideDeliveryPolicySummary");
        if (profileNode && profileNode.dataset.ready !== "1") {
          profileNode.innerHTML = [
            '<option value="auto">Auto</option>',
            ...MISSION_DELIVERY_POLICY_PROFILES.map((item) => `<option value="${esc(item.id)}">${esc(item.label)}</option>`),
          ].join("");
          profileNode.dataset.ready = "1";
        }
        const selection = loadMissionDeliveryPolicySelection();
        if (profileNode) profileNode.value = normalizeMissionDeliveryPolicyProfileId(selection.profile_id, "auto");
        const resolved = resolveMissionDeliveryPolicyProfile(pack);
        if (summaryNode) {
          const profile = resolved.profile && typeof resolved.profile === "object" ? resolved.profile : {};
          const warnMin = Math.max(1, Math.round(Number(profile.warn_sec || MISSION_DELIVERY_SLA_WARN_SEC) / 60));
          const staleMin = Math.max(warnMin + 1, Math.round(Number(profile.stale_sec || MISSION_DELIVERY_SLA_STALE_SEC) / 60));
          const bulkLimit = Math.max(1, Number(profile.bulk_limit || MISSION_DELIVERY_BULK_LIMIT));
          summaryNode.textContent = `Політика: ${String(profile.label || "Balanced")} (${resolved.mode}) · warn=${warnMin}m stale=${staleMin}m bulk=${bulkLimit} · ${String(resolved.reason || "")}`;
        }
      }
      function renderMissionDeliverySummary() {
        const node = byId("sideDeliverySummary");
        if (!node) return;
        const pack = loadMissionResponsePack();
        if (!pack) {
          node.textContent = "Delivery: —";
          return;
        }
        const delivery = pack.delivery && typeof pack.delivery === "object" ? pack.delivery : {};
        const payload = pack.delivery_payload && typeof pack.delivery_payload === "object" ? pack.delivery_payload : {};
        const lines = [
          `Delivery ${String(payload.adapter_label || delivery.adapter_id || "telegram")} · ${String(payload.variant_kind || delivery.variant_kind || "short")}`,
          `target=${String(payload.target || "—")} transport=${String(payload.transport || "—")}`,
        ];
        if (payload.subject) lines.push(`subject: ${missionTrimText(String(payload.subject || ""), 92)}`);
        lines.push(`preview: ${missionTrimText(String(payload.preview || payload.message || ""), 92) || "—"}`);
        node.textContent = lines.join("\n");
      }
      function listMissionDeliveryJournal() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_DELIVERY_JOURNAL_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw
            .map((item) => {
              const source = item && typeof item === "object" ? item : {};
              return {
                id: String(source.id || "").trim(),
                ts: String(source.ts || "").trim(),
                action: String(source.action || "").trim().toLowerCase(),
                adapter_id: String(source.adapter_id || "").trim().toLowerCase(),
                variant_kind: String(source.variant_kind || "").trim().toLowerCase(),
                context: missionTrimText(String(source.context || ""), 96),
                route_channel: String(source.route_channel || "").trim(),
                note: missionTrimText(String(source.note || ""), 180),
              };
            })
            .filter((item) => !!item.ts && !!item.action && !!item.adapter_id && !!item.variant_kind)
            .slice(0, MISSION_DELIVERY_JOURNAL_LIMIT);
        } catch (_error) {
          return [];
        }
      }
      function storeMissionDeliveryJournal(items) {
        const source = Array.isArray(items) ? items : [];
        const normalized = source
          .map((item) => {
            const current = item && typeof item === "object" ? item : {};
            return {
              id: String(current.id || "").trim(),
              ts: String(current.ts || "").trim(),
              action: String(current.action || "").trim().toLowerCase(),
              adapter_id: String(current.adapter_id || "").trim().toLowerCase(),
              variant_kind: String(current.variant_kind || "").trim().toLowerCase(),
              context: missionTrimText(String(current.context || ""), 96),
              route_channel: String(current.route_channel || "").trim(),
              note: missionTrimText(String(current.note || ""), 180),
            };
          })
          .filter((item) => !!item.ts && !!item.action && !!item.adapter_id && !!item.variant_kind)
          .slice(0, MISSION_DELIVERY_JOURNAL_LIMIT);
        try { localStorage.setItem(MISSION_DELIVERY_JOURNAL_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function appendMissionDeliveryJournalEvent(payload = {}) {
        const source = payload && typeof payload === "object" ? payload : {};
        const action = String(source.action || "").trim().toLowerCase();
        const adapterId = normalizeMissionDeliveryAdapterId(source.adapter_id, "telegram");
        const variantKind = normalizeMissionDeliveryVariantKind(source.variant_kind, "short");
        if (!action) return [];
        const current = listMissionDeliveryJournal();
        current.unshift({
          id: `${Date.now()}-${Math.floor(Math.random() * 100000)}`,
          ts: String(source.ts || new Date().toISOString()),
          action,
          adapter_id: adapterId,
          variant_kind: variantKind,
          context: missionTrimText(String(source.context || ""), 96),
          route_channel: missionTrimText(String(source.route_channel || ""), 48),
          note: missionTrimText(String(source.note || ""), 180),
        });
        return storeMissionDeliveryJournal(current);
      }
      function clearMissionDeliveryJournal() {
        return storeMissionDeliveryJournal([]);
      }
      function missionDeliveryJournalActionLabel(action) {
        const clean = String(action || "").trim().toLowerCase();
        if (clean === "apply") return "apply";
        if (clean === "copy") return "copy";
        if (clean === "retry") return "retry";
        if (clean === "ack") return "ack";
        if (clean === "escalate") return "escalate";
        return clean || "event";
      }
      function missionDeliveryActionTsValue(ts) {
        const parsed = Date.parse(String(ts || ""));
        return Number.isFinite(parsed) ? parsed : 0;
      }
      function buildMissionDeliverySlaState(status = null, options = {}) {
        const source = status && typeof status === "object" ? status : {};
        const sourceOptions = options && typeof options === "object" ? options : {};
        const policyWrapper = sourceOptions.policy && typeof sourceOptions.policy === "object"
          ? sourceOptions.policy
          : resolveMissionDeliveryPolicyProfile(sourceOptions.pack || null);
        const policy = policyWrapper.profile && typeof policyWrapper.profile === "object"
          ? policyWrapper.profile
          : missionDeliveryPolicyById("balanced")
          || { warn_sec: MISSION_DELIVERY_SLA_WARN_SEC, stale_sec: MISSION_DELIVERY_SLA_STALE_SEC, stale_strategy: "escalate-first", warn_strategy: "ack" };
        const warnSec = Math.max(60, Number(policy.warn_sec || MISSION_DELIVERY_SLA_WARN_SEC));
        const staleSec = Math.max(warnSec + 60, Number(policy.stale_sec || MISSION_DELIVERY_SLA_STALE_SEC));
        const staleStrategy = String(policy.stale_strategy || "escalate-first").trim().toLowerCase();
        const warnStrategy = String(policy.warn_strategy || "ack").trim().toLowerCase();
        const deliveryEvent = source.last_delivery_event && typeof source.last_delivery_event === "object"
          ? source.last_delivery_event
          : null;
        const ackEvent = source.last_ack_event && typeof source.last_ack_event === "object"
          ? source.last_ack_event
          : null;
        const escalateEvent = source.last_escalate_event && typeof source.last_escalate_event === "object"
          ? source.last_escalate_event
          : null;
        const deliveryTs = missionDeliveryActionTsValue(deliveryEvent && deliveryEvent.ts);
        const ackTs = missionDeliveryActionTsValue(ackEvent && ackEvent.ts);
        const hasDelivery = !!deliveryEvent && deliveryTs > 0;
        const hasAck = !!ackEvent && ackTs > 0;
        const pendingAck = hasDelivery && (!hasAck || ackTs < deliveryTs);
        const referenceEvent = pendingAck
          ? deliveryEvent
          : (ackEvent || deliveryEvent || escalateEvent || source.last_event || null);
        const ageSec = referenceEvent
          ? contextAgeSec(String(referenceEvent.ts || ""))
          : null;
        const staleByAge = Number.isFinite(ageSec) && Number(ageSec) > staleSec;
        const warnByAge = Number.isFinite(ageSec) && Number(ageSec) > warnSec;
        let tone = "stale";
        let label = "STALE";
        let reason = "немає подій доставки";
        if (!hasDelivery) {
          tone = "stale";
          label = "STALE";
          reason = "немає delivery attempt";
        } else if (pendingAck && staleByAge) {
          tone = "stale";
          label = "STALE";
          reason = "очікується ack";
        } else if (pendingAck && warnByAge) {
          tone = "warn";
          label = "WARN";
          reason = warnStrategy === "observe" ? "ack очікується (conservative)" : "ack затримується";
        } else if (pendingAck) {
          tone = "fresh";
          label = "FRESH";
          reason = "очікується ack";
        } else if (warnByAge) {
          tone = "warn";
          label = "WARN";
          reason = "потрібно оновити ack";
        } else {
          tone = "fresh";
          label = "FRESH";
          reason = "ack підтверджено";
        }
        if (pendingAck && escalateEvent) {
          const escalateTs = missionDeliveryActionTsValue(escalateEvent.ts);
          if (escalateTs >= deliveryTs) {
            tone = "stale";
            label = "STALE";
            reason = "ескалація без ack";
          }
        }
        if (pendingAck && staleByAge && staleStrategy === "retry-first") {
          reason = "SLA stale: retry-before-escalate";
        }
        return {
          tone,
          label,
          reason,
          age_sec: Number.isFinite(ageSec) ? Number(ageSec) : null,
          age_label: Number.isFinite(ageSec) ? formatAgeShort(Number(ageSec)) : "—",
          pending_ack: pendingAck,
          warn_sec: warnSec,
          stale_sec: staleSec,
          policy_id: String(policy.id || "balanced"),
          policy_label: String(policy.label || "Balanced"),
          stale_strategy: staleStrategy,
          warn_strategy: warnStrategy,
          reference_event: referenceEvent,
        };
      }
      function buildMissionDeliveryHandoffStatus(pack = null, options = {}) {
        const sourcePack = pack && typeof pack === "object" ? pack : loadMissionResponsePack();
        const currentPack = sourcePack && typeof sourcePack === "object" ? sourcePack : null;
        const sourceOptions = options && typeof options === "object" ? options : {};
        const policy = sourceOptions.policy && typeof sourceOptions.policy === "object"
          ? sourceOptions.policy
          : resolveMissionDeliveryPolicyProfile(currentPack);
        const payload = currentPack && currentPack.delivery_payload && typeof currentPack.delivery_payload === "object"
          ? currentPack.delivery_payload
          : {};
        const routing = currentPack && currentPack.routing && typeof currentPack.routing === "object"
          ? currentPack.routing
          : {};
        const context = currentPack && currentPack.context && typeof currentPack.context === "object"
          ? currentPack.context
          : {};
        const contextLabel = missionTrimText(String(context.label || ""), 96);
        const preview = String(payload.preview || payload.message || "").trim();
        const journal = listMissionDeliveryJournal();
        const latest = journal.length > 0 ? journal[0] : null;
        const deliveryEvents = journal.filter((item) => {
          const action = String(item.action || "").trim().toLowerCase();
          return action === "apply" || action === "copy" || action === "retry";
        });
        const ackEvents = journal.filter((item) => String(item.action || "").trim().toLowerCase() === "ack");
        const escalateEvents = journal.filter((item) => String(item.action || "").trim().toLowerCase() === "escalate");
        const contextJournal = contextLabel
          ? journal.filter((item) => String(item.context || "").trim() === contextLabel)
          : journal;
        const contextDeliveryEvents = contextLabel
          ? deliveryEvents.filter((item) => String(item.context || "").trim() === contextLabel)
          : deliveryEvents;
        const contextAckEvents = contextLabel
          ? ackEvents.filter((item) => String(item.context || "").trim() === contextLabel)
          : ackEvents;
        const contextEscalateEvents = contextLabel
          ? escalateEvents.filter((item) => String(item.context || "").trim() === contextLabel)
          : escalateEvents;
        const latestCopy = contextJournal.find((item) => String(item.action || "") === "copy") || null;
        const lastDeliveryEvent = contextDeliveryEvents[0] || null;
        const lastAckEvent = contextAckEvents[0] || null;
        const lastEscalateEvent = contextEscalateEvents[0] || null;
        const contextEvent = contextDeliveryEvents[0] || contextJournal[0] || latest;
        const ready = !!currentPack && !!preview && !!contextEvent;
        const reasons = [];
        if (!currentPack) reasons.push("немає response pack");
        if (!preview) reasons.push("немає delivery payload");
        if (!contextEvent) reasons.push("немає запису у delivery journal");
        const sla = buildMissionDeliverySlaState({
          last_delivery_event: lastDeliveryEvent,
          last_ack_event: lastAckEvent,
          last_escalate_event: lastEscalateEvent,
          last_event: contextJournal[0] || latest,
        }, { policy, pack: currentPack });
        return {
          ready,
          reasons,
          journal_size: journal.length,
          last_event: latest,
          last_copy_event: latestCopy,
          last_delivery_event: lastDeliveryEvent,
          last_ack_event: lastAckEvent,
          last_escalate_event: lastEscalateEvent,
          ack_pending: !!sla.pending_ack,
          context_event: contextEvent,
          context_label: contextLabel,
          queue_channel: String(routing.channel || "ops-general"),
          adapter_label: String(payload.adapter_label || payload.adapter_id || "telegram"),
          adapter_id: String(payload.adapter_id || "telegram"),
          variant_kind: String(payload.variant_kind || "short"),
          target: String(payload.target || "—"),
          policy,
          sla,
          generated_at: String(currentPack && currentPack.generated_at || ""),
        };
      }
      function renderMissionDeliveryHandoffStatus() {
        const node = byId("sideDeliveryHandoffStatus");
        if (!node) return;
        const status = buildMissionDeliveryHandoffStatus();
        const lines = [
          status.ready ? "Queue-ready: так" : "Queue-ready: ні",
          `adapter=${status.adapter_label} · variant=${status.variant_kind} · queue=${status.queue_channel}`,
          `journal=${Number(status.journal_size || 0)} · target=${status.target}`,
        ];
        if (status.context_label) lines.push(`context: ${status.context_label}`);
        if (status.last_copy_event) {
          lines.push(`last copy: ${formatSessionTime(String(status.last_copy_event.ts || ""))}`);
        } else if (status.last_event) {
          lines.push(`last action: ${formatSessionTime(String(status.last_event.ts || ""))} (${missionDeliveryJournalActionLabel(status.last_event.action)})`);
        }
        if (!status.ready && status.reasons.length > 0) lines.push(`needs: ${status.reasons.join("; ")}`);
        node.textContent = lines.join("\n");
      }
      function renderMissionDeliverySlaStatus() {
        const node = byId("sideDeliverySlaStatus");
        if (!node) return;
        const status = buildMissionDeliveryHandoffStatus();
        const sla = status.sla && typeof status.sla === "object"
          ? status.sla
          : buildMissionDeliverySlaState(status);
        const tone = String(sla.tone || "stale").trim().toLowerCase();
        const label = String(sla.label || tone || "STALE").trim().toUpperCase();
        const ageLabel = String(sla.age_label || "—").trim() || "—";
        const reason = missionTrimText(String(sla.reason || "немає даних"), 120);
        const metaBits = [
          `timer=${ageLabel}`,
          status.ack_pending ? "ack=pending" : "ack=ok",
        ];
        if (status.last_ack_event) {
          metaBits.push(`ack@${formatSessionTime(String(status.last_ack_event.ts || ""))}`);
        }
        node.innerHTML = (
          `<div class="sideSlaRow">`
          + `<span class="sideSlaBadge ${esc(tone)}">${esc(`SLA ${label}`)}</span>`
          + `<span class="sideSlaMeta">${esc(metaBits.join(" · "))}</span>`
          + `</div>`
          + `<div class="sideSlaReason">${esc(reason || "—")}</div>`
        );
      }
      function buildMissionDeliveryContextStates(options = {}) {
        const sourceOptions = options && typeof options === "object" ? options : {};
        const policy = sourceOptions.policy && typeof sourceOptions.policy === "object"
          ? sourceOptions.policy
          : resolveMissionDeliveryPolicyProfile(sourceOptions.pack || null);
        const journal = listMissionDeliveryJournal();
        const byContext = new Map();
        for (const item of journal) {
          const contextLabel = missionTrimText(String(item && item.context || "").trim(), 96);
          const key = contextLabel || "__global__";
          const action = String(item && item.action || "").trim().toLowerCase();
          let state = byContext.get(key);
          if (!state) {
            state = {
              key,
              context_label: contextLabel,
              last_event: null,
              last_delivery_event: null,
              last_ack_event: null,
              last_escalate_event: null,
            };
            byContext.set(key, state);
          }
          if (!state.last_event) state.last_event = item;
          if (!state.last_delivery_event && (action === "apply" || action === "copy" || action === "retry")) {
            state.last_delivery_event = item;
          }
          if (!state.last_ack_event && action === "ack") state.last_ack_event = item;
          if (!state.last_escalate_event && action === "escalate") state.last_escalate_event = item;
        }
        const states = [];
        for (const entry of byContext.values()) {
          const sla = buildMissionDeliverySlaState({
            last_delivery_event: entry.last_delivery_event,
            last_ack_event: entry.last_ack_event,
            last_escalate_event: entry.last_escalate_event,
            last_event: entry.last_event,
          }, { policy, pack: sourceOptions.pack || null });
          const deliveryTs = missionDeliveryActionTsValue(entry.last_delivery_event && entry.last_delivery_event.ts);
          const ackTs = missionDeliveryActionTsValue(entry.last_ack_event && entry.last_ack_event.ts);
          const escalateTs = missionDeliveryActionTsValue(entry.last_escalate_event && entry.last_escalate_event.ts);
          states.push({
            key: entry.key,
            context_label: entry.context_label,
            last_event: entry.last_event,
            last_delivery_event: entry.last_delivery_event,
            last_ack_event: entry.last_ack_event,
            last_escalate_event: entry.last_escalate_event,
            delivery_ts: deliveryTs,
            ack_ts: ackTs,
            escalate_ts: escalateTs,
            escalated_since_delivery: deliveryTs > 0 && escalateTs >= deliveryTs,
            pending_ack: deliveryTs > 0 && ackTs < deliveryTs,
            sla,
            age_sec: Number(sla && sla.age_sec || 0),
          });
        }
        return states;
      }
      function collectMissionDeliveryBulkCandidates(mode, options = {}) {
        const cleanMode = String(mode || "").trim().toLowerCase();
        const sourceOptions = options && typeof options === "object" ? options : {};
        const policy = sourceOptions.policy && typeof sourceOptions.policy === "object"
          ? sourceOptions.policy
          : resolveMissionDeliveryPolicyProfile(sourceOptions.pack || null);
        const profile = policy.profile && typeof policy.profile === "object" ? policy.profile : {};
        const limit = Math.max(1, Number(sourceOptions.limit || profile.bulk_limit || MISSION_DELIVERY_BULK_LIMIT));
        const source = buildMissionDeliveryContextStates({ policy, pack: sourceOptions.pack || null });
        let candidates = source
          .filter((item) => {
            if (!item || !item.pending_ack) return false;
            if (cleanMode === "ack") return String(item.sla && item.sla.tone || "") !== "stale";
            if (cleanMode === "retry") return String(item.sla && item.sla.tone || "") === "stale" && !!item.escalated_since_delivery;
            if (cleanMode === "escalate") return String(item.sla && item.sla.tone || "") === "stale" && !item.escalated_since_delivery;
            return false;
          })
          .sort((left, right) => Number(right.age_sec || 0) - Number(left.age_sec || 0));
        if (candidates.length <= 0) {
          const status = buildMissionDeliveryHandoffStatus(sourceOptions.pack || null, { policy });
          const contextLabel = missionTrimText(String(status.context_label || ""), 96);
          const slaTone = String(status.sla && status.sla.tone || "").trim().toLowerCase();
          const stale = slaTone === "stale";
          const canUseCurrent = !!contextLabel && !!status.ack_pending && (
            (cleanMode === "ack" && !stale)
            || (cleanMode === "retry" && stale && !!status.last_escalate_event)
            || (cleanMode === "escalate" && stale && !status.last_escalate_event)
          );
          if (canUseCurrent) {
            candidates = [{
              key: contextLabel,
              context_label: contextLabel,
              age_sec: Number(status.sla && status.sla.age_sec || 0),
            }];
          }
        }
        return candidates.slice(0, limit);
      }
      function buildMissionDeliveryAutomationPlan(pack = null) {
        const policy = resolveMissionDeliveryPolicyProfile(pack);
        const profile = policy.profile && typeof policy.profile === "object" ? policy.profile : {};
        const status = buildMissionDeliveryHandoffStatus(pack, { policy });
        const ackBulk = collectMissionDeliveryBulkCandidates("ack", { policy, pack });
        const retryBulk = collectMissionDeliveryBulkCandidates("retry", { policy, pack });
        const escalateBulk = collectMissionDeliveryBulkCandidates("escalate", { policy, pack });
        const staleStrategy = String(profile.stale_strategy || "escalate-first").trim().toLowerCase();
        const warnStrategy = String(profile.warn_strategy || "ack").trim().toLowerCase();
        let action = "none";
        let label = "Немає дії";
        let reason = "delivery стан стабільний";
        let confidence = "low";
        let explain = "policy stable";
        if (!status.ready) {
          action = "apply-delivery";
          label = "Оновити delivery";
          reason = status.reasons.length > 0 ? status.reasons.join("; ") : "підготуй queue-ready стан";
          confidence = "high";
          explain = "queue-ready prerequisites missing";
        } else if (status.ack_pending && String(status.sla && status.sla.tone || "") === "stale") {
          if (staleStrategy === "retry-first") {
            if (status.last_escalate_event && status.last_delivery_event) {
              const escalateTs = missionDeliveryActionTsValue(status.last_escalate_event.ts);
              const deliveryTs = missionDeliveryActionTsValue(status.last_delivery_event.ts);
              if (escalateTs >= deliveryTs) {
                action = "escalate-delivery";
                label = "Escalate delivery";
                reason = "SLA stale і retry не допоміг";
                confidence = "high";
                explain = "conservative stale strategy with prior retry/escalate trail";
              } else {
                action = "retry-delivery";
                label = "Retry delivery";
                reason = "SLA stale: conservative policy => retry first";
                confidence = "high";
                explain = "conservative stale strategy";
              }
            } else {
              action = "retry-delivery";
              label = "Retry delivery";
              reason = "SLA stale: conservative policy => retry first";
              confidence = "high";
              explain = "conservative stale strategy";
            }
          } else {
            if (status.last_escalate_event && status.last_delivery_event) {
              const escalateTs = missionDeliveryActionTsValue(status.last_escalate_event.ts);
              const deliveryTs = missionDeliveryActionTsValue(status.last_delivery_event.ts);
              if (escalateTs >= deliveryTs) {
                action = "retry-delivery";
                label = "Retry delivery";
                reason = "SLA stale і вже була ескалація для цієї доставки";
                confidence = "high";
                explain = "stale escalate-first strategy with existing escalation";
              } else {
                action = "escalate-delivery";
                label = "Escalate delivery";
                reason = "SLA stale і ACK відсутній";
                confidence = "high";
                explain = "stale escalate-first strategy";
              }
            } else {
              action = "escalate-delivery";
              label = "Escalate delivery";
              reason = "SLA stale і ACK відсутній";
              confidence = "high";
              explain = "stale escalate-first strategy";
            }
          }
        } else if (status.ack_pending) {
          if (warnStrategy === "observe" && String(status.sla && status.sla.tone || "") !== "warn") {
            action = "none";
            label = "Спостереження";
            reason = "conservative policy: очікуємо без примусової дії";
            confidence = "low";
            explain = "warn strategy observe";
          } else {
            action = "ack-delivery";
            label = "ACK delivery";
            reason = "delivery виконано, потрібне підтвердження";
            confidence = String(status.sla && status.sla.tone || "") === "warn" ? "high" : "medium";
            explain = warnStrategy === "ack-fast" ? "aggressive warn strategy" : "balanced/conservative ack strategy";
          }
        } else if (String(status.sla && status.sla.tone || "") === "warn") {
          if (warnStrategy === "ack-fast") {
            action = "ack-delivery";
            label = "ACK delivery";
            reason = "aggressive policy: confirm sooner on warn";
            confidence = "high";
            explain = "aggressive warn strategy";
          } else {
            action = "retry-delivery";
            label = "Retry delivery";
            reason = "ACK застаріває, рекомендовано повторити доставку";
            confidence = "medium";
            explain = "warn fallback retry";
          }
        }
        return {
          policy,
          status,
          suggestion: {
            action,
            label,
            reason: missionTrimText(String(reason || ""), 180),
            confidence,
            explain: missionTrimText(String(explain || ""), 180),
          },
          bulk: {
            ack_pending: ackBulk,
            retry_stale: retryBulk,
            escalate_stale: escalateBulk,
          },
        };
      }
      function renderMissionDeliveryAutomationSummary() {
        const node = byId("sideDeliveryAutomationSummary");
        if (!node) return;
        const runBtn = byId("sideDeliverySuggestedAction");
        const stickyRunBtn = byId("sideDeliveryStickySuggested");
        const plan = buildMissionDeliveryAutomationPlan();
        const policy = plan.policy && typeof plan.policy === "object" ? plan.policy : resolveMissionDeliveryPolicyProfile();
        const policyProfile = policy.profile && typeof policy.profile === "object" ? policy.profile : {};
        const suggestion = plan.suggestion && typeof plan.suggestion === "object" ? plan.suggestion : {};
        const action = String(suggestion.action || "none").trim().toLowerCase();
        const confidence = String(suggestion.confidence || "low").trim().toUpperCase();
        const reason = missionTrimText(String(suggestion.reason || "—"), 160);
        const explain = missionTrimText(String(suggestion.explain || ""), 160);
        const bulk = plan.bulk && typeof plan.bulk === "object" ? plan.bulk : {};
        if (runBtn) {
          runBtn.disabled = action === "none";
          runBtn.dataset.responsePackAction = action === "none" ? "" : "apply-delivery-suggestion";
          runBtn.classList.toggle("primary", action !== "none");
          runBtn.title = action === "none"
            ? "Немає рекомендованої дії"
            : `Рекомендовано: ${String(suggestion.label || action)} (${confidence})`;
          runBtn.textContent = action === "none"
            ? "Apply suggestion"
            : `Apply: ${missionTrimText(String(suggestion.label || action), 20)}`;
        }
        if (stickyRunBtn) {
          stickyRunBtn.disabled = action === "none";
          stickyRunBtn.dataset.responsePackAction = action === "none" ? "" : "apply-delivery-suggestion";
          stickyRunBtn.classList.toggle("primary", action !== "none");
          stickyRunBtn.title = action === "none"
            ? "Немає рекомендованої дії"
            : `Рекомендовано: ${String(suggestion.label || action)} (${confidence})`;
        }
        const bulkText = `bulk ack=${Number((bulk.ack_pending || []).length)} retry=${Number((bulk.retry_stale || []).length)} escalate=${Number((bulk.escalate_stale || []).length)}`;
        const policyText = `policy=${String(policyProfile.id || policy.profile_id || "balanced")} (${String(policy.mode || "auto")})`;
        node.innerHTML = (
          `<div class="sideSuggestRow">`
          + `<span class="sideSuggestBadge">${esc(`suggestion: ${action}`)}</span>`
          + `<span class="sideSlaMeta">${esc(`confidence=${confidence}`)}</span>`
          + `</div>`
          + `<div class="sideSuggestReason">${esc(reason || "—")}</div>`
          + `<div class="sideSlaMeta">${esc(policyText)}</div>`
          + (explain ? `<div class="sideSlaMeta">${esc(`why: ${explain}`)}</div>` : "")
          + `<div class="sideSlaMeta">${esc(bulkText)}</div>`
        );
      }
      function buildMissionHandoffTemplate(pack = {}) {
        const source = pack && typeof pack === "object" ? pack : {};
        const snapshot = source.snapshot && typeof source.snapshot === "object" ? source.snapshot : null;
        const checklist = source.checklist && typeof source.checklist === "object" ? source.checklist : {};
        const timeline = Array.isArray(source.handoff_timeline) ? source.handoff_timeline : [];
        const context = source.context && typeof source.context === "object" ? source.context : {};
        const lines = [];
        lines.push("Оперативна передача зміни");
        lines.push(`Час: ${String(source.generated_at || new Date().toISOString())}`);
        lines.push(`Preset: ${String(source.preset_label || source.preset_id || "—")}`);
        lines.push(`Route: ${String(source.route || "—")}`);
        lines.push(`Checklist: ${Number(checklist.done || 0)}/${Number(checklist.total || 0)} (${Number(checklist.percent || 0)}%)`);
        const contextLabel = missionTrimText(String(context.label || ""), 96);
        if (contextLabel) lines.push(`Контекст: ${contextLabel}`);
        if (snapshot && snapshot.metrics) {
          lines.push(
            `Метрики: bad=${Number(snapshot.metrics.bad || 0)} open=${Number(snapshot.metrics.open || 0)} sla=${Number(snapshot.metrics.sla || 0)} queue=${Number(snapshot.metrics.queue || 0)} wg=${Number(snapshot.metrics.wg || 0)}`
          );
        }
        const handoffText = missionTrimText(String(source.handoff_text || ""), 220);
        if (handoffText) lines.push(`Нотатка: ${handoffText}`);
        if (timeline.length > 0) {
          lines.push("Останні події:");
          for (const item of timeline.slice(0, 5)) {
            const stamp = formatSessionTime(String(item && item.ts || ""));
            const kind = String(item && item.kind || "event");
            const text = missionTrimText(String(item && item.text || ""), 96);
            lines.push(`- [${stamp}] ${kind}: ${text || "—"}`);
          }
        }
        return lines.join("\n");
      }
      function buildMissionResponsePack(options = {}) {
        const source = options && typeof options === "object" ? options : {};
        const presetId = String(source.preset_id || resolveMissionPresetId()).trim().toLowerCase();
        let snapshot = source.snapshot && typeof source.snapshot === "object" ? source.snapshot : null;
        if (!snapshot && source.capture) {
          snapshot = captureMissionSnapshot({ preset_id: presetId });
        }
        if (!snapshot) {
          const snapshots = listMissionSnapshots();
          snapshot = snapshots.length > 0 ? snapshots[0] : null;
        }
        if (!snapshot) {
          snapshot = buildMissionSnapshotPayload({ preset_id: presetId });
        }
        const checklist = snapshot && snapshot.checklist && typeof snapshot.checklist === "object"
          ? {
              done: Number(snapshot.checklist.done || 0),
              total: Number(snapshot.checklist.total || 0),
              percent: Number(snapshot.checklist.total || 0) > 0
                ? Math.round((Number(snapshot.checklist.done || 0) / Number(snapshot.checklist.total || 1)) * 100)
                : 0,
            }
          : (() => {
              const state = buildMissionPlaybookState(presetId);
              const summary = buildMissionChecklistSummary(state);
              return {
                done: Number(summary.done || 0),
                total: Number(summary.total || 0),
                percent: Number(summary.percent || 0),
              };
            })();
        const context = loadWorkspaceContext({ maxAgeSec: 14 * 24 * 3600 });
        const timeline = listMissionHandoffTimeline().slice(0, 20);
        const handoff = loadMissionHandoffNote();
        const pack = {
          kind: "passengers.mission.response_pack.v1",
          generated_at: new Date().toISOString(),
          route: `${String(window.location.pathname || "")}${String(window.location.search || "")}`,
          preset_id: String(snapshot && snapshot.preset_id || presetId || ""),
          preset_label: String(snapshot && snapshot.preset_label || missionPresetLabelById(presetId)),
          checklist,
          context: context ? {
            label: String(context.label || "").trim(),
            central_id: String(context.central_id || "").trim(),
            code: String(context.code || "").trim(),
          } : {
            label: "",
            central_id: "",
            code: "",
          },
          snapshot,
          handoff_text: missionTrimText(String(handoff && handoff.text || ""), 260),
          handoff_timeline: timeline,
        };
        pack.handoff_template = buildMissionHandoffTemplate(pack);
        const routingSelection = loadMissionRoutingSelection();
        const resolvedRouting = resolveMissionRoutingProfile(pack, routingSelection);
        const defaultTemplateKind = normalizeMissionRoutingTemplateKind(
          resolvedRouting.profile && resolvedRouting.profile.default_template || "short",
          "short"
        );
        const templateKind = normalizeMissionRoutingTemplateKind(routingSelection.template_kind, defaultTemplateKind);
        pack.routing_signal = resolvedRouting.signal;
        pack.routing = {
          mode: String(resolvedRouting.mode || "auto"),
          profile_id: String(resolvedRouting.profile && resolvedRouting.profile.id || "standard-ops"),
          profile_label: String(resolvedRouting.profile && resolvedRouting.profile.label || "Standard Ops"),
          channel: String(resolvedRouting.profile && resolvedRouting.profile.channel || "ops-general"),
          priority: String(resolvedRouting.profile && resolvedRouting.profile.priority || "p2"),
          reasons: Array.isArray(resolvedRouting.reasons) ? resolvedRouting.reasons : [],
        };
        pack.channel_templates = buildMissionChannelTemplates(pack);
        pack.channel_template_kind = templateKind;
        pack.channel_template = String(pack.channel_templates && pack.channel_templates[templateKind] || "");
        if (!pack.channel_template) pack.channel_template = String(pack.handoff_template || "");
        pack.routing_dispatch = buildMissionRoutingDispatchNote(pack);
        const deliverySelection = loadMissionDeliverySelection();
        const deliveryAdapterId = normalizeMissionDeliveryAdapterId(deliverySelection.adapter_id, "telegram");
        const deliveryVariantKind = normalizeMissionDeliveryVariantKind(deliverySelection.variant_kind, pack.channel_template_kind || "short");
        pack.delivery_templates = buildMissionDeliveryTemplates(pack);
        pack.delivery = {
          adapter_id: deliveryAdapterId,
          variant_kind: deliveryVariantKind,
        };
        pack.delivery_payload = buildMissionDeliveryPayload(pack, deliveryAdapterId, deliveryVariantKind);
        return pack;
      }
      function renderMissionResponsePackSummary() {
        const node = byId("sideResponsePackSummary");
        if (!node) return;
        renderMissionResponseRoutingControls();
        renderMissionDeliveryControls();
        renderMissionDeliveryPolicyControls(loadMissionResponsePack());
        const pack = loadMissionResponsePack();
        if (!pack) {
          node.textContent = "Response pack: —";
          renderMissionResponseRoutingSummary();
          renderMissionDeliverySummary();
          renderMissionDeliveryHandoffStatus();
          renderMissionDeliverySlaStatus();
          renderMissionDeliveryAutomationSummary();
          return;
        }
        const stamp = formatSessionTime(String(pack.generated_at || ""));
        const checklist = pack.checklist && typeof pack.checklist === "object" ? pack.checklist : {};
        const timelineCount = Array.isArray(pack.handoff_timeline) ? pack.handoff_timeline.length : 0;
        const context = pack.context && typeof pack.context === "object" ? pack.context : {};
        const routing = pack.routing && typeof pack.routing === "object" ? pack.routing : {};
        const signal = pack.routing_signal && typeof pack.routing_signal === "object" ? pack.routing_signal : {};
        const templateKind = normalizeMissionRoutingTemplateKind(pack.channel_template_kind || "short", "short");
        const contextLabel = missionTrimText(String(context.label || ""), 72);
        const parts = [
          `Pack ${stamp} · ${String(pack.preset_label || pack.preset_id || "preset")}`,
          `checklist ${Number(checklist.done || 0)}/${Number(checklist.total || 0)} · timeline ${timelineCount}`,
        ];
        if (contextLabel) parts.push(`ctx: ${contextLabel}`);
        parts.push(`routing ${String(routing.profile_label || routing.profile_id || "standard-ops")} → ${String(routing.channel || "ops-general")} (${String(routing.priority || "p2").toUpperCase()})`);
        parts.push(`template=${templateKind} · sev=${String(signal.severity || "all")} status=${String(signal.status || "all")}`);
        node.textContent = parts.join("\n");
        renderMissionResponseRoutingSummary();
        renderMissionDeliverySummary();
        renderMissionDeliveryHandoffStatus();
        renderMissionDeliverySlaStatus();
        renderMissionDeliveryAutomationSummary();
      }
      function runMissionResponsePackAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        const statusNode = byId("sideMissionStatus");
        const confirmMissionDangerAction = (title, details = "") => {
          const head = String(title || "Підтвердіть дію").trim();
          const tail = missionTrimText(String(details || "").trim(), 220);
          return window.confirm(tail ? `${head}\n\n${tail}` : head);
        };
        const ensurePack = (options = {}) => {
          const source = options && typeof options === "object" ? options : {};
          let pack = loadMissionResponsePack();
          if (!pack || source.rebuild) {
            pack = buildMissionResponsePack({
              capture: !!source.capture,
              preset_id: String(pack && pack.preset_id || resolveMissionPresetId()),
              snapshot: pack && pack.snapshot && typeof pack.snapshot === "object" ? pack.snapshot : null,
            });
            storeMissionResponsePack(pack);
          }
          return pack;
        };
        const appendDeliveryJournalFromPack = (pack, payload, actionKind, options = {}) => {
          const sourcePack = pack && typeof pack === "object" ? pack : {};
          const sourcePayload = payload && typeof payload === "object" ? payload : {};
          const sourceOptions = options && typeof options === "object" ? options : {};
          const context = sourcePack.context && typeof sourcePack.context === "object" ? sourcePack.context : {};
          const routing = sourcePack.routing && typeof sourcePack.routing === "object" ? sourcePack.routing : {};
          const noteSuffix = missionTrimText(String(sourceOptions.note_suffix || ""), 96);
          const contextLabel = missionTrimText(
            String(sourceOptions.context_override || context.label || ""),
            96,
          );
          const baseNote = `target=${String(sourcePayload.target || "—")} transport=${String(sourcePayload.transport || "—")}`;
          appendMissionDeliveryJournalEvent({
            ts: new Date().toISOString(),
            action: actionKind,
            adapter_id: String(sourcePayload.adapter_id || sourcePack.delivery && sourcePack.delivery.adapter_id || "telegram"),
            variant_kind: String(sourcePayload.variant_kind || sourcePack.delivery && sourcePack.delivery.variant_kind || "short"),
            context: contextLabel,
            route_channel: String(routing.channel || "ops-general"),
            note: noteSuffix ? `${baseNote}; ${noteSuffix}` : baseNote,
          });
        };
        const applyBulkDeliveryAction = (actionKind, candidates, options = {}) => {
          const cleanAction = String(actionKind || "").trim().toLowerCase();
          const sourceCandidates = Array.isArray(candidates) ? candidates : [];
          const sourceOptions = options && typeof options === "object" ? options : {};
          const limit = Math.max(1, Number(sourceOptions.limit || MISSION_DELIVERY_BULK_LIMIT));
          const pack = ensurePack({ rebuild: false });
          const payload = pack.delivery_payload && typeof pack.delivery_payload === "object" ? pack.delivery_payload : {};
          const applied = [];
          for (const candidate of sourceCandidates.slice(0, limit)) {
            const contextLabel = missionTrimText(String(candidate && candidate.context_label || ""), 96);
            if (!contextLabel) continue;
            appendDeliveryJournalFromPack(
              pack,
              payload,
              cleanAction,
              {
                note_suffix: missionTrimText(String(sourceOptions.note_suffix || ""), 96),
                context_override: contextLabel,
              },
            );
            applied.push(contextLabel);
          }
          if (applied.length > 0) {
            appendMissionHandoffTimelineEvent(`delivery_${cleanAction}_bulk`, {
              ts: new Date().toISOString(),
              context: String(pack.context && pack.context.label || ""),
              text: `${cleanAction} bulk: ${applied.join(", ")}`,
            });
          }
          return applied;
        };
        if (mode === "apply-routing" || mode === "auto-route") {
          const selection = syncMissionRoutingSelectionFromControls({ forceAuto: mode === "auto-route" });
          const pack = ensurePack({ rebuild: true });
          renderMissionResponsePackSummary();
          const profileLabel = String(pack.routing && pack.routing.profile_label || selection.profile_id || "auto");
          if (statusNode) statusNode.textContent = `Routing: ${profileLabel} · template ${String(pack.channel_template_kind || "short")}`;
          return true;
        }
        if (mode === "apply-delivery") {
          const selection = syncMissionDeliverySelectionFromControls();
          const pack = ensurePack({ rebuild: true });
          renderMissionResponsePackSummary();
          const payload = pack.delivery_payload && typeof pack.delivery_payload === "object" ? pack.delivery_payload : {};
          appendDeliveryJournalFromPack(pack, payload, "apply");
          const adapterLabel = String(payload.adapter_label || selection.adapter_id || "telegram");
          const variantKind = String(payload.variant_kind || selection.variant_kind || "short");
          if (statusNode) statusNode.textContent = `Delivery: ${adapterLabel} · ${variantKind}`;
          return true;
        }
        if (mode === "generate") {
          const pack = ensurePack({ rebuild: true, capture: true });
          appendMissionHandoffTimelineEvent("response_pack", {
            ts: String(pack.generated_at || new Date().toISOString()),
            context: String(pack.context && pack.context.label || ""),
            text: `preset=${pack.preset_id} checklist=${Number(pack.checklist && pack.checklist.done || 0)}/${Number(pack.checklist && pack.checklist.total || 0)}`,
          });
          renderMissionSnapshotSummary();
          renderMissionHandoffTimeline();
          renderMissionResponsePackSummary();
          if (statusNode) statusNode.textContent = `Response pack: ${formatSessionTime(pack.generated_at)} зібрано`;
          return true;
        }
        if (mode === "copy-template") {
          const pack = ensurePack({ rebuild: false });
          const template = String(pack.channel_template || pack.handoff_template || "").trim();
          if (!template) return false;
          copyTextWithFallback(template, "Скопіюйте handoff template:", "Response pack: шаблон скопійовано", "Response pack: шаблон у prompt");
          renderMissionResponsePackSummary();
          return true;
        }
        if (mode === "copy-route") {
          const pack = ensurePack({ rebuild: false });
          const routingText = String(pack.routing_dispatch || buildMissionRoutingDispatchNote(pack) || "").trim();
          if (!routingText) return false;
          copyTextWithFallback(routingText, "Скопіюйте escalation route:", "Routing: маршрут скопійовано", "Routing: маршрут у prompt");
          renderMissionResponsePackSummary();
          return true;
        }
        if (mode === "copy-delivery" || mode === "copy-telegram" || mode === "copy-email" || mode === "copy-ticket") {
          let overrideAdapter = "";
          if (mode === "copy-telegram") overrideAdapter = "telegram";
          else if (mode === "copy-email") overrideAdapter = "email";
          else if (mode === "copy-ticket") overrideAdapter = "ticket";
          const selection = syncMissionDeliverySelectionFromControls({ adapter_id: overrideAdapter || undefined });
          const pack = ensurePack({ rebuild: true });
          const payload = buildMissionDeliveryPayload(pack, selection.adapter_id, selection.variant_kind);
          const deliveryText = String(payload.preview || payload.message || "").trim();
          if (!deliveryText) return false;
          copyTextWithFallback(
            deliveryText,
            "Скопіюйте delivery payload:",
            `Delivery: ${String(payload.adapter_label || selection.adapter_id)} скопійовано`,
            "Delivery: payload у prompt"
          );
          appendMissionHandoffTimelineEvent("delivery", {
            ts: new Date().toISOString(),
            context: String(pack.context && pack.context.label || ""),
            text: `adapter=${String(payload.adapter_id || selection.adapter_id)} variant=${String(payload.variant_kind || selection.variant_kind)}`,
          });
          appendDeliveryJournalFromPack(pack, payload, "copy");
          renderMissionHandoffTimeline();
          renderMissionResponsePackSummary();
          return true;
        }
        if (mode === "show-delivery-journal") {
          const pack = ensurePack({ rebuild: false });
          const journal = listMissionDeliveryJournal();
          if (journal.length <= 0) {
            if (statusNode) statusNode.textContent = "Delivery journal: порожній";
            renderMissionResponsePackSummary();
            return false;
          }
          window.prompt(
            "Mission delivery journal (JSON):",
            JSON.stringify(
              {
                kind: "passengers.mission.delivery_journal.v1",
                status: buildMissionDeliveryHandoffStatus(pack),
                items: journal.slice(0, 24),
              },
              null,
              2,
            ),
          );
          if (statusNode) statusNode.textContent = `Delivery journal: показано ${Math.min(24, journal.length)}`;
          renderMissionResponsePackSummary();
          return true;
        }
        if (mode === "clear-delivery-journal") {
          clearMissionDeliveryJournal();
          renderMissionResponsePackSummary();
          if (statusNode) statusNode.textContent = "Delivery journal: очищено";
          return true;
        }
        if (mode === "apply-delivery-policy") {
          const selection = syncMissionDeliveryPolicySelectionFromControls();
          const pack = ensurePack({ rebuild: false });
          renderMissionDeliveryPolicyControls(pack);
          renderMissionResponsePackSummary();
          const resolved = resolveMissionDeliveryPolicyProfile(pack);
          if (statusNode) {
            statusNode.textContent = `Delivery policy: ${String(resolved.profile && resolved.profile.label || selection.profile_id || "auto")} (${String(resolved.mode || "auto")})`;
          }
          return true;
        }
        if (mode === "apply-delivery-suggestion") {
          const pack = ensurePack({ rebuild: false });
          const plan = buildMissionDeliveryAutomationPlan(pack);
          const suggestion = plan.suggestion && typeof plan.suggestion === "object" ? plan.suggestion : {};
          const suggestionAction = String(suggestion.action || "none").trim().toLowerCase();
          if (!suggestionAction || suggestionAction === "none" || suggestionAction === "apply-delivery-suggestion") {
            if (statusNode) statusNode.textContent = "Delivery policy: немає рекомендованої дії";
            renderMissionResponsePackSummary();
            return false;
          }
          if (suggestionAction === "retry-delivery" || suggestionAction === "escalate-delivery") {
            const approved = confirmMissionDangerAction(
              "Застосувати ризикову рекомендацію?",
              `action=${suggestionAction}; why=${String(suggestion.reason || "")}`,
            );
            if (!approved) return false;
          }
          const applied = runMissionResponsePackAction(suggestionAction);
          if (statusNode) {
            statusNode.textContent = applied
              ? `Delivery policy: виконано ${suggestionAction}`
              : `Delivery policy: ${suggestionAction} не виконано`;
          }
          renderMissionResponsePackSummary();
          return !!applied;
        }
        if (mode === "bulk-ack-pending") {
          const plan = buildMissionDeliveryAutomationPlan();
          const profile = plan.policy && plan.policy.profile && typeof plan.policy.profile === "object" ? plan.policy.profile : {};
          const limit = Math.max(1, Number(profile.bulk_limit || MISSION_DELIVERY_BULK_LIMIT));
          const candidates = collectMissionDeliveryBulkCandidates("ack", { policy: plan.policy, limit });
          const applied = applyBulkDeliveryAction("ack", candidates, { note_suffix: "bulk=policy-ack", limit });
          renderMissionResponsePackSummary();
          renderMissionHandoffTimeline();
          if (statusNode) {
            statusNode.textContent = applied.length > 0
              ? `Delivery bulk ack: ${applied.length}`
              : "Delivery bulk ack: немає кандидатів";
          }
          return applied.length > 0;
        }
        if (mode === "bulk-retry-stale") {
          const plan = buildMissionDeliveryAutomationPlan();
          const profile = plan.policy && plan.policy.profile && typeof plan.policy.profile === "object" ? plan.policy.profile : {};
          const limit = Math.max(1, Number(profile.bulk_limit || MISSION_DELIVERY_BULK_LIMIT));
          const candidates = collectMissionDeliveryBulkCandidates("retry", { policy: plan.policy, limit });
          if (candidates.length > 0) {
            const approved = confirmMissionDangerAction(
              "Підтвердьте bulk retry",
              `Буде виконано retry до ${Math.min(limit, candidates.length)} контекстів.`,
            );
            if (!approved) return false;
          }
          const applied = applyBulkDeliveryAction("retry", candidates, { note_suffix: "bulk=policy-retry-stale", limit });
          renderMissionResponsePackSummary();
          renderMissionHandoffTimeline();
          if (statusNode) {
            statusNode.textContent = applied.length > 0
              ? `Delivery bulk retry: ${applied.length}`
              : "Delivery bulk retry: немає кандидатів";
          }
          return applied.length > 0;
        }
        if (mode === "bulk-escalate-stale") {
          const plan = buildMissionDeliveryAutomationPlan();
          const profile = plan.policy && plan.policy.profile && typeof plan.policy.profile === "object" ? plan.policy.profile : {};
          const limit = Math.max(1, Number(profile.bulk_limit || MISSION_DELIVERY_BULK_LIMIT));
          const candidates = collectMissionDeliveryBulkCandidates("escalate", { policy: plan.policy, limit });
          if (candidates.length > 0) {
            const approved = confirmMissionDangerAction(
              "Підтвердьте bulk escalate",
              `Буде виконано escalate до ${Math.min(limit, candidates.length)} контекстів.`,
            );
            if (!approved) return false;
          }
          const applied = applyBulkDeliveryAction("escalate", candidates, { note_suffix: "bulk=policy-escalate-stale", limit });
          renderMissionResponsePackSummary();
          renderMissionHandoffTimeline();
          if (statusNode) {
            statusNode.textContent = applied.length > 0
              ? `Delivery bulk escalate: ${applied.length}`
              : "Delivery bulk escalate: немає кандидатів";
          }
          return applied.length > 0;
        }
        if (mode === "ack-delivery") {
          const pack = ensurePack({ rebuild: false });
          const payload = pack.delivery_payload && typeof pack.delivery_payload === "object" ? pack.delivery_payload : {};
          appendDeliveryJournalFromPack(pack, payload, "ack");
          appendMissionHandoffTimelineEvent("delivery_ack", {
            ts: new Date().toISOString(),
            context: String(pack.context && pack.context.label || ""),
            text: `adapter=${String(payload.adapter_id || "telegram")} variant=${String(payload.variant_kind || "short")}`,
          });
          renderMissionHandoffTimeline();
          renderMissionResponsePackSummary();
          if (statusNode) statusNode.textContent = "Delivery: ack зафіксовано";
          return true;
        }
        if (mode === "retry-delivery") {
          const pack = ensurePack({ rebuild: true });
          const payload = pack.delivery_payload && typeof pack.delivery_payload === "object" ? pack.delivery_payload : {};
          const retryApproved = confirmMissionDangerAction(
            "Підтвердьте retry delivery",
            "Використовуйте retry, коли ACK відсутній або SLA переходить у warn/stale.",
          );
          if (!retryApproved) return false;
          const reasonRaw = window.prompt("Retry reason (optional):", "");
          if (reasonRaw === null) return false;
          const reason = missionTrimText(String(reasonRaw || "").trim(), 92);
          const deliveryText = String(payload.preview || payload.message || "").trim();
          if (!deliveryText) return false;
          copyTextWithFallback(
            deliveryText,
            "Скопіюйте retry payload:",
            `Delivery retry: ${String(payload.adapter_label || payload.adapter_id || "adapter")} скопійовано`,
            "Delivery retry: payload у prompt"
          );
          appendDeliveryJournalFromPack(pack, payload, "retry", { note_suffix: reason ? `reason=${reason}` : "" });
          appendMissionHandoffTimelineEvent("delivery_retry", {
            ts: new Date().toISOString(),
            context: String(pack.context && pack.context.label || ""),
            text: reason ? `retry reason=${reason}` : "retry without reason",
          });
          renderMissionHandoffTimeline();
          renderMissionResponsePackSummary();
          if (statusNode) statusNode.textContent = reason ? `Delivery retry: ${reason}` : "Delivery retry: зафіксовано";
          return true;
        }
        if (mode === "escalate-delivery") {
          const pack = ensurePack({ rebuild: false });
          const payload = pack.delivery_payload && typeof pack.delivery_payload === "object" ? pack.delivery_payload : {};
          const escalateApproved = confirmMissionDangerAction(
            "Підтвердьте escalation",
            "Escalate застосовуйте для критичних/прострочених випадків (SLA stale, ACK відсутній).",
          );
          if (!escalateApproved) return false;
          const reasonRaw = window.prompt("Escalation reason:", "");
          if (reasonRaw === null) return false;
          const reason = missionTrimText(String(reasonRaw || "").trim(), 120);
          if (!reason) return false;
          appendDeliveryJournalFromPack(pack, payload, "escalate", { note_suffix: `reason=${reason}` });
          appendMissionHandoffTimelineEvent("delivery_escalate", {
            ts: new Date().toISOString(),
            context: String(pack.context && pack.context.label || ""),
            text: reason,
          });
          renderMissionHandoffTimeline();
          renderMissionResponsePackSummary();
          if (statusNode) statusNode.textContent = `Delivery escalation: ${reason}`;
          return true;
        }
        if (mode === "export-json") {
          const pack = ensurePack({ rebuild: false });
          window.prompt("Mission response pack (JSON):", JSON.stringify(pack, null, 2));
          renderMissionResponsePackSummary();
          if (statusNode) statusNode.textContent = "Response pack: JSON відкрито";
          return true;
        }
        if (mode === "clear") {
          clearMissionResponsePack();
          renderMissionResponsePackSummary();
          if (statusNode) statusNode.textContent = "Response pack: очищено";
          return true;
        }
        return false;
      }
      function listMissionHandoffTimeline() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_HANDOFF_TIMELINE_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw
            .map((item) => {
              const source = item && typeof item === "object" ? item : {};
              return {
                id: String(source.id || "").trim(),
                ts: String(source.ts || "").trim(),
                kind: String(source.kind || "").trim().toLowerCase(),
                context: String(source.context || "").trim(),
                text: String(source.text || "").trim(),
              };
            })
            .filter((item) => !!item.ts && !!item.kind)
            .slice(0, MISSION_EVIDENCE_LIMIT);
        } catch (_error) {
          return [];
        }
      }
      function storeMissionHandoffTimeline(items) {
        const source = Array.isArray(items) ? items : [];
        const normalized = source
          .map((item) => {
            const current = item && typeof item === "object" ? item : {};
            return {
              id: String(current.id || "").trim(),
              ts: String(current.ts || "").trim(),
              kind: String(current.kind || "").trim().toLowerCase(),
              context: String(current.context || "").trim(),
              text: String(current.text || "").trim(),
            };
          })
          .filter((item) => !!item.ts && !!item.kind)
          .slice(0, MISSION_EVIDENCE_LIMIT);
        try { localStorage.setItem(MISSION_HANDOFF_TIMELINE_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function appendMissionHandoffTimelineEvent(kind, payload = {}) {
        const cleanKind = String(kind || "").trim().toLowerCase();
        if (!cleanKind) return [];
        const source = payload && typeof payload === "object" ? payload : {};
        const current = listMissionHandoffTimeline();
        current.unshift({
          id: `${Date.now()}-${Math.floor(Math.random() * 100000)}`,
          ts: String(source.ts || new Date().toISOString()),
          kind: cleanKind,
          context: missionTrimText(String(source.context || ""), 96),
          text: missionTrimText(String(source.text || ""), 180),
        });
        return storeMissionHandoffTimeline(current);
      }
      function clearMissionHandoffTimeline() {
        return storeMissionHandoffTimeline([]);
      }
      function renderMissionHandoffTimeline() {
        const node = byId("sideHandoffTimeline");
        if (!node) return;
        const items = listMissionHandoffTimeline().slice(0, 4);
        if (items.length === 0) {
          node.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        node.innerHTML = items
          .map((item) => {
            const stamp = formatSessionTime(item.ts);
            const kind = String(item.kind || "event").trim();
            const context = String(item.context || "").trim();
            const text = missionTrimText(item.text, 120);
            const metaRight = context ? `${kind} · ${context}` : kind;
            return (
              `<div class="sideHandoffTimelineRow">`
              + `<div class="sideHandoffTimelineMeta"><span>${esc(stamp)}</span><span>${esc(metaRight)}</span></div>`
              + `<div class="sideHandoffTimelineBody">${esc(text || "—")}</div>`
              + `</div>`
            );
          })
          .join("");
      }
      function runMissionHandoffHistoryAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        const statusNode = byId("sideMissionStatus");
        if (mode === "show") {
          const items = listMissionHandoffTimeline();
          if (items.length === 0) {
            if (statusNode) statusNode.textContent = "Handoff history: журнал порожній";
            return false;
          }
          window.prompt("Mission handoff timeline (JSON):", JSON.stringify({ kind: "passengers.mission.handoff_timeline.v1", items: items.slice(0, 20) }, null, 2));
          if (statusNode) statusNode.textContent = `Handoff history: показано ${Math.min(20, items.length)}`;
          return true;
        }
        if (mode === "clear") {
          clearMissionHandoffTimeline();
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Handoff history: очищено";
          return true;
        }
        return false;
      }
      function runMissionHandoffAdoptionAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        const statusNode = byId("sideMissionStatus");
        if (mode === "show") {
          const snapshot = buildSidebarNavAdoptionSnapshot();
          window.prompt("Mission nav adoption snapshot (JSON):", JSON.stringify(snapshot, null, 2));
          recordSidebarNavAdoptionEvent("nav_adoption_show");
          appendMissionHandoffTimelineEvent("adoption_show", {
            text: `score=${Number(snapshot.coaching && snapshot.coaching.score || 0)}% pass=${Number(snapshot.scorecard && snapshot.scorecard.passed || 0)}/${Number(snapshot.scorecard && snapshot.scorecard.total || 0)} actions=${Number(snapshot.summary && snapshot.summary.total_actions || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Adoption snapshot: показано";
          return true;
        }
        if (mode === "export") {
          const snapshot = buildSidebarNavAdoptionSnapshot();
          const payload = JSON.stringify(snapshot, null, 2);
          copyTextWithFallback(
            payload,
            "Скопіюйте adoption snapshot:",
            "Adoption snapshot: скопійовано",
            "Adoption snapshot: у prompt"
          );
          recordSidebarNavAdoptionEvent("nav_adoption_export");
          appendMissionHandoffTimelineEvent("adoption_export", {
            text: `score=${Number(snapshot.coaching && snapshot.coaching.score || 0)}% pass=${Number(snapshot.scorecard && snapshot.scorecard.passed || 0)}/${Number(snapshot.scorecard && snapshot.scorecard.total || 0)} actions=${Number(snapshot.summary && snapshot.summary.total_actions || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Adoption snapshot: експортовано";
          return true;
        }
        if (mode === "reset") {
          const summary = buildSidebarNavAdoptionSummary();
          if (summary.total_actions <= 0) {
            if (statusNode) statusNode.textContent = "Adoption snapshot: вже порожній";
            return false;
          }
          const approved = typeof confirmMissionDangerAction === "function"
            ? confirmMissionDangerAction(
              "Підтвердьте reset adoption snapshot",
              "Будуть очищені локальні telemetry метрики nav-flow для цієї панелі."
            )
            : window.confirm("Очистити локальний adoption snapshot?");
          if (!approved) return false;
          clearSidebarNavAdoption();
          appendMissionHandoffTimelineEvent("adoption_reset", {
            text: `snapshot reset (було actions=${Number(summary.total_actions || 0)})`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Adoption snapshot: очищено";
          return true;
        }
        return false;
      }
      function runMissionHandoffTrendAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        const statusNode = byId("sideMissionStatus");
        const history = loadMissionAdoptionHistory();
        const trendWindow = loadMissionAdoptionTrendWindow();
        const trend = buildMissionAdoptionTrend(history, { window_size: trendWindow });
        const compareSummary = buildMissionAdoptionCompareSummary(trend, history);
        const trendCoach = buildMissionAdoptionTrendCoach(trend, history);
        const lifecycle = buildMissionAdoptionHistoryLifecycle(history);
        const payload = {
          kind: "passengers.mission.adoption_trend_history.v1",
          generated_at: new Date().toISOString(),
          trend_window: trendWindow,
          compare_summary: compareSummary,
          trend_coach: trendCoach,
          lifecycle,
          trend,
          history: history.slice(0, 20),
        };
        if (mode === "show") {
          window.prompt("Mission adoption trend history (JSON):", JSON.stringify(payload, null, 2));
          recordSidebarNavAdoptionEvent("nav_trend_history_show");
          appendMissionHandoffTimelineEvent("adoption_trend_show", {
            text: `status=${String(lifecycle.status_label || "EMPTY")} samples=${history.length} window=${trendWindow}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Trend history: показано ${history.length} (window=${trendWindow})`;
          return true;
        }
        if (mode === "export") {
          const text = JSON.stringify(payload, null, 2);
          copyTextWithFallback(
            text,
            "Скопіюйте adoption trend history:",
            "Trend history: скопійовано",
            "Trend history: у prompt"
          );
          recordSidebarNavAdoptionEvent("nav_trend_history_export");
          appendMissionHandoffTimelineEvent("adoption_trend_export", {
            text: `status=${String(lifecycle.status_label || "EMPTY")} samples=${history.length} window=${trendWindow}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Trend history: експортовано (${history.length}, window=${trendWindow})`;
          return true;
        }
        if (mode === "clear") {
          if (history.length <= 0 && lifecycle.status_id === "reset_recently") {
            if (statusNode) statusNode.textContent = "Trend history: вже очищено (recent reset)";
            return false;
          }
          if (history.length <= 0 && lifecycle.status_id === "empty") {
            if (statusNode) statusNode.textContent = "Trend history: порожньо";
            return false;
          }
          const approved = typeof confirmMissionDangerAction === "function"
            ? confirmMissionDangerAction(
              "Підтвердьте clear trend history",
              `Буде очищено ${history.length} history записів coaching trendline для цієї панелі.`
            )
            : window.confirm("Очистити coaching trend history?");
          if (!approved) return false;
          const resetMeta = clearMissionAdoptionHistory({ reason: "manual trend clear" });
          recordSidebarNavAdoptionEvent("nav_trend_history_clear");
          appendMissionHandoffTimelineEvent("adoption_trend_clear", {
            ts: String(resetMeta.last_reset_ts || new Date().toISOString()),
            text: `history cleared (було samples=${history.length})`,
          });
          renderMissionHandoffTimeline();
          renderMissionHandoffAdoptionSummary();
          if (statusNode) statusNode.textContent = "Trend history: очищено";
          return true;
        }
        return false;
      }
      function runMissionHandoffTrendWindowAction(windowValue) {
        const resolvedWindow = storeMissionAdoptionTrendWindow(windowValue);
        recordSidebarNavAdoptionEvent("nav_trend_window_set");
        appendMissionHandoffTimelineEvent("adoption_trend_window", {
          text: `trend window set to ${resolvedWindow}`,
        });
        renderMissionHandoffTimeline();
        renderMissionHandoffAdoptionSummary();
        const statusNode = byId("sideMissionStatus");
        if (statusNode) statusNode.textContent = `Trend window: last ${resolvedWindow} saves`;
        return true;
      }
      function renderMissionChecklistSummary(state, presetLabel) {
        const node = byId("sideMissionChecklist");
        if (!node) return;
        const checklist = buildMissionChecklistSummary(state);
        if (checklist.total <= 0) {
          node.innerHTML = '<span class="sideChecklistBadge">Checklist: —</span>';
          return;
        }
        const tone = checklist.is_complete ? "done" : (checklist.done > 0 ? "current" : "next");
        const safeLabel = missionTrimText(String(presetLabel || "preset"), 42);
        node.innerHTML = (
          `<div class="sideChecklistRow">`
          + `<span class="sideChecklistBadge ${tone}">${esc(`Checklist ${checklist.done}/${checklist.total}`)}</span>`
          + `<span class="sideChecklistBadge">${esc(`${checklist.percent}%`)}</span>`
          + `<span class="sideChecklistBadge">${esc(safeLabel)}</span>`
          + `</div>`
        );
      }
      function renderMissionPlaybooks() {
        const node = byId("sideMissionPlaybookList");
        if (!node) return;
        const presetId = resolveMissionPresetId();
        const state = buildMissionPlaybookState(presetId);
        const presetMeta = MISSION_TRIAGE_PRESETS.find((item) => String(item.id || "").trim().toLowerCase() === presetId);
        const checklist = buildMissionChecklistSummary(state);
        renderMissionChecklistSummary(state, String(presetMeta && presetMeta.label || presetId || ""));
        if (state.steps.length === 0) {
          node.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        node.innerHTML = state.steps
          .map((step, index) => {
            const cleanHref = String(step && step.href || "").trim();
            const label = String(step && step.label || `Крок ${index + 1}`).trim();
            const hint = String(step && step.hint || "").trim();
            let rowClass = "sidePlaybookRow";
            let meta = "pending";
            if (state.active_index > index) {
              rowClass += " done";
              meta = "done";
            } else if (state.active_index === index) {
              rowClass += " current";
              meta = "current";
            } else if (state.next_index === index) {
              rowClass += " next";
              meta = "next";
            }
            const disabled = cleanHref ? "" : "disabled";
            const title = String(presetMeta && presetMeta.label || presetId || "playbook");
            return (
              `<div class="${rowClass}">`
              + `<div class="sidePlaybookHead"><strong>${esc(`${index + 1}. ${label}`)}</strong><span class="sidePlaybookMeta">${esc(`${meta} · ${checklist.done}/${checklist.total}`)}</span></div>`
              + `<div class="sidePlaybookHint">${esc(hint || title)}</div>`
              + `<button class="sidePlaybookBtn" type="button" data-playbook-run="${esc(cleanHref)}" data-playbook-preset="${esc(presetId)}" data-playbook-step="${esc(index)}" data-playbook-label="${esc(label)}" ${disabled}>Відкрити крок</button>`
              + `</div>`
            );
          })
          .join("");
      }
      function runMissionPlaybookStep(payload = {}) {
        const source = payload && typeof payload === "object" ? payload : {};
        const href = String(source.href || "").trim();
        if (!href) return false;
        const presetId = String(source.preset_id || resolveMissionPresetId()).trim().toLowerCase();
        const stepIndexRaw = Number(source.step_index);
        const stepIndex = Number.isFinite(stepIndexRaw) ? Math.max(0, Math.floor(stepIndexRaw)) : 0;
        const label = String(source.label || "playbook-step").trim();
        if (presetId) {
          storeMissionLastPreset(presetId, { source: "playbook", next_index: stepIndex + 1 });
          recordSidebarIntentUsage(`triage-step:${presetId}:${stepIndex}`);
        }
        recordSidebarSessionShortcut({
          key: `playbook:${presetId}:${stepIndex}`,
          label: `Playbook ${label}`,
          href,
        });
        const statusNode = byId("sideMissionStatus");
        if (statusNode) statusNode.textContent = `Playbook: ${label}`;
        window.location.assign(href);
        return true;
      }
      function renderMissionChain() {
        const node = byId("sideMissionChain");
        if (!node) return;
        const presetId = resolveMissionPresetId();
        const presetMeta = MISSION_TRIAGE_PRESETS.find((item) => String(item.id || "").trim().toLowerCase() === presetId);
        const state = buildMissionPlaybookState(presetId);
        if (!presetId || state.steps.length === 0) {
          node.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        if (state.next_step) {
          const nextLabel = String(state.next_step.label || "next step").trim();
          const nextHref = String(state.next_step.href || "").trim();
          const nextDisabled = nextHref ? "" : "disabled";
          const statusNode = byId("sideMissionStatus");
          if (statusNode) statusNode.textContent = `Preset: ${String(presetMeta && presetMeta.label || presetId)} · Next: ${nextLabel}`;
          node.innerHTML = (
            `<div class="sideMissionChainTitle">Smart triage chaining</div>`
            + `<div class="sideMissionChainText">Наступний рекомендований крок: ${esc(nextLabel)}</div>`
            + `<button class="sideMissionChainBtn" type="button" data-chain-run="${esc(nextHref)}" data-chain-preset="${esc(presetId)}" data-chain-step="${esc(state.next_index)}" data-chain-label="${esc(nextLabel)}" ${nextDisabled}>Виконати next step</button>`
          );
          return;
        }
        const statusNode = byId("sideMissionStatus");
        if (statusNode) statusNode.textContent = `Preset: ${String(presetMeta && presetMeta.label || presetId)} · Ланцюг завершено`;
        node.innerHTML = (
          `<div class="sideMissionChainTitle">Smart triage chaining</div>`
          + `<div class="sideMissionChainText">Ланцюг для цього сценарію завершено. Зафіксуй handoff note.</div>`
        );
      }
      function runMissionChainAction(payload = {}) {
        const source = payload && typeof payload === "object" ? payload : {};
        return runMissionPlaybookStep({
          href: String(source.href || "").trim(),
          preset_id: String(source.preset_id || "").trim().toLowerCase(),
          step_index: Number(source.step_index),
          label: String(source.label || "next step"),
        });
      }
      function loadMissionHandoffNote() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_HANDOFF_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          const text = String(source.text || "");
          const ts = String(source.ts || "");
          const context = String(source.context || "");
          if (!text.trim()) return null;
          return { text, ts, context };
        } catch (_error) {
          return null;
        }
      }
      function saveMissionHandoffNote(text, options = {}) {
        const clean = String(text || "").slice(0, MISSION_HANDOFF_MAX_LENGTH);
        if (!clean.trim()) {
          clearMissionHandoffNote();
          return null;
        }
        const payload = {
          text: clean,
          ts: String(options.ts || new Date().toISOString()),
          context: String(options.context || "").trim(),
        };
        try { localStorage.setItem(MISSION_HANDOFF_STORAGE_KEY, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function clearMissionHandoffNote() {
        try { localStorage.removeItem(MISSION_HANDOFF_STORAGE_KEY); } catch (_error) {}
      }
      function buildMissionContextLabel() {
        const context = loadWorkspaceContext({ maxAgeSec: 14 * 24 * 3600 });
        if (!context) return "";
        const central = String(context.central_id || "").trim();
        const code = String(context.code || "").trim();
        const label = String(context.label || (central && code ? `${central}:${code}` : central || code || "")).trim();
        if (!label) return "";
        return label;
      }
      function loadMissionHandoffComposerDraft() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(MISSION_HANDOFF_COMPOSER_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          const textValue = String(source.text || "");
          if (!textValue.trim()) return null;
          return {
            text: textValue,
            ts: String(source.ts || ""),
            context: String(source.context || "").trim(),
            score_percent: Number(source.score_percent || 0),
            trend_label: String(source.trend_label || "").trim(),
            next_actions_count: Math.max(0, Number(source.next_actions_count || 0)),
          };
        } catch (_error) {
          return null;
        }
      }
      function storeMissionHandoffComposerDraft(payload = {}) {
        const source = payload && typeof payload === "object" ? payload : {};
        const textValue = missionTrimText(String(source.text || ""), MISSION_HANDOFF_MAX_LENGTH);
        if (!textValue.trim()) {
          try { sessionStorage.removeItem(MISSION_HANDOFF_COMPOSER_STORAGE_KEY); } catch (_error) {}
          return null;
        }
        const normalized = {
          text: textValue,
          ts: String(source.ts || new Date().toISOString()),
          context: String(source.context || "").trim(),
          score_percent: Number(source.score_percent || 0),
          trend_label: String(source.trend_label || "").trim(),
          next_actions_count: Math.max(0, Number(source.next_actions_count || 0)),
        };
        try { sessionStorage.setItem(MISSION_HANDOFF_COMPOSER_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function buildMissionHandoffComposerTemplate(snapshot = null, options = {}) {
        const sourceSnapshot = snapshot && typeof snapshot === "object" ? snapshot : buildSidebarNavAdoptionSnapshot();
        const sourceOptions = options && typeof options === "object" ? options : {};
        const generatedAt = String(sourceSnapshot.generated_at || new Date().toISOString());
        const contextLabel = String(sourceOptions.context || buildMissionContextLabel() || "context=n/a").trim();
        const scorecard = sourceSnapshot.scorecard && typeof sourceSnapshot.scorecard === "object" ? sourceSnapshot.scorecard : {};
        const trend = sourceSnapshot.trend && typeof sourceSnapshot.trend === "object" ? sourceSnapshot.trend : {};
        const trendCoach = sourceSnapshot.trend_coach && typeof sourceSnapshot.trend_coach === "object" ? sourceSnapshot.trend_coach : {};
        const compareSummary = missionTrimText(String(sourceSnapshot.compare_summary || ""), 180);
        const nextActions = Array.isArray(sourceSnapshot.next_actions)
          ? sourceSnapshot.next_actions.map((item) => missionTrimText(String(item || "").trim(), 96)).filter(Boolean).slice(0, 3)
          : [];
        const scorePercent = Number(scorecard.percent || 0);
        const scorePassed = Number(scorecard.passed || 0);
        const scoreTotal = Number(scorecard.total || 0);
        const trendLabel = String(trend.label || "NO-DATA").trim();
        const trendDelta = Number(trend.delta_percent || 0);
        const trendDeltaLabel = trendDelta > 0 ? `+${trendDelta}` : `${trendDelta}`;
        const lines = [
          `[HANDOFF ${generatedAt}] ${contextLabel}`,
          `Scorecard: ${scorePassed}/${scoreTotal} · ${scorePercent}% · ${String(scorecard.tone || "warn").toUpperCase()}`,
          `Trend: ${trendLabel} · Δ${trendDeltaLabel}pp · window=${Number(sourceSnapshot.trend_window || 0) || Number(trend.window_size || 0) || 0}`,
          `Compare: ${compareSummary || "n/a"}`,
          `Coach: ${missionTrimText(String(trendCoach.text || "n/a"), 180)}`,
          `Next actions:`,
          ...(nextActions.length > 0 ? nextActions.map((item, index) => `${index + 1}) ${item}`) : ["1) Зберегти handoff note після triage", "2) Перевірити alerts/incidents/audit перед передачею зміни"]),
        ];
        const textValue = missionTrimText(lines.join("\n"), MISSION_HANDOFF_MAX_LENGTH);
        return {
          text: textValue,
          ts: new Date().toISOString(),
          context: contextLabel,
          score_percent: scorePercent,
          trend_label: trendLabel,
          next_actions_count: nextActions.length,
          generated_at: generatedAt,
        };
      }
      function renderMissionHandoffComposerSummary(draft = null) {
        const node = byId("sideHandoffComposer");
        if (!node) return;
        const source = draft && typeof draft === "object" ? draft : loadMissionHandoffComposerDraft();
        if (!source) {
          node.textContent = "Composer: шаблон не зібрано";
          return;
        }
        const stamp = source.ts ? formatSessionTime(source.ts) : "—";
        const context = String(source.context || "").trim();
        const contextSuffix = context ? ` · ${context}` : "";
        node.textContent = `Composer: ${stamp} · chars=${String(source.text || "").length} · score=${Number(source.score_percent || 0)}% · trend=${String(source.trend_label || "NO-DATA")}${contextSuffix}`;
      }
      function runMissionHandoffComposerAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        if (!mode) return false;
        const input = byId("sideHandoffInput");
        const statusNode = byId("sideMissionStatus");
        const contextLabel = buildMissionContextLabel();
        const buildDraft = () => storeMissionHandoffComposerDraft(buildMissionHandoffComposerTemplate(buildSidebarNavAdoptionSnapshot(), { context: contextLabel }));
        if (mode === "compose") {
          const draft = buildDraft();
          renderMissionHandoffComposerSummary(draft);
          renderMissionHandoffQuality();
          appendMissionHandoffTimelineEvent("compose", {
            context: contextLabel,
            text: draft
              ? `score=${Number(draft.score_percent || 0)}% trend=${String(draft.trend_label || "NO-DATA")} next=${Number(draft.next_actions_count || 0)}`
              : "composer draft empty",
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = draft ? "Handoff composer: шаблон зібрано" : "Handoff composer: шаблон порожній";
          return !!draft;
        }
        if (mode === "copy") {
          const draft = loadMissionHandoffComposerDraft() || buildDraft();
          if (!draft) {
            if (statusNode) statusNode.textContent = "Handoff composer: немає шаблону";
            return false;
          }
          copyTextWithFallback(
            draft.text,
            "Скопіюйте handoff composer template:",
            "Handoff composer: шаблон скопійовано",
            "Handoff composer: шаблон у prompt"
          );
          appendMissionHandoffTimelineEvent("compose_copy", {
            context: contextLabel,
            text: `chars=${String(draft.text || "").length}`,
          });
          renderMissionHandoffTimeline();
          renderMissionHandoffComposerSummary(draft);
          renderMissionHandoffQuality();
          if (statusNode) statusNode.textContent = "Handoff composer: скопійовано";
          return true;
        }
        if (mode === "apply") {
          if (!(input instanceof HTMLTextAreaElement)) return false;
          const draft = loadMissionHandoffComposerDraft() || buildDraft();
          if (!draft) {
            if (statusNode) statusNode.textContent = "Handoff composer: немає шаблону";
            return false;
          }
          const currentText = String(input.value || "").trim();
          const nextText = missionTrimText(String(draft.text || ""), MISSION_HANDOFF_MAX_LENGTH);
          if (currentText && currentText !== nextText) {
            const approved = confirmMissionDangerAction(
              "Замінити handoff note шаблоном?",
              "Поточний текст буде замінено підготовленим composer-шаблоном."
            );
            if (!approved) return false;
          }
          input.value = nextText;
          input.dataset.dirty = "1";
          renderMissionHandoffNotes();
          renderMissionHandoffComposerSummary(draft);
          renderMissionHandoffQuality();
          appendMissionHandoffTimelineEvent("compose_apply", {
            context: contextLabel,
            text: `template applied chars=${nextText.length}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Handoff composer: застосовано в note";
          return true;
        }
        return false;
      }
      function normalizeMissionHandoffQualityProfileId(value, fallback = "strict") {
        const clean = String(value || "").trim().toLowerCase();
        if (!clean) return String(fallback || "strict");
        if (MISSION_HANDOFF_QUALITY_PROFILES.some((item) => String(item.id || "").trim().toLowerCase() === clean)) return clean;
        return String(fallback || "strict");
      }
      function missionHandoffQualityProfileById(profileId) {
        const clean = normalizeMissionHandoffQualityProfileId(profileId, "strict");
        return MISSION_HANDOFF_QUALITY_PROFILES.find((item) => String(item.id || "").trim().toLowerCase() === clean)
          || MISSION_HANDOFF_QUALITY_PROFILES[0]
          || null;
      }
      function loadMissionHandoffQualityProfileSelection() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(MISSION_HANDOFF_QUALITY_PROFILE_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          return { profile_id: normalizeMissionHandoffQualityProfileId(source.profile_id, "strict") };
        } catch (_error) {
          return { profile_id: "strict" };
        }
      }
      function storeMissionHandoffQualityProfileSelection(selection = {}) {
        const payload = { profile_id: normalizeMissionHandoffQualityProfileId(selection.profile_id, "strict") };
        try { sessionStorage.setItem(MISSION_HANDOFF_QUALITY_PROFILE_STORAGE_KEY, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function resolveMissionHandoffQualityProfile() {
        const selection = loadMissionHandoffQualityProfileSelection();
        const profile = missionHandoffQualityProfileById(selection.profile_id) || missionHandoffQualityProfileById("strict");
        return {
          mode: "override",
          profile_id: String(profile && profile.id || "strict"),
          profile_label: String(profile && profile.label || "Strict"),
          profile: profile || null,
          reason: "session quality policy",
        };
      }
      function renderMissionHandoffQualityProfileControls(profileId = null) {
        const activeProfileId = normalizeMissionHandoffQualityProfileId(profileId, loadMissionHandoffQualityProfileSelection().profile_id);
        const nodes = Array.from(document.querySelectorAll("button[data-handoff-quality-profile]"));
        for (const node of nodes) {
          if (!(node instanceof HTMLButtonElement)) continue;
          const nodeProfile = normalizeMissionHandoffQualityProfileId(node.getAttribute("data-handoff-quality-profile"), activeProfileId);
          const active = nodeProfile === activeProfileId;
          node.classList.toggle("active", active);
          node.setAttribute("aria-pressed", active ? "true" : "false");
        }
        const policyNode = byId("sideHandoffQualityPolicy");
        if (policyNode) {
          const profile = missionHandoffQualityProfileById(activeProfileId);
          policyNode.textContent = `Quality policy: ${String(profile && profile.label || "Strict")} (${activeProfileId})`;
        }
      }
      function runMissionHandoffQualityProfileAction(profileId) {
        const next = storeMissionHandoffQualityProfileSelection({ profile_id: profileId });
        const resolved = resolveMissionHandoffQualityProfile();
        renderMissionHandoffQualityProfileControls(resolved.profile_id);
        const quality = buildMissionHandoffQualityState({ profile: resolved });
        renderMissionHandoffQuality(quality);
        appendMissionHandoffTimelineEvent("quality_profile_set", {
          context: buildMissionContextLabel(),
          text: `policy=${resolved.profile_id} (${resolved.profile_label})`,
        });
        renderMissionHandoffTimeline();
        const statusNode = byId("sideMissionStatus");
        if (statusNode) statusNode.textContent = `Handoff quality policy: ${resolved.profile_label}`;
        return next;
      }
      function normalizeMissionHandoffRemediationMetrics(source = null) {
        const raw = source && typeof source === "object" ? source : {};
        const samplesRaw = Array.isArray(raw.time_to_ready_sec_samples) ? raw.time_to_ready_sec_samples : [];
        const samples = samplesRaw
          .map((item) => Number(item))
          .filter((item) => Number.isFinite(item) && item >= 0)
          .slice(-MISSION_HANDOFF_REMEDIATION_TTR_LIMIT);
        return {
          applied: Math.max(0, Number(raw.applied || 0)),
          skipped: Math.max(0, Number(raw.skipped || 0)),
          override_after_remediation: Math.max(0, Number(raw.override_after_remediation || 0)),
          ready_cycles: Math.max(0, Number(raw.ready_cycles || 0)),
          time_to_ready_sec_samples: samples,
          cycle_started_at: String(raw.cycle_started_at || ""),
          cycle_has_remediation: !!raw.cycle_has_remediation,
          last_action: String(raw.last_action || ""),
          last_action_ts: String(raw.last_action_ts || ""),
          last_status: String(raw.last_status || ""),
        };
      }
      function loadMissionHandoffRemediationMetrics() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_HANDOFF_REMEDIATION_METRICS_STORAGE_KEY) || "null");
          return normalizeMissionHandoffRemediationMetrics(raw);
        } catch (_error) {
          return normalizeMissionHandoffRemediationMetrics();
        }
      }
      function storeMissionHandoffRemediationMetrics(payload = null) {
        const normalized = normalizeMissionHandoffRemediationMetrics(payload);
        try { localStorage.setItem(MISSION_HANDOFF_REMEDIATION_METRICS_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function normalizeMissionHandoffRemediationTimelineItem(source = null) {
        const raw = source && typeof source === "object" ? source : {};
        const nowIso = new Date().toISOString();
        const action = missionTrimText(String(raw.action || "").trim().toLowerCase(), 48) || "unknown";
        return {
          id: missionTrimText(String(raw.id || `${Date.now()}-${Math.floor(Math.random() * 100000)}`), 48),
          ts: String(raw.ts || nowIso),
          context: missionTrimText(String(raw.context || ""), 96),
          action,
          applied: !!raw.applied,
          status_label: missionTrimText(String(raw.status_label || ""), 32) || "NOT-READY",
          profile_id: missionTrimText(String(raw.profile_id || ""), 32) || "strict",
          passed: Math.max(0, Number(raw.passed || 0)),
          total: Math.max(0, Number(raw.total || 0)),
          block_reason: missionTrimText(String(raw.block_reason || ""), 180),
          fix_label: missionTrimText(String(raw.fix_label || ""), 96),
          cycle_open_sec: Number.isFinite(Number(raw.cycle_open_sec)) ? Math.max(0, Number(raw.cycle_open_sec)) : null,
          ready_after: !!raw.ready_after,
          override_after_remediation: !!raw.override_after_remediation,
        };
      }
      function listMissionHandoffRemediationTimeline() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_HANDOFF_REMEDIATION_TIMELINE_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw.map((item) => normalizeMissionHandoffRemediationTimelineItem(item)).slice(0, MISSION_HANDOFF_REMEDIATION_TIMELINE_LIMIT);
        } catch (_error) {
          return [];
        }
      }
      function storeMissionHandoffRemediationTimeline(items = []) {
        const normalized = (Array.isArray(items) ? items : [])
          .map((item) => normalizeMissionHandoffRemediationTimelineItem(item))
          .slice(0, MISSION_HANDOFF_REMEDIATION_TIMELINE_LIMIT);
        try { localStorage.setItem(MISSION_HANDOFF_REMEDIATION_TIMELINE_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function appendMissionHandoffRemediationTimelineEvent(payload = {}) {
        const source = payload && typeof payload === "object" ? payload : {};
        const current = listMissionHandoffRemediationTimeline();
        current.unshift(normalizeMissionHandoffRemediationTimelineItem(source));
        return storeMissionHandoffRemediationTimeline(current);
      }
      function normalizeMissionHandoffRemediationGovernanceProfileId(value, fallback = "standard") {
        const clean = String(value || "").trim().toLowerCase();
        if (!clean) return String(fallback || "standard");
        if (MISSION_HANDOFF_REMEDIATION_GOVERNANCE_PROFILES.some((item) => String(item.id || "").trim().toLowerCase() === clean)) return clean;
        return String(fallback || "standard");
      }
      function missionHandoffRemediationGovernanceProfileById(profileId) {
        const clean = normalizeMissionHandoffRemediationGovernanceProfileId(profileId, "standard");
        return MISSION_HANDOFF_REMEDIATION_GOVERNANCE_PROFILES.find((item) => String(item.id || "").trim().toLowerCase() === clean)
          || MISSION_HANDOFF_REMEDIATION_GOVERNANCE_PROFILES[0]
          || null;
      }
      function loadMissionHandoffRemediationGovernanceSelection() {
        try {
          const raw = JSON.parse(sessionStorage.getItem(MISSION_HANDOFF_REMEDIATION_GOVERNANCE_STORAGE_KEY) || "null");
          const source = raw && typeof raw === "object" ? raw : {};
          return { profile_id: normalizeMissionHandoffRemediationGovernanceProfileId(source.profile_id, "standard") };
        } catch (_error) {
          return { profile_id: "standard" };
        }
      }
      function storeMissionHandoffRemediationGovernanceSelection(selection = {}) {
        const payload = { profile_id: normalizeMissionHandoffRemediationGovernanceProfileId(selection.profile_id, "standard") };
        try { sessionStorage.setItem(MISSION_HANDOFF_REMEDIATION_GOVERNANCE_STORAGE_KEY, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function resolveMissionHandoffRemediationGovernanceProfile() {
        const selection = loadMissionHandoffRemediationGovernanceSelection();
        const profile = missionHandoffRemediationGovernanceProfileById(selection.profile_id) || missionHandoffRemediationGovernanceProfileById("standard");
        return {
          profile_id: String(profile && profile.id || "standard"),
          profile_label: String(profile && profile.label || "Standard"),
          target_max_override_rate_pct: Math.max(0, Number(profile && profile.target_max_override_rate_pct || 25)),
          target_p95_ttr_sec: Math.max(1, Number(profile && profile.target_p95_ttr_sec || 300)),
        };
      }
      function renderMissionHandoffRemediationGovernanceControls(profileId = null) {
        const activeProfileId = normalizeMissionHandoffRemediationGovernanceProfileId(profileId, loadMissionHandoffRemediationGovernanceSelection().profile_id);
        const nodes = Array.from(document.querySelectorAll("button[data-handoff-remediation-governance]"));
        for (const node of nodes) {
          if (!(node instanceof HTMLButtonElement)) continue;
          const nodeProfileId = normalizeMissionHandoffRemediationGovernanceProfileId(node.getAttribute("data-handoff-remediation-governance"), activeProfileId);
          const active = nodeProfileId === activeProfileId;
          node.classList.toggle("active", active);
          node.setAttribute("aria-pressed", active ? "true" : "false");
        }
      }
      function buildMissionHandoffRemediationGovernanceState(metrics = null, timelineItems = null) {
        const sourceMetrics = normalizeMissionHandoffRemediationMetrics(metrics || loadMissionHandoffRemediationMetrics());
        const timeline = Array.isArray(timelineItems) ? timelineItems : listMissionHandoffRemediationTimeline();
        const profile = resolveMissionHandoffRemediationGovernanceProfile();
        const considered = timeline.slice(0, 24);
        const overrideCount = considered.filter((item) => item.override_after_remediation).length;
        const appliedCount = Math.max(1, considered.filter((item) => item.applied).length);
        const overrideRatePct = Math.round((overrideCount / appliedCount) * 100);
        const samples = Array.isArray(sourceMetrics.time_to_ready_sec_samples) ? sourceMetrics.time_to_ready_sec_samples : [];
        const p95 = missionP95Seconds(samples);
        const compliance = {
          override_ok: overrideRatePct <= profile.target_max_override_rate_pct,
          ttr_ok: p95 <= profile.target_p95_ttr_sec,
        };
        const isOk = compliance.override_ok && compliance.ttr_ok;
        const actions = [];
        if (!compliance.override_ok) actions.push(`Знизити override-rate: перевірити top fix-label у remediation timeline (target <= ${profile.target_max_override_rate_pct}%).`);
        if (!compliance.ttr_ok) actions.push(`Знизити p95 TTR: посилити early-remediation до save (target <= ${profile.target_p95_ttr_sec}s).`);
        if (actions.length === 0) actions.push("Governance OK: зберігайте поточний remediation cadence і контроль handoff quality.");
        return {
          profile,
          override_rate_pct: overrideRatePct,
          p95_ttr_sec: p95,
          compliance,
          status_label: isOk ? "OK" : "WARN",
          next_actions: actions,
          considered_count: considered.length,
        };
      }
      function renderMissionHandoffRemediationGovernance(state = null) {
        const source = state && typeof state === "object" ? state : buildMissionHandoffRemediationGovernanceState();
        renderMissionHandoffRemediationGovernanceControls(source.profile.profile_id);
        const node = byId("sideHandoffRemediationGovernance");
        if (node) {
          node.textContent = `Governance ${source.status_label} · profile=${source.profile.profile_label} · override=${source.override_rate_pct}%/${source.profile.target_max_override_rate_pct}% · p95=${source.p95_ttr_sec}s/${source.profile.target_p95_ttr_sec}s`;
        }
        const actionNode = byId("sideHandoffRemediationActions");
        if (actionNode) {
          actionNode.textContent = `Next: ${source.next_actions[0] || "—"}`;
        }
      }
      function runMissionHandoffRemediationGovernanceAction(profileId) {
        storeMissionHandoffRemediationGovernanceSelection({ profile_id: profileId });
        const governance = buildMissionHandoffRemediationGovernanceState();
        renderMissionHandoffRemediationGovernance(governance);
        renderMissionHandoffRemediationSummary();
        renderMissionHandoffRemediationTimelinePreview();
        appendMissionHandoffTimelineEvent("remediation_governance_profile", {
          context: buildMissionContextLabel(),
          text: `profile=${governance.profile.profile_id} status=${governance.status_label} override=${governance.override_rate_pct}% p95=${governance.p95_ttr_sec}s`,
        });
        renderMissionHandoffTimeline();
        const statusNode = byId("sideMissionStatus");
        if (statusNode) statusNode.textContent = `Remediation governance: ${governance.profile.profile_label} (${governance.status_label})`;
        return governance;
      }
      function normalizeMissionHandoffRemediationIncidentItem(source = null) {
        const raw = source && typeof source === "object" ? source : {};
        const nowIso = new Date().toISOString();
        return {
          id: missionTrimText(String(raw.id || `${Date.now()}-${Math.floor(Math.random() * 100000)}`), 48),
          ts: String(raw.ts || nowIso),
          state: missionTrimText(String(raw.state || "open").toLowerCase(), 24) || "open",
          context: missionTrimText(String(raw.context || ""), 96),
          profile_id: missionTrimText(String(raw.profile_id || "standard"), 32),
          profile_label: missionTrimText(String(raw.profile_label || "Standard"), 48),
          override_rate_pct: Math.max(0, Number(raw.override_rate_pct || 0)),
          target_override_rate_pct: Math.max(0, Number(raw.target_override_rate_pct || 0)),
          p95_ttr_sec: Math.max(0, Number(raw.p95_ttr_sec || 0)),
          target_p95_ttr_sec: Math.max(0, Number(raw.target_p95_ttr_sec || 0)),
          message: missionTrimText(String(raw.message || "governance warning"), 220),
          fingerprint: missionTrimText(String(raw.fingerprint || ""), 96),
          snooze_until: String(raw.snooze_until || ""),
          ack_ts: String(raw.ack_ts || ""),
        };
      }
      function listMissionHandoffRemediationIncidents() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_HANDOFF_REMEDIATION_INCIDENTS_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw.map((item) => normalizeMissionHandoffRemediationIncidentItem(item)).slice(0, MISSION_HANDOFF_REMEDIATION_INCIDENTS_LIMIT);
        } catch (_error) {
          return [];
        }
      }
      function storeMissionHandoffRemediationIncidents(items = []) {
        const normalized = (Array.isArray(items) ? items : [])
          .map((item) => normalizeMissionHandoffRemediationIncidentItem(item))
          .slice(0, MISSION_HANDOFF_REMEDIATION_INCIDENTS_LIMIT);
        try { localStorage.setItem(MISSION_HANDOFF_REMEDIATION_INCIDENTS_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function missionHandoffRemediationIncidentActive(item, nowIso = null) {
        const source = item && typeof item === "object" ? item : {};
        const state = String(source.state || "open").trim().toLowerCase();
        if (state === "acked") return false;
        if (state !== "snoozed") return true;
        const snoozeUntilMs = Date.parse(String(source.snooze_until || ""));
        if (!Number.isFinite(snoozeUntilMs)) return true;
        const nowMs = nowIso ? Date.parse(String(nowIso || "")) : Date.now();
        if (!Number.isFinite(nowMs)) return true;
        return nowMs >= snoozeUntilMs;
      }
      function ensureMissionHandoffRemediationGovernanceIncident(governanceState = null) {
        const governance = governanceState && typeof governanceState === "object" ? governanceState : buildMissionHandoffRemediationGovernanceState();
        const nowIso = new Date().toISOString();
        const incidents = listMissionHandoffRemediationIncidents();
        if (String(governance.status_label || "OK").toUpperCase() !== "WARN") {
          return { incident: null, created: false, incidents };
        }
        const fingerprint = `${governance.profile.profile_id}|${governance.override_rate_pct}|${governance.p95_ttr_sec}|${governance.considered_count}`;
        const existingActive = incidents.find((item) => String(item.fingerprint || "") === fingerprint && missionHandoffRemediationIncidentActive(item, nowIso));
        if (existingActive) return { incident: existingActive, created: false, incidents };
        const recent = incidents.find((item) => {
          if (String(item.fingerprint || "") !== fingerprint) return false;
          const ageSec = missionSecondsSinceIso(String(item.ts || ""), nowIso);
          return Number.isFinite(ageSec) && ageSec !== null && ageSec <= 10 * 60;
        });
        if (recent) return { incident: recent, created: false, incidents };
        const message = `Governance WARN: override=${governance.override_rate_pct}%/${governance.profile.target_max_override_rate_pct}% · p95=${governance.p95_ttr_sec}s/${governance.profile.target_p95_ttr_sec}s`;
        const incident = normalizeMissionHandoffRemediationIncidentItem({
          ts: nowIso,
          state: "open",
          context: buildMissionContextLabel(),
          profile_id: governance.profile.profile_id,
          profile_label: governance.profile.profile_label,
          override_rate_pct: governance.override_rate_pct,
          target_override_rate_pct: governance.profile.target_max_override_rate_pct,
          p95_ttr_sec: governance.p95_ttr_sec,
          target_p95_ttr_sec: governance.profile.target_p95_ttr_sec,
          message,
          fingerprint,
        });
        incidents.unshift(incident);
        const stored = storeMissionHandoffRemediationIncidents(incidents);
        return { incident, created: true, incidents: stored };
      }
      function buildMissionHandoffRemediationIncidentSlaSummary(items = null) {
        const list = Array.isArray(items) ? items : listMissionHandoffRemediationIncidents();
        const active = list.filter((item) => missionHandoffRemediationIncidentActive(item));
        const snoozed = list.filter((item) => String(item.state || "").toLowerCase() === "snoozed" && !missionHandoffRemediationIncidentActive(item));
        const acked = list.filter((item) => String(item.state || "").toLowerCase() === "acked");
        const ages = active
          .map((item) => missionSecondsSinceIso(String(item.ts || "")))
          .filter((value) => Number.isFinite(value) && value !== null)
          .map((value) => Number(value));
        const oldestAgeSec = ages.length > 0 ? Math.max(...ages) : null;
        const oldestAgeLabel = Number.isFinite(oldestAgeSec) ? formatAgeShort(Number(oldestAgeSec)) : "—";
        return {
          active_count: active.length,
          snoozed_count: snoozed.length,
          acked_count: acked.length,
          oldest_active_age_sec: oldestAgeSec,
          oldest_active_age_label: oldestAgeLabel,
        };
      }
      function renderMissionHandoffRemediationIncidentSla(summary = null) {
        const node = byId("sideHandoffRemediationIncidentSla");
        if (!node) return;
        const source = summary && typeof summary === "object"
          ? summary
          : buildMissionHandoffRemediationIncidentSlaSummary();
        node.textContent = `Incident SLA: active=${source.active_count} · snoozed=${source.snoozed_count} · acked=${source.acked_count} · oldest=${source.oldest_active_age_label}`;
      }
      function buildMissionHandoffRemediationIncidentDigest(items = null) {
        const list = Array.isArray(items) ? items : listMissionHandoffRemediationIncidents();
        const groups = new Map();
        for (const item of list) {
          const fingerprint = missionTrimText(String(item && item.fingerprint || "").trim(), 96)
            || missionTrimText(`${String(item && item.profile_id || "standard")}|${String(item && item.context || "")}`, 96);
          const state = String(item && item.state || "open").trim().toLowerCase();
          let group = groups.get(fingerprint);
          if (!group) {
            group = {
              fingerprint,
              total: 0,
              active_count: 0,
              snoozed_count: 0,
              acked_count: 0,
              last_state: state || "open",
              last_ts: String(item && item.ts || ""),
              profile_id: String(item && item.profile_id || "standard"),
              context: missionTrimText(String(item && item.context || ""), 96),
              oldest_age_sec: 0,
            };
            groups.set(fingerprint, group);
          }
          group.total += 1;
          if (missionHandoffRemediationIncidentActive(item)) {
            group.active_count += 1;
          } else if (state === "snoozed") {
            group.snoozed_count += 1;
          } else if (state === "acked") {
            group.acked_count += 1;
          }
          const ageSec = missionSecondsSinceIso(String(item && item.ts || ""));
          if (Number.isFinite(ageSec) && ageSec !== null) {
            group.oldest_age_sec = Math.max(group.oldest_age_sec, Number(ageSec));
          }
          const existingTs = Date.parse(String(group.last_ts || ""));
          const currentTs = Date.parse(String(item && item.ts || ""));
          if (!Number.isFinite(existingTs) || (Number.isFinite(currentTs) && currentTs > existingTs)) {
            group.last_ts = String(item && item.ts || "");
            group.last_state = state || "open";
            group.profile_id = String(item && item.profile_id || group.profile_id || "standard");
            group.context = missionTrimText(String(item && item.context || group.context || ""), 96);
          }
        }
        return Array.from(groups.values())
          .sort((left, right) => {
            if (right.active_count !== left.active_count) return right.active_count - left.active_count;
            if (right.oldest_age_sec !== left.oldest_age_sec) return right.oldest_age_sec - left.oldest_age_sec;
            return right.total - left.total;
          })
          .slice(0, 4)
          .map((item) => ({
            ...item,
            oldest_age_label: Number.isFinite(item.oldest_age_sec) ? formatAgeShort(Number(item.oldest_age_sec)) : "—",
          }));
      }
      function buildMissionHandoffRemediationIncidentTriageHints(digest = null, summary = null) {
        const sourceDigest = Array.isArray(digest) ? digest : buildMissionHandoffRemediationIncidentDigest();
        const sourceSummary = summary && typeof summary === "object"
          ? summary
          : buildMissionHandoffRemediationIncidentSlaSummary();
        const hints = [];
        if (sourceDigest.length <= 0) {
          hints.push("Digest clean: повторюваних fingerprints немає.");
          return hints;
        }
        const top = sourceDigest[0];
        if (top && top.active_count > 0) {
          hints.push(`Top fingerprint ${top.profile_id}: active=${top.active_count}, oldest=${top.oldest_age_label}.`);
        }
        if (sourceSummary.active_count > 0 && Number(sourceSummary.oldest_active_age_sec || 0) >= 20 * 60) {
          hints.push("Oldest active >= 20m: пріоритетно ACK/Snooze або escalation decision.");
        }
        if (top && top.total >= 3) {
          hints.push(`Повторюваний pattern (${top.total}): перевір policy/profile і handoff quality next-actions.`);
        }
        if (hints.length <= 0) hints.push("Інциденти контрольовані: продовжуйте стандартний cadence handoff.");
        return hints.slice(0, 3);
      }
      function renderMissionHandoffRemediationIncidentDigest(items = null, summary = null) {
        const digestNode = byId("sideHandoffRemediationIncidentDigest");
        const triageNode = byId("sideHandoffRemediationIncidentTriage");
        if (!digestNode && !triageNode) return;
        const digest = buildMissionHandoffRemediationIncidentDigest(items);
        const sourceSummary = summary && typeof summary === "object"
          ? summary
          : buildMissionHandoffRemediationIncidentSlaSummary(items);
        const hints = buildMissionHandoffRemediationIncidentTriageHints(digest, sourceSummary);
        if (digestNode) {
          if (digest.length <= 0) {
            digestNode.innerHTML = '<span class="sideMiniEmpty">—</span>';
          } else {
            digestNode.innerHTML = digest
              .map((item, index) => {
                const label = `${index + 1}. ${item.profile_id} · total=${item.total} · active=${item.active_count} · oldest=${item.oldest_age_label}`;
                const meta = `${item.last_state.toUpperCase()} · ${item.context || "context=n/a"}`;
                return (
                  `<div class="sideHandoffTimelineRow">`
                  + `<div class="sideHandoffTimelineMeta"><span>${esc(label)}</span></div>`
                  + `<div class="sideHandoffTimelineBody">${esc(missionTrimText(meta, 120))}</div>`
                  + `</div>`
                );
              })
              .join("");
          }
        }
        if (triageNode) {
          triageNode.textContent = `Digest triage: ${hints[0] || "—"}`;
        }
      }
      function missionHandoffRemediationPlannerSuggestAction(item, summary = null) {
        const source = item && typeof item === "object" ? item : {};
        const sourceSummary = summary && typeof summary === "object"
          ? summary
          : buildMissionHandoffRemediationIncidentSlaSummary();
        const oldestSec = Math.max(0, Number(source.oldest_age_sec || 0));
        const activeCount = Math.max(0, Number(source.active_count || 0));
        const snoozedCount = Math.max(0, Number(source.snoozed_count || 0));
        const total = Math.max(0, Number(source.total || 0));
        let action = "ack";
        let reason = "підтвердити контроль по active incidents";
        if (activeCount > 0 && oldestSec >= 30 * 60) {
          action = "escalate";
          reason = "oldest active >= 30m";
        } else if (activeCount >= 2) {
          action = "ack";
          reason = "multiple active incidents";
        } else if (snoozedCount > 0 && activeCount === 0) {
          action = "profile-check";
          reason = "snoozed backlog без active";
        } else if (total >= 3) {
          action = "profile-check";
          reason = "repeat pattern";
        } else if (activeCount > 0) {
          action = "snooze";
          reason = "active, але без stale threshold";
        }
        if (sourceSummary.active_count <= 0 && action !== "profile-check") {
          action = "profile-check";
          reason = "active incidents відсутні";
        }
        return {
          action,
          reason,
          fingerprint: String(source.fingerprint || ""),
          profile_id: String(source.profile_id || "standard"),
          context: missionTrimText(String(source.context || ""), 96),
          oldest_age_label: String(source.oldest_age_label || "—"),
          active_count: activeCount,
          total,
        };
      }
      function buildMissionHandoffRemediationActionPlan(items = null, summary = null) {
        const digest = buildMissionHandoffRemediationIncidentDigest(items);
        const sourceSummary = summary && typeof summary === "object"
          ? summary
          : buildMissionHandoffRemediationIncidentSlaSummary(items);
        const suggestions = digest.map((item) => missionHandoffRemediationPlannerSuggestAction(item, sourceSummary));
        const primary = suggestions[0] || null;
        const handoffLines = [
          `Remediation digest plan @ ${new Date().toISOString()}`,
          `Incidents: active=${sourceSummary.active_count} snoozed=${sourceSummary.snoozed_count} acked=${sourceSummary.acked_count} oldest=${sourceSummary.oldest_active_age_label}`,
        ];
        if (suggestions.length <= 0) {
          handoffLines.push("1) digest clean: підтримуйте стандартний handoff cadence.");
        } else {
          suggestions.slice(0, 4).forEach((item, index) => {
            handoffLines.push(`${index + 1}) [${item.action}] ${item.profile_id} · active=${item.active_count} · oldest=${item.oldest_age_label} · reason=${item.reason}`);
          });
        }
        return {
          kind: "passengers.mission.handoff_remediation_digest_plan.v1",
          generated_at: new Date().toISOString(),
          summary: sourceSummary,
          suggestions,
          primary,
          handoff_text: handoffLines.join("\n"),
        };
      }
      function renderMissionHandoffRemediationActionPlan(items = null, summary = null) {
        const summaryNode = byId("sideHandoffRemediationPlanSummary");
        const listNode = byId("sideHandoffRemediationPlan");
        if (!summaryNode && !listNode) return;
        const plan = buildMissionHandoffRemediationActionPlan(items, summary);
        const primary = plan.primary && typeof plan.primary === "object" ? plan.primary : null;
        if (summaryNode) {
          summaryNode.textContent = primary
            ? `Planner: primary=${primary.action} · ${primary.profile_id} · reason=${primary.reason}`
            : "Planner: digest clean";
        }
        const ledger = listMissionHandoffRemediationDecisionLedger();
        const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
        const closeoutGovernance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
        renderMissionHandoffRemediationDecisionCoverage(plan, ledger);
        renderMissionHandoffRemediationDecisionLedger(ledger);
        renderMissionHandoffRemediationDecisionBacklog(backlog);
        renderMissionHandoffRemediationCloseoutGovernance(closeoutGovernance);
        if (!listNode) return;
        if (!Array.isArray(plan.suggestions) || plan.suggestions.length <= 0) {
          listNode.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        listNode.innerHTML = plan.suggestions.slice(0, 4)
          .map((item, index) => {
            const title = `${index + 1}. ${item.action.toUpperCase()} · ${item.profile_id}`;
            const body = `active=${item.active_count} · oldest=${item.oldest_age_label} · ${item.reason}`;
            return (
              `<div class="sideHandoffTimelineRow">`
              + `<div class="sideHandoffTimelineMeta"><span>${esc(title)}</span></div>`
              + `<div class="sideHandoffTimelineBody">${esc(missionTrimText(body, 120))}</div>`
              + `</div>`
            );
          })
          .join("");
      }
      function runMissionHandoffRemediationPlanAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        if (!mode) return false;
        const statusNode = byId("sideMissionStatus");
        const plan = buildMissionHandoffRemediationActionPlan();
        if (mode === "show") {
          window.prompt("Mission remediation digest plan (JSON):", JSON.stringify(plan, null, 2));
          appendMissionHandoffTimelineEvent("remediation_digest_plan_show", {
            context: buildMissionContextLabel(),
            text: `suggestions=${Array.isArray(plan.suggestions) ? plan.suggestions.length : 0}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Digest plan: показано ${Array.isArray(plan.suggestions) ? plan.suggestions.length : 0}`;
          return true;
        }
        if (mode === "log-primary") {
          const primary = plan.primary && typeof plan.primary === "object" ? plan.primary : null;
          if (!primary) {
            if (statusNode) statusNode.textContent = "Digest plan: primary suggestion відсутній";
            return false;
          }
          const ledger = appendMissionHandoffRemediationDecision({
            ts: new Date().toISOString(),
            fingerprint: String(primary.fingerprint || ""),
            profile_id: String(primary.profile_id || "standard"),
            context: String(primary.context || ""),
            decision: String(primary.action || "profile-check"),
            reason: String(primary.reason || "planner primary"),
            source: "planner-primary",
          });
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          renderMissionHandoffRemediationDecisionCoverage(plan, ledger);
          renderMissionHandoffRemediationDecisionLedger(ledger);
          renderMissionHandoffRemediationDecisionBacklog(backlog);
          renderMissionHandoffRemediationCloseoutGovernance(buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog));
          appendMissionHandoffTimelineEvent("remediation_digest_plan_log_primary", {
            context: buildMissionContextLabel(),
            text: `action=${String(primary.action || "profile-check")} profile=${String(primary.profile_id || "standard")}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Digest plan: primary logged (${String(primary.action || "profile-check")})`;
          return true;
        }
        if (mode === "ledger-show") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const payload = { kind: "passengers.mission.handoff_remediation_decision_ledger.v1", generated_at: new Date().toISOString(), items: ledger.slice(0, MISSION_HANDOFF_REMEDIATION_DECISION_LEDGER_LIMIT) };
          window.prompt("Remediation decision ledger (JSON):", JSON.stringify(payload, null, 2));
          appendMissionHandoffTimelineEvent("remediation_decision_ledger_show", {
            context: buildMissionContextLabel(),
            text: `items=${payload.items.length}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Decision ledger: показано ${payload.items.length}`;
          return true;
        }
        if (mode === "ledger-export") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const payload = { kind: "passengers.mission.handoff_remediation_decision_ledger.v1", generated_at: new Date().toISOString(), items: ledger.slice(0, MISSION_HANDOFF_REMEDIATION_DECISION_LEDGER_LIMIT) };
          copyTextWithFallback(JSON.stringify(payload, null, 2), "Скопіюйте remediation decision ledger JSON:", "Decision ledger: JSON скопійовано", "Decision ledger: JSON у prompt");
          appendMissionHandoffTimelineEvent("remediation_decision_ledger_export", {
            context: buildMissionContextLabel(),
            text: `items=${payload.items.length}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Decision ledger: JSON експортовано";
          return true;
        }
        if (mode === "ledger-clear") {
          const confirmed = window.confirm("Очистити remediation decision ledger?");
          if (!confirmed) return false;
          storeMissionHandoffRemediationDecisionLedger([]);
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, []);
          renderMissionHandoffRemediationDecisionCoverage(plan, []);
          renderMissionHandoffRemediationDecisionLedger([]);
          renderMissionHandoffRemediationDecisionBacklog(backlog);
          renderMissionHandoffRemediationCloseoutGovernance(buildMissionHandoffRemediationCloseoutGovernance(plan, [], backlog));
          appendMissionHandoffTimelineEvent("remediation_decision_ledger_clear", {
            context: buildMissionContextLabel(),
            text: "items=0",
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Decision ledger: очищено";
          return true;
        }
        const backlogItemMatch = mode.match(/^backlog-item-(ack|snooze|profile-check)-([0-9]+)$/);
        if (backlogItemMatch) {
          const decision = normalizeMissionHandoffRemediationBacklogDecision(String(backlogItemMatch[1] || ""), "profile-check");
          const itemIndex = Number(backlogItemMatch[2]);
          const result = applyMissionHandoffRemediationBacklogCloseout(decision, {
            plan,
            ledger: listMissionHandoffRemediationDecisionLedger(),
            item_index: itemIndex,
          });
          renderMissionHandoffRemediationDecisionCoverage(plan, result.ledger);
          renderMissionHandoffRemediationDecisionLedger(result.ledger);
          renderMissionHandoffRemediationDecisionBacklog(result.backlog);
          renderMissionHandoffRemediationCloseoutGovernance(buildMissionHandoffRemediationCloseoutGovernance(plan, result.ledger, result.backlog));
          appendMissionHandoffTimelineEvent("remediation_decision_backlog_closeout_item", {
            context: buildMissionContextLabel(),
            text: `decision=${result.decision} index=${Number.isFinite(itemIndex) ? itemIndex : -1} applied=${Number(result.applied_count || 0)} remaining=${Number(result.backlog && result.backlog.missing_count || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) {
            statusNode.textContent = Number(result.applied_count || 0) > 0
              ? `Decision backlog: ${result.decision} applied (${result.applied_count})`
              : "Decision backlog: item closeout не застосовано";
          }
          return Number(result.applied_count || 0) > 0;
        }
        const backlogBatchMatch = mode.match(/^backlog-batch-(ack|snooze|profile-check)$/);
        if (backlogBatchMatch) {
          const decision = normalizeMissionHandoffRemediationBacklogDecision(String(backlogBatchMatch[1] || ""), "profile-check");
          const result = applyMissionHandoffRemediationBacklogCloseout(decision, {
            plan,
            ledger: listMissionHandoffRemediationDecisionLedger(),
            batch_limit: MISSION_HANDOFF_REMEDIATION_DECISION_BACKLOG_CLOSEOUT_LIMIT,
          });
          renderMissionHandoffRemediationDecisionCoverage(plan, result.ledger);
          renderMissionHandoffRemediationDecisionLedger(result.ledger);
          renderMissionHandoffRemediationDecisionBacklog(result.backlog);
          renderMissionHandoffRemediationCloseoutGovernance(buildMissionHandoffRemediationCloseoutGovernance(plan, result.ledger, result.backlog));
          appendMissionHandoffTimelineEvent("remediation_decision_backlog_closeout_batch", {
            context: buildMissionContextLabel(),
            text: `decision=${result.decision} applied=${Number(result.applied_count || 0)} remaining=${Number(result.backlog && result.backlog.missing_count || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) {
            statusNode.textContent = Number(result.applied_count || 0) > 0
              ? `Decision backlog batch: ${result.decision} (${result.applied_count})`
              : "Decision backlog batch: немає missing decisions";
          }
          return Number(result.applied_count || 0) > 0;
        }
        if (mode === "backlog-show") {
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, listMissionHandoffRemediationDecisionLedger());
          window.prompt("Mission remediation decision backlog (JSON):", JSON.stringify(backlog, null, 2));
          renderMissionHandoffRemediationDecisionBacklog(backlog);
          renderMissionHandoffRemediationCloseoutGovernance(buildMissionHandoffRemediationCloseoutGovernance(plan, listMissionHandoffRemediationDecisionLedger(), backlog));
          appendMissionHandoffTimelineEvent("remediation_decision_backlog_show", {
            context: buildMissionContextLabel(),
            text: `missing=${Number(backlog.missing_count || 0)} coverage=${Number(backlog.coverage_pct || 0)}%`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Decision backlog: показано ${Number(backlog.missing_count || 0)}`;
          return true;
        }
        if (mode === "backlog-export") {
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, listMissionHandoffRemediationDecisionLedger());
          copyTextWithFallback(JSON.stringify(backlog, null, 2), "Скопіюйте remediation decision backlog JSON:", "Decision backlog: JSON скопійовано", "Decision backlog: JSON у prompt");
          renderMissionHandoffRemediationDecisionBacklog(backlog);
          renderMissionHandoffRemediationCloseoutGovernance(buildMissionHandoffRemediationCloseoutGovernance(plan, listMissionHandoffRemediationDecisionLedger(), backlog));
          appendMissionHandoffTimelineEvent("remediation_decision_backlog_export", {
            context: buildMissionContextLabel(),
            text: `missing=${Number(backlog.missing_count || 0)} coverage=${Number(backlog.coverage_pct || 0)}%`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Decision backlog: JSON експортовано";
          return true;
        }
        if (mode === "backlog-copy") {
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, listMissionHandoffRemediationDecisionLedger());
          copyTextWithFallback(String(backlog.handoff_text || ""), "Скопіюйте decision backlog handoff summary:", "Decision backlog: handoff скопійовано", "Decision backlog: handoff у prompt");
          renderMissionHandoffRemediationDecisionBacklog(backlog);
          renderMissionHandoffRemediationCloseoutGovernance(buildMissionHandoffRemediationCloseoutGovernance(plan, listMissionHandoffRemediationDecisionLedger(), backlog));
          appendMissionHandoffTimelineEvent("remediation_decision_backlog_copy", {
            context: buildMissionContextLabel(),
            text: `missing=${Number(backlog.missing_count || 0)} coverage=${Number(backlog.coverage_pct || 0)}%`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Decision backlog: handoff скопійовано";
          return true;
        }
        if (mode === "closeout-governance-show") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          window.prompt("Mission remediation closeout governance (JSON):", JSON.stringify(governance, null, 2));
          renderMissionHandoffRemediationCloseoutGovernance(governance);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_governance_show", {
            context: buildMissionContextLabel(),
            text: `status=${String(governance.status || "n/a")} remaining=${Number(governance.remaining_gap || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Closeout governance: показано (remaining ${Number(governance.remaining_gap || 0)})`;
          return true;
        }
        if (mode === "closeout-governance-export") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          copyTextWithFallback(JSON.stringify(governance, null, 2), "Скопіюйте remediation closeout governance JSON:", "Closeout governance: JSON скопійовано", "Closeout governance: JSON у prompt");
          renderMissionHandoffRemediationCloseoutGovernance(governance);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_governance_export", {
            context: buildMissionContextLabel(),
            text: `status=${String(governance.status || "n/a")} remaining=${Number(governance.remaining_gap || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Closeout governance: JSON експортовано";
          return true;
        }
        if (mode === "closeout-escalation-show") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          const escalation = buildMissionHandoffRemediationCloseoutEscalation(governance);
          window.prompt("Mission remediation closeout escalation (JSON):", JSON.stringify(escalation, null, 2));
          renderMissionHandoffRemediationCloseoutEscalation(escalation);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_escalation_show", {
            context: buildMissionContextLabel(),
            text: `level=${String(escalation.level || "n/a")} route=${String(escalation.route || "n/a")} remaining=${Number(escalation.remaining_gap || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Closeout escalation: показано (${String(escalation.level || "n/a")})`;
          return true;
        }
        if (mode === "closeout-escalation-export") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          const escalation = buildMissionHandoffRemediationCloseoutEscalation(governance);
          copyTextWithFallback(JSON.stringify(escalation, null, 2), "Скопіюйте remediation closeout escalation JSON:", "Closeout escalation: JSON скопійовано", "Closeout escalation: JSON у prompt");
          renderMissionHandoffRemediationCloseoutEscalation(escalation);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_escalation_export", {
            context: buildMissionContextLabel(),
            text: `level=${String(escalation.level || "n/a")} route=${String(escalation.route || "n/a")} remaining=${Number(escalation.remaining_gap || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Closeout escalation: JSON експортовано";
          return true;
        }
        if (mode === "closeout-escalation-copy") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          const escalation = buildMissionHandoffRemediationCloseoutEscalation(governance);
          copyTextWithFallback(String(escalation.handoff_text || ""), "Скопіюйте remediation closeout escalation handoff:", "Closeout escalation: handoff скопійовано", "Closeout escalation: handoff у prompt");
          renderMissionHandoffRemediationCloseoutEscalation(escalation);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_escalation_copy", {
            context: buildMissionContextLabel(),
            text: `level=${String(escalation.level || "n/a")} route=${String(escalation.route || "n/a")} remaining=${Number(escalation.remaining_gap || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Closeout escalation: handoff скопійовано";
          return true;
        }
        if (mode === "closeout-escalation-ack") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          const escalation = buildMissionHandoffRemediationCloseoutEscalation(governance);
          const executionItems = appendMissionHandoffRemediationCloseoutEscalationExecutionEntry({
            ts: new Date().toISOString(),
            state: "acked",
            level: String(escalation.level || "medium"),
            route: String(escalation.route || "next-shift"),
            channel: String(escalation.channel || "handoff"),
            action: String(escalation.action || "queue-next-shift"),
            policy_id: String(escalation.policy_id || "custom"),
            status: String(escalation.status || "open"),
            remaining_gap: Number(escalation.remaining_gap || 0),
            coverage_pct: Number(escalation.coverage_pct || 0),
            reason: `execution ack ${String(escalation.route || "n/a")}`,
            context: buildMissionContextLabel(),
          });
          const execution = buildMissionHandoffRemediationCloseoutEscalationExecutionState(escalation, executionItems);
          renderMissionHandoffRemediationCloseoutEscalation(escalation);
          renderMissionHandoffRemediationCloseoutEscalationExecution(execution);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_escalation_ack", {
            context: buildMissionContextLabel(),
            text: `level=${String(escalation.level || "n/a")} route=${String(escalation.route || "n/a")} active=${Number(execution.active_count || 0)} stale=${Number(execution.stale_count || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Closeout escalation: ACK записано";
          return true;
        }
        if (mode === "closeout-escalation-snooze") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          const escalation = buildMissionHandoffRemediationCloseoutEscalation(governance);
          const raw = window.prompt("Escalation snooze minutes:", String(MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_SNOOZE_MIN));
          const mins = Math.max(1, Math.min(180, Number(raw || MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_SNOOZE_MIN) || MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_SNOOZE_MIN));
          const snoozeUntil = new Date(Date.now() + mins * 60 * 1000).toISOString();
          const executionItems = appendMissionHandoffRemediationCloseoutEscalationExecutionEntry({
            ts: new Date().toISOString(),
            state: "snoozed",
            level: String(escalation.level || "medium"),
            route: String(escalation.route || "next-shift"),
            channel: String(escalation.channel || "handoff"),
            action: String(escalation.action || "queue-next-shift"),
            policy_id: String(escalation.policy_id || "custom"),
            status: String(escalation.status || "open"),
            remaining_gap: Number(escalation.remaining_gap || 0),
            coverage_pct: Number(escalation.coverage_pct || 0),
            reason: `execution snooze ${mins}m`,
            context: buildMissionContextLabel(),
            snooze_until: snoozeUntil,
          });
          const execution = buildMissionHandoffRemediationCloseoutEscalationExecutionState(escalation, executionItems);
          renderMissionHandoffRemediationCloseoutEscalation(escalation);
          renderMissionHandoffRemediationCloseoutEscalationExecution(execution);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_escalation_snooze", {
            context: buildMissionContextLabel(),
            text: `level=${String(escalation.level || "n/a")} route=${String(escalation.route || "n/a")} mins=${mins} active=${Number(execution.active_count || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Closeout escalation: snooze ${mins}m`;
          return true;
        }
        if (mode === "closeout-escalation-resolve") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          const escalation = buildMissionHandoffRemediationCloseoutEscalation(governance);
          const executionItems = appendMissionHandoffRemediationCloseoutEscalationExecutionEntry({
            ts: new Date().toISOString(),
            state: "resolved",
            level: String(escalation.level || "medium"),
            route: String(escalation.route || "next-shift"),
            channel: String(escalation.channel || "handoff"),
            action: String(escalation.action || "queue-next-shift"),
            policy_id: String(escalation.policy_id || "custom"),
            status: String(escalation.status || "open"),
            remaining_gap: Number(escalation.remaining_gap || 0),
            coverage_pct: Number(escalation.coverage_pct || 0),
            reason: "execution resolved",
            context: buildMissionContextLabel(),
          });
          const execution = buildMissionHandoffRemediationCloseoutEscalationExecutionState(escalation, executionItems);
          renderMissionHandoffRemediationCloseoutEscalation(escalation);
          renderMissionHandoffRemediationCloseoutEscalationExecution(execution);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_escalation_resolve", {
            context: buildMissionContextLabel(),
            text: `level=${String(escalation.level || "n/a")} route=${String(escalation.route || "n/a")} active=${Number(execution.active_count || 0)} stale=${Number(execution.stale_count || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Closeout escalation: resolved";
          return true;
        }
        if (mode === "closeout-escalation-log-show") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          const escalation = buildMissionHandoffRemediationCloseoutEscalation(governance);
          const execution = buildMissionHandoffRemediationCloseoutEscalationExecutionState(escalation);
          window.prompt("Mission remediation closeout escalation execution (JSON):", JSON.stringify(execution, null, 2));
          renderMissionHandoffRemediationCloseoutEscalationExecution(execution);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_escalation_execution_show", {
            context: buildMissionContextLabel(),
            text: `sla=${String(execution.sla_status || "idle")} active=${Number(execution.active_count || 0)} stale=${Number(execution.stale_count || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Closeout escalation execution: показано (${String(execution.sla_status_label || "IDLE")})`;
          return true;
        }
        if (mode === "closeout-escalation-log-export") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          const escalation = buildMissionHandoffRemediationCloseoutEscalation(governance);
          const execution = buildMissionHandoffRemediationCloseoutEscalationExecutionState(escalation);
          copyTextWithFallback(JSON.stringify(execution, null, 2), "Скопіюйте remediation closeout escalation execution JSON:", "Closeout escalation execution: JSON скопійовано", "Closeout escalation execution: JSON у prompt");
          renderMissionHandoffRemediationCloseoutEscalationExecution(execution);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_escalation_execution_export", {
            context: buildMissionContextLabel(),
            text: `sla=${String(execution.sla_status || "idle")} active=${Number(execution.active_count || 0)} stale=${Number(execution.stale_count || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Closeout escalation execution: JSON експортовано";
          return true;
        }
        if (mode === "closeout-escalation-log-copy") {
          const ledger = listMissionHandoffRemediationDecisionLedger();
          const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledger);
          const governance = buildMissionHandoffRemediationCloseoutGovernance(plan, ledger, backlog);
          const escalation = buildMissionHandoffRemediationCloseoutEscalation(governance);
          const execution = buildMissionHandoffRemediationCloseoutEscalationExecutionState(escalation);
          copyTextWithFallback(String(execution.handoff_text || ""), "Скопіюйте remediation closeout escalation execution handoff:", "Closeout escalation execution: handoff скопійовано", "Closeout escalation execution: handoff у prompt");
          renderMissionHandoffRemediationCloseoutEscalationExecution(execution);
          appendMissionHandoffTimelineEvent("remediation_decision_closeout_escalation_execution_copy", {
            context: buildMissionContextLabel(),
            text: `sla=${String(execution.sla_status || "idle")} active=${Number(execution.active_count || 0)} stale=${Number(execution.stale_count || 0)}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Closeout escalation execution: handoff скопійовано";
          return true;
        }
        if (mode === "export") {
          copyTextWithFallback(JSON.stringify(plan, null, 2), "Скопіюйте remediation digest plan JSON:", "Digest plan: JSON скопійовано", "Digest plan: JSON у prompt");
          appendMissionHandoffTimelineEvent("remediation_digest_plan_export", {
            context: buildMissionContextLabel(),
            text: `suggestions=${Array.isArray(plan.suggestions) ? plan.suggestions.length : 0}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Digest plan: JSON експортовано";
          return true;
        }
        if (mode === "copy") {
          copyTextWithFallback(String(plan.handoff_text || ""), "Скопіюйте handoff plan:", "Digest plan: handoff скопійовано", "Digest plan: handoff у prompt");
          appendMissionHandoffTimelineEvent("remediation_digest_plan_copy", {
            context: buildMissionContextLabel(),
            text: `primary=${String(plan.primary && plan.primary.action || "none")}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Digest plan: handoff-план скопійовано";
          return true;
        }
        return false;
      }

      function normalizeMissionHandoffRemediationDecisionItem(source = null) {
        const raw = source && typeof source === "object" ? source : {};
        const ts = String(raw.ts || new Date().toISOString());
        const decision = missionTrimText(String(raw.decision || "profile-check").trim().toLowerCase(), 32) || "profile-check";
        return {
          id: missionTrimText(String(raw.id || `${Date.now()}-${Math.floor(Math.random() * 100000)}`), 48),
          ts,
          fingerprint: missionTrimText(String(raw.fingerprint || ""), 96),
          profile_id: missionTrimText(String(raw.profile_id || "standard"), 32),
          context: missionTrimText(String(raw.context || ""), 96),
          decision,
          reason: missionTrimText(String(raw.reason || ""), 180),
          source: missionTrimText(String(raw.source || "manual"), 48),
        };
      }
      function listMissionHandoffRemediationDecisionLedger() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_HANDOFF_REMEDIATION_DECISION_LEDGER_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw.map((item) => normalizeMissionHandoffRemediationDecisionItem(item)).slice(0, MISSION_HANDOFF_REMEDIATION_DECISION_LEDGER_LIMIT);
        } catch (_error) {
          return [];
        }
      }
      function storeMissionHandoffRemediationDecisionLedger(items = []) {
        const normalized = (Array.isArray(items) ? items : [])
          .map((item) => normalizeMissionHandoffRemediationDecisionItem(item))
          .slice(0, MISSION_HANDOFF_REMEDIATION_DECISION_LEDGER_LIMIT);
        try { localStorage.setItem(MISSION_HANDOFF_REMEDIATION_DECISION_LEDGER_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function appendMissionHandoffRemediationDecision(payload = {}) {
        const current = listMissionHandoffRemediationDecisionLedger();
        current.unshift(normalizeMissionHandoffRemediationDecisionItem(payload));
        return storeMissionHandoffRemediationDecisionLedger(current);
      }
      function missionHandoffRemediationDecisionMatchKey(item = null) {
        const source = item && typeof item === "object" ? item : {};
        const fingerprint = String(source.fingerprint || "").trim();
        const decision = String(source.action || source.decision || "").trim().toLowerCase();
        if (!fingerprint || !decision) return "";
        return `${fingerprint}|${decision}`;
      }
      function buildMissionHandoffRemediationDecisionBacklog(plan = null, ledgerItems = null) {
        const sourcePlan = plan && typeof plan === "object" ? plan : buildMissionHandoffRemediationActionPlan();
        const suggestions = Array.isArray(sourcePlan.suggestions) ? sourcePlan.suggestions : [];
        const ledger = Array.isArray(ledgerItems) ? ledgerItems : listMissionHandoffRemediationDecisionLedger();
        const ledgerKeys = new Set(
          ledger
            .map((item) => missionHandoffRemediationDecisionMatchKey(item))
            .filter((key) => !!key)
        );
        let planned = 0;
        let logged = 0;
        const missingItems = [];
        for (const item of suggestions) {
          const key = missionHandoffRemediationDecisionMatchKey(item);
          if (!key) continue;
          planned += 1;
          if (ledgerKeys.has(key)) {
            logged += 1;
            continue;
          }
          missingItems.push({
            fingerprint: String(item && item.fingerprint || ""),
            profile_id: String(item && item.profile_id || "standard"),
            context: missionTrimText(String(item && item.context || ""), 96),
            action: String(item && item.action || "profile-check").trim().toLowerCase(),
            reason: missionTrimText(String(item && item.reason || ""), 180),
            active_count: Math.max(0, Number(item && item.active_count || 0)),
            oldest_age_label: String(item && item.oldest_age_label || "—"),
          });
        }
        const coveragePct = planned > 0 ? Math.max(0, Math.min(100, Math.round((logged / planned) * 100))) : 100;
        const generatedAt = new Date().toISOString();
        const handoffLines = [
          `Decision backlog @ ${generatedAt}`,
          `Coverage: ${logged}/${planned} (${coveragePct}%)`,
        ];
        if (missingItems.length <= 0) {
          handoffLines.push("1) Backlog clean: planner decisions закрито, підтримуйте стандартний cadence.");
        } else {
          missingItems.slice(0, 6).forEach((item, index) => {
            handoffLines.push(
              `${index + 1}) [${String(item.action || "profile-check")}] ${String(item.profile_id || "standard")} · active=${Number(item.active_count || 0)} · oldest=${String(item.oldest_age_label || "—")} · reason=${String(item.reason || "n/a")}`
            );
          });
          if (missingItems.length > 6) {
            handoffLines.push(`+${missingItems.length - 6} more decisions in backlog`);
          }
        }
        return {
          kind: "passengers.mission.handoff_remediation_decision_backlog.v1",
          generated_at: generatedAt,
          planned,
          logged,
          coverage_pct: coveragePct,
          missing_count: missingItems.length,
          missing_items: missingItems.slice(0, 24),
          missing_labels: missingItems.slice(0, 3).map((item) => `${String(item.profile_id || "standard")}:${String(item.action || "profile-check")}`),
          handoff_text: handoffLines.join("\n"),
        };
      }
      function normalizeMissionHandoffRemediationBacklogDecision(value = "", fallback = "profile-check") {
        const clean = String(value || "").trim().toLowerCase();
        if (clean === "ack" || clean === "snooze" || clean === "profile-check") return clean;
        return String(fallback || "profile-check");
      }
      function applyMissionHandoffRemediationBacklogCloseout(decision = "profile-check", options = {}) {
        const normalizedDecision = normalizeMissionHandoffRemediationBacklogDecision(decision, "profile-check");
        const source = options && typeof options === "object" ? options : {};
        const plan = source.plan && typeof source.plan === "object" ? source.plan : buildMissionHandoffRemediationActionPlan();
        const baseLedger = Array.isArray(source.ledger) ? source.ledger.slice() : listMissionHandoffRemediationDecisionLedger().slice();
        const backlog = source.backlog && typeof source.backlog === "object"
          ? source.backlog
          : buildMissionHandoffRemediationDecisionBacklog(plan, baseLedger);
        const missing = Array.isArray(backlog.missing_items) ? backlog.missing_items : [];
        if (missing.length <= 0) {
          const coverage = buildMissionHandoffRemediationDecisionCoverage(plan, baseLedger);
          return {
            decision: normalizedDecision,
            applied_count: 0,
            target_scope: "none",
            target_index: null,
            applied_items: [],
            ledger: baseLedger,
            backlog,
            coverage,
          };
        }
        let targets = [];
        let targetScope = "batch";
        let targetIndex = null;
        const rawIndex = Number(source.item_index);
        if (Number.isFinite(rawIndex) && rawIndex >= 0 && rawIndex < missing.length) {
          targetScope = "single";
          targetIndex = Math.floor(rawIndex);
          targets = [missing[targetIndex]];
        } else {
          const limitRaw = Number(source.batch_limit);
          const limit = Number.isFinite(limitRaw)
            ? Math.max(1, Math.min(MISSION_HANDOFF_REMEDIATION_DECISION_LEDGER_LIMIT, Math.floor(limitRaw)))
            : MISSION_HANDOFF_REMEDIATION_DECISION_BACKLOG_CLOSEOUT_LIMIT;
          targets = missing.slice(0, limit);
        }
        if (targets.length <= 0) {
          const coverage = buildMissionHandoffRemediationDecisionCoverage(plan, baseLedger);
          return {
            decision: normalizedDecision,
            applied_count: 0,
            target_scope: targetScope,
            target_index: targetIndex,
            applied_items: [],
            ledger: baseLedger,
            backlog,
            coverage,
          };
        }
        const nowIso = new Date().toISOString();
        for (const item of targets) {
          baseLedger.unshift(normalizeMissionHandoffRemediationDecisionItem({
            ts: nowIso,
            fingerprint: String(item && item.fingerprint || ""),
            profile_id: String(item && item.profile_id || "standard"),
            context: String(item && item.context || ""),
            decision: normalizedDecision,
            reason: targetScope === "single"
              ? `backlog closeout ${normalizedDecision}`
              : `backlog batch closeout ${normalizedDecision}`,
            source: targetScope === "single" ? "backlog-closeout" : "backlog-closeout-batch",
          }));
        }
        const storedLedger = storeMissionHandoffRemediationDecisionLedger(baseLedger);
        const nextBacklog = buildMissionHandoffRemediationDecisionBacklog(plan, storedLedger);
        const coverage = buildMissionHandoffRemediationDecisionCoverage(plan, storedLedger);
        return {
          decision: normalizedDecision,
          applied_count: targets.length,
          target_scope: targetScope,
          target_index: targetIndex,
          applied_items: targets,
          ledger: storedLedger,
          backlog: nextBacklog,
          coverage,
        };
      }
      function listMissionHandoffRemediationCloseoutEntries(ledgerItems = null) {
        const source = Array.isArray(ledgerItems) ? ledgerItems : listMissionHandoffRemediationDecisionLedger();
        return source.filter((item) => {
          const itemSource = String(item && item.source || "").trim().toLowerCase();
          return itemSource === "backlog-closeout" || itemSource === "backlog-closeout-batch";
        });
      }
      function buildMissionHandoffRemediationCloseoutGovernance(plan = null, ledgerItems = null, backlog = null) {
        const sourcePlan = plan && typeof plan === "object" ? plan : buildMissionHandoffRemediationActionPlan();
        const ledger = Array.isArray(ledgerItems) ? ledgerItems : listMissionHandoffRemediationDecisionLedger();
        const sourceBacklog = backlog && typeof backlog === "object"
          ? backlog
          : buildMissionHandoffRemediationDecisionBacklog(sourcePlan, ledger);
        const closeoutEntries = listMissionHandoffRemediationCloseoutEntries(ledger);
        const singleCount = closeoutEntries.filter((item) => String(item && item.source || "").trim().toLowerCase() === "backlog-closeout").length;
        const batchCount = closeoutEntries.filter((item) => String(item && item.source || "").trim().toLowerCase() === "backlog-closeout-batch").length;
        const decisionCounters = { ack: 0, snooze: 0, "profile-check": 0 };
        for (const item of closeoutEntries) {
          const decision = normalizeMissionHandoffRemediationBacklogDecision(String(item && item.decision || ""), "profile-check");
          decisionCounters[decision] = Number(decisionCounters[decision] || 0) + 1;
        }
        const coverage = buildMissionHandoffRemediationDecisionCoverage(sourcePlan, ledger);
        const remainingGap = Math.max(0, Number(sourceBacklog && sourceBacklog.missing_count || 0));
        let status = "open";
        let statusLabel = "OPEN";
        if (remainingGap <= 0) {
          status = "closed";
          statusLabel = "CLOSED";
        } else if (closeoutEntries.length > 0 && Number(coverage.coverage_pct || 0) >= 70) {
          status = "progress";
          statusLabel = "PROGRESS";
        } else if (closeoutEntries.length > 0) {
          status = "risk";
          statusLabel = "RISK";
        }
        const generatedAt = new Date().toISOString();
        const lines = [
          `Closeout governance @ ${generatedAt}`,
          `status=${statusLabel} remaining=${remainingGap} coverage=${Number(coverage.coverage_pct || 0)}%`,
          `closeouts total=${closeoutEntries.length} single=${singleCount} batch=${batchCount}`,
          `decisions ack=${Number(decisionCounters.ack || 0)} snooze=${Number(decisionCounters.snooze || 0)} profile-check=${Number(decisionCounters["profile-check"] || 0)}`,
        ];
        return {
          kind: "passengers.mission.handoff_remediation_closeout_governance.v1",
          generated_at: generatedAt,
          status,
          status_label: statusLabel,
          coverage_pct: Number(coverage.coverage_pct || 0),
          remaining_gap: remainingGap,
          closeouts_total: closeoutEntries.length,
          closeouts_single: singleCount,
          closeouts_batch: batchCount,
          decision_counters: decisionCounters,
          recent_closeouts: closeoutEntries.slice(0, 6),
          handoff_text: lines.join("\n"),
        };
      }
      function resolveMissionHandoffRemediationCloseoutEscalationPolicy(governance = null) {
        const source = governance && typeof governance === "object"
          ? governance
          : buildMissionHandoffRemediationCloseoutGovernance();
        const status = String(source.status || "open").trim().toLowerCase() || "open";
        const remainingGap = Math.max(0, Number(source.remaining_gap || 0));
        const policies = Array.isArray(MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_POLICIES)
          ? MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_POLICIES
          : [];
        for (const item of policies) {
          const policy = item && typeof item === "object" ? item : {};
          const statuses = Array.isArray(policy.statuses) ? policy.statuses : [];
          const minGap = Number(policy.min_remaining_gap);
          const maxGap = Number(policy.max_remaining_gap);
          if (statuses.length > 0 && !statuses.includes(status)) continue;
          if (Number.isFinite(minGap) && remainingGap < minGap) continue;
          if (Number.isFinite(maxGap) && remainingGap > maxGap) continue;
          return {
            id: String(policy.id || "custom"),
            level: String(policy.level || "medium"),
            route: String(policy.route || "next-shift"),
            channel: String(policy.channel || "handoff"),
            action: String(policy.action || "queue-next-shift"),
            reason: String(policy.reason || "closeout escalation policy"),
          };
        }
        return {
          id: "fallback",
          level: remainingGap > 0 ? "medium" : "none",
          route: remainingGap > 0 ? "next-shift" : "handoff-only",
          channel: remainingGap > 0 ? "handoff+ticket" : "none",
          action: remainingGap > 0 ? "queue-next-shift" : "monitor-only",
          reason: "fallback closeout escalation policy",
        };
      }
      function buildMissionHandoffRemediationCloseoutEscalation(governance = null) {
        const source = governance && typeof governance === "object"
          ? governance
          : buildMissionHandoffRemediationCloseoutGovernance();
        const policy = resolveMissionHandoffRemediationCloseoutEscalationPolicy(source);
        const remainingGap = Math.max(0, Number(source.remaining_gap || 0));
        const coverage = Number(source.coverage_pct || 0);
        const generatedAt = new Date().toISOString();
        const flags = [];
        if (remainingGap > 0) flags.push("gap-open");
        if (String(source.status || "").trim().toLowerCase() === "risk") flags.push("risk-status");
        if (Number(source.closeouts_batch || 0) > Number(source.closeouts_single || 0)) flags.push("batch-dominant");
        const lines = [
          `Closeout escalation @ ${generatedAt}`,
          `status=${String(source.status_label || "OPEN")} level=${String(policy.level || "medium").toUpperCase()} route=${String(policy.route || "next-shift")}`,
          `remaining=${remainingGap} coverage=${coverage}% action=${String(policy.action || "queue-next-shift")} channel=${String(policy.channel || "handoff")}`,
          `reason=${String(policy.reason || "closeout escalation policy")} flags=${flags.length > 0 ? flags.join(",") : "none"}`,
        ];
        return {
          kind: "passengers.mission.handoff_remediation_closeout_escalation.v1",
          generated_at: generatedAt,
          status: String(source.status || "open"),
          status_label: String(source.status_label || "OPEN"),
          remaining_gap: remainingGap,
          coverage_pct: coverage,
          closeouts_total: Number(source.closeouts_total || 0),
          closeouts_single: Number(source.closeouts_single || 0),
          closeouts_batch: Number(source.closeouts_batch || 0),
          level: String(policy.level || "medium"),
          route: String(policy.route || "next-shift"),
          channel: String(policy.channel || "handoff"),
          action: String(policy.action || "queue-next-shift"),
          policy_id: String(policy.id || "custom"),
          reason: String(policy.reason || "closeout escalation policy"),
          flags,
          handoff_text: lines.join("\n"),
        };
      }
      function normalizeMissionHandoffRemediationCloseoutEscalationExecutionItem(source = null) {
        const raw = source && typeof source === "object" ? source : {};
        const nowIso = new Date().toISOString();
        const rawState = missionTrimText(String(raw.state || "acked").trim().toLowerCase(), 24) || "acked";
        const state = ["acked", "snoozed", "resolved"].includes(rawState) ? rawState : "acked";
        return {
          id: missionTrimText(String(raw.id || `${Date.now()}-${Math.floor(Math.random() * 100000)}`), 48),
          ts: String(raw.ts || nowIso),
          state,
          level: missionTrimText(String(raw.level || "medium"), 24),
          route: missionTrimText(String(raw.route || "next-shift"), 64),
          channel: missionTrimText(String(raw.channel || "handoff"), 64),
          action: missionTrimText(String(raw.action || "queue-next-shift"), 64),
          policy_id: missionTrimText(String(raw.policy_id || "custom"), 48),
          status: missionTrimText(String(raw.status || "open"), 24),
          remaining_gap: Math.max(0, Number(raw.remaining_gap || 0)),
          coverage_pct: Math.max(0, Number(raw.coverage_pct || 0)),
          reason: missionTrimText(String(raw.reason || "execution"), 180),
          context: missionTrimText(String(raw.context || ""), 96),
          snooze_until: String(raw.snooze_until || ""),
        };
      }
      function listMissionHandoffRemediationCloseoutEscalationExecution() {
        try {
          const raw = JSON.parse(localStorage.getItem(MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_EXECUTION_STORAGE_KEY) || "[]");
          if (!Array.isArray(raw)) return [];
          return raw.map((item) => normalizeMissionHandoffRemediationCloseoutEscalationExecutionItem(item)).slice(0, MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_EXECUTION_LIMIT);
        } catch (_error) {
          return [];
        }
      }
      function storeMissionHandoffRemediationCloseoutEscalationExecution(items = []) {
        const normalized = (Array.isArray(items) ? items : [])
          .map((item) => normalizeMissionHandoffRemediationCloseoutEscalationExecutionItem(item))
          .slice(0, MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_EXECUTION_LIMIT);
        try { localStorage.setItem(MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_EXECUTION_STORAGE_KEY, JSON.stringify(normalized)); } catch (_error) {}
        return normalized;
      }
      function appendMissionHandoffRemediationCloseoutEscalationExecutionEntry(payload = {}) {
        const current = listMissionHandoffRemediationCloseoutEscalationExecution();
        current.unshift(normalizeMissionHandoffRemediationCloseoutEscalationExecutionItem(payload));
        return storeMissionHandoffRemediationCloseoutEscalationExecution(current);
      }
      function missionHandoffRemediationCloseoutEscalationExecutionActive(item = null, nowIso = null) {
        const source = item && typeof item === "object" ? item : {};
        const state = String(source.state || "acked").trim().toLowerCase();
        if (state === "resolved") return false;
        if (state !== "snoozed") return true;
        const untilMs = Date.parse(String(source.snooze_until || ""));
        if (!Number.isFinite(untilMs)) return true;
        const nowMs = nowIso ? Date.parse(String(nowIso || "")) : Date.now();
        if (!Number.isFinite(nowMs)) return true;
        return nowMs >= untilMs;
      }
      function buildMissionHandoffRemediationCloseoutEscalationExecutionState(escalation = null, executionItems = null) {
        const sourceEscalation = escalation && typeof escalation === "object"
          ? escalation
          : buildMissionHandoffRemediationCloseoutEscalation();
        const items = Array.isArray(executionItems)
          ? executionItems.map((item) => normalizeMissionHandoffRemediationCloseoutEscalationExecutionItem(item)).slice(0, MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_EXECUTION_LIMIT)
          : listMissionHandoffRemediationCloseoutEscalationExecution();
        const nowIso = new Date().toISOString();
        const activeItems = items.filter((item) => missionHandoffRemediationCloseoutEscalationExecutionActive(item, nowIso));
        let oldestAgeSec = null;
        let staleCount = 0;
        for (const item of activeItems) {
          const tsMs = Date.parse(String(item.ts || ""));
          if (!Number.isFinite(tsMs)) continue;
          const ageSec = Math.max(0, Math.floor((Date.now() - tsMs) / 1000));
          if (!Number.isFinite(ageSec)) continue;
          if (oldestAgeSec === null || ageSec > oldestAgeSec) oldestAgeSec = ageSec;
          if (ageSec >= MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_SLA_STALE_SEC) staleCount += 1;
        }
        let slaStatus = "idle";
        let slaStatusLabel = "IDLE";
        if (activeItems.length > 0) {
          if (staleCount > 0) {
            slaStatus = "stale";
            slaStatusLabel = "STALE";
          } else if (Number(oldestAgeSec || 0) >= Math.floor(MISSION_HANDOFF_REMEDIATION_CLOSEOUT_ESCALATION_SLA_STALE_SEC / 2)) {
            slaStatus = "warn";
            slaStatusLabel = "WARN";
          } else {
            slaStatus = "ok";
            slaStatusLabel = "OK";
          }
        }
        const counters = { acked: 0, snoozed: 0, resolved: 0 };
        for (const item of items) {
          const state = String(item && item.state || "acked");
          if (state === "snoozed") counters.snoozed += 1;
          else if (state === "resolved") counters.resolved += 1;
          else counters.acked += 1;
        }
        const latest = items[0] && typeof items[0] === "object" ? items[0] : null;
        const generatedAt = new Date().toISOString();
        const lines = [
          `Closeout escalation execution @ ${generatedAt}`,
          `level=${String(sourceEscalation.level || "n/a").toUpperCase()} route=${String(sourceEscalation.route || "n/a")} action=${String(sourceEscalation.action || "n/a")}`,
          `sla=${slaStatusLabel} active=${activeItems.length} stale=${staleCount} oldest=${oldestAgeSec !== null ? formatAgeShort(Number(oldestAgeSec)) : "—"}`,
          `counts acked=${counters.acked} snoozed=${counters.snoozed} resolved=${counters.resolved} remaining=${Number(sourceEscalation.remaining_gap || 0)}`,
        ];
        return {
          kind: "passengers.mission.handoff_remediation_closeout_escalation_execution.v1",
          generated_at: generatedAt,
          escalation: sourceEscalation,
          sla_status: slaStatus,
          sla_status_label: slaStatusLabel,
          active_count: activeItems.length,
          stale_count: staleCount,
          oldest_active_age_sec: oldestAgeSec,
          oldest_active_age_label: oldestAgeSec !== null ? formatAgeShort(Number(oldestAgeSec)) : "—",
          counters,
          latest,
          items: items.slice(0, 12),
          handoff_text: lines.join("\n"),
        };
      }
      function renderMissionHandoffRemediationCloseoutEscalationExecution(state = null) {
        const summaryNode = byId("sideHandoffRemediationEscalationExecutionSummary");
        const boardNode = byId("sideHandoffRemediationEscalationExecutionBoard");
        if (!summaryNode && !boardNode) return;
        const source = state && typeof state === "object"
          ? state
          : buildMissionHandoffRemediationCloseoutEscalationExecutionState();
        if (summaryNode) {
          summaryNode.textContent = `Escalation exec ${String(source.sla_status_label || "IDLE")} · active=${Number(source.active_count || 0)} · stale=${Number(source.stale_count || 0)} · oldest=${String(source.oldest_active_age_label || "—")}`;
        }
        if (!boardNode) return;
        const counters = source.counters && typeof source.counters === "object" ? source.counters : {};
        const latest = source.latest && typeof source.latest === "object" ? source.latest : null;
        const top = `acked=${Number(counters.acked || 0)} · snoozed=${Number(counters.snoozed || 0)} · resolved=${Number(counters.resolved || 0)} · level=${String(source.escalation && source.escalation.level || "n/a")}`;
        const latestText = latest
          ? `${formatSessionTime(String(latest.ts || ""))} · ${String(latest.state || "acked").toUpperCase()} · route=${String(latest.route || "n/a")} · ${missionTrimText(String(latest.reason || "n/a"), 96)}`
          : "—";
        const items = Array.isArray(source.items) ? source.items : [];
        const recentHtml = items.length > 0
          ? items.slice(0, 3).map((item, index) => {
              const title = `${index + 1}. ${String(item.state || "acked").toUpperCase()} · ${String(item.route || "n/a")}`;
              const body = `${formatSessionTime(String(item.ts || ""))} · remaining=${Number(item.remaining_gap || 0)} · ${missionTrimText(String(item.reason || "n/a"), 96)}`;
              return `<div class="sideHandoffTimelineRow"><div class="sideHandoffTimelineMeta"><span>${esc(title)}</span></div><div class="sideHandoffTimelineBody">${esc(body)}</div></div>`;
            }).join("")
          : '<span class="sideMiniEmpty">—</span>';
        boardNode.innerHTML = `<div class="sideHandoffMeta sideHandoffAdoption">${esc(top)}</div><div class="sideHandoffTimelineRow"><div class="sideHandoffTimelineBody">${esc(`latest: ${latestText}`)}</div></div>${recentHtml}`;
      }
      function renderMissionHandoffRemediationCloseoutEscalation(escalation = null) {
        const summaryNode = byId("sideHandoffRemediationEscalationSummary");
        const boardNode = byId("sideHandoffRemediationEscalationBoard");
        const source = escalation && typeof escalation === "object"
          ? escalation
          : buildMissionHandoffRemediationCloseoutEscalation();
        const executionState = buildMissionHandoffRemediationCloseoutEscalationExecutionState(source);
        renderMissionHandoffRemediationCloseoutEscalationExecution(executionState);
        if (!summaryNode && !boardNode) return;
        if (summaryNode) {
          summaryNode.textContent = `Escalation ${String(source.level || "none").toUpperCase()} · route=${String(source.route || "n/a")} · action=${String(source.action || "n/a")} · remaining=${Number(source.remaining_gap || 0)}`;
        }
        if (!boardNode) return;
        const top = `policy=${String(source.policy_id || "custom")} · channel=${String(source.channel || "n/a")} · flags=${Array.isArray(source.flags) && source.flags.length > 0 ? source.flags.join(",") : "none"}`;
        const body = `reason=${String(source.reason || "n/a")} · coverage=${Number(source.coverage_pct || 0)}% · closeouts=${Number(source.closeouts_total || 0)} (${Number(source.closeouts_single || 0)}/${Number(source.closeouts_batch || 0)})`;
        boardNode.innerHTML = `<div class="sideHandoffMeta sideHandoffAdoption">${esc(top)}</div><div class="sideHandoffTimelineRow"><div class="sideHandoffTimelineBody">${esc(missionTrimText(body, 180))}</div></div>`;
      }
      function renderMissionHandoffRemediationCloseoutGovernance(governance = null) {
        const summaryNode = byId("sideHandoffRemediationCloseoutSummary");
        const boardNode = byId("sideHandoffRemediationCloseoutBoard");
        const source = governance && typeof governance === "object"
          ? governance
          : buildMissionHandoffRemediationCloseoutGovernance();
        const escalation = buildMissionHandoffRemediationCloseoutEscalation(source);
        renderMissionHandoffRemediationCloseoutEscalation(escalation);
        if (!summaryNode && !boardNode) return;
        if (summaryNode) {
          summaryNode.textContent = `Closeout ${String(source.status_label || "OPEN")} · remaining=${Number(source.remaining_gap || 0)} · coverage=${Number(source.coverage_pct || 0)}% · total=${Number(source.closeouts_total || 0)}`;
        }
        if (!boardNode) return;
        const decisions = source.decision_counters && typeof source.decision_counters === "object"
          ? source.decision_counters
          : {};
        const top = `single=${Number(source.closeouts_single || 0)} · batch=${Number(source.closeouts_batch || 0)} · ack=${Number(decisions.ack || 0)} · snooze=${Number(decisions.snooze || 0)} · profile=${Number(decisions["profile-check"] || 0)}`;
        const recent = Array.isArray(source.recent_closeouts) ? source.recent_closeouts : [];
        const recentHtml = recent.length > 0
          ? recent.slice(0, 3).map((item, index) => {
              const stamp = formatSessionTime(String(item && item.ts || ""));
              const title = `${index + 1}. ${String(item && item.decision || "profile-check").toUpperCase()} · ${String(item && item.profile_id || "standard")}`;
              const body = `${stamp} · ${String(item && item.source || "backlog-closeout")} · ${missionTrimText(String(item && item.reason || "n/a"), 96)}`;
              return `<div class="sideHandoffTimelineRow"><div class="sideHandoffTimelineMeta"><span>${esc(title)}</span></div><div class="sideHandoffTimelineBody">${esc(body)}</div></div>`;
            }).join("")
          : '<span class="sideMiniEmpty">—</span>';
        boardNode.innerHTML = `<div class="sideHandoffMeta sideHandoffAdoption">${esc(top)}</div>${recentHtml}`;
      }
      function buildMissionHandoffRemediationDecisionCoverage(plan = null, ledgerItems = null) {
        const backlog = buildMissionHandoffRemediationDecisionBacklog(plan, ledgerItems);
        return {
          planned: Number(backlog.planned || 0),
          logged: Number(backlog.logged || 0),
          coverage_pct: Number(backlog.coverage_pct || 0),
          label: `${Number(backlog.coverage_pct || 0)}%`,
          missing: Array.isArray(backlog.missing_labels) ? backlog.missing_labels : [],
        };
      }
      function renderMissionHandoffRemediationDecisionCoverage(plan = null, ledgerItems = null) {
        const node = byId("sideHandoffRemediationDecisionCoverage");
        if (!node) return;
        const coverage = buildMissionHandoffRemediationDecisionCoverage(plan, ledgerItems);
        const missingText = coverage.missing.length > 0 ? ` · missing=${coverage.missing.join(", ")}` : "";
        node.textContent = `Decision coverage: ${coverage.logged}/${coverage.planned} (${coverage.label})${missingText}`;
      }
      function renderMissionHandoffRemediationDecisionLedger(items = null) {
        const node = byId("sideHandoffRemediationDecisionLedger");
        if (!node) return;
        const list = Array.isArray(items) ? items : listMissionHandoffRemediationDecisionLedger();
        if (list.length <= 0) {
          node.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        node.innerHTML = list.slice(0, 4)
          .map((item, index) => {
            const stamp = formatSessionTime(String(item.ts || ""));
            const title = `${index + 1}. ${String(item.decision || "profile-check").toUpperCase()} · ${String(item.profile_id || "standard")}`;
            const body = `${stamp} · ${String(item.source || "manual")} · ${missionTrimText(String(item.reason || "n/a"), 96)}`;
            return (
              `<div class="sideHandoffTimelineRow">`
              + `<div class="sideHandoffTimelineMeta"><span>${esc(title)}</span></div>`
              + `<div class="sideHandoffTimelineBody">${esc(body)}</div>`
              + `</div>`
            );
          })
          .join("");
      }
      function renderMissionHandoffRemediationDecisionBacklog(backlog = null) {
        const summaryNode = byId("sideHandoffRemediationDecisionBacklogSummary");
        const listNode = byId("sideHandoffRemediationDecisionBacklog");
        if (!summaryNode && !listNode) return;
        const source = backlog && typeof backlog === "object"
          ? backlog
          : buildMissionHandoffRemediationDecisionBacklog();
        const missingItems = Array.isArray(source.missing_items) ? source.missing_items : [];
        if (summaryNode) {
          if (missingItems.length <= 0) {
            summaryNode.textContent = `Decision backlog: clean · coverage=${Number(source.coverage_pct || 100)}%`;
          } else {
            const first = missingItems[0] && typeof missingItems[0] === "object" ? missingItems[0] : {};
            const batchLimit = Math.max(1, Number(MISSION_HANDOFF_REMEDIATION_DECISION_BACKLOG_CLOSEOUT_LIMIT || 3));
            summaryNode.textContent = `Decision backlog: missing=${missingItems.length}/${Number(source.planned || 0)} · coverage=${Number(source.coverage_pct || 0)}% · next=${String(first.action || "profile-check")}:${String(first.profile_id || "standard")} · batch=${batchLimit}`;
          }
        }
        if (!listNode) return;
        if (missingItems.length <= 0) {
          listNode.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        listNode.innerHTML = missingItems.slice(0, 4)
          .map((item, index) => {
            const title = `${index + 1}. ${String(item.action || "profile-check").toUpperCase()} · ${String(item.profile_id || "standard")}`;
            const body = `active=${Number(item.active_count || 0)} · oldest=${String(item.oldest_age_label || "—")} · ${missionTrimText(String(item.reason || "n/a"), 96)}`;
            const actions = [
              `<button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="backlog-item-ack-${index}">ACK</button>`,
              `<button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="backlog-item-snooze-${index}">Snooze</button>`,
              `<button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="backlog-item-profile-check-${index}">Profile check</button>`,
            ].join("");
            return (
              `<div class="sideHandoffTimelineRow">`
              + `<div class="sideHandoffTimelineMeta"><span>${esc(title)}</span></div>`
              + `<div class="sideHandoffTimelineBody">${esc(body)}</div>`
              + `<div class="sideHandoffTools">${actions}</div>`
              + `</div>`
            );
          })
          .join("");
      }


      function renderMissionHandoffRemediationIncidents(items = null) {
        const list = Array.isArray(items) ? items : listMissionHandoffRemediationIncidents();
        const summaryNode = byId("sideHandoffRemediationIncidentSummary");
        const feedNode = byId("sideHandoffRemediationIncidentFeed");
        const summary = buildMissionHandoffRemediationIncidentSlaSummary(list);
        if (summaryNode) summaryNode.textContent = `Incidents: active=${summary.active_count} · snoozed=${summary.snoozed_count} · acked=${summary.acked_count}`;
        renderMissionHandoffRemediationIncidentSla(summary);
        renderMissionHandoffRemediationIncidentDigest(list, summary);
        renderMissionHandoffRemediationActionPlan(list, summary);
        if (!feedNode) return;
        if (list.length === 0) {
          feedNode.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        feedNode.innerHTML = list.slice(0, 4)
          .map((item) => {
            const stamp = formatSessionTime(item.ts);
            const state = String(item.state || "open").toUpperCase();
            const body = `${item.message} · ${item.context || "context=n/a"}`;
            return (
              `<div class="sideHandoffTimelineRow">`
              + `<div class="sideHandoffTimelineMeta"><span>${esc(stamp)}</span><span>${esc(state)}</span></div>`
              + `<div class="sideHandoffTimelineBody">${esc(missionTrimText(body, 120))}</div>`
              + `</div>`
            );
          })
          .join("");
      }
      function runMissionHandoffRemediationIncidentAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        if (!mode) return false;
        const incidents = listMissionHandoffRemediationIncidents();
        const active = incidents.find((item) => missionHandoffRemediationIncidentActive(item));
        const statusNode = byId("sideMissionStatus");
        if (!active) {
          if (statusNode) statusNode.textContent = "Governance incidents: активних немає";
          return false;
        }
        const nowIso = new Date().toISOString();
        const targetIndex = incidents.findIndex((item) => item.id === active.id);
        if (targetIndex < 0) return false;
        const current = incidents[targetIndex];
        if (mode === "ack") {
          incidents[targetIndex] = {
            ...current,
            state: "acked",
            ack_ts: nowIso,
          };
          const stored = storeMissionHandoffRemediationIncidents(incidents);
          appendMissionHandoffRemediationDecision({
            ts: nowIso,
            fingerprint: String(current.fingerprint || ""),
            profile_id: String(current.profile_id || "standard"),
            context: String(current.context || ""),
            decision: "ack",
            reason: "incident action",
            source: "incident-action",
          });
          renderMissionHandoffRemediationIncidents(stored);
          appendMissionHandoffTimelineEvent("remediation_incident_ack", {
            context: buildMissionContextLabel(),
            text: `incident=${current.id} profile=${current.profile_id}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Governance incident ACK: ${current.profile_label}`;
          return true;
        }
        if (mode === "snooze") {
          const raw = window.prompt("Snooze minutes:", String(MISSION_HANDOFF_REMEDIATION_INCIDENT_SNOOZE_MIN));
          const mins = Math.max(1, Math.min(180, Number(raw || MISSION_HANDOFF_REMEDIATION_INCIDENT_SNOOZE_MIN) || MISSION_HANDOFF_REMEDIATION_INCIDENT_SNOOZE_MIN));
          const untilIso = new Date(Date.now() + mins * 60 * 1000).toISOString();
          incidents[targetIndex] = {
            ...current,
            state: "snoozed",
            snooze_until: untilIso,
          };
          const stored = storeMissionHandoffRemediationIncidents(incidents);
          appendMissionHandoffRemediationDecision({
            ts: nowIso,
            fingerprint: String(current.fingerprint || ""),
            profile_id: String(current.profile_id || "standard"),
            context: String(current.context || ""),
            decision: "snooze",
            reason: `incident action mins=${mins}`,
            source: "incident-action",
          });
          renderMissionHandoffRemediationIncidents(stored);
          appendMissionHandoffTimelineEvent("remediation_incident_snooze", {
            context: buildMissionContextLabel(),
            text: `incident=${current.id} mins=${mins}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Governance incident snoozed: ${mins}m`;
          return true;
        }
        return false;
      }
      function runMissionHandoffRemediationIncidentHistoryAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        if (!mode) return false;
        const statusNode = byId("sideMissionStatus");
        const incidents = listMissionHandoffRemediationIncidents();
        const payload = {
          kind: "passengers.mission.handoff_remediation_incidents.v1",
          generated_at: new Date().toISOString(),
          items: incidents.slice(0, MISSION_HANDOFF_REMEDIATION_INCIDENTS_LIMIT),
        };
        if (mode === "show") {
          window.prompt("Mission remediation incidents (JSON):", JSON.stringify(payload, null, 2));
          appendMissionHandoffTimelineEvent("remediation_incident_journal_show", {
            context: buildMissionContextLabel(),
            text: `items=${payload.items.length}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Incident journal: показано ${payload.items.length}`;
          return true;
        }
        if (mode === "export") {
          copyTextWithFallback(JSON.stringify(payload, null, 2), "Скопіюйте remediation incidents JSON:", "Incident journal: скопійовано", "Incident journal: у prompt");
          appendMissionHandoffTimelineEvent("remediation_incident_journal_export", {
            context: buildMissionContextLabel(),
            text: `items=${payload.items.length}`,
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = `Incident journal: експортовано ${payload.items.length}`;
          return true;
        }
        if (mode === "clear") {
          const confirmed = window.confirm("Очистити governance incident journal?");
          if (!confirmed) return false;
          storeMissionHandoffRemediationIncidents([]);
          renderMissionHandoffRemediationIncidents([]);
          appendMissionHandoffTimelineEvent("remediation_incident_journal_clear", {
            context: buildMissionContextLabel(),
            text: "items=0",
          });
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Incident journal: очищено";
          return true;
        }
        return false;
      }
      function buildMissionHandoffRemediationTimelineSummary(items = null) {
        const list = Array.isArray(items) ? items : listMissionHandoffRemediationTimeline();
        if (list.length === 0) return "Timeline: no remediation cycles yet";
        const considered = list.slice(0, 12);
        const applied = considered.filter((item) => item.applied).length;
        const overrides = considered.filter((item) => item.override_after_remediation).length;
        const ready = considered.filter((item) => item.ready_after).length;
        return `Timeline: ${considered.length} cycles · applied=${applied} · ready=${ready} · override=${overrides}`;
      }
      function renderMissionHandoffRemediationTimelinePreview(items = null) {
        const node = byId("sideHandoffRemediationTimeline");
        if (!node) return;
        const list = Array.isArray(items) ? items : listMissionHandoffRemediationTimeline();
        if (list.length === 0) {
          node.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        node.innerHTML = list.slice(0, 4)
          .map((item) => {
            const stamp = formatSessionTime(item.ts);
            const right = `${String(item.action || "unknown")} · ${item.applied ? "ok" : "skip"}`;
            const body = `${String(item.status_label || "NOT-READY")} ${Number(item.passed || 0)}/${Number(item.total || 0)} · ${item.fix_label || "manual"}`;
            return (
              `<div class="sideHandoffTimelineRow">`
              + `<div class="sideHandoffTimelineMeta"><span>${esc(stamp)}</span><span>${esc(right)}</span></div>`
              + `<div class="sideHandoffTimelineBody">${esc(missionTrimText(body, 120))}</div>`
              + `</div>`
            );
          })
          .join("");
      }
      function runMissionHandoffRemediationHistoryAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        const statusNode = byId("sideMissionStatus");
        if (mode === "show") {
          const items = listMissionHandoffRemediationTimeline();
          if (items.length === 0) {
            if (statusNode) statusNode.textContent = "Remediation timeline: журнал порожній";
            return false;
          }
          window.prompt("Mission remediation timeline (JSON):", JSON.stringify({ kind: "passengers.mission.handoff_remediation_timeline.v1", items: items.slice(0, 24) }, null, 2));
          if (statusNode) statusNode.textContent = `Remediation timeline: показано ${Math.min(24, items.length)}`;
          return true;
        }
        if (mode === "export") {
          const items = listMissionHandoffRemediationTimeline();
          const payload = JSON.stringify({ kind: "passengers.mission.handoff_remediation_timeline.v1", items: items.slice(0, 24) }, null, 2);
          copyTextWithFallback(payload, "Скопіюйте remediation timeline JSON:", "Remediation timeline: скопійовано", "Remediation timeline: у prompt");
          if (statusNode) statusNode.textContent = `Remediation timeline: експортовано ${Math.min(24, items.length)}`;
          return true;
        }
        if (mode === "clear") {
          storeMissionHandoffRemediationTimeline([]);
          renderMissionHandoffRemediationTimelinePreview([]);
          renderMissionHandoffRemediationSummary();
          if (statusNode) statusNode.textContent = "Remediation timeline: очищено";
          return true;
        }
        return false;
      }
      function missionSecondsSinceIso(fromIso, toIso = null) {
        const fromMs = Date.parse(String(fromIso || ""));
        if (!Number.isFinite(fromMs)) return null;
        const toMs = toIso ? Date.parse(String(toIso || "")) : Date.now();
        if (!Number.isFinite(toMs) || toMs < fromMs) return null;
        return Math.max(0, Math.round((toMs - fromMs) / 1000));
      }
      function missionP95Seconds(values = []) {
        const list = Array.isArray(values)
          ? values.map((item) => Number(item)).filter((item) => Number.isFinite(item) && item >= 0).sort((a, b) => a - b)
          : [];
        if (list.length === 0) return 0;
        const index = Math.min(list.length - 1, Math.max(0, Math.ceil(0.95 * list.length) - 1));
        return Math.round(Number(list[index] || 0));
      }
      function updateMissionHandoffRemediationMetrics(qualityState = null, options = {}) {
        const quality = qualityState && typeof qualityState === "object" ? qualityState : buildMissionHandoffQualityState();
        const sourceOptions = options && typeof options === "object" ? options : {};
        const nowIso = String(sourceOptions.ts || new Date().toISOString());
        const event = String(sourceOptions.event || "check").trim().toLowerCase();
        const action = String(sourceOptions.action || "").trim().toLowerCase();
        const applied = !!sourceOptions.applied;
        const sourceMetrics = sourceOptions.metrics && typeof sourceOptions.metrics === "object"
          ? sourceOptions.metrics
          : loadMissionHandoffRemediationMetrics();
        const metrics = normalizeMissionHandoffRemediationMetrics(sourceMetrics);
        if (!quality.ready && !metrics.cycle_started_at) metrics.cycle_started_at = nowIso;
        if (action) {
          metrics.last_action = action;
          metrics.last_action_ts = nowIso;
          if (applied) {
            metrics.applied += 1;
            if (!quality.ready) metrics.cycle_has_remediation = true;
          } else {
            metrics.skipped += 1;
          }
        }
        if (event === "override" && metrics.cycle_has_remediation) {
          metrics.override_after_remediation += 1;
        }
        if (quality.ready && metrics.cycle_started_at) {
          const sec = missionSecondsSinceIso(metrics.cycle_started_at, nowIso);
          if (Number.isFinite(sec)) {
            metrics.time_to_ready_sec_samples.push(sec);
            metrics.time_to_ready_sec_samples = metrics.time_to_ready_sec_samples.slice(-MISSION_HANDOFF_REMEDIATION_TTR_LIMIT);
            metrics.ready_cycles += 1;
          }
          metrics.cycle_started_at = "";
          metrics.cycle_has_remediation = false;
        }
        metrics.last_status = String(quality.status_label || (quality.ready ? "READY" : "NOT-READY"));
        return storeMissionHandoffRemediationMetrics(metrics);
      }
      function renderMissionHandoffRemediationSummary(metrics = null, qualityState = null) {
        const node = byId("sideHandoffRemediationSummary");
        if (!node) return;
        const sourceMetrics = normalizeMissionHandoffRemediationMetrics(metrics || loadMissionHandoffRemediationMetrics());
        const sourceQuality = qualityState && typeof qualityState === "object" ? qualityState : buildMissionHandoffQualityState();
        const timeline = listMissionHandoffRemediationTimeline();
        const samples = Array.isArray(sourceMetrics.time_to_ready_sec_samples) ? sourceMetrics.time_to_ready_sec_samples : [];
        const avg = samples.length > 0
          ? Math.round(samples.reduce((total, item) => total + Number(item || 0), 0) / samples.length)
          : 0;
        const p95 = missionP95Seconds(samples);
        const openSec = !sourceQuality.ready && sourceMetrics.cycle_started_at
          ? missionSecondsSinceIso(sourceMetrics.cycle_started_at)
          : null;
        const openLabel = Number.isFinite(openSec) ? `${openSec}s` : "—";
        node.textContent = `Remediation KPI: applied=${sourceMetrics.applied} · skipped=${sourceMetrics.skipped} · override=${sourceMetrics.override_after_remediation} · TTR avg/p95=${avg}s/${p95}s · open=${openLabel}`;
        const timelineNode = byId("sideHandoffRemediationTimelineMeta");
        if (timelineNode) timelineNode.textContent = buildMissionHandoffRemediationTimelineSummary(timeline);
        const governance = buildMissionHandoffRemediationGovernanceState(sourceMetrics, timeline);
        renderMissionHandoffRemediationGovernance(governance);
        const incidentState = ensureMissionHandoffRemediationGovernanceIncident(governance);
        renderMissionHandoffRemediationIncidents(incidentState.incidents);
        if (incidentState.created && incidentState.incident) {
          appendMissionHandoffTimelineEvent("remediation_incident_open", {
            context: buildMissionContextLabel(),
            text: `incident=${incidentState.incident.id} profile=${incidentState.incident.profile_id} status=${governance.status_label}`,
          });
          renderMissionHandoffTimeline();
        }
      }
      function appendMissionHandoffNextActionsToNote() {
        const input = byId("sideHandoffInput");
        if (!(input instanceof HTMLTextAreaElement)) return false;
        const base = String(input.value || "").trimEnd();
        if (base.includes("Next actions:")) return false;
        const snapshot = buildSidebarNavAdoptionSnapshot();
        const nextActions = Array.isArray(snapshot.next_actions)
          ? snapshot.next_actions.map((item) => missionTrimText(String(item || "").trim(), 96)).filter(Boolean).slice(0, 3)
          : [];
        const lines = nextActions.length > 0
          ? nextActions.map((item, index) => `${index + 1}) ${item}`)
          : ["1) Зафіксувати ризики по активному інциденту.", "2) Перевірити alerts/incidents/audit перед передачею зміни."];
        const block = `Next actions:
${lines.join("\n")}`;
        const separator = base ? "\n" : "";
        input.value = missionTrimText(`${base}${separator}${block}`, MISSION_HANDOFF_MAX_LENGTH);
        input.dataset.dirty = "1";
        renderMissionHandoffNotes();
        return true;
      }
      function appendMissionHandoffExpansionLine() {
        const input = byId("sideHandoffInput");
        if (!(input instanceof HTMLTextAreaElement)) return false;
        const contextLabel = buildMissionContextLabel() || "context=n/a";
        const stamp = new Date().toISOString().slice(11, 16);
        const line = `[${stamp}] remediation: ${contextLabel} · перевірити handoff quality блок перед save`;
        const base = String(input.value || "").trimEnd();
        const separator = base ? "\n" : "";
        input.value = missionTrimText(`${base}${separator}${line}`, MISSION_HANDOFF_MAX_LENGTH);
        input.dataset.dirty = "1";
        renderMissionHandoffNotes();
        return true;
      }
      function buildMissionHandoffQualityState(options = {}) {
        const source = options && typeof options === "object" ? options : {};
        const inputText = String(source.input_text || "").trim();
        const fallbackInput = byId("sideHandoffInput");
        const noteText = inputText || (fallbackInput instanceof HTMLTextAreaElement ? String(fallbackInput.value || "").trim() : "");
        const snapshot = source.snapshot && typeof source.snapshot === "object"
          ? source.snapshot
          : buildSidebarNavAdoptionSnapshot();
        const composerDraft = source.composer && typeof source.composer === "object"
          ? source.composer
          : loadMissionHandoffComposerDraft();
        const profileResolved = source.profile && typeof source.profile === "object"
          ? source.profile
          : resolveMissionHandoffQualityProfile();
        const profile = profileResolved.profile && typeof profileResolved.profile === "object"
          ? profileResolved.profile
          : missionHandoffQualityProfileById(profileResolved.profile_id);
        const contextLabel = String(source.context || buildMissionContextLabel() || "").trim();
        const scorecard = snapshot.scorecard && typeof snapshot.scorecard === "object" ? snapshot.scorecard : {};
        const trend = snapshot.trend && typeof snapshot.trend === "object" ? snapshot.trend : {};
        const trendCoach = snapshot.trend_coach && typeof snapshot.trend_coach === "object" ? snapshot.trend_coach : {};
        const nextActions = Array.isArray(snapshot.next_actions) ? snapshot.next_actions : [];
        const draftText = composerDraft ? String(composerDraft.text || "").trim() : "";
        const resemblesTemplate = noteText.includes("Scorecard:") && noteText.includes("Trend:") && noteText.includes("Next actions:");
        const minCoachChars = Math.max(4, Number(profile && profile.coach_min_chars || 16));
        const minNextActions = Math.max(0, Number(profile && profile.min_next_actions || 2));
        const minNoteChars = Math.max(80, Number(profile && profile.note_min_chars || 140));
        const requiresContext = !!(profile && profile.require_context);
        const requiresComposerMatch = !!(profile && profile.require_composer_match);
        const criticalSet = new Set(Array.isArray(profile && profile.critical_checks) ? profile.critical_checks.map((item) => String(item || "").trim().toLowerCase()) : []);
        const isCritical = (checkId) => criticalSet.has(String(checkId || "").trim().toLowerCase());
        const composerOk = !!noteText && (requiresComposerMatch
          ? (!!draftText ? noteText === draftText || resemblesTemplate : resemblesTemplate)
          : (resemblesTemplate || noteText.length >= minNoteChars));
        const checks = [
          { id: "context", label: "Контекст", critical: isCritical("context"), ok: requiresContext ? !!contextLabel : true, detail: contextLabel || "немає прив'язки до incident" },
          { id: "scorecard", label: "Scorecard", critical: isCritical("scorecard"), ok: Number(scorecard.total || 0) > 0, detail: `${Number(scorecard.passed || 0)}/${Number(scorecard.total || 0)}` },
          { id: "trend", label: "Trend", critical: isCritical("trend"), ok: !!(trend && trend.latest), detail: String(trend && trend.label || "NO-DATA") },
          { id: "coach", label: "Coach cue", critical: isCritical("coach"), ok: missionTrimText(String(trendCoach.text || "").trim(), 180).length >= minCoachChars, detail: missionTrimText(String(trendCoach.text || "—"), 72) },
          { id: "next_actions", label: "Next actions", critical: isCritical("next_actions"), ok: nextActions.length >= minNextActions, detail: `${nextActions.length}/${minNextActions}` },
          { id: "note_size", label: "Обсяг note", critical: isCritical("note_size"), ok: noteText.length >= minNoteChars, detail: `${noteText.length}/${minNoteChars}` },
          { id: "composer", label: "Composer apply", critical: isCritical("composer"), ok: composerOk, detail: draftText ? "draft prepared" : "draft missing" },
        ];
        const passed = checks.filter((item) => item.ok).length;
        const total = checks.length;
        const failedChecks = checks.filter((item) => !item.ok);
        const criticalFailed = checks.filter((item) => item.critical && !item.ok);
        const ready = criticalFailed.length === 0;
        const remediationByCheckId = {
          context: { action_id: "context", label: "Додати контекст", priority: 10, detail: "Додайте active incident context у handoff note." },
          composer: { action_id: "compose-apply", label: "Compose + Apply", priority: 20, detail: "Синхронізуйте note з composer-шаблоном." },
          coach: { action_id: "compose-apply", label: "Compose + Apply", priority: 30, detail: "Оновіть coach cue через composer-шаблон." },
          next_actions: { action_id: "append-next-actions", label: "Додати next actions", priority: 40, detail: "Додайте мінімум required next-actions у note." },
          note_size: { action_id: "expand-note", label: "Розширити note", priority: 50, detail: "Додайте деталізацію, щоб пройти поріг note-size." },
          scorecard: { action_id: "compose", label: "Rebuild composer", priority: 60, detail: "Згенеруйте свіжий composer-драфт для scorecard/trend." },
          trend: { action_id: "compose", label: "Rebuild composer", priority: 60, detail: "Оновіть trend частину через composer." },
        };
        const remediationMap = new Map();
        for (const check of failedChecks) {
          const base = remediationByCheckId[String(check.id || "").trim().toLowerCase()] || { action_id: "compose", label: "Rebuild composer", priority: 90, detail: "Оновіть handoff через composer." };
          const key = String(base.action_id || "").trim().toLowerCase();
          if (!key) continue;
          if (!remediationMap.has(key)) {
            remediationMap.set(key, {
              action_id: key,
              label: String(base.label || key),
              detail: String(base.detail || ""),
              priority: Number(base.priority || 99),
              check_ids: [String(check.id || "")],
              check_labels: [String(check.label || "")],
            });
            continue;
          }
          const current = remediationMap.get(key);
          current.check_ids.push(String(check.id || ""));
          current.check_labels.push(String(check.label || ""));
          current.priority = Math.min(Number(current.priority || 99), Number(base.priority || 99));
        }
        const remediationActions = Array.from(remediationMap.values()).sort((left, right) => Number(left.priority || 99) - Number(right.priority || 99));
        const recommendedAction = remediationActions[0] || null;
        const blockReason = criticalFailed.map((item) => String(item.label || "")).filter(Boolean).join(", ");
        const explainText = ready
          ? `Save дозволено: всі critical checks пройдені (${String(profileResolved.profile_id || "strict")}).`
          : `Save заблоковано policy ${String(profileResolved.profile_id || "strict")}: ${blockReason || "critical checks missing"}.${recommendedAction ? ` Рекомендовано: ${recommendedAction.label}.` : ""}`;
        return {
          ready,
          status_label: ready ? "READY" : "NOT-READY",
          passed,
          total,
          checks,
          failed_checks: failedChecks,
          critical_failed: criticalFailed,
          missing_labels: criticalFailed.map((item) => item.label),
          remediation_actions: remediationActions,
          recommended_action: recommendedAction,
          explain_text: explainText,
          block_reason: blockReason,
          note_length: noteText.length,
          context: contextLabel,
          profile_id: String(profileResolved.profile_id || "strict"),
          profile_label: String(profileResolved.profile_label || (profile && profile.label) || "Strict"),
          profile_mode: String(profileResolved.mode || "override"),
        };
      }
      function renderMissionHandoffQualityRemediationControls(state = null) {
        const source = state && typeof state === "object" ? state : buildMissionHandoffQualityState();
        const available = new Set(Array.isArray(source.remediation_actions)
          ? source.remediation_actions.map((item) => String(item.action_id || "").trim().toLowerCase()).filter(Boolean)
          : []);
        const recommended = source.recommended_action && typeof source.recommended_action === "object"
          ? String(source.recommended_action.action_id || "").trim().toLowerCase()
          : "";
        const buttons = Array.from(document.querySelectorAll("button[data-handoff-quality-remedy]"));
        for (const button of buttons) {
          if (!(button instanceof HTMLButtonElement)) continue;
          const actionId = String(button.getAttribute("data-handoff-quality-remedy") || "").trim().toLowerCase();
          const isRecommended = actionId === "recommended";
          const isKnown = actionId ? available.has(actionId) : false;
          if (isRecommended) {
            button.disabled = !!source.ready || !recommended;
            button.classList.toggle("active", !source.ready && !!recommended);
            button.setAttribute("aria-pressed", !source.ready && !!recommended ? "true" : "false");
            button.textContent = recommended && source.recommended_action
              ? `Fix: ${String(source.recommended_action.label || "recommended")}`
              : "Fix: n/a";
            continue;
          }
          button.disabled = !!source.ready || (!isKnown && actionId !== "compose-apply" && actionId !== "context");
          button.classList.toggle("active", !!recommended && actionId === recommended);
          button.setAttribute("aria-pressed", !!recommended && actionId === recommended ? "true" : "false");
        }
        const explainNode = byId("sideHandoffQualityExplain");
        if (explainNode) {
          const explain = missionTrimText(String(source.explain_text || ""), 320);
          explainNode.textContent = explain || "Quality explain: n/a";
        }
      }
      function renderMissionHandoffQuality(state = null) {
        const node = byId("sideHandoffQuality");
        if (!node) return;
        const source = state && typeof state === "object" ? state : buildMissionHandoffQualityState();
        renderMissionHandoffQualityProfileControls(source.profile_id);
        const statusTone = source.ready ? "done" : "next";
        const missingCount = Array.isArray(source.critical_failed) ? source.critical_failed.length : 0;
        const badges = Array.isArray(source.checks)
          ? source.checks.map((item) => {
            const tone = item.ok ? "done" : (item.critical ? "next" : "current");
            const stateLabel = item.ok ? "OK" : "MISS";
            return `<span class="sideChecklistBadge ${tone}">${esc(`${stateLabel} ${item.label}`)}</span>`;
          }).join(" ")
          : "";
        const missText = missingCount > 0
          ? `missing: ${source.missing_labels.join(", ")}`
          : "all critical checks passed";
        node.innerHTML = (
          `<div class="sideChecklistRow">`
          + `<span class="sideChecklistBadge ${statusTone}">${esc(`Quality ${String(source.status_label || "NOT-READY")}`)}</span>`
          + `<span class="sideChecklistBadge">${esc(`${Number(source.passed || 0)}/${Number(source.total || 0)}`)}</span>`
          + `<span class="sideChecklistBadge">${esc(`policy ${String(source.profile_label || "Strict")}`)}</span>`
          + `<span class="sideChecklistBadge">${esc(`note ${Number(source.note_length || 0)} chars`)}</span>`
          + `</div>`
          + `<div class="sideHandoffQualityText">${esc(missText)}</div>`
          + `<div class="sideHandoffQualityBadges">${badges}</div>`
        );
        renderMissionHandoffQualityRemediationControls(source);
        renderMissionHandoffRemediationSummary(null, source);
      }
      function runMissionHandoffQualityRemediationAction(action) {
        const modeRaw = String(action || "").trim().toLowerCase();
        if (!modeRaw) return false;
        const before = buildMissionHandoffQualityState();
        let mode = modeRaw;
        if (mode === "recommended") {
          mode = before.recommended_action && typeof before.recommended_action === "object"
            ? String(before.recommended_action.action_id || "").trim().toLowerCase()
            : "";
        }
        if (!mode) {
          const metricsIdle = updateMissionHandoffRemediationMetrics(before, { event: "check" });
          renderMissionHandoffQuality(before);
          renderMissionHandoffRemediationSummary(metricsIdle, before);
          return false;
        }
        let applied = false;
        if (mode === "context") {
          applied = runMissionHandoffAction("context");
        } else if (mode === "compose") {
          applied = runMissionHandoffComposerAction("compose");
        } else if (mode === "compose-apply") {
          applied = runMissionHandoffComposerAction("apply");
          if (!applied) {
            runMissionHandoffComposerAction("compose");
            applied = runMissionHandoffComposerAction("apply");
          }
        } else if (mode === "append-next-actions") {
          applied = appendMissionHandoffNextActionsToNote();
        } else if (mode === "expand-note") {
          applied = appendMissionHandoffExpansionLine();
        }
        const after = buildMissionHandoffQualityState();
        const metrics = updateMissionHandoffRemediationMetrics(after, {
          event: "remediate",
          action: mode,
          applied,
        });
        appendMissionHandoffRemediationTimelineEvent({
          ts: new Date().toISOString(),
          context: after.context || buildMissionContextLabel(),
          action: mode,
          applied,
          status_label: String(after.status_label || "NOT-READY"),
          profile_id: String(after.profile_id || "strict"),
          passed: Number(after.passed || 0),
          total: Number(after.total || 0),
          block_reason: String(after.block_reason || ""),
          fix_label: after.recommended_action && typeof after.recommended_action === "object"
            ? String(after.recommended_action.label || "")
            : "manual",
          cycle_open_sec: missionSecondsSinceIso(metrics.cycle_started_at || ""),
          ready_after: !!after.ready,
          override_after_remediation: false,
        });
        renderMissionHandoffQuality(after);
        renderMissionHandoffRemediationSummary(metrics, after);
        renderMissionHandoffRemediationTimelinePreview();
        appendMissionHandoffTimelineEvent("quality_remediate", {
          context: after.context || buildMissionContextLabel(),
          text: `${mode} ${applied ? "ok" : "skip"} -> ${String(after.status_label || "NOT-READY")} ${Number(after.passed || 0)}/${Number(after.total || 0)} policy=${after.profile_id}`,
        });
        renderMissionHandoffTimeline();
        const statusNode = byId("sideMissionStatus");
        if (statusNode) {
          statusNode.textContent = after.ready
            ? `Handoff remediation: READY ${after.passed}/${after.total} (${after.profile_label})`
            : `Handoff remediation: ${mode} ${applied ? "applied" : "skipped"} · ${after.block_reason || "critical checks missing"}`;
        }
        return applied;
      }
      function runMissionHandoffQualityAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        if (mode !== "check") return false;
        const statusNode = byId("sideMissionStatus");
        const quality = buildMissionHandoffQualityState();
        const metrics = updateMissionHandoffRemediationMetrics(quality, { event: "check" });
        renderMissionHandoffQuality(quality);
        renderMissionHandoffRemediationSummary(metrics, quality);
        appendMissionHandoffTimelineEvent("quality_check", {
          context: quality.context || buildMissionContextLabel(),
          text: `${String(quality.status_label || "NOT-READY")} ${Number(quality.passed || 0)}/${Number(quality.total || 0)} policy=${quality.profile_id}`,
        });
        renderMissionHandoffTimeline();
        if (statusNode) {
          statusNode.textContent = quality.ready
            ? `Handoff quality: READY ${quality.passed}/${quality.total} (${quality.profile_label})`
            : `Handoff quality: NOT-READY (${quality.missing_labels.join(", ")}) · ${quality.profile_label} · fix=${quality.recommended_action ? quality.recommended_action.label : "manual"}`;
        }
        return quality.ready;
      }
      function renderMissionHandoffNotes() {
        const input = byId("sideHandoffInput");
        const metaNode = byId("sideHandoffMeta");
        const entry = loadMissionHandoffNote();
        if (input) {
          input.maxLength = MISSION_HANDOFF_MAX_LENGTH;
          const dirty = String(input.dataset.dirty || "") === "1";
          if (!dirty && document.activeElement !== input) {
            input.value = entry ? String(entry.text || "") : "";
          }
        }
        if (!metaNode) return;
        const valueLength = input ? String(input.value || "").length : (entry ? String(entry.text || "").length : 0);
        if (!entry) {
          metaNode.textContent = `Нотатка зміни: порожньо · ${valueLength}/${MISSION_HANDOFF_MAX_LENGTH}`;
          renderMissionHandoffQuality();
          return;
        }
        const stamp = formatSessionTime(entry.ts);
        const ctx = String(entry.context || "").trim();
        metaNode.textContent = ctx
          ? `Оновлено ${stamp} · ${valueLength}/${MISSION_HANDOFF_MAX_LENGTH} · ${ctx}`
          : `Оновлено ${stamp} · ${valueLength}/${MISSION_HANDOFF_MAX_LENGTH}`;
        renderMissionHandoffQuality();
      }
      function runMissionHandoffAction(action) {
        const mode = String(action || "").trim().toLowerCase();
        if (!mode) return false;
        const input = byId("sideHandoffInput");
        const statusNode = byId("sideMissionStatus");
        if (mode === "save") {
          const text = input ? String(input.value || "") : "";
          const contextLabel = buildMissionContextLabel();
          const quality = buildMissionHandoffQualityState({ input_text: text, context: contextLabel });
          renderMissionHandoffQuality(quality);
          if (!quality.ready) {
            const approved = confirmMissionDangerAction(
              "Handoff NOT-READY — зберегти все одно?",
              `Відсутні пункти: ${quality.missing_labels.join(", ")} · policy=${quality.profile_id} · fix=${quality.recommended_action ? quality.recommended_action.label : "manual"}`
            );
            if (!approved) {
              const blockedMetrics = updateMissionHandoffRemediationMetrics(quality, { event: "blocked" });
              renderMissionHandoffRemediationSummary(blockedMetrics, quality);
              renderMissionHandoffRemediationTimelinePreview();
              appendMissionHandoffTimelineEvent("quality_blocked", {
                context: contextLabel,
                text: `save blocked: ${quality.missing_labels.join(", ")} · policy=${quality.profile_id} · fix=${quality.recommended_action ? quality.recommended_action.label : "manual"}`,
              });
              renderMissionHandoffTimeline();
              if (statusNode) statusNode.textContent = `Handoff quality: NOT-READY (${quality.missing_labels.join(", ")}) · fix=${quality.recommended_action ? quality.recommended_action.label : "manual"}`;
              return false;
            }
            const overrideMetrics = updateMissionHandoffRemediationMetrics(quality, { event: "override", action: "override-save", applied: true });
            appendMissionHandoffRemediationTimelineEvent({
              ts: new Date().toISOString(),
              context: contextLabel,
              action: "override-save",
              applied: true,
              status_label: String(quality.status_label || "NOT-READY"),
              profile_id: String(quality.profile_id || "strict"),
              passed: Number(quality.passed || 0),
              total: Number(quality.total || 0),
              block_reason: String(quality.block_reason || ""),
              fix_label: quality.recommended_action && typeof quality.recommended_action === "object"
                ? String(quality.recommended_action.label || "")
                : "manual",
              cycle_open_sec: missionSecondsSinceIso(overrideMetrics.cycle_started_at || ""),
              ready_after: false,
              override_after_remediation: true,
            });
            renderMissionHandoffRemediationSummary(overrideMetrics, quality);
            renderMissionHandoffRemediationTimelinePreview();
            appendMissionHandoffTimelineEvent("quality_override", {
              context: contextLabel,
              text: `override save: ${quality.missing_labels.join(", ")} · policy=${quality.profile_id} · fix=${quality.recommended_action ? quality.recommended_action.label : "manual"}`,
            });
          } else {
            const readyBefore = loadMissionHandoffRemediationMetrics();
            const readyCycleSec = missionSecondsSinceIso(readyBefore.cycle_started_at || "");
            const readyMetrics = updateMissionHandoffRemediationMetrics(quality, { event: "ready-save", metrics: readyBefore });
            appendMissionHandoffRemediationTimelineEvent({
              ts: new Date().toISOString(),
              context: contextLabel,
              action: "ready-save",
              applied: true,
              status_label: String(quality.status_label || "READY"),
              profile_id: String(quality.profile_id || "strict"),
              passed: Number(quality.passed || 0),
              total: Number(quality.total || 0),
              block_reason: "",
              fix_label: quality.recommended_action && typeof quality.recommended_action === "object"
                ? String(quality.recommended_action.label || "")
                : "ready",
              cycle_open_sec: Number.isFinite(readyCycleSec) ? readyCycleSec : null,
              ready_after: true,
              override_after_remediation: false,
            });
            renderMissionHandoffRemediationSummary(readyMetrics, quality);
            renderMissionHandoffRemediationTimelinePreview();
          }
          const saved = saveMissionHandoffNote(text, { context: contextLabel });
          if (input) input.dataset.dirty = "0";
          if (saved) {
            const summary = buildSidebarNavAdoptionSummary();
            const scorecard = buildSidebarNavAdoptionScorecard(summary);
            appendMissionAdoptionHistoryEntry({
              ts: saved.ts,
              context: contextLabel,
              reason: "handoff save",
              summary,
              scorecard,
            });
            appendMissionHandoffTimelineEvent("save", {
              ts: saved.ts,
              context: contextLabel,
              text: `${saved.text}
quality=${quality.status_label} ${quality.passed}/${quality.total} policy=${quality.profile_id}`,
            });
          }
          renderMissionHandoffNotes();
          renderMissionHandoffTimeline();
          renderMissionHandoffAdoptionSummary();
          if (statusNode) statusNode.textContent = saved
            ? `Handoff: збережено (${quality.status_label} ${quality.passed}/${quality.total} · ${quality.profile_label})`
            : "Handoff: очищено";
          return true;
        }
        if (mode === "clear") {
          const contextLabel = buildMissionContextLabel();
          clearMissionHandoffNote();
          if (input) {
            input.value = "";
            input.dataset.dirty = "0";
          }
          appendMissionHandoffTimelineEvent("clear", {
            context: contextLabel,
            text: "handoff note cleared",
          });
          renderMissionHandoffNotes();
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Handoff: очищено";
          return true;
        }
        if (mode === "context") {
          if (!input) return false;
          const contextLabel = buildMissionContextLabel();
          if (!contextLabel) return false;
          const stamp = new Date().toISOString().slice(11, 16);
          const line = `[${stamp}] ${contextLabel}`;
          const base = String(input.value || "").slice(0, MISSION_HANDOFF_MAX_LENGTH);
          const separator = base.trim() ? "\n" : "";
          input.value = `${base}${separator}${line}`.slice(0, MISSION_HANDOFF_MAX_LENGTH);
          input.dataset.dirty = "1";
          appendMissionHandoffTimelineEvent("context", {
            context: contextLabel,
            text: line,
          });
          renderMissionHandoffNotes();
          renderMissionHandoffTimeline();
          if (statusNode) statusNode.textContent = "Handoff: додано контекст";
          return true;
        }
        return false;
      }
      function runMissionTriagePreset(presetId) {
        const clean = String(presetId || "").trim().toLowerCase();
        if (!clean) return false;
        const preset = MISSION_TRIAGE_PRESETS.find((item) => String(item.id || "").trim().toLowerCase() === clean);
        if (!preset) return false;
        const href = String(preset.href || "").trim();
        if (!href) return false;
        const playbook = missionPlaybookSteps(clean);
        storeMissionLastPreset(clean, { source: "preset", next_index: playbook.length > 1 ? 1 : 0 });
        recordSidebarIntentUsage(`triage:${clean}`);
        recordSidebarSessionShortcut({
          key: `triage:${clean}`,
          label: String(preset.label || clean),
          href,
        });
        const statusNode = byId("sideMissionStatus");
        if (statusNode) {
          const nextLabel = playbook.length > 1 ? String(playbook[1].label || "") : "";
          statusNode.textContent = nextLabel
            ? `Preset: ${String(preset.label || clean)} · Next: ${nextLabel}`
            : `Preset: ${String(preset.label || clean)}`;
        }
        window.location.assign(href);
        return true;
      }
      function renderStickyIncidentFocus() {
        const node = byId("sideIncidentFocus");
        if (!node) return;
        const context = loadWorkspaceContext({ maxAgeSec: 14 * 24 * 3600 });
        if (!context || (!context.central_id && !context.code && !context.label)) {
          node.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        const central = String(context.central_id || "").trim();
        const code = String(context.code || "").trim();
        const label = String(context.label || (central && code ? `${central}:${code}` : central || code || "incident")).trim();
        const meta = context.pinned ? "Закріплено" : (context.source ? `джерело=${context.source}` : "контекст");
        const canOpenDetail = !!central && !!code;
        const detailDisabled = canOpenDetail ? "" : "disabled";
        node.innerHTML = (
          `<div class="sideFocusBox">`
          + `<div class="sideFocusTitle">Incident Focus</div>`
          + `<div class="sideFocusValue">${esc(label)}</div>`
          + `<div class="sideFocusState">${esc(meta)}</div>`
          + `<div class="sideFocusActions">`
          + `<button class="sideFocusBtn" type="button" data-focus-action="detail" ${detailDisabled}>Картка</button>`
          + `<button class="sideFocusBtn" type="button" data-focus-action="list">Список</button>`
          + `<button class="sideFocusBtn" type="button" data-focus-action="pin">${context.pinned ? "Unpin" : "Pin"}</button>`
          + `<button class="sideFocusBtn" type="button" data-focus-action="clear">Очистити</button>`
          + `</div>`
          + `</div>`
        );
      }
      function runIncidentFocusAction(action) {
        const context = loadWorkspaceContext({ maxAgeSec: 14 * 24 * 3600 });
        if (!context) return false;
        const central = String(context.central_id || "").trim();
        const code = String(context.code || "").trim();
        const mode = String(action || "").trim().toLowerCase();
        if (mode === "clear") {
          clearWorkspaceContext();
          renderStickyIncidentFocus();
          return true;
        }
        if (mode === "pin") {
          saveWorkspaceContext({
            ...context,
            pinned: !context.pinned,
            ts: context.ts || new Date().toISOString(),
          });
          renderStickyIncidentFocus();
          return true;
        }
        if (mode === "detail") {
          if (!central || !code) return false;
          const href = `/admin/fleet/incidents/${encodeURIComponent(central)}/${encodeURIComponent(code)}`;
          recordSidebarSessionShortcut({ key: `focus:detail:${central}:${code}`, label: `Detail ${central}:${code}`, href });
          window.location.assign(href);
          return true;
        }
        if (mode === "list") {
          const params = new URLSearchParams();
          params.set("include_resolved", "0");
          if (central) params.set("central_id", central);
          if (code) params.set("code", code);
          const href = `/admin/fleet/incidents?${params.toString()}`;
          recordSidebarSessionShortcut({ key: `focus:list:${central}:${code}`, label: `List ${central}:${code}`, href });
          window.location.assign(href);
          return true;
        }
        return false;
      }
      function sidebarNavMeta() {
        const links = Array.from(document.querySelectorAll(".sideLink[data-nav-key]"));
        return links.map((node) => ({
          key: String(node.getAttribute("data-nav-key") || "").trim().toLowerCase(),
          label: String(node.getAttribute("data-nav-label") || node.textContent || "").trim(),
          href: String(node.getAttribute("data-nav-href") || node.getAttribute("href") || "").trim(),
          active: node.classList.contains("active"),
        })).filter((item) => !!item.key && !!item.href);
      }
      function renderSidebarMiniList(targetId, items, options = {}) {
        const node = byId(targetId);
        if (!node) return;
        const source = Array.isArray(items) ? items : [];
        if (source.length === 0) {
          node.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        const activeKey = String(options.activeKey || "").trim().toLowerCase();
        node.innerHTML = source
          .map((item) => {
            const key = String(item && item.key || "").trim().toLowerCase();
            const label = String(item && item.label || key || "");
            const href = String(item && item.href || "");
            const cls = activeKey && key === activeKey ? "sideMiniLink active" : "sideMiniLink";
            return `<a class="${cls}" href="${esc(href)}">${esc(label)}</a>`;
          })
          .join("");
      }
      function renderSidebarFavorites(items, options = {}) {
        const node = byId("sideFavoritesList");
        if (!node) return;
        const source = Array.isArray(items) ? items : [];
        if (source.length === 0) {
          node.innerHTML = '<span class="sideMiniEmpty">—</span>';
          return;
        }
        const activeKey = String(options.activeKey || "").trim().toLowerCase();
        node.innerHTML = source
          .map((item, index) => {
            const key = String(item && item.key || "").trim().toLowerCase();
            const label = String(item && item.label || key || "");
            const href = String(item && item.href || "");
            const cls = activeKey && key === activeKey ? "sideMiniLink active" : "sideMiniLink";
            const disableUp = index <= 0 ? "disabled" : "";
            const disableDown = index >= source.length - 1 ? "disabled" : "";
            return (
              `<div class="sideMiniRow">`
              + `<a class="${cls}" href="${esc(href)}">${esc(label)}</a>`
              + `<div class="sideMiniActions">`
              + `<button class="sideMiniAction" type="button" data-fav-action="up" data-nav-key="${esc(key)}" title="Вгору" ${disableUp}>↑</button>`
              + `<button class="sideMiniAction" type="button" data-fav-action="down" data-nav-key="${esc(key)}" title="Вниз" ${disableDown}>↓</button>`
              + `<button class="sideMiniAction" type="button" data-fav-action="remove" data-nav-key="${esc(key)}" title="Прибрати">×</button>`
              + `</div>`
              + `</div>`
            );
          })
          .join("");
      }
      function refreshSidebarGroups() {
        const collapsedSet = new Set(loadSidebarCollapsedGroups());
        const forceExpand = !!(
          document.body
          && (document.body.classList.contains("sidebar-simple") || document.body.classList.contains("sidebar-searching"))
        );
        const groups = Array.from(document.querySelectorAll(".sideGroup[data-side-group]"));
        for (const group of groups) {
          const key = String(group.getAttribute("data-side-group") || "").trim().toLowerCase();
          if (!key) continue;
          const collapsed = forceExpand ? false : collapsedSet.has(key);
          group.classList.toggle("collapsed", collapsed);
          const toggle = group.querySelector(".sideGroupToggle[data-side-group]");
          if (toggle) {
            toggle.setAttribute("aria-expanded", collapsed ? "false" : "true");
            toggle.title = collapsed ? "Розгорнути групу" : "Згорнути групу";
          }
        }
      }
      function listVisibleSidebarNavLinks() {
        return Array.from(document.querySelectorAll(".sideLinkWrap:not(.navFilteredOut) .sideLink[data-nav-key]"))
          .filter((node) => node instanceof HTMLAnchorElement);
      }
      function applySidebarNavFilter(rawValue = "", options = {}) {
        const source = options && typeof options === "object" ? options : {};
        const query = String(rawValue || "").trim().toLowerCase();
        if (document.body) document.body.classList.toggle("sidebar-searching", !!query);
        try { refreshSidebarGroups(); } catch (_error) {}
        const linkWraps = Array.from(document.querySelectorAll(".sideLinkWrap"));
        let visibleLinks = 0;
        for (const wrap of linkWraps) {
          const link = wrap.querySelector(".sideLink[data-nav-key]");
          if (!(link instanceof HTMLAnchorElement)) continue;
          const key = String(link.getAttribute("data-nav-key") || "").trim().toLowerCase();
          const label = String(link.getAttribute("data-nav-label") || link.textContent || "").trim().toLowerCase();
          const href = String(link.getAttribute("data-nav-href") || link.getAttribute("href") || "").trim().toLowerCase();
          const matches = !query || key.includes(query) || label.includes(query) || href.includes(query);
          wrap.classList.toggle("navFilteredOut", !matches);
          wrap.setAttribute("aria-hidden", matches ? "false" : "true");
          link.tabIndex = matches ? 0 : -1;
          if (matches) visibleLinks += 1;
        }
        const groups = Array.from(document.querySelectorAll(".sideGroup[data-side-group]"));
        let visibleGroups = 0;
        for (const group of groups) {
          const hasVisibleLink = !!group.querySelector(".sideLinkWrap:not(.navFilteredOut)");
          const hideGroup = !!query && !hasVisibleLink;
          group.classList.toggle("navFilteredOut", hideGroup);
          group.setAttribute("aria-hidden", hideGroup ? "true" : "false");
          if (!hideGroup) visibleGroups += 1;
        }
        const jumps = Array.from(document.querySelectorAll(".sideJumpRow .sideJump"));
        let visibleJumps = 0;
        for (const jump of jumps) {
          const label = String(jump.getAttribute("data-nav-label") || jump.textContent || "").trim().toLowerCase();
          const hideJump = !!query && !label.includes(query);
          jump.classList.toggle("navFilteredOut", hideJump);
          jump.setAttribute("aria-hidden", hideJump ? "true" : "false");
          jump.tabIndex = hideJump ? -1 : 0;
          if (!hideJump) visibleJumps += 1;
        }
        const statusNode = byId("sideNavFilterStatus");
        if (statusNode) {
          statusNode.textContent = query
            ? `Фільтр: ${query} · links ${visibleLinks} · groups ${visibleGroups} · jumps ${visibleJumps}`
            : "Фільтр: усі секції";
        }
        if (source.track === true) {
          const prevQuery = String(source.previous_query || "").trim().toLowerCase();
          if (query && query !== prevQuery) {
            recordSidebarNavAdoptionEvent("nav_search_input");
            recordSidebarNavAdoptionEvent("nav_filter_apply");
          } else if (!query && !!prevQuery) {
            recordSidebarNavAdoptionEvent("nav_search_clear");
            recordSidebarNavAdoptionEvent("nav_filter_clear");
          }
        }
      }
      function bindSidebarNavTools() {
        const filterNode = byId("sideNavFilter");
        if (filterNode && filterNode.dataset.bound !== "1") {
          const runFilter = debounce(() => {
            const previousQuery = String(filterNode.dataset.lastQuery || "");
            const nextQuery = String(filterNode.value || "");
            applySidebarNavFilter(nextQuery, {
              track: true,
              source: "input",
              previous_query: previousQuery,
            });
            filterNode.dataset.lastQuery = nextQuery;
          }, 140);
          filterNode.addEventListener("input", () => runFilter());
          filterNode.addEventListener("focus", () => {
            recordSidebarNavAdoptionEvent("nav_search_focus");
          });
          filterNode.addEventListener("keydown", (event) => {
            const key = String(event.key || "").trim().toLowerCase();
            if (key === "escape") {
              event.preventDefault();
              const previousQuery = String(filterNode.dataset.lastQuery || filterNode.value || "");
              filterNode.value = "";
              applySidebarNavFilter("", {
                track: true,
                source: "escape",
                previous_query: previousQuery,
              });
              filterNode.dataset.lastQuery = "";
              return;
            }
            if (key === "arrowdown") {
              const links = listVisibleSidebarNavLinks();
              if (links.length === 0) return;
              event.preventDefault();
              recordSidebarNavAdoptionEvent("nav_search_arrowdown");
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
              if (href) {
                recordSidebarNavAdoptionEvent("nav_search_enter_open");
                window.location.assign(href);
              }
            }
          });
          filterNode.dataset.bound = "1";
          filterNode.dataset.lastQuery = String(filterNode.value || "");
        }
        const compactToggle = byId("sideNavCompactToggle");
        if (compactToggle && compactToggle.dataset.bound !== "1") {
          compactToggle.addEventListener("click", (event) => {
            event.preventDefault();
            const current = loadSidebarCompactMode();
            const next = !current;
            storeSidebarCompactMode(next);
            applySidebarCompactMode(next);
            recordSidebarNavAdoptionEvent(next ? "nav_compact_enable" : "nav_compact_disable");
          });
          compactToggle.dataset.bound = "1";
        }
        const modeToggle = byId("sideNavModeToggle");
        if (modeToggle && modeToggle.dataset.bound !== "1") {
          modeToggle.addEventListener("click", (event) => {
            event.preventDefault();
            const current = loadSidebarSimpleMode();
            const next = !current;
            storeSidebarSimpleMode(next);
            applySidebarSimpleMode(next);
            recordSidebarNavAdoptionEvent(next ? "nav_simple_enable" : "nav_simple_disable");
          });
          modeToggle.dataset.bound = "1";
        }
        const helpToggle = byId("sideNavHelpToggle");
        if (helpToggle && helpToggle.dataset.bound !== "1") {
          helpToggle.addEventListener("click", (event) => {
            event.preventDefault();
            const expanded = String(helpToggle.getAttribute("aria-expanded") || "false") === "true";
            setSidebarNavOnboardingVisible(!expanded, { persistDismiss: false });
            recordSidebarNavAdoptionEvent(expanded ? "nav_onboarding_close" : "nav_onboarding_open");
          });
          helpToggle.dataset.bound = "1";
        }
        const dismissNode = byId("sideNavOnboardingDismiss");
        if (dismissNode && dismissNode.dataset.bound !== "1") {
          dismissNode.addEventListener("click", (event) => {
            event.preventDefault();
            setSidebarNavOnboardingVisible(false, { persistDismiss: true });
            recordSidebarNavAdoptionEvent("nav_onboarding_dismiss");
          });
          dismissNode.dataset.bound = "1";
        }
        if (document.body && document.body.dataset.sidebarNavHotkeys !== "1") {
          document.addEventListener("keydown", (event) => {
            if (event.defaultPrevented) return;
            if (!event.altKey || !event.shiftKey || event.ctrlKey || event.metaKey) return;
            if (isEditableTarget(event.target)) return;
            const key = String(event.key || "").trim().toLowerCase();
            if (key !== "n") return;
            const searchNode = byId("sideNavFilter");
            if (!(searchNode instanceof HTMLInputElement)) return;
            event.preventDefault();
            recordSidebarNavAdoptionEvent("nav_search_hotkey_focus");
            searchNode.focus();
            searchNode.select();
          });
          document.body.dataset.sidebarNavHotkeys = "1";
        }
        applySidebarCompactMode(loadSidebarCompactMode());
        applySidebarSimpleMode(loadSidebarSimpleMode());
        setSidebarNavOnboardingVisible(!isSidebarNavOnboardingDismissed(), { persistDismiss: false });
        applySidebarNavFilter(filterNode ? filterNode.value : "");
        renderMissionHandoffAdoptionSummary();
      }
      function refreshSidebarPersonalization() {
        const meta = sidebarNavMeta();
        if (meta.length === 0) return;
        const metaMap = new Map(meta.map((item) => [item.key, item]));
        const active = meta.find((item) => item.active) || null;
        const activeKey = active ? active.key : "";
        const favorites = loadSidebarFavorites().filter((key) => metaMap.has(key));
        const favoriteEntries = favorites.map((key) => metaMap.get(key));
        renderSidebarFavorites(favoriteEntries, { activeKey });
        const recents = loadSidebarRecent()
          .filter((item) => metaMap.has(item.key))
          .map((item) => {
            const current = metaMap.get(item.key);
            return { key: item.key, label: item.label || current.label, href: current.href };
          });
        renderSidebarMiniList("sideRecentList", recents, { activeKey });
        renderSidebarIntentSections();
        renderSidebarContextHint();
        renderMissionWidgets();
        renderMissionPresets();
        renderMissionPlaybooks();
        renderMissionChain();
        renderMissionSnapshotSummary();
        renderMissionResponsePackSummary();
        renderStickyIncidentFocus();
        renderMissionHandoffNotes();
        renderMissionHandoffTimeline();
        renderMissionHandoffAdoptionSummary();
        renderSidebarSessionShortcuts();
        const favoriteSet = new Set(favorites);
        const pins = Array.from(document.querySelectorAll(".sidePin[data-nav-key]"));
        for (const pin of pins) {
          const key = String(pin.getAttribute("data-nav-key") || "").trim().toLowerCase();
          const isActive = favoriteSet.has(key);
          pin.classList.toggle("active", isActive);
          pin.textContent = isActive ? "★" : "☆";
          pin.setAttribute("aria-pressed", isActive ? "true" : "false");
          pin.title = isActive ? "Прибрати з обраного" : "Додати в обране";
        }
        const filterNode = byId("sideNavFilter");
        applySidebarNavFilter(filterNode ? filterNode.value : "");
      }
      function toggleSidebarFavorite(key) {
        const cleanKey = String(key || "").trim().toLowerCase();
        if (!cleanKey) return;
        const current = loadSidebarFavorites();
        const index = current.indexOf(cleanKey);
        if (index >= 0) current.splice(index, 1);
        else current.unshift(cleanKey);
        storeSidebarFavorites(current);
        refreshSidebarPersonalization();
      }
      function moveSidebarFavorite(key, direction) {
        const cleanKey = String(key || "").trim().toLowerCase();
        const delta = direction === "up" ? -1 : direction === "down" ? 1 : 0;
        if (!cleanKey || delta === 0) return;
        const current = loadSidebarFavorites();
        const index = current.indexOf(cleanKey);
        if (index < 0) return;
        const nextIndex = index + delta;
        if (nextIndex < 0 || nextIndex >= current.length) return;
        const swap = current[nextIndex];
        current[nextIndex] = current[index];
        current[index] = swap;
        storeSidebarFavorites(current);
        refreshSidebarPersonalization();
      }
      function removeSidebarFavorite(key) {
        const cleanKey = String(key || "").trim().toLowerCase();
        if (!cleanKey) return;
        const current = loadSidebarFavorites().filter((item) => item !== cleanKey);
        storeSidebarFavorites(current);
        refreshSidebarPersonalization();
      }
      function trackSidebarRecent() {
        const meta = sidebarNavMeta();
        const active = meta.find((item) => item.active);
        if (!active) return;
        const current = loadSidebarRecent().filter((item) => String(item.key || "") !== active.key);
        current.unshift({
          key: active.key,
          label: active.label,
          href: active.href,
          ts: new Date().toISOString(),
        });
        storeSidebarRecent(current);
      }
      function toggleSidebarGroup(key) {
        const cleanKey = String(key || "").trim().toLowerCase();
        if (!cleanKey) return;
        const current = loadSidebarCollapsedGroups();
        const index = current.indexOf(cleanKey);
        const willCollapse = index < 0;
        if (index >= 0) current.splice(index, 1);
        else current.push(cleanKey);
        storeSidebarCollapsedGroups(current);
        refreshSidebarGroups();
        recordSidebarNavAdoptionEvent("nav_group_toggle");
        recordSidebarNavAdoptionEvent(willCollapse ? "nav_group_collapse" : "nav_group_expand");
      }
      function setSidebarGroupCollapsed(key, collapsed) {
        const cleanKey = String(key || "").trim().toLowerCase();
        if (!cleanKey) return;
        const current = loadSidebarCollapsedGroups();
        const index = current.indexOf(cleanKey);
        let changed = false;
        if (collapsed && index < 0) current.push(cleanKey);
        if (collapsed && index < 0) changed = true;
        if (!collapsed && index >= 0) {
          current.splice(index, 1);
          changed = true;
        }
        storeSidebarCollapsedGroups(current);
        refreshSidebarGroups();
        if (changed) {
          recordSidebarNavAdoptionEvent("nav_group_toggle");
          recordSidebarNavAdoptionEvent(collapsed ? "nav_group_collapse" : "nav_group_expand");
        }
      }
      function isEditableTarget(target) {
        if (!target || !(target instanceof Element)) return false;
        if (target.closest("input, textarea, select, [contenteditable='true']")) return true;
        return false;
      }
      function runQuickIntent(intent) {
        const cleanIntent = String(intent || "").trim().toLowerCase();
        if (!cleanIntent) return false;
        const link = document.querySelector(`a[data-quick-intent="${cleanIntent}"]`);
        if (!(link instanceof HTMLAnchorElement)) return false;
        const href = String(link.getAttribute("href") || "").trim();
        if (!href) return false;
        const intentMeta = SIDEBAR_INTENTS.find((item) => String(item.id || "").trim().toLowerCase() === cleanIntent);
        const label = intentMeta ? String(intentMeta.label || cleanIntent) : cleanIntent;
        recordSidebarIntentUsage(cleanIntent);
        recordSidebarSessionShortcut({
          key: `intent:${cleanIntent}`,
          label,
          href,
        });
        const statusNode = byId("sideHubStatus");
        if (statusNode) statusNode.textContent = `Intent: ${cleanIntent}`;
        window.location.assign(href);
        return true;
      }
      function canRunMissionHotkeyActions() {
        const missionNode = byId("sideMissionControl");
        if (!(missionNode instanceof HTMLElement)) return false;
        if (!document.body || !document.body.contains(missionNode)) return false;
        return true;
      }
      function runMissionHotkeyAction(action, label) {
        const cleanAction = String(action || "").trim().toLowerCase();
        if (!cleanAction || !canRunMissionHotkeyActions()) return false;
        const executed = runMissionResponsePackAction(cleanAction);
        if (!executed) return false;
        const statusNode = byId("sideMissionStatus");
        if (statusNode) statusNode.textContent = `Hotkey: ${String(label || cleanAction)}`;
        return true;
      }
      function bindSidebarCommandHub() {
        const hub = byId("sideCommandHub");
        if (hub) {
          hub.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;
            const actionNode = target.closest("button[data-intent-run]");
            if (!(actionNode instanceof HTMLButtonElement)) return;
            event.preventDefault();
            const intent = String(actionNode.getAttribute("data-intent-run") || "").trim().toLowerCase();
            runQuickIntent(intent);
          });
        }
        const focusToggle = byId("sideFocusToggle");
        if (focusToggle) {
          focusToggle.addEventListener("click", (event) => {
            event.preventDefault();
            const current = document.body.classList.contains("sidebar-focus");
            const next = !current;
            storeSidebarFocusMode(next);
            applySidebarFocusMode(next);
          });
        }
        const quickNode = byId("sideQuickIntentList");
        if (quickNode) {
          quickNode.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;
            const linkNode = target.closest("a[data-quick-intent]");
            if (!(linkNode instanceof HTMLAnchorElement)) return;
            event.preventDefault();
            const intent = String(linkNode.getAttribute("data-quick-intent") || "").trim().toLowerCase();
            runQuickIntent(intent);
          });
        }
        const missionNode = byId("sideMissionControl");
        if (missionNode) {
          missionNode.addEventListener("input", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;
            const handoffInput = target.closest("#sideHandoffInput");
            if (!(handoffInput instanceof HTMLTextAreaElement)) return;
            handoffInput.dataset.dirty = "1";
            renderMissionHandoffNotes();
          });
          missionNode.addEventListener("change", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;
            const routingProfile = target.closest("#sideRoutingProfile");
            if (routingProfile instanceof HTMLSelectElement) {
              syncMissionRoutingSelectionFromControls();
              runMissionResponsePackAction("apply-routing");
              return;
            }
            const routingTemplate = target.closest("#sideRoutingTemplate");
            if (routingTemplate instanceof HTMLSelectElement) {
              syncMissionRoutingSelectionFromControls();
              runMissionResponsePackAction("apply-routing");
              return;
            }
            const deliveryAdapter = target.closest("#sideDeliveryAdapter");
            if (deliveryAdapter instanceof HTMLSelectElement) {
              syncMissionDeliverySelectionFromControls();
              runMissionResponsePackAction("apply-delivery");
              return;
            }
            const deliveryVariant = target.closest("#sideDeliveryVariant");
            if (deliveryVariant instanceof HTMLSelectElement) {
              syncMissionDeliverySelectionFromControls();
              runMissionResponsePackAction("apply-delivery");
              return;
            }
            const deliveryPolicy = target.closest("#sideDeliveryPolicyProfile");
            if (deliveryPolicy instanceof HTMLSelectElement) {
              syncMissionDeliveryPolicySelectionFromControls();
              runMissionResponsePackAction("apply-delivery-policy");
            }
          });
          missionNode.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;
            const triageNode = target.closest("button[data-triage-run]");
            if (triageNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const presetId = String(triageNode.getAttribute("data-triage-run") || "").trim().toLowerCase();
              runMissionTriagePreset(presetId);
              return;
            }
            const playbookNode = target.closest("button[data-playbook-run]");
            if (playbookNode instanceof HTMLButtonElement) {
              event.preventDefault();
              runMissionPlaybookStep({
                href: String(playbookNode.getAttribute("data-playbook-run") || "").trim(),
                preset_id: String(playbookNode.getAttribute("data-playbook-preset") || "").trim().toLowerCase(),
                step_index: Number(playbookNode.getAttribute("data-playbook-step")),
                label: String(playbookNode.getAttribute("data-playbook-label") || "").trim(),
              });
              return;
            }
            const chainNode = target.closest("button[data-chain-run]");
            if (chainNode instanceof HTMLButtonElement) {
              event.preventDefault();
              runMissionChainAction({
                href: String(chainNode.getAttribute("data-chain-run") || "").trim(),
                preset_id: String(chainNode.getAttribute("data-chain-preset") || "").trim().toLowerCase(),
                step_index: Number(chainNode.getAttribute("data-chain-step")),
                label: String(chainNode.getAttribute("data-chain-label") || "").trim(),
              });
              return;
            }
            const snapshotNode = target.closest("button[data-snapshot-action]");
            if (snapshotNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(snapshotNode.getAttribute("data-snapshot-action") || "").trim().toLowerCase();
              runMissionSnapshotAction(action);
              return;
            }
            const responsePackNode = target.closest("button[data-response-pack-action]");
            if (responsePackNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(responsePackNode.getAttribute("data-response-pack-action") || "").trim().toLowerCase();
              runMissionResponsePackAction(action);
              return;
            }
            const focusNode = target.closest("button[data-focus-action]");
            if (focusNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(focusNode.getAttribute("data-focus-action") || "").trim().toLowerCase();
              runIncidentFocusAction(action);
              return;
            }
            const handoffNode = target.closest("button[data-handoff-action]");
            if (handoffNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffNode.getAttribute("data-handoff-action") || "").trim().toLowerCase();
              runMissionHandoffAction(action);
              return;
            }
            const handoffHistoryNode = target.closest("button[data-handoff-history-action]");
            if (handoffHistoryNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffHistoryNode.getAttribute("data-handoff-history-action") || "").trim().toLowerCase();
              runMissionHandoffHistoryAction(action);
              return;
            }
            const handoffRemediationHistoryNode = target.closest("button[data-handoff-remediation-history-action]");
            if (handoffRemediationHistoryNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffRemediationHistoryNode.getAttribute("data-handoff-remediation-history-action") || "").trim().toLowerCase();
              runMissionHandoffRemediationHistoryAction(action);
              return;
            }
            const handoffRemediationGovernanceNode = target.closest("button[data-handoff-remediation-governance]");
            if (handoffRemediationGovernanceNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const profileId = String(handoffRemediationGovernanceNode.getAttribute("data-handoff-remediation-governance") || "").trim().toLowerCase();
              runMissionHandoffRemediationGovernanceAction(profileId);
              return;
            }
            const handoffRemediationIncidentNode = target.closest("button[data-handoff-remediation-incident-action]");
            if (handoffRemediationIncidentNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffRemediationIncidentNode.getAttribute("data-handoff-remediation-incident-action") || "").trim().toLowerCase();
              runMissionHandoffRemediationIncidentAction(action);
              return;
            }
            const handoffRemediationIncidentHistoryNode = target.closest("button[data-handoff-remediation-incident-history-action]");
            if (handoffRemediationIncidentHistoryNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffRemediationIncidentHistoryNode.getAttribute("data-handoff-remediation-incident-history-action") || "").trim().toLowerCase();
              runMissionHandoffRemediationIncidentHistoryAction(action);
              return;
            }
            const handoffRemediationPlanNode = target.closest("button[data-handoff-remediation-plan-action]");
            if (handoffRemediationPlanNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffRemediationPlanNode.getAttribute("data-handoff-remediation-plan-action") || "").trim().toLowerCase();
              runMissionHandoffRemediationPlanAction(action);
              return;
            }
            const handoffAdoptionNode = target.closest("button[data-handoff-adoption-action]");
            if (handoffAdoptionNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffAdoptionNode.getAttribute("data-handoff-adoption-action") || "").trim().toLowerCase();
              runMissionHandoffAdoptionAction(action);
              return;
            }
            const handoffTrendNode = target.closest("button[data-handoff-trend-action]");
            if (handoffTrendNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffTrendNode.getAttribute("data-handoff-trend-action") || "").trim().toLowerCase();
              runMissionHandoffTrendAction(action);
              return;
            }
            const handoffTrendWindowNode = target.closest("button[data-handoff-trend-window]");
            if (handoffTrendWindowNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const windowValue = Number(handoffTrendWindowNode.getAttribute("data-handoff-trend-window"));
              runMissionHandoffTrendWindowAction(windowValue);
              return;
            }
            const handoffComposeNode = target.closest("button[data-handoff-compose-action]");
            if (handoffComposeNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffComposeNode.getAttribute("data-handoff-compose-action") || "").trim().toLowerCase();
              runMissionHandoffComposerAction(action);
              return;
            }
            const handoffQualityNode = target.closest("button[data-handoff-quality-action]");
            if (handoffQualityNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffQualityNode.getAttribute("data-handoff-quality-action") || "").trim().toLowerCase();
              runMissionHandoffQualityAction(action);
              return;
            }
            const handoffQualityRemedyNode = target.closest("button[data-handoff-quality-remedy]");
            if (handoffQualityRemedyNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const action = String(handoffQualityRemedyNode.getAttribute("data-handoff-quality-remedy") || "").trim().toLowerCase();
              runMissionHandoffQualityRemediationAction(action);
              return;
            }
            const handoffQualityProfileNode = target.closest("button[data-handoff-quality-profile]");
            if (handoffQualityProfileNode instanceof HTMLButtonElement) {
              event.preventDefault();
              const profileId = String(handoffQualityProfileNode.getAttribute("data-handoff-quality-profile") || "").trim().toLowerCase();
              runMissionHandoffQualityProfileAction(profileId);
            }
          });
        }
      }
      function bindSidebarQuickIntentHotkeys() {
        if (document.body && document.body.dataset.sidebarQuickHotkeys === "1") return;
        document.addEventListener("keydown", (event) => {
          if (event.defaultPrevented) return;
          if (!event.altKey || !event.shiftKey || event.ctrlKey || event.metaKey) return;
          if (isEditableTarget(event.target)) return;
          const key = String(event.key || "").trim().toLowerCase();
          let intent = "";
          if (key === "a") intent = "alerts-bad";
          else if (key === "i") intent = "incidents-open";
          else if (key === "u") intent = "audit-last";
          if (intent) {
            event.preventDefault();
            runQuickIntent(intent);
            return;
          }
          const missionHotkeys = {
            d: { action: "apply-delivery-suggestion", label: "apply suggestion" },
            k: { action: "ack-delivery", label: "ack delivery" },
            r: { action: "retry-delivery", label: "retry delivery" },
            e: { action: "escalate-delivery", label: "escalate delivery" },
            b: { action: "bulk-ack-pending", label: "bulk ack" },
            y: { action: "bulk-retry-stale", label: "bulk retry" },
            g: { action: "bulk-escalate-stale", label: "bulk escalate" },
            p: { action: "apply-delivery-policy", label: "apply policy" },
            j: { action: "show-delivery-journal", label: "delivery journal" },
          };
          const target = missionHotkeys[key];
          if (!target) return;
          event.preventDefault();
          runMissionHotkeyAction(target.action, target.label);
        });
        if (document.body) document.body.dataset.sidebarQuickHotkeys = "1";
      }
	      function initSidebarPersonalization() {
	        if (!document.querySelector(".sideNav")) return;
	        function isMissionSidebarActive() {
	          // Mission sidebar is a heavy block; keep it out of the way in Simple/Focus modes.
	          return !document.body.classList.contains("sidebar-simple") && !document.body.classList.contains("sidebar-focus");
	        }
	        bindSidebarQuickIntentHotkeys();
	        bindSidebarCommandHub();
	        bindSidebarNavTools();
        applySidebarFocusMode(loadSidebarFocusMode());
        refreshSidebarMiniSections();
        if (document.body && document.body.dataset.sidebarMissionTicker !== "1") {
          setInterval(() => {
            renderSidebarContextHint();
            if (!isMissionSidebarActive()) return;
            renderMissionWidgets();
            renderMissionPresets();
            renderMissionPlaybooks();
            renderMissionChain();
            renderMissionSnapshotSummary();
            renderMissionResponsePackSummary();
            renderStickyIncidentFocus();
            renderMissionHandoffNotes();
            renderMissionHandoffTimeline();
            renderMissionHandoffAdoptionSummary();
            renderMissionHandoffRemediationSummary();
            renderMissionHandoffRemediationTimelinePreview();
          }, 5000);
          document.body.dataset.sidebarMissionTicker = "1";
        }
        if (document.body && document.body.dataset.sidebarPersonalized === "1") {
          refreshSidebarGroups();
          refreshSidebarPersonalization();
          return;
        }
        const groupToggles = Array.from(document.querySelectorAll(".sideGroupToggle[data-side-group]"));
        for (const toggle of groupToggles) {
          toggle.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            toggleSidebarGroup(toggle.getAttribute("data-side-group") || "");
          });
          toggle.addEventListener("keydown", (event) => {
            const key = String(event.key || "").trim().toLowerCase();
            if (key === "arrowleft") {
              event.preventDefault();
              setSidebarGroupCollapsed(toggle.getAttribute("data-side-group") || "", true);
              return;
            }
            if (key === "arrowright") {
              event.preventDefault();
              setSidebarGroupCollapsed(toggle.getAttribute("data-side-group") || "", false);
              return;
            }
            if (key === "home") {
              event.preventDefault();
              if (groupToggles.length > 0) groupToggles[0].focus();
              return;
            }
            if (key === "end") {
              event.preventDefault();
              if (groupToggles.length > 0) groupToggles[groupToggles.length - 1].focus();
            }
          });
        }
        const miniToggles = Array.from(document.querySelectorAll("button.sideMiniToggle[data-side-mini-toggle]"));
        for (const toggle of miniToggles) {
          if (!(toggle instanceof HTMLButtonElement)) continue;
          if (toggle.dataset.bound === "1") continue;
          toggle.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            toggleSidebarMiniSection(toggle.getAttribute("data-side-mini-toggle") || "");
          });
          toggle.dataset.bound = "1";
        }
        const pinNodes = Array.from(document.querySelectorAll(".sidePin[data-nav-key]"));
        for (const pin of pinNodes) {
          pin.addEventListener("click", (event) => {
            event.preventDefault();
            event.stopPropagation();
            toggleSidebarFavorite(pin.getAttribute("data-nav-key") || "");
          });
        }
        const navLinks = Array.from(document.querySelectorAll(".sideLink[data-nav-key]"));
        for (const link of navLinks) {
          link.addEventListener("click", () => {
            const key = String(link.getAttribute("data-nav-key") || "").trim().toLowerCase();
            const label = String(link.getAttribute("data-nav-label") || link.textContent || "").trim();
            const href = String(link.getAttribute("data-nav-href") || link.getAttribute("href") || "").trim();
            if (!key || !href) return;
            recordSidebarSessionShortcut({
              key: `nav:${key}`,
              label: label || key,
              href,
            });
          });
        }
        const favoritesList = byId("sideFavoritesList");
        if (favoritesList) {
          favoritesList.addEventListener("click", (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;
            const actionNode = target.closest("button[data-fav-action][data-nav-key]");
            if (!(actionNode instanceof HTMLButtonElement)) return;
            event.preventDefault();
            event.stopPropagation();
            const action = String(actionNode.getAttribute("data-fav-action") || "").trim().toLowerCase();
            const key = String(actionNode.getAttribute("data-nav-key") || "").trim().toLowerCase();
            if (action === "up" || action === "down") moveSidebarFavorite(key, action);
            else if (action === "remove") removeSidebarFavorite(key);
          });
        }
        const clearFav = byId("sideFavoritesClear");
        if (clearFav) {
          clearFav.addEventListener("click", (event) => {
            event.preventDefault();
            storeSidebarFavorites([]);
            refreshSidebarPersonalization();
          });
        }
        const clearRecent = byId("sideRecentClear");
        if (clearRecent) {
          clearRecent.addEventListener("click", (event) => {
            event.preventDefault();
            storeSidebarRecent([]);
            refreshSidebarPersonalization();
          });
        }
        const clearSession = byId("sideSessionClear");
        if (clearSession) {
          clearSession.addEventListener("click", (event) => {
            event.preventDefault();
            storeSidebarSessionShortcuts([]);
            renderSidebarSessionShortcuts();
            renderMissionPresets();
          });
        }
        const active = sidebarNavMeta().find((item) => item.active);
        if (active) {
          recordSidebarSessionShortcut({
            key: `nav:${String(active.key || "").trim().toLowerCase()}`,
            label: String(active.label || active.key || "").trim(),
            href: String(active.href || "").trim(),
          });
        }
        trackSidebarRecent();
        refreshSidebarGroups();
        refreshSidebarPersonalization();
	        if (isMissionSidebarActive()) {
	          renderMissionHandoffRemediationSummary();
	          renderMissionHandoffRemediationTimelinePreview();
	        }
	        if (document.body) document.body.dataset.sidebarPersonalized = "1";
	      }
		      function applyEmptyTables() {
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
	      }
	      try {
	        initSidebarPersonalization();
	        applyEmptyTables();
	      } catch (_error) {}
	      function formatLatency(ms) {
	        const value = Number(ms);
	        if (!Number.isFinite(value) || value < 0) return "—";
        if (value < 1000) return `${Math.round(value)}мс`;
        return `${(value / 1000).toFixed(2)}с`;
      }
      async function runActionWithLatency(runner) {
        const startedAt = Date.now();
        try {
          const result = await runner();
          return { ok: true, result, elapsed_ms: Date.now() - startedAt };
        } catch (error) {
          return { ok: false, error, elapsed_ms: Date.now() - startedAt };
        }
      }
      function boolFlag(value, fallback = false) {
        if (value === null || value === undefined) return !!fallback;
        const normalized = String(value).trim().toLowerCase();
        if (normalized === "1" || normalized === "true" || normalized === "yes" || normalized === "on") return true;
        if (normalized === "0" || normalized === "false" || normalized === "no" || normalized === "off") return false;
        return !!fallback;
      }
      function parseWorkspaceContext(raw) {
        if (!raw || typeof raw !== "object") return null;
        const centralId = String(raw.central_id || "").trim();
        const code = String(raw.code || "").trim();
        const source = String(raw.source || "").trim();
        const label = String(raw.label || "").trim();
        const ts = String(raw.ts || "").trim();
        const pinned = boolFlag(raw.pinned, false);
        if (!centralId && !code && !label) return null;
        return {
          central_id: centralId,
          code,
          source,
          label,
          ts,
          pinned,
        };
      }
      function contextAgeSec(ts) {
        const parsed = Date.parse(String(ts || ""));
        if (!Number.isFinite(parsed)) return null;
        const diff = Math.floor((Date.now() - parsed) / 1000);
        return Number.isFinite(diff) ? Math.max(0, diff) : null;
      }
      function formatAgeShort(sec) {
        const value = Number(sec);
        if (!Number.isFinite(value) || value < 0) return "";
        if (value < 60) return `${value}с`;
        const min = Math.floor(value / 60);
        if (min < 60) return `${min}хв`;
        const hours = Math.floor(min / 60);
        if (hours < 24) return `${hours}г`;
        const days = Math.floor(hours / 24);
        return `${days}д`;
      }
      function loadWorkspaceContext(options = {}) {
        let parsed = null;
        try {
          const raw = localStorage.getItem(WORKSPACE_STORAGE_KEY);
          parsed = parseWorkspaceContext(raw ? JSON.parse(raw) : null);
        } catch (_error) {
          parsed = null;
        }
        if (!parsed) return null;
        const maxAgeSecRaw = Number(options.maxAgeSec ?? 3 * 24 * 3600);
        const maxAgeSec = Number.isFinite(maxAgeSecRaw) && maxAgeSecRaw > 0 ? maxAgeSecRaw : 0;
        const ageSec = contextAgeSec(parsed.ts);
        if (!parsed.pinned && maxAgeSec > 0 && Number.isFinite(ageSec) && ageSec !== null && ageSec > maxAgeSec) {
          try { localStorage.removeItem(WORKSPACE_STORAGE_KEY); } catch (_error) {}
          return null;
        }
        return { ...parsed, age_sec: ageSec };
      }
      function saveWorkspaceContext(context = {}) {
        const current = loadWorkspaceContext({ maxAgeSec: 365 * 24 * 3600 }) || {};
        const next = parseWorkspaceContext({
          central_id: context.central_id ?? current.central_id ?? "",
          code: context.code ?? current.code ?? "",
          source: context.source ?? current.source ?? "",
          label: context.label ?? current.label ?? "",
          pinned: context.pinned ?? current.pinned ?? false,
          ts: context.ts || new Date().toISOString(),
        });
        if (!next) {
          clearWorkspaceContext();
          return null;
        }
        try { localStorage.setItem(WORKSPACE_STORAGE_KEY, JSON.stringify(next)); } catch (_error) {}
        return { ...next, age_sec: contextAgeSec(next.ts) };
      }
      function clearWorkspaceContext() {
        try { localStorage.removeItem(WORKSPACE_STORAGE_KEY); } catch (_error) {}
      }
      function formatWorkspaceContext(context, options = {}) {
        const prefix = String(options.prefix || "Контекст інциденту");
        const emptyText = String(options.emptyText || `${prefix}: —`);
        if (!context) return emptyText;
        const parts = [];
        if (context.label) parts.push(context.label);
        else if (context.central_id && context.code) parts.push(`${context.central_id}:${context.code}`);
        else if (context.central_id) parts.push(context.central_id);
        else if (context.code) parts.push(context.code);
        if (context.source) parts.push(`джерело=${context.source}`);
        if (context.age_sec !== null && context.age_sec !== undefined) {
          const short = formatAgeShort(context.age_sec);
          if (short) parts.push(`${short} тому`);
        }
        return `${prefix}: ${parts.join(" · ") || "—"}`;
      }
      function applyWorkspaceHint(targetId, options = {}) {
        const node = byId(targetId);
        if (!node) return null;
        const context = loadWorkspaceContext(options);
        node.textContent = formatWorkspaceContext(context, options);
        node.classList.toggle("empty", !context);
        return context;
      }
      function normalizePresetNamespace(namespaceValue) {
        return String(namespaceValue || "").trim().toLowerCase() === "shared" ? "shared" : "local";
      }
      function presetStorageKey(scope) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return "";
        return `${PRESETS_STORAGE_PREFIX}${cleanScope}`;
      }
      function presetArchiveStorageKey(scope, namespaceValue) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return "";
        const namespace = normalizePresetNamespace(namespaceValue);
        return `${PRESET_ARCHIVE_STORAGE_PREFIX}${namespace}:${cleanScope}`;
      }
      function presetCleanupReportStorageKey(scope, namespaceValue) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return "";
        const namespace = normalizePresetNamespace(namespaceValue);
        return `${PRESET_CLEANUP_REPORT_PREFIX}${namespace}:${cleanScope}`;
      }
      function presetTimelineStorageKey(scope, namespaceValue) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return "";
        const namespace = normalizePresetNamespace(namespaceValue);
        return `${PRESET_TIMELINE_STORAGE_PREFIX}${namespace}:${cleanScope}`;
      }
      function presetPolicyLockStorageKey(scope, namespaceValue) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return "";
        const namespace = normalizePresetNamespace(namespaceValue);
        return `${PRESET_POLICY_LOCK_PREFIX}${namespace}:${cleanScope}`;
      }
      function presetRolloutLastStorageKey(namespaceValue) {
        const namespace = normalizePresetNamespace(namespaceValue);
        return `${PRESET_ROLLOUT_LAST_PREFIX}${namespace}`;
      }
      function sharedPresetStorageKey() {
        return `${PRESETS_STORAGE_PREFIX}shared_store`;
      }
      function normalizePresetName(name) {
        return String(name || "").trim().split(" ").filter((part) => !!part).join(" ");
      }
      function normalizePresetList(rawList) {
        if (!Array.isArray(rawList)) return [];
        return rawList
          .map((item) => ({
            name: normalizePresetName(item && item.name),
            data: item && typeof item.data === "object" && item.data ? item.data : {},
            ts: String(item && item.ts ? item.ts : ""),
          }))
          .filter((item) => !!item.name)
          .sort((left, right) => String(right.ts || "").localeCompare(String(left.ts || "")));
      }
      function dedupePresetList(rawList) {
        const seen = new Set();
        const result = [];
        for (const item of normalizePresetList(rawList)) {
          const key = String(item.name || "").toLowerCase();
          if (!key || seen.has(key)) continue;
          seen.add(key);
          result.push(item);
        }
        return result.slice(0, 30);
      }
      function normalizePresetTimelineList(rawList) {
        if (!Array.isArray(rawList)) return [];
        return rawList
          .map((item) => {
            const details = item && typeof item.details === "object" && item.details ? item.details : {};
            return {
              ts: String(item && item.ts ? item.ts : ""),
              action: String(item && item.action ? item.action : "").trim().toLowerCase(),
              scope: String(item && item.scope ? item.scope : "").trim().toLowerCase(),
              namespace: normalizePresetNamespace(item && item.namespace),
              details,
            };
          })
          .filter((item) => !!item.action && !!item.scope)
          .sort((left, right) => String(right.ts || "").localeCompare(String(left.ts || "")))
          .slice(0, 400);
      }
      function loadSharedPresetStore() {
        try {
          const raw = JSON.parse(localStorage.getItem(sharedPresetStorageKey()) || "{}");
          const scopes = {};
          const rawScopes = raw && typeof raw.scopes === "object" && raw.scopes ? raw.scopes : {};
          for (const [scope, presets] of Object.entries(rawScopes)) {
            const cleanScope = String(scope || "").trim().toLowerCase();
            if (!cleanScope) continue;
            scopes[cleanScope] = dedupePresetList(presets);
          }
          return { version: 1, scopes };
        } catch (_error) {
          return { version: 1, scopes: {} };
        }
      }
      function saveSharedPresetStore(store) {
        const scopes = {};
        const sourceScopes = store && typeof store.scopes === "object" && store.scopes ? store.scopes : {};
        for (const [scope, presets] of Object.entries(sourceScopes)) {
          const cleanScope = String(scope || "").trim().toLowerCase();
          if (!cleanScope) continue;
          scopes[cleanScope] = dedupePresetList(presets);
        }
        localStorage.setItem(sharedPresetStorageKey(), JSON.stringify({ version: 1, scopes }));
      }
      function listPresetScopes(options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        if (namespace === "shared") {
          return Object.keys(loadSharedPresetStore().scopes || {}).sort();
        }
        const scopes = new Set();
        try {
          for (let index = 0; index < localStorage.length; index += 1) {
            const key = String(localStorage.key(index) || "");
            if (!key.startsWith(PRESETS_STORAGE_PREFIX)) continue;
            if (key === sharedPresetStorageKey()) continue;
            const scope = key.slice(PRESETS_STORAGE_PREFIX.length).trim().toLowerCase();
            if (!scope) continue;
            scopes.add(scope);
          }
        } catch (_error) {}
        return Array.from(scopes).sort();
      }
      function listPresets(scope, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return [];
        if (namespace === "shared") {
          const store = loadSharedPresetStore();
          return dedupePresetList(store.scopes[cleanScope] || []);
        }
        const key = presetStorageKey(cleanScope);
        if (!key) return [];
        try {
          const raw = JSON.parse(localStorage.getItem(key) || "[]");
          return dedupePresetList(raw);
        } catch (_error) {
          return [];
        }
      }
      function storePresets(scope, presets, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const normalizedList = dedupePresetList(presets);
        if (namespace === "shared") {
          const store = loadSharedPresetStore();
          store.scopes[cleanScope] = normalizedList;
          saveSharedPresetStore(store);
          return normalizedList;
        }
        const key = presetStorageKey(cleanScope);
        localStorage.setItem(key, JSON.stringify(normalizedList));
        return normalizedList;
      }
      function listPresetArchive(scope, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return [];
        const key = presetArchiveStorageKey(cleanScope, options.namespace);
        if (!key) return [];
        try {
          const raw = JSON.parse(localStorage.getItem(key) || "[]");
          const limitRaw = Number(options.limit ?? 200);
          const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(500, limitRaw) : 200;
          return dedupePresetList(raw).slice(0, limit);
        } catch (_error) {
          return [];
        }
      }
      function storePresetArchive(scope, archiveItems, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return [];
        const key = presetArchiveStorageKey(cleanScope, options.namespace);
        if (!key) return [];
        const normalized = dedupePresetList(archiveItems).slice(0, 500);
        localStorage.setItem(key, JSON.stringify(normalized));
        return normalized;
      }
      function getPresetCleanupReport(scope, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return null;
        const key = presetCleanupReportStorageKey(cleanScope, options.namespace);
        if (!key) return null;
        try {
          const raw = JSON.parse(localStorage.getItem(key) || "{}");
          if (!raw || typeof raw !== "object") return null;
          return {
            ts: String(raw.ts || ""),
            namespace: normalizePresetNamespace(raw.namespace),
            scope: cleanScope,
            before: Number(raw.before || 0),
            kept: Number(raw.kept || 0),
            removed: Number(raw.removed || 0),
            stale_removed: Number(raw.stale_removed || 0),
            overflow_removed: Number(raw.overflow_removed || 0),
            blocked_protected: Number(raw.blocked_protected || 0),
            archived_total: Number(raw.archived_total || 0),
            max_entries: Number(raw.max_entries || 0),
            max_age_days: Number(raw.max_age_days || 0),
          };
        } catch (_error) {
          return null;
        }
      }
      function setPresetCleanupReport(scope, report, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return null;
        const key = presetCleanupReportStorageKey(cleanScope, options.namespace);
        if (!key) return null;
        const payload = {
          ts: String(report && report.ts ? report.ts : new Date().toISOString()),
          namespace: normalizePresetNamespace(options.namespace),
          scope: cleanScope,
          before: Number(report && report.before ? report.before : 0),
          kept: Number(report && report.kept ? report.kept : 0),
          removed: Number(report && report.removed ? report.removed : 0),
          stale_removed: Number(report && report.stale_removed ? report.stale_removed : 0),
          overflow_removed: Number(report && report.overflow_removed ? report.overflow_removed : 0),
          blocked_protected: Number(report && report.blocked_protected ? report.blocked_protected : 0),
          archived_total: Number(report && report.archived_total ? report.archived_total : 0),
          max_entries: Number(report && report.max_entries ? report.max_entries : 0),
          max_age_days: Number(report && report.max_age_days ? report.max_age_days : 0),
        };
        localStorage.setItem(key, JSON.stringify(payload));
        return payload;
      }
      function protectedPresetNameSet(scope) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return new Set();
        const templates = presetProfileTemplates(cleanScope);
        const names = templates
          .map((item) => normalizePresetName(item && item.name))
          .filter((item) => !!item)
          .map((item) => String(item).toLowerCase());
        return new Set(names);
      }
      function getPresetProtectionState(scope, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const namespace = normalizePresetNamespace(options.namespace);
        const key = presetPolicyLockStorageKey(cleanScope, namespace);
        let locked = true;
        try {
          if (key) {
            const raw = JSON.parse(localStorage.getItem(key) || "{}");
            if (raw && typeof raw === "object" && typeof raw.locked === "boolean") {
              locked = raw.locked;
            }
          }
        } catch (_error) {}
        const protectedSet = protectedPresetNameSet(cleanScope);
        const protectedNames = Array.from(protectedSet.values()).sort((left, right) => left.localeCompare(right));
        return {
          scope: cleanScope,
          namespace,
          locked,
          protected_total: protectedNames.length,
          protected_names: protectedNames,
        };
      }
      function setPresetProtectionLock(scope, locked, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const namespace = normalizePresetNamespace(options.namespace);
        const key = presetPolicyLockStorageKey(cleanScope, namespace);
        const payload = {
          ts: new Date().toISOString(),
          namespace,
          scope: cleanScope,
          locked: !!locked,
        };
        if (key) localStorage.setItem(key, JSON.stringify(payload));
        appendPresetTimeline(cleanScope, payload.locked ? "policy_lock" : "policy_unlock", {
          locked: payload.locked,
        }, { namespace });
        return {
          ...payload,
          protected_total: getPresetProtectionState(cleanScope, { namespace }).protected_total,
        };
      }
      function isPresetProtectedName(scope, name) {
        const cleanName = normalizePresetName(name);
        if (!cleanName) return false;
        return protectedPresetNameSet(scope).has(String(cleanName).toLowerCase());
      }
      function isProtectedOperationBlocked(scope, name, options = {}) {
        if (!isPresetProtectedName(scope, name)) return false;
        if (!!options.allowProtectedWrite) return false;
        const protection = getPresetProtectionState(scope, options);
        return !!protection.locked;
      }
      function listPresetTimeline(scope, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return [];
        const key = presetTimelineStorageKey(cleanScope, options.namespace);
        if (!key) return [];
        try {
          const raw = JSON.parse(localStorage.getItem(key) || "[]");
          const limitRaw = Number(options.limit ?? 50);
          const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(400, limitRaw) : 50;
          return normalizePresetTimelineList(raw).slice(0, limit);
        } catch (_error) {
          return [];
        }
      }
      function storePresetTimeline(scope, entries, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return [];
        const key = presetTimelineStorageKey(cleanScope, options.namespace);
        if (!key) return [];
        const normalized = normalizePresetTimelineList(entries).slice(0, 400);
        localStorage.setItem(key, JSON.stringify(normalized));
        return normalized;
      }
      function appendPresetTimeline(scope, action, details = {}, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return null;
        const cleanAction = String(action || "").trim().toLowerCase();
        if (!cleanAction) return null;
        const namespace = normalizePresetNamespace(options.namespace);
        const payload = details && typeof details === "object" ? details : {};
        const entry = {
          ts: new Date().toISOString(),
          action: cleanAction,
          scope: cleanScope,
          namespace,
          details: payload,
        };
        const next = storePresetTimeline(cleanScope, [entry, ...listPresetTimeline(cleanScope, { namespace, limit: 400 })], { namespace });
        return next[0] || entry;
      }
      function clearPresetTimeline(scope, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) return 0;
        const key = presetTimelineStorageKey(cleanScope, options.namespace);
        if (!key) return 0;
        const before = listPresetTimeline(cleanScope, { namespace: options.namespace, limit: 400 }).length;
        try { localStorage.removeItem(key); } catch (_error) {}
        return before;
      }
      function getPresetRolloutLast(options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const key = presetRolloutLastStorageKey(namespace);
        try {
          const raw = JSON.parse(localStorage.getItem(key) || "{}");
          if (!raw || typeof raw !== "object") return null;
          return {
            ts: String(raw.ts || ""),
            namespace,
            mode: String(raw.mode || "merge"),
            scopes: normalizeScopeList(raw.scopes, []),
            summary: raw.summary && typeof raw.summary === "object" ? raw.summary : {},
            postcheck: Array.isArray(raw.postcheck) ? raw.postcheck.map((item) => String(item || "")).filter((item) => !!item) : [],
            checklist: Array.isArray(raw.checklist) ? raw.checklist.map((item) => String(item || "")).filter((item) => !!item) : [],
          };
        } catch (_error) {
          return null;
        }
      }
      function setPresetRolloutLast(record, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace || (record && record.namespace));
        const key = presetRolloutLastStorageKey(namespace);
        const payload = {
          ts: String(record && record.ts || new Date().toISOString()),
          namespace,
          mode: String(record && record.mode || "merge"),
          scopes: normalizeScopeList(record && record.scopes, []),
          summary: record && record.summary && typeof record.summary === "object" ? record.summary : {},
          postcheck: Array.isArray(record && record.postcheck) ? record.postcheck.map((item) => String(item || "")).filter((item) => !!item) : [],
          checklist: Array.isArray(record && record.checklist) ? record.checklist.map((item) => String(item || "")).filter((item) => !!item) : [],
        };
        try { localStorage.setItem(key, JSON.stringify(payload)); } catch (_error) {}
        return payload;
      }
      function buildPresetTimelineSummary(scope, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const namespace = normalizePresetNamespace(options.namespace);
        const items = listPresetTimeline(cleanScope, { namespace, limit: 1 });
        const last = items.length > 0 ? items[0] : null;
        return {
          scope: cleanScope,
          namespace,
          count: listPresetTimeline(cleanScope, { namespace, limit: 400 }).length,
          last_action: last ? String(last.action || "") : "",
          last_ts: last ? String(last.ts || "") : "",
          last_details: last && last.details && typeof last.details === "object" ? last.details : {},
        };
      }
      function buildPresetTimelineBundle(options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const scopes = Array.isArray(options.scopes) && options.scopes.length
          ? options.scopes.map((item) => String(item || "").trim().toLowerCase()).filter((item) => !!item)
          : listPresetScopes({ namespace });
        const resultScopes = scopes.map((scope) => ({
          summary: buildPresetTimelineSummary(scope, { namespace }),
          entries: listPresetTimeline(scope, { namespace, limit: 30 }),
        }));
        let total = 0;
        let lastTs = "";
        for (const item of resultScopes) {
          total += Number(item.summary && item.summary.count ? item.summary.count : 0);
          const ts = String(item.summary && item.summary.last_ts ? item.summary.last_ts : "");
          if (ts && (!lastTs || ts > lastTs)) lastTs = ts;
        }
        return {
          generated_at: new Date().toISOString(),
          namespace,
          scopes: resultScopes,
          summary: {
            scope_count: resultScopes.length,
            entries_total: total,
            last_ts: lastTs,
          },
        };
      }
      function savePreset(scope, name, data, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        const namespace = normalizePresetNamespace(options.namespace);
        const cleanName = normalizePresetName(name);
        if (!cleanName) throw new Error("preset_name_required");
        const exists = listPresets(cleanScope, { namespace })
          .some((item) => String(item.name || "").toLowerCase() === cleanName.toLowerCase());
        if (exists && isProtectedOperationBlocked(cleanScope, cleanName, { namespace, allowProtectedWrite: options.allowProtectedWrite })) {
          throw new Error("preset_protected_locked");
        }
        const current = listPresets(cleanScope, { namespace }).filter((item) => String(item.name).toLowerCase() !== cleanName.toLowerCase());
        const next = [{ name: cleanName, data: data && typeof data === "object" ? data : {}, ts: new Date().toISOString() }, ...current];
        const stored = storePresets(cleanScope, next, { namespace });
        appendPresetTimeline(cleanScope, "save_preset", { name: cleanName, total: stored.length }, { namespace });
        return stored;
      }
      function deletePreset(scope, name, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        const namespace = normalizePresetNamespace(options.namespace);
        const cleanName = normalizePresetName(name);
        if (!cleanName) return listPresets(cleanScope, { namespace });
        const current = listPresets(cleanScope, { namespace });
        const existed = current.some((item) => String(item.name).toLowerCase() === cleanName.toLowerCase());
        if (existed && isProtectedOperationBlocked(cleanScope, cleanName, { namespace, allowProtectedWrite: options.allowProtectedWrite })) {
          throw new Error("preset_protected_locked");
        }
        const next = current.filter((item) => String(item.name).toLowerCase() !== cleanName.toLowerCase());
        const stored = storePresets(cleanScope, next, { namespace });
        if (existed) appendPresetTimeline(cleanScope, "delete_preset", { name: cleanName, total: stored.length }, { namespace });
        return stored;
      }
      function getPreset(scope, name, options = {}) {
        const cleanName = normalizePresetName(name);
        if (!cleanName) return null;
        return listPresets(scope, options).find((item) => String(item.name).toLowerCase() === cleanName.toLowerCase()) || null;
      }
      function mergePresetLists(current, incoming, mode = "merge") {
        const normalizedMode = String(mode || "").trim().toLowerCase() === "replace" ? "replace" : "merge";
        if (normalizedMode === "replace") return dedupePresetList(incoming);
        const left = dedupePresetList(incoming);
        const right = dedupePresetList(current).filter((item) => {
          const incomingKeySet = new Set(left.map((entry) => String(entry.name || "").toLowerCase()));
          return !incomingKeySet.has(String(item.name || "").toLowerCase());
        });
        return dedupePresetList([...left, ...right]);
      }
      function stableSerialize(value) {
        if (value === null || value === undefined) return "null";
        if (typeof value === "number" || typeof value === "boolean") return JSON.stringify(value);
        if (typeof value === "string") return JSON.stringify(value);
        if (Array.isArray(value)) {
          return `[${value.map((item) => stableSerialize(item)).join(",")}]`;
        }
        if (typeof value === "object") {
          const keys = Object.keys(value).sort((left, right) => String(left).localeCompare(String(right)));
          const items = keys.map((key) => `${JSON.stringify(key)}:${stableSerialize(value[key])}`);
          return `{${items.join(",")}}`;
        }
        return JSON.stringify(String(value));
      }
      function simpleHash(text) {
        const source = String(text || "");
        let hash = 2166136261;
        for (let index = 0; index < source.length; index += 1) {
          hash ^= source.charCodeAt(index);
          hash = Math.imul(hash, 16777619);
        }
        return (hash >>> 0).toString(16).padStart(8, "0");
      }
      function presetPayloadHash(payload) {
        return simpleHash(stableSerialize(payload && typeof payload === "object" ? payload : {}));
      }
      function presetTsEpoch(ts) {
        const parsed = Date.parse(String(ts || ""));
        return Number.isFinite(parsed) ? parsed : 0;
      }
      function parsePresetImportPayload(rawText) {
        let parsed = {};
        try {
          parsed = JSON.parse(String(rawText || ""));
        } catch (_error) {
          throw new Error("preset_json_invalid");
        }
        if (!parsed || typeof parsed !== "object") throw new Error("preset_json_invalid");
        return parsed;
      }
      function normalizeScopeList(rawScopes, fallbackScopes = []) {
        const source = Array.isArray(rawScopes) ? rawScopes : [];
        const fallback = Array.isArray(fallbackScopes) ? fallbackScopes : [];
        const set = new Set();
        const pushValue = (value) => {
          const clean = String(value || "").trim().toLowerCase();
          if (!clean) return;
          set.add(clean);
        };
        for (const item of source) pushValue(item);
        if (set.size === 0) {
          for (const item of fallback) pushValue(item);
        }
        return Array.from(set.values()).sort((left, right) => left.localeCompare(right));
      }
      function normalizeActionList(rawActions, fallbackActions = []) {
        const source = Array.isArray(rawActions) ? rawActions : [];
        const fallback = Array.isArray(fallbackActions) ? fallbackActions : [];
        const set = new Set();
        const pushValue = (value) => {
          const clean = String(value || "").trim().toLowerCase();
          if (!clean) return;
          set.add(clean);
        };
        for (const item of source) pushValue(item);
        if (set.size === 0) {
          for (const item of fallback) pushValue(item);
        }
        return Array.from(set.values()).sort((left, right) => left.localeCompare(right));
      }
      function extractIncomingPresetsByScope(parsed, scope) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const kind = String(parsed && parsed.kind || "");
        if (kind === "passengers.presets.bundle.v1") {
          const scopesMap = parsed && typeof parsed.scopes === "object" && parsed.scopes ? parsed.scopes : {};
          const rawScope = scopesMap[cleanScope];
          const payload = rawScope && typeof rawScope === "object" ? rawScope : {};
          return {
            source_kind: "bundle",
            incoming: dedupePresetList(Array.isArray(rawScope) ? rawScope : payload.presets),
          };
        }
        const parsedScope = String(parsed && parsed.scope || "").trim().toLowerCase();
        if (parsedScope && parsedScope !== cleanScope) throw new Error("preset_scope_mismatch");
        return {
          source_kind: "scope",
          incoming: dedupePresetList(parsed && parsed.presets),
        };
      }
      function buildPresetMergePreview(scope, current, incoming, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const mode = String(options.mode || "merge").trim().toLowerCase() === "replace" ? "replace" : "merge";
        const protectionState = options && typeof options.protection === "object" && options.protection
          ? options.protection
          : { locked: false, protected_names: [] };
        const protectedSet = new Set(
          (Array.isArray(protectionState.protected_names) ? protectionState.protected_names : [])
            .map((item) => String(item || "").trim().toLowerCase())
            .filter((item) => !!item)
        );
        const protectionLocked = !!protectionState.locked;
        const currentList = dedupePresetList(current);
        const incomingList = dedupePresetList(incoming);
        const currentMap = new Map(currentList.map((item) => [String(item.name || "").toLowerCase(), item]));
        const incomingMap = new Map(incomingList.map((item) => [String(item.name || "").toLowerCase(), item]));
        const entries = [];
        const summary = {
          create: 0,
          update: 0,
          refresh_ts: 0,
          skip: 0,
          conflicts: 0,
          drop: 0,
          keep_existing: 0,
          protected_touched: 0,
          protected_blocked: 0,
          result_total: 0,
        };
        for (const item of incomingList) {
          const key = String(item.name || "").toLowerCase();
          const isProtected = protectedSet.has(key);
          const currentItem = currentMap.get(key) || null;
          const incomingHash = presetPayloadHash(item.data || {});
          const incomingTs = presetTsEpoch(item.ts);
          if (!currentItem) {
            entries.push({
              name: String(item.name || ""),
              action: "create",
              conflict: false,
              incoming_ts: String(item.ts || ""),
              current_ts: "",
              incoming_hash: incomingHash,
              current_hash: "",
              protected: isProtected,
              blocked: false,
            });
            if (isProtected) summary.protected_touched += 1;
            summary.create += 1;
            continue;
          }
          const currentHash = presetPayloadHash(currentItem.data || {});
          const currentTs = presetTsEpoch(currentItem.ts);
          if (incomingHash === currentHash) {
            if (incomingTs > 0 && currentTs > 0 && incomingTs > currentTs) {
              entries.push({
                name: String(item.name || ""),
                action: "refresh_ts",
                conflict: false,
                incoming_ts: String(item.ts || ""),
                current_ts: String(currentItem.ts || ""),
                incoming_hash: incomingHash,
                current_hash: currentHash,
                protected: isProtected,
                blocked: false,
              });
              if (isProtected) summary.protected_touched += 1;
              summary.refresh_ts += 1;
            } else {
              entries.push({
                name: String(item.name || ""),
                action: "skip_same",
                conflict: false,
                incoming_ts: String(item.ts || ""),
                current_ts: String(currentItem.ts || ""),
                incoming_hash: incomingHash,
                current_hash: currentHash,
                protected: isProtected,
                blocked: false,
              });
              if (isProtected) summary.protected_touched += 1;
              summary.skip += 1;
            }
            continue;
          }
          let conflict = false;
          let action = "update";
          if (incomingTs > 0 && currentTs > 0 && incomingTs <= currentTs) {
            conflict = true;
            action = incomingTs === currentTs ? "conflict_same_ts" : "conflict_older";
          } else if (!incomingTs || !currentTs) {
            conflict = true;
            action = "conflict_unknown_ts";
          }
          const blocked = isProtected && protectionLocked;
          entries.push({
            name: String(item.name || ""),
            action,
            conflict,
            incoming_ts: String(item.ts || ""),
            current_ts: String(currentItem.ts || ""),
            incoming_hash: incomingHash,
            current_hash: currentHash,
            protected: isProtected,
            blocked,
          });
          summary.update += 1;
          if (isProtected) summary.protected_touched += 1;
          if (blocked) summary.protected_blocked += 1;
          if (conflict) summary.conflicts += 1;
        }
        if (mode === "replace") {
          for (const item of currentList) {
            const key = String(item.name || "").toLowerCase();
            if (incomingMap.has(key)) continue;
            const isProtected = protectedSet.has(key);
            const blocked = isProtected && protectionLocked;
            entries.push({
              name: String(item.name || ""),
              action: "drop_missing",
              conflict: false,
              incoming_ts: "",
              current_ts: String(item.ts || ""),
              incoming_hash: "",
              current_hash: presetPayloadHash(item.data || {}),
              protected: isProtected,
              blocked,
            });
            if (isProtected) summary.protected_touched += 1;
            if (blocked) summary.protected_blocked += 1;
            summary.drop += 1;
          }
        } else {
          for (const item of currentList) {
            const key = String(item.name || "").toLowerCase();
            if (incomingMap.has(key)) continue;
            summary.keep_existing += 1;
          }
        }
        summary.result_total = mode === "replace"
          ? incomingList.length
          : currentList.length + summary.create;
        return {
          scope: cleanScope,
          mode,
          current_total: currentList.length,
          incoming_total: incomingList.length,
          protection: {
            locked: protectionLocked,
            protected_total: protectedSet.size,
          },
          summary,
          entries,
        };
      }
      function simulatePresetImport(scope, rawText, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const namespace = normalizePresetNamespace(options.namespace);
        const mode = String(options.mode || "merge").trim().toLowerCase() === "replace" ? "replace" : "merge";
        const parsed = parsePresetImportPayload(rawText);
        const extracted = extractIncomingPresetsByScope(parsed, cleanScope);
        const protection = getPresetProtectionState(cleanScope, { namespace });
        const preview = buildPresetMergePreview(
          cleanScope,
          listPresets(cleanScope, { namespace }),
          extracted.incoming,
          { mode, protection }
        );
        return {
          kind: "passengers.presets.preview.scope.v1",
          generated_at: new Date().toISOString(),
          namespace,
          source_kind: extracted.source_kind,
          ...preview,
        };
      }
      function simulatePresetBundleImport(rawText, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const mode = String(options.mode || "merge").trim().toLowerCase() === "replace" ? "replace" : "merge";
        const parsed = parsePresetImportPayload(rawText);
        if (String(parsed && parsed.kind || "") !== "passengers.presets.bundle.v1") {
          throw new Error("preset_bundle_required");
        }
        const scopesMap = parsed && typeof parsed.scopes === "object" && parsed.scopes ? parsed.scopes : {};
        const requestedScopes = Array.isArray(options.scopes) && options.scopes.length
          ? options.scopes.map((item) => String(item || "").trim().toLowerCase()).filter((item) => !!item)
          : Object.keys(scopesMap).map((item) => String(item || "").trim().toLowerCase()).filter((item) => !!item);
        const scopes = requestedScopes.map((scope) => {
          const rawScope = scopesMap[scope];
          const payload = rawScope && typeof rawScope === "object" ? rawScope : {};
          const incoming = dedupePresetList(Array.isArray(rawScope) ? rawScope : payload.presets);
          const protection = getPresetProtectionState(scope, { namespace });
          return buildPresetMergePreview(scope, listPresets(scope, { namespace }), incoming, { mode, protection });
        });
        const summary = {
          create: 0,
          update: 0,
          refresh_ts: 0,
          skip: 0,
          conflicts: 0,
          drop: 0,
          keep_existing: 0,
          protected_touched: 0,
          protected_blocked: 0,
          result_total: 0,
          scope_count: scopes.length,
        };
        for (const scopePreview of scopes) {
          const scopeSummary = scopePreview && scopePreview.summary ? scopePreview.summary : {};
          summary.create += Number(scopeSummary.create || 0);
          summary.update += Number(scopeSummary.update || 0);
          summary.refresh_ts += Number(scopeSummary.refresh_ts || 0);
          summary.skip += Number(scopeSummary.skip || 0);
          summary.conflicts += Number(scopeSummary.conflicts || 0);
          summary.drop += Number(scopeSummary.drop || 0);
          summary.keep_existing += Number(scopeSummary.keep_existing || 0);
          summary.protected_touched += Number(scopeSummary.protected_touched || 0);
          summary.protected_blocked += Number(scopeSummary.protected_blocked || 0);
          summary.result_total += Number(scopeSummary.result_total || 0);
        }
        return {
          kind: "passengers.presets.preview.bundle.v1",
          generated_at: new Date().toISOString(),
          namespace,
          mode,
          scopes,
          summary,
        };
      }
      function buildPresetOperationsSummary(options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const scopes = normalizeScopeList(
          options.scopes,
          Array.from(
            new Set([
              ...listPresetScopes({ namespace: "local" }),
              ...listPresetScopes({ namespace: "shared" }),
            ])
          )
        );
        const rows = scopes.map((scope) => {
          const protection = getPresetProtectionState(scope, { namespace });
          const observability = buildPresetScopeObservability(scope);
          const timeline = buildPresetTimelineSummary(scope, { namespace });
          return {
            scope,
            namespace,
            locked: !!protection.locked,
            protected_total: Number(protection.protected_total || 0),
            total: namespace === "shared" ? Number(observability.shared_total || 0) : Number(observability.local_total || 0),
            archived_total: namespace === "shared" ? Number(observability.shared_archived_total || 0) : Number(observability.local_archived_total || 0),
            timeline_count: Number(timeline.count || 0),
            timeline_last_ts: String(timeline.last_ts || ""),
          };
        });
        const summary = {
          scope_count: rows.length,
          locked_count: rows.filter((item) => item.locked).length,
          protected_total: 0,
          presets_total: 0,
          archived_total: 0,
          timeline_total: 0,
          timeline_last_ts: "",
        };
        for (const row of rows) {
          summary.protected_total += Number(row.protected_total || 0);
          summary.presets_total += Number(row.total || 0);
          summary.archived_total += Number(row.archived_total || 0);
          summary.timeline_total += Number(row.timeline_count || 0);
          if (row.timeline_last_ts && (!summary.timeline_last_ts || row.timeline_last_ts > summary.timeline_last_ts)) {
            summary.timeline_last_ts = row.timeline_last_ts;
          }
        }
        return {
          generated_at: new Date().toISOString(),
          namespace,
          scopes: rows,
          summary,
        };
      }
      function buildPresetCockpitTimeline(options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const availableScopes = Array.from(new Set([
          ...listPresetScopes({ namespace: "local" }),
          ...listPresetScopes({ namespace: "shared" }),
        ]));
        const scopes = normalizeScopeList(options.scopes, availableScopes);
        const requestedActions = normalizeActionList(options.actions, []);
        const actionFilter = new Set(requestedActions);
        const limitRaw = Number(options.limit ?? 120);
        const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(400, limitRaw) : 120;
        const allEntries = [];
        for (const scope of scopes) {
          const entries = listPresetTimeline(scope, { namespace, limit: 400 });
          for (const entry of entries) {
            allEntries.push({
              ts: String(entry && entry.ts || ""),
              action: String(entry && entry.action || "").trim().toLowerCase(),
              scope: String(entry && entry.scope || scope).trim().toLowerCase(),
              namespace,
              details: entry && entry.details && typeof entry.details === "object" ? entry.details : {},
            });
          }
        }
        allEntries.sort((left, right) => String(right.ts || "").localeCompare(String(left.ts || "")));
        const filtered = allEntries.filter((entry) => actionFilter.size === 0 || actionFilter.has(entry.action));
        const visible = filtered.slice(0, limit);
        const scopeCounters = {};
        const actionCounters = {};
        for (const entry of filtered) {
          const scope = String(entry.scope || "");
          const action = String(entry.action || "");
          scopeCounters[scope] = Number(scopeCounters[scope] || 0) + 1;
          actionCounters[action] = Number(actionCounters[action] || 0) + 1;
        }
        return {
          generated_at: new Date().toISOString(),
          namespace,
          scopes,
          actions: requestedActions,
          limit,
          entries: visible,
          counters: {
            scope: scopeCounters,
            action: actionCounters,
          },
          summary: {
            scope_count: scopes.length,
            action_count: Object.keys(actionCounters).length,
            entries_total: allEntries.length,
            filtered_total: filtered.length,
            visible_total: visible.length,
            last_ts: visible.length > 0 ? String(visible[0].ts || "") : "",
            last_action: visible.length > 0 ? String(visible[0].action || "") : "",
          },
        };
      }
      function buildPresetRolloutAssistant(rawText, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const mode = String(options.mode || "merge").trim().toLowerCase() === "replace" ? "replace" : "merge";
        const requestedScopes = normalizeScopeList(options.scopes, []);
        const preview = simulatePresetOperations(rawText, {
          namespace,
          mode,
          scopes: requestedScopes,
          scope: options.scope,
        });
        const previewScopes = Array.isArray(preview && preview.scopes) ? preview.scopes : [];
        const scopes = requestedScopes.length > 0
          ? requestedScopes
          : normalizeScopeList(previewScopes.map((item) => item && item.scope), []);
        const summary = preview && preview.summary && typeof preview.summary === "object" ? preview.summary : {};
        const operations = buildPresetOperationsSummary({ namespace, scopes });
        const rollbackBundle = exportPresetBundle({ namespace, scopes });
        const checklist = [
          "Підтвердіть namespace і scopes для rollout",
          "Перевірте conflicts/drop/protected_blocked у dry-run summary",
          "Збережіть rollback bundle JSON перед apply",
          "Погодьте вікно внесення змін для операторів",
          "Підготуйте post-check: cockpit timeline + monitor/alerts/incidents",
        ];
        const postcheck = [
          "Перевірити Cockpit timeline panel: останній запис rollout_assistant_apply",
          "Перевірити /admin/fleet: monitor cards і stale/pending індикатори",
          "Перевірити /admin/fleet/alerts: критичні/попередження після rollout",
          "Перевірити /admin/fleet/incidents: статуси open/acked/silenced",
        ];
        return {
          kind: "passengers.presets.rollout.plan.v1",
          generated_at: new Date().toISOString(),
          namespace,
          mode,
          scopes,
          summary,
          operations_summary: operations.summary || {},
          preview,
          checklist,
          rollback_hint: {
            kind: "passengers.presets.rollback.bundle.v1",
            note: "Збережіть цей JSON до apply; для rollback імпортуйте bundle у режимі replace.",
            bundle_json: rollbackBundle,
          },
          postcheck,
        };
      }
      function applyPresetRolloutAssistant(rawText, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const mode = String(options.mode || "merge").trim().toLowerCase() === "replace" ? "replace" : "merge";
        const requestedScopes = normalizeScopeList(options.scopes, []);
        const allowProtectedWrite = !!options.allowProtectedWrite;
        const plan = buildPresetRolloutAssistant(rawText, {
          namespace,
          mode,
          scopes: requestedScopes,
          scope: options.scope,
        });
        const scopes = normalizeScopeList(plan.scopes, requestedScopes);
        const result = applyPresetOperations(rawText, {
          namespace,
          mode,
          scopes,
          scope: options.scope,
          allowProtectedWrite,
        });
        const rolloutSummary = {
          ts: new Date().toISOString(),
          namespace,
          mode,
          scopes,
          summary: {
            preview: plan.summary || {},
            result: result && result.result ? result.result : {},
            source_kind: String(result && result.source_kind || ""),
          },
          checklist: plan.checklist || [],
          postcheck: plan.postcheck || [],
        };
        setPresetRolloutLast(rolloutSummary, { namespace });
        for (const scope of scopes) {
          appendPresetTimeline(scope, "rollout_assistant_apply", {
            mode,
            scopes: scopes.length,
            imported: result && result.result ? Number(result.result.imported || 0) : 0,
            total: result && result.result ? Number(result.result.total || 0) : 0,
            conflicts: Number(plan.summary && plan.summary.conflicts || 0),
            protected_blocked: Number(plan.summary && plan.summary.protected_blocked || 0),
          }, { namespace });
        }
        return {
          kind: "passengers.presets.rollout.apply.v1",
          generated_at: new Date().toISOString(),
          namespace,
          mode,
          scopes,
          plan,
          result,
          rollout_summary: rolloutSummary,
        };
      }
      function simulatePresetOperations(rawText, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const mode = String(options.mode || "merge").trim().toLowerCase() === "replace" ? "replace" : "merge";
        const parsed = parsePresetImportPayload(rawText);
        const kind = String(parsed && parsed.kind || "");
        if (kind === "passengers.presets.bundle.v1") {
          const preview = simulatePresetBundleImport(rawText, {
            namespace,
            mode,
            scopes: options.scopes,
          });
          return {
            kind: "passengers.presets.cockpit.preview.v1",
            generated_at: new Date().toISOString(),
            namespace,
            mode,
            source_kind: "bundle",
            scopes: preview.scopes,
            summary: preview.summary,
          };
        }
        const fallbackScope = String(parsed && parsed.scope || options.scope || "").trim().toLowerCase();
        if (!fallbackScope) throw new Error("preset_scope_required");
        const scopePreview = simulatePresetImport(fallbackScope, rawText, { namespace, mode });
        return {
          kind: "passengers.presets.cockpit.preview.v1",
          generated_at: new Date().toISOString(),
          namespace,
          mode,
          source_kind: "scope",
          scopes: [scopePreview],
          summary: {
            ...(scopePreview.summary || {}),
            scope_count: 1,
          },
        };
      }
      function applyPresetOperations(rawText, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const mode = String(options.mode || "merge").trim().toLowerCase() === "replace" ? "replace" : "merge";
        const allowProtectedWrite = !!options.allowProtectedWrite;
        const preview = simulatePresetOperations(rawText, {
          namespace,
          mode,
          scopes: options.scopes,
          scope: options.scope,
        });
        if (Number(preview.summary && preview.summary.protected_blocked ? preview.summary.protected_blocked : 0) > 0 && !allowProtectedWrite) {
          throw new Error("preset_protected_locked");
        }
        const parsed = parsePresetImportPayload(rawText);
        const kind = String(parsed && parsed.kind || "");
        if (kind === "passengers.presets.bundle.v1") {
          const result = importPresetBundle(rawText, {
            namespace,
            mode,
            allowProtectedWrite,
            scopes: options.scopes,
          });
          return {
            kind: "passengers.presets.cockpit.apply.v1",
            generated_at: new Date().toISOString(),
            namespace,
            mode,
            source_kind: "bundle",
            preview_summary: preview.summary,
            result,
          };
        }
        const scope = String(parsed && parsed.scope || options.scope || "").trim().toLowerCase();
        if (!scope) throw new Error("preset_scope_required");
        const result = importPresets(scope, rawText, {
          namespace,
          mode,
          allowProtectedWrite,
        });
        return {
          kind: "passengers.presets.cockpit.apply.v1",
          generated_at: new Date().toISOString(),
          namespace,
          mode,
          source_kind: "scope",
          preview_summary: preview.summary,
          result,
        };
      }
      function setPresetProtectionLockBatch(scopes, locked, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const cleanScopes = normalizeScopeList(scopes, []);
        const results = [];
        for (const scope of cleanScopes) {
          results.push(setPresetProtectionLock(scope, locked, { namespace }));
        }
        return {
          generated_at: new Date().toISOString(),
          namespace,
          locked: !!locked,
          scopes: results,
          summary: {
            scope_count: results.length,
            locked_count: results.filter((item) => !!item.locked).length,
          },
        };
      }
      function presetProfileTemplates(scope) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (cleanScope === "fleet") {
          return [
            { name: "profile-critical-nodes", data: { q: "", alertCentral: "", alertCode: "", severity: "bad", includeSilenced: false, onlyAlerts: true, opsWindow: "24h" } },
            { name: "profile-wg-stale", data: { q: "", alertCentral: "", alertCode: "wg_stale", severity: "all", includeSilenced: false, onlyAlerts: true, opsWindow: "24h" } },
            { name: "profile-pending-queue", data: { q: "", alertCentral: "", alertCode: "pending_batches_high", severity: "all", includeSilenced: false, onlyAlerts: true, opsWindow: "24h" } },
          ];
        }
        if (cleanScope === "fleet_alerts") {
          return [
            { name: "profile-alerts-critical", data: { q: "", central: "", code: "", severity: "bad", includeSilenced: false } },
            { name: "profile-alerts-warn", data: { q: "", central: "", code: "", severity: "warn", includeSilenced: false } },
            { name: "profile-alerts-silenced", data: { q: "", central: "", code: "", severity: "all", includeSilenced: true } },
          ];
        }
        if (cleanScope === "fleet_incidents") {
          return [
            { name: "profile-inc-open", data: { central: "", code: "", q: "", status: "open", severity: "all", slaOnly: false, includeResolved: false } },
            { name: "profile-inc-sla", data: { central: "", code: "", q: "", status: "all", severity: "all", slaOnly: true, includeResolved: false } },
            { name: "profile-inc-critical", data: { central: "", code: "", q: "", status: "all", severity: "bad", slaOnly: false, includeResolved: false } },
          ];
        }
        return [];
      }
      function installPresetProfiles(scope, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const templates = presetProfileTemplates(cleanScope);
        const namespace = normalizePresetNamespace(options.namespace);
        const overwrite = !!options.overwrite;
        const allowProtectedWrite = !!options.allowProtectedWrite;
        const existing = listPresets(cleanScope, { namespace });
        const existingMap = new Map(existing.map((item) => [String(item.name || "").toLowerCase(), item]));
        let installed = 0;
        let skippedProtected = 0;
        for (const template of templates) {
          const cleanName = normalizePresetName(template && template.name);
          if (!cleanName) continue;
          const key = cleanName.toLowerCase();
          if (!overwrite && existingMap.has(key)) continue;
          if (overwrite && existingMap.has(key) && isProtectedOperationBlocked(cleanScope, cleanName, { namespace, allowProtectedWrite })) {
            skippedProtected += 1;
            continue;
          }
          existingMap.set(key, { name: cleanName, data: template && template.data ? template.data : {}, ts: new Date().toISOString() });
          installed += 1;
        }
        const merged = dedupePresetList(Array.from(existingMap.values()));
        storePresets(cleanScope, merged, { namespace });
        const result = { scope: cleanScope, namespace, installed, total: merged.length, templates: templates.length, skipped_protected: skippedProtected };
        appendPresetTimeline(cleanScope, "install_profiles", result, { namespace });
        return result;
      }
      function cleanupPresets(scope, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const namespace = normalizePresetNamespace(options.namespace);
        const allowProtectedWrite = !!options.allowProtectedWrite;
        const maxEntriesRaw = Number(options.maxEntries ?? 20);
        const maxEntries = Number.isFinite(maxEntriesRaw) && maxEntriesRaw > 0 ? Math.min(100, maxEntriesRaw) : 20;
        const maxAgeDaysRaw = Number(options.maxAgeDays ?? 30);
        const maxAgeDays = Number.isFinite(maxAgeDaysRaw) && maxAgeDaysRaw > 0 ? Math.min(3650, maxAgeDaysRaw) : 30;
        const archive = options.archive !== false;
        const nowTs = Date.now();
        const maxAgeMs = maxAgeDays * 24 * 3600 * 1000;
        const current = listPresets(cleanScope, { namespace });
        const stale = [];
        const fresh = [];
        for (const item of current) {
          const ts = Date.parse(String(item.ts || ""));
          if (Number.isFinite(ts) && nowTs - ts > maxAgeMs) stale.push(item);
          else fresh.push(item);
        }
        const kept = fresh.slice(0, maxEntries);
        const overflow = fresh.slice(maxEntries);
        const removed = [...stale, ...overflow];
        let blockedProtected = 0;
        if (!allowProtectedWrite) {
          const locked = getPresetProtectionState(cleanScope, { namespace }).locked;
          if (locked) {
            const removable = [];
            const keptProtected = [];
            for (const item of removed) {
              if (isPresetProtectedName(cleanScope, item && item.name)) {
                keptProtected.push(item);
              } else {
                removable.push(item);
              }
            }
            blockedProtected = keptProtected.length;
            if (keptProtected.length > 0) {
              removed.length = 0;
              for (const item of removable) removed.push(item);
              for (const item of keptProtected) kept.push(item);
            }
          }
        }
        storePresets(cleanScope, kept, { namespace });
        let archivedTotal = 0;
        if (archive && removed.length > 0) {
          const existingArchive = listPresetArchive(cleanScope, { namespace, limit: 500 });
          const updatedArchive = storePresetArchive(cleanScope, [...removed, ...existingArchive], { namespace });
          archivedTotal = updatedArchive.length;
        } else {
          archivedTotal = listPresetArchive(cleanScope, { namespace, limit: 500 }).length;
        }
        const result = {
          scope: cleanScope,
          namespace,
          before: current.length,
          kept: kept.length,
          removed: removed.length,
          stale_removed: stale.length,
          overflow_removed: overflow.length,
          blocked_protected: blockedProtected,
          archived_total: archivedTotal,
          max_entries: maxEntries,
          max_age_days: maxAgeDays,
        };
        setPresetCleanupReport(cleanScope, result, { namespace });
        appendPresetTimeline(cleanScope, "cleanup_presets", result, { namespace });
        return result;
      }
      function buildPresetMetrics(scope, options = {}) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const namespace = normalizePresetNamespace(options.namespace);
        const presets = listPresets(cleanScope, { namespace });
        const archive = listPresetArchive(cleanScope, { namespace, limit: 500 });
        const cleanup = getPresetCleanupReport(cleanScope, { namespace });
        const latestTs = presets.length > 0 ? String(presets[0].ts || "") : "";
        const oldestTs = presets.length > 0 ? String(presets[presets.length - 1].ts || "") : "";
        return {
          scope: cleanScope,
          namespace,
          total: presets.length,
          archived_total: archive.length,
          latest_ts: latestTs,
          oldest_ts: oldestTs,
          last_cleanup_ts: cleanup ? String(cleanup.ts || "") : "",
          last_cleanup_removed: cleanup ? Number(cleanup.removed || 0) : 0,
          last_cleanup_kept: cleanup ? Number(cleanup.kept || 0) : presets.length,
          last_cleanup_archived_total: cleanup ? Number(cleanup.archived_total || archive.length) : archive.length,
        };
      }
      function buildPresetMetricsBundle(options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const scopes = Array.isArray(options.scopes) && options.scopes.length
          ? options.scopes.map((item) => String(item || "").trim().toLowerCase()).filter((item) => !!item)
          : listPresetScopes({ namespace });
        const metrics = [];
        for (const scope of scopes) {
          try {
            metrics.push(buildPresetMetrics(scope, { namespace }));
          } catch (_error) {}
        }
        return metrics.sort((left, right) => String(left.scope || "").localeCompare(String(right.scope || "")));
      }
      function buildPresetScopeObservability(scope) {
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const local = buildPresetMetrics(cleanScope, { namespace: "local" });
        const shared = buildPresetMetrics(cleanScope, { namespace: "shared" });
        const cleanupCandidates = [String(local.last_cleanup_ts || ""), String(shared.last_cleanup_ts || "")]
          .filter((item) => !!item)
          .sort()
          .reverse();
        return {
          scope: cleanScope,
          total: Number(local.total || 0) + Number(shared.total || 0),
          local_total: Number(local.total || 0),
          shared_total: Number(shared.total || 0),
          archived_total: Number(local.archived_total || 0) + Number(shared.archived_total || 0),
          local_archived_total: Number(local.archived_total || 0),
          shared_archived_total: Number(shared.archived_total || 0),
          local_last_cleanup_ts: String(local.last_cleanup_ts || ""),
          shared_last_cleanup_ts: String(shared.last_cleanup_ts || ""),
          last_cleanup_ts: cleanupCandidates.length ? cleanupCandidates[0] : "",
          local_last_cleanup_removed: Number(local.last_cleanup_removed || 0),
          shared_last_cleanup_removed: Number(shared.last_cleanup_removed || 0),
        };
      }
      function buildPresetObservabilityBundle(options = {}) {
        const requestedScopes = Array.isArray(options.scopes) && options.scopes.length
          ? options.scopes.map((item) => String(item || "").trim().toLowerCase()).filter((item) => !!item)
          : [];
        const scopeSet = new Set();
        if (requestedScopes.length > 0) {
          for (const scope of requestedScopes) scopeSet.add(scope);
        } else {
          for (const scope of listPresetScopes({ namespace: "local" })) scopeSet.add(scope);
          for (const scope of listPresetScopes({ namespace: "shared" })) scopeSet.add(scope);
        }
        const scopes = Array.from(scopeSet.values())
          .sort((left, right) => String(left || "").localeCompare(String(right || "")))
          .map((scope) => buildPresetScopeObservability(scope));
        const summary = {
          scope_count: scopes.length,
          total: 0,
          local_total: 0,
          shared_total: 0,
          archived_total: 0,
          local_archived_total: 0,
          shared_archived_total: 0,
          last_cleanup_ts: "",
        };
        for (const item of scopes) {
          summary.total += Number(item.total || 0);
          summary.local_total += Number(item.local_total || 0);
          summary.shared_total += Number(item.shared_total || 0);
          summary.archived_total += Number(item.archived_total || 0);
          summary.local_archived_total += Number(item.local_archived_total || 0);
          summary.shared_archived_total += Number(item.shared_archived_total || 0);
        }
        const cleanupCandidates = scopes
          .map((item) => String(item.last_cleanup_ts || ""))
          .filter((item) => !!item)
          .sort()
          .reverse();
        summary.last_cleanup_ts = cleanupCandidates.length ? cleanupCandidates[0] : "";
        return {
          generated_at: new Date().toISOString(),
          scopes,
          summary,
        };
      }
      function exportPresets(scope, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const payload = {
          kind: "passengers.presets.scope.v1",
          exported_at: new Date().toISOString(),
          namespace,
          scope: cleanScope,
          presets: listPresets(cleanScope, { namespace }),
          archive: listPresetArchive(cleanScope, { namespace, limit: 200 }),
        };
        appendPresetTimeline(cleanScope, "export_presets", {
          presets: payload.presets.length,
          archive: payload.archive.length,
        }, { namespace });
        return JSON.stringify(payload, null, 2);
      }
      function exportPresetBundle(options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const scopes = Array.isArray(options.scopes) && options.scopes.length
          ? options.scopes.map((item) => String(item || "").trim().toLowerCase()).filter((item) => !!item)
          : listPresetScopes({ namespace });
        const bundleScopes = {};
        for (const scope of scopes) {
          bundleScopes[scope] = {
            presets: listPresets(scope, { namespace }),
            archive: listPresetArchive(scope, { namespace, limit: 200 }),
          };
        }
        const payload = {
          kind: "passengers.presets.bundle.v1",
          exported_at: new Date().toISOString(),
          namespace,
          scopes: bundleScopes,
        };
        for (const scope of Object.keys(bundleScopes)) {
          const bucket = bundleScopes[scope] || {};
          appendPresetTimeline(scope, "export_bundle", {
            presets: Array.isArray(bucket.presets) ? bucket.presets.length : 0,
            archive: Array.isArray(bucket.archive) ? bucket.archive.length : 0,
          }, { namespace });
        }
        return JSON.stringify(payload, null, 2);
      }
      function importPresets(scope, rawText, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const cleanScope = String(scope || "").trim().toLowerCase();
        if (!cleanScope) throw new Error("preset_scope_required");
        const mode = String(options.mode || "merge").trim().toLowerCase();
        const allowProtectedWrite = !!options.allowProtectedWrite;
        let parsed = {};
        try {
          parsed = JSON.parse(String(rawText || ""));
        } catch (_error) {
          throw new Error("preset_json_invalid");
        }
        const isBundle = String(parsed && parsed.kind || "") === "passengers.presets.bundle.v1";
        if (isBundle) {
          const scopesMap = parsed && typeof parsed.scopes === "object" && parsed.scopes ? parsed.scopes : {};
          const scopePayload = scopesMap[cleanScope];
          const incoming = dedupePresetList(
            Array.isArray(scopePayload) ? scopePayload : (scopePayload && scopePayload.presets)
          );
          const preview = buildPresetMergePreview(
            cleanScope,
            listPresets(cleanScope, { namespace }),
            incoming,
            { mode, protection: getPresetProtectionState(cleanScope, { namespace }) }
          );
          if (Number(preview.summary && preview.summary.protected_blocked ? preview.summary.protected_blocked : 0) > 0 && !allowProtectedWrite) {
            throw new Error("preset_protected_locked");
          }
          const merged = mergePresetLists(listPresets(cleanScope, { namespace }), incoming, mode);
          storePresets(cleanScope, merged, { namespace });
          appendPresetTimeline(cleanScope, "import_presets", {
            mode,
            imported: incoming.length,
            total: merged.length,
            source_kind: "bundle",
          }, { namespace });
          return { imported: incoming.length, total: merged.length, scope: cleanScope, namespace };
        }
        const parsedScope = String(parsed && parsed.scope || "").trim().toLowerCase();
        if (parsedScope && parsedScope !== cleanScope) throw new Error("preset_scope_mismatch");
        const incoming = dedupePresetList(parsed && parsed.presets);
        const preview = buildPresetMergePreview(
          cleanScope,
          listPresets(cleanScope, { namespace }),
          incoming,
          { mode, protection: getPresetProtectionState(cleanScope, { namespace }) }
        );
        if (Number(preview.summary && preview.summary.protected_blocked ? preview.summary.protected_blocked : 0) > 0 && !allowProtectedWrite) {
          throw new Error("preset_protected_locked");
        }
        const merged = mergePresetLists(listPresets(cleanScope, { namespace }), incoming, mode);
        storePresets(cleanScope, merged, { namespace });
        const incomingArchive = dedupePresetList(parsed && parsed.archive);
        if (incomingArchive.length > 0) {
          const mergedArchive = dedupePresetList([
            ...incomingArchive,
            ...listPresetArchive(cleanScope, { namespace, limit: 500 }),
          ]);
          storePresetArchive(cleanScope, mergedArchive, { namespace });
        }
        appendPresetTimeline(cleanScope, "import_presets", {
          mode,
          imported: incoming.length,
          total: merged.length,
          source_kind: "scope",
          imported_archive: incomingArchive.length,
        }, { namespace });
        return { imported: incoming.length, total: merged.length, scope: cleanScope, namespace };
      }
      function importPresetBundle(rawText, options = {}) {
        const namespace = normalizePresetNamespace(options.namespace);
        const mode = String(options.mode || "merge").trim().toLowerCase();
        const allowProtectedWrite = !!options.allowProtectedWrite;
        let parsed = {};
        try {
          parsed = JSON.parse(String(rawText || ""));
        } catch (_error) {
          throw new Error("preset_json_invalid");
        }
        if (String(parsed && parsed.kind || "") !== "passengers.presets.bundle.v1") {
          throw new Error("preset_bundle_required");
        }
        const scopesMap = parsed && typeof parsed.scopes === "object" && parsed.scopes ? parsed.scopes : {};
        const requestedScopes = normalizeScopeList(options.scopes, Object.keys(scopesMap));
        const scopeSet = new Set(requestedScopes.map((item) => String(item || "").trim().toLowerCase()).filter((item) => !!item));
        let imported = 0;
        let total = 0;
        for (const [scope, incomingRaw] of Object.entries(scopesMap)) {
          const cleanScope = String(scope || "").trim().toLowerCase();
          if (!cleanScope) continue;
          if (scopeSet.size > 0 && !scopeSet.has(cleanScope)) continue;
          const incomingPayload = incomingRaw && typeof incomingRaw === "object" ? incomingRaw : {};
          const incoming = dedupePresetList(
            Array.isArray(incomingRaw) ? incomingRaw : incomingPayload.presets
          );
          const preview = buildPresetMergePreview(
            cleanScope,
            listPresets(cleanScope, { namespace }),
            incoming,
            { mode, protection: getPresetProtectionState(cleanScope, { namespace }) }
          );
          if (Number(preview.summary && preview.summary.protected_blocked ? preview.summary.protected_blocked : 0) > 0 && !allowProtectedWrite) {
            throw new Error("preset_protected_locked");
          }
          const merged = mergePresetLists(listPresets(cleanScope, { namespace }), incoming, mode);
          storePresets(cleanScope, merged, { namespace });
          const incomingArchive = dedupePresetList(incomingPayload.archive);
          if (incomingArchive.length > 0) {
            const mergedArchive = dedupePresetList([
              ...incomingArchive,
              ...listPresetArchive(cleanScope, { namespace, limit: 500 }),
            ]);
            storePresetArchive(cleanScope, mergedArchive, { namespace });
          }
          appendPresetTimeline(cleanScope, "import_bundle", {
            mode,
            imported: incoming.length,
            total: merged.length,
            imported_archive: incomingArchive.length,
          }, { namespace });
          imported += incoming.length;
          total += merged.length;
        }
        return { imported, total, scopes: scopeSet.size > 0 ? scopeSet.size : Object.keys(scopesMap).length, namespace };
      }
      function cockpitTimelineActionLabel(action) {
        const normalized = String(action || "").trim().toLowerCase();
        if (!normalized) return "—";
        return normalized.replaceAll("_", " ");
      }
      function ensureCockpitTimelineDom() {
        const existing = byId("cockpitTimelineOverlay");
        if (existing) return existing;
        const root = document.createElement("div");
        root.id = "cockpitTimelineOverlay";
        root.className = "cockpitTimelineOverlay";
        root.innerHTML = `
          <div class="cockpitTimelineDialog" role="dialog" aria-modal="true" aria-label="Cockpit timeline">
            <div class="cmdHead">
              <span id="cockpitTimelineTitle">Cockpit timeline</span>
              <span class="mono">Esc</span>
            </div>
            <div class="cockpitTimelineFilters">
              <label class="cockpitTimelineField">Namespace
                <select id="cockpitTimelineNamespace">
                  <option value="local">local</option>
                  <option value="shared">shared</option>
                </select>
              </label>
              <label class="cockpitTimelineField">Scope
                <select id="cockpitTimelineScope"></select>
              </label>
              <label class="cockpitTimelineField">Action
                <select id="cockpitTimelineAction"></select>
              </label>
              <label class="cockpitTimelineField">Limit
                <input id="cockpitTimelineLimit" type="number" min="1" max="400" value="120" />
              </label>
              <div class="cockpitTimelineActions">
                <button id="cockpitTimelineRefresh" type="button" class="smallbtn">Оновити</button>
                <button id="cockpitTimelineExport" type="button" class="smallbtn">JSON</button>
                <button id="cockpitTimelineClose" type="button" class="smallbtn">Закрити</button>
              </div>
            </div>
            <div id="cockpitTimelineSummary" class="cockpitTimelineSummary"></div>
            <div class="cockpitTimelineTableWrap">
              <table class="cockpitTimelineTable">
                <thead>
                  <tr>
                    <th>Час</th>
                    <th>Namespace</th>
                    <th>Scope</th>
                    <th>Action</th>
                    <th>Ключові поля</th>
                    <th>Drill-down</th>
                  </tr>
                </thead>
                <tbody id="cockpitTimelineRows"></tbody>
              </table>
            </div>
          </div>
        `;
        root.addEventListener("click", (event) => {
          if (event.target === root) closePresetCockpitTimelinePanel();
        });
        document.body.appendChild(root);
        return root;
      }
      function closePresetCockpitTimelinePanel() {
        const overlay = byId("cockpitTimelineOverlay");
        if (overlay) overlay.classList.remove("open");
        cockpitTimelineState = null;
      }
      function renderPresetCockpitTimelinePanel() {
        if (!cockpitTimelineState) return;
        const namespaceNode = byId("cockpitTimelineNamespace");
        const scopeNode = byId("cockpitTimelineScope");
        const actionNode = byId("cockpitTimelineAction");
        const limitNode = byId("cockpitTimelineLimit");
        const summaryNode = byId("cockpitTimelineSummary");
        const rowsNode = byId("cockpitTimelineRows");
        if (!namespaceNode || !scopeNode || !actionNode || !limitNode || !summaryNode || !rowsNode) return;
        const namespace = normalizePresetNamespace(namespaceNode.value || cockpitTimelineState.namespace || "local");
        const selectedScope = String(scopeNode.value || "all").trim().toLowerCase();
        const selectedAction = String(actionNode.value || "all").trim().toLowerCase();
        const limitRaw = parseInt(String(limitNode.value || cockpitTimelineState.limit || 120), 10);
        const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(400, limitRaw) : 120;
        const allScopes = normalizeScopeList(cockpitTimelineState.scopes, []);
        const effectiveScopes = selectedScope === "all" ? allScopes : [selectedScope];
        const baseReport = buildPresetCockpitTimeline({
          namespace,
          scopes: effectiveScopes,
          limit: 400,
        });
        const actionOptions = ["all", ...Object.keys(baseReport.counters.action || {}).sort((left, right) => left.localeCompare(right))];
        const fallbackAction = actionOptions.includes(selectedAction) ? selectedAction : "all";
        actionNode.innerHTML = actionOptions
          .map((item) => `<option value="${esc(item)}">${esc(item === "all" ? "all actions" : cockpitTimelineActionLabel(item))}</option>`)
          .join("");
        actionNode.value = fallbackAction;
        const report = buildPresetCockpitTimeline({
          namespace,
          scopes: effectiveScopes,
          actions: fallbackAction === "all" ? [] : [fallbackAction],
          limit,
        });
        const summary = report.summary || {};
        summaryNode.innerHTML = [
          `<span class="badge">entries: ${esc(summary.visible_total || 0)}</span>`,
          `<span class="badge">filtered: ${esc(summary.filtered_total || 0)}</span>`,
          `<span class="badge">scopes: ${esc(summary.scope_count || 0)}</span>`,
          `<span class="badge">actions: ${esc(summary.action_count || 0)}</span>`,
          `<span class="badge">last: ${esc(summary.last_action ? cockpitTimelineActionLabel(summary.last_action) : "—")}</span>`,
          `<span class="badge mono">${esc(summary.last_ts || "—")}</span>`,
        ].join("");
        const entries = Array.isArray(report.entries) ? report.entries : [];
        if (entries.length === 0) {
          rowsNode.innerHTML = '<tr><td colspan="6"><span class="badge good">OK</span> Немає записів за поточними фільтрами</td></tr>';
        } else {
          rowsNode.innerHTML = "";
          for (const entry of entries) {
            const details = entry && entry.details && typeof entry.details === "object" ? entry.details : {};
            const keyParts = [];
            if (details.name) keyParts.push(`name=${String(details.name)}`);
            if (details.mode) keyParts.push(`mode=${String(details.mode)}`);
            if (details.imported !== undefined) keyParts.push(`imported=${String(details.imported)}`);
            if (details.total !== undefined) keyParts.push(`total=${String(details.total)}`);
            if (details.locked !== undefined) keyParts.push(`locked=${String(details.locked)}`);
            const keyText = keyParts.length > 0 ? keyParts.join(" · ") : "—";
            const row = document.createElement("tr");
            row.innerHTML = `
              <td><code>${esc(entry.ts || "—")}</code></td>
              <td><code>${esc(entry.namespace || namespace)}</code></td>
              <td><code>${esc(entry.scope || "—")}</code></td>
              <td><span class="badge">${esc(cockpitTimelineActionLabel(entry.action || ""))}</span></td>
              <td>${esc(keyText)}</td>
              <td class="cockpitTimelineActionsCell"><button type="button" class="smallbtn" data-action="details">Деталі</button></td>
            `;
            row.querySelector('button[data-action="details"]')?.addEventListener("click", () => {
              const payload = {
                ts: String(entry.ts || ""),
                namespace: String(entry.namespace || namespace),
                scope: String(entry.scope || ""),
                action: String(entry.action || ""),
                details,
              };
              if (cockpitTimelineState && typeof cockpitTimelineState.onDrillDown === "function") {
                cockpitTimelineState.onDrillDown(payload);
                return;
              }
              window.prompt("Cockpit timeline details (JSON):", JSON.stringify(payload, null, 2));
            });
            rowsNode.appendChild(row);
          }
        }
        cockpitTimelineState = {
          ...cockpitTimelineState,
          namespace,
          last_report: report,
          selected_scope: selectedScope,
          selected_action: fallbackAction,
          limit,
        };
      }
      function openPresetCockpitTimelinePanel(options = {}) {
        const overlay = ensureCockpitTimelineDom();
        const titleNode = byId("cockpitTimelineTitle");
        const namespaceNode = byId("cockpitTimelineNamespace");
        const scopeNode = byId("cockpitTimelineScope");
        const actionNode = byId("cockpitTimelineAction");
        const limitNode = byId("cockpitTimelineLimit");
        const scopes = normalizeScopeList(
          options.scopes,
          Array.from(new Set([
            ...listPresetScopes({ namespace: "local" }),
            ...listPresetScopes({ namespace: "shared" }),
          ]))
        );
        const namespace = normalizePresetNamespace(options.namespace);
        const limitRaw = Number(options.limit ?? 120);
        const limit = Number.isFinite(limitRaw) && limitRaw > 0 ? Math.min(400, limitRaw) : 120;
        cockpitTimelineState = {
          title: String(options.title || "Cockpit timeline"),
          namespace,
          scopes,
          limit,
          onDrillDown: typeof options.onDrillDown === "function" ? options.onDrillDown : null,
          last_report: null,
          selected_scope: "all",
          selected_action: "all",
        };
        if (titleNode) titleNode.textContent = cockpitTimelineState.title;
        if (namespaceNode) namespaceNode.value = namespace;
        if (scopeNode) {
          const scopeOptions = ["all", ...scopes];
          scopeNode.innerHTML = scopeOptions
            .map((item) => `<option value="${esc(item)}">${esc(item === "all" ? "all scopes" : item)}</option>`)
            .join("");
          scopeNode.value = "all";
        }
        if (actionNode) {
          actionNode.innerHTML = '<option value="all">all actions</option>';
          actionNode.value = "all";
        }
        if (limitNode) limitNode.value = String(limit);
        const refreshButton = byId("cockpitTimelineRefresh");
        const closeButton = byId("cockpitTimelineClose");
        const exportButton = byId("cockpitTimelineExport");
        if (refreshButton) refreshButton.onclick = () => renderPresetCockpitTimelinePanel();
        if (closeButton) closeButton.onclick = () => closePresetCockpitTimelinePanel();
        if (exportButton) {
          exportButton.onclick = () => {
            if (!cockpitTimelineState || !cockpitTimelineState.last_report) {
              renderPresetCockpitTimelinePanel();
            }
            const payload = cockpitTimelineState && cockpitTimelineState.last_report
              ? cockpitTimelineState.last_report
              : buildPresetCockpitTimeline({ namespace, scopes, limit });
            window.prompt("Cockpit timeline (JSON):", JSON.stringify(payload, null, 2));
          };
        }
        if (namespaceNode) namespaceNode.onchange = () => renderPresetCockpitTimelinePanel();
        if (scopeNode) scopeNode.onchange = () => renderPresetCockpitTimelinePanel();
        if (actionNode) actionNode.onchange = () => renderPresetCockpitTimelinePanel();
        if (limitNode) {
          limitNode.onchange = () => renderPresetCockpitTimelinePanel();
          limitNode.onkeydown = (event) => {
            if (String(event.key || "").toLowerCase() === "enter") {
              event.preventDefault();
              renderPresetCockpitTimelinePanel();
            }
          };
        }
        overlay.classList.add("open");
        renderPresetCockpitTimelinePanel();
      }
      function ensurePaletteDom() {
        const existing = byId("cmdOverlay");
        if (existing) return existing;
        const root = document.createElement("div");
        root.id = "cmdOverlay";
        root.className = "cmdOverlay";
        root.innerHTML = `
          <div class="cmdDialog" role="dialog" aria-modal="true" aria-label="Командна панель">
            <div class="cmdHead">
              <span id="cmdTitle">Команди</span>
              <span class="mono">Esc</span>
            </div>
            <input id="cmdSearch" class="cmdSearch" type="text" placeholder="Пошук команди..." />
            <div id="cmdList" class="cmdList"></div>
          </div>
        `;
        root.addEventListener("click", (event) => {
          if (event.target === root) closeCommandPalette();
        });
        document.body.appendChild(root);
        return root;
      }
      function renderPaletteItems() {
        if (!paletteState) return;
        const listNode = byId("cmdList");
        if (!listNode) return;
        const search = String(byId("cmdSearch")?.value || "").trim().toLowerCase();
        const all = Array.isArray(paletteState.commands) ? paletteState.commands : [];
        const visible = all.filter((item) => {
          if (!search) return true;
          const hay = `${item.title || ""} ${item.subtitle || ""}`.toLowerCase();
          return hay.includes(search);
        });
        paletteState.visible = visible;
        if (paletteState.activeIndex >= visible.length) paletteState.activeIndex = Math.max(0, visible.length - 1);
        listNode.innerHTML = "";
        if (visible.length === 0) {
          listNode.innerHTML = '<div class="cmdItem"><span class="cmdSub">Нічого не знайдено</span></div>';
          return;
        }
        visible.forEach((item, index) => {
          const button = document.createElement("button");
          button.type = "button";
          button.className = "cmdItem" + (index == paletteState.activeIndex ? " active" : "");
          button.innerHTML = `<span class="cmdTitle">${esc(item.title || "Команда")}</span><span class="cmdSub">${esc(item.subtitle || "")}</span>`;
          button.addEventListener("click", () => runPaletteCommand(index));
          listNode.appendChild(button);
        });
      }
      function closeCommandPalette() {
        const overlay = byId("cmdOverlay");
        if (overlay) overlay.classList.remove("open");
        if (paletteState && typeof paletteState.onClose === "function") {
          try { paletteState.onClose(); } catch (_error) {}
        }
        paletteState = null;
      }
      function runPaletteCommand(index) {
        if (!paletteState) return;
        const visible = Array.isArray(paletteState.visible) ? paletteState.visible : [];
        const item = visible[index];
        if (!item || typeof item.run !== "function") return;
        closeCommandPalette();
        item.run();
      }
      function openCommandPalette(options = {}) {
        const overlay = ensurePaletteDom();
        const titleNode = byId("cmdTitle");
        const searchNode = byId("cmdSearch");
        paletteState = {
          commands: Array.isArray(options.commands) ? options.commands : [],
          visible: [],
          activeIndex: 0,
          onClose: typeof options.onClose === "function" ? options.onClose : null,
        };
        if (titleNode) titleNode.textContent = String(options.title || "Команди");
        if (searchNode) {
          searchNode.value = "";
          searchNode.oninput = () => { paletteState.activeIndex = 0; renderPaletteItems(); };
          searchNode.onkeydown = (event) => {
            if (!paletteState) return;
            const visible = Array.isArray(paletteState.visible) ? paletteState.visible : [];
            if (event.key === "ArrowDown") {
              event.preventDefault();
              paletteState.activeIndex = Math.min(visible.length - 1, paletteState.activeIndex + 1);
              renderPaletteItems();
            } else if (event.key === "ArrowUp") {
              event.preventDefault();
              paletteState.activeIndex = Math.max(0, paletteState.activeIndex - 1);
              renderPaletteItems();
            } else if (event.key === "Enter") {
              event.preventDefault();
              runPaletteCommand(paletteState.activeIndex);
            } else if (event.key === "Escape") {
              event.preventDefault();
              closeCommandPalette();
            }
          };
        }
        renderPaletteItems();
        overlay.classList.add("open");
        setTimeout(() => { searchNode?.focus(); }, 0);
      }
      function bindCommandPalette(opener) {
        if (typeof opener !== "function") return;
        document.addEventListener("keydown", (event) => {
          const key = String(event.key || "").toLowerCase();
          if ((event.ctrlKey || event.metaKey) && key === "k") {
            event.preventDefault();
            opener();
          }
          if (key === "escape" && paletteState) {
            event.preventDefault();
            closeCommandPalette();
            return;
          }
          if (key === "escape" && cockpitTimelineState) {
            event.preventDefault();
            closePresetCockpitTimelinePanel();
          }
        });
      }
      function debounce(callback, delayMs = 280) {
        let timer = null;
        return (...args) => {
          if (timer) clearTimeout(timer);
          timer = setTimeout(() => {
            timer = null;
            callback(...args);
          }, delayMs);
        };
      }
      function bindEnterRefresh(inputIds, refresh) {
        for (const id of inputIds) {
          const node = byId(id);
          if (!node) continue;
          node.addEventListener("keydown", (event) => {
            if (event.key === "Enter") {
              event.preventDefault();
              refresh();
            }
          });
        }
      }
      function bindDebouncedInputs(inputIds, refresh, delayMs = 280) {
        const schedule = debounce(refresh, delayMs);
        for (const id of inputIds) {
          const node = byId(id);
          if (!node) continue;
          node.addEventListener("input", schedule);
        }
      }
      function bindClearFilters(buttonId, resetFilters, refresh) {
        const button = byId(buttonId);
        if (!button) return;
        button.addEventListener("click", () => {
          resetFilters();
          refresh();
        });
      }
      function normalizeDensity(value) {
        return String(value || "").toLowerCase() === "compact" ? "compact" : "regular";
      }
      function densityLabel(value) {
        return normalizeDensity(value) === "compact" ? "Компактна" : "Звичайна";
      }
      function applyDensityMode(value, options = {}) {
        const className = String(options.className || "density-compact");
        const storageKey = String(options.storageKey || "admin_density");
        const normalized = normalizeDensity(value);
        document.body.classList.toggle(className, normalized === "compact");
        try { localStorage.setItem(storageKey, normalized); } catch (_error) {}
        return normalized;
      }
      function initDensityMode(selectId, options = {}) {
        const select = byId(selectId);
        if (!select) return "regular";
        const storageKey = String(options.storageKey || "admin_density");
        const className = String(options.className || "density-compact");
        let stored = "regular";
        try { stored = localStorage.getItem(storageKey) || "regular"; } catch (_error) { stored = "regular"; }
        const normalized = normalizeDensity(stored);
        select.value = normalized;
        applyDensityMode(normalized, { storageKey, className });
        select.addEventListener("change", (event) => {
          const selected = event && event.target ? event.target.value : "regular";
          const value = applyDensityMode(selected, { storageKey, className });
          if (typeof options.onChange === "function") options.onChange(value);
        });
        return normalized;
      }
      function windowToSeconds(rawValue, fallback = 24 * 3600) {
        const normalized = String(rawValue ?? "").trim().toLowerCase();
        if (!normalized) return fallback;
        const match = normalized.match(/^([0-9]+)([smhd])$/);
        if (!match) return fallback;
        const amount = parseInt(match[1], 10);
        if (!Number.isFinite(amount)) return fallback;
        const unit = match[2];
        if (unit === "s") return amount;
        if (unit === "m") return amount * 60;
        if (unit === "h") return amount * 3600;
        if (unit === "d") return amount * 86400;
        return fallback;
      }
      async function fetchJson(path, init = {}) {
        const response = await fetch(path, init);
        const text = await response.text();
        if (!response.ok) throw new Error(`${response.status} ${text}`);
        return text ? JSON.parse(text) : {};
      }
      async function apiGet(path) {
        return fetchJson(path);
      }
      async function apiPost(path, payload) {
        const init = { method: "POST" };
        if (payload !== null && payload !== undefined) {
          init.headers = { "Content-Type": "application/json" };
          init.body = JSON.stringify(payload);
        }
        return fetchJson(path, init);
      }
      async function apiDelete(path) {
        return fetchJson(path, { method: "DELETE" });
      }
      async function loadWhoami() {
        try {
          const data = await apiGet("/api/admin/whoami");
          return {
            role: String(data.role || "viewer"),
            actor: String(data.actor || "невідомо"),
            capabilities: data.capabilities || { read: true, operate: false, admin: false },
          };
        } catch (_error) {
          return {
            role: "viewer",
            actor: "невідомо",
            capabilities: { read: true, operate: false, admin: false },
          };
        }
      }
      function showGlobalToast(title, body) {
        const node = document.getElementById("globalToast");
        if (!(node instanceof HTMLElement)) return;
        const safeTitle = String(title || "Помилка");
        const safeBody = String(body || "");
        node.innerHTML = `
          <button class="toastClose" type="button" aria-label="Закрити">×</button>
          <div class="toastTitle">${esc(safeTitle)}</div>
          <div class="toastBody">${esc(safeBody)}</div>
        `;
        const close = node.querySelector(".toastClose");
        if (close) close.addEventListener("click", () => { node.hidden = true; });
        node.hidden = false;
        clearTimeout(node.__toastTimer || 0);
        node.__toastTimer = setTimeout(() => { node.hidden = true; }, 12000);
      }
      window.addEventListener("error", (event) => {
        const msg = event?.message ? String(event.message) : "JS error";
        showGlobalToast("Помилка інтерфейсу", msg);
      });
      window.addEventListener("unhandledrejection", (event) => {
        const reason = event?.reason ? String(event.reason) : "Unhandled promise rejection";
        showGlobalToast("Помилка запиту", reason);
      });
	      return {
	        byId,
	        setText,
	        setStatus,
	        esc,
	        val,
	        intVal,
	        optInt,
	        setDisabled,
	        copyTextWithFallback,
	        applyEmptyTables,
	        initSidebarPersonalization,
	        refreshSidebarPersonalization,
	        formatLatency,
	        runActionWithLatency,
	        loadWorkspaceContext,
        saveWorkspaceContext,
        clearWorkspaceContext,
        formatWorkspaceContext,
        applyWorkspaceHint,
        normalizePresetNamespace,
        listPresetScopes,
        listPresets,
        listPresetArchive,
        getPresetCleanupReport,
        getPresetProtectionState,
        setPresetProtectionLock,
        getPresetRolloutLast,
        listPresetTimeline,
        clearPresetTimeline,
        buildPresetTimelineSummary,
        buildPresetTimelineBundle,
        buildPresetOperationsSummary,
        buildPresetCockpitTimeline,
        buildPresetRolloutAssistant,
        simulatePresetImport,
        simulatePresetBundleImport,
        simulatePresetOperations,
        applyPresetRolloutAssistant,
        applyPresetOperations,
        setPresetProtectionLockBatch,
        savePreset,
        deletePreset,
        getPreset,
        presetProfileTemplates,
        installPresetProfiles,
        cleanupPresets,
        buildPresetMetrics,
        buildPresetMetricsBundle,
        buildPresetScopeObservability,
        buildPresetObservabilityBundle,
        exportPresets,
        importPresets,
        exportPresetBundle,
        importPresetBundle,
        openPresetCockpitTimelinePanel,
        closePresetCockpitTimelinePanel,
        openCommandPalette,
        closeCommandPalette,
        bindCommandPalette,
        debounce,
        bindEnterRefresh,
        bindDebouncedInputs,
        bindClearFilters,
        normalizeDensity,
        densityLabel,
        applyDensityMode,
        initDensityMode,
        windowToSeconds,
        fetchJson,
        apiGet,
        apiPost,
        apiDelete,
        loadWhoami,
        showGlobalToast,
      };
    })();
    """.strip()


def render_admin_shell(
    *,
    title: str,
    header_title: str,
    chips_html: str,
    toolbar_html: str,
    body_html: str,
    script: str,
    max_width: int = 1280,
    extra_css: str = "",
    include_base_js: bool = True,
    shell_layout: bool = True,
    current_nav: str | None = None,
    show_sidebar: bool = True,
) -> str:
    safe_title = escape(title)
    safe_header_title = escape(header_title)
    css = base_admin_css()
    if extra_css.strip():
        css = css + "\n" + extra_css.strip()
    base_js = base_admin_js() if include_base_js else ""
    current = str(current_nav or "").strip().lower()
    workflow = ADMIN_NAV_WORKFLOW
    workflow_index = {key: index for index, (key, _label, _href, _step) in enumerate(workflow)}
    current_workflow_idx = workflow_index.get(current)
    nav_groups = ADMIN_NAV_GROUPS

    def sidebar_html() -> str:
        def build_link(key: str, label: str, href: str, step: str = "", tier: str = "sub") -> str:
            classes = ["sideLink", "sideLinkHub" if tier == "hub" else "sideLinkSub"]
            if current == key:
                classes.append("active")
            if current_workflow_idx is not None and key in workflow_index and workflow_index[key] <= current_workflow_idx:
                classes.append("trail")
            class_text = " ".join(classes)

            wrap_classes = ["sideLinkWrap"]
            if current == key:
                wrap_classes.append("active")
            if tier != "hub":
                wrap_classes.append("noPin")
            wrap_class_text = " ".join(wrap_classes)

            step_html = f'<span class="sideStep">{escape(step)}</span>' if step else ""
            pin_html = (
                f'<button class="sidePin" type="button" data-nav-key="{escape(key)}" aria-label="Додати {escape(label)} в обране" title="Додати в обране">☆</button>'
                if tier == "hub"
                else ""
            )
            return (
                f'<div class="{wrap_class_text}" data-nav-tier="{escape(tier)}">'
                f'<a class="{class_text}" href="{escape(href, quote=True)}" data-nav-key="{escape(key)}" data-nav-label="{escape(label)}" data-nav-href="{escape(href, quote=True)}" data-nav-tier="{escape(tier)}">'
                f'<span class="sideLabel">{escape(label)}</span>{step_html}</a>'
                + pin_html
                + '</div>'
            )

        jump_links: list[str] = []
        for key, label, href, _step in workflow:
            jump_class = "sideJump active" if current == key else "sideJump"
            jump_links.append(
                f'<a class="{jump_class}" href="{escape(href, quote=True)}" data-nav-key="{escape(key)}" data-nav-label="{escape(label)}">{escape(label)}</a>'
            )

        group_blocks: list[str] = []
        for group_key, group_title, items in nav_groups:
            group_active = any(current == key for key, _label, _href, _step, _tier in items)
            group_collapsed = not group_active
            group_class = "sideGroup active" if group_active else "sideGroup collapsed"
            links = [build_link(key, label, href, step, tier) for key, label, href, step, tier in items]
            list_id = f"sideGroupList-{group_key}"
            group_blocks.append(
                f'        <section class="{group_class}" data-side-group="{escape(group_key)}">\n'
                f'          <div class="sideGroupHead"><button class="sideGroupTitle sideGroupToggle" type="button" data-side-group="{escape(group_key)}" aria-expanded="{"false" if group_collapsed else "true"}" aria-controls="{escape(list_id)}" title="{"Розгорнути групу" if group_collapsed else "Згорнути групу"}"><span>{escape(group_title)}</span><span class="sideGroupChevron">▾</span></button></div>\n'
                f'          <div id="{escape(list_id)}" class="sideList">\n'
                + "\n".join(f"            {item}" for item in links)
                + "\n          </div>\n"
                "        </section>"
            )
        return (
            '    <aside class="sideNav">\n'
            '      <div class="sideBrand">Passengers • Адмінка</div>\n'
            '      <div class="sideHint">Меню та підменю</div>\n'
            '      <div class="sideNavTools">\n'
            '        <label class="sideNavSearchWrap" for="sideNavFilter"><input id="sideNavFilter" class="sideNavSearch" type="search" placeholder="Пошук розділу" aria-label="Пошук по лівому меню" aria-controls="sideNavGroups sideNavJumpRow" aria-describedby="sideNavFilterStatus"></label>\n'
            '        <button id="sideNavCompactToggle" class="sideNavCompactBtn" type="button" aria-pressed="false" aria-label="Перемкнути компактний режим меню" title="Увімкнути компактний режим">Компакт</button>\n'
            '        <button id="sideNavModeToggle" class="sideNavModeBtn" type="button" aria-pressed="false" aria-label="Перемкнути режим меню: простий/розширений" title="Показати розширені блоки sidebar">Розширено</button>\n'
            '        <button id="sideFocusToggle" class="sideNavFocusBtn" type="button" aria-pressed="false" aria-label="Перемкнути фокус-режим меню" title="Увімкнути фокус-режим">Стандарт</button>\n'
            '        <button id="sideNavHelpToggle" class="sideNavHelpBtn" type="button" aria-expanded="false" aria-controls="sideNavOnboarding" title="Показати підказки">Підказки</button>\n'
            "      </div>\n"
            '      <div id="sideNavFilterStatus" class="sideNavFilterStatus" role="status" aria-live="polite" aria-atomic="true">Фільтр: усі секції</div>\n'
            '      <div id="sideNavOnboarding" class="sideNavOnboarding" role="note" hidden>\n'
            '        <p class="sideNavOnboardingTitle">Швидкий старт навігації</p>\n'
            '        <ul class="sideNavOnboardingList">\n'
            '          <li><code>Shift+Alt+N</code> фокус на пошук меню.</li>\n'
            '          <li><code>Enter</code> в полі пошуку відкриває єдиний знайдений розділ.</li>\n'
            '          <li><code>Arrow Down</code> в пошуку переводить фокус на перший пункт меню.</li>\n'
            '        </ul>\n'
            '        <div class="sideNavOnboardingFoot"><button id="sideNavOnboardingDismiss" class="sideNavOnboardingDismiss" type="button">Зрозуміло</button></div>\n'
            '      </div>\n'
            '      <div id="sideNavJumpRow" class="sideJumpRow" role="navigation" aria-label="Швидкий перехід">\n'
            + "\n".join(f"        {item}" for item in jump_links)
            + "\n      </div>\n"
            '      <nav id="sideNavGroups" class="sideGroups" aria-label="Основна навігація">\n'
            + "\n".join(group_blocks)
            + "\n      </nav>\n"
            '      <div class="sideMiniSection" data-side-mini="quick">\n'
            '        <div class="sideMiniHead">\n'
            '          <div class="sideHint">Швидкі дії</div>\n'
            '          <div class="sideMiniHeadActions"><button class="sideMiniToggle" type="button" data-side-mini-toggle="quick" aria-expanded="true" aria-controls="sideMiniBody-quick" aria-label="Згорнути/розгорнути: швидкі дії" title="Згорнути блок"><span class="sideMiniChevron">▾</span></button></div>\n'
            "        </div>\n"
            '        <div id="sideMiniBody-quick" class="sideMiniBody">\n'
            '          <div id="sideQuickIntentList" class="sideMiniList">\n'
            '            <span class="sideMiniEmpty">—</span>\n'
            "          </div>\n"
            "        </div>\n"
            "      </div>\n"
            '      <div class="sideMiniSection" data-side-mini="hub">\n'
            '        <div class="sideMiniHead">\n'
            '          <div class="sideHint">Командний центр</div>\n'
            '          <div class="sideMiniHeadActions"><button class="sideMiniToggle" type="button" data-side-mini-toggle="hub" aria-expanded="true" aria-controls="sideMiniBody-hub" aria-label="Згорнути/розгорнути: командний центр" title="Згорнути блок"><span class="sideMiniChevron">▾</span></button></div>\n'
            "        </div>\n"
            '        <div id="sideMiniBody-hub" class="sideMiniBody">\n'
            '          <div id="sideCommandHub" class="sideHub">\n'
            '          <div class="sideHubHint">Запуск дій</div>\n'
            '          <div id="sideHubGrid" class="sideHubGrid">\n'
            '            <button class="sideHubBtn" type="button" data-intent-run="alerts-bad">Проблемні алерти</button>\n'
            '          </div>\n'
            '          <div id="sideContextHint" class="sideFocusState">Контекст: —</div>\n'
            '          <div id="sideHubStatus" class="sideFocusState">Дія: —</div>\n'
            '          <div id="sideFocusState" class="sideFocusState">Стандарт: повний sidebar з quick/favorites/recent</div>\n'
            "          </div>\n"
            "        </div>\n"
            "      </div>\n"
            '      <div class="sideMiniSection" data-side-mini="mission">\n'
            '        <div class="sideMiniHead">\n'
            '          <div class="sideHint">Центр інцидентів</div>\n'
            '          <div class="sideMiniHeadActions"><button class="sideMiniToggle" type="button" data-side-mini-toggle="mission" aria-expanded="true" aria-controls="sideMiniBody-mission" aria-label="Згорнути/розгорнути: центр інцидентів" title="Згорнути блок"><span class="sideMiniChevron">▾</span></button></div>\n'
            "        </div>\n"
            '        <div id="sideMiniBody-mission" class="sideMiniBody">\n'
            '          <div id="sideMissionControl" class="sideHub">\n'
            '          <div class="sideHubHint">Віджети (алерти першими)</div>\n'
            '          <div id="sideMissionGrid" class="sideMissionGrid">\n'
            '            <span class="sideMiniEmpty">—</span>\n'
            '          </div>\n'
            '          <div class="sideHubHint" style="margin-top:8px;">Тріаж в один клік</div>\n'
            '          <div id="sideMissionPresetList" class="sideMissionPresets">\n'
            '            <span class="sideMiniEmpty">—</span>\n'
            '          </div>\n'
            '          <div id="sideMissionStatus" class="sideMissionStatus">Пресет: —</div>\n'
            '          <div id="sideMissionChecklist" class="sideMissionStatus"><span class="sideChecklistBadge">Чекліст: —</span></div>\n'
            '          <div class="sideHubHint" style="margin-top:8px;">Плейбуки відновлення</div>\n'
            '          <div id="sideMissionPlaybookList" class="sideMissionPlaybooks">\n'
            '            <span class="sideMiniEmpty">—</span>\n'
            '          </div>\n'
            '          <div id="sideMissionChain" class="sideMissionChain"><span class="sideMiniEmpty">—</span></div>\n'
            '          <div class="sideHubHint" style="margin-top:8px;">Знімок доказів</div>\n'
            '          <div id="sideMissionSnapshot" class="sideSnapshotBox">\n'
            '            <div class="sideSnapshotTools">\n'
            '              <button class="sideSnapshotBtn" type="button" data-snapshot-action="capture">Зняти</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-snapshot-action="show">Журнал</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-snapshot-action="clear">Очистити</button>\n'
            '            </div>\n'
            '            <div id="sideMissionSnapshotSummary" class="sideSnapshotSummary">Знімок: —</div>\n'
            '          </div>\n'
            '          <div class="sideHubHint" style="margin-top:8px;">Пакет реагування</div>\n'
            '          <div id="sideMissionResponsePack" class="sideSnapshotBox">\n'
            '            <div class="sideSnapshotTools">\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="generate">Зібрати</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="copy-template">Копіювати шаблон</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="export-json">JSON</button>\n'
            '            </div>\n'
            '            <div class="sideSnapshotTools">\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="clear">Очистити пакет</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="copy-route">Копіювати маршрут</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="auto-route">Авто-маршрут</button>\n'
            '            </div>\n'
            '            <div class="sideRoutingRow">\n'
            '              <label class="sideRoutingLabel" for="sideRoutingProfile">Профіль маршрутизації</label>\n'
            '              <select id="sideRoutingProfile" class="sideRoutingSelect"></select>\n'
            '            </div>\n'
            '            <div class="sideRoutingRow">\n'
            '              <label class="sideRoutingLabel" for="sideRoutingTemplate">Шаблон каналу</label>\n'
            '              <select id="sideRoutingTemplate" class="sideRoutingSelect"></select>\n'
            '            </div>\n'
            '            <div class="sideSnapshotTools">\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="apply-routing">Застосувати</button>\n'
            '            </div>\n'
            '            <div id="sideResponsePackSummary" class="sideSnapshotSummary">Пакет реагування: —</div>\n'
            '            <div id="sideResponseRoutingSummary" class="sideSnapshotSummary">Маршрут: —</div>\n'
            '            <div class="sideSnapshotSection">Адаптери доставки</div>\n'
            '            <div class="sideRoutingRow">\n'
            '              <label class="sideRoutingLabel" for="sideDeliveryAdapter">Адаптер</label>\n'
            '              <select id="sideDeliveryAdapter" class="sideRoutingSelect"></select>\n'
            '            </div>\n'
            '            <div class="sideRoutingRow">\n'
            '              <label class="sideRoutingLabel" for="sideDeliveryVariant">Варіант</label>\n'
            '              <select id="sideDeliveryVariant" class="sideRoutingSelect"></select>\n'
            '            </div>\n'
            '            <div class="sideRoutingRow">\n'
            '              <label class="sideRoutingLabel" for="sideDeliveryPolicyProfile">Профіль політики</label>\n'
            '              <select id="sideDeliveryPolicyProfile" class="sideRoutingSelect"></select>\n'
            '            </div>\n'
            '            <div id="sideDeliveryPolicySummary" class="sideSnapshotSummary">Політика: —</div>\n'
            '            <div class="sideSnapshotTools two">\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="copy-delivery" title="Скопіювати payload для вибраного adapter/variant">Копіювати обраний</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="apply-delivery" title="Оновити delivery state для поточного контексту">Оновити</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="copy-telegram" title="Швидкий payload для Telegram">Telegram</button>\n'
            '            </div>\n'
            '            <div class="sideSnapshotTools two">\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="copy-email" title="Швидкий payload для Email">Email</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="copy-ticket" title="Швидкий payload для Ticket queue">Ticket</button>\n'
            '            </div>\n'
            '            <div class="sideSnapshotTools two">\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="show-delivery-journal" title="Показати delivery history (JSON)">Журнал доставки</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="clear-delivery-journal" title="Очистити delivery journal для нової зміни">Очистити журнал</button>\n'
            '            </div>\n'
            '            <div class="sideSnapshotSection">Життєвий цикл доставки</div>\n'
            '            <div class="sideSnapshotTools two">\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="ack-delivery" title="Підтвердити доставку (Shift+Alt+K)">ACK</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="retry-delivery" title="Повторити доставку (Shift+Alt+R)">Retry</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="escalate-delivery" title="Ескалація в пріоритетний канал (Shift+Alt+E)">Escalate</button>\n'
            '            </div>\n'
            '            <div class="sideSnapshotSection">Automation shortcuts</div>\n'
            '            <div class="sideSnapshotTools two">\n'
            '              <button id="sideDeliverySuggestedAction" class="sideSnapshotBtn primary" type="button" data-response-pack-action="apply-delivery-suggestion" title="Застосувати рекомендацію policy engine (Shift+Alt+D)">Apply suggestion</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="bulk-ack-pending" title="Масовий ACK для pending контекстів (Shift+Alt+B)">Bulk ACK</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="bulk-escalate-stale" title="Масова ескалація stale контекстів (Shift+Alt+G)">Bulk Escalate</button>\n'
            '            </div>\n'
            '            <div class="sideSnapshotTools two">\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="bulk-retry-stale" title="Масовий retry для stale контекстів (Shift+Alt+Y)">Bulk Retry</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="apply-delivery-policy" title="Застосувати обраний policy profile (Shift+Alt+P)">Apply profile</button>\n'
            '            </div>\n'
            '            <div id="sideDeliverySummary" class="sideSnapshotSummary">Delivery: —</div>\n'
            '            <div id="sideDeliveryHandoffStatus" class="sideSnapshotSummary">Queue-ready: —</div>\n'
            '            <div id="sideDeliverySlaStatus" class="sideSnapshotSummary">SLA: —</div>\n'
            '            <div id="sideDeliveryAutomationSummary" class="sideSnapshotSummary">Automation: —</div>\n'
            '            <div id="sideDeliverySticky" class="sideDeliverySticky">\n'
            '              <button id="sideDeliveryStickySuggested" class="sideSnapshotBtn primary wide" type="button" data-response-pack-action="apply-delivery-suggestion" title="Apply suggestion (Shift+Alt+D)">Apply suggestion</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="ack-delivery" title="ACK (Shift+Alt+K)">ACK</button>\n'
            '              <button class="sideSnapshotBtn" type="button" data-response-pack-action="escalate-delivery" title="Escalate (Shift+Alt+E)">Escalate</button>\n'
            '            </div>\n'
          '          </div>\n'
            '          <div class="sideHubHint" style="margin-top:8px;">Sticky incident focus</div>\n'
            '          <div id="sideIncidentFocus" class="sideFocusBox"><span class="sideMiniEmpty">—</span></div>\n'
            '          <div class="sideHubHint" style="margin-top:8px;">Operator handoff notes</div>\n'
            '          <div id="sideMissionHandoff" class="sideHandoffBox">\n'
            '            <textarea id="sideHandoffInput" class="sideHandoffInput" placeholder="Коротко: що зроблено, що лишилось, ризики..."></textarea>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-action="save">Зберегти</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-action="context">+ Контекст</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-action="clear">Очистити</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-history-action="show">Історія</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-history-action="clear">Очистити історію</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-snapshot-action="capture">Snapshot</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-adoption-action="show">Adoption JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-adoption-action="export">Export adoption</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-adoption-action="reset">Reset adoption</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-trend-action="show">Trend JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-trend-action="export">Export trend</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-trend-action="clear">Clear trend</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-trend-window="3">Trend-3</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-trend-window="5">Trend-5</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-trend-window="10">Trend-10</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-compose-action="compose">Compose</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-compose-action="copy">Copy composer</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-compose-action="apply">Apply composer</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-quality-action="check">Quality check</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-quality-remedy="recommended">Fix: n/a</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-quality-profile="strict">Q-Strict</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-quality-profile="balanced">Q-Balanced</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-quality-remedy="compose-apply">Fix composer</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-quality-remedy="context">Fix context</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-quality-remedy="append-next-actions">Fix next-actions</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-history-action="show">Remediation JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-history-action="export">Export remediation</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-history-action="clear">Clear remediation</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-governance="standard">Gov-Standard</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-governance="tight">Gov-Tight</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-incident-action="ack">Incident ACK</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-incident-action="snooze">Incident Snooze</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-incident-history-action="show">Incident JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-incident-history-action="export">Export incidents</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-incident-history-action="clear">Clear incidents</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="show">Plan JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="export">Export plan</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="copy">Copy handoff plan</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="log-primary">Log primary</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="ledger-show">Decision JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="ledger-export">Export decisions</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="ledger-clear">Clear decisions</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="backlog-show">Backlog JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="backlog-export">Export backlog</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="backlog-copy">Copy backlog handoff</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-governance-show">Closeout JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-governance-export">Export closeout</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-escalation-show">Escalation JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-escalation-export">Export escalation</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-escalation-copy">Copy escalation</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-escalation-ack">Esc ACK</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-escalation-snooze">Esc Snooze</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-escalation-resolve">Esc Resolve</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-escalation-log-show">Exec JSON</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-escalation-log-export">Export exec</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="closeout-escalation-log-copy">Copy exec</button>\n'
            '            </div>\n'
            '            <div class="sideHandoffTools">\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="backlog-batch-ack">Batch ACK</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="backlog-batch-snooze">Batch Snooze</button>\n'
            '              <button class="sideHandoffBtn" type="button" data-handoff-remediation-plan-action="backlog-batch-profile-check">Batch profile</button>\n'
            '            </div>\n'
            '            <div id="sideHandoffQualityPolicy" class="sideHandoffMeta sideHandoffAdoption">Quality policy: Strict (strict)</div>\n'
            '            <div id="sideHandoffComposer" class="sideHandoffMeta sideHandoffAdoption">Composer: шаблон не зібрано</div>\n'
            '            <div id="sideHandoffQuality" class="sideHandoffMeta sideHandoffAdoption">Quality: NOT-READY</div>\n'
            '            <div id="sideHandoffQualityExplain" class="sideHandoffMeta sideHandoffAdoption">Quality explain: очікується перевірка.</div>\n'
            '            <div id="sideHandoffRemediationSummary" class="sideHandoffMeta sideHandoffAdoption">Remediation KPI: applied=0 · skipped=0 · override=0 · TTR avg/p95=0s/0s · open=—</div>\n'
            '            <div id="sideHandoffRemediationGovernance" class="sideHandoffMeta sideHandoffAdoption">Governance OK · profile=Standard · override=0%/25% · p95=0s/300s</div>\n'
            '            <div id="sideHandoffRemediationActions" class="sideHandoffMeta sideHandoffAdoption">Next: Governance OK — тримайте поточний remediation cadence.</div>\n'
            '            <div id="sideHandoffRemediationIncidentSummary" class="sideHandoffMeta sideHandoffAdoption">Incidents: active=0 · snoozed=0 · acked=0</div>\n'
            '            <div id="sideHandoffRemediationIncidentSla" class="sideHandoffMeta sideHandoffAdoption">Incident SLA: active=0 · snoozed=0 · acked=0 · oldest=—</div>\n'
            '            <div id="sideHandoffRemediationIncidentFeed" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '            <div id="sideHandoffRemediationIncidentDigest" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '            <div id="sideHandoffRemediationIncidentTriage" class="sideHandoffMeta sideHandoffAdoption">Digest triage: очікується digest.</div>\n'
            '            <div id="sideHandoffRemediationPlanSummary" class="sideHandoffMeta sideHandoffAdoption">Planner: digest clean</div>\n'
            '            <div id="sideHandoffRemediationPlan" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '            <div id="sideHandoffRemediationDecisionCoverage" class="sideHandoffMeta sideHandoffAdoption">Decision coverage: 0/0 (100%)</div>\n'
            '            <div id="sideHandoffRemediationDecisionLedger" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '            <div id="sideHandoffRemediationDecisionBacklogSummary" class="sideHandoffMeta sideHandoffAdoption">Decision backlog: clean · coverage=100%</div>\n'
            '            <div id="sideHandoffRemediationDecisionBacklog" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '            <div id="sideHandoffRemediationCloseoutSummary" class="sideHandoffMeta sideHandoffAdoption">Closeout OPEN · remaining=0 · coverage=0% · total=0</div>\n'
            '            <div id="sideHandoffRemediationCloseoutBoard" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '            <div id="sideHandoffRemediationEscalationSummary" class="sideHandoffMeta sideHandoffAdoption">Escalation NONE · route=handoff-only · action=monitor-only · remaining=0</div>\n'
            '            <div id="sideHandoffRemediationEscalationBoard" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '            <div id="sideHandoffRemediationEscalationExecutionSummary" class="sideHandoffMeta sideHandoffAdoption">Escalation exec IDLE · active=0 · stale=0 · oldest=—</div>\n'
            '            <div id="sideHandoffRemediationEscalationExecutionBoard" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '            <div id="sideHandoffRemediationTimelineMeta" class="sideHandoffMeta sideHandoffAdoption">Timeline: no remediation cycles yet</div>\n'
            '            <div id="sideHandoffRemediationTimeline" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '            <div id="sideHandoffMeta" class="sideHandoffMeta">Нотатка зміни: порожньо</div>\n'
            '            <div id="sideHandoffAdoption" class="sideHandoffMeta sideHandoffAdoption">Adoption: nav-flow ще без дій</div>\n'
            '            <div id="sideHandoffCoaching" class="sideHandoffMeta sideHandoffAdoption">Coach: стартуй із nav-search та compact-toggle.</div>\n'
            '            <div id="sideHandoffScorecard" class="sideHandoffMeta sideHandoffAdoption">Scorecard: 0/5 · WARN · немає практик за зміну.</div>\n'
            '            <div id="sideHandoffTrend" class="sideHandoffMeta sideHandoffAdoption">Trend: NO-DATA · збережіть handoff для формування baseline.</div>\n'
            '            <div id="sideHandoffTrendStatus" class="sideHandoffMeta sideHandoffAdoption">History: EMPTY</div>\n'
            '            <div id="sideHandoffTrendCompare" class="sideHandoffMeta sideHandoffAdoption">Compare: NO-DATA · збережіть handoff для baseline.</div>\n'
            '            <div id="sideHandoffTrendCoach" class="sideHandoffMeta sideHandoffAdoption">Trend coach: старт — зафіксуйте 2+ handoff notes, щоб отримати baseline.</div>\n'
            '            <div id="sideHandoffNextActions" class="sideHandoffMeta sideHandoffAdoption">Next actions:\n1) Відкрий цільовий розділ через nav-search + Enter.\n2) Застосуй Shift+Alt+N для швидкого фокусу на пошук.</div>\n'
            '            <div id="sideHandoffTimeline" class="sideHandoffTimeline"><span class="sideMiniEmpty">—</span></div>\n'
            '          </div>\n'
            "        </div>\n"
            "        </div>\n"
            "      </div>\n"
            '      <div class="sideMiniSection" data-side-mini="cheat">\n'
            '        <div class="sideMiniHead">\n'
            '          <div class="sideHint">Гарячі клавіші</div>\n'
            '          <div class="sideMiniHeadActions"><button class="sideMiniToggle" type="button" data-side-mini-toggle="cheat" aria-expanded="true" aria-controls="sideMiniBody-cheat" aria-label="Згорнути/розгорнути: гарячі клавіші" title="Згорнути блок"><span class="sideMiniChevron">▾</span></button></div>\n'
            "        </div>\n"
            '        <div id="sideMiniBody-cheat" class="sideMiniBody">\n'
            '          <div class="sideCheatList">\n'
            '          <div class="sideCheatRow"><code>Shift+Alt+A</code><span>Перейти до критичних алертів</span></div>\n'
            '          <div class="sideCheatRow"><code>Shift+Alt+I</code><span>Перейти до відкритих інцидентів</span></div>\n'
            '          <div class="sideCheatRow"><code>Shift+Alt+U</code><span>Відкрити аудит</span></div>\n'
            '          <div class="sideCheatRow"><code>Shift+Alt+N</code><span>Фокус на пошук меню</span></div>\n'
            '          <div class="sideCheatRow"><code>Shift+Alt+D</code><span>Застосувати рекомендацію доставки</span></div>\n'
            '          <div class="sideCheatRow"><code>Shift+Alt+K / R / E</code><span>Підтвердити / Повторити / Ескалювати</span></div>\n'
            '          <div class="sideCheatRow"><code>Shift+Alt+B / Y / G</code><span>Масово: підтвердити / повторити / ескалювати</span></div>\n'
            '          <div class="sideCheatRow"><code>Shift+Alt+P / J</code><span>Застосувати політику / Журнал доставки</span></div>\n'
            "          </div>\n"
            "        </div>\n"
            "      </div>\n"
            '      <div class="sideMiniSection" data-side-mini="favorites">\n'
            '        <div class="sideMiniHead">\n'
            '          <div class="sideHint">Обране</div>\n'
            '          <div class="sideMiniHeadActions">\n'
            '            <button id="sideFavoritesClear" class="sideMiniBtn" type="button">Очистити</button>\n'
            '            <button class="sideMiniToggle" type="button" data-side-mini-toggle="favorites" aria-expanded="true" aria-controls="sideMiniBody-favorites" aria-label="Згорнути/розгорнути: обране" title="Згорнути блок"><span class="sideMiniChevron">▾</span></button>\n'
            "          </div>\n"
            "        </div>\n"
            '        <div id="sideMiniBody-favorites" class="sideMiniBody">\n'
            '          <div id="sideFavoritesList" class="sideMiniList"><span class="sideMiniEmpty">—</span></div>\n'
            "        </div>\n"
            "      </div>\n"
            '      <div class="sideMiniSection" data-side-mini="recent">\n'
            '        <div class="sideMiniHead">\n'
            '          <div class="sideHint">Останні</div>\n'
            '          <div class="sideMiniHeadActions">\n'
            '            <button id="sideRecentClear" class="sideMiniBtn" type="button">Очистити</button>\n'
            '            <button class="sideMiniToggle" type="button" data-side-mini-toggle="recent" aria-expanded="true" aria-controls="sideMiniBody-recent" aria-label="Згорнути/розгорнути: останні" title="Згорнути блок"><span class="sideMiniChevron">▾</span></button>\n'
            "          </div>\n"
            "        </div>\n"
            '        <div id="sideMiniBody-recent" class="sideMiniBody">\n'
            '          <div id="sideRecentList" class="sideMiniList"><span class="sideMiniEmpty">—</span></div>\n'
            "        </div>\n"
            "      </div>\n"
            '      <div class="sideMiniSection" data-side-mini="session">\n'
            '        <div class="sideMiniHead">\n'
            '          <div class="sideHint">Сесія</div>\n'
            '          <div class="sideMiniHeadActions">\n'
            '            <button id="sideSessionClear" class="sideMiniBtn" type="button">Очистити</button>\n'
            '            <button class="sideMiniToggle" type="button" data-side-mini-toggle="session" aria-expanded="true" aria-controls="sideMiniBody-session" aria-label="Згорнути/розгорнути: сесія" title="Згорнути блок"><span class="sideMiniChevron">▾</span></button>\n'
            "          </div>\n"
            "        </div>\n"
            '        <div id="sideMiniBody-session" class="sideMiniBody">\n'
            '          <div id="sideSessionList" class="sideMiniList"><span class="sideMiniEmpty">—</span></div>\n'
            "        </div>\n"
            "      </div>\n"
            "    </aside>\n"
        )

    body_fragment = ""
    page_subnav_html = render_page_subnav(current, nav_groups)
    chips_fragment = f'\n            <div class="headerChips">{chips_html}</div>' if chips_html.strip() else ""
    if shell_layout:
        sidebar_fragment = sidebar_html() if show_sidebar else ""
        body_fragment = (
            f"  <div class=\"wrap\" style=\"max-width: {int(max_width)}px;\">\n"
            "    <div class=\"appShell\">\n"
            + sidebar_fragment
            + "      <div class=\"mainPane\">\n"
            "        <header>\n"
            "          <div class=\"title\">\n"
            f"            <h1>{safe_header_title}</h1>\n"
            + chips_fragment
            + "\n          </div>\n"
            "          <div class=\"toolbar\">\n"
            + toolbar_html
            + "\n          </div>\n"
            "        </header>\n"
            + page_subnav_html
            + body_html
            + "\n      </div>\n"
            "    </div>\n"
            "  </div>\n"
        )
    else:
        body_fragment = body_html + "\n"
    ui_build = "2026-02-18-pack33"
    return (
        "<!doctype html>\n"
        "<html lang=\"uk\">\n"
        "<head>\n"
        "  <meta charset=\"utf-8\" />\n"
        "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />\n"
        "  <meta name=\"color-scheme\" content=\"dark\" />\n"
        "  <link rel=\"icon\" href=\"data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='14' fill='%23111a33'/%3E%3Cpath d='M16 36c0-10 8-18 18-18h14v10H34c-4 0-8 4-8 8s4 8 8 8h14v10H34c-10 0-18-8-18-18z' fill='%237fb0ff'/%3E%3C/svg%3E\" />\n"
        f"  <title>{safe_title}</title>\n"
        "  <style>\n"
        + css
        + "\n  </style>\n"
        "</head>\n"
        f"<body data-ui-build=\"{ui_build}\">\n"
        "<div id=\"globalToast\" class=\"toast\" hidden></div>\n"
        + body_fragment
        + "<script>\n"
        + base_js
        + ("\n" if base_js else "")
        + script
        + "\n</script>\n"
        "</body>\n"
        "</html>\n"
    )


def render_legacy_admin_page(*, title: str, legacy_html: str) -> str:
    """Fallback helper for non-migrated pages; heavy fleet pages use render_admin_shell directly."""
    content = legacy_html.strip()
    style_start = content.find("<style>")
    style_end = content.find("</style>")
    body_start = content.find("<body>")
    script_start = content.find("<script>")
    script_end = content.rfind("</script>")
    if min(style_start, style_end, body_start, script_start, script_end) < 0:
        raise ValueError("legacy_html must include <style>, <body>, and <script> sections")
    extra_css = content[style_start + len("<style>") : style_end].strip()
    body_html = content[body_start + len("<body>") : script_start].strip()
    script = content[script_start + len("<script>") : script_end].strip()
    wrap_start = body_html.find("<div class=\"wrap\"")
    wrap_open = body_html.find(">", wrap_start) if wrap_start >= 0 else -1
    wrap_close = body_html.rfind("</div>")
    if min(wrap_start, wrap_open, wrap_close) >= 0 and wrap_close > wrap_open:
        wrap_inner = body_html[wrap_open + 1 : wrap_close]
        header_start = wrap_inner.find("<header>")
        header_end = wrap_inner.find("</header>", header_start) if header_start >= 0 else -1
        if min(header_start, header_end) >= 0 and header_end > header_start:
            header_inner = wrap_inner[header_start + len("<header>") : header_end]
            title_start = header_inner.find("<div class=\"title\">")
            title_end = header_inner.find("</div>", title_start) if title_start >= 0 else -1
            toolbar_start = header_inner.find("<div class=\"toolbar\">")
            toolbar_end = header_inner.find("</div>", toolbar_start) if toolbar_start >= 0 else -1
            if min(title_start, title_end, toolbar_start, toolbar_end) >= 0:
                title_inner = header_inner[title_start + len("<div class=\"title\">") : title_end]
                toolbar_html = header_inner[toolbar_start + len("<div class=\"toolbar\">") : toolbar_end].strip()
                h1_start = title_inner.find("<h1>")
                h1_end = title_inner.find("</h1>", h1_start) if h1_start >= 0 else -1
                if min(h1_start, h1_end) >= 0:
                    raw_h1 = title_inner[h1_start + len("<h1>") : h1_end]
                    header_title = re.sub(r"<[^>]+>", "", raw_h1).strip() or title
                    chips_html = (title_inner[:h1_start] + title_inner[h1_end + len("</h1>") :]).strip()
                    clean_body = wrap_inner[header_end + len("</header>") :].strip()
                    max_width_match = re.search(
                        r"\.wrap\s*\{[^}]*max-width:\s*([0-9]+)px",
                        extra_css,
                        flags=re.IGNORECASE | re.DOTALL,
                    )
                    max_width = int(max_width_match.group(1)) if max_width_match else 1280
                    return render_admin_shell(
                        title=title,
                        header_title=header_title,
                        chips_html=chips_html,
                        toolbar_html=toolbar_html,
                        body_html=clean_body,
                        script=script,
                        extra_css=extra_css,
                        max_width=max_width,
                    ).strip()
    return render_admin_shell(
        title=title,
        header_title="",
        chips_html="",
        toolbar_html="",
        body_html=body_html,
        script=script,
        extra_css=extra_css,
        shell_layout=False,
    ).strip()
