import os, sys, threading, time
from werkzeug.serving import make_server
import requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import tab_spike
app = tab_spike.app
server = make_server('127.0.0.1', 0, app, threaded=True)
port = server.server_port
t = threading.Thread(target=server.serve_forever)
t.daemon = True
t.start()
time.sleep(0.5)
try:
    print("--- FAILURE MODE SPIKE RUN ---")
    r = requests.get(f"http://127.0.0.1:{port}/api/whoami")
    print(f"Final Status: {r.status_code}\nFinal URL: {r.url}\nContent-Type: {r.headers.get('Content-Type')}\nBody snippet:\n{r.text[:100].replace(chr(10), '\\n')}")
finally:
    server.shutdown()
