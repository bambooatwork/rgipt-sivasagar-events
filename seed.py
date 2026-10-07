"""Seed the RGIPT Sivasagar Campus event database.

Run:  python seed.py           # create tables + seed if empty
      python seed.py --reset   # drop everything and reseed
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
#  Events  (real RGIPT Sivasagar flagship events + campus activities)
#  today == 2026-10-07
# --------------------------------------------------------------------------- #
EVENTS = [
    dict(
        title="Urjotsav 2026",
        category="Technical",
        short_description="The annual national-level inter-collegiate technical & entrepreneurial festival of RGIPT, organised by the Science & Technology Council.",
        description=(
            "Urjotsav is RGIPT's flagship annual technical and entrepreneurial festival, "
            "orchestrated by the Science & Technology Council. Over two action-packed days it "
            "brings together students from across the country to compete, collaborate and "
            "innovate. The 2026 edition features robotics, coding sprints, model making, "
            "poster presentations, an entrepreneurship pitch arena, and expert talks from the "
            "oil & gas and energy sectors. It is the definitive platform for tomorrow's "
            "industry leaders to unveil their talent."
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
        short_description="The annual sports fest of RGIPT Sivasagar Campus \u2014 three weeks of cricket, football, athletics, volleyball and more.",
        description=(
            "Krida Oorja is the much-loved annual sports festival of RGIPT Sivasagar Campus, "
            "celebrating teamwork, sportsmanship and healthy competition. The 2026 edition "
            "spans three weeks of cricketing rivalries, football, volleyball, badminton, "
            "athletics and indoor games, opening with the traditional torch-lighting ceremony "
            "and March Past. Departments battle it out for the overall championship trophy, "
            "culminating in a grand closing ceremony with guest dignitaries."
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
        short_description="GDG on Campus RGIPT Sivasagar's flagship open innovation hackathon. Solve. Create. Impact.",
        description=(
            "TechSprint is the flagship open-innovation hackathon hosted by Google Developer "
            "Group on Campus, RGIPT Sivasagar Campus. Student developers identify real "
            "challenges in their campus or local communities and build practical solutions "
            "using Google technologies \u2014 Android, Flutter, Firebase and Google Cloud. "
            "Beginners and experienced builders alike are welcome. Teams progress through "
            "multiple evaluation rounds, with mentorship sessions, codelabs and a final "
            "demo day before industry judges."
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
        short_description="Kickstart your cloud computing journey \u2014 hands-on labs, badges and certifications via Google Cloud Skills Boost.",
        description=(
            "An intensive, hands-on workshop series to kickstart your cloud computing journey "
            "with Google Cloud Study Jams. Participants get guided labs on compute, storage, "
            "networking and AI on the Google Cloud Skills Boost platform, earning badges and "
            "certifications along the way. Bring a laptop \u2014 everything else is provided."
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
    dict(
        title="Industry Connect: OIL Field Visit & Expert Seminar",
        category="Seminar",
        short_description="A guided field visit and seminar with Oil India Limited (OIL) engineers on upstream operations in the Assam oil belt.",
        description=(
            "RGIPT Sivasagar Campus sits in the heart of Assam's oil-rich belt, giving students "
            "unparalleled exposure to the petroleum industry. This Industry Connect session "
            "combines a guided field visit with a technical seminar led by engineers from Oil "
            "India Limited (OIL) and the Department of Petroleum Engineering. Topics include "
            "upstream exploration & production, well logging, enhanced oil recovery and HSE "
            "practices in the North-East fields."
        ),
        organizer="Department of Petroleum Engineering, RGIPT Sivasagar Campus",
        venue="Duliajan / Naharkatia Field + Campus Auditorium",
        event_date=date(2026, 10, 28),
        start_time="08:30 AM",
        end_time="05:30 PM",
        registration_deadline=date(2026, 10, 24),
        capacity=60,
        fee=0,
        team_size="Individual",
        accent="rose",
        is_published=True,
    ),
    dict(
        title="Fire & Safety Drill Workshop",
        category="Workshop",
        short_description="Practical fire-safety training for the Fire & Safety Engineering department \u2014 extinguishers, rescue and evacuation drills.",
        description=(
            "A hands-on fire and industrial safety workshop for students of Fire & Safety "
            "Engineering and allied branches. Sessions cover fire chemistry, types and use of "
            "extinguishers, breathing apparatus, rescue techniques and mock evacuation drills, "
            "delivered by certified safety instructors in partnership with industry."
        ),
        organizer="Department of Fire & Safety Engineering, RGIPT Sivasagar Campus",
        venue="Open Ground, RGIPT Sivasagar Campus",
        event_date=date(2026, 11, 5),
        start_time="09:30 AM",
        end_time="03:30 PM",
        registration_deadline=date(2026, 11, 3),
        capacity=120,
        fee=0,
        team_size="Individual",
        accent="amber",
        is_published=True,
    ),
    dict(
        title="Innovation Pitch: Startup Bootcamp",
        category="Entrepreneurship",
        short_description="A one-day entrepreneurship bootcamp and pitch competition for aspiring founders, hosted by the campus E-Cell.",
        description=(
            "Turn an idea into a venture. This bootcamp walks participants through "
            "problem discovery, business models, unit economics and pitching, followed by a "
            "live pitch competition before a panel of mentors and investors. Winning teams "
            "receive incubation support and certificates. Open to all departments."
        ),
        organizer="Entrepreneurship Cell, RGIPT Sivasagar Campus",
        venue="Seminar Hall, RGIPT Sivasagar Campus",
        event_date=date(2026, 11, 22),
        start_time="09:00 AM",
        end_time="05:00 PM",
        registration_deadline=date(2026, 11, 19),
        capacity=100,
        fee=0,
        team_size="Team (1\u20133)",
        accent="violet",
        is_published=True,
    ),
    dict(
        title="Sivasagar Cultural Night \u2013 Bihu & Borgeet Evening",
        category="Cultural",
        short_description="An evening celebrating Assam's heritage \u2014 Bihu dance, Borgeet, folk music and student performances.",
        description=(
            "A vibrant cultural evening celebrating the rich heritage of Assam and the "
            "North-East. The programme features Bihu dance performances, Borgeet and folk "
            "music, a student talent showcase, and a community dinner. Family and friends of "
            "the campus community are warmly invited."
        ),
        organizer="Cultural Council, RGIPT Sivasagar Campus",
        venue="Campus Open Air Theatre, RGIPT Sivasagar Campus",
        event_date=date(2026, 12, 18),
        start_time="05:00 PM",
        end_time="09:30 PM",
        registration_deadline=date(2026, 12, 16),
        capacity=600,
        fee=0,
        team_size="Individual",
        accent="rose",
        is_published=True,
    ),
    # ------------------------------ Past ------------------------------- #
    dict(
        title="TechWave 2026 \u2013 Ideas in Motion",
        category="Technical",
        short_description="Engineers' Day celebration \u2014 model making and poster presentation competition organised by the Science & Technology Council.",
        description=(
            "TechWave 2026, themed \u201cIdeas in Motion\u201d, was organised by the Science & "
            "Technology Council on the occasion of Engineers' Day. It gave students a platform "
            "to showcase creativity, technical knowledge and problem-solving through Model "
            "Making and Poster Presentation. Beyond the competitions, the event celebrated "
            "collaboration, learning and transforming concepts into meaningful outcomes."
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
        short_description="Campus-level Smart India Hackathon \u2014 selection of RGIPT's best teams for nomination to SIH 2026.",
        description=(
            "RGIPT organised an Internal Hackathon to select the best teams from the institute "
            "for nomination to the prestigious Smart India Hackathon 2026 (SIH 2026), hosted by "
            "the Ministry of Education's Innovation Cell, Government of India. Teams worked "
            "intensely over three days on real problem statements, with shortlisted teams "
            "advancing to the national stage."
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
        short_description="A national-level congress with technical paper presentations, poster sessions, workshops and panel discussions.",
        description=(
            "SCHEMCON (Students' Chemical Engineering Congress) is an annual national-level "
            "event organised by the Indian Institute of Chemical Engineers (IIChE) through its "
            "student chapters. This edition featured technical paper presentations, poster "
            "sessions, guest lectures, workshops and panel discussions around a contemporary "
            "theme of sustainability and energy innovation, fostering knowledge exchange and "
            "professional development."
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
#  Announcements
# --------------------------------------------------------------------------- #
ANNOUNCEMENTS = [
    dict(
        title="Registrations open for Urjotsav 2026",
        body=(
            "Registration for Urjotsav 2026, the annual national-level technical and "
            "entrepreneurial festival, is now open. Students from RGIPT and other institutes "
            "can register for individual and team events. Early registration closes on "
            "8 November 2026. Visit the Events page to register."
        ),
        category="Events",
        is_pinned=True,
        is_published=True,
    ),
    dict(
        title="TechSprint 2026 \u2013 last date to register extended",
        body=(
            "The last date to register for TechSprint 2026, the GDG on Campus open-innovation "
            "hackathon, has been extended. Teams of 2 to 4 members may register via the Events "
            "page. For queries, write to gdgocrgiptsc@rgipt.ac.in."
        ),
        category="Hackathon",
        is_pinned=False,
        is_published=True,
    ),
    dict(
        title="Krida Oorja '26 \u2013 department trials schedule",
        body=(
            "Trials for Krida Oorja '26 begin soon. Captains of each department should submit "
            "their squad lists to the Sports Council. Cricket, football, volleyball, badminton "
            "and athletics events are planned across three weeks. Watch this space for fixtures."
        ),
        category="Sports",
        is_pinned=False,
        is_published=True,
    ),
    dict(
        title="Results: Internal Hackathon for SIH 2026",
        body=(
            "Congratulations to the teams shortlisted from the Internal Hackathon for "
            "nomination to Smart India Hackathon 2026. Shortlisted teams should complete their "
            "SIH portal formalities before the national deadline. Details have been shared with "
            "team leaders."
        ),
        category="Hackathon",
        is_pinned=False,
        is_published=True,
    ),
    dict(
        title="Notice: Academic calendar and winter vacation",
        body=(
            "The academic office has published the revised academic calendar. End-semester "
            "examinations and the winter vacation schedule are available on the notice board. "
            "Students should clear dues and complete lab records before the examination period."
        ),
        category="Academic",
        is_pinned=False,
        is_published=True,
    ),
]

SAMPLE_REGISTRATIONS = [
    dict(event_index=0, name="Ananya Baruah", email="ananya.baruah@example.com", phone="9864012345",
         college="RGIPT Sivasagar Campus", department="Petroleum Engineering", year="3rd Year",
         team_name="Team Hydro", status="confirmed"),
    dict(event_index=0, name="Rahul Das", email="rahul.das@example.com", phone="9864012346",
         college="RGIPT Sivasagar Campus", department="Chemical Engineering", year="2nd Year",
         team_name="Team Hydro", status="confirmed"),
    dict(event_index=2, name="Priya Gogoi", email="priya.gogoi@example.com", phone="9864012347",
         college="RGIPT Sivasagar Campus", department="Computer Science & Engineering", year="3rd Year",
         team_name="CodeBrew", status="confirmed"),
    dict(event_index=2, name="Imran Ahmed", email="imran.ahmed@example.com", phone="9864012348",
         college="RGIPT Sivasagar Campus", department="Electronics & Instrumentation Engineering", year="2nd Year",
         team_name="CodeBrew", status="confirmed"),
    dict(event_index=1, name="Sanjib Saikia", email="sanjib.saikia@example.com", phone="9864012349",
         college="RGIPT Sivasagar Campus", department="Mechanical Engineering", year="1st Year",
         team_name="Team Mech", status="confirmed"),
    dict(event_index=3, name="Nabanita Bora", email="nabanita.bora@example.com", phone="9864012350",
         college="RGIPT Sivasagar Campus", department="Electrical Engineering", year="2nd Year",
         team_name="", status="confirmed"),
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
            created = []
            for data in EVENTS:
                ev = Event(**data)
                # slug from title
                from app import slugify
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
            created = Event.query.order_by(Event.id).all()
            print(f"Events already present ({len(created)}).")

        # Announcements
        if Announcement.query.count() == 0:
            for data in ANNOUNCEMENTS:
                db.session.add(Announcement(**data))
            db.session.commit()
            print(f"Seeded {len(ANNOUNCEMENTS)} announcements.")

        # Sample registrations
        if Registration.query.count() == 0:
            from app import make_ticket_code
            for data in SAMPLE_REGISTRATIONS:
                idx = data.pop("event_index")
                if idx < len(created):
                    reg = Registration(event_id=created[idx].id, ticket_code=make_ticket_code(), **data)
                    db.session.add(reg)
            db.session.commit()
            print(f"Seeded {len(SAMPLE_REGISTRATIONS)} sample registrations.")

        print("\nDone. Admin login -> username: admin | password: rgipt@2026")


if __name__ == "__main__":
    seed(reset="--reset" in sys.argv)
