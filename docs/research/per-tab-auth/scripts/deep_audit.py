import os
import re
import ast

app_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\app"

print("=== 4. POLLING AND WALL SCREENS ===")
polling = []
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith(('.html', '.js')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if 'setInterval' in line or 'setTimeout' in line:
                        polling.append(f"{f}:{i+1} -> {line.strip()}")
                    if '<meta' in line and 'refresh' in line.lower():
                        polling.append(f"{f}:{i+1} -> {line.strip()}")

for p in polling: print(p)

print("\n=== 5. A4 FOR REAL ===")
a4 = []
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith(('.html', '.js')):
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
                for i, line in enumerate(lines):
                    if any(x in line for x in ['window.open', 'location.href', 'location.assign', 'location.replace', '<form']):
                        a4.append(f"{f}:{i+1} -> {line.strip()}")
for p in a4[:15]: print(p)
print(f"(total {len(a4)})")

print("\n=== 8. WRITES AND ATTRIBUTION ===")
routes = []
for root, dirs, files in os.walk(app_dir):
    for f in files:
        if f.endswith('.py') and not 'alter_db' in f:
            path = os.path.join(root, f)
            with open(path, 'r', encoding='utf-8') as file:
                content = file.read()
                try:
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, ast.FunctionDef):
                            for dec in node.decorator_list:
                                if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Attribute) and dec.func.attr == 'route':
                                    methods = []
                                    for kw in dec.keywords:
                                        if kw.arg == 'methods':
                                            methods = ast.literal_eval(kw.value)
                                    if any(m in ['POST', 'PUT', 'DELETE', 'PATCH'] for m in methods):
                                        routes.append(f"{f}:{node.lineno} -> {node.name} {methods}")
                except: pass
for r in routes: print(r)

print("\n=== 9. LOCKOUT CODE ===")
auth_path = os.path.join(app_dir, 'routes', 'auth.py')
with open(auth_path, 'r', encoding='utf-8') as file:
    lines = file.readlines()
    for i in range(11, 25):
        print(f"{i+1}: {lines[i].rstrip()}")

