"""Build a static copy of the public site into ./docs for GitHub Pages.

GitHub Pages serves static files only — it cannot run Flask — so this renders
every public page to HTML with relative links, copies the assets, and swaps the
few server-dependent bits (registration, contact form, admin links) for
equivalent no-server behaviour.

    python build_static.py

Then commit ./docs and enable Pages (Settings → Pages → Branch: main /docs).
"""
import os
import re
import shutil
from urllib.parse import quote

from app import app, CAMPUS
from models import Event, Announcement

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")


def build():
    client = app.test_client()

    with app.app_context():
        events = Event.query.filter_by(is_published=True).all()
        slugs = [e.slug for e in events]
        titles = {e.slug: e.title for e in events}
        contacts = {e.slug: (e.contact_email or CAMPUS["email"]) for e in events}
        ann_ids = [a.id for a in Announcement.query.filter_by(is_published=True).all()]

    # url -> output filename (flat structure keeps every link one level deep)
    pages = {
        "/": "index.html",
        "/events?status=all": "events.html",
        "/announcements": "announcements.html",
        "/faculty": "faculty.html",
        "/about": "about.html",
        "/contact": "contact.html",
        "/my-registrations": "my-registrations.html",
        "/no-such-page": "404.html",
    }
    for slug in slugs:
        pages[f"/events/{slug}"] = f"event-{slug}.html"
    for aid in ann_ids:
        pages[f"/announcements/{aid}"] = f"announcement-{aid}.html"

    if os.path.isdir(DOCS):
        shutil.rmtree(DOCS)
    os.makedirs(DOCS)

    mailto_note = (
        '<div class="panel"><h3>This form needs the live app</h3>'
        '<p class="muted">GitHub Pages hosts static files only, so online forms are '
        'switched off in this build. To register, apply or send an enquiry, email the '
        f'campus team directly:</p><a class="btn btn-primary" href="mailto:{CAMPUS["email"]}">'
        f'Email {CAMPUS["email"]}</a></div>'
    )

    def rewrite(html, path):
        # 1. assets
        html = html.replace('href="/static/', 'href="static/').replace('src="/static/', 'src="static/')

        # 2. drop the admin button from the header (no backend on Pages)
        html = re.sub(r'<a class="btn btn-sm" href="/admin/login">.*?</a>', '', html, flags=re.S)
        # drop the footer "Admin Login" link
        html = re.sub(r'<a href="/admin/login">Admin Login</a>\s*', '', html)
        # any remaining admin link -> contact
        html = html.replace('href="/admin/login"', 'href="contact.html"')

        # 3. registration -> a prefilled email request
        def reg_link(m):
            slug = m.group(1)
            title = titles.get(slug, "the event")
            email = contacts.get(slug, CAMPUS["email"])
            subject = quote(f"Registration request: {title}")
            body = quote(f"Event: {title}\n\nName:\nDepartment:\nYear:\nPhone:\n\n")
            return f'href="mailto:{email}?subject={subject}&body={body}"'
        html = re.sub(r'href="/events/([^"/]+)/register"', reg_link, html)

        # 4. internal page links -> flat .html files
        html = re.sub(r'href="/events/([^"/]+)"', lambda m: f'href="event-{m.group(1)}.html"', html)
        html = re.sub(r'href="/events\?([^"]*)"', lambda m: f'href="events.html?{m.group(1)}"', html)
        html = html.replace('action="/events"', 'action="events.html"')
        html = html.replace('href="/events"', 'href="events.html"')
        html = re.sub(r'href="/announcements/(\d+)"', lambda m: f'href="announcement-{m.group(1)}.html"', html)
        html = html.replace('href="/announcements"', 'href="announcements.html"')
        html = html.replace('href="/faculty"', 'href="faculty.html"')
        html = html.replace('href="/about"', 'href="about.html"')
        html = html.replace('href="/contact"', 'href="contact.html"')
        html = html.replace('href="/my-registrations"', 'href="my-registrations.html"')
        html = html.replace('href="/"', 'href="index.html"')

        # 5. forms need a server -> replace with an email note on form pages
        if path in ("/contact", "/my-registrations"):
            html = re.sub(r'<form\b.*?</form>', mailto_note, html, flags=re.S)

        # 6. add the static-only script
        html = html.replace("</body>", '  <script src="static/js/static-site.js"></script>\n</body>')
        return html

    for path, filename in pages.items():
        resp = client.get(path)
        out = rewrite(resp.get_data(as_text=True), path)
        with open(os.path.join(DOCS, filename), "w", encoding="utf-8") as fh:
            fh.write(out)

    # assets
    shutil.copytree(
        os.path.join(os.path.dirname(DOCS), "static"),
        os.path.join(DOCS, "static"),
    )
    # tell GitHub Pages not to run Jekyll
    open(os.path.join(DOCS, ".nojekyll"), "w").close()

    print(f"Built {len(pages)} pages into {DOCS}/")
    for _, fn in sorted(pages.items(), key=lambda kv: kv[1]):
        print("  ", fn)


if __name__ == "__main__":
    build()
