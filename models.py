from datetime import datetime, date

from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(db.Model):
    __tablename__ = "admins"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), default="Administrator")
    role = db.Column(db.String(32), default="admin")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, raw):
        self.password_hash = generate_password_hash(raw)

    def check_password(self, raw):
        return check_password_hash(self.password_hash, raw)

    def __repr__(self):
        return f"<Admin {self.username}>"


class Event(db.Model):
    __tablename__ = "events"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(180), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    category = db.Column(db.String(60), default="Technical")
    short_description = db.Column(db.String(300))
    description = db.Column(db.Text)
    organizer = db.Column(db.String(160), default="RGIPT Sivasagar Campus")
    venue = db.Column(db.String(180), default="RGIPT Sivasagar Campus, Gohain Gaon")
    event_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date)
    start_time = db.Column(db.String(20), default="10:00 AM")
    end_time = db.Column(db.String(20), default="05:00 PM")
    registration_deadline = db.Column(db.Date)
    capacity = db.Column(db.Integer, default=100)
    fee = db.Column(db.Integer, default=0)  # in INR; 0 == free
    team_size = db.Column(db.String(40), default="Individual")
    contact_email = db.Column(db.String(120), default="coordinator-aei@rgipt.ac.in")
    accent = db.Column(db.String(20), default="teal")  # colour token for the card
    is_featured = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    registrations = db.relationship(
        "Registration",
        backref="event",
        cascade="all, delete-orphan",
        lazy="dynamic",
    )

    @property
    def is_past(self):
        d = self.end_date or self.event_date
        return d < date.today()

    @property
    def is_upcoming(self):
        return not self.is_past

    @property
    def seats_taken(self):
        return self.registrations.filter(
            Registration.status != "cancelled"
        ).count()

    @property
    def seats_left(self):
        return max((self.capacity or 0) - self.seats_taken, 0)

    @property
    def is_full(self):
        return self.seats_left <= 0

    @property
    def registration_open(self):
        if self.is_past:
            return False
        if self.registration_deadline and self.registration_deadline < date.today():
            return False
        return not self.is_full

    def __repr__(self):
        return f"<Event {self.title}>"


class Registration(db.Model):
    __tablename__ = "registrations"

    id = db.Column(db.Integer, primary_key=True)
    event_id = db.Column(db.Integer, db.ForeignKey("events.id"), nullable=False)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False, index=True)
    phone = db.Column(db.String(30))
    college = db.Column(db.String(180), default="RGIPT Sivasagar Campus")
    department = db.Column(db.String(120))
    year = db.Column(db.String(40))
    team_name = db.Column(db.String(120))
    notes = db.Column(db.Text)
    status = db.Column(db.String(20), default="confirmed")  # confirmed/waitlist/cancelled
    ticket_code = db.Column(db.String(20), unique=True)
    registered_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Registration {self.name} -> {self.event_id}>"


class Announcement(db.Model):
    __tablename__ = "announcements"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    body = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(60), default="General")
    is_pinned = db.Column(db.Boolean, default=False)
    is_published = db.Column(db.Boolean, default=True)
    published_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<Announcement {self.title}>"


class ContactMessage(db.Model):
    __tablename__ = "contact_messages"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    subject = db.Column(db.String(200))
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ContactMessage {self.subject}>"
