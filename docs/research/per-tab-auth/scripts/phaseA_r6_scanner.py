import os
from pathlib import Path
import re
import site

# Find project root
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent.parent.parent
OUTPUT_DIR = SCRIPT_DIR.parent / "output"

def write_output(name, lines):
    with open(OUTPUT_DIR / name, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

def scan_files(extensions, dirs=["app", "tools", "."]):
    found = []
    for d in dirs:
        dir_path = PROJECT_ROOT / d
        if not dir_path.is_dir():
            if dir_path.is_file() and dir_path.suffix in extensions:
                found.append(dir_path)
            continue
        for root, _, files in os.walk(dir_path):
            if "node_modules" in root or ".git" in root or "venv" in root:
                continue
            for f in files:
                if any(f.endswith(ext) for ext in extensions):
                    found.append(Path(root) / f)
    return found

def run_scans():
    py_files = scan_files([".py"], ["app", "tools", "wsgi.py", "config.py"])
    html_files = scan_files([".html"], ["app"])
    js_files = scan_files([".js"], ["app"])

    # R1: ROOT-RELATIVE URLS
    r1_lines = ["--- R1: ROOT-RELATIVE URLS ---"]
    r1_patterns = [
        r"fetch\(", r"API\.get\(", r"API\.post\(", r"API\.put\(", r"API\.delete\(",
        r"XMLHttpRequest\.open", r"window\.open\(", r"location\.href", r"location\.assign", r"location\.replace",
        r"<a[^>]+href=\"/[^\"]*\"", r"<form[^>]+action=\"/[^\"]*\"", r"src=\"/[^\"]*\"", r"href=\"/[^\"]*\"",
        r"EventSource\(", r"io\("
    ]
    
    direct_calls = 0
    helper_calls = 0
    hardcoded_paths = 0
    url_for_calls = 0

    r1_lines.append(f"Files scanned: {len(py_files + html_files + js_files)}")
    r1_lines.append("Matches:")
    for f in (html_files + js_files):
        with open(f, "r", encoding="utf-8") as fh:
            content = fh.readlines()
            for i, line in enumerate(content, 1):
                if any(re.search(p, line) for p in r1_patterns):
                    if '/static' in line:
                        continue
                    r1_lines.append(f"{f.relative_to(PROJECT_ROOT)}:{i}: {line.strip()}")
                    if "API." in line or "fetch(" in line and "apiWrapper" in f.name:
                        helper_calls += 1
                    else:
                        direct_calls += 1
                    if "url_for" in line:
                        url_for_calls += 1
                    else:
                        hardcoded_paths += 1
                elif "url_for" in line:
                    url_for_calls += 1
    
    r1_lines.append(f"Direct calls: {direct_calls}")
    r1_lines.append(f"Helper calls: {helper_calls}")
    r1_lines.append(f"url_for calls: {url_for_calls}")
    r1_lines.append(f"hardcoded paths: {hardcoded_paths}")
    write_output("R1-r6.txt", r1_lines)

    # R2: PYTHON REDIRECTS
    r2_lines = ["--- R2: PYTHON REDIRECTS ---"]
    r2_patterns = [r"redirect\(", r"abort\(", r"Response\(", r"Location", r"login_view", r"next"]
    
    for f in py_files:
        with open(f, "r", encoding="utf-8") as fh:
            content = fh.readlines()
            for i, line in enumerate(content, 1):
                if any(re.search(p, line) for p in r2_patterns):
                    r2_lines.append(f"{f.relative_to(PROJECT_ROOT)}:{i}: {line.strip()}")
    write_output("R2-r6.txt", r2_lines)

    # R3: SESSION COOKIE PATH
    r3_lines = ["--- R3: SESSION COOKIE PATH ---"]
    for f in [PROJECT_ROOT / "app" / "__init__.py", PROJECT_ROOT / "config.py"]:
        if f.exists():
            r3_lines.append(f"--- {f.name} ---")
            with open(f, "r", encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if "SESSION" in line or "cookie" in line.lower():
                        r3_lines.append(f"{i}: {line.strip()}")
    
    # Try finding Flask-Session source
    try:
        packages = site.getsitepackages()
        for p in packages:
            fs_path = Path(p) / "flask_session"
            if fs_path.exists():
                r3_lines.append(f"\n--- FOUND FLASK-SESSION at {fs_path} ---")
                for src_file in ["sessions.py", "__init__.py"]:
                    sf = fs_path / src_file
                    if sf.exists():
                        r3_lines.append(f"--- {src_file} ---")
                        with open(sf, "r", encoding="utf-8") as fh:
                            content = fh.read()
                            # find save_session and get_cookie_path
                            for match in re.finditer(r"def save_session.*?(?=def |\Z)", content, re.DOTALL):
                                r3_lines.append(match.group(0))
                            for match in re.finditer(r"def delete_session.*?(?=def |\Z)", content, re.DOTALL):
                                r3_lines.append(match.group(0))
                            # look for cookie_path
                            r3_lines.append(f"Mentions of cookie_path in {src_file}:")
                            for i, line in enumerate(content.split("\n"), 1):
                                if "cookie_path" in line or "request.path" in line or "script_root" in line:
                                    r3_lines.append(f"{i}: {line.strip()}")
    except Exception as e:
        r3_lines.append(f"Error finding Flask-Session source: {e}")
    write_output("R3-r6.txt", r3_lines)

    # R4: SERVER STARTUP
    r4_lines = ["--- R4: SERVER STARTUP ---"]
    wsgi_path = PROJECT_ROOT / "wsgi.py"
    if wsgi_path.exists():
        r4_lines.append("--- wsgi.py ---")
        with open(wsgi_path, "r", encoding="utf-8") as fh:
            r4_lines.extend([l.rstrip() for l in fh.readlines()])
    
    r4_lines.append("\n--- SocketIO Matches ---")
    for f in py_files + html_files + js_files:
        with open(f, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if "SocketIO" in line or "@socketio.on" in line or "emit(" in line or "io(" in line:
                    r4_lines.append(f"{f.relative_to(PROJECT_ROOT)}:{i}: {line.strip()}")
    write_output("R4-r6.txt", r4_lines)

    # R5: PATH DEPENDENCIES
    r5_lines = ["--- R5: PATH DEPENDENCIES ---"]
    r5_patterns = [r"request\.path", r"request\.url", r"request\.endpoint", r"request\.host_url", 
                   r"url_for\([^)]*_external=True", r"request\.referrer", r"startswith\([\"\']/admin[\"\']\)",
                   r"before_request", r"after_request"]
    
    for f in py_files:
        with open(f, "r", encoding="utf-8") as fh:
            for i, line in enumerate(fh, 1):
                if any(re.search(p, line) for p in r5_patterns):
                    r5_lines.append(f"{f.relative_to(PROJECT_ROOT)}:{i}: {line.strip()}")
    write_output("R5-r6.txt", r5_lines)

    # R6: SESSION FILES / LOGIN ROUTE
    r6_lines = ["--- R6: SESSION FILES ---"]
    for f in py_files:
        if "auth.py" in str(f) or "__init__.py" in str(f):
            r6_lines.append(f"--- {f.name} ---")
            with open(f, "r", encoding="utf-8") as fh:
                for i, line in enumerate(fh, 1):
                    if "flash(" in line or "csrf" in line.lower() or "login_user" in line:
                        r6_lines.append(f"{i}: {line.strip()}")
    write_output("R6-r6.txt", r6_lines)

if __name__ == "__main__":
    run_scans()
