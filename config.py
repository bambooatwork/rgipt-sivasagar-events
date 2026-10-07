import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))


class Config:
    """Application configuration.

    A secret key is required for session security. In production this MUST be
    supplied via the environment (SECRET_KEY). A random fallback is generated
    per-process so that the app still runs securely out of the box for a demo.
    """

    SECRET_KEY = os.environ.get("SECRET_KEY") or os.urandom(32)

    # SQLite database stored alongside the application.
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(BASE_DIR, "rgipt_events.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Session / cookie hardening
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = 60 * 60 * 8  # 8 hours

    # Upload / misc
    MAX_CONTENT_LENGTH = 4 * 1024 * 1024  # 4 MB request cap
