# RGIPT Sivasagar Campus — Event Management Website

A complete event portal for **Rajiv Gandhi Institute of Petroleum Technology,
Sivasagar Campus, Assam** — events, registrations, announcements, a faculty
directory and a full **admin panel**, hosted on **GitHub Pages** with a **Firebase**
database. No server to run, nothing to install.

## 🔗 Live links

| | |
|---|---|
| **Website** | **https://bambooatwork.github.io/rgipt-sivasagar-events/** |
| **Admin panel** | **https://bambooatwork.github.io/rgipt-sivasagar-events/admin.html** |
| **Repository** | https://github.com/bambooatwork/rgipt-sivasagar-events |

The admin panel is also reachable from the **Admin** link in the site header.
Sign in with the account created in Firebase Authentication.

## Status

| Piece | State |
|---|---|
| Site files on GitHub Pages (`docs/`) | ✅ live |
| Firebase project `rgipt-event-management` | ✅ connected |
| Firestore security rules | ✅ published and verified |
| Admin login (Firebase Authentication) | ✅ enabled |
| Starter content (7 events, 4 notices) | ⬜ **not loaded yet** — see below |

**One thing left to do:** sign in at the admin panel and click **Load starter data**
on the dashboard. That imports the campus's real events and announcements. Until
then the public site correctly shows an empty state ("No upcoming events").

---

## How it's built

GitHub Pages can only serve static files, so the site keeps its files on GitHub and
uses Firebase (Google's free backend) for the database and the admin login:

| Piece | Where it lives |
|---|---|
| The website | GitHub Pages, from the `docs/` folder |
| Events, announcements, registrations, messages | Firebase **Firestore** |
| Admin login | Firebase **Authentication** (email + password) |
| Security | Firestore rules — the public can read events and register; only a signed-in admin can read registrations or change anything |

---

## The site

| Page | File |
|---|---|
| Home | `docs/index.html` |
| Events (search + filters) | `docs/events.html` |
| Event detail + countdown | `docs/event.html?id=…` |
| Announcements | `docs/announcements.html` |
| Faculty directory (searchable) | `docs/faculty.html` |
| About / Contact | `docs/about.html`, `docs/contact.html` |
| **Admin panel** | `docs/admin.html` |

Registration writes a real record to Firestore and issues a ticket code. The contact
form writes to the messages inbox in the admin panel.

## The admin panel

- **Dashboard** — event, registration, announcement and message counts, plus a
  registrations-by-category chart.
- **Events** — create, edit, publish/hide, delete, and see registered/capacity per event.
- **Registrations** — view everyone who signed up, change status
  (confirmed / waitlist / cancelled), and delete.
- **Announcements** — create, edit, pin, publish/unpublish, delete.
- **Messages** — read/unread inbox from the contact form.
- **Settings** — change your password.
- **Load starter data** — one click to import the 7 real campus events and 4 notices.

> **Seat counts are admin-only.** The public site deliberately cannot read the
> registration list (privacy), so it shows capacity only. Real counts appear in the
> admin panel.

---

## Repository layout

```
rgipt-events/
├── README.md
├── SETUP.md              ← reference guide for connecting Firebase (already done here)
├── docs/                 ← THE WEBSITE (GitHub Pages serves this folder)
│   ├── index.html, events.html, event.html, announcements.html,
│   │   announcement.html, register.html, faculty.html, about.html,
│   │   contact.html, admin.html, 404.html
│   ├── starter-data.json  the 7 real events + 4 notices, imported from the admin
│   ├── css/style.css      the full design system
│   ├── img/logo.png       RGIPT emblem (circular)
│   └── js/
│       ├── firebase-config.js  Firebase project values
│       ├── store.js            data layer (Firestore + Auth)
│       ├── site.js             public pages
│       └── admin.js            admin panel
└── (optional) app.py, models.py, seed.py, run.py — a Flask version for local use
```

The Flask app in the root is **optional** — an offline/local copy of the same site
that talks to a SQLite file instead of Firebase. You do not need it for the hosted site.

---

## About the starter content

**Load starter data** (admin dashboard) imports **13 events and 6 announcements** —
real, publicly documented RGIPT Sivasagar Campus activity, sourced from rgipt.ac.in,
GDG on Campus and the campus's announcements:

- **Upcoming** — Urja Shakti 2026, Krida Oorja '26, Urjotsav 2026, Google Cloud
  Study Jams, SCHEMCON 2026, TechSprint 2026-27
- **Past** — Internal Hackathon for SIH 2026, Build with AI: Antigravity, Solution
  Challenge 2026, and the short-term courses on Hydrogen Energy, Petroleum Refinery,
  CFD and TechSprint 2025-26

Two honest caveats:

- **Upcoming dates follow the campus's recurring pattern, not an official
  announcement.** Confirm the exact dates in the admin panel before publishing.
- **No sample registrations are ever created.** Every registration count comes from
  real students.

**Faculty** is compiled from the institute's official listings (rgipt.ac.in).
Institutional emails are shown; personal mobile numbers published on the institute
site are deliberately not reproduced.

Campus details: Gohain Gaon, Akhoiphutia, Dhaiali Road, Sivasagar – 785697, Assam ·
03772-295231 · coordinator-aei@rgipt.ac.in · Established 2016 (historically the Assam
Energy Institute) · In-Charge: Dr Chinmoy Jit Sarma · Director: Prof. Harish Hirani

---

## Security

- Only accounts you create in Firebase Authentication can sign in to the admin panel.
- Firestore rules let the public **read** published events and **create** a
  registration, but **only a signed-in admin can read the registration list or change
  anything**.
- The Firebase web API key in `firebase-config.js` is public by design — it is not a
  secret and is safe to commit. Your data is protected by the rules, not the key.

---

## Testing

```bash
python test_admin_ui.py   # 34 checks on the admin panel UI (stateful mock, no network)
python verify_static.py   # 96 checks on the GitHub Pages build (headless Chrome)
python test_all.py        # 55 functional checks on the optional Flask app
python test_bootstrap.py  # Flask app boots from an empty database
python audit.py           # 93 browser checks on the Flask app, incl. admin CRUD
```

`test_admin_ui.py` and `verify_static.py` need `websocket-client` and a local
Chrome/Chromium. `test_admin_ui.py` runs the real `docs/js/admin.js` against a mocked
data layer, so the whole admin interface is verified without a network or a Firebase
project. The three Flask suites additionally need `Flask` and `Flask-SQLAlchemy`.

---

© RGIPT Sivasagar Campus. Built as a campus event-management portal.
