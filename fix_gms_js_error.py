path = r'app/templates/admin/components/scripts.html'
with open(path, 'r', encoding='utf-8') as f:
    js = f.read()

# We need to remove or comment out the remarks assignment
old_remarks_line = "document.getElementById('gms-det-remarks').textContent = data.remarks || '-';"
new_remarks_line = "// document.getElementById('gms-det-remarks').textContent = data.remarks || '-';"

if old_remarks_line in js:
    js = js.replace(old_remarks_line, new_remarks_line)
    
with open(path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Commented out gms-det-remarks in JS")
