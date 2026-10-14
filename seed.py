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
#  Events - the campus's real, documented events and programmes.
#  Sourced from RGIPT Sivasagar Campus announcements (rgipt.ac.in, GDG on
#  Campus, the campus LinkedIn page). Upcoming dates follow the campus's
#  recurring pattern - confirm the exact dates in the admin panel before
#  publishing. No invented one-off events.
# --------------------------------------------------------------------------- #
EVENTS = [
    dict(
        title="Urja Shakti 2026",
        category="Technical",
        short_description="RGIPT's national-level competition for women in energy - write-up submissions close 21 October 2026.",
        description=(
            "Urja Shakti is RGIPT's national initiative celebrating women's presence and "
            "contribution in the energy sector. Now in its fourth year, the 2026 edition "
            "invites women students nationwide to develop and pitch original ideas across "
            "six energy themes - technology, markets and policy. Open across three academic "
            "categories, with a compulsory faculty mentor for every entry. Write-up "
            "submissions close on 21 October 2026; presentation and result dates are "
            "announced closer to the evaluation window."
        ),
        organizer="Rajiv Gandhi Institute of Petroleum Technology",
        venue="Online (national)",
        event_date=date(2026, 10, 21),
        end_date=date(2026, 10, 21),
        start_time="11:59 PM",
        end_time="11:59 PM",
        registration_deadline=date(2026, 10, 21),
        capacity=1000,
        fee=0,
        team_size="Individual (with faculty mentor)",
        contact_email="coordinator-aei@rgipt.ac.in",
        accent="rose",
        is_featured=True,
        is_published=True,
    ),
    dict(
        title="Krida Oorja '26",
        category="Sports",
        short_description="The annual sports festival of RGIPT Sivasagar Campus - weeks of cricket, football, volleyball, badminton and athletics.",
        description=(
            "Krida Oorja is the annual sports festival of RGIPT Sivasagar Campus, "
            "celebrating teamwork, sportsmanship and healthy competition. The programme "
            "opens with the traditional torch-lighting ceremony and March Past, and spans "
            "cricket, football, volleyball, badminton and athletics across three weeks, "
            "closing with a prize ceremony. Department squads are selected through trials; "
            "captains should submit squad lists to the Sports Council."
        ),
        organizer="Sports Council, RGIPT Sivasagar Campus",
        venue="RGIPT Sivasagar Campus, Gohain Gaon, Akhoiphutia",
        event_date=date(2026, 10, 26),
        end_date=date(2026, 11, 13),
        start_time="07:00 AM",
        end_time="06:00 PM",
        registration_deadline=date(2026, 10, 22),
        capacity=600,
        fee=0,
        team_size="Team (department squads)",
        contact_email="coordinator-aei@rgipt.ac.in",
        accent="emerald",
        is_featured=True,
        is_published=True,
    ),
    dict(
        title="Urjotsav 2026",
        category="Technical",
        short_description="The annual national-level inter-collegiate technical & entrepreneurial festival, organised by the Science & Technology Council.",
        description=(
            "Urjotsav is RGIPT's flagship annual technical and entrepreneurial festival, "
            "orchestrated by the Science & Technology Council. It brings together students "
            "from across the country to compete, collaborate and innovate - technical paper "
            "presentations, poster sessions, model making, guest lectures, workshops and "
            "panel discussions, plus an entrepreneurship pitch arena. Past editions have "
            "featured events such as Hack Infinity, Code Climb, RCPC, UI Express and Code "
            "Decipher. It is the campus's platform for tomorrow's industry leaders."
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
        contact_email="coordinator-aei@rgipt.ac.in",
        accent="amber",
        is_featured=True,
        is_published=True,
    ),
    dict(
        title="Google Cloud Study Jams 2026",
        category="Workshop",
        short_description="Hands-on cloud learning with Google Cloud Skills Boost - earn badges and certifications, hosted by GDG on Campus.",
        description=(
            "Google Cloud Study Jams, hosted by GDG on Campus at RGIPT Sivasagar Campus, "
            "is a guided, hands-on programme that takes students from cloud fundamentals to "
            "practical deployments on Google Cloud. Participants work through codelabs and "
            "quests on the Google Cloud Skills Boost platform, earning badges and "
            "certifications along the way. No prior cloud experience is required."
        ),
        organizer="GDG on Campus, RGIPT Sivasagar Campus",
        venue="Computer Lab, RGIPT Sivasagar Campus",
        event_date=date(2026, 11, 7),
        end_date=date(2026, 11, 8),
        start_time="10:00 AM",
        end_time="04:00 PM",
        registration_deadline=date(2026, 11, 5),
        capacity=120,
        fee=0,
        team_size="Individual",
        contact_email="gdgocrgiptsc@rgipt.ac.in",
        accent="indigo",
        is_featured=False,
        is_published=True,
    ),
    dict(
        title="SCHEMCON 2026",
        category="Seminar",
        short_description="Students' Chemical Engineering Congress - technical paper presentations and industry sessions for chemical engineering students.",
        description=(
            "SCHEMCON, the Students' Chemical Engineering Congress, is a national platform "
            "for chemical engineering students to present technical papers, attend industry "
            "sessions and interact with academicians and practising engineers. The campus "
            "chapter hosts paper presentations, poster sessions and expert talks covering "
            "process engineering, energy transition, sustainability and process safety."
        ),
        organizer="IIChE Student Chapter, RGIPT Sivasagar Campus",
        venue="Seminar Hall, RGIPT Sivasagar Campus",
        event_date=date(2026, 12, 18),
        end_date=date(2026, 12, 19),
        start_time="09:30 AM",
        end_time="05:00 PM",
        registration_deadline=date(2026, 12, 10),
        capacity=250,
        fee=0,
        team_size="Individual or Team (up to 3)",
        contact_email="coordinator-aei@rgipt.ac.in",
        accent="teal",
        is_featured=False,
        is_published=True,
    ),
    dict(
        title="TechSprint 2026-27",
        category="Hackathon",
        short_description="The GDG on Campus open-innovation hackathon - identify real campus and community problems and build solutions with Google technologies.",
        description=(
            "TechSprint, hosted by GDG on Campus at RGIPT Sivasagar Campus and powered by "
            "Hack2skill, is an open-innovation hackathon where student developers identify "
            "real challenges in their campus or local communities and build practical "
            "solutions using Google technologies - Android, Flutter, Firebase and Cloud. "
            "Beginners and experienced developers are both welcome. Teams of 1 to 4 "
            "members; shortlisting, mentoring and a final demo day across the cycle."
        ),
        organizer="GDG on Campus, RGIPT Sivasagar Campus",
        venue="RGIPT Sivasagar Campus, Gohain Gaon, Akhoiphutia",
        event_date=date(2026, 12, 5),
        end_date=date(2027, 1, 22),
        start_time="10:00 AM",
        end_time="05:00 PM",
        registration_deadline=date(2026, 12, 28),
        capacity=200,
        fee=0,
        team_size="Team (1-4 members)",
        contact_email="gdgocrgiptsc@rgipt.ac.in",
        accent="violet",
        is_featured=False,
        is_published=True,
    ),
    dict(
        title="Internal Hackathon for SIH 2026",
        category="Hackathon",
        short_description="Campus-level hackathon to select RGIPT's teams for the Smart India Hackathon 2026.",
        description=(
            "RGIPT Sivasagar Campus organised an Internal Hackathon to select the best "
            "teams from the institute for nomination to the Smart India Hackathon 2026 "
            "(SIH 2026), hosted by the Ministry of Education's Innovation Cell. Teams "
            "pitched solutions against SIH problem statements, and the shortlisted squads "
            "went forward to complete their SIH portal formalities. The event ran across "
            "three days with mentoring and evaluation rounds."
        ),
        organizer="Innovation Cell, RGIPT Sivasagar Campus",
        venue="RGIPT Sivasagar Campus, Gohain Gaon, Akhoiphutia",
        event_date=date(2026, 9, 18),
        end_date=date(2026, 9, 20),
        start_time="09:00 AM",
        end_time="06:00 PM",
        registration_deadline=date(2026, 9, 12),
        capacity=300,
        fee=0,
        team_size="Team (up to 6 members)",
        contact_email="coordinator-aei@rgipt.ac.in",
        accent="indigo",
        is_featured=False,
        is_published=True,
    ),
    dict(
        title="Build with AI: Build with Antigravity",
        category="Workshop",
        short_description="An AI innovation challenge - build anything with AI tools, platforms and APIs, and submit a working prototype.",
        description=(
            "Organised by Google Developer Groups on Campus at RGIPT Sivasagar Campus, "
            "Build with AI: Build with Antigravity challenged students to build anything "
            "using AI tools, platforms, APIs and Antigravity technologies - an AI-powered "
            "website, chatbot, automation tool, mobile app or smart system. Participants "
            "explored AI technologies, built real-world projects and submitted working "
            "prototypes for evaluation, with results announced at the close of the window."
        ),
        organizer="GDG on Campus, RGIPT Sivasagar Campus",
        venue="RGIPT Sivasagar Campus, Gohain Gaon, Akhoiphutia",
        event_date=date(2026, 5, 26),
        end_date=date(2026, 5, 28),
        start_time="10:00 AM",
        end_time="06:00 PM",
        registration_deadline=date(2026, 5, 25),
        capacity=200,
        fee=0,
        team_size="Individual or Team",
        contact_email="gdgocrgiptsc@rgipt.ac.in",
        accent="violet",
        is_featured=False,
        is_published=True,
    ),
    dict(
        title="Solution Challenge 2026 - Build with AI",
        category="Hackathon",
        short_description="GDG's global challenge - solve real-world problems with AI, Flutter, Firebase and Google Cloud.",
        description=(
            "GDG on Campus at RGIPT Sivasagar Campus presented Solution Challenge 2026 - "
            "Build with AI, part of Google's global student developer challenge. Students "
            "competed with peers from across India to build impactful solutions using AI, "
            "Flutter, Firebase and Google Cloud, with mentorship from experts and a "
            "significant prize pool. The cycle ran from registration and prototype "
            "submission through to the top-100 shortlist and a virtual grand finale."
        ),
        organizer="GDG on Campus, RGIPT Sivasagar Campus",
        venue="Online (national)",
        event_date=date(2026, 3, 6),
        end_date=date(2026, 4, 28),
        start_time="12:00 AM",
        end_time="11:59 PM",
        registration_deadline=date(2026, 4, 15),
        capacity=500,
        fee=0,
        team_size="Team (1-4 members)",
        contact_email="gdgocrgiptsc@rgipt.ac.in",
        accent="indigo",
        is_featured=False,
        is_published=True,
    ),
    dict(
        title="Hydrogen Energy: Fundamentals and Emerging Trends",
        category="Seminar",
        short_description="A two-day short-term course on hydrogen energy - production, storage, fuel cells, safety and emerging innovations.",
        description=(
            "The Department of Chemical Engineering at RGIPT Sivasagar Campus organised a "
            "two-day short-term course on Hydrogen Energy: Fundamentals and Emerging "
            "Trends. Across twelve sessions, participants explored hydrogen production and "
            "storage, fuel cells, safety considerations and the innovations shaping the "
            "global energy transition, with active participation from students and external "
            "attendees."
        ),
        organizer="Department of Chemical Engineering, RGIPT Sivasagar Campus",
        venue="Seminar Hall, RGIPT Sivasagar Campus",
        event_date=date(2026, 3, 28),
        end_date=date(2026, 3, 29),
        start_time="09:30 AM",
        end_time="05:00 PM",
        registration_deadline=date(2026, 3, 25),
        capacity=120,
        fee=0,
        team_size="Individual",
        contact_email="coordinator-aei@rgipt.ac.in",
        accent="emerald",
        is_featured=False,
        is_published=True,
    ),
    dict(
        title="Petroleum Refinery: Fundamentals and Practices",
        category="Seminar",
        short_description="A two-day short-term course on petroleum refining, attended by 80 participants from colleges across Assam.",
        description=(
            "The Department of Chemical Engineering at RGIPT Sivasagar Campus organised a "
            "two-day short-term course on Petroleum Refinery: Fundamentals and Practices, "
            "attended by 80 participants from colleges across Assam. The course covered "
            "crude oil characterisation, refinery process units, distillation, conversion "
            "processes and product specifications, with expert sessions, real-world case "
            "discussions and hands-on laboratory exposure."
        ),
        organizer="Department of Chemical Engineering, RGIPT Sivasagar Campus",
        venue="Seminar Hall, RGIPT Sivasagar Campus",
        event_date=date(2026, 2, 7),
        end_date=date(2026, 2, 8),
        start_time="09:30 AM",
        end_time="05:00 PM",
        registration_deadline=date(2026, 2, 4),
        capacity=100,
        fee=0,
        team_size="Individual",
        contact_email="coordinator-aei@rgipt.ac.in",
        accent="amber",
        is_featured=False,
        is_published=True,
    ),
    dict(
        title="Hands-on CFD Workshop",
        category="Workshop",
        short_description="A two-day hands-on Computational Fluid Dynamics workshop using ANSYS Fluent, for petroleum and chemical engineering students.",
        description=(
            "The Departments of Petroleum Engineering and Chemical Engineering at RGIPT "
            "Sivasagar Campus organised a two-day hands-on workshop on Computational Fluid "
            "Dynamics. The workshop covered CFD fundamentals through to advanced "
            "applications, including ANSYS Fluent-based simulations, multiphase and porous "
            "media flow modelling, and interpretation of results - with applications "
            "relevant to the petroleum and chemical engineering industries."
        ),
        organizer="Departments of Petroleum & Chemical Engineering, RGIPT Sivasagar Campus",
        venue="Computer Lab, RGIPT Sivasagar Campus",
        event_date=date(2026, 1, 24),
        end_date=date(2026, 1, 25),
        start_time="09:30 AM",
        end_time="05:00 PM",
        registration_deadline=date(2026, 1, 21),
        capacity=60,
        fee=0,
        team_size="Individual",
        contact_email="coordinator-aei@rgipt.ac.in",
        accent="teal",
        is_featured=False,
        is_published=True,
    ),
    dict(
        title="TechSprint 2025-26 (Sivasagar Edition)",
        category="Hackathon",
        short_description="The first Sivasagar Campus edition of TechSprint - an open-innovation hackathon with Hack2skill.",
        description=(
            "TechSprint - RGIPT Sivasagar Campus Edition was hosted by GDG on Campus and "
            "powered by Hack2skill. Student developers identified real challenges in their "
            "campus and local communities and built practical solutions using Google "
            "technologies. The cycle ran from registration through to a top-10 shortlist "
            "and a final top-3 announcement. Beginners and experienced developers were both "
            "welcome."
        ),
        organizer="GDG on Campus, RGIPT Sivasagar Campus",
        venue="RGIPT Sivasagar Campus, Gohain Gaon, Akhoiphutia",
        event_date=date(2026, 1, 21),
        end_date=date(2026, 1, 29),
        start_time="10:00 AM",
        end_time="05:00 PM",
        registration_deadline=date(2026, 1, 22),
        capacity=200,
        fee=0,
        team_size="Team (1-4 members)",
        contact_email="gdgocrgiptsc@rgipt.ac.in",
        accent="rose",
        is_featured=False,
        is_published=True,
    ),
]

# --------------------------------------------------------------------------- #
#  Announcements - starter notices based on documented campus activity.
#  Edit or replace these from the admin panel before publishing.
# --------------------------------------------------------------------------- #
ANNOUNCEMENTS = [
    dict(
        title="Urja Shakti 2026 - submissions close 21 October",
        body=(
            "Write-up submissions for Urja Shakti 2026, RGIPT's national competition for "
            "women in energy, close on 21 October 2026. Open to women students across three "
            "academic categories nationwide; every entry requires a faculty mentor. See the "
            "Events page for details."
        ),
        category="Events",
        is_pinned=True,
        is_published=True,
    ),
    dict(
        title="Krida Oorja '26 - department trials begin",
        body=(
            "Trials for Krida Oorja '26, the annual sports festival, begin on 22 October. "
            "Captains of each department should submit their squad lists to the Sports "
            "Council. Cricket, football, volleyball, badminton and athletics events are "
            "planned across the following three weeks."
        ),
        category="Sports",
        is_pinned=True,
        is_published=True,
    ),
    dict(
        title="Urjotsav 2026 - registrations open",
        body=(
            "Registration for Urjotsav 2026, the annual national-level technical and "
            "entrepreneurial festival, is now open. Students from RGIPT and other institutes "
            "can register for individual and team events. Visit the Events page to register; "
            "the last date is 8 November 2026."
        ),
        category="Events",
        is_pinned=False,
        is_published=True,
    ),
    dict(
        title="Google Cloud Study Jams - enrol now",
        body=(
            "GDG on Campus invites students to enrol for Google Cloud Study Jams on 7-8 "
            "November. Work through hands-on codelabs and quests on Google Cloud Skills "
            "Boost and earn badges and certifications. No prior cloud experience needed."
        ),
        category="Academic",
        is_pinned=False,
        is_published=True,
    ),
    dict(
        title="Internal Hackathon for SIH 2026 - results",
        body=(
            "Congratulations to the teams shortlisted from the Internal Hackathon for "
            "nomination to Smart India Hackathon 2026. Shortlisted teams should complete "
            "their SIH portal formalities before the national deadline."
        ),
        category="Hackathon",
        is_pinned=False,
        is_published=True,
    ),
    dict(
        title="Training & Placement - campus recruitment programme 2026-27",
        body=(
            "The Training & Placement Cell invites organisations to participate in the "
            "2026-27 campus recruitment programme for final-year diploma students. The cell "
            "supports pre-placement talks, group discussions, online and offline tests, and "
            "personal interviews. Write to coordinator-aei@rgipt.ac.in to schedule a visit."
        ),
        category="Notice",
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
