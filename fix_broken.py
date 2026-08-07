with open('app/routes/admin.py', 'r') as f:
    code = f.read()

models = ['SPAMS', 'CBPCB', 'INSP2', 'INSP3Run', 'INSP3Vib', 'INSP4', 'Repair']
for m in models:
    broken = f"total, records = _get_paginated_data({m}, page, per_page, request.args.get('date', '')\n    ng = _check_ng_history(records).strip(), request.args.get('serial', '').strip())"
    fixed = f"total, records = _get_paginated_data({m}, page, per_page, request.args.get('date', '').strip(), request.args.get('serial', '').strip())\n    ng = _check_ng_history(records)"
    code = code.replace(broken, fixed)

with open('app/routes/admin.py', 'w') as f:
    f.write(code)
