import os, threading, time, secrets, re
from werkzeug.serving import make_server
from flask import Flask, request, jsonify, redirect
from flask_session import Session
import requests

PREFIX = re.compile(r"^/t/([A-Za-z0-9_-]{22})(/.*)?$")
class TabScope:
    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app
    def __call__(self, environ, start_response):
        m = PREFIX.match(environ.get("PATH_INFO", ""))
        if m:
            environ["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + "/t/" + m.group(1)
            environ["PATH_INFO"] = m.group(2) or "/"
        return self.wsgi_app(environ, start_response)

app = Flask(__name__)
app.config.update(SECRET_KEY="test", SESSION_TYPE="filesystem", SESSION_FILE_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)), "spike_sessions_test"), SESSION_PERMANENT=False, SESSION_COOKIE_NAME="tabspike")
os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
Session(app)
app.session_interface.get_cookie_path = lambda _app: request.script_root or "/"
app.wsgi_app = TabScope(app.wsgi_app)

@app.before_request
def ensure_tab_prefix():
    if request.script_root or request.path.startswith("/static"): return None
    if request.method != "GET": return jsonify(error="Missing tab prefix"), 401
    if "text/html" in request.headers.get("Accept", "") or request.headers.get("Sec-Fetch-Mode", "") == "navigate":
        return redirect("/t/" + secrets.token_urlsafe(16) + request.full_path.rstrip("?"))
    return jsonify(error="Missing tab prefix"), 401

@app.route("/api/ping")
def ping(): return jsonify(success=True)

@app.route("/login", methods=["POST"])
def login(): return jsonify(success=True)

server = make_server('127.0.0.1', 0, app, threaded=True)
port = server.server_port
t = threading.Thread(target=server.serve_forever)
t.daemon = True
t.start()
time.sleep(0.5)

sess_dir = app.config["SESSION_FILE_DIR"]
def count_sessions(): return len(os.listdir(sess_dir))

before = count_sessions()
for _ in range(100): requests.get(f"http://127.0.0.1:{port}/api/ping", headers={"Accept": "application/json"})
after_poll = count_sessions()
r_post = requests.post(f"http://127.0.0.1:{port}/login")
after_post = count_sessions()

print("--- PREFIX POLICY TEST ---")
print(f"Sessions before: {before}")
print(f"Sessions after 100 missed polling requests: {after_poll}")
print(f"Sessions after unprefixed POST: {after_post}")
print(f"POST status: {r_post.status_code}")
if r_post.cookies: print("WARNING: Cookies were set!")
else: print("SUCCESS: No session cookie set for unprefixed POST")
server.shutdown()
