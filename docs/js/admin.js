/* =====================================================================
   Admin panel — Firebase Auth login + full management of events,
   announcements, registrations and messages. Runs entirely in the browser
   on GitHub Pages; Firestore security rules keep writes to signed-in users.
   ===================================================================== */
import * as store from "./store.js";
import { escapeHtml, formatDate, isPast } from "./store.js";

const CATEGORIES = ["Technical", "Cultural", "Sports", "Workshop", "Seminar", "Hackathon", "Entrepreneurship"];
const ACCENTS = ["teal", "amber", "indigo", "rose", "emerald", "violet"];

const app = document.getElementById("app");
let cache = { events: [], anns: [], regs: [], msgs: [] };
let user = null;

/* --------------------------------------------------------------- header */
/* ------------------------------------------------------------- icons */
const ICONS = {
  grid: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>',
  calendar: '<rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/>',
  users: '<path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/>',
  bell: '<path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/><path d="M13.73 21a2 2 0 0 1-3.46 0"/>',
  mail: '<rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 6-10 7L2 6"/>',
  sliders: '<line x1="4" y1="21" x2="4" y2="14"/><line x1="4" y1="10" x2="4" y2="3"/><line x1="12" y1="21" x2="12" y2="12"/><line x1="12" y1="8" x2="12" y2="3"/><line x1="20" y1="21" x2="20" y2="16"/><line x1="20" y1="12" x2="20" y2="3"/><line x1="1" y1="14" x2="7" y2="14"/><line x1="9" y1="8" x2="15" y2="8"/><line x1="17" y1="16" x2="23" y2="16"/>'
};

function ico(name) {
  return `<svg class="ai" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"
    stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONS[name] || ""}</svg>`;
}

/* -------------------------------------------------------------- header */
function header(email) {
  return `<header class="admin-top"><div class="container admin-top-in">
      <span class="admin-brand">
        <img class="logo" src="img/logo.png" alt="RGIPT logo">
        <span class="admin-brand-text"><b>RGIPT Sivasagar Campus</b><span>Admin console</span></span>
      </span>
      <span class="admin-top-right">
        ${email ? `<span class="admin-who">${escapeHtml(email)}</span>
        <button class="btn btn-sm btn-invert" id="topSignOut" type="button">Sign out</button>` : ""}
      </span>
    </div></header>`;
}

function wireHeader() {
  const b = document.getElementById("topSignOut");
  if (b) b.addEventListener("click", () => store.logout());
}

function loginView() {
  app.innerHTML = `${header("")}
    <div class="auth-wrap"><div class="auth-card">
      <div class="center" style="margin-bottom:18px">
        <img class="round" src="img/logo.png" alt="RGIPT logo" style="width:72px;margin:0 auto 12px">
        <h1 style="font-size:1.5rem;margin-bottom:2px">Admin sign in</h1>
        <p class="muted mb-0" style="font-size:.88rem">RGIPT Sivasagar Campus &middot; Event Portal</p>
      </div>
      <div id="loginMsg"></div>
      <form id="loginForm">
        <div class="field"><label>Email</label><input type="email" name="email" required autocomplete="username"></div>
        <div class="field"><label>Password</label><input type="password" name="password" required autocomplete="current-password"></div>
        <button class="btn btn-primary btn-block" type="submit">Sign in</button>
      </form>
    </div></div>`;
  app.querySelector("#loginForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.target, btn = f.querySelector("button");
    btn.disabled = true; btn.textContent = "Signing in\u2026";
    try { await store.login(f.email.value.trim(), f.password.value); }
    catch (err) {
      app.querySelector("#loginMsg").innerHTML =
        `<div class="flash error" style="position:static;margin-bottom:14px"><p>${escapeHtml(err.message)}</p></div>`;
      btn.disabled = false; btn.textContent = "Sign in";
    }
  });
}

/* ---------------------------------------------------------------- shell */
function shellView(view) {
  const nav = [
    ["dashboard", "Dashboard", "grid"], ["events", "Events", "calendar"],
    ["registrations", "Registrations", "users"], ["announcements", "Announcements", "bell"],
    ["messages", "Messages", "mail"], ["settings", "Settings", "sliders"]
  ];
  app.innerHTML = `${header(user.email)}
    <div class="admin-shell">
      <aside class="admin-side">
        <p class="side-title">Manage</p>
        ${nav.map(([k, t, ic]) => `<a href="#/${k}" class="${view === k ? "active" : ""}">${ico(ic)}${t}</a>`).join("")}
      </aside>
      <div class="admin-main" id="main"></div>
    </div>`;
  wireHeader();
}

/* ------------------------------------------------------------ dashboard */
async function dashboard() {
  const [events, anns, regs, msgs] = await Promise.all([
    store.listEvents({ publishedOnly: false }), store.listAnnouncements({ publishedOnly: false }),
    store.listRegistrations(), store.listMessages()
  ]);
  cache = { events, anns, regs, msgs };
  const upcoming = events.filter((e) => !isPast(e)).length;
  const byCat = {};
  regs.forEach((r) => { const e = events.find((x) => x.id === r.eventId); const c = e ? e.category : "Other"; byCat[c] = (byCat[c] || 0) + 1; });
  const maxc = Math.max(1, ...Object.values(byCat));
  const unread = msgs.filter((m) => !m.isRead).length;

  document.getElementById("main").innerHTML = `
    <section class="admin-hero">
      <div>
        <p class="kicker">RGIPT Sivasagar Campus</p>
        <h1>Welcome back</h1>
        <p>Manage the campus's events, registrations, announcements and messages from here.</p>
      </div>
      <div class="admin-hero-logo"><img src="img/logo.png" alt="RGIPT logo"></div>
    </section>
    <div class="admin-head"><div><h2 style="font-size:1.2rem;margin:0">Overview</h2>
      <p class="muted mb-0" style="font-size:.86rem">Signed in as ${escapeHtml(user.email)}</p></div>
      <div class="flex gap wrap">
        <button class="btn btn-sm" id="loadStarter">Load starter data</button>
        <a class="btn btn-sm btn-primary" href="#/event-form">New event</a></div></div>
    <div class="kpi-grid">
      <div class="kpi"><span class="ico">${ico("calendar")}</span><span class="label">Events</span><b>${events.length}</b><span class="hint">${upcoming} upcoming</span></div>
      <div class="kpi"><span class="ico">${ico("users")}</span><span class="label">Registrations</span><b>${regs.length}</b><span class="hint">all time</span></div>
      <div class="kpi"><span class="ico">${ico("bell")}</span><span class="label">Announcements</span><b>${anns.length}</b><span class="hint">${anns.filter((a) => !a.isPublished).length} drafts</span></div>
      <div class="kpi"><span class="ico">${ico("mail")}</span><span class="label">Messages</span><b>${unread}</b><span class="hint">unread</span></div>
    </div>
    ${events.length === 0 ? `<div class="panel" style="border-left:4px solid var(--green)">
      <h3 style="margin-top:0">Your database is empty</h3>
      <p class="mb-0">Click <strong>Load starter data</strong> (top right) to add the campus's
      7 real events and 4 announcements. Every one of them is editable afterwards.</p></div>` : ""}
    <div class="grid grid-2">
      <div class="panel"><div class="panel-head"><h3>Registrations by category</h3></div>
        <div class="bar-chart">${Object.keys(byCat).length ? Object.entries(byCat).map(([c, n]) =>
          `<div class="bar-row"><span class="muted">${escapeHtml(c)}</span>
            <span class="track"><i style="width:${(100 * n / maxc)}%"></i></span><strong>${n}</strong></div>`).join("")
          : '<p class="muted mb-0">No registrations yet.</p>'}</div></div>
      <div class="panel"><div class="panel-head"><h3>Recent registrations</h3><a class="btn btn-sm" href="#/registrations">All</a></div>
        <div class="table-wrap" style="border:none;background:transparent"><table style="min-width:0"><tbody>
          ${regs.slice(0, 6).map((r) => `<tr><td><span class="row-title">${escapeHtml(r.name)}</span><br>
            <span class="hint">${escapeHtml(r.eventTitle || "")}</span></td>
            <td><span class="badge ${r.status}">${r.status}</span></td>
            <td class="hint">${formatDate((r.createdAt || "").slice(0, 10), { day: "2-digit", month: "short" })}</td></tr>`).join("")
          || '<tr><td class="muted">No registrations yet.</td></tr>'}
        </tbody></table></div></div>
    </div>`;

  document.getElementById("loadStarter").addEventListener("click", async (e) => {
    e.target.disabled = true; e.target.textContent = "Loading\u2026";
    try { const n = await store.loadStarterData(); alert(`Loaded ${n} records.`); route(); }
    catch (err) { alert("Failed: " + err.message); e.target.disabled = false; e.target.textContent = "Load starter data"; }
  });
}

/* --------------------------------------------------------------- events */
function eventsView() {
  const rows = cache.events;
  const counts = {};
  cache.regs.forEach((r) => {
    if (r.status !== "cancelled") counts[r.eventId] = (counts[r.eventId] || 0) + 1;
  });
  document.getElementById("main").innerHTML = `
    <div class="admin-head"><div><h1>Events</h1><p class="muted mb-0">${rows.length} event(s).</p></div>
      <a class="btn btn-primary" href="#/event-form">New event</a></div>
    ${rows.length ? `<div class="table-wrap"><table>
      <thead><tr><th>Event</th><th>Date</th><th>Category</th><th>Registered</th><th>Status</th><th>Actions</th></tr></thead><tbody>
      ${rows.map((e) => `<tr>
        <td><span class="row-title">${escapeHtml(e.title)}</span>${e.isFeatured ? '<br><span class="badge pinned">Featured</span>' : ""}</td>
        <td>${formatDate(e.eventDate)}<br><span class="hint">${escapeHtml(e.startTime)}</span></td>
        <td><span class="chip">${escapeHtml(e.category)}</span></td>
        <td>${counts[e.id] || 0} / ${e.capacity}</td>
        <td>${e.isPublished ? '<span class="badge live">Published</span>' : '<span class="badge draft">Hidden</span>'}
            ${isPast(e) ? '<br><span class="badge past">Past</span>' : ""}</td>
        <td><div class="actions">
          <a class="btn btn-sm" href="#/event-form?id=${encodeURIComponent(e.id)}">Edit</a>
          <button class="btn btn-sm" data-toggle="${encodeURIComponent(e.id)}">${e.isPublished ? "Hide" : "Publish"}</button>
          <button class="btn btn-sm btn-danger" data-del="${encodeURIComponent(e.id)}">Delete</button>
        </div></td></tr>`).join("")}
      </tbody></table></div>` : '<div class="empty"><p>No events yet.</p></div>'}`;

  document.querySelectorAll("[data-toggle]").forEach((b) => b.addEventListener("click", async () => {
    const e = cache.events.find((x) => x.id === b.dataset.toggle);
    await store.saveEvent(e.id, { isPublished: !e.isPublished }); route();
  }));
  document.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", async () => {
    const e = cache.events.find((x) => x.id === b.dataset.del);
    if (!confirm(`Delete "${e.title}"? This cannot be undone.`)) return;
    await store.deleteEvent(e.id); route();
  }));
}

async function eventFormView(id) {
  const e = id ? await store.getEvent(id) : null;
  const v = (k, d) => escapeHtml(e ? (e[k] == null ? d || "" : e[k]) : d || "");
  document.getElementById("main").innerHTML = `
    <div class="admin-head"><div><h1>${e ? "Edit event" : "Create event"}</h1></div>
      <a class="btn btn-sm" href="#/events">Back to events</a></div>
    <form class="panel" id="eventForm">
      <div class="form-grid">
        <div class="field full"><label>Event title *</label><input name="title" required value="${v("title")}"></div>
        <div class="field"><label>Category</label><select name="category">${CATEGORIES.map((c) => `<option ${e && e.category === c ? "selected" : ""}>${c}</option>`).join("")}</select></div>
        <div class="field"><label>Accent colour</label><select name="accent">${ACCENTS.map((a) => `<option ${e && e.accent === a ? "selected" : ""}>${a}</option>`).join("")}</select></div>
        <div class="field full"><label>Short description</label><input name="shortDescription" value="${v("shortDescription")}"></div>
        <div class="field full"><label>Full description</label><textarea name="description">${v("description")}</textarea></div>
        <div class="field"><label>Organiser</label><input name="organizer" value="${v("organizer", "RGIPT Sivasagar Campus")}"></div>
        <div class="field"><label>Venue</label><input name="venue" value="${v("venue", "RGIPT Sivasagar Campus, Gohain Gaon")}"></div>
        <div class="field"><label>Start date *</label><input type="date" name="eventDate" required value="${v("eventDate")}"></div>
        <div class="field"><label>End date</label><input type="date" name="endDate" value="${v("endDate")}"></div>
        <div class="field"><label>Start time</label><input name="startTime" value="${v("startTime", "10:00 AM")}"></div>
        <div class="field"><label>End time</label><input name="endTime" value="${v("endTime", "05:00 PM")}"></div>
        <div class="field"><label>Registration deadline</label><input type="date" name="registrationDeadline" value="${v("registrationDeadline")}"></div>
        <div class="field"><label>Capacity</label><input type="number" name="capacity" min="0" value="${v("capacity", "100")}"></div>
        <div class="field"><label>Fee (&#8377;)</label><input type="number" name="fee" min="0" value="${v("fee", "0")}"></div>
        <div class="field"><label>Team size</label><input name="teamSize" value="${v("teamSize", "Individual")}"></div>
        <div class="field"><label>Contact email</label><input type="email" name="contactEmail" value="${v("contactEmail")}"></div>
      </div>
      <div class="divider"></div>
      <div class="flex gap wrap" style="gap:26px">
        <label class="check"><input type="checkbox" name="isFeatured" ${e && e.isFeatured ? "checked" : ""}> Feature on the home page</label>
        <label class="check"><input type="checkbox" name="isPublished" ${!e || e.isPublished ? "checked" : ""}> Published</label>
      </div>
      <div class="flex gap items-center wrap mt-3">
        <button class="btn btn-primary" type="submit">${e ? "Save changes" : "Create event"}</button>
        <a class="btn btn-ghost" href="#/events">Cancel</a></div>
    </form>`;

  document.getElementById("eventForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const f = ev.target, d = Object.fromEntries(new FormData(f).entries());
    d.capacity = Number(d.capacity || 0); d.fee = Number(d.fee || 0);
    d.isFeatured = f.isFeatured.checked; d.isPublished = f.isPublished.checked;
    try { await store.saveEvent(id, d); cache.events = []; location.hash = "#/events"; route(); }
    catch (err) { alert("Could not save: " + err.message); }
  });
}

/* -------------------------------------------------------- announcements */
function announcementsView() {
  const rows = cache.anns;
  document.getElementById("main").innerHTML = `
    <div class="admin-head"><div><h1>Announcements</h1></div><a class="btn btn-primary" href="#/announcement-form">New announcement</a></div>
    ${rows.length ? `<div class="table-wrap"><table>
      <thead><tr><th>Title</th><th>Category</th><th>Published</th><th>Status</th><th>Actions</th></tr></thead><tbody>
      ${rows.map((a) => `<tr>
        <td><span class="row-title">${escapeHtml(a.title)}</span>${a.isPinned ? '<br><span class="badge pinned">Pinned</span>' : ""}</td>
        <td><span class="chip">${escapeHtml(a.category)}</span></td>
        <td>${formatDate((a.publishedAt || "").slice(0, 10))}</td>
        <td>${a.isPublished ? '<span class="badge live">Published</span>' : '<span class="badge draft">Draft</span>'}</td>
        <td><div class="actions">
          <a class="btn btn-sm" href="#/announcement-form?id=${encodeURIComponent(a.id)}">Edit</a>
          <button class="btn btn-sm" data-toggle="${encodeURIComponent(a.id)}">${a.isPublished ? "Unpublish" : "Publish"}</button>
          <button class="btn btn-sm btn-danger" data-del="${encodeURIComponent(a.id)}">Delete</button>
        </div></td></tr>`).join("")}
      </tbody></table></div>` : '<div class="empty"><p>No announcements yet.</p></div>'}`;

  document.querySelectorAll("[data-toggle]").forEach((b) => b.addEventListener("click", async () => {
    const a = cache.anns.find((x) => x.id === b.dataset.toggle);
    await store.saveAnnouncement(a.id, { isPublished: !a.isPublished }); cache.anns = []; route();
  }));
  document.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm("Delete this announcement?")) return;
    await store.deleteAnnouncement(b.dataset.del); cache.anns = []; route();
  }));
}

async function announcementFormView(id) {
  const a = id ? await store.getAnnouncement(id) : null;
  const v = (k, d) => escapeHtml(a ? (a[k] == null ? d || "" : a[k]) : d || "");
  document.getElementById("main").innerHTML = `
    <div class="admin-head"><div><h1>${a ? "Edit announcement" : "New announcement"}</h1></div>
      <a class="btn btn-sm" href="#/announcements">Back</a></div>
    <form class="panel" id="annForm">
      <div class="form-grid">
        <div class="field full"><label>Title *</label><input name="title" required value="${v("title")}"></div>
        <div class="field"><label>Category</label><select name="category">
          ${["General", "Events", "Academic", "Hackathon", "Sports", "Examination", "Notice"].map((c) => `<option ${a && a.category === c ? "selected" : ""}>${c}</option>`).join("")}
        </select></div>
        <div class="field full"><label>Body *</label><textarea name="body" required style="min-height:180px">${v("body")}</textarea></div>
      </div>
      <div class="flex gap wrap" style="gap:22px">
        <label class="check"><input type="checkbox" name="isPinned" ${a && a.isPinned ? "checked" : ""}> Pin to top</label>
        <label class="check"><input type="checkbox" name="isPublished" ${!a || a.isPublished ? "checked" : ""}> Published</label>
      </div>
      <div class="flex gap items-center wrap mt-3">
        <button class="btn btn-primary" type="submit">${a ? "Save changes" : "Create announcement"}</button>
        <a class="btn btn-ghost" href="#/announcements">Cancel</a></div>
    </form>`;

  document.getElementById("annForm").addEventListener("submit", async (ev) => {
    ev.preventDefault();
    const f = ev.target, d = Object.fromEntries(new FormData(f).entries());
    d.isPinned = f.isPinned.checked; d.isPublished = f.isPublished.checked;
    try { await store.saveAnnouncement(id, d); cache.anns = []; location.hash = "#/announcements"; route(); }
    catch (err) { alert("Could not save: " + err.message); }
  });
}

/* --------------------------------------------------------- registrations */
function registrationsView() {
  const rows = cache.regs;
  document.getElementById("main").innerHTML = `
    <div class="admin-head"><div><h1>Registrations</h1><p class="muted mb-0">${rows.length} record(s).</p></div></div>
    ${rows.length ? `<div class="table-wrap"><table>
      <thead><tr><th>Ticket</th><th>Participant</th><th>Event</th><th>Status</th><th>Actions</th></tr></thead><tbody>
      ${rows.map((r) => `<tr>
        <td class="mono">${escapeHtml(r.ticketCode || "")}</td>
        <td><span class="row-title">${escapeHtml(r.name)}</span><br><span class="hint">${escapeHtml(r.email)}${r.phone ? " &middot; " + escapeHtml(r.phone) : ""}</span></td>
        <td>${escapeHtml(r.eventTitle || "")}</td>
        <td><span class="badge ${r.status}">${r.status}</span></td>
        <td><div class="actions">
          <select data-status="${encodeURIComponent(r.id)}" style="padding:6px 8px;font-size:.82rem">
            ${["confirmed", "waitlist", "cancelled"].map((s) => `<option ${r.status === s ? "selected" : ""}>${s}</option>`).join("")}
          </select>
          <button class="btn btn-sm btn-danger" data-del="${encodeURIComponent(r.id)}">Delete</button>
        </div></td></tr>`).join("")}
      </tbody></table></div>` : '<div class="empty"><p>No registrations yet.</p></div>'}`;

  document.querySelectorAll("[data-status]").forEach((s) => s.addEventListener("change", async () => {
    await store.updateRegistration(s.dataset.status, { status: s.value }); cache.regs = []; route();
  }));
  document.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm("Delete this registration?")) return;
    await store.deleteRegistration(b.dataset.del); cache.regs = []; route();
  }));
}

/* -------------------------------------------------------------- messages */
function messagesView() {
  const rows = cache.msgs;
  document.getElementById("main").innerHTML = `
    <div class="admin-head"><div><h1>Messages</h1><p class="muted mb-0">${rows.length} enquir(ies).</p></div></div>
    ${rows.length ? `<div class="grid" style="gap:14px">${rows.map((m) => `
      <div class="panel" style="margin-bottom:0;${m.isRead ? "" : "border-left:4px solid var(--green)"}">
        <div class="panel-head" style="margin-bottom:10px"><div>
          <strong>${escapeHtml(m.subject || "General enquiry")}</strong>
          ${m.isRead ? "" : '<span class="badge draft">New</span>'}
          <div class="hint">${escapeHtml(m.name)} &middot; <a href="mailto:${escapeHtml(m.email)}">${escapeHtml(m.email)}</a> &middot; ${formatDate((m.createdAt || "").slice(0, 10))}</div></div>
          <div class="actions">
            <button class="btn btn-sm" data-read="${encodeURIComponent(m.id)}">${m.isRead ? "Mark unread" : "Mark read"}</button>
            <a class="btn btn-sm" href="mailto:${escapeHtml(m.email)}">Reply</a>
            <button class="btn btn-sm btn-danger" data-del="${encodeURIComponent(m.id)}">Delete</button>
          </div></div>
        <p class="mb-0" style="white-space:pre-line">${escapeHtml(m.message)}</p>
      </div>`).join("")}</div>` : '<div class="empty"><p>No messages yet.</p></div>'}`;

  document.querySelectorAll("[data-read]").forEach((b) => b.addEventListener("click", async () => {
    const m = cache.msgs.find((x) => x.id === b.dataset.read);
    await store.updateMessage(m.id, { isRead: !m.isRead }); cache.msgs = []; route();
  }));
  document.querySelectorAll("[data-del]").forEach((b) => b.addEventListener("click", async () => {
    if (!confirm("Delete this message?")) return;
    await store.deleteMessage(b.dataset.del); cache.msgs = []; route();
  }));
}

/* -------------------------------------------------------------- settings */
function settingsView() {
  document.getElementById("main").innerHTML = `
    <div class="admin-head"><div><h1>Settings</h1><p class="muted mb-0">Signed in as ${escapeHtml(user.email)}.</p></div></div>
    <div class="grid grid-2">
      <form class="panel" id="pwForm"><h3>Change password</h3>
        <div class="field"><label>New password</label><input type="password" name="pw" minlength="6" required></div>
        <div class="field"><label>Confirm new password</label><input type="password" name="pw2" minlength="6" required></div>
        <button class="btn btn-primary" type="submit">Update password</button></form>
      <div class="panel"><h3>How this works</h3>
        <p class="muted" style="font-size:.9rem">The site is static on GitHub Pages; all data lives in your Firebase project
        (Firestore) and the admin login is Firebase Authentication. Only signed-in accounts can write &mdash;
        see the security rules in <strong>SETUP.md</strong>.</p>
        <div class="divider"></div>
        <p class="muted mb-0" style="font-size:.86rem">Questions about the setup? See
        <strong>SETUP.md</strong> in the repository.</p></div>
    </div>`;
  document.getElementById("pwForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const f = e.target;
    if (f.pw.value !== f.pw2.value) { alert("Passwords do not match."); return; }
    try { await store.changePassword(f.pw.value); alert("Password updated."); f.reset(); }
    catch (err) { alert("Could not update: " + err.message); }
  });
}

/* -------------------------------------------------------------- errors */
/* Nothing should ever leave the admin panel blank: any failure is rendered
   as a visible message instead of an empty page. */
function fatal(err) {
  const msg = (err && err.message) ? err.message : String(err);
  const panel = `<div class="panel" style="border-left:4px solid var(--orange)">
      <h3 style="margin-top:0">Something went wrong</h3>
      <p class="mb-0">${escapeHtml(msg)}</p>
      <p class="hint mt-2 mb-0">If this keeps happening, check your Firebase config
      and the Firestore rules (see SETUP.md).</p></div>`;
  const main = document.getElementById("main");
  if (main) main.innerHTML = panel;
  else { app.innerHTML = `${header(user ? user.email : "")}<div class="container section">${panel}</div>`; wireHeader(); }
}

/* ---------------------------------------------------------------- router */
async function route() {
  try {
    if (!user) { loginView(); return; }
    const hash = location.hash.replace(/^#\/?/, "") || "dashboard";
    const [view, qs] = hash.split("?");
    const id = new URLSearchParams(qs || "").get("id");
    const section = view.replace("-form", "s");
    shellView(section);

    if (view === "dashboard") await dashboard();
    else if (view === "events") {
      cache.events = await store.listEvents({ publishedOnly: false });
      cache.regs = await store.listRegistrations();
      eventsView();
    }
    else if (view === "event-form") await eventFormView(id);
    else if (view === "announcements") { cache.anns = await store.listAnnouncements({ publishedOnly: false }); announcementsView(); }
    else if (view === "announcement-form") await announcementFormView(id);
    else if (view === "registrations") { cache.regs = await store.listRegistrations(); registrationsView(); }
    else if (view === "messages") { cache.msgs = await store.listMessages(); messagesView(); }
    else if (view === "settings") settingsView();
    else await dashboard();
  } catch (err) {
    fatal(err);
  }
}

window.addEventListener("hashchange", route);
window.addEventListener("click", (e) => {
  const a = (e.target && e.target.closest) ? e.target.closest('a[href^="#/"]') : null;
  if (a) { e.preventDefault(); location.hash = a.getAttribute("href"); route(); }
});
window.addEventListener("unhandledrejection", (e) => fatal(e.reason));

if (!store.isConfigured()) {
  app.innerHTML = `${header("")}<div class="container section">
    <div class="panel" style="border-left:4px solid var(--orange)">
      <h3 style="margin-top:0">Backend not configured</h3>
      <p class="mb-0">Open <code>docs/js/firebase-config.js</code>, paste your Firebase
      project values, and reload.</p></div></div>`;
} else {
  // watchAuth may or may not return a promise — never assume it does.
  Promise.resolve(store.watchAuth((u) => {
    user = u;
    if (!location.hash) location.hash = "#/dashboard";
    route();
  })).catch(fatal);
}
