(() => {
  const search = document.getElementById("v2NavSearch");
  const status = document.getElementById("v2NavSearchStatus");
  const items = Array.from(document.querySelectorAll(".v2NavItem"));
  const groups = Array.from(document.querySelectorAll(".v2NavGroup"));

  function setStatus(text) {
    if (!status) return;
    status.textContent = String(text || "");
  }

  function applyFilter() {
    if (!(search instanceof HTMLInputElement)) return;
    const q = String(search.value || "").trim().toLowerCase();
    if (!q) {
      for (const it of items) it.classList.remove("v2FilteredOut");
      for (const g of groups) g.classList.remove("v2FilteredOut");
      setStatus("");
      return;
    }

    let shown = 0;
    for (const it of items) {
      const text = String(it.textContent || "").trim().toLowerCase();
      const ok = text.includes(q);
      it.classList.toggle("v2FilteredOut", !ok);
      if (ok) shown += 1;
    }

    for (const g of groups) {
      const anyVisible = !!g.querySelector(".v2NavItem:not(.v2FilteredOut)");
      g.classList.toggle("v2FilteredOut", !anyVisible);
      if (anyVisible) g.open = true;
    }

    setStatus(`результатів: ${shown}`);
  }

  if (search instanceof HTMLInputElement) {
    search.addEventListener("input", applyFilter);
  }

  // Hotkey: "/" focuses menu search (keyboard-first).
  document.addEventListener("keydown", (e) => {
    if (!(search instanceof HTMLInputElement)) return;
    if (e.key !== "/") return;
    if (e.altKey || e.ctrlKey || e.metaKey) return;
    const active = document.activeElement;
    if (active && (active.tagName === "INPUT" || active.tagName === "TEXTAREA" || active.isContentEditable)) return;
    e.preventDefault();
    search.focus({ preventScroll: true });
  });
})();

