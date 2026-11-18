(function () {
  "use strict";

  function initialise(directory) {
    var input = directory.querySelector("[data-network-filter]");
    var result = directory.querySelector("[data-network-results]");
    var cards = Array.prototype.slice.call(directory.querySelectorAll("[data-network-site-card]"));
    var categories = Array.prototype.slice.call(directory.querySelectorAll("[data-network-category]"));
    if (!input || !result || !cards.length) return;

    function update() {
      var query = input.value.trim().toLocaleLowerCase();
      var visible = 0;
      cards.forEach(function (card) {
        var matches = !query || (card.getAttribute("data-search-text") || "").indexOf(query) !== -1;
        card.hidden = !matches;
        if (matches) visible += 1;
      });
      categories.forEach(function (category) {
        var categoryVisible = category.querySelector("[data-network-site-card]:not([hidden])");
        category.hidden = !categoryVisible;
        var heading = category.querySelector("[id]");
        if (heading) {
          var link = directory.querySelector('[data-network-category-link="' + heading.id + '"]');
          if (link) link.hidden = !categoryVisible;
        }
      });
      result.textContent = query
        ? "Showing " + visible + " of " + cards.length + " sites"
        : "Showing all " + cards.length + " sites";
    }

    input.addEventListener("input", update);
    update();
  }

  function initSatelliteClickTracking(directory) {
    var cards = Array.prototype.slice.call(directory.querySelectorAll("[data-network-site-card]"));
    cards.forEach(function (card, index) {
      if (card.dataset && card.dataset.satelliteClickBound) return;
      if (card.dataset) card.dataset.satelliteClickBound = "1";
      var links = Array.prototype.slice.call(card.querySelectorAll("a[href]"));
      links.forEach(function (link) {
        link.addEventListener("click", function () {
          var destination;
          try {
            destination = new URL(link.href, window.location.href);
          } catch (err) {
            return;
          }
          var host = String(destination.hostname || "").toLocaleLowerCase();
          if (!host || host === String(window.location.hostname || "").toLocaleLowerCase()) return;
          var network = "";
          var satelliteId = host;
          var suffix = ".branchoria.com";
          if (host.slice(-suffix.length) === suffix) {
            network = "branchoria";
            satelliteId = host.slice(0, host.length - suffix.length);
          }
          var kind = /(^|\s)network-site-link(\s|$)/.test(String(link.className || "")) ? "explore" : "title";
          var filterInput = directory.querySelector("[data-network-filter]");
          var detail = {
            satellite_id: satelliteId,
            satellite_host: host,
            network: network,
            card_position: index + 1,
            card_total: cards.length,
            link_kind: kind,
            link_text: String(link.textContent || "").replace(/\s+/g, " ").trim().slice(0, 120),
            directory_query: filterInput ? String(filterInput.value || "").trim().slice(0, 120) : "",
            page_path: String(window.location.pathname || "")
          };
          document.dispatchEvent(new CustomEvent("phoenix:satellite-click", { detail: detail }));
          if (typeof window.gtag !== "function") return;
          window.gtag("event", "satellite_click", Object.assign({}, detail, {
            transport_type: "beacon"
          }));
        });
      });
    });
  }

  document.querySelectorAll("[data-network-directory]").forEach(initialise);
  document.querySelectorAll("[data-network-directory]").forEach(initSatelliteClickTracking);
})();
