# RGIPT Sivasagar Campus — College Event Management Website

A complete, working event-management portal for **Rajiv Gandhi Institute of Petroleum
Technology (RGIPT), Sivasagar Campus, Assam** — a public-facing site for events,
registrations and announcements, backed by a secure admin panel and a real SQLite
database.

Built with **Python + Flask + SQLAlchemy**. No build step, no cloud account — one
command and it runs.

---

## Quick start

```bash
# 1. (optional but recommended) create a virtual environment
python3 -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. install dependencies
pip install -r requirements.txt

# 3. seed the database (creates tables + loads events & announcements)
python seed.py

# 4. run it
python run.py
```

Then open **http://127.0.0.1:5000**

### Admin panel

| | |
|---|---|
| URL | http://127.0.0.1:5000/admin/login |
| Username | `admin` |
| Password | `rgipt@2026` |

> Change the password immediately from **Admin → Settings** after your first login.

### Running on macOS

The steps above work unchanged on a MacBook (Intel or Apple Silicon) — Flask and
SQLite are all you need, and Python 3 comes with the Xcode command-line tools.

One macOS gotcha: **port 5000 is used by AirPlay Receiver** on macOS Monterey and
later, so the server may start but not respond in the browser, or macOS may prompt
you about incoming connections. Either turn off *System Settings → General → AirDrop
& Handoff → AirPlay Receiver*, or simply run on another port:

```bash
PORT=5001 python run.py        # then open http://127.0.0.1:5001
```

If `python3` or `pip` aren't found, install the command-line tools with
`xcode-select --install`. When macOS asks whether to allow incoming network
connections, click **Allow**.

### Troubleshooting a blank page

If the URL opens to a blank or white page, work through these in order:

1. **Check the terminal.** The launcher now prints the exact URL it is serving. If
   port 5000 was busy it will say so and pick another port (e.g. 5001) — open the
   URL it prints, not the one in older notes.
2. **Use the exact URL printed**, e.g. `http://127.0.0.1:5001` — not `https://`, and
   not `localhost` if that resolves oddly.
3. **Hard-refresh** the browser (`Cmd+Shift+R`) to clear a cached blank response.
4. **Make sure you're running `run.py` or `app.py`** — opening the `.html` files in
   `templates/` directly in a browser will not work; they are Jinja templates that
   must be served by Flask.
5. The page no longer depends on JavaScript to show its content, so a blocked or
   failed `main.js` will not blank the page.

---

## What's inside

### Public site (students & visitors)
- **Design** — a light, white-canvas institutional theme (navy ink with green and
  saffron accents taken from the RGIPT emblem), set in Fraunces + IBM Plex Sans.
  A dark theme is available from the toggle in the header, but light is the default.
- **Home** — hero, live stats, featured/upcoming/past events, latest notices.
- **Events** — search + filter by category, timing (upcoming/past) and department.
- **Event detail** — full description, key-dates timeline, live countdown, seat
  availability, related events.
- **Registration** — validated sign-up form with duplicate protection, automatic
  waitlist when an event is full, and an instant ticket with a unique code.
- **My Registrations** — look up all your tickets by email.
- **Announcements** — notice board with pinned items and detail pages.
- **Faculty** — the real Sivasagar Campus faculty and leadership, with a
  client-side search over names and research areas.
- **About & Contact** — campus information and a working enquiry form.
- **Dark / light theme**, fully responsive down to mobile, reduced-motion aware.

### Admin panel (secure)
- **Login** — hashed passwords (Werkzeug PBKDF2), session auth, CSRF on every form.
- **Dashboard** — KPI cards, registrations-by-category chart, top events, recent
  activity.
- **Events** — create, edit, publish/hide, feature, delete (cascades registrations).
- **Registrations** — filter by event/status, search, change status
  (confirmed/waitlist/cancelled), delete, and **export to CSV**.
- **Announcements** — create, edit, pin, publish/unpublish (draft control), delete.
- **Messages** — read/unread inbox from the contact form, reply and delete.
- **Settings** — change your password.

---

## Project structure

```
rgipt-events/
├── app.py              # application factory + every route
├── models.py           # SQLAlchemy models (Admin, Event, Registration,
│                       #   Announcement, ContactMessage)
├── config.py           # configuration (secret key, database, cookie hardening)
├── seed.py             # creates the schema and loads events + announcements
├── run.py              # convenience launcher
├── build_static.py     # exports the public site to ./docs for GitHub Pages
├── requirements.txt
├── templates/          # Jinja2 templates
│   ├── base.html, _macros.html, index.html, events.html, event_detail.html,
│   ├── register_event.html, registration_success.html, announcements.html,
│   ├── announcement_detail.html, my_registrations.html, faculty.html,
│   ├── about.html, contact.html, 400/404/500.html
│   └── admin/          # login, dashboard, events, event_form, registrations,
│                       #   announcements, announcement_form, messages, settings
├── static/
│   ├── css/style.css   # the full design system
│   ├── js/main.js      # theme, nav, reveal, countdown, filters, toasts
│   ├── js/static-site.js  # client-side filtering for the static build
│   └── img/logo.png    # RGIPT emblem (circular)
├── docs/               # generated static site — commit this for GitHub Pages
└── .github/workflows/pages.yml   # optional auto-deploy workflow
```

---

## Data model

| Table | Purpose |
|---|---|
| `admins` | Admin accounts (username, hashed password, role). |
| `events` | Title, slug, category, description, dates, venue, capacity, fee, publish/feature flags. |
| `registrations` | Participant details per event, status, unique ticket code. |
| `announcements` | Notice-board posts with pin + publish (draft) flags. |
| `contact_messages` | Enquiries submitted through the contact form. |

Seat counts, "full" state and registration-open state are all computed live from the
registrations table.

---

## Hosting on GitHub Pages

GitHub Pages serves **static files only** — it cannot run Python, so it can't host
the Flask app, its database, the registration system or the admin panel. To satisfy
both needs this repo carries two things:

- the **full Flask app** (events + registration + secure admin), for running locally
  or on a Python host; and
- a **static build in `docs/`** — the whole public site, ready for GitHub Pages.

### What works on the static site
Browsing events, event details, announcements, the faculty directory, about and
contact all work, including event filtering/search (done in the browser). Because
there is no server:
- **Register** opens a pre-filled email to the event's contact address.
- **Contact** shows the campus email instead of a form.
- The **admin panel** and **My Registrations** lookup are not part of the static
  build (they need the database).

### Option A — publish from the `docs` folder (simplest)
1. Push this folder to GitHub (see below).
2. On GitHub: **Settings → Pages → Build and deployment → Source: Deploy from a
   branch**, then choose **Branch: `main`** and **Folder: `/docs`**. Save.
3. Your site appears at `https://<username>.github.io/<repo>/` within a minute.

### Option B — automatic build with GitHub Actions
`.github/workflows/pages.yml` is included. Set **Settings → Pages → Source:
GitHub Actions**, and every push to `main` will rebuild `docs/` and deploy it.

### The admin panel needs a Python host (important)
The **admin panel, registration database and contact form cannot run on GitHub
Pages** — Pages only serves static files, so those pages are intentionally absent
from the `docs/` build. This is not a bug.

To get the **full app online with a working admin panel**, deploy it to a host that
runs Python. A Render blueprint is included (`render.yaml`):

1. Push this repo to GitHub (done).
2. Go to **render.com → New → Blueprint**, pick this repository, and apply.
3. When prompted, set **`ADMIN_PASSWORD`** to a strong password (it is used for the
   `admin` account).
4. Render builds it, runs `python seed.py`, and gives you a live URL — the admin
   panel is at `/admin/login` on that URL.

Any equivalent host works too (Railway, Fly.io, PythonAnywhere). For a generic host:
- start command: `gunicorn --bind 0.0.0.0:$PORT app:app` (see `Procfile`)
- set `SECRET_KEY` and `ADMIN_PASSWORD` environment variables

> Note: on free tiers the disk is ephemeral, so the SQLite file resets on each
deploy. For data that persists, point `DATABASE_URL` at a managed PostgreSQL
instance.

### Pushing to GitHub
```bash
cd rgipt-events
git init
git add .
git commit -m "RGIPT Sivasagar Campus event portal"
git branch -M main
git remote add origin https://github.com/<username>/<repo>.git
git push -u origin main
```

### Rebuilding the static site after edits
Any time you change events, announcements or pages in the app, regenerate `docs/`:
```bash
python seed.py            # or edit data via the admin panel
python build_static.py
git add docs && git commit -m "Rebuild static site" && git push
```

> Tip: to publish on a **custom domain**, add a file `docs/CNAME` containing your
domain and set it in Settings → Pages.

---

## Security notes

- Passwords are stored as salted hashes — never plain text.
- Every state-changing form carries a CSRF token validated server-side.
- Session cookies are `HttpOnly` and `SameSite=Lax`.
- All admin routes are behind a `login_required` guard.
- User input is validated (email format, required fields, numeric ranges) and SQL
  access goes through SQLAlchemy's parameterised queries.
- **Before deploying publicly:** set a strong `SECRET_KEY` environment variable and
  run behind a production WSGI server (e.g. `gunicorn -w 4 'app:app'`) with HTTPS.

---

## Configuration

| Environment variable | Default | Notes |
|---|---|---|
| `SECRET_KEY` | random per process | Set this in production so sessions survive restarts. |
| `DATABASE_URL` | `sqlite:///rgipt_events.db` | Point at Postgres/MySQL if you prefer. |
| `ADMIN_PASSWORD` | `rgipt@2026` | Initial password for the `admin` account. **Set this before deploying publicly.** |

---

## A note on the data

**Events.** The seed data uses real RGIPT Sivasagar Campus events and programmes —
Urjotsav (the annual technical & entrepreneurial festival), Krida Oorja (the annual
sports fest), TechWave, the GDG on Campus TechSprint hackathon, Cloud Study Jams, the
SIH Internal Hackathon and SCHEMCON. The **specific dates and descriptions are
representative examples** for a working demo, not official confirmed schedules.
Replace them with your real calendar through the admin panel (or by editing
`seed.py`) before going live.

**Faculty.** The Faculty page is compiled from the institute's official faculty
listings (rgipt.ac.in) — names, designations and research areas are as published
there. Institutional email addresses are shown; **personal mobile numbers that appear
on the institute site are deliberately not reproduced here**, since republishing them
on a new public site raises a privacy concern. Add them yourself if your campus is
happy to. The listing also changes over time — re-check against the official page
before publishing.

Campus details used:
- **Address:** Gohain Gaon, Akhoiphutia, Dhaiali Road, Sivasagar – 785697, Assam
- **Phone:** 03772-295231 · **Email:** coordinator-aei@rgipt.ac.in
- **Established:** 2016 (as a centre of RGIPT; historically the Assam Energy
  Institute, AEI) · **In-Charge:** Dr Chinmoy Jit Sarma · **Director, RGIPT:** Prof.
  Harish Hirani

---

## Testing

Three verification suites ship with the project:

```bash
python test_all.py       # 58 functional checks — every route, form and feature
python test_bootstrap.py # boots from an empty DB and signs into the admin panel
python audit.py          # 71 browser checks — console errors, overflow, interactions
python verify_static.py  # 46 checks on the GitHub Pages build — links, assets, filters
```

`audit.py` and `verify_static.py` need `websocket-client` and a local Chrome/Chromium.

---

## Customising

- **Colours / branding** — edit the CSS variables at the top of
  `static/css/style.css` (`--navy`, `--green`, `--orange`, `--font-display`, …).
- **Departments / categories** — edit the lists in `app.py`.
- **Faculty** — edit the `FACULTY` list in `app.py`.
- **Campus info** — edit the `CAMPUS` dict in `app.py`.
- **Logo** — replace `static/img/logo.png` with a square image (it is displayed in a
  circle, so use a 1:1 image to avoid distortion), then rerun `python build_static.py`.
- **After any change**, regenerate the static site: `python build_static.py`.

---

© RGIPT Sivasagar Campus. Built as a campus event-management portal.
