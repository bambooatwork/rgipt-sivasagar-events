/* =====================================================================
   Public site — shell, page rendering, filtering, countdown, registration.
   Loaded as an ES module from every public page.
   ===================================================================== */
import * as store from "./store.js";
import { escapeHtml, formatDate, inr, isPast } from "./store.js";

/* ------------------------------------------------------------- shell */
const NAV = [
  ["index.html", "Home"], ["events.html", "Events"], ["announcements.html", "Announcements"],
  ["faculty.html", "Faculty"], ["about.html", "About"], ["contact.html", "Contact"]
];

function shell(active) {
  const nav = document.getElementById("nav");
  if (nav) {
    nav.innerHTML = `
      <div class="topbar"><div class="container">
        <div class="tb-left"><span>Rajiv Gandhi Institute of Petroleum Technology</span>
          <span class="sep">&middot;</span><span>Sivasagar Campus, Assam</span></div>
        <div class="tb-right">
          <a href="tel:03772295231">03772-295231</a><span class="sep">&middot;</span>
          <a href="mailto:coordinator-aei@rgipt.ac.in">coordinator-aei@rgipt.ac.in</a>
        </div>
      </div></div>
      <nav class="nav"><div class="container">
        <a class="brand" href="index.html">
          <img class="logo" src="img/logo.png" alt="RGIPT logo">
          <span class="brand-text"><b>RGIPT Sivasagar</b><span>Campus Events</span></span>
        </a>
        <div class="nav-links">
          ${NAV.map(([h, t]) => `<a href="${h}" class="${active === h ? "active" : ""}">${t}</a>`).join("")}
        </div>
        <div class="nav-actions">
          <a class="btn btn-sm" href="admin.html">Admin</a>
          <button class="icon-btn nav-toggle" aria-label="Menu">&#9776;</button>
        </div>
      </div></nav>`;
  }
  const foot = document.getElementById("footer");
  if (foot) {
    foot.innerHTML = `
      <footer class="footer"><div class="container">
        <div class="footer-grid">
          <div>
            <a class="brand" href="index.html" style="margin-bottom:12px">
              <img class="logo" src="img/logo.png" alt="RGIPT logo">
              <span class="brand-text"><b>RGIPT Sivasagar</b><span>Campus Events</span></span>
            </a>
            <p class="muted" style="font-size:.9rem">Rajiv Gandhi Institute of Petroleum Technology, Sivasagar Campus. An Institution of National Importance under the Ministry of Petroleum &amp; Natural Gas, Government of India.</p>
          </div>
          <div><h4>Explore</h4>
            <a href="events.html">All Events</a><a href="events.html?status=past">Past Events</a>
            <a href="announcements.html">Announcements</a><a href="faculty.html">Faculty</a></div>
          <div><h4>Campus</h4>
            <a href="about.html">About the Campus</a><a href="contact.html">Contact Us</a>
            <a href="admin.html">Admin</a></div>
          <div><h4>Reach Us</h4>
            <p class="muted" style="font-size:.9rem;margin:0 0 6px">Gohain Gaon, Akhoiphutia, Dhaiali Road, Sivasagar &ndash; 785697, Assam</p>
            <p class="muted" style="font-size:.9rem;margin:0 0 4px">Phone: 03772-295231</p>
            <p class="muted" style="font-size:.9rem;margin:0">Email: coordinator-aei@rgipt.ac.in</p></div>
        </div>
        <div class="copy"><span>&copy; ${new Date().getFullYear()} RGIPT Sivasagar Campus.</span>
          <span>Event Management Portal</span></div>
      </div></footer>`;
  }
  const t = document.querySelector(".nav-toggle");
  const l = document.querySelector(".nav-links");
  if (t && l) t.addEventListener("click", () => l.classList.toggle("open"));
}

/* ------------------------------------------------------- notices/errors */
function notice(msg, kind) {
  return `<div class="panel" style="border-left:4px solid var(--${kind || "orange"})"><p class="mb-0">${msg}</p></div>`;
}

function setupNotice() {
  return notice(
    `<strong>Backend not configured yet.</strong> Open <code>docs/js/firebase-config.js</code>
     and paste your Firebase project values (see <strong>SETUP.md</strong>), then reload.
     Nothing is shown here until the database is connected &mdash; no placeholder content.`, "orange");
}

function errorNotice(e) {
  return notice(`<strong>Could not load data.</strong> ${escapeHtml(e && e.message ? e.message : e)}<br>
     This usually means the Firebase SDK could not be fetched (check the internet
     connection) or your Firestore rules do not allow public reads. See
     <strong>SETUP.md</strong>.`, "orange");
}

/* ------------------------------------------------------------- renderers */
function eventRow(e) {
  const past = isPast(e);
  const d = e.eventDate ? new Date(e.eventDate + "T00:00:00") : null;
  const day = d ? String(d.getDate()).padStart(2, "0") : "";
  const mon = d ? d.toLocaleDateString("en-GB", { month: "short" }) : "";
  return `<a class="row" href="event.html?id=${encodeURIComponent(e.id)}">
    <div class="row-date"><b>${day}</b><span>${mon}</span></div>
    <div class="row-main"><h3>${escapeHtml(e.title)}</h3><p>${escapeHtml(e.shortDescription)}</p></div>
    <div class="row-meta">
      <span class="cat"><span class="dot ${past ? "past" : ""}"></span>${escapeHtml(e.category)}</span>
      <span>${escapeHtml((e.venue || "").split(",")[0])}</span>
    </div>
    <div class="row-end"><span class="price ${e.fee === 0 ? "free" : ""}">${inr(e.fee)}</span>
      <span class="ar">&#8594;</span></div>
  </a>`;
}

function annRow(a) {
  return `<a class="ann-row" href="announcement.html?id=${encodeURIComponent(a.id)}">
    <div class="when">${formatDate(a.publishedAt)}${a.isPinned ? '<span class="flag">Pinned</span>' : ""}</div>
    <div><h3>${escapeHtml(a.title)}</h3><p>${escapeHtml(a.body)}</p></div>
  </a>`;
}

function secHead(num, title, linkHref, linkText) {
  return `<header class="sec-head">
    <div class="sec-title"><span class="sec-num">${num}</span><h2>${title}</h2></div>
    ${linkHref ? `<a class="sec-link" href="${linkHref}">${linkText} <span class="ar">&#8594;</span></a>` : ""}
  </header>`;
}

/* ------------------------------------------------------------- pages */
async function home(app) {
  if (!store.isConfigured()) { app.innerHTML = setupNotice(); return; }
  try {
    const [events, anns] = await Promise.all([store.listEvents(), store.listAnnouncements()]);
    const upcoming = events.filter((e) => !isPast(e));
    const past = events.filter(isPast).slice(-3).reverse();
    const next = upcoming[0];

    app.innerHTML = `
      ${upcoming.length ? `<div class="ticker"><div class="track">${[0, 1].map(() =>
        upcoming.slice(0, 5).map((e) => `<span class="item">${escapeHtml(e.title)} &mdash; ${formatDate(e.eventDate, { day: "2-digit", month: "short" })}</span>`).join("")
      ).join("")}</div></div>` : ""}
      <section class="hero"><div class="container"><div class="hero-grid">
        <div class="hero-copy">
          <p class="kicker">Sivasagar Campus &middot; Assam</p>
          <h1>Where campus <mark>events</mark> come to life.</h1>
          <p class="lead">Discover, register and never miss a moment at RGIPT Sivasagar Campus &mdash; from the national-level Urjotsav tech fest and Krida Oorja sports meet to hackathons, workshops and cultural evenings.</p>
          <div class="hero-actions"><a class="btn btn-primary" href="events.html">Browse events</a></div>
        </div>
        ${next ? `<aside class="poster" data-countdown="${next.eventDate}">
          <div><p class="p-kicker">Next up</p>
            <div class="p-date">${formatDate(next.eventDate, { day: "2-digit", month: "short" })}</div>
            <h3>${escapeHtml(next.title)}</h3>
            <p class="p-meta">${escapeHtml((next.venue || "").split(",")[0])} &middot; ${escapeHtml(next.category)}</p></div>
          <div class="countdown"></div>
          <a class="btn btn-poster" href="event.html?id=${encodeURIComponent(next.id)}">View event &#8594;</a>
        </aside>` : ""}
      </div></div></section>
      <div class="band"><div class="container"><div class="stat-row">
        <div class="stat"><b>${events.length}</b><span>Events</span></div>
        <div class="stat"><b>${upcoming.length}</b><span>Upcoming</span></div>
        <div class="stat"><b>${new Set(events.map((e) => e.category)).size}</b><span>Categories</span></div>
        <div class="stat"><b>${anns.length}</b><span>Notices</span></div>
      </div></div></div>
      <section class="section-tight"><div class="container">
        ${secHead("01", "Next up", "events.html?status=upcoming", "All upcoming")}
        <div class="listing">${upcoming.length ? upcoming.slice(0, 6).map((e) => eventRow(e)).join("")
          : '<p class="listing-note">No upcoming events scheduled right now.</p>'}</div>
      </div></section>
      <section class="section-tight"><div class="container">
        ${secHead("02", "Notice board", "announcements.html", "All announcements")}
        <div class="listing">${anns.length ? anns.slice(0, 4).map(annRow).join("")
          : '<p class="listing-note">No announcements published yet.</p>'}</div>
      </div></section>
      ${past.length ? `<section class="section-tight"><div class="container">
        ${secHead("03", "Recently concluded", "events.html?status=past", "Past events")}
        <div class="listing">${past.map((e) => eventRow(e)).join("")}</div>
      </div></section>` : ""}`;
    startCountdowns();
  } catch (e) { app.innerHTML = errorNotice(e); }
}

async function eventsPage(app) {
  if (!store.isConfigured()) { app.innerHTML = setupNotice(); return; }
  try {
    const params = new URLSearchParams(location.search);
    const events = await store.listEvents();
    app.innerHTML = `
      <header class="sec-head">
        <div class="sec-title"><span class="sec-num">/</span><h1 style="font-size:clamp(1.9rem,4vw,2.8rem);margin:0">Events</h1></div>
        <p class="muted mb-0" id="count" style="font-size:.88rem"></p>
      </header>
      <form class="filter-bar" id="filter">
        <div class="field"><label>Search</label><input type="text" name="q" placeholder="Title, organiser or venue"></div>
        <div class="field"><label>Category</label><select name="category">
          <option value="">All</option>
          ${[...new Set(events.map((e) => e.category))].sort().map((c) => `<option>${escapeHtml(c)}</option>`).join("")}
        </select></div>
        <div class="field"><label>When</label><select name="status">
          <option value="upcoming">Upcoming</option><option value="past">Past</option><option value="all">All</option>
        </select></div>
        <div class="field"><label>&nbsp;</label><button class="btn" type="submit">Filter</button></div>
      </form>
      <div class="listing" id="list"></div>
      <div class="empty" id="empty" style="display:none"><p>No events match your filters.</p></div>`;

    const list = app.querySelector("#list"), count = app.querySelector("#count"),
      empty = app.querySelector("#empty"), form = app.querySelector("#filter");
    ["q", "category", "status"].forEach((k) => { if (params.has(k)) form.elements[k].value = params.get(k); });

    const apply = () => {
      const q = form.elements.q.value.trim().toLowerCase();
      const cat = form.elements.category.value, st = form.elements.status.value;
      const rows = events.filter((e) => {
        const hay = (e.title + " " + e.shortDescription + " " + e.organizer + " " + e.venue + " " + e.category).toLowerCase();
        if (q && hay.indexOf(q) === -1) return false;
        if (cat && e.category !== cat) return false;
        if (st === "upcoming" && isPast(e)) return false;
        if (st === "past" && !isPast(e)) return false;
        return true;
      });
      list.innerHTML = rows.map((e) => eventRow(e)).join("");
      count.textContent = rows.length + (rows.length === 1 ? " event" : " events") + " found.";
      empty.style.display = rows.length ? "none" : "block";
    };
    form.addEventListener("submit", (ev) => { ev.preventDefault(); apply(); });
    form.addEventListener("change", apply);
    form.addEventListener("input", apply);
    apply();
  } catch (e) { app.innerHTML = errorNotice(e); }
}

async function eventPage(app) {
  if (!store.isConfigured()) { app.innerHTML = setupNotice(); return; }
  const id = new URLSearchParams(location.search).get("id");
  if (!id) { app.innerHTML = notice("No event specified.", "orange"); return; }
  try {
    const e = await store.getEvent(id);
    if (!e) { app.innerHTML = notice("That event could not be found.", "orange"); return; }
    const past = isPast(e);
    app.innerHTML = `
      <p class="muted" style="font-size:.85rem"><a href="events.html">Events</a> / ${escapeHtml(e.category)}</p>
      <div class="detail-grid">
        <div>
          <div class="detail-head">
            <div class="flex items-center gap wrap">
              <span class="chip">${escapeHtml(e.category)}</span>
              ${e.isFeatured ? '<span class="badge pinned">Featured</span>' : ""}
              ${past ? '<span class="badge past">Completed</span>'
                : '<span class="badge live">Registration open</span>'}
            </div>
            <h1>${escapeHtml(e.title)}</h1>
            <p class="detail-lede">${escapeHtml(e.shortDescription)}</p>
          </div>
          ${past ? "" : `<div data-countdown="${e.eventDate}" style="display:flex;align-items:center;gap:24px;flex-wrap:wrap;justify-content:space-between;margin-bottom:26px">
            <div><strong style="font-family:var(--font-display);font-size:1.05rem">Starts in</strong>
              <p class="muted mb-0" style="font-size:.84rem">${formatDate(e.eventDate, { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}</p></div>
            <div class="countdown" style="min-width:280px"></div></div>`}
          <div class="rule-block"><h3>About this event</h3><div class="prose">${escapeHtml(e.description)}</div></div>
          <div class="rule-block mt-3"><h3>Key dates</h3><div class="timeline">
            ${e.registrationDeadline ? `<div class="item"><div class="dotcol"><span class="dot"></span><span class="line"></span></div>
              <div class="txt"><strong>Registration closes</strong><p class="muted mb-0">${formatDate(e.registrationDeadline, { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}</p></div></div>` : ""}
            <div class="item"><div class="dotcol"><span class="dot"></span>${e.endDate && e.endDate !== e.eventDate ? '<span class="line"></span>' : ""}</div>
              <div class="txt"><strong>Event begins</strong><p class="muted mb-0">${formatDate(e.eventDate, { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}, ${escapeHtml(e.startTime)}</p></div></div>
            ${e.endDate && e.endDate !== e.eventDate ? `<div class="item"><div class="dotcol"><span class="dot"></span></div>
              <div class="txt"><strong>Event concludes</strong><p class="muted mb-0">${formatDate(e.endDate, { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}, ${escapeHtml(e.endTime)}</p></div></div>` : ""}
          </div></div>
        </div>
        <aside><div class="info-card">
          <div class="flex between items-center"><span class="price-tag">${inr(e.fee)}</span>
            <span class="chip">${escapeHtml(e.teamSize)}</span></div>
          <div class="divider"></div>
          <dl class="dl">
            <dt>Organiser</dt><dd>${escapeHtml(e.organizer)}</dd>
            <dt>Venue</dt><dd>${escapeHtml(e.venue)}</dd>
            <dt>Capacity</dt><dd>${e.capacity} seats</dd>
            ${e.contactEmail ? `<dt>Contact</dt><dd style="word-break:break-all">${escapeHtml(e.contactEmail)}</dd>` : ""}
          </dl>
          <div class="divider"></div>
          ${past ? '<button class="btn btn-block" disabled>Event concluded</button>'
            : `<a class="btn btn-primary btn-block" href="register.html?id=${encodeURIComponent(e.id)}">Register</a>
               ${e.registrationDeadline ? `<p class="hint mt-2" style="text-align:center">Closes ${formatDate(e.registrationDeadline)}</p>` : ""}`}
        </div></aside>
      </div>`;
    startCountdowns();
  } catch (err) { app.innerHTML = errorNotice(err); }
}

async function announcementsPage(app) {
  if (!store.isConfigured()) { app.innerHTML = setupNotice(); return; }
  try {
    const anns = await store.listAnnouncements();
    app.innerHTML = `<header class="sec-head">
        <div class="sec-title"><span class="sec-num">/</span><h1 style="font-size:clamp(1.9rem,4vw,2.8rem);margin:0">Announcements</h1></div>
        <p class="muted mb-0" style="font-size:.88rem">Official updates from RGIPT Sivasagar Campus.</p>
      </header>
      <div class="listing">${anns.length ? anns.map(annRow).join("")
        : '<p class="listing-note">No announcements published yet.</p>'}</div>`;
  } catch (e) { app.innerHTML = errorNotice(e); }
}

async function announcementPage(app) {
  if (!store.isConfigured()) { app.innerHTML = setupNotice(); return; }
  const id = new URLSearchParams(location.search).get("id");
  if (!id) { app.innerHTML = notice("No announcement specified.", "orange"); return; }
  try {
    const a = await store.getAnnouncement(id);
    if (!a) { app.innerHTML = notice("That announcement could not be found.", "orange"); return; }
    const others = (await store.listAnnouncements()).filter((x) => x.id !== id).slice(0, 5);
    app.innerHTML = `
      <p class="muted" style="font-size:.85rem"><a href="announcements.html">Announcements</a> / ${escapeHtml(a.category)}</p>
      <div class="detail-grid">
        <article>
          <div class="detail-head">
            <div class="flex items-center gap wrap"><span class="chip">${escapeHtml(a.category)}</span>
              ${a.isPinned ? '<span class="badge pinned">Pinned</span>' : ""}</div>
            <h1>${escapeHtml(a.title)}</h1>
            <p class="muted mono mb-0">${formatDate(a.publishedAt, { weekday: "long", day: "2-digit", month: "long", year: "numeric" })}</p>
          </div>
          <div class="prose">${escapeHtml(a.body)}</div>
        </article>
        <aside><div class="info-card"><h3 style="font-size:1rem">More announcements</h3>
          <div class="listing">${others.length ? others.map(annRow).join("") : '<p class="listing-note">No other announcements.</p>'}</div>
        </div></aside>
      </div>`;
  } catch (e) { app.innerHTML = errorNotice(e); }
}

async function registerPage(app) {
  if (!store.isConfigured()) { app.innerHTML = setupNotice(); return; }
  const id = new URLSearchParams(location.search).get("id");
  if (!id) { app.innerHTML = notice("No event specified.", "orange"); return; }
  try {
    const e = await store.getEvent(id);
    if (!e) { app.innerHTML = notice("That event could not be found.", "orange"); return; }
    if (isPast(e)) { app.innerHTML = notice("Registration for this event has closed.", "orange"); return; }

    app.innerHTML = `
      <p class="muted" style="font-size:.9rem"><a href="events.html">Events</a> / <a href="event.html?id=${encodeURIComponent(e.id)}">${escapeHtml(e.title)}</a> / Register</p>
      <div class="detail-grid">
        <div class="panel">
          <span class="kicker">Registration form</span>
          <h2 style="margin-top:6px">Register for ${escapeHtml(e.title)}</h2>
          <p class="muted">Your ticket code appears instantly. Fields marked <span style="color:var(--orange)">*</span> are required.</p>
          <div id="formMsg"></div>
          <form id="regForm">
            <div class="form-grid">
              <div class="field"><label>Full name <span class="req">*</span></label><input name="name" required></div>
              <div class="field"><label>Email <span class="req">*</span></label><input type="email" name="email" required></div>
              <div class="field"><label>Phone</label><input name="phone"></div>
              <div class="field"><label>College / Institute</label><input name="college" value="RGIPT Sivasagar Campus"></div>
              <div class="field"><label>Department</label><input name="department"></div>
              <div class="field"><label>Year of study</label><input name="year"></div>
              <div class="field full"><label>Team name (${escapeHtml(e.teamSize)})</label><input name="teamName"></div>
              <div class="field full"><label>Anything we should know?</label><textarea name="notes"></textarea></div>
            </div>
            <button class="btn btn-primary" type="submit">Confirm registration</button>
          </form>
        </div>
        <aside><div class="info-card">
          <span class="chip">${escapeHtml(e.category)}</span>
          <h3 class="mt-2">${escapeHtml(e.title)}</h3>
          <div class="meta-list">
            <div class="row">${formatDate(e.eventDate, { day: "2-digit", month: "long", year: "numeric" })}</div>
            <div class="row">${escapeHtml(e.startTime)} &ndash; ${escapeHtml(e.endTime)}</div>
            <div class="row">${escapeHtml(e.venue)}</div>
          </div>
          <div class="divider"></div>
          <div class="seats"><span>Capacity</span><span>${e.capacity} seats</span></div>
        </div></aside>
      </div>`;

    const form = app.querySelector("#regForm"), msg = app.querySelector("#formMsg");
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      const btn = form.querySelector("button");
      btn.disabled = true; btn.textContent = "Submitting\u2026";
      const data = Object.fromEntries(new FormData(form).entries());
      try {
        const reg = await store.createRegistration({ ...data, eventId: e.id, eventTitle: e.title });
        app.innerHTML = `
          <section class="section"><div class="container">
            <div class="center" style="margin-bottom:24px">
              <div style="font-size:2.6rem;color:var(--green)">&#10003;</div>
              <h1 style="font-size:clamp(1.8rem,4vw,2.4rem)">You're registered!</h1>
              <p class="muted">Your spot is confirmed for ${escapeHtml(e.title)}.</p></div>
            <div class="ticket">
              <div class="ticket-top"><span class="chip" style="background:rgba(255,255,255,.16);border-color:rgba(255,255,255,.35);color:#fff">${reg.status.toUpperCase()}</span>
                <h2 style="margin-top:12px">${escapeHtml(e.title)}</h2>
                <p style="color:#fff;opacity:.85;margin:0">${formatDate(e.eventDate, { weekday: "long", day: "2-digit", month: "long", year: "numeric" })} &middot; ${escapeHtml(e.startTime)}</p></div>
              <div class="ticket-body">
                <p class="muted" style="font-size:.84rem;margin-bottom:4px">Ticket code</p>
                <div class="code">${reg.ticketCode}</div>
                <div class="divider"></div>
                <dl class="dl"><dt>Name</dt><dd>${escapeHtml(data.name)}</dd>
                  <dt>Email</dt><dd>${escapeHtml(data.email)}</dd>
                  <dt>Venue</dt><dd>${escapeHtml(e.venue)}</dd></dl>
                <div class="divider"></div>
                <a class="btn btn-primary" href="event.html?id=${encodeURIComponent(e.id)}">View event</a>
                <button class="btn" onclick="window.print()">Print ticket</button>
              </div></div>
          </div></section>`;
      } catch (err) {
        msg.innerHTML = notice("Could not submit: " + escapeHtml(err.message), "orange");
        btn.disabled = false; btn.textContent = "Confirm registration";
      }
    });
  } catch (e) { app.innerHTML = errorNotice(e); }
}

/* ------------------------------------------------------ contact form */
function wireContact() {
  const form = document.getElementById("contactForm");
  if (!form) return;
  form.addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const msg = document.getElementById("contactMsg");
    const btn = form.querySelector("button");
    btn.disabled = true; btn.textContent = "Sending\u2026";
    const d = Object.fromEntries(new FormData(form).entries());
    try {
      if (!store.isConfigured()) throw new Error("The backend is not configured yet (see SETUP.md).");
      await store.createMessage(d);
      msg.innerHTML = `<div class="flash success" style="position:static;margin-bottom:14px"><p>Thanks! Your message has been sent to the campus team.</p></div>`;
      form.reset();
    } catch (err) {
      msg.innerHTML = notice("Could not send: " + escapeHtml(err.message), "orange");
    }
    btn.disabled = false; btn.textContent = "Send message";
  });
}

/* ---------------------------------------------------------- countdown */
function startCountdowns() {
  document.querySelectorAll("[data-countdown]").forEach((el) => {
    const target = new Date(el.dataset.countdown + "T00:00:00").getTime();
    const out = el.querySelector(".countdown") || el;
    const render = () => {
      const diff = target - Date.now();
      if (diff <= 0) { out.innerHTML = '<div class="cd"><b>&#10003;</b><span>Live now</span></div>'; return; }
      const d = Math.floor(diff / 86400000), h = Math.floor((diff % 86400000) / 3600000);
      const m = Math.floor((diff % 3600000) / 60000), s = Math.floor((diff % 60000) / 1000);
      out.innerHTML = `<div class="cd"><b>${d}</b><span>Days</span></div><div class="cd"><b>${h}</b><span>Hrs</span></div>
        <div class="cd"><b>${m}</b><span>Min</span></div><div class="cd"><b>${s}</b><span>Sec</span></div>`;
    };
    render(); setInterval(render, 1000);
  });
}

/* --------------------------------------------------------------- boot */
const page = document.body.dataset.page;
const ACTIVE = { home: "index.html", event: "events.html", announcement: "announcements.html" };
shell(ACTIVE[page] || (page + ".html"));

const appEl = document.getElementById("app");
if (appEl) {
  if (page === "home") {
    home(appEl);                       // home manages its own full-width bands
  } else {
    const inner = document.createElement("div");
    inner.className = "container section";
    appEl.appendChild(inner);
    const render = { events: eventsPage, event: eventPage, announcements: announcementsPage,
      announcement: announcementPage, register: registerPage }[page];
    if (render) render(inner);
  }
}
if (page === "contact") wireContact();
