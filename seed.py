"""Seed the RGIPT Sivasagar Campus event database.

Run:  python seed.py           # create tables + seed if empty
      python seed.py --reset   # drop everything and reseed

Content policy: only real, publicly documented campus events and programmes are
seeded, and NO sample registrations are created — registration counts must
reflect real students only. Event dates are the campus's recurring slots; confirm
the exact dates for the current session in the admin panel before publishing.
"""
import os
import sys
from datetime import date, datetime

from app import app
from models import db, Admin, Event, Registration, Announcement, ContactMessage

# --------------------------------------------------------------------------- #
#  Admin accounts
#  Override the initial password with the ADMIN_PASSWORD environment variable
#  before deploying publicly — the default is only for local use.
# --------------------------------------------------------------------------- #
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "rgipt@2026")

ADMINS = [
    # username, password, full name, role
    ("admin", ADMIN_PASSWORD, "Campus Events Administrator", "admin"),
]

# --------------------------------------------------------------------------- #
#  Events — the campus's real, documented events and programmes.
#  (No invented one-off events; dates are the recurring slots for the session.)
# --------------------------------------------------------------------------- #
EVENTS = [
    dict(
        title="Urjotsav 2026",
        category="Technical",
        short_description="The annual national-level inter-collegiate technical & entrepreneurial festival of RGIPT, organised by the Science & Technology Council.",
        description=(
            "Urjotsav is RGIPT's flagship annual technical and entrepreneurial festival, "
            "orchestrated by the Science & Technology Council. Over two days it brings "
            "together students from across the country to compete, collaborate and "
            "innovate \u2014 technical paper presentations, poster sessions, model making, "
            "guest lectures, workshops and panel discussions, plus an entrepreneurship "
            "pitch arena. It is the campus's platform for tomorrow's industry leaders to "
            "unveil their talent."
        ),
        organizer="Science & Technology Council, RGIPT Sivasagar Campus",
        venue="RGIPT Sivasagar Campus, Gohain Gaon, Akhoiphutia",
        event_date=date(2026, 11, 14),
        end_date=date(2026, 11, 15),
        start_time="09:00 AM",
        end_time="06:00 PM",
        registration_deadline=date(2026, 11, 8),
        capacity=500,
        fee=0,
        team_size="Individual or Team (up to 4)",
        accent="amber",
        is_featured=True,
        is_published=True,
    ),
    dict(
        title="Krida Oorja '26",
        category="Sports",
        short_description="The annual sports festival of RGIPT Sivasagar Campus \u2014 weeks of cricket, football, volleyball, badminton, athletics and team spirit.",
        description=(
            "Krida Oorja is the annual sports festival of RGIPT Sivasagar Campus, "
            "celebrating teamwork, sportsmanship and healthy competition. The programme "
            "opens with the traditional torch-lighting ceremony and March Past, and spans "
            "cricket, football, volleyball, badminton and athletics, closing with a "
            "ceremony attended by invited dignitaries. Departments compete for the overall "
            "championship."
        ),
        organizer="Sports Council, RGIPT Sivasagar Campus",
        venue="Campus Sports Ground, RGIPT Sivasagar Campus",
        event_date=date(2026, 12, 1),
        end_date=date(2026, 12, 19),
        start_time="07:00 AM",
        end_time="06:00 PM",
        registration_deadline=date(2026, 11, 25),
        capacity=400,
        fee=0,
        team_size="Team",
        accent="emerald",
        is_featured=True,
        is_published=True,
    ),
    dict(
        title="TechSprint 2026 \u2013 Campus Edition",
        category="Hackathon",
        short_description="The GDG on Campus open-innovation hackathon \u2014 build practical solutions with Google technologies. Solve. Create. Impact.",
        description=(
            "TechSprint is the flagship open-innovation hackathon hosted by Google "
            "Developer Group on Campus, RGIPT Sivasagar Campus. Student developers identify "
            "real challenges in their campus or local communities and build practical "
            "solutions using Google technologies \u2014 Android, Flutter, Firebase and Google "
            "Cloud. Beginners and experienced builders are both welcome. Teams progress "
            "through evaluation rounds with mentorship and codelabs, ending in a demo day "
            "before judges."
        ),
        organizer="GDG on Campus, RGIPT Sivasagar Campus",
        venue="Online + Computer Lab, RGIPT Sivasagar Campus",
        event_date=date(2026, 12, 4),
        end_date=date(2027, 1, 22),
        start_time="07:00 PM",
        end_time="11:59 PM",
        registration_deadline=date(2027, 1, 22),
        capacity=300,
        fee=0,
        team_size="Team (2\u20134)",
        contact_email="gdgocrgiptsc@rgipt.ac.in",
        accent="indigo",
        is_featured=True,
        is_published=True,
    ),
    dict(
        title="Google Cloud Study Jams",
        category="Workshop",
        short_description="A hands-on cloud computing workshop series with guided labs, badges and certifications via Google Cloud Skills Boost.",
        description=(
            "An intensive, hands-on workshop series to kickstart your cloud computing "
            "journey with Google Cloud Study Jams. Participants work through guided labs on "
            "compute, storage, networking and AI on the Google Cloud Skills Boost platform, "
            "earning badges and certifications along the way. Bring a laptop."
        ),
        organizer="GDG on Campus, RGIPT Sivasagar Campus",
        venue="Computer Lab, RGIPT Sivasagar Campus",
        event_date=date(2026, 10, 20),
        start_time="10:00 AM",
        end_time="04:00 PM",
        registration_deadline=date(2026, 10, 18),
        capacity=80,
        fee=0,
        team_size="Individual",
        accent="teal",
        is_published=True,
    ),
    # ------------------------------ Past ------------------------------- #
    dict(
        title="TechWave 2026 \u2013 Ideas in Motion",
        category="Technical",
        short_description="The campus Engineers' Day celebration \u2014 model making and poster presentation, organised by the Science & Technology Council.",
        description=(
            "TechWave 2026, themed \u201cIdeas in Motion\u201d, was organised by the Science & "
            "Technology Council on the occasion of Engineers' Day. It gave students a "
            "platform to showcase creativity, technical knowledge and problem-solving "
            "through Model Making and Poster Presentation, and celebrated collaboration and "
            "transforming concepts into meaningful outcomes."
        ),
        organizer="Science & Technology Council, RGIPT Sivasagar Campus",
        venue="RGIPT Sivasagar Campus, Gohain Gaon",
        event_date=date(2026, 9, 15),
        start_time="10:00 AM",
        end_time="05:00 PM",
        capacity=250,
        fee=0,
        team_size="Team (1\u20133)",
        accent="teal",
        is_published=True,
    ),
    dict(
        title="Internal Hackathon for SIH 2026",
        category="Hackathon",
        short_description="The campus-level Smart India Hackathon \u2014 selection of RGIPT's best teams for nomination to SIH 2026.",
        description=(
            "RGIPT organised an Internal Hackathon to select the best teams from the "
            "institute for nomination to Smart India Hackathon 2026 (SIH 2026), hosted by "
            "the Ministry of Education's Innovation Cell, Government of India. Teams worked "
            "on real problem statements, with shortlisted teams advancing to the national "
            "stage."
        ),
        organizer="Innovation Cell, RGIPT",
        venue="Computer Lab, RGIPT Sivasagar Campus",
        event_date=date(2026, 9, 18),
        end_date=date(2026, 9, 20),
        start_time="09:00 AM",
        end_time="09:00 PM",
        capacity=200,
        fee=0,
        team_size="Team (6)",
        accent="indigo",
        is_published=True,
    ),
    dict(
        title="SCHEMCON 2026 \u2013 Students' Chemical Engineering Congress",
        category="Seminar",
        short_description="The national Students' Chemical Engineering Congress \u2014 technical papers, poster sessions, workshops and panel discussions.",
        description=(
            "SCHEMCON (Students' Chemical Engineering Congress) is an annual national-level "
            "congress organised by the Indian Institute of Chemical Engineers (IIChE) "
            "through its student chapters. Editions feature technical paper presentations, "
            "poster sessions, guest lectures, workshops and panel discussions around a "
            "contemporary theme in chemical engineering."
        ),
        organizer="IIChE Student Chapter, RGIPT Sivasagar Campus",
        venue="Seminar Hall, RGIPT Sivasagar Campus",
        event_date=date(2026, 8, 8),
        end_date=date(2026, 8, 9),
        start_time="09:00 AM",
        end_time="06:00 PM",
        capacity=300,
        fee=0,
        team_size="Individual or Team",
        accent="emerald",
        is_published=True,
    ),
]

# --------------------------------------------------------------------------- #
#  Announcements — starter notices based on documented campus activity.
#  Edit or replace these from the admin panel before publishing.
# --------------------------------------------------------------------------- #
ANNOUNCEMENTS = [
    dict(
        title="Registrations open for Urjotsav 2026",
        body=(
            "Registration for Urjotsav 2026, the annual national-level technical and "
            "entrepreneurial festival, is now open. Students from RGIPT and other institutes "
            "can register for individual and team events. Visit the Events page to register."
        ),
        category="Events",
        is_pinned=True,
        is_published=True,
    ),
    dict(
        title="TechSprint 2026 \u2013 registration open",
        body=(
            "Teams of 2 to 4 members may register for TechSprint 2026, the GDG on Campus "
            "open-innovation hackathon, via the Events page. For queries, write to "
            "gdgocrgiptsc@rgipt.ac.in."
        ),
        category="Hackathon",
        is_pinned=False,
        is_published=True,
    ),
    dict(
        title="Krida Oorja '26 \u2013 department trials",
        body=(
            "Trials for Krida Oorja '26 begin soon. Captains of each department should "
            "submit their squad lists to the Sports Council. Cricket, football, volleyball, "
            "badminton and athletics events are planned across the coming weeks."
        ),
        category="Sports",
        is_pinned=False,
        is_published=True,
    ),
    dict(
        title="Internal Hackathon for SIH 2026 \u2013 results",
        body=(
            "Congratulations to the teams shortlisted from the Internal Hackathon for "
            "nomination to Smart India Hackathon 2026. Shortlisted teams should complete "
            "their SIH portal formalities before the national deadline."
        ),
        category="Hackathon",
        is_pinned=False,
        is_published=True,
    ),
]


def seed(reset=False):
    with app.app_context():
        if reset:
            db.drop_all()
        db.create_all()

        # Admins
        for username, pw, full_name, role in ADMINS:
            if not Admin.query.filter_by(username=username).first():
                a = Admin(username=username, full_name=full_name, role=role)
                a.set_password(pw)
                db.session.add(a)
        db.session.commit()

        # Events
        if Event.query.count() == 0:
            from app import slugify
            created = []
            for data in EVENTS:
                ev = Event(**data)
                base = slugify(ev.title)
                slug, i = base, 2
                while Event.query.filter_by(slug=slug).first():
                    slug = f"{base}-{i}"
                    i += 1
                ev.slug = slug
                db.session.add(ev)
                created.append(ev)
            db.session.commit()
            print(f"Seeded {len(created)} events.")
        else:
            print(f"Events already present ({Event.query.count()}).")

        # Announcements
        if Announcement.query.count() == 0:
            for data in ANNOUNCEMENTS:
                db.session.add(Announcement(**data))
            db.session.commit()
            print(f"Seeded {len(ANNOUNCEMENTS)} announcements.")

        # No sample registrations are created — the registration table starts
        # empty so every figure shown on the site is a real student's entry.
        print(f"Registrations: {Registration.query.count()} (none are seeded).")

        print("\nDone. Admin login -> username: admin | password: "
              + ("(set via ADMIN_PASSWORD)" if os.environ.get("ADMIN_PASSWORD") else "rgipt@2026"))


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
