"""Admin panel UI test — runs the real docs/js/admin.js against a *stateful*
mock data layer, so every button can be clicked and its effect verified without
a network or a Firebase project.

Builds a throwaway copy of the admin page with `store.js` swapped for the mock,
serves it over HTTP, and drives it in headless Chrome:

  * signed out   -> the sign-in card renders (logo shown, no setup hint)
  * signed in    -> dashboard, sidebar, KPIs and every view render
  * branding     -> the campus logo appears; there is no "View site" link
  * every button -> publish/hide, delete, status change, mark-read, CSV export
  * robustness   -> no uncaught exceptions at any point (an uncaught error used
                    to leave the page blank, which is what this guards against)

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
/* MOCK data layer — stateful, so clicking a button really changes the data.
   NOTE: watchAuth deliberately returns nothing (not a promise), which is the
   case that previously threw "Cannot read properties of undefined (reading
   'catch')" and blanked the page. */
export function isConfigured(){ return true; }
export async function init(){ return true; }
export function watchAuth(cb){ setTimeout(()=>cb(window.__TEST_USER__), 60); }
export async function login(){ return {}; }
export async function logout(){ window.__LOGGED_OUT__ = true; }

let EV=[{id:"1",title:"Urjotsav 2026",category:"Technical",eventDate:"2026-11-14",endDate:"2026-11-15",
  startTime:"09:00 AM",endTime:"06:00 PM",capacity:500,fee:0,isPublished:true,isFeatured:true,
  shortDescription:"The annual festival",description:"Long text",organizer:"Science & Technology Council",
  venue:"RGIPT Sivasagar Campus",teamSize:"Individual or Team",contactEmail:"",accent:"amber",
  registrationDeadline:"2026-11-08"}];
let AN=[{id:"a1",title:"Registrations open",body:"Body text",category:"Events",isPinned:true,
  isPublished:true,publishedAt:"2026-10-07T00:00:00.000Z"}];
let RG=[{id:"r1",name:"Ananya Baruah",email:"a@b.com",phone:"999",eventId:"1",eventTitle:"Urjotsav 2026",
  status:"confirmed",ticketCode:"RGIABC1",createdAt:"2026-10-12T00:00:00.000Z"}];
let MS=[{id:"m1",name:"A",email:"a@b.com",subject:"Hi",message:"Hello",isRead:false,
  createdAt:"2026-10-12T00:00:00.000Z"}];

export async function listEvents(){ return EV; }
export async function getEvent(id){ return EV.find(e=>e.id===id)||null; }
export async function listAnnouncements(){ return AN; }
export async function getAnnouncement(id){ return AN.find(a=>a.id===id)||null; }
export async function listRegistrations(){ return RG; }
export async function listMessages(){ return MS; }

export async function saveEvent(id,data){
  if(id){ const i=EV.findIndex(e=>e.id===id); if(i>-1) EV[i]={...EV[i],...data}; }
  else { EV.push({id:String(Date.now()),...data}); }
  return id||"new";
}
export async function deleteEvent(id){ EV=EV.filter(e=>e.id!==id); }
export async function saveAnnouncement(id,data){
  if(id){ const i=AN.findIndex(a=>a.id===id); if(i>-1) AN[i]={...AN[i],...data}; }
  else { AN.push({id:String(Date.now()),...data}); }
  return id||"new";
}
export async function deleteAnnouncement(id){ AN=AN.filter(a=>a.id!==id); }
export async function updateRegistration(id,patch){ const i=RG.findIndex(r=>r.id===id); if(i>-1) RG[i]={...RG[i],...patch}; }
export async function deleteRegistration(id){ RG=RG.filter(r=>r.id!==id); }
export async function updateMessage(id,patch){ const i=MS.findIndex(m=>m.id===id); if(i>-1) MS[i]={...MS[i],...patch}; }
export async function deleteMessage(id){ MS=MS.filter(m=>m.id!==id); }
export async function changePassword(){ return true; }
export async function loadStarterData(){ return 19; }
export function formatDate(i,o){ if(!i) return ""; const d=new Date(i+"T00:00:00");
  return isNaN(d)?i:d.toLocaleDateString("en-GB",o||{day:"2-digit",month:"short",year:"numeric"}); }
export function inr(n){ const v=Number(n||0); return v===0?"Free":"\u20b9"+v; }
export function escapeHtml(s){ return String(s==null?"":s).replace(/[&<>"']/g,
  c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c])); }
export function isPast(e){ return false; }
export function today(){ return "2026-10-14"; }
"""


def build_harness():
    d = tempfile.mkdtemp(prefix="adminui-")
    for sub in ("js", "css", "img"):
        os.makedirs(os.path.join(d, sub))
    shutil.copy(os.path.join(DOCS, "admin.html"), d)
    shutil.copy(os.path.join(DOCS, "css", "style.css"), os.path.join(d, "css"))
    shutil.copy(os.path.join(DOCS, "img", "logo.png"), os.path.join(d, "img"))
    shutil.copy(os.path.join(DOCS, "js", "admin.js"), os.path.join(d, "js"))
    with open(os.path.join(d, "js", "store.js"), "w", encoding="utf-8") as f:
        f.write(MOCK_STORE)
    return d


def main():
    docs = build_harness()
    PORT, DBG = 5131, 9478

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
    _dialog_ids = set()

    def cmd(m, p=None):
        _id[0] += 1
        mine = _id[0]
        ws.send(json.dumps({"id": mine, "method": m, "params": p or {}}))
        while True:
            r = json.loads(ws.recv())
            if r.get("id") in _dialog_ids:
                _dialog_ids.discard(r.get("id"))
                continue
            if r.get("id") == mine:
                return r
            if r.get("method") == "Page.javascriptDialogOpening":
                _id[0] += 1
                _dialog_ids.add(_id[0])
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

    def goto_hash(h, wait=1.0):
        ev("location.hash=%s" % json.dumps(h))
        time.sleep(wait)

    def click(sel, wait=0.9):
        r = ev("(()=>{const el=document.querySelector(%s); if(!el) return 'missing'; el.click(); return 'ok';})()"
               % json.dumps(sel))
        time.sleep(wait)
        return r

    def body():
        # textContent, not innerText: .badge applies text-transform:uppercase, so
        # innerText would return "PUBLISHED" and break the mixed-case checks.
        return ev("document.body.textContent") or ""

    cmd("Page.enable")
    cmd("Runtime.enable")
    cmd("Log.enable")

    # ---------------- signed out ----------------
    load(None)
    b, e = body(), errors()
    ok("signed out: sign-in card renders", "Admin sign in" in b, b[:90])
    ok("signed out: logo on the sign-in card", ev("!!document.querySelector('.auth-card img')"))
    ok("signed out: no setup hint text", "SETUP.md" not in b)
    ok("signed out: has a 'Return to website' link",
       ev("!!document.querySelector('.auth-card a[href=\"index.html\"]')"))
    ok("signed out: that link reads 'Return to website'",
       "Return to website" in (ev("document.querySelector('.auth-card a[href=\"index.html\"]').textContent") or ""))
    ok("signed out: no 'View site' label", "View site" not in b)
    ok("signed out: no uncaught errors", not e, str(e[:2]))

    # ---------------- signed in ----------------
    load({"email": "admin@rgipt.ac.in"})
    b, e = body(), errors()
    ok("signed in: dashboard renders", "Welcome back" in b, b[:90])
    ok("signed in: header logo present", ev("!!document.querySelector('.admin-brand .logo')"))
    ok("signed in: hero logo present", ev("!!document.querySelector('.admin-hero-logo img')"))
    ok("signed in: no 'View site' link", not ev("!!document.querySelector('a[href=\"index.html\"]')"))
    ok("signed in: sidebar has 6 items", ev("document.querySelectorAll('.admin-side a').length") == 6,
       str(ev("document.querySelectorAll('.admin-side a').length")))
    ok("signed in: sidebar items have icons", ev("document.querySelectorAll('.admin-side a .ai').length") == 6)
    ok("signed in: four KPI cards", ev("document.querySelectorAll('.kpi').length") == 4)
    ok("signed in: KPI icons shown", ev("document.querySelectorAll('.kpi .ico svg').length") == 4)
    ok("signed in: no uncaught errors", not e, str(e[:2]))

    # ---------------- events: toggle + delete ----------------
    goto_hash("#/events")
    b = body()
    ok("events: table renders", "Urjotsav 2026" in b, b[:90])
    ok("events: registered/capacity shown", "1 / 500" in b, b[:150])
    ok("events: starts Published", "Published" in b)
    click("[data-toggle]")
    ok("events: Hide button flips the status", "Hidden" in body(), body()[:150])
    click("[data-toggle]")
    ok("events: Publish button flips it back", "Published" in body())
    click("[data-del]")
    ok("events: Delete removes the row", "Urjotsav 2026" not in body(), body()[:150])

    # ---------------- announcements: publish toggle ----------------
    goto_hash("#/announcements")
    ok("announcements: rows render", "Registrations open" in body())
    click("[data-toggle]")
    ok("announcements: Unpublish flips to Draft", "Draft" in body(), body()[:150])

    # ---------------- registrations: status + CSV ----------------
    goto_hash("#/registrations")
    b = body()
    ok("registrations: rows render", "Ananya Baruah" in b, b[:90])
    ok("registrations: no Export CSV button", not ev("!!document.getElementById('csv')"))
    ok("registrations: no 'Export' text anywhere", "Export" not in body())
    ev("(()=>{const s=document.querySelector('[data-status]'); s.value='waitlist';"
       "s.dispatchEvent(new Event('change'));})()")
    time.sleep(0.9)
    ok("registrations: status change applies", "waitlist" in body(), body()[:150])

    # ---------------- messages: mark read ----------------
    goto_hash("#/messages")
    ok("messages: rows render", "Hello" in body())
    click("[data-read]")
    ok("messages: Mark read applies", "Mark unread" in body(), body()[:150])

    # ---------------- settings ----------------
    goto_hash("#/settings")
    ok("settings: renders", "Change password" in body())
    ok("settings: no 'View the public site' button",
       not ev("!!document.querySelector('a[href=\"index.html\"]')"))

    # ---------------- forms ----------------
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
