import sys, re
import eventlet
eventlet.monkey_patch()
import eventlet.wsgi
from flask import Flask
from flask_socketio import SocketIO, emit
order, port = sys.argv[1], int(sys.argv[2])
PREFIX = re.compile(r"^/t/([A-Za-z0-9_-]{22})(/.*)?$")
class TabScope:
    def __init__(self, wsgi_app): self.wsgi_app = wsgi_app
    def __call__(self, environ, start_response):
        m = PREFIX.match(environ.get("PATH_INFO", ""))
        if m:
            environ["SCRIPT_NAME"] = environ.get("SCRIPT_NAME", "") + "/t/" + m.group(1)
            environ["PATH_INFO"] = m.group(2) or "/"
        return self.wsgi_app(environ, start_response)
app = Flask(__name__)
app.config["SECRET_KEY"] = "x"
sio = SocketIO()
@sio.on("connect")
def on_connect():
    emit("hello", {"ok": True})
if order == "after":
    sio.init_app(app, async_mode="eventlet", cors_allowed_origins="*")
    app.wsgi_app = TabScope(app.wsgi_app)
else:
    app.wsgi_app = TabScope(app.wsgi_app)
    sio.init_app(app, async_mode="eventlet", cors_allowed_origins="*")
eventlet.wsgi.server(eventlet.listen(("127.0.0.1", port)), app, log_output=False)
