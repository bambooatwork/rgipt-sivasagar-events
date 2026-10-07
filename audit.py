"""Browser-level audit via Chrome DevTools Protocol.

Checks every page for JS/console errors, horizontal overflow and missing
elements, and drives real interactions (theme toggle, mobile nav, event
filter, admin login) to prove the UI works end to end.
"""
import json
import subprocess
import threading
import time
import urllib.request
import tempfile

from werkzeug.serving import make_server
import websocket

from app import app
from models import Event
from datetime import date

PORT = 5063
BASE = f"http://127.0.0.1:{PORT}"
DBG = 9377

server = make_server("127.0.0.1", PORT, app)
threading.Thread(target=server.serve_forever, daemon=True).start()
time.sleep(1.5)

with app.app_context():
    slug = Event.query.filter(Event.event_date >= date.today()).first().slug

prof = tempfile.mkdtemp()
chrome = subprocess.Popen(
    ["google-chrome-stable", "--headless=new", "--no-sandbox", "--disable-gpu",
     f"--remote-debugging-port={DBG}", "--remote-allow-origins=*",
     f"--user-data-dir={prof}", "--window-size=1440,1000", "about:blank"],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(4)
tgt = json.load(urllib.request.urlopen(f"http://127.0.0.1:{DBG}/json"))
page = [t for t in tgt if t["type"] == "page"][0]
ws = websocket.create_connection(page["webSocketDebuggerUrl"], max_size=None)

_id = [0]
_events = []


def cmd(method, params=None):
    _id[0] += 1
    ws.send(json.dumps({"id": _id[0], "method": method, "params": params or {}}))
    while True:
        r = json.loads(ws.recv())
        if r.get("id") == _id[0]:
            return r
        _events.append(r)


def ev(expr):
    r = cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True})
    return r.get("result", {}).get("result", {}).get("value")


def goto(path, wait=1.6):
    _events.clear()
    cmd("Page.navigate", {"url": BASE + path})
    for _ in range(40):
        time.sleep(0.25)
        if ev("document.readyState") == "complete":
            break
    time.sleep(wait)


def console_errors():
    errs = []
    for e in _events:
        m = e.get("method")
        if m == "Runtime.exceptionThrown":
            errs.append("EXC: " + str(e["params"]["exceptionDetails"].get("text")))
        if m == "Log.entryAdded":
            entry = e["params"]["entry"]
            if entry.get("level") in ("error",) and "favicon" not in entry.get("text", ""):
                errs.append("LOG: " + entry.get("text", ""))
    return errs


PASS, FAIL = [], []


def ok(label, cond, extra=""):
    (PASS if cond else FAIL).append(label + ("" if cond else f" {extra}"))


cmd("Page.enable")
cmd("Runtime.enable")
cmd("Log.enable")

PAGES = [
    ("/", "home", [".hero", ".grid-3 .event-card", ".stat-row", ".footer"]),
    ("/events", "events", [".filter-bar", ".grid-3 .event-card"]),
    (f"/events/{slug}", "event detail", [".detail-hero", ".info-card", ".timeline", ".countdown"]),
    ("/announcements", "announcements", [".announce"]),
    ("/announcements/1", "announcement detail", [".prose"]),
    ("/my-registrations", "my registrations", ["form"]),
    ("/faculty", "faculty", [".grid-3", "[data-filter-input]", "[data-filter-item]"]),
    ("/about", "about", [".hero", ".panel"]),
    ("/contact", "contact", ["form textarea", ".meta-list"]),
    ("/admin/login", "admin login", ["form input[name=username]"]),
    ("/nope-404", "404 page", ["body"]),
]

for path, name, sels in PAGES:
    goto(path)
    errs = console_errors()
    if "404" not in name:  # a 404 page legitimately logs a 404 resource error
        ok(f"{name}: no console/JS errors", not errs, str(errs[:2]))
    over = ev("document.documentElement.scrollWidth - window.innerWidth")
    ok(f"{name}: no horizontal overflow", (over or 0) <= 2, f"overflow={over}px")
    for sel in sels:
        ok(f"{name}: element {sel}", ev(f"!!document.querySelector('{sel}')"))
    ok(f"{name}: has title", bool(ev("document.title")))

# ---------------- interaction: theme toggle ---------------- #
goto("/")
before = ev("document.documentElement.getAttribute('data-theme')")
ev("document.querySelector('[data-theme-toggle]').click()")
after = ev("document.documentElement.getAttribute('data-theme')")
ok("theme toggle switches theme", before != after, f"{before}->{after}")
ev("document.querySelector('[data-theme-toggle]').click()")

# ---------------- interaction: event filter ---------------- #
goto("/events")
ev("(()=>{const f=document.querySelector('.filter-bar');f.querySelector('[name=q]').value='urjotsav';f.submit();})()")
time.sleep(1.8)
ok("event search filters results", ev("document.body.innerText.includes('Urjotsav')"))
ok("event search shows count", "found" in ev("document.body.innerText").lower())

# ---------------- interaction: countdown ticking ---------------- #
goto(f"/events/{slug}")
c1 = ev("document.querySelector('.countdown') && document.querySelector('.countdown').innerText")
time.sleep(1.4)
c2 = ev("document.querySelector('.countdown') && document.querySelector('.countdown').innerText")
ok("countdown renders", bool(c1))
ok("countdown ticks", c1 != c2, f"{c1!r} vs {c2!r}")

# ---------------- interaction: mobile nav ---------------- #
cmd("Emulation.setDeviceMetricsOverride", {"width": 390, "height": 844, "deviceScaleFactor": 2, "mobile": True})
goto("/")
ok("mobile: nav toggle visible", ev("getComputedStyle(document.querySelector('.nav-toggle')).display") != "none")
ev("document.querySelector('.nav-toggle').click()")
ok("mobile: nav opens", ev("document.querySelector('.nav-links').classList.contains('open')"))
over = ev("document.documentElement.scrollWidth - window.innerWidth")
ok("mobile home: no overflow", (over or 0) <= 2, f"overflow={over}px")
goto("/events")
over = ev("document.documentElement.scrollWidth - window.innerWidth")
ok("mobile events: no overflow", (over or 0) <= 2, f"overflow={over}px")
cmd("Emulation.clearDeviceMetricsOverride")

# ---------------- interaction: admin login + dashboard ---------------- #
goto("/admin/login")
ev("(()=>{const f=document.querySelector('form');f.querySelector('[name=username]').value='admin';f.querySelector('[name=password]').value='rgipt@2026';f.submit();})()")
time.sleep(2.2)
ok("admin login lands on dashboard", "/admin/" in (ev("location.pathname") or ""), ev("location.pathname"))
ok("dashboard shows KPIs", ev("document.querySelectorAll('.kpi').length") >= 4)
goto("/admin/events")
ok("admin events table renders", ev("document.querySelectorAll('table tbody tr').length") >= 5)
goto("/admin/registrations")
ok("admin registrations render", ev("document.querySelectorAll('table tbody tr').length") >= 1)
goto("/admin/announcements")
ok("admin announcements render", ev("document.querySelectorAll('table tbody tr').length") >= 1)
goto("/admin/messages")
ok("admin messages page ok", ev("!!document.querySelector('.admin-main')"))
goto("/admin/settings")
ok("admin settings ok", ev("!!document.querySelector('form')"))
errs = console_errors()
ok("admin: no console errors", not errs, str(errs[:2]))

ws.close()
chrome.terminate()
server.shutdown()

print(f"\n{'='*56}\nBROWSER AUDIT  PASSED: {len(PASS)}   FAILED: {len(FAIL)}")
for f in FAIL:
    print("  FAIL:", f)
if not FAIL:
    print("  All browser checks passed.")
