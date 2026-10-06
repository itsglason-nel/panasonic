path = r'app\templates\admin\components\modals.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

# Update the h4 tags for INSP3RUN modal
old_h4 = 'style="margin: 0 0 12px 0; font-size: 13px; color: #333; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border-light); padding-bottom: 8px; height: 38px; display: flex; align-items: center;"'
new_h4 = 'style="margin: 0 0 12px 0; font-size: 13px; color: #333; text-transform: uppercase; letter-spacing: 0.05em; border-bottom: 1px solid var(--border-light); padding-bottom: 8px; height: 38px; display: flex; align-items: center; justify-content: center; text-align: center;"'

# We replace all occurrences of old_h4 with new_h4
html = html.replace(old_h4, new_h4)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated modals.html to center align text horizontally")
