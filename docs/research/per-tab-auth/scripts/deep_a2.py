import os
app_dir = r"c:\Users\DELL\Desktop\Panasonic Project\PanasonicWeb-tabs\app"
print("=== 6. A2 FOR REAL ===")
for root, dirs, files in os.walk(os.path.join(app_dir, 'templates')):
    for f in files:
        if f.endswith('.html'):
            with open(os.path.join(root, f), 'r', encoding='utf-8') as file:
                content = file.read()
                cu = content.count('current_user')
                su = content.count('session')
                loops = content.count('{% for')
                ifs = content.count('{% if')
                print(f"{f}: cu={cu}, sess={su}, loops={loops}, ifs={ifs}")

