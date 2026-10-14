"""Admin panel UI test — runs the real docs/js/admin.js against a mocked data
layer, so the whole admin interface can be verified without a network or a
Firebase project.

It builds a throwaway copy of the admin page with `store.js` swapped for a mock,
serves it over HTTP, and drives it in headless Chrome:

  * signed out  -> the sign-in card renders (and carries no setup hint text)
  * signed in   -> the dashboard, sidebar, KPIs and every view render
  * no uncaught exceptions at any point (an uncaught error used to leave the
    page blank, which is the bug this test guards against)

    python test_admin_ui.py
"""
import functools
import http.server
import json
import os
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

MOCK_STORE = r"""
/* MOCK data layer — lets the admin UI run with no network.
   NOTE: watchAuth deliberately returns nothing (not a promise), which is the
   case that previously threw "Cannot read properties of undefined (reading
   'catch')" and blanked the page. */
export function isConfigured(){ return true; }
export async function init(){ return true; }
export function watchAuth(cb){ setTimeout(()=>cb(window.__TEST_USER__), 60); }
export async function login(){ return {}; }
export async function logout(){}
const EV=[{id:"1",title:"Urjotsav 2026",category:"Technical",eventDate:"2026-11-14",endDate:"2026-11-15",
  startTime:"09:00 AM",endTime:"06:00 PM",capacity:500,fee:0,isPublished:true,isFeatured:true,
  shortDescription:"The annual festival",description:"Long text",organizer:"Science & Technology Council",
  venue:"RGIPT Sivasagar Campus",teamSize:"Individual or Team",contactEmail:"",accent:"amber",
  registrationDeadline:"2026-11-08"}];
const AN=[{id:"a1",title:"Registrations open",body:"Body text",category:"Events",isPinned:true,
  isPublished:true,publishedAt:"2026-10-07T00:00:00.000Z"}];
const RG=[{id:"r1",name:"Ananya Baruah",email:"a@b.com",phone:"999",eventId:"1",eventTitle:"Urjotsav 2026",
  status:"confirmed",ticketCode:"RGIABC1",createdAt:"2026-10-12T00:00:00.000Z"}];
const MS=[{id:"m1",name:"A",email:"a@b.com",subject:"Hi",message:"Hello",isRead:false,
  createdAt:"2026-10-12T00:00:00.000Z"}];
export async function listEvents(){ return EV; }
export async function getEvent(id){ return EV.find(e=>e.id===id)||null; }
export async function listAnnouncements(){ return AN; }
export async function getAnnouncement(id){ return AN.find(a=>a.id===id)||null; }
export async function listRegistrations(){ return RG; }
export async function listMessages(){ return MS; }
export async function saveEvent(){ return "1"; }
export async function deleteEvent(){}
export async function saveAnnouncement(){ return "a1"; }
export async function deleteAnnouncement(){}
export async function updateRegistration(){}
export async function deleteRegistration(){}
export async function updateMessage(){}
export async function deleteMessage(){}
export async function changePassword(){}
export async function loadStarterData(){ return 11; }
export function formatDate(i,o){ if(!i) return ""; const d=new Date(i+"T00:00:00");
  return isNaN(d)?i:d.toLocaleDateString("en-GB",o||{day:"2-digit",month:"short",year:"numeric"}); }
export function inr(n){ const v=Number(n||0); return v===0?"Free":"\u20b9"+v; }
export function escapeHtml(s){ return String(s==null?"":s).replace(/[&<>"']/g,
  c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
export function isPast(e){ return false; }
export function today(){ return "2026-10-13"; }
"""


def build_harness():
    d = tempfile.mkdtemp(prefix="adminui-")
    os.makedirs(os.path.join(d, "js"))
    os.makedirs(os.path.join(d, "css"))
    os.makedirs(os.path.join(d, "img"))
    shutil.copy(os.path.join(DOCS, "admin.html"), d)
    shutil.copy(os.path.join(DOCS, "css", "style.css"), os.path.join(d, "css"))
    shutil.copy(os.path.join(DOCS, "img", "logo.png"), os.path.join(d, "img"))
    shutil.copy(os.path.join(DOCS, "js", "admin.js"), os.path.join(d, "js"))
    with open(os.path.join(d, "js", "store.js"), "w", encoding="utf-8") as f:
        f.write(MOCK_STORE)
    return d


def main():
    docs = build_harness()
    PORT, DBG = 5130, 9477

    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=docs)

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
         f"--user-data-dir={prof}", "--window-size=1440,1100", "about:blank"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(4)
    tgt = json.load(urllib.request.urlopen(f"http://127.0.0.1:{DBG}/json"))
    page = [t for t in tgt if t["type"] == "page"][0]
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], max_size=None)

    _id = [0]
    _events = []

    def cmd(m, p=None):
        _id[0] += 1
        ws.send(json.dumps({"id": _id[0], "method": m, "params": p or {}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") == _id[0]:
                return r
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
                if ent.get("level") == "error":
                    out.append(ent.get("text", ""))
        return out

    PASS, FAIL = [], []

    def ok(label, cond, extra=""):
        (PASS if cond else FAIL).append(label + ("" if cond else f"  [{extra}]"))

    def load(user):
        _events.clear()
        src = "window.__TEST_USER__ = %s;" % ("null" if user is None else json.dumps(user))
        sid = cmd("Page.addScriptToEvaluateOnNewDocument", {"source": src})["result"]["identifier"]
        cmd("Page.navigate", {"url": BASE + "/admin.html"})
        for _ in range(40):
            time.sleep(0.25)
            if ev("document.readyState") == "complete":
                break
        time.sleep(1.2)
        cmd("Page.removeScriptToEvaluateOnNewDocument", {"identifier": sid})

    def goto_hash(h, wait=1.2):
        ev("location.hash=%s" % json.dumps(h))
        time.sleep(wait)

    def body():
        return ev("document.body.innerText") or ""

    cmd("Page.enable")
    cmd("Runtime.enable")
    cmd("Log.enable")

    # ---- signed out ----
    load(None)
    b, e = body(), errors()
    ok("signed out: sign-in card renders", "Admin sign in" in b, b[:90])
    ok("signed out: email field present", ev("!!document.querySelector('input[name=email]')"))
    ok("signed out: password field present", ev("!!document.querySelector('input[name=password]')"))
    ok("signed out: no setup hint on the login card", "SETUP.md" not in b)
    ok("signed out: no uncaught errors", not e, str(e[:2]))

    # ---- signed in ----
    load({"email": "admin@rgipt.ac.in"})
    b, e = body(), errors()
    ok("signed in: dashboard renders", "Dashboard" in b, b[:90])
    ok("signed in: sidebar renders", ev("document.querySelectorAll('.admin-side a').length") >= 6)
    ok("signed in: four KPI cards", ev("document.querySelectorAll('.kpi').length") == 4)
    ok("signed in: load-starter button present", ev("!!document.getElementById('loadStarter')"))
    ok("signed in: no uncaught errors", not e, str(e[:2]))

    # ---- every view ----
    goto_hash("#/events")
    b = body()
    ok("events view: table renders", "Urjotsav 2026" in b, b[:90])
    ok("events view: registered/capacity shown", "1 / 500" in b, b[:150])
    ok("events view: row actions present",
       ev("!!document.querySelector('[data-toggle]') && !!document.querySelector('[data-del]')"))

    goto_hash("#/registrations")
    b = body()
    ok("registrations view: rows render", "Ananya Baruah" in b, b[:90])
    ok("registrations view: CSV export button", ev("!!document.getElementById('csv')"))
    ok("registrations view: status control", ev("!!document.querySelector('[data-status]')"))

    goto_hash("#/announcements")
    ok("announcements view: rows render", "Registrations open" in body())

    goto_hash("#/messages")
    ok("messages view: rows render", "Hello" in body())

    goto_hash("#/settings")
    ok("settings view: renders", "Change password" in body())

    goto_hash("#/event-form")
    ok("event form: title field", ev("!!document.querySelector('#eventForm input[name=title]')"))
    ok("event form: date field", ev("!!document.querySelector('#eventForm input[name=eventDate]')"))

    goto_hash("#/announcement-form")
    ok("announcement form: body field", ev("!!document.querySelector('#annForm textarea[name=body]')"))

    ok("all views: no uncaught errors", not errors(), str(errors()[:2]))

    ws.close()
    chrome.terminate()
    srv.shutdown()
    shutil.rmtree(docs, ignore_errors=True)

    print(f"\nADMIN UI TEST  PASSED: {len(PASS)}  FAILED: {len(FAIL)}")
    for f in FAIL:
        print("  FAIL:", f)
    if not FAIL:
        print("  All admin UI checks passed.")


if __name__ == "__main__":
    main()
