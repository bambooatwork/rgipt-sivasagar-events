/* RGIPT Sivasagar Campus — front-end behaviour */
(function () {
  "use strict";

  // Signals that JS is alive so the page keeps its reveal animations.
  window.__rgiptReady = true;

  /* ----------------------------------------------------------- Theme */
  const THEME_KEY = "rgipt-theme";
  const root = document.documentElement;

  function applyTheme(theme) {
    root.setAttribute("data-theme", theme);
    document.querySelectorAll("[data-theme-icon]").forEach((el) => {
      el.textContent = theme === "light" ? "\u263e" : "\u2600";
    });
  }
  const saved = localStorage.getItem(THEME_KEY);
  applyTheme(saved || "light");

  document.addEventListener("click", function (e) {
    const t = e.target.closest("[data-theme-toggle]");
    if (t) {
      const next = root.getAttribute("data-theme") === "light" ? "dark" : "light";
      localStorage.setItem(THEME_KEY, next);
      applyTheme(next);
    }
  });

  /* --------------------------------------------------------- Navbar */
  const nav = document.querySelector(".nav");
  const onScroll = () => nav && nav.classList.toggle("scrolled", window.scrollY > 8);
  window.addEventListener("scroll", onScroll, { passive: true });
  onScroll();

  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => navLinks.classList.toggle("open"));
    navLinks.addEventListener("click", (e) => {
      if (e.target.tagName === "A") navLinks.classList.remove("open");
    });
  }

  /* -------------------------------------------------- Reveal on scroll */
  const revealEls = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && revealEls.length) {
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((en) => {
          if (en.isIntersecting) {
            en.target.classList.add("in");
            io.unobserve(en.target);
          }
        });
      },
      { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
    );
    revealEls.forEach((el, i) => {
      el.style.transitionDelay = (i % 4) * 70 + "ms";
      io.observe(el);
    });
  } else {
    revealEls.forEach((el) => el.classList.add("in"));
  }

  /* ------------------------------------------------------- Counters */
  const counters = document.querySelectorAll("[data-count]");
  if ("IntersectionObserver" in window && counters.length) {
    const co = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (!en.isIntersecting) return;
        const el = en.target;
        const target = parseFloat(el.dataset.count) || 0;
        const dur = 1100;
        const start = performance.now();
        function tick(now) {
          const p = Math.min((now - start) / dur, 1);
          const eased = 1 - Math.pow(1 - p, 3);
          el.textContent = Math.round(target * eased).toLocaleString("en-IN");
          if (p < 1) requestAnimationFrame(tick);
        }
        requestAnimationFrame(tick);
        co.unobserve(el);
      });
    }, { threshold: 0.4 });
    counters.forEach((c) => co.observe(c));
  }

  /* ---------------------------------------------------- Bar charts */
  document.querySelectorAll(".bar-row .track > i[data-width]").forEach((bar) => {
    requestAnimationFrame(() => { bar.style.width = bar.dataset.width + "%"; });
  });

  /* ------------------------------------------------------ Countdown */
  document.querySelectorAll("[data-countdown]").forEach((el) => {
    const target = new Date(el.dataset.countdown + "T00:00:00").getTime();
    const out = el.querySelector(".countdown") || el;
    function render() {
      const diff = target - Date.now();
      if (diff <= 0) { out.innerHTML = '<div class="cd"><b>\u2713</b><span>Live now</span></div>'; return; }
      const d = Math.floor(diff / 86400000);
      const h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000);
      const s = Math.floor((diff % 60000) / 1000);
      out.innerHTML =
        '<div class="cd"><b>' + d + "</b><span>Days</span></div>" +
        '<div class="cd"><b>' + h + "</b><span>Hrs</span></div>" +
        '<div class="cd"><b>' + m + "</b><span>Min</span></div>" +
        '<div class="cd"><b>' + s + "</b><span>Sec</span></div>";
    }
    render();
    setInterval(render, 1000);
  });

  /* --------------------------------------------------- Flash toasts */
  document.querySelectorAll(".flash").forEach((f) => {
    const close = f.querySelector("button");
    if (close) close.addEventListener("click", () => f.remove());
    setTimeout(() => {
      f.style.transition = "opacity .4s, transform .4s";
      f.style.opacity = "0";
      f.style.transform = "translateX(40px)";
      setTimeout(() => f.remove(), 420);
    }, 6000);
  });

  /* ------------------------------------ Generic client-side filter */
  document.querySelectorAll("[data-filter-input]").forEach((input) => {
    const scope = input.closest(".container") || document;
    const items = scope.querySelectorAll("[data-filter-item]");
    const empty = scope.querySelector("[data-filter-empty]");
    const apply = () => {
      const q = input.value.trim().toLowerCase();
      let shown = 0;
      items.forEach((it) => {
        const hay = (it.dataset.text || it.textContent).toLowerCase();
        const hit = !q || hay.indexOf(q) !== -1;
        it.style.display = hit ? "" : "none";
        if (hit) shown++;
      });
      if (empty) empty.style.display = shown ? "none" : "block";
    };
    input.addEventListener("input", apply);
  });

  /* --------------------------------------------- Confirm destructive */
  document.querySelectorAll("form[data-confirm]").forEach((form) => {
    form.addEventListener("submit", (e) => {
      if (!window.confirm(form.dataset.confirm)) e.preventDefault();
    });
  });

  /* ------------------------------------------- Auto-submit filters */
  document.querySelectorAll("[data-autosubmit]").forEach((el) => {
    el.addEventListener("change", () => el.form && el.form.submit());
  });

  /* ------------------------------------ Registration capacity guard */
  document.querySelectorAll("[data-capacity-form]").forEach((form) => {
    form.addEventListener("submit", () => {
      const btn = form.querySelector("button[type=submit]");
      if (btn) { btn.disabled = true; btn.textContent = "Submitting\u2026"; }
    });
  });
})();
