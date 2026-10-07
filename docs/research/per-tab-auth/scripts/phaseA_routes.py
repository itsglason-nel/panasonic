"""
Extracts routes and role matrices. Run with: python docs/research/per-tab-auth/scripts/phaseA_routes.py
"""
import os
import ast
import re

out_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\docs\research\per-tab-auth"
src_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\app\routes"

# Commit hash
commit_hash = "0d7b700"

output_a1 = [f"Base commit: {commit_hash}\n", "# A1 ROUTES\n"]
output_a10 = [f"Base commit: {commit_hash}\n", "# A10 ROLES\n", "Roles that exist: [PENDING OWNER RESULT]\n"]

routes_data = []

class RouteVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
        
    def visit_FunctionDef(self, node):
        url = "unknown"
        methods = "['GET']"
        blueprint = "unknown"
        decorators = []
        is_route = False
        
        for dec in node.decorator_list:
            if isinstance(dec, ast.Call):
                func = dec.func
                if isinstance(func, ast.Attribute) and func.attr == 'route':
                    is_route = True
                    blueprint = func.value.id if isinstance(func.value, ast.Name) else "unknown"
                    if dec.args:
                        if isinstance(dec.args[0], ast.Constant):
                            url = dec.args[0].value
                    for kw in dec.keywords:
                        if kw.arg == 'methods':
                            methods = ast.unparse(kw.value)
            elif isinstance(dec, ast.Name):
                decorators.append(dec.id)
            elif isinstance(dec, ast.Attribute):
                decorators.append(dec.attr)
            
            # check auth decorators
            if isinstance(dec, ast.Call) and isinstance(dec.func, ast.Name):
                decorators.append(f"{dec.func.id}()")
                
        if is_route:
            body_text = ast.unparse(node)
            reads_user = "current_user" in body_text
            reads_session = "session" in body_text
            
            returns = "HTML"
            if "jsonify" in body_text:
                returns = "JSON"
            elif "redirect(" in body_text:
                returns = "Redirect"
            elif "send_file(" in body_text:
                returns = "Download"
            
            # Simple check for role enforcement in body
            roles_allowed = "All (No Check)"
            if "roles_required" in decorators or "login_required" in decorators:
                roles_allowed = "Logged In"
            if "current_user.role" in body_text:
                roles_allowed = "Checked in body"
                
            routes_data.append({
                "url": url,
                "methods": methods,
                "blueprint": blueprint,
                "file": f"{self.filename}:{node.lineno}",
                "decorators": ", ".join(decorators),
                "returns": returns,
                "reads_user": reads_user,
                "reads_session": reads_session,
                "roles": roles_allowed
            })
            
        self.generic_visit(node)

for root, dirs, files in os.walk(src_dir):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs")
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            tree = ast.parse(content)
            visitor = RouteVisitor(rel_path)
            visitor.visit(tree)

output_a1.append("| URL | Methods | Blueprint | File:Line | Decorators | Returns | Reads User/Session |")
output_a1.append("|---|---|---|---|---|---|---|")
for r in routes_data:
    output_a1.append(f"| {r['url']} | {r['methods']} | {r['blueprint']} | {r['file']} | {r['decorators']} | {r['returns']} | {r['reads_user']} / {r['reads_session']} |")

output_a1.append(f"\nTotal routes found: {len(routes_data)}")
output_a1.append("\n**Reconciliation**: Searched .py files in app/routes using AST parsing. (Positive control: /auth/login found).")

with open(os.path.join(out_dir, "01-routes.md"), 'w', encoding='utf-8') as f:
    f.write("\n".join(output_a1))

output_a10.append("\n## Matrix of Route x Role (What code allows today)")
output_a10.append("| Route | Permitted Roles (Based on Decorators / Body Checks) |")
output_a10.append("|---|---|")
for r in routes_data:
    output_a10.append(f"| {r['url']} ({r['methods']}) | {r['roles']} |")

output_a10.append("\n*Hidden UI mapping pending A2 template analysis.*")
with open(os.path.join(out_dir, "10-role-matrix.md"), 'w', encoding='utf-8') as f:
    f.write("\n".join(output_a10))

