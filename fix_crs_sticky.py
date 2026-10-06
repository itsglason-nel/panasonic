path = r'app\templates\admin\components\modals.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

old_sticky = 'position: sticky; bottom: -1px; background: white; padding: 16px 0 24px 0; margin-bottom: -24px; border-top: 1px solid var(--border-light); z-index: 10;'
new_sticky = 'position: sticky; bottom: 0; background: white; padding: 16px 0; margin: 0; border-top: 1px solid var(--border-light); z-index: 10; box-shadow: 0 20px 0 20px white;'

html = html.replace(old_sticky, new_sticky)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Fixed sticky styles")
