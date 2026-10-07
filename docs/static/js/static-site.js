/* Client-side behaviour for the static (GitHub Pages) build.
   The Flask app filters events on the server; on a static host there is no
   server, so this filters the already-rendered cards in the browser. */
(function () {
  "use strict";

  var grid = document.querySelector("[data-static-events]");
  if (!grid) return;

  var form = document.querySelector("[data-filter-form]");
  var cards = [].slice.call(grid.querySelectorAll(".event-card"));
  var countEl = document.querySelector("[data-result-count]");

  var emptyEl = document.createElement("div");
  emptyEl.className = "empty";
  emptyEl.style.display = "none";
  emptyEl.innerHTML = '<p>No events match your filters. <a href="events.html">Reset</a></p>';
  grid.parentNode.insertBefore(emptyEl, grid.nextSibling);

  function val(name) {
    if (!form) return "";
    var el = form.querySelector('[name="' + name + '"]');
    return el ? String(el.value || "").trim().toLowerCase() : "";
  }

  function apply() {
    var q = val("q"), cat = val("category"), status = val("status"), dept = val("department");
    var shown = 0;
    cards.forEach(function (c) {
      var text = (c.dataset.text || "").toLowerCase();
      var ok = true;
      if (q && text.indexOf(q) === -1) ok = false;
      if (cat && (c.dataset.category || "").toLowerCase() !== cat) ok = false;
      if (status && status !== "all" && (c.dataset.status || "") !== status) ok = false;
      if (dept && text.indexOf(dept) === -1) ok = false;
      c.style.display = ok ? "" : "none";
      if (ok) shown++;
    });
    if (countEl) countEl.textContent = shown + (shown === 1 ? " event" : " events") + " found.";
    grid.style.display = shown ? "" : "none";
    emptyEl.style.display = shown ? "none" : "block";
  }

  if (form) {
    form.addEventListener("submit", function (e) { e.preventDefault(); apply(); });
    form.addEventListener("change", apply);
    form.addEventListener("input", apply);
    // honour ?status=past / ?category=... etc. from links
    try {
      var params = new URLSearchParams(window.location.search);
      ["q", "category", "status", "department"].forEach(function (k) {
        if (params.has(k)) {
          var el = form.querySelector('[name="' + k + '"]');
          if (el) el.value = params.get(k);
        }
      });
      // the page ships every event in the DOM; default the view to Upcoming
      if (!params.has("status")) {
        var s = form.querySelector('[name="status"]');
        if (s) s.value = "upcoming";
      }
    } catch (e) { /* older browsers: ignore */ }
  }
  apply();
})();
