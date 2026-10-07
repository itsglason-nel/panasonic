"""
Extracts template stats. Run with: python docs/research/per-tab-auth/scripts/phaseA_templates.py
"""
import os
import ast
import re
from collections import defaultdict

out_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\docs\research\per-tab-auth"
py_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\app"
template_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\app\templates"
commit_hash = "0d7b700"

output_a2 = [f"Base commit: {commit_hash}\n", "# A2 TEMPLATES\n"]

render_template_calls = []

class RenderVisitor(ast.NodeVisitor):
    def __init__(self, filename):
        self.filename = filename
    def visit_Call(self, node):
        if isinstance(node.func, ast.Name) and node.func.id == 'render_template':
            template_name = "unknown"
            if node.args and isinstance(node.args[0], ast.Constant):
                template_name = node.args[0].value
            
            kwargs = {}
            for kw in node.keywords:
                try:
                    kwargs[kw.arg] = ast.unparse(kw.value)
                except:
                    kwargs[kw.arg] = "complex_expr"
                    
            render_template_calls.append({
                "file": self.filename,
                "line": node.lineno,
                "template": template_name,
                "kwargs": kwargs
            })
        self.generic_visit(node)

for root, dirs, files in os.walk(py_dir):
    for file in files:
        if file.endswith('.py'):
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            try:
                tree = ast.parse(content)
                visitor = RenderVisitor(os.path.relpath(path, r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs"))
                visitor.visit(tree)
            except:
                pass

output_a2.append("## Render Template Calls\n")
for call in render_template_calls:
    output_a2.append(f"- **{call['template']}** (in {call['file']}:{call['line']})")
    output_a2.append(f"  - kwargs: {call['kwargs']}")

template_stats = []
used_templates = set([c['template'] for c in render_template_calls])
all_templates = set()

for root, dirs, files in os.walk(template_dir):
    for file in files:
        if file.endswith('.html') or file.endswith('.jinja'):
            path = os.path.join(root, file)
            rel_name = os.path.relpath(path, template_dir).replace('\\', '/')
            all_templates.add(rel_name)
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # extract jinja blocks
            uses = []
            if 'current_user' in content: uses.append('current_user')
            if 'session' in content: uses.append('session')
            if 'g.' in content: uses.append('g')
            if 'request.' in content: uses.append('request')
            if 'config[' in content or 'config.' in content: uses.append('config')
            if 'get_flashed_messages' in content: uses.append('get_flashed_messages')
            
            loops = len(re.findall(r'{%\s*for\s', content))
            ifs = len(re.findall(r'{%\s*if\s', content))
            safes = len(re.findall(r'\|safe', content))
            tojsons = len(re.findall(r'\|tojson', content))
            
            has_inline_script = '<script' in content and '{{' in content
            forms = re.findall(r'<form[^>]*>', content)
            form_actions = []
            has_csrf = 'csrf_token' in content
            
            for form in forms:
                match = re.search(r'action=["\'](.*?)["\']', form)
                form_actions.append(match.group(1) if match else "implicit")
                
            template_stats.append({
                "name": rel_name,
                "uses": uses,
                "loops": loops,
                "ifs": ifs,
                "safes": safes,
                "tojsons": tojsons,
                "inline_script_jinja": has_inline_script,
                "forms": len(forms),
                "has_csrf": has_csrf
            })

output_a2.append("\n## Template Features\n")
output_a2.append("| Template | Uses | Loops | Ifs | |safe | |tojson | Inline JS w/ Jinja | Forms | CSRF |")
output_a2.append("|---|---|---|---|---|---|---|---|---|")
for ts in template_stats:
    output_a2.append(f"| {ts['name']} | {', '.join(ts['uses'])} | {ts['loops']} | {ts['ifs']} | {ts['safes']} | {ts['tojsons']} | {ts['inline_script_jinja']} | {ts['forms']} | {ts['has_csrf']} |")

output_a2.append(f"\n**Reconciliation**:")
output_a2.append(f"- Total templates in folder: {len(all_templates)}")
output_a2.append(f"- Templates used by render_template: {len(used_templates)}")
output_a2.append(f"- Unused templates: {len(all_templates - used_templates)}")

with open(os.path.join(out_dir, "02-templates.md"), 'w', encoding='utf-8') as f:
    f.write("\n".join(output_a2))

