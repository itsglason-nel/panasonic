import secrets
import re
from flask import request, jsonify, redirect

def register_prefix_policy(app):
    @app.before_request
    def ensure_tab_prefix():
        if request.script_root or request.path.startswith("/static") or request.path.startswith("/socket.io"):
            return None
        if request.method != "GET":
            return jsonify(error="missing tab prefix"), 401
        
        accept = request.headers.get("Accept", "")
        sec_fetch = request.headers.get("Sec-Fetch-Mode", "")
        if "text/html" in accept or sec_fetch == "navigate":
            tab = secrets.token_urlsafe(16)
            rest = request.full_path.rstrip("?")
            return redirect("/t/" + tab + rest)
        return jsonify(error="missing tab prefix"), 401

def apply_cookie_path(app):
    app.session_interface.get_cookie_path = lambda _app: request.script_root or "/"

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
