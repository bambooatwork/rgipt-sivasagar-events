import functools, http.server, json, os, socketserver, subprocess, threading, time, urllib.request, tempfile
import websocket

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs")
PORT = 5090
handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=DOCS)
class Q(socketserver.TCPServer): allow_reuse_address = True
srv = Q(("127.0.0.1", PORT), handler)
threading.Thread(target=srv.serve_forever, daemon=True).start()
time.sleep(1)
BASE = f"http://127.0.0.1:{PORT}"

prof = tempfile.mkdtemp()
chrome = subprocess.Popen(["google-chrome-stable","--headless=new","--no-sandbox","--disable-gpu",
  "--remote-debugging-port=9422","--remote-allow-origins=*",f"--user-data-dir={prof}","--window-size=1440,1000","about:blank"],
  stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
time.sleep(4)
tgt = json.load(urllib.request.urlopen("http://127.0.0.1:9422/json"))
page = [t for t in tgt if t["type"]=="page"][0]
ws = websocket.create_connection(page["webSocketDebuggerUrl"], max_size=None)
_id=[0]; events=[]
def cmd(m,p=None):
    _id[0]+=1; ws.send(json.dumps({"id":_id[0],"method":m,"params":p or {}}))
    while True:
        r=json.loads(ws.recv())
        if r.get("id")==_id[0]: return r
        events.append(r)
def ev(e):
    return cmd("Runtime.evaluate",{"expression":e,"returnByValue":True}).get("result",{}).get("result",{}).get("value")
def goto(p):
    events.clear()
    cmd("Page.navigate",{"url":BASE+"/"+p})
    for _ in range(40):
        time.sleep(0.25)
        if ev("document.readyState")=="complete": break
    time.sleep(1.2)
cmd("Page.enable"); cmd("Runtime.enable"); cmd("Log.enable")

PASS=[]; FAIL=[]
def ok(l,c,x=""):
    (PASS if c else FAIL).append(l+("" if c else f" {x}"))

for p in ["index.html","events.html","faculty.html","contact.html","about.html",
          "announcements.html","announcement-1.html","event-urjotsav-2026.html","404.html","my-registrations.html"]:
    goto(p)
    errs=[e["params"]["entry"].get("text","") for e in events
          if e.get("method")=="Log.entryAdded" and e["params"]["entry"].get("level")=="error"
          and "favicon" not in e["params"]["entry"].get("text","")]
    ok(f"{p}: no console errors", not errs, str(errs[:2]))
    over = ev("document.documentElement.scrollWidth - window.innerWidth")
    ok(f"{p}: no overflow", (over or 0) <= 2, f"{over}px")
    ok(f"{p}: CSS applied (white bg)", ev("getComputedStyle(document.body).backgroundColor")=="rgb(255, 255, 255)")
    badimg = ev("[...document.images].filter(i=>i.src && !i.complete).length")
    ok(f"{p}: images loaded", (badimg or 0)==0, f"{badimg} pending")

# events filtering
goto("events.html")
up = ev("document.querySelectorAll('[data-static-events] .event-card:not([style*=\"display: none\"])').length")
ok("events: default shows upcoming only", up and up>0 and up< ev("document.querySelectorAll('[data-static-events] .event-card').length"), f"upcoming={up}")
ev("(()=>{const s=document.querySelector('[data-filter-form] [name=status]');s.value='all';s.dispatchEvent(new Event('change',{bubbles:true}));})()")
time.sleep(0.4)
allc = ev("document.querySelectorAll('[data-static-events] .event-card:not([style*=\"display: none\"])').length")
ok("events: 'all' shows every card", allc == ev("document.querySelectorAll('[data-static-events] .event-card').length"), f"all={allc}")
ev("(()=>{const i=document.querySelector('[data-filter-form] [name=q]');i.value='urjotsav';i.dispatchEvent(new Event('input',{bubbles:true}));})()")
time.sleep(0.4)
ok("events: search 'urjotsav' filters", ev("document.querySelectorAll('[data-static-events] .event-card:not([style*=\"display: none\"])').length")==1)

# faculty search
goto("faculty.html")
total = ev("document.querySelectorAll('[data-filter-list] [data-filter-item]').length")
ok("faculty: cards render", total and total>=20, f"total={total}")
ev("(()=>{const i=document.querySelector('[data-filter-input]');i.value='gogoi';i.dispatchEvent(new Event('input',{bubbles:true}));})()")
time.sleep(0.3)
ok("faculty: search filters", ev("document.querySelectorAll('[data-filter-list] [data-filter-item]:not([style*=\"display: none\"])').length")==1)

# registration link is mailto
goto("event-urjotsav-2026.html")
ok("event: register is mailto", ev("!!document.querySelector('a[href^=\"mailto:\"]')"))

ws.close(); chrome.terminate(); srv.shutdown()
print(f"\nSTATIC BUILD AUDIT  PASSED: {len(PASS)}  FAILED: {len(FAIL)}")
for f in FAIL: print("  FAIL:", f)
if not FAIL: print("  All static checks passed.")
