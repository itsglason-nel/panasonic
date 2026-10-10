import os, sys, threading, time
from werkzeug.serving import make_server
from flask import Flask
from flask_socketio import SocketIO
import socketio as sio_client
import requests
import re

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

def test_config(order):
    app = Flask(__name__)
    app.config["SECRET_KEY"] = "test"
    sio = SocketIO(app, async_mode="threading", logger=False, engineio_logger=False)
    import socketio as sio_module
    if order == "innermost":
        app.wsgi_app = TabScope(app.wsgi_app)
        wsgi_app = sio_module.WSGIApp(sio.server, app.wsgi_app)
    else:
        wsgi_app = sio_module.WSGIApp(sio.server, app.wsgi_app)
        wsgi_app = TabScope(wsgi_app)
    server = make_server('127.0.0.1', 0, wsgi_app, threaded=True)
    port = server.server_port
    t = threading.Thread(target=server.serve_forever)
    t.daemon = True
    t.start()
    time.sleep(0.5)
    try:
        path = "/t/1234567890123456789012/socket.io/"
        resp = requests.get(f"http://127.0.0.1:{port}{path}?transport=polling&EIO=4")
        if resp.status_code == 404:
            res_text, upg = "404 Not Found", False
        else:
            client = sio_client.Client()
            client.connect(f"http://127.0.0.1:{port}", socketio_path=path, transports=["websocket", "polling"])
            time.sleep(0.5)
            res_text, upg = f"Connected ({client.transport()})", (client.transport() == "websocket")
            client.disconnect()
    except Exception as e:
        res_text, upg = f"Error: {e}", False
    server.shutdown()
    return res_text, upg

print("--- SOCKET.IO REAL RUN RESULTS ---")
print("Mode: threading")
for mode in ["innermost", "outermost"]:
    try:
        res, upg = test_config(mode)
        print(f"TabScope {'BEFORE' if mode == 'innermost' else 'AFTER'} init_app ({mode}): Result={res}, WebSocket Upgraded={upg}")
    except Exception as e:
        print(f"TabScope {'BEFORE' if mode == 'innermost' else 'AFTER'} init_app ({mode}): Failed with error: {e}")
