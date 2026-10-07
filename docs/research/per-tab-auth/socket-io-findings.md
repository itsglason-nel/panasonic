# socket-io-findings.md
```
__init__.py:9 -> from flask_socketio import SocketIO  # type: ignore
__init__.py:27 -> socketio = SocketIO()
__init__.py:91 -> # Flask-SocketIO
__init__.py:95 -> socketio.init_app(app, async_mode='eventlet', cors_allowed_origins=cors_origins)
app\templates\scoreboard\all_lines.html:8 -> <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
app\templates\scoreboard\all_lines.html:141 -> const socket = io();
app\templates\scoreboard\all_lines.html:176 -> socket.on('scoreboard_update', (msg) => {
app\templates\scoreboard\line.html:8 -> <script src="https://cdn.socket.io/4.7.2/socket.io.min.js"></script>
app\templates\scoreboard\line.html:332 -> const socket = io();
app\templates\scoreboard\line.html:493 -> socket.on('scoreboard_update', (msg) => {
```
ANALYST NOTES (INFERRED):
- socket.io is initialized but NOT actively used in the UI. No emit or @socketio.on logic exists.
