"""Security regression test.

Two halves:

1. **Live XSS test.** The real docs/js/*.js is run in headless Chrome against a
   stubbed Firebase SDK that returns deliberately malicious records — titles,
   dates, categories and statuses containing HTML and `onerror` handlers. If any
   of them reach the DOM unescaped, `window.__XSS__` gets set and the test fails.
   This is the sink that matters: the data is written by whoever can write to
   Firestore, so it must be treated as hostile on the way out.

2. **Static checks** on the security rules and configuration — that the rules no
   longer treat "signed in" as "admin" (anyone can mint a Firebase account with
   the public API key), that the admin roster is sealed, and that no credentials
   are committed.

    python test_security.py
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

PAYLOAD = '<img src=x onerror="window.__XSS__=1">'

MOCK_APP = "export function initializeApp(cfg){ return { cfg }; }\n"
MOCK_AUTH = """export function getAuth(){ return {}; }
export function onAuthStateChanged(){ return () => {}; }
export function signInWithEmailAndPassword(){ return {}; }
export function signOut(){ return {}; }
export function updatePassword(){ return {}; }
"""

# A record in which EVERY field is an injection attempt.
MOCK_FS = """const EVIL = {
  title: %(p)s + ' EVIL TITLE',
  category: %(p)s,
  shortDescription: '<script>window.__XSS__=3<\\/script>desc',
  description: '<img src=x onerror="window.__XSS__=4">',
  organizer: %(p)s,
  venue: %(p)s,
  eventDate: '"><img src=x onerror="window.__XSS__=7">',
  endDate: '"><img src=x onerror="window.__XSS__=8">',
  startTime: %(p)s,
  endTime: %(p)s,
  registrationDeadline: '"><img src=x onerror="window.__XSS__=10">',
  capacity: 'not-a-number',
  fee: 'nope',
  teamSize: %(p)s,
  contactEmail: %(p)s,
  accent: %(p)s,
  isFeatured: true,
  isPublished: true
};
const EVIL_ANN = {
  title: %(p)s + ' EVIL NOTICE',
  body: '<img src=x onerror="window.__XSS__=21">',
  category: %(p)s,
  isPinned: true,
  isPublished: true,
  publishedAt: '"><img src=x onerror="window.__XSS__=22">'
};
export function getFirestore(){ return {}; }
export function collection(db, n){ return { __name: n }; }
export function query(c){ return { __name: c.__name }; }
export function where(){ return {}; }
export function doc(db, n, id){ return { __name: n, id }; }
export async function getDocs(ref){
  const n = ref && ref.__name;
  if (n === 'events') return { docs: [{ id: 'evil-1', data: () => EVIL }] };
  if (n === 'announcements') return { docs: [{ id: 'evil-1', data: () => EVIL_ANN }] };
  return { docs: [] };
}
export async function getDoc(ref){
  const n = ref && ref.__name;
  if (n === 'events') return { exists: () => true, id: 'evil-1', data: () => EVIL };
  if (n === 'announcements') return { exists: () => true, id: 'evil-1', data: () => EVIL_ANN };
  return { exists: () => false, id: 'x', data: () => ({}) };
}
export async function addDoc(){ return { id: 'mock' }; }
export async function updateDoc(){}
export async function deleteDoc(){}
""" % {"p": json.dumps(PAYLOAD)}


def build_harness():
    d = tempfile.mkdtemp(prefix="sec-")
    dst = os.path.join(d, "docs")
    shutil.copytree(DOCS, dst)
    mock = os.path.join(dst, "mock")
    os.makedirs(mock, exist_ok=True)
    open(os.path.join(mock, "firebase-app.js"), "w").write(MOCK_APP)
    open(os.path.join(mock, "firebase-auth.js"), "w").write(MOCK_AUTH)
    open(os.path.join(mock, "firebase-firestore.js"), "w").write(MOCK_FS)
    p = os.path.join(dst, "js", "store.js")
    src = open(p, encoding="utf-8").read()
    new, n = re.subn(r'const SDK = "[^"]+";', 'const SDK = "../mock";', src)
    assert n == 1
    open(p, "w", encoding="utf-8").write(new)
    return d


def static_checks(PASS, FAIL):
    def ok(label, cond, extra=""):
        (PASS if cond else FAIL).append(label + ("" if cond else f"  [{extra}]"))

    rules = open(os.path.join(ROOT, "firestore.rules"), encoding="utf-8").read()
    cfg = open(os.path.join(ROOT, "docs", "js", "firebase-config.js"), encoding="utf-8").read()

    ok("rules: define an isAdmin() gate", "function isAdmin()" in rules)
    ok("rules: admin = listed in the admins collection",
       "exists(/databases/$(database)/documents/admins/$(request.auth.uid))" in rules)
    ok("rules: no write granted to merely-authenticated users",
       not re.search(r"allow\s+write[^;]*request\.auth\s*!=\s*null", rules))
    ok("rules: no read of registrations by merely-authenticated users",
       not re.search(r"allow\s+read[^;]*request\.auth\s*!=\s*null", rules))
    ok("rules: the admins collection is sealed",
       re.search(r"match\s+/admins/\{doc\}\s*\{\s*allow\s+read,\s*write:\s*if\s+false", rules) is not None)
    ok("rules: public can still read published events",
       re.search(r"match\s+/events/\{doc\}[\s\S]{0,200}resource\.data\.isPublished\s*==\s*true", rules) is not None)
    ok("rules: registration create is field-limited",
       "keys().hasOnly(" in rules)
    ok("rules: registration status is pinned to 'confirmed'",
       "request.resource.data.status == 'confirmed'" in rules)

    ok("config: no service-account / private key in the repo",
       not os.path.exists(os.path.join(ROOT, "serviceAccountKey.json")))
    ok("config: firebase-config holds only the public web key",
       cfg.count("AIza") == 1 and "private_key" not in cfg)

    hits = []
    for dirpath, dirnames, files in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in ("__pycache__", ".git")]
        for fn in files:
            if not fn.endswith((".py", ".js", ".json", ".yaml", ".yml", ".md", ".rules")):
                continue
            try:
                txt = open(os.path.join(dirpath, fn), encoding="utf-8", errors="ignore").read()
            except Exception:
                continue
            for pat in (r"-----BEGIN [A-Z ]*PRIVATE KEY", r"ghp_[A-Za-z0-9]{20,}",
                        r"sk-[A-Za-z0-9]{24,}", r"AKIA[0-9A-Z]{16}", r"xox[baprs]-"):
                if re.search(pat, txt):
                    hits.append(f"{fn}:{pat}")
    ok("secrets: no credential-shaped strings committed", not hits, str(hits[:3]))

    for f in ("app.py", "docs/js/store.js", "docs/js/site.js", "docs/js/admin.js"):
        txt = open(os.path.join(ROOT, f), encoding="utf-8").read()
        ok(f"js/py: {f} has no eval()", not re.search(r"\beval\s*\(", txt))
        ok(f"js/py: {f} has no document.write", "document.write" not in txt)

    py = open(os.path.join(ROOT, "app.py"), encoding="utf-8").read()
    models = open(os.path.join(ROOT, "models.py"), encoding="utf-8").read()
    ok("flask: CSRF uses a constant-time compare", "compare_digest" in py)
    ok("flask: passwords are hashed (werkzeug)",
       "generate_password_hash" in models and "check_password_hash" in models)
    ok("flask: session is cleared on login (no fixation)", "session.clear()" in py)
    ok("flask: debug is off", "debug=False" in py)
    ok("flask: open-redirect guarded on ?next",
       'nxt.startswith("/admin")' in py)
    conf = open(os.path.join(ROOT, "config.py"), encoding="utf-8").read()
    ok("flask: cookie HttpOnly + SameSite set",
       "SESSION_COOKIE_HTTPONLY = True" in conf and "SESSION_COOKIE_SAMESITE" in conf)


def main():
    PASS, FAIL = [], []
    static_checks(PASS, FAIL)

    serve_root = build_harness()
    PORT, DBG = 5240, 9510
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
         f"--user-data-dir={prof}", "--window-size=1440,1100", "about:blank"],
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

    def ok(label, cond, extra=""):
        (PASS if cond else FAIL).append(label + ("" if cond else f"  [{extra}]"))

    def go(url, wait=2.4):
        _events.clear()
        cmd("Page.navigate", {"url": BASE + "/" + url})
        for _ in range(40):
            time.sleep(0.25)
            if ev("document.readyState") == "complete":
                break
        time.sleep(wait)

    cmd("Page.enable")
    cmd("Runtime.enable")
    cmd("Log.enable")

    pages = [("index.html", "home"), ("events.html", "events"),
             ("event.html?id=evil-1", "event detail"),
             ("announcements.html", "announcements"),
             ("announcement.html?id=evil-1", "announcement detail"),
             ("register.html?id=evil-1", "register")]

    for url, label in pages:
        go(url)
        injected = ev("document.querySelectorAll('img[src=\"x\"]').length") or 0
        xss = ev("window.__XSS__")
        scripts = ev("document.querySelectorAll('#app script').length") or 0
        ok(f"xss/{label}: no injected element from hostile data", injected == 0, f"{injected} img[src=x]")
        ok(f"xss/{label}: no handler executed", xss is None, f"window.__XSS__={xss}")
        ok(f"xss/{label}: no injected <script>", scripts == 0, f"{scripts} scripts")

    # the hostile title should still be *shown*, as literal text.
    # (status=all: a record whose date will not parse is classified as past, so
    #  the default "upcoming" filter would legitimately hide it.)
    go("events.html?status=all")
    ok("xss/events: hostile title is shown as escaped text, not dropped",
       "EVIL TITLE" in (ev("document.body.textContent") or ""))
    ok("xss/events: hostile title is visible as literal markup",
       "onerror" in (ev("document.body.textContent") or ""))

    # a non-numeric capacity must not render as NaN
    go("event.html?id=evil-1")
    body = ev("document.body.textContent") or ""
    ok("data: non-numeric capacity does not render NaN", "NaN" not in body, body[:120])
    ok("data: unparseable date does not leak raw markup",
       "window.__XSS__=7" not in body)
    ok("xss/event detail: no uncaught errors",
       not [e for e in _events if e.get("method") == "Runtime.exceptionThrown"])

    ws.close()
    chrome.terminate()
    srv.shutdown()
    shutil.rmtree(serve_root, ignore_errors=True)

    print(f"\nSECURITY TEST  PASSED: {len(PASS)}  FAILED: {len(FAIL)}")
    for f in FAIL:
        print("  FAIL:", f)
    if not FAIL:
        print("  All security checks passed.")


if __name__ == "__main__":
    main()
