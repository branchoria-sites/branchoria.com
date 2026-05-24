(function () {
  var root = document.documentElement;
  var storageKey = "phoenix-color-mode";

  function safeRead() {
    try {
      return window.localStorage.getItem(storageKey);
    } catch (err) {
      return null;
    }
  }

  function safeWrite(value) {
    try {
      window.localStorage.setItem(storageKey, value);
    } catch (err) {
      // Ignore storage failures.
    }
  }

  function systemTheme() {
    try {
      return window.matchMedia && window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
    } catch (err) {
      return "light";
    }
  }

  function applyTheme(mode, persist) {
    var nextMode = mode === "dark" || mode === "light" ? mode : "automatic";
    var resolved = nextMode === "automatic" ? systemTheme() : nextMode;
    root.setAttribute("data-color-mode", nextMode);
    root.setAttribute("data-theme", resolved);
    var button = document.querySelector("[data-theme-toggle]");
    if (button) {
      var target = resolved === "dark" ? "light" : "dark";
      button.setAttribute("aria-label", "Switch to " + target + " mode");
      button.setAttribute("title", "Switch to " + target + " mode");
      button.setAttribute("aria-pressed", String(resolved === "dark"));
    }
    if (persist) {
      safeWrite(nextMode);
    }
  }

  function init() {
    applyTheme(safeRead() || root.getAttribute("data-appearance-color-default") || "automatic", false);
    var button = document.querySelector("[data-theme-toggle]");
    if (button) {
      button.addEventListener("click", function () {
        applyTheme(root.getAttribute("data-theme") === "dark" ? "light" : "dark", true);
      });
    }
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
