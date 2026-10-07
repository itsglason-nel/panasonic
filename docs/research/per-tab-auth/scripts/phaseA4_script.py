import os
import re
import ast
from pathlib import Path

script_path = Path(__file__).resolve()
root_dir = script_path.parent.parent.parent.parent.parent
app_dir = root_dir / 'app'
output_dir = script_path.parent.parent / 'output'
output_dir.mkdir(exist_ok=True)

def write_out(name, lines):
    (output_dir / f"{name}.txt").write_text('\n'.join(lines), encoding='utf-8')

def safe_read(p):
    try: return p.read_text(encoding='utf-8')
    except: return ""

# --- 4. SOCKET.IO ---
init_py = safe_read(app_dir / '__init__.py').splitlines()
sio_lines = []
for i, l in enumerate(init_py):
    if 'SocketIO' in l or 'socketio' in l.lower():
        sio_lines.append(f"__init__.py:{i+1} -> {l.strip()}")

for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith(('.py', '.js', '.html')):
            p = Path(root) / f
            lines = safe_read(p).splitlines()
            for i, l in enumerate(lines):
                if any(x in l for x in ['@socketio.on', 'socket.emit', 'socket.on', 'io(', 'EventSource', 'WebSocket', '/socket.io']):
                    sio_lines.append(f"{p.relative_to(root_dir)}:{i+1} -> {l.strip()}")
write_out('socketio_findings', sio_lines)

# --- 5. SHARED FETCH HELPER ---
js_app = safe_read(app_dir / 'static' / 'js' / 'app.js').splitlines()
fetch_helper = []
in_fetch = False
for i, l in enumerate(js_app):
    if 'const API =' in l or 'window.fetch =' in l:
        in_fetch = True
    if in_fetch:
        fetch_helper.append(f"{i+1}: {l.strip()}")
        if l.strip() == '};' or l.strip() == '}':
            # heuristically stop
            if len(fetch_helper) > 10:
                in_fetch = False
                fetch_helper.append('---')
write_out('fetch_helper', fetch_helper)

admin_text = []
for l in safe_read(app_dir / 'templates' / 'admin.html').splitlines():
    m = re.search(r'{%\s*include\s+[\'"](.*?)[\'"]\s*%}', l)
    if m: admin_text.extend(safe_read(app_dir / 'templates' / m.group(1)).splitlines())
    else: admin_text.append(l)
write_out('admin_5425', admin_text[5424:5440])

# --- 6. TIMERS ---
timers = []
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith(('.html', '.js')):
            p = Path(root) / f
            lines = safe_read(p).splitlines()
            for i, l in enumerate(lines):
                if 'setInterval' in l or 'setTimeout' in l or 'visibilitychange' in l or 'online' in l or 'offline' in l:
                    timers.append(f"{p.relative_to(root_dir)}:{i+1} -> {l.strip()}")
write_out('all_timers', timers)

# --- 7. DASHBOARD ---
routes_c = safe_read(app_dir / 'routes' / 'main.py').splitlines()
dash_route = []
for i, l in enumerate(routes_c):
    if 'def dashboard' in l or '@main_bp.route("/dashboard' in l:
        dash_route.append(f"{i+1}: {l.strip()}")
write_out('dashboard_route', dash_route)
write_out('dashboard_html', safe_read(app_dir / 'templates' / 'dashboard.html').splitlines())

# --- 8. WRITES TABLE REBUILT ---
writes = []
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith('.py'):
            p = Path(root) / f
            rel = p.relative_to(root_dir)
            content = safe_read(p)
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        dec_roles = "NONE"
                        methods = ['GET']
                        for dec in node.decorator_list:
                            if isinstance(dec, ast.Call):
                                attr = getattr(dec.func, 'attr', getattr(dec.func, 'id', ''))
                                if attr in ['route', 'post', 'put', 'delete']:
                                    if attr == 'post': methods = ['POST']
                                    elif attr == 'put': methods = ['PUT']
                                    elif attr == 'delete': methods = ['DELETE']
                                    else:
                                        for kw in dec.keywords:
                                            if kw.arg == 'methods': methods = ast.literal_eval(kw.value)
                                if attr == 'roles_required':
                                    dec_roles = ast.unparse(dec.args[0])
                        
                        db_writes = []
                        for sub in ast.walk(node):
                            if isinstance(sub, ast.Call) and 'db.session.commit' in ast.unparse(sub):
                                db_writes.append('db.session.commit')
                            if isinstance(sub, ast.Call) and getattr(sub.func, 'id', '') == 'wip_resolve':
                                db_writes.append('wip_resolve_helper')
                        
                        if any(m in ['POST', 'PUT', 'DELETE', 'PATCH'] for m in methods) or db_writes:
                            writes.append(f"{rel}:{node.lineno} -> {node.name} {methods} Roles: {dec_roles} Writes: {bool(db_writes)} Elements: {db_writes}")
            except: pass
write_out('rebuilt_writes', writes)

ts_def = safe_read(app_dir / 'models.py').splitlines()
ts_out = []
in_ts = False
for l in ts_def:
    if 'class TransferSlip' in l: in_ts = True
    if in_ts:
        ts_out.append(l)
        if len(ts_out) > 20: break
write_out('ts_def', ts_out)

print("Phase A4 Script Executed.")
