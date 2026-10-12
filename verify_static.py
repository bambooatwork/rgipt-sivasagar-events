"""Browser audit of the GitHub Pages build in ./docs.

Serves docs/ over HTTP and drives it in headless Chrome: checks every page for
console errors, overflow and oversized icons, verifies the faculty directory and
its search, and confirms the app shows its "backend not configured" notice (since
firebase-config.js ships empty) rather than any placeholder content.
"""
import functools
import http.server
import json
import os
import socketserver
import subprocess
import tempfile
import threading
import time
import urllib.request

import websocket

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
PORT = 5100
DBG = 9444

handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)


class Q(socketserver.TCPServer):
    allow_reuse_address = True


srv = Q(("127.0.0.1", PORT), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(1)
BASE = f"http://127.0.0.1:{PORT}"

prof = tempfile.mkdtemp()
chrome = subprocess.Popen(
    ["google-chrome-stable", "--headless=new", "--no-sandbox", "--disable-gpu",
     f"--remote-debugging-port={DBG}", "--remote-allow-origins=*",
     f"--user-data-dir={prof}", "--window-size=1440,1200", "about:blank"],
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
    return cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}) \
        .get("result", {}).get("result", {}).get("value")


def goto(path, wait=2.6):
    _events.clear()
    cmd("Page.navigate", {"url": BASE + "/" + path})
    for _ in range(40):
        time.sleep(0.25)
        if ev("document.readyState") == "complete":
            break
    time.sleep(wait)


def console_errors():
    out = []
    for e in _events:
        if e.get("method") == "Runtime.exceptionThrown":
            out.append("EXC: " + str(e["params"]["exceptionDetails"].get("text")))
        if e.get("method") == "Log.entryAdded":
            ent = e["params"]["entry"]
            if ent.get("level") == "error" and "favicon" not in ent.get("text", ""):
                out.append("LOG: " + ent.get("text", ""))
    return out


PASS, FAIL = [], []


def ok(label, cond, extra=""):
    (PASS if cond else FAIL).append(label + ("" if cond else f"  [{extra}]"))


cmd("Page.enable")
cmd("Runtime.enable")
cmd("Log.enable")

PAGES = [
    ("index.html", "home"),
    ("events.html", "events"),
    ("event.html", "event detail"),
    ("announcements.html", "announcements"),
    ("announcement.html", "announcement detail"),
    ("register.html", "register"),
    ("faculty.html", "faculty"),
    ("about.html", "about"),
    ("contact.html", "contact"),
    ("admin.html", "admin"),
    ("404.html", "404"),
]

for path, label in PAGES:
    goto(path)
    errs = console_errors()
    ok(f"{label}: no console/JS errors", not errs, str(errs[:2]))
    over = ev("document.documentElement.scrollWidth - window.innerWidth")
    ok(f"{label}: no horizontal overflow", (over or 0) <= 2, f"{over}px")
    if path != "admin.html":        # the admin app is standalone (its own header)
        ok(f"{label}: navigation rendered", ev("!!document.querySelector('.nav .brand')"))
        ok(f"{label}: footer rendered", ev("!!document.querySelector('.footer')"))
    ok(f"{label}: no theme toggle (light only)", not ev("!!document.querySelector('[data-theme-toggle]')"))
    big = ev("[...document.querySelectorAll('svg')].filter(s=>s.getBoundingClientRect().width>64).length")
    ok(f"{label}: no oversized icons", (big or 0) == 0, f"{big} oversized")
    ok(f"{label}: white background", ev("getComputedStyle(document.body).backgroundColor") == "rgb(255, 255, 255)")

# --- data pages must show the "not configured" notice, never fake content ---
for path, label in [("index.html", "home"), ("events.html", "events")]:
    goto(path)
    body = ev("document.body.innerText") or ""
    ok(f"{label}: shows 'backend not configured' notice", "Backend not configured" in body)

goto("admin.html")
body = ev("document.body.innerText") or ""
ok("admin: shows 'Backend not configured'", "Backend not configured" in body)

# --- faculty directory is static, so it must fully render ---
goto("faculty.html")
rows = ev("document.querySelectorAll('#facList [data-filter-item]').length")
ok("faculty: all members render", (rows or 0) >= 22, f"{rows} rows")
lead = ev("document.querySelectorAll('.listing .dir-row').length")
ok("faculty: leadership rows render", (lead or 0) >= 3, f"{lead} rows")
ev("(()=>{const i=document.getElementById('facSearch');i.value='gogoi';i.dispatchEvent(new Event('input'));})()")
time.sleep(0.4)
shown = ev("document.querySelectorAll('#facList [data-filter-item]:not([style*=\"display: none\"])').length")
ok("faculty: search filters", shown == 1, f"{shown} shown")

# --- link integrity across the docs folder ---
import re
import glob
files = {os.path.basename(f) for f in glob.glob(os.path.join(DOCS, "*.html"))}
broken = []
for f in glob.glob(os.path.join(DOCS, "*.html")):
    txt = open(f, encoding="utf-8").read()
    for href in re.findall(r'href="([^"]+)"', txt):
        if href.startswith(("http", "mailto:", "tel:", "#", "?")):
            continue
        target = href.split("#")[0].split("?")[0]
        if target and target not in files and not os.path.exists(os.path.join(DOCS, target)):
            broken.append((os.path.basename(f), href))
ok("link integrity: no broken internal links", not broken, str(broken[:3]))

ws.close()
chrome.terminate()
srv.shutdown()

print(f"\nSTATIC APP AUDIT  PASSED: {len(PASS)}  FAILED: {len(FAIL)}")
for f in FAIL:
    print("  FAIL:", f)
if not FAIL:
    print("  All static checks passed.")
