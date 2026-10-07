import os
import re
import ast
import inspect
import builtins
from pathlib import Path

# Paths
script_path = Path(__file__).resolve()
# Root: scripts -> per-tab-auth -> research -> docs -> root
root_dir = script_path.parent.parent.parent.parent.parent
app_dir = root_dir / 'app'
output_dir = script_path.parent.parent / 'output'
md_dir = script_path.parent.parent
output_dir.mkdir(exist_ok=True)

def write_out(name, lines):
    text = '\n'.join(lines)
    (output_dir / f"{name}.txt").write_text(text, encoding='utf-8')
    return text

def safe_read(p):
    try: return p.read_text(encoding='utf-8')
    except: return ""

# 3a. Dashboard Wall Screen check
dash_path = app_dir / 'templates' / 'dashboard.html'
dash_c = safe_read(dash_path)
dash_out = [
    "--- Dashboard.html Content ---", dash_c,
    "--- Inherited Templates ---"
]
for match in re.findall(r'{%\s*extends\s+[\'"](.*?)[\'"]\s*%}', dash_c):
    dash_out.append(f"Extends: {match}")
    base_c = safe_read(app_dir / 'templates' / match)
    timers = [line.strip() for line in base_c.splitlines() if 'setInterval' in line or 'setTimeout' in line or '<meta' in line]
    dash_out.append(f"Timers in {match}: {timers}")
write_out('dashboard_check', dash_out)

# 3b. Admin Textual Expansion & Schedules Fetch
admin_path = app_dir / 'templates' / 'admin.html'
admin_lines = []
for line in safe_read(admin_path).splitlines():
    m = re.search(r'{%\s*include\s+[\'"](.*?)[\'"]\s*%}', line)
    if m:
        admin_lines.extend(safe_read(app_dir / 'templates' / m.group(1)).splitlines())
    else:
        admin_lines.append(line)
admin_5425 = admin_lines[5424:5440]
write_out('admin_expansion_5425', admin_5425)

schedules_calls = []
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith(('.html', '.js')):
            p = Path(root) / f
            rel = p.relative_to(root_dir)
            lines = safe_read(p).splitlines()
            for i, l in enumerate(lines):
                if 'schedules' in l and 'fetch(' in l:
                    schedules_calls.append(f"{rel}:{i+1} -> {l.strip()}")
                if 'active' in l and 'fetch(' in l:
                    schedules_calls.append(f"{rel}:{i+1} -> {l.strip()}")
write_out('schedules_fetches', schedules_calls)

# 3e. Observers
init_c = safe_read(app_dir / '__init__.py').splitlines()
observers = []
for i, l in enumerate(init_c):
    if 'Thread(' in l and 'target=' in l and 'observer' in l.lower():
        observers.append(f"__init__.py:{i+1} -> {l.strip()}")
write_out('observers', observers)

# 3f. trigger-pdf
routes_c = safe_read(app_dir / 'routes' / 'admin.py').splitlines()
trigger_pdf = []
in_trigger = False
for i, l in enumerate(routes_c):
    if '@admin_bp.route' in l and 'trigger-pdf' in l:
        in_trigger = True
    if in_trigger:
        trigger_pdf.append(f"{i+1}: {l}")
        if l.startswith('def ') and trigger_pdf[0] != f"{i+1}: {l}":
            pass
        if len(trigger_pdf) > 20: # just get enough to see logic
            break
write_out('trigger_pdf_logic', trigger_pdf)

# 4. A6 FOR REAL: HTTP Clients in launcher, tools, weight reader
http_clients = []
for root, dirs, files in os.walk(root_dir):
    if '.git' in root or 'venv' in root or 'node_modules' in root: continue
    for f in files:
        if f.endswith(('.py', '.pyw', '.ps1')):
            p = Path(root) / f
            rel = p.relative_to(root_dir)
            lines = safe_read(p).splitlines()
            for i, l in enumerate(lines):
                if any(x in l for x in ['import requests', 'urllib', 'httpx', 'http.client', 'aiohttp', 'Invoke-WebRequest', 'socket']):
                    http_clients.append(f"{rel}:{i+1} -> {l.strip()}")
write_out('http_clients', http_clients)

# 6. A4 FOR REAL
a4 = []
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith(('.html', '.js')):
            p = Path(root) / f
            rel = p.relative_to(root_dir)
            lines = safe_read(p).splitlines()
            for i, l in enumerate(lines):
                if any(x in l for x in ['window.open', 'location.href', 'location.assign', 'location.replace', '<form', '<iframe', '<embed', 'download=', 'EventSource']):
                    a4.append(f"{rel}:{i+1} -> {l.strip()}")
write_out('a4_calls', a4)

# 7. WRITES TABLE
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
                        for dec in node.decorator_list:
                            if isinstance(dec, ast.Call) and getattr(dec.func, 'attr', '') == 'route':
                                methods = ['GET']
                                for kw in dec.keywords:
                                    if kw.arg == 'methods':
                                        methods = ast.literal_eval(kw.value)
                                if any(m in ['POST', 'PUT', 'DELETE', 'PATCH'] for m in methods):
                                    db_writes = []
                                    if 'db.session.commit()' in ast.unparse(node):
                                        db_writes.append("DB Commit")
                                    writes.append(f"{rel}:{node.lineno} -> {node.name} {methods} | Writes: {bool(db_writes)}")
            except: pass
write_out('writes', writes)

print("Master script successfully wrote outputs.")
