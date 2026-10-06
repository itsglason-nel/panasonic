path = r'app/templates/admin/components/scripts.html'
with open(path, 'r', encoding='utf-8') as f:
    js = f.read()

# We need to find the overall status logic in viewATTDetails
old_js = """        const overallSt = data.status ? data.status.toUpperCase() : '';
        const overallCls = (overallSt === 'GOOD' || overallSt === 'PASS') ? 'status-ok' : ((overallSt === 'NO GOOD' || overallSt === 'NG' || overallSt === 'FAIL' || overallSt === 'FAILED') ? 'status-fail' : ((overallSt === 'REWORK' || overallSt === 'PENDING') ? 'status-warning' : ''));
        document.getElementById('att-det-overall').innerHTML = `<span class="status-badge ${overallCls}">${data.status || ''}</span>`;"""

new_js = """        const overallSt = data.status ? data.status.toUpperCase() : '';
        const overallCls = (overallSt === 'GOOD' || overallSt === 'PASS') ? 'status-ok' : ((overallSt === 'NO GOOD' || overallSt === 'NG' || overallSt === 'FAIL' || overallSt === 'FAILED') ? 'status-fail' : ((overallSt === 'REWORK' || overallSt === 'PENDING') ? 'status-warning' : ''));
        const overallHTML = `<span class="status-badge ${overallCls}" style="font-size: 13px; padding: 4px 10px;">${data.status || ''}</span>`;
        document.getElementById('att-det-overall').innerHTML = overallHTML;
        document.getElementById('att-det-top-status').innerHTML = overallHTML;"""

js = js.replace(old_js, new_js)

with open(path, 'w', encoding='utf-8') as f:
    f.write(js)

print("Updated JS for ATT modal")
