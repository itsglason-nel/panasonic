path = r'app/templates/admin/components/scripts.html'
with open(path, 'r', encoding='utf-8') as f:
    js = f.read()

# We need to find the overall status logic in viewGMSDetails
old_js = """        const GMS_STATUS = { 'OK': 'status-ok', 'GOOD': 'status-pass', 'PASS': 'status-pass', 'FAIL': 'status-fail', 'NG': 'status-fail', 'NO GOOD': 'status-fail' };
        const badgeCls = data.status ? (GMS_STATUS[data.status.toUpperCase()] || 'status-fail') : '';
        document.getElementById('gms-det-status').innerHTML = `<span class="status-badge ${badgeCls}">${data.status || '-'}</span>`;"""

new_js = """        const GMS_STATUS = { 'OK': 'status-ok', 'GOOD': 'status-pass', 'PASS': 'status-pass', 'FAIL': 'status-fail', 'NG': 'status-fail', 'NO GOOD': 'status-fail' };
        const badgeCls = data.status ? (GMS_STATUS[data.status.toUpperCase()] || 'status-fail') : '';
        document.getElementById('gms-det-status').innerHTML = `<span class="status-badge ${badgeCls}">${data.status || '-'}</span>`;
        const overallHTML = `<span class="status-badge ${badgeCls}" style="font-size: 13px; padding: 4px 10px;">${data.status || '-'}</span>`;
        document.getElementById('gms-det-top-status').innerHTML = overallHTML;"""

js = js.replace(old_js, new_js)

with open(path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated JS for GMS modal")
