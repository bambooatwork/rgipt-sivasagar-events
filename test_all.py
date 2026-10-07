"""End-to-end smoke test for the RGIPT Sivasagar event portal.

Exercises every public and admin route (GET + POST) using Flask's test client,
so the whole application is verified without needing a live server.
"""
import sys
import traceback

from app import app
from models import db, Event, Registration, Announcement, ContactMessage, Admin

FAILS = []
PASSES = []


def check(label, cond, extra=""):
    if cond:
        PASSES.append(label)
    else:
        FAILS.append(f"{label} {extra}")
        print(f"  FAIL: {label} {extra}")


def set_csrf(client, token="testtoken"):
    with client.session_transaction() as s:
        s["_csrf"] = token


def run():
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False)
    with app.app_context():
        # ensure seeded
        if Event.query.count() == 0:
            print("No data — run seed.py first.")
            return
        slug = Event.query.filter(Event.event_date >= __import__("datetime").date.today()).first().slug
        eid = Event.query.first().id
        aid = Announcement.query.first().id
        rid = Registration.query.first().id

    c = app.test_client()

    # ------------------------------ Public GETs ------------------------ #
    for path, label in [
        ("/", "home"),
        ("/events", "events list"),
        ("/events?status=past", "events past filter"),
        ("/events?status=all&category=Technical", "events category filter"),
        ("/events?q=urjotsav", "events search"),
        (f"/events/{slug}", "event detail"),
        ("/announcements", "announcements list"),
        (f"/announcements/{aid}", "announcement detail"),
        ("/my-registrations", "my registrations"),
        ("/faculty", "faculty"),
        ("/about", "about"),
        ("/contact", "contact"),
        ("/admin/login", "admin login page"),
        ("/static/css/style.css", "stylesheet"),
        ("/static/js/main.js", "javascript"),
        ("/static/img/logo.png", "logo image"),
    ]:
        r = c.get(path)
        check(f"GET {label} [{path}]", r.status_code == 200, f"-> {r.status_code}")

    # 404
    check("GET unknown -> 404", c.get("/definitely-not-a-page").status_code == 404)

    # --------------------------- Registration flow --------------------- #
    set_csrf(c)
    r = c.post(f"/events/{slug}/register", data={
        "_csrf": "testtoken", "name": "Test Student", "email": "test.student@example.com",
        "phone": "9800000000", "college": "RGIPT Sivasagar Campus",
        "department": "Petroleum Engineering", "year": "2nd Year", "team_name": "Testers",
        "notes": "smoke test",
    }, follow_redirects=False)
    check("POST event register -> redirect", r.status_code in (302, 303), f"-> {r.status_code}")
    loc = r.headers.get("Location", "")
    check("register redirects to ticket", "/registration/" in loc, loc)

    # duplicate blocked
    set_csrf(c)
    r = c.post(f"/events/{slug}/register", data={
        "_csrf": "testtoken", "name": "Test Student", "email": "test.student@example.com",
    })
    check("duplicate registration blocked", r.status_code == 200 and b"already registered" in r.data)

    # invalid email
    set_csrf(c)
    r = c.post(f"/events/{slug}/register", data={
        "_csrf": "testtoken", "name": "Bad", "email": "not-an-email",
    })
    check("invalid email rejected", b"valid email" in r.data)

    # ticket page
    with app.app_context():
        reg = Registration.query.filter_by(email="test.student@example.com").first()
        code = reg.ticket_code
    check("ticket page loads", c.get(f"/registration/{code}").status_code == 200)

    # my registrations lookup
    set_csrf(c)
    r = c.post("/my-registrations", data={"_csrf": "testtoken", "email": "test.student@example.com"})
    check("my registrations finds record", code.encode() in r.data)

    # ------------------------------- Contact --------------------------- #
    set_csrf(c)
    r = c.post("/contact", data={
        "_csrf": "testtoken", "name": "Enquirer", "email": "enq@example.com",
        "subject": "Hello", "message": "Test message body",
    }, follow_redirects=True)
    check("contact submit", r.status_code == 200)
    with app.app_context():
        check("contact stored", ContactMessage.query.filter_by(email="enq@example.com").count() == 1)

    # -------------------------------- CSRF ----------------------------- #
    r = c.post("/contact", data={"name": "x", "email": "y@z.com", "message": "m"})
    check("POST without CSRF -> 400", r.status_code == 400, f"-> {r.status_code}")

    # ------------------------------- Admin ----------------------------- #
    # wrong login
    set_csrf(c)
    r = c.post("/admin/login", data={"_csrf": "testtoken", "username": "admin", "password": "wrong"})
    check("wrong password rejected", b"Invalid username or password" in r.data)

    # protected route redirects when anonymous
    c2 = app.test_client()
    r = c2.get("/admin/")
    check("anonymous admin -> redirect to login", r.status_code == 302 and "/admin/login" in r.headers.get("Location", ""))

    # correct login
    set_csrf(c)
    r = c.post("/admin/login", data={"_csrf": "testtoken", "username": "admin", "password": "rgipt@2026"},
               follow_redirects=False)
    check("admin login -> redirect", r.status_code in (302, 303), f"-> {r.status_code}")

    for path, label in [
        ("/admin/", "dashboard"),
        ("/admin/events", "admin events"),
        ("/admin/registrations", "admin registrations"),
        ("/admin/announcements", "admin announcements"),
        ("/admin/messages", "admin messages"),
        ("/admin/settings", "admin settings"),
        ("/admin/events/new", "new event form"),
        ("/admin/announcements/new", "new announcement form"),
    ]:
        r = c.get(path)
        check(f"GET {label} [{path}]", r.status_code == 200, f"-> {r.status_code}")

    # CSV export
    r = c.get("/admin/registrations/export.csv")
    check("CSV export 200", r.status_code == 200)
    check("CSV content-type", "text/csv" in r.headers.get("Content-Type", ""))
    check("CSV has header", b"Ticket,Event" in r.data)

    # create event
    set_csrf(c)
    r = c.post("/admin/events/new", data={
        "_csrf": "testtoken", "title": "Smoke Test Event", "category": "Workshop",
        "short_description": "created by test", "description": "body",
        "event_date": "2027-03-01", "end_date": "", "start_time": "10:00 AM",
        "end_time": "04:00 PM", "capacity": "50", "fee": "0", "team_size": "Individual",
        "is_published": "on", "accent": "teal",
    }, follow_redirects=False)
    check("create event -> redirect", r.status_code in (302, 303), f"-> {r.status_code}")
    with app.app_context():
        ev = Event.query.filter_by(title="Smoke Test Event").first()
        check("event persisted", ev is not None)
        new_eid = ev.id if ev else eid

    # edit event
    set_csrf(c)
    r = c.post(f"/admin/events/{new_eid}/edit", data={
        "_csrf": "testtoken", "title": "Smoke Test Event EDITED", "category": "Workshop",
        "short_description": "edited", "description": "body2",
        "event_date": "2027-03-02", "start_time": "09:00 AM", "end_time": "03:00 PM",
        "capacity": "60", "fee": "0", "team_size": "Individual", "is_published": "on",
    }, follow_redirects=False)
    check("edit event -> redirect", r.status_code in (302, 303), f"-> {r.status_code}")
    with app.app_context():
        check("event edited", db.session.get(Event, new_eid).title == "Smoke Test Event EDITED")

    # invalid event (missing title/date)
    set_csrf(c)
    r = c.post("/admin/events/new", data={"_csrf": "testtoken", "title": "", "event_date": ""})
    check("invalid event rejected", b"required" in r.data.lower())

    # toggle publish
    set_csrf(c)
    r = c.post(f"/admin/events/{new_eid}/toggle", data={"_csrf": "testtoken"})
    check("toggle event", r.status_code in (302, 303))
    with app.app_context():
        check("event hidden after toggle", db.session.get(Event, new_eid).is_published is False)

    # registration status change
    set_csrf(c)
    r = c.post(f"/admin/registrations/{rid}/status", data={"_csrf": "testtoken", "status": "waitlist"})
    check("registration status change", r.status_code in (302, 303))
    with app.app_context():
        check("status persisted", db.session.get(Registration, rid).status == "waitlist")

    # create announcement
    set_csrf(c)
    r = c.post("/admin/announcements/new", data={
        "_csrf": "testtoken", "title": "Smoke Announcement", "body": "hello world",
        "category": "General", "is_published": "on",
    }, follow_redirects=False)
    check("create announcement -> redirect", r.status_code in (302, 303))
    with app.app_context():
        a = Announcement.query.filter_by(title="Smoke Announcement").first()
        check("announcement persisted", a is not None)
        new_aid = a.id if a else aid

    # toggle announcement
    set_csrf(c)
    r = c.post(f"/admin/announcements/{new_aid}/toggle", data={"_csrf": "testtoken"})
    check("toggle announcement", r.status_code in (302, 303))

    # message read toggle
    with app.app_context():
        mid = ContactMessage.query.filter_by(email="enq@example.com").first().id
    set_csrf(c)
    r = c.post(f"/admin/messages/{mid}/read", data={"_csrf": "testtoken"})
    check("message mark read", r.status_code in (302, 303))
    with app.app_context():
        check("message read persisted", db.session.get(ContactMessage, mid).is_read is True)

    # password change
    set_csrf(c)
    r = c.post("/admin/settings", data={
        "_csrf": "testtoken", "current_password": "rgipt@2026",
        "new_password": "newpass123", "confirm_password": "newpass123",
    }, follow_redirects=True)
    check("password change", b"updated successfully" in r.data)
    with app.app_context():
        check("new password works", Admin.query.filter_by(username="admin").first().check_password("newpass123"))
    # revert
    set_csrf(c)
    c.post("/admin/settings", data={
        "_csrf": "testtoken", "current_password": "newpass123",
        "new_password": "rgipt@2026", "confirm_password": "rgipt@2026",
    })

    # cleanup created test rows
    set_csrf(c)
    c.post(f"/admin/events/{new_eid}/delete", data={"_csrf": "testtoken"})
    c.post(f"/admin/announcements/{new_aid}/delete", data={"_csrf": "testtoken"})
    c.post(f"/admin/messages/{mid}/delete", data={"_csrf": "testtoken"})
    c.post(f"/admin/registrations/{rid}/status", data={"_csrf": "testtoken", "status": "confirmed"})

    # logout
    r = c.get("/admin/logout", follow_redirects=False)
    check("logout", r.status_code in (302, 303))
    check("admin after logout redirects", c.get("/admin/").status_code == 302)

    # cleanup test student registration
    with app.app_context():
        t = Registration.query.filter_by(email="test.student@example.com").first()
        if t:
            db.session.delete(t)
            db.session.commit()


if __name__ == "__main__":
    try:
        run()
    except Exception:
        traceback.print_exc()
        FAILS.append("EXCEPTION during test run")

    print(f"\n{'='*54}\nPASSED: {len(PASSES)}   FAILED: {len(FAILS)}")
    if FAILS:
        print("\nFailures:")
        for f in FAILS:
            print(" -", f)
        sys.exit(1)
    print("All checks passed.")
