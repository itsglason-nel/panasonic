# 00-summary.md
## A6 REDO
```
launcher.pyw:11 -> import socket
launcher.pyw:131 -> self.server_socket = None
launcher.pyw:507 -> with socket.create_connection(('127.0.0.1', port), timeout=0.5) as s:
launcher.pyw:635 -> self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
launcher.pyw:636 -> self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
launcher.pyw:638 -> self.server_socket.bind(('127.0.0.1', SINGLE_INSTANCE_PORT))
launcher.pyw:639 -> self.server_socket.listen(5)
launcher.pyw:647 -> if not self.server_socket:
launcher.pyw:649 -> conn, addr = self.server_socket.accept()
launcher.pyw:664 -> if self.server_socket:
launcher.pyw:666 -> self.server_socket.close()
launcher.pyw:669 -> self.server_socket = None
launcher.pyw:1595 -> s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
launcher.pyw:1601 -> except socket.error:
wsgi.py:5 -> from app import create_app, socketio
wsgi.py:10 -> socketio.run(
app\__init__.py:9 -> from flask_socketio import SocketIO  # type: ignore
app\__init__.py:27 -> socketio = SocketIO()
app\__init__.py:68 -> socket_timeout=1, # Quick timeout for the fallback check
app\__init__.py:95 -> socketio.init_app(app, async_mode='eventlet', cors_allowed_origins=cors_origins)
app\routes\api.py:31 -> socket_timeout=0.5,
app\services\weight_reader.py:12 -> import socket
app\services\weight_reader.py:98 -> sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
docs\research\per-tab-auth\scripts\master_audit.py:99 -> if any(x in l for x in ['import requests', 'urllib', 'httpx', 'http.client', 'aiohttp', 'Invoke-WebRequest', 'socket']):
```
ANALYST NOTES (INFERRED):
launcher.pyw:507 is a TCP connect socket check only.
