"""
THROWAWAY PROOF OF CONCEPT - one login per browser TAB on the same address.

How it works
  * Every fresh visit to http://localhost:5055/ is redirected to /t/<random id>/
  * A tiny WSGI layer moves that prefix into SCRIPT_NAME, so Flask routes,
    url_for() and redirect(url_for(...)) keep working with NO route changes.
  * The session cookie is given Path=/t/<random id>. The browser then sends
    that cookie only for that prefix, so every tab has its own login.

This file has no database, reads no .env, imports nothing from the real app,
and listens on 127.0.0.1 only. Demo accounts: alice, bob, carol (password: demo).

Run:  python tab_spike.py      Stop: Ctrl+C
"""
import os
import re
import secrets

from flask import (Flask, jsonify, redirect, render_template_string, request,
                   session, url_for)
from flask_login import (LoginManager, UserMixin, current_user, login_required,
                         login_user, logout_user)
from flask_session import Session
from flask_wtf.csrf import CSRFProtect

PREFIX = re.compile(r"^/t/([A-Za-z0-9_-]{22})(/.*)?$")
USERS = {"alice": "demo", "bob": "demo", "carol": "demo"}


class TabScope:
    """Move /t/<id> from PATH_INFO to SCRIPT_NAME (outermost WSGI layer)."""

    def __init__(self, wsgi_app):
        self.wsgi_app = wsgi_app

    def __call__(self, environ, start_response):
        m = PREFIX.match(environ.get("PATH_INFO", ""))
        if m:
            environ["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + "/t/" + m.group(1)
            environ["PATH_INFO"] = m.group(2) or "/"
        return self.wsgi_app(environ, start_response)


class User(UserMixin):
    def __init__(self, name):
        self.id = name
        self.name = name


app = Flask(__name__)
app.config.update(
    SECRET_KEY=secrets.token_hex(32),
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR=os.path.join(os.path.dirname(os.path.abspath(__file__)), "spike_sessions"),
    SESSION_PERMANENT=False,
    SESSION_COOKIE_NAME="tabspike",
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
Session(app)
# The only "magic": the cookie path follows the tab prefix of the current request.
app.session_interface.get_cookie_path = lambda _app: request.script_root or "/"
app.wsgi_app = TabScope(app.wsgi_app)

csrf = CSRFProtect(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


@login_manager.user_loader
def load_user(user_id):
    return User(user_id) if user_id in USERS else None


@app.before_request
def ensure_tab_prefix():
    """A visit without a tab prefix gets a brand new one (= a new, empty login)."""
    if request.script_root or request.path.startswith("/static"):
        return None
    if request.method != "GET":
        return "Missing tab prefix", 400
    tab = secrets.token_urlsafe(16)  # 22 characters
    rest = request.full_path.rstrip("?")
    return redirect("/t/" + tab + rest)


PAGE = """
<!doctype html><title>Tab spike</title>
<body style="font-family:sans-serif;max-width:640px;margin:2em auto">
<h2>Signed in as: <span id="who">{{ current_user.name }}</span></h2>
<p>This tab's URL prefix: <code>{{ request.script_root }}</code></p>
<p><button onclick="callApi()">Call /api/whoami (hard-coded root URL)</button>
   <button onclick="postEcho()">POST /api/echo (with CSRF)</button>
   <a href="{{ url_for('logout') }}">Log out (this tab only)</a></p>
<pre id="out">(nothing yet)</pre>
<script>
// Stand-in for the shim the real app would need: root-relative URLs get the tab prefix.
const BASE = "{{ request.script_root }}";
const realFetch = window.fetch.bind(window);
window.fetch = (u, o) => realFetch(
  (typeof u === "string" && u.startsWith("/") && !u.startsWith(BASE + "/")) ? BASE + u : u, o);
const out = document.getElementById("out");
async function callApi(){ const r = await fetch("/api/whoami"); out.textContent = r.status + " " + await r.text(); }
async function postEcho(){
  const r = await fetch("/api/echo", {method:"POST",
    headers:{"Content-Type":"application/json","X-CSRFToken":"{{ csrf_token() }}"},
    body: JSON.stringify({hello:"from this tab"})});
  out.textContent = r.status + " " + await r.text();
}
</script></body>
"""

LOGIN = """
<!doctype html><title>Login</title>
<body style="font-family:sans-serif;max-width:420px;margin:2em auto">
<h2>Log in (tab {{ request.script_root }})</h2>
{% if error %}<p style="color:#b00">{{ error }}</p>{% endif %}
<form method="post" action="{{ url_for('login') }}">
  <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
  <p><input name="username" placeholder="alice / bob / carol" autofocus></p>
  <p><input name="password" type="password" placeholder="demo"></p>
  <p><button>Log in</button></p>
</form></body>
"""


@app.route("/")
@login_required
def index():
    return render_template_string(PAGE)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        name = request.form.get("username", "")
        if USERS.get(name) == request.form.get("password"):
            login_user(User(name))
            return redirect(url_for("index"))
        error = "Wrong username or password"
    return render_template_string(LOGIN, error=error)


@app.route("/logout")
def logout():
    logout_user()
    session.clear()
    return redirect(url_for("login"))


@app.route("/api/whoami")
@login_required
def api_whoami():
    return jsonify(user=current_user.name, tab=request.script_root)


@app.route("/api/echo", methods=["POST"])
@login_required
def api_echo():
    return jsonify(user=current_user.name, got=request.get_json(silent=True))


if __name__ == "__main__":
    os.makedirs(app.config["SESSION_FILE_DIR"], exist_ok=True)
    print("Open http://localhost:5055/ in TWO tabs and log in as different users.")
    app.run(host="127.0.0.1", port=5055, debug=False, threaded=True)
