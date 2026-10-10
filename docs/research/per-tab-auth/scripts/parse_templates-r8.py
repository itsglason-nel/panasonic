import os
roots = []
for root, _, files in os.walk("app/templates"):
    for f in files:
        if f.endswith(".html"):
            path = os.path.join(root, f)
            with open(path, "r", encoding="utf-8") as fh:
                content = fh.read()
                if "{% extends" not in content:
                    roots.append((path.replace("\\", "/"), "scripts.html" in content, "app.js" in content, "fetch(" in content, "io(" in content))
print("| Template | Extends | Loads scripts.html wrapper | Loads app.js | Calls fetch or io directly |")
print("|---|---|---|---|---|")
for r in roots: print(f"| {r[0]} | None | {r[1]} | {r[2]} | {r[3] or r[4]} |")
