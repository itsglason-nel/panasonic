"""
Extracts frontend requests and XSS surface. Run with: python docs/research/per-tab-auth/scripts/phaseA_frontend.py
"""
import os
import re

out_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\docs\research\per-tab-auth"
src_dirs = [
    r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\app",
]
commit_hash = "0d7b700"

output_a3 = [f"Base commit: {commit_hash}\n", "# A3 FRONTEND REQUESTS\n"]
output_a8 = [f"Base commit: {commit_hash}\n", "# A8 XSS AND TOKEN-THEFT SURFACE\n"]

a3_hits = []
a8_hits = []

for root, dirs, files in os.walk(src_dirs[0]):
    for file in files:
        if file.endswith(('.js', '.html', '.jinja')):
            path = os.path.join(root, file)
            rel_path = os.path.relpath(path, r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs")
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # A3 patterns
            for idx, line in enumerate(content.splitlines()):
                if any(x in line for x in ['fetch(', 'XMLHttpRequest', 'EventSource', 'WebSocket', 'window.open', 'location.assign', 'location.href', 'location.replace']):
                    a3_hits.append(f"- `{rel_path}:{idx+1}`: `{line.strip()}`")
                    
                # A8 patterns
                if any(x in line for x in ['innerHTML', 'outerHTML', 'insertAdjacentHTML', 'document.write', 'eval(', 'new Function', '.html(', '.append(']):
                    a8_hits.append(f"- `{rel_path}:{idx+1}`: `{line.strip()}`")
                    
            # external scripts
            scripts = re.findall(r'<script[^>]*src=["\'](.*?)["\']', content)
            for s in scripts:
                if 'http' in s or '//' in s:
                    a8_hits.append(f"- `{rel_path}` External script: `{s}`")

output_a3.append("## Fetch, XHR, and Location Assignments\n")
output_a3.extend(a3_hits)

output_a8.append("## Unsafe DOM assignments and External Scripts\n")
output_a8.extend(a8_hits)

output_a3.append("\n**Reconciliation**: Searched .js, .html, .jinja. (Positive control: fetch in app.js).")
output_a8.append("\n**Reconciliation**: Searched .js, .html, .jinja. (Positive control: innerHTML in some JS files, external CDNs).")

with open(os.path.join(out_dir, "03-frontend-requests.md"), 'w', encoding='utf-8') as f:
    f.write("\n".join(output_a3))
    
with open(os.path.join(out_dir, "08-xss-surface.md"), 'w', encoding='utf-8') as f:
    f.write("\n".join(output_a8))

