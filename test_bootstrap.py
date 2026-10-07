"""Regression test: the app must be usable from a completely empty database,
no matter which entry point started it (python app.py, flask run, gunicorn…).

It boots the app against a throwaway database, makes one request, and then
checks that the default admin account exists and can actually sign in.
"""
import os
import sys
import tempfile

# point at a fresh, empty database BEFORE importing the app
os.environ["DATABASE_URL"] = "sqlite:///" + os.path.join(tempfile.mkdtemp(), "fresh.db")
for mod in ("app", "models", "config", "seed"):
    sys.modules.pop(mod, None)

from app import app          # noqa: E402
from models import Admin     # noqa: E402


def main():
    client = app.test_client()

    # a single request should bootstrap tables + default admin
    r = client.get("/")
    assert r.status_code == 200, f"home page returned {r.status_code}"

    with app.app_context():
        count = Admin.query.count()
    assert count >= 1, "bootstrap did not create an admin account"
    print(f"admin accounts after bootstrap: {count}")

    # the default credentials must work
    with client.session_transaction() as s:
        s["_csrf"] = "testtoken"
    r = client.post(
        "/admin/login",
        data={"_csrf": "testtoken", "username": "admin", "password": "rgipt@2026"},
        follow_redirects=False,
    )
    assert r.status_code in (302, 303), f"login did not redirect ({r.status_code})"
    print("login redirect:", r.headers.get("Location"))

    r = client.get("/admin/")
    assert r.status_code == 200, f"dashboard returned {r.status_code}"

    # and the dashboard warns about the default password
    assert b"default password" in r.data, "missing default-password warning"
    print("dashboard warning present: yes")

    print("\nBOOTSTRAP TEST: PASS")


if __name__ == "__main__":
    main()
