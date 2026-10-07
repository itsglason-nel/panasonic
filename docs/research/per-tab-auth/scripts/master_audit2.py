import os
import re
import ast
import inspect
from pathlib import Path

script_path = Path(__file__).resolve()
root_dir = script_path.parent.parent.parent.parent.parent
app_dir = root_dir / 'app'
output_dir = script_path.parent.parent / 'output'

def write_out(name, lines):
    text = '\n'.join(lines)
    (output_dir / f"{name}.txt").write_text(text, encoding='utf-8')
    return text

def safe_read(p):
    try: return p.read_text(encoding='utf-8')
    except: return ""

# --- A8. XSS Surface ---
a8_hits = []
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith(('.html', '.js')):
            p = Path(root) / f
            lines = safe_read(p).splitlines()
            for i, l in enumerate(lines):
                if any(x in l for x in ['innerHTML', 'outerHTML', 'insertAdjacentHTML', 'document.write', 'eval(', 'new Function', '.html(', '.append(']):
                    a8_hits.append(f"{p.relative_to(root_dir)}:{i+1} -> {l.strip()}")
write_out('a8_xss', a8_hits)

# --- A10. Role Matrix ---
roles = []
for root, dirs, files in os.walk(app_dir / 'routes'):
    for f in files:
        if f.endswith('.py'):
            p = Path(root) / f
            content = safe_read(p)
            try:
                tree = ast.parse(content)
                for node in ast.walk(tree):
                    if isinstance(node, ast.FunctionDef):
                        dec_roles = []
                        for dec in node.decorator_list:
                            if isinstance(dec, ast.Call) and getattr(dec.func, 'id', '') == 'roles_required':
                                dec_roles.append(ast.unparse(dec.args[0]))
                        if dec_roles:
                            roles.append(f"{f}:{node.lineno} -> {node.name}: {dec_roles}")
            except: pass
write_out('a10_roles', roles)

# --- 3c. Forms vs Fetches (admin models) ---
modals_path = app_dir / 'templates' / 'admin' / 'components' / 'modals.html'
modals_content = safe_read(modals_path)
posts = re.findall(r'<form.*?method=["\']POST["\'].*?>', modals_content, re.IGNORECASE)
write_out('admin_post_forms', posts)

# --- 3d. transfer_slips.created_by ---
transfer_slip_py = safe_read(app_dir / 'routes' / 'admin.py')
ts_lines = transfer_slip_py.splitlines()
ts_creation = []
for i, l in enumerate(ts_lines):
    if 'TransferSlip(' in l:
        ts_creation.append(f"{i+1}: {l.strip()}")
write_out('transfer_slips_creation', ts_creation)

# --- A2 FOR REAL ---
a2_table = []
for root, dirs, files in os.walk(app_dir / 'templates'):
    for f in files:
        if f.endswith('.html'):
            p = Path(root) / f
            c = safe_read(p)
            cu = c.count('current_user')
            su = c.count('session')
            loops = c.count('{% for')
            ifs = c.count('{% if')
            safes = c.count('|safe')
            tojsons = c.count('|tojson')
            a2_table.append(f"{f}: cu={cu}, sess={su}, loops={loops}, ifs={ifs}, safes={safes}, tojsons={tojsons}")
write_out('a2_templates', a2_table)

# --- 9. LOCKOUT CODE ---
auth_py = safe_read(app_dir / 'routes' / 'auth.py').splitlines()
lockout_code = []
for i in range(11, 25):
    lockout_code.append(f"{i+1}: {auth_py[i]}")
write_out('lockout_code', lockout_code)

print("Master script 2 successfully wrote outputs.")
