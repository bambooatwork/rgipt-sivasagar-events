"""Convenience launcher — creates the database and (optionally) seeds it,
then starts the development server.

    python run.py
    PORT=5001 python run.py     # macOS: avoid the AirPlay port (5000)

If the requested port is already taken (on macOS, port 5000 is usually held by
AirPlay Receiver), the launcher automatically picks the next free port and tells
you which URL to open, instead of failing silently.
"""
import os
import socket

from app import app
from models import db, Event, Admin


def _port_free(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            s.bind(("0.0.0.0", port))
            return True
        except OSError:
            return False


def pick_port(preferred):
    if _port_free(preferred):
        return preferred
    for candidate in range(preferred + 1, preferred + 25):
        if _port_free(candidate):
            return candidate
    return preferred


with app.app_context():
    db.create_all()
    if Event.query.count() == 0 or Admin.query.count() == 0:
        print("First run detected \u2014 seeding the database\u2026")
        import seed
        seed.seed(reset=False)


if __name__ == "__main__":
    preferred = int(os.environ.get("PORT", 5000))
    port = pick_port(preferred)

    if port != preferred:
        print(f"\n  NOTE: port {preferred} is already in use, so the app will use {port}.")
        print("  On macOS, port 5000 is usually held by AirPlay Receiver.")
        print("  To free it: System Settings \u203a General \u203a AirDrop & Handoff \u203a AirPlay Receiver \u2192 Off")
        print(f"  Or just keep using: http://127.0.0.1:{port}")

    print("\n  RGIPT Sivasagar Campus \u2014 Event Management Portal")
    print(f"  Open in your browser:  http://127.0.0.1:{port}")
    print(f"  Admin panel:           http://127.0.0.1:{port}/admin/login  (admin / rgipt@2026)")
    print("  Press Ctrl+C to stop.\n")

    app.run(host="0.0.0.0", port=port, debug=True)
