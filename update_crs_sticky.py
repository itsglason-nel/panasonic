path = r'app\templates\admin\components\modals.html'
with open(path, 'r', encoding='utf-8') as f:
    html = f.read()

old_sticky = 'position: sticky; bottom: 0; background: white; padding: 16px 0; border-top: 1px solid var(--border-light); z-index: 10;'
old_sticky2 = 'position: sticky; bottom: -20px; background: white; padding: 16px 0; border-top: 1px solid var(--border-light); z-index: 10;'

# Use bottom: 0 to stick it exactly at the scrollport's bottom edge.
# Add margin-bottom: -24px and padding-bottom: 24px so the white background bleeds into the modal padding and covers any text scrolling behind it.
new_sticky = 'position: sticky; bottom: -1px; background: white; padding: 16px 0 24px 0; margin-bottom: -24px; border-top: 1px solid var(--border-light); z-index: 10;'

html = html.replace(old_sticky, new_sticky)
html = html.replace(old_sticky2, new_sticky)

with open(path, 'w', encoding='utf-8') as f:
    f.write(html)

print("Updated sticky button to cover bottom padding")
