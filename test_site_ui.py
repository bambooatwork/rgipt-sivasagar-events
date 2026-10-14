"""Public-site UI test — runs the REAL docs/js/*.js in headless Chrome against a
stubbed Firebase SDK, with an *empty* database.

That combination is exactly the situation the site ships in right now, so this
test proves two things at once:

  1. the site is never blank and never empty — when the database has nothing
     published, the bundled sample schedule is shown (the preview fallback);
  2. the motion layer is wired up (progress bar, reveal classes, .js class) and
     never throws, which would blank the page.

The SDK stub is swapped in by rewriting the one SDK constant in store.js inside
a throwaway copy of docs/, so the real application code is what runs.

    python test_site_ui.py
"""
import functools
import http.server
import json
import os
import re
import shutil
import socketserver
import subprocess
import tempfile
import threading
import time
import urllib.request

import websocket

ROOT = os.path.dirname(os.path.abspath(__file__))
DOCS = os.path.join(ROOT, "docs")

# --- stubbed Firebase SDK: initialises fine, every collection reads as empty ---
MOCK_APP = "export function initializeApp(cfg){ return { cfg }; }\n"
MOCK_AUTH = """export function getAuth(){ return {}; }
export function onAuthStateChanged(){ return () => {}; }
export function signInWithEmailAndPassword(){ return {}; }
export function signOut(){ return {}; }
export function updatePassword(){ return {}; }
"""
MOCK_FS = """export function getFirestore(){ return {}; }
export function collection(){ return {}; }
export function query(){ return {}; }
export function where(){ return {}; }
export function doc(){ return {}; }
export async function getDocs(){ return { docs: [] }; }
export async function getDoc(){ return { exists: () => false }; }
export async function addDoc(){ return { id: "mock" }; }
export async function updateDoc(){}
export async function deleteDoc(){}
"""


def build_harness():
    d = tempfile.mkdtemp(prefix="siteui-")
    dst = os.path.join(d, "docs")
    shutil.copytree(DOCS, dst)
    mock = os.path.join(dst, "mock")
    os.makedirs(mock, exist_ok=True)
    open(os.path.join(mock, "firebase-app.js"), "w").write(MOCK_APP)
    open(os.path.join(mock, "firebase-auth.js"), "w").write(MOCK_AUTH)
    open(os.path.join(mock, "firebase-firestore.js"), "w").write(MOCK_FS)

    # point store.js at the stub instead of the CDN
    p = os.path.join(dst, "js", "store.js")
    src = open(p, encoding="utf-8").read()
    new, n = re.subn(r'const SDK = "[^"]+";', 'const SDK = "../mock";', src)
    assert n == 1, "could not redirect the SDK constant"
    open(p, "w", encoding="utf-8").write(new)
    return d, dst


def main():
    serve_root, docs = build_harness()
    PORT, DBG = 5160, 9484

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=serve_root)

    class Q(socketserver.TCPServer):
        allow_reuse_address = True

    srv = Q(("127.0.0.1", PORT), handler)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    time.sleep(1)
    BASE = f"http://127.0.0.1:{PORT}/docs"

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

    _id, _events, _dlg = [0], [], set()

    def cmd(m, p=None):
        _id[0] += 1
        mine = _id[0]
        ws.send(json.dumps({"id": mine, "method": m, "params": p or {}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") in _dlg:
                _dlg.discard(r.get("id"))
                continue
            if r.get("id") == mine:
                return r
            if r.get("method") == "Page.javascriptDialogOpening":
                _id[0] += 1
                _dlg.add(_id[0])
                ws.send(json.dumps({"id": _id[0], "method": "Page.handleJavaScriptDialog",
                                    "params": {"accept": True}}))
                continue
            _events.append(r)

    def ev(expr):
        return cmd("Runtime.evaluate", {"expression": expr, "returnByValue": True}) \
            .get("result", {}).get("result", {}).get("value")

    def errors():
        out = []
        for e in _events:
            if e.get("method") == "Runtime.exceptionThrown":
                d = e["params"]["exceptionDetails"]
                ex = d.get("exception") or {}
                out.append(f"{d.get('text')}: {str(ex.get('description','')).splitlines()[0][:160]}")
            if e.get("method") == "Log.entryAdded":
                ent = e["params"]["entry"]
                if ent.get("level") == "error" and "favicon" not in ent.get("text", ""):
                    out.append(ent.get("text", ""))
        return out

    PASS, FAIL = [], []

    def ok(label, cond, extra=""):
        (PASS if cond else FAIL).append(label + ("" if cond else f"  [{extra}]"))

    def go(url, wait=2.2):
        _events.clear()
        cmd("Page.navigate", {"url": BASE + "/" + url})
        for _ in range(40):
            time.sleep(0.25)
            if ev("document.readyState") == "complete":
                break
        time.sleep(wait)

    def body():
        return ev("document.body.textContent") or ""

    cmd("Page.enable")
    cmd("Runtime.enable")
    cmd("Log.enable")

    # ---------------------------------------------------------------- home
    go("index.html")
    b = body()
    ok("home: hero renders", "Where campus" in b, b[:100])
    ok("home: not empty — event rows rendered", ev("document.querySelectorAll('.listing .row').length") > 0,
       str(ev("document.querySelectorAll('.listing .row').length")))
    ok("home: ticker present", ev("!!document.querySelector('.ticker .item')"))
    ok("home: stat band shows a real count", ev("!!document.querySelector('.band .stat b')"))
    ok("home: notice board has rows", ev("document.querySelectorAll('.ann-row').length") > 0)
    ok("home: sample-data note shown", "sample schedule" in b)
    ok("home: no uncaught errors", not errors(), str(errors()[:2]))

    # ------------------------------------------------------------- motion
    ok("motion: .js class set on <html>", ev("document.documentElement.classList.contains('js')"))
    ok("motion: scroll progress bar exists", ev("!!document.getElementById('progress')"))
    ok("motion: reveal elements applied", ev("document.querySelectorAll('.reveal').length") > 3,
       str(ev("document.querySelectorAll('.reveal').length")))
    time.sleep(1.2)
    ok("motion: in-view elements revealed", ev("document.querySelectorAll('.reveal.in').length") > 0,
       str(ev("document.querySelectorAll('.reveal.in').length")))
    ok("motion: nav condenses on scroll",
       ev("(()=>{window.scrollTo(0,400);return true})()") and
       (time.sleep(0.5) or ev("document.querySelector('.nav').classList.contains('scrolled')")))
    ev("window.scrollTo(0,0)")
    time.sleep(0.4)
    ok("motion: no errors after scrolling", not errors(), str(errors()[:2]))

    # ------------------------------------------------------------- events
    go("events.html")
    b = body()
    # the page defaults to the "upcoming" filter
    ok("events: upcoming rows render", ev("document.querySelectorAll('.listing .row').length") >= 5,
       str(ev("document.querySelectorAll('.listing .row').length")))
    ok("events: count text", "events found" in b, b[:150])
    ok("events: sample-data note", "sample schedule" in b)
    ok("events: filter by category works",
       ev("(()=>{const f=document.getElementById('filter');f.elements.category.value='Sports';"
          "f.dispatchEvent(new Event('change'));return document.querySelectorAll('.listing .row').length;})()") >= 1)
    ok("events: search filters down",
       ev("(()=>{const f=document.getElementById('filter');f.elements.category.value='';"
          "f.elements.q.value='zzzznomatch';f.dispatchEvent(new Event('input'));"
          "return document.querySelectorAll('.listing .row').length;})()") == 0)
    ok("events: empty state shows",
       ev("document.getElementById('empty').style.display") == "block")
    ok("events: no uncaught errors", not errors(), str(errors()[:2]))

    # -------------------------------------------------------- event detail
    go("event.html?id=preview-e0")
    b = body()
    ok("event detail: title renders", "Urja Shakti 2026" in b, b[:120])
    ok("event detail: description renders", "national initiative" in b)
    ok("event detail: info card", ev("!!document.querySelector('.info-card')"))
    ok("event detail: register button", "Register" in b)
    ok("event detail: countdown present", ev("!!document.querySelector('.countdown .cd b')"))
    ok("event detail: no uncaught errors", not errors(), str(errors()[:2]))

    # ------------------------------------------------------ announcements
    go("announcements.html")
    b = body()
    ok("announcements: rows render", ev("document.querySelectorAll('.ann-row').length") >= 5,
       str(ev("document.querySelectorAll('.ann-row').length")))
    ok("announcements: sample-data note", "sample schedule" in b)
    ok("announcements: no uncaught errors", not errors(), str(errors()[:2]))

    go("announcement.html?id=preview-a0")
    b = body()
    ok("announcement detail: title renders", "Urja Shakti 2026" in b, b[:120])
    ok("announcement detail: body renders", "faculty mentor" in b)
    ok("announcement detail: related list", ev("!!document.querySelector('.info-card .ann-row')"))
    ok("announcement detail: no uncaught errors", not errors(), str(errors()[:2]))

    # ----------------------------------------------------- static pages
    for url, needle in [("faculty.html", "Faculty"), ("about.html", "RGIPT"),
                        ("contact.html", "Contact")]:
        go(url)
        ok(f"{url}: renders", needle in body(), body()[:80])
        ok(f"{url}: no uncaught errors", not errors(), str(errors()[:2]))

    ws.close()
    chrome.terminate()
    srv.shutdown()
    shutil.rmtree(serve_root, ignore_errors=True)

    print(f"\nSITE UI TEST  PASSED: {len(PASS)}  FAILED: {len(FAIL)}")
    for f in FAIL:
        print("  FAIL:", f)
    if not FAIL:
        print("  All public-site checks passed.")


if __name__ == "__main__":
    main()
