import csv
import io
import os
import re
import secrets
from datetime import date, datetime
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash,
    abort, Response, jsonify,
)
from sqlalchemy import or_, func

from config import Config
from models import db, Admin, Event, Registration, Announcement, ContactMessage

CAMPUS = {
    "name": "RGIPT Sivasagar Campus",
    "full_name": "Rajiv Gandhi Institute of Petroleum Technology, Sivasagar Campus",
    "address": "Gohain Gaon, Akhoiphutia, Dhaiali Road, Sivasagar \u2013 785697, Assam",
    "phone": "03772-295231",
    "email": "coordinator-aei@rgipt.ac.in",
    "established": 2016,
    "incharge": "Dr. Chinmoy Jit Sarma",
    "linkedin": "https://www.linkedin.com/rgiptsivasagarcampus",
}

DEPARTMENTS = [
    "Petroleum Engineering",
    "Chemical Engineering",
    "Mechanical Engineering",
    "Electrical Engineering",
    "Electronics & Instrumentation Engineering",
    "Fire & Safety Engineering",
    "Computer Science & Engineering",
    "Other",
]

CATEGORIES = ["Technical", "Cultural", "Sports", "Workshop", "Seminar", "Hackathon", "Entrepreneurship"]

ACCENTS = ["teal", "amber", "indigo", "rose", "emerald", "violet"]

# --------------------------------------------------------------------------- #
#  Faculty — compiled from the official RGIPT Sivasagar Campus faculty pages
#  (rgipt.ac.in). Institutional email addresses only; personal mobile numbers
#  published on the institute site are intentionally omitted here.
# --------------------------------------------------------------------------- #
FACULTY = [
    # --- campus leadership ---
    dict(group="leadership", name="Dr Chinmoy Jit Sarma", role="In-Charge, Sivasagar Campus",
         dept="Petroleum Engineering", focus="Petroleum Exploration & Production; Alternate Fuels",
         email="cjsarma@rgipt.ac.in"),
    dict(group="leadership", name="Dr Satyajit Chowdhury", role="Head, Department of Petroleum Engineering",
         dept="Petroleum Engineering", focus="Computational Fluid Dynamics; Machine Learning; Reservoir Engineering; Drilling Engineering",
         email="schowdhury@rgipt.ac.in"),
    dict(group="leadership", name="Dr Rajendra Kumar Mishra", role="Professor of Practice",
         dept="Petroleum Engineering", focus="Petroleum Engineering",
         email="rkmishra@rgipt.ac.in"),
    # --- faculty ---
    dict(group="faculty", name="Dr Abhimanyu Kar", role="Assistant Professor", dept="", focus="", email="akar@rgipt.ac.in"),
    dict(group="faculty", name="Ms Ananya Borah", role="Assistant Professor", dept="", focus="Behaviour Based Safety; Bioremediation", email="aborah@rgipt.ac.in"),
    dict(group="faculty", name="Dr Anil Kumar Varma", role="Assistant Professor", dept="", focus="Bioenergy (Biomass & Waste-Plastic Pyrolysis, Algal Bio-Oil); Wastewater Treatment; Separation Processes", email="anilv@rgipt.ac.in"),
    dict(group="faculty", name="Dr Arun Kumar", role="Assistant Professor", dept="", focus="Environmental Remediation; Advanced Oxidation Processes; Electrochemical Sensing; Energy Materials", email="arunk@rgipt.ac.in"),
    dict(group="faculty", name="Dr Bhagirath Sahu", role="Assistant Professor", dept="", focus="Microwave Filter & Antenna Design (Microstrip, SIW); Dielectric Resonator Antennas; Metamaterials", email="bhagirath.sahu@rgipt.ac.in"),
    dict(group="faculty", name="Dr Bhaskar Jyoti Medhi", role="Assistant Professor", dept="", focus="Experimental & Computational Fluid Dynamics; Microfluidics; Complex Fluids", email="bmedhi@rgipt.ac.in"),
    dict(group="faculty", name="Dr Bhaskor Jyoti Bora", role="Assistant Professor", dept="", focus="Internal Combustion Engines", email="bjbora@rgipt.ac.in"),
    dict(group="faculty", name="Dr Chinmayee Hazarika", role="Assistant Professor", dept="", focus="Bio-electronic Devices; MEMS-based Sensors", email="chazarika@rgipt.ac.in"),
    dict(group="faculty", name="Dr Debasis De", role="Assistant Professor", dept="", focus="Fabrication of Solar Cells", email="debasisd@rgipt.ac.in"),
    dict(group="faculty", name="Dr Karthik Babu NB", role="Assistant Professor", dept="", focus="Polymer Nanocomposites", email="kbabu@rgipt.ac.in"),
    dict(group="faculty", name="Dr M Chakkarapani", role="Assistant Professor", dept="Electrical & Electronics Engineering", focus="Control Systems; Power Electronics & Renewable Energy Systems", email="mchakkarapani@rgipt.ac.in"),
    dict(group="faculty", name="Dr Nilambar Bariha", role="Assistant Professor", dept="Fire & Safety Engineering", focus="Industrial Safety & Hazards Management", email="nbariha@rgipt.ac.in"),
    dict(group="faculty", name="Dr Nimisha Raghuvanshi", role="Assistant Professor", dept="", focus="Twisted Bilayer Graphene & Correlated States; Magnetism in Iron-based Superconductors", email="nraghuvanshi@rgipt.ac.in"),
    dict(group="faculty", name="Dr Rupjit Saikia", role="Assistant Professor", dept="", focus="Fuzzy Set Theory; Uncertainty Modelling; Decision Making", email="rsaikia@rgipt.ac.in"),
    dict(group="faculty", name="Dr Sabyasachi Pramanik", role="Assistant Professor", dept="", focus="Nanoscience; Semiconductor Nanocrystals (Quantum Dots); Sensing & Energy Applications", email="spramanik@rgipt.ac.in"),
    dict(group="faculty", name="Dr Sanat Kumar Singha", role="Assistant Professor", dept="", focus="Phase Transitions; Interfacial Phenomena; Non-Equilibrium Thermodynamics", email="sksingha@rgipt.ac.in"),
    dict(group="faculty", name="Dr Santosh Kumar Verma", role="Assistant Professor", dept="", focus="Fractional-Order PID Control Design & Optimisation", email="skverma@rgipt.ac.in"),
    dict(group="faculty", name="Dr Satish Kumar Tiwari", role="Assistant Professor", dept="", focus="Mathematical Ecology; Mathematical Modelling; Differential Equations", email="stiwari@rgipt.ac.in"),
    dict(group="faculty", name="Dr Sekhar Gogoi", role="Assistant Professor", dept="Petroleum Engineering", focus="Petroleum Technology; Enhanced Oil Recovery; Microfluidics; Well Logging", email="sgogoi@rgipt.ac.in"),
    dict(group="faculty", name="Dr Shikha Dwivedi", role="Assistant Professor", dept="", focus="Computational Soft Matter Physics; Complex Systems; Statistical Mechanics", email="sdwivedi@rgipt.ac.in"),
    dict(group="faculty", name="Dr Souvik De", role="Assistant Professor", dept="", focus="Polyelectrolyte Complexes & Multilayers; Functional Coatings & Thin Films", email="sde@rgipt.ac.in"),
    dict(group="faculty", name="Dr Srawanti Medhi", role="Assistant Professor", dept="Petroleum Engineering", focus="Computational Fluid Dynamics; Rheology of Complex Fluids; Drilling & Fracturing Fluids", email="smedhi@rgipt.ac.in"),
]


def slugify(text):
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "event"


def make_ticket_code():
    return "RGI" + secrets.token_hex(3).upper()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)

    # ------------------------------------------------------------------ #
    # Security: lightweight CSRF protection for every state-changing POST
    # ------------------------------------------------------------------ #
    def csrf_token():
        if "_csrf" not in session:
            session["_csrf"] = secrets.token_hex(16)
        return session["_csrf"]

    @app.before_request
    def _csrf_protect():
        if request.method == "POST":
            token = session.get("_csrf")
            sent = request.form.get("_csrf") or request.headers.get("X-CSRF-Token")
            if not token or not sent or not secrets.compare_digest(token, sent):
                abort(400, description="CSRF validation failed. Please reload and try again.")

    # ------------------------------------------------------------------ #
    # Auth helpers
    # ------------------------------------------------------------------ #
    def login_required(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if not session.get("admin_id"):
                flash("Please sign in to access the admin panel.", "warning")
                return redirect(url_for("admin_login", next=request.path))
            return view(*args, **kwargs)
        return wrapped

    def current_admin():
        aid = session.get("admin_id")
        return db.session.get(Admin, aid) if aid else None

    # ------------------------------------------------------------------ #
    # Template globals
    # ------------------------------------------------------------------ #
    @app.context_processor
    def inject_globals():
        return {
            "csrf_token": csrf_token,
            "campus": CAMPUS,
            "departments": DEPARTMENTS,
            "categories": CATEGORIES,
            "accents": ACCENTS,
            "now": datetime.utcnow(),
            "current_admin": current_admin(),
        }

    @app.template_filter("datefmt")
    def datefmt(value, fmt="%d %b %Y"):
        if not value:
            return ""
        if isinstance(value, datetime):
            return value.strftime(fmt)
        if isinstance(value, date):
            return value.strftime(fmt)
        return value

    @app.template_filter("inr")
    def inr(value):
        try:
            value = int(value)
        except (TypeError, ValueError):
            return value
        if value == 0:
            return "Free"
        return "\u20b9" + f"{value:,}"

    # ================================================================== #
    #  PUBLIC SITE
    # ================================================================== #
    @app.route("/")
    def home():
        featured = (
            Event.query.filter_by(is_published=True, is_featured=True)
            .filter((Event.end_date == None) | (Event.end_date >= date.today()))
            .order_by(Event.event_date.asc())
            .limit(3)
            .all()
        )
        if not featured:
            featured = (
                Event.query.filter_by(is_published=True)
                .filter(Event.event_date >= date.today())
                .order_by(Event.event_date.asc())
                .limit(3)
                .all()
            )
        upcoming = (
            Event.query.filter_by(is_published=True)
            .filter(Event.event_date >= date.today())
            .order_by(Event.event_date.asc())
            .all()
        )
        past = (
            Event.query.filter_by(is_published=True)
            .filter(Event.event_date < date.today())
            .order_by(Event.event_date.desc())
            .limit(3)
            .all()
        )
        announcements = (
            Announcement.query.filter_by(is_published=True)
            .order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc())
            .limit(4)
            .all()
        )
        stats = {
            "events": Event.query.filter_by(is_published=True).count(),
            "upcoming": len(upcoming),
            "registrations": Registration.query.filter(Registration.status != "cancelled").count(),
            "departments": len(DEPARTMENTS) - 1,
        }
        return render_template(
            "index.html",
            featured=featured,
            upcoming=upcoming,
            past=past,
            announcements=announcements,
            stats=stats,
        )

    @app.route("/events")
    def events():
        q = request.args.get("q", "").strip()
        category = request.args.get("category", "").strip()
        status = request.args.get("status", "upcoming").strip()
        department = request.args.get("department", "").strip()

        query = Event.query.filter_by(is_published=True)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(
                Event.title.ilike(like),
                Event.short_description.ilike(like),
                Event.description.ilike(like),
                Event.organizer.ilike(like),
                Event.venue.ilike(like),
            ))
        if category:
            query = query.filter(Event.category == category)
        if department:
            query = query.filter(Event.organizer.ilike(f"%{department}%"))

        if status == "upcoming":
            query = query.filter(Event.event_date >= date.today()).order_by(Event.event_date.asc())
        elif status == "past":
            query = query.filter(Event.event_date < date.today()).order_by(Event.event_date.desc())
        else:
            query = query.order_by(Event.event_date.desc())

        all_events = query.all()
        return render_template(
            "events.html",
            events=all_events,
            q=q,
            category=category,
            status=status,
            department=department,
        )

    @app.route("/events/<slug>")
    def event_detail(slug):
        event = Event.query.filter_by(slug=slug, is_published=True).first_or_404()
        related = (
            Event.query.filter_by(is_published=True, category=event.category)
            .filter(Event.id != event.id)
            .order_by(Event.event_date.asc())
            .limit(3)
            .all()
        )
        return render_template("event_detail.html", event=event, related=related)

    @app.route("/events/<slug>/register", methods=["GET", "POST"])
    def register_event(slug):
        event = Event.query.filter_by(slug=slug, is_published=True).first_or_404()

        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            phone = request.form.get("phone", "").strip()
            college = request.form.get("college", "").strip() or CAMPUS["name"]
            department = request.form.get("department", "").strip()
            year = request.form.get("year", "").strip()
            team_name = request.form.get("team_name", "").strip()
            notes = request.form.get("notes", "").strip()

            errors = []
            if not name:
                errors.append("Your full name is required.")
            if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                errors.append("A valid email address is required.")
            if not event.registration_open:
                errors.append("Registration for this event is currently closed.")

            existing = Registration.query.filter_by(event_id=event.id, email=email).first() if email else None
            if existing and existing.status != "cancelled":
                errors.append("This email is already registered for this event.")

            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template("register_event.html", event=event, form=request.form)

            status = "confirmed" if event.seats_left > 0 else "waitlist"
            reg = Registration(
                event_id=event.id,
                name=name,
                email=email,
                phone=phone,
                college=college,
                department=department,
                year=year,
                team_name=team_name,
                notes=notes,
                status=status,
                ticket_code=make_ticket_code(),
            )
            db.session.add(reg)
            db.session.commit()
            return redirect(url_for("registration_success", ticket_code=reg.ticket_code))

        return render_template("register_event.html", event=event, form={})

    @app.route("/registration/<ticket_code>")
    def registration_success(ticket_code):
        reg = Registration.query.filter_by(ticket_code=ticket_code).first_or_404()
        return render_template("registration_success.html", reg=reg)

    @app.route("/announcements")
    def announcements():
        items = (
            Announcement.query.filter_by(is_published=True)
            .order_by(Announcement.is_pinned.desc(), Announcement.published_at.desc())
            .all()
        )
        return render_template("announcements.html", announcements=items)

    @app.route("/announcements/<int:aid>")
    def announcement_detail(aid):
        item = Announcement.query.filter_by(id=aid, is_published=True).first_or_404()
        others = (
            Announcement.query.filter_by(is_published=True)
            .filter(Announcement.id != aid)
            .order_by(Announcement.published_at.desc())
            .limit(5)
            .all()
        )
        return render_template("announcement_detail.html", item=item, others=others)

    @app.route("/my-registrations", methods=["GET", "POST"])
    def my_registrations():
        regs = []
        searched_email = ""
        if request.method == "POST":
            searched_email = request.form.get("email", "").strip().lower()
            if searched_email:
                regs = (
                    Registration.query.filter_by(email=searched_email)
                    .order_by(Registration.registered_at.desc())
                    .all()
                )
                if not regs:
                    flash("No registrations found for that email address.", "info")
        return render_template("my_registrations.html", regs=regs, searched_email=searched_email)

    @app.route("/faculty")
    def faculty():
        leadership = [f for f in FACULTY if f["group"] == "leadership"]
        members = [f for f in FACULTY if f["group"] == "faculty"]
        return render_template("faculty.html", leadership=leadership, members=members)

    @app.route("/about")
    def about():
        stats = {
            "events": Event.query.filter_by(is_published=True).count(),
            "registrations": Registration.query.filter(Registration.status != "cancelled").count(),
        }
        return render_template("about.html", stats=stats)

    @app.route("/contact", methods=["GET", "POST"])
    def contact():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip().lower()
            subject = request.form.get("subject", "").strip()
            message = request.form.get("message", "").strip()

            if not name or not email or not message:
                flash("Name, email and message are required.", "error")
            elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                flash("Please enter a valid email address.", "error")
            else:
                db.session.add(ContactMessage(
                    name=name, email=email, subject=subject or "General enquiry", message=message,
                ))
                db.session.commit()
                flash("Thanks! Your message has been sent to the campus team.", "success")
                return redirect(url_for("contact"))
        return render_template("contact.html")

    # ================================================================== #
    #  ADMIN PANEL
    # ================================================================== #
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if session.get("admin_id"):
            return redirect(url_for("admin_dashboard"))
        if request.method == "POST":
            username = request.form.get("username", "").strip()
            password = request.form.get("password", "")
            admin = Admin.query.filter_by(username=username).first()
            if admin and admin.check_password(password):
                session.clear()
                session["admin_id"] = admin.id
                session["_csrf"] = secrets.token_hex(16)
                session.permanent = True
                flash(f"Welcome back, {admin.full_name}.", "success")
                nxt = request.args.get("next")
                if nxt and nxt.startswith("/admin"):
                    return redirect(nxt)
                return redirect(url_for("admin_dashboard"))
            flash("Invalid username or password.", "error")
        return render_template("admin/login.html")

    @app.route("/admin/logout")
    def admin_logout():
        session.clear()
        flash("You have been signed out.", "info")
        return redirect(url_for("home"))

    @app.route("/admin/")
    @login_required
    def admin_dashboard():
        total_events = Event.query.count()
        published_events = Event.query.filter_by(is_published=True).count()
        upcoming = Event.query.filter(Event.event_date >= date.today()).count()
        total_regs = Registration.query.filter(Registration.status != "cancelled").count()
        waitlist = Registration.query.filter_by(status="waitlist").count()
        unread = ContactMessage.query.filter_by(is_read=False).count()
        drafts = Announcement.query.filter_by(is_published=False).count()

        # registrations per category
        per_cat = (
            db.session.query(Event.category, func.count(Registration.id))
            .join(Registration, Registration.event_id == Event.id)
            .filter(Registration.status != "cancelled")
            .group_by(Event.category)
            .all()
        )
        top_events = (
            db.session.query(Event, func.count(Registration.id).label("cnt"))
            .outerjoin(Registration, (Registration.event_id == Event.id) & (Registration.status != "cancelled"))
            .group_by(Event.id)
            .order_by(func.count(Registration.id).desc())
            .limit(5)
            .all()
        )
        recent_regs = Registration.query.order_by(Registration.registered_at.desc()).limit(6).all()
        recent_msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).limit(5).all()

        return render_template(
            "admin/dashboard.html",
            stats={
                "total_events": total_events,
                "published_events": published_events,
                "upcoming": upcoming,
                "total_regs": total_regs,
                "waitlist": waitlist,
                "unread": unread,
                "drafts": drafts,
            },
            per_cat=per_cat,
            top_events=top_events,
            recent_regs=recent_regs,
            recent_msgs=recent_msgs,
            using_default_password=current_admin().check_password("rgipt@2026"),
        )

    # ---------------------------- Events CRUD ------------------------- #
    @app.route("/admin/events")
    @login_required
    def admin_events():
        events = Event.query.order_by(Event.event_date.desc()).all()
        return render_template("admin/events.html", events=events)

    @app.route("/admin/events/new", methods=["GET", "POST"])
    @login_required
    def admin_event_new():
        if request.method == "POST":
            event, errors = _event_from_form(None)
            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template("admin/event_form.html", event=None, form=request.form)
            db.session.add(event)
            db.session.commit()
            flash(f"Event \u201c{event.title}\u201d created.", "success")
            return redirect(url_for("admin_events"))
        return render_template("admin/event_form.html", event=None, form={})

    @app.route("/admin/events/<int:eid>/edit", methods=["GET", "POST"])
    @login_required
    def admin_event_edit(eid):
        event = db.session.get(Event, eid) or abort(404)
        if request.method == "POST":
            _, errors = _event_from_form(event)
            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template("admin/event_form.html", event=event, form=request.form)
            db.session.commit()
            flash(f"Event \u201c{event.title}\u201d updated.", "success")
            return redirect(url_for("admin_events"))
        return render_template("admin/event_form.html", event=event, form={})

    def _event_from_form(event):
        errors = []
        title = request.form.get("title", "").strip()
        if not title:
            errors.append("Title is required.")

        raw_date = request.form.get("event_date", "").strip()
        try:
            event_date = datetime.strptime(raw_date, "%Y-%m-%d").date() if raw_date else None
        except ValueError:
            event_date = None
        if not event_date:
            errors.append("A valid event date is required.")

        end_date = None
        raw_end = request.form.get("end_date", "").strip()
        if raw_end:
            try:
                end_date = datetime.strptime(raw_end, "%Y-%m-%d").date()
            except ValueError:
                errors.append("End date is not a valid date.")

        deadline = None
        raw_dl = request.form.get("registration_deadline", "").strip()
        if raw_dl:
            try:
                deadline = datetime.strptime(raw_dl, "%Y-%m-%d").date()
            except ValueError:
                errors.append("Registration deadline is not a valid date.")

        try:
            capacity = int(request.form.get("capacity") or 0)
        except ValueError:
            capacity = 0
            errors.append("Capacity must be a number.")
        try:
            fee = int(request.form.get("fee") or 0)
        except ValueError:
            fee = 0
            errors.append("Fee must be a number.")

        if errors:
            return None, errors

        if event is None:
            event = Event()
            base_slug = slugify(title)
            slug = base_slug
            i = 2
            while Event.query.filter_by(slug=slug).first():
                slug = f"{base_slug}-{i}"
                i += 1
            event.slug = slug

        event.title = title
        event.category = request.form.get("category", "Technical")
        event.short_description = request.form.get("short_description", "").strip()[:300]
        event.description = request.form.get("description", "").strip()
        event.organizer = request.form.get("organizer", "").strip() or CAMPUS["name"]
        event.venue = request.form.get("venue", "").strip() or "RGIPT Sivasagar Campus, Gohain Gaon"
        event.event_date = event_date
        event.end_date = end_date
        event.start_time = request.form.get("start_time", "10:00 AM").strip()
        event.end_time = request.form.get("end_time", "05:00 PM").strip()
        event.registration_deadline = deadline
        event.capacity = capacity
        event.fee = fee
        event.team_size = request.form.get("team_size", "Individual").strip()
        event.contact_email = request.form.get("contact_email", CAMPUS["email"]).strip()
        event.accent = request.form.get("accent", "teal")
        event.is_featured = bool(request.form.get("is_featured"))
        event.is_published = bool(request.form.get("is_published"))
        return event, []

    @app.route("/admin/events/<int:eid>/delete", methods=["POST"])
    @login_required
    def admin_event_delete(eid):
        event = db.session.get(Event, eid) or abort(404)
        title = event.title
        db.session.delete(event)
        db.session.commit()
        flash(f"Event \u201c{title}\u201d and its registrations were deleted.", "info")
        return redirect(url_for("admin_events"))

    @app.route("/admin/events/<int:eid>/toggle", methods=["POST"])
    @login_required
    def admin_event_toggle(eid):
        event = db.session.get(Event, eid) or abort(404)
        event.is_published = not event.is_published
        db.session.commit()
        flash(
            f"\u201c{event.title}\u201d is now {'published' if event.is_published else 'hidden'}.",
            "success",
        )
        return redirect(request.referrer or url_for("admin_events"))

    # ------------------------ Registrations --------------------------- #
    @app.route("/admin/registrations")
    @login_required
    def admin_registrations():
        eid = request.args.get("event_id", type=int)
        status = request.args.get("status", "").strip()
        q = request.args.get("q", "").strip()

        query = Registration.query.join(Event)
        if eid:
            query = query.filter(Registration.event_id == eid)
        if status:
            query = query.filter(Registration.status == status)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(
                Registration.name.ilike(like),
                Registration.email.ilike(like),
                Registration.college.ilike(like),
                Registration.department.ilike(like),
                Registration.ticket_code.ilike(like),
            ))
        regs = query.order_by(Registration.registered_at.desc()).all()
        all_events = Event.query.order_by(Event.event_date.desc()).all()
        return render_template(
            "admin/registrations.html",
            regs=regs, all_events=all_events, eid=eid, status=status, q=q,
        )

    @app.route("/admin/registrations/export.csv")
    @login_required
    def admin_registrations_export():
        eid = request.args.get("event_id", type=int)
        status = request.args.get("status", "").strip()
        q = request.args.get("q", "").strip()

        query = Registration.query.join(Event)
        if eid:
            query = query.filter(Registration.event_id == eid)
        if status:
            query = query.filter(Registration.status == status)
        if q:
            like = f"%{q}%"
            query = query.filter(or_(
                Registration.name.ilike(like), Registration.email.ilike(like),
                Registration.college.ilike(like), Registration.ticket_code.ilike(like),
            ))
        regs = query.order_by(Registration.registered_at.desc()).all()

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow([
            "Ticket", "Event", "Event Date", "Name", "Email", "Phone",
            "College", "Department", "Year", "Team", "Status", "Registered At",
        ])
        for r in regs:
            writer.writerow([
                r.ticket_code, r.event.title, r.event.event_date.strftime("%Y-%m-%d"),
                r.name, r.email, r.phone or "", r.college or "", r.department or "",
                r.year or "", r.team_name or "", r.status,
                r.registered_at.strftime("%Y-%m-%d %H:%M"),
            ])
        fname = f"registrations_{datetime.utcnow().strftime('%Y%m%d_%H%M')}.csv"
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment; filename={fname}"},
        )

    @app.route("/admin/registrations/<int:rid>/status", methods=["POST"])
    @login_required
    def admin_registration_status(rid):
        reg = db.session.get(Registration, rid) or abort(404)
        new_status = request.form.get("status", "")
        if new_status in ("confirmed", "waitlist", "cancelled"):
            reg.status = new_status
            db.session.commit()
            flash(f"Registration for {reg.name} set to {new_status}.", "success")
        return redirect(request.referrer or url_for("admin_registrations"))

    @app.route("/admin/registrations/<int:rid>/delete", methods=["POST"])
    @login_required
    def admin_registration_delete(rid):
        reg = db.session.get(Registration, rid) or abort(404)
        db.session.delete(reg)
        db.session.commit()
        flash("Registration deleted.", "info")
        return redirect(request.referrer or url_for("admin_registrations"))

    # -------------------------- Announcements ------------------------- #
    @app.route("/admin/announcements")
    @login_required
    def admin_announcements():
        items = Announcement.query.order_by(Announcement.created_at.desc()).all()
        return render_template("admin/announcements.html", announcements=items)

    @app.route("/admin/announcements/new", methods=["GET", "POST"])
    @login_required
    def admin_announcement_new():
        if request.method == "POST":
            a, errors = _announcement_from_form(None)
            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template("admin/announcement_form.html", item=None, form=request.form)
            db.session.add(a)
            db.session.commit()
            flash("Announcement created.", "success")
            return redirect(url_for("admin_announcements"))
        return render_template("admin/announcement_form.html", item=None, form={})

    @app.route("/admin/announcements/<int:aid>/edit", methods=["GET", "POST"])
    @login_required
    def admin_announcement_edit(aid):
        item = db.session.get(Announcement, aid) or abort(404)
        if request.method == "POST":
            _, errors = _announcement_from_form(item)
            if errors:
                for e in errors:
                    flash(e, "error")
                return render_template("admin/announcement_form.html", item=item, form=request.form)
            db.session.commit()
            flash("Announcement updated.", "success")
            return redirect(url_for("admin_announcements"))
        return render_template("admin/announcement_form.html", item=item, form={})

    def _announcement_from_form(item):
        errors = []
        title = request.form.get("title", "").strip()
        body = request.form.get("body", "").strip()
        if not title:
            errors.append("Title is required.")
        if not body:
            errors.append("Body is required.")
        if errors:
            return None, errors
        if item is None:
            item = Announcement()
        item.title = title
        item.body = body
        item.category = request.form.get("category", "General").strip() or "General"
        item.is_pinned = bool(request.form.get("is_pinned"))
        item.is_published = bool(request.form.get("is_published"))
        if item.is_published and not item.published_at:
            item.published_at = datetime.utcnow()
        elif item.is_published:
            item.published_at = datetime.utcnow()
        return item, []

    @app.route("/admin/announcements/<int:aid>/toggle", methods=["POST"])
    @login_required
    def admin_announcement_toggle(aid):
        item = db.session.get(Announcement, aid) or abort(404)
        item.is_published = not item.is_published
        if item.is_published:
            item.published_at = datetime.utcnow()
        db.session.commit()
        flash(
            f"Announcement is now {'published' if item.is_published else 'a draft'}.",
            "success",
        )
        return redirect(url_for("admin_announcements"))

    @app.route("/admin/announcements/<int:aid>/delete", methods=["POST"])
    @login_required
    def admin_announcement_delete(aid):
        item = db.session.get(Announcement, aid) or abort(404)
        db.session.delete(item)
        db.session.commit()
        flash("Announcement deleted.", "info")
        return redirect(url_for("admin_announcements"))

    # ---------------------------- Messages ---------------------------- #
    @app.route("/admin/messages")
    @login_required
    def admin_messages():
        msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
        return render_template("admin/messages.html", messages=msgs)

    @app.route("/admin/messages/<int:mid>/read", methods=["POST"])
    @login_required
    def admin_message_read(mid):
        m = db.session.get(ContactMessage, mid) or abort(404)
        m.is_read = not m.is_read
        db.session.commit()
        return redirect(request.referrer or url_for("admin_messages"))

    @app.route("/admin/messages/<int:mid>/delete", methods=["POST"])
    @login_required
    def admin_message_delete(mid):
        m = db.session.get(ContactMessage, mid) or abort(404)
        db.session.delete(m)
        db.session.commit()
        flash("Message deleted.", "info")
        return redirect(url_for("admin_messages"))

    # ------------------------- Admin settings ------------------------- #
    @app.route("/admin/settings", methods=["GET", "POST"])
    @login_required
    def admin_settings():
        admin = current_admin()
        if request.method == "POST":
            new_pass = request.form.get("new_password", "")
            confirm = request.form.get("confirm_password", "")
            current = request.form.get("current_password", "")
            if not admin.check_password(current):
                flash("Your current password is incorrect.", "error")
            elif len(new_pass) < 6:
                flash("New password must be at least 6 characters.", "error")
            elif new_pass != confirm:
                flash("New passwords do not match.", "error")
            else:
                admin.set_password(new_pass)
                db.session.commit()
                flash("Password updated successfully.", "success")
            return redirect(url_for("admin_settings"))
        return render_template("admin/settings.html")

    # ---------------------------- Error pages ------------------------- #
    @app.errorhandler(404)
    def not_found(e):
        return render_template("404.html"), 404

    @app.errorhandler(400)
    def bad_request(e):
        return render_template("400.html", message=getattr(e, "description", "Bad request")), 400

    @app.errorhandler(500)
    def server_error(e):
        db.session.rollback()
        return render_template("500.html"), 500

    # ------------------------------------------------------------------ #
    # Bootstrap: make the app usable from ANY entry point (python app.py,
    # flask run, gunicorn, a PaaS start command). On the first request the
    # tables are created and, if the database is empty, the default admin
    # account and starter content are seeded.
    # ------------------------------------------------------------------ #
    _bootstrapped = {"done": False}

    @app.before_request
    def _bootstrap_database():
        if _bootstrapped["done"]:
            return
        _bootstrapped["done"] = True
        try:
            db.create_all()
            if Admin.query.count() == 0 or Event.query.count() == 0:
                import seed as _seed
                _seed.seed(reset=False)
        except Exception:
            db.session.rollback()

    return app


app = create_app()


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
